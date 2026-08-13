# Provenance and known limitations

This file is intentionally explicit. A reproducibility repository is stronger when it documents uncertainty rather than retroactively making the historical project look cleaner than it was.

## 1. Multiple A-CLA implementations survived

The archive contains early entropy/probability versions, final modularity-oriented code, metric-specific implementations, and later refinement/overlap scripts. There is no single recovered executable that can be proven to have generated every number in the final paper.

## 2. Non-overlapping core versus overlap experiments

The final published framing describes A-CLA as a **non-overlapping** community-detection framework and treats overlap-aware work as a direction/extension. The R4 reviewer-response material also explicitly characterizes overlapping experiments as exploratory. Therefore:

- `src/acla/nonoverlap.py` is the primary reference path;
- `src/acla/overlap.py` is clearly labeled an exploratory extension;
- historical overlap scripts are preserved but are not used to redefine the core method.

## 3. Manuscript initialization versus recovered modularity code

The manuscript pseudocode describes equal initial action probabilities. The recovered final modularity script (`A-CLA.02.01.Modularity.py`) instead initializes the hard partition with Louvain when available. This is a material implementation-description difference. It is not silently "fixed" in the archival copy.

## 4. Adaptive-rate formulation differs across scripts

The manuscript discusses node-specific adaptation informed by degree, density, and betweenness centrality. The recovered overlap-refinement script computes node-specific alpha from degree and betweenness; the recovered final modularity script uses a global decaying exploration alpha. Earlier probability-based scripts adapt alpha through entropy change. These lineages should not be conflated.

## 5. F1 historical script is not a safe ground-truth reproduction

The final code bundle's F1 script creates an even/odd node split as a placeholder "ground truth" for the loaded graph. That is not sufficient evidence for the ground-truth F1 claims in the paper. The script is preserved for provenance, but this repository does **not** present it as an authoritative exact regeneration of Figure 5.6.

## 6. NMI semantics are ambiguous in surviving scripts

Several NMI scripts compute NMI between A-CLA and other detected partitions (Louvain, GN, Label Propagation, Leading Eigenvector), while the manuscript describes NMI against ground-truth partitions and names A-CLA-baseline variants. Because the archival linkage is not unique, the published table is transcribed separately and the historical scripts remain unchanged.

## 7. Edge-density and centrality script behavior

The recovered combined ED/BC script computes whole-graph density and standard NetworkX betweenness centrality after running A-CLA, rather than clearly calculating community-conditioned metrics. The manuscript describes community edge density and method-specific top-node centrality values. The surviving script therefore supports provenance but not an unquestioned exact methodological equivalence.

## 8. Dataset-count discrepancy

The final manuscript abstract says sixteen networks. Table 5.1 lists fifteen, and the canonical recovered adjacency directory contains fifteen matrices. This repository reports both facts and does not invent a sixteenth network.

## 9. Karate Club preprocessing

Table 5.1 reports Karate Club as 30 nodes / 57 edges, whereas the commonly used Zachary graph has different canonical counts. The archived A-CLA matrix should be used for paper-oriented reproduction.

## 10. Repeated runs and random seeds

The manuscript states 10 independent runs with different random seeds and error bars as standard deviation. The recovered scripts often contain a single fixed seed (`42`), no explicit seed, or metric-specific random behavior. The paper-level design is preserved in `configs/paper_experiment.json`; exact original seed lists were not recovered.

## 11. Historical code quality

All recovered `.py` files in the source archive passed Python syntax compilation during repository reconstruction. This does **not** imply that every script executes successfully without placing the exact expected workbook in its working directory or installing optional packages.

## 12. Publisher PDF not redistributed

The journal-formatted article PDF is not bundled in this software repository. The DOI and citation metadata point to the official publication. This avoids making assumptions about publisher redistribution rights.
