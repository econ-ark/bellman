---
title: Types
tags:
  - docs/reference
audience: user
type: reference
---

# Types

> [!summary]
> A **type** is what a [stage file](../../wiki/stage.md) or a [methods file](../04-methodization.md) writes after a colon, such as `ℝ₊₊ @ !ctrl` in the declaration `c : ℝ₊₊ @ !ctrl`. Its components are sets, a role word and a perch word, written with `@` between them, and several sets in one type declare their intersection. This page lists the objects of a stage with the type that each declaration writes, the role words, the perch words and their marks, the reserved sets, the forms in which a set is written, and the limits of the language on a type. Every table is printed from the package's own tables, so the page states each type as the package reads it.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](../01-stage.md) §2: declarations and types, with a complete file; [Symbol conventions](symbols-conventions.md) §9: the punctuation of a declaration, the domains and the type words.
> **Formal account** — [Appendix D](../../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) of the Bellman calculus: the classification of a field by its perch, its role and its value domain.
> **See also** — [Refusals](refusals.md): every refusal rule, with the smallest example that breaks it; [Rules and their code](rules.md): the rules of the language beside the functions that check them.

## 1 What a type is

A **declaration** is a name, a colon and a type. In `c : ℝ₊₊ @ !ctrl` the name is `c` and the type is `ℝ₊₊ @ !ctrl`. A type has up to three kinds of component, written in any order with `@` between them.

- A **set** states the values that the name may take. Several sets in one type declare their intersection: `β : (0,1) @ (0, R^(ρ-1))` declares a discount factor that lies in both intervals.
- A **role word** states what the name is in the decision problem: a state, a control, a value or a shock.
- A **perch word** states the [perch](../../wiki/perch.md) at which the name stands, one of the three information sets of a stage.

A type holds at most one role word and at most one perch word. The components that a declaration writes depend on the object that it declares: a parameter is declared with sets alone, while a [field](../../wiki/field.md) has a set, a role and a perch.

## 2 The tables

§2.1 lists the objects of a stage. For each object it gives a line that declares it, taken from an application of the repository, the type which that line writes, the class of the record in which the package holds the object once the file is read, and the expression that reads the object from the [stage object](../API/stage/01-the-stage.md).

§2.2 to §2.4 list the words of a type: the role words, the perch words with the mark that a name carries for each perch, and the sets that the grammar reserves.

§2.5 lists the forms in which a set is written. The **constructor** of a form is the name that the abstract grammar of the language gives it ([ASDL](../../wiki/asdl.md)). Each row gives a declaration that writes the form, the set that the form holds, and the objects in whose type the package reads it.

§2.6 lists the limits of the language on a type. A **refusal** is the package's answer to a file that it does not read, and it names the rule that the file breaks ([Refusals](refusals.md) §1). Each row gives a line that breaks the limit and the rule of its refusal.

<!-- Everything between the two markers below, with its headings, is written by docs/_hooks/reference_pages.py from the tables `OBJECTS`, `SET_FORMS` and `LIMITS` of the package (`packages/bellman/bellman/typing/type_table.py`) and from its vocabulary (`packages/bellman/bellman/syntax/vocabulary.py`); change the tables and run the script, never this part of the page by hand. -->
<!-- reference-table -->

### 2.1 Objects of a stage

Each line stands in a file of the repository and is quoted without its annotation, the part of a line after `::`. The files are `applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/perfect_foresight.bl`, `applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl` and `applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/methods.egm.bl`. A record is named by its module, as a path under `packages/bellman/bellman/`, and its class. The expression in the last column is written for the stage that the file states; where the line stands in a methods file, the stage has that methods file read.

| object | what it is | declared by | type written | record | read by |
|---|---|---|---|---|---|
| <a id="field"></a>field | A named quantity at a perch, with a declared set: a state, a control or a value. | `[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {`<br>in `perfect_foresight.bl` | `ℝ₊₊ @ !ctrl` for `c`: a set and a role word. The word `!dcsn` after the side gives the perch. A field listed with a set and no role word, `a : Xa`, is a state. | `native/records.py`: `Sort` | `stage.fields()["perfect_foresight:dcsn:c"]` |
| <a id="shock"></a>shock | A random quantity whose law the file states on a line of its own, `ψ ~ LogNormal(-(σ_ψ^2)/2, σ_ψ)`; it belongs to no perch. | `ψ : ℝ₊₊`<br>in `buffer_stock.bl` | `ℝ₊₊`: a set. The law is no part of the type. | `native/records.py`: `Sort` | `stage.fields()["buffer_stock:shck:ψ"]` |
| <a id="parameter"></a>parameter | A constant of the model, whose value the calibration supplies. | `β : ℝ₊₊ @ (0, R^(ρ-1))`<br>in `perfect_foresight.bl` | `ℝ₊₊ @ (0, R^(ρ-1))`: two sets, which declare their intersection. A parameter takes no role word and no perch word. | `native/records.py`: `Definition` | `stage.par["β"]` |
| <a id="derived-parameter"></a>derived parameter | A constant that the file defines from parameters, numbers and other derived parameters; the calibration supplies no value for it. | `h := 1/(1 - Γ/R)`<br>in `perfect_foresight.bl` | No type on this line. A definition may declare a set before `:=`, `q : (0,1) := (β*R)^(1/ρ)/R`, and calibration holds the value to that set. The declared set is the set written there, or `ℝ` where none is written; a definition by cases that writes the branch `inf` or `-inf` declares a set that can hold that infinity, as its form decides, as in `h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else inf`. | `native/records.py`: `Definition` | `stage.par["h"]` |
| <a id="setting"></a>setting | A value that a numerical method reads, such as the number of points of a grid; a methods file declares it, and `configure` binds its value. | `n_a : ℕ`<br>in `methods.egm.bl` | `ℕ`: a set. | `native/records.py`: `Definition` | `stage.settings["n_a"]` |
| <a id="function"></a>function | A function that the file defines by an expression in its arguments. | `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)`<br>in `perfect_foresight.bl` | `ℝ₊₊` for the argument `c`: one set for each argument. No set is written for the values of the function. | `native/records.py`: `Definition` | `stage.definitions["perfect_foresight:function:𝑢"]` |
| <a id="operator"></a>operator | The operator that a block denotes, called a builder: it takes the functions, or the measures, at one perch to those at another. | `[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {`<br>in `perfect_foresight.bl` | The two sides of the header: the fields that the block reads, `(V[>] : ℝ @ !vlu, c) : !cntn`, and the fields that it writes, `(V : ℝ @ !vlu) : !dcsn`. | `native/hypergraphs.py`: `Builder` | `stage.builder["cntn", "dcsn"]` |
| <a id="measure"></a>measure | A finite measure on the states of one perch, which the builder of a block that writes a state reads or writes. | `[id=arvl_to_dcsn, (k : Xa) : !arvl -> (m : Xm) : !dcsn] {`<br>in `perfect_foresight.bl` | No type: no line declares a measure. The package makes one on the states of each side of such a block, here on `Xa` at arrival and on `Xm` at decision. | `native/records.py`: `Sort` | `stage.builder["arvl", "dcsn"].signature()` |
| <a id="grid"></a>grid | The finite set of points at which a numerical method computes and stores a function. | `[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))`<br>in `methods.egm.bl` | `!Cartesian(a=(a_min, a_max, n_a))`: a grid constructor, whose arguments name settings. | `native/records.py`: `Definition` | `stage.methods["policy"].grid` |
| <a id="method"></a>method | The numerical procedure chosen for one operator. | `[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))`<br>in `methods.egm.bl` | `!egm`: a method word, followed by its keyword arguments where it takes any. | `native/records.py`: `Definition` | `stage.methods["policy"]` |
| <a id="perch"></a>perch | One of the three information sets of a stage: arrival, decision and continuation. | `[id=arvl_to_dcsn, (k : Xa) : !arvl -> (m : Xm) : !dcsn] {`<br>in `perfect_foresight.bl` | `!arvl` and `!dcsn`: the perch word after each side of the header. A mark on a name states the perch of one field, as `V[>]` does. | `stage/pieces.py`: `PerchHandle` | `stage.dcsn` |

### 2.2 Role words

A role word follows `!` among the components of a type, as in `c : ℝ₊₊ @ !ctrl`. A field that carries no role word is a state, and the subject of a line that states a law with `~` is a shock. A multiplier takes no role word: a line inside a block declares it together with its clause, as `μ[>] : ℝ₊ ⟂ a >= 0` does ([Constraints](../10-constraints.md) §4.2).

| role | word |
|---|---|
| state | `!state` |
| control | `!ctrl` |
| value | `!vlu` |
| shock | `!shck` |
| multiplier | — |

### 2.3 Perch words and marks

A perch word follows `!` after a side of a block header, as in `(k : Xa) : !arvl`. A mark is written directly after a name and states the perch of that one field. A name at the decision perch is written without a mark, and `V[~]` is read as `V`.

| perch | word | mark on a name |
|---|---|---|
| arrival | `!arvl` | `V[<]` |
| decision | `!dcsn` | none: `V` |
| continuation | `!cntn` | `V[>]` |

### 2.4 Reserved sets

The grammar reserves these names, and a file writes one without defining it. [Symbol conventions](symbols-conventions.md) §9.2 says what each set holds.

| set | also written | kind of number | interval |
|---|---|---|---|
| `ℝ` | — | real | `(-inf, inf)` |
| `ℝ₊` | `R_{+}`, `R+` | real | `[0, inf)` |
| `ℝ₊₊` | `R_{++}`, `R++` | real | `(0, inf)` |
| `ℤ` | — | integer | — |
| `ℕ` | — | integer | — |
| `ℝ̄` | — | extended real | — |
| `ℝ_{+∞}` | — | extended real | — |
| `ℝ_{-∞}` | — | extended real | — |
| `ℝ_{±∞}` | — | extended real | — |

### 2.5 Forms of a set expression

The last column names the objects of §2.1 in whose type the package reads the form. A field is taken there as a block header lists it, and §2.6 states what a declaration on a line of its own reads.

| constructor | written | what it holds | read in the type of |
|---|---|---|---|
| <a id="named"></a>`Named` | `R : ℝ₊₊` | The set of that name: a reserved set of the language, here the strictly positive real numbers, or a set that the file defines after `:=`, `Xa := ℝ₊`. | every object that is declared with a set |
| <a id="interval"></a>`Interval` | `ρ : (1, inf)` | The real numbers between two endpoints, where a round bracket leaves its endpoint out and a square bracket includes it; an endpoint may read parameters, and `-inf` or `inf` leaves a side unbounded; an endpoint that is the bare name of a parameter or of a derived parameter which the calibration values at an infinity is read as that infinity. | every object that is declared with a set |
| <a id="finite-set"></a>`FiniteSet` | `d : {work, retire}` | The labels listed, which carry no arithmetic. | [field](#field), [shock](#shock), [parameter](#parameter), [setting](#setting) and [function](#function) |
| <a id="product"></a>`Product` | `x : ℝ × ℝ` | The ordered tuples that take one component from each factor. | [field](#field), [shock](#shock), [parameter](#parameter), [setting](#setting) and [function](#function) |
| <a id="comprehension"></a>`Comprehension` | `θ : ℤ @ [1, inf)` | The members of one set that satisfy every condition stated, here the integers of at least one; several sets in one type are kept in this form, and a named set writes it with braces after `:=`, `H := {i : ℤ | i >= 0, i <= 1}`. | [shock](#shock), [parameter](#parameter), [derived parameter](#derived-parameter) and [setting](#setting) |
| <a id="integer-range"></a>`IntegerRange` | `j : {1, …, 5}` | Every integer from the first bound to the second, both included; a bound may read parameters, and `...` is a second spelling of `…`. | every object that is declared with a set |
| <a id="points"></a>`Points` | `s : {0, 1}` | The integers listed, in the order written; a list in which a member reads a parameter names the set its members lie in, `{0, θ} ⊂ ℤ`. | every object that is declared with a set |
| <a id="functions"></a>`Functions` | `δ : {1, …, 5} → ℝ` | The collections that hold one entry of the second set for each member of the first, which is a finite index set. | [field](#field), [shock](#shock), [parameter](#parameter), [setting](#setting) and [function](#function) |
| <a id="set-union"></a>`SetUnion` | `ρ : (0,1) \/ (1, inf)` | The numbers that lie in at least one of the sets; `∪` is a second spelling of `\/`. | [parameter](#parameter), [derived parameter](#derived-parameter) and [setting](#setting) |
| <a id="set-difference"></a>`SetDifference` | `ρ : ℝ₊₊ \ {1}` | The numbers of the first set that the second does not hold; `∖` is a second spelling of `\`. | [parameter](#parameter), [derived parameter](#derived-parameter) and [setting](#setting) |

### 2.6 Limits on a type

The package refuses each line below, in a stage file that holds no other declaration, under the rule beside it.

| limit | a line that breaks it | refusal |
|---|---|---|
| Several sets in one type are one set of numbers and the intervals that bound it, so at most one of them is written otherwise than as an interval; a named set counts as such a set. | `θ : ℤ @ ℝ₊₊` | [`syntax`](refusals.md#syntax) |
| The several sets of one type have a number in common, which the package decides from the endpoints that are numbers or ratios of two integers, `1/3`. | `β : (0,1) @ (2,3)` | [`syntax`](refusals.md#syntax) |
| Several sets in one type restrict one declared name, and no declaration of several names carries them. | `(w, c) : ℝ @ (0, 1)` | [`syntax`](refusals.md#syntax) |
| Several sets are read on a declaration that stands on a line of its own; a field listed on a block header and an argument of a function carry one set each. | `𝑓(x : ℝ₊ @ (0, 1)) := x^2` | [`readable-form`](refusals.md#readable-form) |
| A union and a difference are formed among sets of numbers; a set of labels, a product and a set of functions are no members of one. | `β : {a, b} \/ (0, 1)` | [`syntax`](refusals.md#syntax) |
| A union and a difference are read in the set of a parameter, of a derived parameter and of a setting; the set of a field, of a shock and of an argument of a function holds neither. | `c : ℝ₊₊ \ {1} @ !ctrl` | [`readable-form`](refusals.md#readable-form) |
| The value of a named set, written after `:=`, is no union and no difference. | `Xρ := (0,1) \/ (1, inf)` | [`syntax`](refusals.md#syntax) |
| The value of a named set holds no union and no difference inside it either, such as the set of the entries of a collection. | `Xq := {1, …, 2} → ℝ \ {0}` | [`readable-form`](refusals.md#readable-form) |
| A definition that declares a set reads at least one name; a value that reads none is a number, which the calibration supplies. | `ρ : ℝ := 2` | [`readable-form`](refusals.md#readable-form) |
| A conditional, `if … then … else …`, stands as the whole right side of a definition without arguments or as a branch of another conditional, and inside no formula, no function's body, no line of a block and no endpoint of a set. | `x : (0, if 1 < 2 then 1 else 2)` | [`syntax`](refusals.md#syntax) |
| In a derived parameter's definition `inf` and `-inf` stand only as a whole branch of a definition by cases; a definition that reads a name valued at an infinity where it is evaluated, in a formula, a call or a test, as the branch that its test chooses or as its whole right side, has no value at that calibration, and neither has a bound of a declared set that computes with such a name; a bound that computes with the written `inf`, `(0, 2*inf)`, has none at any calibration; a bound that calls a function other than `log`, `exp`, `min` and `max` is not decided, whatever it computes with. | `x := 2*inf` | [`derived-parameter`](refusals.md#derived-parameter) |
| The words `if`, `then` and `else` are words of the language and no names. | `if : ℝ₊₊` | [`syntax`](refusals.md#syntax) |
| A branch written `inf` or `-inf` stands in a definition whose declared set can hold that infinity, and the set `ℝ` of a definition that declares none holds neither. | `h := if 1 < 2 then 1 else inf` | [`derived-parameter`](refusals.md#derived-parameter) |

<!-- /reference-table -->
