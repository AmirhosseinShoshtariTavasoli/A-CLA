#!/usr/bin/env python3
# Modularity from CPM, SLPA, DEMON (prints modularity only)
# ---------------------------------------------------------
# Requirements:
#   - networkx, pandas
#   - cdlib (for SLPA and DEMON): pip install cdlib
#
# Output format (only these three lines if all libs available):
#   CPM_modularity: 0.1234
#   SLPA_modularity: 0.2345
#   DEMON_modularity: 0.3456

import pandas as pd
import networkx as nx
from pathlib import Path
from typing import List, Set, Dict
from collections import defaultdict
from networkx.algorithms.community import k_clique_communities
from networkx.algorithms.community.quality import modularity as nx_modularity

# ------------- SETTINGS -------------
FILE_PATH = "adjacency_matrix_yeast_output.xlsx"  # change to your file
# True: treat >0 as edge; False: keep weights (modularity below is unweighted)
BINARIZE = True
CPM_K = 3            # Clique size for CPM
SLPA_T = 100         # SLPA iterations
SLPA_R = 0.03        # SLPA post-processing threshold
DEMON_EPS = 0.25     # DEMON epsilon
# ------------------------------------


def load_adjacency(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, index_col=0)
    elif path.suffix.lower() in (".csv", ".txt"):
        df = pd.read_csv(path, index_col=0)
    else:
        raise ValueError(f"Unsupported file: {path.suffix}")
    if df.shape[0] != df.shape[1]:
        raise ValueError(f"Adjacency must be square, got {df.shape}")
    if not df.index.equals(df.columns):
        # allow reordering if sets match
        if set(map(str, df.index)) == set(map(str, df.columns)):
            df = df.loc[df.index, df.index]
        else:
            raise ValueError("Row/column labels must match.")
    return df


def make_graph(df: pd.DataFrame, binarize: bool) -> nx.Graph:
    if binarize:
        A = (df > 0).astype(int)
        G = nx.from_pandas_adjacency(A)
    else:
        G = nx.from_pandas_adjacency(df.astype(float))
    G.remove_edges_from(nx.selfloop_edges(G))
    # normalize node labels to strings to avoid type mismatches
    G = nx.relabel_nodes(G, lambda x: str(x))
    return G


def overlap_to_partition(overlapping: List[Set], G: nx.Graph) -> List[Set[str]]:
    """
    Convert overlapping communities to a disjoint partition:
    assign each node to the community where it has the most intra-community neighbors.
    Ties: larger community size, then first occurrence. Uncovered nodes -> singleton.
    """
    G_nodes = set(G.nodes())
    comms: List[Set[str]] = []
    for c in overlapping:
        sc = set(map(str, c)) & G_nodes
        if sc:
            comms.append(sc)

    cand: Dict[str, List[int]] = defaultdict(list)
    for cid, c in enumerate(comms):
        for n in c:
            cand[n].append(cid)

    csize = {i: len(c) for i, c in enumerate(comms)}

    assignment: Dict[str, int] = {}
    for n in G_nodes:
        if n not in cand:
            assignment[n] = -1
            continue
        # pick community with max intra-degree (tie-break by size)
        neigh = set(G.neighbors(n))
        best_cid, best_tuple = None, None  # (intra_deg, csize)
        for cid in cand[n]:
            c = comms[cid]
            t = (len(neigh & c), csize[cid])
            if best_tuple is None or t > best_tuple:
                best_tuple = t
                best_cid = cid
        assignment[n] = best_cid if best_cid is not None else cand[n][0]

    part_map: Dict[int, Set[str]] = defaultdict(set)
    singletons: List[Set[str]] = []
    for n, cid in assignment.items():
        if cid == -1:
            singletons.append({n})
        else:
            part_map[cid].add(n)

    partition = [c for c in part_map.values() if len(c) > 0] + singletons
    return partition


def run_cpm_modularity(G: nx.Graph, k: int) -> float:
    comms = [set(c) for c in k_clique_communities(G, k)]
    part = overlap_to_partition(comms, G) if comms else []
    return nx_modularity(G, part) if len(part) > 1 else 0.0


def run_slpa_modularity(G: nx.Graph, T: int, r: float):
    try:
        from cdlib import algorithms
    except Exception:
        return None  # unavailable
    res = algorithms.slpa(G, T, r)
    comms = [set(map(str, c)) & set(G.nodes())
             for c in res.communities if len(c) > 0]
    part = overlap_to_partition(comms, G) if comms else []
    return nx_modularity(G, part) if len(part) > 1 else 0.0


def run_demon_modularity(G: nx.Graph, eps: float):
    try:
        from cdlib import algorithms
    except Exception:
        return None  # unavailable
    res = algorithms.demon(G, epsilon=eps)
    comms = [set(map(str, c)) & set(G.nodes())
             for c in res.communities if len(c) > 0]
    part = overlap_to_partition(comms, G) if comms else []
    return nx_modularity(G, part) if len(part) > 1 else 0.0


if __name__ == "__main__":
    path = Path(FILE_PATH)
    df = load_adjacency(path)
    G = make_graph(df, BINARIZE)

    # CPM
    q_cpm = run_cpm_modularity(G, CPM_K)
    print(f"CPM_modularity: {q_cpm:.4f}")

    # SLPA
    q_slpa = run_slpa_modularity(G, SLPA_T, SLPA_R)
    if q_slpa is None:
        # cdlib not installed or SLPA unavailable
        pass
    else:
        print(f"SLPA_modularity: {q_slpa:.4f}")

    # DEMON
    q_demon = run_demon_modularity(G, DEMON_EPS)
    if q_demon is None:
        # cdlib not installed or DEMON unavailable
        pass
    else:
        print(f"DEMON_modularity: {q_demon:.4f}")
