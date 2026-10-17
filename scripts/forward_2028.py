"""Where does H3815 land in the 2028 and 2029 Star Ratings?

Three pieces:
1. The measure sets CMS already finalized (CY2027 final rule, 91 FR 17384, April 6 2026):
   - 2028 Star Ratings (set 2029 bonus): Call Center interpreter/TTY (C32, D01) and
     Statin Therapy for Patients with Cardiovascular Disease (C18) come out.
   - 2029 Star Ratings (set 2030 bonus): appeals (C30, C31), SNP Care Management (C07),
     complaints (C27, D02), members choosing to leave (C28, D03), MPF price accuracy (D07),
     Customer Service (C23) and Rating of Health Care Quality (C24) come out too.
   - Part D adherence (D08-D10) is case-mix adjusted from the 2028 ratings. Consultants say it
     drops to weight 1 for one year; CMS's documents I found don't say. I run both.
2. A deterministic rerun: H3815's 2027 measure stars on those sets.
3. A simulation: each measure's 2028 star drawn from how contracts with the same 2026 star on that
   measure scored in 2027 (empirical transition, all contracts). Measures drawn independently.
And a plain base rate from the overall ratings 2019-2027.
"""
import os, csv, re, random
import numpy as np
from recompute_stars import stars, W, final_rating, round_half, MAPD, measure_set, mean_var, fac, CAI, rfactor, thresholds_from_data

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
C = 'H3815'
mapd = sorted(MAPD)
D28 = ('C32', 'D01', 'C18')
D29 = D28 + ('C30', 'C31', 'C07', 'C27', 'C28', 'D02', 'D03', 'D07', 'C23', 'C24')
ADH = ('D08', 'D09', 'D10')
BASE_W = dict(W)

def with_weights(adh_w):
    W.update(BASE_W)
    for m in ADH: W[m] = adh_w

def rate(c, drop, adh_w=3, override=None):
    with_weights(adh_w)
    save = dict(stars[c])
    if override: stars[c].update(override)
    r = final_rating(c, 'overall', drop, th_mode='data', contracts=mapd)
    stars[c].clear(); stars[c].update(save)
    W.update(BASE_W)
    return r

print('1) H3815 holding every 2027 measure star still')
for name, drop, aw in (('2027 rules (as published)', (), 3), ('2028 rules, adherence weight 3', D28, 3),
                       ('2028 rules, adherence weight 1', D28, 1), ('2029 rules', D29, 3)):
    r = rate(C, drop, aw)
    print(f'   {name}: raw {r[0]:.3f} -> {r[1]} stars | line for 4 stars is 3.75, line for 3 stars is 3.25')
print('   Measures leaving in 2028 and H3815\'s 2027 stars: ' + ', '.join(f'{m}={stars[C].get(m)}' for m in D28))
print('   Measures leaving in 2029: ' + ', '.join(f'{m}={stars[C].get(m)}' for m in D29[3:]))

RULE = ('C03', 'C04', 'C05', 'C15', 'C16', 'C21', 'C22', 'C23', 'C24', 'C26')   # the 10 in Alignment's suit
r = rate(C, D28 + RULE, 3)
print(f'   2028 rules without the 10 measures in the suit: raw {r[0]:.3f} -> {r[1]} stars')
print('   Contested measures leaving: 2028 none; 2029 ' + ', '.join(m for m in RULE if m in D29))
print('2) What physical and mental health need to be (everything else as 2027)')
for ph, mh in ((1, 1), (2, 2), (2, 3), (3, 2), (3, 3), (4, 4), (5, 5)):
    out = []
    for drop, aw in (((), 3), (D28, 3), (D28, 1), (D29, 3)):
        r = rate(C, drop, aw, {'C04': ph, 'C05': mh}); out.append(f'{r[0]:.3f}->{r[1]}')
    print(f'   PH {ph}* MH {mh}*: 2027 rules {out[0]} | 2028 w3 {out[1]} | 2028 w1 {out[2]} | 2029 {out[3]}')

# ---- 3) simulation from empirical 2026 -> 2027 measure transitions
L = open(os.path.join(DATA, 'measure_stars_2026_compact.txt')).read().strip().split('\n')
names26 = [n.split(': ', 1)[1] for n in L[0].split(';')[1:]]
s26 = {}
for line in L[1:]:
    cid, s = line.split(',')
    s26[cid] = {i: int(ch) for i, ch in enumerate(s) if ch.isdigit()}
# 2027 measure names from the 2027 table header
import recompute_stars as rs
lab27 = {}
for lab in rs.labels:
    m = re.match(r'\s*([CD]\d\d):\s*(.*)', lab)
    if m: lab27[m.group(1)] = m.group(2)
norm = lambda t: re.sub(r'[^a-z]', '', t.lower().replace('â€“', ''))[:22]
idx26 = {}
for code, nm in lab27.items():
    hits = [i for i, n in enumerate(names26) if norm(n) == norm(nm) and n[:1] == ('' if False else n[:1])]
    # keep Part C/Part D apart: 2026 list is C01..C33 then D01..D12
    part = code[0]
    hits = [i for i in hits if (i < 33) == (part == 'C')]
    if hits: idx26[code] = hits[0]
unmatched = sorted(set(lab27) - set(idx26))
print(f'3) 2027 measures matched to a 2026 measure by name: {len(idx26)}; unmatched (held at 2027 star): {unmatched}')

trans = {}
for code, i in idx26.items():
    T = np.zeros((6, 6))
    for cid, d in stars.items():
        if code in d and cid in s26 and i in s26[cid]:
            T[s26[cid][i], d[code]] += 1
    trans[code] = T

def draw(code, cur, rng):
    T = trans.get(code)
    if T is None or T[cur].sum() < 5: return cur
    p = T[cur] / T[cur].sum()
    return int(rng.choice(6, p=p))

def simulate(drop, aw, n=20000, seed=7):
    rng = np.random.default_rng(seed)
    base = dict(stars[C]); res = []
    with_weights(aw)
    ms = measure_set('overall', True, drop) + measure_set('overall', False, drop)
    th = {imp: thresholds_from_data('overall', imp, drop, mapd) for imp in (False, True)}
    cai = CAI[('overall', fac[C]['overall'])]
    for _ in range(n):
        d = {m: draw(m, base[m], rng) for m in base}
        out = {}
        for imp in (False, True):
            xs = [(d[m], W[m]) for m in measure_set('overall', imp, drop) if m in d]
            x = np.array([a for a, _ in xs], float); w = np.array([b for _, b in xs], float)
            mu = (x * w).sum() / w.sum(); k = len(x)
            var = k * (w * (x - mu) ** 2).sum() / (w.sum() * (k - 1))
            out[imp] = mu + rfactor(mu, var, th[imp]) + cai
        use = out[False] if (round_half(out[False]) >= 4 and out[True] < out[False]) else out[True]
        res.append(round_half(use))
    W.update(BASE_W)
    res = np.array(res)
    return {s: float((res == s).mean()) for s in sorted(set(res))}

def simulate2(n=20000, seed=11):
    """Two steps: 2027 stars -> 2028 stars -> 2029 stars, rated under the 2029 measure set."""
    rng = np.random.default_rng(seed)
    base = dict(stars[C]); res = []
    with_weights(3)
    th = {imp: thresholds_from_data('overall', imp, D29, mapd) for imp in (False, True)}
    cai = CAI[('overall', fac[C]['overall'])]
    for _ in range(n):
        d1 = {m: draw(m, base[m], rng) for m in base}
        d = {m: draw(m, d1[m], rng) for m in d1}
        out = {}
        for imp in (False, True):
            xs = [(d[m], W[m]) for m in measure_set('overall', imp, D29) if m in d]
            x = np.array([a for a, _ in xs], float); w = np.array([b for _, b in xs], float)
            mu = (x * w).sum() / w.sum(); k = len(x)
            var = k * (w * (x - mu) ** 2).sum() / (w.sum() * (k - 1))
            out[imp] = mu + rfactor(mu, var, th[imp]) + cai
        use = out[False] if (round_half(out[False]) >= 4 and out[True] < out[False]) else out[True]
        res.append(round_half(use))
    W.update(BASE_W)
    res = np.array(res)
    return {s: float((res == s).mean()) for s in sorted(set(res))}

summary = []
for name, drop, aw in (('2028 rules, adherence weight 3', D28, 3), ('2028 rules, adherence weight 1', D28, 1),
                       ('2027 rules (for comparison)', (), 3)):
    dist = simulate(drop, aw)
    p4 = sum(v for k, v in dist.items() if k >= 4); p3 = sum(v for k, v in dist.items() if k <= 3)
    summary.append((name, p4, dist.get(3.5, 0), p3))
    print(f'   {name}: P(4+) {p4:.0%}, P(3.5) {dist.get(3.5, 0):.0%}, P(3 or less) {p3:.0%}  ' + str({float(k): round(v, 3) for k, v in dist.items()}))
dist = simulate2()
p4 = sum(v for k, v in dist.items() if k >= 4); p3 = sum(v for k, v in dist.items() if k <= 3)
summary.append(('2029 rules, two years out', p4, dist.get(3.5, 0), p3))
print(f'   2029 rules, two years of draws: P(4+) {p4:.0%}, P(3.5) {dist.get(3.5, 0):.0%}, P(3 or less) {p3:.0%}')
with open(os.path.join(HERE, '..', 'results', 'forward_dist.csv'), 'w', newline='') as fh:
    wr = csv.writer(fh); wr.writerow(['scenario', 'p_4plus', 'p_3_5', 'p_3_or_less'])
    for row in summary: wr.writerow([row[0]] + [round(v, 4) for v in row[1:]])

# validation: same machinery on every contract that was rated in 2026, predicting 2027 (in-sample transitions)
# compare average predicted P(4+) with actual share at 4+ among contracts that were 3.5 in 2027 with H3815-like scores

# ---- 4) base rate from overall ratings
rows = list(csv.DictReader(open(os.path.join(DATA, 'stars_and_enrollment_2019_2027.csv'))))
f = lambda x: float(x) if x else None
tot = up = dn = 0
print('4) Contracts that fell from 4+ to 3.5, and their rating the next year')
for Y in range(2023, 2027):   # skips the 2021-2022 COVID-era rules
    n = u = d = 0
    for r in rows:
        a, b, c = f(r[f'stars_{Y-1}']), f(r[f'stars_{Y}']), f(r[f'stars_{Y+1}'])
        if None in (a, b, c) or not (a >= 4 and b == 3.5): continue
        n += 1; u += c >= 4; d += c <= 3
    print(f'   fell in the {Y} ratings: {n} contracts, {u} back at 4+ in {Y+1}, {d} down to 3 or less')
    tot += n; up += u; dn += d
print(f'   pooled 2023-2026: {up}/{tot} = {up/tot:.0%} back to 4+, {dn}/{tot} = {dn/tot:.0%} fell to 3 or less')
