"""
main.py
~~~~~~~
Main entry point for running the LLM-Based Software Requirement Quality Analyzer.
Provides CLI flags for interactive human review, automated evaluation, and provider selection.

Usage:
  python main.py --demo
  python main.py --interactive
  python main.py --provider openai --model gpt-4o --interactive
  python main.py --provider gemini --model gemini-2.5-flash
"""

import argparse
import json
import os
import sys
from rich.console import Console

from sqam_analyzer import (
    GeminiLLMClient,
    MockLLMClient,
    OpenAILLMClient,
    Requirement,
    RequirementQualityPipeline,
    SRSContext,
)
from sqam_analyzer.cli import display_comparison_dossier, run_interactive_review

console = Console()


def get_default_srs_dataset():
    """Provides a realistic sample dataset for evaluation and testing."""
    srs_context = SRSContext(
        document_title="NextGen Avionics Control System SRS v3.4",
        domain_summary=(
            "Flight management and fly-by-wire surface actuation system. "
            "Governed by DO-178C Level A and ISO/IEC/IEEE 29148. "
            "High reliability, hard real-time latency limits, deterministic state transitions."
        ),
        glossary={
            "Fly-by-Wire (FBW)": "Electronic interface replacing mechanical flight controls.",
            "Attitude Perturbation": "Angular velocity disturbance exceeding 3.5 deg/sec on pitch, roll, or yaw.",
            "Primary Flight Computer (PFC)": "Triple-redundant central computing unit for flight surfaces.",
            "Degraded Mode": "Autonomous fallback state when two or more attitude sensors disagree.",
        },
        surrounding_requirements=[
            "REQ-FBW-001: The PFC shall sample attitude rate gyro sensors at a continuous rate of 200 Hz.",
            "REQ-FBW-002: In Degraded Mode, the system shall disable autonomous trim optimization.",
            "REQ-FBW-003: All flight control state transitions shall be stored in crash-survivable memory within 10ms.",
        ],
        applicable_standards=["ISO/IEC/IEEE 29148:2018", "DO-178C Level A", "FAA AC 20-115D"],
    )

    requirements = [
        Requirement(
            req_id="REQ-PFC-101",
            req_type="Functional / Performance",
            section="Section 3.2 - Flight Surface Actuation",
            text="The Primary Flight Computer shall quickly adjust elevator actuators during turbulence.",
        ),
        Requirement(
            req_id="REQ-PFC-102",
            req_type="Functional",
            section="Section 3.3 - Sensor Synchronization",
            text="The system shall synchronize triple-modular sensors and shall also broadcast status telemetry to the black box if applicable.",
        ),
        Requirement(
            req_id="REQ-PFC-103",
            req_type="Functional",
            section="Section 3.4 - Anomaly Response",
            text="When an Attitude Perturbation occurs, the PFC shall command stabilizer corrections within 50 milliseconds.",
        ),
    ]

    return srs_context, requirements


def build_llm_client(provider: str, model: str):
    """Instantiates the chosen LLM provider."""
    provider = provider.lower()
    if provider == "mock":
        console.print("[dim]Using deterministic MockLLMClient (offline mode)...[/dim]")
        return MockLLMClient()
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[bold yellow]Warning: OPENAI_API_KEY not set in environment. Falling back or using client default.[/bold yellow]")
        return OpenAILLMClient(model_name=model)
    elif provider == "gemini":
        return GeminiLLMClient(model_name=model)
    else:
        raise ValueError(f"Unknown provider '{provider}'. Choose 'mock', 'openai', or 'gemini'.")


def main():
    parser = argparse.ArgumentParser(
        description="LLM-Based Software Requirement Quality Analyzer (5-Layer Pipeline)"
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai", "gemini"],
        default="mock",
        help="LLM provider backend (default: mock)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model name (e.g. gpt-4o, gpt-4o-mini, gemini-2.5-flash)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive human-in-the-loop review session in the terminal",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run standard automated showcase demonstration",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=None,
        help="File path to save Markdown audit report (e.g. report.md)",
    )

    args = parser.parse_args()

    # Default to demo if no specific mode selected
    interactive_mode = args.interactive
    llm_client = build_llm_client(args.provider, args.model)
    pipeline = RequirementQualityPipeline(default_llm=llm_client)

    srs_context, requirements = get_default_srs_dataset()

    console.print(f"[bold green]Starting analysis for {len(requirements)} requirements...[/bold green]")
    results = pipeline.analyze_batch(requirements, srs_context)

    if interactive_mode:
        results = run_interactive_review(results, pipeline)
    else:
        for res in results:
            display_comparison_dossier(res)

    # Save Markdown report if requested
    if args.output_report:
        report_sections = [
            f"# SRS Quality Analysis Report: {srs_context.document_title}\n"
        ]
        for res in results:
            sec = pipeline.layer5.render_markdown_report(
                dossier=res.layer5_result,
                layer1_output=res.layer1_result,
                layer2_output=res.layer2_result,
                layer4_output=res.layer4_result,
            )
            report_sections.append(sec)

        full_report = "\n\n---\n\n".join(report_sections)
        with open(args.output_report, "w", encoding="utf-8") as f:
            f.write(full_report)
        console.print(f"\n[bold green]Audit report successfully saved to {args.output_report}[/bold green]")


if __name__ == "__main__":
    main()
