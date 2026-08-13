#!/usr/bin/env python3
# A-CLA (Refined): Adaptive Cellular Learning Automata for (overlapping) community detection
# - Dual feedback: local neighbor agreement + global modularity gain (approx.)
# - Adaptive learning rate per node (degree & betweenness)
# - Soft probabilities -> overlapping memberships (tau/delta)
# - Reproducible, with convergence checks & timing
#
# Deps: pandas, networkx, numpy

import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.community.quality import modularity as nx_modularity

# ===================== SETTINGS =====================
# <-- your Excel/CSV adjacency
FILE_PATH = "adjacency_matrix_Diseasome_output.xlsx"
RANDOM_SEED = 42

# Graph handling
WEIGHT_THRESHOLD = None    # None => use >0 weights as is; or set a number to binarize
USE_EDGE_WEIGHTS = True    # use 'weight' in local/global feedback

# A-CLA core
MAX_ITERS = 300
ALPHA_MIN, ALPHA_MAX = 0.03, 0.25          # adaptive LR bounds
ALPHA_BASE, ALPHA_DEG, ALPHA_BC = 0.03, 0.12, 0.10  # LR shaping
BETA_GLOBAL = 0.35                          # blend: 0=only local, 1=only global
# penalty to discourage trivial new communities
NEW_COMM_PENALTY = 0.05
# fraction of nodes allowed to change per iter
CONVERGENCE_TOL = 0.01
CONVERGENCE_PATIENCE = 8

# Overlap post-processing thresholds
TAU = 0.30        # absolute prob threshold
DELTA = 0.05      # within DELTA of node max prob

# Export
SAVE_COMMUNITIES_TXT = True
SAVE_MEMBERSHIP_CSV = True
OUT_PREFIX = None  # None => derived from file; or set e.g. "Celegans_ACLA"
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
            raise ValueError("Row/column labels must match (same nodes).")
    return df


def build_graph(df: pd.DataFrame, thr: Optional[float], use_weights: bool) -> nx.Graph:
    A = df.copy()
    if thr is None:
        A = A.where(A > 0, 0.0)
    else:
        A = (A >= thr).astype(float)
    # symmetrize
    if not A.equals(A.T):
        A = (A + A.T) / 2.0
    G = nx.from_pandas_adjacency(A)
    G.remove_edges_from(nx.selfloop_edges(G))
    if not use_weights:
        # strip weights to 1
        for u, v, d in G.edges(data=True):
            d["weight"] = 1.0
    else:
        # ensure weight exists
        for u, v, d in G.edges(data=True):
            d["weight"] = float(d.get("weight", 1.0))
    return G


# --------------- Helpers: partition & modularity ---------------
def partition_to_communities(part: Dict) -> List[Set]:
    byc: Dict[int, Set] = {}
    for n, cid in part.items():
        byc.setdefault(cid, set()).add(n)
    # remove empties
    return [c for c in byc.values() if len(c) > 0]


def communities_to_partition(communities: List[Set]) -> Dict:
    part = {}
    for cid, comm in enumerate(communities):
        for n in comm:
            part[n] = cid
    return part


def modularity_of_partition(G: nx.Graph, part: Dict) -> float:
    comms = partition_to_communities(part)
    return nx_modularity(G, comms, weight="weight")


# --------------- A-CLA Core Components ---------------
def normalize01(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return arr
    a, b = np.min(arr), np.max(arr)
    if b - a < 1e-12:
        return np.zeros_like(arr)
    return (arr - a) / (b - a)


def adaptive_alpha(G: nx.Graph) -> Dict:
    degs = dict(G.degree(weight="weight" if USE_EDGE_WEIGHTS else None))
    max_deg = max(degs.values()) if degs else 1.0
    bc = nx.betweenness_centrality(
        G, weight="weight" if USE_EDGE_WEIGHTS else None, normalized=True)
    deg_arr = np.array([degs[n] for n in G.nodes()], dtype=float)
    bc_arr = np.array([bc[n] for n in G.nodes()], dtype=float)
    deg_norm = deg_arr / (max_deg if max_deg > 0 else 1.0)
    bc_norm = (bc_arr - bc_arr.min()) / (bc_arr.max() - bc_arr.min() + 1e-12)
    alpha = ALPHA_BASE + ALPHA_DEG * deg_norm + ALPHA_BC * bc_norm
    alpha = np.clip(alpha, ALPHA_MIN, ALPHA_MAX)
    return {n: float(a) for n, a in zip(G.nodes(), alpha)}


def local_feedback_scores(G: nx.Graph, node: int, hard_labels: Dict[int, int], C: int) -> np.ndarray:
    """Fraction of neighbor weight in each community."""
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


def approx_global_gain(G: nx.Graph, hard_labels: Dict[int, int], node: int, C: int, current_Q: float) -> np.ndarray:
    """Approximate ΔQ if node is placed in each community (recompute modularity partition-wise).
       This is O(C) modularity evals per node; fine for your dataset sizes."""
    gains = np.zeros(C, dtype=float)
    base_c = hard_labels[node]
    # Build current communities list quickly
    communities = partition_to_communities(hard_labels)
    # Ensure indices align 0..C-1
    # For each candidate c: move node -> c (if not already), recompute modularity
    for c in range(C):
        if c == base_c:
            gains[c] = 0.0
            continue
        # Copy partition mapping
        part2 = dict(hard_labels)
        part2[node] = c
        Q2 = modularity_of_partition(G, part2)
        gains[c] = Q2 - current_Q
    # Also provide an option for "new community": index C (handled outside by penalty)
    return gains


def choose_with_dual_feedback(local_s: np.ndarray, global_g: np.ndarray, beta: float, allow_new: bool) -> int:
    """Combine local (0..1) & global gains (can be negative) and choose argmax."""
    # Normalize global to 0..1 (shift + scale)
    g_pos = global_g.copy()
    if g_pos.size:
        g_pos = normalize01(g_pos)
    combined = (1.0 - beta) * local_s + beta * g_pos
    # argmax community
    return int(np.argmax(combined)) if combined.size else 0


def update_probabilities(p: np.ndarray, action_idx: int, alpha: float) -> np.ndarray:
    """Linear reward-inaction style update toward one-hot(action_idx)."""
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


# --------------- A-CLA Main ---------------
def acla_refined(G: nx.Graph,
                 max_iters=MAX_ITERS,
                 beta=BETA_GLOBAL,
                 tau=TAU,
                 delta=DELTA,
                 new_comm_penalty=NEW_COMM_PENALTY) -> Tuple[List[Set], Dict[int, Set[int]], Dict[int, np.ndarray], Dict[int, int]]:

    rng = np.random.default_rng(RANDOM_SEED)
    nodes = list(G.nodes())
    N = len(nodes)

    # Initial hard labels: each node is its own community
    hard_labels = {n: i for i, n in enumerate(nodes)}
    C = N

    # Probability vectors per node (start one-hot at own label)
    # large dims, but fine for N<=few hundred
    P = {n: np.eye(1, C, k=hard_labels[n]).ravel() for n in nodes}

    # Precompute adaptive alphas
    alpha_map = adaptive_alpha(G)

    # Convergence tracking
    patience = CONVERGENCE_PATIENCE
    prev_changed_frac = 1.0

    for it in range(1, max_iters + 1):
        # compact community ids (remove empty labels)
        comms = partition_to_communities(hard_labels)
        C = len(comms)
        # relabel to 0..C-1
        hard_labels = communities_to_partition(comms)

        # current modularity
        Q = modularity_of_partition(G, hard_labels)

        changed = 0

        for n in nodes:
            # local feedback over existing C communities
            local_s = local_feedback_scores(G, n, hard_labels, C)  # shape (C,)

            # global gain approx for each community
            global_g = approx_global_gain(G, hard_labels, n, C, Q)

            # Option to spawn a new community: treat as extra index with penalty
            allow_new = True
            if allow_new:
                # score for new community via small constant; global gain unknown; discourage a bit
                local_s = np.append(local_s, NEW_COMM_PENALTY)
                # neutral gain (or small negative)
                global_g = np.append(global_g, 0.0)
                C_plus = C + 1
            else:
                C_plus = C

            # choose action
            c_star = choose_with_dual_feedback(
                local_s, global_g, beta=beta, allow_new=allow_new)

            # If chosen "new community", assign new label id = C
            if c_star == C and allow_new:
                # add a fresh community id
                # Reuse next integer label (implicitly handled when we rebuild mapping next iter)
                target_label = max(hard_labels.values()) + 1
            else:
                # map c_star (0..C-1) to actual label id in current mapping
                # Since we relabeled compactly, label == index
                target_label = c_star

            # probability update
            p_vec = P[n]
            # Resize probability vector if communities changed
            if p_vec.shape[0] != C_plus:
                new_vec = np.zeros(C_plus, dtype=float)
                new_vec[:min(p_vec.shape[0], C)
                        ] = p_vec[:min(p_vec.shape[0], C)]
                p_vec = new_vec
            P[n] = update_probabilities(p_vec, c_star, alpha=alpha_map[n])

            # hard label = argmax
            prev_label = hard_labels[n]
            hard_labels[n] = target_label
            if hard_labels[n] != prev_label:
                changed += 1

        changed_frac = changed / max(N, 1)
        if changed_frac <= CONVERGENCE_TOL:
            patience -= 1
        else:
            patience = CONVERGENCE_PATIENCE

        if patience <= 0:
            break
        prev_changed_frac = changed_frac

    # Final compact relabel
    comms = partition_to_communities(hard_labels)
    hard_labels = communities_to_partition(comms)

    # Soft to overlapping memberships
    memberships = soft_memberships_from_probs(P, tau, delta)

    # Build outputs
    communities_overlap = []
    # Convert overlapping memberships into overlapping communities (set union per label)
    label_to_nodes: Dict[int, Set[int]] = {}
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
    base = Path(OUT_PREFIX) if OUT_PREFIX else Path(
        path.stem + "_ACLA_refined")

    df = load_adjacency(path)
    G = build_graph(df, WEIGHT_THRESHOLD, USE_EDGE_WEIGHTS)

    t1 = time.time()
    communities_overlap, memberships, P, hard_labels = acla_refined(G)
    t2 = time.time()

    ncom, n_overlap_nodes, n_overlap_comms = overlapping_summary(memberships)

    print(f"\nA-CLA (Refined) results for {path.name}")
    print(f"  Build graph time: {t1 - t0:.4f}s")
    print(f"  A-CLA iterations time: {t2 - t1:.4f}s")
    print(f"  Total time: {t2 - t0:.4f}s")
    print(f"  Detected communities: {len(communities_overlap)}")
    print(f"  Overlapping nodes: {n_overlap_nodes}")
    print(f"  Overlapping communities: {n_overlap_comms}")

    export_outputs(memberships, communities_overlap, base)
