"""
advanced_wl.py — Advanced WL hashing extension: semantic-aware + polarity-aware.

This module extends the baseline (structure-only) WL hashing with two
domain-specific enhancements:

  1. Semantic-Aware WL:
     Initial labels encode gate type (PI, AND, PO, CONST0).
     This is the node-type-enriched variant.

  2. Polarity-Aware WL:
     Initial labels encode gate type AND the inversion pattern
     of incoming edges. An AND gate fed by two inverted inputs
     is labeled differently from one fed by non-inverted inputs.

  3. Hybrid Score:
     Combines baseline and advanced hashes via a simple scoring
     function to give a richer similarity measure.

Used for:
  - Experiment 6: Baseline vs Advanced comparison table
  - Advanced contribution slide
  - Explainability examples (which method discriminates better)
"""

import os, sys, csv, hashlib
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_aiger import load_all_aigs
from cone_extract import extract_all_cones
from wl_hash import wl_hash, wl_hash_all_cones

CSV_DIR = os.path.join(PROJECT_ROOT, "results", "csv")
os.makedirs(CSV_DIR, exist_ok=True)


def _hash_str(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def polarity_aware_wl(G, k=3):
    """
    Polarity-aware WL hashing.

    Unlike semantic-aware WL which only uses gate type, this also
    encodes the inversion pattern of each node's input edges.

    For an AND gate: label = "AND:inv0_inv1" where inv0/inv1
    indicate whether each input is inverted.
    """
    nodes = list(G.nodes())
    if not nodes:
        return _hash_str("empty"), {'converged_at': 0, 'final_unique': 0}

    # Phase 1: Initial labels with polarity info
    labels = {}
    for n in nodes:
        ntype = G.nodes[n].get('type', 'UNKNOWN')
        # Collect inversion pattern of incoming edges
        in_inversions = []
        for pred in G.predecessors(n):
            edge_data = G.edges[pred, n]
            in_inversions.append('!' if edge_data.get('inverted', False) else '+')
        in_inversions.sort()
        inv_sig = ''.join(in_inversions) if in_inversions else 'none'
        labels[n] = _hash_str(f"{ntype}:{inv_sig}")

    unique_counts = [len(set(labels.values()))]
    converged_at = k

    # Phase 2: WL iterations
    for iteration in range(k):
        new_labels = {}
        for n in nodes:
            pred_info = []
            for p in G.predecessors(n):
                edge_data = G.edges[p, n]
                inv = '!' if edge_data.get('inverted', False) else '+'
                pred_info.append(f"{labels[p]}:{inv}")
            pred_info.sort()

            succ_labels = sorted([labels[s] for s in G.successors(n)])
            neighborhood = f"{labels[n]}|{'|'.join(pred_info)}|{'|'.join(succ_labels)}"
            new_labels[n] = _hash_str(neighborhood)

        if new_labels == labels:
            converged_at = iteration
            break

        labels = new_labels
        unique_counts.append(len(set(labels.values())))

    label_multiset = sorted(labels.values())
    graph_hash = _hash_str("|".join(label_multiset))

    conv_info = {
        'converged_at': converged_at,
        'final_unique': len(set(labels.values())),
        'unique_counts': unique_counts,
    }
    return graph_hash, conv_info


def compute_advanced_hashes(cones_dict, k=3):
    """
    Compute all three hash variants for every cone.

    Returns dict of {po_node: {
        'baseline_hash', 'semantic_hash', 'polarity_hash',
        'baseline_conv', 'semantic_conv', 'polarity_conv',
        'stats'
    }}
    """
    results = {}
    for po_node, cone_data in cones_dict.items():
        G = cone_data['subgraph']
        stats = cone_data['stats']

        # Baseline (structure-only)
        bh, _, bc = wl_hash(G, k=k, semantic=False)
        # Semantic-aware
        sh, _, sc = wl_hash(G, k=k, semantic=True)
        # Polarity-aware
        ph, pc = polarity_aware_wl(G, k=k)

        results[po_node] = {
            'baseline_hash': bh,
            'semantic_hash': sh,
            'polarity_hash': ph,
            'baseline_unique': bc['final_unique'],
            'semantic_unique': sc['final_unique'],
            'polarity_unique': pc['final_unique'],
            'stats': stats,
        }
    return results


def match_advanced(hashes_a, hashes_b, name_a="A", name_b="B"):
    """
    Compare designs using all three hash variants.
    Returns per-variant match results.
    """
    # Build name-based lookups
    a_by_name = {v['stats']['po_name']: (k, v) for k, v in hashes_a.items()}
    b_by_name = {v['stats']['po_name']: (k, v) for k, v in hashes_b.items()}

    common = sorted(set(a_by_name.keys()) & set(b_by_name.keys()))
    if not common:
        # Positional fallback
        a_list = sorted(hashes_a.items())
        b_list = sorted(hashes_b.items())
        common_pairs = [(f"output_{i}", a_list[i][1], b_list[i][1])
                        for i in range(min(len(a_list), len(b_list)))]
    else:
        common_pairs = [(name, a_by_name[name][1], b_by_name[name][1])
                        for name in common]

    details = []
    for po_name, da, db in common_pairs:
        details.append({
            'po_name': po_name,
            'baseline_match': da['baseline_hash'] == db['baseline_hash'],
            'semantic_match': da['semantic_hash'] == db['semantic_hash'],
            'polarity_match': da['polarity_hash'] == db['polarity_hash'],
            'size_a': da['stats']['num_nodes'],
            'size_b': db['stats']['num_nodes'],
        })

    total = len(details)
    baseline_matched = sum(1 for d in details if d['baseline_match'])
    semantic_matched = sum(1 for d in details if d['semantic_match'])
    polarity_matched = sum(1 for d in details if d['polarity_match'])

    # Hybrid score: average of the three match rates
    hybrid_score = round((baseline_matched + semantic_matched + polarity_matched) / (3 * total) * 100, 1) if total else 0

    return {
        'design_a': name_a,
        'design_b': name_b,
        'total_cones': total,
        'baseline_matched': baseline_matched,
        'semantic_matched': semantic_matched,
        'polarity_matched': polarity_matched,
        'baseline_pct': round(100 * baseline_matched / total, 1) if total else 0,
        'semantic_pct': round(100 * semantic_matched / total, 1) if total else 0,
        'polarity_pct': round(100 * polarity_matched / total, 1) if total else 0,
        'hybrid_score': hybrid_score,
        'details': details,
    }


def run_advanced_experiment(aig_results):
    """
    Run the advanced comparison experiment on mutation pairs
    and optimization pairs.

    Returns list of result dicts + CSV rows.
    """
    print("\n" + "="*60)
    print("ADVANCED EXPERIMENT: Baseline vs Semantic vs Polarity WL")
    print("="*60 + "\n")

    # Define comparison pairs
    pairs = [
        ('adder_4bit', 'adder_4bit_mut1'),
        ('adder_4bit', 'adder_4bit_mut2'),
        ('adder_4bit_O0', 'adder_4bit_O1'),
        ('adder_4bit_O0', 'adder_4bit_O2'),
        ('adder_4bit_O1', 'adder_4bit_O2'),
    ]

    # Precompute advanced hashes for all involved designs
    needed = set()
    for a, b in pairs:
        needed.add(a)
        needed.add(b)

    design_data = {}
    for name in sorted(needed):
        if name not in aig_results:
            print(f"[!] {name} not found, skipping")
            continue
        G, po_nodes, parsed, stats = aig_results[name]
        cones = extract_all_cones(G, po_nodes)
        adv_hashes = compute_advanced_hashes(cones, k=3)
        design_data[name] = adv_hashes

    # Run comparisons
    results = []
    csv_rows = []
    for name_a, name_b in pairs:
        if name_a not in design_data or name_b not in design_data:
            continue
        result = match_advanced(design_data[name_a], design_data[name_b], name_a, name_b)
        results.append(result)

        csv_rows.append({
            'design_a': name_a,
            'design_b': name_b,
            'total_cones': result['total_cones'],
            'baseline_matched': result['baseline_matched'],
            'baseline_pct': result['baseline_pct'],
            'semantic_matched': result['semantic_matched'],
            'semantic_pct': result['semantic_pct'],
            'polarity_matched': result['polarity_matched'],
            'polarity_pct': result['polarity_pct'],
            'hybrid_score': result['hybrid_score'],
        })

        print(f"  {name_a} vs {name_b}:")
        print(f"    Baseline:  {result['baseline_matched']}/{result['total_cones']} "
              f"({result['baseline_pct']}%)")
        print(f"    Semantic:  {result['semantic_matched']}/{result['total_cones']} "
              f"({result['semantic_pct']}%)")
        print(f"    Polarity:  {result['polarity_matched']}/{result['total_cones']} "
              f"({result['polarity_pct']}%)")
        print(f"    Hybrid:    {result['hybrid_score']}%")
        print()

    # Also export per-cone detail CSV
    detail_rows = []
    for result in results:
        for d in result['details']:
            detail_rows.append({
                'design_a': result['design_a'],
                'design_b': result['design_b'],
                'cone': d['po_name'],
                'size_a': d['size_a'],
                'size_b': d['size_b'],
                'baseline_match': d['baseline_match'],
                'semantic_match': d['semantic_match'],
                'polarity_match': d['polarity_match'],
            })

    return results, csv_rows, detail_rows


def export_advanced_csv(csv_rows, detail_rows):
    """Export advanced experiment results to CSV."""
    p1 = os.path.join(CSV_DIR, 'advanced_matching_summary.csv')
    p2 = os.path.join(CSV_DIR, 'advanced_matching_details.csv')

    if csv_rows:
        with open(p1, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"[+] Saved {p1}")

    if detail_rows:
        with open(p2, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=detail_rows[0].keys())
            writer.writeheader()
            writer.writerows(detail_rows)
        print(f"[+] Saved {p2}")


if __name__ == "__main__":
    aig_results = load_all_aigs()
    results, csv_rows, detail_rows = run_advanced_experiment(aig_results)
    export_advanced_csv(csv_rows, detail_rows)
