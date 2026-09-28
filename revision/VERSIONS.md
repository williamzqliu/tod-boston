# Versions of the analysis

Every version below is kept. Only the last is current.

| Version | Where | Main comparison | Status |
| --- | --- | --- | --- |
| Historical baseline, commit `e18a184` | `build_2026.py`, `2026-rebuild.ipynb`, and frozen in `revision/baseline_e18a184/` | 251 sites; four indicators (land value/ac ↓, buildable area ↑, daily on+off ↑, peak share ↓); mixed percentile reference; strict tie rule; five author-constructed positions plus equal weights | Kept unchanged, reproducible with `revision/reproduce_baseline.py`. Labels and prose in `build_2026.py` were corrected; computations and outputs are byte-identical |
| Revision round 1 | `revision/archive_round1/` | Four vs five indicators and two references on the 251 | **Superseded.** Its "one parcel recorded twice" classification is wrong (see its `NOTE.md`) |
| Revision round 2 | `revision/archive_round2/` (tables, figures, manifest, report) | S3: 246 sites, four indicators with peak share lower-preferred, candidate-set reference, mid-rank ties | **Superseded as the main comparison.** S3 and every other round-2 setting are still computed in `revision/outputs/` with the same numbers, as historical revision settings |
| Revision round 3, current | `revision/outputs/`, `revision/figures/`, `RESEARCH_REVISION_REPORT.md` | **M3**: 246 sites, three indicators (land value/ac lower, buildable area larger, daily on+off higher preferred), candidate-set reference, mid-rank ties, exact 1/3 weights; peak share described only | Current |

Setting IDs in the current outputs (`revision/outputs/settings.csv` has the full dictionary):

| ID | Role |
| --- | --- |
| `M3_equal` | **main comparison** |
| `S0_*` | historical baseline `e18a184`, reproduced |
| `S1_*`, `S2_*`, `S2u_*` | historical revision steps, each changing one thing |
| `S3_*` | round-2 four-indicator setting; now a four-indicator preference scenario (peak share lower preferred) |
| `K3_*` | S3 rules with the five temporarily excluded records kept |
| `E0_equal` … `E3u_equal` | historical accessibility extension **of the four-indicator S3** (adds `jobs45tr`); not an extension of M3 |
| `X4_peak_low_equal`, `X4_peak_high_equal` | exploratory: M3 plus peak share with an explicit direction (`X4_peak_low` has the same scores as `S3_equal`) |

`*` stands for the five scenarios: `developer`, `city`, `transit`, `placemaking` (author-constructed, not validated with those groups) and `equal` (equal weights, itself a preference).
