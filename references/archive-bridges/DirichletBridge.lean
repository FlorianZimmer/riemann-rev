import Development.AutomorphicArithmetic.CharacterBoxes.SupplyChi
import Development.AutomorphicArithmetic.CharacterBoxes.ZeroFreeAllOfTopG
import Development.AutomorphicArithmetic.CharacterBoxes.Imprimitive
import Development.AutomorphicArithmetic.CharacterBoxes.ClaimStrip
import Statements

namespace Reading.DirichletBridge

open Formalism.HC UpperTheory.Top

/-- The cohomology cutoff is 401 for each primitive character. The supplied
host width is the same real number 3/2 for all these characters. -/
theorem primitiveZeroFree_of_topG_vWin401 (hG : UpperTheory.Top.TopG)
    (hV : ∀ ψ : PChar, VWinAt ψ 401) : ZeroFreeAll := by
  apply UpperTheory.Top.zeroFreeAll_of_topG (la := (3 / 2 : ℝ)) (by norm_num) hG
  intro ψ
  exact UpperTheory.Top.supplyChi ψ (hV ψ)

/-- Pass to arbitrary positive moduli, then use the archived critical-strip
and zeta reductions. The right-half-plane predicate retains its pole exception. -/
theorem endpoints_of_topG_vWin401 (hG : UpperTheory.Top.TopG)
    (hV : ∀ ψ : PChar, VWinAt ψ 401) :
    RiemannHypothesis ∧ DirichletLNonvanishingRightOfHalf ∧ DirichletLZerosOnLine := by
  have hχ : DirichletLNonvanishingRightOfHalf :=
    UpperTheory.Top.imprimitive (primitiveZeroFree_of_topG_vWin401 hG hV)
  exact ⟨Claim.zeta hχ, hχ, Claim.strip hχ⟩

end Reading.DirichletBridge

set_option pp.fullNames true

#check @Reading.DirichletBridge.primitiveZeroFree_of_topG_vWin401
#check @Reading.DirichletBridge.endpoints_of_topG_vWin401
#print axioms Reading.DirichletBridge.primitiveZeroFree_of_topG_vWin401
#print axioms Reading.DirichletBridge.endpoints_of_topG_vWin401
