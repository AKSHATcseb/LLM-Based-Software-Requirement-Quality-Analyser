"""
run_multi_project_layer1_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Automated Test Harness for Layer 1 across ALL 15 SRS Projects and ALL Versions.
Extracts 5 to 10 requirements per version from each project, executes ISO 29148
Layer 1 Document Understanding & 7-Attribute Scoring, and generates:
1. `layer1_multi_project_evaluation_report.md` (Intuitive, academic-grade Markdown dossier)
2. `layer1_multi_project_evaluation_results.csv` (Spreadsheet-ready dataset of all evaluations)
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
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

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqam_analyzer import (
    Layer1DocumentScorer,
    Requirement,
    SRSContext,
    resolve_llm_client,
)
from srs_evolution.aligner import SRSParser

console = Console()
SRS_BASE_DIR = PROJECT_ROOT / "srs doc versions"


def discover_all_project_versions() -> Dict[str, List[Path]]:
    """Discovers all version files across each of the 15 SRS project folders."""
    if not SRS_BASE_DIR.exists():
        raise FileNotFoundError(f"Directory '{SRS_BASE_DIR}' not found.")

    def sort_folder_key(f: Path):
        name = f.name
        # Numeric prefix or full name
        num_match = re.match(r"^(\d+)", name)
        if num_match:
            return (1, int(num_match.group(1)), name)
        return (2, 0, name)

    def sort_file_key(f: Path):
        name = f.name.lower()
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

        att_match = re.search(r"attachment_0(?:\s*\((\d+)\))?", name)
        if att_match:
            idx = int(att_match.group(1)) if att_match.group(1) else 0
            return (1, idx, 0, 0, name)

        paren_match = re.search(r"\((\d+)\)", name)
        if paren_match and not att_match:
            return (2, int(paren_match.group(1)), 0, 0, name)

        digit_match = re.match(r"^(\d+)\.pdf$", name)
        if digit_match:
            return (3, int(digit_match.group(1)), 0, 0, name)

        gs_match = re.search(r"v(\d{2})(\d{2})(\d{2})", name)
        if gs_match:
            return (4, int(gs_match.group(1)), int(gs_match.group(2)), int(gs_match.group(3)), name)

        v_match = re.search(r"(?:^|[\-_ ])v?(\d+)(?:[\._](\d+))?(?:[\._](\d+))?", name)
        if v_match:
            p1 = int(v_match.group(1))
            p2 = int(v_match.group(2)) if v_match.group(2) else 0
            p3 = int(v_match.group(3)) if v_match.group(3) else 0
            return (5, p1, p2, p3, name)

        if name == "be_srs.pdf":
            return (5, 1, 0, 0, name)

        return (9, 0, 0, 0, name)

    projects: Dict[str, List[Path]] = {}
    folders = sorted([p for p in SRS_BASE_DIR.iterdir() if p.is_dir()], key=sort_folder_key)

    for folder in folders:
        files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in [".pdf", ".md", ".txt"]]
        if folder.name == "2_SMIRK":
            files = [f for f in files if "System Requirements" in f.name and "(" in f.name]
        elif "5_EVLA" in folder.name:
            files = [f for f in files if "be_srs" in f.name.lower()]

        if files:
            projects[folder.name] = sorted(files, key=sort_file_key)

    return projects


def clean_text_for_display(text: str, max_chars: int = 40) -> str:
    cleaned = re.sub(r"[\u200b-\u200f\ufeff\x00-\x1f\x7f-\x9f]", " ", text)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_chars:
        return cleaned[:max_chars] + "..."
    return cleaned


def main():
    parser = argparse.ArgumentParser(description="Multi-Project Multi-Version Layer 1 SQAM Test Harness")
    parser.add_argument("--limit-per-version", type=int, default=5, help="Number of requirements to extract and test per version (default: 5)")
    parser.add_argument("--provider", default=None, help="LLM backend (gemini, openai, or mock)")
    parser.add_argument("--output-md", default="layer1_multi_project_evaluation_report.md", help="Path to output Markdown dossier")
    parser.add_argument("--output-csv", default="layer1_multi_project_evaluation_results.csv", help="Path to output CSV dataset")
    args = parser.parse_args()

    # Discover projects
    project_versions = discover_all_project_versions()
    total_versions = sum(len(files) for files in project_versions.values())

    console.print(Panel(
        f"[bold white]Layer 1 Cross-Project ISO 29148 Test Harness[/bold white]\n"
        f"[cyan]Projects Discovered:[/cyan] {len(project_versions)} | [cyan]Total Document Versions:[/cyan] {total_versions}\n"
        f"[cyan]Requirements Target per Version:[/cyan] {args.limit_per_version}\n"
        f"[cyan]Estimated Total Evaluations:[/cyan] {total_versions * args.limit_per_version} requirements",
        title="[bold green]SQAM Diagnostic Sweep[/bold green]",
        border_style="green",
    ))

    # Initialize LLM Client
    active_provider = args.provider
    if not active_provider:
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            active_provider = "gemini"
        elif os.getenv("OPENAI_API_KEY"):
            active_provider = "openai"
        else:
            active_provider = "mock"

    try:
        llm_client = resolve_llm_client(
            provider=active_provider,
            allow_mock=(active_provider == "mock"),
        )
    except Exception as e:
        console.print(f"[bold red]LLM initialization error: {e}[/bold red]")
        sys.exit(1)

    layer1 = Layer1DocumentScorer(llm_client=llm_client)
    srs_parser = SRSParser()

    all_results: List[Dict[str, Any]] = []
    project_stats: Dict[str, Dict[str, Any]] = {}

    start_time = time.perf_counter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Testing SRS Versions...", total=total_versions)

        for proj_name, version_files in project_versions.items():
            project_stats[proj_name] = {
                "versions_count": len(version_files),
                "reqs_tested": 0,
                "scores": [],
                "defects_count": 0,
            }

            for file_path in version_files:
                version_label = file_path.stem
                progress.update(task, description=f"[cyan]{proj_name}[/cyan] -> [dim]{version_label}[/dim]")

                # Ingest & parse
                try:
                    req_units = srs_parser.parse_document(file_path, version_label=version_label)
                except Exception as ex:
                    progress.console.print(f"[red]Failed to parse {file_path.name}: {ex}[/red]")
                    progress.advance(task)
                    continue

                if not req_units:
                    progress.advance(task)
                    continue

                # Take subset
                selected_units = req_units[: args.limit_per_version]

                ctx = SRSContext(
                    document_title=f"{proj_name} - {version_label}",
                    domain_summary=f"Automated quality evaluation for {proj_name} requirements specification.",
                    glossary={},
                )

                for u in selected_units:
                    req_obj = Requirement(
                        req_id=u.req_id,
                        text=u.text,
                        section=u.section or "Functional Specifications",
                    )

                    l1_out = layer1.execute(requirement=req_obj, srs_context=ctx)

                    # Extract defect types and scores
                    defect_types = [s.attribute.value for s in l1_out.shortcomings]
                    is_clean = len(l1_out.shortcomings) == 0 and l1_out.overall_quality_score >= 8.0

                    attr_dict = {a.attribute.value.lower(): a.score for a in l1_out.attribute_scores}

                    record = {
                        "project": proj_name,
                        "version_file": file_path.name,
                        "version_stem": version_label,
                        "req_id": u.req_id,
                        "requirement_text": u.text,
                        "overall_quality_score": round(l1_out.overall_quality_score, 2),
                        "unambiguity": round(attr_dict.get("unambiguity", l1_out.overall_quality_score), 2),
                        "completeness": round(attr_dict.get("completeness", l1_out.overall_quality_score), 2),
                        "consistency": round(attr_dict.get("consistency", l1_out.overall_quality_score), 2),
                        "conformance": round(attr_dict.get("conformance", l1_out.overall_quality_score), 2),
                        "correctness": round(attr_dict.get("correctness", l1_out.overall_quality_score), 2),
                        "singularity": round(attr_dict.get("singularity", l1_out.overall_quality_score), 2),
                        "verifiability": round(attr_dict.get("verifiability", l1_out.overall_quality_score), 2),
                        "defects_count": len(l1_out.shortcomings),
                        "defect_types": "; ".join(defect_types) if defect_types else "None (Clean)",
                        "document_understanding": l1_out.document_understanding_summary,
                        "is_clean_pass": is_clean,
                    }

                    all_results.append(record)
                    project_stats[proj_name]["reqs_tested"] += 1
                    project_stats[proj_name]["scores"].append(record["overall_quality_score"])
                    project_stats[proj_name]["defects_count"] += len(l1_out.shortcomings)

                progress.advance(task)

    total_duration = time.perf_counter() - start_time
    total_evaluated = len(all_results)
    avg_score_all = sum(r["overall_quality_score"] for r in all_results) / total_evaluated if total_evaluated else 0.0
    clean_passes = sum(1 for r in all_results if r["is_clean_pass"])
    flawed_reqs = total_evaluated - clean_passes

    # Render Summary Table
    summary_table = Table(title="[bold green]Layer 1 Evaluation Results Across All 15 SRS Projects[/bold green]", show_header=True)
    summary_table.add_column("Project", style="bold cyan", width=18)
    summary_table.add_column("Versions", justify="center", width=10)
    summary_table.add_column("Reqs Tested", justify="right", width=12)
    summary_table.add_column("Avg Score (0-10)", justify="right", width=16)
    summary_table.add_column("Defects Flagged", justify="right", width=16)

    for p_name, st in project_stats.items():
        if st["reqs_tested"] > 0:
            avg_p = sum(st["scores"]) / len(st["scores"])
            score_color = "green" if avg_p >= 7.5 else ("yellow" if avg_p >= 6.0 else "red")
            summary_table.add_row(
                p_name,
                str(st["versions_count"]),
                str(st["reqs_tested"]),
                f"[{score_color}]{avg_p:.2f}[/{score_color}]",
                str(st["defects_count"]),
            )

    console.print("\n")
    console.print(summary_table)

    metrics_panel = Panel(
        f"[bold white]Total Requirements Evaluated:[/bold white] [bold cyan]{total_evaluated}[/bold cyan]\n"
        f"[bold white]Projects Covered:[/bold white] [bold cyan]{len(project_stats)}[/bold cyan] (All 15 Projects)\n"
        f"[bold white]Total Document Versions Evaluated:[/bold white] [bold cyan]{total_versions}[/bold cyan]\n"
        f"[bold white]Overall Mean Quality Score:[/bold white] [bold green]{avg_score_all:.2f} / 10.0[/bold green]\n"
        f"[bold white]Clean Compliant Requirements:[/bold white] [bold green]{clean_passes}[/bold green] ({(clean_passes/total_evaluated*100):.1f}%)\n"
        f"[bold white]Requirements with Actionable ISO Defects:[/bold white] [bold yellow]{flawed_reqs}[/bold yellow] ({(flawed_reqs/total_evaluated*100):.1f}%)\n"
        f"[bold white]Total Execution Time:[/bold white] [cyan]{total_duration:.2f} seconds[/cyan]",
        title="[bold yellow]Comprehensive Benchmark Summary[/bold yellow]",
        border_style="yellow",
    )
    console.print(metrics_panel)

    # -------------------------------------------------------------------------
    # Export to CSV
    # -------------------------------------------------------------------------
    csv_path = Path(args.output_csv)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "project", "version_file", "version_stem", "req_id", "requirement_text",
            "overall_quality_score", "unambiguity", "completeness", "consistency",
            "conformance", "correctness", "singularity", "verifiability",
            "defects_count", "defect_types", "document_understanding", "is_clean_pass"
        ])
        writer.writeheader()
        writer.writerows(all_results)
    console.print(f"[bold green]Complete CSV results exported to: {csv_path.resolve()}[/bold green]")

    # -------------------------------------------------------------------------
    # Export to Markdown Dossier
    # -------------------------------------------------------------------------
    md_path = Path(args.output_md)
    lines = [
        "# Comprehensive Layer 1 Multi-Project & Multi-Version Evaluation Dossier",
        "",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Evaluation Engine:** Layer 1 Document Understanding & 7-Attribute ISO 29148 Scorer  ",
        f"**LLM Backend:** `{type(llm_client).__name__}`  ",
        f"**Total Scope:** {total_evaluated} requirements across {total_versions} versions in all 15 industrial/academic SRS projects.  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Aggregate Metrics",
        "",
        f"- **Total Requirements Tested:** {total_evaluated}",
        f"- **Total Document Versions:** {total_versions} across 15 projects",
        f"- **Overall Mean Quality Score:** **{avg_score_all:.2f} / 10.0**",
        f"- **Fully Compliant Clean Requirements:** {clean_passes} ({(clean_passes/total_evaluated*100):.1f}%)",
        f"- **Requirements with Flagged ISO Flaws:** {flawed_reqs} ({(flawed_reqs/total_evaluated*100):.1f}%)",
        f"- **Average Processing Latency:** {(total_duration / total_evaluated * 1000):.1f} ms per requirement",
        "",
        "## 2. Project-by-Project Performance Breakdown",
        "",
        "| Project | Versions Covered | Reqs Evaluated | Mean Quality Score | Total Candidate Flaws | Compliant Ratio |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for p_name, st in project_stats.items():
        if st["reqs_tested"] > 0:
            avg_p = sum(st["scores"]) / len(st["scores"])
            p_res = [r for r in all_results if r["project"] == p_name]
            clean_p = sum(1 for r in p_res if r["is_clean_pass"])
            ratio_str = f"{(clean_p / len(p_res) * 100):.1f}%"
            lines.append(f"| **{p_name}** | {st['versions_count']} | {st['reqs_tested']} | **{avg_p:.2f} / 10.0** | {st['defects_count']} | {ratio_str} |")

    lines.extend([
        "",
        "## 3. Representative Requirement Evaluations (Sample Across Versions)",
        "",
        "| Project | Version | Req ID | Requirement Statement Body | Quality Score | Primary ISO Shortcomings |",
        "| :--- | :--- | :--- | :--- | :---: | :--- |",
    ])

    # Sample rows across projects
    for r in all_results[:40]:  # Show first 40 representative requirements in the dossier table
        clean_text = r["requirement_text"].replace("\n", " ").replace("|", "\\|")
        if len(clean_text) > 80:
            clean_text = clean_text[:80] + "..."
        lines.append(f"| {r['project']} | {r['version_stem']} | `{r['req_id']}` | {clean_text} | **{r['overall_quality_score']}** | {r['defect_types']} |")

    lines.extend([
        "",
        "---",
        f"*Full tabular results containing all {total_evaluated} records are available in `{args.output_csv}`.*",
    ])

    md_path.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[bold green]Comprehensive Markdown Dossier exported to: {md_path.resolve()}[/bold green]")


if __name__ == "__main__":
    main()
