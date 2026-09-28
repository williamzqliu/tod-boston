# Transit-Oriented Development in Greater Boston

Massachusetts requires the 177 communities the MBTA serves to zone for multi-family
housing near a station. The law says where housing must be *allowed*. It does not say
where anyone should *build*.

This repository holds two passes at that question, two years apart, and a research
revision of the second. All of it is exploratory site screening: it compares candidate
sites on a handful of land and transit indicators and shows how far the comparison
depends on which indicators, which reference and which weights are used. None of it
shows that a site would pay, would be approved, or would work.

**The current result is the research revision's main comparison, `M3`**: three
indicators across 246 sites, set out below the next table. That table compares the two
notebooks, which are kept as history; the 2026 notebook is the four-indicator baseline
the revision reproduces.

| | [`2024-original.ipynb`](2024-original.ipynb) | [`2026-rebuild.ipynb`](2026-rebuild.ipynb) |
| --- | --- | --- |
| Unit of analysis | community, then station | **site** (a MAPC site can combine several parcels) |
| Stages | two, the first discarding seven of eight communities | one |
| Candidates | 8 communities → 4 stations | **251 sites across 9 communities** |
| Scale | min-max inside the sample | empirical percentiles: land value and buildable area against MAPC's regional records, the two station measures against the 251 candidates |
| Shortlist | none | **22 sites that no other site dominates on the four indicators, found without weights** (two of them carry the whole value of a parcel they share, see below) |
| Weights | one set, defended in prose | **five named positions** |
| Demand measured | Fall 2023 | Fall 2025, with a 2017–2025 panel behind it |
| Answer | Quincy Center | three different sites, depending on who is asking |

The 2024 notebook is the original coursework for *Statistics for Design* at
Northeastern University (Nabeel Gillani), Oct–Dec 2024, committed byte for byte as it
was submitted. It is there to be read, not re-run. The 2026 notebook is a second pass
over the same question and mostly the same data.

**Research revision, September 2026.** [`RESEARCH_REVISION_REPORT.md`](RESEARCH_REVISION_REPORT.md)
reproduces the 2026 baseline at commit `e18a184` exactly and keeps it, untouched, as
the historical baseline. It bounds the question to comparing assessed land value,
developable scale and existing station activity across a defined set of sites near
rapid transit, and to testing how far that comparison depends on modelling choices.

| | **Main comparison `M3`** | Four-indicator setting `S3` (round 2) | Accessibility extension `E3` / `E3u` | Historical baseline `S0` (`e18a184`) |
| --- | --- | --- | --- | --- |
| Role | the revision's main comparison | historical revision; a four-indicator preference scenario | historical, extends **S3**, not M3 | the original 2026 notebook, unchanged |
| Candidates | 246 (five of the 251 temporarily excluded because their assessed values cannot be reliably attributed to the site: three attribution problems, two conservative) | 246 | 246 / 244 | 251 |
| Scored indicators (preferred direction) | assessed land value/ac (lower), buildable area (larger), daily station boardings + alightings (higher); **peak share described, not scored** | the three + weekday peak share (lower) | S3's four + MAPC job access (a pre-GLX historical measure) | as S3 |
| Percentile reference, tie rule | the candidate set itself; mid-rank | same | same | land and area against the region, station measures against the 251; strict |
| Weights | equal, exactly 1/3; Dirichlet(1,1,1) | five scenarios; Dirichlet(1,1,1,1) | equal; Dirichlet(1,1,1,1,1) | as S3 |

The directions in M3 are this study's comparison preferences, not objective criteria
of TOD value. Assessed land value is not acquisition cost, and boardings plus
alightings are neither distinct riders nor future demand. Peak share is scored only in
the historical settings and in two labelled exploratory ones. Every version and setting
ID is listed in [`revision/VERSIONS.md`](revision/VERSIONS.md). The report's tables are
in [`revision/outputs/`](revision/outputs/) and the frozen baseline in
[`revision/baseline_e18a184/`](revision/baseline_e18a184/).

**Main comparison, in brief.**
- **Equal weights:** Malden Center #1 and #2 tie exactly for first.
- **Frontier:** 15 of the 246 sites are undominated on the three indicators.
- **Dirichlet(1,1,1)** (seed 7, 200,000 draws): Malden Center #1 comes first in 41.6%
  of draws, Malden Center #2 in 32.0% and Braintree #1 in 12.9%. That describes the
  sampling setting, not anyone's preferences or a probability of being best.
- **Peak share.** Where it is scored, its direction decides the equal-weight first
  place: lower preferred gives Malden Center #1 = #2, higher preferred gives
  Alewife #1.

---

## What the rebuild found, as revised

**Under the 2024 cost assumptions, land is a small share of the total.** The 2024
model gave land price the heaviest weight of its five, 30%. Re-running its arithmetic
over the 2026 scenario winners — the same 500,000 sqft building at FAR 3 on every site,
$700 a square foot, $129.5M of soft costs, and 3.83 acres at each site's assessed value
per acre — the illustrative totals differ by 0.31% while the floor area each site's
buildable area could hold at FAR 3 differs by 2.7×. That follows from holding
everything but land fixed. It is an illustration of those assumptions, not evidence
that choosing a site barely changes what a project costs.

**A two-stage funnel cannot see past its first stage.** The 2024 model ranked Malden
sixth of eight communities and stopped looking; in the 2026 framework, Malden Center
holds the site that comes first in three of five scenarios. Brookline ranked eighth,
was discarded first, and holds none of the four-indicator shortlist (five of its sites
join it when job access is added; seven in the revision's 246-site main set). Medford
never entered the 2024 model: its two stations in the 2024 list, Wellington and
Medford/Tufts, were reverse-geocoded to Somerville postcodes. The revision holds every
2026 score fixed and restricts the candidates to Quincy: in all 36 settings it tests,
that removes the all-candidate first place, and the best Quincy site ranks between 3rd
and 12th among all candidates. This is a controlled experiment inside the 2026
framework, not a re-run of the 2024 method, and it neither confirms nor refutes the 2024
model; the 2024 write-up itself does not discuss what its first stage could miss.

**MAPC's own score measures something else.** Across the candidates, their overall site
score has rank correlations of 0.57 with walk score, 0.55 with buildable area, 0.51
with job access and 0.29 with assessed land value per acre. Station activity registers
at 0.09 and peak share at −0.01. The 68 sites this model puts more than sixty places
above MAPC's ranking have a median assessed $929K an acre and 7,065 daily boardings and
alightings, and 30 are in Quincy; the 67 MAPC puts that far above this model's have
$3.40M and 770, and 29 are in Brookline. The two rankings are built from different
criteria. That they differ does not show that either one is better.

**A station name is not a station.** MAPC's inventory labels seven Somerville sites
`Washington Street`, which in the current MBTA feed is a Green Line B stop about six
kilometres away in Brighton, so joining on the name handed those sites Brighton's
ridership. Every site now goes to the nearest station with a Fall 2025 rating, which
disagrees with the MAPC label at 39 of 285 sites. Sites more than 0.805 km (half a mile)
from that station *in a straight line* leave the candidate set — twenty of them. There
is no walking network in this model.

**Two of the 2024 indicators carry nearly the same ranking.** Fall 2025 daily and
weekend station activity correlate at 0.98 across the candidate sites and at 0.98
across the 39 distinct stations behind them; buildable area and estimated capacity at
0.94. So most of the 60% that the 2024 station model put on those two ridership
measures sat on one dimension. The correlation is measured on 2026 candidates and Fall
2025 data, not on the four Quincy stations the 2024 model weighted.

**One Saturday of service data cannot rank the lines.** An earlier version of this
README concluded that the Green Line's problem is not its service. That is withdrawn.
The service file is a single Saturday (3 February 2024); its Green Line headway is a
trunk figure pooling four branches, and at a branch stop the median wait that day was
9–10 minutes, about the same as the Blue and Orange lines. What the data does show is
that, at the median, a Green Line station carries about a tenth of the Fall 2025
boardings and alightings of a station on the other lines.

**Fall 2023 was lower than Fall 2025 at most candidate stations.** Weekday boardings
and alightings are a median 12% higher in Fall 2025 than in Fall 2023, the season the
2024 model measured, across the 29 candidate stations with a Fall 2019 value. With no
2020–2022 data, the series cannot place a low point. Percentage recovery is sensitive
to its base (Riverside, not a candidate, stands at 236% of Fall 2019 while its weekday
boardings and alightings fell by 1,251 between 2023 and 2025), and absolute change
since 2023 correlates 0.85 with the Fall 2025 level, so neither became an indicator.
Neither says anything about trip purposes or why ridership moved.

**No single site is the answer.** Five positions, three winners, in the baseline:

| Position | The claim it makes | First place |
| --- | --- | --- |
| Developer, cost first | Land is paid before anything earns | Braintree #1 |
| City, housing first | The law exists to produce homes | **Malden Center #1** |
| Transit agency | Put density where the trains already run | **Malden Center #1** |
| All-day place | Shops need customers at noon (proxied by a low weekday peak share) | Revere Beach #1 |
| Equal weights | Treat the four alike (also a preference) | **Malden Center #1** |

The first four are positions I wrote on other people's behalf; no developer, city,
transit agency or place-making group has reviewed them. Under the revision's
four-indicator setting S3 they give: developer Malden Center #2, city Malden Center #1,
transit agency and equal weights Malden Center #1 and #2 tied exactly, and place-making
Revere Beach #1. In the revision's step-by-step controlled comparisons, only the step
that changes the reference and nothing else moves a first place. The record exclusions
and the tie rule move none. The developer and city leads under S3 are 0.30 and 0.37
points; gaps of this size have not been calibrated to any real decision.

Each site is named for its nearest station and numbered within it, largest buildable
area first. Several stations have more than one candidate beside them, so neither the
station name nor the acreage identifies one on its own. Where two sites at a station
have the same buildable area the number depends on the sort, so the names are frozen as
they came out at `e18a184` and
[`revision/outputs/site_id_map.csv`](revision/outputs/site_id_map.csv) maps each one to
MAPC's `site_oid`. The two same-size Assembly sites, #1 and #2, are separate records
(MAPC places them 67 m apart) that, with Assembly #3, carry identical assessed values
for one parcel they share; they are not one site entered twice, and nothing has been
merged or renumbered. The case study's map uses a short form of the same name, three letters and
the number.

Across 200,000 Dirichlet(1,1,1,1) weightings (seed 7), Braintree #1 comes first in
33.4% and Malden Center #1 in 31.1%; ten sites come first at least once, and the
baseline chart shows the seven above 0.5%. These shares describe that sampling setting
over those percentiles. They are not real preferences, not probabilities of success,
and not probabilities that a site is best. Under the revision's four-indicator S3, with
the same draws, Malden Center #1 (26.8%) and Revere Beach #1 (26.1%) are co-leaders,
swapping places if the five excluded records are kept. The main three-indicator
comparison uses a different weight space, Dirichlet(1,1,1), whose shares are not
comparable with these.

---

## Method (baseline)

```
eligibility        12 Rapid Transit Communities          a filter, not a score
      ↓
candidates         3,028 regional MAPC sites
                     581  in an eligible community
                     285  whose MAPC nearest station is rapid transit
                     265  within 0.805 km, straight line, of a station with a Fall 2025 rating
                     257  assessed land value and buildable area above zero
                     251  excluded-land overlap < 50% and flood-zone overlap < 50%, each separately
      ↓
indicators         assessed land value per acre              ·  lower is better
                   buildable acres                           ·  higher
                   daily boardings + alightings at station   ·  higher
                   weekday peak-hour share of those          ·  lower
      ↓
redundancy         drop anything correlating above 0.9 with a sibling
      ↓
shortlist          22 sites no other site dominates on the four, no weights involved
      ↓
typology           three kinds of site
      ↓
scenarios          five positions, each stated
      ↓
robustness         200,000 random weightings
      ↓
checks             against single-indicator baselines, and against MAPC's own score
```

Regional job access (jobs reachable by transit in 45 minutes, from the University of
Minnesota Accessibility Observatory via MAPC) is not one of the baseline's four. MAPC's
own documentation dates it to 2016 in one place and 2018 in another; either way its
transit network predates the Green Line Extension. The earlier argument for leaving it
out — that as a fifth criterion it lengthens the shortlist from 22 to 54 — is
withdrawn: a longer frontier means the criteria disagree, not that one of them is
invalid. The revision carries it only as a historical-accessibility extension of its
four-indicator setting S3.

Scores are empirical percentiles rather than min-max inside the shortlist, so a site's
score does not move when the shortlist does, which is what kept the 2024 scores from
being comparable to anything. In the baseline the reference differs by indicator: land
value is ranked against the 2,973 regional records with a positive value, buildable
area against all 3,028, and the two station measures against the 251 candidates.
Against the region the candidates are expensive, so their land-value percentiles sit in
a narrow low band. The revision's main comparison (M3) ranks every indicator against
the candidate set instead, with a mid-rank tie rule, and does not score peak share.

### Three kinds of site

| Type | Sites | Median land | Median buildable | Median activity | On the shortlist |
| --- | ---: | ---: | ---: | ---: | ---: |
| Big and cheap | 8 | $0.78M/ac | 10.8 ac | 5,211 | **5 (62%)** |
| Small, expensive, busy | 130 | $1.59M/ac | 0.5 ac | 8,269 | 17 (13%) |
| Small, expensive, quiet | 113 | $2.92M/ac | 0.5 ac | 745 | **0** |

Land is assessed value per acre; activity is daily boardings plus alightings at the
nearest station. Forty-five per cent of the candidate pool is in a group that reaches
the four-indicator shortlist zero times, and it is mostly the Green Line branches in
Brookline, Newton and Somerville; seven of its sites join the five-indicator frontier.
On these four indicators, what the shortlist rewards is not ridership alone but large
buildable area at a low assessed value per acre. Whether that area is one contiguous
holding is not something the data records. The three clusters come from k-means on
standardised indicators; silhouette scores rise past three clusters, and three was
chosen because three can be named.

---

## Data

Everything is in `data/` and the notebook runs offline. Each file is a snapshot: the
analysis is about particular autumns, and re-downloading today would give different
numbers. Checksums of every file are in `revision/manifest.json`.

| File | What it is | Source |
| --- | --- | --- |
| `mapc.rethinking_retail_sites.csv` | 3,028 redevelopment sites (one or more parcels each) with assessed land value, buildable area, capacity, walk score, job access (2018) and the station each sits beside | [MAPC DataCommon 442](https://datacommon.mapc.org/browser/datasets/442), Jan 2022; assessment year not stated |
| `Rethinking the Retail Strip Sites-metadata.csv` | Field dictionary for the above | MAPC |
| `Fall_2025_..._by_Hour_RouteLine_and_Stop.csv` | Rail boardings and alightings by stop, day type and hour | MBTA, Fall 2025 |
| `Fall_2024_..._by_SDP_Time_Period_....csv` | Same, by service-planning period | MBTA, Fall 2024 |
| `Fall_2023_MBTA_Rail_Ridership_Data.csv` | Same. The season the 2024 model used | MBTA, Fall 2023 |
| `Rail_Ridership_by_Season_..._and_Stop.csv` | Same, for Fall 2017, 2018 and 2019 | MBTA. Fall 2018 carries a publisher warning about track circuits |
| `2024-02-03-subway-on-time-performance-v1.parquet` | Stop-to-stop travel time, dwell and headway for one Saturday | MBTA, 3 Feb 2024 |
| `MBTA Communities.csv` | Zoning compliance data for all 177 communities | Commonwealth of Massachusetts. Vintage not recorded |
| `zoning_atlas.csv` | Zoning districts and use descriptions. Used by the 2024 notebook | [MAPC DataCommon 421](https://datacommon.mapc.org/browser/datasets/421) |
| `rtc_2020_census.csv` | 2020 population for the Rapid Transit Communities | US Census Bureau |
| `mbta_rapid_transit_shapes.csv` | The drawn geometry of the four rapid transit lines and their nine branches, simplified to 381 points | Extracted from the [MBTA GTFS feed](https://cdn.mbta.com/MBTA_GTFS.zip) |
| `zip_code_ma.csv`, `boston_subway_stations_info.csv` | ZIP crosswalk and station coordinates. The 2024 screening used the crosswalk; the 2026 rebuild uses the coordinates to attach each site to its nearest station | Assembled for this project |
| `assess_community.csv` | The 2024 model's eight-community indicator table. An output, not an input | Derived |

The field-by-field indicator dictionary — source, vintage, unit, computation,
direction, what each is a proxy for and its limits — is
[`revision/outputs/indicator_dictionary.csv`](revision/outputs/indicator_dictionary.csv).

---

## Running it

`build_2026.py` is the source of the 2026 notebook. `2026-rebuild.ipynb` is generated
from it and committed with its outputs, so the notebook renders on GitHub without being
run. Run everything from the repository root.

```bash
pip install -r requirements.txt
python build_2026.py                    # writes figures/ and outputs/
                                        # outputs/map.json feeds the case study's
                                        # interactive map
python tools/build_notebook.py          # regenerates 2026-rebuild.ipynb from
                                        # build_2026.py and executes it
```

The research revision:

```bash
python revision/reproduce_baseline.py   # runs build_2026.py exactly as it was at
                                        # e18a184, in a clean copy, and freezes its
                                        # tables in revision/baseline_e18a184/
python revision/checks.py               # 21 checks on the percentile and tie rules
python revision_2026.py                 # checks it reproduces that baseline, audits the
                                        # flagged records, then writes revision/outputs/
                                        # and revision/figures/ (about 3-4 minutes)
python tools/make_review_package.py     # optional: zips the report, code, tables and
                                        # figures into dist/ for an external reviewer
```

The historical baseline stays independently reproducible: `reproduce_baseline.py`
needs only git and the commit, not anything the revision writes.

`build_2026.py` has since had its labels and prose corrected; its computations are
unchanged, and its four `outputs/` files are byte-identical to the frozen `e18a184`
copies.

**Colab** — neither notebook fetches the repository itself. Clone it first
(`!git clone https://github.com/williamzqliu/tod-boston && %cd tod-boston`) so the paths
into `data/` resolve.

---

## Layout

```
2024-original.ipynb          the coursework, untouched
2026-rebuild.ipynb           the second pass, with outputs (the four-indicator baseline)
build_2026.py                the source the rebuild is generated from
tools/build_notebook.py      build_2026.py → 2026-rebuild.ipynb
RESEARCH_REVISION_REPORT.md  the research revision: what was checked, what changed
revision_2026.py             the revision's analysis
revision/methods.py          percentile rules, exact scoring, tie-aware weight spaces
revision/geometry.py         decodes the site polygons stored in the MAPC file
revision/checks.py           checks on those rules
revision/reproduce_baseline.py
revision/baseline_e18a184/   the frozen baseline tables, printed output and checksums
revision/outputs/            the revision's tables
revision/figures/            the revision's three charts
revision/VERSIONS.md         every version and setting ID, and which is current
revision/archive_round1/     the first revision round's tables, superseded
revision/archive_round2/     the second round's tables, figures and report, superseded
tools/make_review_package.py builds the external review bundle in dist/ (not tracked)
data/                        every input
figures/                     charts, written at 200–450 dpi (not tracked)
outputs/                     scored sites, scenario table, ridership panel (not tracked)
images/                      reference figures used by the 2024 notebook
```

## What neither version can do

Nothing here describes who lives near these sites — income, tenure, household size —
which is what anyone financing housing underwrites on first. Land values are assessed
rather than transacted, and nothing models acquisition, construction or rents, so
nothing here says whether a project would pay. Distances are straight lines from site
centroids, not walks. The indicators come from different years: ridership from Fall
2025, job access from 2018 (before the Green Line Extension opened), the MAPC inventory
from its January 2022 release. The MAPC inventory is retail strip sites, which is a good
frame for redevelopment and is not every parcel near a station, and a few of its records
are inconsistent (see the revision's quality flags). Station ridership is attributed to
every site beside it, which is defensible for a half-mile catchment and wrong at the
corner. And nobody who works in any of these municipalities has seen any of it: all five
positions in the scenario table are ones I wrote on their behalf.
