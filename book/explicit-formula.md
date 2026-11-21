---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# The centered prime sum and the explicit formula

This notebook recomputes the numbers behind {ref}`comp-statistic`: the centered prime sum $G(y)$
from a sieve, the constant $\log 2\pi$ and the band $2+\gamma-\log 4\pi$ that RH would force, the first
zeros of $\zeta$, and the agreement between the prime side and the zero side of the explicit
formula. Every number quoted in the text is computed here and compared with
`assets/figures/facts.json`, from which the atlas figures were drawn.

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
sys.path.insert(0, '../scripts')
import bookdata as bd
import rhlib
import math
import numpy as np
import matplotlib.pyplot as plt
bd.plot_style()
P = bd.PALETTE
fx = bd.facts()
# numbers typed in the prose of this page
assert fx['hero']['y_max'] == 10 ** 7 and fx['hero']['samples'] == 400_000 and fx['hero']['y_min'] == 10
assert fx['explicit']['y_range'] == [100, 2_000_000]
assert fx['explicit']['hypothetical_rho'] == [0.62, 40.0] and fx['explicit']['hyp_growth_exponent'] == 0.12
assert fx['zeros']['count'] == 100
```

## The statistic, from a sieve

$G(y)=\sum_{n\le y}\Lambda(n)(y/n-1)-y\log y+(1+\gamma)y$ is evaluated from cumulative sums of
$\Lambda(n)$ and $\Lambda(n)/n$ up to $10^7$. As a check, it agrees with the naive definition at a few
points:

```{code-cell} ipython3
ps = rhlib.PrimeSums.build(10_000_000)
rows = []
for y in (2.0, 10.5, 97.3, 1000.0, 12345.6):
    fast, naive = float(ps.G(y)), rhlib.centered_prime_sum_naive(y)
    rows.append((y, fast, naive, abs(fast - naive)))
    assert abs(fast - naive) < 1e-7 * max(1.0, y)
for r in rows:
    print(f"y = {r[0]:>8}:  G(y) = {r[1]: .9f}  naive {r[2]: .9f}  |diff| {r[3]:.0e}")
```

## Where $\log 2\pi$ and the band come from

From the explicit formula (see {ref}`comp-statistic`),

$$
G(y)=\log 2\pi-\sum_\rho\frac{y^\rho}{\rho(\rho-1)}-\sum_{n\ge1}\frac{y^{-2n}}{2n(2n+1)},
$$

and under RH $|G(y)-\log2\pi|\le(2+\gamma-\log4\pi)\sqrt y+O(y^{-2})$.

```{code-cell} ipython3
log2pi, band = rhlib.LOG_2PI, rhlib.RH_BAND
print(f"log 2π              = {log2pi:.10f}")
print(f"2 + γ − log 4π      = {band:.10f}")
assert round(band, 6) == fx['hero']['rh_band'] and round(log2pi, 4) == fx['ramp']['log_2pi']
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('band', f"{band:.6f}")
```

## The first zeros of $\zeta$

The zeros are located by bisection on Hardy's function $Z(t)=e^{i\vartheta(t)}\zeta(\tfrac12+it)$, with
$\zeta$ computed by Euler–Maclaurin summation. A sanity check is the Riemann–von Mangoldt formula
$N(T)=\vartheta(T)/\pi+1+S(T)$: in this range the counts differ from $\vartheta(T)/\pi+1$ by less than
one.

```{code-cell} ipython3
zeros = rhlib.zeta_zeros(100)
print("first five:", ", ".join(f"{g:.6f}" for g in zeros[:5]))
print(f"100th     : {zeros[99]:.6f}")
for T in (30.0, 50.0, 100.0, 150.0, 200.0, 230.0):
    count = sum(1 for g in zeros if g < T)
    smooth = rhlib.rs_theta(T) / math.pi + 1
    print(f"T = {T:3.0f}:  N(T) = {count:3d},  θ(T)/π + 1 = {smooth:7.3f},  S(T) ≈ {count - smooth:+.3f}")
    assert abs(count - smooth) < 1
assert round(zeros[0], 6) == fx['zeros']['first'] and round(zeros[99], 6) == fx['zeros']['hundredth']
assert len(zeros) == fx['zeros']['count']
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('z1', f"{zeros[0]:.6f}")
bd.glue('z100', f"{zeros[99]:.6f}")
bd.glue('nzeros', len(zeros))
```

The first zero has ordinate {glue:text}`z1` and the hundredth {glue:text}`z100`.

## The normalized prime sum up to $10^7$

The quantity $r(y)=(G(y)-\log2\pi)/\sqrt y$ is sampled at 400,000 logarithmically spaced points of
$[10,10^7]$ (the same sampling as the atlas's title figure).

```{code-cell} ipython3
hero = fx['hero']
ys = np.exp(np.linspace(math.log(hero['y_min']), math.log(hero['y_max']), hero['samples']))
r = (ps.G(ys) - log2pi) / np.sqrt(ys)
r_min, r_max = float(r.min()), float(r.max())
y_min_at, y_max_at = float(ys[np.argmin(r)]), float(ys[np.argmax(r)])
print(f"min r = {r_min:+.5f} at y ≈ {y_min_at:,.1f}")
print(f"max r = {r_max:+.5f} at y ≈ {y_max_at:,.1f}")
print(f"RH band ±{band:.5f};  largest |r| / band = {max(abs(r_min), r_max) / band:.3f}")
assert round(r_min, 5) == hero['r_min'] and round(r_max, 5) == hero['r_max']
assert round(y_min_at, 1) == hero['y_at_min'] and round(y_max_at, 1) == hero['y_at_max']
assert -band < r_min < r_max < band
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('r_min', f"{r_min:+.5f}")
bd.glue('r_max', f"{r_max:+.5f}")
bd.glue('ratio', f"{max(abs(r_min), r_max) / band:.2f}")
assert hero['samples'] == 400_000 and hero['y_min'] == 10 and hero['y_max'] == 10 ** 7
```

```{code-cell} ipython3
:tags: [remove-input]
lx = np.log10(ys)
cx, lo, hi = bd.envelope(lx, r, 1.0, 7.0, 900)
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.fill_between(cx, lo, hi, color=P['num'], lw=0, alpha=0.85, label='(G(y) − log 2π)/√y, computed')
for v in (band, -band):
    ax.axhline(v, color=P['accent'], lw=1, ls=(0, (2, 4)))
ax.axhline(0, color=P['faint'], lw=0.8)
ax.text(7.0, band + 0.002, '+(2 + γ − log 4π)', ha='right', va='bottom', fontsize=8.5, color=P['accent'])
ax.text(7.0, -band - 0.002, '−(2 + γ − log 4π)', ha='right', va='top', fontsize=8.5, color=P['accent'])
ax.set_xlim(1, 7)
ax.set_ylim(-0.062, 0.062)
ax.set_xticks(range(1, 8), [f"$10^{k}$" for k in range(1, 8)])
ax.set_xlabel('y (log scale)')
ax.set_title('The normalized centered prime sum stays well inside the band RH forces', loc='left')
ax.legend(loc='lower left')
plt.show()
```

The extreme values are {glue:text}`r_min` and {glue:text}`r_max`, at most
{glue:text}`ratio` of the band $\pm${glue:text}`band`. This is what RH predicts; it is of course
not evidence about larger $y$.

## The sum over zeros reproduces the oscillation

Truncating the explicit formula at the first $K$ zeros (RH is not assumed: the zeros used were
*found* on the line) and comparing with the prime side on $[100,2\cdot10^6]$:

```{code-cell} ipython3
ex = fx['explicit']
ys2 = np.exp(np.linspace(math.log(ex['y_range'][0]), math.log(ex['y_range'][1]), 1600))
g2 = (ps.G(ys2) - log2pi) / np.sqrt(ys2)
errs = {}
for K in (10, 25, 50, 100):
    ef = (rhlib.explicit_formula_G(ys2, zeros[:K]) - log2pi) / np.sqrt(ys2)
    errs[K] = float(np.max(np.abs(g2 - ef)))
    print(f"K = {K:3d} zeros (up to γ = {zeros[K - 1]:7.3f}):  max |difference| / √y = {errs[K]:.5f}")
assert round(errs[100], 5) == ex['max_abs_difference_normalized'] and ex['zeros_used'] == 100
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('err100', f"{errs[100]:.5f}")
bd.glue('err10', f"{errs[10]:.4f}")
```

With a hundred zeros the two sides agree to {glue:text}`err100` in the normalized scale (with ten
zeros, to {glue:text}`err10`). The dashed curve below is what a *single* hypothetical zero at
$\rho=0.62+40i$ would add: its normalized contribution grows like $y^{0.12}$, so it would eventually
leave any band — in both directions.

```{code-cell} ipython3
:tags: [remove-input]
rho = complex(*ex['hypothetical_rho'])
assert round(rho.real - 0.5, 2) == ex['hyp_growth_exponent']
ef100 = (rhlib.explicit_formula_G(ys2, zeros) - log2pi) / np.sqrt(ys2)
hyp = -2.0 * np.real(np.exp(rho * np.log(ys2)) / (rho * (rho - 1.0))) / np.sqrt(ys2)
lx2 = np.log10(ys2)
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(lx2, hyp, color=P['dest'], lw=1.3, ls=(0, (5, 4)), label=f'term of one hypothetical zero at {rho.real:.2f} + {rho.imag:.0f}i')
ax.plot(lx2, g2, color=P['num'], lw=2.4, label='prime side: (G(y) − log 2π)/√y')
ax.plot(lx2, ef100, color=P['accent'], lw=1.0, label=f'zero side: first {len(zeros)} zeros')
for v in (band, -band):
    ax.axhline(v, color=P['accent'], lw=0.8, ls=(0, (2, 4)), alpha=0.6)
ax.set_xlim(lx2[0], lx2[-1])
ax.set_ylim(-0.05, 0.05)
ax.set_xticks(range(2, 7), [f"$10^{k}$" for k in range(2, 7)])
ax.set_xlabel('y (log scale)')
ax.set_title('Prime side versus zero side of the explicit formula', loc='left')
ax.legend(loc='upper left', fontsize=8.5)
plt.show()
```

(window-strength-numerics)=
## How strong is the window condition, numerically

Under RH, Schoenfeld's bound $|\psi(t)-t|<\sqrt t\log^2t/(8\pi)$ $(t\ge73.2)$ integrates to
$|G(x)|\le\frac{\sqrt x}{8\pi}(2\log^2x+8\log x+16)$ for $x\ge73.2$ ({ref}`window-strength`). On the
sampled range the computed $|G|$ uses only a tiny fraction of this allowance:

```{code-cell} ipython3
mask = ys >= 73.2
bound = np.sqrt(ys[mask]) / (8 * math.pi) * (2 * np.log(ys[mask]) ** 2 + 8 * np.log(ys[mask]) + 16)
ratio = np.abs(ps.G(ys[mask])) / bound
print(f"max |G(x)| / bound on [73.2, 10^7]: {ratio.max():.2e} (at x ≈ {ys[mask][np.argmax(ratio)]:,.0f})")
assert ratio.max() < 1
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('schoenfeld_ratio', f"{ratio.max():.1e}")
```

The largest ratio is {glue:text}`schoenfeld_ratio`. The one-sided window premise of the first
verified cut is thus satisfied with an enormous margin wherever we can compute — which says
nothing about all $x$, and is exactly why that premise is as hard as RH itself.
