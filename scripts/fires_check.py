# Could the January 2025 Los Angeles fires explain H3815's physical health drop?
# H3815 had 21% of members in 2025 disaster areas (CMS summary table), under the 25% line where relief applies.
# Compare it with every other contract that had at least 10% of members in 2025 disaster areas.
import os, csv, re
import numpy as np
from recompute_stars import read, DATA
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import hos_noise as N

dis = {}
for r in read('summary_ratings_2027.csv')[2:]:
    if r and re.match(r'^[HR]\d', r[0].strip()):
        v = r[7].strip()
        dis[r[0].strip()] = int(v) if v.isdigit() else 0
moves = []
for c, r in N.h26.items():
    a = r['ph_score_2026']; b = N.score27(c, 'C04')
    if a and b is not None and dis.get(c, 0) >= 10:
        moves.append((c, dis[c], int(a), b, b - int(a)))
others = [m for m in moves if m[0] != 'H3815']
d = [m[4] for m in others]
print(f"Contracts with >=10% of members in 2025 disaster areas and PH scores both years: {len(moves)} (H3815 at {dis['H3815']}%)")
print(f"The other {len(others)}: PH change from {min(d):+d} to {max(d):+d} points, median {np.median(d):+.1f}; H3815 {[m[4] for m in moves if m[0]=='H3815'][0]:+d}")
