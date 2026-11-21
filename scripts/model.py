#!/usr/bin/env python3
"""The component model: one source of truth for the atlas, the book, the vault and the PDF.

    python3 -B scripts/model.py        # validates and writes data/model.json

The model has four layers.

1. STRATA -- the four layers of the argument, each with a validated colour.
2. COMPONENTS -- fourteen mathematical components. Each carries a plain-language gist, a
   precise statement in standard notation (MathJax), an explanation, the pinned Lean
   declarations (immutable URLs into the public mirror of the archive), the verification
   tier, the related announcement entries, and the blueprint nodes it owns.
3. INTERFACES and CUTS -- the propositions through which components talk to each other, and
   the two implications that have been machine-checked with the remaining inputs as explicit
   hypotheses.
4. The 87-node blueprint graph imported from the reading project, with every node assigned to
   exactly one component and given a verification tier computed from its receipts.

All statements are paraphrases of the reading project's chapters and of the archive's source
lines they cite; the numbers come from evidence files, not from memory.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "source"
M = "https://github.com/Deicyde/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/"
MATHLIB_RH = ("https://github.com/leanprover-community/mathlib4/blob/0df444a360eaa60ab8c11dca51a86af692955474/"
              "Mathlib/NumberTheory/LSeries/RiemannZeta.lean#L182-L186")

STRATA = [
    {"id": "arith", "title": "Arithmetic supply", "color": "#c2410c",
     "blurb": "Galois representations, theta lifts and Iwasawa-type cohomology bounds that are meant "
              "to produce the families on which a prime sum is small."},
    {"id": "est", "title": "The estimate", "color": "#7c3aed",
     "blurb": "A finite character comparison turns geometric control of a chain of theta lifts of "
              "length about √x into an upper bound for a weighted prime sum."},
    {"id": "ana", "title": "The analytic engine", "color": "#0891b2",
     "blurb": "A localized Landau oscillation argument converts one-sided bounds on whole power "
              "windows into a zero-free half-plane."},
    {"id": "dest", "title": "The destination", "color": "#e11d48",
     "blurb": "Euler factors, conductors and functional equations turn the half-plane theorem into "
              "the five exported statements, including Mathlib's RiemannHypothesis."},
]

TIERS = {
    "two-kernels": {"label": "Checked by two kernels", "color": "#047857", "icon": "✓✓",
                    "meaning": "Accepted by two independent proof checkers in runs of the reading project: "
                               "a Lean replay or verified-mode comparison, and the Rust kernel NanoDA. The "
                               "ledger names the runs and their receipts."},
    "checked": {"label": "Kernel-checked at the archive pin", "color": "#059669", "icon": "✓",
                "meaning": "Named declarations passed type, transitive-axiom (only propext, "
                           "Classical.choice, Quot.sound) and kernel-replay checks at Lean 4.33.1."},
    "partial": {"label": "Partly checked", "color": "#10b981", "icon": "◐",
                "meaning": "Some of the component's named declarations are kernel-checked; the "
                           "producers of its remaining inputs are source-read."},
    "covered": {"label": "Inside a checked closure", "color": "#34d399", "icon": "⊂",
                "meaning": "Called (directly or transitively) by a kernel-checked declaration, so it "
                           "was elaborated and kernel-checked as part of that closure and its axioms "
                           "are within that declaration's report. For a definition this only means "
                           "that it typechecks: a proposition it defines (for instance VWinAt) can "
                           "still be a hypothesis."},
    "read": {"label": "Source-read", "color": "#4f46e5", "icon": "◇",
             "meaning": "Statement and proof term located at pinned source lines and read; not "
                        "replayed as a named declaration by the reading project's audit. It is part of "
                        "the complete proof, whose replays are listed in the ledger."},
    "reported": {"label": "Full replay reported", "color": "#64748b", "icon": "↗",
                 "meaning": "Checked in a full replay of the archive reported by an external builder; the "
                            "reading project has not (yet) recorded a run of its own for it."},
    "motivation": {"label": "Motivation", "color": "#94a3b8", "icon": "○",
                   "meaning": "A heuristic or historical idea from the announcement; no theorem is "
                              "attached to it."},
}


def L(name: str, path: str, note: str = "") -> dict:
    return {"name": name, "url": M + path if not path.startswith("http") else path, "note": note}


def N(node_id: str, note: str = "", name: str | None = None) -> dict:
    """A Lean entry taken from a blueprint node: its declaration name and pinned URL are filled in by
    build() from data/source/map.json, so that a declaration has one line range everywhere."""
    return {"node": node_id, "name": name, "note": note}


COMPONENTS = [
    # ------------------------------------------------------------------ destination
    {
        "id": "endpoints", "stratum": "dest", "n": 1, "title": "The five endpoints",
        "kicker": "Main.lean",
        "gist": "Ordinary RH in Mathlib's own formulation, and Dirichlet GRH for every character of "
                "every positive modulus.",
        "statement": r"\zeta(s)=0,\ s\notin\{-2,-4,\dots\},\ s\neq1\ \Longrightarrow\ \operatorname{Re}s=\tfrac12;"
                     r"\qquad L(s,\chi)=0,\ 0<\operatorname{Re}s<1\ \Longrightarrow\ \operatorname{Re}s=\tfrac12 .",
        "explanation": [
            "The first export has exactly Mathlib's type `RiemannHypothesis`. The other four state the zeta "
            "zeros in expanded form, nonvanishing of $L(s,\\chi)$ for $\\operatorname{Re}s>\\tfrac12$ away from "
            "the principal pole, and the critical-line conclusion in the open strip for all characters and for "
            "primitive ones.",
            "All five pass through one assertion: the half-plane theorem for every Dirichlet character. "
            "The extension to further $L$-functions mentioned in the announcement has no endpoint in the archive.",
        ],
        "lean": [N("main-rh", "type: RiemannHypothesis (Mathlib)"),
                 N("main-zeta", "the same statement, quantifiers written out"),
                 N("main-right", "half-plane nonvanishing, all characters"),
                 N("main-strip", "critical-strip zeros, all characters"),
                 N("main-prim", "critical-strip zeros, primitive characters"),
                 L("Statements (target types)", "Statements.lean#L3-L16"),
                 L("Mathlib RiemannHypothesis", MATHLIB_RH, "Mathlib 0df444a3")],
        "tier": "reported",      # replaced in build() by what the status record says
        "status": "",            # generated in build() from the status record
        "check": "",             # generated in build()
        "figure": "strip", "timeline": [20],
    },
    {
        "id": "reflection", "stratum": "dest", "n": 2, "title": "Reflection",
        "kicker": "functional equations",
        "gist": "A zero left of the critical line reflects to a zero right of it, so the right half-plane "
                "is all one has to clear.",
        "statement": r"\zeta(s)=2(2\pi)^{-w}\,\Gamma(w)\cos\!\big(\tfrac{\pi w}{2}\big)\,\zeta(w),\quad w=1-s;"
                     r"\qquad \Lambda(s,\chi)=\varepsilon(\chi)\,\Lambda(1-s,\chi^{-1})\ \ (\chi\ \text{primitive}).",
        "explanation": [
            "For zeta, put $w=1-s$ with $\\operatorname{Re}w>\\tfrac12$. The power and Gamma factors do not vanish, "
            "and a zero of the cosine would make $s$ an even integer, i.e. $0$ or a trivial zero. Hence a "
            "nontrivial zero on the left gives a zero on the right.",
            "For a primitive character the completed functional equation sends a strip zero at $s$ to a zero "
            "of $L(\\cdot,\\chi^{-1})$ at $1-s$; the Gamma factors are regular and nonzero for "
            "$0<\\operatorname{Re}s<1$. Taking $\\chi^{-1}$ matters when $\\chi$ is complex.",
        ],
        "lean": [N("rh-right", "reflect a zeta zero"),
                 N("prim-reflect", "transfer a primitive zero to 1 − s"),
                 N("strip", "half-plane ⇒ critical-strip zeros on the line"),
                 N("bundle-zeta", "half-plane ⇒ the zeta statement"),
                 N("gamma", "Gamma factors do not vanish in the strip")],
        "tier": "checked",
        "status": "Claim.strip, Claim.zeta and Formalism.VW.rh_of_right passed type, axiom and kernel checks "
                  "at Lean 4.33.1 (Helios job 26639692).",
        "check": "None for the deduction itself; it is classical and machine-checked.",
        "figure": "strip", "timeline": [],
    },
    {
        "id": "descent", "stratum": "dest", "n": 3, "title": "Conductor descent",
        "kicker": "Euler factors",
        "gist": "An imprimitive character differs from its primitive inducing character by finitely many "
                "Euler factors, none of which vanishes for $\\operatorname{Re}s>0$.",
        "statement": r"L(s,\chi)=L(s,\chi^{*})\prod_{p\mid N}\bigl(1-\chi^{*}(p)p^{-s}\bigr),\qquad "
                     r"\bigl|\chi^{*}(p)p^{-s}\bigr|\le p^{-\sigma}<1\quad(\sigma>0).",
        "explanation": [
            "Primes dividing the conductor have $\\chi^*(p)=0$; for the others the second term of the factor "
            "has modulus less than one. So nonvanishing passes from primitive characters to all characters, "
            "with the single exception of the principal character's pole at $s=1$.",
            "The strict left boundary of the strip matters: $1-2^{-s}$ vanishes on $\\operatorname{Re}s=0$, so "
            "$L(s,\\mathbf 1_2)=(1-2^{-s})\\zeta(s)$ has extra zeros on the imaginary axis.",
        ],
        "lean": [N("imprimitive", "primitive ⇒ all characters"),
                 N("prim-zero", "remove the imprimitive Euler factors"),
                 N("factor", "a removed Euler factor is nonzero")],
        "tier": "checked",
        "status": "UpperTheory.Top.imprimitive passed its type, axiom and defining-module checks in the "
                  "1,421-module Dirichlet closure (Helios job 26647685).",
        "check": "None for the deduction; classical and machine-checked.",
        "figure": None, "timeline": [],
    },
    # ------------------------------------------------------------------ analytic engine
    {
        "id": "statistic", "stratum": "ana", "n": 4, "title": "The centered prime sum",
        "kicker": "what must be bounded",
        "gist": "A ramp-weighted von Mangoldt sum, centered so that the main terms cancel exactly, and its "
                "positive combinations over a cyclic family of characters.",
        "statement": r"G(y)=\sum_{n\le y}\Lambda(n)\Bigl(\frac yn-1\Bigr)-y\log y+(1+\gamma)\,y,\qquad "
                     r"G_P(x)=G(x)+\frac{1}{3o+1}\sum_{\chi\in P\setminus\{1\}}\operatorname{Re} g_\chi(x).",
        "explanation": [
            "Here $g_\\chi(y)=\\sum_{n\\le y}\\Lambda(n)\\chi(n)(y/n-1)+y\\,(L'/L)(1,\\chi)$ for nonprincipal "
            "primitive $\\chi$, and $P$ consists of the primitive characters inducing the cyclic group "
            "generated by a fixed primitive $\\psi$ (order $o$). At the trivial level $G_P=G$.",
            "By the explicit formula $G(y)=\\log 2\\pi-\\sum_\\rho y^\\rho/(\\rho(\\rho-1))+O(y^{-2})$, so under RH "
            "$|G(y)-\\log 2\\pi|\\le(2+\\gamma-\\log 4\\pi)\\sqrt y$. The proof needs much less: an *upper* bound "
            "$G_P(x)\\le x^{1/2+O(\\varepsilon)}$ on whole windows.",
        ],
        "lean": [L("Formalism.Gz", "Formalism/StatementOC.lean#L13-L13"),
                 L("Deduction.G / Gchi (CharFamily)", "Development/AutomorphicArithmetic/DedekindLFunctions/CharFamily.lean#L10-L45"),
                 L("Formalism.HC.Level.Gm", "Formalism/SharpRestriction/RamificationFrobenius/TotientGaloisClasses/ExplicitFormulaErrorOfHostConditions.lean#L38-L38"),
                 L("UpperTheory.Comparison₂.Gz_eq", "Development/AutomorphicArithmetic/PrimitiveCosets/GzEq.lean#L6-L47")],
        "tier": "checked",
        "status": "Gz_eq (Formalism.Gz = An.G = Deduction.G pointwise) passed its checks in a 130-module "
                  "union; the definitions are inside every checked closure below.",
        "check": "None: a definition and a checked normalization identity.",
        "figure": "explicit-formula", "timeline": [5],
    },
    {
        "id": "residues", "stratum": "ana", "n": 5, "title": "Mellin transform and positive residues",
        "kicker": "poleData",
        "gist": "The Mellin transform of a ramp is $n^{-s}/(s(s-1))$; a zero of any family member becomes a pole "
                "whose residue cannot be cancelled, because the weights are positive.",
        "statement": r"\int_1^\infty\Bigl(\frac yn-1\Bigr)_{\!+}y^{-s-1}\,dy=\frac{n^{-s}}{s(s-1)},\qquad "
                     r"\operatorname*{Res}_{s=\rho}=-\frac{S(\rho)}{\rho(\rho-1)},\quad "
                     r"S(\rho)=\tfrac12\sum_i a_i\bigl(m_{\chi_i}(\rho)+m_{\chi_i^{-1}}(\rho)\bigr)>0 .",
        "explanation": [
            "Summing ramps against $\\Lambda(n)\\chi(n)$ produces $-L'/L$; the compensating linear term removes the "
            "pole at $s=1$, so $\\int_1^\\infty G_\\chi(y)y^{-s-1}dy=-[(L'/L)(s,\\chi)-s(L'/L)(1,\\chi)]/(s(s-1))$.",
            "Taking real parts averages $\\chi$ and $\\chi^{-1}$, so every member vanishing at $\\rho$ contributes a "
            "positive multiple of the same complex number. For a real zero $0<\\beta<1$ the residue is even "
            "positive, which lets the one-sided bound exclude exceptional real zeros too.",
        ],
        "lean": [L("MellinRamp", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/MellinRamp.lean#L10-L32"),
                 L("mellinGchiOfNeOne", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/mellinGchiOfNeOne.lean#L116-L125"),
                 L("Deduction.poleData", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/poleData.lean#L248-L259"),
                 L("positivity of S(ρ)", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/poleData.lean#L336-L383")],
        "tier": "checked",
        "status": "Deduction.poleData passed type, axiom and kernel checks (38-module landmark closure, "
                  "Helios job 26639692).",
        "check": "None: an analytic lemma, machine-checked.",
        "figure": "residue", "timeline": [],
    },
    {
        "id": "criterion", "stratum": "ana", "n": 6, "title": "The window criterion",
        "kicker": "localized Landau",
        "gist": "If a positive family's prime sum stays below $Cy^\\theta$ throughout arbitrarily late windows "
                "$[Y,Y^{1+\\delta}]$, none of its $L$-functions vanishes to the right of $\\theta$.",
        "statement": r"\exists C\ \forall Y_0\ \exists Y\ge Y_0\ \forall y\in[Y,Y^{1+\delta}]:\ G_F(y)\le C\,y^{\theta}"
                     r"\ \Longrightarrow\ L(s,\chi_i)\neq0\ \text{ for }\operatorname{Re}s>\theta .",
        "explanation": [
            "With $u=\\log y$ and $g(u)=G_F(e^u)$, the moments $A_k(z)=\\int g(u)\\,\\frac{u^k e^{-\\sigma u}}{k!}"
            "e^{-itu}\\,du$ are $(-1)^k\\Phi^{(k)}(z)/k!$ for the Laplace transform $\\Phi$. The kernel peaks at "
            "$u=k/\\sigma$, so $k=\\lceil(1+\\delta/2)\\sigma U\\rceil$ aims it at the window $[U,(1+\\delta)U]$; the tails "
            "are exponentially small.",
            "The one-sided trick: $|g|+g=2\\max(g,0)\\le 2R$ for any majorant $R\\ge g$, which controls "
            "$|A_k(\\sigma+it)|+\\operatorname{Re}A_k(\\sigma)$. A pole at distance $d$ contributes about $d^{-k}$ while "
            "the window bound gives $e^{\\eta U}r^{-k}$ with $r>d$; since $k\\ge U$ and $\\eta$ is arbitrary, the "
            "pole cannot exist.",
        ],
        "lean": [N("landau", "the criterion (statement)"),
                 N("oscillation", "rule out a pole right of θ"),
                 L("isolation of an offending pole (proof)", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/landauWindow.lean#L83-L116"),
                 L("one-sided moment inequality", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/landauWindowIneq.lean#L57-L99"),
                 L("tail estimate", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/landauTails.lean#L80-L102")],
        "tier": "two-kernels",
        "status": "zeroFree_of_rpow_window passed at the archive pin; its specialization to zeta "
                  "(riemannHypothesis_of_prime_windows) passed a fresh Lean replay over 10,530 modules and "
                  "the Rust kernel NanoDA on 61,697 exported declarations.",
        "check": "None: machine-checked twice.",
        "figure": "spotlight", "timeline": [6],
    },
    {
        "id": "choreography", "stratum": "ana", "n": 7, "title": "The order of choices",
        "kicker": "θ after the zero, ε after θ",
        "gist": "The loss exponents are fixed first; given a zero with $\\beta>\\tfrac12$ choose "
                "$\\theta\\in(\\tfrac12,\\beta)$, then $\\varepsilon$ with $\\tfrac12+9\\varepsilon\\le\\theta$. "
                "No bound at $\\varepsilon=0$ is ever needed.",
        "statement": r"\theta=\tfrac12+\tfrac12\min\bigl(\beta-\tfrac12,\tfrac12\bigr),\qquad "
                     r"\tfrac12+(e_D+e_L+7)\,\varepsilon\le\theta\quad(e_D=2,\ e_L=0).",
        "explanation": [
            "This is where the arithmetic and the analysis meet. The arithmetic must deliver, for every small "
            "$\\varepsilon$, families with $G_P(x)\\le x^{1/2+(e_D+e_L+7)\\varepsilon}$ on arbitrarily late windows "
            "$[Y,Y^{3/2}]$, with $e_D,e_L$ independent of $\\varepsilon$. The families themselves may depend on "
            "$\\varepsilon$.",
            "Applying the criterion at each primitive character's cyclic level gives `ZeroFreeAll`: "
            "$L(s,\\psi)\\neq0$ for $\\operatorname{Re}s>\\tfrac12$ and every primitive $\\psi$.",
        ],
        "lean": [N("window-consumer", "choice of θ and ε after a candidate zero"),
                 N("zero-top", "TopG and hosts ⇒ primitive zero-free half-plane"),
                 N("zero-green", "selects the window width 3/2")],
        "tier": "checked",
        "status": "zeroFreeAll_of_topG passed its checks in the 1,421-module Dirichlet closure.",
        "check": "None for the logic; the premise TopG is the arithmetic input.",
        "figure": "choreography", "timeline": [],
    },
    # ------------------------------------------------------------------ the estimate
    {
        "id": "comparison", "stratum": "est", "n": 8, "title": "The finite character comparison",
        "kicker": "core_gm · ch_core · ch_top",
        "gist": "Finite Fourier orthogonality on a subgroup and an exact main-term identity convert a "
                "geometric discrepancy bound into the prime-sum bound, with exponent $\\tfrac12+(e_D+e_L+7)\\varepsilon$.",
        "statement": r"Q\,\tfrac{\delta}{2}\Bigl(G_\Lambda(x)-\Sigma(x)-4x^{1/2+\varepsilon}\Bigr)\le E+\tfrac{2Q}{x}"
                     r"\quad\Longrightarrow\quad G_\Lambda(x)\le x^{1/2+(e_D+e_L+7)\varepsilon}.",
        "explanation": [
            "The geometric discrepancy contains a cost proportional to $x/m$ and another proportional to $m$. "
            "With $m=x^a$ the larger exponent is $\\max(1-a,a)$, smallest at $a=\\tfrac12$: this is the "
            "square root. The worst of the four budget terms is $4x^{1/2+13\\varepsilon/8}$.",
            "Summing a character over the subgroup annihilates it unless it is trivial there; the survivors "
            "that are not retained ($\\Sigma\\le 4o\\,x^{1/2+\\varepsilon}$) need a separate square-root input "
            "(`EAtH.bdG`). The losses add up to exactly $(e_D+e_L+7)\\varepsilon$.",
        ],
        "lean": [N("core-gm", "from the height discrepancy to the prime sum"),
                 N("ch-core", "average over characters"),
                 L("subgroup identity (in ChCore.lean)", "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/ChCore.lean#L16-L54"),
                 N("ch-top", "bound the discrepancy per index"),
                 N("artin-window", "the estimate on a whole window")],
        "tier": "checked",
        "status": "ch_top, ch_core, core_gm and windowInequality_of_artinInputs passed at the archive pin "
                  "(316 modules), with the comparison hypotheses EAtH and CoreAtH explicit.",
        "check": "The hypotheses: existence of the hosts, frames and witnesses at every scale of the window, "
                 "and the square-root bound for discarded characters.",
        "figure": "balance", "timeline": [14, 16],
    },
    {
        "id": "family", "stratum": "est", "n": 9, "title": "The geometric family and the theta chain",
        "kicker": "topDesWin · RankVal",
        "gist": "A chain of about $\\sqrt x$ theta lifts, with divisibility, slope and covolume control, is "
                "chosen so that both loss exponents are fixed numbers: $e_D=2$, $e_L=0$.",
        "statement": r"\sqrt{x\delta_1}\le m\le2\sqrt{x\delta_1},\ \ \delta_1=x^{-\varepsilon/8}"
                     r"\ \Rightarrow\ m\approx x^{1/2-\varepsilon/16};\qquad "
                     r"\mu(A)\le\mu_{\max}(B)+\log C;\qquad w^2=p\ \Rightarrow\ w\mid W_cV_0-W_0V_c .",
        "explanation": [
            "`TopShape` calls `topDesWin` with $C_{\\rm abs}=2$, $C_0=3$, $e_D=2$, $e_L=0$, which gives the exponent "
            "$\\tfrac12+9\\varepsilon$. `RankVal` fixes the chain length; the announcement's \"length of chain "
            "of theta lifts $\\sqrt X$\" is this parameter.",
            "Three local tools are visible in isolation: the denominators of an iterated kernel clear by "
            "$\\prod_j D_j$ (`ChainInt`); a $2\\times2$ minor is divisible by $w$ when $w^2=p$ "
            "(`key_minor_dvd`); and Bost's slope inequality bounds the slope of an injectively mapped lattice. "
            "The global gain requires these to hold simultaneously on one family.",
        ],
        "lean": [N("family-design", "combine divisibility, slopes and windows"),
                 N("shape", "calls topDesWin with e_D = 2, e_L = 0"),
                 N("rank", "the chain length and the other ranks"),
                 N("minor", "a local source of divisibility"),
                 N("slope", "the lattice slope inequality")],
        "tier": "partial",
        "status": "key_minor_dvd passed in its 509-module closure. topDesWin and the family construction are "
                  "source-read here and included in the externally reported full build.",
        "check": "Nonempty compatible data: follow the witnesses of one geometric family through the "
                 "test-vector grids, linked bundles and definite-side hypotheses.",
        "figure": "chain", "timeline": [1, 2, 8, 9, 10, 13, 15],
    },
    {
        "id": "hosts", "stratum": "est", "n": 10, "title": "Hosts for every character",
        "kicker": "supplyChi",
        "gist": "For each primitive character $\\psi$, the cohomological window produces arithmetic hosts of "
                "width $3/2$ at all large scales of a system of scales.",
        "statement": r"\mathrm{VWinAt}\ \psi\ 401\ \Longrightarrow\ \text{hosts of width }3/2\text{ satisfying }(G_\chi\,\psi).\mathrm{req}.",
        "explanation": [
            "The supplier is applied separately to each character; a common host for all characters would be a "
            "stronger quantifier order and is not needed. The character requirement combines the "
            "cyclotomic-level condition `EAtH` with the cohomological inequality for the host field.",
        ],
        "lean": [N("supply", "VWinAt ψ 401 ⇒ hosts of width 3/2")],
        "tier": "checked",
        "status": "supplyChi passed in the Dirichlet closure, with VWinAt ψ 401 as its hypothesis.",
        "check": "Its premise VWinAt ψ 401, for every primitive ψ.",
        "figure": None, "timeline": [],
    },
    # ------------------------------------------------------------------ arithmetic supply
    {
        "id": "cohomology", "stratum": "arith", "n": 11, "title": "The cohomological window",
        "kicker": "VWinAt ψ 401",
        "gist": "On a whole interval $[Y,Y^2]$, weighted lengths of locally trivial Galois cohomology of "
                "twisted modules are at most $\\sqrt{\\exp(x^{\\varepsilon})}$, uniformly over the relevant fields.",
        "statement": r"\sum_{\ell\in S}\log\ell\sum_{1\le h<\lfloor x^{401}\rfloor}s_{\ell,h}(E)\ \le\ \sqrt{\exp(x^{\varepsilon})}"
                     r"\qquad\text{for all }x\in[Y,Y^2],\ \text{all finite }S,\ \text{all admissible }E .",
        "explanation": [
            "An $\\ell$-adic determinant estimate gives at most $R$ centers; each center accounts for at most one "
            "exceptional twist $h\\le Z$ (ultrametric separation). Finitely many exceptional twists forbid at "
            "most $R$ logarithmic intervals $[a,Ba)$.",
            "A real-variable induction (`window1`) finds $[y,2y]$ avoiding all of them with "
            "$y\\ge U/(2^{R+2}B^R)$; exponentiating gives $[Y,Y^2]$ with $X^{1/J}\\le Y$, $J=4(2B)^R$. The bound on "
            "the sums comes from four counting cases, a Ferrero–Washington input and descent.",
        ],
        "lean": [N("vwin-def", "the cohomological window (definition)"),
                 N("vv", "weighted lengths of local–global kernels (definition)"),
                 L("UpperTheory.V.Win.window1", "Development/AutomorphicArithmetic/AutomorphicVarieties/LayeredIsomorphisms/Window1.lean#L6-L58"),
                 L("UpperTheory.V.Win.window", "Development/AutomorphicArithmetic/AutomorphicVarieties/LayeredIsomorphisms/Window.lean#L7-L43"),
                 N("vwin-row", "the window from the Galois row"),
                 N("four-use", "combine the cohomology counts")],
        "tier": "partial",
        "status": "window1 and window (the interval selection) passed at the archive pin, and so did the "
                  "tower deductions thmBab_of (one record of window constants for every cutoff Ct ≥ 1 from "
                  "LemmaK, FixedIn and TwoIn), aBound_of_isTower (a tower cohomology bound from duality and "
                  "finiteness premises) and thmBab_of_lemmaK, each with its premises explicit. Those premises "
                  "(Poitou–Tate and local Tate duality, local finiteness, Ferrero–Washington, LemmaK) and the "
                  "counting cases are source-read here.",
        "lean_nodes": ["tower-window-constants", "tower-bound-from-rank", "tower-window-from-lemma-k"],
        "check": "Uniform cohomological bound: track finiteness and absolute constants from the four counting "
                 "cases to the finite prime sums on the claimed windows.",
        "figure": "windows", "timeline": [11, 17],
    },
    {
        "id": "primes", "stratum": "arith", "n": 12, "title": "Auxiliary primes and Behrend towers",
        "kicker": "QH.pairEx · hostThickExists",
        "gist": "Two auxiliary primes with prescribed congruences and square-root prime-sum bounds for their "
                "quadratic twists, and an additive-combinatorial (Behrend) choice of the tower.",
        "statement": r"q\equiv3\ (8),\ \ d\equiv7\ (16),\ \ q\mid d+1,\qquad |g_\chi(y)|\le y^{1/2+\varepsilon/2}"
                     r"\ \text{on }[Y,Y^A];\qquad |S|\ge\frac nL\,e^{-C\sqrt{\log n\,\log L}} .",
        "explanation": [
            "With $z=Y^{\\varepsilon/5}$ the primes satisfy $z/2<\\log q\\le z$ and "
            "$z(\\log Y)^2/2<\\log d\\le z(\\log Y)^2$; $d+1$ is divisible by $q$ and by every odd prime up to $z$. "
            "They are chosen sequentially from positive shares of candidates, and may change with $Y$.",
            "Behrend: integer vectors of fixed norm, encoded in a large base, avoid short affine relations "
            "because a line meets a sphere at most twice.",
        ],
        "lean": [L("QH.pairEx", "Development/AutomorphicArithmetic/MeanSquareBounds/pairEx.lean#L112-L169"),
                 L("two successive choices", "Development/AutomorphicArithmetic/MeanSquareBounds/PairExists.lean#L9-L48"),
                 N("behrend", "digit spheres avoid short relations"),
                 L("hostThickExists", "Formalism/FrobeniusOrbits/FrobeniusOrbitsProofs/ThickExists.lean#L181-L187")],
        "tier": "checked",
        "status": "QH.pairEx passed in its 293-module closure; the Behrend landmarks (sphere_rel, noRel_image, "
                  "hostThickExists) passed in the 38-module landmark closure.",
        "check": "How the chosen primes feed the window for a fixed target character.",
        "figure": "behrend", "timeline": [19],
    },
    {
        "id": "galois", "stratum": "arith", "n": 13, "title": "The Galois row",
        "kicker": "Row0b",
        "gist": "For regular algebraic polarized cuspidal $\\pi$ on $\\mathrm{GL}_a$ over a CM field, a continuous "
                "semisimple $\\ell$-adic representation whose Frobenius polynomials match the Satake parameters of $\\pi$.",
        "statement": r"\iota\bigl(\operatorname{charpoly}\rho(\sigma^{-1})\bigr)=\prod_{\alpha\in B_v}\bigl(X-q^{(a-1)/2}\alpha\bigr)"
                     r"\quad\text{for all but finitely many }v,\qquad \rho:G_E\to\mathrm{GL}_a(\overline{\mathbb Q}_\ell).",
        "explanation": [
            "The construction starts from a geometric seed and a high-rank theta lift (`tLiftK`), treats a "
            "restricted case, removes the prescribed polarization by twisting, and descends from infinitely "
            "many quadratic CM extensions $K=E(\\sqrt{-p})$ by index-two patching of trace identities.",
            "The exported row also records local–global compatibility away from $\\ell$ and crystalline/de Rham "
            "comparisons above $\\ell$. A rank-one example shows that the hypotheses are inhabited.",
        ],
        "lean": [N("row-def", "the local–global Galois row (definition)"),
                 N("row-prod", "producer of the row"),
                 N("row-geo", "Galois representations from theta lifting"),
                 N("tlift", "theta-lift existence at high rank (theorem)"),
                 N("tlift-def", "quantifiers of the theta lift (definition)"),
                 N("geo-one", "weight-one geometric realization")],
        "tier": "read",
        "status": "Source-read against 62 passages in 36 modules; included in the externally reported full "
                  "build; not separately replayed by this audit.",
        "check": "Unfold the row, the local normalization convention and the theta-lift producer together; "
                 "check all quantified places, twists and weight restrictions.",
        "figure": "galois", "timeline": [],
    },
    {
        "id": "inputs", "stratum": "arith", "n": 14, "title": "Seven inputs at the decisive call",
        "kicker": "every_character_of_literature_of_vWin",
        "gist": "Unitary-group and local theta packages, agreement of theta integrals, local matching, a "
                "covolume bound, local Langlands parameters and the window: the seven arguments of the "
                "arithmetic theorem.",
        "statement": r"P,\ F,\ h_A,\ h_M,\ h_X,\ h_L,\ h_V\ \Longrightarrow\ \text{nonempty definite-side data}"
                     r"\ +\ \text{Green input}\ \Longrightarrow\ \mathrm{TopG}.",
        "explanation": [
            "`everyCharacter_of_row` fills two fields of the literature record with the same Galois row, adds the "
            "existence of local Langlands parameters, and obtains the cohomological window from the same row. "
            "The next line supplies the row by name, so the half-plane theorem has no explicit premise.",
            "A name such as `published_results_eigen` is where to start verifying what the term establishes, "
            "not an explanation of it.",
        ],
        "lean": [N("from-row", "the half-plane theorem from one row"),
                 N("every", "closed half-plane assembly"),
                 N("lit", "assemble the automorphic inputs"),
                 N("seven", "seven inputs for every character")],
        "tier": "read",
        "status": "Source-read; included in the externally reported full build; not separately replayed by "
                  "this audit.",
        "check": "Source comparison of each named input with the mathematics it is meant to encode.",
        "figure": None, "timeline": [7, 12, 18],
    },
]

# Which blueprint nodes (from the reading project's 87-node map) belong to which component.
OWNERSHIP = {
    "endpoints": ["main-rh", "main-zeta", "main-right", "main-strip", "main-prim", "stmt-zeta", "stmt-right",
                  "stmt-strip", "stmt-prim", "rh-all", "all-chi", "crit-all", "claim-all"],
    "reflection": ["rh-every", "rh-right", "vw-crit", "gamma", "strip", "prim-reflect", "bundle-zeta", "alternate-rh"],
    "descent": ["prim-zero", "factor", "every-green", "imprimitive"],
    "statistic": ["g-m", "window-def", "moment-target", "moment-theorem", "moment-calculation", "moment-laurent",
                  "moment-majorant", "moment-dominated"],
    "residues": ["pole"],
    "criterion": ["form-b", "landau", "landau-lemma", "oscillation"],
    "choreography": ["zero-green", "zero-top", "tied-cyc", "tied", "window-consumer"],
    "comparison": ["prime-bound", "artin-window", "core-gm", "ch-top", "ch-core"],
    "hosts": ["supply"],
    "family": ["goal-shape", "shape-fields", "shape", "family-design", "divin", "vv-sum", "rank", "minor",
               "empty-data", "slope", "paper-chain"],
    "galois": ["row-def", "row-prod", "row-geo", "tlift", "geo-one", "tlift-def"],
    "inputs": ["every", "from-row", "rec", "lit", "open-record", "eigen-package", "theta-package", "hodge-package",
               "local-rec", "local-rec-proj", "green", "linked-two-three", "theta-match", "covol", "seven", "definite"],
    "cohomology": ["vv", "vwin-def", "vwin-row", "window-inputs", "depth-window", "lit-window", "patch-window",
                   "four-produce", "four-use",
                   # added by the reading project at 20:28–20:57 UTC (tower and counting-case declarations)
                   "tower-window-from-lemma-k", "tower-window-constants", "tower-bound-from-rank",
                   "tower-operator-bound", "tower-class-rank", "tower-fixed-growth", "counts-i", "counts-ii-iii",
                   "counts-v", "counts-common-integer", "counts-window", "counts-joint", "counts-height",
                   "counts-pointwise", "counts-inside", "counts-outside"],
    "primes": ["behrend", "paper-behrend"],
}

INTERFACES = [
    {"from": "galois", "to": "inputs", "label": "Row0b (two fields)", "lean": "everyCharacter_of_row",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/MainConclusion.lean#L7-L8"},
    {"from": "galois", "to": "cohomology", "label": "Row0b → window", "lean": "vwin_of_row",
     "url": M + "Development/AutomorphicArithmetic/AutomorphicVarieties/ModularityArgument/ThresholdArguments/DenseThresholdCases/VwinOfRow.lean#L4-L5"},
    {"from": "primes", "to": "cohomology", "label": "prime pairs, tower", "lean": "WinPair / hostThickExists",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/ExistsPageN.lean#L27-L37"},
    {"from": "inputs", "to": "family", "label": "definite-side data",
     "lean": "every_character_of_theta_integrals_local_matching",
     "url": M + "Development/AutomorphicArithmetic/ThetaCorrespondence/ThetaPairLifts/ThirdPlaceSeries/SiegelEisensteinSecondTermHypotheses.lean#L69-L73"},
    {"from": "cohomology", "to": "hosts", "label": "VWinAt ψ 401", "lean": "UpperTheory.Top.VWinAt",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/ExistsPageN.lean#L44-L47"},
    {"from": "family", "to": "comparison", "label": "TopG (e_D = 2, e_L = 0)", "lean": "UpperTheory.Top.TopG",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/ZeroFreeAllOfTopG.lean#L12-L34"},
    {"from": "hosts", "to": "comparison", "label": "hosts, width 3/2", "lean": "UpperTheory.Top.supplyChi",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/SupplyChi.lean#L8-L16"},
    {"from": "comparison", "to": "choreography", "label": "G_P ≤ x^(½+9ε) on windows",
     "lean": "level_gm_le_on_family_scales",
     "url": M + "Development/AutomorphicArithmetic/PrimitiveCosets/LevelGmLeOnFamilyScales.lean#L28-L30"},
    {"from": "statistic", "to": "residues", "label": "Mellin transform", "lean": "MellinRamp",
     "url": M + "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/MellinRamp.lean#L10-L32"},
    {"from": "residues", "to": "criterion", "label": "pole data, S(ρ) > 0", "lean": "Deduction.poleData",
     "url": M + "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/poleData.lean#L248-L259"},
    {"from": "criterion", "to": "choreography", "label": "criterion at each level",
     "lean": "zeroFree_of_rpow_window",
     "url": M + "Development/AutomorphicArithmetic/DedekindLFunctions/LandauTheorems/ZeroFreeOfRpowWindow.lean#L11-L14"},
    {"from": "choreography", "to": "descent", "label": "ZeroFreeAll (primitive)", "lean": "zeroFreeAll_of_topG",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/ZeroFreeAllOfTopG.lean#L26-L34"},
    {"from": "descent", "to": "reflection", "label": "every χ, Re s > ½", "lean": "UpperTheory.Top.imprimitive",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/Imprimitive.lean#L5-L35"},
    {"from": "reflection", "to": "endpoints", "label": "critical line", "lean": "Claim.zeta · Claim.strip",
     "url": M + "Development/AutomorphicArithmetic/CharacterBoxes/ClaimStrip.lean#L59-L100"},
]

CUTS = [
    {
        "id": "cut-zeta", "title": "One-sided prime windows imply RH",
        "lean": "Reading.WindowBridge.riemannHypothesis_of_prime_windows",
        "premise": r"\forall\theta\in(\tfrac12,1)\ \exists C\ \forall Y_0\ \exists Y\ge Y_0\ \forall y\in[Y,Y^{3/2}]:\ G(y)\le C\,y^{\theta}",
        "conclusion": "Mathlib's RiemannHypothesis",
        "components": ["statistic", "residues", "criterion", "reflection"],
        "tier": "two-kernels",
        "evidence": "Fresh Lean replay over 10,530 modules (766,938 constants) and the independent Rust kernel "
                    "NanoDA on 61,697 exported declarations; 31 original modules; axioms propext, "
                    "Classical.choice, Quot.sound.",
        "source": "references/archive-bridges/WindowBridge.lean",
    },
    {
        "id": "cut-dirichlet", "title": "TopG and the cohomological windows imply RH and Dirichlet GRH",
        "lean": "Reading.DirichletBridge.endpoints_of_topG_vWin401",
        "premise": r"\mathrm{TopG}\ \wedge\ \forall\psi\ \text{primitive}:\ \mathrm{VWinAt}\ \psi\ 401",
        "conclusion": "RH ∧ half-plane nonvanishing ∧ critical-strip zeros, for every positive modulus",
        "components": ["hosts", "comparison", "statistic", "residues", "criterion", "choreography", "descent",
                       "reflection"],
        "tier": "checked",
        "evidence": "1,421 original modules at Lean 4.33.1; seven type/axiom reports; six defining modules "
                    "replayed (Helios job 26647685).",
        "source": "references/archive-bridges/DirichletBridge.lean",
    },
]


def load(name: str):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def node_tiers(mp: dict) -> dict[str, str]:
    receipts = {e["id"] for e in mp["evidence"] if e["id"].startswith("helios-")}
    checked = {n["id"] for n in mp["nodes"] if any(ev in receipts for ev in n.get("evidence", []))}
    children = defaultdict(list)
    for e in mp["edges"]:
        if e["relation"] in ("calls", "bundle-field", "statement"):
            children[e["from"]].append(e["to"])
    covered: set[str] = set()
    dq = deque(checked)
    while dq:
        u = dq.popleft()
        for v in children[u]:
            if v not in checked and v not in covered:
                covered.add(v)
                dq.append(v)
    tiers = {}
    for n in mp["nodes"]:
        i = n["id"]
        if i in checked:
            tiers[i] = "checked"
        elif i in covered:
            tiers[i] = "covered"
        elif n["kind"] == "motivation":
            tiers[i] = "motivation"
        else:
            tiers[i] = "read"
    # the five exports: externally reported build
    for i in mp["targets"]:
        if tiers[i] == "read":
            tiers[i] = "reported"
    return tiers


def full_proof(status: dict) -> dict:
    """What the status record says about the complete proof of the five theorems."""
    r = status.get("reported_full_export", {})
    own_rust = bool(r.get("local_rust_accepted"))
    own_compare = bool(r.get("local_verified_combined")) and bool(r.get("local_canonical_statement_phase"))
    stages = [{k: st.get(k) for k in ("stage", "operator", "outcome", "detail", "url") if st.get(k)}
              for st in status.get("full_verification", [])]
    return {"own_rust": own_rust, "own_comparison": own_compare, "two_kernels": own_rust and own_compare,
            "stages": stages}


def build() -> dict:
    mp = load("map.json")
    status = load("status.json")
    fp = full_proof(status)
    timeline = load("timeline.json")
    ids = [n["id"] for n in mp["nodes"]]
    owned = [i for v in OWNERSHIP.values() for i in v]
    assert sorted(owned) == sorted(ids), (set(ids) - set(owned), set(owned) - set(ids))
    assert len(owned) == len(set(owned)) == len(ids)
    comp_ids = [c["id"] for c in COMPONENTS]
    assert set(OWNERSHIP) == set(comp_ids)
    for it in INTERFACES:
        assert it["from"] in comp_ids and it["to"] in comp_ids, it
    owner = {i: c for c, v in OWNERSHIP.items() for i in v}
    tiers = node_tiers(mp)
    if fp["two_kernels"]:
        for i in mp["targets"]:
            tiers[i] = "two-kernels"
    node_src = {n["id"]: n for n in mp["nodes"]}
    for c in COMPONENTS:
        resolved = []
        for l in c["lean"]:
            if "node" in l:
                src = node_src[l["node"]]["source"]
                resolved.append({"name": l["name"] or src.get("declaration") or l["node"], "url": src["url"],
                                 "note": l["note"] or node_src[l["node"]]["title"], "node": l["node"]})
            else:
                resolved.append(l)
        c["lean"] = resolved
        for nid in c.pop("lean_nodes", []):
            src = node_src[nid]["source"]
            c["lean"].append({"name": src.get("declaration") or nid, "url": src["url"],
                              "note": node_src[nid]["title"], "node": nid})
        if c["id"] == "endpoints":
            c["tier"] = "two-kernels" if fp["two_kernels"] else "reported"
            c["status"] = (f'{status["headline"]} {status["external"]} '
                           f'(Status recorded by the reading project at {status["as_of"][:16].replace("T", " ")} UTC.)')
            c["check"] = ("What machine checking cannot settle: that the five Lean statements say what is "
                          "meant (they are compared with an independently written Mathlib challenge), the "
                          "soundness of the checkers and of Mathlib's definitions, and the mathematical "
                          "community's own reading of the argument." if fp["two_kernels"] else
                          "Independent confirmation of the reported full replay: the reading project's own "
                          "kernel replay of the published solution, and the comparison of the five targets "
                          "with an independently written challenge.")
    for c in COMPONENTS:
        c["nodes"] = OWNERSHIP[c["id"]]
        assert c["tier"] in TIERS and c["stratum"] in {s["id"] for s in STRATA}
        node_t = [tiers[i] for i in c["nodes"]]
        c["node_tiers"] = {t: node_t.count(t) for t in sorted(set(node_t))}
    nodes = []
    for n in mp["nodes"]:
        src = n["source"]
        nodes.append({
            "id": n["id"], "component": owner[n["id"]], "section": n["section"], "kind": n["kind"],
            "title": n["title"], "contract": n["contract"], "idea": n["idea"],
            "assumptions": n.get("assumptions", []), "lean_head": n.get("lean_head"),
            "declaration": src.get("declaration"), "module": src.get("module"),
            "url": src.get("url"), "excerpt": src.get("excerpt"), "lines": src.get("lines"),
            "evidence": n.get("evidence", []), "tier": tiers[n["id"]],
        })
    edges = [{"from": e["from"], "to": e["to"], "relation": e["relation"], "token": e.get("token"),
              "line": e.get("line")} for e in mp["edges"]]
    tl = []
    comp_of_item = {k: c["id"] for c in COMPONENTS for k in c["timeline"]}
    for it in timeline["items"]:
        tl.append({"number": it["number"], "page": it["page"], "topic": it["topic"],
                   "relation": it["relation"], "assessment": it["assessment"],
                   "component": comp_of_item.get(it["number"])})
    model = {
        "schema": "riemann-rev-model/1",
        "title": "The architecture of the announced proof of the Riemann hypothesis",
        "pins": {"archive_sha256": mp["archive_sha256"], "pdf_sha256": mp["pdf_sha256"],
                 "mirror": mp["mirror_repository"], "mirror_commit": mp["mirror_commit"],
                 "toolchain": mp["archive_toolchain"], "mathlib": mp["mathlib_commit"]},
        "status": {"headline": status["headline"], "detail": status["detail"], "external": status["external"],
                   "native": status["native"], "as_of": status["as_of"], "job": status["job_id"],
                   "full": status["full"],
                   # links that lead into private places are replaced on import by a neutral token; they are
                   # listed by label only
                   "external_sources": [s for s in status["external_sources"] if s["url"].startswith("http")],
                   "private_sources": [s["label"] for s in status["external_sources"]
                                       if not s["url"].startswith("http")],
                   "independent_window": status["independent_window"], "full_proof": fp},
        "strata": STRATA, "tiers": TIERS, "components": COMPONENTS, "interfaces": INTERFACES, "cuts": CUTS,
        "nodes": nodes, "edges": edges, "itineraries": mp["itineraries"], "audit": mp["audit"],
        "sections": mp["sections"], "timeline": tl,
    }
    return model


def main() -> int:
    model = build()
    out = ROOT / "data" / "model.json"
    out.write_text(json.dumps(model, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    from collections import Counter
    t = Counter(n["tier"] for n in model["nodes"])
    print(f"model: {len(model['components'])} components, {len(model['nodes'])} nodes, "
          f"{len(model['edges'])} edges; node tiers {dict(t)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
