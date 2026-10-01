# Research revision report

*TOD site screening in Greater Boston, 2026 rebuild. Revision round 3, 28 September 2026. It supersedes the round-2 report, which is kept with its tables and figures in `revision/archive_round2/`. Round 1 is in `revision/archive_round1/`. Every version is listed in `revision/VERSIONS.md`.*

**Scope.** The revision is bounded to one question:

> Among a defined set of redevelopment sites near rapid transit stations, how do the
> sites compare on assessed land value, developable scale and existing station
> activity, and how far does that ordering depend on modelling choices?

It is not a measure of TOD value, not an investment or feasibility assessment, and not
an evaluation of planning outcomes.

A first-place share from random weights describes one sampling setting. It is not a
real preference, not a probability of implementation success, and not a probability
that a site is best.

---

## 0. Settings at a glance

| ID | Role | Candidates | Scored indicators (preferred direction) | Reference, tie rule | Weights |
| --- | --- | --- | --- | --- | --- |
| **M3_equal** | **Main comparison** | 246 | assessed land value/ac (lower), buildable area (larger), daily boardings + alightings (higher). Peak share **described only** | candidate set, mid-rank | exactly 1/3 each; Dirichlet(1,1,1) |
| S0_* | Historical baseline `e18a184`, reproduced | 251 | the three + peak share (lower) | baseline mixed, strict | five scenarios; Dirichlet(1,1,1,1) |
| S1_*, S2_*, S2u_* | Historical revision steps, one change each | 246 | as S0 | see §5.2 | as S0 |
| S3_* | Round-2 setting; now a **four-indicator preference scenario** | 246 | as S0 | candidate set, mid-rank | as S0 |
| K3_* | S3 with the five temporarily excluded records kept | 251 | as S0 | candidate set, mid-rank | as S0 |
| E0_equal … E3u_equal | **Historical accessibility extension of S3**, not of M3 | 251 / 246 / 244 | S3's four + `jobs45tr` (higher) | varies (§5.4) | 1/5 each; Dirichlet(1,1,1,1,1) |
| X4_peak_low_equal, X4_peak_high_equal | **Exploratory**: M3 + peak share with a named direction | 246 | the three + peak share lower (= S3_equal), or higher | candidate set, mid-rank | 1/4 each |

The five scenarios `*` are:
- `developer`, `city`, `transit`, `placemaking`: **author-constructed positions**, not
  validated with any such group;
- `equal`: **equal weights**, which is also a preference and replaces round 2's "No
  prior" label.

The full dictionary is `revision/outputs/settings.csv`.

The three M3 directions are **comparison preferences chosen for this study**. They are
not objective criteria of TOD value. Assessed land value is not acquisition cost.
Boardings plus alightings are not distinct riders, and they are not future or induced
demand.

---

## 1. What changed in this round, and what did not

| Kind | Change | Effect |
| --- | --- | --- |
| **Main comparison** | New setting **M3**: three indicators, peak share described only. Equal weights of exactly 1/3, held as fractions | New results in §4. The round-2 main (S3) keeps its ID and numbers as a historical, four-indicator preference scenario |
| **Peak share** | No longer scored in the main comparison. It is scored only in labelled historical (S*, K3, E*) and exploratory (X4_*) settings, each with its direction named | Resolves the round-2 open item on its direction for the main comparison (§3) |
| **Labels** | "No prior" → "Equal weights". Scenarios marked author-constructed. The five records described as temporarily excluded for uncertain valuation attribution. Small score gaps described as uncalibrated. Uncommitted code no longer called committed | Wording only |
| **Unchanged** | 246 candidates, record decisions, candidate-set reference, mid-rank rule, exact tie handling, tie-aware weight spaces, all S/K/E settings and their numbers, the frozen baseline | Recomputed in the same run, identical to round 2 |

Not done this round, by instruction: no new accessibility data, and no GLX, parcel or
GIS work. No new indicator combinations beyond M3 and the two labelled X4
peak-share scenarios. No new developer, city or transit variants for three indicators.

---

## 2. Baseline, data, environment, reproduction

| | |
| --- | --- |
| Historical baseline | `e18a1841e4fbba4d4a0342a8f5e44b202ecd3c3d`, frozen in `revision/baseline_e18a184/` by `revision/reproduce_baseline.py` (clean `git archive`, unmodified script). `build_2026.py`, whose labels and prose have been corrected, still reproduces its four output files byte for byte |
| Data | 14 files in `data/`, unchanged; SHA-256 in `revision/manifest.json` |
| Environment | Python 3.13.7, numpy 2.3.2, pandas 2.3.1, matplotlib 3.10.6, scikit-learn 1.8.0, scipy 1.16.2, pyarrow 25.0.1, Windows 11 |
| Randomness | `default_rng(7)`, 200,000 Dirichlet draws per weight space (3-, 4- and 5-dimensional). Five-seed check (7, 11, 23, 42, 2026) on M3, S0, S3 and E3: the largest share moves ≤ 0.33 pt (M3 ≤ 0.26 pt); Monte Carlo SE ≈ 0.1 pt |
| Checks | `revision_2026.py` stops unless its re-implementation matches the frozen baseline to 1e-9 and reproduces the seven printed baseline shares. `revision/checks.py`: 21 of 21 pass |
| This report's numbers | All from one run of `revision_2026.py`, the one that wrote `revision/outputs/` and `revision/manifest.json` |

---

## 3. Peak share: described in the main, scored only where labelled

**What it measures.** For each site's nearest station, peak share is the share of Fall
2025 weekday boardings plus alightings in 07:00–10:00 and 16:00–19:00 (six hours). It
is a station-level value.

**What it does not measure.** It says nothing about:
- service quality or frequency;
- spare capacity or crowding;
- weekend activity;
- demand strength;
- development value, rents or retail viability.

**Why it is out of the main score.** "Lower is better" served the place-making
position: the hypothesis that off-peak activity suits mixed use. The bounded question
does not adopt that position, and the opposite reading (established commute demand) is
just as available. M3 therefore carries peak share as a description in every output
table and does not score it.

**Where it is scored.**
- In the historical S-settings, with the baseline's lower-preferred direction.
- In the two labelled exploratory settings, X4_peak_low (the same scores as S3_equal)
  and X4_peak_high.

What the direction does, at equal weights (`setting_comparisons.csv`):

| Setting | First place | Top-10 overlap with M3 | Spearman with M3 |
| --- | --- | --- | --- |
| **M3** (peak share not scored) | **Malden Center #1 = #2** | — | — |
| X4_peak_low = S3 (lower preferred) | Malden Center #1 = #2 | 8/10 | 0.92 |
| X4_peak_high (higher preferred) | **Alewife #1** (Malden Center #1 and #2 joint 3rd) | 6/10 | 0.85 |

Between the two directions alone, top-ten overlap is 5/10 and Spearman 0.60. The
direction of peak share, where it is scored, is the largest single choice tested in
this revision.

---

## 4. Main comparison M3: results

All figures below come from `first_place_by_setting.csv`, `top10_by_setting.csv`,
`weight_sensitivity*.csv`, `frontier_*.csv`, `quincy_*.csv` and `key_site_ranks.csv`.

### 4.1 Pareto frontier on the raw indicators

- **15 of the 246 sites** are undominated on the three indicators. They sit in 5
  communities (Cambridge 6, Quincy 4, Malden 3, Revere 1, Braintree 1) at 9 stations.
  - Harvard #1–#4, Central #1, Alewife #1
  - Malden Center #1, #2, #4
  - Wollaston #1, #2, North Quincy #2, Quincy Adams #1
  - Wonderland #1
  - Braintree #1
- **Against the four-indicator S3 frontier on the same 246 (20 sites).** In this
  data, all 15 M3 frontier sites are among the 20 S3 frontier sites. The five that
  drop off were undominated only on peak share:
  Quincy Center #1, Revere Beach #1, Sullivan Square #1, Chestnut Hill #1 and Assembly
  #4.
- **Brookline and Somerville have no M3 frontier site.**

### 4.2 Equal weights (exactly 1/3 each)

| Rank | Site | Score |
| --- | --- | --- |
| 1 = | Malden Center #1 | 94.72 |
| 1 = | Malden Center #2 | 94.72 |
| 3 | Malden Center #4 | 92.82 |
| 4 | Malden Center #3 | 90.24 |
| 5 | Malden Center #5 | 89.84 |
| 6 | Malden Center #6 | 87.80 |
| 7 | Quincy Center #1 | 85.64 |
| 8 | Wollaston #1 | 85.50 |
| 9 | Alewife #1 | 85.23 |
| 10 | Malden Center #8 | 84.35 |

- **The joint first place is exact** (rational arithmetic). Under the candidate-set
  reference, Malden Center #1 (10.0 ac, $596K/ac) and #2 (6.1 ac, $584K/ac) are three
  positions apart on area and three positions apart on land in the other direction, with
  identical station values. Percentiles are ordinal, so four acres count the same as a
  hundredth of one.
- **Gap to third place:** 1.90 points. That equals 14 one-position steps, where a step
  is one place on one indicator at weight 1/3.
- **The gap is uncalibrated.** Neither the gaps nor the step unit have been calibrated
  to any real decision. The step is a unit of resolution, not a threshold of
  significance.
- **Clustering.** Seven of the top ten are at one station, Malden Center. The 16
  Malden Center sites share that station's activity value, which is one factor in
  their high ranks; the analysis does not show it is the only one.

### 4.3 Weight sensitivity, Dirichlet(1,1,1), seed 7, 200,000 draws

- **Every draw has a single winner** (no identical-vector or numerical ties). Split
  shares sum to 1.
- **11 sites ever come first; 5 reach 1%.**

| Site | Share of draws first |
| --- | --- |
| Malden Center #1 | 41.6% |
| Malden Center #2 | 32.0% |
| Braintree #1 | 12.9% |
| Malden Center #4 | 9.0% |
| Alewife #1 | 2.3% |
| Harvard #1 | 0.9% |
| Harvard #4 | 0.6% |
| Central #1 | 0.3% |
| Wonderland #1 | 0.3% |
| Quincy Adams #1 | 0.15% |
| Harvard #3 | 0.05% |

This is a three-dimensional weight space. Its shares cannot be compared with the
four-indicator (S3: Malden Center #1 26.8%, Revere Beach #1 26.1%) or five-indicator
spaces as an improvement or a deterioration. Nor do they measure anyone's preferences.

### 4.4 Quincy only, with every M3 score and the reference fixed

This is a controlled experiment in the 2026 framework. It restricts which sites may
come first; the percentiles are computed once on all 246. It does not re-run, confirm
or refute the 2024 model.

- **Equal weights.** The best Quincy site is Quincy Center #1, 7th among all 246. Six
  sites rank above it, all at Malden Center. Next in Quincy are Wollaston #1 and #2.
  Two Quincy sites reach the all-candidate top ten.
- **What the restriction removes from the top ten:** Malden Center #1–#6, Malden
  Center #8 and Alewife #1.
- **Random weights.**
  - Quincy sites together come first in **0.15%** of all-candidate draws, all of it
    Quincy Adams #1.
  - Within Quincy alone: Quincy Center #1 43.9%, Wollaston #1 41.4%, Wollaston #2 9.2%,
    North Quincy #2 4.2%.
- **Across all 37 deterministic settings in the run** (main, historical, extension,
  exploratory), no all-candidate first place is in Quincy. The best Quincy site ranks
  3rd–12th.

### 4.5 Against the four-indicator S3: what removing peak share changes

The change is a removed indicator, not an improvement. Shares from different weight
spaces are not compared.

| | S3 (four, peak share lower preferred) | M3 (three) |
| --- | --- | --- |
| Equal-weight first | Malden Center #1 = #2 | Malden Center #1 = #2 |
| Top-ten members only in this setting | Revere Beach #1, Wonderland #1 | Alewife #1, Malden Center #8 |
| Rank agreement | Spearman 0.923, Kendall 0.767 | |
| Largest and median rank move | 77 and 16 places | |
| Frontier | 20 | 15 |

Selected sites, equal-weight rank in S3 → M3:

| Site | S3 → M3 | Why |
| --- | --- | --- |
| Revere Beach #1 | 7 → 21 | its station has the lowest peak share among the candidates (0.38) |
| Wonderland #1 | 9 → 17 | |
| Alewife #1 | 62 → 9 | its station's peak share is among the highest (0.57; Ball Square's 0.59 is the highest) |
| Quincy Center #1 | 5 → 7 | |
| Wollaston #1 | 10 → 8 | |
| Braintree #1 | 11 → 13 | |

From the historical baseline to M3 (S0 → M3, all changes together, not attributable to
any one): top-ten overlap 5/10, Spearman 0.86.

---

## 5. Supporting evidence carried from round 2 (unchanged in this run)

### 5.1 Why 251 became 246: five records temporarily excluded for uncertain valuation attribution

The five are **not duplicate rows**, **not all confirmed errors**, and **no valuation
was repaired or re-apportioned**. They are held out until the valuation can be
attributed. Evidence: MAPC attributes and definitions, and MAPC's own centroids;
details in `record_audit.csv`.

| Record | What the attributes show | Basis |
| --- | --- | --- |
| Assembly #1 (site_oid 9967) | Parcel 1242329, `nparcels` = 0 (a confirmed field inconsistency). Land $8,492,300, building $5,130,800, identical to #2 and #3. Recorded 2.25 ac | **Valuation attribution problem**: one parcel's whole value on three records of different area (2.25, 2.25, 1.60 ac), at MAPC centroids 67–137 m apart |
| Assembly #2 (9971) | As #1 | **Valuation attribution problem** |
| Quincy Center #6 (6758) | Six parcels including 621026. Land value is, by MAPC's definition, the sum over all six | **Valuation attribution problem**: parcel 621026 is also listed by #8, and the split is unknown |
| Assembly #3 (9949) | One parcel, an address, internally consistent; values identical to #1 and #2 | **Conservative exclusion**: its value may be correct, but it cannot be told apart from the other two |
| Quincy Center #8 (6766) | Parcel 621026, `nparcels` = 0 (a confirmed field inconsistency). Its own, distinct values | **Conservative exclusion**: its values may be the parcel's own, but the parcel is also valued in #6 |

- **Where the five stood.** Before exclusion, all five sat outside every top ten. Under
  S3 rules, keeping them (K3) changes no first place and no top ten.
- **Other flagged records, kept:** Braintree #7 (`nparcels` = 0 only); Davis #1/#9; four
  area discrepancies; two `jobs45tr` zeros.

### 5.2 Controlled comparisons, four indicators (only one thing changes in each)

| Change isolated | Equal-weight first | Top-10 kept | Spearman |
| --- | --- | --- | --- |
| Record handling only (S0 → S1) | unchanged | 10/10 | 1.000 |
| Tie rule only, baseline reference (S1 → S2) | unchanged | 10/10 | 1.000 |
| Tie rule only, candidate-set reference (S2u → S3) | unchanged | 10/10 | 0.9999 |
| **Reference only**, strict ties (S1 → S2u) | Malden Center #1 → Malden Center #1 = #2 | 7/10 | 0.975 |
| **Reference only**, mid-rank ties (S2 → S3) | Malden Center #1 → Malden Center #1 = #2 | 7/10 | 0.975 |

- **Among the four-indicator steps, only the reference-only comparisons move a first
  place.** Under both tie rules (S1 → S2u, S2 → S3), the developer scenario's first
  place changes from Braintree #1 to Malden Center #2. The transit and equal-weight
  scenarios change from Malden Center #1 alone to a Malden Center #1 = #2 tie. City and
  place-making keep their first places.
- **S0 → S3 changes several things at once.** Its total change is not attributed to
  the reference.

The percentile rules are set out in `revision/methods.py` and `transform_rules.csv`:
- **strict** (baseline): 100·L/n for higher-is-better and 100·(G+E)/n for
  lower-is-better, where L, E and G count reference values below, equal and above;
- **mid-rank** (current): 100·(L+E/2)/n and 100·(G+E/2)/n.

Mid-rank gives equal values equal scores, treats both directions alike, and creates no
ties between distinct values.

Final-score ties:
- **Deterministic settings:** exact rational comparison, with every joint first
  listed.
- **Random weights:** a site within 1e-9 of the top is a joint winner and credit is
  split among joint winners; identical-vector ties are told apart from numerical
  ones. `argmax` is shown only for contrast.
- **Quincy-only** uses the same functions.

### 5.3 Four-indicator weight spaces (history)

Split shares, Dirichlet(1,1,1,1):

| | S0 | S1 | S2 | S2u | S3 | K3 |
| --- | --- | --- | --- | --- | --- | --- |
| Malden Center #1 | 31.1 | 31.1 | 31.6 | 26.6 | 26.8 | 26.7 |
| Revere Beach #1 | 14.4 | 14.4 | 14.5 | 26.0 | 26.1 | 27.0 |
| Malden Center #2 | 2.6 | 2.6 | 3.1 | 20.1 | 20.1 | 20.8 |
| Braintree #1 | 33.4 | 33.4 | 33.0 | 10.1 | 10.0 | 9.1 |

The historical scenarios under S3, all author-constructed except equal weights:

| Scenario | S3 first place | Gap to second |
| --- | --- | --- |
| Developer | Malden Center #2 | 0.30 pt |
| City | Malden Center #1 | 0.37 pt |
| Transit agency | Malden Center #1 = #2 | exact tie |
| Place-making | Revere Beach #1 | 2.74 pt |
| Equal weights | Malden Center #1 = #2 | exact tie |

### 5.4 Historical accessibility extension of S3 (E0–E3u)

This extends the four-indicator S3, not M3. It adds MAPC's `jobs45tr`, a University of
Minnesota Accessibility Observatory measure.
- **Vintage.** MAPC's documentation cites the 2016 and 2018 editions. The 2016 edition
  uses LODES 2014 jobs; the 2018 edition's jobs year is unverified.
- **GLX.** The transit network predates the Green Line Extension, and MAPC published
  on 14 Jan 2022.

E3 results:
- **Frontier:** 54 sites on the 246.
- **Equal weights:** Malden Center #1 = #2, then Sullivan Square #1 0.29 pt behind.
- **Dirichlet(1,1,1,1,1):** Malden Center #1 15.7%, Malden Center #2 12.0%, Central #1
  11.5%.
- **E3u** (zero job access treated as unknown): within 0.6 pt of E3 for every site.

Round 1's "Sullivan Square #1 first with five indicators" came from the strict tie rule
and is withdrawn.

### 5.5 What the home-made geometry decoding establishes

No standard GIS reader was available, so every check below is against MAPC's own
fields, not against an independent reader.

| Aspect | Status |
| --- | --- |
| Coordinates, areas and centroids of single-ring polygons | **Validated**: area matches `sitearea_a` for 99.2% of 3,028 sites; centroid within 0.16 m for 99% |
| Multiple parts, holes, and overlaps arising from a second ring | **Provisional**: in 30 multi-ring records, the recorded area matches the decoded total in 12, the first ring alone in 9, neither in 9 |

No exclusion depends on the geometry, and no decoding result is reported as an error in
MAPC's data.

---

## 6. What holds, and where it stops

Stated only for the settings where it actually holds (`key_site_ranks.csv`,
`first_place_by_setting.csv`):

- **Malden Center #1 is first or jointly first under equal weights in M3, in every
  historical four-indicator setting (S0–S3, K3) and in every accessibility extension
  (E0–E3u).**
  - **It is not first in X4_peak_high.** Scoring peak share as higher-preferred puts
    Alewife #1 first, with Malden Center #1 and #2 joint 3rd.
  - In the weight spaces it is first in M3, S2u, S3, E0–E3u, and second in S0–S2 and K3.
- **Malden Center #1 and #2 tie exactly for first** under the candidate-set reference
  (M3, S3, E3, E3u). They do not tie under the baseline reference. The tie comes from
  the ordinal percentiles (§4.2).
- **No Quincy site comes first among all candidates** in any of the 37 deterministic
  settings.
- **The tie rule changes no four-indicator first place or top ten;** neither does
  removing the five records (§5.2).
- **What depends on the setting:**
  - Braintree #1: 3rd at S0, 11th at S3, 13th in M3, 33rd in E3. Its M3 share is 12.9%.
  - Revere Beach #1: 7th at S3, 21st in M3; its S3 position rests on peak share.
  - Alewife #1: 62nd at S3, 9th in M3, 1st in X4_peak_high.
  - The developer scenario's first place: Braintree #1 or Malden Center #2, depending on
    the reference.
  - Everything involving `jobs45tr`.
- **Score gaps** between neighbouring sites have not been calibrated to any real
  decision. This report neither claims them as real advantages nor declares them
  meaningless.

---

## 7. Claims: kept, narrowed, withdrawn

Carried from earlier rounds and still valid: the regional-access exclusion argument
withdrawn; the 2024 "admitted gap" claim withdrawn; the Green Line service conclusion
withdrawn; the cost analysis narrowed to an illustration; "would pay for itself"
withdrawn; "scenario winners on the frontier" reclassified as true by construction;
Medford lost in the 2024 postcode join kept.

| Claim | Status | Reason |
| --- | --- | --- |
| Main analysis is four indicators with peak share lower-preferred (round 2) | **Superseded** | M3: peak share described, not scored (§3) |
| "Malden Center #1 is first or jointly first under equal weights in every setting tested" (round 2) | **Narrowed** | False for X4_peak_high (Alewife #1). Holds for M3, S0–S3, K3 and E0–E3u (§6) |
| "Every change of first place comes from the reference step" (round 2) | **Narrowed** | True of the four-indicator controlled steps only (§5.2). S0 → S3 and S0 → M3 are not attributed to one change |
| "No prior (all four equal)" | **Renamed** | "Equal weights": a preference, not its absence |
| Developer, city, transit, place-making positions | **Narrowed** | Author-constructed, not validated with those groups |
| Five records "unreliable/unverifiable" | **Narrowed** | Temporarily excluded for uncertain valuation attribution: three attribution problems, two conservative. Not duplicates, not all confirmed errors, not repaired |
| Small leads "not substantive" (round 2) | **Withdrawn** | Neither significance nor insignificance has been calibrated |
| "Reproduced by the committed code" (round 2) | **Corrected** | At the time this claim was corrected, the revised code was in the working tree and had not yet been committed |
| "One parcel recorded twice"; effective-weight claim; Sullivan Square #1 five-indicator lead (round 1) | **Withdrawn** (round 2) | See `revision/archive_round1/NOTE.md` |
| Historical baseline results (Braintree #1 33.4%, Malden Center #1 31.1%; three scenario winners) | **Kept as history** | Reproduced exactly; not the main comparison |

---

## 8. Open issues that still affect interpretation

1. **Ordinal percentiles.** They make Malden Center #1 and #2 tie despite four acres'
   difference. Whether magnitude should count is a modelling choice not made here.
2. **Valuation of the five excluded records.** Needs MAPC's parcel layer (parcels
   1242329 and 621026). Until then they stay out of the main comparison.
3. **Station-level indicators.** Daily boardings plus alightings are shared by every
   site at a station, which clusters sites by station (seven of M3's top ten are at
   Malden Center).
4. **Accessibility.** `jobs45tr` is pre-GLX, its edition is ambiguous, and it is used
   only in the S3-based extension. An up-to-date measure would be new data production.
5. **Decoded geometry beyond single rings** is provisional (§5.5).
6. **Distance** is a 0.805 km straight-line cut; 13 sites lie between 0.805 and 1 km.
7. **The positions** (developer, city, transit, place-making) are the author's. The
   M3 preference directions are this study's choices.

---

## 9. Facts for the case page, each with its source

Paths are relative to `revision/outputs/` unless stated. Each is produced by the
code in this repository, in the run recorded in
`revision/manifest.json`.

- **Main comparison (M3):** 246 candidate sites in 9 communities at 39 stations,
  compared on assessed land value per acre (lower preferred), buildable area (larger
  preferred) and daily station boardings + alightings (higher preferred). These are
  this study's comparison preferences. — `settings.csv`, `candidates_quality.csv`
- **Five of the 251 screened sites are temporarily excluded** because their assessed
  values cannot be reliably attributed to the site: three attribution problems, two
  conservative exclusions. — `record_audit.csv`
- **M3 frontier:** 15 sites no other site beats on all three indicators at once, in 5
  communities. — `frontier_summary.csv`, `frontier_by_setting.csv`
- **M3, equal weights:** Malden Center #1 and #2 tie exactly for first; Malden Center
  #4 is 3rd. — `first_place_by_setting.csv`, `top10_by_setting.csv`
- **M3, Dirichlet(1,1,1), seed 7, 200,000 draws:** Malden Center #1 41.6%, Malden
  Center #2 32.0%, Braintree #1 12.9%, Malden Center #4 9.0%; 11 sites ever first. It
  describes the sampling setting only. — `weight_sensitivity_summary.csv`
- **M3, Quincy only, scores fixed:** the best Quincy site, Quincy Center #1, ranks 7th
  of 246. A controlled experiment, not a replication of 2024. — `quincy_vs_all.csv`
- **Peak share, where scored:** its direction decides the equal-weight first place.
  Higher preferred gives Alewife #1; lower preferred gives Malden Center #1 = #2. —
  `setting_comparisons.csv`
- **Historical baseline (`e18a184`, unchanged):** Braintree #1 33.4%, Malden Center #1
  31.1%; author-constructed scenario winners Braintree #1, Malden Center #1, Revere
  Beach #1. — `revision/baseline_e18a184/`
- **Job access (`jobs45tr`):** from the Minnesota Accessibility Observatory via MAPC,
  with a network that predates the Green Line Extension; used only in the historical
  extension. — `indicator_dictionary.csv`

**Not for the case page:**
- that any site is best, or would pay, be approved or work;
- that a share is a probability or a measure of preference;
- that a small score gap is a real advantage;
- that low (or high) peak share means better service, spare capacity or development
  value;
- that the five records are duplicates or confirmed errors;
- that the Quincy experiment refutes the 2024 model;
- that the decoded overlaps are confirmed.

---

## 10. Files and commands

```bash
python revision/reproduce_baseline.py
```
```bash
python revision/checks.py
```
```bash
python revision_2026.py
```
```bash
python tools/make_review_package.py
```

| File | Contents |
| --- | --- |
| `revision_2026.py`, `revision/methods.py`, `revision/geometry.py`, `revision/checks.py` | analysis, scoring rules, polygon decoding, rule checks |
| `revision/VERSIONS.md`, `revision/outputs/settings.csv` | versions; every setting with role, candidates, reference, tie rule, scored directions and weights |
| `record_audit.csv`, `candidates_quality.csv`, `site_id_map.csv`, `candidate_overlaps.csv` | record evidence and decisions; stable IDs |
| `first_place_by_setting.csv`, `rankings_by_setting.csv`, `top10_by_setting.csv`, `setting_comparisons.csv`, `key_site_ranks.csv` | deterministic results and controlled comparisons |
| `weight_sensitivity.csv`, `weight_sensitivity_summary.csv`, `weight_seed_stability.csv` | every site in every weight space: unique, joint and split shares, argmax, top five, MC SE, five-seed ranges |
| `frontier_by_setting.csv`, `frontier_summary.csv` | frontiers on raw values (3, 4 and 5 indicators) |
| `quincy_vs_all.csv`, `quincy_weight_space.csv` | Quincy-only experiment, M3 and history |
| `indicator_dictionary.csv`, `transform_rules.csv`, `internal_checks.csv`, `summary.json` | definitions, percentile behaviour, checks, headline numbers |
| `revision/figures/f1`–`f3` | first-place shares (M3; four-indicator history; S3-based extension); equal-weight ranks by setting; Quincy only |
| `revision/baseline_e18a184/`, `revision/archive_round1/`, `revision/archive_round2/` | frozen baseline; superseded rounds |
