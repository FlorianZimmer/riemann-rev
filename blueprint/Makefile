# The illustrated LaTeX blueprint:   make -C blueprint
#
# Needs TeX Live (latexmk, LuaLaTeX; the fonts Libertinus, Inter and JetBrains Mono ship with it) and
# rsvg-convert. Intermediates go to build/ (git-ignored); the result is atlas-blueprint.pdf.
# The PDF date is the time of the status record (SOURCE_DATE_EPOCH), so rebuilding is reproducible.

ROOT    := ..
PY      := python3 -B
GEN     := $(ROOT)/scripts/build_blueprint_tex.py
FIGS    := $(shell $(PY) $(GEN) --figures)
EPOCH   := $(shell $(PY) $(GEN) --epoch)
FIGPDF  := $(FIGS:%=build/fig/%.pdf)
LATEXMK := latexmk -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build

.PHONY: all generated pdf clean

all: pdf

generated:
	$(PY) $(GEN)

build/fig/%.pdf: $(ROOT)/assets/figures/%.svg
	@mkdir -p build/fig
	SOURCE_DATE_EPOCH=$(EPOCH) rsvg-convert -f pdf -o $@ $<

pdf: generated $(FIGPDF)
	TZ=UTC SOURCE_DATE_EPOCH=$(EPOCH) FORCE_SOURCE_DATE=1 $(LATEXMK) atlas-blueprint.tex
	cp build/atlas-blueprint.pdf atlas-blueprint.pdf

clean:
	rm -rf build
