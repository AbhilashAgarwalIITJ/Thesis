"""
generate_plots.py — Thesis-quality plots from CSV data.

MTP Phase: MTP-2 (preliminary visualisations)

Reads CSVs from results/csv/ and produces publication-ready PNGs.
Each plot corresponds to a thesis slide or report figure.

Plots generated:
  1. Circuit complexity overview (bar chart)
  2. Scalability: size and time vs bit-width
  3. WL convergence: label refinement vs k
  4. Baseline matching: matched vs diverged cones
  5. Advanced comparison: baseline vs semantic vs polarity (grouped bar)
  6. AIG graph visualization
  7. Cone-highlighted visualization
"""

import os, sys, csv
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

CSV_DIR = os.path.join(PROJECT_ROOT, "results", "csv")
PLOTS_DIR = os.path.join(PROJECT_ROOT, "results", "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# Consistent color palette
COLORS = {
    'blue': '#2196F3',
    'green': '#4CAF50',
    'red': '#F44336',
    'orange': '#FF9800',
    'purple': '#9C27B0',
    'grey': '#9E9E9E',
    'teal': '#009688',
    'dark_blue': '#1565C0',
}


def _read_csv(filename):
    """Read a CSV file from results/csv/."""
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        print(f"[!] CSV not found: {path}")
        return []
    with open(path, 'r') as f:
        return list(csv.DictReader(f))


def plot_circuit_overview():
    """Plot 1: Circuit complexity — AND gates and depth per design."""
    rows = _read_csv('graph_statistics.csv')
    if not rows:
        return

    # Filter out optimization variants for cleaner view
    rows = [r for r in rows if '_O0' not in r['design'] and '_O1' not in r['design'] and '_O2' not in r['design']]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    names = [r['design'] for r in rows]
    and_gates = [int(r['and_gates']) for r in rows]
    depths = [int(r['depth']) for r in rows]
    y_pos = range(len(names))

    # AND gates
    ax1.barh(y_pos, and_gates, color=COLORS['blue'], alpha=0.85)
    ax1.set_yticks(list(y_pos))
    ax1.set_yticklabels(names, fontsize=9)
    ax1.set_xlabel('AND Gate Count', fontsize=11)
    ax1.set_title('AIG Complexity: AND Gates', fontsize=12, fontweight='bold')
    for i, v in enumerate(and_gates):
        ax1.text(v + 1, i, str(v), va='center', fontsize=9)

    # Depth
    ax2.barh(y_pos, depths, color=COLORS['teal'], alpha=0.85)
    ax2.set_yticks(list(y_pos))
    ax2.set_yticklabels(names, fontsize=9)
    ax2.set_xlabel('Graph Depth (longest path)', fontsize=11)
    ax2.set_title('AIG Depth', fontsize=12, fontweight='bold')
    for i, v in enumerate(depths):
        ax2.text(v + 0.5, i, str(v), va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig1_circuit_overview.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved fig1_circuit_overview.png")


def plot_scalability():
    """Plot 2: Scalability — nodes/edges and time vs adder bit-width."""
    rows = _read_csv('scalability.csv')
    if not rows:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    bits = [int(r['bits']) for r in rows]
    nodes = [int(r['nodes']) for r in rows]
    edges = [int(r['edges']) for r in rows]
    total_ms = [float(r['total_ms']) for r in rows]

    x = np.arange(len(bits))
    width = 0.35

    ax1.bar(x - width/2, nodes, width, label='Nodes', color=COLORS['blue'], alpha=0.85)
    ax1.bar(x + width/2, edges, width, label='Edges', color=COLORS['orange'], alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{b}-bit" for b in bits])
    ax1.set_ylabel('Count', fontsize=11)
    ax1.set_title('AIG Size vs Adder Bit-Width', fontsize=12, fontweight='bold')
    ax1.legend()

    ax2.plot(bits, total_ms, 'o-', color=COLORS['dark_blue'], linewidth=2.5, markersize=9)
    ax2.fill_between(bits, total_ms, alpha=0.15, color=COLORS['blue'])
    ax2.set_xlabel('Adder Bit-Width', fontsize=11)
    ax2.set_ylabel('Processing Time (ms)', fontsize=11)
    ax2.set_title('Pipeline Runtime vs Design Width', fontsize=12, fontweight='bold')
    ax2.set_xticks(bits)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig2_scalability.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved fig2_scalability.png")


def plot_wl_convergence():
    """Plot 3: WL depth sensitivity — label refinement vs k."""
    rows = _read_csv('wl_convergence.csv')
    if not rows:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ks = [int(r['k']) for r in rows]
    unique_hashes = [int(r['unique_cone_hashes']) for r in rows]
    avg_labels = [float(r['avg_unique_labels']) for r in rows]

    ax1.plot(ks, unique_hashes, 'o-', color=COLORS['blue'], linewidth=2.5, markersize=9)
    ax1.set_xlabel('WL Iterations (k)', fontsize=11)
    ax1.set_ylabel('Unique Cone Hashes', fontsize=11)
    ax1.set_title('Cone Discrimination vs WL Depth', fontsize=12, fontweight='bold')
    ax1.set_xticks(ks)
    ax1.set_ylim(bottom=0)

    ax2.plot(ks, avg_labels, 's-', color=COLORS['red'], linewidth=2.5, markersize=9)
    ax2.fill_between(ks, avg_labels, alpha=0.12, color=COLORS['red'])
    ax2.set_xlabel('WL Iterations (k)', fontsize=11)
    ax2.set_ylabel('Avg Unique Labels per Cone', fontsize=11)
    ax2.set_title('Label Refinement vs WL Depth', fontsize=12, fontweight='bold')
    ax2.set_xticks(ks)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig3_wl_convergence.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved fig3_wl_convergence.png")


def plot_baseline_matching():
    """Plot 4: Baseline matching — matched vs diverged cones per pair."""
    rows = _read_csv('baseline_matching.csv')
    if not rows:
        return

    fig, ax = plt.subplots(figsize=(11, 6))

    labels = [f"{r['design_a']}\nvs\n{r['design_b']}" for r in rows]
    matched = [int(r['matched']) for r in rows]
    diverged = [int(r['diverged']) for r in rows]

    x = np.arange(len(labels))
    width = 0.35

    bars1 = ax.bar(x - width/2, matched, width, label='Matched Cones',
                    color=COLORS['green'], alpha=0.85)
    bars2 = ax.bar(x + width/2, diverged, width, label='Diverged Cones',
                    color=COLORS['red'], alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Number of Cones', fontsize=11)
    ax.set_title('Cone-Level Structural Matching Results (Baseline WL)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)

    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.1, str(int(h)),
                    ha='center', fontsize=9, fontweight='bold')
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.1, str(int(h)),
                    ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig4_baseline_matching.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved fig4_baseline_matching.png")


def plot_advanced_comparison():
    """Plot 5: Advanced — baseline vs semantic vs polarity match rates."""
    rows = _read_csv('advanced_matching_summary.csv')
    if not rows:
        return

    fig, ax = plt.subplots(figsize=(13, 6))

    labels = [f"{r['design_a']}\nvs\n{r['design_b']}" for r in rows]
    baseline = [float(r['baseline_pct']) for r in rows]
    semantic = [float(r['semantic_pct']) for r in rows]
    polarity = [float(r['polarity_pct']) for r in rows]

    x = np.arange(len(labels))
    width = 0.25

    ax.bar(x - width, baseline, width, label='Baseline WL', color=COLORS['blue'], alpha=0.85)
    ax.bar(x, semantic, width, label='Semantic-Aware WL', color=COLORS['green'], alpha=0.85)
    ax.bar(x + width, polarity, width, label='Inversion-Aware WL', color=COLORS['purple'], alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Match Rate (%)', fontsize=11)
    ax.set_title('Cone Match Rate: Baseline vs Semantic vs Inversion-Aware WL', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.set_ylim(0, 110)

    # Add value labels
    for i, (b, s, p) in enumerate(zip(baseline, semantic, polarity)):
        ax.text(i - width, b + 1.5, f"{b:.0f}%", ha='center', fontsize=8)
        ax.text(i, s + 1.5, f"{s:.0f}%", ha='center', fontsize=8)
        ax.text(i + width, p + 1.5, f"{p:.0f}%", ha='center', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig5_advanced_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved fig5_advanced_comparison.png")


def plot_aig_visualization():
    """Plot 6 & 7: AIG graph + cone visualization for 4-bit adder."""
    from parse_aiger import load_all_aigs
    from cone_extract import extract_all_cones
    import networkx as nx

    aig_results = load_all_aigs()
    target = 'adder_4bit'
    if target not in aig_results:
        print(f"[!] {target} not found for visualization")
        return

    G, po_nodes, parsed, stats = aig_results[target]
    cones = extract_all_cones(G, po_nodes)

    # Layout
    try:
        for layer, nodes_in_layer in enumerate(nx.topological_generations(G)):
            for node in nodes_in_layer:
                G.nodes[node]["layer"] = layer
        pos = nx.multipartite_layout(G, subset_key="layer")
    except Exception:
        pos = nx.spring_layout(G, seed=42, k=2)

    # === Plot 6: Full AIG graph ===
    fig, ax = plt.subplots(figsize=(14, 10))

    color_map = []
    for node in G.nodes():
        ntype = G.nodes[node].get('type', '')
        if ntype == 'PI':
            color_map.append(COLORS['green'])
        elif ntype == 'AND':
            color_map.append(COLORS['blue'])
        elif ntype == 'PO':
            color_map.append(COLORS['red'])
        else:
            color_map.append(COLORS['grey'])

    inv_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('inverted')]
    norm_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get('inverted')]

    nx.draw_networkx_edges(G, pos, edgelist=norm_edges, ax=ax,
                           edge_color='#666666', alpha=0.5, arrows=True, arrowsize=10)
    nx.draw_networkx_edges(G, pos, edgelist=inv_edges, ax=ax,
                           edge_color=COLORS['orange'], alpha=0.7, arrows=True,
                           arrowsize=10, style='dashed')
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=color_map, node_size=300, alpha=0.9)

    labels = {n: G.nodes[n].get('name', str(n))[:8] for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=6)

    legend_elements = [
        mpatches.Patch(facecolor=COLORS['green'], label='Primary Input (PI)'),
        mpatches.Patch(facecolor=COLORS['blue'], label='AND Gate'),
        mpatches.Patch(facecolor=COLORS['red'], label='Primary Output (PO)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
    ax.set_title(f'AIG Graph: {target} ({stats["nodes"]} nodes, {stats["edges"]} edges)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig6_aig_graph.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved fig6_aig_graph.png")

    # === Plot 7: Cone visualization ===
    fig, ax = plt.subplots(figsize=(14, 10))

    cone_palette = ['#E91E63', '#3F51B5', '#009688', '#FF9800', '#795548',
                    '#607D8B', '#9C27B0', '#CDDC39', '#00BCD4']

    # Background
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#DDDDDD', alpha=0.3, arrows=True, arrowsize=8)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='#EEEEEE', node_size=200, alpha=0.4)

    legend_patches = []
    for idx, (po, cone_data) in enumerate(sorted(cones.items())):
        cone_nodes = [n for n in cone_data['nodes'] if n in pos]
        color = cone_palette[idx % len(cone_palette)]
        nx.draw_networkx_nodes(G, pos, nodelist=cone_nodes, ax=ax,
                               node_color=[color]*len(cone_nodes), node_size=350, alpha=0.8)
        legend_patches.append(mpatches.Patch(facecolor=color,
                              label=f"{cone_data['stats']['po_name']} ({cone_data['stats']['num_nodes']} nodes)"))

    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=6)
    ax.legend(handles=legend_patches, loc='upper left', fontsize=9)
    ax.set_title(f'Output Cones: {target} ({len(cones)} cones, color-coded)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'fig7_cone_visualization.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("[+] Saved fig7_cone_visualization.png")


def generate_all_plots():
    """Generate all thesis plots."""
    print("\n" + "="*60)
    print("GENERATING THESIS PLOTS")
    print("="*60 + "\n")

    plot_circuit_overview()
    plot_scalability()
    plot_wl_convergence()
    plot_baseline_matching()
    plot_advanced_comparison()
    plot_aig_visualization()

    print(f"\n[+] All plots saved to {PLOTS_DIR}")


if __name__ == "__main__":
    generate_all_plots()
