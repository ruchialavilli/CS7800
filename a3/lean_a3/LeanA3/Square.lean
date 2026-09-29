import Mathlib

/-!
# Unwrapping `f(x) = x^2` all the way down to sets

Layer 0  `f : ℝ → ℝ`, `f x = x ^ 2`            (Lean's built-in function)
Layer 1  `x ^ 2 = x * x`                        (unfold the power)
Layer 2  graph `F = {(x, y) ∈ ℝ × ℝ | y = x * x}` (a function *is* its set of pairs)
Layer 3  "F is a function": `∀ x, ∃! y, (x, y) ∈ F`,
         with `∃!` unfolded to `∃ y, (x, y) ∈ F ∧ ∀ y', (x, y') ∈ F → y' = y`
Layer 4  ordered pairs as sets (Kuratowski): `(a, b) := {{a}, {a, b}}`,
         so `F = { {{x}, {x, x*x}} | x ∈ ℝ }` is literally a set of sets of sets of reals.
-/

namespace Square

/-! ## Layer 0 -/

def f (x : ℝ) : ℝ := x ^ 2

/-! ## Layer 1: the power is just multiplication -/

theorem f_eq_mul (x : ℝ) : f x = x * x := by
  unfold f; ring

/-! ## Layer 2: f as a set of ordered pairs -/

/-- The graph of `f`, in set-builder notation. -/
def F : Set (ℝ × ℝ) := {p | p.2 = p.1 * p.1}

/-- Membership in `F`, spelled out. -/
theorem mem_F (x y : ℝ) : (x, y) ∈ F ↔ y = x * x := Iff.rfl

/-- `F` is exactly the graph of the Lean function `f`. -/
theorem F_eq_graph : F = {p : ℝ × ℝ | p.2 = f p.1} := by
  ext ⟨x, y⟩; simp [F, f_eq_mul]

/-- Equivalently, `F = {(x, x*x) | x ∈ ℝ}` (the image of `x ↦ (x, x*x)`). -/
theorem F_eq_range : F = Set.range (fun x : ℝ => (x, x * x)) := by
  ext ⟨x, y⟩
  constructor
  · intro h; exact ⟨x, by rw [mem_F] at h; rw [h]⟩
  · rintro ⟨z, hz⟩
    simp only [Prod.mk.injEq] at hz
    obtain ⟨rfl, rfl⟩ := hz
    rfl

/-! ## Layer 3: F satisfies the set-theoretic definition of a function ℝ → ℝ -/

/-- Every `x` has exactly one partner `y` (totality + uniqueness). -/
theorem F_is_function : ∀ x : ℝ, ∃! y : ℝ, (x, y) ∈ F :=
  fun x => ⟨x * x, rfl, fun _ hy => hy⟩

/-- The same statement with `∃!` unfolded into plain `∃` / `∀`. -/
theorem F_is_function' :
    ∀ x : ℝ, ∃ y : ℝ, (x, y) ∈ F ∧ ∀ y' : ℝ, (x, y') ∈ F → y' = y :=
  fun x => ⟨x * x, rfl, fun _ hy => hy⟩

/-! ## Layer 4: ordered pairs are themselves sets (Kuratowski) -/

/-- Kuratowski ordered pair: `(a, b) := {{a}, {a, b}}`. -/
def kpair (a b : ℝ) : Set (Set ℝ) := {{a}, {a, b}}

/-- The defining property of ordered pairs: equal pairs have equal components.
This is what makes `{{a}, {a, b}}` a legitimate encoding of `(a, b)`. -/
theorem kpair_inj {a b c d : ℝ} (h : kpair a b = kpair c d) : a = c ∧ b = d := by
  unfold kpair at h
  have h1 : ({a} : Set ℝ) ∈ ({{c}, {c, d}} : Set (Set ℝ)) := h ▸ Or.inl rfl
  have h2 : ({a, b} : Set ℝ) ∈ ({{c}, {c, d}} : Set (Set ℝ)) := h ▸ Or.inr rfl
  have h3 : ({c, d} : Set ℝ) ∈ ({{a}, {a, b}} : Set (Set ℝ)) := h ▸ Or.inr rfl
  simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at h1 h2 h3
  -- first components: {a} is {c} or {c, d}; either way c ∈ {a}
  have hac : a = c := by
    rcases h1 with h1 | h1
    · exact Set.singleton_eq_singleton_iff.mp h1
    · have : c ∈ ({a} : Set ℝ) := h1 ▸ Set.mem_insert c {d}
      exact (Set.mem_singleton_iff.mp this).symm
  subst hac
  refine ⟨rfl, ?_⟩
  -- second components
  have hd : d ∈ ({a, b} : Set ℝ) := by
    rcases h3 with h3 | h3
    · have : d ∈ ({a} : Set ℝ) := h3 ▸ Set.mem_insert_of_mem a rfl
      exact Or.inl (Set.mem_singleton_iff.mp this)
    · exact h3 ▸ Set.mem_insert_of_mem a rfl
  have hb : b ∈ ({a, d} : Set ℝ) := by
    rcases h2 with h2 | h2
    · have : b ∈ ({a} : Set ℝ) := h2 ▸ Set.mem_insert_of_mem a rfl
      exact Or.inl (Set.mem_singleton_iff.mp this)
    · exact h2 ▸ Set.mem_insert_of_mem a rfl
  simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hd hb
  rcases hb with rfl | rfl
  · rcases hd with rfl | rfl <;> rfl
  · rfl

/-- `f`, fully unwrapped: a set whose elements are Kuratowski pairs `{{x}, {x, x*x}}`. -/
def FK : Set (Set (Set ℝ)) := {P | ∃ x : ℝ, P = {{x}, {x, x * x}}}

/-- Membership in `FK` is exactly `y = x^2`, i.e. `FK` encodes the same relation as `f`. -/
theorem mem_FK (x y : ℝ) : kpair x y ∈ FK ↔ y = x ^ 2 := by
  constructor
  · rintro ⟨z, hz⟩
    obtain ⟨rfl, rfl⟩ := kpair_inj hz
    ring
  · intro h
    exact ⟨x, by rw [kpair, h, sq]⟩

/-- Every element of `FK` is a Kuratowski pair (so `FK` is a relation). -/
theorem FK_is_relation : ∀ P ∈ FK, ∃ x y : ℝ, P = kpair x y :=
  fun _ ⟨x, hx⟩ => ⟨x, x * x, hx⟩

/-- `FK` is a function ℝ → ℝ in the pure set-theoretic sense. -/
theorem FK_is_function : ∀ x : ℝ, ∃! y : ℝ, kpair x y ∈ FK := by
  intro x
  refine ⟨x ^ 2, (mem_FK x _).mpr rfl, fun y hy => (mem_FK x y).mp hy⟩

/-- Sanity check: the pair `(3, 9)` is in the set, `(3, 10)` is not. -/
example : kpair 3 9 ∈ FK := (mem_FK 3 9).mpr (by norm_num)
example : kpair 3 10 ∉ FK := fun h => by have := (mem_FK 3 10).mp h; norm_num at this

/-! ## Aside: the "x² = x + x + ⋯ + x (x times), so d/dx = x" fallacy -/

/-- The real derivative: `f' x = 2x`. -/
theorem deriv_f (x : ℝ) : deriv f x = 2 * x := by
  show deriv (fun x : ℝ => x ^ 2) x = 2 * x
  simp

/-- With a *fixed* number `n` of copies, term-by-term differentiation is fine: you get `n`.
The fallacy plugs in `n = x` only after differentiating, treating the count as constant. -/
theorem deriv_fixed_sum (n : ℕ) (x : ℝ) :
    deriv (fun x : ℝ => ∑ _i ∈ Finset.range n, x) x = n := by
  simp

/-- Product rule on `x * x` = (count) * (term): the count's growth contributes the missing `x`.
`1 * x` is from "one more copy of x", `x * 1` is from "each of the x copies grows by 1". -/
theorem deriv_mul_self (x : ℝ) : deriv (fun x : ℝ => x * x) x = 1 * x + x * 1 := by
  exact ((hasDerivAt_id' x).mul (hasDerivAt_id' x)).deriv

end Square
