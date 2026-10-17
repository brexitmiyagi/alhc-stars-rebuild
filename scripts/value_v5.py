"""Value v5: every judgement that drove v4 replaced by a measured number where one exists.

- Odds by year: forward_v2.py (correlated draws; passed the 2027 backtest).
- Margin share: margin_share.py. Contracts that lost 4 stars cut members' rebates by only a quarter of the
  formula amount; their bids absorbed about 74% (bootstrap 90% interval for pass-through 0.13-0.35).
  Bid cuts can come from margin or from cost management inside the bid, so 74% is an upper bound on margin.
- Lawsuit odds: base rate of decided star-ratings cases (see README): insurers got some relief in about
  5 of 12; on the notice-and-comment theory specifically it is 1 win (Clover) and 1 loss (Humana). 25%.
- What the market already knew: implied from the price instead of assumed.
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
SHARE = 0.74          # measured upper bound (margin_share.py)
RATE = 0.10
PRICE_NOW = 8.28      # Oct 16, 2026 close (Yahoo chart API; StockAnalysis history)
p_pre = x['price_close_2026_10_08']
shares = x['shares_outstanding_2026_07_27'] / 1e6

reb4 = B.rebate; s0 = reb4 / 0.65 - B.lift * B.rs
L35 = (reb4 - 0.65 * s0) * B.members * 12 / 1e6
L30 = (reb4 - 0.50 * s0) * B.members * 12 / 1e6
fd = {r['scenario']: r for r in csv.DictReader(open(os.path.join(RES, 'forward_dist_v2.csv')))}
g = lambda k: np.array([float(fd[k]['p_4plus']), float(fd[k]['p_3_5']), float(fd[k]['p_3_or_less'])])
d29 = (g('2028 rules, adherence weight 3') + g('2028 rules, adherence weight 1')) / 2
d30 = g('2029 rules, two years out')
T = {2028: 1.71, 2029: 2.71, 2030: 3.71}

def cost(p_win=P_WIN, share=SHARE, detail=False):
    path = {2028: np.array([p_win, 1 - p_win, 0.0]), 2029: d29, 2030: d30}
    pv = 0.0
    for y, d in path.items():
        el = d[1] * L35 + d[2] * L30
        pv += share * el / (1 + RATE) ** T[y]
        if detail:
            print(f"   {y} payments: P(4+) {d[0]:.0%}, P(3.5) {d[1]:.0%}, P(3 or less) {d[2]:.0%}; expected lost rebate ${el:.0f}m, to margin ${share*el:.0f}m")
    gain27 = p_win * share * B.up27 / (1 + RATE) ** 0.71
    return (pv - gain27) / shares

C = cost(detail=True)
print(f"Stars cost per share, 2028-2030 payments (win {P_WIN:.0%}, margin share {SHARE:.0%}): ${C:.2f}")
move = p_pre - PRICE_NOW
q_implied = 1 - move / C
print(f"Net move since the Oct 8 close: -${move:.2f} = {move/C:.0%} of the cost, so the Oct 8 price already held about {q_implied:.0%} odds of a downgrade")
for q in (0.25, 0.5, 0.75):
    print(f"   if it held {q:.0%}: fair value ${p_pre - (1-q)*C:.2f}")
grid = []
print("Grid: fair value by margin share (rows) and odds already in the Oct 8 price (columns), 25% win odds")
for s in (0.50, 0.65, 0.74, 0.87, 1.00):
    c = cost(P_WIN, s)
    row = [round(p_pre - (1 - q) * c, 2) for q in (0.25, 0.5, 0.75)]
    grid.append([s] + row)
    print(f"  margin share {s:.0%}: " + '  '.join(f"q {q:.0%}: ${v:.2f}" for q, v in zip((0.25, 0.5, 0.75), row)))
lo = min(min(r[1:]) for r in grid); hi = max(max(r[1:]) for r in grid)
print(f"Range ${lo:.2f}-${hi:.2f}; price ${PRICE_NOW}")
with open(os.path.join(RES, 'value_v5_grid.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['margin_share', 'q_25', 'q_50', 'q_75']); w.writerows(grid)
