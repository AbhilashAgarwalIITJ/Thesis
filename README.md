# AI-Augmented Verilog Netlist Matching Using AIG and Graph Neural Networks

**M.Tech Thesis** — School of Artificial Intelligence and Data Science (AIDE), IIT Jodhpur  
**Author:** Abhilash Agarwal  
**MTP-2 → MTP-3 (Final Submission)**

---

## Problem Statement

Modern VLSI design flows require verifying that two versions of a circuit — before and after synthesis optimisation, technology mapping, or manual editing — remain functionally consistent. Traditional approaches rely on formal equivalence checking (SAT/BDD), which is exact but scales poorly on large industrial netlists. Structural comparison methods exist but are shallow: they match aggregate statistics (gate counts, node counts) and miss subtle local differences such as inverted carry signals or swapped gate types.

**This thesis investigates whether graph-based structural hashing — specifically Weisfeiler-Leman (WL) colour refinement applied to And-Inverter Graph (AIG) representations — can serve as a fast, scalable pre-filter for netlist equivalence checking, detecting structural mutations that simpler fingerprinting methods miss.**

## Literature Gap

| Approach | Limitation |
|---|---|
| SAT/BDD-based formal methods | Exponential worst-case; impractical as a quick pre-filter |
| Structural fingerprinting (node/edge/gate counts) | Identical statistics for structurally different circuits (false positives) |
| Graph isomorphism (VF2, etc.) | Exact but NP-hard in general; overkill for pre-filtering |
| GNN-based similarity | Requires labelled training data; not interpretable; no EDA-specific benchmarks |

**Gap:** No existing work applies WL hashing at the output-cone granularity on AIG representations for netlist comparison. This thesis fills that gap with a lightweight, interpretable, training-free approach that simultaneously establishes the analytical GNN baseline for the AI-for-EDA domain.

## AI Relevance: The WL–GNN Equivalence

The thesis title includes "Graph Neural Networks" by design: the WL hashing algorithm used in this work is not merely a graph-similarity heuristic — it is the **analytical foundation of message-passing Graph Neural Networks**.

Xu et al. (ICLR 2019, *"How Powerful are Graph Neural Networks?"*) and Morris et al. (NeurIPS 2019, *"Weisfeiler and Leman Go Neural"*) formally proved that any message-passing GNN with an injective neighbourhood-aggregation function has expressive power **exactly equivalent** to the 1-WL colour refinement algorithm. Two graphs that WL hashing cannot distinguish cannot be distinguished by any such GNN either.

**Implication for this thesis:** By implementing WL hashing on AIG output cones, this work implements the **analytical upper bound** of what any trained GNN could discriminate on these graphs — without requiring labelled training data, training infrastructure, GPU hardware, or hyperparameter tuning. The result is a principled, theoretically grounded approach that:

| Property | WL Hashing (this work) | Trained GNN (future work) |
|---|---|---|
| Training data required | None | Thousands of labelled pairs |
| Interpretability | Full (per-node label trace) | Low (embedding space) |
| Expressive power | 1-WL upper bound | ≤ 1-WL upper bound |
| Deployment complexity | Single Python file | Training pipeline + GPU |
| Theoretical grounding | Proven equivalence | Empirical |

This work therefore serves a dual role: (1) a practical pre-filter for equivalence checking, and (2) the **AI-for-EDA baseline** that any future GNN approach on this problem must surpass to justify its added complexity.

> **Terminology note:** In this thesis, "WL hashing" and "WL graph hashing" always refer to the 1-WL / Weisfeiler-Leman colour refinement algorithm as described by Xu et al. (2019). A "trained GNN" is positioned as future work. No GNN model was trained; none is needed to achieve the 1-WL analytical bound.

## Pipeline

```
Verilog RTL
    │
    ▼  [Yosys + ABC]
AIG (AIGER format)
    │
    ▼  [parse_aiger.py]
NetworkX DAG
    │
    ▼  [cone_extract.py]
Per-output logic cones
    │
    ├──▶ [Baseline] Structural fingerprint (nodes, edges, AND, PI, depth)
    │
    └──▶ [Advanced] WL hash (k=3, semantic-aware, inversion-aware)
            │
            ▼  [match_cones.py / experiments.py]
    Cone-level match/mismatch verdicts
            │
            ▼  [thesis_plots.py]
    Tables, figures, analysis
```

## MTP-2 Deliverables

MTP-2 established the foundational pipeline and initial validation:

| Deliverable | Scripts | Output |
|---|---|---|
| Yosys-based Verilog → AIG synthesis (single optimisation level) | `synthesize.py` | `aig_output/*.aig` |
| AIGER ASCII parser → NetworkX directed graph | `parse_aiger.py` | In-memory DAGs |
| Output cone extraction via backward traversal | `cone_extract.py` | Per-output subgraphs |
| Basic WL hashing (structure-only, fixed k) | `wl_hash.py` | Hash per cone |
| Initial cone matching on 4-bit adder | `match_cones.py` | Match/mismatch list |
| Preliminary graph statistics and visualisation | `graph_stats.py`, `generate_plots.py` | CSV + 7 plots |
| Original 9-phase pipeline runner | `run_all.py` | End-to-end demo |

## MTP-3 Deliverables

MTP-3 extended the pipeline with multi-level experiments, advanced hashing, and thesis-grade analysis:

| Deliverable | Scripts | Output |
|---|---|---|
| Multi-optimisation synthesis (O0 / O1 / O2) | `synthesize.py` (extended) | 3 AIG variants per design |
| Expanded benchmark suite (8 designs + 2 mutants) | `designs/` | 10 Verilog files |
| Baseline vs Advanced experiment framework | `experiments.py` | 6 comparison pairs × 2 methods |
| Semantic-aware and polarity-aware WL hashing | `advanced_wl.py` | Improved cone hashes |
| Scalability analysis (4-bit → 32-bit) | `experiments.py` Exp 4 | Timing data |
| WL convergence / iteration depth study (k=1..6) | `experiments.py` Exp 5 | Convergence curve |
| False-positive detection and case-study analysis | `experiments.py` Exp 3 | Table 6 (case study) |
| 6 thesis-quality figures + 6 formatted tables | `thesis_plots.py` | `results/plots/`, `results/tables/` |
| Explainability reports (pipeline, mutation, method) | `explainability.py` | Text reports |
| Unified thesis runner | `run_thesis.py` | Single-command execution |

## Final Thesis Contribution

1. **Cone-granularity WL hashing on AIGs** — a novel application of Weisfeiler-Leman colour refinement to per-output logic cones extracted from And-Inverter Graphs, providing a fast structural pre-filter for netlist equivalence checking.

2. **False-positive detection** — demonstrated that structural fingerprinting (node/edge/gate counts) reports 100% match on a carry-inversion mutation where WL hashing correctly identifies 2 out of 5 cones as structurally different (60% match), exposing a 40% false-positive rate in the baseline.

3. **Empirical characterisation** — five controlled experiments across mutation detection, re-synthesis equivalence, cross-design rejection, scalability (2.7 ms → 112 ms for 4→32 bits), and WL convergence (stabilises at k=3).

## Key Results

| Comparison | Baseline (Fingerprint) | Advanced (WL Hash) | Observation |
|---|---|---|---|
| Gate replacement (XOR→OR) | 40% | 40% | Both detect; gate count changes |
| **Carry inversion (~c[2])** | **100% (FP)** | **60%** | **WL catches what fingerprint misses** |
| O1 vs O2 optimisation | 100% | 100% | Identical AIG (Yosys deterministic) |
| O0 vs O1 optimisation | 20% | 20% | Heavy restructuring; expected |
| Cross-design (adder vs counter) | 0% | 0% | Correctly rejected |

See [docs/RESULTS_SUMMARY.md](docs/RESULTS_SUMMARY.md) for detailed analysis.

## Academic Milestone Mapping

| Aspect | MTP-2 (Foundation) | MTP-3 (Completion) |
|---|---|---|
| Designs | 1 (4-bit adder) | 8 designs + 2 mutants |
| Synthesis | Single optimisation level | 3 levels (O0, O1, O2) |
| Hashing | Structure-only WL | Semantic-aware + polarity-aware WL |
| Experiments | Self-matching demo | 5 controlled experiments |
| Comparison | No baseline | Fingerprint baseline vs WL advanced |
| Figures | 7 preliminary | 13 publication-ready |
| Tables | None | 6 formatted |
| Mutation testing | None | Gate replacement + carry inversion |
| Scalability | Not measured | 4→32 bit timing analysis |
| Runner | `run_all.py` (demo) | `run_thesis.py` (reproducible) |

For detailed MTP-2/MTP-3 breakdown with per-script mapping, see [docs/MTP_PROGRESS.md](docs/MTP_PROGRESS.md).

## Repository Structure

```
├── designs/                  # Verilog benchmarks (MTP-2 + MTP-3)
│   ├── adder_4bit.v          #   MTP-2: core benchmark
│   ├── adder_8bit.v          #   MTP-3: scalability study
│   ├── adder_16bit.v         #   MTP-3: scalability study
│   ├── adder_32bit.v         #   MTP-3: scalability study
│   ├── mux_4to1.v            #   MTP-3: cross-design experiment
│   ├── counter_4bit.v        #   MTP-3: cross-design experiment
│   ├── alu_simple.v          #   MTP-3: cross-design experiment
│   ├── comparator_4bit.v     #   MTP-3: cross-design experiment
│   └── mutants/
│       ├── adder_4bit_mut1.v #   MTP-3: gate-replacement mutation
│       └── adder_4bit_mut2.v #   MTP-3: carry-inversion mutation
├── src/                      # Python pipeline
│   ├── synthesize.py         #   MTP-2 (core) + MTP-3 (multi-opt)
│   ├── parse_aiger.py        #   MTP-2
│   ├── cone_extract.py       #   MTP-2
│   ├── wl_hash.py            #   MTP-2
│   ├── match_cones.py        #   MTP-2
│   ├── advanced_wl.py        #   MTP-3: semantic + polarity WL
│   ├── experiments.py        #   MTP-3: 5-experiment suite
│   ├── thesis_plots.py       #   MTP-3: thesis figures
│   ├── generate_plots.py     #   MTP-2 (original plots)
│   ├── graph_stats.py        #   MTP-2
│   ├── explainability.py     #   MTP-3: text reports
│   ├── run_thesis.py         #   MTP-3: master runner ★
│   ├── run_all.py            #   MTP-2: original runner
│   └── run_experiments.py    #   MTP-3: standalone experiments
├── aig_output/               # Pre-generated AIGER files
├── results/
│   ├── csv/                  # 18 experiment CSVs
│   ├── plots/                # 13 figures (PNG)
│   └── tables/               # 6 formatted result tables
├── docs/
│   ├── MTP_PROGRESS.md       # MTP-2 → MTP-3 progression
│   └── RESULTS_SUMMARY.md    # Detailed result analysis
└── requirements.txt          # Python dependencies
```

## How to Reproduce Results

```bash
# 1. Clone and setup
git clone https://github.com/AbhilashAgarwalIITJ/Thesis.git
cd Thesis
python -m venv .venv                     # or python3 on Linux/macOS
.\.venv\Scripts\Activate.ps1             # Windows; use source .venv/bin/activate on Linux
pip install -r requirements.txt

# 2. (Optional) Install Yosys for re-synthesis — see Setup Guide below
#    If skipped, pre-generated AIGs in aig_output/ are used automatically.

# 3. Run the full pipeline
python src/run_thesis.py

# 4. Results appear in results/csv/, results/plots/, results/tables/
```

To force re-synthesis from Verilog (requires Yosys): delete `aig_output/` before running.

## Demo / Visualisation

### Interactive notebook

The fastest way to see the pipeline in action is `demo.ipynb` — a Jupyter notebook
that walks through the carry-inversion case study in 6 cells:

| Cell | What it shows |
|------|---------------|
| 1 | Load AIG, print graph statistics |
| 2 | Extract output cones, print per-cone metrics |
| 3 | Compute WL hashes (k=3, semantic + inversion-aware) |
| 4 | Load carry-inversion mutant (`adder_4bit_mut2`) |
| 5 | **Central result:** Fingerprint vs WL — shows 2 false positives caught |
| 6 | Cone graph visualisation (colour-coded by node type) |

Run it:
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

### Command-line pipeline

```bash
python src/run_thesis.py    # full pipeline: synthesis → experiments → plots (<30 sec)
python src/run_all.py       # MTP-2 pipeline with 7 preliminary plots
```

### Generated figures (13 total)

| Figure | Description |
|---|---|
| `fig1_circuit_overview.png` | Benchmark design complexity (nodes, edges, gates) |
| `fig2_scalability.png` | Runtime vs circuit size (4→32 bits) |
| `fig3_wl_convergence.png` | WL hash label count vs iteration depth k |
| `fig4_baseline_matching.png` | Baseline fingerprint match percentages |
| `fig5_advanced_comparison.png` | Advanced WL match percentages |
| `fig6_aig_graph.png` | AIG graph structure visualisation |
| `fig7_cone_visualization.png` | Output cone structure |
| `thesis_fig1–6` | Thesis-specific: scalability, comparison, distribution, benchmark, convergence, case study |

## Limitations and Future Work

**Limitations:**
- Benchmarks are small-scale combinational circuits (up to 32-bit adder, ≈400 nodes). Behaviour on industrial-scale designs (10K+ gates) is untested.
- WL hashing is a necessary but not sufficient condition for isomorphism — it cannot distinguish all non-isomorphic graphs (the 1-WL theoretical limit, as identified by Xu et al. 2019).
- Sequential circuits (with latches/flip-flops) are not handled; the pipeline targets combinational logic only.
- Matching is at cone granularity with name-based or positional pairing; it does not handle arbitrary output permutations.

**Future Work:**
- **Supervised GNN training:** Collect labelled netlist equivalence pairs and train a Graph Isomorphism Network (GIN, Xu et al. 2019) to learn embeddings that generalise beyond the structural 1-WL bound. This is the natural next step from this work's analytical baseline.
- **Higher-order WL (k-WL, k≥2):** Improve discriminative power for circuits where 1-WL hashes collide, at O(V^k) cost.
- **Hybrid pre-filter:** Use cone-level WL mismatch as a pre-filter feeding only divergent cones into a SAT/BDD formal checker — combining speed with completeness.
- **Industrial-scale evaluation:** Evaluate on ISCAS-85, ITC-99, and EPFL benchmark suites for scalability validation beyond academic designs.
- **Sequential circuits:** Extend to flip-flop-containing designs via temporal unrolling or latch abstraction.
- **Technology-mapped netlists:** Apply the pipeline post-technology-mapping (gate-level, not just AIG) to verify place-and-route equivalence.

---

## End-to-End Setup Guide

Follow these steps in order to set up everything from scratch on a clean machine.

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| **Git** | Any recent | Clone the repository |
| **Python** | 3.10 or newer | Run the pipeline |
| **Yosys** (via oss-cad-suite) | 0.40+ | Synthesise Verilog → AIGER |

---

### Step 1 — Install Git

**Windows:**
```powershell
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
```
Then **restart your terminal** (or open a new PowerShell window) so `git` is on PATH.

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install -y git
```

**macOS:**
```bash
xcode-select --install      # installs git as part of command-line tools
```

Verify:
```
git --version
```

---

### Step 2 — Install Python

**Windows:**

Download from https://www.python.org/downloads/ (3.10 or newer).  
During installation, **check "Add Python to PATH"**.

Or via winget:
```powershell
winget install --id Python.Python.3.12 -e
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install -y python3 python3-pip python3-venv
```

**macOS:**
```bash
brew install python@3.12
```

Verify:
```
python --version        # Windows
python3 --version       # Linux/macOS
```

> **Note:** On some Windows machines, use `py` instead of `python`.

---

### Step 3 — Clone the Repository

```bash
git clone https://github.com/AbhilashAgarwalIITJ/Thesis.git
cd Thesis
```

---

### Step 4 — Create a Python Virtual Environment & Install Dependencies

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If you get an execution policy error, run this first:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This installs: `networkx`, `matplotlib`, `numpy`, `pandas`, `tabulate`.

---

### Step 5 — Install Yosys (oss-cad-suite)

Yosys is the open-source synthesis tool that converts Verilog into AIGER format.
The easiest way to get it is via **oss-cad-suite** (pre-built binaries including Yosys + ABC).

#### Windows

1. Go to https://github.com/YosysHQ/oss-cad-suite-build/releases
2. Download the latest **`oss-cad-suite-windows-x64-YYYYMMDD.exe`** (≈300 MB)
3. Run the `.exe` — it is a self-extracting archive. Extract it **into the project folder** so you get:
   ```
   Thesis/
     oss-cad-suite/
       bin/
       lib/
       ...
   ```
4. Add both `bin/` and `lib/` to your PATH in the same terminal session:
   ```powershell
   $env:PATH = "$PWD\oss-cad-suite\bin;$PWD\oss-cad-suite\lib;" + $env:PATH
   ```
5. Verify:
   ```powershell
   yosys -V
   ```
   Expected output: `Yosys 0.xx (git sha1 ..., ...)`

> **Important (Windows only):** Yosys needs **both** `bin/` and `lib/` on PATH for DLL loading.  
> The `synthesize.py` script auto-detects `oss-cad-suite/` in the project root and adds it to PATH automatically, so once extracted to the right place you don't need to set PATH manually when running the pipeline.

#### Linux (Ubuntu/Debian)

Option A — Package manager:
```bash
sudo apt install -y yosys
```

Option B — oss-cad-suite (for latest version):
```bash
# Download the linux-x64 release
wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-04-16/oss-cad-suite-linux-x64-20260416.tgz
tar -xzf oss-cad-suite-linux-x64-20260416.tgz
export PATH="$PWD/oss-cad-suite/bin:$PATH"
yosys -V
```

#### macOS

```bash
brew install yosys
# or download oss-cad-suite darwin-x64 release from GitHub
```

---

### Step 6 — Run the Full Pipeline

Make sure your virtual environment is activated and (on Windows) Yosys is on PATH,
then run:

```bash
python src/run_thesis.py
```

This executes the complete pipeline:

| Phase | What happens |
|---|---|
| **Synthesis** | Converts all 10 Verilog designs into AIGER at 3 optimisation levels (O0, O1, O2) → `aig_output/` |
| **AIG Loading** | Parses all `.aig` files into NetworkX directed graphs |
| **Experiment 1** | Pipeline validation — end-to-end on 4-bit adder |
| **Experiment 2** | Self-equivalence under re-synthesis (O0 vs O1 vs O2) |
| **Experiment 3** | Mutation detection (gate replace + carry inversion) |
| **Experiment 4** | Scalability analysis (4-bit → 32-bit) |
| **Experiment 5** | WL iteration depth sensitivity (k = 1..6) |
| **Tables** | 6 formatted result tables → `results/tables/` |
| **Plots** | 13 publication-ready figures → `results/plots/` |
| **CSVs** | 18 raw data files → `results/csv/` |

Expected runtime: **under 30 seconds** on a modern machine.

> **Note:** If the `aig_output/` directory already contains `.aig` files (which it does
> in the cloned repo), synthesis is **skipped automatically**. To force re-synthesis,
> delete the `aig_output/` folder before running.

---

### Step 7 — Check the Results

After the run completes:

```bash
# View a result table
cat results/tables/table4_comparison.txt

# List all generated plots
ls results/plots/

# Open a CSV in any spreadsheet tool
# results/csv/table4_comparison.csv
```

| Directory | Files | Contents |
|---|---|---|
| `results/csv/` | 18 CSVs | Benchmark stats, matching details, scalability timings, convergence data |
| `results/plots/` | 13 PNGs | Bar charts, line plots, heatmaps, AIG visualisation |
| `results/tables/` | 6 TXTs | Formatted grid tables for each experiment |

---

## Alternative Run Modes

### Run Only Experiments (skip synthesis + use pre-built AIGs)

```bash
python src/run_experiments.py
```

### Run Original 9-Phase Pipeline

```bash
python src/run_all.py
```

### Use Individual Modules in Python

```python
import sys
sys.path.insert(0, "src")

from parse_aiger import parse_aiger_file, aiger_to_networkx
from cone_extract import extract_all_cones
from wl_hash import wl_hash_all_cones

# Parse an AIGER file
parsed = parse_aiger_file("aig_output/adder_4bit.aig")
G, po_nodes = aiger_to_networkx(parsed)

# Extract output cones
cones = extract_all_cones(G, po_nodes)

# Compute WL hash for each cone
hashes = wl_hash_all_cones(cones, k=3, semantic=True)
for name, h in hashes.items():
    print(f"{name}: {h}")
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `python` not found on Windows | Try `py` or `python3` instead. Or reinstall Python with "Add to PATH" checked. |
| `yosys` not found | Ensure oss-cad-suite `bin/` and `lib/` are on PATH. On Windows, the script auto-detects if extracted in project root. |
| `Activate.ps1 cannot be loaded` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first. |
| `pip install` fails | Make sure you activated the venv first (`.\.venv\Scripts\Activate.ps1` or `source .venv/bin/activate`). |
| Synthesis produces different results | Expected — different Yosys versions may produce slightly different AIGs. Core experiments still work. |
| DLL load errors on Windows | Both `oss-cad-suite\bin\` AND `oss-cad-suite\lib\` must be on PATH. |

## Further Documentation

- [docs/MTP_PROGRESS.md](docs/MTP_PROGRESS.md) — Detailed MTP-2 → MTP-3 progression
- [docs/RESULTS_SUMMARY.md](docs/RESULTS_SUMMARY.md) — Complete experiment results and analysis

## Author

Abhilash Agarwal — M.Tech (AI), IIT Jodhpur
