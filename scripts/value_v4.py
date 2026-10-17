"""Value per share, v4. Changes from value_v3.py, after a critical read:

1. Horizon cut to 2028-2030 payments. Those years use ratings that are already published (2028) or
   measure sets CMS has already finalized (2029, 2030). Later years depend on bids Alignment hasn't made.
2. Membership held flat. v3 grew members 5% a year while arguing the downgrade slows growth.
3. The anchor. At Baird on Sep 15 management already had its preliminary ratings (Plan Preview 2) and
   declined to discuss them; the stock had its worst day on record. So the Oct 8 close of $8.71 probably
   already carried some odds of a downgrade. If the market put probability q on it and expected the same
   cost C I do, the stock with 4 stars locked in would have been 8.71 + q*C, and fair value is
   8.71 - (1 - q) * C. v3 implicitly used q = 0.
"""
import os, sys, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DATA = os.path.join(HERE, '..', 'data'); RES = os.path.join(HERE, '..', 'results')
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import bonus_dollars as B
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_inputs.csv')))}

P_WIN = 0.25
SHARE = 0.50
RATE = 0.10
Q_CENTRAL = 0.375  # judgement: midpoint of 25-50% odds the Oct 8 price already gave a downgrade, after the Sep 15 silence

reb4 = B.rebate; s0 = reb4 / 0.65 - B.lift * B.rs
L35 = (reb4 - 0.65 * s0) * B.members * 12 / 1e6
L30 = (reb4 - 0.50 * s0) * B.members * 12 / 1e6
fd = {r['scenario']: r for r in csv.DictReader(open(os.path.join(RES, 'forward_dist.csv')))}
g = lambda k: np.array([float(fd[k]['p_4plus']), float(fd[k]['p_3_5']), float(fd[k]['p_3_or_less'])])
d29 = (g('2028 rules, adherence weight 3') + g('2028 rules, adherence weight 1')) / 2
d30 = g('2029 rules, two years out')
T = {2028: 1.71, 2029: 2.71, 2030: 3.71}
shares = x['shares_outstanding_2026_07_27'] / 1e6
p_pre, p_now = x['price_close_2026_10_08'], x['price_close_2026_10_15']

def cost(p_win=P_WIN, share=SHARE, detail=False):
    path = {2028: np.array([p_win, 1 - p_win, 0.0]), 2029: d29, 2030: d30}
    pv = 0.0
    for y, d in path.items():
        el = d[1] * L35 + d[2] * L30
        pv += share * el / (1 + RATE) ** T[y]
        if detail: print(f"   {y} payments: P(4+) {d[0]:.0%}, P(3.5) {d[1]:.0%}, P(3 or less) {d[2]:.0%}; expected lost rebate ${el:.0f}m")
    gain27 = p_win * share * B.up27 / (1 + RATE) ** 0.71
    return (pv - gain27) / shares

C = cost(detail=True)
print(f"Stars cost, 2028-2030 payments, net of the 2027 upside (win {P_WIN:.0%}, margin share {SHARE:.0%}): ${C:.2f} a share")
print(f"Since the Oct 8 close the stock is down ${p_pre - p_now:.2f}")
for q in (0.0, 0.25, 0.5, 0.75):
    print(f"   if the Oct 8 price already gave the downgrade {q:.0%} odds: fair value ${p_pre - (1 - q) * C:.2f}")
fv = p_pre - (1 - Q_CENTRAL) * C
print(f"Central (q {Q_CENTRAL:.0%}): fair value ${fv:.2f} vs ${p_now}")
grid = []
print("Grid (rows: margin share; columns: odds already in the Oct 8 price), 25% win odds")
for s in (0.25, 0.50, 0.75, 1.00):
    c = cost(P_WIN, s)
    row = [round(p_pre - (1 - q) * c, 2) for q in (0.0, 0.25, 0.5, 0.75)]
    grid.append([s] + row)
    print(f"  margin share {s:.0%}: " + '  '.join(f"q {q:.0%}: ${v:.2f}" for q, v in zip((0.0, 0.25, 0.5, 0.75), row)))
with open(os.path.join(RES, 'value_v4_grid.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['margin_share', 'q_0', 'q_25', 'q_50', 'q_75']); w.writerows(grid)
# growth cost in EBITDA terms, for scale
members_total = 294000          # "more than 294,000" at Q2 (OCBJ, from the Q2 release)
ebitda_mid = (x['fy26_adj_ebitda_low_musd'] + x['fy26_adj_ebitda_high_musd']) / 2
lost = 0.051 * B.members
print(f"Growth cost for scale: 5.1 points of H3815's {B.members:,.0f} members = {lost:,.0f} members; at ${ebitda_mid*1e6/members_total:,.0f} adjusted EBITDA a member, ${lost*ebitda_mid/members_total:.1f}m a year")
