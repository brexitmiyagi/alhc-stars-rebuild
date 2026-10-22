"""What the market actually charged for the star, and what it charged in September.

Peer-relative returns around the two events, from daily closes in data/prices_daily_2026_09_08_to_MM_DD.csv (ASOF, default 2026-10-22).
Peers: UnitedHealth, Humana, Elevance, CVS, Centene, Molina, Cigna. Abnormal return = Alignment's return
less the peer median return over the same window. Dollar figures are per share on the price before the event.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ASOF = os.environ.get('ASOF', '2026-10-22')
px = pd.read_csv(os.path.join(HERE, '..', 'data', f"prices_daily_2026_09_08_to_{ASOF[5:].replace('-', '_')}.csv"), index_col='date')
PEERS = ['UNH', 'HUM', 'ELV', 'CVS', 'CNC', 'MOH', 'CI']
out = []
P = lambda s: (print(s), out.append(s))

def window(a, b, label):
    r = px.loc[b] / px.loc[a] - 1
    med = r[PEERS].median()
    ab = r['ALHC'] - med
    p0 = px.loc[a, 'ALHC']
    exh = r['ALHC'] - r[[t for t in PEERS if t != 'HUM']].median()
    mkt = r['ALHC'] - 1.14 * r['SPX']  # Alignment's 5-year beta
    P(f"{label} ({a} close to {b} close): Alignment {r['ALHC']:+.1%}, peer median {med:+.1%}, S&P 500 {r['SPX']:+.1%}; "
      f"abnormal vs peers {ab:+.1%} (${ab * p0:+.2f}), vs peers without Humana {exh:+.1%} (${exh * p0:+.2f}), vs the market at beta 1.14 {mkt:+.1%} (${mkt * p0:+.2f})")
    return ab

P("Peers each day are " + ", ".join(PEERS))
window('2026-09-14', '2026-09-16', 'Baird conference, claims and cost comments (15 Sep)')
window('2026-09-16', '2026-10-08', 'Between the two events')
window('2026-10-08', '2026-10-09', 'Star Ratings day (CMS release after the 8 Oct close)')
window('2026-10-09', ASOF, 'After the stars day')
window('2026-10-08', ASOF, f'Stars release to {int(ASOF[8:])} Oct')
window('2026-09-14', ASOF, 'Whole period')
r = px.loc['2026-10-09'] / px.loc['2026-10-08'] - 1
P("Stars day by peer: " + ", ".join(f"{t} {r[t]:+.1%}" for t in PEERS))

# chart data: each series rebased to 100 at the 14 Sep close; peers as the median of the rebased series
reb = px / px.loc['2026-09-14'] * 100
chart = pd.DataFrame({'Alignment': reb['ALHC'].round(1), 'Peer median': reb[PEERS].median(axis=1).round(1), 'S&P 500': reb['SPX'].round(1)})
chart.to_csv(os.path.join(HERE, '..', 'results', 'event_study_chart.csv'))
open(os.path.join(HERE, '..', 'results', 'event_study.txt'), 'w').write('\n'.join(out) + '\n')
