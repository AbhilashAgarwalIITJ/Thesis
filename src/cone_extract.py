"""
cone_extract.py - Extract output cones (fan-in cones) from AIG graphs.

MTP Phase: MTP-2 (core cone extraction)

An output cone for a primary output (PO) is the subgraph of all nodes
that transitively feed into that output. This is the backward transitive
fan-in from the PO node.
"""

import os
import sys
import json
import time
import networkx as nx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import from sibling module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_aiger import load_all_aigs


def extract_cone(G, po_node):
    """
    Extract the fan-in cone for a primary output node.

    Uses backward BFS from PO to collect all ancestor nodes.

    Returns:
        cone_subgraph: NetworkX DiGraph (subgraph view)
        cone_nodes: set of node IDs in the cone
    """
    # Get all ancestors (transitive fan-in) of the PO node
    ancestors = nx.ancestors(G, po_node)
    cone_nodes = ancestors | {po_node}

    # Create subgraph
    cone_subgraph = G.subgraph(cone_nodes).copy()

    return cone_subgraph, cone_nodes


def extract_all_cones(G, po_nodes):
    """
    Extract cones for all primary outputs.

    Returns:
        dict of {po_node: {'subgraph': G_cone, 'nodes': set, 'stats': dict}}
    """
    cones = {}

    for po in po_nodes:
        po_data = G.nodes[po]
        cone_subgraph, cone_nodes = extract_cone(G, po)

        # Compute cone statistics
        n_pi = sum(1 for n in cone_nodes if G.nodes[n].get('type') == 'PI')
        n_and = sum(1 for n in cone_nodes if G.nodes[n].get('type') == 'AND')

        # Compute cone depth
        depth = 0
        for node in cone_nodes:
            if G.nodes[node].get('type') == 'PI':
                try:
                    path_len = nx.shortest_path_length(cone_subgraph, node, po)
                    depth = max(depth, path_len)
                except nx.NetworkXNoPath:
                    continue

        stats = {
            'po_name': po_data.get('name', f'po_{po}'),
            'po_var': po,
            'num_nodes': len(cone_nodes),
            'num_edges': cone_subgraph.number_of_edges(),
            'num_pi': n_pi,
            'num_and': n_and,
            'depth': depth,
        }

        cones[po] = {
            'subgraph': cone_subgraph,
            'nodes': cone_nodes,
            'stats': stats,
        }

    return cones


def batch_extract_cones(aig_results):
    """
    Extract cones for all loaded AIG designs.

    Parameters:
        aig_results: dict from load_all_aigs()

    Returns:
        dict of {design_name: {cones_dict, extraction_time, summary_stats}}
    """
    all_cones = {}

    for name, (G, po_nodes, parsed, graph_stats) in sorted(aig_results.items()):
        start = time.time()
        cones = extract_all_cones(G, po_nodes)
        elapsed = time.time() - start

        # Summary stats
        cone_sizes = [c['stats']['num_nodes'] for c in cones.values()]
        cone_depths = [c['stats']['depth'] for c in cones.values()]

        summary = {
            'design': name,
            'num_cones': len(cones),
            'avg_cone_size': round(sum(cone_sizes) / len(cone_sizes), 1) if cone_sizes else 0,
            'max_cone_size': max(cone_sizes) if cone_sizes else 0,
            'min_cone_size': min(cone_sizes) if cone_sizes else 0,
            'avg_cone_depth': round(sum(cone_depths) / len(cone_depths), 1) if cone_depths else 0,
            'max_cone_depth': max(cone_depths) if cone_depths else 0,
            'extraction_time_ms': round(elapsed * 1000, 1),
        }

        all_cones[name] = {
            'cones': cones,
            'summary': summary,
            'graph': G,
            'po_nodes': po_nodes,
        }

        print(f"[+] {name}: {summary['num_cones']} cones, "
              f"avg size={summary['avg_cone_size']}, "
              f"max depth={summary['max_cone_depth']}, "
              f"time={summary['extraction_time_ms']}ms")

    return all_cones


if __name__ == "__main__":
    print("Loading AIG files...\n")
    aig_results = load_all_aigs()

    if not aig_results:
        print("[!] No AIG files found. Run synthesize.py first.")
        sys.exit(1)

    print(f"\nExtracting output cones...\n")
    all_cones = batch_extract_cones(aig_results)

    # Print summary table
    print(f"\n{'='*90}")
    print(f"{'Design':<25} {'Cones':>5} {'Avg Size':>9} {'Max Size':>9} "
          f"{'Avg Depth':>10} {'Max Depth':>10} {'Time(ms)':>9}")
    print(f"{'='*90}")
    for name, data in sorted(all_cones.items()):
        s = data['summary']
        print(f"{name:<25} {s['num_cones']:>5} {s['avg_cone_size']:>9.1f} "
              f"{s['max_cone_size']:>9} {s['avg_cone_depth']:>10.1f} "
              f"{s['max_cone_depth']:>10} {s['extraction_time_ms']:>9.1f}")
    print(f"{'='*90}")

    # Save cone stats
    stats_path = os.path.join(PROJECT_ROOT, "results", "cone_stats.json")
    stats_dict = {name: data['summary'] for name, data in all_cones.items()}
    with open(stats_path, "w") as f:
        json.dump(stats_dict, f, indent=2)
    print(f"\n[+] Cone stats saved to {stats_path}")
