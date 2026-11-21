#!/usr/bin/env python3
"""Assemble the illustrated atlas: a single self-contained HTML file.

    python3 -B scripts/build_atlas.py      # writes atlas/index.html (+ assets/figures/blueprint-graph.svg)

Inputs: data/model.json (scripts/model.py), assets/figures/*.svg and facts.json
(scripts/build_figures.py), data/source/native-scopes.json, data/announcement_dates.json,
verification/logs/axioms.json (scripts/lean_audit.py), lean/Atlas/Architecture.lean and
references/archive-bridges/*.lean. Sources: atlas/src/atlas.{css,js}.

The blueprint graph layout (layered, left = suppliers, right = endpoints) is computed here.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import defaultdict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "assets" / "figures"


def load(p: str):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def esc(s) -> str:
    return escape(str(s), quote=True)


def md(s: str) -> str:
    """Inline Markdown (code, bold, italics) outside $...$ math; HTML-escaped."""
    parts = re.split(r"(\$\$[\s\S]+?\$\$|\$[^$\n]+\$)", s)
    out = []
    for i, p in enumerate(parts):
        if i % 2:
            out.append(esc(p))
        else:
            t = esc(p)
            t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
            t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
            t = re.sub(r"(^|[\s(])\*([^*\n]+)\*", r"\1<em>\2</em>", t)
            out.append(t)
    return "".join(out)


KW = set("""theorem lemma def structure where fun by exact intro have obtain rcases with match namespace end
variable inductive example import rw at refine generalize subst change apply let show from if then else calc
noncomputable section open instance class abbrev private protected deriving set_option simp simpa omega
decide""".split())


def hl(code: str) -> str:
    out, last = [], 0
    for m in re.finditer(r"(--[^\n]*|/-[\s\S]*?-/|\"(?:[^\"\\]|\\.)*\"|[A-Za-z_][A-Za-z0-9_'.₀-₉]*|\d+)", code):
        out.append(esc(code[last:m.start()]))
        t = m.group(0)
        if t.startswith("--") or t.startswith("/-"):
            out.append(f'<span class="c">{esc(t)}</span>')
        elif t.startswith('"'):
            out.append(f'<span class="s">{esc(t)}</span>')
        elif t in KW:
            out.append(f'<span class="k">{esc(t)}</span>')
        elif t in ("Type", "Prop", "Sort", "True", "False", "RiemannHypothesis"):
            out.append(f'<span class="t">{esc(t)}</span>')
        elif t.isdigit():
            out.append(f'<span class="n">{esc(t)}</span>')
        else:
            out.append(esc(t))
        last = m.end()
    out.append(esc(code[last:]))
    return "".join(out)


def strip_svg_header(svg: str) -> str:
    return re.sub(r"^<\?xml[^>]*>\s*", "", svg.strip())


def figure(name: str, uid: str | None = None) -> str:
    svg = strip_svg_header((FIG / f"{name}.svg").read_text(encoding="utf-8"))
    svg = svg.replace('width="', 'data-w="', 1).replace('height="', 'data-h="', 1)
    # make ids unique per figure instance (titles/descs and markers)
    u = uid or name
    svg = svg.replace('id="t"', f'id="t-{u}"').replace('id="d"', f'id="d-{u}"').replace(
        'aria-labelledby="t d"', f'aria-labelledby="t-{u} d-{u}"')
    return svg


def lean_block(path: Path, start_pat: str, stop_pat: str | None = None, max_lines: int = 60) -> str:
    """Quote a declaration verbatim: from the line matching start_pat (including the docstring
    immediately above it) to the first blank line after it (or stop_pat)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(lines) if re.search(start_pat, l))
    j0 = i
    while j0 > 0 and (lines[j0 - 1].strip().startswith(("/--", "--", "`")) or
                      (lines[j0 - 1].strip() and not lines[j0 - 1].strip().startswith(("theorem", "def", "structure"))
                       and "-/" in "\n".join(lines[j0 - 1:i]) and "/--" in "\n".join(lines[max(0, j0 - 12):i]))):
        if lines[j0 - 1].strip() == "":
            break
        j0 -= 1
        if lines[j0].strip().startswith("/--"):
            break
    j = i + 1
    while j < len(lines) and j - i < max_lines:
        if stop_pat and re.search(stop_pat, lines[j]):
            break
        if not stop_pat and lines[j].strip() == "":
            break
        j += 1
    return "\n".join(lines[j0:j]).rstrip()


# --------------------------------------------------------------------------------------
# Blueprint layout
# --------------------------------------------------------------------------------------
def layout(model: dict, NW=212, NH=46, DX=262, DY=60):
    nodes = [n["id"] for n in model["nodes"]]
    comp_index = {c["id"]: k for k, c in enumerate(model["components"])}
    ncomp = {n["id"]: n["component"] for n in model["nodes"]}
    soft = {"analogy"}
    consumers, callees = defaultdict(list), defaultdict(list)
    for e in model["edges"]:
        if e["relation"] in soft:
            continue
        consumers[e["to"]].append(e["from"])
        callees[e["from"]].append(e["to"])
    rank: dict[str, int] = {}

    def r(v: str) -> int:
        if v not in rank:
            rank[v] = 0 if not consumers[v] else 1 + max(r(u) for u in consumers[v])
        return rank[v]

    for v in nodes:
        r(v)
    R = max(rank.values())
    exports = {n["id"] for n in model["nodes"] if n["section"] == "exports"}
    kinds = {n["id"]: n["kind"] for n in model["nodes"]}
    # orphan lemmas (no consumer in the selected graph, not an export, not a motivation) are foundational
    # inputs: put them with the deepest suppliers, on the far left
    for v in nodes:
        if not consumers[v] and v not in exports and kinds[v] != "motivation":
            rank[v] = R
    # motivations sit one layer right of the declaration they motivate
    for e in model["edges"]:
        if e["relation"] in soft and kinds[e["from"]] == "motivation":
            rank[e["from"]] = max(0, rank[e["to"]] - 1)
    layers: dict[int, list[str]] = defaultdict(list)
    for v in nodes:
        layers[rank[v]].append(v)
    for k in layers:
        layers[k].sort(key=lambda v: (comp_index[ncomp[v]], v))
    nbrs = defaultdict(set)
    for e in model["edges"]:
        nbrs[e["from"]].add(e["to"])
        nbrs[e["to"]].add(e["from"])

    def pos_map():
        return {v: (i - (len(layers[k]) - 1) / 2) for k in layers for i, v in enumerate(layers[k])}

    for sweep in range(24):
        p = pos_map()
        order = range(R + 1) if sweep % 2 == 0 else range(R, -1, -1)
        for k in order:
            def key(v):
                ns = [p[u] for u in nbrs[v]]
                bc = sum(ns) / len(ns) if ns else p[v]
                return (bc + 0.18 * (comp_index[ncomp[v]] - 6.5) / 6.5, comp_index[ncomp[v]])
            layers[k].sort(key=key)
            p = pos_map()
    maxlen = max(len(v) for v in layers.values())
    H = maxlen * DY
    coords = {}
    for k, vs in layers.items():
        x = (R - k) * DX
        top = (H - len(vs) * DY) / 2
        for i, v in enumerate(vs):
            coords[v] = (round(x, 1), round(top + i * DY, 1))
    W = R * DX + NW
    return coords, {"w": W, "h": H, "nw": NW, "nh": NH, "ranks": R + 1}


def short(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def static_graph_svg(model: dict, L: dict) -> str:
    """A static rendering of the blueprint graph for the book, the vault and the PDF."""
    strata = {s["id"]: s["color"] for s in model["strata"]}
    comps = {c["id"]: c for c in model["components"]}
    tiers = model["tiers"]
    nodes = {n["id"]: n for n in model["nodes"]}
    NW, NH = L["nw"], L["nh"]
    pad = 30
    W, H = L["w"] + 2 * pad, L["h"] + 2 * pad
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">'
           f'<title>Blueprint graph: {len(model["nodes"])} nodes</title><desc>Layered dependency graph of the reading '
           'project\'s blueprint: suppliers on the left, the five endpoints on the right; bar colour = stratum, '
           'dot colour = verification tier.</desc>'
           '<defs><marker id="bh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
           'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#94a3b8"/></marker></defs>'
           f'<rect width="100%" height="100%" fill="#ffffff"/><g transform="translate({pad},{pad})">']
    for e in model["edges"]:
        a, b = nodes[e["to"]], nodes[e["from"]]
        x1, y1, x2, y2 = a["x"] + NW, a["y"] + NH / 2, b["x"], b["y"] + NH / 2
        dx = max(36, abs(x2 - x1) / 2)
        dash = {"statement": ' stroke-dasharray="2 4"', "support": ' stroke-dasharray="6 4"',
                "analogy": ' stroke-dasharray="6 4"', "alternative": ' stroke-dasharray="8 3 2 3"'}.get(e["relation"], "")
        out.append(f'<path d="M{x1},{y1} C{x1 + dx},{y1} {x2 - dx},{y2} {x2 - 3},{y2}" fill="none" stroke="#94a3b8" '
                   f'stroke-width="1.2" opacity="0.6"{dash} marker-end="url(#bh)"/>')
    for n in model["nodes"]:
        col = strata[comps[n["component"]]["stratum"]]
        out.append(f'<g transform="translate({n["x"]},{n["y"]})"><rect width="{NW}" height="{NH}" rx="9" fill="#fff" '
                   f'stroke="#cbd5e1"/><rect width="6" height="{NH}" rx="3" fill="{col}"/>'
                   f'<circle cx="{NW - 12}" cy="12" r="6" fill="{tiers[n["tier"]]["color"]}"/>'
                   f'<text x="14" y="19" font-family="Inter, Helvetica, Arial, sans-serif" font-size="11.5" '
                   f'font-weight="600" fill="#0f172a">{esc(n["short"])}</text>'
                   f'<text x="14" y="35" font-family="Menlo, monospace" font-size="9.5" fill="#64748b">'
                   f'{esc(n["decl_short"])}</text></g>')
    out.append("</g></svg>\n")
    return "".join(out)


# --------------------------------------------------------------------------------------
# Static sections
# --------------------------------------------------------------------------------------
GRID = {"galois": (1, 1), "inputs": (1, 2), "cohomology": (1, 3), "primes": (1, 4),
        "family": (2, 2), "comparison": (2, 3), "hosts": (2, 4),
        "statistic": (3, 1), "residues": (3, 2), "criterion": (3, 3), "choreography": (3, 4),
        "endpoints": (4, 1), "reflection": (4, 2), "descent": (4, 3)}


def tier_badge(model, t: str) -> str:
    T = model["tiers"][t]
    return (f'<span class="tier" style="--tc:{T["color"]}" title="{esc(T["meaning"])}"><i>{esc(T["icon"])}</i>'
            f'{esc(T["label"])}</span>')


def map_html(model) -> str:
    strata = model["strata"]
    out = ['<div class="map" id="map"><svg class="map-svg" id="map-svg" aria-hidden="true"></svg>']
    for i, s in enumerate(strata):
        out.append(f'<div class="map-col-head" data-col="{i + 1}" style="grid-column:{i + 1};grid-row:1">'
                   f'<h3 style="color:{s["color"]}"><span class="dot" style="background:{s["color"]}"></span>'
                   f'{esc(s["title"])}</h3><p>{esc(s["blurb"])}</p></div>')
    scol = {s["id"]: s["color"] for s in strata}
    for c in model["components"]:
        col, row = GRID[c["id"]]
        out.append(
            f'<div class="comp" tabindex="0" role="button" data-id="{c["id"]}" data-col="{col}" data-row="{row}" '
            f'style="grid-column:{col};grid-row:{row + 1};--sc:{scol[c["stratum"]]}" '
            f'aria-label="{esc(c["title"])}: open details">'
            f'<span class="num">{c["n"]}</span><h4>{esc(c["title"])}</h4><div class="kick">{esc(c["kicker"])}</div>'
            f'<div class="gist">{md(c["gist"])}</div><div>{tier_badge(model, c["tier"])}</div></div>')
    out.append("</div>")
    return "".join(out)


def ideas_html(model, facts) -> str:
    F = facts
    sp = F["spotlight"]["windows"]
    pct = ", ".join(f"{100 * v['mass_inside']:.1f}%" for v in sp.values())
    comps = {c["id"]: c for c in model["components"]}
    ideas = [
        ("explicit-formula", "statistic", True, "The quantity the proof must control", ["computed"],
         f"The archive's statistic is $G(y)=\\sum_{{n\\le y}}\\Lambda(n)(y/n-1)-y\\log y+(1+\\gamma)y$. By the explicit "
         f"formula, $G(y)-\\log 2\\pi=-\\sum_\\rho y^\\rho/(\\rho(\\rho-1))$ up to $O(y^{{-2}})$. The amber curve is computed "
         f"from the primes, the indigo one from the first {F['explicit']['zeros_used']} zeros (computed here by "
         f"Euler–Maclaurin summation); on $[10^2, 2\\cdot10^6]$ they differ by at most "
         f"${F['explicit']['max_abs_difference_normalized']}\\sqrt y$. A zero at $\\beta+i\\gamma$ off the line would add "
         f"oscillations of size $y^{{\\beta-1/2}}$ (dashed: a hypothetical zero at $0.62+40i$). The proof needs only an "
         f"*upper* bound for $G$, and only on windows $[Y,Y^{{3/2}}]$."),
        ("strip", "reflection", False, "Only the right half-plane matters", ["schematic", "computed"],
         f"If $L(\\rho,\\chi)=0$ in the strip, the functional equation gives $L(1-\\rho,\\chi^{{-1}})=0$; with complex "
         f"conjugation this is the mirror image of $\\rho$ in the critical line. So it suffices to clear "
         f"$\\operatorname{{Re}}s>\\tfrac12$ for every character. The dots are the first {F['strip']['zeros_drawn']} zeta zeros, "
         f"computed."),
        ("ramp", "residues", False, "Ramps make the transform exact", ["computed"],
         f"Each prime power switches on a ramp $\\Lambda(n)(y/n-1)_+$ at $y=n$. The Mellin transform of one ramp is "
         f"$n^{{-s}}/(s(s-1))$ (checked numerically at {F['ramp']['mellin_checks']} points, error at most "
         f"{F['ramp']['max_abs_error']:.1e}). Summed, the ramps produce $-L'/L$; the centring terms remove the pole at "
         f"$s=1$, and what remains hovers around $\\log 2\\pi$, the residue at $s=0$."),
        ("residue", "residues", True, "Zeros cannot hide in a positive family", ["schematic"],
         "At a common zero $\\rho$ each member of a positive family contributes a positive multiple of "
         "$-1/(\\rho(\\rho-1))$ to the residue, so the contributions point the same way and add up to $S(\\rho)>0$ times "
         "that number. With signed weights two zeros could cancel; the archive requires every weight $a_i>0$."),
        ("spotlight", "criterion", True, "High derivatives are a spotlight", ["computed"],
         f"The $k$-th derivative of the Laplace transform weights $g(u)=G_F(e^u)$ by $u^k e^{{-\\sigma u}}/k!$, a bump at "
         f"$u=k/\\sigma$ whose relative width shrinks like $k^{{-1/2}}$. Aimed at the window $[U,1.5U]$ with "
         f"$k=\\lceil 1.25\\,\\sigma U\\rceil$ it puts {pct} of its mass inside for $U=20,40,80,160$. A pole at distance $d$ "
         f"contributes about $d^{{-k}}$; the window bound allows only $e^{{\\eta U}}r^{{-k}}$ with $r>d$, which is "
         f"impossible once $k\\ge U$ and $\\eta$ is small."),
        ("choreography", "choreography", True, "The order of choices", ["schematic"],
         "The losses $e_D=2$, $e_L=0$ are fixed first. Given a zero with $\\operatorname{Re}\\rho=\\beta>\\tfrac12$, take "
         "$\\theta=\\tfrac12+\\tfrac12\\min(\\beta-\\tfrac12,\\tfrac12)$ and then $\\varepsilon$ with "
         "$\\tfrac12+9\\varepsilon\\le\\theta$; the arithmetic supplies windows for that $\\varepsilon$, and the "
         "criterion excludes the zero. A bound at $\\varepsilon=0$ is never needed."),
        ("balance", "comparison", True, "Where the square root, and every ε, is paid", ["exact"],
         "The geometric discrepancy has a cost $x/m$ and a cost $m$; with $m=x^a$ their larger exponent "
         "$\\max(1-a,a)$ is smallest at $a=\\tfrac12$ — the announcement's \"chain of length $\\sqrt X$\". The staircase "
         "adds the exact losses of the finite comparison: "
         "$\\tfrac{13}{8}+(e_D+e_L+3)+1+\\tfrac38+1=e_D+e_L+7$, which is $9$ for the archive's $e_D=2$, $e_L=0$."),
        ("windows", "cohomology", True, "One interval survives every exceptional twist", ["computed", "formal"],
         "An $\\ell$-adic determinant estimate leaves at most $R$ centres, and each centre accounts for at most one "
         "exceptional twist (ultrametric separation, proved in this repository's Lean library). Each exceptional twist "
         "forbids a logarithmic interval $[a,Ba)$, and the induction of `window1` finds $[y,2y]$ avoiding all of them. "
         "The reading project's example — twists $2^{16}$ and $2^{180}$, $C_t=2$, $\\eta=1$, $X=2^{128}$ — gives "
         "$[Y,Y^2]=[2^{16},2^{32}]$."),
        ("behrend", "primes", True, "No three in a line: Behrend spheres", ["computed", "formal"],
         f"Integer vectors of fixed norm, written in a base large enough to avoid carries, satisfy no short affine "
         f"relation, because a line meets a sphere at most twice. The six permutations of (0,1,2) in base 24 pass all "
         f"{F['behrend']['checks']:,} relation checks; the general statement is `BehrendReading.sphere_rel`, compiled in "
         f"this repository."),
        ("chain", "family", False, "A chain of about √x theta lifts", ["schematic"],
         "Each theta lift $U(X_j)\\to U(X_{j+1})$ is meant to mimic one order of multiplicity in Stepanov's method. "
         "The archive's `RankVal` fixes the length between $\\sqrt{x\\delta_1}$ and $2\\sqrt{x\\delta_1}$, "
         "$\\delta_1=x^{-\\varepsilon/8}$; denominators clear by $\\prod_j D_j$ (`ChainInt`)."),
        ("galois", "galois", False, "A Galois representation by quadratic descent", ["schematic"],
         "For a regular algebraic polarized cuspidal $\\pi$ on $\\mathrm{GL}_a$ over a CM field $E$, representations over "
         "infinitely many $K=E(\\sqrt{-p})$ are patched, through index-two trace identities, into one $\\rho$ over $E$ "
         "whose Frobenius polynomials match the Satake parameters of $\\pi$ at all but finitely many places."),
    ]
    tagcls = {"computed": "num", "exact": "num", "schematic": "sch", "formal": "formal"}
    out = ['<div class="ideas">']
    for name, cid, wide, title, tags, text in ideas:
        c = comps[cid]
        out.append(
            f'<article class="card idea{" wide" if wide else ""}"><div class="fig" id="fig-{name}">{figure(name)}</div>'
            f'<div class="tags">{"".join(f"<span class=\'tag {tagcls[t]}\'>{t}</span>" for t in tags)}</div>'
            f'<h3>{esc(title)}</h3><p>{md(text)}</p>'
            f'<div class="more"><button class="btn light" data-open-comp="{cid}">Component {c["n"]}: '
            f'{esc(c["title"])} →</button></div></article>')
    out.append("</div>")
    return "".join(out)


def ledger_html(model, scopes, audit) -> str:
    st = model["status"]
    tiers = model["tiers"]
    out = ['<div class="cuts">']
    for k in model["cuts"]:
        out.append(
            f'<div class="card cutcard{" two" if k["tier"] == "two-kernels" else ""}">'
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">{tier_badge(model, k["tier"])}</div>'
            f'<h3 style="margin-top:10px">{esc(k["title"])}</h3><div class="mono small">{esc(k["lean"])}</div>'
            f'<div class="prem">$$\\Bigl[\\,{esc(k["premise"])}\\,\\Bigr]$$</div>'
            f'<p><b>⟹ {esc(k["conclusion"])}</b></p><p class="small">{esc(k["evidence"])}</p>'
            f'<p class="small">Source: <a href="../{esc(k["source"])}"><code>{esc(k["source"])}</code></a>. '
            f'Components inside: {", ".join(esc(c["title"]) for c in model["components"] if c["id"] in k["components"])}.</p></div>')
    out.append("</div>")
    # frontier statistics from the node tiers
    from collections import Counter
    cnt = Counter(n["tier"] for n in model["nodes"])
    out.append('<div class="frontier">')
    for t in ("checked", "covered", "read", "reported"):
        out.append(f'<div><b>{cnt.get(t, 0)}</b>{tier_badge(model, t)}<div class="small muted" style="margin-top:6px">'
                   f'{esc(tiers[t]["meaning"])}</div></div>')
    out.append("</div>")
    out.append(f'<p class="small muted">Tiers of the {len(model["nodes"])} blueprint nodes, computed from the receipts '
               f'registered in the reading project (as of {esc(st["as_of"][:16].replace("T", " "))} UTC); motivation: '
               f'{cnt.get("motivation", 0)}. A component\'s own tier can also rest on receipts for declarations outside '
               f'the blueprint, named in its status (for example <code>Gz_eq</code>, <code>QH.pairEx</code> and the bridge '
               f'theorems).</p>')
    # external report
    links = " · ".join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["label"])}</a>'
                       for s in st["external_sources"])
    out.append(f'<div class="card" style="padding:18px 20px;margin:22px 0"><h3>External report</h3><p>{esc(st["external"])}</p>'
               f'<p class="small">{links}</p><h3 style="margin-top:14px">The reading project\'s own checks</h3>'
               f'<p>{esc(st["native"])}</p><p class="small muted">Headline at {esc(st["as_of"][:16].replace("T", " "))} UTC: '
               f'{esc(st["headline"])} Full original build on Helios (job {esc(st["job"])}): {esc(st["full"])}.</p></div>')
    # native scopes table
    out.append('<h3 style="margin-top:28px">What the native receipts cover</h3><div class="tablewrap"><table class="t">'
               '<thead><tr><th>Scope</th><th>Authority</th><th>Hypotheses</th><th>Conclusion</th><th>Original modules</th>'
               '<th>Lean</th></tr></thead><tbody>')
    for s in scopes:
        out.append(f'<tr><td><b>{esc(s["title"])}</b></td><td>{esc(s["authority"])}</td><td>{esc(s["assumption"])}</td>'
                   f'<td>{esc(s["conclusion"])}</td><td style="text-align:right">{s["original_project_module_count"]:,}</td>'
                   f'<td>{esc(s["lean_version"])}</td></tr>')
    out.append("</tbody></table></div>")
    # open questions
    nodes = {n["id"]: n for n in model["nodes"]}
    out.append('<h3 style="margin-top:28px">Open verification questions</h3><ol>')
    for q in model["audit"]:
        out.append(f'<li><b>{esc(q["title"])}.</b> {esc(q["acceptance"])} '
                   f'<button class="chip" data-open-node="{q["node"]}">{esc(nodes[q["node"]]["title"])}</button></li>')
    out.append("</ol>")
    return "".join(out)


def lean_html(model, audit) -> str:
    arch = ROOT / "lean" / "Atlas" / "Architecture.lean"
    blocks = [
        ("The arithmetic supply, as the single hypothesis", lean_block(arch, r"^structure Supply", r"^/-- The supply and the engine")),
        ("The second verified cut, in the skeleton", lean_block(arch, r"^theorem endpoints_of_supply")),
        ("The whole architecture in one record", lean_block(arch, r"^structure Architecture", r"^/-! ## The hypotheses")),
    ]
    out = ['<div class="ideas">']
    for title, code in blocks:
        out.append(f'<article class="card idea"><h3>{esc(title)}</h3><pre class="lean">{hl(code)}</pre>'
                   f'<p class="small muted" style="margin-top:8px">Quoted from <code>lean/Atlas/Architecture.lean</code>.</p></article>')
    wb = ROOT / "references" / "archive-bridges" / "WindowBridge.lean"
    db = ROOT / "references" / "archive-bridges" / "DirichletBridge.lean"
    out.append(f'<article class="card idea"><h3>The two cuts against the real archive</h3>'
               f'<pre class="lean">{hl(lean_block(wb, r"^def OneSidedWindows"))}\n\n'
               f'{hl(lean_block(wb, r"^theorem riemannHypothesis_of_prime_windows", r"apply Formalism"))}\n\n'
               f'{hl(lean_block(db, r"^theorem endpoints_of_topG_vWin401", r"have hχ"))}</pre>'
               f'<p class="small muted" style="margin-top:8px">Quoted from <code>references/archive-bridges/</code>; compiled '
               f'against the archive at Lean 4.33.1 by the reading project (receipts in its <code>evidence/</code>).</p></article>')
    # The destination layer instantiated with Mathlib's zeta (built on a cluster; the record is
    # verification/logs/mathlib-zeta-axioms.json). Shown only with the status the record carries.
    mz_path = ROOT / "verification" / "logs" / "mathlib-zeta-axioms.json"
    mz_file = ROOT / "lean-mathlib" / "AtlasZeta.lean"
    if mz_file.exists():
        mz = json.loads(mz_path.read_text(encoding="utf-8")) if mz_path.exists() else None
        if mz and mz.get("build") == "passed" and not mz.get("problems"):
            axs = sorted({x for v in mz["declarations"].values() for x in v})
            state = (f'Compiled against Mathlib at the archive\'s pins ({esc(mz["lean"].split(",")[0].replace("Lean (version ", "Lean "))}); '
                     f'axioms of <code>riemannHypothesis_of_right</code>: {esc(", ".join(mz["declarations"]["Atlas.Zeta.riemannHypothesis_of_right"]))}.')
            assert set(axs) <= {"propext", "Classical.choice", "Quot.sound"}, axs
        else:
            state = "Not yet compiled in this checkout (it needs Mathlib at the archive's pin; see BUILDING.md)."
        out.append(f'<article class="card idea" style="grid-column:1/-1"><h3>The destination layer, with Mathlib\'s ζ</h3>'
                   f'<pre class="lean">{hl(lean_block(mz_file, r"^theorem riemannHypothesis_of_right"))}</pre>'
                   f'<p class="small muted" style="margin-top:8px">Quoted from <code>lean-mathlib/AtlasZeta.lean</code>: the '
                   f'skeleton\'s reflection step instantiated with <code>riemannZeta</code> and Mathlib\'s functional equation. '
                   f'{state}</p></article>')
    out.append("</div>")
    rows = "".join(
        f'<tr><td><code>{esc(k)}</code></td><td>{"<span class=\'tier\' style=\'--tc:#059669\'><i>∅</i>none</span>" if not v else esc(", ".join(v))}</td></tr>'
        for k, v in audit["declarations"].items())
    out.append(f'<h3 style="margin-top:26px">Axiom report of this repository\'s library</h3>'
               f'<p class="small">{esc(audit["lean"])} · build {esc(audit["build"])} · problems: {len(audit["problems"])} · '
               f'generated {esc(audit["generated_utc"])}</p>'
               f'<div class="tablewrap"><table class="t"><thead><tr><th>Declaration</th><th>Axioms</th></tr></thead>'
               f'<tbody>{rows}</tbody></table></div>')
    return "".join(out)


def timeline_html(model) -> str:
    items = model["timeline"]
    scol = {s["id"]: s["color"] for s in model["strata"]}
    comps = {c["id"]: c for c in model["components"]}
    d0, d1 = dt.date(2026, 10, 4), dt.date(2026, 11, 18)
    W, H, x0, x1 = 1180, 250, 40, 1140
    def X(d):
        return x0 + (d - d0).days / (d1 - d0).days * (x1 - x0)
    out = [f'<div class="tl card" style="padding:14px 14px 4px"><svg viewBox="0 0 {W} {H}" role="img" aria-label="Timeline">'
           f'<line x1="{x0}" y1="200" x2="{x1}" y2="200" stroke="#cbd5e1" stroke-width="2"/>']
    d = d0
    while d <= d1:
        if d.day in (1, 8, 15, 22) or d == d0:
            out.append(f'<line x1="{X(d):.1f}" y1="196" x2="{X(d):.1f}" y2="206" stroke="#94a3b8"/>'
                       f'<text x="{X(d):.1f}" y="226" font-size="12" fill="#64748b" text-anchor="middle" '
                       f'font-family="Inter, Helvetica, Arial, sans-serif">{d.strftime("%-d %b")}</text>')
        d += dt.timedelta(days=1)
    stack = defaultdict(int)
    for it in sorted(items, key=lambda t: (t["date"], t["number"])):
        dd = dt.date.fromisoformat(it["date"])
        k = stack[it["date"]]
        stack[it["date"]] += 1
        cx, cy = X(dd), 182 - k * 24
        col = scol[comps[it["component"]]["stratum"]] if it["component"] else "#94a3b8"
        attr = f' data-open-comp="{it["component"]}" class="dotlink"' if it["component"] else ""
        out.append(f'<g{attr}><title>{it["number"]}. {esc(it["topic"])} ({esc(it["as_written"])}) — {esc(it["relation"])}</title>'
                   f'<circle cx="{cx:.1f}" cy="{cy}" r="10" fill="{col}" stroke="#fff" stroke-width="2"/>'
                   f'<text x="{cx:.1f}" y="{cy + 4}" font-size="10" font-weight="700" fill="#fff" text-anchor="middle" '
                   f'font-family="Inter, Helvetica, Arial, sans-serif">{it["number"]}</text></g>')
    out.append('</svg></div><div class="tablewrap" style="margin-top:16px"><table class="t"><thead><tr><th>#</th><th>Date</th>'
               '<th>Entry</th><th>Correspondence with the archive</th><th>Component</th></tr></thead><tbody>')
    for it in items:
        c = comps.get(it["component"]) if it["component"] else None
        cc = (f'<button class="chip" data-open-comp="{c["id"]}"><span class="dot" style="background:{scol[c["stratum"]]}">'
              f'</span>{c["n"]}. {esc(c["title"])}</button>') if c else '<span class="small muted">—</span>'
        out.append(f'<tr><td>{it["number"]}</td><td class="mono small">{esc(it["as_written"])}</td><td><b>{esc(it["topic"])}</b>'
                   f'<div class="small muted">{esc(it["assessment"])}</div></td><td><span class="relation">{esc(it["relation"])}</span></td>'
                   f'<td>{cc}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


STORY = [
    ("endpoints", "Start at the end: five Lean theorems, the first with exactly Mathlib's type `RiemannHypothesis`. "
     "All five rest on one statement: no Dirichlet $L$-function vanishes for $\\operatorname{Re}s>\\tfrac12$."),
    ("reflection", "Why only the right half? The functional equation mirrors a zero at $s$ to a zero of "
     "$L(\\cdot,\\chi^{-1})$ at $1-s$: a zero left of the line would produce one on the right."),
    ("descent", "Why only primitive characters? Changing the modulus multiplies by finitely many Euler factors "
     "$1-\\chi^*(p)p^{-s}$, none of which vanishes for $\\operatorname{Re}s>0$."),
    ("choreography", "So everything reduces to a zero-free half-plane for primitive characters. Fix the losses, "
     "look at the zero $\\beta$, choose $\\theta<\\beta$, then $\\varepsilon$ with $\\tfrac12+9\\varepsilon\\le\\theta$."),
    ("criterion", "The engine: if a positive family's prime sum stays below $Cy^\\theta$ throughout arbitrarily late "
     "windows, no member vanishes right of $\\theta$ — high derivatives act as a spotlight on the windows."),
    ("residues", "Why can zeros not hide? In the Mellin transform each zero becomes a pole with residue "
     "$-S(\\rho)/(\\rho(\\rho-1))$, and $S(\\rho)>0$ because every weight is positive."),
    ("statistic", "The quantity: the ramp-weighted centered prime sum $G$ and its cyclic combinations $G_P$. From here "
     "to RH everything is machine-checked with the window bound as hypothesis: the first verified cut."),
    ("comparison", "Where does the bound come from? A finite character comparison turns a geometric discrepancy into "
     "$G_P(x)\\le x^{1/2+(e_D+e_L+7)\\varepsilon}$; the square root is the balance between $x/m$ and $m$."),
    ("hosts", "It needs arithmetic hosts for each primitive character, which `supplyChi` builds from the cohomological "
     "window."),
    ("family", "And a geometric family: a chain of about $\\sqrt x$ theta lifts with controlled divisibility, slopes and "
     "covolumes, with $e_D=2$, $e_L=0$ fixed in advance. Everything to the right of this point is the second "
     "verified cut: TopG ∧ VWinAt ⇒ RH ∧ GRH."),
    ("cohomology", "The cohomological window: weighted lengths of locally trivial Galois cohomology are bounded on a "
     "whole interval $[Y,Y^2]$; finitely many exceptional twists are avoided by an interval lemma."),
    ("primes", "Auxiliary primes with prescribed congruences and square-root bounds for their quadratic twists, and a "
     "Behrend-set choice of the tower."),
    ("galois", "Underneath: Galois representations attached to automorphic forms over CM fields, built through theta "
     "lifts and quadratic descent."),
    ("inputs", "Finally the seven literature-shaped inputs — theta integrals, local matching, covolumes, local "
     "Langlands, the window — assembled at the decisive call. This is the part read at pinned lines here, and "
     "compiled in the externally reported full build."),
]


GLOSSARY = [
    ("Centered prime sum", "$G(y)=\\sum_{n\\le y}\\Lambda(n)(y/n-1)-y\\log y+(1+\\gamma)y$; its twisted versions $g_\\chi$ add "
     "$y\\,(L'/L)(1,\\chi)$ instead of the main terms."),
    ("Power window", "All $y$ with $Y\\le y\\le Y^{\\lambda}$; the archive uses $\\lambda=3/2$ for the prime sums and "
     "$[Y,Y^2]$ for the cohomology."),
    ("One-sided bound", "An upper bound $G_F(y)\\le Cy^\\theta$ at every point of a window; no lower bound is required."),
    ("Positive family", "A finite family of characters with weights $a_i>0$ (principal member only of modulus one); "
     "residues at common zeros add up."),
    ("Primitive character", "A Dirichlet character at its conductor; every character is induced by a unique primitive one."),
    ("Theta lift", "Transfer of automorphic forms between groups by a theta kernel; the archive chains about $\\sqrt x$ of them."),
    ("Galois row", "`Row0b`: the local–global compatibility package attaching $\\ell$-adic Galois representations to "
     "regular algebraic polarized cuspidal automorphic representations over CM fields."),
    ("Cohomological length", "The $\\mathbb Z_\\ell$-length of the locally trivial part of $H^1$ of a twisted module; "
     "`VWinAt` bounds weighted sums of these lengths."),
    ("Verified cut", "An implication machine-checked against the archive with the remaining inputs as explicit hypotheses."),
    ("Axiom audit", "Lean's list of axioms a declaration depends on; the audits permit only `propext`, "
     "`Classical.choice` and `Quot.sound`."),
    ("Source-read", "A declaration located at pinned source lines and read, but not separately replayed by this audit."),
    ("Pinned link", "A URL into the public mirror at commit `40e56bab`, whose tree is byte-identical to the archive."),
]


def main() -> int:
    model = load("data/model.json")
    facts = load("assets/figures/facts.json")
    scopes = load("data/source/native-scopes.json")
    audit = load("verification/logs/axioms.json")
    dates = {d["number"]: d for d in load("data/announcement_dates.json")["items"]}
    prov = load("data/source/PROVENANCE.json")
    mp = load("data/source/map.json")
    coords, L = layout(model)
    for n in model["nodes"]:
        n["x"], n["y"] = coords[n["id"]]
        n["short"] = short(n["title"], 30)
        decl = n.get("declaration") or ""
        n["decl_short"] = short(".".join(decl.split(".")[-2:]) if decl else n["kind"], 34)
    for t in model["timeline"]:
        d = dates[t["number"]]
        t["date"], t["as_written"] = d["date"], d["as_written"]
    (FIG / "blueprint-graph.svg").write_text(static_graph_svg(model, L), encoding="utf-8")
    evidence = {e["id"]: f'{e.get("kind", "")}: {e.get("scope", "")}' for e in mp["evidence"]}
    data = {"strata": model["strata"], "tiers": model["tiers"], "components": model["components"],
            "interfaces": model["interfaces"], "cuts": model["cuts"], "edges": model["edges"],
            "nodes": [{k: n.get(k) for k in ("id", "component", "section", "kind", "title", "contract", "idea",
                                              "assumptions", "lean_head", "declaration", "module", "url", "excerpt",
                                              "lines", "evidence", "tier", "x", "y", "short", "decl_short")}
                      for n in model["nodes"]],
            "itineraries": model["itineraries"], "timeline": model["timeline"], "layout": L, "evidence": evidence,
            "story": [{"comp": c, "text": t} for c, t in STORY]}
    st = model["status"]
    asof = st["as_of"][:16].replace("T", " ") + " UTC"
    mod_count = re.search(r"all ([\d,]+) original modules", st["external"]).group(1)
    n_decl = sum(1 for n in model["nodes"] if n["kind"] != "motivation")
    n_motiv = len(model["nodes"]) - n_decl
    n_edges = len(model["edges"])
    pills = [
        ("#047857", "✓✓", "One-sided prime windows ⇒ RH", "checked by two kernels"),
        ("#059669", "✓", "TopG ∧ VWinAt ⇒ RH ∧ Dirichlet GRH", "kernel-checked"),
        ("#047857", "✓✓", f"Five endpoints, complete proof ({mod_count} modules)", "accepted by two independent kernels")
        if st["full_proof"]["two_kernels"] else
        ("#64748b", "↗", f"Five endpoints, full replay of {mod_count} modules (Lean + Rust kernel)", "reported externally"),
    ]
    difficulty = ("Its terms belong to the complete proof, which two independent kernels accepted and several "
                  "independent builders replayed (see Verification); in this atlas they are read at their pinned "
                  "source lines, and only some of them were also checked one by one."
                  if st["full_proof"]["two_kernels"] else
                  "Its terms belong to the full replay of the archive reported by an external builder (Lean kernel "
                  "and the Rust kernel NanoDA, standard axioms only); in this atlas they are read at their pinned "
                  "source lines, and the reading project's own replay of the published solution is recorded "
                  "separately (see Verification).")
    pills_html = "".join(f'<span class="pill"><span class="ic" style="background:{c}">{i}</span>{esc(a)}: <b>{esc(b)}</b></span>'
                         for c, i, a, b in pills)
    filt = ['<option value="">Highlight…</option><optgroup label="Strata">']
    filt += [f'<option value="s:{s["id"]}">{esc(s["title"])}</option>' for s in model["strata"]]
    filt += ['</optgroup><optgroup label="Components">']
    filt += [f'<option value="c:{c["id"]}">{c["n"]}. {esc(c["title"])}</option>' for c in model["components"]]
    filt += ['</optgroup><optgroup label="Verification tier">']
    filt += [f'<option value="t:{k}">{esc(v["label"])}</option>' for k, v in model["tiers"].items()]
    filt += ["</optgroup>"]
    tours = "".join(f'<button class="btn light" data-tour="{i}">{esc(t["title"])}</button>'
                    for i, t in enumerate(model["itineraries"]))
    legend = "".join(f'<span><span class="dot" style="background:{s["color"]}"></span>{esc(s["title"])}</span>'
                     for s in model["strata"])
    tier_legend = "".join(f'<span class="tier" style="--tc:{v["color"]}" title="{esc(v["meaning"])}"><i>{esc(v["icon"])}</i>'
                          f'{esc(v["label"])}</span>' for v in model["tiers"].values())
    gloss = "".join(f'<div class="card"><dl style="margin:0"><dt>{esc(a)}</dt><dd>{md(b)}</dd></dl></div>' for a, b in GLOSSARY)
    figs_about = []
    for name in ("hero", "explicit-formula", "strip", "ramp", "spotlight", "balance", "windows", "behrend"):
        svg = (FIG / f"{name}.svg").read_text(encoding="utf-8")
        m = re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.S)
        figs_about.append(f"<li><b>{esc(name)}.</b> {m.group(1) if m else ''}</li>")
    pins = model["pins"]
    css = (ROOT / "atlas" / "src" / "atlas.css").read_text(encoding="utf-8")
    js = (ROOT / "atlas" / "src" / "atlas.js").read_text(encoding="utf-8")
    built = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The architecture of the announced proof of the Riemann hypothesis — an illustrated atlas</title>
<meta name="description" content="An illustrated map and Lean blueprint of Levent Alpöge's announced proof of RH and Dirichlet GRH: {len(model["components"])} components, {len(model["cuts"])} implications checked in isolation, {n_decl} mapped declarations.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<script>window.MathJax={{tex:{{inlineMath:[['$','$']],displayMath:[['$$','$$']]}},options:{{skipHtmlTags:['script','noscript','style','textarea','pre','code']}},chtml:{{scale:0.97}},startup:{{pageReady:()=>MathJax.startup.defaultPageReady().then(()=>window.dispatchEvent(new Event('mathjax-ready')))}}}};</script>
<script>(function(){{var s=document.createElement("script");s.src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js";document.head.appendChild(s);}})();</script>
<style>{css}</style>
</head>
<body>
<header class="hero" id="top">
  <div class="hero-bg" aria-hidden="true">{figure("hero")}</div>
  <div class="hero-content">
    <div class="hero-label">An illustrated atlas · Lean blueprint</div>
    <h1>How the announced proof of the <em>Riemann hypothesis</em> is put together</h1>
    <p class="lead">Levent Alpöge's four-page announcement (20&nbsp;November&nbsp;2026) claims proofs of RH and of GRH for
    Dirichlet characters, formalized in a Lean archive of {mod_count} modules. This atlas maps the argument component by
    component, links every step to pinned Lean source, and marks exactly what has been machine-checked.</p>
    <div class="pills">{pills_html}</div>
    <p class="small" style="color:#94a3b8;margin:-12px 0 22px;max-width:640px">Status recorded by the reading project at
    {esc(asof)}: {esc(st["headline"])}</p>
    <div class="cta"><a class="btn" href="#map-section">The proof in one picture</a><a class="btn ghost" href="#blueprint">Blueprint graph</a>
    <a class="btn ghost" href="#ideas">Illustrated ideas</a><a class="btn ghost" href="#ledger">What is checked</a></div>
  </div>
  <div class="hero-foot">Background: the centered prime sum $(G(y)-\\log 2\\pi)/\\sqrt y$, computed from the primes up to $10^7$ (see “About the images”).</div>
</header>
<nav class="topnav"><div class="wrap"><span class="brand">RH atlas</span>
<a href="#gist">Gist</a><a href="#map-section">Map</a><a href="#blueprint">Blueprint</a><a href="#ideas">Ideas</a>
<a href="#ledger">Verification</a><a href="#lean">Lean</a><a href="#timeline">Timeline</a><a href="#glossary">Glossary</a><a href="#about">Sources</a>
<span class="legend-mini">{legend}</span></div></nav>

<section id="gist"><div class="wrap">
  <div class="kicker">01 · The gist</div><h2 class="section-title">The proof in three sentences</h2>
  <p class="section-lead">The argument has one hard estimate and two well-understood transformations of it. Read the
  three cards from the arithmetic to the destination; every term in them is a component of the map below.</p>
  <div class="three">
    <div class="card arith"><h3>Arithmetic supplies a one-sided bound</h3><p>For every primitive character $\\psi$ and every
    small $\\varepsilon$, build families on which a positive combination of centered prime sums satisfies
    $G_P(x)\\le x^{{1/2+9\\varepsilon}}$ at <em>every</em> point of arbitrarily late windows $[Y,Y^{{3/2}}]$. The tools: chains of
    about $\\sqrt x$ theta lifts, Galois representations attached to automorphic forms, Iwasawa-type bounds for Galois
    cohomology.</p></div>
    <div class="card ana"><h3>Analysis turns the bound into a zero-free half-plane</h3><p>The Mellin transform turns a zero
    $\\rho$ into a pole with residue $-S(\\rho)/(\\rho(\\rho-1))$, $S(\\rho)>0$. High derivatives aimed at the windows would see
    that pole. Choosing $\\theta$ after the zero and $\\varepsilon$ after $\\theta$, no zero survives to the right of $\\tfrac12$.</p></div>
    <div class="card dest"><h3>Reflection delivers the critical line</h3><p>Euler factors pass from primitive to all
    characters, and the functional equations reflect the half-plane onto the line: Mathlib's
    <code>RiemannHypothesis</code> and Dirichlet GRH for every positive modulus.</p></div>
  </div>
  <div class="note"><b>Where the difficulty lives.</b> The analytic engine and the closing deductions are machine-checked
  with the window estimate as an explicit hypothesis (two verified cuts). The estimate itself comes from the arithmetic
  supply. {difficulty}</div>
</div></section>

<section id="map-section" class="alt"><div class="wrap">
  <div class="kicker">02 · The map</div><h2 class="section-title">The proof in one picture</h2>
  <p class="section-lead">Fourteen components in four strata. Information flows down the arithmetic column, across the
  estimate, down the analytic engine and up to the endpoints. Arrows carry the Lean propositions through which the
  components talk. Click a card for its statement, idea, Lean declarations and status; toggle a verified cut to see
  which part has been machine-checked with the rest as a hypothesis.</p>
  <div class="map-toolbar"><button class="btn" id="story-start">▶ Guided tour: from RH backwards</button><span class="label" style="margin-left:10px">Verified cuts:</span>
    <button class="btn light" data-cut="cut-zeta">✓✓ One-sided windows ⇒ RH</button>
    <button class="btn light" data-cut="cut-dirichlet">✓ TopG ∧ VWinAt ⇒ RH ∧ GRH</button>
    <span class="label" style="margin-left:auto">{tier_legend}</span></div>
  <div class="cut-callout" id="cut-callout"></div>
  {map_html(model)}
</div></section>

<section id="blueprint"><div class="wrap">
  <div class="kicker">03 · The blueprint</div><h2 class="section-title">{n_decl} declarations, {n_edges} dependencies, all pinned</h2>
  <p class="section-lead">The reading project's declaration map ({n_decl} Lean declarations and {n_motiv} ideas quoted from the
  announcement), laid out by dependency depth: suppliers on the left, the five exported theorems on the right. Bar colour = stratum, dot = verification tier. Click a declaration for its
  statement in standard mathematics, its Lean head and source excerpt, and links to the pinned lines; drag to pan, scroll
  to zoom. The three tours follow the reading routes of the reading project.</p>
  <div class="bp-tools"><input type="search" id="bp-search" placeholder="Search declarations, e.g. poleData, window, Galois, θ…" aria-label="Search">
    <span class="small muted" id="bp-count"></span><select id="bp-filter" aria-label="Highlight">{"".join(filt)}</select></div>
  <div class="bp-tools"><span class="small muted">Tours:</span>{tours}</div>
  <div class="bp-shell" id="bp-shell">
    <svg id="bp-svg" role="img" aria-label="Blueprint dependency graph"><g id="bp-vp"></g></svg>
    <div class="bp-zoom"><button id="bp-in" aria-label="Zoom in" title="Zoom in">+</button><button id="bp-out" aria-label="Zoom out" title="Zoom out">−</button><button id="bp-home" aria-label="Endpoints" title="Back to the endpoints">⌂</button><button id="bp-fit" aria-label="Fit" title="Show everything">⤢</button></div>
    <div class="bp-help">← dependencies run to the left · drag · scroll · click a box · minimap ↘</div>
    <svg class="bp-mini" id="bp-mini" aria-label="Minimap"></svg>
  </div>
  <div class="tour" id="tour"></div>
</div></section>

<section id="ideas" class="alt"><div class="wrap">
  <div class="kicker">04 · Illustrated ideas</div><h2 class="section-title">Eleven pictures of the argument</h2>
  <p class="section-lead">Amber tags mark figures computed from definitions (every number asserted by the build); grey tags
  mark schematic diagrams; green marks facts also proved in this repository's Lean library.</p>
  {ideas_html(model, facts)}
</div></section>

<section id="ledger"><div class="wrap">
  <div class="kicker">05 · Verification</div><h2 class="section-title">What has been checked, and by whom</h2>
  <p class="section-lead">Status recorded by the reading project at {esc(asof)}. A verified cut is an implication; its
  premise is still a hypothesis. A source-read component has been located and read at pinned lines, not replayed.</p>
  {ledger_html(model, scopes, audit)}
</div></section>

<section id="lean" class="alt"><div class="wrap">
  <div class="kicker">06 · The architecture, compiled</div><h2 class="section-title">A Lean skeleton of the whole argument</h2>
  <p class="section-lead">This repository's Lean library (Lean 4.35.0, no imports) states every component as an explicit
  hypothesis over abstract types and proves only how they compose — the shape of the proof, checked. A toy model with zeros
  on the line shows the hypotheses are jointly satisfiable. It is a map, not a proof of RH.</p>
  {lean_html(model, audit)}
</div></section>

<section id="timeline"><div class="wrap">
  <div class="kicker">07 · From announcement to archive</div><h2 class="section-title">The twenty timeline entries</h2>
  <p class="section-lead">Dates as written on pages 3–4 of the announcement (some mean “from that day on”), coloured by the
  component each entry corresponds to; grey entries are motivation without a matching theorem. Click a dot.</p>
  {timeline_html(model)}
</div></section>

<section id="glossary" class="alt"><div class="wrap">
  <div class="kicker">08 · Glossary</div><h2 class="section-title">Words that carry weight here</h2>
  <div class="gloss">{gloss}</div>
</div></section>

<section id="about"><div class="wrap">
  <div class="kicker">09 · Sources, pins and images</div><h2 class="section-title">Where everything comes from</h2>
  <div class="ideas">
   <div class="card idea"><h3>Pins</h3><ul class="small">
    <li>Archive SHA-256 <code>{esc(pins["archive_sha256"])}</code> (14 parts, {mod_count} modules), Lean <code>{esc(pins["toolchain"])}</code>, Mathlib <code>{esc(pins["mathlib"][:12])}</code>.</li>
    <li>Public mirror <a href="{esc(pins["mirror"])}/tree/{esc(pins["mirror_commit"])}" target="_blank" rel="noopener">{esc(pins["mirror"].split("github.com/")[1])}</a> at <code>{esc(pins["mirror_commit"][:12])}</code>; every Lean link points there.</li>
    <li>Announcement PDF SHA-256 <code>{esc(pins["pdf_sha256"])}</code> — <a href="https://alpo.ge/remark.pdf" target="_blank" rel="noopener">alpo.ge/remark.pdf</a>.</li>
    <li>Reading project (the data of this atlas): <code>{esc(prov["source_project"])}</code> at commit <code>{esc((prov["source_commit"] or "")[:12])}</code>, imported {esc(prov["imported_utc"])}.</li>
   </ul></div>
   <div class="card idea"><h3>Reproduce</h3><pre class="lean">make data      # import + model
make figures   # compute figures, assert facts
make lean      # build the Lean library, axiom audit
make atlas     # this page
make pdf guide book
make check</pre><p class="small muted">Built {esc(built)}. Fonts and MathJax load from a CDN; without a network the page
   still works with system fonts and TeX source for formulas.</p></div>
  </div>
  <h3 style="margin-top:22px">About the images</h3><ul class="small">{"".join(figs_about)}</ul>
</div></section>

<footer><div class="wrap cols">
  <div><b>The architecture of the announced proof of the Riemann hypothesis.</b> An independent reading aid. The original
  announcement and the Lean archive belong to their author; this atlas paraphrases them and links to immutable sources. It
  does not assert that the announced theorem is true.</div>
  <div><a href="../guide/proof-guide.pdf">Guide to the proof (PDF)</a><br><a href="../blueprint/atlas-blueprint.pdf">Blueprint PDF</a><br>
  <!--site-links--><a href="../lean/Atlas/Architecture.lean">Lean skeleton</a><br><a href="../README.md">Status dashboard (README)</a></div>
  <div><a href="#top">Back to top ↑</a></div>
</div></footer>

<div class="drawer-back" id="drawer-back"></div>
<aside class="drawer" id="drawer" aria-hidden="true" aria-label="Details"><div id="drawer-content"></div></aside>
<script id="atlas-data" type="application/json">{json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>{js}</script>
</body>
</html>
"""
    out = ROOT / "atlas" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"atlas: {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.0f} KiB), graph {L['ranks']} layers "
          f"{L['w']}×{L['h']}px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
