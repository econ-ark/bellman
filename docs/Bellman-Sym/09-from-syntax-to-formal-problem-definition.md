---
audience: user
type: user-guide
---
# From syntax to a mathematical problem

> [!summary]
> Read the income-and-consumption stage as a problem with explicit state arguments. The budget equation determines where continuation value is evaluated; the policy chooses consumption after income is observed; the arrival equation averages over income. The same reading applies when consumption is separated from discounting and investment.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](01-stage.md): the complete `buffer_stock.bl`; [Field equations](03-field-equations.md): the reusable consumption source.
> **Formal account** — [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md): rules R1–R12; [Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md): computation boundaries and indexing; [Bellman calculus](../bellman-calculus/index.md): mathematical foundations.
> **Used by** — [Semantics](../overview/05-semantics.md) and [Methodization](04-methodization.md): the constructed stage read in words, and the selection of numerical methods for its equations.

## 1 State the consumption context

Use the complete `buffer_stock.bl` in [Stages](01-stage.md#4-a-complete-stage-file). Its **fields** are quantities interpreted in declared information sets, called **perches**. We use the following state and control notation:

| Quantity | Information and domain                                                                |
| -------- | ------------------------------------------------------------------------------------- |
| $b$      | Beginning assets, observed at arrival, in $[0,\infty)$.                               |
| $y$      | Current income, drawn after arrival and observed before consumption, in $(0,\infty)$. |
| $w=Rb+y$ | Decision resources in $(0,\infty)$, with gross return $R>0$.                          |
| $c$      | Consumption chosen at decision, with $0<c\leq w$.                                     |
| $a=w-c$  | Savings available for continuation, in $[0,\infty)$.                                  |
| $W$      | Supplied continuation-value function on $[0,\infty)$.                                 |

Utility is $u(c)=c^{1-\rho}/(1-\rho)$ for $\rho>1$ and $c>0$, and $0<\beta<1$ is the discount factor. Under the example's explicit law, log income has mean $\mu_y$ and standard deviation $\sigma_y\geq0$, with a conditional distribution constant given arrival information. Write $\nu_y$ for this positive income law.

Assume resources contain the information needed for the consumption problem and savings contain the information needed for continuation value. This does not say the household forgets its earlier observations. A **representative** is a function of the declared state describing a field; the state must suffice for that representation and for the required conditional laws. Choose representatives on every feasible state where the equations or alternative controls evaluate them. Agreement almost surely under one state distribution does not fix their values at all those states ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R5–R6).

## 2 Make the state arguments explicit

The following backward block is an excerpt from the complete `buffer_stock.bl`, with its budget transition and utility definition retained:

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]            :: [id=value]
}
```

`V[>]` denotes the continuation-value field, which the function $W$ represents; holding a feasible consumption choice fixed, the field's value is $W(a)$. Substitution of the savings transition gives the **choice value**, the objective with the control still an argument:

$$
Q(w,c)=u(c)+\beta W(w-c),\qquad w>0,\quad 0<c\leq w.
$$

This is the reading of the value equation before a policy is evaluated. The control remains a decision choice even when the signature lists it alongside continuation inputs. The stage's information marks are not calendar-time subscripts.

Substitution must retain every declared output and every free or bound dependency. In particular, savings must still be determined by `a = w-c` even when `w-c` is also substituted into $W$. The local utility argument and the control bound by `argmax_{c}` have distinct scopes. [Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md#4-composition-and-substitution) gives a generic two-output example of this preservation rule. Marking the savings equation `!node` records a computation boundary without changing its budget relation; `!doc` instead removes its defining equation.

## 3 Choose consumption and average over income

The policy equation in `buffer_stock.bl` is `c = argmax_{c}(𝑢(c) + β*V[>])`. Its feasible set comes from positive consumption, nonnegative savings, and the budget equation. A **policy** is a measurable choice of consumption for each resource state. An optimal selection $\pi$ and its decision-value function $v$ satisfy

$$
\pi(w)\in\operatorname*{arg\,max}_{0<c\leq w}Q(w,c),\qquad
v(w)=Q(w,\pi(w)).
$$

For attainment, assume $W$ is finite and continuous on every compact savings interval. It is then bounded on $[0,w]$, while utility tends to minus infinity as consumption tends to zero. The maximization excludes a sufficiently small interval near zero and attains its maximum on the remaining compact interval. Select a measurable maximizer; if $W$ is concave, strict concavity of utility makes the maximizer unique. These are mathematical conditions, not conclusions of parsing `argmax`.

The arrival equation `V[<] = E_{y}(V)` averages the decision value after that policy has been selected. Substituting the resource transition gives

$$
B(b)=\int v(Rb+y)\,\nu_y(dy),\qquad b\geq0,
$$

where $B$ is arrival value. Require $\int|v(Rb+y)|\,\nu_y(dy)<\infty$. Bounded continuous $W$ is one sufficient case under the stated lognormal law, which has the required negative income moment. [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R7–R8 gives the integration and policy conditions.

The order matters: consumption responds to realized income inside the expectation. Maximizing before income were observed would describe a different decision problem. The supplied $W$ comes from an adjoining period or terminal boundary; the equation does not silently set $W=B$. Stationary closure would be an additional model assumption.

## 4 Reuse the consumption module

The separate `cons.bl` in [Field equations](03-field-equations.md#1-consumption-and-savings) begins with observed resources $m>0$, sets decision resources $m_d=m$, and uses the same savings equation. Let $H:[0,\infty)\to\mathbb R$ be its supplied continuation function. Because its value equation contains no beta, the choice value is

$$
Q_H(m_d,c)=u(c)+H(m_d-c),\qquad 0<c\leq m_d.
$$

Apply the continuity, attainment, and measurable-selection conditions above to $H$. Arrival resources are already observed, so the module evaluates its policy without taking another income expectation. When the adjoining discount and investment stages supply $H=\beta P_v$, where $P_v$ is investment value given next-period resource value $v$, discounting appears exactly once. [Periods](06-period.md#31-choosing-the-period-boundary) derives the composed problem and states the additional conditions on $P_v$.

The separate `cons_interior.bl` uses the endogenous grid method's candidate relation, described in [Field equations](03-field-equations.md#3-an-implicit-policy-relation). Its equation `c = c[>]` becomes a relation through savings, not an assignment or a guarantee of global optimality. Its inverse-marginal formula requires a finite strictly positive continuation derivative agreeing with the supplied value function. The first-order boundary criterion uses the finite right derivative at zero. To declare the full constrained policy, write the Kuhn–Tucker condition in one of its three spellings, the clause `⟂ m_d - c >= 0` on the decision-perch first-order condition using the forward law `a = m_d - c`, a multiplier declared in the policy block, or the clause `⟂ a >= 0` on the continuation-marked candidate line written as an inequality, which the loading software reads as the corner ([Constraints](10-constraints.md) §4); or restrict the equality to the interior and declare the boundary branch separately, or retain constrained maximization. A numerical boundary extension is not a solution of the unrestricted interior equality. Candidate coordinates must determine a measurable policy on the required domain. Those additional conditions do not belong to the value-only constrained source used above.

## 5 Inspect equations and then solve

A stage is inspected through the queries of the constructed object: its fields, its definitions table, its graphs, whose boxes open from whole builders down to their single operations, the conditions its construction states, and the card that `denote()` prints for any piece or definition ([API](API/index.md)). A builder's card prints each of its operations with its rule written at a point, the state arguments explicit ([A builder](API/stage/04-builder.md) §1), so the functions of §§2 and 3 are read from the constructed stage itself. On `buffer_stock.bl`:

| Card | Rule printed | Function of §§2 and 3 |
|---|---|---|
| The decision builder, `stage.dcsn.builder.bwd.denote()` | `𝑉(w) = 𝑢(𝑐(w)) + β · 𝑉≻(𝑔≻(w, 𝑐(w)))` | $v(w)=Q(w,\pi(w))$ |
| The policy builder, `stage.dcsn.builder.policy.denote()` | `𝑐(w) ∈ argmax_{c ∈ ℝ₊₊} [𝑢(c) + β · 𝑉≻(𝑔≻(w, c))]` | the maximization of §3 |
| The arrival builder, `stage.arvl.builder.bwd.denote()` | `𝑉≺(b) = E_{y}[𝑉(𝑔≺(b, y))]` | $B(b)$ |

Here `𝑉≻` is the continuation value $W$. The two laws of motion are `𝑔≻(w, c)`, the savings $w-c$, and `𝑔≺(b, y)`, the resources $Rb+y$. The decision builder's card writes the law at the policy out where a rule reads it, `𝑉≻(𝑔≻(w, 𝑐(w)))`, the continuation value at the savings the policy leaves. The analytic conditions the construction assumes, such as the integrability of the arrival expectation, are what `stage.obligations()` returns ([The stage](API/stage/01-the-stage.md) §5); [the factory API](API/factory/index.md) states the calls that construct a stage.

Construction retains interpreted equations and definitions after discarding the temporary syntax tree. Inspection therefore needs neither a second source-string model nor an inferred policy formula based on block names.

Selecting [methods, settings, and parameters](04-methodization.md) prepares numerical calculation. Solving also requires the adjoining stages and [terminal data](07-trellis.md); neither inspecting equations nor recognizing a numerical target supplies those results. The lesson `tutorials/models/cons-port/03-solving-the-two-orders.ipynb` of the repository solves the portfolio–consumption model numerically, separately from the source-to-function derivation here.
