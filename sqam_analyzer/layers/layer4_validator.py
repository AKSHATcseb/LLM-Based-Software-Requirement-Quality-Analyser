"""
sqam_analyzer.layers.layer4_validator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Layer 4: Solution Reasoning & Validation.

Implements an independent validation stage to check whether the Layer 3 refinement
successfully resolves the shortcomings without introducing new ambiguity, assumptions,
or unintended changes to the original functional intent. Unsuitable solutions
are flagged for rejection.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional
from sqam_analyzer.layers.base import BaseLayer
from sqam_analyzer.llm_provider import BaseLLMClient
from sqam_analyzer.models import (
    Layer3Output,
    Layer4Output,
    Requirement,
    Shortcoming,
    SRSContext,
    ValidationCheck,
    ValidationVerdict,
)
from sqam_analyzer.prompts import LAYER_4_SYSTEM_PROMPT, LAYER_4_USER_TEMPLATE

logger = logging.getLogger(__name__)


class Layer4SolutionValidator(BaseLayer):
    """
    Implements Layer 4: Solution Reasoning & Validation.
    Acts as an independent adversarial critic/auditor to guarantee refinement safety.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
    ):
        super().__init__(llm_client, system_prompt, user_prompt_template)

    def get_default_system_prompt(self) -> str:
        return LAYER_4_SYSTEM_PROMPT

    def get_default_user_prompt_template(self) -> str:
        return LAYER_4_USER_TEMPLATE

    def execute(
        self,
        requirement: Requirement,
        srs_context: SRSContext,
        retained_defects: List[Shortcoming],
        layer3_output: Layer3Output,
        temperature: float = 0.0,
    ) -> Layer4Output:
        """
        Executes independent verification on the proposed refinement.
        """
        logger.info("Executing Layer 4 solution validation for %s", requirement.req_id)

        # If no defects were present to begin with and text wasn't changed, validate directly
        if not retained_defects and layer3_output.refined_text.strip() == requirement.text.strip():
            return Layer4Output(
                req_id=requirement.req_id,
                is_valid=True,
                verdict=ValidationVerdict.VALIDATED,
                checks=[
                    ValidationCheck(
                        criterion="Pre-existing Quality Baseline",
                        passed=True,
                        observations="Original requirement had zero justified defects.",
                    )
                ],
                unwarranted_assumptions_detected=[],
                new_ambiguities_detected=[],
                critique_and_feedback="Requirement was already compliant with SRS quality baseline.",
            )

        defects_dict = [d.model_dump() for d in retained_defects]
        changes_str = "\n".join(f"- {c}" for c in layer3_output.changes_made) or "No changes recorded."

        formatted_user_prompt = self.user_prompt_template.format(
            srs_context=srs_context.to_formatted_context_string(),
            req_id=requirement.req_id,
            original_text=requirement.text,
            justified_defects_json=json.dumps(defects_dict, indent=2),
            refined_text=layer3_output.refined_text,
            changes_made=changes_str,
            intent_rationale=layer3_output.functional_intent_preservation_rationale,
        )

        output: Layer4Output = self.llm_client.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=formatted_user_prompt,
            schema_class=Layer4Output,
            temperature=temperature,
        )

        # Enforce consistency: if any assumption/ambiguity detected or checks failed, force is_valid to match
        has_critical_failure = (
            bool(output.unwarranted_assumptions_detected)
            or bool(output.new_ambiguities_detected)
            or any(not check.passed for check in output.checks)
        )
        if has_critical_failure and output.is_valid:
            logger.warning(
                "Layer 4 found critical issues but reported is_valid=True. Correcting to False."
            )
            output.is_valid = False
            output.verdict = ValidationVerdict.REJECTED

        logger.info(
            "Layer 4 complete for %s: is_valid=%s, verdict=%s",
            requirement.req_id,
            output.is_valid,
            output.verdict.value,
        )
        return output
