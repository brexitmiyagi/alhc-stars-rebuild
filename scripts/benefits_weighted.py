"""The 2027 benefit comparison weighted by the members who will hold each plan.

Each 2027 plan gets the October 2026 enrollment, county by county, of every 2026 plan CMS's crosswalk sends
into it. Brand-new 2027 plans have no members yet and get no weight. Counts under 11 are hidden by CMS and
left out. Same plan universe as benefits_2027.py: individual HMO, HMO-POS and local PPO plans with drug
coverage, no SNPs, no employer plans, Los Angeles and Orange County.
Inputs: data/pbp_2027_la_oc.csv, data/enrollment_2026_10_la_oc.csv, data/plan_crosswalk_2027_la_oc.csv.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, '..', 'data', f)
pbp = pd.read_csv(D('pbp_2027_la_oc.csv'), dtype={'plan': str, 'segment': str})
pbp['plan'] = pbp.plan.str.zfill(3)
enr = pd.read_csv(D('enrollment_2026_10_la_oc.csv'), dtype={'plan': str})
enr['plan'] = enr.plan.str.zfill(3)
cw = pd.read_csv(D('plan_crosswalk_2027_la_oc.csv'), dtype=str)
cw = cw[~cw.STATUS.str.contains('Terminated', na=False)]
cw['PREVIOUS_PLAN_ID'] = cw.PREVIOUS_PLAN_ID.str.zfill(3); cw['CURRENT_PLAN_ID'] = cw.CURRENT_PLAN_ID.str.zfill(3)
m = enr.merge(cw[['PREVIOUS_CONTRACT_ID', 'PREVIOUS_PLAN_ID', 'CURRENT_CONTRACT_ID', 'CURRENT_PLAN_ID']],
              left_on=['contract', 'plan'], right_on=['PREVIOUS_CONTRACT_ID', 'PREVIOUS_PLAN_ID'])
w = m.groupby(['CURRENT_CONTRACT_ID', 'CURRENT_PLAN_ID', 'county']).members_2026_10.sum().rename('members').reset_index()
# one segment per plan in this universe gets the plan's members; if a plan has several segments, split evenly
pbp = pbp.merge(w, left_on=['contract', 'plan', 'county'], right_on=['CURRENT_CONTRACT_ID', 'CURRENT_PLAN_ID', 'county'], how='left')
pbp['members'] = pbp.members.fillna(0) / pbp.groupby(['contract', 'plan', 'county']).segment.transform('count')

GROUPS = [('Alignment', r'^ALIGNMENT HEALTH'), ('UnitedHealth', r'^UHC OF CALIFORNIA'), ('Humana', r'^HUMANA'),
          ('SCAN', r'^SCAN HEALTH'), ('Kaiser', r'^KAISER'), ('Elevance', r'^BLUE CROSS OF CALIFORNIA'),
          ('CVS (Aetna)', r'^AETNA HEALTH OF CALIFORNIA'), ('Blue Shield', r"CALIFORNIA PHYSICIANS' SERVICE")]
pbp['group'] = None
for g, pat in GROUPS:
    pbp.loc[pbp.org_name.str.upper().str.contains(pat, regex=True) & pbp.group.isna(), 'group'] = g
df = pbp[pbp.group.notna()].copy()
df['giveback_year'] = df.partb_giveback_month * 12
df['allowance_year'] = df.otc_year + df.combined_allowance_year
wavg = lambda x, c: np.average(x[c], weights=x.members) if x.members.sum() > 0 else np.nan
rows = []
for g, x in df.groupby('group'):
    xm = x[x.moop_in_network.notna()]
    rows.append({'Parent': g, 'Members (Oct 2026, mapped to 2027 plans)': int(x.members.sum()),
                 'Members with a Part B giveback': round(100 * x.loc[x.partb_giveback_month > 0, 'members'].sum() / max(x.members.sum(), 1)),
                 'Giveback, $ a year per member': round(wavg(x, 'giveback_year')),
                 'OTC + flex allowance, $ a year per member': round(wavg(x, 'allowance_year')),
                 'In-network MOOP, member-weighted $': round(wavg(xm, 'moop_in_network')),
                 'Plans with no 2026 members (new)': int((x.members == 0).sum())})
t = pd.DataFrame(rows).set_index('Parent')
t = t.loc[['Alignment'] + sorted(i for i in t.index if i != 'Alignment')]
pd.set_option('display.width', 250)
print(t.to_string())
t.to_csv(os.path.join(HERE, '..', 'results', 'benefits_weighted_table.csv'))
a = df[df.group == 'Alignment']; o = df[df.group != 'Alignment']
ext = lambda x: (x.giveback_year + x.allowance_year)
lines = [f"Cash-like extras (giveback + allowance) per member a year: Alignment ${np.average(ext(a), weights=a.members):,.0f}, the other seven ${np.average(ext(o), weights=o.members):,.0f}",
         f"Alignment members in plans with a giveback: {100 * a.loc[a.partb_giveback_month > 0, 'members'].sum() / a.members.sum():.0f}%; others {100 * o.loc[o.partb_giveback_month > 0, 'members'].sum() / o.members.sum():.0f}%",
         f"Members covered by this table: Alignment {int(a.members.sum()):,}, others {int(o.members.sum()):,}"]
for l in lines: print(l)
open(os.path.join(HERE, '..', 'results', 'benefits_weighted.txt'), 'w').write(t.to_string() + '\n' + '\n'.join(lines) + '\n')
