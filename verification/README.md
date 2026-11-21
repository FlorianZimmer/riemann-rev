# Verification records of this repository

These files record what **this repository** checked. The verification of the original archive
(native receipts, kernel replays, the external report) belongs to the reading project and is
summarized, with its as-of time, in `data/source/status.json` and `data/source/native-scopes.json`.

| file | produced by | what it shows |
|---|---|---|
| `logs/lean-build.log` | `scripts/lean_audit.py` (`make lean`) | build of `lean/` with Lean 4.35.0, no imports, and the `#print axioms` output of `Atlas/Audit.lean` |
| `logs/axioms.json` | same | the axioms of the 18 audited declarations (10 use none; the rest only `propext`, `Quot.sound`, `Classical.choice`), and the list of problems (must be empty) |
| `logs/mathlib-zeta-build.log` | `scripts/helios_mathlib.sh` (`make mathlib`) | build of `lean-mathlib/` on Helios at the archive's pins (Lean 4.33.1, Mathlib `0df444a3`) |
| `logs/mathlib-zeta-axioms.json` | same | axioms of the Mathlib instantiation of the destination layer |
| `../assets/figures/facts.json` | `scripts/build_figures.py` | every number shown by the figures, each asserted before the figure is written |

`python3 -B scripts/check_project.py` (part of `make check`) re-reads these records and fails on
problems, non-standard axioms, unpinned links, or a number in the atlas that does not occur in the
evidence.
