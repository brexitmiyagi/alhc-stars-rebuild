"""Stress tests for the margin-share result in margin_share.py.

1. Enrollment-weighted (February enrollment of the payment year, CMS monthly enrollment by contract).
2. Matched controls: each contract that lost 4 stars is compared with same-year contracts that held 4 stars
   and sit in the same quintile of A/B payment (a proxy for benchmark level and market).
3. Pre-trend placebo: the same comparison one year earlier, before the star changed. Should be near zero.
4. Size: contracts with 5+ plans only.
5. Alignment's own history: H3815's rebate path, including its one comparable episode (4.5 stars in the
   2020 ratings, back to 4.0 in 2021, which moved its rebate share 65% -> 70% -> 65%).
"""
import os, csv, statistics as st, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'data')
cases = {(r['y'], r['contract']): r for r in csv.DictReader(open(os.path.join(D, 'rebate_cases_2019_2023.csv')))}
prev = {(r['y'], r['contract']): r for r in csv.DictReader(open(os.path.join(D, 'rebate_prev_2019_2023.csv')))}
enr = {r['contract']: r for r in csv.DictReader(open(os.path.join(D, 'stars_and_enrollment_2019_2027.csv')))}
rows = []
for k, r in cases.items():
    p = prev[k]
    y = int(k[0])
    e = enr.get(k[1], {}).get(f'enroll_feb_{y}', '')
    rows.append(dict(y=y, c=k[1], g=r['g'], r0=float(r['r0']), r1=float(r['r1']), ab0=float(r['ab0']),
                     rp=float(p['r_prev']), np=int(p['np0'] or 0), w=float(e) if e else 0.0))
mech = lambda r: 0.65 * 0.05 / 1.05 * (r['ab0'] + r['r0'] / 0.65)

def base(y, pred=lambda r: True, field=('r0', 'r1')):
    s = [r[field[1]] - r[field[0]] for r in rows if r['y'] == y and r['g'] == 'S' and pred(r)]
    return st.median(s) if s else None

def wmedian(x, w):
    o = np.argsort(x); x = np.array(x)[o]; w = np.array(w)[o]; c = np.cumsum(w) / w.sum()
    return float(x[np.searchsorted(c, 0.5)])

drops = [r for r in rows if r['g'] == 'D']
pt = [-(r['r1'] - r['r0'] - base(r['y'])) / mech(r) for r in drops]
print(f"Baseline (margin_share.py): n {len(pt)}, median pass-through {st.median(pt):.2f}")

w = [r['w'] for r in drops]; ok = [i for i, x in enumerate(w) if x > 0]
print(f"1. Enrollment-weighted median: {wmedian([pt[i] for i in ok], [w[i] for i in ok]):.2f} (n {len(ok)} with enrollment)")

# 2. matched on A/B payment quintile within year
mt = []
for y in sorted(set(r['y'] for r in rows)):
    pool = [r for r in rows if r['y'] == y and r['g'] in ('S', 'D')]
    if not pool: continue
    qs = np.quantile([r['ab0'] for r in pool], [0.2, 0.4, 0.6, 0.8])
    q = lambda r: int(np.searchsorted(qs, r['ab0']))
    for r in pool:
        if r['g'] != 'D': continue
        ctl = [s['r1'] - s['r0'] for s in pool if s['g'] == 'S' and q(s) == q(r)]
        if len(ctl) >= 3: mt.append(-(r['r1'] - r['r0'] - st.median(ctl)) / mech(r))
print(f"2. Matched on year and A/B payment quintile: n {len(mt)}, median pass-through {st.median(mt):.2f}")

# 3. pre-trend placebo: change from the year before, same comparison
pre = []
for r in drops:
    b = base(r['y'], field=('rp', 'r0'))
    pre.append(-(r['r0'] - r['rp'] - b) / mech(r))
print(f"3. Placebo, year before the change: median {st.median(pre):.2f} (0 means no pre-trend)")
random.seed(5)
bt = sorted(st.median(random.choices(pre, k=len(pre))) for _ in range(4000))
print(f"   bootstrap 90% interval {bt[200]:.2f} to {bt[3800]:.2f}")

# 4. bigger contracts
big = [x for x, r in zip(pt, drops) if r['np'] >= 5]
print(f"4. Contracts with 5+ plans: n {len(big)}, median pass-through {st.median(big):.2f}")

# 5. H3815
print("5. H3815 (simple mean of plan rebates, CMS Plan Payment Data):")
h = {2018: 157.83, 2019: 204.24, 2020: 195.36, 2021: 214.27, 2022: 210.05, 2023: 209.61, 2024: 234.82}
print("   " + ', '.join(f"PY{y} ${v:.2f}" for y, v in h.items()))
stay = {y: base(y) for y in range(2019, 2024)}
# gain to 4.5 in the 2020 ratings -> PY2021 share 70%; back to 4.0 in the 2021 ratings -> PY2022 share 65%
g_mech = h[2020] * (0.70 / 0.65 - 1)
g_rel = (h[2021] - h[2020]) - stay[2020]
l_mech = h[2021] * (1 - 0.65 / 0.70)
l_rel = (h[2022] - h[2021]) - stay[2021]
print(f"   PY2021 (4.5 stars, share 65%->70%): rebate {h[2021]-h[2020]:+.2f} vs 4-star peers {stay[2020]:+.2f} -> relative {g_rel:+.2f}; formula {g_mech:+.2f}; pass-through {g_rel/g_mech:.2f}")
print(f"   PY2022 (back to 4.0, share 70%->65%): rebate {h[2022]-h[2021]:+.2f} vs 4-star peers {stay[2021]:+.2f} -> relative {l_rel:+.2f}; formula {-l_mech:+.2f}; pass-through {-l_rel/l_mech:.2f}")

# 6. Second year: contracts still below 4 stars a year later. Does the bid keep absorbing, or does the cut reach members?
y2 = {(r['y'], r['contract']): r['r2'] for r in csv.DictReader(open(os.path.join(D, 'rebate_year2_2019_2022.csv')))}
stars = {r['contract']: r for r in csv.DictReader(open(os.path.join(D, 'stars_and_enrollment_2019_2027.csv')))}
def sv(c, y):
    v = stars.get(c, {}).get(f'stars_{y}', ''); return float(v) if v else None
two = []
for y in (2019, 2020, 2021, 2022):
    ctl = [float(y2[(str(y), r['c'])]) - r['r0'] for r in rows if r['y'] == y and r['g'] == 'S'
           and y2.get((str(y), r['c'])) and (sv(r['c'], y + 1) or 0) >= 4]
    if len(ctl) < 5: continue
    m = st.median(ctl)
    for r in rows:
        if r['y'] != y or r['g'] != 'D' or not y2.get((str(y), r['c'])): continue
        s1 = sv(r['c'], y + 1)
        if s1 is None or s1 >= 4: continue
        two.append(-(float(y2[(str(y), r['c'])]) - r['r0'] - m) / mech(r))
print(f"6. Two payment years after the drop, still below 4 stars: n {len(two)}, median pass-through {st.median(two):.2f}" if two else "6. not enough cases")
