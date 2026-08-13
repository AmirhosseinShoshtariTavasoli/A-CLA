#!/usr/bin/env python3
# A-CLA (Optimized): fast dual-feedback with Louvain-style local modularity gain (ΔQ)
# - Global feedback uses local ΔQ (no full modularity recomputation)
# - Local feedback = neighbor agreement by community
# - Adaptive learning rate per node (degree + betweenness)
# - Soft probabilities -> overlapping memberships (tau/delta)
#
# Deps: pandas, networkx, numpy
# Usage: set FILE_PATH below and run: python acla_overlap_fast.py

import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

import numpy as np
import pandas as pd
import networkx as nx

# ===================== SETTINGS =====================
# <-- your Excel/CSV adjacency
FILE_PATH = "adjacency_matrix_yeast_output.xlsx"
RANDOM_SEED = 42

# Graph handling
# None => use >0 weights; or numeric to binarize (e.g., 0.0, 0.2)
WEIGHT_THRESHOLD = None
USE_EDGE_WEIGHTS = True    # keep 'weight' on edges

# A-CLA core
MAX_ITERS = 200
ALPHA_MIN, ALPHA_MAX = 0.03, 0.25
ALPHA_BASE, ALPHA_DEG, ALPHA_BC = 0.03, 0.12, 0.10
BETA_GLOBAL = 0.45                 # blend local vs global ΔQ (0..1)
NEW_COMM_PENALTY = 0.02            # small score for spawning new comm
CONVERGENCE_TOL = 0.01             # fraction of nodes changing per iter allowed
CONVERGENCE_PATIENCE = 6

# Overlap post-processing thresholds
TAU = 0.30
DELTA = 0.05

# Export
SAVE_COMMUNITIES_TXT = True
SAVE_MEMBERSHIP_CSV = True
OUT_PREFIX = None  # None => derived from file name
# ====================================================


# -------------------- IO & Graph --------------------
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


def build_graph(df: pd.DataFrame, thr: Optional[float], use_weights: bool) -> nx.Graph:
    A = df.copy()
    if thr is None:
        A = A.where(A > 0, 0.0)
    else:
        A = (df >= thr).astype(float)
    if not A.equals(A.T):
        A = (A + A.T) / 2.0
    G = nx.from_pandas_adjacency(A)
    G.remove_edges_from(nx.selfloop_edges(G))
    if not use_weights:
        for _, _, d in G.edges(data=True):
            d["weight"] = 1.0
    else:
        for _, _, d in G.edges(data=True):
            d["weight"] = float(d.get("weight", 1.0))
    return G


# --------------- Partition helpers ---------------
def partition_to_communities(part: Dict) -> List[Set]:
    byc = {}
    for n, cid in part.items():
        byc.setdefault(cid, set()).add(n)
    return [c for c in byc.values() if len(c) > 0]


def communities_to_partition(communities: List[Set]) -> Dict:
    part = {}
    for cid, comm in enumerate(communities):
        for n in comm:
            part[n] = cid
    return part


# --------------- Adaptive learning rate ---------------
def adaptive_alpha(G: nx.Graph) -> Dict:
    degs = dict(G.degree(weight="weight" if USE_EDGE_WEIGHTS else None))
    max_deg = max(degs.values()) if degs else 1.0
    bc = nx.betweenness_centrality(
        G, weight="weight" if USE_EDGE_WEIGHTS else None, normalized=True)
    deg_arr = np.array([degs[n] for n in G.nodes()], dtype=float)
    bc_arr = np.array([bc[n] for n in G.nodes()], dtype=float)
    deg_norm = deg_arr / (max_deg if max_deg > 0 else 1.0)
    if bc_arr.max() - bc_arr.min() < 1e-12:
        bc_norm = np.zeros_like(bc_arr)
    else:
        bc_norm = (bc_arr - bc_arr.min()) / (bc_arr.max() - bc_arr.min())
    alpha = ALPHA_BASE + ALPHA_DEG * deg_norm + ALPHA_BC * bc_norm
    alpha = np.clip(alpha, ALPHA_MIN, ALPHA_MAX)
    return {n: float(a) for n, a in zip(G.nodes(), alpha)}


# --------------- Local signals ---------------
def local_feedback_scores(G: nx.Graph, node, hard_labels: Dict[int, int], C: int) -> np.ndarray:
    """Neighbor weight fraction per community (size C)."""
    scores = np.zeros(C, dtype=float)
    total = 0.0
    for nbr in G.neighbors(node):
        w = G[node][nbr].get("weight", 1.0)
        cid = hard_labels[nbr]
        scores[cid] += w
        total += w
    if total > 0:
        scores /= total
    return scores


# --------------- Fast local ΔQ (Louvain-style) ---------------
class CommunityStats:
    """Maintain community totals needed for ΔQ computations."""

    def __init__(self, G: nx.Graph, labels: Dict[int, int]):
        self.G = G
        self.labels = dict(labels)
        self.m = sum(d.get("weight", 1.0) for _, _, d in G.edges(
            data=True))  # total edge weight (not doubled)
        self.m2 = 2.0 * self.m
        # degree per node
        self.k = {n: sum(G[n][nbr].get("weight", 1.0)
                         for nbr in G.neighbors(n)) for n in G.nodes()}
        # community total degree (sum of degrees of nodes in community)
        self.tot = {}
        for n, c in self.labels.items():
            self.tot[c] = self.tot.get(c, 0.0) + self.k[n]

    def set_label(self, n, new_c):
        old_c = self.labels[n]
        if new_c == old_c:
            return
        self.tot[old_c] -= self.k[n]
        self.tot[new_c] = self.tot.get(new_c, 0.0) + self.k[n]
        self.labels[n] = new_c

    def neigh_comm_weights(self, n) -> Dict[int, float]:
        """Sum of weights from node n to each neighboring community."""
        w_per_comm = {}
        for nbr in self.G.neighbors(n):
            w = self.G[n][nbr].get("weight", 1.0)
            c = self.labels[nbr]
            w_per_comm[c] = w_per_comm.get(c, 0.0) + w
        return w_per_comm

    def delta_Q_move(self, n, target_c) -> float:
        """Approximate modularity gain of moving n into community target_c (after removing it from its own)."""
        # Louvain local gain (up to constant scaling):
        # ΔQ ∝ k_i,in - (k_i * tot[target_c]) / m2
        k_i = self.k[n]
        k_i_in = 0.0
        for nbr in self.G.neighbors(n):
            if self.labels[nbr] == target_c:
                k_i_in += self.G[n][nbr].get("weight", 1.0)
        tot_c = self.tot.get(target_c, 0.0)
        return k_i_in - (k_i * tot_c) / self.m2


def normalize01(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return arr
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-12:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def update_probabilities(p: np.ndarray, action_idx: int, alpha: float) -> np.ndarray:
    target = np.zeros_like(p)
    target[action_idx] = 1.0
    return (1.0 - alpha) * p + alpha * target


def soft_memberships_from_probs(P: Dict[int, np.ndarray], tau: float, delta: float) -> Dict[int, Set[int]]:
    mem = {}
    for n, vec in P.items():
        if vec.size == 0:
            mem[n] = set()
            continue
        maxp = float(np.max(vec))
        keep = {i for i, p in enumerate(vec) if (
            p >= tau) or (maxp - p <= delta)}
        mem[n] = keep if keep else {int(np.argmax(vec))}
    return mem


def overlapping_summary(memberships: Dict[int, Set[int]]) -> Tuple[int, int, int]:
    all_c = set()
    overlap_nodes = 0
    comm_has_overlap = {}
    for n, cs in memberships.items():
        for c in cs:
            all_c.add(c)
        if len(cs) > 1:
            overlap_nodes += 1
            for c in cs:
                comm_has_overlap[c] = True
    overlap_comms = sum(1 for c in all_c if comm_has_overlap.get(c, False))
    return len(all_c), overlap_nodes, overlap_comms


# --------------- A-CLA (fast) ---------------
def acla_fast(G: nx.Graph,
              max_iters=MAX_ITERS,
              beta=BETA_GLOBAL,
              tau=TAU,
              delta=DELTA,
              new_comm_penalty=NEW_COMM_PENALTY):
    rng = np.random.default_rng(RANDOM_SEED)
    nodes = list(G.nodes())
    N = len(nodes)

    # Initial labels: each node own community
    hard_labels = {n: i for i, n in enumerate(nodes)}
    # Probability vectors per node
    P = {n: np.eye(1, len(nodes), k=hard_labels[n]).ravel() for n in nodes}

    # Adaptive alphas
    alpha_map = adaptive_alpha(G)

    patience = CONVERGENCE_PATIENCE
    for it in range(1, max_iters + 1):
        # Compact relabel 0..C-1
        comms = partition_to_communities(hard_labels)
        C = len(comms)
        hard_labels = communities_to_partition(comms)

        # Community stats for ΔQ
        stats = CommunityStats(G, hard_labels)

        changed = 0
        for n in nodes:
            # local scores (size C)
            local_s = local_feedback_scores(G, n, hard_labels, C)

            # global ΔQ for neighbor communities only + staying
            g_scores = np.zeros(C + 1, dtype=float)  # +1 for "new community"
            cur_c = hard_labels[n]
            g_scores[cur_c] = 0.0
            # neighbor community candidates
            neigh_w = stats.neigh_comm_weights(n)
            for c in neigh_w.keys():
                g_scores[c] = stats.delta_Q_move(n, c)

            # new community option
            new_idx = C
            local_s = np.append(local_s, new_comm_penalty)  # small baseline
            g_scores[new_idx] = 0.0  # neutral ΔQ

            # normalize global to 0..1 for blending
            g_norm = normalize01(g_scores)

            combined = (1.0 - beta) * local_s + beta * g_norm
            c_star = int(np.argmax(combined))

            # Expand probability vector if needed
            if P[n].shape[0] != C + 1:
                p_new = np.zeros(C + 1, dtype=float)
                copy_len = min(P[n].shape[0], C)
                p_new[:copy_len] = P[n][:copy_len]
                P[n] = p_new

            # Update probabilities toward chosen action
            P[n] = update_probabilities(P[n], c_star, alpha=alpha_map[n])

            # Update hard label
            prev = hard_labels[n]
            if c_star == new_idx:
                # spawn new label id = C (will be compacted next iter)
                hard_labels[n] = C
            else:
                hard_labels[n] = c_star
            if hard_labels[n] != prev:
                changed += 1

        changed_frac = changed / max(N, 1)
        if changed_frac <= CONVERGENCE_TOL:
            patience -= 1
        else:
            patience = CONVERGENCE_PATIENCE
        if patience <= 0:
            break

    # Final compact relabel
    comms = partition_to_communities(hard_labels)
    hard_labels = communities_to_partition(comms)

    # Soft to overlapping
    memberships = soft_memberships_from_probs(P, tau, delta)

    # Build community -> nodes from memberships
    label_to_nodes = {}
    for n, cs in memberships.items():
        for c in cs:
            label_to_nodes.setdefault(c, set()).add(n)
    communities_overlap = [nodes for _, nodes in sorted(
        label_to_nodes.items(), key=lambda x: x[0])]

    return communities_overlap, memberships, P, hard_labels


# -------------------- Export --------------------
def export_outputs(memberships: Dict[int, Set[int]],
                   communities: List[Set[int]],
                   out_base: Path):
    if SAVE_COMMUNITIES_TXT:
        txt_path = out_base.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for cid, comm in enumerate(communities, 1):
                members = sorted(
                    list(comm), key=lambda x: (isinstance(x, str), x))
                f.write(
                    f"Community {cid} (size={len(members)}): {', '.join(map(str, members))}\n")
        print(f"Communities saved to: {txt_path}")

    if SAVE_MEMBERSHIP_CSV:
        rows = []
        for n, cs in memberships.items():
            rows.append({"node": n,
                         "communities": "[" + ",".join(map(str, sorted(list(cs)))) + "]",
                         "multiplicity": len(cs)})
        df = pd.DataFrame(rows).sort_values(
            by=["multiplicity", "node"], ascending=[False, True])
        csv_path = Path(str(out_base) + "_membership.csv")
        df.to_csv(csv_path, index=False)
        print(f"Memberships (with overlaps) saved to: {csv_path}")


# -------------------- Main --------------------
if __name__ == "__main__":
    np.random.seed(RANDOM_SEED)

    t0 = time.time()
    path = Path(FILE_PATH)
    base = Path(OUT_PREFIX) if OUT_PREFIX else Path(path.stem + "_ACLA_fast")

    df = load_adjacency(path)
    G = build_graph(df, WEIGHT_THRESHOLD, USE_EDGE_WEIGHTS)

    t1 = time.time()
    communities_overlap, memberships, P, hard_labels = acla_fast(G)
    t2 = time.time()

    # Overlap summary
    def overlapping_summary_local(memberships: Dict[int, Set[int]]) -> Tuple[int, int, int]:
        all_c = set()
        overlap_nodes = 0
        comm_has_overlap = {}
        for n, cs in memberships.items():
            for c in cs:
                all_c.add(c)
            if len(cs) > 1:
                overlap_nodes += 1
                for c in cs:
                    comm_has_overlap[c] = True
        overlap_comms = sum(1 for c in all_c if comm_has_overlap.get(c, False))
        return len(all_c), overlap_nodes, overlap_comms

    ncom, n_overlap_nodes, n_overlap_comms = overlapping_summary_local(
        memberships)

    print(f"\nA-CLA (Fast ΔQ) results for {path.name}")
    print(f"  Build graph time: {t1 - t0:.4f}s")
    print(f"  A-CLA iterations time: {t2 - t1:.4f}s")
    print(f"  Total time: {t2 - t0:.4f}s")
    print(f"  Detected communities: {len(communities_overlap)}")
    print(f"  Overlapping nodes: {n_overlap_nodes}")
    print(f"  Overlapping communities: {n_overlap_comms}")

    export_outputs(memberships, communities_overlap, base)
