import Main

example : RiemannHypothesis := riemannHypothesis
example : RiemannZetaZerosOnLine := riemannZeta_eq_zero_re
example : DirichletLNonvanishingRightOfHalf := LFunction_ne_zero_of_half_lt_re
example : DirichletLZerosOnLine := LFunction_eq_zero_re
example : PrimitiveDirichletLZerosOnLine := LFunction_eq_zero_re_of_isPrimitive
example : DirichletLZerosOnLine ↔
    (∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N) (s : ℂ),
       0 < s.re → s.re < 1 → DirichletCharacter.LFunction χ s = 0 → s.re = 1 / 2) := Iff.rfl
#print axioms riemannHypothesis
#print axioms riemannZeta_eq_zero_re
#print axioms LFunction_ne_zero_of_half_lt_re
#print axioms LFunction_eq_zero_re
#print axioms LFunction_eq_zero_re_of_isPrimitive
