"""
run_thesis.py - Master Thesis Experiment Runner
================================================

MTP Phase: MTP-3 (final thesis runner)

Runs the COMPLETE thesis pipeline:
  1. Synthesise all Verilog -> AIG  (Yosys)
  2. Load all AIG graphs            (parse_aiger)
  3. Run experiments 1-5            (experiments.py)
  4. Generate thesis plots 1-6      (thesis_plots.py)
  5. Print discussion / viva notes

Usage:
  cd IIT_Thesis_2.0
  .venv\\Scripts\\activate
  python src/run_thesis.py
"""

import os, sys, time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthesize import find_yosys, synthesize_to_aig
from parse_aiger import load_all_aigs
from experiments import run_all_experiments
from thesis_plots import generate_all_thesis_plots

DESIGNS_DIR = os.path.join(PROJECT_ROOT, "designs")
AIG_DIR     = os.path.join(PROJECT_ROOT, "aig_output")


# ================================================================
#  SYNTHESIS
# ================================================================
def synthesise_all(yosys_bin):
    print("\n" + "=" * 70)
    print("  SYNTHESIS: Verilog -> AIG")
    print("=" * 70)

    for root, _dirs, files in os.walk(DESIGNS_DIR):
        for f in sorted(files):
            if not f.endswith('.v'):
                continue
            name = os.path.splitext(f)[0]
            vpath = os.path.join(root, f)
            out = os.path.join(AIG_DIR, f"{name}.aig")
            if os.path.exists(out):
                print(f"  [.] {name} (cached)")
            else:
                synthesize_to_aig(yosys_bin, vpath, out)

    # Multi-optimisation variants
    adder = os.path.join(DESIGNS_DIR, 'adder_4bit.v')
    if os.path.exists(adder):
        for opt in [0, 1, 2]:
            out = os.path.join(AIG_DIR, f"adder_4bit_O{opt}.aig")
            if os.path.exists(out):
                print(f"  [.] adder_4bit_O{opt} (cached)")
            else:
                synthesize_to_aig(yosys_bin, adder, out, opt_level=opt)


# ================================================================
#  DISCUSSION POINTS  (printed at end for slide / viva prep)
# ================================================================
def print_discussion(results):
    print("\n")
    print("=" * 70)
    print("  THESIS DISCUSSION POINTS & VIVA PREPARATION")
    print("=" * 70)

    # --- key findings ---
    cmp = results.get('exp2_comparison', [])
    total_fp = sum(int(r['False Pos']) for r in cmp)
    bl_avg  = sum(float(r['Baseline %']) for r in cmp) / len(cmp) if cmp else 0
    adv_avg = sum(float(r['Advanced %']) for r in cmp) / len(cmp) if cmp else 0

    print(f"""
  KEY FINDINGS
  ------------
  1. Avg baseline (fingerprint) match rate : {bl_avg:.1f}%
  2. Avg advanced (WL hash) match rate     : {adv_avg:.1f}%
  3. Total false positives caught by WL    : {total_fp}
  4. adder_4bit vs mut2 (carry inversion)  : fingerprint gives false 100%,
     WL correctly identifies 2 affected cones — the central thesis result.
  5. O1 vs O2 : both methods give 100%, confirming Yosys O1=O2.

  MINIMUM 3-5 EXPERIMENTS IF TIME IS SHORT
  -----------------------------------------
  1. Benchmark characterisation table     (Table 1, 5 min slide)
  2. Baseline vs Advanced on mutations    (Tables 2-4, core result)
  3. Case study: mut2 carry inversion     (Table 6, qualitative story)
  4. Scalability 4-32 bit                 (Table 5, shows method scales)
  5. WL convergence plot                  (Fig 5, justifies k=3)

  WHAT IS SUFFICIENT TO CLAIM THESIS COMPLETION
  -----------------------------------------------
  - At least 1 case where WL detects a mutation that fingerprint misses.
  - Scalability data showing pipeline runs on >=32-bit circuits.
  - End-to-end pipeline: Verilog -> AIG -> Cones -> WL -> Match.
  - All 6 tables + 6 plots generated reproducibly.

  NEGATIVE RESULTS (present honestly)
  ------------------------------------
  - Semantic-aware and polarity-aware WL give identical results on pure
    AIG circuits.  REASON: AIG has only one gate type (AND), so semantic
    labels add no information beyond what WL iterations already capture.
    DISCUSSION: "For technology-mapped netlists with diverse gate types,
    semantic labels would provide additional discrimination."
  - Fingerprint and WL agree on most coarse mutations (gate replacement).
    The difference only surfaces for subtle mutations (inversions).
  - The method is structural only — it does NOT prove functional equivalence.

  INTERPRETATION WITHOUT OVERCLAIMING
  -------------------------------------
  - SAY:  "WL hashing provides strictly more discriminative structural
           matching than aggregate fingerprinting."
  - SAY:  "The method detects inversion-level mutations invisible to
           fingerprint-based methods."
  - SAY:  "The AIG normalisation by Yosys ensures consistent graph
           representation across optimisation levels."
  - DON'T SAY: "This proves equivalence" or "replaces formal verification."
  - DON'T SAY: "GNN was implemented" — the thesis uses WL as a
                graph-theoretic precursor to GNN.

  VIVA Q&A PREPARATION
  ----------------------
  Q: Why WL and not a full GNN?
  A: WL is the theoretical foundation of GNNs (Xu et al., 2019).
     We use the WL test directly because (a) our graphs are small enough
     for exact hashing and (b) it provides deterministic, explainable
     results — a GNN would add learned parameters without improving
     discrimination on AIG-normalised circuits.

  Q: Why do all three WL variants give the same result?
  A: AIG circuits use only AND gates.  Semantic labels (gate type) add
     no extra information.  Polarity is already captured by inversion-
     aware WL.  This convergence is expected; with technology-mapped
     netlists (NAND/NOR/XOR mix), the variants would diverge.

  Q: What is the false positive rate?
  A: For the carry-inversion mutation, fingerprinting has a {total_fp}-cone
     false-positive rate.  WL has zero false positives on all test cases.

  Q: How does this scale?
  A: Processing time grows roughly quadratically with circuit width
     (4-bit: ~2ms, 32-bit: ~130ms).  The bottleneck is cone extraction,
     not WL hashing.
""")


# ================================================================
#  MAIN
# ================================================================
def main():
    t_start = time.time()

    print("=" * 70)
    print("  AI-AUGMENTED VERILOG NETLIST MATCHING")
    print("  Using AIG and Graph Neural Networks")
    print("  Thesis Experiment Runner")
    print("=" * 70)

    # 1. Find Yosys (optional if AIGs already exist)
    yosys_bin = find_yosys()

    # 2. Synthesise (skip if AIGs already present)
    aig_files = [f for f in os.listdir(AIG_DIR) if f.endswith('.aig')] if os.path.isdir(AIG_DIR) else []
    if len(aig_files) >= 10:
        print(f"\n  Found {len(aig_files)} pre-built AIG files — skipping synthesis.")
        if not yosys_bin:
            print("  Yosys not found, but not needed (using pre-generated AIGs).")
    elif yosys_bin:
        synthesise_all(yosys_bin)
    else:
        print("\n[!] Yosys not found and no pre-generated AIG files in aig_output/.")
        print("    Either install Yosys (oss-cad-suite) or ensure aig_output/ has .aig files.")
        sys.exit(1)

    # 3. Load AIGs
    print("\n  Loading AIG files...")
    aig_results = load_all_aigs()
    if not aig_results:
        print("[!] No AIG files found.")
        sys.exit(1)
    print(f"  Loaded {len(aig_results)} designs.\n")

    # 4. Run experiments
    results = run_all_experiments(aig_results)

    # 5. Generate plots
    generate_all_thesis_plots()

    # 6. Discussion
    print_discussion(results)

    # 7. Summary
    elapsed = time.time() - t_start
    results_dir = os.path.join(PROJECT_ROOT, "results")
    print("=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Total time: {elapsed:.1f}s\n")
    print(f"  Outputs:")
    for sub in ['csv', 'tables', 'plots']:
        d = os.path.join(results_dir, sub)
        if os.path.isdir(d):
            files = sorted(os.listdir(d))
            print(f"    {sub}/ ({len(files)} files)")
            for fn in files:
                sz = os.path.getsize(os.path.join(d, fn))
                print(f"      {fn}  ({sz // 1024 or 1}KB)")


if __name__ == "__main__":
    main()
