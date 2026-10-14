"""
Script to generate publication-grade SVGs for the SQAM Project:
1. figures/pipeline1_architecture.svg (5-Layer Quality Analyzer)
2. figures/pipeline2_architecture.svg (Empirical Final SRS Benchmark)
3. figures/dual_pipeline_overview.svg (Master Dual-Pipeline Cooperation Architecture)
"""

import xml.etree.ElementTree as ET
from pathlib import Path

FIGURES_DIR = Path(r"e:\sem 7\SQAM_Project_Code\figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def build_pipeline1_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 1380" width="100%" height="100%">
  <defs>
    <filter id="shadow" x="-3%" y="-2%" width="106%" height="106%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <filter id="shadow-sm" x="-2%" y="-2%" width="104%" height="104%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.06"/>
    </filter>
    
    <linearGradient id="header-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>

    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
    </marker>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb"/>
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#dc2626"/>
    </marker>
    <marker id="arrow-emerald" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669"/>
    </marker>
  </defs>

  <style>
    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 24px; font-weight: 700; fill: #ffffff; }
    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; font-weight: 400; fill: #94a3b8; }
    .card-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 16px; font-weight: 700; }
    .badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 700; }
    .body-bold { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; font-weight: 600; fill: #1e293b; }
    .body-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 400; fill: #334155; }
    .muted-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 400; fill: #64748b; }
    .code-text { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #0f172a; }
    .math-text { font-family: "Cambria Math", "Times New Roman", serif; font-size: 13px; font-style: italic; }
  </style>

  <!-- Background -->
  <rect width="1100" height="1380" fill="#f8fafc"/>

  <!-- Master Header -->
  <g transform="translate(40, 24)">
    <rect width="1020" height="84" rx="12" fill="url(#header-grad)" filter="url(#shadow)"/>
    <text x="32" y="38" class="title">Pipeline 1: Five-Layer Surgical Requirements Quality Analyzer</text>
    <text x="32" y="62" class="subtitle">ISO/IEC/IEEE 29148 Compliance Auditing, Contextual False-Positive Elimination &amp; EARS Surgical Refinement</text>
    
    <!-- Header Badges -->
    <rect x="850" y="26" width="140" height="32" rx="16" fill="#1e1b4b" stroke="#6366f1" stroke-width="1.5"/>
    <text x="920" y="46" text-anchor="middle" class="badge-text" fill="#a5b4fc">FAIL-CLOSED GATING</text>
  </g>

  <!-- INPUT SECTION -->
  <g transform="translate(40, 130)">
    <rect width="1020" height="110" rx="10" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" filter="url(#shadow-sm)"/>
    
    <!-- Badge -->
    <rect x="20" y="16" width="90" height="24" rx="6" fill="#eff6ff"/>
    <text x="65" y="32" text-anchor="middle" class="badge-text" fill="#1d4ed8">INPUT DATA</text>
    
    <!-- Subsections -->
    <g transform="translate(20, 50)">
      <!-- Target Requirement Box -->
      <rect width="470" height="46" rx="6" fill="#f1f5f9" stroke="#e2e8f0"/>
      <text x="14" y="20" class="body-bold">Target Requirement (Requirement Unit)</text>
      <text x="14" y="36" class="code-text" fill="#2563eb">req_id: str | type: REQ_TYPE | section: str | text: str</text>

      <!-- SRS Context Box -->
      <rect x="490" y="0" width="490" height="46" rx="6" fill="#f1f5f9" stroke="#e2e8f0"/>
      <text x="504" y="20" class="body-bold">Enclosing SRS Context (SRSContext)</text>
      <text x="504" y="36" class="muted-text">Domain Summary • Domain Glossary • Surrounding Window (±3 Reqs) • Applicable Standards</text>
    </g>
  </g>

  <!-- Connector: Inputs -> Layer 1 -->
  <path d="M 550 240 L 550 270" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- ==================== LAYER 1 ==================== -->
  <g transform="translate(40, 270)">
    <rect width="1020" height="175" rx="10" fill="#ffffff" stroke="#bfdbfe" stroke-width="2" filter="url(#shadow-sm)"/>
    
    <!-- Layer Header Banner -->
    <rect width="1020" height="38" rx="10" fill="#eff6ff"/>
    <rect x="20" y="8" width="80" height="22" rx="4" fill="#2563eb"/>
    <text x="60" y="23" text-anchor="middle" class="badge-text" fill="#ffffff">LAYER 1</text>
    <text x="115" y="24" class="card-title" fill="#1e3a8a">Requirement Quality Analysis (Layer1DocumentScorer)</text>
    <text x="990" y="24" text-anchor="end" class="code-text" fill="#3b82f6">Pydantic: Layer1Output</text>

    <!-- Content Columns -->
    <g transform="translate(24, 52)">
      <!-- Col 1: Attributes Evaluated -->
      <text x="0" y="16" class="body-bold">7 ISO/IEC/IEEE 29148 Quality Attributes:</text>
      <g transform="translate(0, 26)">
        <rect x="0" y="0" width="100" height="20" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="50" y="14" text-anchor="middle" class="muted-text">Unambiguity (w=0.2)</text>
        <rect x="108" y="0" width="100" height="20" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="158" y="14" text-anchor="middle" class="muted-text">Completeness (0.2)</text>
        <rect x="216" y="0" width="95" height="20" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="263" y="14" text-anchor="middle" class="muted-text">Consistency (0.1)</text>
        <rect x="319" y="0" width="95" height="20" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="366" y="14" text-anchor="middle" class="muted-text">Conformance (0.1)</text>
        <rect x="422" y="0" width="90" height="20" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="467" y="14" text-anchor="middle" class="muted-text">Correctness (0.1)</text>
        <rect x="520" y="0" width="90" height="20" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="565" y="14" text-anchor="middle" class="muted-text">Singularity (0.1)</text>
        <rect x="618" y="0" width="110" height="20" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="673" y="14" text-anchor="middle" class="muted-text">Verifiability (0.2)</text>
      </g>

      <!-- Col 2: Deterministic Composite Math & Defect Gating -->
      <g transform="translate(0, 64)">
        <rect width="470" height="46" rx="6" fill="#f0f9ff" stroke="#bae6fd"/>
        <text x="12" y="18" class="body-bold" fill="#0369a1">Deterministic Quality Score Calculation (Python Runtime)</text>
        <text x="12" y="36" class="code-text" fill="#0284c7">Q_req = Σ (w_i · S(A_i)) ∈ [0.0, 10.0]  |  Prevents Hallucinated Math</text>

        <rect x="490" y="0" width="480" height="46" rx="6" fill="#fef2f2" stroke="#fecaca"/>
        <text x="504" y="18" class="body-bold" fill="#991b1b">Candidate Defect Trigger Rule</text>
        <text x="504" y="36" class="body-text" fill="#b91c1c">If S(A_i) &lt; 8.0 ➔ Emit candidate Shortcoming(id, attr, excerpt, explanation)</text>
      </g>
    </g>
  </g>

  <!-- Connector: Layer 1 -> Layer 2 -->
  <path d="M 550 445 L 550 475" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="450" y="448" width="200" height="20" rx="10" fill="#f1f5f9" stroke="#cbd5e1"/>
  <text x="550" y="462" text-anchor="middle" class="code-text" fill="#475569">Passes: D_L1 Candidate Defects</text>

  <!-- ==================== LAYER 2 ==================== -->
  <g transform="translate(40, 475)">
    <rect width="1020" height="195" rx="10" fill="#ffffff" stroke="#fde68a" stroke-width="2" filter="url(#shadow-sm)"/>
    
    <!-- Layer Header Banner -->
    <rect width="1020" height="38" rx="10" fill="#fffbeb"/>
    <rect x="20" y="8" width="80" height="22" rx="4" fill="#d97706"/>
    <text x="60" y="23" text-anchor="middle" class="badge-text" fill="#ffffff">LAYER 2</text>
    <text x="115" y="24" class="card-title" fill="#92400e">Contextual Defect Reasoning (Layer2DefectReasoner)</text>
    <text x="990" y="24" text-anchor="end" class="code-text" fill="#b45309">Pydantic: Layer2Output</text>

    <g transform="translate(24, 50)">
      <text x="0" y="16" class="body-bold">Resolves the "Contextual False-Positive Paradox":</text>
      <text x="0" y="34" class="body-text">Audits candidate defects against surrounding definitions, glossary entries, and companion requirements across the SRS.</text>

      <!-- Partition Boxes -->
      <g transform="translate(0, 46)">
        <!-- Discarded Partition -->
        <rect width="470" height="80" rx="6" fill="#fef2f2" stroke="#fca5a5" stroke-dasharray="4 2"/>
        <rect x="12" y="10" width="130" height="20" rx="4" fill="#fee2e2"/>
        <text x="77" y="24" text-anchor="middle" class="badge-text" fill="#991b1b">DISCARDED DEFECTS</text>
        <text x="155" y="24" class="muted-text">False Positives (Resolved in Context)</text>
        <text x="14" y="48" class="body-text" fill="#7f1d1d">• Term explicitly defined in Glossary or Standards</text>
        <text x="14" y="66" class="body-text" fill="#7f1d1d">• Bound established by neighboring requirement • Suppressed from Generation</text>

        <!-- Retained Partition -->
        <rect x="490" y="0" width="480" height="80" rx="6" fill="#f0fdf4" stroke="#86efac"/>
        <rect x="504" y="10" width="125" height="20" rx="4" fill="#dcfce7"/>
        <text x="566" y="24" text-anchor="middle" class="badge-text" fill="#166534">RETAINED DEFECTS</text>
        <text x="640" y="24" class="muted-text">True Quality Vulnerabilities</text>
        <text x="504" y="48" class="body-text" fill="#14532d">• Genuine specification ambiguity, missing bounds, or untestable clauses</text>
        <text x="504" y="66" class="body-bold" fill="#166534">➔ Only Retained Defects proceed downstream to Layer 3</text>
      </g>
    </g>

    <!-- Side Metric Box -->
    <rect x="800" y="8" width="190" height="22" rx="4" fill="#fef3c7"/>
    <text x="895" y="23" text-anchor="middle" class="code-text" fill="#92400e">FSR = |D_discarded| / |D_L1|</text>
  </g>

  <!-- Connectors from Layer 2 -->
  <!-- Main Path to Layer 3 -->
  <path d="M 750 670 L 750 710" stroke="#059669" stroke-width="2.5" marker-end="url(#arrow-emerald)"/>
  <rect x="660" y="678" width="180" height="20" rx="10" fill="#ecfdf5" stroke="#a7f3d0"/>
  <text x="750" y="692" text-anchor="middle" class="code-text" fill="#065f46">Passes: D_retained ONLY</text>

  <!-- Terminated Path for Discarded -->
  <path d="M 270 670 L 270 705" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3 3"/>
  <circle cx="270" cy="708" r="4" fill="#dc2626"/>
  <text x="280" y="695" class="code-text" fill="#b91c1c">Terminated (No downstream action)</text>

  <!-- ==================== LAYER 3 ==================== -->
  <g transform="translate(40, 710)">
    <rect width="1020" height="175" rx="10" fill="#ffffff" stroke="#ddd6fe" stroke-width="2" filter="url(#shadow-sm)"/>
    
    <!-- Layer Header Banner -->
    <rect width="1020" height="38" rx="10" fill="#f5f3ff"/>
    <rect x="20" y="8" width="80" height="22" rx="4" fill="#7c3aed"/>
    <text x="60" y="23" text-anchor="middle" class="badge-text" fill="#ffffff">LAYER 3</text>
    <text x="115" y="24" class="card-title" fill="#5b21b6">Surgical Requirement Refinement (Layer3SolutionGenerator)</text>
    <text x="990" y="24" text-anchor="end" class="code-text" fill="#7c3aed">Pydantic: Layer3Output</text>

    <g transform="translate(24, 52)">
      <text x="0" y="16" class="body-bold">Constrained Surgical Refinement Engine (Zero Wholesale Rewriting):</text>
      
      <!-- 4 Pillars -->
      <g transform="translate(0, 28)">
        <rect width="230" height="74" rx="6" fill="#faf5ff" stroke="#e9d5ff"/>
        <text x="12" y="20" class="body-bold" fill="#6b21a8">1. Strict Scope Lock</text>
        <text x="12" y="38" class="body-text">Preserve domain entities,</text>
        <text x="12" y="54" class="body-text">system names &amp; intent</text>

        <rect x="245" y="0" width="230" height="74" rx="6" fill="#faf5ff" stroke="#e9d5ff"/>
        <text x="257" y="20" class="body-bold" fill="#6b21a8">2. EARS Syntax</text>
        <text x="257" y="38" class="body-text">Ubiquitous ("shall"),</text>
        <text x="257" y="54" class="body-text">Event/State-driven rules</text>

        <rect x="490" y="0" width="230" height="74" rx="6" fill="#faf5ff" stroke="#e9d5ff"/>
        <text x="502" y="20" class="body-bold" fill="#6b21a8">3. Defect-Targeted</text>
        <text x="502" y="38" class="body-text">Resolves ONLY defect IDs</text>
        <text x="502" y="54" class="body-text">present in D_retained</text>

        <rect x="735" y="0" width="235" height="74" rx="6" fill="#faf5ff" stroke="#e9d5ff"/>
        <text x="747" y="20" class="body-bold" fill="#6b21a8">4. Traceable Audit</text>
        <text x="747" y="38" class="body-text">Emits changes_made &amp;</text>
        <text x="747" y="54" class="body-text">intent_preservation_rationale</text>
      </g>
    </g>
  </g>

  <!-- Connector: Layer 3 -> Layer 4 -->
  <path d="M 550 885 L 550 915" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="420" y="888" width="260" height="20" rx="10" fill="#f1f5f9" stroke="#cbd5e1"/>
  <text x="550" y="902" text-anchor="middle" class="code-text" fill="#475569">Passes: Proposed Refinement + D_retained</text>

  <!-- ==================== LAYER 4 ==================== -->
  <g transform="translate(40, 915)">
    <rect width="1020" height="185" rx="10" fill="#ffffff" stroke="#a7f3d0" stroke-width="2" filter="url(#shadow-sm)"/>
    
    <!-- Layer Header Banner -->
    <rect width="1020" height="38" rx="10" fill="#ecfdf5"/>
    <rect x="20" y="8" width="80" height="22" rx="4" fill="#059669"/>
    <text x="60" y="23" text-anchor="middle" class="badge-text" fill="#ffffff">LAYER 4</text>
    <text x="115" y="24" class="card-title" fill="#065f46">Independent Solution Validation (Layer4SolutionValidator)</text>
    <text x="990" y="24" text-anchor="end" class="code-text" fill="#059669">Pydantic: Layer4Output</text>

    <g transform="translate(24, 52)">
      <text x="0" y="16" class="body-bold">Fail-Closed Adversarial Critic (Conjunctive Audit Function: V = ⋀ c_j):</text>
      
      <!-- 5 Audit Checks -->
      <g transform="translate(0, 26)">
        <rect width="180" height="42" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="10" y="18" class="body-bold" font-size="11">1. Defect Resolution</text>
        <text x="10" y="32" class="muted-text">All D_retained fixed?</text>

        <rect x="195" y="0" width="180" height="42" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="205" y="18" class="body-bold" font-size="11">2. No New Ambiguity</text>
        <text x="205" y="32" class="muted-text">Zero vague terms added?</text>

        <rect x="390" y="0" width="190" height="42" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="400" y="18" class="body-bold" font-size="11">3. No Unwarranted Assumptions</text>
        <text x="400" y="32" class="muted-text">No fabricated features?</text>

        <rect x="595" y="0" width="185" height="42" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="605" y="18" class="body-bold" font-size="11">4. Intent Preservation</text>
        <text x="605" y="32" class="muted-text">Original logic retained?</text>

        <rect x="795" y="0" width="180" height="42" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="805" y="18" class="body-bold" font-size="11">5. Conformance</text>
        <text x="805" y="32" class="muted-text">IEEE 29148 modal syntax?</text>
      </g>

      <!-- Decision Rule Box -->
      <g transform="translate(0, 80)">
        <rect width="975" height="36" rx="6" fill="#f0fdf4" stroke="#86efac"/>
        <text x="16" y="22" class="body-bold" fill="#166534">Gating Rule:</text>
        <text x="100" y="22" class="body-text" fill="#14532d">If ANY check fails (False) ➔ pass_validation = False. Proposal is flagged with explicit critic observation.</text>
      </g>
    </g>
  </g>

  <!-- Connector: Layer 4 -> Layer 5 -->
  <path d="M 550 1100 L 550 1130" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="420" y="1105" width="260" height="20" rx="10" fill="#f1f5f9" stroke="#cbd5e1"/>
  <text x="550" y="1119" text-anchor="middle" class="code-text" fill="#475569">Passes: Validated Audit Payload</text>

  <!-- ==================== LAYER 5 ==================== -->
  <g transform="translate(40, 1130)">
    <rect width="1020" height="135" rx="10" fill="#ffffff" stroke="#99f6e4" stroke-width="2" filter="url(#shadow-sm)"/>
    
    <!-- Layer Header Banner -->
    <rect width="1020" height="38" rx="10" fill="#f0fdfa"/>
    <rect x="20" y="8" width="80" height="22" rx="4" fill="#0d9488"/>
    <text x="60" y="23" text-anchor="middle" class="badge-text" fill="#ffffff">LAYER 5</text>
    <text x="115" y="24" class="card-title" fill="#115e59">Human Decision Management (Layer5HumanDecisionManager)</text>
    <text x="990" y="24" text-anchor="end" class="code-text" fill="#0d9488">Pydantic: Layer5Output</text>

    <g transform="translate(24, 52)">
      <g transform="translate(0, 0)">
        <rect width="300" height="64" rx="6" fill="#f0fdfa" stroke="#ccfbf1"/>
        <text x="14" y="20" class="body-bold" fill="#0f766e">Word-Level Diff Engine</text>
        <text x="14" y="38" class="body-text">Punctuation-preserving inline</text>
        <text x="14" y="52" class="body-text">deletions &amp; insertions</text>

        <rect x="320" y="0" width="340" height="64" rx="6" fill="#f0fdfa" stroke="#ccfbf1"/>
        <text x="334" y="20" class="body-bold" fill="#0f766e">Complete Chain of Custody</text>
        <text x="334" y="38" class="body-text">Aggregates rationales from L1 score,</text>
        <text x="334" y="52" class="body-text">L2 suppression trace &amp; L4 validation audit</text>

        <rect x="680" y="0" width="295" height="64" rx="6" fill="#f0fdfa" stroke="#ccfbf1"/>
        <text x="694" y="20" class="body-bold" fill="#0f766e">Actionable Recommendation</text>
        <text x="694" y="38" class="body-text">Auto-Accept / Stakeholder Review /</text>
        <text x="694" y="52" class="body-text">Manual Override Trigger</text>
      </g>
    </g>
  </g>

  <!-- FINAL OUTPUT BANNER -->
  <g transform="translate(40, 1290)">
    <rect width="1020" height="56" rx="10" fill="#1e293b" filter="url(#shadow-sm)"/>
    <text x="32" y="34" class="title" font-size="16">OUTPUT ARTIFACT: PipelineExecutionResult</text>
    <text x="480" y="34" class="code-text" fill="#38bdf8">status: "completed" | "error"  •  execution_time_seconds: float  •  all layer payloads encapsulated</text>
  </g>

</svg>
"""


def build_pipeline2_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 960" width="100%" height="100%">
  <defs>
    <filter id="p2-shadow" x="-3%" y="-2%" width="106%" height="106%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <filter id="p2-shadow-sm" x="-2%" y="-2%" width="104%" height="104%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.06"/>
    </filter>

    <linearGradient id="p2-header-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>

    <marker id="p2-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
    </marker>
    <marker id="p2-arrow-indigo" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#4f46e5"/>
    </marker>
    <marker id="p2-arrow-emerald" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669"/>
    </marker>
  </defs>

  <style>
    .p2-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 22px; font-weight: 700; fill: #ffffff; }
    .p2-subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; font-weight: 400; fill: #c7d2fe; }
    .p2-card-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 15px; font-weight: 700; }
    .p2-badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; font-weight: 700; }
    .p2-body-bold { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 600; fill: #1e293b; }
    .p2-body-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 400; fill: #334155; }
    .p2-muted-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10.5px; font-weight: 400; fill: #64748b; }
    .p2-code-text { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #0f172a; }
  </style>

  <!-- Background -->
  <rect width="1200" height="960" fill="#f8fafc"/>

  <!-- Master Header -->
  <g transform="translate(40, 24)">
    <rect width="1120" height="84" rx="12" fill="url(#p2-header-grad)" filter="url(#p2-shadow)"/>
    <text x="32" y="38" class="p2-title">Pipeline 2: Empirical SRS Version Evolution Benchmark</text>
    <text x="32" y="62" class="p2-subtitle">Benchmarking Automated Refinements Directly Against the Official Final Version of the SRS (V_final / V_N+1)</text>
    
    <rect x="910" y="26" width="180" height="32" rx="16" fill="#312e81" stroke="#818cf8" stroke-width="1.5"/>
    <text x="1000" y="46" text-anchor="middle" class="p2-badge-text" fill="#e0e7ff">DOCUMENT GROUND TRUTH</text>
  </g>

  <!-- TOP INPUT DOCUMENTS -->
  <g transform="translate(40, 130)">
    <!-- Draft SRS Document V_N -->
    <g transform="translate(0, 0)">
      <rect width="530" height="80" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" filter="url(#p2-shadow-sm)"/>
      <rect x="16" y="12" width="160" height="22" rx="4" fill="#eff6ff"/>
      <text x="96" y="27" text-anchor="middle" class="p2-badge-text" fill="#1d4ed8">DRAFT SPECIFICATION (V_N)</text>
      <text x="190" y="28" class="p2-body-bold">Preliminary SRS Document</text>
      <text x="16" y="58" class="p2-body-text">Contains raw draft requirements prior to engineering review and safety revisions.</text>
    </g>

    <!-- Final SRS Document V_final -->
    <g transform="translate(590, 0)">
      <rect width="530" height="80" rx="8" fill="#ffffff" stroke="#86efac" stroke-width="1.5" filter="url(#p2-shadow-sm)"/>
      <rect x="16" y="12" width="200" height="22" rx="4" fill="#dcfce7"/>
      <text x="116" y="27" text-anchor="middle" class="p2-badge-text" fill="#166534">FINAL SRS RELEASE (V_final / V_N+1)</text>
      <text x="230" y="28" class="p2-body-bold">Empirical Ground Truth Document</text>
      <text x="16" y="58" class="p2-body-text">Official approved specification incorporating real-world engineering refinements.</text>
    </g>
  </g>

  <!-- Connectors from Inputs -->
  <!-- V_N to Pipeline 1 -->
  <path d="M 200 210 L 200 270" stroke="#4f46e5" stroke-width="2" marker-end="url(#p2-arrow-indigo)"/>
  <rect x="120" y="225" width="160" height="20" rx="10" fill="#e0e7ff"/>
  <text x="200" y="239" text-anchor="middle" class="p2-code-text" fill="#3730a3">Blind Evaluation (No V_final)</text>

  <!-- V_N and V_final to Document Aligner -->
  <path d="M 400 210 L 400 240 L 700 240 L 700 270" stroke="#475569" stroke-width="1.5" fill="none" marker-end="url(#p2-arrow)"/>
  <path d="M 850 210 L 850 270" stroke="#475569" stroke-width="1.5" marker-end="url(#p2-arrow)"/>

  <!-- ==================== MIDDLE ROW: TWO COOPERATING ENGINES ==================== -->
  
  <!-- LEFT: Pipeline 1 Execution Harness -->
  <g transform="translate(40, 270)">
    <rect width="480" height="240" rx="10" fill="#ffffff" stroke="#c7d2fe" stroke-width="2" filter="url(#p2-shadow-sm)"/>
    
    <rect width="480" height="36" rx="10" fill="#eef2ff"/>
    <rect x="14" y="7" width="90" height="22" rx="4" fill="#4f46e5"/>
    <text x="59" y="22" text-anchor="middle" class="p2-badge-text" fill="#ffffff">SYSTEM TEST</text>
    <text x="115" y="23" class="p2-card-title" fill="#312e81">Pipeline 1 Execution Harness</text>

    <g transform="translate(16, 50)">
      <text x="0" y="16" class="p2-body-bold">Operates strictly on Draft V_N Requirements:</text>
      
      <!-- Mini 5 layer flow -->
      <g transform="translate(0, 26)">
        <rect width="448" height="30" rx="4" fill="#f8fafc" stroke="#e2e8f0"/>
        <text x="10" y="20" class="p2-code-text" font-size="10">L1: Score ➔ L2: Suppress ➔ L3: Refine ➔ L4: Audit ➔ L5: Diff</text>
      </g>

      <g transform="translate(0, 70)">
        <rect width="448" height="74" rx="6" fill="#faf5ff" stroke="#e9d5ff"/>
        <text x="12" y="20" class="p2-body-bold" fill="#6b21a8">Output: Independent Quality Proposal</text>
        <text x="12" y="38" class="p2-body-text">• Flagged Defect Attributes (Layer 1 &amp; 2)</text>
        <text x="12" y="54" class="p2-body-text">• Proposed Surgical Refinement (Layer 3 &amp; 4)</text>
        <text x="12" y="70" class="p2-code-text" fill="#7c3aed">Active Proposals: R_prop = { u ∈ U | Refined(u) ≠ Original(u) }</text>
      </g>
    </g>
  </g>

  <!-- RIGHT: Empirical Ground Truth Extraction -->
  <g transform="translate(560, 270)">
    <rect width="600" height="240" rx="10" fill="#ffffff" stroke="#bbf7d0" stroke-width="2" filter="url(#p2-shadow-sm)"/>
    
    <rect width="600" height="36" rx="10" fill="#f0fdf4"/>
    <rect x="14" y="7" width="130" height="22" rx="4" fill="#16a34a"/>
    <text x="79" y="22" text-anchor="middle" class="p2-badge-text" fill="#ffffff">GROUND TRUTH ENGINE</text>
    <text x="155" y="23" class="p2-card-title" fill="#14532d">Document Alignment &amp; Evolution Classification</text>

    <g transform="translate(16, 50)">
      <!-- Step 1: Structural Aligner -->
      <rect width="568" height="66" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
      <text x="12" y="18" class="p2-body-bold">1. Structural Document Aligner (aligner.py)</text>
      <text x="12" y="34" class="p2-body-text">• Stage 1: Exact ID matching over genuine specification keys (synthetic IDs isolated)</text>
      <text x="12" y="50" class="p2-body-text">• Stage 2: Normalized Levenshtein edit similarity alignment for unnumbered requirements</text>

      <!-- Step 2: Change Classifier -->
      <g transform="translate(0, 76)">
        <rect width="568" height="74" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
        <text x="12" y="18" class="p2-body-bold">2. Evolutionary Change Classifier (6 Mutually Exclusive Classes):</text>
        <text x="12" y="36" class="p2-muted-text">UNCHANGED • EDITORIAL_TEXTUAL • FUNCTIONAL_SCOPE_CHANGE • ADDED • DELETED</text>
        <text x="12" y="54" class="p2-body-bold" fill="#047857">QUALITY_REFINEMENT:</text>
        <text x="148" y="54" class="p2-muted-text">Ambiguity • Quantification • Parameterization • Scope Clarification • Consistency</text>
      </g>
    </g>
  </g>

  <!-- Connectors to Evaluator -->
  <path d="M 280 510 L 280 550 L 520 550 L 520 580" stroke="#4f46e5" stroke-width="2" fill="none" marker-end="url(#p2-arrow-indigo)"/>
  <path d="M 860 510 L 860 550 L 680 550 L 680 580" stroke="#16a34a" stroke-width="2" fill="none" marker-end="url(#p2-arrow-emerald)"/>

  <!-- ==================== CONVERGENCE: SEMANTIC CORRESPONDENCE EVALUATOR ==================== -->
  <g transform="translate(40, 580)">
    <rect width="1120" height="185" rx="10" fill="#ffffff" stroke="#cbd5e1" stroke-width="2" filter="url(#p2-shadow)"/>
    
    <rect width="1120" height="38" rx="10" fill="#f1f5f9"/>
    <rect x="14" y="8" width="130" height="22" rx="4" fill="#334155"/>
    <text x="79" y="23" text-anchor="middle" class="p2-badge-text" fill="#ffffff">SEMANTIC AUDIT</text>
    <text x="155" y="24" class="p2-card-title" fill="#0f172a">Semantic Correspondence Evaluator (evaluator.py)</text>
    <text x="1090" y="24" text-anchor="end" class="p2-code-text" fill="#475569">Qualitative Chain-of-Thought Comparison vs Final SRS</text>

    <!-- 3-Way Rating Badges -->
    <g transform="translate(20, 50)">
      <!-- MATCHED -->
      <rect width="345" height="110" rx="8" fill="#f0fdf4" stroke="#86efac"/>
      <rect x="14" y="12" width="90" height="22" rx="4" fill="#16a34a"/>
      <text x="59" y="27" text-anchor="middle" class="p2-badge-text" fill="#ffffff">MATCHED</text>
      <text x="115" y="28" class="p2-body-bold" fill="#14532d">Independent Discovery</text>
      <text x="14" y="56" class="p2-body-text">Pipeline-1 independently flagged the defect</text>
      <text x="14" y="72" class="p2-body-text">and generated a refinement semantically</text>
      <text x="14" y="88" class="p2-body-bold" fill="#166534">equivalent to the Final Version of the SRS.</text>

      <!-- PARTIALLY_MATCHED -->
      <rect x="365" y="0" width="345" height="110" rx="8" fill="#fffbeb" stroke="#fde68a"/>
      <rect x="379" y="12" width="150" height="22" rx="4" fill="#d97706"/>
      <text x="454" y="27" text-anchor="middle" class="p2-badge-text" fill="#ffffff">PARTIALLY_MATCHED</text>
      <text x="540" y="28" class="p2-body-bold" fill="#92400e">Correct Defect Clause</text>
      <text x="379" y="56" class="p2-body-text">Pipeline-1 targeted the exact defect clause,</text>
      <text x="379" y="72" class="p2-body-text">but proposed an alternative remediation</text>
      <text x="379" y="88" class="p2-body-bold" fill="#b45309">compared to the Final SRS resolution.</text>

      <!-- NOT_MATCHED -->
      <rect x="730" y="0" width="350" height="110" rx="8" fill="#fef2f2" stroke="#fca5a5"/>
      <rect x="744" y="12" width="115" height="22" rx="4" fill="#dc2626"/>
      <text x="801" y="27" text-anchor="middle" class="p2-badge-text" fill="#ffffff">NOT_MATCHED</text>
      <text x="870" y="28" class="p2-body-bold" fill="#991b1b">Uncorrelated / Error</text>
      <text x="744" y="56" class="p2-body-text">Proposal has no counterpart in the Final SRS,</text>
      <text x="744" y="72" class="p2-body-text">represented an extraneous modification, or</text>
      <text x="744" y="88" class="p2-body-bold" fill="#991b1b">Pipeline-1 execution encountered an error.</text>
    </g>
  </g>

  <!-- Connector: Evaluator -> Metrics Summary -->
  <path d="M 600 765 L 600 795" stroke="#475569" stroke-width="2" marker-end="url(#p2-arrow)"/>

  <!-- ==================== FORMAL EVALUATION METRICS BANNER ==================== -->
  <g transform="translate(40, 795)">
    <rect width="1120" height="135" rx="10" fill="#0f172a" filter="url(#p2-shadow)"/>
    
    <text x="24" y="30" class="p2-title" font-size="16">Benchmark Summary Analytics (Mathematically Bounded &amp; True-Negative Separated):</text>
    
    <g transform="translate(24, 46)">
      <!-- Metric 1: PMR_strict -->
      <rect width="205" height="66" rx="6" fill="#1e293b" stroke="#334155"/>
      <text x="12" y="20" class="p2-body-bold" fill="#38bdf8">Strict Match Rate (PMR_strict)</text>
      <text x="12" y="40" class="p2-code-text" fill="#e2e8f0">|R_prop ∩ R_MATCHED|</text>
      <line x1="12" y1="45" x2="150" y2="45" stroke="#64748b"/>
      <text x="12" y="58" class="p2-code-text" fill="#94a3b8">|R_prop|  (Active Proposals)</text>

      <!-- Metric 2: PMR_comb -->
      <rect x="220" y="0" width="215" height="66" rx="6" fill="#1e293b" stroke="#334155"/>
      <text x="232" y="20" class="p2-body-bold" fill="#38bdf8">Combined Match (PMR_comb)</text>
      <text x="232" y="40" class="p2-code-text" fill="#e2e8f0">|R_prop ∩ (R_M ∪ R_PART)|</text>
      <line x1="232" y1="45" x2="385" y2="45" stroke="#64748b"/>
      <text x="232" y="58" class="p2-code-text" fill="#94a3b8">|R_prop|  (Full + Partial)</text>

      <!-- Metric 3: QRR -->
      <rect x="450" y="0" width="205" height="66" rx="6" fill="#1e293b" stroke="#334155"/>
      <text x="462" y="20" class="p2-body-bold" fill="#4ade80">Quality Recall (QRR)</text>
      <text x="462" y="40" class="p2-code-text" fill="#e2e8f0">|R_prop ∩ H_qual ∩ R_M|</text>
      <line x1="462" y1="45" x2="600" y2="45" stroke="#64748b"/>
      <text x="462" y="58" class="p2-code-text" fill="#94a3b8">|H_qual|  (Final SRS Changes)</text>

      <!-- Metric 4: QRP -->
      <rect x="670" y="0" width="205" height="66" rx="6" fill="#1e293b" stroke="#334155"/>
      <text x="682" y="20" class="p2-body-bold" fill="#4ade80">Quality Precision (QRP)</text>
      <text x="682" y="40" class="p2-code-text" fill="#e2e8f0">|R_prop ∩ H_qual ∩ R_M|</text>
      <line x1="682" y1="45" x2="820" y2="45" stroke="#64748b"/>
      <text x="682" y="58" class="p2-code-text" fill="#94a3b8">|R_prop|  (Pipeline Output)</text>

      <!-- Metric 5: OEA -->
      <rect x="890" y="0" width="180" height="66" rx="6" fill="#1e293b" stroke="#334155"/>
      <text x="902" y="20" class="p2-body-bold" fill="#fbbf24">Overall Agreement (OEA)</text>
      <text x="902" y="40" class="p2-code-text" fill="#e2e8f0">|Matched| + |True_Negatives|</text>
      <line x1="902" y1="45" x2="1050" y2="45" stroke="#64748b"/>
      <text x="902" y="58" class="p2-code-text" fill="#94a3b8">|Total Requirements U|</text>
    </g>
  </g>

</svg>
"""


def build_dual_pipeline_overview_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 840" width="100%" height="100%">
  <defs>
    <filter id="m-shadow" x="-3%" y="-2%" width="106%" height="106%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <filter id="m-shadow-sm" x="-2%" y="-2%" width="104%" height="104%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.06"/>
    </filter>

    <linearGradient id="m-header-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="50%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>

    <marker id="m-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
    </marker>
    <marker id="m-arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb"/>
    </marker>
    <marker id="m-arrow-indigo" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#4f46e5"/>
    </marker>
    <marker id="m-arrow-emerald" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669"/>
    </marker>
  </defs>

  <style>
    .m-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 22px; font-weight: 700; fill: #ffffff; }
    .m-subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; font-weight: 400; fill: #94a3b8; }
    .m-card-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 15px; font-weight: 700; }
    .m-badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10.5px; font-weight: 700; }
    .m-body-bold { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 600; fill: #1e293b; }
    .m-body-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 400; fill: #334155; }
    .m-muted-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; font-weight: 400; fill: #64748b; }
    .m-code-text { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 10.5px; fill: #0f172a; }
  </style>

  <!-- Canvas Background -->
  <rect width="1440" height="840" fill="#f8fafc"/>

  <!-- Master Header -->
  <g transform="translate(40, 20)">
    <rect width="1360" height="74" rx="10" fill="url(#m-header-grad)" filter="url(#m-shadow)"/>
    <text x="28" y="34" class="m-title">Dual-Pipeline Architecture: Surgical Quality Analyzer &amp; Final SRS Ground Truth Benchmark</text>
    <text x="28" y="56" class="m-subtitle">System-Wide Separation of Concerns: In-Situ 5-Layer Staged Quality Analysis (Pipeline 1) &amp; Empirical Specification Evolution (Pipeline 2)</text>
    
    <rect x="1140" y="22" width="190" height="30" rx="15" fill="#1e1b4b" stroke="#6366f1" stroke-width="1.5"/>
    <text x="1235" y="41" text-anchor="middle" class="m-badge-text" fill="#c7d2fe">ISO 29148 • EARS • IEEE</text>
  </g>

  <!-- ==================== LEFT COLUMN: PIPELINE 1 (SURGICAL ANALYZER) ==================== -->
  <g transform="translate(40, 110)">
    <rect width="660" height="695" rx="10" fill="#ffffff" stroke="#bfdbfe" stroke-width="2" filter="url(#m-shadow-sm)"/>
    
    <!-- Header -->
    <rect width="660" height="40" rx="10" fill="#eff6ff"/>
    <rect x="16" y="8" width="95" height="24" rx="4" fill="#2563eb"/>
    <text x="63" y="24" text-anchor="middle" class="m-badge-text" fill="#ffffff">PIPELINE 1</text>
    <text x="125" y="25" class="m-card-title" fill="#1e3a8a">Surgical Requirements Quality Analyzer (5 Staged Layers)</text>

    <!-- Content: Inputs -->
    <g transform="translate(16, 52)">
      <rect width="628" height="54" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
      <text x="12" y="20" class="m-body-bold">Input Contract:</text>
      <text x="120" y="20" class="m-code-text" fill="#2563eb">Requirement(id, type, section, text) + SRSContext(domain, glossary, window±3, standards)</text>
      <text x="12" y="40" class="m-muted-text">Audits individual requirement in context without leaking future specification data.</text>
    </g>

    <!-- Layer 1 -->
    <g transform="translate(16, 118)">
      <rect width="628" height="88" rx="6" fill="#ffffff" stroke="#e2e8f0"/>
      <rect x="10" y="8" width="60" height="20" rx="3" fill="#dbeafe"/>
      <text x="40" y="22" text-anchor="middle" class="m-badge-text" fill="#1e40af">LAYER 1</text>
      <text x="80" y="23" class="m-body-bold" fill="#1e3a8a">Document Scorer (ISO 29148 7-Attribute Continuous Scoring)</text>
      <text x="10" y="46" class="m-body-text">• Unambiguity, Completeness, Consistency, Conformance, Correctness, Singularity, Verifiability</text>
      <text x="10" y="64" class="m-code-text" fill="#0369a1">Deterministic Q_req = Σ w_i · S(A_i) ∈ [0,10]  |  Shortcoming emitted if S(A_i) &lt; 8.0</text>
      <text x="10" y="80" class="m-muted-text">Emits D_L1 candidate defects (Zero filtering at this stage)</text>
    </g>

    <!-- Connector L1 -> L2 -->
    <path d="M 330 206 L 330 220" stroke="#475569" stroke-width="1.5" marker-end="url(#m-arrow)"/>

    <!-- Layer 2 -->
    <g transform="translate(16, 220)">
      <rect width="628" height="92" rx="6" fill="#ffffff" stroke="#fde68a"/>
      <rect x="10" y="8" width="60" height="20" rx="3" fill="#fef3c7"/>
      <text x="40" y="22" text-anchor="middle" class="m-badge-text" fill="#92400e">LAYER 2</text>
      <text x="80" y="23" class="m-body-bold" fill="#92400e">Defect Reasoner (Contextual False-Positive Suppression)</text>
      <text x="10" y="46" class="m-body-text">• Resolves the Contextual False-Positive Paradox via glossary, boundary &amp; neighbor cross-check.</text>
      <text x="10" y="66" class="m-body-text" fill="#7f1d1d">✕ Discarded: Resolved in surrounding context (FSR = |D_discarded| / |D_L1|) ➔ Terminated</text>
      <text x="10" y="84" class="m-body-bold" fill="#166534">✓ Retained: Genuine defects (D_retained) ➔ ONLY these proceed downstream</text>
    </g>

    <!-- Connector L2 -> L3 -->
    <path d="M 330 312 L 330 326" stroke="#475569" stroke-width="1.5" marker-end="url(#m-arrow)"/>

    <!-- Layer 3 -->
    <g transform="translate(16, 326)">
      <rect width="628" height="84" rx="6" fill="#ffffff" stroke="#ddd6fe"/>
      <rect x="10" y="8" width="60" height="20" rx="3" fill="#f5f3ff"/>
      <text x="40" y="22" text-anchor="middle" class="m-badge-text" fill="#6d28d9">LAYER 3</text>
      <text x="80" y="23" class="m-body-bold" fill="#5b21b6">Solution Generator (EARS-Compliant Surgical Refinement)</text>
      <text x="10" y="46" class="m-body-text">• Synthesizes minimal surgical edits: preserves system names, domain entities &amp; business intent.</text>
      <text x="10" y="64" class="m-body-text">• Applies EARS patterns (Ubiquitous, Event, State) to address ONLY retained defect IDs.</text>
      <text x="10" y="78" class="m-muted-text">Emits refined text, itemized changes, and intent preservation rationale.</text>
    </g>

    <!-- Connector L3 -> L4 -->
    <path d="M 330 410 L 330 424" stroke="#475569" stroke-width="1.5" marker-end="url(#m-arrow)"/>

    <!-- Layer 4 -->
    <g transform="translate(16, 424)">
      <rect width="628" height="88" rx="6" fill="#ffffff" stroke="#a7f3d0"/>
      <rect x="10" y="8" width="60" height="20" rx="3" fill="#ecfdf5"/>
      <text x="40" y="22" text-anchor="middle" class="m-badge-text" fill="#047857">LAYER 4</text>
      <text x="80" y="23" class="m-body-bold" fill="#065f46">Solution Validator (Fail-Closed Adversarial Critic)</text>
      <text x="10" y="46" class="m-body-text">• 5 Fail-Closed Checks: Defect Resolution • No Ambiguities • No Unwarranted Assumptions</text>
      <text x="10" y="62" class="m-body-text">  • Functional Intent Preservation • Syntactic Conformance</text>
      <text x="10" y="80" class="m-code-text" fill="#047857">Conjunctive Gating: V = ⋀ c_j  ➔ Fail-closed rejection if any check fails</text>
    </g>

    <!-- Connector L4 -> L5 -->
    <path d="M 330 512 L 330 526" stroke="#475569" stroke-width="1.5" marker-end="url(#m-arrow)"/>

    <!-- Layer 5 -->
    <g transform="translate(16, 526)">
      <rect width="628" height="84" rx="6" fill="#ffffff" stroke="#99f6e4"/>
      <rect x="10" y="8" width="60" height="20" rx="3" fill="#f0fdfa"/>
      <text x="40" y="22" text-anchor="middle" class="m-badge-text" fill="#0d9488">LAYER 5</text>
      <text x="80" y="23" class="m-body-bold" fill="#115e59">Decision Manager (Word Diff &amp; Review Governance)</text>
      <text x="10" y="46" class="m-body-text">• Generates punctuation-preserving word diff highlighting exact surgical replacements.</text>
      <text x="10" y="64" class="m-body-text">• Packages full chain-of-custody audit record for stakeholder sign-off.</text>
      <text x="10" y="78" class="m-code-text" fill="#0d9488">Emits PipelineExecutionResult(status="completed"|"error", proposal, time)</text>
    </g>

    <!-- Pipeline 1 Output Pill -->
    <g transform="translate(16, 624)">
      <rect width="628" height="54" rx="6" fill="#1e293b"/>
      <text x="14" y="22" class="m-body-bold" fill="#38bdf8">Pipeline 1 Resulting Proposal:</text>
      <text x="14" y="42" class="m-code-text" fill="#ffffff">R_prop = { u ∈ U | Refined(u) ≠ Original(u) ∧ Status = "completed" }</text>
    </g>
  </g>

  <!-- Master Connector: Pipeline 1 -> Pipeline 2 -->
  <path d="M 700 765 L 750 765 L 750 490 L 780 490" stroke="#4f46e5" stroke-width="2.5" fill="none" marker-end="url(#m-arrow-indigo)"/>
  <rect x="670" y="610" width="130" height="34" rx="6" fill="#e0e7ff" stroke="#818cf8"/>
  <text x="735" y="625" text-anchor="middle" class="m-badge-text" fill="#312e81">INDEPENDENT</text>
  <text x="735" y="638" text-anchor="middle" class="m-badge-text" fill="#312e81">PROPOSALS</text>

  <!-- ==================== RIGHT COLUMN: PIPELINE 2 (EMPIRICAL BENCHMARK) ==================== -->
  <g transform="translate(780, 110)">
    <rect width="620" height="695" rx="10" fill="#ffffff" stroke="#86efac" stroke-width="2" filter="url(#m-shadow-sm)"/>
    
    <!-- Header -->
    <rect width="620" height="40" rx="10" fill="#f0fdf4"/>
    <rect x="16" y="8" width="95" height="24" rx="4" fill="#16a34a"/>
    <text x="63" y="24" text-anchor="middle" class="m-badge-text" fill="#ffffff">PIPELINE 2</text>
    <text x="125" y="25" class="m-card-title" fill="#14532d">Empirical Evolution Benchmark vs Final SRS Release</text>

    <!-- Input Ground Truth -->
    <g transform="translate(16, 52)">
      <rect width="588" height="64" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>
      <text x="12" y="20" class="m-body-bold">Document Ground Truth Inputs:</text>
      <text x="12" y="38" class="m-body-text">• <tspan font-weight="600">Draft SRS (V_N):</tspan> Early specification evaluated blindly by Pipeline 1</text>
      <text x="12" y="54" class="m-body-bold" fill="#15803d">• Final Version of SRS (V_final / V_N+1): Official release ground truth</text>
    </g>

    <!-- Stage 1 & 2 Box -->
    <g transform="translate(16, 128)">
      <rect width="588" height="130" rx="6" fill="#ffffff" stroke="#e2e8f0"/>
      <text x="12" y="20" class="m-body-bold" fill="#0f172a">1. Structural Document Aligner (aligner.py)</text>
      <text x="12" y="38" class="m-body-text">• Two-Stage Alignment: Stage 1 Exact ID + Stage 2 Normalized Levenshtein</text>
      <text x="12" y="54" class="m-code-text" fill="#b91c1c">• Synthetic ID Isolation: Prevents unnumbered items collapsing into "REQ"</text>
      
      <line x1="12" y1="64" x2="576" y2="64" stroke="#e2e8f0"/>
      
      <text x="12" y="82" class="m-body-bold" fill="#0f172a">2. Evolutionary Change Classifier (change_classifier.py)</text>
      <text x="12" y="100" class="m-body-text">• 6 Exclusive Classes: Unchanged • Editorial • Scope Change • Added • Deleted</text>
      <text x="12" y="118" class="m-body-bold" fill="#15803d">• Quality Refinement: Ambiguity, Parameterization, Scope Clarification, Consistency</text>
    </g>

    <!-- Connector to Evaluator -->
    <path d="M 310 258 L 310 274" stroke="#475569" stroke-width="1.5" marker-end="url(#m-arrow)"/>

    <!-- Correspondence Evaluator -->
    <g transform="translate(16, 274)">
      <rect width="588" height="185" rx="6" fill="#f8fafc" stroke="#94a3b8"/>
      <text x="12" y="22" class="m-body-bold" fill="#0f172a">3. Semantic Correspondence Evaluator (evaluator.py)</text>
      <text x="12" y="40" class="m-muted-text">Chain-of-thought qualitative audit comparing Pipeline-1 proposal vs Final SRS text</text>

      <g transform="translate(12, 52)">
        <rect width="564" height="34" rx="4" fill="#f0fdf4" stroke="#86efac"/>
        <text x="10" y="21" class="m-body-bold" fill="#166534">MATCHED:</text>
        <text x="85" y="21" class="m-body-text">Independently anticipated semantically equivalent fix in Final SRS.</text>

        <rect y="40" width="564" height="34" rx="4" fill="#fffbeb" stroke="#fde68a"/>
        <text x="10" y="61" class="m-body-bold" fill="#92400e">PARTIALLY_MATCHED:</text>
        <text x="155" y="61" class="m-body-text">Targeted correct defect clause; alternative resolution.</text>

        <rect y="80" width="564" height="34" rx="4" fill="#fef2f2" stroke="#fca5a5"/>
        <text x="10" y="101" class="m-body-bold" fill="#991b1b">NOT_MATCHED:</text>
        <text x="110" y="101" class="m-body-text">Uncorrelated change, extraneous edit, or pipeline crash.</text>
      </g>
      
      <text x="12" y="174" class="m-code-text" fill="#475569">Fast Short-Circuits: Pipeline error ➔ NOT_MATCHED | Both unchanged ➔ MATCHED</text>
    </g>

    <!-- Connector to Metrics -->
    <path d="M 310 459 L 310 475" stroke="#475569" stroke-width="1.5" marker-end="url(#m-arrow)"/>

    <!-- Benchmark Summary Metrics -->
    <g transform="translate(16, 475)">
      <rect width="588" height="203" rx="6" fill="#0f172a"/>
      <text x="16" y="24" class="m-title" font-size="14">4. Bounded Benchmark Evaluation Metrics:</text>

      <g transform="translate(16, 38)">
        <!-- Strict Match -->
        <rect width="270" height="46" rx="4" fill="#1e293b"/>
        <text x="10" y="18" class="m-body-bold" fill="#38bdf8">Strict Match Rate (PMR_strict):</text>
        <text x="10" y="36" class="m-code-text" fill="#e2e8f0">|R_prop ∩ R_MATCHED| / |R_prop|</text>

        <!-- Combined Match -->
        <rect x="286" width="270" height="46" rx="4" fill="#1e293b"/>
        <text x="296" y="18" class="m-body-bold" fill="#38bdf8">Combined Match (PMR_comb):</text>
        <text x="296" y="36" class="m-code-text" fill="#e2e8f0">|R_prop ∩ (R_M ∪ R_PART)| / |R_prop|</text>

        <!-- Quality Recall -->
        <rect y="54" width="270" height="46" rx="4" fill="#1e293b"/>
        <text x="10" y="72" class="m-body-bold" fill="#4ade80">Quality Refinement Recall (QRR):</text>
        <text x="10" y="90" class="m-code-text" fill="#e2e8f0">|R_prop ∩ H_qual ∩ R_M| / |H_qual|</text>

        <!-- Quality Precision -->
        <rect x="286" y="54" width="270" height="46" rx="4" fill="#1e293b"/>
        <text x="296" y="72" class="m-body-bold" fill="#4ade80">Quality Precision (QRP):</text>
        <text x="296" y="90" class="m-code-text" fill="#e2e8f0">|R_prop ∩ H_qual ∩ R_M| / |R_prop|</text>

        <!-- Overall Agreement -->
        <rect y="108" width="556" height="46" rx="4" fill="#1e293b"/>
        <text x="10" y="126" class="m-body-bold" fill="#fbbf24">Overall Evolutionary Agreement (OEA):</text>
        <text x="10" y="144" class="m-code-text" fill="#e2e8f0">(|R_prop ∩ R_MATCHED| + |U_TN|) / |U|  [True Negatives strictly separated]</text>
      </g>
    </g>
  </g>

</svg>
"""


def main():
    p1_svg = build_pipeline1_svg()
    p2_svg = build_pipeline2_svg()
    master_svg = build_dual_pipeline_overview_svg()

    # Validate XML parsing
    ET.fromstring(p1_svg)
    ET.fromstring(p2_svg)
    ET.fromstring(master_svg)

    p1_path = FIGURES_DIR / "pipeline1_architecture.svg"
    p2_path = FIGURES_DIR / "pipeline2_architecture.svg"
    master_path = FIGURES_DIR / "dual_pipeline_overview.svg"

    p1_path.write_text(p1_svg, encoding="utf-8")
    p2_path.write_text(p2_svg, encoding="utf-8")
    master_path.write_text(master_svg, encoding="utf-8")

    print(f"Successfully generated: {p1_path}")
    print(f"Successfully generated: {p2_path}")
    print(f"Successfully generated: {master_path}")


if __name__ == "__main__":
    main()

