"""Hospital use per Medicare Advantage member: takes the HCAI hospital-day counts and divides out enrollment growth.

The open objection to hcai_hospital_use.py is that MA hospital days in Los Angeles and Orange County rose because
MA enrollment rose, not because use per member rose. This script divides each region's matched-hospital MA days
and discharges by the MA enrollment of the same counties, from CMS's MA State/County Penetration files, using the
middle month of each quarter (August for Q3, November for Q4, February for Q1).

Limits, stated plainly: days are counted where the hospital sits, enrollment where the member lives, so cross-county
admissions blur the line (most of it washes out in a year-over-year ratio). The matched-hospital set does not cover
every hospital in a county, so the per-member level is not a true admission rate; only the change is used.
This is all MA plans in the region, not Alignment's members, and it says nothing about price.
Inputs: data/hcai_qfur_2024q3_2026q1.csv (hcai_extract.py) and data/ma_penetration_ca_2024_2026.csv
(CMS MA State/County Penetration, months 2024-08, 2024-11, 2025-02, 2025-08, 2025-11, 2026-02; California rows,
https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/ma-state/county-penetration).
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, '..', 'data', f)
h = pd.read_csv(D('hcai_qfur_2024q3_2026q1.csv'), dtype={'fac_no': str, 'year_qtr': str})
pen = pd.read_csv(D('ma_penetration_ca_2024_2026.csv'))
month = {'20243': '2024-08', '20244': '2024-11', '20251': '2025-02', '20253': '2025-08', '20254': '2025-11', '20261': '2026-02'}
b = pd.read_csv(D('benefits_alhc_counties_2027.csv'))
alc = set(b[(b.parent == 'Alignment Healthcare') & (b.state == 'CA')].county)
cuts = {
    'LA + Orange': lambda c: c in ('Los Angeles', 'Orange'),
    'Rest of California': lambda c: c not in ('Los Angeles', 'Orange'),
    "Alignment's CA counties": lambda c: c in alc,
    'Other CA counties': lambda c: c not in alc,
}
pairs = [('20243', '20253'), ('20244', '20254'), ('20251', '20261')]
rows = []
for a, b_ in pairs:
    x = h[h.year_qtr == a].set_index('fac_no'); y = h[h.year_qtr == b_].set_index('fac_no')
    both = x.index.intersection(y.index)
    for reg, f in cuts.items():
        idx = [i for i in both if f(x.loc[i, 'county_name']) and pd.notna(x.loc[i, 'day_mcar_mc']) and pd.notna(y.loc[i, 'day_mcar_mc'])]
        X, Y = x.loc[idx], y.loc[idx]
        ea = pen[(pen.month == month[a]) & pen.county.map(f)].ma_enrolled.sum()
        eb = pen[(pen.month == month[b_]) & pen.county.map(f)].ma_enrolled.sum()
        days_g = Y.day_mcar_mc.sum() / X.day_mcar_mc.sum() - 1
        dis_g = Y.dis_mcar_mc.sum() / X.dis_mcar_mc.sum() - 1
        enr_g = eb / ea - 1
        rows.append({'quarter': f"Q{b_[-1]} {b_[:4]} vs Q{a[-1]} {a[:4]}", 'region': reg, 'hospitals': len(idx),
                     'MA enrollees (mid-quarter)': int(eb), 'MA enrollment yoy %': round(100 * enr_g, 1),
                     'MA days yoy %': round(100 * days_g, 1),
                     'MA days per member yoy %': round(100 * ((1 + days_g) / (1 + enr_g) - 1), 1),
                     'MA discharges per member yoy %': round(100 * ((1 + dis_g) / (1 + enr_g) - 1), 1),
                     'MA days per 1,000 members (quarter)': round(1000 * Y.day_mcar_mc.sum() / eb, 1)})
t = pd.DataFrame(rows)
pd.set_option('display.width', 250)
print(t.to_string(index=False))
# gap: LA + Orange minus rest of California, per member
for q in t.quarter.unique():
    s = t[t.quarter == q].set_index('region')
    print(f"{q}: per-member days gap LA+OC minus rest of CA {s.loc['LA + Orange', 'MA days per member yoy %'] - s.loc['Rest of California', 'MA days per member yoy %']:+.1f} pts; "
          f"Alignment counties minus other {s.loc[chr(65)+'lignment' + chr(39) + 's CA counties', 'MA days per member yoy %'] - s.loc['Other CA counties', 'MA days per member yoy %']:+.1f} pts")
t.to_csv(os.path.join(HERE, '..', 'results', 'hcai_per_member.csv'), index=False)
open(os.path.join(HERE, '..', 'results', 'hcai_per_member.txt'), 'w').write(t.to_string(index=False) + '\n')
