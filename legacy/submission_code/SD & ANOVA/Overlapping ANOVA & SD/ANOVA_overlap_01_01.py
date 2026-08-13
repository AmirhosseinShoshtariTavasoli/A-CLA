# anova_overlap_robust.py
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scipy.stats import ttest_ind

LONG_CSV = "overlap_long_table.csv"   # from the previous step

df = pd.read_csv(LONG_CSV)
# Basic cleaning
df = df.dropna(subset=["Dataset", "Method", "Overlaps"])
df["Method"] = df["Method"].astype(str).str.strip()
df["Dataset"] = df["Dataset"].astype(str).str.strip()
df["Overlaps"] = pd.to_numeric(df["Overlaps"], errors="coerce")
df = df.dropna(subset=["Overlaps"])

datasets = sorted(df["Dataset"].unique())

anova_rows = []
tukey_rows = []
fallback_rows = []

for ds in datasets:
    sub = df[df["Dataset"] == ds].copy()

    # Ensure we actually have multiple methods and enough observations
    method_counts = sub.groupby(
        "Method")["Overlaps"].count().sort_values(ascending=False)
    methods_ok = method_counts[method_counts >=
                               2].index.tolist()  # keep methods with >=2 obs
    sub = sub[sub["Method"].isin(methods_ok)]

    unique_methods = sorted(sub["Method"].unique())
    print(f"\n=== Dataset: {ds} ===")
    print("Methods present & counts:\n", method_counts)

    if len(unique_methods) >= 3:
        # One-way ANOVA
        try:
            model = ols("Overlaps ~ C(Method)", data=sub).fit()
            anova_tab = sm.stats.anova_lm(model, typ=2)
            print("\nANOVA table:\n", anova_tab)

            anova_rows.append({
                "Dataset": ds,
                "df_Method": anova_tab.loc["C(Method)", "df"] if "C(Method)" in anova_tab.index else np.nan,
                "df_Residual": anova_tab.loc["Residual", "df"] if "Residual" in anova_tab.index else np.nan,
                "F": anova_tab.loc["C(Method)", "F"] if "C(Method)" in anova_tab.index else np.nan,
                "p_value": anova_tab.loc["C(Method)", "PR(>F)"] if "C(Method)" in anova_tab.index else np.nan,
            })

            # Tukey HSD post-hoc
            tukey = pairwise_tukeyhsd(
                endog=sub["Overlaps"], groups=sub["Method"], alpha=0.05)
            # Convert Tukey summary to rows
            tk_df = pd.DataFrame(data=tukey.summary(
            ).data[1:], columns=tukey.summary().data[0])
            tk_df.insert(0, "Dataset", ds)
            tukey_rows.append(tk_df)

        except Exception as e:
            print("ANOVA failed:", e)
            # Fall back to pairwise t-tests among methods present
            for i in range(len(unique_methods)):
                for j in range(i+1, len(unique_methods)):
                    m1, m2 = unique_methods[i], unique_methods[j]
                    v1 = sub[sub["Method"] == m1]["Overlaps"].values
                    v2 = sub[sub["Method"] == m2]["Overlaps"].values
                    if len(v1) >= 2 and len(v2) >= 2:
                        t, p = ttest_ind(v1, v2, equal_var=False)  # Welch
                        fallback_rows.append({
                            "Dataset": ds, "Comparison": f"{m1} vs {m2}",
                            "t_stat": round(t, 3), "p_value": p,
                            f"{m1}_mean": round(v1.mean(), 3),
                            f"{m2}_mean": round(v2.mean(), 3),
                            f"{m1}_std": round(v1.std(ddof=1), 3),
                            f"{m2}_std": round(v2.std(ddof=1), 3),
                            "note": "Fallback Welch t-test (ANOVA failed)"
                        })
    elif len(unique_methods) == 2:
        # Only two methods—use t-test directly
        m1, m2 = unique_methods
        v1 = sub[sub["Method"] == m1]["Overlaps"].values
        v2 = sub[sub["Method"] == m2]["Overlaps"].values
        if len(v1) >= 2 and len(v2) >= 2:
            t, p = ttest_ind(v1, v2, equal_var=False)  # Welch
            fallback_rows.append({
                "Dataset": ds, "Comparison": f"{m1} vs {m2}",
                "t_stat": round(t, 3), "p_value": p,
                f"{m1}_mean": round(v1.mean(), 3),
                f"{m2}_mean": round(v2.mean(), 3),
                f"{m1}_std": round(v1.std(ddof=1), 3),
                f"{m2}_std": round(v2.std(ddof=1), 3),
                "note": "Welch t-test (only 2 methods)"
            })
        else:
            print("Not enough observations for t-test.")
    else:
        print("Not enough methods for any test.")

# Save outputs
if anova_rows:
    pd.DataFrame(anova_rows).to_csv("anova_overlaps_summary.csv", index=False)
    print("\nSaved: anova_overlaps_summary.csv")
if tukey_rows:
    pd.concat(tukey_rows, ignore_index=True).to_csv(
        "anova_tukey_overlaps.csv", index=False)
    print("Saved: anova_tukey_overlaps.csv")
if fallback_rows:
    pd.DataFrame(fallback_rows).to_csv(
        "anova_fallback_pairwise.csv", index=False)
    print("Saved: anova_fallback_pairwise.csv")

print("\nDone.")
