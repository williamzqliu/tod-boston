# Research revision of the 2026 rebuild (round 3; see revision/VERSIONS.md).
#
#     python revision/reproduce_baseline.py     # freezes the e18a184 baseline (once)
#     python revision/checks.py                 # checks the scoring rules
#     python revision_2026.py
#
# Run from the repository root. Reads data/ and the frozen baseline in
# revision/baseline_e18a184/, and writes revision/outputs/, revision/figures/
# and revision/manifest.json. It never writes to figures/ or outputs/, which
# belong to build_2026.py, or to the frozen baseline.
#
# The research question is bounded to: among a defined set of redevelopment
# sites near rapid transit stations, compare assessed land value, developable
# scale and existing station activity, and test how far the ordering depends on
# modelling choices. It is not a measure of TOD value, of investment
# feasibility, or of planning outcomes.
#
# The main comparison is M3: lower assessed land value per acre, larger
# buildable area and more station boardings + alightings preferred, equal
# weights of exactly 1/3. Those preferences are this study's, not objective
# criteria of TOD value. Peak share is described, not scored; it is scored only
# in the labelled historical (S*) and exploratory (X4_*) settings.
#
# The script
#   1. re-implements the baseline screening and checks it against the frozen
#      e18a184 tables, stopping if anything differs;
#   2. audits the records the first round flagged, using the site polygons
#      stored in the MAPC file (revision/geometry.py), and decides which enter
#      the main candidate set;
#   3. scores every setting with exact arithmetic under two percentile rules
#      and two references (revision/methods.py), changing one thing at a time;
#   4. runs the Dirichlet weight spaces with ties counted, not resolved by row;
#   5. repeats the Quincy-only comparison with every score held fixed;
#   6. writes the tables, three figures and a manifest.

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import warnings
from fractions import Fraction

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib as mpl
import matplotlib.pyplot as plt

sys.path.insert(0, 'revision')
import geometry as geo                                           # noqa: E402
from methods import (pct_exact, exact_scores, top_set, runner_up_gap,  # noqa: E402
                     weight_space, dirichlet, pareto_mask, dominance,
                     vector_groups, TOL)

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

if not os.path.exists(BASE + 'outputs/sites_scored_2026.csv'):
    sys.exit('run `python revision/reproduce_baseline.py` first')

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
# 1. The baseline screening, re-implemented, and checked
# ---------------------------------------------------------------------------

s = pd.read_csv(DATA + 'mapc.rethinking_retail_sites.csv', low_memory=False)
s['ppa'] = s.land_value / s.sitearea_a
s['site_oid'] = s.site_oid.astype(int)

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
site = site[site.station_km <= 0.805]
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

# Display names exactly as the baseline builds them. They are frozen and
# checked against the e18a184 table; site_oid is the key everywhere below.
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
site = site.set_index('site_oid', drop=False)
SID = site.sid

base = pd.read_csv(BASE + 'outputs/sites_scored_2026.csv').set_index('sid')
mine = site.set_index('sid')
assert set(base.index) == set(mine.index) and len(base) == 251
for c in ['long', 'lat', 'sitearea_a', 'buildar_ac', 'ppa', 'daily', 'peak_share',
          'jobs45tr', 'regipctile', 'station_km']:
    assert np.allclose(mine.loc[base.index, c].to_numpy(float), base[c].to_numpy(float),
                       rtol=1e-12, atol=0, equal_nan=True), c
for c in ['municipal', 'station', 'line']:
    assert (mine.loc[base.index, c] == base[c]).all(), c

# ---------------------------------------------------------------------------
# 2. Percentiles: two rules, two references, exact
# ---------------------------------------------------------------------------

REGION_REF = {'ppa': s.loc[s.ppa > 0, 'ppa'], 'buildar_ac': s.buildar_ac.dropna(),
              'jobs45tr': s.jobs45tr.dropna()}
ALL251 = list(site.index)


def pct_table(ranked, ref, rule, cols):
    """Exact percentiles for the ranked sites. `mixed0` is the baseline's
    reference, frozen: region-wide for land value, buildable area and job
    access, the original 251 candidates for the two station measures.
    `uniform` ranks every indicator against the ranked set itself."""
    out = {}
    for c in cols:
        if ref == 'mixed0':
            b = REGION_REF[c] if c in REGION_REF else site.loc[ALL251, c]
        elif ref == 'uniform':
            b = site.loc[ranked, c]
        else:
            raise ValueError(ref)
        out[c] = pct_exact(site.loc[ranked, c], b, c in LOWER, rule)
    return out


SCENARIOS = {
    'Developer (cost first)': {'ppa': '0.50', 'buildar_ac': '0.25', 'daily': '0.15', 'peak_share': '0.10'},
    'City (housing first)': {'buildar_ac': '0.50', 'ppa': '0.20', 'daily': '0.20', 'peak_share': '0.10'},
    'Transit agency (ridership first)': {'daily': '0.40', 'peak_share': '0.30', 'ppa': '0.15', 'buildar_ac': '0.15'},
    'Place-making (all-day use first)': {'peak_share': '0.40', 'buildar_ac': '0.25', 'daily': '0.20', 'ppa': '0.15'},
    'No prior (all four equal)': {'ppa': '0.25', 'buildar_ac': '0.25', 'daily': '0.25', 'peak_share': '0.25'},
}
SCEN_ID = dict(zip(SCENARIOS, ['developer', 'city', 'transit', 'placemaking', 'equal']))
# The keys above are the baseline's own column names and stay as they are so the
# frozen tables can be matched. What the revision prints: equal weights are a
# preference too, not the absence of one, and the other four are positions the
# author wrote for groups that have not reviewed them.
SCEN_LABEL = {'Developer (cost first)': 'Developer (author-constructed)',
              'City (housing first)': 'City (author-constructed)',
              'Transit agency (ridership first)': 'Transit agency (author-constructed)',
              'Place-making (all-day use first)': 'Place-making (author-constructed)',
              'No prior (all four equal)': 'Equal weights (four indicators)'}
EQUAL5 = {c: '0.2' for c in IND5}
IND3 = ['ppa', 'buildar_ac', 'daily']
EQUAL3 = {c: Fraction(1, 3) for c in IND3}        # exactly 1/3, not 0.3333

# The baseline scores, reproduced exactly from the exact percentiles.
P0 = pct_table(ALL251, 'mixed0', 'strict', IND5)
for name, w in SCENARIOS.items():
    sc = exact_scores(P0, w)
    b_ = base[name].reindex(SID.loc[ALL251].to_numpy()).to_numpy()
    assert np.allclose([float(x) for x in sc], b_, rtol=0, atol=1e-9), name
check('re-implementation reproduces frozen e18a184 sites_scored_2026.csv', 'yes',
      '251 names, coordinates, indicators and all five scenario scores, to 1e-9')

# ---------------------------------------------------------------------------
# 3. Record audit
# ---------------------------------------------------------------------------

val, acres_all = geo.validate(s)
check('site polygons decoded from the MAPC shape field', f'{val["sites"]} sites',
      f'decoded area equals sitearea_a to 0.01 ac for {val["area_equal_to_0.01_ac"]:.1%}; '
      f'centroid within {val["centroid_offset_m_p99"]:.2f} m of MAPC lat/long for 99% '
      f'(median {val["centroid_offset_m_median"]:.2f} m)')
s['poly_acres'] = acres_all
RINGS = {o: geo.rings(h) for o, h in zip(s.site_oid, s['shape'])}
BBOX = {o: geo.bbox(r) for o, r in RINGS.items()}
AREA = {o: geo.area_m2(r) for o, r in RINGS.items()}

# Parcel ids, region-wide. MAPC's dictionary: parcel IDs are the parcels that
# *overlap* the site, and land_value is the combined value of the parcels in
# the site, so one parcel can appear in, and be valued in full by, several.
pids = s.parcelids.astype(str).apply(lambda x: re.findall(r'\d+', x))
exp = pd.DataFrame({'site_oid': np.repeat(s.site_oid.to_numpy(), pids.str.len()),
                    'pid': np.concatenate(pids.to_numpy())})
pair = exp.merge(exp, on='pid', suffixes=('', '_other'))
pair = pair[pair.site_oid != pair.site_oid_other]
shares_parcel = pair.groupby('site_oid').site_oid_other.apply(lambda x: sorted(set(x))).to_dict()
sv = s.set_index('site_oid')

# Spatial overlap of every candidate with every MAPC site.
ov_rows = []
for o in ALL251:
    a = BBOX[o]
    for q, b in BBOX.items():
        if q != o and a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]:
            m2 = geo.overlap_m2(RINGS[o], RINGS[q])
            if m2 > 1:
                ov_rows.append(dict(site_oid=o, other=q, overlap_m2=round(m2, 1),
                                    share_of_site=m2 / AREA[o], share_of_other=m2 / AREA[q]))
overlaps = pd.DataFrame(ov_rows, columns=['site_oid', 'other', 'overlap_m2',
                                          'share_of_site', 'share_of_other'])


def same_values(o, q):
    a, b = sv.loc[o], sv.loc[q]
    return all(a[c] == b[c] for c in ['land_value', 'bldg_value', 'othr_value', 'total_valu'])


# MAPC's own centroids, projected: attribute evidence on location that does not
# depend on the polygon decoding.
MX, MY = geo.project(sv.long.to_numpy(), sv.lat.to_numpy())
MAPC_XY = dict(zip(sv.index, zip(MX, MY)))


def mapc_gap_m(o, q):
    return float(np.hypot(MAPC_XY[o][0] - MAPC_XY[q][0], MAPC_XY[o][1] - MAPC_XY[q][1]))


def geometry_status(o):
    """Where the decoded polygon sits relative to what has been validated.
    Validated: a single ring whose area matches sitearea_a to 0.01 ac and whose
    centroid is within 1 m of MAPC's. Everything else (several rings, which
    may be parts or holes, or a mismatch) is a provisional reading: no
    standard GIS reader was available to check it."""
    rs = RINGS[o]
    cx, cy = geo.centroid(rs)
    off = float(np.hypot(cx - MAPC_XY[o][0], cy - MAPC_XY[o][1]))
    ok_area = abs(AREA[o] / geo.SQM_PER_ACRE - sv.loc[o, 'sitearea_a']) <= 0.01
    if len(rs) == 1 and ok_area and off < 1:
        return 'validated: one ring, area and centroid match MAPC', off
    return f'provisional: {len(rs)} ring(s), area match {ok_area}, centroid offset {off:.1f} m', off


audit = []
for o in ALL251:
    r = sv.loc[o]
    others = shares_parcel.get(o, [])
    ovl = overlaps[overlaps.site_oid == o]
    classes, cost, reasons = [], 'reliable', []
    for q in others:
        cover = geo.overlap_m2(RINGS[o], RINGS[q])
        coincide = cover / AREA[o] > 0.95 and cover / AREA[q] > 0.95
        gap = mapc_gap_m(o, q)
        if coincide and same_values(o, q) and gap < 1:
            classes.append('1_same_site_duplicate')
        elif same_values(o, q):
            classes.append('3_whole_parcel_value_repeated')
            cost = 'unreliable'
            reasons.append(f'identical land/building/other/total values to site {q}, which lists the '
                           f'same parcel; recorded areas {r.sitearea_a:.2f} and {sv.loc[q, "sitearea_a"]:.2f} ac; '
                           f'MAPC centroids {gap:.0f} m apart; decoded polygons overlap {cover:.0f} m2')
        else:
            classes.append('2_sites_share_a_parcel')
            if cost == 'reliable':
                cost = 'unverifiable'
            reasons.append(f'lists a parcel also listed by site {q}; values differ, so how that parcel '
                           f'is valued between the two cannot be checked; MAPC centroids {gap:.0f} m '
                           f'apart; decoded polygons overlap {cover:.0f} m2 (provisional where a '
                           f'second ring is involved)')
    if r.nparcels == 0:
        classes.append('4_nparcels_field_anomaly')
        reasons.append('nparcels = 0 although one parcel id is listed (no brackets, no address)')
    for x in ovl.itertuples():
        if x.other not in others:
            first_only = geo.overlap_m2([RINGS[o][0]], [RINGS[x.other][0]])
            classes.append('decoded_overlap_without_shared_parcel')
            reasons.append(f'decoded polygon overlaps site {x.other} by {x.overlap_m2:.0f} m2 '
                           f'({x.share_of_site:.0%} of this site)'
                           + (' only through a second decoded ring, provisional' if first_only < 1 else '')
                           + '; parcel lists disjoint, values distinct')
    poly = AREA[o] / geo.SQM_PER_ACRE
    ring0 = geo.area_m2([RINGS[o][0]]) / geo.SQM_PER_ACRE
    if abs(poly / r.sitearea_a - 1) > 0.02 and abs(poly - r.sitearea_a) > 0.01:
        classes.append('recorded_area_differs_from_decoded')
        reasons.append(f'decoded {poly:.2f} ac against recorded {r.sitearea_a:.2f} ac'
                       + (f'; the first ring alone ({ring0:.2f} ac) matches' if abs(ring0 - r.sitearea_a) <= 0.01
                          else '') + '; cause unknown, not treated as a source error')
    jobs = 'recorded_zero_unverified' if r.jobs45tr == 0 else 'as_recorded'
    gstat, goff = geometry_status(o)
    audit.append(dict(site_oid=o, objectid=int(r.objectid), sid=SID[o],
                      station=site.station[o], municipal=r.municipal,
                      nparcels=int(r.nparcels), parcelids=r.parcelids,
                      parceladdr=str(r.parceladdr).strip() if pd.notna(r.parceladdr) else '',
                      land_value=r.land_value, bldg_value=r.bldg_value,
                      othr_value=r.othr_value, total_valu=r.total_valu,
                      sitearea_a=r.sitearea_a, buildar_ac=r.buildar_ac,
                      polygon_acres=round(poly, 3), polygon_first_ring_acres=round(ring0, 3),
                      polygon_rings=len(RINGS[o]), centroid_offset_m=round(goff, 2),
                      geometry_evidence=gstat,
                      shares_parcel_with=' '.join(map(str, others)),
                      overlaps_with=' '.join(f'{x.other}:{x.overlap_m2:.0f}m2' for x in ovl.itertuples()),
                      record_classes=';'.join(dict.fromkeys(classes)),
                      cost_indicator=cost, jobs45tr_status=jobs,
                      evidence=' | '.join(reasons)))
audit = pd.DataFrame(audit).set_index('site_oid', drop=False)

# Main candidate set: drop the sites whose land value cannot be attributed to
# the site (repeated whole-parcel values, or a parcel valued in two sites with
# an unknown split). Keep the nparcels anomaly, the disjoint-parcel overlap and
# the area discrepancies, which are flagged but leave the four indicators
# supported. Nothing is merged: no pair of records is the same site.
EXCLUDED = audit.index[audit.cost_indicator != 'reliable'].tolist()
MAIN = [o for o in ALL251 if o not in EXCLUDED]
JOBS0 = audit.index[audit.jobs45tr_status != 'as_recorded'].tolist()
MAIN_J = [o for o in MAIN if o not in JOBS0]
assert not audit.record_classes.str.contains('1_same_site').any()
audit['in_main_set'] = audit.site_oid.isin(MAIN)

# Why each excluded record is out, in one of two kinds. None of it rests on the
# decoded geometry: the parcel ids, the values and MAPC's own definitions and
# centroids carry each decision.
EXCLUSION_BASIS = {
    9967: ('valuation not allocatable',
           'confirmed from attributes: same parcel id and identical land, building, other and total '
           'value as 9971 and 9949, on recorded areas of 2.25, 2.25 and 1.60 ac at MAPC centroids 67-137 m '
           'apart, so one parcel value stands for three different areas; nparcels = 0 contradicts the '
           'listed parcel'),
    9971: ('valuation not allocatable', 'as 9967'),
    9949: ('conservative',
           'record internally consistent (one parcel, an address); its value may be the parcel\'s own, '
           'but it is identical to two other records on other areas and which record it belongs to '
           'cannot be told'),
    6758: ('valuation not allocatable',
           'confirmed from attributes: lists parcel 621026, which 6766 also lists; by MAPC\'s definition '
           'its land value sums all six listed parcels, so that parcel is valued in both sites and the '
           'split is unknown'),
    6766: ('conservative',
           'its own values differ from 6758\'s and may be parcel 621026\'s alone; out because the same '
           'parcel is also valued in 6758; nparcels = 0 contradicts the listed parcel'),
}
assert set(EXCLUSION_BASIS) == set(EXCLUDED), (sorted(EXCLUSION_BASIS), sorted(EXCLUDED))
audit['exclusion_basis'] = audit.site_oid.map(lambda o: EXCLUSION_BASIS.get(o, ('', ''))[0])
audit['exclusion_reason'] = audit.site_oid.map(lambda o: EXCLUSION_BASIS.get(o, ('', ''))[1])
multi = [o for o in s.site_oid if len(RINGS[o]) > 1]
rec_tot = sum(abs(AREA[o] / geo.SQM_PER_ACRE - sv.loc[o, 'sitearea_a']) <= 0.01 for o in multi)
rec_first = sum(abs(geo.area_m2([RINGS[o][0]]) / geo.SQM_PER_ACRE - sv.loc[o, 'sitearea_a']) <= 0.01
                and abs(AREA[o] / geo.SQM_PER_ACRE - sv.loc[o, 'sitearea_a']) > 0.01 for o in multi)
check('multi-ring decoded polygons, region-wide', f'{len(multi)} records',
      f'recorded area matches the decoded total for {rec_tot}, the first ring alone for {rec_first}, '
      f'neither for {len(multi) - rec_tot - rec_first}; the part/hole reading is not validated and no '
      f'standard GIS reader was available to check it', 'note')
flagged = audit[audit.record_classes != ''].copy()
write(flagged.reset_index(drop=True), 'record_audit.csv')
write(overlaps.round(4), 'candidate_overlaps.csv')
check('candidate records that are the same site recorded twice', '0',
      'no pair shares a parcel, identical values and a coinciding polygon', 'ok')
check('candidates temporarily excluded: valuation attribution uncertain',
      f'{len(EXCLUDED)}', ', '.join(f'{SID[o]} ({o})' for o in EXCLUDED), 'check')
check('main candidate set', f'{len(MAIN)} sites',
      f'{site.loc[MAIN].municipal.nunique()} communities, {site.loc[MAIN].station.nunique()} stations')

# ---------------------------------------------------------------------------
# 4. Settings
# ---------------------------------------------------------------------------

SETS = {'all251': ALL251, 'main': MAIN, 'main_jobs_known': MAIN_J}
SETTINGS = {}


def add(sid_, k, ranked, ref, rule, weights, label, role, indicators=None, flip=()):
    SETTINGS[sid_] = dict(id=sid_, k=k, ranked=ranked, ref=ref, rule=rule, weights=weights,
                          label=label, role=role, indicators=indicators or (IND4 if k == 4 else IND5),
                          flip=set(flip))


# The main comparison: three indicators, each with a stated preference (lower
# assessed land value per acre, larger buildable area, more station boardings
# plus alightings). Peak share is carried as a description only. M3 is its own
# setting; it is not S3 relabelled.
add('M3_equal', 3, 'main', 'uniform', 'midrank', EQUAL3,
    'M3 main comparison | equal weights (three indicators)', 'main', indicators=IND3)

STEP4 = {
    'S0': ('all251', 'mixed0', 'strict', 'historical baseline e18a184'),
    'S1': ('main', 'mixed0', 'strict', 'baseline rules on the 246'),
    'S2': ('main', 'mixed0', 'midrank', 'baseline reference, mid-rank ties'),
    'S2u': ('main', 'uniform', 'strict', 'candidate-set reference, strict ties'),
    'S3': ('main', 'uniform', 'midrank', 'round-2 four-indicator setting'),
    'K3': ('all251', 'uniform', 'midrank', 'S3 rules, flagged records kept'),
}
ROLE4 = {'S0': 'historical baseline', 'S1': 'historical revision step', 'S2': 'historical revision step',
         'S2u': 'historical revision step', 'S3': 'historical revision; four-indicator preference scenario',
         'K3': 'historical revision; record sensitivity'}
for st, (ranked, ref, rule, lab) in STEP4.items():
    for name, w in SCENARIOS.items():
        add(f'{st}_{SCEN_ID[name]}', 4, ranked, ref, rule, w, f'{st} {lab} | {SCEN_LABEL[name]}',
            ROLE4[st] + ('' if SCEN_ID[name] == 'equal' else '; author-constructed scenario'))
STEP5 = {
    'E0': ('all251', 'mixed0', 'strict', 'five indicators, baseline rules'),
    'E2': ('main', 'mixed0', 'midrank', 'five indicators, baseline reference'),
    'E3': ('main', 'uniform', 'midrank', 'S3 + jobs45tr, zero as recorded'),
    'E3u': ('main_jobs_known', 'uniform', 'midrank', 'S3 + jobs45tr, zero as unknown'),
}
for st, (ranked, ref, rule, lab) in STEP5.items():
    add(f'{st}_equal', 5, ranked, ref, rule, EQUAL5, f'{st} {lab} | equal weights',
        'historical accessibility extension of the four-indicator S3')
# Peak share appears in scoring only here, and only with its direction named.
add('X4_peak_low_equal', 4, 'main', 'uniform', 'midrank', SCENARIOS['No prior (all four equal)'],
    'exploratory: four indicators, lower peak share preferred | equal weights',
    'exploratory peak-share scenario (same scores as S3_equal)')
add('X4_peak_high_equal', 4, 'main', 'uniform', 'midrank', SCENARIOS['No prior (all four equal)'],
    'exploratory: four indicators, higher peak share preferred | equal weights',
    'exploratory peak-share scenario', flip=['peak_share'])

PCTS = {}


def pcts(d):
    key = (d['ranked'], d['ref'], d['rule'], tuple(sorted(d['flip'])))
    if key not in PCTS:
        ranked = SETS[d['ranked']]
        tab = pct_table(ranked, d['ref'], d['rule'], IND5)
        for c in d['flip']:
            b = site.loc[ranked, c] if d['ref'] == 'uniform' else site.loc[ALL251, c]
            tab[c] = pct_exact(site.loc[ranked, c], b, c not in LOWER, d['rule'])
        PCTS[key] = tab
    return PCTS[key]


EXACT, SCORE, RANK = {}, {}, {}
for sid_, d in SETTINGS.items():
    ranked = SETS[d['ranked']]
    w = {c: (v if isinstance(v, Fraction) else Fraction(v)) for c, v in d['weights'].items()}
    ex = exact_scores(pcts(d), w)
    EXACT[sid_] = pd.Series(ex, index=ranked)
    SCORE[sid_] = pd.Series([float(x) for x in ex], index=ranked)
    RANK[sid_] = pd.Series([1 + sum(1 for y in ex if y > x) for x in ex], index=ranked)


def firsts(sid_):
    ex = EXACT[sid_]
    return [ex.index[i] for i in top_set(list(ex))]


def first_label(sid_):
    return ' = '.join(SID[o] for o in firsts(sid_))


# Step tables
set_rows = []
for sid_, d in SETTINGS.items():
    ex = EXACT[sid_]
    g = runner_up_gap(list(ex))
    n = len(ex)
    wmin = min(Fraction(v) if not isinstance(v, Fraction) else v for v in d['weights'].values())
    step = (wmin * 100 / n) if d['ref'] == 'uniform' else None
    second = [SID[o] for o in ex.index if ex[o] == max(y for y in ex if y < max(ex))] if g is not None else []
    set_rows.append(dict(setting=sid_, role=d['role'], label=d['label'], indicators=' '.join(d['indicators']),
                         n_sites=n, candidate_set=d['ranked'], reference=d['ref'], tie_rule=d['rule'],
                         weights=' '.join(f'{c}={float(Fraction(v) if not isinstance(v, Fraction) else v):.4g}'
                                          for c, v in d['weights'].items()),
                         first=first_label(sid_), n_joint_first=len(firsts(sid_)),
                         first_score=round(float(max(ex)), 4),
                         runner_up=' = '.join(second), gap_to_runner_up=None if g is None else float(g),
                         gap_in_one_position_steps=None if (g is None or step is None) else float(g / step)))
first_tab = pd.DataFrame(set_rows)
write(first_tab.round(6), 'first_place_by_setting.csv')

def _dir(c, flip):
    low = (c in LOWER) != (c in flip)
    return f'{c} {"lower" if low else "higher"} preferred'


setdefs = pd.DataFrame([dict(setting=k, role=v['role'], label=v['label'], n_sites=len(SETS[v['ranked']]),
                             candidate_set=v['ranked'], reference=v['ref'], tie_rule=v['rule'],
                             scored_indicators='; '.join(_dir(c, v['flip']) for c in v['indicators']),
                             weights=' '.join(f'{c}={Fraction(w) if not isinstance(w, Fraction) else w}'
                                              for c, w in v['weights'].items()),
                             peak_share='described only, not scored' if 'peak_share' not in v['indicators']
                             else 'scored, direction as listed')
                        for k, v in SETTINGS.items()])
write(setdefs, 'settings.csv')

wide = audit[['site_oid', 'sid', 'municipal', 'station', 'record_classes', 'cost_indicator',
              'jobs45tr_status', 'in_main_set']].copy()
for c in IND5:
    wide[c] = site[c]
for sid_ in SETTINGS:
    wide[f'score_{sid_}'] = SCORE[sid_].reindex(wide.index).round(6)
    wide[f'rank_{sid_}'] = RANK[sid_].reindex(wide.index).astype('Int64')
write(wide.sort_values('rank_M3_equal'), 'rankings_by_setting.csv')

top_rows = []
for sid_ in SETTINGS:
    r = RANK[sid_]
    for o in r[r <= 10].sort_values().index:
        top_rows.append(dict(setting=sid_, rank=int(r[o]), sid=SID[o], site_oid=o,
                             municipal=site.municipal[o], score=round(SCORE[sid_][o], 4),
                             exact_tie_with_another=int((EXACT[sid_] == EXACT[sid_][o]).sum()) > 1))
write(pd.DataFrame(top_rows), 'top10_by_setting.csv')


def compare(a, b, what):
    common = RANK[a].index.intersection(RANK[b].index)
    ra, rb = RANK[a][common], RANK[b][common]
    ta, tb = set(RANK[a][RANK[a] <= 10].index), set(RANK[b][RANK[b] <= 10].index)
    return dict(change=what, setting_a=a, setting_b=b, first_a=first_label(a), first_b=first_label(b),
                same_first=set(firsts(a)) == set(firsts(b)), n_common=len(common),
                top10_overlap=len(ta & tb), top10_only_a='; '.join(SID[o] for o in sorted(ta - tb, key=lambda o: RANK[a][o])),
                top10_only_b='; '.join(SID[o] for o in sorted(tb - ta, key=lambda o: RANK[b][o])),
                spearman=round(SCORE[a][common].corr(SCORE[b][common], method='spearman'), 4),
                kendall_tau_b=round(SCORE[a][common].corr(SCORE[b][common], method='kendall'), 4),
                max_abs_rank_shift=int((ra - rb).abs().max()),
                median_abs_rank_shift=float((ra - rb).abs().median()))


cmp_rows = []
for name in SCENARIOS:
    k, nm = SCEN_ID[name], SCEN_LABEL[name]
    cmp_rows += [compare(f'S0_{k}', f'S1_{k}', f'record handling only | {nm}'),
                 compare(f'S1_{k}', f'S2_{k}', f'tie rule only, baseline reference | {nm}'),
                 compare(f'S2u_{k}', f'S3_{k}', f'tie rule only, candidate-set reference | {nm}'),
                 compare(f'S1_{k}', f'S2u_{k}', f'reference only, strict ties | {nm}'),
                 compare(f'S2_{k}', f'S3_{k}', f'reference only, mid-rank ties | {nm}'),
                 compare(f'K3_{k}', f'S3_{k}', f'record handling only, S3 rules | {nm}'),
                 compare(f'S0_{k}', f'S3_{k}', f'all changes together, not attributable to one | {nm}')]
cmp_rows += [compare('S3_equal', 'M3_equal', 'remove peak share: four-indicator S3 to three-indicator main M3'),
             compare('S0_equal', 'M3_equal', 'historical baseline to main M3: all changes together'),
             compare('M3_equal', 'X4_peak_low_equal', 'main M3 vs exploratory: add peak share, lower preferred'),
             compare('M3_equal', 'X4_peak_high_equal', 'main M3 vs exploratory: add peak share, higher preferred'),
             compare('X4_peak_low_equal', 'X4_peak_high_equal', 'peak share direction only'),
             compare('S3_equal', 'E3_equal', 'accessibility extension: S3 + jobs45tr'),
             compare('E2_equal', 'E3_equal', 'reference only, five indicators, mid-rank'),
             compare('E3_equal', 'E3u_equal', 'jobs45tr zero: as recorded vs unknown'),
             compare('E0_equal', 'E3_equal', 'five indicators: round-1 rules vs S3 rules')]
# X4_peak_low is S3_equal under another name; say so rather than let it look new.
assert (EXACT['X4_peak_low_equal'] == EXACT['S3_equal']).all()
comparisons = pd.DataFrame(cmp_rows)
write(comparisons, 'setting_comparisons.csv')

# ---------------------------------------------------------------------------
# 5. What the transform does
# ---------------------------------------------------------------------------

tr_rows = []
for ranked_key, ref, rule in [('all251', 'mixed0', 'strict'), ('main', 'mixed0', 'strict'),
                              ('main', 'mixed0', 'midrank'), ('main', 'uniform', 'strict'),
                              ('main', 'uniform', 'midrank')]:
    ranked = SETS[ranked_key]
    tab = pct_table(ranked, ref, rule, IND5)
    for c in IND5:
        raw = site.loc[ranked, c].to_numpy()
        p = np.array([float(x) for x in tab[c]])
        exact = pd.Series(tab[c])
        g = pd.DataFrame({'raw': raw, 'p': exact})
        pairs = lambda col: int((g.groupby(col).size() * (g.groupby(col).size() - 1) / 2).sum())
        best = p[np.argmin(raw)] if c in LOWER else p[np.argmax(raw)]
        worst = p[np.argmax(raw)] if c in LOWER else p[np.argmin(raw)]
        n_ref = len(site.loc[ranked]) if ref == 'uniform' else (
            len(REGION_REF[c]) if c in REGION_REF else 251)
        tr_rows.append(dict(candidate_set=ranked_key, n_sites=len(ranked), reference=ref, rule=rule,
                            indicator=c, direction='lower' if c in LOWER else 'higher',
                            n_reference=n_ref, distinct_raw=len(set(raw)), distinct_score=exact.nunique(),
                            tied_pairs_in_data=pairs('raw'),
                            ties_created_by_transform=pairs('p') - pairs('raw'),
                            largest_tie_group=int(g.groupby('raw').size().max()),
                            best_site_score=round(best, 3), worst_site_score=round(worst, 3),
                            p10=round(np.percentile(p, 10), 2), median=round(np.median(p), 2),
                            p90=round(np.percentile(p, 90), 2), sd=round(p.std(ddof=1), 2)))
transform = pd.DataFrame(tr_rows)
write(transform, 'transform_rules.csv')
assert (transform.ties_created_by_transform == 0).all()

# ---------------------------------------------------------------------------
# 6. Weight spaces
# ---------------------------------------------------------------------------

DRAWS = {3: dirichlet(3, SEED, N_DRAWS), 4: dirichlet(4, SEED, N_DRAWS), 5: dirichlet(5, SEED, N_DRAWS)}
WS_SETTINGS = ['M3', 'S0', 'S1', 'S2', 'S2u', 'S3', 'K3', 'E0', 'E2', 'E3', 'E3u']


def ws_matrix(st, subset=None):
    d = SETTINGS[f'{st}_equal']
    tab = pcts(d)
    ranked = SETS[d['ranked']]
    cols = d['indicators']
    P = np.array([[float(tab[c][i]) for c in cols] for i in range(len(ranked))])
    groups = vector_groups(np.array([[tab[c][i] for c in cols] for i in range(len(ranked))], dtype=object))
    idx = pd.Index(ranked)
    if subset is not None:
        keep = idx.isin(subset)
        return P[keep], groups[keep], idx[keep], d['k']
    return P, groups, idx, d['k']


WS, ws_rows, ws_sum = {}, [], []
for st in WS_SETTINGS:
    P, groups, idx, k = ws_matrix(st)
    r = weight_space(P, DRAWS[k], groups)
    WS[st] = (r, idx)
    assert abs(r['split'].sum() - 1) < 1e-9
    frontier = pareto_mask(np.c_[[(-site.loc[idx, c] if c in LOWER else site.loc[idx, c]).to_numpy()
                                  for c in SETTINGS[f'{st}_equal']['indicators']]].T)
    for n, o in enumerate(idx):
        ws_rows.append(dict(setting=st, indicators=k, alpha='(' + ','.join(['1'] * k) + ')',
                            seed=SEED, n_draws=N_DRAWS, site_oid=o, sid=SID[o],
                            municipal=site.municipal[o], on_frontier=bool(frontier[n]),
                            split_share=r['split'][n], unique_win_share=r['unique'][n],
                            joint_win_share=r['joint'][n], argmax_share=r['argmax'][n],
                            top5_share=r['top5'][n],
                            mc_se=np.sqrt(r['split'][n] * (1 - r['split'][n]) / N_DRAWS)))
    sh = pd.Series(r['split'], index=SID[idx].values).sort_values(ascending=False)
    ever = sh[sh > 0]
    ws_sum.append(dict(setting=st, indicators=k, n_sites=len(idx),
                       candidate_set=SETTINGS[f'{st}_equal']['ranked'],
                       reference=SETTINGS[f'{st}_equal']['ref'], tie_rule=SETTINGS[f'{st}_equal']['rule'],
                       alpha='(' + ','.join(['1'] * k) + ')', seed=SEED, n_draws=N_DRAWS,
                       draws_won_outright=round(float(r['unique'].sum()), 6),
                       draws_tied_identical_vectors=r['tied_identical'],
                       draws_tied_numerical=r['tied_numerical'],
                       split_shares_sum=round(float(r['split'].sum()), 12),
                       sites_ever_first=len(ever), sites_above_1pct=int((sh >= 0.01).sum()),
                       leader=ever.index[0], leader_share=round(ever.iloc[0], 4),
                       second=ever.index[1], second_share=round(ever.iloc[1], 4),
                       all_sites_ever_first='; '.join(f'{nm} {v:.4f}' for nm, v in ever.items())))
write(pd.DataFrame(ws_rows), 'weight_sensitivity.csv')
ws_sum = pd.DataFrame(ws_sum)
write(ws_sum, 'weight_sensitivity_summary.csv')

# Reproduce the baseline's printed shares the baseline's way.
F = [o for o, f in zip(ALL251, pareto_mask(np.c_[[(-site.loc[ALL251, c] if c in LOWER else site.loc[ALL251, c]).to_numpy() for c in IND4]].T)) if f]
PF = np.array([[float(P0[c][ALL251.index(o)]) for c in IND4] for o in F])
wins = np.bincount(np.argmax(DRAWS[4] @ PF.T, axis=1), minlength=len(F)) / N_DRAWS
b_share = pd.Series(wins, index=SID[F].values)
printed = {}
with open(BASE + 'run_stdout.txt', encoding='utf-8') as fh:
    lines = fh.read().splitlines()
for ln in lines[lines.index('sid') + 1:]:
    m = re.match(r'^(.+?#\d+)\s+(0\.\d+)$', ln)
    if not m:
        break
    printed[m.group(1)] = float(m.group(2))
assert b_share[b_share > 0.005].round(3).to_dict() == printed
check('baseline Dirichlet(1,1,1,1), seed 7, 200,000 draws reproduced', 'yes',
      f'{len(printed)} printed shares match; S0 split shares equal the baseline argmax shares: '
      f'{np.allclose(WS["S0"][0]["split"], b_share.reindex(SID[WS["S0"][1]].values).fillna(0).to_numpy())}')

seed_rows = []
for st in ['M3', 'S0', 'S3', 'E3']:
    P, groups, idx, k = ws_matrix(st)
    per = {sd: weight_space(P, dirichlet(k, sd, N_DRAWS), groups)['split'] for sd in SEEDS_CHECK}
    for n, o in enumerate(idx):
        vals = [per[sd][n] for sd in SEEDS_CHECK]
        if max(vals) > 0:
            seed_rows.append(dict(setting=st, sid=SID[o], site_oid=o,
                                  **{f'seed_{sd}': v for sd, v in zip(SEEDS_CHECK, vals)},
                                  min=min(vals), max=max(vals), range=max(vals) - min(vals)))
seed_stab = pd.DataFrame(seed_rows)
write(seed_stab, 'weight_seed_stability.csv')

# ---------------------------------------------------------------------------
# 7. Frontiers (raw values; the reference and the tie rule cannot move them)
# ---------------------------------------------------------------------------

fr_rows = []
FRONT = {}
for key, ranked, cols in [('3ind_main', MAIN, IND3),
                          ('4ind_all251', ALL251, IND4), ('4ind_main', MAIN, IND4),
                          ('5ind_all251', ALL251, IND5), ('5ind_main', MAIN, IND5),
                          ('5ind_main_jobs_known', MAIN_J, IND5)]:
    A = np.c_[[(-site.loc[ranked, c] if c in LOWER else site.loc[ranked, c]).to_numpy() for c in cols]].T
    fm = pareto_mask(A)
    assert ((~dominance(A).any(1)) == fm).all()
    FRONT[key] = pd.Series(fm, index=ranked)
for o in ALL251:
    row = dict(site_oid=o, sid=SID[o], municipal=site.municipal[o], station=site.station[o],
               in_main_set=o in MAIN)
    for key, f in FRONT.items():
        row[key] = bool(f.get(o, False)) if o in f.index else None
    fr_rows.append(row)
frontiers = pd.DataFrame(fr_rows)
write(frontiers, 'frontier_by_setting.csv')
fr_summary = pd.DataFrame([dict(frontier=k, sites=int(f.sum()),
                                communities=site.loc[f.index[f]].municipal.nunique(),
                                stations=site.loc[f.index[f]].station.nunique())
                           for k, f in FRONT.items()])
write(fr_summary, 'frontier_summary.csv')
entered = FRONT['4ind_main'][FRONT['4ind_main']].index.difference(FRONT['4ind_all251'][FRONT['4ind_all251']].index)
check('four-indicator frontier, all 251 vs main set', f'{int(FRONT["4ind_all251"].sum())} vs {int(FRONT["4ind_main"].sum())}',
      'entering once the excluded records are gone: ' + (', '.join(SID[entered]) or 'none'))
f3, f4 = FRONT['3ind_main'], FRONT['4ind_main']
out3 = f3[f3].index.difference(f4[f4].index)
check('three-indicator main frontier against the four-indicator one, same 246',
      f'{int(f3.sum())} vs {int(f4.sum())}',
      'on the three but not the four: ' + (', '.join(SID[out3]) or 'none') + '; on the four only: '
      + ', '.join(SID[f4[f4].index.difference(f3[f3].index)]), 'note')

# ---------------------------------------------------------------------------
# 8. Quincy only, every score held fixed
# ---------------------------------------------------------------------------

QUINCY = set(site.index[site.municipal == 'Quincy'])
q_rows = []
for sid_, d in SETTINGS.items():
    ex = EXACT[sid_]
    qx = ex[ex.index.isin(QUINCY)]
    qf = [qx.index[i] for i in top_set(list(qx))]
    r = RANK[sid_]
    top_all = r[r <= 10].sort_values().index
    q_rows.append(dict(setting=sid_, label=d['label'], n_all=len(ex), n_quincy=len(qx),
                       first_all=first_label(sid_),
                       first_all_in_quincy=any(o in QUINCY for o in firsts(sid_)),
                       first_quincy=' = '.join(SID[o] for o in qf),
                       first_quincy_rank_in_all=int(r[qf[0]]),
                       sites_above_best_quincy=int((ex > qx.max()).sum()),
                       quincy_top3='; '.join(SID[o] for o in qx.sort_values(ascending=False).index[:3]),
                       all_top10_outside_quincy='; '.join(SID[o] for o in top_all if o not in QUINCY),
                       all_top10_in_quincy=int(sum(o in QUINCY for o in top_all))))
quincy = pd.DataFrame(q_rows)
write(quincy, 'quincy_vs_all.csv')
qws = []
for st in ['M3', 'S0', 'S3', 'E3', 'E3u']:
    P, groups, idx, k = ws_matrix(st, subset=QUINCY)
    r = weight_space(P, DRAWS[k], groups)
    full, fidx = WS[st]
    full = pd.Series(full['split'], index=fidx)
    for n, o in enumerate(idx):
        qws.append(dict(setting=st, sid=SID[o], site_oid=o, station=site.station[o],
                        split_share_within_quincy=r['split'][n],
                        unique_win_share_within_quincy=r['unique'][n],
                        split_share_among_all=full[o],
                        quincy_total_share_among_all=float(full[full.index.isin(QUINCY)].sum())))
qws = pd.DataFrame(qws)
qws = qws[(qws.split_share_within_quincy > 0) | (qws.split_share_among_all > 0)]
write(qws.sort_values(['setting', 'split_share_within_quincy'], ascending=[True, False]),
      'quincy_weight_space.csv')

# ---------------------------------------------------------------------------
# 9. Key sites, dictionary, other checks
# ---------------------------------------------------------------------------

key = set()
for sid_ in SETTINGS:
    key |= set(firsts(sid_))
for st, (r, idx) in WS.items():
    key |= set(idx[r['split'] >= 0.02])
key |= {o for o in ALL251 if SID[o] in ('Quincy Center #1', 'Wollaston #1')}
key |= set(EXCLUDED)
KEY_SETTINGS = ['M3_equal', 'S0_equal', 'S1_equal', 'S2_equal', 'S3_equal', 'K3_equal',
                'X4_peak_high_equal', 'E3_equal', 'E3u_equal',
                'S0_developer', 'S3_developer', 'S3_city', 'S3_transit', 'S3_placemaking']
ks = audit.loc[sorted(key, key=lambda o: (RANK['M3_equal'].get(o, 999), RANK['S0_equal'][o])),
               ['site_oid', 'sid', 'municipal', 'cost_indicator', 'in_main_set']].copy()
ks['peak_share'] = site.peak_share.reindex(ks.index).round(4)       # described, not scored in M3
for sid_ in KEY_SETTINGS:
    ks[f'rank_{sid_}'] = RANK[sid_].reindex(ks.index).astype('Int64')
for st in ['M3', 'S0', 'S3', 'E3']:
    r, idx = WS[st]
    ks[f'split_share_{st}'] = pd.Series(r['split'], index=idx).reindex(ks.index).round(4)
write(ks, 'key_site_ranks.csv')

DICT = [
    dict(column='ppa', name='Assessed land value per acre', direction='lower preferred (a comparison preference of this study)',
         source='MAPC Rethinking the Retail Strip Sites (DataCommon 442)',
         vintage='MAPC publication 14 Jan 2022; assessment year not stated',
         computation='land_value / sitearea_a; land_value is "combined assessed land value of all parcels '
                     'in site", and the parcels listed are those that overlap the site',
         proxy_for='land-cost exposure',
         status='scored in M3; five candidates temporarily excluded because the valuation cannot be '
                'reliably attributed to the site (three attribution problems, two conservative)',
         limitations='assessed for taxation, not a sale or acquisition price; excludes buildings, '
                     'demolition, holding costs'),
    dict(column='buildar_ac', name='Buildable area', direction='larger preferred (a comparison preference of this study)',
         source='MAPC 442', vintage='as published', computation='MAPC field, acres', proxy_for='developable scale',
         status='scored in M3', limitations='MAPC method; a site may be several parcels; four candidates have a '
                                    'recorded area that differs from the decoded area by more than 2%'),
    dict(column='daily', name='Daily boardings + alightings at the nearest rated station',
         direction='higher preferred (a comparison preference of this study)',
         source='MBTA Fall 2025 rail ridership by hour, route/line and stop',
         vintage='Fall 2025',
         computation='(5 x weekday + 2 x mean weekend day) / 7 of the sum over hours, routes and directions '
                     'of average_ons + average_offs',
         proxy_for='existing station activity', status='scored in M3',
         limitations='movements, not distinct riders and not future or induced demand; station-level, so '
                     'sites at one station tie; hourly averages rounded in the source'),
    dict(column='peak_share', name='Weekday peak-hour share of boardings + alightings',
         direction='none in the main comparison; lower or higher preferred only in labelled exploratory '
                   'settings (S*, K3, E*, X4_peak_low; X4_peak_high)',
         source='MBTA Fall 2025', vintage='Fall 2025',
         computation='weekday on+off in 07-09 and 16-18 / all weekday on+off',
         proxy_for='how concentrated weekday station activity is in the peaks',
         status='described only in M3; scored only in the historical S-settings and the X4 exploratory pair',
         limitations='not a measure of all-day or weekly evenness; station-level'),
    dict(column='jobs45tr', name='Jobs reachable by transit within 45 minutes, AM peak',
         direction='higher is better', source='MAPC 442, citing the University of Minnesota Accessibility '
         'Observatory ("Access Across America")',
         vintage='MAPC gitbook dictionary: "Minnesota Accessibility Observatory, 2016"; MAPC references: '
                 '"Access Across America: Transit 2018 Data" (Owen & Murphy, 2020); DataCommon metadata: 2018. '
                 'The 2016 edition uses LEHD LODES 2014 jobs and GTFS "various dates"; the jobs year of the '
                 '2018 edition was not retrieved. Either way the network predates Jan 2022',
         computation='MAPC field, used as is', proxy_for='historical regional access to employment',
         status='only in E0-E3u, the historical accessibility extension of the four-indicator S3; not an '
                'extension of M3',
         limitations='transit network predates the Green Line Extension (service from Mar and Dec 2022) '
                     'and MAPC published before it opened; jobs year and network year are different things '
                     'and neither is the 2025 of the ridership; two candidates record 0, unverified'),
    dict(column='station_km', name='Straight-line distance to nearest rated station', direction='filter (<= 0.805 km)',
         source='boston_subway_stations_info.csv', vintage='project station list',
         computation='equirectangular approximation, site centroid to station', proxy_for='proximity',
         status='kept as the baseline filter', limitations='not walking distance'),
    dict(column='excl_p / fz100_p', name='Overlap with non-buildable land / FEMA 1% flood zone',
         direction='filters (each < 50)', source='MAPC 442', vintage='flood layer July 2017 (MAPC dictionary)',
         computation='MAPC fields', proxy_for='physical constraint', status='kept',
         limitations='two separate conditions, not their sum; not a permitting test'),
]
write(pd.DataFrame(DICT), 'indicator_dictionary.csv')

idmap = audit[['site_oid', 'objectid', 'sid', 'station', 'municipal', 'nparcels', 'parcelids',
               'record_classes', 'cost_indicator', 'in_main_set']].copy()
idmap['code'] = site.code
idmap['mapc_station'] = site.mapc_station
idmap['merged_into'] = ''            # no record is merged: none is the same site as another
idmap['sid_source'] = f'build_2026.py at {BASELINE_COMMIT}; frozen, not renumbered after exclusions'
write(idmap.sort_values(['station', 'sid']), 'site_id_map.csv')

cand = audit.copy()
cand['line'] = site.line
for c in IND5 + ['excl_p', 'fz100_p', 'regipctile']:
    cand[c] = site[c]
cand['straight_line_km'] = site.station_km.round(4)
cand['frontier4_all251'] = FRONT['4ind_all251']
cand['frontier4_main'] = FRONT['4ind_main'].reindex(cand.index)
write(cand.sort_values(['station', 'sid']), 'candidates_quality.csv')

for c in IND5:
    bad = int(site[c].isna().sum() + np.isinf(site[c]).sum())
    check(f'missing or infinite values: {c}', f'{bad} of 251', status='ok' if bad == 0 else 'check')
check('site_oid unique (region, candidates)', f'{s.site_oid.is_unique}, {site.site_oid.is_unique}')
st_c = site.drop_duplicates('station')
check('daily vs weekend, Pearson: site level / 39 candidate stations',
      f'{site.daily.corr(site.weekend):.3f} / {st_c.daily.corr(st_c.weekend):.3f}')
for sid_ in SETTINGS:
    if len(firsts(sid_)) > 1:
        check(f'exact joint first place: {sid_}', first_label(sid_), status='note')
check('ties created by either percentile rule between distinct raw values', '0',
      'every candidate value is also in its reference, so distinct values keep distinct scores')
checks = pd.DataFrame(CHECKS)
write(checks, 'internal_checks.csv')

# ---------------------------------------------------------------------------
# 10. Figures
# ---------------------------------------------------------------------------

STEP_LABEL = {'S0': 'S0 baseline\ne18a184', 'S1': 'S1 + record\nhandling', 'S2': 'S2 + mid-rank\nties',
              'S3': 'S3 + candidate-set\nreference', 'M3': 'M3 main\n(three indicators)',
              'E2': 'E2 five, baseline\nreference', 'E3': 'E3 = S3 + jobs45tr\n(zero as recorded)',
              'E3u': 'E3u = S3 + jobs45tr\n(zero as unknown)'}

# F1. First-place share, every site that reaches 1% in some column. Three
# weight spaces of different dimension, drawn apart and never compared.
panels = [('Main M3: three indicators,\nDirichlet(1,1,1)', ['M3'], 'M3'),
          ('Historical revision: four indicators,\nDirichlet(1,1,1,1)', ['S0', 'S1', 'S2', 'S3'], 'S3'),
          ('Historical accessibility extension of S3,\nDirichlet(1,1,1,1,1)', ['E2', 'E3', 'E3u'], 'E3')]
tabs = []
for title, cols, sort_by in panels:
    t_ = pd.DataFrame({st: pd.Series(WS[st][0]['split'], index=SID[WS[st][1]].values) for st in cols}).fillna(0)
    t_ = t_[(t_ >= 0.01).any(axis=1)]
    tabs.append(t_.loc[t_[sort_by].sort_values().index])
h = max(len(x) for x in tabs) * 0.36 + 2.2
fig, axes = plt.subplots(1, 3, figsize=(16, h), gridspec_kw={'width_ratios': [1.7, 4, 3]})
for ax, (title, cols, _), t_ in zip(axes, panels, tabs):
    for j, st in enumerate(cols):
        for i, (nm, v) in enumerate(t_[st].items()):
            if v > 0:
                ax.scatter(j, i, s=v * 2600 + 6, color=ACCENT if st == 'M3' else ACCENT2,
                           alpha=0.9, lw=0, zorder=3)
            ax.text(j + 0.2, i, f'{v:.0%}' if v >= 0.005 else ('<1%' if v > 0 else '—'),
                    va='center', fontsize=8.6, color=INK if v >= 0.05 else MUTE)
    ax.set_yticks(range(len(t_)), t_.index, fontsize=9.5)
    ax.set_xticks(range(len(cols)), [STEP_LABEL[c] for c in cols], fontsize=8.8)
    ax.set_xlim(-0.5, len(cols) - 0.2 + (0.4 if len(cols) == 1 else 0))
    ax.set_ylim(-0.7, len(t_) - 0.3)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(title, fontsize=11)
fig.suptitle('Share of 200,000 sampled weightings in which each site comes first',
             x=0.005, ha='left', fontweight='bold', fontsize=13)
fig.text(0.005, 0.005, 'Shares split equally between joint winners; seed 7. The three panels are weight spaces of '
         'different dimension, so shares are not comparable across them. A share describes the sampling scheme, '
         'not a real preference, a probability of success or of being the best site.', fontsize=8.8, color=MUTE)
plt.tight_layout(rect=(0, 0.03, 1, 0.95))
save('f1-first-place-by-step')

# F2. Equal-weight rank of the leading sites: historical steps, main, extension.
order = ['S0_equal', 'S1_equal', 'S2_equal', 'S3_equal', 'M3_equal', 'E3_equal', 'E3u_equal']
xl = [STEP_LABEL[o.split('_')[0]] for o in order]
show = [o for o in ks.index if any(RANK[st].get(o, 99) <= 10
                                   for st in ['S0_equal', 'S3_equal', 'M3_equal', 'E3_equal'])]
CAP = 25


def fanned(col):
    """Label positions: sites drawn at the same height are spread around it."""
    ys = {o: min(RANK[col][o], CAP) for o in show if o in RANK[col].index}
    out = {}
    for yv in set(ys.values()):
        grp = sorted([o for o in ys if ys[o] == yv], key=lambda o: RANK[col][o])
        for j, o in enumerate(grp):
            out[o] = yv + (j - (len(grp) - 1) / 2) * 0.62
    return out


fig, ax = plt.subplots(figsize=(15, 8))
xs = [0, 1, 2, 3, 4.4, 6.6, 7.6]
left, mlab, right = fanned(order[0]), fanned(order[4]), fanned(order[6])
for o in show:
    ys = [RANK[st].get(o, np.nan) for st in order]
    yc = [min(y, CAP) if not np.isnan(y) else np.nan for y in ys]
    hot = o in firsts('M3_equal')
    col = ACCENT if hot else ACCENT2
    ax.plot(xs[:4], yc[:4], '-o', color=col, lw=1.3, ms=4.5, zorder=3, alpha=0.8)
    ax.plot([xs[4]], [yc[4]], 'o', color=col, ms=8, zorder=4)
    ax.plot(xs[5:], yc[5:], '-o', color=col, lw=1.3, ms=4.5, zorder=3, alpha=0.8)
    ax.text(-0.12, left[o], f'{SID[o]}  {int(ys[0])}', ha='right', va='center', fontsize=8.8, color=INK)
    if o in mlab:
        ax.text(4.56, mlab[o], f'{int(ys[4])}  {SID[o]}', ha='left', va='center', fontsize=8.8,
                color=INK, fontweight='bold' if o in firsts('M3_equal') else 'normal')
    if o in right:
        ax.text(7.72, right[o], f'{int(ys[6])}  {SID[o]}', ha='left', va='center', fontsize=8.8, color=INK)
for xv in (3.7, 6.1):
    ax.axvline(xv, color=FAINT, lw=1.2)
ax.axhspan(10.5, CAP + 1, color=FAINT, alpha=0.35, lw=0, zorder=0)
ax.set_ylim(CAP + 1, 0.3)
ax.set_xlim(-1.9, 9.5)
ax.set_xticks(xs, xl, fontsize=8.8)
ax.set_yticks([])
ax.grid(False)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_title('Equal-weight rank of the leading sites: historical steps, main comparison, accessibility extension')
fig.text(0.005, 0.005, f'Sites in a top ten at S0, S3, M3 or E3. Joint ranks share a number. Shaded: outside the '
         f'top ten; ranks past {CAP} drawn at {CAP}, labelled with the actual rank. Orange: joint first in the main '
         'M3. Left: four indicators, S0 to S3. Centre: the main three-indicator comparison. Right: S3 plus job '
         'access, which extends S3, not M3.', fontsize=8.8, color=MUTE)
plt.tight_layout(rect=(0, 0.04, 1, 1))
save('f2-key-site-ranks-by-step')

# F3. Quincy only, every score held fixed.
qs = (['M3_equal'] + ['S3_' + SCEN_ID[n] for n in SCENARIOS] + ['S0_' + SCEN_ID[n] for n in SCENARIOS]
      + ['E3_equal', 'E3u_equal'])
qq = quincy.set_index('setting').loc[qs].iloc[::-1]
lab = {'M3_equal': 'Main M3 · equal weights (three indicators)',
       **{f'S3_{v}': f'{SCEN_LABEL[k]} · S3' for k, v in SCEN_ID.items()},
       **{f'S0_{v}': f'{SCEN_LABEL[k]} · baseline S0' for k, v in SCEN_ID.items()},
       'E3_equal': 'E3 = S3 + jobs45tr · zero as recorded',
       'E3u_equal': 'E3u = S3 + jobs45tr · zero as unknown'}
fig, ax = plt.subplots(figsize=(13.5, 6.8))
yy = np.arange(len(qq))
ax.scatter(qq.first_quincy_rank_in_all, yy, s=[90 if i == 'M3_equal' else 55 for i in qq.index], zorder=3,
           color=[ACCENT if i == 'M3_equal' else MUTE if i.startswith('S0') else ACCENT2 for i in qq.index])
for yv, (i, r) in zip(yy, qq.iterrows()):
    ax.text(r.first_quincy_rank_in_all * 1.12, yv, r.first_quincy, va='center', fontsize=9, color=INK)
    ax.text(62, yv, r.first_all, va='center', fontsize=9, color=MUTE)
ax.set_xscale('log')
ax.set_xlim(0.8, 260)
ax.set_xticks([1, 2, 5, 10, 20])
ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f'{v:g}'))
ax.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
ax.set_yticks(yy, [lab[i] for i in qq.index], fontsize=9)
ax.grid(axis='y', visible=False)
ax.text(62, len(qq) - 0.3, 'first among all candidates', fontsize=9, color=MUTE, fontweight='bold', va='bottom')
ax.set_xlabel('rank among all candidates of the best Quincy site (scores and reference fixed; log scale)')
ax.set_title('What restricting the candidates to Quincy leaves, with every score held fixed')
save('f3-quincy-only')

# ---------------------------------------------------------------------------
# 11. Manifest and summary
# ---------------------------------------------------------------------------

manifest = {
    'baseline_commit': git('rev-parse', BASELINE_COMMIT),
    'working_tree_head': git('rev-parse', 'HEAD'),
    'working_tree_dirty': bool(git('status', '--porcelain')),
    'commands': ['python revision/reproduce_baseline.py', 'python revision/checks.py',
                 'python revision_2026.py'],
    'script_sha256': {f: sha256(f) for f in ['revision_2026.py', 'revision/methods.py',
                                             'revision/geometry.py', 'revision/checks.py',
                                             'revision/reproduce_baseline.py']},
    'seeds': {'dirichlet': SEED, 'seed_stability_check': list(SEEDS_CHECK)},
    'n_draws': N_DRAWS, 'tie_tolerance_random_weights': TOL,
    'deterministic_ties': 'exact rational arithmetic',
    'main_setting': ('M3_equal: 246 candidates, three indicators (ppa lower, buildar_ac larger, daily '
                     'higher preferred), candidate-set reference, mid-rank percentiles, exact 1/3 '
                     'weights; peak share described only'),
    'main_candidate_set_size': len(MAIN), 'excluded_site_oids': EXCLUDED,
    'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                    'numpy': np.__version__, 'pandas': pd.__version__, 'matplotlib': mpl.__version__,
                    'scipy': __import__('scipy').__version__, 'pyarrow': __import__('pyarrow').__version__},
    'data_sha256': {f: sha256(DATA + f) for f in sorted(os.listdir(DATA))},
    'baseline_outputs_sha256': json.load(open(BASE + 'manifest.json', encoding='utf-8'))['outputs_sha256'],
    'geometry_validation': val,
    'outputs': sorted(os.listdir(OUT)), 'figures': sorted(os.listdir(FIG)),
}
with open('revision/manifest.json', 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(manifest, fh, indent=2)
    fh.write('\n')

summary = {
    'main_set': len(MAIN), 'excluded': {SID[o]: o for o in EXCLUDED},
    'jobs_zero': {SID[o]: o for o in JOBS0},
    'first_place': first_tab.set_index('setting')[['first', 'gap_to_runner_up',
                                                   'gap_in_one_position_steps']].to_dict('index'),
    'weight_space': ws_sum.set_index('setting')[['leader', 'leader_share', 'second', 'second_share',
                                                 'sites_ever_first', 'draws_tied_identical_vectors',
                                                 'draws_tied_numerical']].to_dict('index'),
    'frontiers': fr_summary.set_index('frontier').to_dict('index'),
}
with open(OUT + 'summary.json', 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(summary, fh, indent=2, default=str)
    fh.write('\n')

print(f'main set: {len(MAIN)} sites; excluded: ' + ', '.join(SID[o] for o in EXCLUDED))
print(first_tab[first_tab.setting.str.endswith(('equal', 'developer'))]
      [['setting', 'n_sites', 'first', 'gap_to_runner_up', 'gap_in_one_position_steps']].to_string(index=False))
print(ws_sum[['setting', 'n_sites', 'leader', 'leader_share', 'second', 'second_share', 'sites_ever_first',
              'draws_tied_identical_vectors', 'draws_tied_numerical']].to_string(index=False))
print(fr_summary.to_string(index=False))
print('written:', len(os.listdir(OUT)), 'tables,', len(os.listdir(FIG)), 'figures')
