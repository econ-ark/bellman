---
title: A piece
tags:
  - docs/api
  - operator
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# A piece

> [!summary]
> A piece with no interior is either an operation inside a builder, one [primitive operator](../../../wiki/operator.md), or an authored line inside a [block](../../01-stage.md#3-builder-blocks). Each is read by its name from the piece that holds it and answers its printed record, its inputs and outputs, its conditions and its methods; an operation also answers the kernel it applies and that kernel as a Python function. §5 states the conventions by which every card is read, and §6 the types a [wire](02-initial.md) and an operation answer. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`.

> [!info]- Relationship with other documents
> **Builds on** — [A builder](04-builder.md): the builder whose operations are read here; [The initial diagrams](02-initial.md): the blocks whose lines are read here.
> **Formal account** — [Operators and builders](../../../bellman-calculus/05-Operators%20and%20builders.md): the operators a kind of operation realizes.
> **See also** — [Operations](../../reference/operations.md): the kinds an operation can be; [API](../index.md) §2.4: every path of the stage object in one table.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 An operation

An operation is read from its builder by its name after the builder's own, `stage.dcsn.builder.bwd["pullback"]`, or from a graph at the primitive grain by its whole name, `stage.builder.bwd.primitives["cntn_to_dcsn:Pullback"]`. Its `denote()` answers its card: the functions it reads and writes with their types, the law of motion at the policy where the operation reads one, the rule it applies, the conditions the construction has not established, the line of the file it realizes and the records of the definitions table the card names. `print(pullback)` prints the same card.

```python
pullback = stage.dcsn.builder.bwd["pullback"]
print(repr(pullback))
print(pullback.denote())
```

```text
Operator('cons', 'cntn_to_dcsn:Pullback')
STAGE cons / BACKWARD BUILDER cntn → dcsn (cntn_to_dcsn) / Pullback
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → [−∞, ∞)
       ──────────────────
  out  𝑉≻ ∘ 𝑔≻(·, 𝑐)
           : Xm → [−∞, ∞)

Rule
  (𝑉≻ ∘ 𝑔≻(·, 𝑐))(m_d) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  17  a = m_d - c

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

A card has its title over a heavy line; then its sections, each opening with its heading at the left margin, its content two columns in and a blank line between two sections; then a light line, the sections `Source` and `Definitions referenced`, and a heavy line that closes it. No line passes column 78, and a section with nothing to print is not printed. An operation's card has, in this order: `Signature`, its input wires under `in` and its output wires under `out`, each with its type, and a short line between the two; `Where`, the local names its rules use, each stated once: the law of motion at the policy where the operation reads one, with its type and its rule at a point, the law of motion read at one label of a branching block, the outputs of a law named by their fields, and the set of admitted pairs of a block that declares a multiplier ([Constraints](../../10-constraints.md) §4.2); `Rule`, the rule the operation applies; `Conditions`, the memberships the rule needs that the construction has not established; on a methodized version, `Method`, the method bound within the piece with its handler and, at the right margin, the place it is bound at, and `Options`, the method's options with the values of the settings they name, both left out on the card of a block, of a line and of a piece read through `stage.declared`, whose `methods` answers them; `Source`, which names the file once and gives each line the operation realizes, as the author wrote it, after its line number, with a section for each file where the lines stand in the stage file and its methods file; and `Definitions referenced`, the key of each declared name the card writes, followed by the file and the line where the methods file defines the name. A line of the file stands once on a card, under `Source`, and what it denotes stands in the sections above; the identity of a wire is on the record and in no column of the card.

Read along the wires of the decision builder: the continuation value 𝑉≻ is a function of savings `a`; the pullback composes it with the law of motion, so that 𝑉≻ ∘ 𝑔≻ is a function of `(m_d, c)`; the aggregation applies 𝐺; the policy indexes the pullback, the aggregation or the conditional distribution in which it occurs; and the evaluation returns 𝑉 under its field name as a function of `m_d` alone, with the derivative that the line `cntn_to_dcsn.marginal` states, `D_{m_d}𝑉(m_d) = 𝑑𝑢(𝑐(m_d))`, recorded beside it.

`denote()` is the one verb below the stage that answers a piece's record: an operation, a builder, a sub-builder, a builders graph at any grain, an initial diagram, a block and a line each answer it, and the definitions table answers it for one of its records, `stage.definitions.denote(identity)` ([The definitions table](08-definitions.md) §3). The record holds the mathematical structure of what the piece denotes: the typed wires, the image, the kernel with the statements it denotes and the objects they denote, the hypotheses, the conditions and, on a methodized version, the method bound within the piece, except on a block, a line and a piece read through `stage.declared`, whose records hold no binding; an aggregation's record also states, under `affine`, in which of its value inputs the map is affine, `V in V≻` on the decision builder. It displays itself, so `print(piece)` and `print(piece.denote())` write the same card, and the card is that record printed, never made by taking a printed line apart.

`signature()` answers the operation's inputs and outputs, the same wires with their types that the card's `Signature` section names; the identity of each wire stands on the record it answers, under `.inputs` and `.outputs`, and in no printed column. `list()` answers an empty listing, since an operation has no interior, and `box` answers the DisCoPy box, an object of the diagram library the package keeps its graphs in ([The initial diagrams](02-initial.md) §2).

```python
print(pullback.signature())
print(pullback.list())
```

```text
in         𝑉≻ : Xa → [−∞, ∞)
out        𝑉≻∘𝑔(·, 𝑐) : Xm → [−∞, ∞)
none
```

Two kinds of operation are the two actions of one law of motion 𝑔. A **pullback** composes a function with 𝑔, $V \mapsto V \circ g$; a **push-forward** carries a measure through the same 𝑔, $\mu \mapsto g_\# \mu$, the measure that gives a set $B$ the value $\mu(g^{-1}(B))$. With the pairing $\langle \mu, V \rangle = \int V \, \mathrm d\mu$ the two satisfy $\langle g_\# \mu, V \rangle = \langle \mu, V \circ g \rangle$: the average of 𝑉 under the measure the law of motion produces is the average, under the original measure, of 𝑉 at the law of motion's output. That change-of-variables identity holds for bounded measurable 𝑉 and wherever the two integrals are absolutely finite ([Operators and builders](../../../bellman-calculus/05-Operators%20and%20builders.md) §3), and it is why one word is used backward and the other forward. It is the deterministic statement: where a block reads a shock, the integral over that shock is a separate box on each side, an expectation in the backward graph and a box that extends the measure by the declared distribution in the forward graph. The consumption stage declares no shock, so neither box appears in its graphs. The push-forward's card:

```python
print(stage.dcsn.builder.fwd["pushforward"].denote())
```

```text
STAGE cons / FORWARD BUILDER dcsn → cntn (dcsn_to_cntn) / Pushforward
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ   : finite measure on Xm
       ──────────────────────────
  out  μ≻  : finite measure on Xa

Rule
  μ≻(B) = μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  17  a = m_d - c

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 2 The kernel

`kernel()` answers the **kernel** an operation applies, the pointwise function it reads from the definitions table and from which the card's `Where` and `Rule` sections are written: the law of motion 𝑔 for a pullback or a push-forward, the aggregator 𝐺 for an aggregation. Its attribute `origins` holds the records of the definitions table it is read from.

```python
aggregation = stage.dcsn.builder.bwd["aggregation"]
print(aggregation.kernel())
print([record.identity for record in aggregation.kernel().origins])
```

```text
𝐺 of cntn_to_dcsn: 𝐺(V≻, m_d, c) = 𝑢(c) + V≻
output V; unused m_d
['cons:G:cntn_to_dcsn']
```

The first argument of 𝐺, `V≻`, is its value input: the scalar continuation value the aggregator receives once the continuation value function has been composed with the law of motion, the continuation value at the saving `a = m_d - c`. The line `outputs (V); unused m_d; V reads V≻, c` records that `m_d` does not enter the output and then names the arguments the output reads: 𝑉 reads the value input and consumption. An aggregator with several outputs answers this way whenever they read different arguments, so that what one component depends on is read and not inferred from the list of unused arguments.

In a [branching](../../05-branching.md) block, a pullback of one branch applies the complete law of motion, so its `kernel()` prints the components of every branch, with the coordinate whose value selects the branch, the label coordinate, among the unused arguments. The record's attribute `section` holds the kernel of that law read at the branch's label, the map the card's `Where` section defines, `𝑔_keep≻` for the branch `keep` of the durables model's `tenure.bl`: the same title, the law's arguments without the label coordinate, and the components of the fields the branch writes with their outputs and what each reads, printed by the same rules. `section` holds no Python text, since `compile_kernel()` compiles the complete law, and it is `None` on every other operation.

On a symbolic version as on a calibrated one, `compile_kernel()` answers the kernel as a Python function, whose arguments are those of the printed kernel in the same order, followed by the parameters the kernel reads. It evaluates the kernel at points; it neither integrates, nor chooses, nor solves.

```python
import inspect

calibrated = stage.calibrate({"ρ": 2.0})
aggregator = calibrated.dcsn.builder.bwd["aggregation"].compile_kernel()
print(inspect.signature(aggregator))
```

```text
(V_cntn, m_d, c, ρ)
```

The record `kernel()` answers holds under `python` the source text of one plain Python function, and `compile_kernel()` executes that text in a namespace holding NumPy alone and answers the function, which is attached to no stage. Its arguments are the kernel's own, in the printed order, followed by each parameter the kernel reads, in the order of the declarations, whose names `parameters` holds; `parameter_values` holds the values the version's calibration binds to them, `None` on a symbolic version, where the caller supplies them. The values are passed at each call, so that a new calibration needs no new function. Given numbers the function answers a number, or a tuple of numbers where the kernel has several outputs, and given NumPy arrays it answers arrays:

```python
aggregation = calibrated.dcsn.builder.bwd["aggregation"]
g = calibrated.dcsn.builder.bwd["pullback"].compile_kernel()
G = aggregation.compile_kernel()
print(g(2.0, 0.5))
print(G(4.0, 2.0, 0.5, *aggregation.kernel().parameter_values))
print(aggregation.kernel().python)
```

```text
1.5
2.0
# bellman kernel of cons, cntn_to_dcsn:Aggregation; cons.bl sha256 e60110b0b964ce482812c558922bc7aa6eaaf14421e2e162b9f87cc7b120a667; bellman 0.1.6
# 𝐺 of cntn_to_dcsn: 𝐺(V≻, m_d, c) = 𝑢(c) + V≻
# output V; unused m_d
# parameters: ρ ∈ [1, inf)
# names: V_cntn is V≻; u is 𝑢
import numpy as np

def G_cntn_to_dcsn(V_cntn, m_d, c, ρ):
    def u(c):
        return c**(1 - ρ)/(1 - ρ)
    V = u(c) + V_cntn
    return V

```

`g(2.0, 0.5)` evaluates the law of motion at `m_d = 2` and `c = 0.5` and returns the saving; `G(4.0, 2.0, 0.5, 2.0)` evaluates the aggregator at the continuation value 4, `m_d = 2` and `c = 0.5`, with `ρ = 2` passed last, and returns 𝑉, the one output that the line `outputs (V)` of the printed kernel names. The comment lines of the text name the stage, the operation, the stage file with the digest of its text, the package's version, the printed rule, the Python name given to each name of the file and the declared set of each parameter; they hold no date and no value, so the text of an unchanged model does not change. The function 𝑢 that the rule calls is written inside the function, so `numba.njit(G)` compiles it in one call, `inspect.getsource(G)` prints its definition and cloudpickle saves it. The standard `pickle` and Numba's cache refuse a function made in memory; for them, write the text to a file of your choosing and import the function from that file. A builder answers the kernels of all its operations as one record, `kernels()` ([A builder](04-builder.md) §5).

`compile_kernel()` is refused with a `ConstructionError` under the rule `kernel-target` on an operation that applies no explicit function, an evaluation among them, whose `kernel()` states the identity it applies, and on a row that states a relation with no explicit side, the identification `c = c[>]`; an authored line refuses both verbs (§4). It is refused under the rule `kernel-form` on an operation whose kernel calls a function the stage file defines by a derivative or an inverse, `𝑑𝑢 := D_{c}(𝑢)` or `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)`, and the refusal names the call. A row that reads a derivative term compiles, the term among the function's arguments: the candidate line `InvEuler` of the policy builder reads `D_{a}V[>]`, its `kernel()` prints the map with the term, `(D_{a}𝑉≻, a) ↦ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻)`, and its `compile_kernel()` answers the function `G_policy_InvEuler(V_cntn, a, argument, ρ)`, whose third argument takes the value of the term, since `𝑑𝑢𝑖𝑛𝑣` is defined in closed form ([Expression forms](../../reference/forms.md) §3).

## 3 Conditions and methods

`obligations()` answers every condition the operation owns, each with its status; a condition that the declarations or the calibration settle is marked `[established]`, as the one below is. `methods` answers the method bound at the operation, empty before [methodization](07-methods.md).

```python
pushforward = stage.dcsn.builder.fwd["pushforward"]
print(repr(pushforward))
print(pushforward.obligations())
print(pushforward.methods)
```

```text
Operator('cons', 'dcsn_to_cntn:Pushforward')
range-compatibility   m_d − c(m_d) ∈ Xa   [established]
none
```

The one condition here is established: the declared sets decide that the law of motion at the policy takes its values in `Xa`, and the declaration is its evidence.

## 4 An authored line

A line of a block is read from its block by its id, `stage.initial.backward["cntn_to_dcsn", "value"]`, and answers `denote()`, `signature()`, `obligations()` and `methods`; [The initial diagrams](02-initial.md) §3 prints one. A line states a relation and applies no rule, so it refuses `kernel()` and `compile_kernel()`: the operation that realizes it is the piece that applies a rule. A line marked `!doc` has no box and answers `denote()` and `methods` alone; the consumption stage marks none, and its maximization `optimality` is a line with a box, whose card prints the line as the file writes it.

```python
optimality = stage.initial.backward["policy", "optimality"]
print(repr(optimality))
print(optimality.denote())
```

```text
Line('cons', 'policy.optimality')
STAGE cons / POLICY BLOCK policy / optimality
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source  cons.bl
  30  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 5 Reading a card

These conventions are read across every card and every printed signature, and written on none of them.

- `x ↦ e` binds the point, and an operator acting pointwise writes its image as `x ↦ …`.
- `↦` maps a point to its image in a `Defines` line and in a rule; the file's `:=` and its ids stand only in the lines of `Source`, as the author wrote them.
- The policy is a free name: there is one operator for each policy, and that policy indexes the pullback, the aggregation or the conditional distribution in which it occurs. A decision builder's card names it under `At`, never as a parameter or as an input wire.
- An evaluation is the identity on a function, or on a set of feasible policies, into its declared carrier.
- Under `Operations` the pieces stand in the order of application, each after every piece that writes a wire it reads, and `∘` applies its right factor first.
- A card's `Conditions` section carries no status word: the words `required`, `assumed` and `established`, and the evidence of a condition the declarations settle, stand on `obligations()` (§3).
- A set written `{f ∈ … | ∀ a ∈ Xa, x ∈ 𝑐≻(a): …}`, as the identification's `signature()` prints it ([A builder](04-builder.md) §2), is the set of the functions that satisfy the rule at every admitted pair, possibly empty, with no selection made.
- A push-forward's rule gives the image measure at a set `B`, `μ≻(B) = μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})`, the measure of the points the law of motion at the policy sends into `B`; and `λ⊗P` is the extension of a measure `λ` by the declared distribution `P` of a shock, whose rule integrates `P` against `λ`.
- A mark at the right margin of a line is the region note `on …` of a rule, the set on which the rule holds, or the address at which a method is bound; `undeclared` in a type is a set the file does not declare; and `⇉` marks a correspondence.
- `Method` names the numerical method bound within the piece, which is part of what the piece denotes on the version asked; a block, a line and a piece read through `stage.declared` print none, and their `methods` answers the methods bound within them.

## 6 Types and defining expressions

A wire's type is derived from the declarations when it is asked for and stored nowhere. The continuation input of the decision builder goes through seven steps from the file to the printed type:

1. The file declares `V[>] : [-inf, inf) @ !vlu`.
2. The declaration introduces a field, a named quantity at the continuation perch with the declared value set `[-inf, inf)`.
3. The builders graph has a wire for that input, whose `Sort` keeps the wire's identity and its field classification.
4. The wire's mathematical type is derived from the declared sets of its ordered coordinates and its declared value set; where a control is among the coordinates, its feasibility correspondence also restricts the domain of the arguments. Here the type is the set of measurable functions from the savings set `Xa`, declared `ℝ₊`, to `[-inf, inf)`.
5. The query answers a structured carrier expression, which denotes that set of functions.
6. The set itself is the carrier, and no object of the package is that set.
7. The printed type, `Xa → [−∞, ∞)`, is the printed form of the carrier expression.

The wire `stage.dcsn.builder.bwd.signature().inputs[0]` answers the derived type through `.mathematical_type`, a `WireType` with two attributes: `.sort`, the representation, the field classification where there is one, the ordered identities of the coordinates, the domain of the arguments and the result set; and `.carrier`, the structured carrier expression. The wire's `.identity` names the continuation input; neither the type nor the carrier identifies that particular input. A wire of an initial diagram is typed by the field it carries, printed `{V≻}`, and a wire of the forward graph by the finite measures on the states of its perch.

An operation's record answers its typed defining expression, `stage.dcsn.builder.bwd["Pullback"].denote().expression`, the composition with the stage's law of motion, whose `.bindings` and `.body` are expression objects and not fragments of the printed card; `denote().kernel.denoted[0]` answers the `.mathematical_type` and the `.expression` of the law of motion itself. The definitions of a utility or an aggregator answer the same queries where their data determine them, and a component the package cannot resolve names the mathematical data it lacks rather than being assumed real-valued. `Denoted.type` and `Denoted.rule` are the printed forms of the carrier and of the defining expression, each computed from the object beside it, `mathematical_type` and `expression`, so that the card, the structured answer and the encoding present one object and never two readings of it. A set marked `!categories` ([Symbol conventions](../../reference/symbols-conventions.md) §9.3) denotes a second object, its category map, and its card, `stage.definitions.denote(identity)`, holds a second `Denoted`, whose `expression` is the set's `CategoryCodes` record, `Definition.categories` ([The definitions table](08-definitions.md) §2), and whose `rule` is the map as `bellman.typing.category_codes.describe` writes it, `0 ↦ newborn, 1 ↦ old (categories household_status)`, or `(categories local to HouseholdStatus)` where the marker names no identifier. Every answer of `denote()` whose definitions include the set holds both objects. A declaration of one real shock by `N`, `LogNormal`, `Uniform`, `TruncatedNormal` or `TypeIExtremeValue` likewise denotes a second object, its measure at the written arguments under the symbol `P_y` ([Shock distributions](../../reference/laws.md) §1); the answers of `denote()` of the other records that read the declaration list it by its law alone, the measure standing on the declaration's own card, and the cards of the expectations and distribution extensions that read it print the law as written alone; the forward builder's card also names the measure `P_y` that its extension rule reads, as before.

A printed carrier, a function belonging to the set it denotes and a numerical representation of that function are three different objects. Methodization leaves the carriers unchanged, and a declared carrier says where an object must lie: it proves no measurability, finiteness or feasibility, and no numerical method's correctness. The restricted domains of the defining expressions state those requirements.

A wire that is the output of a joint choice answers two more attributes. `Wire.controls` names the declared controls of the policy, in the order the block writes them, and is empty on every other wire. `Wire.component(name)` answers the set-valued type of one of them, the set of functions of the decision state that agree, coordinate by coordinate, with some member of the joint set; it creates no wire, selects no policy, and raises `KeyError` for a name that is no control of the wire. A wire holds the carrier its query derived and no reference to its stage, which is how a card or an encoding is written away from the version it came from.

On a [branching stage](../../05-branching.md) the continuation state space is the disjoint union of the branches' state spaces, $\mathsf X_\succ = \bigsqcup_j \mathsf X_{\succ,j}$, one set for each label, named by the fields its branch writes. A function on it is the tuple $(Q_j)_j$ of functions, one on each branch's set, and a finite measure on it the tuple of measures, $\operatorname{Meas}(\bigsqcup_j \mathsf X_{\succ,j}) \cong \prod_j \operatorname{Meas}(\mathsf X_{\succ,j})$, writing $\operatorname{Meas}(\mathsf X)$ for the finite measures on $\mathsf X$. Each branch value is therefore typed on its own branch's set, `V_w[>]` of the retirement choice on the set of `a_w`, and the forward builder writes one measure for each branch.
