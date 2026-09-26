"""
srs_evolution.models
~~~~~~~~~~~~~~~~~~~~
Pydantic data models for Pipeline 2: Historical SRS Version Comparison & Change Extraction.
Provides schemas for requirement parsing, cross-version alignment, change taxonomy classification,
and Pipeline-1 semantic correspondence evaluation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AlignmentType(str, Enum):
    """Method by which requirements across versions were aligned."""
    IDENTICAL_ID = "identical_id"        # Direct match by requirement identifier/tag
    SEMANTIC_MATCH = "semantic_match"    # Aligned via cosine/vector similarity (renamed/renumbered)
    ADDED = "added"                      # Requirement introduced in Version N+1 only
    DELETED = "deleted"                  # Requirement deprecated/removed in Version N


class ChangeCategory(str, Enum):
    """
    Empirical change taxonomy distinguishing quality refinements from
    stakeholder scope shifts and superficial edits.
    """
    UNCHANGED = "UNCHANGED"
    EDITORIAL_TEXTUAL = "EDITORIAL_TEXTUAL"
    AMBIGUITY_REDUCTION = "AMBIGUITY_REDUCTION"
    COMPLETENESS_IMPROVEMENT = "COMPLETENESS_IMPROVEMENT"
    CONSTRAINT_REFINEMENT = "CONSTRAINT_REFINEMENT"
    CONSISTENCY_CORRECTION = "CONSISTENCY_CORRECTION"
    REQUIREMENT_ADDED = "REQUIREMENT_ADDED"
    REQUIREMENT_DELETED = "REQUIREMENT_DELETED"
    FUNCTIONAL_SCOPE_CHANGE = "FUNCTIONAL_SCOPE_CHANGE"


class CorrespondenceRating(str, Enum):
    """
    Three-way semantic correspondence evaluation between Pipeline-1 proposals
    and actual historical human changes in Version N+1.
    """
    MATCHED = "MATCHED"                    # System independently surfaced and resolved what stakeholders actually fixed
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"# System flagged the correct flaw area but proposed an alternate resolution
    NOT_MATCHED = "NOT_MATCHED"            # System suggestion has no counterpart in Version N+1 evolution


# ---------------------------------------------------------------------------
# Requirement Unit & Alignment Models
# ---------------------------------------------------------------------------

class RequirementUnit(BaseModel):
    """A discrete requirement statement extracted from an SRS document."""
    req_id: str = Field(..., description="Extracted requirement tag or synthetic ID (e.g. 'REQ-101', 'SYS-SAF-1')")
    text: str = Field(..., description="The normative requirement statement body")
    section: Optional[str] = Field(default=None, description="Section heading or feature module")
    version: str = Field(default="N", description="Document version identifier (e.g. 'v1.1', 'v3.0')")
    line_number: Optional[int] = Field(default=None, description="Line offset in source document")
    raw_header: Optional[str] = Field(default=None, description="Raw heading or bullet prefix if present")


class AlignedRequirementPair(BaseModel):
    """A pair of aligned requirements representing evolution from Version N to Version N+1."""
    req_id_v1: Optional[str] = Field(default=None, description="Requirement ID in Version N (None if newly added)")
    req_id_v2: Optional[str] = Field(default=None, description="Requirement ID in Version N+1 (None if deleted)")
    text_v1: Optional[str] = Field(default=None, description="Statement in Version N")
    text_v2: Optional[str] = Field(default=None, description="Statement in Version N+1")
    section_v1: Optional[str] = None
    section_v2: Optional[str] = None
    alignment_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Similarity score / confidence")
    alignment_type: AlignmentType = Field(default=AlignmentType.IDENTICAL_ID)


# ---------------------------------------------------------------------------
# Change Classification Models
# ---------------------------------------------------------------------------

QUALITY_REFINEMENT_CATEGORIES = {
    ChangeCategory.AMBIGUITY_REDUCTION,
    ChangeCategory.COMPLETENESS_IMPROVEMENT,
    ChangeCategory.CONSTRAINT_REFINEMENT,
    ChangeCategory.CONSISTENCY_CORRECTION,
}


class HistoricalChangeRecord(BaseModel):
    """Structured record of the empirical change observed between Version N and Version N+1."""
    req_id: str = Field(..., description="Primary requirement identifier (v1 ID, or v2 if newly added)")
    req_id_v_n: Optional[str] = None
    req_id_v_n1: Optional[str] = None
    text_v_n: Optional[str] = None
    text_v_n1: Optional[str] = None
    change_category: ChangeCategory = Field(..., description="Taxonomy classification of the change")
    summary_of_change: str = Field(..., description="Concise explanation of what was modified")
    detailed_diff: Optional[str] = Field(default=None, description="Word or phrase-level diff")
    is_quality_refinement: bool = Field(
        default=False,
        description="True if change represents an ISO 29148 quality repair; False if scope change/editorial/addition/deletion"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Correspondence Benchmark Evaluation Models
# ---------------------------------------------------------------------------

class EvolutionBenchmarkResult(BaseModel):
    """
    Comparison record mapping Pipeline-1 analyzer suggestions against
    the ground-truth historical evolution observed in Version N+1.
    """
    req_id: str
    original_v_n_text: str
    layer1_defects_flagged: List[str] = Field(default_factory=list)
    layer3_refinement_text: Optional[str] = None
    v_next_actual_text: Optional[str] = None
    historical_change_category: ChangeCategory
    correspondence_rating: CorrespondenceRating
    explanation: str = Field(..., description="Chain-of-thought rationale explaining the match rating")
    is_true_positive_prediction: bool = Field(
        default=False,
        description="True if Pipeline-1 successfully anticipated a historical quality refinement"
    )


class BenchmarkSummaryReport(BaseModel):
    """Aggregate evaluation metrics across the historical evolution dataset."""
    total_aligned_pairs: int = 0
    unchanged_count: int = 0
    editorial_count: int = 0
    quality_refinements_count: int = 0
    scope_changes_count: int = 0
    added_count: int = 0
    deleted_count: int = 0
    
    # Correspondence Metrics
    total_pipeline_proposals_evaluated: int = 0
    matched_count: int = 0
    partially_matched_count: int = 0
    not_matched_count: int = 0
    
    match_rate: float = Field(0.0, description="Proportion of proposals that were Matched or Partially Matched")
    strict_match_rate: float = Field(0.0, description="Proportion of proposals that were strictly Matched")
    quality_prediction_precision: float = Field(
        0.0,
        description="Proportion of Pipeline-1 refinements that corresponded to genuine historical quality fixes"
    )
