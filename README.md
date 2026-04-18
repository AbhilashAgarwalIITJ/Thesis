# AI-Augmented Verilog Netlist Matching Using AIG and Graph Neural Networks

**M.Tech Thesis** — Department of Electrical Engineering, IIT Jodhpur  
**Author:** Abhilash Agarwal  
**Semesters:** MTP-2 (Foundation) → MTP-3 (Completion)  
**Repository:** [github.com/AbhilashAgarwalIITJ/Thesis](https://github.com/AbhilashAgarwalIITJ/Thesis)

---

## Quick Academic Review

> For panel members and evaluators: this section summarises the entire thesis in under 60 seconds.

**Problem:** Formal equivalence checking gives whole-circuit YES/NO verdicts but does not localise which output cones diverged. Aggregate structural metrics (gate counts, depth) miss subtle topology changes like signal inversions.

**Solution:** An end-to-end pipeline — Verilog → AIG → Graph → Output Cones → Structural Matching — using Weisfeiler-Leman (WL) graph hashing with semantic node labels and inversion-aware edge encoding.

**Central result:** On a carry-inversion mutation where all aggregate metrics are identical, structural fingerprinting reports 100% match (false positive). WL hashing correctly identifies 2 of 5 cones as structurally different (60% match), eliminating the 40% false-positive rate.

**Scope:** 13 benchmarks, 6 comparison pairs, 5 controlled experiments. Sub-second processing up to 32-bit circuits. No GNN training required — WL provides the theoretical discrimination upper bound for message-passing GNNs (Xu et al., 2019).

| | MTP-2 | MTP-3 |
|---|---|---|
| Benchmarks | 1 design | 10 designs (8 + 2 mutants) |
| Experiments | Proof-of-concept | 5 controlled experiments |
| Key addition | Pipeline validation | Baseline vs advanced comparison, false-positive detection |

**Run it:** `python src/run_thesis.py` — full pipeline in <30 seconds.  
**Demo:** Open `demo.ipynb` — reproduces the central result in 6 cells (<2 seconds).

---

## Thesis Summary

This thesis presents an end-to-end pipeline for structural matching of Verilog netlists at the output-cone level. Designs are synthesised to And-Inverter Graph (AIG) format using Yosys, parsed into directed graphs, and decomposed into per-output cones. A baseline structural fingerprint — a 5-tuple of node count, edge count, AND gates, primary inputs, and depth — is compared against a Weisfeiler-Leman (WL) graph hash with semantic node labels and inversion-aware edge encoding (k=3). Experiments on 13 benchmarks and 6 comparison pairs show that both methods agree on 5 of 6 pairs. The critical divergence occurs on a carry-inversion mutation: fingerprinting reports 100% match while WL correctly identifies 2 of 5 cones as structurally different, exposing a 40% false-positive rate in the baseline. The pipeline processes circuits up to 32-bit width in under 120 milliseconds. The WL test is the proven theoretical upper bound on message-passing GNN discrimination (Xu et al., 2019); this work establishes the deterministic, interpretable foundation for future GNN-based netlist comparison.

**One-line contribution:** WL graph hashing applied at the output-cone level detects inversion-level structural changes in AIG netlists that aggregate-metric fingerprinting misses.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Literature Gap](#literature-gap)
- [Thesis Objective](#thesis-objective)
- [Proposed Pipeline](#proposed-pipeline)
- [Academic Milestone Mapping](#academic-milestone-mapping)
- [Key Results](#key-results)
- [Thesis Contributions](#thesis-contributions)
- [Demo / Visualisation](#demo--visualisation)
- [Repository Structure](#repository-structure)
- [How to Reproduce](#how-to-reproduce)
- [Limitations](#limitations)
- [Future Work](#future-work)
- [Further Documentation](#further-documentation)
- [Author](#author)

---

## Problem Statement

Modern VLSI design flows require verifying that two versions of a circuit — before and after synthesis optimisation, technology mapping, or manual editing — remain structurally consistent. Traditional approaches rely on formal equivalence checking (SAT/BDD), which provides binary whole-circuit verdicts but does not localise which outputs diverged. Aggregate structural metrics (gate counts, depth) can miss subtle topology changes such as inverted carry signals.

**Research question:** Can graph-theoretic hashing at the output-cone level detect structural divergences that aggregate-metric fingerprinting misses?

**Formal statement:**  
Given two Verilog designs synthesised to AIG, determine for each primary output cone whether the two versions are structurally identical or divergent, using a method that captures neighbourhood topology beyond aggregate metrics.

## Literature Gap

| Existing Approach | What It Provides | Gap for This Problem |
|---|---|---|
| SAT/BDD formal equivalence | Whole-circuit correctness proof | No per-cone localisation |
| Structural fingerprinting | Fast aggregate comparison | Misses inversion-level changes |
| Graph isomorphism (VF2) | Exact subgraph matching | NP-hard; overkill for pre-filtering |
| GNN-based similarity | Learned circuit embeddings | Requires training data; not interpretable |
| WL graph kernels | Structural signatures | Not applied to AIG output cones |

**Gap addressed:** No existing work applies WL hashing at the output-cone granularity on AIG representations. This thesis fills that gap with a lightweight, interpretable, training-free structural matching pipeline.

## Thesis Objective

1. Build an end-to-end pipeline: Verilog → AIG → Graph → Cones → Match
2. Implement a baseline method (structural fingerprint) and an advanced method (WL hash)
3. Compare both on mutation, optimisation, and cross-design pairs
4. Demonstrate a concrete case where WL catches false positives that fingerprinting misses
5. Analyse scalability (4-bit to 32-bit) and WL convergence (k=1 to 6)

## Proposed Pipeline

```
Verilog (.v)
    │
    ▼  Yosys (synth -flatten; aigmap; write_aiger)
AIG (.aag) — ASCII AIGER format
    │
    ▼  parse_aiger.py → NetworkX DiGraph
Graph — Nodes: PI, AND, PO  |  Edges: with inversion attribute
    │
    ▼  cone_extract.py — backward BFS from each PO
Per-output logic cones
    │
    ├──▶ Structural fingerprint: sig = (nodes, edges, AND, PI, depth)
    │    Match = exact tuple equality  |  Cost: O(1)
    │
    └──▶ WL hash (k=3, semantic + inversion-aware)
         Match = exact hash equality   |  Cost: O(k × |E|)
            │
            ▼  experiments.py / match_cones.py
    Per-cone MATCH / MISMATCH verdicts + statistics
            │
            ▼  thesis_plots.py
    Tables, figures, CSV data
```

## Academic Milestone Mapping

### MTP-2 → MTP-3 Progression

| Aspect | MTP-2 (Foundation) | MTP-3 (Completion) |
|---|---|---|
| Designs | 1 (4-bit adder) | 8 designs + 2 mutants |
| Synthesis | Single optimisation level | 3 levels (O0, O1, O2) |
| Hashing method | Structure-only WL | Semantic + inversion-aware WL |
| Comparison approach | Self-matching validation | Fingerprint baseline vs WL advanced |
| Experiments | Proof-of-concept | 5 controlled experiments |
| Mutation testing | None | Gate replacement + carry inversion |
| Scalability study | Not measured | 4-bit to 32-bit timing analysis |
| Outputs | 7 preliminary plots | 13 figures, 6 tables, 18 CSVs |
| Pipeline runner | `run_all.py` (demo) | `run_thesis.py` (reproducible) |
| Documentation | Minimal | README, progress docs, result analysis |

### MTP-2 Deliverables

| Deliverable | Scripts | Output |
|---|---|---|
| Verilog → AIG synthesis (single opt level) | `synthesize.py` | `aig_output/*.aig` |
| AIGER parser → NetworkX directed graph | `parse_aiger.py` | In-memory DAGs |
| Output cone extraction via backward BFS | `cone_extract.py` | Per-output subgraphs |
| Structure-only WL hashing | `wl_hash.py` | Hash per cone |
| Initial cone matching on 4-bit adder | `match_cones.py` | Match/mismatch list |
| Graph statistics and 7 preliminary plots | `graph_stats.py`, `generate_plots.py` | CSV + PNG |
| 9-phase pipeline runner | `run_all.py` | End-to-end demo |

### MTP-3 Deliverables

| Deliverable | Scripts | Output |
|---|---|---|
| Multi-optimisation synthesis (O0 / O1 / O2) | `synthesize.py` (extended) | 3 AIG variants per design |
| Expanded benchmark suite (8 designs + 2 mutants) | `designs/` | 10 Verilog files |
| Baseline vs advanced experiment framework | `experiments.py` | 6 pairs × 2 methods |
| Semantic + inversion-aware WL hashing | `advanced_wl.py` | Improved cone hashes |
| Scalability analysis (4-bit → 32-bit) | `experiments.py` | Timing data |
| WL convergence study (k=1..6) | `experiments.py` | Convergence curve |
| False-positive case study (carry inversion) | `experiments.py` | Per-cone breakdown |
| 6 thesis-quality figures + 6 formatted tables | `thesis_plots.py` | `results/plots/`, `results/tables/` |
| Explainability reports | `explainability.py` | Text reports |
| Unified thesis runner | `run_thesis.py` | Single-command execution |

For detailed per-script MTP phase mapping, see [docs/MTP_PROGRESS.md](docs/MTP_PROGRESS.md).

## Key Results

### Experiment Summary

| Comparison Pair | Baseline (Fingerprint) | Advanced (WL Hash) | Observation |
|---|---|---|---|
| Gate replacement (XOR→OR) | 40% match | 40% match | Both detect; gate count changes |
| **Carry inversion (~c[2])** | **100% match (FP)** | **60% match** | **WL catches what fingerprint misses** |
| O1 vs O2 optimisation | 100% match | 100% match | Identical AIG (Yosys deterministic) |
| O0 vs O1 optimisation | 20% match | 20% match | Heavy restructuring; expected |
| Cross-design (adder vs counter) | 0% match | 0% match | Correctly rejected |
| Cross-design (adder vs ALU) | 0% match | 0% match | Correctly rejected |

### Central Result — Carry-Inversion Case Study

| Cone | Nodes (A) | Nodes (B) | Fingerprint | WL Hash | Verdict |
|------|-----------|-----------|-------------|---------|---------|
| po_0 | 10 | 10 | Match | Match | Both agree |
| po_1 | 18 | 18 | Match | Match | Both agree |
| po_2 | 26 | 26 | Match | Match | Both agree |
| po_3 | 34 | 34 | Match | **Mismatch** | **False positive** |
| po_4 | 34 | 34 | Match | **Mismatch** | **False positive** |

po_3 and po_4 depend on the inverted carry bit. All aggregate metrics are identical (34 nodes, 24 AND gates, same depth). Fingerprinting cannot distinguish them. WL hashing encodes the inversion pattern into neighbourhood signatures and correctly rejects both cones.

### Additional Results

- **Scalability:** 4-bit 2.7 ms → 32-bit 112 ms (all sub-second)
- **WL convergence:** Stabilises at k=3; tested on adder_8bit (9 cones, k=1..6)
- **Negative result:** Semantic-aware and polarity-aware WL variants gave identical results on AIG — expected because AIG has only AND gates. This confirms AIG normalisation limits label diversity; on technology-mapped netlists these variants would diverge.

See [docs/RESULTS_SUMMARY.md](docs/RESULTS_SUMMARY.md) for detailed analysis.

## Thesis Contributions

1. **End-to-end pipeline** from Verilog to per-cone structural match/mismatch results (13 benchmarks, single-command reproducibility).

2. **False-positive detection** — structural fingerprinting reports 100% match on a carry-inversion mutation where WL hashing correctly identifies 2 of 5 cones as different (40% FP rate eliminated).

3. **Empirical characterisation** — 5 controlled experiments across mutation detection, re-synthesis equivalence, cross-design rejection, scalability (2.7 ms → 112 ms), and WL convergence (k=3).

## Demo / Visualisation

### Interactive Notebook

The fastest way to see the pipeline in action is **`demo.ipynb`** — a Jupyter notebook that walks through the carry-inversion case study in 6 cells:

| Cell | What it shows |
|------|---------------|
| 1 | Load AIG, print graph statistics |
| 2 | Extract output cones, print per-cone metrics |
| 3 | Compute WL hashes (k=3, semantic + inversion-aware) |
| 4 | Load carry-inversion mutant (`adder_4bit_mut2`) |
| 5 | **Central result:** Fingerprint vs WL — shows 2 false positives caught |
| 6 | Cone graph visualisation (colour-coded by node type) |

```bash
jupyter notebook demo.ipynb
# or open in VS Code and run cells sequentially
```

**Key output (cell 5):**
```
Cone      Nodes A  Nodes B  FP Match  WL Match  Verdict
--------------------------------------------------------------
po_0           10       10     Yes       Yes     Both agree
po_1           18       18     Yes       Yes     Both agree
po_2           26       26     Yes       Yes     Both agree
po_3           34       34     Yes        No     <-- FALSE POSITIVE
po_4           34       34     Yes        No     <-- FALSE POSITIVE

Fingerprint match: 5/5 (100%)
WL hash match:     3/5 (60%)
False positives caught by WL: 2
```

### Command-Line Pipeline

```bash
python src/run_thesis.py    # full pipeline: synthesis → experiments → plots (<30 sec)
python src/run_all.py       # MTP-2 pipeline with 7 preliminary plots
```

### Generated Outputs

| Category | Count | Location |
|---|---|---|
| Publication figures | 13 PNG | `results/plots/` |
| Experiment CSVs | 18 | `results/csv/` |
| Formatted tables | 6 | `results/tables/` |
| AIGER files | 16 | `aig_output/` |

## Repository Structure

```
├── demo.ipynb                # Interactive demo (6 cells, <2 sec)
├── designs/                  # Verilog benchmarks
│   ├── adder_4bit.v          #   Core benchmark (MTP-2)
│   ├── adder_8bit.v          #   Scalability (MTP-3)
│   ├── adder_16bit.v         #   Scalability (MTP-3)
│   ├── adder_32bit.v         #   Scalability (MTP-3)
│   ├── mux_4to1.v            #   Cross-design (MTP-3)
│   ├── counter_4bit.v        #   Cross-design (MTP-3)
│   ├── alu_simple.v          #   Cross-design (MTP-3)
│   ├── comparator_4bit.v     #   Cross-design (MTP-3)
│   └── mutants/
│       ├── adder_4bit_mut1.v #   Gate replacement: XOR→OR (MTP-3)
│       └── adder_4bit_mut2.v #   Carry inversion: ~c[2] (MTP-3)
├── src/
│   ├── synthesize.py         #   Verilog → AIG (MTP-2 core + MTP-3 multi-opt)
│   ├── parse_aiger.py        #   AIGER parser (MTP-2)
│   ├── cone_extract.py       #   Cone extraction (MTP-2)
│   ├── wl_hash.py            #   WL hashing (MTP-2 + MTP-3 semantic mode)
│   ├── match_cones.py        #   Cone matching (MTP-2)
│   ├── advanced_wl.py        #   Semantic + inversion-aware WL (MTP-3)
│   ├── experiments.py        #   5-experiment suite (MTP-3)
│   ├── thesis_plots.py       #   Thesis figures (MTP-3)
│   ├── generate_plots.py     #   Preliminary plots (MTP-2)
│   ├── graph_stats.py        #   Graph statistics (MTP-2)
│   ├── explainability.py     #   Text reports (MTP-3)
│   ├── run_thesis.py         #   Master runner (MTP-3) ★
│   ├── run_all.py            #   Original runner (MTP-2)
│   └── run_experiments.py    #   Standalone experiments (MTP-3)
├── aig_output/               # Pre-generated AIGER files (16 files)
├── results/
│   ├── csv/                  # 18 experiment CSVs
│   ├── plots/                # 13 figures
│   └── tables/               # 6 formatted tables
├── docs/
│   ├── MTP_PROGRESS.md       # MTP-2 → MTP-3 progression
│   └── RESULTS_SUMMARY.md    # Detailed result analysis
├── requirements.txt          # networkx, matplotlib, numpy, pandas, tabulate
└── .gitignore
```

## How to Reproduce

### Quick Start (3 commands)

```bash
git clone https://github.com/AbhilashAgarwalIITJ/Thesis.git
cd Thesis
pip install -r requirements.txt    # or use a venv first
python src/run_thesis.py           # full pipeline, <30 sec
```

Pre-generated AIGs are included — no Yosys installation required for running experiments.

### Full Setup (with Yosys for re-synthesis)

<details>
<summary>Click to expand step-by-step setup guide</summary>

#### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Git | Any recent | Clone the repository |
| Python | 3.10+ | Run the pipeline |
| Yosys (oss-cad-suite) | 0.40+ | Synthesise Verilog → AIGER (optional) |

#### 1. Install Python

**Windows:** Download from [python.org](https://www.python.org/downloads/) — check "Add to PATH". Or: `winget install --id Python.Python.3.12 -e`  
**Linux:** `sudo apt install -y python3 python3-pip python3-venv`  
**macOS:** `brew install python@3.12`

#### 2. Clone and Set Up

```bash
git clone https://github.com/AbhilashAgarwalIITJ/Thesis.git
cd Thesis
python -m venv .venv

# Activate:
.\.venv\Scripts\Activate.ps1             # Windows PowerShell
source .venv/bin/activate                # Linux / macOS

pip install -r requirements.txt
```

> Windows execution policy error? Run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

#### 3. Install Yosys (optional — only for re-synthesis)

**Windows:**
1. Download `oss-cad-suite-windows-x64-YYYYMMDD.exe` from [oss-cad-suite releases](https://github.com/YosysHQ/oss-cad-suite-build/releases)
2. Extract into the project folder (creates `Thesis/oss-cad-suite/`)
3. The pipeline auto-detects `oss-cad-suite/` in the project root

**Linux:** `sudo apt install -y yosys` or download oss-cad-suite tarball  
**macOS:** `brew install yosys`

Verify: `yosys -V`

> **Windows note:** Yosys needs both `bin/` and `lib/` on PATH for DLL loading. The `synthesize.py` script handles this automatically when oss-cad-suite is in the project root.

#### 4. Run

```bash
python src/run_thesis.py     # full pipeline (<30 sec)
```

To force re-synthesis: delete `aig_output/` before running.

#### 5. Check Results

| Directory | Files | Contents |
|---|---|---|
| `results/csv/` | 18 CSVs | Benchmark stats, matching details, timing, convergence |
| `results/plots/` | 13 PNGs | Bar charts, line plots, heatmaps, graph visualisations |
| `results/tables/` | 6 TXTs | Formatted tables for each experiment |

</details>

### Alternative Run Modes

```bash
python src/run_experiments.py    # experiments only (skip synthesis)
python src/run_all.py            # MTP-2 original 9-phase pipeline
```

### Troubleshooting

| Problem | Solution |
|---|---|
| `python` not found (Windows) | Try `py` or `python3`. Reinstall with "Add to PATH". |
| `yosys` not found | Ensure oss-cad-suite is extracted in project root. Pipeline auto-detects it. |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |
| DLL load errors (Windows) | Both `oss-cad-suite\bin\` AND `lib\` must be accessible. |

## Limitations

- **Scale:** Benchmarks are small-scale combinational circuits (up to 32-bit adder, 387 nodes). Industrial-scale behaviour (10K+ gates) is untested.
- **Structural only:** WL hashing detects structural divergence, not functional inequivalence. Two structurally different cones may implement the same function.
- **AIG gate diversity:** AIG has only AND gates, limiting label diversity. Semantic WL variants converge to the same result on AIG (confirmed experimentally).
- **Combinational only:** Sequential circuits (latches/flip-flops) are not handled.
- **Cone pairing:** Name-based or positional; does not handle arbitrary output permutations.

## Future Work

1. **GNN implementation** — Train a Graph Isomorphism Network (GIN) on cone pairs to learn similarity beyond exact structural matching. WL establishes the discrimination baseline that GIN should at least match.
2. **Technology-mapped netlists** — Apply to post-synthesis gate libraries (NAND, NOR, XOR, MUX) where gate-type diversity would enable richer semantic labels.
3. **Hybrid verification** — Use WL matching as a pre-filter; run SAT only on cones flagged as structurally different.
4. **Standard benchmarks** — Evaluate on ISCAS-85, ITC-99, and OpenCores for broader validation.

## Further Documentation

- [docs/MTP_PROGRESS.md](docs/MTP_PROGRESS.md) — Detailed MTP-2 → MTP-3 progression (10 sections)
- [docs/RESULTS_SUMMARY.md](docs/RESULTS_SUMMARY.md) — Complete experiment results and analysis

## Author

**Abhilash Agarwal** — M.Tech (AI), IIT Jodhpur
