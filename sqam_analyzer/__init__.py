"""
sqam_analyzer
~~~~~~~~~~~~~
LLM-Based Software Requirement Quality Analyzer.
Functions as an AI-assisted requirements editor via a structured 5-layer LLM pipeline:
- Layer 1: Document Understanding, Scoring & Shortcoming Identification
- Layer 2: Defect Reasoning & Context Verification (false-positive elimination)
- Layer 3: Solution Generation (targeted refinement preserving functional intent)
- Layer 4: Solution Reasoning & Validation (independent auditor / critic)
- Layer 5: Comparison & Human-in-the-Loop Decision
"""

from sqam_analyzer.layers import (
    BaseLayer,
    Layer1DocumentScorer,
    Layer2DefectReasoner,
    Layer3SolutionGenerator,
    Layer4SolutionValidator,
    Layer5HumanDecisionManager,
)
from sqam_analyzer.llm_provider import (
    BaseLLMClient,
    GeminiLLMClient,
    LangChainLLMClient,
    MockLLMClient,
    OpenAILLMClient,
)
from sqam_analyzer.models import (
    DefectStatus,
    HumanDecision,
    HumanDecisionStatus,
    Layer1Output,
    Layer2Output,
    Layer3Output,
    Layer4Output,
    Layer5Output,
    PipelineExecutionResult,
    QualityAttribute,
    Requirement,
    SeverityLevel,
    Shortcoming,
    SRSContext,
    ValidationVerdict,
)
from sqam_analyzer.pipeline import RequirementQualityPipeline

__version__ = "1.0.0"

__all__ = [
    # Core Pipeline
    "RequirementQualityPipeline",
    # Data Models
    "Requirement",
    "SRSContext",
    "QualityAttribute",
    "SeverityLevel",
    "DefectStatus",
    "ValidationVerdict",
    "HumanDecisionStatus",
    "Shortcoming",
    "HumanDecision",
    "PipelineExecutionResult",
    "Layer1Output",
    "Layer2Output",
    "Layer3Output",
    "Layer4Output",
    "Layer5Output",
    # Layers
    "BaseLayer",
    "Layer1DocumentScorer",
    "Layer2DefectReasoner",
    "Layer3SolutionGenerator",
    "Layer4SolutionValidator",
    "Layer5HumanDecisionManager",
    # LLM Providers
    "BaseLLMClient",
    "OpenAILLMClient",
    "GeminiLLMClient",
    "LangChainLLMClient",
    "MockLLMClient",
]
