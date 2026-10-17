# Reruns Alignment's California contract H3815 under the measure sets that are being litigated.
# Needs recompute_stars.py to tie out first (it does: 503 of 508 MA-PD overall ratings match CMS).
import os, csv, re
from recompute_stars import *

C = 'H3815'
contested = {}
for r in read('contested_measures.csv')[1:]:
    contested.setdefault(r[2], []).append(r[0])
RULE = tuple(contested['rulemaking'])            # the 10 Alignment is suing over (Clover group 2)
DATA_SRC = tuple(contested['data_source'])       # Clover group 1, mapped to 2027 measure IDs
NOT_HHC = ('C07', 'C27', 'C28', 'C29', 'C30', 'C31', 'C32', 'D01', 'D02', 'D03', 'D04', 'D07', 'D08', 'D09', 'D10', 'D11', 'D12', 'D13')
# NOT_HHC approximates CMS's June 2026 approach: keep only HEDIS, HOS and CAHPS measures

scen = [
    ('As published by CMS', ()),
    ('Without the 10 measures in the lawsuit', RULE),
    ('Without all 19 Clover measures (2027 IDs)', RULE + DATA_SRC),
    ('HEDIS/HOS/CAHPS only (CMS June 2026 approach, approx.)', NOT_HHC),
]
mapd = sorted(MAPD)
rows = []
print(f"{C} measure stars, contested measures: " + ', '.join(f"{m}={stars[C].get(m,'n/a')} (w{W[m]:g})" for m in RULE))
for name, drop in scen:
    a = final_rating(C, 'overall', drop)                                  # CMS published reward thresholds
    b = final_rating(C, 'overall', drop, th_mode='data', contracts=mapd)  # thresholds re-derived on the same measure set
    base_gap = 0.0
    wi = a[2][True]; wo = a[2][False]
    rows.append([name, len(measure_set('overall', True, drop)), round(wi[1], 4), round(wi[0], 4), a[1], round(b[0], 4), b[1], round(3.75 - a[0], 4)])
    print(f"{name}: weighted mean {wi[1]:.4f}, reward {wi[4]}, CAI {wi[5]:+.4f}, raw {a[0]:.4f} -> {a[1]} stars "
          f"(thresholds re-derived: raw {b[0]:.4f} -> {b[1]}); distance to the 3.75 line {3.75 - a[0]:+.4f}")

# Same question with the improvement measures left out (CMS would recompute C29/D04 on the new measure set, which I can't)
for name, drop in scen[1:3]:
    mu, v, n = mean_var(stars[C], measure_set('overall', False, drop))
    th = thresholds_published('overall', False)
    raw = mu + rfactor(mu, v, th) + CAI[('overall', fac[C]['overall'])]
    print(f"{name}, improvement measures excluded: raw {raw:.4f} -> {round_half(raw)}")

# How many other MA-PD contracts cross 4.0 if the 10 come out industry-wide
up = [c for c in mapd if final_rating(c, 'overall')[1] < 4 <= final_rating(c, 'overall', RULE)[1]]
down = [c for c in mapd if final_rating(c, 'overall')[1] >= 4 > final_rating(c, 'overall', RULE)[1]]
print(f"industry: {len(up)} MA-PD contracts move up to 4+ without the 10; {len(down)} fall below 4")

os.makedirs(os.path.join(HERE, '..', 'results'), exist_ok=True)
with open(os.path.join(HERE, '..', 'results', 'h3815_scenarios.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['scenario', 'measures_used', 'weighted_mean', 'raw_overall_published_thresholds', 'stars', 'raw_overall_rederived_thresholds', 'stars_rederived', 'gap_to_3_75'])
    w.writerows(rows)
