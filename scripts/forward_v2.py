"""H3815 forward, with the method that passed the backtest: correlated draws (rho from the data),
2026 -> 2027 transitions, measure sets CMS finalized for the 2028 and 2029 ratings."""
import os, sys, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import recompute_stars as rs
import sim_engine as se

C = 'H3815'
s26, _ = se.stars_in_2027_codes('measure_stars_2026_compact.txt')
codes = list(se.LAB27.keys())
T = se.transitions(s26, rs.stars, codes)
rho = se.estimate_rho(se.pit_normal_scores(s26, rs.stars, T))
D28 = ('C32', 'D01', 'C18')
D29 = D28 + ('C30', 'C31', 'C07', 'C27', 'C28', 'D02', 'D03', 'D07', 'C23', 'C24')
mapd = sorted(rs.MAPD)
base_w = dict(rs.W)
N = 40000
start = dict(rs.stars[C])

def th_for(drop, adh):
    rs.W.update(base_w)
    for m in ('D08', 'D09', 'D10'): rs.W[m] = adh
    t = {imp: rs.thresholds_from_data('overall', imp, drop, mapd) for imp in (False, True)}
    rs.W.update(base_w)
    return t

def dist(r):
    return {'p_4plus': float((r >= 4).mean()), 'p_3_5': float((r == 3.5).mean()), 'p_3_or_less': float((r <= 3).mean())}

out = []
for name, drop, adh, steps, r_ in (('2027 rules (comparison)', (), 3, 1, rho),
                                   ('2028 rules, adherence weight 3', D28, 3, 1, rho),
                                   ('2028 rules, adherence weight 1', D28, 1, 1, rho),
                                   ('2029 rules, two years out', D29, 3, 2, rho),
                                   ('2028 rules, adherence weight 3, independent', D28, 3, 1, 0.0)):
    rng = np.random.default_rng(5)
    D = se.draw_matrix(start, T, codes, N, r_, rng)
    if steps == 2:   # second year: draw again from each first-year outcome, contract by contract
        D2 = np.zeros_like(D)
        for i in range(N):
            st = {codes[j]: int(D[i, j]) for j in range(len(codes)) if D[i, j] > 0}
            D2[i] = se.draw_matrix(st, T, codes, 1, r_, rng)[0]
        D = D2
    r, raw = se.rate_matrix(D, codes, C, drop=drop, th=th_for(drop, adh), weights={m: adh for m in ('D08', 'D09', 'D10')})
    dd = dist(r)
    out.append([name] + [round(dd[k], 4) for k in ('p_4plus', 'p_3_5', 'p_3_or_less')])
    print(f"{name}: P(4+) {dd['p_4plus']:.0%}, P(3.5) {dd['p_3_5']:.0%}, P(3 or less) {dd['p_3_or_less']:.0%}")
print(f"rho used: {rho:.3f}")
with open(os.path.join(HERE, '..', 'results', 'forward_dist_v2.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['scenario', 'p_4plus', 'p_3_5', 'p_3_or_less']); w.writerows(out)
