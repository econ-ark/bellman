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

The colon `:` introduces type information, whose components are written with `@` between them. `:=` supplies a definition. The following top-level fragment can precede the consumption blocks in [Field equations](../03-field-equations.md), replacing their corresponding declarations and utility functions:

```bl
Xm := ℝ₊₊
Xa := ℝ₊
ρ : (1, inf)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
𝑑𝑢 := D_{c}(𝑢)
𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)
```

`D_{c}` differentiates the function with respect to its argument `c`. Applied to a value field with its perch mark, `D_{a}` forms the derivative term `D_{a}V[>]`, which may also be written `D_{a}(V[>])` with the same meaning: the derivative of the value in the state coordinate `a` of the perch at which the value is read, the coordinate written without its mark. A subscript that names no state coordinate of that perch, or names a discrete coordinate, is refused. `Inv` denotes an inverse function on an appropriate domain. Here marginal utility is strictly decreasing from positive consumption onto the positive reals, because `ρ > 1`; its inverse exists on positive arguments. A chosen name such as `𝑑𝑢` has no derivative meaning by itself. Similarly, a derivative term names the derivative of a value but differentiates nothing automatically.

Typed function arguments are local names with domains; do not give them field roles or perch marks. The name a comprehension binds is local in the same way: `H := {i : ℤ | i >= 0, i <= 1}` defines the named set of the integers `i` that satisfy both conditions and declares no field `i` ([Symbol conventions](../reference/symbols-conventions.md) §9.2). Define functions at the top level. A function definition written inside a block, such as `𝑞(x : ℝ) := x^2`, is refused under the rule [`not-constructed`](../reference/refusals.md#not-constructed), whether its body is a formula or a set. The refusal asks for the definition at the top level of the file. An equation inside a block whose left side is a call, such as `𝑞(a) = a^2`, defines no function `𝑞`. In a block that states a transition, such as `transform` in §3, the package reads this line as an equation that defines `a` from itself, and it refuses the block's law of motion under [`definition-order`](../reference/refusals.md#definition-order).

A function definition whose body is a set defines a feasibility correspondence. A product body keeps its factor order, `Γ(z : ℝ₊) := [0, z] × ℝ₊`. A comprehension binds its member locally and may use equality as well as inequalities:

```bl
Γ(z : ℝ₊) := {q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z, q[3] <= z}
```

Both conditions hold together on the whole triple; `q[1]` selects its first component and `z` is the correspondence's argument. Equality is written in a comprehension only. Several sets in one type, written with `@` between them as in `β : (0,1) @ (0, R^(ρ-1))`, declare their intersection, and at most one of them is written otherwise than as an interval with brackets. Several sets are read on a top-level declaration of one name only; on a field's listing in a block header they are refused under `readable-form` ([Symbol conventions](../reference/symbols-conventions.md) §9.2). Parenthesized expression tuples remain distinct from product sets, so a body `(a, b)` still defines a numerical pair. [Constraints](../10-constraints.md#1-three-kinds-of-constraint-and-where-each-is-written) §1 explains how a maximization statement uses the feasible set.

A definition without arguments whose right side is arithmetic defines a **derived parameter**, a constant of the stage computed from its parameters. The perfect-foresight stage defines the return patience factor `q` from discounting, the return and risk aversion:

```bl
β : (0,1)
R : ℝ₊₊
ρ : (1, inf)
q : (0,1) := (β*R)^(1/ρ)/R
```

Its human wealth is a field sent backward. The closed-form methods supply a separate fixed-point formula, `h_lim`, where `Γ < R`.

The outermost form of the right side decides that a definition is a derived parameter: a number, a sign, a sum, a difference, a product, a quotient, a power, a call of `log`, `exp`, `min` or `max`, a conditional `if … then … else …`, or a name the stage defines as neither a set nor a function. Any other right side keeps its own reading. A set expression, such as `ℝ₊₊` or `Xm × Xa`, defines a named set, and `D_{c}(𝑢)`, `Inv(𝑑𝑢)` or the name of a function defines a function of the stage. No other right side is read as a definition. Elaboration refuses under the rule [`not-constructed`](../reference/refusals.md#not-constructed) a right side that is a call other than those of `log`, `exp`, `min`, `max`, `D` and `Inv`, such as `sqrt(R)`, `𝑢(R)` or the grid constructor `linspace(0, 1, 10)`; a tuple, such as `(R, Γ)`; an expectation, such as `E_{y}(y)`; or the bare name of a set the file defines, such as `Xm`. The definition of a derived parameter reads declared parameters, finite numbers and other derived parameters. It is formed by signs, sums, differences, products, quotients, powers, the calls `log` and `exp`, each of one argument, and the calls `min` and `max`, each of one argument or more, as in `min(R, Γ)`, or it is written by cases, as this section states below. Elaboration refuses, under the rule `derived-parameter` and at the definition, a derived parameter whose definition reads any other name, such as a setting, a shock, a field, a set or a function; writes `inf` elsewhere than as a whole branch of a definition by cases; calls any other function, such as `sqrt` in `h := 1/sqrt(1 - Γ/R)`; calls `log`, `exp`, `min` or `max` where the stage defines a function of that name, since in a derived parameter's definition the four are the functions of the language; writes any other form, such as an expectation; or writes a number that is not finite. A cycle among the definitions is refused under the rule `definition-order`.

Calibration supplies no value for a derived parameter, and a calibration source that names one is refused under `derived-parameter`. The value of a derived parameter is its definition evaluated at the calibration values, after the derived parameters it reads, by the rules of real arithmetic. A divisor is not zero. The argument of `log` is positive. A power with an integer exponent is defined at every base except zero, where the exponent must be positive, and a power with a noninteger exponent requires a positive base. `min` and `max` are the least and the greatest of their arguments, and every argument is evaluated and must have a value. Every operation and every call gives a finite real number, and a number that floating-point arithmetic rounds to zero from a nonzero result does not count as positive. A calibration at which a definition has no value is refused under `derived-parameter`, at that definition, with the operation that fails and the numbers it reads.

A derived parameter may be defined by cases. The right side of its definition is then a conditional, `if test then a else b`, written on one line, with or without a declared set before `:=`. The test compares two formulas by one of the relations `<`, `<=`, `=`, `>=` and `>`, of which `≤` and `≥` are second spellings of `<=` and `>=`, and its formulas read what the definition of any derived parameter reads. The two branches `a` and `b` are both written, and each is a formula, a further conditional, `inf` or `-inf`. Human wealth `h`, which is infinite where income grows at least as fast as it is discounted, and the lowest income `ξ_min` of a consumer who is unemployed with probability `p_zero`, with the income `ξ_u` in unemployment and an income of at least `θ_min` in employment, are written so:

```bl
R : ℝ₊₊
Γ : ℝ₊₊
p_zero : [0, 1)
θ_min : (0, 1]
ξ_u : ℝ₊
h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else inf
ξ_min := if p_zero = 0 then θ_min else min(ξ_u, θ_min)
```

The value is the branch the test chooses, and the other branch is not evaluated, so that the division in the definition of `h` is not made at `Γ = R`. An equality compares the two computed numbers exactly, with no tolerance. A side of a test that floating-point arithmetic rounds to zero from a nonzero result decides no comparison, and the definition then has no value. Three cases are written by a conditional in the second branch, `if Γ < R then 1 else if Γ = R then 0 else -1`.

A branch written `inf` or `-inf` gives that infinity, the one value of a derived parameter that is no finite real number. Such a branch is admitted only where the definition declares a set that holds that infinity, such as a set of extended reals that holds that infinity, `ℝ_{+∞}` for `inf`, `ℝ_{-∞}` for `-inf` and `ℝ̄` for both ([Symbol conventions](../reference/symbols-conventions.md) §9.2), or an interval closed at that infinite endpoint, `(0, inf]`. The declared set of a definition that writes none is `ℝ` ([Kinds and sorts](../../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §4), so `h := if Γ < R then 1/(1 - Γ/R) else inf` is refused under `derived-parameter` when the file is read, and so is a definition whose declared set, by its form, cannot hold the infinity, such as `ℝ₊₊` or `(0, inf)`; the refusal gives a set to write. Where the closed endpoint of the declared set is the name of a parameter or of a derived parameter, as in `(0, T]`, the file is read and calibration judges. At a calibration the value, finite or infinite, is judged against the declared set as the value of any derived parameter is, which the last paragraph of this section describes.

A declared set reads an infinite value where one of its endpoints, or a side of one of the conditions after the bar of a comprehension, as `x < h` in `{x : ℝ | x < h}`, is the bare name of the derived parameter, the name with no arithmetic. With `debt : ℝ₊ @ [0, h)`, the set of `debt` is `[0, ∞)` where `h` is `inf`, and calibration decides the membership of the value of `debt` there as it does where `h` is finite; a lower endpoint valued at `inf`, as in `(h, inf)`, leaves no number in the set. An endpoint that names a declared parameter valued at an infinity is read in the same way: with `T : ℝ̄` calibrated at `inf`, `debt : [0, T)` declares `debt` on `[0, ∞)`. In a derived parameter definition, evaluating a name valued at infinity, in a formula, in a test, in a call or as the bare name, has no value, and the calibration is refused at that definition under `derived-parameter`. A bound of a declared set that computes with such a name, such as `2*h` in `[0, 2*h)`, or `-h`, has no value either, and the calibration is refused at that bound. Inside a block, arithmetic with infinity is read where its result is determined. The rules for block equations appear in §5.

A conditional stands as the whole right side of a derived parameter definition or an equation, and as a branch of another conditional. The syntax refuses it inside arithmetic, in a function definition or in a bound of a declared set. `if`, `then` and `else` are reserved words of the language: a file that writes one of them as a name, in a declaration, a definition, a function's argument, a block's header or a formula, is refused under `syntax`, with a sentence that says the three are the words of a definition by cases and no names; a name that begins with one of them, such as `iffy`, is read. [Parameters and settings](../API/stage/06-par-and-settings.md) §1.1 shows the derived parameters in `stage.par`, and [Refusals](../reference/refusals.md#derived-parameter) states the rule.

> [!ast]- Abstract grammar: Conditional
> ```asdl
> expr += Conditional(cond test, expr then, expr otherwise)
> ```
> `test` is one relation, a `Rel` of the box Abstract grammar: Slack of [Constraints](../10-constraints.md) §3, and a relation with two bounds, `a < b < c`, is refused here. A `Conditional` stands as the whole value of a definition without arguments, the `value` of an `Assignment` or, where the definition declares a set, of a `Declaration`, and as the `then` or the `otherwise` of another `Conditional`; it can also stand as the right side of an equation. Each of `then` and `otherwise` is a formula, a `Conditional`, or `inf` or `-inf` standing alone, and an infinity is admitted only where the definition declares a set that holds it.
>
> **Keys.** `test` is the relation that chooses the branch (§2); `then` is the branch whose value the definition takes where the relation holds, and `otherwise` the branch whose value it takes where the relation fails (§2). The words `if`, `then` and `else` mark the three positions, and none of the three ASDL fields is a key to write in a file.
>
> **Head.** The word `if` after `:=`, then the test, the word `then`, the first branch, the word `else` and the second branch, on one line, before any annotation.
>
> **Denotes.** A function of the parameters: at each parameter vector, the value of the branch that the test chooses there, where the two sides of the test and the chosen branch have values ([Kinds and sorts](../../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §4).
>
> **Status.** The loading software parses the form after `:=` for a derived parameter and after `=` in a block equation. It refuses under `syntax` a file that writes `if`, `then` or `else` as a name, except as the id of a line's annotation, `:: [id=if]`, which it reads ([Appendix C](14-appendix-c-syntax-to-semantics.md) §5.3), and under `derived-parameter` an infinite branch in a definition whose declared set, by its form, cannot hold that infinity.

A derived parameter may declare the set in which its value lies, on the line of its definition, in a stage file or in a methods file. The return impatience condition of a perfect foresight consumption problem, for example, requires the return patience factor `q`, the growth factor of consumption divided by the gross interest factor, to be below one, and the declared set `(0,1)` states that condition:

```bl
β : (0,1)
ρ : (1, inf)
R : ℝ₊₊
q : (0,1) := (β*R)^(1/ρ)/R
```

The line declares one name with sets alone and no type word ([Symbol conventions](../reference/symbols-conventions.md) §9.3), and its right side is the definition of a derived parameter as above. `<-` is a second spelling of `:=`, here as in every definition. Two forms close to this one are refused. A declaration whose right side reads no name, `ρ : ℝ := 2`, is refused under `readable-form`: it gives a parameter a value, which the calibration supplies. The set written on a line of its own beside the definition, `q : (0,1)` and `q := (β*R)^(1/ρ)/R`, gives one name two meanings and is refused under `one-name-one-meaning`. The declared set of a derived parameter reads no setting, since calibration judges the derived value before any setting has a value, and a set that reads one is refused under `derived-parameter`.

Calibration first judges the value of each declared parameter against its declared set, where the declared values decide the membership. It then computes the derived values. Before it evaluates a definition, it judges each value the definition reads against that value's own declared set: a parameter whose set reads a derived parameter, as in `β : (0,1) @ (0, 1/q)`, once that derived parameter has its value, and a derived value against the set its definition declares. A value outside its set is therefore refused at its own name, and a definition that computes with it is not evaluated: with `ξ : ℝ₊ @ [0, b)`, `b := 1/p`, `s := 1 - p*ξ` and `μ := log(s)`, a value of `ξ` at or above `b` is refused at `ξ`, by the condition `ξ < b`, and not at the logarithm. The values that such a set reads are judged with the value, a set written by name being read through its definition, so that a faulty value is refused at its own name and not at a name whose set reads it: with a second parameter `ζ : (ξ, b)` and a definition that reads `ζ` alone, a value of `ξ` at or above `b` is refused at `ξ`, and not at `ζ`, which lies outside `(ξ, b)` only at the faulty `ξ`. Last, calibration judges every membership still open, so the membership of a value in a set that reads a derived parameter is decided at calibration. A bound that holds an expectation over a shock is not decided, and `stage.obligations()` lists the membership as required. A calibration at which a derived value lies outside its declared set is refused, with a sentence that names the derived parameter, its definition, the set and the values read. At `β = 0.99`, `ρ = 2` and `R = 0.9`, for example, the value of `q` is about `1.049`, and the calibration is refused. `configure` judges a setting whose declared set reads a derived parameter at the derived value ([The binding verbs](../API/stage/09-binding-verbs.md) §3).

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

A tuple of two fields and one field with a product domain are distinct declarations. `(w, c) : S` declares two fields and is read where `S` is a product with one factor for each name, written out, `(w, c) : ℝ₊ × ℝ₊`, or named, `S := ℝ₊ × ℝ₊`; each field then lies in its own factor. Any other `S` is refused. A named set that couples the two fields, `S := {p : ℝ₊ × ℝ₊ | p[1] <= p[2]}`, and a set that is not such a product, such as `ℝ₊`, are refused under `readable-form`. A comprehension is read only after `:=`, so the same comprehension written directly after the colon, `(w, c) : {p : ℝ₊ × ℝ₊ | p[1] <= p[2]}`, is refused under `syntax`. A feasibility constraint that couples two controls is written in the feasible set of the maximization statement ([Constraints](../10-constraints.md#1-three-kinds-of-constraint-and-where-each-is-written) §1). `x : ℝ × ℝ`, by contrast, declares one product-valued field. In `(w, c : ℝ₊₊)`, the domain after the colon applies to `c` alone.

In `wage_fn[age[>]][tau]`, `age[>]` is a marked continuation field used as the first key. The forward header lists that input. A forward line can read the incoming age when a backward equation computes the same stage's output age.

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

A joint distribution such as `(ε, η) ~ N((0, 0), ((1, 0.5), (0.5, 1)))` writes its mean and its covariance in the order of the shocks in the tuple, so the first entry of the mean and the first row of the covariance belong to `ε`. Each shock's set is declared on its own line, `ε : ℝ` and `η : ℝ`, before or after the law. Elaboration does not refuse a joint law whose shocks no line declares, and such a shock has no declared set. The covariance of this example is positive definite, with eigenvalues `0.5` and `1.5`. A covariance must be symmetric and positive semidefinite, so a singular covariance is read; any other is refused under `distribution-domain`, at elaboration where its entries are numbers and at calibration where they read parameters ([Shock distributions](../reference/laws.md) §3).

Separate declarations define the joint distribution as the product of the declared conditional distributions, each given its named parent shocks and the source coordinates. Two shocks declared separately with no shock argument are conditionally independent given the source state and control. A declaration that names another shock, as `Ψ ~ LogNormal(ν, σ_Ψ)` names `ν`, is conditional on that shock. Elaboration records this factorization as an assumption beside the operators. Do not combine an ordinary normal distribution of positive variance with a strictly positive domain. The package does not yet check this ([Appendix C](14-appendix-c-syntax-to-semantics.md) §5.3). Elaboration records the agreement of each law's support with the shock's declared set as the condition `law-support`, which `stage.obligations()` lists and which calibration decides for a truncated lognormal law alone ([Shock distributions](../reference/laws.md) §3).

A discretization is a method, not the model. The stage declares the process the paper states: a continuous law such as `z ~ N(μ, σ^2)`, whose second argument is the variance, or `z ~ LogNormal(μ, σ)` where the paper writes a continuous process, and a finite chain such as `(z, q) ~ MarkovChain(Π, (Z, Q), z_prev)`, with `Π` the transition probabilities, `Z` and `Q` the sets of `z` and `q`, and `z_prev` the previous state, where the paper's own process is a finite chain. Replacing a continuous first-order autoregression by a chain of a chosen number of states, by Tauchen's or Rouwenhorst's construction, approximates the distribution the stage declares; it is the choice of a numerical method, and it belongs in the methods file with the grids and the tolerances (see [Methodization](../04-methodization.md)), not in the stage. The distinction matters because the stage is the statement of the model that every method must agree with: a reader of the stage should see the paper's process, and two methods that discretize it differently should still be methods of one model.

A law can take an [incoming constant](../01-stage.md#31-fields-sent-backward), for example `y(_age) ~ LogNormal(μ_tab[_age], σ_y)`. The name `_age` is local to the law's right side. An equation on the forward edge reads the draw as `y(age)` or `y[age]`, and the forward header lists both `y` and `age`. See [Shock distributions](../reference/laws.md) for the type and scope of these arguments.

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

In expectation and maximization, the designated shock or control is **bound**, meaning local to the operator's expression; other dependencies remain free. In `D_{c}(𝑢)`, the subscript names a formal argument of the declared function: `c` identifies that argument, not an unrelated stage control with the same name. The package does not yet check this ([Appendix C](14-appendix-c-syntax-to-semantics.md) §5.3). Substitution must retain both kinds. In particular, `E_{y}(V + y)` differs from `E_{y}(V) + y` when `y` is not observed in the output context.

An implicit equation such as `c = c[>]` identifies an unknown through the declared transitions; it is not a universal assignment shorthand or a claim that a numerical root is optimal. [Field equations](../03-field-equations.md#3-an-implicit-policy-relation) gives its complete consumption context. Use that authored relation when it is the intended mathematical condition; selecting a solution method does not author missing conditions.

A block equation admits `B = if m > 0 then 1/m else 0`. The comparison selects the branch whose value is required. The dependence check includes the comparison and both branches.

A block expression may use infinity where arithmetic determines the result. For a finite `x`, `x + inf` is `inf`. For positive `p`, `inf^(-p)` is zero. Expressions such as `inf - inf` and `0*inf` have no value. An endpoint of a declared set still follows the rules of that set.

## 6 Expression and annotation checks

Write multiplication explicitly as `*` and group powers and denominators with parentheses, for example `c^(-ρ)` and `c^(1-ρ)/(1-ρ)`. Parenthesize a nested power rather than relying on an unstated associativity convention. Domain declarations use intervals such as `(0,1)` and `[0,1]`, and named sets such as `ℝ₊` and `ℝ₊₊`.

`:: [id=shift, !node]` marks the line as an authored node, a computation kept as a unit of its own. `!doc` excludes a statement from the defining equations. The combined annotation has no specified meaning. [Appendix D](15-appendix-d-node-tag-and-field-indexing.md) gives the distinction between the containing block, a marked statement, and mathematical operations inside it. On a named set defined by a comprehension, `:: [!categories household_status, newborn=0, old=1]` gives each integer member a category name; elaboration checks the marker, its entries and the set, and refuses a failed check, or the marker on any other item, under `category-codes` ([Symbol conventions](../reference/symbols-conventions.md) §9.3).

> [!note]- Technical details
> The abstract mark constructor is `Node`; the documentation annotation is represented as a text tag rather than a separate constructor.

The file inherits syntax from **dynspec**, an expression language. This ancestry does not make stage perch marks calendar dates or steady-state notation. Use `[<]`, bare or `[~]`, and `[>]` in their stage contexts, and consult [Perch tagging rules](13-perch-tagging-rules.md) before moving a field between them. Parser acceptance establishes syntax; construction checks information and types; analytic assumptions establish the functional and optimality claims.
