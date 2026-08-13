# A-CLA algorithm notes

## Published conceptual formulation

The final manuscript describes A-CLA as an extension of Cellular Learning Automata built around three ideas:

1. dual local-global feedback;
2. adaptive learning rates informed by network structure;
3. convergence/stability control.

The article's primary formulation is non-overlapping. It describes node-level automata, action probabilities, local reinforcement, periodic global modularity feedback, and a probability-change convergence condition.

## Recovered implementation families

The historical archive does not contain one monolithic program from which every table and figure was generated. Instead it contains metric-specific and revision-specific scripts.

### Final modularity-oriented implementation

`legacy/submission_code/Modularity/A-CLA.02.01.Modularity.py`

This script produces a hard partition and optimizes modularity using:

- Louvain initialization when `python-louvain` is installed;
- neighbor-label local scores;
- hypothetical modularity-gain global scores;
- a fused local/global decision score;
- a decaying exploration probability;
- early stopping on modularity improvement.

The maintainable version is `src/acla/nonoverlap.py`.

### Earlier probability/entropy implementation

`legacy/code_archive/A-CLA.01.01.py` and `A-CLA.01.02.py`

These scripts use:

- uniform action probabilities;
- reward/penalty probability updates;
- entropy-change convergence;
- an adaptive node learning rate modified by entropy change.

This lineage more closely resembles several equations in the manuscript, but it predates the final benchmark/refinement scripts.

### Exploratory overlap-aware implementation

`legacy/code_archive/Overlap/A-CLA_refin_01_01.py`

This later recovered script uses local feedback, approximate modularity gain, node-specific learning rates based on degree and betweenness, and soft post-processing thresholds for multiple memberships. The final manuscript and R4 reviewer response characterize overlap work as exploratory. The maintainable wrapper is therefore named `src/acla/overlap.py` and is not presented as the primary core algorithm.

## Why both `src/` and `legacy/` exist

`legacy/` answers: **what code survived from the study?**  
`src/` answers: **what code should a researcher run and maintain now?**

The repository does not rewrite the archival scripts to make them appear more internally consistent than they were.
