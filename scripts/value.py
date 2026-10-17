# What the stars hit is worth per share, and what the price is already paying for.
# Anchor: the October 8 close, the day before the ratings hit the price. Everything else comes from
# bonus_dollars.py (the cash hole and the 2026-case upgrade) and hos_noise.py (the odds H3815 is still
# below 4 stars in next year's ratings). Judgement inputs are at the top. Change them and rerun.
import os, sys, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DATA = os.path.join(HERE, '..', 'data')
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import bonus_dollars as B
    import hos_noise as N
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_inputs.csv')))}

P_WIN = 0.30      # judgement: Judge Cooper strikes the 10 measures and CMS pays on the recalculated ratings
SHARE = 0.50      # judgement: share of lost rebate dollars that lands on margin (the rest is benefit trims and provider risk pools)
RATE = 0.10
GROWTH = 0.05
T27, T28, T29 = 0.71, 1.71, 2.71   # years from mid-October 2026 to the middle of each payment year
Q_LOW = 1 - N.p4                   # odds H3815 is still under 4 stars in the 2028 ratings, if the case is lost

shares = x['shares_outstanding_2026_07_27'] / 1e6
p_pre, p_now, p_sep = x['price_close_2026_10_08'], x['price_close_2026_10_15'], x['price_close_2026_09_04']
L28 = B.cash                                     # $m, 2028 rebate dollars lost at 3.5 stars
U27 = B.up27                                     # $m, 2027 upside if the 2026-ratings case wins (65% -> 70%)
d = lambda t: 1 / (1 + RATE) ** t

def value(p=P_WIN, s=SHARE, q=Q_LOW):
    loss28 = (1 - p) * s * L28 * d(T28)
    loss29 = (1 - p) * q * s * L28 * (1 + GROWTH) * d(T29)
    gain27 = p * s * U27 * d(T27)
    return p_pre - (loss28 + loss29 - gain27) / shares, loss28 / shares, loss29 / shares, gain27 / shares

mcap = p_now * shares
ev = mcap - x['cash_2026_06_30_musd'] + x['long_term_debt_2026_06_30_musd']
mid = (x['fy26_adj_ebitda_low_musd'] + x['fy26_adj_ebitda_high_musd']) / 2
print(f"Shares {shares:.1f}m. Market value at ${p_now}: ${mcap:,.0f}m; EV ${ev:,.0f}m = {ev/mid:.1f}x 2026 adjusted EBITDA midpoint")
print(f"Since Sep 4 (${p_sep}): -${(p_sep-p_now)*shares:,.0f}m. Oct 9 alone: -${(p_pre-x['price_close_2026_10_09'])*shares:,.0f}m. Since the Oct 8 close: -${(p_pre-p_now)*shares:,.0f}m (${p_pre-p_now:.2f} a share)")
print(f"Whole 2028 cash hole, no offsets, today's money: ${L28*d(T28)/shares:.2f} a share")
v, a, b, c = value()
print(f"Central case (win {P_WIN:.0%}, margin share {SHARE:.0%}, still-low odds {Q_LOW:.0%}): value ${v:.2f}; 2028 -{a:.2f}, 2029 -{b:.2f}, 2027 upside +{c:.2f}")
print("Grid, value per share (rows: share of lost dollars on margin; columns: odds the D.C. cases win)")
grid = []
for s in (0.25, 0.50, 0.75, 1.00):
    row = [round(value(p, s)[0], 2) for p in (0.0, 0.15, 0.30, 0.45, 0.60)]
    grid.append([s] + row)
    print(f"  margin share {s:.0%}: " + '  '.join(f"{p:.0%}: ${r:.2f}" for p, r in zip((0.0, 0.15, 0.30, 0.45, 0.60), row)))
# what margin share does today's price imply, at 30% win odds?
lo, hi = 0.0, 3.0
for _ in range(60):
    mid_s = (lo + hi) / 2
    if value(P_WIN, mid_s)[0] > p_now: lo = mid_s
    else: hi = mid_s
print(f"At {P_WIN:.0%} win odds the ${p_now} price implies {mid_s:.0%} of the lost dollars land on margin")
with open(os.path.join(HERE, '..', 'results', 'value_grid.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['margin_share', 'win_0', 'win_15', 'win_30', 'win_45', 'win_60']); w.writerows(grid)
