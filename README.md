# Transit-Oriented Development in Greater Boston

Massachusetts requires the 177 communities the MBTA serves to zone for multi-family
housing near a station. The law says where housing must be *allowed*. It does not say
where anyone should *build*.

This repository holds two answers to that question, two years apart.

| | [`2024-original.ipynb`](2024-original.ipynb) | [`2026-rebuild.ipynb`](2026-rebuild.ipynb) |
| --- | --- | --- |
| Unit of analysis | community, then station | **site** |
| Stages | two, the first discarding seven of eight communities | one |
| Candidates | 8 communities → 4 stations | **249 sites across 12 communities** |
| Scale | min-max inside the sample | percentile against 3,028 regional sites |
| Shortlist | none | **27-site Pareto frontier, reached with no weights** |
| Weights | one set, defended in prose | **six named positions** |
| Demand measured | Fall 2023 | Fall 2025, with a 2017–2025 panel behind it |
| Answer | Quincy Center | three different sites, depending on who is asking |

The 2024 notebook is the original coursework for *Statistics for Design* at
Northeastern University (Nabeel Gillani), Oct–Dec 2024, committed byte for byte as it
was submitted. It is there to be read, not re-run. The 2026 notebook is a second pass
over the same question and mostly the same data.

---

## What the rebuild found

**The weights were on the smallest lever.** The 2024 model gave land price the
heaviest weight of its five, 30%. Running the same cost model over each of the 2026
winners: the total cost of an identical 500,000 sqft building varies by **0.31%** from
the cheapest site to the dearest. What those sites can *hold* at a floor area ratio of
3 varies by **2.7×**. Choosing a site barely changes what it costs. It changes how much
you get.

**A two-stage funnel cannot see past its first stage.** The 2024 model ranked Malden
sixth of eight communities and stopped looking. Malden Center holds the site that wins
four of six scenarios here. Newton ranked third and holds none of the frontier.
Medford was lost in a postcode join and never entered the 2024 model at all.

**Two of the 2024 indicators were one indicator.** Average daily and average weekend
ridership correlate at 0.98 across these sites; buildable area and estimated capacity
at 0.96. Sixty per cent of that model's station-level weight sat on a single quantity
entered twice under two names.

**The Green Line's problem is not its service.** Half the candidate sites sit on Green
Line branches. Those branches have the shortest times between stops, the most frequent
service and the best regional job access in the candidate set, and roughly a tenth of
the ridership. Three independent measurements, one conclusion, and it is not the one
the reputation suggests.

**Fall 2023 was a trough.** Weekday flow at the candidate stations is a median 12%
higher in Fall 2025 than in Fall 2023, which is the season the 2024 model measured.
Six seasons of new data changed *which year the model reads*, not how many indicators
it carries: percentage recovery is an artefact of the base (Riverside "recovered" to
236% of 2019 while shedding 1,251 riders a day since 2023), and absolute growth
correlates 0.76 with ridership itself.

**No single site is the answer.** Six positions, three winners:

| Position | The claim it makes | First place |
| --- | --- | --- |
| Developer, cost first | Land is paid before anything earns | Braintree |
| City, housing first | The law exists to produce homes | **Malden Center** |
| Transit agency | Put density where the trains already run | **Malden Center** |
| All-day place | Shops need customers at noon | Revere Beach |
| Regional access | Maximise jobs reachable without a car | **Malden Center** |
| No prior, equal | I cannot tell these four apart | **Malden Center** |

Across 200,000 random weightings over the frontier, Malden Center takes first place in
31% and Braintree in 26%. Every scenario winner is on the frontier, which is the check
that the no-weights shortlist was doing real work.

---

## Method

```
eligibility        12 Rapid Transit Communities          a filter, not a score
      ↓
candidates         3,028 regional sites
                     581  in an eligible community
                     285  beside a rapid transit station
                     261  joined to Fall 2025 ridership
                     255  land value and buildable area above zero
                     249  under half excluded land or flood zone
      ↓
indicators         land price per acre      ·  lower is better
                   buildable acres          ·  higher
                   average daily riders     ·  higher
                   peak share of weekday    ·  lower
      ↓
redundancy         drop anything correlating above 0.95 with a sibling
      ↓
Pareto frontier    27 sites, no weights involved
      ↓
typology           three kinds of site
      ↓
scenarios          six positions, each stated
      ↓
robustness         200,000 random weightings
      ↓
checks             against single-indicator baselines, and against MAPC's own score
```

Scores are percentiles against all 3,028 regional sites rather than min-max inside the
shortlist, so a site's score does not move when the shortlist does — which was the
reason the 2024 scores could not be compared to anything.

### Three kinds of site

| Type | Sites | Median land | Median buildable | Median riders | On the frontier |
| --- | ---: | ---: | ---: | ---: | ---: |
| Big and cheap | 9 | $0.60M/ac | 11.5 ac | 5,211 | **7 (78%)** |
| Small, dear, busy | 141 | $1.46M/ac | 0.5 ac | 8,269 | 20 (14%) |
| Small, dear, quiet | 99 | $2.84M/ac | 0.5 ac | 745 | **0** |

Forty per cent of the candidate pool is in a group that reaches the frontier zero
times, and it is mostly the Green Line branches in Brookline, Newton and Somerville.
What is scarce is not ridership. It is a large, cheap, contiguous parcel.

---

## Data

Everything is in `data/` and the notebook runs offline. Each file is a snapshot: the
analysis is about particular autumns, and re-downloading today would give different
numbers.

| File | What it is | Source |
| --- | --- | --- |
| `mapc.rethinking_retail_sites.csv` | 3,028 redevelopment sites with land value, buildable area, capacity, walk score, job access and the station each sits beside | [MAPC DataCommon 442](https://datacommon.mapc.org/browser/datasets/442), Jan 2022 |
| `Rethinking the Retail Strip Sites-metadata.csv` | Field dictionary for the above | MAPC |
| `Fall_2025_..._by_Hour_RouteLine_and_Stop.csv` | Rail ridership by stop, day type and hour | MBTA, Fall 2025 |
| `Fall_2024_..._by_SDP_Time_Period_....csv` | Same, by service-planning period | MBTA, Fall 2024 |
| `Fall_2023_MBTA_Rail_Ridership_Data.csv` | Same. The season the 2024 model used | MBTA, Fall 2023 |
| `Rail_Ridership_by_Season_..._and_Stop.csv` | Same, for Fall 2017, 2018 and 2019 | MBTA. Fall 2018 carries a publisher warning about track circuits |
| `2024-02-03-subway-on-time-performance-v1.parquet` | Stop-to-stop travel time, dwell and headway for one Saturday | MBTA, 3 Feb 2024 |
| `MBTA Communities.csv` | Zoning compliance data for all 177 communities | Commonwealth of Massachusetts. Vintage not recorded |
| `zoning_atlas.csv` | Zoning districts and use descriptions. Used by the 2024 notebook | [MAPC DataCommon 421](https://datacommon.mapc.org/browser/datasets/421) |
| `rtc_2020_census.csv` | 2020 population for the Rapid Transit Communities | US Census Bureau |
| `zip_code_ma.csv`, `boston_subway_stations_info.csv` | ZIP crosswalk and station coordinates, used by the 2024 screening | Assembled for this project |
| `assess_community.csv` | The 2024 model's eight-community indicator table. An output, not an input | Derived |

---

## Running it

`build_2026.py` is the source. `2026-rebuild.ipynb` is generated from it and committed
with its outputs, so the notebook renders on GitHub without being run.

```bash
pip install -r requirements.txt
python build_2026.py            # writes figures/ and outputs/
```

To regenerate the notebook from the script:

```bash
python -m nbconvert --to notebook --execute --inplace 2026-rebuild.ipynb
```

**Colab** — open either notebook from GitHub and run all. The first code cell clones
the repository so the paths into `data/` resolve, and does nothing when the files are
already present.

---

## Layout

```
2024-original.ipynb   the coursework, untouched
2026-rebuild.ipynb    the second pass, with outputs
build_2026.py         the source the rebuild is generated from
data/                 every input
figures/              charts, written at 200 dpi (not tracked)
outputs/              scored sites, scenario table, ridership panel (not tracked)
images/               reference figures used by the 2024 notebook
```

## What neither version can do

Nothing here describes who lives near these sites — income, tenure, household size —
which is what anyone financing housing underwrites on first. Land values are assessed
rather than transacted. The MAPC inventory is retail strip sites, which is a good frame
for redevelopment and is not every parcel near a station. Station ridership is
attributed to every site beside it, which is right for a half-mile catchment and wrong
at the corner. And nobody who works in any of these municipalities has seen any of it:
all six positions in the scenario table are ones I wrote on their behalf.
