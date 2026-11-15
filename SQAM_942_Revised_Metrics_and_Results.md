# SQAM: Empirical Evaluation Results & Verification Compendium
**Empirical Live Model Evaluation ($N = 50$) & Full-Corpus Architectural Verification ($N = 942$)**

- **Evaluation Standard:** ISO/IEC/IEEE 29148:2018 (*Systems and software engineering — Life cycle processes — Requirements engineering*)
- **Corpus Scope:** 15 Industrial & Academic SRS Projects, 46 Evaluated Document Files (43 Primary Specifications), 942 Normative Statements
- **Empirical Evaluation Battery:** 50 Normative Requirements Stratified across all 15 Projects, evaluated end-to-end with live LLM inference (`gemini-3.5-flash-lite`)
- **Architectural Benchmark Battery:** 942 Requirements evaluated via deterministic offline state-machine verification (`MockLLMClient`)

---

## 1. Methodological Provenance & Execution Transparency

To ensure strict scientific integrity, this compendium discloses the exact origin and execution mode of all reported metrics:

1. **Empirical Live Model Results ($N = 50$, `gemini-3.5-flash-lite`):**
   - **Engine:** Google Gemini API (`models/gemini-3.5-flash-lite`), live remote inference at temperature $T = 0.0$.
   - **Workload:** 168 live remote API calls executed through `scripts/run_pilot_evaluation.py` with sliding-window rate limiting (15 RPM) and per-requirement JSON checkpointing (`results/raw/pilot/`).
   - **Coverage:** Exactly 50 requirements stratified across all 15 projects (3–4 requirements per project across diverse operational domains).
   - **Layer Progression:** Full end-to-end evaluation across all four computational layers (Layer 1 Document Scorer $\rightarrow$ Layer 2 Defect Reasoner $\rightarrow$ Layer 3 Solution Generator $\rightarrow$ Layer 4 Solution Validator).
   - **Quality Score Variance:** Demonstrates authentic, non-uniform scoring distributions across all 7 ISO 29148 quality attributes.
   - **False Alarm Suppression & Validation:** Genuine contextual discards in Layer 2 and active adversarial rejections in Layer 4.

2. **Corpus-Scale Architectural Verification ($N = 942$, `MockLLMClient`):**
   - **Engine:** Deterministic Python rule engine and heuristic parser (`MockLLMClient`, zero external API calls).
   - **Purpose:** Rigorous stress-testing of pipeline state sequence adherence (100.0%), Pydantic schema validation (0.0% format escapes), and deterministic syntactic defect distribution across the full corpus of 942 requirements.
   - **Heuristic Scorer Properties:** Produces zero-variance scores across Consistency (9.5), Correctness (9.5), and Conformance (9.0) because deterministic heuristics assign standard normative scores in the absence of explicit intra-document contradictions.
   - **Downstream Decisions:** Layer 5 sign-offs in this offline run are simulated (auto-acceptance upon successful Layer 4 validation).

3. **Comparative Baseline Omission:**
   - In accordance with rigorous evaluation standards, **all comparative claims against un-run or mismatched baseline models (e.g. GPT-4o) have been dropped**. Comparative benchmarks will be published only when both SQAM and baseline models are evaluated simultaneously under identical live experimental conditions.

---

## 2. Empirical Findings: Live Multi-Layer Evaluation ($N = 50$ Battery)

The 50-requirement battery sampled across all 15 projects was executed live against `gemini-3.5-flash-lite` through `scripts/run_pilot_evaluation.py`.

### 2.1 Live Pipeline Performance Summary

| Metric Dimension | Measured Live Value ($N = 50$) | Operational Definition / Pipeline Derivation |
| :--- | :---: | :--- |
| **Requirements Evaluated** | **50** | Stratified across all 15 industrial/academic SRS projects |
| **Live LLM Calls Executed** | **168** | Discrete remote inference requests across Layers 1–4 |
| **Pydantic Schema Failures** | **0 / 168 (0.0%)** | Strict structured JSON schema compliance |
| **Mean Quality Score ($Q_{\text{req}}$)** | **5.63 / 10.0** | Weighted aggregate score across 7 ISO dimensions (Eq. 1) |
| **Requirements Flagged in Layer 1** | **50 / 50 (100.0%)** | Requirements carrying $\ge 1$ shortcoming or attribute score $< 8.0$ |
| **Total Candidate Shortcomings** | **131** | Preliminary defects detected by Layer 1 Document Scorer |
| **Contextual False Positives Discarded (L2)**| **47 / 131** | Shortcomings eliminated by Layer 2 contextual domain reasoning |
| **Contextual Suppression Rate (CFSR)** | **35.9%** (47 / 131) | Rate of candidate false alarm filtering |
| **Requirements Cleared by Layer 2** | **14 / 50 (28.0%)** | Requirements where *all* candidate defects were dismissed |
| **Requirements Retained for Refinement** | **36 / 50 (72.0%)** | Requirements carrying confirmed, justified defects |
| **Surgical Refinements Generated (L3)** | **36** | Minimal diff rewrites produced by Layer 3 |
| **Refinements Validated by Critic (L4)** | **26 / 36 (72.2%)** | Approved by Layer 4 independent validator |
| **Refinements Rejected by Critic (L4)** | **10 / 36 (27.8%)** | Caught for hallucination, ambiguity, or unwarranted assumptions |
| **Refinement Rejection Rate (RRR)** | **27.8%** (10 / 36) | Active adversarial safety filter rate |

### 2.2 Live ISO/IEC/IEEE 29148 Attribute Breakdown ($N = 50$)

Under live model evaluation, draft requirements exhibit significant variance across quality dimensions:

| Quality Dimension | Paper Weight | Live Mean Score | Candidate Defects | Observed Real-World Defect Patterns |
| :--- | :---: | :---: | :---: | :--- |
| **Consistency** | 10% | **7.40** | 1 | High semantic alignment across document sections; isolated naming discrepancies |
| **Correctness** | 10% | **7.18** | 6 | Domain-specific term usage aligned with technical context |
| **Unambiguity** | 20% | **6.06** | 20 | Subjective qualifiers (*"quickly"*, *"high quality"*, *"intuitively"*) |
| **Singularity** | 10% | **5.54** | 32 | Compound sentence structures conjoining multiple obligations with *"and"* / *"as well as"* |
| **Verifiability / Feasibility**| 20% | **5.11** | 7 | Untestable acceptance criteria lacking objective pass/fail metrics |
| **Completeness** | 20% | **4.66** | 23 | Missing operational states, ungrounded conditional branches (*"if applicable"*), omitted error paths |
| **Conformance** | 10% | **4.54** | 42 | Widespread use of passive voice, missing normative modals (*"shall"* / *"must"*), missing explicit system subjects |
| **OVERALL ($Q_{\text{req}}$)** | **100%** | **5.63** | **131** | **Empirical draft quality reflecting real-world engineering specifications** |

> [!NOTE]
> **Key Finding from Live Inference:**
> The live empirical evaluation demonstrates that draft SRS specifications across industrial domains contain substantial conformance (42 defects) and completeness (23 defects) shortcomings.
> Layer 2 actively suppressed **35.9%** of candidate flags as contextual false alarms (e.g. recognizing domain-specific terms defined in specification glossaries), while Layer 4 rejected **27.8%** of proposed rewrites because the solution generator introduced ungrounded parameters or altered normative scope.

---

## 3. Corpus-Scale Pipeline Verification Benchmark ($N = 942$)

The full 942-requirement benchmark evaluates the deterministic pipeline orchestration, state transitions, and syntactic defect distribution across the entire corpus.

### 3.1 Verification Summary

| Metric Dimension | Full Benchmark Corpus ($N=942$) | Verification Role & Status |
| :--- | :---: | :--- |
| **Requirements Evaluated** | **942** | Complete normative corpus across 15 projects |
| **Document Files Sampled** | **46** (43 primary specs) | Exhaustive file set across project directories |
| **Mean Quality Score ($Q_{\text{req}}$)** | **9.06 / 10.0** | Deterministic baseline quality score (Eq. 1) |
| **Clean Compliant Pass Rate** | **89.1% (839 / 942)** | Normative statements meeting syntactic quality threshold |
| **Defect Flag Rate** | **10.9% (103 / 942)** | Requirements carrying $\ge 1$ syntax defect |
| **Total Defect Instances** | **106** | Syntactic defect instances identified |
| **Contextual Suppression Rate (CFSR)** | **11.3% (12 / 106)** | Deterministic glossary-based false alarm suppression |
| **Refinement Proposals (L3)** | **94** | Surgical rewrites generated for retained defects |
| **Refinement Rejection Rate (RRR)** | **6.4% (6 / 94)** | Rule-based rejection of invalid syntactic refinements |
| **Simulated Acceptance Rate (UAR)** | **93.2% (82 / 88)** | Simulated Layer 5 sign-offs (auto-accept on L4 pass) |
| **Pipeline Sequence Adherence** | **100.0% (942 / 942)** | Zero state transition or orchestration violations |
| **Format Escape Rate** | **0.0% (0 / 942)** | Zero JSON / Pydantic schema validation failures |

---

## 4. Project-by-Project Performance Breakdown (All 15 Projects)

The 942 requirements are distributed across 15 industrial and academic SRS projects:

| Project ID | Project Folder | Engineering Domain | Files Sampled | Total Reqs | Mean Score | Flagged Reqs | Clean Pass Rate |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | **1_FROG** | Gesture Recognition / Vision | 2 | 108 | **9.04** | 14 | 88.0% (95 clean) |
| **2** | **2_SMIRK** | Autonomous Driving ML Safety | 3$^\dagger$ | 12 | **9.10** | 0 | 100.0% (12 clean) |
| **3** | **3_ONEM** | IoT & Machine-to-Machine (oneM2M) | 5 | 74 | **9.06** | 7 | 90.5% (67 clean) |
| **4** | **4_UIC** | Railway Telecom (EIRENE Radio) | 5 | 142 | **9.00** | 34 | 76.8% (109 clean) |
| **5** | **5_EVLA** | Radio Astronomy Correlator Backend | 4$^\ddagger$ | 65 | **9.10** | 0 | 100.0% (65 clean) |
| **6** | **6** | Telecommunication Infrastructure (MEC) | 6 | 89 | **9.00** | 17 | 82.0% (73 clean) |
| **7** | **7** | Industrial Embedded Control | 2 | 44 | **9.10** | 0 | 100.0% (44 clean) |
| **8** | **8** | Embedded Robotic Actuation | 3 | 51 | **9.10** | 0 | 100.0% (51 clean) |
| **9** | **9** | Critical Real-Time Patient Monitoring | 2 | 38 | **9.06** | 4 | 89.5% (34 clean) |
| **10** | **10** | Spacecraft Avionics Subsystem | 2 | 58 | **9.07** | 3 | 94.8% (55 clean) |
| **11** | **11** | Medical Infusion Pump Firmware | 2 | 62 | **9.08** | 3 | 95.2% (59 clean) |
| **12** | **12** | Distributed Cyber-Physical Sensor Grid | 2 | 49 | **9.04** | 5 | 89.8% (44 clean) |
| **13** | **13** | Circular Economy Knowledge Graph (Onto) | 2 | 43$^*$ | **9.03** | 7 | 83.7% (36 clean) |
| **14** | **14** | Secure Network Boundary Gateway | 3 | 52$^*$ | **9.00** | 10 | 80.8% (42 clean) |
| **15** | **15** | Cloud Enterprise Data Platform | 3 | 55$^*$ | **9.06** | 2 | 96.4% (53 clean) |
| **TOTAL** | **Full Benchmark Corpus** | **10 Engineering Domains** | **46** | **942** | **9.06** | **106** | **89.1% (839 clean)** |

### Explanatory Notes on Document Versions & Requirement Allocations
- **$^\dagger$ Project 2 Versions:** Table 1 of the paper lists 2 primary specifications (`SRS (2).md` and `SRS (3).md`). The evaluation directory contains 3 files, including `Data Management Specification.md`. Omitting this auxiliary data management file yields the canonical 2 versions.
- **$^\ddagger$ Project 5 Versions:** Table 1 of the paper lists 2 versions (`be_srs.pdf` and `be_srs_2.1.pdf`). The directory holds 4 files including two subsystem annexes (`Corr_bkend_Req.pdf` and `Corr_bkend_Req_Soft.pdf`). Omitting these two annexes yields the canonical 2 versions.
- **Canonical Specification Versions:** $46 - 1 - 2 = \mathbf{43}$ primary SRS document versions.
- **$^*$ Reallocation of Projects 13–15 (33/41/76 $\rightarrow$ 43/52/55):**
  In the initial corpus design (Table 1), Projects 13, 14, and 15 were nominally assigned 33, 41, and 76 requirements respectively ($\sum = 150$). However, exhaustive parser extraction revealed that Project 15's three PDF files contains a total of only **61 extractable requirements**. Requesting 76 distinct requirements from Project 15 was physically impossible without synthetic duplication. To preserve the exact 942-requirement corpus total and avoid synthetic over-sampling, the 150-requirement pool across these three projects was reallocated to match actual document volume: Project 13 was allocated 43 (of 63 available), Project 14 was allocated 52 (of 234 available), and Project 15 was allocated 55 (of 61 available). $\mathbf{43 + 52 + 55 = 150}$.

---

## 5. Detailed Analysis of Case Studies & Failure Modes

### Case 1: Singularity Violation — Documented Failure Mode of Naive Replacement
- **Document Source:** `srs doc versions/1_FROG/SRS_v1.1.pdf` (Requirement: `1_FROG-REQ-001`)
- **Original Statement:**
  > *"Gestures are the entities which shall be modeled as well as recognized by the FROG project."*
- **Layer 1 Diagnosis:** Singularity score = 5.0. Conjunction `"as well as"` binds two distinct functional obligations (`modeled` and `recognized`).
- **Layer 3 Proposal:**
  > *"Gestures are the entities which shall be modeled and recognized by the FROG project."*
- **Word-Level Diff:** `[-as well as-] [+and+]`
- **Critical Failure Analysis:**
  Replacing `"as well as"` with `"and"` **does not remediate the singularity defect**. The sentence remains compound, assigning two distinct functional responsibilities to the system. Layer 4 erroneously marked this refinement as `VALIDATED`. This represents a **documented failure mode of naive lexical substitution**:
  - *Root Cause:* Layer 3 attempted an in-place string replacement rather than structural clause decomposition.
  - *Correct Engineering Remediation:* The requirement must be structurally split into two atomic requirements:
    - **REQ-001a:** *"The FROG project shall model continuous spatial-temporal hand gestures."*
    - **REQ-001b:** *"The FROG project shall recognize modeled hand gestures in real time."*

### Case 2: Vague UI Descriptor — Unambiguity & Verifiability Shortcoming
- **Document Source:** `srs doc versions/1_FROG/Software_Requirements_Specification_v30.pdf` (Requirement: `REQ-Software_Requirements_Specification_v30-012`)
- **Original Statement:**
  > *"The user interface shall be clean and intuitively labeled to promote a high quality look and feel."*
- **Layer 1 Diagnosis:** Overall Quality Score = 7.8 / 10.0. Flagged for:
  - *Unambiguity (7.8):* Descriptor `"intuitively labeled"` is subjective and context-dependent.
  - *Verifiability (7.8):* Descriptor `"high quality look and feel"` cannot be falsified by an automated or objective test suite.
- **Layer 3 Refinement (With Placeholder Annotation):**
  > *"The user interface shall conform to the navigation hierarchy defined in Section 3.2, with all interactive controls labeled using standard terminology from the FROG System Glossary [Placeholder: UI Standard Specification Reference Required]."*
- **Critical Parameterization Notice:**
  Any technical threshold or specification reference introduced into non-verifiable requirements **must be explicitly classified as a parameter placeholder requiring engineering stakeholder confirmation**, rather than assuming unverified operational domain boundaries.

---

## 6. Format & Pipeline Protocol Compliance

Systematic verification across both the live Gemini run and the full 942-requirement corpus yielded zero architectural or communication protocol failures:

| Metric | Measured Live ($N=50$) | Measured Corpus ($N=942$) | Standard Threshold | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Format Escapes** | **0 / 168 (0.0%)** | **0 / 942 (0.0%)** | 0.0% | **PASS** |
| **Pydantic Schema Violations** | **0 / 168 (0.0%)** | **0 / 942 (0.0%)** | 0.0% | **PASS** |
| **Pipeline Sequence Adherence** | **50 / 50 (100.0%)** | **942 / 942 (100.0%)** | 100.0% | **PASS** |
| **Average Layer 1 Latency** | **1.42 s / req** (remote API) | **0.82 ms / req** (local rule) | $< 5.0\text{ s}$ | **PASS** |

---

## 7. Data Provenance & Repository Cross-Reference

All evaluation datasets and reproduction artifacts are maintained in the following workspace locations:

1. **`results/raw/pilot_report.json`** — Machine-readable summary of the live Gemini 50-requirement empirical evaluation.
2. **`results/raw/pilot/*.json`** (50 files) — Checkpointed per-requirement JSON execution logs containing raw prompts, responses, token counts, latencies, and multi-layer structured outputs.
3. **`results/sqam_942_metrics_summary.json`** — Consolidated metrics compendium combining both live empirical evaluation and 942 corpus verification.
4. **`layer1_multi_project_evaluation_results.csv`** (428 KB) — Complete tabular dataset of the 942-requirement offline sweep.
5. **`layer1_deep_behaviour_log.csv`** (282 KB) — Sequence-level execution log of all 942 evaluations.
6. **`results/sample_manifest.json`** (487 KB) — Cryptographic SHA-256 manifest identifying all 942 requirements and the 50 pilot battery samples.
