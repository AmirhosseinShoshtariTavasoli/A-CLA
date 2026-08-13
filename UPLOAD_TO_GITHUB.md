# Uploading this reconstructed repository to GitHub

The contents of this folder are intended to replace the sparse root of `AmirhosseinShoshtariTavasoli/A-CLA`.

## Recommended method: Git

1. Back up the existing repository or create a branch.
2. Clone the repository.
3. Copy **the contents of this folder** into the repository root (not the outer folder itself).
4. Review `docs/PROVENANCE_AND_KNOWN_LIMITATIONS.md`.
5. Run `python scripts/validate_repository.py` and `pytest -q`.
6. Commit and push.

Example:

```bash
git clone https://github.com/AmirhosseinShoshtariTavasoli/A-CLA.git
cd A-CLA
# copy reconstructed files here
git add .
git commit -m "Complete publication reproducibility repository"
git push
```

## GitHub web upload

GitHub's browser uploader can be used, but the repository contains many files and a ~38 MB adjacency workbook, so Git is more reliable. No individual file in this package is intentionally above GitHub's normal 100 MB single-file limit.

## Do not upload the outer ZIP

Upload/extract the repository files themselves so `README.md`, `src/`, `data/`, etc. appear directly at the repository root.
