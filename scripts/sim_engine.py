"""Shared pieces for the star simulations: measure-name mapping across years, empirical transitions,
a Gaussian-copula draw (measures move together through one common factor), and a vectorised rating."""
import os, re
import numpy as np
from scipy.stats import norm
import recompute_stars as rs

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')

def load_compact(name):
    L = open(os.path.join(DATA, name)).read().strip().split('\n')
    names = [n.split(': ', 1)[1] for n in L[0].split(';')[1:]]
    parts = [n.split(':')[0][0] for n in L[0].split(';')[1:]]
    out = {}
    for line in L[1:]:
        cid, s = line.split(',')
        out[cid] = {i: int(ch) for i, ch in enumerate(s) if ch.isdigit()}
    return names, parts, out

LAB27 = {}
for lab in rs.labels:
    m = re.match(r'\s*([CD]\d\d):\s*(.*)', lab)
    if m: LAB27[m.group(1)] = m.group(2)
norm_name = lambda t: re.sub(r'[^a-z]', '', t.lower().replace('â€“', ''))[:22]

def map_to_2027(names, parts):
    idx = {}
    for code, nm in LAB27.items():
        for i, n in enumerate(names):
            if norm_name(n) == norm_name(nm) and parts[i] == code[0]:
                idx[code] = i; break
    return idx

def stars_in_2027_codes(fname):
    names, parts, d = load_compact(fname)
    idx = map_to_2027(names, parts)
    return {c: {code: v[i] for code, i in idx.items() if i in v} for c, v in d.items()}, idx

def transitions(a, b, codes):
    """T[code][s0] = probability vector over next star 1..5 (index 1..5)."""
    T = {}
    for code in codes:
        M = np.zeros((6, 6))
        for c in a:
            if c in b and code in a[c] and code in b[c]:
                M[a[c][code], b[c][code]] += 1
        T[code] = M
    return T

def pit_normal_scores(a, b, T):
    """Mid-rank PIT of each observed transition, mapped to normal scores, by contract."""
    Z = {}
    for c in a:
        if c not in b: continue
        zs = {}
        for code, M in T.items():
            if code in a[c] and code in b[c]:
                s0, s1 = a[c][code], b[c][code]
                row = M[s0]; n = row.sum()
                if n < 10: continue
                lo = row[:s1].sum() / n; hi = row[:s1 + 1].sum() / n
                zs[code] = norm.ppf(min(max((lo + hi) / 2, 1e-4), 1 - 1e-4))
        if len(zs) >= 10: Z[c] = zs
    return Z

def estimate_rho(Z):
    """Average within-contract correlation of normal scores = variance of the contract mean, corrected."""
    # Var(contract mean) = s2 * (rho + (1 - rho)/n), s2 = variance of a single score
    ms = np.array([np.mean(list(z.values())) for z in Z.values()])
    ns = np.array([len(z) for z in Z.values()])
    s2 = np.mean([v ** 2 for z in Z.values() for v in z.values()])
    inv_n = np.mean(1 / ns)
    rho = (np.mean(ms ** 2) / s2 - inv_n) / (1 - inv_n)
    return float(max(0.0, min(0.95, rho)))

def draw_matrix(start, T, codes, n, rho, rng):
    """Return n x len(codes) array of next-year stars (0 = missing)."""
    k = len(codes)
    common = rng.standard_normal((n, 1))
    eps = rng.standard_normal((n, k))
    z = np.sqrt(rho) * common + np.sqrt(1 - rho) * eps
    u = norm.cdf(z)
    out = np.zeros((n, k), dtype=int)
    for j, code in enumerate(codes):
        s0 = start.get(code)
        if s0 is None: continue
        M = T.get(code)
        if M is None or M[s0].sum() < 5:
            out[:, j] = s0; continue
        cdf = np.cumsum(M[s0][1:] / M[s0][1:].sum())
        out[:, j] = 1 + np.searchsorted(cdf, u[:, j], side='left').clip(0, 4)
    return out

def rate_matrix(D, codes, contract, drop=(), th=None, weights=None):
    """Vectorised overall rating for an n x k draw matrix, CMS method (rebuild), returns rounded stars and raw."""
    W = dict(rs.W)
    if weights: W.update(weights)
    res = {}
    for imp in (False, True):
        mset = [m for m in rs.measure_set('overall', imp, drop) if m in codes]
        cols = [codes.index(m) for m in mset]
        X = D[:, cols].astype(float); w = np.array([W[m] for m in mset])
        mask = X > 0
        wsum = (mask * w).sum(1); kk = mask.sum(1)
        mu = (X * w).sum(1) / wsum
        var = kk * ((mask * w) * (X - mu[:, None]) ** 2).sum(1) / (wsum * (kk - 1))
        t = th[imp]
        hi = mu >= t['m85']; rel = (mu >= t['m65']) & (mu < t['m85'])
        low = var < t['v30']; med = (var >= t['v30']) & (var < t['v70'])
        rf = np.select([hi & low, hi & med, rel & low, rel & med], [0.4, 0.3, 0.2, 0.1], 0.0)
        cai = rs.CAI.get(('overall', rs.fac.get(contract, {}).get('overall', 'N/A')), 0.0)
        res[imp] = mu + rf + cai
    wo, wi = res[False], res[True]
    use = np.where((rs.round_half(wo) >= 4) & (wi < wo), wo, wi)
    return rs.round_half(use), use
