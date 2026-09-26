"""
sqam_analyzer.layers.layer5_decision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Layer 5: Comparison & Human-in-the-Loop Decision.

Formats the final output to present the original requirement alongside the validated
refinement and the complete audit reasoning behind the change. Allows a human reviewer
to easily accept the refinement, retain the original, or provide a manual modification.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Optional

from sqam_analyzer.diff_utils import compute_word_diff
from sqam_analyzer.models import (
    HumanDecision,
    HumanDecisionStatus,
    Layer1Output,
    Layer2Output,
    Layer3Output,
    Layer4Output,
    Layer5Output,
    Requirement,
    ValidationVerdict,
)

logger = logging.getLogger(__name__)


class Layer5HumanDecisionManager:
    """
    Manages Layer 5: Comparison, Traceability Presentation, and Human-in-the-Loop Sign-off.
    """

    def prepare_review_dossier(
        self,
        requirement: Requirement,
        layer1_output: Optional[Layer1Output] = None,
        layer2_output: Optional[Layer2Output] = None,
        layer3_output: Optional[Layer3Output] = None,
        layer4_output: Optional[Layer4Output] = None,
    ) -> Layer5Output:
        """
        Synthesizes the outputs of Layers 1-4 into a transparent, reviewable dossier.
        """
        logger.info("Preparing Layer 5 review dossier for %s", requirement.req_id)

        # Calculate word diff if refinement is present
        refined_text = layer3_output.refined_text if layer3_output else None
        diff = None
        if refined_text and refined_text.strip() != requirement.text.strip():
            diff = compute_word_diff(requirement.text, refined_text)

        # Quality score breakdown
        quality_summary = None
        if layer1_output:
            quality_summary = {
                score.attribute.value: score.score for score in layer1_output.attribute_scores
            }
            quality_summary["OVERALL"] = layer1_output.overall_quality_score

        initial_count = len(layer1_output.shortcomings) if layer1_output else 0
        justified_count = len(layer2_output.retained_defects) if layer2_output else 0

        # Determine default human decision proposal
        is_validated = layer4_output.is_valid if layer4_output else False
        default_target = (
            refined_text
            if (is_validated and refined_text and refined_text.strip() != requirement.text.strip())
            else requirement.text
        )

        initial_decision = HumanDecision(
            status=HumanDecisionStatus.PENDING_REVIEW,
            final_text=default_target,
            reviewer_comments=None,
            decision_timestamp=None,
        )

        return Layer5Output(
            req_id=requirement.req_id,
            original_text=requirement.text,
            refined_text=refined_text,
            diff=diff,
            quality_summary=quality_summary,
            initial_defects_count=initial_count,
            justified_defects_count=justified_count,
            validation_verdict=layer4_output.verdict if layer4_output else None,
            validation_critique=layer4_output.critique_and_feedback if layer4_output else None,
            solution_summary=(
                "; ".join(layer3_output.changes_made) if layer3_output else "No changes proposed"
            ),
            human_decision=initial_decision,
        )

    def record_decision(
        self,
        dossier: Layer5Output,
        status: HumanDecisionStatus,
        comments: Optional[str] = None,
        custom_text: Optional[str] = None,
    ) -> Layer5Output:
        """
        Records the explicit choice of the human reviewer.
        - ACCEPTED: Adopts the AI validated refinement.
        - REJECTED: Retains the original requirement text.
        - EDITED_BY_HUMAN: Applies reviewer-supplied custom text.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if status == HumanDecisionStatus.ACCEPTED:
            final_text = dossier.refined_text or dossier.original_text
        elif status == HumanDecisionStatus.REJECTED:
            final_text = dossier.original_text
        elif status == HumanDecisionStatus.EDITED_BY_HUMAN:
            if not custom_text:
                raise ValueError("custom_text must be provided when status is EDITED_BY_HUMAN")
            final_text = custom_text
        else:
            final_text = dossier.human_decision.final_text

        dossier.human_decision = HumanDecision(
            status=status,
            final_text=final_text,
            reviewer_comments=comments,
            decision_timestamp=now_iso,
        )
        logger.info(
            "Recorded human decision for %s: %s", dossier.req_id, status.value
        )
        return dossier

    def render_markdown_report(
        self,
        dossier: Optional[Layer5Output],
        layer1_output: Optional[Layer1Output] = None,
        layer2_output: Optional[Layer2Output] = None,
        layer4_output: Optional[Layer4Output] = None,
    ) -> str:
        """
        Generates an audit-ready Markdown report comparing original and refined requirement
        with complete 5-layer reasoning traceability.
        """
        if dossier is None:
            return "# Requirements Quality Review\n\n*Error: Dossier is not available.*"

        lines = [
            f"# Requirements Quality Review: {dossier.req_id}",
            "",
            "## 1. Requirement Comparison",
            f"**Original Requirement:**",
            f"> {dossier.original_text}",
            "",
        ]

        if dossier.refined_text:
            lines.extend([
                f"**Proposed Refinement:**",
                f"> {dossier.refined_text}",
                "",
            ])
            if dossier.diff:
                lines.extend([
                    f"**Word-Level Diff:**",
                    f"> {dossier.diff.diff_markup}",
                    "",
                    f"*Words changed: {dossier.diff.changed_words_count}*",
                    "",
                ])

        lines.extend([
            "## 2. Quality Audit Traceability",
            f"- **Initial Candidate Defects (Layer 1):** {dossier.initial_defects_count}",
            f"- **Contextually Justified Defects (Layer 2):** {dossier.justified_defects_count}",
            f"- **Validation Verdict (Layer 4):** `{dossier.validation_verdict.value if dossier.validation_verdict else 'N/A'}`",
            "",
        ])

        if dossier.quality_summary:
            lines.append("### Quality Scorecard (Layer 1)")
            lines.append("| Quality Attribute | Score (0-10) |")
            lines.append("| :--- | :--- |")
            for attr, score in dossier.quality_summary.items():
                lines.append(f"| {attr} | {score:.1f} |")
            lines.append("")

        if layer2_output and layer2_output.evaluations:
            lines.append("### Defect Reasoning & False-Positive Filter (Layer 2)")
            for ev in layer2_output.evaluations:
                status_icon = "JUSTIFIED" if ev.status.value == "justified" else "DISCARDED"
                lines.append(f"- **[{status_icon}] {ev.attribute.value}** (`{ev.original_problematic_excerpt}`)")
                lines.append(f"  *Reasoning:* {ev.context_reasoning}")
            lines.append("")

        if layer4_output:
            lines.append("### Independent Auditor Validation (Layer 4)")
            lines.append(f"*{layer4_output.critique_and_feedback}*")
            lines.append("")
            for check in layer4_output.checks:
                passed_str = "PASS" if check.passed else "FAIL"
                lines.append(f"- `[{passed_str}]` **{check.criterion}:** {check.observations}")
            lines.append("")

        lines.extend([
            "## 3. Human-in-the-Loop Decision",
            f"- **Decision Status:** `{dossier.human_decision.status.value}`",
            f"- **Final Approved Text:**",
            f"> {dossier.human_decision.final_text}",
        ])

        if dossier.human_decision.reviewer_comments:
            lines.append(f"- **Reviewer Notes:** {dossier.human_decision.reviewer_comments}")

        return "\n".join(lines)
