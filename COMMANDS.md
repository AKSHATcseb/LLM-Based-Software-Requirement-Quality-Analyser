# SQAM Project Showcase Commands Guide

This document contains all ready-to-run commands to demonstrate and showcase the capabilities of the **SQAM (Software Requirement Quality Analyzer)** system.

---

## 1. Quick Verification & Test Suite
*Proves that all components, layers, and dependencies are healthy and functional.*

```powershell
# 1. Run all automated unit and integration tests (29 passing tests)
python -m pytest

# 2. Run the end-to-end 5-layer showcase demonstration (Colored Rich UI in Terminal)
python example.py
```

---

## 2. Pipeline 1: 5-Layer AI-Assisted Requirement Quality Analyzer
*Evaluates requirements across 7 ISO/IEC/IEEE 29148 dimensions, filters false positives using document context/glossary, performs minimal surgical refinement, validates via an independent auditor, and displays word-level colored diffs.*

### A. Quick Demonstrations
```powershell
# Run automated showcase on built-in Avionics sample SRS (5 requirements)
python main.py --demo

# Run on the included sample SRS JSON file
python main.py --srs-file sample_new_srs.json --limit 3
```

### B. Interactive Human-in-the-Loop Mode
*Walks through requirements one-by-one, displaying quality scorecards, context justifications, auditor critiques, and diffs, prompting for reviewer sign-off (`[A]ccept`, `[R]eject`, `[E]dit`).*

```powershell
python main.py --srs-file sample_new_srs.json --interactive --limit 2
```

### C. Run Directly on Real-World SRS Documents (`srs doc versions/`)
*Extracts requirements from actual industrial PDFs and Markdown files and runs them through the 5-layer pipeline:*

```powershell
# 1. Computer Vision & Gesture Recognition (1_FROG) - Real PDF document
python test_srs_doc.py --project 1_FROG --limit 3

# 2. Autonomous Driving ML Safety (2_SMIRK) - Markdown specification
python test_srs_doc.py --project 2_SMIRK --limit 3

# 3. Direct path to any specific PDF document
python test_srs_doc.py --file "srs doc versions/1_FROG/SRS_v1.1.pdf" --limit 3

# 4. Interactive review on a real SRS document
python test_srs_doc.py --project 1_FROG --limit 2 --interactive
```

### D. Exporting Quality Audit Reports
*Generates a formal Markdown audit dossier summarizing scorecards, defects, and refinements:*

```powershell
# Export audit report to Markdown
python main.py --srs-file sample_new_srs.json --limit 5 --output-report audit_report.md

# Export audit report directly from a real PDF
python test_srs_doc.py --project 1_FROG --limit 5 --output-report frog_audit_report.md
```

### E. Selecting LLM Provider Backends
```powershell
# Google Gemini (Default - requires GEMINI_API_KEY in .env)
python main.py --srs-file sample_new_srs.json --provider gemini --model gemini-2.5-flash

# OpenAI GPT-4o (requires OPENAI_API_KEY in .env)
python main.py --srs-file sample_new_srs.json --provider openai --model gpt-4o

# High-Fidelity Mock LLM (100% offline, zero API keys or network required)
python main.py --srs-file sample_new_srs.json --provider mock
```

---

## 3. Pipeline 2: Historical Version Evolution & Benchmark
*Compares earlier working drafts against final release versions ($Version_N$ vs. $Version_{N+1}$), aligns requirements using exact-ID and TF-IDF fallback, extracts semantic diffs, classifies changes into the 9-category empirical taxonomy, and rates AI proposals against human engineer revisions.*

```powershell
# 1. Run evolution pipeline on Project 14 (Later Draft vs Final Release)
python run_evolution_pipeline.py --project 14 --limit 5

# 2. Run evolution pipeline on Project 1_FROG
python run_evolution_pipeline.py --project 1_FROG --limit 5

# 3. Compare two specific PDF version files directly
python run_evolution_pipeline.py --v1 "srs doc versions/1_FROG/SRS_v1.1.pdf" --v2 "srs doc versions/1_FROG/Software_Requirements_Specification_v30.pdf" --limit 5

# 4. Compare Earliest Draft vs Final Release
python run_evolution_pipeline.py --project 14 --mode earliest_vs_final --limit 5

# 5. Export evolution audit report to Markdown and CSV
python run_evolution_pipeline.py --project 1_FROG --limit 5 --output-markdown frog_evolution.md --output-csv frog_evolution.csv
```

---

## 4. Dataset Inspection & Empirical Research Evaluation
*Inspects the 15 versioned SRS projects and calculates the 5 core research metrics: User Acceptance Rate (UAR), Refinement Rejection Rate (RRR), Flawed Suggestion Rate (FSR), Intent Preservation Rate (IPR), and Aligned Precision/Loss (APL).*

```powershell
# 1. List all 15 SRS projects and discovered document versions
python build_dataset.py --list

# 2. Inspect text and requirement statements extracted from a project
python build_dataset.py --inspect 1_FROG
python build_dataset.py --inspect 2_SMIRK

# 3. Compute empirical research metrics on benchmark dataset
python evaluate_srs.py --benchmark sample_benchmark.json --output evaluation_summary.md

# 4. Run benchmark evaluation with Gemini or OpenAI
python evaluate_srs.py --benchmark sample_benchmark.json --provider gemini --model gemini-2.5-flash
```

---

## 5. Diagnostic & Format-Compliance MCP Server (CLI Mode)
*Stress-tests the pipeline against adversarial prompt injections, format escapes, schema violations, and pipeline sequence integrity.*

```powershell
# 1. Audit format and pipeline compliance for a specific project
python sqam_mcp_server.py --cli --project 1_FROG --limit 3

# 2. Run adversarial fuzzing / stress test suite (prompt injection & malformed inputs)
python sqam_mcp_server.py --cli --fuzz

# 3. Scan all 15 projects for format and schema adherence
python sqam_mcp_server.py --cli --scan-all --limit 1
```

---

## 6. Full-Corpus 942-Requirement Empirical Evaluation Sweep
*Runs Layer 1 ISO 29148 scoring, deep behavior logging, and the full 5-layer pipeline evaluation across all 942 requirements in all 15 SRS projects and 44 document versions.*

```powershell
# 1. Run master evaluation on all 942 requirements (generates complete CSV, MD dossiers, and JSON metrics)
python scripts/run_942_evaluation.py

# 2. Run multi-project Layer 1 test harness on all 942 requirements
python run_multi_project_layer1_test.py --all --provider mock

# 3. Run Layer 1 deep behavior log across all 942 requirements
python run_layer1_deep_analysis.py
```

