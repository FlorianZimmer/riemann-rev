/-!
# The architecture of the announced proof, as a checked skeleton

This file is a **map**, not a proof of the Riemann hypothesis. Each mathematical component of
Levent Alpöge's Lean archive (pinned at commit `40e56bab` of the public mirror) appears here as an
explicit hypothesis over abstract types, and the theorems prove only how the components
compose. The skeleton is checked by Lean 4.35.0 with no imports; `Atlas/Audit.lean` prints the
axioms of every theorem.

Reading guide (archive declaration ↦ field or theorem below):

* `Formalism.VW.rh_of_right`, `Claim.prim_reflect`, `Claim.strip`, `Claim.zeta` ↦ the fields of
  `Reflection` and the theorems `strip_of_halfPlane`, `rh_of_halfPlane`;
* `UpperTheory.Top.imprimitive`, `Claim.prim_zero` ↦ `Descent` and `halfPlane_of_primitive`;
* `Deduction.zeroFree_of_rpow_window` (with `poleData`, `landau_window`) ↦ `Engine.criterion`;
* `Formalism.HC.level_of_tiedWin` (θ after the zero, ε after θ) ↦ `Supply.choose`;
* `UpperTheory.Top.TopG` with `supplyChi`, `VWinAt ψ 401` and `core_gm` ↦ `Supply.windows`;
* `UpperTheory.Top.zeroFreeAll_of_topG` ↦ `primitiveHalfPlane_of_supply`;
* `Reading.DirichletBridge.endpoints_of_topG_vWin401` ↦ `endpoints_of_supply`;
* `Reading.WindowBridge.riemannHypothesis_of_prime_windows` ↦ `rh_of_prime_windows`.

The toy model at the end shows that the hypotheses are jointly satisfiable with zeros present,
all of them on the line. The skeleton is therefore not vacuous; it says nothing about which model
is the real one.
-/

namespace Atlas

/-! ## The objects -/

/-- The objects the endpoints talk about. `Point` stands for complex numbers `s`, `Char` for
Dirichlet characters of all positive moduli, `Zero χ s` for `L(s, χ) = 0`. Lean's `L`-functions
are total functions, so a value exists even at the principal pole. -/
structure Plane where
  Point : Type
  Char : Type
  Zero : Char → Point → Prop
  /-- `Re s > 1/2`. -/
  Right : Point → Prop
  /-- `Re s = 1/2`. -/
  Line : Point → Prop
  /-- `Re s < 1/2`. -/
  Left : Point → Prop
  /-- `0 < Re s < 1`. -/
  Strip : Point → Prop
  /-- `(χ, s) = (1_N, 1)`: the principal character at the pole. -/
  Pole : Char → Point → Prop
  Primitive : Char → Prop
  /-- The primitive character inducing `χ`. -/
  prim : Char → Char
  /-- `χ ↦ χ⁻¹`. -/
  inv : Char → Char
  /-- `s ↦ 1 - s`. -/
  refl : Point → Point
  /-- The character of modulus one, whose `L`-function is `ζ`. -/
  zeta : Char
  /-- `s ∈ {-2, -4, -6, …}`. -/
  Trivial : Point → Prop
  /-- `s = 1`. -/
  One : Point → Prop

variable (P : Plane)

/-- Mathlib's `RiemannHypothesis`, transported to the abstract plane: every zero of `ζ` that is
neither trivial nor at `s = 1` lies on the critical line. -/
def RH : Prop :=
  ∀ s, P.Zero P.zeta s → ¬ P.Trivial s → ¬ P.One s → P.Line s

/-- The half-plane theorem (archive: `DirichletLNonvanishingRightOfHalf`): no `L(s, χ)` vanishes
for `Re s > 1/2`, the principal pole excepted. -/
def HalfPlane : Prop :=
  ∀ χ s, P.Right s → ¬ P.Pole χ s → ¬ P.Zero χ s

/-- The primitive half-plane statement (archive: `ZeroFreeAll`). It quantifies over primitive
characters only and has no pole exception, because Lean's totalized `ζ` takes a nonzero value
at `s = 1`. -/
def PrimitiveHalfPlane : Prop :=
  ∀ ψ s, P.Primitive ψ → P.Right s → ¬ P.Zero ψ s

/-- Dirichlet GRH in the open strip (archive: `DirichletLZerosOnLine`). -/
def StripGRH : Prop :=
  ∀ χ s, P.Strip s → P.Zero χ s → P.Line s

/-! ## The destination: reflection and conductor descent -/

/-- Classical facts used by the closing deductions. All of them are proved in the archive and
were kernel-checked at Lean 4.33.1 by the reading project's audit (`rh_of_right`, `Claim.strip`,
`Claim.zeta`). -/
structure Reflection where
  /-- Every point is left of, on, or right of the critical line. -/
  trichotomy : ∀ s, P.Left s ∨ P.Line s ∨ P.Right s
  /-- `s ↦ 1 - s` maps the open strip to itself. -/
  refl_strip : ∀ s, P.Strip s → P.Strip (P.refl s)
  /-- `s ↦ 1 - s` sends the left half of the strip to the right half. -/
  refl_right : ∀ s, P.Strip s → P.Left s → P.Right (P.refl s)
  /-- The completed functional equation of a primitive character reflects a strip zero of `χ`
  to a zero of `χ⁻¹` at `1 - s`; the Gamma factors do not vanish in the strip. -/
  functional_equation :
    ∀ ψ s, P.Primitive ψ → P.Strip s → P.Zero ψ s → P.Zero (P.inv ψ) (P.refl s)
  /-- The open strip contains no pole. -/
  strip_no_pole : ∀ χ s, P.Strip s → ¬ P.Pole χ s
  /-- `ζ` is the `L`-function of the primitive character of modulus one, which is its own inverse. -/
  zeta_primitive : P.Primitive P.zeta
  zeta_inv : P.inv P.zeta = P.zeta
  /-- Outside the open strip `ζ` has only the trivial zeros (functional equation) and no zeros
  for `Re s ≥ 1` (in Mathlib); `s = 1` is the pole. Stated constructively: a zeta zero that is
  neither trivial nor at `1` lies in the strip. -/
  zeta_strip : ∀ s, P.Zero P.zeta s → ¬ P.Trivial s → ¬ P.One s → P.Strip s

/-- Conductor descent (archive: `Claim.prim_zero`, `UpperTheory.Top.imprimitive`):
`L(s,χ) = L(s,χ*) ∏_{p ∣ N} (1 - χ*(p) p^{-s})`, and no removed factor vanishes for `Re s > 0`
because `|χ*(p) p^{-s}| ≤ p^{-Re s} < 1`. -/
structure Descent where
  prim_primitive : ∀ χ, P.Primitive (P.prim χ)
  /-- A zero of `L(s, χ)` with `Re s > 1/2`, away from the pole, is a zero of `L(s, χ*)`. -/
  euler_right : ∀ χ s, P.Right s → ¬ P.Pole χ s → P.Zero χ s → P.Zero (P.prim χ) s
  /-- The same in the open strip. -/
  euler_strip : ∀ χ s, P.Strip s → P.Zero χ s → P.Zero (P.prim χ) s

variable {P}

/-- Primitive half-plane ⇒ half-plane for every character (mirrors `UpperTheory.Top.imprimitive`). -/
theorem halfPlane_of_primitive (D : Descent P) (h : PrimitiveHalfPlane P) : HalfPlane P :=
  fun χ s hs hpole hz => h (P.prim χ) s (D.prim_primitive χ) hs (D.euler_right χ s hs hpole hz)

/-- Half-plane ⇒ Dirichlet GRH in the strip (mirrors `Claim.strip`). A zero left of the line
descends to the primitive character and reflects to a zero of its inverse on the right; a zero
on the right contradicts the hypothesis directly. -/
theorem strip_of_halfPlane (R : Reflection P) (D : Descent P) (h : HalfPlane P) : StripGRH P := by
  intro χ s hstrip hz
  rcases R.trichotomy s with hl | hline | hr
  · have hp : P.Zero (P.prim χ) s := D.euler_strip χ s hstrip hz
    have hzr : P.Zero (P.inv (P.prim χ)) (P.refl s) :=
      R.functional_equation _ s (D.prim_primitive χ) hstrip hp
    exact absurd hzr
      (h _ _ (R.refl_right s hstrip hl) (R.strip_no_pole _ _ (R.refl_strip s hstrip)))
  · exact hline
  · exact absurd hz (h χ s hr (R.strip_no_pole χ s hstrip))

/-- Half-plane ⇒ RH (mirrors `Claim.zeta`): a nontrivial zeta zero lies in the strip, where the
previous theorem applies at modulus one. -/
theorem rh_of_halfPlane (R : Reflection P) (D : Descent P) (h : HalfPlane P) : RH P :=
  fun s hz htriv hone => strip_of_halfPlane R D h P.zeta s (R.zeta_strip s hz htriv hone) hz

/-! ## The analytic engine and the arithmetic supply -/

/-- The analytic engine over an abstract scale of exponents.

* `Exp` carries the exponents `θ`, with `Le θ θ'` for `θ ≤ θ'`;
* `RightOf s θ` is `Re s > θ`;
* `Family` carries the finite positive character families and `Mem χ F` is membership;
* `Windows F θ` is the one-sided estimate: one constant `C` and arbitrarily late windows
  `[Y, Y^(3/2)]` on which the family's centered prime sum is at most `C·y^θ` at every point. -/
structure Engine (P : Plane) where
  Exp : Type
  Le : Exp → Exp → Prop
  RightOf : P.Point → Exp → Prop
  Family : Type
  Mem : P.Char → Family → Prop
  Windows : Family → Exp → Prop
  /-- A weaker exponent is easier to satisfy. -/
  windows_mono : ∀ F θ θ', Windows F θ → Le θ θ' → Windows F θ'
  /-- `Deduction.zeroFree_of_rpow_window`: a one-sided bound on arbitrarily late power windows
  forbids zeros of every member to the right of the exponent. Proof in the archive: the Mellin
  transform of the ramp, positive residues (`poleData`), and high derivatives aimed at the
  windows (`landau_window`). -/
  criterion : ∀ F θ, Windows F θ → ∀ χ, Mem χ F → ∀ s, RightOf s θ → ¬ P.Zero χ s

/-- The arithmetic supply, in the form consumed by `zeroFreeAll_of_topG`. For each primitive `ψ`
and each admissible small `ε` there is a family containing `ψ` whose prime sum satisfies the
window bound with exponent `loss ε = 1/2 + (e_D + e_L + 7)·ε`, where `e_D = 2`, `e_L = 0` were
fixed **before** `ε`. In the archive this is produced from `TopG` and `VWinAt ψ 401` (through
`supplyChi`, `core_gm` and `topDesWin`). It is the one non-classical input. -/
structure Supply (P : Plane) (E : Engine P) where
  Eps : Type
  Small : Eps → Prop
  loss : Eps → E.Exp
  family : P.Char → Eps → E.Family
  mem_family : ∀ ψ ε, E.Mem ψ (family ψ ε)
  windows : ∀ ψ ε, P.Primitive ψ → Small ε → E.Windows (family ψ ε) (loss ε)
  /-- θ after the zero, ε after θ (`level_of_tiedWin`): for `Re s > 1/2` take
  `θ = 1/2 + min(Re s - 1/2, 1/2)/2`, so that `Re s > θ`, then a small `ε` with `loss ε ≤ θ`.
  This is possible because `loss ε → 1/2` as `ε → 0` with the losses fixed. -/
  choose : ∀ s, P.Right s → ∃ θ, E.RightOf s θ ∧ ∃ ε, Small ε ∧ E.Le (loss ε) θ

/-- The supply and the engine give the primitive half-plane (mirrors `zeroFreeAll_of_topG`). -/
theorem primitiveHalfPlane_of_supply (E : Engine P) (S : Supply P E) : PrimitiveHalfPlane P := by
  intro ψ s hψ hs hz
  obtain ⟨θ, hθ, ε, hε, hle⟩ := S.choose s hs
  exact E.criterion (S.family ψ ε) θ (E.windows_mono _ _ _ (S.windows ψ ε hψ hε) hle)
    ψ (S.mem_family ψ ε) s hθ hz

/-- **The second verified cut** (mirrors `Reading.DirichletBridge.endpoints_of_topG_vWin401`,
kernel-checked against the archive in a 1,421-module closure): the arithmetic supply implies
RH, the half-plane theorem for every character and Dirichlet GRH in the strip. -/
theorem endpoints_of_supply (R : Reflection P) (D : Descent P) (E : Engine P) (S : Supply P E) :
    RH P ∧ HalfPlane P ∧ StripGRH P :=
  have hhalf := halfPlane_of_primitive D (primitiveHalfPlane_of_supply E S)
  ⟨rh_of_halfPlane R D hhalf, hhalf, strip_of_halfPlane R D hhalf⟩

/-- **The first verified cut** (mirrors `Reading.WindowBridge.riemannHypothesis_of_prime_windows`,
checked by the Lean kernel and by the Rust kernel NanoDA): one family `{ζ}`, and the window bound
at every exponent `θ ∈ (1/2, 1)`, give RH. No other character and no descent is involved. -/
theorem rh_of_prime_windows (R : Reflection P) (E : Engine P) (Fz : E.Family)
    (hmem : E.Mem P.zeta Fz) (Above : E.Exp → Prop)
    (choose : ∀ s, P.Right s → ∃ θ, Above θ ∧ E.RightOf s θ)
    (h : ∀ θ, Above θ → E.Windows Fz θ) : RH P := by
  intro s hz htriv hone
  have hstrip : P.Strip s := R.zeta_strip s hz htriv hone
  rcases R.trichotomy s with hl | hline | hr
  · have hz' : P.Zero (P.inv P.zeta) (P.refl s) :=
      R.functional_equation _ s R.zeta_primitive hstrip hz
    rw [R.zeta_inv] at hz'
    obtain ⟨θ, hθ, hright⟩ := choose (P.refl s) (R.refl_right s hstrip hl)
    exact absurd hz' (E.criterion Fz θ (h θ hθ) P.zeta hmem _ hright)
  · exact hline
  · obtain ⟨θ, hθ, hright⟩ := choose s hr
    exact absurd hz (E.criterion Fz θ (h θ hθ) P.zeta hmem s hright)

/-! ## The whole architecture in one record -/

/-- The four layers of the argument bundled together. The first three are classical or
machine-checked; the fourth, `supply`, is where the arithmetic lives. -/
structure Architecture where
  plane : Plane
  reflection : Reflection plane
  descent : Descent plane
  engine : Engine plane
  supply : Supply plane engine

/-- The five endpoints, as conjunctions on the abstract plane. -/
theorem Architecture.endpoints (A : Architecture) :
    RH A.plane ∧ HalfPlane A.plane ∧ StripGRH A.plane :=
  endpoints_of_supply A.reflection A.descent A.engine A.supply

/-! ## The hypotheses are satisfiable, with zeros present

A toy plane with three kinds of points and zeros exactly on the line satisfies every field. It
shows that the skeleton is not vacuous; it does not, of course, say anything about `ζ`. -/

/-- Left of, on, or right of the critical line. -/
inductive Side where
  | left | line | right

/-- `s ↦ 1 - s` on the three sides. -/
def Side.refl : Side → Side
  | .left => .right
  | .line => .line
  | .right => .left

/-- A plane with one character, whose zeros are exactly the points on the line. -/
def toyPlane : Plane where
  Point := Side
  Char := Unit
  Zero := fun _ s => s = .line
  Right := fun s => s = .right
  Line := fun s => s = .line
  Left := fun s => s = .left
  Strip := fun _ => True
  Pole := fun _ _ => False
  Primitive := fun _ => True
  prim := id
  inv := id
  refl := Side.refl
  zeta := ()
  Trivial := fun _ => False
  One := fun _ => False

theorem side_ne_right_line : Side.right ≠ Side.line := fun h => Side.noConfusion h

/-- Every field of the architecture holds in the toy plane. -/
def toyArchitecture : Architecture where
  plane := toyPlane
  reflection :=
    { trichotomy := fun s => match s with
        | .left => Or.inl rfl
        | .line => Or.inr (Or.inl rfl)
        | .right => Or.inr (Or.inr rfl)
      refl_strip := fun _ _ => True.intro
      refl_right := fun s _ hl => by
        change s = Side.left at hl
        subst hl
        rfl
      functional_equation := fun _ s _ _ hz => by
        change s = Side.line at hz
        subst hz
        rfl
      strip_no_pole := fun _ _ _ h => h
      zeta_primitive := True.intro
      zeta_inv := rfl
      zeta_strip := fun _ _ _ _ => True.intro }
  descent :=
    { prim_primitive := fun _ => True.intro
      euler_right := fun _ _ _ _ hz => hz
      euler_strip := fun _ _ _ hz => hz }
  engine :=
    { Exp := Unit
      Le := fun _ _ => True
      RightOf := fun s _ => s = Side.right
      Family := Unit
      Mem := fun _ _ => True
      Windows := fun _ _ => True
      windows_mono := fun _ _ _ _ _ => True.intro
      criterion := fun _ _ _ _ _ s hr hz => by
        change s = Side.right at hr
        change s = Side.line at hz
        exact side_ne_right_line (hr.symm.trans hz) }
  supply :=
    { Eps := Unit
      Small := fun _ => True
      loss := fun _ => ()
      family := fun _ _ => ()
      mem_family := fun _ _ => True.intro
      windows := fun _ _ _ _ => True.intro
      choose := fun _ hs => ⟨(), hs, (), True.intro, True.intro⟩ }

/-- In the toy plane, the conclusion of the skeleton holds and there is a zero (on the line). -/
example : RH toyArchitecture.plane ∧ toyArchitecture.plane.Zero () Side.line :=
  ⟨(Architecture.endpoints toyArchitecture).1, rfl⟩

end Atlas
