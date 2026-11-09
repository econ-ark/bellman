---
audience: user
type: user-guide
---
# Constraints

> [!summary]
> A constraint on a choice is written in one of three places, according to what it is. A fixed bound is part of the control's declared set. A bound that depends on the state is a **feasibility correspondence**, a set-valued function defined at the top of the file and named in the maximization statement of the policy block. A constraint that binds at some states and not at others is written with the Kuhn–Tucker condition in one of three spellings, which denote one relation between the state and the choice under the hypotheses of §2: the complementary-slackness clause `⟂` after the first-order condition, a multiplier declared in the policy block, or the clause after the candidate line of the endogenous grid method. The candidate line written without a clause states the policy only at the states its candidates reach and nothing at the states where the constraint binds.

> [!info]- Relationship with other documents
> **Builds on** — [Field equations](03-field-equations.md) §3: the consumption stage and its inverse Euler line, the running example of this page.
> **Formal account** — [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R10, §4.5 and §4.6: the reading of the clause and of the declared multiplier, and the theorem that the three spellings denote one relation and, under concavity, one policy.
> **Used by** — [Methodization](04-methodization.md) §8: how the lines of a method such as the endogenous grid method carry a constraint's clause.
> **See also** — [A builder](API/stage/04-builder.md) §§1 and 2: the policy builder, its operations and its printed card; [Refusals](reference/refusals.md): the rules under which the loading software refuses a writing.

## 1 Three kinds of constraint and where each is written

An economic model constrains a choice in three ways, and the language, Bellman-SYM, gives each its own place.

A **fixed bound** does not depend on the state. A portfolio share lies in $[0,1]$; investment is nonnegative; a labor supply lies in $[0,1]$. Such a bound is the control's declared set, written in the signature of the block where the control is introduced, for example `ς : [0,1] @ !ctrl` or `i : ℝ₊ @ !ctrl`. Nothing further is written, because the set is the constraint. Declarations, roles such as `!ctrl` and annotations `:: [id=…]` are read as in [Stages](01-stage.md) §2, [Symbol conventions](reference/symbols-conventions.md) and [Equation parsing rules](appendices/12-equation-parsing-rules.md) §1; `[>]` marks a field at the continuation **perch**, the information set at which the quantities after the decision are known ([Stages](01-stage.md) §1).

A **state-dependent bound** is a feasibility correspondence, a function from states to sets, which the notation of the [Bellman calculus](../bellman-calculus/index.md) writes $\Gamma$. It is defined at the top of the file by a function definition whose body is a set rather than a formula, and it is named in the binder of the **maximization statement** of the **policy block**, the block of a stage that states how the control is chosen; the maximization statement names the control as a maximizer of its objective over its feasible set, and §4 states, for each spelling, whether it forms an operation. A statement marked `!doc` is a declaration: it forms no operation, and no method is attached to it. A correspondence is not written as the type of a control: controls keep plain declared sets, and the loading software reads the feasible set from the maximization statement.

In the maximization statement the binder introduces a bound variable, local to the statement, that ranges over the feasible set: `argmax_{cp : Γ(w, h)}` binds `cp` to $\Gamma(w,h)$, the feasible set at the state $(w, h)$ of §5.2, with the same colon that types a declaration. When the bound is fixed the bare binder suffices, `argmax_{i}(…)`, because the control's declared set is its feasible set.

A feasible set for a pair of jointly chosen quantities may be a product:

```bl
Γ(z : ℝ₊) := [0, z] × ℝ₊
```

The first component lies between zero and `z`, while the second is nonnegative. To couple components by a budget identity, write a set comprehension, which gives a domain and conditions on its members:

```bl
Γ(z : ℝ₊) := {q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z}
```

Here `q` is one nonnegative triple, and its first two components must sum to `z`; its third component remains nonnegative. For `z = 3`, `(1, 2, 0)` is feasible, whereas `(1, 1, 0)` violates the equality and `(1, 2, -1)` violates nonnegativity. Comma-separated conditions must all hold, so an equality may be combined with inequalities. The policy's maximization statement retains this complete feasible set for the joint choice; [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md#r7-the-operations-a-line-writes) R7 states the separate requirements for a maximizer and its numerical selection.

An **occasionally binding constraint** holds with equality at some states and with slack at others: the borrowing limit that binds at low wealth, the irreversibility of investment that binds when capital is abundant, the collateral limit that binds when house prices fall. Its first-order condition is the Kuhn–Tucker condition of §2, which the language writes in one of three spellings (§4).

A fixed bound on a parameter is written in its declaration as a comma-separated condition after the set, `β : ℝ₊₊, < 1` for a discount factor, read as the set of values of the declared name that satisfy the condition; several conditions are separated by commas, as in `x : ℝ, >= 0, <= 1`.

> [!ast]- Abstract grammar: CorrDef
> ```asdl
> stmt  += CorrDef(identifier name, coordinate* params, setexpr body)
> ```
> `params` has at least one entry, each a typed argument; `body` is an interval, a finite set, a product of sets or a set comprehension, in the arguments. A comprehension may restrict its member by equalities and inequalities. A set comprehension is admitted in one other place, after `:=` in the definition of a named set, which has no arguments, as in `H := {i : ℤ | i >= 0, i <= 1}` ([Symbol conventions](reference/symbols-conventions.md) §9.2); marked `!categories`, such a set is bounded by inequalities alone, and an equality condition is refused under `category-codes`.
>
> **Keys.** `name` is the correspondence's name, applied in a binder (§1); `params` are its typed arguments; `body` is the set it assigns to each argument value (§1).
>
> **Head.** A function-definition line, `name(arg : set, …) := body`, whose body is a set rather than a formula.
>
> **Denotes.** The feasibility correspondence $\Gamma$ of [Stages and perches](../bellman-calculus/03-Stages%20and%20perches.md) §1, a function from decision states to sets of admissible controls.
>
> **Status.** The loading software parses the definition and reads the feasible set from the binder of the maximization statement into the declared set of functions for the policy, which the policy card prints beside the policy's type as `𝑐(m_d) ∈ Γ(m_d)` (§4).

> [!ast]- Abstract grammar: In
> ```asdl
> subscript = Var(identifier name)
>           | In(identifier var, expr set)
> ```
> `var` is the bound variable; `set` is a named set or an applied correspondence.
>
> **Keys.** `var` is the name bound by the operator (§1); `set` is the set it ranges over (§1).
>
> **Head.** Inside the operator's subscript braces, `argmax_{var : set}`; the bare form `argmax_{var}` is `Var`.
>
> **Denotes.** The maximization of [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R7 over the set the binder names, with the variable local to the statement.
>
> **Status.** The loading software parses both forms and records the binder with the operator occurrence. A maximization statement marked `!doc` is printed on the policy card under the heading `Declared` with the policy substituted for the control, `𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]`, and forms no operation; written without the mark, it forms the Argmax operation that outputs the policy, and the card prints the same statement as that operation's rule (§4.1).

## 2 The Kuhn–Tucker condition

The running example is the consumption stage of [Field equations](03-field-equations.md) §3. At cash on hand $m_d > 0$ the household chooses consumption $c > 0$ and saves $a = m_d - c$, subject to the borrowing limit $a \ge 0$, to maximize $u(c) + V_\succ(a)$, where $u$ is utility and $V_\succ$ is the continuation value, the function the field `V[>]` denotes; the period's other stage, `disc`, applies the discount factor, so $V_\succ$ is already discounted and no $\beta$ appears ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §4.2). The page writes $u'$ for marginal utility, `𝑑𝑢` in the file, $(u')^{-1}$ for its inverse, `𝑑𝑢𝑖𝑛𝑣`, and $V_\succ'$ for the marginal value of saving, the derivative of the continuation value, which the derivative term `D_{a}V[>]` denotes and a card prints as `D_{a}𝑉≻`. Throughout, $u'$ is a strictly decreasing bijection of $\mathbb R_{++}$, and $V_\succ$ is differentiable on $X_a = \mathbb R_+$, from the right at zero, with derivative $V_\succ'$ valued in $\mathbb R_{++}$.

With a multiplier $\mu$ on the borrowing limit, the Kuhn–Tucker condition of Karush (1939) and Kuhn and Tucker (1951) for this problem is

$$
u'(c) - V_\succ'(m_d - c) = \mu, \qquad \mu \ge 0, \qquad m_d - c \ge 0, \qquad \mu\,(m_d - c) = 0 .
$$

The last three parts are **complementary slackness**: the multiplier and the slack $m_d - c$ of the bound are nonnegative and their product is zero, so the Euler equation holds with equality where the household saves, and marginal utility may exceed the marginal value of saving where it saves nothing. The states at which the bound binds form the **constrained region**. The **residual** $r = u'(c) - V_\succ'(m_d - c)$, the left side of the Euler equation less its right side, equals the multiplier, so the condition is

$$
r \ge 0, \qquad m_d - c \ge 0, \qquad r\,(m_d - c) = 0 ,
$$

written $0 \le r \perp m_d - c \ge 0$ in the complementarity-problem literature (§6). This is the form the language writes. Under the concavity hypotheses of [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md#45-an-implicit-statement-with-a-constrained-policy) §4.5 the condition has one solution at each $m_d$, and that solution is the maximizer.

For an upper bound $z \le b$ the slack is $b - z$, and the residual is nonpositive, zero wherever the bound is slack. For two bounds on one quantity, $lb \le z \le ub$ with $lb < ub$, each bound has a multiplier, $\mu_{lo}$ and $\mu_{hi}$, at most one of them positive, and the residual is $\mu_{lo} - \mu_{hi}$: nonnegative where the lower bound binds, zero where neither binds, and nonpositive where the upper bound binds.

## 3 The complementary-slackness clause

A statement of a block may have a clause after its equality or inequality:

```bl
    lhs = rhs ⟂ bound >= 0
```

The clause pairs the residual, the left side less the right side, with the slack of the bound, as in §2: on a lower bound `>=` the residual is nonnegative, the bound holds and their product is zero, so the equation holds wherever the bound is slack; on an upper bound `<=` the residual is nonpositive instead. The author orients the equation so that its residual has the sign its bound requires, as the examples of §5 do. After an inequality statement the residual takes the sign of that inequality, and the clause adds the bound and the zero product (§4.3). The sign is read from the relation as written, so a clause with one bound writes the bounded quantity first: `a >= 0` on a continuation-marked candidate line, or `m_d - c >= 0` on a decision-perch condition whose forward law is `a = m_d - c`. The reversed one-bound spelling `⟂ 0 <= a` is refused under `readable-form`. The glyph is ⟂ (U+27C2); ⊥ (U+22A5) is not admitted. The rules under which the loading software refuses a writing are listed in [Refusals](reference/refusals.md).

A clause names one bounded quantity. On a statement it may have two bounds, written as an ascending chain of weak inequalities, from the lower bound through the bounded quantity to the upper bound:

```bl
    lhs = rhs ⟂ lb <= x <= ub
```

The two-bound clause states the condition of §2 for two bounds. The worker's saving stage of the pension application writes one on the pension deposit $c_p$, which lies between zero and earnings $w_d$, in the block `policy` of its methods file, `applications/pension-retirement/declaration/stages/worker_saving/methods.bl`, whose two lines are the first-order conditions of the stage's maximization, brought to the policy builder under time iteration ([Methodization](04-methodization.md) §5):

```bl
    𝑑𝑢(c) = β*(1 + 𝑑𝜒(c_p))*D_{y_p}V[>] ⟂ 0 <= c_p <= w_d
```

Its residual is the stationarity condition in the deposit less that in consumption. In a system of several conditions each clause is written so that its residual is the multiplier of its own bound, the other multipliers being eliminated by combining the first-order conditions; the loading software holds the statements as written and checks no such arrangement ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R10).

The clause is written on the first-order condition (§4.1), on the declaration of a multiplier (§4.2), or on the candidate line of the endogenous grid method (§4.3). Where the maximization statement is marked `!doc` and the control enters the first-order condition only through the law of motion, as in §5.1 and §5.3, the condition names no output of the block, and a block that states the control by that condition alone is refused under the rule `output-defined`; attached as the property of the maximization statement written without `!doc`, the first spelling of §4.1, the same condition is accepted.

> [!note]- Technical details
> Where the left side of a statement is an expression rather than a name, as it is in the examples of §5.1 and §5.2, its unknowns are the outputs of the policy block that its two sides mention and that no other **operative** statement of the block defines by name, an operative statement being one the block computes with, so any line that is neither marked `!doc` nor attached to another line as its property by a dotted id (§4.1; [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R10). Where the maximization statement is marked `!doc` it is not operative, so the control it names on its left side stays an unknown of the operative statements below it; in the first spelling (§4.1) it is written without `!doc` and is itself the operation that outputs the control. Several such statements of one block that share an unknown state one system, whose unknowns are taken in the order of the block's header.

> [!ast]- Abstract grammar: Slack
> ```asdl
> stmt  += Slack(stmt core, cond bound)
> cond   = Rel(expr left, relop op, expr right)
> relop  = Lt | Le | Eq | Ge | Gt
> ```
> The statement `core` is an equality or an inequality; on an inequality the residual takes the sign of its relation. The relation `bound` is written with `>=` for a lower bound or `<=` for an upper bound (`≥` and `≤` are the same spellings); `left` is the bounded quantity and `right` the bound, an expression in the stage's declared quantities, and a `left` that is a number or `inf` alone is refused. A clause with two bounds is the `Between` of the next box.
>
> **Keys.** `core` is the equality or inequality whose residual the clause constrains (§3); `bound` is the relation the constrained quantity satisfies throughout (§3).
>
> **Head.** The glyph ⟂ between the statement and its bound, on one statement line, before any annotation.
>
> **Denotes.** The Kuhn–Tucker condition of §2 for the residual of `core` and the slack of `bound`, with the residual's sign taken from the relation of `core`; stated with its concavity hypotheses in [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §4.5.
>
> **Status.** The loading software parses the clause and keeps it with its statement. It reads the clause by the product of the residual and the slack: where the slack is positive the residual is zero, and where the slack is zero the residual has the sign the clause states; a chain has three such cases, one at each bound and one between them. This reading admits at each state exactly the values the condition of §2 admits, and nothing is solved. The card prints the clause in the rule of the operation its statement forms, read at the point, the state at which the rule holds: on a first-order condition, each function at the coordinates of its own perch and each continuation state replaced by the law of motion at the decision state and the policy, under the Argmax operation when the condition is its property and under an Aggregation of its own when the condition is an operative line (§4.1); on the candidate line, at the saving (§4.3). The statements of one system share one rule, their conjunction.

> [!ast]- Abstract grammar: Between
> ```asdl
> cond  += Between(expr lower, relop lo, expr middle, relop hi, expr upper)
> ```
> `lo` and `hi` are both `<=` (or `≤`), so the chain ascends from the lower bound through the bounded quantity to the upper bound. A descending, strict or mixed chain, a chain after an inequality statement and a chain on the declaration of a multiplier are refused.
>
> **Keys.** `lower` and `upper` are the two bounds (§3); `middle` is the bounded quantity (§3); `lo` and `hi` are the two relation signs as written (§3).
>
> **Head.** Two relation signs after the glyph ⟂, `⟂ lb <= x <= ub`, on one statement line, before any annotation.
>
> **Denotes.** With $r$ the residual of the statement, the bounds $lb \le x \le ub$ together with $r\,(x - lb) \le 0$ and $r\,(ub - x) \ge 0$: the residual is nonnegative where the lower bound binds, zero where neither binds and nonpositive where the upper bound binds, and with $lb < ub$ it is the difference of the two bounds' multipliers (§2).
>
> **Status.** The loading software parses the chain, keeps both relation signs, and prints the chain read at the point. On the card of the pension application's worker stage the chain on the deposit is printed after the clause of the first condition, whose bound prints as `y_f ≥ 0`: `y_f` is the name that the card's `Where` line gives to the financial saving in the law of motion. The refusals above are made under `readable-form`, and on a declaration under `multiplier-declaration`.

## 4 Three spellings of one condition

The **endogenous grid method** (Carroll 2006, §2.2) inverts the interior Euler equation on a grid of the continuation state, the state after the decision is taken ([Stages and perches](../bellman-calculus/03-Stages%20and%20perches.md) §1). In the running example the continuation state is the saving $a$, with declared set `Xa`, and the **law of motion** $g_\succ$, the map from the decision state and the control to the continuation state, is $a = m_d - c$. Inverting the interior Euler equation $u'(c) = V_\succ'(a)$ at each saving gives the **candidate at each saving**, which the field `c[>]` denotes, $c_\succ(a) = (u')^{-1}(V_\succ'(a))$ (Carroll's equation 17), and the budget gives the **cash on hand at each saving**, which `m_d[>]` denotes, $m_{d\succ}(a) = a + c_\succ(a)$ (his equation 18), written in the file by the **grid line** `m_d[>] = a + c[>]`; a card prints them `𝑐≻` and `𝑚_d≻`. Where the candidate line has no clause, both are functions of the saving alone ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R8); with the clause of §4.3 they are correspondences of the saving alone, `𝑐≻ : Xa ⇉ ℝ₊₊` and `𝑚_d≻ : Xa ⇉ Xm`, the double arrow marking a correspondence, each taking several values at zero saving; with the multiplier of §4.2 they are functions of the saving and the multiplier. Write $\bar m = (u')^{-1}(V_\succ'(0))$ for the interior value at zero saving. The **image** $m_{d\succ}(X_a)$ is the set of cash on hand that some saving reaches; under the hypotheses of [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §4.5 it is $[\bar m, \infty)$.

The policy block's lines are read into the **policy builder**, the operator the block denotes, whose printed **card** lists its operations under the heading `Operations`, one entry each: the entry's number and its key: the id of the line it realizes followed by its kind, as in `InvEuler:Aggregation`, or the kind alone, as in `Pullback` and `Evaluation`, for an operation that no line of the block forms; the functions it reads after `in:` and those it writes after `out:`; and its rule after `rule:`, with a note at the right margin, `on …`, naming the set on which the rule holds. Under the heading `Source` the card gives the lines of the file its operations come from ([A piece](API/stage/05-piece.md) §1). An operation of a policy builder is of one of five kinds, each a row of [Operations](reference/operations.md): a [Pullback](reference/operations.md#pullback) composes a function with a map, such as a continuation function with the law of motion; an [Aggregation](reference/operations.md#aggregation) applies a pointwise map, or holds the relation its line writes, with the unknown on both sides where the line puts it there; an [Expectation](reference/operations.md#expectation) integrates over a shock; an [Argmax](reference/operations.md#argmax) maximizes an objective over the feasible set; and the [Evaluation](reference/operations.md#evaluation) is the identity into the declared set of functions for the policy, the place at which a numerical method stores its representation of the policy. The three spellings share the header of the policy block and its maximization statement, which the second and the third mark `!doc`, as below, a declaration of what their operations are meant to reach that the operations neither confirm nor check, and which the first writes without the mark, as the operation itself (§4.1):

```bl
[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality, !doc]
    …
}
```

A stage file may instead write the maximization alone and leave the candidate lines to its methods file, whose block `policy` brings them to the policy builder under a solution method ([Methodization](04-methodization.md) §5). Such a block writes the second or the third spelling. It holds no maximization line, since the stage file's maximization stays the policy block's declared line, so the first spelling, a property of that line, has no line to attach to there; the first spelling belongs to a stage file that writes the maximization as an operation and attaches to it the first-order condition, which reads the derivative term `D_{a}V[>]`. The methods file of the portfolio–consumption demonstration, `applications/portfolio-choice/declaration/stages/cons/methods.bl`, writes the third spelling, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`.

### 4.1 The clause on the first-order condition

```bl
    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality]
    𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0          :: [id=optimality.euler]
```

The first line is the maximization statement without the mark `!doc`: it is the operation that outputs the policy, and a method is attached to it. The second line is attached to the first as its property by the dotted id `optimality.euler`: it forms no operation, and the loading software neither checks it against the objective nor derives anything from it. Its bound writes the decision-perch expression $m_d-c$ supplied by the law of motion $a = g_\succ(m_d, c) = m_d - c$, so the property states the Kuhn–Tucker condition of §2 at every cash on hand $m_d$. No candidate and no cash on hand at each saving is written, so a method attached to the Argmax operation solves the condition at each $m_d$, by a root finder in $c$ or by the endogenous grid method, which inverts the property for the candidate, as the lines of §4.3 do in the file, and forms the cash on hand by the law of motion. The card of the stage `cons_argmax`, which is `applications/portfolio-choice/declaration/stages/cons/cons.bl` with its policy block written in this way:

```text
STAGE cons_argmax / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → [−∞, ∞)
       ──────────────────────────────────────────────────────────────────────
  out  𝑐   : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Operations
  1  Pullback
     in: 𝑉≻                             out: 𝑉≻ ∘ 𝑔≻
     ────────────────────────────────────────────────────────────────────────
     rule: (𝑉≻ ∘ 𝑔≻)(m_d, c) = 𝑉≻(𝑔≻(m_d, c))

  2  optimality:Aggregation
     in: (1)                            out: (m_d, c) ↦ 𝑢(c) + 𝑉≻(𝑔≻(m_d, c))
     ────────────────────────────────────────────────────────────────────────
     rule: (m_d, c) ↦ 𝑢(c) + 𝑉≻(𝑔≻(m_d, c))

  3  optimality:Argmax
     in: (2)                            out: 𝑐
     ────────────────────────────────────────────────────────────────────────
     rule: 𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]
           optimality.euler: 𝑑𝑢(𝑐(m_d))
                               = (f
                               ↦ (c, y)
                               ↦ sup_{a ∈
                               {a ∈ ℝ |
                               ∀ epsilon ∈ (0, ∞): (∃ delta ∈ (0, ∞): (∀ t ∈
                               {t ∈ ℝ |
                               (t²)^(1/2) > 0
                               ∧ (t²)^(1/2) < delta
                               ∧ c + t ∈ ℝ₊}: ((((f(c + t, y) − f(c, y))/t
                               − a)²)^(1/2)
                               < epsilon)))}} [a])((a, unit)
                               ↦ 𝑉≻(𝑔≻(m_d, 𝑐(m_d))))(a≻, ())
                               ⟂ m_d − 𝑐(m_d) ≥ 0                        on Xm

  4  Evaluation
     in: 𝑐                              out: 𝑐
     ────────────────────────────────────────────────────────────────────────
     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)
──────────────────────────────────────────────────────────────────────────────
Source  cons_argmax.bl
  31  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality]
  32  𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0             :: [id=optimality.euler]

Definitions referenced
  Xm    cons_argmax:set:Xm
  Xa    cons_argmax:set:Xa
  𝑢     cons_argmax:function:𝑢
  𝑑𝑢    cons_argmax:function:𝑑𝑢
  Γ     cons_argmax:correspondence:Γ
  𝑔≻    cons_argmax:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The operations are those of the maximization: a Pullback of the continuation value along the law of motion, an Aggregation that forms the objective, the Argmax over the feasible set with the policy as its output, and the Evaluation. The property prints under the Argmax entry, labeled by its id and read at the point, and no `Declared` section is printed, since no line is marked `!doc`. A block may instead keep the maximization statement marked `!doc` and write the first-order condition with its clause as an operative line of its own, `𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0 :: [id=euler]`, as the pension application's worker stage writes its two conditions using its own forward laws. The condition then forms a Pullback of the derivative `D_{a}𝑉≻` along the law of motion and an Aggregation whose rule is the relation with the policy on both sides, `𝑑𝑢(𝑐(m_d)) = D_{a}𝑉≻(𝑔≻(m_d, 𝑐(m_d))) ⟂ 𝑔≻(m_d, 𝑐(m_d)) ≥ 0` on `Xm`, and a root finder is attached to that line.

### 4.2 The declared multiplier

```bl
    μ[>]   : ℝ₊ ⟂ a >= 0             :: [id=slackness]
    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>] + μ[>]) :: [id=InvEuler]
    m_d[>] = a + c[>]                :: [id=endoggrid]
    c      = c[>]                    :: [id=cons_choice]
```

The first line declares a **multiplier**: a field `μ` at the continuation perch with the declared set $\mathbb R_+$, joined by its clause to the bound `a >= 0`. It is a declaration inside the block's body and defines no equation. The second line is the inverse Euler equation with the multiplier added, $c = (u')^{-1}(V_\succ'(a) + \mu)$. For the functions the block defines at the continuation perch, the candidate and the cash on hand, the declaration adds the coordinate $\mu$ beside $a$ and restricts the pair to the **admitted pairs**, those at which complementary slackness holds:

$$
A_{\succ,\mathrm{policy}} = \{(a, \mu) \in X_a \times \mathbb R_+ \mid a \ge 0,\ \mu\, a = 0\} ,
$$

where $X_a$ is the declared set `Xa` of the saving; the half-line $a = 0$ is thus declared by the file, not inferred. On this set the candidate and the cash on hand are functions of the saving and the multiplier, $c_\succ(a, \mu) = (u')^{-1}(V_\succ'(a) + \mu)$ and $m_{d\succ}(a, \mu) = a + c_\succ(a, \mu)$, while $V_\succ$ and its derivative $V_\succ'$ remain functions of $a$ alone and the multiplier is an input or output of no block. The identification equates the policy at the cash on hand of each admitted pair with the candidate there, $c(m_{d\succ}(a, \mu)) = c_\succ(a, \mu)$ on the image $m_{d\succ}(A_{\succ,\mathrm{policy}})$. On the half-line $\mu = 0$ that image is the image $m_{d\succ}(X_a)$ of §4. On the half-line $a = 0$ the candidate $(u')^{-1}(V_\succ'(0) + \mu)$ decreases from $\bar m$ toward zero as $\mu$ grows, because $u'$ is a strictly decreasing bijection of $\mathbb R_{++}$ (§2), so the image there is $(0, \bar m]$, the constrained region. The card the package prints for the stage `cons_obs` of `applications/portfolio-choice/declaration/stages/cons_obs/cons_obs.bl`, the consumption stage with this policy block:

```text
STAGE cons_obs / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → [−∞, ∞)
       ──────────────────────────────────────────────
  out  𝑐   : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Where
  A≻,policy = {a, μ ∈ Xa × ℝ₊ | a ≥ 0 ∧ μ · a = 0}

Declared
  𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]

Operations
  1  endoggrid:Aggregation
     in: 𝑉≻                             out: 𝑐≻, 𝑚_d≻
     ────────────────────────────────────────────────
     rule: 𝑐≻
             = 𝑑𝑢𝑖𝑛𝑣((f
                       ↦ (c, y)
                         ↦ sup_{a ∈
                           {a ∈ ℝ |
                             ∀ epsilon ∈ (0, ∞): (∃ delta ∈ (0, ∞): (∀ t ∈
                               {t ∈ ℝ |
                               (t²)^(1/2) > 0
                               ∧ (t²)^(1/2) < delta
                               ∧ c + t ∈ ℝ₊}: ((((f(c + t, y) − f(c, y))/t
                               − a)²)^(1/2)
                               < epsilon)))}} [a])((a, unit) ↦ 𝑉≻(a))(a, ())
                       + μ)                              on (a, μ) ∈ A≻,policy
           𝑚_d≻ = a + 𝑐≻                                 on (a, μ) ∈ A≻,policy

  2  cons_choice:Pullback
     in: 𝑐≻, 𝑚_d≻                       out: 𝑐
     ────────────────────────────────────────────────
     rule: 𝑐(𝑚_d≻(a, μ)) = 𝑐≻(a, μ)                         on 𝑚_d≻(A≻,policy)

  3  Evaluation
     in: 𝑐                              out: 𝑐
     ────────────────────────────────────────────────
     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Conditions
  endoggrid:Aggregation  𝑐≻(a, μ) ∈ ℝ₊₊
  endoggrid:Aggregation  𝑚_d≻(a, μ) ∈ Xm
──────────────────────────────────────────────────────────────────────────────
Source  cons_obs.bl
  31  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality, !doc]
  32  μ[>]   : ℝ₊ ⟂ a >= 0                         :: [id=slackness]
  33  c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>] + μ[>])             :: [id=InvEuler]
  34  m_d[>] = a + c[>]                            :: [id=endoggrid]
  35  c      = c[>]                                :: [id=cons_choice]

Definitions referenced
  Xm     cons_obs:set:Xm
  Xa     cons_obs:set:Xa
  𝑢      cons_obs:function:𝑢
  𝑑𝑢𝑖𝑛𝑣  cons_obs:function:𝑑𝑢𝑖𝑛𝑣
  Γ      cons_obs:correspondence:Γ
  μ      cons_obs:multiplier:μ
  𝑔≻     cons_obs:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> [!note]- Technical details
> The card states the set of admitted pairs once, under the heading `Where`, as `A≻,policy`; its coordinates have no perch marks, because on a card `μ≻` names the measure of the continuation state.

The bound is held as written, even where the declared set of the continuation state already implies it: the loading software compares no bound with a declared set, and on a state declared on $\mathbb R$ the bound is the only place the constraint enters the set of admitted pairs; §5.2 writes such a bound. Because a bound may not name a control, a constraint on a control, such as the cap on the pension deposit in §3, is written with the clause on the first-order condition.

> [!ast]- Abstract grammar: Complementary
> ```asdl
> typer += Complementary(typer d, cond bound)
> ```
> `d` declares one coordinate with the continuation mark `[>]` and one set; `bound` is one relation, a `Rel` written with the bounded quantity first, and a `Between` is refused here. The item is `Declare(Complementary(d, bound), annot)`, so `Declare` keeps its two ASDL fields. The bound may name continuation states, other multipliers of the block, parameters, numbers and `inf`. A multiplier with a mark other than `[>]`, a bound naming a control, a decision or arrival state or a candidate such as `c[>]`, a second declaration of one name, a block header that lists the multiplier's name, and a declaration without its clause are refused.
>
> **Keys.** `d` is the declaration of the multiplier, its name, its perch and its set (§4.2); `bound` is the constraint whose multiplier it is (§4.2).
>
> **Head.** A declaration in the body of a policy block followed by the glyph ⟂ and one relation, `μ[>] : ℝ₊ ⟂ a >= 0`, before any annotation.
>
> **Denotes.** For the functions its block defines at the continuation perch, the coordinate $\mu$ beside the continuation states, the pair restricted to the admitted pairs $\{(a, \mu) \mid \text{bound},\ \mu\, s = 0\}$, where $s$ is the slack of the bound, $x - b$ for `x >= b` and $b - x$ for `x <= b`. The declaration forms no operation and no wire, a wire being an input or output of an operation on the card. That this spelling and the clause of §3 denote one relation is a theorem of [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §4.5.
>
> **Status.** The loading software parses the declaration, gives its name the role of a multiplier at the continuation perch, adds it to the coordinates of the functions its block defines there, forms the set of admitted pairs from the bound as written, with one bound and one product for each declaration where a block declares several (§4.5), and the identification, a Pullback, states the grid relation on the image of that set. The grid line is checked against the law of motion as in §4.3. The refusals above are made under `multiplier-declaration`, and that of a declaration without its clause under `syntax`.

### 4.3 The clause on the candidate line

```bl
    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0       :: [id=InvEuler]
    m_d[>] = a + c[>]                :: [id=endoggrid]
    c      = c[>]                    :: [id=cons_choice]
```

The first line, the **candidate line**, is the inverse Euler statement of [Field equations](03-field-equations.md) §3 with `<=` in place of `=` and the clause of §3 after it. An inequality statement defines its left side as a **correspondence**, and the clause takes the sign of its residual from the inequality (§3). A value $x$ is admitted at the saving $a$ when

$$
x - (u')^{-1}\bigl(V_\succ'(a)\bigr) \le 0, \qquad a \ge 0, \qquad \bigl(x - (u')^{-1}(V_\succ'(a))\bigr)\, a = 0 .
$$

A product is zero exactly when one of its factors is zero. Where the bound is slack, $a > 0$, the residual is therefore zero and one value is admitted, $(u')^{-1}(V_\succ'(a))$; where it binds, $a = 0$, every $x$ with $0 < x \le \bar m$ is admitted, the lower end open because consumption is declared positive. The card writes the set admitted at $a$ as `𝑐≻(a)`, so that `𝑐≻(0)` is the segment $(0, \bar m]$. The second line gives each admitted value its cash on hand, $a + x$. The third line, the identification, is a Pullback, the pullback of the policy along the cash on hand at each saving equated to the candidate; its rule is the **grid relation** `𝑐(𝑚_d≻(a)) = 𝑐≻(a)` on `𝑚_d≻(Xa)`, the candidate and the cash on hand taking their values together, so that it states $c(a + x) = x$ at every saving $a$ and every value $x$ admitted there:

$$
c(m_d) = m_d \quad \text{for } 0 < m_d \le \bar m, \qquad c\bigl(a + (u')^{-1}(V_\succ'(a))\bigr) = (u')^{-1}(V_\succ'(a)) \quad \text{for } a \ge 0 .
$$

The first part is the **corner**, the pairs at which the household consumes all its cash on hand, and the second is the interior policy on the image $m_{d\succ}(X_a)$; the two share the pair $(\bar m, \bar m)$. The corner is Carroll's segment from the origin to the first grid point (2006, §4.2.2, equation 29). The policy card of the consumption stage `cons` of `applications/portfolio-choice/declaration/stages/cons/cons.bl`, after its addition `applications/portfolio-choice/declaration/stages/cons/methods.bl` supplies these lines:

```text
STAGE cons / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → [−∞, ∞)
       ──────────────────────────────────────────
  out  𝑐   : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Declared
  𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]

Operations
  1  InvEuler:Aggregation
     in: 𝑉≻                             out: 𝑐≻
     ────────────────────────────────────────────
     rule: 𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0

  2  grid:Aggregation
     in: 𝑐≻                             out: 𝑚_d≻
     ────────────────────────────────────────────
     rule: 𝑚_d≻(a) = a + 𝑐≻(a)

  3  identification:Pullback
     in: 𝑐≻, 𝑚_d≻                       out: 𝑐
     ────────────────────────────────────────────
     rule: 𝑐(𝑚_d≻(a)) = 𝑐≻(a)                                      on 𝑚_d≻(Xa)

  4  Evaluation
     in: 𝑐                              out: 𝑐
     ────────────────────────────────────────────
     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Conditions
  grid:Aggregation  𝑚_d≻(a) ∈ Xm
  policy            egm-eligibility: the construction satisfies the declared
                      line where the continuation value 𝑉≻ is concave and
                      continuously differentiable on (0, ∞) with a finite
                      positive right derivative at 0   [required]

Method
  !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"            policy
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  30  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality]

Source  methods.bl
  29  c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0          :: [id=InvEuler]
  30  m_d[>] = a + c[>]                            :: [id=grid]
  31  c      = c[>]                                :: [id=identification]

Definitions referenced
  Xm     cons:set:Xm
  Xa     cons:set:Xa
  𝑢      cons:function:𝑢
  Γ      cons:correspondence:Γ
  𝑑𝑢𝑖𝑛𝑣  cons:function:𝑑𝑢𝑖𝑛𝑣  methods.bl:19
  𝑔≻     cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The card writes each rule at the saving; three answers beside it show the correspondences. The card of the first entry, `cons.dcsn.builder.policy["InvEuler:Aggregation"].denote()`, gives its output as `𝑐≻ : Xa ⇉ ℝ₊₊`, and the card of the second gives `𝑚_d≻ : Xa ⇉ Xm`. The query `signature()`, which answers an operation's inputs and outputs with their sets, gives as the output of the identification the set of policies $f$ with $f(a + x) = x$ for every saving $a$ and every value $x$ admitted there, the relation over the pairs each saving admits. The loading software checks the second line, the grid line, against the law of motion: it solves $a = m_d - c$ for the decision coordinate, $m_d = a + c$, puts the candidate in place of the control, and compares the result with the line. A line that does not agree, such as `m_d[>] = a + 2*c[>]`, is refused under the rule `grid-line-consistency`, and the refusal names the line as written and the law solved for the coordinate.

**Without the clause** the candidate line is read as the equality selection, $c_\succ(a) = (u')^{-1}(V_\succ'(a))$ at every saving, the part of the relation of §2 with $\mu = 0$, and is no spelling of the Kuhn–Tucker condition. The identification then states the policy on the image $m_{d\succ}(X_a)$; below it, where the constraint binds, it states nothing.

> [!ast]- Abstract grammar: Inequality
> ```asdl
> stmt  += Inequality(expr lhs, relop op, expr rhs)
> ```
> The relation `op` is `<=` or `>=` for a bound (`<` and `>` are also admitted); `lhs` names the quantity defined and `rhs` is the bound the definition admits.
>
> **Keys.** `lhs` is the quantity the statement defines as a correspondence (§4.3); `op` and `rhs` state the relation its values satisfy (§4.3).
>
> **Head.** The relation sign between two expressions on a statement line, where an equation would have `=`.
>
> **Denotes.** The set-valued relation $\{\,\text{lhs} : \text{lhs} \le \text{rhs}\,\}$ at each state, a correspondence. Written as the inverse Euler line without a clause, it is read as the equality selection, the interior candidate $(u')^{-1}(V_\succ'(a))$ at every saving, and is no spelling of the Kuhn–Tucker condition (§4.3). With a clause of one bound after it, the residual takes the sign of the relation and the clause adds the bound and the zero product: the Kuhn–Tucker condition of §2, one value at each saving where the bound is slack and, where it binds, the segment of values up to the interior value at zero saving, $\bar m$ (§4.3).
>
> **Status.** The loading software parses the statement, keeps the relation, and forms from it one Aggregation of the policy builder, whose output is the candidate at each saving and whose rule is the relation as written, read at the saving, `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a))`. With a clause of one bound the rule holds the clause as well, `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0`, the operation's record holds the values the clause admits at each saving, and the card of that operation prints its output as the correspondence `𝑐≻ : Xa ⇉ ℝ₊₊`; a clause with two bounds after the inequality is refused under `readable-form`. The identification, a Pullback, states the grid relation `𝑐(𝑚_d≻(a)) = 𝑐≻(a)` on `𝑚_d≻(Xa)`: with the clause it holds at every value admitted at each saving, the corner among them; without it the candidate is the interior value at every saving, and the relation states nothing below the image of the grid. No inverse of the cash on hand at each saving is formed.

### 4.4 One relation

Under the hypotheses of §2 and the law of motion $a = m_d - c$, the three spellings denote one relation between cash on hand and consumption: the pairs that satisfy the clause on the first-order condition, the pairs the declared multiplier reaches on its two half-lines, and the pairs of the grid relation of §4.3, corner included, are one set. The identity of the first spelling with the second uses only that `𝑑𝑢𝑖𝑛𝑣` is the inverse of $u'$; that of the third with them also uses the monotonicity of $u'$, through which $x \le \bar m$ holds exactly when $u'(x) \ge V_\succ'(0)$. For the first spelling, whose operation is the maximization and whose first-order condition is its property (§4.1), the pairs are those of the property; that the maximizer is among them, and is the only one, holds under the concavity hypotheses of [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md#45-an-implicit-statement-with-a-constrained-policy) §4.5 and not otherwise. [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md#45-an-implicit-statement-with-a-constrained-policy) §4.5 proves the identity and, under concavity hypotheses stated there, that the relation is the graph of one policy and that this policy maximizes the objective over the feasible set; the loading software checks none of these hypotheses. The spellings differ in what a method reads: the first states the condition at every decision state, for a method attached to the Argmax operation to solve; the second and the third state the candidate and the cash on hand at every saving, which the endogenous grid method, attached at the Evaluation, evaluates at the savings of its grid, joins with the pairs of the corner and interpolates as one function of cash on hand, without forming the inverse of the cash on hand at each saving ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §4.6).

### 4.5 A bound on both sides

Take a saving bounded on both sides, $0 \le a \le \bar a$, with `ā : ℝ₊₊` a declared parameter. In the first spelling the chain is written on the first-order condition, `𝑑𝑢(c) = D_{a}V[>] ⟂ 0 <= m_d - c <= ā`, using the forward law $a=m_d-c$. In the second each bound has its own multiplier, since a declaration's clause has one bound, and the two enter the inverse Euler line with the signs of §2:

```bl
    μ_lo[>] : ℝ₊ ⟂ a >= 0                    :: [id=slack_lo]
    μ_hi[>] : ℝ₊ ⟂ a <= ā                    :: [id=slack_hi]
    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>] + μ_lo[>] - μ_hi[>])  :: [id=InvEuler]
```

In the third the correct writing is the equation with the chain and the interior value on the left, `𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) = c[>] ⟂ 0 <= a <= ā`, whose residual is nonnegative at zero saving and nonpositive at the cap. The loading software refuses it under `signature-complete`, since a field is defined only by a line with its name on the left, so a bound on both sides is written in the first or the second spelling. A chain after the inequality, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ 0 <= a <= ā`, is refused under `readable-form`, because a chain has a sign rule after an equation alone.

> [!warning]
> The line `c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ 0 <= a <= ā` is accepted but states the wrong constraint. Its residual, the candidate less the interior value, has the opposite sign to the Euler residual ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §4.5), so the chain places consumption above the interior value at zero saving and below it at the cap. The loading software checks no sign.

## 5 Examples

Each example shows the transition block and the policy block; the declarations of parameters and shocks and the backward blocks of a complete stage file are omitted.

### 5.1 Irreversible investment

A firm with capital $k$ and depreciation rate $\delta$ chooses investment $i \ge 0$, and its capital next period is $k' = (1-\delta)k + i$. Investment cannot be undone, so the constraint binds when the firm would rather disinvest. The Kuhn–Tucker condition is

$$
1 - \beta\, W'(k') \ge 0, \qquad i \ge 0, \qquad \bigl(1 - \beta\, W'(k')\bigr)\, i = 0 ,
$$

where $W$ is the continuation value of capital and $\beta$ the discount factor: the firm invests until the discounted marginal value of capital equals its unit cost, unless that value is below the cost, in which case it invests nothing. The bound is fixed, so the control's declared set is the nonnegative reals, and the clause is written on the first-order condition with the unit cost on the left, which makes the residual nonnegative at the bound.

```bl
[id=dcsn_to_cntn, (k_d : ℝ₊₊, i : ℝ₊ @ !ctrl) : !dcsn -> (k_n : ℝ₊₊) : !cntn] {
    k_n = (1 - δ)*k_d + i
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (i : ℝ₊ @ !ctrl) : !dcsn] {
    i = argmax_{i}(-i + β*V[>])     :: [id=optimality, !doc]
    1 = β*D_{k_n}V[>] ⟂ i >= 0      :: [id=investment]
}
```

In the fragment `k_d` is $k$, `k_n` is $k'$, `V[>]` is $W$ and the derivative term `D_{k_n}V[>]` is $W'$. The first statement, marked `!doc`, declares the control to be a maximizer over its declared set and forms no operation. Investment enters the first-order condition only through the transition, so the condition names no output of the block, and the loading software refuses the block under `output-defined` (§3). In the first spelling of §4.1 the maximization statement is written without `!doc` and the condition is attached to it as its property, `:: [id=optimality.investment]`; the block is then accepted, the maximization forming the Argmax operation that outputs investment and the condition printing under it.

### 5.2 A collateral constraint

A household with a house of size $h$ and price $p$ consumes $c$ out of cash on hand $w$ and may borrow against the house: end-of-period net assets $a = w - c$ may be negative down to a fraction $\theta$ of the house's value. The feasible set of consumption depends on the state, so it is a correspondence,

$$
\Gamma(w, h) = \bigl(0,\; w + \theta p h\bigr] ,
$$

and the Euler equation has the collateral limit as its bound. The house is held fixed within this stage, $h' = h$.

```bl
Γ(x : ℝ₊₊, h : ℝ₊) := (0, x + θ*p*h]        :: [id=feasible]

[id=dcsn_to_cntn, (w : ℝ₊₊, h : ℝ₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ, h_n : ℝ₊) : !cntn] {
    a   = w - c
    h_n = h
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ(w, h)}(𝑢(cp) + β*V[>])   :: [id=optimality, !doc]
    𝑑𝑢(c) = β*D_{a}V[>] ⟂ w - c >= -θ*p*h       :: [id=euler]
}
```

In the fragment `h_n` is $h'$, and `𝑢` and `𝑑𝑢` are utility and marginal utility, defined as in [Field equations](03-field-equations.md) §3. The Euler clause writes `w - c` for `a` and `h` for `h_n`, as the forward block defines them. At states where the limit has slack the Euler equation holds with equality. Where it binds, the household borrows the full $\theta p h$, consumption is $w + \theta p h$, and marginal utility exceeds the discounted marginal value of assets by the multiplier on the collateral constraint. The bound is an expression in declared quantities; a constant limit `w - c >= 0` is the special case $\theta = 0$.

### 5.3 A portfolio share with two bounds

A household allocates a share $\varsigma \in [0,1]$ of its savings $s$ to a risky asset with gross return $\Psi$, the rest earning the safe gross return $R$, and receives income $\eta$; next period's resources are $m' = s\,(\varsigma\Psi + (1-\varsigma)R) + \eta$. Both bounds are fixed, so the control's declared set states them, and with $W$ the continuation value of resources the first-order condition, divided by the positive savings $s$, holds with equality only in the interior:

$$
\mathbb{E}\bigl[W'(m')\,(\Psi - R)\bigr]
\begin{cases}
\le 0 & \text{if } \varsigma = 0, \\
= 0 & \text{if } 0 < \varsigma < 1, \\
\ge 0 & \text{if } \varsigma = 1 .
\end{cases}
$$

The two-bound clause of §3 states this condition exactly. Written with zero on the left and the expectation on the right,

```bl
    0 = E_{Ψ,η}(D_{m}V[>]*(Ψ - R)) ⟂ 0 <= ς <= 1
```

the statement has the residual $-\mathbb E\bigl[W'(m')\,(\Psi - R)\bigr]$, which is nonnegative where the share is zero, zero in the interior and nonpositive where the share is one, as the display requires; written the other way round, it would have the opposite sign at each bound. The share enters the condition only through the transition, so a block that states the share by this line alone is refused under `output-defined` (§3). The block therefore writes the interior first-order condition with `solve_{ς}`, which names its unknown, and the declared set `[0,1]` states the two bounds; the maximization statement, marked `!doc`, declares the share to be a maximizer over that set and forms no operation:

```bl
[id=dcsn_to_cntn, (s : ℝ₊₊, ς : [0,1] @ !ctrl, Ψ, η) : !dcsn -> (m : ℝ₊₊) : !cntn] {
    m = s*(ς*Ψ + (1-ς)*R) + η
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (ς : [0,1] @ !ctrl) : !dcsn] {
    ς = argmax_{ς}(E_{Ψ,η}(V[>]))              :: [id=optimality, !doc]
    ς = solve_{ς}(E_{Ψ,η}(D_{m}V[>]*(Ψ - R)))   :: [id=foc]
}
```

In the fragment `s` is the savings allocated, `m` is $m'$, the derivative term `D_{m}V[>]` is $W'$, and `E_{Ψ,η}` is the expectation $\mathbb{E}$ over the declared distribution of the shocks, under which $W'(m')\,(\Psi - R)$ is assumed integrable. The `solve_{ς}` statement determines the share as a root of the residual in its argument ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R8) and states nothing at a corner. A method that solves the first-order condition must check both corners before accepting an interior root; the declared set is what tells it where the corners are. In the first spelling of §4.1 the two-bound line above is instead attached as its property to the maximization statement written without `!doc`, `:: [id=optimality.foc]`, and the block is accepted, the condition with both corners printing under the Argmax operation.

## 6 Notation in the literature

The Kuhn–Tucker conditions with complementary slackness are stated in the standard texts on constrained optimization: Nocedal and Wright (2006, Theorem 12.1), whose condition (12.34e) is named the complementarity condition, and Boyd and Vandenberghe (2004, §5.5.2–5.5.3). The perpendicular sign for a pair of inequalities with a zero product is the notation of the complementarity-problem literature: Ferris and Pang (1997, §2.1) write the problem as $0 \le x \perp F(x) \ge 0$ and explain the sign as adding the equation $x^{\mathsf T} F(x) = 0$ to the stated inequalities; Cottle, Pang and Stone (1992) treat the linear problem in the form of the three conditions, and Facchinei and Pang (2003) the general theory. In economics, Brumm and Grill (2014, §2.1) write the borrowing constraint of their equilibrium conditions as $0 \le b - \underline{b} \perp \mu \ge 0$ with the sign denoting orthogonality.

The notation entered computational economics through the complementarity formulation of equilibrium (Mathiesen 1985), the GAMS and PATH software (Rutherford 1995; Dirkse and Ferris 1995), and the toolkits for models with occasionally binding constraints. Dynare up to version 6 attaches the bound to an equation with the `mcp` tag; from version 7 it writes the bound after the equation separated by ⟂ (U+27C2, or `_|_`), with the residual positive at a lower bound, zero between the bounds, and negative at an upper bound, the convention of §3 (Dynare Team 2026, §4.12). Dolo writes an arbitrage equation as `rhs-lhs ⟂ lb <= x <= ub` and states the same sign at a binding lower bound (EconForge 2024).

In dynamic programming the same condition is usually written without the sign. Ljungqvist and Sargent (2018, §17.5 and §18.5.2) write the Euler equation of a household with a borrowing constraint as an inequality that holds with equality when savings are positive; Christiano and Fisher (2000) and Guerrieri and Iacoviello (2015) state the Kuhn–Tucker conditions of the investment constraint in equilibrium models, and Swarbrick (2021, §2) reviews the solution methods; Maliar, Maliar and Winant (2021, §4.1) rewrite the Kuhn–Tucker conditions of the constrained consumption problem as a single equation for solution by a neural network. Carroll (2006, §2.2) inverts the first-order condition on an exogenous grid of end-of-period assets, his equations 17 and 18 being the candidate and the cash on hand at each saving of §4, and handles the borrowing constraint by the segment from the origin to the first grid point (§4.2.2, equations 28 and 29); Hintermaier and Koeniger (2010) extend the method to occasionally binding constraints among endogenous variables. Dobrescu and Shanker (2024) define the inverse Euler problem on the **observables**, the post-decision states joined with the Kuhn–Tucker multipliers (§2.1, Definition 1; an observable is not a quantity the agent observes), pair the first-order condition with complementary slackness (§3, conditions (3) and (4)), index the pieces of the exogenous grid by the set of binding constraints (§4.1, equation (5)), give the invertibility results in §4.2 (Claim 4.1, Theorem 4.1 and Claim 4.2), and lay a piece out in any variables in one-to-one correspondence with its observables (§4.3); the one-dimensional case is the declared multiplier of §4.2. Their later paper (Dobrescu and Shanker 2026, p. 10) appends the constrained region, written as consumption values, to the endogenous grid, which is the corner of §4.3.

## References

- Boyd, S. and Vandenberghe, L. (2004). *Convex Optimization*. Cambridge University Press. §5.5.2–5.5.3.
- Brumm, J. and Grill, M. (2014). "Computing equilibria in dynamic models with occasionally binding constraints." *Journal of Economic Dynamics and Control* 38, 142–160.
- Carroll, C. D. (2006). "The method of endogenous gridpoints for solving dynamic stochastic optimization problems." *Economics Letters* 91(3), 312–320. §2.2 (equations 17 and 18, the method) and §4.2.2 (equations 28 and 29, the liquidity constraint).
- Christiano, L. J. and Fisher, J. D. M. (2000). "Algorithms for solving dynamic models with occasionally binding constraints." *Journal of Economic Dynamics and Control* 24(8), 1179–1232.
- Cottle, R. W., Pang, J.-S. and Stone, R. E. (1992). *The Linear Complementarity Problem*. Academic Press; reprinted as SIAM Classics in Applied Mathematics 60, 2009.
- Dirkse, S. P. and Ferris, M. C. (1995). "The PATH solver: a non-monotone stabilization scheme for mixed complementarity problems." *Optimization Methods and Software* 5(2), 123–156.
- Dobrescu, L. I. and Shanker, A. (2024). "Using inverse Euler equations to solve multidimensional discrete-continuous dynamic models: a general method." Working paper, 7 December 2024. §2.1 (Definition 1 and the inverse problem on observables), §3 (the S-function and the saddle-point conditions (2) to (4)), §4.1 (observables and constrained regions, equation (5)), §4.2 (Claim 4.1, Theorem 4.1 and Claim 4.2), §4.3 (the exogenous grid as variables in one-to-one correspondence with the observables; the grid pasting function).
- Dobrescu, L. I. and Shanker, A. (2026). "A fast upper envelope scan method for discrete-continuous dynamic programming." Working paper, draft of 6 August 2026. p. 10, the constrained region appended to the endogenous grid.
- Dynare Team (2026). *Dynare Reference Manual*, Release 7.1, §4.12 "Deterministic simulation". https://www.dynare.org/manual/the-model-file.html
- EconForge (2024). "The dolo language", section "Declaration of equations", dolo.py documentation. https://www.econforge.org/dolo.py/modeling_language/
- Facchinei, F. and Pang, J.-S. (2003). *Finite-Dimensional Variational Inequalities and Complementarity Problems*, two volumes. Springer.
- Ferris, M. C. and Pang, J.-S. (1997). "Engineering and economic applications of complementarity problems." *SIAM Review* 39(4), 669–713.
- Guerrieri, L. and Iacoviello, M. (2015). "OccBin: A toolkit for solving dynamic models with occasionally binding constraints easily." *Journal of Monetary Economics* 70, 22–38.
- Hintermaier, T. and Koeniger, W. (2010). "The method of endogenous gridpoints with occasionally binding constraints among endogenous variables." *Journal of Economic Dynamics and Control* 34(10), 2074–2088.
- Karush, W. (1939). "Minima of functions of several variables with inequalities as side conditions." Master's thesis, Department of Mathematics, University of Chicago. Reprinted in G. Giorgi and T. H. Kjeldsen (eds.), *Traces and Emergence of Nonlinear Programming*, Birkhäuser, 2014, 217–245.
- Kuhn, H. W. and Tucker, A. W. (1951). "Nonlinear programming." In J. Neyman (ed.), *Proceedings of the Second Berkeley Symposium on Mathematical Statistics and Probability*, 481–492. University of California Press.
- Ljungqvist, L. and Sargent, T. J. (2018). *Recursive Macroeconomic Theory*, 4th edition. MIT Press. §17.5 and §18.5.2.
- Maliar, L., Maliar, S. and Winant, P. (2021). "Deep learning for solving dynamic economic models." *Journal of Monetary Economics* 122, 76–101.
- Mathiesen, L. (1985). "Computation of economic equilibria by a sequence of linear complementarity problems." *Mathematical Programming Studies* 23, 144–162.
- Nocedal, J. and Wright, S. J. (2006). *Numerical Optimization*, 2nd edition. Springer. Theorem 12.1.
- Rutherford, T. F. (1995). "Extension of GAMS for complementarity problems arising in applied economic analysis." *Journal of Economic Dynamics and Control* 19(8), 1299–1324.
- Swarbrick, J. (2021). "Occasionally binding constraints in large models: a review of solution methods." Bank of Canada Staff Discussion Paper 2021-5.
