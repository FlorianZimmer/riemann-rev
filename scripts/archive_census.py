#!/usr/bin/env python3
"""Census of the Lean archive: how large it is, how it is cut into directories, and how much of
it lies under the blueprint and under each digest.

It reads every file of the archive once (about two minutes), builds the import graph of its
modules and writes `data/census.json`.  The numbers answer one question: how many notes of the
kind of `digests/tower-bound` a deformalization of the archive needs, at each resolution.

    python3 -B scripts/archive_census.py            # read the archive, write data/census.json
    python3 -B scripts/archive_census.py --check    # only check the stored file (no archive needed)

The archive is found through the environment variable ARCHIVE_SRC or the entry `archive_src` of
private/config.json.  With the data of the embedding atlas (ATLAS_DATA or `atlas_data` there) it also
measures the part of the archive that the five endpoints reach.  Nothing here is typed by hand: every figure quoted from the census in the
journal, the plan or a page comes from the stored file.
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "census.json"
MAIN = "Main"                       # the module that states the five endpoints
CUTS = (1, 5, 10, 20, 50, 100, 200, 500, 1000)

IMPORT = re.compile(r"^\s*(?:public\s+|private\s+|meta\s+)*import\s+(?:all\s+)?(\S+)")
MODIFIERS = r"(?:@\[[^\]]*\]\s*)*(?:private |protected |noncomputable |nonrec |unsafe |partial |local |scoped )*"
COMMAND = re.compile(r"^" + MODIFIERS + r"(theorem|lemma|def|abbrev|structure|class|instance|inductive|axiom|opaque|example|alias"
                     r"|notation|macro_rules|macro|syntax|elab|infixl|infixr|infix|prefix|postfix)\b")
OTHER = re.compile(r"^(?:@\[|/--|/-!|namespace\b|section\b|end\b|open\b|variable\b|universe\b|set_option\b|attribute\b|export\b"
                   r"|mutual\b|omit\b|include\b|#|initialize\b|deriving\b|unseal\b|suppress_compilation\b)")
BUCKETS = ((3, "1-3"), (10, "4-10"), (30, "11-30"), (100, "31-100"), (10 ** 9, "101+"))


def archive_src() -> Path | None:
    return located("ARCHIVE_SRC", "archive_src")


def atlas_data() -> Path | None:
    """The data of the embedding atlas (index.json, records/), for the endpoint masks."""
    return located("ATLAS_DATA", "atlas_data")


def located(variable: str, key: str) -> Path | None:
    loc = os.environ.get(variable)
    cfg = ROOT / "private" / "config.json"
    if not loc and cfg.exists():
        loc = json.loads(cfg.read_text(encoding="utf-8")).get(key)
    if loc and Path(loc).expanduser().is_dir():
        return Path(loc).expanduser()
    return None


def bucket(n: int) -> str:
    return next(name for top, name in BUCKETS if n <= top)


def read_archive(src: Path):
    """Module -> imports, lines, theorem commands as (line, length).  Imports precede everything else
    in a Lean file, so the scan for them stops at the first line that is neither an import nor a
    comment.  A command is recognized at the start of a line; its length runs to the next command."""
    graph: dict[str, list[str]] = {}
    lines: dict[str, int] = {}
    theorems: dict[str, list[tuple[int, int]]] = {}
    kinds: collections.Counter = collections.Counter()
    extra = collections.Counter()
    nbytes = 0
    for root, _dirs, files in os.walk(src):
        for f in files:
            if not f.endswith(".lean"):
                continue
            p = os.path.join(root, f)
            mod = os.path.relpath(p, src)[:-5].replace(os.sep, ".")
            with open(p, "rb") as h:
                data = h.read()
            nbytes += len(data)
            lines[mod] = data.count(b"\n")
            text = data.decode("utf-8", "replace").split("\n")
            deps, comment, header, starts = [], False, True, []
            for i, ln in enumerate(text):
                if header:
                    s = ln.strip()
                    if comment:
                        comment = "-/" not in s
                    elif s.startswith("/-"):
                        comment = "-/" not in s
                    elif s and not s.startswith("--") and not s.startswith("module") and not s.startswith("prelude"):
                        m = IMPORT.match(ln)
                        if m:
                            deps.append(m.group(1))
                        else:
                            header = False
                if not ln or ln[0] in " \t":
                    continue
                m = COMMAND.match(ln)
                if m:
                    kinds[m.group(1)] += 1
                    starts.append((i, m.group(1)))
                    extra["docstrings"] += i > 0 and text[i - 1].rstrip().endswith("-/")
                elif OTHER.match(ln):
                    starts.append((i, None))
                    extra["variable_commands"] += ln.startswith("variable")
                    extra["module_docstrings"] += ln.startswith("/-!")
            starts.append((len(text), None))
            found = []
            for (i, k), (j, _k) in zip(starts, starts[1:]):
                if k in ("theorem", "lemma"):
                    n = j - i
                    while n > 1 and not text[i + n - 1].strip():
                        n -= 1
                    found.append((i + 1, n))
            theorems[mod] = found
            graph[mod] = deps
    return graph, lines, theorems, kinds, dict(extra), nbytes


def read_masks(atlas: Path) -> dict[tuple[str, int], int | None]:
    """(file, line) of a written theorem or lemma -> its type-or-value mask towards the five endpoints;
    None for the names that several modules define."""
    index = json.loads((atlas / "index.json").read_text(encoding="utf-8"))
    out = {}
    for i in range(-(-index["count"] // index["recordStride"])):
        with gzip.open(atlas / "records" / f"{i}.json.gz") as h:
            for r in json.load(h):
                out[(r["file"], r["line"])] = None if r["match"].startswith("ambiguous") else (r["termMask"] or 0)
    return out


def dirof(mod: str) -> str:
    return mod.rpartition(".")[0]


def census(src: Path) -> dict:
    model = json.loads((ROOT / "data" / "model.json").read_text(encoding="utf-8"))
    graph, lines, theorems, kinds, extra, nbytes = read_archive(src)
    lemmas = {m: len(v) for m, v in theorems.items()}
    atlas = atlas_data()
    masks = read_masks(atlas) if atlas else None
    mods = set(graph)
    inner = {m: [x for x in ds if x in mods] for m, ds in graph.items()}
    outer = collections.Counter(x.split(".")[0] for ds in graph.values() for x in ds if x not in mods)
    total_lines, total_lemmas = sum(lines.values()), sum(lemmas.values())

    def cone(roots):
        seen, stack = set(), [r for r in roots if r in mods]
        while stack:
            m = stack.pop()
            if m not in seen:
                seen.add(m)
                stack.extend(x for x in inner[m] if x not in seen)
        return seen

    def mass(ms) -> dict:
        ms = list(ms)
        return {"modules": len(ms), "lines": sum(lines[m] for m in ms), "lemmas": sum(lemmas[m] for m in ms),
                "command_lines": sum(n for m in ms for _l, n in theorems[m]), "directories": len({dirof(m) for m in ms})}

    # the longest chain of imports below Main (depth-first, without recursion)
    depth: dict[str, int] = {}
    stack = [(MAIN, iter(inner[MAIN]))]
    opened = {MAIN}
    while stack:
        m, it = stack[-1]
        for x in it:
            if x not in opened:
                opened.add(x)
                stack.append((x, iter(inner[x])))
                break
        else:
            depth[m] = 1 + max((depth[y] for y in inner[m]), default=0)
            stack.pop()

    # directories
    # per directory: modules, lines, theorem commands, lines of theorem commands, reached commands, their lines
    D: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    lengths = {"all": collections.Counter(), "reached": collections.Counter()}
    span = {"all": collections.Counter(), "reached": collections.Counter()}
    modules_reached = ambiguous = unjoined = 0
    for m in mods:
        d = D[dirof(m)]
        d[0] += 1
        d[1] += lines[m]
        d[2] += lemmas[m]
        hit = False
        for line, n in theorems[m]:
            d[3] += n
            lengths["all"][bucket(n)] += 1
            span["all"][bucket(n)] += n
            if masks is None:
                continue
            key = (m.replace(".", "/") + ".lean", line)
            if key not in masks:
                unjoined += 1
            elif masks[key] is None:
                ambiguous += 1
            elif masks[key]:
                d[4] += 1
                d[5] += n
                hit = True
                lengths["reached"][bucket(n)] += 1
                span["reached"][bucket(n)] += n
        modules_reached += hit
    by_size = sorted(D, key=lambda k: -D[k][1])
    concentration, run = [], 0
    for i, k in enumerate(by_size, 1):
        run += D[k][1]
        if i in CUTS:
            concentration.append({"largest": i, "share_of_lines": round(run / total_lines, 4)})

    # which modules depend on which (for the dependents of a digest)
    users: dict[str, set[str]] = collections.defaultdict(set)
    for m, ds in inner.items():
        for x in ds:
            users[x].add(m)

    def dependents(ms) -> int:
        seen, stack = set(), list(ms)
        while stack:
            m = stack.pop()
            if m not in seen:
                seen.add(m)
                stack.extend(users[m] - seen)
        return len(seen) - len(set(ms))

    # the blueprint: where its modules live, and the rings of directories around them
    bp_mods = sorted({n["module"] for n in model["nodes"] if n.get("module")})
    missing = [m for m in bp_mods if m not in mods]
    spine = collections.Counter(dirof(m) for m in bp_mods if m in mods)
    nodes_in = collections.Counter(dirof(n["module"]) for n in model["nodes"] if n.get("module") in mods)
    dgraph: dict[str, set[str]] = collections.defaultdict(set)
    for m, ds in inner.items():
        a = dirof(m)
        for x in ds:
            if dirof(x) != a:
                dgraph[a].add(dirof(x))
    ring_of: dict[str, int] = {k: 0 for k in spine}
    rings, front, k = [], set(spine), 0
    while front:
        rings.append({"ring": k, "directories": len(front), "lines": sum(D[x][1] for x in front),
                      "share_of_lines": round(sum(D[x][1] for x in front) / total_lines, 4)})
        nxt = set().union(*(dgraph[a] for a in front)) - set(ring_of)
        k += 1
        for x in nxt:
            ring_of[x] = k
        front = nxt

    # the digests written so far: their directory, and what lies beneath it
    digests = []
    for conc in sorted((ROOT / "digests").glob("*/concordance.json")):
        c = json.loads(conc.read_text(encoding="utf-8"))
        home = c["directory"]["path"].strip("/").replace("/", ".")
        own = [m for m in mods if dirof(m) == home]
        below = cone(own)
        digests.append({"digest": conc.parent.name, "directory": home, "own": mass(own), "cone": mass(below),
                        "dependents": dependents(own), "declarations_cited": len(c["declarations"]),
                        "blueprint_nodes": nodes_in.get(home, 0)})

    unit = digests[0]["own"]["lines"] if digests else None
    units = {}
    if unit:
        units = {"unit_lines": unit, "unit_lemmas": digests[0]["own"]["lemmas"],
                 "by_lines": total_lines // unit, "by_lemmas": total_lemmas // digests[0]["own"]["lemmas"],
                 "by_directory": {str(c): sum(max(1, math.ceil(v[1] / (c * unit))) for v in D.values()) for c in (1, 2, 3)},
                 "reached_command_lines_per_digest": (sum(v[5] for v in D.values()) // digests[0]["own"]["command_lines"]) if masks else None,
                 "reached_by_directory": ({str(c): sum(math.ceil(v[5] / (c * digests[0]["own"]["command_lines"])) for v in D.values() if v[5])
                                           for c in (1, 2, 3)} if masks else None),
                 "spine_by_lines": sum(D[k][1] for k in spine) // unit,
                 "spine_by_directory": {str(c): sum(max(1, math.ceil(D[k][1] / (c * unit))) for k in spine) for c in (1, 2, 3)}}

    return {
        "schema": 1,
        "pins": {"mirror_commit": model["pins"]["mirror_commit"], "archive_sha256": model["pins"]["archive_sha256"]},
        "totals": {"modules": len(mods), "bytes": nbytes, "lines": total_lines, "lemmas": total_lemmas,
                   "directories": len(D), "lines_per_lemma": round(total_lines / total_lemmas, 1),
                   "imports_outside": dict(outer.most_common())},
        "commands": {"kinds": dict(kinds.most_common()), **extra,
                     "theorem_lengths": {b: [lengths["all"][b], span["all"][b]] for _t, b in BUCKETS}},
        "used": None if masks is None else {
            "source": "endpoint masks (types or values) of the embedding atlas records, submitted edition",
            "theorem_commands": sum(v[2] for v in D.values()), "command_lines": sum(v[3] for v in D.values()),
            "reached": sum(v[4] for v in D.values()), "reached_lines": sum(v[5] for v in D.values()),
            "ambiguous_names": ambiguous, "unjoined": unjoined, "modules_with_a_reached_command": modules_reached,
            "directories": {"with_theorem_commands": sum(1 for v in D.values() if v[2]),
                            "none_reached": sum(1 for v in D.values() if v[2] and not v[4]),
                            "all_reached": sum(1 for v in D.values() if v[2] and v[4] == v[2])},
            "lengths": {b: [lengths["reached"][b], span["reached"][b]] for _t, b in BUCKETS}},
        "main": {"module": MAIN, "cone": mass(cone([MAIN])), "longest_import_chain": depth[MAIN]},
        "concentration": concentration,
        "blueprint": {"nodes": len(model["nodes"]), "nodes_with_module": sum(1 for n in model["nodes"] if n.get("module")),
                      "modules": len(bp_mods), "missing": missing, "components": len(model["components"]),
                      "directories": [{"directory": k, "files": D[k][0], "lines": D[k][1], "lemmas": D[k][2],
                                       "nodes": nodes_in[k]} for k in sorted(spine, key=lambda k: -D[k][1])],
                      "lines": sum(D[k][1] for k in spine), "share_of_lines": round(sum(D[k][1] for k in spine) / total_lines, 4)},
        "rings": rings,
        "digests": digests,
        "units": units,
        "directories": [[k, D[k][0], D[k][1], D[k][2], ring_of.get(k, -1), D[k][3], D[k][4], D[k][5]] for k in sorted(D)],
    }


def check(c: dict) -> list[str]:
    bad = []
    model = json.loads((ROOT / "data" / "model.json").read_text(encoding="utf-8"))
    if c["pins"]["mirror_commit"] != model["pins"]["mirror_commit"]:
        bad.append("the census was taken at another commit of the archive than the model's pin")
    t = c["totals"]
    for i, key in ((1, "modules"), (2, "lines"), (3, "lemmas")):
        if sum(r[i] for r in c["directories"]) != t[key]:
            bad.append(f"the directory table does not add up to the total number of {key}")
    if len(c["directories"]) != t["directories"]:
        bad.append("the directory table and the number of directories disagree")
    if sum(r["directories"] for r in c["rings"]) != t["directories"]:
        bad.append("the rings around the blueprint do not exhaust the directories")
    u = c.get("used")
    if u:
        if u["unjoined"]:
            bad.append("theorem commands without a record in the atlas data")
        if sum(r[6] for r in c["directories"]) != u["reached"] or sum(v[0] for v in u["lengths"].values()) != u["reached"]:
            bad.append("the reached commands do not add up")
    if c["blueprint"]["missing"]:
        bad.append("blueprint modules absent from the archive: " + ", ".join(c["blueprint"]["missing"]))
    return bad


def main() -> int:
    if "--check" in sys.argv:
        if not OUT.exists():
            print("census: data/census.json is missing (python3 -B scripts/archive_census.py)")
            return 1
        c = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        src = archive_src()
        if src is None:
            print("census: the archive is not available here (set ARCHIVE_SRC)")
            return 1
        c = census(src)
        head = {k: v for k, v in c.items() if k != "directories"}
        text = json.dumps(head, ensure_ascii=False, indent=1)[:-2] + ',\n "directories": [\n  '
        text += ",\n  ".join(json.dumps(r, ensure_ascii=False) for r in c["directories"]) + "\n ]\n}\n"
        OUT.write_text(text, encoding="utf-8")
    bad = check(c)
    for b in bad:
        print("census: " + b)
    t = c["totals"]
    print(f"census: {t['modules']:,} modules, {t['lines']:,} lines, {t['lemmas']:,} theorems and lemmas in "
          f"{t['directories']:,} directories; blueprint in {len(c['blueprint']['directories'])} directories"
          + (f"; the endpoints reach {c['used']['reached']:,} theorem commands" if c.get("used") else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
