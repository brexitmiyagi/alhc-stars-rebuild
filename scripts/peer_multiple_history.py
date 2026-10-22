"""The primary method run on every close since 8 September, to show how much of the target is the day's peer multiple.

Same inputs as price_target.py (peer shares, 2025 net debt and 2027 consensus EBITDA from
data/peers_consensus_2026_10.csv; Alignment's 2027 EBITDA after stock pay, net cash, 215.0m diluted shares and the
stars cost from results/price_target.txt), with only the peer prices changing day by day. Set ASOF as in
price_target.py to include later closes. Inputs are read back at the precision printed there, so a day's value
can differ from price_target.py by a cent ($7.18 here against $7.17 on 21 October).
"""
import os, re, csv
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, '..', 'data', f)
ASOF = os.environ.get('ASOF', '2026-10-21')
peers = [r for r in csv.DictReader(open(D('peers_consensus_2026_10.csv'))) if r['ticker'] != 'ALHC']
days = list(csv.DictReader(open(D(f"prices_daily_2026_09_08_to_{ASOF[5:].replace('-', '_')}.csv"))))
pt = open(os.path.join(HERE, '..', 'results', 'price_target.txt')).read()
E_AFTER = float(re.search(r'after stock pay \$([\d.]+)m, net cash', pt).group(1))
NET_CASH = float(re.search(r'net cash \$([\d.]+)m', pt).group(1))
STARS = float(re.search(r'Stars cost per diluted share: \$([\d.]+)', pt).group(1))
SH = 215.024483

out = []
P = lambda s: (print(s), out.append(s))
rows = []
for d in days:
    m = float(np.median([(float(d[r['ticker']]) * float(r['shares_m']) + float(r['net_debt_2025_musd'])) / float(r['ebitda_2027_cons_musd']) for r in peers]))
    rows.append((d['date'], m, (m * E_AFTER + NET_CASH) / SH - STARS, float(d['ALHC'])))
for r in rows:
    P(f"{r[0]}: peer median {r[1]:.2f}x, value after the stars cost ${r[2]:.2f}, Alignment ${r[3]:.2f}")
ms, vs = [r[1] for r in rows], [r[2] for r in rows]
last20 = rows[-20:]
P(f"\n{len(rows)} closes, {rows[0][0]} to {rows[-1][0]}: peer multiple {min(ms):.2f}x to {max(ms):.2f}x (median {np.median(ms):.2f}x); value ${min(vs):.2f} to ${max(vs):.2f} (median ${np.median(vs):.2f})")
P(f"Last 20 closes: median multiple {np.median([r[1] for r in last20]):.2f}x, value ${np.median([r[2] for r in last20]):.2f}")
P(f"Closes where the value was below Alignment's price: {sum(r[2] < r[3] for r in rows)} of {len(rows)}; latest multiple's rank: {sorted(ms).index(rows[-1][1]) + 1} of {len(ms)} (1 = lowest)")
open(os.path.join(HERE, '..', 'results', 'peer_multiple_history.txt'), 'w').write('\n'.join(out) + '\n')
