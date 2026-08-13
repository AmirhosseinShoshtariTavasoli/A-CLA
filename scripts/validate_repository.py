from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]
required = [
    "README.md", "CITATION.cff", "CITATION.bib", "LICENSE", "pyproject.toml",
    "configs/paper_experiment.json", "docs/PROVENANCE_AND_KNOWN_LIMITATIONS.md",
    "data/adjacency_matrices/adjacency_matrix_Dolphin_output.xlsx",
    "legacy/submission_code/Modularity/A-CLA.02.01.Modularity.py",
    "results/published_tables/table_5_3_modularity.csv",
]
errors = []
for rel in required:
    if not (ROOT / rel).exists():
        errors.append(f"missing: {rel}")

python_files = list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "tests").rglob("*.py"))
for path in python_files:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"compile failure: {path.relative_to(ROOT)}: {exc}")

matrices = list((ROOT / "data" / "adjacency_matrices").glob("*.xlsx"))
if len(matrices) != 15:
    errors.append(f"expected 15 canonical adjacency matrices, found {len(matrices)}")

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print(f"VALIDATION PASS: {len(python_files)} maintained Python files compile; {len(matrices)} canonical adjacency matrices present.")
