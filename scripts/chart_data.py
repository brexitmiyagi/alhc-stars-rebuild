# Writes the CSVs behind the four Datawrapper charts.
import os, csv
from recompute_stars import *
import hos_noise as H
import h3815_scenarios as S

R = os.path.join(HERE, '..', 'results')
# Chart B: physical health score, 2026 vs 2027, every contract with both
with open(os.path.join(R, 'chart_ph_scatter.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['contract', 'PH score 2026 Star Ratings', 'PH score 2027 Star Ratings', 'group'])
    for c, r in sorted(H.h26.items()):
        a = r['ph_score_2026']; b = H.score27(c, 'C04')
        if a and b is not None:
            w.writerow([c, int(a), b, 'Alignment H3815' if c == 'H3815' else 'Other contracts'])
# Chart A: the recompute table
rows = []
for name, drop in S.scen:
    a = final_rating('H3815', 'overall', drop)
    used = a[2][False] if a[0] == a[2][False][0] else a[2][True]
    rows.append([name, used[3], round(float(a[0]), 2), float(a[1])])
W_saved = dict(W); W['C04'] = W['C05'] = 1.0
a = final_rating('H3815', 'overall'); rows.append(['As published, but physical and mental health at their 2026 weight of 1', a[2][True][3], round(float(a[0]), 2), float(a[1])])
W.clear(); W.update(W_saved)
with open(os.path.join(R, 'chart_recompute_table.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Measure set', 'Measures', 'Raw score', 'Stars']); w.writerows(rows)
for r in rows: print(r)
