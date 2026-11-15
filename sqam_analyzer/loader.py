"""
sqam_analyzer.loader
~~~~~~~~~~~~~~~~~~~~
Loader utilities to parse external SRS datasets (JSON, PDF, Markdown) into typed
SRSContext and Requirement models for analysis in Pipeline 1.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sqam_analyzer.models import Requirement, SRSContext


def load_srs_from_json(file_path: str | Path) -> Tuple[SRSContext, List[Requirement]]:
    """
    Parses a JSON file into an SRSContext and a list of Requirement objects.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"SRS file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        req_dicts = data
        context = SRSContext(
            document_title=path.stem.replace("_", " ").title() + " SRS",
            domain_summary="General software requirements specification loaded from file.",
            glossary={},
            surrounding_requirements=[],
            applicable_standards=["ISO/IEC/IEEE 29148:2018"],
        )
    elif isinstance(data, dict):
        req_dicts = data.get("requirements") or data.get("reqs") or data.get("items") or []
        if not isinstance(req_dicts, list):
            raise ValueError(f"Expected 'requirements' field to be a list in {path.name}")

        context = SRSContext(
            document_title=data.get("document_title") or (path.stem.replace("_", " ").title() + " SRS"),
            domain_summary=data.get("domain_summary") or "Custom software requirements specification.",
            glossary=data.get("glossary") or {},
            surrounding_requirements=data.get("surrounding_requirements") or [],
            applicable_standards=data.get("applicable_standards") or ["ISO/IEC/IEEE 29148:2018"],
        )
    else:
        raise ValueError(f"Invalid JSON format in {path.name}: Root must be an object or a list.")

    requirements: List[Requirement] = []
    for idx, item in enumerate(req_dicts, start=1):
        if not isinstance(item, dict):
            continue
        req_id = item.get("req_id") or item.get("id") or f"REQ-{idx:03d}"
        text = item.get("text") or item.get("statement") or item.get("description") or item.get("requirement") or ""
        req_type = item.get("req_type") or item.get("type") or "Functional"
        section = item.get("section") or item.get("module") or None

        if not text:
            continue

        requirements.append(
            Requirement(
                req_id=str(req_id),
                text=str(text),
                req_type=str(req_type),
                section=str(section) if section else None,
            )
        )

    if not requirements:
        raise ValueError(f"No valid requirements found in {path.name}.")

    return context, requirements


def clean_pdf_text(text: str) -> str:
    """Removes private use Unicode glyphs and replaces bullet characters with ASCII hyphens."""
    if not text:
        return ""
    replacements = {
        "\uf0b7": "-",
        "\uf0a7": "-",
        "\uf0d8": "-",
        "\u2022": "-",
        "\u25cf": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb00": "ff",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    cleaned = "".join(c if not (0xE000 <= ord(c) <= 0xF8FF) else "" for c in text)
    return " ".join(cleaned.split())


def load_srs_from_document(file_path: str | Path) -> Tuple[SRSContext, List[Requirement]]:
    """
    Extracts text and normative requirements from a PDF or Markdown file.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Document file not found: {path.resolve()}")

    from build_dataset import extract_candidate_requirements, extract_text_from_file

    doc_text = extract_text_from_file(path)
    extracted_req_texts = extract_candidate_requirements(doc_text)
    if not extracted_req_texts:
        raise ValueError(f"No normative requirement statements ('shall' / 'must') found in {path.name}.")

    project_name = path.stem.replace("_", " ").title()

    glossary: Dict[str, str] = {}
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
                    glossary[clean_pdf_text(term)] = clean_pdf_text(defn)

    summary_snippet = " ".join([l.strip() for l in lines[10:35] if l.strip()])[:350]
    domain_summary = clean_pdf_text(summary_snippet) or f"Software Requirements Specification for {project_name}."

    context = SRSContext(
        document_title=f"SRS Specification - {project_name}",
        domain_summary=domain_summary,
        glossary=glossary,
        applicable_standards=["ISO/IEC/IEEE 29148:2018"],
    )

    requirements = [
        Requirement(
            req_id=f"{path.stem.upper()}-REQ-{idx:03d}",
            text=clean_pdf_text(text),
            req_type="Functional",
            section="Extracted from SRS Document",
        )
        for idx, text in enumerate(extracted_req_texts, start=1)
    ]

    return context, requirements


def load_srs_any(file_path: str | Path) -> Tuple[SRSContext, List[Requirement]]:
    """
    Intelligently loads an SRS from JSON, PDF, or Markdown file.
    If the file path is not found in CWD, automatically searches `srs doc versions/`.
    """
    path = Path(file_path)
    if not path.is_file():
        # Check inside 'srs doc versions/'
        candidate = Path("srs doc versions") / file_path
        if candidate.is_file():
            path = candidate
        else:
            # Recursive search in 'srs doc versions/' by name
            matches = list(Path("srs doc versions").rglob(path.name))
            if not matches:
                # Fuzzy search by keywords (e.g. 'onem4' -> 3_ONEM V4 file)
                query = str(file_path).lower().replace(" ", "").replace("_", "").replace("-", "")
                all_files = [
                    f for f in Path("srs doc versions").rglob("*")
                    if f.is_file() and f.suffix.lower() in [".pdf", ".md", ".json"]
                ]
                for f in all_files:
                    norm = (f.parent.name + f.name).lower().replace(" ", "").replace("_", "").replace("-", "")
                    if query in norm or all(part in norm for part in ["onem", "4"] if "onem" in query and "4" in query):
                        matches.append(f)
            if matches:
                path = matches[0]
            else:
                raise FileNotFoundError(f"SRS file not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".json":
        return load_srs_from_json(path)
    elif ext in [".pdf", ".md", ".txt"]:
        return load_srs_from_document(path)
    else:
        raise ValueError(f"Unsupported file format '{ext}' for {path.name}. Supported formats: .json, .pdf, .md, .txt")
