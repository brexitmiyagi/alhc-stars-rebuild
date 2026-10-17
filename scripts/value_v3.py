"""Value per share, v3: the stars hit as a multi-year path, not one lost year.

What changed from value.py (v2):
- v2 lost one bonus year in full and 34% of a second, then nothing. That 34% came from moving only the
  two survey measures. forward_2028.py moves every measure and applies the measure set CMS already
  finalized for the 2028 ratings: H3815 gets back to 4 stars in 22-29% of draws, not 66%.
- A rating under 3.5 cuts the rebate share from 65% to 50% (42 CFR 422.266(a)(2)(ii)). v2 had no 3-star
  state. Under the 2029 measure set H3815's 2027 stars round to 3.0.
- After the first two rating years the path follows the base-rate transition matrix of all contracts,
  2023-2027 ratings.

Payment year Y uses the ratings released in October Y-2 (the "Y-1 Star Ratings"):
  2028 payments <- 2027 ratings (H3815 3.5, unless the D.C. cases win, then 4.0)
  2029 payments <- 2028 ratings (forward_2028.py, 2028 measure set)
  2030 payments <- 2029 ratings (forward_2028.py, two-step draw, 2029 measure set)
  2031-2032 payments <- base-rate matrix
"""
import os, sys, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DATA = os.path.join(HERE, '..', 'data'); RES = os.path.join(HERE, '..', 'results')
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import bonus_dollars as B
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_inputs.csv')))}

# ---- judgement inputs (change and rerun)
P_WIN = 0.25      # D.C. cases restore 4.0 for 2028 payments (see the piece: Clover for, Humana N.D. Tex. against, both on appeal)
SHARE = 0.50      # share of lost rebate dollars that comes out of margin; the rest is benefit cuts (which cost growth)
RATE = 0.10
GROWTH = 0.05     # H3815 membership growth used to scale later years
YEARS = [2028, 2029, 2030, 2031, 2032]

# ---- rebate arithmetic per member per month, from bonus_dollars.py (2024 plan payment data, 2027 rate book)
reb4 = B.rebate                         # 254.01 at 65% of savings with the bonus in the benchmark
lift_rs = B.lift * B.rs                 # risk-adjusted bonus lift
s0 = reb4 / 0.65 - lift_rs              # savings without the bonus
reb35 = 0.65 * s0
reb30 = 0.50 * s0
members = B.members
L35 = (reb4 - reb35) * members * 12 / 1e6
L30 = (reb4 - reb30) * members * 12 / 1e6
print(f"Rebate a member a month: 4.0 stars {reb4:.2f}, 3.5 stars {reb35:.2f}, 3.0 stars {reb30:.2f}")
print(f"Lost rebate a year vs 4 stars at {members:,.0f} members: 3.5 stars ${L35:.1f}m, 3.0 stars ${L30:.1f}m")

# ---- state distributions by payment year: [4+, 3.5, 3 or less]
fd = {r['scenario']: r for r in csv.DictReader(open(os.path.join(RES, 'forward_dist.csv')))}
g = lambda k: np.array([float(fd[k]['p_4plus']), float(fd[k]['p_3_5']), float(fd[k]['p_3_or_less'])])
d29 = (g('2028 rules, adherence weight 3') + g('2028 rules, adherence weight 1')) / 2
d30 = g('2029 rules, two years out')
# base-rate transitions 2023->2027 ratings, all contracts (rows from, cols to: 4+, 3.5, <=3)
rows = list(csv.DictReader(open(os.path.join(DATA, 'stars_and_enrollment_2019_2027.csv'))))
st = lambda s: 0 if s >= 4 else (1 if s == 3.5 else 2)
M = np.zeros((3, 3))
for Y in range(2023, 2027):
    for r in rows:
        a, b = r[f'stars_{Y}'], r[f'stars_{Y+1}']
        if a and b: M[st(float(a)), st(float(b))] += 1
M = M / M.sum(axis=1, keepdims=True)
print("Base-rate transition matrix (4+, 3.5, 3 or less):\n" + "\n".join("   " + " ".join(f"{v:.3f}" for v in row) for row in M))
d31 = d30 @ M; d32 = d31 @ M

def path(p_win):
    d28 = np.array([p_win, 1 - p_win, 0.0])
    return {2028: d28, 2029: d29, 2030: d30, 2031: d31, 2032: d32}

T = {y: (y - 2026) - 0.29 for y in YEARS}       # years from mid-Oct 2026 to mid payment year
shares = x['shares_outstanding_2026_07_27'] / 1e6
p_pre, p_now = x['price_close_2026_10_08'], x['price_close_2026_10_15']

def value(p_win=P_WIN, share=SHARE, detail=False):
    pv = 0.0; lines = []
    for y, d in path(p_win).items():
        scale = (1 + GROWTH) ** (y - 2028)
        exp_loss = (d[1] * L35 + d[2] * L30) * scale
        pv += share * exp_loss / (1 + RATE) ** T[y]
        lines.append(f"   {y}: P(4+) {d[0]:.0%}, P(3.5) {d[1]:.0%}, P(3 or less) {d[2]:.0%}; expected lost rebate ${exp_loss:.0f}m")
    gain27 = p_win * share * B.up27 / (1 + RATE) ** 0.71
    v = p_pre - (pv - gain27) / shares
    if detail: print("\n".join(lines))
    return v, pv / shares, gain27 / shares

v, loss_ps, gain_ps = value(detail=True)
print(f"Central (win {P_WIN:.0%}, margin share {SHARE:.0%}): value ${v:.2f} (anchor ${p_pre} Oct 8 close; stars path -${loss_ps:.2f}, 2027 upside +${gain_ps:.2f})")
v_v2_style, *_ = value()
grid = []
print("Grid, value per share (rows: margin share; columns: odds the D.C. cases win)")
for s in (0.25, 0.50, 0.75, 1.00):
    row = [round(value(p, s)[0], 2) for p in (0.0, 0.15, 0.30, 0.45, 0.60)]
    grid.append([s] + row)
    print(f"  margin share {s:.0%}: " + '  '.join(f"{p:.0%}: ${r:.2f}" for p, r in zip((0.0, 0.15, 0.30, 0.45, 0.60), row)))
lo, hi = 0.0, 3.0
for _ in range(60):
    m = (lo + hi) / 2
    if value(P_WIN, m)[0] > p_now: lo = m
    else: hi = m
print(f"At {P_WIN:.0%} win odds the ${p_now} price implies {m:.0%} of lost rebate dollars come out of margin")
# 2028-only view (v2 basis) for comparison
only28 = SHARE * (1 - P_WIN) * L35 / (1 + RATE) ** T[2028] / shares
print(f"For comparison, 2028 alone at the central inputs costs ${only28:.2f} a share; the full path costs ${loss_ps:.2f}")
with open(os.path.join(RES, 'value_v3_grid.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['margin_share', 'win_0', 'win_15', 'win_30', 'win_45', 'win_60']); w.writerows(grid)
