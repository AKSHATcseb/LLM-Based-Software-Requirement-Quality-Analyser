"""
test_srs_doc.py
~~~~~~~~~~~~~~~
Directly test and analyze real SRS documents from `srs doc versions/`.
Extracts requirements from PDF or Markdown files and runs them through the 5-layer pipeline.

Usage:
  python test_srs_doc.py --project 1_FROG --limit 3
  python test_srs_doc.py --project 1_FROG --limit 5 --output-report frog_v1_audit.md
  python test_srs_doc.py --file "srs doc versions/1_FROG/SRS_v1.1.pdf" --limit 3 --interactive
  python test_srs_doc.py --project 1_FROG --provider gemini --model gemini-2.5-flash --limit 3
"""

import argparse
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from sqam_analyzer import (
    GeminiLLMClient,
    MockLLMClient,
    OpenAILLMClient,
    Requirement,
    RequirementQualityPipeline,
    SRSContext,
    resolve_llm_client,
)
from sqam_analyzer.cli import display_comparison_dossier, run_interactive_review
from build_dataset import extract_candidate_requirements, extract_text_from_file

console = Console()
SRS_BASE_DIR = Path("srs doc versions")


def find_earliest_file_in_project(project_folder: Path) -> Path:
    """Identifies the earliest chronological version file in a project folder."""
    files = [f for f in sorted(project_folder.iterdir()) if f.is_file() and f.suffix.lower() in [".pdf", ".md"]]
    if not files:
        raise FileNotFoundError(f"No PDF or Markdown files found in {project_folder}")

    # Prioritize files with 'v1', 'v0', 'Attachment_0', or sort alphabetically
    for f in files:
        name_lower = f.name.lower()
        if "v1" in name_lower or "v0" in name_lower or "(1)" in name_lower or "1.pdf" in name_lower:
            return f
    return files[0]


def extract_context_from_document(doc_text: str, project_name: str) -> SRSContext:
    """Extracts high-level domain summary and glossary from document text."""
    # Find Glossary or Definitions section
    glossary = {}
    lines = doc_text.splitlines()
    in_glossary = False

    for line in lines[:300]:
        line_clean = line.strip()
        if any(h in line_clean.lower() for h in ["1.3 glossary", "definitions", "acronyms", "terminology"]):
            in_glossary = True
            continue
        if in_glossary:
            if line_clean.startswith("#") or (len(line_clean) > 3 and line_clean[0].isdigit() and line_clean[1] == "."):
                break
            if "-" in line_clean or ":" in line_clean:
                parts = line_clean.split(":", 1) if ":" in line_clean else line_clean.split("-", 1)
                term = parts[0].strip().lstrip("-* ")
                defn = parts[1].strip() if len(parts) > 1 else ""
                if 2 < len(term) < 40 and len(defn) > 5:
                    glossary[term] = defn

    # Extract first 500 chars for domain summary
    summary_snippet = " ".join([l.strip() for l in lines[10:35] if l.strip()])[:350]
    domain_summary = summary_snippet or f"Software Requirements Specification for {project_name}."

    return SRSContext(
        document_title=f"SRS Specification - {project_name}",
        domain_summary=domain_summary,
        glossary=glossary,
        applicable_standards=["ISO/IEC/IEEE 29148:2018"],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Directly Test Real SRS Documents Through the 5-Layer Pipeline"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Project folder name in 'srs doc versions/' (e.g., 1_FROG, 2_SMIRK, 15)",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Direct path to an SRS PDF or Markdown file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of requirements to extract and test (default: 5)",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai", "mock"],
        default=None,
        help="LLM provider (default: auto-detects configured GEMINI_API_KEY or OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model name (defaults to gemini-2.5-flash or gpt-4o)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive terminal review session",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        help="Optional path to export Markdown audit report",
    )

    args = parser.parse_args()

    # Determine file to test
    if args.file:
        target_file = Path(args.file)
        project_name = target_file.parent.name
    elif args.project:
        project_dir = SRS_BASE_DIR / args.project
        if not project_dir.exists():
            console.print(f"[bold red]Error: Project directory '{project_dir}' not found.[/bold red]")
            return
        target_file = find_earliest_file_in_project(project_dir)
        project_name = args.project
    else:
        # Default to 1_FROG
        project_name = "1_FROG"
        target_file = find_earliest_file_in_project(SRS_BASE_DIR / "1_FROG")

    console.print(Panel(
        f"[bold white]Target Project:[/bold white] [cyan]{project_name}[/cyan]\n"
        f"[bold white]Input Document:[/bold white] [green]{target_file}[/green]\n"
        f"[bold white]LLM Provider:[/bold white] [yellow]{args.provider} ({args.model})[/yellow]",
        title="[bold yellow]Direct SRS Document Quality Test[/bold yellow]",
        border_style="yellow",
    ))

    # 1. Extract text and requirements
    console.print("[dim]Reading document and extracting candidate requirements...[/dim]")
    doc_text = extract_text_from_file(target_file)
    extracted_req_texts = extract_candidate_requirements(doc_text)

    if not extracted_req_texts:
        console.print("[bold red]No 'shall' or normative requirement statements found in document.[/bold red]")
        return

    console.print(f"Total Requirements Detected: [bold green]{len(extracted_req_texts)}[/bold green]")
    selected_texts = extracted_req_texts[: args.limit]
    console.print(f"Testing the first [bold yellow]{len(selected_texts)}[/bold yellow] requirements...\n")

    # 2. Build Context and Requirement objects
    srs_context = extract_context_from_document(doc_text, project_name)
    requirements = [
        Requirement(
            req_id=f"{project_name}-REQ-{idx:03d}",
            text=text,
            req_type="Functional",
            section="Extracted from SRS Document",
        )
        for idx, text in enumerate(selected_texts, start=1)
    ]

    # 3. Setup LLM and Pipeline (Mandatory Live LLM)
    try:
        llm_client = resolve_llm_client(
            provider=args.provider,
            model=args.model,
            allow_mock=(args.provider == "mock"),
        )
    except ValueError as e:
        console.print(f"[bold red]{e}[/bold red]")
        sys.exit(1)

    pipeline = RequirementQualityPipeline(default_llm=llm_client)

    # 4. Execute Analysis
    results = pipeline.analyze_batch(requirements, srs_context)

    if args.interactive:
        results = run_interactive_review(results, pipeline)
    else:
        for res in results:
            display_comparison_dossier(res)

    # 5. Export Report
    if args.output_report:
        report_sections = [
            f"# Real Document Quality Audit: {project_name}",
            f"**Source Document:** `{target_file.name}`\n",
        ]
        for res in results:
            sec = pipeline.layer5.render_markdown_report(
                dossier=res.layer5_result,
                layer1_output=res.layer1_result,
                layer2_output=res.layer2_result,
                layer4_output=res.layer4_result,
            )
            report_sections.append(sec)

        with open(args.output_report, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(report_sections))
        console.print(f"\n[bold green]Complete audit report saved to {args.output_report}![/bold green]")


if __name__ == "__main__":
    main()
