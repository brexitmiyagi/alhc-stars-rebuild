"""What happens to a contract's membership after it loses 4 stars?

Data: data/stars_and_enrollment_2019_2027.csv
  stars_YYYY  = CMS Star Rating released in October of YYYY-1 (overall for MA-PD, Part C summary for MA-only)
  enroll_feb_YYYY = CMS Monthly Enrollment by Contract, February YYYY

Timing. Stars year Y are shown to shoppers in the fall before plan year Y, so
Feb(Y-1) -> Feb(Y) is the "display" year. They set the quality bonus for
payment year Y+1, so Feb(Y) -> Feb(Y+1) is the "bonus" year, the one where
the rebate (benefits) actually changes.

Groups, comparing stars Y-1 with stars Y:
  DROP  4+ -> under 4      STAY  4+ -> 4+
  GAIN  under 4 -> 4+      LOW   under 4 -> under 4
Contracts need at least 1,000 members at the start and a growth rate within +/-60%
(cuts out consolidations, crosswalks and new-contract ramps).
Excess growth = contract growth minus the median STAY growth that year.
"""
import csv, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, '..', 'data', 'stars_and_enrollment_2019_2027.csv')

rows = list(csv.DictReader(open(F)))
def num(x):
    return float(x) if x not in ('', None) else None

def q(a, p):
    s = sorted(a); return s[int(p * (len(s) - 1))]

def classify(a, b):
    if a >= 4: return 'STAY' if b >= 4 else 'DROP'
    return 'GAIN' if b >= 4 else 'LOW'

exp, disp = [], []
for Y in range(2020, 2026):
    for r in rows:
        a, b = num(r[f'stars_{Y-1}']), num(r[f'stars_{Y}'])
        if a is None or b is None: continue
        k = classify(a, b)
        e0, e1 = num(r[f'enroll_feb_{Y}']), num(r.get(f'enroll_feb_{Y+1}'))
        em = num(r.get(f'enroll_feb_{Y-1}'))
        if e0 is not None and e0 >= 1000 and e1 is not None:
            g = e1 / e0 - 1
            if abs(g) < 0.6: exp.append((Y, r['contract'], k, e0, e1, g))
        if em is not None and em >= 1000 and e0 is not None:
            g = e0 / em - 1
            if abs(g) < 0.6: disp.append((Y, r['contract'], k, em, e0, g))

print('Per year, median growth (%) by group')
print('stars yr | bonus year (Feb Y -> Feb Y+1)                     | display year (Feb Y-1 -> Feb Y)')
for Y in range(2020, 2026):
    parts, dparts = [], []
    for k in ('DROP', 'STAY', 'GAIN', 'LOW'):
        v = [x[5] for x in exp if x[0] == Y and x[2] == k]
        d = [x[5] for x in disp if x[0] == Y and x[2] == k]
        parts.append(f"{k} n{len(v)} {100*st.median(v):.1f}" if v else f"{k} n0 -")
        dparts.append(f"{k} {100*st.median(d):.1f}" if d else f"{k} -")
    print(Y, '|', ', '.join(parts), '|', ', '.join(dparts))

stay_med = {Y: st.median([x[5] for x in exp if x[0] == Y and x[2] == 'STAY']) for Y in range(2020, 2026)}
stay_med_d = {Y: st.median([x[5] for x in disp if x[0] == Y and x[2] == 'STAY']) for Y in range(2020, 2026)}

def excess(k, src=exp, base=stay_med, skip=()):
    return [x[5] - base[x[0]] for x in src if x[2] == k and x[0] not in skip]

def wgrowth(k, src=exp):
    rs = [x for x in src if x[2] == k]
    return sum(x[4] for x in rs) / sum(x[3] for x in rs) - 1

d = excess('DROP')
print()
print(f"Pooled bonus year, DROP n {len(d)}: median excess {100*st.median(d):.1f}pp, IQR {100*q(d,.25):.1f} to {100*q(d,.75):.1f}")
for k in ('GAIN', 'LOW'):
    v = excess(k); print(f"Pooled bonus year, {k} n {len(v)}: median excess {100*st.median(v):.1f}pp")
print('Enrollment-weighted bonus-year growth: ' + ', '.join(f"{k} {100*wgrowth(k):.1f}%" for k in ('DROP','STAY','GAIN','LOW')))
dr = [x for x in exp if x[2] == 'DROP']
print(f"DROP contracts that shrank in the bonus year: {100*sum(1 for x in dr if x[5] < 0)/len(dr):.0f}%")
d21 = excess('DROP', skip=(2021,))
print(f"Excluding 2021 (COVID hold-harmless years), DROP n {len(d21)}: median excess {100*st.median(d21):.1f}pp")
dd = excess('DROP', src=disp, base=stay_med_d)
print(f"Display year, DROP n {len(dd)}: median excess {100*st.median(dd):.1f}pp (the star on the label, before any rebate change)")

# H3815 itself
h = next(r for r in rows if r['contract'] == 'H3815')
print()
print('H3815 stars ' + ' '.join(f"{y}:{h[f'stars_{y}']}" for y in range(2019, 2028)))
print('H3815 Feb enrollment ' + ' '.join(f"{y}:{h[f'enroll_feb_{y}']}" for y in range(2019, 2027)))
