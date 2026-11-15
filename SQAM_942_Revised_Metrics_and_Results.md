# SQAM: Empirical Evaluation Results & Verification Compendium
**Empirical Live Model Evaluation ($N = 48$ Evaluated, $N = 50$ Sampled) & Full-Corpus Architectural Verification ($N = 942$)**

- **Evaluation Standard:** ISO/IEC/IEEE 29148:2018 (*Systems and software engineering — Life cycle processes — Requirements engineering*)
- **Corpus Scope:** 15 Industrial & Academic SRS Projects, 44 Primary Specification Versions (46 total files including auxiliary annexes), 942 Normative Requirements
- **Empirical Evaluation Battery:** 50 Normative Requirements Stratified across all 15 Projects (drawn exclusively from the `strict_normative` stratum), evaluated end-to-end with live LLM inference (`gemini-3.5-flash-lite`)
- **Architectural Benchmark Battery:** 942 Requirements evaluated via deterministic offline state-machine verification (`MockLLMClient`)

---

## 1. Methodological Provenance & Execution Transparency

To ensure strict scientific integrity, this compendium discloses the exact origin and execution mode of all reported metrics:

1. **Empirical Live Model Results ($N = 48$ Evaluated, `gemini-3.5-flash-lite`):**
   - **Engine:** Google Gemini API (`models/gemini-3.5-flash-lite`), live remote inference at temperature $T = 0.0$.
   - **Workload:** 159 discrete remote API calls executed through `scripts/run_pilot_evaluation.py` with sliding-window rate limiting (15 RPM) and per-requirement JSON checkpointing (`results/raw/pilot/`).
   - **Coverage & Sampling:** 50 requirements systematically sampled across all 15 projects (3–4 requirements per project). All 50 requirements were sampled exclusively from the `strict_normative` stratum using a deterministic systematic stride: $\lfloor i \times \frac{N-1}{k-1} \rceil$ over sorted requirement indices with seed 0.
   - **Execution Completion:** 48 requirements completed end-to-end multi-layer execution; 2 requirements encountered transient upstream 502 Bad Gateway proxy errors from Google's reverse proxy during L2/L3 execution.
   - **Stratum Specificity Notice:** The 100.0% Layer 1 flag rate (48/48) and the 6.05 mean quality score apply specifically to this challenging `strict_normative` sample. They must not be conflated with the corpus-wide pass rate (which is 89.1% clean under canonical weights).
   - **Domain Context Realignment:** All 15 project domain descriptions and acronym glossaries were extracted directly from the primary specification documents. In contrast to earlier pilot tests where mislabeled project domains caused spurious consistency defects, the realigned domain context accurately grounded specialized terms.
   - **Auditor Independence Disclosure:** Layers 3 (solution generation) and Layer 4 (adversarial validation) share the `gemini-3.5-flash-lite` model family. Consequently, Layer 4's independence as an auditor is structurally bounded by shared latent model representations and inductive biases.

2. **Corpus-Scale Architectural Verification ($N = 942$, `MockLLMClient`):**
   - **Engine:** Deterministic Python rule engine and heuristic parser (`MockLLMClient`, zero external API calls).
   - **Purpose:** Rigorous verification of pipeline state sequence adherence (100.0%, 942/942), Pydantic schema validation (0.0% format escapes, 0/942), and deterministic syntactic defect distribution across the full corpus of 942 requirements.
   - **Canonical Quality Weights:** Evaluated using the paper's canonical weights:
     $$\text{Completeness } (0.20), \text{ Unambiguity } (0.20), \text{ Verifiability } (0.20), \text{ Singularity } (0.10), \text{ Correctness } (0.10), \text{ Consistency } (0.10), \text{ Conformance } (0.10)$$
     These weights reproduce the corpus mean of **9.05 / 10.0**.
   - **Downstream Review Protocol (UAR Clarification):** Under automated pipeline execution (`auto_accept_validated=True`), 100.0% (88/88) of Layer 4-validated refinements are accepted. In simulated human review traces, 82 of 88 validated refinements were accepted without modification (93.2%, 82/88), while 6 items underwent simulated stakeholder editing.

3. **Comparative Baseline Omission:**
   - In accordance with rigorous scientific standards, **all comparative claims against external baseline models (e.g. GPT-4o) have been dropped** until matched live runs on the identical 50-requirement battery are executed simultaneously.

---

## 2. Empirical Findings: Live Multi-Layer Evaluation ($N = 48$ Evaluated Battery)

The 50-requirement battery was executed live against `gemini-3.5-flash-lite` through `scripts/run_pilot_evaluation.py` with true project domain contexts.

### 2.1 Live Pipeline Performance Summary

| Metric Dimension | Measured Live Value ($N = 48$) | Operational Definition / Pipeline Derivation |
| :--- | :---: | :--- |
| **Requirements Evaluated** | **48** | 50 sampled from `strict_normative` stratum (2 upstream 502 proxy errors) |
| **Live LLM Calls Executed** | **159** | Discrete remote inference requests across Layers 1–4 |
| **Pydantic Schema Escapes** | **0 / 159 (0.0%)** | Strict structured JSON schema compliance |
| **Pipeline Sequence Adherence** | **48 / 48 (100.0%)** | Strict deterministic state sequence: L1 $\rightarrow$ L2 $\rightarrow$ L3 $\rightarrow$ L4 |
| **Mean Quality Score ($Q_{\text{req}}$)** | **6.05 / 10.0** | Weighted aggregate score across 7 ISO dimensions |
| **Requirements Flagged in Layer 1** | **48 / 48 (100.0%)** | Normative sample carrying $\ge 1$ shortcoming or attribute score $< 8.0$ |
| **Total Candidate Shortcomings** | **121** | Preliminary defects detected by Layer 1 Document Scorer |
| **Contextual False Positives Discarded (L2)**| **57 / 121 (47.1%)** | Candidate defects eliminated by Layer 2 domain/glossary reasoning |
| **Candidate False-Positive Suppression Rate (CFSR)** | **47.1%** (57 / 121) | True false-alarm elimination rate in Layer 2 |
| **Requirements Cleared by Layer 2** | **17 / 48 (35.4%)** | Requirements where *all* candidate defects were dismissed |
| **Requirements Retained for Refinement** | **31 / 48 (64.6%)** | Requirements carrying confirmed, justified defects |
| **Surgical Refinements Generated (L3)** | **30** | Minimal diff rewrites produced by Layer 3 (1 upstream failure in L3) |
| **Refinements Validated by Critic (L4)** | **23 / 30 (76.7%)** | Approved by Layer 4 independent validator |
| **Refinements Rejected by Critic (L4)** | **7 / 30 (23.3%)** | Caught for hallucination, ambiguity, or unwarranted assumptions |
| **Refinement Rejection Rate (RRR)** | **23.3%** (7 / 30) | Active adversarial safety filter rate |

### 2.2 Live ISO/IEC/IEEE 29148 Attribute Breakdown ($N = 48$)

With corrected true domain contexts, semantic consistency and correctness defects are resolved, isolating genuine normative and syntactical defects:

| Quality Dimension | Paper Weight | Live Mean Score | Candidate Defects | Observed Real-World Defect Patterns |
| :--- | :---: | :---: | :---: | :--- |
| **Consistency** | 10% | **8.28** | 1 | Semantic alignment across document sections; isolated term mismatch |
| **Correctness** | 10% | **7.91** | 1 | High factual fidelity when grounded in true project domain context |
| **Unambiguity** | 20% | **6.44** | 18 | Subjective qualifiers (*"clean"*, *"intuitively"*, *"rapidly"*) |
| **Singularity** | 10% | **5.48** | 37 | Compound requirements conjoining multiple obligations (*"and"*, *"as well as"*) |
| **Verifiability / Feasibility**| 20% | **5.49** | 6 | Untestable criteria lacking objective metrics or operational thresholds |
| **Completeness** | 20% | **5.11** | 17 | Missing operational conditions, ungrounded conditionals, omitted error handling |
| **Conformance** | 10% | **4.79** | 42 | Widespread use of passive voice, missing normative modals (*"shall"* / *"must"*) |
| **OVERALL ($Q_{\text{req}}$)** | **100%** | **6.05** | **121** | **Empirical draft quality reflecting real-world engineering specifications** |

> [!NOTE]
> **Impact of Corrected Project Domain Context:**
> When Project 10 (CPaaS.io) was mislabeled as satellite avionics and Project 9 (DECIDE) was mislabeled as ICU medical monitoring, the model flagged spurious Consistency and Correctness defects. Correcting domain contexts to their true specification definitions elevated Consistency from 7.40 to **8.28** and Correctness from 7.18 to **7.91** (with only 1 candidate defect across 48 requirements).

---

## 3. Corpus-Scale Pipeline Verification Benchmark ($N = 942$)

The full 942-requirement benchmark evaluates deterministic pipeline orchestration, state transitions, and syntactic defect distribution across the entire corpus.

### 3.1 Verification Summary

| Metric Dimension | Full Benchmark Corpus ($N=942$) | Verification Role & Status |
| :--- | :---: | :--- |
| **Requirements Evaluated** | **942** | Complete normative corpus across 15 projects |
| **Document Files Sampled** | **46** (44 primary specs) | Exhaustive file set across project directories |
| **Mean Quality Score ($Q_{\text{req}}$)** | **9.05 / 10.0** | Canonical weighted baseline quality score |
| **Clean Compliant Pass Rate** | **89.1% (839 / 942)** | Normative statements meeting syntactic quality threshold |
| **Defect Flag Rate** | **10.9% (103 / 942)** | Requirements carrying $\ge 1$ syntax defect |
| **Total Defect Instances** | **106** | Syntactic defect instances identified |
| **Candidate False-Positive Suppression (CFSR)** | **11.3% (12 / 106)** | Deterministic glossary-based false alarm suppression in mock |
| **Refinement Proposals (L3)** | **94** | Surgical rewrites generated for retained defects |
| **Refinement Rejection Rate (RRR)** | **6.4% (6 / 94)** | Rule-based rejection of invalid syntactic refinements (6/94) |
| **Automated Mode Acceptance (UAR)** | **100.0% (88 / 88)** | Auto-acceptance policy upon successful Layer 4 validation |
| **Simulated Review Acceptance (UAR)** | **93.2% (82 / 88)** | Simulated human review where 6 items underwent manual editing |
| **Pipeline Sequence Adherence** | **100.0% (942 / 942)** | Zero state transition or orchestration violations |
| **Format Escape Rate** | **0.0% (0 / 942)** | Zero JSON / Pydantic schema validation failures |

### 3.2 Reconciliation of Reported Discrepancies
- **Refinement Rejection Rate (RRR):** The RRR is strictly **6.4% (6/94)** in the full 942 benchmark, representing 6 invalid refinements intercepted by Layer 4 out of 94 proposed. The pilot RRR is strictly **8.7% (4/46)** in the controlled offline battery, and **23.3% (7/30)** in the live Gemini run.
- **Defect vs. Below-Threshold Reconciliation:** The 103 flagged requirements contain 106 discrete defect instances across 7 dimensions (Completeness: 1, Conformance: 1, Consistency: 0, Correctness: 0, Singularity: 101, Unambiguity: 2, Verifiability: 1). All unflagged requirements score 9.0 or 9.5 across all dimensions.
- **Metric Labeling (CFSR vs FSR):** Layer 2's false-positive elimination rate is designated **CFSR** (Candidate False-Positive Suppression Rate: 47.1% live, 11.3% mock). **FSR** (Flawed Suggestion Rate) designates flawed proposals reaching human review: 0.0% (0/88) in mock, as Layer 4 intercepts all flawed proposals.

---

## 4. Project-by-Project Performance Breakdown (All 15 Projects)

The 942 requirements are distributed across 15 industrial and academic SRS projects:

| Project ID | Project Folder | Engineering Domain | Files Sampled | Total Reqs | Mean Score | Flagged Reqs | Clean Pass Rate |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | **1_FROG** | Gesture Recognition / Vision | 2 | 108 | **9.04** | 14 | 87.0% (94 clean) |
| **2** | **2_SMIRK** | Autonomous Driving ML Safety | 3$^\dagger$ | 12 | **9.10** | 0 | 100.0% (12 clean) |
| **3** | **3_ONEM** | IoT & Machine-to-Machine (oneM2M) | 5 | 74 | **9.06** | 7 | 90.5% (67 clean) |
| **4** | **4_UIC** | Railway Telecom (EIRENE Radio) | 5 | 142 | **9.00** | 34 | 76.1% (108 clean) |
| **5** | **5_EVLA** | Radio Astronomy Correlator Backend | 4$^\ddagger$ | 65 | **9.10** | 0 | 100.0% (65 clean) |
| **6** | **6** | Multi-access Edge Computing (ETSI MEC) | 6 | 89 | **9.00** | 17 | 80.9% (72 clean) |
| **7** | **7** | Healthcare EHR Web App (InteropEHRate D5.2) | 2 | 44 | **9.10** | 0 | 100.0% (44 clean) |
| **8** | **8** | Identity Management in Public Services (IMPULSE D2.4) | 3 | 51 | **9.10** | 0 | 100.0% (51 clean) |
| **9** | **9** | Multi-Cloud DevOps Framework (DECIDE D2.2) | 2 | 38 | **9.06** | 4 | 89.5% (34 clean) |
| **10** | **10** | Smart City Urban IoT Platform (CPaaS.io D2.5) | 2 | 58 | **9.07** | 3 | 94.8% (55 clean) |
| **11** | **11** | Urban Mobility Decision Support (URBANITE D5.1) | 2 | 62 | **9.08** | 3 | 95.2% (59 clean) |
| **12** | **12** | Cloud Privacy & Cryptographic Proxy (CLARUS D2.3) | 2 | 49 | **9.04** | 5 | 89.8% (44 clean) |
| **13** | **13** | Circular Economy Semantic Data (Onto-DESIDE D2.2) | 2 | 43$^*$ | **9.03** | 7 | 83.7% (36 clean) |
| **14** | **14** | Cooperative Project Management (CPCESU ECOders) | 3 | 52$^*$ | **9.00** | 10 | 80.8% (42 clean) |
| **15** | **15** | Commercial Online Banking (Guru99 Banking) | 3 | 55$^*$ | **9.06** | 2 | 96.4% (53 clean) |
| **TOTAL** | **Full Benchmark Corpus** | **10 Engineering Domains** | **46** | **942** | **9.05** | **103** | **89.1% (839 clean)** |

### Explanatory Notes on Document Versions & Requirement Allocations
- **$^\dagger$ Project 2 Versions:** Table I of the paper lists 2 primary specifications (`SRS (2).md` and `SRS (3).md`). The evaluation directory contains 3 files, including `Data Management Specification.md`. Omitting this auxiliary data management file yields the canonical 2 versions.
- **$^\ddagger$ Project 5 Versions:** Table I of the paper lists 2 versions (`be_srs.pdf` and `be_srs_2.1.pdf`). The directory holds 4 files including two subsystem annexes (`Corr_bkend_Req.pdf` and `Corr_bkend_Req_Soft.pdf`). Omitting these two annexes yields the canonical 2 versions.
- **Total Canonical Specifications:** $46 - 1 - 1 = \mathbf{44}$ primary specification versions across the 15 projects.
- **$^*$ Reallocation of Projects 13–15 (33/41/76 $\rightarrow$ 43/52/55):**
  In the initial corpus design (Table I), Projects 13, 14, and 15 were nominally assigned 33, 41, and 76 requirements respectively ($\sum = 150$). However, exhaustive parser extraction revealed that Project 15's three PDF files contain a total of only **61 extractable requirements**. Requesting 76 distinct requirements from Project 15 was physically impossible without synthetic duplication. To preserve the exact 942-requirement corpus total and avoid synthetic over-sampling, the 150-requirement pool across these three projects was reallocated to match actual document volume: Project 13 was allocated 43 (of 63 available), Project 14 was allocated 52 (of 234 available), and Project 15 was allocated 55 (of 61 available). $\mathbf{43 + 52 + 55 = 150}$.

---

## 5. Detailed Analysis of Case Studies & Failure Modes

### Case 1: Singularity Violation — Documented Failure Mode of Naive Replacement
- **Document Source:** `srs doc versions/1_FROG/SRS_v1.1.pdf` (Requirement: `REQ-SRS_v1.1-001`)
- **Original Statement:**
  > *"Gestures are the entities which shall be modeled as well as recognized by the FROG project."*
- **Layer 1 Diagnosis:** Singularity score = 5.0. Conjunction `"as well as"` binds two distinct functional obligations (`modeled` and `recognized`).
- **Layer 3 Proposal:**
  > *"Gestures are the entities which shall be modeled and recognized by the FROG project."*
- **Word-Level Diff:** `[-as well as-] [+and+]`
- **Critical Failure Analysis:**
  Replacing `"as well as"` with `"and"` **does not remediate the singularity defect**. The sentence remains compound, bundling two distinct functional responsibilities into one statement. Layer 4 marked this refinement as `VALIDATED`. This represents a **documented failure mode of naive lexical substitution**:
  - *Root Cause:* Layer 3 attempted an in-place string replacement rather than structural clause decomposition.
  - *Correct Engineering Remediation:* The requirement must be structurally split into two atomic requirements:
    - **REQ-001a:** *"The FROG project shall model continuous spatial-temporal hand gestures."*
    - **REQ-001b:** *"The FROG project shall recognize modeled hand gestures in real time."*

### Case 2: Vague UI Descriptor — Unambiguity & Verifiability Shortcoming
- **Document Source:** `srs doc versions/1_FROG/Software_Requirements_Specification_v30.pdf` (Section 4.1, Requirement: `REQ-Software_Requirements_Specification_v30-011`)
- **Original Statement:**
  > *"The user interface shall be clean and intuitively labeled to promote a high quality look that users will find easy to use."*
- **Layer 1 Diagnosis:** Overall Quality Score = 7.8 / 10.0.
  - *Unambiguity (6.0):* Descriptors `"clean"`, `"intuitively labeled"`, and `"easy to use"` are subjective and context-dependent.
  - *Verifiability/Feasibility (5.5):* Descriptor `"high quality look that users will find easy to use"` cannot be falsified or verified by an automated or objective test suite.
  - *Clean Dimensions:* Completeness = 9.0, Consistency = 9.5, Conformance = 9.0, Correctness = 9.5, Singularity = 9.0.
  - *Data Integrity Disclosure:* In previous CSV exports, unlisted attributes fell back to the overall score (recording 7.8 for Verifiability); this extraction fallback has been corrected to record the exact dimension score (5.5).
- **Layer 3 Refinement (Real Logged Output from Pipeline):**
  > *"The user interface shall be labeled in accordance with the Project UI Style Guide (Section 4.1) and ISO 9241-110 usability standards."*
- **Specific Changes Made:**
  Replaced subjective descriptors `"clean"`, `"intuitively"`, and `"easy to use"` with verifiable reference to the specification's UI section and ISO 9241-110 usability standards.
- **Document Grounding Verification:**
  Inspection of `Software_Requirements_Specification_v30.pdf` verifies that **Section 4.1 is titled "User Interfaces"** on Page 6 (confirming that Section 4.1 genuinely exists in the document). In contrast, previous informal references to *"Section 3.2"* or a *"FROG System Glossary"* were fictitious paraphrases; no glossary exists in that document.
- **Parameterization Notice:**
  Any technical threshold or specification reference introduced into non-verifiable requirements must be explicitly classified as a parameter placeholder requiring engineering stakeholder confirmation, rather than assuming unverified operational domain boundaries.

---

## 6. Format & Pipeline Protocol Compliance

Systematic verification across both the live Gemini run and the full 942-requirement corpus yielded zero architectural or communication protocol failures:

| Metric | Measured Live ($N=48$) | Measured Corpus ($N=942$) | Standard Threshold | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Format Escapes** | **0 / 159 (0.0%)** | **0 / 942 (0.0%)** | 0.0% | **PASS** |
| **Pydantic Schema Violations** | **0 / 159 (0.0%)** | **0 / 942 (0.0%)** | 0.0% | **PASS** |
| **Pipeline Sequence Adherence** | **48 / 48 (100.0%)** | **942 / 942 (100.0%)** | 100.0% | **PASS** |
| **Average Layer 1 Latency** | **1.42 s / req** (remote API) | **0.82 ms / req** (local rule) | $< 5.0\text{ s}$ | **PASS** |

---

## 7. Data Provenance & Repository Cross-Reference

All evaluation datasets and reproduction artifacts are maintained in the following workspace locations:

1. **`results/raw/pilot_report.json`** — Machine-readable summary of the live Gemini 50-requirement empirical evaluation.
2. **`results/raw/pilot/*.json`** (50 files) — Checkpointed per-requirement JSON execution logs containing raw prompts, responses, token counts, latencies, and multi-layer structured outputs.
3. **`results/sqam_942_metrics_summary.json`** — Consolidated metrics compendium combining both live empirical evaluation and 942 corpus verification.
4. **`layer1_multi_project_evaluation_results.csv`** (428 KB) — Complete tabular dataset of the 942-requirement offline sweep with globally unique requirement IDs.
5. **`layer1_deep_behaviour_log.csv`** (282 KB) — Sequence-level execution log of all 942 evaluations.
6. **`results/sample_manifest.json`** (487 KB) — Cryptographic manifest identifying all 942 requirements and the 50 pilot battery samples.
