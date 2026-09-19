# Transit-Oriented Development in Greater Boston

A two-stage weighted model that picks one of the MBTA's 124 rapid transit stations as
the best candidate for a mixed-use transit-oriented development, and then tests how
far the answer depends on the weights I chose.

**Answer: Quincy Center.** The more useful output is the range around it, which is in
[Sensitivity](#sensitivity) below.

Written for a course at Northeastern University, Oct to Dec 2024.

---

## The question

In January 2021 Massachusetts introduced a multi-family zoning requirement for the 177
communities the MBTA serves. Each has to zone a district where multi-family housing is
permitted by right, near a transit station.

The policy says where housing must be *allowed*. It does not say where anyone should
*build*. This project treats that gap as a site-selection problem: given the whole
rapid transit network, which single station is the best place to put a TOD, and what
would it cost?

Three conditions pull against each other. Ridership has to justify the density, land
has to be cheap enough for the numbers to work, and the area has to have room to grow.
No single measure carries all three, so the answer comes from a weighted model, which
means the weights are the argument.

## Screening

| Step | Count |
| --- | --- |
| MBTA communities | 177 |
| Rapid Transit Communities | 12 |
| Rapid transit and light rail stops | 124 |
| Stops inside a Rapid Transit Community | 45 |
| Communities holding those stops | 8 |

Stations carry coordinates and communities carry names, so the two were joined by
reverse geocoding all 124 stops through Nominatim to get a postcode, then intersecting
those postcodes with the communities'. One station, Harvard, came back with the wrong
postcode and was corrected by hand. The Silver Line is excluded: it is bus rapid
transit, not rail.

## Stage one, eight communities

| Indicator | Weight | Direction | Range across the eight |
| --- | --- | --- | --- |
| Land price per acre | 30% | lower is better | Braintree $429K to Brookline $4.34M |
| Coverage of the district by station areas | 25% | higher | three at 50%, five at 90% |
| Inbound rate, boardings per resident | 20% | higher | Newton 0.15% to Revere 5.68% |
| Developable land within half a mile | 15% | higher | Revere 457 to Newton 2,833 acres |
| Existing commercial zoning districts | 10% | lower is better | Cambridge 0 to Revere 6 |

Every indicator is min-max normalised across the eight, with a smoothing term of 1e-5
on both sides of the fraction so neither end lands on exactly 0 or 1.

**Quincy 71.14**, Cambridge 65.54, Newton 62.57, Somerville 48.46, Revere 48.17,
Malden 48.12, Braintree 41.50, Brookline 39.62.

Quincy does not win on ridership; it is sixth of eight. Against Cambridge it loses
three indicators and ties a fourth, and wins on land price by enough to cover all of
them:

| Indicator | Quincy over Cambridge |
| --- | --- |
| Inbound rate | −6.36 |
| Coverage | 0.00 |
| Developable area | −1.07 |
| Commercial zoning | −1.67 |
| Land price | **+14.70** |
| **Net** | **+5.60** |

## Stage two, four stations

Inside Quincy the question changes: not whether a development is feasible, but whether
enough people pass through, across enough of the week, to keep mixed use alive.

| Indicator | Weight | Direction |
| --- | --- | --- |
| Average daily ridership | 40% | higher is better |
| Average weekend ridership | 20% | higher |
| Peak share of weekday flow | 20% | lower is better |
| Weekday to weekend ratio | 20% | lower is better |

**Quincy Center 100.00**, Wollaston 53.21, North Quincy 40.23, Quincy Adams 0.33.

Quincy Center leads on all four: 3,366 average daily riders, 1,660 at the weekend,
36.5% of its weekday flow in the two peak periods (the lowest of the four), and a
weekday-to-weekend ratio of 2.46 (the smallest gap). On four stations a min-max scale
puts the best of them at 100 by construction, so the score means *best of these four*
rather than a percentage of anything.

Quincy Adams is the contrast: a park-and-ride, worst on both spread measures on top of
the lowest ridership.

### A note on the peak measure

The ridership data cuts a weekday into nine time periods, two of which are peaks. Peak
flow divided by off-peak flow therefore compares two buckets with seven and has no
natural reference value. The **share** of the weekday arriving inside the peaks is the
quantity the indicator is about: bounded, comparable between stations, and lower is
better. Weekday-to-weekend runs the same way. Both are min-max scaled and inverted, so
every column stays inside 0 to 1 and the weighted sum is already on a 0 to 100 scale
with no offset needed.

## A first cost check

A 500,000 sqft mixed-use project, sized against local precedent rather than ambition
(119 Parkingway, seven storeys and 300 units; 1469 Hancock Street, fifteen storeys and
204). At a floor area ratio of 3 it needs about 3.8 acres.

| Line | Basis | Cost |
| --- | --- | --- |
| Construction | 500,000 sqft at $700 | $350,000,000 |
| Land | 3.8 acres at $555,520 | $2,110,977 |
| Soft costs | | $129,500,000 |
| **Total** | | **$481,610,977** |

Land is 0.44% of the total, which sits oddly beside the 30% weight the community model
gives land price. Land is a small share of the budget and a large share of the risk,
because it is paid up front.

## Sensitivity

The weights are my judgement. Nothing in the data set them, so the question worth
answering is not whether they are right but how far they can be wrong.

Sweeping one weight at a time from nothing to half the total, and sharing the
remainder among the other four in their existing proportions:

| Weight | Given | Quincy wins while | Margin |
| --- | --- | --- | --- |
| Land price | 30% | above 21.0% | 9.0 |
| Developable area | 15% | below 24.5% | 9.5 |
| Inbound rate | 20% | below 32.0% | 12.0 |
| Coverage | 25% | above 2.6% | 22.4 |
| Commercial zoning | 10% | below 32.6% | 22.6 |

Moving all five at once, over 200,000 draws: shifting each weight by up to half its
own value, Quincy wins **84.9%**. Drawing all five at random with no starting point,
it wins **27.0%**, behind Cambridge at 39.7%.

Both are true and they say different things. The recommendation holds if you accept
that land cost is the binding constraint, and that is a belief rather than a result.

## What the model cannot do

Min-max is taken inside the sample, so every score is relative to the eight
communities and four stations that were in the frame. Nothing here transfers to a
different candidate set. The station model has had no sensitivity analysis of its own.
And nobody who works in Quincy has seen any of it.

---

## Data

Everything the notebook reads is in `data/`, so it runs with no network except for one
step (see below). Each file is a snapshot: the analysis is about Fall 2023 ridership
and MAPC data as of January 2022, and re-downloading today would give different
numbers and different results.

| File | What it is | Source |
| --- | --- | --- |
| `MBTA Communities.csv` | Multi-family zoning compliance data for all 177 MBTA communities, with service category, developable station area and required coverage | Commonwealth of Massachusetts. Vintage not recorded |
| `Fall_2023_MBTA_Rail_Ridership_Data.csv` | Heavy and light rail ridership by stop, direction, day type and time period | MBTA. Fall 2023 rating, 27 Aug to 16 Dec, 112 days |
| `rtc_2020_census.csv` | 2020 population for the twelve Rapid Transit Communities | US Census Bureau, 2020 |
| `zoning_atlas.csv` | Zoning districts and their use descriptions | [MAPC Zoning Atlas](https://datacommon.mapc.org/browser/datasets/421), DataCommon dataset 421 |
| `mapc.rethinking_retail_sites.csv` | Retail strip sites with assessed land value and site area in acres, used to derive land price per acre | [MAPC Rethinking the Retail Strip Sites](https://datacommon.mapc.org/browser/datasets/442), DataCommon dataset 442. Last updated Jan 2022 |
| `Rethinking the Retail Strip Sites-metadata.csv` | Field dictionary for the above | MAPC |
| `zip_code_ma.csv` | Massachusetts ZIP to city, county and CHIA region crosswalk | Assembled for this project |
| `boston_subway_stations_info.csv` | The 124 rapid transit and light rail stops with line and coordinates | Assembled for this project |
| `assess_community.csv` | The eight-community indicator table. An output of the notebook rather than an input | Derived here |

The two MAPC files come from DataCommon, MAPC's open data portal for the 101
municipalities of Greater Boston. The two regional maps in `images/` are Boston Region
MPO figures, included for reference.

## Running it

The notebook is saved without outputs. Run all cells to regenerate them.

One step needs the network: the screening reverse-geocodes 124 stations through
Nominatim with a rate limiter, which takes a few minutes. Everything after that reads
from `data/`.

**GitHub Codespaces** — open the repo, Code → Codespaces → create, then

```bash
pip install -r requirements.txt
```

and run the notebook in the editor.

**Locally**

```bash
pip install -r requirements.txt
jupyter notebook tod-boston.ipynb
```

**Colab** — open `tod-boston.ipynb` from GitHub, then clone the repo into the runtime
so the relative paths in `data/` resolve:

```python
!git clone https://github.com/williamzqliu/tod-boston.git
%cd tod-boston
```

## Layout

```
tod-boston.ipynb    the analysis, top to bottom
data/               every input, plus the derived indicator table
images/             reference figures used in the notebook's markdown
```
