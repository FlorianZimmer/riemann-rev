#!/usr/bin/env python3
"""Import the already-produced reading data from the reading project, with provenance.

The reading project is a separate, still-active and private working copy in which the
announcement and the Lean archive are read and the verification runs are recorded. This script
copies only the small, derived data files that the atlas renders, verifies that they parse, and
writes ``data/source/PROVENANCE.json`` with the SHA-256 of every file (as it was in the reading
project and as it is stored here), the reading project's commit and the time of the import. Every
import is also appended to ``data/sync-log.json``.

It never copies the 14 archive parts or the proof exports; those are referenced by hash.

    python3 scripts/import_sources.py [--source DIR] [--check]

The location of the reading project comes from ``--source``, from the environment variable
``READING_PROJECT`` or from ``private/config.json`` (which is not part of the public tree). The
same private file may list redactions: regular expressions that are replaced on import, so that
references into private places are not copied. The number of replacements is recorded per file.

``--check`` recomputes the hashes of the stored files and compares them with PROVENANCE.json
without touching the reading project; it works in the public tree too.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "source"
SYNC_LOG = ROOT / "data" / "sync-log.json"
PRIVATE = ROOT / "private" / "config.json"


def private_config() -> dict:
    return json.loads(PRIVATE.read_text(encoding="utf-8")) if PRIVATE.exists() else {}

# (path in source project, destination name, kind)
FILES = [
    ("blueprint/map.json", "map.json", "json"),
    ("evidence/status.json", "status.json", "json"),
    ("evidence/sources.json", "sources.json", "json"),
    ("research/agents/arithmetic/timeline.json", "timeline.json", "json"),
    ("dashboard/data/native-scopes.json", "native-scopes.json", "json"),
    ("evidence/helios/progress.json", "helios-progress.json", "json"),
]

# Lean sources that are re-used verbatim (teaching files compile here; the archive
# bridges compile only against the original archive and are kept as references).
LEAN = [
    ("formal/standalone/WindowLogic.lean", ROOT / "lean" / "Reading" / "WindowLogic.lean"),
    ("formal/behrend/BehrendSphere.lean", ROOT / "lean" / "Reading" / "BehrendSphere.lean"),
    ("formal/window-bridge/WindowBridge.lean", ROOT / "references" / "archive-bridges" / "WindowBridge.lean"),
    ("formal/window-bridge/GeometricTransport.lean", ROOT / "references" / "archive-bridges" / "GeometricTransport.lean"),
    ("formal/dirichlet-bridge/DirichletBridge.lean", ROOT / "references" / "archive-bridges" / "DirichletBridge.lean"),
    ("formal/upstream/EndpointAudit.lean", ROOT / "references" / "archive-bridges" / "EndpointAudit.lean"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(src: Path, git_dirs: list[str]) -> str | None:
    for g in git_dirs or [".git"]:
        try:
            out = subprocess.run(["git", f"--git-dir={src / g}", "rev-parse", "HEAD"],
                                 capture_output=True, text=True, timeout=20)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    return None


def copy_redacted(s: Path, d: Path, redactions: list[dict]) -> int:
    """Copy s to d, applying the redactions; return the number of replacements."""
    text = s.read_text(encoding="utf-8")
    count = 0
    for r in redactions:
        text, n = re.subn(r["pattern"], r["replace"], text)
        count += n
    d.parent.mkdir(parents=True, exist_ok=True)
    d.write_text(text, encoding="utf-8")
    return count


def do_import(src: Path, cfg: dict) -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    redactions = cfg.get("redactions", [])
    record = {
        "source_project": "the reading project (private working copy)",
        "source_commit": git_head(src, cfg.get("git_dirs", [])),
        "imported_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "redaction_rules": [r.get("why", "redaction") for r in redactions],
        "files": [],
    }
    for rel, d, kind in [(rel, DEST / name, kind) for rel, name, kind in FILES] + [(rel, d, "lean") for rel, d in LEAN]:
        s = src / rel
        if not s.exists():
            raise SystemExit(f"missing source file: {rel}")
        n = copy_redacted(s, d, redactions)
        if kind == "json":
            json.loads(d.read_text(encoding="utf-8"))  # must parse
        record["files"].append({"from": rel, "to": str(d.relative_to(ROOT)), "sha256": sha256(d),
                                "sha256_in_reading_project": sha256(s), "redactions": n, "bytes": d.stat().st_size})
    (DEST / "PROVENANCE.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    # one line per import in the public log of syncs
    status = json.loads((DEST / "status.json").read_text(encoding="utf-8"))
    log = json.loads(SYNC_LOG.read_text(encoding="utf-8")) if SYNC_LOG.exists() else []
    entry = {"imported_utc": record["imported_utc"], "source_commit": record["source_commit"],
             "status_as_of": status.get("as_of"), "headline": status.get("headline")}
    if not log or (log[-1]["status_as_of"], log[-1]["source_commit"]) != (entry["status_as_of"], entry["source_commit"]):
        log.append(entry)
    else:
        log[-1] = entry
    SYNC_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def do_check() -> int:
    prov = json.loads((DEST / "PROVENANCE.json").read_text(encoding="utf-8"))
    bad = 0
    for f in prov["files"]:
        p = ROOT / f["to"]
        if not p.exists():
            print(f"MISSING {f['to']}")
            bad += 1
        elif sha256(p) != f["sha256"]:
            print(f"CHANGED {f['to']}")
            bad += 1
    print(f"provenance: {len(prov['files']) - bad}/{len(prov['files'])} files match "
          f"(imported {prov['imported_utc']}, source commit {prov['source_commit']})")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=None, help="the reading project (default: $READING_PROJECT or private/config.json)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return do_check()
    cfg = private_config()
    source = a.source or os.environ.get("READING_PROJECT") or cfg.get("reading_project")
    if not source:
        print("import: the reading project is not available here (set READING_PROJECT or use --source); "
              "the imported data in data/source/ are complete and can be checked with --check")
        return 1
    rec = do_import(Path(source).expanduser(), cfg)
    print(f"imported {len(rec['files'])} files from {rec['source_project']} (commit {rec['source_commit']}); "
          f"{sum(f['redactions'] for f in rec['files'])} redactions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
