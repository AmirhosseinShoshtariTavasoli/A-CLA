# QA report

Reconstruction QA performed on 2026-08-14.

## Passed checks

- Maintained package/scripts/tests compile successfully.
- Canonical adjacency-matrix count: 15.
- Historical Python files recovered from the project: 69.
- Historical Python syntax compilation: 69/69 PASS before packaging.
- Test suite: 3/3 PASS using the reconstructed package source.
- Clean non-overlap CLI smoke test on the archived Dolphin matrix: PASS.
- Exploratory overlap CLI smoke test on the archived Dolphin matrix: PASS.
- Dolphin matrix loaded as 62 nodes / 147 edges, matching manuscript Table 5.1.

## Smoke-test observation

The clean non-overlap wrapper produced modularity 0.5352168 on the Dolphin matrix with seed 42 in the reconstruction environment. The published Table 5.3 reports A-CLA mean 0.527 ± 0.011. This difference is consistent with the provenance warning: the paper reports repeated-run means while the clean wrapper is a deterministic maintainable reconstruction of one recovered final script family, not a claim of bit-for-bit regeneration of the paper's 10-run pipeline.

## Environment limitation during QA

An editable `pip install -e .` with build isolation attempted to contact PyPI for build dependencies, but the reconstruction container has no internet access. Tests and CLI execution were therefore run with `PYTHONPATH=src`. The package metadata is standard setuptools/PEP 517 and is intended to install normally in an internet-connected environment.
