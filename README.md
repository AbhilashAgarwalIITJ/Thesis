# AI-Augmented Verilog Netlist Matching Using AIG and WL Hashing

M.Tech Thesis — Department of Electrical Engineering, IIT Jodhpur

## Overview

This project implements an automated pipeline for **comparing Verilog netlists** at the structural level using:

1. **Yosys synthesis** — converts Verilog designs into And-Inverter Graphs (AIG) in AIGER format
2. **AIG parsing** — builds a directed acyclic graph (NetworkX) from the AIGER file
3. **Output cone extraction** — isolates the logic cone for each primary output
4. **Weisfeiler-Leman (WL) hashing** — computes structural fingerprints of each cone (semantic-aware + inversion-aware)
5. **Cone-level matching** — compares corresponding cones between two designs to determine equivalence

The key contribution is demonstrating that **WL-based hashing detects subtle mutations** (e.g., carry-inversion) that simple structural fingerprinting (node/edge/gate counts) misses as false positives.

## Key Results

| Comparison | Baseline (Fingerprint) | Advanced (WL Hash) |
|---|---|---|
| Gate replacement (XOR→OR) | 40% match | 40% match |
| **Carry inversion (~c[2])** | **100% (false positive)** | **60% (correctly rejects 2 cones)** |
| O1 vs O2 optimisation | 100% | 100% |
| O0 vs O1 optimisation | 20% | 20% |
| Cross-design (adder vs counter) | 0% | 0% |

Scalability: 4-bit adder 2.7 ms → 32-bit adder 112 ms (linear growth).

## Repository Structure

```
├── designs/                  # Verilog source files
│   ├── adder_4bit.v          # 4-bit ripple carry adder
│   ├── adder_8bit.v          # 8-bit hierarchical adder
│   ├── adder_16bit.v         # 16-bit parameterised adder
│   ├── adder_32bit.v         # 32-bit parameterised adder
│   ├── mux_4to1.v            # 4-to-1 multiplexer
│   ├── counter_4bit.v        # 4-bit combinational incrementer
│   ├── alu_simple.v          # 4-bit ALU (ADD/SUB/AND/OR)
│   ├── comparator_4bit.v     # 4-bit magnitude comparator
│   └── mutants/
│       ├── adder_4bit_mut1.v # XOR→OR gate replacement in bit 2
│       └── adder_4bit_mut2.v # Carry inversion (~c[2]) at bit 3
├── src/                      # Python source code
│   ├── synthesize.py         # Yosys synthesis runner (O0/O1/O2)
│   ├── parse_aiger.py        # AIGER ASCII → NetworkX DAG
│   ├── cone_extract.py       # Output cone extraction
│   ├── wl_hash.py            # WL hashing (structural + semantic)
│   ├── match_cones.py        # Cone-level matching
│   ├── advanced_wl.py        # Polarity-aware + hybrid WL
│   ├── experiments.py        # 5-experiment suite (baseline vs advanced)
│   ├── thesis_plots.py       # Thesis-quality figure generation
│   ├── generate_plots.py     # Additional plot generation
│   ├── graph_stats.py        # Graph/cone statistics → CSV
│   ├── explainability.py     # Text report generation
│   ├── run_thesis.py         # Master runner: synthesis → experiments → plots
│   ├── run_all.py            # Original pipeline runner
│   └── run_experiments.py    # Standalone experiment runner
├── aig_output/               # Synthesised AIGER files (pre-generated)
├── results/
│   ├── csv/                  # 18 experiment data files
│   ├── plots/                # 13 figures (PNG)
│   └── tables/               # 6 formatted result tables
└── requirements.txt          # Python dependencies
```

## Quick Start (No Yosys needed)

The repository includes **pre-generated AIGER files** in `aig_output/`, so you can run
all experiments without installing Yosys. Just clone, install Python dependencies, and run.

### Windows (PowerShell)

```powershell
git clone https://github.com/AbhilashAgarwalIITJ/Thesis.git
cd Thesis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/run_thesis.py
```

### Linux / macOS

```bash
git clone https://github.com/AbhilashAgarwalIITJ/Thesis.git
cd Thesis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/run_thesis.py
```

Results will be written to `results/csv/`, `results/plots/`, and `results/tables/`.

## Full Setup (with Yosys for re-synthesis)

If you want to re-synthesise the Verilog designs from scratch (not required — AIGs
are already included), install Yosys:

### Windows

1. Download [oss-cad-suite](https://github.com/YosysHQ/oss-cad-suite-build/releases) (the `windows-x64` self-extracting `.exe`)
2. Extract it into the project folder (creates an `oss-cad-suite/` directory)
3. Add to PATH before running:

```powershell
$env:PATH = ".\oss-cad-suite\bin;.\oss-cad-suite\lib;" + $env:PATH
yosys -V   # should print "Yosys 0.x ..."
python src/run_thesis.py
```

### Linux

```bash
sudo apt install yosys   # Ubuntu/Debian
# or download oss-cad-suite and add bin/ to PATH
python src/run_thesis.py
```

## Usage

### Full Pipeline (recommended)

```bash
python src/run_thesis.py
```

Runs everything end-to-end:
1. Synthesis (skipped automatically if `aig_output/` has pre-built `.aig` files)
2. Parses AIGER files into graph representations
3. Runs 5 experiments (mutation, optimisation, cross-design, scalability, convergence)
4. Generates 6 tables, 6 thesis figures, and prints discussion notes

### Individual Modules

```python
import sys, os
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

## Output

All results are written to `results/`:

| Directory | Contents |
|---|---|
| `results/csv/` | 18 CSV files — benchmark stats, matching details, scalability timings, convergence data |
| `results/plots/` | 13 PNG figures — publication-ready charts and visualisations |
| `results/tables/` | 6 text files — formatted grid tables for each experiment |

## Method Summary

**Baseline** — Structural fingerprint: compares (node count, edge count, AND gates, primary inputs, depth) per cone. Fast but cannot distinguish structurally different circuits with identical aggregate statistics.

**Advanced** — Weisfeiler-Leman hash (k=3, semantic-aware): iteratively refines node labels by aggregating neighbour labels. Captures local topology and gate semantics. Detects carry-inversion mutations that fingerprinting misses.

## Author

Abhilash Agarwal — M.Tech (AI), IIT Jodhpur
