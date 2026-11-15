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
    load_srs_any,
    resolve_llm_client,
)
from sqam_analyzer.cli import display_comparison_dossier, run_interactive_review

console = Console()

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


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


def build_llm_client(provider: str | None, model: str | None):
    """Instantiates the chosen LLM provider, enforcing live LLM setup."""
    return resolve_llm_client(
        provider=provider,
        model=model,
        allow_mock=(provider == "mock"),
    )


def main():
    parser = argparse.ArgumentParser(
        description="LLM-Based Software Requirement Quality Analyzer (5-Layer Pipeline)"
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai", "mock"],
        default=None,
        help="LLM provider backend (default: auto-detects configured GEMINI_API_KEY or OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (defaults to gemini-3.5-flash or gpt-4o)",
    )
    parser.add_argument(
        "srs_file_pos",
        nargs="?",
        default=None,
        help="Optional positional path to custom SRS file (.pdf, .md, or .json)",
    )
    parser.add_argument(
        "output_report_pos",
        nargs="?",
        default=None,
        help="Optional positional path to save audit report (.json or .md)",
    )
    parser.add_argument(
        "--srs-file",
        "-f",
        type=str,
        default=None,
        help="Path to custom SRS file (.pdf, .md, or .json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of requirements to analyze from the dataset",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all requirements extracted from the document (disables the default 5-requirement limit)",
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
        help="File path to save Markdown or JSON audit report (e.g. report.md, report.json)",
    )

    args = parser.parse_args()

    # Resolve arguments (positional takes fallback priority)
    target_srs_file = args.srs_file or args.srs_file_pos
    target_output_report = args.output_report or args.output_report_pos
    interactive_mode = args.interactive

    try:
        llm_client = build_llm_client(args.provider, args.model)
    except ValueError as e:
        console.print(f"[bold red]{e}[/bold red]")
        sys.exit(1)

    pipeline = RequirementQualityPipeline(default_llm=llm_client)

    if target_srs_file:
        try:
            console.print(f"[bold cyan]Loading custom SRS from: {target_srs_file}[/bold cyan]")
            srs_context, requirements = load_srs_any(target_srs_file)
        except Exception as e:
            console.print(f"[bold red]Failed to load SRS file: {e}[/bold red]")
            sys.exit(1)
    else:
        console.print("[dim]No SRS file provided. Using built-in Avionics sample SRS. (Pass <file.pdf/.json> to test your own SRS)[/dim]")
        srs_context, requirements = get_default_srs_dataset()

    # Limit requirements
    if args.all or (args.limit and args.limit <= 0):
        console.print(f"[bold yellow]Full Document Mode: Analyzing all {len(requirements)} requirements (--all).[/bold yellow]")
    elif args.limit and args.limit > 0:
        requirements = requirements[: args.limit]
        console.print(f"[dim]Limiting analysis to first {len(requirements)} requirements (--limit {args.limit})[/dim]")
    elif len(requirements) > 10 and not args.limit:
        # Prevent runaway token usage on large real documents unless requested
        default_limit = 5
        console.print(f"[dim]Notice: Document has {len(requirements)} requirements. Defaulting to first {default_limit} requirements (pass --all or --limit <N> to adjust).[/dim]")
        requirements = requirements[:default_limit]

    console.print(f"[bold green]Document: {srs_context.document_title}[/bold green]")
    console.print(f"[bold green]Starting analysis for {len(requirements)} requirement(s)...[/bold green]")
    results = pipeline.analyze_batch(requirements, srs_context)

    if interactive_mode:
        results = run_interactive_review(results, pipeline)
    else:
        for res in results:
            display_comparison_dossier(res)

    # Save report if requested
    if target_output_report:
        if target_output_report.lower().endswith(".json"):
            dump_data = [
                res.model_dump() if hasattr(res, "model_dump") else res.dict()
                for res in results
            ]
            with open(target_output_report, "w", encoding="utf-8") as f:
                json.dump(dump_data, f, indent=2, default=str)
            console.print(f"\n[bold green]JSON audit report successfully saved to {target_output_report}[/bold green]")
        else:
            report_sections = [
                f"# SRS Quality Analysis Report: {srs_context.document_title}\n"
            ]
            for res in results:
                if res.layer5_result:
                    sec = pipeline.layer5.render_markdown_report(
                        dossier=res.layer5_result,
                        layer1_output=res.layer1_result,
                        layer2_output=res.layer2_result,
                        layer4_output=res.layer4_result,
                    )
                else:
                    sec = (
                        f"# Requirements Quality Review: {res.requirement.req_id}\n\n"
                        f"**Original Requirement:**\n> {res.requirement.text}\n\n"
                        f"⚠️ **Analysis Status:** {res.status.upper()}\n\n"
                        f"**Reason / Error:** `{res.error_message}`\n"
                    )
                report_sections.append(sec)

            full_report = "\n\n---\n\n".join(report_sections)
            with open(target_output_report, "w", encoding="utf-8") as f:
                f.write(full_report)
            console.print(f"\n[bold green]Audit report successfully saved to {target_output_report}[/bold green]")


if __name__ == "__main__":
    main()
