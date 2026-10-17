# What 4 stars is worth to H3815 in dollars, three ways, and what the D.C. cases are worth together.
# County rates: CMS 2027 rate book (5% bonus rate minus 0% bonus rate), weighted by H3815's October 2026
# county enrollment. Risk score and rebates: CMS 2024 Plan Payment Data (Part C, plan level), weighted by
# July 2024 plan enrollment. Rebate shares: 65% at 3.5 to 4.0 stars, 70% at 4.5 and up (CMS rate announcement).
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')

rates = {r['contract']: r for r in csv.DictReader(open(os.path.join(DATA, 'contract_county_rates_2027.csv')))}
x = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(DATA, 'alhc_inputs.csv')))}
plans = list(csv.DictReader(open(os.path.join(DATA, 'h3815_plans_2024.csv'))))

members = x['h3815_enrollment_2026_10']
base = float(rates['H3815']['avg_rate_0pct'])
lift = float(rates['H3815']['avg_qbp_delta'])
w = sum(int(p['enrollment_jul_2024']) for p in plans)
rs = sum(int(p['enrollment_jul_2024']) * float(p['avg_part_c_risk_score_2024']) for p in plans) / w
rebate = sum(int(p['enrollment_jul_2024']) * float(p['avg_rebate_pmpm_2024']) for p in plans) / w

gross_rs1 = members * lift * 12 / 1e6
gross_rs = gross_rs1 * rs
cash = gross_rs * 0.65
print(f"H3815: {members:,.0f} members (Oct 2026); bonus lifts the county benchmark {lift:.2f} a member a month on a {base:.2f} base ({100*lift/base:.2f}%)")
print(f"2024 plan payment data: {len(plans)} plans, {w:,} members, risk score {rs:.4f}, rebate {rebate:.2f} a member a month")
print(f"Benchmark lift a year: ${gross_rs1:.1f}m at risk score 1.0, ${gross_rs:.1f}m at H3815's risk score")
print(f"Cash to the plan (65% rebate share of the risk-adjusted lift): ${cash:.1f}m a year")
qbp_rebate_pmpm = 0.65 * lift * rs
print(f"The bonus funds {qbp_rebate_pmpm:.2f} of the {rebate:.2f} monthly rebate, {100*qbp_rebate_pmpm/rebate:.0f}% of the extra-benefit budget")

# 2026 case (1:26-cv-02441): Alignment says H3815 would be 4.5 without the 10 measures, so a 70% rebate share in 2027.
up27 = rebate * (0.70 - 0.65) / 0.65 * members * 12 / 1e6
print(f"2026-ratings case: moving H3815 from a 65% to a 70% rebate share is worth about ${up27:.1f}m in 2027 (complaint: 'well over $50 million')")

ebitda_mid = (x['fy26_adj_ebitda_low_musd'] + x['fy26_adj_ebitda_high_musd']) / 2
print(f"Against 2026 adjusted EBITDA guidance midpoint ${ebitda_mid:.0f}m: cash hole is {100*cash/ebitda_mid:.0f}%, both cases together ${cash+up27:.0f}m = {100*(cash+up27)/ebitda_mid:.0f}%")

with open(os.path.join(HERE, '..', 'results', 'bonus_dollars.csv'), 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(['item', 'value'])
    for k, v in [('h3815_members_oct26', members), ('benchmark_lift_pmpm', round(lift, 2)), ('base_rate_pmpm', round(base, 2)),
                 ('risk_score_2024', round(rs, 4)), ('rebate_pmpm_2024', round(rebate, 2)), ('gross_rs1_musd', round(gross_rs1, 1)),
                 ('gross_at_rs_musd', round(gross_rs, 1)), ('cash_65pct_musd', round(cash, 1)), ('case_2026_upgrade_musd', round(up27, 1))]:
        wr.writerow([k, v])
