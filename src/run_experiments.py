"""
run_experiments.py - Master experiment runner.

Runs all 5 experiments, generates tables and plots.
Experiment 1: Pipeline Validation (end-to-end demo)
Experiment 2: Self-Equivalence Under Re-synthesis (optimization levels)
Experiment 3: Mutation Detection
Experiment 4: Scalability Analysis
Experiment 5: WL Iteration Depth Sensitivity
"""

import os
import sys
import json
import time
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_aiger import parse_aiger_file, aiger_to_networkx, get_graph_stats, load_all_aigs
from cone_extract import extract_all_cones
from wl_hash import wl_hash_all_cones, wl_sensitivity_analysis
from match_cones import match_designs, print_match_result
from synthesize import find_yosys, synthesize_to_aig

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
TABLES_DIR = os.path.join(RESULTS_DIR, "tables")
AIG_DIR = os.path.join(PROJECT_ROOT, "aig_output")
DESIGNS_DIR = os.path.join(PROJECT_ROOT, "designs")

os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)


def synthesize_all(yosys_bin):
    """Synthesize all designs needed for experiments."""
    designs = {
        'adder_4bit':  os.path.join(DESIGNS_DIR, 'adder_4bit.v'),
        'adder_8bit':  os.path.join(DESIGNS_DIR, 'adder_8bit.v'),
        'adder_16bit': os.path.join(DESIGNS_DIR, 'adder_16bit.v'),
        'adder_32bit': os.path.join(DESIGNS_DIR, 'adder_32bit.v'),
        'mux_4to1':    os.path.join(DESIGNS_DIR, 'mux_4to1.v'),
        'counter_4bit': os.path.join(DESIGNS_DIR, 'counter_4bit.v'),
        'adder_4bit_mut1': os.path.join(DESIGNS_DIR, 'mutants', 'adder_4bit_mut1.v'),
        'adder_4bit_mut2': os.path.join(DESIGNS_DIR, 'mutants', 'adder_4bit_mut2.v'),
    }

    print("\n" + "="*60)
    print("SYNTHESIS PHASE")
    print("="*60 + "\n")

    for name, vpath in designs.items():
        out = os.path.join(AIG_DIR, f"{name}.aig")
        if not os.path.exists(out):
            synthesize_to_aig(yosys_bin, vpath, out)
        else:
            print(f"[.] Skipping {name} (already exists)")

    # Multi-optimization for Experiment 2
    adder_v = designs['adder_4bit']
    for opt in [0, 1, 2]:
        out = os.path.join(AIG_DIR, f"adder_4bit_O{opt}.aig")
        if not os.path.exists(out):
            synthesize_to_aig(yosys_bin, adder_v, out, opt_level=opt)
        else:
            print(f"[.] Skipping adder_4bit_O{opt} (already exists)")


def experiment_1(aig_results):
    """Experiment 1: Pipeline Validation — end-to-end on 4-bit adder."""
    print("\n" + "="*60)
    print("EXPERIMENT 1: Pipeline Validation (End-to-End)")
    print("="*60 + "\n")

    target = 'adder_4bit'
    if target not in aig_results:
        print(f"[!] {target} not found in AIG results")
        return None

    G, po_nodes, parsed, stats = aig_results[target]
    cones = extract_all_cones(G, po_nodes)
    hashes = wl_hash_all_cones(cones, k=3, semantic=False)
    hashes_sem = wl_hash_all_cones(cones, k=3, semantic=True)

    print(f"\nDesign: {target}")
    print(f"  AIGER header: M={parsed['M']} I={parsed['I']} L={parsed['L']} O={parsed['O']} A={parsed['A']}")
    print(f"  Graph: {stats['nodes']} nodes, {stats['edges']} edges")
    print(f"  Primary Inputs: {stats['primary_inputs']}")
    print(f"  AND gates: {stats['and_gates']}")
    print(f"  Primary Outputs: {stats['primary_outputs']}")
    print(f"  Depth: {stats['depth']}")
    print(f"\n  Output Cones:")
    for po, cone_data in cones.items():
        s = cone_data['stats']
        h = hashes[po]['hash']
        hs = hashes_sem[po]['hash']
        print(f"    {s['po_name']}: {s['num_nodes']} nodes, depth={s['depth']}, "
              f"WL={h[:12]}..., WL-sem={hs[:12]}...")

    return {
        'design': target,
        'parsed': {k: v for k, v in parsed.items() if k != 'filepath'},
        'stats': stats,
        'cones': {str(po): cone_data['stats'] for po, cone_data in cones.items()},
        'hashes': {str(po): d['hash'] for po, d in hashes.items()},
    }


def experiment_2(aig_results):
    """Experiment 2: Self-Equivalence Under Re-synthesis (optimization levels)."""
    print("\n" + "="*60)
    print("EXPERIMENT 2: Self-Equivalence Under Re-synthesis")
    print("="*60 + "\n")

    opt_names = ['adder_4bit_O0', 'adder_4bit_O1', 'adder_4bit_O2']
    available = {n: aig_results[n] for n in opt_names if n in aig_results}

    if len(available) < 2:
        print("[!] Need at least 2 optimization variants")
        return None

    # Extract cones and hashes for each
    all_data = {}
    for name, (G, po_nodes, parsed, stats) in available.items():
        cones = extract_all_cones(G, po_nodes)
        hashes = wl_hash_all_cones(cones, k=3, semantic=False)
        all_data[name] = {
            'cones': cones, 'hashes': hashes, 'stats': stats,
            'graph': G, 'po_nodes': po_nodes
        }
        print(f"  {name}: {stats['nodes']} nodes, {stats['edges']} edges, "
              f"{stats['and_gates']} AND gates")

    # Compare all pairs
    results = []
    names = sorted(all_data.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            result = match_designs(
                all_data[names[i]]['cones'], all_data[names[i]]['hashes'],
                all_data[names[j]]['cones'], all_data[names[j]]['hashes'],
                names[i], names[j]
            )
            print_match_result(result)
            results.append(result)

    return results


def experiment_3(aig_results):
    """Experiment 3: Mutation Detection."""
    print("\n" + "="*60)
    print("EXPERIMENT 3: Mutation Detection")
    print("="*60 + "\n")

    original = 'adder_4bit'
    mutants = ['adder_4bit_mut1', 'adder_4bit_mut2']

    if original not in aig_results:
        print(f"[!] {original} not found")
        return None

    # Get original data
    G_orig, po_orig, _, stats_orig = aig_results[original]
    cones_orig = extract_all_cones(G_orig, po_orig)
    hashes_orig = wl_hash_all_cones(cones_orig, k=3, semantic=False)

    results = []
    for mut_name in mutants:
        if mut_name not in aig_results:
            print(f"[!] {mut_name} not found, skipping")
            continue

        G_mut, po_mut, _, stats_mut = aig_results[mut_name]
        cones_mut = extract_all_cones(G_mut, po_mut)
        hashes_mut = wl_hash_all_cones(cones_mut, k=3, semantic=False)

        result = match_designs(
            cones_orig, hashes_orig,
            cones_mut, hashes_mut,
            original, mut_name
        )
        print_match_result(result)
        results.append(result)

    return results


def experiment_4(aig_results):
    """Experiment 4: Scalability Analysis."""
    print("\n" + "="*60)
    print("EXPERIMENT 4: Scalability Analysis")
    print("="*60 + "\n")

    scalability_designs = ['adder_4bit', 'adder_8bit', 'adder_16bit', 'adder_32bit']
    rows = []

    for name in scalability_designs:
        if name not in aig_results:
            print(f"[!] {name} not found, skipping")
            continue

        G, po_nodes, parsed, stats = aig_results[name]

        # Time cone extraction
        start = time.time()
        cones = extract_all_cones(G, po_nodes)
        cone_time = (time.time() - start) * 1000

        # Time WL hashing
        start = time.time()
        hashes = wl_hash_all_cones(cones, k=3, semantic=False)
        wl_time = (time.time() - start) * 1000

        bits = int(''.join(filter(str.isdigit, name)))
        row = {
            'design': name,
            'bits': bits,
            'nodes': stats['nodes'],
            'edges': stats['edges'],
            'and_gates': stats['and_gates'],
            'pi': stats['primary_inputs'],
            'po': stats['primary_outputs'],
            'depth': stats['depth'],
            'num_cones': len(cones),
            'cone_extract_ms': round(cone_time, 2),
            'wl_hash_ms': round(wl_time, 2),
            'total_ms': round(cone_time + wl_time, 2),
        }
        rows.append(row)
        print(f"  {name}: {row['nodes']} nodes, {row['edges']} edges, "
              f"cones={row['num_cones']}, total={row['total_ms']}ms")

    return rows


def experiment_5(aig_results):
    """Experiment 5: WL Iteration Depth Sensitivity."""
    print("\n" + "="*60)
    print("EXPERIMENT 5: WL Iteration Depth Sensitivity")
    print("="*60 + "\n")

    target = 'adder_8bit'
    if target not in aig_results:
        # Fall back to adder_4bit
        target = 'adder_4bit'
        if target not in aig_results:
            print("[!] No suitable design found")
            return None

    G, po_nodes, parsed, stats = aig_results[target]
    cones = extract_all_cones(G, po_nodes)

    print(f"Design: {target} ({stats['nodes']} nodes, {len(cones)} cones)\n")

    # For each cone, test k=1..6
    all_results = {}
    max_k = 6

    for po, cone_data in cones.items():
        cone_name = cone_data['stats']['po_name']
        sensitivity = wl_sensitivity_analysis(cone_data, max_k=max_k, semantic=False)
        all_results[cone_name] = sensitivity

        print(f"  Cone {cone_name}:")
        for s in sensitivity:
            print(f"    k={s['k']}: hash={s['hash'][:12]}... unique_labels={s['final_unique']} "
                  f"converged@{s['converged_at']}")

    # Also aggregate: at each k, how many unique graph-level hashes across cones?
    k_summary = []
    for k_val in range(1, max_k + 1):
        hashes_at_k = set()
        total_unique_labels = 0
        for cone_name, sensitivity in all_results.items():
            for s in sensitivity:
                if s['k'] == k_val:
                    hashes_at_k.add(s['hash'])
                    total_unique_labels += s['final_unique']
        k_summary.append({
            'k': k_val,
            'unique_cone_hashes': len(hashes_at_k),
            'total_unique_labels': total_unique_labels,
            'avg_unique_labels': round(total_unique_labels / len(all_results), 1) if all_results else 0,
        })
        print(f"\n  k={k_val}: {len(hashes_at_k)} unique cone hashes, "
              f"avg unique labels per cone = {k_summary[-1]['avg_unique_labels']}")

    return {'design': target, 'cone_results': all_results, 'k_summary': k_summary}


# =============================================================================
# TABLE AND PLOT GENERATION
# =============================================================================

def generate_tables(exp1_data, exp2_data, exp3_data, exp4_data, exp5_data, aig_results):
    """Generate all result tables."""
    from tabulate import tabulate

    print("\n" + "="*60)
    print("GENERATING TABLES")
    print("="*60 + "\n")

    # Table 1: Circuit Statistics
    rows = []
    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        # Skip optimization variants for the main table
        if '_O0' in name or '_O1' in name or '_O2' in name:
            continue
        rows.append([
            name,
            stats['primary_inputs'],
            stats['primary_outputs'],
            stats['and_gates'],
            stats['nodes'],
            stats['edges'],
            stats['depth'],
        ])

    headers = ['Design', '#PI', '#PO', '#AND', 'Total Nodes', 'Total Edges', 'Depth']
    table1 = tabulate(rows, headers=headers, tablefmt='grid')
    print("Table 1: Circuit Statistics")
    print(table1)
    with open(os.path.join(TABLES_DIR, 'table1_circuit_stats.txt'), 'w') as f:
        f.write("Table 1: Circuit Statistics\n\n")
        f.write(table1)

    # Table 2: Cone Extraction Results
    rows2 = []
    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        if '_O0' in name or '_O1' in name or '_O2' in name:
            continue
        cones = extract_all_cones(G, po_nodes)
        sizes = [c['stats']['num_nodes'] for c in cones.values()]
        depths = [c['stats']['depth'] for c in cones.values()]
        rows2.append([
            name,
            len(cones),
            round(sum(sizes)/len(sizes), 1) if sizes else 0,
            max(sizes) if sizes else 0,
            round(sum(depths)/len(depths), 1) if depths else 0,
            max(depths) if depths else 0,
        ])
    headers2 = ['Design', '#Cones', 'Avg Size', 'Max Size', 'Avg Depth', 'Max Depth']
    table2 = tabulate(rows2, headers=headers2, tablefmt='grid')
    print("\nTable 2: Cone Extraction Results")
    print(table2)
    with open(os.path.join(TABLES_DIR, 'table2_cone_stats.txt'), 'w') as f:
        f.write("Table 2: Cone Extraction Results\n\n")
        f.write(table2)

    # Table 3: Matching Results
    all_match_results = []
    if exp2_data:
        all_match_results.extend(exp2_data)
    if exp3_data:
        all_match_results.extend(exp3_data)

    if all_match_results:
        rows3 = []
        for r in all_match_results:
            rows3.append([
                f"{r['design_a']} vs {r['design_b']}",
                r['total_compared'],
                r['matched'],
                r['diverged'],
                f"{r['match_pct']}%",
            ])
        headers3 = ['Design Pair', 'Cones Compared', 'Matched', 'Diverged', 'Match %']
        table3 = tabulate(rows3, headers=headers3, tablefmt='grid')
        print("\nTable 3: Cone Matching Results")
        print(table3)
        with open(os.path.join(TABLES_DIR, 'table3_matching.txt'), 'w') as f:
            f.write("Table 3: Cone Matching Results\n\n")
            f.write(table3)

    # Table 4: Scalability
    if exp4_data:
        rows4 = []
        for r in exp4_data:
            rows4.append([
                r['design'],
                r['bits'],
                r['nodes'],
                r['edges'],
                r['num_cones'],
                r['cone_extract_ms'],
                r['wl_hash_ms'],
                r['total_ms'],
            ])
        headers4 = ['Design', 'Bits', 'Nodes', 'Edges', '#Cones',
                     'Cone(ms)', 'WL(ms)', 'Total(ms)']
        table4 = tabulate(rows4, headers=headers4, tablefmt='grid')
        print("\nTable 4: Scalability Analysis")
        print(table4)
        with open(os.path.join(TABLES_DIR, 'table4_scalability.txt'), 'w') as f:
            f.write("Table 4: Scalability Analysis\n\n")
            f.write(table4)

    # Table 5: WL Convergence
    if exp5_data and exp5_data.get('k_summary'):
        rows5 = []
        for ks in exp5_data['k_summary']:
            rows5.append([
                ks['k'],
                ks['unique_cone_hashes'],
                ks['avg_unique_labels'],
                ks['total_unique_labels'],
            ])
        headers5 = ['k (iterations)', 'Unique Cone Hashes', 'Avg Unique Labels/Cone', 'Total Unique Labels']
        table5 = tabulate(rows5, headers=headers5, tablefmt='grid')
        print(f"\nTable 5: WL Convergence ({exp5_data['design']})")
        print(table5)
        with open(os.path.join(TABLES_DIR, 'table5_wl_convergence.txt'), 'w') as f:
            f.write(f"Table 5: WL Convergence Analysis ({exp5_data['design']})\n\n")
            f.write(table5)

    print(f"\n[+] All tables saved to {TABLES_DIR}")


def generate_plots(exp4_data, exp5_data, exp2_data, exp3_data, aig_results):
    """Generate all result plots."""
    print("\n" + "="*60)
    print("GENERATING PLOTS")
    print("="*60 + "\n")

    plt.style.use('seaborn-v0_8-whitegrid')

    # Plot 1: Scalability — Nodes/Edges vs Bit-width
    if exp4_data:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        bits = [r['bits'] for r in exp4_data]
        nodes = [r['nodes'] for r in exp4_data]
        edges = [r['edges'] for r in exp4_data]
        times = [r['total_ms'] for r in exp4_data]

        ax1.bar([str(b) for b in bits], nodes, color='steelblue', alpha=0.8, label='Nodes')
        ax1.bar([str(b) for b in bits], edges, color='coral', alpha=0.5, label='Edges')
        ax1.set_xlabel('Adder Bit-width')
        ax1.set_ylabel('Count')
        ax1.set_title('AIG Size vs Design Width')
        ax1.legend()

        ax2.plot(bits, times, 'o-', color='darkgreen', linewidth=2, markersize=8)
        ax2.set_xlabel('Adder Bit-width')
        ax2.set_ylabel('Total Time (ms)')
        ax2.set_title('Processing Time vs Design Width')

        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, 'plot1_scalability.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print("[+] Saved plot1_scalability.png")

    # Plot 2: WL Convergence
    if exp5_data and exp5_data.get('k_summary'):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ks = [s['k'] for s in exp5_data['k_summary']]
        unique_hashes = [s['unique_cone_hashes'] for s in exp5_data['k_summary']]
        avg_labels = [s['avg_unique_labels'] for s in exp5_data['k_summary']]

        ax1.plot(ks, unique_hashes, 'o-', color='steelblue', linewidth=2, markersize=8)
        ax1.set_xlabel('WL Iterations (k)')
        ax1.set_ylabel('Unique Cone Hashes')
        ax1.set_title('Cone Discrimination vs WL Depth')
        ax1.set_xticks(ks)

        ax2.plot(ks, avg_labels, 's-', color='coral', linewidth=2, markersize=8)
        ax2.set_xlabel('WL Iterations (k)')
        ax2.set_ylabel('Avg Unique Node Labels per Cone')
        ax2.set_title('Label Refinement vs WL Depth')
        ax2.set_xticks(ks)

        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, 'plot2_wl_convergence.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print("[+] Saved plot2_wl_convergence.png")

    # Plot 3: Matching Results Bar Chart
    all_match = []
    if exp2_data:
        all_match.extend(exp2_data)
    if exp3_data:
        all_match.extend(exp3_data)

    if all_match:
        fig, ax = plt.subplots(figsize=(10, 6))

        labels = [f"{r['design_a']}\nvs\n{r['design_b']}" for r in all_match]
        matched = [r['matched'] for r in all_match]
        diverged = [r['diverged'] for r in all_match]

        x = range(len(labels))
        width = 0.35
        bars1 = ax.bar([i - width/2 for i in x], matched, width, label='Matched', color='forestgreen', alpha=0.8)
        bars2 = ax.bar([i + width/2 for i in x], diverged, width, label='Diverged', color='crimson', alpha=0.8)

        ax.set_xlabel('Design Pair')
        ax.set_ylabel('Number of Cones')
        ax.set_title('Cone-Level Matching: Matched vs Diverged')
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=8)
        ax.legend()

        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords="offset points", ha='center', fontsize=9)
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords="offset points", ha='center', fontsize=9)

        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, 'plot3_matching.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print("[+] Saved plot3_matching.png")

    # Plot 4: Circuit Statistics Overview
    fig, ax = plt.subplots(figsize=(10, 6))
    design_names = []
    and_counts = []
    for name, (G, po_nodes, parsed, stats) in sorted(aig_results.items()):
        if '_O0' in name or '_O1' in name or '_O2' in name:
            continue
        design_names.append(name)
        and_counts.append(stats['and_gates'])

    ax.barh(design_names, and_counts, color='steelblue', alpha=0.8)
    ax.set_xlabel('Number of AND Gates')
    ax.set_title('AIG Complexity: AND Gate Count per Design')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'plot4_circuit_overview.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved plot4_circuit_overview.png")

    print(f"\n[+] All plots saved to {PLOTS_DIR}")


def generate_visualizations(aig_results):
    """Generate AIG graph and cone visualizations."""
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60 + "\n")

    # Visualize a small AIG (4-bit adder)
    target = 'adder_4bit'
    if target not in aig_results:
        print(f"[!] {target} not found")
        return

    G, po_nodes, parsed, stats = aig_results[target]
    cones = extract_all_cones(G, po_nodes)

    # Plot 1: Full AIG graph
    fig, ax = plt.subplots(figsize=(14, 10))

    # Color nodes by type
    color_map = []
    for node in G.nodes():
        ntype = G.nodes[node].get('type', '')
        if ntype == 'PI':
            color_map.append('#4CAF50')  # green
        elif ntype == 'AND':
            color_map.append('#2196F3')  # blue
        elif ntype == 'PO':
            color_map.append('#F44336')  # red
        else:
            color_map.append('#9E9E9E')  # grey

    # Use layered layout
    try:
        # Try topological layout
        for layer, nodes in enumerate(nx.topological_generations(G)):
            for node in nodes:
                G.nodes[node]["layer"] = layer
        pos = nx.multipartite_layout(G, subset_key="layer")
    except Exception:
        pos = nx.spring_layout(G, seed=42, k=2)

    # Draw edges with inversion indication
    inv_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('inverted')]
    norm_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get('inverted')]

    nx.draw_networkx_edges(G, pos, edgelist=norm_edges, ax=ax,
                           edge_color='#666666', alpha=0.6, arrows=True, arrowsize=10)
    nx.draw_networkx_edges(G, pos, edgelist=inv_edges, ax=ax,
                           edge_color='#FF9800', alpha=0.8, arrows=True, arrowsize=10,
                           style='dashed')

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=color_map, node_size=300, alpha=0.9)

    # Labels: show node names
    labels = {n: G.nodes[n].get('name', str(n))[:8] for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=6)

    ax.set_title(f'AIG Graph: {target} ({stats["nodes"]} nodes, {stats["edges"]} edges)')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4CAF50', label='Primary Input (PI)'),
        Patch(facecolor='#2196F3', label='AND Gate'),
        Patch(facecolor='#F44336', label='Primary Output (PO)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left')

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'viz1_aig_graph.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved viz1_aig_graph.png")

    # Plot 2: Highlighted cones
    fig, ax = plt.subplots(figsize=(14, 10))

    import matplotlib.cm as cm
    cone_colors = cm.get_cmap('tab10', len(cones))

    # First draw all nodes in grey
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#CCCCCC', alpha=0.3, arrows=True, arrowsize=8)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='#EEEEEE', node_size=200, alpha=0.5)

    # Then overlay each cone with a distinct color
    for idx, (po, cone_data) in enumerate(sorted(cones.items())):
        cone_nodes = list(cone_data['nodes'])
        cone_subgraph = cone_data['subgraph']
        color = cone_colors(idx)

        cone_pos = {n: pos[n] for n in cone_nodes if n in pos}
        nx.draw_networkx_nodes(G, cone_pos, nodelist=[n for n in cone_nodes if n in pos],
                               ax=ax, node_color=[color], node_size=350, alpha=0.8)

    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=6)

    ax.set_title(f'Output Cones: {target} ({len(cones)} cones, color-coded)')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'viz2_cones.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved viz2_cones.png")

    print(f"\n[+] Visualizations saved to {PLOTS_DIR}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import networkx as nx

    print("="*60)
    print("THESIS EXPERIMENT RUNNER")
    print("AI-Augmented Verilog Netlist Matching Using AIG and GNNs")
    print("="*60)

    # Step 1: Find Yosys
    yosys_bin = find_yosys()
    if not yosys_bin:
        print("[!] Yosys not found. Cannot proceed.")
        sys.exit(1)

    # Step 2: Synthesize all designs
    synthesize_all(yosys_bin)

    # Step 3: Load all AIGs
    print("\n" + "="*60)
    print("LOADING ALL AIG FILES")
    print("="*60 + "\n")
    aig_results = load_all_aigs()

    if not aig_results:
        print("[!] No AIG files found after synthesis.")
        sys.exit(1)

    # Step 4: Run experiments
    exp1_data = experiment_1(aig_results)
    exp2_data = experiment_2(aig_results)
    exp3_data = experiment_3(aig_results)
    exp4_data = experiment_4(aig_results)
    exp5_data = experiment_5(aig_results)

    # Step 5: Generate tables
    generate_tables(exp1_data, exp2_data, exp3_data, exp4_data, exp5_data, aig_results)

    # Step 6: Generate plots
    generate_plots(exp4_data, exp5_data, exp2_data, exp3_data, aig_results)

    # Step 7: Generate visualizations
    generate_visualizations(aig_results)

    # Step 8: Save all experiment data
    all_data = {
        'experiment_1': exp1_data,
        'experiment_2': [
            {k: v for k, v in r.items()} for r in (exp2_data or [])
        ],
        'experiment_3': [
            {k: v for k, v in r.items()} for r in (exp3_data or [])
        ],
        'experiment_4': exp4_data,
        'experiment_5': {
            'design': exp5_data['design'] if exp5_data else None,
            'k_summary': exp5_data['k_summary'] if exp5_data else None,
        } if exp5_data else None,
    }

    with open(os.path.join(RESULTS_DIR, 'all_experiments.json'), 'w') as f:
        json.dump(all_data, f, indent=2, default=str)

    print("\n" + "="*60)
    print("ALL EXPERIMENTS COMPLETE")
    print("="*60)
    print(f"\nResults directory: {RESULTS_DIR}")
    print(f"  Tables: {TABLES_DIR}")
    print(f"  Plots:  {PLOTS_DIR}")
    print(f"  Data:   {os.path.join(RESULTS_DIR, 'all_experiments.json')}")
