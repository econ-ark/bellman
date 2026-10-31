/-!
# ConsExtMargMed — Lean 4 Formalization

Auto-generated from HARK model specification.
State spaces, transitions, and Bellman structure.
-/

axiom Real : Type
axiom Real.add : Real → Real → Real
axiom Real.mul : Real → Real → Real
axiom Real.sub : Real → Real → Real
axiom Real.le : Real → Real → Prop
axiom Real.lt : Real → Real → Prop
axiom Real.zero : Real
axiom Real.one : Real

infixl:65 " + " => Real.add
infixl:70 " * " => Real.mul
infixl:65 " - " => Real.sub
infix:50 " ≤ " => Real.le
infix:50 " < " => Real.lt

-- State space types
axiom RealNonneg : Type  -- [0,∞)
axiom RealPos : Type     -- (0,∞)

-- Ensure state spaces are subsets of Real
axiom RealNonneg.toReal : RealNonneg → Real
axiom RealPos.toReal : RealPos → Real
axiom RealNonneg.nonneg : ∀ (x : RealNonneg), Real.zero ≤ RealNonneg.toReal x
axiom RealPos.pos : ∀ (x : RealPos), Real.zero < RealPos.toReal x

-- Arrival state: capital and previous permanent income
def ArrivalState : Type := RealNonneg × RealPos

-- Post-income state: market resources and permanent income
def PostIncomeState : Type := RealNonneg × RealPos

-- Medical shocks: cost and utility penalty
def MedicalShock : Type := RealNonneg × RealNonneg

-- Decision state: includes medical shock information
def DecisionState : Type := PostIncomeState × MedicalShock

-- Continuation state: end-of-period assets and permanent income
def ContinuationState : Type := RealNonneg × RealPos

-- Action spaces
def CareBool : Type := Bool
def Consumption : Type := RealNonneg

-- Income shocks: permanent and transitory
def IncomeShock : Type := RealPos × RealNonneg

-- Model parameters
structure Parameters where
  Rfree : Real      -- risk-free return factor
  LivPrb : Real     -- survival probability
  Rfree_pos : Real.zero < Rfree
  LivPrb_bounds : Real.zero ≤ LivPrb ∧ LivPrb ≤ Real.one

-- Shock distributions (abstract probability distributions)
axiom ProbDist : Type → Type
axiom IncShkDstn : ProbDist IncomeShock
axiom MedShockDstn : ProbDist MedicalShock
axiom pLvlInitDstn : ProbDist RealPos
axiom kNrmInitDstn : ProbDist RealNonneg

-- Permanent income growth function (expected permanent income)
axiom pLvlNextFunc : RealPos → RealPos

-- Value function over bank balances and permanent income (pre-consumption)
axiom vFuncMid : RealNonneg → RealPos → Real

-- Consumption function over bank balances and permanent income
axiom cFunc : RealNonneg → RealPos → RealNonneg

-- Feasibility constraint: consumption cannot exceed bank balances
axiom cFunc_feasible : ∀ (b : RealNonneg) (p : RealPos),
  RealNonneg.toReal (cFunc b p) ≤ RealNonneg.toReal b

-- Transition from arrival state to post-income state
def incomeTransition (params : Parameters) (s : ArrivalState) (shock : IncomeShock) : PostIncomeState :=
  let (kLvl, pLvlPrev) := s
  let (PermShk, TranShk) := shock
  let p_temp := pLvlNextFunc pLvlPrev
  let pLvl : RealPos := sorry  -- pLvl = p_temp * PermShk (multiplication of RealPos)
  let wLvl : RealNonneg := sorry  -- wLvl = Rfree * kLvl
  let yLvl : RealNonneg := sorry  -- yLvl = TranShk * pLvl
  let mLvl : RealNonneg := sorry  -- mLvl = wLvl + yLvl
  (mLvl, pLvl)

-- Medical care decision: compare value with and without care
def medicalCareDecision (mLvl : RealNonneg) (pLvl : RealPos) (medShock : MedicalShock) : CareBool :=
  let (MedCost, MedShk) := medShock
  let b_if_care : RealNonneg := sorry  -- b_if_care = mLvl - MedCost
  let v_if_care := vFuncMid b_if_care pLvl
  let v_temp := vFuncMid mLvl pLvl
  let v_no_care : Real := sorry  -- v_no_care = v_temp - MedShk
  sorry  -- return (v_if_care > v_no_care)

-- Bank balances after medical expenditure
def bankBalances (mLvl : RealNonneg) (medShock : MedicalShock) (care : CareBool) : RealNonneg :=
  let (MedCost, _) := medShock
  if care then sorry  -- mLvl - MedCost
  else mLvl

-- Transition from decision state to continuation state
def consumptionTransition (state : DecisionState) (care : CareBool) : ContinuationState :=
  let ((mLvl, pLvl), medShock) := state
  let bLvl := bankBalances mLvl medShock care
  let cLvl := cFunc bLvl pLvl
  let aLvl : RealNonneg := sorry  -- aLvl = bLvl - cLvl
  (aLvl, pLvl)

-- Twist: continuation state becomes next period arrival state
def twist (cont : ContinuationState) : ArrivalState :=
  let (aLvl, pLvl) := cont
  (aLvl, pLvl)  -- aLvl becomes kLvl, pLvl becomes pLvlPrev

-- Bellman equation structure
-- V(k, p⁻) = E[W(m, p, μ, ζ) | k, p⁻]
-- where W(m, p, μ, ζ) = max{v_if_care, v_no_care}
-- and value continues via consumption decision

def valueFunction (params : Parameters) (s : ArrivalState) : Real :=
  sorry  -- E_{(Ψ,ξ) ~ IncShkDstn} [ E_{(μ,ζ) ~ MedShockDstn} [ max_care W(m,p,μ,ζ) ] ]

-- Value after observing medical shock (before consumption)
def postMedicalValue (state : PostIncomeState) (medShock : MedicalShock) : Real :=
  let (mLvl, pLvl) := state
  let (MedCost, MedShk) := medShock
  let b_if_care : RealNonneg := sorry  -- mLvl - MedCost
  let v_if_care := vFuncMid b_if_care pLvl
  let v_temp := vFuncMid mLvl pLvl
  let v_no_care : Real := sorry  -- v_temp - MedShk
  sorry  -- max(v_if_care, v_no_care)

-- Key properties to verify

-- Consumption function is increasing in bank balances
theorem cFunc_increasing_in_b : 
  ∀ (b1 b2 : RealNonneg) (p : RealPos),
    RealNonneg.toReal b1 ≤ RealNonneg.toReal b2 →
    RealNonneg.toReal (cFunc b1 p) ≤ RealNonneg.toReal (cFunc b2 p) :=
  sorry

-- Value function is increasing in permanent income
theorem vFuncMid_increasing_in_p :
  ∀ (b : RealNonneg) (p1 p2 : RealPos),
    RealPos.toReal p1 ≤ RealPos.toReal p2 →
    vFuncMid b p1 ≤ vFuncMid b p2 :=
  sorry

-- Value function is increasing in bank balances
theorem vFuncMid_increasing_in_b :
  ∀ (b1 b2 : RealNonneg) (p : RealPos),
    RealNonneg.toReal b1 ≤ RealNonneg.toReal b2 →
    vFuncMid b1 p ≤ vFuncMid b2 p :=
  sorry

-- Care is more likely when medical shock is larger
theorem care_responsive_to_shock :
  ∀ (mLvl : RealNonneg) (pLvl : RealPos) (cost : RealNonneg) (shk1 shk2 : RealNonneg),
    RealNonneg.toReal shk1 < RealNonneg.toReal shk2 →
    medicalCareDecision mLvl pLvl (cost, shk1) = false →
    medicalCareDecision mLvl pLvl (cost, shk2) = false :=
  sorry

-- Budget constraint: end-of-period assets are non-negative
theorem assets_nonnegative :
  ∀ (state : DecisionState) (care : CareBool),
    let (aLvl, _) := consumptionTransition state care
    Real.zero ≤ RealNonneg.toReal aLvl :=
  sorry

-- Medical expenditure equals cost if care chosen, zero otherwise
theorem medical_expenditure_binary :
  ∀ (mLvl : RealNonneg) (pLvl : RealPos) (medShock : MedicalShock),
    let (MedCost, _) := medShock
    let care := medicalCareDecision mLvl pLvl medShock
    let bLvl := bankBalances mLvl medShock care
    (care = true → sorry) ∧  -- RealNonneg.toReal mLvl - RealNonneg.toReal bLvl = RealNonneg.toReal MedCost
    (care = false → bLvl = mLvl) :=
  sorry

-- Bellman optimality condition
theorem bellman_equation (params : Parameters) :
  ∀ (s : ArrivalState),
    valueFunction params s = sorry  -- full expectation over shocks and optimal decisions
  := sorry

-- Permanent income process respects growth function
theorem permanent_income_growth (params : Parameters) :
  ∀ (pLvlPrev : RealPos) (PermShk : RealPos),
    let p_expected := pLvlNextFunc pLvlPrev
    sorry  -- pLvl = p_expected * PermShk defines the permanent income process
  := sorry

-- Survival affects continuation value
theorem survival_affects_continuation (params : Parameters) :
  ∀ (cont : ContinuationState),
    let next_arrival := twist cont
    sorry  -- E[value(next_arrival)] weighted by LivPrb
  := sorry
