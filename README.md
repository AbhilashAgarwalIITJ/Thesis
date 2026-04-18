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
```

## Prerequisites

- **Python 3.10+** with pip
- **Yosys** (for synthesis from Verilog → AIGER)
  - Recommended: [oss-cad-suite](https://github.com/YosysHQ/oss-cad-suite-build/releases) (includes Yosys + ABC)
  - On Windows, extract the self-extracting archive and ensure `bin/` and `lib/` are on PATH

## Installation

```bash
# Clone the repository
git clone https://github.com/AbhilashAgarwalIITJ/Thesis.git
cd Thesis

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Activate (Linux/macOS)
# source .venv/bin/activate

# Install dependencies
pip install networkx matplotlib numpy pandas tabulate
```

### Yosys Setup (Windows)

```powershell
# Download oss-cad-suite from GitHub releases, extract it into the project folder
# Then add to PATH before running:
$env:PATH = "path\to\oss-cad-suite\bin;path\to\oss-cad-suite\lib;" + $env:PATH
yosys -V  # verify: should print "Yosys 0.x ..."
```

### Yosys Setup (Linux)

```bash
# Ubuntu/Debian
sudo apt install yosys
# Or download oss-cad-suite and add to PATH
```

## Usage

### Full Pipeline (synthesis + experiments + plots)

```bash
python src/run_thesis.py
```

This runs the complete pipeline:
1. Synthesises all Verilog designs at 3 optimisation levels (O0, O1, O2)
2. Parses AIGER files into graph representations
3. Runs 5 experiments (mutation, optimisation, cross-design, scalability, convergence)
4. Generates 6 tables, 6 thesis figures, and prints discussion notes

### Skip Synthesis (use pre-generated AIGER files)

If you don't have Yosys installed, the `aig_output/` directory already contains all synthesised AIGER files. You can run experiments directly:

```bash
python src/run_experiments.py
```

### Individual Modules

```python
from src.parse_aiger import parse_aiger
from src.cone_extract import extract_cones
from src.wl_hash import wl_hash

# Parse an AIGER file
graph = parse_aiger("aig_output/adder_4bit.aig")

# Extract output cones
cones = extract_cones(graph)

# Compute WL hash for each cone
for name, cone in cones.items():
    h = wl_hash(cone, k=3)
    print(f"{name}: {h}")
```

## Output

All results are written to `results/`:

- **`results/csv/`** — Raw data (18 CSV files) including benchmark stats, matching details, scalability timings, convergence data
- **`results/plots/`** — 13 publication-ready figures (PNG)
- **`results/tables/`** — 6 formatted tables (text/grid format)

## Method Summary

**Baseline** — Structural fingerprint: compares (node count, edge count, AND gates, primary inputs, depth) per cone. Fast but cannot distinguish structurally different circuits with identical aggregate statistics.

**Advanced** — Weisfeiler-Leman hash (k=3, semantic-aware): iteratively refines node labels by aggregating neighbour labels. Captures local topology and gate semantics. Detects carry-inversion mutations that fingerprinting misses.

## Author

Abhilash Agarwal — M.Tech (AI), IIT Jodhpur
