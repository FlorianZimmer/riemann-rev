#!/usr/bin/env python3
"""Copy the companion artifacts into the Jupyter Book's static folder before a build.

    python3 -B scripts/sync_book_assets.py

* ``atlas/index.html``              -> ``book/_static/atlas/index.html``
* ``blueprint/atlas-blueprint.pdf`` -> ``book/_static/blueprint/atlas-blueprint.pdf``

A source that does not exist is skipped and a stale copy of it is removed, so the book never
links to an outdated companion; its pages then show a clearly marked "pending" note. Both
targets are build inputs, not sources, and are git-ignored. The figures need no copying: Sphinx
copies the images referenced from ``../assets/figures/`` itself.

The book's local Sphinx extension (``book/_ext/bookbuild.py``) calls :func:`sync` at the start of
every build, so ``jupyter-book build book/`` alone is enough; running this script first is
harmless.
"""
from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "book" / "_static"
COMPANIONS = {
    "atlas": (ROOT / "atlas" / "index.html", STATIC / "atlas" / "index.html"),
    "blueprint": (ROOT / "blueprint" / "atlas-blueprint.pdf", STATIC / "blueprint" / "atlas-blueprint.pdf"),
}


def sync(verbose: bool = True) -> dict[str, str]:
    """Copy each companion that exists; remove stale copies of those that do not."""
    report: dict[str, str] = {}
    for name, (src, dst) in COMPANIONS.items():
        if src.is_file():
            if dst.is_file() and filecmp.cmp(src, dst, shallow=False):
                report[name] = "up to date"
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                report[name] = f"copied ({src.stat().st_size:,} bytes)"
        else:
            if dst.exists():
                dst.unlink()
                report[name] = "source absent; stale copy removed"
            else:
                report[name] = "source absent (pending)"
    if verbose:
        for name, state in report.items():
            print(f"sync_book_assets: {name}: {state}")
    return report


if __name__ == "__main__":
    sync()
    sys.exit(0)
