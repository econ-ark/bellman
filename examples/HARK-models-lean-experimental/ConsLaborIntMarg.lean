/-!
# ConsLaborIntMarg — Lean 4 Formalization

Auto-generated from HARK model specification.
State spaces, transitions, and Bellman structure.
-/

import Lean

-- State spaces
axiom NormalizedCapital : Type
axiom PermanentIncome : Type
axiom TransitoryShock : Type
axiom PermanentShock : Type

-- Action spaces
axiom NormalizedConsumption : Type
axiom LaborSupply : Type

-- Basic assumptions on state spaces
axiom normalized_capital_nonneg : NormalizedCapital → Prop
axiom permanent_income_pos : PermanentIncome → Prop
axiom transitory_shock_nonneg : TransitoryShock → Prop
axiom permanent_shock_pos : PermanentShock → Prop

-- Basic assumptions on action spaces
axiom labor_supply_in_unit_interval : LaborSupply → Prop
axiom normalized_consumption_nonneg : NormalizedConsumption → Prop

-- Parameters
axiom Rfree : Real
axiom PermGroFac : Real
axiom LivPrb : Real
axiom WageRte : Real

-- Parameter assumptions
axiom Rfree_pos : Rfree > 0
axiom PermGroFac_pos : PermGroFac > 0
axiom LivPrb_prob : 0 ≤ LivPrb ∧ LivPrb ≤ 1
axiom WageRte_nonneg : WageRte ≥ 0

-- Arrival perch state: (kNrm, pLvlPrev)
def ArrivalState : Type := NormalizedCapital × PermanentIncome

-- Decision perch state: (bNrm, pLvl, TranShk)
def DecisionState : Type := Real × PermanentIncome × TransitoryShock

-- Continuation perch state: (aNrm, pLvl)
def ContinuationState : Type := Real × PermanentIncome

-- Action pair: (cNrm, Lbr)
def Action : Type := NormalizedConsumption × LaborSupply

-- Shock pair
def IncomeShock : Type := PermanentShock × TransitoryShock

-- Permanent income growth calculation
def permanent_growth (G_bar : Real) (psi : PermanentShock) : Real :=
  G_bar * (sorry : Real)  -- represents PermGroFac * PermShk

-- Permanent income update
def update_permanent_income (p_prev : PermanentIncome) (G : Real) : PermanentIncome :=
  sorry  -- represents p_prev * G

-- Normalized bank balances calculation
def normalized_bank_balances (R : Real) (k : NormalizedCapital) (G : Real) : Real :=
  R * (sorry : Real) / G  -- represents Rfree * kNrm / G

-- Effective labor supply
def effective_labor (theta : TransitoryShock) (ell : LaborSupply) : Real :=
  (sorry : Real) * (sorry : Real)  -- represents TranShk * Lbr

-- Normalized labor income
def normalized_income (w : Real) (theta : TransitoryShock) (ell : LaborSupply) : Real :=
  w * effective_labor theta ell

-- Market resources
def market_resources (b : Real) (y : Real) : Real :=
  b + y

-- End-of-period assets
def end_of_period_assets (m : Real) (c : NormalizedConsumption) : Real :=
  m - (sorry : Real)  -- represents mNrm - cNrm

-- Policy functions (to be determined by optimization)
axiom cFunc : Real → TransitoryShock → NormalizedConsumption
axiom LbrFunc : Real → TransitoryShock → LaborSupply

-- Shock distribution
axiom IncShkDstn : Type
axiom income_shock_distribution : IncShkDstn

-- Utility function structure
axiom utility : NormalizedConsumption → LaborSupply → Real

-- Discount factor
axiom DiscFac : Real
axiom DiscFac_bounds : 0 < DiscFac ∧ DiscFac < 1

-- Value function at arrival perch
axiom value_arrival : ArrivalState → Real

-- Value function at decision perch
axiom value_decision : DecisionState → Real

-- Continuation value function
axiom continuation_value : ContinuationState → Real

-- Expected value over income shocks
axiom E_income_shocks : (IncomeShock → Real) → Real

-- Expected value over survival shock
def expected_survival (LivPrb : Real) (v_survive : Real) (v_die : Real) : Real :=
  LivPrb * v_survive + (1 - LivPrb) * v_die

-- Budget constraint: consumption must not exceed market resources
def budget_feasible (b : Real) (theta : TransitoryShock) (c : NormalizedConsumption) (ell : LaborSupply) : Prop :=
  let y := normalized_income WageRte theta ell
  let m := market_resources b y
  (sorry : Real) ≤ m  -- represents cNrm ≤ mNrm

-- Labor supply constraint
def labor_feasible (ell : LaborSupply) : Prop :=
  labor_supply_in_unit_interval ell

-- Combined feasibility constraint
def action_feasible (b : Real) (theta : TransitoryShock) (c : NormalizedConsumption) (ell : LaborSupply) : Prop :=
  budget_feasible b theta c ell ∧ labor_feasible ell

-- Transition from decision perch to continuation perch
def transition_to_continuation (b : Real) (p : PermanentIncome) (theta : TransitoryShock) 
    (c : NormalizedConsumption) (ell : LaborSupply) : ContinuationState :=
  let y := normalized_income WageRte theta ell
  let m := market_resources b y
  let a := end_of_period_assets m c
  (a, p)

-- Transition from continuation perch to next arrival perch (through survival)
def transition_to_arrival (a : Real) (p : PermanentIncome) : ArrivalState :=
  (sorry, p)  -- represents (aNrm twisted to kNrm, pLvl twisted to pLvlPrev)

-- Bellman equation at decision perch
def bellman_decision : Prop :=
  ∀ (b : Real) (p : PermanentIncome) (theta : TransitoryShock),
    value_decision (b, p, theta) = 
      (sorry : Real)  -- max over feasible (c, ell) of:
                      -- utility c ell + DiscFac * E[continuation_value | survival]

-- Bellman equation at arrival perch
def bellman_arrival : Prop :=
  ∀ (s : ArrivalState),
    let (k, p_prev) := s
    value_arrival s = E_income_shocks (fun shock =>
      let (psi, theta) := shock
      let G := permanent_growth PermGroFac psi
      let p := update_permanent_income p_prev G
      let b := normalized_bank_balances Rfree k G
      value_decision (b, p, theta))

-- Optimality of policy functions
theorem policy_optimal : 
  ∀ (b : Real) (theta : TransitoryShock),
    let c := cFunc b theta
    let ell := LbrFunc b theta
    action_feasible b theta c ell ∧
    (∀ (c' : NormalizedConsumption) (ell' : LaborSupply),
      action_feasible b theta c' ell' →
        utility c ell + DiscFac * (sorry : Real) ≥ 
        utility c' ell' + DiscFac * (sorry : Real)) :=
by sorry

-- Euler equation for consumption (FOC)
theorem euler_equation :
  ∀ (b : Real) (p : PermanentIncome) (theta : TransitoryShock),
    let c := cFunc b theta
    let ell := LbrFunc b theta
    ∃ (du_dc : Real), du_dc = sorry  -- marginal utility of consumption equals 
                                      -- expected discounted marginal utility of future consumption
:= by sorry

-- Labor supply FOC
theorem labor_supply_foc :
  ∀ (b : Real) (theta : TransitoryShock),
    let c := cFunc b theta
    let ell := LbrFunc b theta
    ∃ (du_dc du_dell : Real),
      du_dell = WageRte * (sorry : Real) * du_dc  -- marginal disutility of labor equals
                                                    -- wage times transitory shock times marginal utility of consumption
:= by sorry

-- Value function is increasing in bank balances
theorem value_increasing_in_b :
  ∀ (b1 b2 : Real) (p : PermanentIncome) (theta : TransitoryShock),
    b1 < b2 → value_decision (b1, p, theta) ≤ value_decision (b2, p, theta) :=
by sorry

-- Value function is increasing in permanent income
theorem value_increasing_in_p :
  ∀ (b : Real) (p1 p2 : PermanentIncome) (theta : TransitoryShock),
    (sorry : Real) < (sorry : Real) →  -- represents p1 < p2
    value_decision (b, p1, theta) ≤ value_decision (b, p2, theta) :=
by sorry

-- Consumption is increasing in bank balances
theorem consumption_increasing_in_b :
  ∀ (b1 b2 : Real) (theta : TransitoryShock),
    b1 < b2 → (sorry : Real) ≤ (sorry : Real)  -- represents cFunc b1 theta ≤ cFunc b2 theta
:= by sorry

-- Labor supply is decreasing in bank balances (leisure is normal good)
theorem labor_decreasing_in_b :
  ∀ (b1 b2 : Real) (theta : TransitoryShock),
    b1 < b2 → (sorry : Real) ≥ (sorry : Real)  -- represents LbrFunc b1 theta ≥ LbrFunc b2 theta
:= by sorry

-- Labor supply is increasing in transitory productivity
theorem labor_increasing_in_theta :
  ∀ (b : Real) (theta1 theta2 : TransitoryShock),
    (sorry : Real) < (sorry : Real) →  -- represents theta1 < theta2
    (sorry : Real) ≤ (sorry : Real)    -- represents LbrFunc b theta1 ≤ LbrFunc b theta2
:= by sorry

-- Full model consistency: Bellman equations hold with optimal policies
theorem model_consistency :
  bellman_arrival ∧ bellman_decision ∧
  (∀ (b : Real) (theta : TransitoryShock), 
    let c := cFunc b theta
    let ell := LbrFunc b theta
    action_feasible b theta c ell) :=
by sorry
