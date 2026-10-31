---
title: "Discounting stage (disc)"
audience: developer
type: index
---
# Discounting stage (`disc`)

This folder holds the stage YAML (Bellman-SYM's earlier YAML surface; the
`.bl` form is `applications/portfolio-choice/disc.bl`) for the discounting
stage of the portfolio-choice example, *Portfolio Choice with Correlated
Shocks*. The
discounting stage is period-terminal and carries no economic content of its
own. All of its transitions are the identity map, so the state passes through
unchanged; there are no shocks, no optimization, and no stage reward. Its sole
purpose is to apply the discount factor β to the continuation value.

The motivation for isolating β in its own stage is symmetry: by extracting the
discount factor here, every economic stage (`cons`, `port`) can be written with
β = 1, and discounting is handled once, in one place. The factorization is
set out in `docs/Bellman-Sym/06-period.md` §1 and §1.1, which join the
beta-free consumption stage to a discounting stage.

The folder contains two files:

- `disc_stage.yaml` — the symbolic stage (symbols and equations).
- `disc_stage_methods.yml` — the methodization that pairs nodes with methods.

## `disc_stage.yaml`

The stage YAML follows the strict skeleton of the earlier YAML surface: a
`name`, a `symbols` block, and an `equations` block.

### stage name

The stage is named `disc_stage`.

```yaml
# stage name
name: disc_stage
```

### symbol declarations

The symbol declarations open with a single space, `Xa`, the non-negative reals
`R+`, which serves as the asset space. The arrival prestate `a`, the decision
state `a_d`, and the continuation poststate `a` all live in `Xa`. The three
values — the arrival value `V[<]`, the decision value `V`, and the continuation
value `V[>]` — each take real values. The single parameter is the discount
factor β, constrained to the open interval `(0,1)`.

```yaml
# symbol declarations
symbols:
  spaces:
    Xa: "@def R+"

  prestate:
    a: "@in Xa"

  states:
    a_d: "@in Xa"

  poststates:
    a: "@in Xa"

  values:
    V[<]: "@in R"
    V: "@in R"
    V[>]: "@in R"

  parameters:
    β: "@in (0,1)"
```

### stage equations

The equations are grouped into the four standard stage sub-blocks. Each is
described below.

```yaml
# stage equations
equations:
  # arrival to decision transition
  arvl_to_dcsn:
    - a_d = a

  # decision to continuation transition
  dcsn_to_cntn:
    - a = a_d

  # continuation to decision backward evaluation
  cntn_to_dcsn:
    - V = β*V[>]

  # decision to arrival backward evaluation
  dcsn_to_arvl:
    - V[<] = V
```

#### arrival to decision transition

This is the identity map: the arrival state equals the decision state, so the
asset carried into the stage passes through unchanged to the decision.

#### decision to continuation transition

This is again the identity map: the decision state equals the continuation
state, so the asset passes through unchanged to the continuation.

#### continuation to decision backward evaluation

Here the continuation value is scaled by the discount factor, `V = β*V[>]`. This
is the one operation the stage actually performs. It is a backward evaluation
with no maximization.

#### decision to arrival backward evaluation

This is the identity map on values: the arrival value equals the decision
value, `V[<] = V`.

## `disc_stage_methods.yml`

The methodization file follows spec 0.1d / 0.1d.1 (the operator-slot surface):
one entry per named node, written as `on: <node>` with an optional
`method: !tag`, and no `schemes:` list. Because the stage performs no
optimization, has no shocks, and uses no interpolation grid, most nodes carry no
method at all.

A note on handlers (the solver callable that would realize each node, per spec
0.1d.1): none of this application's solvers instantiates, compiles, or solves
`disc_stage`. A walk through `code/solve_port_cons.py` and
`code/semiconjugate_solve.py` finds no reference to `disc_stage` — β-discounting
is folded directly into the `cons` and `port` reward aggregators rather than
extracted into a separate stage. Every node here is therefore left without a
handler.

### stage name

The methodization targets the stage `disc_stage`.

```yaml
# stage name
stage: disc_stage
```

### node method assignments

The `methods` list assigns a method (or no method) to each node, as described
below.

```yaml
# node method assignments
methods:
  # continuation to decision backward evaluation
  - on: cntn_to_dcsn

  # decision to arrival backward evaluation
  - on: dcsn_to_arvl

  # arrival to decision transition
  - on: arvl_to_dcsn

  # decision to continuation transition
  - on: dcsn_to_cntn

  # arrival to decision forward builder
  - on: arvl_to_dcsn_builder
    method: !deterministic

  # decision to continuation forward builder
  - on: dcsn_to_cntn_builder
    method: !deterministic
```

#### continuation to decision backward evaluation

The backward evaluation `V = β*V[>]` is a scalar aggregator: it involves no
expectation and no maximization. Under the one-method-per-node discipline, the
method-bearing operator nodes are `E`, `evaluate`, `argmax`, `solve`,
`upper_env`, and `policy`; a plain scalar node like this one carries at most a
handler, not a method. Because `disc_stage` is unused in this application there
is no realizing handler either, so this entry is a bare structural target with
neither method nor handler. (An earlier draft tagged this node
`method: !scalar-multiply`; that was dropped, because `!scalar-multiply` is not
a method-bearing operator node.)

#### decision to arrival backward evaluation

This node is the identity evaluation on values and carries no method.

#### arrival to decision transition

This node is an identity transition function and carries no method.

#### decision to continuation transition

This node is an identity transition function and carries no method.

#### arrival to decision forward builder

The forward (simulation) builder is an identity pass-through, methodized as
`!deterministic`.

#### decision to continuation forward builder

The forward (simulation) builder is an identity pass-through, methodized as
`!deterministic`.
