"""
srs_evolution.change_classifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
LLM-based change extraction and semantic classification engine.
Categorizes empirical modifications between Version N and Version N+1
into the formal SQAM research taxonomy, rigorously separating ISO 29148 quality repairs
from stakeholder scope changes and editorial updates.
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Optional

from sqam_analyzer.diff_utils import compute_word_diff
from sqam_analyzer.llm_provider import BaseLLMClient, MockLLMClient
from srs_evolution.models import (
    AlignedRequirementPair,
    AlignmentType,
    ChangeCategory,
    HistoricalChangeRecord,
    QUALITY_REFINEMENT_CATEGORIES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

CHANGE_CLASSIFIER_SYSTEM_PROMPT = """You are an expert Requirements Quality Researcher and Empirical Evolution Auditor.
Your task is to analyze the modification made to a software requirement between two historical SRS versions (Version N and Version N+1).

You must categorize the empirical modification into EXACTLY ONE of the following taxonomy categories:

1. UNCHANGED:
   The requirement is semantically, functionally, and textually identical (or only differs by trivial whitespace).

2. EDITORIAL_TEXTUAL:
   Superficial phrasing, spelling, capitalization, grammar, or formatting fixes that have ZERO semantic or quality impact.

3. AMBIGUITY_REDUCTION (Quality Refinement):
   Eliminating vague adjectives ("intuitive", "appropriate", "robust", "flexible"), subjective adverbs ("quickly", "promptly"), open-ended phrases ("etc.", "including but not limited to"), or ambiguous pronouns.

4. COMPLETENESS_IMPROVEMENT (Quality Refinement):
   Adding missing operational conditions, explicit triggers, omitted input/output parameters, or error/exception handling paths.

5. CONSTRAINT_REFINEMENT (Quality Refinement):
   Adding or refining concrete, measurable, testable performance or operational constraints (e.g., latency bounds, throughput limits, frequency in Hz, proximity thresholds, or ISO/industry standard references).

6. CONSISTENCY_CORRECTION (Quality Refinement):
   Harmonizing terminology, resolving contradictions with surrounding requirements, or fixing numerical/unit clashes.

7. FUNCTIONAL_SCOPE_CHANGE:
   Stakeholder-driven modification that alters the core business logic, adds new functional capabilities, or contracts existing scope. (This is a feature/scope change, NOT a quality repair of an existing requirement).

8. REQUIREMENT_ADDED:
   A completely new requirement introduced in Version N+1.

9. REQUIREMENT_DELETED:
   An existing requirement deprecated or removed in Version N.

IMPORTANT:
- Distinguish carefully between a Quality Refinement (improving the quality of how a requirement is expressed) and a Functional Scope Change (changing what the system does).
- Return ONLY a strict JSON object matching the requested schema.
"""

CHANGE_CLASSIFIER_USER_TEMPLATE = """Classify the empirical requirement modification between Version N and Version N+1.

Requirement ID: {req_id}

### VERSION N (EARLIER):
"{text_v1}"

### VERSION N+1 (LATER):
"{text_v2}"

### INLINE WORD DIFF:
{diff_markup}

### OUTPUT FORMAT
Provide your response as a strict JSON object:
{{
  "req_id": "{req_id}",
  "change_category": "<One of: UNCHANGED, EDITORIAL_TEXTUAL, AMBIGUITY_REDUCTION, COMPLETENESS_IMPROVEMENT, CONSTRAINT_REFINEMENT, CONSISTENCY_CORRECTION, FUNCTIONAL_SCOPE_CHANGE, REQUIREMENT_ADDED, REQUIREMENT_DELETED>",
  "summary_of_change": "<Concise 1-2 sentence explanation of what was modified>",
  "confidence": 0.95
}}
"""


class ChangeClassifier:
    """
    Classifies the empirical nature of changes between aligned requirement versions.
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
    ):
        self.llm_client = llm_client or MockLLMClient()
        self.system_prompt = system_prompt or CHANGE_CLASSIFIER_SYSTEM_PROMPT
        self.user_prompt_template = user_prompt_template or CHANGE_CLASSIFIER_USER_TEMPLATE

    def classify_pair(
        self,
        pair: AlignedRequirementPair,
        temperature: float = 0.0,
    ) -> HistoricalChangeRecord:
        """
        Classifies an aligned pair of requirements from Version N to Version N+1.
        Applies fast short-circuits for additions, deletions, and identical statements.
        """
        req_id = pair.req_id_v1 or pair.req_id_v2 or "REQ-UNKNOWN"

        # Case 1: Newly Added in Version N+1
        if pair.alignment_type == AlignmentType.ADDED or not pair.text_v1:
            return HistoricalChangeRecord(
                req_id=req_id,
                req_id_v_n=None,
                req_id_v_n1=pair.req_id_v2,
                text_v_n=None,
                text_v_n1=pair.text_v2,
                change_category=ChangeCategory.REQUIREMENT_ADDED,
                summary_of_change="New requirement introduced in Version N+1.",
                detailed_diff=f"[+{pair.text_v2}+]",
                is_quality_refinement=False,
                confidence=1.0,
            )

        # Case 2: Deleted in Version N+1
        if pair.alignment_type == AlignmentType.DELETED or not pair.text_v2:
            return HistoricalChangeRecord(
                req_id=req_id,
                req_id_v_n=pair.req_id_v1,
                req_id_v_n1=None,
                text_v_n=pair.text_v1,
                text_v_n1=None,
                change_category=ChangeCategory.REQUIREMENT_DELETED,
                summary_of_change="Requirement was deprecated or removed in Version N+1.",
                detailed_diff=f"[-{pair.text_v1}-]",
                is_quality_refinement=False,
                confidence=1.0,
            )

        # Case 3: Identical Text (Zero-token short-circuit)
        if pair.text_v1.strip() == pair.text_v2.strip():
            return HistoricalChangeRecord(
                req_id=req_id,
                req_id_v_n=pair.req_id_v1,
                req_id_v_n1=pair.req_id_v2,
                text_v_n=pair.text_v1,
                text_v_n1=pair.text_v2,
                change_category=ChangeCategory.UNCHANGED,
                summary_of_change="Requirement text is identical across versions.",
                detailed_diff=pair.text_v1,
                is_quality_refinement=False,
                confidence=1.0,
            )

        # Compute word-level diff for context
        diff_res = compute_word_diff(pair.text_v1, pair.text_v2)

        # Check if using MockLLMClient to provide realistic heuristic classification
        if isinstance(self.llm_client, MockLLMClient):
            return self._heuristic_mock_classify(pair, diff_res.diff_markup)

        # Real LLM Classification
        formatted_user_prompt = self.user_prompt_template.format(
            req_id=req_id,
            text_v1=pair.text_v1,
            text_v2=pair.text_v2,
            diff_markup=diff_res.diff_markup,
        )

        try:
            raw_result = self.llm_client.generate_text(
                system_prompt=self.system_prompt,
                user_prompt=formatted_user_prompt,
                temperature=temperature,
            )
            from sqam_analyzer.llm_provider import extract_json_from_response
            data = extract_json_from_response(raw_result)
            cat_str = data.get("change_category", "EDITORIAL_TEXTUAL").upper()
            category = ChangeCategory(cat_str) if cat_str in ChangeCategory.__members__ else ChangeCategory.EDITORIAL_TEXTUAL
            summary = data.get("summary_of_change", "Modified requirement text.")
            confidence = float(data.get("confidence", 0.9))
        except Exception as e:
            logger.warning("LLM change classification failed for %s (%s); falling back to heuristic.", req_id, e)
            return self._heuristic_mock_classify(pair, diff_res.diff_markup)

        is_quality = category in QUALITY_REFINEMENT_CATEGORIES

        return HistoricalChangeRecord(
            req_id=req_id,
            req_id_v_n=pair.req_id_v1,
            req_id_v_n1=pair.req_id_v2,
            text_v_n=pair.text_v1,
            text_v_n1=pair.text_v2,
            change_category=category,
            summary_of_change=summary,
            detailed_diff=diff_res.diff_markup,
            is_quality_refinement=is_quality,
            confidence=confidence,
        )

    def classify_all(
        self,
        pairs: List[AlignedRequirementPair],
        temperature: float = 0.0,
    ) -> List[HistoricalChangeRecord]:
        """Classifies a batch of aligned requirement pairs."""
        records = []
        for pair in pairs:
            record = self.classify_pair(pair, temperature=temperature)
            records.append(record)
        return records

    def _heuristic_mock_classify(
        self,
        pair: AlignedRequirementPair,
        diff_markup: str,
    ) -> HistoricalChangeRecord:
        """Deterministic rule-based classification for offline testing and evaluation."""
        v1_lower = (pair.text_v1 or "").lower()
        v2_lower = (pair.text_v2 or "").lower()
        req_id = pair.req_id_v1 or pair.req_id_v2 or "REQ-01"

        # Heuristic 1: Ambiguity Reduction
        vague_terms = ["quickly", "promptly", "intuitive", "easy to use", "appropriate", "adequate", "clean", "fast"]
        if any(term in v1_lower and term not in v2_lower for term in vague_terms):
            return HistoricalChangeRecord(
                req_id=req_id,
                req_id_v_n=pair.req_id_v1,
                req_id_v_n1=pair.req_id_v2,
                text_v_n=pair.text_v1,
                text_v_n1=pair.text_v2,
                change_category=ChangeCategory.AMBIGUITY_REDUCTION,
                summary_of_change="Eliminated subjective or ambiguous terms and replaced with concrete specifications.",
                detailed_diff=diff_markup,
                is_quality_refinement=True,
                confidence=0.98,
            )

        # Heuristic 2: Constraint Refinement (numbers, Hz, ms, seconds, standards)
        constraint_terms = ["millisecond", "ms", "hz", "second", "meters", "standard", "iso", "uic"]
        if any(term in v2_lower and term not in v1_lower for term in constraint_terms):
            return HistoricalChangeRecord(
                req_id=req_id,
                req_id_v_n=pair.req_id_v1,
                req_id_v_n1=pair.req_id_v2,
                text_v_n=pair.text_v1,
                text_v_n1=pair.text_v2,
                change_category=ChangeCategory.CONSTRAINT_REFINEMENT,
                summary_of_change="Added measurable operational constraints or numerical performance limits.",
                detailed_diff=diff_markup,
                is_quality_refinement=True,
                confidence=0.95,
            )

        # Heuristic 3: Completeness Improvement
        completeness_terms = ["if obstacle", "when", "error", "failsafe", "exception"]
        if any(term in v2_lower and term not in v1_lower for term in completeness_terms):
            return HistoricalChangeRecord(
                req_id=req_id,
                req_id_v_n=pair.req_id_v1,
                req_id_v_n1=pair.req_id_v2,
                text_v_n=pair.text_v1,
                text_v_n1=pair.text_v2,
                change_category=ChangeCategory.COMPLETENESS_IMPROVEMENT,
                summary_of_change="Specified missing conditional trigger or error handling branch.",
                detailed_diff=diff_markup,
                is_quality_refinement=True,
                confidence=0.92,
            )

        # Heuristic 4: Minor Editorial
        if len(v1_lower.split()) == len(v2_lower.split()):
            return HistoricalChangeRecord(
                req_id=req_id,
                req_id_v_n=pair.req_id_v1,
                req_id_v_n1=pair.req_id_v2,
                text_v_n=pair.text_v1,
                text_v_n1=pair.text_v2,
                change_category=ChangeCategory.EDITORIAL_TEXTUAL,
                summary_of_change="Minor stylistic or grammatical rephrasing.",
                detailed_diff=diff_markup,
                is_quality_refinement=False,
                confidence=0.88,
            )

        # Default fallback: Functional Scope Change
        return HistoricalChangeRecord(
            req_id=req_id,
            req_id_v_n=pair.req_id_v1,
            req_id_v_n1=pair.req_id_v2,
            text_v_n=pair.text_v1,
            text_v_n1=pair.text_v2,
            change_category=ChangeCategory.FUNCTIONAL_SCOPE_CHANGE,
            summary_of_change="Modified functional capabilities or altered requirement scope.",
            detailed_diff=diff_markup,
            is_quality_refinement=False,
            confidence=0.85,
        )
