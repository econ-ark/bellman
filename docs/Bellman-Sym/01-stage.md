---
title: Stage Syntax
tags:
  - stage
  - syntax
status: Draft — 7 September 2026
related:
  - "[[02-stage]]"
  - "[[03-field-equations]]"
  - "[[05-branching]]"
  - "[[06-period]]"
  - "[[03-Stages and perches]]"
date: 2026-09-07
audience: user
type: user-guide
---

# Stages

#stage #dolo-plus

> [!summary]
> Write a household's consumption problem in a `.bl` file. Declare what the household knows, what it chooses, and which equations determine resources, savings, and value. The example includes income risk and a borrowing constraint. Further examples declare indexed city data and integer states with recorded category meanings.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](../overview/02-stage.md): the stage, its perches and its fields in prose, on a buffer-stock model like this page's.
> **Used by** — [Field equations](03-field-equations.md): consumption as a separate stage file and its first-order equations; [Periods](06-period.md): joining stages.
> **Formal account** — [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md): conditions for interpreting fields as functions of states.

## 1 Stages and perches

<!--
AI: Describe user friendly way what a stage is! Define describe what perches aer. 

AI: describe what states are

Mention information sets 
### BST Example
AI: Apply it to the example already stated in 00 
-->

A household begins with nonnegative assets `b`, earns the gross return `R`, and observes positive income `y`. It chooses consumption `c` from resources `w = R*b + y` and retains savings `a = w-c`. Consumption must be strictly positive and savings nonnegative, so the feasible choices satisfy $0<c\leq w$.

A **[stage](../wiki/stage.md)** is a module of a Bellman problem with three information sets, called **[perches](../wiki/perch.md)**. In this example they distinguish income arriving, consumption being chosen, and savings being available for continuation:

| Perch | What the household knows | State used in this example |
|---|---|---|
| Arrival | Beginning assets, before the current income draw. | `b`, beginning assets. |
| Decision | Beginning assets and realized income; consumption is chosen here. | `w`, resources available to consume or save. |
| Continuation | The consumption choice and the resulting savings. | `a`, savings available for the future. |

A **state** summarizes the information needed for the remaining problem. We assume resources suffice for the consumption decision and savings suffice for continuation value. The household may remember more than these scalar states record; the perch describes its information, whereas the state supplies the arguments of its value function. These sufficiency assumptions are part of the economic model, not consequences of the notation.

## 2 Declarations and types

A **declaration** is a name, a colon and a type. The type says what the name may denote: a set of admissible values, called its **declared set**, a role in the decision problem, an information set, or a combination of these. The complete file in §4 declares a parameter, a shock, a control and a value this way:

```bl
β : (0,1)
y : ℝ₊₊
c : ℝ₊₊ @ !ctrl
V : ℝ @ !vlu
```

A **type** is a list of components, written with `@` between them. A component is either a set, written in mathematical notation, or a word with the prefix `!`. The components are unordered, so `c : ℝ₊₊ @ !ctrl` and `c : !ctrl @ ℝ₊₊` declare the same type. A type names at most one role and one perch: two different role words are refused under `one-name-one-meaning`, two different perch words under `field-perch`, and a word written twice is read once. A perch word is written only in a block's header: a top-level declaration, which stands on a line of its own outside the blocks, is refused under `field-perch` when it carries one. Several sets in one type declare their intersection: the declared name lies in each of them, as in `β : (0,1) @ (0, R^(ρ-1))` ([Symbols and conventions](reference/symbols-conventions.md) §9.2). Several sets are read on a top-level declaration of one name, and at most one of them may be other than an interval written out with its endpoints, such as `(0,1)` or `[1, inf)`; a set named by a definition counts as not an interval. The one set that is not an interval is a set of numbers, so `x : ℝ × ℝ @ (0,1)` is refused under `syntax`. Two equal sets are read as one, and two intervals with no number in common, such as `(0,1) @ (2,3)`, are refused under `syntax`. A name listed in a block's header carries one set, and several sets there are refused under `readable-form`. The sign `@` stands between descriptions of one quantity; it never multiplies sets. A quantity valued in a product is declared with `×` inside its set, as `x : ℝ × ℝ`. The prefix is what marks a vocabulary word, so a bare word is always a name and no word is reserved.

| Word | What it says |
|---|---|
| `!arvl`, `!dcsn`, `!cntn` | The name belongs to the arrival, the decision or the continuation perch. |
| `!ctrl` | The name is a control, chosen at decision. |
| `!vlu` | The name is a value. |
| `!cnst` | Written with `!vlu`: the field and its admissible domain are independent of state, shock and choice (§3.1). |
| `!shck` | The name is a shock; a restatement where the name has a law, since the law makes the name a shock. |
| `!state` | The name is a state; a restatement, since a name with a set and a perch and no role word is a state. |
| `!node` | Written in a statement's annotation, not after a colon: the statement is a separately inspectable computation ([Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md)). |

Parameters carry a set and neither a role nor a perch, as `R : ℝ₊₊`. States are declared with a set alone; their role is derived. A value carries its role word `!vlu`, and the control carries `!ctrl`. A marginal value is no field and has no role word: the derivative of a value is read where a line needs it, by the term `D_{a}V[>]`, the derivative of the continuation value in the continuation coordinate `a` ([Field equations](03-field-equations.md) §2).

A field name is local to the stage occurrence that declares it. Another stage
may use the same spelling for a different field, and a matching name does not
by itself connect the stages. All branches of one stage share its declarations,
so separate branch states need separate names. A parameter has different
scope: a name declared by two stages in one [period](06-period.md) denotes one
period parameter, with one compatible declaration and one value; the same name
in another period denotes another parameter. [Fields](../wiki/field.md) and
[Parameters](../wiki/parameters.md) give these distinctions.

**The colon binds to the smallest complete object on its left.** In `(w, c : ℝ₊₊ @ !ctrl)` the type belongs to `c` alone, and `w` is a reference to an earlier declaration. Parentheses make several names one object: `(w, c) : S` declares two names when `S` is a product with one factor per name, written out or defined by name, and each name lies in its own factor, so that `(w, c) : ℝ₊ × ℝ₊₊` places `w` in `ℝ₊` and `c` in `ℝ₊₊`. A set that is not such a product is refused under `readable-form`, and a feasibility constraint that couples a control with other names is written on the binder of the maximization ([Constraints](10-constraints.md) §1). Tuples nest inside a tuple, in a declaration and on a side of a block signature, as in `((k, h) : K, y) : !arvl` with `K` a product of two factors, and an argument of a function is a single name. In a top-level declaration, a name inside a nested tuple is a parameter when no block's header lists it, like a name of a flat tuple. The package does not yet check this ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §5.3). A tuple of two names and one name valued in a product are different declarations: `(w, c) : ℝ × ℝ` declares two names, each in `ℝ`, whereas `x : ℝ × ℝ` declares one name whose components are selected as `x[1]` and `x[2]` ([Equation parsing rules](appendices/12-equation-parsing-rules.md)).

**A law is not a type.** A shock's distribution is an object, like the number `0.96`, and two shocks with the same distribution are not interchangeable, so the distribution is assigned on its own line with `~`, before or after the line that declares the shock's set:

```bl
y : ℝ₊₊
y ~ LogNormal(μ_y, σ_y)
```

The fused form `y : ℝ₊₊ ~ LogNormal(…)` is not admitted. The distribution declaration makes `y` a shock; `!shck` may restate that role on the line of its set, `y : ℝ₊₊ @ !shck`. A joint distribution takes a tuple subject, `(Ψ, θ) ~ N(…)`. Separate declarations imply conditional independence given the source coordinates unless one names the other as an argument. The stage records this factorization as an assumption. [Shock distributions](reference/laws.md) lists the families a shock's distribution may take, [`LogNormal`](reference/laws.md#log-normal) among them.

**Block signatures are typed the same way.** In `[id=arvl_to_dcsn, (b : ℝ₊, y) : !arvl -> (w : ℝ₊₊) : !dcsn]`, the word after each parenthesized side names the perch of every coordinate listed on that side, with three exceptions: a shock listed on a side is an argument of the block's equations and belongs to no perch, a control is at decision wherever it is listed, and a constant that the stage takes in at its continuation perch stays at that perch where the input side of a forward block lists it (§2.1). A backward block's header lists the value fields it reads and writes and the controls at which its lines are read, and no state: a state of the perch at which the block's output stands is a coordinate of that output, which a line reads without listing it, and a listed state is refused under `header-coordinate`. It lists no marginal value either: a line reads the derivative of a value the header lists by the term `D_{a}V[>]`, and a line of a value builder's block may state the derivative of the value the block writes, `D_{m_d}V = 𝑑𝑢(c)`, with nothing listed for it ([Field equations](03-field-equations.md) §2). A value field the header lists and no line of the block reads is admitted. Where a line of the block reads another listed value, the unread one is left out of the block's builder, and the elaboration records it as a diagnostic, `the header lists V[>], which no line of the block reads`, in place of a refusal. A field that the header keeps (§3.1) is no such unread value: it stays in the block's builder, and no diagnostic names it. A block whose lines read none of its listed values keeps them all as the inputs of its builder and records no diagnostic.

A state or a value is placed at a perch by each of its listings: by the perch word of the side, by a perch word in its own type, or by its mark `[<]` or `[>]`. Where a listing carries two of these they agree, and a disagreement is refused under `field-perch`, except for such a constant on the input side of a forward block, as `age[>]` in `(m : Xa, c : !ctrl @ ℝ₊, age[>]) : !dcsn`. A forward block lists no field that a backward block of the same stage writes; such a listing is refused under [`header-coordinate`](reference/refusals.md#header-coordinate). The same name listed at another perch is another field with its own set, as `a` at arrival and `a[>]` at continuation in the portfolio application's `disc.bl`. Where one name stands at both the arrival and the continuation perch, a line of a backward block names either state with its mark, `a[<]` or `a[>]`; the bare name there is refused under `name-in-scope`. A field's set may be written at any of its occurrences, in a top-level declaration or on a side, and several occurrences that write a set declare their intersection ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §2.4). With `w : ℝ₊₊` on the side that writes `w` and `w : ℝ₊` on a side that reads it, `w` lies in `ℝ₊₊`. The other direction, `ℝ₊` written and `ℝ₊₊` read, is refused under `set-mismatch`, because the set written where a block writes a field must lie in the set written where another block reads it. The package does not yet check this where it cannot compare the two sets, as with an endpoint that names a parameter ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §5.3). Every field, a shock included, has a declared set. The package does not yet check this ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §5.3). The sets written for a field at several occurrences have a value in common. The package does not yet check this, except between a block that writes the field and a block that reads it ([Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) §5.3). A side may omit its perch word only when every coordinate on it is a shock, a control, or carries its own perch word or the mark `[<]` or `[>]`, as the output side of the portfolio application's policy signature `(V[>]) : !cntn -> ς` does. On a side without a perch word, a field that an earlier side placed must still carry its own perch word or its mark `[<]` or `[>]`, so a perch is never guessed. [Perch tagging rules](appendices/13-perch-tagging-rules.md) gives the information-set reading of these rules.

**Definitions and binders use the same colon.** A named set is defined with `:=`, as `Xa := ℝ₊` or `Xa := [0, ā]`. A function is defined with typed arguments, `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)`, whose `c` is local to the definition and is not the stage's control. A definition without arguments whose right side is arithmetic in the parameters, `h := 1/(1 - Γ/R)`, or is written by cases ([Equation parsing rules](appendices/12-equation-parsing-rules.md) §2), defines a derived parameter: calibration computes its value from the definition and refuses a value supplied for it ([Parameters](../wiki/parameters.md)). The definition may declare the set its value lies in, as `h : ℝ₊₊ := 1/(1 - Γ/R)`, and calibration then refuses values of the parameters at which the computed value lies outside that set. The set is written on the line of the definition: `h : ℝ₊₊` on a line of its own beside `h := 1/(1 - Γ/R)` is refused under `one-name-one-meaning`. Similarly, the binder of a maximization ranges over a feasible set written after a colon, `argmax_{c : Γ(w)}(…)`, with the bare binder `argmax_{c}` when the control's declared set is its feasible set ([Constraints](10-constraints.md)).

**A parameter's set may be a union or a difference of sets of numbers.** The union is written `A \/ B` and the difference `A \ B`. `ρ : (0,1) \/ (1, inf)` declares a risk aversion that is positive and is not one: a value lies in a union when it lies in at least one of its members. `ρ : ℝ₊₊ \ {1}` declares the same set as a difference: a value lies in a difference when it lies in the left set and outside the right. The signs `∪` and `∖` are second spellings of the two. A union or a difference is read in the declared set of a parameter, of a derived parameter and of a setting, which a methods file declares with its set ([Methodization](04-methodization.md) §4). It is refused in the set of a field, of a shock and of a function's argument, and it is not read after `:=`, in the definition of a named set or of a function. [Types](reference/types.md) lists the role words, the perch words, the reserved sets, the forms a set may take and the limits on them.

These sets describe admissible economic values. A numerical grid used to approximate a continuous domain is written separately, in the methods file ([Methodization](04-methodization.md) §3.2).

The complete file uses the following spellings:

| Spelling | What the modeller states |
|---|---|
| `R : ℝ₊₊` | The gross return is a strictly positive parameter. |
| `c : ℝ₊₊ @ !ctrl` | Consumption is a strictly positive decision control. |
| `V : ℝ @ !vlu` | `V` is a real-valued value field. |
| `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)` | Utility is a function of positive consumption. |
| `a = w - c` | Savings equal resources less consumption. |
| `y ~ LogNormal(μ_y, σ_y)` | The separately declared income shock has the specified law. |
| `:: [id=savings]` | The equation has the address `savings` within its block. |

Thus `:` declares a type, `@` stands between its components, `:=` defines, `=` states an equation, `~` supplies a shock distribution, and `->` separates the two sides of a block signature. `@` appears in one other place, at the start of a metadata line `@key: value`. The line `@stage: buffer_stock` names the stage, and a line with another key, such as `@author: someone`, is kept in `stage.metadata` ([The stage](API/stage/01-the-stage.md) §2). Each key is written once.

The file declares the discount factor `β` between zero and one and risk aversion `ρ` greater than one. For example, `ρ = 2` gives utility $u(c)=-1/c$, finite on positive consumption. This example excludes unit risk aversion, where the displayed formula would divide by zero. The income convention is explicit: conditional on arrival information, log income is normal with mean `μ_y` and standard deviation `σ_y`. This conditional distribution is constant given that information, so current income is independent of earlier observations. Positive income ensures positive resources even at zero beginning assets. A zero standard deviation gives deterministic positive income.

### 2.1 Indexed data

For a household choosing among `J` cities, the number of cities can remain a parameter when the stage is written. Declare the city set and the data indexed by it:

```bl
J : ℤ @ [1, inf)
L_J := {1, …, J}
δ : L_J → ℝ
dist : L_J × L_J → ℝ₊
```

The collection `δ` supplies one payoff per city, and `dist` supplies one distance per ordered pair of cities. If the current city is declared as a state `i : L_J` and the destination as a control `j : L_J @ !ctrl`, an equation reads their entries as `δ[j]` and `dist[j][i]`. Their use as indices does not determine their economic roles: `i` records the current location, `j` is chosen, and `J` determines the size of the common domain.

Every destination leads to the same successor stage, so the choice is one block and not a [branching stage](05-branching.md): `[id=dcsn_to_cntn, (i_d, j : !ctrl @ L_J) : !dcsn -> (i_n : L_J) : !cntn] { i_n = j }` retains the chosen city as the integer continuation state, and the number of cities stays the parameter `J`.

A numerical key must be integer-valued, including when a parameter determines it. A listed set such as `S_θ := {0, θ} ⊂ ℤ` is also admitted, with an integer-valued parameter `θ`; its keys need not be consecutive. By contrast, entries such as payoffs, distances and wages may be real-valued. In `q[s]` with `s : S_θ`, the value of `s` identifies a key; it is not a position in the list supplied at calibration. Positions counted from one select components of a fixed tuple, as in `x[1]` and `x[2]` for `x : ℝ × ℝ`.

Calibration supplies the values of `J`, `δ` and `dist`, checking the integer bounds and the number and domains of their entries. A different `J` uses the same stage declaration with correspondingly sized data. [Symbol conventions §9.2.1](reference/symbols-conventions.md#921-finite-indexed-data) gives the admitted index sets, data order and a calibration example. Each index's declared domain must fit the corresponding table domain: a state ranging over cities and an outside option cannot directly select from a table defined only on cities ([Appendix D §5.2](appendices/15-appendix-d-node-tag-and-field-indexing.md#52-collection-and-family-selection)).

A numerical key may also be a constant that the stage takes in. In the application of Benhabib, Bisin and Luo, `applications/benhabib-2019/declaration/stages/benhabib_bellman/benhabib_bellman.bl`, the header of the forward block `dcsn_to_cntn` lists the incoming `age[>]`, and its line reads the wage table as `wage_fn[age[>]][tau]`. The same calibration table is used at every age. Its row under the incoming age gives the wage for the year the stage computes.

### 2.2 Category codes

A household's status can be an integer state whose codes have recorded meanings. Define the set and give each member a category name:

```bl
HouseholdStatus := {i : ℤ | i >= 0, i <= 1} :: [!categories household_status, newborn=0, old=1]
n : HouseholdStatus
```

The expression between braces is a **comprehension**: it contains the integers satisfying every condition after `|`, with `i` local to that definition. The annotation assigns the name `newborn` to 0 and `old` to 1. A state declared on `HouseholdStatus` therefore takes integer values, while the stage retains the correspondence between those values and their meanings. Recording categories does not create a [branching stage](05-branching.md); the blocks still specify the state transitions and any choices.

Equations use the codes. For example, a transition to old age is written `n_next = 1`, with `n_next` also declared on `HouseholdStatus`; writing `n_next = old` is refused because the annotation does not declare `old` as a name usable in equations. Ordinary arithmetic remains available, so `100 - 120*n` equals 100 for a newborn household and −20 for an old one. With three or more categories, using an affine formula in the code imposes equal steps in that formula; assigning codes alone supplies no distance between categories.

The marked set must have a nonempty integer range bounded by literal inequalities, with exactly one name per code and one code per name. Use the shared identifier `household_status` when these meanings are used across stage files; [Periods §2](06-period.md#2-connectors) explains how connections check them. The complete annotation rules and the distinction from collection index sets are in [Symbol conventions §9.2.2](reference/symbols-conventions.md#922-category-codes).

## 3 Builder blocks

<!--
Explan what Builder blocks describe, ie the trnsdifiton equations. 

They are wirtten simuilar to dyunare syntax 

Explain the annodation 
-->

A **field** is a quantity interpreted in its declared information set. A **block** groups equations between declared inputs and outputs. These two blocks, taken from the complete file in §4, express the household's budget:

```bl
[id=arvl_to_dcsn, (b : ℝ₊, y) : !arvl -> (w : ℝ₊₊) : !dcsn] {
    w = R*b + y                  :: [id=resources]
}
[id=dcsn_to_cntn, (w, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = w - c                    :: [id=savings]
}
```

Read the first signature from left to right: beginning assets and the income shock determine decision resources. Here `ℝ₊` means nonnegative real numbers and `ℝ₊₊` means strictly positive real numbers. Income and the return parameter are declared elsewhere in the same file. The second signature declares `c` as a **control**, a quantity the household chooses at decision, and `a` as nonnegative continuation savings. Its equation and domains jointly impose the borrowing constraint; the maximization in §4 ranges over these feasible choices.

The words `!arvl`, `!dcsn`, and `!cntn` identify the three information sets, the perches. A shock listed on a signature side is an argument of the transition: listing `y` on the arrival side does not say that income has already been observed. Similarly, a control retains its decision role when a later block lists it with continuation inputs. [Perch tagging rules](appendices/13-perch-tagging-rules.md) explains both exceptions.

The identifiers `arvl_to_dcsn`, `resources`, and `savings` supply addresses for inspection and supported numerical methods. Their names do not supply mathematical equations. Renaming `resources` consistently changes its address but preserves `w = R*b + y`.

### 3.1 Fields sent backward

A backward header lists the value-type fields, the fields typed `!vlu`, that the block takes in and gives back. A field's **representing function** gives its value at the state coordinates on which it depends. The block may take in several fields, such as a continuation value `V[>]`, age `age[>]` and a borrowing bound `L`. The policy block determines one policy. The block that gives the decision fields, `cntn_to_dcsn` in the file of §4, evaluates its field equations at that policy.

A header may keep a field by listing the same unmarked name on both sides and writing no equation for it. A kept nonconstant field retains its representing function, and the corresponding forward block must keep every state coordinate it depends on. A constant has no state coordinates to keep. A block that keeps every output writes no line, and its body is empty, `{}`. A marked input such as `age[>]` and the bare output `age` name different fields, so an equation such as `age = age[>] - 1` states the change explicitly. See [Perch tagging rules](appendices/13-perch-tagging-rules.md).

Write `!cnst` after `!vlu` for a value-type field whose value and admissible domain are independent of states, shocks and controls. Its whole value can be a number, a table or a function. For example, an incoming field `f : Xa → ℝ @ !vlu @ !cnst` takes one fixed function on `Xa`. A line can read the field whole. A call `f(a)` also depends on the argument `a`. A table lookup likewise depends on its key. The package refuses a declaration that violates this independence under [`constant-dependence`](reference/refusals.md#constant-dependence). A declared state set itself reads no field. A value field's admissible domain may depend on supplied continuation data.

In a [modular model](../bellman-calculus/APPX-H-MODULARITY.md), repeated uses of a declaration share its operators and calibration sources. Data such as age can change through a field on each use. A recipe can still select calibration, methods and settings by position for a general model. The package checks their declarations and values and leaves the modularity judgment to the author. See [Trellises](07-trellis.md).

## 4 A complete stage file

Save this source as `buffer_stock.bl`. The final three blocks add current utility to continuation value, average over income before it is observed, and choose a feasible consumption maximizer:

```bl
@stage: buffer_stock

β : (0,1)
ρ : (1, inf)
R : ℝ₊₊
μ_y : ℝ
σ_y : ℝ₊
y : ℝ₊₊
y ~ LogNormal(μ_y, σ_y)

𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)

[id=arvl_to_dcsn, (b : ℝ₊, y) : !arvl -> (w : ℝ₊₊) : !dcsn] {
    w = R*b + y                  :: [id=resources]
}
[id=dcsn_to_cntn, (w, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = w - c                    :: [id=savings]
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]            :: [id=value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y}(V)              :: [id=value]
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{c}(𝑢(c) + β*V[>]) :: [id=choice]
}
```

Here `V[>]` is the continuation-value input, `V` is decision value, and `V[<]` is arrival value. `[<]` and `[>]` select the stage's information sets; they do not mean the preceding and following calendar periods. A bare field or `[~]` uses the decision interpretation when its declaration and equation context establish it, as for `V` here. An ordinary collection selection such as `q[a]` has a different meaning from evaluating a function at `q(a)`; see [Equation parsing rules](appendices/12-equation-parsing-rules.md).

The continuation input is a function $W:[0,\infty)\to\mathbb R$ of savings, supplied by the next period or a terminal boundary. For a given feasible consumption choice, the value equation represents

$$
Q(w,c)=u(c)+\beta W(w-c).
$$

The policy block chooses $\pi(w)\in\arg\max_{0<c\leq w}Q(w,c)$, and decision value is $v(w)=Q(w,\pi(w))$. Before income is observed, arrival value is $B(b)=\int v(Rb+y)\,\nu_y(dy)$, where $\nu_y$ is the specified income distribution. The expectation therefore uses the policy selected after income is observed. Setting $W=B$ would be an additional stationary-model condition; the stage does not impose it.

Assume $W$ is finite and continuous on every compact savings interval and select a measurable maximizer. The maximum is attained because utility tends to minus infinity at zero consumption while continuation value is bounded on the feasible savings interval. Concavity of $W$ makes the consumption maximizer unique. The arrival equation additionally requires $\int|v(Rb+y)|\,\nu_y(dy)<\infty$; bounded continuous $W$ is a sufficient case under this lognormal distribution. [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R5–R8 gives the state-representation, integration, and policy conditions.

This documentation example modifies the repository's `applications/consumption-savings-iid/declaration/stages/cons_savings_iid/cons_savings_iid.bl`: it uses wholly positive income, restricts the discount factor to `(0,1)`, and states the choice by the maximization alone, as that application's stage file also does, over its declared feasible set `Γ(w) = (0, w]`; the application writes the candidate lines of the endogenous grid method and the derivative lines of its values in its methods file, `methods.bl` beside the stage file ([Methodization](04-methodization.md)). The displayed source is the example taught here; it does not certify the different application source.

## 5 Files and next steps

The stage file states the model equations. To solve a finite-horizon problem, supply [continuation and terminal values](07-trellis.md), [methods, settings, and calibration](04-methodization.md). The methods file is written in the same language, beside the stage file; the settings and calibration files are YAML. [Field equations](03-field-equations.md) separates consumption from income and discounting so that these stage files can be joined in a [period](06-period.md).

A **block** is the authored typed group of equations between declared inputs and outputs, and a **[builder](../wiki/builder.md)** is the operator that block defines: a transition, a value calculation, or a policy relation. The builder keeps the block's id as its name, and a reader reaches it in the elaborated stage by the pair of [perches](../wiki/perch.md) its block joins, `stage.builder["cntn", "dcsn"]` for the block `cntn_to_dcsn`, the policy builder by its own key, `stage.builder["policy"]`, or from a perch, which reaches the builders of the edge that leaves it, the step from that perch to the next: `stage.dcsn.builder.bwd` is the same builder, which constructs the value at the decision perch, `stage.arvl.builder.bwd` the builder of `dcsn_to_arvl`, and `stage.dcsn.builder.policy` that of `policy`. The backward builders used in solution form the graph `stage.builder.bwd`, and the forward ones used in simulation the graph `stage.builder.fwd` ([The builders graphs](API/stage/03-build.md) §§1 to 3). To make one equation separately inspectable, add `!node` to its annotation; [Field equations](03-field-equations.md#4-statements-and-computation-boundaries) demonstrates this with savings. Neither a block's name nor a numerical-method choice supplies a missing equation.

For loading, use the [factory API](API/factory/index.md), and for inspection [the API](API/index.md). The stage retains interpreted equations and definitions in a graph of mathematical operations and their typed connections. With the required assumptions, its field equations can also be inspected as functions of states. Their mathematical relationship is described in [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md).

> [!note]- Technical details
> `.bl` inherits its syntax from dynspec, an expression language. Parsing constructs a temporary abstract syntax tree, a structured representation of the written file. Checked interpretation constructs the stage's [semgraph](../wiki/semgraph.md), the semantic graph of its equations, and discards that tree and its [source spans](../wiki/source_span.md).

> [!ast]- Abstract grammar: FILE
> This is a projection of the dynspec host grammar in [ASDL](../wiki/asdl.md), the notation for syntax-tree constructors. `*` means an ordered list and `?` means optional. The omitted declaration alternative and the definitions of the referenced sorts belong to the full grammar; this projection does not redefine them.
>
> ```asdl
> file = FILE(item* items)
> item = Metadata(identifier key, scalar value)
>      | Statement(stmt core, annotation? annot)
>      | Block(annotation tag, item* body)
> ```
>
> **Keys.** `items` preserves source order; `key` and `value` give metadata; `core` is a statement with optional `annot`; `tag` is a block header and `body` its contents. These are ASDL fields, not YAML keys to write in a `.bl` file. `scalar`, `stmt`, and `annotation` are host sorts.
>
> **Head.** Stage metadata identifies the stage file; the syntax-tree root remains `FILE`.
>
> **Denotes.** Interpretation constructs the declared stage equations and their typed connections, subject to [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md).
>
> **Status.** The three item constructors shown retain their argument order and multiplicity. Scope, type agreement, and complete output definitions are construction checks, not consequences of this grammar box.
