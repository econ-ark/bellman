---
audience: user
type: reference
---
# Appendix C — From stage syntax to Bellman-calculus semantics

> [!summary]
> This appendix states the rules by which the equations of a stage file
> determine the mathematical objects of the Bellman calculus: which random
> variable each written name denotes and at which information set, which
> function of the state represents it, and how those functions compose into
> the stage's backward and forward operators. The rules are stated over the
> written expressions and the declared context, not over any parser or
> program, so that an economist can follow them by hand from a `.bl` file to
> the composed functions. Twelve rules, R1 to R12, state the account, and
> §4 applies them to complete stage files.

> [!info]- Relationship with other documents
> **Formal account** — [Stages and perches](../../bellman-calculus/03-Stages%20and%20perches.md): perches as information sets and the almost-sure function representation; [Fields, functions and types](../../bellman-calculus/04-fields%2C%20functions%20and%20types.md): the field diagram and the functional diagram; [Operators and builders](../../bellman-calculus/05-Operators%20and%20builders.md): the primitive operators the rules name.
> **Builds on** — [Stage syntax](../01-stage.md), [Equation parsing rules](12-equation-parsing-rules.md), and [Perch tagging rules](13-perch-tagging-rules.md): what may be written in a stage file.
> **Used by** — [Appendix D](15-appendix-d-node-tag-and-field-indexing.md): the `!node` mark and the addressing of statements; [Methodization](../04-methodization.md): numerical methods attach to the operators these rules produce.
> **See also** — [Operations](../reference/operations.md): the kinds `Pullback`, `Aggregation`, `Expectation`, `Argmax` and `Evaluation` of the operations a builder holds, which R7 and R8 name.

## 1 What the rules produce

### 1.1 Stages, perches, and fields

A **stage** is one step of a Bellman problem, read as a passage through
three states of knowledge. The agent arrives, learns what the pre-decision
shock reveals, decides, and continues, learning what the post-decision
shock reveals. The three states of knowledge are the **perches**: arrival,
written $\prec$; decision, written $\sim$; continuation, written $\succ$.
Formally each perch is a $\sigma$-algebra on one underlying probability
space $(\Omega, \mathcal F, \mathbb P)$, and the three are nested,
$\mathcal F_\prec \subseteq \mathcal F_\sim \subseteq \mathcal F_\succ$,
because the agent only ever learns more
([Stages and perches](../../bellman-calculus/03-Stages%20and%20perches.md) §3).

A **field** is a random variable on $\Omega$ that takes values in its
declared set and is measurable with respect to the $\sigma$-algebra of its
perch. Every name a stage file declares with a set and a perch is a field:
a state coordinate, a control, a value. The derivative of a value is no
field: a line reads it by the term `D_{a}V[>]`, the derivative of the
continuation value in the continuation coordinate `a` (§1.5, R8). A
**parameter** is classified as such by the complete context, including the
block headers;
it is constant with respect to the stage uncertainty. A **shock** is a
random variable supplied on an edge between two perches. Its law is declared
on a line of its own, `y ~ …`, and an expectation over a shock that has no
declared law is refused under `not-constructed`. The shock is drawn on one
edge, the edge of the forward block whose header lists it
([Shock distributions](../reference/laws.md) §1). A second forward block
that lists it is refused under `distribution-edge`. A later law of motion
therefore reads the realized shock through a state that the earlier law of
motion defines, such as `y_d = y`. The shock is available at the later perch and
is not assumed known earlier. This does not rule out a degenerate shock
that is already measurable earlier.

One name may be read at two perches. In a stage file `w` denotes cash on
hand at the decision perch and `w[>]` denotes cash on hand at the
continuation perch; these are two fields, two random variables, and they
are equal only when a statement says so. The perch marks `[<]`, `[~]`,
and `[>]` name the arrival, decision, and continuation perches; a field
at the decision perch is written bare, and `x[~]` is the same field as `x`
([Perch tagging rules](13-perch-tagging-rules.md)). The package reads
`x[~]` as the bare name `x` wherever it is written, and it does not yet
check that the name is at the decision perch (§5.3). On a backward line the
package does not yet read the bare name of a decision state when a state at
another perch has the same name: the line is refused under `name-in-scope`,
so such a decision state takes a name of its own, such as `w_d` (§5.3).

### 1.2 The state at a perch and the function representing a field

The **state vector** $X_p$ collects the declared state coordinates at perch
$p$, in their declared order, and takes values in the **state space**
$\mathsf X_p$. These are different objects: $X_p$ is a random variable,
whereas $\mathsf X_p$ is its set of possible values. A state space may be a
product or a labeled union of branch spaces.

To represent a field $Z$ by a function of $X_p$, require that $Z$ be
measurable with respect to the information generated by $X_p$, up to null
sets. Measurability at the perch $\mathcal F_p$ alone is insufficient if
$X_p$ omits relevant information. The state must also determine the
conditional laws needed for the stage. These are the relevant
**state-sufficiency assumptions**; they do not assert that the current
state reconstructs every earlier observation. The package does not yet
check these assumptions (§5.3).

For real-valued fields, and more generally standard Borel value spaces,
this gives a measurable representative $\mathrm z$ with
$Z = \mathrm z(X_p)$ almost surely. A standard Borel space is a measurable
space equivalent to a Borel subset of a complete separable metric space;
real domains and their finite products are examples. The functional
representation is the Doob–Dynkin lemma (Kallenberg 1997, Lemma 1.13).
Representatives agree almost everywhere under the law of $X_p$; the lemma
does not determine their values at states that have zero probability under
that law.

Thus a field $Z$, its representative function $\mathrm z$, and the value
$\mathrm z(x)$ at a specified state are distinct. A decision control chosen
as a measurable function of the decision state satisfies
$c = \pi(X_\sim)$, where $\pi$ is its **policy**. Before choosing a policy,
the control is retained as an argument of the transition and choice value,
$\mathrm g_\succ(x,c)$ and $Q(x,c)$. Their definitions on all feasible
state-control pairs cannot be recovered solely from observations under one
fixed policy. R5 states the additional domain requirement.

### 1.3 The typing context and the two graphs

The **typing context** $\Xi$ is the collection of everything the
declarations and block headers of a file assert: for each name its set,
its role, and its perch; for each declared function its formal arguments and
its body; for each shock its law; for each block its inputs, its outputs, and
the perches on its two sides. The letter is $\Xi$ because $\Gamma$ names a
feasible set in this documentation, as in [Constraints](../10-constraints.md).
Every rule below has the form *under
$\Xi$, the expression $e$ denotes the object such-and-such*; nothing
about an expression is decided from its spelling alone, and nothing is
decided from the identifier a statement or block carries.

The rules describe two related diagrams, the field diagram and the
functional diagram of the calculus, which the package constructs as the two
initial diagrams and the two builders graphs of a stage
([semgraph](../../wiki/semgraph.md)). In the **field diagram**, inputs and
outputs are typed fields and each operation relates the quantities in its
context. An implicit equation remains a relation rather than a directed
assignment to an already determined output. In the **functional diagram**,
state arguments, pullback along the law of motion, and operators on functions
are explicit. Both sides of each final equation remain available in both
diagrams, with the source equations and rules that justify their correspondence.
A pullback along the law of motion may use several field equations.

A function is not always an input value of the same type as an evaluated
field. For example, a transition has type
$\mathrm g_\succ : \mathsf X_\sim \times \mathsf C \to \mathsf X_\succ$,
restricted to feasible pairs, while a backward operator has type
$B_\succ : \mathcal V_\succ \to \mathcal Q$. Here $\mathcal V_\succ$ is
the chosen class of continuation functions and $\mathcal Q$ the class of
choice-value functions of state and control. Evaluating a member of
$\mathcal V_\succ$ at a state is a further operation.

In a categorical reading, an arrow has a specified input and output type;
composition connects matching types and preserves identities and order.
Products combine inputs, whereas a labeled union describes alternatives
(R3). Describing two diagrams does not by itself establish a **functor**, a
map between categories preserving identities and composition. R5 supplies a
conditional interpretation, with state choices, representative functions,
and analytic assumptions stated explicitly. It does not assert that the
field and functional diagrams are identical or that either recovers a unique
source spelling. See [Fields, functions and types](../../bellman-calculus/04-fields%2C%20functions%20and%20types.md).

The backward operator $\mathbb T$ is read from the value and policy
operations. The forward operator $\mathbb M_\pi$ uses the transitions,
laws, and a specified policy. Their exact relationship is given in R9.

### 1.4 The two written forms

A value statement can be written in two forms. In the **perch form** the
names denote fields and carry no state arguments:

```bl
V[<] = E_{y}(V)
```

In the **functional form** the state arguments are explicit:

$$
\mathrm v_\prec(b) = \int \mathrm v_\sim(y + R\,b)\,\mu_y(\mathrm dy).
$$

A stage file writes the perch form, and the rules derive the functional
form from it under the context $\Xi$; §4.4 carries one derivation
through in full. Where a functional-form spelling is admitted, it is read
under the same context and must determine the same functional diagram.
The displayed integral assumes $w=y+Rb$ and the conditional law specified
in §4.4. The perch form names fields; functional notation makes their
representatives and arguments explicit. A perch label alone does not change
a random variable into a function or an evaluated number (§1.2).

### 1.5 Notation

| Symbol | Meaning |
|---|---|
| $\prec, \sim, \succ$ | the arrival, decision, and continuation perches; $\mathcal F_\prec \subseteq \mathcal F_\sim \subseteq \mathcal F_\succ$ their $\sigma$-algebras |
| `x[<]`, `x[~]`, `x[>]` | the field named `x` at the arrival, decision, and continuation perches (§1.1) |
| `x` | the bare name: a control at the decision perch and a shock at no perch; otherwise the field that the block's header lists as `x`, at the perch that its listing gives it (§2.2), so that `b` in `w = y + b*R` is the arrival state where the arrival side lists `b`; a state that a backward line reads without a listing is the state at the one perch at which the stage places a state `x` |
| $X_p$, $\mathsf X_p$ | the random state vector and its state space; $x \in \mathsf X_p$ a specified state |
| $\mathrm g_\prec, \mathrm g_\succ$ | the declared forward transitions, $X_\sim = \mathrm g_\prec(X_\prec, \zeta)$ and $X_\succ = \mathrm g_\succ(X_\sim, c, \eta)$ |
| $\zeta, \eta$ | a pre-decision and a post-decision shock; $\mu_\zeta, \mu_\eta$ their declared laws |
| $V, V_\prec, V_\succ$ | value fields; $\mathrm v, \mathrm v_\prec, \mathrm v_\succ$ the functions representing them |
| `D_{a}V[>]`, $\mathrm{dv}_\succ$ | the derivative term: the derivative of the continuation value in the continuation coordinate $a$. It denotes $\partial_a \mathrm v_\succ$, a function of $\mathrm v_\succ$ and not a second object, which this page writes $\mathrm{dv}_\succ$; $\mathrm{dv}_\sim$ and $\mathrm{dv}_\prec$ are the derivatives of $\mathrm v_\sim$ and $\mathrm v_\prec$ in the state coordinate of their perch. No field is a marginal value. A line at an earlier perch reads the term at the state that the law of motion gives, as $\mathrm{dv}_\succ(\mathrm g_\succ(x, c, \eta))$. |
| $c, \pi$ | a control and the policy representing it |
| $Q(x, c)$ | the choice value: the objective represented with the control retained |
| $\mathcal C(x)$ | the feasible set of the control at state $x$ |
| $\mathbb T, \mathbb M$ | the backward and forward stage operators |

Sets are declared in the file with the glyphs of
[the symbol reference](../reference/symbols-conventions.md): $\mathbb R_+$ is
$[0, \infty)$ and $\mathbb R_{++}$ is $(0, \infty)$.

## 2 Syntax and the typing context

### 2.1 Declarations

A declaration is a name, a colon, and a type; a type is a set, a role word
prefixed by `!`, or a conjunction of them, written with `@` between them
in any order.
Several sets in one type declare their intersection, as in
`β : (0,1) @ (0, R^(ρ-1))`
([Symbols and conventions](../reference/symbols-conventions.md) §9.2).
Several sets are read on the declaration of one name on a line of its own,
outside the blocks. They are sets of numbers, none of them a set of labels
or a product, and at most one of them is not written as an interval with two
endpoints, such as `[1, inf)`. The glyphs `ℝ₊` and `ℝ₊₊` count here as sets
not so written, and two equal sets count as one: `θ : ℤ @ [1, inf)` is read,
and `θ : ℝ₊₊ @ ℤ` is refused under `syntax`. Two intervals with no number in
common, `(0,1) @ (2,3)`, are refused under the same rule. The package decides
this only between intervals whose endpoints are numbers or ratios of two
integers. Where the sets have no number in common and one of them is a
reserved set, a named set, a list of integers, a union or a difference, as in
`β : ℝ₊₊ @ (-2,-1)`, or an endpoint is a formula, as in `(2*1, 3)`, it reads
the declaration, and no calibration can bind the name (§5.3). A field listed in
a block header carries one set, and several sets there are refused under
`readable-form`.

```bl
β : (0,1)
w : ℝ₊
c : !ctrl @ ℝ₊
V : ℝ @ !vlu
y : Y
y ~ LogNormal(μ_y, σ_y)
Xm := ℝ₊₊
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
```

These are declaration forms, not a complete stage: the surrounding file
supplies `Y`, `μ_y`, `σ_y`, `ρ`, and the field perches. The complete context
distinguishes the parameter `β` from the state coordinate `w` and classifies
the controls and values.

A **derived parameter** is a constant that a definition without arguments
writes from the declared parameters, `h := 1/(1 - Γ/R)`
([Symbol conventions](../reference/symbols-conventions.md) §8). Its
definition may declare the set its value lies in, on the same line:
`q : (0,1) := (β*R)^(1/ρ)/R`. Calibration computes the value and refuses
parameter values at which it lies outside that set. A separate declaration
`q : (0,1)` beside the definition `q := …` is refused under
`one-name-one-meaning`. A definition that declares a set and whose value
reads no name, `ρ : ℝ := 2`, is refused under `readable-form`, since the
calibration supplies that number. The set that a definition declares is a
set of numbers, and any other set there is refused under
`derived-parameter`.

The definition of a derived parameter may call `log` and `exp`, each of one
argument, and `min` and `max`, each of one argument or more; a call of any
other function, or of `log` or `exp` with several arguments, is refused
under `derived-parameter`, or under `not-constructed` where a call of
another function is the whole right side. The definition may also be
written by cases, with or without a declared set:
`h := if Γ < R then 1/(1 - Γ/R) else 0` and
`q : (0, 3) := if β < R then 1 else 2` are both read
([Equation parsing rules](12-equation-parsing-rules.md) §2 gives the forms
of the test and of the branches). The conditional `if … then … else …`
stands as the right side of a derived parameter definition, the right side
of a block equation or a branch of another conditional. Inside arithmetic,
in a function's body and at a set endpoint it is refused under `syntax`.
The words `if`, `then` and `else` are no names: a file that writes one of
them as a name, in a declaration, a definition, a binder, a block header or
a formula, is refused under `syntax`. The package does not yet refuse one
written as the id of a line's annotation, `:: [id=if]` (§5.3). In a derived
parameter's definition `log`, `exp`, `min` and `max` are the functions of
the language, and a definition that calls one of them where the stage
defines a function of that name is refused under `derived-parameter`. A
test reads what a branch reads, parameters, derived parameters and finite
numbers: a set, a field or a function written there is refused under
`derived-parameter`, and a label of a finite set under `well-typed`, as a
label in arithmetic is.

The value of a derived parameter is its definition evaluated at the
calibration. For a definition by cases it is the branch that the test
chooses, and the other branch is not evaluated, so that the value of `h`
above is 0 at `Γ = R`. A branch written `inf` or `-inf` gives that
infinity, and the definition of a derived parameter computes with no infinity: a definition that
reads a name valued at an infinity where it is evaluated, in a formula, a
call or a test, as the branch that its test chooses or as its whole right
side, has no value, and the calibration is refused under
`derived-parameter` at that definition. A branch written `inf` or `-inf`
is admitted only in a definition whose declared set can hold that
infinity, as `ℝ_{+∞}`, `ℝ̄` and `(0, inf]` hold `inf`. A definition whose
declared set cannot hold it is refused under `derived-parameter` when the
file is read. The set ℝ, the declared set of a definition that writes none,
holds no infinity, so `h := if Γ < R then 1/(1 - Γ/R) else inf` is refused
and `h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else inf` is read. Whether a
set can hold the infinity is judged from its form, also for several sets in
one type and for a named set written with a bar: `ℝ̄ @ (0, inf]` can hold
`inf`, and `ℝ̄ @ (0, inf)`, `ℝ_{+∞} @ (0, 100]` and `{x : ℝ̄ | x < 100}`,
which exclude it by an open endpoint, by an endpoint that is a number and
by a condition, cannot. A condition `x <= e` excludes `inf` only where `e`
is a number, so `ℝ_{+∞} @ (0, 2*100]` is read and calibration refuses its
infinite value, while `(0, 2*100]` is refused when the file is read. A
union can hold an infinity that one of its members can hold. A difference
is judged by its left side alone, so a definition on `ℝ̄ \ [0, inf]` is
read, and calibration refuses its infinite value. Where the answer depends
on a calibrated value, as for `(0, T]`, the file is read, and calibration
holds the value, finite or infinite, to the declared set, as it holds the
value of every definition that declares a set.

The declared set of a parameter may be a union or a difference of sets of
numbers. `ρ : (0,1) \/ (1, inf)` declares that `ρ` lies in one of the two
intervals, and `ρ : ℝ₊₊ \ {1}` that `ρ` is positive and is not 1;
`A ∪ B` and `A ∖ B` are second spellings of `A \/ B` and `A \ B`. A union
and a difference are read in the declared set of a parameter, of a derived
parameter and of a setting, which a methods file declares
([Methodization](../04-methodization.md) §4). They are refused in the set
of a field, of a shock and of a function's argument, and they are not read
after `:=`, in the definition of a named set or of a set-valued function
such as `Γ(x : ℝ₊) := (0, x]`.

The set of a parameter or of a derived parameter reads parameters, derived
parameters, named sets and numbers, and the set of a setting may also read
settings. A derived parameter's set that reads a setting is refused under
`derived-parameter`. A shock is read inside an expectation over it where its
law reads no field. A set that reads a field, whether directly, through a
named set or through the law of a shock that an expectation in it
integrates, is refused under `readable-form`. An interval of numbers holds
at least one number, so `(2, 1)` is refused under `readable-form` when the
file is read. A difference holds at least one number as well. One whose left
side lies within its right side, as in `(0,1) \ ℝ₊`, is refused under
`readable-form` when the file is read, where the package can decide the
inclusion. A difference that is a member of a union is not judged.

An endpoint of an interval, or a side of a condition after the bar of a
comprehension, `{x : ℝ | x < T}`, that is the bare name of a parameter or
of a derived parameter valued at an infinity is read as that infinity,
whatever supplies the value. With `T : ℝ̄` calibrated at `inf`, the set
`[0, T)` is $[0, \infty)$, and so is the set of `debt : ℝ₊ @ [0, h)` where
the definition of `h` above, declared on `ℝ_{+∞}`, gives `h` the value
`inf`. A bound of a parameter's set may call `log`, `exp`, `min` and `max`,
which calibration evaluates as in a derived parameter's definition. A bound
that calls another function is not decided, also where it computes with an
infinity: calibration binds the value, and `stage.obligations()` lists its
membership in the set as required. A bound that calibration evaluates and
whose arithmetic has no value at the calibration, `1/(R-2)` at `R = 2`,
refuses the calibration, and so does one that computes with a name valued
at an infinity, as `2*T` and `-T` do at `T = inf`, or with the written
infinity, as `2*inf` does at every calibration.

A declared function binds its formal arguments: the `c` in the body of `𝑢`
is the function's own variable and not the control `c` of the stage (R4). The
operators `D_{c}` and `Inv` applied to a declared function denote its
derivative with respect to the named argument and its functional inverse,
under the assumptions R7 records. The subscript of `D_{c}` names one scalar
argument of the function: a subscript that names several arguments is
refused under `derivative-one-name`, and one that names a product-valued
argument under `derivative-scalar-coordinate`. The package does not yet
check that the subscript names an argument of the function (§5.3).

A named set may also be a comprehension, `H := {i : ℤ | i >= 0, i <= 1}`,
whose bound name `i` is local to the definition, as a formal argument is
local to its function. Marked `!categories`, a comprehension over ℤ, or
over ℕ with a lower bound of at least 1, whose conditions bound the name
below and above by integers written as numbers gives its
members category names
([Symbol conventions](../reference/symbols-conventions.md) §§9.2–9.3):

```bl
HouseholdStatus := {i : ℤ | i >= 0, i <= 1} :: [!categories household_status, newborn=0, old=1]
```

The declaration denotes the set $I = \{0, 1\}$ and its **category map**
$m_I : I \to C$, with $m_I(0) = (\kappa, \mathrm{newborn})$ and
$m_I(1) = (\kappa, \mathrm{old})$, a bijection onto the set
$C = \{(\kappa, \mathrm{newborn}), (\kappa, \mathrm{old})\}$ of the categories
the annotation names. Here $\kappa$ is the identifier written after the
marker, `household_status`, or, where none is written, the pair of the
SHA-256 digest of the stage text and the set's name, so that two stage texts
share categories only through an identifier. A field $n : \Omega \to I$
declared on the set takes integer values, and the random variable
$m_I \circ n$ is its category. Arithmetic on the codes has its usual meaning,
since every function $f$ of the code is the function $f \circ m_I^{-1}$ of the
category composed with $m_I$, so that the term `100 - 120*n` is 100 for a
newborn household and $-20$ for an old one; the coding, however, defines no
distance between the categories and gives no meaning to a number between two
codes. A category name is no term of the file, so `n_next = old` is refused
under `name-in-scope`, and the transition is written with the code,
`n_next = 1`.

A stage expectation requires a conditional law relative to its information
context. When the law statement supplies that conditional law, dependence
on earlier state fields must be retained. A constant conditional law implies
independence from that earlier information. A marginal distribution with
constant numerical parameters alone does not imply independence. The examples
below explicitly use the constant-conditional-law interpretation. A tuple
subject, `(Ψ, θ) ~ N(…)`, declares a joint law as one factor. Separate
declarations on one edge define the joint law of its shocks as the product of
the declared conditional laws, each given its named parent shocks and the
source coordinates: parent-free factors are conditionally independent given
the source coordinates, and two children of one random parent need not be.
The elaboration records the factorization as an assumption.

### 2.2 Blocks and their headers

A backward header gives the value-type fields taken in and sent back. The input names include continuation constants as well as any field maximized by the policy. `!vlu @ !cnst` marks a field whose value and declared domain are independent of states, shocks and choices. A repeated bare name on the two sides can keep the field without a defining equation. A marked and a bare name are different fields. A forward header lists an incoming constant where its law of motion or a shock law reads it.

A block is a bracketed header followed by statements:

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V      = 𝑢(c) + β*V[>]          :: [id=value]
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}
```

The word after a side names the information set of the coordinates listed
on that side, with three exceptions. A shock listed on a side is an edge argument, not a state coordinate
of that side. Its eventual measurability follows its timing (§1.1). A control is at the
decision perch wherever it is listed, because a control is chosen with the
decision information; listing it on a continuation side records that it is
available there, which it is, since $\mathcal F_\sim \subseteq \mathcal F_\succ$.
A constant that the stage takes in at its continuation perch stays at that
perch where the input side of a forward block lists it.
A side may omit its perch word only when every non-shock coordinate it
lists is placed without it: a control is at the decision perch, and any
other coordinate carries the mark `[<]` or `[>]` or a perch word in its own
type, as in `(w : !dcsn, c : !ctrl @ ℝ₊₊) -> (a : ℝ₊) : !cntn`. A bare name
is not placed by another block's listing of it; the perch of a name is never
guessed. A perch mark on a name must agree with what the context already
records, and a mark `[<]` or `[>]` that disagrees with the perch word of its
side is refused under `field-perch`, except the mark of such a constant. The package does not yet check the
mark `[~]`, which it reads as the bare name (§5.3). Sets written for the
same name at several places are intersected as described in §2.4. Where one
block writes a field and another reads it, the set written must lie in the
set read (§2.4).

The second line of the block is a **derivative line**: its left side is the
derivative term `D_{w}V`, the derivative of the value `V` the block writes
in the state coordinate `w` of its output perch, and the line states that
derivative (R8). It adds no field to the header and no output to the block.

The identifier after `id=` is an address. It names the block for the
methods file and for error messages, and it decides nothing about the
block's meaning (R1).

### 2.3 Statements and annotations

A statement is an equation, optionally followed by `::` and a bracketed
list of annotations. `[id=value]` gives the statement an address. A dotted
id, `[id=optimality.euler]`, instead attaches the statement to the line
`optimality` of its policy block as a property of that line: the statement
forms no operation and takes no address of its own
([Constraints](../10-constraints.md) §4.1). A dotted id is refused under
`readable-form` where its block writes no control, or where the line it
names is absent, is marked `!doc` or is itself a property. `!doc`
marks a statement as documentation. It defines no equation of the block's
operator, but its content may be retained as a condition. The binder of a
documentary maximization also declares the feasible set of its control, which
enters the control's type. `!node` marks a statement as an authored node, so that the
function it defines is an operator of its own for a method to address
([Appendix D](15-appendix-d-node-tag-and-field-indexing.md)). The mark
needs an id in the same annotation, `:: [id=disc, !node]`; without one the
statement is refused under `declared-once`. The marker
`!categories` is written only in the annotation of a named set of the form
of §2.1; on a statement, a block header or any other item it is refused
under `category-codes`. The clause
`⟂ m_d - c >= 0` after a decision-perch equation of a policy block gives a complementarity
condition with a specified residual sign (R10), using the law of motion
`a = m_d - c`. It is not unchanged when the equation's
two sides are exchanged. After an equation the clause may carry two bounds
on one quantity, `⟂ 0 <= c_p <= w_d`; after an inequality it carries one.
The body of a policy block may also declare a **multiplier**,
`μ[>] : ℝ₊ ⟂ a >= 0`: a name with the continuation mark, one declared set
and a clause with one bound. The declaration defines no equation; it adds a
coordinate at the continuation perch to the functions its block defines
there (R1, R10). A clause and a multiplier are written in a policy block.
The package does not yet check this: in another block it reads them, and
they enter no rule of that block's builder (§5.3).

### 2.4 Forming the context

The context is formed before any statement is read. Every declaration and
every block side contributes what it asserts about each name; a name's set
is the intersection of the sets asserted for it, so `c : !ctrl @ ℝ₊` on
one side and `c : ℝ₊₊ @ !ctrl` on another give the control the set
$\mathbb R_{++}$. The package computes the intersection of sets that are
written identically, of the sets `ℝ`, `ℝ₊` and `ℝ₊₊`, and of intervals whose
endpoints are numbers or infinity. It does not yet compute the intersection
of other sets, such as a named set `Z := ℝ₊₊` beside `ℝ₊₊`, and it then
records no set for the name (§5.3).

Where one block writes a field and another reads it, the set written must
lie in the set read. The policy block may write `c : ℝ₊₊ @ !ctrl` for a
transition that reads `c : !ctrl @ ℝ₊`. With the two sets exchanged, the
reading block declares the narrower set, and the stage is refused under
`set-mismatch`. The package does not yet check the inclusion where it
cannot decide it, as with an endpoint that names a parameter, or where the
control stands on the left side of a line marked `!doc` (§5.3). A field declared on a set
with category codes (§2.1) is declared on that set at every place that
writes a set for it, and another set at one of them is refused under
`category-codes`.

Two assertions that cannot both hold, such as two perches for one field
(`field-perch`) or two roles for one name (`one-name-one-meaning`), are an
error. Sets written for one field that have no value in common are such
assertions. The package does not yet check this, except between a block
that writes the field and a block that reads it (§5.3). A name whose set is
asserted nowhere is an error, not a parameter: a parameter exists only where
the file declares one. The package does not yet check this for a field or a
shock that a block header lists (§5.3); a name that a line reads and that
the file declares nowhere is refused under `name-in-scope`. A name that the file
declares with a set on a line of its own, and that no block header lists,
is a parameter, and a line of a block that writes it is refused under
`parameter-or-field`.

### 2.5 Binders, free names, and bound names

The formal arguments of functions and operator subscripts determine the
local variables of an expression. `E_{y}` integrates over the designated
shock, while `argmax_{c}` and `solve_{c}` specify a control or unknown within
their arguments. The binders of `argmax` and `solve` stand, in order, for
the fields that the left side of the line writes, and a binder may be a new
name, as `cp` is in `c = argmax_{cp : Γ(w)}(𝑢(cp) + β*V[>])`. The left
side's own names written in another order are refused under
`not-constructed`. Nested local variables refer to their innermost binder.
`D_{c}(𝑢)` identifies the formal argument of the declared function that is
differentiated; it does not bind unrelated occurrences of the stage control.
The package does not yet check that the subscript names a formal argument of
the function (§5.3).

Two kinds of dependence must be distinguished. The integration variable
introduced by an expectation is local. Its integrand's declared field
dependencies may include that shock indirectly: if `w = y + b*R`, the
field `V` represented by $\mathrm v_\sim(w)$ depends on `y` through `w`.
R5 exposes this dependence before R7 integrates it. An independently bound
parameter with the same spelling is not that shock. Expanding a function
must substitute its arguments without capturing a different local variable.

A name **free relative to an operator** is not bound by that operator. It
may still be random. In expectation over `Y`, quantities `R` and `K` remain
free unless another rule binds them. Holding them fixed in a conditional
integral requires the appropriate conditional law; it does not establish
that they are constant or independent of `Y`.

## 3 The rules

Each rule states the written form it governs, what the context supplies,
the object the form denotes, and the assumptions under which the denotation
holds or the condition under which the form is rejected. A rejection may identify conflicting declarations, an undefined operation,
or a construction for which the required context has not been supplied.
An analytic assumption is a condition needed for a stated interpretation;
it is recorded separately from the information that defines the model.
The reference page [Rules and their code](../reference/rules.md) lists, for
each rule, the functions of the package that implement it and check it, and
the refusals that the package raises when a file breaks it. Where the
package does not yet check a rule, this appendix says so at the rule, and
§5.3 lists each such rule.

### R1 Blocks and their headers

**Written form.** A block `[id=B, (inputs) : !p -> (outputs) : !q] { … }`
with its statements, as in §2.2.

**Context.** The header contributes the sets, roles, and perches of its
coordinates (§2.4). The statements are read in order (R2). A multiplier
declared in the body of a policy block (§2.3) contributes one more name, at
the continuation perch, with the role of a multiplier and its declared set.
It is a coordinate of the functions the policy block defines at that perch
and of no other function: it is no input or output of the block or of any
other block, no header lists it, and the functions the block reads keep
their own coordinates (R10).

**Interpretation.** A block denotes a typed relation between its inputs and
outputs. Explicit definitions give an operator; an implicit system gives one
only after the required solution or selection conditions are supplied.
Under R5 the block can denote an operator between the functions
representing those fields. What kind of operator it is follows from the
header and the roles of its outputs, never from its identifier:

| Header | Kind | Denotes |
|---|---|---|
| a state at $\prec$, possibly with a shock, to a state at $\sim$ | forward transition | $\mathrm g_\prec$, and the forward operator $\mathbb M_\prec$ (R9) |
| a state at $\sim$ with controls, possibly with a shock, to a state at $\succ$ | forward transition | $\mathrm g_\succ$, and $\mathbb M_{\succ,\pi}$ (R9) |
| value fields at $\succ$ (with controls) to value fields at $\sim$; a state at $\sim$ is a coordinate, while a state at $\succ$ is reached through the law of motion | backward block | the builder at a policy $\mathbb T_{\succ,\pi}$, which carries the continuation value function to the decision value function, $(\mathbb T_{\succ,\pi}\mathrm v_\succ)(x) = Q(x, \pi(x))$, where $Q = B_\succ(\mathrm v_\succ)$ is the choice value that the induced aggregator $B_\succ$ gives on state and control; the block's lines are read at the control that the policy gives, and where the policy block writes a maximization, the choice value on state and control is its objective ([Stages and perches](../../bellman-calculus/03-Stages%20and%20perches.md) §2; [Operators and builders](../../bellman-calculus/05-Operators%20and%20builders.md) §6; R5, R7, R8) |
| value fields at $\sim$ to value fields at $\prec$; a state at $\prec$ is a coordinate, while a state at $\sim$ or $\succ$ is reached through the law of motion | backward block | the arrival aggregator $B_\prec$ (R5, R7) |
| value fields at $\succ$ to controls at $\sim$; the lines read the derivatives of those values by derivative terms such as `D_{a}V[>]`, which the header does not list; a state at $\sim$ is a coordinate, while a state at $\succ$ is reached through the law of motion, apart from candidate lines indexed by continuation state | policy block | the policy $\pi$ (R8, R10) |

A header is the rank of the symbol its block adds to the stage signature, its
input sorts and its output sort ([The stage
term](../../bellman-calculus/APPX-C-STAGE-TERM.md#c1-the-signature-named) §1).
The backward symbols have ranks over the value-function sorts alone, so a
backward header lists the value fields it reads and writes, with the controls
at which its lines are read, and no state: the derivative of a value is
read by the term `D_{a}V[>]` and is no field of a header. A shock may also
be listed, as on any side (§2.2). The listing adds no input to the block's
builder. It lets a line read, outside an expectation, a shock drawn on the
edge between the block's two perches, where a later line of the block
integrates it, as in `W = η*V[>]` followed by `V = 𝑢(c) + E_{η}(W)`. A state of the
perch at which the block's output
stands is a coordinate of the output function and is not listed; a state of
its input perch is reached only through the law of motion (R5, R7). The
reason is the one [Fields, functions and
types](../../bellman-calculus/04-fields,%20functions%20and%20types.md)
§1.2 gives: a value field at a perch is measurable with respect to that
perch's state, so every coordinate of the state is already an argument of the
output, and a state of another perch is not. A header that lists a state
writes a rank the signature has no symbol for, and the term algebra holds only
the terms they admit ([Initial-algebra
semantics](../../bellman-calculus/APPX-B-INITIAL-ALGEBRA.md#b1-signature-and-term-algebra)
§1); it is refused under `header-coordinate` rather than read with the state
removed, since read by the rule that a header's inputs are the builder's wires
it would assert a wire of state sort that no builder produces, and the written
header would no longer determine the rank. A control is listed because the
lines are read at it: the block denotes the operator at the policy that
represents the control (R8), whose output is the value function on the
decision state alone, and the control remains an argument only of the choice
value that the written equation gives (R5) and of the law of motion. Forward
headers list the arguments of the law of motion, a map between state spaces.

A direct read of an input or later perch's state on any backward line is
refused, including a read in a relation or a condition after `⟂`: under
`input-perch-state` where no forward block between the two perches draws a
shock, and under `shock-observed` where one does. A read under an expectation
over the edge's shock is admitted, as
is the continuation-state indexing of a policy candidate line (R8, R10).

Two blocks with the same header and the same statements denote the same
operator whatever their identifiers; renaming every identifier consistently
throughout a file and its methods file changes no denotation. Changing a
header or a statement can.

Within a block, statements define outputs, introduce intermediate quantities,
or impose implicit relations (R10). An **output statement**
defines an output of the block. An **alias** is an operator-free statement
whose left side is neither an output nor the unknown of an implicit
statement (R10); it names an intermediate quantity and is substituted into
the statements that follow (R2). A statement marked `!doc` is
documentation. A statement marked `!node` is an output statement or alias
whose function is additionally an operator of its own. Every statement that
contributes an operation named in R7 (an expectation, a maximization, a
solution, an authored evaluation or envelope) retains that operation within
its expression. A method may address the occurrence without thereby
introducing another authored node.

The stage as a whole has as inputs the continuation value fields and the
arrival state, and as outputs the arrival value fields and the continuation
state. Its backward operator $\mathbb T$ carries the continuation value
functions to the arrival value functions, and its forward operator
$\mathbb M_\pi$ carries the law of the arrival state to the law of the
continuation state.

**Rejection.** An output that no statement determines is an error, unless the header keeps it by listing the same bare name on both sides (§2.2); a policy
block whose lines write the candidate at the continuation perch determines
its policy only by the line that identifies the control with the candidate
(R10). An input that a statement redefines is an error. The package does not
yet check this (§5.3). A second block between the same two perches whose
output side lists a field that another block writes is an error
(`one-builder-per-output`), and so is a second forward block, or a second
block that writes value fields, between the same two perches, even where it
writes another field (`forward-composite`). A coordinate whose set is declared
nowhere is an error (§2.4). The package does not yet check this (§5.3). A
multiplier is declared only in the body of a policy block. The package does
not yet check this (§5.3). A multiplier declaration is also an error when it
has no clause, a mark other than `[>]`, a clause of two bounds, or a bound
naming a control, a decision or arrival state or a candidate; so are a second
declaration of one multiplier and a header that lists a multiplier.

### R2 Ordered statements and substitution

**Written form.** Several statements in one block.

**Interpretation.** Explicit definitions are read in dependency order. An
alias is available after its defining statement; an implicit condition is
retained as a relation in its designated unknowns (R10), not used as an
assignment before those unknowns are determined. A block composes these
operations according to their inputs and outputs.

**Substitution.** Replacing an explicit alias by its defining expression
preserves the field relation wherever the operations are defined. An explicit
statement may also be solved for a name that occurs in it once and affinely,
with a coefficient that the declared sets show to be nonzero:
the result is an equation between the same fields, holding wherever the
statement holds, so that the transition `a = m_d - c` of §4.2 gives
`m_d = a + c`, and `a = R*m_d - c` with `R : ℝ₊₊` gives `m_d = (a + c)/R`.
For a name that occurs more than once, or not affinely, or with a
coefficient that the declared sets do not show to be nonzero, as under
`R : ℝ₊`, the
statement is not solved; R10 uses this rearrangement to check a coordinate
line against the transition, and makes no check where it does not apply. Resolve
bindings before substitution (§2.5). A shock dependence reached through an
alias or transition belongs inside the expectation containing that use of
the alias; a different locally bound variable with the same spelling does
not. A `!node` keeps its statement as an authored node. Dependency
analysis and mathematical substitution may still inspect its definition;
the mark does not conceal the shocks or controls on which its output depends.

**Assumptions.** The composing functions must be defined on the supplied
arguments and measurable when a probabilistic interpretation needs them.
Grammatical acceptance does not prove measurability, differentiability,
invertibility, or existence of a solution.

### R3 Product outputs

**Written form.** An output side with several coordinates,
`-> (k[>] : ℝ₊, b[>] : ℝ₊) : !cntn`; a tuple expression `(e_1, e_2)`; a
selection `(e_1, e_2)[d]`; a tuple left side `(i, b_n) = …`.

**Context.** The typing of a tuple subject follows the declared form:
`(w, c) : S` declares two fields when `S` is a product with one factor for
each name, written out or named, and each field takes its own factor, so
that `(w, c) : ℝ₊ × ℝ₊₊` declares `w` in $\mathbb R_+$ and `c` in
$\mathbb R_{++}$. A set that couples the names is refused under
`readable-form`; a constraint that couples a control with a state is written
on the binder of the maximization (R7). `x : ℝ × ℝ` declares one field with
values in a product, whose coordinates are reached by selection.

**Interpretation.** The output of a block whose side lists several
coordinates is the tuple of those fields, so the continuation state space of the
example is $\mathsf X_\succ = \mathbb R_+ \times \mathbb R_+$. Each
coordinate is defined by its own statement. A statement with a tuple left
side defines several outputs at once only where its right side is one
`argmax` or one `solve`, as in the joint choice of a policy block (R7, R10);
an ordinary tuple assignment, such as `(k[>], b[>]) = ((1-δ)*k_d + i, b_n)`,
is refused under `not-constructed`. The transition
$\mathrm g_\succ : \mathsf X_\sim \times \mathsf C \to \mathsf X_\succ$ has
one component per output coordinate. A component may itself be product-valued;
coordinate count alone does not determine a Euclidean dimension. A tuple expression denotes a finite family in the
written order; a selection `(e_1, …, e_J)[d]` by a control `d` valued in a
finite set of labels denotes $e_j$ when $d$ is the $j$-th label in the
order the set literal lists them. A collection declared on the functions
from a finite integer or label set, `δ : L_J → ℝ` with `L_J := {1, …, J}`, denotes at
each calibration one function on the members of that set, and `δ[j]` its
value at a key `j` declared within the index set, never a position;
`dist[j][i]` denotes the entry at the ordered pair, the first key on the
first factor. Integer keys identify entries whose values may be real numbers;
equal numerical outcomes at two distinct keys do not identify those keys.
The forward reading of a product output is
the joint law of the tuple (R9), not a product of marginal laws.

**Rejection.** A positional selection must be within the family. A
selection by a name reads a declared selector variable and never a label
written in the brackets, so that `(e_1, e_2)[work]` is refused even where
`work` is a member of a declared set. A selector variable must
have a compatible domain and scope: for a tuple, a finite set with as many
members as the tuple has entries, and for a collection on an index set, a
set within that index set. A selection outside these forms is refused under
`family-selection`, and on the value line of a branching block under
`branch-tuple-mismatch`. The family and its labels must agree
in length and order. A tuple of alternative value functions is distinct
from the labeled union of successor state spaces in §4.7.

### R4 Scope, binding, and information

Two questions must be kept apart. **Binding** asks which occurrences of a
name are bound by an operator (§2.5). **Determination** asks which fields a
block takes as given and which it defines (R1). A perch mark answers
neither: it asserts at which information set a field is measurable.

> [!important] A perch mark is not a binder
> In `V = 𝑢(c) + V[>]`, the continuation value is an input. Its
> representative is evaluated at the state supplied by the transition.
> Neither the mark nor the pullback along the law of motion binds the continuation
> function. In `V[<] = E_{y}(V)`, the shock is integrated after exposing
> its dependence in the integrand.

**Interpretation.** Information checks apply to each operation in its own
context, with local bindings and indirect dependencies preserved. An
explicit field definition must produce a quantity measurable at its stated
perch. On a backward line the construction asks for a function of the state
at that perch (§1.2): a state of an earlier perch is refused under
`forward-composite`, and a field of a later perch that is read across an
edge that draws a shock is refused under `shock-observed` unless it stands
inside an expectation over each shock drawn on the way. The package does not
yet check this for a shock that the header of a backward block lists and
that is drawn on an earlier edge or on no edge: the line reads it as known,
and the function that the line defines keeps the shock free (§5.3). An implicit
equation instead defines a relation to be solved under
the information available to its unknowns; it is not a claim that every
intermediate expression already has that measurability. Its two sides are
one relation (R10), and a term on either side that reads a field of a later
perch is read through the law of motion and, across an edge that draws a
shock, inside an expectation over that shock. The package does not yet check
this on the left side, for a term outside an expectation that combines a
field of a later perch, or its derivative, with other quantities, such as
`β*D_{a}V[>]` (§5.3).

Declared dependencies give a sufficient information bound, not necessarily
the smallest information set of the mathematical expression: a shock may
cancel algebraically. A construction that does not prove such cancellation
may report that the required measurability has not been established, but
must not assert that the expression is mathematically nonmeasurable for
that reason or insert an expectation. The package takes as declared
dependencies the shocks that the forward blocks between the two perches
list, whether or not a law of motion reads them, and it refuses under
`shock-observed` a field of the later perch that is read outside an
expectation over them. The message of that refusal says that the value is
not known at the earlier perch; the package does not yet word it as a report
that measurability has not been established (§5.3).

For example, at arrival `E_{y}(V + y)` integrates the designated shock in
both terms, whereas `E_{y}(V) + y` retains a free final `y`. If `y` is not
known at arrival, the latter is not an arrival-field definition. The mere
presence of an expectation elsewhere in the equation supplies no exemption.

**Consequence for the two written forms.** In the perch form the binders
are visible in the expression, `E_{y}` binding `y` and nothing else. In
the functional form the same information must be carried by the state
arguments: the integrand is written as the function evaluated at the state
that contains the bound shock, $\mathrm v_\sim(y + R\,b)$, and the free
names $b$ and $R$ appear as arguments or parameters (R5, §4.4).

### R5 Fields to functions

This is the central rule: it passes from a statement between fields to a
relation between functions of the state, and it records what the passage
assumes.

**Written form.** A statement `Z = F(Y_1, …, Y_n)` whose left side is a
field at perch $p$ and whose right side mentions fields $Y_i$ at perches
$q_i$ and parameters, after the aliases and declared functions of R2 have
been expanded, so that `F` is the function the expression denotes. The
package does not yet print the expanded expression on the card of a builder,
the record of the builder that `denote()` prints
([A piece](../API/stage/05-piece.md) §5), where the block writes an alias
before the output statement: the rule that the card prints for the output is
then the alias's line, while the function that the operation computes is the
expanded expression (§5.3).

**Context.** The state arguments, the declared transitions, the functions
supplied as inputs, and any recovery maps for earlier quantities needed as
functions of the chosen state.

**Interpretation.** Require:

- (A1) each input field has a representative on its declared domain,
  $Y_i = \mathrm y_i(X_{q_i})$ almost surely. For fields being constructed,
  establish the required state sufficiency (§1.2).
- (A2) a later state is supplied by the declared measurable transition
  $X_{q_i} = \mathrm t_i(X_p,c,\xi)$, where $c$ collects retained controls
  and $\xi$ the shocks on that transition. At the same state, $\mathrm t_i$
  is the identity.
- (A3) an earlier quantity used as a function of the current state has an
  explicit representation in the available arguments, which a line of the
  file supplies. A field whose name is a coordinate $x$ of perch $p$, written
  with the mark of another perch $q$, denotes that coordinate read at $q$,
  and in a policy block a line `x[q] = e` supplies the map $\mathrm r_x$, the
  function `e` denotes at $q$, from the state at $q$ to the coordinate $x$
  of $p$. Under the continuation mark, $x$ is a state of the decision perch,
  and a line there for a state of another perch is refused under
  `candidate-coordinate`. In a value block or an arrival block the line
  supplies no map: under the arrival mark it is retained as a relation that
  no operation realizes, which `stage.obligations()`, the list of the
  conditions the stage records, holds as `retained-relation`, and under the
  continuation mark it is refused under `input-perch-state`. In the
  consumption stage of §4.2, `m_d[>] = a + c[>]` supplies the decision
  coordinate read at the continuation perch, the coordinate map
  $\varphi(a) = a + \mathrm f(a)$ of R8; (A2) supplies the reading in the
  other direction, a later state read at an earlier perch through the
  transition. Inclusion of earlier information in $\mathcal F_p$ does not
  make a non-injective transition invertible or ensure that the current
  state retains that quantity.

With no remaining shock arguments, pointwise composition gives
$$
\mathrm z(x,c)=F\bigl(\mathrm y_1(\mathrm t_1(x,c)),\ldots,
\mathrm y_n(\mathrm t_n(x,c))\bigr).
$$
Here the appropriate argument map for each component includes any recovery
map required by (A3). With shocks present, retain them as explicit arguments
until the authored operator integrates them using R7. Their appearance
alone does not prove that the final expression depends on them: cancellation
or degeneracy may remove that dependence (R4).

The control is retained until a policy is specified. In a deterministic
consumption transition, the written value equation gives
$$
Q(x,c)=\mathrm u(c)+\mathrm v_\succ(\mathrm g_\succ(x,c)),\qquad
\mathrm v_\sim(x)=Q(x,\pi(x)).
$$
The second operation evaluates the first at a policy; a discount factor
appears only when authored. For a stochastic transition, an expectation
must occur at its written position, not be inserted by substitution.

> [!warning] Evaluation must be specified
> `E_{η}(V[>])` integrates a field whose representative is evaluated at
> $\mathrm g_\succ(x,c,\eta)$. Thus the integrand is
> $\mathrm v_\succ(\mathrm g_\succ(x,c,\eta))$. An operator on functions
> could be defined separately, but these rules do not interpret an
> unqualified $\mathbb E_\eta\,\mathrm v_\succ$ as that evaluation.

**Implicit dependence.** If a substituted argument depends on the output
being determined, the substitution produces a residual in that unknown.
It does not fail; it gives the implicit relation of R10. The package does
not yet read the statement in this way where its left side is the bare
control and the dependence enters through an alias (§5.3). An alias such as
`z = c[>]` can describe dependence on an undetermined control without
itself supplying an equation that determines that control.

**A statement across two perches.** A statement `Y = Z` whose left side is
at perch $p$ and whose right side is at perch $q$ denotes one relation, and
the relation may be rewritten at either perch by putting for the other
side's state its representation there, the transition of (A2) or the map of
(A3). Rewritten at $q$ it reads $\mathrm y \circ \mathrm r = \mathrm z$ on
the state at $q$; rewritten at $p$ it reads
$\mathrm y = \mathrm z \circ \mathrm g$, which contains the unknown when
`Z` depends on it and is then the implicit form of R10. Where the map and
the transition are consistent (R10), the two rewritings denote the same set
of pairs, each substitution reversing the other. No unknown is assigned, so
R2's rule that an implicit condition is retained as a relation stands; the
construction rewrites the relation at the perch whose map contains no
unknown. The package does not yet do this for every such statement (§5.3).

**Where the equality holds.** An almost-sure field equality determines
representatives only almost everywhere under the relevant state law. A
written formula or supplied continuation function may instead specify a
pointwise function on a declared domain. Use those domain-defined functions
for policy comparisons, new initial distributions, and transition
substitution. Almost-everywhere equality under one distribution alone does
not justify substitution at states to which a different policy assigns
positive probability. Retain the representative/domain choices or establish
that the changed law does not give positive probability to the exceptional
set. Neither diagram silently upgrades an almost-sure identity to a
pointwise one.

### R6 Well-formedness

Five checks apply to every statement. The first two check the declarations:
the first records the conditions that the declared sets leave open, and the
second finds contradictions between roles. The third and fourth check
whether the supplied context justifies the claimed field interpretation. The
fifth finds blocks that determine less than they promise.

1. **Domain.** Every name has a set (§2.4). The package does not yet check
   this for a field or a shock that a block header lists (§5.3). A function applied to
   an argument whose set is not known to lie in the declared set of its
   formal argument is not refused: the stage records the condition
   `function-argument-domain-inclusion`, which `stage.obligations()` lists
   as required and calibration does not decide.
   `𝑢(c)` with `𝑢(c : ℝ₊₊)` and `c : ℝ₊` records one, and the file removes it
   by declaring the control in $\mathbb R_{++}$. A restriction that the
   declared sets do not state is recorded as a condition as well, and
   calibration decides it where it reads parameters alone:
   the body `c^(1-γ)/(1-γ)` under `γ : ℝ₊` records that $1 - \gamma$ is not
   zero, which a calibration at $\gamma = 2$ establishes, and a calibration
   at $\gamma = 1$ is refused. A declared set can state such a restriction:
   under `γ : ℝ₊₊ \ {1}` a calibration at $\gamma = 1$ is refused as a value
   outside the declared set. A restriction that reads a state, a control
   or the argument of a function stays required and is not checked.
2. **Role.** A name has at most one role. A control is at the decision
   perch. A value field carries `!vlu`; the derivative of a value is read
   by a derivative term and has no role. A shock has a law or the word
   `!shck`.
3. **Information.** Apply the local rules of R4 and R7 to explicit
   definitions. An unresolved shock or a missing current-state
   representation requires additional context, an authored operation, or
   a diagnostic. Algebraic cancellation can justify more cases than a
   conservative dependency check establishes.
4. **Scope.** Resolve every reference to a declaration, a local definition,
   or a binder. A bare name that resolves to none of them is refused under
   `name-in-scope`. A call of a function that the file does not declare,
   such as `log(c)` or the misspelling `𝑢𝑢(c)` beside a declared `𝑢`, is not
   refused: it is read as a function supplied from outside the file, the
   stage records the conditions `external-callable-signature-and-provider`
   and `external-callable-result-domain`, and the stage's diagnostics,
   `stage.diagnostics()`, list the call under `external_calls`. On a
   backward line the package does not yet resolve the bare name of a
   decision state where a state at another perch has the same name, and it
   refuses the line under `name-in-scope` (§1.1, §5.3). A field that a
   forward block reads is listed in its header or defined earlier in the
   block. So is a value field or a control that a backward block reads, and
   a shock that it reads outside an expectation over that shock. A backward
   block lists no state: it reads a state of the perch of its output without
   a listing, and a state of its input perch only through the law of motion
   (R1). Using a field still requires the appropriate state
   representation. For example, knowledge of decision `w` does not make
   `w[>] = w` a function of the saving state `a` without a recovery
   relation. Check references and selections inside functions and
   distribution declarations too.
5. **Boundary.** Each required output has an explicit definition or a
   justified relation in its unknowns. Several coupled conditions must be
   treated as a simultaneous system, not competing assignments. A declared
   output port or an empty body supplies no defining relation.

**Inconsistency and assumption.** Distinguish an inconsistent declaration
from a missing rule or premise; do not call an unproved analytic property a
contradiction. Sufficiency (A1), integrability (R7), existence and measurable
selection of maximizers and roots (R8, R10), uniqueness where required, and concavity where a
first-order condition is used are assumptions; the rules record them beside
the operator that needs them and do not verify them.

### R7 The operations a line writes

A block's operator is composed from five operations that its lines write,
each with its own mathematical requirement. The
[primitive operators](../../wiki/operator.md) of the block's
[builder](../../wiki/builder.md) hold
them; a maximization written on a line not marked `!doc`, for instance,
stands in an operation of the kind `Argmax`, and the residuals of a
solution in an `Aggregation` (R8, R10).

**Application.** Arithmetic and the application of a function, `𝑢(c)`,
`log(c)`, act pointwise and preserve the perch of their arguments. A
function that the file does not declare, such as `log`, is read as a
function supplied from outside the file, under the conditions that R6
names. `D_{c}(𝑢)` denotes the derivative of the declared function with
respect to its named argument and assumes differentiability. The package
does not yet check that the subscript names an argument of the function
(§2.1, §5.3). It does not yet record the assumption of differentiability
as a condition of the stage (§5.3). `Inv(𝑑𝑢)`
denotes the functional inverse and assumes that the function is a bijection
between the declared set of its argument and its range; for the marginal utility
of power utility with strictly positive risk aversion, $\mathbb R_{++}$
onto $\mathbb R_{++}$. The stage records this assumption as the condition
`inverse-function-domain`.

**Expectation.** Interpret `E_{ζ}(e)` in its current conditioning context
$\mathcal G$. For an outermost arrival-value equation this is
$\mathcal F_\prec$; nested integrations must retain their own still-free
arguments and conditional laws. Suppose $e=F(X,\zeta)$, with $X$
$\mathcal G$-measurable, and the specified kernel $K_\zeta$ satisfies
$\mathbb P(\zeta\in A\mid\mathcal G)=K_\zeta(X,A)$ almost surely for
measurable sets $A$. A **probability kernel** assigns a distribution to
each conditioning argument and depends measurably on that argument. Then
$$
\mathbb E[F(X,\zeta)\mid\mathcal G]
=\int F(X,z)\,K_\zeta(X,\mathrm dz)\quad\text{almost surely},
$$
for a measurable integrable $F(X,\zeta)$ (Kallenberg 1997, Theorem 5.4).
The specified kernel and its dependence on $X$ are necessary premises.
Standard Borel shock spaces support regular conditional distributions;
the chosen state must still suffice to parameterize the required law.

The integral binds $z$. Other free quantities must be part of the supplied
conditioning context or remain explicit dependencies of an enclosing
operation. They are not automatically independent or deterministic.
`E_{Ψ,θ}` uses the joint conditional law; successive integrations use its
conditional factorization, in which separately declared parent-free shocks
are conditionally independent given the source coordinates. The same
left-side perch cannot be assigned to every inner expectation without
checking those contexts.

The elaboration selects that conditional law at each occurrence. Let $R$ be
the shocks the integrand still depends on, $H$ the shocks earlier
occurrences on its paths have integrated, $S$ the shocks the occurrence
names, and $A(S)$ the shock arguments and other subject components of the
declarations of $S$. The occurrence conditions on
$C = ((R \setminus S) \cup A(S)) \setminus (S \cup H)$ and the source
coordinates, and uses the law of $S$ given $C$ derived from the joint law of
the edge whose law of motion the block substitutes: a declared conditional, a product of declared conditionals in
dependency order, or a marginal or conditional of a joint normal declaration
whose conditioning covariance block is positive definite. Every shock of
$S$ is drawn on that edge: an expectation over a shock that another edge
draws, or that no edge draws, is refused under `distribution-edge`. The
result of the occurrence is a
function of the source coordinates and $C$, and the shocks of $S$ outside
$C$ join $H$. At a pointwise combination, remove from the combined history
the shocks on which any genuine sibling value input still depends. A later
explicit arithmetic read is refused only if its shock remains in this
history (`shock-reintroduced`). Any other conditional, a posterior among them, is
refused (`conditional-not-declared`). Under `ν ~ N(κ_1, σ_ν^2)` and
`Ψ ~ LogNormal(ν, σ_Ψ)` the order `E_{ν}(E_{Ψ}(·))` uses the law of $\Psi$
given $\nu$ and then the marginal of $\nu$; the reversed order would need the
law of $\nu$ given $\Psi$ and is refused. In the objective of a policy block
the package does not yet refuse the reversed order under this rule: it
refuses it under `shock-observed` (§5.3). A block output depends on no shock,
and every shock of the edge is integrated on each path to it
(`shock-observed`).

For finite real-valued results require the relevant integrals to be finite.
Nonnegative or one-sided-integrable expressions can also have extended-real
conditional expectations, provided that extended values belong to the
output domain and subsequent arithmetic does not form undefined
expressions such as $+\infty-\infty$. A sum with a term $-\infty$ and no
term $+\infty$ is $-\infty$, the value of an infeasible point. These are
analytic requirements, not consequences of the operator's syntax.

**Maximization and maximum.** With feasible controls $\mathcal C(x)$ and
choice value $Q(x,c)$, `argmax_{c}(e)` names at each state $x$ the maximizer
set of the display below, and the line that writes it denotes the set of
maximizing policies (R8). A policy, where one is required, is a measurable
selection from the maximizer set,
$$
\pi(x)\in\operatorname*{arg\,max}_{c\in\mathcal C(x)}Q(x,c).
$$
The binders stand, in order, for the fields that the left side of the line
writes (§2.5). A line whose binders and left-side fields differ in number is
refused, under `well-typed`, or under `output-defined` where an output of
the block is thereby left without a definition.
A feasibility correspondence can specify a product of sets or a product
restricted by conditions, as [Constraints](../10-constraints.md#1-three-kinds-of-constraint-and-where-each-is-written)
§1 shows. A call `Γ(x)` substitutes `x` for the definition's formal argument
in every factor and condition, while the member named by a comprehension
remains bound. Thus a triple constrained by `q[1] + q[2] = z` becomes a
triple constrained by `q[1] + q[2] = x` at that call. Its result values are
still triples, with the equality retained as a restriction on the whole
product; neither the formal argument `z` nor the bound member `q` becomes
an additional free state coordinate.

The operation of the kind `Argmax` that a line not marked `!doc` forms has
as its output the set of maximizing policies, the measurable policies that
select a member of the maximizer set at every state; the set may be empty or
hold several policies. The closing `Evaluation` of the policy builder
selects no member of it, and the selection is the numerical method's. The maximum value
$\max_{c}Q(x,c)$ may be well-defined without a unique maximizer or a
chosen policy. Nonempty compact feasible sets and
upper semicontinuity in the control ensure attainment; measurability of a
selection requires additional conditions on the state dependence.

> [!note]- Technical details
> One sufficient measurable-maximum theorem uses a separable metric control
> space, a weakly measurable feasible correspondence with nonempty compact
> values, and an objective measurable in the state and continuous in the
> control. Weak measurability means that the states whose feasible set
> meets each open control set form a measurable set. Under these hypotheses
> the maximizer correspondence has a measurable selection (Aliprantis and
> Border 2006, Theorem 18.19). Pointwise attainment alone is insufficient.

Where several maximizers exist, keep the selection requirement explicit;
the syntax supplies no automatic tie-break.

**Solution.** `solve_{c}(r_1, …, r_k)` denotes the relation of feasible
unknowns satisfying every residual equation. The package does not yet form
this relation for one unknown with two or more residuals: it reads such a
line without a refusal, and the rule of its operation holds no residual
(§5.3). A unique solution gives a
single-valued map; several solutions require a specified selection to
produce one. In either case measurability is an additional requirement.
Existence, selection, and optimality are separate questions (R8, R10).

**Evaluation.** Evaluation of a given function at a point is ordinary
application. Finite pairs `(knots, values)` determine a function only on
their listed coordinates, with repeated coordinates permitted only when
the values agree. They do not uniquely determine a function between knots.
The form `evaluate(knots, values, x)` therefore requires a stated numerical
representation, including interpolation and any extrapolation, before it
has a numerical value off the knots. For exact candidate/coordinate maps,
evaluation instead uses the function determined by their relation under
R10. Keep this exact interpretation distinct from its tabulated approximation.

**Levels of detail.** When the required conditions determine a block's
operator, its statements describe the constituents of that operator, and
the occurrences of the operations above
inside the statements are the finest constituents. A numerical method may be
attached to the block, to a declared function, to a statement marked `!node`
or a line that has an id, or to an occurrence;
the choice of level is the methods file's, and it does not change what the
block denotes. Every mathematical operation remains present at its appropriate detail,
including within an unmarked equation. Only `!node` creates a separately
authored node; a method's convenience does not create a
new authored equation or place.

**The result of an occurrence.** An occurrence of an operation inside an
unmarked equation, `E_{η}(V[>])` in the line `V = 𝑢(c) + E_{η}(V[>])` of a
backward block whose header lists the control `c`, receives a function of the arguments the
equation has bound so far and returns a function of the arguments that
remain. The block's builder is the operator at a policy (R1), so the
integrand is $\mathrm v_\succ(\mathrm g_\succ(x, \pi(x), \eta))$ and the
result is a function of the decision state $x$ alone; the same occurrence
in the objective of the policy block, `c = argmax_{c}(𝑢(c) + E_{η}(V[>]))`,
returns a function of `(x, c)`. The statement's aggregation reads that
result as its value input, and whether it is affine in that input is a
property of the statement, never a condition of construction. That result
exists in the composed
operator, because the occurrence is one of the operations above and has its
own domain condition; it is not an authored object. Only the operation's own
methods attach to it (a quadrature rule to an expectation, a maximizer to a
maximization, a root finder to a solution), and nothing may represent it: its
value is obtained exactly, through its definition, wherever the equation
reads it. A representation, an interpolant or a table on a grid, attaches
only to a declared function, a builder output, a statement marked `!node`,
a line that has an id, where it represents the function that the line
defines, or an authored `evaluate`, where the representation is the method
by which that evaluation is computed; an author who wants
the expectation held as an object writes it on its own line and gives the
line an id or marks it `!node`. The two questions are therefore separate:
whether a function exists as an object is decided by the source (the block
outputs, the `!node` marks and the ids of lines), and whether an existing object is exact or
an approximation is decided by the methods file, with exact as the default.
Attaching a method to an occurrence, a quadrature rule to `E_{η}(·)`, does
not make the occurrence a node: a sub-builder is created by `!node` alone,
whether or not the marked line cuts off an expectation, and a method's attachment changes neither the graph nor what
the occurrence is.
#functional-semantics

### R8 Evaluation and policy

A stage's one policy is the rule in the policy block. A maximization objective must match exactly one decision field's right side after the bound candidates are aligned with the control names, including the declared label order of selection tuples. When the rule is an explicit or implicit equation, it determines the same one policy without an objective comparison. The block `cntn_to_dcsn` evaluates all of its fields at the policy.

Three operations are easily confused and must be kept distinct.

**Evaluation at a policy.** Given the choice value $Q(x, c)$ and a policy
$\pi$, the decision value function is
$\mathrm v_\sim(x) = Q(x, \pi(x))$. No optimality is involved; this is the
policy operator $T_\pi$ of Sargent and Stachurski, and it is what a stage
computes when the policy is given from outside.

**Maximization.** A line `c = argmax_{c}(…)` denotes the set of maximizing
policies: the measurable policies $\pi$ with
$\pi(x) \in \arg\max_{c \in \mathcal C(x)} Q(x, c)$ at every state $x$, which
are the measurable selections from the maximizer set of R7. The set may be
empty or hold several policies. Under the assumptions of
R7 it holds a policy, and evaluation at a policy in it gives
$\mathrm v_\sim(x) = \max_{c} Q(x, c)$. The two steps together
are the maximum; the calculus writes them as evaluation composed with
selection
([Operators and builders](../../bellman-calculus/05-Operators%20and%20builders.md) §7).
The stage states the set, and the selection is the numerical method's (R7).

**Solution of a first-order condition.** A `solve` statement or an
implicit statement (R10) determines $\pi(x)$ as a root of a residual
$r(x, c) = 0$. Existence and an appropriate measurable root selection are required.
Uniqueness is one sufficient way to determine that selection. The root
yields an optimizer only with additional conditions, such as a differentiable
concave objective on a convex feasible domain and the appropriate first-order
conditions; strict concavity supplies uniqueness when a maximizer exists. An
equality residual states the interior condition; where the control's bound
can bind, the file must state the corner condition, by the clause `⟂` of
R10 on the first-order condition, by the clause on the continuation-marked
candidate line, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>]) ⟂ a >= 0` (§4.5), by a multiplier declared in the policy
block with the clause on its declaration (R10), or by a separately declared
branch, or the statement determines the policy only on the region where the
interior condition has a solution.

**The endogenous-grid policy.** In a policy block whose header names the
continuation value `V[>]` and whose lines read its derivative by the term
`D_{a}V[>]`, the continuation-marked candidate lines read the
continuation state `a` as their coordinate. Such a line writes a control
under the continuation mark, `c[>]`, a state of the decision perch under the
mark, `w[>]`, or the value candidate that an `upper_env` of the block
compares (R12); a line that writes another name under the mark is refused,
as `z[>] = 2*c[>]` is under `candidate-coordinate`. The statements
`c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])` and `w[>] = a + c[>]` define two fields at the
continuation perch, represented with respect to $a$ by the **candidate**
$\mathrm f(a) = \mathrm{du}^{-1}(\beta\,\mathrm{dv}_\succ(a))$ and the
**coordinate map** $\varphi(a) = a + \mathrm f(a)$. The final line
`c = c[>]` states the identification of the control with the candidate.
Read at the decision perch it is an implicit equation in $c$ at the saving
$a = w - c$ (R10); rewritten at the continuation perch through the
coordinate map (R5), it states $\pi(\varphi(a)) = \mathrm f(a)$, the
control at the cash on hand $w = \varphi(a)$ equal to the candidate there.
Under R10's consistency and single-valuedness conditions the two readings
give the same policy on the represented decision domain. A block that
omits the final line determines no policy and is refused (R1). A line that
writes a candidate which no later line of the block reads is refused under
`candidate-read`; the coordinate line, `w[>] = a + c[>]`, needs no reader. If $\varphi$ is injective,
this policy can be written $\pi = \mathrm f \circ \varphi^{-1}$; injectivity
is sufficient but is not the general condition. The
tabulation of $(\varphi(a_i), \mathrm f(a_i))$ on an asset grid and the
interpolation between the points are the numerical method's approximation of
this composition; they are not operations of the stage. An authored
`c = evaluate(w[>], c[>], w)` expresses evaluation of the determined
relation where such a functional interpretation is supplied. With finite
tables, it instead evaluates the chosen approximation (R7). The package does
not yet construct either of these readings: it reads the line and records
its rule without a definition of `evaluate`, also where the methods file
types a representation at the line (§5.3).

**Marginal values.** A marginal value is the derivative of a value and no
field: a line reads it by the derivative term, `D_{a}V[>]` for the
derivative of the continuation value in the continuation coordinate `a`,
which denotes $\partial_a \mathrm v_\succ$, written $\mathrm{dv}_\succ$ on
this page, a function of $\mathrm v_\succ$ and not a second object. The
value functions are read on the domain of locally Lipschitz functions on
the declared set, on which the one-sided derivative exists everywhere and
the derivative is single-valued almost everywhere and set-valued at a kink,
as a value with a discrete choice downstream is at its switching points;
differentiability at the point a line reads is a condition the rules
record, not a type. The package does not yet read a derivative in this way:
it defines the derivative as the limit of the difference quotients, a single
number, and it records no condition at a line that reads a derivative
(§5.3). `stage.obligations()` lists differentiability only for a derivative
line, under `marginal-reading`, and for a policy builder under the
endogenous grid method, under `egm-eligibility`. A derivative line (§2.2), `D_{w}V = 𝑑𝑢(c)` in the
value builder's block of the stage file, or the same line in the block of
the methods file that names the builder's block by its id,
`[id=cntn_to_dcsn]`, states the derivative of the value the builder
writes, in the state coordinate of the perch at which
that value stands. It is the author's assertion about that value, an
identity that holds under the envelope conditions, and not the definition
of a new field; it proves nothing. Under an envelope theorem's hypotheses,
the derivative of an optimized value is obtained from the objective's state
derivative, with any state-dependent constraints treated correctly
(Benveniste and Scheinkman 1979). Differentiability and interiority alone
are not a general formula for that derivative.

For $Q(w,c)=\mathrm u(c)+\beta\,\mathrm v_\succ(w-c)$, the interior
Euler condition and a valid envelope theorem give
$\mathrm v_\sim'(w)=\beta\,\mathrm v_\succ'(w-\pi(w))=
\mathrm u'(\pi(w))$. This justifies the example's `D_{w}V = 𝑑𝑢(c)` under
these conditions: concavity of the continuation value; interiority of the
maximizer or, at a binding constraint, the multiplier's term as the
Kuhn–Tucker clause states it; differentiability of the reward in the
control; uniqueness or a measurable selection of the policy; and
differentiability of the value at the point read (Milgrom and Segal 2002;
Clausen and Strub 2020). Other rewards, transition derivatives, or binding
constraints need their own derivative line. No term and no role supplies a
formula that is absent from the written lines: nothing is differentiated,
and the only analytic source of a derivative is a line the author writes.

**The lines of a solution method on the policy builder.** A stage file may
write its policy block with the maximization alone and leave the
computation to its methods file, whose block `policy` types a solution
method on the policy builder and brings the method's lines
([Methodization](../04-methodization.md) §5). Those lines are read by these
rules as the lines of a stage block are, with the stage's declarations in
scope: for the endogenous grid method (Carroll 2006), the candidate lines
of the endogenous-grid paragraph above, the candidate line carrying the
clause of R10. Their operations are the **rows** of the operative policy
builder, `stage.builder`; the declared builder, `stage.declared`, and the
initial diagram keep the maximization, which the builder's card prints
under `Declared` as the line whose policy the rows are to compute.
The rows reach it only under a condition that the stage records and nothing
checks, listed by `stage.obligations()` under the method table's name for
it: for the endogenous grid method, `egm-eligibility`, that the continuation
value $\mathrm v_\succ$ is concave and continuously differentiable on
$(0,\infty)$ with a finite positive right derivative at zero. Under it the
candidate $\mathrm f$ is continuous and nondecreasing, the coordinate map
$\varphi$ is strictly increasing from $\mathrm f(0)$ to infinity, and the
policy is $\mathrm f \circ \varphi^{-1}$ at cash on hand of at least
$\mathrm f(0)$ and the whole of cash on hand below it (§4.5). The package
does not yet record such a condition for another solution method: under
`!time_iteration` or `!explicit` the method's lines stand in place of the
maximization, and `stage.obligations()` lists no condition under which they
compute its policy (§5.3).

**Derivative lines of the methods file.** Where the stage file writes no
derivative line, the author writes it in the methods file, in a block that
names the backward value builder's block by its id and carries no
signature. The block's lines are derivative lines of the value that builder
writes, `D_{w}V = 𝑑𝑢(c)`. Each line is recorded at the builder's Evaluation
as a stated derivative, beside the method that represents the value; it
adds no wire and no box, and the builder's signature is unchanged,
$(\mathrm V_\succ) \mapsto (\mathrm V)$, whether the line is added or not.
Nothing is differentiated: each line is a line the author wrote, and its
reading as the derivative of the value the builder writes is the author's
assertion, which `stage.obligations()` lists as `marginal-reading` and
nothing checks. How the derivative of a value is evaluated is a property of
the value, fixed where the value is built: by the stated line, whose values
the representation at the builder's Evaluation stores, or by the
representation of the value itself; the methods file types that
representation at the Evaluation, `cntn_to_dcsn.evaluate` for the value and
its stated derivative together, or `cntn_to_dcsn.evaluate[D_{m}V]` for the
derivative alone. A block that reads `D_{a}V[>]` declares that reading and
nothing else; it knows only that the value it reads is a function. At a
constrained choice the line is read at the policy, where the multiplier of
the constraint is the residual of the first-order condition. For
$Q(w,c)=\mathrm u(c)+\beta\,\mathrm v_\succ(w-c)$ with the bound
$w - c \ge 0$ and its multiplier $\mu^*$,
$\mathrm v_\sim'(w)=\beta\,\mathrm v_\succ'(a^*)+\mu^*=\mathrm u'(\pi(w))$
at the optimal saving $a^* = w-\pi(w)$, the corner included through the
right derivative at zero saving; the clause of the third spelling states
this multiplier, and the declared multiplier of the second spelling is read
the same way ([Constraints](../10-constraints.md) §4). For a parametrized
convex program the multipliers are the subgradients of the optimal value as
a function of the constraint's perturbation (Rockafellar 1970, Theorem
29.1), and they exist under Slater's condition (Theorem 28.2). In the
dynamic setting the derivative of the value function is given by the
envelope theorems of Benveniste and Scheinkman (1979), as Stokey, Lucas and
Prescott (1989, Theorems 4.10 and 4.11) state them for an interior policy,
of Milgrom and Segal (2002) for arbitrary choice sets, and of
Rincón-Zapatero and Santos (2009) without interiority assumptions.

**When the split is not exact.** Several controls solved jointly are one
`solve` with several unknowns (R10). An occasionally binding constraint is
the clause `⟂`, a declared multiplier (R10) or a branch (R3, §4.7). A policy
that feeds back into the transition or the feasible set through an
aggregate, as in an equilibrium model, is a fixed point above the stage and
not an object of these rules.

### R9 The forward reading

**Written form.** The same transition blocks and law statements as the
backward reading, together with the policy the policy block determines. A
statement of a transition block defines the law of motion and contains no
expectation. A statement there that integrates a shock, as
`w = E_{y}(y) + b*R` would in the arrival transition of `cons_savings_iid`
(§4.2), is refused under `transition-without-expectation`; an integration
over a shock is written in a backward block or in the policy block (R7,
R11).

**Interpretation.** Under a measurable feasible policy $\pi$, the declared
transitions and conditional shock laws determine a state-transition kernel.
For either edge write it as $K(x,A)$: the probability that the next state
belongs to a measurable set $A$, conditional on the current state $x$.
Its forward action on a state law $\mu$ and backward action on a test
function $v$ are
$$
(K_\#\mu)(A)=\int K(x,A)\,\mu(\mathrm dx),\qquad
(K^*v)(x)=\int v(y)\,K(x,\mathrm dy).
$$
For bounded measurable $v$, or the corresponding integrable cases,
$$
\int v\,\mathrm d(K_\#\mu)=\int K^*v\,\mathrm d\mu.
$$
This is the forward/backward pairing identity. Composition of transitions
propagates measures forward and functions in reverse order. It does not
make the full Bellman operator the transpose of a probability transition:
with reward and constant discount,
$T_\pi v=r_\pi+\beta K_\pi^*v$ is generally affine, and maximization over
policies is generally nonlinear. The pairing concerns $K_\pi^*$; rewards,
discounting, and optimization remain their separately authored operations.

For a stage the forward composition is
$\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec$.
A product output has the joint law of its components, and a selected branch
has its law on the appropriate labeled successor space. For a branching
block the stage records the condition `mass-conservation`, that the masses
of the branch measures sum to the mass of the measure pushed forward. The
condition is established where a control selects the branch, or a shock
selects it with weights written as numbers, provided that the stage
establishes that every line of a branch writes a value in the declared set
of its field; otherwise `stage.obligations()` lists it as required. State-space
sufficiency must include the conditional kernels used in this composition.

**Dependence.** A joint conditional law, or the declared conditional laws
that factor it, specifies shocks used together. Separate declarations define
the product of the declared conditional laws, each given its named parents
and the source coordinates, and the forward extension adds them in that
dependency order, parents first. Declarations that have no such order are
refused under `distribution-dependency`: a declaration that reads a
component of its own subject as an argument, `(y, z) ~ N((y, 0), …)`, and
declarations whose shock arguments form a cycle, `y ~ N(z, 1)` with
`z ~ N(y, 1)`. The factorization is an assumption the
elaboration records; it is not inferred from distinct variable names.

**Scope.** Forward propagation needs the transitions, laws, and a supplied
policy. Value equations are needed if that policy is itself obtained by
solving the stage, but are not needed to propagate a given policy. Recording
additional quantities along individual histories is a separate simulation
choice.

### R10 Implicit equations

**Written form.** A statement whose right side depends on its own left
side through a transition; a statement whose left side is an expression,
`𝑑𝑢(c) = β*D_{a}V[>]`; a `solve` statement; a decision-perch statement followed
by the clause `⟂ m_d - c >= 0` where the decision-to-continuation law is
`a = m_d - c`; a continuation-marked candidate line with `⟂ a >= 0`;
an equation followed by a clause with two bounds, `⟂ 0 <= c_p <= w_d`;
and a multiplier declared in the body of a policy
block, `μ[>] : ℝ₊ ⟂ a >= 0`.

**Context.** The block's outputs, and the transitions through which a
right side may reach the output being determined.

**Interpretation.** The **unknown** of an implicit statement is the output
of the block that the statement determines, and a bare control on the left
side names it. Where the left side of an equation is neither a name, nor a
tuple of names, nor one derivative term, the statement is a **candidate statement**, and its
**candidates** are the outputs of its block that it mentions, bare or under a
perch mark, and that no operative statement of the block with a name on its
left side defines. A line whose left side is one derivative term,
`D_{a}V[>]`, is no candidate statement: every block reads it as a derivative
line (§2.2). In a policy block `D_{a}V[>] = 𝑑𝑢(c) ⟂ m_d - c >= 0` is
therefore refused, under `forward-composite`, and the first-order condition
is written with the term on its right side,
`𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0`. A statement is **operative** when the block computes with
it, which is every line that the author neither marks `!doc` nor attaches to
another line as its property by a dotted id (§2.3); a line marked `!doc`
states what an object is and no operation realizes it, so the maximization
statement of a policy block leaves the control it names undetermined here,
and a property line forms no operation, defines no output and enters no
system.
A candidate statement mentions a field when the field's
name occurs on either side of its equation after the substitution of aliases
(R2): an argument of a call is an occurrence, the body of a called function
is not read, no transition is followed, the clause after `⟂` is not read,
and a name under a perch mark, `c[>]`, is a field of its own and no
occurrence of the bare `c`. The candidate statements of one block that share
a candidate form one **system**, and one that shares none is a system of
one; the unknowns of a system are its candidates in the order of the block's
header, a marked field directly after the output it marks. A system with as
many statements as unknowns determines them jointly, as a `solve` statement
over several unknowns does (R8), with the residuals in file order and the
complementarity clauses of this rule retained. A system whose statements and
unknowns differ in number, both being positive, determines nothing and is
refused; the relation is not retained as a correspondence. A candidate
statement with no candidate determines nothing the block must supply and is
retained as a relation the block realizes by no operation, as is an
inequality whose left side is not a name. The statement denotes the relation
$\{(x, c) : r(x, c) = 0\}$, with $r$ the residual, left side minus right
side, after the substitution of R5. The output is the field $c$ with
$r(X_\sim, c) = 0$ almost surely. The entire relation is the graph of a function where there is exactly one
solution; a selected part may define a function even when the relation has
several solutions. Existence and measurability of that selection, and
whether its root is an optimizer, remain separate requirements (R8). A fresh left-hand name does not make a statement
explicit: `z = c[>]`, where `c[>]` depends on the undetermined output `c`
through `a = w - c`, defines `z` as a function of `c` and leaves `c`
undetermined.

**The operation of a system.** A system forms one operation of the policy
builder, an Aggregation whose rule holds the relation with the system's
unknowns on both sides, reached by one `solve` occurrence at its first
statement that holds the system's unknowns, so that a method attached to the
policy block addresses the system as one place. The package does not yet
record this occurrence on every system (§5.3). On the first-order condition
`𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0`, the example of this paragraph, no place
`policy.solve` exists, a root finder has no place at which to be typed, and
a solution method is typed at the policy builder, as
`policy.method : !time_iteration` is. The rule of
the operation is the conjunction, over the system's statements, of each
statement read at the decision state $x$: every function at the coordinates
of its own perch, every continuation coordinate replaced by the matching
component of the law of motion at $x$ and the policy,
$\mathrm g_\succ(x, \pi(x))$, and a clause read in the same way and held
whole beside its statement. The package does not yet read the left side of a
statement in this way: a continuation value written there is not composed
with the law of motion (R4, §5.3). The rule holds at every $x$ in the declared
decision domain. For the consumption stage of §4.2 with its three policy
lines replaced by `𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0` it is
$$
\mathrm{du}(\pi(x)) = \mathrm{dv}_\succ(\mathrm g_\succ(x, \pi(x)))
\ \perp\ \mathrm g_\succ(x, \pi(x)) \ge 0
\qquad\text{for every } x \in X_m ,
$$
the Kuhn–Tucker system of the next paragraph at every state.

**Complementarity.** A clause pairs the residual $r$, left side minus
right side, with the slack $s$ of its bound on a quantity $z$: $s = z - b$
for `z >= b`, written $z$ when $b$ is zero, and $s = b - z$ for `z <= b`. A
bound is written with `>=` or `<=`. The package does not yet check this for
a clause with one bound: it reads a strict sign there as the weak one, so
that `⟂ a > 0` states the condition of `⟂ a >= 0` (§5.3). In a clause with
two bounds a strict sign is refused under `readable-form`. A
lower bound means
$$
r\geq0,\qquad s\geq0,\qquad r\,s=0,
$$
an upper bound means $r\leq0$, $s\geq0$ and $r\,s=0$, and two bounds,
`⟂ lb <= z <= ub`, mean
$$
z-lb\geq0,\qquad ub-z\geq0,\qquad r\,(z-lb)\leq0,\qquad r\,(ub-z)\geq0 :
$$
the residual is nonnegative where the lower bound binds, zero where neither
binds and nonpositive where the upper bound binds. After an inequality the
residual takes the sign of that relation, the clause adding $s\geq0$ and
$r\,s=0$; a clause with two bounds after an inequality has no sign rule and
is refused. The construction reads a clause by its product: either $s>0$
and $r=0$, or $s=0$ and $r$ has the stated sign; two bounds give three
cases, $z=lb$ with $r\geq0$, $z=ub$ with $r\leq0$, and both slacks positive
with $r=0$, each case keeping both bounds. The reading admits exactly the
pairs the conditions above admit, a strict inequality admitting none where
the bound is slack. On the candidate line of §4.5,
`c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>]) ⟂ a >= 0`, it admits at each positive saving the
one value $\mathrm f(a)$ and at zero saving every value in
$(0, \mathrm f(0)]$. The sign is read from the relation as written, so a clause with
one bound writes the bounded quantity first: `⟂ 0 <= a` would state the
reversed sign and is refused. The clause imposes equality where the bound is
slack and a residual sign where the bound binds. Exchanging an equation's
sides negates the residual and hence changes this condition. The sign must
agree with the constrained problem's first-order conditions. For the Euler
residual in §4.5 it gives the stated borrowing-constraint conditions; it
does not establish their sufficiency, existence, or domain coverage for an
arbitrary model.

**The residual as a multiplier.** With one bound the residual is the
multiplier of that bound; with two bounds, $lb < ub$, it is the difference
$\mu_{lo} - \mu_{hi}$ of the two bounds' multipliers, of which at most one
is positive. In a system each statement with a clause is written so that
its residual is the multiplier of its own bound, the multipliers of the
other bounds being eliminated by combining the first-order conditions. In
the worker stage of the pension application the second condition is the
stationarity condition in the pension deposit less that in consumption, and
carries the deposit's two bounds, `⟂ 0 <= c_p <= w_d`; in the adjuster stage
of the housing application the housing condition carries no clause, because
the multiplier of the liquid-asset bound is eliminated from it. The rules
hold the statements as written and check no such arrangement; under the
rank condition of Dobrescu and Shanker (2024, Assumption 3.3), which makes
the multipliers of the binding constraints recoverable from the first-order
conditions (their §4.2), one exists.

**The relation of the identification.** Let
$\mathrm U:\mathsf S\to\mathsf C$ be the candidate map and
$\mathrm H:\mathsf S\to\mathsf X_\sim$ the coordinate map, the
functions that the candidate line and the coordinate line of a policy
block denote on the continuation coordinates $\mathsf S$, the second
supplied under R5 (A3). R8 states which names a continuation-marked line may
write (`candidate-coordinate`) and that a later line reads each candidate
(`candidate-read`). Other retained state arguments must be explicit if
the displayed map gives only one coordinate. Rewritten at the continuation
perch (R5), the identification states $\pi(\mathrm H(s)) = \mathrm U(s)$
for every $s \in \mathsf S$, the relation
$$
P=\{(\mathrm H(s),\mathrm U(s)):s\in\mathsf S\}.
$$
Where the candidate line admits several values at one point, as the clause
on the candidate line does at zero saving (§4.5), the pairs range over the
admitted values, the coordinate line read at each:
$P=\{(\mathrm H(s, x), x) : s\in\mathsf S,\ x \in \mathrm U(s)\}$.
The relation is the identification rewritten, not a rule of its own.
A **fiber** $\mathrm H^{-1}(x)$ is the set of arguments mapped to $x$.
The relation defines one control at every represented $x$ exactly when
$$
\mathrm H(s_1)=\mathrm H(s_2)\ \Longrightarrow\
\mathrm U(s_1)=\mathrm U(s_2).
\tag{F}
$$
Indeed, this condition makes $\pi(\mathrm H(s))=\mathrm U(s)$ independent
of the chosen argument; conversely, any such function $\pi$ makes the two
controls equal. Injectivity of $\mathrm H$ is stronger and gives the
convenient formula $\pi=\mathrm U\circ\mathrm H^{-1}$. For example,
$\mathrm H(s)=s^2$ and $\mathrm U(s)=s^2$ on $\mathbb R$ satisfy (F)
with $\pi(x)=x$ on $\mathbb R_+$ although $\mathrm H$ is not injective.
If $\mathrm U(s)=s$ instead, the same coordinate map gives two controls
at each $x>0$ and needs a selection rule.

Single-valuedness is separate from measurability and coverage. Require the
induced policy to be measurable on its stated decision domain, and state
which boundary or other rule extends it outside $\mathrm H(\mathsf S)$.
A useful sufficient case is a measurable bijection from a standard Borel
candidate space onto a declared standard Borel decision domain: its inverse
is measurable (Kallenberg 1997, Theorem A1.7).
In the non-injective case, a measurable choice $s(x)\in\mathrm H^{-1}(x)$
together with (F) also gives a measurable policy when $\mathrm U$ is
measurable. State these hypotheses rather than infer them from the diagram.

**Consistency with the transition.** Candidate and coordinate names alone
do not identify the solution of a Bellman problem. In a deterministic
transition $s=\mathrm g_\succ(x,u)$ the two rewritings of the
identification (R5) denote the same relation when
$\mathrm g_\succ(\mathrm H(s),\mathrm U(s))=s$, with feasibility and the
candidate's defining equations, and when every feasible solution of the
explicit relation $u=\mathrm U(\mathrm g_\succ(x,u))$ satisfies
$x=\mathrm H(\mathrm g_\succ(x,u))$. Otherwise the parameterized
candidate relation may omit solutions of the explicit equation. These
conditions must hold for retained state arguments as well.

Both identities follow from R2's rearrangement where the transition is
affine in the decision coordinate: solved for that coordinate, with the
candidate in place of the control, the transition gives the coordinate
line, and substituting in either direction gives the two identities. For
the savings transition $a=w-c$, solved as $w=a+c$, and the coordinate map
$\varphi(a)=a+\mathrm f(a)$, both follow algebraically, and the two
rewritings of the final line give the same relation on the same represented
domain. This is not a rule that any three suitably named fields define a
policy. The construction checks the coordinate line in this way: it solves
the transition for the decision coordinate, puts the candidate in place of
the control, and compares the result with the line by algebraic
simplification, every declared function being an opaque symbol. A line that
does not reduce to it, such as `w[>] = a + 2*c[>]`, or that agrees with it
only under an identity between declared functions, is refused under the
rule `grid-line-consistency`, and the refusal names the line as written and
the transition solved for the coordinate. Where a transition has several
outputs, the check is made only where every other output's line is given;
otherwise nothing is checked and nothing is recorded. An omitted candidate
or coordinate definition cannot be supplied by an analytic assumption. A
borrowing-boundary extension requires a separate condition or branch, such
as the clause on the candidate line of §4.5; it need not be attached to one
particular final-line spelling.

**A declared multiplier.** A declaration `μ[>] : ℝ₊ ⟂ a >= 0` in the body
of a policy block adds the coordinate $\mu$, with its declared set, to the
functions the block defines at the continuation perch, and restricts the
continuation state and $\mu$ jointly to the block's **observable set**
$$
A_\succ=\{(a,\mu)\in X_a\times\mathbb R_+ : a\geq0,\ \mu\,a=0\},
$$
which holds the bound as written and the product of $\mu$ with the bound's
slack; the bound is held even where the declared set of $a$ implies it. The
functions the block reads, $\mathrm v_\succ$ and its derivative
$\mathrm{dv}_\succ$ among them, keep their own
coordinates. The candidate and coordinate maps of the identification are
then maps on $A_\succ$. For the consumption stage of §4.2 with the
declaration added and the inverse Euler line written
`c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>] + μ[>])` they are
$$
\mathrm U(a,\mu)=\mathrm{du}^{-1}(\mathrm{dv}_\succ(a)+\mu),\qquad
\mathrm H(a,\mu)=a+\mathrm U(a,\mu),
$$
and the identification, rewritten at the continuation perch, states
$\pi(\mathrm H(s))=\mathrm U(s)$ for every $s\in A_\succ$, one
statement quantified over the observable set, on the image
$\mathrm H(A_\succ)$. Condition (F), coverage of the decision domain
and measurability are required on $A_\succ$ as on $\mathsf S$. The
declaration forms no operation and no wire. Its bound may name continuation
states, other multipliers of the block, parameters, numbers and `inf`; a
bound naming a control, a decision or arrival state or a candidate is
refused, since reading a control through its candidate would be an
inference. A constraint on a control is therefore written with the clause
on the first-order condition. A multiplier declared in the body of a block
that is no policy block is an error (R1). The package does not yet check
this (§5.3).

**Several unknowns.** `(i, b_n) = solve_{i, b_n}(r_1, r_2)` denotes the
relation in the product of the unknowns' sets. It determines a tuple of
outputs where there is one solution or an explicit selection from the
solutions, under the measurability conditions above.

### R11 Sub-transitions and the placement of expectations

**Written form.** A transition written across several statements, one per
intermediate quantity, and a value statement whose expectation binds the
shock realized on one of them.

**Interpretation.** Statements
$a_1=\mathrm g_1(x,c)$ and $a=\mathrm g_2(a_1,\eta)$ give the typed
transition
$\mathrm g_\succ(x,c,\eta)=\mathrm g_2(\mathrm g_1(x,c),\eta)$.
The shock argument is retained; the unqualified composition
$\mathrm g_2\circ\mathrm g_1$ would omit it. Substituting into a
continuation value gives
$\mathrm v_\succ(\mathrm g_2(\mathrm g_1(x,c),\eta))$.

When an expectation over $\eta$ is authored, its position and conditional
law determine which intermediate function is formed. If the conditional law
depends only on $a_1$, that function can be written
$\mathrm w(a_1)=\int\mathrm v_\succ(\mathrm g_2(a_1,z))
K_\eta(a_1,\mathrm dz)$. If the law retains other state or control
dependence, those arguments must remain too. An additional expectation or
an exchange with maximization cannot be inferred solely from the shock's
occurrence in a transition. Conditional expectations can be combined using
the tower property only with the required nested conditioning information
and integrability; nonlinear aggregation must stay in its authored order.

Shock timing therefore constrains the validity of the written value
operators; it does not insert them. An expectation is written in a statement
of a backward block or of the policy block: a statement of a transition, an
intermediate one included, takes no expectation, and `a = a_1 + E_{η}(η)` is
refused under `transition-without-expectation` (R9). Intermediate functions remain part of
the mathematical composition whether or not a `!node` gives one an
independently addressable node. The package does not yet print the
composition on the card of a builder whose intermediate line has no `!node`:
the card then prints the rule of the intermediate line as the rule of the
value (R5, §5.3). See
[Operators and builders](../../bellman-calculus/05-Operators%20and%20builders.md) §10.

**Recursive preferences.** The order of expectation and any nonlinear
transformation is part of the value equation's meaning. A **certainty
equivalent** replaces a random continuation value with a certain one under
the model's preference rule. This appendix defines no specialized form for
that operation; the value statement must write the required transformations
explicitly, with their domains and order preserved.

### R12 Envelopes

**Written form.** A selection among branch values, `(V_w[>] - δ, V_r[>])[d]`
with `d = argmax_{d}(V_w[>] - δ, V_r[>])`, whose maximand is the tuple of the
value line, written entry by entry in the same order; an authored `upper_env(…)`; or nothing, when an
envelope is a step inside a numerical method. A maximand that is another
tuple is refused under `branch-tuple-mismatch`, also where it holds the same
entries in another order or an entry equal in value but written differently,
such as `-δ + V_w[>]`. A value line that selects by no tuple indexed by `d`,
such as `V = max(V_w[>] - δ, V_r[>])`, is refused under the same rule.

**Interpretation.** A finite branch maximum and a selection among a
parameterized set of candidates are different uses of an upper envelope.
For branches, the value is $\max_j Q(x,j)$ and a selected label attains it.
For the relation of R10, define the feasible fiber
$S_x=\{s:\mathrm H(s)=x,\ \mathrm U(s)\in\mathcal C(x)\}$.
The candidate value and selected control are
$$
\overline V(x)=\sup_{s\in S_x}Q(x,\mathrm U(s)),\qquad
s^*(x)\in\operatorname*{arg\,max}_{s\in S_x}Q(x,\mathrm U(s)),\qquad
\pi(x)=\mathrm U(s^*(x)).
$$
The maximization selects a parameter $s^*$; the policy is its control
$\mathrm U(s^*)$, not the parameter itself. Attainment and a measurable
selection are required for the latter two expressions. A non-injective
coordinate map need not give different controls in a fiber (condition (F)),
and concavity alone does not make an arbitrarily parameterized map injective.

An authored `upper_env` requests the stated mathematical operation. The
package does not yet give it that definition: it reads the line, lets a
method such as `!FUES` address the operator, checks none of its arguments,
and lists the condition `external-callable-signature-and-provider` for it
(§5.3). A
numerical method may compare interpolated candidate values as part of
realizing a declared optimization problem, without creating an authored
`upper_env`, `evaluate`, or `!node` statement. An envelope between finite
samples is generally an approximation, not a proof of the exact maximum.

**Assumptions.** Selecting by value requires the value of each candidate;
marginal values alone generally do not suffice. Including a global maximizer
is sufficient for equality with the full Bellman maximum. If the candidate
supremum is attained, equality also requires an included global maximizer;
an unattained supremum can equal the optimum value without supplying an
optimal control.
Differentiability makes the first-order condition necessary at an interior
maximum, but does not prove that a particular candidate parameterization
covers all such roots. Binding constraints, corners, and any missing
branches need their own candidates or conditions. A numerical envelope
cannot supply missing equations or establish global optimality by itself.

## 4 Worked derivations

The examples show stage files and an identified constrained-policy fragment,
followed by their mathematical interpretation. Grammatical acceptance does
not establish the domain, information, or analytic assumptions. The consumption
examples reproduce the equations of
`applications/consumption-savings-iid/declaration/stages/cons_savings_iid/cons_savings_iid.bl` and, in §4.2,
those of `applications/portfolio-choice/declaration/stages/cons/cons.bl`, apart from the differences
stated here. The listing of §4.2 writes the policy block of `cons` in the
interior form, with the candidate line as an equality. The application's
stage file writes that policy block as one maximization,
`c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])`, which is not marked `!doc` and
whose binder gives the control's feasible set by the correspondence
`Γ(x : ℝ₊₊) := (0, x]`. The application's methods file, `methods.bl` beside
the stage file, declares `𝑑𝑢𝑖𝑛𝑣`, types the endogenous grid method on the
policy builder and writes the method's three lines: the candidate line as
the inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`, whose clause states the
borrowing constraint (§4.5), the coordinate line `m_d[>] = a + c[>]` and
the final line `c = c[>]`. These three lines take the place of the
maximization in the operative policy builder, the stage keeping the
maximization at the declared level (R8). The application
also declares the control in `ℝ₊₊` on the forward block's header, where the
listing declares it in `ℝ₊`, and it lists a second arrival state,
`l : ℝ₊`, which the listing omits; the reading of the control's set in §4.2
is the listing's. Any additional mathematical restrictions are stated below the
examples.

### 4.1 A product output without consumption

> [!example] A firm with capital and debt
> A firm arrives with capital $k$ and debt $b$, observes a productivity
> shock $z$, chooses investment $i$ and new borrowing $b_n$, and pays out
> what remains. The continuation state is the pair (capital, debt).

```bl
@stage: firm

α : (0,1)
β : (0,1)
δ : [0,1]
r : ℝ₊
b_max : ℝ₊₊
μ_z : ℝ
σ_z : ℝ₊

z : ℝ₊₊
z ~ LogNormal(μ_z, σ_z)

𝑓(k : ℝ₊, z : ℝ₊₊) := z*k^α                                    :: [id=production]
𝑑𝑖𝑣(k : ℝ₊, b : ℝ₊, z : ℝ₊₊, i : ℝ₊, b_n : ℝ₊) := 𝑓(k, z) - i - (1+r)*b + b_n   :: [id=payout]

[id=arvl_to_dcsn, (k : ℝ₊, b : ℝ₊, z) : !arvl -> (k_d : ℝ₊, b_d : ℝ₊, z_d : ℝ₊₊) : !dcsn] {
    k_d = k
    b_d = b
    z_d = z
}

[id=dcsn_to_cntn, (k_d, b_d, i : !ctrl @ ℝ₊, b_n : !ctrl @ [0, b_max]) : !dcsn -> (k[>] : ℝ₊, b[>] : ℝ₊) : !cntn] {
    k[>] = (1-δ)*k_d + i
    b[>] = b_n
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, i, b_n) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑑𝑖𝑣(k_d, b_d, z_d, i, b_n) + β*V[>]        :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{z}(V)                                :: [id=value]
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (i, b_n) : !dcsn] {
    (i, b_n) = argmax_{i, b_n}(𝑑𝑖𝑣(k_d, b_d, z_d, i, b_n) + β*V[>])   :: [id=choice]
}
```

**Context (§2.4).** Parameters $\alpha, \beta, \delta, r, b_{\max}, \mu_z, \sigma_z$.
The shock $z$ is taken to have the displayed law conditionally on arrival
information. This is a constant conditional law and hence states independence
from that information; the numerical parameters alone would not imply it. The arrival state $X_\prec = (k, b)$,
the decision state $X_\sim = (k_d, b_d, z_d)$, the controls
$i \in \mathbb R_+$ and $b_n \in [0, b_{\max}]$, the continuation state
$X_\succ = (k_\succ, b_\succ)$ with the two coordinates the second
block's output side lists (R3). Two declared functions, each binding its
formal arguments.

**R1.** The first block is a forward transition from $\prec$ to $\sim$ with
the shock as an argument, $\mathrm g_\prec(k, b, z) = (k, b, z)$: the
realized shock becomes a coordinate of the decision state. The second is
the forward transition $\mathrm g_\succ(k_d, b_d, i, b_n) = ((1-\delta) k_d + i,\; b_n)$,
with two coordinate functions (R3). The third and fourth are backward
blocks; the fifth is a policy block, because its output is a pair of
controls.

**R6, scope.** The value statement reads $k_d, b_d, z_d$, the coordinates
of the decision state, at which the value it defines stands: they are
coordinates of the output function, and the header does not list them (R1).
The header lists the continuation value `V[>]`, the one input of the block,
and the controls $i, b_n$, at which its lines are read; the controls are at
the decision perch (§2.2).

**R5.** With $V_\succ = \mathrm v_\succ(k_\succ, b_\succ)$ and the
transition substituted,
$$
Q(k, b, z, i, b_n) = \mathrm{div}(k, b, z, i, b_n) + \beta\,\mathrm v_\succ\bigl((1-\delta) k + i,\; b_n\bigr),
$$
the choice value with both controls retained.

**R8 and R7.** The policy block binds $i$ and $b_n$ jointly. Its line,
which is not marked `!doc`, denotes the set of the maximizing policies (R8):
at each state the pairs that maximize $Q$ over
$\mathbb R_+ \times [0, b_{\max}]$ form the maximizer set, and a policy is a
measurable selection from it, $(i, b_n) = \pi(k, b, z) \in \arg\max$. The
interpretation assumes that the maximum is attained. The stage records no
condition for it: `stage.obligations()` lists no condition of attainment
beside the operation of the kind `Argmax` that the line forms, and the set
of the maximizing policies may be empty (R7). The bound $b_{\max}$ is what makes the feasible set
compact in the borrowing direction, and attainment in the investment
direction requires a separate restriction. For example, continuity and an
objective tending to $-\infty$ as investment grows, uniformly over the
compact borrowing interval, suffice. A marginal value merely below unit cost
without a uniform tail condition is not by itself an attainment proof. Then
$\mathrm v_\sim(k, b, z) = Q(k, b, z, \pi(k, b, z))$.

**R7, expectation.** In `V[<] = E_{z}(V)` the shock $z$ is bound and
$k, b$ are free. Since $V = \mathrm v_\sim(k, b, z)$ with $(k, b)$ measurable
at arrival and $z$ independent of the arrival information,
$$
\mathrm v_\prec(k, b) = \int \mathrm v_\sim(k, b, z)\,\mu_z(\mathrm dz),
$$
provided that, at each $(k, b)$, the integrand $\mathrm v_\sim(k, b, \cdot)$
is integrable under the law of $z$, so that the integral is finite, as the
declaration of `V[<]` in $\mathbb R$ requires (R7). The stage records this
requirement as the condition `expectation-integrability`, which
`stage.obligations()` lists as required.

**The stage operator.** $\mathbb T : \mathrm v_\succ \mapsto \mathrm v_\prec$
is the composite of these four steps: substitute $\mathrm g_\succ$, add the
payout, select, integrate over $z$.

**R9.** Forward, a law $\mu_\prec$ of $(k, b)$ becomes the product
$\mu_\prec \otimes \mu_z$ on the decision state, and then the law of
$((1-\delta)k + \pi_i(k, b, z),\; \pi_{b_n}(k, b, z))$ on the continuation
state, a joint law of the pair and not a product of marginals.

### 4.2 The consumption stage and the discounting convention

The stage `cons` is the consumption step of a two-stage period whose
other stage, `disc`, carries the discount factor.

```bl
@stage: cons

Xm := ℝ₊₊
Xa := ℝ₊

ρ : [1, inf)

𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]
𝑑𝑢(c : ℝ₊₊) := c^(-ρ)               :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)          :: [id=inv_marg_util]

[id=arvl_to_dcsn, (m : Xm) : !arvl -> (m_d : Xm) : !dcsn] {
    m_d = m
}

[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊) : !dcsn -> (a : Xa) : !cntn] {
    a = m_d - c
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V        = 𝑢(c) + V[>]          :: [id=value]
    D_{m_d}V = 𝑑𝑢(c)                :: [id=marginal]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}

[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])       :: [id=InvEuler]
    m_d[>] = a + c[>]                :: [id=endoggrid]
    c      = c[>]                    :: [id=cons_choice]
}
```

**Context.** The parameter $\rho \ge 1$; the sets $X_m = \mathbb R_{++}$
and $X_a = \mathbb R_+$; the control $c$ with set
$\mathbb R_+ \cap \mathbb R_{++} = \mathbb R_{++}$ (§2.4), which also
satisfies the domain check for `𝑢(c)` (R6). The body of `𝑢` requires
$\rho \neq 1$, which the declared set $[1, \infty)$ does not state. The
stage records it as the condition `arithmetic-definedness`, that the
divisor $1 - \rho$ is not zero, and calibration decides that condition, so
a calibration with $\rho = 1$ is refused although the declared set admits
it (R6). States $m$ at arrival, $m_d$ at
decision, $a$ at continuation. No shock: the income and return process of
this period live in other stages.

**R1.** $\mathrm g_\prec(m) = m$; $\mathrm g_\succ(m_d, c) = m_d - c$; a
backward block with one output and a derivative line; an arrival block that
copies; a policy block. The stage operator carries $\mathrm v_\succ$, a
function of $a$, to $\mathrm v_\prec$, a function of $m$; the derivative
$\mathrm{dv}_\succ$ that the policy block reads by `D_{a}V[>]` is a
function of $\mathrm v_\succ$ and not a second object the operator carries.

**R5, the value statement.** $V_\succ = \mathrm v_\succ(a)$ and
$a = m_d - c$, so
$$
Q(m, c) = \mathrm u(c) + \mathrm v_\succ(m - c).
$$
No discount factor appears, because none is written: the stage `disc`
writes `V = β*V[>]` and no derivative line, so the continuation value this
stage receives is already discounted, and its derivative with it. The
rules preserve whatever the file
writes and never insert a discount factor.

**R8, the policy.** The candidate and coordinate map are
$\mathrm f(a) = \mathrm{du}^{-1}(\mathrm{dv}_\succ(a))$ and
$\varphi(a) = a + \mathrm f(a)$, again without $\beta$, since
$\mathrm{dv}_\succ$ is discounted by `disc`. The implicit statement
`c = c[>]` reads $c = \mathrm f(m - c)$, which is the Euler equation
$\mathrm{du}(c) = \mathrm{dv}_\succ(m - c)$ (R10). When $\varphi$ is
injective, its solution is $\pi(m) = \mathrm f(\varphi^{-1}(m))$ for $m$ in
the range of $\varphi$. The interval $[\mathrm f(0), \infty)$ follows
under the positivity, continuity, monotonicity, and endpoint assumptions
stated in §4.5, not from nonincreasing marginal value alone. The
application's own candidate line, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`, adds the
corner below $\mathrm f(0)$: its clause admits at zero saving every
candidate value up to $\mathrm f(0)$, and the final line then states
$\pi(m) = m$ for $0 < m \le \mathrm f(0)$ (§4.5).

**Evaluation and the stated derivative.** $\mathrm v_\sim(m) = \mathrm u(\pi(m)) + \mathrm v_\succ(m - \pi(m))$
and $\mathrm{dv}_\sim(m) = \mathrm{du}(\pi(m))$, the second by the
envelope condition the derivative line `D_{m_d}V = 𝑑𝑢(c)` asserts (R8);
the line is recorded at the block's Evaluation beside the value and adds
no output to the block. The arrival block copies the value,
$\mathrm v_\prec = \mathrm v_\sim$ with $m_d = m$, and writes no derivative
line: its law between the perches is the identity, so the derivative of
the arrival value is $\mathrm{dv}_\prec = \mathrm{dv}_\sim$.

**R9.** $\mathbb M_\prec$ is the identity and $\mathbb M_{\succ,\pi}$
carries a law of $m$ to the law of $m - \pi(m)$.

The stage `cons_savings_iid` writes the same problem with the discount
factor inside the stage and an income shock realized before the decision.
Its stage file states the values and the maximization:

```bl
@stage: cons_savings_iid

Y := ℝ₊

β : ℝ₊₊ :: ["discount factor must be a strictly positive number"] 
γ : (1, inf) :: ["Relative risk aversion must be greater than 1"]
R : ℝ₊₊
μ_y : ℝ
σ_y : ℝ₊
p_zero : (0,1)

y : Y
y ~ Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_y, σ_y)))

𝑢(c : ℝ₊₊) := c^(1-γ)/(1-γ)         :: [id=util]
𝑑𝑢     := D_{c}(𝑢)                   :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)                    :: [id=inv_marg_util]
Γ(x : ℝ₊) := (0, x]                  :: [id=feasible_consumption]

[id=arvl_to_dcsn, (b : ℝ₊, y) : !arvl -> (w : ℝ₊) : !dcsn] {
    w = y + b*R                 :: [id=cash_on_hand, "market_resources are blah blah"] 
}

[id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = w - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y}(V)                 :: [id=value]
}
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ(w)}(𝑢(cp) + β*V[>])  :: [id=optimality]
}
```

Its methods file, `methods.bl` beside the stage file, writes three blocks
named by the stage's block ids, in the same syntax: the block `policy`
types the endogenous grid method on the policy builder, with its grid of
savings, and brings the method's three lines, and the blocks
`cntn_to_dcsn` and `dcsn_to_arvl` add the derivative lines of the two
values ([Methodization](../04-methodization.md) §1):

```bl
[id=policy, method : !egm
    | policy.grid : !Cartesian(a=(a_min, a_max, n_a))] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}
```

```bl
[id=cntn_to_dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}
```

```bl
[id=dcsn_to_arvl] {
    D_{b}V[<] = E_{y}(R * D_{w}V)   :: [id=marginal]
}
```

Here `𝑑𝑢` is the derivative of `𝑢` with respect to its argument and
`𝑑𝑢𝑖𝑛𝑣` its inverse (R7), so
$\mathrm{du}(c) = c^{-\gamma}$ and $\mathrm{du}^{-1}(x) = x^{-1/\gamma}$,
the inverse existing because $\mathrm{du}$ is a bijection of
$\mathbb R_{++}$ for $\gamma > 0$, a restriction that the declared set
`γ : (1, inf)` implies. The shock $y$ is listed on the arrival
side as an argument of the transition, not as a coordinate of the arrival
state, and is realized between arrival and decision. The value statement
lowers to $Q(w, c) = \mathrm u(c) + \beta\,\mathrm v_\succ(w - c)$, the
methods file's candidate to $\mathrm f(a) = (\beta\,\mathrm{dv}_\succ(a))^{-1/\gamma}$,
and the implicit statement, written `c[~] = c[>]` with the optional mark
of the decision perch, to the Euler equation
$\mathrm{du}(c) = \beta\,\mathrm{dv}_\succ(w - c)$. The stage file's
policy line, `c = argmax_{cp : Γ(w)}(𝑢(cp) + β*V[>])`, forms an operation
of the kind `Argmax`, whose output is the set of maximizing policies (R7,
R8); its binder supplies the feasible set $\Gamma(w)=(0,w]$ for the
control's derived type. The three lines of the methods file's block `policy` take the place of
the maximization in the operative policy builder, the stage keeping the
maximization at the declared level, since a block defines its control once
(the rule `defined-once`). The interior-only
form, a stage file whose policy block states the control by the candidate
and the implicit statement alone, remains admitted. The arrival value's
statement and its derivative line are derived in §4.4. The declared set
`γ : (1, inf)` excludes $\gamma = 1$, at which the body of `𝑢` is undefined,
and it states the restriction that the prose annotation describes: a
calibration with $\gamma = 1$ or with $\gamma = 0.5$ is refused as a value
outside the declared set. The declared set shows that $1 - \gamma$ is not
zero, so the stage records no condition for the division in the body of
`𝑢`. The interpretation used here requires $\gamma>0$ and $\gamma\neq1$
(R6), and the declared set implies both.
At zero resources, the stated strictly positive control and the nonnegative
saving constraint cannot both hold. A value or policy at that state needs
an explicit boundary interpretation; the income mixture includes an atom
at zero, so that issue cannot be dismissed as a null event for all initial
conditions.

### 4.3 Identifiers are addresses

The reading of §4.2 used the identifiers `InvEuler`, `endoggrid`,
`g_cntn_to_dcsn`, and `cons_choice` nowhere. What it used were the perch
marks and the roles: `c[>]` is the output `c` read at the continuation
perch, defined by the first statement; `w[>]` is the decision coordinate
`w` read at the continuation perch, defined by the second; and the third
statement identifies the output with its continuation-perch version, its
right side depending on the output through the transition `a = w - c`
(R10). Renaming the three identifiers to `first`, `second`, and `third`,
and updating the methods file that addresses them, leaves every denotation
unchanged (R1).

The final line states one relation, which R5 rewrites at either perch.
Read at the decision perch, `c = c[>]` is $c = \mathrm f(w - c)$, an
implicit equation that a root finder can solve without the coordinate map.
The package does not yet form this reading. It reads a block that writes
the candidate line and the final line without the coordinate line, and the
card then states no relation for the final line (R5, §5.3).
Rewritten at the continuation perch, the second statement supplying the
decision coordinate `w` read there (R5 (A3)), the final line is
$\pi(\varphi(a)) = \mathrm f(a)$, the relation the construction states,
since that perch's map contains no unknown. The mark on `w[>]` identifies
that coordinate; the budget identity and the equations establish the
transition consistency required by R10, which the construction checks. A
mark or an identifier alone cannot establish that consistency. A block
without the final line states no policy and is refused (R1).

### 4.4 The perch form and the functional form of one statement

The arrival block of `cons_savings_iid` writes, in the perch form,

```bl
V[<] = E_{y}(V)
```

**Step 1, the fields.** `V[<]` denotes the value field at arrival, `V` the
value field at decision, `y` the income shock, realized on the edge from
arrival to decision.

**Step 2, binding (R4).** Inside `E_{y}(…)` the shock `y` is bound. The
free names of the statement are those `V` depends on other than `y`: by R5
applied to the decision value, $V = \mathrm v_\sim(w)$ with
$w = y + R\,b$, so the remaining state argument is $b$. The supplied function
$\mathrm v_\sim$, the return $R$, and the parameters of the shock law
remain inputs or parameters; binding the shock does not bind that function.

**Step 3, the conditional expectation (R7).** The left side is at the
arrival perch, so `E_{y}` denotes $\mathbb E[\,\cdot \mid \mathcal F_\prec]$.
The integrand is $\mathrm v_\sim(y + R\,b)$, a function of the
$\mathcal F_\prec$-measurable $b$ and the shock $y$, whose displayed law is here assumed to be its conditional law given
$\mathcal F_\prec$. Its constancy in the arrival state is a conditional
independence assertion, not an inference from a marginal distribution. By the disintegration theorem,
$$
V_\prec = \mathbb E\bigl[\mathrm v_\sim(y + R\,b) \,\big|\, \mathcal F_\prec\bigr]
= \int \mathrm v_\sim(y' + R\,b)\,\nu_y(\mathrm dy')
\quad\text{almost surely.}
$$

**Step 4, the functional form (R5).** The right side is a function of $b$
alone, so it represents $V_\prec$ with respect to $X_\prec = b$:
$$
\mathrm v_\prec(b) = \int \mathrm v_\sim(y + R\,b)\,\nu_y(\mathrm dy),
\qquad
\nu_y = p_0\,\delta_0 + (1 - p_0)\,\mathrm{LogNormal}(\mu_y, \sigma_y).
$$

Here $\nu_y$ names the probability law, $\mu_y$ is the lognormal
location parameter written `μ_y`, $p_0$ is `p_zero`, and $\delta_0$ is
unit probability at zero. This avoids using one symbol for both a law
and its numerical parameter.

**Step 5, the derivative line.** The methods file's block `dcsn_to_arvl`
writes `D_{b}V[<] = E_{y}(R * D_{w}V)`, which lowers in the same way to
$\mathrm{dv}_\prec(b) = R \int \mathrm{dv}_\sim(y + R\,b)\,\nu_y(\mathrm dy)$:
`D_{w}V` denotes $\mathrm{dv}_\sim$, the derivative of the decision value
in $w$, and the factor $R$ is the derivative of the law $w = y + R\,b$ in
$b$. The line states the derivative
of the arrival value in $b$, and it is
that derivative when differentiation under the integral sign is justified,
an assumption the rules record and nothing checks (R8). The author writes
the line because the law between the perches is not the identity and
carries the factor $R$. Where the law is the identity, as in `V[<] = V` of
§4.2, no derivative line is written: the derivative of the arrival value is
the derivative of the decision value.

**What the functional form must not say.** The expectation acts on the
field, that is on the function evaluated at the state $y + R\,b$ that
contains the bound shock. The expression $\mathbb E_y\,\mathrm v_\sim$, an
expectation of the function itself, does not denote the arrival value, and
no reading of it recovers the evaluation the perch form carries implicitly
(R5). A functional-form spelling of this statement must therefore be
$\mathrm v_\prec(b) = \mathbb E_y\,\mathrm v_\sim(y + R\,b)$, with the
argument written.

### 4.5 An implicit statement with a constrained policy

Under the concavity and endpoint hypotheses stated below, the Euler
equality has a feasible solution for $w\geq\mathrm f(0)$, with positive
saving for $w>\mathrm f(0)$. Below that threshold the borrowing constraint
binds. The following two-block fragment states the transition and constrained
policy relation on $w>0$; it does not supply the complete value stage. The
power-utility body also requires $\gamma\neq1$.

```bl
@stage: cons_constrained

β : (0,1)
γ : ℝ₊₊

𝑢(c : ℝ₊₊) := c^(1-γ)/(1-γ)         :: [id=util]
𝑑𝑢     := D_{c}(𝑢)                   :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)                    :: [id=inv_marg_util]

[id=dcsn_to_cntn, (w : ℝ₊₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = w - c
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])        :: [id=candidate]
    w[>] = a + c[>]                  :: [id=coordinate]
    𝑑𝑢(c) = β*D_{a}V[>] ⟂ w - c >= 0 :: [id=euler]
}
```

**R10.** The third statement has an expression on its left, and its unknown
is the block's output $c$. Its clause writes `w - c`, the expression for
the continuation state supplied by the forward block. After the substitution
of R5, under which `D_{a}V[>]` denotes $\mathrm{dv}_\succ(a)$, the
derivative of $\mathrm v_\succ$ at the saving $a = w - c$, the residual is
$r(w, c) = \mathrm{du}(c) - \beta\,\mathrm{dv}_\succ(w - c)$. The clause denotes
$$
r(w, c) \ge 0, \qquad w - c \ge 0, \qquad r(w, c)\,(w - c) = 0 .
$$
Where saving is positive the Euler equation holds with equality; where the
agent saves nothing, $c = w$, marginal utility may exceed the discounted
marginal value of saving. This is the Kuhn–Tucker system of
$\max_{0 < c \le w} \{\mathrm u(c) + \beta\,\mathrm v_\succ(w - c)\}$.

**The solution under concavity.** Suppose $\mathrm u$ is strictly concave
and continuously differentiable with $\mathrm{du}$ a decreasing bijection
of $\mathbb R_{++}$, and $\mathrm v_\succ$ is continuously differentiable
with $\mathrm{dv}_\succ$ positive, continuous, and nonincreasing. Then
$\mathrm f = \mathrm{du}^{-1} \circ (\beta\,\mathrm{dv}_\succ)$ is
continuous and nondecreasing, $\varphi = \mathrm{id} + \mathrm f$ is
continuous and strictly increasing with range $[\mathrm f(0), \infty)$, the
fiber condition holds on that range, and the system has exactly one solution
at every $w > 0$:
$$
\pi^\ast(w) =
\begin{cases}
w, & 0 < w \le \mathrm f(0), \\
\mathrm f(\varphi^{-1}(w)), & w > \mathrm f(0).
\end{cases}
$$
This $\pi^\ast$ is the maximizer, because the objective is strictly concave
in $c$ and the Kuhn–Tucker conditions are then sufficient. Without the
clause the statement `𝑑𝑢(c) = β*D_{a}V[>]` denotes the interior relation only,
which has no solution below $\mathrm f(0)$; a method that returns
$c = w$ there is solving a problem the file has not declared, and the rules
require it to report the extension rather than to return it silently.

**Equality and complementarity are different.** On the candidate relation,
the equalities `𝑑𝑢(c) = β*D_{a}V[>]`, `c = c[>]`, and `w = w[>]` have the
same roots. They cannot all carry the same complementarity sign. Since
$\mathrm{du}$ is strictly decreasing,
$$
\mathrm{du}(c)-\beta\,\mathrm{dv}_\succ(a)\geq0
\quad\Longleftrightarrow\quad
\mathrm f(a)-c\geq0.
$$
The residual of `c = c[>]` is instead $c-\mathrm f(a)$, with the opposite
sign. The coordinate residual with the correct sign is
$\varphi(a)-w=\mathrm f(a)-c$ when $a=w-c$. Thus converting an Euler
complementarity condition into a candidate or coordinate condition requires
orienting the residual correctly; equivalence of the underlying equalities
is insufficient.

**The declared multiplier.** The same constraint can be written with its
multiplier declared (R10). The policy block is then

```bl
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    μ[>] : ℝ₊ ⟂ a >= 0                 :: [id=slackness]
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>] + μ[>])   :: [id=candidate]
    w[>] = a + c[>]                    :: [id=coordinate]
    c    = c[>]                        :: [id=choice]
}
```

Its candidate and coordinate maps are defined on the observable set
$A_\succ = \{(a, \mu) \in \mathbb R_+ \times \mathbb R_+ : a \ge 0,\ \mu\, a = 0\}$:
$\mathrm U(a, \mu) = \mathrm{du}^{-1}(\beta\,\mathrm{dv}_\succ(a) + \mu)$
and $\mathrm H(a, \mu) = a + \mathrm U(a, \mu)$, and the block states
$\pi(\mathrm H(s)) = \mathrm U(s)$ for every $s \in A_\succ$.

**The clause on the candidate line.** The same constraint can be written
as a clause on the candidate line. The policy block is then

```bl
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>]) ⟂ a >= 0   :: [id=candidate]
    w[>] = a + c[>]                      :: [id=coordinate]
    c    = c[>]                          :: [id=choice]
}
```

After an inequality the residual takes the sign of that relation (R10), so
the clause admits at each saving $a$ the values $x \in \mathbb R_{++}$ with
$x - \mathrm f(a) \le 0$, $a \ge 0$ and $(x - \mathrm f(a))\,a = 0$: the
one value $\mathrm f(a)$ where $a > 0$, and every $x$ in
$(0, \mathrm f(0)]$ where $a = 0$. The coordinate line gives each admitted
value its cash on hand $a + x$, and the final line, rewritten at the
continuation perch (R5), states $\pi(a + x) = x$ for every saving $a$ and
every value $x$ admitted there: $\pi(\varphi(a)) = \mathrm f(a)$ where
$a > 0$, and $\pi(x) = x$ for $0 < x \le \mathrm f(0)$, the corner.

**The three spellings denote one relation.** Assume that `𝑑𝑢𝑖𝑛𝑣` is the
inverse of `𝑑𝑢` on $\mathbb R_{++}$, authored as in §4.2 or derived by
`Inv` as here, and that the saving is $a = w - c$. Then the clause of the
first block and the declared multiplier of the second denote one relation
between $w$ and $c$. For $(a, \mu) \in A_\succ$ put $c = \mathrm U(a, \mu)$
and $w = a + c$: then $w - c = a \ge 0$, $r(w, c) = \mu \ge 0$ and
$r(w, c)\,(w - c) = \mu\, a = 0$, which is the system of the clause.
Conversely, a solution $(w, c)$ of that system gives $a = w - c$ and
$\mu = r(w, c)$, a point of $A_\succ$ with $\mathrm H(a, \mu) = w$ and
$\mathrm U(a, \mu) = c$. If further $\mathrm{du}$ is strictly
decreasing, the clause on the candidate line of the third block denotes the
same relation, and its pairs are those of the declared multiplier: the grid
pair $(\varphi(a), \mathrm f(a))$ at a saving $a > 0$ is the pair at
$(a, 0)$, and the corner pair $(x, x)$ with $0 < x \le \mathrm f(0)$ is the
pair at $(0, \mu)$ with $\mu = \mathrm{du}(x) - \beta\,\mathrm{dv}_\succ(0)$,
which is nonnegative exactly when $x \le \mathrm f(0)$ because
$\mathrm{du}$ is strictly decreasing. Conversely the pair at $(0, \mu)$ is
the corner pair at $x = \mathrm U(0, \mu) \le \mathrm f(0)$. When
$\mathrm{du}$ is a decreasing bijection of $\mathbb R_{++}$, the map
$x \mapsto \mathrm{du}(x) - \beta\,\mathrm{dv}_\succ(0)$ carries
$(0, \mathrm f(0)]$ onto $[0, \infty)$. The inequality statement written
without the clause, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])`, its relation read as the
equality on the grid, denotes the part of the relation with $\mu = 0$ and
is no spelling of the condition. The identity of the first block with the
second uses no monotonicity and no concavity; that of the third uses the
monotonicity of $\mathrm{du}$ and no concavity.

**One policy, the maximizer.** Suppose further (H1) that $\mathrm u$ is
strictly concave and differentiable with $\mathrm{du}$ a decreasing
bijection of $\mathbb R_{++}$, (H1′) that `𝑑𝑢𝑖𝑛𝑣` is its inverse, (H2) that
$\mathrm{dv}_\succ : \mathbb R_+ \to \mathbb R_{++}$ is continuous and
nonincreasing, $\mathrm{dv}_\succ(0)$ being the right derivative of
$\mathrm v_\succ$ at zero, and (H3) that the transition is
$\mathrm g_\succ(w, c) = w - c$. Let
$\bar w = \mathrm f(0) = \mathrm{du}^{-1}(\beta\,\mathrm{dv}_\succ(0))$.

1. The residual $r(w, c) = \mathrm{du}(c) - \beta\,\mathrm{dv}_\succ(w - c)$
   is strictly decreasing in $c$ on $(0, w]$ and tends to $+\infty$ as
   $c \to 0$, so the clause's system has one solution at every $w > 0$:
   $c = w$, with multiplier $r(w, w) \ge 0$, when $w \le \bar w$, and the
   unique interior root otherwise. The first block defines the policy
   $\pi^\ast$ above.
2. $\mathrm H$ is a bijection of $A_\succ$ onto $\mathbb R_{++}$. On the
   half-line $\mu = 0$ it is $\varphi$, strictly increasing with range
   $[\bar w, \infty)$; on the half-line $a = 0$ it is
   $\mu \mapsto \mathrm{du}^{-1}(\beta\,\mathrm{dv}_\succ(0) + \mu)$,
   strictly decreasing with range $(0, \bar w]$; the two meet at
   $(0, 0) \mapsto \bar w$. The half-line $a = 0$ reaches every $w$ below
   $\bar w$ because the declared set of $\mu$, $\mathbb R_+$, is unbounded.
3. The policy of the second block, $\mathrm U \circ \mathrm H^{-1}$, equals
   $\pi^\ast$, by the identity of relations with items 1 and 2, and so does
   the policy the third block states, $\mathrm f \circ \varphi^{-1}$ on
   $[\bar w, \infty)$ and the identity on $(0, \bar w]$.
4. Both are the maximizer of $\mathrm u(c) + \beta\,\mathrm v_\succ(w - c)$
   over $(0, w]$ when $\mathrm v_\succ$ is concave with derivative
   $\mathrm{dv}_\succ$: for a concave objective and a linear constraint the
   Kuhn–Tucker conditions are sufficient (Boyd and Vandenberghe 2004,
   §5.5.3), the conditions being those of Nocedal and Wright (2006,
   Theorem 12.1). Dobrescu and Shanker (2024, Proposition 3.1) state the
   corresponding result for the sequence problem, given a fixed and optimal
   sequence of future discrete choices; their Definition 1 names the
   property that roots coincide with solutions and proves nothing.
   Sufficiency is a property of the stage's problem: it holds or fails
   whichever method computes the policy. For the three blocks above,
   written in a stage file, it is stated here, on this page, and the stage
   records no condition for it. Where the endogenous grid method is typed
   on the policy builder, `stage.obligations()` lists the condition
   `egm-eligibility` (R8), that the continuation value is concave and
   continuously differentiable on $(0,\infty)$ with a finite positive right
   derivative at zero, and nothing checks it.
5. The inequality statement without its clause agrees with $\pi^\ast$ on
   $\varphi(\mathbb R_+) = [\bar w, \infty)$, the image of its grid, and
   states nothing below $\bar w$, where $\pi^\ast(w) = w$ follows from
   item 1; with the clause it states $\pi^\ast$ at every $w > 0$, by
   item 3.

**In general.** Uniqueness and optimality of a root rest on concavity of
the continuation value, equivalently $\mathrm{dv}_\succ$ nonincreasing,
with strict concavity of $\mathrm u$; uniqueness of the multiplier given a
root rests on the rank condition of Dobrescu and Shanker (2024,
Assumption 3.3). Their Theorem 4.1 gives only local existence of the
inverse near an interior solution in one constrained region, a piece of the
observable set (their equation (5)); existence on a whole region needs the
Poincaré–Miranda theorem (their §4.2 and online appendix, Corollary F.1)
or, in one dimension, item 2. By their Claims 4.1 and 4.2 the grid a method
inverts from has on each region the dimension of the state, one coordinate
here: the saving on one half-line of $A_\succ$ and the multiplier on the
other.
Condition (F), coverage and measurability are stated hypotheses (R10),
injectivity being one stronger sufficient condition. Where the continuation
value is not concave, the case their paper is written for, the three
spellings still denote one relation but none defines a function: several
roots stand at one state, and a method selects among them. For the third,
two admitted pairs may then share one cash on hand with different
candidates, and the stage states the relation and no selection among them.
The rules check none of this.

### 4.6 The endogenous-grid policy with and without its final line

Take the policy block of §4.2 in its two forms.

**With the final line.** `c = c[>]` gives
$\{(w,c):c=\mathrm f(w-c),\ w-c\geq0\}$ on the declared control
domain. By the budget identity this is the candidate relation below.
Under condition (F), coverage of the chosen domain $D$, and measurability,
it defines a policy $\pi$ on $D$. In this savings example, injectivity of
$\varphi$ permits $\pi=\mathrm f\circ\varphi^{-1}$.

**Without the final line.** The candidate and coordinate equations give
the pairs $P=\{(\varphi(a),\mathrm f(a)):a\in\mathbb R_+\}$, but no line
states the policy, and the block is refused (R1). The final line is what
states the relation on those pairs, rewritten at the continuation perch as
$\pi(\varphi(a)) = \mathrm f(a)$ (R10). The identities
$\varphi(a)-\mathrm f(a)=a$ and
$w=(w-c)+\mathrm f(w-c)$ for any explicit solution establish both
directions of R10's consistency requirement, so the two readings of the
final line give the same relation on the same domain. It is these equations
and their declared types that justify the rewriting, not the conventional
names of the aliases.

This relation does not by itself include every constrained corner. The
boundary $c=w$ below the threshold requires the correctly oriented condition
of §4.5, the declared multiplier of §4.5, the clause on the candidate line
of §4.5, or a separately declared boundary rule or branch. That condition need not be attached to one particular
final-line spelling. In a more
general model, the candidate and coordinate maps must specify the full
required state dependence, satisfy the transition and feasibility conditions,
and cover the solutions being claimed. Three perch/role labels alone do
not establish those premises.

**What the method adds.** The endogenous grid method chooses an asset grid
$a_1 < \dots < a_N$, tabulates the pairs $(\varphi(a_i), \mathrm f(a_i))$,
and takes as its approximate policy the function through those points, with
a stated extrapolation beyond the last knot (the endogenous grid method of
Carroll 2006). When the file writes the clause on the first-order condition, declares
the multiplier, or writes the clause on the candidate line (§4.5), the
segment $c = w$ on $(0, \varphi(0)]$ is not something the method adds: it
belongs to the exact relation the file states (§4.5, items 1 and 3), and
the method computes it with the other points, by the segment to the origin,
on the multiplier's half-line of the observable set, or at the values the
clause on the candidate line admits at zero saving. Without any of the
three, the segment lies outside the declared relation, and a method that
returns it reports an extension (§4.5). If the method uses an
interpolant, it agrees with its computed pairs at the knots. Those pairs equal the exact policy only when the supplied
continuation values and candidate calculations are exact. Increasing knots
are a diagnostic, not a proof of global injectivity or condition (F):
behavior between sampled points is untested. The construction
records none of these conditions: whether one holds, is established under
the hypotheses of §4.5, is shown by a numerical diagnostic without such a
proof, or is unverified is a statement about the problem and the method,
made on no record of the stage.

**An explicit evaluation.** The author may instead write
`c = evaluate(w[>], c[>], w)`. With exact coordinate and candidate maps,
and the functional interpretation of R10, this evaluates the same policy.
With tabulated pairs the line evaluates the chosen interpolating representation,
which generally approximates that policy. The package does not yet construct
either reading: the rule of the line prints
`UNRESOLVED[evaluate; mathematical definition]`, also with `!Linear` typed
at the line (R8, §5.3). Distinct knots alone neither
choose an interpolant nor establish the exact policy between them (R7).

### 4.7 A discrete choice and the pension model

A discrete choice is written as a block whose one control is valued in a finite
set of labels and whose output side is empty, with one nested block per
label, in the order in which the set lists the labels; nested blocks in
another order are refused under `branch-labels`. The backward block selects
among the branch values by the control. Each continuation value stands at
one position of the tuple, and that position decides the branch to which the
value belongs; a value at two positions or at none is refused under
`branch-value-position`. The policy block chooses the control by maximizing
over the same tuple in the same order (R12):

```bl
@stage: ret_choice

δ : ℝ₊

[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}

[id=dcsn_to_cntn, (a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    [label=work,   () -> (a_w : ℝ₊) : !cntn] { a_w = a_d }
    [label=retire, () -> (a_r : ℝ₊) : !cntn] { a_r = a_d }
}

[id=cntn_to_dcsn, (V_w[>] : ℝ @ !vlu, V_r[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = (V_w[>] - δ, V_r[>])[d]        :: [id=choice_value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}

[id=policy, (V_w[>], V_r[>]) -> (d)] {
    d = argmax_{d}(V_w[>] - δ, V_r[>])  :: [id=choice]
}
```

**R3.** The continuation state is the disjoint union
$\mathsf X_\succ = \mathbb R_+ \sqcup \mathbb R_+$, one copy per label,
each nested block defining the coordinates of its copy
([Branching](../../bellman-calculus/09-branching.md)). The tuple
`(V_w[>] - δ, V_r[>])` is a family in label order, and `[d]` selects the
entry the control names.

**R5, R8, R12.** With $V_{w,\succ} = \mathrm v_w(a_w)$ and
$V_{r,\succ} = \mathrm v_r(a_r)$ and both branch transitions the identity,
the choice value is $Q(a, d) = (\mathrm v_w(a) - \delta,\ \mathrm v_r(a))[d]$,
a selected policy $\pi(a) \in \arg\max_d Q(a, d)$ with a tie-break
the rules do not fix, and $\mathrm v_\sim(a) = \max\{\mathrm v_w(a) - \delta, \mathrm v_r(a)\}$,
the exact branch maximum. Forward, a state $a$ is routed to the copy
$\pi(a)$ names (R9).

**The pension model.** The savings-and-retirement model of Druedahl and
Jørgensen (2017), with a contribution cap, as solved by the inverse Euler
method of Dobrescu and Shanker, combines the constructions above. Its
worker stage has a decision state with three coordinates, liquid assets,
pension assets and earnings, two controls, consumption and the pension
deposit, and a
continuation state with two coordinates, so both transitions are products
(R3); its retirement choice is a branch of the form just shown; its
earnings shock is realized between arrival and decision, so the expectation
over it stands in the arrival block, `V[<] = E_{w}(V)` in `dcsn_to_arvl`,
as in §4.4 (R7); and its first-order conditions, one per
asset, form one system in two unknowns, which R10 reads as a `solve`
over both, whose residuals are subject
to the three constraints the model imposes, the liquidity constraint on the
liquid asset, the no-withdrawal constraint on the pension, and the cap, with their appropriate inequality directions and multipliers in a
coupled constrained system. R10's scalar lower-bound example is not a
complete derivation of that system. Discrete retirement choice can create
non-concavities and competing candidates; neither policy non-monotonicity
nor non-injectivity of a particular coordinate map follows from the branch
syntax alone. When candidates overlap and the required coverage and selection
conditions hold, R12 describes selection by value; an upper-envelope method
approximates that operation. The application's stage files stand under
`applications/pension-retirement/declaration/stages/`: `worker_saving.bl` states the
worker's maximization, the block `policy` of its methods file,
`applications/pension-retirement/declaration/stages/worker_saving/methods.bl`, writes its two
first-order conditions with the clauses `⟂ m_f - c - c_p >= 0` and
`⟂ 0 <= c_p <= w_d` of R10 under time iteration, and `applications/pension-retirement/economics.md`
records their correspondence with the paper's equations.

## 5 Assumptions and scope

### 5.1 The assumptions the rules record

| Requirement | Where it is used | What must be established |
|---|---|---|
| State sufficiency for the relevant fields and conditional laws | R5 (A1), R7 | the chosen arguments contain the information needed for the claimed representatives and kernels |
| Measurable transitions and any required recovery maps | R5 (A2–A3) | compositions have the claimed domains and earlier quantities are available as functions of the chosen arguments |
| Specified conditional shock laws | R7, R9, §4.4 | the integral uses the law for its actual conditioning context; a constant marginal law alone does not establish independence |
| Integrability and permitted output values | R7 | expectations and subsequent arithmetic are defined in their stated domains |
| Joint dependence for shocks used together | R7, R9 | a joint law or consistent conditional factorization is supplied; a product law needs conditional independence |
| Attainment and measurable policy selection | R7, R8 | an optimizer can be chosen as a measurable function; the maximum value alone does not select it |
| Root existence and measurable selection | R8, R10 | a policy can be obtained from the solution relation; uniqueness is sufficient for single-valuedness but does not replace all measurability conditions |
| Sufficient optimality conditions | R8, §4.5 | a chosen root or constrained stationary point is a global optimizer |
| Condition (F), domain coverage, and measurability | R10, §4.6 | the candidate relation defines the claimed policy; injectivity is one stronger sufficient condition for (F) |
| Transition consistency and coverage of explicit solutions | R2, R5, R10 | the identification rewritten at the continuation perch agrees with the explicit policy equation; the construction checks the coordinate line against the transition |
| A valid envelope theorem and derivative formula | R8, §4.4 | the stated derivative line is the derivative it claims, including constraints and transition derivatives |
| Differentiation under the integral sign | §4.4 | the arrival derivative line, with the law's factor, is the derivative of the arrival value |
| Domain and boundary restrictions | R6, §4.2 | formulas are defined at the parameter and state values being used |

These are sufficient premises or explicit requirements for particular
interpretations. Failure to verify one does not prove that the desired
conclusion is false; it means that the stated justification is unavailable.

The rules record each assumption beside the operator that needs it. The
stage records some of them as conditions, which `stage.obligations()` lists,
and §5.3 lists the ones that a rule says the stage records and that the
package does not yet record. Calibration decides a recorded restriction that
reads parameters alone and refuses the values at which it fails, so that
`ρ = 1` is refused for the body of `𝑢` in §4.2. A recorded restriction that
reads a state, a control or the argument of a function stays required and is
not checked. A file that satisfies R6 and is read by the
rules is a well-formed statement of a problem, not a proof that the problem
has a solution.

### 5.2 What the rules do not decide

The rules assign no numerical method. Quadrature for an expectation,
interpolation for an evaluation, the grid on which a policy is tabulated,
and the envelope step of a method attach afterwards
([Methodization](../04-methodization.md)). The grid on which a problem is
solved and the grid on which a population is simulated are two numerical
choices with separate accuracy criteria, and neither is part of the
declared sets or laws. Which quantities are recorded along a simulated path
is a matter for the simulation and not for the stage.

### 5.3 Open points

- A functional-form spelling of a value statement, with the state arguments
  written, is intended to be admitted under the same context as the perch
  form (§1.4); which such spellings the grammar admits is a separate
  question from what they mean.
- A tuple law can specify a joint distribution. Separate declarations on
  one edge are read as the product of §2.1, which the elaboration records as
  the condition `joint-distribution-factorization`. Any unsupported
  conditional-law spelling must be distinguished from the mathematical
  conditional kernel it intends.
- A specialized form for a certainty equivalent under recursive preferences
  remains outside these rules; explicit transformations are read in their
  written order (R11).

The table below lists the rules that the language is meant to have and that
the package does not yet check, or does not yet get right. Each row gives
the sections of this appendix that the rule concerns and states the rule,
then what the package does today, and the smallest text that shows it. The
rows follow the order of those sections. A rule that another page states
stands at the section of this appendix that it concerns, with a link to
that page.

A text is the text of a stage file, with one line of the file on each line
of the cell. A line `@methods: t` and the lines after it, up to a last line
that begins with `stage.`, are a methods file of the stage. A last line that
begins with `stage.` is a call on the stage that the text gives, in which
`methods` names that methods file. Where a
cell holds two texts, an empty line stands between them. `stage.fields()`
lists every field of a stage with its perch, its role and its declared set
([The stage](../API/stage/01-the-stage.md) §5).
[A piece](../API/stage/05-piece.md) describes the kernel of an operation in
its §2 and how a card is read in its §5.

<!-- The table between the two markers below is written by docs/_hooks/reference_pages.py from the tables `SEMANTIC_RULES` and `UNCHECKED_ELSEWHERE` of the package (`packages/bellman/bellman/semantic_rules.py`); change the tables and run the script, never the table by hand. -->
<!-- reference-table -->

| Rule | What the package does today | Smallest text |
|---|---|---|
| §1.1, §2.2. The mark `[~]` names a field at the decision perch, and a perch mark on a name agrees with the perch word of the side that lists the name. See also [Symbol conventions](../reference/symbols-conventions.md) §3 and [Perch tagging rules](13-perch-tagging-rules.md) §1. | The package reads `x[~]` as the bare name `x` and checks nothing about the mark. A name marked `[~]` on an arrival side or on a continuation side is read as the field of that side: for the text, `stage.fields()` lists `x` as a state at the arrival perch. | `@stage: t`<br>`[id=arvl_to_dcsn, (x[~] : ℝ) : !arvl -> (y : ℝ) : !dcsn] { y = x[~] }` |
| §1.1, R6. A backward line reads a decision state by its bare name, also where the stage places a state of the same name at another perch. | The package refuses the line under `name-in-scope`, with the bare name and with the name marked `[~]`. The refusal tells the author to write `w` for the decision state, which is the spelling that it has just refused. | `@stage: t`<br>`[id=dcsn_to_cntn, (w : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (w[>] : ℝ) : !cntn] { w[>] = w - c }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = c + V[>] + 0*w }` |
| §1.2, R4. A value line defines a function of the state at its perch, so outside an expectation it reads no shock that this state does not determine. | A shock that the header of a backward block lists, and that is drawn on an earlier edge or on no edge, is read as known on the lines of the block. The line is read, the rule that the card prints for the value function keeps the shock free, here `𝑉(m) = 𝑉≻(𝑔≻(m)) + y`, and no condition records the reading. | `@stage: t`<br>`y : ℝ`<br>`y ~ N(0, 1)`<br>`[id=dcsn_to_cntn, (m : ℝ) : !dcsn -> (a : ℝ) : !cntn] { a = m }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, y) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = V[>] + y }` |
| §2.1. The several sets in the type of one name have a number in common, also where one of them is a reserved set, a named set, a list of integers, a union or a difference, and where an endpoint of an interval is a formula. See also [Symbol conventions](../reference/symbols-conventions.md) §9.2, [Stages](../01-stage.md) §2 and [Types](../reference/types.md) §2.6. | The package compares the intervals of the type alone, by those of their endpoints that are numbers or ratios of two integers. A set of another form and an endpoint that is a formula enter no comparison. The package reads both texts, and `calibrate` then refuses every value given for `β`. | `@stage: t`<br>`β : ℝ₊₊ @ (-2,-1)`<br><br>`@stage: t`<br>`β : (0,1) @ (2*1, 3)` |
| §2.1. The value bound to a parameter lies in its declared set, also where that set is a set of extended reals, `ℝ̄`, `ℝ_{-∞}`, `ℝ_{+∞}` or `ℝ_{±∞}`. See also [Symbol conventions](../reference/symbols-conventions.md) §9.2 and [The binding verbs](../API/stage/09-binding-verbs.md) §2. | `calibrate` decides the membership of a number in a set of extended reals: a finite number lies in every such set, and an infinity in the sets that hold it, so that `inf` is refused for `ℝ_{-∞}`. A value that is no number, a string or the floating-point value NaN (not a number), is still bound there, and `stage.obligations()` lists its membership as the condition `calibration-domain-membership`, which stays required. In an interval whose bound is an expectation over a shock, such as `(0, E_{y}(y))`, it binds any number in the same way. | `@stage: t`<br>`x : ℝ_{-∞}`<br>`stage.calibrate({"x": float("nan")})` |
| §2.1, §2.5, R7. In `D_{c}(𝑢)` the subscript names a formal argument of the function that is differentiated. See also [Equation parsing rules](12-equation-parsing-rules.md) §5. | A subscript that names no formal argument of the function is read without a refusal: the text is read, although `𝑢` has the one argument `c` and the file declares no `x`. | `@stage: t`<br>`𝑢(c : ℝ₊₊) := c^2`<br>`𝑑𝑢 := D_{x}(𝑢)` |
| §2.1. The law of a shock gives probability only to values in the declared set of the shock, so a normal law of positive variance is not declared on a strictly positive set. See also [Equation parsing rules](12-equation-parsing-rules.md) §4. | The package reads the stage and records the requirement as the condition `law-support`, which `stage.obligations()` lists as required. Calibration decides the condition for a truncated lognormal law, and leaves it required for a normal, a lognormal and a uniform law. | `@stage: t`<br>`y : ℝ₊₊`<br>`y ~ N(0, 1)`<br>`[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (m : ℝ) : !dcsn] { m = k + y }` |
| §2.1, §2.3. The words `if`, `then` and `else` are no names also as the id of a line's annotation, `:: [id=if]`, as they are none as the id of a block. | The package reads a line annotated `:: [id=if]` and gives the line the place `arvl_to_dcsn.if`. A methods file cannot address that place: the entry `arvl_to_dcsn.if.method : …` is refused under `syntax`, with the sentence that `if` is no name. The id of a block, `[id=if, …]`, is refused under `syntax`. | `@stage: t`<br>`[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (m : ℝ) : !dcsn] {`<br>`m = k :: [id=if]`<br>`}` |
| §2.2, §2.4. Where one block writes a field and another reads it, the set written lies in the set read. See also [Symbol conventions](../reference/symbols-conventions.md) §9.3, [Stages](../01-stage.md) §2 and [Perch tagging rules](13-perch-tagging-rules.md) §2. | The package refuses under `set-mismatch` only an inclusion that it decides to fail. Where it cannot decide the inclusion, as with an endpoint that names a parameter, it reads the stage, records no condition, leaves the field with no declared set, and binds a calibration at which the inclusion fails, as the first text shows at `ā = 5`. Where the block that writes a control also holds a line marked `!doc` with the control on its left side, it compares no sets for the control: the second text is read, and without its `!doc` line it is refused under `set-mismatch`. | `@stage: t`<br>`ā : ℝ₊₊`<br>`[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (y : [0, ā]) : !dcsn] { y = x }`<br>`[id=dcsn_to_cntn, (y : [0, 1]) : !dcsn -> (w : ℝ) : !cntn] { w = y }`<br>`stage.calibrate({"ā": 5.0})`<br><br>`@stage: t`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] { a = m - c }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = c + V[>] }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊ @ !ctrl) : !dcsn] {`<br>`c = m/2 :: [id=half, !doc]`<br>`c = argmax_{cp}(cp + V[>])`<br>`}` |
| §2.3, R1, R10. A clause after `⟂` and the declaration of a multiplier are written in a policy block and in no other block. | The package reads both in a block of any kind. A clause after a line of a value block or of a forward block is read and enters no rule and no condition of the builder. A multiplier declared there is recorded as a multiplier at the continuation perch, no observable set is formed, and a value line that reads it keeps it free in its rule: for the text the card prints `𝑉(m) = 𝑐(m) + 𝑉≻(𝑔≻(m, 𝑐(m))) + ν≻`. | `@stage: t`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {`<br>`ν[>] : ℝ₊ ⟂ a >= 0`<br>`V = c + V[>] + ν[>] ⟂ m - c >= 0`<br>`}` |
| §2.4. The declared set of a name is the intersection of the sets written for it. See also [Symbol conventions](../reference/symbols-conventions.md) §9.2 and [Perch tagging rules](13-perch-tagging-rules.md) §2. | The package computes the intersection of sets that are written identically, of the sets `ℝ`, `ℝ₊` and `ℝ₊₊`, and of intervals whose endpoints are numbers or infinity. For other sets, such as a named set beside the set that defines it, or an interval with an endpoint that names a parameter, it records the field with no set and refuses nothing, and the stage loses the condition `range-compatibility` of the line that writes the field. | `@stage: t`<br>`Xp := ℝ₊`<br>`[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (y : Xp) : !dcsn] { y = x }`<br>`[id=dcsn_to_cntn, (y : ℝ₊) : !dcsn -> (w : ℝ) : !cntn] { w = y }` |
| §2.4. The sets written for one field at its several places have a value in common. See also [Symbol conventions](../reference/symbols-conventions.md) §9.3, [Stages](../01-stage.md) §2 and [Perch tagging rules](13-perch-tagging-rules.md) §2. | The package compares only the set of a block that writes the field with the set of a block that reads it. A set declared on a line of its own beside the set of a header, and the sets of two blocks that read the field, are not compared: the stage is read, and the field is recorded with no set. | `@stage: t`<br>`b : [-3, -1]`<br>`[id=arvl_to_dcsn, (b : ℝ₊) : !arvl -> (w : ℝ) : !dcsn] { w = b }` |
| §2.4, R1, R6. Every field, a shock included, has a declared set. See also [Stages](../01-stage.md) §2 and [Perch tagging rules](13-perch-tagging-rules.md) §2. | A field that the block headers list with no set at any place is read: `stage.fields()` prints it with no set, the signature of its builder prints `UNRESOLVED[k≺; argument set]`, and `calibrate` admits the stage. A shock with a law and no set is read as well. Only a name that the file declares nowhere is refused, under `name-in-scope`. | `@stage: t`<br>`[id=arvl_to_dcsn, (k) : !arvl -> (m) : !dcsn] { m = k }` |
| §2.4. In a declaration outside the blocks, a name inside a nested tuple is a parameter when no block header lists it, as a name of a flat tuple is. See also [Stages](../01-stage.md) §2. | The package reads the declaration, and a line may read the nested names, but `stage.par`, the list of the parameters, omits them. `calibrate` requires no value for them and judges no value against their sets. | `@stage: t`<br>`((p, q) : ℝ₊ × ℝ₊, r : ℝ)`<br>`stage.calibrate({"r": 1.0, "p": -1.0})` |
| R1. No statement of a block redefines an input of that block. | The package compares the lines of a block with one another only. A line that writes an input, a state, a control or a value, is read, the lines that follow read what the line writes in place of the input, and `calibrate` admits the stage. For the text the kernel of the operation is `𝐺(V≻, m, c) = c + 0`, in which the continuation value is unused. | `@stage: t`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {`<br>`V[>] = 0`<br>`V = c + V[>]`<br>`}` |
| R3, §4.7. Within an alternative of a branching block, a law of motion reads no continuation state of another alternative. See also [Perch tagging rules](13-perch-tagging-rules.md) §5. | The package reads such a law and puts the law of motion of the other alternative for the state that the line names: for the text the law of motion is `𝑔(a_d, d) = (a_d + a_d, a_d)`. | `@stage: t`<br>`[id=dcsn_to_cntn, (a_d : ℝ₊, d : !ctrl @ {work, retire}) : !dcsn -> ()] {`<br>`[label=work, () -> (a_w : ℝ₊) : !cntn] { a_w = a_d + a_r }`<br>`[label=retire, () -> (a_r : ℝ₊) : !cntn] { a_r = a_d }`<br>`}`<br>`[id=cntn_to_dcsn, (V_w[>] : ℝ @ !vlu, V_r[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = (V_w[>], V_r[>])[d] }`<br>`[id=policy, (V_w[>], V_r[>]) : !cntn -> (d : {work, retire} @ !ctrl) : !dcsn] { d = argmax_{d}(V_w[>], V_r[>]) }` |
| R4, R10. The two sides of an implicit equation are one relation: a term on either side that reads a field of a later perch is composed with the law of motion and, across an edge that draws a shock, stands inside an expectation over that shock. | Both sides are checked under `shock-observed`. The left side in the example binds `η` with an expectation. The policy relation's card prints the derivative under that expectation and leaves its evaluation at the law of motion implicit. | `@stage: t`<br>`η : ℝ₊₊`<br>`η ~ LogNormal(0, 1)`<br>`𝑑𝑢(c : ℝ₊₊) := c^(-2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊, η) : !dcsn -> (a : ℝ₊) : !cntn] { a = (m - c)*η }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { E_{η}(1*D_{a}V[>]) = 𝑑𝑢(c) }` |
| R4. A refusal for a dependence on a shock that the construction has not shown to cancel reports that measurability has not been established, and does not assert that the value is unknown. | The message of `shock-observed` says "so the value of V is not known at the arvl perch" wherever a forward block between the two perches lists a shock, also where its law of motion does not read the shock or the shock cancels in it, as in the text. | `@stage: t`<br>`y : ℝ`<br>`y ~ N(0, 1)`<br>`[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (m : ℝ) : !dcsn] { m = k + y - y }`<br>`[id=dcsn_to_arvl, (V : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] { V[<] = V }` |
| R5, R11. The rule of an output statement is its expression with the aliases of its block expanded, whether or not an intermediate line is marked `!node`. | Where a block writes an alias before the output statement, the card of the builder prints the line of the alias as the rule of the output, while the function that the operation computes is the expanded expression. For the text the card prints `𝑉(m) = 𝑐(m)`, and the kernel of the operation is `𝐺(V≻, m, c) = c + V≻`. | `@stage: t`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {`<br>`W = c`<br>`V = W + V[>]`<br>`}` |
| R5. Where a substituted alias depends on the output being determined, the statement gives the implicit relation of R10. | A line whose left side is the bare control and whose right side reads a field of a later perch through an alias is refused under `not-constructed`. The same reading written in the line itself, `c = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`, is read, and so is the alias inside `solve_{c}(…)`. | `@stage: t`<br>`𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {`<br>`z = D_{a}V[>]`<br>`c = 𝑑𝑢𝑖𝑛𝑣(z)`<br>`}` |
| R5, §4.3. A statement across two perches states one relation, which is rewritten at the perch whose map contains no unknown. Read at the decision perch, the final line `c = c[>]` of a policy block is an implicit equation in the control, which needs no coordinate line. | The package rewrites only the identification `c = c[>]` of a block that writes the coordinate line. A block that writes the candidate line and the final line without the coordinate line is read, as the text is: the card prints the type of `𝑐` in place of a rule for the operation of the final line, the record of that operation is `UNRESOLVED[policy.2:Pullback; solution coordinate relation]`, and no refusal, condition or diagnostic reports it. With the coordinate line `m[>] = a + c[>]` and another right side on the final line, `c = 1*c[>]`, the card prints `𝑐(m) = 1 · UNRESOLVED[c≻; free mathematical reference]`. | `@stage: t`<br>`𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {`<br>`c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`<br>`c = c[>]`<br>`}` |
| R7. The differentiability that `D_{c}(𝑢)` assumes is recorded as a condition of the stage, as the bijection that `Inv` assumes is. | `stage.obligations()` lists `inverse-function-domain` for `Inv(𝑑𝑢)`. For `D_{c}(𝑢)` it lists only `binding-domain`, which requires that the bound variable have a declared domain, and no condition of differentiability. | `@stage: t`<br>`𝑢(c : ℝ₊₊) := c^(-1)`<br>`𝑑𝑢 := D_{c}(𝑢)`<br>`𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)`<br>`[id=arvl_to_dcsn, (k : ℝ₊₊) : !arvl -> (m : ℝ₊₊) : !dcsn] { m = 𝑑𝑢𝑖𝑛𝑣(𝑑𝑢(k)) }` |
| R7. An order of expectations that needs a conditional law the file does not declare, a posterior among them, is refused under `conditional-not-declared`. | In a backward block the package refuses such an order under that rule. In the objective of a policy block it refuses the order first under `shock-observed`, with a message that asks for an expectation that the line already writes, "Write the expectation over it, `E_{ν}(…)`". | `@stage: t`<br>`ν : ℝ`<br>`ν ~ N(0, 1)`<br>`Ψ : ℝ₊₊`<br>`Ψ ~ LogNormal(ν, 1)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊, ν, Ψ) : !dcsn -> (a : ℝ₊) : !cntn] { a = (m - c)*Ψ }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = argmax_{c}(c + E_{Ψ}(E_{ν}(V[>]))) }` |
| R7. The set of a binder, `argmax_{var : set}`, is a named set or a correspondence applied to its arguments. See also [Constraints](../10-constraints.md) §1. | The package reads `set` as an expression and checks only that its names are declared. A parameter, a state, a number, a pair such as `(0, m)` or the name of a correspondence without arguments is read, and the policy card prints the maximization over it, as in `argmax_{cp ∈ ρ}`. | `@stage: t`<br>`ρ : ℝ₊₊`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = c + V[>] }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = argmax_{cp : ρ}(cp + V[>]) }` |
| R7. The body of a feasibility correspondence may be a finite set of integers, written as an integer range `{0, …, J}` or as a list `{0, 1}`. See also [Constraints](../10-constraints.md) §1. | Written alone as the body, either is refused under `not-constructed`. As a factor of a product, `{0, …, 3} × ℝ`, either is read. | `@stage: t`<br>`Γ(x : ℝ₊₊) := {0, …, 3}` |
| R7. `solve_{c}(r_1, …, r_k)` denotes the relation of the feasible unknowns that satisfy every residual equation. | For one unknown with two or more residuals the line is read without a refusal, the rule of its operation holds no residual, and the output of the operation is recorded as `UNRESOLVED[policy.1:Aggregation; solve relation]`. With the one residual `c - 1/2` the card prints `r₁ = c − 1/2` and `c = solve_{c}(r₁)`. | `@stage: t`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = solve_{c}(c - 1/2, c - 1/3) }` |
| R7. No method is attached to a statement marked `!doc`, which is a declaration and forms no operation. See also [Constraints](../10-constraints.md) §1. | The id of a `!doc` line is a place of the kind `statement`. `methodize` reads a representation such as `!Linear` typed there, holds the entry in `stage.methods`, and the policy card prints it under `Method`. | `@stage: t`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {`<br>`c = argmax_{c}(c + V[>]) :: [id=optimality, !doc]`<br>`c = m/2`<br>`}`<br>`@methods: t`<br>`policy.optimality.method : !Linear`<br>`stage.methodize(methods)` |
| R8, §4.6. An authored `c = evaluate(w[>], c[>], w)` with exact candidate and coordinate maps denotes evaluation of the relation that the candidate line and the coordinate line determine. With tabulated pairs it evaluates the interpolating representation that the methods file types at the line. | The package holds no definition of `evaluate`. The line is read, the rule of its operation prints `UNRESOLVED[evaluate; mathematical definition]`, and `stage.obligations()` lists the condition `external-callable-signature-and-provider` for `evaluate`. The printed rule and the condition are the same where the methods file types a representation such as `!Linear` at `policy.evaluate`. | `@stage: t`<br>`𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {`<br>`c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`<br>`m[>] = a + c[>]`<br>`c = evaluate(m[>], c[>], m)`<br>`}` |
| R8. Differentiability of a value at the point where a line reads its derivative is a condition that the stage records, the value being read as a locally Lipschitz function whose derivative is set-valued at a kink. | The package defines the derivative as the limit of the difference quotients, a single number, and a line that reads `D_{a}V[>]` records no condition. `stage.obligations()` lists differentiability only under `marginal-reading`, for a derivative line, and under `egm-eligibility`, for a policy builder under `!egm`. | `@stage: t`<br>`𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {`<br>`c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`<br>`m[>] = a + c[>]`<br>`c = c[>]`<br>`}` |
| R8. The lines of a solution method compute the policy of the declared maximization only under a condition, which the stage records under the method table's name for it. | In the method table only `!egm` names such a condition, `egm-eligibility`. Under `!time_iteration` or `!explicit` the lines of the method stand in place of the maximization in `stage.builder`, and `stage.obligations()` lists no condition under which they compute its policy. | `@stage: t`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = c + V[>] }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = argmax_{c}(c + V[>]) }`<br>`@methods: t`<br>`[id=policy, method : !explicit] { c = m/2 }`<br>`stage.methodize(methods)` |
| R10. A system of candidate statements is reached by one `solve` occurrence at its first statement, so that a method addresses the system as one place. | The package records the occurrence on some systems only. Where the first statement is `𝑑𝑢(c) = D_{a}V[>] ⟂ m - c >= 0`, as in the text, or `2*D_{a}V[>] = 𝑑𝑢(c) ⟂ m - c >= 0`, the block has no place `policy.solve`, and an entry that types a root finder there is refused under `name-in-scope`. Where the first statement is `𝑑𝑢(c) - D_{a}V[>] = 0 ⟂ m - c >= 0`, the block has the place. | `@stage: t`<br>`𝑑𝑢(c : ℝ₊₊) := c^(-2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { 𝑑𝑢(c) = D_{a}V[>] ⟂ m - c >= 0 }`<br>`@methods: t`<br>`policy.solve.method : !root_find`<br>`stage.methodize(methods)` |
| R10. The bound of a clause is written with `>=` or `<=`. | A clause with one bound and a strict sign is read as the clause with the weak sign: the card prints the sign as written, and the Kuhn–Tucker conditions that the package forms from the clause are those of the weak sign. A strict sign in a clause with two bounds is refused under `readable-form`. | `@stage: t`<br>`𝑑𝑢(c : ℝ₊₊) := c^(-2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { 𝑑𝑢(c) = D_{a}V[>] ⟂ m - c > 0 }` |
| R12. An authored `upper_env` denotes the upper envelope of R12: at each decision state, the control of a candidate that attains the greatest candidate value. | The package holds no definition of `upper_env` and checks none of its arguments. The line is read with no value candidate among its arguments, as in the text, and with one argument or four, and a method such as `!FUES` is typed at `policy.upper_env`. The rule of the line prints `UNRESOLVED[upper_env; mathematical definition]`, and `stage.obligations()` lists `external-callable-signature-and-provider` for `upper_env`. | `@stage: t`<br>`𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)`<br>`[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - c }`<br>`[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {`<br>`c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`<br>`m[>] = a + c[>]`<br>`c = upper_env(m[>], c[>])`<br>`}` |
| §5.2. A setting bound before a calibration lies in its declared set at the values that the calibration binds, a calibration that replaces an earlier one included. See also [Methodization](../04-methodization.md) §7 and [The binding verbs](../API/stage/09-binding-verbs.md) §3. | `configure` admits a value whose set names a parameter while no calibration is bound, and `calibrate` judges no setting bound before it. The value stays bound outside its set until a later `configure` refuses it under `setting-outside-set`. In the order `calibrate`, `methodize`, `configure`, the call of `configure` refuses the same value. | `@stage: t`<br>`R : ℝ₊₊`<br>`[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (m : ℝ) : !dcsn] { m = R*k }`<br>`@methods: t`<br>`tol_s : (0, R)`<br>`arvl_to_dcsn.method : !deterministic`<br>`stage.methodize(methods).configure({"tol_s": 5.0}).calibrate({"R": 1.04})` |
| §5.2. A bound of a grid lies inside the declared set of its coordinate, read at the calibrated value of each parameter that the set names. See also [Methodization](../04-methodization.md) §3.2 and [Settings](../../wiki/settings.md) §2. | `configure` decides the membership at the calibration that is bound, and refuses a bound outside the set there under `grid-bounds`. `calibrate` judges no bound of a grid again, so a calibration that replaces an earlier one leaves a bound outside the set of its coordinate, as in the text. Before a calibration is bound, `configure` refuses every bound on a coordinate whose set names a parameter, as not decidably inside the declared set. | `@stage: t`<br>`Xk := [k_lo, inf)`<br>`k_lo : ℝ`<br>`[id=arvl_to_dcsn, (k : Xk) : !arvl -> (m : ℝ) : !dcsn] { m = k }`<br>`[id=dcsn_to_arvl, (V : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] { V[<] = V }`<br>`@methods: t`<br>`n_k : ℕ`<br>`k_min : ℝ`<br>`k_max : ℝ`<br>`dcsn_to_arvl.evaluate.method : !Linear`<br>`dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))`<br>`stage.calibrate({"k_lo": 0.0}).methodize(methods).configure({"n_k": 5, "k_min": 1.0, "k_max": 2.0}).calibrate({"k_lo": 1.5})` |

<!-- /reference-table -->

## References

- Aliprantis, C. D., and Border, K. C. (2006). *Infinite Dimensional
  Analysis: A Hitchhiker's Guide*, 3rd ed. Springer. Theorem 18.19, the
  measurable maximum theorem.
- Benveniste, L. M., and Scheinkman, J. A. (1979). On the differentiability
  of the value function in dynamic models of economics. *Econometrica*
  47(3), 727–732.
- Boyd, S., and Vandenberghe, L. (2004). *Convex Optimization*. Cambridge
  University Press. §5.5.3, the Kuhn–Tucker conditions for convex problems.
- Carroll, C. D. (2006). The method of endogenous gridpoints for solving
  dynamic stochastic optimization problems. *Economics Letters* 91(3),
  312–320.
- Clausen, A., and Strub, C. (2020). Reverse calculus and nested
  optimization. *Journal of Economic Theory* 187, 105019. The envelope
  conditions under which a stated derivative line holds.
- Dobrescu, L. I., and Shanker, A. (2024). Using inverse Euler equations to
  solve multidimensional discrete-continuous dynamic models: a general
  method. Working paper, 7 December 2024. §2.1, Definition 1 and the inverse
  problem on observables; §3, Assumption 3.3, the rank condition, and
  Proposition 3.1, the sufficient first-order conditions; §4.1, equation
  (5), the constrained regions; §4.2, Claim 4.1, Theorem 4.1 and Claim 4.2,
  and the Poincaré–Miranda theorem for existence (online appendix,
  Corollary F.1).
- Druedahl, J., and Jørgensen, T. H. (2017). A general endogenous grid
  method for multi-dimensional models with non-convexities and constraints.
  *Journal of Economic Dynamics and Control* 74, 87–107.
- Kallenberg, O. (1997). *Foundations of Modern Probability*. Springer.
  Lemma 1.13 (Doob–Dynkin), Theorem 5.4 (disintegration), and Theorem A1.7
  (measurability of the inverse between Borel spaces).
- Milgrom, P., and Segal, I. (2002). Envelope theorems for arbitrary choice
  sets. *Econometrica* 70(2), 583–601.
- Nocedal, J., and Wright, S. J. (2006). *Numerical Optimization*, 2nd ed.
  Springer. Theorem 12.1, the first-order conditions.
- Rincón-Zapatero, J. P., and Santos, M. S. (2009). Differentiability of the
  value function without interiority assumptions. *Journal of Economic
  Theory* 144(5), 1948–1964.
- Rockafellar, R. T. (1970). *Convex Analysis*. Princeton University Press.
  Theorem 28.2, the existence of Kuhn–Tucker vectors, and Theorem 29.1,
  Kuhn–Tucker vectors as subgradients of the perturbation function.
- Sargent, T. J., and Stachurski, J. *Dynamic Programming*, Vol. II: the
  aggregator and the policy operator.
- Stokey, N. L., and Lucas, R. E., with Prescott, E. C. (1989). *Recursive
  Methods in Economic Dynamics*. Harvard University Press. Theorems 4.10
  and 4.11, the differentiability of the value function; Chapter 7,
  conditional expectation.
