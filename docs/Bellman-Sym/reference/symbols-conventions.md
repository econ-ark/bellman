---
title: Symbol conventions
tags:
  - docs/reference
  - notation
audience: user
type: reference
---

# Symbol conventions

> [!summary]
> Bellman-SYM distinguishes a field, its domain, and a function representing that field in state coordinates. Perch marks identify arrival, decision, and continuation information within a stage. Names such as `V` and `policy` are conventions; their declarations and equations determine their roles, and the derivative of a value is read by the term `D_{a}V[>]`, not named by a field. The last section lists the punctuation, the reserved sets and the type words with which a stage file declares its objects.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](../01-stage.md): a complete stage file; [Perch tagging rules](../appendices/13-perch-tagging-rules.md): typing and information.
> **Used by** — [Field equations](../03-field-equations.md), [Periods](../06-period.md), and [Trellises](../07-trellis.md).
> **Formal account** — [Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md) for mathematical interpretation; [Appendix D](../appendices/15-appendix-d-node-tag-and-field-indexing.md) for nodes and indexing.
> **See also** — [Expression forms](forms.md): the operators and functions a line of a stage file writes.

## 1 Reading a stage equation

The discounting stage multiplies the continuation value by the discount factor. This is its complete source:

```bl
@stage: disc

Xa := ℝ₊
β : (0,1)

[id=arvl_to_dcsn, (a : Xa) : !arvl -> (a_d : Xa) : !dcsn] {
    a_d = a
}

[id=dcsn_to_cntn, (a_d) : !dcsn -> (a[>] : Xa) : !cntn] {
    a[>] = a_d
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]                      :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}
```

Here `a`, `a_d`, and `a[>]` are assets at three information contexts. The transition equations state that their values agree in this stage. The stage writes no derivative line: its two backward lines are a scaling and an identity of the value, whose state passes unchanged, so the derivative of the value passes through them, and a stage before this one that reads `D_{a}V[>]` of its continuation receives the derivative of the discounted value. No letters of a name establish a derivative; the derivative of a value is read by the term `D_{a}V[>]`, which applies the operator `D` to the declared value in the named coordinate (§4).

The block identifier `cntn_to_dcsn` provides an address. Renaming it changes references such as the path of a place in a methods file, but does not change multiplication by `β`. In a model with a separate discounting stage, do not insert a second discount factor into the beta-free consumption equations.

## 2 Fields, functions, and spaces

A **field** is a named quantity of a stage: a state, a control, a value or a multiplier ([Constraints](../10-constraints.md) §4.2) at one perch, or a shock, which belongs to no perch (§9.3). Once shocks are declared, fields may be interpreted as random variables on the underlying probability space. A **representing function** gives the field's value as a function of the state coordinates on which it depends. A domain describes the values an object may take; it is distinct from the space of functions on a state domain.

| Mathematical notation | Object |
|---|---|
| $\mathsf X_\prec$, $\mathsf X$, $\mathsf X_\succ$ | Arrival, decision, and continuation state domains. |
| $\mathrm x_\prec$, $\mathrm x$, $\mathrm x_\succ$ | State fields taking values in those domains. |
| $\mathrm V_\prec$, $\mathrm V$, $\mathrm V_\succ$ | Value fields. |
| $v_\prec$, $v$, $v_\succ$ | Functions of state coordinates representing the value fields under the stated assumptions. |
| $g_\prec$, $g_\succ$ | Laws of motion, from arrival to decision and from decision to continuation. |
| $\pi$ | A policy, meaning a measurable choice as a function of decision information. |
| $\mu$ | A probability distribution. |
| $\mathbb T_\pi$ | The backward value operator at a fixed policy. |
| $\mathbb M_\pi$ | The forward distribution operator at that policy. |

Sans-serif capitals denote spaces, italic letters denote functions, and roman letters denote the fields those functions represent, the same letter for both. These typography conventions help the reader; they do not type a source identifier. The source `V[>]` is a value field because of its declaration. A name such as `V_fn` has no reserved function meaning.

For example, if the continuation state field is $x_\succ$ and a value field is measurable with respect to that state, an appropriate measurable factorization gives $\mathrm V_\succ=v_\succ(x_\succ)$. The factorization requires the measurable-space assumptions stated in [Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md). It does not follow from choosing a font, and it need not specify a unique extension away from the states represented by $x_\succ$.

The notation $L^2(\Omega,\mathcal F)$ denotes square-integrable fields on a probability space with information $\mathcal F$. Use it only when square integrability is assumed. A declaration allowing extended values does not automatically put a field in $L^2$.

A value-type field sent backward can be declared `!cnst`. The field then has no state coordinates in its representing function. If the field's whole value is itself a function, evaluating that function still takes its own arguments. See [Fields sent backward](../01-stage.md#31-fields-sent-backward).

## 3 Perches and information

A **perch** is one of the three information contexts within a stage:

| Context | Mathematical subscript | `.bl` reference | Type word |
|---|---|---|---|
| Arrival | $\prec$ | `V[<]` | `!arvl` |
| Decision | $\sim$, usually omitted | `V` or `V[~]` | `!dcsn` |
| Continuation | $\succ$ | `V[>]` | `!cntn` |

In a block's header a mark agrees with the perch word of its side: the listing `(a[>] : Xa) : !arvl` is refused under [`field-perch`](refusals.md#field-perch). The one exception is a constant that the stage takes in at its continuation perch: the input side of a forward block lists it as the backward header spells it, `age[>]`, and it stays at the continuation perch ([Stages](../01-stage.md#21-indexed-data) §2.1). The package reads `a[~]` as the bare name `a`, so the listing `(a[~] : Xa) : !arvl`, which breaks the rule, is read as the arrival field `a`. The package does not yet check this ([Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md) §5.3).

When nested information is assumed, the information structure can be written $\mathcal F_\prec\subseteq\mathcal F_\sim\subseteq\mathcal F_\succ$. Stage marks alone do not establish this assumption. These inclusions need not be strict: an identity transition can reveal no additional information. Nor must a list of current state coordinates alone generate all past information. State sufficiency is an assumption used when passing to functions of those coordinates.

Information marks distinguish field references within the stage. They are not dates, and a perch is not an operator endpoint. In particular, a shock listed as a transition argument need not be observed before that transition. A decision control written beside continuation values is still a decision control. The rules for the sides of a block's header respect these role exceptions.

The diagram below records information order and the usual directions of transition and value calculations; its circles denote information contexts:

```text
arrival information  ── state transition ──>  decision information
        ^                                            |
        | arrival value calculation                  | state transition
        |                                            v
        +                                  continuation information
                        <── backward value calculation ──
```

A stage can use pre-decision shocks, post-decision shocks, both, or neither. In a deterministic stage the law can be degenerate, but determinism does not require the arrival transition to be the identity. The equations decide the transition.

## 4 Operators and derivatives

The policy is written as a subscript: $\mathbb T_{\succ,\pi}$ and $\mathbb M_{\succ,\pi}$. Superscripts can then denote iteration, such as $\mathbb T_\pi^n$. When a stage index is needed it comes first, for example $\mathbb T_{k,\succ,\pi}$. Omit an index only when its referent is unambiguous.

In the usual two-transition stage, backward composition is $\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi}$, while forward composition is $\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec$. These equations specify order on compatible domains; the backward operator additionally depends on the declared reward and discounting. It must not be identified with a probability transition merely because both use the same state transition.

> [!note]- Technical details
> For a transition-only calculation, let $(X,\mathcal X)$ and $(Y,\mathcal Y)$ be measurable state spaces. A probability kernel $P$ assigns a probability measure $P(x,\cdot)$ on $Y$ to each $x\in X$, with $x\mapsto P(x,A)$ measurable for every $A\in\mathcal Y$. For bounded measurable $f:Y\to\mathbb R$, define $(Kf)(x)=\int f(y)P(x,dy)$, a bounded measurable function on $X$. For a probability measure $\mu$ on $X$, define the probability measure on $Y$ by $(M\mu)(A)=\int P(x,A)\mu(dx)$ for $A\in\mathcal Y$. Integration then gives $\int f\,d(M\mu)=\int Kf\,d\mu$. This identity concerns transition and expectation. Adding a reward, discount, or maximization requires the corresponding additional operations; a rewarded Bellman operator need not satisfy this identity.

A derivative expression applies the operator `D` to a function the file holds: to a declared function, `D_{c}(𝑢)`, where the subscript names one of its formal arguments, or to a value field written with its perch mark, `D_{a}V[>]`, where the subscript names a state coordinate of the perch at which the value is read, written without its mark. The second form is the **derivative term**; it denotes the derivative of the value in that coordinate, a function of the value and no second object, and it has this one spelling. A name such as `𝑑𝑢` can be defined by a derivative expression or by a closed form, and a stage file may define `dV = D_{a}V[>]` and read the name. The package differentiates nothing: a kernel that calls a function defined by `D_{c}(𝑢)` has no compiled form and is refused under `kernel-form`, a kernel that reads a derivative term compiles with the term among its arguments ([Expression forms](forms.md) §3), and the derivative of a value is evaluated as the stage that built the value fixed it ([Methodization](../04-methodization.md) §5). A line whose left side is a derivative term of the value its builder writes, `D_{m_d}V = 𝑑𝑢(c)`, is the author's assertion that the derivative equals the right side, which holds under the envelope conditions; the stage lists the reading and checks it against nothing.

Expectation and maximization subscripts bind their integration and choice variables. The derivative subscript selects a declared formal argument of the function, or a state coordinate of the perch at which a value is read; it does not create a new local stage variable. An ordinary underscore is part of a name. Thus `E_{θ}(V[>])` specifies integration over a shock, while `μ_θ` is simply a chosen parameter name. The operation forms are listed in [Expression forms](forms.md).

## 5 Equations and nodes

A **block** is an authored typed header and body. Its identifier provides an address, and its header and statements declare the fields and equations. A **builder** is the operator a block denotes. Within a block, `!node` marks a line as an authored node, a computation kept as a unit of its own that a method can address; in a backward block it forms a [sub-builder](../../wiki/sub_builder.md) of the block's builder. An expectation nested inside an equation remains a mathematical operation whether or not its containing statement is marked.

Conventional labels such as `value`, `marginal`, `InvEuler`, and `cons_choice` can make a file readable. They do not select mathematical rules. Likewise, calling a block `policy` does not insert optimization. A methods file can type a method at a line with an id or at an operator occurrence without `!node`; [Methodization](../04-methodization.md) §2 lists the places a methods file names.

An unmarked explicit intermediate equation may be substituted while preserving all outputs and dependencies. An implicit equation instead defines a relation. For candidate state coordinates $H(s)$ and controls $U(s)$ indexed by $s$, the pairs $(H(s),U(s))$ define one control on the image of $H$ exactly when equal coordinates imply equal controls. Measurability, coverage of the intended state domain, and optimality remain separate conditions. [Appendix D](../appendices/15-appendix-d-node-tag-and-field-indexing.md) applies this distinction to the endogenous grid method.

## 6 Branches and collections

For a finite nonempty set of alternatives, a branch can have its own state coordinates and continuation value. A branch state can be described as a pair $(j,x_j)$, where $j$ labels an alternative and $x_j$ belongs to its state domain. When the domains differ, retaining the label is necessary to interpret the coordinates. When every alternative shares a domain $X$, these pairs belong to the product of the alternative set and $X$.

A tuple of continuation values and selection by the declared choice can express this distinction in `.bl`. Ordinary selection such as `q[d]` selects a collection entry; it does not declare a function over `d`. The complete retirement example in [Branching](../05-branching.md) supplies the domains, values, selection equation, and finite maximization. Finite maximization attains a value when the feasible set is nonempty and each candidate value is defined; ties still need a choice rule.

Stochastic alternatives use a declared joint or conditional law and an expectation instead. A list of marginal laws does not specify independence. Neither the spelling of a branch label nor a method tag decides whether the model maximizes or averages.

## 7 Stage and period indices

A **stage occurrence** is one use of a stage file under a particular key in a period. Reusing the same `.bl` source requires distinct occurrence keys; it does not identify the resulting stages or their bindings.

| Notation or key | Meaning |
|---|---|
| `periods[h]` | The period `h` periods before terminal. |
| `periods[0]` | The terminal period. |
| `inter_connectors[h]` | Field renaming joining period `h+1` to period `h`. |
| `syntactic["periods"][h]["stages"][stage_name]` | The record of that occurrence and period: its merged parameter, setting, and method mappings. |
| `[<]`, `[~]`, `[>]` | Information contexts within one stage, independently of `h`. |

Terminal data supply all unconnected continuation fields of period zero at realization. A connector renames corresponding fields between occurrences; matching names alone does not prove matching domains or information roles. The per-stage mathematical graph and the syntactic trellis, a dictionary of stage records, serve different purposes; the order of a period's stages is computed from the fields they join. [Periods](../06-period.md) and [Trellises](../07-trellis.md) give their composition rules.

## 8 Parameters, settings, and interpretation

A **parameter** defines the economic problem; a **setting** controls a numerical calculation. A finite menu of housing sizes is a mathematical domain, so changing its endpoints or number of available sizes changes the problem. A grid approximating a continuous housing domain is a numerical choice. A simulation grid need not equal the solution grid.

A **derived parameter** is a constant defined from calibrated parameters without arguments. For example, `q : (0,1) := (β*R)^(1/ρ)/R` defines the return patience factor. Its value must lie in the declared set, which calibration checks (§9.2).

A definition may use cases, such as `h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else inf`. The declared set must admit the infinite branch. This generic syntax example does not state the human-wealth declaration of the perfect-foresight application. That application sends human wealth backward as a field.

[Equation parsing rules](../appendices/12-equation-parsing-rules.md) §2 gives the definition forms. [Parameters and settings](../API/stage/06-par-and-settings.md) §1.1 shows the parameter table.

The meaning map $\Upsilon$ interprets declarations and equations. The representation map Ρ denotes their numerical realization after the required choices and bindings. Lowercase $\rho$ remains available for an economic parameter, such as risk aversion. These names do not assert that interpretation or approximation is invertible, or that different numerical choices commute.

Elaboration keeps the fields, with the interpreted equation bodies and definitions, in the two [initial diagrams](../../wiki/semgraph.md), and derives from them, under explicit assumptions, the two builders graphs, on functions and on measures. The temporary syntax tree and source spans are discarded; a second independently editable function model is not required. See [From source to a formal problem](../09-from-syntax-to-formal-problem-definition.md).

## 9 Declarations, domains and type words

The reference page [Types](types.md) lists the role words, the perch words, the reserved sets, the forms of a set expression and the limits on them.

### 9.1 Punctuation

The examples are lines of the stage files under `applications/portfolio-choice/`: `disc.bl`, whose source §1 shows, `cons.bl` and `noport.bl`; the definition of `q` that declares its set is a line of `perfect_foresight.bl` under `applications/consumption-perfect-foresight-crra/`. The examples of the union and the difference are written for this table.

| Spelling | Use | Example |
|---|---|---|
| `:` | Declare a type: a declared set (§9.2) or a role, on a line of its own or on a side of a block's header, and an information context on a side of a block's header only. A declaration on a line of its own that carries a perch word is refused under [`field-perch`](refusals.md#field-perch). | `β : (0,1)`; `(a : Xa) : !arvl` |
| `@` | Write the components of a type with `@` between them; their order does not matter. Several sets in one type declare their intersection (§9.2). | `c : !ctrl @ ℝ₊₊` |
| `\/`, also `∪` | Form the union of two sets of numbers, in the declared set of a parameter, a derived parameter or a setting (§9.2). | `ρ : (0,1) \/ (1, inf)` |
| `\`, also `∖` | Form the difference of two sets of numbers, the members of the first that lie outside the second, in the same places (§9.2). | `ρ : ℝ₊₊ \ {1}` |
| `:=`, also `<-` | Define a named set, which may be written as a comprehension (§9.2), a function, or a derived parameter (§8), whose definition may declare its set, `q : (0,1) := (β*R)^(1/ρ)/R`. | `Xa := ℝ₊`; `Xa := [0, ā]`; `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)`; `q : (0,1) := (β*R)^(1/ρ)/R` |
| `=` | State an equation inside a block, explicit or implicit. | `V = β*V[>]` |
| `~` | Give a shock its law, on a line of its own. | `θ ~ LogNormal(μ_θ, σ_θ)` |
| `->` | Separate the input side of a block's header from its output side. | `(a : Xa) : !arvl -> (a_d : Xa) : !dcsn` |
| `:: [id=…]` | Give a line an id, by which a methods file and the stage object name it. | `:: [id=value]` |
| `@stage: name` | Name the stage, once in the file. | `@stage: disc` |

The argument `c` of `𝑢(c : ℝ₊₊)` is local to the definition and declares no control, and a name such as `𝑑𝑢` differentiates nothing: the body of its definition defines the function. An equation is not an assignment or a policy function by its form alone: `c = c[>]` in the block `policy` of `methods.bl`, the methods file beside `cons.bl`, is an implicit relation between the policy and the candidate `c[>]`, which the line `m_d[>] = a + c[>]` places at the cash on hand of each saving ([Appendix D](../appendices/15-appendix-d-node-tag-and-field-indexing.md) §7).

### 9.2 Domains

A **domain** is the set of values a field or a parameter may take, also called its **declared set**. These set names are reserved by the grammar and need no definition line:

| Spelling | Set |
|---|---|
| `ℝ` | All real numbers. |
| `ℝ₊`, also `R+` or `R_{+}` | Nonnegative real numbers, zero included. |
| `ℝ₊₊`, also `R++` or `R_{++}` | Strictly positive real numbers. |
| `ℤ` | Integers. |
| `ℕ` | Natural numbers; state a sharper lower bound where it matters. |
| `ℝ_{-∞}` | Real numbers with negative infinity adjoined, written with the ASCII hyphen. |
| `ℝ_{+∞}` | Real numbers with positive infinity adjoined. |
| `ℝ_{±∞}`, also `ℝ̄` | Real numbers with both infinities adjoined. |

A bare `R`, `N` or `Z` is an ordinary name and not one of these sets; `R` may be the gross return on assets. Define any other named set before using it, `Xa := ℝ₊`. A named set may also be an interval, `Xa := [0, ā]`, `Xa := (0, ā]` or `Xa := [0, ā)`, whose endpoints may name parameters; a field typed `a : Xa` then has the same declared set as `a : [0, ā]`. The same holds where one block header lists the field on `Xa` and another on `[0, ā]`. The package does not yet check this ([Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md) §5.3). The open-open form is the exception: after `:=`, `(0, ā)` is read as a pair of values, which is neither a set nor a derived parameter, so the line `Xa := (0, ā)` is refused under [`not-constructed`](refusals.md#not-constructed), even where nothing reads `Xa`. An open interval is written after the typing colon where it is used, `a : (0, ā)`. An interval writes its endpoints with the usual brackets, `(a,b)`, `(a,b]`, `[a,b)` and `[a,b]`, and an endpoint may be infinite, `ρ : [1, inf)`; an interval that holds no number, such as `(2, 1)`, is refused when the file is read. A finite set lists its labels, `R_type := {r1, r2, r3, r4, r5}` or, inline, `d : !ctrl @ {work, retire}`, and a product uses `×`, `x : ℝ × ℝ`.

The union of two sets of numbers is written `A \/ B`, also `A ∪ B`, and their difference `A \ B`, also `A ∖ B`: `ρ : (0,1) \/ (1, inf)` declares a parameter in one of the two intervals, and `ρ : ℝ₊₊ \ {1}` a positive parameter other than one. A value lies in a union when it lies in at least one member, and in a difference when it lies in the left set and outside the right. The product `×` is read before the two signs and the arrow `→` after them, and the two signs are read from left to right. The package prints them as `\/` and `\`. A union and a difference are read in the declared set of a parameter, of a derived parameter and of a setting. They are refused in the set of a field, of a shock and of a function's argument, and they are not read after `:=`. A difference whose left side lies within its right side, as in `(0,1) \ ℝ₊`, holds no number and is refused under [`readable-form`](refusals.md#readable-form) when the file is read, where the package can decide the inclusion. A difference that is a member of a union is not judged.

A declaration may write several sets in one type, with `@` between them, and the declared name then lies in each of them, so that the sets declare their intersection: `β : (0,1) @ (0, R^(ρ-1))` declares a discount factor in both intervals, below one and below `R^(ρ-1)`. A bound is written as an interval, whose endpoints may name parameters and derived parameters and whose unbounded side is `-inf` or `inf`: `θ : ℤ @ [1, inf)` declares an integer of at least one. A parameter's or a setting's set that names a field is refused, and an undeclared name there is refused under [`name-in-scope`](refusals.md#name-in-scope); a shock inside an expectation over that shock is still read where its law reads no field, as in the bound `(0, E_{Ψ}(Ψ^(1-γ)))`. At most one of the sets is written otherwise than as an interval with brackets, and a named set counts as such a set; a second such set is refused under [`syntax`](refusals.md#syntax). The sets may be written in any order, and two equal sets are read as one. Two intervals of numbers with no number in common, such as `(0,1) @ (2,3)`, are refused under `syntax`. Several sets are read on the declaration of one name on a line of its own only; on a field's listing in a block header they are refused under [`readable-form`](refusals.md#readable-form).

When values are bound, `calibrate` refuses a value outside any of the sets and names the bound it breaks. A value bound to a name declared on an extended real, `ℝ_{-∞}`, `ℝ_{+∞}` or `ℝ_{±∞}`, must lie in that set. `calibrate` decides the membership of a number: a finite number lies in each of the three sets, and an infinity in those that hold it, so that `inf` is refused for a name declared on `ℝ_{-∞}`. A value that is no number, such as a string, lies in none of them. The package does not yet check this ([Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md) §5.3). An endpoint that is the bare name of a parameter or of a derived parameter valued at an infinity is read as that infinity ([Equation parsing rules](../appendices/12-equation-parsing-rules.md) §2). A bound that reads a derived parameter is judged once calibration has computed the derived value from the declared values. The value of a derived parameter whose definition declares a set is judged against that set in the same step, and calibration refuses a value outside it with a sentence that names the parameter, its definition, the set and the values read. A bound whose arithmetic has no value at the calibration, such as `1/(R-2)` at `R = 2`, refuses the calibration, and so does a bound that computes with a name valued at an infinity. A bound that holds an expectation over a shock, or that calls a function other than `log`, `exp`, `min` and `max`, such as a function the file defines, is not decided: the stage binds, and `stage.obligations()` lists the membership as required.

Adjoining infinity lets a value reach an endpoint; it does not make every operation on such values defined. An expectation needs integrability or an extended-value convention, and infinity minus infinity is undefined. [Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md) states the assumptions used for value equations.

#### 9.2.1 Finite indexed data

A finite set of integer keys lists them, `{0, 1}`, or names the set its members lie in when a member names a parameter, `S_θ := {0, θ} ⊂ ℤ`, with `θ` integer-valued. An integer range whose bounds may name parameters, `L_J := {1, …, J}`, with `…` or `...` between the commas, holds every integer from the first bound to the second, including both bounds. The bounds and the listed members must be integers; their conditions are retained until calibration if they depend on parameters. A value such as `3.0` is integer-valued and identifies the same key as `3`, without rounding another integer to it. Separately listed keys must be distinct. A bare `{a, b}` continues to list two labels.

A collection is declared with one entry per key, `δ : L_J → ℝ`, or per ordered pair, `dist : L_J × L_J → ℝ₊`. The admitted index sets are integer ranges, listed integer keys, finite label sets, and products of these sets. Selection uses a name declared on the corresponding index set: `δ[j]` selects the entry at `j : L_J`, and `dist[j][i]` the entry at the pair of keys. An integer literal in brackets denotes a position, and a collection on an index set is not selected by a position: `δ[1]` is refused under [`family-selection`](refusals.md#family-selection), although 1 is a key of `L_J`. Select with a name declared on the index set, `δ[j]` with `j : L_J`. Numerical keys must be integer-valued; the entries they identify, such as wages, distances and shock outcomes, may be real-valued. Separate indices of a finite shock distribution may identify equal numerical outcomes.

Calibration supplies a sequence in index order or a mapping from keys to entries. Integer ranges are ordered from the lower bound to the upper bound; listed sets retain the order in which their members are written. For example, declare:

```bl
θ : ℤ @ [1, inf)
S_θ := {0, θ} ⊂ ℤ
q : S_θ → ℝ₊
```

The calibration fragment below sets `θ` to 5 and supplies 10.25 at key 0 and 20.75 at key 5:

```yaml
θ: 5
q: [10.25, 20.75]
```

Writing `q: {5: 20.75, 0: 10.25}` gives the same association. If `s : S_θ` takes the value 5, `q[s]` selects 20.75; 5 is the key, not the fifth position. Calibration checks the integer keys, their distinctness, the data shape and the entries' declared domains. A matrix uses this order on each axis. Copying a collection between stages also requires matching key order ([Periods §2](../06-period.md#2-connectors)).

> [!note]- Technical details
> Compiled numerical selection uses signed 64-bit integers, with arithmetic checks that require each operand and intermediate result to fit that range. Constant integer expressions are evaluated exactly before the function is written. A power in an index bound or listed member requires a nonnegative integer exponent, which may depend on parameters, and parameter-dependent division is compiled only when the denominator is 1. For another division, supply the integer result as a separately declared parameter; the mathematical set remains available for inspection when `compile_kernel()` refuses the expression under `kernel-form`. A compiled integer calculation that overflows is refused rather than identifying another key.

#### 9.2.2 Category codes

A named set may also be a comprehension, `H := {i : ℤ | i >= 0, i <= 1}`, which binds the name `i` to the set after the colon and holds the members that satisfy every condition after the bar. Mark such a set with `!categories` to assign meanings to its integer members, called **category codes**:

```bl
HouseholdStatus := {i : ℤ | i >= 0, i <= 1} :: [!categories household_status, newborn=0, old=1]
n : HouseholdStatus
```

A marked comprehension must range over `ℤ` or `ℕ`, and every condition must compare its bound name with an integer literal by a strict or weak inequality, with the name on either side. The conditions must give a nonempty range bounded below and above. Parameter bounds and equality conditions are refused on a marked set, although equality remains available in ordinary unmarked comprehensions. A marked range over `ℕ` must have a lower bound of at least 1, since the language does not decide whether 0 is a natural number. The annotation supplies exactly one category name for each member, with no repeated name or code (§9.3).

Here the code 0 stands for a newborn household and 1 for an old one. The **category map** records these associations between codes and categories. Arithmetic on the field has its usual numerical meaning: `100 - 120*n` is 100 for a newborn household and −20 for an old one. With three or more categories, a formula affine in the code gives equal steps between the values at successive codes; that is an assumption of the formula the author writes. Assigning codes supplies no distance between categories or meaning to interpolation between them. The word *category* here denotes a value of a categorical variable, as in a statistical value label. [Appendix C §2.1](../appendices/14-appendix-c-syntax-to-semantics.md#21-declarations) gives the mathematical interpretation.

A category name is not a name usable in stage equations. The transition to old age is written with the code, `n_next = 1`; `n_next = old` is refused under `name-in-scope`. The category map remains part of the set's displayed definition, denotation and exported stage, so the meanings can be inspected alongside equations using the codes. Unmarked comprehensions keep their ordinary set meaning.

The identifier `household_status` asserts shared category meanings across stage files. Two sets using it identify a category by that identifier and the category's name; a different identifier denotes different categories. Without an identifier, categories are local to the named set in its stage text and shared by occurrences of that text. [Periods §2](../06-period.md#2-connectors) states when fields using these meanings can be connected.

> [!important]
> A comprehension marked `!categories` is admitted as a field domain, but is not an admitted index set for a collection. Thus `n : HouseholdStatus` is admitted, while `payment : HouseholdStatus → ℝ` is refused under `readable-form`. Use the index-set forms in §9.2.1 for indexed data.

> [!note]- Technical details
> A stage constructed by `make_stage` from a syntax tree has no stage text. A marked set without an explicit category identifier therefore has no established category identity for connections in such a stage; supply the identifier when constructing it this way.

### 9.3 Type words and statement marks

A **type word** is a word after `!` that gives a field its role, its information context or, for `!cnst`, its independence of the state; the `!` sets it apart from a name the author chooses.

| Word | Meaning |
|---|---|
| `!state` | A state field. |
| `!ctrl` | A control, chosen with the information of the decision perch. |
| `!shck` | A shock, whose law and timing are declared separately. A shock belongs to no perch: it is drawn on the edge between two perches, and a perch word or a mark `[<]` or `[>]` written on a shock is refused under [`field-perch`](refusals.md#field-perch). |
| `!vlu` | A value field. |
| `!cnst` | Written with `!vlu`: a constant, a value-type field whose value and declared set depend on no state, shock or control (§2). |
| `!arvl`, `!dcsn`, `!cntn` | The arrival, decision and continuation perches of §3. |

Removing a word can change the problem: without `!ctrl`, `c` is no longer chosen. A parameter needs no word: a name declared with a set on a line of its own, which no block header lists, is a parameter, as `β : (0,1)` is, and a line of a block that writes it is refused under [`parameter-or-field`](refusals.md#parameter-or-field).

A name is declared on a line of its own at most once ([`declared-once`](refusals.md#declared-once)), and a role restated in a block header must agree with the first statement ([`one-name-one-meaning`](refusals.md#one-name-one-meaning)). A set restated in a block header need not equal the first. The field lies in each of the sets written for it, so that they declare their intersection, as several sets in one type do (§9.2), and these sets must have a member in common. The package does not yet check this, except between a block that writes the field and a block that reads it ([Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md) §5.3). The set written by the block that writes a field must also lie in the set written by each block that reads it; where the package can compare the two sets, a field that breaks this is refused under [`set-mismatch`](refusals.md#set-mismatch). The package does not yet check this where it cannot compare the two sets, as with `[0, ā]` written and `[0, 1]` read, since the endpoint `ā` names a parameter ([Appendix C](../appendices/14-appendix-c-syntax-to-semantics.md) §5.3).

A word written on a side of a block's header follows the rules for roles: a shock listed as an argument is not thereby observed on that side, and a control listed beside continuation values remains a decision control ([Perch tagging rules](../appendices/13-perch-tagging-rules.md) §2).

Two marks go in a line's annotation, `:: [id=value, !node]`, and a third in the annotation of a named set, `:: [!categories household_status, newborn=0, old=1]`:

| Mark | Effect |
|---|---|
| `!node` | Keep the line as a computation of its own, an authored node that a method can address, without changing its equation. |
| `!doc` | Exclude the line from the equations that define the model; it documents them. |
| `!categories` | Give each member of a named integer comprehension a category name (§9.2.2). Write the marker, optionally followed by one shared identifier, and one `name=code` entry per member. |

No mark is a role of a field, and `!node` and `!doc` together have no specified meaning. A failed check of the category marker, its entries or its set, the marker on any other item, and a field declared on a set with category codes at one site and on another set at another are refused under [`category-codes`](refusals.md#category-codes).

> [!note]- Technical details
> A category name begins with a letter and continues with letters, digits and `_`. Its code is decimal digits with an optional sign, read as an integer, so `0`, `-0` and `00` are one code. An `id=` entry supplies the declaration's address, and a double-quoted description may accompany the category entries.
>
> Inside the brackets a double-quoted entry keeps its quotes and is read as a description, so `["!categories"]` marks nothing, while `:: "!categories"`, written without brackets, is the marker without codes and is refused. Single quotes are characters of the entry, so `'old=1'` is the key `'old` with the value `1'`, which a marked annotation refuses, and a single-quoted marker, `['!categories']`, marks nothing.

### 9.4 Brackets

| Written | Reading |
|---|---|
| `V[<]`, `V` or `V[~]`, `V[>]` | The field at the arrival, decision or continuation perch (§3). |
| `x[1]`, `q[a]` | Selection from a family, by position counted from one, by a label or by a key declared on the collection's index set; a position is a whole number. |
| `L_J := {1, …, J}` | The integers from the first bound to the second, each bound integer-valued and allowed to depend on parameters. |
| `S_θ := {0, θ} ⊂ ℤ` | A finite set of integer keys in authored order, with integer membership and distinctness checked at calibration when they depend on parameters. |
| `δ : L_J → ℝ` | One parameter whose value is a collection with one entry, in `ℝ`, per member of `L_J`. |
| `(x, y)` | An ordered tuple. |
| `(x, y) : S` | Two names declared together, read where `S` is a product with one factor for each name, written out or named, `S := ℝ₊ × [0, 1]`; each name then lies in its own factor, `x` in `ℝ₊` and `y` in `[0, 1]`. Any other `S`, such as a set that couples the two names, is refused under [`readable-form`](refusals.md#readable-form); a constraint that couples two controls is written in the feasible set of the maximization statement ([Constraints](../10-constraints.md) §1). |
| `x : ℝ × ℝ` | One field whose values lie in a product set. |
| `𝑞(x)` | A declared function applied to an argument. |

In a type, `(a,b)` is an open interval; in an expression it is a tuple. Brackets never declare a function's domain: a function is defined with typed arguments. [Equation parsing rules](../appendices/12-equation-parsing-rules.md) §3 gives the rules for functions and families.

#ambiguity #marginal-value #notation #todo #grammar #bellman-core
