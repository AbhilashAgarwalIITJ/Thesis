"""
parse_aiger.py - Parse ASCII AIGER format into NetworkX directed graph.

AIGER ASCII format:
  Line 1: aag M I L O A
    M = max variable index
    I = number of primary inputs
    L = number of latches
    O = number of outputs
    A = number of AND gates
  Next I lines: input literals (even numbers)
  Next L lines: latch definitions
  Next O lines: output literals
  Next A lines: AND gate definitions (lhs rhs0 rhs1)
  Symbol table (optional): i<idx> name, o<idx> name

A literal is 2*variable + inversion_bit.
Even literal = non-inverted, odd = inverted.
"""

import os
import sys
import json
import networkx as nx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIG_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "aig_output")


def literal_to_var(lit):
    """Convert a literal to its variable index."""
    return lit >> 1


def is_inverted(lit):
    """Check if a literal is inverted (negated)."""
    return lit & 1


def parse_aiger_file(filepath):
    """
    Parse an ASCII AIGER (.aig) file.

    Returns:
        dict with keys:
            'M': max variable index
            'I': number of inputs
            'L': number of latches
            'O': number of outputs
            'A': number of AND gates
            'inputs': list of input literals
            'latches': list of latch definitions
            'outputs': list of output literals
            'ands': list of (lhs, rhs0, rhs1) tuples
            'symbols': dict of symbol names
    """
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    # Parse header
    header = lines[0].split()
    assert header[0] == 'aag', f"Not an ASCII AIGER file: {filepath}"

    M = int(header[1])  # max variable index
    I = int(header[2])  # inputs
    L = int(header[3])  # latches
    O = int(header[4])  # outputs
    A = int(header[5])  # AND gates

    idx = 1

    # Parse inputs
    inputs = []
    for i in range(I):
        inputs.append(int(lines[idx]))
        idx += 1

    # Parse latches
    latches = []
    for i in range(L):
        parts = lines[idx].split()
        latches.append(tuple(int(x) for x in parts))
        idx += 1

    # Parse outputs
    outputs = []
    for i in range(O):
        outputs.append(int(lines[idx]))
        idx += 1

    # Parse AND gates
    ands = []
    for i in range(A):
        parts = lines[idx].split()
        lhs = int(parts[0])
        rhs0 = int(parts[1])
        rhs1 = int(parts[2])
        ands.append((lhs, rhs0, rhs1))
        idx += 1

    # Parse symbol table (optional)
    symbols = {}
    while idx < len(lines):
        line = lines[idx]
        if line.startswith('i') or line.startswith('o') or line.startswith('l'):
            parts = line.split(None, 1)
            if len(parts) == 2:
                symbols[parts[0]] = parts[1]
        elif line == 'c':
            break  # comment section
        idx += 1

    return {
        'M': M, 'I': I, 'L': L, 'O': O, 'A': A,
        'inputs': inputs,
        'latches': latches,
        'outputs': outputs,
        'ands': ands,
        'symbols': symbols,
        'filepath': filepath,
    }


def aiger_to_networkx(parsed):
    """
    Convert parsed AIGER data to a NetworkX directed graph.

    Node attributes:
        - 'type': 'PI' (primary input), 'AND', 'PO' (primary output), 'CONST0'
        - 'var': variable index
        - 'name': symbol name if available

    Edge attributes:
        - 'inverted': True if the connection is through an inverter
    """
    G = nx.DiGraph()

    # Add constant-0 node (variable 0)
    G.add_node(0, type='CONST0', var=0, name='const0')

    # Add primary input nodes
    for i, lit in enumerate(parsed['inputs']):
        var = literal_to_var(lit)
        name = parsed['symbols'].get(f'i{i}', f'pi_{i}')
        G.add_node(var, type='PI', var=var, name=name)

    # Add AND gate nodes and their edges
    for lhs, rhs0, rhs1 in parsed['ands']:
        var = literal_to_var(lhs)
        G.add_node(var, type='AND', var=var, name=f'and_{var}')

        # Edge from rhs0 source to this AND gate
        src0 = literal_to_var(rhs0)
        inv0 = is_inverted(rhs0)
        G.add_edge(src0, var, inverted=bool(inv0), port='rhs0')

        # Edge from rhs1 source to this AND gate
        src1 = literal_to_var(rhs1)
        inv1 = is_inverted(rhs1)
        G.add_edge(src1, var, inverted=bool(inv1), port='rhs1')

    # Add primary output nodes
    # PO nodes are virtual nodes (var index = M+1+i to avoid collision)
    po_nodes = []
    for i, lit in enumerate(parsed['outputs']):
        po_var = parsed['M'] + 1 + i
        name = parsed['symbols'].get(f'o{i}', f'po_{i}')
        G.add_node(po_var, type='PO', var=po_var, name=name)

        # Edge from the output's source to the PO node
        src = literal_to_var(lit)
        inv = is_inverted(lit)
        if src == 0 and lit == 0:
            # Output is constant 0
            G.add_edge(0, po_var, inverted=False, port='out')
        elif src == 0 and lit == 1:
            # Output is constant 1
            G.add_edge(0, po_var, inverted=True, port='out')
        else:
            G.add_edge(src, po_var, inverted=bool(inv), port='out')

        po_nodes.append(po_var)

    return G, po_nodes


def get_graph_stats(G, po_nodes):
    """Compute basic statistics about the AIG graph."""
    n_pi = sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'PI')
    n_and = sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'AND')
    n_po = len(po_nodes)
    n_const = sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'CONST0')

    # Compute depth using longest path in DAG (efficient for DAGs)
    depth = 0
    if G.number_of_nodes() > 0:
        try:
            depth = nx.dag_longest_path_length(G)
        except (nx.NetworkXError, nx.NetworkXUnfeasible):
            depth = 0

    return {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
        'primary_inputs': n_pi,
        'and_gates': n_and,
        'primary_outputs': n_po,
        'depth': depth,
    }


def load_all_aigs(aig_dir=None):
    """Load all .aig files from the output directory. Returns dict of {name: (G, po_nodes, parsed, stats)}."""
    if aig_dir is None:
        aig_dir = AIG_OUTPUT_DIR

    results = {}
    for root, dirs, files in os.walk(aig_dir):
        for f in files:
            if f.endswith('.aig'):
                filepath = os.path.join(root, f)
                name = os.path.splitext(f)[0]
                try:
                    parsed = parse_aiger_file(filepath)
                    G, po_nodes = aiger_to_networkx(parsed)
                    stats = get_graph_stats(G, po_nodes)
                    results[name] = (G, po_nodes, parsed, stats)
                    print(f"[+] Loaded {name}: {stats['nodes']} nodes, {stats['edges']} edges, "
                          f"{stats['primary_inputs']} PI, {stats['and_gates']} AND, {stats['primary_outputs']} PO")
                except Exception as e:
                    print(f"[!] Failed to load {filepath}: {e}")

    return results


if __name__ == "__main__":
    print("Loading all AIG files...\n")
    results = load_all_aigs()

    if not results:
        print("[!] No AIG files found. Run synthesize.py first.")
        sys.exit(1)

    # Print summary table
    print(f"\n{'='*80}")
    print(f"{'Design':<25} {'Nodes':>6} {'Edges':>6} {'PI':>4} {'AND':>5} {'PO':>4} {'Depth':>6}")
    print(f"{'='*80}")
    for name, (G, po_nodes, parsed, stats) in sorted(results.items()):
        print(f"{name:<25} {stats['nodes']:>6} {stats['edges']:>6} "
              f"{stats['primary_inputs']:>4} {stats['and_gates']:>5} "
              f"{stats['primary_outputs']:>4} {stats['depth']:>6}")
    print(f"{'='*80}")

    # Save stats
    stats_path = os.path.join(PROJECT_ROOT, "results", "graph_stats.json")
    stats_dict = {name: stats for name, (G, po, p, stats) in results.items()}
    with open(stats_path, "w") as f:
        json.dump(stats_dict, f, indent=2)
    print(f"\n[+] Graph stats saved to {stats_path}")
