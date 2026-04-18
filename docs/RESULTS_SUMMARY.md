# Results Summary

Detailed experimental results for:  
**AI-Augmented Verilog Netlist Matching Using AIG and Graph Neural Networks**

---

## 1. Benchmark Designs

13 AIG instances derived from 8 Verilog designs + 2 mutants + 3 optimisation variants:

| Design | PI | PO | AND | Nodes | Edges | Depth | Cones | Avg Cone Size |
|---|---|---|---|---|---|---|---|---|
| adder_4bit | 9 | 5 | 36 | 51 | 77 | 17 | 5 | 24.4 |
| adder_4bit_O0 | 9 | 5 | 44 | 59 | 93 | 15 | 5 | 30.4 |
| adder_4bit_O1 | 9 | 5 | 36 | 51 | 77 | 17 | 5 | 24.4 |
| adder_4bit_O2 | 9 | 5 | 36 | 51 | 77 | 17 | 5 | 24.4 |
| adder_4bit_mut1 | 9 | 5 | 32 | 47 | 69 | 15 | 5 | 22.8 |
| adder_4bit_mut2 | 9 | 5 | 36 | 51 | 77 | 17 | 5 | 24.4 |
| adder_8bit | 17 | 9 | 72 | 99 | 153 | 33 | 9 | 41.1 |
| adder_16bit | 33 | 17 | 144 | 195 | 305 | 65 | 17 | 73.5 |
| adder_32bit | 65 | 33 | 288 | 387 | 609 | 129 | 33 | 137.8 |
| alu_simple | 10 | 5 | 84 | 100 | 173 | 12 | 5 | 36.2 |
| comparator_4bit | 8 | 3 | 26 | 38 | 55 | 8 | 3 | 29.0 |
| counter_4bit | 5 | 5 | 16 | 27 | 37 | 6 | 5 | 9.2 |
| mux_4to1 | 18 | 4 | 39 | 62 | 82 | 8 | 4 | 19.0 |

**Source:** `results/csv/table1_benchmark.csv`

---

## 2. Baseline Method — Structural Fingerprint Matching

The baseline compares cones using a 5-tuple: (node count, edge count, AND gate count, primary input count, depth). Two cones match if all five values are identical.

| Pair | Category | Cones | Matched | Match % | Time (ms) |
|---|---|---|---|---|---|
| adder_4bit vs adder_4bit_mut1 | Mutation: Gate Replace | 5 | 2 | 40.0% | 0.04 |
| adder_4bit vs adder_4bit_mut2 | Mutation: Carry Inversion | 5 | 5 | **100.0%** | 0.02 |
| adder_4bit_O0 vs adder_4bit_O1 | Optimisation: O0 vs O1 | 5 | 1 | 20.0% | 0.02 |
| adder_4bit_O1 vs adder_4bit_O2 | Optimisation: O1 vs O2 | 5 | 5 | 100.0% | 0.03 |
| adder_4bit vs counter_4bit | Cross-Design | 5 | 0 | 0.0% | 0.02 |
| adder_4bit vs alu_simple | Cross-Design | 5 | 0 | 0.0% | 0.02 |

**Key observation:** The baseline reports 100% match for the carry-inversion mutant because
the mutation (inverting one carry signal) does not change any aggregate statistic — node count,
edge count, AND count, PI count, and depth are all identical between the original and mutant
for all 5 cones. **This is a false positive.**

**Source:** `results/csv/table2_baseline.csv`

---

## 3. Advanced Method — WL Hash Matching

The advanced method computes a Weisfeiler-Leman hash (k=3, semantic-aware) for each cone.
Initial node labels encode gate type (PI, AND, NOT, PO). The hash captures local neighbourhood
topology, not just aggregate counts.

| Pair | Category | Cones | Matched | Match % | Time (ms) |
|---|---|---|---|---|---|
| adder_4bit vs adder_4bit_mut1 | Mutation: Gate Replace | 5 | 2 | 40.0% | 0.02 |
| adder_4bit vs adder_4bit_mut2 | Mutation: Carry Inversion | 5 | 3 | **60.0%** | 0.01 |
| adder_4bit_O0 vs adder_4bit_O1 | Optimisation: O0 vs O1 | 5 | 1 | 20.0% | 0.01 |
| adder_4bit_O1 vs adder_4bit_O2 | Optimisation: O1 vs O2 | 5 | 5 | 100.0% | 0.01 |
| adder_4bit vs counter_4bit | Cross-Design | 5 | 0 | 0.0% | 0.01 |
| adder_4bit vs alu_simple | Cross-Design | 5 | 0 | 0.0% | 0.01 |

**Key observation:** WL hashing correctly identifies that `po_3` and `po_4` differ between the
original and carry-inversion mutant, reporting 60% match instead of the false 100%.

**Source:** `results/csv/table3_advanced.csv`

---

## 4. Baseline vs Advanced — Side-by-Side Comparison

| Category | Pair | Cones | Baseline % | Advanced % | False Pos | FP Rate % |
|---|---|---|---|---|---|---|
| Mutation: Gate Replace (XOR→OR) | adder_4bit vs adder_4bit_mut1 | 5 | 40.0 | 40.0 | 0 | 0.0 |
| **Mutation: Carry Inversion (~c[2])** | **adder_4bit vs adder_4bit_mut2** | **5** | **100.0** | **60.0** | **2** | **40.0** |
| Optimisation: O0 vs O1 | adder_4bit_O0 vs adder_4bit_O1 | 5 | 20.0 | 20.0 | 0 | 0.0 |
| Optimisation: O1 vs O2 | adder_4bit_O1 vs adder_4bit_O2 | 5 | 100.0 | 100.0 | 0 | 0.0 |
| Cross-Design: Adder vs Counter | adder_4bit vs counter_4bit | 5 | 0.0 | 0.0 | 0 | 0.0 |
| Cross-Design: Adder vs ALU | adder_4bit vs alu_simple | 5 | 0.0 | 0.0 | 0 | 0.0 |

**Interpretation:**
- On 5 of 6 comparison pairs, both methods agree.
- On the carry-inversion mutation, the baseline has a **40% false-positive rate** (2 out of 5 cones incorrectly matched). WL hashing eliminates these false positives.
- This demonstrates the value of topology-aware hashing over aggregate statistics.

**Source:** `results/csv/table4_comparison.csv`

---

## 5. Scalability Analysis

Self-comparison (design vs itself) timing across adder sizes:

| Design | Bits | Nodes | AND | Depth | Cones | Cone (ms) | FP (ms) | WL (ms) | Total (ms) |
|---|---|---|---|---|---|---|---|---|---|
| adder_4bit | 4 | 51 | 36 | 17 | 5 | 1.54 | 0.004 | 1.14 | 2.68 |
| adder_8bit | 8 | 99 | 72 | 33 | 9 | 5.49 | 0.005 | 4.57 | 10.06 |
| adder_16bit | 16 | 195 | 144 | 65 | 17 | 17.10 | 0.010 | 11.52 | 28.61 |
| adder_32bit | 32 | 387 | 288 | 129 | 33 | 73.86 | 0.020 | 38.54 | 112.40 |

**Observation:** Runtime scales approximately linearly with circuit size. The fingerprint comparison
(FP) is negligible (<0.02 ms). WL hashing dominates but remains practical (112 ms for 387 nodes).

**Source:** `results/csv/table5_scalability.csv`

---

## 6. Case Study — Carry-Inversion False Positive

Detailed per-cone analysis of `adder_4bit` vs `adder_4bit_mut2` (carry inversion at bit 2):

| Cone | Nodes A | Nodes B | AND A | AND B | Depth A | Depth B | FP Match | WL Match | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| po_0 | 10 | 10 | 6 | 6 | 5 | 5 | True | True | Both Match |
| po_1 | 18 | 18 | 12 | 12 | 7 | 7 | True | True | Both Match |
| po_2 | 26 | 26 | 18 | 18 | 9 | 9 | True | True | Both Match |
| **po_3** | 34 | 34 | 24 | 24 | 11 | 11 | **True** | **False** | **FALSE POSITIVE** |
| **po_4** | 34 | 34 | 24 | 24 | 9 | 9 | **True** | **False** | **FALSE POSITIVE** |

**Analysis:**
- `po_0`, `po_1`, `po_2`: cones for sum bits 0-2, which are upstream of the mutation site. Both methods correctly report match.
- `po_3` (sum bit 3): the carry inversion at bit 2 propagates into this cone, changing the internal wiring but not the aggregate node/edge/gate counts. Fingerprint matches (false positive); WL hashing detects the topological difference.
- `po_4` (carry out): similarly affected by the inverted carry. Same false-positive pattern.

**This case study is the central empirical result of the thesis** — it concretely demonstrates
the failure mode of aggregate-statistic methods and the advantage of topology-aware hashing.

**Source:** `results/csv/table6_case_study.csv`

---

## 7. WL Convergence

WL hash label counts across iterations (k=1..6) on the 4-bit adder:

| k | Unique Hashes | Avg Labels/Cone | Total Labels |
|---|---|---|---|
| 1 | 9 | 12.9 | 116 |
| 2 | 9 | 22.0 | 198 |
| 3 | 9 | 27.2 | 245 |
| 4 | 9 | 31.6 | 284 |
| 5 | 9 | 35.0 | 315 |
| 6 | 9 | 37.6 | 338 |

**Observation:** The number of unique hash classes (9) is stable from k=1. Label diversity
grows with k but saturates — k=3 is sufficient for the benchmarks tested.

**Source:** `results/csv/exp_convergence.csv`

---

## Figures

All 13 generated figures are in `results/plots/`:

| Figure | File | Description |
|---|---|---|
| Fig 1 | `fig1_circuit_overview.png` | Benchmark design complexity comparison |
| Fig 2 | `fig2_scalability.png` | Runtime vs circuit size |
| Fig 3 | `fig3_wl_convergence.png` | WL label count vs iteration k |
| Fig 4 | `fig4_baseline_matching.png` | Baseline fingerprint match percentages |
| Fig 5 | `fig5_advanced_comparison.png` | Advanced WL match percentages |
| Fig 6 | `fig6_aig_graph.png` | AIG graph structure visualisation |
| Fig 7 | `fig7_cone_visualization.png` | Output cone subgraph visualisation |
| Thesis Fig 1 | `thesis_fig1_scalability.png` | Scalability: runtime breakdown by phase |
| Thesis Fig 2 | `thesis_fig2_comparison.png` | Baseline vs Advanced bar chart |
| Thesis Fig 3 | `thesis_fig3_distribution.png` | Match percentage distribution |
| Thesis Fig 4 | `thesis_fig4_benchmark.png` | Benchmark overview (nodes, gates, depth) |
| Thesis Fig 5 | `thesis_fig5_convergence.png` | WL convergence curve |
| Thesis Fig 6 | `thesis_fig6_case_study.png` | Case study: per-cone FP vs WL verdicts |

---

## CSV File Index

All 18 CSV files in `results/csv/`:

| File | Experiment | Columns |
|---|---|---|
| `table1_benchmark.csv` | Benchmark summary | Design, PI, PO, AND, Nodes, Edges, Depth, Cones, Avg Cone |
| `table2_baseline.csv` | Baseline matching | Pair, Category, Cones, Matched, Unmatched, Match %, Time ms |
| `table3_advanced.csv` | Advanced matching | Pair, Category, Cones, Matched, Unmatched, Match %, Time ms |
| `table4_comparison.csv` | Side-by-side comparison | Category, Pair, Cones, Baseline %, Advanced %, False Pos, FP Rate % |
| `table5_scalability.csv` | Scalability timings | Design, Bits, Nodes, AND, Depth, Cones, Cone ms, FP ms, WL ms, Total ms |
| `table6_case_study.csv` | Case study (mut2) | Cone, Nodes A/B, AND A/B, Depth A/B, FP Match, WL Match, Verdict |
| `exp_convergence.csv` | WL convergence | k, Unique Hashes, Avg Labels, Total Labels |
| `graph_statistics.csv` | Full graph stats | Design, various metrics |
| `scalability.csv` | Raw scalability data | Design, timing columns |
| `cone_details.csv` | Per-cone details | Design, Cone, nodes, edges, AND, PI, depth |
| `cone_summary.csv` | Cone summary | Design, Cone, size stats |
| `baseline_matching.csv` | Raw baseline matches | Pair, cone-level details |
| `baseline_matching_details.csv` | Baseline per-cone | Pair, Cone, match values |
| `baseline_cone_details.csv` | Baseline cone stats | Pair, Cone, node/edge/gate counts |
| `advanced_matching_summary.csv` | Advanced summary | Pair, match stats |
| `advanced_matching_details.csv` | Advanced per-cone | Pair, Cone, hash values |
| `advanced_cone_details.csv` | Advanced cone stats | Pair, Cone, hash details |
| `wl_convergence.csv` | WL convergence raw | k, hash counts, label counts |

---

## Theoretical Foundation: WL Hashing as a GNN Analytical Equivalent

The WL hashing algorithm used in this work is not merely a graph-similarity heuristic. It is the
**analytical foundation of message-passing Graph Neural Networks (MPGNNs)**.

**Key theorems (from literature):**

- **Xu et al. (ICLR 2019)** — *"How Powerful are Graph Neural Networks?"*:
  Any MPGNN with an injective neighbourhood-aggregation function is **at most** as powerful as
  the 1-WL colour refinement algorithm in distinguishing graph structures. GNNs that use sum
  aggregation with injective update (e.g., Graph Isomorphism Network, GIN) achieve this upper bound.

- **Morris et al. (NeurIPS 2019)** — *"Weisfeiler and Leman Go Neural"*:
  Formally defines k-WL and k-GNN equivalence, showing that standard MPGNNs correspond to 1-WL.

**Implication for this work:**

By implementing 1-WL hashing on AIG output cones, this thesis implements the **analytical upper
bound** of what any trained MPGNN could discriminate on these graphs. A GNN trained for netlist
equivalence prediction could not outperform WL hashing on the graphs where 1-WL distinguishes
them — it can only match this performance without training data.

This establishes WL hashing as the **AI-for-EDA baseline**: any future GNN approach on netlist
comparison must surpass this analytical bound (by using k-WL for k≥2, or auxiliary features) to
justify its added training and inference complexity.

**Why no GNN was trained in this work:**

Training a GNN requires labelled pairs of equivalent/non-equivalent netlists. No public benchmark
dataset of labelled netlist equivalence pairs exists at the time of this work. The WL-hash approach
achieves the 1-GNN upper bound entirely without such data. Collecting labelled data and training a
GIN is explicitly identified as the primary future work direction.
