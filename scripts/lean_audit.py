#!/usr/bin/env python3
"""Build the repository's Lean library and record the build log and the axiom report.

    python3 -B scripts/lean_audit.py            # builds lean/, writes verification/logs/

Checks (exit 1 on failure): the build succeeds; no line of the log is a warning or an error;
no source file contains `sorry`, `admit`, an `axiom` declaration or `native_decide`; every
reported axiom is one of propext, Quot.sound, Classical.choice.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / "lean"
LOGS = ROOT / "verification" / "logs"
ALLOWED = {"propext", "Quot.sound", "Classical.choice"}
FORBIDDEN = re.compile(r"\b(sorry|admit|native_decide)\b|^\s*axiom\s", re.M)


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    bad = []
    for f in sorted(LEAN.rglob("*.lean")):
        if ".lake" in f.parts:
            continue
        text = f.read_text(encoding="utf-8")
        # ignore the words inside comments and docstrings
        code = re.sub(r"/-.*?-/", "", text, flags=re.S)
        code = re.sub(r"--[^\n]*", "", code)
        if FORBIDDEN.search(code):
            bad.append(f"forbidden token in {f.relative_to(ROOT)}")
    # force the audit module to re-elaborate so that its messages are fresh
    for p in (LEAN / ".lake" / "build" / "lib" / "lean" / "Atlas").glob("Audit.*"):
        p.unlink()
    version = subprocess.run(["lean", "--version"], cwd=LEAN, capture_output=True, text=True).stdout.strip()
    proc = subprocess.run(["lake", "build"], cwd=LEAN, capture_output=True, text=True)
    log = proc.stdout + proc.stderr
    (LOGS / "lean-build.log").write_text(f"$ lean --version\n{version}\n$ lake build\n{log}", encoding="utf-8")
    if proc.returncode != 0:
        bad.append("lake build failed")
    for line in log.splitlines():
        if re.search(r"\bwarning\b|\berror\b", line) and "does not depend" not in line:
            bad.append(f"log: {line.strip()}")
    report = {}
    for m in re.finditer(r"Audit\.lean:\d+:\d+: '([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])", log):
        name, axioms = m.group(1), m.group(3)
        report[name] = [a.strip() for a in axioms.split(",")] if axioms else []
    for name, ax in report.items():
        extra = set(ax) - ALLOWED
        if extra:
            bad.append(f"{name} uses non-standard axioms {sorted(extra)}")
    if len(report) < 18:
        bad.append(f"only {len(report)} axiom lines found in the audit log")
    out = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "lean": version,
        "build": "passed" if proc.returncode == 0 else "failed",
        "warnings": 0 if not any(b.startswith("log:") for b in bad) else "see log",
        "declarations": report,
        "axiom_free": sorted(k for k, v in report.items() if not v),
        "problems": bad,
    }
    (LOGS / "axioms.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"lean audit: build {out['build']}, {len(report)} declarations, "
          f"{len(out['axiom_free'])} axiom-free, problems: {len(bad)}")
    for b in bad:
        print("  !", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
