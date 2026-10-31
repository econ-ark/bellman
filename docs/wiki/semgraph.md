---
slug: semgraph
title: semgraph
tags:
- bellman-calculus
- semantics
- semgraph
- discopy
- functional-semantics
description: The constructed semantic graph, with the two initial diagrams on fields and the two builders graphs on functions and on finite measures;
  builder, primitive, node and combined inspection; and the value bundles a box acts on.
sources:
- path: docs/bellman-calculus/03-Stages and perches.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/05-Operators and builders.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- path: packages/bellman/bellman/stage/semgraph.py
  class: working
  date: '2026-09-07'
- path: packages/bellman/bellman/native/records.py
  class: working
  date: '2026-09-07'
- path: packages/bellman/bellman/graphs/initial_diagrams.py
  class: working
  date: '2026-09-07'
- path: packages/bellman/bellman/stage/method_table.py
  class: working
  date: '2026-09-07'
- path: packages/bellman/bellman/stage/stage_answers.py
  class: working
  date: '2026-09-07'
- path: packages/bellman/bellman/stage/inventory.py
  class: working
  date: '2026-09-07'
- path: docs/Bellman-Sym/API/stage/02-initial.md
  class: canonical
  date: '2026-09-28'
- path: docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/03-field-equations.md
  class: canonical
  date: '2026-09-07'
merged_from:
- field_graph
- declaration_problem
authority_high_water_mark: canonical
needs_resolution: false
updated: '2026-09-07'
wiki_status: budding
last_reviewed: '2026-09-07'
flags: []
audience: user
type: concept
---

# semgraph

**semgraph** means **semantic graph**: the constructed mathematical
representation of the model. Use `semgraph` in current explanations. The
**parsed AST**, or abstract syntax tree, records the constructor structure
of the authored text; it is the input to construction, not the semgraph.
Existing API names and historical quotations keep their spellings.

This page is the terminology home for a semgraph's graphs, grains and wire
bundles. Using `semgraph` as the Python module name introduces no second
mathematical representation.

## The four graphs and what they represent

A [[stage]] holds four graphs, and each states which mathematical objects it
represents. The boxes are operations, the ports are their individual
input/output positions, and the **wires** connect compatible ports. A wire's type
states what kind of object it carries. The stage reaches them as
`stage.initial.backward` and `stage.initial.forward`, the two initial
diagrams, and `stage.builder.bwd` and `stage.builder.fwd`, the two builders
graphs. A [[builder]] is reached by the ordered pair of [[perch|perches]] it
joins, `stage.builder["cntn", "dcsn"]` for the decision builder, or from
the perch its edge leaves, the edge being the step from that perch to the
next, `stage.dcsn.builder.bwd`, a path defined as that one pair; the policy
builder is read by its own key, `policy`
([The builders graphs](../Bellman-Sym/API/stage/03-build.md) §2).

| Graph | Objects and operations |
|---|---|
| **Backward initial diagram** | The authored [blocks](../Bellman-Sym/01-stage.md#3-builder-blocks) that compute values and the policy, on the fields they read and write. |
| **Forward initial diagram** | The authored transition blocks, likewise. The two initial diagrams are separate graphs and are never drawn as one. |
| **Backward builders graph** | Operators receiving continuation-value functions and producing objective, decision-value or arrival-value functions, as specified by their definitions. |
| **Forward builders graph** | Operators receiving finite measures over states and producing the measures induced by transitions, conditional distributions and a supplied policy. |

A [[field]] is a named quantity at its perch, with a declared set. Once
shocks are declared, fields may be interpreted as random variables at the
corresponding information sets. Representing fields as functions requires
specified representing functions and sufficient state information. **Sufficient** means that
the state contains the information needed for the relevant payoff arguments
and conditional distributions. The required domains and integration conditions remain
explicit; a field equation does not supply them automatically.

### Fields, values, functions and builders

A [[field]] is a quantity defined over possible outcomes with an information context. Evaluating it at an outcome gives a value. Representing it by a function of a chosen state requires that state to retain the relevant information; measurability with respect to the full information set alone does not prove this. A [[backward_builder|backward builder]] acts on such functions, whereas a [[forward_builder|forward builder]] acts on measures describing state distributions; both are [[builder|builders]], the [[operator|operators]] the blocks of a [[stage|stage file]] denote.

For consumption, the authored reward and continuation equations together with `a = m_d - c` give the choice value `utility(c) + continuation(m_d-c)` under the required state representation; discounting follows the authored equations. Consumption remains a free choice until a policy is supplied or selected. Evaluating the choice value at a feasible policy gives its one-step value update for the supplied continuation. The optimizing value is the supremum over feasible choices where defined; representing it by a policy additionally requires attainment and a measurable maximizing selection.

These distinctions resolve a common ambiguity in compact Bellman notation: a field, its scalar value, its state-function representative and an operator on functions are different mathematical objects. A transition alone does not supply utility, discounting, expectations or a policy. Conditional distributions and integrability must be stated; a fixed independent [[operator#Kernels|shock probability distribution]] is a special assumption, not a consequence of diagram wiring.

### Representation and interpretation

This entry owns the account of the four graphs of a stage, their grains and their value bundles. The two initial diagrams are the backward and the forward graphs on fields; the two builders graphs act on functions, backward, and on measures, forward. Whole builders, [[operator|primitive operators]] and the [[sub_builder|sub-builders]] that authored nodes denote provide different inspection grains. Their boundaries need not nest, and arithmetic remains within the retained equation and function definitions.

The origins of a box and the analytic conditions of the stage are answers of queries, not parts of the native graph. A missing interpretation rule is reported while the initial diagrams remain inspectable; display text is not parsed again to recover meaning.

See [The initial diagrams](../Bellman-Sym/API/stage/02-initial.md), [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) and [[methodization]].

The backward initial diagram preserves the authored policy block separately.
A policy relation is not a selected function. In the decision [[builder|builder at a policy]], the policy reference is [[operator#Kernels|kernel]] data of the policy-indexed
[[operator#Kernels|law of motion]], [[aggregation|value aggregator]] or conditional distribution. The forward decision
builder is the push-forward through the policy-indexed transition
$g_{\succ,c}$, with any policy-dependent conditional distribution in its
kernel data. Exact Evaluation reads no policy. The insertion of the policy is
a factor of the pullback and of the push-forward at the policy, which their
cards write out, `𝑉≻(𝑔≻(m_d, 𝑐(m_d)))` and
`μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})`, and no stage of the applications forms a
separate `PolicyInsertion` row. The policy is typed once, on the policy builder's
output, and no wire joins that output to the policy-indexed builders; how the
backward builders and the policy builder are joined is stated at
[[methodization]]. The forward
builders graph uses transition and distribution definitions; it is not obtained by reversing every arrow
of a reward-bearing [[bellman_operator|Bellman operator]]. See [[backward_builder|backward builder]] and
[[forward_builder|forward builder]] for the respective mathematical operations.

## Grains expose defining operations

A **grain** chooses which boxes are opened within a graph.
It does not change that graph's mathematical objects. Elaboration constructs
the two initial diagrams and the builder grain of the two builders graphs.
Other grains are derived from those retained graphs when requested and kept
on that [[stage|stage version]]. A reader reaches the two finer public grains by an
attribute of a graph, a builder or a sub-builder, `primitives` and
`sub_builders`, as `stage.builder.bwd.primitives`; the combined and the
factored grains are answered by `semgraph.record`, below.

| Principal grain | What remains visible as a box |
|---|---|
| **Builder** | One complete builder operation, with its defining composition retained. |
| **Primitive** | Natural mathematical operations such as the pullback along the law of motion, whole scalar aggregation, conditional integration, probability transport, maximization and evaluation, where defined. |
| **Sub-builder** (`node` in code) | The [[sub_builder|sub-builders]], the operators the statements marked `!node` denote, closed, with their definitions and actual dependencies. Unmarked equations remain wherever the composition needs them. A sub-builder's output is a function wire of its own, which a method can represent exactly or by an admitted approximation. The result of an operator occurrence inside an unmarked line (an `E`, an `argmax`, or a `solve`) is a wire the construction makes, not an authored one: it is present in the builders graphs below the builder grain, absent from the initial diagrams, and admits only the operation's own method. Attaching that method does not make the occurrence a node; `!node` alone creates the authored boundary. |
| **Factored** | The boxes that respect both the primitive and sub-builder divisions together with the eligible local method targets. It opens a sub-builder around an operator to which a method may attach: an expectation, the maximization of an operative `argmax` line, or a row whose output is among its own unknowns. |

The complete transition **g** and scalar aggregator **G** are mathematical
definitions on their declared arguments. Each has one definition record
referring to its retained source equations, and every operation that uses
the definition references it by identity:
the pullback and the push-forward reference the forward
builder's g, the value aggregation references G. DisCoPy is the diagram
library used to store the boxes and wires of the graphs; the finest box of a graph is a primitive operator or a sub-builder. A box represents an occurrence and carries references to the definitions table: the transition, aggregator or distribution record, or the statement address. Its equation is printed from those references and its conditions are computed from that equation. Addition, subtraction and other arithmetic inside those equations are not boxes and do not become an additional grain. A `!node` inside g or G remains inspectable there.

The grains need not nest. Two coordinate equations may together define one
vector transition g; one named utility equation may define only part of G.
Opening a sub-builder inside g cannot replace an outer operator on functions with a scalar box of another type.

The additional **combined grain** starts at all declared builder outputs
and traces their actual dependencies backward. On reaching a primitive operator or sub-builder, it keeps that box closed and continues along
all its external input wires. It stops opening the box, not following its
dependencies. Shared occurrences are visited once, and every output of a
multi-output box is preserved. A sub-builder containing an expectation therefore remains closed until it is opened. An operation no declared output
depends on is not drawn at this grain. This is a stopping rule, not a
fifth graph or a claim that every decomposition has one finest grain.

## How a [[statement|value statement]] is folded

A [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks)'s [[statement|statements]] are folded by structural
recursion on their retained terms into primitive operators of three kinds
on function wires, in the order the term nests them: the pullback of
every continuation function along the block's law of motion, an expectation
for every occurrence `E_μ(·)`, and an [[aggregation]] for the arithmetic
that combines terms carrying a [[sub_builder|value input]]. The arithmetic inside an
occurrence's brackets is one aggregation before that expectation; the
arithmetic outside is one aggregation per maximal pointwise segment. The
fold never moves arithmetic across an expectation, so a statement that
writes the expectation inside the line denotes the aggregation after the
expectation, reading its result as a value input, and a statement that
writes the aggregation inside the expectation denotes the canonical form
with the aggregator inside the integral. Whether
an aggregation's map is affine in its value inputs is never a condition of
construction. A sub-term that carries no value input,
a named function of fields, a parameter, an expression in fields and
shocks, is part of the aggregation's map, never a box. The stored form of
every equation is the retained term; the printed string and the compiled
function are queries. A `!node` statement denotes a
[[sub_builder|sub-builder]], a cut of the builder's composition; a [[branch]] is a
[[branch|summand]] of the continuation coproduct, a bubble of the forward initial
diagram and no wire.

<!-- synth: class=canonical, source=docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md, date=2026-09-07 -->
## Opening a box preserves its operation

A **builder signature** declares a builder's [[signature|inputs and outputs]]. Opening any
box must preserve its exact ordered input and output identities and types,
and its operation on every admissible assignment of its free inputs. The
replacement must also preserve the conditions under which the formulas are
defined, local-variable scope, conditional distributions and shared dependencies.
Those conditions are often called **guards**. A **capture** is an input used
by a function definition besides its formal arguments.

Each operation has one authoritative definition. Its expansion is derived
from that definition; independently editable g/G definitions and expansions
cannot supply competing meanings. A named numerical method is not by itself
a proof that its output equals the defining operation. Native composition
checks connections and types, not integrability, optimality or numerical
convergence.
<!-- /synth -->

The inspected DisCoPy 1.2.2 installation provides native identity, sequential
composition (`>>`), tensor composition (`@`), and
`Diagram.substitute(i, inner)` for replacing a selected diagram box.
`Hypergraph` itself has no `substitute` method. Conversion with
`Hypergraph.from_diagram` must preserve the ordered inputs and outputs and
**incidence**, meaning which ports connect to which wires. The mathematical
definitions remain in native `Box.data`; a drawing frame is not their replacement.

## Source order and evaluation order

**Source order** is the order in which equations were authored. Queries
may retain it for inspecting the source. The order of boxes in a stored
Hypergraph is a separate representation detail; neither order necessarily
puts a producer before its consumers.

For an explicit acyclic computation, **topological order** puts each
producer before every operation using its result. Independent operations
may occupy the same layer, with source order breaking ties. If h supplies
both y and z, evaluation requires h before y and z even when stored boxes
list y, z, h. Backward traversal discovers this dependency; it does not mean
evaluating consumers before producers.

A cycle or implicit relation needs its own admitted interpretation. Drawing
arrows differently, sorting boxes, or inserting a formal trace does not
solve the economic problem or establish the existence of a fixed point. Equation addresses and method
targets remain unchanged when the presentation follows dependencies.

## Value bundles preserve their constituents

A **value bundle** is the tuple of value objects on one base: the maximal set
of **parallel wires** of a backward graph that share their base coordinates and
are written by one box and read by one box. Its components are the value
objects the stage declares at that perch, and a bundle may hold one component
only: the derivative of a value is no component, since it is read by the
derivative term `D_{a}V[>]` and adds no wire. Parallel means that the wires
coexist there, not that their values are independent, and grouping asserts no
independence. The relation between a value and its derivative is written by
the author on a derivative line, with the chain-rule factor where the law of
motion between the perches is not the identity.

The bundle is derived from the graph and stored nowhere; its type is the
tensor of its wires, read as one function into the product of its components'
result sets. One box acts on the whole bundle for one of two reasons. A
pullback and an expectation apply one kernel to every component — the same
law of motion, the same policy-indexed conditional distribution and the same
shocks under the same conditioning — and an aggregation applies one vector-valued
kernel, the pairing of the components' own maps, from the tuple of inputs to
the tuple of outputs. A component that a later operator reads alone is a wire
of the tensor carried on; no box unbundles it.

A **branch tuple** is not a bundle. A branching stage has a continuation state
space that is a disjoint union of the branches' state spaces, and functions on
a disjoint union are a tuple of functions, one per label, so a branch also
shows as several value wires side by side. The two differ in what is put side
by side: a bundle is indexed by the value fields the perch declares and its
components are functions on one state space, across which a kernel acts; a
branch tuple is indexed by labels and its components are functions on different
state spaces, across which the operator is a case analysis. A drawing shows a
bundle as one thick wire labeled with its components and a branch tuple as one
labeled wire per alternative meeting the aggregation of the selection line,
and never the other way round. The thick wire says what the graph does, not what a header declares: at a graph's own boundary the graph stands for the box on its own side and one box is still required on the other, so the input `V[>]` of `cons.bl`'s backward graph stands at the boundary, the decision builder and the policy builder each reading it, the policy builder by the derivative term `D_{a}V[>]`. In type notation the wire the arrival pullback of `cons.bl` writes is
`V∘g : m → ℝ`; the drawing writes the same wire in the calculus
spelling it uses for every other wire, `V(g(m))`.

A graph — an initial diagram or a builders graph — fixes the mathematical
objects, a grain selects which boxes are opened, and a bundle is read off the
wires those boxes write and read.

Native `A @ B` gives an ordered tensor of wire types. Grouping preserves
each constituent's identity, type, domain, scope and dependencies. Tracing
the grouped outputs together retains shared producers once. Reordering
requires explicit swaps. Unbundling recovers the original ordered wires.

Representing a bundle by one product wire is an additional structural
operation. It requires defined packing and unpacking maps whose expansion
recovers those same constituents. Tensor concatenation alone does not turn
two wires into one, and boxes merely named `pack` and `unpack` do not cancel
under native equality.

A value bundle also preserves its components' separate domains. For example,
bundling 1/x and x does not discard the latter's value at zero; forming one
paired partial function on a common domain is a separate operation.
Likewise, two separate coordinate distributions, or **marginal measures**,
do not determine a joint distribution. Preserve the
actual joint distribution and every coordinate needed by later conditional
distributions. Copying one realized shock is different from drawing independently
twice. Bundling may not conceal such dependencies or move a local variable
outside its binding scope.

### Outputs computed within one builder

Outputs of one authored builder can instead come from one joint local
computation on that builder's effective domain: the inputs for which all
its formulas are defined. With E denoting conditional
expectation, `V = E(W)`, `U = V^2` and an unused local equation `h = 1/U`
compute V once, then U, and restrict the builder to U ≠ 0. Both returned functions preserve that
restriction, even though h is not an output. Their arguments follow the
actual local dependencies and the checked declaration order; a control
needed only by a domain condition remains an argument. This construction
is distinct from placing independently defined functions on parallel
wires: it does not impose one common domain on arbitrary bundles.

<!-- synth: class=working, source=packages/bellman/bellman/stage/semgraph.py, date=2026-09-15 -->
## Public query

`bellman.stage.semgraph.record` is implemented for ordinary stages whose retained
equations, domains, laws of motion and distributions have an admitted interpretation. It accepts an
`ElaboratedStage`, the object `elaborate_stage` makes of a stage file. Import it
with `from bellman.stage import semgraph`, the module that defines it. The
operation returns the graph together
with its inputs, outputs, conditions and parameter information.

Its call signature is `semgraph.record(stage, *, level, direction,
grain="builder", assumptions=())`. For example:

```python
from bellman.stage import semgraph

record = semgraph.record(stage, level="builders", direction="backward", grain="primitive")
```

`level` selects `"initial"`, the initial diagrams, or `"builders"`, the
builders graphs; `direction` selects `"forward"` or `"backward"` and is
required. `grain` selects `"builder"`, `"sub-builder"` (the code token `"node"`), `"primitive"`, `"combined"` or `"factored"`. An unsupported interpretation
gives a diagnostic identifying the authored item and missing rule; the
constructed initial diagrams remain available. The record states the graph
and computes no solution.

The immutable `Semgraph` record describes the native graph and its inputs
and outputs. It adds no alternative graph language or second set of edges.

| Attribute | What it retains |
|---|---|
| `.graph` | The native DisCoPy Hypergraph that the selected direction's handle holds, `stage.builder.bwd.graph` or `stage.initial.forward.graph`, at the grain the attribute `primitives` or `sub_builders` selects, with its records in `Box.data`. |
| `.inputs`, `.outputs` | The [[sort]]s of the graph's ordered input and output wires: identity, kind, perch, role, domain and coordinates. |
| `.obligations` | The conditions of the stage with their scope and status (required, assumed or established), the caller's assumptions in place of those they discharge. |
| `.parameters` | The sorts of the [[parameters]] that the terms of the graph's rows name, directly or through the functions they call; empty for an initial diagram. |
| `.calibration` | Supplied parameter values, or `None` before [[calibration]]. |

The record holds no copy of the origins or the methods: the origins of a box
are its data, read with the box's `kernel().origins`, and the methods attached
inside a graph are read with that graph's `methods`.

An initial diagram includes any supplied functions still required through its
retained definitions after its declared field inputs. Model parameters
remain named inside those definitions, with their declarations and values
available separately. Function arguments remain distinct from model
parameters, captures and locally bound variables.
The graph of a record is frozen, and a transformation constructs a new
record. The ordered method inventory that a piece's `methods` reads retains
its target identities across changes of graph and grain. Its entries retain their original stage meaning: an
expectation's numerical integration method does not become a method for transporting
probability measures. An empty inventory means no effective choices are
attached; it does not by itself describe which setup steps ran.

The optional `assumptions` value is a tuple of `Condition` records
with status `"assumed"`, matching requirements of the requested interpretation.
An assumption cannot supply a missing policy or an unsupported structural
rule. Conditions on formula domains remain explicit.

Elaboration stores the two initial diagrams and the builder grain of each
builders graph, or a refusal where one cannot be constructed. A query derives
the requested grain from those retained objects and caches it for the stage
version. `ElaboratedStage` has seven attributes: `name`, `metadata`,
`definitions`, `initial`, `_builders`, `bindings` and `provenance`, the fifth the stored record of the two builders graphs, which `stage.builder` reads. The object is a [[stage|stage occurrence]], one stage file elaborated at one position of a [[period]], and it is not adjusted in place: a binding gives a new stage version, and a different text is elaborated again as its own stage occurrence. Definitions retain
source equations; queries derive their mathematical and display information.
<!-- /synth -->

A stage is a term over a many-sorted [[signature]] and each graph is its image under the unique homomorphism (Goguen, Thatcher, Wagner and Wright 1977, "Initial Algebra Semantics and Continuous Algebras", §2 pp. 70–71 and §3.2 p. 76; in categorical form, Jacobs 1999, *Categorical Logic and Type Theory*, §2.2 p. 129, Theorem 2.2.5). A semantics given by a fold is compositional (Hutton 2023, "Programming Language Semantics: It's Easy as 1,2,3", §3 p. 4; Winskel 1993, *The Formal Semantics of Programming Languages*, §5.2 p. 60), and two homomorphisms that agree on a generating set are equal (Burris and Sankappanavar 2012, *A Course in Universal Algebra*, the Millennium Edition, Chapter II §6 p. 47, Theorem 6.2), so what the term determines is a query rather than a stored member. A grain is one presentation of the object, not a second object (Scott and Strachey 1971, *Toward a Mathematical Semantics for Computer Languages*, §0 pp. 1 and 4–5), and the fold cata f = f ∘ F(cata f) ∘ in⁻¹ opens a bubble (Leal de Freitas 2020, *Recursion Schemes for Mathematicians*, pp. 15–16). A box holds the parameters of its form and nothing else (Backus 1978, "Can Programming Be Liberated from the von Neumann Style?", §11.2.6 p. 622 and §13.1 p. 631). The definitions table is an environment that the bindings extend, with no store at elaboration (Schmidt 1986, *Denotational Semantics: A Methodology for Language Development*, §4.1 p. 54, §2.3.1 pp. 25–26, §5.1 pp. 66–68, §8.3 p. 170 and §10.2 p. 202); the methods form a second algebra held apart from the term, as effect handlers are (Plotkin and Pretnar 2009, "Handlers of Algebraic Effects", §4.1 p. 7 and §5.1 p. 8); and elaboration produces the internal representation once (Pfenning 2021, *Lecture Notes on Elaboration*, §1 p. L11.1). The definitions are the economist's objects, the feasible correspondence, the value space and the aggregator of a recursive decision process (Sargent and Stachurski 2026, *Dynamic Programming*, vol. 2, §7.1.1.1, pp. 206–207), and every record class the schema keeps is a class each tool that reads the stage must know (Wang, Appel, Korn and Serra 1997, "The Zephyr Abstract Syntax Description Language", §4 p. 11).

<!-- synth: class=working, source=packages/bellman/bellman/stage/stage_answers.py, date=2026-09-07 -->
## Inspecting equations and complete maps

`stage.definitions` holds the retained source statements as records of
kind `line`, in authored order, including statements inside authored
nodes, and `stage.definitions.list()` prints every record grouped by kind.
The records of the lines retain the terms, conditions and addressed
unknowns. Complete g and G records refer to these statements by identity; a
printed preview does not replace them.

`stage.builder.bwd.primitives` and `stage.builder.fwd.primitives` read the
operations of the two builders graphs, one box per primitive operator, and
`stage.dcsn.builder.bwd.list()` lists the operations of one builder in the
order of application. `stage.definitions.denote("cons:g:dcsn_to_cntn")`
answers the complete law of motion of a forward block, and the records of
kind `G` the value aggregators of the backward blocks. A builder's inputs
and outputs are `stage.dcsn.builder.bwd.signature()`, and the inputs and
outputs of one graph are `stage.builder.bwd.signature()`, one record with two
parts, `inputs` and `outputs`.
<!-- /synth -->

<!-- synth: class=working, source=packages/bellman/bellman/stage/inventory.py, date=2026-09-07 -->
`denote()` is the one verb below the stage, and `view()` is the stage's
own: `stage.view()` prints the inventory of the occurrence, while
`stage.definitions.denote("<identity>")` for a definition and
`stage.dcsn.builder.bwd["pullback"].denote()` for a box each answer a
record whose printed form is that piece's card. A card carries the typed
inputs and outputs under `Signature`, the rule the piece applies, the
operations of a builder in the order of application, the conditions and, on
a methodized version, the method bound within the piece, and under a light
line the lines of the stage file it comes from ([[semantics]]).
`print(piece)` prints the same card. `kernel()` on a box
prints the pointwise map the operator applies. Kernel arguments are
pointwise values; the coordinates of a function on a wire describe where
that function is evaluated. The two lists need not coincide.

`compile_kernel()` on a box answers one plain Python function of a supported
kernel, on a symbolic version as on a calibrated one, taking the kernel's
arguments and then the values of the parameters it reads, which
`kernel().parameter_values` holds in that order; `kernel().python` is its
text. It is refused under the rule `kernel-target` for a box whose
kernel is neither a law of motion nor a value aggregator, as an expectation's
or an evaluation's is, and for a row whose rule has no side that is an
explicit function of its inputs, as the identification of a policy block has
none; it chooses no policy and solves no Bellman equation. Printing and these
queries read the retained terms, without parsing source previews again.
<!-- /synth -->

## Names and parameters in diagrams

Every wire of the backward builders graph carries a function or a set of
functions. The set-valued case is the result of an [`Argmax`](../Bellman-Sym/reference/operations.md#argmax) row or of a row
whose output is among its own unknowns; exact Evaluation preserves that set and
selects no member. Function-valued
wires include
a value function such as `V[>](·)`, its composition with the transition
`V[>](g(·))`, an expectation's result, an objective function of state and
control `V(·, ·)`, the declared
policy of a maximization `π(·)`, the functions the policy lines define on the
continuation states (`c[>](·)`, `m_d[>](·)`) and a policy function `c(·)`.
States, controls and shocks are coordinates of the functions on backward wires, not separate wires. A kernel's arguments are the pointwise values used to define those functions, and the aggregation's results are the
functions themselves. An **evaluation** operation (`Evaluation`) is the
identity from a derived carrier into a declared carrier. Its object may be a
function or a set of feasible policies, and it makes no selection. It reads
no policy and inserts none. A numerical method may store an interpolant as
its representation of a function without changing exact Evaluation. In a
builder at a policy, the policy instead indexes the pullback, aggregation or
conditional distribution in which it occurs.

**Pullback of the function along the law of motion g** composes a supplied function with g, V ↦ V∘g; its forward partner is the **push-forward through the law of motion g**, μ ↦ g_#μ. **Value
aggregation G** applies the complete value calculations defined by G and
yields the value functions or, when a control is bound, the objective functions, using the pulled-back function or an expectation's result as its input (see [[aggregation]]). The policy builder uses the same kinds: its objective or residual is aggregated on the decision coordinates after the pullback along g. On the continuation grid, the inverse-Euler candidate line `c[>]` forms one `Aggregation` whose rule is the line's relation, an inequality or a complementarity included, and the coordinate line `m_d[>]` another, each reading the derivative of the continuation value at the saving by the term `D_{a}V[>]`, with the author's derivative lines and inverse marginal utility and no automatic differentiation. Where the candidate line carries the clause `⟂ a >= 0`, as in `cons.bl`, the candidate at each saving is a set: the interior value alone where the saving is positive, and every value up to it at zero saving. The candidate and the coordinate are then correspondences, printed `𝑐≻ : Xa ⇉ ℝ₊₊` and `𝑚_d≻ : Xa ⇉ Xm`. The identification line `c = c[>]` forms the `Pullback` of the policy along the coordinate map `m_d[>]`, equated to the candidate; its rule holds at every value admitted at each saving, the corner, consumption equal to cash on hand, among them ([Constraints](../Bellman-Sym/10-constraints.md) §4.3). The grid line is checked against the law of motion solved for the decision coordinate, and a line that disagrees is refused under the rule `grid-line-consistency`. An operative `argmax` line forms an `Argmax` row, whose output is the set of maximizing policies; and a `solve` line forms one `Aggregation` of its residuals. Expectation
remains a separate operation. The kinds of the rows are `Pullback`, `Aggregation`, `Expectation`, `Evaluation` and `Argmax` ([operations](../Bellman-Sym/reference/operations.md)): a relation is the rule of a row whose output is among its own unknowns, and no kind of its own. A line attached to an operative line by a dotted id, as the first-order condition `optimality.euler` is attached to the argmax line `optimality`, is that row's property: it forms no row, no address and no method place, and it prints under the row.

Parameters belong with definitions and calibration. They are held fixed
when the functions act on states, controls or supplied functions, and are
not drawn as separate semgraph wires. Their identities, domains and any
supplied values remain inspectable. An uncalibrated parameter remains a
symbolic quantity; its restrictions still apply. A parameter's absence
from the displayed inputs does not remove it from the mathematical model.

<!-- synth: class=canonical, source=docs/bellman-calculus/03-Stages and perches.md, date=2026-09-07 -->
## Sources and related concepts

The mathematical distinctions are developed in
[Stages and perches §2](../bellman-calculus/03-Stages%20and%20perches.md#2-mathematical-elaboration),
[Operators and builders](../bellman-calculus/05-Operators%20and%20builders.md),
and [Appendix B §§4–7](../bellman-calculus/APPX-B-INITIAL-ALGEBRA.md#4-exact-refinement).
Related concepts are [[stage]], [[perch]], [[operator]], [[sub_builder|sub-builder]], [[aggregation]], [[statement]], [[branch]], [[ordering_conventions|ordering conventions]] and [[source_span|source span]].
<!-- /synth -->
