"""
tests/test_evolution.py
~~~~~~~~~~~~~~~~~~~~~~~
Unit test suite for Pipeline 2: Historical SRS Version Comparison & Change Extraction.
Covers:
- Document parsing & requirement unit extraction
- Cross-version requirement alignment (Exact ID, Semantic Match, Added, Deleted)
- Change taxonomy classification (Quality Refinements vs Scope Changes)
- Pipeline-1 semantic correspondence evaluation (MATCHED, PARTIALLY_MATCHED, NOT_MATCHED)
- End-to-End evolution pipeline orchestration and CSV/JSON export
"""

import os
import tempfile
import unittest
from pathlib import Path

from sqam_analyzer.llm_provider import MockLLMClient
from sqam_analyzer.models import PipelineExecutionResult, Requirement, SRSContext
from srs_evolution import (
    AlignedRequirementPair,
    AlignmentType,
    ChangeCategory,
    ChangeClassifier,
    CorrespondenceRating,
    EvolutionEvaluator,
    HistoricalChangeRecord,
    HistoricalEvolutionPipeline,
    RequirementAligner,
    RequirementUnit,
    SRSParser,
)


class TestSRSEvolutionPipeline(unittest.TestCase):
    """Test suite for Pipeline 2 modules."""

    def setUp(self):
        self.mock_llm = MockLLMClient()
        self.parser = SRSParser(doc_prefix="REQ")
        self.aligner = RequirementAligner(similarity_threshold=0.45)
        self.classifier = ChangeClassifier(llm_client=self.mock_llm)
        self.evaluator = EvolutionEvaluator(llm_client=self.mock_llm)

    # -----------------------------------------------------------------------
    # 1. Parsing Tests
    # -----------------------------------------------------------------------
    def test_parser_extracts_tagged_and_synthetic_requirements(self):
        sample_doc = """
# 1. System Overview
The system is designed for autonomous train operation.

# 3. Functional Requirements
## 3.1 Braking System
REQ-BRK-01: The train controller shall initiate service braking when red aspect is passed.
The system shall continuously monitor brake pipe pressure.
Copyright 2026 Rail Corp. All rights reserved.
        """
        reqs = self.parser.parse_text(sample_doc, version_label="N")
        self.assertEqual(len(reqs), 2)

        # Check explicit ID extracted
        self.assertEqual(reqs[0].req_id, "REQ-BRK-01")
        self.assertIn("service braking", reqs[0].text)
        self.assertEqual(reqs[0].section, "3.1 Braking System")

        # Check synthetic ID generated for untagged shall
        self.assertTrue(reqs[1].req_id.startswith("REQ-N-"))
        self.assertIn("brake pipe pressure", reqs[1].text)

    # -----------------------------------------------------------------------
    # 2. Alignment Tests
    # -----------------------------------------------------------------------
    def test_alignment_exact_id(self):
        v1 = [
            RequirementUnit(req_id="REQ-101", text="The system shall quickly alert the user.", section="Alerts")
        ]
        v2 = [
            RequirementUnit(req_id="REQ-101", text="The system shall alert the user within 500ms.", section="Alerts")
        ]
        pairs = self.aligner.align(v1, v2)

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].alignment_type, AlignmentType.IDENTICAL_ID)
        self.assertEqual(pairs[0].req_id_v1, "REQ-101")
        self.assertEqual(pairs[0].req_id_v2, "REQ-101")
        self.assertEqual(pairs[0].alignment_confidence, 1.0)

    def test_alignment_semantic_fallback_and_lifecycle(self):
        # Renumbered / renamed requirement
        v1 = [
            RequirementUnit(req_id="OLD-01", text="The autopilot shall maintain altitude at 10000 feet.", section="Nav"),
            RequirementUnit(req_id="DEL-99", text="The system shall display legacy analog telemetry.", section="UI"),
        ]
        v2 = [
            RequirementUnit(req_id="NEW-01", text="The autopilot shall maintain aircraft altitude at 10000 feet.", section="Nav"),
            RequirementUnit(req_id="ADD-02", text="The system shall support ADS-B In broadcast reception.", section="Comms"),
        ]
        pairs = self.aligner.align(v1, v2)

        types = {p.alignment_type for p in pairs}
        self.assertIn(AlignmentType.SEMANTIC_MATCH, types)
        self.assertIn(AlignmentType.DELETED, types)
        self.assertIn(AlignmentType.ADDED, types)

        sem_pair = next(p for p in pairs if p.alignment_type == AlignmentType.SEMANTIC_MATCH)
        self.assertEqual(sem_pair.req_id_v1, "OLD-01")
        self.assertEqual(sem_pair.req_id_v2, "NEW-01")
        self.assertGreater(sem_pair.alignment_confidence, 0.45)

    # -----------------------------------------------------------------------
    # 3. Change Classifier Tests
    # -----------------------------------------------------------------------
    def test_classifier_unchanged_short_circuit(self):
        pair = AlignedRequirementPair(
            req_id_v1="REQ-01",
            req_id_v2="REQ-01",
            text_v1="The system shall log all transactions.",
            text_v2="The system shall log all transactions.",
            alignment_type=AlignmentType.IDENTICAL_ID,
        )
        record = self.classifier.classify_pair(pair)

        self.assertEqual(record.change_category, ChangeCategory.UNCHANGED)
        self.assertFalse(record.is_quality_refinement)

    def test_classifier_ambiguity_reduction(self):
        pair = AlignedRequirementPair(
            req_id_v1="REQ-02",
            req_id_v2="REQ-02",
            text_v1="The system shall quickly process login requests.",
            text_v2="The system shall process login requests within 500 milliseconds.",
            alignment_type=AlignmentType.IDENTICAL_ID,
        )
        record = self.classifier.classify_pair(pair)

        self.assertEqual(record.change_category, ChangeCategory.AMBIGUITY_REDUCTION)
        self.assertTrue(record.is_quality_refinement)
        self.assertIn("[-quickly-]", record.detailed_diff)

    def test_classifier_added_and_deleted(self):
        add_pair = AlignedRequirementPair(
            req_id_v2="REQ-NEW",
            text_v2="The system shall stream telemetry.",
            alignment_type=AlignmentType.ADDED,
        )
        del_pair = AlignedRequirementPair(
            req_id_v1="REQ-OLD",
            text_v1="The system shall use dialup modem.",
            alignment_type=AlignmentType.DELETED,
        )

        add_rec = self.classifier.classify_pair(add_pair)
        del_rec = self.classifier.classify_pair(del_pair)

        self.assertEqual(add_rec.change_category, ChangeCategory.REQUIREMENT_ADDED)
        self.assertEqual(del_rec.change_category, ChangeCategory.REQUIREMENT_DELETED)

    # -----------------------------------------------------------------------
    # 4. Correspondence Evaluator Tests
    # -----------------------------------------------------------------------
    def test_evaluator_matched_prediction(self):
        # Pipeline-1 independently parameterized "quickly" to 500ms
        p_res = PipelineExecutionResult(
            requirement=Requirement(
                req_id="REQ-01",
                text="The system shall quickly process alerts.",
            )
        )
        from sqam_analyzer.models import Layer3Output
        p_res.layer3_result = Layer3Output(
            req_id="REQ-01",
            original_text="The system shall quickly process alerts.",
            refined_text="The system shall process alerts within 500 milliseconds.",
            changes_made=["Replaced quickly with 500ms"],
            functional_intent_preservation_rationale="Maintained alerting.",
        )

        # Historical ground truth in Version N+1
        change_rec = HistoricalChangeRecord(
            req_id="REQ-01",
            text_v_n="The system shall quickly process alerts.",
            text_v_n1="The system shall process alerts within 500 milliseconds of detection.",
            change_category=ChangeCategory.AMBIGUITY_REDUCTION,
            summary_of_change="Added 500ms constraint in Version N+1.",
            is_quality_refinement=True,
        )

        res = self.evaluator.evaluate_correspondence(p_res, change_rec)

        self.assertEqual(res.correspondence_rating, CorrespondenceRating.MATCHED)
        self.assertTrue(res.is_true_positive_prediction)
        self.assertIn("anticipated", res.explanation.lower())

    def test_evaluator_not_matched_unrelated(self):
        p_res = PipelineExecutionResult(
            requirement=Requirement(
                req_id="REQ-02",
                text="The system shall log transactions.",
            )
        )
        change_rec = HistoricalChangeRecord(
            req_id="REQ-02",
            text_v_n="The system shall log transactions.",
            text_v_n1="The system shall log transactions.",
            change_category=ChangeCategory.UNCHANGED,
            summary_of_change="Unchanged.",
            is_quality_refinement=False,
        )
        from sqam_analyzer.models import Layer3Output
        p_res.layer3_result = Layer3Output(
            req_id="REQ-02",
            original_text="The system shall log transactions.",
            refined_text="The system shall log transactions to an encrypted SQL table.",
            changes_made=["Added encryption"],
            functional_intent_preservation_rationale="Logged transactions.",
        )

        res = self.evaluator.evaluate_correspondence(p_res, change_rec)
        self.assertEqual(res.correspondence_rating, CorrespondenceRating.NOT_MATCHED)

    # -----------------------------------------------------------------------
    # 5. End-to-End Evolution Pipeline Orchestrator Test
    # -----------------------------------------------------------------------
    def test_end_to_end_pipeline_and_export(self):
        pipeline = HistoricalEvolutionPipeline(llm_client=self.mock_llm)

        v1_text = """
# Section 1
REQ-01: The system shall quickly process transactions.
REQ-02: The system shall verify credentials.
        """
        v2_text = """
# Section 1
REQ-01: The system shall process transactions within 500 milliseconds.
REQ-02: The system shall verify credentials.
REQ-03: The system shall support multi-factor authentication.
        """

        output = pipeline.run_comparison(
            v_n_source=v1_text,
            v_n1_source=v2_text,
            srs_context=SRSContext(domain_summary="Banking Transaction Engine"),
            run_analyzer=True,
        )

        self.assertEqual(len(output["v1_requirements"]), 2)
        self.assertEqual(len(output["v2_requirements"]), 3)
        self.assertGreaterEqual(len(output["aligned_pairs"]), 3)
        self.assertGreaterEqual(len(output["change_records"]), 3)

        summary = output["summary"]
        self.assertGreaterEqual(summary.total_aligned_pairs, 3)

        # Test CSV export
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
        try:
            pipeline.export_csv(output, csv_path)
            self.assertTrue(os.path.exists(csv_path))
            content = Path(csv_path).read_text(encoding="utf-8")
            self.assertIn("Requirement_ID", content)
            self.assertIn("REQ-01", content)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

        # Test JSON export
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_json:
            json_path = tmp_json.name
        try:
            pipeline.export_json(output, json_path)
            self.assertTrue(os.path.exists(json_path))
            content = Path(json_path).read_text(encoding="utf-8")
            self.assertIn('"summary"', content)
            self.assertIn('"benchmark_results"', content)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)

        # Test Markdown report rendering
        md_report = pipeline.render_markdown_report(output, project_title="Test Evolution")
        self.assertIn("# Historical SRS Evolution & Benchmark Report: Test Evolution", md_report)
        self.assertIn("Pipeline-1 Semantic Correspondence", md_report)

    def test_version_file_discovery_modes(self):
        from run_evolution_pipeline import get_version_files_for_project
        # Project 14 has 1.pdf, 2.pdf, 3.pdf -> later draft is 2.pdf, final is 3.pdf
        draft_later, final_later = get_version_files_for_project("14", mode="later_vs_final")
        self.assertEqual(draft_later.name, "2.pdf")
        self.assertEqual(final_later.name, "3.pdf")

        draft_early, final_early = get_version_files_for_project("14", mode="earliest_vs_final")
        self.assertEqual(draft_early.name, "1.pdf")
        self.assertEqual(final_early.name, "3.pdf")

        # Project 1_FROG has 2 files: SRS_v1.1.pdf and Software_Requirements_Specification_v30.pdf
        draft_frog, final_frog = get_version_files_for_project("1_FROG", mode="later_vs_final")
        self.assertEqual(draft_frog.name, "SRS_v1.1.pdf")
        self.assertEqual(final_frog.name, "Software_Requirements_Specification_v30.pdf")


if __name__ == "__main__":
    unittest.main()
