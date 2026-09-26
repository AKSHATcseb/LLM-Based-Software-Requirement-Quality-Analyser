"""
sqam_analyzer.pipeline
~~~~~~~~~~~~~~~~~~~~~~
Core Pipeline Orchestrator for the 5-Layer Software Requirement Quality Analyzer.
Sequences Layer 1 through Layer 5, supporting swappable LLMs per layer,
telemetry, and both interactive and automated review modes.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Union

from sqam_analyzer.layers import (
    Layer1DocumentScorer,
    Layer2DefectReasoner,
    Layer3SolutionGenerator,
    Layer4SolutionValidator,
    Layer5HumanDecisionManager,
)
from sqam_analyzer.llm_provider import BaseLLMClient, MockLLMClient
from sqam_analyzer.models import (
    HumanDecisionStatus,
    PipelineExecutionResult,
    Requirement,
    SRSContext,
    ValidationVerdict,
)

logger = logging.getLogger(__name__)


class RequirementQualityPipeline:
    """
    Modular 5-layer pipeline orchestrator for AI-assisted requirement quality analysis.

    Pipeline Stages:
    - Layer 1: Document Understanding, Scoring & Shortcoming Identification
    - Layer 2: Defect Reasoning & Context Verification (false positive filter)
    - Layer 3: Solution Generation (targeted refinement preserving functional intent)
    - Layer 4: Solution Reasoning & Validation (independent auditor / critic)
    - Layer 5: Comparison & Human-in-the-Loop Decision Dossier
    """

    def __init__(
        self,
        default_llm: Optional[BaseLLMClient] = None,
        layer1_llm: Optional[BaseLLMClient] = None,
        layer2_llm: Optional[BaseLLMClient] = None,
        layer3_llm: Optional[BaseLLMClient] = None,
        layer4_llm: Optional[BaseLLMClient] = None,
        layer1_scorer: Optional[Layer1DocumentScorer] = None,
        layer2_reasoner: Optional[Layer2DefectReasoner] = None,
        layer3_generator: Optional[Layer3SolutionGenerator] = None,
        layer4_validator: Optional[Layer4SolutionValidator] = None,
        layer5_manager: Optional[Layer5HumanDecisionManager] = None,
    ):
        """
        Initializes the pipeline with either a single default LLM client across all layers,
        or specialized LLM clients per layer (e.g. high-throughput for L1/L3, deep-reasoning for L2/L4).
        """
        fallback_llm = default_llm or MockLLMClient()

        # Initialize individual layers with corresponding or fallback LLM
        self.layer1 = layer1_scorer or Layer1DocumentScorer(
            llm_client=layer1_llm or fallback_llm
        )
        self.layer2 = layer2_reasoner or Layer2DefectReasoner(
            llm_client=layer2_llm or fallback_llm
        )
        self.layer3 = layer3_generator or Layer3SolutionGenerator(
            llm_client=layer3_llm or fallback_llm
        )
        self.layer4 = layer4_validator or Layer4SolutionValidator(
            llm_client=layer4_llm or fallback_llm
        )
        self.layer5 = layer5_manager or Layer5HumanDecisionManager()

    def analyze_requirement(
        self,
        requirement: Requirement,
        srs_context: SRSContext,
        temperature: float = 0.0,
        auto_accept_validated: bool = False,
    ) -> PipelineExecutionResult:
        """
        Executes the full 5-layer pipeline for a single requirement.

        Parameters:
            requirement: The software requirement statement to analyze.
            srs_context: Document-level context including domain summary, glossary, and neighbors.
            temperature: LLM sampling temperature (default 0.0 for deterministic analysis).
            auto_accept_validated: If True, marks human decision as ACCEPTED automatically if
                                   Layer 4 validates the refinement. Otherwise PENDING_REVIEW.
        """
        start_time = time.perf_counter()
        logger.info("Starting 5-layer analysis for requirement: %s", requirement.req_id)

        result = PipelineExecutionResult(requirement=requirement)

        try:
            # ---------------------------------------------------------------
            # Layer 1: Document Understanding, Scoring & Shortcoming Identification
            # ---------------------------------------------------------------
            l1_output = self.layer1.execute(
                requirement=requirement,
                srs_context=srs_context,
                temperature=temperature,
            )
            result.layer1_result = l1_output

            # ---------------------------------------------------------------
            # Layer 2: Defect Reasoning (Contextual Verification)
            # ---------------------------------------------------------------
            l2_output = self.layer2.execute(
                requirement=requirement,
                srs_context=srs_context,
                candidate_shortcomings=l1_output.shortcomings,
                temperature=temperature,
            )
            result.layer2_result = l2_output

            # ---------------------------------------------------------------
            # Layer 3: Solution Generation (Targeted Refinement)
            # ---------------------------------------------------------------
            l3_output = self.layer3.execute(
                requirement=requirement,
                srs_context=srs_context,
                retained_defects=l2_output.retained_defects,
                temperature=temperature,
            )
            result.layer3_result = l3_output

            # ---------------------------------------------------------------
            # Layer 4: Solution Reasoning & Validation (Auditor / Critic)
            # ---------------------------------------------------------------
            l4_output = self.layer4.execute(
                requirement=requirement,
                srs_context=srs_context,
                retained_defects=l2_output.retained_defects,
                layer3_output=l3_output,
                temperature=temperature,
            )
            result.layer4_result = l4_output

            # ---------------------------------------------------------------
            # Layer 5: Comparison & Human-in-the-Loop Decision Dossier
            # ---------------------------------------------------------------
            l5_output = self.layer5.prepare_review_dossier(
                requirement=requirement,
                layer1_output=l1_output,
                layer2_output=l2_output,
                layer3_output=l3_output,
                layer4_output=l4_output,
            )

            # Auto-accept if requested and validated
            if auto_accept_validated and l4_output.verdict == ValidationVerdict.VALIDATED:
                l5_output = self.layer5.record_decision(
                    dossier=l5_output,
                    status=HumanDecisionStatus.ACCEPTED,
                    comments="Auto-accepted based on successful Layer 4 independent validation.",
                )

            result.layer5_result = l5_output
            result.status = "completed"

        except Exception as exc:
            logger.exception("Pipeline failed while analyzing requirement %s", requirement.req_id)
            result.status = "error"
            result.error_message = str(exc)

        finally:
            result.execution_time_seconds = round(time.perf_counter() - start_time, 3)

        return result

    def analyze_batch(
        self,
        requirements: List[Requirement],
        srs_context: SRSContext,
        temperature: float = 0.0,
        auto_accept_validated: bool = False,
    ) -> List[PipelineExecutionResult]:
        """
        Executes analysis sequentially across a collection of requirements from an SRS.
        """
        results = []
        for req in requirements:
            res = self.analyze_requirement(
                requirement=req,
                srs_context=srs_context,
                temperature=temperature,
                auto_accept_validated=auto_accept_validated,
            )
            results.append(res)
        return results
