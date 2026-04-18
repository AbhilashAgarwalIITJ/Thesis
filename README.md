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
├── designs/                  # Verilog source files (8 designs + 2 mutants)
│   ├── adder_4bit.v          # 4-bit ripple carry adder (core benchmark)
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
│   ├── match_cones.py        # Cone-level matching by WL hash
│   ├── advanced_wl.py        # Polarity-aware + hybrid WL scoring
│   ├── experiments.py        # 5-experiment suite (baseline vs advanced)
│   ├── thesis_plots.py       # Thesis-quality figure generation (6 plots)
│   ├── generate_plots.py     # Additional plot generation (7 plots)
│   ├── graph_stats.py        # Graph/cone statistics → CSV
│   ├── explainability.py     # Text report generation
│   ├── run_thesis.py         # ★ Master runner: synthesis → experiments → plots
│   ├── run_all.py            # Original pipeline runner (9 phases)
│   └── run_experiments.py    # Standalone experiment runner
├── aig_output/               # Synthesised AIGER files (pre-generated)
├── results/
│   ├── csv/                  # 18 experiment data files
│   ├── plots/                # 13 figures (PNG)
│   └── tables/               # 6 formatted result tables
└── requirements.txt          # Python dependencies
```

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

---

## Method Summary

**Baseline** — Structural fingerprint: compares (node count, edge count, AND gates, primary inputs, depth) per cone. Fast but cannot distinguish structurally different circuits with identical aggregate statistics.

**Advanced** — Weisfeiler-Leman hash (k=3, semantic-aware): iteratively refines node labels by aggregating neighbour labels. Captures local topology and gate semantics. Detects carry-inversion mutations that fingerprinting misses.

## Author

Abhilash Agarwal — M.Tech (AI), IIT Jodhpur
