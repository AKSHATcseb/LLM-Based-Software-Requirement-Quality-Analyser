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
import re
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from sqam_analyzer.llm_provider import (
    GeminiLLMClient,
    MockLLMClient,
    OpenAILLMClient,
    resolve_llm_client,
)
from sqam_analyzer.models import SRSContext
from srs_evolution import (
    AlignmentType,
    ChangeCategory,
    CorrespondenceRating,
    HistoricalEvolutionPipeline,
)

console = Console()
SRS_BASE_DIR = Path("srs doc versions")


def clean_preview(text: Optional[str], max_len: int = 35) -> str:
    """Cleans raw text for console display, stripping control and zero-width characters."""
    if not text:
        return ""
    cleaned = re.sub(r"[\u200b-\u200f\ufeff\x00-\x1f\x7f-\x9f]", " ", text)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "..."
    return cleaned


def get_version_files_for_project(project_name: str, mode: str = "later_vs_final") -> tuple[Path, Path]:
    """
    Finds the working draft file and final release file for an SRS project.

    Modes:
      - 'later_vs_final' (Default):
        Selects the later working draft (penultimate mature version, e.g. vN-1 or v2)
        and benchmarks against the final release (vFinal, e.g. vN or v3).
        Rationale: Initial skeletons (v1) have high functional volatility, whereas later
        working drafts represent stabilized features where changes before final release
        are genuine ISO 29148 specification quality hardening.
      - 'earliest_vs_final':
        Selects the initial draft (v1) and compares against the final release.
    """
    import re

    project_dir = SRS_BASE_DIR / project_name
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory '{project_dir}' not found.")

    files = [f for f in sorted(project_dir.iterdir()) if f.is_file() and f.suffix.lower() in [".pdf", ".md", ".txt"]]
    if len(files) < 2:
        raise ValueError(f"Project '{project_name}' must have at least 2 version files, found {len(files)}.")

    # Project-specific document filtering if multiple specification artifacts exist
    if project_name == "2_SMIRK":
        srs_files = [f for f in files if "System Requirements" in f.name and "(" in f.name]
        if len(srs_files) >= 2:
            files = srs_files
    elif "5_EVLA" in project_name:
        be_files = [f for f in files if "be_srs" in f.name.lower()]
        if len(be_files) >= 2:
            files = be_files

    def sort_key(f: Path):
        name = f.name.lower()

        # 4_UIC specific version hierarchy: 15.0 -> 15.1 -> 15.3 -> 16.0 -> 16.1
        if "16.1" in name:
            return (5, 16, 1, 0, name)
        if "16.0" in name:
            return (5, 16, 0, 0, name)
        if "15.3" in name:
            return (5, 15, 3, 0, name)
        if "15.1" in name:
            return (5, 15, 1, 0, name)
        if "v15" in name:
            return (5, 15, 0, 0, name)

        # Attachment_0 handling: Attachment_0.pdf (0) -> Attachment_0 (1).pdf (1) -> Attachment_0 (2).pdf (2)
        att_match = re.search(r"attachment_0(?:\s*\((\d+)\))?", name)
        if att_match:
            idx = int(att_match.group(1)) if att_match.group(1) else 0
            return (1, idx, 0, 0, name)

        # Numbered parenthetical drafts: e.g. (1).md -> (2).md -> (3).md
        paren_match = re.search(r"\((\d+)\)", name)
        if paren_match and not att_match:
            return (2, int(paren_match.group(1)), 0, 0, name)

        # Single digit files: e.g. 1.pdf -> 2.pdf -> 3.pdf
        digit_match = re.match(r"^(\d+)\.pdf$", name)
        if digit_match:
            return (3, int(digit_match.group(1)), 0, 0, name)

        # gs_mec002v040101p.pdf -> version subfields
        gs_match = re.search(r"v(\d{2})(\d{2})(\d{2})", name)
        if gs_match:
            return (4, int(gs_match.group(1)), int(gs_match.group(2)), int(gs_match.group(3)), name)

        # General version tag format: v1.1, v30, V1_0_1, V4_1_0, V5_1_0, be_srs_2.1
        v_match = re.search(r"(?:^|[\-_ ])v?(\d+)(?:[\._](\d+))?(?:[\._](\d+))?", name)
        if v_match:
            p1 = int(v_match.group(1))
            p2 = int(v_match.group(2)) if v_match.group(2) else 0
            p3 = int(v_match.group(3)) if v_match.group(3) else 0
            return (5, p1, p2, p3, name)

        if name == "be_srs.pdf":
            return (5, 1, 0, 0, name)

        return (9, 0, 0, 0, name)

    sorted_files = sorted(files, key=sort_key)

    if mode == "later_vs_final":
        # Penultimate working draft vs Final release
        draft_file = sorted_files[-2] if len(sorted_files) >= 3 else sorted_files[0]
        final_file = sorted_files[-1]
    else:
        # Earliest initial draft vs Final release
        draft_file = sorted_files[0]
        final_file = sorted_files[-1]

    return draft_file, final_file


def display_alignment_summary(aligned_pairs: list):
    """Renders a Rich table of the aligned requirements across versions."""
    table = Table(title="[bold cyan]Step 1 & 2: Cross-Version Requirement Alignment (Later Draft vs Final Release)[/bold cyan]", show_header=True)
    table.add_column("Type", width=14)
    table.add_column("Later Working Draft (vDraft)", width=32)
    table.add_column("Final SRS Release (vFinal)", width=32)
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

        v1_preview = f"[{p.req_id_v1}] " + clean_preview(p.text_v1, max_len=30) if p.text_v1 else "[dim]None (Added)[/dim]"
        v2_preview = f"[{p.req_id_v2}] " + clean_preview(p.text_v2, max_len=30) if p.text_v2 else "[dim]None (Deleted)[/dim]"

        table.add_row(type_str, v1_preview, v2_preview, f"{p.alignment_confidence:.2f}")

    if len(aligned_pairs) > 8:
        table.add_row("...", f"[dim]+{len(aligned_pairs) - 8} more pairs[/dim]", "...", "...")

    console.print(table)


def display_change_classification_summary(change_records: list, summary):
    """Renders a Rich table of the empirical change categories."""
    table = Table(title="[bold yellow]Step 3: Empirical Change Taxonomy (Later Draft -> Final Release Changes)[/bold yellow]", show_header=True)
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
    table = Table(title="[bold green]Step 4 & 5: Pipeline-1 (on Later Draft) vs Final Release Semantic Correspondence[/bold green]", show_header=True)
    table.add_column("Rating", width=18)
    table.add_column("Count", justify="right", width=8)
    table.add_column("Academic Evaluation Meaning", style="dim")

    table.add_row(
        "[bold green]MATCHED[/bold green]",
        str(summary.matched_count),
        "Pipeline-1 independently surfaced and resolved what stakeholders actually fixed in Final Release.",
    )
    table.add_row(
        "[bold yellow]PARTIALLY_MATCHED[/bold yellow]",
        str(summary.partially_matched_count),
        "Pipeline-1 correctly targeted the flawed area, but applied an alternative fix strategy.",
    )
    table.add_row(
        "[bold red]NOT_MATCHED[/bold red]",
        str(summary.not_matched_count),
        "Pipeline-1 proposal had no historical counterpart in the Final Release evolution.",
    )

    console.print(table)

    metrics_panel = Panel(
        f"[bold white]Total Evaluated Proposals:[/bold white] {summary.total_pipeline_proposals_evaluated}\n"
        f"[bold white]Overall Match Rate (Strict + Partial):[/bold white] [bold green]{summary.match_rate:.1f}%[/bold green]\n"
        f"[bold white]Strict Match Rate:[/bold white] [bold yellow]{summary.strict_match_rate:.1f}%[/bold yellow]\n"
        f"[bold white]Quality Prediction Precision:[/bold white] [bold cyan]{summary.quality_prediction_precision:.1f}%[/bold cyan]",
        title="[bold green]Benchmark Performance Metrics (Later Draft vs Final Release)[/bold green]",
        border_style="green",
    )
    console.print(metrics_panel)


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline 2: Historical SRS Version Comparison & Change Extraction Pipeline"
    )
    parser.add_argument("--project", type=str, help="Project name in 'srs doc versions/' (e.g. 1_FROG, 2_SMIRK, 14, 15)")
    parser.add_argument(
        "--mode",
        choices=["later_vs_final", "earliest_vs_final"],
        default="later_vs_final",
        help="Comparison mode: 'later_vs_final' (default, compares penultimate working draft against final SRS) or 'earliest_vs_final'",
    )
    parser.add_argument("--v1", type=str, help="Path to Working Draft SRS file (overrides automatic discovery)")
    parser.add_argument("--v2", type=str, help="Path to Final Release SRS file (overrides automatic discovery)")
    parser.add_argument("--limit", type=int, default=5, help="Maximum requirements to analyze (default: 5)")
    parser.add_argument("--provider", choices=["gemini", "openai", "mock"], default=None, help="LLM backend (default: auto-detects configured GEMINI_API_KEY or OPENAI_API_KEY)")
    parser.add_argument("--model", default=None, help="Model name (defaults to gemini-2.5-flash or gpt-4o)")
    parser.add_argument("--output-markdown", type=str, help="Path to save Markdown audit report")
    parser.add_argument("--output-csv", type=str, help="Path to save CSV evaluation summary")
    parser.add_argument("--output-json", type=str, help="Path to save full JSON execution trace")

    args = parser.parse_args()

    # Determine files
    if args.project:
        project_name = args.project
        v1_path, v2_path = get_version_files_for_project(project_name, mode=args.mode)
    elif args.v1 and args.v2:
        v1_path = Path(args.v1)
        v2_path = Path(args.v2)
        project_name = v1_path.parent.name
    else:
        project_name = "1_FROG"
        v1_path, v2_path = get_version_files_for_project("1_FROG", mode=args.mode)

    # Initialize LLM (Mandatory Live LLM)
    try:
        llm_client = resolve_llm_client(
            provider=args.provider,
            model=args.model,
            allow_mock=(args.provider == "mock"),
        )
    except ValueError as e:
        console.print(f"[bold red]{e}[/bold red]")
        sys.exit(1)

    draft_label = "Later Working Draft (Target)" if args.mode == "later_vs_final" else "Initial Draft (Target)"
    final_label = "Final SRS Release (Ground Truth)"

    console.print(Panel(
        f"[bold white]Project:[/bold white] [cyan]{project_name}[/cyan]\n"
        f"[bold white]Comparison Mode:[/bold white] [magenta]{args.mode}[/magenta]\n"
        f"[bold white]{draft_label}:[/bold white] [green]{v1_path}[/green]\n"
        f"[bold white]{final_label}:[/bold white] [green]{v2_path}[/green]\n"
        f"[bold white]LLM Backend:[/bold white] [yellow]{args.provider or type(llm_client).__name__} ({args.model or getattr(llm_client, 'model_name', 'default')})[/yellow]",
        title="[bold yellow]Pipeline 2: Historical SRS Version Comparison & Change Extraction[/bold yellow]",
        border_style="yellow",
    ))

    # Build Pipeline
    pipeline = HistoricalEvolutionPipeline(llm_client=llm_client)

    # Ingest & parse limited subset if requested
    console.print("\n[dim]Ingesting and parsing requirements from documents...[/dim]")
    parser_inst = pipeline.parser
    v1_all = parser_inst.parse_document(v1_path, version_label="Draft")
    v2_all = parser_inst.parse_document(v2_path, version_label="Final")

    v1_subset = v1_all[: args.limit] if args.limit else v1_all
    v2_subset = v2_all[: args.limit] if args.limit else v2_all

    console.print(f"Extracted [cyan]{len(v1_all)}[/cyan] reqs from {draft_label} (analyzing first {len(v1_subset)})")
    console.print(f"Extracted [cyan]{len(v2_all)}[/cyan] reqs from {final_label} (analyzing first {len(v2_subset)})")

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
