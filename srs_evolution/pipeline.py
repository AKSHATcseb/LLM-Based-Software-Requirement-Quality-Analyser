"""
srs_evolution.pipeline
~~~~~~~~~~~~~~~~~~~~~~
Orchestrator for Pipeline 2: Historical SRS Version Comparison & Change Extraction.
Executes the end-to-end flow:
1. Document ingestion and requirement parsing
2. Requirement alignment across Version N and Version N+1
3. Semantic change classification into the SQAM research taxonomy
4. Execution/ingestion of Pipeline-1 quality analysis on Version N
5. Semantic correspondence matching against Version N+1 ground truth
6. Exporting comprehensive evaluation metrics into JSON, CSV, and Markdown
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from sqam_analyzer.llm_provider import BaseLLMClient, MockLLMClient
from sqam_analyzer.models import PipelineExecutionResult, Requirement, SRSContext
from sqam_analyzer.pipeline import RequirementQualityPipeline
from srs_evolution.aligner import RequirementAligner, SRSParser
from srs_evolution.change_classifier import ChangeClassifier
from srs_evolution.evaluator import EvolutionEvaluator
from srs_evolution.models import (
    AlignedRequirementPair,
    BenchmarkSummaryReport,
    EvolutionBenchmarkResult,
    HistoricalChangeRecord,
    RequirementUnit,
)

logger = logging.getLogger(__name__)


class HistoricalEvolutionPipeline:
    """
    End-to-End Orchestrator for Historical SRS Version Comparison and Empirical Evaluation.
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        similarity_threshold: float = 0.45,
        doc_prefix: str = "REQ",
    ):
        self.llm_client = llm_client or MockLLMClient()
        self.parser = SRSParser(doc_prefix=doc_prefix)
        self.aligner = RequirementAligner(similarity_threshold=similarity_threshold)
        self.classifier = ChangeClassifier(llm_client=self.llm_client)
        self.evaluator = EvolutionEvaluator(llm_client=self.llm_client)
        self.analyzer_pipeline = RequirementQualityPipeline(default_llm=self.llm_client)

    def run_comparison(
        self,
        v_n_source: Union[str, Path, List[RequirementUnit]],
        v_n1_source: Union[str, Path, List[RequirementUnit]],
        srs_context: Optional[SRSContext] = None,
        run_analyzer: bool = True,
        existing_analyzer_results: Optional[List[PipelineExecutionResult]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Executes complete evolution extraction and benchmark evaluation:
        1. Parses Version N and Version N+1.
        2. Aligns requirement units across versions.
        3. Classifies all changes into the SQAM taxonomy.
        4. (Optional) Analyzes Version N requirements using the 5-layer pipeline.
        5. Evaluates semantic correspondence (Matched / Partially Matched / Not Matched).
        """
        logger.info("Starting Historical Evolution Pipeline...")

        # -------------------------------------------------------------------
        # Step 1: Parsing
        # -------------------------------------------------------------------
        if isinstance(v_n_source, list) and all(isinstance(r, RequirementUnit) for r in v_n_source):
            v1_reqs = v_n_source
        else:
            v1_reqs = self.parser.parse_document(v_n_source, version_label="N")

        if isinstance(v_n1_source, list) and all(isinstance(r, RequirementUnit) for r in v_n1_source):
            v2_reqs = v_n1_source
        else:
            v2_reqs = self.parser.parse_document(v_n1_source, version_label="N+1")

        logger.info("Parsed %d requirements from vN, %d from vN+1", len(v1_reqs), len(v2_reqs))

        # -------------------------------------------------------------------
        # Step 2: Alignment
        # -------------------------------------------------------------------
        aligned_pairs = self.aligner.align(v1_reqs, v2_reqs)

        # -------------------------------------------------------------------
        # Step 3: Change Classification
        # -------------------------------------------------------------------
        change_records = self.classifier.classify_all(aligned_pairs, temperature=temperature)

        # -------------------------------------------------------------------
        # Step 4: Pipeline-1 Quality Analysis on Version N
        # -------------------------------------------------------------------
        analyzer_results: List[PipelineExecutionResult] = []

        if run_analyzer:
            effective_context = srs_context or SRSContext(
                document_title="Historical SRS Evolution Benchmark",
                domain_summary="Baseline domain specification for versioned requirements analysis.",
            )

            # Analyze only requirements present in Version N
            v1_pairs_with_text = [p for p in aligned_pairs if p.text_v1]

            if existing_analyzer_results:
                analyzer_results = existing_analyzer_results
            else:
                logger.info("Executing Pipeline-1 on %d Version N requirements...", len(v1_pairs_with_text))
                for pair in v1_pairs_with_text:
                    req_obj = Requirement(
                        req_id=pair.req_id_v1 or "REQ-01",
                        text=pair.text_v1,
                        section=pair.section_v1 or "General",
                    )
                    res = self.analyzer_pipeline.analyze_requirement(
                        requirement=req_obj,
                        srs_context=effective_context,
                        temperature=temperature,
                    )
                    analyzer_results.append(res)

        # -------------------------------------------------------------------
        # Step 5: Correspondence Evaluation
        # -------------------------------------------------------------------
        benchmark_results: List[EvolutionBenchmarkResult] = []
        summary = BenchmarkSummaryReport()

        if analyzer_results:
            benchmark_results, summary = self.evaluator.evaluate_batch(
                pipeline_results=analyzer_results,
                change_records=change_records,
                temperature=temperature,
            )

        return {
            "v1_requirements": v1_reqs,
            "v2_requirements": v2_reqs,
            "aligned_pairs": aligned_pairs,
            "change_records": change_records,
            "analyzer_results": analyzer_results,
            "benchmark_results": benchmark_results,
            "summary": summary,
        }

    def export_csv(self, execution_output: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Exports benchmark comparison results into a structured CSV file."""
        benchmark_results: List[EvolutionBenchmarkResult] = execution_output.get("benchmark_results", [])
        change_records: List[HistoricalChangeRecord] = execution_output.get("change_records", [])
        change_lookup = {c.req_id: c for c in change_records}

        path = Path(file_path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Requirement_ID",
                "Version_N_Text",
                "Pipeline1_Defects_Flagged",
                "Pipeline1_Refinement_Text",
                "Version_N1_Actual_Text",
                "Historical_Change_Category",
                "Is_Quality_Refinement",
                "Correspondence_Rating",
                "Is_True_Positive_Prediction",
                "Evaluation_Explanation",
            ])

            for b in benchmark_results:
                c = change_lookup.get(b.req_id)
                writer.writerow([
                    b.req_id,
                    b.original_v_n_text,
                    "; ".join(b.layer1_defects_flagged),
                    b.layer3_refinement_text or "",
                    b.v_next_actual_text or "",
                    b.historical_change_category.value,
                    "Yes" if (c and c.is_quality_refinement) else "No",
                    b.correspondence_rating.value,
                    "Yes" if b.is_true_positive_prediction else "No",
                    b.explanation,
                ])

        logger.info("Successfully exported benchmark CSV to %s", path)

    def export_json(self, execution_output: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Exports full execution trace into structured JSON format."""
        serializable = {
            "summary": execution_output["summary"].model_dump(),
            "change_records": [c.model_dump() for c in execution_output["change_records"]],
            "benchmark_results": [b.model_dump() for b in execution_output["benchmark_results"]],
        }
        path = Path(file_path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)

        logger.info("Successfully exported benchmark JSON to %s", path)

    def render_markdown_report(
        self,
        execution_output: Dict[str, Any],
        project_title: str = "SRS Evolution Benchmark",
    ) -> str:
        """Renders an academic publication-ready Markdown evaluation summary."""
        summary: BenchmarkSummaryReport = execution_output["summary"]
        changes: List[HistoricalChangeRecord] = execution_output["change_records"]
        benchmark_results: List[EvolutionBenchmarkResult] = execution_output["benchmark_results"]

        lines = [
            f"# Historical SRS Evolution & Benchmark Report: {project_title}",
            "",
            "## 1. Empirical Change Classification Breakdown",
            "",
            "| Change Taxonomy Category | Count | Type |",
            "| :--- | :---: | :--- |",
            f"| **UNCHANGED** | {summary.unchanged_count} | Baseline / Compliant |",
            f"| **EDITORIAL_TEXTUAL** | {summary.editorial_count} | Formatting / Superficial |",
            f"| **QUALITY_REFINEMENTS** | **{summary.quality_refinements_count}** | **ISO 29148 Quality Repairs** |",
            f"| **FUNCTIONAL_SCOPE_CHANGE** | {summary.scope_changes_count} | Business / Feature Scope Shift |",
            f"| **REQUIREMENT_ADDED** | {summary.added_count} | New Capability in vN+1 |",
            f"| **REQUIREMENT_DELETED** | {summary.deleted_count} | Deprecated in vN |",
            f"| **TOTAL ALIGNED UNITS** | **{summary.total_aligned_pairs}** | |",
            "",
            "## 2. Pipeline-1 Semantic Correspondence (vs Version N+1 Reality)",
            "",
            "| Evaluation Metric | Observed Value | Description |",
            "| :--- | :---: | :--- |",
            f"| **Total Pipeline Proposals** | **{summary.total_pipeline_proposals_evaluated}** | Requirements where Pipeline-1 proposed edits |",
            f"| **MATCHED** | **{summary.matched_count}** | Independent discovery matching actual historical fix |",
            f"| **PARTIALLY_MATCHED** | **{summary.partially_matched_count}** | Flagged correct defect with alternative fix |",
            f"| **NOT_MATCHED** | **{summary.not_matched_count}** | Proposal had no counterpart in Version N+1 |",
            f"| **Match Rate (Strict + Partial)** | **{summary.match_rate:.1f}%** | Overall correspondence rate |",
            f"| **Strict Match Rate** | **{summary.strict_match_rate:.1f}%** | Close semantic correspondence |",
            f"| **Quality Prediction Precision** | **{summary.quality_prediction_precision:.1f}%** | Precision against human quality fixes |",
            "",
            "## 3. Itemized Evolution & Evaluation Findings",
            "",
            "| Req ID | Version N (Earlier Input) | Pipeline-1 Refinement | Version N+1 (Ground Truth) | Historical Category | Correspondence |",
            "| :--- | :--- | :--- | :--- | :---: | :---: |",
        ]

        for b in benchmark_results:
            c_tag = f"`{b.correspondence_rating.value}`"
            v1_clean = b.original_v_n_text.replace("\n", " ").replace("|", "\\|")
            ref_clean = (b.layer3_refinement_text or b.original_v_n_text).replace("\n", " ").replace("|", "\\|")
            v2_clean = (b.v_next_actual_text or b.original_v_n_text).replace("\n", " ").replace("|", "\\|")

            lines.append(
                f"| {b.req_id} | {v1_clean} | {ref_clean} | {v2_clean} | {b.historical_change_category.value} | {c_tag} |"
            )

        return "\n".join(lines)
