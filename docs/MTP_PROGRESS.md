# MTP Progress: MTP-2 → MTP-3

## Thesis Title

**AI-Augmented Verilog Netlist Matching Using AIG and Graph Neural Networks**

M.Tech (AI), Department of Electrical Engineering, IIT Jodhpur  
Author: Abhilash Agarwal

---

## MTP-2: Foundation and Proof of Concept

**Objective:** Establish whether graph-based structural hashing on AIG representations
can distinguish equivalent from non-equivalent Verilog netlists at the output-cone level.

### What was built

| Component | Description | Status |
|---|---|---|
| Yosys synthesis wrapper | Automates Verilog → AIGER conversion via Yosys + ABC | Complete |
| AIGER parser | Reads ASCII AIGER format, constructs NetworkX directed graph with typed nodes (PI, AND, PO) | Complete |
| Output cone extraction | Backward traversal from each primary output to collect its transitive fan-in subgraph | Complete |
| WL hash (structure-only) | 1-D Weisfeiler-Leman colour refinement; produces a single hash per cone | Complete |
| Cone matching | Compares WL hashes between corresponding cones of two designs | Complete |
| Graph statistics | Extracts node/edge/gate counts, depth, cone sizes → CSV | Complete |
| Preliminary plots | 7 figures: complexity overview, scalability, WL convergence, matching bars, AIG visualisation | Complete |
| Pipeline runner | `run_all.py`: 9-phase sequential runner for end-to-end demo | Complete |

### MTP-2 benchmark

- **Single design:** 4-bit ripple carry adder (`adder_4bit.v`)
- **Single optimisation level:** default Yosys synthesis
- **Validation:** self-matching (design vs itself) confirmed 100% cone match
- **Limitation:** no mutation testing, no cross-design comparison, no scalability study

### Key scripts (MTP-2 origin)

```
src/synthesize.py       — Yosys runner (single-opt mode)
src/parse_aiger.py      — AIGER parser
src/cone_extract.py     — Cone extraction
src/wl_hash.py          — WL hashing (basic)
src/match_cones.py      — Cone matching
src/graph_stats.py      — Statistics export
src/generate_plots.py   — Preliminary plots
src/run_all.py          — Original pipeline runner
```

---

## MTP-3: Full Experimental Evaluation and Thesis Completion

**Objective:** Extend the MTP-2 pipeline into a complete thesis with controlled experiments,
baseline vs advanced comparison, scalability analysis, and publication-ready outputs.

### What was added/extended

| Component | Description | Extends |
|---|---|---|
| Multi-optimisation synthesis | O0 (minimal), O1 (standard), O2 (aggressive) variants for the same design | `synthesize.py` |
| Expanded benchmark suite | 8 designs (4/8/16/32-bit adders, MUX, counter, ALU, comparator) + 2 mutants | `designs/` |
| Mutant designs | `adder_4bit_mut1` (XOR→OR gate swap), `adder_4bit_mut2` (carry inversion) | `designs/mutants/` |
| Baseline method | Structural fingerprint: (nodes, edges, AND count, PI count, depth) per cone | `experiments.py` |
| Advanced method | WL hash with semantic-aware labels (gate type encoded in initial colour) | `advanced_wl.py` |
| Experiment 1 | Pipeline validation: end-to-end on 4-bit adder, verify correct parsing and hashing | `experiments.py` |
| Experiment 2 | Re-synthesis equivalence: O0 vs O1 vs O2 on same design (tests optimisation invariance) | `experiments.py` |
| Experiment 3 | Mutation detection: original vs gate-replace, original vs carry-inversion (tests sensitivity) | `experiments.py` |
| Experiment 4 | Scalability: 4-bit → 8 → 16 → 32-bit adder, timing cone extraction + hashing | `experiments.py` |
| Experiment 5 | WL convergence: hash stability across k=1..6 iterations | `experiments.py` |
| False-positive analysis | Case study on carry-inversion (Table 6): per-cone fingerprint vs WL verdicts | `experiments.py` |
| Thesis figures | 6 publication-ready plots from experiment CSVs | `thesis_plots.py` |
| Explainability reports | Pipeline walkthrough, mutation analysis, method comparison (text format) | `explainability.py` |
| Unified thesis runner | `run_thesis.py`: single command for synthesis → experiments → plots → discussion notes | New |

### MTP-3 experiments and results

**Experiment 1 — Pipeline Validation**
- Confirmed correct end-to-end operation: 4-bit adder parsed to 51 nodes, 36 AND gates, 5 cones.

**Experiment 2 — Re-synthesis Equivalence**
- O1 vs O2: 100% match (Yosys produces identical AIG at both levels).
- O0 vs O1: 20% match (heavy structural differences from minimal vs standard optimisation).

**Experiment 3 — Mutation Detection**
- Gate replacement (mut1): both baseline and WL report 40% match. Gate count difference is visible to both methods.
- **Carry inversion (mut2):** baseline reports 100% match (false positive on 2 cones with identical node/edge/gate counts), WL reports 60% match (correctly rejects `po_3` and `po_4`). **This is the central result.**

**Experiment 4 — Scalability**
- 4-bit: 2.7 ms, 8-bit: 10.1 ms, 16-bit: 28.6 ms, 32-bit: 112.4 ms.
- Approximately linear in circuit size.

**Experiment 5 — WL Convergence**
- 9 unique hash classes across all cones.
- Hash labels stabilise at k=3 (average labels 27.2); k>3 adds labels but no new discriminative power.

### Key scripts (MTP-3 additions)

```
src/advanced_wl.py      — Semantic + polarity-aware WL hashing
src/experiments.py      — 5-experiment suite with baseline vs advanced
src/thesis_plots.py     — Thesis-quality figures
src/explainability.py   — Human-readable analysis reports
src/run_thesis.py       — Master thesis runner
src/run_experiments.py  — Standalone experiment runner
designs/mutants/        — Mutation benchmarks
designs/adder_8bit.v    — Scalability benchmarks (8/16/32-bit)
designs/mux_4to1.v      — Cross-design benchmarks
designs/alu_simple.v
designs/counter_4bit.v
designs/comparator_4bit.v
```

---

## Progression Summary

```
MTP-2                              MTP-3
─────                              ─────
1 design (4-bit adder)     →       8 designs + 2 mutants
1 optimisation level       →       3 levels (O0, O1, O2)
Structure-only WL hash     →       Semantic-aware + polarity-aware WL
Self-matching demo         →       5 controlled experiments
No baseline comparison     →       Fingerprint baseline vs WL advanced
7 preliminary plots        →       13 publication-ready figures
No tables                  →       6 formatted experiment tables
No mutation testing        →       2 mutation types with case study
No scalability study       →       4→32 bit timing analysis
run_all.py (demo)          →       run_thesis.py (reproducible)
```

---

## Final Thesis Contribution

1. **Novel application of WL hashing at cone granularity on AIGs** for netlist comparison — lightweight, interpretable, training-free.
2. **Empirical demonstration of false-positive detection** — carry-inversion mutation exposes the limitation of aggregate-statistic fingerprinting.
3. **Reproducible experimental framework** — 5 experiments, 18 CSVs, 13 plots, single-command execution.
