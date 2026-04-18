"""
run_all.py — Master thesis pipeline orchestrator.

MTP Phase: MTP-2 (original pipeline runner)

Runs the COMPLETE thesis pipeline end-to-end:
  Phase 1: Synthesis (Verilog → AIG via Yosys)
  Phase 2: Graph statistics extraction → CSV
  Phase 3: Cone extraction statistics → CSV
  Phase 4: Baseline matching experiments → CSV
  Phase 5: Scalability experiment → CSV
  Phase 6: WL convergence experiment → CSV
  Phase 7: Advanced WL experiment → CSV
  Phase 8: Plot generation (7 figures)
  Phase 9: Explainability reports (3 reports)

Usage:
  cd IIT_Thesis_2.0
  .venv\\Scripts\\activate
  python src/run_all.py

All outputs go to results/csv/, results/plots/, results/reports/.
"""

import os, sys, csv, json, time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthesize import find_yosys, synthesize_to_aig
from parse_aiger import load_all_aigs
from cone_extract import extract_all_cones
from wl_hash import wl_hash_all_cones, wl_sensitivity_analysis
from match_cones import match_designs
from graph_stats import (compute_graph_statistics, compute_cone_statistics,
                         export_graph_stats_csv, export_cone_stats_csv)
from advanced_wl import run_advanced_experiment, export_advanced_csv
from generate_plots import generate_all_plots
from explainability import generate_all_reports

RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
CSV_DIR = os.path.join(RESULTS_DIR, "csv")
DESIGNS_DIR = os.path.join(PROJECT_ROOT, "designs")
AIG_DIR = os.path.join(PROJECT_ROOT, "aig_output")

os.makedirs(CSV_DIR, exist_ok=True)


def _write_csv(rows, filename):
    """Helper to write a list of dicts to CSV."""
    if not rows:
        return
    path = os.path.join(CSV_DIR, filename)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [+] {filename}")
    return path


# =========================================================================
# PHASE 1: SYNTHESIS
# =========================================================================
def phase_1_synthesis(yosys_bin):
    """Synthesize all Verilog designs to AIG format."""
    print("\n" + "="*60)
    print("PHASE 1: SYNTHESIS (Verilog → AIG)")
    print("="*60)

    designs = {}
    for root, dirs, files in os.walk(DESIGNS_DIR):
        for f in files:
            if f.endswith('.v'):
                name = os.path.splitext(f)[0]
                designs[name] = os.path.join(root, f)

    for name, vpath in sorted(designs.items()):
        rel = os.path.relpath(os.path.dirname(vpath), DESIGNS_DIR)
        out_dir = AIG_DIR if rel == "." else os.path.join(AIG_DIR, rel)
        out = os.path.join(out_dir, f"{name}.aig")
        if os.path.exists(out):
            print(f"  [.] {name} (cached)")
        else:
            synthesize_to_aig(yosys_bin, vpath, out)

    # Multi-optimization variants
    adder_v = os.path.join(DESIGNS_DIR, 'adder_4bit.v')
    if os.path.exists(adder_v):
        for opt in [0, 1, 2]:
            out = os.path.join(AIG_DIR, f"adder_4bit_O{opt}.aig")
            if os.path.exists(out):
                print(f"  [.] adder_4bit_O{opt} (cached)")
            else:
                synthesize_to_aig(yosys_bin, adder_v, out, opt_level=opt)


# =========================================================================
# PHASE 2: GRAPH STATISTICS
# =========================================================================
def phase_2_graph_stats(aig_results):
    """Extract and export graph-level statistics."""
    print("\n" + "="*60)
    print("PHASE 2: GRAPH STATISTICS → CSV")
    print("="*60)

    rows = compute_graph_statistics(aig_results)
    export_graph_stats_csv(rows, 'graph_statistics.csv')
    return rows


# =========================================================================
# PHASE 3: CONE STATISTICS
# =========================================================================
def phase_3_cone_stats(aig_results):
    """Extract and export cone-level statistics."""
    print("\n" + "="*60)
    print("PHASE 3: CONE STATISTICS → CSV")
    print("="*60)

    cone_rows, summary_rows = compute_cone_statistics(aig_results)
    export_cone_stats_csv(cone_rows, summary_rows)
    return cone_rows, summary_rows


# =========================================================================
# PHASE 4: BASELINE MATCHING
# =========================================================================
def phase_4_baseline_matching(aig_results):
    """Run baseline WL matching on relevant design pairs."""
    print("\n" + "="*60)
    print("PHASE 4: BASELINE MATCHING → CSV")
    print("="*60)

    pairs = [
        ('adder_4bit_O0', 'adder_4bit_O1'),
        ('adder_4bit_O0', 'adder_4bit_O2'),
        ('adder_4bit_O1', 'adder_4bit_O2'),
        ('adder_4bit', 'adder_4bit_mut1'),
        ('adder_4bit', 'adder_4bit_mut2'),
    ]

    # Precompute
    design_data = {}
    for pair in pairs:
        for name in pair:
            if name not in design_data and name in aig_results:
                G, po_nodes, parsed, stats = aig_results[name]
                cones = extract_all_cones(G, po_nodes)
                hashes = wl_hash_all_cones(cones, k=3, semantic=False)
                design_data[name] = {'cones': cones, 'hashes': hashes}

    csv_rows = []
    detail_rows = []
    for name_a, name_b in pairs:
        if name_a not in design_data or name_b not in design_data:
            continue
        result = match_designs(
            design_data[name_a]['cones'], design_data[name_a]['hashes'],
            design_data[name_b]['cones'], design_data[name_b]['hashes'],
            name_a, name_b
        )
        csv_rows.append({
            'design_a': result['design_a'],
            'design_b': result['design_b'],
            'total_cones': result['total_compared'],
            'matched': result['matched'],
            'diverged': result['diverged'],
            'match_pct': result['match_pct'],
        })
        for d in result['details']:
            detail_rows.append({
                'design_a': name_a,
                'design_b': name_b,
                'cone': d['po_name'],
                'match': d['match'],
                'size_a': d['size_a'],
                'size_b': d['size_b'],
                'hash_a': d['hash_a'],
                'hash_b': d['hash_b'],
            })

        status = f"{result['matched']}/{result['total_compared']} ({result['match_pct']}%)"
        print(f"  {name_a} vs {name_b}: {status}")

    _write_csv(csv_rows, 'baseline_matching.csv')
    _write_csv(detail_rows, 'baseline_matching_details.csv')
    return csv_rows


# =========================================================================
# PHASE 5: SCALABILITY
# =========================================================================
def phase_5_scalability(aig_results):
    """Run scalability experiment on adders of increasing width."""
    print("\n" + "="*60)
    print("PHASE 5: SCALABILITY ANALYSIS → CSV")
    print("="*60)

    targets = ['adder_4bit', 'adder_8bit', 'adder_16bit', 'adder_32bit']
    csv_rows = []

    for name in targets:
        if name not in aig_results:
            continue
        G, po_nodes, parsed, stats = aig_results[name]

        t0 = time.time()
        cones = extract_all_cones(G, po_nodes)
        t_cone = (time.time() - t0) * 1000

        t0 = time.time()
        hashes = wl_hash_all_cones(cones, k=3, semantic=False)
        t_wl = (time.time() - t0) * 1000

        bits = int(''.join(filter(str.isdigit, name)))
        row = {
            'design': name, 'bits': bits,
            'nodes': stats['nodes'], 'edges': stats['edges'],
            'and_gates': stats['and_gates'], 'depth': stats['depth'],
            'num_cones': len(cones),
            'cone_extract_ms': round(t_cone, 2),
            'wl_hash_ms': round(t_wl, 2),
            'total_ms': round(t_cone + t_wl, 2),
        }
        csv_rows.append(row)
        print(f"  {name}: {row['nodes']} nodes, {row['total_ms']}ms")

    _write_csv(csv_rows, 'scalability.csv')
    return csv_rows


# =========================================================================
# PHASE 6: WL CONVERGENCE
# =========================================================================
def phase_6_wl_convergence(aig_results):
    """Run WL depth sensitivity experiment."""
    print("\n" + "="*60)
    print("PHASE 6: WL CONVERGENCE ANALYSIS → CSV")
    print("="*60)

    target = 'adder_8bit' if 'adder_8bit' in aig_results else 'adder_4bit'
    G, po_nodes, parsed, stats = aig_results[target]
    cones = extract_all_cones(G, po_nodes)

    print(f"  Design: {target} ({stats['nodes']} nodes, {len(cones)} cones)")

    max_k = 6
    k_data = {}
    for po, cone_data in cones.items():
        sensitivity = wl_sensitivity_analysis(cone_data, max_k=max_k, semantic=False)
        cone_name = cone_data['stats']['po_name']
        k_data[cone_name] = sensitivity

    csv_rows = []
    for k_val in range(1, max_k + 1):
        hashes_at_k = set()
        total_unique = 0
        for cone_name, sens in k_data.items():
            for s in sens:
                if s['k'] == k_val:
                    hashes_at_k.add(s['hash'])
                    total_unique += s['final_unique']
        csv_rows.append({
            'k': k_val,
            'unique_cone_hashes': len(hashes_at_k),
            'avg_unique_labels': round(total_unique / len(k_data), 1),
            'total_unique_labels': total_unique,
        })
        print(f"  k={k_val}: {len(hashes_at_k)} unique hashes, avg labels={csv_rows[-1]['avg_unique_labels']}")

    _write_csv(csv_rows, 'wl_convergence.csv')
    return csv_rows, target


# =========================================================================
# PHASE 7: ADVANCED WL EXPERIMENT
# =========================================================================
def phase_7_advanced(aig_results):
    """Run advanced WL comparison experiment."""
    print("\n" + "="*60)
    print("PHASE 7: ADVANCED WL (Semantic + Polarity) → CSV")
    print("="*60)

    results, csv_rows, detail_rows = run_advanced_experiment(aig_results)
    export_advanced_csv(csv_rows, detail_rows)
    return results, csv_rows


# =========================================================================
# PHASE 8: PLOTS
# =========================================================================
def phase_8_plots():
    """Generate all thesis plots from CSVs."""
    generate_all_plots()


# =========================================================================
# PHASE 9: EXPLAINABILITY REPORTS
# =========================================================================
def phase_9_reports(aig_results):
    """Generate explainability text reports."""
    generate_all_reports(aig_results)


# =========================================================================
# MAIN
# =========================================================================
def main():
    total_start = time.time()

    print("=" * 60)
    print("  AI-AUGMENTED VERILOG NETLIST MATCHING")
    print("  Using AIG and Graph Neural Networks")
    print("  Full Thesis Pipeline Runner")
    print("=" * 60)

    # Find Yosys
    yosys_bin = find_yosys()
    if not yosys_bin:
        print("\n[!] Yosys not found. Cannot proceed.")
        print("    Ensure oss-cad-suite is extracted in the project root.")
        sys.exit(1)

    # Phase 1: Synthesis
    phase_1_synthesis(yosys_bin)

    # Load all AIGs
    print("\n  Loading all AIG files...")
    aig_results = load_all_aigs()
    if not aig_results:
        print("[!] No AIG files found.")
        sys.exit(1)
    print(f"  Loaded {len(aig_results)} designs.\n")

    # Phases 2-7: Analysis + CSV export
    phase_2_graph_stats(aig_results)
    phase_3_cone_stats(aig_results)
    phase_4_baseline_matching(aig_results)
    phase_5_scalability(aig_results)
    phase_6_wl_convergence(aig_results)
    phase_7_advanced(aig_results)

    # Phase 8: Plots
    phase_8_plots()

    # Phase 9: Reports
    phase_9_reports(aig_results)

    # Summary
    total_time = time.time() - total_start
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\n  Total time: {total_time:.1f}s")
    print(f"\n  Output directory: {RESULTS_DIR}")
    print(f"    CSV files:     {CSV_DIR}/")
    print(f"    Plots:         {os.path.join(RESULTS_DIR, 'plots')}/")
    print(f"    Reports:       {os.path.join(RESULTS_DIR, 'reports')}/")

    # List all generated files
    print(f"\n  Generated files:")
    for subdir in ['csv', 'plots', 'reports']:
        d = os.path.join(RESULTS_DIR, subdir)
        if os.path.exists(d):
            for f in sorted(os.listdir(d)):
                size = os.path.getsize(os.path.join(d, f))
                print(f"    {subdir}/{f}  ({size//1024}KB)")


if __name__ == "__main__":
    main()
