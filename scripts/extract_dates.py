#!/usr/bin/env python3
"""Extract the dates of the twenty timeline entries from the announcement PDF.

    python3 -B scripts/extract_dates.py   # needs source/remark.pdf (git-ignored) and pdftotext

Writes data/announcement_dates.json with the PDF's SHA-256, so the committed dates can be
re-derived from the exact bytes. Dates are written in the announcement as M/D/YY, some with a
trailing '+' (meaning "from that day on").
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pdf = ROOT / "source" / "remark.pdf"
text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
items = {}
for line in text.splitlines():
    m = re.match(r"^\s*(\d{1,2})\.\s+(\d{1,2})/(\d{1,2})/(\d{2})(\+?)\s*:", line)
    if m:
        n, mo, d, y, plus = int(m[1]), int(m[2]), int(m[3]), int(m[4]), m[5]
        items[n] = {"number": n, "date": f"20{y:02d}-{mo:02d}-{d:02d}", "from_on": bool(plus),
                    "as_written": f"{mo}/{d}/{y}{plus}"}
assert sorted(items) == list(range(1, 21)), sorted(items)
out = {"pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "items": [items[k] for k in sorted(items)]}
(ROOT / "data" / "announcement_dates.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(f"dates: {len(items)} entries from {out['pdf_sha256'][:12]}…")
