"""When a contract loses 4 stars, how much of the lost bonus actually shows up as a smaller rebate?

Data: data/rebate_cases_2019_2023.csv, built from CMS Plan Payment Data (Part C plan level, payment
years 2019-2024; contract = simple mean across its plans) and CMS overall Star Ratings 2018-2023.
  y   = rating year of the change; the rating for year y sets payments in year y+1
  g   = D (4.0 -> 3.5), S (4.0 -> 4.0), G (3.5 -> 4.0), L (3.5 -> 3.5)
  r0  = average rebate per member per month in payment year y   (bonus set by rating y-1)
  r1  = average rebate per member per month in payment year y+1 (bonus set by rating y)
  ab0 = average A/B payment per member per month in payment year y

Mechanical cut if nothing else changes: rebate = 65% x (risk-adjusted benchmark - bid), and a 5% bonus
sits inside the benchmark, so the rebate falls by 0.65 x benchmark x 0.05/1.05. Benchmark is
approximated as ab0 + r0/0.65 (bid plus the gap the rebate is 65% of). Counties with a doubled 10% bonus
make the true mechanical cut larger, so the pass-through below is if anything overstated.

Pass-through = (contract's rebate change minus the median change of same-year contracts that held
4 stars) / mechanical cut. 1.0 means members lose the whole formula amount; 0 means the plan lowered
its bid enough to keep the rebate where it was.
"""
import os, csv, statistics as st, random
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, '..', 'data', 'rebate_cases_2019_2023.csv'))))
for r in rows:
    for k in ('r0', 'r1', 'ab0'): r[k] = float(r[k])
    r['y'] = int(r['y'])
print(f"cases {len(rows)}; checksum {sum(r['r0'] + r['r1'] + r['ab0'] for r in rows):.2f}")

def q(a, p):
    s = sorted(a); return s[int(p * (len(s) - 1))]

def passthrough(group, base, scale=1.0, years=range(2019, 2024)):
    out = []
    for y in years:
        b = [r['r1'] - r['r0'] for r in rows if r['y'] == y and r['g'] == base]
        if not b: continue
        mb = st.median(b)
        for r in rows:
            if r['y'] == y and r['g'] == group:
                mech = 0.65 * 0.05 / (1.05 if group == 'D' else 1.0) * (r['ab0'] + r['r0'] / 0.65)
                x = (r['r1'] - r['r0'] - mb) / mech
                out.append((y, -x if group == 'D' else x, mech))
    return out

d = passthrough('D', 'S')
xs = [x for _, x, _ in d]
print(f"Lost 4 stars (4.0 -> 3.5), n {len(xs)}: median pass-through {st.median(xs):.2f}, IQR {q(xs,.25):.2f} to {q(xs,.75):.2f}; median mechanical cut ${st.median([m for *_, m in d]):.1f} a member a month")
for y in range(2019, 2024):
    a = [x for yy, x, _ in d if yy == y]
    if a: print(f"   rating year {y}: n {len(a)}, median {st.median(a):.2f}")
ex = [x for y, x, _ in d if y != 2021]
print(f"   excluding the 2021 ratings: n {len(ex)}, median {st.median(ex):.2f}")
random.seed(3)
boots = sorted(st.median(random.choices(xs, k=len(xs))) for _ in range(5000))
print(f"   bootstrap 90% interval for the median: {boots[250]:.2f} to {boots[4750]:.2f}")
g = [x for _, x, _ in passthrough('G', 'L')]
print(f"Gained 4 stars (3.5 -> 4.0), n {len(g)}: median pass-through {st.median(g):.2f}")
print(f"Read: when the bonus goes, members lose about {st.median(xs):.0%} of the formula cut in their rebate; the plan's bid absorbs the rest, about {1-st.median(xs):.0%}.")
