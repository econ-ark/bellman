/-!
# ConsGenIncProcess — Lean 4 Formalization

Auto-generated from HARK model specification.
State spaces, transitions, and Bellman structure.
-/

import Lean

axiom Real : Type
axiom RealPos : Type
axiom RealNonneg : Type

axiom Real.add : Real → Real → Real
axiom Real.sub : Real → Real → Real
axiom Real.mul : Real → Real → Real
axiom Real.le : Real → Real → Prop

instance : Add Real := ⟨Real.add⟩
instance : Sub Real := ⟨Real.sub⟩
instance : Mul Real := ⟨Real.mul⟩
instance : LE Real := ⟨Real.le⟩

axiom RealPos.toReal : RealPos → Real
axiom RealNonneg.toReal : RealNonneg → Real

axiom RealPos.mul : RealPos → RealPos → RealPos

instance : Coe RealPos Real := ⟨RealPos.toReal⟩
instance : Coe RealNonneg Real := ⟨RealNonneg.toReal⟩

axiom IncomeShock : Type
axiom PermShk : IncomeShock → RealPos
axiom TranShk : IncomeShock → RealPos

axiom IncShkDstn : Type
axiom sampleShock : IncShkDstn → IncomeShock

axiom SurvivalShock : Type
axiom survives : SurvivalShock → Bool

axiom Rfree : RealPos
axiom LivPrb : Real
axiom LivPrb_in_unit_interval : (0 : Real) ≤ LivPrb ∧ LivPrb ≤ (1 : Real)

axiom pLvlNextFunc : RealPos → RealPos

structure ArrivalState where
  kLvl : RealNonneg
  pLvlPrev : RealPos

structure DecisionState where
  mLvl : RealNonneg
  pLvl : RealPos

structure ContinuationState where
  aLvl : RealNonneg
  pLvl : RealPos
  live : Bool

axiom Action : Type
axiom cLvl : Action → RealNonneg

axiom feasible : DecisionState → Action → Prop

axiom feasible_iff (ds : DecisionState) (a : Action) :
  feasible ds a ↔ (cLvl a : Real) ≤ (ds.mLvl : Real)

def arrivalToDecision (s : ArrivalState) (shock : IncomeShock) : DecisionState :=
  let perm := PermShk shock
  let tran := TranShk shock
  let p_temp := pLvlNextFunc s.pLvlPrev
  let pLvl := RealPos.mul p_temp perm
  let yLvl := RealPos.mul tran pLvl
  let bLvl := RealPos.mul Rfree (s.kLvl.toReal)
  let mLvl := (bLvl : Real) + (yLvl : Real)
  { mLvl := mLvl, pLvl := pLvl }

def decisionToContinuation (ds : DecisionState) (a : Action) (surv : SurvivalShock) : ContinuationState :=
  let consumption := cLvl a
  let aLvl := (ds.mLvl : Real) - (consumption : Real)
  { aLvl := aLvl, pLvl := ds.pLvl, live := survives surv }

def continuationToArrival (cs : ContinuationState) : ArrivalState :=
  { kLvl := cs.aLvl, pLvlPrev := cs.pLvl }

axiom ValueFunction : DecisionState → Real

axiom UtilityFunction : RealNonneg → RealPos → Real

axiom u : RealNonneg → RealPos → Real
axiom u_definition : u = UtilityFunction

axiom DiscFac : Real
axiom DiscFac_in_unit_interval : (0 : Real) ≤ DiscFac ∧ DiscFac ≤ (1 : Real)

axiom ExpectedValue : ContinuationState → Real

def bellmanObjective (ds : DecisionState) (a : Action) (dist : IncShkDstn) : Real :=
  let consumption := cLvl a
  let immediateUtility := u consumption ds.pLvl
  let continuation := decisionToContinuation ds a
  let expectedContinuation := ExpectedValue (continuation undefined)
  immediateUtility + DiscFac * expectedContinuation

theorem bellman_equation (ds : DecisionState) (dist : IncShkDstn) :
  ValueFunction ds = 
    (⨆ (a : Action), if feasible ds a then bellmanObjective ds a dist else (-1 : Real)) := by
  sorry

axiom ConsumptionFunction : DecisionState → RealNonneg

axiom cFunc_definition (m : RealNonneg) (p : RealPos) :
  ConsumptionFunction { mLvl := m, pLvl := p } = 
    (cLvl (⨆ (a : Action), if feasible { mLvl := m, pLvl := p } a 
                            then a 
                            else undefined))

theorem consumption_optimality (ds : DecisionState) (dist : IncShkDstn) :
  let c_star := ConsumptionFunction ds
  let a_star : Action := sorry
  cLvl a_star = c_star ∧ 
  feasible ds a_star ∧
  ∀ (a : Action), feasible ds a → 
    bellmanObjective ds a_star dist ≥ bellmanObjective ds a dist := by
  sorry

theorem budget_constraint (ds : DecisionState) (a : Action) :
  feasible ds a → (cLvl a : Real) + 
    (decisionToContinuation ds a undefined).aLvl.toReal = ds.mLvl.toReal := by
  sorry

theorem permanent_income_evolution (s : ArrivalState) (shock : IncomeShock) :
  let ds := arrivalToDecision s shock
  (ds.pLvl : Real) = 
    (pLvlNextFunc s.pLvlPrev : Real) * (PermShk shock : Real) := by
  sorry

theorem market_resources_equation (s : ArrivalState) (shock : IncomeShock) :
  let ds := arrivalToDecision s shock
  (ds.mLvl : Real) = 
    (Rfree : Real) * (s.kLvl : Real) + 
    (TranShk shock : Real) * (ds.pLvl : Real) := by
  sorry

theorem state_transition_law (s : ArrivalState) (shock : IncomeShock) 
    (a : Action) (surv : SurvivalShock) :
  let ds := arrivalToDecision s shock
  let cs := decisionToContinuation ds a surv
  let s_next := continuationToArrival cs
  cs.live = survives surv ∧
  s_next.kLvl = cs.aLvl ∧
  s_next.pLvlPrev = cs.pLvl := by
  sorry

axiom InitialPermanentIncomeDistribution : Type
axiom InitialNormalizedCapitalDistribution : Type

axiom sampleInitialPermanentIncome : InitialPermanentIncomeDistribution → RealPos
axiom sampleInitialNormalizedCapital : InitialNormalizedCapitalDistribution → RealNonneg

def initializeAgent (pInit : InitialPermanentIncomeDistribution) 
    (kNrmInit : InitialNormalizedCapitalDistribution) : ArrivalState :=
  let pLvlPrev := sampleInitialPermanentIncome pInit
  let kNrm := sampleInitialNormalizedCapital kNrmInit
  let kLvl := (pLvlPrev : Real) * (kNrm : Real)
  { kLvl := kLvl, pLvlPrev := pLvlPrev }

theorem survival_probability_constraint :
  (0 : Real) ≤ LivPrb ∧ LivPrb ≤ (1 : Real) := by
  exact LivPrb_in_unit_interval

theorem discount_factor_constraint :
  (0 : Real) ≤ DiscFac ∧ DiscFac ≤ (1 : Real) := by
  exact DiscFac_in_unit_interval

theorem positive_income_shocks (shock : IncomeShock) :
  ∃ (p : RealPos), PermShk shock = p ∧ 
  ∃ (t : RealPos), TranShk shock = t := by
  sorry

theorem consumption_nonnegativity (ds : DecisionState) (a : Action) :
  feasible ds a → (0 : Real) ≤ (cLvl a : Real) := by
  sorry

theorem assets_nonnegativity (ds : DecisionState) (a : Action) (surv : SurvivalShock) :
  feasible ds a → 
    (0 : Real) ≤ (decisionToContinuation ds a surv).aLvl.toReal := by
  sorry

axiom ExpectedValueIntegral : IncShkDstn → SurvivalShock → 
  (ContinuationState → Real) → Real

theorem value_function_recursive (s : ArrivalState) (dist : IncShkDstn) :
  ∀ (shock : IncomeShock),
    let ds := arrivalToDecision s shock
    ValueFunction ds = 
      (⨆ (a : Action), if feasible ds a 
        then u (cLvl a) ds.pLvl + 
             DiscFac * ExpectedValueIntegral dist undefined 
               (fun cs => ValueFunction (arrivalToDecision (continuationToArrival cs) undefined))
        else (-1 : Real)) := by
  sorry
