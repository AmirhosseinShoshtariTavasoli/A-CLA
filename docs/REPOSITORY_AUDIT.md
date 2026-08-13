# Repository reconstruction audit

Reconstruction date: **2026-08-14**

## Inputs used

- historical `A-CLA.zip` project archive;
- current GitHub repository structure and README;
- final R4 manuscript PDF supplied by the author;
- published article metadata (Computer Networks, volume 278, article 112103, DOI 10.1016/j.comnet.2026.112103).

## Historical archive inventory

- total files: 253;
- Python files: 69;
- unique Python contents by SHA-256: 47;
- all 69 historical Python files passed syntax compilation in the reconstruction environment;
- the historical archive includes datasets, adjacency matrices, result workbooks, statistical outputs, manuscript revisions, reviewer responses, and development variants.

## Current GitHub before reconstruction

The repository root contained only:

- `README.md`;
- `A-CLA-CODES/`.

The old README still described the manuscript as submitted and referenced a missing `requirements.txt`.

## Public-package decisions

Included:

- canonical benchmark matrices;
- node/edge-format workbooks needed by historical code;
- original result workbooks and refinement outputs;
- final manuscript code bundle;
- all distinct historical Python development scripts;
- clean package, tests, configs, reproducibility documentation, publication table transcriptions, and provenance inventory.

Excluded from the GitHub-ready package:

- manuscript DOCX drafts;
- reviewer-response DOCX files;
- EndNote databases;
- Office lock/temp files;
- duplicated copies of the same code embedded in manuscript revision directories;
- journal PDF.

These exclusions reduce clutter and avoid publishing editorial/private workflow material while preserving a SHA-256 inventory of the original archive.
