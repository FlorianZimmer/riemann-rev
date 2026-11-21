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

# The verification ledger

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
import re
import bookdata as bd

m = bd.model()
st = m['status']
prov = bd.provenance()
tot = bd.scope_totals()
# the counts stated in the status text must agree with the imported scopes (each pattern that occurs
# in the current wording is checked; at least the three main counts must be found)
WORDS = {w: i for i, w in enumerate('zero one two three four five six seven eight nine ten eleven twelve'.split())}
def number(tok):
    tok = tok.replace(',', '').lower()
    return int(tok) if tok.isdigit() else WORDS[tok]
expect = {r'(\d+) named original results': len(tot['original']),
          r'(\d+) (?:additional )?reading deductions': len(tot['reading_deductions']),
          r'([\d,]+) distinct original modules': tot['modules'],
          r'(\w+) (?:further )?teaching declarations': len(tot['teaching']),
          r'(\w+) endpoint equivalences and an Euler-factor boundary example': len(tot['statement_checks']) - 1,
          r'([\d,]+)[- ]declarations?\b': st['independent_window']['declarations']}
found = 0
for pat, val in expect.items():
    mm = re.search(pat, st['native'])
    if mm:
        assert number(mm.group(1)) == val, (pat, mm.group(1), val)
        found += 1
assert found >= 3, found
bd.glue('as_of', bd.as_of())
bd.glue('import_time', bd.as_of(prov['imported_utc']))
bd.glue('src_commit', prov['source_commit'][:8])
bd.glue('job', st['job'])
bd.glue('n_original', len(tot['original']))
bd.glue('n_reading', len(tot['reading_deductions']))
bd.glue('n_modules', f"{tot['modules']:,}")
bd.glue('n_scopes', tot['scopes'])
bd.glue('n_teaching', len(tot['teaching']))
bd.glue('n_audit', len(m['audit']))
for t in ('checked', 'covered', 'reported', 'motivation', 'read'):
    bd.glue(f't_{t}', m['tiers'][t]['label'].lower())
export_tiers = {n['tier'] for n in m['nodes'] if n['component'] == 'endpoints' and n['kind'] == 'export'} or \
    {bd.comp('endpoints')['tier']}
assert len(export_tiers) == 1, export_tiers
bd.glue('t_exports', m['tiers'][export_tiers.pop()]['label'].lower())
fp = m['status']['full_proof']
bd.glue('n_stages', len(fp['stages']))
bd.glue('n_statement_checks', len(tot['statement_checks']))
bd.glue('ext_record', bd.status_record().get('external_time') or 'not recorded')
```

This page records what has been machine-checked, by whom and when, and what has not. All of it
is read from the imported record of the reading project (status as of {glue:text}`as_of`, imported
{glue:text}`import_time` from commit {glue:text}`src_commit`) and from this repository's own
Lean audit. The source project continues to run checks; anything it has recorded since then is not
reflected here until the next import (`python3 scripts/import_sources.py`, then
`python3 -B scripts/model.py`).

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.status_box())
```

*In quoted status texts, "this audit" and "our" refer to the reading project's audit.*

## The tiers

Every component and every blueprint declaration carries one of these tiers. For declarations they
are computed in `scripts/model.py`: *{glue:text}`t_checked`* if a native receipt of the reading
project covers the declaration, *{glue:text}`t_covered`* if a checked declaration calls it
(directly or through bundle fields or statements), *{glue:text}`t_motivation`* for the announcement's
historical remarks, and *{glue:text}`t_read`* otherwise. The five exports carry the tier that the record
of the complete proof supports, at present *{glue:text}`t_exports`*. A component's tier summarizes the
evidence for its own deductions.

```{code-cell} ipython3
:tags: [remove-input]
bd.show(bd.tiers_table())
```

## Component by component

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for c in bd.comps():
    rows.append([f"{c['n']}. {{ref}}`{bd.esc(c['title'], True)} <comp-{c['id']}>`",
                 bd.tier_badge(c['tier'], short=True), bd.esc(c['status'], True), bd.esc(c['check'], True)])
bd.show(bd.md_table(['Component', 'Tier', 'Status in the imported record', 'What remains to check'], rows))
```

## The two verified cuts

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for k in m['cuts']:
    rows.append([f"{{ref}}`{bd.esc(k['title'], True)} <{k['id']}>`", bd.tier_badge(k['tier'], short=True),
                 f"`{k['lean']}`", bd.esc(k['conclusion'], True), bd.esc(k['evidence'], True)])
bd.show(bd.md_table(['Cut', 'Tier', 'Lean theorem', 'Conclusion', 'Evidence'], rows))
```

The premises are displayed with each cut in {ref}`cuts`. A cut is an implication; its premise is
exactly what the components on the other side of the cut must supply.

## Native checks of the reading project

At the archive pins the reading project ran {glue:text}`n_scopes` scoped checks (each: compile a
closure of original modules, elaborate the named declarations, check their types and transitive axioms,
replay the defining modules in the kernel). Over all scopes these cover {glue:text}`n_original`
distinct named original results, {glue:text}`n_reading` reading deductions and
{glue:text}`n_statement_checks` statement comparisons for the endpoints, in {glue:text}`n_modules`
distinct original modules; {glue:text}`n_teaching` further teaching declarations use Lean 4.35.0.
The job named in the record is Helios {glue:text}`job`.

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for s in bd.scopes():
    rows.append([f"**{bd.esc(s['title'], True)}**", bd.esc(s['authority'], True), s['lean_version'],
                 f"{s['original_project_module_count']:,}", f"{s['additional_original_project_modules']:,}",
                 "<br>".join(f"`{d['name']}`" for d in s['declarations'])])
rows.append(['**Total**', '', '', '', f"**{tot['modules']:,}**", f"{len(tot['original'])} original, "
             f"{len(tot['reading_deductions'])} reading deductions, {len(tot['statement_checks'])} statement "
             f"comparisons, {len(tot['teaching'])} teaching"])
bd.show(bd.md_table(['Scope', 'Authority', 'Lean', 'Original modules', 'Newly counted', 'Declarations'], rows,
                    align='---|---|---|--:|--:|---'))
```

The supplied hypotheses and the conclusions of the scopes behind the two cuts are quoted in
{ref}`lean-bridges`. All named declarations above have transitive axioms among `propext`,
`Classical.choice` and `Quot.sound`.

## The external report

```{code-cell} ipython3
:tags: [remove-input]
links = "\n".join(f"* [{bd.esc(s['label'])}]({s['url']})" for s in st['external_sources'])
bd.show(f"{bd.esc(st['external'])}\n\n{links}")
```

The summary above is the reading project's review of the external reports (as recorded:
{glue:text}`ext_record`). Together with the reading project's own runs it is the evidence behind the
tier of the five exports.

## The complete proof: every recorded run

The record lists {glue:text}`n_stages` checks of the complete proof of the five theorems, by the
reading project and by independent builders. Each row is one run or comparison, with its operator and
outcome as recorded; a link is given where the run is documented publicly.

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for s in fp['stages']:
    link = f"[source]({s['url']})" if s.get('url', '').startswith('http') else ''
    rows.append([bd.esc(s['stage'], True), bd.esc(s['operator'], True), f"**{bd.esc(s['outcome'], True)}**",
                 bd.esc(s.get('detail', ''), True), link])
bd.show(bd.md_table(['Check', 'Operator', 'Outcome', 'Detail', ''], rows))
```

## Open questions

The reading project lists {glue:text}`n_audit` verification tasks with explicit acceptance criteria:

```{code-cell} ipython3
:tags: [remove-input]
items = []
for k, a in enumerate(m['audit'], 1):
    n = bd.node(a['node'])
    c = bd.comp(n['component'])
    items.append(f"{k}. **{bd.esc(a['title'])}.** {bd.esc(a['acceptance'])} "
                 f"Start at [`{n['declaration']}`]({n['url']}) "
                 f"(component {c['n']}, {{ref}}`{bd.esc(c['title'])} <comp-{c['id']}>`).")
bd.show("\n".join(items))
```

## What is established, and what is not

```{code-cell} ipython3
:tags: [remove-input]
by_tier = {t: [c for c in bd.comps() if c['tier'] == t] for t in bd.TIER_ORDER}
def names(t):
    return ", ".join(f"{{ref}}`{c['n']}. {bd.esc(c['title'])} <comp-{c['id']}>`" for c in by_tier[t]) or "none"
lab = lambda t: m['tiers'][t]['label']
bd.show(f"""* **Machine-checked implications.** One-sided prime windows for $\\zeta$ imply Mathlib's RH (two
  kernels); `TopG` together with `VWinAt ψ 401` for every primitive $\\psi$ implies RH and Dirichlet GRH
  (Lean at the archive pin). The analytic engine and the destination are checked as parts of these
  implications.
* **{lab('two-kernels')}:** {names('two-kernels')}. **{lab('checked')}:** {names('checked')}.
  **{lab('partial')}:** {names('partial')}. **{lab('read')}:** {names('read')}. **{lab('reported')}:**
  {names('reported')}.
* **Checked only as part of the whole:** the premises of the cuts — the existence of the geometric
  families with uniform losses (`TopG`), the cohomological bound on whole windows (`VWinAt ψ 401`), and
  the arithmetic producers behind them (the Galois row and the seven inputs). Their proofs belong to the
  complete proof, which the checkers accepted as a whole; in this record they were read at their source
  lines but not examined one by one. A kernel establishes that the five stated theorems follow from the
  axioms; it does not establish that an intermediate declaration means what its name suggests, which is
  what the open questions above are about.
* **Not claimed anywhere in this book:** that the Riemann hypothesis has been proved.""")
```
