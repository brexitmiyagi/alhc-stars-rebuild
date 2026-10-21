"""Contract-level model: where Alignment's members, revenue and quality bonus sit, contract by contract.

Inputs (all CMS, in data/): October 2026 enrollment by contract; 2027 county rate book weighted by each
contract's October 2026 county enrollment (avg_rate_0pct = benchmark with no bonus, avg_qbp_delta = what the 5%
quality bonus adds); Star Ratings 2019-2027; February enrollment 2019-2026.

Bonus rules: a contract's rating in year t sets its quality bonus in payment year t+1 (4 stars or more earns it).
Rebate share of the benchmark-minus-bid margin: 70% at 4.5 stars and up, 65% at 3.5 to 4, 50% below.
H6697 (new for 2027) takes the enrollment-weighted average of Alignment's other contracts, about 3.71, so no bonus
in 2028.

Revenue is allocated across contracts in proportion to members x benchmark (with the bonus where earned), scaled
to my company revenue from model/ALHC_model.xlsx. That assumes risk scores and bid ratios are similar across
contracts; H3815's 2024 risk score (1.0992, CMS plan payment data) is used for its bonus dollars.
Writes results/contract_model.csv and model/ALHC_contract_model.xlsx.
"""
import os, csv
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, '..', 'data', f)
M = load_workbook(os.path.join(HERE, '..', 'model', 'ALHC_model.xlsx'), data_only=True)['Model']
REV26, REV27, REV28 = M['P8'].value, M['Q8'].value, M['R8'].value

STATE = {'H3815': 'CA', 'H4961': 'CA', 'H8832': 'CA', 'H6697': 'CA', 'H5296': 'NC', 'H7074': 'NC', 'H3443': 'AZ', 'H5472': 'AZ', 'H9686': 'NV'}
TYPE = {}
enr = {}
for r in csv.DictReader(open(D('enrollment_by_contract_2026_10.csv'))):
    c = r['Contract Number']
    if c in STATE:
        enr[c] = int(r['Enrollment']); TYPE[c] = r['Plan Type']
rates = {r['contract']: (float(r['avg_rate_0pct']), float(r['avg_qbp_delta'])) for r in csv.DictReader(open(D('contract_county_rates_2027.csv')))}
hist = {r['contract']: r for r in csv.DictReader(open(D('stars_and_enrollment_2019_2027.csv')))}
summ = {}
for line in open(D('summary_ratings_2027.csv'), encoding='utf-8', errors='ignore'):
    p = next(csv.reader([line]))
    if p and p[0].strip() in STATE:
        summ[p[0].strip()] = p[10].strip()
RS_H3815 = 1.0992

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

# contracts too new for a 2026 rating (H8832) take the enrollment-weighted 2026 average of Alignment's rated contracts
rated26 = [(num(h['stars_2026']), num(h['enroll_feb_2026'])) for k, h in hist.items() if k in STATE and num(h.get('stars_2026')) and num(h.get('enroll_feb_2026'))]
NEW26 = sum(a * b for a, b in rated26) / sum(b for a, b in rated26)
rows = []
for c in sorted(enr, key=lambda k: -enr[k]):
    s26 = num(hist.get(c, {}).get('stars_2026')); s27 = num(summ.get(c))
    if s26 is None and c == 'H8832': s26 = round(NEW26, 2)
    if c == 'H6697': s27 = None
    base, lift = rates.get(c, (None, None))
    bonus27 = s26 is not None and s26 >= 4
    bonus28 = s27 is not None and s27 >= 4
    f25 = num(hist.get(c, {}).get('enroll_feb_2025')); f26 = num(hist.get(c, {}).get('enroll_feb_2026'))
    rows.append(dict(contract=c, state=STATE[c], plan_type=TYPE[c], members_oct26=enr[c], stars_2026=s26, stars_2027=s27 if s27 is not None else summ.get(c, ''),
                     bonus_2027=bonus27, bonus_2028=bonus28, base_rate=base, qbp_lift=lift,
                     growth_feb25_feb26=(f26 / f25 - 1) if f25 and f26 else None, growth_feb26_oct26=(enr[c] / f26 - 1) if f26 else None))
tot = sum(r['members_oct26'] for r in rows)
w27 = {r['contract']: r['members_oct26'] * ((r['base_rate'] or 0) + (r['qbp_lift'] if r['bonus_2027'] else 0)) for r in rows}
W = sum(w27.values())
out = []
P = lambda s: (print(s), out.append(s))
P(f"New-contract rule: H8832 (first rated in 2027) takes the 2026 weighted average of Alignment's rated contracts, {NEW26:.2f}, so it earns the bonus in 2027; H7074 has too few members to rate and is shown with no bonus")
P(f"Alignment contracts, October 2026 (CMS): {tot:,} members; company 2027E revenue ${REV27:,.0f}m allocated by members x benchmark")
P(f"{'Contract':8s} {'St':3s} {'Members':>8s} {'Share':>6s} {'Stars26':>7s} {'Stars27':>7s} {'Bonus27':>7s} {'Bonus28':>7s} {'Base':>8s} {'Lift':>6s} {'Rev27 $m':>9s} {'Bonus $m 28 at risk':>19s} {'Gr Feb25-26':>11s}")
for r in rows:
    r['share'] = r['members_oct26'] / tot
    r['rev27_musd'] = REV27 * w27[r['contract']] / W
    rs = RS_H3815 if r['contract'] == 'H3815' else 1.0
    lost = (r['bonus_2027'] and not r['bonus_2028'])
    r['bonus_lost_2028_gross_musd'] = r['members_oct26'] * (r['qbp_lift'] or 0) * rs * 12 / 1e6 if lost else 0.0
    r['bonus_lost_2028_cash_musd'] = r['bonus_lost_2028_gross_musd'] * 0.65
    g = r['growth_feb25_feb26']
    P(f"{r['contract']:8s} {r['state']:3s} {r['members_oct26']:>8,} {r['share']:>6.1%} {str(r['stars_2026'] or '-'):>7s} {str(r['stars_2027']):>7s} {str(r['bonus_2027']):>7s} {str(r['bonus_2028']):>7s} {r['base_rate'] or 0:>8.2f} {r['qbp_lift'] or 0:>6.2f} {r['rev27_musd']:>9.0f} {r['bonus_lost_2028_cash_musd']:>19.1f} {('%+.0f%%' % (100 * g)) if g is not None else '-':>11s}")
by_state = {}
for r in rows:
    s = by_state.setdefault(r['state'], [0, 0.0]); s[0] += r['members_oct26']; s[1] += r['rev27_musd']
P('By state: ' + ', '.join(f"{k} {v[0]:,} members ({v[0] / tot:.0%}), ${v[1]:,.0f}m 2027E revenue" for k, v in sorted(by_state.items(), key=lambda kv: -kv[1][0])))
in27 = sum(r['members_oct26'] for r in rows if r['bonus_2027']) / tot
in28 = sum(r['members_oct26'] for r in rows if r['bonus_2028']) / tot
P(f"Members in bonus-earning contracts: 2027 payments {in27:.0%}, 2028 payments {in28:.0%} (on October 2026 enrollment)")
P(f"2028 bonus lost: H3815 ${sum(r['bonus_lost_2028_gross_musd'] for r in rows):.1f}m gross at its risk score, ${sum(r['bonus_lost_2028_cash_musd'] for r in rows):.1f}m as rebate dollars (65%) on October 2026 members")
non = [r for r in rows if r['contract'] != 'H3815']
P(f"Outside H3815: {sum(r['members_oct26'] for r in non):,} members ({sum(r['members_oct26'] for r in non) / tot:.0%}), all rated 4 or higher in 2027 except H7074 (too small to rate)")
P(f"Growth Feb 2025 to Feb 2026: H3815 {rows[0]['growth_feb25_feb26']:+.0%}; contracts outside California " +
  f"{sum(num(hist[r['contract']]['enroll_feb_2026']) or 0 for r in non if r['state'] != 'CA' and r['contract'] in hist) / max(1, sum(num(hist[r['contract']]['enroll_feb_2025']) or 0 for r in non if r['state'] != 'CA' and r['contract'] in hist)) - 1:+.0%}")

fields = ['contract', 'state', 'plan_type', 'members_oct26', 'share', 'stars_2026', 'stars_2027', 'bonus_2027', 'bonus_2028', 'base_rate', 'qbp_lift', 'rev27_musd', 'bonus_lost_2028_gross_musd', 'bonus_lost_2028_cash_musd', 'growth_feb25_feb26', 'growth_feb26_oct26']
with open(os.path.join(HERE, '..', 'results', 'contract_model.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader()
    for r in rows: w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k in fields})
open(os.path.join(HERE, '..', 'results', 'contract_model.txt'), 'w').write('\n'.join(out) + '\n')

# workbook with live formulas
wb = Workbook(); ws = wb.active; ws.title = 'Contracts'
BLUE, BOLD, HDR = Font(color='0000FF'), Font(bold=True), PatternFill('solid', fgColor='DCE6E8')
ws['A1'] = 'Alignment Healthcare: contract-level model (inputs blue; CMS October 2026 enrollment, 2027 rate book, Star Ratings)'; ws['A1'].font = BOLD
ws['A2'] = 'Company 2027E revenue ($m)'; ws['B2'] = round(REV27, 1); ws['B2'].font = BLUE
ws['A3'] = 'H3815 risk score (2024 plan payment data)'; ws['B3'] = RS_H3815; ws['B3'].font = BLUE
ws['A4'] = 'Rebate share at 3.5 to 4 stars'; ws['B4'] = 0.65; ws['B4'].font = BLUE
hdr = ['Contract', 'State', 'Members Oct 2026', 'Share', 'Stars 2026', 'Stars 2027', 'Bonus in 2027', 'Bonus in 2028', 'Benchmark, no bonus ($pmpm)', 'Bonus lift ($pmpm)', 'Allocation weight', '2027E revenue ($m)', '2028 bonus lost, gross ($m)', '2028 bonus lost, rebate dollars ($m)']
for j, h in enumerate(hdr): c = ws.cell(6, 1 + j, h); c.font = BOLD; c.fill = HDR
n = len(rows); first, last = 7, 6 + n
for i, r in enumerate(rows):
    k = 7 + i
    vals = [r['contract'], r['state'], r['members_oct26'], None, r['stars_2026'] if r['stars_2026'] is not None else '-', r['stars_2027'] if isinstance(r['stars_2027'], float) else (r['stars_2027'] or 'new'),
            'Yes' if r['bonus_2027'] else 'No', 'Yes' if r['bonus_2028'] else 'No', r['base_rate'] or 0, r['qbp_lift'] or 0]
    for j, v in enumerate(vals):
        cell = ws.cell(k, 1 + j, v)
        if j in (2, 4, 5, 6, 7, 8, 9): cell.font = BLUE
    ws.cell(k, 4, f'=C{k}/SUM($C${first}:$C${last})').number_format = '0.0%'
    ws.cell(k, 11, f'=C{k}*(I{k}+IF(G{k}="Yes",J{k},0))').number_format = '#,##0'
    ws.cell(k, 12, f'=$B$2*K{k}/SUM($K${first}:$K${last})').number_format = '#,##0'
    rs_ref = '$B$3' if r['contract'] == 'H3815' else '1'
    ws.cell(k, 13, f'=IF(AND(G{k}="Yes",H{k}="No"),C{k}*J{k}*{rs_ref}*12/1000000,0)').number_format = '#,##0.0'
    ws.cell(k, 14, f'=M{k}*$B$4').number_format = '#,##0.0'
t = last + 1
ws.cell(t, 1, 'Total').font = BOLD
for col in 'CKLMN':
    ws[f'{col}{t}'] = f'=SUM({col}{first}:{col}{last})'; ws[f'{col}{t}'].font = BOLD
ws[f'A{t + 2}'] = 'Share of members in bonus-earning contracts, 2028 payments'
ws[f'B{t + 2}'] = f'=SUMIF(H{first}:H{last},"Yes",C{first}:C{last})/C{t}'; ws[f'B{t + 2}'].number_format = '0%'
for col, wdt in zip('ABCDEFGHIJKLMN', (10, 6, 12, 8, 9, 9, 10, 10, 14, 12, 14, 12, 14, 16)): ws.column_dimensions[col].width = wdt
wb.save(os.path.join(HERE, '..', 'model', 'ALHC_contract_model.xlsx'))
