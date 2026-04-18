"""
experiments.py - Thesis Experiment Suite
========================================

MTP Phase: MTP-3 (full experiment framework)

Thesis: AI-Augmented Verilog Netlist Matching Using AIG and Graph Neural Networks

BASELINE METHOD: Structural Fingerprint Matching
  Per-cone signature: (num_nodes, num_edges, num_and, num_pi, depth)
  Match criterion: exact fingerprint equality
  Strength: fast, intuitive, easy to explain
  Weakness: cannot detect inversion-level or fine topology changes

ADVANCED METHOD: WL-Hash Cone Matching (k=3, semantic + inversion-aware)
  Per-cone signature: Weisfeiler-Leman graph hash
  Match criterion: exact hash equality
  Strength: captures full neighbourhood topology including edge inversions
  Weakness: more computationally expensive

EXPERIMENTS:
  EXP 1  Benchmark Characterization             -> Table 1
  EXP 2  Cone Matching: Baseline vs Advanced     -> Tables 2, 3, 4
  EXP 3  Scalability Analysis                    -> Table 5
  EXP 4  WL Convergence Study                    -> CSV (for plot)
  EXP 5  Qualitative Case Study (mut2)           -> Table 6
"""

import os, sys, csv, time
from collections import OrderedDict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cone_extract import extract_all_cones
from wl_hash import wl_hash

try:
    from tabulate import tabulate
except ImportError:
    def tabulate(data, headers='keys', tablefmt='grid'):
        if not data:
            return ''
        keys = list(data[0].keys())
        lines = ['\t'.join(str(k) for k in keys)]
        for row in data:
            lines.append('\t'.join(str(row.get(k, '')) for k in keys))
        return '\n'.join(lines)

CSV_DIR   = os.path.join(PROJECT_ROOT, "results", "csv")
TABLE_DIR = os.path.join(PROJECT_ROOT, "results", "tables")
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(TABLE_DIR, exist_ok=True)

# ----------------------------------------------------------------
#  CONFIGURATION
# ----------------------------------------------------------------
MATCHING_PAIRS = [
    ("adder_4bit",    "adder_4bit_mut1", "Mutation: Gate Replace (XOR->OR)"),
    ("adder_4bit",    "adder_4bit_mut2", "Mutation: Carry Inversion (~c[2])"),
    ("adder_4bit_O0", "adder_4bit_O1",   "Optimisation: Minimal vs Standard"),
    ("adder_4bit_O1", "adder_4bit_O2",   "Optimisation: Standard vs Full"),
    ("adder_4bit",    "counter_4bit",    "Cross-Design: Adder vs Counter"),
    ("adder_4bit",    "alu_simple",      "Cross-Design: Adder vs ALU"),
]

SCALABILITY_DESIGNS = ["adder_4bit", "adder_8bit", "adder_16bit", "adder_32bit"]
WL_K = 3


# ================================================================
#  BASELINE: Structural Fingerprint
# ================================================================
def structural_fingerprint(stats):
    """Return a 5-tuple fingerprint for one cone."""
    return (stats['num_nodes'], stats['num_edges'],
            stats['num_and'],  stats['num_pi'], stats['depth'])


# ================================================================
#  CONE ALIGNMENT
# ================================================================
def _align_cones(cones_a, cones_b):
    """Pair up cones by PO name; fall back to positional order."""
    a_map = {d['stats']['po_name']: (po, d) for po, d in cones_a.items()}
    b_map = {d['stats']['po_name']: (po, d) for po, d in cones_b.items()}
    common = sorted(set(a_map) & set(b_map))
    if common:
        return [(n, a_map[n], b_map[n]) for n in common]
    al = sorted(cones_a.items())
    bl = sorted(cones_b.items())
    return [(f"output_{i}", al[i], bl[i]) for i in range(min(len(al), len(bl)))]


# ================================================================
#  GENERIC MATCH FUNCTION
# ================================================================
def match_pair(cones_a, cones_b, name_a, name_b,
               method="fingerprint", wl_a=None, wl_b=None):
    """
    Compare cones between two designs.

    method  "fingerprint"  ->  baseline (tuple equality)
            "wl"           ->  advanced (WL hash equality)

    wl_a, wl_b: optional pre-computed {po_node: hash_str} dicts.
    """
    aligned = _align_cones(cones_a, cones_b)

    # Compute WL hashes on demand if not pre-supplied
    if method == "wl":
        if wl_a is None:
            wl_a = {}
            for po, data in cones_a.items():
                h, _, _ = wl_hash(data['subgraph'], k=WL_K, semantic=True)
                wl_a[po] = h
        if wl_b is None:
            wl_b = {}
            for po, data in cones_b.items():
                h, _, _ = wl_hash(data['subgraph'], k=WL_K, semantic=True)
                wl_b[po] = h

    details = []
    for cone_name, (po_a, da), (po_b, db) in aligned:
        sa, sb = da['stats'], db['stats']
        fp_a = structural_fingerprint(sa)
        fp_b = structural_fingerprint(sb)

        if method == "fingerprint":
            is_match = (fp_a == fp_b)
        else:
            is_match = (wl_a[po_a] == wl_b[po_b])

        row = {
            'cone': cone_name,
            'match': is_match,
            'nodes_a': sa['num_nodes'], 'nodes_b': sb['num_nodes'],
            'edges_a': sa['num_edges'], 'edges_b': sb['num_edges'],
            'and_a':   sa['num_and'],   'and_b':   sb['num_and'],
            'pi_a':    sa['num_pi'],    'pi_b':    sb['num_pi'],
            'depth_a': sa['depth'],     'depth_b': sb['depth'],
            'fp_a': str(fp_a), 'fp_b': str(fp_b),
        }
        if method == "wl":
            row['hash_a'] = wl_a[po_a][:12]
            row['hash_b'] = wl_b[po_b][:12]
        details.append(row)

    n_match = sum(1 for d in details if d['match'])
    total   = len(details)
    return {
        'design_a': name_a, 'design_b': name_b,
        'method': method, 'total': total,
        'matched': n_match, 'unmatched': total - n_match,
        'pct': round(100 * n_match / total, 1) if total else 0,
        'details': details,
    }


# ================================================================
#  EXPERIMENT 1 — BENCHMARK CHARACTERISATION
# ================================================================
def exp1_benchmark(aig_results):
    print("\n" + "=" * 70)
    print("  EXPERIMENT 1: BENCHMARK CHARACTERISATION")
    print("=" * 70)

    rows = []
    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        cones = extract_all_cones(G, po_nodes)
        sizes = [c['stats']['num_nodes'] for c in cones.values()]
        rows.append(OrderedDict([
            ('Design',    name),
            ('PI',        stats['primary_inputs']),
            ('PO',        stats['primary_outputs']),
            ('AND',       stats['and_gates']),
            ('Nodes',     stats['nodes']),
            ('Edges',     stats['edges']),
            ('Depth',     stats['depth']),
            ('Cones',     len(cones)),
            ('Avg Cone',  round(sum(sizes) / len(sizes), 1) if sizes else 0),
        ]))

    print(tabulate(rows, headers='keys', tablefmt='grid'))
    _save_csv(rows, 'table1_benchmark.csv')
    _save_table(rows, 'table1_benchmark.txt', 'Table 1: Benchmark Summary')
    return rows


# ================================================================
#  EXPERIMENT 2 — MATCHING (baseline + advanced + comparison)
# ================================================================
def exp2_matching(aig_results):
    print("\n" + "=" * 70)
    print("  EXPERIMENT 2: CONE MATCHING — BASELINE vs ADVANCED")
    print("=" * 70)

    # --- pre-compute cones and WL hashes for every needed design ---
    needed = set()
    for a, b, _ in MATCHING_PAIRS:
        needed |= {a, b}

    all_cones = {}
    all_wl    = {}
    for name in sorted(needed):
        if name not in aig_results:
            continue
        G, po_nodes, _, _ = aig_results[name]
        cones = extract_all_cones(G, po_nodes)
        all_cones[name] = cones
        wl_dict = {}
        for po, data in cones.items():
            h, _, _ = wl_hash(data['subgraph'], k=WL_K, semantic=True)
            wl_dict[po] = h
        all_wl[name] = wl_dict

    # --- run pairs ---
    bl_rows, adv_rows, cmp_rows = [], [], []
    bl_detail, adv_detail = [], []

    for name_a, name_b, category in MATCHING_PAIRS:
        if name_a not in all_cones or name_b not in all_cones:
            print(f"  [!] Skipping {name_a} vs {name_b}: not found")
            continue

        # Timing — baseline
        t0 = time.time()
        bl = match_pair(all_cones[name_a], all_cones[name_b],
                        name_a, name_b, "fingerprint")
        t_bl = (time.time() - t0) * 1000

        # Timing — advanced (hashes already computed, so this is comparison time)
        t0 = time.time()
        adv = match_pair(all_cones[name_a], all_cones[name_b],
                         name_a, name_b, "wl",
                         wl_a=all_wl[name_a], wl_b=all_wl[name_b])
        t_adv = (time.time() - t0) * 1000

        # False positives: baseline says match but WL says mismatch
        fp_count = sum(1 for bd, ad in zip(bl['details'], adv['details'])
                       if bd['match'] and not ad['match'])

        pair_label = f"{name_a} vs {name_b}"
        bl_rows.append(OrderedDict([
            ('Pair', pair_label), ('Category', category),
            ('Cones', bl['total']),
            ('Matched', bl['matched']), ('Unmatched', bl['unmatched']),
            ('Match %', bl['pct']), ('Time ms', round(t_bl, 2)),
        ]))
        adv_rows.append(OrderedDict([
            ('Pair', pair_label), ('Category', category),
            ('Cones', adv['total']),
            ('Matched', adv['matched']), ('Unmatched', adv['unmatched']),
            ('Match %', adv['pct']), ('Time ms', round(t_adv, 2)),
        ]))
        cmp_rows.append(OrderedDict([
            ('Category', category),
            ('Pair', pair_label),
            ('Cones', bl['total']),
            ('Baseline %', bl['pct']),
            ('Advanced %', adv['pct']),
            ('False Pos', fp_count),
            ('FP Rate %', round(100 * fp_count / bl['total'], 1) if bl['total'] else 0),
        ]))

        # Detail rows
        for d in bl['details']:
            bl_detail.append(OrderedDict([
                ('Pair', pair_label), ('Cone', d['cone']),
                ('Match', d['match']),
                ('Nodes_A', d['nodes_a']), ('Nodes_B', d['nodes_b']),
                ('AND_A', d['and_a']), ('AND_B', d['and_b']),
                ('Depth_A', d['depth_a']), ('Depth_B', d['depth_b']),
                ('FP_A', d['fp_a']), ('FP_B', d['fp_b']),
            ]))
        for d in adv['details']:
            adv_detail.append(OrderedDict([
                ('Pair', pair_label), ('Cone', d['cone']),
                ('Match', d['match']),
                ('Nodes_A', d['nodes_a']), ('Nodes_B', d['nodes_b']),
                ('Hash_A', d.get('hash_a', '')), ('Hash_B', d.get('hash_b', '')),
            ]))

        flag = f"  ** {fp_count} false positive(s) **" if fp_count else ""
        print(f"\n  {category}")
        print(f"    {pair_label}")
        print(f"    Baseline (Fingerprint) : {bl['matched']}/{bl['total']}  ({bl['pct']}%)")
        print(f"    Advanced (WL Hash)     : {adv['matched']}/{adv['total']}  ({adv['pct']}%){flag}")

    # --- tables ---
    print("\n\n  Table 2: Baseline Results (Structural Fingerprint)")
    print(tabulate(bl_rows, headers='keys', tablefmt='grid'))

    print("\n  Table 3: Advanced Results (WL Hash, k=3)")
    print(tabulate(adv_rows, headers='keys', tablefmt='grid'))

    print("\n  Table 4: Comparison — Baseline vs Advanced")
    print(tabulate(cmp_rows, headers='keys', tablefmt='grid'))

    _save_csv(bl_rows,  'table2_baseline.csv')
    _save_csv(adv_rows, 'table3_advanced.csv')
    _save_csv(cmp_rows, 'table4_comparison.csv')
    _save_csv(bl_detail,  'baseline_cone_details.csv')
    _save_csv(adv_detail, 'advanced_cone_details.csv')

    _save_table(bl_rows,  'table2_baseline.txt',
                'Table 2: Baseline Matching (Structural Fingerprint)')
    _save_table(adv_rows, 'table3_advanced.txt',
                'Table 3: Advanced Matching (WL Hash, k=3, semantic)')
    _save_table(cmp_rows, 'table4_comparison.txt',
                'Table 4: Baseline vs Advanced Comparison')

    return bl_rows, adv_rows, cmp_rows


# ================================================================
#  EXPERIMENT 3 — SCALABILITY
# ================================================================
def exp3_scalability(aig_results):
    print("\n" + "=" * 70)
    print("  EXPERIMENT 3: SCALABILITY ANALYSIS")
    print("=" * 70)

    rows = []
    for name in SCALABILITY_DESIGNS:
        if name not in aig_results:
            continue
        G, po_nodes, _, stats = aig_results[name]

        # Cone extraction timing
        t0 = time.time()
        cones = extract_all_cones(G, po_nodes)
        t_cone = (time.time() - t0) * 1000

        # Fingerprint timing
        t0 = time.time()
        for _, d in cones.items():
            structural_fingerprint(d['stats'])
        t_fp = (time.time() - t0) * 1000

        # WL hash timing
        t0 = time.time()
        for _, d in cones.items():
            wl_hash(d['subgraph'], k=WL_K, semantic=True)
        t_wl = (time.time() - t0) * 1000

        bits = int(''.join(filter(str.isdigit, name)))
        rows.append(OrderedDict([
            ('Design', name),
            ('Bits',   bits),
            ('Nodes',  stats['nodes']),
            ('AND',    stats['and_gates']),
            ('Depth',  stats['depth']),
            ('Cones',  len(cones)),
            ('Cone ms',     round(t_cone, 2)),
            ('FP ms',       round(t_fp, 3)),
            ('WL ms',       round(t_wl, 2)),
            ('Total ms',    round(t_cone + t_wl, 2)),
        ]))
        print(f"  {name:15s}  {stats['nodes']:>4} nodes  "
              f"cone={t_cone:.1f}ms  fp={t_fp:.3f}ms  wl={t_wl:.1f}ms")

    print("\n  Table 5: Scalability")
    print(tabulate(rows, headers='keys', tablefmt='grid'))
    _save_csv(rows, 'table5_scalability.csv')
    _save_table(rows, 'table5_scalability.txt', 'Table 5: Scalability Analysis')
    return rows


# ================================================================
#  EXPERIMENT 4 — WL CONVERGENCE
# ================================================================
def exp4_convergence(aig_results):
    print("\n" + "=" * 70)
    print("  EXPERIMENT 4: WL CONVERGENCE")
    print("=" * 70)

    target = 'adder_8bit' if 'adder_8bit' in aig_results else 'adder_4bit'
    G, po_nodes, _, stats = aig_results[target]
    cones = extract_all_cones(G, po_nodes)
    print(f"  Design: {target} ({stats['nodes']} nodes, {len(cones)} cones)\n")

    max_k = 6
    rows = []
    for k_val in range(1, max_k + 1):
        hashes = set()
        total_unique = 0
        for _, data in cones.items():
            h, _, conv = wl_hash(data['subgraph'], k=k_val, semantic=True)
            hashes.add(h)
            total_unique += conv['final_unique']
        avg_u = round(total_unique / len(cones), 1)
        rows.append(OrderedDict([
            ('k', k_val),
            ('Unique Hashes', len(hashes)),
            ('Avg Labels',    avg_u),
            ('Total Labels',  total_unique),
        ]))
        print(f"  k={k_val}:  {len(hashes)} unique hashes,  avg {avg_u} labels/cone")

    _save_csv(rows, 'exp_convergence.csv')
    return rows, target


# ================================================================
#  EXPERIMENT 5 — CASE STUDY  (adder_4bit vs adder_4bit_mut2)
# ================================================================
def exp5_case_study(aig_results):
    print("\n" + "=" * 70)
    print("  EXPERIMENT 5: CASE STUDY — CARRY INVERSION MUTATION")
    print("  adder_4bit  vs  adder_4bit_mut2  (~c[2])")
    print("=" * 70)

    na, nb = 'adder_4bit', 'adder_4bit_mut2'
    if na not in aig_results or nb not in aig_results:
        print("  [!] Required designs not found")
        return []

    G_a, po_a, _, _ = aig_results[na]
    G_b, po_b, _, _ = aig_results[nb]
    ca = extract_all_cones(G_a, po_a)
    cb = extract_all_cones(G_b, po_b)

    bl  = match_pair(ca, cb, na, nb, "fingerprint")
    adv = match_pair(ca, cb, na, nb, "wl")

    rows = []
    for bd, ad in zip(bl['details'], adv['details']):
        fp_m = bd['match']
        wl_m = ad['match']
        if fp_m and wl_m:
            verdict = "Both Match"
        elif not fp_m and not wl_m:
            verdict = "Both Reject"
        elif fp_m and not wl_m:
            verdict = "FALSE POSITIVE (FP match, WL reject)"
        else:
            verdict = "FP reject, WL match"

        rows.append(OrderedDict([
            ('Cone',    bd['cone']),
            ('Nodes A', bd['nodes_a']),
            ('Nodes B', bd['nodes_b']),
            ('AND A',   bd['and_a']),
            ('AND B',   bd['and_b']),
            ('Depth A', bd['depth_a']),
            ('Depth B', bd['depth_b']),
            ('FP Match',  fp_m),
            ('WL Match',  wl_m),
            ('Verdict',   verdict),
        ]))

    print(f"\n  Table 6: Per-Cone Case Study")
    print(tabulate(rows, headers='keys', tablefmt='grid'))

    fp_count = sum(1 for r in rows if 'FALSE POSITIVE' in r['Verdict'])
    print(f"\n  Fingerprint match rate: {bl['pct']}%")
    print(f"  WL hash match rate:    {adv['pct']}%")
    print(f"  False positives:       {fp_count}")

    if fp_count > 0:
        print(f"\n  KEY FINDING: Structural fingerprinting falsely matches {fp_count} cone(s)")
        print(f"  that the WL hash correctly rejects.  The carry inversion (~c[2])")
        print(f"  preserves gate counts and depth but changes inversion patterns,")
        print(f"  which are invisible to aggregate-metric fingerprinting but fully")
        print(f"  captured by the WL neighbourhood hashing algorithm.")

    _save_csv(rows, 'table6_case_study.csv')
    _save_table(rows, 'table6_case_study.txt',
                'Table 6: Qualitative Case Study — adder_4bit vs adder_4bit_mut2')
    return rows


# ================================================================
#  CSV / TABLE UTILITIES
# ================================================================
def _save_csv(rows, filename):
    if not rows:
        return
    path = os.path.join(CSV_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [CSV] {filename}")


def _save_table(rows, filename, title):
    if not rows:
        return
    path = os.path.join(TABLE_DIR, filename)
    text = tabulate(rows, headers='keys', tablefmt='grid')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"{title}\n{'=' * len(title)}\n\n{text}\n")
    print(f"  [TXT] {filename}")


# ================================================================
#  MASTER RUNNER
# ================================================================
def run_all_experiments(aig_results):
    """Run the complete thesis experiment suite."""
    t0 = time.time()

    r = {}
    r['exp1'] = exp1_benchmark(aig_results)

    bl, adv, cmp = exp2_matching(aig_results)
    r['exp2_baseline']    = bl
    r['exp2_advanced']    = adv
    r['exp2_comparison']  = cmp

    r['exp3'] = exp3_scalability(aig_results)
    r['exp4'], r['exp4_target'] = exp4_convergence(aig_results)
    r['exp5'] = exp5_case_study(aig_results)

    print(f"\n  All experiments completed in {time.time() - t0:.1f}s")
    return r


# ================================================================
if __name__ == "__main__":
    from parse_aiger import load_all_aigs
    print("Loading AIG files...")
    aig_results = load_all_aigs()
    if not aig_results:
        print("[!] No AIG files. Run synthesize.py first.")
        sys.exit(1)
    run_all_experiments(aig_results)
