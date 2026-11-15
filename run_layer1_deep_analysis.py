"""
Layer 1 Deep-Behaviour Analysis Script
Runs all 942 requirements through Layer 1 only and prints a detailed log
of exactly what the scorer returns for every single requirement.
"""
import sys, time, csv, json
from pathlib import Path
sys.path.insert(0, '.')

from sqam_analyzer import Layer1DocumentScorer, Requirement, SRSContext, resolve_llm_client
from srs_evolution.aligner import SRSParser

THRESHOLD = 8.0
WEIGHTS   = {"unambiguity":0.20,"completeness":0.20,"consistency":0.15,
             "conformance":0.10,"correctness":0.15,"singularity":0.10,"verifiability":0.10}
ATTRS     = list(WEIGHTS.keys())


def get_attr(out, name: str, fallback: float) -> float:
    """Extract a per-attribute score from Layer1Output.attribute_scores list."""
    attr_dict = {a.attribute.value.lower(): a.score for a in out.attribute_scores}
    return round(attr_dict.get(name, fallback), 2)


def run():
    client   = resolve_llm_client(provider="mock", allow_mock=True)
    scorer   = Layer1DocumentScorer(llm_client=client)

    manifest_path = Path("results/sample_manifest.json")
    if not manifest_path.exists():
        manifest_path = Path("sample_manifest.json")

    all_req_records = []
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            m_data = json.load(f)
            all_req_records = m_data.get("requirements", [])

    total_count = len(all_req_records) if all_req_records else 942

    print(f"\n{'='*95}")
    print(f"  LAYER 1 DEEP BEHAVIOUR LOG — ALL {total_count} REQUIREMENTS")
    print(f"  Backend: MockLLMClient  |  Temp=0.0  |  Defect threshold < {THRESHOLD}")
    print(f"{'='*95}")

    all_results  = []
    flagged_reqs = []
    req_counter  = 0

    print(f"\n  {'#':>4}  {'REQ-ID':<26} {'Score':>5}  "
          f"{'Unamb':>5} {'Compl':>5} {'Cons':>5} {'Conf':>5} "
          f"{'Corr':>5} {'Sing':>5} {'Veri':>5}  Status")
    print("  " + "─" * 90)

    for rec in all_req_records:
        req_counter += 1
        req_id = rec.get("req_id", f"REQ-{req_counter:04d}")
        req_text = rec.get("requirement_text", "")
        proj_name = rec.get("project", "Unknown")
        v_stem = rec.get("version_stem", "v1")
        vf_name = rec.get("version_file", f"{v_stem}.pdf")

        req_obj = Requirement(
            req_id=req_id,
            text=req_text,
            section=rec.get("section", "Functional Specifications")
        )
        ctx = SRSContext(
            document_title=f"{proj_name} — {v_stem}",
            domain_summary=f"Automated quality evaluation for {proj_name}.",
            glossary={},
        )

        t0 = time.perf_counter()
        out = scorer.execute(requirement=req_obj, srs_context=ctx)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        overall = round(out.overall_quality_score, 2)
        defects = out.shortcomings
        fallback = overall

        unamb = get_attr(out, "unambiguity", fallback)
        compl = get_attr(out, "completeness", fallback)
        cons  = get_attr(out, "consistency",  fallback)
        conf  = get_attr(out, "conformance",  fallback)
        corr  = get_attr(out, "correctness",  fallback)
        sing  = get_attr(out, "singularity",  fallback)
        veri  = get_attr(out, "verifiability",fallback)

        flagged_attrs = [a for a, v in {
            "Unamb": unamb,"Compl": compl,"Cons": cons,"Conf": conf,
            "Corr": corr,"Sing": sing,"Veri": veri}.items() if v < THRESHOLD]

        is_flagged = len(defects) > 0
        status = f"⚠ FLAGGED [{','.join(flagged_attrs)}]" if is_flagged else "✓ CLEAN"

        if req_counter <= 40 or req_counter % 50 == 0 or is_flagged:
            print(f"  {req_counter:>4}.  {req_obj.req_id:<26} {overall:>5.1f}  "
                  f"{unamb:>5.1f} {compl:>5.1f} {cons:>5.1f} {conf:>5.1f} "
                  f"{corr:>5.1f} {sing:>5.1f} {veri:>5.1f}  {status}")

        row = dict(
            seq=req_counter, project=proj_name,
            version_file=vf_name, req_id=req_obj.req_id,
            text_snippet=req_obj.text[:100].replace('\n',' '),
            overall=overall,
            unambiguity=unamb, completeness=compl, consistency=cons,
            conformance=conf,  correctness=corr,  singularity=sing,
            verifiability=veri,
            defects_count=len(defects),
            defect_types="; ".join(d.attribute.value for d in defects) or "None (Clean)",
            is_flagged=is_flagged, elapsed_ms=round(elapsed_ms, 3),
            document_understanding=out.document_understanding_summary[:100]
        )
        all_results.append(row)
        if is_flagged:
            flagged_reqs.append({**row, "full_text": req_obj.text, "defect_objs": defects})

    # ═══════════════════════════════════════════════════════════════════
    # AGGREGATE SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    n = len(all_results)
    scores_all = [r["overall"]     for r in all_results]
    times_all  = [r["elapsed_ms"]  for r in all_results]

    print(f"\n\n{'='*95}")
    print("  LAYER 1 — AGGREGATE SUMMARY")
    print(f"{'='*95}")
    print(f"  Total requirements processed : {n}")
    print(f"  ✓ Clean (no defects)         : {n - len(flagged_reqs)}  ({100*(n-len(flagged_reqs))/n:.1f}%)")
    print(f"  ⚠ Flagged (≥1 defect)        : {len(flagged_reqs)}  ({100*len(flagged_reqs)/n:.1f}%)")
    print(f"  Mean overall score           : {sum(scores_all)/n:.4f} / 10")
    print(f"  Min / Max overall score      : {min(scores_all):.2f} / {max(scores_all):.2f}")
    print(f"  Mean Layer-1 latency         : {sum(times_all)/n:.3f} ms")
    print(f"  Min / Max latency            : {min(times_all):.3f} / {max(times_all):.3f} ms")

    # Per-attribute table
    attr_keys = ["unambiguity","completeness","consistency","conformance",
                 "correctness","singularity","verifiability"]
    print(f"\n  Per-Attribute Score Distribution  (defect threshold < {THRESHOLD})")
    print(f"  {'Attribute':<16} {'Mean':>6} {'Min':>5} {'Max':>5} {'Below 8.0':>10} {'ISO Weight':>11}")
    print(f"  {'─'*16} {'─'*6} {'─'*5} {'─'*5} {'─'*10} {'─'*11}")
    for a in attr_keys:
        vals  = [r[a] for r in all_results]
        below = sum(1 for v in vals if v < THRESHOLD)
        w     = WEIGHTS.get(a, 0)
        print(f"  {a:<16} {sum(vals)/n:>6.3f} {min(vals):>5.1f} {max(vals):>5.1f} "
              f"  {below:3d} ({100*below/n:4.1f}%)  {w*100:>9.0f}%")

    # Score distribution
    print(f"\n  Overall Score Distribution (bucket = 0.5)")
    buckets = {}
    for r in all_results:
        b = round(r["overall"] * 2) / 2
        buckets[b] = buckets.get(b, 0) + 1
    for b in sorted(buckets.keys()):
        bar = "█" * (buckets[b] // 2)
        print(f"  {b:5.1f}  {bar:<60}  {buckets[b]:3d}")

    # Defect-attribute tally
    print(f"\n  Defect Attribute Frequency (across {len(flagged_reqs)} flagged reqs)")
    attr_tally = {}
    for fr in flagged_reqs:
        for d in fr["defect_objs"]:
            k = d.attribute.value
            attr_tally[k] = attr_tally.get(k, 0) + 1
    for a, cnt in sorted(attr_tally.items(), key=lambda x:-x[1]):
        bar = "█" * cnt
        print(f"  {a:<20}  {bar}  ({cnt})")

    # CSV EXPORT
    out_csv = "layer1_deep_behaviour_log.csv"
    export_rows = [{k: v for k, v in r.items()
                    if k not in ("full_text","defect_objs")} for r in all_results]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(export_rows[0].keys()))
        writer.writeheader()
        writer.writerows(export_rows)

    print(f"\n\n  Full per-requirement CSV → {out_csv}")
    print(f"{'='*95}\n")


if __name__ == "__main__":
    run()
