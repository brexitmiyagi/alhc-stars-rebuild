# Detail behind the H3815 result: both improvement paths, the reward-factor tests, the weight change on the
# two HOS outcome measures, and which measures pull the rating down most.
import os, csv
from recompute_stars import *
import h3815_scenarios as S

C = 'H3815'
cai = CAI[('overall', fac[C]['overall'])]
mapd = sorted(MAPD)
for name, drop in (('published', ()), ('without the 10', S.RULE)):
    for imp in (False, True):
        mset = measure_set('overall', imp, drop)
        mu, v, n = mean_var(stars[C], mset)
        for mode in ('published', 'data'):
            th = thresholds_published('overall', imp) if mode == 'published' else thresholds_from_data('overall', imp, drop, mapd)
            rf = rfactor(mu, v, th)
            print(f"{name:15s} improvement={str(imp):5s} thresholds={mode:9s} n={n} mean={mu:.4f} var={v:.4f} "
                  f"| mean65={th['m65']:.4f} mean85={th['m85']:.4f} var30={th['v30']:.4f} var70={th['v70']:.4f} "
                  f"| reward={rf} raw={mu+rf+cai:.4f} -> {round_half(mu+rf+cai)}")

# 2026 weights for C04/C05 were 1 (Tech Notes 2027, 'Changes' a.)
W_saved = dict(W)
W['C04'] = W['C05'] = 1.0
r = final_rating(C, 'overall')
print(f"H3815 with C04/C05 at their 2026 weight of 1: raw {r[0]:.4f} -> {r[1]}")
W.clear(); W.update(W_saved)

# drag by measure: weight x (measure star - contract mean), with-improvement overall set
mset = measure_set('overall', True, ())
mu, v, n = mean_var(stars[C], mset)
wsum = sum(W[m] for m in mset if m in stars[C])
drag = sorted(((W[m] * (stars[C][m] - mu) / wsum, m, stars[C][m], W[m]) for m in mset if m in stars[C]))
print('largest drags on the weighted mean (stars of overall rating):')
for d, m, s, w in drag[:8]:
    print(f"  {m} star {s} weight {w:g}: {d:+.4f}")
