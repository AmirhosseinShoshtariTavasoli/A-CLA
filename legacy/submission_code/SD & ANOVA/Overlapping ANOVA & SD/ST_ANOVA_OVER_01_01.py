# --------------------------------------------
# Input:  result.xlsx  (10 runs per dataset × method)
# Output: overlapp_std.xlsx   (mean ± std)
#         anova_overlapp.xlsx (ANOVA + Tukey HSD results)

import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# ===== SETTINGS =====
INPUT_FILE = "statistic.xlsx"
OUT_STD = "overlapp_STD.xlsx"
OUT_ANOVA = "anova_OVERLAPPp.xlsx"

# Method order based on file structure
methods = ["A-CLA", "LE", "CPM", "SLPA", "DEMON", "Leiden"]
# ====================

# --- Load data ---
df = pd.read_excel(INPUT_FILE)

# Expect format: col0 = dataset, next groups of 10 = methods
datasets = df.iloc[:, 0]
data = df.iloc[:, 1:]

# --- Build long-form dataframe ---
records = []
for idx, row in df.iterrows():
    dataset = row.iloc[0]
    for m, method in enumerate(methods):
        cols = row.iloc[1 + m*10: 1 + (m+1)*10].values.astype(float)
        for val in cols:
            records.append(
                {"Dataset": dataset, "Method": method, "Value": val})

df_long = pd.DataFrame(records)

# --- Compute mean & std ---
summary = df_long.groupby(["Dataset", "Method"])[
    "Value"].agg(["mean", "std"]).reset_index()
summary.to_excel(OUT_STD, index=False)
print(f"Saved: {OUT_STD}")

# --- ANOVA + Tukey per dataset ---
anova_results = []
tukey_records = []

for dataset, group in df_long.groupby("Dataset"):
    model = ols("Value ~ C(Method)", data=group).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    anova_results.append((dataset, anova_table))

    # Tukey HSD
    tukey = pairwise_tukeyhsd(group["Value"], group["Method"], alpha=0.05)
    tukey_df = pd.DataFrame(data=tukey.summary(
    ).data[1:], columns=tukey.summary().data[0])
    tukey_df.insert(0, "Dataset", dataset)
    tukey_records.append(tukey_df)

# Combine results
anova_combined = pd.concat(
    [tbl.assign(Dataset=ds) for ds, tbl in anova_results], axis=0
)
anova_combined.reset_index(inplace=True)
anova_combined.rename(columns={"index": "Source"}, inplace=True)

tukey_combined = pd.concat(tukey_records, axis=0)

# Write to Excel
with pd.ExcelWriter(OUT_ANOVA) as writer:
    anova_combined.to_excel(writer, sheet_name="ANOVA", index=False)
    tukey_combined.to_excel(writer, sheet_name="TukeyHSD", index=False)

print(f"Saved: {OUT_ANOVA}")
