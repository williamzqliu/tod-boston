"""Read the site polygons that ship inside the MAPC inventory.

The `shape` column of `mapc.rethinking_retail_sites.csv` is a hex dump of an
Esri ST_Geometry value. It is not documented in the file, so the decoding here
was worked out from the bytes and is validated against the inventory's own
fields rather than taken on trust:

    bytes 0-3    total length (always equals the byte count)
    bytes 4-7    number of points, including part separators
    bytes 8-11   entity flags (polygon)
    bytes 12-15  SRID 26986, NAD83 / Massachusetts Mainland, metres
    bytes 24-    signed variable-length integers: bit 7 continues, bit 6 of
                 the first byte is the sign, 6 then 7 value bits per byte.
                 The first pair is absolute, every later pair a delta. A pair
                 that lands on the raw origin separates the parts of a
                 multi-part polygon.

Raw units are 1/10,000 m from a false origin of (-36,530,900, -28,803,200) m,
ArcSDE's usual grid for this projection. `validate()` reports how well that
reproduces MAPC's recorded site area and centroid; at the time of writing the
decoded area equals `sitearea_a` to 0.01 ac for 99.2% of the 3,028 sites and
the centroid lies within 0.2 m of MAPC's for 99% of them.

Overlap between two polygons is measured by sampling a 0.5 m grid over the
intersection of their bounding boxes, which is exact enough to tell a shared
footprint from a shared edge and needs nothing beyond numpy and matplotlib.
"""
import struct

import numpy as np
from matplotlib.path import Path

FALSE_X, FALSE_Y, UNITS_PER_M = -36_530_900.0, -28_803_200.0, 10_000.0
SQM_PER_ACRE = 4046.8564224


def _varints(b, pos):
    out = []
    while pos < len(b):
        c = b[pos]
        pos += 1
        neg, val, shift = c & 0x40, c & 0x3F, 6
        while c & 0x80:
            if pos >= len(b):
                return out
            c = b[pos]
            pos += 1
            val |= (c & 0x7F) << shift
            shift += 7
        out.append(-val if neg else val)
    return out


def rings(hexstr):
    """Closed rings of one site polygon, as (x, y) arrays in metres."""
    b = bytes.fromhex(hexstr)
    npts = struct.unpack('<I', b[4:8])[0]
    v = _varints(b, 24)[:2 * npts]
    x = np.cumsum(v[0::2]).astype(float)
    y = np.cumsum(v[1::2]).astype(float)
    sep = (np.abs(x) < UNITS_PER_M) & (np.abs(y) < UNITS_PER_M)
    parts, cur = [], []
    for k in range(len(x)):
        if sep[k]:
            if cur:
                parts.append(cur)
            cur = []
        else:
            cur.append(k)
    if cur:
        parts.append(cur)
    out = []
    for idx in parts:
        px = x[idx] / UNITS_PER_M + FALSE_X
        py = y[idx] / UNITS_PER_M + FALSE_Y
        start, i = 0, 1
        while i < len(px):
            if px[i] == px[start] and py[i] == py[start]:
                out.append((px[start:i + 1], py[start:i + 1]))
                start, i = i + 1, i + 2
            else:
                i += 1
        if start < len(px) - 1:
            out.append((px[start:], py[start:]))
    return out


def area_m2(rs):
    total = 0.0
    for rx, ry in rs:
        ax, ay = rx - rx[0], ry - ry[0]
        total += (ax[:-1] * ay[1:] - ax[1:] * ay[:-1]).sum() / 2
    return abs(total)


def centroid(rs):
    a = cx = cy = 0.0
    x0, y0 = rs[0][0][0], rs[0][1][0]
    for rx, ry in rs:
        ax, ay = rx - x0, ry - y0
        cr = ax[:-1] * ay[1:] - ax[1:] * ay[:-1]
        a += cr.sum() / 2
        cx += ((ax[:-1] + ax[1:]) * cr).sum() / 6
        cy += ((ay[:-1] + ay[1:]) * cr).sum() / 6
    return cx / a + x0, cy / a + y0


def bbox(rs):
    xs = np.concatenate([r[0] for r in rs])
    ys = np.concatenate([r[1] for r in rs])
    return xs.min(), ys.min(), xs.max(), ys.max()


def _inside(rs, pts):
    c = np.zeros(len(pts), int)
    for rx, ry in rs:
        c += Path(np.c_[rx, ry]).contains_points(pts)
    return c % 2 == 1          # even-odd, so holes subtract


def overlap_m2(ra, rb, step=0.5):
    a, b = bbox(ra), bbox(rb)
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x0 >= x1 or y0 >= y1:
        return 0.0
    gx, gy = np.meshgrid(np.arange(x0, x1, step) + step / 2,
                         np.arange(y0, y1, step) + step / 2)
    pts = np.c_[gx.ravel(), gy.ravel()]
    return float((_inside(ra, pts) & _inside(rb, pts)).sum() * step * step)


# NAD83 / Massachusetts Mainland (EPSG:26986), Lambert conformal conic on GRS80,
# written out so the validation needs no projection library.
_A, _F = 6378137.0, 1 / 298.257222101
_E = np.sqrt(2 * _F - _F * _F)
_P1, _P2, _P0, _L0 = np.radians([42 + 41 / 60, 41 + 43 / 60, 41.0, -71.5])
_m = lambda p: np.cos(p) / np.sqrt(1 - (_E * np.sin(p)) ** 2)
_t = lambda p: np.tan(np.pi / 4 - p / 2) / ((1 - _E * np.sin(p)) / (1 + _E * np.sin(p))) ** (_E / 2)
_N = (np.log(_m(_P1)) - np.log(_m(_P2))) / (np.log(_t(_P1)) - np.log(_t(_P2)))
_FF = _m(_P1) / (_N * _t(_P1) ** _N)
_R0 = _A * _FF * _t(_P0) ** _N


def project(lon, lat):
    p, lam = np.radians(lat), np.radians(lon)
    r = _A * _FF * _t(p) ** _N
    th = _N * (lam - _L0)
    return 200000.0 + r * np.sin(th), 750000.0 + _R0 - r * np.cos(th)


def validate(frame):
    """Decoded area and centroid against MAPC's own fields, every site."""
    rs = [rings(h) for h in frame['shape']]
    acres = np.array([area_m2(r) for r in rs]) / SQM_PER_ACRE
    cx, cy = np.array([centroid(r) for r in rs]).T
    X, Y = project(frame.long.to_numpy(), frame.lat.to_numpy())
    d = np.hypot(cx - X, cy - Y)
    return {
        'sites': len(frame),
        'area_equal_to_0.01_ac': float((np.round(acres, 2) == frame.sitearea_a.to_numpy()).mean()),
        'area_within_2pct': float((np.abs(acres / frame.sitearea_a.to_numpy() - 1) < 0.02).mean()),
        'centroid_offset_m_median': float(np.median(d)),
        'centroid_offset_m_p99': float(np.percentile(d, 99)),
    }, acres
