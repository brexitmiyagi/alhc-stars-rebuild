"""Value v8: the stars-adjusted value, with two corrections to v7 from the tests run on 17 Oct 2026.

1. Persistence. matrix_backtest.py shows the first-order matrix closes the gap between dropped and held
   contracts too fast after two years (3 years out: predicted 13 points, actual 23-35 across cohorts). So
   from 2031 the gap between H3815's downgraded path and its 4-star counterfactual decays at the rate seen
   in the data, 0.84 a year (pooled gap 39.5 points one year out, 27.6 three years out), not the matrix's.
2. Member economics. v7 valued a member not gained at the average adjusted EBITDA per member. Alignment
   says about half its members are in their first or second year and carry a higher MBR, and puts the
   gross profit of its current book at maturity at about $880m against $640m at the 2026 guidance
   midpoint (Q2 2026 call). With half the book new, that implies a new member earns about $1,340 of gross
   profit a year against $2,940 for a mature one. Taking adjusted SG&A per member as equal across
   cohorts ($1,623 = (640 - 154) / 299,500), a lost member is worth about -$290 of EBITDA in each of its
   first two years and +$1,315 after that.

This is the value of the stars news against the October 8 price. It is not a price target; the target
comes from valuation_v1.py.
"""
import os, sys, csv, io, contextlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import value_v7 as V
RES = os.path.join(HERE, '..', 'results')

DECAY = (27.6 / 39.5) ** 0.5            # matrix_backtest.py pooled gaps, 3-of-4 filter
GP_NOW, GP_MATURE, MEMBERS_26 = 640.0, 880.0, 299_500   # Q2 2026 call: guidance midpoint, embedded potential; FY26 member guide midpoint
SGA = (GP_NOW - V.e26) * 1e6 / MEMBERS_26
gp_avg = GP_NOW * 1e6 / MEMBERS_26; gp_mat = GP_MATURE * 1e6 / MEMBERS_26
gp_new = 2 * gp_avg - gp_mat
E_NEW, E_MAT = gp_new - SGA, gp_mat - SGA

def paths(p_win, persist=True):
    act, cf = V.paths(p_win)
    if persist:
        g30 = (act[2030][1] + act[2030][2]) - (cf[2030][1] + cf[2030][2])
        for y in range(2031, max(act) + 1):
            below_cf = cf[y][1] + cf[y][2]
            below = min(1.0, below_cf + g30 * DECAY ** (y - 2030))
            split = act[y][2] / (act[y][1] + act[y][2])
            act[y] = np.array([1 - below, below * (1 - split), below * split])
    return act, cf

def pv_loss(path, margin, margin_later, growth_pts, tenure=True):
    pv = 0.0; cohorts = []
    for y, d in sorted(path.items()):
        disc = 1 / (1 + V.RATE) ** ((y - 2026) - 0.29)
        m = margin if y == 2028 else margin_later
        pv += m * (d[1] * V.L35 + d[2] * V.L30) * disc
        cohorts = [[n * (1 - V.ATTRITION), a + 1] for n, a in cohorts]
        cohorts.append([(d[1] + d[2]) * growth_pts * V.members, 0])
        if tenure:
            ebitda = sum(n * (E_NEW if a < 2 else E_MAT) for n, a in cohorts)
        else:
            ebitda = sum(n for n, a in cohorts) * V.ebitda_per_member
        pv += ebitda / 1e6 * disc
    return pv

def cost(p_win=V.P_WIN, margin=0.77, margin_later=0.55, growth_pts=0.051, persist=True, tenure=True):
    act, cf = paths(p_win, persist)
    return (pv_loss(act, margin, margin_later, growth_pts, tenure) - pv_loss(cf, margin, margin_later, growth_pts, tenure)) / V.shares

out = []
P = lambda s: (print(s), out.append(s))
P(f"Gap decay used after 2030: {DECAY:.3f} a year (matrix implies about 0.55)")
P(f"Member economics: gross profit a member ${gp_avg:,.0f} now, ${gp_mat:,.0f} mature, ${gp_new:,.0f} new; SG&A ${SGA:,.0f}; EBITDA a member new ${E_NEW:,.0f}, mature ${E_MAT:,.0f} (average ${V.ebitda_per_member:,.0f})")
act, cf = paths(V.P_WIN)
P("Below 4 stars, downgraded vs counterfactual: " + ', '.join(f"{y} {act[y][1]+act[y][2]:.0%}/{cf[y][1]+cf[y][2]:.0%}" for y in (2028, 2029, 2030, 2032, 2035, 2040)))
rows = []
for lab, kw in (('v7 as published (matrix, average member)', dict(persist=False, tenure=False)),
                ('persistence only', dict(persist=True, tenure=False)),
                ('tenure economics only', dict(persist=False, tenure=True)),
                ('v8 (both)', dict(persist=True, tenure=True))):
    a = cost(**kw); b1 = cost(margin=0, margin_later=0, **kw); b2 = cost(margin=0, margin_later=0, growth_pts=0.10, **kw)
    blend = 0.5 * a + 0.25 * b1 + 0.25 * b2
    rows.append((lab, a, b1, b2, blend))
    P(f"{lab:42s} A ${a:.2f}  B5.1 ${b1:.2f}  B10 ${b2:.2f}  blend ${blend:.2f}")
A, B1, B2, BL = rows[-1][1:]
p_pre, PRICE = V.p_pre, V.PRICE
P("\nStars-adjusted value = Oct 8 close less the part of the cost not already priced")
grid = []
for name, c in (('A industry', A), ('B Alignment 5.1 pts', B1), ('B Alignment 10 pts', B2), ('Blend', BL)):
    vals = [p_pre - (1 - q) * c for q in (0.31, 0.40, 0.50)]
    grid.append((name, c, vals))
    P(f"   {name:20s} cost ${c:.2f}: " + '  '.join(f"{q:.0%} ${v:.2f}" for q, v in zip((0.31, 0.40, 0.50), vals)))
lo = min(min(g[2]) for g in grid); hi = max(max(g[2]) for g in grid)
P(f"Central (blend, prior 40%): ${p_pre - 0.6*BL:.2f}; range ${lo:.2f}-${hi:.2f}; price ${PRICE}")
fall = 12.94 - PRICE
P(f"Share of the ${fall:.2f} fall since Sep 14 explained by the full stars cost: A {A/fall:.0%}, B {B1/fall:.0%}-{B2/fall:.0%}, blend {BL/fall:.0%}; unexplained ${fall-A:.2f}-${fall-B1:.2f}")
blend_w = lambda pw: 0.5 * cost(p_win=pw) + 0.25 * cost(p_win=pw, margin=0, margin_later=0) + 0.25 * cost(p_win=pw, margin=0, margin_later=0, growth_pts=0.10)
P(f"2027-ratings case: win -> value ${p_pre - 0.6*blend_w(1.0):.2f}, lose -> ${p_pre - 0.6*blend_w(0.0):.2f}")
with open(os.path.join(RES, 'value_v8.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['path', 'cost_per_share', 'prior_31', 'prior_40', 'prior_50'])
    for name, c, vals in grid: w.writerow([name, round(c, 3)] + [round(v, 2) for v in vals])
open(os.path.join(RES, 'value_v8.txt'), 'w').write('\n'.join(out) + '\n')
