/-!
# ConsKinkyPref — Lean 4 Formalization

Auto-generated from HARK model specification.
State spaces, transitions, and Bellman structure.
-/

-- ConsKinkyPref: Consumption-saving model with kinky interest rates
-- Formal Lean 4 specification

-- State spaces
axiom KNrm : Type  -- normalized capital holdings (can be negative)
axiom PLvl : Type  -- permanent income level (positive)

-- Action space
axiom CNrm : Type  -- normalized consumption (non-negative)

-- Shock spaces
axiom PermShk : Type  -- permanent income shock
axiom TranShk : Type  -- transitory income shock
axiom PrefShk : Type  -- preference/marginal utility shock

-- Parameters
axiom Rboro : Real  -- interest rate when borrowing
axiom Rsave : Real  -- interest rate when saving
axiom PermGroFac : Real  -- expected permanent income growth factor
axiom LivPrb : Real  -- survival probability

-- Parameter constraints
axiom rboro_positive : Rboro > 1
axiom rsave_positive : Rsave > 1
axiom kinky_rates : Rboro > Rsave
axiom growth_positive : PermGroFac > 0
axiom livprb_valid : 0 ≤ LivPrb ∧ LivPrb ≤ 1

-- Shock distributions
axiom IncShkDstn : Type  -- joint distribution of permanent and transitory shocks
axiom PrefShkDstn : Type  -- distribution of preference shocks
axiom pLvlInitDstn : Type  -- initial permanent income distribution
axiom kNrmInitDstn : Type  -- initial capital distribution

-- Distribution properties
axiom incshk_draw : IncShkDstn → PermShk × TranShk
axiom prefshk_draw : PrefShkDstn → PrefShk
axiom perm_mean_one : ∀ (d : IncShkDstn), Real  -- E[PermShk] = 1
axiom tran_mean_one : ∀ (d : IncShkDstn), Real  -- E[TranShk] = 1

-- Conversion functions for state/action spaces
axiom kNrm_to_real : KNrm → Real
axiom pLvl_to_real : PLvl → Real
axiom cNrm_to_real : CNrm → Real
axiom permshk_to_real : PermShk → Real
axiom transhk_to_real : TranShk → Real
axiom prefshk_to_real : PrefShk → Real

axiom pLvl_positive : ∀ (p : PLvl), pLvl_to_real p > 0
axiom cNrm_nonneg : ∀ (c : CNrm), cNrm_to_real c ≥ 0
axiom permshk_positive : ∀ (ψ : PermShk), permshk_to_real ψ > 0
axiom transhk_positive : ∀ (ξ : TranShk), transhk_to_real ξ > 0

-- Intermediate variables
def yNrm (ξ : TranShk) : Real :=
  transhk_to_real ξ

def G (ψ : PermShk) : Real :=
  PermGroFac * permshk_to_real ψ

def is_borrowing (k : KNrm) : Bool :=
  kNrm_to_real k < 0

def Rfree (k : KNrm) : Real :=
  if is_borrowing k then Rboro else Rsave

def bNrm (k : KNrm) (ψ : PermShk) : Real :=
  Rfree k * kNrm_to_real k / G ψ

def mNrm (k : KNrm) (ψ : PermShk) (ξ : TranShk) : Real :=
  bNrm k ψ + yNrm ξ

def pLvl_next (p_prev : PLvl) (ψ : PermShk) : Real :=
  pLvl_to_real p_prev * G ψ

def aNrm (m : Real) (c : CNrm) : Real :=
  m - cNrm_to_real c

-- Consumption function
axiom cFunc : Real → PrefShk → CNrm

-- Budget constraint
axiom budget_constraint : ∀ (k : KNrm) (p : PLvl) (ψ : PermShk) (ξ : TranShk) (η : PrefShk),
  let m := mNrm k ψ ξ
  let c := cFunc m η
  cNrm_to_real c ≤ m ∧ cNrm_to_real c ≥ 0

-- State transition
def state_transition (k : KNrm) (p_prev : PLvl) (ψ : PermShk) (ξ : TranShk) (η : PrefShk) : Real × Real :=
  let m := mNrm k ψ ξ
  let c := cFunc m η
  let a := aNrm m c
  let p := pLvl_next p_prev ψ
  (a, p)

-- Value function type
axiom Value : KNrm → PLvl → Real

-- Utility function (depends on consumption and preference shock)
axiom u : CNrm → PrefShk → Real

-- Discount factor
axiom β : Real
axiom beta_valid : 0 < β ∧ β < 1

-- Bellman equation
def bellman_rhs (k : KNrm) (p_prev : PLvl) : Real :=
  sorry  -- sup over c, integrated over shocks

theorem bellman_equation : ∀ (k : KNrm) (p_prev : PLvl),
  Value k p_prev = bellman_rhs k p_prev := by
  sorry

-- Formal statement: Value is the supremum over consumption choices
-- integrated over all shocks (ψ, ξ, η) and survival
axiom bellman_definition : ∀ (k : KNrm) (p_prev : PLvl),
  Value k p_prev = 
    sorry  -- sup_{c ∈ feasible(m,η)} E[ u(c,η) + β * LivPrb * Value(a, p) ]

-- Feasible consumption set given market resources and preference shock
def feasible_consumption (m : Real) (η : PrefShk) : Set Real :=
  {c : Real | 0 ≤ c ∧ c ≤ m}

-- Policy function optimality
theorem policy_optimal : ∀ (k : KNrm) (p_prev : PLvl) (ψ : PermShk) (ξ : TranShk) (η : PrefShk),
  let m := mNrm k ψ ξ
  let c := cFunc m η
  cNrm_to_real c ∈ feasible_consumption m η := by
  sorry

-- Kinky interest rate structure properties
theorem interest_rate_kink : ∀ (k1 k2 : KNrm),
  kNrm_to_real k1 < 0 → kNrm_to_real k2 ≥ 0 → Rfree k1 = Rboro ∧ Rfree k2 = Rsave := by
  sorry

-- Permanent income evolution
theorem permanent_income_growth : ∀ (p_prev : PLvl) (ψ : PermShk),
  pLvl_next p_prev ψ = pLvl_to_real p_prev * PermGroFac * permshk_to_real ψ := by
  sorry

-- Market resources decomposition
theorem market_resources_identity : ∀ (k : KNrm) (ψ : PermShk) (ξ : TranShk),
  mNrm k ψ ξ = Rfree k * kNrm_to_real k / G ψ + yNrm ξ := by
  sorry

-- Asset accumulation identity
theorem asset_accumulation : ∀ (k : KNrm) (p_prev : PLvl) (ψ : PermShk) (ξ : TranShk) (η : PrefShk),
  let m := mNrm k ψ ξ
  let c := cFunc m η
  let (a, p_next) := state_transition k p_prev ψ ξ η
  a = m - cNrm_to_real c := by
  sorry

-- Survival probability structure
axiom mortality_outcome : Type
axiom mortality_draw : mortality_outcome → Bool
axiom mortality_prob : ∀ (ω : mortality_outcome), Real

theorem survival_probability : ∀ (ω : mortality_outcome),
  mortality_draw ω = true → mortality_prob ω = LivPrb := by
  sorry

-- Normalized variables remain finite
theorem normalized_finite : ∀ (k : KNrm) (p : PLvl) (ψ : PermShk) (ξ : TranShk),
  pLvl_to_real p > 0 → G ψ > 0 → 
  ∃ (M : Real), |mNrm k ψ ξ| < M := by
  sorry

-- Value function properties
theorem value_continuous : ∀ (ε : Real), ε > 0 → 
  ∃ (δ : Real), δ > 0 → ∀ (k1 k2 : KNrm) (p1 p2 : PLvl),
  |kNrm_to_real k1 - kNrm_to_real k2| < δ → 
  |pLvl_to_real p1 - pLvl_to_real p2| < δ →
  |Value k1 p1 - Value k2 p2| < ε := by
  sorry

theorem value_bounded : ∃ (M : Real), ∀ (k : KNrm) (p : PLvl),
  |Value k p| < M := by
  sorry

-- Consumption function properties
theorem consumption_function_continuous : ∀ (ε : Real) (η : PrefShk), ε > 0 →
  ∃ (δ : Real), δ > 0 → ∀ (m1 m2 : Real),
  |m1 - m2| < δ → 
  |cNrm_to_real (cFunc m1 η) - cNrm_to_real (cFunc m2 η)| < ε := by
  sorry

theorem consumption_increasing : ∀ (m1 m2 : Real) (η : PrefShk),
  m1 < m2 → 
  cNrm_to_real (cFunc m1 η) ≤ cNrm_to_real (cFunc m2 η) := by
  sorry
