# How noisy are the two HOS outcome measures CMS tripled in weight for 2027?
# Compares each contract's 2026 and 2027 scores and stars for physical health (C04), mental health (C05),
# and two controls: breast cancer screening (C01) and reducing the risk of falling (C15).
# 2026 values come from CMS's 2026 Star Ratings data tables (transcribed to data/hos_and_controls_2026.csv),
# 2027 values from the 2027 tables in data/.
import os, csv, re
import numpy as np
from recompute_stars import *

h26 = {}
with open(os.path.join(DATA, 'hos_and_controls_2026.csv')) as f:
    for r in csv.DictReader(f):
        h26[r['contract']] = r

md = read('measure_data_2027.csv')
lab = md[3] if not any(re.match(r'\s*C01:', x) for x in md[2]) else md[2]
for i_row in range(1, 5):
    if any(re.match(r'\s*C01:', x) for x in md[i_row]):
        lab = md[i_row]; break
col = {m.group(1): i for i, x in enumerate(lab) for m in [re.match(r'\s*([CD]\d\d):', x)] if m}
s27 = {}
for r in md:
    if r and re.match(r'^[HR]\d', r[0].strip()):
        s27[r[0].strip()] = r

def score27(c, m):
    v = s27.get(c, [''] * 200)[col[m]].strip() if c in s27 else ''
    mm = re.fullmatch(r'(\d+)%', v)
    return int(mm.group(1)) if mm else None

out = []
for name, key, m in (('Physical health (C04)', 'ph', 'C04'), ('Mental health (C05)', 'mh', 'C05'),
                     ('Breast cancer screening (C01)', 'bcs', 'C01'), ('Reducing risk of falling (C15)', 'fall', 'C15')):
    pairs, spairs = [], []
    for c, r in h26.items():
        a = r[f'{key}_score_2026']; b = score27(c, m)
        if a and b is not None:
            pairs.append((int(a), b, c))
        sa = r[f'{key}_star_2026']; sb = stars.get(c, {}).get(m)
        if sa and sb:
            spairs.append((int(sa), sb))
    x = np.array([p[0] for p in pairs]); y = np.array([p[1] for p in pairs])
    rr = np.corrcoef(x, y)[0, 1]
    same = np.mean([a == b for a, b in spairs]); two = np.mean([abs(a - b) >= 2 for a, b in spairs])
    d = y - x
    line = (f"{name}: n={len(pairs)} contracts, year-on-year correlation {rr:.2f}, 2027 cross-contract SD {np.std(y):.1f} pts, "
            f"same star both years {100*same:.0f}%, moved 2+ stars {100*two:.0f}%")
    if key in ('ph', 'mh'):
        hc = [p for p in pairs if p[2] == 'H3815'][0]
        rank = int(np.sum(d <= hc[1] - hc[0]))
        line += f"; H3815 {hc[0]} -> {hc[1]} ({hc[1]-hc[0]:+d}), rank {rank} of {len(d)} from the bottom"
    print(line)
    out.append([name, len(pairs), round(rr, 2), round(float(np.std(y)), 1), round(100 * same), round(100 * two)])

# Empirical odds next year, for a contract sitting at 1 star on both PH and MH (where H3815 is now)
def trans(key, m, from_star):
    nxt = [stars[c][m] for c, r in h26.items() if r[f'{key}_star_2026'] == str(from_star) and m in stars.get(c, {})]
    return {k: nxt.count(k) / len(nxt) for k in range(1, 6)}, len(nxt)
tp, nph = trans('ph', 'C04', 1); tm, nmh = trans('mh', 'C05', 1)
print(f"PH 1-star contracts in 2026 (n={nph}) one year later: " + ', '.join(f'{k}*: {100*v:.0f}%' for k, v in tp.items()))
print(f"MH 1-star contracts in 2026 (n={nmh}) one year later: " + ', '.join(f'{k}*: {100*v:.0f}%' for k, v in tm.items()))
C = 'H3815'; base = dict(stars[C]); p4 = 0.0
for a in range(1, 6):
    for b in range(1, 6):
        stars[C] = dict(base); stars[C]['C04'] = a; stars[C]['C05'] = b
        if final_rating(C, 'overall')[1] >= 4:
            p4 += tp[a] * tm[b]
stars[C] = dict(base)
print(f"H3815 back to 4.0+ if only PH and MH move, at those historical odds and everything else held: {100*p4:.0f}%")
with open(os.path.join(HERE, '..', 'results', 'hos_noise.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['measure', 'n', 'yoy_corr', 'sd_2027', 'pct_same_star', 'pct_moved_2plus']); w.writerows(out)
