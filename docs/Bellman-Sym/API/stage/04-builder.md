---
title: A builder
tags:
  - docs/api
  - builder
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# A builder

> [!summary]
> A builder is the operator one [block](../../01-stage.md#3-builder-blocks) denotes, reached from the [perch](../../../wiki/perch.md) its edge leaves, the edge being the step from that perch to the next ([The builders graphs](03-build.md) §2): `stage.dcsn.builder.bwd`, a path that reads the pair of perches the builder joins, `stage.builder["cntn", "dcsn"]`. It answers the operations inside it, its inputs and outputs, its printed record, its drawing and its kernels, and opens to a finer grain by an attribute; an operation inside it is read by its name as a key. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`, and §4 from `applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl`.

> [!info]- Relationship with other documents
> **Builds on** — [The builders graphs](03-build.md): the pairs and the perch paths that reach the builders, and the graphs that hold them.
> **Used by** — [A piece](05-piece.md): what an operation inside a builder answers.
> **Formal account** — [Operators and builders](../../../bellman-calculus/05-Operators%20and%20builders.md): the operator a builder denotes.
> **See also** — [API](../index.md) §2.4: every path of the stage object in one table.

A [builder](../../../wiki/builder.md) is one box of a builders graph at the builder grain. Inside it stand the **operations** it applies in order, each a primitive operator such as a pullback, an aggregation or an evaluation; [Operations](../../reference/operations.md) lists the kinds. Where a line of the block is tagged `!node`, marking a named computation of its own, the builder also holds a **sub-builder**, a box that keeps that computation closed.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 What a builder answers

`list()` names the operations inside the builder in order of application, each under the key that reaches it, with its kind and the function it writes. `signature()` answers the functions the builder reads and writes, each with its type: the value functions alone, each on its own [wire](02-initial.md), while a derivative the file states for a value stands at the builder's evaluation and on no wire; for the decision builder it is the signature of the operator at a policy, and it names no policy.

```python
decision = stage.dcsn.builder.bwd
print(repr(decision))
print(decision.list())
print(decision.signature())
```

```text
Builder('cons', 'cntn_to_dcsn')
1  Pullback     primitive
2  Aggregation  primitive  → 𝑉
3  Evaluation   primitive  → 𝑉
in         𝑉≻ : Xa → [−∞, ∞)
out        𝑉 : Xm → [−∞, ∞)
```

A **builder at a policy** is a backward builder or a push-forward stated at the policy function: wherever its lines are written in the control, the policy stands in place of that coordinate. There is one such operator for each policy, all with the same inputs and outputs, which is why the calculus writes the policy as a subscript on the decision operator, and why policy iteration, which holds the policy fixed while it computes the value under that policy, can be stated at all. Its `signature()` therefore says nothing about the policy, whose type is printed on the policy's own wire, the output of the policy builder (§2), and on no line of the builder at a policy. The name the builder uses for the policy is a free name, declared by no header of the builder: the elaboration resolves it to the line of the policy block that defines it, and the function that stands in its place in a computation is supplied later, by the method or by the realization, the later step in which a numerical routine is supplied for each operator, as calibration supplies the value of a parameter. The policy is not a parameter of the model, one of the declared constants that `stage.par` lists ([Parameters and settings](06-par-and-settings.md)).

`denote()` answers the builder's printed record, its **card**: the functions it reads and writes, the policy it is stated at, the law of motion it reads, the operations within it with their rules, the conditions the construction has not established, and the lines of the file it realizes. `print(decision)` prints the same card.

```python
print(decision.denote())
```

```text
STAGE cons / BACKWARD BUILDER cntn → dcsn (cntn_to_dcsn)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → [−∞, ∞)
       ───────────────────────────────────────────────────
  out  𝑉   : Xm → [−∞, ∞)

At
  𝑐  : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Operations
  1  Pullback
     in: 𝑉≻                             out: 𝑉≻ ∘ 𝑔≻(·, 𝑐)
     ─────────────────────────────────────────────────────
     rule: (𝑉≻ ∘ 𝑔≻(·, 𝑐))(m_d) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))

  2  Aggregation
     in: (1)                            out: 𝑉
     ─────────────────────────────────────────────────────
     rule: 𝑉(m_d) = 𝑢(𝑐(m_d)) + 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))

  3  Evaluation
     in: 𝑉                              out: 𝑉
     ─────────────────────────────────────────────────────
     rule: 𝑉 : Xm → [−∞, ∞)
     derivative: D_{m_d}𝑉(m_d) = 𝑑𝑢(𝑐(m_d))
                 cntn_to_dcsn.marginal, marginal-reading

Conditions
  Aggregation  𝑉(m_d) ∈ [−∞, ∞)
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  22  V        = 𝑢(c) + V[>]  :: [id=value]
  23  D_{m_d}V = 𝑑𝑢(c)        :: [id=marginal]

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  𝑢     cons:function:𝑢
  𝑑𝑢    cons:function:𝑑𝑢
  Γ     cons:correspondence:Γ
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The card's title names the stage, the builder's direction and the builder by the pair of perches it joins, `cntn → dcsn`, with the id of its block in brackets, while the policy builder's card is titled by its key, `POLICY BUILDER policy` ([The builders graphs](03-build.md) §1). The card's `Operations` section lists the operations within the builder, one entry each, with a blank line between two entries. An entry opens with its number and its name; the next line gives its inputs after `in:` and its outputs after `out:`, `out:` standing at column 40, or on the next line where the inputs or the outputs leave it no room there; a short line follows, and every short line of a card ends at the same column; then the rule the operation applies stands after `rule:`, with the set on which it holds, `on …`, at the right margin or under the rule; on an evaluation, a derivative the file states for the value stands after `derivative:`, with the line that states it and its condition `marginal-reading`. The lines state the wiring: the name after `out:` in one entry is the name after `in:` in the entry that reads it, and an output the file does not name is written, in the entry that reads it, as the number of the entry that produced it, `(1)`, as a paper cites an equation by its number. Where the operations form a chain, each one's outputs being the next one's inputs, the same wires in the same order, the entries stand in the order they are applied; otherwise each stands after every entry that writes a wire it reads. On a builders graph's card each builder is an entry with no number, and its operations stand beneath it, numbered and set further in ([The builders graphs](03-build.md) §3).

`diagram()` answers the drawing of the builder's interior, a `Drawing`; `obligations()` the conditions of its operations and of the lines it realizes; `methods` the methods bound at it or inside it, empty before [methodization](07-methods.md); and `box` the DisCoPy box itself, an object of the diagram library the package keeps its graphs in ([The initial diagrams](02-initial.md) §2). In the drawing an aggregation is labeled `Value aggregation 𝐺` where it produces value functions at a perch, as in the two backward builders, and `Apply 𝐺` otherwise, as in the policy builder; where one builder holds several aggregations, the label names the statement each aggregates, `Apply 𝐺 of the statement InvEuler`, so that the two aggregations of the policy builder are told apart. The names of the operations carry the same distinction (§2). A pullback is labeled by the function it pulls back and the map it pulls back along: `Pullback of 𝑉≻ along 𝑔 at 𝑐` in the decision builder, and `Pullback of 𝑐 along 𝑚_d≻` for the identification of the policy builder, which pulls the policy back along the map from each saving to its cash on hand and not along the law of motion (§2). A stage's two builders graphs, of which each builder is a box, are also read interactively in Google's Model Explorer, where each builder opens to its operations and a selected operation shows the rows of its card; the drawing remains the figure of this page ([The view in Model Explorer](10-model-explorer.md)).

## 2 The policy builder

`stage.dcsn.builder.policy` is the policy builder, the builder whose outputs are the controls. Its `signature()` carries the policy's type, the set of feasible policies where the file declares a feasibility correspondence, `Γ` here, beside the value functions it reads. The clause `c(m_d) ∈ Γ(m_d)` is the feasibility condition: the consumption the policy chooses lies in the feasible set that the correspondence `Γ(x) := (0, x]` of the file gives.

```python
print(repr(stage.dcsn.builder.policy))
print(stage.dcsn.builder.policy.signature())
```

```text
Builder('cons', 'policy')
in         𝑉≻ : Xa → [−∞, ∞)
out        𝑐(m_d) : 𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})
```

Its operations, by the names that reach them: an operation that belongs to one line of the policy block takes that line's id, and the two aggregations are told apart by their lines.

```python
for name in stage.dcsn.builder.policy.list():
    print(name)
```

```text
InvEuler:Aggregation
endoggrid:Aggregation
cons_choice:Pullback
Evaluation
```

The four operations state the policy as the lines of the block write it, and [Operations](../../reference/operations.md) §4 states how each such line is read. `InvEuler:Aggregation` is formed by the **candidate line** `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`, which states the candidate consumption at each saving from the derivative term `D_{a}V[>]`, the derivative of the continuation value in savings. Its clause `⟂ a >= 0`, the complementary-slackness condition of the borrowing constraint, admits the interior value `𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a))` alone at a positive saving and every positive value up to it at zero saving, so the operation's output is typed as a correspondence, a map to sets, `Xa ⇉ ℝ₊₊` ([Constraints](../../10-constraints.md) §4.3). `endoggrid:Aggregation` is formed by the **grid line** `m_d[>] = a + c[>]`, the cash on hand at each saving and each value admitted there. `cons_choice:Pullback` is formed by the **identification** `c = c[>]`: it reads the policy at that cash on hand and equates it with the candidate, a relation that must hold at every saving and every value admitted there, and its `signature()` answers the set of the feasible policies that satisfy it, which may be empty or hold several. `Evaluation` places that set in its declared carrier and selects no member; the method bound there, `!egm` in the application's methods file, stores its numerical representation of the function and asserts nothing about the set ([Methods and places](07-methods.md) §2; [Methodization](../../04-methodization.md) §3).

```python
policy = stage.dcsn.builder.policy
print(policy["InvEuler:Aggregation"].signature())
print(policy["cons_choice:Pullback"].signature())
```

```text
in         𝑉≻ : Xa → [−∞, ∞)
out        𝑐≻ : Xa ⇉ ℝ₊₊
in         𝑐≻ : Xa ⇉ ℝ₊₊
in         𝑚_d≻ : Xa ⇉ Xm
out        {f ∈ {c ∈ (Xm → ℝ₊₊
           ) | c(m_d) ∈ Γ(m_d)} | ∀ a ∈ Xa, x ∈ 𝑐≻(a): (f(a + x) = x)} :
           𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})
```

The line `optimality`, marked `!doc`, forms no operation. An `argmax` line that is not marked `!doc` forms an operation of the kind `Argmax`, whose output is the set of maximizing policies, as `choice:Argmax` does in the policy builder of `applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl`.

## 3 A forward builder at a policy

`stage.dcsn.builder.fwd` carries the measure at decision forward through the law of motion at the policy. It answers the same verbs, and `state_choice_measure()` besides: the joint measure of the decision state and the control under the policy the builder is stated at, the measure against which a simulated moment of a control is an integral.

```python
print(stage.dcsn.builder.fwd.list())
print(stage.dcsn.builder.fwd.state_choice_measure())
```

```text
1  Pushforward  primitive  → μ≻
mu
  ↦ measure on {m_d, c ∈ Xm × ℝ₊₊ | c ∈ Γ(m_d)} given by
    B ↦ mu({m_d ∈ Xm | (m_d ↦ (m_d, c(m_d)))(m_d) ∈ B})
```

## 4 Grains and keys

`primitives` answers the builder with every sub-builder opened and `sub_builders` the builder with each `!node` line kept as a box; each answers the same verbs. An operation is read by its name after the builder's own, the kind compared without regard to case, `decision["pullback"]`, or by the whole name. A tuple of keys reads one level further down per element: the first names a sub-builder, the next an operation inside it. The consumption stage writes no `!node` line, so this section reads the smooth-ambiguity savings stage, whose decision builder computes a risk certainty equivalent `risk_ce` and an ambiguity certainty equivalent `ambiguity_ce`, each marked `!node`.

```python
sa = elaborate_stage(load_stage("applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl"))
print(sa.dcsn.builder.bwd.list())
print(repr(sa.dcsn.builder.bwd["risk_ce"]))
print(repr(sa.dcsn.builder.bwd["risk_ce", "expectation:1"]))
print(repr(sa.dcsn.builder.bwd.primitives))
```

```text
    risk_ce          sub-builder  → 𝐶𝐸(m_d, ν)
 1    Pullback       primitive
 2    Aggregation:1  primitive
 3    Expectation:1  primitive
 4    Aggregation    primitive
 5    Evaluation     primitive    → 𝐶𝐸
    ambiguity_ce     sub-builder  → 𝐴𝑀𝐵(m_d)
 6    Aggregation:1  primitive
 7    Expectation:1  primitive
 8    Aggregation    primitive
 9    Evaluation     primitive    → 𝐴𝑀𝐵
10  Aggregation      primitive    → 𝑉
11  Evaluation       primitive    → 𝑉
SubBuilder('sa_savings', 'cntn_to_dcsn.risk_ce')
Operator('sa_savings', 'cntn_to_dcsn.risk_ce:Expectation:1')
Builder('sa_savings', 'cntn_to_dcsn', primitives)
```

A key that names no operation, or two, is refused with a `KeyError` that names the keys the builder holds.

A sub-builder is one named intermediate result: the construction keeps the operations of a line marked `!node` inside a box of their own, named `<block id>.<line id>`, and the two sub-builders are the first two boxes inside the decision builder. In this stage the gross return `Ψ` is lognormal with an uncertain log mean `ν`, and `γ` is risk aversion. Each sub-builder has its own card:

```python
print(sa.dcsn.builder.bwd["risk_ce"].denote())
```

```text
STAGE sa_savings / BACKWARD BUILDER cntn → dcsn (cntn_to_dcsn) / risk_ce
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : ℝ₊₊ → ℝ₊₊
       ───────────────────────────────────────────────────────────────────
  out  𝐶𝐸  : ℝ₊₊ × ℝ → ℝ₊₊

At
  𝑐  : ℝ₊₊ → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Operations
  1  Pullback
     in: 𝑉≻                             out: 𝑉≻ ∘ 𝑔≻(·, 𝑐, ·)
     ─────────────────────────────────────────────────────────────────────
     rule: (𝑉≻ ∘ 𝑔≻(·, 𝑐, ·))(m_d, Ψ) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))

  2  Aggregation:1
     in: (1)
     out: (m_d, Ψ) ↦ 𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))^(1 − γ)
     ─────────────────────────────────────────────────────────────────────
     rule: (m_d, Ψ) ↦ 𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))^(1 − γ)

  3  Expectation:1
     in: (2)                            out: (m_d, ν) ↦ E_{Ψ}[(2)(m_d, Ψ)]
     ─────────────────────────────────────────────────────────────────────
     rule: (3)(m_d, ν) = E_{Ψ}[(2)(m_d, Ψ)]

  4  Aggregation
     in: (3)                            out: 𝐶𝐸
     ─────────────────────────────────────────────────────────────────────
     rule: 𝐶𝐸 = E_{Ψ}[𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))^(1 − γ)]^(1/(1 − γ))
           on (m_d, ν) ∈ ℝ₊₊ × ℝ

  5  Evaluation
     in: 𝐶𝐸                             out: 𝐶𝐸
     ─────────────────────────────────────────────────────────────────────
     rule: 𝐶𝐸 : ℝ₊₊ × ℝ → ℝ₊₊
──────────────────────────────────────────────────────────────────────────────
Source  sa_savings.bl
  27  CE = E_{Ψ}(V[>]^(1-γ))^(1/(1-γ))  :: [id=risk_ce, !node]

Definitions referenced
  γ     sa_savings:parameter:γ
  ν     sa_savings:distribution:ν
  Ψ     sa_savings:distribution:Ψ
  Γ     sa_savings:correspondence:Γ
  𝑔≻    sa_savings:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

An output the file does not name is written as what produced it: an aggregation's result as the map it computes, `(m_d, Ψ) ↦ 𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))^(1 − γ)`, and an expectation's as the expectation of the result it reads, named by the box that wrote it. The expectation symbol `E` is an operator symbol and stays roman, while the functions beside it are italic, and the type on the same line gives the sets the function is defined on. The expectation box is where the shock is integrated: the backward graph takes the expectation over `Ψ` here, and the forward graph's corresponding box extends the measure by the same declared distribution ([A piece](05-piece.md) §1). A pair of keys reaches the operation, the first naming the sub-builder and the rest resolved inside it:

```python
print(sa.dcsn.builder.bwd["risk_ce", "expectation:1"].denote())
```

```text
STAGE sa_savings / BACKWARD BUILDER cntn → dcsn (cntn_to_dcsn)
  / risk_ce:Expectation:1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   (m_d, Ψ) ↦ 𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))^(1 − γ)
         : ℝ₊₊ × ℝ₊₊ → ℝ₊₊
       ───────────────────────────────────────────────
  out  (m_d, ν) ↦ E_{Ψ}[risk_ce:Aggregation:1(m_d, Ψ)]
         : ℝ₊₊ × ℝ → ℝ₊₊

Rule
  risk_ce:Expectation:1(m_d, ν) = E_{Ψ}[risk_ce:Aggregation:1(m_d, Ψ)]
──────────────────────────────────────────────────────────────────────────────
Source  sa_savings.bl
  14  Ψ ~ LogNormal(ν, σ_Ψ)
  27  CE = E_{Ψ}(V[>]^(1-γ))^(1/(1-γ))  :: [id=risk_ce, !node]

Definitions referenced
  γ     sa_savings:parameter:γ
  ν     sa_savings:distribution:ν
  Ψ     sa_savings:distribution:Ψ
  𝑔≻    sa_savings:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 5 The kernels of a builder

`kernels()` answers one record of the builder's kernels, from which a numerical operator is built with no stage in hand: each operation in the order it is applied, with its printed kernel and the wires it reads and writes, and, where its kernel is an explicit function, its function with the names of its arguments and outputs, or, for a row that states a relation its output satisfies, such as the identification of a policy block, or a row that reads a derivative term, such as the candidate line `InvEuler`, whose `compile_kernel()` is refused under `kernel-form` ([A piece](05-piece.md) §2), its printed relation; then the parameters with their values and the declared sets its operations are read on. The record refers to no stage, so cloudpickle saves it and another process reads it. The endogenous-grid step of the portfolio–consumption application is built from two such records of a specified version by one call of `asva`, the numerical toolkit installed beside the package, `asva.egm(specified.dcsn.builder.policy.kernels(), specified.dcsn.builder.bwd.kernels(), savings, evaluation)`, the caller reading the savings grid and the evaluation grid from the settings. [A piece](05-piece.md) §2 gives one operation's kernel as a function, and the lesson `tutorials/topics/kernels.ipynb` of the repository composes one step of the decision builder from its two kernels, compiles them with Numba and passes the values of a second calibration without compiling again; [Solutions at the perches](../../11-solutions-at-the-perches.md) describes the dictionaries in which a solver keeps what the kernels compute.
