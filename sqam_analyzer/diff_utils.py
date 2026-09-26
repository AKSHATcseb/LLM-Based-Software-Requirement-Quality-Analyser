"""
sqam_analyzer.diff_utils
~~~~~~~~~~~~~~~~~~~~~~~~
Diffing and text comparison utilities for comparing original and refined requirements.
Generates word-level inline diffs, ANSI-colored diffs for terminals, and structured
change statistics.
"""

from __future__ import annotations

import difflib
import re
from typing import Tuple
from sqam_analyzer.models import TextDiff


def compute_word_diff(original: str, refined: str) -> TextDiff:
    """
    Computes a word-level diff between original and refined requirement strings.
    Produces markup where deletions are indicated as `[-deleted word-]` and
    additions as `[+added word+]`.
    """
    # Tokenize words while preserving punctuation and spacing
    orig_tokens = re.findall(r"\w+|\S", original)
    ref_tokens = re.findall(r"\w+|\S", refined)

    matcher = difflib.SequenceMatcher(None, orig_tokens, ref_tokens)
    diff_parts = []
    changed_words = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            diff_parts.append(" ".join(orig_tokens[i1:i2]))
        elif tag == "delete":
            deleted = " ".join(orig_tokens[i1:i2])
            diff_parts.append(f"[-{deleted}-]")
            changed_words += (i2 - i1)
        elif tag == "insert":
            added = " ".join(ref_tokens[j1:j2])
            diff_parts.append(f"[+{added}+]")
            changed_words += (j2 - j1)
        elif tag == "replace":
            deleted = " ".join(orig_tokens[i1:i2])
            added = " ".join(ref_tokens[j1:j2])
            diff_parts.append(f"[-{deleted}-] [+{added}+]")
            changed_words += (i2 - i1) + (j2 - j1)

    diff_markup = " ".join(diff_parts)
    # Clean up double spaces
    diff_markup = re.sub(r"\s+", " ", diff_markup).strip()

    return TextDiff(
        original=original,
        refined=refined,
        diff_markup=diff_markup,
        changed_words_count=changed_words,
    )


def format_ansi_diff(original: str, refined: str) -> str:
    """
    Produces ANSI colored terminal output for diffs.
    Deletions are rendered in red strikethrough, additions in bright green.
    """
    RED = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"
    STRIKE = "\033[9m"

    orig_tokens = re.findall(r"\w+|\S", original)
    ref_tokens = re.findall(r"\w+|\S", refined)

    matcher = difflib.SequenceMatcher(None, orig_tokens, ref_tokens)
    parts = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            parts.append(" ".join(orig_tokens[i1:i2]))
        elif tag == "delete":
            deleted = " ".join(orig_tokens[i1:i2])
            parts.append(f"{RED}{STRIKE}{deleted}{RESET}")
        elif tag == "insert":
            added = " ".join(ref_tokens[j1:j2])
            parts.append(f"{GREEN}{added}{RESET}")
        elif tag == "replace":
            deleted = " ".join(orig_tokens[i1:i2])
            added = " ".join(ref_tokens[j1:j2])
            parts.append(f"{RED}{STRIKE}{deleted}{RESET} {GREEN}{added}{RESET}")

    return re.sub(r"\s+", " ", " ".join(parts)).strip()
