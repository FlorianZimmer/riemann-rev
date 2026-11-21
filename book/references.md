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

# Sources, pins and references

```{code-cell} ipython3
:tags: [remove-cell]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '_lib')
import bookdata as bd

m = bd.model()
pins = m['pins']
src = bd.archive_sources()
prov = bd.provenance()
assert src['archive_sha256'] == pins['archive_sha256'] and src['pdf_sha256'] == pins['pdf_sha256']
source_md = (bd.ROOT / 'source' / 'SOURCE.md').read_text(encoding='utf-8')
for key in ('archive_sha256', 'pdf_sha256', 'mirror_commit', 'mathlib'):
    assert pins[key] in source_md, key            # model pins and source/SOURCE.md agree
```

## The announcement and the archive

```{code-cell} ipython3
:tags: [remove-input]
rows = [
    ["Announcement (PDF)", "Levent Alpöge, announcement of proofs of RH and of GRH for Dirichlet characters, "
     "20 November 2026; public at <https://alpo.ge/remark.pdf>"],
    ["PDF SHA-256", f"`{pins['pdf_sha256']}`"],
    ["Lean archive", f"`lean.tar.gz.part01` … `part{len(src['parts']):02d}` (one gzip stream), "
     f"<https://alpo.ge/>"],
    ["Archive SHA-256", f"`{pins['archive_sha256']}`"],
    ["Members", f"{src['members']:,} archive members, {src['lean_files']:,} Lean files, "
     f"{src['unpacked_bytes']:,} bytes unpacked"],
    ["Toolchain", f"`{pins['toolchain']}`"],
    ["Mathlib", f"`{pins['mathlib']}`"],
    ["Public mirror", f"<{pins['mirror']}> at commit `{pins['mirror_commit']}`; every source link in this "
     "book points to this commit"],
]
bd.show(bd.md_table(["", ""], rows, align="---|---"))
```

```{code-cell} ipython3
:tags: [remove-input]
rows = [[f"`{k}`", f"`{v}`"] for k, v in src['parts'].items()]
groups = ", ".join(f"`{g}` {n:,}" for g, n in sorted(src['groups'].items(), key=lambda kv: -kv[1]))
bd.show(":::{dropdown} SHA-256 of the archive parts and the top-level groups of the tree\n\n"
        + bd.md_table(["Part", "SHA-256"], rows) + f"\n\nTop-level groups (number of members): {groups}.\n:::")
```

## Imported data

The book is built from data imported from the reading project with SHA-256 checksums
(`data/source/PROVENANCE.json`):

```{code-cell} ipython3
:tags: [remove-input]
bd.show(f"Source project `{prov['source_project']}`, commit `{prov['source_commit']}`, imported "
        f"{bd.as_of(prov['imported_utc'])}.\n\n"
        + bd.md_table(["Imported from", "Stored as", "Bytes", "SHA-256"],
                      [[f"`{f['from']}`", f"`{f['to']}`", f"{f['bytes']:,}", f"`{f['sha256'][:20]}…`"]
                       for f in prov['files']]))
```

The figures and their numbers come from `scripts/build_figures.py` (numerics in `scripts/rhlib.py`,
which has a self-test: `python3 -B scripts/rhlib.py`); the component model from `scripts/model.py`;
the Lean audit from `scripts/lean_audit.py`.

## External reports

```{code-cell} ipython3
:tags: [remove-input]
bd.show("\n".join(f"* [{bd.esc(s['label'])}]({s['url']})" for s in m['status']['external_sources'])
        + f"\n\nAs summarized in the reading project's status record of {bd.as_of()}; see {{doc}}`verification`.")
```

## Classical background

Bibliographic details are given only where the reading project supplies them (with its links).

* Landau's theorem on Dirichlet series with nonnegative coefficients (a real singularity at the
  abscissa of convergence) — the window criterion is a localized, one-sided version of his oscillation
  argument.
* L. Schoenfeld, *Sharper bounds for the Chebyshev functions θ(x) and ψ(x). II*, Math. Comp.,
  [doi:10.1090/S0025-5718-1976-0457374-X](https://doi.org/10.1090/S0025-5718-1976-0457374-X), Theorem 10
  — the bound used in {ref}`window-strength`.
* F. A. Behrend, Proc. Nat. Acad. Sci. U.S.A. (1946),
  [PDF at PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/instance/1078964/pdf/pnas01693-0039.pdf)
  — the digit-sphere construction ({doc}`behrend`).
* B. Ferrero and L. C. Washington, *Annals of Mathematics* (1979),
  [doi:10.2307/1971116](https://doi.org/10.2307/1971116) — vanishing of the Iwasawa $\mu$-invariant for
  abelian fields, invoked in the archive's formulation behind the cohomological window.
* Bost's slope inequality for Euclidean lattices (Séminaire Bourbaki), in the form proved in the
  archive as `Formalism.F.slopeInequality_of` ({ref}`comp-family`).
* NIST Digital Library of Mathematical Functions: [the von Mangoldt series](https://dlmf.nist.gov/27.4.E12),
  [Laurent expansion of ζ at 1](https://dlmf.nist.gov/25.2.E4),
  [Dirichlet $L$-functions and the change of level](https://dlmf.nist.gov/25.15.E4).

```{code-cell} ipython3
:tags: [remove-input]
mathlib = next(l for l in bd.comp('endpoints')['lean'] if l['name'] == 'Mathlib RiemannHypothesis')
assert pins['mathlib'] in mathlib['url']
bd.show(f"* Mathlib's definition of `RiemannHypothesis` at the archive's Mathlib pin: [{mathlib['url'].split('/')[-1]}]({mathlib['url']}).")
```

## This book

Built with Jupyter Book from the MyST notebooks in `book/`; every page is executed at build time
(`jupyter-book build book/`). Companions: the guide to the proof (`guide/proof-guide.pdf`), the interactive atlas
(`atlas/index.html`), the illustrated PDF blueprint (`blueprint/`) and the Lean library (`lean/`).
