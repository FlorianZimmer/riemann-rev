# Build everything from the sources of truth.  `make all` then `make check`.
#   data     re-import the reading project's data (needs the private reading project) and rebuild the model
#   figures  compute the figures and assert every number they show
#   lean     build the self-contained Lean library (Lean 4.35.0) and record the axiom audit
#   atlas    assemble atlas/index.html
#   pdf      compile the illustrated LaTeX blueprint
#   guide    compile the guide to the proof (guide/proof-guide.pdf: every symbol defined, notation page)
#   guide-gif  the same guide as an animated GIF, one frame per page (guide/proof-guide.gif)
#   digest   compile the deformalization digests (digests/tower-bound/tower-bound.pdf: one cluster of the
#            archive as mathematics; Lean concordance and examples are generated and checked)
#   readme   regenerate README.md, the public dashboard, from the data
#   site     assemble the web site in _site/ (home page, atlas, guide, blueprint, book)
#   book     build the Jupyter Book (executes the notebooks)
#   vault    regenerate the Obsidian vault and check its links
#   mathlib  the Mathlib instantiation of the destination layer (runs on a cluster, see BUILDING.md)
PY := python3 -B

.PHONY: all data model figures lean atlas pdf guide guide-gif digest census watch book vault readme site check selftest mathlib clean

all: model figures lean atlas pdf guide guide-gif digest book vault readme

data:
	$(PY) scripts/import_sources.py
	$(PY) scripts/extract_dates.py
	$(MAKE) model

model:
	$(PY) scripts/model.py

figures:
	$(PY) scripts/rhlib.py
	$(PY) scripts/build_figures.py

lean:
	$(PY) scripts/lean_audit.py

atlas: model
	$(PY) scripts/build_atlas.py

pdf: model
	$(PY) scripts/build_blueprint_tex.py
	$(MAKE) -C blueprint

guide: model figures
	$(PY) scripts/build_guide.py

guide-gif: guide
	$(PY) scripts/build_guide_gif.py

digest: model
	$(PY) scripts/build_digest.py

# reads the whole archive once (about two minutes); not part of `all`
census: model
	$(PY) scripts/archive_census.py

# compares the Lean files behind every digest with upstream main and the open upstream pull requests (network, gh)
watch:
	$(PY) scripts/watch_upstream.py

readme: model
	$(PY) scripts/build_readme.py

site: atlas guide book
	$(PY) scripts/build_site.py --require-book

book: atlas
	$(PY) scripts/sync_book_assets.py
	jupyter-book build book/ --warningiserror --keep-going

vault: atlas
	@if [ -f scripts/build_vault.py ]; then $(PY) scripts/build_vault.py && $(PY) vault/check_vault.py vault; \
	 else echo "vault: the knowledge base is part of the private working copy"; fi

mathlib:
	bash scripts/helios_mathlib.sh

selftest:
	$(PY) scripts/rhlib.py

check: selftest
	$(PY) scripts/import_sources.py --check
	$(PY) scripts/check_project.py
	$(PY) scripts/build_readme.py --check
	$(PY) scripts/build_digest.py --check
	$(PY) scripts/archive_census.py --check
	$(PY) scripts/watch_upstream.py --check

clean:
	rm -rf book/_build blueprint/build guide/build digests/*/build lean/.lake
