# MTP Progress: MTP-2 → MTP-3

## Thesis Title

**AI-Augmented Verilog Netlist Matching Using AIG and Graph Neural Networks**

M.Tech (AI), Department of Electrical Engineering, IIT Jodhpur  
Author: Abhilash Agarwal

---

## 1. Thesis Overview

This thesis investigates graph-based structural hashing as a lightweight pre-filter
for Verilog netlist equivalence checking. Verilog designs are synthesised into
And-Inverter Graphs (AIG) using Yosys, decomposed into per-output logic cones, and
compared using Weisfeiler-Leman (WL) colour refinement. The central finding is that
WL hashing at cone granularity detects subtle structural mutations — such as a single
inverted carry signal — that aggregate-statistic fingerprinting methods miss entirely,
producing false positives.

---

## 2. Project Objective

To design, implement, and evaluate a complete pipeline that:

1. Converts Verilog RTL to AIG representation via open-source synthesis (Yosys + ABC).
2. Extracts per-output logic cones from the AIG.
3. Computes structural fingerprints using two methods:
   - **Baseline:** aggregate statistics (node count, edge count, AND gates, PI count, depth).
   - **Advanced:** Weisfeiler-Leman hash with semantic-aware initial labels.
4. Matches corresponding cones between two design variants and reports equivalence/divergence.
5. Evaluates the approach across mutation detection, optimisation invariance, cross-design rejection, scalability, and hash convergence.

---

## 3. MTP-2: Scope and Completed Items

**Scope:** Build the foundational pipeline and validate it on a single benchmark.

| Item | Description | Status |
|---|---|---|
| Yosys synthesis wrapper | Verilog → AIGER conversion via subprocess | Done |
| AIGER ASCII parser | Parses header + literal definitions into NetworkX DAG with typed nodes (PI, AND, PO) | Done |
| Output cone extraction | Backward traversal (`nx.ancestors`) from each PO to collect fan-in subgraph | Done |
| WL hashing (structure-only) | 1-D WL colour refinement; node degree as initial label; fixed k iterations | Done |
| Cone matching | Hash comparison between name-matched or positionally-paired cones | Done |
| Graph statistics export | Node/edge/gate counts, depth, cone sizes → CSV | Done |
| Preliminary visualisations | 7 figures: complexity overview, scalability, WL convergence, matching bars, AIG graph, cone structure | Done |
| Pipeline runner | `run_all.py`: 9-phase sequential runner covering synthesis through plots | Done |

**Benchmark used:** single 4-bit ripple carry adder, single Yosys optimisation level, self-matching only.

**Limitations at end of MTP-2:**
- No mutation or cross-design testing.
- No baseline vs advanced comparison (only one hashing method).
- No scalability evaluation.
- No controlled experimental framework.

---

## 4. MTP-3: Scope and Completed Items

**Scope:** Expand the pipeline into a complete thesis with controlled experiments,
a proper baseline-vs-advanced comparison, and publication-ready outputs.

| Item | Description | Status |
|---|---|---|
| Multi-optimisation synthesis | O0 (minimal), O1 (standard), O2 (aggressive) variants | Done |
| Expanded benchmark suite | 8 designs: 4/8/16/32-bit adders, MUX, counter, ALU, comparator | Done |
| Mutation benchmarks | `adder_4bit_mut1` (XOR→OR gate swap), `adder_4bit_mut2` (carry inversion ~c[2]) | Done |
| Baseline method (structural fingerprint) | 5-tuple per cone: (nodes, edges, AND, PI, depth) | Done |
| Advanced method (semantic WL hash) | Gate-type-aware initial labels; k=3 WL iterations | Done |
| Polarity-aware WL extension | Inversion-pattern encoding in WL labels | Done |
| Experiment 1: Pipeline validation | End-to-end on 4-bit adder; verify parsing, cones, hashing | Done |
| Experiment 2: Re-synthesis equivalence | O0 vs O1, O1 vs O2 comparison | Done |
| Experiment 3: Mutation detection | Gate-replace and carry-inversion; false-positive analysis | Done |
| Experiment 4: Scalability | 4→8→16→32 bit adder timing | Done |
| Experiment 5: WL convergence | Hash label count vs iteration depth k=1..6 | Done |
| Case study (Table 6) | Per-cone breakdown of carry-inversion false positive | Done |
| Thesis-quality figures | 6 additional plots from experiment CSVs | Done |
| Explainability reports | Pipeline walkthrough, mutation analysis, method comparison | Done |
| Unified thesis runner | `run_thesis.py`: single command for full reproduction | Done |
| Documentation | README, MTP_PROGRESS.md, RESULTS_SUMMARY.md | Done |

---

## 5. Baseline Experiment Summary

**Method:** Structural fingerprint — each cone is represented by a 5-tuple
`(nodes, edges, AND_gates, primary_inputs, depth)`. Two cones match if all five
values are identical.

| Pair | Category | Cones | Matched | Match % |
|---|---|---|---|---|
| adder_4bit vs adder_4bit_mut1 | Mutation: gate replace | 5 | 2 | 40% |
| adder_4bit vs adder_4bit_mut2 | Mutation: carry inversion | 5 | 5 | **100% (FP)** |
| adder_4bit_O0 vs adder_4bit_O1 | Optimisation: O0 vs O1 | 5 | 1 | 20% |
| adder_4bit_O1 vs adder_4bit_O2 | Optimisation: O1 vs O2 | 5 | 5 | 100% |
| adder_4bit vs counter_4bit | Cross-design | 5 | 0 | 0% |
| adder_4bit vs alu_simple | Cross-design | 5 | 0 | 0% |

**Finding:** The baseline reports 100% match on the carry-inversion mutant because
inverting one carry wire does not change any aggregate count. This is a false positive —
the designs are functionally different but structurally indistinguishable by this method.

---

## 6. Advanced Experiment Summary

**Method:** WL hash (k=3, semantic-aware) — initial node labels encode gate type
(PI, AND, NOT, PO). After 3 rounds of neighbourhood aggregation, a canonical hash
is computed per cone. Two cones match if their hashes are identical.

| Pair | Category | Cones | Matched | Match % |
|---|---|---|---|---|
| adder_4bit vs adder_4bit_mut1 | Mutation: gate replace | 5 | 2 | 40% |
| adder_4bit vs adder_4bit_mut2 | Mutation: carry inversion | 5 | 3 | **60%** |
| adder_4bit_O0 vs adder_4bit_O1 | Optimisation: O0 vs O1 | 5 | 1 | 20% |
| adder_4bit_O1 vs adder_4bit_O2 | Optimisation: O1 vs O2 | 5 | 5 | 100% |
| adder_4bit vs counter_4bit | Cross-design | 5 | 0 | 0% |
| adder_4bit vs alu_simple | Cross-design | 5 | 0 | 0% |

**Finding:** WL hashing correctly rejects `po_3` and `po_4` in the carry-inversion case,
reporting 60% match (vs the false 100% from the baseline). The 2 rejected cones are
exactly those whose fan-in includes the inverted carry — the local neighbourhood topology
differs even though aggregate counts are identical.

**Side-by-side (carry-inversion case):**

| Cone | Nodes A | Nodes B | FP Match | WL Match | Verdict |
|---|---|---|---|---|---|
| po_0 | 10 | 10 | Match | Match | Both agree |
| po_1 | 18 | 18 | Match | Match | Both agree |
| po_2 | 26 | 26 | Match | Match | Both agree |
| po_3 | 34 | 34 | Match | **Reject** | **False positive exposed** |
| po_4 | 34 | 34 | Match | **Reject** | **False positive exposed** |

---

## 7. Key Outputs Generated

| Category | Count | Location | Format |
|---|---|---|---|
| AIGER files | 16 | `aig_output/` | `.aig` (ASCII AIGER) |
| Experiment CSVs | 18 | `results/csv/` | CSV |
| Result tables | 6 | `results/tables/` | Formatted text (grid) |
| Figures | 13 | `results/plots/` | PNG |
| Verilog designs | 10 | `designs/` | `.v` |

**Tables generated:**
1. `table1_benchmark` — Design statistics (PI, PO, AND, nodes, depth, cones)
2. `table2_baseline` — Baseline fingerprint matching results
3. `table3_advanced` — Advanced WL matching results
4. `table4_comparison` — Side-by-side baseline vs advanced with FP analysis
5. `table5_scalability` — Runtime breakdown by circuit size
6. `table6_case_study` — Per-cone carry-inversion case study

**Figures generated:**
- `fig1`–`fig7`: complexity, scalability, WL convergence, baseline matching, advanced comparison, AIG graph, cone structure
- `thesis_fig1`–`thesis_fig6`: scalability breakdown, baseline-vs-advanced bars, match distribution, benchmark overview, convergence curve, case study heatmap

---

## 8. Repository — Academic Milestone Mapping

### MTP-2 scripts (foundation layer)

| Script | Role |
|---|---|
| `src/synthesize.py` | Yosys synthesis runner (core single-opt mode) |
| `src/parse_aiger.py` | AIGER ASCII → NetworkX DAG |
| `src/cone_extract.py` | Output cone extraction via `nx.ancestors` |
| `src/wl_hash.py` | WL hashing (structure-only mode) |
| `src/match_cones.py` | Cone-level matching by hash comparison |
| `src/graph_stats.py` | Graph/cone statistics → CSV |
| `src/generate_plots.py` | Preliminary visualisations (7 figures) |
| `src/run_all.py` | Original 9-phase pipeline runner |

### MTP-3 scripts (experiment + analysis layer)

| Script | Role |
|---|---|
| `src/synthesize.py` | Extended: multi-optimisation (O0/O1/O2) |
| `src/wl_hash.py` | Extended: semantic-aware WL mode |
| `src/advanced_wl.py` | New: polarity-aware + hybrid WL scoring |
| `src/experiments.py` | New: 5-experiment suite, baseline vs advanced framework |
| `src/thesis_plots.py` | New: 6 thesis-quality figures from experiment CSVs |
| `src/explainability.py` | New: human-readable analysis reports |
| `src/run_thesis.py` | New: master thesis runner (single-command reproduction) |
| `src/run_experiments.py` | New: standalone experiment runner |

### MTP-3 design additions

| File | Purpose |
|---|---|
| `designs/adder_8bit.v` | Scalability benchmark |
| `designs/adder_16bit.v` | Scalability benchmark |
| `designs/adder_32bit.v` | Scalability benchmark |
| `designs/mux_4to1.v` | Cross-design comparison |
| `designs/counter_4bit.v` | Cross-design comparison |
| `designs/alu_simple.v` | Cross-design comparison |
| `designs/comparator_4bit.v` | Cross-design comparison |
| `designs/mutants/adder_4bit_mut1.v` | Mutation: XOR→OR gate swap |
| `designs/mutants/adder_4bit_mut2.v` | Mutation: carry inversion |

---

## 9. Current Completion Status

| Component | Status | Notes |
|---|---|---|
| Verilog design suite | Complete | 8 designs + 2 mutants |
| Synthesis pipeline | Complete | Yosys + ABC, 3 opt levels |
| AIGER parser | Complete | ASCII format, NetworkX output |
| Cone extraction | Complete | All designs processed |
| Baseline fingerprinting | Complete | 6 comparison pairs |
| Advanced WL hashing | Complete | Semantic + polarity aware |
| Experiment 1 (validation) | Complete | End-to-end verified |
| Experiment 2 (re-synthesis) | Complete | O0/O1/O2 comparisons |
| Experiment 3 (mutation) | Complete | Gate-replace + carry-inversion |
| Experiment 4 (scalability) | Complete | 4→32 bit |
| Experiment 5 (WL convergence) | Complete | k=1..6 |
| Tables and figures | Complete | 6 tables, 13 figures |
| Explainability reports | Complete | 3 report types |
| Repo documentation | Complete | README, MTP_PROGRESS, RESULTS_SUMMARY |
| Single-command reproduction | Complete | `python src/run_thesis.py` |

**Overall status: implementation and experimentation complete. Ready for thesis writing and viva.**

---

## 10. Limitations and Next Steps

### Limitations

1. **Small-scale benchmarks.** The largest design is a 32-bit adder (387 nodes, 288 AND gates). Industrial netlists have 10K–1M+ gates. Scalability beyond ~400 nodes is extrapolated, not measured.

2. **Combinational logic only.** The pipeline handles combinational circuits. Sequential designs with latches and flip-flops would require unrolling or abstraction at latch boundaries, which is not implemented.

3. **WL expressiveness bound.** The 1-WL test cannot distinguish all non-isomorphic graphs. There exist pairs of structurally different circuits that would produce identical WL hashes (WL dimension limitation). The method is a necessary-condition pre-filter, not a sufficient-condition proof.

4. **Name-based cone pairing.** Cone matching relies on output port names or positional ordering. Designs with permuted output ports would require a more sophisticated pairing strategy.

5. **Two mutation types.** Only gate replacement and carry inversion are tested. Other mutation classes (e.g., stuck-at faults, wire swaps, reconvergent paths) are not covered.

### Next Steps

1. **ISCAS/ITC benchmarks.** Evaluate on standard academic benchmarks (e.g., ISCAS-85, ITC-99) for comparability with published results.

2. **Higher-order WL or GNN embeddings.** Replace 1-WL with k-WL or a trained GNN to improve discriminative power on circuits where 1-WL hashes collide.

3. **Integration with formal verification.** Use WL-based matching as a pre-filter: matched cones are assumed equivalent, mismatched cones are forwarded to a SAT solver for exact checking. This could reduce SAT solver load significantly on large designs.

4. **Technology-mapped netlists.** Extend parsing to handle post-synthesis gate-level netlists (e.g., Liberty-mapped cells) in addition to AIG.

5. **Sequential circuit support.** Handle flip-flop boundaries by either timeframe unrolling or treating latch outputs as additional primary inputs.

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
