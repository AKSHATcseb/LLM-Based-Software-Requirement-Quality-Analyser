"""
evaluate_srs.py
~~~~~~~~~~~~~~~
Evaluation Script for the 15 Versioned SRS Projects.
Computes the 5 project research metrics (UAR, RRR, FSR, IPR, APL) and
performs the 3-way historical classification (Matched / Partially Matched / Not Matched).

Usage:
  python evaluate_srs.py --benchmark sample_benchmark.json --output evaluation_report.md
  python evaluate_srs.py --provider gemini --model gemini-2.5-flash
  python evaluate_srs.py --provider openai --model gpt-4o
"""

import argparse
import json
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sqam_analyzer import (
    GeminiLLMClient,
    MockLLMClient,
    OpenAILLMClient,
    RequirementQualityPipeline,
    SRSContext,
)
from sqam_analyzer.evaluator import (
    HistoricalCorrespondence,
    SRSEvaluator,
    VersionedRequirementPair,
)

console = Console()


def load_benchmark(file_path: str):
    """Loads versioned requirement pairs from a JSON benchmark file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [VersionedRequirementPair(**item) for item in data]


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate 5-Layer SQAM Pipeline against Versioned SRS Documents"
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="sample_benchmark.json",
        help="Path to JSON benchmark containing Version N & Version N+1 pairs",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai", "gemini"],
        default="mock",
        help="LLM provider (default: mock)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model name (e.g. gpt-4o, gemini-2.5-flash)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_report.md",
        help="Output Markdown report file",
    )

    args = parser.parse_args()

    # Load pairs
    console.print(f"\n[bold cyan]Loading benchmark dataset from {args.benchmark}...[/bold cyan]")
    pairs = load_benchmark(args.benchmark)
    console.print(f"Loaded {len(pairs)} versioned requirement pairs.")

    # Shared domain context for benchmark
    srs_context = SRSContext(
        document_title="Cross-Project System Requirements Specification Evaluation Benchmark",
        domain_summary=(
            "Cross-domain specifications covering transportation, avionics, robotics, and safety-critical control systems. "
            "Governed by ISO/IEC/IEEE 29148 standards."
        ),
        glossary={
            "Vital Anomaly": "Critical state disturbance defined in project safety manual.",
            "UIC 612": "Driver-machine interface standard for railway applications.",
        },
        surrounding_requirements=[
            "REQ-SMIRK-03: The system shall transmit status telemetry to ground control at 1 Hz.",
            "REQ-SAFE-01: System fail-safe state shall engage within 200 milliseconds of anomaly.",
        ],
        applicable_standards=["ISO/IEC/IEEE 29148:2018", "IEC 61508"],
    )

    # Instantiate LLM Client
    if args.provider == "mock":
        llm_client = MockLLMClient()
    elif args.provider == "openai":
        llm_client = OpenAILLMClient(model_name=args.model)
    elif args.provider == "gemini":
        llm_client = GeminiLLMClient(model_name=args.model)
    else:
        raise ValueError(f"Unknown provider: {args.provider}")

    pipeline = RequirementQualityPipeline(default_llm=llm_client)
    evaluator = SRSEvaluator(pipeline=pipeline)

    console.print(f"[bold green]Running blind pipeline evaluation across {len(pairs)} requirements...[/bold green]\n")
    eval_result = evaluator.evaluate_dataset(pairs, srs_context)

    metrics = eval_result["metrics"]

    # Render Summary Table
    table = Table(title="[bold yellow]SQAM Research Metrics Summary[/bold yellow]", show_header=True)
    table.add_column("Metric", style="cyan", width=12)
    table.add_column("Full Name", width=34)
    table.add_column("Formula / Meaning", width=42)
    table.add_column("Observed Value", justify="right", style="bold green", width=16)

    table.add_row(
        "UAR",
        "User Acceptance Rate",
        "Accepted Refinements / Total Presented",
        f"{metrics.uar:.1f}%",
    )
    table.add_row(
        "RRR",
        "Refinement Rejection Rate",
        "Layer 4 Rejected / Layer 3 Proposed",
        f"{metrics.rrr:.1f}%",
    )
    table.add_row(
        "FSR",
        "Flawed Suggestion Rate",
        "False/Unnecessary Suggestions / Total",
        f"{metrics.fsr:.1f}%",
    )
    table.add_row(
        "IPR",
        "Intent Preservation Rate",
        "Intent-Preserving Refinements / Total",
        f"{metrics.ipr:.1f}%",
    )
    table.add_row(
        "APL",
        "Average Pipeline Latency",
        "Total Pipeline Time / Total Requirements",
        f"{metrics.apl:.3f} s/req",
    )
    table.add_row(
        "L2 Discard",
        "Layer 2 False-Positive Filter",
        "Candidate Defects Discarded / Total Flagged",
        f"{metrics.layer2_discard_rate:.1f}%",
    )

    console.print(table)

    # Render Historical Correspondence Breakdown
    corr_table = Table(title="[bold yellow]Historical Version Correspondence (vs Version N+1)[/bold yellow]", show_header=True)
    corr_table.add_column("Correspondence Class", width=22)
    corr_table.add_column("Count", justify="right", width=10)
    corr_table.add_column("Description")

    corr_table.add_row("[green]Matched[/green]", str(metrics.historical_matches), "Pipeline refinement anticipated actual human historical revision")
    corr_table.add_row("[yellow]Partially Matched[/yellow]", str(metrics.historical_partial_matches), "Targeted the correct defect area with an alternative formulation")
    corr_table.add_row("[red]Not Matched[/red]", str(metrics.historical_not_matches), "No corresponding change in historical Version N+1")

    console.print(corr_table)

    # Render Markdown Report
    md_content = evaluator.render_summary_markdown(eval_result, project_name="15 Versioned SRS Benchmark")
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md_content)
    console.print(f"\n[bold green]Complete evaluation report exported to {args.output}![/bold green]\n")


if __name__ == "__main__":
    main()
