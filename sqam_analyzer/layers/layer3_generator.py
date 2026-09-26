"""
sqam_analyzer.layers.layer3_generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Layer 3: Solution Generation.

For the shortcomings retained after Layer 2, generates a targeted refinement
aimed at resolving that specific defect rather than rewriting the requirement wholesale.
The functional intent of the original requirement is strictly maintained.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional
from sqam_analyzer.layers.base import BaseLayer
from sqam_analyzer.llm_provider import BaseLLMClient
from sqam_analyzer.models import (
    Layer3Output,
    Requirement,
    Shortcoming,
    SRSContext,
)
from sqam_analyzer.prompts import LAYER_3_SYSTEM_PROMPT, LAYER_3_USER_TEMPLATE

logger = logging.getLogger(__name__)


class Layer3SolutionGenerator(BaseLayer):
    """
    Implements Layer 3: Solution Generation (Targeted Refinement).
    Operates as an AI-assisted requirements editor applying minimal, surgical edits.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
    ):
        super().__init__(llm_client, system_prompt, user_prompt_template)

    def get_default_system_prompt(self) -> str:
        return LAYER_3_SYSTEM_PROMPT

    def get_default_user_prompt_template(self) -> str:
        return LAYER_3_USER_TEMPLATE

    def execute(
        self,
        requirement: Requirement,
        srs_context: SRSContext,
        retained_defects: List[Shortcoming],
        temperature: float = 0.0,
    ) -> Layer3Output:
        """
        Generates a targeted refinement addressing the justified shortcomings.
        If no shortcomings are retained, returns the original requirement unchanged.
        """
        logger.info(
            "Executing Layer 3 solution generation for %s with %d retained defects",
            requirement.req_id,
            len(retained_defects),
        )

        # Early exit if no defects were retained
        if not retained_defects:
            return Layer3Output(
                req_id=requirement.req_id,
                original_text=requirement.text,
                refined_text=requirement.text,
                changes_made=[],
                addressed_defect_ids=[],
                functional_intent_preservation_rationale=(
                    "Requirement passed contextual validation with zero justified defects. No refinement needed."
                ),
            )

        defects_dict = [d.model_dump() for d in retained_defects]
        formatted_user_prompt = self.user_prompt_template.format(
            srs_context=srs_context.to_formatted_context_string(),
            req_id=requirement.req_id,
            req_text=requirement.text,
            justified_defects_json=json.dumps(defects_dict, indent=2),
        )

        output: Layer3Output = self.llm_client.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=formatted_user_prompt,
            schema_class=Layer3Output,
            temperature=temperature,
        )

        # Ensure original text matches the requirement
        output.original_text = requirement.text

        logger.info(
            "Layer 3 complete for %s: Generated refinement with %d specific changes",
            requirement.req_id,
            len(output.changes_made),
        )
        return output
