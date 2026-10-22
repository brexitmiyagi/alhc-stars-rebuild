"""Pull October 2026 Medicare Advantage enrollment by plan for Los Angeles and Orange County, and the
2026-to-2027 plan crosswalk, out of CMS's files.

Run: python enrollment_extract.py /path/to/cpsc_enrollment_2026_10.zip /path/to/plan_crosswalk_2027.zip
Sources: CMS Monthly Enrollment by Contract/Plan/State/County, October 2026
(https://www.cms.gov/files/zip/monthly-enrollment-cpsc-october-2026.zip) and the 2027 Part C&D Plan Crosswalk
(https://www.cms.gov/files/zip/plan-crosswalk-2027.zip). CMS hides counts under 11 ("*"); those are left out.
Writes data/enrollment_2026_10_la_oc.csv and data/plan_crosswalk_2027_la_oc.csv.
"""
import os, sys, zipfile, io
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, '..', 'data', f)
z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
enr_name = [n for n in names if 'Enrollment_Info' in n][0]; con_name = [n for n in names if 'Contract_Info' in n][0]
enr = pd.read_csv(io.BytesIO(z.read(enr_name)), dtype=str)
enr = enr[(enr.State == 'CA') & enr.County.isin(['Los Angeles', 'Orange'])]
enr['Enrollment'] = pd.to_numeric(enr.Enrollment, errors='coerce')
con = pd.read_csv(io.BytesIO(z.read(con_name)), dtype=str, encoding='latin-1')[['Contract ID', 'Plan ID', 'Parent Organization', 'SNP Plan', 'EGHP', 'Offers Part D']]
out = enr.merge(con, left_on=['Contract Number', 'Plan ID'], right_on=['Contract ID', 'Plan ID'], how='left')
out = out[['Contract Number', 'Plan ID', 'County', 'Enrollment', 'Parent Organization', 'SNP Plan', 'EGHP', 'Offers Part D']]
out.columns = ['contract', 'plan', 'county', 'members_2026_10', 'parent', 'snp', 'eghp', 'part_d']
out.to_csv(D('enrollment_2026_10_la_oc.csv'), index=False)
print(f"{len(out)} plan-county rows, {int(out.members_2026_10.sum()):,} members shown (counts under 11 hidden)")

zc = zipfile.ZipFile(sys.argv[2])
cw_name = [n for n in zc.namelist() if n.endswith('.txt')][0]
cw = pd.read_csv(io.BytesIO(zc.read(cw_name)), sep='\t', dtype=str, encoding='latin-1')
keep = set(zip(out.contract, out.plan))
cw = cw[[(a, b) in keep for a, b in zip(cw.PREVIOUS_CONTRACT_ID, cw.PREVIOUS_PLAN_ID)]]
cw.to_csv(D('plan_crosswalk_2027_la_oc.csv'), index=False)
print(f"{len(cw)} crosswalk rows for plans sold in the two counties; statuses: {cw.STATUS.value_counts().to_dict()}")
