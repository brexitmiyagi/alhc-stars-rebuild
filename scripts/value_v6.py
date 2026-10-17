"""Value v6. Fixes the two problems left in v5.

1. Horizon. v5 stopped at 2030 payments. Here 2028-2030 use the backtested simulation and every later year
   follows a transition matrix estimated on contracts with a good record (4+ stars in at least 3 of the
   previous 4 ratings, like H3815), to perpetuity, membership flat, 10% discount rate. The multiple view
   (today's EV/EBITDA times the 2028 hit) is printed alongside for comparison.
2. Circularity. v5 inferred the market's prior from the price. Here the prior comes from outside the price:
   the same backtested method, run on the public 2026 data before the ratings, gave H3815 a 69% chance of
   keeping 4 stars, so an informed outsider started at 31%. Management's silence at Baird on Sep 15 can only
   push that up; I use 31% to 50%. The price-implied prior is printed for comparison, not used.

Two ways the cost can land (margin_share.py, margin_share_robust.py):
 A. Industry pattern: plans absorb ~77% of the cut in their bids (pass-through 0.20-0.26 across tests),
    members see the rest, and growth slows by the observed 5.1 points a year while below 4 stars.
 B. Alignment's own pattern: when H3815 lost its 4.5-star rebate share in 2022 it cut members' rebates by
    1.5x the formula. Margin is protected and the whole cost shows up as slower growth. I run growth at
    5.1 and 10 points.
"""
import os, sys, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DATA = os.path.join(HERE, '..', 'data'); RES = os.path.join(HERE, '..', 'results')
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import bonus_dollars as B
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_inputs.csv')))}
o = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_operating_inputs.csv')))}

RATE, P_WIN = 0.10, 0.25
PRICE = o['price_close_2026_10_16']; p_pre = x['price_close_2026_10_08']
shares = x['shares_outstanding_2026_07_27'] / 1e6
members = B.members
ebitda_per_member = ((o['guide_fy2026_ebitda_low'] + o['guide_fy2026_ebitda_high']) / 2) * 1e6 / o['members_q2_2026']
reb4 = B.rebate; s0 = reb4 / 0.65 - B.lift * B.rs
L35 = (reb4 - 0.65 * s0) * members * 12 / 1e6
L30 = (reb4 - 0.50 * s0) * members * 12 / 1e6

# state paths: [4+, 3.5, 3 or less]
fd = {r['scenario']: r for r in csv.DictReader(open(os.path.join(RES, 'forward_dist_v2.csv')))}
g = lambda k: np.array([float(fd[k]['p_4plus']), float(fd[k]['p_3_5']), float(fd[k]['p_3_or_less'])])
d29 = (g('2028 rules, adherence weight 3') + g('2028 rules, adherence weight 1')) / 2
d30 = g('2029 rules, two years out')
rows = list(csv.DictReader(open(os.path.join(DATA, 'stars_and_enrollment_2019_2027.csv'))))
f = lambda v: float(v) if v else None
st = lambda s: 0 if s >= 4 else (1 if s == 3.5 else 2)
M = np.zeros((3, 3))
for Y in range(2023, 2027):
    for r in rows:
        a, b = f(r[f'stars_{Y}']), f(r[f'stars_{Y+1}'])
        hist = [f(r[f'stars_{y}']) for y in range(Y - 4, Y)]
        if a is None or b is None or any(h is None for h in hist): continue
        if sum(h >= 4 for h in hist) >= 3: M[st(a), st(b)] += 1
M = M / M.sum(1, keepdims=True)
w, v = np.linalg.eig(M.T); pi = np.real(v[:, np.argmin(abs(w - 1))]); pi = pi / pi.sum()

def path(p_win, years=60):
    d = {2028: np.array([p_win, 1 - p_win, 0.0]), 2029: d29, 2030: d30}
    cur = d30
    for y in range(2031, 2028 + years):
        cur = cur @ M; d[y] = cur
    return d

ATTRITION = 0.10   # H3815 'Members Choosing to Leave the Plan' 10% (CMS 2027 measure data, C28); deaths not added, so conservative

def cost(p_win=P_WIN, margin=0.77, margin_later=0.55, growth_pts=0.051, horizon=None):
    """PV per share of the stars cost. Margin channel: share of lost rebate from margin, 77% in the first
    payment year below 4 stars and 55% after (margin_share_robust.py, tests 1-4 and 6). Growth channel:
    members not gained each year below 4 stars, worth EBITDA per member a year, leaving at the plan's
    10% voluntary disenrollment rate."""
    pv = 0.0
    lost_members = 0.0
    for y, d in path(p_win).items():
        if horizon and y > horizon: break
        t = (y - 2026) - 0.29
        disc = 1 / (1 + RATE) ** t
        m = margin if y == 2028 else margin_later
        pv += m * (d[1] * L35 + d[2] * L30) * disc
        lost_members = lost_members * (1 - ATTRITION) + (d[1] + d[2]) * growth_pts * members
        pv += lost_members * ebitda_per_member / 1e6 * disc
    gain27 = p_win * margin * B.up27 / (1 + RATE) ** 0.71
    return (pv - gain27) / shares

print(f"Good-record transition matrix (4+, 3.5, <=3):\n{M.round(3)}\nlong-run shares {pi.round(3)}; long-run expected rebate loss ${pi[1]*L35+pi[2]*L30:.0f}m a year")
print(f"EBITDA per member ${ebitda_per_member:,.0f} (2026 guidance midpoint / Q2 membership)")
A = cost(margin=0.77, growth_pts=0.051)
A_to2030 = cost(margin=0.77, growth_pts=0.051, horizon=2030)
B1 = cost(margin=0.0, margin_later=0.0, growth_pts=0.051)
B2 = cost(margin=0.0, margin_later=0.0, growth_pts=0.10)
print(f"Stars cost per share, full horizon: A industry pattern ${A:.2f} (2028-2030 only ${A_to2030:.2f}); B Alignment pattern ${B1:.2f} at 5.1 pts growth, ${B2:.2f} at 10 pts")
ev = o['price_close_2026_10_16'] * shares - o['cash_consolidated_2026_06_30_musd'] + o['convertible_notes_face_musd']
mult = ev / ((o['guide_fy2026_ebitda_low'] + o['guide_fy2026_ebitda_high']) / 2)
hit28 = 0.77 * (1 - P_WIN) * L35
print(f"Multiple view for comparison: {mult:.1f}x x expected 2028 margin hit ${hit28:.0f}m = ${mult*hit28/shares:.2f} a share, which treats 2028 as permanent")

print("\nFair value = Oct 8 close less the part of the cost not already priced (prior from outside the price)")
res = []
for name, c in (('A industry', A), ('B Alignment, 5.1 pts', B1), ('B Alignment, 10 pts', B2)):
    for q in (0.31, 0.40, 0.50):
        fv = p_pre - (1 - q) * c
        res.append((name, q, c, fv))
        print(f"   {name:22s} cost ${c:.2f}, prior {q:.0%}: fair value ${fv:.2f}")
    print(f"   {'':22s} price-implied prior at ${PRICE}: {1 - (p_pre - PRICE)/c:.0%}")
central = p_pre - (1 - 0.40) * (0.5 * A + 0.5 * B1)
print(f"Central (equal weight A and B at 5.1 pts, prior 40%): ${central:.2f}; price ${PRICE}")
with open(os.path.join(RES, 'value_v6.csv'), 'w', newline='') as fh:
    wr = csv.writer(fh); wr.writerow(['path', 'prior', 'cost_per_share', 'fair_value'])
    for r in res: wr.writerow([r[0], r[1], round(r[2], 3), round(r[3], 2)])
