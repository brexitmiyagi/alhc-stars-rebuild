"""How rich are Alignment's 2027 plans in Los Angeles and Orange County next to the big rivals?

Reads data/pbp_2027_la_oc.csv (built by pbp_extract.py from CMS's PBP Benefits 2027 file).
Individual-market HMO, HMO-POS and local PPO plans, no SNPs, no employer plans. Plans are counted equally
(CMS does not publish plan-level enrollment in this file), so this is what is on the shelf, not what was bought.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, '..', 'data', 'pbp_2027_la_oc.csv'), dtype={'plan': str, 'segment': str})
GROUPS = [('Alignment', r'^ALIGNMENT HEALTH'), ('UnitedHealth', r'^UHC OF CALIFORNIA'), ('Humana', r'^HUMANA'),
          ('SCAN', r'^SCAN HEALTH'), ('Kaiser', r'^KAISER'), ('Elevance', r'^BLUE CROSS OF CALIFORNIA'),
          ('CVS', r'^AETNA HEALTH OF CALIFORNIA'), ('Blue Shield', r"CALIFORNIA PHYSICIANS' SERVICE")]
df['group'] = None
for g, pat in GROUPS:
    df.loc[df.org_name.str.upper().str.contains(pat, regex=True) & df.group.isna(), 'group'] = g
df = df[df.group.notna()].copy()
df['allowance_year'] = df.otc_year + df.combined_allowance_year
df['giveback_year'] = df.partb_giveback_month * 12
df['zero_premium'] = df.premium_month == 0

rows = []
for (g, c), x in df.groupby(['group', 'county']):
    rows.append(dict(group=g, county=c, plans=len(x), zero_premium_share=round(x.zero_premium.mean(), 2),
                     median_premium=x.premium_month.median(), giveback_share=round((x.partb_giveback_month > 0).mean(), 2),
                     median_giveback_year=x.giveback_year.median(), max_giveback_year=x.giveback_year.max(),
                     median_moop=x.moop_in_network.median(), median_allowance_year=x.allowance_year.median(),
                     median_dental_year=(x.dental_preventive_year + x.dental_comprehensive_year).median()))
t = pd.DataFrame(rows).sort_values(['county', 'group'])
pd.set_option('display.width', 200)
print(t.to_string(index=False))
t.to_csv(os.path.join(HERE, '..', 'results', 'benefits_2027_la_oc.csv'), index=False)

# Alignment against the plan-count-weighted field of the other seven, both counties together
a = df[df.group == 'Alignment']; o = df[df.group != 'Alignment']
for col, lab in (('giveback_year', 'Part B giveback a year'), ('allowance_year', 'OTC plus flexible allowance a year'),
                 ('moop_in_network', 'in-network MOOP'), ('premium_month', 'monthly premium')):
    print(f"{lab}: Alignment median ${a[col].median():,.0f} (mean ${a[col].mean():,.0f}), rivals median ${o[col].median():,.0f} (mean ${o[col].mean():,.0f})")
print(f"Plans with a Part B giveback: Alignment {(a.partb_giveback_month > 0).mean():.0%}, rivals {(o.partb_giveback_month > 0).mean():.0%}")
print(f"Alignment plans: {len(a)} plan-county rows; rivals {len(o)}")

# pooled table for the chart: both counties together, each plan-county offering counted once
g = df.groupby('group')
tab = pd.DataFrame({'Plans (LA + Orange)': g.size(),
                    'With a Part B giveback': (g.partb_giveback_month.apply(lambda s: (s > 0).mean()) * 100).round(0),
                    'Avg giveback, $ a year': g.giveback_year.mean().round(0),
                    'Median OTC + flex allowance, $ a year': g.allowance_year.median().round(0),
                    'Median in-network MOOP, $': g.moop_in_network.median().round(0)})
order = ['Alignment'] + sorted([x for x in tab.index if x != 'Alignment'])
tab = tab.loc[order]
print(tab.to_string())
tab.to_csv(os.path.join(HERE, '..', 'results', 'benefits_2027_table.csv'))
