prices_daily_2026_09_08_to_10_21.csv: daily closes from Yahoo Finance's chart API (query1.finance.yahoo.com/v8/finance/chart), pulled 21 Oct 2026 after the close. SPX is the S&P 500 (^GSPC).
prices_2026_10_21_close.csv: the 21 Oct closes from the same pull. It replaces prices_2026_10_21.csv, which I pulled before the close by mistake (differences under 0.5%).
Cross-checks: ALHC 14 Sep 12.94, 16 Sep 8.71, 8 Oct 8.71 and 9 Oct 7.545 match StockAnalysis; RTTNews (9 Oct, 11:26 ET) gives the 8 Oct close as 8.71.

prices_2026_10_22_close.csv and prices_daily_2026_09_08_to_10_22.csv: 22 Oct 2026 closes. Stocks: Nasdaq quote API official 4:00 pm ET close (secondaryData 'Closed at'), pulled 20:07 UTC; Yahoo chart API agrees on ALHC (8.43) and within 0.3% on peers. S&P 500 from Yahoo (^GSPC 7663.43).
