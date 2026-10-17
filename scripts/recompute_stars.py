# Rebuilds CMS 2027 summary and overall star ratings from the published measure stars,
# checks the rebuild against what CMS published, then reruns contract H3815 (Alignment, California)
# without the measures it is suing over.
import os, csv, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')

def read(name):
    with open(os.path.join(DATA, name), encoding='latin1') as f:
        return list(csv.reader(f))

# measure stars: header row 2 holds "C01: Breast Cancer Screening" style labels
ms = read('measure_stars_2027.csv')
labels = ms[2]
cols = {}
for i, lab in enumerate(labels):
    m = re.match(r'\s*([CD]\d\d):', lab)
    if m:
        cols[m.group(1)] = i
stars = {}
for r in ms[3:]:
    if not r or not re.match(r'^[EHRS]\d', r[0].strip()):
        continue
    d = {}
    for code, i in cols.items():
        v = r[i].strip() if i < len(r) else ''
        if re.fullmatch(r'[1-5]', v):
            d[code] = int(v)
    stars[r[0].strip()] = d

W = {r[0]: float(r[1]) for r in read('measure_weights_2027.csv')[1:]}

pub = {}
for r in read('summary_ratings_2027.csv')[2:]:
    if r and re.match(r'^[EHRS]\d', r[0].strip()):
        pub[r[0].strip()] = (r[8].strip(), r[9].strip(), r[10].strip())

fac = {}
for r in read('cai_2027.csv')[2:]:
    if r and re.match(r'^[EHRS]\d', r[0].strip()):
        fac[r[0].strip()] = {'part_c': r[5].strip(), 'part_d_mapd': r[6].strip(), 'overall': r[8].strip()}
CAI = {}
for r in read('cai_values_2027.csv')[1:]:
    CAI[(r[0], r[1])] = float(r[2])

TH = {}
for r in read('reward_thresholds_2027.csv')[1:]:
    imp, new, pct = r[0], r[1], int(r[2])
    for j, key in zip(range(3, 7), ['part_c', 'part_d_mapd', 'part_d_pdp', 'overall']):
        TH[(imp, key, pct)] = float(r[j])

MAPD = {c for c, p in pub.items() if re.fullmatch(r'[\d.]+', p[2] or '')}
C_MEAS = [f'C{i:02d}' for i in range(1, 33)]
D_MEAS = [f'D{i:02d}' for i in range(1, 14)]
DUPES_IN_OVERALL = {'D02', 'D03'}   # complaints and members leaving count once, on the Part C side

def measure_set(rating, improvement, drop):
    if rating == 'part_c':
        s = C_MEAS
    elif rating == 'part_d_mapd':
        s = D_MEAS
    else:
        s = C_MEAS + [m for m in D_MEAS if m not in DUPES_IN_OVERALL]
    s = [m for m in s if m not in drop]
    if not improvement:
        s = [m for m in s if m not in ('C29', 'D04')]
    return s

def mean_var(d, mset):
    xs = [(d[m], W[m]) for m in mset if m in d]
    if len(xs) < 2:
        return None, None, 0
    x = np.array([a for a, _ in xs], float); w = np.array([b for _, b in xs], float)
    mu = (x * w).sum() / w.sum()
    n = len(x)
    var = n * (w * (x - mu) ** 2).sum() / (w.sum() * (n - 1))
    return mu, var, n

def rfactor(mu, var, th):
    hi = mu >= th['m85']; rel = th['m65'] <= mu < th['m85']
    low = var < th['v30']; med = th['v30'] <= var < th['v70']
    if hi and low: return 0.4
    if hi and med: return 0.3
    if rel and low: return 0.2
    if rel and med: return 0.1
    return 0.0

def round_half(x):
    # Table 22: 3.25 to <3.75 -> 3.5, 3.75 to <4.25 -> 4.0, etc.
    return np.floor((x + 0.25) * 2) / 2

def thresholds_published(rating, imp):
    k = 'with' if imp else 'without'
    return {'m65': TH[(k, rating, 65)], 'm85': TH[(k, rating, 85)], 'v30': TH[(k, rating, 30)], 'v70': TH[(k, rating, 70)]}

def thresholds_from_data(rating, imp, drop, contracts):
    mus, vs = [], []
    for c in contracts:
        mu, v, n = mean_var(stars[c], measure_set(rating, imp, drop))
        if mu is not None:
            mus.append(mu); vs.append(v)
    p = lambda a, q: float(np.percentile(a, q))
    return {'m65': p(mus, 65), 'm85': p(mus, 85), 'v30': p(vs, 30), 'v70': p(vs, 70)}

def raw_score(c, rating, imp, drop, th):
    mu, v, n = mean_var(stars[c], measure_set(rating, imp, drop))
    if mu is None:
        return None
    f = fac.get(c, {}).get(rating, 'N/A')
    cai = CAI.get((rating, f), 0.0)
    return mu + rfactor(mu, v, th) + cai, mu, v, n, rfactor(mu, v, th), cai

def final_rating(c, rating, drop=(), th_mode='published', contracts=None):
    out = {}
    for imp in (False, True):
        th = thresholds_published(rating, imp) if th_mode == 'published' else thresholds_from_data(rating, imp, drop, contracts)
        out[imp] = raw_score(c, rating, imp, drop, th)
    if out[True] is None:
        return None
    wo, wi = out[False][0], out[True][0]
    # improvement-measure rule: if the rating without improvement is 4+ and adding improvement lowers it, keep the 'without'
    # Tech Notes p.15-16: the hold-harmless applies to the MA-PD overall rating and to MA-only Part C summaries.
    # MA-PD Part C and Part D summaries always include their improvement measure.
    hold = (rating == 'overall') or (rating == 'part_c' and c not in MAPD)
    use = wo if (hold and round_half(wo) >= 4 and wi < wo) else wi
    return use, round_half(use), out

if __name__ == '__main__':
    mapd = [c for c in stars if pub.get(c, ('', '', ''))[2] not in ('', 'Not Applicable') and re.fullmatch(r'[\d.]+', pub[c][2] or '')]
    ma = [c for c in stars if re.fullmatch(r'[\d.]+', pub.get(c, ('', '', ''))[0] or '')]
    # 1) tie-out: how often does the rebuild match CMS's published ratings?
    for rating, idx, pool in (('part_c', 0, ma), ('part_d_mapd', 1, mapd), ('overall', 2, mapd)):
        ok = tot = 0
        for c in pool:
            r = final_rating(c, rating)
            if r is None or not re.fullmatch(r'[\d.]+', pub[c][idx]): continue
            tot += 1; ok += (abs(r[1] - float(pub[c][idx])) < 1e-9)
        print(f'tie-out {rating}: rebuild matches CMS on {ok} of {tot} contracts ({ok/tot:.1%})')
    # threshold check: percentiles from the data vs Table 8/9
    for rating, pool in (('overall', mapd), ('part_c', ma)):
        for imp in (True, False):
            t = thresholds_from_data(rating, imp, (), pool); tp = thresholds_published(rating, imp)
            print(f'thresholds {rating} improvement={imp}: data ' + ', '.join(f'{k} {t[k]:.4f}' for k in t) + ' | CMS ' + ', '.join(f'{k} {tp[k]:.4f}' for k in tp))
