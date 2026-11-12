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
> **Formal account** — [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) defines the words these catalogues use: kinds, sorts, declared sets, the admissible sets of the parameters and of the settings, and the signatures of a stage.
> **Used by** — [Method types](../../Bellman-Sym/reference/methods.md) and [Expression forms](../../Bellman-Sym/reference/forms.md): the language's catalogues, whose rows link to the operations of [Operators](./operators.md); [Methodization](../../Bellman-Sym/04-methodization.md) and [The Bellman factory](../../Bellman-Sym/08-bellman-factory.md): the current numerical attachment forms and the binding of stage occurrences.

The catalogues of fields, functions and operators describe the objects and function spaces used in the mathematical interpretation Υ. [Methods](../06-Methods.md) describes the numerical procedures of the construction Ρ. These maps distinguish meaning from numerical computation.

| Part | Catalogue | What it lists |
|---|---|---|
| E.1 | [Fields](./fields.md) | Fields, each with its role, its declared set and its perch or, for a shock, its transition. |
| E.2 | [Functions](./functions.md) | Representing functions, laws of motion, aggregators and policies with their domains. |
| E.3 | [Operators](./operators.md) | Mathematical operations with their ranks, the input and output sorts of each. |
| E.4 | [Parameters and settings](./parameters-settings.md) | Parameters, which the stage file declares, and settings, which a methods file declares, with what each determines. |

> [!note] Related language references
> Bellman-SYM's Methodization page, listed under **Used by** above, explains how
> to attach numerical choices to a declared stage.

These catalogues list the objects of the calculus. [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) defines the words of the type system that they use, and the source grammar fixes the written forms.

<a id="the-data-model"></a>

## 1. Catalogue entries

| Entry | Meaning | Reference |
|---|---|---|
| Operator | A mathematical operation with a rank, its input sorts and its output sort ([Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §3). | [Operators](./operators.md) |
| Method | A numerical procedure for a supported place. | [Methods](../06-Methods.md) |
| Settings | Names that a methods file declares with a set, which the methods and the grids read ([Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §4). | [Parameters and settings](./parameters-settings.md) |
| Handler | The implementation of a numerical procedure, including its input/output requirements. | [Handler](../../wiki/handler.md) |

A method may require its own representation and equation inputs. [Initial-algebra semantics](../APPX-B-INITIAL-ALGEBRA.md) states conditions for exact interpretation and refinement; [Operator algebra](../APPX-F-OPERATOR-ALGEBRA.md) §6 explains why numerical accuracy and stability require additional assumptions. No ordering between method tags and operator symbols is inferred merely from these inventory categories.

<a id="two-distinctions-that-keep-the-methods-catalogue-honest"></a>

## 2. Types and equation inputs

**Matching sorts allow composition.** Two operators compose when the output sort of the first is the input sort of the second ([Methods](../06-Methods.md) §3). Distinct operations can have the same rank without the same meaning. An approximate method can change the values received by subsequent operations even when its declared boundaries agree. Numerical representation compatibility and approximation error must therefore be checked separately.

**The model supplies its equations.** Stage equations and local definitions are authored in `.bl`. Method entries select supported places and supply numerical choices; they do not invent omitted economic relations or make an implicit equation optimal. The current source rules of Bellman-SYM's Methodization page determine permitted place and reference forms. A method's tag binds no equation.

The method's documented options, the keyword arguments of its method word, specify the numerical inputs it accepts, and the value of an option may name a declared setting. A handler must interpret those options as intended by its package. A discrete economic state or action space that the model declares is the declared set of a field and no grid. A grid approximates a continuous domain, and the grid word that names it takes settings among its arguments ([Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §4). The same integer or real value can be a parameter or a setting: the file that declares it decides which, and the author chooses the file by what the value changes.

<a id="the-authoring-surface"></a>

## 3. Authoring

Stage source is `.bl`. A methods file is a `.bl` file as well: it writes the methods and the grids and declares the settings with their sets. YAML files hold the calibration, the values of the settings and the specification recipes. Bellman-SYM's Methodization page gives the current syntax and distinguishes a declared place from an available method attachment, and its page on the Bellman factory explains how bindings are resolved for stage occurrences.

Before using a method, establish that the place exists, the handler supports the required operation and its assumptions hold for the model. The comparison with other toolkits, the coverage map of the Rosetta stone, which is being rebuilt, is a separate inventory, not a default handler-selection rule.

<a id="see-also"></a>

## 4. Related documents

- [Fields, functions and types](../04-fields,%20functions%20and%20types.md) §5 — exact refinement and numerical methods.
- [Operators and builders](../05-Operators%20and%20builders.md) — the defined operations and their compositions.
- [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) — the account of types: kinds, sorts, declared sets, the admissible sets of the parameters and of the settings, and the signatures, the models and the versions of a stage.
- [Bellman calculus](../index.md) — chapter reading order.
