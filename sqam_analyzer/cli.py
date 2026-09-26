"""
sqam_analyzer.cli
~~~~~~~~~~~~~~~~~
Interactive Command-Line Interface and Human-in-the-Loop Review Console.
Leverages the `rich` library for terminal rendering of side-by-side comparisons,
word diffs, quality scorecards, and audit logs.
"""

from __future__ import annotations

import json
import sys
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from sqam_analyzer.diff_utils import format_ansi_diff
from sqam_analyzer.models import (
    HumanDecisionStatus,
    PipelineExecutionResult,
    ValidationVerdict,
)
from sqam_analyzer.pipeline import RequirementQualityPipeline

console = Console()


def display_quality_scorecard(result: PipelineExecutionResult) -> None:
    """Renders a formatted table of the 7 quality attributes and their scores."""
    if not result.layer1_result:
        return

    table = Table(title=f"Quality Scorecard (Overall: {result.layer1_result.overall_quality_score:.1f}/10)", show_header=True)
    table.add_column("Attribute", style="cyan", width=26)
    table.add_column("Score", justify="right", style="bold", width=8)
    table.add_column("Rationale", style="dim")

    for score_obj in result.layer1_result.attribute_scores:
        score_val = score_obj.score
        if score_val >= 8.5:
            color = "green"
        elif score_val >= 7.0:
            color = "yellow"
        else:
            color = "red"
        table.add_row(
            score_obj.attribute.value,
            f"[{color}]{score_val:.1f}[/{color}]",
            score_obj.rationale,
        )

    console.print(table)


def display_defect_reasoning_panel(result: PipelineExecutionResult) -> None:
    """Renders Layer 2 reasoning showing which defects were retained vs discarded."""
    if not result.layer2_result or not result.layer2_result.evaluations:
        console.print("[dim]Layer 2: No candidate defects were subjected to reasoning.[/dim]")
        return

    table = Table(title="Layer 2: Defect Reasoning & Context Verification", show_header=True)
    table.add_column("Defect ID", width=10)
    table.add_column("Attribute", width=18)
    table.add_column("Status", width=12)
    table.add_column("Contextual Reasoning / Justification")

    for ev in result.layer2_result.evaluations:
        if ev.status.value == "justified":
            status_text = "[bold red]JUSTIFIED[/bold red]"
        else:
            status_text = "[bold green]DISCARDED[/bold green] (Contextual False Positive)"

        table.add_row(
            ev.defect_id,
            ev.attribute.value,
            status_text,
            ev.context_reasoning,
        )

    console.print(table)


def display_validation_panel(result: PipelineExecutionResult) -> None:
    """Renders Layer 4 independent audit checks."""
    if not result.layer4_result:
        return

    l4 = result.layer4_result
    verdict_style = "bold green" if l4.is_valid else "bold red"
    panel_title = f"Layer 4: Independent Auditor Verdict: [{verdict_style}]{l4.verdict.value.upper()}[/{verdict_style}]"

    table = Table(show_header=True)
    table.add_column("Criterion", width=25)
    table.add_column("Result", width=8)
    table.add_column("Observations")

    for check in l4.checks:
        res_str = "[green]PASS[/green]" if check.passed else "[red]FAIL[/red]"
        table.add_row(check.criterion, res_str, check.observations)

    console.print(Panel(table, title=panel_title, expand=False))
    console.print(f"[italic]Auditor Critique:[/italic] {l4.critique_and_feedback}\n")


def display_comparison_dossier(result: PipelineExecutionResult) -> None:
    """Displays the side-by-side comparison of original vs refined requirement."""
    req = result.requirement
    console.print("\n" + "=" * 80)
    console.rule(f"[bold cyan]Requirement: {req.req_id}[/bold cyan] ({req.req_type} - {req.section or 'General'})")

    if result.status == "error":
        console.print(Panel(
            f"[bold red]Pipeline Error:[/bold red] {result.error_message}",
            title="[bold red]Execution Failure[/bold red]",
            border_style="red",
        ))
        return

    # Original requirement
    console.print(Panel(
        f"[bold white]{req.text}[/bold white]",
        title="[bold yellow]Original Requirement[/bold yellow]",
        border_style="yellow",
    ))

    # Quality breakdown
    display_quality_scorecard(result)

    # Defect reasoning
    display_defect_reasoning_panel(result)

    # Refined requirement and diff
    l3 = result.layer3_result
    l4 = result.layer4_result

    if l3 and l3.refined_text != req.text:
        display_validation_panel(result)

        # Word Diff
        diff_str = format_ansi_diff(req.text, l3.refined_text)
        console.print(Panel(
            diff_str,
            title="[bold magenta]Word-Level Diff (Red: Removed, Green: Added)[/bold magenta]",
            border_style="magenta",
        ))

        # Refined Proposal
        console.print(Panel(
            f"[bold green]{l3.refined_text}[/bold green]\n\n"
            f"[dim]Changes Made: {', '.join(l3.changes_made)}[/dim]\n"
            f"[dim]Intent Rationale: {l3.functional_intent_preservation_rationale}[/dim]",
            title="[bold green]Proposed Refinement (Layer 3)[/bold green]",
            border_style="green",
        ))
    else:
        console.print("[green]No refinement necessary. The requirement passed all quality thresholds.[/green]")


def run_interactive_review(
    results: List[PipelineExecutionResult],
    pipeline: RequirementQualityPipeline,
) -> List[PipelineExecutionResult]:
    """
    Steps through each analysis result, presents the comparison dossier,
    and prompts the human reviewer to make a decision.
    """
    console.print("\n[bold cyan]Starting Human-in-the-Loop Review Session...[/bold cyan]")
    console.print("Commands: [a] Accept Refinement | [r] Retain Original | [e] Edit Manually | [s] Skip\n")

    for idx, result in enumerate(results, start=1):
        display_comparison_dossier(result)
        dossier = result.layer5_result
        if not dossier:
            continue

        prompt_str = f"[{idx}/{len(results)}] Decision for {result.requirement.req_id}"
        choice = Prompt.ask(
            prompt_str,
            choices=["a", "r", "e", "s"],
            default="a" if (result.layer4_result and result.layer4_result.is_valid) else "r",
        ).lower()

        if choice == "a":
            comments = Prompt.ask("Optional reviewer notes (press enter to skip)", default="")
            pipeline.layer5.record_decision(
                dossier=dossier,
                status=HumanDecisionStatus.ACCEPTED,
                comments=comments or "Accepted refinement via interactive review.",
            )
            console.print("[bold green] Refinement accepted![/bold green]\n")

        elif choice == "r":
            reason = Prompt.ask("Reason for retaining original requirement", default="Retained original text.")
            pipeline.layer5.record_decision(
                dossier=dossier,
                status=HumanDecisionStatus.REJECTED,
                comments=reason,
            )
            console.print("[bold yellow] Original requirement retained.[/bold yellow]\n")

        elif choice == "e":
            default_val = dossier.refined_text or dossier.original_text
            console.print(f"Current suggestion: {default_val}")
            custom = Prompt.ask("Enter custom requirement text")
            comments = Prompt.ask("Notes on custom edit", default="Manual modification by reviewer.")
            pipeline.layer5.record_decision(
                dossier=dossier,
                status=HumanDecisionStatus.EDITED_BY_HUMAN,
                comments=comments,
                custom_text=custom,
            )
            console.print("[bold blue] Custom requirement recorded.[/bold blue]\n")

        elif choice == "s":
            console.print("[dim]Skipped decision. Status remains pending.[/dim]\n")

    console.print("\n[bold green]Human-in-the-Loop Review Session Complete![/bold green]")
    return results
