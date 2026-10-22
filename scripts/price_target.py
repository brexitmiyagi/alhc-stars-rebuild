"""The price target at the 21 October close, with the review changes.

Changes from valuation_v10.py: closing prices (that file used prices pulled before the close), the P/E check
dropped (at under 1% net margin after stock pay one point of cost ratio moves 2027 EPS by more than 100%, so a
P/E says little this year), a straight-debt cost check on the discount rate (the 4.25% is a convertible coupon),
the stars cost at 0%, 25% and 50% lawsuit odds, and the comparable value at the 8 October close.

Earlier notes from valuation_v10.py:

What changed from valuation_bank.py:
  - One primary method: peer-median forward EV/EBITDA on 2027, EBITDA after stock pay, cash netted the
    same way peers net it. P/E and a DCF are cross-checks, not averaged in.
  - Shares held at today's 215.0m diluted. Stock pay is expensed, so growing the share count as well would
    count it twice.
  - The DCF discount rate comes from betas (Yahoo 5y monthly, and my own 2y weekly), the 10-year Treasury
    at 5.10% (FRED, 15 Oct) and Damodaran's 4.20% implied premium (1 Oct). The stars cost is rerun at the
    same rate.
  - Scenarios are symmetric around base (plus the bridge's own asymmetric cases, shown separately).
  - Peer-set sensitivity, 2026 guidance arithmetic, a backtest of the bridge, dilution vs peers,
    positioning and valuation history.
"""
import os, sys, csv, io, contextlib
import numpy as np
from openpyxl import load_workbook
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
D = lambda f: os.path.join(HERE, '..', 'data', f)
rd = lambda f: list(csv.DictReader(open(D(f))))
kv = lambda f: {r['item']: r['value'] for r in rd(f)}
out = []
P = lambda s='': (print(s), out.append(s))

wb = load_workbook(os.path.join(HERE, '..', 'model', 'ALHC_model.xlsx'), data_only=True)
M = wb['Model']; g = lambda a: M[a].value
REV26, E26, SBC26 = g('P8'), g('P14'), g('P19')
REV27, E27, DA27, INT27, SBC27, MBR27 = g('Q8'), g('Q14'), g('Q17'), g('Q18'), g('Q19'), g('Q10')
REV28, E28, SBC28 = g('R8'), g('R16'), g('R19')
HIT28 = -g('R15')

SH, TAX, NOL = 215.024483, 0.24, 0.463
PRICE = None  # set below from prices_2026_10_21.csv
RF, ERP, KD = 0.0515, 0.0420, 0.0425  # 10-year Treasury 5.15% on 19 Oct (FRED DGS10, latest on 22 Oct)
reg = {k: float(v) for k, v in kv('regulatory_capital.csv').items()}
CASH, DEBT, PARENT, DIVD = reg['consolidated_cash_and_st_inv_2026_06_30_musd'], reg['convertible_face_musd'], reg['parent_cash_2026_06_30_musd'], reg['dividendable_2025_12_31_musd']
peers = [r for r in rd('peers_consensus_2026_10.csv') if r['ticker'] != 'ALHC']
# prices rolled to the latest close (consensus EPS and EBITDA rechecked on Yahoo 22 Oct: unchanged)
LATEST = {r['ticker']: float(r['close_2026_10_21']) for r in rd('prices_2026_10_21_close.csv')}
for r in peers: r['price_2026_10_16'] = str(LATEST[r['ticker']])
cons = [r for r in rd('peers_consensus_2026_10.csv') if r['ticker'] == 'ALHC'][0]
ev_m = {r['ticker']: (float(r['price_2026_10_16']) * float(r['shares_m']) + float(r['net_debt_2025_musd'])) / float(r['ebitda_2027_cons_musd']) for r in peers}
pe_m = {r['ticker']: float(r['price_2026_10_16']) / float(r['adj_eps_2027_yahoo']) for r in peers}
med = lambda d, drop=(): float(np.median([v for k, v in d.items() if k not in drop]))
MEV, MPE = med(ev_m), med(pe_m)

# ---- discount rate
betas = {r['ticker']: (float(r['beta_yahoo_5y_monthly']), float(r['beta_2y_weekly_mine'])) for r in rd('betas_2026_10.csv')}
peer_beta = float(np.median([b[0] for t, b in betas.items() if t != 'ALHC']))
PRICE = LATEST['ALHC']
E_VAL = PRICE * SH; wE = E_VAL / (E_VAL + DEBT)
wacc = lambda beta, prem=0.0: wE * (RF + beta * ERP + prem) + (1 - wE) * KD * (1 - TAX)
W = {'peer median beta': wacc(peer_beta), 'Alignment beta (base)': wacc(betas['ALHC'][0]), 'Alignment beta + 1% size premium': wacc(betas['ALHC'][0], 0.01)}
WACC = W['Alignment beta (base)']
P(f"Discount rate: risk-free {RF:.2%}, premium {ERP:.2%}, betas Alignment {betas['ALHC'][0]:.2f} (5y monthly; {betas['ALHC'][1]:.2f} on my 2y weekly), peer median {peer_beta:.2f}; equity weight {wE:.0%}")
for k, v in W.items(): P(f"  WACC, {k}: {v:.2%}")

# ---- stars cost at the same rate (value_v8.py), restated per diluted share
with contextlib.redirect_stdout(io.StringIO()):
    import value_v8 as S8
def stars_cost(rate):
    S8.V.RATE = rate
    c = 0.5 * S8.cost() + 0.25 * S8.cost(margin=0, margin_later=0) + 0.25 * S8.cost(margin=0, margin_later=0, growth_pts=0.10)
    return c * S8.V.shares / SH
STARS = stars_cost(WACC); STARS10 = stars_cost(0.10)
STARS_2028 = HIT28 / (1 + WACC) ** (2028.5 - 2026.79) / SH
P(f"Stars cost per diluted share: ${STARS:.2f} at {WACC:.2%} (${STARS10:.2f} at 10%); of which the 2028 hit ${STARS_2028:.2f}")

# ---- methods
e_after = lambda E: E - SBC27
def ev_leg(E, mult=None, nd=DEBT - CASH):
    return ((mult or MEV) * e_after(E) - nd) / SH - STARS
def pe_leg(E, mult=None):
    eps = (e_after(E) - DA27 - INT27) * (1 - TAX) / SH
    return (mult or MPE) * eps + NOL - STARS, eps
def dcf(E, mstar=0.03, w=None, gT=0.03, growth=(0.14, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03)):
    """FCF = EBITDA after stock pay - 24% tax on (EBITDA - D&A) - capex (= D&A = 0.5% of revenue).
    Claims cash is working capital here: it arrives with premiums and leaves with claims, so the DCF credits
    only cash free of claims and of the capital rules (parent cash plus what subsidiaries can pay up).
    The multiple leg nets all cash because the peers' enterprise values do."""
    w = w or WACC
    m27 = e_after(E) / REV27; m28 = (E28 - SBC28) / REV28 + (m27 - e_after(E27) / REV27)
    revs = {2027: REV27, 2028: REV28}; y = 2028
    for gg in growth:
        y += 1; revs[y] = revs[y - 1] * (1 + gg)
    pv = 0.0
    for Y in range(2027, 2037):
        m = m27 if Y == 2027 else m28 if Y == 2028 else (m28 + (mstar - m28) * (Y - 2028) / 5 if Y <= 2033 else mstar)
        R = revs[Y]; eb = m * R; fcf = eb - TAX * (eb - 0.005 * R) - 0.005 * R
        pv += fcf / (1 + w) ** (Y - 2026.29)
    tv = fcf * (1 + gT) / (w - gT) / (1 + w) ** (2036 - 2026.29)
    return (pv + tv + PARENT + DIVD - DEBT) / SH + NOL - (STARS - STARS_2028)

PT = ev_leg(E27); pe_v, eps = pe_leg(E27); dcf_v = dcf(E27)
P(f"\nPrimary: peer-median EV/EBITDA {MEV:.2f}x on 2027 EBITDA after stock pay ${e_after(E27):.1f}m, net cash ${CASH - DEBT:.0f}m -> ${PT:.2f} ({PT / PRICE - 1:+.0%})")
P(f"Cross-check DCF at {WACC:.2%}, 3% long-run margin: ${dcf_v:.2f}")
for k, w in W.items():
    imp = brentq(lambda m: dcf(E27, m, w) - PRICE, 0.0, 0.2)
    P(f"  DCF at {w:.2%} ({k}): 2.5% ${dcf(E27, 0.025, w):.2f}, 3% ${dcf(E27, 0.03, w):.2f}, 4% ${dcf(E27, 0.04, w):.2f}; price-implied long-run margin {imp:.2%}")
P(f"  Margin after stock pay: 2026E {(E26 - SBC26) / REV26:.2%}, 2027E {e_after(E27) / REV27:.2%}, 2028E {(E28 - SBC28) / REV28:.2%}")
P(f"Company-adjusted EBITDA (stock pay left out) on the same multiple: ${((MEV * E27 - (DEBT - CASH)) / SH - STARS):.2f}")

P('\nCash treatment on the primary method:')
for k, nd in (('consolidated (as peers)', DEBT - CASH), ('parent plus dividend capacity', DEBT - PARENT - DIVD), ('parent only', DEBT - PARENT)):
    P(f"  {k}: ${ev_leg(E27, nd=nd):.2f}")

P('\nPeer-set sensitivity (EV/EBITDA median -> target):')
for lab, drop in (('all seven', ()), ('without CVS and Cigna (diversified)', ('CVS', 'CI')), ('without Humana and Molina (recovering earnings)', ('HUM', 'MOH')), ('without all four', ('CVS', 'CI', 'HUM', 'MOH'))):
    P(f"  {lab}: {med(ev_m, drop):.2f}x -> ${ev_leg(E27, med(ev_m, drop)):.2f}")

shift = lambda mbr: E27 - (mbr - MBR27) * REV27
per_pt = ev_leg(shift(MBR27 - 0.005)) - ev_leg(shift(MBR27 + 0.005))
P(f"\nOne point of 2027 MBR: ${per_pt:.2f} a share on the primary method")
for lab, d in (('symmetric +/-1.2 pts', 0.012),):
    b, u = ev_leg(shift(MBR27 + d)), ev_leg(shift(MBR27 - d))
    P(f"  {lab}: bear {MBR27 + d:.2%} ${b:.2f}, base ${PT:.2f}, bull {MBR27 - d:.2%} ${u:.2f}; 25/50/25 ${0.25 * b + 0.5 * PT + 0.25 * u:.2f}")
b, u = ev_leg(shift(MBR27 + 0.0153)), ev_leg(shift(MBR27 - 0.0084))
P(f"  bridge cases (+1.53 / -0.84 pts): bear ${b:.2f}, bull ${u:.2f}; 25/50/25 ${0.25 * b + 0.5 * PT + 0.25 * u:.2f}")
imp27 = brentq(lambda m: ev_leg(shift(m)) - PRICE, 0.80, 0.95)
P(f"  2027 MBR at which the primary method equals the price: {imp27:.2%} (my {MBR27:.2%}; consensus EBITDA ${float(cons['ebitda_2027_cons_musd']):.1f}m vs mine ${E27:.1f}m)")

# ---- 2026 guidance arithmetic
H1, Q3_25, Q4_25 = 37.851 + 68.145, 32.439, 11.4  # Q4 2025 adj. EBITDA $11.4m (Q4 2025 release)
P(f"\n2026 guidance: adj. EBITDA $145m-$163m; H1 actual ${H1:.1f}m, so H2 must be ${145 - H1:.1f}m-${163 - H1:.1f}m; Q3 guide $20m-$30m")
ratio = Q4_25 / Q3_25
for q3 in (15, 20, 25, 30, 35):
    P(f"  Q3 ${q3}m: Q4 needed for the low end ${145 - H1 - q3:.1f}m; FY if Q4 = Q3 x {ratio:.2f} (2025 shape) ${H1 + q3 * (1 + ratio):.1f}m")
P(f"  Q3 needed to hold $145m on 2025's Q4/Q3 shape: ${(145 - H1) / (1 + ratio):.1f}m")

# ---- bridge backtest
bt = {k: float(v) for k, v in kv('bridge_backtest_inputs.csv').items()}
RET, GAP = 0.88, 0.0921
ye = {2022: bt['members_ye2022_k'], 2023: bt['members_ye2023_k'], 2024: bt['members_ye2024_k'], 2025: bt['members_ye2025_k'], 2026: bt['members_ye2026e_k']}
new = {y: ye[y] - RET * ye[y - 1] for y in (2023, 2024, 2025, 2026)}
young = {y: (new[y] + RET * new[y - 1]) / ye[y] for y in (2024, 2025, 2026)}
P('\nBridge backtest (same method: half-credit maturity, rate vs effective growth rate, half the prior second-half gap)')
for y, mprev, actual, h2 in ((2025, bt['mbr_2024_gaap'], bt['mbr_2025_gaap'], bt['h2_minus_fy_2024_pts']), (2026, bt['mbr_2025_adj'], bt['mbr_2026e_adj'], bt['h2_minus_fy_2025_pts'])):
    mat = 0.5 * (young[y] - young[y - 1]) * GAP
    rate = (bt[f'egr_{y}_pct'] - bt[f'rate_change_{y}_pct']) / 100 * mprev
    carry = 0.5 * h2 / 100
    pred = mat + rate + carry
    P(f"  {y}: maturity {100 * mat:+.2f}, rate vs trend {100 * rate:+.2f}, carry {100 * carry:+.2f} -> predicted {100 * pred:+.2f} pts vs actual {100 * (actual - mprev):+.2f} ({'2026 = guidance-based estimate' if y == 2026 else '10-K'})")
P(f"  Young-member share: 2024 {young[2024]:.0%}, 2025 {young[2025]:.0%}, 2026 {young[2026]:.0%}")

# ---- dilution and stock pay
sbc = rd('sbc_peers_2025.csv')
P('\nStock pay as a share of revenue, 2025: ' + ', '.join(f"{r['ticker']} {float(r['sbc_2025_musd']) / float(r['revenue_2025_musd']):.2%}" for r in sbc))
P(f"Weighted shares: Q2 2024 190.9m; Q2 2026 207.4m basic (+{207.448894 / 190.891787 - 1:.1%}), 215.0m diluted")

# ---- positioning and history
pos = kv('positioning_2026_10.csv')
P(f"\nPositioning: short interest {int(pos['short_interest_shares']) / 1e6:.1f}m shares ({float(pos['short_pct_float']):.1%} of float), {float(pos['days_to_cover']):.1f} days to cover, borrow {pos['borrow_fee_pct']}%; "
  f"{pos['analysts']} analysts, mean target ${pos['target_mean']} (median ${pos['target_median']}, range ${pos['target_low']}-${pos['target_high']}), ratings strong buy/buy/hold/sell {pos['ratings_strongbuy_buy_hold_sell']}")
P('Valuation history (EV = price x shares + debt - cash - short-term investments; next-year figures are actuals or my estimates):')
for r in rd('valuation_history.csv'):
    ev = float(r['price']) * float(r['shares_m']) + float(r['debt_musd']) - float(r['cash_musd']) - float(r['st_inv_musd'])
    e = r['next_year_adj_ebitda_musd']
    P(f"  {r['date']}: EV ${ev:,.0f}m; ${ev * 1e3 / float(r['members_k']):,.0f} a member; {ev / float(r['next_year_revenue_musd']):.2f}x next-year revenue" + (f"; {ev / float(e):.1f}x next-year adj. EBITDA" if e else ''))
P(f"  Now on EBITDA after stock pay, on the 215.0m diluted shares the target uses: EV ${PRICE * SH - (CASH - DEBT):,.0f}m, {(PRICE * SH - (CASH - DEBT)) / e_after(E27):.1f}x vs the peer median {MEV:.2f}x (basic shares: {(PRICE * 207.435149 + 324.056 - 693.453 - 8.258) / e_after(E27):.1f}x)")
P(f"  Gap from price to target: ${PRICE - PT:.2f}, of which the stars cost ${STARS:.2f} and the multiple ${PRICE - PT - STARS:.2f}")

# ---- the convertible: 4.25% is a convert coupon, not what straight debt would cost
KD_STRAIGHT = 0.08  # my assumption for an unrated insurer holding company; not a market quote
w_s = wE * (RF + betas['ALHC'][0] * ERP) + (1 - wE) * KD_STRAIGHT * (1 - TAX)
STARS_S = stars_cost(w_s)
P(f"\nConvert check: at an {KD_STRAIGHT:.0%} straight-debt cost the discount rate is {w_s:.2%} (vs {WACC:.2%}); stars cost ${STARS_S:.2f} (vs ${STARS:.2f}); "
  f"target ${PT + STARS - STARS_S:.2f}; DCF at 3% margin ${dcf(E27, 0.03, w_s):.2f}. Conversion price about $16.04, far above the stock, so the notes are debt.")

# ---- lawsuit odds: the stars cost above uses 25%
S8.V.RATE = WACC
def stars_at(p):
    c = 0.5 * S8.cost(p_win=p) + 0.25 * S8.cost(p_win=p, margin=0, margin_later=0) + 0.25 * S8.cost(p_win=p, margin=0, margin_later=0, growth_pts=0.10)
    return c * S8.V.shares / SH
sl = {p: stars_at(p) for p in (0.0, 0.25, 0.44, 0.5, 1.0)}
P("Stars cost by odds of winning the 2027-ratings case: " + ", ".join(f"{p:.0%} ${v:.2f}" for p, v in sl.items())
  + f"; a win is worth ${sl[0.0] - sl[1.0]:.2f}; target at the 44% base rate (rulings counted once) ${PT + STARS - sl[0.44]:.2f}, at 50% ${PT + STARS - sl[0.5]:.2f}")

# ---- comparable value at the 8 October close, before CMS released the ratings
d8 = {r['date']: r for r in rd('prices_daily_2026_09_08_to_10_21.csv')}['2026-10-08']
ev8 = {r['ticker']: (float(d8[r['ticker']]) * float(r['shares_m']) + float(r['net_debt_2025_musd'])) / float(r['ebitda_2027_cons_musd']) for r in peers}
M8 = float(np.median(list(ev8.values())))
v8 = (M8 * e_after(E27) - (DEBT - CASH)) / SH
P(f"8 Oct: peer median {M8:.2f}x, comparable value before any stars cost ${v8:.2f} vs the ${float(d8['ALHC']):.2f} close (premium ${float(d8['ALHC']) - v8:.2f}); "
  f"21 Oct: {MEV:.2f}x, ${PT + STARS:.2f} vs ${PRICE:.2f} (premium ${PRICE - PT - STARS:.2f})")

# ---- the Street, re-pulled 21 Oct
an = kv('analysts_2026_10_21.csv'); post = [float(an[k]) for k in an if k.startswith('post_stars_target')]
P(f"Street: {an['targets_count']} targets, mean ${float(an['target_mean']):.2f}, median ${float(an['target_median']):.0f}; {an['recommendations_strongbuy_buy_hold_sell']} strong buy/buy/hold/sell (14 recommendations); "
  f"the {len(post)} targets reset after the ratings average ${np.mean(post):.2f}")

with open(os.path.join(HERE, '..', 'results', 'price_target.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['line', 'value'])
    for k, v in (('price_target', PT), ('dcf_crosscheck', dcf_v), ('wacc', WACC), ('stars_cost', STARS), ('per_point', per_pt), ('mbr_equal_price', imp27)):
        w.writerow([k, round(v, 4)])
open(os.path.join(HERE, '..', 'results', 'price_target.txt'), 'w').write('\n'.join(out) + '\n')
