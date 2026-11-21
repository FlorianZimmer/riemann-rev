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

# The spotlight kernel and the window masses

The window criterion ({ref}`comp-criterion`) samples the prime sum through the moments
$A_k(z)=\int g(u)\,\frac{u^ke^{-\sigma u}}{k!}e^{-itu}\,du$ of its Laplace transform. This notebook
computes how sharply the kernel $u^ke^{-\sigma u}/k!$ concentrates on one logarithmic window
$[U,(1+\delta)U]$ when $k=\lceil(1+\delta/2)\sigma U\rceil$, checks the numbers shown in the atlas, and
quantifies the two exponential effects the argument plays against each other.

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
sp = bd.facts()['spotlight']
```

## Mass inside the window, two ways

Normalized by $\sigma^{k+1}$ the kernel is the density of a Gamma$(k+1,\sigma)$ variable, so the mass
inside $[a,b]$ has the closed form $\sum_{j=0}^{k}\big(e^{-\sigma a}(\sigma a)^j-e^{-\sigma b}(\sigma b)^j\big)/j!$
(Poisson sums). We compare it with the trapezoidal quadrature used for the atlas figure
(`rhlib.spotlight_mass_in`).

```{code-cell} ipython3
def pois(x, j):
    """e^{-x} x^j / j!, computed in logarithms."""
    return math.exp(-x + j * math.log(x) - math.lgamma(j + 1))

def mass_exact(U, delta, k, sigma):
    a, b = sigma * U, sigma * (1 + delta) * U
    return math.fsum(pois(a, j) - pois(b, j) for j in range(k + 1))

sigma, delta = sp['sigma'], sp['delta']
rows = []
for U_str, w in sp['windows'].items():
    U = float(U_str)
    k = math.ceil((1 + delta / 2) * sigma * U)
    quad = rhlib.spotlight_mass_in(U, delta, k, sigma)
    exact = mass_exact(U, delta, k, sigma)
    rows.append((int(U), k, quad, exact))
    assert k == w['k'] and round(quad, 4) == w['mass_inside'] and abs(quad - exact) < 1e-6
for U, k, quad, exact in rows:
    print(f"U = {U:4d}, k = {k:4d}:  quadrature {quad:.6f}   closed form {exact:.6f}")
```

```{code-cell} ipython3
:tags: [remove-cell]
assert (sigma, delta) == (1.0, 0.5)
bd.glue('masses', ', '.join(f"{100 * e:.2f}%" for _, _, _, e in rows))
bd.glue('Us', ', '.join(str(U) for U, *_ in rows))
```

For $\sigma=1$, $\delta=\tfrac12$ and $U=${glue:text}`Us`, the fractions of mass inside the window are
{glue:text}`masses`.

```{code-cell} ipython3
:tags: [remove-input]
u = np.linspace(0.5, 260.0, 1600)
fig, ax = plt.subplots(figsize=(9, 3.2))
for i, (U, k, quad, exact) in enumerate(rows):
    v = rhlib.spotlight(u, k, sigma)
    ax.axvspan(U, (1 + delta) * U, color=P['ana'], alpha=0.07 + 0.03 * i, lw=0)
    ax.plot(u, v / v.max(), color=P['ana'], lw=1.8, alpha=0.5 + 0.16 * i)
    ax.text(1.25 * U, 1.04 + 0.2 * (i % 2 == 0 and i < 2), f"k = {k}\n{100 * exact:.1f}% inside", ha='center',
            va='bottom', fontsize=8.5, color=P['text'])
ax.set_xlim(0, 260)
ax.set_ylim(0, 1.5)
ax.set_xlabel('u = log y')
ax.set_yticks([])
ax.set_title('Kernels u^k e^{-u}/k! (peak normalized) and their windows [U, 1.5U]', loc='left')
plt.show()
```

## The tails are exponentially small

Outside the window, the mass splits into a lower tail $P(\text{Gamma}<U)$ and an upper tail
$P(\text{Gamma}>(1+\delta)U)$, both computed below as sums of positive Poisson terms (so no
cancellation occurs). Large deviations predict decay like $e^{-cU}$ with
$c=(1+\delta/2)\sigma\min\big(I(t_-),I(t_+)\big)$, $I(t)=t-1-\log t$, $t_-=\frac{1}{1+\delta/2}$,
$t_+=\frac{1+\delta}{1+\delta/2}$; the polynomial prefactor makes the convergence of
$-\log(\text{outside})/U$ to $c$ slow.

```{code-cell} ipython3
def outside(U, delta, k, sigma):
    a, b = sigma * U, sigma * (1 + delta) * U
    lower = math.fsum(pois(a, j) for j in range(k + 1, k + 60 * int(math.sqrt(k)) + 200))  # P(Poisson(a) > k)
    upper = math.fsum(pois(b, j) for j in range(k + 1))                                    # P(Poisson(b) <= k)
    return lower + upper

I = lambda t: t - 1 - math.log(t)
c = (1 + delta / 2) * sigma * min(I(1 / (1 + delta / 2)), I((1 + delta) / (1 + delta / 2)))
prev = None
tail_rows = []
for U in (20, 40, 80, 160, 320, 640, 1280):
    k = math.ceil((1 + delta / 2) * sigma * U)
    out = outside(U, delta, k, sigma)
    tail_rows.append((U, k, out, -math.log(out) / U))
    if prev is not None:
        assert out < prev
    prev = out
for U, k, out, rate in tail_rows:
    print(f"U = {U:5d}, k = {k:5d}:  mass outside = {out:.3e},  −log(outside)/U = {rate:.4f}")
print(f"large-deviation rate c = {c:.4f}")
assert all(r2[3] < r1[3] for r1, r2 in zip(tail_rows, tail_rows[1:])) and all(r[3] > c for r in tail_rows)
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('rate_c', f"{c:.4f}")
bd.glue('out_last', f"{tail_rows[-1][2]:.1e}")
bd.glue('U_last', f"{tail_rows[-1][0]:,}")
```

At $U=${glue:text}`U_last` the mass outside the window is {glue:text}`out_last`, and the observed rate
decreases towards $c=${glue:text}`rate_c` from above (the prefactor is smaller than one). Computing
$1-(\text{mass inside})$ instead would lose most significant digits at this size. In the proof the tails are not estimated through these exact
values but through a crude global bound $|g(u)|\le C_0e^{2u}$ and a large $\sigma$; the computation
only shows how fast the spotlight focuses.

## Pole against window

A pole at distance $d$ from the point $z$ contributes about $d^{-k}$ to $A_k(z)$, while the
window bound only allows $e^{\eta U}r^{-k}$ with $r>d$. With $k\ge U$ the ratio is at least
$e^{U(\log(r/d)-\eta)}$. For example, with $d/r=0.9$ and $\eta=0.05$:

```{code-cell} ipython3
d_over_r, eta = 0.9, 0.05
for U in (20, 80, 320, 1280):
    k = math.ceil((1 + delta / 2) * sigma * U)
    log10_ratio = (k * math.log(1 / d_over_r) - eta * U) / math.log(10)
    print(f"U = {U:5d}, k = {k:5d}:  pole term / window bound ≥ 10^{log10_ratio:.1f}")
    assert log10_ratio > 0
```

Since $\eta>0$ is arbitrary in the source's estimate, any $\eta<\log(r/d)$ gives a contradiction for
large $U$; only arbitrarily late windows are needed, which is why sparse windows suffice.
