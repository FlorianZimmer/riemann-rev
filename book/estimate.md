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

# The estimate: from a chain of theta lifts to a prime-sum bound

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
from fractions import Fraction as F
import bookdata as bd

m = bd.model()
fx = bd.facts()['balance']
expected = {8: 'The finite character comparison', 9: 'The geometric family and the theta chain',
            10: 'Hosts for every character'}
assert {c['n']: c['title'] for c in bd.comps('est')} == expected
# constants quoted below, checked against the model (statements and Lean excerpts)
assert fx['worst_budget_eps'] == '13/8' and fx['total_eps'] == '9' and (fx['eD'], fx['eL']) == (2, 0)
assert sum(F(v) for _, v in fx['steps']) == F(fx['total_eps']) == fx['eD'] + fx['eL'] + 7
assert sum(r['coef'] for r in fx['budget']) == 10
st = bd.comp('comparison')['statement']
assert '4x^{1/2+\\varepsilon}' in st and '\\tfrac{2Q}{x}' in st
rank = bd.node('rank')['excerpt']
for frag in ('s.x ^ (2 + 8 * s.eps)', 'Real.sqrt (s.x * s.delta1)', '2 * Real.sqrt (s.x * s.delta1)',
             's.x ^ (9 / 2 + 10 * s.eps)'):
    assert frag in rank, frag
assert 'delta_1=x^{-\\varepsilon/8}' in bd.comp('family')['statement'].replace('\\delta_1', 'delta_1')
assert 'x^{1/2-\\varepsilon/16}' in bd.comp('family')['statement']
vwin = bd.node('vwin-def')['excerpt']
for frag in ('eps < 1 / 52', 'X ^ (1 / J) ≤ Y', 'Y ^ (2 : ℝ) ≤ X', '1 ≤ J'):
    assert frag in vwin, frag
sup = bd.node('supply')['excerpt']
assert 'VWinAt ψ 401' in sup and 'HostExW (3 / 2)' in sup
assert 'C_{\\rm abs}=2' in bd.comp('family')['explanation'][0] and 'C_0=3' in bd.comp('family')['explanation'][0]
assert any('C* = e_D + e_L + 3' in w for w, _ in fx['steps'])
assert '(4 * (Λ.o : ℝ))' in bd.node('core-gm')['excerpt']
tl8 = next(t for t in m['timeline'] if t['number'] == 8)
assert tl8['topic'] == 'A chain with square-root length' and tl8['component'] == 'family'
```

```{code-cell} ipython3
:tags: [remove-input]
bd.show(f"{bd.stratum_badge('est')} {bd.esc(bd.stratum('est')['blurb'])}")
```

The analytic engine needs, for each primitive character $\psi$ and each small $\varepsilon$, a bound
$G_P(x)\le x^{1/2+(e_D+e_L+7)\varepsilon}$ for the level $P$ of $\psi$ on arbitrarily late windows. This
stratum is where that bound is produced from geometry. Its centre, the finite character
comparison, is machine-checked as an implication: it takes as hypotheses, at each scale $x$, the
existence of arithmetic data (a frame, a host, a set of classes) with explicit size, norm and
discrepancy bounds, and returns the prime-sum bound. The data are the business of the theta chain
and of the hosts.

(comp-comparison)=
## 8 · The finite character comparison

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.card('comparison'))
```

### What is fixed and what is estimated

The comparison theorem `UpperTheory.Comparison₂.core_gm` fixes the level $\Lambda$, real parameters
$e_D,e_L,K,c_{HH},e_K,C$ and $\varepsilon>0$, and *then* produces a threshold $x_1$. At each scale
$x\ge x_1$ it receives a finite frame (a finite abelian group $A$ with a translation subgroup $A_0$),
an arithmetic host, a set $T$ of classes, and two packages of hypotheses at that same $x$:
`EAtH` (the characters, their smoothed sums and the shares of $T$) and `CoreAtH` (the witnesses,
weights, slopes and size bounds). The frame and the witnesses may change with $x$; the threshold
may not. A single application gives an estimate at one scale — arbitrarily late *windows* require
the family construction of the next section.

### The main term shared by geometry and primes

For a top weight $a>0$ and local weights $w_\rho>0$ at a set $\Phi$ of places, the analytic side
subtracts

$$
\mathrm{MAIN}(a,w)=a\Big(\log a-1-\gamma+\ell(\mathrm{chC})-\frac1{|\Phi|}\sum_{\rho\in\Phi}\log w_\rho\Big),
$$

where $\ell$ is the logarithmic derivative at $1$ of the represented primitive character. A
prime-by-prime identity (`ch_balance`) expresses the finite prime count minus this main term as a
Fourier sum of centered prime sums; on the geometric side, the slope computation of the theta chain
produces the same expression (a cancellation identity in the source), so that main terms cancel
exactly and only discrepancies remain.

### Which characters survive the subgroup average

The Fourier group is $E_0\times A$ with $E_0=(\mathbb Z/2)^2$. Writing $e_1(t)=((1,0),t)$ and $\Psi_0$
for the characters trivial on $\{0\}\times A_0$, translation gives, for $s$ in the subgroup set $T_2$,

$$
\sum_{z\in A_0}\psi\big(-e_1(s+z-t)\big)=\begin{cases}|A_0|\,\psi(e_1(t)),&\psi\in\Psi_0,\\[2pt] 0,&\psi\notin\Psi_0.\end{cases}
$$

Averaging the per-translation discrepancy bounds over $A_0$ therefore leaves exactly the characters
in $\Psi_0$. Those that are retained in the level carry the weights of $G_\Lambda$; the others — the
discarded survivors — contribute a term $\Sigma(x)$, which a separate square-root input (`EAtH.bdG`)
bounds by $4o\,x^{1/2+\varepsilon}$. With $Q=umb$, $\delta=v/n$ and $E$ the common bound on the geometric
discrepancy, the finite comparison reads

$$
Q\,\frac{\delta}{2}\Big(G_\Lambda(x)-\Sigma(x)-4x^{1/2+\varepsilon}\Big)\le E+\frac{2Q}{x}.
$$

### The budget: where $\sqrt x$ and each $\varepsilon$ are paid

The geometric proof gives $E\le x^{C_*\varepsilon}B$ with $C_*=e_D+e_L+3$, where $B$ is an exact
bracket with four terms. Under the simultaneous size hypotheses of the source, the four terms of
$B/Q$ are bounded as follows (exponents in exact arithmetic; recomputed in {doc}`balance`):

```{code-cell} ipython3
:tags: [remove-input]
import re
# typeset versions of the four rows of facts.json; the assertion ties them to the data
TEX = {
    "a_E/(m b)": (r"a_E/(mb)", r"$a_E/(mb)\le 2x/m$ and $m\ge x^{1/2-\varepsilon}$",
                  "a_E/(mb) <= 2x/m and m >= x^{1/2-eps}"),
    "a_E m/(b k)": (r"a_E m/(bk)", r"$xm\le k$", "x m <= k"),
    "2 (n/u) m x^eps": (r"2\,(n/u)\,m\,x^{\varepsilon}",
                        r"$n/u\le 2x^{\varepsilon/8}$, $m\le x^{1/2+\varepsilon/2}$, and the explicit $x^{\varepsilon}$",
                        "n/u <= 2x^{eps/8}, m <= x^{1/2+eps/2}, the explicit x^eps"),
    "(v/u)(k/n^2) x^{2 eps}": (r"(v/u)(k/n^2)\,x^{2\varepsilon}",
                               r"$v/u\le n/u\le 2x^{\varepsilon/8}$, $k/n^2\le x^{1/2-\varepsilon}$, and the explicit $x^{2\varepsilon}$",
                               "v/u <= n/u <= 2x^{eps/8}, k/n^2 <= x^{1/2-eps}, the explicit x^{2eps}"),
}
def exponent_tex(e):
    if e == "O(1)":
        return r"$O(1)$"
    q = F(re.fullmatch(r"1/2 \+ ([\d/]+)·ε", e).group(1))
    return r"$\tfrac12+\varepsilon$" if q == 1 else rf"$\tfrac12+\tfrac{{{q.numerator}}}{{{q.denominator}}}\varepsilon$"
rows = []
for r in fx['budget']:
    term_tex, why_tex, why_raw = TEX[r['term']]
    assert r['why'] == why_raw, r['why']
    rows.append([f"${term_tex}$", str(r['coef']), exponent_tex(r['exponent']), why_tex])
assert len(rows) == len(TEX)
bd.show(bd.md_table(["Term of $B/Q$", "Coefficient", "Exponent of $x$", "From the size hypotheses"], rows,
                    align="---|--:|---|---"))
```

The first and third rows are the heart of the matter. Ignoring the $x^{O(\varepsilon)}$ factors and
writing the chain length as $m=x^a$, one pays $x/m=x^{1-a}$ and $m=x^a$; the larger exponent
$\max(1-a,a)$ is smallest at $a=\tfrac12$. *This is where the square root of the Riemann hypothesis
comes from in this argument*: a chain of about $\sqrt x$ theta lifts balances the two costs. The
worst term carries $x^{1/2+13\varepsilon/8}$, and the remaining steps add the losses recorded in the
staircase:

```{code-cell} ipython3
:tags: [remove-input]
acc = F(0)
rows = []
for what, v in fx['steps']:
    acc += F(v)
    rows.append([bd.esc(what, True), f"$+{v}$" if '/' not in v else f"$+\\tfrac{{{F(v).numerator}}}{{{F(v).denominator}}}$",
                 f"${acc}$" if acc.denominator == 1 else f"$\\tfrac{{{acc.numerator}}}{{{acc.denominator}}}$"])
bd.show(bd.md_table(["Step", "Loss (units of $\\varepsilon$)", "Running total"], rows, align="---|--:|--:"))
```

The total is $e_D+e_L+7$, independent of the particular constants, and equals $9$ for the source's
choice $e_D=2$, $e_L=0$. The proof that the scalar inequalities really allow the worst term — an
explicit admissible choice of all parameters attaining $4x^{1/2+13\varepsilon/8}$ — is in
{doc}`balance`.

### What the comparison does not supply

The comparison consumes three things it does not prove: the existence of the geometric data at
every scale of a window, the discrepancy bound $E$ (the geometric content), and the square-root
bound for the discarded characters. The last is a square-root bound for finitely many specific
characters; the auxiliary-prime theorem of {ref}`comp-primes` proves bounds of this shape for
quadratic twists, and how the chosen primes feed a fixed target character is one of the points the
model lists as still to check. The machine-checked statement is the implication with these
hypotheses explicit.

(comp-family)=
## 9 · The geometric family and the theta chain

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.card('family'))
```

### The parameters of a chain

At a scale $x$ with small $\varepsilon$ the source sets $\delta_1=x^{-\varepsilon/8}$, and the predicate
`GlobalTheory.EX.RankVal` fixes integers $n,m,k$ with

$$
x^{2+8\varepsilon}\le n\le 2x^{2+8\varepsilon},\qquad \sqrt{x\delta_1}\le m\le 2\sqrt{x\delta_1},\qquad
x^{9/2+10\varepsilon}\le k\le 2x^{9/2+10\varepsilon}.
$$

So the chain length is $m\asymp x^{1/2-\varepsilon/16}$, comfortably inside the window
$x^{1/2-\varepsilon}\le m\le x^{1/2+\varepsilon/2}$ demanded by the comparison: this is the precise
meaning of the announcement's "chain of theta lifts of length $\sqrt X$" (entry 8). The same
predicate ties an auxiliary rank $t$ to these parameters; its growth is what the fixed cutoff
exponent $401$ of the cohomological window has to dominate. All of this is a *hypothesis* of the
downstream implications; producing families with these ranks is a separate task.

### Three local mechanisms, visible in isolation

* **Denominators clear along the chain** (`ThetaLiftIndependence.ChainInt`). For finite kernels
  $(Tf)(v)=\sum_u w(u)f(u)K(u,v)$ with $D_jw_j$ and all kernel entries in a subring $S$, one has
  $\big(\prod_{j<m}D_j\big)(T_{m-1}\cdots T_0f)(v)\in S$. This is bookkeeping; a *gain* needs actual
  automorphic maps with controlled denominators and norms.
* **A divisor appears in a minor** (`key_minor_dvd`, kernel-checked). If $w^2=p$ in a commutative
  ring $A$, two rows supported at index $0$ modulo $w$, and $M^{p^e}\equiv N'$ entrywise modulo $p$,
  then modulo $w$ both transformed rows are multiples of the same row, so $w$ divides the
  $2\times2$ minor $W_cV_0-W_0V_c$ — even when $A/(w)$ has zero divisors.
* **Slopes of lattices** (`slopeInequality_of`). For an injective integral map $\phi:A\to B$ of
  Euclidean lattices with $\|\phi v\|\le C\|v\|$, comparing Gram determinants gives
  $\mu(A)\le\mu_{\max}(B)+\log C$, where $\mu=-\log(\mathrm{covol})/\mathrm{rank}$ (Bost's slope
  inequality; the general sublattice bound $\mu(A')\le\mu_{\max}(B)$ is a named hypothesis).

### Fixing the losses

`TopShape` calls the family constructor `UpperTheory.Top.topDesWin` with the constants on the
card, which fixes $e_D=2$ and $e_L=0$ *before* $\varepsilon$ is chosen; this is the uniformity that
{ref}`comp-choreography` needs. The constructor combines existence of a design, family inclusions,
the window hypothesis `HypV`, the links `LinkN`, `LinkEta`, `LinkIRR`, a rank equality, and the
divisibility, rank and global links — on **one** family. The local facts above are each plausible
and some are checked; that they hold *simultaneously* on a single family at every scale of a window
is the substantive claim. The source also contains identities that are uniform over an index set
(for instance a volume identity for every admissible character datum); whether such an index set
is nonempty is a separate question, which is why "nonempty compatible data" is one of the open
audit items in {doc}`verification`.

(comp-hosts)=
## 10 · Hosts for every character

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.card('hosts'))
```

### What one character must supply

Fix a primitive $\psi$. The proposition `VWinAt ψ 401` reads, in the archive's quantifier order:
for every $0<\varepsilon<\tfrac1{52}$ and every admissible layer function $e:\mathbb R\to\mathbb N$, there
are $J\ge1$ and $X_0$ such that for every $X\ge X_0$ and every pair of auxiliary primes $q,d$
admissible at scale $X^{1/J}$, some $Y$ with $X^{1/J}\le Y$ and $Y^2\le X$ makes the cohomological
bound of {ref}`comp-cohomology` hold at every $x\in[Y,Y^2]$. The interval may depend on $X,q,d$; the
exponent $J$ may not; all choices may depend on $\psi$.

The supplier `supplyChi ψ` (kernel-checked, with `VWinAt ψ 401` as hypothesis) turns this into
hosts of width $3/2$ satisfying the character requirement `(GChi ψ).req`, which combines the
cyclotomic-level condition `EAtH` with the cohomological inequality for the host field. Hosts are
produced *per character*: a common host for all characters would be a stronger quantifier order
and is not needed. `zeroFreeAll_of_topG` then takes the width $\lambda=3/2$, the requirement
`GChi ψ`, the hosts and `TopG`, and returns the primitive half-plane statement `ZeroFreeAll`.
