# Research revision report

*TOD site screening in Greater Boston, 2026 rebuild. Two revision rounds, both 28 September 2026. This document supersedes the round-1 version; round-1 tables are kept in `revision/archive_round1/`.*

**Scope.** This revision is bounded to one question:

> Among a defined set of redevelopment sites near rapid transit stations, how do the
> sites compare on assessed land value, developable scale and existing station
> activity, and how far does that ordering depend on modelling choices?

It is not a measure of TOD value, not an investment or feasibility assessment, and not
an evaluation of planning outcomes. A first-place share from random weights describes
a sampling scheme. It is not a probability that a site is best, and not a measure of
anyone's preferences.

**Three questions this report answers directly:**

1. *Why does the main candidate set go from 251 to 246?* See §3.2. Five records, by
   ID: three whose valuation cannot be allocated to the site, and two excluded as a
   conservative precaution. None is a duplicate row.
2. *Why does peak share point the way it does?* See §1.5. The direction is an
   exploratory preference inherited from the baseline's place-making position. It
   lacks sufficient grounds within the bounded question, and it is listed as an
   unresolved method choice.
3. *What does the home-made geometry decoding establish?* See §3.4. It establishes
   areas and centroids for single-ring polygons. Holes, multiple parts and the
   overlaps derived from them are provisional, and no exclusion depends on them.

---

## 0. What changed, by kind

| Kind | This round | Where |
| --- | --- | --- |
| **Presentation and terminology** | Round 1's "one parcel recorded twice" corrected. The claim that a narrow percentile band means an indicator "moves the weighted sums less than its nominal weight" withdrawn. Sites, straight-line distance, assessed value, boardings + alightings and the two separate filters kept as corrected in round 1 | `build_2026.py`, `README.md`, §7 |
| **Evidence retrieved or verified** | MAPC's definitions of parcel IDs and land value (§3.1). MAPC's own centroids and areas for the flagged records. Site polygons decoded from the MAPC file, validated for areas and centroids of single-ring polygons; provisional for rings, parts and overlaps (§3.4). The source and vintage of `jobs45tr` (§1.4) | `record_audit.csv`, `candidate_overlaps.csv`, `indicator_dictionary.csv` |
| **Methods or data handling that change results** | Five candidates whose land value cannot be attributed to the site leave the main set (251 → 246). Mid-rank percentile ties. Every indicator ranked against the candidate set. Exact arithmetic for joint first places. Tie-aware weight spaces. Main setting fixed as four indicators; job access demoted to a historical extension | §1, §3–§5 |
| **Limits still open** | The direction of peak share (an unresolved method choice). Parcel-level values. Multi-part and hole reading of the decoded geometry (provisional). Post-GLX accessibility. The ordinal nature of percentiles. The straight-line distance cut | §8 |

---

## 1. Final research setting

### 1.1 Settings

| | **Main analysis (S3)** | Extension (E3 / E3u) | Historical baseline (S0 = `e18a184`) |
| --- | --- | --- | --- |
| Candidate set | **246 sites**: the 251 less the five in §3 | 246 (E3), or 244 with the two zero job-access records treated as unknown (E3u) | 251 |
| Indicators | assessed land value per acre ↓, buildable area ↑, daily boardings + alightings at the station ↑, weekday peak-hour share ↓ (direction exploratory, §1.5) | the four + `jobs45tr` ↑, a historical, pre-GLX access measure | the four |
| Percentile reference | every indicator against the candidate set (n = 246) | against its own candidate set | land value, buildable area and job access against MAPC's regional records; station measures against the 251 |
| Percentile tie rule | mid-rank | mid-rank | strict |
| Weights | five named positions and equal weights; Dirichlet(1,1,1,1), seed 7, 200,000 draws | equal weights; Dirichlet(1,1,1,1,1), seed 7, 200,000 draws | as S3 |
| Joint first places | exact rational comparison, all listed | same | `argmax`, row order |

Intermediate settings isolate one change at a time:

- **S1**: 246 sites, baseline reference, strict ties.
- **S2**: 246 sites, baseline reference, mid-rank ties.
- **S2u**: 246 sites, candidate-set reference, strict ties.
- **K3**: main rules with the five flagged records kept (251).
- **E0**: five indicators under baseline rules.
- **E2**: five indicators, baseline reference, mid-rank ties.

All are listed in `settings.csv`.

### 1.2 Why this setting (not chosen by its winners)

- **Four indicators as the main analysis.** The bounded question is about land value, scale and existing station activity. `jobs45tr` measures something else: modelled regional access to jobs. It is also dated before the Green Line Extension, and 17 of the 34 sites it adds to the main-set frontier are on the Green Line, 11 of them in Somerville (§5.3). It is kept as a historical-accessibility extension. Shortlist length plays no part in this decision.
- **Candidate-set reference.** The question compares sites inside the defined set. Ranking every indicator against that set gives every score one meaning: the share of candidates this site is better than, with ties counted half. The baseline mixes two meanings, regional standing for land, area and access and candidate standing for the station measures. The candidate-set reference also matches the Quincy experiment, where scores are fixed on the full candidate set. Costs: it is coarser (steps of 1/246), it creates exact ties in weighted sums (§4.2), and scores move when the candidate set changes (K3 against S3). This revision does not claim that the candidate-set reference makes "effective" weights equal nominal ones. It changes how the percentiles are spread (§4.1), and that is all it has been shown to do.
- **Mid-rank ties.** This was chosen for its properties, before looking at any first place (§4.1). Equal raw values get equal scores. Scoring v as higher-is-better gives exactly the same score as scoring −v as lower-is-better; the strict rule does not. No ties are created between distinct values. Its effect on results was checked afterwards: it changes no four-indicator first place or top ten under either reference. It changes one five-indicator result, removing round 1's Sullivan Square #1 lead (§5.3).

### 1.3 Are the four indicators themselves sound?

| Indicator | Definition and direction | Verdict | Minimal correction |
| --- | --- | --- | --- |
| Assessed land value / acre ↓ | `land_value / sitearea_a`; MAPC sums the full value of every parcel *overlapping* the site | **Sound for most sites; not reliably attributable for five** (§3.2: three not allocatable, two conservative) | Those five leave the main set; no value is re-apportioned |
| Buildable area ↑ | MAPC `buildar_ac` | Sound. Four candidates' recorded area differs from the decoded area by more than 2%, cause unknown (decoding or source) | Flag only (§3.2) |
| Daily boardings + alightings ↑ | Station-level, Fall 2025 | Sound as station activity. It counts movements, not riders, and ties within a station | None |
| Weekday peak share ↓ | Six peak hours ÷ weekday total | **The direction is an exploratory preference without sufficient grounds in the bounded question** (§1.5) | Kept for continuity with the baseline, with the dependence reported; listed as an unresolved method choice (§8) |

### 1.4 `jobs45tr`: source, jobs year, network year, GLX

What was verified this round, and how:

- **Source.** MAPC's methods page names the University of Minnesota Accessibility Observatory, *Access Across America*.
- **Which edition is ambiguous in MAPC's own documentation.**
  - The gitbook data dictionary gives "Number of jobs within a 45-minute commute by public transit (Minnesota Accessibility Observatory, 2016)".
  - The gitbook references list *Access Across America: Transit 2018 Data* (Owen & Murphy, 2020).
  - The DataCommon metadata in this repository says 2018.
  - The field names differ between the documentation (`jobs45intr`) and the data (`jobs45tr`).
- **Jobs year.** The Transit 2016 methodology (Owen, Murphy & Levinson, 27 Sept 2017) uses LEHD LODES **2014** jobs, GTFS schedules of "various dates", and a 7–9 AM departure window averaged at 1-minute steps. The Transit 2018 methodology (CTS 20-02, Feb 2020) could not be retrieved, so if that edition was used, its jobs year is **unverified**.
- **Network year and GLX.** Whichever edition, the transit schedules come before 2022. MAPC published the dataset on 14 January 2022. The Green Line Extension opened in March 2022 (Union Square) and December 2022 (Medford). So `jobs45tr` does **not** include GLX service. The jobs year and the network year are different things, and neither matches the Fall 2025 ridership.
- **The two zeros** (Assembly #4, #5). Their neighbours, 300 m away, record 700,445. The Observatory works at census-block level, so a zero can be a computed value for a block the pedestrian network does not reach. That was not verified, so the zeros are kept as recorded, flagged, and compared against treating them as unknown (E3 against E3u).

Sources:
[MAPC methods](https://mapc.gitbook.io/rethinking-the-retail-strip/readme/methods.md),
[data dictionary](https://mapc.gitbook.io/rethinking-the-retail-strip/readme/appendix-2-data-dictionary.md),
[references](https://mapc.gitbook.io/rethinking-the-retail-strip/readme/references.md),
[MAPC article, 14 Jan 2022](https://www.mapc.org/planning101/are-strip-malls-key-to-solving-greater-bostons-housing-woes/),
[Access Across America: Transit 2016 Methodology](https://fdot.gov/docs/default-source/planning/FTO/accessibility/2016TransitMethod.pdf),
[Access Across America: Transit 2018 (CTS 20-01)](https://www.cts.umn.edu/publications/report/access-across-america-transit-2018).

Minimal update, not done: obtain a post-2022 jobs-by-transit measure for the same site
centroids, swap it for `jobs45tr` and re-run E3. That is new data production, outside
this round.

### 1.5 Why peak share points the way it does, and why that is still open

**What it measures.** For the station nearest each site, it is the share of Fall 2025
weekday boardings plus alightings that fall in 07:00–10:00 and 16:00–19:00. That is six
of roughly twenty service hours, averaged over the season. Every site at a station
gets the same value. A low value means the station's weekday activity is less
concentrated in those six hours, and relatively more of it falls at midday, in the
evening or early morning.

**What it does not measure.** It is not:
- service quality, frequency or reliability;
- spare capacity or crowding: nothing here measures loads against capacity, and MBTA's
  on-board `average_flow` field is not used;
- weekend activity, or how even the off-peak hours are;
- demand strength: a quiet station can have a low peak share;
- development value, rents or retail viability.

**What "lower is better" was for.** The direction comes from the baseline. It serves one
specific objective, the place-making position: sites whose station already sees
activity outside the commute peaks are assumed to suit mixed-use or ground-floor
retail. That assumption is a hypothesis about how existing activity relates to a
planning goal. The data here do not test it.

**Whether that is enough for the main analysis.** It is not. The bounded question is to
*compare* existing station activity, and describing peak concentration fits that. But
ranking low peak share as better presupposes the place-making objective, which the
bounded question does not adopt. The opposite reading is equally available: a
peak-heavy station has established commute demand, which a housing-first or
transit-agency position might prefer. So the current direction is an **exploratory
preference**, kept in S3 only so that the main analysis stays comparable with the
baseline. It is listed as an unresolved method choice (§8.1).

**How much the results depend on it** (`setting_comparisons.csv`, `first_place_by_setting.csv`,
equal weights under S3):

| Variant | First place | Top-10 overlap with S3 | Spearman with S3 |
| --- | --- | --- | --- |
| S3, peak share lower-is-better (current) | Malden Center #1 = #2 | — | — |
| S3 without peak share (three indicators) | Malden Center #1 = #2 | 8/10 | 0.92 |
| S3 with peak share higher-is-better | **Alewife #1** | 5/10 | 0.60 |

- The equal-weight first place survives dropping peak share, but not reversing it.
- The place-making position's first place (Revere Beach #1) exists only because of this
  direction.
- Every result in this report that involves peak share is conditional on this
  exploratory preference.

---

## 2. Baseline, data and environment

| | |
| --- | --- |
| Baseline | `e18a1841e4fbba4d4a0342a8f5e44b202ecd3c3d`, frozen in `revision/baseline_e18a184/` by `revision/reproduce_baseline.py` (clean `git archive`, unmodified script). Its four output files are byte-identical to the pre-revision local copies, and `build_2026.py` as edited still reproduces them byte for byte |
| Data | 14 files in `data/`, unchanged; SHA-256 in `revision/manifest.json` |
| Environment | Python 3.13.7, numpy 2.3.2, pandas 2.3.1, matplotlib 3.10.6, scikit-learn 1.8.0, scipy 1.16.2, pyarrow 25.0.1, Windows 11 |
| Randomness | Dirichlet `default_rng(7)`, 200,000 draws per space; five-seed check (7, 11, 23, 42, 2026) on S0, S3 and E3: the largest share moves ≤ 0.33 pt; Monte Carlo SE ≈ 0.1 pt |
| Reproduction | `revision_2026.py` re-implements the screening and stops unless it matches the frozen baseline to 1e-9. The seven printed Dirichlet shares are also reproduced. 21 rule checks in `revision/checks.py` pass |

Every round-1 checkpoint still reproduces: 251 sites in 9 communities, a 22-site
frontier in 7 communities, the three scenario winners, 33.4% / 31.1%, 10 sites ever
first, and 54 sites with job access.

---

## 3. Record audit

### 3.1 Evidence used, in order of strength

1. **MAPC attribute fields**: `site_oid`, parcel IDs, address, `nparcels`, land,
   building, other and total value, site and buildable area, and MAPC's own centroid
   (lat/long).
2. **MAPC's definitions** (gitbook dictionary): parcel IDs are "parcels overlapping the
   site", and "Number of Parcels" is the number of overlapping parcels. The repository's
   metadata defines `land_value` as the "combined assessed land value of all parcels in
   site". A parcel overlapping several sites can therefore be valued in full in each.
3. **Site polygons decoded by this revision** from the undocumented `shape` field. What
   this does and does not establish is set out in §3.4. **No exclusion rests on the
   decoded geometry.**

Not available: parcel geometry and parcel-level values. The MAPC Land Parcel Database
(2015) is not in the repository.

### 3.2 Why 251 became 246: the five excluded records

None of the five is a duplicate row. Every decision is made on the attribute evidence
(1–2 above). The geometry column only records what the decoding shows, and how far it
can be trusted.

| Record | Confirmed from attributes | Basis for exclusion | Decoded geometry (§3.4) |
| --- | --- | --- | --- |
| **Assembly #1**, site_oid 9967 (objectid 3) | Parcel 1242329, with no brackets and no address. `nparcels` = 0 contradicts the listed parcel (**confirmed field error**). Land $8,492,300, building $5,130,800, other $1,099,000, total $14,722,100: identical to #2 and #3. Recorded area 2.25 ac. MAPC centroid 67 m from #2 and 70 m from #3 | **Valuation cannot be allocated.** One parcel's whole value stands for three records on different areas (2.25, 2.25, 1.60 ac) at different MAPC centroids, so at most one per-acre figure could be the parcel's own, and which one is unknown | One ring, 2.254 ac, centroid 0.06 m from MAPC's: validated regime. No decoded overlap with #2 or #3 |
| **Assembly #2**, 9971 (objectid 13) | As #1: `nparcels` = 0, identical values, recorded 2.25 ac; MAPC centroid 137 m from #3 | **Valuation cannot be allocated**, as #1 | One ring, 2.246 ac (88 vertices against #1's 17), centroid 0.06 m: validated regime. No decoded overlap |
| **Assembly #3**, 9949 (objectid 7) | `nparcels` = 1, parcel [1242329], address 771 McGrath Hwy: internally consistent. Values identical to #1 and #2; recorded 1.60 ac | **Conservative exclusion.** Its value may well be the parcel's own. It is excluded because it cannot be told apart from two records carrying the same value on other areas | One ring, 1.604 ac, centroid 0.06 m: validated regime |
| **Quincy Center #6**, 6758 (objectid 855) | Six parcels including 621026; land $2,047,300, the combined value of all six by MAPC's definition. Parcel 621026 is also listed by #8, whose values differ | **Valuation cannot be allocated.** Parcel 621026's value is in #6's sum and, in some form, in #8's; the split cannot be checked | Two rings. The first (0.735 ac) matches the recorded 0.73 ac and MAPC's centroid (0.08 m); the second (0.624 ac) coincides with #8's footprint. **Provisional**: whether that second ring is real is unconfirmed |
| **Quincy Center #8**, 6766 (objectid 836) | Parcel 621026, with no brackets and no address. `nparcels` = 0 contradicts it (**confirmed field error**). Land $432,800, building $3,234,600, distinct from #6. Recorded 0.62 ac; MAPC centroid 68 m from #6's | **Conservative exclusion.** Its values may be parcel 621026's alone. It is excluded because the same parcel is also valued in #6 | One ring, 0.624 ac, centroid 0.08 m: validated regime |

In short:

- **Confirmed errors:** `nparcels` = 0 on #1, #2 and #8 (and on the retained
  Braintree #7).
- **Valuation not allocatable** (the land-value indicator is not a site-level value):
  Assembly #1, Assembly #2, Quincy Center #6.
- **Conservative exclusions** (their own values may be right): Assembly #3, Quincy
  Center #8.
- **No duplicate rows.** Every pair above has different MAPC centroids (67–137 m
  apart), so nothing is de-duplicated or merged. `site_id_map.csv` keeps every original
  `site_oid` and the frozen `e18a184` display name, and no site is renumbered. Round 1's
  "one parcel recorded twice" was wrong.
- **No value was apportioned by area.** The five are left out of the main set rather
  than corrected.

**Other flagged records, all kept.** Each has its four indicators supported by the
attributes (`record_audit.csv`):

- **Braintree #7** (5992): `nparcels` = 0 (confirmed field error). Its parcel appears
  in no other site, and its geometry is in the validated regime (one ring, 0.401 ac,
  centroid 0.07 m). The anomaly is in one field only.
- **Davis #1** (10038) / **Davis #9** (10046): disjoint parcel lists and distinct
  values. Davis #1's second decoded ring overlaps #9 by 580 m². The first ring matches
  Davis #1's recorded area and MAPC centroid. Provisional, and not treated as a source
  error.
- **Sullivan Square #4, Eliot #2, Newton Highlands #3, North Quincy #8**: the recorded
  area differs from the decoded area by more than 2% (0.28 against 0.24; 3.72 against
  3.64; 0.85 against 0.52; 0.36 against 0.27 ac). The cause is unknown and could lie in
  the decoding or in how MAPC computed the area. Not treated as a source error.
- **Assembly #4** (10012), **#5** (9995): `jobs45tr` = 0 (§1.4). Kept as recorded in
  E3 and treated as unknown in E3u.

### 3.3 What the five exclusions change

Output sensitivity. It is reported alongside the data decision above and does not
replace it.

- **Where the five stood.**
  - Before exclusion, all five sat outside every top ten, in every scenario and
    reference: equal-weight ranks at S0 of 16, 16, 24, 54 and 30 for Assembly #1, #2,
    #3 and Quincy Center #6, #8.
  - None came first in any draw of any four-indicator weight space. The one exception
    is K3, where Assembly #1 = #2 split 13 identical-vector ties.
  - Assembly #1 and #2 were on the baseline four-indicator frontier.
- **Frontier.** The four-indicator frontier goes from 22 to 20 (Assembly #1 and #2
  leave; nothing enters). The five-indicator frontier stays at 54: two leave and
  Brookline Village #1 and Coolidge Corner #2 enter (`frontier_summary.csv`).
- **Baseline reference and tie rule (S0 → S1).** Every first place and every top ten is
  unchanged. Rank shifts come only from removing five rows (≤ 5 places).
- **Main rules (K3 → S3).** First places are unchanged and every top ten is identical,
  but the reference itself changes (251 → 246). The Dirichlet leader flips between two
  sites within 0.8 pt: K3 Revere Beach #1 27.0% against Malden Center #1 26.7%; S3
  Malden Center #1 26.8% against Revere Beach #1 26.1%.
- **Partial exclusion not run.** A variant that drops only the three unallocatable
  records and keeps the two conservative ones was not run. K3 (all five kept) and S3
  (all five out) bracket it, and neither end moves a first place or a top ten.
- **Job-access zeros (E3 → E3u):** same joint first, top-ten overlap 10/10, Spearman
  0.9999.

### 3.4 What the home-made geometry decoding does and does not establish

The `shape` column is an Esri ST_Geometry blob that the file does not document.
`revision/geometry.py` reads it as follows: SRID 26986, integer coordinates in units of
0.1 mm from a false origin of (−36,530,900, −28,803,200) m, delta-encoded, with a
marker between parts. The reading was worked out from the bytes. **No standard GIS
reader was available** to check it: no GDAL/OGR, QGIS, ArcGIS, shapely, pyogrio or
DuckDB in the environment. So everything below is checked against MAPC's own fields,
not against an independent reader.

| Aspect | Status | Basis |
| --- | --- | --- |
| Coordinate scale, origin and vertex order | **Validated** | Decoded area equals `sitearea_a` to 0.01 ac for 99.2% of 3,028 sites; centroid within 0.16 m of MAPC's lat/long for 99% (median 0.07 m) |
| Area and centroid of **single-ring** polygons | **Validated** where they match MAPC | Four of the five excluded records are single rings matching MAPC's area to 0.01 ac and centroid to 0.08 m |
| Non-overlap between single-ring polygons (Assembly #1–#3) | **Supported, not independently checked** | Follows from validated coordinates, but not confirmed by a standard reader |
| **Multiple parts** (the separator reading) | **Provisional** | Of 30 multi-ring records, MAPC's recorded area matches the decoded total for 12, the first ring alone for 9, neither for 9 |
| **Holes** (inner rings) | **Provisional, untested** | Rings are combined by even-odd inclusion; orientation and nesting were not checked against a reference |
| **Overlaps involving a second ring** (Quincy Center #6/#8, Davis #1/#9) | **Provisional** | Both overlaps come only from a decoded second ring. In both cases MAPC's area and centroid fit the first ring alone (0.08 m and 0.06 m), so the second ring may be a decoding artefact or a real part that MAPC's own figures ignore |
| The 25 records (0.8%) whose decoded area differs from `sitearea_a` | **Unresolved** | Could be decoding or source; not treated as source errors |

What this means for the decisions:

- The geometry is used for two things only: showing that no pair of records coincides
  (supporting "not a duplicate"), and describing the Quincy Center relationship.
- For Assembly, MAPC's own centroids (67–137 m apart) and recorded areas already rule
  out a duplicate row. The single-ring geometry agrees.
- For Quincy Center, the exclusion rests on the shared parcel ID and MAPC's definition
  of `land_value`. The two-ring picture is provisional.
- A wrong decoding would therefore change a description, not an exclusion.
- Nothing in the decoding is reported as a confirmed error in the MAPC data.

*Minimal check if wanted:* open the MAPC DataCommon 442 layer in a GIS for site_oid
6758, 6766, 10038 and 10046, and compare parts and holes. That needs a download and a
GIS tool, so it was not done.

---

## 4. Ties

### 4.1 Ties in the indicator percentiles

For a value v against a reference of n values, with L below, E equal and G above:

| Rule | Higher-is-better | Lower-is-better | Best unique value | Tied group |
| --- | --- | --- | --- | --- |
| strict (baseline) | 100·L/n | 100·(G+E)/n | 100(n−1)/n if higher-is-better; 100 if lower-is-better | bottom of its range if higher-is-better, top if lower-is-better |
| **mid-rank (main)** | 100·(L+E/2)/n | 100·(G+E/2)/n | 100(n−½)/n either way | middle of its range either way |

Checked on the data (`transform_rules.csv`):

- **Equal raw values get equal scores** under both rules.
- **Distinct raw values never share a score (0 created ties):** every candidate value
  is in its own reference.
- **Ties in the data.** Station measures take 39 distinct values across 246 sites;
  the largest group is 20 sites (Union Square). Buildable area has 105 distinct values;
  land value 246.
- **Endpoints under mid-rank and the candidate-set reference:** the best land value
  scores 99.80, the best buildable area 99.80, the best station activity 99.19 (four
  Harvard sites tied) and the best peak share 98.58 (seven Revere Beach sites tied).
  Under the strict rule the lowest peak share scores 100 but the highest activity
  98.37.
- **Spread.** Under the baseline reference, the candidates' land-value percentiles have
  a median of 8.3 (10th–90th percentile 1.1–41.7, SD 16.4). Job access has a median of
  91.8 (75.5–98.5, SD 11.5). The station measures have an SD of about 29. Under the
  candidate-set reference every indicator has an SD of about 29. This is reported as a
  property of the distributions. It is not converted into a claim about effective
  weights.

**Separate effects** (`setting_comparisons.csv`, equal weights):

| Change | First place | Top-10 shared | Spearman |
| --- | --- | --- | --- |
| Tie rule, baseline reference (S1 → S2) | Malden Center #1 → same | 10 | 1.000 |
| Tie rule, candidate-set reference (S2u → S3) | Malden Center #1 = #2 → same | 10 | 0.9999 |
| Reference, strict (S1 → S2u) | Malden Center #1 → Malden Center #1 = #2 | 7 | 0.975 |
| Reference, mid-rank (S2 → S3) | Malden Center #1 → Malden Center #1 = #2 | 7 | 0.975 |

The reference choice moves rankings; the tie rule barely does. The two effects are
reported separately and not combined.

### 4.2 Ties in the final scores

**Deterministic settings.** Scores are computed exactly as fractions: percentiles are
rational, and the weights are decimal strings. Every site sharing the exact maximum is
listed (`first_place_by_setting.csv`). The table also gives the gap to the runner-up,
in points and in *one-position steps*: the score change from moving one place on the
least-weighted indicator, which is w_min × 100/246 under the candidate-set reference.
Scores that differ, however slightly, are not ties: the checks include a pair that
floats print identically but that differ exactly, and a pair that is exactly equal but
differs in floats.

**Exact joint first places found:** Malden Center #1 = #2 under S3 (equal and
transit), S2u (equal and transit), K3 (equal and transit), E3, E3u and S3 without peak
share. The mechanism: under a candidate-set reference, #1 (10.0 ac, $596K/ac) and #2
(6.1 ac, $584K/ac) are one position apart on area and one position apart on land in
the other direction, with identical station values. Percentiles discard magnitude, so
four extra acres count the same as a hundredth of one.

**Random weights** (`weight_space` in `revision/methods.py`). Every site within 1e-9 of
the top is a joint winner. Each draw records:
- the unique winner, or the joint winners;
- a split share of 1/k to each of k joint winners, so the shares sum to one (checked in
  every run);
- the kind of tie: *identical-vector* (the sites are equal under every weighting) or
  *numerical*.

`argmax` is kept only to show where it would have differed.

| Space | Draws won outright | Identical-vector ties | Numerical ties |
| --- | --- | --- | --- |
| S0–S3, E2, E3, E3u | 100% | 0 | 0 |
| K3 (flagged records kept) | 99.99% | 13 (Assembly #1 = #2) | 0 |
| E0 (round-1 five-indicator) | 99.0% | 1,986 (Assembly #1 = #2) | 0 |

**Quincy-only** uses the same functions on the same fixed percentile rows.

**Checks** (`python revision/checks.py`, 21 of 21 pass):
- equal values get equal scores;
- direction symmetry under mid-rank, and its failure under strict;
- no created ties;
- every joint first place is listed;
- exact ties are told apart from display ties;
- split shares sum to one;
- identical vectors share their wins equally and are classified as identical-vector
  ties;
- row-order independence;
- the frontier keeps identical undominated rows.

---

## 5. Results: old against new, and which change did what

### 5.1 Named scenarios and equal weights (`first_place_by_setting.csv`)

| Position | S0 baseline | S1 + records | S2 + mid-rank | **S3 main** | Gap at S3 |
| --- | --- | --- | --- | --- | --- |
| Developer | Braintree #1 | same | same | **Malden Center #2** | 0.30 pt over Malden Center #1 (7.5 steps) |
| City | Malden Center #1 | same | same | **Malden Center #1** | 0.37 pt over #2 (9 steps) |
| Transit agency | Malden Center #1 | same | same | **Malden Center #1 = #2** | exact tie |
| Place-making | Revere Beach #1 | same | same | **Revere Beach #1** | 2.74 pt over Malden Center #1 (45 steps) |
| Equal | Malden Center #1 | same | same | **Malden Center #1 = #2** | exact tie; 1.42 pt over Malden Center #4 |

- Every change of first place comes from the reference step (S2 → S3). The same change
  appears under the strict rule (S1 → S2u).
- The developer's switch from Braintree #1 to Malden Center #2 comes with top-ten
  overlap 8/10, Spearman 0.91 and a largest move of 87 places.
- The developer and city leads at S3 are smaller than one place on a single indicator
  at full weight (0.4 pt). They are not substantive leads.

### 5.2 Weight spaces, four indicators (`weight_sensitivity*.csv`; figure `f1`)

Shares of 200,000 draws (split):

| | S0 | S1 | S2 | S2u | **S3** | K3 |
| --- | --- | --- | --- | --- | --- | --- |
| Malden Center #1 | 31.1 | 31.1 | 31.6 | 26.6 | **26.8** | 26.7 |
| Revere Beach #1 | 14.4 | 14.4 | 14.5 | 26.0 | **26.1** | 27.0 |
| Malden Center #2 | 2.6 | 2.6 | 3.1 | 20.1 | **20.1** | 20.8 |
| Braintree #1 | 33.4 | 33.4 | 33.0 | 10.1 | **10.0** | 9.1 |
| Wonderland #1 | 10.2 | 10.2 | 10.2 | 5.9 | **6.3** | 5.8 |
| Malden Center #4 | 0.4 | 0.4 | 0.6 | 4.1 | **4.2** | 3.8 |
| Harvard #1 | 5.9 | 5.9 | 5.4 | 3.6 | **3.3** | 3.4 |
| Harvard #4 | 1.4 | 1.4 | 1.3 | 3.0 | **2.7** | 3.0 |
| Sites ever first | 10 | 10 | 10 | 12 | **12** | 14 |

- The reference step produces nearly all the movement.
- At S3 the top two are 0.7 pt apart. That exceeds Monte Carlo error, but they swap
  places when the flagged records are kept (K3), so they are best read as co-leaders.
- The full list of every site that ever comes first, for every space, is in
  `weight_sensitivity_summary.csv`.

### 5.3 Five-indicator extension (historical access)

**Frontier** (`frontier_summary.csv`):
- 54 sites on 246 candidates (27 stations, 9 communities), of which 34 are added by job
  access: 17 on the Green Line, 11 in Somerville, 7 in Brookline.
- 53 sites if the two zeros are treated as unknown (E3u).
- Against 20 on the four indicators.

**Equal weights:** Malden Center #1 = #2 (exact), then Sullivan Square #1 0.29 pt
behind (3.5 steps).
- Round 1 reported Sullivan Square #1 *first* here. That came from the strict tie
  rule on the 251 and does not survive the mid-rank rule.
- Four against five under main rules: top-ten overlap 8/10, Spearman 0.93.

**Dirichlet(1,1,1,1,1):** 31 sites ever come first and 17 reach 1%. Split shares:
- E3: Malden Center #1 15.7%, Malden Center #2 12.0%, Central #1 11.5%, Harvard #1
  11.4%, Revere Beach #1 10.7%, Sullivan Square #1 8.7%, Harvard #4 8.4%.
- E3u: within 0.6 pt of E3 for every site.

The four- and five-indicator spaces are different probability spaces. A site's share
rising or falling between them is not an improvement or a deterioration.

### 5.4 Quincy only, every score held fixed (`quincy_vs_all.csv`, `quincy_weight_space.csv`; figure `f3`)

This is a controlled experiment inside the 2026 framework. It restricts which sites may
win, with percentiles computed once on the full candidate set. It does not reproduce
the 2024 model, and it neither confirms nor refutes it.

- **Deterministic settings.** In none of the 36 is the all-candidate first place in
  Quincy. The best Quincy site ranks 3rd–12th among all.
  - Main S3: developer Wollaston #1 (5th); city Quincy Center #1 (5th); transit Quincy
    Center #1 (9th); place-making Quincy Center #1 (3rd); equal Quincy Center #1 (5th).
  - Extension E3: Wollaston #1 (12th).
- **What the restriction removes** under S3 equal weights: Malden Center #1–#6,
  Revere Beach #1 and Wonderland #1. Under the extension, Sullivan Square #1 and
  Central #1 as well.
- **Weight spaces.** Quincy sites together come first in 0.37% of S0 draws, 0% of S3
  draws, 1.4% of E3 and 1.5% of E3u. Within Quincy alone, the leader is Quincy
  Center #1 (S0 39.9%, S3 72.2%) or Wollaston #1 (E3 50.1%). Even inside Quincy,
  which site leads depends on the setting.

### 5.5 Key sites (`key_site_ranks.csv`; figure `f2`)

Equal-weight rank at S0 → S3 → E3:

- Malden Center #1: 1 → 1 = → 1 =
- Malden Center #2: 2 → 1 = → 1 =
- Malden Center #4: 7 → 3 → 4
- Quincy Center #1: 6 → 5 → 14
- Revere Beach #1: 9 → 7 → 10
- Wonderland #1: 10 → 9 → 8
- Wollaston #1: 4 → 10 → 12
- Braintree #1: 3 → 11 → 33
- Sullivan Square #1: 34 → 21 → 3
- Central #1: 47 → 38 → 5
- Harvard #1: 26 → 64 → 21

---

## 6. What is stable and what depends on the setting

**Stable** across record handling, both tie rules, both references and, where tested,
four or five indicators:

- Malden Center #1 is first or jointly first under equal weights in every setting
  (S0–S3, K3, E0–E3u), and in the top two of every four-indicator weight space.
- Revere Beach #1 wins the place-making position in every setting. Malden Center #1
  wins or jointly wins the city and transit positions.
- No Quincy site comes first among all candidates in any setting.
- The tie rule changes no four-indicator first place or top ten.
- Removing the five unattributable records changes no first place or top ten.
- The four-indicator frontier is contained in the five-indicator one. Brookline has no
  four-indicator frontier site.

**Setting-dependent:**

- **The developer's first place:** Braintree #1 under the baseline reference, Malden
  Center #2 under the candidate-set one.
- **Braintree #1:** 3rd at S0, 11th at S3, 33rd at E3. Its weight-space share falls
  from 33.4% to 10.0%.
- **The four-indicator weight-space leader:** Braintree #1 (baseline), then Malden
  Center #1 and Revere Beach #1 as co-leaders (main).
- **The shape of the five-indicator ranking:** Sullivan Square #1 is 3rd and Central
  #1 5th with job access; 21st and 38th without.
- **Whether Malden Center #1 and #2 tie:** they tie exactly under the candidate-set
  reference and not under the baseline one.
- **The direction of peak share:** reversing it changes the equal-weight first place
  to Alewife #1.
- **Any single first place whose lead is a few one-position steps**: the main
  developer lead (7.5 steps), the city lead (9), and Malden Center #1 = #2 over
  Sullivan Square #1 with five indicators (3.5). None is a substantive margin. The
  place-making lead (45 steps) and the equal-weight lead of the joint winners (14
  steps) are wider, but still depend on the reference.

---

## 7. Claims: kept, narrowed, withdrawn

Round-1 decisions carried forward (full list in the round-1 register, still valid
except where noted): the regional-access exclusion argument withdrawn; the 2024
"admitted gap" claim withdrawn; the Green Line service conclusion withdrawn; the cost
analysis narrowed to an illustration; "would pay for itself" withdrawn; "scenario
winners on the frontier" reclassified as true by construction.

| Claim | Status now | Reason |
| --- | --- | --- |
| 22 undominated sites on four indicators | **Kept for the baseline; narrowed** | 20 in the main set; two of the 22 have unattributable land values |
| "Two Assembly sites are one parcel recorded twice" (round 1) | **Withdrawn** | Distinct records at MAPC centroids 67–137 m apart that carry one parcel's whole value; the decoded single-ring polygons agree (§3.2, §3.4) |
| Narrow percentile band ⇒ indicator "moves the weighted sums less than its nominal weight" (round 1) | **Withdrawn** | No definition or test of effective weight; the spread itself is kept as a finding |
| Sullivan Square #1 first with five indicators under a candidate-set reference (round 1) | **Withdrawn** | Strict-rule artefact; under mid-rank Malden Center #1 = #2 lead by 0.29 pt |
| Five indicators recommended as the main analysis (round 1) | **Superseded** | Research question bounded; job access is a pre-GLX historical measure of a different construct (§1.2) |
| Five positions, three winners (Braintree #1, Malden Center #1, Revere Beach #1) | **Kept as the historical baseline; narrowed** | Main setting: Malden Center #2, Malden Center #1, Malden Center #1 = #2, Revere Beach #1, Malden Center #1 = #2 |
| Braintree #1 33.4%, Malden Center #1 31.1% of random weightings | **Kept as the baseline; narrowed** | Main: Malden Center #1 26.8%, Revere Beach #1 26.1%, co-leaders |
| Malden Center holds the leading site across positions | **Kept** | Stable across every setting (§6) |
| Quincy-only restriction removes every all-candidate first place | **Kept, as a controlled experiment** | 36 of 36 deterministic settings; not a replication of 2024 |
| Medford lost in the 2024 postcode join | **Kept** | Verified in round 1 |
| `jobs45tr` is "2018" | **Narrowed** | MAPC documents 2016 and 2018 editions; jobs year LODES 2014 (2016 edition) or unverified; network pre-2022, no GLX |

---

## 8. Open issues that affect interpretation

1. **Peak share's direction: an unresolved method choice.** "Lower is better" is an
   exploratory preference that serves the place-making position. The bounded question
   does not adopt that position, and it is not an established property of good
   stations (§1.5). Reversing it changes the equal-weight first place to Alewife #1.
   *Decision needed:* keep it in the main analysis as a stated exploratory position
   (current, for comparability with the baseline); move it to a scenario-only role
   (the main analysis would then use three indicators, whose equal-weight first place
   is the same Malden Center #1 = #2); or replace it with a direction-free description
   of station activity.
2. **Accessibility measure.** It is pre-GLX, the edition is ambiguous and the jobs
   year is unverified for the 2018 edition. *Minimal work:* a post-2022 accessibility
   layer at the site centroids (MAPC, or a GTFS + LODES run) swapped into E3. That is
   new data production.
3. **Parcel-level evidence.** The MAPC 2015 parcel database, or MAPC itself, would
   settle how parcel 1242329 and parcel 621026 should be valued, and whether the two
   conservative exclusions (Assembly #3, Quincy Center #8) could return. *Minimal
   work:* obtain that parcel layer and check those parcels. Until then the five stay
   out of the main set, and K3 shows they change no first place or top ten.
4. **Decoded geometry beyond single rings.** Multi-part, hole and second-ring overlap
   readings are provisional (§3.4). *Minimal work:* open DataCommon 442 in a GIS for
   site_oid 6758, 6766, 10038 and 10046. No exclusion depends on the answer.
5. **Percentiles are ordinal.** They tie Malden Center #1 and #2 despite four acres'
   difference. Whether magnitude should count (log or capped-linear scores) is a
   modelling choice not made here.
6. **The 0.805 km straight-line cut.** Thirteen sites sit between 0.805 and 1 km. A
   network distance or a 1 km run would change the candidate set.
7. **Regional records.** The baseline reference keeps regional records with the same
   parcel-value pattern (13 region-wide share a parcel ID). This affects only S0–S2
   and E0–E2.
8. **The positions** are the author's; no stakeholder has reviewed them.

---

## 9. Facts for the case page, each with its source file

All paths are relative to `revision/outputs/` unless given. Each is reproduced by
the committed code.

- **Main candidate set:** 246 sites near rapid transit in 9 communities at 39
  stations. They are the 251 screened sites less five whose assessed land value
  cannot be attributed to the site. — `candidates_quality.csv`, `record_audit.csv`
- **Three Assembly records** (site_oid 9967, 9971, 9949) list the same parcel and
  carry identical assessed values (land $8,492,300) on recorded areas of 2.25, 2.25 and
  1.60 acres, at MAPC centroids 67–137 m apart. The land value per acre therefore cannot
  be allocated to any one of them. — `record_audit.csv`
- **Under the main setting, equal weights:** Malden Center #1 and #2 tie exactly for
  first; Malden Center #4 is 1.42 points behind. — `first_place_by_setting.csv`
- **Main setting, positions:** developer Malden Center #2 (by 0.30 pt), city Malden
  Center #1 (by 0.37 pt), transit Malden Center #1 = #2, place-making Revere Beach #1
  (by 2.74 pt). — `first_place_by_setting.csv`
- **Main setting, Dirichlet(1,1,1,1), seed 7, 200,000 draws:** Malden Center #1 26.8%,
  Revere Beach #1 26.1%, Malden Center #2 20.1%, Braintree #1 10.0%; 12 sites ever
  first. It is a property of the sampling scheme. — `weight_sensitivity_summary.csv`
- **Historical baseline** (unchanged, `e18a184`): Braintree #1 33.4%, Malden Center #1
  31.1%; winners Braintree #1, Malden Center #1, Revere Beach #1. —
  `revision/baseline_e18a184/`
- **Malden Center #1** is first or jointly first under equal weights in every setting
  tested. — `key_site_ranks.csv`
- **Reference choice:** ranking against the candidate set rather than the region moves
  Braintree #1 from 3rd to 11th under equal weights, and from 33.4% to 10.0% of draws.
  — `key_site_ranks.csv`, `weight_sensitivity_summary.csv`
- **Quincy-only restriction,** every score fixed: no all-candidate first place in any
  of 36 settings is in Quincy; the best Quincy site ranks 3rd–12th. A controlled
  experiment in the 2026 framework. — `quincy_vs_all.csv`
- **Job access:** MAPC's `jobs45tr` comes from the University of Minnesota
  Accessibility Observatory, and its transit network predates the Green Line
  Extension. — `indicator_dictionary.csv`
- **Station measures:** Fall 2025 daily and weekend boardings + alightings correlate at
  0.98 at site and at station level. — `internal_checks.csv`
- **Our decoding of MAPC's site polygons** reproduces the recorded site area for
  99.2% of 3,028 sites. It is a home-made reading, not checked with a standard GIS
  reader; state it as such if used. — `internal_checks.csv`, `revision/manifest.json`

**Not for the case page:**
- that any site is the best, or would pay, be approved or work;
- that a low peak share means better service, spare capacity or higher development value;
- that the decoded overlaps (Quincy Center #6/#8, Davis #1/#9) are confirmed, or are errors in the MAPC data;
- that a first-place share is a probability or a measure of support;
- that the candidate-set reference makes effective weights equal nominal ones;
- that Sullivan Square #1 leads with job access;
- that the Quincy experiment refutes the 2024 model;
- any lead smaller than a few one-position steps presented as meaningful.

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
| `revision_2026.py` | the analysis; `revision/methods.py` scoring rules; `revision/geometry.py` polygon decoding; `revision/checks.py` rule checks |
| `revision/outputs/settings.csv` | every setting: candidate set, n, reference, tie rule, indicators |
| `record_audit.csv`, `candidate_overlaps.csv`, `candidates_quality.csv`, `site_id_map.csv` | record evidence, decisions, flags, stable IDs |
| `indicator_dictionary.csv`, `transform_rules.csv` | indicator definitions and sources; percentile rules, ties and spread |
| `first_place_by_setting.csv`, `rankings_by_setting.csv`, `top10_by_setting.csv`, `setting_comparisons.csv`, `key_site_ranks.csv` | deterministic results and one-change-at-a-time comparisons |
| `weight_sensitivity.csv`, `weight_sensitivity_summary.csv`, `weight_seed_stability.csv` | every site in every weight space: unique, joint and split shares, argmax, top five, MC SE; five-seed ranges |
| `frontier_by_setting.csv`, `frontier_summary.csv` | frontiers on raw values |
| `quincy_vs_all.csv`, `quincy_weight_space.csv` | the Quincy experiment |
| `internal_checks.csv`, `summary.json`, `revision/manifest.json` | checks; headline numbers; commit, checksums, environment, seeds |
| `revision/figures/f1–f3` | first-place shares by step; key-site ranks by step; Quincy only |
| `revision/baseline_e18a184/` | the frozen historical baseline |
| `revision/archive_round1/` | round-1 tables and script, superseded (see its `NOTE.md`) |
