---
audience: user
type: reference
---
# Appendix D — Nodes and field indexing

> [!summary]
> A statement's equations determine its mathematical meaning; `!node`
> marks a statement as an authored node, a computation that can be named
> and addressed separately.
> Perch marks identify fields in their information context, while other
> bracket selections require a declared collection or family. This appendix
> explains how these distinctions preserve composition in both the field
> diagram and the functional diagram that Appendix C reads.

> [!info]- Relationship with other documents
> **Formal account** — [Fields, functions and types](../../bellman-calculus/04-fields%2C%20functions%20and%20types.md): field and functional diagrams; [Operators and builders](../../bellman-calculus/05-Operators%20and%20builders.md): operations within a block.
> **Builds on** — [Appendix C](14-appendix-c-syntax-to-semantics.md): the declared context, substitution, and the conditions for interpreting equations as functions or relations; [Perch tagging rules](13-perch-tagging-rules.md): the information sets of fields.
> **Used by** — [Methodization](../04-methodization.md): numerical methods address the computations identified here.

## 1 What the marks describe

The rules concern a `.bl` stage file. A **typing context** collects the
declared domains, roles, perches, the typed arguments of the declared
functions, and shock laws. A
**perch** is an information set, and a **field** is a random variable
measurable at its declared perch. Representing that field by a function of
the declared state requires the sufficiency assumptions of
[Appendix C](14-appendix-c-syntax-to-semantics.md) §1.2 and R5.

Three pieces of syntax answer different questions:

- A block's header, with its typed inputs and outputs, states which
  quantities it relates. Its equations determine the relation or operator.
- An annotation such as `:: [id=shift, !node]` names a statement and marks
  it as an authored node: a computation to inspect or realize as a unit
  within the block.
- A perch mark such as `[>]` identifies a field at continuation. It does
  not supply a state space, a representative function, or a numerical grid.

For example, this transition fragment has one real input and two real
outputs. The intermediate result `y` is also a declared output:

```bl
[id=transform, (a : ℝ) : !dcsn -> (y : ℝ, q : ℝ) : !cntn] {
    y = 2 + a    :: [id=shift, !node]
    q = 4*y      :: [id=scale]
}
```

The header identifies a decision-to-continuation transition. Renaming
`transform` or `shift` does not change that transition. The `!node` on the
first line keeps that line as a unit of its own; the addition and
multiplication are mathematical operations whether that mark is present
or absent.

The statement mark is `!node`, written inside the annotation after `::`.
Methods remain in a separate methods file, and neither a block identifier nor
a method name selects the block's mathematical formula.

## 2 What an equation determines

An explicit definition such as `y = 2 + a` gives a function when its
arguments, domains, and dependencies are established. In §1, with
$a\in\mathbb R$, its representative is
$\mathrm g:\mathbb R\to\mathbb R$, $\mathrm g(a)=2+a$.
The field equation and the function equation are related as Appendix C
specifies; they are not the same kind of object.

An implicit equation instead states a relation. For example, suppose the
stage declares $a=w-c$ and the continuation candidate
$c_\succ=\mathrm f(a)$. The policy equation `c = c[>]` then gives
$$
\{(w,c):c=\mathrm f(w-c),\ (w,c)\text{ is feasible}\}.
$$
It defines a policy only where a unique solution, or a specified selection
from its solutions, meets the required measurability conditions. Adding
`!node` makes the relation separately addressable; it proves neither
existence nor uniqueness and does not make a root an optimizer
([Appendix C](14-appendix-c-syntax-to-semantics.md) R8 and R10).

An **alias** is an explicit definition of an intermediate quantity that
can be substituted at its uses. Substitution must preserve local binding,
domains, shock dependence, and any retained control arguments. An implicit
condition cannot be used as an assignment before its unknowns are
determined. An equation defining a block output must continue to determine
that output even if its expression is also substituted elsewhere.

A statement marked `!doc` is documentation and contributes no defining
equation. Consequently, adding `!doc` can remove a condition from the
mathematical problem; it is not equivalent to adding or removing `!node`.
An identifier alone changes neither kind of statement.

## 3 Authored nodes and operator occurrences inside equations

There are three levels of detail within the diagrams of a stage:

1. A block is represented as a unit with its declared inputs and outputs.
2. A statement marked `!node` specifies a unit within that block.
3. The mathematical operations inside each equation remain available at
   finer detail, including their arguments and local binding.

A computational statement is an **authored node** exactly when it carries
`!node`.
An **operator occurrence** is a particular use of an operation within an
expression. An expectation, `argmax`, `solve`, `upper_env`, or an authored
`evaluate` remains an operator occurrence even when its statement is
unmarked. It does not thereby make that statement an authored node.

For example, this arrival-value fragment contains two expectations and
no authored nodes:

```bl
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<]      = E_{y}(V)          :: [id=value]
    D_{b}V[<] = E_{y}(R*D_{w}V)   :: [id=marginal]
}
```

The surrounding stage supplies the transition `w = R*b + y` from the
arrival state `b` to the decision state `w`, the law of `y`, the return
parameter `R`, and the decision value field. The second line is a
derivative line: it states the derivative of the arrival value in `b`,
with the factor `R` that the transition contributes. Both integrations
belong to the mathematical interpretation, subject to Appendix C R7. A
numerical method can address them without adding `!node` to either line.

Arithmetic and the applications of declared functions also remain, within
the equations that a block or a statement marked `!node` carries. Being
mathematically represented does not make
every operation
a separate place: a **place** is an operator at which a methods file can
type a method, which the stage lists with its path and its kind
([Methodization](../04-methodization.md) §2; §6).

These three levels occur within both the field diagram and the functional
diagram, and replace neither. Both sides of an implicit equation and the
rule relating the two diagrams must remain available; a printed formula or a
method attachment cannot replace those mathematical objects.

## 4 Composition and substitution

In §1, let $\mathrm g(a)=2+a$ and $\mathrm h(y)=4y$, both maps from
$\mathbb R$ to $\mathbb R$. The second output is
$$
\mathrm q(a)=\mathrm h(\mathrm g(a))=4(2+a).
$$
The whole transition has type $\mathbb R\to\mathbb R\times\mathbb R$
and is
$$
\mathrm F(a)=\bigl(\mathrm g(a),\mathrm h(\mathrm g(a))\bigr).
$$
Substituting `2 + a` for `y` in the second equation preserves $\mathrm F$.
Deleting the first output would not: the block promises both `y` and `q`.
Keeping `shift` as a node records the intermediate computation while the
composite function remains $\mathrm F$.

Composition requires matching types. For general maps
$\mathrm g:A\to B$ and $\mathrm h:B\to C$, the composite
$\mathrm h\circ\mathrm g:A\to C$ is defined because the output of
$\mathrm g$ is an admissible input to $\mathrm h$. If the second operation
also needs a shock or another state argument, that argument must be
retained; a node does not supply it.

A node also does not hide dependencies. If `y` depends on a shock,
substitution must retain that dependence. An expectation integrates over
that shock only when its stated binding and law require it; other free
arguments remain free. The formal arguments of functions and
operator-bound variables keep their own scope. A perch mark binds no
variable; a statement identifier binds no mathematical argument
([Appendix C](14-appendix-c-syntax-to-semantics.md) R2, R4, R5, and R11).

**Denotation** means the mathematical object represented by an expression
or diagram. For the same typed equations, adding or removing `!node`
preserves their mathematical denotation while changing the recorded
nodes: the marked statement's result becomes a function
that later statements consume and a method may represent exactly or by
an approximation. An operation occurring inside an unmarked statement
also returns a function of the remaining arguments, but that function is
not an authored object: it is obtained exactly through its definition and
admits only the operation's own methods, never a representation
([Appendix C](14-appendix-c-syntax-to-semantics.md) R7, the result of an
occurrence). #functional-semantics The diagrams therefore need not be identical.
Likewise, equality of mathematical functions does not guarantee identical
floating-point results after different numerical methods are attached.

> [!note]- Technical details
> The substitution argument concerns equal denotations on the required
> domain, with local binding preserved. Almost-sure equality under one
> state law alone does not justify substituting representatives at states
> reached under a different policy or initial law. The distinction and
> the required representative choices are stated in Appendix C R5.

## 5 Field marks, collection selection, and function arguments

### 5.1 Perch marks

`V[<]`, `V`, and `V[>]` identify the arrival, decision, and continuation
value fields. `V[~]` is an explicit spelling of the decision field `V`.
For other names, the complete declarations and headers establish the
native perch. A non-native marked occurrence, such as `c[>]`, needs a
definition or supplied interpretation at that perch; it is not
automatically equal to the decision control `c`.

The state at a perch can have several coordinates. A field marked `[>]`
may therefore be represented by a function of a vector, not necessarily
one scalar asset. Its arguments follow from the declared state and the
equations, under the sufficiency assumptions of Appendix C. The mark
alone establishes no factorization through a particular coordinate.

### 5.2 Collection and family selection

Brackets other than the perch marks require an appropriate collection or
family. For a tuple, positions start at one: `(y, q)[1]` selects `y`.
A named selector must resolve to a declared key or to a selector with a
compatible domain. For example, the retirement choice uses

```bl
V = (V_w[>] - δ, V_r[>])[d]    :: [id=choice_value]
```

Here the surrounding declaration gives `d` the ordered labels
`{work, retire}`. `work` selects the first expression and `retire` the
second. Each expression must have the required value type. The tuple of
alternative values is distinct from the labeled union of successor state
spaces ([Appendix C](14-appendix-c-syntax-to-semantics.md) R3 and §4.7).

An indexed collection may have a parameter-defined number of entries.
With an integer parameter `J`, `L_J := {1, …, J}` and `δ : L_J → ℝ`,
a name `j : L_J` selects the entry `δ[j]`; `dist : L_J × L_J → ℝ₊`
is selected as `dist[j][i]`
when both names have suitable declared domains. The selector can be a
state, a control or a parameter. Its declaration must establish membership
in the index set; declaring it only on `ℕ` does not do so.
[Symbol conventions §9.2.1](../reference/symbols-conventions.md#921-finite-indexed-data)
states the admitted index sets and how calibration associates keys with
entries.

For a product-valued field, `q[>][1]` first identifies the continuation
field and then selects its first component. Put the perch mark before
component selectors. An integer literal in brackets selects a component by
position; it is not an inter-period time shift.

> [!warning] A name in brackets does not declare an information set
> The spellings `q[a]` and `q[y]` do not by themselves declare that `q` is
> a function of the state `a` or the intermediate value `y`. They require
> an established indexed object and the appropriate selection rule. They
> neither bind the bracketed name in an equation's right side nor provide
> missing domains or measurability assumptions. A state can select an entry
> when its declared domain supplies suitable keys, as above. To apply a
> declared function to a state, use parentheses, `𝑞(a)` (§5.3).

### 5.3 Explicit function arguments

Use a declared function when the intended mathematical map and its
arguments should be explicit:

```bl
𝑔(a : ℝ) := 2 + a
𝑞(y : ℝ) := 4*y
```

The second declaration defines a function on $\mathbb R$; its formal
argument `y` is local to that function. In a field equation, `𝑞(y)` applies the
function to the field `y`, while `𝑞(𝑔(a))` writes the composition directly.
Neither application changes the field's declared perch.

Suppose $q_A:A\to Q$ is a function on a state space $A$, with value set
$Q$, and $g:A\to Y$ is an intermediate map. Representing $q_A$ using only
that intermediate value requires $q_Y:g(A)\to Q$ with
$q_A=q_Y\circ g$. Such a function exists exactly when
$g(a_1)=g(a_2)$ implies $q_A(a_1)=q_A(a_2)$. To construct it, set
$q_Y(g(a))=q_A(a)$; the condition makes the result independent of the
chosen $a$. Conversely, the composition forces equal $g$ values to give
equal $q_A$ values. Measurability of $q_Y$ remains a separate requirement.
A bracket spelling cannot establish that equation. Appendix C R10 uses
the same condition when candidate parameters represent a policy.

## 6 Addresses and numerical methods

An **address** identifies a declared block, statement, or operation for
inspection or method attachment. The address says where to attach; the
typed equations say what computation is being approximated. In the
examples above:

- `transform` addresses the whole transition, and `transform.shift`
  addresses the statement marked `!node`.
- `dcsn_to_arvl.value.E_y` addresses the expectation in the named value
  equation. The statement's `id=value` identifies that occurrence; it does
  not make the statement a node.
- A stage-wide `E_y` address applies to the occurrences of expectation
  over `y` covered by that methods interface. A statement-qualified address
  distinguishes the integration in the value line from the one in the
  derivative line when they need different attachments.

Use explicit statement identifiers for stable addresses. A line number is
not a method address: inserting documentation must not redirect an
attachment. Renaming identifiers consistently in the stage and its methods
file preserves the equations and the intended attachments. Identifiers
must be unambiguous in their enclosing scope.

An address used for inspection is not necessarily a place. An unmarked
scalar alias can remain identifiable without defining a separate numerical
task. An authored node, an operator occurrence and the Evaluation of a
builder are places of different kinds, and typing a method requires a place
of a kind the method admits and a method suitable for its mathematical
operation ([Method types](../reference/methods.md)).

The address `<block-id>.<statement-id>.<operator>` must identify the
intended occurrence. If a statement contains two indistinguishable
occurrences under that address, the attachment is ambiguous; it must not
silently choose the first. A stage-wide attachment, where supported, is
an explicit choice to govern the corresponding group.

Methods and their settings are written separately from the stage. A
quadrature rule approximates an integral; a root finder approximates a
solution of the stated relation. Neither supplies a missing shock law,
constraint, or optimality condition. A numerical grid is part of a chosen
representation, whereas the field's domain belongs to the model: the
methods file writes the grid by its own entry at the place,
`cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))`, one
factor for each coordinate, and the method by its basis, such as `!Linear`
(see [Methodization](../04-methodization.md) §3.2).

**The name `evaluate`.** An authored `evaluate(knots, values, x)` denotes
evaluation of a stated representation, with coordinates first and values
second. The numerical interpolation and extrapolation must be specified
as Appendix C R7 requires. It is an operation inside its line, with
declared arguments, and a method attaches to it at its own address,
`<block-id>.<statement-id>.evaluate`, where a representation needs no grid,
since the first argument holds the knots; `evaluate` alone names the one
authored occurrence of a stage and is refused where the stage authors
none or several. A methods file also writes `evaluate` after a block id
for the [Evaluation](../reference/operations.md#evaluation) that closes
the builder, the place of a declared output representation, and may say
which stored object it types: `policy.evaluate` for the policy function
of the policy builder, `cntn_to_dcsn.evaluate` for everything the
Evaluation of a backward value builder stores, the value function and the
derivative of it that a derivative line states, or `cntn_to_dcsn.evaluate[V]`
and `cntn_to_dcsn.evaluate[D_{m_d}V]` for each of them apart, with a grid
of its own. That place names an operation every such builder closes with;
it does not assert that an `evaluate` expression was written in the stage,
and it creates none. A representation typed on the builder itself is
refused under `method-admission`. See [Methodization](../04-methodization.md)
§2 for the written form.

## 7 Policy relations and numerical decomposition

The policy block of the consumption stage `cons` of Appendix C §4.2,
written in the interior form with its candidate line an equation, provides
an example in which an unmarked statement is a relation rather than an
alias:

```bl
[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])    :: [id=InvEuler]
    m_d[>] = a + c[>]             :: [id=endoggrid]
    c      = c[>]                 :: [id=cons_choice]
}
```

The surrounding `cons` stage declares the transition $a=m_d-c$ and the
inverse marginal-utility function. Its continuation value, and so the
derivative `D_{a}V[>]` that the candidate line reads, is already
discounted; no discount factor should be inserted into this fragment.
Appendix C §4.2 derives its functions and §4.5 states sufficient
conditions and a constrained extension; the methods file
`applications/portfolio-choice/declaration/stages/cons/methods.bl`, beside `cons.bl`, writes the candidate line as the
inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`, whose clause states the
borrowing constraint (Appendix C §4.5).

The first two lines define the candidate and its decision coordinate.
The third identifies the decision control with the candidate. Read at the
decision perch, it determines the control implicitly through the
transition; rewritten at the continuation perch, through the coordinate
map of the second line, it states the policy at the cash on hand of each
saving, the relation the construction states (Appendix C R5 and §4.3). It
remains a relation even though it has no `!node` mark and contains no
written `solve` operator: the [policy builder](../../wiki/builder.md), the
operator the policy block denotes, holds it as an operation whose
output is its own unknown. A method may address it as a solution, and the
methods interface records a `solve` place for it; that recognition does not
turn it into an authored `solve` expression or erase either side of the
equation.

The endogenous grid method approximates this relation by computing
candidate pairs and representing the resulting policy, which the pairs
determine under Appendix C R10's consistency, single-valuedness, coverage,
and measurability conditions. When the final line is omitted, no line
states the policy and the block is refused under the rule `output-defined`
(Appendix C R1 and §4.6); an implementation does not invent a missing final
equation or a place from the names of the lines.

Choosing a numerical method does not add `evaluate`, `upper_env`, or
`!node` statements to the model. If a method internally interpolates or
compares candidate values, those computations realize the stated problem.
An authored `upper_env` is instead a mathematical operation in its own
right, with the selection and attainment requirements of Appendix C R12.
A method's internal steps may be displayed for inspection, but must remain
distinguishable from the authored equations and their nodes.

## 8 Compositional meaning

The **compositionality** requirement is that the meaning of an expression
is determined by the meanings of its parts. For a language with names,
those meanings retain their declared context, free arguments, and local
binding. An operator's interpretation can then combine them without
guessing what a statement identifier was intended to mean. This is the
denotational discipline described by Hutton (2023, §3), applied here to
the field equations and typed operations of Appendix C.

It permits substitution of equal mathematical meanings within a valid
context. It does not equate every diagram recording those meanings:
an annotated diagram also records authored addresses and nodes.
Removing a `!node` mark can preserve the represented mathematical function
or relation while changing the diagram available for method attachment.

> [!note]- Technical details
> A syntactic **sort** is a category of expressions. For an ordinary
> many-sorted signature, which lists constructors together with their
> input and output sorts, the freely generated terms form an
> initial algebra. Initial means that there is a unique map preserving
> those constructors into each specified algebra of the same signature
> (Goguen, Thatcher, Wagner, and Wright 1977, §2, Proposition 2.1).
> The target must already specify the mathematical sets and operations.
> The theorem does not choose missing interpretations, solve implicit
> equations, or prove their analytic assumptions. Binding and substitution
> require a representation that accounts for contexts; a many-sorted list
> of constructor arities alone is not a proof that those binding rules
> are respected (Lamiaux and Ahrens 2024, §1.1.1).

The formal implementation must preserve these distinctions when it
constructs the two diagrams. This appendix specifies their mathematical
meaning and authored nodes; it does not prescribe parser constructors,
storage records, or an execution order for a numerical solver.

## References

- Goguen, J. A., Thatcher, J. W., Wagner, E. G., and Wright, J. B. (1977).
  [Initial Algebra Semantics and Continuous Algebras](https://doi.org/10.1145/321992.321997).
  *Journal of the ACM* 24(1), 68–95. §2, especially Proposition 2.1.
- Hutton, G. (2023).
  [Programming language semantics: It's easy as 1,2,3](https://people.cs.nott.ac.uk/pszgmh/123.pdf).
  *Journal of Functional Programming* 33, e9. §3, pp. 3–4.
- Lamiaux, T., and Ahrens, B. (2024).
  [An Introduction to Different Approaches to Initial Semantics](https://arxiv.org/abs/2401.09366).
  §1.1.1, on syntax with binding and substitution.
