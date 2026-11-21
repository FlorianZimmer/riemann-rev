# Building and checking this repository

Everything except the prose is generated. All commands are run from the repository root.

## Requirements

| for | you need |
|---|---|
| `make check` | Python 3.11 or later with NumPy and Pillow; Poppler (`pdfinfo`, `pdftoppm`) |
| `make lean` | [elan](https://github.com/leanprover/elan); the toolchain named in `lean/lean-toolchain` is fetched automatically. The library has no dependencies |
| `make figures`, `make atlas`, `make readme` | Python only |
| `make pdf`, `make guide` | TeX Live with LuaLaTeX and `latexmk`; the fonts Libertinus, Inter and JetBrains Mono |
| `make guide-gif` | Poppler and Pillow |
| `make book` | Jupyter Book 1.0 |
| `make mathlib` | a machine with about 11 GB free for Mathlib; see below |
| `make data` | the reading project, which is private; without it the imported data in `data/source/` are used as they are |

## Targets

| command | what it does | what you should see |
|---|---|---|
| `make check` | self-test of the numerics; hashes of the imported data; consistency of model, atlas, guide, logs and README | `check: 0 errors`, `readme: up to date` |
| `make model` | builds `data/model.json` from the imported data and `scripts/model.py` | `model: … components, … nodes, … edges` |
| `make figures` | computes the figures and `assets/figures/facts.json`, with assertions | `figures: … SVG files` |
| `make lean` | builds `lean/` and writes the axiom report | `lean audit: build passed, … problems: 0` |
| `make atlas` | assembles `atlas/index.html` | `atlas: atlas/index.html (… KiB)` |
| `make pdf` | compiles the illustrated blueprint | `blueprint/atlas-blueprint.pdf` |
| `make guide` | compiles the guide; fails if a symbol is missing from the notation list, on an overfull box, or on a changed page count | `guide: guide/proof-guide.pdf, … pages` |
| `make guide-gif` | the guide as an animated GIF | `guide gif: … frames` |
| `make book` | builds the Jupyter Book; notebooks are executed and contain assertions | `build succeeded` |
| `make readme` | regenerates `README.md` from the data | `readme: README.md, … lines` |
| `make site` | assembles the web site in `_site/`: home page, atlas, guide, blueprint, book | `site: _site/, … files` |
| `make all` | all of the above in order | |

## The web site

The site at https://nasqret.github.io/riemann-rev/ is built by `.github/workflows/pages.yml` on every push:
the book is built from its sources with every notebook executed (`jupyter-book build book/ --warningiserror`),
`scripts/build_site.py` puts it next to the atlas, the guide and the blueprint and writes the home page, and
GitHub Pages publishes the result. Locally, `make site` gives the same pages in `_site/`.

## The check against Mathlib

`lean-mathlib/AtlasZeta.lean` re-proves the last step of the argument against Mathlib at the commit the
archive uses. Mathlib is large, so the file is compiled on a SLURM cluster by `scripts/helios_mathlib.sh`,
which is configured through four environment variables described at its head. The result is recorded in
`verification/logs/mathlib-zeta-axioms.json` together with the SHA-256 of the files that were compiled;
`make check` fails if one of them is changed afterwards. On any machine with Mathlib available the same
check is `cd lean-mathlib && lake exe cache get && lake build`.

## Refreshing the evidence

The status shown everywhere comes from `data/source/status.json`, imported from the reading project by
`scripts/import_sources.py`. Each import records the hashes of the files (`data/source/PROVENANCE.json`)
and adds a line to `data/sync-log.json`. After an import, `make all && make check` rebuilds every page.
Nothing in `data/source/` is edited by hand.

## Rules the build enforces

- Numbers shown on a page must occur in the evidence; the check compares them.
- Every link to a Lean declaration is pinned to one commit of the public mirror of the archive.
- Lean code is quoted from files, never retyped.
- The guide must define every symbol it uses.
