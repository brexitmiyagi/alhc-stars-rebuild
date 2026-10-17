"""The company around the stars: a lean operating view, the Q3 set-up, usable cash, and multiples.
Every input is in data/alhc_operating_inputs.csv with its source. Anything labelled 'implied' is my
arithmetic on consensus, not a reported number."""
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__))
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'alhc_operating_inputs.csv')))}
y = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'alhc_inputs.csv')))}

price = x['price_close_2026_10_16']; shares = y['shares_outstanding_2026_07_27'] / 1e6
mcap = price * shares
ev = mcap - x['cash_consolidated_2026_06_30_musd'] + x['convertible_notes_face_musd']
ttm_rev = x['rev_h1_2026_musd'] + (x['rev_fy2025_musd'] - x['rev_h1_2025_musd'])
g26 = (x['guide_fy2026_rev_low'] + x['guide_fy2026_rev_high']) / 2
e26 = (x['guide_fy2026_ebitda_low'] + x['guide_fy2026_ebitda_high']) / 2
# 2027 adjusted EBITDA implied by consensus adjusted EPS: add back interest and D&A at the H1 2026 run rate; tax ~0 (NOLs)
ni27 = x['consensus_eps_2027'] * x['shares_diluted_q2_2026_m']
e27 = ni27 + 2 * x['interest_h1_2026_musd'] + 2 * x['da_h1_2026_musd']
print(f"Price ${price}; market value ${mcap:,.0f}m; EV ${ev:,.0f}m (cash ${x['cash_consolidated_2026_06_30_musd']:.0f}m, convertible notes ${x['convertible_notes_face_musd']:.0f}m)")
print(f"Revenue: TTM to June 2026 ${ttm_rev:,.0f}m; 2026 guidance midpoint ${g26:,.0f}m; 2027 consensus ${x['consensus_rev_2027_musd']:,.0f}m (+{x['consensus_rev_2027_musd']/g26-1:.0%})")
print(f"Adjusted EBITDA: 2026 guidance midpoint ${e26:.0f}m ({e26/g26:.1%} margin); 2027 implied by consensus EPS ${e27:.0f}m ({e27/x['consensus_rev_2027_musd']:.1%})")
print(f"EV / TTM sales {ev/ttm_rev:.2f}x (Humana {x['hum_ev_to_sales_ttm']:.2f}x, Clover {x['clov_ev_to_sales_ttm']:.2f}x); EV / 2026 adj. EBITDA {ev/e26:.1f}x; EV / 2027 implied {ev/e27:.1f}x")
loss_full = 133.6 * 0.74
loss_exp = loss_full * 0.75
print(f"Stars hit to 2028 margin at the measured 74% share: ${loss_full:.0f}m if the cases lose (${loss_exp:.0f}m expected at 25% win odds) = {loss_full/e27:.0%} / {loss_exp/e27:.0%} of 2027 implied EBITDA")

print("\nQ3 set-up")
q3l, q3h = x['guide_q3_2026_rev_low'], x['guide_q3_2026_rev_high']
print(f"Q3 revenue guide ${q3l:.0f}-{q3h:.0f}m = +{q3l/x['rev_q3_2025_musd']-1:.0%} to +{q3h/x['rev_q3_2025_musd']-1:.0%} y/y; adj. EBITDA guide ${x['guide_q3_2026_ebitda_low']:.0f}-{x['guide_q3_2026_ebitda_high']:.0f}m")
h2 = (x['guide_fy2026_ebitda_low'] - x['adj_ebitda_h1_2026_musd'], x['guide_fy2026_ebitda_high'] - x['adj_ebitda_h1_2026_musd'])
print(f"Full-year guide leaves ${h2[0]:.0f}-{h2[1]:.0f}m of adj. EBITDA for H2 after ${x['adj_ebitda_h1_2026_musd']:.0f}m in H1")
q1med = x['med_h1_2026_musd'] - x['med_q2_2026_musd']; q1med25 = x['med_h1_2025_musd'] - x['med_q2_2025_musd']
dcp = lambda mep, med, days: mep / (med / days)
print(f"Days claims payable: Q1'25 {dcp(x['mep_2025_03_31_musd'], q1med25, 90):.1f}, Q2'25 {dcp(x['mep_2025_06_30_musd'], x['med_q2_2025_musd'], 91):.1f}, Q1'26 {dcp(x['mep_2026_03_31_musd'], q1med, 90):.1f}, Q2'26 {dcp(x['mep_2026_06_30_musd'], x['med_q2_2026_musd'], 91):.1f}")
print(f"Claims incurred but not paid: ${x['ibnr_2025_06_30_musd']:.0f}m (Jun 25) -> ${x['ibnr_2025_12_31_musd']:.0f}m (Dec 25) -> ${x['ibnr_2026_06_30_musd']:.0f}m (Jun 26); as days of quarterly medical cost: {x['ibnr_2025_06_30_musd']/(x['med_q2_2025_musd']/91):.1f} -> {x['ibnr_2026_06_30_musd']/(x['med_q2_2026_musd']/91):.1f}")
print(f"Prior-year reserve development: Q2'26 ${x['pyd_q2_2026_musd']:.1f}m (unfavorable), H1'26 +${x['pyd_h1_2026_musd']:.1f}m")

print("\nCash the parent can use")
print(f"Consolidated cash and short-term investments ${x['cash_and_st_inv_2026_06_30_musd']:.1f}m; at the operating parent ${x['cash_operating_parent_2026_06_30_musd']:.1f}m; dividendable without approval at end-2025 ${x['dividendable_wo_approval_2025_12_31_musd']:.1f}m; convertible notes ${x['convertible_notes_face_musd']:.0f}m due Nov 2029")
ev_parent = mcap - x['cash_operating_parent_2026_06_30_musd'] + x['convertible_notes_face_musd']
print(f"EV counting only parent cash: ${ev_parent:,.0f}m = {ev_parent/e26:.1f}x 2026 adj. EBITDA")
