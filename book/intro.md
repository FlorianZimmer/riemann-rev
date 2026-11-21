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

# The architecture of the announced proof of the Riemann hypothesis

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
import bookdata as bd

m = bd.model()
src = bd.archive_sources()
# guards for the counts and constants quoted in the prose of this page
assert len(m['strata']) == 4 and len(m['components']) == 14 and len(m['cuts']) == 2
assert len(m['timeline']) == 20
assert sum(1 for n in m['nodes'] if n['kind'] == 'export') == 5
assert bd.facts()['balance']['total_eps'] == '9'
assert 'width $3/2$' in bd.comp('hosts')['gist'] and 'Y^{3/2}' in bd.cut('cut-zeta')['premise']
assert '\\sqrt x' in bd.comp('family')['gist']
bd.glue('n_modules', f"{src['lean_files']:,}")
bd.glue('as_of', bd.as_of())
bd.glue('n_decls', sum(1 for n in m['nodes'] if n['declaration']))
bd.glue('n_itin', len(m['itineraries']))
bd.glue('mirror_short', m['pins']['mirror_commit'][:8])
```

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.figure_md('hero', 'fig-hero', figclass='hero'))
```

On 20 November 2026 Levent Alpöge announced a proof of the Riemann hypothesis and of the
generalized Riemann hypothesis for Dirichlet $L$-functions, accompanied by a Lean archive of
{glue:text}`n_modules` modules whose final theorems state these results in Mathlib's own
language. This book is an illustrated atlas and blueprint of the **architecture** of that
argument, written for a mathematician who knows the zeta function and wants to see

1. the gist of each component of the argument in standard mathematical language,
2. how the components fit together,
3. precise, pinned links to the Lean declarations (all source links point to commit
   {glue:text}`mirror_short` of the public mirror of the archive), and
4. exactly what has and has not been machine-checked, with time stamps.

The announcement is a **claim**. Nothing in this book asserts that the Riemann hypothesis has been
proved. The book separates kernel-checked implications (whose premises remain hypotheses),
source-read components, the recorded replays of the complete formal proof, and motivation; what a
formal check does and does not establish is discussed in {doc}`verification`.

## The announced argument in three sentences

1. **Analytic engine.** If a centered, ramp-weighted sum over prime powers, taken for a *positive*
   combination of Dirichlet characters, is bounded *from above* by $C\,y^{\theta}$ at every point of
   arbitrarily late windows $[Y, Y^{3/2}]$, then none of the corresponding $L$-functions vanishes in
   $\Re s>\theta$; this localized Landau argument, and the classical reductions by conductor descent
   and the functional equation that turn such half-plane statements into the critical-line
   statements, are machine-checked.
2. **The estimate.** The archive claims such bounds with $\theta=\tfrac12+9\varepsilon$ for every small
   $\varepsilon>0$, by comparing the prime sum, through a finite character-orthogonality computation,
   with arithmetic data attached to a chain of about $\sqrt x$ theta lifts — the square root is where
   two competing costs $x/m$ and $m$ balance.
3. **Arithmetic supply.** The chain, its hosts and the uniformity in $\varepsilon$ are claimed to come
   from Galois representations attached to automorphic representations, auxiliary primes and Behrend
   sets, and a bound for Galois cohomology along cyclotomic towers; apart from a few kernel-checked
   steps these producers have been read at the source rather than replayed one by one; they are part
   of the complete proof, whose replays are recorded in {doc}`verification`.

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.status_box())
```

## How to read this book

* **Ten minutes.** Read {doc}`map`: the four strata, the fourteen components, the interfaces
  between them, and the two machine-checked implications ("cuts") with their premises.
* **The mathematics.** The chapters {doc}`destination`, {doc}`engine`, {doc}`estimate` and
  {doc}`supply` follow the argument backwards, from the five exported theorems to the arithmetic
  input. Every component section opens with a generated card (gist, statement, explanation, figure,
  pinned Lean declarations, verification tier, what remains to check) followed by a more detailed
  mathematical discussion.
* **The computations.** Five executed notebooks recompute what the figures show: the explicit
  formula behind the centered prime sum, the spotlight kernel of the window criterion, the exact
  exponent budget, the interval lemma and ultrametric separation, and a Behrend digit sphere.
* **The formal record.** {doc}`formalization` quotes this repository's compilable Lean skeleton
  and the archive bridges; {doc}`blueprint` lists all {glue:text}`n_decls` declarations of the reading
  project's map;
  {doc}`verification` is the ledger of what was checked, by whom, and when; {doc}`timeline` maps the
  announcement's twenty dated entries to the components.

The reading project proposes {glue:text}`n_itin` itineraries through the blueprint:

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for k, it in enumerate(m['itineraries'], 1):
    first = bd.node(it['nodes'][0])['title']
    last = bd.node(it['nodes'][-1])['title']
    rows.append(f"{k}. **{bd.esc(it['title'])}.** *{bd.esc(it['question'])}* "
                f"({len(it['nodes'])} steps, from “{bd.esc(first)}” to “{bd.esc(last)}”; see {{ref}}`itineraries`.)")
bd.show("\n".join(rows))
```

## Companions

```{code-cell} ipython3
:tags: [remove-input]
ax = bd.axioms()
atlas = bd.companion('atlas')
pdf = bd.companion('blueprint')
vault = bd.ROOT / 'vault' / 'Home.md'
nfig = len(list(bd.FIGURES.glob('*.svg')))
rows = [
    ["Interactive atlas: master map, blueprint graph with Lean links, ideas, ledger",
     (f'<a href="_static/atlas/index.html">open the atlas</a> ({atlas.stat().st_size:,} bytes, '
      'single self-contained file)') if atlas else '<span class="pending">pending: atlas</span>'],
    ["Illustrated PDF blueprint",
     f'<a href="_static/blueprint/atlas-blueprint.pdf">atlas-blueprint.pdf</a>' if pdf
     else '<span class="pending">pending: PDF blueprint (blueprint/atlas-blueprint.pdf)</span>'],
    *([["Obsidian vault: one note per component, concept and blueprint node",
        "`vault/Home.md` (open the folder `vault/` in Obsidian)"]] if vault.is_file() else []),
    ["Compilable Lean library (no imports)",
     f"{{doc}}`formalization` — `lake build` {ax['build']}, {ax['warnings']} warnings, "
     f"{len(ax['declarations'])} audited declarations"],
    ["Computed figures", f"{nfig} SVG files in `assets/figures/`, numbers in `assets/figures/facts.json`"],
]
bd.show(bd.md_table(["Companion", "Where"], rows))
```

## Conventions

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.tiers_table())
```

Stratum colours follow the atlas: the destination, the analytic engine, the estimate and the
arithmetic supply. Numbers on every page are recomputed or read from the repository's data files
when the book is built; hidden assertions stop the build if a quoted number disagrees with
`data/model.json`, `assets/figures/facts.json` or `verification/logs/axioms.json`. The data of
the reading project were imported with SHA-256 checksums (see {doc}`references`); its status record
is quoted with its time stamp ({glue:text}`as_of`) and later developments are not reflected here
until the next import.
