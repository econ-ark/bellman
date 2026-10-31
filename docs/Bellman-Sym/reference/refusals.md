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
> A stage file the package cannot read is refused, and so is a method target that names no place of a stage and a compilation the stage does not support. Every refusal says four things: where it is, what stands there, why it cannot be read, and what to write instead. This page lists every rule the package refuses under, each with the smallest example that breaks it and the refusal that example provokes. Every listing below is printed from the package, so what you read here is what your own session prints.

> [!info]- Relationship with other documents
> **Builds on** — [Stage tutorial](../01-stage.md): the file whose rules these are, written line by line.
> **Used by** — [The stage](../API/stage/01-the-stage.md): the object a file becomes once it passes them.

A refusal of the file is raised when the file is read: elaboration returns a stage or refuses the file. A refusal is held rather than raised only where the construction builds no graph for a form the file writes: the stage then holds a refusal under `not-constructed` in place of that graph, as it does for the forward builders graph where a shock's distribution names a family outside the table of [Shock distributions](laws.md). A method target is refused when `methodize` binds it, a setting's value when `configure` reads it, and a compilation when `compile_kernel()` is asked for it. Each refusal carries the rule it names as a field, so an editor or a script reads the rule rather than the sentence.

## 1 The four parts

Take the consumption stage and write `]` where a side of a block's header closes with `)`. The parser stops at that character, and the refusal reads:

```python
from bellman.refusal_examples import EXAMPLES
from bellman.refusal_catalogue import refusal_of

print(refusal_of(EXAMPLES["syntax"]))
```

```text
cons.bl:17:40: the file writes `]` here, and the language admits `)` or `,` at this place
    [id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊] : !dcsn -> (a : Xa) : !cntn] {
                                           ^
a side of a block header: a side is parenthesized in general; a single coordinate may stand bare (V : !dcsn -> …) (rule syntax)
```

**Where** is the file, the line and the column, which leads every refusal, as an editor and a compiler both print it. **What** is the line of the file with a mark under the column. **Why** is what the file writes there and the forms the language admits at that place, in the spellings you write them in. **What to write** is the sentence the grammar keeps for that place, given where the position falls — here inside the side of a block header.

A word the vocabulary does not hold is refused in the same four parts, at the word itself:

```python
from bellman.refusal_examples import Example
from bellman.refusal_catalogue import refusal_of

print(refusal_of(Example(
    rule="syntax", address=None, words=(),
    text="@stage: t\n[id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n")))
```

```text
t.bl:2:18: the file writes `!contrl` here, which is no word-type of the language
    [id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {
                     ^
the word-types are !arvl, !cntn, !ctrl, !dcsn, !shck, !state, !vlu (rule syntax)
```

## 2 The three vocabularies of rules

The package refuses under three closed vocabularies. The rules of **graph construction** are claims about the authored file: that it names itself once, that every name it writes is declared where it is used, that a forward block's header lists every field its lines read and a backward block's the value fields its lines read, with the controls at which they are read. The rules of the **identity table** are the rules by which the string written after `on:` in a methods file is read: which places a target may name and how each is spelled. The rules of the **Bellman factory** are claims about a model's files and the dictionaries made from them: the recipe, its source files and its fills, the trellis file, the records, the joins of a period, and a file given by its path to `load_stage` or to a binding verb, which is read as one YAML mapping with each key written once; each refusal names the file or the address, what stands there, why it is refused and what to write.

A rule is written once, in the package, and a refusal names it. The three vocabularies are:

```python
from bellman.refusals import FACTORY_RULES, RULES, TARGET_RULES

for vocabulary, rules in (("graph construction", RULES), ("the identity table", TARGET_RULES),
                          ("the Bellman factory", FACTORY_RULES)):
    print(vocabulary)
    print("\n".join("  " + rule for rule in rules))
```

```text
graph construction
  syntax
  stage-name
  declared-once
  defined-once
  one-name-one-meaning
  parameter-or-field
  field-perch
  name-in-scope
  family-selection
  well-typed
  divisor-nonzero
  shock-observed
  shock-reintroduced
  forward-composite
  transition-without-expectation
  one-implicit-statement
  definition-order
  derivative-one-name
  derivative-scalar-coordinate
  stage-boundary
  output-defined
  grid-line-consistency
  identity-collision
  readable-form
  multiplier-declaration
  set-mismatch
  category-codes
  value-input-role
  marginal-role-retired
  derivative-coordinate
  signature-complete
  header-coordinate
  input-perch-state
  kernel-form
  method-option-value
  kernel-target
  distribution-dependency
  distribution-edge
  distribution-domain
  conditional-not-declared
  branch-form
  branch-labels
  branch-tuple-mismatch
  branch-value-position
  branch-law
  not-constructed
  block-header-mismatch
  block-name-undefined
the identity table
  (a) a builder box by its block id; `<block-id>_builder` for a transition block
  (b), (c) a node box or a line by `<block-id>.<statement-id>`
  (ii) a positional address `<block-id>.<n>` is not a target; the line needs an id
  (d) every occurrence of an operator by its stage-wide name
  (e) one occurrence by `<block-id>.<statement-id>.<operator>`
  (g) `evaluate`: the one authored occurrence, else the boundary representation; two or more authored occurrences are named by their addresses
  (h) one target per entry; a comma-separated entry is split by L02
  a target has one, two, or three dot-separated parts
  a target reaches one place; two is a construction defect
  target-not-found
  target-ambiguous
  target-version
  method-attachment
the Bellman factory
  recipe-shape
  recipe-source
  recipe-slot-unknown
  recipe-template-agreement
  slot-value-not-a-mapping
  fill-names-nothing
  fill-mixes-kinds
  trellis-file-shape
  record-shape
  period-join-cycle
  connector-names-no-field
  period-parameter-agreement
  readable-file
```

The table gives each rule of graph construction: **written**, the rule's name as a refusal closes with it, `(rule X)`, or `; rule X)` after the address the refusal names; **claim**, what the rule requires of a stage file, in the words of the package; **denotes**, a dash, since a rule is a claim about the file and not an object of the Bellman calculus; and **read from**, the module under `packages/bellman/bellman/`, its table and the key.

<!-- reference-table -->

| rule | written | claim | denotes | read from |
|---|---|---|---|---|
| <a id="syntax"></a>`syntax` | `(rule syntax)` | The file is written in the forms the grammar admits, and every !-marked word is one of the vocabulary. It is the first rule a file meets: the refusal is raised where the parser or the lowering stops, and names the forms admitted at that place. | — | `refusals.py`, `RULES`, `"syntax"` |
| <a id="stage-name"></a>`stage-name` | `(rule stage-name)` | The file names itself once: exactly one `@stage` line, with a name. | — | `refusals.py`, `RULES`, `"stage-name"` |
| <a id="declared-once"></a>`declared-once` | `(rule declared-once)` | Each name, block id, statement id, and law is written once. | — | `refusals.py`, `RULES`, `"declared-once"` |
| <a id="defined-once"></a>`defined-once` | `(rule defined-once)` | Within one block, an operative equation defines each name-sided left side once. A documentary line (`!doc`) defines none. | — | `refusals.py`, `RULES`, `"defined-once"` |
| <a id="one-name-one-meaning"></a>`one-name-one-meaning` | `(rule one-name-one-meaning)` | A name is a field, a function, a named space, a shock, or a parameter — one of them — and is not the name of a numerical operator. | — | `refusals.py`, `RULES`, `"one-name-one-meaning"` |
| <a id="parameter-or-field"></a>`parameter-or-field` | `(rule parameter-or-field)` | A top-level scalar declaration is a parameter; only a shock is both declared at the top level and listed on the side of a block. | — | `refusals.py`, `RULES`, `"parameter-or-field"` |
| <a id="field-perch"></a>`field-perch` | `(rule field-perch)` | Every listed field has one perch, fixed by its side's perch word, its mark, or its role, and the three must agree. | — | `refusals.py`, `RULES`, `"field-perch"` |
| <a id="name-in-scope"></a>`name-in-scope` | `(rule name-in-scope)` | Every name a statement or a definition body mentions is declared where the statement stands. | — | `refusals.py`, `RULES`, `"name-in-scope"` |
| <a id="family-selection"></a>`family-selection` | `(rule family-selection)` | A selection takes a coordinate of a declared family by a key the family admits: a label of its finite set, a position counted from one on a fixed product, or a name declared within the finite integer or label index set of a collection declared on a set of functions. | — | `refusals.py`, `RULES`, `"family-selection"` |
| <a id="well-typed"></a>`well-typed` | `(rule well-typed)` | Every operation of a line, a function body or a declared set reads values of the kinds it takes: arithmetic, an ordered comparison and the bounds of an interval read numbers, and a label is no number; a function is applied to as many arguments as it declares, each of the kind it declares; `Inv` inverts one function; the two sides of a line are of one kind, and its left side names one field for each result of its right side. | — | `refusals.py`, `RULES`, `"well-typed"` |
| <a id="divisor-nonzero"></a>`divisor-nonzero` | `(rule divisor-nonzero)` | A divisor the file writes as a number is not zero: a division by a written zero is defined at no point (the definedness conditions of the fold). | — | `refusals.py`, `RULES`, `"divisor-nonzero"` |
| <a id="shock-observed"></a>`shock-observed` | `(rule shock-observed)` | A statement's perch has observed every shock the statement's right side depends on; otherwise the statement asks for an expectation. | — | `refusals.py`, `RULES`, `"shock-observed"` |
| <a id="shock-reintroduced"></a>`shock-reintroduced` | `(rule shock-reintroduced)` | A backward function does not read a shock again beside a term whose expectation has integrated it. | — | `refusals.py`, `RULES`, `"shock-reintroduced"` |
| <a id="forward-composite"></a>`forward-composite` | `(rule forward-composite)` | The fields a statement's right side mentions are at the left side's perch, before it, or forward of it along the stage's transitions. | — | `refusals.py`, `RULES`, `"forward-composite"` |
| <a id="transition-without-expectation"></a>`transition-without-expectation` | `(rule transition-without-expectation)` | A transition block's statements define the state transition g and contain no expectation: the forward builder is the push-forward of a measure through g, and integration over a shock belongs to a value block (Operators and builders, §"Forward operators"). | — | `refusals.py`, `RULES`, `"transition-without-expectation"` |
| <a id="one-implicit-statement"></a>`one-implicit-statement` | `(rule one-implicit-statement)` | A block has at most one implicit statement for each output field. | — | `refusals.py`, `RULES`, `"one-implicit-statement"` |
| <a id="definition-order"></a>`definition-order` | `(rule definition-order)` | The function definitions have a dependency order, and each applies a defined function. | — | `refusals.py`, `RULES`, `"definition-order"` |
| <a id="derivative-one-name"></a>`derivative-one-name` | `(rule derivative-one-name)` | A derivative names one formal argument, not several arguments at once. | — | `refusals.py`, `RULES`, `"derivative-one-name"` |
| <a id="derivative-scalar-coordinate"></a>`derivative-scalar-coordinate` | `(rule derivative-scalar-coordinate)` | The one formal argument a derivative names is scalar, not product-valued. | — | `refusals.py`, `RULES`, `"derivative-scalar-coordinate"` |
| <a id="stage-boundary"></a>`stage-boundary` | `(rule stage-boundary)` | Every field is produced and consumed: a block writes it or the stage receives it, and a block reads it or the stage delivers it. | — | `refusals.py`, `RULES`, `"stage-boundary"` |
| <a id="output-defined"></a>`output-defined` | `(rule output-defined)` | Every required block output has an equation. | — | `refusals.py`, `RULES`, `"output-defined"` |
| <a id="grid-line-consistency"></a>`grid-line-consistency` | `(rule grid-line-consistency)` | A grid line, a line that writes a decision state under the continuation mark (`m_d[>] = a + c[>]`), agrees with the law of motion solved for that state at the candidates: its right side and the law of motion so solved reduce to one expression, every function read as an opaque symbol. | — | `refusals.py`, `RULES`, `"grid-line-consistency"` |
| <a id="identity-collision"></a>`identity-collision` | `(rule identity-collision)` | No authored name collides with the spelling of an identity: a name containing the colon that separates its segments, or a name equal to one of the words a reader tests for in the last segment — `result`, `declared`, `merged`. | — | `refusals.py`, `RULES`, `"identity-collision"` |
| <a id="readable-form"></a>`readable-form` | `(rule readable-form)` | The item is a form the construction rules read. | — | `refusals.py`, `RULES`, `"readable-form"` |
| <a id="multiplier-declaration"></a>`multiplier-declaration` | `(rule multiplier-declaration)` | A multiplier is declared inside the block whose continuation grid it extends, once, marked `[>]`, with one declared set and one bound after ⟂ that names continuation states, multipliers of the block, parameters, numbers or `inf`. | — | `refusals.py`, `RULES`, `"multiplier-declaration"` |
| <a id="set-mismatch"></a>`set-mismatch` | `(rule set-mismatch)` | A field produced on one declared set and consumed on another is declared with sets whose inclusion holds; otherwise the stage declares the inclusion through the control's feasible set. | — | `refusals.py`, `RULES`, `"set-mismatch"` |
| <a id="category-codes"></a>`category-codes` | `(rule category-codes)` | A set marked `!categories` is a nonempty range of integers written as a comprehension over ℤ or ℕ, whose annotation gives each member one category name and each name one member. The marker is written only on a top-level named set, and a field declared on a set with category codes names that set at every site that names a set. | — | `refusals.py`, `RULES`, `"category-codes"` |
| <a id="value-input-role"></a>`value-input-role` | `(rule value-input-role)` | A statement of a backward block reads values or marginal values, not both: its kernel acts on one role and its output has that role. | — | `refusals.py`, `RULES`, `"value-input-role"` |
| <a id="marginal-role-retired"></a>`marginal-role-retired` | `(rule marginal-role-retired)` | A header lists value fields and the controls at which its lines are read, and no marginal value: a role word the language no longer holds is refused with a sentence naming the derivative term `D_{a}V[>]`, by which a line reads the derivative of a value. | — | `refusals.py`, `RULES`, `"marginal-role-retired"` |
| <a id="derivative-coordinate"></a>`derivative-coordinate` | `(rule derivative-coordinate)` | The subscript of a derivative term names a state coordinate of the perch at which the value is read, written without its mark, and no discrete coordinate; the refusal names the perch's coordinates. | — | `refusals.py`, `RULES`, `"derivative-coordinate"` |
| <a id="signature-complete"></a>`signature-complete` | `(rule signature-complete)` | A forward block's header lists every field its lines read that no earlier line of the block defines. A backward block's header lists the value fields its lines read and the controls at which they are read, but no state; a state of its output perch is a coordinate. A value field a backward header lists and no line of the block reads is admitted: it is left out of the block's builder and recorded as a diagnostic, `unread-input`, in place of a refusal. | — | `refusals.py`, `RULES`, `"signature-complete"` |
| <a id="header-coordinate"></a>`header-coordinate` | `(rule header-coordinate)` | A backward block's header lists the value fields it reads and writes and the controls at which its lines are read, and no state: a state of the perch at which its output stands is a coordinate of the output function, and a state of its input perch is reached through the law of motion. | — | `refusals.py`, `RULES`, `"header-coordinate"` |
| <a id="input-perch-state"></a>`input-perch-state` | `(rule input-perch-state)` | A backward line reads a state of its input or a later perch only through the law of motion. A direct read is refused, including in a relation or a condition after `⟂`. A read under the expectation over the edge's shock and continuation-state indexing on a policy candidate line are admitted. | — | `refusals.py`, `RULES`, `"input-perch-state"` |
| <a id="kernel-form"></a>`kernel-form` | `(rule kernel-form)` | A kernel that `compile_kernel` writes as a Python function is retained arithmetic and calls to closed-form functions; a symbolic derivative has no compile rule. The function takes the values of the parameters it reads as arguments, so a symbolic version compiles too and answers no values, `parameter_values` None. | — | `refusals.py`, `RULES`, `"kernel-form"` |
| <a id="method-option-value"></a>`method-option-value` | `(rule method-option-value)` | Every configured method option has the type its public method row names. | — | `refusals.py`, `RULES`, `"method-option-value"` |
| <a id="kernel-target"></a>`kernel-target` | `(rule kernel-target)` | `kernel` and `compile` read a primitive operator box, and `compile` one whose kernel is g or G. | — | `refusals.py`, `RULES`, `"kernel-target"` |
| <a id="distribution-dependency"></a>`distribution-dependency` | `(rule distribution-dependency)` | The distribution declarations read one another without a cycle, and a declaration does not read its own subject. | — | `refusals.py`, `RULES`, `"distribution-dependency"` |
| <a id="distribution-edge"></a>`distribution-edge` | `(rule distribution-edge)` | The shocks of connected declarations are drawn on the edge of one forward builder. | — | `refusals.py`, `RULES`, `"distribution-edge"` |
| <a id="distribution-domain"></a>`distribution-domain` | `(rule distribution-domain)` | A declaration's family parameters lie in the family's domain: matched dimensions, a symmetric positive semidefinite covariance, nonnegative variances and deviations, finite endpoints in order, positive scales, and real arguments that have a number. | — | `refusals.py`, `RULES`, `"distribution-domain"` |
| <a id="conditional-not-declared"></a>`conditional-not-declared` | `(rule conditional-not-declared)` | The conditional distribution an expectation needs is a declared conditional, a product of them, or a marginal or conditional of a joint normal declaration whose conditioning block is positive definite. | — | `refusals.py`, `RULES`, `"conditional-not-declared"` |
| <a id="branch-form"></a>`branch-form` | `(rule branch-form)` | A branching block holds one labeled nested block per label and nothing else, at least two, in the forward block from the decision perch to the continuation perch, whose own output side is empty; a nested block has an empty input side and writes continuation fields. | — | `refusals.py`, `RULES`, `"branch-form"` |
| <a id="branch-labels"></a>`branch-labels` | `(rule branch-labels)` | The nested blocks carry the labels of the block's label coordinate, a control or a shock with its law, whose set is a finite set of at least two labels, each once and in the set's order. | — | `refusals.py`, `RULES`, `"branch-labels"` |
| <a id="branch-tuple-mismatch"></a>`branch-tuple-mismatch` | `(rule branch-tuple-mismatch)` | The value line selects by one tuple indexed by the label coordinate, one entry per label, and the policy maximizes over the same tuple in the same order; a branch a shock selects is read under the expectation over the shock alone. | — | `refusals.py`, `RULES`, `"branch-tuple-mismatch"` |
| <a id="branch-value-position"></a>`branch-value-position` | `(rule branch-value-position)` | A continuation value stands at one position of the selection tuples, the position of the branch on whose fields it is a function. | — | `refusals.py`, `RULES`, `"branch-value-position"` |
| <a id="branch-law"></a>`branch-law` | `(rule branch-law)` | The law of a label shock gives one probability to each label in the order of the labels, `Categorical((p₁, …, pₙ))` or `Bernoulli(p)` over two. | — | `refusals.py`, `RULES`, `"branch-law"` |
| <a id="not-constructed"></a>`not-constructed` | `(rule not-constructed)` | The item is a form of the language the construction does not read (`NotConstructed`). | — | `refusals.py`, `RULES`, `"not-constructed"` |
| <a id="block-header-mismatch"></a>`block-header-mismatch` | `(rule block-header-mismatch)` | A method block's header matches the builder the methods file opens with it: the block joins the builder's perches, writes the builder's outputs, and reads the builder's inputs or inputs its header declares with a set and a role. | — | `refusals.py`, `RULES`, `"block-header-mismatch"` |
| <a id="block-name-undefined"></a>`block-name-undefined` | `(rule block-name-undefined)` | A line of a method block calls a function the stage file or the block file defines, or a primitive function of the language. | — | `refusals.py`, `RULES`, `"block-name-undefined"` |

<!-- /reference-table -->

## 3 The catalogue

Every rule with the four parts of its refusal, provoked from the smallest example the package keeps for it. The example of each rule is the text the refusal test provokes, so a rule that changes is read here and in the test at once.

```python
from bellman.refusal_catalogue import catalogue

print(catalogue())
```

```text
syntax  (graph construction)
  where  cons.bl, line 17, column 40
  what
    [id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊] : !dcsn -> (a : Xa) : !cntn] {
                                           ^
  why    the file writes `]` here, and the language admits `)` or `,` at this place
  write  a side of a block header: a side is parenthesized in general; a single coordinate may stand bare (V : !dcsn -> …)

stage-name  (graph construction)
  where  t.bl, line 2, column 1 (address '2')
  what
    @stage: two
    ^
  why    2 '@stage' lines name the stage: 'one' at t.bl:1:1 (term address '1'), 'two' at t.bl:2:1 (term address '2'); a stage file has exactly one, so delete all but the line that names it

declared-once  (graph construction)
  where  t.bl, line 5, column 5 (address 'b.3')
  what
        y = u + z :: [!node]
        ^
  why    an authored node requires a nonempty explicit id; write an id before the mark, `:: [id=<name>, !node]`

defined-once  (graph construction)
  where  t.bl, line 4, column 5 (address 'b.second')
  what
        W = 2*V[>] :: [id=second, !node]
        ^
  why    block 'b' already defines W at t.bl:3:5 (term address 'b.first'), and this operative equation defines it again; an operative left side is defined once within a block
  write  Remove one definition, give one result another name, or mark a line that only documents the model `!doc`.

one-name-one-meaning  (graph construction)
  where  t.bl, line 3, column 1 (address 'b')
  what
    [id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {
    ^
  why    'y' is a field, first listed here, and a function, defined at t.bl:2:1 (term address '2'); a name has one meaning in a stage

parameter-or-field  (graph construction)
  where  t.bl, line 2, column 1 (address '2')
  what
    c : ℝ₊ @ !ctrl
    ^
  why    the top-level declaration of 'c' carries the role word for 'control', but no block header lists 'c': a role belongs to a field, and a field is a name a block reads or writes, while a top-level declaration that no header lists is a parameter, a number calibration binds. List 'c' on a side of the block that uses it, or drop the role word and leave it a parameter

field-perch  (graph construction)
  where  t.bl, line 2, column 1 (address 'b')
  what
    [id=b, (V[>] : ℝ @ !vlu) : !dcsn -> (W : ℝ) : !dcsn] {
    ^
  why    the mark on V[>] places the field at the cntn perch, but the input side of block 'b' is marked `: !dcsn`; a mark agrees with its side's perch word (D06)

name-in-scope  (graph construction)
  where  t.bl, line 3, column 5 (address 'b.1')
  what
        y = q
        ^
  why    the line mentions q, which the stage does not declare: it is no field of the stage, no line of block 'b' above it defines it, and it is no parameter, shock, named space, or function. Declare it, or write one of the names in scope here: x, y

family-selection  (graph construction)
  where  t.bl, line 3, column 5 (address 'b.1')
  what
        y = (a, b)[q]
        ^
  why    the selection (a, b)[q] selects by 'q', which the stage does not declare; a key requires a finite set of 2 members

well-typed  (graph construction)
  where  t.bl, line 4, column 5 (address 'b.1')
  what
        w = 𝑓 + 1
        ^
  why    `𝑓` is a function, and `𝑓 + 1` reads it as a number; arithmetic, an ordered comparison and the bounds of an interval read numbers. Apply the function to its arguments, `𝑓(…)`

divisor-nonzero  (graph construction)
  where  t.bl, line 3, column 5 (address 'b.1')
  what
        y = x/0
        ^
  why    `x/0` divides by zero, which is defined at no point; a divisor the file writes as a number is not zero. Write a divisor other than zero

shock-observed  (graph construction)
  where  t.bl, line 32, column 5 (address 'dcsn_to_arvl.value')
  what
        V[<]  = V                :: [id=value]
        ^
  why    the line is read at the arvl perch and mentions V, a field at the dcsn perch; the edge from the arvl perch to the dcsn perch draws the shock y, so the value of V is not known at the arvl perch. Write the expectation over it, `E_{y}(…)`

shock-reintroduced  (graph construction)
  where  t.bl, line 17, column 5 (address 'cntn_to_dcsn.value')
  what
        V = E_{y,z}(V[>]) + y :: [id=value]
        ^
  why    the line reads the shock y beside a term in which cntn_to_dcsn.value:Expectation:1 has already integrated y, and no other value input of that combination still depends on y; a backward function does not depend again on a shock after its expectation (AMD-SG-008 §4, rule shock-reintroduced); move the read of y inside that expectation, or integrate the combination after it

forward-composite  (graph construction)
  where  t.bl, line 38, column 5 (address 'policy.g_cntn_to_dcsn')
  what
        w[>] = w              :: [id=g_cntn_to_dcsn]
        ^
  why    the line is read at the cntn perch and mentions w, a field at the dcsn perch, which comes before it: a stage runs arrival, decision, continuation, so a line at the cntn perch is a function of the cntn state, and the file defines the cntn state from the dcsn state, not the dcsn state from the cntn state. Write the cntn-perch field the law of motion defines, or state the equation at the dcsn perch

transition-without-expectation  (graph construction)
  where  t.bl, line 5, column 5 (address 'step.1')
  what
        y = x + E_{z}(z)
        ^
  why    the transition block 'step' integrates over a shock in statement 'step.1'; a forward builder is the push-forward of a measure through the law of motion 𝑔 and takes no expectation; write the integration in a backward block

one-implicit-statement  (graph construction)
  where  t.bl, line 9, column 5 (address 'policy.second')
  what
        c + 1 = 2*c[>] :: [id=second]
        ^
  why    block 'policy' has a second implicit statement for its output 'c'; the first is at t.bl:8:5 (term address 'policy.first'). A block has at most one implicit statement per output field, since two equations in one unknown state two problems

definition-order  (graph construction)
  where  t.bl, line 2, column 1 (address '2')
  what
    𝑓(x : ℝ) := 𝑔(x)
    ^
  why    the function definitions form a cycle: 𝑓 (t.bl:2:1 (term address '2')) references 𝑔 (t.bl:3:1 (term address '3')) references 𝑓 (t.bl:2:1 (term address '2')). No dependency order exists, so no definition can be expanded; break the cycle

derivative-one-name  (graph construction)
  where  t.bl, line 3, column 1 (address '3')
  what
    df := D_{x,y}(f)
    ^
  why    the derivative D_{x, y}(f) names 2 formal arguments (x, y); a derivative names exactly one formal argument
  write  Write one derivative for one named formal argument, such as `D_{x}(f)`.

derivative-scalar-coordinate  (graph construction)
  where  t.bl, line 3, column 1 (address '3')
  what
    df := D_{x}(f)
    ^
  why    the derivative D_{x}(f) names the formal argument 'x' of function 'f', which is product-valued; a derivative names one scalar formal argument
  write  Declare scalar formal arguments and write one derivative with respect to one of them.

stage-boundary  (graph construction)
  where  t.bl, line 24, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊, z : ℝ) : !dcsn -> (a : ℝ₊) : !cntn] {
    ^
  why    no block writes the field 'z' at the dcsn perch, and the stage does not receive it: the stage receives the continuation values and the arrival state, and a field at the dcsn perch in this position is neither. Write it as the output of a block, or list it where the stage receives it

output-defined  (graph construction)
  where  t.bl, line 17, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : Xa) : !cntn] {
    ^
  why    block 'dcsn_to_cntn' declares output 'cons:cntn:a', but its body supplies no defining equation

grid-line-consistency  (graph construction)
  where  cons.bl, line 34, column 5 (address 'policy.endoggrid')
  what
        m_d[>] = a + 2*c[>]              :: [id=endoggrid]
        ^
  why    the grid line m_d[>] = a + 2*c[>] disagrees with the law of motion of block 'dcsn_to_cntn': with its line a = m_d - c solved for m_d at the candidate c[>], the law of motion gives m_d[>] = a + c[>], and a + 2*c[>] does not reduce to a + c[>] by algebraic simplification; write the grid line as the law of motion solved for m_d, m_d[>] = a + c[>]

identity-collision  (graph construction)
  where  t.bl, line 2, column 1 (address 'b')
  what
    [id=b, (x : ℝ) : !dcsn -> (result : ℝ) : !dcsn] {
    ^
  why    the field 'result' is one of the reserved words result, declared, merged, by which a reader knows an occurrence's result wire, a declared wire and a merged box from the last segment of an identity; write another name for the field

readable-form  (graph construction)
  where  t.bl, line 2, column 1 (address '2')
  what
    ρ : ℝ := 2
    ^
  why    the declaration of ρ carries a value; a stage file declares what a name is, not what it equals: calibration supplies the value, and the stage reads it through `.calibration`

multiplier-declaration  (graph construction)
  where  cons.bl, line 33, column 5 (address 'policy.slackness')
  what
        μ[>]   : ℝ₊ ⟂ c >= 0             :: [id=slackness]
        ^
  why    the bound of the multiplier 'μ' names 'c', written c, a control; the bound of a declared multiplier names continuation states, multipliers of block 'policy', parameters, numbers or `inf` (AMD-SG-035 D11). Write the bound on a continuation state, or state the condition on a line of the block with its own clause

set-mismatch  (graph construction)
  where  t.bl, line 2, column 1 (address 'a')
  what
    [id=a, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] { y = x }
    ^
  why    the field y is produced by 'a' on ℝ and consumed by 'b' on ℝ₊₊, and ℝ does not lie in ℝ₊₊; declare matching sets, or state the control's feasible set in the declarative maximisation statement (D18, D19)

category-codes  (graph construction)
  where  t.bl, line 3, column 1 (address 't.bl:3')
  what
    HouseholdStatus := {i : ℤ | i >= 0, i <= 1} :: [!categories household_status, newborn=0, old=2]
    ^
  why    the set HouseholdStatus is marked `!categories`, and its definition and its annotation give no category map. The entry `old=2` gives a code outside HouseholdStatus, the integers from 0 to 1; give each category a code from 0 to 1. The set HouseholdStatus holds the integers from 0 to 1, and the member 1 has no category; give each member one category

value-input-role  (graph construction)
  where  t.bl, line 6, column 5 (address 'cntn_to_dcsn.value')
  what
        V = V[>] + dV[>] :: [id=value]
        ^
  why    the statement reads the value V[>] and the marginal value dV[>]; a kernel of a backward block acts on values or on marginal values and its output has one role (AMD-SG-005 §1a rule 4), so a statement mixing the two has no single kernel: write the value and the marginal value on separate statements

marginal-role-retired  (graph construction)
  where  t.bl, line 7, column 45 (address 'policy')
  what
    [id=policy, (V[>] : ℝ @ !vlu, dV[>] : ℝ₊₊ @ !mrgnvl) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
                                                ^
  why    the header writes `!mrgnvl`, a role word the language no longer holds: a backward header lists value fields and the controls at which its lines are read, and a line reads the derivative of a value by the term D_{a}V[>]
  write  Delete dV[>] from the header and write D_{a}V[>] where a line reads the derivative of V[>].

derivative-coordinate  (graph construction)
  where  t.bl, line 8, column 14 (address 'policy.InvEuler')
  what
        c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{m_d}V[>])    :: [id=InvEuler]
                     ^
  why    the derivative term D_{m_d}V[>] names m_d, which is no state coordinate of the continuation perch, at which V[>] is read; the perch's coordinates are a. A derivative is taken in a state coordinate of the perch at which the value is read, written without its mark, and over no discrete coordinate
  write  Write D_{a}V[>].

signature-complete  (graph construction)
  where  t.bl, line 6, column 5 (address 'd.1')
  what
        w = x + y
        ^
  why    the line reads x, which the header of block 'd' does not list and no earlier line of the block defines; a forward block's header lists every field its lines read (AMD-SG-007 §5, rule signature-complete). List it in the header, `(y, x) : !dcsn -> (w : ℝ) : !dcsn`, or define it on an earlier line of the block. The correction writes a perch word on each field of a side where the side's one word no longer holds for every field; the perch of a control is unchanged by either spelling, being the decision perch wherever a header lists it (AMD-SG-017 §2)

header-coordinate  (graph construction)
  where  t.bl, line 5, column 1 (address 'cntn_to_dcsn')
  what
    [id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, x_d : !dcsn) -> (V : ℝ @ !vlu) : !dcsn] {
    ^
  why    the header of block 'cntn_to_dcsn' lists x_d on its input side, and the block is a backward block, whose header lists the value fields it reads and writes and the controls at which its lines are read, and no state (rule header-coordinate). x_d is a state of the dcsn perch, the perch at which the block's output stands, so it is a coordinate of the output function and no input of the block. Remove the listing, `(V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu) : !dcsn`; a line of the block may still mention a state of the dcsn perch, which is a coordinate of what it defines
  write  Remove the state from the header; a line of the block may mention a state of the perch at which its output stands, as a coordinate of what it defines.

input-perch-state  (graph construction)
  where  t.bl, line 9, column 5 (address 'cntn_to_dcsn.1')
  what
        V = a + V[>]
        ^
  why    the line is read at the dcsn perch and mentions a, a state of the cntn perch, the perch block 'cntn_to_dcsn' reads its inputs at; a backward block reaches a state of its input perch, or of a later perch, through the law of motion alone, and read directly the state would stand free in a rule that holds on the dcsn state (rule input-perch-state). The forward block 'dcsn_to_cntn' defines it at t.bl:6:5 (term address 'dcsn_to_cntn.1'), `a = x_d`. Write `x_d` in its place
  write  Write the forward block's expression for the state in its place, or read the state under the expectation over the shock drawn on the edge.

kernel-form  (graph construction)
  where  address 'cntn_to_dcsn.marginal'
  why    stage 'cons_savings_iid': the component dV (cntn_to_dcsn.marginal) of the kernel of 'cntn_to_dcsn:Aggregation' (cons_savings_iid:G:cntn_to_dcsn) contains the call 𝑑𝑢(c) of 𝑑𝑢 := D_{c}(𝑢) (cons_savings_iid:function:𝑑𝑢), which is not a closed-form function; no compile rule evaluates it: compile evaluates retained arithmetic and calls to closed-form named functions and selects no numerical method (AMD-SG-007 §3.1, rule kernel-form); define that function in closed form, or read the kernel with kernel(stage, box)

method-option-value  (graph construction)
  where  address 'cntn_to_dcsn:Evaluation'
  why    stage 'cons', place cntn_to_dcsn:Evaluation, method !Cartesian, option 'orders': {'m_d': -5} does not give positive integers; configure requires the option value to have its declared type; write positive integer orders at actual coordinates

kernel-target  (graph construction)
  where  address 'cntn_to_dcsn'
  why    stage 'cons': compile evaluates the explicit numerical kernels g and G, and 'cntn_to_dcsn:Evaluation' is a Evaluation box whose kernel, identity at (m_d, m_d); no policy is inserted, has no callable representation (AMD-SG-007 §3.1, rule kernel-target); inspect it with kernel(stage, box), or compile a pullback, push-forward or aggregation box

distribution-dependency  (graph construction)
  where  t.bl, line 4, column 1 (address '4')
  what
    y ~ N(z, 1)
    ^
  why    the distribution declarations form a cycle: t:distribution:y (at 4) reads z, t:distribution:z (at 5) reads y; the joint distribution of an edge is the product of declared conditional distributions in a dependency order, which a cycle does not have (AMD-SG-009 §§2–3, rule distribution-dependency); remove one of the shock arguments, or write the dependent shocks as one joint declaration

distribution-edge  (graph construction)
  where  t.bl, line 3, column 1 (address '3')
  what
    y ~ N(0, 1)
    ^
  why    the shock y is listed by the forward builders 'arvl_to_dcsn' and 'dcsn_to_cntn'; a shock is drawn on one edge, the edge of the one forward builder whose signature lists it (AMD-SG-009 §2, rule distribution-edge); list it on one forward builder

distribution-domain  (graph construction)
  where  t.bl, line 4, column 1 (address 't.bl:4')
  what
    (y, z) ~ N((0, 0), ((1, 2), (2, 1)))
    ^
  why    the covariance ((1, 2), (2, 1)) of the normal declaration t:distribution:y_z is not positive semidefinite: its smallest eigenvalue is -1.0 (AMD-SG-009 §4, rule distribution-domain); write a symmetric positive semidefinite covariance matrix

conditional-not-declared  (graph construction)
  where  t.bl, line 17, column 5 (address 'cntn_to_dcsn.value')
  what
        V = E_{z}(E_{y}(V[>])) :: [id=value]
        ^
  why    the expectation cntn_to_dcsn.value:Expectation:2 needs the distribution of y given z from the normal declaration two_nodes:distribution:y_z, whose conditioning covariance Σ_CC = 0 = 0.0 is singular (smallest eigenvalue 0.0); the normal conditional requires Σ_CC positive definite, and no pseudoinverse is taken (AMD-SG-009 §4, rule conditional-not-declared); condition on shocks whose covariance block is positive definite, or integrate them jointly

branch-form  (graph construction)
  where  t.bl, line 5, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    ^
  why    block 'dcsn_to_cntn' holds one nested block; a branching block holds at least two, one for each label of its label coordinate; write a nested block for each missing label

branch-labels  (graph construction)
  where  t.bl, line 9, column 5 (address 'dcsn_to_cntn.stop')
  what
        [label=stop, () -> (a_r : ℝ₊) : !cntn] {
        ^
  why    the label 'stop' is not a member of {work, retire}, the set of the label coordinate 'd'; write one nested block for each member, in the set's order

branch-tuple-mismatch  (graph construction)
  where  t.bl, line 14, column 5 (address 'cntn_to_dcsn.choice_value')
  what
        V = (V_w[>], V_r[>])[d]                :: [id=choice_value]
        ^
  why    the value line selects from (V_w[>], V_r[>]) by 'd', and the policy line policy.choice maximizes over (V_r[>], V_w[>]); write the policy's maximand as the value line's tuple, in its order

branch-value-position  (graph construction)
  where  t.bl, line 14, column 5 (address 'cntn_to_dcsn.choice_value')
  what
        V = (V_w[>], V_w[>])[d]                :: [id=choice_value]
        ^
  why    V_w[>] is read at the position of 'work' and at the position of 'retire'; a branch value stands at one position in every tuple, the position of its branch; write each branch value at its own branch's position alone

branch-law  (graph construction)
  where  t.bl, line 7, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (a_d, s) : !dcsn -> ()] {
    ^
  why    the shock 's' selects the branches of block 'dcsn_to_cntn' and has no distribution; the branches are weighted by the distribution of the shock, so write `s ~ Categorical((p_young, p_old))`, one probability for each label in the order {young, old}

not-constructed  (graph construction)
  where  t.bl, line 5, column 1 (address 'dcsn_to_cntn')
  what
    [id=dcsn_to_cntn, (a_d, c : !ctrl @ [0,1], d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    ^
  why    block 'dcsn_to_cntn' lists the controls 'c', 'd' beside its branches; this version of the package constructs a branching block whose branches state equations alone and whose label coordinate is its one control, or a shock over a finite set in a stage that chooses nothing (docs/Bellman-Sym/05-branching.md)

(a) a builder box by its block id; `<block-id>_builder` for a transition block  (the identity table)
  where  stage 'cons', target 'nowhere'
  why    'nowhere' in stage 'cons' names no builder of the stage, no operator a statement of it records, and not its boundary representation. The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

(b), (c) a node box or a line by `<block-id>.<statement-id>`  (the identity table)
  where  stage 'cons', target 'cntn_to_dcsn.absent'
  why    'cntn_to_dcsn.absent' in stage 'cons' names no line of block 'cntn_to_dcsn': no line carries the id 'absent'; the block's named lines are cntn_to_dcsn.value, cntn_to_dcsn.marginal. The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

(ii) a positional address `<block-id>.<n>` is not a target; the line needs an id  (the identity table)
  where  stage 'cons', target 'cntn_to_dcsn.1'
  why    'cntn_to_dcsn.1' in stage 'cons' is a positional address; line 1 of block 'cntn_to_dcsn' is `V = 𝑢(c) + V[>]`, named 'cntn_to_dcsn.value' — name it by its id. The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

(d) every occurrence of an operator by its stage-wide name  (the identity table)
  where  stage 'cons', target 'E'
  why    'E' in stage 'cons' names the expectation over the shocks; no statement of the stage records an occurrence of 'E', and an operator is a target only where a statement records it — none is derived from a method name. The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

(e) one occurrence by `<block-id>.<statement-id>.<operator>`  (the identity table)
  where  stage 'cons', target 'cntn_to_dcsn.value.E'
  why    'cntn_to_dcsn.value.E' in stage 'cons' names an operator in `V = 𝑢(c) + V[>]`, the output statement cntn_to_dcsn.value, which carries no operator occurrence; a method attaches to an operator occurrence, to the builder, to a node box, to an output statement with no operator occurrence (the representation of the field it defines — `on: cntn_to_dcsn.value` names this one), to one occurrence of a named line that carries it, by `<block-id>.<statement-id>.<operator>`, or to the boundary representation. The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

(g) `evaluate`: the one authored occurrence, else the boundary representation; two or more authored occurrences are named by their addresses  (the identity table)
  where  stage 'cons', target 'evaluate'
  why    'evaluate' in stage 'cons' names no authored occurrence, and the stage has the implicit statement policy.cons_choice (`c = c[>]`): the representation of that policy is a method at the Evaluation of its block (`on: policy`), `!egm` among them where the block writes the grid line, and the representation of the value function at the decision perch is named by the lines of the backward builder (cntn_to_dcsn.value, cntn_to_dcsn.marginal) (the consequence for a stage with an implicit statement; D07). The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

(h) one target per entry; a comma-separated entry is split by L02  (the identity table)
  where  stage 'cons', target 'policy, cntn_to_dcsn'
  why    'policy, cntn_to_dcsn' in stage 'cons' lists several targets separated by commas, and an entry names one target (spec 0.3c §4.3: a comma-containing string is not an operator identifier); the migration L02 splits such an entry, and each part resolves on its own. The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

a target has one, two, or three dot-separated parts  (the identity table)
  where  stage 'cons', target 'a.b.c.d'
  why    'a.b.c.d' in stage 'cons' is not the form of a target: a block id, `<block-id>.<statement-id>`, `<block-id>.<statement-id>.<operator>`, a stage-wide operator name, or `evaluate`. The places of stage 'cons' are — builders: arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy; named lines: cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality, policy.InvEuler, policy.endoggrid, policy.cons_choice; operators: solve (policy.cons_choice.solve); `evaluate`: not a target here, since the stage has the implicit statement policy.cons_choice.

a target reaches one place; two is a construction defect  (the identity table)
  where  stage 'two_places', target 'arvl_to_dcsn_builder'
  why    'arvl_to_dcsn_builder' in stage 'two_places' reaches 2 places, which is a construction defect: the builder box 'arvl_to_dcsn_builder' and the builder box 'arvl_to_dcsn' under the suffix `_builder`. The places of stage 'two_places' are — builders: arvl_to_dcsn, arvl_to_dcsn_builder; named lines: none; operators: none; `evaluate`: not a target here: no backward builder from the continuation to the decision perch writes a value field.

target-not-found  (the identity table)
  where  stage 'cons', target 'cntn_to_dcsn:Substitution:V'
  why    stage 'cons': 'cntn_to_dcsn:Substitution:V' names no box of the version's views and no record of its definitions table; a printed view, a kernel and a compiled kernel read an actual box or definition (AMD-SG-007 §2, rule target-not-found); write a box name that stage.builder.bwd.primitives.list() or stage.builder.fwd.primitives.list() shows, or an identity of stage.definitions

target-ambiguous  (the identity table)
  where  stage 'cons', target 'cntn_to_dcsn'
  why    stage 'cons': 'cntn_to_dcsn' names 2 different targets — the box cntn_to_dcsn in the initial diagram, backward at the grain builder, builder cntn_to_dcsn | the box cntn_to_dcsn in the builders graph, backward at the grain builder, builder cntn_to_dcsn; one name selects one target only when the boxes it names are equal (AMD-SG-007 §2, rule target-ambiguous); pass the box itself from the view and grain you mean

target-version  (the identity table)
  where  stage 'cons', target 'cntn_to_dcsn:Pullback'
  why    stage 'cons': the box 'cntn_to_dcsn:Pullback' passed is no box of a graph of this version; a query reads the boxes of the version it is asked of, and versions share no object (AMD-SG-007 §2, rule target-version); ask the version whose view holds the box, or pass a box of this version's view

method-attachment  (the identity table)
  where  stage 'cons', target 'cntn_to_dcsn.value'
  why    Method target 'cntn_to_dcsn.value' in stage 'cons': !egm does not admit target kind statement; method-attachment admits builder, operator argmax; !egm stands at the Evaluation of a block that writes the grid line, named by the block id, or on a maximization that carries its first-order condition as a property; write an on: target of one of these kinds

recipe-shape  (the Bellman factory)
  where  registry/spec.yml, address 'stages'
  what
{'registry': {}}
  why    the recipe has no top-level `stages` mapping
  write  stages: {<stage key>: {stage: <path>.bl, calibration: {all: [...]}, settings: {all: [...]}, methods: {all: [...]}}}

recipe-source  (the Bellman factory)
  where  registry/spec.yml, address 'stages.two_nodes.calibration.all'
  what
calibration/absent
  why    the registry holds no source file 'calibration/absent'; tried registry/calibration/absent.yml, registry/calibration/absent.yaml, registry/calibration/absent
  write  the name of a file under the registry, without its extension

recipe-slot-unknown  (the Bellman factory)
  where  registry/spec.yml, address 'fil'
  what
fil
  why    the keyword 'fil' names no slot of the recipe; its slots are $fill, $method_switch
  write  one of $fill, $method_switch, or a new `$` name in a source list of the recipe

recipe-template-agreement  (the Bellman factory)
  where  registry/spec.yml, address 'other'
  what
other
  why    the recipe names the stage 'other', which no period of registry/trellis.yml holds
  write  'other' in a period template of registry/trellis.yml, or no entry for it in the recipe

slot-value-not-a-mapping  (the Bellman factory)
  where  registry/spec.yml, address 'fill'
  what
'β: 0.9'
  why    slot 'fill' is given a str, not a mapping
  write  fill={'calibration': {...}, 'settings': {...}} or a flat mapping of names to values

fill-names-nothing  (the Bellman factory)
  where  registry/spec.yml, address 'fill'
  what
beta
  why    slot 'fill', key 'beta': no stage that receives this slot declares 'beta' as a parameter (two_nodes declares β, R) or as a setting (two_nodes declares n_k), and no registry block admits it; a fill key names a parameter or a setting of a stage that receives it (AMD-FAC-002 §5)
  write  one of the declared names R, n_k, β

fill-mixes-kinds  (the Bellman factory)
  where  registry/spec.yml, address 'fill'
  what
β, n_k
  why    slot 'fill' names the parameters β and the settings n_k in one flat mapping
  write  fill={'calibration': {...}, 'settings': {...}}, each name under its kind

trellis-file-shape  (the Bellman factory)
  where  registry/broken.yml, address 'periods'
  what
{'stages': []}
  why    the trellis file has no list `periods`
  write  periods: [{template: period.yml, repeat: 51}] or the periods written out

record-shape  (the Bellman factory)
  where  address 'record'
  what
['stage']
  why    missing fields ['calibration', 'methods', 'settings']; unknown fields []
  write  a record with stage, calibration, settings and methods, and optionally label and provenance

period-join-cycle  (the Bellman factory)
  where  address 'periods[0]'
  what
disc continues to 'a' and port arrives at 'k'; port continues to 'm_next' and disc arrives at 'a'
  why    the joins of the period form a cycle: disc continues to 'a' and port arrives at 'k'; port continues to 'm_next' and disc arrives at 'a'; the stages of a period are ordered by their field dependencies, so no stage may take a field it produces through the others
  write  remove or redirect an authored connector so that the stage dependencies have no cycle; qualify an endpoint with its stage key where its bare name is ambiguous

connector-names-no-field  (the Bellman factory)
  where  address 'periods[0].connectors[0]'
  what
{'from': 'cons', 'to': 'port', 'fields': {'a': 'k'}, 'label': 'x'}
  why    the connector is written in the keyed form and has the key 'label' beside from, to and fields
  write  {<continuation field>: <arrival field>}, or within a period {from: <stage key>, to: <stage key>, fields: {<continuation field>: <arrival field>}}

period-parameter-agreement  (the Bellman factory)
  where  registry/trellis.yml, address 'periods[0]'
  what
R : ℝ₊₊ in two_nodes; R : (-inf, 0) in other
  why    the stages two_nodes (registry/stages/two_nodes/two_nodes.bl) and other (registry/stages/other/other.bl) of the period declare the parameter 'R' with the sets ℝ₊₊ and (-inf, 0), which have no nonempty intersection; a parameter name names one parameter of the period, shared by the stages that declare it, so their declared sets agree (AMD-COMP-001 §2.3)
  write  one set for 'R' in every stage of the period, or sets the package reads whose intersection is not empty, or distinct names for distinct parameters

readable-file  (the Bellman factory)
  where  cons.txt
  what
cons.txt
  why    load_stage reads a stage file, and cons.txt is no .bl file
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
registry/spec.yml: address 'stages.two_nodes': the entry `stages.two_nodes` names no stage file; write `stage: stages/two_nodes/two_nodes.bl`, the path from this folder (rule recipe-shape)
```
