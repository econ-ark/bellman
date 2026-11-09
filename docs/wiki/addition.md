---
slug: addition
title: Addition (methods file)
description: A methods file, a stage-grammar file unioned with the stage file on the syntax trees before elaboration, which adds entries and lines to the stage's blocks and removes nothing.
tags:
- methodization
- syntax
wiki_status: budding
last_reviewed: '2026-11-05'
reviewed_by: Claude (Fable), session of 5 November 2026, at AAS's request; written from the decisions of 4 November 2026 on the union of a stage file with its methods files, checked against the Bellman calculus page on methods, and revised after one adversarial review round
sources:
- path: docs/bellman-calculus/06-Methods.md
  class: canonical
  date: '2026-11-05'
- path: docs/Bellman-Sym/04-methodization.md
  class: canonical
  date: '2026-11-05'
audience: user
type: concept
---

# Addition (methods file)

> [!summary]
> An **addition** is a methods file: a `.bl` file read by the stage grammar, whose first line is `@methods: <stage>`, and which is unioned with the [[stage|stage file]] on the two syntax trees before elaboration. The union adds and never replaces: a block of the addition names a block of the stage by its `id` and adds its header entries to that block's header and its lines after that block's lines. The stage file alone states the model; the union with its additions is the stage as it is computed.

> [!info]- Relationship with other documents
> **Formal account** — [Methods](../bellman-calculus/06-Methods.md) §§8, 9: the erasure of the addition and the two levels of a stage.
> **Builds on** — [[methods|Methods]] and [[grid|Grid]]: the two components an addition's entries type; [[settings|Settings]]: the declarations an addition carries.
> **Used by** — [Methodization](../Bellman-Sym/04-methodization.md): the written form; [The Bellman factory](../Bellman-Sym/08-bellman-factory.md): the recipe that names the additions of each stage occurrence.

## 1 The form

```bl
@methods: buffer_stock

n_a : ℕ              :: ["number of points of the savings grid"]
a_min : Xa           :: ["lower bound of the savings grid"]
a_max : Xa           :: ["upper bound of the savings grid"]

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))
    | evaluate.method : !Linear] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{m}V = 𝑑𝑢(c)                                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | evaluate.method : !Linear(extrap=clamp)
    | evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))
    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)] {
    D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)    :: [id=marginal]
}
```

The file reads the buffer-stock stage, whose savings coordinate `a` is declared on the set `Xa` and whose permanent income growth factor is `Γ`. The first group of a bracket holds the block's own entries, its `id` and, where the author writes it there, the typing of the block's own method; each later group, opened by `|`, holds one typing entry, either of a component of the block itself by its absolute path, `policy.grid`, or of an [[operator]] inside the block by a path relative to the block, `evaluate.method` for the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that stores the [[builder|builder's]] result and `E_ψ_ξ.method` for the expectation of a line. A typing entry at file level carries the full path, `policy.evaluate.method : !Linear`, and the union attaches it to the node the path names. A [[handler]] is written as a binding in the same way, `policy.handler : "cons-port:egm"`, with or without a method word. The file declares each setting it reads with its domain ([[settings]]). A mark after a [[field]] names its [[perch]]: `V[>]` is the value at the continuation perch, `V[<]` at the arrival perch, and `c[~]` the consumption at the decision perch; a candidate the method computes, `c[>]`, carries the mark of the perch whose coordinate it is computed at.

## 2 The rules of the union

The union is defined on the syntax trees and knows no word of the vocabulary: it merges structure, and the elaborator reads the merged term afterwards as if everything had been written in the stage file.

1. **Blocks by id.** A block of the addition whose `id` equals the `id` of a block of the stage merges with it; a block with an id in one file only is kept. Nested blocks, the [[branch|branches]] of a branching stage, merge by their label under their parent, and no branch is added.
2. **Entries by key.** The header entries merge as a keyed collection: a typing by its subject, a `key=value` pair by its key, a tag by its text. A pair or a tag written in both files becomes one where the content is equal and is refused, naming both, where it differs. A component typed by both files is refused, so that each method and each grid of a block is written once.
3. **Signatures coordinate by coordinate.** Within a stage the field names determine the signature: a coordinate of the addition with the name of a coordinate of the stage is that coordinate, the stage's typing is kept, and a differing type is refused. A coordinate is appended by a partial signature whose arrow says the side: `() -> (h : ℝ₊ @ !ctrl) : !dcsn` appends an output, a control (the role word `!ctrl`) chosen at the decision perch (the perch word `!dcsn`), and `(z : ℝ) : !cntn -> ()` appends an input at the continuation perch. A derivative is never appended as a field: it is read by the derivative term, `D_{m}V`, and stated by a line. A side of a [[backward_builder|backward block]]'s header, the inputs before the arrow or the outputs after it, admits a value field or a control and no state, since a state of a perch is a coordinate of the functions the block writes and no input of its own.
4. **Bodies appended.** The lines of the addition stand after the lines of the stage's block; a line id written in both files is refused.
5. **File-level items appended.** Declarations, definitions and laws of the addition are appended; a name defined in both files with different content is refused.
6. **Files in order.** A [[stage|stage occurrence]], one use of a stage file at one position of a [[trellis]], takes the additions its [[wiki/spec_factory|recipe]] names, applied in that order; the union is associative, and the stage file unioned with no addition is the stage file. A change of selection, `!egm` at one occurrence and `!vfi` at another, is written by naming another file in the recipe, never inside the union.
7. **Provenance kept.** Every item keeps the file and position it was written at, so that `stage.declared`, the tables of [[parameters]] and settings, and the erasure are defined.

## 3 The two levels

After the union the elaborator reads a block under the word in its method component at two levels. The **declared level**, `stage.declared`, holds the stage file's own lines. At the **operative level**, where the block's component holds a solution method and the addition supplies its **rows**, the lines by which the method computes the builder, the rows stand in place of the declared lines, so that the three lines of the endogenous grid method above stand in place of `c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])`, where `Γ_c(m)` is the feasible set of consumption at resources `m`. A derivative line stands at both levels; a solution method without rows, `!vfi`, leaves the declared lines; and where the component holds no solution method, an appended line is an authored line of the block and a second definition of a field is refused. Removing every item whose provenance is the addition returns the stage file: the erasure of the addition of [Methods](../bellman-calculus/06-Methods.md) §8.
