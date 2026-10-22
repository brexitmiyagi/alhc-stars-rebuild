"""Build the 2027 benefit comparison for every county where Alignment sells, with members attached.

Run: python benefits_all_counties_extract.py pbp-benefits-2027.zip cpsc_enrollment_2026_10.zip plan_crosswalk_2027.zip
Sources: CMS PBP Benefits 2027, Monthly Enrollment by Contract/Plan/State/County (October 2026), 2027 Plan Crosswalk.
Universe: every individual HMO, HMO-POS and local PPO plan with drug coverage sold in the 55 counties where
Alignment sells a 2027 individual plan; employer plans (plan IDs 800+) and 'No Rx' plans left out. Segments:
general plans, chronic-condition SNPs (C-SNP), dual-eligible SNPs (D-SNP); institutional SNPs left out.
Each 2027 plan-county gets the October 2026 members of the 2026 plans CMS's crosswalk carries into it.
Writes data/benefits_alhc_counties_2027.csv.
"""
import os, sys, io, zipfile
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
zp, ze, zc = (zipfile.ZipFile(p) for p in sys.argv[1:4])
rd = lambda z, n, **k: pd.read_csv(io.BytesIO(z.read(n)), dtype=str, encoding='latin-1', **k)
KEY = ['pbp_a_hnumber', 'pbp_a_plan_identifier', 'segment_id']
a = rd(zp, 'pbp_Section_A.txt', sep='\t', usecols=KEY + ['pbp_a_org_name', 'pbp_a_plan_name', 'pbp_a_plan_type', 'pbp_a_special_need_plan_type'])
area = rd(zp, 'PlanArea.txt', sep='\t', usecols=KEY + ['county', 'stcd', 'eghp_flag'])
area = area[area.eghp_flag == '0'].drop_duplicates(KEY + ['stcd', 'county'])
alhc = a[a.pbp_a_org_name.str.upper().str.startswith('ALIGNMENT HEALTH')]
counties = area.merge(alhc[KEY], on=KEY)[['stcd', 'county']].drop_duplicates()
df = area.merge(counties, on=['stcd', 'county']).merge(a, on=KEY)
df = df[df.pbp_a_plan_type.isin(['01', '02', '04']) & (pd.to_numeric(df.pbp_a_plan_identifier) < 800)
        & ~df.pbp_a_plan_name.str.contains('No Rx', case=False, na=False)
        & df.pbp_a_special_need_plan_type.fillna('G').isin(['G', '3', '4'])]
df['segment'] = df.pbp_a_special_need_plan_type.fillna('G').map({'G': 'General', '4': 'C-SNP', '3': 'D-SNP'})

d = rd(zp, 'pbp_Section_D.txt', sep='\t', usecols=KEY + ['pbp_d_mplusc_premium', 'pbp_d_mco_pay_reduct_amt', 'pbp_d_out_pocket_amt']
       + [f'pbp_d_combo_max_plan_ben_amt_{i}' for i in range(1, 6)] + [f'pbp_d_combo_max_plan_period_{i}' for i in range(1, 6)])
otc = rd(zp, 'pbp_b13_other_services.txt', sep='\t', usecols=KEY + ['pbp_b13b_maxplan_amt', 'pbp_b13b_otc_maxplan_per'])
df = df.merge(d, on=KEY, how='left').merge(otc, on=KEY, how='left')
PER = {'1': 1 / 3, '2': 0.5, '3': 1, '4': 2, '5': 4, '7': 12}
num = lambda s: pd.to_numeric(s, errors='coerce')
ann = lambda amt, per: num(amt) * per.map(PER).fillna(1)
df['giveback_year'] = num(df.pbp_d_mco_pay_reduct_amt).fillna(0) * 12
df['allowance_year'] = ann(df.pbp_b13b_maxplan_amt, df.pbp_b13b_otc_maxplan_per).fillna(0) + sum(
    ann(df[f'pbp_d_combo_max_plan_ben_amt_{i}'], df[f'pbp_d_combo_max_plan_period_{i}']).fillna(0) for i in range(1, 6))
df['premium_month'] = num(df.pbp_d_mplusc_premium).fillna(0)
df['moop'] = num(df.pbp_d_out_pocket_amt)
df['plan3'] = df.pbp_a_plan_identifier.str.zfill(3)

en_name = [n for n in ze.namelist() if 'Enrollment_Info' in n][0]; ci_name = [n for n in ze.namelist() if 'Contract_Info' in n][0]
enr = rd(ze, en_name)
enr = enr.merge(counties, left_on=['State', 'County'], right_on=['stcd', 'county'])
enr['members'] = pd.to_numeric(enr.Enrollment, errors='coerce')
enr['plan3'] = enr['Plan ID'].str.zfill(3)
cw = rd(zc, [n for n in zc.namelist() if n.endswith('.txt')][0], sep='\t')
cw = cw[~cw.STATUS.str.contains('Terminated', na=False)]
cw['prev3'] = cw.PREVIOUS_PLAN_ID.str.zfill(3); cw['cur3'] = cw.CURRENT_PLAN_ID.str.zfill(3)
m = enr.merge(cw, left_on=['Contract Number', 'plan3'], right_on=['PREVIOUS_CONTRACT_ID', 'prev3'])
w = m.groupby(['CURRENT_CONTRACT_ID', 'cur3', 'stcd', 'county']).members.sum().reset_index()
df = df.merge(w, left_on=['pbp_a_hnumber', 'plan3', 'stcd', 'county'], right_on=['CURRENT_CONTRACT_ID', 'cur3', 'stcd', 'county'], how='left')
df['members'] = df.members.fillna(0) / df.groupby(['pbp_a_hnumber', 'plan3', 'stcd', 'county']).segment_id.transform('count')

ci = rd(ze, ci_name)[['Contract ID', 'Parent Organization']].drop_duplicates('Contract ID')
df = df.merge(ci, left_on='pbp_a_hnumber', right_on='Contract ID', how='left')
df['parent'] = df['Parent Organization'].fillna(df.pbp_a_org_name)
df.loc[df.pbp_a_org_name.str.upper().str.startswith('ALIGNMENT HEALTH'), 'parent'] = 'Alignment Healthcare'
out = df[['pbp_a_hnumber', 'plan3', 'segment_id', 'stcd', 'county', 'segment', 'parent', 'pbp_a_plan_name', 'members', 'premium_month', 'giveback_year', 'allowance_year', 'moop']]
out.columns = ['contract', 'plan', 'segment_id', 'state', 'county', 'segment', 'parent', 'plan_name', 'members_oct2026', 'premium_month', 'giveback_year', 'allowance_year', 'moop_in_network']
out.to_csv(os.path.join(HERE, '..', 'data', 'benefits_alhc_counties_2027.csv'), index=False)
print(f"{len(counties)} counties, {len(out)} plan-county rows, {int(out.members_oct2026.sum()):,} members mapped")
