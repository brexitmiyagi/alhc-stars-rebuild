"""Every price-linked figure in the Seeking Alpha article, read from the results files, so a price roll is checkable.

Run after price_target.py and event_study.py (same ASOF). Prints the figure the article should carry next to
the phrase it sits in. Figures that do not move with prices (the stars-day move, the September window, the
8 October comparison, the takeout range) are left out.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
R = lambda f: open(os.path.join(HERE, '..', 'results', f)).read()
pt, es = R('price_target.txt'), R('event_study.txt')
ASOF = os.environ.get('ASOF', '2026-10-21')
f = lambda pat, s=pt, g=1: re.search(pat, s).group(g)

price = float(f(r'vs \$([\d.]+) \(premium \$[\d.]+\)\nStreet'))
target = float(f(r'-> \$([\d.]+) \(-?\d+%\)'))
mult = float(f(r'peer-median EV/EBITDA ([\d.]+)x'))
e_after = float(f(r'after stock pay \$([\d.]+)m, net cash'))
before = float(f(r'\d+ Oct: [\d.]+x, \$([\d.]+) vs \$[\d.]+ \(premium'))
adj = float(f(r'stock pay left out\) on the same multiple: \$([\d.]+)'))
per_pt = float(f(r'One point of 2027 MBR: \$([\d.]+)'))
rows = [
    ('close used', f'${price:.2f} ({ASOF})'),
    ('price target (summary, para 4, PT section, close)', f'${target:.2f}'),
    ('downside to target', f'{target / price - 1:.0%}'),
    ('peer-median EV/EBITDA on 2027', f'{mult:.2f} times'),
    ('enterprise value on EBITDA after stock pay', f'about ${mult * e_after:,.0f} million'),
    ('value before the star', f'${before:.2f}'),
    ('stock pay left out', f'${adj:.2f}'),
    ('gap, stock pay left out vs target', f'${adj - target:.2f}'),
    ('stars cost', '$' + f(r'Stars cost per diluted share: \$([\d.]+)')),
    ('discount rate (WACC, base)', f(r'WACC, Alignment beta \(base\): ([\d.]+%)')),
    ('convert check: discount rate / target', f(r'discount rate is ([\d.]+%)') + ' / $' + f(r'; target \$([\d.]+); DCF at 3%')),
    ('DCF at 3% / 4% margin', '$' + f(r'\(Alignment beta \(base\)\): 2\.5% \$[\d.]+, 3% \$([\d.]+)') + ' / $' + f(r'\(Alignment beta \(base\)\): 2\.5% \$[\d.]+, 3% \$[\d.]+, 4% \$([\d.]+)')),
    ('price-implied long-run margin (base)', f(r'\(Alignment beta \(base\)\).*?price-implied long-run margin ([\d.]+%)')),
    ('without CVS and Cigna / without Humana and Molina', '$' + f(r'without CVS and Cigna \(diversified\): [\d.]+x -> \$([\d.]+)') + ' / $' + f(r'without Humana and Molina \(recovering earnings\): [\d.]+x -> \$([\d.]+)')),
    ('EV per member (latest row)', '$' + re.findall(r'\$([\d,]+) a member', pt)[-1]),
    ('one point of cost ratio', f'${per_pt:.2f} a share'),
    ('cost ratio at which value = price', f(r'equals the price: ([\d.]+%)')),
    ('symmetric +/-1.2 pts bear / bull', '$' + f(r'bear 89\.03% \$([\d.]+)') + ' / $' + f(r'bull 86\.63% \$([\d.]+)')),
    ('seasonal carry worth (0.33 pts)', f'about ${0.33 * per_pt:.2f}'),
    ('parent cash only', '$' + f(r'parent only: \$([\d.]+)')),
    ('target at 44% lawsuit odds', '$' + f(r'44% base rate \(rulings counted once\) \$([\d.]+)')),
    ('since 8 Oct vs peers / vs market', '$' + f(r'Stars release to .*?abnormal vs peers [-+\d.]+% \(\$([-+\d.]+)\)', es).lstrip('-+') + ' / $' + f(r'Stars release to .*?market at beta 1\.14 [-+\d.]+% \(\$([-+\d.]+)\)', es).lstrip('-+')),
]
for k, v in rows:
    print(f'{k:55s} {v}')
