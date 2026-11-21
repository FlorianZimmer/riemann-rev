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

# The square-root balance and the exact staircase of losses

This notebook redoes, in exact rational arithmetic, the exponent bookkeeping of the finite character
comparison ({ref}`comp-comparison`): why the chain length is $\sqrt x$, why the worst of the four
budget terms costs $x^{1/2+13\varepsilon/8}$, an explicit admissible choice of parameters that
*attains* that term, and the staircase that ends at $\tfrac12+(e_D+e_L+7)\varepsilon$.

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
sys.path.insert(0, '../scripts')
import bookdata as bd
import rhlib
from fractions import Fraction as F
import numpy as np
import matplotlib.pyplot as plt
bd.plot_style()
P = bd.PALETTE
fb = bd.facts()['balance']
```

## Why $\sqrt x$

With $m=x^a$ the two competing costs are $x/m=x^{1-a}$ and $m=x^a$. On a grid of exact rationals
the larger exponent $\max(1-a,a)$ is minimized at $a=\tfrac12$, where both equal $\tfrac12$:

```{code-cell} ipython3
grid = [F(j, 64) for j in range(65)]
best = min(grid, key=lambda a: max(1 - a, a))
print("argmin =", best, "  min =", max(1 - best, best))
assert best == F(1, 2) and rhlib.balance_exponent(float(best)) == 0.5
```

## The four budget terms

`rhlib.budget_rows()` encodes the four contributions to $B/Q$ with exact exponents
$\tfrac12\cdot[\text{half}]+(\text{eps})\cdot\varepsilon$, derived from the size hypotheses
$a_E\le2xb$, $n/u\le2x^{\varepsilon/8}$, $x^{1/2-\varepsilon}\le m\le x^{1/2+\varepsilon/2}$,
$xm\le k\le n^2x^{1/2-\varepsilon}$, $v\le n$:

```{code-cell} ipython3
rows = rhlib.budget_rows()
for r in rows:
    expo = f"1/2 + {r['eps']}·ε" if r['half'] else "O(1)"
    print(f"{r['term']:<24} coefficient {r['coef']}   exponent {expo:<14} ({r['why']})")
worst = max(r['eps'] for r in rows if r['half'] == F(1, 2))
total_coef = sum(r['coef'] for r in rows)
print("worst ε-coefficient:", worst, "  sum of coefficients:", total_coef)
assert str(worst) == fb['worst_budget_eps'] and worst == F(1, 8) + F(1, 2) + 1
assert [r['coef'] for r in rows] == [b['coef'] for b in fb['budget']]
```

The worst term is the third: $\tfrac18$ from $n/u$, $\tfrac12$ from the upper bound on $m$, and $1$ from
the explicit factor $x^{\varepsilon}$.

## An admissible example attaining the worst term

Can all size hypotheses hold at once *and* the third term be as large as the bound allows? Take
$\varepsilon=\tfrac1{64}$, $x=2^{1024}$, $b=1$, $a_E=2x$, and $m,n,u,v,k$ powers of two with exponents
$520,524,521,508,1544$. Everything is a power of two, so all comparisons are exact comparisons of
rational exponents of $2$:

```{code-cell} ipython3
eps = F(1, 64)
X = F(1024)                                            # x = 2^X; below, every quantity is log2 of itself
lg = dict(m=F(520), n=F(524), u=F(521), v=F(508), k=F(1544), b=F(0), aE=1 + X)
xp = lambda e: X * e                                   # log2 of x^e

checks = {
    "a_E ≤ 2 x b":                  lg['aE'] <= 1 + X + lg['b'],
    "n/u ≤ 2 x^(ε/8)":              lg['n'] - lg['u'] <= 1 + xp(eps / 8),
    "x^(1/2−ε) ≤ m":                xp(F(1, 2) - eps) <= lg['m'],
    "m ≤ x^(1/2+ε/2)":              lg['m'] <= xp(F(1, 2) + eps / 2),
    "x m ≤ k":                      X + lg['m'] <= lg['k'],
    "k ≤ n² x^(1/2−ε)":             lg['k'] <= 2 * lg['n'] + xp(F(1, 2) - eps),
    "v ≤ n":                        lg['v'] <= lg['n'],
}
for name, ok in checks.items():
    print(f"{name:<20} {ok}")
assert all(checks.values())

terms = {
    "a_E/(m b)":               lg['aE'] - lg['m'] - lg['b'],
    "a_E m/(b k)":             lg['aE'] + lg['m'] - lg['b'] - lg['k'],
    "2 (n/u) m x^ε":           1 + lg['n'] - lg['u'] + lg['m'] + xp(eps),
    "(v/u)(k/n²) x^(2ε)":      lg['v'] - lg['u'] + lg['k'] - 2 * lg['n'] + xp(2 * eps),
}
bounds = {   # coefficient · x^(exponent) from the budget, as log2
    "a_E/(m b)":               1 + xp(F(1, 2) + 1 * eps),
    "a_E m/(b k)":             F(1),                   # the term is at most 2
    "2 (n/u) m x^ε":           2 + xp(F(1, 2) + F(13, 8) * eps),
    "(v/u)(k/n²) x^(2ε)":      1 + xp(F(1, 2) + F(9, 8) * eps),
}
for t in terms:
    print(f"{t:<22} = 2^{terms[t]}   bound 2^{bounds[t]}")
    assert terms[t] <= bounds[t]
assert terms["2 (n/u) m x^ε"] == bounds["2 (n/u) m x^ε"]
```

```{code-cell} ipython3
:tags: [remove-cell]
assert [int(terms[t]) for t in terms] == [505, 1, 540, 515]
from IPython.display import Markdown
bd.glue('t_exps', Markdown(', '.join(f"$2^{{{int(terms[t])}}}$" for t in terms)))
bd.glue('attained', Markdown(f"$2^{{{int(terms['2 (n/u) m x^ε'])}}}$"))
```

The four normalized terms are {glue:md}`t_exps:myst`, and the third, {glue:md}`attained:myst`, equals
$4x^{1/2+13\varepsilon/8}$ exactly. So the exponent $\tfrac{13}{8}$ is not an artefact of a lossy
estimate: within the scalar hypotheses it can be reached. (The example tests the scalar calculation
only; it says nothing about the existence of arithmetic hosts with these parameters.)

## From the worst term to $e_D+e_L+7$

With $P=x^{C_*\varepsilon}$, $C_*=e_D+e_L+3$, and $Y=x^{1/2+13\varepsilon/8}$, the four coefficients add
up to $10$, so $E/Q\le10PY$. The finite comparison
$Q\frac\delta2(G_\Lambda-\Sigma-4x^{1/2+\varepsilon})\le E+\frac{2Q}x$ and $2/\delta\le2x^{\varepsilon}$ give

$$
G_\Lambda-\Sigma\le 2x^{\varepsilon}\Big(10PY+\frac2x\Big)+4x^{1/2+\varepsilon}\le 22\,PYx^{\varepsilon}+4x^{1/2+\varepsilon}
\le 26\,x^{1/2+(C_*+21/8)\varepsilon},
$$

then $26\le x^{3\varepsilon/8}$ gives $G_\Lambda-\Sigma\le x^{1/2+(C_*+3)\varepsilon}$, and with
$\Sigma\le4o\,x^{1/2+\varepsilon}$ and $1+4o\le x^{\varepsilon}$ finally
$G_\Lambda\le x^{1/2+(C_*+4)\varepsilon}=x^{1/2+(e_D+e_L+7)\varepsilon}$. In units of $\varepsilon$:

```{code-cell} ipython3
eD, eL = fb['eD'], fb['eL']
Cstar = eD + eL + 3
steps = [(w, F(v)) for w, v in fb['steps']]
assert [v for _, v in steps] == [worst, F(Cstar), F(1), F(3, 8), F(1)]
acc = F(0)
for what, v in steps:
    acc += v
    print(f"+{str(v):>4}  → {str(acc):>5}   {what}")
assert acc == eD + eL + 7 == F(fb['total_eps'])
# the exponent C* + 21/8 of the intermediate bound, and the absorption of 26
assert worst + Cstar + 1 == Cstar + F(21, 8) and Cstar + F(21, 8) + F(3, 8) == Cstar + 3
assert 2 * 10 + 2 == 22 and 22 + 4 == 26 and sum(r['coef'] for r in rows) == 10
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('total', str(acc))
bd.glue('eD', str(eD))
bd.glue('eL', str(eL))
```

With the source's $e_D=${glue:text}`eD` and $e_L=${glue:text}`eL` the total is
{glue:text}`total`: the comparison delivers $G_\Lambda(x)\le x^{1/2+9\varepsilon}$, which is what the
order of choices ({ref}`comp-choreography`) consumes.

```{code-cell} ipython3
:tags: [remove-input]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.4), gridspec_kw=dict(width_ratios=[1, 1.35]))
a = np.linspace(0, 1, 201)
ax1.plot(a, 1 - a, color=P['est'], lw=1.2, ls=(0, (5, 4)), alpha=0.7, label='x/m')
ax1.plot(a, a, color=P['est'], lw=1.2, ls=(0, (2, 3)), alpha=0.7, label='m')
ax1.plot(a, np.maximum(a, 1 - a), color=P['est'], lw=2.6, label='the larger cost')
ax1.plot([0.5], [0.5], 'o', color=P['est'])
ax1.set_xlabel('a, where m = x^a')
ax1.set_ylabel('exponent of x')
ax1.set_title('Balance: m ≈ √x', loc='left')
ax1.legend(fontsize=8)
left = 0.0
for i, (what, v) in enumerate(steps):
    ax2.barh(i, float(v), left=left, color=P['est'], alpha=0.25 + 0.14 * i, height=0.6)
    ax2.text(left + float(v) + 0.1, i, f"+{v}", va='center', fontsize=9, color=P['text'])
    left += float(v)
ax2.set_yticks(range(len(steps)), [w.split(':')[0].split('(')[0].strip() for w, _ in steps], fontsize=8)
ax2.invert_yaxis()
ax2.axvline(float(acc), color=P['ink'], lw=1, ls=(0, (3, 3)))
ax2.set_xlim(0, float(acc) + 1.2)
ax2.set_xlabel('losses above ½, in units of ε')
ax2.set_title(f'Staircase: total {acc} = e_D + e_L + 7', loc='left')
ax2.grid(axis='y', visible=False)
plt.tight_layout()
plt.show()
```

## How small must $\varepsilon$ be?

The order of choices takes $\theta=\tfrac12+\tfrac12\min(\beta-\tfrac12,\tfrac12)$ for a putative zero with
real part $\beta$ and then any $\varepsilon\le(\theta-\tfrac12)/9$:

```{code-cell} ipython3
for beta in (F(52, 100), F(6, 10), F(3, 4), F(1)):
    theta = F(1, 2) + F(1, 2) * min(beta - F(1, 2), F(1, 2))
    eps_max = (theta - F(1, 2)) / (eD + eL + 7)
    assert F(1, 2) < theta < min(beta, 1) or (beta == 1 and theta < 1)
    print(f"β = {str(beta):>6}:  θ = {str(theta):>7},  ε ≤ {eps_max}")
```

## The chain length of the source fits the window

`RankVal` puts $m$ between $\sqrt{x\delta_1}$ and $2\sqrt{x\delta_1}$ with $\delta_1=x^{-\varepsilon/8}$, i.e.
$m\asymp x^{1/2-\varepsilon/16}$; the comparison demands $x^{1/2-\varepsilon}\le m\le x^{1/2+\varepsilon/2}$.
For every $\varepsilon>0$ the exponent $\tfrac12-\tfrac{\varepsilon}{16}$ lies strictly inside, so the
factor $2$ is absorbed once $x$ is large:

```{code-cell} ipython3
for e in (F(1, 53), F(1, 100), F(1, 1000)):
    lo, mid, hi = F(1, 2) - e, F(1, 2) - e / 16, F(1, 2) + e / 2
    assert lo < mid < hi
    # 2 x^mid <= x^hi  <=>  x^(hi - mid) >= 2  <=>  x >= 2^(1/(hi - mid))
    print(f"ε = {e}:  {lo} < {mid} < {hi};  the factor 2 is absorbed for log2 x ≥ {1 / (hi - mid)}")
```
