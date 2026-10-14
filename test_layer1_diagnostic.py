"""
test_layer1_diagnostic.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Deep Diagnostic Test Harness for Layer 1 of Pipeline 1:
Document Understanding, 7-Attribute ISO 29148 Scoring & Shortcoming Identification.

Executes Layer 1 across diverse requirements (clean, ambiguous, compound, and non-conforming)
and generates an intuitive Markdown diagnostic dossier (`layer1_analysis_dossier.md`).
"""

import os
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqam_analyzer import (
    Layer1DocumentScorer,
    Requirement,
    SRSContext,
    resolve_llm_client,
)

console = Console()


def build_test_suite():
    """Builds a curated test suite representing different requirement quality states."""
    
    # 1. Aviation / Gesture Recognition (Real SRS from 1_FROG)
    ctx_frog = SRSContext(
        document_title="FROG Gesture Recognizer SRS v1.1",
        domain_summary="Continuous hand gesture modeling and real-time vision recognition system for human-computer interaction.",
        glossary={
            "Gesture": "A spatial-temporal trajectory of the hand representing a discrete symbolic command.",
            "FROG": "Framework for Recognized Online Gestures.",
        },
        surrounding_requirements=[
            "REQ-FROG-001: The system shall capture video input at a minimum rate of 30 frames per second.",
            "REQ-FROG-002: Recognition latency shall not exceed 100 milliseconds from gesture termination."
        ]
    )
    req_frog = Requirement(
        req_id="FROG-REQ-003",
        text="Gestures are the entities which shall be modeled as well as recognized by the FROG project.",
        req_type="Functional",
        section="3.2 Gesture Definitions",
    )

    # 2. Autonomous Driving Safety (Real SRS from 2_SMIRK)
    ctx_smirk = SRSContext(
        document_title="SMIRK Autonomous Safety Monitor v0.2",
        domain_summary="Machine learning safety supervisor for low-speed autonomous shuttle braking. Governed by AMLAS framework.",
        glossary={
            "Operational Design Domain (ODD)": "Environmental boundaries defined as daylight illumination (>500 lux), dry asphalt, and vehicle speed <= 25 km/h.",
            "Pedestrian Hazard": "A static or dynamic human figure intersecting the vehicle stopping trajectory within 2.5 seconds."
        },
        surrounding_requirements=[
            "REQ-SMIRK-01: The ML component shall maintain safety verification within the stated ODD boundaries.",
        ]
    )
    req_smirk = Requirement(
        req_id="SMIRK-REQ-002",
        text="The SMIRK system shall detect pedestrian hazards under AMLAS Operational Design Domain boundaries.",
        req_type="Safety / Functional",
        section="Section 7 - ML Safety Allocations",
    )

    # 3. Flawed Mission-Critical Requirement (Multiple ISO 29148 Violations)
    ctx_avionics = SRSContext(
        document_title="Flight Surface Actuator Control SRS v3.4",
        domain_summary="Primary flight computer surface actuation for fly-by-wire aircraft under DO-178C Level A.",
        glossary={
            "PFC": "Primary Flight Computer with triple-modular redundancy.",
            "Turbulence": "Atmospheric vertical gust velocity exceeding 15 ft/sec."
        }
    )
    req_flawed = Requirement(
        req_id="PFC-ACT-101",
        text="The PFC should quickly adjust elevator actuators during turbulence and also transmit telemetry if applicable.",
        req_type="Functional / Performance",
        section="Section 3.2 - Flight Surface Actuation",
    )

    # 4. Gold-Standard Fully Compliant Requirement (Negative Control: Should Pass Cleanly)
    ctx_hvac = SRSContext(
        document_title="Environmental Control System SRS v1.0",
        domain_summary="Automated cabin thermal and pressure regulation for commercial transport aircraft.",
        glossary={
            "Secondary Cooling": "Auxiliary vapor-cycle cooling loop rated at 5 kW thermal dissipation."
        }
    )
    req_compliant = Requirement(
        req_id="ECS-THM-042",
        text="When cabin ambient temperature exceeds 28 degrees Celsius, the ECS shall activate secondary cooling within 1.5 seconds.",
        req_type="Performance / Reactive",
        section="Section 4.1 - Temperature Regulation",
    )

    return [
        ("Real SRS: Frog Non-Singularity Test", req_frog, ctx_frog),
        ("Real SRS: SMIRK Contextual Specification", req_smirk, ctx_smirk),
        ("Synthetic: Highly Flawed Multi-Defect Requirement", req_flawed, ctx_avionics),
        ("Gold Standard: Fully Compliant Negative Control", req_compliant, ctx_hvac),
    ]


def run_diagnostic():
    provider = os.getenv("SQAM_PROVIDER", "mock")
    llm_client = resolve_llm_client(provider=provider, allow_mock=True)
    layer1 = Layer1DocumentScorer(llm_client=llm_client)

    test_cases = build_test_suite()

    console.print(Panel(
        f"[bold white]Layer 1 Diagnostic Test Runner[/bold white]\n"
        f"[dim]Provider: {type(llm_client).__name__} | Test Cases: {len(test_cases)}[/dim]",
        border_style="cyan"
    ))

    markdown_records = [
        "# Layer 1 Diagnostic Evaluation Dossier",
        f"**Execution Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**LLM Backend Client:** `{type(llm_client).__name__}`  ",
        f"**Evaluation Standard:** ISO/IEC/IEEE 29148:2018 (7 Quality Dimensions)  \n",
        "---",
    ]

    for title, req, ctx in test_cases:
        console.print(f"\n[bold yellow]>>> Running Test: {title} ({req.req_id})[/bold yellow]")
        start = time.perf_counter()
        
        output = layer1.execute(requirement=req, srs_context=ctx)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Console Rendering
        console.print(f"Overall Quality Score: [bold green]{output.overall_quality_score:.1f} / 10.0[/bold green] (Latency: {elapsed_ms:.1f}ms)")
        console.print(f"[dim]Summary: {output.document_understanding_summary}[/dim]")

        # Scorecard Table
        score_table = Table(title=f"ISO 29148 Scorecard: {req.req_id}", show_header=True)
        score_table.add_column("Attribute", width=22)
        score_table.add_column("Score", justify="center", width=10)
        score_table.add_column("Rationale", width=45)

        for s in output.attribute_scores:
            color = "green" if s.score >= 8.5 else ("yellow" if s.score >= 6.0 else "red")
            score_table.add_row(s.attribute.value, f"[{color}]{s.score:.1f}[/{color}]", s.rationale)
        console.print(score_table)

        # Shortcomings Table
        if output.shortcomings:
            defect_table = Table(title=f"Flagged Candidate Shortcomings ({len(output.shortcomings)})", show_header=True)
            defect_table.add_column("Defect ID", width=10)
            defect_table.add_column("Attribute", width=16)
            defect_table.add_column("Severity", justify="center", width=10)
            defect_table.add_column("Problematic Excerpt", width=20)
            defect_table.add_column("Explanation", width=40)

            for d in output.shortcomings:
                sev_color = "red" if d.severity.value in ["high", "critical"] else "yellow"
                defect_table.add_row(
                    d.defect_id,
                    d.attribute.value,
                    f"[{sev_color}]{d.severity.value.upper()}[/{sev_color}]",
                    f"'{d.problematic_excerpt}'",
                    d.explanation
                )
            console.print(defect_table)
        else:
            console.print("[bold green]Zero shortcomings flagged! Requirement is fully compliant.[/bold green]")

        # Markdown Record Generation
        md_entry = [
            f"## Case: {title}",
            f"- **Requirement ID:** `{req.req_id}`",
            f"- **Section:** {req.section}",
            f"- **Input Text:** *\"{req.text}\"*",
            f"- **Overall Quality Score:** **{output.overall_quality_score:.1f} / 10.0**",
            f"- **Document Understanding Summary:** {output.document_understanding_summary}\n",
            "### ISO/IEC/IEEE 29148 Quality Scorecard",
            "| Quality Dimension | Score (0-10) | Evaluation Rationale |",
            "| :--- | :---: | :--- |",
        ]
        for s in output.attribute_scores:
            md_entry.append(f"| **{s.attribute.value}** | {s.score:.1f} | {s.rationale} |")

        md_entry.append("\n### Candidate Shortcomings Identified (Forwarded to Layer 2)")
        if output.shortcomings:
            md_entry.append("| Defect ID | Violated Attribute | Severity | Problematic Excerpt | Failure Explanation |")
            md_entry.append("| :---: | :--- | :---: | :--- | :--- |")
            for d in output.shortcomings:
                md_entry.append(f"| `{d.defect_id}` | {d.attribute.value} | `{d.severity.value.upper()}` | \"{d.problematic_excerpt}\" | {d.explanation} |")
        else:
            md_entry.append("*No shortcomings identified. Requirement satisfies all 7 quality dimensions.*")

        md_entry.append("\n---\n")
        markdown_records.append("\n".join(md_entry))

    # Write output dossier
    output_path = PROJECT_ROOT / "layer1_analysis_dossier.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_records))

    console.print(f"\n[bold green]Intuitive Layer 1 Diagnostic Dossier generated successfully at:[/bold green] [cyan]{output_path}[/cyan]\n")


if __name__ == "__main__":
    run_diagnostic()
