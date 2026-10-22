"""Alignment's 2027 benefits against every rival in the counties where it sells, weighted by members,
with general plans, chronic-condition SNPs and dual-eligible SNPs shown separately.
Input: data/benefits_alhc_counties_2027.csv (benefits_all_counties_extract.py).
Giveback is the Part B premium reduction a plan funds from its rebate, a revenue item; the allowance
(over-the-counter plus any combined supplemental benefit) is a benefit cost. Both are plan maximums, annualised.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, '..', 'data', 'benefits_alhc_counties_2027.csv'), dtype={'plan': str})
df['alhc'] = df.parent == 'Alignment Healthcare'
wa = lambda x, c: np.average(x[c], weights=x.members_oct2026) if x.members_oct2026.sum() > 0 else np.nan
out = []
P = lambda s: (print(s), out.append(s))
rows = []
for seg in ['General', 'C-SNP', 'D-SNP']:
    s = df[df.segment == seg]
    for lab, x in (('Alignment', s[s.alhc]), ('All rivals', s[~s.alhc])):
        rows.append({'segment': seg, 'who': lab, 'members': int(x.members_oct2026.sum()),
                     'giveback $/yr': round(wa(x, 'giveback_year')), 'allowance $/yr': round(wa(x, 'allowance_year')),
                     'MOOP $': round(wa(x[x.moop_in_network.notna()], 'moop_in_network'))})
    big = s[~s.alhc].groupby('parent').members_oct2026.sum().sort_values(ascending=False).head(5)
    for p in big.index:
        x = s[s.parent == p]
        rows.append({'segment': seg, 'who': p, 'members': int(x.members_oct2026.sum()),
                     'giveback $/yr': round(wa(x, 'giveback_year')), 'allowance $/yr': round(wa(x, 'allowance_year')),
                     'MOOP $': round(wa(x[x.moop_in_network.notna()], 'moop_in_network'))})
t = pd.DataFrame(rows)
pd.set_option('display.width', 220); pd.set_option('display.max_colwidth', 45)
P(t.to_string(index=False))
t.to_csv(os.path.join(HERE, '..', 'results', 'benefits_all_counties.csv'), index=False)
a = df[df.alhc]
P(f"Alignment members covered: {int(a.members_oct2026.sum()):,} of 301,157 in its contracts (Oct 2026); by segment " +
  ", ".join(f"{k} {int(v):,}" for k, v in a.groupby('segment').members_oct2026.sum().items()))
st = []
for s_, x in df[df.segment == 'General'].groupby('state'):
    al, ri = x[x.alhc], x[~x.alhc]
    st.append(f"{s_}: Alignment ${wa(al, 'giveback_year') + wa(al, 'allowance_year'):,.0f} vs rivals ${wa(ri, 'giveback_year') + wa(ri, 'allowance_year'):,.0f} (Alignment members {int(al.members_oct2026.sum()):,})")
P('General plans, giveback + allowance per member a year, by state: ' + '; '.join(st))
open(os.path.join(HERE, '..', 'results', 'benefits_all_counties.txt'), 'w').write('\n'.join(out) + '\n')
