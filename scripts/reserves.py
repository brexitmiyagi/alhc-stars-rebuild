"""Reserve quality: days claims payable, the unpaid-claims cushion, and prior-year development by quarter.

Reads data/reserves_quarterly.csv (SEC XBRL plus the 10-Q reserve notes) and data/quarterly_mbr_2023_2026.csv.
Days claims payable = medical expenses payable / (quarterly medical expenses / days in the quarter).
The unpaid-claims days use only the claims-incurred-but-not-paid line, the part that is an actuarial estimate;
the rest of the payable is capitation and risk-sharing owed to provider groups.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, '..', 'data', f)
res = pd.read_csv(D('reserves_quarterly.csv'), parse_dates=['quarter_end'])
mbr = pd.read_csv(D('quarterly_mbr_2023_2026.csv'))
q = mbr[mbr.quarter != 'FY'].copy(); q['quarter'] = q.quarter.astype(int)
fy = mbr[mbr.quarter == 'FY'].set_index('year')
for y in fy.index:
    have = q[q.year == y]
    if len(have) == 3:
        q = pd.concat([q, pd.DataFrame([{'year': y, 'quarter': 4, 'revenue_kusd': fy.loc[y, 'revenue_kusd'] - have.revenue_kusd.sum(),
                                         'medical_expenses_kusd': fy.loc[y, 'medical_expenses_kusd'] - have.medical_expenses_kusd.sum()}])])
q['quarter_end'] = pd.to_datetime([f"{y}-{3 * k:02d}-01" for y, k in zip(q.year, q.quarter)]) + pd.offsets.MonthEnd(0)
df = res.merge(q[['quarter_end', 'medical_expenses_kusd']], on='quarter_end')
df['days'] = (df.quarter_end - (df.quarter_end - pd.offsets.QuarterEnd(1))).dt.days
daily = df.medical_expenses_kusd / 1e3 / df.days
df['dcp_days'] = df.medical_expenses_payable_musd / daily
df['unpaid_claims_days'] = df.claims_incurred_not_paid_musd / daily
open_bal = {y: df[df.quarter_end == f"{y - 1}-12-31"].claims_incurred_not_paid_musd.squeeze() for y in (2024, 2025, 2026)}
df['pyd_pct_of_opening'] = [p / open_bal[d.year] * 100 if pd.notna(p) else None for p, d in zip(df.pyd_ex_pad_quarter_musd, df.quarter_end)]
out = df[['quarter_end', 'medical_expenses_kusd', 'medical_expenses_payable_musd', 'dcp_days', 'claims_incurred_not_paid_musd', 'unpaid_claims_days', 'pyd_ex_pad_quarter_musd', 'pyd_pct_of_opening']].round(2)
pd.set_option('display.width', 200)
print(out.to_string(index=False))
out.to_csv(os.path.join(HERE, '..', 'results', 'reserves.csv'), index=False)

last = df.iloc[-1]; prev = df.iloc[-2]
y24 = df[df.quarter_end.dt.year == 2024]
lines = [
    f"Days claims payable: 2024 range {y24.dcp_days.min():.1f}-{y24.dcp_days.max():.1f}; peak {df.dcp_days.max():.1f} at {df.loc[df.dcp_days.idxmax(), 'quarter_end']:%b %Y}; now {last.dcp_days:.1f}",
    f"Unpaid-claims days: 2024 range {y24.unpaid_claims_days.min():.1f}-{y24.unpaid_claims_days.max():.1f}; {prev.unpaid_claims_days:.1f} in Mar 2026, {last.unpaid_claims_days:.1f} in Jun 2026",
    f"One day of medical expenses in Q2 2026: ${last.medical_expenses_kusd / 1e3 / last.days:.1f}m",
    f"Prior-year development ex-PAD: 2024 ${df[df.quarter_end.dt.year == 2024].pyd_ex_pad_quarter_musd.sum():.1f}m favorable, 2025 ${df[df.quarter_end.dt.year == 2025].pyd_ex_pad_quarter_musd.sum():.1f}m, "
    f"Q1 2026 ${prev.pyd_ex_pad_quarter_musd:+.1f}m, Q2 2026 ${last.pyd_ex_pad_quarter_musd:+.1f}m (first unfavorable quarter in the series)",
    "Prior-year claims paid in the first half: 2025 $127.1m against a $168.4m opening balance (76%); 2026 $245.4m against $297.4m (83%) (10-Q Q2 2026 reserve table)",
]
for l in lines: print(l)
open(os.path.join(HERE, '..', 'results', 'reserves.txt'), 'w').write(out.to_string(index=False) + '\n' + '\n'.join(lines) + '\n')
