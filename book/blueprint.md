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

# The blueprint

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
from collections import Counter
import bookdata as bd

m = bd.model()
# the component headings below are typed; they must agree with the model
headings = {1: 'The five endpoints', 2: 'Reflection', 3: 'Conductor descent', 4: 'The centered prime sum',
            5: 'Mellin transform and positive residues', 6: 'The window criterion', 7: 'The order of choices',
            8: 'The finite character comparison', 9: 'The geometric family and the theta chain',
            10: 'Hosts for every character', 11: 'The cohomological window',
            12: 'Auxiliary primes and Behrend towers', 13: 'The Galois row', 14: 'Seven inputs at the decisive call'}
assert {c['n']: c['title'] for c in bd.comps()} == headings
owned = [n for c in m['components'] for n in c['nodes']]
assert sorted(owned) == sorted(n['id'] for n in m['nodes'])          # every node owned exactly once
bd.glue('n_nodes', len(m['nodes']))
n_decl = sum(1 for n in m['nodes'] if n['declaration'])
n_ideas = sum(1 for n in m['nodes'] if not n['declaration'])
assert n_decl + n_ideas == len(m['nodes']) and all(n['kind'] == 'motivation' for n in m['nodes'] if not n['declaration'])
bd.glue('n_decl', n_decl)
bd.glue('n_ideas', n_ideas)
bd.glue('n_itin', len(m['itineraries']))
bd.glue('n_edges', len(m['edges']))
bd.glue('n_sections', len(m['sections']))
```

The reading project traced the archive's proof of the five exports through a map of
{glue:text}`n_nodes` nodes — {glue:text}`n_decl` Lean declarations and {glue:text}`n_ideas` ideas
from the announcement — connected by {glue:text}`n_edges` labelled edges (calls, statement
dependencies, bundle fields, supporting lemmas, analogies). Each declaration is pinned to exact
lines of the public mirror of the archive and comes with a *contract* in mathematical language and
an *idea* of its proof. This book assigns every declaration to exactly one of the fourteen components
and gives it a verification tier computed from the receipts (see {doc}`verification`).

```{code-cell} ipython3
:tags: [remove-input]
import re
svg_head = (bd.FIGURES / 'blueprint-graph.svg').read_text(encoding='utf-8')[:400]
natural = int(re.search(r'width="(\d+)"', svg_head).group(1))
bd.show("The static rendering below is wide: scroll it horizontally, or click it to open the SVG; "
        + bd.atlas_link('blueprint', 'the interactive graph is in the atlas ↗') + "\n\n"
        + bd.figure_md('blueprint-graph', 'fig-blueprint-graph', width=f'{natural}px', figclass='scroll-x'))
```

```{code-cell} ipython3
:tags: [remove-input]
tiers = Counter(n['tier'] for n in m['nodes'])
kinds = Counter(n['kind'] for n in m['nodes'])
rels = Counter(e['relation'] for e in m['edges'])
rows_t = [[bd.tier_badge(t, short=True), bd.esc(m['tiers'][t]['label'], True), str(tiers[t])]
          for t in bd.TIER_ORDER if tiers[t]]
bd.show(bd.md_table(['Tier', '', 'Nodes'], rows_t, '---|---|--:') + "\n\n"
        + "**Kinds of node:** " + ", ".join(f"{k} ({v})" for k, v in kinds.most_common()) + ".  \n"
        + "**Kinds of edge:** " + ", ".join(f"{k} ({v})" for k, v in rels.most_common()) + ".")
```

(itineraries)=
## Itineraries

The reading project proposes {glue:text}`n_itin` paths through the blueprint, each answering one
question.

```{code-cell} ipython3
:tags: [remove-input]
parts = []
for k, it in enumerate(m['itineraries'], 1):
    parts.append(f"**{k}. {bd.esc(it['title'])}.** " + bd.itinerary_md(it))
bd.show("\n\n".join(parts))
```

## Declarations by component

Each table lists the component's declarations in the order of the reading project's map; the
dropdown below it prints the Lean source of each declaration as recorded in `data/model.json`
(the pinned link gives the full context).

(bp-endpoints)=
### 1 · The five endpoints

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('endpoints') + "\n\n" + bd.node_excerpts('endpoints'))
```

(bp-reflection)=
### 2 · Reflection

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('reflection') + "\n\n" + bd.node_excerpts('reflection'))
```

(bp-descent)=
### 3 · Conductor descent

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('descent') + "\n\n" + bd.node_excerpts('descent'))
```

(bp-statistic)=
### 4 · The centered prime sum

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('statistic') + "\n\n" + bd.node_excerpts('statistic'))
```

(bp-residues)=
### 5 · Mellin transform and positive residues

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('residues') + "\n\n" + bd.node_excerpts('residues'))
```

(bp-criterion)=
### 6 · The window criterion

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('criterion') + "\n\n" + bd.node_excerpts('criterion'))
```

(bp-choreography)=
### 7 · The order of choices

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('choreography') + "\n\n" + bd.node_excerpts('choreography'))
```

(bp-comparison)=
### 8 · The finite character comparison

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('comparison') + "\n\n" + bd.node_excerpts('comparison'))
```

(bp-family)=
### 9 · The geometric family and the theta chain

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('family') + "\n\n" + bd.node_excerpts('family'))
```

(bp-hosts)=
### 10 · Hosts for every character

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('hosts') + "\n\n" + bd.node_excerpts('hosts'))
```

(bp-cohomology)=
### 11 · The cohomological window

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('cohomology') + "\n\n" + bd.node_excerpts('cohomology'))
```

(bp-primes)=
### 12 · Auxiliary primes and Behrend towers

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('primes') + "\n\n" + bd.node_excerpts('primes'))
```

(bp-galois)=
### 13 · The Galois row

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('galois') + "\n\n" + bd.node_excerpts('galois'))
```

(bp-inputs)=
### 14 · Seven inputs at the decisive call

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.node_table('inputs') + "\n\n" + bd.node_excerpts('inputs'))
```
