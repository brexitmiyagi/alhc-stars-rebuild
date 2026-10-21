"""What the market actually charged for the star, and what it charged in September.

Peer-relative returns around the two events, from daily closes in data/prices_daily_2026_09_08_to_10_21.csv.
Peers: UnitedHealth, Humana, Elevance, CVS, Centene, Molina, Cigna. Abnormal return = Alignment's return
less the peer median return over the same window. Dollar figures are per share on the price before the event.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
px = pd.read_csv(os.path.join(HERE, '..', 'data', 'prices_daily_2026_09_08_to_10_21.csv'), index_col='date')
PEERS = ['UNH', 'HUM', 'ELV', 'CVS', 'CNC', 'MOH', 'CI']
out = []
P = lambda s: (print(s), out.append(s))

def window(a, b, label):
    r = px.loc[b] / px.loc[a] - 1
    med = r[PEERS].median()
    ab = r['ALHC'] - med
    P(f"{label} ({a} close to {b} close): Alignment {r['ALHC']:+.1%}, peer median {med:+.1%}, S&P 500 {r['SPX']:+.1%}; "
      f"abnormal {ab:+.1%}, about ${ab * px.loc[a, 'ALHC']:+.2f} a share on ${px.loc[a, 'ALHC']:.2f}")
    return ab

P("Peers each day are " + ", ".join(PEERS))
window('2026-09-14', '2026-09-16', 'Baird conference, claims and cost comments (15 Sep)')
window('2026-09-16', '2026-10-08', 'Between the two events')
window('2026-10-08', '2026-10-09', 'Star Ratings day (CMS release after the 8 Oct close)')
window('2026-10-09', '2026-10-21', 'After the stars day')
window('2026-10-08', '2026-10-21', 'Stars release to 21 Oct')
window('2026-09-14', '2026-10-21', 'Whole period')
r = px.loc['2026-10-09'] / px.loc['2026-10-08'] - 1
P("Stars day by peer: " + ", ".join(f"{t} {r[t]:+.1%}" for t in PEERS))

# chart data: each series rebased to 100 at the 14 Sep close; peers as the median of the rebased series
reb = px / px.loc['2026-09-14'] * 100
chart = pd.DataFrame({'Alignment': reb['ALHC'].round(1), 'Peer median': reb[PEERS].median(axis=1).round(1), 'S&P 500': reb['SPX'].round(1)})
chart.to_csv(os.path.join(HERE, '..', 'results', 'event_study_chart.csv'))
open(os.path.join(HERE, '..', 'results', 'event_study.txt'), 'w').write('\n'.join(out) + '\n')
