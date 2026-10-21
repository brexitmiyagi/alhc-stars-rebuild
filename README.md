# alhc-stars-rebuild

This is the data and code behind my October 2026 piece on Alignment Healthcare (ALHC), "The Market Charges Nothing For The Lost Star", and the seven-page research note in `note/` (rating, estimates, financial summary, valuation, risks). Earlier drafts had other titles. See Corrections at the bottom.

On October 8 CMS cut Alignment's California HMO, contract H3815, from 4 stars to 3.5. I wanted to know three things. Why it fell, what the lawsuit can actually fix, and what the lost bonus is worth in dollars. So I rebuilt CMS's 2027 Star Ratings for every contract from the published measure stars, checked the rebuild against everything CMS and the companies published, and then reran H3815 and the whole industry under the measure sets the courts are fighting over.

## How to run it

Python 3 with numpy, scipy and openpyxl (`pip install -r requirements.txt`). Each script finds its inputs relative to its own folder, so you can run them from anywhere. The spreadsheet in `model/` already has its values calculated; to rebuild it, run `build_model_xlsx.py` and open the file in Excel or LibreOffice to recalculate.

```
python3 scripts/tieout.py
python3 scripts/h3815_scenarios.py
python3 scripts/h3815_detail.py
python3 scripts/near_miss.py
python3 scripts/hos_noise.py
python3 scripts/fires_check.py
python3 scripts/industry_table.py
python3 scripts/bonus_dollars.py
python3 scripts/value.py
python3 scripts/chart_data.py
python3 scripts/lose_four_stars.py
python3 scripts/forward_2028.py      # about 3 minutes, writes results/forward_dist.csv
python3 scripts/margin_share.py      # payment-data test of who pays for a lost star
python3 scripts/backtest.py         # out-of-sample check of the simulation (needs scipy)
python3 scripts/forward_v2.py       # the odds in the piece, correlated draws; writes results/forward_dist_v2.csv
python3 scripts/margin_share_robust.py  # stress tests of the margin share
python3 scripts/history_test.py     # event study of past stars cuts at listed insurers
python3 scripts/matrix_backtest.py  # out-of-sample test of the transition matrix
python3 scripts/value_v8.py         # stars-adjusted value in the piece
python3 scripts/valuation_v1.py     # v7 estimates and target (kept for the record)
python3 scripts/build_model_xlsx.py # writes model/ALHC_model.xlsx: quarterly three-statement model, MBR bridge, TNE check, valuation
# open model/ALHC_model.xlsx in Excel or LibreOffice and save, so the formulas calculate
python3 scripts/read_model.py       # prints the model's outputs to results/model_outputs.txt
python3 scripts/ops_model.py        # operating snapshot, Q3 set-up, usable cash, multiples
python3 scripts/ops_model_v6.py     # 2026-2028 bridge, parent liquidity vs the 2029 convertible, peer read-through
python3 scripts/seasonality.py      # first half vs second half cost ratio, 2023-2026
python3 scripts/valuation_bank.py   # v9 target build (kept for the record)
python3 scripts/valuation_v10.py    # the price target now: one primary method, cross-checks, discount rate, backtest, positioning, history
python3 scripts/financial_summary.py # financial summary page and estimates vs consensus
python3 scripts/contract_model.py   # contract-level model: members, stars, bonus status, revenue by contract; writes model/ALHC_contract_model.xlsx
# older: forward_2028.py, value_v3.py ... value_v7.py are kept for the record
```

The output of my own run is in `results/`, one text file per script.

## What each script gives you

- `recompute_stars.py` rebuilds summary and overall ratings from the measure stars, the weights, the reward factor, the CAI adjustment and CMS's rounding. Run on its own it prints the tie-out: 503 of 508 drug-plan overall ratings and 514 of 515 Part C ratings match what CMS published.
- `tieout.py` fails loudly if any of the checks break. The rebuild has to match CMS on 99% of contracts and on all three of H3815's ratings. It has to land on CMS's fact sheet (188 drug-plan contracts at 4 stars or more, about 71% of their members), on Humana's 95% and on Aetna's "more than 69%". And without the 10 measures it has to give the same four ratings Alignment's October 9 complaint claims: H3815 at 4.0, H8832, H3443 and H9686 at 4.5.
- `h3815_scenarios.py` reruns H3815 as published (raw 3.37, so 3.5 stars), without the 10 measures in the lawsuit (4.07, so 4.0), without all 19 Clover measures, and with only HEDIS, HOS and CAHPS measures, which is close to what CMS did in June (3.34, still 3.5).
- `h3815_detail.py` shows both improvement-measure paths, the reward factor tests, the 3.86 you get with physical and mental health back at their 2026 weight of 1, and which measures drag the score down most (physical and mental health, 0.094 each).
- `near_miss.py` reads CMS's cut points and finds the smallest score change that keeps 4 stars: one point on physical health and three on mental health.
- `hos_noise.py` tests how repeatable the measures are. Year-on-year correlation is 0.24 for physical health and 0.20 for mental health, against 0.95 for breast cancer screening and 0.85 for reducing falls. H3815's 13-point drop on physical health is the largest of 253 contracts. It also works out the 66% odds that H3815 is back at 4 stars next year if only those two measures move.
- `fires_check.py` checks the Los Angeles fires. The other 14 contracts with at least 10% of members in 2025 disaster areas moved between minus 7 and plus 8 points on physical health.
- `industry_table.py` weights everything by CMS's October 2026 enrollment, turns crossings of the 4-star line into rebate dollars at each contract's own risk score, and writes the table by parent company plus the list of 59 contracts that cross.
- `bonus_dollars.py` works out what 4 stars is worth on H3815: $205.6m a year of benchmark lift, $133.6m of it as rebate dollars to the plan, and about $52.9m in 2027 if the 2026-ratings case wins.
- `value.py` turns that into dollars a share and prints the grid in the piece. Central case $8.49; the $8.15 price needs 129% of the lost rebate to come out of profit at 30% lawsuit odds.
- `chart_data.py` writes the CSVs behind the charts.
- `margin_share.py` uses CMS Plan Payment Data (Part C, plan level, payment years 2019-2024) for 108 contracts that fell from 4 stars to 3.5 in the 2019-2023 ratings. Their rebates per member fell by a median 26% of what the rebate formula implies (bootstrap 90% interval 13% to 35%), against same-year contracts that held 4 stars. The other 74% went into lower bids. Rating labels were checked against the separate 2019-2027 star file: 0 mismatches in 685.
- `backtest.py` builds the simulation only from the 2025 -> 2026 ratings and predicts every MA-PD contract's 2027 rating. With measures moving together through one common factor (correlation 0.084, estimated from the data), it is calibrated: contracts given 15-45% averaged 29% and 30% reached 4 stars (132 contracts). Independent draws were overconfident at both ends.
- `forward_v2.py` runs H3815 with the backtested method: 39% back to 4 stars on this year's rules, 32-38% on next year's measure set, 22-25% down to 3 stars; two years out, 39% at 3 or lower.
- `value_v5.py` puts it together with a 74% margin share and 25% lawsuit odds: stars cost $0.97 a share for 2028-2030 payments; the $0.43 fall since October 8 implies the market had already priced about 56% odds. Fair value about $8.25.
- `ops_model.py` gives the operating snapshot (guidance, consensus-implied 2027 EBITDA, multiples), the Q3 set-up (prior-year development, days claims payable, IBNR) and the cash the parent can actually use ($135.4m at June 30).
- `valuation_v10.py` is the price target in the valuation note. One primary method: peer-median forward EV/EBITDA on 2027 (10.35x on S&P Global consensus EBITDA, consolidated net debt), on Alignment's EBITDA after stock pay ($129.3m), with Alignment's cash netted the way the peers' is, over 215.0m diluted shares held flat so stock pay is counted once, less the stars cost: $6.96. Checks: P/E ($3.45), a DCF ($13.48 at 8.84%, built from the 10-year Treasury, Damodaran's premium and Alignment's beta), stock pay left out ($10.64), the Molina-Bright deal, peer-set and cash choices, symmetric scenarios, the 2026 guidance arithmetic, a backtest of the cost-ratio bridge on 2025 and 2026 (off by 0.2 and 2.6 points), stock pay against peers, positioning and valuation history.
- `contract_model.py` splits Alignment by Medicare contract from CMS's October 2026 enrollment file, the 2027 Star Ratings and the 2027 rate book. H3815 has 225,609 of 301,157 members (75%) and about $4.9bn of my $6.5bn 2027 revenue; every other rated contract is at 4 stars or more; members in bonus-earning contracts fall from nearly all in 2027 payments to 25% in 2028. Revenue is allocated by members x county benchmark, which assumes similar risk scores and bids across contracts.
- `financial_summary.py` writes the 2025-2028 financial summary and the estimates-vs-consensus table used in the note.
- `valuation_bank.py` was the v9 target (three methods averaged); kept for the record. It values my 2027 numbers three ways: peer-median forward P/E (14.5x on Yahoo adjusted EPS), peer-median forward EV/EBITDA (10.3x on S&P Global consensus 2027 EBITDA from MarketScreener, with consolidated net debt) and a DCF to 2036. Stock pay is expensed because the peers' numbers are after it, and Alignment's cash is netted the same way as the peers'. It prints every other choice too: $9.59 with stock pay left out, about $6.20 with parent-only cash, $6.67 weighted across the cost-ratio cases, the margin the price implies in the DCF, the growth-adjusted P/E, and the Molina-Bright takeout check. Base $7.10.
- `seasonality.py` shows Alignment's second-half cost ratio came in below the first half in 2023, 2024 and 2025 (by 1.05, 1.84 and 0.07 points), against about 1.0 point above in this year's guidance and 1.35 in my quarters.
- `forward_2028.py` (first version, independent draws) runs H3815 under the measure sets CMS finalized in its CY2027 rule (91 FR 17384, April 6 2026). The call center measures and statin therapy leave the 2028 ratings; appeals, complaints, members leaving, SNP care management, Plan Finder accuracy, customer service and rating of health care quality leave in 2029. With this year's measure stars held, H3815 scores 3.27 on the 2028 set and 3.17 on the 2029 set, which is 3 stars. It then draws every measure's next star from what happened to contracts with the same star between the 2026 and 2027 ratings: back to 4 stars in 22% to 29% of draws, down to 3 in 12% to 15%. It also prints the plain base rate: of 184 contracts that fell from 4+ to 3.5 in the 2023 to 2026 ratings, 35% were back the next year.
- `value_v3.py` values the stars hit as a path of payment years (2028 to 2032), with a 3-star state where the rebate share drops from 65% to 50% (42 CFR 422.266). Central case $7.49; grid $6.07 to $8.17.
- `value_v4.py` was the value in the v4 draft. It values lost rebate for 2028-2030 payments only, holds membership flat, and asks how much of the downgrade the October 8 price already held (management had its preliminary ratings by September 15 and declined to discuss them). Stars cost $0.67 a share; fair value $8.04 if the price held none of it, $8.38 at even odds.
- `margin_share_robust.py` stress-tests the 26%: enrollment-weighted 23%, matched on A/B payment quintile 23%, contracts with 5+ plans 20%, a placebo one year before the change 6% (90% interval -4% to 15%), and 45% in the second payment year below 4 stars (25 contracts). It also prints H3815's own episode: when its rebate share fell from 70% to 65% for 2022 it cut member rebates by $23.05 a month against a $15.30 formula cut, 1.5 times the formula.
- `value_v6.py` adds a horizon past 2030 and an outside prior, but charges H3815 for every future year below 4 stars. Superseded by v7.
- `value_v7.py` was the value in the v6 draft. The cost of the downgrade is the present value of H3815's downgraded path less the path where it kept 4 stars, both run through a transition matrix for contracts with H3815's record (748 contract-years) after the simulated 2028 and 2029 ratings. Path A (industry margin pattern) $0.92 a share; Path B (Alignment's 2022 pattern) $0.22 to $0.42. Prior 31% to 50% from the pre-ratings model. Fair value $8.07 to $8.60, central $8.34.
- `history_test.py` finds the ten cases since 2019 where a listed insurer's share of members in 4+ star plans fell 10 points or more in one release and measures each stock against the other listed managed-care names (prices in `data/stars_cut_events.csv`, Yahoo adjusted closes pulled 17 Oct 2026). CVS 2022: -9.2% vs peers, about $12bn, 12-15x the $0.8-1.0bn one-year hit it later disclosed; its stars came back the next year. Diversified parents: -3.6% to +3.1%.
- `matrix_backtest.py` trains the transition matrix on 2023-2025 transitions only and predicts the 2025 cohorts: gap between dropped and held contracts predicted 41 and 21 points one and two years out, actual 39 and 20. Over three years the full matrix closes the gap too fast (13 points vs 23-35 actual for the 2023 and 2024 cohorts), which is why value_v8.py uses the observed decay.
- `value_v8.py` is the stars-adjusted value in the piece: v7 plus the observed gap decay (0.84 a year after 2030) and member economics by tenure (new members about -$290 of EBITDA a year for two years, mature about +$1,315, from management's $880m embedded gross profit vs $640m guidance midpoint). Blend cost $0.94; value $7.83-$8.51, central $8.15.
- `valuation_v1.py` gives my Q3, FY2026-2028 estimates against guidance and consensus, the price target ($7.85 base, $4.22 bear, $10.82 bull) from peer-median forward P/E and EV/EBITDA less the stars cost, and the 2027 medical benefit ratio the price implies (87.8% now vs 86.6% at the Sep 14 close, at today's peer multiples). Inputs in `data/valuation_inputs.csv`.
- `model/ALHC_model.xlsx` (built by `build_model_xlsx.py`) is the model in the piece. Inputs sheet: every hardcoded number in blue with its source. MBR Bridge: 2026E ratio, member maturity (share of members in year 1-2 from growth and retention; new-vs-mature gap from management's $880m vs $640m gross profit), rate (+4.98%) vs CMS effective growth rate (5.33%), 2027 benefit trims, carried H2-2026 pressure; bear 89.3%, base 87.8%, bull 87.0%. Model: Q1'26-Q4'28 members x revenue per member, cost ratio, SG&A, adj. EBITDA, D&A, interest, stock comp, tax, net income, adj. EPS, balance sheet and cash flow (checks to zero every quarter). Statutory Capital: California TNE requirement under the Knox-Keene formula quoted in the 10-Q, against a rough regulated net worth. Valuation: peer forward P/E and approximated forward EV/EBITDA (now and at 14 Sep prices), the target, scenarios, a P/E x MBR grid and the price-implied 2027 MBR (87.4% now, 86.1% on 14 Sep).
- `data/landscape_*.csv`: 2026 vs 2027 plan benefits in Los Angeles and Orange County from CMS's landscape files (see landscape_README.txt).
- `data/peers_2026_10_16.csv`: peer prices (16 Oct and 14 Sep), shares, EV, TTM EBITDA and consensus EPS from Yahoo Finance.
- `ops_model_v6.py` gives the 2026-2028 bridge, the 2027 rate notice, the parent's cash against the $330m convertible ($208m vs $379m of principal and coupons) and the UnitedHealth read-through.
- `lose_four_stars.py` checks what happened to membership at every contract that fell below 4 stars between the 2020 and 2025 ratings. In the year the lower bonus hits benefits, those contracts grew a median 5.1 points slower than contracts that held 4 stars (207 cases). The year the lower star only shows up on the label, the gap is 0.7 points.

## Data

- `measure_stars_2027.csv`, `measure_data_2027.csv`, `summary_ratings_2027.csv`, `cai_2027.csv`, `part_c_cut_points_2027.csv`: CMS 2027 Star Ratings Data Tables (Oct 8 2026), unchanged.
- `measure_weights_2027.csv`, `reward_thresholds_2027.csv`, `cai_values_2027.csv`: typed from the 2027 Technical Notes (Attachment G, Tables 8 and 9, Tables 12, 15 and 18).
- `contested_measures.csv`: the two groups of 10 from the Clover ruling, mapped to 2027 measure IDs. MTM completion was in the data-source group and is off the 2027 ratings, so that group has 9 here.
- `enrollment_by_contract_2026_10.csv`: CMS Monthly Enrollment by Contract, October 2026, unchanged.
- `contract_county_rates_2027.csv`: for each contract, its October 2026 county enrollment (CMS state/county/contract file) and the enrollment-weighted 0% bonus rate and bonus lift from the 2027 MA rate book. The county file is big, so I built this in the browser. Checksums are in `tieout.py`, and I spot-checked six contracts against a second pull.
- `hos_and_controls_2026.csv`: 2026 scores and stars for physical health, mental health, breast cancer screening and falls, from the 2026 Star Ratings Data Tables. Also built in the browser and checksummed. A second pull matched it exactly (513 rows, sum 113,732).
- `h3815_plans_2024.csv`: H3815's 22 plans from CMS's 2024 Plan Payment Data (average A/B payment, Part C risk score, rebate) with July 2024 plan enrollment.
- `risk_scores_2024_crossing_contracts.csv`: the same risk scores, enrollment-weighted, for every contract that crosses the 4-star line. Two are too new to have 2024 data and get 1.0.
- `measure_stars_2026_compact.txt`: every contract's measure stars from the CMS 2026 Star Ratings Data Tables (Measure Stars file), one character per measure in the order of the NAMES line, "." for no star. 769 contracts; the stars sum to 78,480.
- `stars_and_enrollment_2019_2027.csv`: overall star rating (Part C summary for plans without drug coverage) for each contract in the 2019 to 2027 ratings, with February enrollment for 2019 to 2026 from CMS Monthly Enrollment by Contract. 651 contracts. The cell values sum to 234,300,254.5.
- `rebate_cases_2019_2023.csv`: contract-level average rebate and A/B payment per member from CMS Plan Payment Data, for contracts that held or changed 4-star status, with the rating-year group. 850 rows; r0 + r1 + ab0 sum to 916,058.00.
- `measure_stars_2025_compact.txt`: MA contracts' measure stars from the 2025 Star Ratings Data Tables (Dec 2 2024 version). 672 contracts; stars sum to 72,446.
- `rebate_prev_2019_2023.csv`: the same contracts' rebate one payment year earlier, for the placebo test. r_prev sums to 77,906.16.
- `rebate_year2_2019_2022.csv`: rebate two payment years after the change, for the second-year test. 264 rows, 262 with values.
- `alhc_operating_inputs.csv`: every company and market input to ops_model.py and ops_model_v6.py with its source.
- `alhc_inputs.csv`: prices, share count, cash, debt, guidance and NOLs, each with its source.

## Sources

- Betas, short interest, Street targets and ratings: Yahoo Finance quoteSummary (17 Oct 2026), cross-checked on finviz; borrow fee: https://www.iborrowdesk.com/report/ALHC
- CMS Rate Announcements: 2025 https://www.cms.gov/newsroom/fact-sheets/2025-medicare-advantage-and-part-d-rate-announcement ; 2026 https://www.cms.gov/newsroom/fact-sheets/2026-medicare-advantage-part-d-rate-announcement
- Peer stock pay and revenue: SEC XBRL companyconcept API (FY2025 10-Ks)

- Alignment 10-K FY2025, regulatory capital note: https://www.sec.gov/Archives/edgar/data/1832466/000162828026012545/R18.htm and parent-only schedule: https://www.sec.gov/Archives/edgar/data/1832466/000162828026012545/R22.htm
- Quarterly statements of operations (10-Q and 10-K XBRL R pages, 2024 to 2026), listed in `data/quarterly_mbr_2023_2026.csv`
- Peer consensus 2027 EBITDA and net debt: MarketScreener finances pages (S&P Global consensus), e.g. https://www.marketscreener.com/quote/stock/UNITEDHEALTH-GROUP-INC-14750/finances/
- 10-year Treasury yield: https://fred.stlouisfed.org/series/DGS10 ; implied equity risk premium: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm
- Bright Health sale to Molina: https://www.sec.gov/Archives/edgar/data/1671284/000167128424000007/ex-991proformafinancials.htm and Molina's 8-K of 2 Jan 2024: https://molinahealthcare.gcs-web.com/node/23166/html

- CMS Part C and D performance data (Star Ratings data tables, Technical Notes, fact sheet): https://www.cms.gov/medicare/health-drug-plans/part-c-d-performance-data
- CMS 2027 Technical Notes: https://www.cms.gov/files/document/2027-tech-notes-2026-09-30.pdf
- CMS 2027 Star Ratings fact sheet: https://www.cms.gov/files/document/fact-sheet-2027-ma-part-d-star-ratings-october-8-2026.pdf
- CMS Monthly Enrollment by Contract: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-enrollment-contract
- CMS Monthly MA Enrollment by State/County/Contract: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-ma-enrollment-state/county/contract
- CMS Monthly Enrollment by Plan: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-enrollment-plan
- CMS Plan Payment Data (2024): https://www.cms.gov/medicare/health-drug-plans/plan-payment-data
- CMS 2027 MA rate book: https://www.cms.gov/medicare/payment/medicare-advantage-rates-statistics/ratebooks-supporting-data/2027
- Alignment 8-K, October 8 2026: https://www.sec.gov/Archives/edgar/data/1832466/000162828026065470/alhc-20261008.htm
- Alignment Q2 2026 results: https://www.sec.gov/Archives/edgar/data/1832466/000117184326005078/exh_991.htm
- Alignment v. HHS, 1:26-cv-02441 (2026 ratings, D.D.C.): https://www.courtlistener.com/docket/73603819/alignment-healthcare-inc-v-department-of-health-and-human-services/
- Alignment v. HHS, 1:26-cv-03550 (2027 ratings, D.D.C.): https://www.courtlistener.com/docket/74944965/alignment-healthcare-inc-v-department-of-health-and-human-services/
- KFF on the quality bonus program and its method: https://www.kff.org/medicare/medicare-will-spend-more-than-13-billion-on-the-medicare-advantage-quality-bonus-program-in-2026/
- Crowell on the Clover ruling and the two groups of measures: https://www.crowell.com/en/insights/client-alerts/clover-insurance-v-hhs-sd-of-georgia-holds-20-star-ratings-measures-unlawful

## More sources

- CMS Plan Payment Data, 2018-2024: https://www.cms.gov/medicare/health-drug-plans/plan-payment-data
- MedPAC, Medicare Advantage payment basics (rebate on the risk-adjusted benchmark): https://www.medpac.gov/wp-content/uploads/2024/10/MedPAC_Payment_Basics_24_MA_FINAL_SEC.pdf
- Georgetown Health Care Litigation Tracker, star ratings cases: https://litigationtracker.law.georgetown.edu/issues/star-ratings/
- Alignment Q2 2026 10-Q: https://www.sec.gov/Archives/edgar/data/1832466/000162828026051060/alhc-20260630.htm
- Alignment 8-K on the 2029 convertible notes (Nov 25 2024): https://www.sec.gov/Archives/edgar/data/1832466/000162828024049159/alhc-20241122.htm
- UnitedHealth Q3 2026 release: https://www.sec.gov/Archives/edgar/data/731766/000073176626000255/earningsrelease3q26unh.htm
- Humana 8-K, October 9 2026: https://www.sec.gov/Archives/edgar/data/49071/000004907126000057/hum-20261009.htm
- Alignment Q3 2025 results (8-K exhibit 99.1): https://www.sec.gov/Archives/edgar/data/1832466/000117184325006831/exh_991.htm
- Alignment Q2 2026 call summary (embedded gross profit, member tenure, Q3 guidance): https://www.marketbeat.com/instant-alerts/alignment-healthcare-q2-earnings-call-highlights-2026-07-30/
- Alignment 2027 expansions: https://www.globenewswire.com/news-release/2026/10/15/3381676/0/en/alignment-health-expands-medicare-advantage-coverage-to-san-antonio-for-2027.html and https://www.globenewswire.com/news-release/2026/10/13/3379626/0/en/alignment-health-expands-medicare-advantage-coverage-to-four-new-charlotte-area-counties-for-2027.html
- CVS 2024 stars cost ($0.8-1.0bn): https://www.healthcaredive.com/news/cvs-income-hit-ma-star-ratings-drop/651408/
- CMS CY2027 and CY2026 Landscape files: https://www.cms.gov/medicare/coverage/prescription-drug-coverage
- CMS CY2027 Rate Announcement fact sheet (effective growth rate 5.33%, +2.48%/+4.98%): https://www.cms.gov/newsroom/fact-sheets/2027-medicare-advantage-part-d-rate-announcement
- CMS RADV expansion (21 May 2025): https://www.cms.gov/newsroom/press-releases/cms-rolls-out-aggressive-strategy-enhance-and-accelerate-medicare-advantage-audits
- Court vacates 2023 RADV rule (Humana v. Becerra, 25 Sep 2025): https://www.crowell.com/en/insights/client-alerts/court-vacates-cmss-2023-final-rule-on-radv-audits
- Molina exits MAPD for 2027: https://www.fiercehealthcare.com/payers/molina-healthcares-stocks-fall-company-plans-exit-medicare-advantage
- CMS star ratings release dates: CMS fact sheets for 2021 (Oct 8 2020), 2023 (Oct 6 2022), 2024 (Oct 13 2023), 2025 (Oct 10 2024) ratings; 2020 ratings Oct 9 2019 per Avalere's citation of the CMS fact sheet

## Things to be careful with

- `valuation_v10.py`: betas move a lot with the window. Yahoo's 5-year monthly beta for Alignment is 1.14; my 2-year weekly regression gives 0.49. The peer median (0.71) gives a 7.33% WACC and a much higher DCF. The bridge backtest uses year-end members, an 88% retention assumption and management's 2026 new-vs-mature gap for every year. Valuation history uses next-year actuals or my estimates, not historical consensus, which isn't available free.
- I couldn't retrieve California's hospital utilization data (HCAI) or the per-plan DMHC filings: both sites block access from my location.

- `valuation_bank.py`: the DCF's growth path (14% fading to 3%), the 3% long-run margin, the 10% discount rate and the assumption that the claims float and regulatory capital growth offset are my judgement. The peer EBITDA consensus pages on MarketScreener carry quotes dated 15 Sep to 16 Oct; the dates are in `data/peers_consensus_2026_10.csv`. The takeout precedent is one deal and the seller was distressed.
- I couldn't retrieve the per-plan statements Alignment files with California's regulator (DMHC), so the capital check uses the aggregate in the 10-K.

- The dollars use 2024 risk scores and rebates, the latest CMS has published, and 2027 county rates standing in for 2028.
- Regional PPO contracts are paid on regional benchmarks. I used their county mix anyway. Only one of them (R0110, about $16m) crosses the line.
- When I take measures out I keep CMS's published CAI values. CMS would recompute them. The effect is a few hundredths of a star.
- I can't recompute the improvement measures on a new measure set. For H3815 it doesn't matter, because the path without them is the one that clears 4.0.
- My re-derived reward thresholds run a little above CMS's published ones. I show both.
- "CMS's June approach" is my approximation: HEDIS, HOS and CAHPS measures only.
- The 66% recovery odds come from 14 and 31 contracts and hold everything else still.
- `valuation_v1.py` assumptions: 2027 revenue $6.5bn, adj. SG&A 9.0% of revenue, 24% normalized tax, NOLs used over about 4 years, 2028 revenue +15%. Each point of 2027 MBR moves the target about $3.30.
- The equal weight on Path A and Path B in `value_v7.py` and `value_v8.py` is my judgement; Path B rests on one Alignment episode. The 25% lawsuit odds, the 50% margin share, the 10% discount rate and the odds already in the October 8 price in `value_v4.py` are my judgement. Change them and rerun.
- `forward_2028.py` draws each measure on its own. If a plan's measures move together, outcomes spread wider on both sides. Cut points are not rerun; the transitions carry last year's cut-point drift.
- CMS hasn't said what weight the newly risk-adjusted Part D adherence measures get in the 2028 ratings. Consultants say 1 for a year. The script runs weight 1 and weight 3.
- CY2027 final rule: https://www.federalregister.gov/documents/2026/04/06/2026-06600/ (text used from govinfo.gov, FR-2026-04-06/2026-06600).

## Corrections

- 22 October 2026, before publication. Prices rolled to the 21 October close (`data/prices_2026_10_21.csv`; consensus rechecked, unchanged) and the 10-year Treasury to 5.15%. Target $7.20 at $8.45 (was $7.00 at $8.28). The multiple is now quoted on the 215.0m diluted shares the target uses (11.2x against a 10.73x peer median); earlier drafts quoted 10.4x on basic shares.

- 17 October 2026, v10, before publication. After a critical review of v9: my 2027 estimates match consensus, so the Sell rested on a valuation convention. The target now comes from one primary method instead of an average, shares are held at 215.0m so stock pay isn't counted twice, the discount rate is derived from betas, scenarios are symmetric, and the cost-ratio bridge was backtested (it missed 2026 by 2.6 points). Rating Hold with a negative skew, target $7.00 (was Sell, $7.10). The model's Valuation sheet is marked superseded.

- 17 October 2026, v9, before publication. v8 said Alignment doesn't disclose its regulatory capital and estimated about $430m of regulated net worth. The 10-K does disclose it: $268.5m at the end of 2025 against a $116.1m minimum, with $72.9m payable to the parent without approval. The Statutory Capital sheet in the model now starts from the filed number. The price target is now built in `valuation_bank.py` (P/E, EV/EBITDA on real consensus EBITDA, and a DCF, with stock pay expensed and cash treated the same as the peers); the Valuation sheet in the model is the v8 method and is kept for the record. The target is still $7.10 and the rating Sell (moderate).

- 17 October 2026, before publication. My earlier draft said H3815 had about a 66% chance of being back at 4 stars in the 2028 ratings, and valued the stock at $8.49 (Hold). That number let only the two survey measures move and kept the 2027 measure set. Moving every measure and using the 2028 measure set CMS has already finalized gives 22% to 29%. The value is now $7.49 and the rating is Sell. `hos_noise.py` and `value.py` are kept so the old numbers can be checked. The 66% line in `hos_noise.py` is the superseded figure.
- 17 October 2026, v5. The three inputs that drove v4 are now measured: margin share from payment data, odds from a backtested correlated simulation, and the market's prior from the price. The 26-29% odds from forward_2028.py (independent draws) are superseded by forward_v2.py.
- 17 October 2026, later the same day, before publication. A Sell at $7.50 (value_v3.py) was withdrawn. It started from the October 8 price as if that price held no chance of a downgrade, ran losses to 2032, and grew membership 5% a year while arguing the downgrade slows growth. value_v4.py fixes all three; the rating is Hold.
- 17 October 2026, v8, before publication. Peer EV/EBITDA is now forward (approximated from consensus EPS) instead of trailing, the September implied cost ratio uses September peer prices, revenue is built from members x revenue per member (with the January enrollment step), and the 2027 cost ratio comes from a bridge instead of an assumption. The target moved from $7.85 to $7.10 and the rating from Hold to Sell (moderate).
- 17 October 2026, v7, before publication. The fair value was relabeled: $8.15 is a stars-adjusted value, and the 12-month price target ($7.85) now comes from estimates and peer multiples. The transition matrix was backtested and found to close the gap too fast after two years, and growth is now valued by member tenure; both raise the stars cost (blend $0.62 -> $0.94).
- 17 October 2026, v6, before publication. value_v6.py charged H3815 for every future year below 4 stars, including years a 4-star plan would also have spent below 4. value_v7.py values only the difference from the 4-star path, which cuts the industry-pattern cost from $3.19 to $0.92 a share. The prior now comes from the pre-ratings model, not the price. Fair value $8.35, Hold.
- The 30% lawsuit odds are now 25%, after reading the government's cross-motion in 1:26-cv-02441.

## License

MIT. Data files are public CMS, SEC and market data as cited above.
