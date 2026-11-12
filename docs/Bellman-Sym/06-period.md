---
title: Period Syntax
tags:
  - trellis
  - syntax-rules
status: Draft — revised 2 October 2026
related:
  - "[[07-trellis]]"
  - "[[08-periods-and-trellis]]"
  - "[[08-bellman-factory]]"
  - "[[01-stage]]"
date: 2026-10-02
audience: user
type: user-guide
---

# Period Syntax

<!-- tags: backus-functionals, function-composition -->

> [!summary]
> A **period** is a collection of stage occurrences and the connections between their fields. We keep this outer description in YAML and write the stage files in `.bl`. Field dependencies determine the order of computation; the order of names in the stage list does not. The period file is a template that a trellis file repeats: written as a list of stage keys it binds nothing, and a recipe supplies each stage's file and values; written as a mapping from each key to a record, it carries them itself ([Trellises](07-trellis.md) §3).

> [!info]- Relationship with other documents
> **Builds on** — [Stages](01-stage.md): typed fields and stage files; [Branching](05-branching.md): separate continuation alternatives.
> **Used by** — [Trellises](07-trellis.md): ordering periods; [The Bellman factory](08-bellman-factory.md): loading, elaborating and binding every stage occurrence of a trellis.
> **Formal account** — [Periods and the trellis](../bellman-calculus/08-periods-and-trellis.md): composition through compatible fields.

## 1 Period YAML

The household observes resources, consumes, and invests its remaining assets before next period's income and return are drawn. We express this sequence with the beta-free `cons.bl` from [Field equations](03-field-equations.md#1-consumption-and-savings) and the `disc.bl` and `port.bl` sources below. The discount stage multiplies value by beta, while its asset transition is an identity. It adds no economic decision.

Save this period template as `period.yml`:

```yaml
!period
name: consumption_investment
stages:
  - cons
  - disc
  - port
connectors:
  - {k_next: k}
```

The recipe beside the template associates each key with its stage file, `stage: cons.bl`, and with the files of its parameter values, settings and methods ([Trellises](07-trellis.md) §§1, 5); the template itself binds nothing. Consumption's outgoing `a` and discounting's incoming `a` are different fields; their compatible, uniquely selected same-name pair connects them. The authored connector pairs discounting's outgoing `k_next` with investment's incoming `k`. The period begins with observed resources `m` and ends with next resources `m_next`; their join across periods is kept outside this file.

| Key | Contents |
|---|---|
| `name` | A documentation label for the period template. |
| `stages` | A list of distinct stage-occurrence keys, or a mapping from each key to a record that names its stage file and its bindings ([Trellises](07-trellis.md) §3). |
| `connectors` | A list of authored pairs from continuation state fields to arrival state fields; paired names may agree or differ. |

A **stage occurrence** is one use of a stage file in a period: the file elaborated at that position, with its own field names, methods and settings. A parameter name declared by two stages of one period denotes one shared period parameter; it need not have the same value in another period. A stage key identifies that use; the file's declared name remains its `.name`, the same for every stage occurrence of the file, and may differ from an application-supplied key, and the position is recorded in the occurrence's provenance. Missing or duplicate keys are errors. Repeating a stage file requires distinct stage-occurrence keys, not repeated list entries with the same key.

A stage's source is a `.bl` file, named by the recipe under `stage:` or by a record under the same key, or in-memory text with an explicit origin ([Trellises](07-trellis.md) §6). No stage is written inline in the template, which remains YAML and describes the outer composition only, separately from the grammar of the statements inside a `.bl` stage.

### 1.1 Discounting

Save the following value-only stage as `disc.bl`. Both asset boundaries are nonnegative and measured in the same units. This example calls its outgoing assets `k_next` to distinguish the next investment input. A distinct name is not required to avoid automatic matching: selection considers eligible fields, their stage addresses, compatibility and the whole period's dependencies. The position of investment relative to the period boundary is stated by its connector.

```bl
@stage: disc
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d) : !dcsn -> (k_next : ℝ₊) : !cntn] {
    k_next = a_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
```

The backward equation discounts the supplied continuation value once. Consumption itself contains no beta. This variant omits the marginal-value output in `applications/portfolio-choice/declaration/stages/disc/disc.bl` and gives outgoing assets a distinct name; it is the source used on this page.

### 1.2 Investment

Save this stage as `port.bl`. The household chooses its risky share `ς` in `[0,1]` before observing either the risky gross return `Ψ` or next income `θ`. The safe gross return is `R`. Both shocks are positive, so next resources are positive even when capital is zero.

For each shock, log values are normal with the displayed mean and standard deviation. In addition, we specify the ordered joint conditional law

$$
K(d\psi,d\theta)=\nu_\Psi(d\psi)\nu_\theta(d\theta),
$$

constant given investment-decision information, where $\nu_\Psi$ and $\nu_\theta$ are the two lognormal laws. This states both independence between the shocks and independence of their joint draw from earlier observations. The two marginal declarations in the source do not encode that additional joint-law assumption; it accompanies this example.

```bl
@stage: port
R : ℝ₊₊
μ_Ψ : ℝ
σ_Ψ : ℝ₊
μ_θ : ℝ
σ_θ : ℝ₊
Ψ : ℝ₊₊
θ : ℝ₊₊
Ψ ~ LogNormal(μ_Ψ, σ_Ψ)
θ ~ LogNormal(μ_θ, σ_θ)
[id=arvl_to_dcsn, (k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn] {
    k_d = k
}
[id=dcsn_to_cntn, (k_d, ς : [0,1] @ !ctrl, Ψ, θ) : !dcsn -> (m_next : ℝ₊₊) : !cntn] {
    m_next = k_d*(ς*Ψ + (1-ς)*R) + θ
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = E_{Ψ,θ}(V[>])
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V[>]) : !cntn -> (ς) : !dcsn] {
    ς = argmax_{ς}(E_{Ψ,θ}(V[>]))
}
```

For capital $k\geq0$ and share $s\in[0,1]$, next resources are $M(k,s,\Psi,\theta)=k(s\Psi+(1-s)R)+\theta$. Given a continuation function $v:(0,\infty)\to\mathbb R$ of next resources, the portfolio objective is $E[v(M(k,s,\Psi,\theta))]$. Assume it is finite, jointly measurable in capital and share, and continuous in the share; select a measurable maximizer. Continuity on the compact share interval then gives attainment. Continuous $v$ with a suitable integrable bound can justify the required expectation continuity; finite pointwise expectations alone do not.

At zero capital every share gives resources `θ`; choose share zero there. The operative `argmax` includes both share endpoints, unlike an interior first-order equation. This documented variant also admits zero capital and uses positive shocks with the joint law above. The repository's `applications/portfolio-choice/declaration/stages/port/port.bl` declares the joint law as one lognormal declaration with correlation ρ_ζ and continues to `m_next`, as here. A no-risky-asset variant fixes the share to zero and removes its policy and unused return-shock declarations; it still uses the same nonnegative-capital and positive-resource boundaries.

## 2 Connectors

A **connector** selects eligible continuation and arrival state fields for a stage join. In the main period, the outgoing field is written first and the incoming field second:

```yaml
connectors:
  - {k_next: k}
```

The declared boundaries explain which connections are within the period and which are left for its successor. A stage's local field name does not identify a field in another stage:

| Join | Domains and units | Where it is specified |
|---|---|---|
| `cons.a` to `disc.a` | Nonnegative assets in the same units. | Unique compatible same-name selection within the period. |
| `disc.k_next` to `port.k` | Nonnegative assets in the same units. | `{k_next: k}` within the period. |
| `port.m_next` to the next `cons.m` | Strictly positive resources in the same units. | `{m_next: m}` between periods. |

The stage declarations establish direction. Reversing the pair is not another spelling of the same join. The second authored pair belongs in the [inter-period connector](07-trellis.md#2-inter-period-connectors), not alongside the first: placing both in this period would close a cycle.

The pair performs no calculation. Interest, income, depreciation, discounting, and unit conversion must appear in a stage equation. Equal domain labels alone do not establish compatibility: the fields must denote compatible quantities with matching economic roles and information at the join. Their continuation and arrival tags refer to different stages, but describe the same boundary information after identification. [Perch tagging rules](appendices/13-perch-tagging-rules.md) explains why tags within a stage do not by themselves identify quantities across stages.

Declared sets are **compatible** when the set of the outgoing field is contained in the set of the incoming field, so that every value the preceding stage can write is one the receiving stage accepts. The two sets need not be equal: a declared set states where a field's values may lie and does not claim that every member is reached. A field on `ℝ₊₊` can therefore be copied into one on `ℝ₊`, and the reverse is marked incompatible, because `ℝ₊` contains zero. Two sets written alike in one period are one set. Otherwise, where a bound names a parameter, the sets are compared at the parameters' values, and the connection is not established until a calibration supplies them.

For a field with [category codes](01-stage.md#22-category-codes), a connection checks both the admissible integers and their recorded meanings. Every code the preceding stage can write must be accepted by the receiving stage with the same meaning. This applies to authored pairs, inferred pairs and connections between periods, and to each coordinate of a product. A domain with category meanings is incompatible with an ordinary integer domain that records none.

For example, two stages using the identifier `household_status` with `newborn=0, old=1` can copy their status fields. If the receiving stage instead declares `newborn=1, old=0`, copying 0 would change its meaning, so the connection is marked incompatible. A stage equation such as `n_next = 1 - n` can express the required conversion into that reversed coding; a connector performs no conversion, and the package does not prove that an arbitrary transition preserves category meanings. The identifier and its scope are described in [Symbol conventions §9.2.2](reference/symbols-conventions.md#922-category-codes).

A restriction of a coded set retains the meanings of its admitted codes. For example, `Old := {j : HouseholdStatus | j = 1}` admits only old households under the preceding coding. A field on `Old` can be copied into one on `HouseholdStatus`, but the reverse is marked incompatible because `HouseholdStatus` also admits newborn households.

> [!note]- Technical details
> Literal conditions such as `j >= 1` or `j = 1` determine which codes a restriction admits. If another condition, such as one naming a parameter, leaves its members undetermined, a connection whose answer depends on those members is not established. This includes a connection into that restriction, and a connection out of it into a set with disagreeing meanings, since the restriction may be empty. Within one period the same restriction on both sides is one set when its conditions use numbers and parameters; a condition that calls a function leaves even that connection unestablished.

For [indexed collections](01-stage.md#21-indexed-data), a connection requires matching keys in the same order as well as compatible entry domains. Thus collections on `{0, θ} ⊂ ℤ` and `{θ, 0} ⊂ ℤ` cannot be copied directly, even at the same value of `θ`. A stage equation must express any reordering of their entries.

An authored connector selects one eligible continuation use and one eligible arrival use. Write `{k_next: k}` when each endpoint name is unique on its side of the period; if either name occurs at more than one eligible stage, prefix that endpoint with its stage key, as in `{disc.k_next: port.k}`. The prefix is an address, not a change to the stage's equation. Authored pairs are considered before automatic same-name inference and claim their endpoints. Automatic inference selects only a uniquely compatible, globally consistent pair; an unresolved candidate is not a connection. The package checks declared sets, while the author must establish economic meaning, units and information. Reused value names inside different stages remain local; they are not an instruction to identify all value fields in the period. On branches, preserve the branch-specific field names and route each declared continuation to the intended successor. The [retirement stage](05-branching.md#1-work-or-retire), for example, distinguishes `a_w` from `a_r`.

Selecting field pairs does not yet establish a complete stage connection. A **route** is the selected pairing of one complete ordered continuation state with one complete ordered arrival state. The package checks every coordinate, the declared treatment of branches and any required joint law, and the value and derivative components passed backwards. Separate marginal laws do not establish an unspecified joint law. A coordinate exchange reorders the supplied derivative components; it neither differentiates an equation nor changes the stage order.

The [connection report](API/factory/trellis-factory.md) distinguishes selected pairs from certified routes and records the parameter bindings used in their checks. A route is certified only when its required conditions are established. An incomplete route, an incompatible component or a condition left undecided remains visible with its reason; none is confirmation of a complete connection. In Workbench, an unresolved authored entry remains in the source with its diagnostic while the model is being edited.

## 3 Stage order

The **stage-dependency graph** records which stage supplies fields needed by another. Its directed edges follow the economic direction from continuation to arrival. For the example in §1, consumption precedes discounting and investment in forward time; computing value works backwards through investment, discounting, and consumption.

The list `[cons, disc, port]` does not define this order. Reordering it leaves the intended connections unchanged. Where independent branches exist, several stages can be ready for computation at once. A within-period cycle has no such backward order and must be rejected for this construction. Boundary fields are those not supplied or consumed by a within-period connection; inter-period joins are described on the next page.

There are three different objects to keep separate:

| Object | What it represents |
|---|---|
| A stage's [semgraph](../wiki/semgraph.md) | The typed equations and dependencies within one stage, held in four graphs, each a DisCoPy Hypergraph: two initial diagrams on the fields, and two builders graphs, the backward one on value functions and the forward one on distributions. |
| The stage-dependency graph | Connections between stage occurrences, used to obtain a permissible computation order. |
| The [syntactic trellis](../wiki/trellis.md) | The model as written: the methods, settings, and calibration of each stage occurrence, by period index and stage key, held as data. |

The first represents the model's mathematical equations, the second its between-stage dependencies, and the third its numerical and parameter assignments. A graph showing an order does not establish that the value functions are measurable, expectations finite, or optima attained; those assumptions remain as in [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md).

### 3.1 Choosing the period boundary

For the main period, let $v$ be next period's value of positive resources and let $P_v(k)=\max_{s\in[0,1]}E[v(M(k,s,\Psi,\theta))]$ be investment value. The resulting consumption problem is

$$
C_v(m)=\max_{0<c\leq m}\{u(c)+\beta P_v(m-c)\}.
$$

Consumption and the share decision precede the next shock draw. The income realization that produced initial resources is already observed at this period's arrival. In addition to §1.2's conditions, require $P_v$ to be finite and continuous on compact capital intervals so that the consumption attainment argument applies. Concavity supplies the additional uniqueness and first-order characterizations when those are used.

Alternatively, begin the period before investment and end after consumption and discounting. Save this period template separately as `period.investment-first.yml`, a variant beside the first ([Trellises](07-trellis.md) §5):

```yaml
!period
name: investment_consumption
stages:
  - port
  - cons
  - disc
connectors:
  - {m_next: m}
```

Now `port.m_next` joins `cons.m` within the period, while `disc.k_next` joins the next period's `port.k` through `{k_next: k}`. The period's arrival and continuation states are nonnegative capital. Its share decision precedes the shocks, but consumption observes the realized resources. Given next-period capital value $J:[0,\infty)\to\mathbb R$, the period problem is

$$
I_J(k)=\max_{s\in[0,1]}E\!\left[
\max_{0<c\leq M(k,s,\Psi,\theta)}
\{u(c)+\beta J(M(k,s,\Psi,\theta)-c)\}
\right].
$$

Require $J$ to be finite and continuous on compact capital intervals. Define $q_J(m)=\max_{0<c\leq m}\{u(c)+\beta J(m-c)\}$ and impose §1.2's portfolio integration, continuity, and measurable-selection conditions with continuation $v=q_J$. These assumptions concern the composed functions and do not follow from matching domains.

Both period definitions discount once. They have different arrival information, state domains, and terminal-value interpretations; their finite-horizon value operators are not equal. Changing the stage list alone cannot change the economic order. The changed within-period connector and inter-period boundary make this second definition different. Exchanging expectation and consumption maximization would change what consumption observes. [Trellises](07-trellis.md) states the terminal domains for each definition.

## 4 Constructing a period

A period is a dictionary of records: `{"stages": {key: record}, "connectors": [...]}`, with one record for each stage occurrence. A record holds the stage source, its text and origin, and the three specification mappings the occurrence is bound with; `bellman.stage.load_stage` reads a stage file into a record whose three mappings are empty:

```python
from bellman.stage import load_stage

record = load_stage("cons.bl")
# {"stage": {"text": ..., "origin": "cons.bl"}, "calibration": {}, "settings": {},
#  "methods": [], "provenance": {...}}
```

The application completes the three mappings and places the period in a trellis, since no call elaborates a period on its own. Either it appends the period with `bellman.trellis.accrete(trellis, period, inter_connector=None)`, the terminal period first and each earlier period after it with the mapping that joins them, starting from `{"periods": [], "inter_connectors": []}`; or it writes the period into the `periods` list of a trellis dictionary, `{"periods": [period], "inter_connectors": []}`. [Elaboration](07-trellis.md#6-a-trellis-built-in-python) then constructs each distinct stage text once and returns the same dictionary with a constructed stage occurrence at each key, deriving the joins of the period from the fields as §3 describes, and the three trellis verbs, `bellman.trellis.calibrate_trellis`, `bellman.trellis.methodize_trellis` and `bellman.trellis.configure_trellis`, each given the elaborated trellis and the dictionary of records it came from, bind the three mappings in that order. The four stopping points, the symbolic trellis and the trellis after each verb, are the results of those four calls. A period may equally be built from stages already elaborated and bound one by one, `bellman.stage.elaborate_stage(bellman.stage.load_stage(path))` followed by the stage's own `calibrate`, `methodize` and `configure`, and appended by `accrete`; a trellis verb later copies such a stage occurrence as it stands. The period is a dictionary of records before elaboration and a dictionary of constructed occurrences after it; nothing before the elaborator parses or rewrites a stage file.

The records of every period of a model are written at once by `bellman.trellis.load_trellis(file)`, from a trellis file whose periods write their stages as records, or by `bellman.trellis.load_recipe(directory, recipe)`, from a registry and its recipe; [The Bellman factory](08-bellman-factory.md) is the route through those calls, and [Period functions](API/factory/period-factory.md) states `accrete`.

> [!warning] Elaboration takes a trellis, not a period
> `bellman.trellis.elaborate_trellis` refuses a bare period. Place the period in a
> trellis, by `accrete` or as `{"periods": [period], "inter_connectors": []}`,
> and elaborate the trellis, as the trellis page shows. No stage-dependency
> graph is stored: the joins of a period and the order of its stages are
> derived from the selected connections. Construction records a cycle as a
> diagnostic; requesting a stage order for that cycle raises an error. Read
> the [connection report](API/factory/trellis-factory.md#9-inspect-the-selected-connections)
> to inspect unresolved or incompatible connections.

None of these calls solves the model.

## 5 Independent stage occurrences

Two uses of `cons.bl` may share source text, but each constructed stage occurrence is a separate object with its own graphs and its own specification, and the two share no object. What the stages of one period do share is the parameters they declare under one name: `β` declared in two stages of a period is one parameter of the period, whose declared sets must agree and which the period's calibration sources supply once, each declaring stage then binding that value ([The trellis factory](API/factory/trellis-factory.md) §4). A calibration change in one period does not alter another, since the same spelling in another period is another parameter, and no stage occurrence is adjusted in place. Reusing a stage file or caching its parse therefore does not justify sharing mutable stage annotations.

If a stage file occurs twice inside one period, give the two uses distinct keys and supply a source entry for each. Distinct keys identify the occurrences; their field interfaces must still make every join unambiguous. Across periods, the same local key may recur because the period index distinguishes its uses. The application evaluates a parameter schedule for each index when assembling that occurrence's record.
