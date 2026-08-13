import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ======= SETTINGS (edit these) =======
excel_path = "statistic.xlsx"  # your file
# Use the exact dataset names printed by check_datasets.py
target_datasets = ["Disesome", "Yeast"]  # <-- EDIT if needed
# =====================================

methods_in_order = ["SLPA", "DEMON", "CPM", "A-CLA", "Leiden", "Louvain", "GN"]
block_size = 10

# --- load & reshape to long format: Dataset, Method, Run, Overlaps ---
raw = pd.read_excel(excel_path)
raw.rename(columns={raw.columns[0]: "Dataset"}, inplace=True)

data_cols = list(raw.columns[1:])
num_blocks = len(data_cols) // block_size
data_cols = data_cols[:num_blocks * block_size]  # truncate if extra columns

long_rows = []
for bi in range(min(num_blocks, len(methods_in_order))):
    method = methods_in_order[bi]
    cols = data_cols[bi*block_size: (bi+1)*block_size]
    block = raw[["Dataset"] + cols].copy()
    melted = block.melt(id_vars="Dataset",
                        var_name="RunCol", value_name="Overlaps")
    melted["Run"] = melted.groupby("Dataset").cumcount() % block_size + 1
    melted["Method"] = method
    melted.drop(columns=["RunCol"], inplace=True)
    long_rows.append(melted)

long_df = pd.concat(long_rows, ignore_index=True)
long_df["Dataset"] = long_df["Dataset"].astype(str).str.strip()
long_df["Method"] = long_df["Method"].astype(str).str.strip()
long_df["Overlaps"] = pd.to_numeric(long_df["Overlaps"], errors="coerce")
long_df = long_df.dropna(subset=["Overlaps"])

# --- output folder ---
outdir = Path("figures")
outdir.mkdir(exist_ok=True)

# --- 1) BOX PLOTS: one figure per dataset ---
for ds in target_datasets:
    sub = long_df[long_df["Dataset"] == ds]
    if sub.empty:
        print(f"[skip] dataset not found: {ds}")
        continue
    methods_present = [
        m for m in methods_in_order if m in sub["Method"].unique()]
    data_by_method = [sub[sub["Method"] == m]
                      ["Overlaps"].values for m in methods_present]

    plt.figure(figsize=(10, 6), dpi=300)
    plt.boxplot(data_by_method, labels=methods_present, showmeans=True)
    plt.title(f"Overlapping Communities by Method — {ds}")
    plt.ylabel("Number of Overlapping Communities")
    plt.xlabel("Method")
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    out = outdir / f"boxplot_overlaps_{ds.replace(' ', '_')}.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[saved] {out}")

# --- 2) MEAN ± STD BAR CHARTS: one figure per dataset ---
for ds in target_datasets:
    sub = long_df[long_df["Dataset"] == ds]
    if sub.empty:
        continue
    summary = (sub.groupby("Method")["Overlaps"]
               .agg(['mean', 'std'])
               .reindex(methods_in_order)
               .dropna())
    plt.figure(figsize=(10, 6), dpi=300)
    plt.bar(summary.index, summary["mean"], yerr=summary["std"], capsize=5)
    plt.title(f"Overlapping Communities — Mean ± Std over 10 runs — {ds}")
    plt.ylabel("Number of Overlapping Communities")
    plt.xlabel("Method")
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    out = outdir / f"bar_overlaps_meanstd_{ds.replace(' ', '_')}.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[saved] {out}")
