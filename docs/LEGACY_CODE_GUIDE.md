# Legacy code guide

## `legacy/submission_code/`

Exact copy of the recovered `A-CLA-CODES` directory that also appears inside the final manuscript revision folder. Hash comparison showed that the repeated manuscript-embedded copies are identical to the top-level final code bundle for the major metric/statistical scripts.

Contents include:

- Modularity
- NMI variants
- F1-score
- Edge density and betweenness centrality
- Overlap statistical analysis
- Modularity statistical analysis

Do not edit these files in place.

## `legacy/code_archive/`

Python scripts recovered from the broader historical `Code/` directory, including:

- `A-CLA.01.01.py` / `A-CLA.01.02.py` early probability/entropy variants;
- exploratory overlap scripts;
- community-overlap comparison scripts;
- other development code.

Workbooks referenced by these scripts have been centralized under `data/` and `results/` when practical.

## `legacy/refinement_scripts/`

Later revision-stage comparison and statistical scripts, including Leiden, Leading Eigenvector, CPM, SLPA, DEMON, ANOVA, Tukey HSD, and overlap experiments.

## `legacy/original_archive_inventory.csv`

Inventory of all 253 files in the uploaded historical project archive, including SHA-256 hashes and a note describing whether each file was included in the public repository package or intentionally excluded (for example manuscript drafts and temporary Office files).
