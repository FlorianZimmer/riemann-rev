"""Local Sphinx extension of the riemann-rev Jupyter Book: prepare a build.

1. **Companions.** Copy the atlas and the PDF blueprint into ``_static/`` with
   ``scripts/sync_book_assets.py`` (absent companions are reported as pending on the pages).

2. **Execution kernel.** The notebooks are executed at every build with the ``python3`` kernel.
   Jupyter Book runs in its own (pipx) environment, whose ``python3`` kernelspec points at that
   environment's interpreter, and ``jupyter_client`` rewrites a kernel command ``python`` to the
   running interpreter. That interpreter has no numpy. So this extension writes a kernelspec named
   ``python3`` whose command is the *absolute* path of a system Python that has ``ipykernel``,
   ``numpy``, ``matplotlib`` and ``networkx``, into ``_build/jupyter/kernels/python3/``, and puts that folder
   first on ``JUPYTER_PATH`` before any notebook runs. Nothing is installed and no file outside
   ``book/_build`` is written.

   The interpreter is ``$RIEMANN_REV_PYTHON`` if set, else the first ``python3`` on ``PATH`` (then
   ``/opt/homebrew/bin/python3``, ``/usr/local/bin/python3``, ``/usr/bin/python3``) that imports these
   packages.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from sphinx.util import logging

LOG = logging.getLogger(__name__)
NEEDED = "import ipykernel, numpy, matplotlib, networkx"


def _find_python() -> str:
    candidates = [os.environ.get("RIEMANN_REV_PYTHON"), shutil.which("python3"),
                  "/opt/homebrew/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3"]
    for cand in candidates:
        if cand and os.path.isfile(cand):
            ok = subprocess.run([cand, "-c", NEEDED], capture_output=True).returncode == 0
            if ok:
                return os.path.abspath(cand)
    raise RuntimeError("bookbuild: no python3 with ipykernel, numpy, matplotlib and networkx was found; "
                       "set RIEMANN_REV_PYTHON to such an interpreter")


def _register_kernel(srcdir: Path) -> str:
    python = _find_python()
    root = srcdir / "_build" / "jupyter"
    kdir = root / "kernels" / "python3"
    kdir.mkdir(parents=True, exist_ok=True)
    spec = {"argv": [python, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Python 3 (riemann-rev book)", "language": "python",
            "env": {"PYTHONDONTWRITEBYTECODE": "1"}}
    (kdir / "kernel.json").write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8")
    rest = [p for p in os.environ.get("JUPYTER_PATH", "").split(os.pathsep) if p and p != str(root)]
    os.environ["JUPYTER_PATH"] = os.pathsep.join([str(root)] + rest)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    return python


def _sync_companions(srcdir: Path) -> None:
    script = srcdir.parent / "scripts" / "sync_book_assets.py"
    if not script.is_file():
        LOG.info("bookbuild: scripts/sync_book_assets.py not found; companions not synced")
        return
    sys.dont_write_bytecode = True  # keep scripts/ free of __pycache__
    spec = importlib.util.spec_from_file_location("sync_book_assets", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    for name, state in module.sync(verbose=False).items():
        LOG.info(f"bookbuild: companion {name}: {state}")


def setup(app):
    srcdir = Path(app.srcdir)
    _sync_companions(srcdir)
    python = _register_kernel(srcdir)
    LOG.info(f"bookbuild: notebooks execute with {python}")
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
