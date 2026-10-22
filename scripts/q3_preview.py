"""Prints the October 29 preview table: my pre-registered Q3 2026 estimates (written 17 Oct, track record),
the company's Q2 2026 guidance, and Yahoo Finance consensus pulled 22 Oct 2026. Input: data/q3_preview.csv.
"""
import os
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
t = pd.read_csv(os.path.join(HERE, '..', 'data', 'q3_preview.csv'), dtype=str).fillna('')
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 80)
print(t.to_string(index=False))
open(os.path.join(HERE, '..', 'results', 'q3_preview.txt'), 'w').write(t.to_string(index=False) + '\n')
