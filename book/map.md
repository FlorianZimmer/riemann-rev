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

# Map of the argument

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
import bookdata as bd

m = bd.model()
assert len(m['strata']) == 4 and len(m['components']) == 14 and len(m['cuts']) == 2
assert len(m['interfaces']) == 14
# the cut headings below are typed; they must agree with the model
assert bd.cut('cut-zeta')['title'] == 'One-sided prime windows imply RH'
assert bd.cut('cut-dirichlet')['title'] == 'TopG and the cohomological windows imply RH and Dirichlet GRH'
assert '\\mathrm{VWinAt}\\ \\psi\\ 401' in bd.cut('cut-dirichlet')['premise']
assert 'Y^{3/2}' in bd.cut('cut-zeta')['premise']
bd.glue('n_ifaces', len(m['interfaces']))
bd.glue('zeta_comps', len(bd.cut('cut-zeta')['components']))
bd.glue('dir_comps', len(bd.cut('cut-dirichlet')['components']))
bd.glue('n_nodes', len(m['nodes']))
```

The argument has four strata. Read in the direction of the logic, the **arithmetic supply**
produces families of arithmetic objects; **the estimate** turns them into an upper bound for a
weighted prime sum on long windows; the **analytic engine** turns such bounds into zero-free
half-planes; and **the destination** turns the half-plane theorem into the five exported
statements. The chapters of this book take the reverse order, from the claimed theorems back to
the input they need.

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.strata_table())
```

(component-graph)=
## The component graph

The fourteen components and the {glue:text}`n_ifaces` interfaces of the model, drawn from
`data/model.json`. Arrows point in the direction of the logic (supply at the top, the exported
theorems at the bottom); each box carries its verification tier, and the pills **Z** and **D**
mark the components through which the two machine-checked implications run. The two dashed arrows
are exactly the premises of the second cut; the premise of the first cut enters the window criterion
from outside the model's interfaces (a bound for the zeta prime sum alone).

```{code-cell} ipython3
:tags: [remove-input]
import textwrap
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

bd.plot_style()
P = bd.PALETTE
comps = {c['id']: c for c in m['components']}
G = nx.DiGraph()
G.add_nodes_from(comps)
G.add_edges_from((i['from'], i['to']) for i in m['interfaces'])
assert nx.is_directed_acyclic_graph(G)
layer = {}
for v in nx.topological_sort(G):                      # longest path from a source
    layer[v] = 1 + max((layer[u] for u in G.predecessors(v)), default=-1)
# horizontal lanes (a drawing choice): analytic column right, the two arithmetic chains left
lane = {'statistic': 2.4, 'residues': 2.4, 'criterion': 2.4,
        'primes': 1.2, 'cohomology': 1.2, 'hosts': 1.2,
        'galois': 0.0, 'inputs': 0.0, 'family': 0.0,
        'comparison': 0.6, 'choreography': 1.5, 'descent': 1.5, 'reflection': 1.5, 'endpoints': 1.5}
assert set(lane) == set(comps)
pos = {v: (lane[v], -layer[v]) for v in comps}
W, H = 1.1, 0.72
in_cut = {k['id']: set(k['components']) for k in m['cuts']}
premise_edges = {('family', 'comparison'), ('cohomology', 'hosts')}

fig, ax = plt.subplots(figsize=(8.8, 10.6))
ax.set_axis_off()
for (a, b) in G.edges:
    (xa, ya), (xb, yb) = pos[a], pos[b]
    prem = (a, b) in premise_edges
    arr = FancyArrowPatch((xa, ya - H / 2), (xb, yb + H / 2), arrowstyle='-|>', mutation_scale=11,
                          color=P['accent'] if prem else P['faint'], lw=1.7 if prem else 1.2,
                          linestyle=(0, (4, 3)) if prem else '-', shrinkA=2, shrinkB=2, zorder=1)
    ax.add_patch(arr)
    label = next(i['label'] for i in m['interfaces'] if i['from'] == a and i['to'] == b)
    mx, my = (xa + xb) / 2, (ya - H / 2 + yb + H / 2) / 2
    ax.text(mx, my, label, ha='center', va='center', fontsize=8.6,
            color=P['accent'] if prem else P['muted'],
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='none', alpha=0.92), zorder=3)
# the premise of the zeta cut enters the criterion from outside
xc, yc = pos['criterion']
ax.add_patch(FancyArrowPatch((xc + 0.36, yc - 0.86), (xc + 0.36, yc - H / 2), arrowstyle='-|>',
                             mutation_scale=11, color=P['accent'], lw=1.7, linestyle=(0, (4, 3)), zorder=1))
ax.text(xc + 0.2, yc - 0.9, 'premise of Z:\none-sided windows\nfor G alone', fontsize=8.6, color=P['accent'],
        ha='left', va='top')
for v, (x, y) in pos.items():
    c = comps[v]
    col = bd.stratum(c['stratum'])['color']
    T = bd.tier(c['tier'])
    ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H, boxstyle='round,pad=0.02,rounding_size=0.06',
                                fc=col + '1a', ec=col, lw=1.6, zorder=2))
    title = textwrap.fill(f"{c['n']}. {c['title']}", 24)
    ax.text(x - W / 2 + 0.05, y + H / 2 - 0.08, title, ha='left', va='top', fontsize=10.5,
            color=P['ink'], fontweight=bd.SEMIBOLD, zorder=4, linespacing=1.15)
    ax.text(x - W / 2 + 0.05, y - H / 2 + 0.07, f"{T['icon']} {bd.SHORT_TIER[c['tier']]}", ha='left',
            va='bottom', fontsize=8.8, color=T['color'], zorder=4, fontweight=bd.SEMIBOLD)
    tags = [t for t, key in (('Z', 'cut-zeta'), ('D', 'cut-dirichlet')) if v in in_cut[key]]
    for k, t in enumerate(tags):
        tc = bd.tier(bd.cut('cut-zeta' if t == 'Z' else 'cut-dirichlet')['tier'])['color']
        ax.text(x + W / 2 - 0.05 - 0.13 * (len(tags) - 1 - k), y - H / 2 + 0.07, t, ha='right', va='bottom',
                fontsize=8.4, color='white', fontweight='bold', zorder=5,
                bbox=dict(boxstyle='round,pad=0.2', fc=tc, ec='none'))
# legend: strata
for k, sid in enumerate(bd.STRATUM_ORDER):
    s = bd.stratum(sid)
    ax.add_patch(FancyBboxPatch((-0.55, -7.55 + 0.32 * k), 0.16, 0.18, boxstyle='round,pad=0.01',
                                fc=s['color'] + '1a', ec=s['color'], lw=1.4))
    ax.text(-0.33, -7.46 + 0.32 * k, s['title'], fontsize=9.4, va='center', color=P['text'])
ax.text(-0.55, -7.55 + 0.32 * 4 + 0.02, 'Strata', fontsize=9.8, fontweight=bd.SEMIBOLD, color=P['ink'])
ax.text(-0.55, -6.05, 'Z: in the cut "prime windows ⇒ RH"\nD: in the cut "TopG ∧ VWinAt ⇒ RH ∧ GRH"',
        fontsize=9, color=P['text'], va='bottom', linespacing=1.4)
ax.set_xlim(-0.62, 3.3)
ax.set_ylim(-max(layer.values()) - 0.55, 0.62)
ax.set_aspect('auto')
plt.tight_layout()
plt.show()
```

## The fourteen components

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.components_table())
```

## The interfaces

Each interface is a proposition (or a structure) produced by one component and consumed by the
next; the last column names the Lean declaration that realizes it in the archive.

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.interfaces_table())
```

(cuts)=
## The two verified cuts

A **cut** is a Lean theorem, compiled against the original archive, whose hypotheses are exactly
the inputs on one side of a line drawn through the component graph and whose conclusion is an
endpoint. A cut certifies an *implication*. Its premise is not checked by it: the premise is
precisely the part of the argument that remains to be supplied — in the archive, by the components
on the other side of the line.

(cut-zeta)=
### One-sided prime windows imply RH

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.cut_md('cut-zeta'))
```

The family here is the singleton $\{\zeta\}$ (the character of modulus one with weight one), so
only {glue:text}`zeta_comps` components are involved and no character other than the trivial one
appears. The premise is *equivalent* to RH: under RH, Schoenfeld's bound for $\psi(x)-x$ gives
$|G(x)|\ll\sqrt x\,\log^2x$ for all large $x$ (see {ref}`window-strength`). The cut therefore does
not make RH easier; it shows that the analytic engine and the closing reductions are correct and
moves the whole difficulty into one explicit, one-sided estimate.

(cut-dirichlet)=
### TopG and the cohomological windows imply RH and Dirichlet GRH

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.cut_md('cut-dirichlet'))
```

This cut runs through {glue:text}`dir_comps` components and stops at two named propositions of the
archive: `UpperTheory.Top.TopG`, a statement about families of arithmetic data (its producer is
{ref}`comp-family`), and `UpperTheory.Top.VWinAt ψ 401` for every primitive character $\psi$, the
cohomological window (its producer is {ref}`comp-cohomology`). Everything below the dashed arrows
of the component graph is machine-checked as an implication; everything above them — the theta
chain, the Galois row, the seven literature-shaped inputs, the producers of the cohomology bound —
lies outside both cuts. Its status is recorded component by component in {doc}`verification`:
mostly source-read, with some kernel-checked steps whose own premises are explicit, and all of it
inside the complete proof whose replays are listed there.

## What the map shows and what it does not

* The arrows are the model's interfaces, not the full dependency graph of the archive; the
  reading project's map of {glue:text}`n_nodes` nodes is in {doc}`blueprint`.
* A component's tier summarizes the evidence for its *own* deductions. A checked component may
  still consume an unchecked input; that input is then shown as a premise.
* The five exported theorems carry no explicit arithmetic premise in their Lean types; whether the
  terms that discharge the premises are correct is what the replays of the complete proof and the
  open audit questions in {doc}`verification` are about.
