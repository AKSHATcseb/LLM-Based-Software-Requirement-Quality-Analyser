"""
scripts/sample_requirements.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generates a deterministic, reproducible, stratified sample of 480 requirements
(51.0% of the 942-requirement corpus), ensuring all 15 projects and 43 versions
are represented, while forming a strict superset of the original 215 requirements.
"""

import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from srs_evolution.aligner import SRSParser

RANDOM_SEED = 42
TOTAL_TARGET = 480

TABLE1_EXTRACTED = {
    "1_FROG": 108,
    "2_SMIRK": 12,
    "3_ONEM": 74,
    "4_UIC": 142,
    "5_EVLA BACKEND SYSTEM REQUIREMENTS": 65,
    "6": 89,
    "7": 44,
    "8": 51,
    "9": 38,
    "10": 58,
    "11": 62,
    "12": 49,
    "13": 43,
    "14": 52,
    "15": 55,
}

ORIGINAL_COUNTS = {
    "1_FROG": 10,
    "2_SMIRK": 10,
    "3_ONEM": 25,
    "4_UIC": 25,
    "5_EVLA BACKEND SYSTEM REQUIREMENTS": 10,
    "6": 30,
    "7": 10,
    "8": 15,
    "9": 10,
    "10": 10,
    "11": 10,
    "12": 10,
    "13": 10,
    "14": 15,
    "15": 15,
}


def build_sample_manifest():
    rng = random.Random(RANDOM_SEED)
    srs_dir = Path("srs doc versions")
    orig_csv = Path("results/original_215/layer1_multi_project_evaluation_results.csv")
    if not orig_csv.exists():
        orig_csv = Path("layer1_multi_project_evaluation_results.csv")

    df_orig = pd.read_csv(orig_csv)
    parser = SRSParser()

    # Calculate proportional allocation of the delta (480 - 215 = 265)
    needed = TOTAL_TARGET - sum(ORIGINAL_COUNTS.values())
    total_t1 = sum(TABLE1_EXTRACTED.values())

    raw_alloc = {p: (TABLE1_EXTRACTED[p] / total_t1) * needed for p in TABLE1_EXTRACTED}
    base_alloc = {p: int(raw_alloc[p]) for p in TABLE1_EXTRACTED}
    remainder = {p: raw_alloc[p] - base_alloc[p] for p in TABLE1_EXTRACTED}
    shortfall = needed - sum(base_alloc.values())

    for p, _ in sorted(remainder.items(), key=lambda x: x[1], reverse=True)[:shortfall]:
        base_alloc[p] += 1

    manifest_records: List[Dict[str, Any]] = []
    project_manifest_stats: Dict[str, Any] = {}

    # Extract all original requirements grouped by (project, version_file)
    orig_by_file: Dict[tuple, List[Dict[str, Any]]] = {}
    for _, row in df_orig.iterrows():
        key = (row["project"], row["version_file"])
        orig_by_file.setdefault(key, []).append(row.to_dict())

    # Pre-parse documents
    for proj_name, delta_needed in base_alloc.items():
        proj_dir = srs_dir / proj_name
        version_files = sorted(
            [f for f in proj_dir.iterdir() if f.suffix.lower() in [".pdf", ".md"]],
            key=lambda x: x.name,
        )

        proj_orig_records: List[Dict[str, Any]] = []
        proj_available_candidates: List[Dict[str, Any]] = []

        for vf in version_files:
            vstem = vf.stem
            units = parser.parse_document(vf, version_label=vstem)
            orig_in_vf = orig_by_file.get((proj_name, vf.name), [])
            orig_texts = {r["requirement_text"].strip(): r for r in orig_in_vf}

            for r in orig_in_vf:
                proj_orig_records.append({
                    "project": proj_name,
                    "version_file": vf.name,
                    "version_stem": vstem,
                    "req_id": r["req_id"],
                    "requirement_text": r["requirement_text"].strip(),
                    "is_original_215": True,
                })

            for u in units:
                u_text = u.text.strip()
                if u_text not in orig_texts:
                    proj_available_candidates.append({
                        "project": proj_name,
                        "version_file": vf.name,
                        "version_stem": vstem,
                        "req_id": u.req_id,
                        "requirement_text": u_text,
                        "is_original_215": False,
                    })

        # Deterministically sample delta_needed from candidates
        rng.shuffle(proj_available_candidates)
        if len(proj_available_candidates) < delta_needed:
            raise RuntimeError(
                f"Project {proj_name} has only {len(proj_available_candidates)} candidates, needed {delta_needed}"
            )
        sampled_additional = proj_available_candidates[:delta_needed]

        combined_proj = proj_orig_records + sampled_additional
        manifest_records.extend(combined_proj)

        project_manifest_stats[proj_name] = {
            "table1_extracted": TABLE1_EXTRACTED[proj_name],
            "original_215_count": len(proj_orig_records),
            "additional_sampled_count": len(sampled_additional),
            "total_sampled": len(combined_proj),
            "sampling_fraction_of_extracted": round(len(combined_proj) / TABLE1_EXTRACTED[proj_name], 3),
        }

    # Add 1..N sample_id and assign 20 pilot requirements spread across all 15 projects
    # 1 from each of the 15 projects (15 items) + 1 additional from 5 largest projects (5 items) = 20 items
    largest_5 = [p for p, _ in sorted(TABLE1_EXTRACTED.items(), key=lambda x: x[1], reverse=True)[:5]]
    pilot_targets = {p: (2 if p in largest_5 else 1) for p in TABLE1_EXTRACTED}
    pilot_counts = {p: 0 for p in TABLE1_EXTRACTED}

    # Deterministic pilot selection
    pilot_rng = random.Random(RANDOM_SEED + 100)
    indices = list(range(len(manifest_records)))
    pilot_rng.shuffle(indices)

    pilot_assigned = 0
    for idx in indices:
        rec = manifest_records[idx]
        p = rec["project"]
        if pilot_counts[p] < pilot_targets[p] and pilot_assigned < 20:
            rec["is_pilot_sample"] = True
            pilot_counts[p] += 1
            pilot_assigned += 1
        else:
            rec["is_pilot_sample"] = False

    for idx, rec in enumerate(manifest_records, start=1):
        rec["sample_id"] = idx

    manifest_data = {
        "metadata": {
            "random_seed": RANDOM_SEED,
            "total_corpus_extracted": total_t1,
            "total_requirements_sampled": len(manifest_records),
            "percentage_of_corpus": round((len(manifest_records) / total_t1) * 100, 2),
            "target_threshold": ">= 471 requirements (50.0% of 942)",
            "methodology": "Stratified proportional sampling superset with fixed seed (Largest Remainder Hare-Niemeyer)",
            "original_215_count": sum(1 for r in manifest_records if r["is_original_215"]),
            "new_additions_count": sum(1 for r in manifest_records if not r["is_original_215"]),
            "pilot_sample_count": sum(1 for r in manifest_records if r["is_pilot_sample"]),
        },
        "per_project_allocation": project_manifest_stats,
        "requirements": manifest_records,
    }

    out_path = Path("results/sample_manifest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"Sample manifest successfully generated at {out_path}:")
    print(f"  Total Sampled: {len(manifest_records)} ({manifest_data['metadata']['percentage_of_corpus']}%)")
    print(f"  Original 215 preserved: {manifest_data['metadata']['original_215_count']}")
    print(f"  New additions: {manifest_data['metadata']['new_additions_count']}")
    print(f"  Pilot sample: {manifest_data['metadata']['pilot_sample_count']}")


if __name__ == "__main__":
    build_sample_manifest()
