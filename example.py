"""
example.py
~~~~~~~~~~
End-to-End demonstration of the LLM-Based Software Requirement Quality Analyzer.
Demonstrates:
1. Setting up SRS document context (domain summary, glossary, companion requirements).
2. Running requirements through all 5 layers:
   - Layer 1: Evaluation against 7 ISO/IEC/IEEE 29148 quality attributes.
   - Layer 2: Defect reasoning & false-positive elimination using document context.
   - Layer 3: Targeted refinement maintaining functional intent.
   - Layer 4: Independent auditor verification.
   - Layer 5: Visual diffing, Markdown report generation, and human decision recording.
3. Swapping LLM clients (MockLLMClient, OpenAILLMClient, GeminiLLMClient, LangChainLLMClient).
"""

import os
from sqam_analyzer import (
    HumanDecisionStatus,
    MockLLMClient,
    OpenAILLMClient,
    GeminiLLMClient,
    Requirement,
    RequirementQualityPipeline,
    SRSContext,
)
from sqam_analyzer.cli import display_comparison_dossier


def run_demo():
    print("=" * 80)
    print("   AI-ASSISTED SOFTWARE REQUIREMENT QUALITY ANALYZER (5-LAYER PIPELINE)")
    print("=" * 80)

    # -----------------------------------------------------------------------
    # 1. Define SRS Document Context
    # -----------------------------------------------------------------------
    srs_context = SRSContext(
        document_title="MedPulse EHR - Clinical Decision Support System SRS v2.1",
        domain_summary=(
            "MedPulse is a mission-critical Electronic Health Record (EHR) system used in acute care "
            "hospitals. It manages patient vitals, biometric telemetry, clinical alerts, and physician order entry. "
            "High reliability, strict latency under 1 second, and HIPAA compliance are mandatory."
        ),
        glossary={
            "CDSS": "Clinical Decision Support System rule engine.",
            "Vital Anomaly": "Systolic BP > 180 mmHg or Heart Rate < 40 / > 130 bpm.",
            "Attending Physician": "Licensed clinician currently assigned as primary care provider in ward.",
            "HL7 FHIR": "Fast Healthcare Interoperability Resources standard for health data exchange.",
        },
        surrounding_requirements=[
            "REQ-NOTIF-01: All emergency notifications shall be delivered to the nurse station console via WebSocket within 500ms.",
            "REQ-AUDIT-03: The system shall record all biometric telemetry access events in the HIPAA audit log.",
            "REQ-FAIL-02: If network connectivity is lost, the local bedside monitor shall cache up to 72 hours of telemetry data.",
        ],
        applicable_standards=["ISO/IEC/IEEE 29148:2018", "HL7 FHIR Release 4", "FDA Software as Medical Device (SaMD)"],
    )

    # -----------------------------------------------------------------------
    # 2. Define Sample Requirements Exhibiting Real-World Quality Challenges
    # -----------------------------------------------------------------------
    requirements = [
        # Case A: Vague latency and subjective descriptors (Unambiguity defect)
        Requirement(
            req_id="REQ-ALERT-101",
            req_type="Functional / Performance",
            section="Section 4.2 - Anomaly Alerting",
            text="The system shall quickly process vital anomaly alerts and display them to the attending physician in an intuitive format.",
        ),
        # Case B: Multi-action bundling & open-ended branch (Singularity & Completeness defect)
        Requirement(
            req_id="REQ-DATA-204",
            req_type="Functional",
            section="Section 5.1 - Telemetry Ingestion",
            text="The system shall ingest bedside monitor telemetry data and shall also synchronize with external HL7 FHIR servers if applicable.",
        ),
        # Case C: Term that might seem ambiguous in isolation, but is explicitly defined in glossary
        # Layer 2 should recognize that 'Vital Anomaly' is contextually defined and discard false positives!
        Requirement(
            req_id="REQ-MON-305",
            req_type="Functional",
            section="Section 4.1 - Telemetry Monitoring",
            text="When a Vital Anomaly is detected, the CDSS engine shall flag the patient record for clinical review within 2 seconds.",
        ),
    ]

    # -----------------------------------------------------------------------
    # 3. Initialize Pipeline with Swappable LLM Providers
    # -----------------------------------------------------------------------
    # In production, you can easily use:
    # llm_client = OpenAILLMClient(model_name="gpt-4o")
    # or
    # llm_client = GeminiLLMClient(model_name="gemini-2.5-flash")
    #
    # Here, we use the deterministic MockLLMClient for zero-dependency local execution:
    llm_client = MockLLMClient()

    pipeline = RequirementQualityPipeline(
        default_llm=llm_client,
    )

    print(f"\nAnalyzing {len(requirements)} requirements through the 5-layer pipeline...\n")

    # -----------------------------------------------------------------------
    # 4. Execute Analysis & Human-in-the-Loop Review
    # -----------------------------------------------------------------------
    for req in requirements:
        result = pipeline.analyze_requirement(
            requirement=req,
            srs_context=srs_context,
            temperature=0.0,
            auto_accept_validated=False,  # Keeps status PENDING_REVIEW for human sign-off
        )

        # Display rich terminal presentation
        display_comparison_dossier(result)

        # Simulate Human-in-the-loop review decision
        dossier = result.layer5_result
        if dossier:
            if result.layer4_result and result.layer4_result.is_valid:
                # Human accepts the refinement
                pipeline.layer5.record_decision(
                    dossier=dossier,
                    status=HumanDecisionStatus.ACCEPTED,
                    comments="Refinement approved: verified against 500ms hospital latency baseline.",
                )
                print(f"[Human Reviewer Sign-off]: ACCEPTED refinement for {req.req_id}")
            else:
                pipeline.layer5.record_decision(
                    dossier=dossier,
                    status=HumanDecisionStatus.REJECTED,
                    comments="Retained original requirement.",
                )
                print(f"[Human Reviewer Sign-off]: REJECTED refinement for {req.req_id}")

        # Render complete markdown audit report
        md_report = pipeline.layer5.render_markdown_report(
            dossier=result.layer5_result,
            layer1_output=result.layer1_result,
            layer2_output=result.layer2_result,
            layer4_output=result.layer4_result,
        )
        print("\n--- Generated Markdown Review Report Snippet ---")
        print("\n".join(md_report.splitlines()[:25]))
        print("...\n")

    print("\n" + "=" * 80)
    print("Demo completed successfully. All 5 layers executed and verified!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
