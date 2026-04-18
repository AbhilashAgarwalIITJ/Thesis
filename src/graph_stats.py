"""
graph_stats.py — Extract and export graph-level and node-level statistics.

MTP Phase: MTP-2 (statistics collection)

Produces:
  - graph_statistics.csv: per-design summary (nodes, edges, PI, AND, PO, depth)
  - cone_statistics.csv:  per-cone breakdown across all designs

Used for: Table 1, Table 2, circuit overview plot.
"""

import os, sys, csv, json
import networkx as nx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_aiger import load_all_aigs
from cone_extract import extract_all_cones

CSV_DIR = os.path.join(PROJECT_ROOT, "results", "csv")
os.makedirs(CSV_DIR, exist_ok=True)


def compute_graph_statistics(aig_results, skip_opt_variants=False):
    """
    Compute per-design graph statistics.

    Returns list of dicts, one per design.
    """
    rows = []
    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        if skip_opt_variants and ('_O0' in name or '_O1' in name or '_O2' in name):
            continue
        rows.append({
            'design': name,
            'primary_inputs': stats['primary_inputs'],
            'primary_outputs': stats['primary_outputs'],
            'and_gates': stats['and_gates'],
            'total_nodes': stats['nodes'],
            'total_edges': stats['edges'],
            'depth': stats['depth'],
        })
    return rows


def compute_cone_statistics(aig_results, skip_opt_variants=False):
    """
    Compute per-cone statistics across all designs.

    Returns:
        cone_rows: list of dicts (one per cone)
        summary_rows: list of dicts (one per design, aggregated)
    """
    cone_rows = []
    summary_rows = []

    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        if skip_opt_variants and ('_O0' in name or '_O1' in name or '_O2' in name):
            continue

        cones = extract_all_cones(G, po_nodes)
        sizes = []
        depths = []

        for po, cone_data in sorted(cones.items()):
            s = cone_data['stats']
            cone_rows.append({
                'design': name,
                'cone_name': s['po_name'],
                'cone_nodes': s['num_nodes'],
                'cone_edges': s['num_edges'],
                'cone_pi': s['num_pi'],
                'cone_and': s['num_and'],
                'cone_depth': s['depth'],
            })
            sizes.append(s['num_nodes'])
            depths.append(s['depth'])

        summary_rows.append({
            'design': name,
            'num_cones': len(cones),
            'avg_cone_size': round(sum(sizes) / len(sizes), 1) if sizes else 0,
            'max_cone_size': max(sizes) if sizes else 0,
            'min_cone_size': min(sizes) if sizes else 0,
            'avg_cone_depth': round(sum(depths) / len(depths), 1) if depths else 0,
            'max_cone_depth': max(depths) if depths else 0,
        })

    return cone_rows, summary_rows


def export_graph_stats_csv(rows, filename='graph_statistics.csv'):
    """Write graph statistics to CSV."""
    path = os.path.join(CSV_DIR, filename)
    if not rows:
        return path
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[+] Saved {path}")
    return path


def export_cone_stats_csv(cone_rows, summary_rows):
    """Write cone statistics to CSV files."""
    p1 = os.path.join(CSV_DIR, 'cone_details.csv')
    p2 = os.path.join(CSV_DIR, 'cone_summary.csv')

    if cone_rows:
        with open(p1, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=cone_rows[0].keys())
            writer.writeheader()
            writer.writerows(cone_rows)
        print(f"[+] Saved {p1}")

    if summary_rows:
        with open(p2, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"[+] Saved {p2}")

    return p1, p2


if __name__ == "__main__":
    print("Computing graph statistics...\n")
    aig_results = load_all_aigs()

    graph_rows = compute_graph_statistics(aig_results)
    export_graph_stats_csv(graph_rows)

    cone_rows, summary_rows = compute_cone_statistics(aig_results)
    export_cone_stats_csv(cone_rows, summary_rows)

    print("\nDone.")
