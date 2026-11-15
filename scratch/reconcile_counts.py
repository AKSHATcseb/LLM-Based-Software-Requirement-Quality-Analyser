import json
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from srs_evolution.aligner import SRSParser

df_orig = pd.read_csv('layer1_multi_project_evaluation_results.csv')
srs_dir = Path('srs doc versions')
parser = SRSParser()

with open('results/sample_manifest.json', 'r', encoding='utf-8') as f:
    manifest = json.load(f)

manifest_counts = {}
for r in manifest['requirements']:
    manifest_counts[r['project']] = manifest_counts.get(r['project'], 0) + 1

table1_extracted = {
    '1_FROG': 108,
    '2_SMIRK': 12,
    '3_ONEM': 74,
    '4_UIC': 142,
    '5_EVLA BACKEND SYSTEM REQUIREMENTS': 65,
    '6': 89,
    '7': 44,
    '8': 51,
    '9': 38,
    '10': 58,
    '11': 62,
    '12': 49,
    '13': 43,
    '14': 52,
    '15': 55
}

# The 43 version files from df_orig
vfiles_by_proj = {}
for (p, vf, vs) in df_orig[['project', 'version_file', 'version_stem']].drop_duplicates().values:
    vfiles_by_proj.setdefault(p, []).append((vf, vs))

header = f"{'Project':<35} | {'Versions':<8} | {'Table I Extr':<12} | {'Actual Parser':<14} | {'In Manifest':<11} | {'Orig 215':<8}"
print(header)
print("-" * len(header))

total_t1 = 0
total_parser = 0
total_manifest = 0
total_orig = 0

for p, t1_val in table1_extracted.items():
    vlist = vfiles_by_proj[p]
    n_versions = len(vlist)
    p_parser_count = 0
    for vf, vs in vlist:
        fpath = srs_dir / p / vf
        units = parser.parse_document(fpath, version_label=vs)
        p_parser_count += len(units)
    orig_count = len(df_orig[df_orig['project'] == p])
    m_count = manifest_counts.get(p, 0)
    
    total_t1 += t1_val
    total_parser += p_parser_count
    total_manifest += m_count
    total_orig += orig_count
    
    print(f"{p:<35} | {n_versions:<8} | {t1_val:<12} | {p_parser_count:<14} | {m_count:<11} | {orig_count:<8}")

print("=" * len(header))
print(f"{'TOTAL':<35} | {43:<8} | {total_t1:<12} | {total_parser:<14} | {total_manifest:<11} | {total_orig:<8}")
