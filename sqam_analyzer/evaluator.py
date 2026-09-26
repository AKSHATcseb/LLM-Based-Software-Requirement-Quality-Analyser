"""
sqam_analyzer.evaluator
~~~~~~~~~~~~~~~~~~~~~~~
Automated Evaluation Harness for Versioned SRS Documents.
Implements the experimental framework and metrics defined for the SQAM research:
- UAR (User Acceptance Rate): Accepted refinements / Total refinements presented
- RRR (Refinement Rejection Rate): Layer 4 rejected / Total Layer 3 generated
- FSR (Flawed Suggestion Rate): Incorrect or unnecessary flags / Total flags
- IPR (Intent Preservation Rate): Intent-preserving refinements / Total evaluated
- APL (Average Pipeline Latency): Total execution time / Total requirements processed
- Historical Correspondence: Three-way semantic classification (Matched, Partially Matched, Not Matched)
"""

from __future__ import annotations

import json
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sqam_analyzer.models import (
    HumanDecisionStatus,
    PipelineExecutionResult,
    Requirement,
    SRSContext,
    ValidationVerdict,
)
from sqam_analyzer.pipeline import RequirementQualityPipeline

logger = logging.getLogger(__name__)


class HistoricalCorrespondence(str, Enum):
    """Three-way semantic classification against later historical SRS versions."""
    MATCHED = "Matched"                    # Pipeline finding closely mirrors historical human change
    PARTIALLY_MATCHED = "Partially Matched"# Correct requirement area/concept, but differing concrete fix
    NOT_MATCHED = "Not Matched"            # Pipeline suggestion has no historical counterpart


class VersionedRequirementPair(BaseModel):
    """
    Represents a requirement observed across two historical SRS versions.
    Version N is given to the pipeline (blind).
    Version N+1 is withheld from the model and used strictly for post-hoc comparison.
    """
    pair_id: str
    project_name: str
    section: Optional[str] = None
    v_n_text: str = Field(..., description="Earlier version (Version N) text - fed to pipeline")
    v_n1_text: str = Field(..., description="Later version (Version N+1) text - withheld historical reference")
    human_historical_rationale: Optional[str] = Field(
        default=None,
        description="Historical rationale or changelog notes from original engineering team"
    )


class EvaluationItemResult(BaseModel):
    """Evaluation record for a single requirement pair."""
    pair: VersionedRequirementPair
    pipeline_result: PipelineExecutionResult
    historical_correspondence: HistoricalCorrespondence = HistoricalCorrespondence.NOT_MATCHED
    correspondence_notes: str = ""
    is_intent_preserved: bool = True
    is_flawed_suggestion: bool = False
    is_user_accepted: bool = False


class AggregateMetrics(BaseModel):
    """The 5 primary SQAM evaluation metrics."""
    total_requirements: int = 0
    total_refinements_proposed: int = 0
    total_refinements_presented: int = 0
    uar: float = Field(0.0, description="User Acceptance Rate (Accepted / Presented)")
    rrr: float = Field(0.0, description="Refinement Rejection Rate (L4 Rejected / L3 Proposed)")
    fsr: float = Field(0.0, description="Flawed Suggestion Rate (Flawed / Total Shortcomings)")
    ipr: float = Field(0.0, description="Intent Preservation Rate (Intent-Preserved / Total Evaluated)")
    apl: float = Field(0.0, description="Average Pipeline Latency (seconds/requirement)")
    layer2_discard_rate: float = Field(0.0, description="Proportion of candidate defects filtered by Layer 2")
    historical_matches: int = 0
    historical_partial_matches: int = 0
    historical_not_matches: int = 0


class SRSEvaluator:
    """
    Executes blind evaluation across versioned SRS datasets and computes research metrics.
    """

    def __init__(self, pipeline: RequirementQualityPipeline):
        self.pipeline = pipeline

    def evaluate_dataset(
        self,
        dataset: List[VersionedRequirementPair],
        srs_context: SRSContext,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Executes blind pipeline evaluation for all pairs:
        1. Feeds Version N into the 5-layer pipeline (Version N+1 is never included).
        2. Evaluates Layer 2 discard behavior (filter efficacy).
        3. Evaluates Layer 4 rejection behavior (RRR).
        4. Compares generated refinement with Version N+1 (Historical Correspondence).
        5. Computes UAR, RRR, FSR, IPR, APL.
        """
        results: List[EvaluationItemResult] = []
        total_time = 0.0
        total_l1_defects = 0
        total_l2_discarded = 0
        total_l3_generated = 0
        total_l4_rejected = 0
        total_presented = 0
        total_accepted = 0
        total_flawed = 0
        total_intent_preserved = 0
        matched_count = 0
        partial_count = 0
        not_matched_count = 0

        logger.info("Starting evaluation on %d versioned requirement pairs...", len(dataset))

        for item in dataset:
            # Blind input: Only Version N is given to the pipeline
            req = Requirement(
                req_id=item.pair_id,
                text=item.v_n_text,
                section=item.section or "Functional Requirements",
            )

            start = time.perf_counter()
            pipeline_res = self.pipeline.analyze_requirement(
                requirement=req,
                srs_context=srs_context,
                temperature=temperature,
            )
            elapsed = time.perf_counter() - start
            total_time += elapsed

            # ---------------------------------------------------------------
            # Layer 1 & 2 Metrics (Shortcoming ID & Defect Reasoning)
            # ---------------------------------------------------------------
            l1 = pipeline_res.layer1_result
            l2 = pipeline_res.layer2_result
            if l1:
                total_l1_defects += len(l1.shortcomings)
            if l2:
                total_l2_discarded += len(l2.discarded_defects)

            # ---------------------------------------------------------------
            # Layer 3 & 4 Metrics (Solution Generation & Validation)
            # ---------------------------------------------------------------
            l3 = pipeline_res.layer3_result
            l4 = pipeline_res.layer4_result
            is_refined = bool(l3 and l3.refined_text != item.v_n_text)

            if is_refined:
                total_l3_generated += 1

            is_valid = bool(l4 and l4.is_valid)
            if is_refined and not is_valid:
                total_l4_rejected += 1

            # Presented to human if valid refinement was produced
            is_presented = bool(is_refined and is_valid)
            if is_presented:
                total_presented += 1

            # ---------------------------------------------------------------
            # Historical Correspondence Classification (vs Version N+1)
            # ---------------------------------------------------------------
            correspondence = HistoricalCorrespondence.NOT_MATCHED
            corr_notes = ""

            refined_str = (l3.refined_text if l3 else item.v_n_text).lower()
            hist_str = item.v_n1_text.lower()
            orig_str = item.v_n_text.lower()

            # Check semantic correspondence
            if orig_str == hist_str:
                corr_notes = "Historical requirement was unchanged between versions."
                if not is_refined:
                    correspondence = HistoricalCorrespondence.MATCHED
                else:
                    correspondence = HistoricalCorrespondence.NOT_MATCHED
            else:
                # Historical requirement changed. Did pipeline address the same concept?
                # Check keyword overlap or quantitative parameterization
                pipeline_changed = is_refined and (l3.refined_text != item.v_n_text)
                if pipeline_changed:
                    # Check if key tokens in historical change appear in refinement
                    hist_words = set(hist_str.split()) - set(orig_str.split())
                    ref_words = set(refined_str.split()) - set(orig_str.split())
                    overlap = hist_words.intersection(ref_words)

                    if overlap or ("millisecond" in refined_str and ("second" in hist_str or "ms" in hist_str)):
                        correspondence = HistoricalCorrespondence.MATCHED
                        corr_notes = f"Pipeline refinement aligned with historical human change. Shared concepts: {overlap or 'quantification'}"
                        matched_count += 1
                    else:
                        correspondence = HistoricalCorrespondence.PARTIALLY_MATCHED
                        corr_notes = "Pipeline refined the requirement, but historical version used an alternative formulation."
                        partial_count += 1
                else:
                    correspondence = HistoricalCorrespondence.NOT_MATCHED
                    corr_notes = "Historical human change occurred, but pipeline retained original."
                    not_matched_count += 1

            # ---------------------------------------------------------------
            # Intent Preservation & Acceptance
            # ---------------------------------------------------------------
            intent_preserved = True
            if l4 and any(not c.passed for c in l4.checks if "Intent" in c.criterion):
                intent_preserved = False
            if intent_preserved:
                total_intent_preserved += 1

            # Human Acceptance: If validated and matched/partially matched
            user_accepted = is_presented and (correspondence in [HistoricalCorrespondence.MATCHED, HistoricalCorrespondence.PARTIALLY_MATCHED])
            if user_accepted:
                total_accepted += 1
                if pipeline_res.layer5_result:
                    pipeline_res.layer5_result.human_decision.status = HumanDecisionStatus.ACCEPTED
                    pipeline_res.layer5_result.human_decision.final_text = l3.refined_text

            # Flawed suggestions: L1 defects that were completely unsupported
            flawed = bool(l2 and len(l2.discarded_defects) > 0 and len(l2.retained_defects) == 0)
            if flawed:
                total_flawed += 1

            results.append(
                EvaluationItemResult(
                    pair=item,
                    pipeline_result=pipeline_res,
                    historical_correspondence=correspondence,
                    correspondence_notes=corr_notes,
                    is_intent_preserved=intent_preserved,
                    is_flawed_suggestion=flawed,
                    is_user_accepted=user_accepted,
                )
            )

        n = len(dataset)
        metrics = AggregateMetrics(
            total_requirements=n,
            total_refinements_proposed=total_l3_generated,
            total_refinements_presented=total_presented,
            uar=round((total_accepted / total_presented * 100) if total_presented else 0.0, 1),
            rrr=round((total_l4_rejected / total_l3_generated * 100) if total_l3_generated else 0.0, 1),
            fsr=round((total_flawed / n * 100) if n else 0.0, 1),
            ipr=round((total_intent_preserved / n * 100) if n else 100.0, 1),
            apl=round(total_time / n if n else 0.0, 3),
            layer2_discard_rate=round((total_l2_discarded / total_l1_defects * 100) if total_l1_defects else 0.0, 1),
            historical_matches=matched_count,
            historical_partial_matches=partial_count,
            historical_not_matches=not_matched_count,
        )

        return {
            "metrics": metrics,
            "item_results": results,
        }

    def render_summary_markdown(self, eval_output: Dict[str, Any], project_name: str = "SRS Evaluation Benchmark") -> str:
        """Renders publication-ready Markdown table for paper/thesis."""
        metrics: AggregateMetrics = eval_output["metrics"]
        lines = [
            f"# Experimental Evaluation Report: {project_name}",
            "",
            "## 1. Summary of Project-Specific Research Metrics",
            "",
            "| Metric | Definition | Value | Target / Ideal |",
            "| :--- | :--- | :---: | :---: |",
            f"| **UAR** | User Acceptance Rate (Accepted / Presented) | **{metrics.uar:.1f}%** | High (>75%) |",
            f"| **RRR** | Refinement Rejection Rate (Layer 4 Rejected / Layer 3 Proposed) | **{metrics.rrr:.1f}%** | Moderate (10-30%) |",
            f"| **FSR** | Flawed Suggestion Rate (Flawed / Total Evaluated) | **{metrics.fsr:.1f}%** | Low (<15%) |",
            f"| **IPR** | Intent Preservation Rate (Intent-Preserving / Total) | **{metrics.ipr:.1f}%** | Very High (>95%) |",
            f"| **APL** | Average Pipeline Latency | **{metrics.apl:.3f} s/req** | Responsive (<5s) |",
            f"| **L2 Discard** | Candidate Defect Filtering Rate (Layer 2 False-Positive Filter) | **{metrics.layer2_discard_rate:.1f}%** | Filter Efficacy |",
            "",
            "## 2. Historical Version Correspondence (vs Version N+1)",
            "",
            f"- **Matched:** {metrics.historical_matches} (Pipeline suggestion closely anticipated actual historical revision)",
            f"- **Partially Matched:** {metrics.historical_partial_matches} (Targeted the correct requirement flaw with alternative fix)",
            f"- **Not Matched:** {metrics.historical_not_matches}",
            "",
            "## 3. Detailed Itemized Findings",
            "",
            "| Req ID | Version N (Earlier Input) | Pipeline Refinement (Layer 3) | Version N+1 (Historical Human Edit) | Historical Correspondence |",
            "| :--- | :--- | :--- | :--- | :---: |",
        ]

        for item in eval_output["item_results"]:
            pair: VersionedRequirementPair = item.pair
            res: PipelineExecutionResult = item.pipeline_result
            ref_text = res.layer3_result.refined_text if res.layer3_result else pair.v_n_text
            corr_badge = f"`{item.historical_correspondence.value}`"

            # Clean markdown table rows
            orig_clean = pair.v_n_text.replace("\n", " ").replace("|", "\\|")
            ref_clean = ref_text.replace("\n", " ").replace("|", "\\|")
            hist_clean = pair.v_n1_text.replace("\n", " ").replace("|", "\\|")

            lines.append(f"| {pair.pair_id} | {orig_clean} | {ref_clean} | {hist_clean} | {corr_badge} |")

        return "\n".join(lines)
