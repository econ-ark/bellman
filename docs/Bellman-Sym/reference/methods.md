---
title: Method types
tags:
  - docs/reference
  - catalogue
  - methodization
audience: user
type: reference
---

# Method types

> [!summary]
> A **method type** is a numerical method that a methods file can type at a place of a stage, such as `!egm` or `!gauss_hermite`, and a **grid constructor** is a word that writes the grid of a place, such as `!Cartesian`. This page holds one entry for each method type the package admits, registered representation families included, and one for each grid constructor: what it is, how a methods file declares it and where, its arguments, what it is compatible with, an example, whether a numerical implementation is identified, and its links. The entries are printed from the records the package's checks read, so that an entry and the checks cannot differ, and an entry that names a word absent from them is refused.

> [!info]- Relationship with other documents
> **Builds on** — [Methodization](../04-methodization.md): how a methods file types a method, a grid and a handler at a place of a stage and declares its settings.
> **Formal account** — [Methods](../../bellman-calculus/06-Methods.md): the method and the grid as components of an operator's signature; [Operators](../../bellman-calculus/catalogues/operators.md): the operations the methods realize.
> **See also** — [Expression forms](forms.md): the forms a stage file writes, among them the operators `E`, `argmax` and `solve` at which a method may be typed; [Refusals](refusals.md): the rules `method-admission`, `method-setting-declared`, `component-typed-twice`, `grid-coordinate`, `grid-setting-declared`, `grid-bounds` and `method-option-value`; the wiki entries [methods](../../wiki/methods.md) and [grid](../../wiki/grid.md).

<a id="1-reading-the-table"></a>

## 1 Reading an entry

Each entry has the same parts in the same order.

- **Declaration** is the entry a methods file writes, `<place>.method : !word` or `<place>.grid : !Word(…)`, with the places at which it may stand. The place is written as [Methodization](../04-methodization.md) §2 writes it, in the bracket of the block that holds the operator or at file level with the full path. A word with a hyphen, `!gauss-hermite`, is written in a methods file with an underscore, `!gauss_hermite`, and the package reads the two as one word. The kinds of place are those `stage.places()` prints ([Methods and places](../API/stage/07-methods.md) §1): a whole [builder](../../wiki/builder.md), named by the id of its [block](symbols-conventions.md#5-equations-and-nodes); a line marked `!node` or any other line with an id, named `<block id>.<line id>`; a defined function; and the occurrences of an operator, named by its head in one line, in a block or in the whole stage. The head `evaluate` names the [Evaluation](operations.md#evaluation) that closes a builder, `cntn_to_dcsn.evaluate`, and each object it stores, `cntn_to_dcsn.evaluate[V]`.
- **Type parameters** index the type, such as the domain X of a grid; the place supplies each one, and none is a keyword a methods file writes.
- **Arguments** are the keyword arguments the package reads, each with the kind of value it takes, what leaving it out means, its restrictions and its meaning. A number that a keyword takes is written as the name of a declared setting, so that the number stands in the settings file, and an entry that writes the number itself is refused ([Methodization](../04-methodization.md) §3.1). A keyword the entry does not list is admitted and kept for the [handler](../../wiki/handler.md) that carries the method out, which reads it or refuses it.
- **Compatibility** names the grid or the data the method reads, the conditions configuration checks once the settings have values, and the obligations listed before numerical use; `stage.obligations()` lists a method's condition, and the package does not check it.
- **Example** is a small declaration with its meaning.
- **Availability** states the language's admission and, separately, whether a numerical implementation is identified. Admission alone establishes no numerical support.
- **Links** give the formal definition, the section of [Appendix E.3](../../bellman-calculus/catalogues/operators.md) that defines the object the method realizes where its places name an operator, the related entries, and the location of the definition in the package with its public link, or the statement that no exported revision holds it yet.

An entry that names a word absent from the records is refused (`syntax`), and so is a word typed at a place of a kind its entry does not admit (`method-admission`), one component written twice with different content (`declared-twice`) or typed at one place by two paths (`component-typed-twice`), and a typing of the derivative operator `D` (`no-method-for-derivative`). Configuration checks the values: a keyword's value outside the set its entry names is refused under `method-option-value`, and a grid's bounds out of order, outside the declared set or with a count below two under `grid-bounds` ([Refusals](refusals.md)). A method's entry that writes a number among its arguments is refused under `method-setting-declared`. A factor that writes a number, or names a setting no methods file declares, is refused under `grid-setting-declared`, and a factor keyed by a name that is no coordinate of the function at the place, or a grid written at a place whose method reads none, under `grid-coordinate`. A place without a grid entry, and a coordinate that no factor names, take the default, the product over the states of the perch the method's entry names, with no number supplied.

> [!note] Grids and the model's sets
> A grid is a numerical object, the finite set of points at which a function is computed and between which it is interpolated. Changing it changes the approximation and leaves the model as it was. A finite set of alternatives the household chooses from is part of the model and is declared in the stage file, and the scalars that define it are parameters.

<!-- reference-table -->

<a id="2-the-table"></a>

## 2 The methods

Each method stands at the places this index names; the entries follow it in the order of the method table.

| site | methods |
|---|---|
| operator `E` | [`!gauss-hermite`](#gauss-hermite), [`!quadrature`](#quadrature), [`!exact`](#exact), [`!exact-markov`](#exact-markov), [`!markov`](#markov), [`!markov-expectation`](#markov-expectation), [`!sum`](#sum), [`!tauchen`](#tauchen), [`!monte-carlo`](#monte-carlo) |
| operator `argmax` | [`!egm`](#egm), [`!max`](#max), [`!discrete-choice`](#discrete-choice), [`!golden_section`](#golden-section), [`!scipy-bounded`](#scipy-bounded), [`!root-find`](#root-find) |
| operator `evaluate` | [`!Linear`](#linear), [`!pchip`](#pchip), [`!closed-form`](#closed-form) |
| operator `solve` | [`!time-iteration`](#time-iteration), [`!root-find`](#root-find), [`!newton`](#newton), [`!analytic-inverse`](#analytic-inverse) |
| operator `upper_env` | [`!FUES`](#fues) |
| a defined function | [`!Linear`](#linear), [`!pchip`](#pchip), [`!closed-form`](#closed-form), [`!analytic-inverse`](#analytic-inverse) |
| a line marked `!node` | [`!time-iteration`](#time-iteration), [`!Linear`](#linear), [`!pchip`](#pchip), [`!closed-form`](#closed-form), [`!analytic-inverse`](#analytic-inverse), [`!FUES`](#fues) |
| a line with an id | [`!Linear`](#linear), [`!pchip`](#pchip), [`!closed-form`](#closed-form) |
| a whole builder | [`!egm`](#egm), [`!vfi`](#vfi), [`!time-iteration`](#time-iteration), [`!explicit`](#explicit), [`!deterministic`](#deterministic), [`!histogram`](#histogram), [`!identity`](#identity), [`!monte-carlo`](#monte-carlo), [`!max`](#max), [`!discrete-choice`](#discrete-choice) |

<a id="egm"></a>

### 2.1 `!egm`

In the endogenous grid method, the lines of the method's block invert the first-order condition on a grid of end-of-period savings to give the policy pairs, each a choice and the decision state at which it is chosen.

**Declaration.** `<place>.method : !egm`, at a whole builder and an occurrence of the operator `argmax`.

**Type parameters.** `X` is inferred from the attachment site. It is the set of states on which the method's grid lies; the place and the method's row determine it. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** Its grid lies on the states of the continuation perch; the grid constructors its place admits are [`!Cartesian`](#cartesian) and [`!Points`](#points). The obligation `egm-eligibility` states that the construction satisfies the declared line where the continuation value 𝑉≻ is concave and continuously differentiable above the savings bound, with a positive right derivative at the bound, finite or infinite; an infinite derivative gives zero consumption as the interpolation endpoint, outside a strictly positive consumption domain. Its grid lies on the continuation states, written by the builder's grid entry or taken as the default product over those states. Its block's lines stand in place of the declared lines at the operative level. A representation at the builder's closing Evaluation reads the pairs it selects and takes no grid there. A block of explicit formulas that reads no value input is refused, naming `!explicit`. The condition `egm-eligibility` is listed among the obligations and checked by nothing.

**Example.**

```text
policy.method : !egm
policy.grid : !Cartesian(a=(a_min, a_max, n_a))
```

The policy builder is solved by the endogenous grid method on `n_a` evenly spaced savings from `a_min` to `a_max`.

**Availability.** Admission: a row of the method table, admitted at a whole builder and an occurrence of the operator `argmax`. Numerical implementation: Application handlers realize it, such as `cons-port:egm` of the consumption-portfolio application and `asva:make_egm_1d` of the asva package; the package itself solves nothing.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#9-the-two-levels-of-a-stage); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!explicit`](#explicit), [`!time-iteration`](#time-iteration), [`!vfi`](#vfi) and [`!Linear`](#linear); source `stage/method_rows.py`, `ROWS_BEFORE`, line 236; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"egm"`.

<a id="vfi"></a>

### 2.2 `!vfi`

In value function iteration, the value of a backward builder is updated by maximizing over the control at each point of its grid, given the continuation value.

**Declaration.** `<place>.method : !vfi`, at a whole builder.

**Type parameters.** `X` is inferred from the attachment site. It is the set of states on which the method's grid lies; the place and the method's row determine it. A type parameter is no source keyword.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `tol` | positive real | Optional: when it is left out, the numerical handler chooses. | none | The tolerance at which the iteration of the value stops. |
| `n_c` | positive integer | Optional: when it is left out, the numerical handler chooses. | none | The number of candidate levels of the control the search compares at each point of the grid. |

A keyword the record does not list is retained for the numerical handler.

**Compatibility.** Its grid lies on the states of the perch at which the function the place holds stands; the grid constructors its place admits are [`!Cartesian`](#cartesian), [`!Points`](#points) and [`!Fibred`](#fibred). Its grid lies on the states of the builder's output perch and may write a feasible factor for the control it searches over; where no grid is written the default product over those states stands. The values of `tol` and `n_c` are checked at configuration.

**Example.**

```text
cntn_to_dcsn.method : !vfi(n_c=n_c)
```

The decision value builder is solved by value function iteration, comparing `n_c` candidate levels of the control at each point.

**Availability.** Admission: a row of the method table, admitted at a whole builder. Numerical implementation: Application handlers realize it, such as `cons-port:share_search`; the package itself solves nothing.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); related entries [`!egm`](#egm), [`!time-iteration`](#time-iteration) and [`!max`](#max); source `stage/method_rows.py`, `ROWS_BEFORE`, line 277; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"vfi"`.

<a id="time-iteration"></a>

### 2.3 `!time-iteration`

In time iteration, the policy is updated by solving, at each point of its grid, the first-order condition the method's lines write, which reads the derivative of the continuation value.

**Declaration.** `<place>.method : !time_iteration`, at a whole builder, a line marked `!node` and an occurrence of the operator `solve`.

**Type parameters.** `X` is inferred from the attachment site. It is the set of states on which the method's grid lies; the place and the method's row determine it. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** Its grid lies on the states of the perch at which the function the place holds stands; the grid constructors its place admits are [`!Cartesian`](#cartesian), [`!Points`](#points) and [`!Fibred`](#fibred). Its grid lies on the states of the output perch, or takes the default product over them. On a builder its block's lines stand in place of the declared lines. A block of explicit formulas that reads no value input is refused, naming `!explicit`.

**Example.**

```text
policy.method : !time_iteration
```

The policy builder is solved by time iteration on the first-order condition its appended lines state.

**Availability.** Admission: a row of the method table, admitted at a whole builder, a line marked `!node` and an occurrence of the operator `solve`. Numerical implementation: Application handlers realize it, such as `cons-port:share_search`; the package itself solves nothing.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#9-the-two-levels-of-a-stage); denotes [E.3 §7 Implicit and auxiliary operations](../../bellman-calculus/catalogues/operators.md#implicit-and-auxiliary-operators); related entries [`!egm`](#egm), [`!explicit`](#explicit) and [`!root-find`](#root-find); source `stage/method_rows.py`, `ROWS_BEFORE`, line 326; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"time-iteration"`.

<a id="explicit"></a>

### 2.4 `!explicit`

In the explicit solution of a policy or backward value builder, the lines of the method's block define every output by an authored expression of the states of the output perch, the parameters and earlier local names.

**Declaration.** `<place>.method : !explicit`, at a whole builder.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method admits the policy builder and backward value builders and refuses a forward builder and a grid. Each line defines one name by `name = expression`, reads no value input or its derivative, states no relation, applies no `argmax`, `solve` or `upper_env`, and defines or reads no field at another perch; every output has such a line and a compiled kernel. The declared optimization problem stays at the declared level. The builder's Evaluation takes the closed form generated from this entry unless an entry names another representation there.

**Example.**

```text
[id=policy, policy.method : !explicit] {
    c = (1 - (R*β)^(1/ρ)/R)*(m - 1 + 1/(1 - Γ/R))    :: [id=consumption]
}
```

Consumption is the authored expression of resources and the parameters, which stands in place of the declared maximization when the stage is solved.

**Availability.** Admission: a row of the method table, admitted at a whole builder. Numerical implementation: The compiled kernels of the block's lines evaluate the solution; compiling establishes an evaluator and no optimality.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#9-the-two-levels-of-a-stage); related entries [`!closed-form`](#closed-form), [`!egm`](#egm) and [`!time-iteration`](#time-iteration); source `stage/method_rows.py`, `ROWS_BEFORE`, line 364; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"explicit"`.

<a id="linear"></a>

### 2.5 `!Linear`

The family represents a function on one real coordinate by continuous piecewise linear interpolation through strictly increasing nodes and the values aligned with them.

**Declaration.** `<place>.method : !Linear`, at a line marked `!node`, a line with an id, a defined function and an occurrence of the operator `evaluate`.

**Type parameters.** `X` is inferred from the attachment site. It is the domain of the represented function, whose coordinates are those of the place in their declared order. `Y` is inferred from the attachment site. It is the set of the represented function's values. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** Its grid lies on the states of the perch at which the function the place holds stands; the grid constructors its place admits are [`!Cartesian`](#cartesian), [`!Points`](#points) and [`!Fibred`](#fibred). The derivatives it evaluates are the first derivative, piecewise constant between its nodes and so a step function, which an inverse Euler step that reads it turns into a step candidate; the second derivative is zero and is not offered. The family reads an authored table `evaluate(knots, values, x)`, the policy pairs `!egm` selects at the closing Evaluation of its builder, where a grid is refused, or its own nodes on the grid of its place, the default product over the function's coordinates where no grid is written. An optional grid beside a table discretizes the coordinates at which the table is evaluated, written as a name or as a tuple of names in the order of the grid's coordinates, and has exactly the table's finite support, compared at configuration where both are given exactly and otherwise before numerical preparation. Numerical use needs at least two finite strictly increasing nodes with aligned finite values, and an identified extension outside the node interval.

**Stored data.** The values at the nodes, aligned with the nodes in increasing order.

**Example.**

```text
cntn_to_dcsn.evaluate.method : !Linear
cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_min, m_max, n_m))
```

The decision value is represented by linear interpolation between its values at `n_m` evenly spaced points of cash on hand from `m_min` to `m_max`.

**Availability.** Admission: a registered representation family; registration alone establishes no numerical support, admitted at a line marked `!node`, a line with an id, a defined function and an occurrence of the operator `evaluate`. Numerical implementation: The scalar evaluator `consumption-perfect-foresight-crra:Linear`, the class `Linear` of the perfect-foresight application's module `code/closed_form_check.py`, evaluates it and its first derivative and refuses a point outside the node interval; the package itself supplies no evaluator.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!pchip`](#pchip), [`!closed-form`](#closed-form) and [`!egm`](#egm); source `stage/representations.py`, `register`, line 643; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"Linear"`.

<a id="pchip"></a>

### 2.6 `!pchip`

The family represents a function on one real coordinate by piecewise cubic Hermite interpolation, with the shape-preserving slopes of PCHIP, through strictly increasing nodes and the values aligned with them.

**Declaration.** `<place>.method : !pchip`, at a line marked `!node`, a line with an id, a defined function and an occurrence of the operator `evaluate`.

**Type parameters.** `X` is inferred from the attachment site. It is the domain of the represented function, whose coordinates are those of the place in their declared order. `Y` is inferred from the attachment site. It is the set of the represented function's values. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** Its grid lies on the states of the perch at which the function the place holds stands; the grid constructors its place admits are [`!Cartesian`](#cartesian), [`!Points`](#points) and [`!Fibred`](#fibred). The derivatives it evaluates are the first derivative, continuous across its nodes, and the second derivative between its nodes, which may jump at a node. The family reads the same data as `!Linear`: an authored table, the policy pairs of an `!egm` builder's closing Evaluation, where a grid is refused, or its own nodes on the grid of its place. Numerical use needs at least two finite strictly increasing nodes with aligned finite values; evaluation outside the node interval is refused.

**Stored data.** The values at the nodes, aligned with the nodes in increasing order.

**Example.**

```text
dcsn_to_arvl.evaluate.method : !pchip
dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))
```

The arrival value is represented by the shape-preserving cubic between its values at `n_k` evenly spaced points of assets from `k_min` to `k_max`.

**Availability.** Admission: a registered representation family; registration alone establishes no numerical support, admitted at a line marked `!node`, a line with an id, a defined function and an occurrence of the operator `evaluate`. Numerical implementation: The scalar evaluator `consumption-perfect-foresight-crra:Pchip`, the class `Pchip` of the perfect-foresight application's module `code/closed_form_check.py`, evaluates it and its first and second derivatives with the slopes that SciPy's `PchipInterpolator` defines and refuses a point outside the node interval; the package itself supplies no evaluator.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!Linear`](#linear) and [`!closed-form`](#closed-form); source `stage/representations.py`, `register`, line 696; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"pchip"`.

<a id="closed-form"></a>

### 2.7 `!closed-form`

The family represents a function by its complete authored expression, evaluated through the compiled kernel of that expression at the calibration.

**Declaration.** `<place>.method : !closed_form`, at a line marked `!node`, a line with an id, a defined function and an occurrence of the operator `evaluate`.

**Type parameters.** `X` is inferred from the attachment site. It is the domain of the represented function, whose coordinates are those of the place in their declared order. `Y` is inferred from the attachment site. It is the set of the represented function's values. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The derivatives it evaluates are no derivative of its own: a derivative is offered only where an authored expression or an identified evaluator states it, and nothing is differentiated automatically. The family reads a complete authored expression with an explicit kernel: the lines of an `!explicit` builder at its closing Evaluation, where it stands by default, or the expression of a line, a `!node` line or a declared function. It refuses a representation grid, a table and the pairs of `!egm`. The expression owes its stated conditions on the domain where the function is evaluated.

**Stored data.** The authored expression, with its parameters read at the calibration.

**Example.**

```text
policy.evaluate.method : !closed_form
```

The consumption function is read from the expression the lines of the `!explicit` policy builder write, with no grid and no fitted data.

**Availability.** Admission: a registered representation family; registration alone establishes no numerical support, admitted at a line marked `!node`, a line with an id, a defined function and an occurrence of the operator `evaluate`. Numerical implementation: The compiled kernel of the authored expression, `compile_kernel()` of the row that holds it, evaluates the function; no other procedure is needed.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!explicit`](#explicit), [`!Linear`](#linear) and [`!pchip`](#pchip); source `stage/representations.py`, `register`, line 744; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"closed-form"`.

<a id="gauss-hermite"></a>

### 2.8 `!gauss-hermite`

In Gauss-Hermite quadrature, the expectation over normally or lognormally distributed shocks is approximated by weighted values at quadrature nodes.

**Declaration.** `<place>.method : !gauss_hermite`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `n_<shock>` | positive integer | Required: an entry that leaves it out is refused. | none | The number of quadrature nodes for the shock named after `n_`, one keyword for each shock the expectation at the place integrates. |

A keyword the record does not list is retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation and takes no grid. It requires one node count `n_<shock>` for each shock the expectation integrates, a positive integer checked at configuration; a point mass of a mixture is carried exactly.

**Example.**

```text
E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)
```

The expectation over the shocks ψ and ξ uses `n_ψ_nodes` and `n_ξ_nodes` quadrature nodes.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: Application handlers realize it, such as `cons-port:gauss_hermite`; the package computes no nodes or weights.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!quadrature`](#quadrature) and [`!monte-carlo`](#monte-carlo); source `stage/method_rows.py`, `ROWS_AFTER`, line 415; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"gauss-hermite"`.

<a id="quadrature"></a>

### 2.9 `!quadrature`

In a quadrature rule for an expectation, the integral is approximated by weighted values of the integrand, by a rule the method does not name.

**Declaration.** `<place>.method : !quadrature`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation and takes no grid; the handler identifies the rule and its nodes.

**Example.**

```text
E_y.method : !quadrature
```

The expectation over the shock y is computed by a quadrature rule.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!gauss-hermite`](#gauss-hermite); source `stage/method_rows.py`, `ROWS_AFTER`, line 444; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"quadrature"`.

<a id="exact"></a>

### 2.10 `!exact`

The method evaluates an expectation exactly where the law of the shocks allows it and names no further numerical rule.

**Declaration.** `<place>.method : !exact`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation and takes no grid.

**Example.**

```text
E_y.method : !exact
```

The expectation over the shock y is evaluated exactly.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!sum`](#sum) and [`!exact-markov`](#exact-markov); source `stage/method_rows.py`, `ROWS_AFTER`, line 466; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"exact"`.

<a id="exact-markov"></a>

### 2.11 `!exact-markov`

The method computes the expectation exactly under the declared Markov transition probabilities of the shocks.

**Declaration.** `<place>.method : !exact_markov`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation and takes no grid.

**Example.**

```text
E_z.method : !exact_markov
```

The expectation over the Markov state z sums its transition probabilities exactly.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!markov`](#markov) and [`!markov-expectation`](#markov-expectation); source `stage/method_rows.py`, `ROWS_AFTER`, line 483; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"exact-markov"`.

<a id="markov"></a>

### 2.12 `!markov`

The method computes the expectation under a Markov law of the shocks and names no further numerical rule.

**Declaration.** `<place>.method : !markov`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation and takes no grid.

**Example.**

```text
E_z.method : !markov
```

The expectation over the Markov state z uses its Markov law.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!exact-markov`](#exact-markov) and [`!markov-expectation`](#markov-expectation); source `stage/method_rows.py`, `ROWS_AFTER`, line 503; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"markov"`.

<a id="markov-expectation"></a>

### 2.13 `!markov-expectation`

The method computes the expectation under a Markov law of the shocks and names no further numerical rule; its word is distinct from `!markov`, with the same admission.

**Declaration.** `<place>.method : !markov_expectation`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation and takes no grid.

**Example.**

```text
E_z.method : !markov_expectation
```

The expectation over the Markov state z uses its Markov law.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!markov`](#markov) and [`!exact-markov`](#exact-markov); source `stage/method_rows.py`, `ROWS_AFTER`, line 520; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"markov-expectation"`.

<a id="sum"></a>

### 2.14 `!sum`

The method computes the expectation as the probability-weighted sum over the points of a finite law of the shocks.

**Declaration.** `<place>.method : !sum`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation over shocks with a finite law and takes no grid.

**Example.**

```text
E_d.method : !sum
```

The expectation over the discrete shock d sums its values weighted by their probabilities.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!exact`](#exact); source `stage/method_rows.py`, `ROWS_AFTER`, line 538; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"sum"`.

<a id="tauchen"></a>

### 2.15 `!tauchen`

In Tauchen's method, a Gaussian autoregressive law of a shock is approximated by a finite-state Markov chain.

**Declaration.** `<place>.method : !tauchen`, at an occurrence of the operator `E`.

**Type parameters.** `Z` is inferred from the attachment site. It stands for the shocks that the expectation at the place integrates. A type parameter is no source keyword.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `n_states` | positive integer | Optional: when it is left out, the numerical handler chooses. | none | The number of states of the approximating Markov chain. |
| `n_income_states` | positive integer | Optional: when it is left out, the numerical handler chooses. | none | The number of states of the chain of the income process, where the handler reads it apart from `n_states`. |
| `n_std` | positive real | Optional: when it is left out, the numerical handler chooses. | none | The number of standard deviations the states of the chain span on each side of the mean. |
| `min_prob` | positive real | Optional: when it is left out, the numerical handler chooses. | none | The smallest transition probability the chain keeps. |

A keyword the record does not list is retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an expectation and takes no grid; the values of its keywords are checked at configuration.

**Example.**

```text
E_ε.method : !tauchen(n_states=n_ε)
```

The expectation over the autoregressive shock ε uses a Markov chain of `n_ε` states.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!markov`](#markov); source `stage/method_rows.py`, `ROWS_AFTER`, line 561; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"tauchen"`.

<a id="deterministic"></a>

### 2.16 `!deterministic`

The method pushes a measure forward through the law of motion of a forward builder without sampling and names no further numerical rule.

**Declaration.** `<place>.method : !deterministic`, at a whole builder.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a builder and takes no grid.

**Example.**

```text
arvl_to_dcsn.method : !deterministic
```

The measure of the arrival states is pushed forward through the law of motion to the decision states.

**Availability.** Admission: a row of the method table, admitted at a whole builder. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); related entries [`!histogram`](#histogram) and [`!monte-carlo`](#monte-carlo); source `stage/method_rows.py`, `ROWS_AFTER`, line 615; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"deterministic"`.

<a id="histogram"></a>

### 2.17 `!histogram`

The method represents a measure by its masses on a grid of the states of the forward builder's output perch.

**Declaration.** `<place>.method : !histogram`, at a whole builder.

**Type parameters.** `X` is inferred from the attachment site. It is the set of states on which the method's grid lies; the place and the method's row determine it. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** Its grid lies on the states of the perch at which the function the place holds stands; the grid constructors its place admits are [`!Cartesian`](#cartesian), [`!Points`](#points) and [`!Fibred`](#fibred). The method stands at a builder; its grid lies on the states of the builder's output perch, or takes the default product over them.

**Example.**

```text
arvl_to_dcsn.method : !histogram
arvl_to_dcsn.grid : !Cartesian(m=(m_min, m_max, n_m))
```

The measure of the decision states is kept as masses on `n_m` evenly spaced points from `m_min` to `m_max`.

**Availability.** Admission: a row of the method table, admitted at a whole builder. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain); related entries [`!deterministic`](#deterministic) and [`!monte-carlo`](#monte-carlo); source `stage/method_rows.py`, `ROWS_AFTER`, line 635; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"histogram"`.

<a id="identity"></a>

### 2.18 `!identity`

The method `!identity` computes a forward measure and names no further numerical rule; the word is distinct from the identity label of an unassigned component.

**Declaration.** `<place>.method : !identity`, at a whole builder.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a builder and takes no grid.

**Example.**

```text
arvl_to_dcsn.method : !identity
```

The forward builder's measure is computed by the method `!identity`.

**Availability.** Admission: a row of the method table, admitted at a whole builder. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); related entries [`!deterministic`](#deterministic); source `stage/method_rows.py`, `ROWS_AFTER`, line 663; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"identity"`.

<a id="monte-carlo"></a>

### 2.19 `!monte-carlo`

In the Monte Carlo method, random draws approximate an expectation, or simulate the forward outcomes of a builder.

**Declaration.** `<place>.method : !monte_carlo`, at a whole builder and an occurrence of the operator `E`.

**Type parameters.** None.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `n_paths` | positive integer | Required: an entry that leaves it out is refused. | none | The number of simulated draws or paths. |
| `seed` | seed | Optional: when it is left out, the numerical handler chooses. | none | The seed of the random number generator, a nonnegative integer. |

A keyword the record does not list is retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a builder or an expectation and takes no grid. It requires `n_paths`; the values of its keywords are checked at configuration.

**Example.**

```text
dcsn_to_cntn.method : !monte_carlo(n_paths=n_paths)
```

The forward builder's measure is simulated by `n_paths` random paths.

**Availability.** Admission: a row of the method table, admitted at a whole builder and an occurrence of the operator `E`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!deterministic`](#deterministic) and [`!gauss-hermite`](#gauss-hermite); source `stage/method_rows.py`, `ROWS_AFTER`, line 683; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"monte-carlo"`.

<a id="max"></a>

### 2.20 `!max`

The method selects maximizing controls and names no search rule.

**Declaration.** `<place>.method : !max`, at a whole builder and an occurrence of the operator `argmax`.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a builder or an `argmax` and takes no grid.

**Example.**

```text
policy.method : !max
```

The policy is the maximizing control the handler selects.

**Availability.** Admission: a row of the method table, admitted at a whole builder and an occurrence of the operator `argmax`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!discrete-choice`](#discrete-choice), [`!golden_section`](#golden-section) and [`!vfi`](#vfi); source `stage/method_rows.py`, `ROWS_AFTER`, line 716; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"max"`.

<a id="discrete-choice"></a>

### 2.21 `!discrete-choice`

The method compares discrete alternatives to select the maximizing one and names no further rule.

**Declaration.** `<place>.method : !discrete_choice`, at a whole builder and an occurrence of the operator `argmax`.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a builder or an `argmax` and takes no grid.

**Example.**

```text
policy.method : !discrete_choice
```

The policy selects the alternative of highest value.

**Availability.** Admission: a row of the method table, admitted at a whole builder and an occurrence of the operator `argmax`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!max`](#max); source `stage/method_rows.py`, `ROWS_AFTER`, line 729; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"discrete-choice"`.

<a id="golden-section"></a>

### 2.22 `!golden_section`

The method is golden-section search for a scalar maximum on an interval.

**Declaration.** `<place>.method : !golden_section`, at an occurrence of the operator `argmax`.

**Type parameters.** None.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `n_sections` | positive integer | Optional: when it is left out, the numerical handler chooses. | none | The number of golden-section steps of the search. |

A keyword the record does not list is retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an `argmax` and takes no grid; the value of `n_sections` is checked at configuration.

**Example.**

```text
policy.argmax.method : !golden_section(n_sections=n_sections)
```

The maximization over the control narrows its interval by `n_sections` golden-section steps.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `argmax`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!scipy-bounded`](#scipy-bounded) and [`!max`](#max); source `stage/method_rows.py`, `ROWS_AFTER`, line 745; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"golden_section"`.

<a id="scipy-bounded"></a>

### 2.23 `!scipy-bounded`

The method is a bounded scalar search for a maximum within finite bounds, as SciPy's bounded `minimize_scalar` performs it.

**Declaration.** `<place>.method : !scipy_bounded`, at an occurrence of the operator `argmax`.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at an `argmax` and takes no grid.

**Example.**

```text
policy.argmax.method : !scipy_bounded
```

The maximization over the control is a bounded scalar search between the bounds of its feasible set.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `argmax`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §4 Constituent operations](../../bellman-calculus/catalogues/operators.md#primitive-operators); related entries [`!golden_section`](#golden-section) and [`!max`](#max); source `stage/method_rows.py`, `ROWS_AFTER`, line 771; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"scipy-bounded"`.

<a id="root-find"></a>

### 2.24 `!root-find`

The method finds a root of the residual equations a `solve` or a first-order condition writes, at each point of a grid of the output perch's states, and names no particular algorithm.

**Declaration.** `<place>.method : !root_find`, at an occurrence of the operator `solve` and an occurrence of the operator `argmax`.

**Type parameters.** `X` is inferred from the attachment site. It is the set of states on which the method's grid lies; the place and the method's row determine it. A type parameter is no source keyword.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** Its grid lies on the states of the perch at which the function the place holds stands; the grid constructors its place admits are [`!Cartesian`](#cartesian), [`!Points`](#points) and [`!Fibred`](#fibred). The method stands at a `solve` or an `argmax`; its grid lies on the states of the output perch, or takes the default product over them.

**Example.**

```text
policy.solve.method : !root_find
```

The residual equations of the policy's `solve` are solved by a root finder at each point of the default grid.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `solve` and an occurrence of the operator `argmax`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §7 Implicit and auxiliary operations](../../bellman-calculus/catalogues/operators.md#implicit-and-auxiliary-operators); related entries [`!newton`](#newton) and [`!time-iteration`](#time-iteration); source `stage/method_rows.py`, `ROWS_AFTER`, line 792; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"root-find"`.

<a id="newton"></a>

### 2.25 `!newton`

In Newton's method, the residual equations of a `solve` are solved by successive local linear approximations.

**Declaration.** `<place>.method : !newton`, at an occurrence of the operator `solve`.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a `solve` and takes no grid.

**Example.**

```text
policy.solve.method : !newton
```

The residual equations of the policy's `solve` are solved by Newton's method.

**Availability.** Admission: a row of the method table, admitted at an occurrence of the operator `solve`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §7 Implicit and auxiliary operations](../../bellman-calculus/catalogues/operators.md#implicit-and-auxiliary-operators); related entries [`!root-find`](#root-find); source `stage/method_rows.py`, `ROWS_AFTER`, line 817; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"newton"`.

<a id="analytic-inverse"></a>

### 2.26 `!analytic-inverse`

The method uses an analytic inverse to solve a defining equation at a `!node` line, a declared function or a `solve`.

**Declaration.** `<place>.method : !analytic_inverse`, at a line marked `!node`, a defined function and an occurrence of the operator `solve`.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a `!node` line, a declared function or a `solve` and takes no grid.

**Example.**

```text
𝑑𝑢𝑖𝑛𝑣.method : !analytic_inverse
```

The inverse of the marginal utility, declared as `Inv(𝑑𝑢)`, is evaluated by its analytic inverse.

**Availability.** Admission: a row of the method table, admitted at a line marked `!node`, a defined function and an occurrence of the operator `solve`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §7 Implicit and auxiliary operations](../../bellman-calculus/catalogues/operators.md#implicit-and-auxiliary-operators); related entries [`!newton`](#newton); source `stage/method_rows.py`, `ROWS_AFTER`, line 835; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"analytic-inverse"`.

<a id="fues"></a>

### 2.27 `!FUES`

In the fast upper-envelope scan, competing policy candidates are scanned to construct their upper value envelope.

**Declaration.** `<place>.method : !FUES`, at a line marked `!node` and an occurrence of the operator `upper_env`.

**Type parameters.** None.

**Arguments.** No registered arguments; unlisted keywords are retained for the numerical handler.

**Compatibility.** It reads no grid. The method stands at a `!node` line or an `upper_env` and takes no grid.

**Example.**

```text
policy.upper_env.method : !FUES
```

The upper envelope of the policy's candidates is constructed by the fast upper-envelope scan.

**Availability.** Admission: a row of the method table, admitted at a line marked `!node` and an occurrence of the operator `upper_env`. Numerical implementation: No numerical implementation is identified: the package solves nothing, and the handler a methods file names realizes the method.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator); denotes [E.3 §6 Branch values and envelopes](../../bellman-calculus/catalogues/operators.md#branching-operators); related entries [`!egm`](#egm); source `stage/method_rows.py`, `ROWS_AFTER`, line 857; public link unavailable until an exported revision holds the definition; read from `stage/method_table.py`, `METHOD_TYPES`, `"FUES"`.

## 3 The grid

A method that reads a grid takes it from the grid entry of its place, `<place>.grid : !Cartesian(…)`, a typing beside the method's. The language admits these grid constructors:

| constructor | declaration |
|---|---|
| [`!Cartesian`](#cartesian) | `<place>.grid : !Cartesian(<coordinate>=<factor form>, …)` |
| [`!Points`](#points) | `<place>.grid : !Points(nodes=<declared points>)`<br>`<place>.grid : !Points` |
| [`!Fibred`](#fibred) | `<place>.grid : !Fibred(base=<!Points or !Cartesian term>, fibre=!Cartesian(<control>=(<feasible set>, <count>), …))` |

Each constructor may end with `require=`, one predicate word or a tuple of them, a condition on the resulting grid:

| predicate | meaning |
|---|---|
| `!Empty` | The grid holds no point. |
| `!Cartesian` | The grid is nonempty and holds every combination of its projected coordinate values. |
| `!NonCartesian` | The grid is nonempty and misses some combination of its projected coordinate values. |
| `!UniformCartesian` | The grid is Cartesian on at least one real coordinate, with at least two distinct, equally spaced values in every coordinate. |

<a id="cartesian"></a>

### 3.1 `!Cartesian`

The product of one finite node set per coordinate of the place, holding every combination of the coordinates' nodes.

**Declaration.** `<place>.grid : !Cartesian(<coordinate>=<factor form>, …)`; at the grid of [`!egm`](#egm), [`!vfi`](#vfi), [`!time-iteration`](#time-iteration), [`!Linear`](#linear), [`!pchip`](#pchip), [`!histogram`](#histogram) and [`!root-find`](#root-find), and at a place whose entries name no method word, for its handler. Each factor names a coordinate of the place, a control of the stage for a feasible-control factor or a shock for an expectation factor. The predicate words of `require` are written last.

**Type parameters.** `X` is inferred from the attachment site. It is the domain of the grid, whose coordinates are those of the function the place holds, in their declared order, or the continuation states for !egm. A type parameter is no source keyword.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `<coordinate>` | factor | Optional: when it is left out, no value is supplied and the core records none. | names a coordinate of the place, a control of the stage for a feasible-control factor or a shock for an expectation factor; written in one of the four factor forms; at least one factor is written, and a coordinate no factor names keeps its obligation | At most one factor per coordinate, keyed by the coordinate's name. |
| `require` | predicate words | Optional: when it is left out, no value is supplied and the core records none. | one of !Empty, !Cartesian, !NonCartesian and !UniformCartesian, or a tuple of them, of which no two contradict each other | The properties the resulting grid satisfies, decided at configuration where the bound values decide them and established before numerical use; inside the fibre of !Fibred they concern each fibre. |

**Factor forms.** Each factor takes one of these forms:

| form | meaning | parts |
|---|---|---|
| `a=(a_min, a_max, n_a)` | Equally spaced nodes from the lower bound to the upper bound, both included; with a spacing word written as a fourth item, `a=(a_min, a_max, n_a, !expmult)`, the nodes that word's handler places between the bounds. | `lower`: setting, Required: an entry that leaves it out is refused.<br>`upper`: setting, Required: an entry that leaves it out is refused.<br>`count`: setting, Required: an entry that leaves it out is refused.<br>`spacing`: spacing word, Optional: when it is left out, no value is supplied and the core records none. |
| `m=M_nodes` | The listed nodes, in their order. | `nodes`: node set, Required: an entry that leaves it out is refused. |
| `ν=E_ν` | The quadrature nodes of the expectation operator that integrates the shock coordinate. | `nodes`: expectation operator, Required: an entry that leaves it out is refused. |
| `c=(Γ_c, n_c)` | A grid of the control's feasible set at each state, a family of grids indexed by the states; `!Fibred` pairs it with the states of a base to make one joint grid. | `set`: feasible set, Required: an entry that leaves it out is refused.<br>`count`: setting, Required: an entry that leaves it out is refused. |

**Compatibility.** Stands at the grid of a representation, of a solution method on the states of its output perch, of !egm on the continuation states, and of a place with no method word for its handler. Bounds, counts and listed nodes are settings; configuration checks the bounds in order and inside the coordinate's declared set, each count at least two, listed nodes strictly increasing, and the requirements the bound values decide. A coordinate no factor names keeps its obligation, which numerical construction reports before the grid is used.

**Example.**

```text
policy.grid : !Cartesian(a=(a_min, a_max, n_a), require=!UniformCartesian)
```

The grid of savings of !egm: n_a equally spaced points from a_min to a_max, both included, required to be uniform, which the construction establishes.

**Availability.** Admission: a grid constructor of the language, admitted by the lowering and the grid checks. Numerical implementation: The core constructs equally spaced and listed nodes at the configured settings, which a builder's `kernels().grids` holds. A spacing word is retained for its handler, of which the cons-port application implements the argument-free !expmult, and quadrature nodes come from the expectation's handler.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain); related entries [`!Points`](#points) and [`!Fibred`](#fibred); source `stage/grids.py`, `_DEFINED`, line 369; public link unavailable until an exported revision holds the definition; read from `stage/grids.py`, `GRID_CONSTRUCTORS`, `"Cartesian"`.

<a id="points"></a>

### 3.2 `!Points`

The finite support of declared points of the place's domain, each point given in the domain's declared coordinate order; !Points alone is the empty grid.

**Declaration.** `<place>.grid : !Points(nodes=<declared points>)`<br>`<place>.grid : !Points`; at the grid of [`!egm`](#egm), [`!vfi`](#vfi), [`!time-iteration`](#time-iteration), [`!Linear`](#linear), [`!pchip`](#pchip), [`!histogram`](#histogram) and [`!root-find`](#root-find), and at a place whose entries name no method word, for its handler. The points lie in the domain of the place, in its declared coordinate order. The predicate words of `require` are written last.

**Type parameters.** `X` is inferred from the attachment site. It is the domain of the grid, whose coordinates are those of the function the place holds, in their declared order, or the continuation states for !egm. A type parameter is no source keyword.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `nodes` | declared points | Optional: when it is left out, no value is supplied and the core records none. | a set the stage defines by its finite members, or a setting declared on a fixed finite product of points of the place's domain; each point has one coordinate for each coordinate of the domain, in its declared order, each a finite real inside the coordinate's declared set | The name of the declared points; when it is left out, the grid is empty. |
| `require` | predicate words | Optional: when it is left out, no value is supplied and the core records none. | one of !Empty, !Cartesian, !NonCartesian and !UniformCartesian, or a tuple of them, of which no two contradict each other | The properties the resulting grid satisfies, decided at configuration where the bound values decide them and established before numerical use; inside the fibre of !Fibred they concern each fibre. |

**Compatibility.** Stands where !Cartesian stands. The points are a set the stage defines by its finite members, or a setting declared on a fixed finite product of points, `X2 := ℝ × ℝ` and `P : X2 × X2 × X2`; configuration checks each point's shape, its finite real coordinates, its membership of the coordinates' declared sets where that is decided, and the requirements. Repeated points collapse in the support, and an interpolation procedure may still require at least two nodes.

**Example.**

```text
policy.grid : !Points(nodes=A_points)
```

The grid of savings of !egm is the set of the configured points of the setting A_points, declared `A_points : ℝ₊ × ℝ₊ × ℝ₊`: three points of the one coordinate a.

**Availability.** Admission: a grid constructor of the language, admitted by the lowering and the grid checks. Numerical implementation: The core constructs the support at the configured settings, which a builder's `kernels().grids` holds.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain); related entries [`!Cartesian`](#cartesian) and [`!Fibred`](#fibred); source `stage/grids.py`, `_DEFINED`, line 425; public link unavailable until an exported revision holds the definition; read from `stage/grids.py`, `GRID_CONSTRUCTORS`, `"Points"`.

<a id="fibred"></a>

### 3.3 `!Fibred`

Each state of a finite base paired with the finite feasible grid of the control at that state: a grid of feasible pairs of states and controls.

**Declaration.** `<place>.grid : !Fibred(base=<!Points or !Cartesian term>, fibre=!Cartesian(<control>=(<feasible set>, <count>), …))`; at the grid of [`!vfi`](#vfi), [`!time-iteration`](#time-iteration), [`!Linear`](#linear), [`!pchip`](#pchip), [`!histogram`](#histogram) and [`!root-find`](#root-find), and at a place whose entries name no method word, for its handler. The domain of the occurrence is the product of the base's states and the fibre's controls; a place of any other coordinate domain refuses. The predicate words of `require` are written last.

**Type parameters.** `X` is inferred from the attachment site. It is the set of states of the occurrence, on which the base lies. `C` is inferred from the attachment site. It is the declared set of the fibre's control; the grid lies in the graph of the control's feasible set, a subset of X × C. A type parameter is no source keyword.

**Arguments.**

| argument | type | when left out | restrictions | meaning |
|---|---|---|---|---|
| `base` | grid word | Required: an entry that leaves it out is refused. | !Points or a !Cartesian term without feasible-control factors, on the states of the occurrence; complete before numerical construction; a state no factor names keeps its obligation | The grid of the states at which the control's feasible set is sampled. |
| `fibre` | grid word | Required: an entry that leaves it out is refused. | a !Cartesian term whose factors are feasible-control factors, `c=(Γ_c, n_c)`; one control in the numerical construction; several controls or a coupled restriction report unsupported joint sampling | The grid of the control at each base state, sampled from its feasible set. |
| `require` | predicate words | Optional: when it is left out, no value is supplied and the core records none. | one of !Empty, !Cartesian, !NonCartesian and !UniformCartesian, or a tuple of them, of which no two contradict each other | The properties the resulting grid satisfies, decided at configuration where the bound values decide them and established before numerical use; inside the fibre of !Fibred they concern each fibre. |

**Compatibility.** Stands at a solution method whose grid lies on the states of its output perch; such a method chooses or solves over the place's states and the stage's controls. Fibred stands at a representation or at a place with no method word only for a function whose coordinates are the base's states followed by the fibre's controls, and a representation of a function of states alone refuses it. The base is !Points or a !Cartesian term without feasible-control factors and must be complete before numerical construction; the fibre is a !Cartesian term of feasible-control factors. An outer requirement concerns the joint grid, and a requirement inside the fibre concerns each fibre.

**Example.**

```text
cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))
```

With B = {1, 2}, Γ_c(m) = [0, m] and n_c = 2, the grid of value function iteration is the four pairs (1, 0), (1, 1), (2, 0) and (2, 2).

**Availability.** Admission: a grid constructor of the language, admitted by the lowering and the grid checks. Numerical implementation: The core constructs the case of one control: at each base state it evaluates the control's feasible interval at the arguments the stage applies it to and places the declared count of equally spaced points, both closed finite endpoints included. An open or unbounded interval reports an unresolved numerical requirement, and several controls or a coupled restriction report unsupported joint sampling.

**Links.** [formal definition](../../bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain); related entries [`!Points`](#points) and [`!Cartesian`](#cartesian); source `stage/grids.py`, `_DEFINED`, line 475; public link unavailable until an exported revision holds the definition; read from `stage/grids.py`, `GRID_CONSTRUCTORS`, `"Fibred"`.

<!-- /reference-table -->
