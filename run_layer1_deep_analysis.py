"""
Layer 1 Deep-Behaviour Analysis Script
Runs all 215 requirements through Layer 1 only and prints a detailed log
of exactly what the scorer returns for every single requirement.
"""
import sys, time, csv
from pathlib import Path
sys.path.insert(0, '.')

from sqam_analyzer import Layer1DocumentScorer, Requirement, SRSContext, resolve_llm_client
from srs_evolution.aligner import SRSParser
from run_multi_project_layer1_test import discover_all_project_versions

THRESHOLD = 8.0
LIMIT     = 5     # reqs per version — matches original sweep
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
    parser   = SRSParser()
    projects = discover_all_project_versions()

    print(f"\n{'='*95}")
    print("  LAYER 1 DEEP BEHAVIOUR LOG — ALL 215 REQUIREMENTS")
    print(f"  Backend: MockLLMClient  |  Temp=0.0  |  Defect threshold < {THRESHOLD}")
    print(f"{'='*95}")

    all_results  = []
    flagged_reqs = []
    req_counter  = 0
    proj_counter = 0

    for proj_name, version_files in projects.items():
        proj_counter += 1
        print(f"\n{'─'*95}")
        print(f"  PROJECT {proj_counter:02d}/15 │ {proj_name}  ({len(version_files)} version(s))")
        print(f"{'─'*95}")

        for v_idx, file_path in enumerate(version_files):
            version_label = file_path.stem
            try:
                req_units = parser.parse_document(file_path, version_label=version_label)
            except Exception as ex:
                print(f"  [SKIP] Cannot parse {file_path.name}: {ex}")
                continue

            if not req_units:
                print(f"  [SKIP] 0 reqs extracted from {file_path.name}")
                continue

            selected = req_units[:LIMIT]
            ctx = SRSContext(
                document_title=f"{proj_name} — {version_label}",
                domain_summary=f"Automated quality evaluation for {proj_name}.",
                glossary={},
            )

            print(f"\n  Version {v_idx+1}/{len(version_files)}: {file_path.name}  [{len(selected)} reqs]")
            print(f"  {'#':>3}  {'REQ-ID':<24} {'Score':>5}  "
                  f"{'Unamb':>5} {'Compl':>5} {'Cons':>5} {'Conf':>5} "
                  f"{'Corr':>5} {'Sing':>5} {'Veri':>5}  Status")
            print("  " + "─" * 90)

            for u in selected:
                req_counter += 1
                req_obj = Requirement(req_id=u.req_id, text=u.text,
                                      section=u.section or "Functional Specifications")

                t0  = time.perf_counter()
                out = scorer.execute(requirement=req_obj, srs_context=ctx)
                elapsed_ms = (time.perf_counter() - t0) * 1000

                overall  = out.overall_quality_score
                defects  = out.shortcomings
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

                print(f"  {req_counter:>3}.  {req_obj.req_id:<24} {overall:>5.1f}  "
                      f"{unamb:>5.1f} {compl:>5.1f} {cons:>5.1f} {conf:>5.1f} "
                      f"{corr:>5.1f} {sing:>5.1f} {veri:>5.1f}  {status}")

                row = dict(
                    seq=req_counter, project=proj_name,
                    version_file=file_path.name, req_id=req_obj.req_id,
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
        bar = "█" * buckets[b]
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

    # ═══════════════════════════════════════════════════════════════════
    # DETAILED FLAGGED REQUIREMENTS REPORT
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n\n{'='*95}")
    print(f"  DETAILED DEFECT REPORT — ALL {len(flagged_reqs)} FLAGGED REQUIREMENTS")
    print(f"{'='*95}")

    for i, fr in enumerate(flagged_reqs, 1):
        print(f"\n  ┌── [{i:02d}/{len(flagged_reqs)}] {fr['req_id']}  {'─'*65}")
        print(f"  │  Project      : {fr['project']}")
        print(f"  │  Version file : {fr['version_file']}")
        print(f"  │  Overall score: {fr['overall']:.1f} / 10.0")
        print(f"  │  Scores       : Unamb={fr['unambiguity']} | Compl={fr['completeness']} | "
              f"Cons={fr['consistency']} | Conf={fr['conformance']} | "
              f"Corr={fr['correctness']} | Sing={fr['singularity']} | Veri={fr['verifiability']}")
        print(f"  │  Req text     : {fr['full_text'][:300].replace(chr(10),' ')}")
        print(f"  │  Defects ({fr['defects_count']}):")
        for d in fr["defect_objs"]:
            print(f"  │    ● Attribute        : {d.attribute.value}")
            print(f"  │      Problematic text : \"{d.problematic_excerpt}\"")
            print(f"  │      Severity         : {d.severity.value}")
            print(f"  │      Explanation      : {d.explanation[:250]}")
        print(f"  └{'─'*80}")

    # ═══════════════════════════════════════════════════════════════════
    # CSV EXPORT
    # ═══════════════════════════════════════════════════════════════════
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
