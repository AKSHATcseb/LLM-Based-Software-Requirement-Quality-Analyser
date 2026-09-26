"""
sqam_analyzer.models
~~~~~~~~~~~~~~~~~~~~
Pydantic data models for the 5-Layer Software Requirement Quality Analyzer.
Provides typed, validated schemas for requirements, SRS context, quality attributes,
defects, refinements, validation audits, and human-in-the-loop decisions.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class QualityAttribute(str, Enum):
    """
    Standard Software Requirement Quality Attributes aligned with
    ISO/IEC/IEEE 29148:2018 and IEEE 830 standards.
    """
    UNAMBIGUITY = "Unambiguity"
    COMPLETENESS = "Completeness"
    CONSISTENCY = "Consistency"
    CONFORMANCE = "Conformance"
    CORRECTNESS = "Correctness"
    SINGULARITY = "Singularity"
    VERIFIABILITY_FEASIBILITY = "Verifiability/Feasibility"


class SeverityLevel(str, Enum):
    """Severity classification for requirement shortcomings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DefectStatus(str, Enum):
    """Layer 2 reasoning verdict for candidate defects."""
    JUSTIFIED = "justified"
    DISCARDED = "discarded"


class ValidationVerdict(str, Enum):
    """Layer 4 validation verdict for generated refinements."""
    VALIDATED = "validated"
    REJECTED = "rejected"
    NEEDS_HUMAN_ATTENTION = "needs_human_attention"


class HumanDecisionStatus(str, Enum):
    """Layer 5 human reviewer decision status."""
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED_BY_HUMAN = "edited_by_human"


# ---------------------------------------------------------------------------
# Requirement & Context Models
# ---------------------------------------------------------------------------

class Requirement(BaseModel):
    """Represents a software requirement under analysis."""
    req_id: str = Field(..., description="Unique identifier (e.g. 'REQ-001', 'SEC-04')")
    text: str = Field(..., description="The raw requirement statement")
    req_type: str = Field(default="Functional", description="Type (Functional, Performance, Security, Interface, etc.)")
    section: Optional[str] = Field(default=None, description="Section or feature module within the SRS")


class SRSContext(BaseModel):
    """
    Surrounding document context for contextual requirement analysis.
    Prevents false-positive defect flagging by giving the LLM document-level awareness.
    """
    document_title: str = Field(default="Software Requirements Specification", description="Title of the SRS document")
    domain_summary: str = Field(..., description="High-level description of the system and project domain")
    surrounding_requirements: List[str] = Field(
        default_factory=list,
        description="Neighboring or related requirements in the same section"
    )
    glossary: Dict[str, str] = Field(
        default_factory=dict,
        description="Domain terms, acronyms, and project definitions"
    )
    applicable_standards: List[str] = Field(
        default_factory=lambda: ["ISO/IEC/IEEE 29148"],
        description="Standards or style guides governing the specification"
    )

    def to_formatted_context_string(self) -> str:
        """Helper to format context into a readable prompt block."""
        parts = [
            f"Document Title: {self.document_title}",
            f"System Domain Summary: {self.domain_summary}",
        ]
        if self.glossary:
            glossary_lines = [f"  - {k}: {v}" for k, v in self.glossary.items()]
            parts.append("Project Glossary / Domain Terms:\n" + "\n".join(glossary_lines))
        if self.surrounding_requirements:
            req_lines = [f"  - {req}" for req in self.surrounding_requirements]
            parts.append("Surrounding / Related Requirements:\n" + "\n".join(req_lines))
        if self.applicable_standards:
            parts.append("Applicable Standards: " + ", ".join(self.applicable_standards))
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Layer 1 Models: Document Understanding, Scoring & Shortcoming Identification
# ---------------------------------------------------------------------------

class Shortcoming(BaseModel):
    """A candidate defect or flaw identified in the requirement."""
    defect_id: str = Field(..., description="Unique identifier for the defect (e.g., 'DEF-1')")
    attribute: QualityAttribute = Field(..., description="Quality attribute violated")
    problematic_excerpt: str = Field(..., description="Specific word, phrase, or clause exhibiting the defect")
    explanation: str = Field(..., description="Why this constitutes a shortcoming under the given attribute")
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM, description="Impact severity of the defect")


class AttributeScore(BaseModel):
    """Score and assessment for a single quality attribute."""
    attribute: QualityAttribute
    score: float = Field(..., ge=0.0, le=10.0, description="Numerical score from 0.0 (unacceptable) to 10.0 (flawless)")
    rationale: str = Field(..., description="Brief justification for the score")


class Layer1Output(BaseModel):
    """Output schema for Layer 1: Document Understanding, Scoring & Shortcoming Identification."""
    req_id: str
    attribute_scores: List[AttributeScore] = Field(
        default_factory=list,
        description="Individual scores for all 7 quality attributes"
    )
    overall_quality_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Weighted aggregate quality score (0.0 - 10.0)"
    )
    shortcomings: List[Shortcoming] = Field(
        default_factory=list,
        description="List of candidate defects identified"
    )
    document_understanding_summary: str = Field(
        ...,
        description="Brief summary of how this requirement fits into the overall document/domain"
    )


# ---------------------------------------------------------------------------
# Layer 2 Models: Defect Reasoning
# ---------------------------------------------------------------------------

class DefectEvaluation(BaseModel):
    """Detailed reasoning assessing the legitimacy of a candidate defect."""
    defect_id: str
    attribute: QualityAttribute
    original_problematic_excerpt: str
    status: DefectStatus = Field(
        ...,
        description="'justified' if genuinely a defect; 'discarded' if resolved by context or invalid"
    )
    context_reasoning: str = Field(
        ...,
        description="Detailed contextual reasoning explaining why this flag is genuine or a false positive"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in this reasoning verdict"
    )


class Layer2Output(BaseModel):
    """Output schema for Layer 2: Defect Reasoning."""
    req_id: str
    evaluations: List[DefectEvaluation] = Field(
        default_factory=list,
        description="Detailed evaluation for each candidate defect from Layer 1"
    )
    retained_defects: List[Shortcoming] = Field(
        default_factory=list,
        description="Shortcomings confirmed as justified after contextual reasoning"
    )
    discarded_defects: List[Shortcoming] = Field(
        default_factory=list,
        description="False positives or contextually resolved shortcomings that were discarded"
    )
    reasoning_summary: str = Field(
        ...,
        description="High-level synthesis of why defects were kept or eliminated"
    )


# ---------------------------------------------------------------------------
# Layer 3 Models: Solution Generation
# ---------------------------------------------------------------------------

class Layer3Output(BaseModel):
    """Output schema for Layer 3: Solution Generation."""
    req_id: str
    original_text: str
    refined_text: str = Field(
        ...,
        description="Targeted refinement resolving the retained defects without wholesale rewriting"
    )
    changes_made: List[str] = Field(
        default_factory=list,
        description="Specific surgical modifications made to the text"
    )
    addressed_defect_ids: List[str] = Field(
        default_factory=list,
        description="IDs of the retained defects resolved by this refinement"
    )
    functional_intent_preservation_rationale: str = Field(
        ...,
        description="Explanation demonstrating how the original functional intent was strictly maintained"
    )


# ---------------------------------------------------------------------------
# Layer 4 Models: Solution Reasoning & Validation
# ---------------------------------------------------------------------------

class ValidationCheck(BaseModel):
    """Individual quality check during Layer 4 solution auditing."""
    criterion: str = Field(..., description="Name of check (e.g. 'Defect Resolution', 'Ambiguity Check')")
    passed: bool = Field(..., description="Whether the refinement passed this specific check")
    observations: str = Field(..., description="Audit observation regarding this criterion")


class Layer4Output(BaseModel):
    """Output schema for Layer 4: Solution Reasoning & Validation."""
    req_id: str
    is_valid: bool = Field(..., description="True if refinement is approved for human review; False if rejected")
    verdict: ValidationVerdict = Field(..., description="Final validation verdict")
    checks: List[ValidationCheck] = Field(
        default_factory=list,
        description="Detailed checks against defect resolution, ambiguity, assumptions, and intent preservation"
    )
    unwarranted_assumptions_detected: List[str] = Field(
        default_factory=list,
        description="Any new technical or business assumptions introduced by the refinement"
    )
    new_ambiguities_detected: List[str] = Field(
        default_factory=list,
        description="Any new vague or subjective terms introduced"
    )
    critique_and_feedback: str = Field(
        ...,
        description="Independent critic summary evaluating the refinement"
    )


# ---------------------------------------------------------------------------
# Layer 5 Models: Comparison & Human-in-the-Loop Decision
# ---------------------------------------------------------------------------

class TextDiff(BaseModel):
    """Representation of the difference between original and refined text."""
    original: str
    refined: str
    diff_markup: str = Field(..., description="Inline diff markup (e.g., [-deleted-] [+added+])")
    changed_words_count: int = Field(default=0)


class HumanDecision(BaseModel):
    """Recorded decision from human-in-the-loop review."""
    status: HumanDecisionStatus = Field(default=HumanDecisionStatus.PENDING_REVIEW)
    final_text: str = Field(..., description="The final text approved by reviewer (or original if rejected)")
    reviewer_comments: Optional[str] = Field(default=None, description="Notes from the human reviewer")
    decision_timestamp: Optional[str] = Field(default=None)


class Layer5Output(BaseModel):
    """
    Output schema for Layer 5: Comparison & Human-in-the-Loop Decision.
    Presents complete traceability from original requirement through validation to human decision.
    """
    req_id: str
    original_text: str
    refined_text: Optional[str] = None
    diff: Optional[TextDiff] = None
    quality_summary: Optional[Dict[str, float]] = None
    initial_defects_count: int = 0
    justified_defects_count: int = 0
    validation_verdict: Optional[ValidationVerdict] = None
    validation_critique: Optional[str] = None
    solution_summary: Optional[str] = None
    human_decision: HumanDecision


# ---------------------------------------------------------------------------
# Pipeline Aggregate Result
# ---------------------------------------------------------------------------

class PipelineExecutionResult(BaseModel):
    """Comprehensive end-to-end trace of all 5 layers for a requirement."""
    requirement: Requirement
    layer1_result: Optional[Layer1Output] = None
    layer2_result: Optional[Layer2Output] = None
    layer3_result: Optional[Layer3Output] = None
    layer4_result: Optional[Layer4Output] = None
    layer5_result: Optional[Layer5Output] = None
    execution_time_seconds: float = 0.0
    status: str = "completed"
    error_message: Optional[str] = None
