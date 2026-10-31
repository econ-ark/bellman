/-!
# ConsKinkedR — Lean 4 Formalization

Auto-generated from HARK model specification.
State spaces, transitions, and Bellman structure.
-/

import Lean

axiom Real : Type
axiom RealPos : Type
axiom Bool : Type

axiom add : Real → Real → Real
axiom sub : Real → Real → Real
axiom mul : Real → Real → Real
axiom div : Real → Real → Real
axiom lt : Real → Real → Bool
axiom ge : Real → Real → Bool

infixl:65 " + " => add
infixl:65 " - " => sub
infixl:70 " * " => mul
infixl:70 " / " => div
infix:50 " < " => lt
infix:50 " ≥ " => ge

axiom zero : Real
axiom one : Real

axiom RealPos.toReal : RealPos → Real

axiom PermShock : Type
axiom TranShock : Type

axiom PermShock.toRealPos : PermShock → RealPos
axiom TranShock.toRealPos : TranShock → RealPos

axiom IncShkDstn : Type
axiom sample_IncShkDstn : IncShkDstn → PermShock × TranShock

axiom pLvlInitDstn : Type
axiom kNrmInitDstn : Type
axiom sample_pLvlInitDstn : pLvlInitDstn → RealPos
axiom sample_kNrmInitDstn : kNrmInitDstn → Real

structure Parameters where
  Rboro : RealPos
  Rsave : RealPos
  PermGroFac : RealPos
  LivPrb : Real

axiom cFunc : Real → Real

structure ArrivalState where
  kNrm : Real
  pLvlPrev : RealPos

structure DecisionState where
  mNrm : Real
  pLvl : RealPos
  bNrm : Real
  yNrm : Real
  Rfree : RealPos
  boro : Bool

structure ContinuationState where
  aNrm : Real
  pLvl : RealPos
  live : Bool

def boro_indicator (kNrm : Real) : Real :=
  if kNrm < zero then one else zero

def realized_interest_factor (params : Parameters) (kNrm : Real) : RealPos :=
  let b := boro_indicator kNrm
  let Rsave_val := RealPos.toReal params.Rsave
  let Rboro_val := RealPos.toReal params.Rboro
  let R_val := Rsave_val + (Rboro_val - Rsave_val) * b
  axiom_RealPos_from_interest : RealPos

def transition_to_decision 
  (params : Parameters)
  (arrival : ArrivalState)
  (shocks : IncShkDstn) : DecisionState :=
  let (PermShk, TranShk) := sample_IncShkDstn shocks
  let yNrm := RealPos.toReal (TranShock.toRealPos TranShk)
  let G := RealPos.toReal params.PermGroFac * RealPos.toReal (PermShock.toRealPos PermShk)
  let pLvl_val := RealPos.toReal arrival.pLvlPrev * G
  let boro := arrival.kNrm < zero
  let Rfree := realized_interest_factor params arrival.kNrm
  let bNrm := (RealPos.toReal Rfree * arrival.kNrm) / G
  let mNrm := bNrm + yNrm
  {
    mNrm := mNrm,
    pLvl := axiom_pLvl : RealPos,
    bNrm := bNrm,
    yNrm := yNrm,
    Rfree := Rfree,
    boro := boro
  }

def apply_control (decision : DecisionState) (cNrm : Real) : ContinuationState :=
  let aNrm := decision.mNrm - cNrm
  {
    aNrm := aNrm,
    pLvl := decision.pLv,
    live := axiom_live : Bool
  }

def optimal_consumption (decision : DecisionState) : Real :=
  cFunc decision.mNrm

def twist_to_next_period (cont : ContinuationState) : ArrivalState :=
  {
    kNrm := cont.aNrm,
    pLvlPrev := cont.pLvl
  }

def budget_constraint (mNrm cNrm aNrm : Real) : Prop :=
  aNrm = mNrm - cNrm

theorem budget_constraint_holds (decision : DecisionState) (cNrm : Real) :
  let cont := apply_control decision cNrm
  budget_constraint decision.mNrm cNrm cont.aNrm :=
by
  sorry

def market_resources_identity (bNrm yNrm mNrm : Real) : Prop :=
  mNrm = bNrm + yNrm

theorem market_resources_identity_holds (decision : DecisionState) :
  market_resources_identity decision.bNrm decision.yNrm decision.mNrm :=
by
  sorry

def bank_balance_identity (params : Parameters) (kNrm : Real) (G : Real) (Rfree : RealPos) (bNrm : Real) : Prop :=
  bNrm = (RealPos.toReal Rfree * kNrm) / G

theorem bank_balance_identity_holds (params : Parameters) (arrival : ArrivalState) (shocks : IncShkDstn) :
  let decision := transition_to_decision params arrival shocks
  let (PermShk, TranShk) := sample_IncShkDstn shocks
  let G := RealPos.toReal params.PermGroFac * RealPos.toReal (PermShock.toRealPos PermShk)
  bank_balance_identity params arrival.kNrm G decision.Rfree decision.bNrm :=
by
  sorry

def kinked_interest_rate (params : Parameters) (kNrm : Real) (Rfree : RealPos) : Prop :=
  (kNrm ≥ zero → Rfree = params.Rsave) ∧
  (kNrm < zero → Rfree = params.Rboro)

axiom Rboro_gt_Rsave (params : Parameters) :
  RealPos.toReal params.Rboro > RealPos.toReal params.Rsave

theorem kinked_rate_property (params : Parameters) (kNrm : Real) :
  let Rfree := realized_interest_factor params kNrm
  kinked_interest_rate params kNrm Rfree :=
by
  sorry

axiom CRRA_utility : Real → Real → Real

axiom discount_factor : Real

def value_function (params : Parameters) (arrival : ArrivalState) : Real :=
  axiom_value : Real

def bellman_equation (params : Parameters) (arrival : ArrivalState) : Prop :=
  let expected_continuation := axiom_expected_value : Real
  value_function params arrival = 
    let decision := transition_to_decision params arrival axiom_shocks
    let cNrm := optimal_consumption decision
    let cont := apply_control decision cNrm
    CRRA_utility cNrm axiom_risk_aversion + 
      discount_factor * RealPos.toReal params.LivPrb * expected_continuation

theorem bellman_optimality (params : Parameters) (arrival : ArrivalState) :
  bellman_equation params arrival :=
by
  sorry

def consumption_feasible (decision : DecisionState) (cNrm : Real) : Prop :=
  cNrm ≥ zero ∧ cNrm ≤ decision.mNrm

theorem optimal_consumption_feasible (params : Parameters) (arrival : ArrivalState) (shocks : IncShkDstn) :
  let decision := transition_to_decision params arrival shocks
  let cNrm := optimal_consumption decision
  consumption_feasible decision cNrm :=
by
  sorry

def permanent_income_evolution (params : Parameters) (pLvlPrev : RealPos) (PermShk : PermShock) (pLvl : RealPos) : Prop :=
  RealPos.toReal pLvl = RealPos.toReal pLvlPrev * RealPos.toReal params.PermGroFac * RealPos.toReal (PermShock.toRealPos PermShk)

theorem permanent_income_random_walk (params : Parameters) (arrival : ArrivalState) (shocks : IncShkDstn) :
  let decision := transition_to_decision params arrival shocks
  let (PermShk, _) := sample_IncShkDstn shocks
  permanent_income_evolution params arrival.pLvlPrev PermShk decision.pLvl :=
by
  sorry

axiom shock_independence : ∀ (shocks : IncShkDstn), 
  axiom_independent : Prop

axiom shock_positive_support : ∀ (shocks : IncShkDstn),
  let (PermShk, TranShk) := sample_IncShkDstn shocks
  (RealPos.toReal (PermShock.toRealPos PermShk) > zero) ∧ 
  (RealPos.toReal (TranShock.toRealPos TranShk) > zero)

def normalization_invariance (params : Parameters) : Prop :=
  ∀ (arrival : ArrivalState) (scale : RealPos),
    let scaled_pLvl := axiom_scaled_pLvl : RealPos
    let scaled_arrival := { kNrm := arrival.kNrm, pLvlPrev := scaled_pLvl }
    optimal_consumption (transition_to_decision params arrival axiom_shocks) =
    optimal_consumption (transition_to_decision params scaled_arrival axiom_shocks)

theorem consumption_function_homogeneous (params : Parameters) :
  normalization_invariance params :=
by
  sorry
