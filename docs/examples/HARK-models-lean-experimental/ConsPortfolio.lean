/-!
# ConsPortfolio — Lean 4 Formalization

Auto-generated from HARK model specification.
State spaces, transitions, and Bellman structure.
-/

-- ConsPortfolio: Consumption-saving with risky and risk-free assets
-- Formal Lean 4 specification

-- State spaces

axiom NormalizedWealth : Type
axiom PermanentIncome : Type
axiom RiskyShare : Type

-- We assume normalized wealth, permanent income, and risky shares are nonnegative reals
-- with appropriate constraints, but we leave them abstract for now

-- Arrival state: (kNrm, pLvlPrev, SharePrev)
def ArrivalState : Type := NormalizedWealth × PermanentIncome × RiskyShare

-- Decision state: (mNrm, pLvl, SharePrev, Adjust)
def DecisionState : Type := NormalizedWealth × PermanentIncome × RiskyShare × Bool

-- Continuation state: (aNrm, pLvl, Share)
def ContinuationState : Type := NormalizedWealth × PermanentIncome × RiskyShare

-- Action space: (cNrm, Share)
def Action : Type := NormalizedWealth × RiskyShare

-- Parameters

axiom Rfree : Real
axiom PermGroFac : Real
axiom LivPrb : Real
axiom AdjustPrb : Real

-- Parameter constraints
axiom Rfree_pos : Rfree > 0
axiom PermGroFac_pos : PermGroFac > 0
axiom LivPrb_prob : 0 ≤ LivPrb ∧ LivPrb ≤ 1
axiom AdjustPrb_prob : 0 ≤ AdjustPrb ∧ AdjustPrb ≤ 1

-- Shock types

axiom PermShk : Type
axiom TranShk : Type
axiom RiskyReturn : Type

-- Joint shock distribution
axiom ShockDstn : Type
axiom shock_sample : ShockDstn → (PermShk × TranShk × RiskyReturn)

-- Initial distributions
axiom pLvlInitDstn : Type
axiom kNrmInitDstn : Type

-- Value conversion functions (abstract mappings from shock types to Real)
axiom perm_to_real : PermShk → Real
axiom tran_to_real : TranShk → Real
axiom risky_to_real : RiskyReturn → Real

axiom kNrm_to_real : NormalizedWealth → Real
axiom pLvl_to_real : PermanentIncome → Real
axiom share_to_real : RiskyShare → Real

axiom real_to_kNrm : Real → NormalizedWealth
axiom real_to_pLvl : Real → PermanentIncome
axiom real_to_share : Real → RiskyShare

-- Policy functions

axiom cFuncFxd : NormalizedWealth → RiskyShare → NormalizedWealth
axiom cFuncAdj : NormalizedWealth → NormalizedWealth
axiom ShareFuncAdj : NormalizedWealth → RiskyShare
axiom ShareFuncFxd : NormalizedWealth → RiskyShare → RiskyShare

-- Transition dynamics from arrival to decision state

def portfolio_return (Risky : RiskyReturn) (SharePrev : RiskyShare) : Real :=
  let R := risky_to_real Risky
  let s := share_to_real SharePrev
  Rfree + (R - Rfree) * s

def permanent_income_growth (PermShk : PermShk) : Real :=
  PermGroFac * (perm_to_real PermShk)

def normalized_bank_balances (kNrm : NormalizedWealth) (Rport G : Real) : Real :=
  (kNrm_to_real kNrm) * Rport / G

def normalized_market_resources (bNrm yNrm : Real) : Real :=
  bNrm + yNrm

def arrival_to_decision (arr : ArrivalState) (shocks : PermShk × TranShk × RiskyReturn) (adjust : Bool) : DecisionState :=
  let (kNrm, pLvlPrev, SharePrev) := arr
  let (PermShk, TranShk, Risky) := shocks
  let yNrm := tran_to_real TranShk
  let G := permanent_income_growth PermShk
  let pLvl := real_to_pLvl ((pLvl_to_real pLvlPrev) * G)
  let Rport := portfolio_return Risky SharePrev
  let bNrm := normalized_bank_balances kNrm Rport G
  let mNrm := real_to_kNrm (normalized_market_resources bNrm yNrm)
  (mNrm, pLvl, SharePrev, adjust)

-- Decision rule: compute action from decision state

def decision_rule (dec : DecisionState) : Action :=
  let (mNrm, _pLvl, SharePrev, Adjust) := dec
  let cNrmF := cFuncFxd mNrm SharePrev
  let ShareF := ShareFuncFxd mNrm SharePrev
  let cNrmA := cFuncAdj mNrm
  let ShareA := ShareFuncAdj mNrm
  let cNrm := if Adjust then cNrmA else cNrmF
  let Share := if Adjust then ShareA else ShareF
  (cNrm, Share)

-- Transition from decision state and action to continuation state

def decision_to_continuation (dec : DecisionState) (act : Action) : ContinuationState :=
  let (mNrm, pLvl, _SharePrev, _Adjust) := dec
  let (cNrm, Share) := act
  let aNrm := real_to_kNrm ((kNrm_to_real mNrm) - (kNrm_to_real cNrm))
  (aNrm, pLvl, Share)

-- Continuation to next arrival (twist)

def continuation_to_arrival (cont : ContinuationState) (live : Bool) : ArrivalState :=
  let (aNrm, pLvl, Share) := cont
  if live then
    (aNrm, pLvl, Share)
  else
    -- Terminal state: death ends the process; we model as transition to absorbing state
    (aNrm, pLvl, Share)

-- Feasibility constraint

def feasible_action (dec : DecisionState) (act : Action) : Prop :=
  let (mNrm, _pLvl, _SharePrev, _Adjust) := dec
  let (cNrm, Share) := act
  let c_val := kNrm_to_real cNrm
  let m_val := kNrm_to_real mNrm
  let s_val := share_to_real Share
  0 ≤ c_val ∧ c_val ≤ m_val ∧ 0 ≤ s_val ∧ s_val ≤ 1

-- Utility function (CRRA assumed, but left abstract)

axiom u : Real → Real

-- Discount factor
axiom β : Real
axiom β_discount : 0 < β ∧ β < 1

-- Value function (to be determined via Bellman equation)

axiom V : DecisionState → Real

-- Bellman equation: the value function satisfies the recursive optimality condition
-- V(dec) = max_{act ∈ feasible} { u(c * P) + β * E[ live * V(arrival_to_decision(continuation_to_arrival(cont, live), shocks', adjust')) ] }
-- where cont = decision_to_continuation(dec, act)
--
-- We state this as a formal definition for the optimal value

def bellman_operator (V_next : DecisionState → Real) (dec : DecisionState) : Real :=
  let (mNrm, pLvl, SharePrev, Adjust) := dec
  let act := decision_rule dec
  let (cNrm, Share) := act
  let c_level := (kNrm_to_real cNrm) * (pLvl_to_real pLvl)
  let flow_utility := u c_level
  let cont := decision_to_continuation dec act
  -- Expected continuation value would involve integrating over shocks and survival
  -- We represent this abstractly as E_cont (to be formalized with measure theory)
  let E_cont := 0  -- placeholder for E[ LivPrb * V_next(next_dec) ]
  flow_utility + β * E_cont

-- Bellman fixed point property

theorem bellman_fixed_point :
  ∀ dec : DecisionState, V dec = bellman_operator V dec := by
  sorry

-- Optimality of the decision rule: the policy functions achieve the Bellman maximum

theorem decision_rule_optimal (dec : DecisionState) :
  let act := decision_rule dec
  feasible_action dec act ∧
  ∀ act' : Action, feasible_action dec act' →
    let (cNrm, _Share) := act
    let (cNrm', _Share') := act'
    let (mNrm, pLvl, _SharePrev, _Adjust) := dec
    let c_level := (kNrm_to_real cNrm) * (pLvl_to_real pLvl)
    let c_level' := (kNrm_to_real cNrm') * (pLvl_to_real pLvl)
    u c_level ≥ u c_level' := by
  sorry

-- Budget constraint: end-of-period assets equal market resources minus consumption

theorem budget_constraint (dec : DecisionState) :
  let act := decision_rule dec
  let (mNrm, pLvl, _SharePrev, _Adjust) := dec
  let (cNrm, _Share) := act
  let cont := decision_to_continuation dec act
  let (aNrm, _pLvl_cont, _Share_cont) := cont
  kNrm_to_real aNrm = kNrm_to_real mNrm - kNrm_to_real cNrm := by
  sorry

-- Portfolio return consistency: Rport = Rfree + (Risky - Rfree) * SharePrev

theorem portfolio_return_formula (Risky : RiskyReturn) (SharePrev : RiskyShare) :
  portfolio_return Risky SharePrev = Rfree + (risky_to_real Risky - Rfree) * share_to_real SharePrev := by
  sorry

-- Permanent income evolution: pLvl = pLvlPrev * PermGroFac * PermShk

theorem permanent_income_evolution (pLvlPrev : PermanentIncome) (PermShk : PermShk) :
  let G := permanent_income_growth PermShk
  let pLvl := real_to_pLvl ((pLvl_to_real pLvlPrev) * G)
  pLvl_to_real pLvl = (pLvl_to_real pLvlPrev) * PermGroFac * (perm_to_real PermShk) := by
  sorry

-- Shock distribution structure: the joint distribution of (PermShk, TranShk, Risky) is given by ShockDstn

axiom shock_dist_well_defined : ∀ dstn : ShockDstn,
  let (ψ, θ, R) := shock_sample dstn
  perm_to_real ψ > 0 ∧ tran_to_real θ ≥ 0 ∧ risky_to_real R > 0

-- Adjustment probability: agent can adjust portfolio with probability AdjustPrb

axiom adjustment_probability : ∀ dec : DecisionState,
  let (_mNrm, _pLvl, _SharePrev, Adjust) := dec
  (Adjust = true → True) ∧ (Adjust = false → True)  -- placeholder for probabilistic statement

-- Survival probability: agent survives to next period with probability LivPrb

axiom survival_probability : ∀ live : Bool,
  (live = true → True) ∧ (live = false → True)  -- placeholder for probabilistic statement

-- Consumption function properties (to be verified)

theorem cFuncAdj_nonneg : ∀ mNrm : NormalizedWealth,
  kNrm_to_real (cFuncAdj mNrm) ≥ 0 := by
  sorry

theorem cFuncAdj_bounded : ∀ mNrm : NormalizedWealth,
  kNrm_to_real (cFuncAdj mNrm) ≤ kNrm_to_real mNrm := by
  sorry

theorem cFuncFxd_nonneg : ∀ mNrm : NormalizedWealth, ∀ SharePrev : RiskyShare,
  kNrm_to_real (cFuncFxd mNrm SharePrev) ≥ 0 := by
  sorry

theorem cFuncFxd_bounded : ∀ mNrm : NormalizedWealth, ∀ SharePrev : RiskyShare,
  kNrm_to_real (cFuncFxd mNrm SharePrev) ≤ kNrm_to_real mNrm := by
  sorry

-- Risky share function properties

theorem ShareFuncAdj_in_range : ∀ mNrm : NormalizedWealth,
  let s := share_to_real (ShareFuncAdj mNrm)
  0 ≤ s ∧ s ≤ 1 := by
  sorry

theorem ShareFuncFxd_in_range : ∀ mNrm : NormalizedWealth, ∀ SharePrev : RiskyShare,
  let s := share_to_real (ShareFuncFxd mNrm SharePrev)
  0 ≤ s ∧ s ≤ 1 := by
  sorry

-- State transition respects feasibility

theorem state_transition_feasible :
  ∀ arr : ArrivalState,
  ∀ shocks : PermShk × TranShk × RiskyReturn,
  ∀ adjust : Bool,
  let dec := arrival_to_decision arr shocks adjust
  let act := decision_rule dec
  feasible_action dec act := by
  sorry

-- End of ConsPortfolio formalization
