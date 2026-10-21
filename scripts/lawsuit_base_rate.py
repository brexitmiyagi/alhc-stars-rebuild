"""How often plans win star-ratings cases, so the lawsuit odds in the stars cost have a base rate.

Reads data/star_ratings_cases.csv: district-court star-ratings cases with a decision, from the Georgetown
Health Care Litigation Tracker (litigationtracker.law.georgetown.edu/issues/star-ratings/, read 21 Oct 2026)
checked against news coverage of each ruling. Pending cases (Alignment's 2026 and 2027 suits, SCAN 2026,
CareFirst, Healthfirst, Elevance 2026, the appeals) are left out.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
c = pd.read_csv(os.path.join(HERE, '..', 'data', 'star_ratings_cases.csv'))
known = c[c.outcome != 'unclear']
wins = known.outcome.str.startswith('relief').sum()
print(c[['plaintiff', 'rating_year', 'court', 'outcome']].to_string(index=False))
lines = [f"Decided with a known outcome: {len(known)}; plan got relief in {wins} ({wins / len(known):.0%}); {len(c) - len(known)} unclear",
         "Wins came on errors in how CMS ran its own method or on measures it had no authority to use; losses came on plan-specific facts.",
         "Alignment's 2027 case asks for 10 measures to be struck (the Clover theory). Clover is on appeal, and CMS's own June recalculation",
         "on HEDIS, HOS and CAHPS only still leaves H3815 at 3.34, so 3.5 stars (h3815_scenarios.py). I keep 25% odds, below the base rate."]
for l in lines: print(l)
open(os.path.join(HERE, '..', 'results', 'lawsuit_base_rate.txt'), 'w').write('\n'.join(lines) + '\n')
