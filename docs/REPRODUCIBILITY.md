# Reproducibility guide

## Scope

This repository supports two levels of reproducibility:

1. **archival reproducibility** — preservation of the historical code, matrices, outputs, and parameters used during article development;
2. **maintainable reruns** — a clean Python package for executing the recovered non-overlapping and exploratory overlap-aware variants on archived adjacency matrices.

Exact bit-for-bit reproduction of every published table is **not claimed** because the recovered project contains multiple metric-specific implementations and some final manuscript statements are not uniquely tied to one executable script. Those cases are documented in `PROVENANCE_AND_KNOWN_LIMITATIONS.md`.

## Environment

Recommended:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .
pip install -r requirements-full.txt
```

The full environment includes packages required by historical comparison scripts: `python-louvain`, `python-igraph`, `leidenalg`, and `cdlib`.

## Clean smoke test

```bash
python -m acla --input data/adjacency_matrices/adjacency_matrix_Dolphin_output.xlsx --mode nonoverlap --seed 42
```

Then run:

```bash
pytest -q
python scripts/validate_repository.py
```

## Paper-level design recovered from the final manuscript

- repeated runs: 10;
- iteration range: 100-1000;
- initial learning-rate range: 0.01-0.2;
- reported error bars: standard deviation over the repeated runs.

These paper-level ranges are stored in `configs/paper_experiment.json`. They should not be confused with the fixed defaults in individual recovered scripts, which often reflect one selected configuration.

## Historical experiment scripts

For maximal historical fidelity, run files from `legacy/submission_code/` from a working directory that contains the adjacency workbook named inside each script. Many historical scripts use hard-coded filenames. Rather than rewriting those files, they remain unchanged and are documented in `LEGACY_CODE_GUIDE.md`.

## Reference outputs

Historical workbooks and generated CSV/PNG outputs are under `results/reference_archive/`. Machine-readable transcriptions of final manuscript tables are under `results/published_tables/`.

## Recommended reproduction workflow

1. Start with Dolphin or Karate Club for a fast smoke test.
2. Confirm the exact experiment and script in `PAPER_RESULTS_MAP.md`.
3. Use the clean wrapper for maintainable reruns, or the legacy script for historical behavior.
4. Record package versions, seed, matrix filename, and parameters.
5. Treat differences from the published value as a provenance question before changing the algorithm.
