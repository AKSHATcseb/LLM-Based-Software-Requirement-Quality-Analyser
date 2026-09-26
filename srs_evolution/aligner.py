"""
srs_evolution.aligner
~~~~~~~~~~~~~~~~~~~~~
Ingestion, parsing, and alignment engine for comparing chronological SRS versions.
Extracts requirement units from PDF, Markdown, and text documents, and aligns them across
Version N and Version N+1 using explicit ID matching, TF-IDF cosine similarity, and
token overlap heuristics.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from srs_evolution.models import (
    AlignedRequirementPair,
    AlignmentType,
    RequirementUnit,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regular Expressions for Requirement Identification
# ---------------------------------------------------------------------------

# Common SRS tag patterns: REQ-01, SYS-SAF-REQ1, FR-12, SR-3.2, F29, etc.
REQ_TAG_PATTERN = re.compile(
    r"(?:^|[\s\*\-\[\(])"
    r"((?:REQ|SYS|SAF|SEC|PERF|FUNC|FR|SR|F|BR|CR)[-_]?(?:[A-Z]+[-_])?[0-9]+[a-zA-Z0-9\.]*)"
    r"(?:[:\]\)\*\s-]|$)",
    re.IGNORECASE,
)

SECTION_HEADING_PATTERN = re.compile(
    r"^(?:#{1,6}\s+|(?:\d+\.)+\d*\s+|[A-Z][0-9A-Za-z\s]{3,40}:)\s*(.+)$"
)

NORMATIVE_VERB_PATTERN = re.compile(
    r"\b(shall|shall not|must|must not|will|should)\b",
    re.IGNORECASE,
)


class SRSParser:
    """
    Parses natural language SRS documents (PDF, Markdown, or raw text)
    into structured RequirementUnit objects.
    """

    def __init__(self, doc_prefix: str = "REQ"):
        self.doc_prefix = doc_prefix

    def parse_document(
        self,
        source: Union[str, Path],
        version_label: str = "N",
    ) -> List[RequirementUnit]:
        """
        Parses a document file or raw text string into a list of RequirementUnits.
        """
        if isinstance(source, Path) or (isinstance(source, str) and (source.endswith(".pdf") or source.endswith(".md") or source.endswith(".txt")) and "\n" not in source):
            text = self._read_file(Path(source))
        else:
            text = str(source)

        return self.parse_text(text, version_label=version_label)

    def _read_file(self, file_path: Path) -> str:
        """Reads text from PDF, Markdown, or plain text."""
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(file_path)
                return "\n\n".join(page.get_text() for page in doc)
            except ImportError:
                raise ImportError("PyMuPDF (fitz) is required to read PDFs. Install with: pip install pymupdf")
        elif ext in [".md", ".txt"]:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        else:
            return file_path.read_text(encoding="utf-8", errors="ignore")

    def parse_text(
        self,
        text: str,
        version_label: str = "N",
    ) -> List[RequirementUnit]:
        """
        Extracts discrete requirement units from raw text.
        Tracks active section titles and extracts or assigns requirement identifiers.
        """
        lines = text.splitlines()
        requirements: List[RequirementUnit] = []
        current_section = "General Requirements"
        synthetic_counter = 1

        # Buffer for multi-line requirement accumulation
        current_block: List[str] = []
        block_start_line = 0

        for line_idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                if current_block:
                    self._process_candidate_block(
                        "\n".join(current_block),
                        block_start_line,
                        current_section,
                        version_label,
                        requirements,
                        synthetic_counter,
                    )
                    if len(requirements) >= synthetic_counter:
                        synthetic_counter = len(requirements) + 1
                    current_block = []
                continue

            # Check if this line is a section heading
            heading_match = SECTION_HEADING_PATTERN.match(line)
            if heading_match and not NORMATIVE_VERB_PATTERN.search(line):
                if current_block:
                    self._process_candidate_block(
                        "\n".join(current_block),
                        block_start_line,
                        current_section,
                        version_label,
                        requirements,
                        synthetic_counter,
                    )
                    if len(requirements) >= synthetic_counter:
                        synthetic_counter = len(requirements) + 1
                    current_block = []
                current_section = heading_match.group(1).strip("#* ")
                continue

            if not current_block:
                block_start_line = line_idx
            current_block.append(line)

        # Flush final block
        if current_block:
            self._process_candidate_block(
                "\n".join(current_block),
                block_start_line,
                current_section,
                version_label,
                requirements,
                synthetic_counter,
            )

        logger.info(
            "Parsed %d requirements from Version %s (prefix=%s)",
            len(requirements),
            version_label,
            self.doc_prefix,
        )
        return requirements

    def _process_candidate_block(
        self,
        block_text: str,
        line_num: int,
        section: str,
        version_label: str,
        output_list: List[RequirementUnit],
        synthetic_index: int,
    ) -> None:
        """Tests if a block contains normative requirement statements and extracts them."""
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\-\*])", block_text.replace("\n", " "))

        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue

            # Must contain a normative auxiliary verb
            if NORMATIVE_VERB_PATTERN.search(s_clean):
                # Filter out boilerplate sentences
                lower_s = s_clean.lower()
                if any(boilerplate in lower_s for boilerplate in [
                    "this standard specifies",
                    "copyright",
                    "all rights reserved",
                    "the following table",
                ]):
                    continue

                if len(s_clean) < 25:
                    continue

                # Search for explicit ID tag in sentence or block
                tag_match = REQ_TAG_PATTERN.search(s_clean)
                raw_header = None

                if tag_match:
                    req_id = tag_match.group(1).upper()
                    raw_header = tag_match.group(0).strip(" *:-[]()")
                else:
                    req_id = f"{self.doc_prefix}-{version_label}-{synthetic_index:03d}"

                # Clean leading markdown bullets/bold formatting
                cleaned_text = re.sub(r"^[\*\-\s]+", "", s_clean)
                cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

                output_list.append(
                    RequirementUnit(
                        req_id=req_id,
                        text=cleaned_text,
                        section=section,
                        version=version_label,
                        line_number=line_num,
                        raw_header=raw_header,
                    )
                )


# ---------------------------------------------------------------------------
# Alignment Engine
# ---------------------------------------------------------------------------

class RequirementAligner:
    """
    Aligns requirements between Version N (earlier) and Version N+1 (later).
    Combines exact ID matching with TF-IDF cosine similarity fallback.
    """

    def __init__(self, similarity_threshold: float = 0.45):
        self.similarity_threshold = similarity_threshold

    def align(
        self,
        v1_reqs: List[RequirementUnit],
        v2_reqs: List[RequirementUnit],
    ) -> List[AlignedRequirementPair]:
        """
        Executes multi-stage alignment between Version N and Version N+1:
        1. Exact ID match
        2. Semantic TF-IDF similarity match for unaligned units
        3. Identifies Added (only in v2) and Deleted (only in v1) units
        """
        aligned_pairs: List[AlignedRequirementPair] = []

        unmatched_v1 = list(v1_reqs)
        unmatched_v2 = list(v2_reqs)

        # -------------------------------------------------------------------
        # Stage 1: Exact ID Matching
        # -------------------------------------------------------------------
        # Build lookup table for v2 requirements by normalized ID
        v2_by_id = {}
        for r2 in unmatched_v2:
            norm_id = self._normalize_id(r2.req_id)
            if norm_id:
                v2_by_id.setdefault(norm_id, []).append(r2)

        matched_v1_ids = set()
        matched_v2_ids = set()

        for r1 in unmatched_v1:
            norm_id = self._normalize_id(r1.req_id)
            # Only match if it's a real explicit tag (not a generic synthetic ID)
            if norm_id and norm_id in v2_by_id and not norm_id.startswith("REQ-N-"):
                candidate_v2 = v2_by_id[norm_id][0]
                matched_v1_ids.add(r1.req_id)
                matched_v2_ids.add(candidate_v2.req_id)

                aligned_pairs.append(
                    AlignedRequirementPair(
                        req_id_v1=r1.req_id,
                        req_id_v2=candidate_v2.req_id,
                        text_v1=r1.text,
                        text_v2=candidate_v2.text,
                        section_v1=r1.section,
                        section_v2=candidate_v2.section,
                        alignment_confidence=1.0,
                        alignment_type=AlignmentType.IDENTICAL_ID,
                    )
                )

        unmatched_v1 = [r for r in unmatched_v1 if r.req_id not in matched_v1_ids]
        unmatched_v2 = [r for r in unmatched_v2 if r.req_id not in matched_v2_ids]

        # -------------------------------------------------------------------
        # Stage 2: Fallback Semantic Matching (TF-IDF + Cosine Similarity)
        # -------------------------------------------------------------------
        if unmatched_v1 and unmatched_v2:
            v1_texts = [r.text for r in unmatched_v1]
            v2_texts = [r.text for r in unmatched_v2]

            try:
                vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
                all_texts = v1_texts + v2_texts
                tfidf_matrix = vectorizer.fit_transform(all_texts)

                v1_matrix = tfidf_matrix[: len(v1_texts)]
                v2_matrix = tfidf_matrix[len(v1_texts) :]

                sim_matrix = cosine_similarity(v1_matrix, v2_matrix)

                used_v1_indices = set()
                used_v2_indices = set()

                # Greedy matching in descending order of similarity
                flat_indices = np.argsort(-sim_matrix, axis=None)
                for idx in flat_indices:
                    i, j = np.unravel_index(idx, sim_matrix.shape)
                    score = float(sim_matrix[i, j])

                    if score < self.similarity_threshold:
                        break

                    if i in used_v1_indices or j in used_v2_indices:
                        continue

                    r1 = unmatched_v1[i]
                    r2 = unmatched_v2[j]

                    used_v1_indices.add(i)
                    used_v2_indices.add(j)

                    aligned_pairs.append(
                        AlignedRequirementPair(
                            req_id_v1=r1.req_id,
                            req_id_v2=r2.req_id,
                            text_v1=r1.text,
                            text_v2=r2.text,
                            section_v1=r1.section,
                            section_v2=r2.section,
                            alignment_confidence=round(score, 3),
                            alignment_type=AlignmentType.SEMANTIC_MATCH,
                        )
                    )

                unmatched_v1 = [r for idx, r in enumerate(unmatched_v1) if idx not in used_v1_indices]
                unmatched_v2 = [r for idx, r in enumerate(unmatched_v2) if idx not in used_v2_indices]

            except Exception as e:
                logger.warning("Semantic TF-IDF alignment encountered error (%s); proceeding with unaligned.", e)

        # -------------------------------------------------------------------
        # Stage 3: Unmatched Units (Deleted in N, Added in N+1)
        # -------------------------------------------------------------------
        for r1 in unmatched_v1:
            aligned_pairs.append(
                AlignedRequirementPair(
                    req_id_v1=r1.req_id,
                    req_id_v2=None,
                    text_v1=r1.text,
                    text_v2=None,
                    section_v1=r1.section,
                    section_v2=None,
                    alignment_confidence=1.0,
                    alignment_type=AlignmentType.DELETED,
                )
            )

        for r2 in unmatched_v2:
            aligned_pairs.append(
                AlignedRequirementPair(
                    req_id_v1=None,
                    req_id_v2=r2.req_id,
                    text_v1=None,
                    text_v2=r2.text,
                    section_v1=None,
                    section_v2=r2.section,
                    alignment_confidence=1.0,
                    alignment_type=AlignmentType.ADDED,
                )
            )

        logger.info(
            "Alignment complete: %d total aligned pairs (%d identical ID, %d semantic match, %d deleted, %d added)",
            len(aligned_pairs),
            sum(1 for p in aligned_pairs if p.alignment_type == AlignmentType.IDENTICAL_ID),
            sum(1 for p in aligned_pairs if p.alignment_type == AlignmentType.SEMANTIC_MATCH),
            sum(1 for p in aligned_pairs if p.alignment_type == AlignmentType.DELETED),
            sum(1 for p in aligned_pairs if p.alignment_type == AlignmentType.ADDED),
        )
        return aligned_pairs

    def _normalize_id(self, req_id: Optional[str]) -> str:
        """Normalizes ID by stripping version indicators and punctuation."""
        if not req_id:
            return ""
        # Strip common version prefixes like "-V1", "-V2", "_v1.1"
        cleaned = re.sub(r"[-_]V[0-9]+.*$", "", req_id, flags=re.IGNORECASE)
        cleaned = re.sub(r"[^A-Za-z0-9]", "", cleaned).upper()
        return cleaned
