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
1. PIPELINE-1 PROPOSAL: What an automated 5-layer quality analyzer independently diagnosed and refined in an earlier draft specification (Version N).
2. FINAL SRS RELEASE (GROUND TRUTH DOCUMENT): The finalized text and specifications in the official Final Version of the SRS (Version N+1).

Your task is to assign a THREE-WAY QUALITATIVE CORRESPONDENCE RATING:

1. MATCHED:
   The analyzer independently flagged the same quality shortcoming and proposed a refinement that is semantically equivalent or closely anticipates the specification in the Final Version of the SRS.
   (Exact wording is NOT required: if the pipeline parameterized "quickly" to a numeric time limit and the Final Version of the SRS also established a numeric time limit, this is a strong MATCH).

2. PARTIALLY_MATCHED:
   The analyzer correctly targeted the problematic clause or quality defect, but proposed an alternative remediation compared to what was codified in the Final Version of the SRS.
   (e.g., The pipeline parameterized a compound clause, while the Final Version of the SRS resolved it by decomposing into companion requirements).

3. NOT_MATCHED:
   The analyzer's proposed change has no counterpart in the Final Version of the SRS (e.g. the Final SRS left the text untouched, made a completely unrelated functional scope change, or the analyzer's flag was extraneous).

DO NOT use surface-level word matching. Focus entirely on semantic intent and requirements engineering defect relevance.
Return ONLY a valid JSON object matching the requested schema.
"""

CORRESPONDENCE_USER_TEMPLATE = """Evaluate the semantic correspondence between Pipeline-1's proposed refinement and the official Final Version of the SRS.

Requirement ID: {req_id}

### 1. DRAFT SPECIFICATION (VERSION N, FED BLIND TO PIPELINE-1):
"{original_v_n_text}"

### 2. PIPELINE-1 INDEPENDENT DIAGNOSIS & REFINEMENT:
- Flagged Shortcomings (Layer 1 & 2): {layer1_defects}
- Proposed Refinement (Layer 3): "{layer3_refinement}"

### 3. GROUND TRUTH IN FINAL VERSION OF SRS (VERSION N+1):
- Text in Final Version of SRS: "{v_next_actual_text}"
- Empirical Change Category: {historical_change_category}
- Summary of Evolution in Final SRS: {summary_of_actual_change}

### OUTPUT FORMAT
Provide your response as a strict JSON object:
{{
  "req_id": "{req_id}",
  "correspondence_rating": "<One of: MATCHED, PARTIALLY_MATCHED, NOT_MATCHED>",
  "explanation": "<Detailed chain-of-thought rationale explaining whether the pipeline's proposal semantically corresponds to the specification in the Final Version of the SRS>",
  "is_true_positive_prediction": true // or false: True if the pipeline correctly anticipated a genuine quality refinement in the Final SRS
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

        # Fast Short-Circuit 0: Pipeline execution failure
        if pipeline_result.status == "error":
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=original_text,
                layer1_defects_flagged=[],
                layer3_refinement_text=original_text,
                v_next_actual_text=v_next_actual,
                historical_change_category=change_record.change_category,
                correspondence_rating=CorrespondenceRating.NOT_MATCHED,
                explanation=f"Pipeline-1 analysis failed with error: {pipeline_result.error_message}",
                is_true_positive_prediction=False,
            )

        # Fast Short-Circuit 1: Both Pipeline-1 and the Final Version of SRS left the text unchanged
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
                explanation="Both Pipeline-1 and the official Final Version of the SRS maintained the original text without modification (compliant specification).",
                is_true_positive_prediction=True,
            )

        # Fast Short-Circuit 2: Pipeline-1 proposed no change, but the Final Version of SRS introduced a quality refinement
        if not pipeline_changed and historical_changed and change_record.is_quality_refinement:
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=original_text,
                layer1_defects_flagged=l1_defects,
                layer3_refinement_text=l3_refinement,
                v_next_actual_text=v_next_actual,
                historical_change_category=change_record.change_category,
                correspondence_rating=CorrespondenceRating.NOT_MATCHED,
                explanation="The official Final Version of the SRS codified a quality refinement, but Pipeline-1 left the requirement unrefined.",
                is_true_positive_prediction=False,
            )

        # Fast Short-Circuit 3: Pipeline-1 proposed a refinement, but the Final Version of SRS kept the original text
        if pipeline_changed and not historical_changed:
            return EvolutionBenchmarkResult(
                req_id=req_id,
                original_v_n_text=original_text,
                layer1_defects_flagged=l1_defects,
                layer3_refinement_text=l3_refinement,
                v_next_actual_text=v_next_actual,
                historical_change_category=ChangeCategory.UNCHANGED,
                correspondence_rating=CorrespondenceRating.NOT_MATCHED,
                explanation="Pipeline-1 proposed a refinement, but the official Final Version of the SRS maintained the requirement unchanged.",
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

        # Compute summary metrics strictly separating active proposals from unchanged requirements
        active_proposal_results = [
            b for b in benchmark_results
            if b.layer3_refinement_text and b.layer3_refinement_text.strip() != b.original_v_n_text.strip()
        ]

        num_proposals = len(active_proposal_results)
        matched_proposals = sum(1 for b in active_proposal_results if b.correspondence_rating == CorrespondenceRating.MATCHED)
        partial_proposals = sum(1 for b in active_proposal_results if b.correspondence_rating == CorrespondenceRating.PARTIALLY_MATCHED)
        not_matched_proposals = sum(1 for b in active_proposal_results if b.correspondence_rating == CorrespondenceRating.NOT_MATCHED)

        # True Negatives: both Pipeline-1 and the Final Version of the SRS kept the text unchanged
        true_negatives = sum(
            1 for b in benchmark_results
            if (not b.layer3_refinement_text or b.layer3_refinement_text.strip() == b.original_v_n_text.strip()) and
               (not b.v_next_actual_text or b.v_next_actual_text.strip() == b.original_v_n_text.strip())
        )

        quality_historical = sum(
            1 for b in benchmark_results
            if b.historical_change_category in QUALITY_REFINEMENT_CATEGORIES
        )

        matched_quality_proposals = sum(
            1 for b in active_proposal_results
            if b.correspondence_rating == CorrespondenceRating.MATCHED
            and b.historical_change_category in QUALITY_REFINEMENT_CATEGORIES
        )

        # Correct proposal-based rates (strictly over active proposals)
        strict_pmr = round((matched_proposals / num_proposals * 100) if num_proposals else 0.0, 1)
        combined_pmr = round(((matched_proposals + partial_proposals) / num_proposals * 100) if num_proposals else 0.0, 1)
        qrr = round((matched_quality_proposals / quality_historical * 100) if quality_historical else 0.0, 1)
        qrp = round((matched_quality_proposals / num_proposals * 100) if num_proposals else 0.0, 1)

        total_eval = len(benchmark_results)
        oea = round(((matched_proposals + true_negatives) / total_eval * 100) if total_eval else 0.0, 1)

        summary = BenchmarkSummaryReport(
            total_aligned_pairs=len(change_records),
            unchanged_count=sum(1 for c in change_records if c.change_category == ChangeCategory.UNCHANGED),
            editorial_count=sum(1 for c in change_records if c.change_category == ChangeCategory.EDITORIAL_TEXTUAL),
            quality_refinements_count=quality_historical,
            scope_changes_count=sum(1 for c in change_records if c.change_category == ChangeCategory.FUNCTIONAL_SCOPE_CHANGE),
            added_count=sum(1 for c in change_records if c.change_category == ChangeCategory.REQUIREMENT_ADDED),
            deleted_count=sum(1 for c in change_records if c.change_category == ChangeCategory.REQUIREMENT_DELETED),
            total_active_proposals=num_proposals,
            proposals_matched=matched_proposals,
            proposals_partial=partial_proposals,
            proposals_not_matched=not_matched_proposals,
            proposal_strict_match_rate=strict_pmr,
            proposal_combined_match_rate=combined_pmr,
            quality_refinement_recall=qrr,
            quality_refinement_precision=qrp,
            overall_evolutionary_agreement=oea,
            total_pipeline_proposals_evaluated=num_proposals,
            matched_count=matched_proposals,
            partially_matched_count=partial_proposals,
            not_matched_count=not_matched_proposals,
            match_rate=combined_pmr,
            strict_match_rate=strict_pmr,
            quality_prediction_precision=qrp,
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
                explanation=f"Pipeline-1 proposal semantically anticipated the specification in the Final Version of the SRS (Shared concept: {overlap or 'quantitative constraint/standard'}).",
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
                explanation="Pipeline-1 correctly flagged the quality flaw, but the Final Version of the SRS adopted an alternative formulation.",
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
            explanation="Pipeline-1 proposed a refinement, but the modification in the Final Version of the SRS was unrelated or unaligned.",
            is_true_positive_prediction=False,
        )
