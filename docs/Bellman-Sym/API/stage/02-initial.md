---
title: The initial diagrams
tags:
  - docs/api
  - stage
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# The initial diagrams

> [!summary]
> `stage.initial` holds the two initial diagrams of a stage, `backward` and `forward`: the [blocks](../../01-stage.md#3-builder-blocks) of each direction on the [fields](../../../wiki/field.md) they read and write. A block is read by its id as a key of the diagram that holds it, and a line of a block by a second key. This page states what each of them answers, with every listing printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the object `stage` below.
> **Used by** — [The builders graphs](03-build.md): the same blocks as the operators they denote.
> **See also** — [API](../index.md) §2.4: every path of the stage object in one table.

The stage holds four graphs, and two words name any one of them: its **level**, the field level of the initial diagrams on this page or the operator level of [the builders graphs](03-build.md), and its **direction**, `backward` or `forward`, which the paths of the builders write `bwd` and `fwd` ([The builders graphs](03-build.md) §1). `stage.initial.forward` is the graph at the field level in the forward direction, and `stage.builder.bwd` the graph at the operator level in the backward direction.

An **initial diagram** is a graph of the stage whose boxes are the blocks of the stage file and whose **wires**, the typed connections along which the boxes read and write, carry fields, one graph for each direction. The **backward initial diagram** holds the blocks whose outputs are values or the policy's control; the **forward initial diagram** holds the blocks whose outputs are states of a later [perch](../../../wiki/perch.md). The two are separate graphs and no path puts them in one picture. They hold no operator: the operators stand in [the builders graphs](03-build.md).

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 The two diagrams

`stage.initial` answers the two diagrams, `stage.initial.backward` and `stage.initial.forward`. Its `list()` names the blocks of both directions, and its `methods` the methods bound within them, empty before [methodization](07-methods.md).

```python
print(repr(stage.initial))
print(stage.initial.list())
```

```text
InitialDiagrams('cons', backward, forward)
cntn_to_dcsn   block, backward
dcsn_to_arvl   block, backward
policy         block, backward
arvl_to_dcsn   block, forward
dcsn_to_cntn   block, forward
```

## 2 One diagram

`stage.initial.backward` answers one diagram. `list()` names its blocks with the fields each writes; `signature()` names the fields supplied to the diagram and the fields it produces; `denote()` answers the diagram's printed record, one entry per block and the lines of the file the blocks hold; `diagram()` answers its drawing, a `Drawing` that displays in a notebook and writes SVG by `svg()`; `graph` answers the hypergraph itself, an object of DisCoPy, the diagram library the package keeps its graphs in.

```python
print(repr(stage.initial.backward))
print(stage.initial.backward.list())
print(stage.initial.backward.signature())
```

```text
InitialDiagram('cons', 'backward')
cntn_to_dcsn  block  → V
dcsn_to_arvl  block  → V≺
policy        block  → c
in         V≻ : {V≻}
out        V≺ : {V≺}
out        c : {c}
```

The diagram's printed record states which fields are supplied to each block on a wire and which each writes, not what any of them computes. A coordinate stands on no wire, and a derivative line adds none: the line `cntn_to_dcsn.marginal`, `D_{m_d}V = 𝑑𝑢(c)`, states the derivative of the value `V` that its block writes, reads only the coordinate `c` and writes no field of its own. The backward diagram's record, then the forward one's:

```python
print(stage.initial.backward.denote())
```

```text
STAGE cons / BACKWARD INITIAL DIAGRAM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   V≻  : {V≻}
       ─────────────────────────────────────────────
  out  V≺  : {V≺}
       c   : {c}

Operations
  cntn_to_dcsn
  in: V≻                                out: V

  dcsn_to_arvl
  in: V                                 out: V≺

  policy
  in: V≻                                out: c
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  backward  ≺ V≺  ←  ∼ V  ←  ≻ V≻
  policy    ∼ c  ←  ≻ V≻
  22        V        = 𝑢(c) + V[>]
              :: [id=value]
  23        D_{m_d}V = 𝑑𝑢(c)
              :: [id=marginal]
  27        V[<] = V
              :: [id=value]
  31        c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])
              :: [id=optimality, !doc]
  32        c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0
              :: [id=InvEuler]
  33        m_d[>] = a + c[>]
              :: [id=endoggrid]
  34        c      = c[>]
              :: [id=cons_choice]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```python
print(stage.initial.forward.denote())
```

```text
STAGE cons / FORWARD INITIAL DIAGRAM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   m≺  : {m≺}
       ─────────────────────────────────────────
  out  a≻  : {a≻}

Operations
  arvl_to_dcsn
  in: m≺                                out: m_d

  dcsn_to_cntn
  in: m_d                               out: a≻
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  forward  ≺ m≺  →  ∼ m_d  →  ≻ a≻
  14       m_d = m
  18       a = m_d - c
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> [!note]
> DisCoPy's own class `Diagram` names something else, the interior of one box. These pages write "DisCoPy `Diagram`" for the class and "initial diagram" for the field-level graph of a stage.

## 3 A block and its lines

A block is read by its id, as a key of the diagram that holds it. It answers `list()`, the lines it holds, and `denote()`, its wires, its conditions and the lines of the file it holds. A control that a block lists among its inputs is the coordinate its lines are written in and no wire, so the block's `signature()` does not list it: `cntn_to_dcsn` lists `c` among its inputs, and its only input wire is `V≻`.

```python
block = stage.initial.backward["cntn_to_dcsn"]
print(repr(block))
print(block.list())
print(block.signature())
```

```text
Block('cons', 'cntn_to_dcsn')
value     line  → V
marginal  line  → D_{m_d}V
in         V≻ : {V≻}
out        V : {V}
```

The block's printed record, its card, gives its wires, the conditions on its outputs and the lines of the file it holds:

```python
print(block.denote())
```

```text
STAGE cons / BACKWARD BLOCK cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   V≻  : {V≻}
       ──────────
  out  V   : {V}

Conditions
  𝑉(m_d) ∈ [−∞, ∞)
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  22  V        = 𝑢(c) + V[>]  :: [id=value]
  23  D_{m_d}V = 𝑑𝑢(c)        :: [id=marginal]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

A line of a block is read by a second key, its id, and answers `denote()`, the statement the file writes with its position, `signature()`, `obligations()` and `methods`. A line marked `!doc` states what the control is and is no equation a method solves, so it has no box in the diagram and forms no operation of the builder: the builder's card prints it under `Declared`, with the constructed output substituted, and the line as the file writes it under `Source` ([The builders graphs](03-build.md) §3). It is still read by its key.

```python
line = stage.initial.backward["cntn_to_dcsn", "value"]
print(repr(line))
print(line.denote())
print(repr(stage.initial.backward["policy", "optimality"]))
```

```text
Line('cons', 'cntn_to_dcsn.value')
STAGE cons / BACKWARD BLOCK cntn_to_dcsn / value
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conditions
  𝑉(m_d) ∈ [−∞, ∞)
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  22  V        = 𝑢(c) + V[>]  :: [id=value]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Line('cons', 'policy.optimality')
```

A key that names no block, or a line the block does not hold, is refused with a `KeyError` that names the keys the diagram or the block holds.
