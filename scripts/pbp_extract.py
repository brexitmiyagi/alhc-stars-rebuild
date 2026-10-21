"""Pull the 2027 plan benefits I compare for Los Angeles and Orange County out of CMS's PBP Benefits 2027 zip.

Run: python pbp_extract.py /path/to/pbp-benefits-2027.zip
Source: https://www.cms.gov/files/zip/pbp-benefits-2027.zip (CMS "PBP Benefits-2027", posted 1 Oct 2026).
Writes data/pbp_2027_la_oc.csv: one row per plan segment and county, individual-market plans only
(no employer group plans, no special needs plans, no plans without drug coverage), with premium, Part B giveback, in-network MOOP,
over-the-counter allowance, dental limits and any combined-benefit allowance, all annualised.
"""
import os, sys, zipfile, io
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', 'pbp_2027_la_oc.csv')
z = zipfile.ZipFile(sys.argv[1])
rd = lambda name, cols=None: pd.read_csv(io.BytesIO(z.read(name)), sep='\t', dtype=str, encoding='latin-1', usecols=cols)
KEY = ['pbp_a_hnumber', 'pbp_a_plan_identifier', 'segment_id']

area = rd('PlanArea.txt')
area = area[(area.stcd == 'CA') & area.county.isin(['Los Angeles', 'Orange']) & (area.eghp_flag == '0')][KEY + ['county']]
a = rd('pbp_Section_A.txt', KEY + ['pbp_a_org_name', 'pbp_a_plan_name', 'pbp_a_plan_type', 'pbp_a_special_need_plan_type'])
d = rd('pbp_Section_D.txt', KEY + ['pbp_d_mplusc_premium', 'pbp_d_mco_pay_reduct_amt', 'pbp_d_out_pocket_amt']
       + [f'pbp_d_combo_max_plan_ben_amt_{i}' for i in range(1, 6)] + [f'pbp_d_combo_max_plan_period_{i}' for i in range(1, 6)])
otc = rd('pbp_b13_other_services.txt', KEY + ['pbp_b13b_maxplan_amt', 'pbp_b13b_otc_maxplan_per'])
den = rd('pbp_b16_dental.txt', KEY + ['pbp_b16b_maxplan_pv_amt', 'pbp_b16b_maxplan_pv_per', 'pbp_b16c_maxplan_cmp_type', 'pbp_b16c_maxplan_cmp_amt', 'pbp_b16c_maxplan_cmp_per'])

df = area.merge(a, on=KEY, how='left').merge(d, on=KEY, how='left').merge(otc, on=KEY, how='left').merge(den, on=KEY, how='left')
df = df[df.pbp_a_special_need_plan_type.isna() & df.pbp_a_plan_type.isin(['01', '02', '04'])]
# plan IDs 800 and up are employer group plans; 'No Rx' plans carry no Part D, so they are not like for like
df = df[(pd.to_numeric(df.pbp_a_plan_identifier) < 800) & ~df.pbp_a_plan_name.str.contains('No Rx', case=False, na=False)]

# periodicity codes from the CMS data dictionary: 1 every 3 years, 2 every 2 years, 3 every year,
# 4 every six months, 5 every three months, 7 every month (6 "other" is left unannualised)
PER = {'1': 1 / 3, '2': 0.5, '3': 1, '4': 2, '5': 4, '7': 12}
num = lambda s: pd.to_numeric(s, errors='coerce')
ann = lambda amt, per: num(amt) * per.map(PER).fillna(1)

out = pd.DataFrame({
    'contract': df.pbp_a_hnumber, 'plan': df.pbp_a_plan_identifier, 'segment': df.segment_id, 'county': df.county,
    'org_name': df.pbp_a_org_name, 'plan_name': df.pbp_a_plan_name, 'plan_type': df.pbp_a_plan_type,
    'premium_month': num(df.pbp_d_mplusc_premium).fillna(0),
    'partb_giveback_month': num(df.pbp_d_mco_pay_reduct_amt).fillna(0),
    'moop_in_network': num(df.pbp_d_out_pocket_amt),
    'otc_year': ann(df.pbp_b13b_maxplan_amt, df.pbp_b13b_otc_maxplan_per).fillna(0),
    'dental_preventive_year': ann(df.pbp_b16b_maxplan_pv_amt, df.pbp_b16b_maxplan_pv_per).fillna(0),
    'dental_comprehensive_year': ann(df.pbp_b16c_maxplan_cmp_amt, df.pbp_b16c_maxplan_cmp_per).where(df.pbp_b16c_maxplan_cmp_type != '1').fillna(0),
})
combo = sum(ann(df[f'pbp_d_combo_max_plan_ben_amt_{i}'], df[f'pbp_d_combo_max_plan_period_{i}']).fillna(0) for i in range(1, 6))
out['combined_allowance_year'] = combo.values
out = out.drop_duplicates(['contract', 'plan', 'segment', 'county'])
out.to_csv(OUT, index=False)
print(f"{len(out)} plan-county rows written to data/pbp_2027_la_oc.csv")
