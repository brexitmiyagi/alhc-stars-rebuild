"""Does the simulation's 31% mean anything? Backtest it.

Out-of-sample test: build the transitions from the 2025 -> 2026 ratings only, start from every MA-PD
contract's 2026 measure stars, simulate its 2027 rating under the 2027 rules, and compare with what CMS
actually published in October 2026. Run it twice: measures moving independently, and moving together
through one common factor whose strength (rho) is estimated from the 2025 -> 2026 data.

Two leaks, both small and stated: physical and mental health were display-only in the 2025 ratings, so
their transitions come from 2026 -> 2027; and the three measures new in 2027 (C09, D12, D13) are held at
their actual 2027 stars.
"""
import os, sys, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import recompute_stars as rs
import sim_engine as se

s25, i25 = se.stars_in_2027_codes('measure_stars_2025_compact.txt')
s26, i26 = se.stars_in_2027_codes('measure_stars_2026_compact.txt')
s27 = rs.stars
codes = list(se.LAB27.keys())
T56 = se.transitions(s25, s26, codes)
T67 = se.transitions(s26, s27, codes)
for code in ('C04', 'C05'):            # display-only in 2025
    T56[code] = T67[code]
rho56 = se.estimate_rho(se.pit_normal_scores(s25, s26, T56))
rho67 = se.estimate_rho(se.pit_normal_scores(s26, s27, T67))
print(f"measures mapped 2025->2027 codes: {len(i25)}, 2026->2027: {len(i26)}")
print(f"common-factor correlation rho: 2025->26 {rho56:.3f}, 2026->27 {rho67:.3f}")

pub = {c: float(v[2]) for c, v in rs.pub.items() if v[2] and v[2].replace('.', '', 1).isdigit()}
th = {imp: rs.thresholds_published('overall', imp) for imp in (False, True)}
NEW = ('C09', 'D12', 'D13')
rng = np.random.default_rng(21)
N = 2000
rows = []
for c in sorted(rs.MAPD):
    if c not in s26 or c not in pub: continue
    start = dict(s26[c])
    for m in NEW:
        if m in s27.get(c, {}): start[m] = s27[c][m]
    if len(start) < 20: continue
    p = {}
    for name, rho in (('indep', 0.0), ('corr', rho56)):
        D = se.draw_matrix(start, T56, codes, N, rho, rng)
        for j, m in enumerate(codes):
            if m in NEW and m in start: D[:, j] = start[m]
        r, _ = se.rate_matrix(D, codes, c, th=th)
        p[name] = (r >= 4).mean()
    prev = s26_overall = None
    rows.append((c, p['indep'], p['corr'], 1.0 if pub[c] >= 4 else 0.0))

def report(k, label):
    P = np.array([r[k] for r in rows]); Y = np.array([r[3] for r in rows])
    brier = np.mean((P - Y) ** 2); base = np.mean((Y.mean() - Y) ** 2)
    print(f"{label}: {len(rows)} contracts, Brier {brier:.3f} (climatology {base:.3f}, skill {1-brier/base:.0%})")
    for lo, hi in ((0, .1), (.1, .3), (.3, .5), (.5, .7), (.7, .9), (.9, 1.01)):
        sel = (P >= lo) & (P < hi)
        if sel.sum(): print(f"   predicted {lo:.0%}-{min(hi,1):.0%}: n {sel.sum():3d}, mean predicted {P[sel].mean():.0%}, actually 4+ {Y[sel].mean():.0%}")
    return P, Y

Pi, Y = report(1, 'Independent draws')
Pc, _ = report(2, 'Correlated draws')
# the contracts that look most like H3815's question: in the 25-45% band
for P, label in ((Pi, 'independent'), (Pc, 'correlated')):
    sel = (P >= .15) & (P < .45)
    print(f"Contracts given 15-45% ({label}): n {sel.sum()}, mean predicted {P[sel].mean():.0%}, actually 4+ {Y[sel].mean():.0%}")
with open(os.path.join(HERE, '..', 'results', 'backtest_2027.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['contract', 'p_indep', 'p_corr', 'actual_4plus']); w.writerows(rows)
with open(os.path.join(HERE, '..', 'results', 'rho.txt'), 'w') as f:
    f.write(f"{rho56}\n{rho67}\n")
