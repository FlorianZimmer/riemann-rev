/-!
Two logical deductions used by the reading guide, independent of Mathlib.
`Good y` and `Bad y` refer to the entire window starting at y. The
quantifiers deliberately permit arbitrarily wide gaps between good windows.
The application to L-functions requires the analytic oscillation and the
arithmetic window-existence theorems of the original archive.
-/
namespace Reading

theorem excludeZeroByWindows {Index : Type} (Later : Index → Index → Prop)
    (Zero : Prop) (Good Bad : Index → Prop)
    (arithmetic : ∀ cutoff, ∃ y, Later cutoff y ∧ Good y)
    (oscillation : Zero → ∃ cutoff, ∀ y, Later cutoff y → Bad y)
    (incompatible : ∀ y, Good y → Bad y → False) : ¬ Zero := by
  intro zero
  obtain ⟨cutoff, allBad⟩ := oscillation zero
  obtain ⟨y, late, good⟩ := arithmetic cutoff
  exact incompatible y good (allBad y late)

/-- For a strip zero, trichotomy, right-hand exclusion and a reflected zero
on the inverse character rule out both strict sides. -/
theorem criticalLineByReflection {Point : Type} (Zero Left Line Right : Point → Prop)
    (side : ∀ s, Left s ∨ Line s ∨ Right s)
    (reflect : ∀ s, Zero s → Left s → ∃ t, Zero t ∧ Right t)
    (exclude : ∀ s, Right s → ¬ Zero s) (s : Point) (hs : Zero s) : Line s := by
  rcases side s with h | h | h
  · obtain ⟨t, hz, hr⟩ := reflect s hs h
    exact False.elim (exclude t hr hz)
  · exact h
  · exact False.elim (exclude s h hs)

#print axioms excludeZeroByWindows
#print axioms criticalLineByReflection
end Reading
