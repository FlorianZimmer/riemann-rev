#!/usr/bin/env python3
"""Are the Lean files behind each digest still what they were?

For every digest (`digests/*/concordance.json`) the script compares the files the note cites, at
the pinned commit of the archive, with the same files on the upstream default branch and at the
head of every open upstream pull request. It writes `digests/<id>/upstream.json` and prints one
line per digest. The upstream source changes daily; a note is valid for the edition it names and
for every later one in which its cited files are unchanged.

    python3 -B scripts/watch_upstream.py            # needs the GitHub CLI (`gh`), network
    python3 -B scripts/watch_upstream.py --check    # only read the stored reports
    python3 -B scripts/watch_upstream.py --read <digest> <declaration> "<verdict>"

The check fails while a cited declaration has changed on the upstream default branch and the change
has not been read. `--read` records that it was read, with a verdict in a sentence, in
`digests/<id>/upstream-read.json`. The record holds the hash of the upstream file in which the change
was read, so it stops counting as soon as that file changes again.

Requests go to the public upstream repository and contain nothing but its own paths.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER, NAME = "leanprover-community", "riemann-hypothesis"
CHUNK = 4          # references per GraphQL request


def gql(query: str) -> dict:
    r = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query], capture_output=True, text=True)
    if r.returncode:
        sys.exit("watch: GitHub request failed: " + r.stderr.strip()[:300])
    return json.loads(r.stdout)["data"]["repository"]


def repo(body: str) -> str:
    return 'query { repository(owner: "%s", name: "%s") { %s } }' % (OWNER, NAME, body)


def open_pulls() -> list[dict]:
    out, cursor = [], ""
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        d = gql(repo("pullRequests(states: OPEN, first: 50%s) { pageInfo { hasNextPage endCursor } "
                     "nodes { number title headRefOid updatedAt } }" % after))["pullRequests"]
        out += d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            return out
        cursor = d["pageInfo"]["endCursor"]


def trees(refs: list[str], dirs: list[str], entries: bool = False) -> dict[str, dict[str, object]]:
    """ref -> directory -> tree id (or name -> blob id when entries is set); None if absent."""
    out: dict[str, dict[str, object]] = {r: {} for r in refs}
    for i in range(0, len(refs), CHUNK):
        part = refs[i:i + CHUNK]
        body = []
        for a, r in enumerate(part):
            for b, d in enumerate(dirs):
                inner = "... on Tree { oid entries { name oid } }" if entries else "... on Tree { oid }"
                body.append('r%d_%d: object(expression: "%s:src/%s") { %s }' % (a, b, r, d, inner))
        data = gql(repo(" ".join(body)))
        for a, r in enumerate(part):
            for b, d in enumerate(dirs):
                node = data.get(f"r{a}_{b}")
                if not node:
                    out[r][d] = None
                elif entries:
                    out[r][d] = {e["name"]: e["oid"] for e in node["entries"]}
                else:
                    out[r][d] = node["oid"]
    return out


def texts(ref: str, paths: list[str]) -> dict[str, str | None]:
    """path -> text of the file at ref, None when the file is not there."""
    out: dict[str, str | None] = {}
    for i in range(0, len(paths), 8):
        part = paths[i:i + 8]
        body = " ".join('f%d: object(expression: "%s:src/%s") { ... on Blob { text } }' % (k, ref, f) for k, f in enumerate(part))
        data = gql(repo(body))
        for k, f in enumerate(part):
            node = data.get(f"f{k}")
            out[f] = node.get("text") if node else None
    return out


def flat(t: str) -> str:
    return " ".join(t.split())


def compare(base_text: dict[str, str | None], new_text: dict[str, str | None], decls: dict[str, dict]) -> dict[str, list[str]]:
    """Sort the cited declarations of the changed files: file absent, statement changed, proof changed.
    A declaration whose whole command occurs verbatim in the new file is unchanged, wherever it moved."""
    out: dict[str, list[str]] = {"file_absent": [], "statement_changed": [], "proof_changed": []}
    for key, d in sorted(decls.items()):
        f = d["file"]
        if f not in new_text:
            continue
        new, old = new_text[f], base_text.get(f) or ""
        a, b = d["lines"]
        command = "\n".join(old.split("\n")[a - 1:b])
        if new is None:
            out["file_absent"].append(d["name"])
        elif command and command in new:
            continue
        elif flat(d["statement"]) in flat(new):
            out["proof_changed"].append(d["name"])
        else:
            out["statement_changed"].append(d["name"])
    return out


def watch(conc: Path, pulls: list[dict], main: dict) -> dict:
    c = json.loads(conc.read_text(encoding="utf-8"))
    base = c["archive_commit"]
    cited: dict[str, set[str]] = {}
    for d in c["declarations"].values():
        folder, _, name = d["file"].rpartition("/")
        cited.setdefault(folder, set()).add(name)
    dirs = sorted(cited)
    refs = [base, main["oid"]] + [p["headRefOid"] for p in pulls]
    t = trees(refs, dirs)

    def differing(ref):
        return [d for d in dirs if t[ref][d] != t[base][d]]

    def changed_paths(ref):
        """Cited files in directories whose tree differs: the candidates for a closer look."""
        return [f"{d}/{f}" for d in differing(ref) for f in sorted(cited[d])]

    base_text: dict[str, str | None] = {}

    seen: dict[str, dict[str, str | None]] = {}

    def look(ref):
        paths = changed_paths(ref)
        if not paths:
            return {"file_absent": [], "statement_changed": [], "proof_changed": []}
        missing = [f for f in paths if f not in base_text]
        base_text.update(texts(base, missing))
        new = texts(ref, paths)
        new = {f: t for f, t in new.items() if t != base_text.get(f)}       # identical files need no comparison
        seen[ref] = new
        return compare(base_text, new, c["declarations"])

    touching = []
    for p in pulls:
        r = look(p["headRefOid"])
        if any(r.values()):
            touching.append({"number": p["number"], "title": p["title"], "head": p["headRefOid"], "updated": p["updatedAt"], **r})
    at_main = look(main["oid"])
    # the upstream text in which each change at main can be read: declaration -> hash of its file there
    file_of = {d["name"]: d["file"] for d in c["declarations"].values()}
    hashes = {n: (hashlib.sha256(t.encode("utf-8")).hexdigest() if (t := seen.get(main["oid"], {}).get(file_of[n])) else None)
              for k in ("statement_changed", "proof_changed", "file_absent") for n in at_main[k]}
    report = {
        "schema": 2, "digest": c["digest"], "upstream": f"{OWNER}/{NAME}", "base": base,
        "checked": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "cited": {"directories": len(dirs), "files": sum(len(v) for v in cited.values()), "declarations": len(c["declarations"])},
        "main": {"commit": main["oid"], "committed": main["committedDate"], **at_main, "file_sha256": hashes},
        "open_pull_requests": {"checked": len(pulls), "touching": touching},
    }
    (conc.parent / "upstream.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return report


def tally(r: dict) -> str:
    parts = [f"{len(r[k])} {label}" for k, label in (("statement_changed", "statements changed"), ("proof_changed", "proofs changed"), ("file_absent", "in files that are gone")) if r[k]]
    return ", ".join(parts) if parts else "all cited declarations unchanged"


def unread(r: dict, folder: Path) -> list[str]:
    """Declarations changed at upstream main whose change has not been read in the file as it is there now."""
    f = folder / "upstream-read.json"
    read = json.loads(f.read_text(encoding="utf-8"))["read"] if f.exists() else []
    done = {(x["declaration"], x["file_sha256"]) for x in read}
    m = r["main"]
    return [n for k in ("statement_changed", "proof_changed", "file_absent") for n in m[k]
            if (n, m.get("file_sha256", {}).get(n)) not in done]


def line(r: dict, folder: Path) -> str:
    m, p = r["main"], r["open_pull_requests"]
    left = unread(r, folder)
    n = sum(len(m[k]) for k in ("statement_changed", "proof_changed", "file_absent"))
    note = "" if not n else "; all read (upstream-read.json)" if not left else f"; NOT READ: {', '.join(left)}"
    out = [f"watch: {r['digest']}: {r['cited']['declarations']} cited declarations in {r['cited']['files']} files [{r['checked']}]",
           f"  upstream main {m['commit'][:8]} ({m['committed'][:10]}): {tally(m)}{note}",
           f"  {p['checked']} open pull requests, {len(p['touching'])} change a cited declaration"]
    out += [f"    #{x['number']} {x['title'][:70]}: {tally(x)}" for x in p["touching"]]
    return "\n".join(out)


def record(digest: str, name: str, verdict: str) -> int:
    """Note that the change of one declaration at upstream main was read, for the file as the report saw it."""
    folder = ROOT / "digests" / digest
    r = json.loads((folder / "upstream.json").read_text(encoding="utf-8"))
    m = r["main"]
    kind = next((k for k in ("statement_changed", "proof_changed", "file_absent") if name in m[k]), None)
    if kind is None or not verdict.strip():
        print(f"watch: {name} is not among the changed declarations of the stored report, or the verdict is empty")
        return 1
    f = folder / "upstream-read.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {
        "what": "changes of cited declarations on the upstream default branch that were read, with the verdict; "
                "an entry counts while the upstream file has the recorded hash", "read": []}
    data["read"] = [x for x in data["read"] if x["declaration"] != name] + [{
        "declaration": name, "change": kind.replace("_", " "), "upstream_commit": m["commit"],
        "file_sha256": m["file_sha256"][name], "verdict": verdict.strip(),
        "read": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")}]
    data["read"].sort(key=lambda x: x["declaration"])
    f.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    concs = sorted((ROOT / "digests").glob("*/concordance.json"))
    if "--read" in sys.argv:
        i = sys.argv.index("--read")
        if len(sys.argv) != i + 4:
            sys.exit(__doc__)
        return record(*sys.argv[i + 1:i + 4])
    if "--check" in sys.argv:
        bad = 0
        for c in concs:
            f = c.parent / "upstream.json"
            if not f.exists():
                print(f"watch: {c.parent.name}: no report yet (python3 -B scripts/watch_upstream.py)")
                continue
            r = json.loads(f.read_text(encoding="utf-8"))
            print(line(r, c.parent))
            bad += bool(unread(r, c.parent))
        return 1 if bad else 0
    head = gql(repo("defaultBranchRef { target { ... on Commit { oid committedDate } } }"))["defaultBranchRef"]["target"]
    pulls = open_pulls()
    for c in concs:
        print(line(watch(c, pulls, head), c.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
