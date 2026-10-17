"""Out-of-sample test of the transition matrix that value_v7.py uses after 2030.

What the valuation needs from the matrix is the gap between two cohorts: good-record contracts that have
just dropped to 3.5 stars, and good-record contracts that are still at 4+. Here the matrix is trained on
earlier transitions only and asked to predict how that gap closes for later cohorts.

Test A (same filter as value_v7): good record = 4+ in at least 3 of the previous 4 ratings. Train on the
2023->2024 and 2024->2025 transitions; test cohorts defined in the 2025 ratings, observed in 2026 and 2027.
Test B (longer horizon, NOT out of sample): the matrix value_v7 actually uses (3 of 4 filter, trained on
2023->2027) applied to cohorts defined in the 2023 and 2024 ratings with a looser filter (4+ in both previous
ratings), observed up to 2027. It overlaps the training years, so it only checks the shape over 3-4 years.
A truly out-of-sample long-horizon test is not possible: a matrix trained on 2021-2023 has no contracts with
a good record falling to 3 stars (pandemic relief), so it cannot be estimated.
"""
import os, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'data')
rows = list(csv.DictReader(open(os.path.join(D, 'stars_and_enrollment_2019_2027.csv'))))
f = lambda v: float(v) if v else None
st = lambda s: 0 if s >= 4 else (1 if s == 3.5 else 2)
S = lambda r, y: f(r.get(f'stars_{y}', ''))
out = []
P = lambda s: (print(s), out.append(s))

def good(r, Y, lookback, need):
    h = [S(r, y) for y in range(Y - lookback, Y)]
    return all(x is not None for x in h) and sum(x >= 4 for x in h) >= need

def train(years, lookback, need):
    M = np.zeros((3, 3))
    for Y in years:
        for r in rows:
            a, b = S(r, Y), S(r, Y + 1)
            if a is None or b is None or not good(r, Y, lookback, need): continue
            M[st(a), st(b)] += 1
    n = int(M.sum()); return M / M.sum(1, keepdims=True), n

def test(M, starts, lookback, need, last=2027):
    res = {}
    for Y0 in starts:
        for r in rows:
            s0 = S(r, Y0)
            if s0 is None or not good(r, Y0, lookback, need): continue
            prev = S(r, Y0 - 1)
            if s0 == 3.5 and prev is not None and prev >= 4: g = 'drop'
            elif s0 >= 4 and prev is not None and prev >= 4: g = 'stay'
            else: continue
            v = np.eye(3)[st(s0)]
            for h in range(1, last - Y0 + 1):
                v = v @ M; s = S(r, Y0 + h)
                if s is None: continue
                k = res.setdefault((g, h), [0, 0.0, 0]); k[0] += 1; k[1] += v[1] + v[2]; k[2] += (s < 4)
    return res

def report(name, res):
    P(name)
    for h in sorted({h for (_, h) in res}):
        d, s = res.get(('drop', h)), res.get(('stay', h))
        if not d or not s: continue
        pd, ad, ps, as_ = d[1] / d[0], d[2] / d[0], s[1] / s[0], s[2] / s[0]
        P(f"  {h} yr later: dropped (n {d[0]}) predicted {pd:.0%} below 4, actual {ad:.0%}; held (n {s[0]}) predicted {ps:.0%}, actual {as_:.0%}; gap predicted {pd-ps:+.0%}, actual {ad-as_:+.0%}")

MA, nA = train([2023, 2024], 4, 3)
P(f"Test A matrix ({nA} contract-years):\n{MA.round(3)}")
report("Test A: cohorts in the 2025 ratings", test(MA, [2025], 4, 3))
MB, nB = train([2023, 2024, 2025, 2026], 4, 3)
P(f"Matrix used in value_v7 ({nB} contract-years):\n{MB.round(3)}")
report("Test B (in-sample, shape check): cohorts in the 2023 and 2024 ratings", test(MB, [2023, 2024], 2, 2))
open(os.path.join(HERE, '..', 'results', 'matrix_backtest.txt'), 'w').write('\n'.join(out) + '\n')
