# Fails loudly if the rebuild stops matching what CMS and the companies published.
import os, csv, re
from recompute_stars import *

ok = tot = 0
for c in MAPD:
    r = final_rating(c, 'overall')
    if r is None:
        continue
    tot += 1; ok += abs(r[1] - float(pub[c][2])) < 1e-9
assert ok / tot >= 0.99, f'overall tie-out fell to {ok}/{tot}'
print(f'overall ratings rebuilt: {ok} of {tot} match CMS')

for rating, i in (('part_c', 0), ('part_d_mapd', 1), ('overall', 2)):
    r = final_rating('H3815', rating)
    assert abs(r[1] - float(pub['H3815'][i])) < 1e-9, f'H3815 {rating} does not match CMS'
print('H3815 Part C, Part D and overall all match CMS (3.5 / 3.5 / 3.5)')

# the two hand-transferred files carry the checksums the browser printed when I pulled them
r = list(csv.DictReader(open(os.path.join(DATA, 'contract_county_rates_2027.csv'))))
assert len(r) == 687 and sum(int(x['scc_enrolled']) for x in r) == 36147135
assert round(sum(float(x['avg_qbp_delta']) for x in r), 2) == 45866.27
rows = list(csv.reader(open(os.path.join(DATA, 'hos_and_controls_2026.csv'))))[1:]
assert len(rows) == 513 and sum(int(v) for row in rows for v in row[1:] if v) == 113732
print('transferred files match their checksums')

import industry_table as T
hum = [o for o in T.out if o[0] == 'Humana'][0]
alhc = [o for o in T.out if o[0] == 'Alignment'][0]
assert abs(hum[3] - 95.0) < 0.6, 'Humana share in 4+ no longer near the 95% in its Oct 9 release'
assert abs(alhc[3] - 25.0) < 0.6, 'Alignment share in 4+ no longer near 25%'
cvs = [o for o in T.out if o[0] == 'CVS (Aetna)'][0]
assert cvs[3] > 69.0, 'CVS share in 4+ no longer above the "more than 69%" in its Oct 8 release'
print(f'Humana {hum[3]}% in 4+ (release: 95%); Alignment {alhc[3]}% (reported: 25%); CVS {cvs[3]}% (release: more than 69%)')

# CMS 2027 fact sheet: 188 MA-PD contracts at 4+ stars, about 71% of MA-PD enrollees in them
n4 = sum(1 for c in MAPD if float(pub[c][2]) >= 4)
assert n4 == 188, f'{n4} MA-PD contracts at 4+, fact sheet says 188'
e4 = sum(T.enr.get(c, 0) for c in MAPD if float(pub[c][2]) >= 4); et = sum(T.enr.get(c, 0) for c in MAPD)
assert abs(100 * e4 / et - 71) < 1.0, 'MA-PD enrollment share in 4+ drifted from the fact sheet 71%'
print(f'CMS fact sheet: {n4} MA-PD contracts at 4+ (188), {100*e4/et:.1f}% of MA-PD enrollees (about 71%)')

# Alignment's October 9 complaint (1:26-cv-03550, para 151): without the ten measures, H3815 would be 4.0 and
# H8832, H3443 and H9686 would be 4.5. The rebuild has to land on the same four ratings.
import h3815_scenarios as S
want = {'H3815': 4.0, 'H8832': 4.5, 'H3443': 4.5, 'H9686': 4.5}
for c, v in want.items():
    got = final_rating(c, 'overall', S.RULE)[1]
    assert got == v, f'{c}: rebuild gives {got} without the ten measures, complaint says {v}'
print('Without the ten measures the rebuild gives H3815 4.0 and H8832, H3443, H9686 4.5, the same four ratings as the complaint')
print('tie-out passed')
