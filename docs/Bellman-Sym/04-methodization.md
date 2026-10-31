---
audience: user
type: user-guide
---
# Methodization

#specification #spec_factory

> [!summary]
> **Methodization** attaches a numerical method to an authored computation in a stage. A method type states where the method may stand and which numerical options it reads. We write one `on:` target per entry in a methods YAML file, then supply numerical settings and economic parameter values separately. Choosing a method adds no equation to the stage file and does not turn candidate controls into an optimal policy. A methods line may name a **method block**, a block written in a file of its own, whose lines, elaborated with the stage's declarations in scope, become the operations of the builder the line names and satisfy the stage file's declared line only under the condition the stage records (§4.1).

> [!info]- Relationship with other documents
> **Builds on** — [Stages](01-stage.md) and [Field equations](03-field-equations.md): typed blocks and their equations.
> **Used by** — [Periods](06-period.md) and [The Bellman factory](08-bellman-factory.md): attaching choices to each use of a stage.
> **Formal account** — [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md): analytic assumptions; [Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md): computation boundaries and candidate coordinates.

## 1 A consumption method

The complete `cons.bl` in [Field equations](03-field-equations.md#1-consumption-and-savings) chooses consumption by maximizing current utility plus continuation value over `0 < c ≤ m_d`. A numerical method must solve that declared constrained problem, including the zero-savings boundary.

Save the following recognition-only mapping as `methodization.yml`:

```yaml
methods:
  - on: argmax
```

The address `argmax` identifies the stage's maximization occurrence without adding `!node`. This entry records the target but attaches no numerical algorithm. Solving requires a registered routine that accepts this constrained objective and its domain; the example does not invent a handler or assert that target recognition supplies one. Settings would then provide the numerical options required by that routine.

### 1.1 An interior method

The separate `cons_interior.bl` in [Field equations](03-field-equations.md#3-an-implicit-policy-relation) replaces the constrained maximization with an interior candidate relation and adds the derivative line of the decision value. Read the following fragment inside that complete replacement context, which declares the budget transition, domains, utility functions, and continuation values:

```bl
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])      :: [id=InvEuler]
    m_d[>] = a + c[>]                 :: [id=endoggrid]
    c      = c[>]                     :: [id=cons_choice]
}
```

For this interior variant, save the following mapping as `cons_interior_methods.yml`. It attaches the endogenous grid method, [`!egm`](reference/methods.md#egm), which calculates candidate consumption at given savings and recovers its cash-on-hand coordinate:

```yaml
methods:
  - on: policy
    method: !egm
```

Here `policy` is the interior block's chosen identifier. The equations supply the inverse marginal utility calculation and the implicit condition for consumption. The `!egm` tag selects a numerical technique for these equations; it supplies no missing condition. Renaming the block requires changing `on:` to its new address, but leaves the mathematics unchanged. This attachment belongs to `cons_interior.bl`; the constrained `cons.bl` writes neither these candidate lines nor the derivative line.

## 2 Computations and addresses

A **block** is the authored header and body that define a transition, value calculation, or policy relation. A **builder** is the operator constructed from that block. A statement marked `!node` requests a separately addressable computation within the block. The distinction matters when choosing where to attach a method:

| Object | What it identifies |
|---|---|
| Authored block | The header and body written in the stage file, such as the block `policy` above. |
| Constructed builder | The operator constructed from the block. Its wires, the inputs it reads and the outputs it writes, carry functions or measures, not the fields listed in the block header. |
| Declared function | A named function declared outside the blocks, such as utility `𝑢`. It is not a field. |
| Authored `!node` statement | A computation boundary explicitly requested inside a block. The statement's result becomes a function in its own right, which later statements consume and a method can represent; without the mark the same expression is a subexpression of the statement that uses it, and no method can attach to it. |
| Nested mathematical operation | An expectation, derivative, maximization, or other operation inside an equation; nesting alone does not author another `!node`. Its result is a function of the remaining arguments, obtained exactly through its definition; only the operation's own methods attach to it (a quadrature rule to `E`, a maximizer to `argmax`, a root finder to `solve`), never a representation. |
| Alias address | The identity of an explicit intermediate equation, retained for inspection even when substitution removes an intermediate calculation. |
| Numerical representation | A grid, interpolant, quadrature rule, or other object a selected method uses to approximate the mathematical calculation. |

A declared function or an evaluated field is treated through its exact definition unless a method attached to it supplies a numerical representation. A builder output and the left side of a `!node` statement are evaluated fields; a declared function such as utility is not a field. The stage file itself never states a representation: the methods file alone chooses one. An interpolation method attached to either kind of function means that the method stores values on the named grid and uses an interpolant to represent the function between them. This is mathematics supplied by the method and does not change the exact [Evaluation](reference/operations.md#evaluation), which remains the identity into the declared set of functions. The `!node` mark determines whether a line's left-side field is evaluated; the attachment determines the representation used for its function.

Which methods a target admits follows from what the target is. #functional-semantics

| Target | Admits | Does not admit |
|---|---|---|
| a declared function | an admitted representation or function method | treatment as a field |
| an evaluated field: a builder output or the left side of a `!node` statement | a representation: an interpolant or a table on the grid the settings name | treatment as a declared function |
| an operator occurrence inside an unmarked statement (`E`, `argmax`, `solve`) | the operation's own method: quadrature, a maximizer, a root finder | a representation, since the occurrence's result is not an authored object |
| a builder | a [handler](../wiki/handler.md) for the builder as a whole; [`!vfi`](reference/methods.md#vfi) stands on the backward decision builder alone, which it realizes with its maximization; with `block:`, a method block on the policy builder, under `!egm`, or a marginal block, whose derivative lines state the derivatives of the value a backward value builder writes, under [`!marginals`](reference/methods.md#marginals) (§4.1) | |
| a derivative line of a value builder, named by the builder and the line, `cntn_to_dcsn.envelope` | a representation of the stated derivative, bound at the value builder's Evaluation beside the representation of the value (§4.1) | treatment as a field: the derivative is a property of the value |
| the Evaluation of a policy block that writes the grid line (the cash on hand at each saving, `m_d[>] = a + c[>]`), named by the block id | `!egm`, which stores the policy from the pairs the block's lines give at the savings | a policy block that writes no grid line |
| the [Argmax](reference/operations.md#argmax) row of an operative `argmax` line, one the block computes with rather than marks `!doc` ([Constraints](10-constraints.md) §3), that carries its first-order condition as a property (a line whose id is dotted, `optimality.euler`) | `!egm`, which inverts the property for the candidate, or a root finder | |

An author who wants an occurrence's result represented, the expectation of a continuation value held as an interpolant for instance, writes the expectation on its own line and marks the line `!node`; the result is then an authored function and admits a representation. The converse does not hold: attaching a method to an occurrence, a quadrature rule to an expectation, does not make the occurrence a `!node` or a separately addressable computation. A methods line without `block:` names a computation that the stage file created and creates none. A line with `block:` names a method block, whose lines, elaborated with the stage's declarations in scope, become the method rows of the builder the line names, in the builders graph, and satisfy the declared line only under the condition the stage records (§4.1).

Method attachment resolves an address against a supported computation in the constructed stage. An identifier used for inspection is not by itself evidence that a numerical method can attach there. An unmarked explicit alias can be substituted only with every declared output and free or bound dependency preserved. An implicit equation remains a relation and is not an alias to substitute away.

For example, a `policy.InvEuler` address identifies the inverse-Euler statement in §1.1. Its identifier alone does not request a separate computation boundary. If that calculation must be separately methodized, author and type the required boundary and use a method supported for it. [Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md) explains this distinction.

Supported implicit equations and operator occurrences can receive methods without an added `!node`. The following addresses identify different scopes:

| Address | Target |
|---|---|
| `policy` | The authored policy block. With `!egm`, the Evaluation that closes the block, where the block writes the grid line. |
| `policy.cons_choice` | The consumption example's authored implicit equation. |
| `argmax` | Every `argmax` occurrence in this stage. |
| `policy.choice.argmax` | The `argmax` in the retirement example's statement `choice` within block `policy`. |

An occurrence-specific attachment overrides the stage-wide attachment for that occurrence. Naming an operator this way does not turn its containing statement into an authored node. A `!node` statement needs its own identifier to be a method target; its automatically assigned positional address is insufficient.

The block-level `!egm` form requires the grid line, a line whose left side is a decision coordinate under the continuation mark; a policy block that writes no grid line is refused with the requirement named, and a first-order condition written as an operation takes a root finder instead.

Neither a block called `policy` nor a method called `!egm` creates automatic `evaluate` or `upper_env` targets. A stage with discrete choices likewise needs its authored branch-selection equations; see [Branching](05-branching.md).

## 3 Method places and options

The expectation of the buffer-stock application, `applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl`, integrates the shocks $\psi$ and $\xi$. The method type of [`!gauss-hermite`](reference/methods.md#gauss-hermite) admits an expectation operator and gives `n_nodes` the type "one positive integer per shock". Its methods entry therefore lists the two node-count settings in the order $\psi$, $\xi$. These are the two parts of every public method type: `admits` and `options`.

The admitted place depends on what the method does. A quadrature or maximization method computes a primitive operator and stands on that operator. A representation method stores a declared function or an evaluated field and stands at that function's definition or at the field's closing Evaluation. The third placement class is a handler for a whole builder, which stands on the builder. A declared function such as utility is not a field, and a function the stage file does not name has no address at which a method can stand.

An option has a name and a value type. Common types include positive integers, real numbers, positive real numbers, ordered pairs and seeds. `orders` and `bounds` are records keyed by the actual coordinates being gridded. The keys must name coordinates of the function, but the method may grid only a subset: a [`!Linear`](reference/methods.md#linear) representation of a function of $(m,z_d)$ may, for example, grid $m$ separately for each income state $z_d$. An order must be positive, and each bound must be an ordered pair inside its coordinate's declared set. `n_nodes` has one positive-integer entry per shock, in shock order. Methodization checks that required option names are present. Configuration checks the supplied values and joint conditions. An option unknown to the method is refused unless the entry names a handler that owns the option; such a handler-specific option is retained as untyped rather than treated as part of the method's contract.

Methodization adds no convergence or existence requirement. Defining equations, declared sets and authored constraints remain part of the exact stage, and ordinary type and calibration-definedness checks remain in force.

The listing `method_types`, which `bellman.stage` exports, gives the registered method types by their written tags, and [Method types](reference/methods.md) prints them in one table with the places each admits and its options. A stage's `places()` query lists the addresses to which methods may attach and the kind of each place. These are inspection queries: they neither attach a method nor execute one.

## 4 Writing the methodization file

Every entry requires one `on:` address. A method tag is optional: an entry containing only `on` records recognition without attaching a numerical method, and a handler may be given when the operator family determines the method. Separate targets require separate entries. Do not put a comma-separated list in `on:` or write a nested `schemes:` list.

The available entry fields are:

| Field | Meaning |
|---|---|
| `on` | One supported computation address in the stage. |
| `method` | Optional YAML tag naming the numerical technique, such as `!egm`. |
| `grid` | Optional grid on which a representation stores its values, for a method whose type admits the option, such as `!Linear`, or for a named handler that reads it. |
| `settings` | Optional mapping of method options to values or references. Referenced setting values are supplied during configuration. |
| `handler` | Optional identifier of the registered numerical routine used to carry out the computation. |
| `block` | Optional path of a block file, written from the folder of the methods file, whose block the method binds on the builder that `on` names; only a method whose type takes a block admits it, such as `!egm` or `!marginals` (§4.1). |

Option names depend on the chosen method. Use the method's documented contract; changing a tag does not establish that another method accepts the same options or solves the same relation.

A **handler** is a numerical routine, or an adapter calling one, registered for the requested computation. One handler may carry out an entire builder, including internal interpolation or maximization. Alternatively, supported authored boundaries may have separate handlers. The handler's documented capabilities determine which choices it honors. Merely recording an option does not show that a routine uses it, or that two routines agree to a chosen tolerance.

A handler evaluates only the equations of the stage file. A builder's `kernels()` answers them as one record that refers to no stage. A **kernel** is the mathematical data an operation uses: a law of motion, a value aggregator, a shock distribution, a correspondence or a policy reference. The record lists each operation of the builder in the order of application, with the plain Python function its kernel compiles to, or its printed relation where its rule is no explicit function, the names of the function's arguments and outputs, and the parameters with the values the calibration binds ([A builder](API/stage/04-builder.md) §5). A handler builds its numerical operator from such records and from the grids it reads from the settings, and the operator reads no stage. The endogenous-grid handler of the portfolio–consumption application, `cons-port:egm`, is one call of `egm` in asva, the numerical toolkit beside the package, `asva.egm(stage.dcsn.builder.policy.kernels(), stage.dcsn.builder.bwd.kernels(), savings, evaluation)`, with the savings grid and the evaluation grid read from the settings. Each function is made from the source text its kernel holds under `python`, which reaches array functions through the name `np` alone; a handler written for another array package executes the same text and then binds `np`, in the namespace of the function, to that package.

> [!note]- Technical details
> Read tagged methods YAML through `bellman.stage.sources.load_methods`, which preserves method tags and handles YAML's treatment of the key `on`. Ordinary YAML loading is not a substitute for that loader. Loading a method tag records a choice; it does not verify the numerical algorithm or prove that its assumptions hold.

### 4.1 A method block and a marginal block

A stage file may state the policy by its maximization alone, as `cons.bl` of §1 does, and leave the computation to a **method block**: a block written in a file of its own, the **block file**, whose header carries the signature of a builder of the stage and whose lines compute that builder's output. A methods line names the block file under `block:`, by a path from the methods file's own folder, and the builder under `on:`. The methods file of the consumption stage of the portfolio–consumption application, `applications/cons-port/declaration/methods/cons.yml`, holds these three entries:

```yaml
methods:
  - on: policy
    method: !egm
    block: cons_egm.bl
    handler: cons-port:egm
  - on: cntn_to_dcsn
    method: !marginals
    block: cons_egm.bl
  - on: cntn_to_dcsn.envelope
    method: !Cartesian
    settings: {orders: {m: n_m}, bounds: {m: [m_min, m_max]}}
```

The block file `cons_egm.bl` beside it opens with the stage's mark, defines marginal utility and its inverse in closed form, and holds one block of each kind; the stage's decision state is `m`, its continuation state `a`:

```bl
@stage: cons
𝑑𝑢(c : ℝ₊₊) := c^(-ρ)
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)

[id=egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]
    m[>] = a + c[>]                        :: [id=grid]
    c    = c[>]                            :: [id=identification]
}

[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {
    D_{m}V = 𝑑𝑢(c)                         :: [id=envelope]
}
```

The first entry binds `!egm` on the policy builder with the block `egm`, which writes the three lines of §1.1 with its candidate line as the inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0` ([Constraints](10-constraints.md) §4.3). Its header lists the value it reads and the control it writes, and nothing else; the derivative of the continuation value is read by the term, and the header lists nothing for it. `methodize` elaborates the block with the stage's declarations and the block file's own definitions in scope, and its lines become the policy builder's **method rows**, the operations of that builder in `stage.builder`. The initial diagrams keep the stage file's maximization, and so do the builders as the stage file states them, which `stage.declared` reads by the same keys as `stage.builder`. The stage records the condition under which the method rows reach the declared maximization, and `stage.obligations()` lists it under the name `egm-eligibility`; nothing checks it.

The block reads the derivative of the continuation value by the term `D_{a}V[>]` and declares nothing about how it is evaluated: the stage that built that value fixed it, and this block knows only that the value it reads is a function. The second entry binds `!marginals` on the decision value builder with the block file's **marginal block**, a block whose lines are **derivative lines**, each stating a derivative of the value the builder writes as the author asserts it: the envelope condition `D_{m}V = 𝑑𝑢(c)`, the derivative of the decision value in cash on hand. Its header is the builder's header restricted to what its line reads, the control `c` and the value `V`. `methodize` records the line at the builder's closing [Evaluation](reference/operations.md#evaluation), beside the representation method bound there, as a stated derivative of the value by coordinate, with the line's id and its source; the builder's signature is unchanged, no wire and no box is added, and the value's record lists the coordinate `m` under `derivatives`. The reading of the line as the derivative of the value rests on the envelope conditions; `stage.obligations()` lists it under `marginal-reading` and nothing checks it.

How the derivative of a value is evaluated is a property of the value, fixed here, in the methods file of the stage that writes it, in one of three ways: by the stated line, whose values a representation stores beside the value's; by the representation of the value itself, where its method's row says it evaluates the derivative ([Method types](reference/methods.md), the column **derivatives it evaluates**); or by a representation of the stated derivative of its own, bound on the derivative line's id, as the third entry binds `!Cartesian` on `cntn_to_dcsn.envelope`, so that the derivative is interpolated apart from the value. A later stage whose block reads `D_{a}V[>]` of this stage's value receives the derivative so fixed and declares nothing ([Trellises](07-trellis.md) §2.1). The demonstration's consumption stage declares no arrival perch: its decision value is the value the stage exports, and its decision state `m` is where the trellis joins the stage before it. A stage with an arrival builder whose law between the perches is the identity, `V[<] = V` or `V[<] = E_{y}V`, writes no derivative line on it, since the stored derivative values pass through the same map; where the pass-through crosses an expectation the package lists the condition that the derivative of the expectation is the expectation of the derivative, as `differentiation-under-the-integral`, and checks nothing. Where the law is not the identity, the author writes the arrival derivative line with the law's factor, as the buffer-stock model writes `D_{k}V[<] = E_{ψ,ξ}(R*(Γ*ψ)^(-ρ)*D_{m}V)`. Nothing is differentiated: the package computes no derivative that no line states and no representation evaluates. A stage file whose value builder writes the derivative line itself, as `cons_interior.bl` of §1.1 does, needs no marginal block. [Expression forms](reference/forms.md) §4 gives the two forms of a block file.

## 5 Loading and attaching choices

Stages are written in `.bl`; the three attachment files remain YAML:

| Source | Contents |
|---|---|
| `cons.bl` | Declarations, typed blocks, equations, and shock laws. |
| `methodization.yml` | Computation targets, method tags, and references to settings. |
| `settings.yml` | Values for numerical settings. |
| `calibration.yml` | Economic parameter values. |

For `cons.bl`, use the recognition-only `methodization.yml` in §1 and supply `settings.yml` as an empty mapping and `calibration.yml` with `ρ: 2`. The sequence is:

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("cons.bl"))
calibrated = stage.calibrate("calibration.yml")
methodized = calibrated.methodize("methodization.yml")
specified = methodized.configure("settings.yml")
```

Loading reads the file into a source record, and elaboration constructs the initial stage from it, with no methods, settings, or calibration attached. Each subsequent operation adds its binding to the stage it is called on and returns that stage, so `calibrated`, `methodized` and `specified` name one stage ([The binding verbs](API/stage/09-binding-verbs.md)). The recommended order shown above puts calibration first and configuration last. The package also accepts methodization followed by calibration and configuration, or methodization followed by configuration and calibration. It refuses configuration before methodization because the chosen methods determine which settings are needed. Calibration supplies parameter values without replacing the symbolic equations. These three accepted orders prepare the same specified stage; with recognition-only methods they supply no maximization algorithm and do not solve the model. For the interior example, substitute `cons_interior.bl` and `cons_interior_methods.yml`, with settings appropriate to that method.

Duplicate method targets, unknown method tags and unresolved targets are errors. A refusal names the entry and the stage's available places. Methodization also refuses a missing required option or an option the method does not admit, except for an untyped option owned by a named handler. Configuration requires a methodized stage, values for every required option reference and values satisfying the option types and joint conditions. Calibration requires every declared parameter and binds only declared parameter names. Extra supplied settings remain in the settings mapping, but do not become declarations.

The queries below inspect the three public parts of this process without executing a numerical routine:

```python
from bellman.stage import method_types

print(method_types["!Cartesian"])
print(calibrated.places())
print(specified.settings)
```

Each `method_types` entry displays its admitted places and typed options. `places()` lists the addresses and kinds available on this stage ([Methods and places](API/stage/07-methods.md)). `settings` lists each setting value and, for every method that reads it, the place under `read at` and the method under `by` ([Parameters and settings](API/stage/06-par-and-settings.md)). A setting that no method reads remains listed with no reader.

[The Bellman factory](08-bellman-factory.md) applies the same sequence to each stage occurrence of a trellis, meaning one stage file elaborated at one position of a period ([Periods](06-period.md#4-constructing-a-period)). Repeated stage occurrences have independent graphs and specifications; that independence does not imply that lifecycle operations can be applied in any order.

## 6 Candidate consumption and interpolation

In the separate interior example in §1.1, `c[>]` is candidate consumption indexed by savings, and `m_d[>]` is its associated cash on hand. The equation `c = c[>]`, interpreted through `a = m_d-c`, constrains the unknown consumption choice. It does not assert that every numerical root maximizes value.

For the displayed power utility, use strictly positive consumption and `ρ > 1`, for example `ρ = 2`; then inverse marginal utility is defined on strictly positive, finite continuation marginal values. Interior optimality uses the Euler condition and the relevant differentiability assumptions. The borrowing boundary needs its own declared feasible choice and optimality conditions. In particular, a constrained policy requires the Kuhn–Tucker condition in one of its three spellings, the clause `⟂ m_d - c >= 0` on the decision-perch first-order condition, using the forward law `a = m_d - c`, a multiplier declared in the policy block, or the clause `⟂ a >= 0` on the continuation-marked candidate line `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])` ([Constraints](10-constraints.md) §4), or a declared constrained branch, or a restriction of the implicit equality to the interior with the constrained branch declared separately. With the clause on the candidate line the corner belongs to the relation the file states. At zero saving the candidate takes every value up to the interior value, and the identification, the last line `c = c[>]` ([Field equations](03-field-equations.md) §3), gives consumption equal to cash on hand there; a method attached at the Evaluation therefore takes the corner's pairs, which the clause declares, beside the pairs of its grid ([Constraints](10-constraints.md) §4.3). A handler adding a boundary segment to a block that states none of these must report it as an extension outside the declared equality; see [Appendix C §4.5](appendices/14-appendix-c-syntax-to-semantics.md#45-an-implicit-statement-with-a-constrained-policy), which also states when the three spellings define one policy and when that policy is the maximizer. This modular consumption stage contains no discount factor: when composed with a separate discounting stage, the continuation value and its derivative already include that stage's discounting.

More generally, candidate coordinates and controls define a relation: a set of state–control pairs. They define one control on the candidate state domain exactly when candidates with equal coordinates have equal controls. A policy on the intended domain additionally needs coverage of that domain and appropriate measurability. If several controls occur at one state, a selection must be supplied. Comparing candidate values establishes the true optimum only if the candidate family includes the relevant feasible optima and a maximum is attained. [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R10 and R12 state these conditions.

A numerical method may interpolate candidate pairs internally. An explicitly authored `evaluate(knots, values, x)` is optional: it is a separate mathematical operation with declared inputs and its own approximation conditions. Naming an interpolation method does not insert that equation into the stage. Nor does internal upper-envelope selection, which compares candidate values at a common state, create a separately authored `upper_env` target.

A **numerical grid** is a finite collection of points for approximating a function on its declared domain. It does not replace that domain. A simulation grid may differ from the grid used to solve the model; the numerical routine must specify how its representations are related.
