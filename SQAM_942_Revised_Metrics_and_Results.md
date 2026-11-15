# SQAM: Empirical Evaluation Results & Verification Compendium
**Empirical Live Model Evaluation ($N = 50$ Fully Evaluated) & Full-Corpus Architectural Verification ($N = 942$)**

- **Evaluation Standard:** ISO/IEC/IEEE 29148:2018 (*Systems and software engineering — Life cycle processes — Requirements engineering*)
- **Corpus Scope:** 15 Industrial & Academic SRS Projects, 43 Primary Specification Documents (46 total document files evaluated in dataset including 3 auxiliary annexes), 942 Normative Requirements
- **Empirical Evaluation Battery:** 50 Normative Requirements Stratified across all 15 Projects (sampled strictly from the `strict_normative` stratum), evaluated end-to-end with live LLM inference (`gemini-3.5-flash-lite`)
- **Architectural Benchmark Battery:** 942 Requirements evaluated via deterministic offline state-machine verification (`MockLLMClient`)

---

## 1. Methodological Provenance & Execution Transparency

To ensure strict scientific integrity, this compendium discloses the exact origin and execution mode of all reported metrics:

1. **Empirical Live Model Results ($N = 50$, `gemini-3.5-flash-lite`):**
   - **Engine:** Google Gemini API (`models/gemini-3.5-flash-lite`), live remote inference at temperature $T = 0.0$.
   - **Workload:** 165 discrete remote API calls executed through `scripts/run_pilot_evaluation.py` with sliding-window rate limiting (15 RPM) and per-requirement JSON checkpointing (`results/raw/pilot/`).
   - **Sampling & Stratum Specificity:** 50 requirements systematically sampled across all 15 projects (3–4 requirements per project). All 50 requirements were sampled strictly from the `strict_normative` stratum using a deterministic systematic stride: $\lfloor i \times \frac{N-1}{k-1} \rceil$ over sorted requirement indices with seed 0.
   - **Execution Completion:** Exactly 50 of 50 requirements completed end-to-end multi-layer execution with zero schema escapes or unhandled exceptions (100.0% completion). The two requirements that encountered transient upstream HTTP 502 Bad Gateway proxy errors during initial execution (`REQ-Attachment_0 (3)-037` and `REQ-Attachment_0 (1)-092`) were re-run to completion under identical model, temperature, and checkpointing conditions.
   - **Stratum Specificity Notice:** The 100.0% Layer 1 flag rate (50/50) and the 6.11 mean quality score apply specifically to this challenging `strict_normative` sample. They must not be conflated with the corpus-wide pass rate (which is 89.1% clean under canonical weights).
   - **Domain Context Realignment:** All 15 project domain descriptions and acronym glossaries were extracted directly from the primary specification documents, eliminating false-alarm Consistency and Correctness defects.
   - **Auditor Independence Disclosure:** Layers 3 (solution generation) and Layer 4 (adversarial validation) share the `gemini-3.5-flash-lite` model family. Consequently, Layer 4's independence as an auditor is structurally bounded by shared latent model representations and inductive biases.

2. **Corpus-Scale Architectural Verification ($N = 942$, `MockLLMClient`):**
   - **Engine:** Deterministic Python rule engine and heuristic parser (`MockLLMClient`, zero external API calls).
   - **Purpose:** Rigorous verification of pipeline state sequence adherence (100.0%, 942/942), Pydantic schema validation (0.0% format escapes, 0/942), and deterministic syntactic defect distribution across the full corpus of 942 requirements.
   - **Canonical Quality Weights:** Evaluated using the paper's canonical weights:
     $$\text{Completeness } (0.20), \text{ Unambiguity } (0.20), \text{ Verifiability } (0.20), \text{ Singularity } (0.10), \text{ Correctness } (0.10), \text{ Consistency } (0.10), \text{ Conformance } (0.10)$$
     These weights reproduce the corpus mean of **9.05 / 10.0**.
   - **Automated Sign-Off Policy:** The pipeline implements automated acceptance (`auto_accept_validated=True`). Out of 94 refinements generated, Layer 4 validated 88 and rejected 6. All 88 validated proposals were accepted (88/88, 100.0%). No speculative manual review or simulated adjustment rules are claimed; only the computed pipeline behavior is reported.

3. **Comparative Baseline Omission:**
   - In accordance with rigorous scientific standards, **all comparative claims against external baseline models (e.g. GPT-4o) have been dropped** until matched live runs on the identical 50-requirement battery are executed simultaneously.

---

## 2. Empirical Findings: Live Multi-Layer Evaluation ($N = 50$ Battery)

The complete 50-requirement battery was executed live against `gemini-3.5-flash-lite` through `scripts/run_pilot_evaluation.py` with true project domain contexts.

### 2.1 Live Pipeline Performance Summary

| Metric Dimension | Measured Live Value ($N = 50$) | Operational Definition / Pipeline Derivation |
| :--- | :---: | :--- |
| **Requirements Evaluated** | **50 / 50 (100.0%)** | Stratified across all 15 industrial/academic SRS projects |
| **Live LLM Calls Executed** | **165** | Discrete remote inference requests across Layers 1–4 |
| **Pydantic Schema Escapes** | **0 / 165 (0.0%)** | Strict structured JSON schema compliance |
| **Pipeline Sequence Adherence** | **50 / 50 (100.0%)** | Strict deterministic state sequence: L1 $\rightarrow$ L2 $\rightarrow$ L3 $\rightarrow$ L4 |
| **Mean Quality Score ($Q_{\text{req}}$)** | **6.11 / 10.0** | Weighted aggregate score across 7 ISO dimensions |
| **Requirements Flagged in Layer 1** | **50 / 50 (100.0%)** | Normative sample carrying $\ge 1$ shortcoming or attribute score $< 8.0$ |
| **Total Candidate Shortcomings** | **125** | Preliminary defects detected by Layer 1 Document Scorer |
| **Contextual False Positives Discarded (L2)**| **59 / 125 (47.2%)** | Candidate defects eliminated by Layer 2 domain/glossary reasoning |
| **Candidate False-Positive Suppression Rate (CFSR)** | **47.2%** (59 / 125) | True false-alarm elimination rate in Layer 2 |
| **Requirements Cleared Entirely by Layer 2** | **19 / 50 (38.0%)** | Requirements where *all* candidate defects were dismissed |
| **Requirements Retained for Refinement** | **31 / 50 (62.0%)** | Requirements carrying confirmed, justified defects |
| **Surgical Refinements Generated (L3)** | **31 / 31 (100.0%)** | Minimal diff rewrites produced by Layer 3 |
| **Refinements Evaluated by Critic (L4)** | **31 / 31 (100.0%)** | Independent adversarial validation gate |
| **Refinements Validated by Critic (L4)** | **24 / 31 (77.4%)** | Approved by Layer 4 independent validator |
| **Refinements Rejected by Critic (L4)** | **7 / 31 (22.6%)** | Intercepted for hallucination, ambiguity, or unwarranted assumptions |
| **Refinement Rejection Rate (RRR)** | **22.6%** (7 / 31) | Active adversarial safety filter rate |

### Reconciliation of Funnel Counts
Every stage of the live funnel adds up with complete mathematical consistency:
$$\text{Evaluated (50)} = \text{Cleared by L2 (19)} + \text{Retained by L2 (31)}$$
$$\text{Retained by L2 (31)} = \text{Proposed by L3 (31)} = \text{Evaluated by L4 (31)}$$
$$\text{Evaluated by L4 (31)} = \text{Validated by L4 (24)} + \text{Rejected by L4 (7)} = 31$$
$$\text{Candidate Defects (125)} = \text{Retained Defects (66)} + \text{Discarded False Positives (59)} = 125$$

> **Resolution of the Previous Missing Refinement:**  
> In the intermediate checkpoint, 31 requirements were retained by Layer 2 but only 30 were recorded at Layer 4. The single missing requirement was `REQ-Attachment_0 (3)-037` (Project 11), which had passed Layer 2 but encountered an upstream HTTP 502 proxy error during its initial Layer 3 invocation. Re-running `REQ-Attachment_0 (3)-037` produced a valid Layer 3 refinement that was successfully validated by Layer 4, reconciling the counts to exactly 31 proposed, 24 validated, and 7 rejected ($24 + 7 = 31$).

### 2.2 Live ISO/IEC/IEEE 29148 Attribute Breakdown ($N = 50$)

With corrected true domain contexts, semantic consistency and correctness defects are resolved, isolating genuine normative and syntactical defects:

| Quality Dimension | Paper Weight | Live Mean Score | Candidate Defects | Observed Real-World Defect Patterns |
| :--- | :---: | :---: | :---: | :--- |
| **Consistency** | 10% | **8.30** | 0 retained (1 flag) | High semantic alignment across document sections; 0 confirmed defects |
| **Correctness** | 10% | **7.96** | 0 retained (1 flag) | High factual fidelity when grounded in true project domain context |
| **Unambiguity** | 20% | **6.51** | 18 | Subjective qualifiers (*"clean"*, *"intuitively"*, *"rapidly"*, *"market ready"*) |
| **Singularity** | 10% | **5.49** | 38 | Compound requirements conjoining multiple obligations (*"and"*, *"as well as"*) |
| **Verifiability / Feasibility**| 20% | **5.56** | 6 | Untestable criteria lacking objective metrics or operational thresholds |
| **Completeness** | 20% | **5.18** | 18 | Missing operational conditions, ungrounded conditionals, omitted error handling |
| **Conformance** | 10% | **4.84** | 44 | Widespread use of passive voice, missing normative modals (*"shall"* / *"must"*) |
| **OVERALL ($Q_{\text{req}}$)** | **100%** | **6.11** | **125** | **Empirical draft quality reflecting real-world engineering specifications** |

---

## 3. Corpus-Scale Pipeline Verification Benchmark ($N = 942$)

The full 942-requirement benchmark evaluates deterministic pipeline orchestration, state transitions, and syntactic defect distribution across the entire corpus.

### 3.1 Verification Summary

| Metric Dimension | Full Benchmark Corpus ($N=942$) | Verification Role & Status |
| :--- | :---: | :--- |
| **Requirements Evaluated** | **942** | Complete normative corpus across 15 projects |
| **Primary Specifications Covered** | **43** (46 files in dataset) | Exhaustive file set across project directories |
| **Mean Quality Score ($Q_{\text{req}}$)** | **9.05 / 10.0** | Canonical weighted baseline quality score |
| **Clean Compliant Pass Rate** | **89.1% (839 / 942)** | Normative statements meeting syntactic quality threshold |
| **Defect Flag Rate** | **10.9% (103 / 942)** | Requirements carrying $\ge 1$ syntax defect |
| **Total Defect Instances** | **106** | Discrete syntactic defect instances across 103 flagged requirements |
| **Contextual Suppression Rate (CFSR)** | **8.7% (9 / 103 reqs)** | 9 requirements (12 defect instances, 11.3%) dismissed in mock |
| **Refinement Proposals (L3)** | **94** | Surgical rewrites generated for retained defects |
| **Refinement Rejection Rate (RRR)** | **6.4% (6 / 94)** | Rule-based rejection of invalid syntactic refinements |
| **Automated Mode Acceptance** | **100.0% (88 / 88)** | Auto-acceptance policy upon successful Layer 4 validation |
| **Pipeline Sequence Adherence** | **100.0% (942 / 942)** | Zero state transition or orchestration violations |
| **Format Escape Rate** | **0.0% (0 / 942)** | Zero JSON / Pydantic schema validation failures |

### 3.2 942 Dimension Score and Defect Accounting Reconciliation
The 942 evaluation dataset (`layer1_multi_project_evaluation_results.csv`) exhibits the following precise distribution across all seven dimensions:

| Quality Dimension | Canonical Weight | Corpus Mean | Minimum | Below 8.0 Count | Defect Tally | Scoring Behavior in Rule Engine |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Completeness** | 20% | **8.94** | 5.5 | 15 | 15 | Lowered by open conditionals (*"if applicable"* / *"etc."*) |
| **Unambiguity** | 20% | **8.98** | 5.5 | 6 | 6 | Lowered by subjective adverbs (*"quickly"*, *"intuitive"*) |
| **Verifiability** | 20% | **8.98** | 5.5 | 6 | 1 | Evaluated per ISO 29148 testability (see explanation below) |
| **Singularity** | 10% | **8.64** | 5.0 | 84 | 84 | Lowered by compound conjunctions (*"as well as"*, multi-shall) |
| **Correctness** | 10% | **9.50** | 9.5 | 0 | 0 | Default normative standard in absence of semantic contradiction |
| **Consistency** | 10% | **9.50** | 9.5 | 0 | 0 | Default normative standard in absence of intra-document clash |
| **Conformance** | 10% | **9.00** | 9.0 | 0 | 0 | Default normative standard for extracted normative clauses |
| **OVERALL** | **100%** | **9.05** | **6.25** | **103** | **106** | **Reproduces canonical corpus mean of 9.05 / 10.0** |

#### Verifiability Scorer Behavior Disclosure
In `layer1_multi_project_evaluation_results.csv`, Unambiguity and Verifiability have nearly identical means (8.9798 vs 8.9819, both rounding to 8.98) and both have 6 requirements scoring below 8.0:
1. In `MockLLMClient`, when subjective adverbs such as *"quickly"* (unbounded time) or *"intuitive"* (subjective UX) are detected, both Unambiguity and Verifiability scores are lowered (e.g. Unambiguity to 5.5/6.0 and Verifiability to 6.0/6.5), because subjective adverbs inherently degrade objective testability.
2. However, for 5 of those 6 requirements, the primary shortcoming was categorized under `Unambiguity` (e.g. *"Subjective adverb lacks quantifiable bounds"*).
3. Exactly 1 requirement (`REQ-Software_Requirements_Specification_v30-011`, containing *"easy to use"*) had its primary shortcoming categorized under `Verifiability/Feasibility`.
4. Therefore, the defect tally records 1 Verifiability defect and 6 Unambiguity defects, while the score distribution records 6 requirements scoring below 8.0 on both dimensions.

---

## 4. Primary Document Versions Breakdown (All 15 Projects)

The benchmark corpus encompasses **43 primary software requirements specifications** (46 total document files evaluated in the dataset):

| Project ID | Project Folder | Engineering Domain | Primary Specifications (File Names) | Primary Count | Total Files in Dataset |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **1** | **1_FROG** | Gesture Recognition / Vision | `SRS_v1.1.pdf`, `Software_Requirements_Specification_v30.pdf` | **2** | 2 |
| **2** | **2_SMIRK** | Autonomous Driving ML Safety | `System Requirements Specification (2).md`, `System Requirements Specification (3).md` | **2** | 3$^\dagger$ |
| **3** | **3_ONEM** | IoT & Machine-to-Machine (oneM2M) | `TS-0002-Requirements-V1_0_1.DOC.pdf`, `TS-0002-Requirements-V2_10_2.DOCX.pdf`, `TS-0002-Requirements-V3_1_2.DOCX.pdf`, `TS-0002-Requirements-V4_1_0(cl).pdf`, `TS-0002-Requirements-V5_1_0_CL.pdf` | **5** | 5 |
| **4** | **4_UIC** | Railway Telecom (EIRENE Radio) | `eirene_-_system_requirements_specification_-_version_16.1_0.pdf`, `eirene_srs_15.1.pdf`, `eirene_srs_v15.pdf`, `p0028d004.3-15.3.0.pdf`, `srs-16.0.0_uic_951-0.0.2_final.pdf` | **5** | 5 |
| **5** | **5_EVLA** | Radio Astronomy Correlator Backend | `be_srs.pdf`, `be_srs_2.1.pdf` | **2** | 4$^\ddagger$ |
| **6** | **6** | Multi-access Edge Computing (MEC) | `gs_mec002v010101p.pdf`, `gs_mec002v020201p.pdf`, `gs_mec002v030101p.pdf`, `gs_mec002v030201p.pdf`, `gs_mec002v040101p.pdf`, `gs_mec002v040201p.pdf` | **6** | 6 |
| **7** | **7** | Healthcare EHR Web App (InteropEHRate) | `Attachment_0 (1).pdf`, `Attachment_0.pdf` | **2** | 2 |
| **8** | **8** | Identity Management in Public Services (IMPULSE) | `Attachment_0 (1).pdf`, `Attachment_0 (2).pdf`, `Attachment_0.pdf` | **3** | 3 |
| **9** | **9** | Multi-Cloud DevOps Framework (DECIDE) | `Attachment_0 (1).pdf`, `Attachment_0.pdf` | **2** | 2 |
| **10** | **10** | Smart City Urban IoT Platform (CPaaS.io) | `Attachment_0 (1).pdf`, `Attachment_0.pdf` | **2** | 2 |
| **11** | **11** | Urban Mobility Decision Support (URBANITE) | `Attachment_0 (2).pdf`, `Attachment_0 (3).pdf` | **2** | 2 |
| **12** | **12** | Cloud Privacy & Cryptographic Proxy (CLARUS) | `Attachment_0 (1).pdf`, `Attachment_0.pdf` | **2** | 2 |
| **13** | **13** | Circular Economy Semantic Data (Onto-DESIDE) | `Attachment_0 (2).pdf`, `Attachment_0 (3).pdf` | **2** | 2 |
| **14** | **14** | Cooperative Project Management (CPCESU) | `1.pdf`, `2.pdf`, `3.pdf` | **3** | 3 |
| **15** | **15** | Commercial Online Banking (Guru99 Banking) | `SRS_v1.pdf`, `SRS_v2.pdf`, `SRS_v3.pdf` | **3** | 3 |
| **TOTAL** | **15 Projects** | **10 Engineering Domains** | **Canonical Primary Specification Documents** | **43** | **46** |

### Explanatory Notes on Auxiliary Files & Requirement Allocations
- **$^\dagger$ Project 2 Auxiliary File:** The repository directory contains 3 files. `Data Management Specification.md` is an auxiliary data management specification rather than a primary system requirement specification. Excluding it yields the canonical 2 primary versions.
- **$^\ddagger$ Project 5 Auxiliary Files:** The directory contains 4 files. `Corr_bkend_Req.pdf` and `Corr_bkend_Req_Soft.pdf` are subsystem hardware/software annexes to the backend correlator. Excluding these 2 annexes yields the canonical 2 primary versions.
- **Primary Specifications Sum:** $46 - 1 - 2 = \mathbf{43}$ primary specification documents.
- **Reallocation of Projects 13–15 (33/41/76 $\rightarrow$ 43/52/55):**  
  Exhaustive parser extraction revealed that Project 15's three PDF files contain a total of 61 extractable requirements. Requesting 76 requirements from Project 15 was impossible without synthetic duplication. To preserve the exact 942-requirement corpus total without synthetic over-sampling, the 150-requirement pool was reallocated according to document volume: Project 13 was allocated 43 (of 63 available), Project 14 was allocated 52 (of 234 available), and Project 15 was allocated 55 (of 61 available). $\mathbf{43 + 52 + 55 = 150}$.

---

## 5. Case Studies: Grounded in Verified Execution Logs

### Case 1: Illustrative Analysis — Singularity Violation and Decomposition
*(Note: Labelled as an illustrative analysis of naive lexical substitution versus atomic decomposition; not a direct pipeline output).*
- **Document Source:** `srs doc versions/1_FROG/SRS_v1.1.pdf` (Requirement: `REQ-SRS_v1.1-001`)
- **Original Statement:**
  > *"Gestures are the entities which shall be modeled as well as recognized by the FROG project."*
- **Defect Mechanism:** The conjunction `"as well as"` binds two distinct functional obligations (`modeled` and `recognized`).
- **Naive Replacement:**
  > *"Gestures are the entities which shall be modeled and recognized by the FROG project."*
- **Engineering Failure Analysis:** Replacing `"as well as"` with `"and"` leaves the requirement compound. The correct remediation requires structural decomposition into two atomic requirements:
  - **REQ-001a:** *"The FROG project shall model continuous spatial-temporal hand gestures."*
  - **REQ-001b:** *"The FROG project shall recognize modeled hand gestures in real time."*

---

### Case 2: Real Logged Pipeline Execution — EARS Phrasing & False Positive Dismissal
*(Exact logged execution record from `results/raw/pilot/1_FROG_REQ-SRS_v1.1-052.json`).*
- **Requirement ID:** `REQ-SRS_v1.1-052`
- **Project & Source:** `1_FROG` (`SRS_v1.1.pdf`, Section: Functional Specifications)
- **Original Text:**
  > *"User(s) follow the on-screen instructions and must make use of gestures to “win” the game"*
- **Layer 1 Diagnostic Output:**
  - *Overall Quality Score:* **6.35 / 10.0**
  - *Dimension Scores:* Unambiguity: 6.0, Completeness: 5.5, Consistency: 8.5, Conformance: 5.0, Correctness: 8.0, Singularity: 6.0, Verifiability/Feasibility: 6.5.
  - *Identified Shortcomings:*
    - `DEF-1` (Conformance): *"User(s) follow the on-screen instructions and must make use of"* (lacks mandatory normative modal 'shall').
    - `DEF-2` (Singularity): *"follow the on-screen instructions and must make use of gestures"* (couples reading instructions with performing gestures).
    - `DEF-3` (Unambiguity): *"“win” the game"* (subjective term lacking testable pass/fail criteria).
- **Layer 2 Contextual Reasoning (CFSR in Action):**
  - `DEF-1` (Conformance): **JUSTIFIED** (confidence 0.98; fails IEEE 29148 modal verb rule).
  - `DEF-2` (Singularity): **DISCARDED** (confidence 0.90; *"The flagging of singularity is overly pedantic. Reading instructions and executing the corresponding gestures are inextricably linked parts of a single unified user interaction loop within a gesture recognition game, rather than two distinct functional requirements."*)
  - `DEF-3` (Unambiguity): **JUSTIFIED** (confidence 0.95; *"The term 'win' is enclosed in quotes and lacks clear, measurable boundary conditions, score thresholds, or completion states."*)
- **Layer 3 Refinement Proposal (Exact Logged Text):**
  > *"When following on-screen instructions, the FROG system shall require user(s) to execute gestures to achieve the defined game completion condition."*
- **Layer 3 Changes Made:**
  1. Applied EARS event-driven syntax (`"When..., the FROG system shall..."`) to introduce mandatory modal verb 'shall'.
  2. Replaced subjective term `"“win”"` with precise, testable phrase `"achieve the defined game completion condition"`.
- **Word-Level Diff:**
  `[-User(s) follow-] [+When following+] on-screen instructions[- and must make use of-][+, the FROG system shall require user(s) to execute+] gestures to [-"win"-] [+achieve the defined game completion condition+] [-the game-]`
- **Layer 4 Adversarial Validation (Exact Logged Output):**
  - *Verdict:* **`validated`** (`is_valid: true`)
  - *Checks:* Defect Resolution: PASSED; No New Ambiguities: PASSED; No Unwarranted Assumptions: PASSED; Functional Intent Preservation: PASSED; Syntactic Conformance: PASSED.
  - *Critic Feedback:* *"The proposed refinement successfully addresses all identified defects from Layer 2. It introduces the mandatory modal verb 'shall' using standard EARS format, and properly replaces the subjective term 'win' with a testable, objective phrase ('achieve the defined game completion condition') without over-specifying implementation details or altering the functional scope of the system."*

---

### Case 3: Real Logged Pipeline Execution — Adversarial Rejection of Unwarranted Assumptions
*(Exact logged execution record from `results/raw/pilot/10_REQ-Attachment_0__1_-063.json`).*
- **Requirement ID:** `REQ-Attachment_0 (1)-063`
- **Project & Source:** `10` (CPaaS.io, `Attachment_0 (1).pdf`)
- **Original Text:**
  > *"Done for the currently available data sources. he data from various data sources must be integrated and offered in a uniform manner."*
- **Layer 1 Diagnostic Output:**
  - *Overall Quality Score:* **6.75 / 10.0**
  - *Shortcomings:* Past-tense status note (`"Done for..."`), non-normative modal (`"must be"`), vague phrasing (`"uniform manner"`).
- **Layer 3 Refinement Proposal:**
  > *"The CPaaS.io platform shall integrate data from various data sources and offer the integrated data via uniform data schemas and standard APIs."*
- **Layer 4 Adversarial Validation (Exact Logged Output):**
  - *Verdict:* **`rejected`** (`is_valid: false`)
  - *Check 3 (No Unwarranted Assumptions):* **FAILED**
  - *Critic Feedback:* *"While the refinement successfully eliminates the non-actionable status text and properly utilizes the 'shall' operator, it over-corrects the ambiguity defect by injecting specific technical mechanisms ('uniform data schemas and standard APIs'). In requirement engineering, defining 'standard APIs' without specifying which standards (e.g., OGC, REST/JSON) constitutes an unwarranted technical assumption and shifts the requirement from a functional need to an under-specified design constraint. The refinement must resolve the ambiguity without inventing specific implementation details."*
- **Operational Significance:** Demonstrates the fail-closed adversarial safety gate actively intercepting unwarranted technical assumptions before stakeholder exposure (contributing to the 22.6% RRR).

---

## 6. Format & Pipeline Protocol Compliance

Systematic verification across both the live Gemini run and the full 942-requirement corpus yielded zero architectural or communication protocol failures:

| Metric | Measured Live ($N=50$) | Measured Corpus ($N=942$) | Standard Threshold | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Format Escapes** | **0 / 165 (0.0%)** | **0 / 942 (0.0%)** | 0.0% | **PASS** |
| **Pydantic Schema Violations** | **0 / 165 (0.0%)** | **0 / 942 (0.0%)** | 0.0% | **PASS** |
| **Pipeline Sequence Adherence** | **50 / 50 (100.0%)** | **942 / 942 (100.0%)** | 100.0% | **PASS** |
| **Average Layer 1 Latency** | **1.42 s / req** (remote API) | **0.82 ms / req** (local rule) | $< 5.0\text{ s}$ | **PASS** |

---

## 7. Data Provenance & Repository Cross-Reference

All evaluation datasets and reproduction artifacts are maintained in the following workspace locations:

1. **`results/raw/pilot_report.json`** — Machine-readable summary of the live Gemini 50-requirement empirical evaluation ($N=50$).
2. **`results/raw/pilot/*.json`** (50 files) — Checkpointed per-requirement JSON execution logs containing raw prompts, responses, token counts, latencies, and multi-layer structured outputs.
3. **`results/sqam_942_metrics_summary.json`** — Consolidated metrics compendium combining both live empirical evaluation ($N=50$) and 942 corpus verification.
4. **`layer1_multi_project_evaluation_results.csv`** (428 KB) — Complete tabular dataset of the 942-requirement offline sweep with globally unique requirement IDs.
5. **`layer1_deep_behaviour_log.csv`** (282 KB) — Sequence-level execution log of all 942 evaluations.
6. **`results/sample_manifest.json`** (487 KB) — Cryptographic manifest identifying all 942 requirements and the 50 pilot battery samples.
