---
audience: user
type: reference
---
# Perch tagging rules

> [!summary]
> A **perch** is an information set within a stage. Field declarations and typed block headers establish where quantities are interpreted; perch marks request arrival, decision, or continuation contexts. A control or shock listed on a block side follows its role-specific timing rule, rather than automatically becoming a state observed at that side.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](../01-stage.md): domains, roles, and headers; [Equation parsing rules](12-equation-parsing-rules.md): written syntax.
> **Formal account** — [Appendix C](14-appendix-c-syntax-to-semantics.md): state sufficiency and information checks; [Appendix D](15-appendix-d-node-tag-and-field-indexing.md): field indexing and implicit policy relations.
> **Used by** — [Field equations](../03-field-equations.md): consumption and expectations; [Branching](../05-branching.md): discrete alternatives.

## 1 What a perch mark requests

The stage marks identify information contexts, not calendar dates:

| Written reference | Requested context |
|---|---|
| `V[<]` | Arrival value. |
| `V` or `V[~]` | Decision value. |
| `V[>]` | Continuation value. |

A **field** is a quantity measurable with respect to its information context, meaning that its value is determined by the information available there. The same token at different perches can denote different fields. Equal spelling does not make `V[<]`, `V`, and `V[>]` equal, and an explicit mark does not establish that the requested field is defined.

For example, the discounting stage keeps the three asset coordinates explicit:

```bl
@stage: assets

Xa := ℝ₊

[id=arvl_to_dcsn, (a : Xa) : !arvl -> (a_d : Xa) : !dcsn] {
    a_d = a
}

[id=dcsn_to_cntn, (a_d) : !dcsn -> (a[>] : Xa) : !cntn] {
    a[>] = a_d
}
```

This complete transition fragment states the two identities; it does not infer them from a shared name. The declaration establishes unmarked `a` as an arrival input in the first block, whereas `a[>]` explicitly identifies the continuation output in the second. The decision state is named `a_d`. Bare references are resolved from declarations and the expression's context; the parser's identical treatment of a bare token and `[~]` does not itself determine its economic role.

We use `[<]`, `[~]`, and `[>]` for stage information. Although `.bl` inherits syntax from **dynspec**, an expression language, we do not transfer its steady-state reading of `[~]` into these equations, or use ordinary component indices such as `[1]` as alternative perch marks.

## 2 How headers establish context

A new field requires a domain and an established information context, supplied by its declaration or by a side of a block's header that names its perch. The construction checks all declarations for agreement. A later occurrence may restate a domain or role, but cannot silently replace it. A side may omit its perch word only when the existing declarations determine its context without guessing.

> [!ast]- Abstract grammar: Signature
> This [ASDL](../../wiki/asdl.md) projection gives the constructor `Signature`, by which the grammar records a block's header, and the simple coordinate case. Other `typer` and coordinate alternatives remain in the full grammar; the box does not redefine them.
>
> ```asdl
> typer = Signature(subject source, classifier* source_types,
>                   subject target, classifier* target_types)
> subject = Subject(coordinate* coordinates)
> coordinate = Coordinate(identifier stem, index? at,
>                         classifier* classifiers)
> classifier = Domain(setexpr space)
>            | Infoset(perch side)
>            | Role(role kind)
> perch = Arrival | Decision | Continuation
> ```
>
> **Keys.** `source` and `target` are ordered subjects with side types; `coordinates` lists their members; `stem` names a coordinate, `at` records optional indexing, and `classifiers` lists type components. `index`, `setexpr`, and `role` are sorts in the full grammar. `*` means a list and `?` optional.
>
> **Head.** A block header writes the two subjects around `->`, with `:` for type information.
>
> **Denotes.** The header specifies the inputs and outputs of the block's equations, interpreted under [Appendix C](14-appendix-c-syntax-to-semantics.md) §2.2.
>
> **Status.** The grammar records the header's shape. Construction checks role and perch agreement, output definitions, and the exceptions below; it rejects a contradictory declaration at the offending header or declaration's [source span](../../wiki/source_span.md).

The side annotation normally supplies the information context of its state or value coordinates. There are three exceptions:

- A decision control remains a decision control when listed beside continuation inputs. Listed there, it is the coordinate at which the block's lines are read, not an input of the block; it does not redefine the control as a continuation-state coordinate.
- A shock listed as a transition argument is not thereby known at the input perch. Its law and transition use establish the relevant uncertainty and timing.
- A state of the perch at which a backward block's output stands is a coordinate of that output and is listed on no backward header; a line of the block reads it without a listing, and a listed state is refused under `header-coordinate`. A state of the block's input perch is reached through the law of motion alone. A backward header therefore lists the value fields the block reads and writes and the controls at which its lines are read ([Appendix C](14-appendix-c-syntax-to-semantics.md#r1-blocks-and-their-headers) R1).

For example, the consumption backward block lists `(V[>], c)` on its continuation side. The role `!ctrl` established for `c` still identifies a decision control. The calculation of value uses the chosen control and continuation value together. The continuation calculation must retain any decision information it needs; a smaller continuation state vector alone need not encode the control.

Parameters are constant with respect to stage uncertainty and have no perch. They still require declarations and admissible values. A parameter name declared by two stages of one period denotes one period parameter; this does not identify either stage's fields. Numerical settings are supplied separately and are not economic fields.

## 3 Shocks and expectations

In the [income transition](12-equation-parsing-rules.md#4-shock-laws), `y` is listed beside arrival assets `b`, but income is realized between arrival and decision. The state equation `w = y + b*R` makes income available in decision cash on hand. The backward equation `V[<] = E_{y}(V)` uses the shock's conditional law to form arrival value.

Writing an explicit perch mark cannot make an unobserved shock known. For example, replacing that arrival equation by `V[<] = E_{y}(V) + y` leaves an unintegrated shock outside the expectation. Construction must reject this use when `y` is unobserved at arrival, identifying the statement and offending occurrence. The nested expression `E_{y}(V + y)` has a different scope: both terms are integrated, subject to integrability.

An ordered joint distribution for `(ε, η)` determines a joint expectation over those shocks. The order of the inputs a header lists implies nothing about dependence. Separate marginal laws do not establish the joint law required for a complete connection route; independence must be stated in the model rather than inferred from separate declarations. Constant parameters describe an IID draw only when the declared distribution is conditional on earlier information and does not depend on that information.

## 4 Fields at another perch

A reference at another perch needs an equation or supported transition interpretation that defines it there. The mark is not an inverse-transition operator. For instance, a forward equation defining decision cash on hand from arrival wealth and income does not automatically recover the two inputs from cash on hand.

The consumption example deliberately defines `c[>]` and `m_d[>]` as candidates indexed by continuation savings. Its final `c = c[>]` is an implicit relation between the policy and the candidate: read at the decision perch, it relates them through the savings transition; rewritten at the continuation perch, it relates them through the coordinate map that `m_d[>] = a + c[>]` defines, and the construction states it there ([Appendix C](14-appendix-c-syntax-to-semantics.md) R5 and R10). The continuation candidate and decision policy are distinct objects; matching their values requires the relation and the function-selection conditions in [Field equations](../03-field-equations.md#3-an-implicit-policy-relation).

A **state vector** collects chosen state coordinates. Representing a field as a function of that vector requires that those coordinates contain enough information to determine the field, as well as the relevant conditional laws. Perch measurability alone does not establish this. Nor does writing three state vectors prove their generated information sets are nested: a state transition can discard information. [Appendix C](14-appendix-c-syntax-to-semantics.md) R5 separates these assumptions from syntax.

## 5 Discrete alternatives

A branching stage declares a finite-valued control and the state outputs for each labeled alternative. For example, the retirement stage declares the labels `work` and `retire`, distinct continuation fields `V_w[>]` and `V_r[>]`, and selects from their ordered tuple using the control `d`. The branch labels identify alternatives within the continuation interface; they do not add calendar dates or new perch kinds. [Branching](../05-branching.md) supplies the complete source.

Within each alternative, the fields and functions must use that alternative's declared state domain. The value comparison also requires a common objective and the declared label order. Ordinary tuple selection is distinct from a perch mark, so `(V_w[>], V_r[>])[d]` first names continuation quantities and then chooses a tuple entry.
