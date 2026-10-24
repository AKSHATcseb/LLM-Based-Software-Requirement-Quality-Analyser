"""
scripts/build_full_manifest.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Extracts the full candidate pool of 2,920 requirements across all 43 version files:
- 2,864 strict normative requirements (shall / shall not / must / must not)
- 56 fallback candidates from Project 13 (will / should deliverable stratum)
Computes SHA-256 text hashes, tags a 20-item pilot set spanning all 15 projects,
and writes results/sample_manifest.json.
"""

import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from build_dataset import extract_text_from_file

RANDOM_SEED = 42

def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_candidates_for_file(file_path: Path, is_project_13: bool = False) -> List[str]:
    txt = extract_text_from_file(file_path)
    clean_text = re.sub(r"\r\n", "\n", txt)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean_text)
    candidates = []

    pattern_strict = re.compile(r"\b(shall|shall not|must|must not)\b", re.IGNORECASE)
    pattern_fallback = re.compile(r"\b(will|will not|should|should not)\b", re.IGNORECASE)

    for s in sentences:
        s_clean = s.strip().replace("\n", " ")
        s_clean = re.sub(r"\s+", " ", s_clean)
        if 30 < len(s_clean) < 450:
            if not any(stop in s_clean.lower() for stop in ["this standard specifies", "copyright", "all rights reserved"]):
                if is_project_13:
                    if pattern_fallback.search(s_clean):
                        candidates.append(s_clean)
                else:
                    if pattern_strict.search(s_clean):
                        candidates.append(s_clean)
    return candidates

def generate_full_manifest():
    rng = random.Random(RANDOM_SEED)
    df_orig = pd.read_csv(PROJECT_ROOT / "results/original_215_mock/layer1_multi_project_evaluation_results.csv")
    srs_dir = PROJECT_ROOT / "srs doc versions"

    # Get the 43 version files preserving project ordering
    vfiles_by_proj: Dict[str, List[str]] = {}
    for (p, vf) in df_orig[["project", "version_file"]].drop_duplicates().values:
        vfiles_by_proj.setdefault(p, []).append(vf)

    manifest_records: List[Dict[str, Any]] = []
    project_stats: Dict[str, Dict[str, Any]] = {}

    total_id = 1
    for proj_name, vfiles in vfiles_by_proj.items():
        is_p13 = (proj_name == "13")
        proj_records: List[Dict[str, Any]] = []

        for vf in vfiles:
            file_path = srs_dir / proj_name / vf
            vstem = Path(vf).stem
            cand_texts = extract_candidates_for_file(file_path, is_project_13=is_p13)

            for idx, text in enumerate(cand_texts, start=1):
                clean_t = text.strip()
                req_id = f"REQ-{vstem}-{idx:04d}"
                rec = {
                    "sample_id": total_id,
                    "project": proj_name,
                    "version_file": vf,
                    "version_stem": vstem,
                    "req_id": req_id,
                    "requirement_text": clean_t,
                    "text_hash": sha256_hash(clean_t),
                    "stratum": "fallback_deliverable" if is_p13 else "strict_normative",
                    "is_pilot_sample": False,
                }
                proj_records.append(rec)
                total_id += 1

        manifest_records.extend(proj_records)
        project_stats[proj_name] = {
            "versions_count": len(vfiles),
            "candidate_count": len(proj_records),
            "stratum": "fallback_deliverable" if is_p13 else "strict_normative",
        }

    # Tag 20 pilot requirements covering all 15 projects:
    # 1 per project for all 15 projects + 1 extra for 5 largest projects (3_ONEM, 4_UIC, 12, 6, 5_EVLA) = 20 items
    largest_5 = sorted(project_stats.keys(), key=lambda p: project_stats[p]["candidate_count"], reverse=True)[:5]
    pilot_targets = {p: (2 if p in largest_5 else 1) for p in project_stats}
    pilot_assigned: Dict[str, int] = {p: 0 for p in project_stats}

    # Deterministic selection of pilot items within each project
    for rec in manifest_records:
        p = rec["project"]
        if pilot_assigned[p] < pilot_targets[p]:
            rec["is_pilot_sample"] = True
            pilot_assigned[p] += 1

    total_pilot = sum(1 for r in manifest_records if r["is_pilot_sample"])
    assert total_pilot == 20, f"Expected 20 pilot items, got {total_pilot}"

    manifest_data = {
        "metadata": {
            "random_seed": RANDOM_SEED,
            "total_candidate_pool": len(manifest_records),
            "strict_normative_pool": sum(1 for r in manifest_records if r["stratum"] == "strict_normative"),
            "fallback_deliverable_pool": sum(1 for r in manifest_records if r["stratum"] == "fallback_deliverable"),
            "total_versions": 43,
            "total_projects": 15,
            "pilot_sample_count": total_pilot,
            "pilot_model": "gemini-3.5-flash",
            "pilot_temperature": 0.0,
            "normative_rule": "strict (shall / shall not / must / must not); project 13 fallback (will / should)",
        },
        "per_project_allocation": project_stats,
        "requirements": manifest_records,
    }

    out_file = PROJECT_ROOT / "results" / "sample_manifest.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"Manifest successfully built at {out_file}:")
    print(f"  Total Candidate Pool: {len(manifest_records)}")
    print(f"    - Strict Normative: {manifest_data['metadata']['strict_normative_pool']}")
    print(f"    - Project 13 Fallback: {manifest_data['metadata']['fallback_deliverable_pool']}")
    print(f"  Pilot items tagged: {total_pilot} across 15 projects")
    print("\nPer-Project Candidate Breakdown:")
    for p, s in project_stats.items():
        print(f"  {p:<35}: {s['candidate_count']:<5} (Versions: {s['versions_count']}) [{s['stratum']}]")


if __name__ == "__main__":
    generate_full_manifest()
