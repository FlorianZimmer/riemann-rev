"""A tiny SVG writer with the atlas design tokens (no dependencies).

All figures of the atlas, the book, the vault and the PDF share these tokens:

* text ink ``INK``/``TEXT``/``MUTED``, hairline grid ``GRID``;
* the four strata of the proof (validated colour-blind-safe palette):
  arithmetic supply ``ARITH``, the estimate ``EST``, the analytic engine ``ANA``,
  the destination ``DEST``;
* verification status: kernel-checked ``OK`` (two kernels ``OK2``), source-read ``READ``,
  motivation ``MOTIV``;
* computations (owner's tokens): numerics ``NUM`` (amber), formal proof ``FORMAL`` (green),
  accent ``ACCENT`` (indigo).
"""
from __future__ import annotations

from html import escape

INK = "#0f172a"
TEXT = "#1e293b"
MUTED = "#64748b"
FAINT = "#94a3b8"
GRID = "#e2e8f0"
SURFACE = "#ffffff"
SURFACE_ALT = "#f8fafc"
NIGHT = "#0b1020"

ARITH = "#c2410c"
EST = "#7c3aed"
ANA = "#0891b2"
DEST = "#e11d48"

OK = "#059669"
OK2 = "#047857"
READ = "#4f46e5"
MOTIV = "#94a3b8"

NUM = "#d97706"
FORMAL = "#059669"
ACCENT = "#4f46e5"

STRATA = {"arith": ARITH, "est": EST, "ana": ANA, "dest": DEST}
SANS = "Inter, 'Helvetica Neue', Helvetica, Arial, system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
SERIF = "'STIX Two Text', 'Cambria Math', 'Times New Roman', serif"


def f(x: float) -> str:
    """Compact number formatting for coordinates."""
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class SVG:
    def __init__(self, w: int, h: int, title: str, desc: str, bg: str | None = SURFACE):
        self.w, self.h = w, h
        self.parts: list[str] = []
        self.defs: list[str] = []
        self.title, self.desc, self.bg = title, desc, bg

    # primitives ---------------------------------------------------------------------
    def add(self, s: str) -> None:
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke="none", sw=1.0, rx=0, opacity=1.0, extra=""):
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(rx)}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}" opacity="{f(opacity)}" {extra}/>')

    def line(self, x1, y1, x2, y2, stroke=GRID, sw=1.0, dash=None, opacity=1.0, extra=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{stroke}" '
                 f'stroke-width="{f(sw)}" opacity="{f(opacity)}" stroke-linecap="round"{d} {extra}/>')

    def path(self, d, stroke=INK, sw=2.0, fill="none", opacity=1.0, dash=None, extra=""):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{f(sw)}" '
                 f'stroke-linejoin="round" stroke-linecap="round" opacity="{f(opacity)}"{da} {extra}/>')

    def circle(self, cx, cy, r, fill=INK, stroke="none", sw=1.0, opacity=1.0, extra=""):
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{f(sw)}" opacity="{f(opacity)}" {extra}/>')

    def text(self, x, y, s, size=13, fill=TEXT, anchor="start", weight=400, family=SANS,
             italic=False, opacity=1.0, extra=""):
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text xml:space="preserve" x="{f(x)}" y="{f(y)}" font-family="{family}" font-size="{f(size)}" '
                 f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" opacity="{f(opacity)}"'
                 f'{st} {extra}>{escape(s)}</text>')

    def rich(self, x, y, spans, size=13, fill=TEXT, anchor="start", family=SANS, weight=400):
        """spans: list of (text, dict(style)) with keys italic/sub/sup/weight/fill/family."""
        out = [f'<text xml:space="preserve" x="{f(x)}" y="{f(y)}" font-family="{family}" font-size="{f(size)}" '
               f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">']
        for t, st in spans:
            attrs = []
            if st.get("italic"):
                attrs.append('font-style="italic"')
            if st.get("weight"):
                attrs.append(f'font-weight="{st["weight"]}"')
            if st.get("fill"):
                attrs.append(f'fill="{st["fill"]}"')
            if st.get("family"):
                attrs.append(f'font-family="{st["family"]}"')
            if st.get("sub"):
                attrs.append(f'baseline-shift="sub" font-size="{f(size * 0.72)}"')
            if st.get("sup"):
                attrs.append(f'baseline-shift="super" font-size="{f(size * 0.72)}"')
            out.append(f'<tspan {" ".join(attrs)}>{escape(t)}</tspan>')
        out.append("</text>")
        self.add("".join(out))

    def arrow_marker(self, mid: str, color: str, size: float = 7.0) -> str:
        self.defs.append(
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="{f(size)}" '
            f'markerHeight="{f(size)}" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
            f'fill="{color}"/></marker>')
        return f"url(#{mid})"

    def render(self) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-labelledby="t d">'
                f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>')
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        bg = f'<rect width="100%" height="100%" fill="{self.bg}"/>' if self.bg else ""
        return head + defs + bg + "".join(self.parts) + "</svg>\n"


class Axes:
    """Linear (or pre-transformed) data -> pixel mapping inside a plot rectangle."""

    def __init__(self, x0, y0, w, h, xlim, ylim):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xlim, self.ylim = xlim, ylim

    def X(self, x):
        a, b = self.xlim
        return self.x0 + (x - a) / (b - a) * self.w

    def Y(self, y):
        a, b = self.ylim
        return self.y0 + self.h - (y - a) / (b - a) * self.h

    def polyline(self, xs, ys) -> str:
        pts = [f"{f(self.X(x))},{f(self.Y(y))}" for x, y in zip(xs, ys)]
        return "M" + " L".join(pts)
