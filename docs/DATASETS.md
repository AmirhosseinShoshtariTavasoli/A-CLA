# Datasets

The final manuscript's Table 5.1 lists the following 15 networks. The abstract states that sixteen networks were evaluated; no sixteenth row appears in Table 5.1, and the recovered canonical adjacency directory also contains 15 matrices. The repository preserves this as a documented publication/archive discrepancy.

| Manuscript name | Nodes | Edges | Archived matrix |
|---|---:|---:|---|
| Celegans | 306 | 2359 | `adjacency_matrix_C.elegans_output.xlsx` |
| Diseasome | 1419 | 3926 | `adjacency_matrix_Diseasome_output.xlsx` |
| Dolphin | 62 | 147 | `adjacency_matrix_Dolphin_output.xlsx` |
| Hi-tech | 33 | 91 | `adjacency_matrix_hi-tech_output.xlsx` |
| Jazz | 198 | 5484 | `adjacency_matrix_Jazz_output.xlsx` |
| Karate Club | 30 | 57 | `adjacency_matrix_karate_output.xlsx` |
| Les Misérables | 77 | 254 | `adjacency_matrix_lesmisrable_output.xlsx` |
| Netscience | 1461 | 2742 | `adjacency_matrix_netscience_output.xlsx` |
| Polbooks | 105 | 441 | `adjacency_matrix_polbook_output.xlsx` |
| Yeast | 2361 | 7182 | `adjacency_matrix_yeast_output.xlsx` |
| Candida_Multiplex_Genetic | 367 | 410 | `adjacency_matrix_Candida_output.xlsx` |
| Bos_multiplex_Genetic | 325 | 373 | `adjacency_matrix_BoS_output.xlsx` |
| Celegans_Multiplex_Genetic | 3879 | 4077 | `adjacency_matrix_C.elegans-Genetic_output.xlsx` |
| DanioRerio_Multiplex_Genetic | 155 | 212 | `adjacency_matrix_DanioRerio_output.xlsx` |
| HepatitusCVirus_Multiplex_Genetic | 105 | 110 | `adjacency_matrix_HepatitC_output.xlsx` |

## Important notes

- The Karate Club counts in the manuscript are 30 nodes and 57 edges, not the canonical 34-node Zachary graph often used elsewhere. Reproduction should therefore use the archived matrix rather than substituting NetworkX's built-in karate graph unless the goal is only a software smoke test.
- Several historical scripts use separate node/edge-format workbooks; these are preserved under `data/network_tables/`.
- Dataset source URLs and redistribution licenses were not consistently stored in the recovered project directory. Verify original third-party dataset terms before redistributing individual datasets outside this repository.
