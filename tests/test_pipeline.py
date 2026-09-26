"""
tests/test_pipeline.py
~~~~~~~~~~~~~~~~~~~~~~
Comprehensive unit test suite for the 5-layer Software Requirement Quality Analyzer.
Covers:
- Layer 1 scoring against all 7 ISO/IEC/IEEE 29148 quality attributes
- Layer 2 contextual defect reasoning & false-positive elimination
- Layer 3 targeted refinement & functional intent preservation
- Layer 4 independent validation & rejection criteria
- Layer 5 diff generation, human review sign-offs, and Markdown export
- Full end-to-end pipeline execution
- Custom prompt template injection
"""

import unittest
from sqam_analyzer import (
    DefectStatus,
    HumanDecisionStatus,
    Layer1DocumentScorer,
    Layer2DefectReasoner,
    Layer3SolutionGenerator,
    Layer4SolutionValidator,
    Layer5HumanDecisionManager,
    MockLLMClient,
    QualityAttribute,
    Requirement,
    RequirementQualityPipeline,
    Shortcoming,
    SRSContext,
    ValidationVerdict,
)
from sqam_analyzer.diff_utils import compute_word_diff


class TestSQAMPipeline(unittest.TestCase):
    """Test suite for SQAM 5-layer pipeline components."""

    def setUp(self):
        self.mock_llm = MockLLMClient()
        self.srs_context = SRSContext(
            document_title="Test Flight Control System SRS",
            domain_summary="Avionics autopilot and flight surface control system with sub-second hard real-time requirements.",
            glossary={
                "Flight Surface": "Ailerons, elevators, and rudder responsible for aerodynamic attitude control.",
                "Vital Anomaly": "Uncommanded attitude change exceeding 5 degrees per second.",
            },
            surrounding_requirements=[
                "REQ-AV-01: The system shall poll attitude sensors at a frequency of 100 Hz.",
                "REQ-AV-02: All control commands shall be logged to non-volatile flash memory.",
            ],
            applicable_standards=["DO-178C Level A", "ISO/IEC/IEEE 29148"],
        )

        self.sample_req = Requirement(
            req_id="REQ-TEST-01",
            req_type="Functional",
            section="Flight Controls",
            text="The system shall quickly adjust the flight surface when a perturbation occurs.",
        )

    # -----------------------------------------------------------------------
    # Layer 1 Tests
    # -----------------------------------------------------------------------
    def test_layer1_scoring_and_attributes(self):
        scorer = Layer1DocumentScorer(llm_client=self.mock_llm)
        output = scorer.execute(self.sample_req, self.srs_context)

        self.assertEqual(output.req_id, "REQ-TEST-01")
        self.assertGreaterEqual(output.overall_quality_score, 0.0)
        self.assertLessEqual(output.overall_quality_score, 10.0)

        # Verify all 7 standard quality attributes are present
        evaluated_attrs = {score.attribute for score in output.attribute_scores}
        expected_attrs = {
            QualityAttribute.UNAMBIGUITY,
            QualityAttribute.COMPLETENESS,
            QualityAttribute.CONSISTENCY,
            QualityAttribute.CONFORMANCE,
            QualityAttribute.CORRECTNESS,
            QualityAttribute.SINGULARITY,
            QualityAttribute.VERIFIABILITY_FEASIBILITY,
        }
        self.assertEqual(evaluated_attrs, expected_attrs)

        # Check shortcomings
        self.assertTrue(len(output.shortcomings) > 0)
        self.assertTrue(any(s.problematic_excerpt == "quickly" for s in output.shortcomings))

    # -----------------------------------------------------------------------
    # Layer 2 Tests: Defect Reasoning & False Positive Elimination
    # -----------------------------------------------------------------------
    def test_layer2_defect_reasoning_and_context_filtering(self):
        reasoner = Layer2DefectReasoner(llm_client=self.mock_llm)

        # Two candidate defects:
        # 1. 'quickly' (unjustified ambiguity -> should be JUSTIFIED)
        # 2. 'Vital Anomaly' (defined in glossary -> should be DISCARDED as false positive)
        candidate_defects = [
            Shortcoming(
                defect_id="DEF-001",
                attribute=QualityAttribute.UNAMBIGUITY,
                problematic_excerpt="quickly",
                explanation="Subjective adverb lacking time constraint.",
            ),
            Shortcoming(
                defect_id="DEF-002",
                attribute=QualityAttribute.UNAMBIGUITY,
                problematic_excerpt="Vital Anomaly",
                explanation="Requires medical or physical definition.",
            ),
        ]

        output = reasoner.execute(self.sample_req, self.srs_context, candidate_defects)

        retained_ids = [d.defect_id for d in output.retained_defects]
        discarded_ids = [d.defect_id for d in output.discarded_defects]

        # 'quickly' retained
        self.assertIn("DEF-001", retained_ids)
        # 'Vital Anomaly' discarded because it's defined in the glossary
        self.assertIn("DEF-002", discarded_ids)

    def test_layer2_empty_candidate_defects(self):
        reasoner = Layer2DefectReasoner(llm_client=self.mock_llm)
        output = reasoner.execute(self.sample_req, self.srs_context, candidate_shortcomings=[])

        self.assertEqual(len(output.retained_defects), 0)
        self.assertEqual(len(output.discarded_defects), 0)
        self.assertIn("compliant", output.reasoning_summary.lower())

    # -----------------------------------------------------------------------
    # Layer 3 Tests: Solution Generation
    # -----------------------------------------------------------------------
    def test_layer3_solution_generation(self):
        generator = Layer3SolutionGenerator(llm_client=self.mock_llm)
        retained = [
            Shortcoming(
                defect_id="DEF-001",
                attribute=QualityAttribute.UNAMBIGUITY,
                problematic_excerpt="quickly",
                explanation="Subjective adverb.",
            )
        ]

        output = generator.execute(self.sample_req, self.srs_context, retained)

        self.assertNotEqual(output.refined_text, self.sample_req.text)
        self.assertIn("milliseconds", output.refined_text.lower())
        self.assertTrue(len(output.changes_made) > 0)
        self.assertIn("DEF-001", output.addressed_defect_ids)
        self.assertTrue(len(output.functional_intent_preservation_rationale) > 0)

    # -----------------------------------------------------------------------
    # Layer 4 Tests: Solution Validation & Auditor
    # -----------------------------------------------------------------------
    def test_layer4_solution_validation_pass(self):
        generator = Layer3SolutionGenerator(llm_client=self.mock_llm)
        validator = Layer4SolutionValidator(llm_client=self.mock_llm)

        retained = [
            Shortcoming(
                defect_id="DEF-001",
                attribute=QualityAttribute.UNAMBIGUITY,
                problematic_excerpt="quickly",
                explanation="Subjective adverb.",
            )
        ]
        l3_output = generator.execute(self.sample_req, self.srs_context, retained)
        l4_output = validator.execute(self.sample_req, self.srs_context, retained, l3_output)

        self.assertTrue(l4_output.is_valid)
        self.assertEqual(l4_output.verdict, ValidationVerdict.VALIDATED)
        self.assertTrue(len(l4_output.checks) >= 5)
        for check in l4_output.checks:
            self.assertTrue(check.passed)

    def test_layer4_solution_validation_reject(self):
        # Create a mock that returns rejection for Layer 4
        rejection_mock = MockLLMClient(
            custom_responses={
                "Audit and validate the proposed requirement refinement": """{
                    "req_id": "REQ-TEST-01",
                    "is_valid": false,
                    "verdict": "rejected",
                    "checks": [
                        {"criterion": "Defect Resolution", "passed": true, "observations": "Fixed latency."},
                        {"criterion": "No New Ambiguities", "passed": false, "observations": "Added subjective term 'smoothly'."},
                        {"criterion": "No Unwarranted Assumptions", "passed": false, "observations": "Assumed 10Gbps Ethernet network protocol not in SRS."},
                        {"criterion": "Functional Intent Preservation", "passed": true, "observations": "Same intent."},
                        {"criterion": "Syntactic Conformance", "passed": true, "observations": "Valid grammar."}
                    ],
                    "unwarranted_assumptions_detected": ["Assumed 10Gbps Ethernet network protocol"],
                    "new_ambiguities_detected": ["smoothly"],
                    "critique_and_feedback": "Refinement introduces unwarranted architectural assumptions and new subjective adverbs. Rejected."
                }"""
            }
        )
        validator = Layer4SolutionValidator(llm_client=rejection_mock)
        retained = [
            Shortcoming(
                defect_id="DEF-001",
                attribute=QualityAttribute.UNAMBIGUITY,
                problematic_excerpt="quickly",
                explanation="Subjective adverb.",
            )
        ]
        from sqam_analyzer.models import Layer3Output
        bad_l3_output = Layer3Output(
            req_id="REQ-TEST-01",
            original_text=self.sample_req.text,
            refined_text="The system shall smoothly adjust the flight surface over 10Gbps Ethernet.",
            changes_made=["Added smoothly and 10Gbps Ethernet"],
            addressed_defect_ids=["DEF-001"],
            functional_intent_preservation_rationale="Adjusts surface.",
        )
        l4_output = validator.execute(self.sample_req, self.srs_context, retained, bad_l3_output)

        self.assertFalse(l4_output.is_valid)
        self.assertEqual(l4_output.verdict, ValidationVerdict.REJECTED)
        self.assertIn("smoothly", l4_output.new_ambiguities_detected)
        self.assertTrue(len(l4_output.unwarranted_assumptions_detected) > 0)

    # -----------------------------------------------------------------------
    # Layer 5 Tests: Comparison & Human Decision Flow
    # -----------------------------------------------------------------------
    def test_layer5_decision_lifecycle(self):
        pipeline = RequirementQualityPipeline(default_llm=self.mock_llm)
        result = pipeline.analyze_requirement(self.sample_req, self.srs_context)

        dossier = result.layer5_result
        self.assertIsNotNone(dossier)
        self.assertEqual(dossier.human_decision.status, HumanDecisionStatus.PENDING_REVIEW)

        # Test ACCEPT
        pipeline.layer5.record_decision(
            dossier=dossier,
            status=HumanDecisionStatus.ACCEPTED,
            comments="Approved by lead requirements engineer.",
        )
        self.assertEqual(dossier.human_decision.status, HumanDecisionStatus.ACCEPTED)
        self.assertEqual(dossier.human_decision.final_text, dossier.refined_text)

        # Test REJECT
        pipeline.layer5.record_decision(
            dossier=dossier,
            status=HumanDecisionStatus.REJECTED,
            comments="Rejecting edit to preserve original terminology.",
        )
        self.assertEqual(dossier.human_decision.status, HumanDecisionStatus.REJECTED)
        self.assertEqual(dossier.human_decision.final_text, self.sample_req.text)

        # Test EDITED_BY_HUMAN
        custom_req = "The system shall adjust the flight surface within 250ms of perturbation."
        pipeline.layer5.record_decision(
            dossier=dossier,
            status=HumanDecisionStatus.EDITED_BY_HUMAN,
            comments="Custom tightened latency.",
            custom_text=custom_req,
        )
        self.assertEqual(dossier.human_decision.status, HumanDecisionStatus.EDITED_BY_HUMAN)
        self.assertEqual(dossier.human_decision.final_text, custom_req)

        # Test Markdown report generation
        md_report = pipeline.layer5.render_markdown_report(
            dossier=dossier,
            layer1_output=result.layer1_result,
            layer2_output=result.layer2_result,
            layer4_output=result.layer4_result,
        )
        self.assertIn("# Requirements Quality Review: REQ-TEST-01", md_report)
        self.assertIn("Word-Level Diff:", md_report)
        self.assertIn("Quality Scorecard", md_report)

    # -----------------------------------------------------------------------
    # Diff Utilities Test
    # -----------------------------------------------------------------------
    def test_word_diff_computation(self):
        orig = "The system shall quickly process alerts."
        ref = "The system shall process alerts within 500ms."
        diff = compute_word_diff(orig, ref)

        self.assertIn("[-quickly-]", diff.diff_markup)
        self.assertIn("[+within 500ms+]", diff.diff_markup)
        self.assertGreater(diff.changed_words_count, 0)

    # -----------------------------------------------------------------------
    # End-to-End Batch Pipeline Test
    # -----------------------------------------------------------------------
    def test_batch_pipeline_execution(self):
        pipeline = RequirementQualityPipeline(default_llm=self.mock_llm)
        reqs = [
            self.sample_req,
            Requirement(
                req_id="REQ-TEST-02",
                req_type="Interface",
                section="Sensors",
                text="The sensor shall log readings and shall also transmit telemetry if applicable.",
            ),
        ]
        results = pipeline.analyze_batch(reqs, self.srs_context, auto_accept_validated=True)

        self.assertEqual(len(results), 2)
        for res in results:
            self.assertEqual(res.status, "completed")
            self.assertIsNotNone(res.layer1_result)
            self.assertIsNotNone(res.layer2_result)
            self.assertIsNotNone(res.layer3_result)
            self.assertIsNotNone(res.layer4_result)
            self.assertIsNotNone(res.layer5_result)
            self.assertGreaterEqual(res.execution_time_seconds, 0.0)

    # -----------------------------------------------------------------------
    # Edge Case: Minimal / Empty SRS Context
    # -----------------------------------------------------------------------
    def test_minimal_srs_context(self):
        minimal_context = SRSContext(domain_summary="Generic application service.")
        pipeline = RequirementQualityPipeline(default_llm=self.mock_llm)
        result = pipeline.analyze_requirement(self.sample_req, minimal_context)

        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.layer1_result)
        self.assertIsNotNone(result.layer5_result)

    # -----------------------------------------------------------------------
    # Fault Tolerance: LLM Failure & Graceful Degradation
    # -----------------------------------------------------------------------
    def test_llm_failure_graceful_handling(self):
        class BrokenLLM(MockLLMClient):
            def generate_text(self, *args, **kwargs):
                raise ConnectionError("Simulated LLM network timeout or rate limit")

        broken_pipeline = RequirementQualityPipeline(default_llm=BrokenLLM())
        result = broken_pipeline.analyze_requirement(self.sample_req, self.srs_context)

        self.assertEqual(result.status, "error")
        self.assertIn("Simulated LLM network timeout", result.error_message)
        self.assertGreaterEqual(result.execution_time_seconds, 0.0)

    # -----------------------------------------------------------------------
    # Custom Prompt Template Injections
    # -----------------------------------------------------------------------
    def test_custom_prompt_overrides(self):
        custom_system = "You are a Custom Safety Auditor for ISO 26262."
        custom_layer1 = Layer1DocumentScorer(
            llm_client=self.mock_llm,
            system_prompt=custom_system,
        )
        self.assertEqual(custom_layer1.system_prompt, custom_system)

    # -----------------------------------------------------------------------
    # Pydantic JSON Serialization & Deserialization
    # -----------------------------------------------------------------------
    def test_json_serialization(self):
        pipeline = RequirementQualityPipeline(default_llm=self.mock_llm)
        result = pipeline.analyze_requirement(self.sample_req, self.srs_context)

        json_str = result.model_dump_json(indent=2)
        self.assertIsInstance(json_str, str)
        self.assertIn('"req_id": "REQ-TEST-01"', json_str)
        self.assertIn('"overall_quality_score"', json_str)


if __name__ == "__main__":
    unittest.main()

