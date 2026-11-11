---
title: Refusals
tags:
  - docs/reference
  - bellman-sym
  - docs
  - user-facing
status: Draft — 20 September 2026
related:
  - "[[01-stage]]"
  - "[[01-the-stage]]"
date: 2026-09-20
audience: user
type: reference
---

# Refusals

> [!summary]
> A stage file the package cannot read is refused, and so is an entry of a methods file that names no place of a stage or a method at a place it does not admit, a setting's value outside its declared set, and a compilation the stage does not support. Every refusal says four things: where it is, what stands there, why it cannot be read, and what to write instead. This page lists every rule the package refuses under, each with the smallest example that breaks it and the refusal that example provokes. Every listing below is printed from the package, so what you read here is what your own session prints.

> [!info]- Relationship with other documents
> **Builds on** — [Stage tutorial](../01-stage.md): the file whose rules these are, written line by line.
> **Used by** — [The stage](../API/stage/01-the-stage.md): the object a file becomes once it passes them.

A refusal of the file is raised when the file is read: elaboration returns a stage or refuses the file. A refusal is held rather than raised only where the construction builds no graph for a form the file writes: the stage then holds a refusal under `not-constructed` in place of that graph, as it does for the forward builders graph where a shock's distribution names a family outside the table of [Shock distributions](laws.md). An entry of a methods file is refused when the stage is elaborated with the file, a setting's value when `configure` reads it, and a compilation when `compile_kernel()` is asked for it. Each refusal carries the rule it names as a field, so an editor or a script reads the rule rather than the sentence.

## 1 The four parts

Take the consumption stage and write `]` where a side of a block's header closes with `)`. The parser stops at that character, and the refusal reads:

```python
from bellman.refusal_examples import EXAMPLES
from bellman.refusal_catalogue import refusal_of

print(refusal_of(EXAMPLES["syntax"]))
```

```text
cons.bl:16:40-16:41: the file writes `]` here, and the language admits `)` or `,` at this place
    [id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊] : !dcsn -> (a : Xa) : !cntn] {
                                           ^ (rule syntax)
  write: a side of a block header: a side is parenthesized in general; a single coordinate may stand bare (V : !dcsn -> …)
```

**Where** is the file, the line and the column, which leads every refusal, as an editor and a compiler both print it. **What** is the line of the file with a mark under the column. **Why** is what the file writes there and the forms the language admits at that place, in the spellings you write them in. **What to write** is the sentence the grammar keeps for that place, given where the position falls, here inside the side of a block header.

A word the vocabulary does not hold is refused in the same four parts, at the word itself:

```python
from bellman.refusal_examples import Example
from bellman.refusal_catalogue import refusal_of

print(refusal_of(Example(
    rule="syntax", address=None, words=(),
    text="@stage: t\n[id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n")))
```

```text
t.bl:2:18-2:25: the file writes `!contrl` here, which is no word-type of the language
    [id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {
                     ^ (rule syntax)
  write: the word-types are !arvl, !cntn, !ctrl, !dcsn, !shck, !state, !vlu
```

## 2 The three vocabularies of rules

The package refuses under three closed vocabularies. The rules of **graph construction** are claims about the authored file: that it names itself once, that every name it writes is declared where it is used, that a forward block's header lists every field its lines read and a backward block's the value fields its lines read, with the controls at which they are read. The rules of **the names of the pieces** are the rules by which a name given to a query of the stage object, a box name or an identity, is read: that it names one piece of the version asked. The rules of the **Bellman factory** are claims about a model's files and the dictionaries made from them: the recipe, its source files and its fills, the trellis file, the records, the joins of a period, and a file given by its path to `load_stage` or to a binding verb, which is read as one YAML mapping with each key written once; each refusal names the file or the address, what stands there, why it is refused and what to write.

A representation method, such as `!Linear`, is typed at the [Evaluation](operations.md#evaluation) of a builder, and the methods file writes that place: `policy.evaluate` for the policy builder, whose Evaluation stores the policy function, and for a backward value builder `cntn_to_dcsn.evaluate`, for the value function and the derivative of it that a derivative line states together, or `cntn_to_dcsn.evaluate[V]` and `cntn_to_dcsn.evaluate[D_{m_d}V]` for each apart ([Methodization](../04-methodization.md) §2). The rules of graph construction refuse a word typed at a place of a kind its row does not admit, a representation on a builder among them (`method-admission`), one component written twice with different content, in one file or in two (`declared-twice`), or typed at one place by two paths (`component-typed-twice`), a path that names no place (`name-in-scope`) and a typing of the derivative operator (`no-method-for-derivative`); each refusal names the entry and what to write.

A representation names its basis as the method, such as `!Linear`, and the grid of its place by the place's own grid entry, `<place>.grid : !Cartesian(m=(m_min, m_max, n_m))`, each factor keyed by a coordinate of the function the place holds, a coordinate no factor names taking the default; the endogenous grid method names its grid of savings in the same way ([Methodization](../04-methodization.md) §3.2). The rules of graph construction check the grid: `grid-coordinate` and `grid-setting-declared` where the grid is typed, and `grid-bounds` at configuration; a setting's value is checked against its declared set under `setting-outside-set`, and a declared setting without a value is refused under `setting-unvalued`.

A rule is written once, in the package, and a refusal names it. The three tables below give each rule of each vocabulary: **written**, the rule's name as a refusal closes with it, `(rule X)`, or `; rule X)` after the address the refusal names, or the `rule` field for a refusal of a query's target; **operation**, what refuses under the rule: the Workbench's word for the operation that meets the refusal, `parse`, `elaborate`, `configure`, `connect` or `read`, and `query` for a rule that a query of the stage object refuses under, such as `kernel`, `compile_kernel` or `card`; **claim**, what the rule requires, in the words of the package; **denotes**, a dash, since a rule is a claim about the file and not an object of the Bellman calculus; and **read from**, the module under `packages/bellman/bellman/`, its table and the key. The name of a rule is the anchor of its row, so a refusal's rule links its entry here, `refusals/#name-in-scope`, which is the link the Workbench's Rule link opens.

<!-- reference-table -->

### 2.1 Graph construction

| rule | written | operation | claim | denotes | read from |
|---|---|---|---|---|---|
| <a id="syntax"></a>`syntax` | `(rule syntax)` | `parse` | The file is written in the forms the grammar admits, and every !-marked word is one of the vocabulary. It is the first rule a file meets: the refusal is raised where the parser or the lowering stops, and names the forms admitted at that place. | — | `refusals.py`, `RULES`, `"syntax"` |
| <a id="marginal-role-retired"></a>`marginal-role-retired` | `(rule marginal-role-retired)` | `elaborate` | The roles `!mrgnvl` and `!sndmrgnvl` are retired from the language: a backward header lists value fields and controls, and a derivative of a value is the term `D_{x}V`. | — | `refusals.py`, `RULES`, `"marginal-role-retired"` |
| <a id="stage-name"></a>`stage-name` | `(rule stage-name)` | `elaborate` | The file names itself once: exactly one `@stage` line, with a name. | — | `refusals.py`, `RULES`, `"stage-name"` |
| <a id="declared-once"></a>`declared-once` | `(rule declared-once)` | `elaborate` | Each name, block id, statement id, and law is written once. | — | `refusals.py`, `RULES`, `"declared-once"` |
| <a id="defined-once"></a>`defined-once` | `(rule defined-once)` | `elaborate` | Within one block, an operative equation defines each name-sided left side once, and a derivative line states each derivative term, `D_{m}V`, once. A documentary line (`!doc`) defines and states none. | — | `refusals.py`, `RULES`, `"defined-once"` |
| <a id="one-name-one-meaning"></a>`one-name-one-meaning` | `(rule one-name-one-meaning)` | `elaborate` | A name is one of a field, a function, a named space, a shock or a parameter, and is not the name of a numerical operator. | — | `refusals.py`, `RULES`, `"one-name-one-meaning"` |
| <a id="parameter-or-field"></a>`parameter-or-field` | `(rule parameter-or-field)` | `elaborate` | A top-level scalar declaration is a parameter; only a shock is both declared at the top level and listed on the side of a block. | — | `refusals.py`, `RULES`, `"parameter-or-field"` |
| <a id="field-perch"></a>`field-perch` | `(rule field-perch)` | `elaborate` | Every listed field has one perch, fixed by its side's perch word, its mark, or its role, and the three must agree. | — | `refusals.py`, `RULES`, `"field-perch"` |
| <a id="name-in-scope"></a>`name-in-scope` | `(rule name-in-scope)` | `elaborate` | Every name a statement, method entry or definition body mentions is declared where it is used, and every set a typing names, `n_m : Foo`, is a named set the stage defines or a set of the language. | — | `refusals.py`, `RULES`, `"name-in-scope"` |
| <a id="family-selection"></a>`family-selection` | `(rule family-selection)` | `elaborate` | A selection takes a coordinate of a declared family by a key the family admits. | — | `refusals.py`, `RULES`, `"family-selection"` |
| <a id="well-typed"></a>`well-typed` | `(rule well-typed)` | `elaborate` | Every operation of a line, a function body or a declared set reads values of the kinds it takes: arithmetic, an ordered comparison and the bounds of an interval read numbers, and a label is no number; a function is applied to as many arguments as it declares, each of the kind it declares; `Inv` inverts one function; the two sides of a line are of one kind, and its left side names one field for each result of its right side. | — | `refusals.py`, `RULES`, `"well-typed"` |
| <a id="divisor-nonzero"></a>`divisor-nonzero` | `(rule divisor-nonzero)` | `elaborate` | A divisor the file writes as a number is not zero: a division by a written zero is defined at no point (the definedness conditions of the fold). | — | `refusals.py`, `RULES`, `"divisor-nonzero"` |
| <a id="shock-observed"></a>`shock-observed` | `(rule shock-observed)` | `elaborate` | A statement's perch has observed every shock the statement's right side depends on; otherwise the statement asks for an expectation. | — | `refusals.py`, `RULES`, `"shock-observed"` |
| <a id="shock-reintroduced"></a>`shock-reintroduced` | `(rule shock-reintroduced)` | `elaborate` | A backward function does not read a shock again beside a term whose expectation has integrated it. | — | `refusals.py`, `RULES`, `"shock-reintroduced"` |
| <a id="forward-composite"></a>`forward-composite` | `(rule forward-composite)` | `elaborate` | The fields a statement's right side mentions are at the left side's perch, before it, or forward of it along the stage's transitions. | — | `refusals.py`, `RULES`, `"forward-composite"` |
| <a id="one-builder-per-output"></a>`one-builder-per-output` | `(rule one-builder-per-output)` | `elaborate` | One block writes a field between two perches: a second block that joins the same perches and writes a field the first writes is refused naming both blocks. | — | `refusals.py`, `RULES`, `"one-builder-per-output"` |
| <a id="candidate-coordinate"></a>`candidate-coordinate` | `(rule candidate-coordinate)` | `elaborate` | A candidate line of a policy block, `x[>] = …`, names a control at the candidate points, `c[>]`, a state of the decision perch, the grid line `m[>] = a + c[>]`, or the value candidate an upper envelope of the block compares; any other name is refused with the coordinates in scope. | — | `refusals.py`, `RULES`, `"candidate-coordinate"` |
| <a id="candidate-read"></a>`candidate-read` | `(rule candidate-read)` | `elaborate` | A candidate a policy block writes is read by a later line of the block or is the grid line, whose points are the knots of the policy; a candidate nothing reads is refused naming the line. | — | `refusals.py`, `RULES`, `"candidate-read"` |
| <a id="transition-without-expectation"></a>`transition-without-expectation` | `(rule transition-without-expectation)` | `elaborate` | A transition block's statements define the state transition g and contain no expectation: the forward builder is the push-forward of a measure through g, and integration over a shock belongs to a value block (Operators and builders, §"Forward operators"). | — | `refusals.py`, `RULES`, `"transition-without-expectation"` |
| <a id="one-implicit-statement"></a>`one-implicit-statement` | `(rule one-implicit-statement)` | `elaborate` | A block has at most one implicit statement for each output field. | — | `refusals.py`, `RULES`, `"one-implicit-statement"` |
| <a id="definition-order"></a>`definition-order` | `(rule definition-order)` | `elaborate` | The function definitions have a dependency order, and each applies a defined function. | — | `refusals.py`, `RULES`, `"definition-order"` |
| <a id="derivative-one-name"></a>`derivative-one-name` | `(rule derivative-one-name)` | `elaborate` | A derivative names one formal argument, not several arguments at once. | — | `refusals.py`, `RULES`, `"derivative-one-name"` |
| <a id="derivative-scalar-coordinate"></a>`derivative-scalar-coordinate` | `(rule derivative-scalar-coordinate)` | `elaborate` | The one formal argument a derivative names is scalar, not product-valued. | — | `refusals.py`, `RULES`, `"derivative-scalar-coordinate"` |
| <a id="derivative-coordinate"></a>`derivative-coordinate` | `(rule derivative-coordinate)` | `elaborate` | A derivative of a value field, `D_{a}V[>]`, names a state coordinate of the perch at which the field is read, and not a discrete one; for the value of a branch, `D_{a_w}V_w[>]`, a state the branch writes. | — | `refusals.py`, `RULES`, `"derivative-coordinate"` |
| <a id="stage-boundary"></a>`stage-boundary` | `(rule stage-boundary)` | `elaborate` | Every field is produced and consumed: a block writes it or the stage receives it, and a block reads it or the stage delivers it. | — | `refusals.py`, `RULES`, `"stage-boundary"` |
| <a id="output-defined"></a>`output-defined` | `(rule output-defined)` | `elaborate` | Every required block output has an equation. | — | `refusals.py`, `RULES`, `"output-defined"` |
| <a id="grid-line-consistency"></a>`grid-line-consistency` | `(rule grid-line-consistency)` | `elaborate` | A grid line, a line that writes a decision state under the continuation mark (`m_d[>] = a + c[>]`), agrees with the law of motion solved for that state at the candidates: its right side and the law of motion so solved reduce to one expression, every function read as an opaque symbol. | — | `refusals.py`, `RULES`, `"grid-line-consistency"` |
| <a id="identity-collision"></a>`identity-collision` | `(rule identity-collision)` | `elaborate` | No authored name collides with the spelling of an identity: a name containing the colon that separates its segments, or a name equal to one of the words a reader tests for in the last segment, `result`, `declared` or `merged`. | — | `refusals.py`, `RULES`, `"identity-collision"` |
| <a id="readable-form"></a>`readable-form` | `(rule readable-form)` | `elaborate` | The item is a form the construction rules read. | — | `refusals.py`, `RULES`, `"readable-form"` |
| <a id="component-typed-twice"></a>`component-typed-twice` | `(rule component-typed-twice)` | `elaborate` | A component of an operator's signature, its method, its grid or its handler, is typed by one entry: two entries at one place, an entry for the whole of an Evaluation beside one for an object it stores, or a stage-wide or block-wide operator head beside one of its occurrences, are refused naming both. | — | `refusals.py`, `RULES`, `"component-typed-twice"` |
| <a id="no-method-for-derivative"></a>`no-method-for-derivative` | `(rule no-method-for-derivative)` | `elaborate` | The derivative operator `D` and its occurrences admit no typing: nothing is differentiated by a method, and a definition by `D` is an authored expression or a handler's. | — | `refusals.py`, `RULES`, `"no-method-for-derivative"` |
| <a id="method-admission"></a>`method-admission` | `(rule method-admission)` | `elaborate` | A method word stands at a place of a kind its row of the catalogue admits, a representation at an Evaluation, a quadrature at an expectation, a solution method on a builder, and its entry writes every keyword the row requires there, one count per shock for a quadrature's nodes. | — | `refusals.py`, `RULES`, `"method-admission"` |
| <a id="representation-source"></a>`representation-source` | `(rule representation-source)` | `elaborate` | A function representation's family accepts the data its place supplies, chosen in the order of an authored table, the policy pairs of an `!egm` builder's closing Evaluation, a complete authored expression with an explicit kernel, and the family's own nodes; missing data selects no other case, and an optional grid beside an authored table discretizes the coordinates at which the table is evaluated, written as a name or as a tuple of names in the order of the grid's coordinates, and has exactly its finite support where both are known at configuration. | — | `refusals.py`, `RULES`, `"representation-source"` |
| <a id="explicit-solution"></a>`explicit-solution` | `(rule explicit-solution)` | `elaborate` | An `!explicit` builder is a policy or backward value builder to which an addition appends lines in a block of the builder's id, `[id=policy, policy.method : !explicit]`, which stand in place of the declared lines at the operative level; a builder with no such block is refused. The lines write every output by `output = expression` on the states of the builder's own perch, the parameters, the derived parameters and the names the block introduces, with a compiled kernel for each output: a line that reads an input of the builder's header, a value input or its derivative or a control at which a value builder's declared lines are read, states a relation or applies an operator on its right side is refused naming `!egm` or `!time_iteration`, a line that defines or reads a field at another perch, the candidate `c[>]` or the identification `c = c[>]`, naming `!egm`, and a block that writes no output with the line `<output> = <expression>` to write; each refusal stands at the line at fault, and at the typing entry where no line is. A complete block of such lines under `!egm` or `!time_iteration`, appended by an addition or written in the stage file, is refused, naming `!explicit`. | — | `refusals.py`, `RULES`, `"explicit-solution"` |
| <a id="declared-twice"></a>`declared-twice` | `(rule declared-twice)` | `elaborate` | Over the files of a stage, a component is typed once, whether by an absolute or a relative spelling of its path, a name is defined once, or identically in each file, and a line id names one line of a block; the union of the stage file and its additions refuses a second entry, definition or line naming both positions. | — | `refusals.py`, `RULES`, `"declared-twice"` |
| <a id="label-not-in-parent"></a>`label-not-in-parent` | `(rule label-not-in-parent)` | `elaborate` | A nested block of an addition merges with the branch of the same label under its parent, and a path inside a block names a line or an operator of that block: a label the parent lacks, and a first segment that names another block, are refused. | — | `refusals.py`, `RULES`, `"label-not-in-parent"` |
| <a id="type-conflict"></a>`type-conflict` | `(rule type-conflict)` | `elaborate` | The field names determine a signature: a coordinate an addition restates keeps the stage's typing, and a different type on it, or a different perch word on its side, is refused. | — | `refusals.py`, `RULES`, `"type-conflict"` |
| <a id="metadata-mismatch"></a>`metadata-mismatch` | `(rule metadata-mismatch)` | `elaborate` | An addition names the stage it adds to, `@methods: <stage>`, with the name the stage file gives itself, and a metadata line of another key agrees with the stage file's line of that key. | — | `refusals.py`, `RULES`, `"metadata-mismatch"` |
| <a id="grid-coordinate"></a>`grid-coordinate` | `(rule grid-coordinate)` | `elaborate` | Every factor of a grid names a coordinate of the function the place holds, a control of the builder for a feasible factor or a shock for a quadrature factor; a coordinate no factor names takes the default, the product over the coordinates of that function, as every coordinate does where the place writes no grid entry; a method that reads no grid has none written at its place, and a representation fitted from the pairs the endogenous grid method computes has no grid of its own at the Evaluation of the builder that method solves, since its nodes are the endogenous points of the pairs. A grid constructor stands only at the places its record admits, `!Fibred` only where the occurrence's domain is its base's states followed by its fibre's controls; the base of `!Fibred` is `!Points` or a `!Cartesian` term on the states, and its fibre a `!Cartesian` term of feasible-control factors; each declared point of `!Points` has one coordinate for each coordinate of the place. | — | `refusals.py`, `RULES`, `"grid-coordinate"` |
| <a id="grid-setting-declared"></a>`grid-setting-declared` | `(rule grid-setting-declared)` | `elaborate` | Every name a factor of a grid writes is a setting the methods file declares, a node set the stage defines or an expectation operator of the stage, and the declared points of `!Points` are a setting the methods file declares or a set the stage defines; a bound or a count written as a number is refused. | — | `refusals.py`, `RULES`, `"grid-setting-declared"` |
| <a id="grid-bounds"></a>`grid-bounds` | `(rule grid-bounds)` | `configure` | At configuration the bounds of a factor are in order and inside the coordinate's declared set, its count is at least two, and a node set is strictly increasing; each configured point of `!Points` has finite real coordinates inside the coordinates' declared sets. | — | `refusals.py`, `RULES`, `"grid-bounds"` |
| <a id="grid-requirement"></a>`grid-requirement` | `(rule grid-requirement)` | `elaborate` | The predicate words a grid writes after `require` are among `!Empty`, `!Cartesian`, `!NonCartesian` and `!UniformCartesian`, and no two contradict each other; each holds of the grid wherever the bound values decide it, an outer requirement of `!Fibred` of the joint grid and one inside its fibre of each fibre. The numerical construction of a grid establishes its finite points, a factor for each coordinate, a sampler for each feasible set and every required property before the grid is used, and reports what it cannot establish instead of supplying a default. | — | `refusals.py`, `RULES`, `"grid-requirement"` |
| <a id="setting-outside-set"></a>`setting-outside-set` | `(rule setting-outside-set)` | `configure` | A setting's configured value lies in the set its declaration names. | — | `refusals.py`, `RULES`, `"setting-outside-set"` |
| <a id="setting-unvalued"></a>`setting-unvalued` | `(rule setting-unvalued)` | `configure` | Every setting the methods file declares, and every setting a bound method's keyword arguments or grid name, has a value when settings are bound. | — | `refusals.py`, `RULES`, `"setting-unvalued"` |
| <a id="multiplier-declaration"></a>`multiplier-declaration` | `(rule multiplier-declaration)` | `elaborate` | A multiplier is declared inside the block whose continuation grid it extends, once, marked `[>]`, with one declared set and one bound after ⟂ that names continuation states, multipliers of the block, parameters, numbers or `inf`. | — | `refusals.py`, `RULES`, `"multiplier-declaration"` |
| <a id="set-mismatch"></a>`set-mismatch` | `(rule set-mismatch)` | `elaborate` | A field produced on one declared set and consumed on another is declared with sets whose inclusion holds; otherwise the stage declares the inclusion through the control's feasible set. | — | `refusals.py`, `RULES`, `"set-mismatch"` |
| <a id="category-codes"></a>`category-codes` | `(rule category-codes)` | `elaborate` | A set marked `!categories` is a nonempty range of integers written as a comprehension over ℤ or ℕ, whose annotation gives each member one category name and each name one member. The marker is written only on a top-level named set, and a field declared on a set with category codes names that set at every site that names a set. | — | `refusals.py`, `RULES`, `"category-codes"` |
| <a id="value-input-role"></a>`value-input-role` | `(rule value-input-role)` | `elaborate` | A statement of a backward block reads values or marginal values, not both: its kernel acts on one role and its output has that role. | — | `refusals.py`, `RULES`, `"value-input-role"` |
| <a id="signature-complete"></a>`signature-complete` | `(rule signature-complete)` | `elaborate` | A forward block's header lists every field its lines read that no earlier line of the block defines. A backward block's header lists the value fields its lines read and the controls at which they are read, but no state; a state of its output perch is a coordinate. A value field a backward header lists and no line of the block reads is admitted: it is left out of the block's builder and recorded as a diagnostic, `unread-input`, in place of a refusal. | — | `refusals.py`, `RULES`, `"signature-complete"` |
| <a id="header-coordinate"></a>`header-coordinate` | `(rule header-coordinate)` | `elaborate` | A backward block's header lists the value fields it reads and writes and the controls at which its lines are read, and no state: a state of the perch at which its output stands is a coordinate of the output function, and a state of its input perch is reached through the law of motion. | — | `refusals.py`, `RULES`, `"header-coordinate"` |
| <a id="input-perch-state"></a>`input-perch-state` | `(rule input-perch-state)` | `elaborate` | A backward line reads a state of its input or a later perch only through the law of motion. A direct read is refused, including in a relation or a condition after `⟂`. A read under the expectation over the edge's shock and continuation-state indexing on a policy candidate line are admitted. | — | `refusals.py`, `RULES`, `"input-perch-state"` |
| <a id="kernel-form"></a>`kernel-form` | `(rule kernel-form)` | `query` | A kernel that `compile_kernel` writes as a Python function is retained arithmetic and calls to closed-form functions; a symbolic derivative has no compile rule. The function takes the values of the parameters it reads as arguments, so a symbolic version compiles too and answers no values, `parameter_values` None. | — | `refusals.py`, `RULES`, `"kernel-form"` |
| <a id="method-option-value"></a>`method-option-value` | `(rule method-option-value)` | `configure` | Every configured keyword argument of a method lies in the domain its row of the catalogue names for it. | — | `refusals.py`, `RULES`, `"method-option-value"` |
| <a id="kernel-target"></a>`kernel-target` | `(rule kernel-target)` | `query` | `kernel` and `compile` read a primitive operator box, and `compile` one whose kernel is g or G. | — | `refusals.py`, `RULES`, `"kernel-target"` |
| <a id="distribution-dependency"></a>`distribution-dependency` | `(rule distribution-dependency)` | `elaborate` | The distribution declarations read one another without a cycle, and a declaration does not read its own subject. | — | `refusals.py`, `RULES`, `"distribution-dependency"` |
| <a id="distribution-edge"></a>`distribution-edge` | `(rule distribution-edge)` | `elaborate` | The shocks of connected declarations are drawn on the edge of one forward builder. | — | `refusals.py`, `RULES`, `"distribution-edge"` |
| <a id="distribution-domain"></a>`distribution-domain` | `(rule distribution-domain)` | `elaborate` | A declaration's family parameters lie in the family's domain: matched dimensions, a symmetric positive semidefinite covariance, nonnegative variances and deviations, finite endpoints in order, positive scales, and real arguments that have a number. | — | `refusals.py`, `RULES`, `"distribution-domain"` |
| <a id="derived-parameter"></a>`derived-parameter` | `(rule derived-parameter)` | `elaborate` | A derived parameter's definition, `h := 1/(1 - Γ/R)`, reads declared parameters, finite numbers and other derived parameters, and is formed by signs, sums, differences, products, quotients, powers and the calls `log` and `exp` of one argument; the calibration supplies no value for it, and at the calibration values every operation of its definition is defined and its value is a finite real number. | — | `refusals.py`, `RULES`, `"derived-parameter"` |
| <a id="conditional-not-declared"></a>`conditional-not-declared` | `(rule conditional-not-declared)` | `elaborate` | The conditional distribution an expectation needs is a declared conditional, a product of them, or a marginal or conditional of a joint normal declaration whose conditioning block is positive definite. | — | `refusals.py`, `RULES`, `"conditional-not-declared"` |
| <a id="branch-form"></a>`branch-form` | `(rule branch-form)` | `elaborate` | A branching block holds one labeled nested block per label and nothing else, at least two, in the forward block from the decision perch to the continuation perch, whose own output side is empty; a nested block has an empty input side and writes continuation fields. | — | `refusals.py`, `RULES`, `"branch-form"` |
| <a id="branch-labels"></a>`branch-labels` | `(rule branch-labels)` | `elaborate` | The nested blocks carry the labels of the block's label coordinate, a control or a shock with its law, whose set is a finite set of at least two labels, each once and in the set's order. | — | `refusals.py`, `RULES`, `"branch-labels"` |
| <a id="branch-tuple-mismatch"></a>`branch-tuple-mismatch` | `(rule branch-tuple-mismatch)` | `elaborate` | The value line selects by one tuple indexed by the label coordinate, one entry per label, and the policy maximizes over the same tuple in the same order; a branch a shock selects is read under the expectation over the shock alone. | — | `refusals.py`, `RULES`, `"branch-tuple-mismatch"` |
| <a id="branch-value-position"></a>`branch-value-position` | `(rule branch-value-position)` | `elaborate` | A continuation value stands at one position of the selection tuples, the position of the branch on whose fields it is a function. | — | `refusals.py`, `RULES`, `"branch-value-position"` |
| <a id="branch-law"></a>`branch-law` | `(rule branch-law)` | `elaborate` | The law of a label shock gives one probability to each label in the order of the labels, `Categorical((p₁, …, pₙ))` or `Bernoulli(p)` over two. | — | `refusals.py`, `RULES`, `"branch-law"` |
| <a id="not-constructed"></a>`not-constructed` | `(rule not-constructed)` | `elaborate` | The item is a form of the language the construction does not read. | — | `refusals.py`, `RULES`, `"not-constructed"` |

### 2.2 The names of the pieces

| rule | written | operation | claim | denotes | read from |
|---|---|---|---|---|---|
| <a id="target-not-found"></a>`target-not-found` | `rule = 'target-not-found'` | `query` | A name given to a query of the stage object, a box name or an identity, names a piece the version asked holds. | — | `refusals.py`, `TARGET_RULES`, `"target-not-found"` |
| <a id="target-ambiguous"></a>`target-ambiguous` | `rule = 'target-ambiguous'` | `query` | A name given to a query reaches one piece of the version, not two. | — | `refusals.py`, `TARGET_RULES`, `"target-ambiguous"` |
| <a id="target-version"></a>`target-version` | `rule = 'target-version'` | `query` | An object given to a query belongs to the version asked: a box or a record of one version is not read against another version, since versions share no object. | — | `refusals.py`, `TARGET_RULES`, `"target-version"` |

### 2.3 The Bellman factory

| rule | written | operation | claim | denotes | read from |
|---|---|---|---|---|---|
| <a id="recipe-shape"></a>`recipe-shape` | `(rule recipe-shape)` | `read` | The recipe names its trellis file under `trellis:` and has a `stages` mapping; each stage key stands once and its entry names its stage file under `stage:`, each file by its path from the recipe's folder; each kind block is a mapping with an `all` list; a range key is written `lo-hi` with lo ≤ hi and no two ranges of one list overlap; `periods:` is a pair. | — | `refusals.py`, `FACTORY_RULES`, `"recipe-shape"` |
| <a id="recipe-source"></a>`recipe-source` | `(rule recipe-source)` | `read` | Every source name is relative to the registry without `..`, names a file the registry holds, of the kind of the list it stands in, and its `parent:` chain neither cycles nor exceeds ten files. | — | `refusals.py`, `FACTORY_RULES`, `"recipe-source"` |
| <a id="recipe-slot-unknown"></a>`recipe-slot-unknown` | `(rule recipe-slot-unknown)` | `read` | Every fill names a slot the recipe declares by a `$` name in one of its source lists. | — | `refusals.py`, `FACTORY_RULES`, `"recipe-slot-unknown"` |
| <a id="recipe-template-agreement"></a>`recipe-template-agreement` | `(rule recipe-template-agreement)` | `read` | Every stage the recipe names occupies a period the trellis file holds, and every stage a period holds is named by the recipe. | — | `refusals.py`, `FACTORY_RULES`, `"recipe-template-agreement"` |
| <a id="slot-value-not-a-mapping"></a>`slot-value-not-a-mapping` | `(rule slot-value-not-a-mapping)` | `read` | A slot is bound to a mapping. | — | `refusals.py`, `FACTORY_RULES`, `"slot-value-not-a-mapping"` |
| <a id="fill-names-nothing"></a>`fill-names-nothing` | `(rule fill-names-nothing)` | `read` | Every key of a fill names a parameter or a setting a receiving stage declares, or a name the `registry` block admits. | — | `refusals.py`, `FACTORY_RULES`, `"fill-names-nothing"` |
| <a id="fill-mixes-kinds"></a>`fill-mixes-kinds` | `(rule fill-mixes-kinds)` | `read` | A flat fill names parameters or settings, not both. | — | `refusals.py`, `FACTORY_RULES`, `"fill-mixes-kinds"` |
| <a id="trellis-file-shape"></a>`trellis-file-shape` | `(rule trellis-file-shape)` | `read` | A trellis file, or a trellis dictionary, lists its `periods` and its `inter_connectors`; each period holds `stages` and `connectors`; each record of a file names its `stage`. | — | `refusals.py`, `FACTORY_RULES`, `"trellis-file-shape"` |
| <a id="record-shape"></a>`record-shape` | `(rule record-shape)` | `elaborate` | A record holds `stage` as `{text, origin}` and its three mappings, and a supplied digest or origin agrees with the source. | — | `refusals.py`, `FACTORY_RULES`, `"record-shape"` |
| <a id="period-join-cycle"></a>`period-join-cycle` | `(rule period-join-cycle)` | `connect` | The pairs of a period, authored by its connectors or inferred from equal field names, close no cycle, and no connector joins a stage to itself. | — | `refusals.py`, `FACTORY_RULES`, `"period-join-cycle"` |
| <a id="connector-names-no-field"></a>`connector-names-no-field` | `(rule connector-names-no-field)` | `connect` | A connector is a mapping, flat or in the keyed form {from, to, fields} within a period, and one entry maps a continuation field; a connector whose endpoint names no field, or several, is a diagnostic of the trellis's selection of its connections and no refusal. | — | `refusals.py`, `FACTORY_RULES`, `"connector-names-no-field"` |
| <a id="period-parameter-agreement"></a>`period-parameter-agreement` | `(rule period-parameter-agreement)` | `connect` | A parameter name two or more stages of one period declare names one parameter of the period: the sets the stages declare it with have one nonempty intersection the package reads, the stages' sources supply it one value, and that value lies in every declared set; a setting name two or more stages declare in their methods files names one setting of the period in the same way. | — | `refusals.py`, `FACTORY_RULES`, `"period-parameter-agreement"` |
| <a id="readable-file"></a>`readable-file` | `(rule readable-file)` | `read` | A stage file, read by its path or named under `stage:` in a recipe, is a readable `.bl` file of UTF-8 text; a source file a binding verb reads, or a record of a trellis file names, is a readable YAML mapping that writes each key once. | — | `refusals.py`, `FACTORY_RULES`, `"readable-file"` |

<!-- /reference-table -->

## 3 The catalogue

Every rule's entry: the rule with its vocabulary and the operation that refuses under it, its condition, the claim of the tables above, and, under the label `example`, the four parts of the refusal its example provokes, the smallest example the package keeps for it. The example of each rule is the text the refusal test provokes, so a rule that changes is read here and in the test at once; the Workbench shows the same entry beside a refusal's sentence, answered by the package it imports.

```python
from bellman.refusal_catalogue import catalogue

print(catalogue())
```

```text
syntax  (graph construction; parse)
  condition  The file is written in the forms the grammar admits, and every !-marked word is one of the vocabulary. It is the first rule a file meets: the refusal is raised where the parser or the lowering stops, and names the forms admitted at that place.
  example  the package's example of the rule, and the refusal it provokes:
  where  cons.bl, line 16, column 40
  what
    [id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊] : !dcsn -> (a : Xa) : !cntn] {
                                           ^
  why    the file writes `]` here, and the language admits `)` or `,` at this place
  write  a side of a block header: a side is parenthesized in general; a single coordinate may stand bare (V : !dcsn -> …)

marginal-role-retired  (graph construction; elaborate)
  condition  The roles `!mrgnvl` and `!sndmrgnvl` are retired from the language: a backward header lists value fields and controls, and a derivative of a value is the term `D_{x}V`.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 91
  what
    [id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c : !ctrl @ ℝ₊₊) : !cntn -> (V : ℝ @ !vlu, dV : ℝ₊₊ @ !mrgnvl) : !dcsn] {
                                                                                              ^
  why    the file writes `!mrgnvl` here, a role word the language has retired: a backward header lists value fields and controls alone, and a derivative of a value is written as the term `D_{x}V`, with `x` a state coordinate of the perch at which the value stands, such as `D_{m}V` or `D_{a}V[>]`
  write  Remove the field from the header, write the line that defined it as a derivative line of the value, such as `D_{m}V = …`, and read the derivative where a line needs it as a term such as `D_{a}V[>]`

stage-name  (graph construction; elaborate)
  condition  The file names itself once: exactly one `@stage` line, with a name.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 1 (address '2')
  what
    @stage: two
    ^
  why    2 '@stage' lines name the stage: 'one' at t.bl:1:1 (term address '1'), 'two' at t.bl:2:1 (term address '2'); a stage file has exactly one, so delete all but the line that names it

declared-once  (graph construction; elaborate)
  condition  Each name, block id, statement id, and law is written once.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 5, column 5 (address 'b.3')
  what
        y = u + z :: [!node]
        ^
  why    the line `y = u + z` is marked `!node` and carries no id; an authored node is named by an id written before the mark
  write  Write an id before the mark, `:: [id=<name>, !node]`

defined-once  (graph construction; elaborate)
  condition  Within one block, an operative equation defines each name-sided left side once, and a derivative line states each derivative term, `D_{m}V`, once. A documentary line (`!doc`) defines and states none.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 4, column 5 (address 'b.second')
  what
        W = 2*V[>] :: [id=second, !node]
        ^
  why    block 'b' already defines W at t.bl:3:5 (term address 'b.first'), and this operative equation defines it again; an operative left side is defined once within a block
  write  Remove one of the two definitions of W, give one of the two results another name, or mark the line that only documents the model `!doc`

one-name-one-meaning  (graph construction; elaborate)
  condition  A name is one of a field, a function, a named space, a shock or a parameter, and is not the name of a numerical operator.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 1 (address 'b')
  what
    [id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {
    ^
  why    'y' is a field, first listed here, and a function, defined at t.bl:2:1 (term address '2'); a name has one meaning in a stage, so give one of the two another name
  write  Give 'y' here or the function 'y' another name

parameter-or-field  (graph construction; elaborate)
  condition  A top-level scalar declaration is a parameter; only a shock is both declared at the top level and listed on the side of a block.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 1 (address '2')
  what
    c : ℝ₊ @ !ctrl
    ^
  why    the top-level declaration of 'c' carries the role word for 'control', but no block header lists 'c': a role belongs to a field, and a field is a name a block reads or writes, while a top-level declaration that no header lists is a parameter, a number calibration binds. List 'c' on a side of the block that uses it, or drop the role word and leave it a parameter

field-perch  (graph construction; elaborate)
  condition  Every listed field has one perch, fixed by its side's perch word, its mark, or its role, and the three must agree.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 1 (address 'b')
  what
    [id=b, (V[>] : ℝ @ !vlu) : !dcsn -> (W : ℝ) : !dcsn] {
    ^
  why    the mark on V[>] places the field at the cntn perch, and the input side of block 'b' is marked `: !dcsn`; a mark agrees with the perch word of its side: list the field without its mark, `V`, and write `V` in place of `V[>]` on the lines of the block
  write  List V without its mark and write `V` in place of `V[>]` on the lines of block 'b'

name-in-scope  (graph construction; elaborate)
  condition  Every name a statement, method entry or definition body mentions is declared where it is used, and every set a typing names, `n_m : Foo`, is a named set the stage defines or a set of the language.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 9 (address 'b.1')
  what
        y = q
            ^
  why    the line mentions q, which the stage does not declare: it is no field of the stage, no line of block 'b' above it defines it, and it is no parameter, shock, named space, or function. Declare it, or write one of the names in scope here: x, y
  write  If you meant the input x, write `y = x`

family-selection  (graph construction; elaborate)
  condition  A selection takes a coordinate of a declared family by a key the family admits.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 5 (address 'b.1')
  what
        y = (a, b)[q]
        ^
  why    the selection (a, b)[q] selects by 'q', which the stage does not declare; a selection from a tuple of 2 coordinates reads a position, such as `(a, b)[1]`, or a name declared on a finite set of 2 members
  write  Select a position, such as `(a, b)[1]`, or select by a name declared on a finite set of 2 members

well-typed  (graph construction; elaborate)
  condition  Every operation of a line, a function body or a declared set reads values of the kinds it takes: arithmetic, an ordered comparison and the bounds of an interval read numbers, and a label is no number; a function is applied to as many arguments as it declares, each of the kind it declares; `Inv` inverts one function; the two sides of a line are of one kind, and its left side names one field for each result of its right side.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 4, column 5 (address 'b.1')
  what
        w = 𝑓 + 1
        ^
  why    `𝑓` is a function, and `𝑓 + 1` reads it as a number; arithmetic, an ordered comparison and the bounds of an interval read numbers. Apply the function to its arguments, `𝑓(…)`

divisor-nonzero  (graph construction; elaborate)
  condition  A divisor the file writes as a number is not zero: a division by a written zero is defined at no point (the definedness conditions of the fold).
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 5 (address 'b.1')
  what
        y = x/0
        ^
  why    `x/0` divides by zero, which is defined at no point; a divisor the file writes as a number is not zero. Write a divisor other than zero

shock-observed  (graph construction; elaborate)
  condition  A statement's perch has observed every shock the statement's right side depends on; otherwise the statement asks for an expectation.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 31, column 5 (address 'dcsn_to_arvl.value')
  what
        V[<] = V                 :: [id=value]
        ^
  why    the line is read at the arvl perch and mentions V, a field at the dcsn perch; the edge from the arvl perch to the dcsn perch draws the shock y, so the value of V is not known at the arvl perch. Write the expectation over it, `E_{y}(…)`
  write  Write the expectation over it, `E_{y}(…)`

shock-reintroduced  (graph construction; elaborate)
  condition  A backward function does not read a shock again beside a term whose expectation has integrated it.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 17, column 5 (address 'cntn_to_dcsn.value')
  what
        V = E_{y,z}(V[>]) + y :: [id=value]
        ^
  why    the line reads the shock y beside a term in which the expectation over y on line cntn_to_dcsn.value has already integrated y, and no other value input of that combination still depends on y; a backward function does not read a shock again after its expectation; move the read of y inside that expectation, or integrate the combination after it
  write  Move the read of y inside the expectation over y, or integrate the combination after it

forward-composite  (graph construction; elaborate)
  condition  The fields a statement's right side mentions are at the left side's perch, before it, or forward of it along the stage's transitions.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 35, column 5 (address 'policy.g_cntn_to_dcsn')
  what
        w[>] = w                        :: [id=g_cntn_to_dcsn]
        ^
  why    the line is read at the cntn perch and mentions w, a field at the dcsn perch, which comes before it: a stage runs arrival, decision, continuation, so a line at the cntn perch is a function of the cntn state, and the file defines the cntn state from the dcsn state, not the dcsn state from the cntn state. Write the cntn-perch field the law of motion defines, or state the equation at the dcsn perch
  write  Write the cntn-perch field the law of motion defines, or state the equation at the dcsn perch

one-builder-per-output  (graph construction; elaborate)
  condition  One block writes a field between two perches: a second block that joins the same perches and writes a field the first writes is refused naming both blocks.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 22, column 1 (address 'egm')
  what
    [id=egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    ^
  why    block 'egm' writes c at the dcsn perch from the cntn perch, which block 'policy' already writes; one builder writes a field between two perches (rule one-builder-per-output). Write the lines of the two blocks in one block, or make block 'egm' write another field
  write  Write the lines of the two blocks in one block, or make block 'egm' write another field

candidate-coordinate  (graph construction; elaborate)
  condition  A candidate line of a policy block, `x[>] = …`, names a control at the candidate points, `c[>]`, a state of the decision perch, the grid line `m[>] = a + c[>]`, or the value candidate an upper envelope of the block compares; any other name is refused with the coordinates in scope.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 19, column 5 (address 'policy.grid')
  what
        w[>] = a + c[>]        :: [id=grid]
        ^
  why    the line writes w[>], a candidate of 'w', which is no control and no state of the dcsn perch, and no upper envelope of block 'policy' compares it; a candidate line of a solution method names a control at the candidate points, a state of the decision perch, which is the grid line, or the value candidate an upper envelope reads (rule candidate-coordinate). The controls are c and the states of the dcsn perch are m
  write  Write, in place of `w[>]`, `m[>]` for the grid line

candidate-read  (graph construction; elaborate)
  condition  A candidate a policy block writes is read by a later line of the block or is the grid line, whose points are the knots of the policy; a candidate nothing reads is refused naming the line.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 18, column 5 (address 'policy.InvEuler')
  what
        c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]
        ^
  why    the line writes the candidate c[>], which no later line of block 'policy' reads; a candidate is read by a later line of the block, as an identification `c = c[>]` reads it, or is the grid line, a state of the decision perch at the candidates, whose points are the knots at which the policy is stored (rule candidate-read). Read the candidate on a later line, or remove the line
  write  Read c[>] on a later line, as `c = c[>]` reads it, or remove the line

transition-without-expectation  (graph construction; elaborate)
  condition  A transition block's statements define the state transition g and contain no expectation: the forward builder is the push-forward of a measure through g, and integration over a shock belongs to a value block (Operators and builders, §"Forward operators").
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 5, column 5 (address 'step.1')
  what
        y = x + E_{z}(z)
        ^
  why    the transition block 'step' integrates over a shock in statement 'step.1'; a forward builder is the push-forward of a measure through the law of motion 𝑔 and takes no expectation; write the integration in a backward block

one-implicit-statement  (graph construction; elaborate)
  condition  A block has at most one implicit statement for each output field.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 7, column 5 (address 'policy.second')
  what
        c + 1 = 2*V[>]     :: [id=second]
        ^
  why    block 'policy' writes a second implicit statement for its output 'c', `c + 1 = 2*V[>]`; the first is `c + 0 = w - V[>]` at t.bl:6:5 (term address 'policy.first'). A block holds at most one implicit statement for each output, since two equations in one unknown state two problems; keep one of the two
  write  Keep one of the two implicit statements for c, `c + 0 = w - V[>]` or `c + 1 = 2*V[>]`

definition-order  (graph construction; elaborate)
  condition  The function definitions have a dependency order, and each applies a defined function.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 1 (address '2')
  what
    𝑓(x : ℝ) := 𝑔(x)
    ^
  why    the definitions form a cycle: 𝑓 (t.bl:2:1 (term address '2')) references 𝑔 (t.bl:3:1 (term address '3')) references 𝑓 (t.bl:2:1 (term address '2')). No dependency order exists, so no definition can be expanded; break the cycle

derivative-one-name  (graph construction; elaborate)
  condition  A derivative names one formal argument, not several arguments at once.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 1 (address '3')
  what
    df := D_{x,y}(f)
    ^
  why    the derivative D_{x, y}(f) names 2 formal arguments (x, y); a derivative names exactly one formal argument
  write  Write one derivative for one formal argument, `D_{x}(f)` or `D_{y}(f)`

derivative-scalar-coordinate  (graph construction; elaborate)
  condition  The one formal argument a derivative names is scalar, not product-valued.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 1 (address '3')
  what
    df := D_{x}(f)
    ^
  why    the derivative D_{x}(f) names the formal argument 'x' of function 'f', which is product-valued; a derivative names one scalar formal argument
  write  Declare 'f' with a scalar formal argument for each coordinate of 'x', reading them in its body in place of those coordinates, and take the derivative in one of them

derivative-coordinate  (graph construction; elaborate)
  condition  A derivative of a value field, `D_{a}V[>]`, names a state coordinate of the perch at which the field is read, and not a discrete one; for the value of a branch, `D_{a_w}V_w[>]`, a state the branch writes.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 7, column 5 (address 'policy.InvEuler')
  what
        c = 𝑑𝑢𝑖𝑛𝑣(D_{q}V[>]) :: [id=InvEuler]
        ^
  why    the derivative D_{q}V[>] names 'q', which is no state coordinate of the cntn perch, at which V[>] is read; a derivative of a value is taken in a state coordinate of the perch at which the value is read, written without its mark, and the coordinates of the cntn perch are a
  write  Name a state coordinate of the cntn perch, `D_{a}V[>]`

stage-boundary  (graph construction; elaborate)
  condition  Every field is produced and consumed: a block writes it or the stage receives it, and a block reads it or the stage delivers it.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 24, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊, z : ℝ) : !dcsn -> (a : ℝ₊) : !cntn] {
    ^
  why    no block writes the field 'z' at the dcsn perch, and the stage does not receive it: the stage receives the continuation values and the arrival state, and a field at the dcsn perch in this position is neither. Write it as the output of a block, or list it where the stage receives it

output-defined  (graph construction; elaborate)
  condition  Every required block output has an equation.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 16, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : Xa) : !cntn] {
    ^
  why    the header of block 'dcsn_to_cntn' lists a on its output side, and no line of the block defines a; write a line that defines it, `a = …`, or, if the block is not meant to write a, remove it from the output side
  write  Write a line that defines a, `a = …`, or, if block 'dcsn_to_cntn' is not meant to write a, remove it from the output side

grid-line-consistency  (graph construction; elaborate)
  condition  A grid line, a line that writes a decision state under the continuation mark (`m_d[>] = a + c[>]`), agrees with the law of motion solved for that state at the candidates: its right side and the law of motion so solved reduce to one expression, every function read as an opaque symbol.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 19, column 5 (address 'policy.grid')
  what
        m[>] = a + 2*c[>]      :: [id=grid]
        ^
  why    the grid line m[>] = a + 2*c[>] disagrees with the law of motion of block 'dcsn_to_cntn': with its line a = m - c solved for m at the candidate c[>], the law of motion gives m[>] = a + c[>], and a + 2*c[>] does not reduce to a + c[>] by algebraic simplification; write the grid line as the law of motion solved for m, m[>] = a + c[>]
  write  Write the grid line as the law of motion solved for m, `m[>] = a + c[>]`

identity-collision  (graph construction; elaborate)
  condition  No authored name collides with the spelling of an identity: a name containing the colon that separates its segments, or a name equal to one of the words a reader tests for in the last segment, `result`, `declared` or `merged`.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 1 (address 'b')
  what
    [id=b, (x : ℝ) : !dcsn -> (result : ℝ) : !dcsn] {
    ^
  why    the field 'result' is one of the reserved words result, declared, merged, by which a reader knows an occurrence's result wire, a declared wire and a merged box from the last segment of an identity; write another name for the field

readable-form  (graph construction; elaborate)
  condition  The item is a form the construction rules read.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 1 (address '2')
  what
    ρ : ℝ := 2
    ^
  why    the declaration of ρ carries the value 2; a stage file declares the set a name lies in, `ρ : ℝ`, and the calibration file supplies its value, `ρ: 2`
  write  Write `ρ : ℝ` here, and `ρ: 2` in the calibration file

component-typed-twice  (graph construction; elaborate)
  condition  A component of an operator's signature, its method, its grid or its handler, is typed by one entry: two entries at one place, an entry for the whole of an Evaluation beside one for an object it stores, or a stage-wide or block-wide operator head beside one of its occurrences, are refused naming both.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 10, column 35 (address 'cntn_to_dcsn.evaluate[V].method')
  what
        | evaluate.method : !Linear | evaluate[V].method : !pchip] {
                                      ^
  why    the method component is typed twice, by `cntn_to_dcsn.evaluate.method : !Linear` at t.bl:10:7 and by `cntn_to_dcsn.evaluate[V].method : !pchip` here, at `cntn_to_dcsn.evaluate` and at `cntn_to_dcsn.evaluate[V]`, which both reach the object `V` stored at the operator `evaluate` of block 'cntn_to_dcsn'; a component is typed by one entry; remove one of the two
  write  Remove one of the two entries, `cntn_to_dcsn.evaluate.method : !Linear` or `cntn_to_dcsn.evaluate[V].method : !pchip`

no-method-for-derivative  (graph construction; elaborate)
  condition  The derivative operator `D` and its occurrences admit no typing: nothing is differentiated by a method, and a definition by `D` is an authored expression or a handler's.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 1 (address '7')
  what
    D.method : !Linear
    ^
  why    the entry `D.method : !Linear` types the method component of the derivative operator `D`, which admits no typing: nothing is differentiated by a method, and a definition by `D` is an authored expression or a handler's; remove the entry
  write  Remove the entry `D.method : !Linear`

method-admission  (graph construction; elaborate)
  condition  A method word stands at a place of a kind its row of the catalogue admits, a representation at an Evaluation, a quadrature at an expectation, a solution method on a builder, and its entry writes every keyword the row requires there, one count per shock for a quadrature's nodes.
  example  the package's example of the rule, and the refusal it provokes:
  where  applications/portfolio-choice/declaration/stages/cons/cons.bl, line 2, column 1 (address 'cntn_to_dcsn.method')
  what
    cntn_to_dcsn.method : !Linear
    ^
  why    the entry `cntn_to_dcsn.method : !Linear` types `cntn_to_dcsn`, a place of the kind builder, with `!Linear`, whose row of the catalogue admits node, statement, definition, operator evaluate; write the word at a place of a kind it admits, or a word that admits this place
  write  Write the entry at `cntn_to_dcsn.evaluate`, `cntn_to_dcsn.evaluate.method : !Linear`, or give `cntn_to_dcsn` a word that admits the kind builder

representation-source  (graph construction; elaborate)
  condition  A function representation's family accepts the data its place supplies, chosen in the order of an authored table, the policy pairs of an `!egm` builder's closing Evaluation, a complete authored expression with an explicit kernel, and the family's own nodes; missing data selects no other case, and an optional grid beside an authored table discretizes the coordinates at which the table is evaluated, written as a name or as a tuple of names in the order of the grid's coordinates, and has exactly its finite support where both are known at configuration.
  example  the package's example of the rule, and the refusal it provokes:
  where  applications/portfolio-choice/declaration/stages/cons/cons.bl, line 2, column 1 (address 'cntn_to_dcsn.evaluate')
  what
    cntn_to_dcsn.evaluate.method : !closed_form
    ^
  why    stage 'cons', place 'cntn_to_dcsn.evaluate': !closed_form reads a complete authored expression with an explicit kernel, and the place supplies none: the closing Evaluation of an !explicit builder, a line that defines one name by an expression, or a declared function supplies one, and a label without its expression does not; its data sources are expression
  write  Type a family that samples the function on its own grid, such as !Linear, at `cntn_to_dcsn.evaluate`, or write the function's expression

explicit-solution  (graph construction; elaborate)
  condition  An `!explicit` builder is a policy or backward value builder to which an addition appends lines in a block of the builder's id, `[id=policy, policy.method : !explicit]`, which stand in place of the declared lines at the operative level; a builder with no such block is refused. The lines write every output by `output = expression` on the states of the builder's own perch, the parameters, the derived parameters and the names the block introduces, with a compiled kernel for each output: a line that reads an input of the builder's header, a value input or its derivative or a control at which a value builder's declared lines are read, states a relation or applies an operator on its right side is refused naming `!egm` or `!time_iteration`, a line that defines or reads a field at another perch, the candidate `c[>]` or the identification `c = c[>]`, naming `!egm`, and a block that writes no output with the line `<output> = <expression>` to write; each refusal stands at the line at fault, and at the typing entry where no line is. A complete block of such lines under `!egm` or `!time_iteration`, appended by an addition or written in the stage file, is refused, naming `!explicit`.
  example  the package's example of the rule, and the refusal it provokes:
  where  methods.bl, line 2, column 13 (address 'policy')
  what
    [id=policy, policy.method : !egm] {
                ^
  why    stage 'perfect_foresight', builder 'policy': the block of the builder under !egm defines every output by an explicit expression of its states and parameters and reads no value input, so it states an explicit solution, on which !egm has nothing to iterate; type !explicit on the builder for such a block, or write the lines !egm solves, which read the continuation value or its derivative
  write  Type `policy.method : !explicit` in place of `policy.method : !egm`

declared-twice  (graph construction; elaborate)
  condition  Over the files of a stage, a component is typed once, whether by an absolute or a relative spelling of its path, a name is defined once, or identically in each file, and a line id names one line of a block; the union of the stage file and its additions refuses a second entry, definition or line naming both positions.
  example  the package's example of the rule, and the refusal it provokes:
  where  m.bl, line 2, column 29 (address 'policy.policy.method')
  what
    [id=policy, method : !egm | policy.method : !vfi] {
                                ^
  why    the component `method` of block 'policy' is written twice with different content: `method : !egm` at m.bl:2:13 (term address 'policy.method') and `policy.method : !vfi` here; a component holds one entry over the files of a stage, so keep one of the two
  write  Keep one of the two entries, `method : !egm` or `policy.method : !vfi`

label-not-in-parent  (graph construction; elaborate)
  condition  A nested block of an addition merges with the branch of the same label under its parent, and a path inside a block names a line or an operator of that block: a label the parent lacks, and a first segment that names another block, are refused.
  example  the package's example of the rule, and the refusal it provokes:
  where  m.bl, line 3, column 5 (address 'dcsn_to_cntn.rent')
  what
        [label=rent, () -> (a_x : ℝ₊) : !cntn] {
        ^
  why    the nested block `label=rent` has no branch of that label in block 'dcsn_to_cntn', whose header stands at t.bl:5:1 (term address 'dcsn_to_cntn'); a nested block of an addition merges with the branch of the same label under its parent, and the union adds no branch
  write  Write the nested block under one of the labels block 'dcsn_to_cntn' holds: work, retire

type-conflict  (graph construction; elaborate)
  condition  The field names determine a signature: a coordinate an addition restates keeps the stage's typing, and a different type on it, or a different perch word on its side, is refused.
  example  the package's example of the rule, and the refusal it provokes:
  where  m.bl, line 2, column 26 (address 'cntn_to_dcsn.out.V')
  what
    [id=cntn_to_dcsn, () -> (V : ℝ @ !vlu) : !dcsn] {
                             ^
  why    the coordinate 'V' on the output side of block 'cntn_to_dcsn' is typed `[-inf, inf) @ !vlu` at t.bl:20:62 (term address 'cntn_to_dcsn.out.V') and `ℝ @ !vlu` here; the field names determine the signature and the stage's typing is kept, so write the coordinate without a type or with the stage's
  write  Write `V` without a type, or with the stage's, `V : [-inf, inf) @ !vlu`

metadata-mismatch  (graph construction; elaborate)
  condition  An addition names the stage it adds to, `@methods: <stage>`, with the name the stage file gives itself, and a metadata line of another key agrees with the stage file's line of that key.
  example  the package's example of the rule, and the refusal it provokes:
  where  m.bl, line 1, column 1 (address '1')
  what
    @methods: port
    ^
  why    the addition names the stage 'port', and the stage file names itself 'cons' at t.bl:1:1 (term address '1'); an addition's first line is `@methods: <stage>` with the name of the stage file it adds to
  write  Write `@methods: cons`

grid-coordinate  (graph construction; elaborate)
  condition  Every factor of a grid names a coordinate of the function the place holds, a control of the builder for a feasible factor or a shock for a quadrature factor; a coordinate no factor names takes the default, the product over the coordinates of that function, as every coordinate does where the place writes no grid entry; a method that reads no grid has none written at its place, and a representation fitted from the pairs the endogenous grid method computes has no grid of its own at the Evaluation of the builder that method solves, since its nodes are the endogenous points of the pairs. A grid constructor stands only at the places its record admits, `!Fibred` only where the occurrence's domain is its base's states followed by its fibre's controls; the base of `!Fibred` is `!Points` or a `!Cartesian` term on the states, and its fibre a `!Cartesian` term of feasible-control factors; each declared point of `!Points` has one coordinate for each coordinate of the place.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 20, column 5 (address 'policy')
  what
        m[>] = a + c[>]        :: [id=grid]
        ^
  why    stage 't', place 'policy': the factor m=(a_min, a_max, n_a) of the grid names 'm', which is no coordinate of the function at policy; the coordinates are a; a factor names one of them, keyed by its name, and a coordinate no factor names takes the default
  write  Write the factor for a, `a=(a_min, a_max, n_a)`

grid-setting-declared  (graph construction; elaborate)
  condition  Every name a factor of a grid writes is a setting the methods file declares, a node set the stage defines or an expectation operator of the stage, and the declared points of `!Points` are a setting the methods file declares or a set the stage defines; a bound or a count written as a number is refused.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 20, column 5 (address 'policy')
  what
        m[>] = a + c[>]        :: [id=grid]
        ^
  why    stage 't', place 'policy': the factor a=(0, a_max, n_a) of the grid writes the number 0; a bound and a count are settings declared in the methods file and valued in the settings file; write the setting's name

grid-bounds  (graph construction; configure)
  condition  At configuration the bounds of a factor are in order and inside the coordinate's declared set, its count is at least two, and a node set is strictly increasing; each configured point of `!Points` has finite real coordinates inside the coordinates' declared sets.
  example  the package's example of the rule, and the refusal it provokes:
  where  address 'cntn_to_dcsn.evaluate'
  why    stage 'cons', place 'cntn_to_dcsn.evaluate', grid !Cartesian(m_d=(m_min, m_max, n_m)): the factor m_d=(m_min, m_max, n_m) has the bounds 10.0 and 1.0, which are not two finite reals in order; configure requires the bounds of a factor in order and inside the coordinate's declared set, its count at least two and a node set strictly increasing; write a lower bound below the upper bound

grid-requirement  (graph construction; elaborate)
  condition  The predicate words a grid writes after `require` are among `!Empty`, `!Cartesian`, `!NonCartesian` and `!UniformCartesian`, and no two contradict each other; each holds of the grid wherever the bound values decide it, an outer requirement of `!Fibred` of the joint grid and one inside its fibre of each fibre. The numerical construction of a grid establishes its finite points, a factor for each coordinate, a sampler for each feasible set and every required property before the grid is used, and reports what it cannot establish instead of supplying a default.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 20, column 5 (address 'policy')
  what
        m[>] = a + c[>]        :: [id=grid]
        ^
  why    stage 't', place 'policy': the grid !Cartesian requires !Uniform, which is no predicate word; a grid may require !Empty, !Cartesian, !NonCartesian and !UniformCartesian, or a tuple of them
  write  Write predicate words among !Empty, !Cartesian, !NonCartesian and !UniformCartesian

setting-outside-set  (graph construction; configure)
  condition  A setting's configured value lies in the set its declaration names.
  example  the package's example of the rule, and the refusal it provokes:
  where  methods.bl, line 3, column 1 (address 'methods.bl:3')
  what
    a_min : ℝ₊           :: ["lower bound of the savings grid"]
    ^
  why    stage 't', setting 'a_min': the value -1.0 lies outside the declared set ℝ₊; a setting's value lies in the set its declaration names; write a value in ℝ₊

setting-unvalued  (graph construction; configure)
  condition  Every setting the methods file declares, and every setting a bound method's keyword arguments or grid name, has a value when settings are bound.
  example  the package's example of the rule, and the refusal it provokes:
  where  methods.bl, line 2, column 1 (address 'methods.bl:2')
  what
    n_a : ℕ              :: ["number of points of the savings grid"]
    ^
  why    stage 't', setting 'n_a': the settings source supplies no value for it; every setting the methods file declares is valued when settings are bound; write `n_a: <value>` in the settings source

multiplier-declaration  (graph construction; elaborate)
  condition  A multiplier is declared inside the block whose continuation grid it extends, once, marked `[>]`, with one declared set and one bound after ⟂ that names continuation states, multipliers of the block, parameters, numbers or `inf`.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 18, column 5 (address 'policy.slackness')
  what
        μ[>]   : ℝ₊ ⟂ c >= 0             :: [id=slackness]
        ^
  why    the bound of the multiplier 'μ' names 'c', written c, a control; the bound of a declared multiplier names continuation states, multipliers of block 'policy', parameters, numbers or `inf`. Write the bound on a continuation state, or state the condition on a line of the block with its own clause
  write  Write the bound of 'μ' on a continuation state, or state the condition on a line of block 'policy' with its own clause

set-mismatch  (graph construction; elaborate)
  condition  A field produced on one declared set and consumed on another is declared with sets whose inclusion holds; otherwise the stage declares the inclusion through the control's feasible set.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 2, column 1 (address 'a')
  what
    [id=a, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] { y = x }
    ^
  why    the field y is produced by 'a' on ℝ and consumed by 'b' on ℝ₊₊, and ℝ does not lie in ℝ₊₊; declare the field with one set in both blocks, or state the control's feasible set in the maximization line
  write  Declare y with one set in blocks 'a' and 'b', or state the control's feasible set in the maximization line

category-codes  (graph construction; elaborate)
  condition  A set marked `!categories` is a nonempty range of integers written as a comprehension over ℤ or ℕ, whose annotation gives each member one category name and each name one member. The marker is written only on a top-level named set, and a field declared on a set with category codes names that set at every site that names a set.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 1 (address 't.bl:3')
  what
    HouseholdStatus := {i : ℤ | i >= 0, i <= 1} :: [!categories household_status, newborn=0, old=2]
    ^
  why    the set HouseholdStatus is marked `!categories`, and its definition and its annotation give no category map. The entry `old=2` gives a code outside HouseholdStatus, the integers from 0 to 1; give each category a code from 0 to 1. The set HouseholdStatus holds the integers from 0 to 1, and the member 1 has no category; give each member one category

value-input-role  (graph construction; elaborate)
  condition  A statement of a backward block reads values or marginal values, not both: its kernel acts on one role and its output has that role.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 6, column 5 (address 'cntn_to_dcsn.value')
  what
        V = 3   :: [id=value]
        ^
  why    the line cntn_to_dcsn.value reads no value input, and the header of block 'cntn_to_dcsn' lists none; a line of a backward block acts on a value or a marginal value that its header lists; list a value input in the header and read it on the line
  write  List a value input in the header of block 'cntn_to_dcsn' and read it on line cntn_to_dcsn.value

signature-complete  (graph construction; elaborate)
  condition  A forward block's header lists every field its lines read that no earlier line of the block defines. A backward block's header lists the value fields its lines read and the controls at which they are read, but no state; a state of its output perch is a coordinate. A value field a backward header lists and no line of the block reads is admitted: it is left out of the block's builder and recorded as a diagnostic, `unread-input`, in place of a refusal.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 6, column 5 (address 'd.1')
  what
        w = x + y
        ^
  why    the line reads x, which the header of block 'd' does not list and no earlier line of the block defines; a forward block's header lists every field its lines read. List it in the header, `(y, x) : !dcsn -> (w : ℝ) : !dcsn`, or define it on an earlier line of the block. The corrected header writes a perch word on each field of a side where the side's one word no longer holds for every field; a control is at the decision perch under either spelling
  write  List x in the header, `(y, x) : !dcsn -> (w : ℝ) : !dcsn`

header-coordinate  (graph construction; elaborate)
  condition  A backward block's header lists the value fields it reads and writes and the controls at which its lines are read, and no state: a state of the perch at which its output stands is a coordinate of the output function, and a state of its input perch is reached through the law of motion.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 5, column 1 (address 'cntn_to_dcsn')
  what
    [id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, x_d : !dcsn) -> (V : ℝ @ !vlu) : !dcsn] {
    ^
  why    the header of block 'cntn_to_dcsn' lists x_d on its input side, and the block is a backward block, whose header lists the value fields it reads and writes and the controls at which its lines are read, and no state (rule header-coordinate). x_d is a state of the dcsn perch, the perch at which the block's output stands, so it is a coordinate of the output function and no input of the block. Remove the listing, `(V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu) : !dcsn`; a line of the block may still mention a state of the dcsn perch, which is a coordinate of what it defines
  write  Remove x_d from the header: `(V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu) : !dcsn`

input-perch-state  (graph construction; elaborate)
  condition  A backward line reads a state of its input or a later perch only through the law of motion. A direct read is refused, including in a relation or a condition after `⟂`. A read under the expectation over the edge's shock and continuation-state indexing on a policy candidate line are admitted.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 9, column 5 (address 'cntn_to_dcsn.1')
  what
        V = a + V[>]
        ^
  why    the line is read at the dcsn perch and mentions a, a state of the cntn perch, the perch block 'cntn_to_dcsn' reads its inputs at; a backward block reaches a state of its input perch, or of a later perch, through the law of motion alone, and read directly the state would stand free in a rule that holds on the dcsn state (rule input-perch-state). The forward block 'dcsn_to_cntn' defines it at t.bl:6:5 (term address 'dcsn_to_cntn.1'), `a = x_d`. Write `x_d` in its place, as the law of motion holds with no shock drawn on the edge of block 'dcsn_to_cntn'; across an edge that draws a shock, the state is read under the expectation over that shock
  write  Write `x_d` in place of `a`

kernel-form  (graph construction; query)
  condition  A kernel that `compile_kernel` writes as a Python function is retained arithmetic and calls to closed-form functions; a symbolic derivative has no compile rule. The function takes the values of the parameters it reads as arguments, so a symbolic version compiles too and answers no values, `parameter_values` None.
  example  the package's example of the rule, and the refusal it provokes:
  where  address 'cntn_to_dcsn.marginal'
  why    stage 'cons_savings_iid': the kernel of 'marginal:Derivative:1' (cons_savings_iid:G:cntn_to_dcsn) contains the call 𝑑𝑢(c) of 𝑑𝑢 := D_{c}(𝑢) (cons_savings_iid:function:𝑑𝑢), which is not a closed-form function; no compile rule evaluates it: compile evaluates retained arithmetic and calls to closed-form named functions and selects no numerical method (AMD-SG-007 §3.1, rule kernel-form); define that function in closed form, or read the kernel with kernel(stage, box)

method-option-value  (graph construction; configure)
  condition  Every configured keyword argument of a method lies in the domain its row of the catalogue names for it.
  example  the package's example of the rule, and the refusal it provokes:
  where  address 'cntn_to_dcsn'
  why    stage 'cons', place 'cntn_to_dcsn', method !vfi, keyword 'tol': -1.0 is not a positive real; configure requires the value to lie in the domain the method's row names; write a finite value greater than zero

kernel-target  (graph construction; query)
  condition  `kernel` and `compile` read a primitive operator box, and `compile` one whose kernel is g or G.
  example  the package's example of the rule, and the refusal it provokes:
  where  address 'cntn_to_dcsn'
  why    stage 'cons': compile evaluates the explicit numerical kernels g and G, and 'cntn_to_dcsn:Evaluation' is a Evaluation box whose kernel, identity at m_d; no policy is inserted, has no callable representation (AMD-SG-007 §3.1, rule kernel-target); inspect it with kernel(stage, box), or compile a pullback, push-forward or aggregation box

distribution-dependency  (graph construction; elaborate)
  condition  The distribution declarations read one another without a cycle, and a declaration does not read its own subject.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 4, column 1 (address '4')
  what
    y ~ N(z, 1)
    ^
  why    the distribution declarations form a cycle: `y ~ N(z, 1)` reads z, `z ~ N(y, 1)` reads y; the joint distribution of an edge is the product of the declared conditional distributions in a dependency order, which a cycle does not have; remove one of the shock arguments, or declare the dependent shocks jointly, such as `(y, z) ~ N(…)`
  write  Remove one of the shock arguments, or declare y, z jointly, such as `(y, z) ~ N(…)`

distribution-edge  (graph construction; elaborate)
  condition  The shocks of connected declarations are drawn on the edge of one forward builder.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 1 (address '3')
  what
    y ~ N(0, 1)
    ^
  why    the shock y is listed on the headers of the forward blocks 'arvl_to_dcsn' and 'dcsn_to_cntn'; a shock is drawn on one edge, the edge of the one forward block whose header lists it; remove y from the header and from the lines of one of the two blocks, which changes the law of motion of that block
  write  Remove y from the header and from the lines of block 'arvl_to_dcsn' or of block 'dcsn_to_cntn', which changes the law of motion of that block

distribution-domain  (graph construction; elaborate)
  condition  A declaration's family parameters lie in the family's domain: matched dimensions, a symmetric positive semidefinite covariance, nonnegative variances and deviations, finite endpoints in order, positive scales, and real arguments that have a number.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 4, column 1 (address 't.bl:4')
  what
    (y, z) ~ N((0, 0), ((1, 2), (2, 1)))
    ^
  why    the covariance ((1, 2), (2, 1)) of the normal declaration `(y, z) ~ N((0, 0), ((1, 2), (2, 1)))` is not positive semidefinite: its smallest eigenvalue is -1.0; write a symmetric positive semidefinite covariance matrix
  write  Write a symmetric positive semidefinite covariance matrix

derived-parameter  (graph construction; elaborate)
  condition  A derived parameter's definition, `h := 1/(1 - Γ/R)`, reads declared parameters, finite numbers and other derived parameters, and is formed by signs, sums, differences, products, quotients, powers and the calls `log` and `exp` of one argument; the calibration supplies no value for it, and at the calibration values every operation of its definition is defined and its value is a finite real number.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 3, column 1 (address '3')
  what
    h := 1/sqrt(1 - β)
    ^
  why    the derived parameter h, defined as `1/sqrt(1 - β)`, calls sqrt, `sqrt(1 - β)`, which is neither log nor exp; a derived parameter's definition reads declared parameters, finite numbers and other derived parameters, and is formed by signs, sums, differences, products, quotients, powers and the calls `log` and `exp`, each of one argument
  write  Write the definition of h from declared parameters, finite numbers and derived parameters, with signs, sums, differences, products, quotients, powers, log and exp

conditional-not-declared  (graph construction; elaborate)
  condition  The conditional distribution an expectation needs is a declared conditional, a product of them, or a marginal or conditional of a joint normal declaration whose conditioning block is positive definite.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 17, column 5 (address 'cntn_to_dcsn.value')
  what
        V = E_{z}(E_{y}(V[>])) :: [id=value]
        ^
  why    the expectation over y on line cntn_to_dcsn.value needs the distribution of y given z from the normal declaration `(y, z) ~ N((0, 0), ((1, 0), (0, 0)))`, whose covariance block of z, which is 0, is singular (smallest eigenvalue 0.0); the conditional of a joint normal declaration requires a positive definite block for the shocks conditioned on, and no pseudoinverse is taken; condition on shocks whose covariance block is positive definite, or integrate them jointly, `E_{y, z}(…)`
  write  Condition on shocks whose covariance block is positive definite, or integrate y, z jointly, `E_{y, z}(…)`

branch-form  (graph construction; elaborate)
  condition  A branching block holds one labeled nested block per label and nothing else, at least two, in the forward block from the decision perch to the continuation perch, whose own output side is empty; a nested block has an empty input side and writes continuation fields.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 5, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    ^
  why    block 'dcsn_to_cntn' holds one nested block, `work`; a branching block holds one nested block for each label of its label coordinate 'd', {work, retire}; write the nested block of `retire`
  write  Write the nested block `[label=retire, …] { … }` after the branch `work`

branch-labels  (graph construction; elaborate)
  condition  The nested blocks carry the labels of the block's label coordinate, a control or a shock with its law, whose set is a finite set of at least two labels, each once and in the set's order.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 9, column 5 (address 'dcsn_to_cntn.stop')
  what
        [label=stop, () -> (a_r : ℝ₊) : !cntn] {
        ^
  why    the label 'stop' is not a member of {work, retire}, the set of the label coordinate 'd'; write one nested block for each member, in the set's order

branch-tuple-mismatch  (graph construction; elaborate)
  condition  The value line selects by one tuple indexed by the label coordinate, one entry per label, and the policy maximizes over the same tuple in the same order; a branch a shock selects is read under the expectation over the shock alone.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 14, column 5 (address 'cntn_to_dcsn.choice_value')
  what
        V = (V_w[>], V_r[>])[d]                :: [id=choice_value]
        ^
  why    the value line selects from (V_w[>], V_r[>]) by 'd', and the policy line policy.choice maximizes over (V_r[>], V_w[>]); write the policy's maximand as the value line's tuple, in its order

branch-value-position  (graph construction; elaborate)
  condition  A continuation value stands at one position of the selection tuples, the position of the branch on whose fields it is a function.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 14, column 5 (address 'cntn_to_dcsn.choice_value')
  what
        V = (V_w[>], V_w[>])[d]                :: [id=choice_value]
        ^
  why    V_w[>] is read at the position of 'work' and at the position of 'retire'; a branch value stands at one position in every tuple, the position of its branch; write each branch value at its own branch's position alone

branch-law  (graph construction; elaborate)
  condition  The law of a label shock gives one probability to each label in the order of the labels, `Categorical((p₁, …, pₙ))` or `Bernoulli(p)` over two.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 7, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (a_d, s) : !dcsn -> ()] {
    ^
  why    the shock 's' selects the branches of block 'dcsn_to_cntn' and has no distribution; the branches are weighted by the distribution of the shock, so write `s ~ Categorical((p_young, p_old))`, one probability for each label in the order {young, old}

not-constructed  (graph construction; elaborate)
  condition  The item is a form of the language the construction does not read.
  example  the package's example of the rule, and the refusal it provokes:
  where  t.bl, line 5, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (a_d, c : !ctrl @ [0,1], d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    ^
  why    block 'dcsn_to_cntn' lists the controls 'c', 'd' beside its branches; the construction reads a branching block whose branches state equations alone and whose label coordinate is its one control, or a shock over a finite set in a stage that chooses nothing, and reads no other form of a branching block; the declarations and the other blocks of the stage are read, and no builder of the stage is drawn while this block keeps this form

target-not-found  (the names of the pieces; query)
  condition  A name given to a query of the stage object, a box name or an identity, names a piece the version asked holds.
  example  the package's example of the rule, and the refusal it provokes:
  where  stage 'cons', target 'cntn_to_dcsn:Substitution:V'
  why    stage 'cons': 'cntn_to_dcsn:Substitution:V' names no box of the version's views and no record of its definitions table; a printed view, a kernel and a compiled kernel read an actual box or definition
  write  Write a box name that stage.builder.bwd.primitives.list() or stage.builder.fwd.primitives.list() shows, or an identity of stage.definitions

target-ambiguous  (the names of the pieces; query)
  condition  A name given to a query reaches one piece of the version, not two.
  example  the package's example of the rule, and the refusal it provokes:
  where  stage 'cons', target 'cntn_to_dcsn'
  why    stage 'cons': 'cntn_to_dcsn' names 2 different targets: the box cntn_to_dcsn in the initial diagram, backward at the grain builder, builder cntn_to_dcsn | the box cntn_to_dcsn in the builders graph, backward at the grain builder, builder cntn_to_dcsn; one name selects one target only when the boxes it names are equal
  write  Pass the box itself from the view and grain you mean

target-version  (the names of the pieces; query)
  condition  An object given to a query belongs to the version asked: a box or a record of one version is not read against another version, since versions share no object.
  example  the package's example of the rule, and the refusal it provokes:
  where  stage 'cons', target 'cntn_to_dcsn:Pullback'
  why    stage 'cons': the box 'cntn_to_dcsn:Pullback' passed is no box of a graph of this version; a query reads the boxes of the version it is asked of, and versions share no object
  write  Ask the version whose view holds the box, or pass a box of this version's view

recipe-shape  (the Bellman factory; read)
  condition  The recipe names its trellis file under `trellis:` and has a `stages` mapping; each stage key stands once and its entry names its stage file under `stage:`, each file by its path from the recipe's folder; each kind block is a mapping with an `all` list; a range key is written `lo-hi` with lo ≤ hi and no two ranges of one list overlap; `periods:` is a pair.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/spec.yml, address 'stages'
  what
{'registry': {}}
  why    the recipe has no top-level `stages` mapping
  write  stages: {<stage key>: {stage: <path>.bl, calibration: {all: [...]}, settings: {all: [...]}, methods: {all: [stages/<key>/methods.bl]}}}

recipe-source  (the Bellman factory; read)
  condition  Every source name is relative to the registry without `..`, names a file the registry holds, of the kind of the list it stands in, and its `parent:` chain neither cycles nor exceeds ten files.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/spec.yml, address 'stages.two_nodes.calibration.all'
  what
calibration/absent
  why    the registry holds no source file 'calibration/absent'; tried registry/calibration/absent.yml, registry/calibration/absent.yaml, registry/calibration/absent
  write  the name of a file under the registry, without its extension

recipe-slot-unknown  (the Bellman factory; read)
  condition  Every fill names a slot the recipe declares by a `$` name in one of its source lists.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/spec.yml, address 'fil'
  what
fil
  why    the keyword 'fil' names no slot of the recipe; its slots are $fill
  write  one of $fill, or a new `$` name in a source list of the recipe

recipe-template-agreement  (the Bellman factory; read)
  condition  Every stage the recipe names occupies a period the trellis file holds, and every stage a period holds is named by the recipe.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/spec.yml, address 'other'
  what
other
  why    the recipe names the stage 'other', which no period of registry/trellis.yml holds
  write  'other' in a period template of registry/trellis.yml, or no entry for it in the recipe

slot-value-not-a-mapping  (the Bellman factory; read)
  condition  A slot is bound to a mapping.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/spec.yml, address 'fill'
  what
'β: 0.9'
  why    slot 'fill' is given the text 'β: 0.9', which is no mapping of names to values
  write  fill={'calibration': {...}, 'settings': {...}} or a flat mapping of names to values

fill-names-nothing  (the Bellman factory; read)
  condition  Every key of a fill names a parameter or a setting a receiving stage declares, or a name the `registry` block admits.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/spec.yml, address 'fill'
  what
beta
  why    slot 'fill', key 'beta': no stage that receives this slot declares 'beta' as a parameter (two_nodes declares β, R) or as a setting (two_nodes declares n_k), and no registry block admits it; a fill key names a parameter or a setting of a stage that receives it
  write  one of the declared names R, n_k, β

fill-mixes-kinds  (the Bellman factory; read)
  condition  A flat fill names parameters or settings, not both.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/spec.yml, address 'fill'
  what
β, n_k
  why    slot 'fill' names the parameters β and the settings n_k in one flat mapping
  write  fill={'calibration': {...}, 'settings': {...}}, each name under its kind

trellis-file-shape  (the Bellman factory; read)
  condition  A trellis file, or a trellis dictionary, lists its `periods` and its `inter_connectors`; each period holds `stages` and `connectors`; each record of a file names its `stage`.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/broken.yml, address 'periods'
  what
{'stages': []}
  why    the trellis file has no list `periods`
  write  periods: [{template: period.yml, repeat: 51}] or the periods written out

record-shape  (the Bellman factory; elaborate)
  condition  A record holds `stage` as `{text, origin}` and its three mappings, and a supplied digest or origin agrees with the source.
  example  the package's example of the rule, and the refusal it provokes:
  where  address 'record'
  what
stage
  why    the record holds no calibration, methods or settings fields
  write  a record with stage, calibration, settings and methods, and optionally label and provenance

period-join-cycle  (the Bellman factory; connect)
  condition  The pairs of a period, authored by its connectors or inferred from equal field names, close no cycle, and no connector joins a stage to itself.
  example  the package's example of the rule, and the refusal it provokes:
  where  address 'periods[0]'
  what
disc continues to 'a' and port arrives at 'k'; port continues to 'm_next' and disc arrives at 'a'
  why    the joins of the period form a cycle: disc continues to 'a' and port arrives at 'k'; port continues to 'm_next' and disc arrives at 'a'; the stages of a period are ordered by their field dependencies, so no stage may take a field it produces through the others
  write  connectors with no cycle among the stages; remove or redirect an authored connector, and qualify an endpoint with its stage key where its bare name is ambiguous

connector-names-no-field  (the Bellman factory; connect)
  condition  A connector is a mapping, flat or in the keyed form {from, to, fields} within a period, and one entry maps a continuation field; a connector whose endpoint names no field, or several, is a diagnostic of the trellis's selection of its connections and no refusal.
  example  the package's example of the rule, and the refusal it provokes:
  where  address 'periods[0].connectors[0]'
  what
{'from': 'cons', 'to': 'port', 'fields': {'a': 'k'}, 'label': 'x'}
  why    the connector is written in the keyed form and has the key 'label' beside from, to and fields
  write  {<continuation field>: <arrival field>}, or within a period {from: <stage key>, to: <stage key>, fields: {<continuation field>: <arrival field>}}

period-parameter-agreement  (the Bellman factory; connect)
  condition  A parameter name two or more stages of one period declare names one parameter of the period: the sets the stages declare it with have one nonempty intersection the package reads, the stages' sources supply it one value, and that value lies in every declared set; a setting name two or more stages declare in their methods files names one setting of the period in the same way.
  example  the package's example of the rule, and the refusal it provokes:
  where  registry/trellis.yml, address 'periods[0]'
  what
R : ℝ₊₊ in two_nodes; R : (-inf, 0) in other
  why    the stages two_nodes (registry/stages/two_nodes/two_nodes.bl) and other (registry/stages/other/other.bl) of the period declare the parameter 'R' with the sets ℝ₊₊ and (-inf, 0), which have no nonempty intersection; a parameter name names one parameter of the period, shared by the stages that declare it, so their declared sets agree
  write  one set for 'R' in every stage of the period, or sets the package reads whose intersection is not empty, or distinct names for distinct parameters

readable-file  (the Bellman factory; read)
  condition  A stage file, read by its path or named under `stage:` in a recipe, is a readable `.bl` file of UTF-8 text; a source file a binding verb reads, or a record of a trellis file names, is a readable YAML mapping that writes each key once.
  example  the package's example of the rule, and the refusal it provokes:
  where  cons.txt
  what
cons.txt
  why    cons.txt names no stage file, since a stage file is a `.bl` file
  write  the path of a stage file, `<name>.bl`
```

The example of `recipe-shape` above is a recipe with no `stages` mapping. A recipe names every file it reads by its path from its own folder, the trellis file under `trellis:` and each stage's file under `stage:` in the stage's entry, and nothing is read in place of a path it does not write. The same rule therefore refuses the example [registry](../../wiki/spec_factory.md)'s recipe without its `trellis:` line, and without the `stage:` line of its one entry, although `trellis.yml` and `stages/two_nodes/two_nodes.bl` stand in the registry:

```python
from bellman.refusal_examples import EXAMPLES
from bellman.refusal_catalogue import refusal_of

for name in ("recipe-names-no-trellis-file", "entry-names-no-stage-file"):
    print(refusal_of(EXAMPLES[name]))
```

```text
registry/spec.yml: address 'trellis': the recipe names no trellis file; write `trellis: trellis.yml`, the path from this folder (rule recipe-shape)
registry/spec.yml:3:3: address 'stages.two_nodes': the entry `stages.two_nodes` names no stage file; write `stage: stages/two_nodes/two_nodes.bl`, the path from this folder (rule recipe-shape)
```
