"""
wl_hash.py - Weisfeiler-Leman (WL) graph hashing for AIG cones.

Implements the 1-dimensional WL test / color refinement algorithm.
At each iteration:
  new_label(v) = hash( current_label(v), sorted([current_label(u) for u in neighbors(v)]) )

After k iterations, the graph hash is the hash of the sorted multiset of all node labels.

Two modes:
  - Structure-only: all nodes get the same initial label (uniform)
  - Semantic-aware: initial label = node type (PI, AND, PO, CONST0)
"""

import hashlib
import json
from collections import Counter


def _hash_str(s):
    """Deterministic hash of a string."""
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def wl_hash(G, k=3, semantic=False):
    """
    Compute WL hash of a graph.

    Parameters:
        G: NetworkX DiGraph (a cone subgraph)
        k: number of WL iterations
        semantic: if True, use node type as initial label; otherwise uniform

    Returns:
        graph_hash: str (hash of the final multiset of labels)
        label_history: list of dicts (labels at each iteration, for analysis)
        convergence_info: dict with convergence data
    """
    nodes = list(G.nodes())
    if not nodes:
        return _hash_str("empty"), [], {'converged_at': 0, 'unique_labels': [0]}

    # Initialize labels
    if semantic:
        labels = {}
        for n in nodes:
            node_type = G.nodes[n].get('type', 'UNKNOWN')
            labels[n] = _hash_str(node_type)
    else:
        labels = {n: _hash_str("node") for n in nodes}

    label_history = [dict(labels)]
    unique_counts = [len(set(labels.values()))]
    converged_at = k  # default: did not converge early

    for iteration in range(k):
        new_labels = {}
        for n in nodes:
            # Get predecessors (fan-in) and successors (fan-out)
            pred_labels = sorted([labels[p] for p in G.predecessors(n)])
            succ_labels = sorted([labels[s] for s in G.successors(n)])

            # Include edge inversion info if available
            pred_inv = []
            for p in G.predecessors(n):
                edge_data = G.edges[p, n]
                inv = edge_data.get('inverted', False)
                pred_inv.append(f"{labels[p]}:{'!' if inv else '+'}")
            pred_inv.sort()

            # Combine: current label + predecessor context + successor context
            neighborhood = f"{labels[n]}|{'|'.join(pred_inv)}|{'|'.join(succ_labels)}"
            new_labels[n] = _hash_str(neighborhood)

        # Check convergence (labels stopped changing)
        if new_labels == labels:
            converged_at = iteration
            break

        labels = new_labels
        label_history.append(dict(labels))
        unique_counts.append(len(set(labels.values())))

    # Compute graph-level hash from sorted multiset of final labels
    label_multiset = sorted(labels.values())
    graph_hash = _hash_str("|".join(label_multiset))

    convergence_info = {
        'converged_at': converged_at,
        'unique_labels': unique_counts,
        'final_unique': len(set(labels.values())),
        'iterations_run': len(label_history) - 1,
    }

    return graph_hash, label_history, convergence_info


def wl_hash_cone(cone_data, k=3, semantic=False):
    """
    Compute WL hash for a single cone.

    Parameters:
        cone_data: dict with 'subgraph' key (from cone_extract)
        k, semantic: forwarded to wl_hash()

    Returns:
        hash_str, convergence_info
    """
    G = cone_data['subgraph']
    graph_hash, _, conv_info = wl_hash(G, k=k, semantic=semantic)
    return graph_hash, conv_info


def wl_hash_all_cones(cones_dict, k=3, semantic=False):
    """
    Compute WL hashes for all cones of a design.

    Parameters:
        cones_dict: dict from extract_all_cones() — {po_node: {subgraph, nodes, stats}}
        k, semantic: forwarded to wl_hash()

    Returns:
        dict of {po_node: {'hash': str, 'convergence': dict, 'stats': dict}}
    """
    results = {}
    for po_node, cone_data in cones_dict.items():
        graph_hash, conv_info = wl_hash_cone(cone_data, k=k, semantic=semantic)
        results[po_node] = {
            'hash': graph_hash,
            'convergence': conv_info,
            'stats': cone_data['stats'],
        }
    return results


def wl_sensitivity_analysis(cone_data, max_k=6, semantic=False):
    """
    Analyze WL hash sensitivity to iteration depth.

    Returns:
        list of dicts, one per k value, with hash and convergence info
    """
    results = []
    G = cone_data['subgraph']

    for k in range(1, max_k + 1):
        graph_hash, label_history, conv_info = wl_hash(G, k=k, semantic=semantic)
        results.append({
            'k': k,
            'hash': graph_hash,
            'unique_labels': conv_info['unique_labels'],
            'converged_at': conv_info['converged_at'],
            'final_unique': conv_info['final_unique'],
        })

    return results


if __name__ == "__main__":
    import sys
    import os

    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from parse_aiger import load_all_aigs
    from cone_extract import extract_all_cones

    print("Loading AIGs and extracting cones...\n")
    aig_results = load_all_aigs()

    if not aig_results:
        print("[!] No AIG files. Run synthesize.py first.")
        sys.exit(1)

    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        cones = extract_all_cones(G, po_nodes)
        print(f"\n--- {name} ---")

        # Structure-only WL
        hashes = wl_hash_all_cones(cones, k=3, semantic=False)
        print(f"  Structure-only (k=3):")
        for po, data in sorted(hashes.items()):
            print(f"    {data['stats']['po_name']}: {data['hash']} "
                  f"(conv@{data['convergence']['converged_at']}, "
                  f"unique={data['convergence']['final_unique']})")

        # Semantic-aware WL
        hashes_sem = wl_hash_all_cones(cones, k=3, semantic=True)
        print(f"  Semantic-aware (k=3):")
        for po, data in sorted(hashes_sem.items()):
            print(f"    {data['stats']['po_name']}: {data['hash']} "
                  f"(conv@{data['convergence']['converged_at']}, "
                  f"unique={data['convergence']['final_unique']})")
