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

# The destination: from a half-plane to the five endpoints

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
import bookdata as bd

m = bd.model()
# the section headings of this page are typed; they must agree with the model
expected = {1: 'The five endpoints', 2: 'Reflection', 3: 'Conductor descent'}
assert {c['n']: c['title'] for c in bd.comps('dest')} == expected
assert sum(1 for n in m['nodes'] if n['kind'] == 'export') == 5
ax = bd.axioms()['declarations']
for d in ('Atlas.halfPlane_of_primitive', 'Atlas.strip_of_halfPlane', 'Atlas.rh_of_halfPlane'):
    assert ax[d] == [], d          # quoted below as axiom-free
```

```{code-cell} ipython3
:tags: [remove-input]
s = bd.stratum('dest')
bd.show(f"{bd.stratum_badge('dest')} {bd.esc(s['blurb'])}")
```

The last stratum is classical. Write $\mathrm{HalfPlane}$ for the assertion

$$
\begin{gathered}
L(s,\chi)\neq 0\quad\text{for every Dirichlet character }\chi\bmod N,\ N\ge1, \\
\text{and every } s \text{ with } \Re s>\tfrac12,\ (\chi,s)\neq(\mathbf 1_N,1).
\end{gathered}
$$

The archive calls it `DirichletLNonvanishingRightOfHalf`. Everything on this page explains how the
five exported theorems follow from it, and how it follows from its restriction to **primitive**
characters. These deductions are short, standard and machine-checked; their only role in the
architecture is to make sure that nothing is lost between the analytic statement that the rest of
the argument produces and the statements in Mathlib's language.

(comp-endpoints)=
## 1 · The five endpoints

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.card('endpoints'))
```

### What exactly is exported

The archive's `Main.lean` exports five theorems. Their contracts, as recorded in the reading
project's blueprint, are:

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for n in m['nodes']:
    if n['kind'] == 'export':
        rows.append([f"[{bd.code(n['declaration'])}]({n['url']})", bd.esc(n['contract'], True),
                     bd.tier_badge(n['tier'])])
bd.show(bd.md_table(["Declaration", "Contract", "Tier"], rows))
```

Three conventions matter when one compares these types with the classical statements.

* **Total functions.** Lean's `riemannZeta` and `DirichletCharacter.LFunction` are total
  functions on $\mathbb C$; at the pole they take *some* value. Mathlib's `RiemannHypothesis`
  therefore excludes $s=1$ explicitly, and the half-plane statement excludes the single pair
  $(\chi,s)=(\mathbf 1_N,1)$. Mathlib's value of the totalized $\zeta$ at $s=1$ is
  $(\gamma-\log 4\pi)/2$, which it proves to be nonzero
  ([Mathlib, pinned](https://github.com/leanprover-community/mathlib4/blob/0df444a360eaa60ab8c11dca51a86af692955474/Mathlib/NumberTheory/Harmonic/ZetaAsymp.lean#L416-L449));
  that is why the archive's primitive predicate `ZeroFreeAll` can include $s=1$ for the character of
  modulus one without any exception.
* **Trivial zeros.** The negative even integers are actual zeros of $\zeta$ and are excluded;
  $\zeta(0)=-\tfrac12\neq0$.
* **The open strip.** The all-character critical-line statement quantifies over $0<\Re s<1$, and
  the strict left inequality is necessary: for the principal character modulo $2$,
  $L(s,\mathbf 1_2)=(1-2^{-s})\zeta(s)$ vanishes at $s=2\pi i k/\log 2$ for every integer $k\neq0$,
  on the line $\Re s=0$, and also at $s=0$.

Matching these types with the classical statements is a matter of reading definitions, and the
three conventions above are the whole difference. The announcement's further expectation about
other $L$-functions has no endpoint in the archive.

(comp-reflection)=
## 2 · Reflection

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.card('reflection'))
```

### The two functional equations in use

For $\zeta$ the archive's deduction `Formalism.VW.rh_of_right` uses the asymmetric form

$$
\zeta(s)=2(2\pi)^{-w}\,\Gamma(w)\cos\!\Big(\frac{\pi w}{2}\Big)\zeta(w),\qquad w=1-s .
$$

If $\zeta(s)=0$ with $\Re s<\tfrac12$, then $\Re w>\tfrac12$; the factors $(2\pi)^{-w}$ and
$\Gamma(w)$ do not vanish, and $\cos(\pi w/2)=0$ forces $w$ to be an odd integer, i.e. $s$ an even
integer $\le 0$ — the excluded trivial zeros or $s=0$, where $\zeta(0)\neq0$. Hence $\zeta(w)=0$
with $\Re w>\tfrac12$, which the half-plane statement forbids. (The archive also contains a second
route through Mathlib's completed zeta function; the two zeta exports use the first.)

For a primitive character $\chi$ modulo $q$ with parity $\mathfrak a\in\{0,1\}$, put
$\Lambda(s,\chi)=(q/\pi)^{(s+\mathfrak a)/2}\,\Gamma\big(\tfrac{s+\mathfrak a}2\big)L(s,\chi)$. Then

$$
\Lambda(s,\chi)=\varepsilon(\chi)\,\Lambda(1-s,\bar\chi),\qquad |\varepsilon(\chi)|=1 .
$$

In the open strip the Gamma factor is finite and nonzero, so a zero of $L(s,\chi)$ at $\rho$ gives a
zero of $L(s,\bar\chi)$ at $1-\rho$. The archive's `Claim.prim_reflect` records exactly this, with
$\bar\chi=\chi^{-1}$. The inverse matters when $\chi$ is complex: the reflected zero belongs to a
*different* $L$-function, which is why the half-plane statement must hold for all characters at
once (or at least for a set closed under inversion).

### The deduction, abstractly

The logical skeleton is a trichotomy argument: a zero in the strip lies left of, on, or right of
the critical line; on the right it contradicts the half-plane statement directly, on the left its
reflection does. This repository's Lean skeleton states it over abstract types
(`Atlas.strip_of_halfPlane`, `Atlas.rh_of_halfPlane`), with the analytic facts as fields of a
structure `Reflection`; the build reports both theorems as depending on no axioms at all (see
{ref}`lean-skeleton`).

(comp-descent)=
## 3 · Conductor descent

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.card('descent'))
```

### Why finitely many Euler factors are harmless

Let $\chi$ be a character modulo $N$ induced by the primitive $\chi^*$ of conductor $f\mid N$. Then

$$
L(s,\chi)=L(s,\chi^*)\prod_{p\mid N}\bigl(1-\chi^*(p)\,p^{-s}\bigr),
$$

where only primes $p\mid N$, $p\nmid f$ contribute nontrivially. For $\sigma=\Re s>0$ every factor is
nonzero, since $|\chi^*(p)p^{-s}|\le p^{-\sigma}<1$. So in $\Re s>\tfrac12$ the zeros of $L(s,\chi)$
and of $L(s,\chi^*)$ coincide, and the half-plane statement for primitive characters implies it for
all characters. The principal character is the one case where a pole intervenes: the level-change
formula is used under the side condition $\chi\neq\mathbf 1$ or $s\neq1$, which is exactly the
exception carried by the exported statement.

In the strip the same identity transports zeros *down* to the primitive character, where the
functional equation applies; this is the step `Claim.prim_zero`. The boundary example of the
previous section shows what the strict inequality $\Re s>0$ protects: the factor $1-2^{-s}$ has its
zeros on $\Re s=0$.

### How the destination is checked

The archive's deductions `Formalism.VW.rh_of_right`, `Claim.strip`, `Claim.zeta` and
`UpperTheory.Top.imprimitive` passed the reading project's type, transitive-axiom and replay
checks at the archive's toolchain; the imported statuses, with their scopes, are on the cards above. Independently, this repository mirrors them in an
axiom-free abstract form (`Atlas.halfPlane_of_primitive`, `Atlas.strip_of_halfPlane`,
`Atlas.rh_of_halfPlane`), quoted in {ref}`lean-skeleton`. The abstract version is not a proof about
$\zeta$: it shows which properties of $\zeta$ and of the $L$-functions the closing deductions use,
and that nothing else is needed.
