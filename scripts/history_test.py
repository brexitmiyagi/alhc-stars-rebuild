"""History test: what happened when a listed insurer lost a big slice of its 4-star enrollment.

Events: listed parents whose enrollment-weighted share of members in 4+ star contracts fell by 10 points or
more in one ratings release, 2020-2025 ratings (so 12 months of prices exist afterwards). Parent mapping uses
CMS's October 2026 contract file, so contracts that changed hands are attributed to today's owner.
Prices: Yahoo Finance chart API, adjusted closes, pulled 17 Oct 2026 (data/stars_cut_events.csv).
Window: close before the first news (CMS release, or earlier company/Plan Finder news) to the close one
trading day after CMS's release. Drift: from that close to +126 and +252 trading days.
Excess = firm return less an equal-weight basket of the other listed MA insurers (UNH, HUM, CVS, ELV, CNC,
MOH, CI). CMS release dates: CMS fact sheets (Oct 8 2020, Oct 6 2022, Oct 13 2023, Oct 10 2024); Oct 9 2019
from Avalere's citation of the CMS fact sheet. Humana's first news: Oct 1 2024 (Plan Finder data), 8-K Oct 2.
"""
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'data')
par = {r['Contract Number']: r['Parent Organization'] for r in csv.DictReader(open(os.path.join(D, 'enrollment_by_contract_2026_10.csv'), encoding='latin-1'))}
T = {'UnitedHealth Group, Inc.': 'UNH', 'Humana Inc.': 'HUM', 'CVS Health Corporation': 'CVS', 'Elevance Health, Inc.': 'ELV',
     'Elevance Health, Inc. & BCBSMA & BCBSRI & BCBSVT': 'ELV', 'Centene Corporation': 'CNC', 'Molina Healthcare, Inc.': 'MOH',
     'Clover Health Holdings, Inc.': 'CLOV', 'Alignment Healthcare USA, LLC': 'ALHC'}
rows = list(csv.DictReader(open(os.path.join(D, 'stars_and_enrollment_2019_2027.csv'))))
f = lambda v: float(v) if v not in ('', None) else None
def share(tk, Y):
    W = a = b = 0
    for r in rows:
        if T.get(par.get(r['contract'])) != tk: continue
        w, s, s0 = f(r[f'enroll_feb_{Y-1}']), f(r[f'stars_{Y}']), f(r[f'stars_{Y-1}'])
        if not w or s is None or s0 is None: continue
        W += w; a += w * (s0 >= 4); b += w * (s >= 4)
    return 100 * a / W, 100 * b / W
ev = list(csv.DictReader(open(os.path.join(D, 'stars_cut_events.csv'))))
out = []
P = lambda s: (print(s), out.append(s))
P(f"{'event':10s} {'4+ share':>13s} {'next yr':>7s} {'window xs':>9s} {'6m xs':>7s} {'12m xs':>7s}")
for e in ev:
    tk, Y = e['ticker'], int(e['ratings_year'])
    a, b = share(tk, Y)
    nxt = f"{share(tk, Y+1)[1]:.0f}%" if Y < 2027 else '-'
    P(f"{tk} {Y:<5d} {a:5.0f}%->{b:3.0f}%  {nxt:>7s} {float(e['excess_win']):+8.1f}% {e['excess_6m'] or '-':>7s} {e['excess_12m'] or '-':>7s}")
# CVS: market value lost vs the one-year hit it later disclosed
sh = 1312828807  # CVS 10-Q cover, 27 Jul 2022 (SEC XBRL dei:EntityCommonStockSharesOutstanding)
cv = [e for e in ev if e['ticker'] == 'CVS'][0]
raw = (float(cv['close_d0']) - float(cv['close_d1'])) * sh / 1e9
adj = -float(cv['excess_win']) / 100 * float(cv['close_d0']) * sh / 1e9
P(f"CVS Oct 2022: market value lost ${raw:.1f}bn raw, ${adj:.1f}bn after peers; CVS put the 2024 cost at $0.8-1.0bn of operating income (8-K, May 2023) = {adj/1.0:.0f}x to {adj/0.8:.0f}x the one-year hit; its 4+ share recovered to 91% the next year")
big = [e for e in ev if e['ticker'] in ('CVS', 'HUM')]
P("MA-heavy events (CVS 2022, HUM 2024): window excess " + ', '.join(f"{e['ticker']} {float(e['excess_win']):+.1f}%" for e in big) +
  "; 12 months later " + ', '.join(f"{e['ticker']} {float(e['excess_12m']):+.1f}%" for e in big))
small = [float(e['excess_win']) for e in ev if e['ticker'] not in ('CVS', 'HUM', 'ALHC')]
P(f"Diversified parents (UNH, ELV, CNC, MOH; {len(small)} events): window excess {min(small):+.1f}% to {max(small):+.1f}%, median {__import__('statistics').median(small):+.1f}%")
P("Caveat: HUM's 12-month excess is flattered by the peer basket falling 24.6% from Oct 2024 to Oct 2025; CVS kept lagging after its stars came back.")
open(os.path.join(HERE, '..', 'results', 'history_test.txt'), 'w').write('\n'.join(out) + '\n')
