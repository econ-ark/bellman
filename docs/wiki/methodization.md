---
slug: methodization
title: Methodization
tags:
- method
- methodization
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
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

**Methodization** records numerical choices for existing supported computations in a [[stage]]. A **method** names a technique; a [[handler]] identifies the routine or adapter that performs it. Their [[settings]] describe numerical options. None supplies a missing model equation or proves that a computed policy is optimal.

The consumption stage `cons.bl` of the portfolio application attaches the endogenous grid method to its policy [block](../Bellman-Sym/01-stage.md#3-builder-blocks):

```yaml
methods:
  - on: policy
    method: !egm
    handler: cons-port:egm
```

The method binds at the Evaluation that closes the policy [[builder]], `policy:Evaluation`, because the block writes the grid line `m_d[>] = a + c[>]`, which gives the cash on hand at each saving; `stage.methods["policy"]` then answers it by the target as the file writes it. Only `on` is required: an entry without a method, `- on: policy`, records the target and attaches no numerical algorithm. A handler, a grid, settings and the roles of named equations are optional according to the method's contract.

## Where a method stands

A method type states the places it admits and the numerical options it reads ([method types](../Bellman-Sym/reference/methods.md)). A place is a whole builder, a line marked `!node` or any other [[statement]] with an id, a function the [[stage|stage file]] defines, the representation of a value function at the output of a [[backward_builder|backward builder]], or one occurrence of an [[operator]] inside a line. The address written under `on` names it:

| Address | Place |
|---|---|
| Block id, `policy` | The builder the block denotes; with `!egm`, the Evaluation that closes a policy block that writes the grid line. |
| Block id and line id, `cntn_to_dcsn.value` | One authored line; a representation method named there stands at the Evaluation of the [[field]] the line defines, as `!Cartesian` on `cntn_to_dcsn.value` stands at `cntn_to_dcsn:Evaluation`. |
| Operator name, `argmax` | Every occurrence of that operator in the stage. |
| Block id, line id and operator, `policy.choice.argmax` | One occurrence, overriding the stage-wide choice. |

`!vfi` stands on the backward decision builder alone, and a root finder on the [`Argmax`](../Bellman-Sym/reference/operations.md#argmax) row of an operative maximization line or on a joint `solve`. `stage.places()` lists the addresses of a stage with the kind of each place. A [[term_address|term address]] can be inspectable without supporting attachment. Implicit statements and operator occurrences need not carry `!node`; an authored node needs an explicit id to be a method target. Arithmetic inside an equation is not automatically an independent target. A block-level `!egm` on a policy block that writes no grid line is refused, and the refusal names the requirement.

Interpolation or an upper-envelope routine does not create an authored equation. The constrained part of the policy must be declared, as the clause on the candidate line of `cons.bl` declares the corner, or an added numerical boundary segment identified as an extension outside the interior equality ([Constraints](../Bellman-Sym/10-constraints.md) §4.3).

## Specification contract

The stage verb `stage.methodize(methods_source)` accepts a methods path or mapping and returns a new [[stage|stage version]] whose `stage.methods` holds each method by the place it binds at; `methodize_trellis(elaborated, syntactic)` applies it at every position of a [[trellis]]. Duplicate targets are errors, and unknown methods and unresolved targets are refused.

The entry [[specified_stage|specified stage]] states the order of the bindings. The [[trellis|syntactic trellis]] holds the merged mappings, and the stage verb binds; the [[wiki/spec_factory|specification factory]] states how the [[wiki/spec_factory|recipe]] combines source overrides, and it creates no mathematical targets. Target eligibility and numerical capability require implementation checks in addition to the declared contract. See [Methodization](../Bellman-Sym/04-methodization.md) and [Stage functions](../Bellman-Sym/API/factory/stage-factory.md).
