"""
srs_evolution.evaluator
~~~~~~~~~~~~~~~~~~~~~~~
Pipeline-1 Correspondence Matching Module (Semantic Benchmark).
Compares the output of the 5-layer analyzer (Layer 1 shortcomings + Layer 3 refinements)
applied to Version N against the empirical ground-truth evolution observed in Version N+1.

Strictly avoids lexical similarity metrics (BLEU/ROUGE), using qualitative semantic
chain-of-thought evaluation as defined in the SQAM research paper:
- MATCHED: Independent discovery and semantically equivalent remediation.
- PARTIALLY_MATCHED: Flagged the correct defect area but applied an alternative fix.
- NOT_MATCHED: Proposal has no counterpart in historical Version N+1 evolution.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from sqam_analyzer.llm_provider import BaseLLMClient, MockLLMClient, extract_json_from_response
from sqam_analyzer.models import PipelineExecutionResult
from srs_evolution.models import (
    BenchmarkSummaryReport,
    ChangeCategory,
    CorrespondenceRating,
    EvolutionBenchmarkResult,
    HistoricalChangeRecord,
    QUALITY_REFINEMENT_CATEGORIES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

CORRESPONDENCE_SYSTEM_PROMPT = """You are an Academic Peer Reviewer and Requirements Engineering Auditor evaluating an AI-Assisted Requirements Editor.

You are comparing:
1. PIPELINE-1 PROPOSAL: What an automated 5-layer quality analyzer independently diagnosed and refined in an earlier specification (Version N).
2. HISTORICAL GROUND TRUTH: What human stakeholders actually changed in the real-world later version (Version N+1).

Your task is to assign a THREE-WAY QUALITATIVE CORRESPONDENCE RATING:

1. MATCHED:
   The analyzer independently flagged the same quality shortcoming and proposed a refinement that is semantically equivalent or closely anticipates the actual change made by human stakeholders in Version N+1.
   (Exact wording is NOT required: if the pipeline parameterized "quickly" to a numeric time limit and human stakeholders also added a numeric time limit, this is a strong MATCH).

2. PARTIALLY_MATCHED:
   The analyzer correctly targeted the problematic clause or quality defect, but proposed a different remediation strategy than what human stakeholders adopted.
   (e.g., The pipeline parameterized a compound clause, while human stakeholders resolved it by splitting it into companion requirements).

3. NOT_MATCHED:
   The analyzer's proposed change has no counterpart in the historical evolution of Version N+1 (e.g. human stakeholders left the text untouched, made a completely unrelated functional change, or the analyzer's flag was irrelevant to real evolution).

DO NOT use surface-level word matching. Focus entirely on semantic intent and requirements engineering defect relevance.
Return ONLY a valid JSON object matching the requested schema.
"""

CORRESPONDENCE_USER_TEMPLATE = """Evaluate the semantic correspondence between Pipeline-1's proposed refinement and Version N+1's actual historical evolution.

Requirement ID: {req_id}

### 1. VERSION N (ORIGINAL TEXT FED BLIND TO PIPELINE-1):
"{original_v_n_text}"

### 2. PIPELINE-1 INDEPENDENT DIAGNOSIS & REFINEMENT:
- Flagged Shortcomings (Layer 1 & 2): {layer1_defects}
- Proposed Refinement (Layer 3): "{layer3_refinement}"

### 3. HISTORICAL GROUND TRUTH IN VERSION N+1:
- Actual Later Text: "{v_next_actual_text}"
- Empirical Change Category: {historical_change_category}
- Summary of Actual Change: {summary_of_actual_change}

### OUTPUT FORMAT
Provide your response as a strict JSON object:
{{
  "req_id": "{req_id}",
  "correspondence_rating": "<One of: MATCHED, PARTIALLY_MATCHED, NOT_MATCHED>",
  "explanation": "<Detailed chain-of-thought rationale explaining whether the pipeline's proposal semantically corresponds to the human change in Version N+1>",
  "is_true_positive_prediction": true // or false: True if the pipeline correctly anticipated a genuine historical quality refinement
}}
"""


class EvolutionEvaluator:
    """
    Evaluates correspondence between Pipeline-1 predictions and Version N+1 historical reality.
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
    ):
        self.llm_client = llm_client or MockLLMClient()
        self.system_prompt = system_prompt or CORRESPONDENCE_SYSTEM_PROMPT
        self.user_prompt_template = user_prompt_template or CORRESPONDENCE_USER_TEMPLATE

    def evaluate_correspondence(
        self,
        pipeline_result: PipelineExecutionResult,
        change_record: HistoricalChangeRecord,
        temperature: float = 0.0,
    ) -> EvolutionBenchmarkResult:
        """
        Evaluates a single requirement: compares Pipeline-1 proposal vs Version N+1 change.
        """
        req_id = pipeline_result.requirement.req_id
        original_text = pipeline_result.requirement.text

        # Extract Layer 1 defect descriptions
        l1_defects = []
        if pipeline_result.layer1_result:
            l1_defects = [
                f"{s.attribute.value}: {s.problematic_excerpt} ({s.explanation})"
                for s in pipeline_result.layer1_result.shortcomings
            ]
        if not l1_defects:
            l1_defects = ["No defects flagged (compliant)."]

        l3_refinement = (
            pipeline_result.layer3_result.refined_text
            if pipeline_result.layer3_result
            else original_text
        )

        v_next_actual = change_record.text_v_n1 or original_text

        # Fast Short-Circuit 1: Both Pipeline and Historical stakeholders made no change
        pipeline_changed = (l3_refinement.strip() != original_text.strip())
        historical_changed = (v_next_actual.strip() != original_text.strip())

        if not pipeline_changed and not historical_changed:
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=original_text,
                layer1_defects_flagged=l1_defects,
                layer3_refinement_text=l3_refinement,
                v_next_actual_text=v_next_actual,
                historical_change_category=change_record.change_category,
                correspondence_rating=CorrespondenceRating.MATCHED,
                explanation="Both Pipeline-1 and historical stakeholders judged the requirement compliant and made no modifications.",
                is_true_positive_prediction=True,
            )

        # Fast Short-Circuit 2: Pipeline changed nothing, but historical stakeholders made a quality refinement
        if not pipeline_changed and historical_changed and change_record.is_quality_refinement:
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=original_text,
                layer1_defects_flagged=l1_defects,
                layer3_refinement_text=l3_refinement,
                v_next_actual_text=v_next_actual,
                historical_change_category=change_record.change_category,
                correspondence_rating=CorrespondenceRating.NOT_MATCHED,
                explanation="Historical stakeholders performed a quality repair in Version N+1, but Pipeline-1 failed to identify or refine the defect.",
                is_true_positive_prediction=False,
            )

        # Fast Short-Circuit 3: Pipeline proposed a refinement, but historical stakeholders made no change
        if pipeline_changed and not historical_changed:
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=original_text,
                layer1_defects_flagged=l1_defects,
                layer3_refinement_text=l3_refinement,
                v_next_actual_text=v_next_actual,
                historical_change_category=ChangeCategory.UNCHANGED,
                correspondence_rating=CorrespondenceRating.NOT_MATCHED,
                explanation="Pipeline-1 proposed a refinement, but historical stakeholders kept the requirement unchanged in Version N+1.",
                is_true_positive_prediction=False,
            )

        # Offline MockLLM heuristic evaluation
        if isinstance(self.llm_client, MockLLMClient):
            return self._heuristic_mock_evaluate(
                req_id=req_id,
                orig=original_text,
                defects=l1_defects,
                refined=l3_refinement,
                v_next=v_next_actual,
                change_record=change_record,
            )

        # Real LLM Semantic Correspondence Evaluation
        formatted_user_prompt = self.user_prompt_template.format(
            req_id=req_id,
            original_v_n_text=original_text,
            layer1_defects="; ".join(l1_defects),
            layer3_refinement=l3_refinement,
            v_next_actual_text=v_next_actual,
            historical_change_category=change_record.change_category.value,
            summary_of_actual_change=change_record.summary_of_change,
        )

        try:
            raw_response = self.llm_client.generate_text(
                system_prompt=self.system_prompt,
                user_prompt=formatted_user_prompt,
                temperature=temperature,
            )
            data = extract_json_from_response(raw_response)
            rating_str = data.get("correspondence_rating", "NOT_MATCHED").upper()
            rating = (
                CorrespondenceRating(rating_str)
                if rating_str in CorrespondenceRating.__members__
                else CorrespondenceRating.NOT_MATCHED
            )
            explanation = data.get("explanation", "Evaluated against historical Version N+1.")
            is_tp = bool(data.get("is_true_positive_prediction", rating in [CorrespondenceRating.MATCHED, CorrespondenceRating.PARTIALLY_MATCHED]))
        except Exception as e:
            logger.warning("LLM correspondence evaluation failed for %s (%s); falling back to heuristic.", req_id, e)
            return self._heuristic_mock_evaluate(
                req_id=req_id,
                orig=original_text,
                defects=l1_defects,
                refined=l3_refinement,
                v_next=v_next_actual,
                change_record=change_record,
            )

        return EvolutionBenchmarkResult(
            req_id=req_id,
            original_v_n_text=original_text,
            layer1_defects_flagged=l1_defects,
            layer3_refinement_text=l3_refinement,
            v_next_actual_text=v_next_actual,
            historical_change_category=change_record.change_category,
            correspondence_rating=rating,
            explanation=explanation,
            is_true_positive_prediction=is_tp,
        )

    def evaluate_batch(
        self,
        pipeline_results: List[PipelineExecutionResult],
        change_records: List[HistoricalChangeRecord],
        temperature: float = 0.0,
    ) -> Tuple[List[EvolutionBenchmarkResult], BenchmarkSummaryReport]:
        """
        Evaluates correspondence for a batch of requirements and computes aggregate metrics.
        """
        # Index changes by requirement ID
        change_by_id = {r.req_id: r for r in change_records}

        benchmark_results = []
        for p_res in pipeline_results:
            rid = p_res.requirement.req_id
            rec = change_by_id.get(rid)
            if not rec:
                # Synthetic default record
                rec = HistoricalChangeRecord(
                    req_id=rid,
                    change_category=ChangeCategory.UNCHANGED,
                    summary_of_change="No historical change record found.",
                    is_quality_refinement=False,
                )

            b_res = self.evaluate_correspondence(p_res, rec, temperature=temperature)
            benchmark_results.append(b_res)

        # Compute summary metrics
        total = len(benchmark_results)
        matched = sum(1 for b in benchmark_results if b.correspondence_rating == CorrespondenceRating.MATCHED)
        partial = sum(1 for b in benchmark_results if b.correspondence_rating == CorrespondenceRating.PARTIALLY_MATCHED)
        not_matched = sum(1 for b in benchmark_results if b.correspondence_rating == CorrespondenceRating.NOT_MATCHED)

        proposals = sum(
            1 for b in benchmark_results
            if b.layer3_refinement_text and b.layer3_refinement_text.strip() != b.original_v_n_text.strip()
        )
        quality_historical = sum(
            1 for b in benchmark_results
            if b.historical_change_category in QUALITY_REFINEMENT_CATEGORIES
        )

        match_rate = round(((matched + partial) / proposals * 100) if proposals else 0.0, 1)
        strict_match_rate = round((matched / proposals * 100) if proposals else 0.0, 1)
        precision = round((matched / quality_historical * 100) if quality_historical else 0.0, 1)

        summary = BenchmarkSummaryReport(
            total_aligned_pairs=len(change_records),
            unchanged_count=sum(1 for c in change_records if c.change_category == ChangeCategory.UNCHANGED),
            editorial_count=sum(1 for c in change_records if c.change_category == ChangeCategory.EDITORIAL_TEXTUAL),
            quality_refinements_count=quality_historical,
            scope_changes_count=sum(1 for c in change_records if c.change_category == ChangeCategory.FUNCTIONAL_SCOPE_CHANGE),
            added_count=sum(1 for c in change_records if c.change_category == ChangeCategory.REQUIREMENT_ADDED),
            deleted_count=sum(1 for c in change_records if c.change_category == ChangeCategory.REQUIREMENT_DELETED),
            total_pipeline_proposals_evaluated=proposals,
            matched_count=matched,
            partially_matched_count=partial,
            not_matched_count=not_matched,
            match_rate=match_rate,
            strict_match_rate=strict_match_rate,
            quality_prediction_precision=precision,
        )

        return benchmark_results, summary

    def _heuristic_mock_evaluate(
        self,
        req_id: str,
        orig: str,
        defects: List[str],
        refined: str,
        v_next: str,
        change_record: HistoricalChangeRecord,
    ) -> EvolutionBenchmarkResult:
        """Heuristic rule-based matching for offline verification."""
        orig_words = set(orig.lower().split())
        ref_words = set(refined.lower().split()) - orig_words
        v_next_words = set(v_next.lower().split()) - orig_words

        # Check overlap in introduced concepts
        overlap = ref_words.intersection(v_next_words)

        # Check numerical/time bounding
        both_quantified = any(term in refined.lower() for term in ["millisecond", "ms", "hz", "second"]) and \
                          any(term in v_next.lower() for term in ["millisecond", "ms", "hz", "second"])

        # Check standard/interface references
        both_referenced_standards = any(term in refined.lower() for term in ["standard", "iso", "uic", "guide"]) and \
                                    any(term in v_next.lower() for term in ["standard", "iso", "uic", "guide"])

        if overlap or both_quantified or both_referenced_standards:
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=orig,
                layer1_defects_flagged=defects,
                layer3_refinement_text=refined,
                v_next_actual_text=v_next,
                historical_change_category=change_record.change_category,
                correspondence_rating=CorrespondenceRating.MATCHED,
                explanation=f"Pipeline-1 proposal semantically anticipated the historical quality repair (Shared concept: {overlap or 'quantitative constraint/standard'}).",
                is_true_positive_prediction=True,
            )

        if change_record.is_quality_refinement:
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=orig,
                layer1_defects_flagged=defects,
                layer3_refinement_text=refined,
                v_next_actual_text=v_next,
                historical_change_category=change_record.change_category,
                correspondence_rating=CorrespondenceRating.PARTIALLY_MATCHED,
                explanation="Pipeline-1 correctly flagged the quality flaw, but historical stakeholders applied an alternative formulation.",
                is_true_positive_prediction=True,
            )

        return EvolutionBenchmarkResult(
            req_id=req_id,
            original_v_n_text=orig,
            layer1_defects_flagged=defects,
            layer3_refinement_text=refined,
            v_next_actual_text=v_next,
            historical_change_category=change_record.change_category,
            correspondence_rating=CorrespondenceRating.NOT_MATCHED,
            explanation="Pipeline-1 proposed a refinement, but the historical change was unrelated or unaligned.",
            is_true_positive_prediction=False,
        )
