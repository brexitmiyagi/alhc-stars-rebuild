"""Financial summary page: 2025 actual (10-K) and my 2026-2028 estimates (model/ALHC_model.xlsx), with ratios,
and estimates against consensus. Writes results/financial_summary.csv and results/estimates_vs_consensus.csv."""
import os, csv
from openpyxl import load_workbook
HERE = os.path.dirname(os.path.abspath(__file__))
R = lambda f: os.path.join(HERE, '..', 'results', f)
M = load_workbook(os.path.join(HERE, '..', 'model', 'ALHC_model.xlsx'), data_only=True)['Model']
col = {'2026E': 'P', '2027E': 'Q', '2028E': 'R'}
v = lambda r, y: M[f'{col[y]}{r}'].value
# 2025 actual: 10-K FY2025 (statements of operations, balance sheet, cash flows); adj. GP / MBR / EBITDA from the Q4 2025 release
A = dict(rev=3948.719, med=3460.156, gp=494.8, mbr=0.875, sga=443.407, ebitda=109.9, da=30.404, interest=15.799, sbc=62.082,
         pretax=-0.958, ni=-0.724, eps=0.00, cash=575.817, sti=28.413, assets=1065.786, mep=474.569, debt=323.176, equity=179.277,
         cfo=139.927, capex=26.781, members=236.3, shares=198.006216)
rows = []
def add(label, a, f, fmt):
    rows.append([label, fmt.format(a) if a is not None else '', *[fmt.format(f(y)) for y in col]])
cfo26 = 111.4 + M['E55'].value + M['F55'].value  # H1 actual $111.4m (Q2 2026 10-Q) + my Q3/Q4
add('Members, year end (k)', A['members'], lambda y: v(5, y), '{:,.1f}')
add('Revenue ($m)', A['rev'], lambda y: v(8, y), '{:,.0f}')
add('Revenue growth', None, lambda y: v(8, y) / (A['rev'] if y == '2026E' else v(8, {'2027E': '2026E', '2028E': '2027E'}[y])) - 1, '{:.1%}')
add('Adj. MBR', A['mbr'], lambda y: v(10, y), '{:.1%}')
add('Adj. gross profit ($m)', A['gp'], lambda y: v(12, y), '{:,.0f}')
add('Adj. SG&A ratio', None, lambda y: v(13, y) / v(8, y), '{:.1%}')
add('Adj. EBITDA ($m)', A['ebitda'], lambda y: v(16, y), '{:,.1f}')
add('Adj. EBITDA margin', A['ebitda'] / A['rev'], lambda y: v(16, y) / v(8, y), '{:.2%}')
add('Stock pay ($m)', A['sbc'], lambda y: v(19, y), '{:,.1f}')
add('EBITDA after stock pay ($m)', A['ebitda'] - A['sbc'], lambda y: v(16, y) - v(19, y), '{:,.1f}')
add('Margin after stock pay', (A['ebitda'] - A['sbc']) / A['rev'], lambda y: (v(16, y) - v(19, y)) / v(8, y), '{:.2%}')
add('D&A ($m)', A['da'], lambda y: v(17, y), '{:,.1f}')
add('Interest ($m)', A['interest'], lambda y: v(18, y), '{:,.1f}')
add('Pre-tax income, approx. GAAP ($m)', A['pretax'], lambda y: v(20, y), '{:,.1f}')
add('Net income ($m)', A['ni'], lambda y: v(22, y), '{:,.1f}')
add('Adj. EPS, company definition ($)', None, lambda y: v(25, y), '{:.2f}')
add('GAAP EPS ($)', A['eps'], lambda y: v(26, y), '{:.2f}')
add('EPS after stock pay, taxed 24%, 215.0m shares ($)', None, lambda y: (v(16, y) - v(19, y) - v(17, y) - v(18, y)) * 0.76 / 215.024483, '{:.2f}')
add('Cash and equivalents ($m)', A['cash'], lambda y: v(29, y), '{:,.0f}')
add('Total assets ($m)', A['assets'], lambda y: v(35, y), '{:,.0f}')
add('Medical expenses payable ($m)', A['mep'], lambda y: v(37, y), '{:,.0f}')
add('Days claims payable', A['mep'] / A['med'] * 365, lambda y: v(37, y) / v(11, y) * 365, '{:.1f}')
add('Convertible notes, carrying ($m)', A['debt'], lambda y: v(40, y), '{:,.0f}')
add("Stockholders' equity ($m)", A['equity'], lambda y: v(42, y), '{:,.0f}')
add('Cash from operations ($m)', A['cfo'], lambda y: cfo26 if y == '2026E' else v(55, y), '{:,.0f}')
add('Capital expenditure ($m; 2026E second half only)', A['capex'], lambda y: -(M['E57'].value + M['F57'].value) if y == '2026E' else -v(57, y), '{:,.0f}')
add('Cash per share, consolidated ($)', A['cash'] / 204.153619, lambda y: v(29, y) / 215.024483, '{:.2f}')
with open(R('financial_summary.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Line', '2025A', *col]); w.writerows(rows)
for r in rows: print(f"{r[0]:52s} " + '  '.join(f'{x:>9s}' for x in r[1:]))

cons = [
    ('Revenue 2026E ($m)', v(8, '2026E'), 5217.91, 'Yahoo, 17 Oct (11 analysts)'),
    ('Revenue 2027E ($m)', v(8, '2027E'), 6505.68, 'Yahoo, 17 Oct'),
    ('Adj. EBITDA 2026E ($m)', v(16, '2026E'), 148.3, 'S&P Global via MarketScreener'),
    ('Adj. EBITDA 2027E ($m)', v(14, '2027E'), 205.9, 'S&P Global via MarketScreener'),
    ('Adj. EBITDA 2028E ($m)', v(16, '2028E'), 224.6, 'S&P Global via MarketScreener'),
    ('Adj. EPS 2026E ($)', v(25, '2026E'), 0.4525, 'Yahoo, 17 Oct'),
    ('Adj. EPS 2027E ($)', v(25, '2027E'), 0.65, 'Yahoo, 17 Oct (S&P 0.74, 9 Oct)'),
    ('Q3 2026 adj. EPS ($)', M['E25'].value, 0.0425, 'Yahoo, 17 Oct (4 analysts)'),
    ('Q3 2026 revenue ($m)', M['E8'].value, 1313.08, 'Yahoo, 17 Oct (11 analysts)'),
]
with open(R('estimates_vs_consensus.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Line', 'Mine', 'Consensus', 'Difference', 'Source'])
    for lab, m, c, s in cons:
        fm = lambda x: f'{x:.3f}' if abs(x) < 10 else f'{x:,.1f}'
        w.writerow([lab, fm(m), fm(c), f'{m / c - 1:+.1%}', s]); print(f"{lab:26s} mine {m:,.3f} cons {c:,.3f} {m / c - 1:+.1%}")
