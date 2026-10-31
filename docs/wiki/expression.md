---
slug: expression
title: Expression
tags:
- syntax
- grammar
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/Bellman-Sym/03-field-equations.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/appendices/12-equation-parsing-rules.md
  class: canonical
  date: '2026-09-07'
- reference: "Backus, J. (1978). Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs. Communications of the ACM 21(8): 613–641. §13.1, p. 631, and §13.3.1, p. 632."
  class: external
  date: '2026-09-07'
merged_from:
- dolang
audience: user
type: concept
---

# Expression

An **expression** combines names, literals and operations. In [[sym|Bellman-SYM]], expressions occur on both sides of equations and within the definitions of functions, [[operator#Kernels|shock probability distributions]] and sets. For example, `m_d - c` denotes savings in the context supplied by the complete consumption [[stage]]. Arithmetic is parsed and its interpreted structure is retained; it is not opaque formula text reserved for a solver.

## Names, application and binding

Declarations determine a [[field]]'s domain, role and information context. Parentheses apply a function; ordinary brackets select a collection entry. [[perch|Perch]] marks distinguish arrival, decision and continuation references. A function argument or an expectation or optimization binder governs local identities: the same printed name in another scope need not denote the same variable.

The derivative term on a value field, `D_{a}V[>]`, a named marginal-utility function such as `𝑑𝑢` and differentiation of a declared function such as `D_{c}(𝑢)` are distinct forms. The term alone does not establish that a supplied representation evaluates the derivative; how a derivative is evaluated is fixed where the value is built. Likewise, an implicit policy equation remains a relation until its selection and other mathematical conditions are established.

A **block** is a complete authored typed group of equations, and the [[operator]] it denotes is its [[builder]]. An expression inside a block is not automatically another block, builder or authored node. Whole mathematical operations and `!node` boundaries can be inspected separately; addition and power remain inside their equation and function definitions. See [[semgraph]] and [[methodization]].

## Functional expressions

At the mathematical level, an expression can also represent a composition of functions. Backus (1978), *Can Programming Be Liberated from the von Neumann Style?*, §13.1 p. 631, represents functional forms by object sequences. The representation and meaning functions are part of the system's description (§13.3.1 p. 632). This comparison does not prescribe Bellman-SYM's parser or eliminate its temporary parsed AST (abstract syntax tree).

Use [Field equations](../Bellman-Sym/03-field-equations.md) and [Equation parsing rules](../Bellman-Sym/appendices/12-equation-parsing-rules.md) for current source forms.
