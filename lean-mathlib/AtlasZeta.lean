import Mathlib.NumberTheory.LSeries.RiemannZeta
import Mathlib.NumberTheory.LSeries.Nonvanishing
import Atlas.Architecture

/-!
# The destination layer of the skeleton, instantiated with Mathlib's ζ

`Atlas.Architecture` (in `../lean/`, no imports) states every component of the announced proof as
an explicit hypothesis over abstract types. Here, at the archive's own pins (Lean 4.33.1, Mathlib
`0df444a3`), the abstract plane is instantiated with complex numbers and Mathlib's
`riemannZeta`, restricted to the character of modulus one. We check that

* the skeleton's `RH` for this plane **is** Mathlib's `RiemannHypothesis` (`rh_iff`, by `Iff.rfl`);
* every field of `Reflection` and `Descent` holds for `ζ` (`reflection`, `descent`), from
  Mathlib's functional equation `riemannZeta_one_sub`, the nonvanishing of `ζ` on `Re s ≥ 1`,
  `ζ 0 = -1/2` and the zeros of `cos` and `Γ`;
* hence the skeleton's `rh_of_halfPlane` yields: right-half-plane nonvanishing of `ζ` implies
  Mathlib's RH (`riemannHypothesis_of_right`).

This is the classical last page of the argument, re-checked independently of the archive (whose own
version is `Formalism.VW.rh_of_right`, which uses the same Mathlib lemmas). It says nothing about
the half-plane statement itself.
-/

open Complex

namespace Atlas.Zeta

/-- The abstract plane with `Point = ℂ` and the single character of modulus one, whose
`L`-function is `riemannZeta`. -/
noncomputable def plane : Atlas.Plane where
  Point := ℂ
  Char := Unit
  Zero := fun _ s => riemannZeta s = 0
  Right := fun s => 1 / 2 < s.re
  Line := fun s => s.re = 1 / 2
  Left := fun s => s.re < 1 / 2
  Strip := fun s => 0 < s.re ∧ s.re < 1
  Pole := fun _ s => s = 1
  Primitive := fun _ => True
  prim := id
  inv := id
  refl := fun s => 1 - s
  zeta := ()
  Trivial := fun s => ∃ n : ℕ, s = -2 * (n + 1)
  One := fun s => s = 1

/-- The skeleton's `RH` for this plane is, definitionally, Mathlib's `RiemannHypothesis`. -/
theorem rh_iff : Atlas.RH plane ↔ RiemannHypothesis := Iff.rfl

/-- The half-plane statement of the skeleton, for this plane, in Mathlib's terms. -/
theorem halfPlane_iff :
    Atlas.HalfPlane plane ↔ ∀ s : ℂ, 1 / 2 < s.re → s ≠ 1 → riemannZeta s ≠ 0 :=
  ⟨fun h s hs h1 => h () s hs h1, fun h _ s hs h1 => h s hs h1⟩

/-- A point of positive real part is not a non-positive integer. -/
lemma ne_neg_nat_of_re_pos {s : ℂ} (hs : 0 < s.re) (n : ℕ) : s ≠ -(n : ℂ) := by
  intro h
  have hr := congrArg Complex.re h
  rw [Complex.neg_re, Complex.natCast_re] at hr
  have : (0 : ℝ) ≤ n := n.cast_nonneg
  linarith

/-- In the open strip, a zero of `ζ` reflects to a zero at `1 - s`
(Mathlib's functional equation `riemannZeta_one_sub`). -/
lemma zero_one_sub {s : ℂ} (h0 : 0 < s.re) (h1 : s.re < 1) (hz : riemannZeta s = 0) :
    riemannZeta (1 - s) = 0 := by
  have hs1 : s ≠ 1 := by
    intro h
    rw [h, Complex.one_re] at h1
    exact lt_irrefl _ h1
  rw [riemannZeta_one_sub (ne_neg_nat_of_re_pos h0) hs1, hz, mul_zero]

/-- A zero of `ζ` that is neither trivial nor at `1` lies in the open critical strip. -/
lemma mem_strip_of_zero {s : ℂ} (hz : riemannZeta s = 0)
    (htriv : ¬ ∃ n : ℕ, s = -2 * (n + 1)) (_hone : s ≠ 1) : 0 < s.re ∧ s.re < 1 := by
  have hpi : (Real.pi : ℂ) ≠ 0 := by exact_mod_cast Real.pi_ne_zero
  have hs0 : s ≠ 0 := by
    rintro rfl
    rw [riemannZeta_zero] at hz
    norm_num at hz
  refine ⟨?_, ?_⟩
  · -- For `Re s ≤ 0` reflect: `1 - s` has real part `≥ 1`, where `ζ` and the Gamma factor do not
    -- vanish, so the functional equation forces `cos (π (1 - s) / 2) = 0`: `s` is an even integer.
    by_contra hle
    have hle' : s.re ≤ 0 := not_lt.mp hle
    have hwre : 1 ≤ (1 - s).re := by
      rw [Complex.sub_re, Complex.one_re]
      linarith
    have hwpos : 0 < (1 - s).re := by linarith
    have hw1 : (1 - s) ≠ 1 := by
      intro h
      apply hs0
      linear_combination -h
    have key := riemannZeta_one_sub (ne_neg_nat_of_re_pos hwpos) hw1
    rw [sub_sub_cancel, hz] at key
    have hzw : riemannZeta (1 - s) ≠ 0 := riemannZeta_ne_zero_of_one_le_re hwre
    have h2pi : (2 : ℂ) * (2 * (Real.pi : ℂ)) ^ (-(1 - s)) ≠ 0 :=
      mul_ne_zero two_ne_zero (Complex.cpow_ne_zero_iff.2 (Or.inl (mul_ne_zero two_ne_zero hpi)))
    have hG : Complex.Gamma (1 - s) ≠ 0 := Complex.Gamma_ne_zero_of_re_pos hwpos
    have hcos : Complex.cos ((Real.pi : ℂ) * (1 - s) / 2) = 0 := by
      by_contra hc
      exact (mul_ne_zero (mul_ne_zero (mul_ne_zero h2pi hG) hc) hzw) key.symm
    obtain ⟨k, hk⟩ := Complex.cos_eq_zero_iff.mp hcos
    have h3 : ((1 - s) - (2 * (k : ℂ) + 1)) * (Real.pi : ℂ) = 0 := by
      linear_combination 2 * hk
    have hsk : s = -2 * (k : ℂ) := by
      rcases mul_eq_zero.1 h3 with h | h
      · linear_combination -h
      · exact absurd h hpi
    have hre : s.re = -2 * (k : ℝ) := by
      rw [hsk, Complex.mul_re]
      simp
    -- `Re s ≤ 0` gives `k ≥ 0`, and `s ≠ 0` gives `k ≠ 0`: so `s = -2 (n + 1)` with `n = k - 1`.
    have hk0 : 0 ≤ k := by
      by_contra hneg
      have : (k : ℝ) ≤ -1 := by exact_mod_cast (show k ≤ -1 by omega)
      linarith
    have hk1 : k ≠ 0 := by
      intro hk'
      apply hs0
      rw [hsk, hk']
      simp
    apply htriv
    refine ⟨(k - 1).toNat, ?_⟩
    have hnk : ((k - 1).toNat : ℤ) = k - 1 := Int.toNat_of_nonneg (by omega)
    have h' : (((k - 1).toNat : ℕ) : ℂ) = (k : ℂ) - 1 := by
      have := congrArg (fun m : ℤ => (m : ℂ)) hnk
      push_cast at this
      exact this
    rw [hsk, h']
    ring
  · -- For `Re s ≥ 1`, Mathlib's nonvanishing theorem applies.
    by_contra hge
    exact riemannZeta_ne_zero_of_one_le_re (not_lt.mp hge) hz

/-- Every field of the skeleton's `Reflection` holds for `ζ`. -/
theorem reflection : Atlas.Reflection plane where
  trichotomy := fun (s : ℂ) => by
    rcases lt_trichotomy s.re (1 / 2) with h | h | h
    · exact Or.inl h
    · exact Or.inr (Or.inl h)
    · exact Or.inr (Or.inr h)
  refl_strip := fun (s : ℂ) (hs : 0 < s.re ∧ s.re < 1) => by
    show 0 < (1 - s).re ∧ (1 - s).re < 1
    rw [Complex.sub_re, Complex.one_re]
    exact ⟨by linarith [hs.2], by linarith [hs.1]⟩
  refl_right := fun (s : ℂ) _ (hl : s.re < 1 / 2) => by
    show 1 / 2 < (1 - s).re
    rw [Complex.sub_re, Complex.one_re]
    linarith
  functional_equation := fun _ (s : ℂ) _ (hs : 0 < s.re ∧ s.re < 1) (hz : riemannZeta s = 0) =>
    zero_one_sub hs.1 hs.2 hz
  strip_no_pole := fun _ (s : ℂ) (hs : 0 < s.re ∧ s.re < 1) (h : s = 1) => by
    have h2 : s.re < 1 := hs.2
    rw [h, Complex.one_re] at h2
    exact lt_irrefl _ h2
  zeta_primitive := trivial
  zeta_inv := rfl
  zeta_strip := fun (s : ℂ) (hz : riemannZeta s = 0) htriv hone => mem_strip_of_zero hz htriv hone

/-- Descent is trivial for a single primitive character. -/
theorem descent : Atlas.Descent plane where
  prim_primitive := fun _ => trivial
  euler_right := fun _ _ _ _ hz => hz
  euler_strip := fun _ _ _ hz => hz

/-- **The destination layer, checked against Mathlib**: right-half-plane nonvanishing of `ζ`
implies Mathlib's `RiemannHypothesis`, by the skeleton's `rh_of_halfPlane` instantiated with `ζ`. -/
theorem riemannHypothesis_of_right
    (h : ∀ s : ℂ, 1 / 2 < s.re → s ≠ 1 → riemannZeta s ≠ 0) : RiemannHypothesis :=
  rh_iff.mp (Atlas.rh_of_halfPlane reflection descent (halfPlane_iff.mpr h))

end Atlas.Zeta

#print axioms Atlas.Zeta.rh_iff
#print axioms Atlas.Zeta.reflection
#print axioms Atlas.Zeta.riemannHypothesis_of_right
