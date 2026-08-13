#!/usr/bin/env python3
# LIDEN-style overlapping community detection:
# - Start with Louvain (crisp communities)
# - Compute node -> community "affinity" = (sum of incident edge weights to that community) / (node degree)
# - Assign a node to multiple communities if secondary affinities are close to the top (relative + absolute thresholds)

import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

import pandas as pd
import networkx as nx

# =============== SETTINGS ===============
# <-- put your file here (.xlsx/.xls/.csv)
file_path = "adjacency_matrix_yeast_output.xlsx"
# None => treat >0 as edge; numeric => binarize at threshold for building G
weight_threshold = None
# if True: use weights in affinity; if False: count edges
use_weights_for_affinity = True
# LIDEN assignment thresholds:
ABS_MIN = 0.20     # absolute minimum affinity to include a community (0..1)
# include communities with affinity >= (1 - REL_MARGIN) * top_affinity
REL_MARGIN = 0.15
# require at least this many edges from node to the candidate community
MIN_EDGES_TO_COMM = 1
# Outputs
SAVE_COMMUNITIES_TXT = True
SAVE_MEMBERSHIP_CSV = True
OUT_PREFIX = None  # None => derived from file name; or set like "DanioRerio_LIDEN"
# ========================================


def load_adjacency(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, index_col=0)
    elif path.suffix.lower() in (".csv", ".txt"):
        df = pd.read_csv(path, index_col=0)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    if df.shape[0] != df.shape[1]:
        raise ValueError(f"Adjacency must be square, got {df.shape}")
    if not df.index.equals(df.columns):
        if set(df.index) == set(df.columns):
            df = df.loc[df.index, df.index]
        else:
            raise ValueError("Row/column labels must match.")
    return df


def build_graph(df: pd.DataFrame, thr: Optional[float]) -> nx.Graph:
    """Build undirected graph; optionally binarize edges for the topology (CPM/label-like behavior)."""
    if thr is None:
        A = df.copy()
        # keep any positive weight edges
        A = A.where(A > 0, 0.0)
    else:
        A = (df >= thr).astype(float)
    # ensure symmetry
    if not A.equals(A.T):
        A = (A + A.T) / 2.0
    G = nx.from_pandas_adjacency(A)
    G.remove_edges_from(nx.selfloop_edges(G))
    return G


def run_louvain(G: nx.Graph) -> Dict:
    try:
        import community as community_louvain  # python-louvain
    except Exception as e:
        raise RuntimeError(
            "Please install python-louvain: pip install python-louvain") from e
    part = community_louvain.best_partition(
        G, weight="weight" if use_weights_for_affinity else None)
    return part  # dict node -> community id


def communities_from_partition(partition: Dict) -> List[Set]:
    byc: Dict[int, Set] = {}
    for n, cid in partition.items():
        byc.setdefault(cid, set()).add(n)
    return [byc[c] for c in sorted(byc.keys())]


def node_affinities(
    G: nx.Graph,
    partition: Dict,
    use_weights: bool = True,
    min_edges_to_comm: int = 1
) -> Dict:
    """
    For each node, compute affinity to all *neighboring* communities:
    affinity(node, C) = (sum of edge weights from node to nodes in C) / (sum of weights of node)
    If use_weights=False, weights are treated as 1 (edge counts).
    Only consider communities that actually receive at least 'min_edges_to_comm' edges from the node.
    """
    # Map community -> set of members
    comm_members: Dict[int, Set] = {}
    for n, cid in partition.items():
        comm_members.setdefault(cid, set()).add(n)

    aff: Dict = {}
    for u in G.nodes():
        # degree (weighted or unweighted)
        if use_weights:
            deg_u = sum(data.get("weight", 1.0)
                        for _, _, data in G.edges(u, data=True))
        else:
            deg_u = G.degree(u)
        if deg_u == 0:
            aff[u] = {}
            continue

        # collect neighbor communities for speed
        neigh_nodes = set(G.neighbors(u))
        neigh_comms = set(partition[v] for v in neigh_nodes)

        scores = {}
        for cid in neigh_comms:
            members = comm_members[cid]
            # neighbors that belong to this community
            targets = neigh_nodes & members
            if len(targets) < min_edges_to_comm:
                continue
            if use_weights:
                wsum = 0.0
                for v in targets:
                    w = G[u][v].get("weight", 1.0)
                    wsum += w
            else:
                wsum = float(len(targets))
            scores[cid] = wsum / deg_u  # in [0,1]

        aff[u] = scores
    return aff  # dict node -> dict{cid: affinity}


def liden_assignments(
    partition: Dict,
    affinities: Dict,
    abs_min: float,
    rel_margin: float
) -> Dict:
    """
    Build overlapping memberships:
    - Always include the node's Louvain community
    - Include any other community with affinity >= abs_min AND within (1 - rel_margin) * top_affinity
    """
    memberships: Dict = {}
    for u, aff_map in affinities.items():
        # always include Louvain's own assignment
        primary = partition[u]
        chosen = {primary}
        if aff_map:
            # top affinity among seen communities (including primary if present)
            top_aff = max(aff_map.values()) if aff_map else 0.0
            for cid, a in aff_map.items():
                if a >= abs_min and a >= (1.0 - rel_margin) * top_aff:
                    chosen.add(cid)
        memberships[u] = chosen
    return memberships  # node -> set of community ids


def overlapping_summary(memberships: Dict) -> Tuple[int, int, int]:
    """
    Returns:
      - num_communities (distinct IDs)
      - num_overlapping_nodes (membership size > 1)
      - num_overlapping_communities (communities containing >=1 overlapping node)
    """
    all_cids = set()
    overlap_nodes = 0
    comm_has_overlap: Dict[int, bool] = {}
    for u, cset in memberships.items():
        for c in cset:
            all_cids.add(c)
        if len(cset) > 1:
            overlap_nodes += 1
            for c in cset:
                comm_has_overlap[c] = True
    overlap_comms = sum(1 for c in all_cids if comm_has_overlap.get(c, False))
    return len(all_cids), overlap_nodes, overlap_comms


def export_outputs(
    memberships: Dict,
    out_base: Path
):
    # Communities as lines
    comm_to_nodes: Dict[int, Set] = {}
    for node, cset in memberships.items():
        for c in cset:
            comm_to_nodes.setdefault(c, set()).add(node)

    if SAVE_COMMUNITIES_TXT:
        txt_path = out_base.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for cid in sorted(comm_to_nodes.keys()):
                members = sorted(
                    list(comm_to_nodes[cid]), key=lambda x: (isinstance(x, str), x))
                f.write(
                    f"Community {cid} (size={len(members)}): {', '.join(map(str, members))}\n")
        print(f"Communities saved to: {txt_path}")

    if SAVE_MEMBERSHIP_CSV:
        rows = []
        for node, cset in memberships.items():
            rows.append({
                "node": node,
                "communities": "[" + ",".join(map(str, sorted(list(cset)))) + "]",
                "multiplicity": len(cset)
            })
        df = pd.DataFrame(rows).sort_values(
            by=["multiplicity", "node"], ascending=[False, True])
        csv_path = Path(str(out_base) + "_membership.csv")
        df.to_csv(csv_path, index=False)
        print(f"Memberships (with overlaps) saved to: {csv_path}")


if __name__ == "__main__":
    path = Path(file_path)
    base = Path(OUT_PREFIX) if OUT_PREFIX else Path(
        path.stem + f"_LIDEN_abs{str(ABS_MIN).replace('.', 'p')}_rel{str(REL_MARGIN).replace('.', 'p')}")
    # 1) Load & build graph
    df = load_adjacency(path)
    G = build_graph(df, weight_threshold)

    # 2) Louvain baseline
    t0 = time.time()
    part = run_louvain(G)
    t_louvain = time.time() - t0

    # 3) Affinities & LIDEN assignments
    t1 = time.time()
    aff = node_affinities(
        G, part, use_weights=use_weights_for_affinity, min_edges_to_comm=MIN_EDGES_TO_COMM)
    memberships = liden_assignments(part, aff, ABS_MIN, REL_MARGIN)
    t_liden = time.time() - t1

    # 4) Summary
    ncom, n_overlap_nodes, n_overlap_comms = overlapping_summary(memberships)
    print(f"\nLIDEN results for {path.name}")
    print(
        f"  Louvain time: {t_louvain:.4f}s | LIDEN post-process time: {t_liden:.4f}s")
    print(f"  Communities: {ncom}")
    print(f"  Overlapping nodes: {n_overlap_nodes}")
    print(f"  Overlapping communities: {n_overlap_comms}")

    # 5) Export
    export_outputs(memberships, base)
