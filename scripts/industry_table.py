# Who else moves if the 10 rulemaking measures come out: enrollment-weighted, by parent company.
# Enrollment: CMS Monthly Enrollment by Contract, October 2026.
# Dollars: CMS 2027 MA rate book, county 5% bonus rate minus 0% bonus rate, weighted by each
# contract's October 2026 county enrollment (CMS state/county/contract file). Benchmark basis,
# risk score 1.0, 2027 rates standing in for 2028. QBP is the same 5% (10% in double-bonus counties)
# for any rating of 4.0 or above, so only crossings of the 4.0 line move money.
import os, csv, re
from recompute_stars import *
import h3815_scenarios as S

enr = {}
with open(os.path.join(DATA, 'enrollment_by_contract_2026_10.csv'), encoding='latin1') as f:
    for r in csv.DictReader(f):
        c = r['Contract Number'].strip()
        e = r['Enrollment'].strip()
        if e.isdigit():
            enr[c] = int(e)

qbp = {}
with open(os.path.join(DATA, 'contract_county_rates_2027.csv')) as f:
    for r in csv.DictReader(f):
        qbp[r['contract']] = (float(r['avg_rate_0pct']), float(r['avg_qbp_delta']))

parent = {}
for r in read('summary_ratings_2027.csv')[2:]:
    if r and re.match(r'^[EHRS]\d', r[0].strip()):
        parent[r[0].strip()] = r[4].strip()

def qbp_rating(c, drop=()):
    # MA-PD contracts are paid on the overall rating, MA-only on the Part C summary
    if c in MAPD:
        return final_rating(c, 'overall', drop)[1]
    r = final_rating(c, 'part_c', drop)
    return None if r is None else r[1]

# Risk scores for the contracts that cross the 4.0 line: CMS 2024 Plan Payment Data, plan-level Part C risk
# scores weighted by July 2024 plan enrollment. Two contracts are too new to have 2024 data; they get 1.0.
RS = {}
with open(os.path.join(DATA, 'risk_scores_2024_crossing_contracts.csv')) as f:
    for r in csv.DictReader(f):
        RS[r['contract']] = float(r['avg_part_c_risk_score_2024_enrollment_weighted']) if r['avg_part_c_risk_score_2024_enrollment_weighted'] else 1.0

rows = {}
for c in stars:
    if not c.startswith(('H', 'R')) or c not in enr:
        continue
    try:
        a = qbp_rating(c); b = qbp_rating(c, S.RULE)
    except Exception:
        continue
    if a is None or b is None:
        continue
    d = qbp.get(c, (None, None))[1]
    usd = enr[c] * d * 12 if d is not None else None
    # KFF's method: Medicare's extra spend is the benchmark lift times the rebate share,
    # 65% for 3.5 to 4.0 stars and 70% for 4.5 and up (paid at the 4+ rating)
    paid_at = b if b >= 4 else a
    share = 0.70 if paid_at >= 4.5 else 0.65
    rs = RS.get(c, 1.0)
    rows[c] = dict(parent=parent.get(c, ''), enr=enr[c], pub=a, alt=b, usd=usd, kff=(usd * share if usd is not None else None),
                   cash=(usd * share * rs if usd is not None else None), rs=rs)

GROUPS = [('UnitedHealth', 'UnitedHealth Group, Inc.'), ('Humana', 'Humana Inc.'), ('CVS (Aetna)', 'CVS Health Corporation'),
          ('Elevance', 'Elevance Health, Inc.'), ('Alignment', 'Alignment Healthcare USA, LLC')]

def summarize(name, pick):
    cs = [c for c in rows if pick(rows[c])]
    tot = sum(rows[c]['enr'] for c in cs)
    in4 = sum(rows[c]['enr'] for c in cs if rows[c]['pub'] >= 4)
    in4b = sum(rows[c]['enr'] for c in cs if rows[c]['alt'] >= 4)
    up = [c for c in cs if rows[c]['pub'] < 4 <= rows[c]['alt']]
    dn = [c for c in cs if rows[c]['pub'] >= 4 > rows[c]['alt']]
    gain = sum(rows[c]['usd'] or 0 for c in up); loss = sum(rows[c]['usd'] or 0 for c in dn)
    pool = sum(rows[c]['usd'] or 0 for c in cs if rows[c]['pub'] >= 4)
    kg = sum(rows[c]['kff'] or 0 for c in up); kl = sum(rows[c]['kff'] or 0 for c in dn)
    cg = sum(rows[c]['cash'] or 0 for c in up); cl = sum(rows[c]['cash'] or 0 for c in dn)
    return [name, len(cs), tot, round(100 * in4 / tot, 1), round(100 * in4b / tot, 1), len(up), len(dn),
            round(gain / 1e6), round(-loss / 1e6), round((gain - loss) / 1e6), round(gain / 1e6), round(pool / 1e6),
            round(kg / 1e6), round(-kl / 1e6), round((kg - kl) / 1e6), round(cg / 1e6), round(-cl / 1e6), round((cg - cl) / 1e6)]

hdr = ['group', 'rated_contracts', 'oct26_enrollment', 'pct_in_4plus_published', 'pct_in_4plus_without_10',
       'contracts_up', 'contracts_down', 'qbp_gain_musd', 'qbp_loss_musd', 'net_if_symmetric_musd', 'one_way_musd', 'qbp_pool_published_musd',
       'kff_gain_musd', 'kff_loss_musd', 'kff_net_musd', 'cash_gain_musd', 'cash_loss_musd', 'cash_net_musd']
out = [summarize(n, lambda r, p=p: r['parent'] == p) for n, p in GROUPS]
out.append(summarize('All rated MA contracts', lambda r: True))
for o in out:
    print(dict(zip(hdr, o)))
h = rows['H3815']
print(f"H3815: {h['enr']:,} members (Oct 2026), avg county QBP {qbp['H3815'][1]:.2f} PMPM on a 0% base of {qbp['H3815'][0]:.2f} "
      f"({100*qbp['H3815'][1]/qbp['H3815'][0]:.2f}%), annual QBP at stake {h['usd']/1e6:.1f}m at risk score 1.0, "
      f"{h['kff']/1e6:.1f}m on KFF's rebate-share basis")
with open(os.path.join(HERE, '..', 'results', 'industry_table.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(out)
with open(os.path.join(HERE, '..', 'results', 'contracts_crossing_4.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['contract', 'parent', 'oct26_enrollment', 'stars_published', 'stars_without_10', 'risk_score_2024', 'benchmark_lift_musd_rs1', 'cash_musd'])
    for c in sorted(rows, key=lambda c: -(rows[c]['usd'] or 0)):
        r = rows[c]
        if (r['pub'] >= 4) != (r['alt'] >= 4):
            w.writerow([c, r['parent'], r['enr'], r['pub'], r['alt'], r['rs'], round((r['usd'] or 0) / 1e6, 1), round((r['cash'] or 0) / 1e6, 1)])
