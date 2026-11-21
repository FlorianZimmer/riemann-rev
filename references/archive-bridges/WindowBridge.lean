import Development.AutomorphicArithmetic.DedekindLFunctions.LandauTheorems.ZeroFreeOfRpowWindow
import Formalism.GammaFactorNonvanishing.RhOfRight

noncomputable section

namespace Reading.WindowBridge

/-- The constant may depend on the exponent. A chosen window must work at every real point. -/
def OneSidedWindows (g : ℝ → ℝ) : Prop :=
  ∀ θ : ℝ, 1 / 2 < θ → θ < 1 → ∃ C : ℝ,
    ∀ Y₀ : ℝ, ∃ Y : ℝ, Y₀ ≤ Y ∧
      ∀ y ∈ Set.Icc Y (Y ^ (3 / 2 : ℝ)), g y ≤ C * y ^ θ

/-- The family has one index, the character modulo one and a positive coefficient of one. -/
def zetaFamily : Deduction.CharFamily where
  ι := Unit
  fin := inferInstance
  N := fun _ => 1
  nz := fun _ => inferInstance
  χ := fun _ => (1 : DirichletCharacter ℂ 1)
  a := fun _ => 1
  a_pos := fun _ => zero_lt_one
  adm := fun _ => Or.inl rfl

/-- The singleton's centered sum agrees with the archive's real zeta prime sum for every y. -/
theorem gm_zetaFamily (y : ℝ) : Deduction.Gm zetaFamily y = Deduction.G y := by
  classical
  have hχ : (fun n : ℕ => (1 : DirichletCharacter ℂ 1) n) = (fun _ : ℕ => (1 : ℂ)) := by
    funext n
    exact MulChar.one_apply (isUnit_of_subsingleton _)
  change (∑ _ : Unit, (1 : ℝ) * (Deduction.Gchi (1 : DirichletCharacter ℂ 1) y).re) = _
  calc
    _ = (Deduction.Gchi (1 : DirichletCharacter ℂ 1) y).re := by simp
    _ = Deduction.G y := by
      simp [Deduction.Gchi, hχ, Deduction.G, Complex.add_re, Complex.sub_re]

/-- A one-sided estimate on arbitrarily late three-halves windows implies Mathlib's RH. -/
theorem riemannHypothesis_of_prime_windows (h : OneSidedWindows Deduction.G) : RiemannHypothesis := by
  apply Formalism.VW.rh_of_right
  intro s hs _
  have hhalf : (1 / 2 : ℝ) < min s.re 1 := lt_min hs (by norm_num)
  obtain ⟨θ, hθhalf, hθmin⟩ := exists_between hhalf
  have hθs : θ < s.re := lt_of_lt_of_le hθmin (min_le_left _ _)
  have hθ1 : θ < 1 := lt_of_lt_of_le hθmin (min_le_right _ _)
  obtain ⟨C, hC⟩ := h θ hθhalf hθ1
  have hscale : (1 : ℝ) + 1 / 2 = 3 / 2 := by norm_num
  have hfree : Deduction.ZeroFree zetaFamily θ :=
    Deduction.zeroFree_of_rpow_window zetaFamily (θ := θ) (δ := 1 / 2) (C := C)
      (lt_trans (by norm_num : (0 : ℝ) < 1 / 2) hθhalf) hθ1 (by norm_num)
      (by simpa only [hscale, gm_zetaFamily] using hC)
  have hz : DirichletCharacter.LFunction (1 : DirichletCharacter ℂ 1) s ≠ 0 :=
    hfree () s hθs
  rwa [DirichletCharacter.LFunction_modOne_eq] at hz

/-- A pointwise identification transports a bound given in another prime-sum normalization. -/
theorem riemannHypothesis_of_identified_windows (g : ℝ → ℝ)
    (hg : ∀ y, g y = Deduction.G y) (h : OneSidedWindows g) : RiemannHypothesis := by
  rw [funext hg] at h
  exact riemannHypothesis_of_prime_windows h

end Reading.WindowBridge

#print axioms Reading.WindowBridge.gm_zetaFamily
#print axioms Reading.WindowBridge.riemannHypothesis_of_prime_windows
#print axioms Reading.WindowBridge.riemannHypothesis_of_identified_windows

end
