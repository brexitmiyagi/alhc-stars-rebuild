"""Operating bridge, parent liquidity against the 2029 convertible, and peer read-through.
Every input is in data/alhc_operating_inputs.csv or data/alhc_inputs.csv with its source.
'Implied' means my arithmetic on consensus or guidance, not a reported number."""
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'data')
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(D, 'alhc_operating_inputs.csv')))}
y = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(D, 'alhc_inputs.csv')))}
out = []
P = lambda s: (print(s), out.append(s))

price = x['price_close_2026_10_16']; shares = y['shares_outstanding_2026_07_27'] / 1e6
r26 = (x['guide_fy2026_rev_low'] + x['guide_fy2026_rev_high']) / 2
e26 = (x['guide_fy2026_ebitda_low'] + x['guide_fy2026_ebitda_high']) / 2
m26 = (x['guide_fy2026_members_low'] + x['guide_fy2026_members_high']) / 2
r27 = x['consensus_rev_2027_musd']
e27 = x['consensus_eps_2027'] * x['shares_diluted_q2_2026_m'] + 2 * x['interest_h1_2026_musd'] + 2 * x['da_h1_2026_musd']
rate = x['rate_notice_2027_with_risk_trend_pct'] / 100
vol = (r27 / r26) / (1 + rate) - 1
P("Operating bridge")
P(f"  2026 guidance midpoint: revenue ${r26:,.0f}m, adj. EBITDA ${e26:.0f}m ({e26/r26:.1%}), year-end members {m26:,.0f}")
P(f"  2027 consensus: revenue ${r27:,.0f}m (+{r27/r26-1:.0%}); implied adj. EBITDA ${e27:.0f}m ({e27/r27:.1%})")
P(f"  2027 rate notice +{rate:.2%} including risk trend (+{x['rate_notice_2027_net_pct']:.2f}% without), so ~{vol:.0%} of 2027 revenue growth has to come from members and mix")
reb = 133.6
P(f"  2028 stars line, H3815 at 3.5 stars, lawsuit lost: A industry pattern -${0.77*reb:.0f}m margin (expected at 25% win odds -${0.77*0.75*reb:.0f}m); B Alignment pattern ~-$6m (growth only)")
P(f"  2028 stars line as a share of 2027 implied EBITDA: A {0.77*reb/e27:.0%} full / {0.77*0.75*reb/e27:.0%} expected")

P("\nParent liquidity against the convertible")
face, cpn = x['convertible_notes_face_musd'], x['convert_coupon_pct'] / 100
pc, divd = x['cash_operating_parent_2026_06_30_musd'], x['dividendable_wo_approval_2025_12_31_musd']
coupons = 7 * face * cpn / 2   # Nov 2026 to Nov 2029 inclusive
P(f"  Notes ${face:.0f}m at {cpn:.2%}, due Nov 15 {int(x['convert_maturity_year'])}; coupon ${face*cpn:.1f}m a year; 7 coupons left from Nov 2026 = ${coupons:.1f}m")
P(f"  Conversion price ${x['convert_conversion_price']:.2f} vs ${price} = {x['convert_conversion_price']/price-1:.0%} above the stock; the notes are debt in practice")
P(f"  Parent cash Jun 30 ${pc:.1f}m; payable from subsidiaries without approval at end-2025 ${divd:.1f}m; together ${pc+divd:.0f}m vs ${face+coupons:.0f}m of principal and coupons")
P(f"  Gross debt / 2026 adj. EBITDA {face/e26:.1f}x; / (2027 implied less full A-path stars hit) {face/(e27-0.77*reb):.1f}x")
ev = price * shares - x['cash_consolidated_2026_06_30_musd'] + face
evp = price * shares - pc + face
P(f"  EV ${ev:,.0f}m ({ev/e26:.1f}x 2026, {ev/e27:.1f}x 2027 implied); on parent cash only ${evp:,.0f}m ({evp/e26:.1f}x, {evp/e27:.1f}x)")

P("\nPeer read-through before Alignment's Oct 29 print")
P(f"  UNH Q3 (Oct 13): MCR {x['unh_q3_2026_mcr_pct']}% vs {x['unh_q3_2025_mcr_pct']}% a year earlier; ${x['unh_q3_2026_pyd_musd']:.0f}m favorable development on 2026 claims; MA members {x['unh_ma_members_q3_2026_k']-x['unh_ma_members_ye2025_k']:+.0f}k since year-end in the people-served table ({x['unh_ma_members_change_since_ye2025_k']:+.0f}k including Medicaid-linked programs)")
P("  Elevance Oct 21 and Centene Oct 27 (dates from secondary calendars); Humana Nov 6 (company release), Humana affirmed 2026 guidance on Oct 9")
open(os.path.join(HERE, '..', 'results', 'ops_model_v6.txt'), 'w').write('\n'.join(out) + '\n')
