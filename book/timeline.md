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

# The announcement's twenty entries

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
from collections import Counter
from datetime import date
import bookdata as bd

m = bd.model()
tl = sorted(m['timeline'], key=lambda t: t['number'])
D = bd.dates()
assert [t['number'] for t in tl] == list(range(1, 21)) == sorted(D)
assert bd._load('data/announcement_dates.json')['pdf_sha256'] == m['pins']['pdf_sha256']
first = min(date.fromisoformat(D[n]['date']) for n in D)
last = max(date.fromisoformat(D[n]['date']) for n in D)
pages = sorted({t['page'] for t in tl})
bd.glue('first', f"{first.day} {first:%B}")
bd.glue('last', f"{last.day} {last:%B %Y}")
bd.glue('pages', ' and '.join(str(p) for p in pages))
bd.glue('n_mapped', sum(1 for t in tl if t['component']))
bd.glue('n_unmapped', sum(1 for t in tl if not t['component']))
# the observations at the end of the page
assert {t['number'] for t in tl if 'matched' in t['relation']} == {5, 13, 20}
assert [t['topic'] for t in tl if 'matched' in t['relation']] == [
    'The smoothed von Mangoldt sum', 'The slope inequality', 'Dirichlet GRH']
assert tl[13]['number'] == 14 and tl[13]['topic'] == 'The provisional exponent two-thirds'
```

On pages {glue:text}`pages` of the announcement the author lists, in twenty dated entries, the
order in which the ideas occurred — from {glue:text}`first` to {glue:text}`last`. The entries mix
formulas, theorem claims, auxiliary problems and approaches later superseded. The reading project
compared each with the archive; the column *relation* records how far that comparison goes, and the
component model assigns {glue:text}`n_mapped` entries to components ({glue:text}`n_unmapped` are
historical remarks without a component). The dates are those written in the announcement (a "+"
there, rendered "onward" here, marks an idea pursued from that date on).

```{code-cell} ipython3
:tags: [remove-input]
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
bd.plot_style()
P = bd.PALETTE
fig, ax = plt.subplots(figsize=(9, 4.9))
seen = set()
for t in tl:
    dd = date.fromisoformat(D[t['number']]['date'])
    if t['component']:
        c = bd.comp(t['component'])
        col = bd.stratum(c['stratum'])['color']
        lab = bd.stratum(c['stratum'])['title']
    else:
        col, lab = P['motiv'], 'no component (historical remark)'
    ax.plot([dd], [t['number']], 'o', ms=9, color=col, mec='white', mew=1.2,
            label=None if lab in seen else lab, zorder=3)
    if D[t['number']].get('from_on'):
        ax.annotate('', xy=(mdates.date2num(dd) + 4, t['number']), xytext=(mdates.date2num(dd) + 0.6, t['number']),
                    arrowprops=dict(arrowstyle='->', color=col, lw=1.2))
    seen.add(lab)
    ax.text(mdates.date2num(dd) + (5 if D[t['number']].get('from_on') else 1.2), t['number'],
            t['topic'], va='center', fontsize=7.6, color=P['text'])
ax.set_ylim(20.8, 0.2)
ax.set_yticks(range(1, 21))
ax.set_ylabel('entry')
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
ax.set_xlim(mdates.date2num(first) - 2, mdates.date2num(last) + 24)
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.09), ncol=3, fontsize=8)
ax.set_title('When each entry was written, coloured by the stratum of its component', loc='left')
plt.tight_layout()
plt.show()
```

## The entries

```{code-cell} ipython3
:tags: [remove-input]
rows = []
for t in tl:
    d = D[t['number']]
    comp = (f"{bd.comp(t['component'])['n']}. {{ref}}`{bd.esc(bd.comp(t['component'])['title'], True)} "
            f"<comp-{t['component']}>`") if t['component'] else '—'
    rows.append([str(t['number']), f"{bd.entry_date(t['number'])}<br><small>“{d['as_written']}”, p. {t['page']}</small>",
                 f"**{bd.esc(t['topic'], True)}**<br><small>{bd.esc(t['relation'], True)}</small>", comp,
                 bd.esc(t['assessment'], True)])
bd.show(bd.md_table(['#', 'Written', 'Topic · relation to the archive', 'Component', 'Assessment'], rows,
                    align='--:|---|---|---|---'))
```

## Summary

```{code-cell} ipython3
:tags: [remove-input]
rel = Counter(t['relation'] for t in tl)
by_comp = Counter(t['component'] for t in tl if t['component'])
rows1 = [[bd.esc(r, True), str(n)] for r, n in rel.most_common()]
rows2 = [[f"{bd.comp(c)['n']}. {{ref}}`{bd.esc(bd.comp(c)['title'], True)} <comp-{c}>`",
          ", ".join(str(n) for n in bd.comp(c)['timeline'])]
         for c, _ in sorted(by_comp.items(), key=lambda kv: bd.comp(kv[0])['n'])]
assert sum(rel.values()) == len(tl)
bd.show(bd.md_table(['Relation', 'Entries'], rows1, align='---|--:') + "\n\n"
        + bd.md_table(['Component', 'Entries'], rows2))
```

Two observations matter for the architecture. First, the entries that can be matched to a formula or
statement of the archive (the smoothed von Mangoldt sum, the slope inequality, Dirichlet GRH) are few;
most are *supporting* or *quantitative* comparisons, where the archive contains a related but more
specific statement. Second, the provisional exponent two-thirds of entry 14 is an intermediate
strategy: the archive's estimate has exponent $\tfrac12+(e_D+e_L+7)\varepsilon$, and how the earlier
barrier was overcome is not derived in the comparison.
