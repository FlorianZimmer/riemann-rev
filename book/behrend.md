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

# The Behrend digit sphere

In the choice of the tower ({ref}`comp-primes`) the archive uses Behrend's construction: integer
vectors of fixed norm, written as digits in a large base, give a large set of integers without short
affine relations. This notebook recomputes the atlas's six-point example with its exhaustive check,
verifies the two facts the proof combines (no carries; a line meets a sphere at most twice), and runs a
larger exhaustive check.

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
sys.path.insert(0, '../scripts')
import bookdata as bd
import rhlib
import math
import random
from itertools import permutations, product
import numpy as np
import matplotlib.pyplot as plt
bd.plot_style()
P = bd.PALETTE
fb = bd.facts()['behrend']
ax_rep = bd.axioms()['declarations']
```

## The example

Take the vectors of $\{0,1,2\}^3$ with squared norm $5$ and encode $(x,y,z)\mapsto 24^2x+24y+z$ (base
$4Ld=24$ for $L=2$, $d=3$). The claim is that no three distinct encodings satisfy
$j(s_2-s_1)=i(s_3-s_1)$ with $1\le|i|,|j|\le2$ and $i\neq j$; `rhlib.behrend_example` checks every ordered
triple and coefficient pair (it raises on a relation).

```{code-cell} ipython3
S, d, L, norm = fb['S'], fb['d'], fb['L'], fb['norm']
pts, enc, checks = rhlib.behrend_example(S=S, d=d, L=L, norm=norm)
print("points    :", pts)
print("encodings :", enc)
print(f"checks    : {checks:,}  (= {len(pts) * (len(pts) - 1) * (len(pts) - 2)} ordered triples × "
      f"{(2 * L) * (2 * L - 1)} coefficient pairs)")
assert [list(p) for p in pts] == fb['points'] and enc == fb['encodings'] and checks == fb['checks']
assert 4 * L * d == fb['base'] and checks == len(pts) * (len(pts) - 1) * (len(pts) - 2) * (2 * L) * (2 * L - 1)
```

```{code-cell} ipython3
:tags: [remove-cell]
assert (S, d, L, norm, fb['base']) == (3, 3, 2, 5, 24)
bd.glue('checks', f"{checks:,}")
bd.glue('npts', len(pts))
```

All {glue:text}`checks` relations fail. The {glue:text}`npts` points are the permutations of
$(0,1,2)$: they lie on the circle cut out of the sphere $x^2+y^2+z^2=5$ by the plane $x+y+z=3$.

```{code-cell} ipython3
:tags: [remove-input]
c = np.array([1.0, 1.0, 1.0])
e1 = np.array([1.0, -1.0, 0.0]) / math.sqrt(2)
e2 = np.array([1.0, 1.0, -2.0]) / math.sqrt(6)
fig, ax = plt.subplots(figsize=(5.6, 4.6))
t = np.linspace(0, 2 * math.pi, 400)
rad = math.sqrt(2)
ax.plot(rad * np.cos(t), rad * np.sin(t), color=P['arith'], lw=1.2, alpha=0.6)
xy = []
for v, s in zip(pts, enc):
    w = np.array(v, dtype=float) - c
    assert abs(sum(v) - 3) == 0 and abs(float(w @ w) - 2.0) < 1e-12
    xy.append((float(w @ e1), float(w @ e2), v, s))
p0, p3 = xy[0], xy[3]
dx, dy = p3[0] - p0[0], p3[1] - p0[1]
ax.plot([p0[0] - 0.4 * dx, p3[0] + 0.4 * dx], [p0[1] - 0.4 * dy, p3[1] + 0.4 * dy], color=P['muted'],
        lw=1, ls=(0, (4, 3)))
for X_, Y_, v, s in xy:
    ax.plot([X_], [Y_], 'o', color=P['arith'], ms=9, mec='white', mew=1.5)
    ax.annotate(f"{v} ↦ {s}", (X_, Y_), textcoords='offset points',
                xytext=(10 if X_ >= -1e-9 else -10, 8 if Y_ > 0 else -14),
                ha='left' if X_ >= -1e-9 else 'right', fontsize=8.5, color=P['text'])
ax.set_aspect('equal')
ax.set_xlim(-2.6, 2.6)
ax.set_ylim(-2.0, 2.0)
ax.set_axis_off()
ax.set_title('A digit sphere in the plane x + y + z = 3; a line meets it at most twice', loc='left',
             fontsize=10)
plt.show()
```

## Why no carries

For digits $0\le v_k<d$ and $|i|,|j|\le L$, every digit of $j(v_2-v_1)-i(v_3-v_1)$ has absolute value at
most $2L(d-1)<2Ld$, half the base. A base-$4Ld$ expansion with digits in $(-2Ld,2Ld)$ vanishes only if
every digit does, so a relation between encodings is a relation between the vectors,
coordinate by coordinate:

```{code-cell} ipython3
base = 4 * L * d
coeffs = [c_ for c_ in range(-L, L + 1) if c_ != 0]
max_digit = 0
for v1, v2, v3 in permutations(pts, 3):
    for i in coeffs:
        for j in coeffs:
            if i != j:
                digits = [j * (b - a) - i * (c_ - a) for a, b, c_ in zip(v1, v2, v3)]
                max_digit = max(max_digit, max(abs(x) for x in digits))
print(f"largest digit |j(v2−v1) − i(v3−v1)| = {max_digit};  2L(d−1) = {2 * L * (d - 1)};  base/2 = {base // 2}")
assert max_digit <= 2 * L * (d - 1) < base // 2
```

## Why a line meets a sphere at most twice

If $j(v-u)=i(w-u)$ coordinatewise, the chord identity

$$
j(j-i)\,|v-u|^2=i^2\big(|w|^2-|u|^2\big)-ij\big(|v|^2-|u|^2\big)
$$

holds; on a sphere the right side vanishes, so $v=u$ when $j\neq0$ and $i\neq j$. The identity is
checked here exactly on random integer data with $v=u+i\Delta$, $w=u+j\Delta$:

```{code-cell} ipython3
rng = random.Random(1946)
n_id = 10_000
for _ in range(n_id):
    n = rng.randint(1, 6)
    u = [rng.randint(-50, 50) for _ in range(n)]
    D = [rng.randint(-50, 50) for _ in range(n)]
    i, j = rng.randint(-9, 9), rng.randint(-9, 9)
    v = [a + i * b for a, b in zip(u, D)]
    w = [a + j * b for a, b in zip(u, D)]
    assert all(j * (b - a) == i * (c_ - a) for a, b, c_ in zip(u, v, w))
    nsq = lambda x: sum(t * t for t in x)
    lhs = j * (j - i) * nsq([b - a for a, b in zip(u, v)])
    rhs = i * i * (nsq(w) - nsq(u)) - i * j * (nsq(v) - nsq(u))
    assert lhs == rhs
print(f"chord identity verified exactly on {n_id:,} random instances")
```

```{code-cell} ipython3
:tags: [remove-cell]
for dname in ('BehrendReading.chord_identity', 'BehrendReading.sphere_rel', 'BehrendReading.sphere_midpoint'):
    assert dname in ax_rep
bd.glue('n_id', f"{n_id:,}")
from IPython.display import Markdown
bd.glue('sphere_axioms', Markdown(', '.join(f"`{a}`" for a in ax_rep['BehrendReading.sphere_rel'])))
```

This identity and its consequence are proved for all dimensions in this repository's Lean library
(`BehrendReading.chord_identity`, `BehrendReading.sphere_rel`; transitive axioms
{glue:md}`sphere_axioms`), and in the archive as `Formalism.FrobeniusOrbits.ThickExists.sphere_rel`.

## A larger exhaustive check

The most populous sphere in $\{0,\dots,d-1\}^S$ is what makes the construction large. For a few small
$(S,d)$ we find it and run the same exhaustive relation check with $L=2$; pigeonhole guarantees at least
$d^S/(S(d-1)^2+1)$ points on it.

```{code-cell} ipython3
from collections import Counter
rows = []
for S_, d_ in ((3, 3), (3, 5), (4, 4), (3, 7)):
    counts = Counter(sum(c_ * c_ for c_ in v) for v in product(range(d_), repeat=S_))
    best_norm, size = max(counts.items(), key=lambda kv: (kv[1], -kv[0]))
    pig = math.ceil(d_ ** S_ / (S_ * (d_ - 1) ** 2 + 1))
    _, enc_, checks_ = rhlib.behrend_example(S=S_, d=d_, L=2, norm=best_norm)
    assert len(enc_) == size >= pig
    rows.append((S_, d_, best_norm, size, pig, checks_))
    print(f"S = {S_}, d = {d_}: most populous squared norm {best_norm} with {size} points "
          f"(pigeonhole ≥ {pig});  {checks_:,} relation checks, none holds")
```

```{code-cell} ipython3
:tags: [remove-cell]
bd.glue('big_checks', f"{max(r[5] for r in rows):,}")
```

The largest of these runs checks {glue:text}`big_checks` relations. The archive's quantitative
version (`hostThickExists`, kernel-checked) produces a set of size at least
$\frac nL e^{-C\sqrt{\log n\,\log L}}$ with an absolute constant $C$, and `HostThickOrbit` turns the
relation avoidance into a bound of two points on short segments of high-order orbits.
