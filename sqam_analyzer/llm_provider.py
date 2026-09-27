"""
sqam_analyzer.llm_provider
~~~~~~~~~~~~~~~~~~~~~~~~~~
Modular LLM client abstractions supporting:
- OpenAI & OpenAI-compatible servers (vLLM, Ollama, LMStudio, Azure)
- Google Gemini (via google-genai SDK)
- LangChain BaseChatModel wrappers
- High-fidelity Mock LLM for offline testing and verification
"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def extract_json_from_response(raw_text: str) -> Dict[str, Any]:
    """
    Robust JSON extraction supporting Markdown code fences, stray formatting,
    and trailing content.
    """
    text = raw_text.strip()
    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract content from ```json ... ``` blocks
    fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fenced_match:
        try:
            return json.loads(fenced_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Find outermost matching braces { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from LLM response:\n{raw_text[:500]}...")


class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers in the SQAM pipeline."""

    @abstractmethod
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        """Generates raw text response."""
        pass

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_class: Type[T],
        temperature: float = 0.0,
    ) -> T:
        """
        Generates a response adhering strictly to the provided Pydantic schema class.
        Default implementation calls generate_text and parses using robust JSON extraction.
        """
        raw_text = self.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )
        data = extract_json_from_response(raw_text)
        return schema_class.model_validate(data)


# ---------------------------------------------------------------------------
# OpenAI & OpenAI-Compatible Implementation
# ---------------------------------------------------------------------------

class OpenAILLMClient(BaseLLMClient):
    """
    LLM Client for OpenAI models or any OpenAI-compatible API
    (e.g., Local Ollama, vLLM, DeepSeek, Azure, OpenRouter).
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")

        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key and not base_url:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required to run the OpenAI LLM client. "
                "Please set OPENAI_API_KEY in your environment or .env file, or provide base_url for local models."
            )
        self.model_name = model_name
        self.client = OpenAI(api_key=resolved_key or "EMPTY", base_url=base_url, timeout=timeout)

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Google Gemini Implementation
# ---------------------------------------------------------------------------

class GeminiLLMClient(BaseLLMClient):
    """
    LLM Client for Google Gemini using the official `google-genai` SDK.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
    ):
        try:
            from google import genai
            from google.genai import types
            self._types = types
        except ImportError:
            raise ImportError("google-genai package is required. Install with: pip install google-genai")

        resolved_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not resolved_key:
            raise ValueError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable is required to run the Gemini LLM client. "
                "Please set GEMINI_API_KEY in your environment or .env file."
            )
        self.client = genai.Client(api_key=resolved_key)
        self.model_name = model_name

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        config = self._types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=config,
        )
        return response.text or ""


# ---------------------------------------------------------------------------
# LangChain ChatModel Wrapper
# ---------------------------------------------------------------------------

class LangChainLLMClient(BaseLLMClient):
    """
    Wraps any LangChain BaseChatModel (e.g. ChatOpenAI, ChatAnthropic, etc.).
    Allows drop-in integration with existing LangChain pipelines and agent ecosystems.
    """

    def __init__(self, chat_model: Any):
        self.chat_model = chat_model

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        result = self.chat_model.invoke(messages)
        return str(result.content)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_class: Type[T],
        temperature: float = 0.0,
    ) -> T:
        # Check if the LangChain model supports native structured output
        if hasattr(self.chat_model, "with_structured_output"):
            try:
                structured_llm = self.chat_model.with_structured_output(schema_class)
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                return structured_llm.invoke(messages)
            except Exception as e:
                logger.warning("with_structured_output failed (%s), falling back to JSON parsing", e)

        return super().generate_structured(system_prompt, user_prompt, schema_class, temperature)


# ---------------------------------------------------------------------------
# High-Fidelity Mock Client (For Testing, Verification & Demos)
# ---------------------------------------------------------------------------

class MockLLMClient(BaseLLMClient):
    """
    High-fidelity, deterministic Mock LLM for offline unit testing, evaluation benchmarks,
    and demonstrations without requiring external API keys or network latency.
    """

    def __init__(self, custom_responses: Optional[Dict[str, str]] = None):
        self.custom_responses = custom_responses or {}

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        # Check if a custom scripted response matches
        for key, response in self.custom_responses.items():
            if key in user_prompt or key in system_prompt:
                return response


        # Check Layer 4: Independent Auditor
        if "independent requirements auditor" in system_prompt.lower() or "layer 4" in system_prompt.lower():
            req_id_match = re.search(r"Requirement ID:\s*(\S+)", user_prompt)
            req_id = req_id_match.group(1) if req_id_match else "REQ-TARGET"

            # Check if there are unresolvable flaws
            return json.dumps({
                "req_id": req_id,
                "is_valid": True,
                "verdict": "validated",
                "checks": [
                    {"criterion": "Defect Resolution", "passed": True, "observations": "All justified defects successfully eliminated in refinement."},
                    {"criterion": "No New Ambiguities", "passed": True, "observations": "Refinement uses concrete, unambiguous technical metrics."},
                    {"criterion": "No Unwarranted Assumptions", "passed": True, "observations": "Latency and interface specs align directly with SRS domain constraints."},
                    {"criterion": "Functional Intent Preservation", "passed": True, "observations": "Core clinical/system workflow remains identical to original."},
                    {"criterion": "Syntactic Conformance", "passed": True, "observations": "Conforms strictly to ISO/IEC/IEEE 29148 active 'shall' syntax."}
                ],
                "unwarranted_assumptions_detected": [],
                "new_ambiguities_detected": [],
                "critique_and_feedback": "The refinement surgically resolves the flagged ambiguities without introducing scope creep or altering original intent. Ready for human review."
            })

        # Check Layer 3: Solution Generation (Targeted Refinement)
        if "targeted refinement" in system_prompt.lower() or "ai-assisted requirements editor" in system_prompt.lower():
            req_id_match = re.search(r"Requirement ID:\s*(\S+)", user_prompt)
            req_id = req_id_match.group(1) if req_id_match else "REQ-TARGET"

            req_text_match = re.search(r'Requirement Text:\s*"([^"]+)"', user_prompt)
            req_text = req_text_match.group(1) if req_text_match else "The system shall process requests."

            refined_text = req_text
            changes = []
            addressed_ids = []

            # Surgical replacements based on defects
            if "quickly" in refined_text.lower():
                refined_text = re.sub(r"\bquickly\b", "within 500 milliseconds of detection", refined_text, flags=re.IGNORECASE)
                changes.append("Replaced vague adverb 'quickly' with quantifiable bound 'within 500 milliseconds of detection'")
                addressed_ids.append("DEF-001")

            if "in an intuitive format" in refined_text.lower():
                refined_text = re.sub(
                    r"\bin an intuitive format\b",
                    "formatted according to the MedPulse Clinical Alert Interface standard",
                    refined_text,
                    flags=re.IGNORECASE,
                )
                changes.append("Replaced subjective descriptor 'in an intuitive format' with designated standard interface specification")
            if "clean and intuitively labeled to promote a high quality look that users will find easy to use" in refined_text.lower():
                refined_text = re.sub(
                    r"clean and intuitively labeled to promote a high quality look that users will find easy to use",
                    "labeled in accordance with the Project UI Style Guide (Section 4.1) and ISO 9241-110 usability standards",
                    refined_text,
                    flags=re.IGNORECASE,
                )
                changes.append("Replaced subjective descriptors 'clean', 'intuitively', and 'easy to use' with verifiable ISO 9241-110 usability standards.")
                addressed_ids.extend(["DEF-001", "DEF-002"])

            if "modeled as well as recognized" in refined_text.lower():
                refined_text = re.sub(
                    r"modeled as well as recognized",
                    "modeled and recognized",
                    refined_text,
                    flags=re.IGNORECASE,
                )
                changes.append("Simplified compound clause 'modeled as well as recognized' to ensure singular responsibility.")
                addressed_ids.append("DEF-001")

            if refined_text == req_text:
                refined_text = req_text + " within 1.0 second."
                changes.append("Specified deterministic completion time constraint.")
                addressed_ids.append("DEF-001")

            return json.dumps({
                "req_id": req_id,
                "original_text": req_text,
                "refined_text": refined_text,
                "changes_made": changes,
                "addressed_defect_ids": addressed_ids,
                "functional_intent_preservation_rationale": "Surgically rectified the non-quantifiable or non-singular terms while preserving the primary operational objective."
            })

        # Check Layer 2: Defect Reasoning & Context Verification
        if "defect reasoning" in system_prompt.lower() or "candidate shortcomings from layer 1" in user_prompt.lower():
            req_id_match = re.search(r"Requirement ID:\s*(\S+)", user_prompt)
            req_id = req_id_match.group(1) if req_id_match else "REQ-TARGET"

            # Parse incoming candidate shortcomings
            candidate_defects = []
            shortcomings_match = re.search(r"### CANDIDATE SHORTCOMINGS FROM LAYER 1\s*(\[[\s\S]*?\])", user_prompt)
            if shortcomings_match:
                try:
                    candidate_defects = json.loads(shortcomings_match.group(1))
                except Exception:
                    pass

            evaluations = []
            retained = []
            discarded = []

            for d in candidate_defects:
                did = d.get("defect_id", "DEF-001")
                attr = d.get("attribute", "Unambiguity")
                excerpt = d.get("problematic_excerpt", "")

                # Context-check: if excerpt refers to 'vital anomaly' or 'cdss', it is defined in the glossary!
                if "vital anomaly" in excerpt.lower() or "cdss" in excerpt.lower():
                    evaluations.append({
                        "defect_id": did,
                        "attribute": attr,
                        "original_problematic_excerpt": excerpt,
                        "status": "discarded",
                        "context_reasoning": f"Term '{excerpt}' is explicitly defined in the SRS Project Glossary. Flagged concern is a contextual false positive.",
                        "confidence": 0.99
                    })
                    discarded.append(d)
                else:
                    evaluations.append({
                        "defect_id": did,
                        "attribute": attr,
                        "original_problematic_excerpt": excerpt,
                        "status": "justified",
                        "context_reasoning": f"The excerpt '{excerpt}' is not quantified or clarified anywhere in the surrounding SRS context and represents an actionable quality flaw.",
                        "confidence": 0.95
                    })
                    retained.append(d)

            summary = f"Evaluated {len(candidate_defects)} candidate shortcomings against SRS context. Retained {len(retained)} justified defects; discarded {len(discarded)} contextual false positives."

            return json.dumps({
                "req_id": req_id,
                "reasoning_summary": summary,
                "evaluations": evaluations,
                "retained_defects": retained,
                "discarded_defects": discarded
            })

        # Check Layer 1: Document Understanding, Scoring & Shortcoming Identification
        if "expert requirements quality engineer" in system_prompt.lower() or "quality attributes" in system_prompt.lower():
            req_id_match = re.search(r"Requirement ID:\s*(\S+)", user_prompt)
            req_id = req_id_match.group(1) if req_id_match else "REQ-TARGET"

            req_text_match = re.search(r'Requirement Text:\s*"([^"]+)"', user_prompt)
            req_text = req_text_match.group(1) if req_text_match else user_prompt

            shortcomings = []
            scores = {
                "Unambiguity": 9.0,
                "Completeness": 9.0,
                "Consistency": 9.5,
                "Conformance": 9.0,
                "Correctness": 9.5,
                "Singularity": 9.0,
                "Verifiability/Feasibility": 9.0,
            }

            req_lower = req_text.lower()

            if "quickly" in req_lower:
                scores["Unambiguity"] = 5.5
                scores["Verifiability/Feasibility"] = 6.0
                shortcomings.append({
                    "defect_id": "DEF-001",
                    "attribute": "Unambiguity",
                    "problematic_excerpt": "quickly",
                    "explanation": "Subjective adverb 'quickly' lacks quantifiable time bounds (e.g. milliseconds).",
                    "severity": "high",
                })

            if "intuitive" in req_lower or "intuitively" in req_lower:
                scores["Unambiguity"] = min(scores["Unambiguity"], 6.0)
                scores["Verifiability/Feasibility"] = min(scores["Verifiability/Feasibility"], 6.5)
                shortcomings.append({
                    "defect_id": f"DEF-{len(shortcomings)+1:03d}",
                    "attribute": "Unambiguity",
                    "problematic_excerpt": "intuitively labeled" if "intuitively labeled" in req_lower else "intuitive",
                    "explanation": "Subjective descriptor cannot be objectively tested or measured under ISO/IEC/IEEE 29148.",
                    "severity": "medium",
                })

            if "easy to use" in req_lower or "high quality look" in req_lower:
                scores["Verifiability/Feasibility"] = min(scores["Verifiability/Feasibility"], 5.5)
                shortcomings.append({
                    "defect_id": f"DEF-{len(shortcomings)+1:03d}",
                    "attribute": "Verifiability/Feasibility",
                    "problematic_excerpt": "easy to use",
                    "explanation": "Non-quantifiable qualitative claim cannot be validated through a finite test procedure.",
                    "severity": "high",
                })

            if "as well as" in req_lower or "and shall also" in req_lower or (" and " in req_lower and req_lower.count("shall") > 1):
                scores["Singularity"] = 5.0
                shortcomings.append({
                    "defect_id": f"DEF-{len(shortcomings)+1:03d}",
                    "attribute": "Singularity",
                    "problematic_excerpt": "as well as" if "as well as" in req_lower else "and shall also",
                    "explanation": "Bundles multiple distinct functional responsibilities into a single compound statement.",
                    "severity": "medium",
                })

            if "if applicable" in req_lower or "etc." in req_lower:
                scores["Completeness"] = 5.5
                shortcomings.append({
                    "defect_id": f"DEF-{len(shortcomings)+1:03d}",
                    "attribute": "Completeness",
                    "problematic_excerpt": "if applicable",
                    "explanation": "Open-ended conditional clause leaves branch criteria completely undefined.",
                    "severity": "high",
                })

            # Check if text contains 'vital anomaly' in isolation
            if "vital anomaly" in req_lower and not shortcomings:
                # Potential candidate flag that Layer 2 will test against context
                scores["Unambiguity"] = 7.5
                shortcomings.append({
                    "defect_id": "DEF-001",
                    "attribute": "Unambiguity",
                    "problematic_excerpt": "Vital Anomaly",
                    "explanation": "Medical anomaly threshold requires verification against clinical definitions.",
                    "severity": "low",
                })

            overall_score = round(sum(scores.values()) / len(scores), 1)

            attribute_scores_list = [
                {"attribute": attr, "score": score, "rationale": f"Evaluated under ISO/IEC/IEEE 29148 {attr} criteria."}
                for attr, score in scores.items()
            ]

            return json.dumps({
                "req_id": req_id,
                "document_understanding_summary": "Requirement articulates functional behavior within the clinical monitoring module.",
                "attribute_scores": attribute_scores_list,
                "overall_quality_score": overall_score,
                "shortcomings": shortcomings,
            })

        return "{}"


def resolve_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    allow_mock: bool = False,
) -> BaseLLMClient:
    """
    Resolves the required LLM client.
    Because this is an LLM-Based Quality Analyzer, a live LLM is compulsory.
    Auto-detects between Google Gemini and OpenAI if provider is not explicitly set.
    """
    p = (provider or "").strip().lower()

    if p == "mock":
        if not allow_mock:
            raise ValueError(
                "Mock client is restricted to offline testing. "
                "To use real LLM analysis, set GEMINI_API_KEY or OPENAI_API_KEY, "
                "or pass allow_mock=True."
            )
        return MockLLMClient()

    if p == "gemini":
        return GeminiLLMClient(model_name=model or "gemini-2.5-flash")

    if p == "openai":
        return OpenAILLMClient(model_name=model or "gpt-4o")

    # If provider is not specified, auto-detect available keys
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        return GeminiLLMClient(model_name=model or "gemini-2.5-flash")
    elif openai_key:
        return OpenAILLMClient(model_name=model or "gpt-4o")
    else:
        raise ValueError(
            "\n" + "=" * 76 + "\n"
            "[MANDATORY LLM SETUP REQUIRED]\n"
            "This system is an LLM-Based Software Requirement Quality Analyzer.\n"
            "A live LLM backend (Google Gemini or OpenAI) is compulsory to perform\n"
            "requirement quality scoring, reasoning, refinement, and validation.\n\n"
            "Please configure at least one API key in your environment or .env file:\n\n"
            "  Option 1 (Google Gemini - Recommended):\n"
            '    PowerShell: $env:GEMINI_API_KEY = "your-key"\n'
            '    Bash/Linux: export GEMINI_API_KEY="your-key"\n\n'
            "  Option 2 (OpenAI):\n"
            '    PowerShell: $env:OPENAI_API_KEY = "your-key"\n'
            '    Bash/Linux: export OPENAI_API_KEY="your-key"\n\n'
            "  Option 3 (Offline CI Testing Only):\n"
            "    Pass --provider mock to run synthetic tests.\n"
            + "=" * 76
        )
