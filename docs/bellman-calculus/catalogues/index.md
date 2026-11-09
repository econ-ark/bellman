---
title: "Appendix E — Catalogues"
short_title: "E. Catalogues"
status: drafted — reference catalogues
tags:
  - bellman-calculus
  - catalogue
  - operator
  - method
  - settings
  - methodization
authors:
  - Akshay Shanker
audience: user
type: reference
---
# Appendix E — Catalogues

> [!summary]
> These catalogues summarize the calculus's fields, functions, operators, parameters and numerical choices. The method types that a methods file can name are listed with the language, each with the operation of these catalogues it realizes.

> [!info]- Relationship with other documents
> **Builds on** — [Fields, functions and types](../04-fields,%20functions%20and%20types.md) and [Operators and builders](../05-Operators%20and%20builders.md) define the mathematical objects.
> **Formal account** — [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) states the classification conventions.
> **Used by** — [Method types](../../Bellman-Sym/reference/methods.md) and [Expression forms](../../Bellman-Sym/reference/forms.md): the language's catalogues, whose rows link to the operations of [Operators](./operators.md); [Methodization](../../Bellman-Sym/04-methodization.md) and [The Bellman factory](../../Bellman-Sym/08-bellman-factory.md): the current numerical attachment forms and the binding of occurrences.

The type catalogues describe the objects and function spaces used in the mathematical interpretation Υ. [Methods](../06-Methods.md) describes the numerical procedures of the construction Ρ. These maps distinguish meaning from numerical computation.

| Part | Catalogue | What it lists |
|---|---|---|
| E.1 | [Fields](./fields.md) | Declared quantities, value domains and information contexts. |
| E.2 | [Functions](./functions.md) | Representing functions, transitions, aggregators and policies with their domains. |
| E.3 | [Operators](./operators.md) | Mathematical operations and their input/output types. |
| E.4 | [Parameters and settings](./parameters-settings.md) | Economic inputs and numerical choices, classified by their mathematical role. |

> [!note] Related language references
> Bellman-SYM's Methodization page, listed under **Used by** above, explains how
> to attach numerical choices to a declared stage.

These calculus catalogues supply mathematical explanations rather than superseding the source grammar.

<a id="the-data-model"></a>

## 1. Catalogue entries

| Entry | Meaning | Reference |
|---|---|---|
| Operator | A mathematical operation with declared input and output types, called its rank. | [Operators](./operators.md) |
| Method | A numerical procedure for a supported place. | [Methods](../06-Methods.md) |
| Settings | Numerical inputs required by the selected procedure. | [Parameters and settings](./parameters-settings.md) |
| Handler | The implementation of a numerical procedure, including its input/output requirements. | [Handler](../../wiki/handler.md) |

A method may require its own representation and equation inputs. [Initial-algebra semantics](../APPX-B-INITIAL-ALGEBRA.md) states conditions for exact interpretation and refinement; [Operator algebra](../APPX-F-OPERATOR-ALGEBRA.md) §6 explains why numerical accuracy and stability require additional assumptions. No ordering between method tags and operator symbols is inferred merely from these inventory categories.

<a id="two-distinctions-that-keep-the-methods-catalogue-honest"></a>

## 2. Types and equation inputs

**Compatible types allow composition.** Distinct operations can have the same rank without the same meaning. An approximate method can change the values received by subsequent operations even when its declared boundaries agree. Numerical representation compatibility and approximation error must therefore be checked separately.

**The model supplies its equations.** Stage equations and local definitions are authored in `.bl`. Method entries select supported places and supply numerical choices; they do not invent omitted economic relations or make an implicit equation optimal. The current source rules of Bellman-SYM's Methodization page determine permitted place and reference forms. A method's tag binds no equation.

The method's documented settings specify the numerical inputs it accepts. A handler must interpret those settings as intended by its package. A grid that defines a discrete economic state or action space is model data; a grid approximating a continuous domain is numerical data. The same integer or real value can have either role depending on what it changes.

<a id="the-authoring-surface"></a>

## 3. Authoring

Stage source is `.bl`. Supporting YAML describes method assignments, settings, calibration and specification recipes. Bellman-SYM's Methodization page gives the current syntax and distinguishes a declared place from an available method attachment, and its page on the Bellman factory explains how bindings are resolved for occurrences.

Before using a method, establish that the place exists, the handler supports the required operation and its assumptions hold for the model. The comparison with other toolkits, the coverage map of the Rosetta stone, which is being rebuilt, is a separate inventory, not a default handler-selection rule.

<a id="see-also"></a>

## 4. Related documents

- [Fields, functions and types](../04-fields,%20functions%20and%20types.md) §5 — exact refinement and numerical methods.
- [Operators and builders](../05-Operators%20and%20builders.md) — the defined operations and their compositions.
- [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) — declared type relations and interpreted carriers.
- [Bellman calculus](../index.md) — chapter reading order.
