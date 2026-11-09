---
slug: methods
title: Methods
description: The numerical method chosen for one operator of a stage, named by a word with keyword arguments and written as the typing of the operator's method component in the signature.
tags:
- methodization
- method
- type
wiki_status: budding
last_reviewed: '2026-11-05'
reviewed_by: Claude (Fable), session of 5 November 2026, at AAS's request; written from the decisions of 4 November 2026 on methods as components of the signature, checked against the Bellman calculus page on methods, and revised after one adversarial review round
sources:
- path: docs/bellman-calculus/06-Methods.md
  class: canonical
  date: '2026-11-05'
- path: docs/Bellman-Sym/reference/methods.md
  class: canonical
  date: '2026-11-05'
- reference: "Capucci, M., Gavranović, B., Hedges, J. and Rischel, E. F. (2022). Towards Foundations of Categorical Cybernetics. Electronic Proceedings in Theoretical Computer Science 372: 235–248. Definition 2, p. 236."
  class: literature
  date: '2026-11-05'
- reference: "Plotkin, G. and Pretnar, M. (2009). Handlers of Algebraic Effects. In Programming Languages and Systems (ESOP 2009), Lecture Notes in Computer Science 5502: 80–94. Abstract and §3.2."
  class: literature
  date: '2026-11-05'
audience: user
type: concept
---

# Methods

> [!summary]
> A **method** is the numerical procedure chosen for one [[operator]] of a [[stage]]: a quadrature rule for an expectation, an interpolant for the function an Evaluation stores, a solution method such as the endogenous grid method for the policy [[builder]]. It is named by a word with keyword arguments, `!gauss_hermite(n_ψ=n_ψ_nodes)`, `!Linear(extrap=clamp)`, `!egm`, and written as the typing of the operator's method component, `policy.method : !egm`, so that the method is a component of the operator's [[signature]] beside its [[signature|inputs and outputs]] and its [[grid]]. The model does not depend on it: forgetting every label leaves the model's operations unchanged, and forgetting the methods file returns the [[stage|stage file]].

> [!info]- Relationship with other documents
> **Formal account** — [Methods](../bellman-calculus/06-Methods.md): the signature with its components, composition, the method as a type, the handler, the erasures and the two levels.
> **Builds on** — [[grid|Grid]]: the discretized domain beside the method; [[settings|Settings]]: the names a method's arguments read; [[addition|Addition]]: the methods file that writes the entries.
> **Used by** — [[methodization|Methodization]]: the binding of methods to a stage and the places they bind at; [[handler|Handler]]: the program that computes a method; [Method types](../Bellman-Sym/reference/methods.md): the catalogue.

## 1 Where a method stands

A method types an operator and nothing else: not a [[field]], which is a quantity and not a computation, and not a side of a block header, the inputs before the arrow or the outputs after it, whose [[perch]] word types every coordinate listed on it. The entry is written in the methods file, an [[addition]] to the stage file, inside the bracket of the block that holds the operator, `[id=policy, policy.method : !egm | evaluate.method : !Linear] { … }`, the block's own method in the first group and each inner operator's in a group opened by `|`; or at file level with the full path, `dcsn_to_arvl.evaluate.method : !Linear`. The operators that admit a method are those `stage.places()` lists: a builder; the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that stores the builder's result, named by what it evaluates where the value and its stated derivative are represented apart, `evaluate[V[<]].method` and `evaluate[D_{k}V[<]].method`; an operator of a line, such as the expectation `E_ψ_ξ` or the maximization `argmax`; a line marked `!node`, a computation inside a block that the author names so that a method can stand on it; and a declared function. The derivative operator `D` admits no method.

Which methods an operator admits depends on its kind: the method is a type over the kind of operator, and the catalogue [Method types](../Bellman-Sym/reference/methods.md) lists each word with the kinds it admits and the keywords the package reads. A further keyword is read by the [[handler]] that computes the method. A method takes keyword arguments only, each valued by the name of a declared setting, a number, a quoted string or a word with its own arguments; a numerical choice that is to be configured is written as a declared setting's name, and no value is part of a signature.

## 2 What a method does to the stage

A method does one of three things, according to the operator it stands on. A **representation**, `!Linear` or `!pchip`, stores a function over the grid its grid component names: at the Evaluation that closes a builder, one entry for everything the Evaluation stores or one entry per stored object, each with its own grid; or at a `!node` line or a declared function. A **solution method**, `!egm` or `!vfi` or time iteration, stands on a builder and supplies the lines by which the builder is computed at the operative level, the stage keeping the declared lines in `stage.declared` ([[addition]] §3); `!vfi` supplies no lines. A method of an **operator of a line** fixes how that operation is computed: a quadrature or a discretization of a law at an expectation, `!gauss_hermite` or `!tauchen`, and a root finder or a search at a maximization. Interpolation and the comparison of candidates inside a method create no authored equation, and no method proves that a computed policy is optimal.

## 3 Composition and erasure

Two operators compose when the outputs of the first are the inputs of the second; the method plays no part in that condition, and a composite carries the list of its operators' labels, which are kept and never combined. This is the composition of parametrized morphisms of Capucci, Gavranović, Hedges and Rischel (2022, Definition 2, p. 236) under the trivial action. The exact meaning of a stage reads no label; the numerical semantics [Ρ](rho.md) reads each label as the routine its handler computes, a handler in the sense of Plotkin and Pretnar (2009): a model of the operators it admits, extended to every composite. Forgetting every label is the erasure $U_m$, and assigning them from a methods file the methodization $M_m$, with $U_m \circ M_m = \mathrm{id}$, the identity label, the list with no entries, standing on every operator without an entry; forgetting the methods file by its provenance is the second erasure, which returns the stage file ([Methods](../bellman-calculus/06-Methods.md) §8). A stage is **methodized** when any operator's signature carries a nonempty method component. `stage.methods` answers each method by the place it binds at, and `stage.builder[...].signature()` prints the two components beside the inputs and outputs.
