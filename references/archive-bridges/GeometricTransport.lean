import WindowBridge
import Development.AutomorphicArithmetic.PrimitiveCosets.GzEq

namespace Reading.WindowBridge

/-- The archive identifies both normalizations pointwise, at every real argument. -/
theorem riemannHypothesis_of_geometric_windows (h : OneSidedWindows Formalism.Gz) : RiemannHypothesis := by
  apply riemannHypothesis_of_identified_windows Formalism.Gz _ h
  intro y
  obtain ⟨hza, had⟩ := UpperTheory.Comparison₂.Gz_eq y
  exact hza.trans had

end Reading.WindowBridge

#print axioms Reading.WindowBridge.riemannHypothesis_of_geometric_windows
