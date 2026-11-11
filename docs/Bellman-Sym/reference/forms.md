---
title: Expression forms
tags:
  - docs/reference
  - catalogue
  - grammar
audience: user
type: reference
---

# Expression forms

> [!summary]
> An [expression](../../wiki/expression.md) in a line of a stage file is built from names, numbers and arithmetic, and from nine named forms: the expectation `E_{θ}(…)`, the maximization `argmax_{c}(…)`, the implicit solution `solve_{c}(…)`, the derivative `D_{c}(𝑢)` of a declared function and `D_{a}V[>]` of a value, the inverse `Inv(𝑓)`, and the real functions `exp`, `log`, `max` and `min`. A shock's law is written on a line of its own, after `~`. The table gives each form as a stage file writes it, what it computes, the object of the [Bellman calculus](../../wiki/bellman_calculus.md) it realizes where the calculus defines one, and the entry of the package that defines it. A methods file, the addition beside a stage file, writes its blocks in the same forms, and §4 says how its lines are read.

> [!info]- Relationship with other documents
> **Builds on** — [Field equations](../03-field-equations.md): the lines in which these forms stand; [Constraints](../10-constraints.md): the inequalities and the `⟂` clause a line may carry.
> **Formal account** — [Operators](../../bellman-calculus/catalogues/operators.md): the operations the forms denote; [Equation parsing rules](../appendices/12-equation-parsing-rules.md) §§4–5: the variable a form binds and the reading of a law.
> **See also** — [Shock distributions](laws.md): the families a law names; [Symbol conventions](symbols-conventions.md): declarations, domains and type words.

## 1 Reading the table

Each row is one form. **written** gives the first occurrence of the form that the package finds in the stage files under `applications/`, printed back as normalized `.bl` text by `to_source` of `syntax/source.py`, so that `E_{Ψ,θ}` in `port.bl` shows as `E_{Ψ, θ}`, with the file, or says that no stage file writes it; the arithmetic row gives the six signs of the grammar, and the laws row the call of each family as the module docstring of `distributions/families.py` spells it. **meaning** gives, for an operator written with a subscript, the words the package attaches to it in `OPERATOR_MEANINGS` of `typing/line_unknowns.py`, followed for `D` by its defining expression; for a named function of the definitions table, its defining expression; and for the arithmetic, the names the grammar gives its six operations, add, sub, neg, mul, div and pow. **denotes** links to the section of [Appendix E.3](../../bellman-calculus/catalogues/operators.md) that defines the object the form realizes, and shows a dash where E.3 defines no such object, as for a real function applied at each point, such as `exp`. The laws row also shows a dash: each family has its own row, with its own link to E.3, on [the laws page](laws.md). **read from** names the module under `packages/bellman/bellman/`, its table and the key: `BOUND_OPERATORS` for the four heads written with a subscript in braces, and `PRIMITIVE_DEFINITIONS["definitions"]` for the named functions, each of which it defines exactly.

A subscript in braces names the variable the form binds: the shock an expectation integrates, the control a maximization chooses, or the unknowns a solution solves for. The subscript of a derivative instead names an argument of a function the file has already defined, as in `𝑑𝑢 := D_{c}(𝑢)`, or, where the operator is applied to a value field written with its perch mark, a state coordinate of the perch at which the value is read, written without its mark: `D_{a}V[>]` is the **derivative term**, the derivative of the continuation value in the continuation coordinate `a`, and `D_{a}D_{a}V[>]` its second derivative. A stage file writes the term without parentheses, and the row of `D` shows the first spelling of `D` on the corpus as the package's printer writes it, `D_{m_d}(V)`, the left side of the derivative line `D_{m_d}V = 𝑑𝑢(c)` of `cons.bl`. A subscript that names no state coordinate of that perch, or a discrete coordinate, is refused with the perch's coordinates named, and a derivative term of a value the block neither reads nor writes is refused as an undeclared name is ([Refusals](refusals.md)). A derivative term may stand on the right side of any line, where it reads a derivative, and on the left side of a line of a value builder's block, where it states the derivative of the value the builder writes, `D_{m_d}V = 𝑑𝑢(c)` ([Field equations](../03-field-equations.md) §2). The term applies an operator to a function the graph already holds; the package reads it and differentiates nothing.

<!-- reference-table -->

| form | written | meaning | denotes | read from |
|---|---|---|---|---|
| <a id="e"></a>`E` | `E_{Ψ, θ}(V[>])`<br>in `applications/portfolio-choice/declaration/stages/port/port.bl` | the expectation | [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators) | `typing/line_unknowns.py`, `BOUND_OPERATORS`, `"E"` |
| <a id="argmax"></a>`argmax` | `argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])`<br>in `applications/portfolio-choice/declaration/stages/cons/cons.bl` | the maximizer | [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators) | `typing/line_unknowns.py`, `BOUND_OPERATORS`, `"argmax"` |
| <a id="solve"></a>`solve` | `solve_{ς}(E_{Ψ, θ}(D_{m_next}V[>]*(Ψ - R)))`<br>in `applications/portfolio-choice/declaration/stages/port/port.bl` | root finding | [E.3 §7 Implicit and auxiliary operations](../../bellman-calculus/catalogues/operators.md#implicit-and-auxiliary-operators) | `typing/line_unknowns.py`, `BOUND_OPERATORS`, `"solve"` |
| <a id="d"></a>`D` | `D_{m_d}(V)`<br>in `applications/portfolio-choice/declaration/stages/cons/cons.bl` | the derivative<br>`f ↦ (c, y) ↦ sup_{a ∈ {a ∈ ℝ | ∀ epsilon ∈ (0, ∞): (∃ delta ∈ (0, ∞): (∀ t ∈ {t ∈ ℝ | (t²)^(1/2) > 0 ∧ (t²)^(1/2) < delta ∧ c + t ∈ C}: ((((f(c + t, y) − f(c, y))/t − a)²)^(1/2) < epsilon)))}} [a]` | [E.3 §7 Implicit and auxiliary operations](../../bellman-calculus/catalogues/operators.md#implicit-and-auxiliary-operators) | `typing/line_unknowns.py`, `BOUND_OPERATORS`, `"D"`<br>`typing/primitive_definitions.py`, `PRIMITIVE_DEFINITIONS["definitions"]`, `"D"` |
| <a id="exp"></a>`exp` | `exp(σ_z*ε)`<br>in `applications/durables/declaration/stages/tenure/tenure.bl` | `x ↦ exp(x)` | — | `typing/primitive_definitions.py`, `PRIMITIVE_DEFINITIONS["definitions"]`, `"exp"` |
| <a id="log"></a>`log` | `log(1 - p_zero)`<br>in `applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl` | `x ↦ sup_{t ∈ {t ∈ ℝ | exp(t) ≤ x}} [t]` | — | `typing/primitive_definitions.py`, `PRIMITIVE_DEFINITIONS["definitions"]`, `"log"` |
| <a id="min"></a>`min` | no stage file under `applications/` writes it | `a ↦ −sup_{i ∈ {i ∈ [0, ∞) | i ∈ ℤ ∧ i < n}} [−a(i)]` | — | `typing/primitive_definitions.py`, `PRIMITIVE_DEFINITIONS["definitions"]`, `"min"` |
| <a id="max"></a>`max` | no stage file under `applications/` writes it | `a ↦ sup_{i ∈ {i ∈ [0, ∞) | i ∈ ℤ ∧ i < n}} [a(i)]` | [E.3 §5 Named composites](../../bellman-calculus/catalogues/operators.md#derived-named-operators) | `typing/primitive_definitions.py`, `PRIMITIVE_DEFINITIONS["definitions"]`, `"max"` |
| <a id="inv"></a>`Inv` | `Inv(𝑑𝑢)`<br>in `applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl` | `f ↦ y ↦ sup_{x ∈ {x ∈ X | f(x) = y}} [x]` | — | `typing/primitive_definitions.py`, `PRIMITIVE_DEFINITIONS["definitions"]`, `"Inv"` |
| <a id="arithmetic"></a>arithmetic | `+` `-` `*` `/` `^` `**` | add, sub, neg, mul, div, pow | — | `syntax/grammars/stage.lark`, the rules `sum`, `product`, `molecule` and `_POW` |
| <a id="laws"></a>laws | `N(μ, v)` `LogNormal(μ, σ)` `Uniform(a, b)` `TruncatedNormal(μ, σ, l, u)` `TruncatedLogNormal(μ, σ, l, u)` `TypeIExtremeValue(μ, s)` `DiscreteMarkov(Π, points)` `MarkovChain(Π, points)` `Mixture((f₁, J₁), …)` `Categorical((f₁, …))` `Bernoulli(p)` | the law of a shock, written after `~` in its declaration; each family, its arguments and its meaning stand on [the laws page](laws.md) | — | `distributions/families.py`, `FAMILY_ARGUMENTS` |

<!-- /reference-table -->

A law names a shock, or a tuple of shocks, on the left of `~` and a family applied to its arguments on the right. [Shock distributions](laws.md) lists the families and the meaning of their arguments; [Equation parsing rules](../appendices/12-equation-parsing-rules.md) §4 states how separate laws and a joint law are read.

A braced form with any other head, such as `max_{c}(…)`, is refused under the rule `not-constructed` of [Refusals](refusals.md). A call of a name that neither the stage file nor the table defines, such as `sqrt(x)`, has no definition and denotes nothing; define the function in the stage file instead, `𝑟(x : ℝ₊) := x^(1/2)`.

## 2 Arithmetic

Between the named forms stand numbers, the names of [fields](../../wiki/field.md), [parameters](../../wiki/parameters.md) and functions, and the arithmetic of the grammar, `syntax/grammars/stage.lark`:

| Written | Reading |
|---|---|
| `a + b`, `a - b`, `-a` | Sum, difference and negation. A leading minus negates the product that follows it: `-a*b` is `-(a*b)`. |
| `a*b`, `a/b` | Product and quotient. A product is always written with `*`. |
| `a^b`, `a**b` | Power. The exponent is a single term, a name, a number, a call or an expression in parentheses: `c^(1-ρ)`. |
| `∞`, `inf` | Infinity; both spellings are one constant. |
| `(a, b)` | A tuple, a finite family of values. |
| `x[1]`, `(V_young[>], W_old[>])[s]` | Selection from a family, by position counted from one or by the label a coordinate takes. |
| `𝑢(c)` | A function the stage file defines, applied to as many arguments as it declares. |

A power binds more tightly than a product or a quotient, and these more tightly than a sum or a difference; parentheses group. A line relates two expressions by `=` or by one of the inequalities `<=`, `>=`, `<`, `>`, `≤` and `≥`, and may carry a complementary-slackness clause after `⟂`.

## 3 Forms that compile

A **kernel** is the function an [operation](operations.md) of a stage applies: the law of motion 𝑔 that a [pullback](operations.md#pullback) or a [push-forward](operations.md#pushforward) applies, and the value aggregator 𝐺 that an [aggregation](operations.md#aggregation) applies. `compile_kernel()` answers the kernel of such an operation as a plain Python function, made from the source text that `kernel().python` holds. It answers one where the row writes its output as a function of its inputs, or states a relation with an explicit side whose function it compiles: the candidate line `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`, which stands in `methods.bl`, the methods file beside `cons.bl`, compiles to the function `𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`, whose arguments include the derivative term, while the relation with its clause remains the row's rule. A pullback or an aggregation whose row states a relation with no explicit side, such as the identification `c = c[>]`, is refused under the rule `kernel-target` of [Refusals](refusals.md). The function takes the kernel's arguments and then the parameters the kernel reads, and computes on numbers or on NumPy arrays. The values the [calibration](../../wiki/calibration.md) gives those parameters stand in `kernel().parameter_values`, `None` on a version not yet calibrated, and are passed at each call, so that a new calibration needs no new compilation. The text holds numbers and infinity, the kernel's arguments, the parameters, the arithmetic of §2, and the functions the stage file defines in closed form, such as `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)`, written as functions inside the one function. An expectation over a label shock, a shock whose law gives each label of a finite set its probability, compiles to the sum of the values weighted by those probabilities.

The named functions `exp`, `log`, `max`, `min` and `Inv`, and a function the stage file defines by a derivative or an inverse, such as `𝑑𝑢 := D_{c}(𝑢)`, have no compile rule: their definitions state what they denote, and a kernel that calls one is not compiled, under the rule `kernel-form` of [Refusals](refusals.md). The same function written in closed form, `𝑑𝑢(c : ℝ₊₊) := c^(-ρ)`, compiles. The other operations, among them an expectation that stands as an operation of its own, whatever the law of its shock, and a maximization, have no compiled kernel: `compile_kernel()` refuses them under the rule `kernel-target`.

## 4 The blocks of a methods file

A **methods file** is the addition beside a stage file, `methods.bl`, a `.bl` file that opens with `@methods:` and the stage's name and that the package reads together with the stage file ([Methodization](../04-methodization.md)). It is written in the forms of this page: it may define functions in closed form, `𝑑𝑢(c : ℝ₊₊) := c^(-ρ)`, whose kernels compile as a stage file's do (§3); it may define a derived parameter, such as the marginal propensity to consume `κ := 1 - q` in the methods file of `applications/consumption-perfect-foresight-crra/`, which `stage.par` lists once the file is read with the stage file ([Symbol conventions](symbols-conventions.md) §8); and it declares the settings it reads in the form of a parameter's declaration, `n_a : ℕ :: ["number of points of the savings grid"]`. Its blocks name blocks of the stage file by their ids, `[id=policy, …]`, and are written as a stage file's blocks are ([Stages](../01-stage.md)), with two differences: the bracket holds typing entries, `method : !egm`, `grid : !Cartesian(a=(a_min, a_max, n_a))`, `handler : "cons-port:egm"` and, in groups opened by `|`, the entries of the operators inside the block, `evaluate.method : !Linear`; and a block that adds no coordinate to the stage's block carries no signature. The lines of such a block are appended to the stage block's lines:

| Written | Reading |
|---|---|
| `[id=policy, method : !egm \| grid : !Cartesian(a=(a_min, a_max, n_a))] { … }` | A block whose method is a solution method that brings lines: its lines are those by which the policy builder is computed, and they stand in place of the stage file's maximization at the operative level while the stage keeps the maximization as the declared line ([Methodization](../04-methodization.md) §5). A line may read the derivative of a value by the term `D_{a}V[>]`. |
| `[id=cntn_to_dcsn] { D_{m}V = 𝑑𝑢(c) :: [id=marginal] }` | A block that adds derivative lines to a value builder's block, each stating a derivative of the value the builder writes as the author asserts it. The line is recorded at the builder's Evaluation as a stated derivative, beside the representation typed there; the builder gains no wire and no box, and its signature is unchanged. |

An entry for a block to which the file adds no line is written at file level with the full path of its place, `cntn_to_dcsn.evaluate.method : !Linear`, since a block with an empty body is refused. A block whose id the stage file lacks is kept as a new block of the stage, written with its full signature. A line id written in both files and a component written twice with different content are refused under `declared-twice`, a coordinate typed differently in the two files under `type-conflict`, and a second definition of a field in a block whose method component holds no solution method under `defined-once` ([Refusals](refusals.md)). The demonstration's methods file is `applications/portfolio-choice/declaration/stages/cons/methods.bl`, quoted on [Methods and places](../API/stage/07-methods.md) §2.
