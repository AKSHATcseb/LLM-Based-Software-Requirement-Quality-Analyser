"""
sqam_analyzer.layers.layer1_scorer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Layer 1: Document Understanding, Scoring & Shortcoming Identification.

Evaluates an individual software requirement within the context of the surrounding
SRS document against standard quality attributes:
1. Unambiguity
2. Completeness
3. Consistency
4. Conformance
5. Correctness
6. Singularity
7. Verifiability/Feasibility

Flags potential shortcomings based on these criteria.
"""

from __future__ import annotations

import logging
from typing import Optional
from sqam_analyzer.layers.base import BaseLayer
from sqam_analyzer.llm_provider import BaseLLMClient
from sqam_analyzer.models import Layer1Output, Requirement, SRSContext
from sqam_analyzer.prompts import LAYER_1_SYSTEM_PROMPT, LAYER_1_USER_TEMPLATE

logger = logging.getLogger(__name__)


class Layer1DocumentScorer(BaseLayer):
    """
    Implements Layer 1: Document Understanding, Scoring & Shortcoming Identification.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
    ):
        super().__init__(llm_client, system_prompt, user_prompt_template)

    def get_default_system_prompt(self) -> str:
        return LAYER_1_SYSTEM_PROMPT

    def get_default_user_prompt_template(self) -> str:
        return LAYER_1_USER_TEMPLATE

    def execute(
        self,
        requirement: Requirement,
        srs_context: SRSContext,
        temperature: float = 0.0,
    ) -> Layer1Output:
        """
        Executes Layer 1 analysis on a single requirement with contextual awareness.
        """
        logger.info("Executing Layer 1 for requirement %s", requirement.req_id)

        formatted_user_prompt = self.user_prompt_template.format(
            srs_context=srs_context.to_formatted_context_string(),
            req_id=requirement.req_id,
            req_type=requirement.req_type,
            section=requirement.section or "General System Requirements",
            req_text=requirement.text,
        )

        output: Layer1Output = self.llm_client.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=formatted_user_prompt,
            schema_class=Layer1Output,
            temperature=temperature,
        )

        logger.info(
            "Layer 1 complete for %s: Overall score %.1f/10, %d candidate shortcomings identified",
            requirement.req_id,
            output.overall_quality_score,
            len(output.shortcomings),
        )
        return output
