"""Value v7. Fixes a counterfactual error in v6.

v6 charged H3815 for every future year below 4 stars, forever. But the October 8 price already assumed that
even a plan that kept 4 stars would sometimes fall below it later. The cost of the October 8 news is the
difference between two paths:
  actual:          2027 ratings 3.5 (4 if the lawsuit wins), then the backtested simulation for the 2028 and
                   2029 ratings, then the good-record transition matrix to perpetuity;
  counterfactual:  2027 ratings 4, then the same good-record matrix.
The CY2027 final rule (April 2026) was public before October 8 and hurts H3815 under both paths, so for the
2029 ratings I apply the same rule shift to the counterfactual that the simulation shows for the actual path
(variant 'shared rule shift'); the variant without it is printed too and gives a higher cost.
The 2026-ratings case (2027 payments) was filed before October 8, so its upside is no longer netted off here.

Two ways the cost can land (margin_share.py, margin_share_robust.py):
 A. Industry pattern: 77% of the cut absorbed in the bid in the first payment year below 4 stars, 55% after,
    and growth 5.1 points a year slower while below 4 stars.
 B. Alignment's own pattern (one episode, PY2022): members take the cut, margin protected, growth slower by
    5.1 or 10 points.
"""
import os, sys, csv, io, contextlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DATA = os.path.join(HERE, '..', 'data'); RES = os.path.join(HERE, '..', 'results')
with contextlib.redirect_stdout(io.StringIO()):
    import bonus_dollars as B
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_inputs.csv')))}
o = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_operating_inputs.csv')))}

RATE, P_WIN, ATTRITION = 0.10, 0.25, 0.10
PRICE = o['price_close_2026_10_16']; p_pre = x['price_close_2026_10_08']
shares = x['shares_outstanding_2026_07_27'] / 1e6
members = B.members
e26 = (o['guide_fy2026_ebitda_low'] + o['guide_fy2026_ebitda_high']) / 2
ebitda_per_member = e26 * 1e6 / o['members_q2_2026']
reb4 = B.rebate; s0 = reb4 / 0.65 - B.lift * B.rs
L35 = (reb4 - 0.65 * s0) * members * 12 / 1e6
L30 = (reb4 - 0.50 * s0) * members * 12 / 1e6

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
n_M = int(M.sum()); M = M / M.sum(1, keepdims=True)
rule_shift = d30 - d29 @ M          # what the 2029 measure removals do to H3815 beyond normal drift

def paths(p_win, shared_rule=True, years=60):
    act = {2028: np.array([p_win, 1 - p_win, 0.0]), 2029: d29, 2030: d30}
    cf = {2028: np.array([1.0, 0.0, 0.0])}
    cf[2029] = cf[2028] @ M
    c30 = cf[2029] @ M + (rule_shift if shared_rule else 0)
    c30 = np.clip(c30, 0, None); cf[2030] = c30 / c30.sum()
    a, c = act[2030], cf[2030]
    for y in range(2031, 2028 + years):
        a, c = a @ M, c @ M; act[y], cf[y] = a, c
    return act, cf

def pv_loss(path, margin, margin_later, growth_pts):
    pv = lost = 0.0
    for y, d in path.items():
        disc = 1 / (1 + RATE) ** ((y - 2026) - 0.29)
        m = margin if y == 2028 else margin_later
        pv += m * (d[1] * L35 + d[2] * L30) * disc
        lost = lost * (1 - ATTRITION) + (d[1] + d[2]) * growth_pts * members
        pv += lost * ebitda_per_member / 1e6 * disc
    return pv

def cost(p_win=P_WIN, margin=0.77, margin_later=0.55, growth_pts=0.051, shared_rule=True, horizon=None):
    act, cf = paths(p_win, shared_rule)
    if horizon:
        act = {y: d for y, d in act.items() if y <= horizon}; cf = {y: d for y, d in cf.items() if y <= horizon}
    return (pv_loss(act, margin, margin_later, growth_pts) - pv_loss(cf, margin, margin_later, growth_pts)) / shares

out = []
P = lambda s: (print(s), out.append(s))
P(f"Good-record transition matrix (4+, 3.5, <=3), {n_M} contract-years:\n{M.round(3)}")
act, cf = paths(P_WIN)
for y in (2028, 2029, 2030, 2032, 2035, 2040):
    P(f"  payment {y}: actual P(below 4) {act[y][1]+act[y][2]:.2f}  counterfactual {cf[y][1]+cf[y][2]:.2f}")
P(f"Rule shift applied to both paths in 2030 payments: {rule_shift.round(3)}")
A = cost(); A28 = cost(horizon=2030); A_noshare = cost(shared_rule=False)
B1 = cost(margin=0.0, margin_later=0.0, growth_pts=0.051); B2 = cost(margin=0.0, margin_later=0.0, growth_pts=0.10)
P(f"Cost of the Oct 8 news per share: A ${A:.2f} (payments 2028-2030 ${A28:.2f}; without the shared rule shift ${A_noshare:.2f}); B ${B1:.2f} at 5.1 pts, ${B2:.2f} at 10 pts")
mult = (PRICE * shares - o['cash_consolidated_2026_06_30_musd'] + o['convertible_notes_face_musd']) / e26
hit28 = 0.77 * (1 - P_WIN) * L35
P(f"Multiple view: {mult:.1f}x EV/2026 adj. EBITDA x expected 2028 hit ${hit28:.0f}m = ${mult*hit28/shares:.2f} a share; it treats 2028 as permanent, the cash-flow view lets the gap close")
P(f"Sensitivities on A: discount 8% / 12%, margin later 0.77, attrition 5%")
for lab, kw in (('margin later 0.77', dict(margin_later=0.77)), ('lawsuit 0%', dict(p_win=0.0)), ('lawsuit 50%', dict(p_win=0.5))):
    P(f"   {lab}: ${cost(**kw):.2f}")
globals()['RATE'] = 0.08; c8 = cost(); globals()['RATE'] = 0.12; c12 = cost(); globals()['RATE'] = 0.10
globals()['ATTRITION'] = 0.05; c_att = cost(); globals()['ATTRITION'] = 0.10
P(f"   discount 8% ${c8:.2f}, 12% ${c12:.2f}; attrition 5% ${c_att:.2f}")

P("\nFair value = Oct 8 close less the part of the cost the Oct 8 price had not already carried")
res = []
for name, c in (('A industry', A), ('B Alignment, 5.1 pts', B1), ('B Alignment, 10 pts', B2)):
    for q in (0.31, 0.40, 0.50):
        fv = p_pre - (1 - q) * c; res.append((name, q, c, fv))
        P(f"   {name:22s} cost ${c:.2f}, prior {q:.0%}: fair value ${fv:.2f}")
    imp = 1 - (p_pre - PRICE) / c
    P(f"   {'':22s} price-implied prior at ${PRICE}: " + (f"{imp:.0%}" if imp >= 0 else "none, the price is below this value even with nothing priced in advance"))
central = p_pre - 0.60 * (0.5 * A + 0.25 * B1 + 0.25 * B2)   # A and B equal; B split across its two growth cases
lo = min(r[3] for r in res); hi = max(r[3] for r in res)
P(f"Central (A 50%, B 50% split evenly across 5.1 and 10 pts, prior 40%): ${central:.2f}; grid ${lo:.2f} to ${hi:.2f}; price ${PRICE}")
blend = lambda pw: 0.5 * cost(p_win=pw) + 0.25 * cost(p_win=pw, margin=0, margin_later=0) + 0.25 * cost(p_win=pw, margin=0, margin_later=0, growth_pts=0.10)
P(f"If the 2027 case wins (H3815 4 stars for 2028 payments): blended cost ${blend(1.0):.2f}, fair value ${p_pre - 0.6*blend(1.0):.2f}")
P(f"If it loses for certain: blended cost ${blend(0.0):.2f}, fair value ${p_pre - 0.6*blend(0.0):.2f}")
P(f"Fall from the Sep 14 close $12.94 to ${PRICE}: ${12.94-PRICE:.2f}; full stars cost with nothing priced in advance is A ${A:.2f} ({A/(12.94-PRICE):.0%}), B ${B1:.2f}-${B2:.2f} ({B1/(12.94-PRICE):.0%}-{B2/(12.94-PRICE):.0%})")
with open(os.path.join(RES, 'value_v7.csv'), 'w', newline='') as fh:
    wr = csv.writer(fh); wr.writerow(['path', 'prior', 'cost_per_share', 'fair_value'])
    for r in res: wr.writerow([r[0], r[1], round(r[2], 3), round(r[3], 2)])
open(os.path.join(RES, 'value_v7.txt'), 'w').write('\n'.join(out) + '\n')
