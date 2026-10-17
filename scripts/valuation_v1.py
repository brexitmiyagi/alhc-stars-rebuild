"""Estimates, an independent 12-month price target, and what the price implies about medical costs.

House price-target method (the same one I would apply to any managed-care name):
  12-month target = average of
   (a) peer-median forward P/E x next-year adjusted EPS, tax-normalized to 24%, plus the value of the NOLs;
   (b) peer-median EV/EBITDA x next-year adjusted EBITDA, less net debt measured at the parent
       (convertible notes less parent cash, because most consolidated cash backs claims);
  then less any company-specific cost the next-year earnings do not yet carry (here the stars cost from
  value_v8.py, which falls mostly in 2028 and later).
  Peers: UNH, HUM, ELV, CVS, CNC, MOH, CI, multiples taken live on the day of writing (valuation_inputs.csv).

Estimates are mine. Every assumption is printed. Adjusted EPS here = adjusted EBITDA less D&A less interest,
no tax (Alignment has $617m of federal NOLs), which is how the consensus-implied EBITDA was built in ops_model.py.
"""
import os, sys, csv, io, contextlib, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); D = os.path.join(HERE, '..', 'data')
rd = lambda f: {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(D, f)))}
o, x, v = rd('alhc_operating_inputs.csv'), rd('alhc_inputs.csv'), rd('valuation_inputs.csv')
with contextlib.redirect_stdout(io.StringIO()):
    import value_v8 as V8
out = []
P = lambda s: (print(s), out.append(s))

PRICE = o['price_close_2026_10_16']; DIL = o['shares_diluted_q2_2026_m']; BASIC = x['shares_outstanding_2026_07_27'] / 1e6
DA26 = 2 * o['da_h1_2026_musd']; INT = 2 * o['interest_h1_2026_musd']
TAX, NOL_PV_FACTOR = 0.24, 0.79   # assumption: normalized tax rate; NOLs used over ~4 years, 10% discount
peers = ['UNH', 'HUM', 'ELV', 'CVS', 'CNC', 'MOH', 'CI']
PE = st.median(v[f'peer_{p}_pe_fwd2027'] for p in peers)
EVE = st.median(v[f'peer_{p}_ev_ebitda_ttm'] for p in peers)
nol_ps = v['federal_nol_musd'] * 0.21 * NOL_PV_FACTOR / DIL
net_debt_parent = o['convertible_notes_face_musd'] - o['cash_operating_parent_2026_06_30_musd']
stars = 0.5 * V8.cost() + 0.25 * V8.cost(margin=0, margin_later=0) + 0.25 * V8.cost(margin=0, margin_later=0, growth_pts=0.10)
P(f"Peer medians: forward P/E {PE:.1f}x, EV/EBITDA {EVE:.1f}x; NOL value ${nol_ps:.2f}/share; parent net debt ${net_debt_parent:.0f}m; stars cost (v8 blend, full) ${stars:.2f}/share")

# ---- 2026: history, guidance, my Q3/Q4 ----
h1_rev, h1_med = o['rev_h1_2026_musd'], o['med_h1_2026_musd']
q2_rev, q2_gp = o['rev_q2_2026_musd'], v['q2_2026_adj_gp_musd']
h1_gp = h1_rev - (h1_med - 4.0)            # GAAP medical includes ~$2m a quarter of equity comp and depreciation
P(f"H1 2026 adj. gross profit ~${h1_gp:.0f}m (MBR {1-h1_gp/h1_rev:.1%}); Q2 MBR {1-q2_gp/q2_rev:.1%}; Q1 ~{1-(h1_gp-q2_gp)/(h1_rev-q2_rev):.1%}")
q3g_rev = (o['guide_q3_2026_rev_low'] + o['guide_q3_2026_rev_high']) / 2
q3g_gp = (v['guide_q3_2026_adj_gp_low'] + v['guide_q3_2026_adj_gp_high']) / 2
q3g_e = (o['guide_q3_2026_ebitda_low'] + o['guide_q3_2026_ebitda_high']) / 2
q3_sga = q3g_gp - q3g_e
q25 = (v['q3_2025_rev_musd'], v['q3_2025_adj_gp_musd'], v['q3_2025_adj_ebitda_musd'])
# my Q3: costs ran hot into Jul-Aug (Baird, Sep 15) -> low end of the gross-profit guide, SG&A as guided
my_q3 = dict(rev=1310.0, gp=v['guide_q3_2026_adj_gp_low']); my_q3['e'] = my_q3['gp'] - q3_sga
eps = lambda e, da, it: (e - da - it) / DIL
P("\nQ3 2026                 Q3 2025 actual   Guidance (mid)    Consensus          Mine")
P(f"  Revenue $m            {q25[0]:8.0f}        {o['guide_q3_2026_rev_low']:.0f}-{o['guide_q3_2026_rev_high']:.0f}       {v['cons_q3_2026_rev_yahoo_musd']:8.0f}      {my_q3['rev']:8.0f}")
P(f"  MBR                   {1-q25[1]/q25[0]:8.1%}        {1-q3g_gp/q3g_rev:.1%}            n/a           {1-my_q3['gp']/my_q3['rev']:8.1%}")
P(f"  Adj. EBITDA $m        {q25[2]:8.1f}        {o['guide_q3_2026_ebitda_low']:.0f}-{o['guide_q3_2026_ebitda_high']:.0f}            n/a           {my_q3['e']:8.1f}")
P(f"  Adj. EPS              {0.0981:8.2f}        n/a              {v['cons_q3_2026_eps_yahoo']:8.3f}      {eps(my_q3['e'], DA26/4, INT/4):8.3f}")
fy26_e = o['adj_ebitda_h1_2026_musd'] + my_q3['e'] + 19.0     # Q4 ~ $19m: H2 ~30% of the year per management
fy26_rev = 5210.0
P(f"FY2026 mine: revenue ${fy26_rev:,.0f}m, adj. EBITDA ${fy26_e:.0f}m (guide 145-163), EPS {eps(fy26_e, DA26, INT):.2f} (consensus {v['cons_fy2026_eps_yahoo']:.2f} Yahoo / 0.48 S&P)")

# ---- 2027-2028 scenarios ----
SGA27 = 0.090      # assumption: 2026 adj. SG&A ~9.3% of revenue (guide midpoints: GP $640m less EBITDA $154m), some scale in 2027
REV27, G28 = 6500.0, 0.15   # assumptions: 2027 near consensus (~20% members + 4.98% rate); 2028 +15%
stars28 = 0.5 * 0.77 * (1 - 0.25) * V8.V.L35    # expected 2028 margin hit, blend of paths (B has none)
def scen(mbr):
    e27 = REV27 * (1 - mbr - SGA27)
    e28 = e27 * (1 + G28) - stars28
    eps27 = eps(e27, DA26 * 1.0, INT); eps28 = eps(e28, DA26 * 1.1, INT)
    pe_val = PE * eps27 * (1 - TAX) + nol_ps
    ev_val = (EVE * e27 - net_debt_parent) / DIL
    tgt = (pe_val + ev_val) / 2 - stars
    return dict(mbr=mbr, e27=e27, e28=e28, eps27=eps27, eps28=eps28, pe=pe_val, ev=ev_val, tgt=tgt)
S = {'Bear': scen(0.890), 'Base': scen(0.879), 'Bull': scen(0.870)}
P(f"\nAssumptions: 2027 revenue ${REV27:,.0f}m, adj. SG&A {SGA27:.1%} of revenue, 2028 revenue +{G28:.0%}, expected 2028 stars hit ${stars28:.0f}m")
P("Scenario  2027 MBR  2027 EBITDA  2027 EPS  2028 EBITDA  2028 EPS   P/E value  EV value  Target")
for k, s in S.items():
    P(f"{k:8s}  {s['mbr']:7.1%}  {s['e27']:10.0f}  {s['eps27']:8.2f}  {s['e28']:10.0f}  {s['eps28']:8.2f}   {s['pe']:8.2f}  {s['ev']:8.2f}  {s['tgt']:6.2f}")
P(f"Consensus 2027: revenue ${v['cons_fy2027_rev_yahoo_musd']:,.0f}m, EPS {v['cons_fy2027_eps_yahoo']:.2f} (Yahoo, 17 Oct) / 0.74 (S&P, 9 Oct)")
dT = (S['Base']['tgt'] - scen(0.889)['tgt'])
P(f"Each point of 2027 MBR moves 2027 EBITDA ${REV27*0.01:.0f}m and the target ${dT:.2f}")

# ---- what the price implies ----
lo, hi = 0.85, 0.92
for _ in range(60):
    mid = (lo + hi) / 2
    if scen(mid)['tgt'] > PRICE: lo = mid
    else: hi = mid
P(f"\nPrice-implied 2027 MBR under the house method: {mid:.1%} (my base {S['Base']['mbr']:.1%}; 2026 guide midpoint ~{1-640/5210:.1%}; H2 2026 implied ~{1-(640-h1_gp)/(5210-h1_rev):.1%})")
res_lo, res_hi = 12.94 - PRICE - V8.cost(), 12.94 - PRICE - V8.cost(margin=0, margin_later=0)
ev_now = PRICE * BASIC - o['cash_consolidated_2026_06_30_musd'] + o['convertible_notes_face_musd']
ev_sep = 12.94 * BASIC - o['cash_consolidated_2026_06_30_musd'] + o['convertible_notes_face_musd']
m_now, m_sep = ev_now / 154.0, ev_sep / 154.0
for lab, m in (('at today\'s', m_now), ('at the Sep 14', m_sep)):
    a, b = res_lo * BASIC / m, res_hi * BASIC / m
    P(f"Unexplained fall ${res_lo:.2f}-${res_hi:.2f}/share {lab} {m:.1f}x EV/EBITDA = ${a:.0f}-{b:.0f}m of EBITDA = {a/REV27:.1%}-{b/REV27:.1%} of 2027 revenue, i.e. that many points of MBR")
def implied(target, stars_sub):
    lo, hi = 0.80, 0.95
    for _ in range(60):
        m = (lo + hi) / 2
        if scen(m)['tgt'] + stars - stars_sub > target: lo = m
        else: hi = m
    return m
i_sep, i_now = implied(12.94, 0.31 * stars), implied(PRICE, stars)
P(f"At today's peer multiples the Sep 14 close ($12.94, with 31% odds of the stars cost) implied a 2027 MBR of {i_sep:.1%}; ${PRICE} with the full stars cost implies {i_now:.1%}: +{100*(i_now-i_sep):.1f} points")
open(os.path.join(HERE, '..', 'results', 'valuation_v1.txt'), 'w').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, '..', 'results', 'valuation_v1.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['scenario', 'mbr_2027', 'ebitda_2027', 'eps_2027', 'ebitda_2028', 'eps_2028', 'pe_value', 'ev_value', 'target'])
    for k, s in S.items(): w.writerow([k] + [round(s[c], 4) for c in ('mbr', 'e27', 'eps27', 'e28', 'eps28', 'pe', 'ev', 'tgt')])
