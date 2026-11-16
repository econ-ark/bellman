---
audience: user
type: user-guide
---
# Field equations

#syntax-rules

> [!summary]
> Separate consumption from income and investment so that the same consumption module can be reused. Its equations state the borrowing constraint and the optimal choice. A later variant derives interior candidates from the derivative of the continuation value and explains the additional conditions needed by the endogenous grid method.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](01-stage.md): consumption after income is observed, declarations, and information sets.
> **Used by** — [Methodization](04-methodization.md): numerical methods for authored computations; [Periods](06-period.md): joining consumption, discounting, and investment.
> **Formal account** — [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md): field and functional interpretation; [Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md): computation boundaries and indexing.

## 1 Consumption and savings

The household now enters the consumption stage with observed positive resources `m`. Resources do not change before its consumption decision, so the decision state is `m_d = m`. Consumption `c` leaves savings `a = m_d-c`, subject to $0<c\leq m_d$. A **field** is a quantity interpreted in its declared information set; the signatures place resources at arrival and decision, the control at decision, and savings at continuation.

Save the following complete source as `cons.bl`:

```bl
@stage: cons
ρ : (1, inf)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
[id=arvl_to_dcsn, (m : ℝ₊₊) : !arvl -> (m_d : ℝ₊₊) : !dcsn] {
    m_d = m
}
[id=dcsn_to_cntn, (m_d, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m_d - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{c}(𝑢(c) + V[>])
}
```

`V[>]` denotes the continuation-value field, which a supplied function $H:[0,\infty)\to\mathbb R$ of savings represents. Holding consumption fixed, the backward block denotes the **choice value**, the objective before a policy is substituted:

$$
Q(m_d,c)=u(c)+H(m_d-c).
$$

The policy block selects $\pi(m_d)\in\arg\max_{0<c\leq m_d}Q(m_d,c)$, giving optimized value $v(m_d)=Q(m_d,\pi(m_d))$. Because arrival resources already contain the information needed for this decision, arrival value equals $v(m)$.

Assume $H$ is finite and continuous on every compact savings interval and select a measurable maximizer. As in [Stages](01-stage.md#4-a-complete-stage-file), utility's limit at zero consumption gives attainment; concavity of $H$ makes the maximizer unique. This value-only source includes zero savings and requires no positive continuation derivative. A constant terminal continuation is admissible and leads to consuming all resources.

There is no discount factor in this module. When it is joined to the separate discount stage, $H$ already includes that stage's discounting. [Periods](06-period.md) supplies the discount and investment sources and explains their order. The earlier `buffer_stock.bl` combines income, consumption, and discounting in one stage; adding its discount factor again here would count it twice.

This source is a documentation variant of `applications/portfolio-choice/declaration/stages/cons/cons.bl`: it excludes zero consumption and unit risk aversion and uses the constrained maximization as its operative line, the line the block computes with ([Constraints](10-constraints.md) §3), in place of the application's candidate line with its complementary-slackness clause, which §3 reads. A numerical solution also requires [method choices, settings, and calibration](04-methodization.md), together with [continuation and terminal inputs](07-trellis.md). The source does not choose those inputs.

## 2 Equations, definitions, and dependence

The `:=` line defines utility as a function of its explicit argument. By contrast, `a = m_d - c` relates stage fields. When continuation value is represented as $H(a)$, substituting the transition gives $H(m_d-c)$, with consumption still free until the policy block selects it. This substitution uses the state-sufficiency assumptions in [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R5–R7.

An **alias** is an explicit intermediate definition that can be substituted at its uses. Substitution preserves every declared output, the domains, and every free or bound dependency. The savings equation must continue to determine the output `a` even if its right side is substituted into a value calculation. The [two-output example in Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md#4-composition-and-substitution) shows the same rule when a block promises two outputs: substituting one into the other does not delete either output.

The package checks each output after substituting the forward transition and taking account of the policy and the shocks bound by expectations. A decision field may use the control in its equation. The [representing function](01-stage.md#31-fields-sent-backward) that the backward block computes uses the control at the policy and depends on its own state coordinates. A shock still unbound at the output's perch is refused on either side of a relation.

An equation may use a formula by cases, such as `B = if m > 0 then 1/m else 0`. The comparison and both branches contribute dependencies. At a particular point the package requires only the comparison and the branch it selects. For example, the line gives 0 at `m = 0`.

The utility definition binds its argument `c`, a name local to the definition; [`argmax_{c}`](reference/forms.md#argmax) binds the control in its objective. A substitution must distinguish these scopes rather than identify variables solely by spelling. An implicit equation supplies a relation between unknowns and cannot be substituted as though it were an explicit alias.

For a maximization, the objective must match the right side of exactly one decision field after the package aligns the bound candidate with the control. Thus `𝑢(cp) + V[>]` with candidate `cp` matches `V = 𝑢(c) + V[>]` with control `c`. An absent or ambiguous match is refused under [`policy-objective`](reference/refusals.md#policy-objective). The block `cntn_to_dcsn` evaluates every other decision field at that same policy. The policy block can also state an explicit formula or an implicit relation.

A block identifier supplies an address, not a formula. The labels in §1 are descriptive conventions: typed signatures, economic roles, and equations identify what each block defines. Naming a block `policy` does not make an arbitrary equation an optimality condition.

A **marginal value** is the derivative of a value in a state coordinate of its perch. It is no field: a header lists value fields and controls alone, and a line reads the derivative where it needs it by the **derivative term** `D_{a}V[>]`, the operator `D` applied to the value field written with its perch mark, the subscript naming a state coordinate of the perch at which the value is read, written without its mark; `D_{a}D_{a}V[>]` is the second derivative. The term has this one spelling. It denotes a function of the value and no second object, so a block that reads it declares nothing about how the derivative is evaluated: that is a property of the value, fixed by the methods file of the stage that writes it ([Methodization](04-methodization.md) §5). A **derivative line** is a line of a value builder's block whose left side is a derivative term of the value the builder writes, `D_{m_d}V = 𝑑𝑢(c)` in §3. It states the author's assertion that the derivative equals the right side, which holds under the envelope conditions, and it defines no new field. Such a line stands in the stage file, as in §3, or in the methods file beside it, in a block that names the value builder's block by its id ([Methodization](04-methodization.md) §1). The package never computes a derivative: it differentiates no value function, and a derivative that no line states and no representation evaluates is not part of the stage.

## 3 An implicit policy relation

The **endogenous grid method** calculates candidate consumption at given savings and then recovers the associated resources. To derive its interior equation from §1, assume $H$ is differentiable at positive savings with finite strictly positive derivative. Differentiating the choice value with respect to consumption gives $u'(c)-H'(m_d-c)$, so an interior optimum satisfies

$$
u'(c)=H'(m_d-c),\qquad
f(a)=H'(a)^{-1/\rho},\qquad h(a)=a+f(a).
$$

Here $f(a)$ is candidate consumption and $h(a)$ its resource coordinate. The source below includes zero savings, so also assume a finite strictly positive right derivative $H'_+(0)$ and use it in $f(0)$.

For this separate interior example, copy §1's source to `cons_interior.bl` and change its metadata to `@stage: cons_interior`. Keep the utility definition and both forward-transition blocks. Replace the three blocks `cntn_to_dcsn`, `dcsn_to_arvl`, and `policy` by the following function definitions and blocks; the `argmax` policy from §1 is removed, not retained as a second policy:

```bl
𝑑𝑢(c : ℝ₊₊) := c^(-ρ)             :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)        :: [id=inv_marg_util]

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V        = 𝑢(c) + V[>]          :: [id=value]
    D_{m_d}V = 𝑑𝑢(c)                :: [id=marginal]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])      :: [id=InvEuler]
    m_d[>] = a + c[>]                :: [id=endoggrid]
    c      = c[>]                    :: [id=cons_choice]
}
```

The term `D_{a}V[>]` reads the derivative of the same continuation function $H$ supplied through `V[>]`; how that derivative is evaluated was fixed where $H$ was built, and this block declares nothing about it. The derivative line `D_{m_d}V = 𝑑𝑢(c)` states the derivative of the optimized value in cash on hand. Interpreting it so requires an optimal policy and the envelope conditions in [Appendix C, R8](appendices/14-appendix-c-syntax-to-semantics.md#r8-evaluation-and-policy), applied to consumption in §4.2 of that appendix; the stage lists the reading under `marginal-reading` and checks it against nothing. The arrival block writes no derivative line: its law between the perches is the identity, so the derivative of `V` passes through it to `V[<]`. If discounting is applied in another stage, both continuation value and its derivative must include it once.

At `ρ = 2`, marginal utility is $1/c^2$ and its inverse on positive arguments is $1/\sqrt{x}$. Their composition returns $c$ for every positive $c$. A constant continuation has derivative zero and is therefore outside this inverse-marginal example, although it is valid in §1.

The candidate fields `c[>]` and `m_d[>]` are represented by $f(a)$ and $h(a)$. Through the budget equation, the final line `c = c[>]` states the feasible relation

$$
\{(m_d,c):c=f(m_d-c),\ 0<c\leq m_d\}.
$$

A **relation** is a set of state–control pairs. This relation defines a policy only where it determines one admissible control per resource state, or a suitable measurable selection is supplied. The equation neither instructs the program to copy an array nor establishes that an arbitrary root is optimal.

Elaboration keeps this division. The two explicit lines form one operation of the policy builder, an [Aggregation](reference/operations.md#aggregation) keyed `endoggrid:Aggregation`, whose kernel, the map it applies at each saving, is $G(w, a) = (w^{-1/\rho},\ a + w^{-1/\rho})$, with $w$ the derivative of the continuation value at $a$, which the term `D_{a}V[>]` reads. `stage.dcsn.builder.policy['policy.endoggrid:Aggregation'].kernel()` answers that map, and `compile_kernel()` compiles it, since `𝑑𝑢𝑖𝑛𝑣` is defined in closed form: the derivative term is one of the function's arguments ([Expression forms](reference/forms.md) §3). The policy builder is realized by a handler ([Methodization](04-methodization.md) §3.3). The last line forms the **identification**, a [Pullback](reference/operations.md#pullback): the policy composed with the resource coordinate and equated to the candidate, $\pi(h(a)) = f(a)$, which the policy builder's card prints as `𝑐(𝑚_d≻(a)) = 𝑐≻(a)`, `𝑐` being the card's italic name for the policy. Its output is its own unknown, so it states a relation, which no query solves, and `compile_kernel()` refuses it. In `applications/portfolio-choice/declaration/stages/cons/methods.bl`, the methods file beside `cons.bl`, the first line of the block `policy` is the inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])` with the clause `⟂ a >= 0`; it forms an operation of its own, `InvEuler:Aggregation`, whose rule is the relation with its clause and whose kernel is its bound $w^{-1/\rho}$, and the values the clause admits at zero saving give the policy's corner ([Constraints](10-constraints.md) §4.3). Neither form differentiates $H$ or inverts marginal utility: the derivative is read by the term `D_{a}V[>]` and evaluated as the stage that built $H$ fixed it, and the inverse is the definition `𝑑𝑢𝑖𝑛𝑣`.

For a global optimality interpretation, assume concavity of $H$ as well as the attainment conditions in §1. At the borrowing boundary $a=0$, assume the finite right derivative $H'_+(0)$ exists. Consuming all resources is optimal when

$$
u'(m_d)\geq H'_+(0).
$$

The sign follows by differentiating with respect to savings: the derivative is $-u'(m_d-a)+H'(a)$ and must be nonpositive at the left endpoint. Interior equality alone omits the cases with strict inequality. Thus `cons_interior.bl` states a candidate relation. A declaration of the full constrained policy writes the Kuhn–Tucker condition in one of its three spellings: the clause `⟂ m_d - c >= 0` on the decision-perch first-order condition, using the forward law `a = m_d - c`, a multiplier declared in the policy block, or the clause `⟂ a >= 0` on the continuation-marked candidate line written as the inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`, as `applications/portfolio-choice/declaration/stages/cons/methods.bl`, the methods file beside `cons.bl`, writes it ([Constraints](10-constraints.md) §4). The loading software reads that clause as the corner: at zero saving the candidate takes every value up to the interior value $f(0)$, and the final line then gives consumption equal to cash on hand at every cash on hand up to $f(0)$. A declaration may instead restrict the equality to its interior domain and separately state the borrowing-boundary branch, or retain the constrained maximization in §1. If a numerical method adds a boundary segment to the interior candidates, it must report that segment as an extension outside the authored equality. Attaching [`!egm`](reference/methods.md#egm) does not declare the missing branch or establish global optimality; see [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md#45-an-implicit-statement-with-a-constrained-policy) §4.5. The resulting policy must also cover the requested resource domain.

More generally, candidate controls $U:S\to C$ and coordinates $K:S\to X$ define pairs $(K(s),U(s))$, where $S$ is the set that indexes the candidates, $C$ the control domain, and $X$ the state domain. They define one control on $K(S)$ exactly when candidates with equal coordinates have equal controls. Measurability and coverage of the desired state domain are additional conditions. [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R10 and R12 and [Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md) state these conditions without assuming every implicit relation is a function.

Interpolation may approximate candidate pairs on a numerical grid, with its interpolation and extrapolation assumptions stated. It does not add an equation to the model. An authored `evaluate(knots, values, x)` is a separate optional operation with declared arguments; choosing an endogenous-grid method creates neither that statement nor an automatic upper-envelope computation, which would compare competing candidates.

## 4 Statements and computation boundaries

In §1's `dcsn_to_cntn` block, replace the savings equation by:

```bl
a = m_d - c    :: [id=savings, !node]
```

The `!node` requests a **computation boundary**, a statement to inspect or realize as a unit. It preserves the budget equation and its output `a`. The marked statement's result is a function of its own in the constructed stage, one that the statements after it consume and that a numerical method can represent, by interpolation for instance; an unmarked intermediate quantity is substituted into the statements that use it and has no separate existence to which a method could attach. The block itself is authored, while subtraction or maximization inside an equation is a mathematical operation; nesting alone does not make it another authored `!node` place. [Methodization](04-methodization.md) describes which operations and boundaries support numerical methods.

A statement marked `!doc` contributes documentation and no defining equation. Removing an equation this way can change the model or leave an output undefined. Use the two marks separately: their combined meaning is not specified. An `id` without either mark supplies an address and changes neither the equation nor its mathematical status.

## 5 Expectations

The separate consumption module has no shock because resources are already observed. In [the income-and-consumption stage](01-stage.md#4-a-complete-stage-file), the backward equation `V[<] = E_{y}(V)` instead integrates decision value over income, conditional on arrival information. The income law is explicitly conditional and constant given earlier information; the expected value must be integrable. Income affects value through resources, so that dependence remains after the transition is substituted.

The scope of the expectation matters. `E_{y}(V + y)` integrates both terms; `E_{y}(V) + y` leaves the final shock outside the expectation. When income is unobserved at arrival, the latter cannot define arrival value. [Equation parsing rules](appendices/12-equation-parsing-rules.md) gives the function, law, and operator spellings; [Perch tagging rules](appendices/13-perch-tagging-rules.md) gives the information checks.
