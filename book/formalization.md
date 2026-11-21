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

# The Lean library and the archive bridges

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
import hashlib
import re
import bookdata as bd

ax = bd.axioms()
LEAN = bd.ROOT / 'lean'
files = sorted(p for p in LEAN.rglob('*.lean') if '.lake' not in p.parts)
library = {'Atlas', 'Reading'}
for p in files:
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.startswith('import '):
            assert line.split()[1].split('.')[0] in library, (p, line)   # no external imports
assert ax['build'] == 'passed' and ax['warnings'] == 0 and ax['problems'] == []
version = re.search(r'version (\d+\.\d+\.\d+)', ax['lean']).group(1)
toolchain = (LEAN / 'lean-toolchain').read_text().strip()
assert toolchain.endswith(version), (toolchain, version)
bd.glue('lean_version', version)
bd.glue('n_decl', len(ax['declarations']))
bd.glue('n_free', len(ax['axiom_free']))
bd.glue('n_files', len(files))
bd.glue('audit_time', ax['generated_utc'].replace('T', ' ').replace('+00:00', ' UTC'))
assert 'Lean 4.35.0' not in bd.model()['pins']['toolchain'] and bd.model()['pins']['toolchain'].endswith('v4.33.1')
bd.glue('archive_toolchain', bd.model()['pins']['toolchain'].split(':')[-1])
```

This repository contains a small Lean library that compiles on its own (Lean
{glue:text}`lean_version`, **no imports** — not even Mathlib): an axiom-free skeleton of the
architecture, an ultrametric separation lemma, and two teaching files from the reading project. It
does not, and cannot, prove anything about $\zeta$. Its purpose is to state precisely how the
components compose, and to make the shape of the two verified cuts checkable by anyone in seconds.
The reading project's *archive bridges*, which do talk about Mathlib's $\zeta$, compile only against
the original archive ({glue:text}`archive_toolchain` with its Mathlib pin) and are quoted at the end
with what their receipts establish.

## Build and axiom audit

`cd lean && lake build` builds the libraries `Atlas`, `Reading` and `AtlasAudit`; the last one
prints the transitive axioms of every theorem, and `scripts/lean_audit.py` parses that output into
`verification/logs/axioms.json` (generated {glue:text}`audit_time`). Of the
{glue:text}`n_decl` audited declarations, {glue:text}`n_free` depend on no axioms at all.

```{code-cell} ipython3
:tags: [remove-input]
texts = {p: p.read_text(encoding='utf-8') for p in files}
def where(decl):
    short = decl.split('.')[-1]
    pat = re.compile(r'^\s*(?:private\s+)?(?:theorem|def|lemma|abbrev|structure|instance)\s+(?:[\w.]*\.)?'
                     + re.escape(short) + r'\b', re.M)
    hits = [p for p, t in texts.items() if pat.search(t)]
    return hits[0].relative_to(bd.ROOT).as_posix() if hits else '?'
rows = []
for decl, axs in ax['declarations'].items():
    rows.append([f"`{decl}`", where(decl).split('/')[-1], ', '.join(axs) if axs else '**none**'])
assert all(r[1] != '?' for r in rows)
bd.show(bd.md_table(['Declaration', 'File', 'Transitive axioms'], rows))
```

The standard axioms that appear (`propext`, `Classical.choice`, `Quot.sound`) are the three that
Mathlib itself uses; the skeleton needs none of them.

```{literalinclude} ../verification/logs/lean-build.log
:language: text
:caption: verification/logs/lean-build.log
```

(lean-skeleton)=
## The skeleton: `Atlas/Architecture.lean`

The file models the argument over abstract types. A `Plane` carries points, characters, the zero
relation and the geometric predicates; the classical facts are fields of the structures
`Reflection` and `Descent`; the analytic engine and the arithmetic supply are structures `Engine`
and `Supply` whose fields are exactly the interfaces of the component model. The theorems then prove
only how these compose.

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- The objects the endpoints talk about."
:end-before: "variable (P : Plane)"
:caption: The objects
```

The three target statements: Mathlib's RH transported to the abstract plane, the half-plane theorem
for all characters, its primitive version, and Dirichlet GRH in the strip.

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- Mathlib's `RiemannHypothesis`, transported"
:end-before: "/-! ## The destination: reflection and conductor descent -/"
:caption: The targets
```

The destination ({doc}`destination`): reflection and conductor descent as structures of classical
facts, and the three closing deductions.

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- Classical facts used by the closing deductions."
:end-before: "variable {P}"
:caption: Reflection and descent
```

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- Primitive half-plane ⇒ half-plane for every character"
:end-before: "/-! ## The analytic engine and the arithmetic supply -/"
:caption: The closing deductions
```

The analytic engine ({doc}`engine`) and the arithmetic supply. `Engine.criterion` is the window
criterion; `Supply.windows` is what the estimate and the arithmetic have to deliver, with the loss
fixed before $\varepsilon$; `Supply.choose` is the order of choices.

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- The analytic engine over an abstract scale of exponents."
:end-before: "/-- The supply and the engine give the primitive half-plane"
:caption: Engine and supply
```

The two verified cuts, mirrored: `endpoints_of_supply` has the shape of the Dirichlet bridge and
`rh_of_prime_windows` the shape of the window bridge (both quoted below).

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- The supply and the engine give the primitive half-plane"
:end-before: "/-! ## The whole architecture in one record -/"
:caption: The cuts, abstractly
```

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- The four layers of the argument bundled together."
:end-before: "/-! ## The hypotheses are satisfiable, with zeros present"
:caption: The whole architecture in one record
```

(lean-toy)=
## The hypotheses are satisfiable

A skeleton whose hypotheses were contradictory would prove anything. The toy model below — a plane
with three kinds of points, one character and zeros exactly on the line — satisfies every field, and
the final `example` shows that the skeleton's conclusion holds there *together with* the existence of
a zero. It says nothing about which model is the real one.

```{literalinclude} ../lean/Atlas/Architecture.lean
:language: lean4
:start-at: "/-- Left of, on, or right of the critical line. -/"
:end-before: "end Atlas"
:caption: The toy model
```

(lean-separation)=
## Ultrametric separation: `Atlas/Separation.lean`

The integer core of the exceptional-twist count of {ref}`comp-cohomology`, with the example of the
reading guide and the failure of the weak inequality (computed in {doc}`windows`).

```{literalinclude} ../lean/Atlas/Separation.lean
:language: lean4
:caption: lean/Atlas/Separation.lean
```

(lean-teaching)=
## Teaching files from the reading project

Two files written by the reading project, imported with SHA-256 checksums. `WindowLogic.lean`
isolates the pure logic of the window argument and of reflection; `BehrendSphere.lean` proves the
chord identity and the sphere lemma behind the Behrend construction ({doc}`behrend`) in every
finite dimension.

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for f in bd.provenance()['files']:
    if f['to'].startswith('lean/') or f['to'].startswith('references/'):
        now = hashlib.sha256((bd.ROOT / f['to']).read_bytes()).hexdigest()
        rows.append([f"`{f['to']}`", f"`{f['from']}`", f"`{f['sha256'][:16]}…`",
                     'identical' if now == f['sha256'] else '**differs from the import**'])
bd.show(bd.md_table(['File here', 'In the reading project', 'SHA-256 at import', 'Now'], rows))
```

```{literalinclude} ../lean/Reading/WindowLogic.lean
:language: lean4
:caption: lean/Reading/WindowLogic.lean
```

```{literalinclude} ../lean/Reading/BehrendSphere.lean
:language: lean4
:caption: lean/Reading/BehrendSphere.lean
```

The audit driver:

```{literalinclude} ../lean/Atlas/Audit.lean
:language: lean4
:caption: lean/Atlas/Audit.lean
```

(lean-mathlib)=
## The destination layer, with Mathlib's ζ

The skeleton is abstract. The file `lean-mathlib/AtlasZeta.lean` instantiates its plane with the
complex numbers and Mathlib's `riemannZeta`, at the archive's own pins (Lean 4.33.1, Mathlib
`0df444a3`), and proves every field of `Reflection` and `Descent` for this plane from Mathlib's
functional equation, the nonvanishing of $\zeta$ on $\Re s\ge 1$ and the zeros of $\cos$ and
$\Gamma$. The skeleton's `rh_of_halfPlane` then gives the classical last step: nonvanishing of
$\zeta$ for $\Re s>\tfrac12$ implies Mathlib's `RiemannHypothesis`. This re-checks the last page of
the argument independently of the archive; it says nothing about the half-plane statement itself.

```{literalinclude} ../lean-mathlib/AtlasZeta.lean
:language: lean4
:caption: lean-mathlib/AtlasZeta.lean (the plane, and the two identifications)
:start-at: "/-- The abstract plane with `Point = ℂ`"
:end-before: "/-- A point of positive real part is not a non-positive integer. -/"
```

```{literalinclude} ../lean-mathlib/AtlasZeta.lean
:language: lean4
:caption: lean-mathlib/AtlasZeta.lean (the conclusion)
:start-at: "/-- **The destination layer, checked against Mathlib**"
:end-before: "end Atlas.Zeta"
```

Mathlib is too large for the machine this book is built on, so the file is compiled on a cluster
(`scripts/helios_mathlib.sh`, see `BUILDING.md`). The log of that build is kept in the
repository, with the axioms of the three main declarations:

```{literalinclude} ../verification/logs/mathlib-zeta-build.log
:language: text
:caption: verification/logs/mathlib-zeta-build.log
```

(lean-bridges)=
## The archive bridges

The reading project wrote four short files that import modules of the original archive and state
the conditional theorems in Mathlib's language. They compile only inside the archive's environment
and were compiled by the reading project on the Helios cluster; they are kept here as references,
with the receipts summarized from `data/source/native-scopes.json`. A receipt certifies that the
stated theorem — *with its hypotheses* — was elaborated and kernel-checked at the archive pins, with
the listed transitive axioms. It does not certify the hypotheses.

### One-sided prime windows imply RH

```{literalinclude} ../references/archive-bridges/WindowBridge.lean
:language: lean4
:caption: references/archive-bridges/WindowBridge.lean
```

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.scope_md('core') + "\n\n" + bd.scope_md('fresh-core'))
```

```{code-cell} ipython3
:tags: [remove-input]
iw = bd.model()['status']['independent_window']
bd.show(f"**Second kernel.** The proof of `riemannHypothesis_of_prime_windows` was exported as a "
        f"stream of {iw['declarations']:,} declarations ({iw['raw_bytes']:,} bytes raw, "
        f"{iw['compressed_bytes']:,} compressed; compressed SHA-256 `{iw['compressed_sha256'][:16]}…`) and "
        f"accepted by the independent Rust kernel NanoDA. Evidence summary from the model: "
        f"{bd.esc(bd.cut('cut-zeta')['evidence'])}")
```

### The geometric normalization

```{literalinclude} ../references/archive-bridges/GeometricTransport.lean
:language: lean4
:caption: references/archive-bridges/GeometricTransport.lean
```

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.scope_md('geometric'))
```

### TopG and the cohomological windows imply RH and Dirichlet GRH

```{literalinclude} ../references/archive-bridges/DirichletBridge.lean
:language: lean4
:caption: references/archive-bridges/DirichletBridge.lean
```

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.scope_md('dirichlet'))
```

### The five exports

`EndpointAudit.lean` restates the five exported types of `Main.lean` and asks for their axioms. It
belongs to the reading project's *exact endpoint replay*, the first open item in {doc}`verification`.

```{code-cell} ipython3
:tags: [remove-input]
e = bd.comp('endpoints')
bd.show(f"{bd.tier_badge(e['tier'])} *Status of the five exports in the imported record ({bd.as_of()}):* "
        f"{bd.esc(e['status'])}\n\n*Still to check:* {bd.esc(e['check'])}")
```

```{literalinclude} ../references/archive-bridges/EndpointAudit.lean
:language: lean4
:caption: references/archive-bridges/EndpointAudit.lean
```

### What the receipts establish

* The window bridge: *if* the zeta prime sum satisfies the one-sided bound on arbitrarily late
  windows $[Y,Y^{3/2}]$ for every $\theta\in(\tfrac12,1)$, *then* Mathlib's `RiemannHypothesis` holds —
  checked twice, by Lean (including a fresh replay of the Mathlib imports) and by NanoDA.
* The Dirichlet bridge: *if* `TopG` holds and `VWinAt ψ 401` holds for every primitive $\psi$, *then*
  RH, the half-plane theorem for every character and Dirichlet GRH in the open strip hold — checked by
  Lean at the archive pin.
* Neither receipt says anything about the truth of its premises. The premises are produced in the
  archive by the components of {doc}`estimate` and {doc}`supply`, whose status is recorded component
  by component in {doc}`verification`.
