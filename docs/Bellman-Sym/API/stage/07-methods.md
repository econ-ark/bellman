---
title: Methods and places
tags:
  - docs/api
  - method
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# Methods and places

> [!summary]
> `stage.places()` answers the places of a stage, the operators at which a methods file may type a method, a grid or a handler, each with its kind. `methods`, asked of the stage, a graph, a builder or an operation, answers the components typed within it, each read by its place's path as the methods file writes it, `stage.methods["policy"]`. Typing a method changes no equation of the model and runs no computation; where the method brings lines, the operative builders hold them and the declared builders keep the stage file's. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl` and its methods file `methods.bl`, the addition beside it.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the object `stage` below; [The binding verbs](09-binding-verbs.md): `methodize`, which reads the methods file with the stage file.
> **Used by** — [Parameters and settings](06-par-and-settings.md): the settings the typed methods read.
> **See also** — [Method types](../../reference/methods.md): every method word, the kinds of place it admits and the keyword arguments the package reads; [Methodization](../../04-methodization.md): the methods file; [API](../index.md) §2.4: every path of the stage object in one table.

A [method](../../../wiki/methods.md) names a numerical procedure for one operator of a stage, such as the endogenous grid method for the policy builder, a [grid](../../../wiki/grid.md) the points at which the function at the operator is stored, and a [handler](../../../wiki/handler.md) the routine that carries the method out. The methods file types each at a **place**, an operator it can name, written by its path: a [block](../../01-stage.md#3-builder-blocks), the Evaluation that stores the block's result, an operator inside a line, a line, or a definition. The method and the grid are components of the operator's signature and the handler a binding beside them; the signature of a builder prints the three beside the functions it reads and writes, and nothing in the package executes them.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
specified = (stage.calibrate("applications/portfolio-choice/declaration/calibration/portfolio.yml")
             .methodize("applications/portfolio-choice/declaration/stages/cons/methods.bl")
             .configure("applications/portfolio-choice/declaration/settings/cons.yml"))
```

## 1 The places

`stage.places()` answers one row per place, its path as a methods file writes it in the first column, `address`, and its kind in the second: a builder, by the id of its block; a line, by its address `<block>.<line>`, of the kind `node` where the line is marked `!node` and `statement` otherwise; an operator of one line, `<block>.<line>.<operator>`, of every line of a block, `<block>.<operator>`, or of every line of the stage, by the operator's head alone; and a definition, by its name. After the lines of the policy builder and of each backward value builder stand the places of the [Evaluation](../../reference/operations.md#evaluation) that closes it, of the kind `operator evaluate`, where a representation of what the builder stores is typed: `policy.evaluate` and its one object, the policy, `policy.evaluate[c]`, for the policy builder, and for a backward value builder the Evaluation as a whole, `cntn_to_dcsn.evaluate`, and each object it stores, `cntn_to_dcsn.evaluate[V]` for the value function and `cntn_to_dcsn.evaluate[D_{m_d}V]` for the derivative of it that the stage's derivative line states, so that the value and its derivative may be represented together or each on a grid of its own ([Methodization](../../04-methodization.md) §2). A representation is typed at these places and at no builder. The consumption stage writes no line marked `!node`. The kinds are read from the objects of the stage, whatever is typed at them; the derivative operator `D` is listed and admits no method. The listing reads `stage` after the verbs above have bound it, so the three lines of the methods file's block `policy` stand among the places beside the stage file's maximization.

```python
print(stage.places())
```

```text
address                          kind
arvl_to_dcsn                     builder
dcsn_to_cntn                     builder
cntn_to_dcsn                     builder
cntn_to_dcsn.value               statement
cntn_to_dcsn.marginal            statement
cntn_to_dcsn.evaluate            operator evaluate
cntn_to_dcsn.evaluate[V]         operator evaluate
cntn_to_dcsn.evaluate[D_{m_d}V]  operator evaluate
dcsn_to_arvl                     builder
dcsn_to_arvl.value               statement
dcsn_to_arvl.evaluate            operator evaluate
dcsn_to_arvl.evaluate[V[<]]      operator evaluate
policy                           builder
policy.optimality                statement
policy.optimality.argmax         operator argmax
policy.InvEuler                  statement
policy.InvEuler.D                operator D
policy.grid                      statement
policy.identification            statement
policy.argmax                    operator argmax
policy.D                         operator D
policy.evaluate                  operator evaluate
policy.evaluate[c]               operator evaluate
argmax                           operator argmax
D                                operator D
𝑢                                definition
𝑑𝑢                               definition
Γ                                definition
𝑑𝑢𝑖𝑛𝑣                            definition
```

A path that names no place is refused when the methods file is read, as is an unknown method word and a known word at a place of a kind its row does not admit: a quadrature rule, for instance, belongs to an expectation and not to the policy builder. [Method types](../../reference/methods.md) states the kinds of place each word admits, and `admitted_methods(stage, address)` of `bellman.stage` answers the words admitted at one place. Typing a method runs nothing; where the method's row names a condition, such as `egm-eligibility` of the endogenous grid method, the stage records it among the builder's conditions, and the package does not check it (§3).

## 2 The methods typed at a stage

`specified.methods` answers every place at which a component is typed, one line each: the place, the method word with its keyword arguments, the grid where the place has one, and the handler, a quoted string, where one is named. Before methodization it is empty and prints `none`, as the stage elaborated from `cons.bl` alone shows; the binding verbs bind the stage they are called on, so `stage` and `specified` above name one stage.

```python
print(elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl")).methods)
print(specified.methods)
```

```text
none
arvl_to_dcsn            !deterministic
dcsn_to_cntn            "cons-port:transition_fwd"
cntn_to_dcsn.evaluate   !Linear   !Cartesian(m_d=(m_min, m_max, n_m))   "cons-port:_make_interp"
policy                  !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"
```

The methods file types four places:

```python
from pathlib import Path

print(Path("applications/portfolio-choice/declaration/stages/cons/methods.bl").read_text(encoding="utf-8"), end="")
```

```text
@methods: cons
# The methods of the consumption stage, written as an addition to cons.bl
# beside this file: the endogenous grid method on the policy builder, with its
# grid of savings and the function egm of cons-port as its handler, and the
# three lines of the method, the inverted Euler equation with its Kuhn-Tucker
# clause, the inverted law of motion and the identification c = c[>], which
# stand in place of the declared maximization at the operative level while
# the declared level keeps the maximization of cons.bl; one linear
# representation of the decision value and of its stated derivative on the
# grid of resources; the deterministic arrival builder; and the handler of the
# forward decision builder, which takes no method word. The block `policy`
# carries no signature, since it adds no coordinate. The entries that add no
# line are file-level lines, each routed to its place by its path, since an
# empty body is refused. Each grid is its own typing entry at its place, one
# factor per coordinate keyed by the coordinate's name, and every setting a
# grid reads is declared above the blocks and lines with its set, a bound as
# a point of the set its coordinate is declared on, a count in ℕ.

𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)

n_a : ℕ        :: ["number of points of the savings grid"]
a_min : Xa     :: ["lower bound of the savings grid"]
a_max : Xa     :: ["upper bound of the savings grid"]
n_m : ℕ        :: ["number of points of the grid of resources"]
m_min : Xm     :: ["lower bound of the grid of resources"]
m_max : Xm     :: ["upper bound of the grid of resources"]

[id=policy, method : !egm | grid : !Cartesian(a=(a_min, a_max, n_a)) | handler : "cons-port:egm"] {
    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]
    m_d[>] = a + c[>]                        :: [id=grid]
    c      = c[>]                            :: [id=identification]
}

cntn_to_dcsn.evaluate.method : !Linear
cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))
cntn_to_dcsn.evaluate.handler : "cons-port:_make_interp"
arvl_to_dcsn.method : !deterministic
dcsn_to_cntn.handler : "cons-port:transition_fwd"
```

The block `policy` of the methods file names the stage's policy block by its id. Its bracket types the policy builder's method, `method : !egm`, its grid of savings, `grid : !Cartesian(a=(a_min, a_max, n_a))`, and its handler, `handler : "cons-port:egm"`, by paths relative to the block, and its three lines are the lines of the endogenous grid method, which the operative builder holds in place of the maximization (§3). The five entries after it stand at file level, each with the full path of its place: the representation of the decision value and of its stated derivative at the decision builder's Evaluation, one entry for both, with its grid of resources and its handler; the method of the forward builder from arrival to decision; and the handler of the forward builder from decision to continuation, which has no method word. The settings the two grids name are declared above the block with their sets ([Parameters and settings](06-par-and-settings.md) §2).

One place is read by its path as the methods file writes it: `specified.methods["policy"]` answers the components typed at the policy builder and `specified.methods["cntn_to_dcsn.evaluate"]` those at the decision builder's Evaluation. The answer is the place's record, which prints the word with its arguments, the grid as written and the handler, and holds each under `word`, `grid` and `handler`; a place at which no component is typed is refused with a `KeyError` that names the typed places.

```python
print(repr(specified.methods["policy"]))
print(repr(specified.methods["cntn_to_dcsn.evaluate"]))
print(specified.methods["policy"].handler, specified.methods["dcsn_to_cntn"].word == "")
try:
    specified.methods["cntn_to_dcsn"]
except KeyError as refusal:
    print(refusal)
```

```text
!egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"
!Linear   !Cartesian(m_d=(m_min, m_max, n_m))   "cons-port:_make_interp"
cons-port:egm True
"stage 'cons': no component is typed at 'cntn_to_dcsn'; the components here are typed at arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn.evaluate, policy"
```

The signature of a builder prints the components beside its inputs and outputs: the policy builder's method, grid and handler, and the forward builder's handler alone.

```python
print(specified.builder.policy.signature())
print(specified.builder["dcsn", "cntn"].signature())
```

```text
in         𝑉≻ : Xa → [−∞, ∞)
out        𝑐(m_d) : 𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})
method     !egm
grid       !Cartesian(a=(a_min, a_max, n_a))
handler    "cons-port:egm"
in         μ : finite measure on Xm
out        μ≻ : finite measure on Xa
handler    "cons-port:transition_fwd"
```

## 3 Methods at every level

Every piece answers `methods`, the components typed at it or inside it, read from the typing entries of the stage; no piece keeps a copy. A [builders graph](03-build.md), the backward graph `stage.builder.bwd` or the forward graph `stage.builder.fwd`, answers the components typed within it, and `stage.builder` those typed within both; a builder answers those typed at it or inside it, among them the representation at its Evaluation, which the builder holds under the key `"evaluation"`; and an operation or a line answers the components typed at it.

```python
print(specified.builder.bwd.methods)
print()
print(specified.dcsn.builder.bwd.methods)
print()
print(specified.dcsn.builder.bwd["evaluation"].methods)
print()
print(specified.builder.fwd.methods)
```

```text
cntn_to_dcsn.evaluate   !Linear   !Cartesian(m_d=(m_min, m_max, n_m))   "cons-port:_make_interp"
policy                  !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"

cntn_to_dcsn.evaluate   !Linear   !Cartesian(m_d=(m_min, m_max, n_m))   "cons-port:_make_interp"

cntn_to_dcsn.evaluate   !Linear   !Cartesian(m_d=(m_min, m_max, n_m))   "cons-port:_make_interp"

arvl_to_dcsn   !deterministic
dcsn_to_cntn   "cons-port:transition_fwd"
```

A solution method that brings lines changes what the operative builder holds. The policy builder of the stage elaborated from `cons.bl` alone holds the maximization of the stage file as three operations and its Evaluation; after methodization, `stage.builder.policy` holds the three lines of the endogenous grid method as its operations, with the maximization kept under `Declared` on its card and in `stage.declared.policy`, the builder as the stage file states it ([The builders graphs](03-build.md) §1; [Methodization](../../04-methodization.md) §5). The card, the printed summary that `denote()` answers, prints the components typed within the builder under `Method`, before the source lines of both files and the definitions the builder refers to.

```python
print(stage.declared.policy.list())
print()
print(specified.builder.policy.list())
print()
print(specified.builder.policy.denote())
```

```text
1  Pullback                primitive
2  optimality:Aggregation  primitive
3  optimality:Argmax       primitive  → 𝑐
4  Evaluation              primitive  → 𝑐

1  InvEuler:Aggregation     primitive  → 𝑐≻
2  grid:Aggregation         primitive  → 𝑚_d≻
3  identification:Pullback  primitive  → 𝑐
4  Evaluation               primitive  → 𝑐

STAGE cons / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → [−∞, ∞)
       ──────────────────────────────────────────
  out  𝑐   : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Declared
  𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]

Operations
  1  InvEuler:Aggregation
     in: 𝑉≻                             out: 𝑐≻
     ────────────────────────────────────────────
     rule: 𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0

  2  grid:Aggregation
     in: 𝑐≻                             out: 𝑚_d≻
     ────────────────────────────────────────────
     rule: 𝑚_d≻(a) = a + 𝑐≻(a)

  3  identification:Pullback
     in: 𝑐≻, 𝑚_d≻                       out: 𝑐
     ────────────────────────────────────────────
     rule: 𝑐(𝑚_d≻(a)) = 𝑐≻(a)                                      on 𝑚_d≻(Xa)

  4  Evaluation
     in: 𝑐                              out: 𝑐
     ────────────────────────────────────────────
     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Conditions
  grid:Aggregation  𝑚_d≻(a) ∈ Xm
  policy            egm-eligibility: the construction satisfies the declared
                      line where the continuation value 𝑉≻ is concave and
                      continuously differentiable on (0, ∞) with a finite
                      positive right derivative at 0   [required]

Method
  !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"            policy
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  30  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality]

Source  methods.bl
  29  c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0          :: [id=InvEuler]
  30  m_d[>] = a + c[>]                            :: [id=grid]
  31  c      = c[>]                                :: [id=identification]

Definitions referenced
  Xm     cons:set:Xm
  Xa     cons:set:Xa
  𝑢      cons:function:𝑢
  Γ      cons:correspondence:Γ
  𝑑𝑢𝑖𝑛𝑣  cons:function:𝑑𝑢𝑖𝑛𝑣  methods.bl:19
  𝑔≻     cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
