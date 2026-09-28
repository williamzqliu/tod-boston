# Research revision of the 2026 rebuild: bounded, controlled comparisons.
#
#     python revision/reproduce_baseline.py     # once: freezes the e18a184 baseline
#     python revision_2026.py
#
# Run from the repository root. Reads data/ and the frozen baseline in
# revision/baseline_e18a184/, and writes revision/outputs/ (CSV and JSON),
# revision/figures/ and revision/manifest.json. It never writes to figures/ or
# outputs/, which belong to build_2026.py.
#
# The screening, the indicators and the baseline percentile rule are
# re-implemented here rather than imported, because build_2026.py is a
# notebook source that draws every chart as it goes. Before anything else the
# script checks that the re-implementation reproduces the frozen baseline
# number for number, and stops if it does not.
#
# What this adds, and nothing more:
#   A. four indicators against five (the four plus regional job access)
#   B. the current mixed percentile reference against one fixed 251-site one
#   C. all candidate sites against Quincy's alone, with every score held fixed
#   D. the internal checks those comparisons depend on
# Distances stay straight-line, land stays assessed, and nothing new is fetched.

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import warnings

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

DATA = 'data/'
BASE = 'revision/baseline_e18a184/'
OUT = 'revision/outputs/'
FIG = 'revision/figures/'
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

BASELINE_COMMIT = 'e18a184'
SEED = 7                      # the baseline's seed, reused for both weight spaces
N_DRAWS = 200_000
SEEDS_CHECK = (7, 11, 23, 42, 2026)
TOL = 1e-9                    # scores are 0-100; anything closer than this is a tie

if not os.path.exists(BASE + 'outputs/sites_scored_2026.csv'):
    sys.exit('run `python revision/reproduce_baseline.py` first')

# Same palette and faces as build_2026.py, so the revision reads as part of the set.
INK, MUTE, FAINT = '#14120C', '#6E685A', '#E2D7BE'
ACCENT, ACCENT2 = '#D03B00', '#3E7C8A'
import glob
for _f in glob.glob('fonts/*.ttf'):
    mpl.font_manager.fontManager.addfont(_f)
INSTALLED = {f.name for f in mpl.font_manager.fontManager.ttflist}
SANS = 'Instrument Sans' if 'Instrument Sans' in INSTALLED else 'DejaVu Sans'
mpl.rcParams.update({
    'font.family': SANS, 'font.sans-serif': [SANS],
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'axes.edgecolor': MUTE, 'axes.labelcolor': INK, 'text.color': INK,
    'xtick.color': MUTE, 'ytick.color': MUTE,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': FAINT, 'grid.linewidth': 0.8,
    'axes.axisbelow': True, 'font.size': 11, 'axes.titlesize': 13,
    'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
    'axes.titlepad': 12, 'figure.dpi': 100, 'savefig.bbox': 'tight',
})


def save(name, dpi=200):
    plt.savefig(f'{FIG}{name}.png', dpi=dpi)
    plt.close()


def write(df, name, **kw):
    df.to_csv(OUT + name, index=kw.pop('index', False), lineterminator='\n', **kw)


CHECKS = []


def check(name, result, detail='', status='ok'):
    CHECKS.append(dict(check=name, result=result, detail=detail, status=status))


# ---------------------------------------------------------------------------
# 0. Provenance
# ---------------------------------------------------------------------------

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def git(*args):
    try:
        return subprocess.run(['git', *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 1. The baseline screening, re-implemented
# ---------------------------------------------------------------------------

s = pd.read_csv(DATA + 'mapc.rethinking_retail_sites.csv', low_memory=False)
s['ppa'] = s.land_value / s.sitearea_a

com = pd.read_csv(DATA + 'MBTA Communities.csv')
RTC = sorted(com.loc[com.community_category == 'Rapid Transit', 'community'])

steps = [('MAPC sites, region-wide', len(s))]
site = s[s.municipal.isin(RTC)].copy()
steps.append(('in a Rapid Transit Community', len(site)))
site = site[site.stattyp == 'Rapid Transit']
steps.append(('MAPC nearest station is rapid transit', len(site)))
site['mapc_station'] = site.statname.str.replace(' Glx', '', regex=False).str.strip()


def load_ridership(fn):
    d = pd.read_csv(DATA + fn, encoding='utf-8-sig', low_memory=False)
    d.columns = [c.lower() for c in d.columns]
    d['day_type'] = d.day_type_name.str.lower()
    d['flow'] = d.average_ons + d.average_offs     # boardings + alightings
    return d


f25 = load_ridership('Fall_2025_MBTA_Rail_Ridership_by_Hour_RouteLine_and_Stop.csv')
f25['hour'] = f25.hour_of_service.str.slice(0, 2).astype(int)
wd25, we25 = f25[f25.day_type == 'weekday'], f25[f25.day_type.isin(['saturday', 'sunday'])]
wd_flow = wd25.groupby('stop_name').flow.sum()
PEAK_HOURS = {7, 8, 9, 16, 17, 18}
we_flow = we25.groupby('stop_name').flow.sum() / 2
station = pd.DataFrame({
    'daily': (wd_flow * 5 + we_flow * 2) / 7,
    'weekend': we_flow,
    'peak_share': wd25[wd25.hour.isin(PEAK_HOURS)].groupby('stop_name').flow.sum() / wd_flow,
    'wkday_wknd': wd_flow / we_flow,
    'line': f25.groupby('stop_name').route_id.agg(lambda x: sorted(set(x))[0]),
})
station['line'] = station.line.str.split('-').str[0]

coords_all = pd.read_csv(DATA + 'boston_subway_stations_info.csv')
coords = coords_all[coords_all.stop_name.isin(station.index)].reset_index(drop=True)
KM_PER_DEG = 111.32
gap = np.hypot(
    (site.long.to_numpy()[:, None] - coords.position_x.to_numpy())
    * KM_PER_DEG * np.cos(np.radians(site.lat.to_numpy()[:, None])),
    (site.lat.to_numpy()[:, None] - coords.position_y.to_numpy()) * KM_PER_DEG)
site['station'] = coords.stop_name.to_numpy()[gap.argmin(1)]
site['station_km'] = gap.min(1)
beyond = site[site.station_km > 0.805].copy()

HALF_MILE_KM = 0.805
site = site[site.station_km <= HALF_MILE_KM]
steps.append(('within 0.805 km straight-line of a rated station', len(site)))
site = site.join(station.drop(columns='line'), on='station')
site['line'] = site.station.map(station.line)
site = site[(site.ppa > 0) & (site.buildar_ac > 0)]
steps.append(('assessed land value and buildable area above zero', len(site)))
site = site[(site.excl_p < 50) & (site.fz100_p < 50)]
steps.append(('excl_p < 50 and fz100_p < 50, each separately', len(site)))

assert [n for _, n in steps] == [3028, 581, 285, 265, 257, 251], steps

IND4 = ['ppa', 'buildar_ac', 'daily', 'peak_share']
IND5 = IND4 + ['jobs45tr']
LOWER = {'ppa', 'peak_share'}
SHORT = {'ppa': 'land value/ac', 'buildar_ac': 'buildable ac', 'daily': 'daily on+off',
         'peak_share': 'peak share', 'jobs45tr': 'jobs 45 min'}

# The display names, built exactly as the baseline builds them, then frozen.
STATION_CODE = {'Assembly': 'ASM', 'Brookline Hills': 'BRH', 'Brookline Village': 'BRV',
                'Harvard Avenue': 'HAV', 'Newton Centre': 'NEC', 'Newton Highlands': 'NEH',
                'Quincy Adams': 'QUA', 'Quincy Center': 'QUC'}


def _code_options(name):
    words = name.replace('/', ' ').replace("'", '').split()
    flat = ''.join(words)
    out = [flat[:3]]
    if len(words) > 2:
        out.append(''.join(w[0] for w in words[:3]))
    if len(words) > 1:
        out += [words[0][:2] + words[1][0], words[0][0] + words[1][:2]]
    out += [flat[:2] + flat[3:4], flat[:1] + flat[2:4]]
    return [c.upper() for c in out if len(c) == 3]


_taken, _codes = set(STATION_CODE.values()), dict(STATION_CODE)
for _st in sorted(site.station.unique()):
    if _st not in _codes:
        _codes[_st] = next(c for c in _code_options(_st) if c not in _taken)
        _taken.add(_codes[_st])
site['sid'], site['code'] = '', ''
for _st, _g in site.groupby('station'):
    _order = _g.sort_values('buildar_ac', ascending=False).index
    site.loc[_order, 'sid'] = [f'{_st} #{i}' for i in range(1, len(_order) + 1)]
    site.loc[_order, 'code'] = [f'{_codes[_st]}-{i}' for i in range(1, len(_order) + 1)]
site['site_oid'] = site.site_oid.astype(int)

# ---------------------------------------------------------------------------
# 2. Percentiles, and the check against the frozen baseline
# ---------------------------------------------------------------------------


def pct(values, base, lower, ties='baseline'):
    """Empirical percentile of each value against a reference set.

    `baseline` is the rule build_2026.py uses: the share of the reference
    strictly below the value, times 100, and 100 minus that for a
    lower-is-better indicator. Ties therefore fall on the unfavourable side for
    a higher-is-better indicator and on the favourable side for a
    lower-is-better one. `midrank` counts half of the tied reference values,
    which treats both directions alike; it is used only as a diagnostic.
    """
    b = np.sort(np.asarray(base, float))
    v = np.asarray(values, float)
    less = np.searchsorted(b, v, 'left')
    leq = np.searchsorted(b, v, 'right')
    if ties == 'baseline':
        p = less / len(b) * 100
    else:
        p = (less + (leq - less) / 2) / len(b) * 100
    return 100 - p if lower else p


REF_SETS = {
    'mixed': {'ppa': s.loc[s.ppa > 0, 'ppa'], 'buildar_ac': s.buildar_ac.dropna(),
              'jobs45tr': s.jobs45tr.dropna(), 'daily': site.daily,
              'peak_share': site.peak_share},
    'uniform': {c: site[c] for c in IND5},
}
REF_DESC = {
    'mixed': {'ppa': f'MAPC records with ppa > 0 (n={int((s.ppa > 0).sum()):,})',
              'buildar_ac': f'all MAPC records (n={s.buildar_ac.notna().sum():,})',
              'jobs45tr': f'all MAPC records (n={s.jobs45tr.notna().sum():,})',
              'daily': f'the {len(site)} candidate sites', 'peak_share': f'the {len(site)} candidate sites'},
    'uniform': {c: f'the {len(site)} candidate sites' for c in IND5},
}
PCT = {ref: pd.DataFrame({c: pct(site[c], REF_SETS[ref][c], c in LOWER) for c in IND5},
                         index=site.index) for ref in REF_SETS}
PCT_MID = {ref: pd.DataFrame({c: pct(site[c], REF_SETS[ref][c], c in LOWER, 'midrank')
                              for c in IND5}, index=site.index) for ref in REF_SETS}

SCENARIOS = {
    'Developer (cost first)': {'ppa': .50, 'buildar_ac': .25, 'daily': .15, 'peak_share': .10},
    'City (housing first)': {'buildar_ac': .50, 'ppa': .20, 'daily': .20, 'peak_share': .10},
    'Transit agency (ridership first)': {'daily': .40, 'peak_share': .30, 'ppa': .15, 'buildar_ac': .15},
    'Place-making (all-day use first)': {'peak_share': .40, 'buildar_ac': .25, 'daily': .20, 'ppa': .15},
    'No prior (all four equal)': {'ppa': .25, 'buildar_ac': .25, 'daily': .25, 'peak_share': .25},
}
SCEN_ID = dict(zip(SCENARIOS, ['developer', 'city', 'transit', 'placemaking', 'equal']))


def pareto_mask(frame, cols, lower):
    """The baseline's own frontier: weak dominance, checked against every row."""
    A = frame[cols].to_numpy(float).copy()
    for i, c in enumerate(cols):
        if c in lower:
            A[:, i] = -A[:, i]
    keep = np.ones(len(A), bool)
    for i in range(len(A)):
        if keep[i] and (np.all(A >= A[i], axis=1) & np.any(A > A[i], axis=1)).any():
            keep[i] = False
    return keep


def dominated_by(A):
    """D[i, j] is True when row j dominates row i: >= on every column, > on one.
    All columns already oriented so that higher is better."""
    ge = (A[None, :, :] >= A[:, None, :]).all(2)
    gt = (A[None, :, :] > A[:, None, :]).any(2)
    return ge & gt


def oriented(frame, cols):
    A = frame[cols].to_numpy(float).copy()
    for i, c in enumerate(cols):
        if c in LOWER:
            A[:, i] = -A[:, i]
    return A


site['pareto4'] = pareto_mask(site, IND4, LOWER)
site['pareto5'] = pareto_mask(site, IND5, LOWER)

base = pd.read_csv(BASE + 'outputs/sites_scored_2026.csv').set_index('sid')
mine = site.set_index('sid')
assert set(base.index) == set(mine.index) and len(base) == len(mine) == 251
for c in ['long', 'lat', 'sitearea_a', 'buildar_ac', 'ppa', 'daily', 'peak_share',
          'jobs45tr', 'regipctile', 'station_km']:
    a, b = mine.loc[base.index, c].to_numpy(float), base[c].to_numpy(float)
    assert np.allclose(a, b, rtol=1e-12, atol=0, equal_nan=True), c
assert (mine.loc[base.index, 'pareto4'].to_numpy() == base.pareto.to_numpy()).all()
for name, w in SCENARIOS.items():
    mine_sc = sum(PCT['mixed'][c] * v for c, v in w.items())
    mine_sc.index = site.sid
    assert np.allclose(mine_sc.loc[base.index].to_numpy(), base[name].to_numpy(),
                       rtol=0, atol=1e-9), name
for c in ['municipal', 'station', 'line']:
    assert (mine.loc[base.index, c] == base[c]).all(), c
check('re-implementation reproduces frozen e18a184 sites_scored_2026.csv',
      'yes', '251 site names, coordinates, all indicators, frontier flags and all five '
      'scenario scores match to 1e-9')

top5_base = pd.read_csv(BASE + 'outputs/scenario_top5.csv')

# ---------------------------------------------------------------------------
# 3. Stable identifiers and quality flags
# ---------------------------------------------------------------------------

pids = s.parcelids.astype(str).apply(lambda x: re.findall(r'\d+', x))
exp = pd.DataFrame({'site_oid': np.repeat(s.site_oid.astype(int).to_numpy(), pids.str.len()),
                    'pid': np.concatenate(pids.to_numpy())})
sharing = exp.merge(exp, on='pid', suffixes=('', '_other'))
sharing = sharing[sharing.site_oid != sharing.site_oid_other]
shared_with = sharing.groupby('site_oid').site_oid_other.apply(lambda x: sorted(set(x)))
oid_to_sid = site.set_index('site_oid').sid

DUP_COLS = ['parcelids', 'land_value', 'bldg_value', 'sitearea_a', 'buildar_ac', 'jobs45tr']
dup_key = site[DUP_COLS].astype(str).agg('|'.join, axis=1)
dup_groups = site.groupby(dup_key).site_oid.apply(list)
dup_groups = dup_groups[dup_groups.str.len() > 1]
duplicate_of = {o: [p for p in g if p != o] for g in dup_groups for o in g}

n_same_station = site.groupby('station').site_oid.transform('size')

q = pd.DataFrame(index=site.index)
q['flag_nparcels_zero'] = site.nparcels == 0
q['flag_parcel_shared'] = site.site_oid.isin(shared_with.index)
q['flag_duplicate_record'] = site.site_oid.isin(duplicate_of)
q['flag_jobs45tr_zero'] = site.jobs45tr == 0
q['flag_station_differs_from_mapc'] = site.station != site.mapc_station


def _flags(i):
    out = []
    if q.flag_duplicate_record[i]:
        out.append('duplicate_record_suspected')
    if q.flag_nparcels_zero[i]:
        out.append('nparcels_zero_meaning_unknown')
    if q.flag_parcel_shared[i]:
        out.append('parcel_id_also_in_another_site')
    if q.flag_jobs45tr_zero[i]:
        out.append('jobs45tr_zero_suspected_missing')
    return ';'.join(out)


cand = pd.DataFrame({
    'site_oid': site.site_oid, 'objectid': site.objectid, 'sid': site.sid, 'code': site.code,
    'municipal': site.municipal, 'station': site.station, 'mapc_station': site.mapc_station,
    'line': site.line, 'straight_line_km': site.station_km.round(4),
    'nparcels': site.nparcels.astype(int), 'parcelids': site.parcelids,
    'land_value': site.land_value, 'sitearea_a': site.sitearea_a,
    'ppa': site.ppa, 'buildar_ac': site.buildar_ac, 'daily': site.daily,
    'weekend': site.weekend, 'peak_share': site.peak_share, 'jobs45tr': site.jobs45tr,
    'excl_p': site.excl_p, 'fz100_p': site.fz100_p, 'regipctile': site.regipctile,
    'sites_sharing_station': n_same_station,
    'frontier4': site.pareto4, 'frontier5': site.pareto5,
})
cand = cand.join(q)
cand['parcel_shared_with'] = site.site_oid.map(
    lambda o: ' '.join(f'{p}' + (f' ({oid_to_sid[p]})' if p in oid_to_sid.index else ' (not a candidate)')
                       for p in shared_with.get(o, [])))
cand['duplicate_of'] = site.site_oid.map(lambda o: ' '.join(f'{p} ({oid_to_sid[p]})'
                                                           for p in duplicate_of.get(o, [])))
cand['quality_flags'] = [_flags(i) for i in site.index]
cand['quality_status'] = np.where(cand.quality_flags == '', 'ok',
                                  np.where(q.flag_nparcels_zero, 'unknown', 'check'))
write(cand.sort_values(['station', 'sid']), 'candidates_quality.csv')

idmap = cand[['site_oid', 'objectid', 'sid', 'code', 'station', 'mapc_station', 'municipal',
              'line', 'nparcels', 'parcelids', 'quality_flags']].copy()
idmap['long'], idmap['lat'] = site.long, site.lat
idmap['sid_source'] = f'build_2026.py at {BASELINE_COMMIT}: station, then #n by buildable area, largest first'
write(idmap.sort_values(['station', 'sid']), 'site_id_map.csv')

# Ties in buildable area inside a station make the #n order depend on the sort.
tied_acres = site[site.duplicated(['station', 'buildar_ac'], keep=False)].sort_values(['station', 'sid'])
check('buildable-area ties inside a station (numbering then depends on sort order)',
      f'{len(tied_acres)} sites',
      '; '.join(f'{r.sid} = site_oid {r.site_oid}' for r in tied_acres.itertuples())
      + '. Names are frozen from the baseline and every table carries site_oid.',
      'note')

# ---------------------------------------------------------------------------
# 4. Indicator dictionary
# ---------------------------------------------------------------------------

DICT = [
    dict(column='ppa', name='Assessed land value per acre', source='MAPC Rethinking the Retail Strip Sites (DataCommon 442)',
         vintage='dataset published Jan 2022; assessment year not stated in the file', unit='USD per acre',
         computation='land_value / sitearea_a (site = one or more parcels; land_value is the sum over its parcels)',
         direction='lower is better', proxy_for='land-cost exposure',
         limitations='Assessed for taxation, not a transaction or acquisition price; excludes building value, '
                     'demolition, relocation and holding costs. MAPC landv_pac is a municipal-level figure '
                     '(one value per municipality in most cases) and is not used. Some records carry a whole '
                     "parcel's value on part of it (see quality flags)."),
    dict(column='buildar_ac', name='Buildable area', source='MAPC 442', vintage='as published Jan 2022',
         unit='acres', computation='MAPC field buildar_ac, used as is', direction='higher is better',
         proxy_for='how much could be built', limitations='MAPC method; site may be several parcels, so '
         'area is not evidence of a single owner or of contiguity'),
    dict(column='daily', name='Average daily boardings + alightings at the nearest rated station',
         source='MBTA Fall 2025 rail ridership by hour, route/line and stop', vintage='Fall 2025',
         unit='boardings + alightings per average day',
         computation='(5 x weekday + 2 x mean(Saturday, Sunday)) / 7 of the sum over hours, routes and '
                     'directions of average_ons + average_offs; hourly averages are rounded in the source',
         direction='higher is better', proxy_for='station activity',
         limitations='A count of on and off movements, not of distinct riders: a round trip counts up to '
                     'four times across two stations. Station-level: every site at a station gets the same '
                     'value. Not MBTA\'s average_flow field, which is on-board load.'),
    dict(column='peak_share', name='Weekday peak-hour share of boardings + alightings', source='MBTA Fall 2025, as above',
         vintage='Fall 2025', unit='share (0-1)',
         computation='weekday flow in hours 07-09 and 16-18 (six hours) / all weekday flow; hours chosen '
                     'as the window that best matches the Fall 2024 AM/PM peak periods (r = 0.958)',
         direction='lower is better', proxy_for='how concentrated weekday activity is in the peaks',
         limitations='Says nothing about weekends or about how even the off-peak hours are; it is not a '
                     'measure of all-day demand. Station-level.'),
    dict(column='jobs45tr', name='Jobs reachable by transit within 45 minutes (AM peak)', source='MAPC 442',
         vintage='2018 per the MAPC field dictionary', unit='jobs',
         computation='MAPC field jobs45tr, used as is', direction='higher is better',
         proxy_for='regional access to employment',
         limitations='2018 network: predates the Green Line Extension (opened 2022), so GLX-adjacent sites '
                     'are measured without it. Two Assembly sites carry 0, almost certainly missing. Used in '
                     'the five-indicator setting only.'),
    dict(column='station_km', name='Straight-line distance to nearest rated station', source='boston_subway_stations_info.csv',
         vintage='station list as assembled for the project', unit='km',
         computation='equirectangular approximation between the site centroid and station coordinates, '
                     'nearest station among those with a Fall 2025 rating',
         direction='filter only (<= 0.805 km)', proxy_for='proximity to the station',
         limitations='Not a walking-network distance; centroid, not parcel edge. The baseline labelled this '
                     'a "half-mile walk".'),
    dict(column='excl_p', name='Overlap with non-buildable area', source='MAPC 442', vintage='as published',
         unit='% of site area', computation='MAPC field', direction='filter only (< 50)',
         proxy_for='physical constraint',
         limitations='Applied separately from fz100_p; neither is a permitting or feasibility test'),
    dict(column='fz100_p', name='Overlap with FEMA 1% annual-chance flood zone', source='MAPC 442', vintage='as published',
         unit='% of site area', computation='MAPC field', direction='filter only (< 50)',
         proxy_for='flood exposure',
         limitations='Applied separately from excl_p (each < 50, not their sum); not a permitting test'),
    dict(column='weekend', name='Average weekend-day boardings + alightings', source='MBTA Fall 2025', vintage='Fall 2025',
         unit='per weekend day', computation='mean of Saturday and Sunday totals', direction='not used',
         proxy_for='weekend station activity', limitations='Dropped as redundant with daily; see checks'),
]
dictionary = pd.DataFrame(DICT)
dictionary['reference_mixed'] = dictionary.column.map(REF_DESC['mixed']).fillna('')
dictionary['reference_uniform'] = dictionary.column.map(REF_DESC['uniform']).fillna('')
dictionary['in_4ind'] = dictionary.column.isin(IND4)
dictionary['in_5ind'] = dictionary.column.isin(IND5)
write(dictionary, 'indicator_dictionary.csv')

# ---------------------------------------------------------------------------
# 5. What the transform does: ties it creates, spread it leaves
# ---------------------------------------------------------------------------

rows = []
for ref in REF_SETS:
    for c in IND5:
        raw, p = site[c], PCT[ref][c]
        g = pd.DataFrame({'raw': raw, 'p': p.round(9)})
        pairs_same_p = int((g.groupby('p').size() * (g.groupby('p').size() - 1) / 2).sum())
        pairs_same_raw = int((g.groupby('raw').size() * (g.groupby('raw').size() - 1) / 2).sum())
        mid_gap = (PCT[ref][c] - PCT_MID[ref][c]).abs()
        rows.append(dict(reference=ref, indicator=c, reference_set=REF_DESC[ref][c],
                         distinct_raw=raw.nunique(), distinct_percentile=g.p.nunique(),
                         tied_pairs_raw=pairs_same_raw,
                         tied_pairs_created_by_transform=pairs_same_p - pairs_same_raw,
                         largest_tie_group=int(g.groupby('p').size().max()),
                         pct_min=p.min(), pct_p10=p.quantile(.1), pct_median=p.median(),
                         pct_p90=p.quantile(.9), pct_max=p.max(), pct_sd=p.std(),
                         max_gap_vs_midrank=mid_gap.max()))
transform = pd.DataFrame(rows)
write(transform.round(3), 'transform_ties_and_spread.csv')

# ---------------------------------------------------------------------------
# 6. Settings, scores and ranks
# ---------------------------------------------------------------------------

SETTINGS = []
for ref in ('mixed', 'uniform'):
    for name, w in SCENARIOS.items():
        SETTINGS.append(dict(id=f'4ind_{ref}_{SCEN_ID[name]}', k=4, ref=ref, weights=w,
                             label=f'{name} | 4 ind | {ref}'))
    SETTINGS.append(dict(id=f'5ind_{ref}_equal', k=5, ref=ref,
                         weights={c: 0.2 for c in IND5}, label=f'Equal (five) | 5 ind | {ref}'))
SET = {d['id']: d for d in SETTINGS}


def score(setting, P=None):
    P = PCT[setting['ref']] if P is None else P
    return sum(P[c] * w for c, w in setting['weights'].items()).round(9)


SCORES = pd.DataFrame({d['id']: score(d) for d in SETTINGS}, index=site.index)
RANKS = SCORES.rank(ascending=False, method='min').astype(int)
SID = site.sid


def firsts(sc):
    """Every site at the top, joined with ' = ' when there is a tie. idxmax
    would quietly return whichever of them comes first in the table."""
    return ' = '.join(SID[i] for i in sc[sc >= sc.max() - TOL].index)

wide = cand[['site_oid', 'sid', 'code', 'municipal', 'station', 'line', 'frontier4', 'frontier5',
             'quality_flags'] + IND5].copy()
for ref in REF_SETS:
    for c in IND5:
        wide[f'pct_{ref}_{c}'] = PCT[ref][c].round(4)
for d in SETTINGS:
    wide[f'score_{d["id"]}'] = SCORES[d['id']].round(4)
    wide[f'rank_{d["id"]}'] = RANKS[d['id']]
write(wide.sort_values('rank_4ind_mixed_equal'), 'rankings_by_setting.csv')

top_rows = []
for d in SETTINGS:
    r = RANKS[d['id']]
    for i in r[r <= 10].sort_values().index:
        top_rows.append(dict(setting=d['id'], indicators=d['k'], reference=d['ref'],
                             weights=' '.join(f'{c}={w:g}' for c, w in d['weights'].items()),
                             rank=int(r[i]), sid=SID[i], site_oid=site.site_oid[i],
                             municipal=site.municipal[i], score=round(SCORES[d['id']][i], 3),
                             tied=int((SCORES[d['id']] == SCORES[d['id']][i]).sum()) > 1))
top10 = pd.DataFrame(top_rows)
write(top10, 'top10_by_setting.csv')

# The baseline top five, reproduced: nlargest breaks ties by row order, so say where it did.
for name in SCENARIOS:
    sc = SCORES[f'4ind_mixed_{SCEN_ID[name]}']
    top = sc.nlargest(5)
    mine5 = [SID[i] for i in top.index]
    theirs = top5_base[top5_base.scenario == name].sort_values('rank').site.tolist()
    assert mine5 == theirs, (name, mine5, theirs)
    tied = sc[(sc >= top.iloc[-1] - TOL) & sc.duplicated(keep=False)]
    if len(tied):
        check(f'baseline top five "{name}" contains or borders tied scores', f'{len(tied)} sites',
              ', '.join(SID[i] for i in tied.index) + '; nlargest ordered them by row position', 'note')
check('baseline scenario top fives reproduced', 'yes', 'all five scenarios, same sites in the same order')


def compare(a, b, what):
    ra, rb = RANKS[a], RANKS[b]
    ta, tb = set(ra[ra <= 10].index), set(rb[rb <= 10].index)
    return dict(setting_a=a, setting_b=b, what_changes=what,
                first_a=firsts(SCORES[a]), first_b=firsts(SCORES[b]),
                same_first=firsts(SCORES[a]) == firsts(SCORES[b]),
                top10_overlap=len(ta & tb), top10_size_a=len(ta), top10_size_b=len(tb),
                top10_only_a='; '.join(SID[i] for i in sorted(ta - tb, key=lambda i: ra[i])),
                top10_only_b='; '.join(SID[i] for i in sorted(tb - ta, key=lambda i: rb[i])),
                spearman=round(SCORES[a].corr(SCORES[b], method='spearman'), 4),
                kendall_tau_b=round(SCORES[a].corr(SCORES[b], method='kendall'), 4),
                median_abs_rank_shift=float((ra - rb).abs().median()),
                max_abs_rank_shift=int((ra - rb).abs().max()),
                sites_moving_20_plus=int(((ra - rb).abs() >= 20).sum()))


comparisons = [compare('4ind_mixed_equal', '4ind_uniform_equal', 'reference set (4 ind, equal)'),
               compare('5ind_mixed_equal', '5ind_uniform_equal', 'reference set (5 ind, equal)'),
               compare('4ind_mixed_equal', '5ind_mixed_equal', 'indicator set (mixed ref, equal)'),
               compare('4ind_uniform_equal', '5ind_uniform_equal', 'indicator set (uniform ref, equal)')]
for name in SCENARIOS:
    if SCEN_ID[name] != 'equal':
        comparisons.append(compare(f'4ind_mixed_{SCEN_ID[name]}', f'4ind_uniform_{SCEN_ID[name]}',
                                   f'reference set (4 ind, {name})'))
comparisons = pd.DataFrame(comparisons)
write(comparisons, 'setting_comparisons.csv')

# Tie-rule diagnostic: the same settings with mid-rank percentiles.
tie_rows = []
for d in SETTINGS:
    alt = score(d, PCT_MID[d['ref']])
    ra, rb = RANKS[d['id']], alt.rank(ascending=False, method='min')
    tie_rows.append(dict(setting=d['id'], first_baseline_rule=firsts(SCORES[d['id']]),
                         first_midrank_rule=firsts(alt.round(9)),
                         top10_overlap=len(set(ra[ra <= 10].index) & set(rb[rb <= 10].index)),
                         spearman=round(SCORES[d['id']].corr(alt, method='spearman'), 4),
                         max_abs_rank_shift=int((ra - rb).abs().max())))
write(pd.DataFrame(tie_rows), 'tie_rule_diagnostic.csv')

# ---------------------------------------------------------------------------
# 7. A. Four indicators against five: the frontier
# ---------------------------------------------------------------------------

A4, A5 = oriented(site, IND4), oriented(site, IND5)
D4, D5 = dominated_by(A4), dominated_by(A5)
check('frontier: baseline loop agrees with an independent pairwise dominance matrix',
      'yes' if ((~D4.any(1)) == site.pareto4.to_numpy()).all()
      and ((~D5.any(1)) == site.pareto5.to_numpy()).all() else 'NO',
      f'4 ind: {site.pareto4.sum()} sites; 5 ind: {site.pareto5.sum()} sites')
assert ((~D4.any(1)) == site.pareto4.to_numpy()).all()
assert ((~D5.any(1)) == site.pareto5.to_numpy()).all()
check('four-indicator frontier is contained in the five-indicator frontier',
      'yes' if not (site.pareto4 & ~site.pareto5).any() else 'NO',
      'guaranteed unless two sites tie on all four and differ on jobs45tr')

for ref in REF_SETS:
    for k, cols in ((4, IND4), (5, IND5)):
        fp = ~dominated_by(PCT[ref][cols].to_numpy()).any(1)
        fr = site[f'pareto{k}'].to_numpy()
        check(f'frontier recomputed on {ref}-reference percentiles, {k} indicators',
              f'{fp.sum()} sites (raw: {fr.sum()})',
              'identical membership' if (fp == fr).all() else
              'differs: ' + ', '.join(SID.iloc[np.where(fp != fr)[0]]),
              'ok' if (fp == fr).all() else 'note')

vec4 = site[IND4].round(12).astype(str).agg('|'.join, axis=1)
same4 = site[vec4.duplicated(keep=False)]
check('candidates with identical values on all four indicators',
      f'{len(same4)} sites',
      '; '.join(f'{g.sid.tolist()}' for _, g in same4.groupby(vec4[vec4.duplicated(keep=False)])),
      'note' if len(same4) else 'ok')

front = cand[cand.frontier4 | cand.frontier5].copy()
front['membership'] = np.select([front.frontier4 & front.frontier5, front.frontier5],
                                ['both', 'added_in_5'], 'dropped_in_5')
pos = {i: n for n, i in enumerate(site.index)}
front['n_dominators_4ind'] = [int(D4[pos[i]].sum()) for i in front.index]
front['dominated_4ind_by'] = [' '.join(SID.iloc[np.where(D4[pos[i]])[0]].tolist()) for i in front.index]
for ref in REF_SETS:
    for c in IND5:
        front[f'pct_{ref}_{c}'] = PCT[ref].loc[front.index, c].round(2)
front['rank_4ind_mixed_equal'] = RANKS.loc[front.index, '4ind_mixed_equal']
front['rank_5ind_mixed_equal'] = RANKS.loc[front.index, '5ind_mixed_equal']
front['rank_5ind_uniform_equal'] = RANKS.loc[front.index, '5ind_uniform_equal']
cols = ['site_oid', 'sid', 'code', 'municipal', 'station', 'line', 'membership', 'frontier4',
        'frontier5'] + IND5 + ['n_dominators_4ind', 'dominated_4ind_by',
                               'rank_4ind_mixed_equal', 'rank_5ind_mixed_equal',
                               'rank_5ind_uniform_equal', 'quality_flags'] + \
       [c for c in front.columns if c.startswith('pct_')]
write(front[cols].sort_values(['membership', 'rank_5ind_mixed_equal']), 'frontier_4v5.csv')

added = site[site.pareto5 & ~site.pareto4]
f4 = site[site.pareto4]
profile = pd.DataFrame({
    'all 251 candidates': site[IND5].median(),
    'four-indicator frontier': f4[IND5].median(),
    'added by the fifth indicator': added[IND5].median(),
}).T
profile['sites'] = [len(site), len(f4), len(added)]
profile['communities'] = [site.municipal.nunique(), f4.municipal.nunique(), added.municipal.nunique()]
profile['stations'] = [site.station.nunique(), f4.station.nunique(), added.station.nunique()]
profile['jobs45tr_pct_mixed_median'] = [PCT['mixed'].jobs45tr.median(),
                                        PCT['mixed'].loc[f4.index, 'jobs45tr'].median(),
                                        PCT['mixed'].loc[added.index, 'jobs45tr'].median()]
profile['median_4ind_equal_rank'] = [RANKS['4ind_mixed_equal'].median(),
                                     RANKS.loc[f4.index, '4ind_mixed_equal'].median(),
                                     RANKS.loc[added.index, '4ind_mixed_equal'].median()]
write(profile.round(3).reset_index(names='group'), 'frontier_profile.csv')

geo = pd.DataFrame({'candidates': site.municipal.value_counts(),
                    'frontier4': f4.municipal.value_counts(),
                    'frontier5': site[site.pareto5].municipal.value_counts(),
                    'added_in_5': added.municipal.value_counts()}).fillna(0).astype(int)
geo = geo.sort_values(['frontier5', 'frontier4'], ascending=False)
write(geo.reset_index(names='municipal'), 'frontier_by_community.csv')

# ---------------------------------------------------------------------------
# 8. Weight sensitivity, with ties counted rather than resolved by row order
# ---------------------------------------------------------------------------


def weight_space(P, draws, chunk=25_000):
    """First-place and top-five shares over sampled weightings.

    A draw where several sites share the maximum (within TOL) splits its
    credit equally among them, and is counted, instead of going to whichever
    comes first in the table as `argmax` would. The argmax share is kept only
    to compare with the baseline's own number.
    """
    n, m = len(draws), P.shape[0]
    frac, strict, argm, top5 = (np.zeros(m) for _ in range(4))
    tied, max_tie = 0, 1
    for a in range(0, n, chunk):
        S = draws[a:a + chunk] @ P.T
        mx = S.max(1, keepdims=True)
        at = S >= mx - TOL
        c = at.sum(1)
        frac += (at / c[:, None]).sum(0)
        strict += at[c == 1].sum(0)
        tied += int((c > 1).sum())
        max_tie = max(max_tie, int(c.max()))
        argm += np.bincount(S.argmax(1), minlength=m)
        if m > 5:
            v5 = np.partition(S, m - 5, axis=1)[:, m - 5:m - 4]
            top5 += (S >= v5 - TOL).sum(0)
        else:
            top5 += len(S)
    return dict(first=frac / n, strict=strict / n, argmax=argm / n, top5=top5 / n,
                tied_draws=tied, max_tie=max_tie)


def dirichlet(k, seed):
    return np.random.default_rng(seed).dirichlet(np.ones(k), N_DRAWS)


DRAWS = {4: dirichlet(4, SEED), 5: dirichlet(5, SEED)}
WS_SETTINGS = [(k, ref) for k in (4, 5) for ref in ('mixed', 'uniform')]
WS = {}
ws_rows, ws_summary = [], []
for k, ref in WS_SETTINGS:
    cols = IND4 if k == 4 else IND5
    res = weight_space(PCT[ref][cols].to_numpy(), DRAWS[k])
    WS[(k, ref)] = res
    key = f'{k}ind_{ref}'
    for n, i in enumerate(site.index):
        ws_rows.append(dict(setting=key, indicators=' '.join(cols), alpha='(' + ','.join(['1'] * k) + ')',
                            seed=SEED, n_draws=N_DRAWS, site_oid=site.site_oid[i], sid=SID[i],
                            municipal=site.municipal[i], station=site.station[i],
                            on_frontier=bool(site[f'pareto{k}'][i]),
                            first_share=res['first'][n], first_share_unique_max=res['strict'][n],
                            first_share_argmax=res['argmax'][n], top5_share=res['top5'][n],
                            mc_se=np.sqrt(res['first'][n] * (1 - res['first'][n]) / N_DRAWS)))
    sh = pd.Series(res['first'], index=SID.values).sort_values(ascending=False)
    ever = sh[sh > 0]
    ws_summary.append(dict(setting=key, indicators=k, reference=ref, alpha='(' + ','.join(['1'] * k) + ')',
                           seed=SEED, n_draws=N_DRAWS, sites_ever_first=len(ever),
                           sites_above_0_5pct=int((sh > 0.005).sum()),
                           tied_draws=res['tied_draws'], largest_tie=res['max_tie'],
                           non_frontier_first_share=float(res['first'][~site[f'pareto{k}'].to_numpy()].sum()),
                           first=ever.index[0], first_share=round(ever.iloc[0], 4),
                           second=ever.index[1], second_share=round(ever.iloc[1], 4),
                           all_sites_ever_first='; '.join(f'{nm} {v:.4f}' for nm, v in ever.items())))
ws_long = pd.DataFrame(ws_rows)
write(ws_long, 'weight_sensitivity.csv')
ws_summary = pd.DataFrame(ws_summary)
write(ws_summary, 'weight_sensitivity_summary.csv')

# The baseline number, the baseline way: argmax over the frontier rows only.
F = site[site.pareto4]
PF = PCT['mixed'].loc[F.index, IND4].to_numpy()
wins = np.bincount(np.argmax(DRAWS[4] @ PF.T, axis=1), minlength=len(F)) / N_DRAWS
b_share = pd.Series(wins, index=F.sid).sort_values(ascending=False)
printed = {}
with open(BASE + 'run_stdout.txt', encoding='utf-8') as fh:
    lines = fh.read().splitlines()
start = lines.index('sid') + 1
for ln in lines[start:]:
    m = re.match(r'^(.+?#\d+)\s+(0\.\d+)$', ln)
    if not m:
        break
    printed[m.group(1)] = float(m.group(2))
repro = b_share[b_share > 0.005].round(3).to_dict()
assert repro == printed, (repro, printed)
same_as_tieaware = np.allclose(b_share.reindex(SID.values).fillna(0).to_numpy(),
                               WS[(4, 'mixed')]['first'])
check('baseline Dirichlet(1,1,1,1), seed 7, 200,000 draws reproduced',
      'yes', f'{len(printed)} printed shares match; {int((b_share > 0).sum())} sites rank first at least once, '
             f'{int((b_share > 0.005).sum())} above 0.5% (the baseline chart shows only these)')
check('baseline first-place shares equal the tie-aware shares over all 251 sites',
      'yes' if same_as_tieaware else 'NO',
      f'tied draws: {WS[(4, "mixed")]["tied_draws"]}; restricting to the frontier loses nothing because a '
      'dominated site can at best tie its dominator')

seed_rows = []
for k, ref in WS_SETTINGS:
    cols = IND4 if k == 4 else IND5
    P = PCT[ref][cols].to_numpy()
    per = {sd: weight_space(P, dirichlet(k, sd))['first'] for sd in SEEDS_CHECK}
    for n, i in enumerate(site.index):
        vals = [per[sd][n] for sd in SEEDS_CHECK]
        if max(vals) > 0:
            seed_rows.append(dict(setting=f'{k}ind_{ref}', sid=SID[i], site_oid=site.site_oid[i],
                                  **{f'seed_{sd}': v for sd, v in zip(SEEDS_CHECK, vals)},
                                  min=min(vals), max=max(vals), range=max(vals) - min(vals)))
seed_stab = pd.DataFrame(seed_rows)
write(seed_stab, 'weight_seed_stability.csv')

# Key sites: anything that comes first somewhere, or holds 1% of a weight space,
# plus the 2024 answer and the duplicated pair.
key = set()
for d in SETTINGS:
    key |= set(SCORES.index[SCORES[d['id']] >= SCORES[d['id']].max() - TOL])
for res in WS.values():
    key |= set(site.index[res['first'] >= 0.01])
key |= set(site.index[site.sid.isin(['Quincy Center #1']) | q.flag_duplicate_record])
ks = wide.loc[sorted(key, key=lambda i: RANKS['4ind_mixed_equal'][i]),
              ['site_oid', 'sid', 'municipal', 'frontier4', 'frontier5', 'quality_flags']].copy()
for d in SETTINGS:
    ks[f'rank_{d["id"]}'] = RANKS.loc[ks.index, d['id']]
for (k, ref), res in WS.items():
    ks[f'first_share_{k}ind_{ref}'] = pd.Series(res['first'], index=site.index).loc[ks.index].round(4)
write(ks, 'key_site_ranks.csv')

# ---------------------------------------------------------------------------
# 9. C. All candidates against Quincy's alone, every score held fixed
# ---------------------------------------------------------------------------

QN = site.municipal == 'Quincy'
qrows = []
for d in SETTINGS:
    sc, r = SCORES[d['id']], RANKS[d['id']]
    qsc = sc[QN]
    w_q = qsc.idxmax()
    top_all = r[r <= 10].sort_values().index
    qrows.append(dict(setting=d['id'], indicators=d['k'], reference=d['ref'],
                      weights=' '.join(f'{c}={w:g}' for c, w in d['weights'].items()),
                      first_all=firsts(sc),
                      first_all_municipal=' = '.join(site.municipal[sc >= sc.max() - TOL].unique()),
                      first_quincy=firsts(qsc), first_quincy_rank_in_all=int(r[w_q]),
                      first_quincy_score=round(qsc.max(), 2), first_all_score=round(sc.max(), 2),
                      sites_above_best_quincy=int((sc > qsc.max() + TOL).sum()),
                      quincy_top3='; '.join(SID[i] for i in qsc.nlargest(3).index),
                      all_top10_outside_quincy='; '.join(SID[i] for i in top_all if not QN[i]),
                      all_top10_in_quincy=int(QN[top_all].sum())))
quincy = pd.DataFrame(qrows)
write(quincy, 'quincy_vs_all.csv')

qws = []
for k, ref in WS_SETTINGS:
    cols = IND4 if k == 4 else IND5
    res = weight_space(PCT[ref].loc[QN, cols].to_numpy(), DRAWS[k])
    full = pd.Series(WS[(k, ref)]['first'], index=site.index)
    for n, i in enumerate(site.index[QN.to_numpy()]):
        qws.append(dict(setting=f'{k}ind_{ref}', alpha='(' + ','.join(['1'] * k) + ')', seed=SEED,
                        n_draws=N_DRAWS, site_oid=site.site_oid[i], sid=SID[i], station=site.station[i],
                        first_share_within_quincy=res['first'][n], first_share_among_all=full[i],
                        quincy_total_share_among_all=float(full[QN].sum())))
qws = pd.DataFrame(qws)
qws = qws[(qws.first_share_within_quincy > 0) | (qws.first_share_among_all > 0)]
write(qws.sort_values(['setting', 'first_share_within_quincy'], ascending=[True, False]),
      'quincy_weight_space.csv')

qsites = wide[wide.municipal == 'Quincy'].copy()
qsites['frontier4_within_quincy'] = pareto_mask(site[QN], IND4, LOWER)
qsites['frontier5_within_quincy'] = pareto_mask(site[QN], IND5, LOWER)
write(qsites.sort_values('rank_4ind_mixed_equal'), 'quincy_sites.csv')

# ---------------------------------------------------------------------------
# 10. D. Internal checks
# ---------------------------------------------------------------------------

for c in IND5 + ['excl_p', 'fz100_p', 'station_km']:
    v = site[c]
    bad = int(v.isna().sum() + np.isinf(v).sum())
    check(f'missing or infinite values: {c}', f'{bad} of 251', status='ok' if bad == 0 else 'check')
check('site_oid unique (region, candidates)', f'{s.site_oid.is_unique}, {site.site_oid.is_unique}')
check('display name and map code unique', f'{site.sid.is_unique}, {site.code.is_unique}')
check('MAPC records with nparcels = 0', f'{int((s.nparcels == 0).sum())} region, {int(q.flag_nparcels_zero.sum())} candidates',
      'every one lists a single parcel id without brackets and an empty address; '
      + ', '.join(f'{r.sid} ({r.site_oid})' for r in site[q.flag_nparcels_zero].itertuples()),
      'unknown')
check('candidate records whose parcel id also appears in another MAPC site',
      f'{int(q.flag_parcel_shared.sum())} candidates',
      '; '.join(f'{r.sid} ({r.site_oid}) with {shared_with[r.site_oid]}' for r in site[q.flag_parcel_shared].itertuples()),
      'check')
check('candidate records identical to another on parcel id, land, building, area and job access',
      f'{int(q.flag_duplicate_record.sum())} candidates',
      '; '.join(' = '.join(f'{oid_to_sid[o]} ({o})' for o in g) for g in dup_groups), 'check')
check('jobs45tr = 0', f'{int((s.jobs45tr == 0).sum())} region, {int(q.flag_jobs45tr_zero.sum())} candidates',
      ', '.join(site.sid[q.flag_jobs45tr_zero]) + '; neighbours at the same station carry ~700,000',
      'check')
land_pac_levels = s.groupby('municipal').landv_pac.nunique()
check('MAPC landv_pac granularity', f'max {land_pac_levels.max()} distinct values per municipality',
      'a municipal-level figure despite its dictionary entry; not used, ppa is computed per site', 'note')

days = f25[f25.stop_name.isin(site.station.unique())].groupby('stop_name').day_type.agg(set)
missing_days = [st for st, dset in days.items() if not {'weekday', 'saturday', 'sunday'} <= dset]
check('candidate stations with weekday, Saturday and Sunday rows', f'{len(days) - len(missing_days)} of {len(days)}',
      ', '.join(missing_days))

st_c = site.drop_duplicates('station')
corr_rows = {
    'site level, 251 sites': (site.daily.corr(site.weekend), site.daily.corr(site.weekend, method='spearman')),
    f'station level, {len(st_c)} candidate stations': (st_c.daily.corr(st_c.weekend),
                                                       st_c.daily.corr(st_c.weekend, method='spearman')),
    f'station level, all {len(station)} rated stations': (station.daily.corr(station.weekend),
                                                         station.daily.corr(station.weekend, method='spearman')),
}
for k_, (pr, sp) in corr_rows.items():
    check(f'daily vs weekend correlation, {k_}', f'Pearson {pr:.3f}, Spearman {sp:.3f}',
          'site-level figures repeat each station once per site' if k_.startswith('site') else '', 'note')
check('buildar_ac vs estcapmix correlation, site level', f'Pearson {site.buildar_ac.corr(site.estcapmix):.3f}')
sizes = site.groupby('station').size()
check('sites per candidate station', f'{len(sizes)} stations; median {sizes.median():.0f}, max {sizes.max()} ({sizes.idxmax()})',
      'daily and peak_share are identical within a station, so sites at one station compete on land, '
      'area and job access alone, and site-level correlations weight busy multi-site stations more', 'note')
jobs_corr = site[['ppa', 'buildar_ac', 'estcapmix', 'daily', 'weekend', 'peak_share', 'wkday_wknd',
                  'jobs45tr']].corr().jobs45tr.drop('jobs45tr')
check('strongest Pearson correlation of jobs45tr with the other candidate indicators',
      f'{jobs_corr.abs().max():.2f} ({jobs_corr.abs().idxmax()})')
check('Spearman of jobs45tr with the four-indicator equal-weight score',
      f'{site.jobs45tr.corr(SCORES["4ind_mixed_equal"], method="spearman"):+.3f}')

for d in SETTINGS:
    sc = SCORES[d['id']]
    n_top = int((sc >= sc.max() - TOL).sum())
    on_front = bool(site[f'pareto{d["k"]}'][sc.idxmax()])
    if n_top > 1 or not on_front:
        check(f'winner of {d["id"]}', f'{n_top} tied at the top; on frontier: {on_front}', status='check')
check('every weighted-sum winner lies on the frontier', 'yes, by construction',
      'percentiles are monotone in the raw values, so a dominated site scores at most what its dominator '
      'scores under any positive weights; the baseline presented this as a check, but it cannot fail '
      'except by a tie', 'note')

qc_fixed = sum(1 for k in SCENARIOS
               if site.station[SCORES[f"4ind_mixed_{SCEN_ID[k]}"].idxmax()] == 'Quincy Center')
check('baseline "Quincy Center wins N scenarios" count', f'0 printed; corrected test also {qc_fixed}',
      'the baseline tested labels for the prefix "Quincy / Quincy Center", which no label has, so it could '
      'only print 0', 'note')

# Numbers the prose quotes that the script did not compute.
panel = pd.read_csv(BASE + 'outputs/ridership_panel_2017_2025.csv', index_col=0)
pc = panel.reindex(sorted(site.station.unique())).dropna(subset=['Fall 2019', 'Fall 2025'])
rv = panel.loc['Riverside']
check('Riverside, Fall 2025 weekday flow as % of Fall 2019; change since Fall 2023',
      f'{rv["Fall 2025"] / rv["Fall 2019"] * 100:.0f}%; {rv["Fall 2025"] - rv["Fall 2023"]:+,.0f}',
      'weekday boardings + alightings, not riders; Riverside is not a candidate station')
g23 = pc['Fall 2025'] - pc['Fall 2023']
g19 = pc['Fall 2025'] - pc['Fall 2019']
check('"absolute growth correlates 0.87 with ridership itself"', 'not reproduced as stated',
      f'{len(pc)} candidate stations with Fall 2019 data: change 2023-25 vs Fall 2025 flow Pearson '
      f'{np.corrcoef(g23, pc["Fall 2025"])[0, 1]:.2f}, Spearman {g23.corr(pc["Fall 2025"], method="spearman"):.2f}; '
      f'change 2019-25 vs Fall 2025 Pearson {np.corrcoef(g19, pc["Fall 2025"])[0, 1]:.2f}', 'check')
check('median Fall 2023 to Fall 2025 weekday flow change, candidate stations',
      f'{(pc["Fall 2025"] / pc["Fall 2023"]).median() * 100 - 100:+.1f}%',
      f'over the {len(pc)} of {site.station.nunique()} candidate stations with Fall 2019 data (the GLX '
      'stations opened in 2022)', 'note')
ws_ = s[s.statname.str.replace(' Glx', '', regex=False).str.strip().eq('Washington Street')
        & s.municipal.eq('Somerville')]
wst = coords_all.drop_duplicates('stop_name').set_index('stop_name').loc['Washington Street']
wkm = np.hypot((ws_.long - wst.position_x) * KM_PER_DEG * np.cos(np.radians(ws_.lat)),
               (ws_.lat - wst.position_y) * KM_PER_DEG)
check('Somerville sites MAPC labels "Washington Street": distance to that GTFS stop',
      f'{len(ws_)} sites, {wkm.min():.1f}-{wkm.max():.1f} km')
check('sites dropped by the 0.805 km straight-line cut', f'{len(beyond)} of 285',
      f'{int((beyond.station_km < 1).sum())} between 0.805 and 1 km; '
      + ', '.join(f'{m} {n}' for m, n in beyond[beyond.station_km >= 1].municipal.value_counts().items())
      + ' beyond 1 km (Medford: MAPC "Route 16"; Milton: Mattapan-line stops have no Fall 2025 rating). '
      'The baseline comment said seven.', 'check')
hav = 2 * 6371.0088 * np.arcsin(np.sqrt(
    np.sin(np.radians(site.lat - site.station.map(coords.drop_duplicates('stop_name').set_index('stop_name').position_y)) / 2) ** 2
    + np.cos(np.radians(site.lat)) * np.cos(np.radians(site.station.map(coords.drop_duplicates('stop_name').set_index('stop_name').position_y)))
    * np.sin(np.radians(site.long - site.station.map(coords.drop_duplicates('stop_name').set_index('stop_name').position_x)) / 2) ** 2))
check('equirectangular vs haversine straight-line distance, candidates',
      f'max difference {(hav - site.station_km).abs().max() * 1000:.1f} m',
      'the approximation is not the issue; the absence of a network is')

otp = pd.read_parquet(DATA + '2024-02-03-subway-on-time-performance-v1.parquet')
hw = otp.groupby('route_id').agg(trunk=('headway_trunk_seconds', 'median'),
                                 branch=('headway_branch_seconds', 'median')) / 60
hop = otp.groupby('trunk_route_id').travel_time_seconds.median()
check('Saturday 3 Feb 2024 median headway, minutes: trunk vs branch',
      '; '.join(f'{r} trunk {v.trunk:.1f}' + ('' if np.isnan(v.branch) else f' branch {v.branch:.1f}')
                for r, v in hw.iterrows()),
      'the baseline chart plots trunk headway, which on the Green Line pools four branches', 'check')
check('Saturday 3 Feb 2024 median seconds between stops by line',
      '; '.join(f'{r} {v:.0f}' for r, v in hop.items()),
      'Blue is shorter than Green; hop time reflects stop spacing, not speed', 'check')
vv = site.dropna(subset=['regipctile'])
check('Spearman of MAPC ovscr with land value per acre, candidates',
      f'{vv.ovscr.corr(vv.ppa, method="spearman"):+.2f}', 'README quotes 0.44; the script prints 0.29',
      'check')

checks = pd.DataFrame(CHECKS)
write(checks, 'internal_checks.csv')

# Flagged records: does leaving them out move anything? Scores held fixed.
flag_rows = []
cases = {
    'drop the four nparcels = 0 records': q.flag_nparcels_zero,
    'keep one of the duplicated Assembly pair': site.site_oid.isin(
        [g[-1] for g in dup_groups]),
    'drop the two jobs45tr = 0 records': q.flag_jobs45tr_zero,
    'drop every flagged record': cand.quality_flags != '',
}
for label, drop in cases.items():
    keep = ~drop.to_numpy()
    sub = site[keep]
    for k, cols in ((4, IND4), (5, IND5)):
        fr = pareto_mask(sub, cols, LOWER)
        was = site[f'pareto{k}'].to_numpy()[keep]
        flag_rows.append(dict(case=label, dropped=' '.join(site.sid[drop]), setting=f'frontier {k} ind',
                              baseline=int(site[f'pareto{k}'].sum()), after=int(fr.sum()),
                              entering=' '.join(sub.sid[fr & ~was]), leaving=' '.join(sub.sid[~fr & was])))
    for sid_ in ('4ind_mixed_equal', '4ind_uniform_equal', '5ind_mixed_equal', '5ind_uniform_equal'):
        sc = SCORES.loc[keep, sid_]
        r_after = sc.rank(ascending=False, method='min')
        t0 = [i for i in RANKS[sid_][RANKS[sid_] <= 10].index if keep[pos[i]]]
        t1 = list(r_after[r_after <= 10].index)
        flag_rows.append(dict(case=label, dropped=' '.join(site.sid[drop]), setting=sid_,
                              baseline=firsts(SCORES[sid_]), after=firsts(sc),
                              entering=' '.join(SID[i] for i in t1 if i not in t0),
                              leaving=' '.join(SID[i] for i in t0 if i not in t1)))
write(pd.DataFrame(flag_rows), 'flag_sensitivity.csv')

# ---------------------------------------------------------------------------
# 11. Figures: indicator set, reference set, candidate scope
# ---------------------------------------------------------------------------

thousands = FuncFormatter(lambda x, _: f'{x:,.0f}')

# R1. What the fifth indicator adds.
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.9), gridspec_kw={'width_ratios': [1.3, 1]})
x = SCORES['4ind_mixed_equal']
rest = ~(site.pareto4 | site.pareto5)
ax1.scatter(x[rest], site.jobs45tr[rest], s=16, color=FAINT, lw=0, label='neither frontier')
ax1.scatter(x[site.pareto4], site.jobs45tr[site.pareto4], s=52, marker='o', color=ACCENT,
            edgecolor='white', lw=0.6, zorder=3, label=f'four-indicator frontier (n={site.pareto4.sum()})')
ax1.scatter(x[added.index], added.jobs45tr, s=48, marker='D', color=ACCENT2,
            edgecolor='white', lw=0.6, zorder=3, label=f'added by job access (n={len(added)})')
ax1.set_xlabel('four-indicator equal-weight score (mixed reference)')
ax1.set_ylabel('jobs reachable by transit in 45 min, 2018')
ax1.yaxis.set_major_formatter(thousands)
ax1.legend(frameon=False, fontsize=9, loc='lower left')
ax1.set_title('Candidate sites by four-indicator score and job access')
g = geo[(geo.frontier4 > 0) | (geo.frontier5 > 0)].sort_values('frontier5')
yy = np.arange(len(g))
ax2.barh(yy + 0.2, g.frontier4, height=0.38, color=ACCENT, label='four indicators')
ax2.barh(yy - 0.2, g.frontier5, height=0.38, color=ACCENT2, label='five indicators')
for yv, a, b in zip(yy, g.frontier4, g.frontier5):
    ax2.text(a + 0.3, yv + 0.2, str(a), va='center', fontsize=9, color=MUTE)
    ax2.text(b + 0.3, yv - 0.2, str(b), va='center', fontsize=9, color=MUTE)
ax2.set_yticks(yy, g.index)
ax2.set_xlim(0, g.frontier5.max() * 1.18)
ax2.grid(axis='y', visible=False)
ax2.legend(frameon=False, fontsize=9, loc='lower right')
ax2.set_title('Frontier sites by community')
plt.tight_layout()
save('r1-frontier-four-vs-five')

# R2. First-place share by reference set, one panel per weight space.
panels = []
for k in (4, 5):
    m_ = pd.Series(WS[(k, 'mixed')]['first'], index=SID.values)
    u_ = pd.Series(WS[(k, 'uniform')]['first'], index=SID.values)
    both = pd.DataFrame({'mixed': m_, 'uniform': u_})
    both = both[(both.mixed > 0) | (both.uniform > 0)]
    both = both.loc[both.max(1).sort_values().index]
    panels.append((k, both))
DUP_SIDS = set(site.sid[q.flag_duplicate_record])
height = max(len(b) for _, b in panels) * 0.3 + 1.9
fig, axes = plt.subplots(1, 2, figsize=(14, height))
for ax, (k, both) in zip(axes, panels):
    yy = np.arange(len(both))
    for yv, (a, b) in zip(yy, both.to_numpy() * 100):
        ax.plot([a, b], [yv, yv], color=FAINT, lw=2, zorder=1)
    ax.scatter(both.mixed * 100, yy, s=46, color=ACCENT, zorder=3)
    ax.scatter(both.uniform * 100, yy, s=46, marker='D', color=ACCENT2, zorder=3)
    lim = both.to_numpy().max() * 100
    ax.text(lim * 1.08, len(both) - 0.3, 'mixed / uniform, %', va='bottom', fontsize=8.6,
            color=MUTE, fontweight='bold')
    for yv, (a, b) in zip(yy, both.to_numpy() * 100):
        ax.text(lim * 1.08, yv, f'{a:.1f} / {b:.1f}', va='center', fontsize=8.6, color=MUTE)
    ax.set_yticks(yy, [f'{n} *' if n in DUP_SIDS else n for n in both.index], fontsize=9)
    ax.set_ylim(-0.7, len(both) + 0.4)
    ax.set_xlim(0, lim * 1.32)
    ax.set_xlabel('% of 200,000 sampled weightings in which the site ranks first')
    ax.grid(axis='y', visible=False)
    ax.set_title(f'{"Four" if k == 4 else "Five"} indicators, Dirichlet({",".join(["1"] * k)}), seed {SEED}',
                 fontsize=11.5)
handles = [plt.Line2D([], [], ls='', marker='o', ms=7, color=ACCENT, label='mixed reference (baseline)'),
           plt.Line2D([], [], ls='', marker='D', ms=6.5, color=ACCENT2,
                      label='every indicator against the 251 candidates')]
fig.suptitle('First-place share of every site that ever ranks first, by reference set',
             x=0.005, y=0.995, ha='left', fontweight='bold', fontsize=13)
fig.text(0.005, 0.005, '* one parcel recorded twice (site_oid 9967, 9971); draws where they tie are split '
         'between them.   The two panels are different weight spaces and their shares are not '
         'comparable with each other.', fontsize=8.8, color=MUTE)
plt.tight_layout(rect=(0, 0.02, 1, 0.965))
fig.legend(handles=handles, frameon=False, fontsize=9.5, ncol=2, loc='upper left',
           bbox_to_anchor=(0.005, 0.978))
save('r2-first-place-by-reference')

# R3. Equal-weight rank under the two reference sets.
fig, axes = plt.subplots(1, 2, figsize=(14, 6.4))
for ax, k in zip(axes, (4, 5)):
    a, b = RANKS[f'{k}ind_mixed_equal'], RANKS[f'{k}ind_uniform_equal']
    show = sorted(set(a[a <= 10].index) | set(b[b <= 10].index), key=lambda i: (a[i], b[i]))
    cap = 25

    def spread(ranks):
        # Tied ranks share one point on the axis; their labels are fanned out
        # around it so neither is printed over the other.
        pos_, seen = {}, {}
        for i in show:
            seen.setdefault(min(ranks[i], cap), []).append(i)
        for yv, members in seen.items():
            for j, i in enumerate(members):
                pos_[i] = yv + (j - (len(members) - 1) / 2) * 0.55
        return pos_

    la, lb = spread(a), spread(b)
    for i in show:
        stay = a[i] <= 10 and b[i] <= 10
        col = ACCENT2 if stay else ACCENT
        ya, yb = min(a[i], cap), min(b[i], cap)
        ax.plot([0, 1], [ya, yb], '-o', color=col, lw=1.8, ms=6, zorder=3)
        ax.text(-0.04, la[i], f'{SID[i]}  {a[i]}', ha='right', va='center', fontsize=9, color=INK)
        ax.text(1.04, lb[i], f'{b[i]}  {SID[i]}', ha='left', va='center', fontsize=9, color=INK)
    ax.axhspan(10.5, cap + 1.2, color=FAINT, alpha=0.35, lw=0, zorder=0)
    ax.set_ylim(cap + 1.2, -0.2)
    ax.set_xlim(-0.9, 1.9)
    ax.set_xticks([0, 1], ['mixed reference\n(baseline)', 'every indicator against\nthe 251 candidates'])
    ax.set_yticks([])
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(f'{"Four" if k == 4 else "Five"} indicators, equal weights', fontsize=11.5)
fig.suptitle('Top-ten sites under either reference set, and their rank under the other',
             x=0.005, ha='left', fontweight='bold', fontsize=13)
fig.text(0.005, 0.005, f'Shaded: outside the top ten. Ranks past {cap} are drawn at {cap} and '
         'labelled with their actual rank. Tied sites share a rank.', fontsize=8.8, color=MUTE)
plt.tight_layout(rect=(0, 0.03, 1, 1))
save('r3-rank-by-reference')

# R4. Quincy only, with every score fixed at its all-candidate value.
qq = quincy.copy()
qq['label'] = [SET[i]['label'].replace(' | 4 ind | ', '  ·  4 ind  ·  ').replace(' | 5 ind | ', '  ·  5 ind  ·  ')
               for i in qq.setting]
qq = qq.iloc[::-1]
fig, ax = plt.subplots(figsize=(12.5, 6.2))
yy = np.arange(len(qq))
ax.scatter(qq.first_quincy_rank_in_all, yy, s=58,
           color=[ACCENT if r == 'mixed' else ACCENT2 for r in qq.reference],
           marker='o', zorder=3)
for yv, r in zip(yy, qq.itertuples()):
    ax.text(r.first_quincy_rank_in_all * 1.12, yv, r.first_quincy, va='center', fontsize=9, color=INK)
    ax.text(58, yv, r.first_all.replace(' = Malden Center ', ' = '), va='center', fontsize=9, color=MUTE)
ax.set_xscale('log')
ax.set_xlim(0.8, 160)
ax.set_xticks([1, 2, 5, 10, 20])
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
ax.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
ax.set_yticks(yy, qq.label, fontsize=9)
ax.grid(axis='y', visible=False)
ax.text(58, len(qq) - 0.2, 'first among all 251', fontsize=9, color=MUTE, fontweight='bold', va='bottom')
ax.set_xlabel('rank among all 251 candidates of the best Quincy site (scores fixed; log scale)')
ax.set_title('What restricting the candidates to Quincy leaves, under each setting')
save('r4-quincy-only')

# ---------------------------------------------------------------------------
# 12. Manifest and summary
# ---------------------------------------------------------------------------

head = git('rev-parse', 'HEAD')
dirty = git('status', '--porcelain')
manifest = {
    'baseline_commit': git('rev-parse', BASELINE_COMMIT),
    'working_tree_head': head,
    'working_tree_dirty': bool(dirty),
    'command': 'python revision_2026.py',
    'script_sha256': sha256('revision_2026.py'),
    'seeds': {'dirichlet': SEED, 'seed_stability_check': list(SEEDS_CHECK)},
    'n_draws': N_DRAWS,
    'dirichlet_alpha': {'4 indicators': [1] * 4, '5 indicators': [1] * 5},
    'tie_tolerance': TOL,
    'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                    'numpy': np.__version__, 'pandas': pd.__version__,
                    'matplotlib': mpl.__version__,
                    'scipy': __import__('scipy').__version__,
                    'pyarrow': __import__('pyarrow').__version__},
    'data_sha256': {f: sha256(DATA + f) for f in sorted(os.listdir(DATA))},
    'baseline_outputs_sha256': json.load(open(BASE + 'manifest.json', encoding='utf-8'))['outputs_sha256'],
    'outputs': sorted(os.listdir(OUT)),
    'figures': sorted(os.listdir(FIG)),
}
with open('revision/manifest.json', 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(manifest, fh, indent=2)
    fh.write('\n')

summary = {
    'screening': steps,
    'frontier': {'4': int(site.pareto4.sum()), '5': int(site.pareto5.sum()),
                 'communities_4': int(f4.municipal.nunique()),
                 'communities_5': int(site[site.pareto5].municipal.nunique())},
    'first': {d['id']: firsts(SCORES[d['id']]) for d in SETTINGS},
    'weight_space': ws_summary.set_index('setting')[['first', 'first_share', 'second', 'second_share',
                                                     'sites_ever_first', 'tied_draws']].to_dict('index'),
}
with open(OUT + 'summary.json', 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(summary, fh, indent=2, default=str)
    fh.write('\n')

print('screening:', ' -> '.join(str(n) for _, n in steps))
print(f'frontier: {site.pareto4.sum()} (4 ind), {site.pareto5.sum()} (5 ind)')
print(comparisons[['setting_a', 'setting_b', 'first_a', 'first_b', 'top10_overlap', 'spearman']].to_string(index=False))
print(ws_summary[['setting', 'first', 'first_share', 'second', 'second_share', 'sites_ever_first',
                  'tied_draws']].to_string(index=False))
print(quincy[['setting', 'first_all', 'first_quincy', 'first_quincy_rank_in_all']].to_string(index=False))
print(checks[checks.status != 'ok'][['check', 'result']].to_string(index=False))
print('written:', len(os.listdir(OUT)), 'tables,', len(os.listdir(FIG)), 'figures')
