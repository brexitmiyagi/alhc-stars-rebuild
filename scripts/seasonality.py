"""Is a worse second half normal for Alignment? Its own 2023-2025 quarters say no.

Uses GAAP medical expenses / total revenue from the 10-Q and 10-K XBRL statements (Q4 = full year less
nine months). The company's adjusted MBR differs by about 0.1-0.2 points in 2026 (Q1 88.18% adjusted vs
88.30% GAAP, Q2 86.3% vs 86.45%), small enough that the seasonal shape carries over.
"""
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, '..', 'data', 'quarterly_mbr_2023_2026.csv'))))
rev = {(r['year'], r['quarter']): float(r['revenue_kusd']) for r in rows}
med = {(r['year'], r['quarter']): float(r['medical_expenses_kusd']) for r in rows}
out = []
P = lambda s: (print(s), out.append(s))
for y in ('2023', '2024', '2025'):
    rev[(y, '4')] = rev[(y, 'FY')] - sum(rev[(y, q)] for q in '123')
    med[(y, '4')] = med[(y, 'FY')] - sum(med[(y, q)] for q in '123')
r = lambda y, qs: sum(med[(y, q)] for q in qs) / sum(rev[(y, q)] for q in qs)
gaps = []
for y in ('2023', '2024', '2025'):
    h1, h2, q3, q4 = r(y, '12'), r(y, '34'), r(y, '3'), r(y, '4')
    gaps.append(h2 - h1)
    P(f"{y}: Q1 {r(y, '1'):.2%} Q2 {r(y, '2'):.2%} Q3 {q3:.2%} Q4 {q4:.2%} | H1 {h1:.2%} H2 {h2:.2%} | H2 minus H1 {100 * (h2 - h1):+.2f} pts, Q3 minus H1 {100 * (q3 - h1):+.2f}")
h1_26 = r('2026', '12')
P(f"2026: Q1 {r('2026', '1'):.2%} Q2 {r('2026', '2'):.2%} | H1 {h1_26:.2%}")
P(f"Average H2 minus H1, 2023-2025: {100 * sum(gaps) / 3:+.2f} pts")
# 2026 second half implied by guidance and by my model (adjusted basis; H1 adjusted 87.2%)
h1_adj = 1 - (146 + 183) / (1235.197 + 1335.633)
guide_h2 = 1 - (640 - 329) / (5210 - 2570.83)
q3_guide_mid = 1 - 153 / 1310
mine_h2 = (0.887 * 1310 + 0.884 * 1329.17) / (1310 + 1329.17)
P(f"2026 adjusted: H1 {h1_adj:.2%}; guidance midpoint implies H2 {guide_h2:.2%} ({100 * (guide_h2 - h1_adj):+.2f} pts) and Q3 {q3_guide_mid:.2%}; my H2 {mine_h2:.2%} ({100 * (mine_h2 - h1_adj):+.2f} pts)")
q3_25 = h1_adj + (r('2025', '3') - r('2025', '12'))
P(f"If Q3 2026 followed 2025's pattern it would be about {q3_25:.2%} adjusted, against my 88.70%")
open(os.path.join(HERE, '..', 'results', 'seasonality.txt'), 'w').write('\n'.join(out) + '\n')
