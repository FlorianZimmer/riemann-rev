"""Data access and MyST formatting for the notebooks of the riemann-rev Jupyter Book.

The book never types a number by hand. Every quantity on its pages is read at build time from

* ``data/model.json``               -- the component model (``scripts/model.py``);
* ``assets/figures/facts.json``     -- the numbers the figures show (``scripts/build_figures.py``);
* ``verification/logs/axioms.json`` -- the axiom audit of this repository's Lean library;
* ``data/source/*.json``            -- evidence imported from the reading project (``PROVENANCE.json``);
* ``data/announcement_dates.json``  -- the dates of the twenty announcement entries;

or recomputed with ``scripts/rhlib.py``. This module only reads those files and formats them as
MyST Markdown (rendered by MyST-NB with ``nb_render_markdown_format = myst``). Headings are never
generated: section structure lives in the page sources, generated blocks only fill sections.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

sys.dont_write_bytecode = True

BOOK = Path(__file__).resolve().parents[1]
ROOT = BOOK.parent
FIGURES = ROOT / "assets" / "figures"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import svg as tokens  # noqa: E402  -- the design tokens of all figures (no dependencies)

GLUE_PREFIX = "application/papermill.record/"


# --------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------
def _load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def model() -> dict:
    return _load("data/model.json")


@lru_cache(maxsize=None)
def facts() -> dict:
    return _load("assets/figures/facts.json")


@lru_cache(maxsize=None)
def axioms() -> dict:
    return _load("verification/logs/axioms.json")


@lru_cache(maxsize=None)
def scopes() -> list:
    return _load("data/source/native-scopes.json")


@lru_cache(maxsize=None)
def provenance() -> dict:
    return _load("data/source/PROVENANCE.json")


@lru_cache(maxsize=None)
def archive_sources() -> dict:
    return _load("data/source/sources.json")


@lru_cache(maxsize=None)
def status_record() -> dict:
    return _load("data/source/status.json")


@lru_cache(maxsize=None)
def dates() -> dict:
    return {it["number"]: it for it in _load("data/announcement_dates.json")["items"]}


# --------------------------------------------------------------------------------------
# Look-ups
# --------------------------------------------------------------------------------------
def comps(stratum: str | None = None) -> list[dict]:
    cs = sorted(model()["components"], key=lambda c: c["n"])
    return [c for c in cs if stratum is None or c["stratum"] == stratum]


def comp(cid: str) -> dict:
    return next(c for c in model()["components"] if c["id"] == cid)


def stratum(sid: str) -> dict:
    return next(s for s in model()["strata"] if s["id"] == sid)


def node(nid: str) -> dict:
    return next(n for n in model()["nodes"] if n["id"] == nid)


def cut(cut_id: str) -> dict:
    return next(k for k in model()["cuts"] if k["id"] == cut_id)


def tier(t: str) -> dict:
    return model()["tiers"][t]


TIER_ORDER = ["two-kernels", "checked", "partial", "covered", "read", "reported", "motivation"]
STRATUM_ORDER = ["dest", "ana", "est", "arith"]   # the order of the book's chapters


def as_of(iso: str | None = None) -> str:
    """'20 November 2026, 19:02 UTC' for the status record's time stamp."""
    dt = datetime.fromisoformat(iso or model()["status"]["as_of"])
    return f"{dt.day} {dt:%B %Y, %H:%M} UTC"


def entry_date(n: int, short: bool = True) -> str:
    d = dates()[n]
    dt = datetime.fromisoformat(d["date"])
    s = f"{dt.day} {dt:%b}" if short else f"{dt.day} {dt:%B %Y}"
    return s + (" onward" if d.get("from_on") else "")


# --------------------------------------------------------------------------------------
# Notebook plumbing
# --------------------------------------------------------------------------------------
def glue(name: str, value) -> None:
    """Store ``value`` for ``{glue:text}`name``` without displaying it (as ``myst_nb.glue``;
    reimplemented because the execution kernel does not have MyST-NB installed)."""
    import IPython
    from IPython.display import display
    bundle, meta = IPython.core.formatters.format_display_data(value)
    meta["scrapbook"] = dict(name=name, mime_prefix=GLUE_PREFIX)
    display({GLUE_PREFIX + k: v for k, v in bundle.items()}, raw=True, metadata=meta)


def show(text: str) -> None:
    """Display MyST Markdown as a cell output."""
    from IPython.display import Markdown, display
    display(Markdown(text))


def companion(name: str) -> Path | None:
    """The synced companion file in book/_static, or None if pending."""
    p = {"atlas": BOOK / "_static" / "atlas" / "index.html",
         "blueprint": BOOK / "_static" / "blueprint" / "atlas-blueprint.pdf"}[name]
    return p if p.is_file() else None


def atlas_link(fragment: str, text: str = "Open in the interactive atlas ↗") -> str:
    if companion("atlas") is None:
        return '<span class="pending">pending: atlas</span>'
    return f'<a class="atlas-link" href="_static/atlas/index.html#{fragment}">{html.escape(text)}</a>'


# --------------------------------------------------------------------------------------
# Escaping and small formatting helpers
# --------------------------------------------------------------------------------------
_SPAN = re.compile(r"(\$[^$]+\$|`[^`]+`)")


def esc(text: str, table: bool = False, markdown: bool = False) -> str:
    """Make model text safe for MyST: keep $math$ and `code` spans, escape the rest.

    Plain-text fields (titles, contracts, statuses) have ``*`` escaped; the model's Markdown fields
    (``gist``, ``explanation``) keep their emphasis (``markdown=True``)."""
    out = []
    for i, part in enumerate(_SPAN.split(text or "")):
        if i % 2:
            if table:
                part = part.replace("|", r"\vert " if part.startswith("$") else r"\|")
        else:
            part = part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if not markdown:
                part = part.replace("*", r"\*")
            if table:
                part = part.replace("|", r"\|")
        out.append(part)
    return "".join(out)


def _lin(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(hexcolor: str) -> float:
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ink_on(bg: str) -> str:
    """White or the ink token, whichever has the higher WCAG contrast on ``bg``."""
    lb, li = _lum(bg), _lum(tokens.INK)
    white = 1.05 / (lb + 0.05)
    dark = (lb + 0.05) / (li + 0.05)
    return "#ffffff" if white >= dark else tokens.INK


def badge(text: str, color: str, cls: str, title: str | None = None) -> str:
    t = f' title="{html.escape(title, quote=True)}"' if title else ""
    return (f'<span class="rr-badge {cls}" style="background:{color};color:{ink_on(color)}"{t}>'
            f'{html.escape(text)}</span>')


# Short tier labels for table cells (the full label and its meaning stay in the tooltip).
SHORT_TIER = {"two-kernels": "two kernels", "checked": "kernel-checked", "partial": "partly checked",
              "covered": "in checked closure", "read": "source-read", "reported": "replay reported",
              "motivation": "motivation"}


def tier_badge(t: str, short: bool = False) -> str:
    T = tier(t)
    assert set(SHORT_TIER) == set(model()["tiers"]), "SHORT_TIER out of date with the model"
    text = f"{T['icon']} {SHORT_TIER[t] if short else T['label']}"
    return badge(text, T["color"], f"tier tier-{t}" + (" short" if short else ""),
                 f"{T['label']}: {T['meaning']}")


def stratum_badge(sid: str, short: bool = False) -> str:
    S = stratum(sid)
    text = S["title"]
    if short:
        text = re.sub(r"^The ", "", text)
        text = text[0].lower() + text[1:]
    return badge(text, S["color"], f"stratum stratum-{sid}" + (" short" if short else ""),
                 f"{S['title']}: {S['blurb']}")


def display_math(tex: str, width: int = 80) -> str:
    """A model statement as display math, one formula per line (split at \\qquad and, for long
    lines, before the main implication), so that it fits the text column."""
    lines = []
    for part in re.split(r"\\qquad", tex):
        part = part.strip()
        if len(part) > width and "\\Longrightarrow" in part:
            a, b = part.split("\\Longrightarrow", 1)
            a = re.sub(r"(\\quad|\\ |\s)+$", "", a)
            b = re.sub(r"^(\\quad|\\ |\s)+", "", b)
            lines += [a, "\\Longrightarrow\\ " + b]
        elif part:
            lines.append(part)
    if len(lines) == 1:
        return f"$$\n{lines[0]}\n$$"
    return "$$\n\\begin{gathered}\n" + " \\\\\n".join(lines) + "\n\\end{gathered}\n$$"


_IDENT = re.compile(r"^([A-Za-z_][\w.'₀-₉⁻¹]*)(\s+\(.+\))?$")


def lean_name(name: str) -> str:
    """`Ident` (comment) for declaration-like names, escaped text otherwise."""
    m = _IDENT.match(name)
    if m:
        return f"`{m.group(1)}`" + (" " + esc(m.group(2).strip(), table=True) if m.group(2) else "")
    return esc(name, table=True)


def code(s: str) -> str:
    return f"`{s}`"


def fence_for(text: str, char: str = "`") -> str:
    runs = re.findall(re.escape(char) + "+", text or "")
    return char * max(3, max((len(r) for r in runs), default=0) + 1)


# --------------------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------------------
def svg_meta(name: str) -> tuple[str, str]:
    s = (FIGURES / f"{name}.svg").read_text(encoding="utf-8")
    t = re.search(r"<title[^>]*>(.*?)</title>", s, re.S)
    d = re.search(r"<desc[^>]*>(.*?)</desc>", s, re.S)
    return (html.unescape(t.group(1)) if t else name, html.unescape(d.group(1)) if d else "")


def figure_md(name: str, label: str, width: str = "100%", figclass: str | None = None) -> str:
    title, desc = svg_meta(name)
    opts = [f":name: {label}", f":width: {width}", f":alt: {title}"]
    if figclass:
        opts.append(f":figclass: {figclass}")
    caption = f"**{esc(title)}.** {esc(desc)}"
    return "```{figure} ../assets/figures/" + name + ".svg\n" + "\n".join(opts) + "\n\n" + caption + "\n```"


# --------------------------------------------------------------------------------------
# Component cards
# --------------------------------------------------------------------------------------
def lean_table(rows: list[dict]) -> str:
    if not any(r.get("note") for r in rows):
        out = ["| Lean declarations (archive, pinned at the mirror commit) |", "|---|"]
        out += [f"| [{lean_name(r['name'])}]({r['url']}) |" for r in rows]
        return "\n".join(out)
    out = ["| Lean declaration (archive, pinned at the mirror commit) | Note |", "|---|---|"]
    for r in rows:
        out.append(f"| [{lean_name(r['name'])}]({r['url']}) | {esc(r.get('note') or '', table=True)} |")
    return "\n".join(out)


def _node_tier_summary(c: dict) -> str:
    counts = c["node_tiers"]
    keys = sorted(counts, key=TIER_ORDER.index)
    return ", ".join(f"{counts[k]} {tier(k)['label'].lower()}" for k in keys)


def card(cid: str) -> str:
    """The generated part of a component section (everything except the heading)."""
    c = comp(cid)
    m = model()
    parts = [f"{stratum_badge(c['stratum'])} {tier_badge(c['tier'])} "
             f"<code class=\"kicker\">{html.escape(c['kicker'])}</code>",
             f":::{{admonition}} The gist\n:class: gist\n{esc(c['gist'], markdown=True)}\n:::",
             "**Statement** (paraphrase of the archive's Lean statements in standard notation):",
             display_math(c["statement"])]
    parts += [esc(p, markdown=True) for p in c["explanation"]]
    if c.get("figure"):
        parts.append(figure_md(c["figure"], f"fig-{cid}"))
    parts.append(lean_table(c["lean"]))
    parts.append(f"**Verification.** {tier_badge(c['tier'])} {esc(tier(c['tier'])['meaning'])}")
    parts.append(f"*Status in the imported record ({as_of()}).* {esc(c['status'])}")
    parts.append(f"**What remains to check.** {esc(c['check'])}")
    parts.append(f"**Blueprint.** {len(c['nodes'])} of the reading project's declarations belong to this "
                 f"component ({_node_tier_summary(c)}); see {{ref}}`bp-{cid}`.")
    inc = [i for i in m["interfaces"] if i["to"] == cid]
    out = [i for i in m["interfaces"] if i["from"] == cid]
    if inc:
        parts.append("**Receives** " + "; ".join(
            f"from {{ref}}`comp-{i['from']}`: {esc(i['label'])} ({code(i['lean'])})" for i in inc) + ".")
    if out:
        parts.append("**Delivers** " + "; ".join(
            f"to {{ref}}`comp-{i['to']}`: {esc(i['label'])} ({code(i['lean'])})" for i in out) + ".")
    ks = [k for k in m["cuts"] if cid in k["components"]]
    if ks:
        parts.append("**Verified cuts through this component:** " + " and ".join(
            f"{{ref}}`{k['id']}`" for k in ks) + ".")
    else:
        parts.append("**Verified cuts:** this component lies outside both machine-checked implications "
                     "(see {ref}`cuts`).")
    if c["timeline"]:
        tl = {t["number"]: t for t in m["timeline"]}
        parts.append("**Announcement entries:** " + "; ".join(
            f"{n} ({entry_date(n)}: {esc(tl[n]['topic'])})" for n in c["timeline"]) + " — see {doc}`timeline`.")
    parts.append(atlas_link(f"c-{cid}", "Open this component in the interactive atlas ↗"))
    return "\n\n".join(parts)


# --------------------------------------------------------------------------------------
# Tables for the overview pages
# --------------------------------------------------------------------------------------
def components_table() -> str:
    out = ["| # | Component | Gist | Stratum · tier |", "|--:|---|---|---|"]
    for c in comps():
        out.append(f"| {c['n']} | {{ref}}`{esc(c['title'], True)} <comp-{c['id']}>` "
                   f"| {esc(c['gist'], table=True, markdown=True)} "
                   f"| {stratum_badge(c['stratum'], short=True)}<br>{tier_badge(c['tier'], short=True)} |")
    return "\n".join(out)


def interfaces_table() -> str:
    out = ["| From | To | What passes | Lean |", "|---|---|---|---|"]
    for i in model()["interfaces"]:
        a, b = comp(i["from"]), comp(i["to"])
        out.append(f"| {a['n']}. {{ref}}`{esc(a['title'], True)} <comp-{a['id']}>` "
                   f"| {b['n']}. {{ref}}`{esc(b['title'], True)} <comp-{b['id']}>` "
                   f"| {esc(i['label'], True)} | {code(i['lean'])} |")
    return "\n".join(out)


def strata_table() -> str:
    out = ["| Stratum | Components |", "|---|---|"]
    for sid in STRATUM_ORDER:
        s = stratum(sid)
        cs = "<br>".join(f"{c['n']}. {{ref}}`{esc(c['title'], True)} <comp-{c['id']}>`" for c in comps(sid))
        out.append(f"| {stratum_badge(sid, short=True)}<br>{esc(s['blurb'], True)} | {cs} |")
    return "\n".join(out)


def tiers_table() -> str:
    m = model()
    out = ["| Tier | Meaning | Components | Blueprint nodes |", "|---|---|--:|--:|"]
    for t in TIER_ORDER:
        nc = sum(1 for c in m["components"] if c["tier"] == t)
        nn = sum(1 for n in m["nodes"] if n["tier"] == t)
        out.append(f"| {tier_badge(t, short=True)}<br><small>{esc(tier(t)['label'], True)}</small> "
                   f"| {esc(tier(t)['meaning'], True)} | {nc} | {nn} |")
    return "\n".join(out)


def cut_md(cut_id: str) -> str:
    k = cut(cut_id)
    names = ", ".join(f"{comp(c)['n']}. {{ref}}`{esc(comp(c)['title'])} <comp-{c}>`"
                      for c in sorted(k["components"], key=lambda c: comp(c)["n"]))
    return "\n\n".join([
        f"{tier_badge(k['tier'])} Lean theorem {code(k['lean'])} (source quoted in {{ref}}`lean-bridges`).",
        "**Premise** — an explicit hypothesis of the checked theorem, *not* something the check establishes:",
        display_math(k["premise"]),
        f"**Conclusion.** {esc(k['conclusion'])}.",
        f"**Components the implication runs through.** {names}.",
        f"**Evidence.** {esc(k['evidence'])}",
        atlas_link(cut_id, "Show this cut on the atlas map ↗"),
    ])


def status_box() -> str:
    st = model()["status"]
    links = " · ".join(f"[{esc(s['label'])}]({s['url']})" for s in st["external_sources"])
    rec = status_record().get("external_time")
    when = f" (external reports as recorded: {esc(rec)})" if rec else ""
    return f""":::{{admonition}} Status — imported record of {as_of()}
:class: status-box

**The announcement is a claim; this book reports records and does not itself assert that the theorem
is true.** The five exported theorems carry the tier *{tier(comp('endpoints')['tier'])['label'].lower()}*:
{esc(tier(comp('endpoints')['tier'])['meaning'])} The reading project's native checks of named
declarations, and this repository's own checks, establish *implications* whose premises are explicit.
The tiers used on every page are explained in {{doc}}`verification`.

*Headline of the reading project's status record:* “{esc(st['headline'])}”

*Checked natively by the reading project:* {esc(st['native'])}

*External reports, as summarized by the reading project{when}:* {esc(st['external'])}
Sources: {links}
:::"""


# --------------------------------------------------------------------------------------
# Blueprint
# --------------------------------------------------------------------------------------
def node_table(cid: str) -> str:
    out = ["| Node | Declaration | Contract | Tier |", "|---|---|---|---|"]
    for nid in comp(cid)["nodes"]:
        n = node(nid)
        decl = (f"[{code(n['declaration'])}]({n['url']})" if n["declaration"]
                else f"[announcement, p. {n['url'].rsplit('=', 1)[-1]}]({n['url']})")
        out.append(f"| **{esc(n['title'], True)}**<br><small>{esc(n['kind'], True)} · {code(nid)}</small> "
                   f"| {decl} | {esc(n['contract'], True)} | {tier_badge(n['tier'], short=True)} |")
    return "\n".join(out)


def node_excerpts(cid: str) -> str:
    """A dropdown with the Lean heads/excerpts of a component's nodes, printed from the model."""
    blocks = []
    nodes = [node(nid) for nid in comp(cid)["nodes"]]
    with_src = [n for n in nodes if n["excerpt"]]
    for n in with_src:
        f = fence_for(n["excerpt"])
        lines = n["lines"] or ["?", "?"]
        blocks.append(f"**{esc(n['title'])}** — [{code(n['declaration'])}]({n['url']}), "
                      f"`{n['module']}`, lines {lines[0]}–{lines[1]}. *Idea:* {esc(n['idea'])}\n\n"
                      f"{f}lean4\n{n['excerpt']}\n{f}")
    if not blocks:
        return ""
    body = "\n\n".join(blocks)
    colon = fence_for(body, ":")
    colon = colon if len(colon) > 3 else "::::"
    return (f"{colon}{{dropdown}} Lean source of these {len(with_src)} declarations "
            f"(excerpts printed from data/model.json)\n:icon: code\n\n{body}\n{colon}")


def itinerary_md(it: dict) -> str:
    lines = [f"*{esc(it['question'])}*", ""]
    for k, nid in enumerate(it["nodes"], 1):
        n = node(nid)
        c = comp(n["component"])
        lines.append(f"{k}. **{esc(n['title'])}** — [{code(n['declaration'])}]({n['url']}) "
                     f"{tier_badge(n['tier'], short=True)} · {esc(n['contract'])} "
                     f"(component {c['n']}, {{ref}}`{esc(c['title'])} <comp-{c['id']}>`)")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Plots
# --------------------------------------------------------------------------------------
PALETTE = {
    "arith": tokens.ARITH, "est": tokens.EST, "ana": tokens.ANA, "dest": tokens.DEST,
    "num": tokens.NUM, "accent": tokens.ACCENT, "ok": tokens.OK, "ok2": tokens.OK2,
    "read": tokens.READ, "motiv": tokens.MOTIV, "ink": tokens.INK, "text": tokens.TEXT,
    "muted": tokens.MUTED, "faint": tokens.FAINT, "grid": tokens.GRID,
}


def plot_style() -> None:
    """Matplotlib in the atlas palette; inline figures as SVG with live text."""
    import matplotlib as mpl
    try:
        from IPython import get_ipython
        ip = get_ipython()
        if ip is not None:
            ip.run_line_magic("config", "InlineBackend.figure_formats = ['svg']")
    except Exception:  # pragma: no cover - outside IPython
        pass
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    # an explicit list (not the generic family) enables per-glyph fallback to DejaVu Sans,
    # which has the tier icons; only installed families are named, so findfont stays silent
    families = [f for f in ("Inter", "Helvetica Neue", "Helvetica", "Arial") if f in have][:1] + ["DejaVu Sans"]
    mpl.rcParams.update({
        "svg.fonttype": "none", "svg.hashsalt": "riemann-rev",
        "font.family": families,
        "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "semibold", "axes.labelsize": 10,
        "axes.edgecolor": tokens.FAINT, "axes.labelcolor": tokens.TEXT, "axes.titlecolor": tokens.INK,
        "xtick.color": tokens.MUTED, "ytick.color": tokens.MUTED, "text.color": tokens.TEXT,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": tokens.GRID, "grid.linewidth": 0.8,
        "legend.frameon": False, "legend.fontsize": 9,
        "figure.figsize": (9.0, 3.6), "figure.dpi": 100, "figure.facecolor": "white",
        "lines.linewidth": 1.6,
    })


def envelope(xs, ys, x0: float, x1: float, cols: int):
    """Min/max of ys in ``cols`` equal bins of [x0, x1]: faithful downsampling for plots."""
    import numpy as np
    idx = np.clip(((xs - x0) / (x1 - x0) * cols).astype(int), 0, cols - 1)
    lo = np.full(cols, np.inf)
    hi = np.full(cols, -np.inf)
    np.minimum.at(lo, idx, ys)
    np.maximum.at(hi, idx, ys)
    centers = x0 + (np.arange(cols) + 0.5) / cols * (x1 - x0)
    ok = np.isfinite(lo)
    return centers[ok], lo[ok], hi[ok]


def md_table(header: list[str], rows: list[list], align: str | None = None) -> str:
    """A Markdown table from plain values (cells are escaped)."""
    align = align or "|".join("---" for _ in header)
    out = ["| " + " | ".join(header) + " |", "|" + align + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# Verification scopes (data/source/native-scopes.json)
# --------------------------------------------------------------------------------------
def scope(sid: str) -> dict:
    return next(s for s in scopes() if s["id"] == sid)


def scope_md(sid: str) -> str:
    """One native verification scope of the reading project, as a compact block."""
    s = scope(sid)
    decls = "<br>".join(f"{code(d['name'])} — axioms: "
                        + (", ".join(code(a) for a in sorted(d["axioms"])) if d["axioms"] else "none")
                        for d in s["declarations"])
    rows = [["Authority", esc(s["authority"], True)],
            ["Toolchain", f"Lean {esc(s['lean_version'], True)}"],
            ["Original archive modules in the closure",
             f"{s['original_project_module_count']:,} ({s['additional_original_project_modules']:,} "
             f"not already counted in earlier scopes)"],
            ["Hypotheses supplied", esc(s["assumption"], True)],
            ["Conclusion", esc(s["conclusion"], True)],
            ["Declarations checked", decls],
            ["Receipt (in the reading project)", code(s["receipt_file"])]]
    return f"**{esc(s['title'])}**\n\n" + md_table(["", ""], rows, align="---|---")


def scope_totals() -> dict:
    """Counts over all scopes: distinct named original results, reading deductions and statement
    comparisons (``Reading.Reference.*``) checked at the archive's toolchain, the sum of newly counted
    original modules, and the teaching declarations (Lean 4.35.0)."""
    native = [s for s in scopes() if s["lean_version"] != "4.35.0"]
    names = {d["name"] for s in native for d in s["declarations"]}
    return {"original": sorted(n for n in names if not n.startswith("Reading.")),
            "reading_deductions": sorted(n for n in names if n.startswith("Reading.")
                                         and not n.startswith("Reading.Reference.")),
            "statement_checks": sorted(n for n in names if n.startswith("Reading.Reference.")),
            "modules": sum(s["additional_original_project_modules"] for s in scopes()),
            "teaching": [d["name"] for s in scopes() if s["lean_version"] == "4.35.0" for d in s["declarations"]],
            "scopes": len(scopes())}
