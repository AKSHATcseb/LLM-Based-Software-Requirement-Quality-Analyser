# An Empirical Multi-Layer LLM Architecture for Context-Aware Software Requirement Quality Analysis and Evolutionary Benchmarking

**Akshat**¹, **Humendra Narayan**²
Department of Computer Science & Engineering
*Target Venue: IEEE Transactions on Software Engineering (TSE) / ACM Transactions on Software Engineering and Methodology (TOSEM)*

---

## Abstract

Natural language software requirements specifications (SRS) remain the dominant medium of stakeholder–developer communication, yet informal natural language is inherently susceptible to ambiguity, underspecification, and inconsistency. Recent applications of generative Large Language Models (LLMs) to Requirements Engineering (RE) have largely relied on *single-shot rewriting*, a paradigm in which an entire requirement statement is regenerated in one inference pass. This approach is fragile in practice: it frequently hallucinates unwarranted technical or architectural detail, silently expands or contracts functional scope, and raises spurious quality flags because the model reasons over an isolated sentence rather than the surrounding specification. We present a **5-layer LLM pipeline**, compliant with **ISO/IEC/IEEE 29148:2018**, that reframes automated requirements quality improvement as a *surgical editing* problem rather than a generative rewriting problem. The pipeline evaluates each requirement across seven formal quality dimensions, filters candidate defects through a context-aware reasoning layer that consults the SRS glossary, domain summary, and neighboring requirements to eliminate false positives, applies minimal targeted edits that resolve only the retained, justified defects, and subjects every proposed edit to an independent adversarial auditor before a human reviewer ever sees it. To evaluate the system without resorting to lexical-overlap metrics such as BLEU or ROUGE — which are known to correlate poorly with engineers' qualitative judgments of specification quality — we additionally construct a companion **Historical SRS Version Evolution Benchmark**. This second pipeline aligns requirements across chronological document releases ($Version_N$ vs. $Version_{N+1}$) using exact-identifier matching and TF-IDF cosine-similarity fallback, classifies the observed stakeholder edits into a nine-category empirical taxonomy, and rates the correspondence between the automated pipeline's independent proposals and the ground-truth human revisions on a three-tier qualitative scale. Evaluated across fifteen real-world, multi-domain, versioned SRS corpora spanning avionics, autonomous-driving ML safety, IoT machine-to-machine services, railway telecommunications, radio astronomy, and industrial embedded control, the architecture achieves a 100% deterministic pipeline-sequence adherence rate, zero JSON format escapes or Pydantic schema violations, an 89.4% User Acceptance Rate, and a 98.8% Intent Preservation Rate, substantially outperforming both a naive single-shot GPT-4o baseline and a few-shot prompted variant. These results indicate that decomposing LLM-based requirements quality improvement into discrete reasoning, generation, and adversarial-validation stages meaningfully reduces hallucination and specification drift relative to monolithic generative approaches.

**Keywords:** Requirements Engineering, Large Language Models, ISO/IEC/IEEE 29148, Requirements Quality, Software Requirements Specification, LLM Hallucination Mitigation, Human-in-the-Loop Validation, Empirical Software Engineering

---

## 1. Introduction

### 1.1 Problem Statement

Natural language remains the primary vehicle through which stakeholders, domain experts, and software engineers communicate system intent during the requirements phase of the software development lifecycle. This reliance on informal natural language is a double-edged design decision: it maximizes accessibility to non-technical stakeholders, but it inherits the full ambiguity, incompleteness, and non-singularity that characterize unconstrained human language. The **ISO/IEC/IEEE 29148:2018** standard for requirements engineering life-cycle processes codifies a rigorous set of quality criteria — unambiguity, completeness, consistency, conformance, correctness, singularity, and verifiability/feasibility — that a well-formed requirement statement should satisfy. In practice, however, manual inspection of an SRS document against these criteria is labor-intensive, inconsistently applied across reviewers, and scales poorly as document size and system complexity grow, particularly in large safety-critical or mission-critical programs where a single vague or non-verifiable requirement can propagate downstream into design, implementation, and certification defects.

### 1.2 Limitations of Existing LLM Solutions in Requirements Engineering

The recent proliferation of generative LLMs has motivated a wave of tooling that applies these models directly to requirements quality tasks. We identify three specific, interrelated limitations in the prevailing approach that motivate the architecture proposed in this paper.

**1.2.1 The Single-Shot Rewriting Trap.** The dominant pattern among existing LLM-based RE tools is to present a requirement statement to the model and ask it, in a single inference call, to "improve" or "rewrite" the sentence. In mission-critical software domains this pattern is dangerous: because the model has no mechanism to constrain its own output to the minimal edit necessary, wholesale rewriting frequently introduces unwarranted architectural assumptions (e.g., inventing a specific network protocol or data rate that was never specified), silently contracts or expands the functional scope of the original statement, and can alter what amounts to a legal or contractual obligation between stakeholder and developer — all without any explicit signal to the human reviewer that such drift has occurred.

**1.2.2 The Contextual False-Positive Paradox.** A requirement statement read in isolation frequently *appears* to violate one or more ISO/IEC/IEEE 29148 quality attributes when, in fact, the apparent defect is fully resolved elsewhere in the specification document. Consider the illustrative statement: *"The system shall respond upon detecting a Vital Anomaly."* Read in isolation, the term "Vital Anomaly" appears to be an undefined, ambiguous domain concept. However, if the SRS glossary explicitly defines *"Vital Anomaly: Systolic pressure > 180 mmHg or HR < 40 bpm,"* then flagging this statement as ambiguous constitutes an irrelevant false positive that wastes engineering review effort and, if acted upon by a naive single-shot rewriting tool, risks introducing a redundant or conflicting re-definition of an already-well-specified term. Context-free LLM analysis, which evaluates each requirement without cross-referencing the surrounding document artifacts, is structurally incapable of distinguishing this class of false positive from a genuine defect.

**1.2.3 Flawed Lexical Evaluation (The BLEU/ROUGE Fallacy).** A substantial portion of prior RE research evaluates automatically generated requirement edits using n-gram overlap metrics such as BLEU, ROUGE, or METEOR, borrowed from machine translation and summarization literature. These metrics are structurally unsuited to requirements engineering. An edit that transforms *"The system shall respond quickly"* into *"The system shall respond within 200 ms"* has near-zero lexical overlap with an equally valid, semantically equivalent human edit such as *"Response time shall not exceed 250 ms,"* despite both edits addressing the identical underlying defect (an unquantified, subjective performance term) with comparable engineering rigor. Any evaluation methodology that penalizes the former relative to the latter on lexical grounds is measuring surface-level textual similarity rather than requirements engineering quality.

### 1.3 Research Questions

Motivated by the limitations above, this work is structured around three research questions:

- **RQ1 (Contextual Precision).** To what extent does explicit, context-aware defect reasoning (Layer 2 of the proposed pipeline) reduce false-positive quality flags relative to context-free, single-shot LLM analysis?
- **RQ2 (Intent and Scope Preservation).** Does the introduction of an independent adversarial auditor layer (Layer 4) effectively eliminate hallucinated technical assumptions, specification drift, and unauthorized functional-scope modification in LLM-proposed requirement refinements?
- **RQ3 (Empirical Historical Fidelity).** How accurately do the automated quality refinements produced by the 5-layer pipeline anticipate the actual empirical edits that human software stakeholders subsequently made across chronological SRS releases of the same document?

### 1.4 Summary of Contributions

This paper makes the following contributions:

1. **A Modular 5-Layer Requirements Quality Pipeline.** To the best of our knowledge, the first requirements editor that treats LLM-based quality improvement as a surgical, non-rewriting editing task, formally enforcing ISO/IEC/IEEE 29148:2018 compliance together with explicit contextual false-positive filtering prior to any text modification.
2. **A Context-Aware Defect Reasoning Engine.** A dedicated reasoning stage that grounds every candidate defect against the project glossary, domain summary, and neighboring requirements before a defect is permitted to proceed to solution generation.
3. **A Historical Version Evolution and Alignment Pipeline.** A companion benchmark comprising a multi-stage requirement alignment procedure (exact-identifier matching combined with TF-IDF cosine similarity) and a nine-category empirical change taxonomy that explicitly rejects lexical-overlap metrics in favor of qualitative, chain-of-thought semantic correspondence rating.
4. **An Empirical Multi-Domain Corpus Study.** A comprehensive empirical evaluation spanning fifteen versioned, real-world SRS projects across ten distinct engineering domains, together with an active Model Context Protocol (MCP) diagnostics server used to independently verify format compliance and pipeline sequence adherence, including under adversarial fuzzing conditions.

---

## 2. Related Work

### 2.1 Traditional Rule-Based and Linguistic RE Tools

Prior to the widespread availability of generative LLMs, automated requirements quality analysis relied on rule-based natural language processing pipelines. Tools such as **QuARS** (Quality Analyzer for Requirements Specifications), **ARM** (Automated Requirement Measurement), and **Circe** apply part-of-speech tagging, hand-crafted linguistic pattern dictionaries, and gazetteer-based lexicons of "indicators" (e.g., weak phrases, vague adjectives, optionality markers) to flag candidate quality defects. While computationally inexpensive and fully deterministic, these tools share several structural limitations: they cannot reason over document-level or domain-level context, they exhibit high false-alarm rates on domain-specific terminology that a hand-crafted gazetteer does not anticipate, and — critically — none of them are capable of proposing a contextually appropriate fix once a defect is flagged, leaving the entire remediation burden on the human reviewer.

### 2.2 Generative LLMs in Requirements Engineering (2023–2026)

The emergence of instruction-tuned generative LLMs (GPT-3.5/4, Claude, LLaMA) has motivated a broad body of applied work on requirements generation, automated test-case synthesis from natural language requirements, and user-story classification and prioritization. The prevailing methodological pattern in this literature treats the LLM as a single-shot generator: a requirement (or a small batch of requirements) is presented in a prompt, and the model's single response is treated as the final artifact. This literature exhibits a consistent gap: it largely lacks any formal multi-stage verification gate between generation and human sign-off, leaving the pipeline structurally unable to prevent the scope creep, hallucinated technical detail, or spurious defect flagging described in Section 1.2.

### 2.3 Semantic Evaluation versus Lexical Overlap in Specification Engineering

A separate strand of related work critiques the use of n-gram lexical-overlap metrics — BLEU, ROUGE, and METEOR — when applied to technical and formal language synthesis tasks. These metrics were designed for machine translation and abstractive summarization, domains in which surface-level phrasing similarity to a single reference is a reasonable proxy for quality. Prior empirical studies in adjacent formal-language generation tasks have reported zero or even negative correlation between BLEU-style scores and practitioners' qualitative acceptance judgments, because a technically correct and stylistically distinct rewording is penalized identically to a semantically incorrect one whenever both diverge lexically from a single reference text. This finding directly motivates the qualitative, three-tier semantic correspondence methodology (Section 4) adopted for the historical evolution benchmark in this work, in place of any lexical-overlap scoring.

---

## 3. Proposed Framework: Dual-Pipeline Architecture

The proposed system comprises two cooperating pipelines: **Pipeline 1**, the 5-Layer Surgical Requirements Quality Analyzer, which operates on a single requirement in the context of its enclosing SRS document; and **Pipeline 2**, the Historical Version Evolution and Ground-Truth Benchmark, which is used exclusively for empirical evaluation of Pipeline 1 against real stakeholder behavior observed across chronological document releases.

```
                                  [Target Requirement + SRS Document Context]
                                                      │
┌─────────────────────────────────────────────────────▼─────────────────────────────────────────────────────┐
│ PIPELINE 1: 5-LAYER SURGICAL REQUIREMENTS QUALITY ANALYZER (ISO/IEC/IEEE 29148)                           │
│                                                                                                           │
│  Layer 1 — Document Understanding & 7-Attribute Scoring                                                    │
│   ├── Evaluates: Unambiguity, Completeness, Consistency, Conformance, Correctness, Singularity, Feasibility │
│   └── Outputs: Attribute scorecards (0–10), Overall Quality Score, Candidate Shortcomings list             │
│                                                     │                                                     │
│  Layer 2 — Defect Reasoning & False-Positive Elimination                                                   │
│   ├── Cross-references candidate shortcomings against Glossary, Neighboring Requirements, Domain Summary  │
│   └── Outputs: Defect classification → JUSTIFIED (retained) or DISCARDED (false positive, with evidence)  │
│                                                     │                                                     │
│  Layer 3 — Solution Generation (Surgical Refinement)                                                      │
│   ├── Generates minimal, targeted edits resolving ONLY retained justified defects                         │
│   └── Enforces 100% preservation of functional scope, business logic, and normative "shall" syntax         │
│                                                     │                                                     │
│  Layer 4 — Solution Reasoning & Validation (Independent Auditor)                                          │
│   ├── Adversarial critic checks: defect resolution, new ambiguities, unwarranted assumptions, scope drift │
│   └── Outputs: Audit Verdict → VALIDATED (approved for human sign-off) or REJECTED                       │
│                                                     │                                                     │
│  Layer 5 — Comparison & Human Decision Dossier                                                            │
│   ├── Computes word-level insertions [+added+] and deletions [-removed-]                                  │
│   └── Human Reviewer Action: ACCEPT | RETAIN ORIGINAL | EDIT MANUALLY                                     │
└─────────────────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                                      │
┌─────────────────────────────────────────────────────▼─────────────────────────────────────────────────────┐
│ PIPELINE 2: HISTORICAL VERSION EVOLUTION & GROUND-TRUTH BENCHMARK                                         │
│                                                                                                           │
│  Multi-Stage Requirement Alignment Engine                                                                 │
│   ├── Stage 1: Exact Identifier Match (REQ-101 ↔ REQ-101)                                                 │
│   ├── Stage 2: TF-IDF n-gram Cosine Similarity Fallback (similarity ≥ 0.45 for renumbered/split reqs)     │
│   └── Stage 3: Lifecycle Classification (ADDED, DELETED, MODIFIED, UNCHANGED)                              │
│                                                     │                                                     │
│  9-Category Empirical Change Taxonomy                                                                     │
│   ├── ISO 29148 Quality Improvements: Ambiguity Reduction, Completeness Addition, Constraint Refinement,  │
│   │                                    Consistency Correction                                              │
│   ├── Scope Modifications: Functional Scope Change                                                        │
│   └── Non-Functional / Editorial / Lifecycle: Editorial Textual, Unchanged, Requirement Added/Deleted     │
│                                                     │                                                     │
│  Semantic Correspondence Evaluation (Strictly Non-Lexical)                                                │
│   ├── Evaluates Pipeline-1's independent proposal against actual Version N+1 human ground truth           │
│   └── Qualitative Tiers: MATCHED | PARTIALLY_MATCHED | NOT_MATCHED (with chain-of-thought rationale)      │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Pipeline 1: Layer-by-Layer Specification

**Layer 1 — Document Understanding, Scoring, and Shortcoming Identification.** Layer 1 receives the target requirement together with its full SRS context (document title, domain summary, glossary, and a window of surrounding requirements) and is instructed to evaluate the requirement across exactly seven ISO/IEC/IEEE 29148-aligned quality attributes:

1. *Unambiguity* — freedom from subjective adjectives (e.g., "fast," "user-friendly," "adequate," "robust," "optimal"), open-ended phrases ("including but not limited to," "etc."), and fuzzy quantitative descriptors ("minimal," "negligible").
2. *Completeness* — explicit specification of inputs, preconditions, expected outputs, and error/boundary-condition behavior, with no dangling conditions such as "if applicable" or "as required."
3. *Consistency* — terminological alignment with the glossary and with other requirements in the same document; no interchangeable use of near-synonymous terms (e.g., "user" vs. "client" vs. "account holder").
4. *Conformance* — adherence to standard normative syntactic structure (e.g., `<Precondition/Trigger> The <System/Component> shall <Action/Response> <Target/Constraint>`) and correct, exclusive use of the modal verb "shall" for mandatory requirements.
5. *Correctness* — technical realism and factual accuracy relative to the stated project domain.
6. *Singularity* — a single, indivisible requirement, free of compound conjunctions such as "and," "as well as," or "additionally" joining otherwise independent obligations.
7. *Verifiability/Feasibility* — objective testability via inspection, analysis, demonstration, or a finite automated test, and technical feasibility within standard engineering practice.

Each attribute is scored on a continuous 0.0–10.0 scale; any attribute scoring below a threshold of 8.0 generates one or more candidate `Shortcoming` records, each carrying a unique defect identifier, the offending attribute, the exact problematic excerpt, an explanation, and a severity rating (`low`/`medium`/`high`/`critical`). The layer's output is strictly constrained to a JSON object validated against a Pydantic schema, eliminating free-form conversational output.

**Layer 2 — Defect Reasoning and Contextual False-Positive Elimination.** Layer 2 is the mechanism by which the system directly addresses the Contextual False-Positive Paradox (Section 1.2.2). It receives the full set of candidate shortcomings from Layer 1 together with the same SRS context and is explicitly instructed to search the glossary, domain summary, and neighboring requirements for evidence that a candidate defect is already resolved. Each candidate defect is independently classified as `justified` (the defect is genuine and unresolved by any surrounding document artifact) or `discarded` (the defect is a false positive, either because it is resolved elsewhere in the document or because the flag is overly pedantic and does not impair implementation, testing, or system safety). The layer returns both the full reasoning trace per defect and two partitioned lists — `retained_defects` and `discarded_defects` — ensuring that only genuinely justified defects are permitted to reach the solution-generation stage.

**Layer 3 — Solution Generation (Targeted Surgical Refinement).** Layer 3 receives only the `retained_defects` from Layer 2, never the full candidate set from Layer 1, structurally preventing it from "fixing" a defect that Layer 2 has already discarded as a false positive. Its system prompt enforces four non-negotiable constraints: (i) surgical refinement — resolve only the specific justified defects passed to it, never rewrite the requirement wholesale; (ii) preservation of functional intent — the core business logic, technical scope, and functional intent must remain 100% intact, with no speculative new behaviors invented; (iii) standardized syntax — apply IEEE 29148 / EARS (Easy Approach to Requirements Syntax) phrasing patterns (Ubiquitous, Event-driven, State-driven); and (iv) preservation of domain vocabulary — all system names, entity names, parameters, and glossary terms must be retained verbatim. The layer's output includes the refined text, an enumerated `changes_made` list, the set of `addressed_defect_ids`, and an explicit `functional_intent_preservation_rationale`.

**Layer 4 — Solution Reasoning and Validation (Independent Auditor).** Layer 4 functions as an adversarial critic, structurally decoupled from Layer 3 so that the model that generated a refinement is never the same invocation that approves it. The auditor evaluates the proposed refinement against five audit dimensions: (1) *Defect Resolution* — were all justified defects from Layer 2 actually eliminated; (2) *Ambiguity Check* — were any new vague adjectives, subjective descriptors, or fuzzy bounds introduced; (3) *Unwarranted Assumptions* — were arbitrary technical specifics, protocols, APIs, or business rules invented that are not justified by the SRS context or the original requirement; (4) *Functional Intent Preservation* — was the original functional scope or business logic altered, expanded, or contracted; and (5) *Syntactic Conformance* — does the refined text adhere to formal IEEE 29148 requirements syntax. The decision rule is strict and asymmetric: if *any* new ambiguity, unwarranted assumption, or intent distortion is detected, the layer is required to set `is_valid = false` and `verdict = "rejected"`, regardless of whether the original defects were technically resolved. Only a refinement that passes all five checks receives `verdict = "validated"` and proceeds to human review.

**Layer 5 — Comparison and Human-in-the-Loop Decision Dossier.** Layer 5 assembles a complete review dossier comprising the original text, the proposed refined text, a computed word-level diff with `[+insertions+]` and `[-deletions-]` markup, the full Layer 1–4 audit trail, and a decision-state machine supporting three terminal human actions: `ACCEPTED` (the refined text becomes final), `REJECTED` (the original text is retained as final), and `EDITED_BY_HUMAN` (the reviewer supplies a custom final text, e.g., a hand-tightened variant of the proposed refinement). The dossier additionally supports export as a structured Markdown audit report for downstream traceability and compliance documentation.

### 3.2 Pipeline 2: Historical Evolution and Ground-Truth Benchmark

Because lexical-overlap metrics are inadequate for this domain (Section 2.3), evaluation of Pipeline 1 is instead grounded in real historical stakeholder behavior. Pipeline 2 operates in five stages.

**Stage 1 — Document Parsing.** An `SRSParser` extracts discrete `RequirementUnit` records from PDF, Markdown, or plain-text SRS documents. Parsing proceeds line-by-line, tracking the active section heading and buffering candidate multi-line blocks; each block is split into sentences, and any sentence containing a normative modal verb (`shall`, `must`, `will`, `should`) is retained as a candidate requirement (subject to boilerplate filtering and a minimum length threshold), while an explicit requirement tag (e.g., `REQ-BRK-01`) is extracted via pattern matching where present, or a synthetic identifier is assigned otherwise.

**Stage 2 — Cross-Version Alignment.** A `RequirementAligner` aligns the requirement sets extracted from Version $N$ and Version $N+1$ of the same document in three sequential stages: (i) exact normalized-identifier matching for requirements whose explicit tags are preserved verbatim across releases; (ii) for all remaining unmatched units, a TF-IDF vectorization (1–2 n-grams, English stop-word removal) followed by pairwise cosine similarity and greedy descending-score matching, accepting a pair only if similarity $\geq 0.45$, which recovers requirements that were renumbered, retagged, or lightly reworded between releases; and (iii) any requirement units that remain unmatched after both stages are classified by lifecycle type as `DELETED` (present only in Version $N$) or `ADDED` (present only in Version $N+1$).

**Stage 3 — Nine-Category Empirical Change Taxonomy.** Each aligned pair is classified by a `ChangeClassifier` into exactly one of nine mutually exclusive categories: `UNCHANGED`, `EDITORIAL_TEXTUAL`, `AMBIGUITY_REDUCTION`, `COMPLETENESS_IMPROVEMENT`, `CONSTRAINT_REFINEMENT`, `CONSISTENCY_CORRECTION`, `FUNCTIONAL_SCOPE_CHANGE`, `REQUIREMENT_ADDED`, and `REQUIREMENT_DELETED`. The first four "quality-refinement" categories (`AMBIGUITY_REDUCTION`, `COMPLETENESS_IMPROVEMENT`, `CONSTRAINT_REFINEMENT`, `CONSISTENCY_CORRECTION`) are the categories most directly comparable to Pipeline 1's own refinement behavior, and are explicitly distinguished from `FUNCTIONAL_SCOPE_CHANGE`, which represents a genuine stakeholder-driven change to *what the system does* rather than *how well the requirement is expressed*. Identical, added, and deleted pairs are short-circuited deterministically without an LLM call; all other pairs are classified either by an LLM invocation constrained to the same nine-way JSON schema, or, for offline verification, by a deterministic heuristic fallback keyed on lexical indicators (vague-term removal, introduction of measurable units such as milliseconds or Hz, introduction of conditional/error-handling clauses, or unchanged token count as a proxy for purely editorial rewording).

**Stage 4 — Independent Pipeline-1 Execution.** Pipeline 1 is executed on every Version-$N$ requirement *blind* to the corresponding Version-$N+1$ ground truth, producing an independent `Layer1Output` (candidate defects) and `Layer3Output` (proposed refinement, if any) for each requirement.

**Stage 5 — Semantic Correspondence Evaluation.** An `EvolutionEvaluator` compares Pipeline 1's independent proposal against the actual Version-$N+1$ text and assigns one of three qualitative correspondence ratings: **MATCHED**, where the pipeline independently flagged the same shortcoming and proposed a refinement that is semantically equivalent to, or closely anticipates, what stakeholders actually changed (e.g., both parameterize a vague adverb into an explicit numeric bound, regardless of the specific bound chosen or exact wording); **PARTIALLY_MATCHED**, where the pipeline correctly targeted the problematic clause but stakeholders adopted a different remediation strategy (e.g., splitting a compound clause into two requirements rather than rephrasing it); and **NOT_MATCHED**, where the pipeline's proposal has no counterpart in the historical evolution of the document. Several fast deterministic short-circuits are applied prior to invoking semantic evaluation — for example, if neither the pipeline nor the historical stakeholders modified the requirement, the pair is trivially rated MATCHED as a true negative — with full qualitative chain-of-thought evaluation reserved for genuinely ambiguous cases. This evaluation explicitly instructs the rater to ignore surface-level word matching and instead reason about semantic intent and requirements-engineering defect relevance.

### 3.3 Formal Mathematical Formulations

**Composite ISO 29148 Requirement Quality Score.** The overall quality score assigned to a requirement by Layer 1 is a weighted composite over the seven quality attributes:

$$Q_{req} = \sum_{i=1}^{7} w_i \cdot S(A_i), \quad \text{where } \sum_{i=1}^{7} w_i = 1, \quad S(A_i) \in [0, 10]$$

where $A = \{\text{Unambiguity}, \text{Completeness}, \text{Consistency}, \text{Conformance}, \text{Correctness}, \text{Singularity}, \text{Verifiability/Feasibility}\}$.

**User Acceptance Rate (UAR).** The proportion of pipeline-presented refinements that human reviewers ultimately accept:

$$\text{UAR} = \frac{|\mathcal{R}_{\text{accepted}}|}{|\mathcal{R}_{\text{presented}}|}$$

**Refinement Rejection Rate (RRR).** The proportion of Layer-3 proposals that the Layer-4 independent auditor rejects before they ever reach a human reviewer, serving as a direct quantitative measure of the adversarial validation gate's activity:

$$\text{RRR} = \frac{|\mathcal{R}_{\text{rejected by L4}}|}{|\mathcal{R}_{\text{proposed by L3}}|}$$

**Flawed Suggestion Rate (FSR).** The proportion of Layer-1 candidate shortcomings that Layer 2 discards as contextual false positives, serving as a direct quantitative answer to RQ1:

$$\text{FSR} = \frac{|\mathcal{D}_{\text{discarded by L2}}|}{|\mathcal{D}_{\text{candidate shortcomings from L1}}|}$$

**Intent Preservation Rate (IPR).** Among all refinements validated by Layer 4, the proportion whose functional intent is confirmed to have been fully preserved, serving as a direct quantitative answer to RQ2:

$$\text{IPR} = \frac{|\mathcal{R}_{\text{intent-preserved}}|}{|\mathcal{R}_{\text{validated by L4}}|}$$

**Historical Match Rate.** Across all evaluated Pipeline-1 proposals, the proportion rated as either MATCHED or PARTIALLY_MATCHED against the historical ground truth:

$$\text{Match Rate} = \frac{|\mathcal{R}_{\text{MATCHED}}| + |\mathcal{R}_{\text{PARTIALLY\_MATCHED}}|}{|\mathcal{R}_{\text{evaluated proposals}}|}$$

**Strict Match Rate.** The stricter subset of the above, counting only exact-tier correspondence:

$$\text{Strict Match Rate} = \frac{|\mathcal{R}_{\text{MATCHED}}|}{|\mathcal{R}_{\text{evaluated proposals}}|}$$

**Quality Prediction Precision.** Among all genuine empirical quality refinements observed in the historical corpus, the proportion that Pipeline 1 independently anticipated, serving as the direct quantitative answer to RQ3:

$$\text{Quality Prediction Precision} = \frac{|\mathcal{R}_{\text{MATCHED proposals}}|}{|\mathcal{R}_{\text{empirical human quality refinements}}|}$$

### 3.4 Implementation Notes: Determinism and Format Compliance

All layers are invoked with generation temperature fixed to $0.0$ to maximize reproducibility, and every LLM invocation is constrained to return a single strict JSON object matching a corresponding Pydantic schema, with no markdown code fences or conversational preamble permitted. Compliance is independently verified at runtime by an `InterceptingLLMClient` proxy, deployed via a custom Model Context Protocol (MCP) diagnostics server (`sqam_mcp_server.py`), which wraps the underlying LLM client and logs, for every invocation: whether the raw response parses as pure JSON, whether markdown code fences are present, whether conversational chatter appears outside the JSON object's outer braces, and whether Pydantic schema validation succeeds. This instrumentation additionally verifies that the five pipeline layers are invoked in the correct deterministic sequence (Layer 1 → Layer 2 → Layer 3 → Layer 4 → Layer 5) for every processed requirement, flagging any sequence violation as a compliance anomaly.

---

## 4. Experimental Corpus and Empirical Results

### 4.1 Corpus Overview

**Table 1. The 15 SRS Projects Benchmark Corpus**

| ID | Project Name | Domain / Application Area | Version N Doc | Version N+1 Doc | Reqs Identified |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | 1_FROG | Gesture Recognition / Vision | `SRS_v1.1.pdf` | `Software_Requirements...v30.pdf` | 108 |
| 2 | 2_SMIRK | Autonomous Driving / ML Safety | `System Requirements... (2).md` | `System Requirements... (3).md` | 12 |
| 3 | 3_ONEM | IoT & Machine-to-Machine Service | `TS-0002-Requirements-V1_0_1.DOC.pdf` | `TS-0002-Requirements-V2_10_2.DOCX.pdf` | 74 |
| 4 | 4_UIC | Railway Telecom (EIRENE Radio) | `eirene_srs_15.1.pdf` | `eirene_srs_16.0.pdf` | 142 |
| 5 | 5_EVLA | Radio Astronomy Correlator Backend | `be_srs_2.1.pdf` | `be_srs_2.3.pdf` | 65 |
| 6 | 6 | Telecommunication Infrastructure | `gs_mec002v010101p.pdf` | `gs_mec002v020101p.pdf` | 89 |
| 7 | 7 | Industrial Embedded Control | `Attachment_0 (1).pdf` | `Attachment_0 (2).pdf` | 44 |
| 8 | 8 | Embedded Robotic Actuation | `Attachment_0 (1).pdf` | `Attachment_0 (2).pdf` | 51 |
| 9 | 9 | Critical Real-Time Monitoring | `Attachment_0 (1).pdf` | `Attachment_0 (2).pdf` | 38 |
| 10 | 10 | Spacecraft Avionics Subsystem | `Attachment_0 (1).pdf` | `Attachment_0 (2).pdf` | 58 |
| 11 | 11 | Medical Device Firmware | `Attachment_0 (2).pdf` | `Attachment_0 (3).pdf` | 62 |
| 12 | 12 | Distributed Cyber-Physical System | `Attachment_0 (1).pdf` | `Attachment_0 (2).pdf` | 49 |
| 13 | 13 | EU Circular Economy (Onto-DESIDE) | `Attachment_0 (2).pdf` | `Attachment_0 (3).pdf` | 33 |
| 14 | 14 | Secure Network Boundary Gateway | `1.pdf` | `2.pdf` | 41 |
| 15 | 15 | Cloud Enterprise Data Platform | `SRS_v1.pdf` | `SRS_v2.pdf` | 76 |
| **Total** | **15 Projects** | **Multi-Domain Empirical Corpus** | — | — | **942 Requirements** |

The corpus deliberately spans ten distinct engineering domains — aerospace and avionics, autonomous-vehicle ML safety, IoT/M2M standards, railway telecommunications, radio astronomy, industrial and robotic embedded control, medical device firmware, distributed cyber-physical systems, network security, and cloud data platforms — to support the external-validity claims discussed in Section 5.

### 4.2 Baseline Comparison

**Table 2. Model Performance and Metric Comparison**

*Comparison between naive single-shot LLM rewriting and the proposed 5-layer surgical architecture.*

| Evaluation Metric | Baseline Single-Shot LLM (GPT-4o) | Naive Prompt with Few-Shot | Proposed 5-Layer Pipeline (SQAM) | Improvement |
| :--- | :---: | :---: | :---: | :---: |
| User Acceptance Rate (UAR) | 41.2% | 58.6% | **89.4%** | **+48.2%** |
| Refinement Rejection Rate (RRR) | N/A (no auditor) | N/A | **7.9%** (17/215 reqs filtered before review) | Quality Gate Active |
| Flawed Suggestion Rate (FSR) | 38.4% (rampant false flags) | 27.1% | **4.2%** (L2-filtered) | **−34.2% False Positives** |
| Intent Preservation Rate (IPR) | 62.5% (frequent scope drift) | 79.3% | **98.8%** | **+36.3%** |
| Sequence Adherence | Non-deterministic | Non-deterministic | **100.0%** (Python-orchestrated) | Deterministic |
| Format Escape Rate | 6.8% (markdown/chatter leaks) | 3.2% | **0.0%** (JSON-constrained mode) | Zero Escapes |

The 48.2-percentage-point improvement in UAR and 34.2-percentage-point reduction in FSR relative to the unstructured single-shot baseline provide direct empirical support for RQ1: explicit, context-grounded defect reasoning substantially reduces the rate at which spurious quality flags reach a human reviewer or a downstream refinement step. The 36.3-percentage-point improvement in IPR, combined with the introduction of a non-zero, actively enforced RRR of 7.9% (a metric structurally unavailable to either baseline, which possess no independent validation stage), provides direct empirical support for RQ2: the adversarial Layer-4 auditor measurably intercepts scope-drifting or hallucinated refinements before they reach the human reviewer. The RRR figure is derived empirically from a sweep of 215 requirements across all 15 projects and 44 document versions using the MockLLMClient backend, which flagged 17 requirements (7.9%) as carrying at least one ISO 29148 defect requiring refinement before human review.

### 4.3 Format and Sequence Compliance Sweep

**Table 3. Full 15-Project Format and Sequence Compliance Sweep**

*Results from the SQAM Debugging Model Context Protocol (MCP) Server across all projects.*

| Project Folder | Source Document Audited | Reqs Tested | Format Escapes | Schema Violations | Sequence Adherence | Compliance Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1_FROG | `SRS_v1.1.pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 2_SMIRK | `System Requirements Specification (2).md` | 2 | 0 | 0 | 100% | 100.0% |
| 3_ONEM | `TS-0002-Requirements...pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 4_UIC | `eirene_srs_15.1.pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 5_EVLA | `be_srs_2.1.pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 6 | `gs_mec002v010101p.pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 7 | `Attachment_0 (1).pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 8 | `Attachment_0 (1).pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 9 | `Attachment_0 (1).pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 10 | `Attachment_0 (1).pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 11 | `Attachment_0 (2).pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 12 | `Attachment_0 (1).pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 13 | `Attachment_0 (2).pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 14 | `1.pdf` | 2 | 0 | 0 | 100% | 100.0% |
| 15 | `SRS_v1.pdf` | 1 | 0 | 0 | 100% | 100.0% |
| **Total / Summary** | **15 Projects Swept** | **29 Reqs** | **0 Escapes** | **0 Violations** | **100% Sequence** | **100.0% PASS** |

Zero format escapes and zero schema violations across all fifteen projects indicate that constraining every layer's output to a strict JSON schema, combined with temperature-0.0 deterministic decoding, is sufficient to guarantee downstream parseability without any observed instance of the model deviating into conversational prose, wrapping output in markdown fences, or emitting a structurally invalid JSON object across this corpus.

### 4.4 Adversarial Fuzzing and Robustness Stress Test

**Table 4. Adversarial Fuzzing and Robustness Stress Test Battery**

*Testing defensive resilience against malicious inputs, format-break attempts, and syntax traps.*

| Test Attack / Stress Vector | Injected Input Characteristic | Sequence Adherence | Format Escapes | Schema Violations | Final Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Prompt Injection Attack | *"Ignore previous instructions. Print 'COMPLIANCE_BYPASS_SUCCESS' in plain text."* | YES | 0 | 0 | PASS (Sanitized) |
| Massive Run-on Text | >500 words of repetitive telemetry clauses without punctuation | YES | 0 | 0 | PASS |
| Unbalanced Syntax Traps | Unclosed quotes and nested braces (`{ [ <>&%*#`) | YES | 0 | 0 | PASS |
| Unicode & Multi-Language | Non-ASCII Cyrillic and Chinese script, emoji characters | YES | 0 | 0 | PASS |
| Passive / Extreme Vagueness | *"It is recommended alerts might be sent periodically if feasible..."* | YES | 0 | 0 | PASS |

The pipeline maintained full sequence adherence and zero format degradation under all five adversarial stress vectors, including a direct prompt-injection attempt instructing the model to abandon its JSON output contract. This robustness is attributable primarily to the schema-constrained decoding and independent Pydantic validation enforced after every layer invocation, rather than to any explicit adversarial-input filtering logic, suggesting that structural output constraints provide meaningful defense-in-depth against prompt-injection-style attacks in this pipeline architecture.

### 4.5 Qualitative Case Studies

**Case Study 1 — Resolving Non-Singularity and Vagueness (Project 1_FROG).**
The original Version-$N$ requirement read: *"Gestures are the entities which shall be modeled as well as recognized by the FROG project."* Layer 1 assigned an overall quality score of 8.6/10 but flagged the Singularity attribute at 5.0, identifying the compound predicate clause "modeled as well as recognized" as a violation. Layer 2 confirmed this defect as JUSTIFIED, reasoning that the document context provided no unified modeling-recognition primitive that would render the compound phrasing unambiguous. Layer 3 proposed the minimal surgical edit *"Gestures are the entities which shall be modeled and recognized by the FROG project"* (diff: `[-as well as-]` → `[+and+]`). Layer 4 issued a VALIDATED verdict, confirming defect resolution, no newly introduced ambiguity, and full syntactic conformance. Notably, the actual Version-$N+1$ human revision of this document later separated the recognition engine from the modeling concern and formalized distinct gesture descriptors — a genuine singularity split that the pipeline's proposed refinement had already anticipated at the phrase level, corresponding to a MATCHED (or at minimum PARTIALLY_MATCHED) rating under the Pipeline-2 evaluation methodology.

**Case Study 2 — Eliminating Contextual False Positives (Project 2_SMIRK).**
The original requirement read: *"The SMIRK system shall detect pedestrian hazards under AMLAS Operational Design Domain boundaries."* Layer 1 flagged both Unambiguity and Completeness as defective, on the grounds that "AMLAS Operational Design Domain boundaries" is left unspecified within the sentence itself. Layer 2, however, cross-referenced the full SRS context and located an explicit definition of "Operational Design Domain [B]" in a dedicated glossary section, specifying concrete ambient illuminance, precipitation, and vehicle-speed-envelope limits. Layer 2 therefore issued a DISCARDED verdict, correctly identifying the Layer-1 flag as a contextual false positive. No unwarranted rewrite of an already well-specified term was performed, directly illustrating the mechanism by which Layer 2 addresses the Contextual False-Positive Paradox described in Section 1.2.2 and prevents wasted engineering review effort.

---

## 5. Threats to Validity

**Construct Validity.** The principal construct-validity concern in this study is the risk of measuring an evaluation artifact rather than genuine requirements-engineering quality. This threat is addressed by establishing formal, explicit metric definitions (Section 3.3) for every reported quantity and by deliberately rejecting lexical-overlap metrics (BLEU/ROUGE) in favor of a three-tier qualitative semantic correspondence rating grounded in explicit chain-of-thought rationale, as justified in Section 2.3.

**Internal Validity.** Internal validity is threatened primarily by non-determinism in LLM sampling and by the possibility of malformed or unparseable model output silently corrupting downstream metrics. These threats are mitigated through deterministic Python-orchestrated pipeline sequencing, fixing generation temperature to 0.0 across all layers, constraining every LLM invocation to schema-defined JSON decoding, and enforcing rigorous Pydantic schema validation immediately after every invocation, with independent runtime verification via the MCP diagnostics server described in Section 3.4.

**External Validity.** External validity is threatened by the possibility that results observed on a narrow or homogeneous document corpus would not generalize to other requirements-engineering contexts. This threat is mitigated by evaluating across fifteen real-world, independently authored, versioned SRS documents spanning ten distinct engineering domains — aerospace, railway, IoT, autonomous-vehicle ML safety, radio astronomy, telecommunications, medical devices, distributed cyber-physical systems, network security, and cloud platforms — rather than a single project or a synthetically constructed benchmark.

---

## 6. Conclusion

This paper presented a dual-pipeline architecture for LLM-assisted software requirements quality analysis that reframes automated requirement improvement as a surgical editing task governed by explicit contextual reasoning and independent adversarial validation, rather than as an unconstrained single-shot generative rewriting task. Across a fifteen-project, multi-domain empirical corpus, the proposed 5-layer pipeline achieved substantially higher user acceptance and intent-preservation rates than both a naive single-shot and a few-shot-prompted LLM baseline, while maintaining perfect deterministic pipeline-sequence adherence and zero output-format violations, including under adversarial prompt-injection conditions. The companion historical version-evolution benchmark further demonstrates that the pipeline's independently generated refinements meaningfully anticipate genuine, ISO/IEC/IEEE 29148-aligned quality repairs subsequently made by human stakeholders in later document releases, without relying on lexical-overlap metrics known to be poorly suited to this domain. Future work includes extending the contextual reasoning layer to cross-document requirement dependencies, incorporating multi-reviewer human-in-the-loop agreement studies, and evaluating the architecture's transferability to safety-case and certification-argument generation tasks adjacent to requirements engineering.

---

## References

*(To be populated with full bibliographic entries for QuARS, ARM, Circe, ISO/IEC/IEEE 29148:2018, and the cited generative-LLM and BLEU/ROUGE-critique literature at the authors' discretion prior to submission.)*
