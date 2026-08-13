import pandas as pd
import matplotlib.pyplot as plt

# --- Input Data ---
data = {
    "datasets": ["dolphin", "BoS", "C.elegans", "Candida", "DanioRerio", "Disesome", "karate", "lesmisreable", "netscience", "yeast"],
    "Louvain": [5, 4, 6, 2, 5, 29, 4, 6, 11, 28],
    "Louvain_time": [0.002, 0, 0.024, 0.0075, 0.002, 0.0482, 0, 0.003, 0.0404, 0.2163],
    "GN": [4, 4, 5, 3, 4, 6, 4, 5, 6, 7],
    "GN_time": [0.0986, 4.6285, 11.0795, 4.4395, 1.0591, 44.7748, 0.0085, 0.2001, 8.6599, 77.0901],
    "A-CLA": [0]*10,
    "A-CLA_time": [0.773, 3.1742, 2.87, 3.569, 1.4882, 19.6258, 0.3698, 0.782, 20.9956, 39.6338]
}

df = pd.DataFrame(data)

# --- Bar Chart: Number of Overlapping Communities ---
plt.figure(figsize=(12, 6))
bar_width = 0.25
x = range(len(df["datasets"]))

plt.bar([i - bar_width for i in x], df["Louvain"],
        width=bar_width, label="Louvain")
plt.bar(x, df["GN"], width=bar_width, label="GN")
plt.bar([i + bar_width for i in x], df["A-CLA"],
        width=bar_width, label="A-CLA")

plt.xticks(x, df["datasets"], rotation=45)
plt.ylabel("Number of Overlapping Communities")
plt.title("Overlapping Communities Detected per Dataset")
plt.legend()
plt.tight_layout()
plt.show()

# --- Line Plot: Execution Time Comparison ---
plt.figure(figsize=(12, 6))
plt.plot(df["datasets"], df["Louvain_time"], marker='o', label="Louvain Time")
plt.plot(df["datasets"], df["GN_time"], marker='s', label="GN Time")
plt.plot(df["datasets"], df["A-CLA_time"], marker='^', label="A-CLA Time")

plt.xticks(rotation=45)
plt.ylabel("Execution Time (seconds)")
plt.title("Execution Time of Community Detection Methods")
plt.legend()
plt.tight_layout()
plt.show()
