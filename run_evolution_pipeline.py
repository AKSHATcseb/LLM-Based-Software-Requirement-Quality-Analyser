"""
run_evolution_pipeline.py
~~~~~~~~~~~~~~~~~~~~~~~~~
CLI Runner for Pipeline 2: Historical SRS Version Comparison & Change Extraction.

Usage:
  python run_evolution_pipeline.py --project 1_FROG --limit 5
  python run_evolution_pipeline.py --project 2_SMIRK --limit 5
  python run_evolution_pipeline.py --v1 "srs doc versions/1_FROG/SRS_v1.1.pdf" --v2 "srs doc versions/1_FROG/Software_Requirements_Specification_v30.pdf" --limit 5
  python run_evolution_pipeline.py --project 1_FROG --provider gemini --model gemini-2.5-flash
  python run_evolution_pipeline.py --project 1_FROG --output-markdown frog_evolution_report.md --output-csv frog_evolution.csv
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sqam_analyzer.llm_provider import GeminiLLMClient, MockLLMClient, OpenAILLMClient
from sqam_analyzer.models import SRSContext
from srs_evolution import (
    AlignmentType,
    ChangeCategory,
    CorrespondenceRating,
    HistoricalEvolutionPipeline,
)

console = Console()
SRS_BASE_DIR = Path("srs doc versions")


def get_version_files_for_project(project_name: str) -> tuple[Path, Path]:
    """Finds the earlier (v1) and later (v2) chronological files for a project."""
    project_dir = SRS_BASE_DIR / project_name
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory '{project_dir}' not found.")

    files = [f for f in sorted(project_dir.iterdir()) if f.is_file() and f.suffix.lower() in [".pdf", ".md", ".txt"]]
    if len(files) < 2:
        raise ValueError(f"Project '{project_name}' must have at least 2 version files, found {len(files)}.")

    # Sort files chronologically by naming conventions
    # E.g. v1.1 before v30, (1).md before (2).md, 1.pdf before 2.pdf
    def version_sort_key(f: Path):
        name = f.name.lower()
        if "v1" in name or "(1)" in name or "1.pdf" in name or "0.2" in name or "010101" in name:
            return 1
        if "v2" in name or "(2)" in name or "2.pdf" in name or "0.9" in name or "020201" in name:
            return 2
        if "v3" in name or "(3)" in name or "3.pdf" in name or "30" in name or "030101" in name:
            return 3
        return 4

    sorted_files = sorted(files, key=version_sort_key)
    return sorted_files[0], sorted_files[-1]


def display_alignment_summary(aligned_pairs: list):
    """Renders a Rich table of the aligned requirements across versions."""
    table = Table(title="[bold cyan]Step 1 & 2: Cross-Version Requirement Alignment[/bold cyan]", show_header=True)
    table.add_column("Type", width=14)
    table.add_column("Version N (Earlier)", width=32)
    table.add_column("Version N+1 (Later)", width=32)
    table.add_column("Confidence", justify="right", width=12)

    for p in aligned_pairs[:8]:
        if p.alignment_type == AlignmentType.IDENTICAL_ID:
            type_str = "[green]IDENTICAL ID[/green]"
        elif p.alignment_type == AlignmentType.SEMANTIC_MATCH:
            type_str = "[yellow]SEMANTIC[/yellow]"
        elif p.alignment_type == AlignmentType.ADDED:
            type_str = "[blue]ADDED[/blue]"
        else:
            type_str = "[red]DELETED[/red]"

        v1_preview = (f"[{p.req_id_v1}] " + (p.text_v1 or ""))[:35] + "..." if p.text_v1 else "[dim]None (Added)[/dim]"
        v2_preview = (f"[{p.req_id_v2}] " + (p.text_v2 or ""))[:35] + "..." if p.text_v2 else "[dim]None (Deleted)[/dim]"

        table.add_row(type_str, v1_preview, v2_preview, f"{p.alignment_confidence:.2f}")

    if len(aligned_pairs) > 8:
        table.add_row("...", f"[dim]+{len(aligned_pairs) - 8} more pairs[/dim]", "...", "...")

    console.print(table)


def display_change_classification_summary(change_records: list, summary):
    """Renders a Rich table of the empirical change categories."""
    table = Table(title="[bold yellow]Step 3: Empirical Change Taxonomy Classification[/bold yellow]", show_header=True)
    table.add_column("Category", width=26)
    table.add_column("Count", justify="right", width=8)
    table.add_column("Classification Nature", style="dim")

    category_counts = {}
    for c in change_records:
        category_counts[c.change_category] = category_counts.get(c.change_category, 0) + 1

    for cat in ChangeCategory:
        count = category_counts.get(cat, 0)
        if count > 0:
            if cat.value in ["AMBIGUITY_REDUCTION", "COMPLETENESS_IMPROVEMENT", "CONSTRAINT_REFINEMENT", "CONSISTENCY_CORRECTION"]:
                style = "bold green"
                desc = "ISO 29148 Quality Refinement (Ground truth for benchmark)"
            elif cat.value == "FUNCTIONAL_SCOPE_CHANGE":
                style = "bold magenta"
                desc = "Stakeholder Business / Scope Shift"
            elif cat.value in ["REQUIREMENT_ADDED", "REQUIREMENT_DELETED"]:
                style = "blue"
                desc = "Requirement Lifecycle Change"
            else:
                style = "dim"
                desc = "Baseline / Unchanged / Formatting"

            table.add_row(f"[{style}]{cat.value}[/{style}]", str(count), desc)

    console.print(table)


def display_correspondence_benchmark_summary(benchmark_results: list, summary):
    """Renders the semantic correspondence benchmark results."""
    table = Table(title="[bold green]Step 4 & 5: Pipeline-1 vs Version N+1 Semantic Correspondence[/bold green]", show_header=True)
    table.add_column("Rating", width=18)
    table.add_column("Count", justify="right", width=8)
    table.add_column("Academic Evaluation Meaning", style="dim")

    table.add_row(
        "[bold green]MATCHED[/bold green]",
        str(summary.matched_count),
        "Pipeline-1 independently surfaced and resolved what stakeholders actually fixed in vN+1.",
    )
    table.add_row(
        "[bold yellow]PARTIALLY_MATCHED[/bold yellow]",
        str(summary.partially_matched_count),
        "Pipeline-1 correctly targeted the flawed area, but applied an alternative fix strategy.",
    )
    table.add_row(
        "[bold red]NOT_MATCHED[/bold red]",
        str(summary.not_matched_count),
        "Pipeline-1 proposal had no historical counterpart in Version N+1 evolution.",
    )

    console.print(table)

    metrics_panel = Panel(
        f"[bold white]Total Evaluated Proposals:[/bold white] {summary.total_pipeline_proposals_evaluated}\n"
        f"[bold white]Overall Match Rate (Strict + Partial):[/bold white] [bold green]{summary.match_rate:.1f}%[/bold green]\n"
        f"[bold white]Strict Match Rate:[/bold white] [bold yellow]{summary.strict_match_rate:.1f}%[/bold yellow]\n"
        f"[bold white]Quality Prediction Precision:[/bold white] [bold cyan]{summary.quality_prediction_precision:.1f}%[/bold cyan]",
        title="[bold green]Benchmark Performance Metrics[/bold green]",
        border_style="green",
    )
    console.print(metrics_panel)


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline 2: Historical SRS Version Comparison & Change Extraction Pipeline"
    )
    parser.add_argument("--project", type=str, help="Project name in 'srs doc versions/' (e.g. 1_FROG, 2_SMIRK)")
    parser.add_argument("--v1", type=str, help="Path to Version N earlier SRS file")
    parser.add_argument("--v2", type=str, help="Path to Version N+1 later SRS file")
    parser.add_argument("--limit", type=int, default=5, help="Maximum requirements to analyze (default: 5)")
    parser.add_argument("--provider", choices=["mock", "openai", "gemini"], default="mock", help="LLM backend")
    parser.add_argument("--model", default="gpt-4o", help="Model name (e.g. gpt-4o, gemini-2.5-flash)")
    parser.add_argument("--output-markdown", type=str, help="Path to save Markdown audit report")
    parser.add_argument("--output-csv", type=str, help="Path to save CSV evaluation summary")
    parser.add_argument("--output-json", type=str, help="Path to save full JSON execution trace")

    args = parser.parse_args()

    # Determine files
    if args.project:
        project_name = args.project
        v1_path, v2_path = get_version_files_for_project(project_name)
    elif args.v1 and args.v2:
        v1_path = Path(args.v1)
        v2_path = Path(args.v2)
        project_name = v1_path.parent.name
    else:
        project_name = "1_FROG"
        v1_path, v2_path = get_version_files_for_project("1_FROG")

    console.print(Panel(
        f"[bold white]Project:[/bold white] [cyan]{project_name}[/cyan]\n"
        f"[bold white]Version N (Earlier):[/bold white] [green]{v1_path}[/green]\n"
        f"[bold white]Version N+1 (Later):[/bold white] [green]{v2_path}[/green]\n"
        f"[bold white]LLM Backend:[/bold white] [yellow]{args.provider} ({args.model})[/yellow]",
        title="[bold yellow]Pipeline 2: Historical SRS Version Comparison & Change Extraction[/bold yellow]",
        border_style="yellow",
    ))

    # Initialize LLM
    if args.provider == "mock":
        llm_client = MockLLMClient()
    elif args.provider == "openai":
        llm_client = OpenAILLMClient(model_name=args.model)
    elif args.provider == "gemini":
        llm_client = GeminiLLMClient(model_name=args.model)
    else:
        raise ValueError(f"Unknown provider: {args.provider}")

    # Build Pipeline
    pipeline = HistoricalEvolutionPipeline(llm_client=llm_client)

    # Ingest & parse limited subset if requested
    console.print("\n[dim]Ingesting and parsing requirements from documents...[/dim]")
    parser_inst = pipeline.parser
    v1_all = parser_inst.parse_document(v1_path, version_label="N")
    v2_all = parser_inst.parse_document(v2_path, version_label="N+1")

    v1_subset = v1_all[: args.limit] if args.limit else v1_all
    v2_subset = v2_all[: args.limit] if args.limit else v2_all

    console.print(f"Extracted [cyan]{len(v1_all)}[/cyan] reqs from Version N (analyzing first {len(v1_subset)})")
    console.print(f"Extracted [cyan]{len(v2_all)}[/cyan] reqs from Version N+1 (analyzing first {len(v2_subset)})")

    # Run Pipeline Comparison
    srs_ctx = SRSContext(
        document_title=f"{project_name} SRS Evolution Specification",
        domain_summary=f"Automated evolution benchmark for {project_name} requirements.",
    )

    results = pipeline.run_comparison(
        v_n_source=v1_subset,
        v_n1_source=v2_subset,
        srs_context=srs_ctx,
        run_analyzer=True,
    )

    # Display Summaries
    display_alignment_summary(results["aligned_pairs"])
    display_change_classification_summary(results["change_records"], results["summary"])
    display_correspondence_benchmark_summary(results["benchmark_results"], results["summary"])

    # Export outputs if requested
    if args.output_markdown:
        md_text = pipeline.render_markdown_report(results, project_title=project_name)
        Path(args.output_markdown).write_text(md_text, encoding="utf-8")
        console.print(f"[bold green]Markdown report exported to {args.output_markdown}![/bold green]")

    if args.output_csv:
        pipeline.export_csv(results, args.output_csv)
        console.print(f"[bold green]CSV results exported to {args.output_csv}![/bold green]")

    if args.output_json:
        pipeline.export_json(results, args.output_json)
        console.print(f"[bold green]JSON trace exported to {args.output_json}![/bold green]")


if __name__ == "__main__":
    main()
