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

# Glossary and notation

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
import bookdata as bd

m = bd.model()
fx = bd.facts()
# constants used below, checked against the model and the Lean excerpts it stores
assert 'VWinAt ψ 401' in bd.node('supply')['excerpt'] and 'HostExW (3 / 2)' in bd.node('supply')['excerpt']
assert 'eps < 1 / 52' in bd.node('vwin-def')['excerpt']
assert 'Y^{3/2}' in bd.cut('cut-zeta')['premise']
assert (fx['balance']['eD'], fx['balance']['eL'], fx['balance']['total_eps']) == (2, 0, '9')
assert '\\frac{1}{3o+1}' in bd.comp('statistic')['statement']
assert set(bd.model()['tiers']) == set(bd.SHORT_TIER)
assert m['pins']['toolchain'].endswith('v4.33.1')
```

**Analytic objects**

$\Lambda(n)$
: The von Mangoldt function: $\log p$ if $n=p^k$, $k\ge1$, and $0$ otherwise.

Ramp
: The weight $(y/n-1)_+$. Its Mellin transform is $n^{-s}/(s(s-1))$ ({ref}`comp-residues`).

Centered prime sum $G(y)$
: $\sum_{n\le y}\Lambda(n)(y/n-1)-y\log y+(1+\gamma)y$; the archive's `Deduction.G`, `Formalism.Gz`. Under
  RH, $|G(y)-\log2\pi|\le(2+\gamma-\log4\pi)\sqrt y+O(y^{-2})$ ({ref}`comp-statistic`).

$g_\chi(y)$, level $G_P$
: For nonprincipal primitive $\chi$, $g_\chi(y)=\sum_{n\le y}\Lambda(n)\chi(n)(y/n-1)+y\frac{L'}{L}(1,\chi)$. The
  level of a primitive $\psi$ of order $o$ is $G_P=G+\frac1{3o+1}\sum_{\chi\in P\setminus\{1\}}\Re g_\chi$, $P$ the
  primitive characters inducing $\langle\psi\rangle$.

Positive family
: A finite family of characters with positive coefficients (a principal member only of modulus one);
  positivity makes the residues at a common zero add up ({ref}`comp-residues`).

Power window, arbitrarily late windows
: $[Y,Y^{\lambda}]$ for fixed $\lambda>1$ (the archive uses $\lambda=\tfrac32$); "arbitrarily late" means:
  for every $Y_0$ some $Y\ge Y_0$ works.

One-sided window bound
: $G_F(y)\le Cy^{\theta}$ at *every* point of arbitrarily late windows, with $C$ independent of the window.
  No lower bound is assumed ({ref}`comp-criterion`).

Window criterion
: `Deduction.zeroFree_of_rpow_window`: a one-sided window bound with exponent $\theta<1$ implies that no
  member of the family vanishes in $\Re s>\theta$.

Spotlight
: The kernel $u^ke^{-\sigma u}/k!$ of the $k$-th derivative of the Laplace transform, aimed at a
  logarithmic window by $k=\lceil(1+\delta/2)\sigma U\rceil$ ({doc}`spotlight`).

Order of choices
: Loss exponents $e_D,e_L$ first, then the zero, then $\theta$, then $\varepsilon$ ({ref}`comp-choreography`).

**The estimate**

$e_D$, $e_L$
: The divisibility and loss exponents of the geometric family; the archive fixes $e_D=2$, $e_L=0$,
  giving the exponent $\tfrac12+9\varepsilon$.

Finite character comparison
: `core_gm` with `ch_core` and `ch_top`: subgroup orthogonality and a shared main term turn a
  geometric discrepancy bound into $G_\Lambda(x)\le x^{1/2+(e_D+e_L+7)\varepsilon}$ ({ref}`comp-comparison`).

Chain length $m$
: The number of successive theta lifts; `RankVal` puts $m$ between $\sqrt{x\delta_1}$ and $2\sqrt{x\delta_1}$,
  $\delta_1=x^{-\varepsilon/8}$ — the "square root" of the argument ({ref}`comp-family`).

Theta lift
: A transfer of automorphic forms between groups in a dual pair, built from a theta kernel; iterated
  here along a chain of unitary groups.

`TopG`
: The archive's proposition that suitable geometric families with uniform losses exist for every
  admissible requirement and width; premise of the second verified cut.

Hosts
: Arithmetic data on which the comparison is evaluated at a scale; `supplyChi` produces them for each
  primitive character at width $\tfrac32$ ({ref}`comp-hosts`).

**The arithmetic supply**

`VWinAt ψ 401`
: The cohomological window for $\psi$: for $0<\varepsilon<\tfrac1{52}$ and admissible auxiliary primes,
  weighted lengths of locally trivial $H^1$ of twisted modules, for twists below $\lfloor x^{401}\rfloor$, are
  at most $\sqrt{\exp(x^\varepsilon)}$ at every $x$ of an interval $[Y,Y^2]$ ({ref}`comp-cohomology`).

Exceptional twist
: A twist $h\le Z$ that is $\ell$-adically closer than $\ell^{-\lfloor\log_\ell Z\rfloor}$ to a centre of the
  determinant estimate; at most one per centre ({doc}`windows`).

`window1`
: The real-variable lemma that finds $[y,2y]$ avoiding finitely many intervals $[a,Ba)$ with
  $y\ge U/(2^{R+2}B^R)$.

Auxiliary primes $q,d$
: Primes with prescribed congruences and sizes chosen by `QH.pairEx`, with square-root bounds for the
  prime sums of quadratic twists ({ref}`comp-primes`).

Behrend set
: Integer vectors of fixed norm encoded in base $4Ld$; free of short affine relations ({doc}`behrend`).

Galois row `Row0b`
: The local–global statement: Galois representations attached to regular algebraic polarized cuspidal
  representations of $\mathrm{GL}_a$ over CM fields, with Frobenius–Satake compatibility
  ({ref}`comp-galois`).

Seven inputs
: The arguments `P`, `F`, `hA`, `hM`, `hX`, `hL`, `hV` of the decisive assembly theorem
  ({ref}`comp-inputs`).

**Verification**

The tiers, as defined in the component model:

```{code-cell} ipython3
:tags: [remove-input]
bd.show("\n\n".join(f"{bd.tier_badge(t, short=True)} {bd.esc(m['tiers'][t]['label'])}\n: {bd.esc(m['tiers'][t]['meaning'])}"
                      for t in bd.TIER_ORDER))
```

Transitive axioms
: Lean's `#print axioms`: the axioms a constant depends on, through everything it uses. The admissible
  set here is `propext`, `Classical.choice`, `Quot.sound`.

Closure
: The set of original modules a checked declaration imports, compiled for the check; a declaration
  called by a checked one is *inside a checked closure*.

Fresh replay
: Rechecking a proof from an empty kernel environment, including the imported Mathlib constants.

NanoDA
: An independent type checker for Lean, written in Rust; it checked the exported proof of the first cut.

Cut
: A machine-checked implication from explicit premises to an endpoint ({ref}`cuts`).

Pinned link
: A link to a fixed commit of the public mirror of the archive, whose tree was verified to be identical
  to the published archive ({doc}`references`).
