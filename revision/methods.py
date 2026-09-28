"""Scoring rules shared by revision_2026.py and revision/checks.py.

Percentile rules, for a value v against a reference of n values, with
L = #reference < v, E = #reference == v and G = #reference > v:

    strict   higher-is-better  100 * L / n
             lower-is-better   100 - 100 * L / n  =  100 * (G + E) / n
    midrank  higher-is-better  100 * (L + E/2) / n
             lower-is-better   100 * (G + E/2) / n  =  100 - the above

`strict` is the rule build_2026.py uses. Under it a tied group sits at the
bottom of its range when higher is better and at the top when lower is better,
so the same tie is scored differently depending on the indicator's direction:
the best value of a higher-is-better indicator gets 100 * (n - E) / n and the
best value of a lower-is-better one gets 100. `midrank` puts every tied group
at the middle of its range in both directions, so reversing an indicator maps
each score s to exactly 100 - s. Both rules give equal raw values equal scores,
and neither creates ties between distinct raw values when both values are in
the reference.

Scores are kept as exact fractions as well as floats. A deterministic setting
has decimal weights, so its scores are rational numbers and two sites either
tie exactly or they do not; the float is only for display. Random weights are
real numbers, so there a tie means two sites with the same percentile vector
(equal under every weighting), and anything else within TOL of the top is
counted separately as a numerical near-tie.
"""
from fractions import Fraction

import numpy as np

TOL = 1e-9


def pct_exact(values, base, lower, rule):
    b = np.sort(np.asarray(base, float))
    n = len(b)
    out = []
    for v in np.asarray(values, float):
        less = int(np.searchsorted(b, v, 'left'))
        eq = int(np.searchsorted(b, v, 'right')) - less
        if rule == 'strict':
            num = Fraction(n - less, n) if lower else Fraction(less, n)
        elif rule == 'midrank':
            below = Fraction(2 * less + eq, 2 * n)
            num = 1 - below if lower else below
        else:
            raise ValueError(rule)
        out.append(100 * num)
    return out


def exact_scores(pct_cols, weights):
    """pct_cols: {indicator: list of Fraction}; weights: {indicator: str or Fraction}."""
    w = {c: Fraction(str(v)) for c, v in weights.items()}
    n = len(next(iter(pct_cols.values())))
    return [sum(w[c] * pct_cols[c][i] for c in w) for i in range(n)]


def top_set(scores):
    """Indices of every site sharing the exact maximum."""
    m = max(scores)
    return [i for i, s in enumerate(scores) if s == m]


def runner_up_gap(scores):
    """Exact gap between the first score and the best score below it."""
    m = max(scores)
    below = [s for s in scores if s < m]
    return (m - max(below)) if below else None


def vector_groups(P):
    """Group id per row; rows with identical percentile vectors share an id."""
    keys = {}
    return np.array([keys.setdefault(tuple(r), len(keys)) for r in map(tuple, P)])


def weight_space(P, draws, groups=None, chunk=25_000):
    """First-place accounting over sampled weightings.

    For each draw, every site within TOL of the top score is a joint winner.
    `unique` counts draws a site wins alone, `joint` draws it shares, and
    `split` gives each of k joint winners 1/k, so the split shares sum to one.
    A tie is `identical` when all joint winners share one percentile vector
    and `numerical` otherwise. `argmax` is the row-order rule the baseline
    used, kept only to show where it would have differed.
    """
    P = np.asarray(P, float)
    n, m = len(draws), P.shape[0]
    groups = vector_groups(P) if groups is None else groups
    unique, joint, split, argm, top5 = (np.zeros(m) for _ in range(5))
    tied_identical = tied_numerical = 0
    for a in range(0, n, chunk):
        S = draws[a:a + chunk] @ P.T
        mx = S.max(1, keepdims=True)
        at = S >= mx - TOL
        k = at.sum(1)
        split += (at / k[:, None]).sum(0)
        unique += at[k == 1].sum(0)
        joint += at[k > 1].sum(0)
        argm += np.bincount(S.argmax(1), minlength=m)
        for row in np.where(k > 1)[0]:
            g = groups[at[row]]
            if (g == g[0]).all():
                tied_identical += 1
            else:
                tied_numerical += 1
        if m > 5:
            v5 = np.partition(S, m - 5, axis=1)[:, m - 5:m - 4]
            top5 += (S >= v5 - TOL).sum(0)
        else:
            top5 += len(S)
    return {'unique': unique / n, 'joint': joint / n, 'split': split / n,
            'argmax': argm / n, 'top5': top5 / n,
            'tied_identical': tied_identical, 'tied_numerical': tied_numerical,
            'n_draws': n}


def dirichlet(k, seed, n):
    return np.random.default_rng(seed).dirichlet(np.ones(k), n)


def pareto_mask(A):
    """Rows of A (columns oriented so higher is better) no other row dominates:
    at least as good on every column and better on one."""
    A = np.asarray(A, float)
    keep = np.ones(len(A), bool)
    for i in range(len(A)):
        if (np.all(A >= A[i], axis=1) & np.any(A > A[i], axis=1)).any():
            keep[i] = False
    return keep


def dominance(A):
    """D[i, j] is True when row j dominates row i."""
    A = np.asarray(A, float)
    return (A[None, :, :] >= A[:, None, :]).all(2) & (A[None, :, :] > A[:, None, :]).any(2)
