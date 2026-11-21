import Atlas.Architecture
import Atlas.Separation
import Reading.WindowLogic
import Reading.BehrendSphere

/-! Axiom audit of every theorem in this repository's Lean library. The build log of this file is
parsed by `scripts/lean_audit.py` into `verification/logs/axioms.json`. -/

#print axioms Atlas.halfPlane_of_primitive
#print axioms Atlas.strip_of_halfPlane
#print axioms Atlas.rh_of_halfPlane
#print axioms Atlas.primitiveHalfPlane_of_supply
#print axioms Atlas.endpoints_of_supply
#print axioms Atlas.rh_of_prime_windows
#print axioms Atlas.Architecture.endpoints
#print axioms Atlas.toyArchitecture
#print axioms Atlas.Separation.eq_of_dvd_sub
#print axioms Atlas.Separation.at_most_one_per_centre
#print axioms Reading.excludeZeroByWindows
#print axioms Reading.criticalLineByReflection
#print axioms BehrendReading.normSq_nonneg
#print axioms BehrendReading.coordinates_zero_of_normSq_zero
#print axioms BehrendReading.distance_pos_of_ne
#print axioms BehrendReading.chord_identity
#print axioms BehrendReading.sphere_rel
#print axioms BehrendReading.sphere_midpoint
