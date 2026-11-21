/-!
# Integer spheres and integer affine relations

The coordinates are indexed by `Fin n`, including dimension zero. All
coefficients may be negative. The norm is the sum of the coordinate squares.
-/
namespace BehrendReading

/-- The squared Euclidean norm of an integer vector. -/
def normSq : {n : Nat} → (Fin n → Int) → Int
  | 0, _ => 0
  | n + 1, v => v 0 ^ 2 + normSq (n := n) (fun k => v k.succ)

theorem normSq_nonneg {n : Nat} (v : Fin n → Int) : 0 ≤ normSq v := by
  induction n with
  | zero => exact Int.le_refl 0
  | succ n ih =>
    exact Int.add_nonneg (Int.sq_nonneg _) (ih (fun k => v k.succ))

theorem coordinates_zero_of_normSq_zero {n : Nat} (v : Fin n → Int)
    (h : normSq v = 0) : ∀ k, v k = 0 := by
  induction n with
  | zero => exact fun k => Fin.elim0 k
  | succ n ih =>
    change v 0 ^ 2 + normSq (fun k : Fin n => v k.succ) = 0 at h
    have hhead := Int.sq_nonneg (v 0)
    have htail := normSq_nonneg (fun k : Fin n => v k.succ)
    have headZero : v 0 ^ 2 = 0 := by omega
    have tailZero : normSq (fun k : Fin n => v k.succ) = 0 := by omega
    rw [Int.pow_succ, Int.pow_one] at headZero
    exact Fin.cases ((Int.mul_eq_zero.mp headZero).elim id id) (ih _ tailZero)

/-- Distinct integer vectors have strictly positive squared distance. -/
theorem distance_pos_of_ne {n : Nat} (u v : Fin n → Int) (hne : v ≠ u) :
    0 < normSq (fun k => v k - u k) := by
  have nonnegative := normSq_nonneg (fun k => v k - u k)
  have nonzero : normSq (fun k => v k - u k) ≠ 0 := by
    intro h
    apply hne
    funext k
    exact Int.sub_eq_zero.mp (coordinates_zero_of_normSq_zero _ h k)
  omega

private theorem coordinate_identity (x y z i j : Int)
    (h : j * (y - x) = i * (z - x)) :
    j * (j - i) * (y - x) ^ 2 =
      i ^ 2 * (z ^ 2 - x ^ 2) - i * j * (y ^ 2 - x ^ 2) := by
  have factorization :
      i ^ 2 * (z ^ 2 - x ^ 2) - i * j * (y ^ 2 - x ^ 2) - j * (j - i) * (y - x) ^ 2 =
      (i * (z - x) - j * (y - x)) * (i * (z - x) + j * (y - x) + 2 * i * x) := by
    grind only
  rw [← h, Int.sub_self, Int.zero_mul] at factorization
  omega

/-- The weighted chord identity before imposing equality of the three radii. -/
theorem chord_identity {n : Nat} (u v w : Fin n → Int) (i j : Int)
    (line : ∀ k, j * (v k - u k) = i * (w k - u k)) :
    j * (j - i) * normSq (fun k => v k - u k) =
      i ^ 2 * (normSq w - normSq u) - i * j * (normSq v - normSq u) := by
  induction n with
  | zero => simp [normSq]
  | succ n ih =>
    have head := coordinate_identity (u 0) (v 0) (w 0) i j (line 0)
    have tail := ih (fun k => u k.succ) (fun k => v k.succ)
      (fun k => w k.succ) (fun k => line k.succ)
    simp only [normSq]
    grind only

/-- On a sphere and on an integer-parameter line, the second point must
coincide with the first whenever the denominator and its difference from the
numerator are nonzero. The numerator may itself be zero. -/
theorem sphere_rel {n : Nat} (u v w : Fin n → Int) (radiusSq i j : Int)
    (hu : normSq u = radiusSq) (hv : normSq v = radiusSq) (hw : normSq w = radiusSq)
    (hj : j ≠ 0) (hij : i ≠ j) (line : ∀ k, j * (v k - u k) = i * (w k - u k)) :
    v = u := by
  have identity := chord_identity u v w i j line
  simp only [hu, hv, hw, Int.sub_self, Int.mul_zero] at identity
  have coefficient : j * (j - i) ≠ 0 := Int.mul_ne_zero hj (by omega)
  have distanceZero := (Int.mul_eq_zero.mp identity).resolve_left coefficient
  funext k
  exact Int.sub_eq_zero.mp (coordinates_zero_of_normSq_zero _ distanceZero k)

/-- A three-term arithmetic progression on an integer sphere is constant. -/
theorem sphere_midpoint {n : Nat} (u v w : Fin n → Int) (radiusSq : Int)
    (hu : normSq u = radiusSq) (hv : normSq v = radiusSq) (hw : normSq w = radiusSq)
    (midpoint : ∀ k, 2 * v k = u k + w k) : u = v ∧ v = w := by
  have line (k : Fin n) : 2 * (v k - u k) = 1 * (w k - u k) := by
    have h := midpoint k
    omega
  have eqVU := sphere_rel u v w radiusSq 1 2 hu hv hw (by decide) (by decide) line
  refine ⟨eqVU.symm, ?_⟩
  funext k
  have h := midpoint k
  have e := congrFun eqVU k
  omega

end BehrendReading
