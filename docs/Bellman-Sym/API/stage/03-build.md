---
title: The builders graphs
tags:
  - docs/api
  - builder
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# The builders graphs

> [!summary]
> `stage.builder` reaches each builder of a stage by the ordered pair of [perches](../../../wiki/perch.md) it joins, `stage.builder["cntn", "dcsn"]`, and each perch reaches the builders of the edge that leaves it, `stage.dcsn.builder.bwd`, a path defined as one such pair. The builders stand in two builders graphs: `stage.builder.bwd`, the backward builders on value functions that a solution applies, and `stage.builder.fwd`, the forward builders on measures that a simulation applies. Each graph answers the verbs of §3 and opens to a finer grain by an attribute. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the object `stage` below; [The initial diagrams](02-initial.md): the blocks these graphs read as operators.
> **Used by** — [A builder](04-builder.md) and [A piece](05-piece.md): what a builder and an operator inside it answer.
> **Formal account** — [Operators and builders](../../../bellman-calculus/05-Operators%20and%20builders.md): the operators these graphs denote.
> **See also** — [API](../index.md) §2.4: every path of the stage object in one table.

A **builders graph** holds the [blocks](../../01-stage.md#3-builder-blocks) of one direction as the operators they denote, one box per block. That box is the block's **builder**: in the backward graph an operator on value functions, in the forward graph an operator on finite measures over the states. The block and its builder share the block's id and are two objects, so that a request about the block, `stage.initial.backward["cntn_to_dcsn"]`, and one about the builder, `stage.builder["cntn", "dcsn"]`, are different requests. Reaching a builder neither solves nor simulates anything; it answers what the operator is.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 The builders by their two ends

A builder joins two perches in order: it reads the objects of the first perch and writes those of the second, as the header of its block declares them. The block `cntn_to_dcsn` reads the value at the continuation perch, `!cntn`, and writes the value at the decision perch, `!dcsn`, so its builder joins `cntn` to `dcsn`. That ordered pair is the builder's identity, and `stage.builder` is the mapping from each pair to the builder that joins it: `stage.builder["cntn", "dcsn"]` is the backward builder from continuation to decision, whatever id its block has. The words of a pair are the three perch words `"arvl"`, `"dcsn"` and `"cntn"`, which `bellman.stage` exports, so that after `from bellman.stage import cntn, dcsn` the same builder is `stage.builder[cntn, dcsn]`.

```python
print(repr(stage.builder))
print(stage.builder.view())
```

```text
Builders('cons', 5 by their perches)
arvl_to_dcsn   arvl → dcsn, fwd
dcsn_to_cntn   dcsn → cntn, fwd
cntn_to_dcsn   cntn → dcsn, bwd
dcsn_to_arvl   dcsn → arvl, bwd
policy         policy, bwd
```

The short form counts the builders. `view()` prints one line for each builder, the forward builders first: the id of the block; the pair, written `source → target`, or for the policy builder its key, `policy`; and the word of the builder's direction, `fwd` for a forward builder and `bwd` for a backward one. `list()` answers that listing itself, a mapping from the id of each block to the pair and the direction word, which `stage.list()` shows under `builder` ([The stage](01-the-stage.md) §4); `methods` answers the methods bound within the builders of both graphs ([Methods and places](07-methods.md) §3). The policy block joins the same two perches as the block `cntn_to_dcsn`, reading at the continuation perch and writing the controls at the decision perch, so the policy builder is read by a key of its own, the word `"policy"`: `stage.builder["policy"]` and the attribute `stage.builder.policy` answer the same builder, and the pair `("cntn", "dcsn")` reads the decision builder alone.

In the notation of the calculus, the five builders of the consumption stage are these; $\mathbb T_{\succ,\pi}$ is the decision operator at a policy $\pi$ ([A builder](04-builder.md) §1).

| Read as | Block | The builder | In the calculus |
|---|---|---|---|
| `stage.builder["arvl", "dcsn"]` | `arvl_to_dcsn` | carries the measure at arrival to the measure at decision | $\mathbb M_\prec$ |
| `stage.builder["dcsn", "cntn"]` | `dcsn_to_cntn` | carries the measure at decision to the measure at continuation, at a policy | $\mathbb M_{\succ,\pi}$ |
| `stage.builder["cntn", "dcsn"]` | `cntn_to_dcsn` | constructs the value functions at decision from those at continuation, at a policy | $\mathbb T_{\succ,\pi}$ |
| `stage.builder["dcsn", "arvl"]` | `dcsn_to_arvl` | constructs the value functions at arrival from those at decision | $\mathbb T_\prec$ |
| `stage.builder.policy` | `policy` | constructs the policy, the controls as functions of the decision state | the policy builder |

The title of a builder's card prints its pair and after it, in brackets, the id of its block; the policy builder's title prints its key alone, `POLICY BUILDER policy`:

```python
decision = stage.builder["cntn", "dcsn"]
print(repr(decision))
print(str(decision.denote()).splitlines()[0])
```

```text
Builder('cons', 'cntn_to_dcsn')
STAGE cons / BACKWARD BUILDER cntn → dcsn (cntn_to_dcsn)
```

The short form of a builder names the id of its block; [A builder](04-builder.md) §1 prints the whole card. A pair that no builder joins is refused with a `KeyError` that names every builder of the stage by its pair, and the policy builder by its key, `policy`:

```python
try:
    stage.builder["cntn", "arvl"]
except KeyError as refusal:
    print(refusal.args[0])
```

```text
stage 'cons': no builder joins cntn → arvl; the builders are arvl → dcsn, dcsn → cntn, cntn → dcsn, dcsn → arvl, policy
```

A pair that two builders join, as two forward blocks from arrival to decision may, is refused in the same way, and the refusal names the two builders, each with the key of its graph that reads it by the id of its block (§3). Where the construction refused the graph of one direction, a pair of that direction raises the construction's refusal, `NotConstructed` ([Refusals](../../reference/refusals.md)), while the pairs of the other direction still answer.

The declared builders, the operators the blocks of the stage file denote as elaboration builds them, are read by the same pairs through `stage.declared`: `stage.declared["cntn", "dcsn"]`, `stage.declared.policy` and `stage.declared.bwd` answer as `stage.builder` does. The two differ as soon as a methods file adds a line: a derivative line the file adds stands at the Evaluation of the operative builder and not at the declared one's, and the lines of a solution method stand in the operative builder in place of the stage file's, `stage.declared` keeping each builder as the stage file states it ([Methodization](../../04-methodization.md) §5; [Binding verbs](09-binding-verbs.md); [A builder](04-builder.md) §2). The card of a declared builder prints no binding, nor do the cards of the blocks and the lines of the initial diagrams, so that no binding changes them; their `methods` answers the methods the stage binds within them, which the cards of `stage.builder` print.

## 2 The perch paths

Each perch of the stage is an object of its own, `stage.arvl`, `stage.dcsn` and `stage.cntn`, and its `builder` reaches the builders of the edge that leaves it, the step from that perch to the next: `fwd` is the forward builder of the edge, which carries the measure at the perch to the measure at the next perch, and `bwd` its backward builder, which constructs the value functions at the perch from those at the next perch. At the decision perch, `policy` also reaches the policy builder. Each path is defined as one key of `stage.builder` and nothing else, so a path and its pair never disagree.

| Path | The key it reads | The builder |
|---|---|---|
| `stage.arvl.builder.fwd` | `stage.builder["arvl", "dcsn"]` | $\mathbb M_\prec$ |
| `stage.arvl.builder.bwd` | `stage.builder["dcsn", "arvl"]` | $\mathbb T_\prec$ |
| `stage.dcsn.builder.fwd` | `stage.builder["dcsn", "cntn"]` | $\mathbb M_{\succ,\pi}$ |
| `stage.dcsn.builder.bwd` | `stage.builder["cntn", "dcsn"]` | $\mathbb T_{\succ,\pi}$ |
| `stage.dcsn.builder.policy` | `stage.builder["policy"]`, which `stage.builder.policy` also reads | the policy builder |
| `stage.cntn.builder.fwd` | none | refused: the forward pass leaves the stage at continuation, and the [connector](../../../wiki/connector.md) identifies the measure at continuation with the next stage's arrival measure |
| `stage.cntn.builder.bwd` | none | refused: no value is built at continuation, and the connector identifies the continuation value with the next stage's arrival value |

`list()` names the paths of one perch, each with the key it reads, in a listing keyed by the path, and prints `none` at continuation, which no edge of the stage leaves:

```python
perches = {"arrival": stage.arvl, "decision": stage.dcsn, "continuation": stage.cntn}
for name, perch in perches.items():
    print(name)
    print(perch.builder.list())
print(stage.dcsn.builder.bwd == stage.builder["cntn", "dcsn"])
```

```text
arrival
stage.arvl.builder.fwd   arvl → dcsn
stage.arvl.builder.bwd   dcsn → arvl
decision
stage.dcsn.builder.fwd      dcsn → cntn
stage.dcsn.builder.bwd      cntn → dcsn
stage.dcsn.builder.policy   policy
continuation
none
True
```

The two paths at continuation are refused with the reasons of the table:

```python
for word in ("fwd", "bwd"):
    try:
        getattr(stage.cntn.builder, word)
    except AttributeError as refusal:
        print(refusal)
```

```text
stage 'cons': the forward pass leaves the stage at continuation, so `stage.cntn.builder.fwd` names no builder; the connector identifies the measure at continuation with the next stage's arrival measure
stage 'cons': no value is built at continuation, so `stage.cntn.builder.bwd` names no builder; the connector identifies the continuation value with the next stage's arrival value
```

The arrival perch refuses `policy` in the same way, since the policy builder stands at decision. A terminal stage writes no forward block from decision to continuation, so it refuses `stage.dcsn.builder.fwd`; the bequest stage of the durables application is one:

```python
bequest = elaborate_stage(load_stage("applications/durables/declaration/stages/bequest/bequest.bl"))
try:
    bequest.dcsn.builder.fwd
except AttributeError as refusal:
    print(refusal)
```

```text
stage 'bequest': no builder joins dcsn → cntn; like a terminal stage, the stage writes no forward block from decision to continuation, so `stage.dcsn.builder.fwd` names no builder
```

On a branching stage the decision edge still has one forward builder, which writes one measure for each branch: `stage.dcsn.builder.fwd` of the retirement choice `applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl` writes the measures `μ_work≻` and `μ_retire≻` ([Branching](../../05-branching.md)).

## 3 The two graphs

`stage.builder.bwd` is the backward builders graph, the builders a solution applies, on value functions, and `stage.builder.fwd` the forward builders graph, the builders a simulation applies, on measures; the policy builder stands in the backward graph. A builder is also a key of its graph by the id of its block, `stage.builder.bwd["cntn_to_dcsn"]`, which reaches each of two builders that join one pair.

```python
print(repr(stage.builder.bwd))
print(repr(stage.builder.fwd))
print(repr(stage.builder.bwd["cntn_to_dcsn"]))
```

```text
BuildersGraph('cons', 'backward')
BuildersGraph('cons', 'forward')
Builder('cons', 'cntn_to_dcsn')
```

The short form of a graph names the builders graph and its direction. A builders graph answers `list()`, its builders in order of application with the functions or measures each writes; `signature()`, the functions or measures it reads and those it writes, each with its type; `denote()`, its printed record, the operator the graph denotes with the builders within it; `diagram()`, its drawing, a `Drawing`; `obligations()`, the conditions its builders own together with those of the whole stage, each with its status; `methods`, the methods bound within it, which on this symbolic version are none ([Methods and places](07-methods.md) §3); and `graph`, the DisCoPy hypergraph, an object of the diagram library the package keeps its graphs in ([The initial diagrams](02-initial.md) §2).

```python
print(stage.builder.bwd.list())
print(stage.builder.bwd.signature())
print()
print(stage.builder.fwd.list())
print(stage.builder.fwd.signature())
print()
print(type(stage.builder.bwd.diagram()).__name__)
print(stage.builder.bwd.methods)
```

```text
1  cntn_to_dcsn  builder  → 𝑉
2  dcsn_to_arvl  builder  → 𝑉≺
3  policy        builder  → 𝑐
in         𝑉≻ : Xa → [−∞, ∞)
out        𝑉≺ : Xm → ℝ
out        𝑐(m_d) : 𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})

1  arvl_to_dcsn  builder  → μ
2  dcsn_to_cntn  builder  → μ≻
in         μ≺ : finite measure on Xm × ℝ₊
out        μ≻ : finite measure on Xa

Drawing
none
```

The policy stands on no [wire](02-initial.md) into the decision builder: the decision builder is the operator at a policy, and the policy's type is printed once, on the output of the policy builder, `𝑐(m_d)` above.

Read as one operator, the backward graph takes the value functions supplied at the continuation perch to those of the arrival perch, the stage's contribution to the Bellman operator. Its wires carry value functions, or sets of functions where an operation admits several: an operation of the kind `Argmax`, whose output is the set of maximizing policies, and an operation whose output is among the unknowns of its own rule, such as `identification:Pullback`, the identification of the policy builder once the methods file has brought the lines of the endogenous grid method, which equates the policy at the cash on hand of each saving with the candidate consumption there ([A builder](04-builder.md) §2; [Operations](../../reference/operations.md) §§1 and 4). An exact evaluation keeps such a set as it is, selecting no member. The policy builder states the policy, and which policy stands at the decision builder in a computation is stated at [methodization](07-methods.md). The policy is read where the control appears: in the law of motion, the aggregator and a conditional distribution of a decision builder, and in the push-forward of a forward decision builder, each of which the builder is stated at. An evaluation reads, selects and inserts no policy: it returns the field's function, and a set of feasible policies as that same set. The backward graph's printed record:

```python
print(stage.builder.bwd.denote())
```

```text
STAGE cons / BACKWARD BUILDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → [−∞, ∞)
       ──────────────────────────────────────────────────────────────────────
  out  𝑉≺  : Xm → ℝ
       𝑐   : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

At
  𝑐  : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Operations
      cntn_to_dcsn
      in: 𝑉≻                            out: 𝑉
      ───────────────────────────────────────────────────────────────────────
      rule: 𝑉 : Xm → [−∞, ∞)

   1    Pullback
        in: 𝑉≻                          out: 𝑉≻ ∘ 𝑔≻(·, 𝑐)
        ─────────────────────────────────────────────────────────────────────
        rule: (𝑉≻ ∘ 𝑔≻(·, 𝑐))(m_d) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))

   2    Aggregation
        in: (1)                         out: 𝑉
        ─────────────────────────────────────────────────────────────────────
        rule: 𝑉(m_d) = 𝑢(𝑐(m_d)) + 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))

   3    Evaluation
        in: 𝑉                           out: 𝑉
        ─────────────────────────────────────────────────────────────────────
        rule: 𝑉 : Xm → [−∞, ∞)
              D_{m_d}𝑉(m_d) = 𝑑𝑢(𝑐(m_d))

      dcsn_to_arvl
      in: 𝑉                             out: 𝑉≺
      ───────────────────────────────────────────────────────────────────────
      rule: 𝑉≺ : Xm → ℝ

   4    Pullback
        in: 𝑉                           out: 𝑉 ∘ 𝑔≺
        ─────────────────────────────────────────────────────────────────────
        rule: (𝑉 ∘ 𝑔≺)(m, l) = 𝑉(𝑔≺(m, l))

   5    Aggregation
        in: (4)                         out: 𝑉≺
        ─────────────────────────────────────────────────────────────────────
        rule: 𝑉≺ = 𝑉(𝑔≺(m, l))                             on (m, l) ∈ Xm × ℝ₊

   6    Evaluation
        in: 𝑉≺                          out: 𝑉≺
        ─────────────────────────────────────────────────────────────────────
        rule: 𝑉≺ : Xm → ℝ

      policy
      in: 𝑉≻                            out: 𝑐
      ───────────────────────────────────────────────────────────────────────
      rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

   7    Pullback
        in: 𝑉≻                          out: 𝑉≻ ∘ 𝑔≻
        ─────────────────────────────────────────────────────────────────────
        rule: (𝑉≻ ∘ 𝑔≻)(m_d, c) = 𝑉≻(𝑔≻(m_d, c))

   8    optimality:Aggregation
        in: (7)                         out: (m_d, c) ↦ 𝑢(c) + 𝑉≻(𝑔≻(m_d, c))
        ─────────────────────────────────────────────────────────────────────
        rule: (m_d, c) ↦ 𝑢(c) + 𝑉≻(𝑔≻(m_d, c))

   9    optimality:Argmax
        in: (8)                         out: 𝑐
        ─────────────────────────────────────────────────────────────────────
        rule: 𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]

  10    Evaluation
        in: 𝑐                           out: 𝑐
        ─────────────────────────────────────────────────────────────────────
        rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Conditions
  cntn_to_dcsn:Aggregation       𝑉(m_d) ∈ [−∞, ∞)
  dcsn_to_arvl:Aggregation       𝑉≺(m) ∈ ℝ
  dcsn_to_arvl:Aggregation       𝑉≺(m, l) ∈ ℝ
  policy.optimality:Aggregation  ¬(𝑢(cp) ∈ [∞, ∞] ∧ V[>] ∈ [−∞, −∞])
  𝑢                              ¬(1 − ρ = 0)
  cntn_to_dcsn.marginal          marginal-reading: the right side of each
                                   derivative line equals the derivative, in
                                   the named coordinate, of the value the
                                   builder writes, under the envelope
                                   conditions: concavity of the continuation
                                   value, interiority of the maximizer or the
                                   multiplier's term at a binding constraint,
                                   differentiability of the reward in the
                                   control, a measurable selection of the
                                   policy, and differentiability of the value
                                   at the point read; listed and not checked
                                   [required]
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  13  m_d = m
  17  a = m_d - c
  21  V        = 𝑢(c) + V[>]                       :: [id=value]
  22  D_{m_d}V = 𝑑𝑢(c)                             :: [id=marginal]
  26  V[<] = V                                     :: [id=value]
  30  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality]

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  ρ     cons:parameter:ρ
  𝑢     cons:function:𝑢
  𝑑𝑢    cons:function:𝑑𝑢
  Γ     cons:correspondence:Γ
  𝑔≺    cons:g:arvl_to_dcsn
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The card names the policy under `At` and writes the law of motion at that policy out in its rules, `𝑉≻(𝑔≻(m_d, 𝑐(m_d)))`; on a version whose policy builder holds the lines of a solution method, it states the stage file's maximization under `Declared`, with the constructed output substituted ([A builder](04-builder.md) §2). The graph holds the chain of the two backward builders and, beside it, the policy builder, which reads a copy of the continuation functions. No wire joins the policy builder's output to the decision builder, whose pullback, aggregation or conditional distribution refers to the policy by a free name ([A builder](04-builder.md) §1), so the pieces form no chain: they stand in the order of their dependencies, each after every piece that writes a wire it reads, and the drawing shows the wiring.

The forward graph is the operator on measures that a simulation, or the computation of a stationary distribution, iterates, and it is a chain: `arvl_to_dcsn` carries the arrival measure to the decision measure, and `dcsn_to_cntn` pushes that measure forward through the law of motion at the policy, the map `m_d ↦ 𝑔≻(m_d, 𝑐(m_d))`, taking as kernel data any conditional distribution of a shock that depends on the policy. Its printed record, the pieces of each builder in order of application:

```python
print(stage.builder.fwd.denote())
```

```text
STAGE cons / FORWARD BUILDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ≺  : finite measure on Xm × ℝ₊
       ────────────────────────────────────────
  out  μ≻  : finite measure on Xa

At
  𝑐  : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Operations
     arvl_to_dcsn
     in: μ≺                             out: μ
     ──────────────────────────────────────────
     rule: μ : finite measure on Xm

  1    Pushforward
       in: μ≺                           out: μ
       ────────────────────────────────────────
       rule: μ(B) = μ≺({m≺, l≺ ∈ Xm × ℝ₊ | 𝑔≺(m≺, l≺) ∈ B})

     dcsn_to_cntn
     in: μ                              out: μ≻
     ──────────────────────────────────────────
     rule: μ≻ : finite measure on Xa

  2    Pushforward
       in: μ                            out: μ≻
       ────────────────────────────────────────
       rule: μ≻(B) = μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})

Conditions
  𝑢                         ¬(1 − ρ = 0)
  policy.optimality         ¬(𝑢(cp) ∈ [∞, ∞] ∧ V[>] ∈ [−∞, −∞])
  cntn_to_dcsn:Aggregation  𝑉(m_d) ∈ [−∞, ∞)
  cntn_to_dcsn.marginal     marginal-reading: the right side of each
                              derivative line equals the derivative, in the
                              named coordinate, of the value the builder
                              writes, under the envelope conditions: concavity
                              of the continuation value, interiority of the
                              maximizer or the multiplier's term at a binding
                              constraint, differentiability of the reward in
                              the control, a measurable selection of the
                              policy, and differentiability of the value at
                              the point read; listed and not checked
                              [required]
  dcsn_to_arvl:Aggregation  𝑉≺(m) ∈ ℝ
  dcsn_to_arvl.value        𝑉≺(m, l) ∈ ℝ
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  13  m_d = m
  17  a = m_d - c

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  ρ     cons:parameter:ρ
  𝑢     cons:function:𝑢
  Γ     cons:correspondence:Γ
  𝑔≺    cons:g:arvl_to_dcsn
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 4 The grains

The **grain** of a graph is how far its boxes are opened. The stored graphs are at the builder grain, one box per block. `primitives` answers the same graph with every builder opened into its **primitive operators**, the finest boxes the construction makes, and `sub_builders` the graph with each line marked `!node` kept as a box of its own, a **sub-builder**. Each answers the same verbs as the graph, and a box at a finer grain is read by its whole name as a key of the graph at that grain.

```python
print(repr(stage.builder.bwd.primitives))
print(stage.builder.bwd.primitives.list())
print(repr(stage.builder.bwd.primitives["cntn_to_dcsn:Aggregation"]))
```

```text
BuildersGraph('cons', 'backward', primitives)
1  cntn_to_dcsn:Pullback          primitive
2  cntn_to_dcsn:Aggregation       primitive  → 𝑉
3  cntn_to_dcsn:Evaluation        primitive  → 𝑉
1  dcsn_to_arvl:Pullback          primitive
2  dcsn_to_arvl:Aggregation       primitive  → 𝑉
3  dcsn_to_arvl:Evaluation        primitive  → 𝑉≺
1  policy:Pullback                primitive
2  policy.optimality:Aggregation  primitive
3  policy.optimality:Argmax       primitive  → 𝑐
4  policy:Evaluation              primitive  → 𝑐
Operator('cons', 'cntn_to_dcsn:Aggregation')
```

A primitive operator's name is its builder and its kind, `cntn_to_dcsn:Pullback`, with a number where one builder holds several of one kind; an operator that realizes one line of the file carries that line's address in place of the bare builder, `policy.optimality:Aggregation`. [Operations](../../reference/operations.md) lists the kinds an operator can be. A box that acts on every value function its block reads on one base carries no field in its name, whether that is one function or several: `cntn_to_dcsn:Pullback` and `dcsn_to_arvl:Pullback` each act on the one value their block reads. Where two boxes of one kind and one law of motion remain in one builder, because they act on functions of different states, each keeps in its name the field it acts on; no stage under `applications/` has two such boxes. The address of a line is the stable name: adding a statement to a file can merge two boxes of one kind into one box, whose name is then the builder's and no longer the line's, while the line's address is unchanged, which is why methods attach to lines.

The consumption stage writes no line marked `!node`, so its two finer grains hold the same boxes. The smooth-ambiguity savings stage `applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl` marks two, the risk and the ambiguity certainty equivalents that [A builder](04-builder.md) §4 reads, and its backward graph counts a different number of boxes at each grain:

```python
sa = elaborate_stage(load_stage("applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl"))
backward = sa.builder.bwd
for grain, graph in (("builder", backward), ("sub-builder", backward.sub_builders),
                     ("primitive", backward.primitives)):
    print(f"{grain:<12} {len(graph.graph.boxes)} boxes")
```

```text
builder      2 boxes
sub-builder  12 boxes
primitive    19 boxes
```

A box that a grain merges exists only at that grain, so it is not reached from the stored graph's boxes but from the graph or the builder opened at that grain. A derivative line adds no box: in the buffer-stock stage `applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl`, whose value line and derivative line at the arrival perch each take an expectation, the expectation of the value is the one expectation box of the arrival builder, and the derivative line is recorded at that builder's evaluation. The consumption stage declares no shock, so none of its boxes is merged.

Reaching a piece resolves its pair, its perch path or its name against the stored graphs and stores nothing, so the box returned is the box the stored graph holds. Opening a finer grain builds fresh boxes, equal to the stored ones but not the same objects:

```python
stored  = stage.dcsn.builder.bwd["pullback"].box
again   = stage.builder["cntn", "dcsn"]["pullback"].box
derived = stage.builder.bwd.primitives["cntn_to_dcsn:Pullback"].box
print("the same box twice:     ", again is stored)
print("a box of a finer grain: ", derived is stored, "but equal:", derived == stored)
```

```text
the same box twice:      True
a box of a finer grain:  False but equal: True
```

## 5 The hypergraph

`graph` answers the graph itself, a `discopy.frobenius.Hypergraph` in the package's frozen subclass.

> [!note]- Technical details
> A box of the hypergraph records only its own ends, which DisCoPy, the diagram library the package keeps its graphs in, calls ports. Each port sits on the input side or the output side of its box and carries one `Sort`, the type of its wire: an identity, a kind (`field`, `function` or `measure`), a perch, a role, a domain and, for a function, the coordinates it is written in. No box records a connection to any other box.
>
> The graph is the table that joins the ports. It numbers the wires, gives each number one `Sort`, and places every port, its own and every box's, on a wire. That is the whole of a hypergraph: `dom` and `cod`, its inputs and outputs, its `boxes`, `spider_types`, the sort of each wire number, and the three tables `dom_wires`, `box_wires` and `cod_wires`.
>
> A connection is a shared wire number and nothing else. Where one wire carries an output port of one box and an input port of another, the output of the first builder is an input of the second. Where one wire carries several input ports, one function is read by several builders, a wire DisCoPy calls a spider. A graph has no arrows: the direction is read from the side of the box each port sits on, which is why one wire can be read by many boxes at once.

The tables of the backward graph, each box with the wires it has an input port on and the wires it has an output port on:

```python
graph = stage.builder.bwd.graph
for wire, sort in enumerate(graph.spider_types):
    print(f"wire {wire}: {sort.inside[0].name}")
print("dom_wires ", graph.dom_wires)
for box, (inputs, outputs) in zip(graph.boxes, graph.box_wires):
    print(f"  {box.name:<14} in {inputs}  out {outputs}")
print("cod_wires ", graph.cod_wires)
```

```text
wire 0: cons:function:cntn:V
wire 1: cons:function:dcsn:V
wire 2: cons:function:arvl:V
wire 3: policy:Evaluation:c:result
dom_wires  (0,)
  cntn_to_dcsn   in (0,)  out (1,)
  dcsn_to_arvl   in (1,)  out (2,)
  policy         in (0,)  out (3,)
cod_wires  (2, 3)
```
