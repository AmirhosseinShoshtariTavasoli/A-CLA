import pandas as pd
import numpy as np
from scipy.stats import ttest_rel

# ===================== SETTINGS =====================
excel_path = "statistic.xlsx"   # your file
methods_in_order = ["SLPA", "DEMON", "CPM", "A-CLA", "Leiden", "Louvain", "GN"]
block_size = 10                 # 10 columns per method
datasets_of_interest = ["Yeast", "Disesome"]  # change/add as needed
# ====================================================

# Load
df_raw = pd.read_excel(excel_path)
# Normalize first column name to "Dataset"
df_raw.rename(columns={df_raw.columns[0]: "Dataset"}, inplace=True)

# Identify the data columns after "Dataset"
all_cols = list(df_raw.columns)
data_cols = all_cols[1:]  # everything after 'Dataset'

# Sanity-check: number of columns should be multiple of block_size
if len(data_cols) % block_size != 0:
    raise ValueError(
        f"Expected data columns to be a multiple of {block_size}, got {len(data_cols)}.")

# Sanity-check: number of method blocks should match methods_in_order length
num_blocks = len(data_cols) // block_size
if num_blocks != len(methods_in_order):
    raise ValueError(
        f"Expected {len(methods_in_order)} method blocks, found {num_blocks} blocks in file.")

# Build long-form table: Dataset, Method, Run, Overlaps
long_rows = []
for bi in range(num_blocks):
    method = methods_in_order[bi]
    # columns for this method
    start = bi * block_size
    stop = start + block_size
    cols = data_cols[start:stop]
    # Extract this block as (Dataset + 10 run columns)
    block = df_raw[["Dataset"] + cols].copy()
    # Melt to long
    block_long = block.melt(
        id_vars="Dataset", var_name="RunCol", value_name="Overlaps")
    # Assign method and run index 1..block_size
    # Derive run index from column order
    # Map original column -> run index
    col_to_run = {c: (i + 1) for i, c in enumerate(cols)}
    block_long["Run"] = block_long["RunCol"].map(col_to_run)
    block_long["Method"] = method
    block_long.drop(columns=["RunCol"], inplace=True)
    long_rows.append(block_long)

long_df = pd.concat(long_rows, ignore_index=True)

# Clean dataset names (optional standardization)
long_df["Dataset"] = long_df["Dataset"].astype(str).str.strip()

# ---- Summary: mean ± std per dataset × method ----
summary = (long_df
           .groupby(["Dataset", "Method"], as_index=False)["Overlaps"]
           .agg(mean="mean", std="std", n="count"))
# should be number_of_rows_per_dataset = 10
summary["runs_per_method"] = summary["n"]
summary = summary.drop(columns=["n"])

print("\n=== Summary (mean ± std) per Dataset × Method ===")
print(summary.to_string(index=False))

# Save summaries
summary.to_csv("overlap_summary_mean_std.csv", index=False)
long_df.to_csv("overlap_long_table.csv", index=False)
print("\nSaved: overlap_summary_mean_std.csv, overlap_long_table.csv")

# ---- Optional: paired t-tests A-CLA vs SLPA and A-CLA vs Leiden on selected datasets ----


def paired_t(acla_vals, baseline_vals):
    """Return (t, p) for paired t-test; if lengths differ, align by run index."""
    a = np.array(acla_vals, dtype=float)
    b = np.array(baseline_vals, dtype=float)
    # Require same length and paired by run index:
    n = min(len(a), len(b))
    a = a[:n]
    b = b[:n]
    t, p = ttest_rel(a, b)
    return t, p, n, a.mean(), b.mean(), a.std(ddof=1), b.std(ddof=1)


print("\n=== Paired t-tests: A-CLA vs baselines on selected datasets ===")
tests_rows = []
for ds in datasets_of_interest:
    for baseline in ["SLPA", "Leiden"]:
        acla_vals = long_df[(long_df["Dataset"] == ds) & (
            long_df["Method"] == "A-CLA")].sort_values("Run")["Overlaps"].values
        base_vals = long_df[(long_df["Dataset"] == ds) & (
            long_df["Method"] == baseline)].sort_values("Run")["Overlaps"].values
        if len(acla_vals) == 0 or len(base_vals) == 0:
            print(f"- Skipping {ds}: missing values for {baseline} or A-CLA")
            continue
        t, p, n, ma, mb, sa, sb = paired_t(acla_vals, base_vals)
        tests_rows.append({
            "Dataset": ds,
            "Comparison": f"A-CLA vs {baseline}",
            "n_runs": n,
            "A-CLA_mean": round(ma, 3),
            f"{baseline}_mean": round(mb, 3),
            "A-CLA_std": round(sa, 3),
            f"{baseline}_std": round(sb, 3),
            "t_stat": round(t, 3),
            "p_value": p
        })
        print(f"- {ds}: A-CLA vs {baseline} → t={t:.3f}, p={p:.4f} | "
              f"means {ma:.2f} vs {mb:.2f} (n={n})")

if tests_rows:
    tests_df = pd.DataFrame(tests_rows)
    tests_df.to_csv("overlap_paired_ttests.csv", index=False)
    print("\nSaved: overlap_paired_ttests.csv")
else:
    print("No tests performed (check dataset names and methods).")
