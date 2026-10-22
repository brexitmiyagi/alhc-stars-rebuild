"""Is Alignment's reserve release unusual? Prior-year development as a share of revenue, Alignment against
UnitedHealth, Humana, Centene, Molina and Elevance, 2024 and 2025, all on the reported basis.
Also stock pay as a share of EBITDA, Alignment against the peers. Inputs in data/.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, '..', 'data', f)
r = pd.read_csv(D('peer_reserves_2024_2025.csv'))
r['release_pct_revenue'] = (-r.prior_year_development_musd / r.revenue_musd * 100).round(2)
t = r.pivot(index='ticker', columns='year', values='release_pct_revenue')
print('Favorable prior-year development, % of revenue (reported basis):'); print(t.to_string())
peers = t.drop('ALHC')
lines = [f"2025: Alignment {t.loc['ALHC', 2025]:.2f}% vs peer median {peers[2025].median():.2f}% (range {peers[2025].min():.2f}-{peers[2025].max():.2f}); 2024: {t.loc['ALHC', 2024]:.2f}% vs {peers[2024].median():.2f}%",
         "Alignment H1 2026 reported: $17.8m favorable on $2,570.8m revenue (0.69%); ex-PAD: $1.8m (0.07%)"]
s = pd.read_csv(D('sbc_peers_2025.csv')).set_index('ticker')
c = pd.read_csv(D('peers_consensus_2026_10.csv')).set_index('ticker')
share = {t_: s.loc[t_, 'sbc_2025_musd'] / c.loc[t_, 'ebitda_2027_cons_musd'] * 100 for t_ in s.index if t_ != 'ALHC' and t_ in c.index}
lines.append(f"Stock pay as a share of EBITDA: Alignment 2027E 37.1% ($76.3m of $205.6m adjusted EBITDA); peers, 2025 stock pay over 2027 consensus EBITDA: " +
             ", ".join(f"{k} {v:.1f}%" for k, v in share.items()) + f" (median {np.median(list(share.values())):.1f}%)")
for l in lines: print(l)
open(os.path.join(HERE, '..', 'results', 'peer_reserves.txt'), 'w').write(t.to_string() + '\n' + '\n'.join(lines) + '\n')
