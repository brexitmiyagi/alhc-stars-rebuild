"""Pull hospital inpatient use by payer out of HCAI's Hospital Quarterly Financial and Utilization files.

Run: python hcai_extract.py /folder/with/2024_q3.xlsx ... 2026_q1.xlsx
Source: HCAI via the California Health and Human Services Open Data Portal, "Hospital Quarterly Financial &
Utilization Report - Complete Data Set" (https://data.chhs.ca.gov/dataset/hospital-quarterly-financial-utilization-report-complete-data-set),
quarters Q3 2024 to Q1 2026, the latest published when I pulled them on 22 Oct 2026.
Writes data/hcai_qfur_2024q3_2026q1.csv: one row per hospital per quarter, with discharges and patient days
for traditional Medicare (MCAR) and Medicare managed care, i.e. Medicare Advantage (MCAR_MC), and totals.
"""
import os, sys, glob
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
cols = ['FAC_NO', 'FAC_NAME', 'YEAR_QTR', 'COUNTY_NAME', 'TYPE_HOSP', 'DIS_MCAR', 'DIS_MCAR_MC', 'DAY_MCAR', 'DAY_MCAR_MC', 'DIS_TOT', 'DAY_TOT']
frames = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], '20*_q*.xlsx'))):
    d = pd.read_excel(f, dtype=str)
    frames.append(d[cols])
df = pd.concat(frames)
for c in cols[5:]:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df.columns = [c.lower() for c in df.columns]
df.to_csv(os.path.join(HERE, '..', 'data', 'hcai_qfur_2024q3_2026q1.csv'), index=False)
print(f"{len(df)} hospital-quarters; quarters {sorted(df.year_qtr.unique())}")
