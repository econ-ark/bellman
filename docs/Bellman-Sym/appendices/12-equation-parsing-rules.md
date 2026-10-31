---
audience: user
type: reference
---
# Equation parsing rules

> [!summary]
> A `.bl` file contains declarations, function definitions, shock laws, and typed equation blocks. This reference explains their written forms and distinguishes parsing from the checks needed to construct a mathematical stage. Timing and information restrictions belong to [Perch tagging rules](13-perch-tagging-rules.md).

> [!info]- Relationship with other documents
> **Builds on** — [Stages](../01-stage.md): complete contexts for introductory fragments; [Field equations](../03-field-equations.md): a consumption stage.
> **Formal account** — [Appendix C](14-appendix-c-syntax-to-semantics.md): the interpretation of equations; [Appendix D](15-appendix-d-node-tag-and-field-indexing.md): nodes and collection selection.
> **See also** — [Symbol conventions](../reference/symbols-conventions.md): notation; [Operations](../reference/operations.md#argmax): the kinds of the operations a builder holds, `Argmax` among them.

## 1 Statements and blocks

Equations are written directly inside braces, as in this complete transition fragment:

```bl
@stage: arithmetic

[id=transform, (a : ℝ) : !dcsn -> (y : ℝ, q : ℝ) : !cntn] {
    y = 2 + a    :: [id=shift]
    q = 4*y      :: [id=scale]
}
```

Each equation has a left and right expression separated by `=`. The optional `:: [...]` annotation gives an identifier, a documentation string, or a supported mark. A block's header supplies its identifier and the typed sides of its inputs and outputs. Newlines separate statements; parentheses group subexpressions. Use the braced block itself, without YAML quotes or a YAML `|` indicator.

> [!ast]- Abstract grammar: Equation and annotation
> This projection uses [ASDL](../../wiki/asdl.md) constructor notation. It shows the equation alternative and the annotation structure; other statement alternatives are omitted rather than redefined.
>
> ```asdl
> stmt = Equation(expr lhs, expr rhs)
> annotation = Annotation(entry* entries)
> entry = Tag(string tag)
>       | KeyValue(identifier key, scalar value)
>       | Typer(typer t)
> ```
>
> **Keys.** `lhs` and `rhs` are expressions; `entries` preserves annotation order; `tag` is text; `key` and `value` record a named scalar; `t` is type material. `expr`, `scalar`, and `typer` are defined by the full grammar. `*` permits a list; it does not establish uniqueness or scope.
>
> **Head.** `=` separates equation expressions; `::` introduces the statement annotation.
>
> **Denotes.** An equation imposes equality in its declared context. Its explicit or implicit reading depends on its dependencies and unknowns, as [Field equations](../03-field-equations.md) explains.
>
> **Status.** Construction checks declarations, operator scope, domain agreement, and output definitions. A parsed equation is not evidence that those checks or its mathematical assumptions hold.

For example, substituting an undeclared name `missing` for `a` still has the grammatical shape of an equation. Construction must reject the unresolved reference and identify the statement and source span, the part of the source file where the error occurs. An empty body does not define an identity transition; write the identity equation explicitly.

## 2 Types and definitions

The colon `:` introduces type information; `@` combines its components. `:=` supplies a definition. The following top-level fragment can precede the consumption blocks in [Field equations](../03-field-equations.md), replacing their corresponding declarations and utility functions:

```bl
Xm := ℝ₊₊
Xa := ℝ₊
ρ : (1, inf)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
𝑑𝑢 := D_{c}(𝑢)
𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)
```

`D_{c}` differentiates the function with respect to its argument `c`. Applied to a value field with its perch mark, `D_{a}` forms the derivative term `D_{a}V[>]`, in this one spelling and never `D_{a}(V[>])`: the derivative of the value in the state coordinate `a` of the perch at which the value is read, the coordinate written without its mark. A subscript that names no state coordinate of that perch, or names a discrete coordinate, is refused. `Inv` denotes an inverse function on an appropriate domain. Here marginal utility is strictly decreasing from positive consumption onto the positive reals, because `ρ > 1`; its inverse exists on positive arguments. A chosen name such as `𝑑𝑢` has no derivative meaning by itself. Similarly, a derivative term names the derivative of a value but differentiates nothing automatically.

Typed function arguments are local names with domains; do not give them field roles or perch marks. The name a comprehension binds is local in the same way: `H := {i : ℤ | i >= 0, i <= 1}` defines the named set of the integers `i` that satisfy both conditions and declares no field `i` ([Symbol conventions](../reference/symbols-conventions.md) §9.2). Define functions at the top level. A function-like expression accepted inside a block is not by itself a supported construction rule for a complete stage.

A function definition whose body is a set defines a feasibility correspondence. A product body keeps its factor order, `Γ(z : ℝ₊) := [0, z] × ℝ₊`. A comprehension binds its member locally and may use equality as well as inequalities:

```bl
Γ(z : ℝ₊) := {q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z, q[3] <= z}
```

Both conditions hold together on the whole triple; `q[1]` selects its first component and `z` is the correspondence's argument. Equality in a comprehension does not extend the comma-separated comparison tails of parameter declarations, such as `β : ℝ₊₊, < 1`. Parenthesized expression tuples remain distinct from product sets, so a body `(a, b)` still defines a numerical pair. [Constraints](../10-constraints.md#1-three-kinds-of-constraint-and-where-each-is-written) §1 explains how a maximization statement uses the feasible set.

## 3 Functions and collections

A function uses parentheses for application. This complete transition fragment defines `𝑞` and applies it:

```bl
@stage: square

𝑞(x : ℝ) := x^2

[id=transform, (a : ℝ) : !dcsn -> (y : ℝ) : !cntn] {
    y = 𝑞(a)
}
```

The function argument `x` is bound by its definition, while `a` is a stage field. External functions require a declared type for each argument and a supplied interpretation; a parser accepting a name does not provide that function.

Ordinary square brackets select a member of a declared collection. They do not define a function's domain. This fragment instead has one product-valued input and two scalar outputs:

```bl
@stage: coordinates

[id=components, (x : ℝ × ℝ) : !dcsn -> (y : ℝ, q : ℝ) : !cntn] {
    y = x[1]
    q = x[2]
}
```

The positions are one-based. Thus `x[1]` and `x[2]` select the first and second components. A position is a whole number, so `x[2.5]` is refused. On a collection declared on a set of functions, `δ : L_J → ℝ`, the key is a name declared on its finite integer or label set, `δ[j]`, never a position; `dist[j][i]` selects by the ordered pair, the first key on the first factor. The entries may be real-valued. [Symbols and conventions](../reference/symbols-conventions.md#92-domains) gives the domain forms and the numerical compilation rules. In `q[a]`, `q` must be a declared collection and `a` an admissible selection key; the expression is not an alternative spelling of `q(a)`. For discrete choices, tuple entries are ordered by the declared branch labels; see [Branching](../05-branching.md).

A tuple of two fields and one field with a product domain are distinct declarations. `(w, c) : S` jointly constrains two fields by `S`, whereas `x : ℝ × ℝ` declares one product-valued field. In `(w, c : ℝ₊₊)`, the domain after the colon applies to `c` alone.

## 4 Shock laws

We declare a shock's domain separately from its law. This complete arrival-to-decision transition fragment uses nonnegative income, including a possible zero realization:

```bl
@stage: income

Y := ℝ₊
R : ℝ₊₊
μ_y : ℝ
σ_y : ℝ₊₊
p_zero : [0,1]

y : Y
y ~ Mixture((p_zero, 0), (1-p_zero, LogNormal(μ_y, σ_y)))

[id=resources, (b : ℝ₊, y) : !arvl -> (w : ℝ₊) : !dcsn] {
    w = y + b*R
}
```

The `~` line declares a mixture with probability `p_zero` at zero and the remaining probability on a lognormal income draw. Here `R` is the gross return on assets. In this example, `μ_y` and `σ_y` are the mean and standard deviation of the logarithm of the positive income component; the atom at zero is outside that component. Its support agrees with `Y`. The law, rather than the domain declaration alone, establishes `y` as a shock; use `y : !shck @ Y` when declaring a shock before supplying its law.

For the IID reading, the displayed law is the conditional law of the draw given earlier information, and does not vary with that information. A marginal distribution with constant parameters alone would not establish independence from earlier information. Listing `y` beside arrival inputs does not say it is observed at arrival.

A joint distribution such as `(ε, η) ~ N((0, 0), ((1, 0.5), (0.5, 1)))` must follow declarations of both real shocks and preserve their written order. The covariance is positive definite, with eigenvalues `0.5` and `1.5`.

Separate declarations define the joint distribution as the product of the declared conditional distributions, each given its named parent shocks and the source coordinates. Two shocks declared separately with no shock argument are conditionally independent given the source state and control. A declaration that names another shock, as `Ψ ~ LogNormal(ν, σ_Ψ)` names `ν`, is conditional on that shock. Elaboration records this factorization as an assumption beside the operators. Do not combine an ordinary normal distribution of positive variance with a strictly positive domain.

A discretization is a method, not the model. The stage declares the process the paper states: a continuous law such as `z ~ N(μ, σ^2)`, whose second argument is the variance, or `z ~ LogNormal(μ, σ)` where the paper writes a continuous process, and a finite chain such as `(z, q) ~ MarkovChain(Q, (Z, Q), z_prev)` where the paper's own process is a finite chain. Replacing a continuous first-order autoregression by a chain of a chosen number of states, by Tauchen's or Rouwenhorst's construction, approximates the distribution the stage declares; it is the choice of a numerical method, and it belongs in the methods file with the grids and the tolerances (see [Methodization](../04-methodization.md)), not in the stage. The distinction matters because the stage is the statement of the model that every method must agree with: a reader of the stage should see the paper's process, and two methods that discretize it differently should still be methods of one model.

## 5 Operators and binding

An **operator** acts on an expression or function, with any subscript specifying the variable over which it acts. Its parentheses delimit the expression under that operation.

| Written form | Reading and conditions |
|---|---|
| `E_{y}(V)` | Integrate over the declared shock `y`, under its relevant conditional law; the integrand must admit the expectation. |
| `E_{ε,η}(V)` | Integrate over an ordered joint law, retaining its dependence. |
| `argmax_{c}(𝑢(c) + V[>])` | The set of maximizing controls. Feasibility and attainment make it nonempty, and a policy is a measurable selection from it, which a numerical method makes; on a line not marked `!doc`, the [policy builder](../../wiki/builder.md), the operator the policy block denotes, holds an operation of the kind `Argmax` whose output is that set. |
| `D_{c}(𝑢)` | Differentiate the named function in its declared argument. |
| `D_{a}V[>]` | The derivative of the value field in the state coordinate `a` of its perch (§2). |
| `Inv(𝑑𝑢)` | Invert that function where it is one-to-one and the desired values lie in its image. |

In expectation and maximization, the designated shock or control is **bound**, meaning local to the operator's expression; other dependencies remain free. In `D_{c}(𝑢)`, `c` identifies the declared function's formal argument, not an unrelated stage control with the same name. Substitution must retain both kinds. In particular, `E_{y}(V + y)` differs from `E_{y}(V) + y` when `y` is not observed in the output context.

An implicit equation such as `c = c[>]` identifies an unknown through the declared transitions; it is not a universal assignment shorthand or a claim that a numerical root is optimal. [Field equations](../03-field-equations.md#3-an-implicit-policy-relation) gives its complete consumption context. Use that authored relation when it is the intended mathematical condition; selecting a solution method does not author missing conditions.

## 6 Expression and annotation checks

Write multiplication explicitly as `*` and group powers and denominators with parentheses, for example `c^(-ρ)` and `c^(1-ρ)/(1-ρ)`. Parenthesize a nested power rather than relying on an unstated associativity convention. Domain declarations use intervals such as `(0,1)` and `[0,1]`, and named sets such as `ℝ₊` and `ℝ₊₊`.

`:: [id=shift, !node]` marks the line as an authored node, a computation kept as a unit of its own. `!doc` excludes a statement from the defining equations. The combined annotation has no specified meaning. [Appendix D](15-appendix-d-node-tag-and-field-indexing.md) gives the distinction between the containing block, a marked statement, and mathematical operations inside it. On a named set defined by a comprehension, `:: [!categories household_status, newborn=0, old=1]` gives each integer member a category name; elaboration checks the marker, its entries and the set, and refuses a failed check, or the marker on any other item, under `category-codes` ([Symbol conventions](../reference/symbols-conventions.md) §9.3).

> [!note]- Technical details
> The abstract mark constructor is `Node`; the documentation annotation is represented as a text tag rather than a separate constructor.

The file inherits syntax from **dynspec**, an expression language. This ancestry does not make stage perch marks calendar dates or steady-state notation. Use `[<]`, bare or `[~]`, and `[>]` in their stage contexts, and consult [Perch tagging rules](13-perch-tagging-rules.md) before moving a field between them. Parser acceptance establishes syntax; construction checks information and types; analytic assumptions establish the functional and optimality claims.
