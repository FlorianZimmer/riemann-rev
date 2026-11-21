/-!
# Ultrametric separation: one exceptional twist per centre

In the cohomological window (`UpperTheory.V.Win`, files `Near1.lean` and `Exc.lean` of the
archive) an integer twist `1 ≤ h ≤ Z` is *exceptional* for an `ℓ`-adic centre `s` when
`|h - s|_ℓ < ℓ^{-k}` with `k = ⌊log_ℓ Z⌋`, that is when `ℓ^{k+1} ∣ h - s`. Since `ℓ^{k+1} > Z`,
two exceptional twists for the same centre coincide. Hence there are at most `R` exceptional
twists in total, however large `Z` is, and finitely many logarithmic intervals to avoid.

This file proves the integer core of that argument with no imports.
-/

namespace Atlas.Separation

/-- Two integers in `[1, Z]` that are congruent modulo some `m > Z` are equal. -/
theorem eq_of_dvd_sub {a b m Z : Int} (hm : Z < m) (ha1 : 1 ≤ a) (haZ : a ≤ Z)
    (hb1 : 1 ≤ b) (hbZ : b ≤ Z) (h : m ∣ a - b) : a = b := by
  obtain ⟨c, hc⟩ := h
  have hm0 : 0 ≤ m := by omega
  rcases Int.lt_trichotomy c 0 with hneg | hzero | hpos
  · have hle : m * c ≤ m * (-1) := Int.mul_le_mul_of_nonneg_left (by omega) hm0
    generalize m * c = t at hc hle
    omega
  · subst hzero
    rw [Int.mul_zero] at hc
    omega
  · have hle : m * 1 ≤ m * c := Int.mul_le_mul_of_nonneg_left (by omega) hm0
    generalize m * c = t at hc hle
    omega

/-- Two twists in `[1, Z]` that are both `m`-adically close to the same centre `s`, with `m > Z`,
coincide: each centre accounts for at most one exceptional twist. -/
theorem at_most_one_per_centre {a b s m Z : Int} (hm : Z < m)
    (ha1 : 1 ≤ a) (haZ : a ≤ Z) (hb1 : 1 ≤ b) (hbZ : b ≤ Z)
    (hsa : m ∣ a - s) (hsb : m ∣ b - s) : a = b := by
  obtain ⟨c₁, h₁⟩ := hsa
  obtain ⟨c₂, h₂⟩ := hsb
  refine eq_of_dvd_sub hm ha1 haZ hb1 hbZ ⟨c₁ - c₂, ?_⟩
  rw [Int.mul_sub]
  generalize m * c₁ = t₁ at h₁ ⊢
  generalize m * c₂ = t₂ at h₂ ⊢
  omega

/-- The example of the reading guide: `ℓ = 3`, `Z = 80`, `k = 3`, centre `1`. Proximity strictly
below `3^{-3}` means `81 ∣ h - 1`, which leaves only `h = 1`. -/
example (h : Int) (h1 : 1 ≤ h) (hZ : h ≤ 80) (hd : (81 : Int) ∣ h - 1) : h = 1 :=
  at_most_one_per_centre (by decide) h1 hZ (by decide) (by decide) hd ⟨0, by decide⟩

/-- With `≤` instead of `<`, the condition would only be `27 ∣ h - 1`, and `28` and `55` would
also qualify: the strict inequality matters. -/
example : (27 : Int) ∣ 28 - 1 ∧ (27 : Int) ∣ 55 - 1 := ⟨⟨1, by decide⟩, ⟨2, by decide⟩⟩

end Atlas.Separation
