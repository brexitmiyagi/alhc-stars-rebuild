"""Medicare Advantage hospital use in Los Angeles and Orange County, from HCAI's quarterly hospital filings.

Year-over-year change in Medicare Advantage (Medicare managed care) inpatient days and discharges, matched on the
same hospitals in both quarters, against traditional Medicare in the same hospitals and against the rest of the
state. Days per discharge is the length-of-stay read. This is hospital-reported use across all MA plans, not
Alignment's own claims, and it says nothing about price.
Input: data/hcai_qfur_2024q3_2026q1.csv (hcai_extract.py).
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, '..', 'data', 'hcai_qfur_2024q3_2026q1.csv'), dtype={'fac_no': str, 'year_qtr': str})
df['region'] = df.county_name.where(df.county_name.isin(['Los Angeles', 'Orange']), 'Rest of California')
df['region'] = df.region.replace({'Los Angeles': 'LA + Orange', 'Orange': 'LA + Orange'})
pairs = [('20243', '20253'), ('20244', '20254'), ('20251', '20261')]
rows = []
for a, b in pairs:
    x = df[df.year_qtr == a].set_index('fac_no'); y = df[df.year_qtr == b].set_index('fac_no')
    both = x.index.intersection(y.index)
    for reg in ['LA + Orange', 'Rest of California']:
        idx = [i for i in both if x.loc[i, 'region'] == reg and pd.notna(x.loc[i, 'day_mcar_mc']) and pd.notna(y.loc[i, 'day_mcar_mc'])]
        X, Y = x.loc[idx], y.loc[idx]
        g = lambda c: (Y[c].sum() / X[c].sum() - 1) * 100
        rows.append({'quarter': f"Q{b[-1]} {b[:4]} vs Q{a[-1]} {a[:4]}", 'region': reg, 'hospitals': len(idx),
                     'MA days yoy %': round(g('day_mcar_mc'), 1), 'MA discharges yoy %': round(g('dis_mcar_mc'), 1),
                     'MA days per discharge': round(Y.day_mcar_mc.sum() / Y.dis_mcar_mc.sum(), 2),
                     'MA days per discharge a year earlier': round(X.day_mcar_mc.sum() / X.dis_mcar_mc.sum(), 2),
                     'Traditional Medicare days yoy %': round(g('day_mcar'), 1),
                     'MA share of Medicare days %': round(100 * Y.day_mcar_mc.sum() / (Y.day_mcar_mc.sum() + Y.day_mcar.sum()), 1)})
# second cut: every California county where Alignment sells a 2027 plan against the rest of the state
b = pd.read_csv(os.path.join(HERE, '..', 'data', 'benefits_alhc_counties_2027.csv'))
alc = set(b[(b.parent == 'Alignment Healthcare') & (b.state == 'CA')].county)
df['region2'] = df.county_name.apply(lambda c: "Alignment's CA counties" if c in alc else 'Other CA counties')
for a, b_ in pairs:
    x = df[df.year_qtr == a].set_index('fac_no'); y = df[df.year_qtr == b_].set_index('fac_no')
    both = x.index.intersection(y.index)
    for reg in ["Alignment's CA counties", 'Other CA counties']:
        idx = [i for i in both if x.loc[i, 'region2'] == reg and pd.notna(x.loc[i, 'day_mcar_mc']) and pd.notna(y.loc[i, 'day_mcar_mc'])]
        X, Y = x.loc[idx], y.loc[idx]
        g = lambda c: (Y[c].sum() / X[c].sum() - 1) * 100
        rows.append({'quarter': f"Q{b_[-1]} {b_[:4]} vs Q{a[-1]} {a[:4]}", 'region': reg, 'hospitals': len(idx),
                     'MA days yoy %': round(g('day_mcar_mc'), 1), 'MA discharges yoy %': round(g('dis_mcar_mc'), 1),
                     'MA days per discharge': round(Y.day_mcar_mc.sum() / Y.dis_mcar_mc.sum(), 2),
                     'MA days per discharge a year earlier': round(X.day_mcar_mc.sum() / X.dis_mcar_mc.sum(), 2),
                     'Traditional Medicare days yoy %': round(g('day_mcar'), 1),
                     'MA share of Medicare days %': round(100 * Y.day_mcar_mc.sum() / (Y.day_mcar_mc.sum() + Y.day_mcar.sum()), 1)})
t = pd.DataFrame(rows)
pd.set_option('display.width', 250)
print(t.to_string(index=False))
t.to_csv(os.path.join(HERE, '..', 'results', 'hcai_hospital_use.csv'), index=False)
open(os.path.join(HERE, '..', 'results', 'hcai_hospital_use.txt'), 'w').write(t.to_string(index=False) + '\n')
