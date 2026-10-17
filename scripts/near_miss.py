# How close H3815 came: the 2027 cut points for the two survey measures, and the smallest score
# changes that would have kept the contract at 4 stars, everything else as published.
import os, csv, re
from recompute_stars import *

cp = list(csv.reader(open(os.path.join(DATA, 'part_c_cut_points_2027.csv'), encoding='latin1')))
lab = cp[2]
def cuts(m):
    i = [k for k, x in enumerate(lab) if x.strip().startswith(m + ':')][0]
    lo = [float(re.findall(r'[\d.]+', cp[r][i])[0]) for r in range(5, 9)]   # lower bound of 2..5 stars
    return lo
for m, name in (('C01', 'breast cancer screening'), ('C04', 'physical health'), ('C05', 'mental health')):
    lo = cuts(m)
    print(f"{name}: 2 stars starts at {lo[0]:g}%, 5 stars at {lo[3]:g}%, {lo[3]-lo[0]:g} points apart")

score = {}
md = read('measure_data_2027.csv')
labs = [r for r in md[:6] if any(re.match(r'\s*C01:', x) for x in r)][0]
for r in md:
    if r and r[0].strip() == 'H3815':
        for m in ('C04', 'C05'):
            i = [k for k, x in enumerate(labs) if x.strip().startswith(m + ':')][0]
            score[m] = int(r[i].strip().rstrip('%'))
print(f"H3815: physical health {score['C04']}% (1 star), mental health {score['C05']}% (1 star)")

def star_for(m, s):
    lo = cuts(m); return 1 + sum(s >= x for x in lo)
base = dict(stars['H3815']); best = None
for dp in range(0, 12):
    for dm in range(0, 8):
        stars['H3815'] = dict(base)
        stars['H3815']['C04'] = star_for('C04', score['C04'] + dp)
        stars['H3815']['C05'] = star_for('C05', score['C05'] + dm)
        if final_rating('H3815', 'overall')[1] >= 4 and (best is None or dp + dm < best[0]):
            best = (dp + dm, dp, dm, final_rating('H3815', 'overall')[0])
stars['H3815'] = dict(base)
print(f"Smallest combined move that keeps 4 stars: +{best[1]} points on physical health and +{best[2]} on mental health ({best[0]} points), raw {best[3]:.2f}")
alone = min(dp for dp in range(0, 15) if (lambda: (stars.__setitem__('H3815', {**base, 'C04': star_for('C04', score['C04'] + dp)}), final_rating('H3815', 'overall')[1] >= 4)[1])())
stars['H3815'] = dict(base)
print(f"Physical health alone would have needed +{alone} points")
