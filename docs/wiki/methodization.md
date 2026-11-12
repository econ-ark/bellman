---
slug: methodization
title: Methodization
tags:
- method
- methodization
wiki_status: canonical
last_reviewed: '2026-11-05'
reviewed_by: Codex (Astra); source-checked. Revised by Claude (Fable), session of 5 November 2026, at AAS's request, for the methods written as components of the operators' signatures in a methods file that is an addition to the stage file, checked against the Bellman calculus page on methods
sources:
- path: docs/bellman-calculus/06-Methods.md
  class: canonical
  date: '2026-11-05'
- path: docs/Bellman-Sym/API/factory/stage-factory.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/04-methodization.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---


# Methodization

**Methodization** binds numerical methods to the operators of a [[stage]]. A [[methods|method]] names a technique and is a label on the [[operator]] it serves, beside the operator's [[signature|inputs and outputs]], written as a typing of the operator's name; a [[handler]] identifies the routine that performs it; the [[settings]] are the declared names whose values the methods read. None supplies a missing model equation or proves that a computed policy is optimal.

The methods of a stage are written in its methods file, the [[addition]] to the stage file: a `.bl` file read by the stage grammar and unioned with the stage file before elaboration. The buffer-stock addition binds the endogenous grid method on the policy [[builder]], with the method's grid of savings, and piecewise linear interpolation on the Evaluation that stores the policy:

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
```

The method stands on the policy builder, `policy`: the block of the addition names the stage's block by its `id`, its entry `policy.method : !egm` types the builder's method component, its entry `policy.grid : !Cartesian(a=(a_min, a_max, n_a))` types the builder's [[grid]] component, the group `| evaluate.method : !Linear` types the Evaluation inside the block, and its three lines are the rows by which the method computes the policy at the operative level, the stage keeping the declared maximization in `stage.declared` ([[addition]] §3). `stage.methods["policy"]` answers the method by the place it binds at. A handler is written as a binding in the same form, `policy.handler : "cons-port:egm"`, with or without a method word. The settings the entries name are declared in the addition with their domains and valued in the settings file.

## Where a method stands

A method type states the kinds of place it admits and the keyword arguments it reads ([method types](../Bellman-Sym/reference/methods.md)). A place is what `stage.places()` lists: a whole builder; the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that closes a builder, where a representation of what it stores stands; a line marked `!node` or any other [[statement]] with an id; a function the [[stage|stage file]] defines; or one occurrence of an operator inside a line. The path written before `.method` names it:

| Path | Place |
|---|---|
| Block id, `policy` | The builder the block denotes, where a solution method such as `!egm` or `!vfi` stands. |
| Block id and `evaluate`, `cntn_to_dcsn.evaluate` | The Evaluation that closes the builder, where a representation stands: one entry for everything the Evaluation stores, or one entry per stored object, `evaluate[V[<]]` for the value and `evaluate[D_{k}V[<]]` for the derivative a derivative line states, each with its own grid. |
| Block id and line id, `cntn_to_dcsn.risk_ce` | One authored line, marked `!node` here, whose result a representation can store at its Evaluation. |
| Block id and operator, `dcsn_to_arvl.E_ψ_ξ` | Every occurrence of that operator in the block; the operator alone at file level, `E_ψ_ξ`, every occurrence in the stage. |
| Block id, line id and operator, `dcsn_to_arvl.value.E_ψ_ξ` | One occurrence. |
| Function name, `𝑢` | A declared function, where a representation can store it. |

`stage.places()` lists the places of a stage with the kind of each. A [[term_address|term address]] can be inspectable without admitting a method; the derivative operator `D` admits none. Interpolation or an upper-envelope routine does not create an authored equation. The constrained part of the policy must be declared, as the clause on the candidate line of the consumption stage's methods file declares the corner, or an added numerical boundary segment identified as an extension outside the interior equality ([Constraints](../Bellman-Sym/10-constraints.md) §4.3).

## Specification contract

The stage verb `stage.methodize` reads its additions into the stage, which is elaborated anew from the union, so that the stage carries the method and grid components and the handlers the additions type. In a [[trellis]], `elaborate_trellis` reads at every position the additions the [[wiki/spec_factory|recipe]] names for the [[stage|stage occurrence]], in order, with the stage text, and `methodize_trellis` binds nothing more. A component typed by two files with different content is refused, an unknown method word and an unresolved path are refused, and a method at a place of a kind it does not admit is refused naming the place.

The entry [[specified_stage|specified stage]] states the order of the bindings. The [[wiki/spec_factory|specification factory]] states how the recipe combines its sources, and it creates no mathematical object. Whether a handler can carry a method out requires checks of the implementation in addition to the declared contract. See [Methodization](../Bellman-Sym/04-methodization.md) and [Stage functions](../Bellman-Sym/API/factory/stage-factory.md).
