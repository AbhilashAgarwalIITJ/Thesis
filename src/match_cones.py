"""
match_cones.py - Cone-level matching between two AIG designs.

Compares WL hashes of output cones between design pairs to detect
structural equivalence or divergence at cone granularity.
"""

import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_aiger import load_all_aigs
from cone_extract import extract_all_cones
from wl_hash import wl_hash_all_cones


def match_designs(cones_a, hashes_a, cones_b, hashes_b, name_a="A", name_b="B"):
    """
    Match cones between two designs by comparing WL hashes.

    Uses output name matching first (if available), then positional matching.

    Returns:
        dict with match results and statistics
    """
    # Build lookup by PO name
    a_by_name = {}
    for po, data in hashes_a.items():
        po_name = data['stats']['po_name']
        a_by_name[po_name] = {'po': po, 'hash': data['hash'], 'stats': data['stats']}

    b_by_name = {}
    for po, data in hashes_b.items():
        po_name = data['stats']['po_name']
        b_by_name[po_name] = {'po': po, 'hash': data['hash'], 'stats': data['stats']}

    # Match by name
    matched = []
    unmatched_a = []
    unmatched_b = []

    common_names = set(a_by_name.keys()) & set(b_by_name.keys())

    for name in sorted(common_names):
        a_info = a_by_name[name]
        b_info = b_by_name[name]
        is_match = a_info['hash'] == b_info['hash']
        matched.append({
            'po_name': name,
            'hash_a': a_info['hash'],
            'hash_b': b_info['hash'],
            'match': is_match,
            'size_a': a_info['stats']['num_nodes'],
            'size_b': b_info['stats']['num_nodes'],
        })

    for name in sorted(set(a_by_name.keys()) - common_names):
        unmatched_a.append({'po_name': name, 'hash': a_by_name[name]['hash']})

    for name in sorted(set(b_by_name.keys()) - common_names):
        unmatched_b.append({'po_name': name, 'hash': b_by_name[name]['hash']})

    # If no common names found, fall back to positional matching
    if not matched and not common_names:
        a_list = sorted(hashes_a.items())
        b_list = sorted(hashes_b.items())
        for i in range(min(len(a_list), len(b_list))):
            po_a, data_a = a_list[i]
            po_b, data_b = b_list[i]
            is_match = data_a['hash'] == data_b['hash']
            matched.append({
                'po_name': f"output_{i}",
                'hash_a': data_a['hash'],
                'hash_b': data_b['hash'],
                'match': is_match,
                'size_a': data_a['stats']['num_nodes'],
                'size_b': data_b['stats']['num_nodes'],
            })

    n_matched = sum(1 for m in matched if m['match'])
    n_diverged = sum(1 for m in matched if not m['match'])
    total = len(matched)

    result = {
        'design_a': name_a,
        'design_b': name_b,
        'total_compared': total,
        'matched': n_matched,
        'diverged': n_diverged,
        'match_pct': round(100 * n_matched / total, 1) if total > 0 else 0,
        'details': matched,
        'unmatched_a': unmatched_a,
        'unmatched_b': unmatched_b,
    }

    return result


def print_match_result(result):
    """Pretty-print a match result."""
    print(f"\n{'='*70}")
    print(f"Matching: {result['design_a']} vs {result['design_b']}")
    print(f"{'='*70}")
    print(f"  Cones compared: {result['total_compared']}")
    print(f"  Matched:        {result['matched']}")
    print(f"  Diverged:       {result['diverged']}")
    print(f"  Match rate:     {result['match_pct']}%")
    print()

    if result['details']:
        print(f"  {'Output':<20} {'Match':>6} {'Size A':>7} {'Size B':>7} {'Hash A':>18} {'Hash B':>18}")
        print(f"  {'-'*76}")
        for d in result['details']:
            status = "  YES" if d['match'] else "** NO"
            print(f"  {d['po_name']:<20} {status:>6} {d['size_a']:>7} {d['size_b']:>7} "
                  f"{d['hash_a'][:16]:>18} {d['hash_b'][:16]:>18}")

    if result['unmatched_a']:
        print(f"\n  Unmatched in {result['design_a']}: {[u['po_name'] for u in result['unmatched_a']]}")
    if result['unmatched_b']:
        print(f"  Unmatched in {result['design_b']}: {[u['po_name'] for u in result['unmatched_b']]}")


if __name__ == "__main__":
    print("Loading AIGs...\n")
    aig_results = load_all_aigs()

    if len(aig_results) < 2:
        print("[!] Need at least 2 AIG files for matching. Run synthesize.py first.")
        sys.exit(1)

    # Extract cones and hashes for all designs
    all_data = {}
    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        cones = extract_all_cones(G, po_nodes)
        hashes = wl_hash_all_cones(cones, k=3, semantic=False)
        all_data[name] = {'cones': cones, 'hashes': hashes}

    # Match all pairs
    names = sorted(all_data.keys())
    all_results = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            result = match_designs(
                all_data[names[i]]['cones'], all_data[names[i]]['hashes'],
                all_data[names[j]]['cones'], all_data[names[j]]['hashes'],
                names[i], names[j]
            )
            print_match_result(result)
            all_results.append(result)

    # Save results
    results_path = os.path.join(PROJECT_ROOT, "results", "matching_results.json")
    # Remove non-serializable parts
    save_results = []
    for r in all_results:
        save_results.append({k: v for k, v in r.items()})
    with open(results_path, "w") as f:
        json.dump(save_results, f, indent=2)
    print(f"\n[+] Results saved to {results_path}")
