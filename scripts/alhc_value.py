# What the share price is paying for, and what I think the stars hit is worth per share.
# The bonus at stake comes from industry_table.py (KFF basis: benchmark lift x 65% rebate share, risk score 1.0,
# 2027 county rates standing in for 2028). The odds of the rating coming back come from hos_noise.py.
# The two judgement inputs are the 10% discount rate and the 30% lawsuit odds. Change them and rerun.
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_inputs.csv')))}

shares = x['shares_outstanding_2026_06_30'] / 1e6
p0, p1, now = x['price_close_2026_10_08'], x['price_close_2026_10_09'], x['price_close_2026_10_15']
mcap = now * shares
ev = mcap - x['cash_2026_06_30_musd'] + x['long_term_debt_2026_06_30_musd']
ebitda_mid = (x['fy26_adj_ebitda_low_musd'] + x['fy26_adj_ebitda_high_musd']) / 2
print(f"Market cap at ${now}: ${mcap:,.0f}m; EV ${ev:,.0f}m; EV / FY26 adj EBITDA midpoint ${ebitda_mid:.0f}m = {ev/ebitda_mid:.1f}x")
print(f"Oct 9 move: ${p1-p0:+.2f} a share = ${(p1-p0)*shares:,.0f}m; since Oct 8 close: ${now-p0:+.2f} = ${(now-p0)*shares:,.0f}m")

import sys; sys.path.insert(0, HERE)
import industry_table as T, hos_noise as N
BONUS_2028 = T.rows['H3815']['kff'] / 1e6    # $m, KFF basis
GROSS_2028 = T.rows['H3815']['usd'] / 1e6    # $m, gross benchmark lift
RATE = 0.10
P_LAWSUIT = 0.30          # judgement: odds a ruling restores 4.0 in time for 2028 bids
P_STAYS_LOW = 1 - N.p4    # from hos_noise.py: odds H3815 is still below 4.0 in the 2028 Star Ratings
GROWTH = 0.05

t28, t29 = 1.71, 2.71     # years from mid-Oct 2026 to mid-2028 and mid-2029
pv28 = BONUS_2028 / (1 + RATE) ** t28
pv29 = BONUS_2028 * (1 + GROWTH) / (1 + RATE) ** t29
ps28, ps29 = pv28 / shares, pv29 / shares
print("--- valuation ---")
print(f"2028 bonus at stake ${BONUS_2028:.1f}m (gross ${GROSS_2028:.1f}m) = ${BONUS_2028/shares:.2f} a share; present value ${pv28:.0f}m = ${ps28:.2f}")
print(f"A second lost year (2029) present value ${pv29:.0f}m = ${ps29:.2f} a share")
print(f"The drop since Oct 8 (${p0-now:.2f}) is {100*(p0-now)/ps28:.0f}% of one lost year in today's money")

value = p0 - (1 - P_LAWSUIT) * ps28 - P_STAYS_LOW * ps29
print(f"Expected value: ${p0} - {1-P_LAWSUIT:.0%} x ${ps28:.2f} - {P_STAYS_LOW:.0%} x ${ps29:.2f} = ${value:.2f} vs ${now} price")
cases = {
    'Win the case, rating recovers in 2028': p0,
    'Win the case, rating stays low': p0 - ps29,
    'Lose the case, rating recovers': p0 - ps28,
    'Lose the case, rating stays low': p0 - ps28 - ps29,
}
for k, v in cases.items():
    print(f"  {k}: ${v:.2f}")
for pl in (0.0, 0.15, 0.30, 0.45, 0.60):
    print(f"  lawsuit odds {pl:.0%}: ${p0 - (1-pl)*ps28 - P_STAYS_LOW*ps29:.2f}")
print(f"Lawsuit odds the price implies (holding the 34% stays-low odds): {100*(1 - (p0 - now - P_STAYS_LOW*ps29)/ps28):.0f}%")
with open(os.path.join(HERE, '..', 'results', 'alhc_value.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['case', 'value_per_share'])
    w.writerow(['expected', round(value, 2)]); [w.writerow([k, round(v, 2)]) for k, v in cases.items()]
