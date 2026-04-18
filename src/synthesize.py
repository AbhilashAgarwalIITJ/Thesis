"""
synthesize.py - Batch Yosys synthesis: Verilog -> AIG (AIGER format)
Runs Yosys to synthesize each Verilog file and export as AIGER.

MTP Phase: MTP-2 (core), MTP-3 (multi-optimisation O0/O1/O2 extension)
"""

import subprocess
import os
import sys
import time
import json

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS_DIR = os.path.join(PROJECT_ROOT, "designs")
AIG_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "aig_output")

# Try to find yosys in oss-cad-suite or PATH
def find_yosys():
    """Locate the yosys binary."""
    # Ensure oss-cad-suite lib dir is on PATH (needed for DLLs on Windows)
    oss_bin = os.path.join(PROJECT_ROOT, "oss-cad-suite", "bin")
    oss_lib = os.path.join(PROJECT_ROOT, "oss-cad-suite", "lib")
    for d in [oss_bin, oss_lib]:
        if os.path.isdir(d) and d not in os.environ.get("PATH", ""):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")

    # Check common locations
    candidates = [
        os.path.join(PROJECT_ROOT, "oss-cad-suite", "bin", "yosys.exe"),
        os.path.join(PROJECT_ROOT, "oss-cad-suite", "lib", "yosys.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "oss-cad-suite", "bin", "yosys.exe"),
        os.path.join(os.path.expanduser("~"), "oss-cad-suite", "bin", "yosys.exe"),
        "yosys",  # fallback to PATH
    ]
    for c in candidates:
        if c == "yosys" or os.path.isfile(c):
            try:
                # Yosys uses -V (not --version) for version string
                result = subprocess.run([c, "-V"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"[+] Found yosys: {c}")
                    print(f"    Version: {result.stdout.strip()}")
                    return c
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    return None


def synthesize_to_aig(yosys_bin, verilog_path, output_path, top_module=None, opt_level=None):
    """
    Synthesize a Verilog file to AIGER format using Yosys.

    Parameters:
        yosys_bin: path to yosys executable
        verilog_path: input .v file
        output_path: output .aig file
        top_module: optional top module name (auto-detected if None)
        opt_level: None (default), 0, 1, or 2
    Returns:
        dict with synthesis statistics
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Build Yosys script
    commands = []
    commands.append(f"read_verilog {verilog_path}")

    if top_module:
        commands.append(f"hierarchy -top {top_module}")

    # Synthesis with optimization control
    if opt_level is not None:
        if opt_level == 0:
            # Minimal optimization: just flatten and map to AIG
            commands.append("proc")
            commands.append("flatten")
            commands.append("aigmap")
        elif opt_level == 1:
            # Light optimization
            commands.append("synth -flatten")
            commands.append("aigmap")
        elif opt_level == 2:
            # Full optimization
            commands.append("synth -flatten")
            commands.append("opt -full")
            commands.append("aigmap")
    else:
        # Default: standard synthesis
        commands.append("synth -flatten")
        commands.append("aigmap")

    # Write AIGER and also stats
    commands.append("stat")
    commands.append(f"write_aiger -ascii {output_path}")

    script = "; ".join(commands)

    start_time = time.time()
    result = subprocess.run(
        [yosys_bin, "-p", script],
        capture_output=True,
        text=True,
        timeout=120
    )
    elapsed = time.time() - start_time

    stats = {
        "verilog_file": os.path.basename(verilog_path),
        "aig_file": os.path.basename(output_path),
        "opt_level": opt_level,
        "synthesis_time_s": round(elapsed, 3),
        "success": result.returncode == 0,
    }

    if result.returncode != 0:
        stats["error"] = result.stderr[-500:] if result.stderr else "Unknown error"
        print(f"[!] FAILED: {verilog_path}")
        print(f"    Error: {stats['error'][:200]}")
    else:
        # Parse stats from Yosys output
        for line in result.stdout.split("\n"):
            line = line.strip()
            if "Number of wires:" in line:
                stats["wires"] = int(line.split(":")[-1].strip())
            elif "Number of cells:" in line:
                stats["cells"] = int(line.split(":")[-1].strip())
            elif "Number of public wires:" in line:
                stats["public_wires"] = int(line.split(":")[-1].strip())

        print(f"[+] Synthesized: {os.path.basename(verilog_path)} -> {os.path.basename(output_path)} ({elapsed:.2f}s)")

    return stats


def batch_synthesize(yosys_bin):
    """Synthesize all Verilog designs in the designs/ directory."""

    all_stats = []

    # Collect all .v files
    verilog_files = []
    for root, dirs, files in os.walk(DESIGNS_DIR):
        for f in files:
            if f.endswith(".v"):
                verilog_files.append(os.path.join(root, f))

    verilog_files.sort()
    print(f"\n{'='*60}")
    print(f"Batch Synthesis: {len(verilog_files)} Verilog files")
    print(f"{'='*60}\n")

    for vf in verilog_files:
        basename = os.path.splitext(os.path.basename(vf))[0]
        # Determine subdirectory structure
        rel = os.path.relpath(os.path.dirname(vf), DESIGNS_DIR)
        if rel == ".":
            out_dir = AIG_OUTPUT_DIR
        else:
            out_dir = os.path.join(AIG_OUTPUT_DIR, rel)

        output_path = os.path.join(out_dir, f"{basename}.aig")
        stats = synthesize_to_aig(yosys_bin, vf, output_path)
        all_stats.append(stats)

    # Also do multi-optimization-level synthesis for adder_4bit (Experiment 2)
    adder_4bit = os.path.join(DESIGNS_DIR, "adder_4bit.v")
    if os.path.exists(adder_4bit):
        print(f"\n{'='*60}")
        print(f"Multi-Optimization Synthesis (Experiment 2)")
        print(f"{'='*60}\n")
        for opt in [0, 1, 2]:
            output_path = os.path.join(AIG_OUTPUT_DIR, f"adder_4bit_O{opt}.aig")
            stats = synthesize_to_aig(yosys_bin, adder_4bit, output_path, opt_level=opt)
            all_stats.append(stats)

    # Save stats
    stats_path = os.path.join(PROJECT_ROOT, "results", "synthesis_stats.json")
    with open(stats_path, "w") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\n[+] Synthesis stats saved to {stats_path}")

    return all_stats


if __name__ == "__main__":
    yosys_bin = find_yosys()
    if yosys_bin is None:
        print("[!] Yosys not found. Please install oss-cad-suite and ensure yosys is in PATH.")
        print("    Or extract oss-cad-suite to the project root directory.")
        sys.exit(1)

    batch_synthesize(yosys_bin)
