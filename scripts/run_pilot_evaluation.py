"""
scripts/run_pilot_evaluation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Executes the empirical pilot evaluation across all 15 projects
with resilient rate-limiting, daily quota handling, automatic pause/resume,
and isolated per-model disk caching.

Features:
- --model: Configurable model name
- --daily-request-limit N: Hard stop or auto-pause for daily free-tier caps
- --requests-per-minute RPM: Sliding window rate limiter to prevent RPM 429s
- Automatic 429 retryDelay extraction: Sleeps exact delay instead of hammering
- Checkpointed progress: Resumes seamlessly from last completed requirement
- Per-model cache isolation: Cache files stored in results/raw/cache/{model}/
"""

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from google import genai
from google.genai import types

from sqam_analyzer.llm_provider import BaseLLMClient
from sqam_analyzer.models import (
    Layer1Output,
    Layer2Output,
    Layer3Output,
    Layer4Output,
    Requirement,
    SRSContext,
    compute_overall_quality_score,
)
from sqam_analyzer.layers import (
    Layer1DocumentScorer,
    Layer2DefectReasoner,
    Layer3SolutionGenerator,
    Layer4SolutionValidator,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sqam_pilot_runner")

BASE_CACHE_DIR = PROJECT_ROOT / "results" / "raw" / "cache"
PILOT_RAW_DIR = PROJECT_ROOT / "results" / "raw" / "pilot"
BASE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
PILOT_RAW_DIR.mkdir(parents=True, exist_ok=True)


def extract_retry_delay(err_str: str) -> Optional[float]:
    """Extracts retryDelay in seconds from Google API error response."""
    m = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+(?:\.\d+)?)s?['\"]?", err_str, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


class RateLimiter:
    """
    Manages rate limits:
    1. Sliding window per-minute rate limiter (RPM)
    2. Daily request budget limiter with automatic midnight UTC pause/resume
    """

    def __init__(
        self,
        requests_per_minute: int = 15,
        daily_request_limit: Optional[int] = None,
        auto_resume: bool = True,
    ):
        self.rpm = requests_per_minute
        self.daily_limit = daily_request_limit
        self.auto_resume = auto_resume
        self.call_timestamps: List[float] = []
        self.daily_call_count = 0
        self.day_start_utc = datetime.now(timezone.utc).date()

    def check_and_wait(self):
        # 1. Day boundary rollover check
        today_utc = datetime.now(timezone.utc).date()
        if today_utc > self.day_start_utc:
            logger.info("New UTC day reached. Resetting daily request counter from %d to 0.", self.daily_call_count)
            self.day_start_utc = today_utc
            self.daily_call_count = 0

        # 2. Daily limit check
        if self.daily_limit is not None and self.daily_call_count >= self.daily_limit:
            if not self.auto_resume:
                logger.warning("Daily request limit of %d reached. Exiting runner as requested.", self.daily_limit)
                sys.exit(0)
            
            # Compute wait time until 00:00:30 UTC
            now_utc = datetime.now(timezone.utc)
            tomorrow_utc = datetime.combine(now_utc.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
            sleep_sec = max(10.0, (tomorrow_utc - now_utc).total_seconds() + 30.0)
            hours = sleep_sec / 3600.0
            logger.warning(
                "Daily request limit (%d) reached. Automatic pause for %.1f hours (%.0fs) until midnight UTC quota reset...",
                self.daily_limit, hours, sleep_sec
            )
            time.sleep(sleep_sec)
            self.day_start_utc = datetime.now(timezone.utc).date()
            self.daily_call_count = 0

        # 3. RPM Sliding window check
        now = time.perf_counter()
        self.call_timestamps = [t for t in self.call_timestamps if now - t < 60.0]
        if len(self.call_timestamps) >= self.rpm:
            sleep_needed = 60.0 - (now - self.call_timestamps[0]) + 0.5
            if sleep_needed > 0:
                logger.info("RPM limit reached (%d calls in last 60s). Rate limiter pausing for %.1fs...", len(self.call_timestamps), sleep_needed)
                time.sleep(sleep_needed)

        self.call_timestamps.append(time.perf_counter())
        self.daily_call_count += 1


class ResilientGeminiClient(BaseLLMClient):
    """
    Gemini client with:
    - Dedicated per-model cache directory
    - Rate limiter integration
    - retryDelay-aware 429 handling
    - Detailed token and latency recording
    """

    def __init__(
        self,
        model_name: str,
        rate_limiter: RateLimiter,
        input_cost_per_m: float = 0.0,
        output_cost_per_m: float = 0.0,
    ):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment or .env file.")
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        self.rate_limiter = rate_limiter
        self.input_cost_per_m = input_cost_per_m
        self.output_cost_per_m = output_cost_per_m

        safe_model = "".join(c if c.isalnum() or c in "._-" else "_" for c in self.model_name)
        self.cache_dir = BASE_CACHE_DIR / safe_model
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.active_layer = "L1"
        self.active_req_id = "UNKNOWN"
        self.call_log: List[Dict[str, Any]] = []

    def _cache_key(self, prompt: str) -> Path:
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
        filename = f"{self.active_layer}_{self.active_req_id}_{prompt_hash}.json"
        safe_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        return self.cache_dir / safe_filename

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        full_prompt = f"{system_prompt}\n---USER---\n{user_prompt}"
        cache_file = self._cache_key(full_prompt)

        start_time = time.perf_counter()

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            meta = cached_data["meta"]
            meta["cached"] = True
            self.call_log.append(meta)
            return cached_data["raw_response"]

        # Enforce rate limiter before non-cached remote request
        self.rate_limiter.check_and_wait()

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )

        max_retries = 10
        backoff = 2.0
        response = None

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=config,
                )
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    server_delay = extract_retry_delay(err_str)
                    if server_delay is not None:
                        wait_sec = server_delay + 5.0
                        if wait_sec > 600:
                            if not self.rate_limiter.auto_resume:
                                logger.error(
                                    "Daily quota exhausted (retryDelay=%.0fs). auto_resume is False; exiting.",
                                    server_delay
                                )
                                raise e
                            logger.warning(
                                "Daily quota exhausted on %s (retryDelay=%.0fs / %.1fh). Sleeping until reset...",
                                self.model_name, server_delay, server_delay / 3600.0
                            )
                            time.sleep(wait_sec)
                            continue
                        else:
                            logger.warning(
                                "429 rate limit hit. Sleeping for server requested retryDelay: %.1fs...",
                                wait_sec
                            )
                            time.sleep(wait_sec)
                            continue
                    else:
                        logger.warning(
                            "Attempt %d hit 429 without retryDelay; backing off for %.1fs...",
                            attempt + 1, backoff
                        )
                        time.sleep(backoff)
                        backoff = min(64.0, backoff * 2.0)
                elif "503" in err_str or "UNAVAILABLE" in err_str:
                    logger.warning(
                        "Attempt %d hit transient 503; backing off for %.1fs...",
                        attempt + 1, backoff
                    )
                    time.sleep(backoff)
                    backoff = min(64.0, backoff * 2.0)
                else:
                    raise e

        latency = time.perf_counter() - start_time
        raw_text = response.text or "{}"

        usage = getattr(response, "usage_metadata", None)
        in_tokens = usage.prompt_token_count if usage else 0
        out_tokens = usage.candidates_token_count if usage else 0

        cost = (in_tokens * self.input_cost_per_m / 1_000_000) + (
            out_tokens * self.output_cost_per_m / 1_000_000
        )

        meta = {
            "layer": self.active_layer,
            "req_id": self.active_req_id,
            "model": self.model_name,
            "temperature": temperature,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "total_tokens": in_tokens + out_tokens,
            "cost_usd": cost,
            "latency_seconds": round(latency, 3),
            "cached": False,
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"raw_response": raw_text, "meta": meta}, f, indent=2)

        self.call_log.append(meta)
        return raw_text

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_class: Type[Any],
        temperature: float = 0.0,
    ) -> Any:
        raw_text = self.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=4096,
        )
        return schema_class.model_validate_json(raw_text)


def build_capped_srs_context(project_name: str, version_file: str) -> SRSContext:
    domain_map = {
        "1_FROG": "3D vision-based gesture recognition system for medical rehabilitation.",
        "2_SMIRK": "Machine learning pedestrian safety braking system under ISO 26262 ASIL D.",
        "3_ONEM": "Global IoT/M2M architecture specification for interoperable services.",
        "4_UIC": "EIRENE radio telecom standard for European high-speed railway networks.",
        "5_EVLA BACKEND SYSTEM REQUIREMENTS": "Radio astronomy correlator backend signal processing.",
        "6": "ETSI multi-access edge computing (MEC) telecommunication architecture.",
        "7": "Industrial programmable logic controller embedded monitoring and safety.",
        "8": "Robotic embedded actuator positioning and telemetry acquisition.",
        "9": "Critical medical patient monitoring system with real-time alerting.",
        "10": "Satellite avionics telemetry, power distribution, and command routing.",
        "11": "Infusion pump medical firmware under IEC 62304 life-critical standards.",
        "12": "Distributed smart-city cyber-physical sensor grid and telemetry.",
        "13": "Onto-DESIDE EU circular economy semantic data platform deliverable.",
        "14": "Secure boundary gateway firewall and cryptographic traffic inspection.",
        "15": "Enterprise cloud financial banking transaction ledger platform.",
    }
    glossary_map = {
        "1_FROG": {"SunSPOT": "Wireless transducer sensor node", "Telemetry": "Sensor data stream"},
        "2_SMIRK": {"Ego-Vehicle": "Subject autonomous rail vehicle", "ASIL D": "Highest safety level"},
        "3_ONEM": {"AE": "Application Entity", "CSE": "Common Services Entity", "M2M": "Machine to Machine"},
        "4_UIC": {"eMLPP": "Enhanced Multi-Level Precedence and Pre-emption", "REC": "Railway Emergency Call"},
        "9": {"Vital Anomaly": "Systolic > 180 mmHg or HR < 40 bpm", "Central Station": "Nurse monitoring node"},
        "13": {"WP2": "Work Package 2 Research Methodology", "Onto-DESIDE": "Circular economy platform"},
    }

    d_summary = domain_map.get(project_name, f"Automated specification quality analysis for {project_name}.")
    glossary = glossary_map.get(project_name, {})

    return SRSContext(
        document_title=f"{project_name} - {version_file}"[:100],
        domain_summary=d_summary[:300],
        glossary=glossary,
        applicable_standards=["ISO/IEC/IEEE 29148:2018"],
        surrounding_requirements=[],
    )


def run_evaluation(
    model_name: str,
    daily_request_limit: Optional[int],
    requests_per_minute: int,
    auto_resume: bool,
    pilot_only: bool = True,
):
    manifest_path = PROJECT_ROOT / "results" / "sample_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("results/sample_manifest.json not found.")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if pilot_only:
        items = [r for r in manifest["requirements"] if r.get("is_pilot_sample")]
        run_name = f"PILOT ({len(items)} items) on {model_name}"
    else:
        items = manifest["requirements"]
        run_name = f"FULL CORPUS ({len(items)} items) on {model_name}"

    print("\n=======================================================")
    print(f"SQAM EVALUATION RUNNER: {run_name}")
    print(f"Model: {model_name} | Temperature: 0.0")
    print(f"Daily Limit: {daily_request_limit or 'Unlimited'} | RPM Limiter: {requests_per_minute}")
    print(f"Auto Resume: {auto_resume}")
    print("=======================================================\n")

    rate_limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        daily_request_limit=daily_request_limit,
        auto_resume=auto_resume,
    )

    client = ResilientGeminiClient(
        model_name=model_name,
        rate_limiter=rate_limiter,
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
    )

    l1_scorer = Layer1DocumentScorer(llm_client=client)
    l2_reasoner = Layer2DefectReasoner(llm_client=client)
    l3_generator = Layer3SolutionGenerator(llm_client=client)
    l4_validator = Layer4SolutionValidator(llm_client=client)

    eval_results = []
    schema_failures = 0
    flagged_in_l1 = 0
    retained_in_l2 = 0
    validated_in_l4 = 0
    rejected_in_l4 = 0

    checkpoint_dir = PROJECT_ROOT / "results" / "raw" / ("pilot" if pilot_only else "full")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    for idx, item in enumerate(items, start=1):
        req_id = item["req_id"]
        proj = item["project"]
        text = item["requirement_text"]
        vfile = item["version_file"]
        stratum = item.get("stratum", "strict_normative")

        # Checkpoint check
        safe_proj = "".join(c if c.isalnum() or c in "._-" else "_" for c in proj)
        safe_req = "".join(c if c.isalnum() or c in "._-" else "_" for c in req_id)
        raw_file = checkpoint_dir / f"{safe_proj}_{safe_req}.json"

        if raw_file.exists():
            print(f"[{idx:02d}/{len(items)}] [CHECKPOINT LOADED] {proj} | {req_id}")
            with open(raw_file, "r", encoding="utf-8") as f:
                rec = json.load(f)
            eval_results.append(rec)
            if rec.get("layer2"):
                flagged_in_l1 += 1
            if rec.get("layer3"):
                retained_in_l2 += 1
            if rec.get("layer4"):
                if rec["layer4"].get("is_valid"):
                    validated_in_l4 += 1
                else:
                    rejected_in_l4 += 1
            continue

        print(f"[{idx:02d}/{len(items)}] Processing {proj} | {req_id} [{stratum}]...")

        srs_ctx = build_capped_srs_context(proj, vfile)
        req_obj = Requirement(req_id=req_id, text=text, section="Functional Specifications")

        # Layer 1
        client.active_layer = "L1"
        client.active_req_id = req_id
        try:
            l1_out = l1_scorer.execute(req_obj, srs_ctx)
        except Exception as ex:
            schema_failures += 1
            logger.error("Schema failure in L1 for %s: %s", req_id, ex)
            continue

        is_flagged = len(l1_out.shortcomings) > 0 or any(a.score < 8.0 for a in l1_out.attribute_scores)
        l2_out = None
        l3_out = None
        l4_out = None

        if is_flagged:
            flagged_in_l1 += 1
            print(f"      -> L1 FLAGGED ({len(l1_out.shortcomings)} defects, Q_req={l1_out.overall_quality_score:.2f})")

            # Layer 2
            client.active_layer = "L2"
            try:
                l2_out = l2_reasoner.execute(req_obj, srs_ctx, candidate_shortcomings=l1_out.shortcomings)
            except Exception as ex:
                schema_failures += 1
                logger.error("Schema failure in L2 for %s: %s", req_id, ex)
                continue

            if l2_out.retained_defects:
                retained_in_l2 += 1
                print(f"      -> L2 RETAINED ({len(l2_out.retained_defects)} defects)")

                # Layer 3
                client.active_layer = "L3"
                try:
                    l3_out = l3_generator.execute(req_obj, srs_ctx, retained_defects=l2_out.retained_defects)
                except Exception as ex:
                    schema_failures += 1
                    logger.error("Schema failure in L3 for %s: %s", req_id, ex)
                    continue

                # Layer 4
                client.active_layer = "L4"
                try:
                    l4_out = l4_validator.execute(req_obj, srs_ctx, retained_defects=l2_out.retained_defects, layer3_output=l3_out)
                except Exception as ex:
                    schema_failures += 1
                    logger.error("Schema failure in L4 for %s: %s", req_id, ex)
                    continue

                if l4_out.is_valid:
                    validated_in_l4 += 1
                    print(f"      -> L4 VALIDATED (Verdict: {l4_out.verdict.value})")
                else:
                    rejected_in_l4 += 1
                    print(f"      -> L4 REJECTED (Verdict: {l4_out.verdict.value})")
            else:
                print(f"      -> L2 DISCARDED all defects as false positives")
        else:
            print(f"      -> L1 CLEAN PASS (Q_req={l1_out.overall_quality_score:.2f})")

        rec = {
            "req_id": req_id,
            "project": proj,
            "version_file": vfile,
            "stratum": stratum,
            "original_text": text,
            "model": model_name,
            "layer1": l1_out.model_dump(),
            "layer2": l2_out.model_dump() if l2_out else None,
            "layer3": l3_out.model_dump() if l3_out else None,
            "layer4": l4_out.model_dump() if l4_out else None,
        }
        eval_results.append(rec)

        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)

    # Save summary report
    summary_path = PROJECT_ROOT / "results" / "raw" / ("pilot_report.json" if pilot_only else "full_report.json")
    
    # Detailed metric aggregations
    overall_scores = [r["layer1"]["overall_quality_score"] for r in eval_results if r.get("layer1")]
    mean_q = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0

    attr_sums = defaultdict(float)
    attr_counts = defaultdict(int)
    defect_counts = defaultdict(int)
    total_l1_defects = 0
    total_l2_retained = 0
    total_l2_discarded = 0

    for r in eval_results:
        l1 = r.get("layer1")
        if l1:
            for sc in l1.get("attribute_scores", []):
                a_name = sc.get("attribute")
                a_score = sc.get("score")
                if a_name and a_score is not None:
                    attr_sums[a_name] += float(a_score)
                    attr_counts[a_name] += 1
            for df in l1.get("shortcomings", []):
                a_name = df.get("attribute")
                defect_counts[a_name] += 1
                total_l1_defects += 1

        l2 = r.get("layer2")
        if l2:
            total_l2_retained += len(l2.get("retained_defects", []))
            total_l2_discarded += len(l2.get("discarded_defects", []))

    attr_means = {k: round(attr_sums[k] / attr_counts[k], 2) for k in sorted(attr_sums.keys())}
    cfsr = round(total_l2_discarded / total_l1_defects * 100, 1) if total_l1_defects > 0 else 0.0
    l4_total = validated_in_l4 + rejected_in_l4
    rrr = round(rejected_in_l4 / l4_total * 100, 1) if l4_total > 0 else 0.0

    summary = {
        "model": model_name,
        "total_evaluated": len(eval_results),
        "schema_failures": schema_failures,
        "flagged_in_l1": flagged_in_l1,
        "clean_pass_in_l1": len(eval_results) - flagged_in_l1,
        "retained_in_l2": retained_in_l2,
        "validated_in_l4": validated_in_l4,
        "rejected_in_l4": rejected_in_l4,
        "flag_rate_pct": round(flagged_in_l1 / len(eval_results) * 100, 1) if eval_results else 0.0,
        "mean_overall_quality_score": round(mean_q, 2),
        "attribute_means": attr_means,
        "total_candidate_defects_l1": total_l1_defects,
        "defect_breakdown_by_attribute": dict(defect_counts),
        "total_defects_retained_l2": total_l2_retained,
        "total_defects_discarded_l2": total_l2_discarded,
        "cfsr_pct": cfsr,
        "rrr_pct": rrr,
        "calls_made": len(client.call_log),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=======================================================")
    print("EVALUATION FINISHED")
    print(f"Evaluated: {len(eval_results)} | Schema Failures: {schema_failures}")
    print(f"Mean Quality Score: {summary['mean_overall_quality_score']:.2f} / 10.0")
    print(f"Flagged L1: {flagged_in_l1}/{len(eval_results)} ({summary['flag_rate_pct']}%)")
    print(f"Candidate Defects: {total_l1_defects} | Retained L2: {total_l2_retained} | CFSR: {cfsr}%")
    print(f"Refinements Evaluated L4: {l4_total} | Validated: {validated_in_l4} | Rejected: {rejected_in_l4} | RRR: {rrr}%")
    print("=======================================================\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQAM Resilient Runner")
    parser.add_argument("--model", type=str, default="gemini-3.5-flash-lite", help="Model name")
    parser.add_argument("--daily-request-limit", type=int, default=None, help="Daily request limit")
    parser.add_argument("--requests-per-minute", type=int, default=15, help="Requests per minute limit")
    parser.add_argument("--auto-resume", action="store_true", default=True, help="Auto pause and resume on quota limit")
    parser.add_argument("--full", action="store_true", default=False, help="Run full candidate pool instead of pilot")

    args = parser.parse_args()
    run_evaluation(
        model_name=args.model,
        daily_request_limit=args.daily_request_limit,
        requests_per_minute=args.requests_per_minute,
        auto_resume=args.auto_resume,
        pilot_only=not args.full,
    )
