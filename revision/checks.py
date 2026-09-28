"""A handful of checks on the scoring rules in revision/methods.py.

    python revision/checks.py

Each check is a behaviour the revision's results depend on. They run on small
constructed inputs, not on the data, so a failure points at the rule rather
than at a site.
"""
import os
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from methods import (pct_exact, exact_scores, top_set, runner_up_gap,  # noqa: E402
                     weight_space, dirichlet, pareto_mask, dominance, vector_groups)

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))


ref = [1, 2, 2, 2, 5, 7, 7, 9]

# 1. Equal raw values get equal scores, under both rules and both directions.
for rule in ('strict', 'midrank'):
    for lower in (False, True):
        s = pct_exact([2, 2, 7, 7], ref, lower, rule)
        check(f'equal values, equal scores ({rule}, lower={lower})',
              s[0] == s[1] and s[2] == s[3])

# 2. Direction. Scoring v as higher-is-better and -v as lower-is-better is the
#    same ordering; a rule that treats directions alike scores them the same.
neg = [-x for x in ref]
hm, lm = pct_exact(ref, ref, False, 'midrank'), pct_exact(neg, neg, True, 'midrank')
check('midrank: v higher-is-better scores the same as -v lower-is-better', hm == lm)
hs, ls = pct_exact(ref, ref, False, 'strict'), pct_exact(neg, neg, True, 'strict')
check('strict: the same ordering scores differently by direction (documented)',
      hs != ls,
      f'the best of 8 values scores {float(max(hs)):.1f} as higher-is-better, '
      f'{float(max(ls)):.1f} as lower-is-better')
check('both rules: the better raw value never scores lower',
      all(pct_exact([a], ref, False, r)[0] <= pct_exact([b], ref, False, r)[0]
          for r in ('strict', 'midrank') for a, b in [(1, 2), (2, 5), (5, 9)]))

# 3. No new ties between distinct values that are both in the reference.
for rule in ('strict', 'midrank'):
    vals = sorted(set(ref))
    s = pct_exact(vals, ref, False, rule)
    check(f'distinct reference values stay distinct ({rule})', len(set(s)) == len(s))

# 4. Every joint first place is listed, and exact ties are told from display ties.
cols = {'a': [Fraction(10), Fraction(20), Fraction(15)], 'b': [Fraction(20), Fraction(10), Fraction(15)]}
sc = exact_scores(cols, {'a': '0.5', 'b': '0.5'})
check('three-way exact tie: all three listed first', top_set(sc) == [0, 1, 2])
cols = {'a': [Fraction(1001, 10), Fraction(100)], 'b': [Fraction(0), Fraction(0)]}
sc = exact_scores(cols, {'a': '1', 'b': '0'})
check('scores that round alike are not a tie', top_set(sc) == [0] and runner_up_gap(sc) == Fraction(1, 10),
      '100.1 vs 100.0 both print as 100 at no decimals')
# Percentiles on a 246-site grid: these two sums are equal exactly, but not in floats.
cols = {'a': [Fraction(100 * 225, 492), Fraction(100 * 261, 492)],
        'b': [Fraction(100 * 340, 492), Fraction(100 * 268, 492)]}
sc = exact_scores(cols, {'a': '0.4', 'b': '0.2'})
flo = [0.4 * (100 * 225 / 492) + 0.2 * (100 * 340 / 492),
       0.4 * (100 * 261 / 492) + 0.2 * (100 * 268 / 492)]
check('exact arithmetic finds a tie that floats miss', top_set(sc) == [0, 1] and flo[0] != flo[1],
      f'float scores {flo[0]!r} and {flo[1]!r}')

# 5. Weight space: split shares sum to one, ties are shared and classified,
#    and the answer does not depend on row order.
rng = np.random.default_rng(0)
P = rng.uniform(0, 100, (12, 3))
P[5] = P[2]                                   # two sites with identical vectors
P[2, :] = P[5, :] = P.max(0) + 1              # ... and they dominate the rest
draws = dirichlet(3, 1, 20_000)
r = weight_space(P, draws)
check('split shares sum to one', abs(r['split'].sum() - 1) < 1e-12)
check('identical-vector pair shares every win equally',
      abs(r['split'][2] - 0.5) < 1e-12 and abs(r['split'][5] - 0.5) < 1e-12 and r['unique'][2] == 0)
check('those ties are classified as identical-vector ties',
      r['tied_identical'] == len(draws) and r['tied_numerical'] == 0)
check('argmax would have given every tied draw to the first row',
      r['argmax'][2] == 1 and r['argmax'][5] == 0)
perm = rng.permutation(len(P))
rp = weight_space(P[perm], draws)
check('shares do not depend on row order',
      np.allclose(rp['split'], r['split'][perm]) and np.allclose(rp['unique'], r['unique'][perm]))
Q = rng.uniform(0, 100, (30, 4))
rq = weight_space(Q, dirichlet(4, 2, 20_000))
check('with no identical rows, draws are won outright',
      rq['tied_identical'] == 0 and abs(rq['unique'].sum() - 1) < 1e-3)

# 6. Frontier: dominated rows go, identical rows both stay.
A = np.array([[3, 3], [2, 2], [3, 3], [1, 4], [0, 4]], float)
keep = pareto_mask(A)
check('frontier keeps both identical undominated rows and drops the dominated',
      keep.tolist() == [True, False, True, True, False])
check('frontier loop agrees with the dominance matrix', (~dominance(A).any(1) == keep).all())
check('identical rows share a vector group', vector_groups(A)[0] == vector_groups(A)[2])

width = max(len(n) for n, _, _ in results)
for name, ok, detail in results:
    print(f"{'ok  ' if ok else 'FAIL'}  {name:<{width}}  {detail}")
failed = [n for n, ok, _ in results if not ok]
print(f'\n{len(results) - len(failed)} of {len(results)} checks passed')
sys.exit(1 if failed else 0)
