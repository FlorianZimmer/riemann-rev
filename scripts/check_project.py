#!/usr/bin/env python3
"""Project-wide consistency checks (run by `make check`).

Fails (exit 1) on: a model that does not cover the blueprint nodes exactly once; a Lean link
that is not pinned to the archive mirror commit or the archive's Mathlib commit; a figure named by
the model that does not exist; an axiom audit with problems or non-standard axioms; an atlas whose
embedded data disagree with data/model.json; numbers in the atlas that are not in the evidence.
Warns (exit 0) about deliverables that have not been built yet.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR = "https://github.com/Deicyde/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/"
MATHLIB = "https://github.com/leanprover-community/mathlib4/blob/0df444a360eaa60ab8c11dca51a86af692955474/"
errors: list[str] = []
warnings: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def main() -> int:
    model = json.loads((ROOT / "data/model.json").read_text(encoding="utf-8"))
    ids = [n["id"] for n in model["nodes"]]
    owned = [i for c in model["components"] for i in c["nodes"]]
    src_ids = [n["id"] for n in json.loads((ROOT / "data/source/map.json").read_text(encoding="utf-8"))["nodes"]]
    check(sorted(ids) == sorted(src_ids) and sorted(ids) == sorted(owned) and len(set(owned)) == len(owned),
          "components do not own the blueprint nodes exactly once")
    for c in model["components"]:
        for l in c["lean"]:
            check(l["url"].startswith(MIRROR) or l["url"].startswith(MATHLIB), f"unpinned link {l['url']}")
        if c.get("figure"):
            check((ROOT / "assets/figures" / f"{c['figure']}.svg").exists(), f"missing figure {c['figure']}")
    for n in model["nodes"]:
        if n.get("url"):
            check(n["url"].startswith(MIRROR) or "alpo.ge" in n["url"], f"unpinned node link {n['url']}")
    facts = json.loads((ROOT / "assets/figures/facts.json").read_text(encoding="utf-8"))
    for key in ("hero", "explicit", "ramp", "spotlight", "balance", "windows", "behrend", "zeros"):
        check(key in facts, f"facts.json lacks {key}")
    audit = json.loads((ROOT / "verification/logs/axioms.json").read_text(encoding="utf-8"))
    check(audit["build"] == "passed" and not audit["problems"], "Lean audit has problems")
    allowed = {"propext", "Quot.sound", "Classical.choice"}
    for k, v in audit["declarations"].items():
        check(set(v) <= allowed, f"{k} uses {v}")
    atlas = ROOT / "atlas/index.html"
    if atlas.exists():
        h = atlas.read_text(encoding="utf-8")
        m = re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>', h, re.S)
        check(bool(m), "atlas has no embedded data")
        if m:
            data = json.loads(m.group(1).replace("<\\/", "</"))
            check(len(data["components"]) == len(model["components"]), "atlas components differ from the model")
            check([c["gist"] for c in data["components"]] == [c["gist"] for c in model["components"]],
                  "atlas is older than data/model.json (run make atlas)")
            check(len(data["nodes"]) == len(ids), "atlas does not carry every blueprint node")
        # every number with a thousands separator shown in the atlas must occur in the evidence
        evidence = (json.dumps(model) + json.dumps(facts) + (ROOT / "data/source/native-scopes.json").read_text()
                    + (ROOT / "data/source/status.json").read_text())
        text = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", h, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        for num in sorted(set(re.findall(r"(?<![\d.,])\d{1,3}(?:,\d{3})+(?![\d,])", text))):
            check(num in evidence or num.replace(",", "") in evidence, f"atlas shows {num}, not found in evidence")
    else:
        warnings.append("atlas/index.html not built")
    mz = ROOT / "verification/logs/mathlib-zeta-axioms.json"
    if mz.exists():
        z = json.loads(mz.read_text(encoding="utf-8"))
        check(z.get("build") == "passed" and not z.get("problems"), "the Mathlib instantiation is not recorded as passed")
        check(all(set(v) <= {"propext", "Classical.choice", "Quot.sound"} for v in z["declarations"].values()),
              "the Mathlib instantiation uses non-standard axioms")
        check("Atlas.Zeta.riemannHypothesis_of_right" in z["declarations"], "riemannHypothesis_of_right is missing from the record")
        check(z.get("mathlib_rev") == MATHLIB.rstrip("/").split("/")[-1], "the Mathlib instantiation was not built at the archive's Mathlib pin")
        for rel, digest in z.get("sources", {}).items():
            check(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest,
                  f"{rel} changed after the Mathlib check: re-run `make mathlib`")
        check(len(z.get("sources", {})) == 3, "the Mathlib record does not name the compiled sources")
        log = ROOT / "verification/logs/mathlib-zeta-build.log"
        check(log.exists() and hashlib.sha256(log.read_bytes()).hexdigest() == z.get("build_log_sha256"),
              "the Mathlib build log does not match its record")
    else:
        warnings.append("Mathlib instantiation not built (verification/logs/mathlib-zeta-axioms.json)")
    guide = ROOT / "guide/proof-guide.pdf"
    if guide.exists():
        info = subprocess.run(["pdfinfo", "-url", str(guide)], capture_output=True, text=True).stdout
        pages = subprocess.run(["pdfinfo", str(guide)], capture_output=True, text=True).stdout
        from build_guide import GUIDE_PAGES
        check(re.search(rf"Pages:\s+{GUIDE_PAGES}\b", pages) is not None, f"the guide does not have {GUIDE_PAGES} pages")
        urls = {l.split()[-1] for l in info.splitlines()[1:] if l.strip()}
        check(len(urls) >= 25 and all(u.startswith(MIRROR) for u in urls), "the guide has unpinned links")
        gif = ROOT / "guide/proof-guide.gif"
        if gif.exists():
            from PIL import Image
            with Image.open(gif) as g:
                frames, note = getattr(g, "n_frames", 1), g.info.get("comment", b"")
            note = note.decode("ascii", "replace") if isinstance(note, bytes) else str(note)
            check(frames == GUIDE_PAGES, f"the GIF of the guide has {frames} frames for {GUIDE_PAGES} pages")
            check(note.endswith("sha256=" + hashlib.sha256(guide.read_bytes()).hexdigest()),
                  "the GIF of the guide was made from another version of the PDF: re-run `make guide-gif`")
        else:
            warnings.append("GIF of the guide not built (guide/proof-guide.gif)")
    else:
        warnings.append("guide not built (guide/proof-guide.pdf)")
    digest = ROOT / "digests/tower-bound/tower-bound.pdf"
    if digest.exists():
        info = subprocess.run(["pdfinfo", "-url", str(digest)], capture_output=True, text=True).stdout
        urls = re.findall(r"https?://\S+", info)
        mirror_tree = MIRROR.replace("/blob/", "/tree/")
        ok = ("https://nasqret.github.io/riemann-proof-atlas/",)
        check(len(urls) >= 60 and all(u.startswith((MIRROR, mirror_tree) + ok) for u in urls),
              "the digest has unpinned links")
    else:
        warnings.append("digest not built (digests/tower-bound/tower-bound.pdf)")
    expected = [("blueprint/atlas-blueprint.pdf", "blueprint PDF"), ("book/_build/html/index.html", "Jupyter Book")]
    if (ROOT / "scripts/build_vault.py").exists():      # the knowledge base belongs to the working copy only
        expected.append(("vault/Home.md", "Obsidian vault"))
    for path, what in expected:
        if not (ROOT / path).exists():
            warnings.append(f"{what} not built ({path})")
    if (ROOT / "vault/check_vault.py").exists() and (ROOT / "vault/Home.md").exists():
        r = subprocess.run([sys.executable, "-B", str(ROOT / "vault/check_vault.py"), str(ROOT / "vault")],
                           capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip().splitlines()
        if r.returncode != 0:
            errors.append("vault link check failed: " + (out[-1] if out else ""))
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"check: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
