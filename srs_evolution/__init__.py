"""
srs_evolution
~~~~~~~~~~~~~
Pipeline 2: Historical SRS Version Comparison & Change Extraction.
Extracts, aligns, and classifies empirical human modifications between Version N and Version N+1,
and semantically evaluates Pipeline-1 proposals against historical evolution ground truth.
"""

from srs_evolution.aligner import RequirementAligner, SRSParser
from srs_evolution.change_classifier import ChangeClassifier
from srs_evolution.evaluator import EvolutionEvaluator
from srs_evolution.models import (
    AlignedRequirementPair,
    AlignmentType,
    BenchmarkSummaryReport,
    ChangeCategory,
    CorrespondenceRating,
    EvolutionBenchmarkResult,
    HistoricalChangeRecord,
    QUALITY_REFINEMENT_CATEGORIES,
    RequirementUnit,
)
from srs_evolution.pipeline import HistoricalEvolutionPipeline

__all__ = [
    # Models
    "RequirementUnit",
    "AlignedRequirementPair",
    "AlignmentType",
    "ChangeCategory",
    "CorrespondenceRating",
    "HistoricalChangeRecord",
    "EvolutionBenchmarkResult",
    "BenchmarkSummaryReport",
    "QUALITY_REFINEMENT_CATEGORIES",
    # Modules
    "SRSParser",
    "RequirementAligner",
    "ChangeClassifier",
    "EvolutionEvaluator",
    "HistoricalEvolutionPipeline",
]
