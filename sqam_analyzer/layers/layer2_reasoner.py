"""
sqam_analyzer.layers.layer2_reasoner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Layer 2: Defect Reasoning.

Creates a dedicated reasoning stage that checks whether each flagged shortcoming
from Layer 1 is genuinely justified in context. The logic discards unsupported
or irrelevant flags (false positives) before proceeding to solution generation.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional
from sqam_analyzer.layers.base import BaseLayer
from sqam_analyzer.llm_provider import BaseLLMClient
from sqam_analyzer.models import (
    DefectStatus,
    Layer2Output,
    Requirement,
    Shortcoming,
    SRSContext,
)
from sqam_analyzer.prompts import LAYER_2_SYSTEM_PROMPT, LAYER_2_USER_TEMPLATE

logger = logging.getLogger(__name__)


class Layer2DefectReasoner(BaseLayer):
    """
    Implements Layer 2: Defect Reasoning and Contextual Verification.
    Acts as a false-positive filter by testing candidate defects against document context.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
    ):
        super().__init__(llm_client, system_prompt, user_prompt_template)

    def get_default_system_prompt(self) -> str:
        return LAYER_2_SYSTEM_PROMPT

    def get_default_user_prompt_template(self) -> str:
        return LAYER_2_USER_TEMPLATE

    def execute(
        self,
        requirement: Requirement,
        srs_context: SRSContext,
        candidate_shortcomings: List[Shortcoming],
        temperature: float = 0.0,
    ) -> Layer2Output:
        """
        Executes Layer 2 defect reasoning on candidate shortcomings.
        If no candidate shortcomings exist, returns a clean output immediately.
        """
        logger.info(
            "Executing Layer 2 defect reasoning for %s with %d candidate shortcomings",
            requirement.req_id,
            len(candidate_shortcomings),
        )

        # Early exit if Layer 1 found no defects
        if not candidate_shortcomings:
            return Layer2Output(
                req_id=requirement.req_id,
                evaluations=[],
                retained_defects=[],
                discarded_defects=[],
                reasoning_summary="No candidate shortcomings were flagged by Layer 1. Requirement is compliant.",
            )

        shortcomings_dict = [s.model_dump() for s in candidate_shortcomings]
        formatted_user_prompt = self.user_prompt_template.format(
            srs_context=srs_context.to_formatted_context_string(),
            req_id=requirement.req_id,
            req_text=requirement.text,
            shortcomings_json=json.dumps(shortcomings_dict, indent=2),
        )

        output: Layer2Output = self.llm_client.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=formatted_user_prompt,
            schema_class=Layer2Output,
            temperature=temperature,
        )

        # Ensure retained_defects and discarded_defects strictly match the evaluation statuses
        justified_ids = {
            ev.defect_id for ev in output.evaluations if ev.status == DefectStatus.JUSTIFIED
        }
        discarded_ids = {
            ev.defect_id for ev in output.evaluations if ev.status == DefectStatus.DISCARDED
        }

        # Cross-reference with candidate shortcomings to prevent hallucinated defect models
        candidate_lookup = {s.defect_id: s for s in candidate_shortcomings}
        retained = [candidate_lookup[did] for did in justified_ids if did in candidate_lookup]
        discarded = [candidate_lookup[did] for did in discarded_ids if did in candidate_lookup]

        output.retained_defects = retained
        output.discarded_defects = discarded

        logger.info(
            "Layer 2 complete for %s: %d retained (justified), %d discarded (false positives)",
            requirement.req_id,
            len(output.retained_defects),
            len(output.discarded_defects),
        )
        return output
