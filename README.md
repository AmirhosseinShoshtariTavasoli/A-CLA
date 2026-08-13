# A-CLA: Adaptive Cellular Learning Automata for Community Detection

This repository is the reproducibility and archival code package for:

**A-CLA: A Novel Adaptive Cellular Learning Automata Approach for Uncovering Communities in Complex Networks**  
Amirhossein Fathinavid and Amirhossein Shoshtari Tavasoli  
*Computer Networks*, Volume 278, Article 112103 (2026)  
DOI: https://doi.org/10.1016/j.comnet.2026.112103

A-CLA is a Cellular Learning Automata (CLA)-based community-detection framework developed around adaptive update behavior and local/global structural feedback. The published article evaluates the method using modularity, normalized mutual information (NMI), F1-score, edge density, betweenness centrality, convergence behavior, and statistical analyses across social, biological, and technological networks.

## Repository status

This package was reconstructed from the authors' historical project archive and the code bundle that accompanied the final manuscript revisions. It deliberately separates:

- **clean reference code** in `src/acla/`;
- **paper-facing experiment material** in `experiments/` and `results/`;
- **archived benchmark matrices** in `data/`;
- **exact historical scripts** in `legacy/`;
- **provenance and known discrepancies** in `docs/`.

The historical project contains several generations of A-CLA code. They are preserved rather than silently overwritten. The article's final framing treats the core method as **non-overlapping**; overlap-oriented experiments are retained as an **exploratory extension**, not as a replacement for the published core formulation. See `docs/PROVENANCE_AND_KNOWN_LIMITATIONS.md` before attempting exact numerical reproduction.

## Quick start

### 1. Create an environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -e .
```

For the full historical benchmark stack, including Leiden/CDlib scripts:

```bash
pip install -r requirements-full.txt
```

### 2. Run the clean non-overlapping reference implementation

```bash
python -m acla \
  --input data/adjacency_matrices/adjacency_matrix_Dolphin_output.xlsx \
  --mode nonoverlap \
  --iterations 200 \
  --seed 42
```

On Windows PowerShell, put the command on one line or replace `\` with PowerShell continuation characters.

### 3. Run the exploratory overlap-aware extension

```bash
python -m acla \
  --input data/adjacency_matrices/adjacency_matrix_Dolphin_output.xlsx \
  --mode overlap \
  --iterations 100 \
  --seed 42
```

### 4. Validate the repository

```bash
python scripts/validate_repository.py
pytest -q
```

## Repository layout

```text
A-CLA/
├── README.md
├── CITATION.cff
├── CITATION.bib
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── requirements-full.txt
├── environment.yml
├── configs/
├── data/
│   ├── adjacency_matrices/
│   └── network_tables/
├── docs/
├── examples/
├── experiments/
├── results/
│   ├── published_tables/
│   └── reference_archive/
├── scripts/
├── src/acla/
├── tests/
└── legacy/
```

## What is considered authoritative?

For **publication claims and reported numerical values**, the published article is authoritative. For **historical implementation provenance**, files under `legacy/submission_code/` and `legacy/code_archive/` are authoritative snapshots of the recovered project. The cleaned `src/acla/` package is a maintainable reference implementation derived from those materials; it is not presented as proof that every number in the paper can be regenerated bit-for-bit from one single script.

## Datasets

Fifteen adjacency matrices matching the networks listed in Table 5.1 of the final manuscript are archived under `data/adjacency_matrices/`. The paper abstract states sixteen networks, while Table 5.1 enumerates fifteen; this discrepancy is documented rather than silently changed. See `docs/DATASETS.md`.

## Reproducing paper analyses

Start with:

- `docs/REPRODUCIBILITY.md`
- `docs/PAPER_RESULTS_MAP.md`
- `configs/paper_experiment.json`
- `results/published_tables/`

Exact historical scripts are preserved under `legacy/`, including the final code bundle supplied with the revised manuscript.

## Citation

If you use A-CLA, cite the published article. Citation files are provided as `CITATION.cff` and `CITATION.bib`.

## License

The historical repository did not contain a formal open-source license. Accordingly, this reconstruction does **not** assert an OSI-approved software license. See `LICENSE` for the repository's rights notice and contact the copyright holders if broader reuse or redistribution permission is required.

## Contact

Repository maintained for research transparency and reproducibility. For article-related questions, please contact the authors through the publication or GitHub repository.
