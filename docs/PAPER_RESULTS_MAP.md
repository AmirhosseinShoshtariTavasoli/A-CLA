# Paper-to-repository results map

This map links the final manuscript's main experiments to the strongest recovered repository evidence.

| Paper item | Topic | Main repository material | Confidence |
|---|---|---|---|
| Table 5.1 | Dataset nodes/edges | `results/published_tables/table_5_1_dataset_features.csv`, `data/adjacency_matrices/` | High |
| Section 5.2 / Table 5.2 | Exploratory overlap comparison | `results/reference_archive/overlap_refinement/`, `legacy/refinement_scripts/overlap/`, `legacy/code_archive/Overlap/` | Medium |
| Table 5.3 / Fig. 5.4 | Modularity | `legacy/submission_code/Modularity/A-CLA.02.01.Modularity.py`, `results/reference_archive/modularity_refinement/`, `table_5_3_modularity.csv` | High for archived code/results; medium for exact rerun linkage |
| Table 5.4 | NMI | `legacy/submission_code/NMI/`, `results/reference_archive/original_results/02-NMI.xlsx`, `table_5_4_nmi.csv` | Medium |
| Fig. 5.6 | F1-score | `legacy/submission_code/F1-Score/`, `results/reference_archive/original_results/03-F1-Scor.xlsx` | Medium-low; see provenance note |
| Table 5.5 / Fig. 5.10 | Edge density | `legacy/submission_code/Eadge density & Betweenness centrality/`, `04-Edge Densit.xlsx`, `table_5_5_edge_density.csv` | Medium |
| Table 5.6 | Betweenness centrality | same ED/BC script, `05-Betweenness Centrality.xlsx`, `table_5_6_betweenness_centrality.csv` | Medium |
| Fig. 5.11 | CLA/CLACD/A-CLA convergence | `results/reference_archive/convergence/Convergence_Data_for_CLA_Variants.csv` | Medium |
| Sec. 5.9.1 | Overlap ANOVA/Tukey/statistics | `legacy/submission_code/SD & ANOVA/Overlapping ANOVA & SD/`, `results/reference_archive/overlap_refinement/` | High for archived outputs |
| Sec. 5.9.2 | Modularity ANOVA/Tukey/statistics | `legacy/submission_code/SD & ANOVA/Modularity ANOVA & SD/`, `results/reference_archive/modularity_refinement/` | High for archived outputs |

## Interpretation of confidence

- **High**: final manuscript code bundle and/or direct result artifacts align clearly with the paper item.
- **Medium**: relevant scripts and outputs exist, but there are multiple versions or the paper description is broader than one script.
- **Medium-low**: historical script exists but contains assumptions that make it unsafe to treat as an exact standalone reproduction of the published claim.

The detailed reasons are in `PROVENANCE_AND_KNOWN_LIMITATIONS.md`.
