---
title: Semantics
tags:
  - docs/overview
  - bellman-sym
  - user-facing
  - semantics
  - semgraph
  - workflow
status: Draft
related:
  - "[[01-the-stage]]"
  - "[[14-appendix-c-syntax-to-semantics]]"
date: 2026-09-28
audience: user
type: overview
---

# Semantics

<!-- > [!todo]
> **AAS (19 Sep 2026):** Page to be written. -->

> [!summary]
> Elaboration reads a stage file and constructs one Python object, the stage object. We describe what it holds, in words and on the buffer-stock stage: the table of everything the file declares, two graphs of the blocks on the fields they read and write, and two graphs of the operators the blocks denote, backward on value functions and forward on finite measures. We then describe how parameter values, numerical methods and settings are attached, and what a stage with all three attached still does not contain.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](02-stage.md): perches, fields and the Bellman equation of a stage; [The Bellman-SYM language](03-language.md): the buffer-stock stage file this page reads.
> **Used by** — [Workflow](06-workflow.md): elaboration and specification as steps of the workflow.
> **See also** — [The stage](../Bellman-Sym/API/stage/01-the-stage.md) and the pages after it in the API: every object of this page with the listing the package prints for it.
> **Formal account** — [Bellman calculus](../bellman-calculus/index.md): the mathematics the graphs represent; [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the rules by which equations are read as functions.

> [!note]- Key terminology
> | Term | What it names |
> |---|---|
> | [Block](../Bellman-Sym/01-stage.md#3-builder-blocks) | A group of equations of a stage file between declared inputs and outputs: forward when it writes the states of a later perch, backward when it writes values or the control (§2). |
> | [Semgraph (semantic graph)](../wiki/semgraph.md) | What elaboration builds from a stage file: a table of every declared object and four graphs whose boxes are the blocks and the operators they denote (§1). |
> | Elaboration | The step that reads a stage file and constructs the stage object (§1). |
> | Initial diagram | The blocks of one direction on the fields they read and write; one graph backward and one forward (§3). |
> | Builders graph | The same blocks as the operators they denote, on function wires backward and on measure wires forward (§4, §5). |
> | [Builder](../wiki/builder.md) | The operator a block denotes; one box of a builders graph (§4). |
> | Grain | How far a graph's boxes are opened: one box per block, or each block opened into its primitive operators (§4). |
> | Specifying a stage | The three steps, [calibration](../wiki/calibration.md), [methodization](../wiki/methodization.md) and configuration, that attach parameter values, methods and settings (§6). |
> | [Specified stage](../wiki/specified_stage.md) | A stage that has been elaborated, calibrated, methodized and configured (§6). |

We read the repository's buffer-stock stage, `applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl`. It is the normalized buffer-stock model: the household arrives with assets `k`, a permanent income shock `ψ` and a transitory shock `ξ` give its market resources `m`, it chooses consumption `c`, and it saves `a = m - c`. Each [perch](../wiki/perch.md) carries a value, and the derivative of a value is read where it is needed by a derivative term, `D_{a}V[>]` for the derivative of the continuation value in savings. The policy block states the maximization alone, `c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])`. The three lines of the endogenous grid method stand in the methods file beside the stage file, `applications/buffer-stock/declaration/stages/buffer_stock/methods.bl`, an addition to the stage file that is read together with it ([Methodization](../Bellman-Sym/04-methodization.md) §1), appended to the policy block: consumption from the inverted Euler equation at each level of savings, `c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])`, the resources at which that consumption is chosen, `m[>] = a + c[>]`, and the line `c[~] = c[>]`, which states that the policy at those resources is that consumption. The derivatives of the decision value and of the arrival value stand in the same file, each appended to the block of the value builder that writes the value (§6).

## 1 What elaboration builds

**Elaboration** reads the stage file and constructs one object, the **stage object**. The object is a **stage occurrence**: the file elaborated at one position of a [period](../wiki/period.md), with its own parameter values, methods and settings. One file may be elaborated at several positions, and each elaboration is a separate object that shares nothing with the others. The file is parsed once, and the parsed syntax tree is discarded once the object is constructed: everything the rest of this page describes is read from the object, never from the text again.

The object holds the stage's declared name, the file's other `@` lines, a table of definitions, four graphs, the bindings and the provenance, which records the file, its digest and where each binding was read from. The table and the four graphs together are the stage's [semgraph](../wiki/semgraph.md), its semantic graph. A **graph** here is made of **boxes** joined by **wires**, each wire carrying one typed object, and the package stores each graph as a hypergraph of the diagram library DisCoPy, a graph whose wires may join several boxes. Nothing else is stored: whatever the table and the graphs determine is computed when it is asked for.

For a model of several stages, each stage file is held in a **record**, a dictionary with the file's text and the three mappings of methods, settings and calibration, and a [trellis](../wiki/trellis.md) arranges the records into periods ([Periods and trellis](04-periods-and-trellis.md)). Elaborating a trellis constructs one stage occurrence at each position and attaches nothing yet.

## 2 The definitions

Every name the file declares is kept once, as a record with a kind and an identity of the form `<stage>:<kind>:<name>`, and the graphs refer to the records by identity. A line of a block is a record too, named by its address, such as `cntn_to_dcsn.value`. The sets, the parameters, the distributions of the two shocks, the utility function, its marginal utility, the inverse of that marginal utility and the correspondence of feasible consumption each have one record.

A block is **forward** when it writes the states of a later perch and **backward** when it writes values or the control, and two kinds of record are made from the blocks. The **law of motion** `𝑔` of a forward block is the map from the fields it reads to the fields it defines: for the saving block, `(m, c) ↦ m − c`, whose declared sets state the borrowing constraint. The **value aggregator** `𝐺` of a backward block is the map that combines the continuation value with current quantities into the block's value: for the decision block, `(V[>], m, c) ↦ 𝑢(c) + β V[>]`. Each record prints its own **card**, the printed description the package gives of one piece of the stage: the function it denotes under `Defines`, any conditions on its values under `Conditions`, the statements of the file it comes from under `Source`, and the key of each declared name it writes, the parameters among them, under `Definitions referenced`.

The equations keep the names of the parameters; their values arrive later, with calibration (§6). Each argument of `𝐺` is a number, not a function, and is written in roman type; the functions the operators read are written in italic. A declared set imposes a condition that a reader or a routine must check: the construction states the condition and does not establish it.

## 3 The two initial diagrams

An **initial diagram** has one box per block of one direction, wired by the [fields](../wiki/field.md) those blocks share, so that every wire is a field. The forward diagram is supplied with the arrival assets `k[<]` and the two shocks, and produces the continuation assets `a[>]`. The backward diagram is supplied with the continuation value `V[>]` and produces the arrival value `V[<]` and the policy `c`.

Consumption is written by the policy block, and no wire carries it to another block. The decision block and the saving block list `c` among their inputs, but a control that a block lists among its inputs is a **coordinate**, the variable its lines are written in, not a field that another block supplies. Neither block has an input wire for it, and the `Signature` section of each block's card, which lists the wires, does not list it.

The two diagrams are read separately. The forward one is not supplied with the continuation value, the backward one is not supplied with the arrival state, and neither computes what the other computes.

## 4 The backward builders

In the **backward builders graph** every wire carries a function and every box is an operator on functions. At the **builder grain** each block is one box, its [builder](../wiki/builder.md), the operator the block denotes. The decision builder takes the continuation value function `𝑉[>]` and returns the decision value `𝑉`; the arrival builder takes `𝑉` and returns the arrival value `𝑉[<]`; the policy builder takes `𝑉[>]`, the one function its maximization reads, and returns the policy `𝑐`. The two derivative lines of `methods.bl`, each appended to the block of the value builder that writes the value, state the derivative of the decision value in resources, `D_{m}V = 𝑑𝑢(c)`, and the derivative of the arrival value in assets, with the factor of the law of motion; methodization records each at the Evaluation of the builder that writes the value, and neither adds a box (§6).

The decision builder is a **builder at a policy**. Its equations are written in the control, and the policy `𝑐` stands in place of the control wherever it appears, in the law of motion and in the aggregator, so each policy gives one operator, all with the same inputs and outputs. The policy is no input wire of the decision builder: it is a name the builder's operations refer to, and its type is printed once, on the output of the policy builder.

A **grain** chooses which boxes are opened without changing what the graph represents. At the **primitive grain** each builder is opened into its **primitive operators**, the finest boxes the construction makes. A value statement becomes a chain of boxes of a few kinds. The **pullback** composes the continuation function with the block's law of motion, so that `𝑉[>]` becomes `𝑉[>] ∘ 𝑔`. The **expectation** integrates over the shocks the distribution declarations name. The **aggregation** applies the block's `𝐺` at each point. The **evaluation** returns the result unchanged, under the field's name and in the set the file declares for it. Arithmetic, parameters and named functions are not boxes: they are part of the rule of the box that applies them. In the policy block, the maximization becomes a pullback of the continuation value along the law of motion, an aggregation that forms the choice value, an argmax and the evaluation. Once the methods file's block `policy` brings the lines of the endogenous grid method (§6), the operative policy builder's operations are those lines instead: the inverted Euler equation and the line that gives resources become one aggregation on functions of savings, and the line `c = c[>]` becomes a pullback of the policy along the map from savings to resources, a relation that the policy must satisfy at the resources that map reaches.

Read the decision builder from the top. The pullback gives the continuation value at savings, a function of resources and consumption; the aggregation adds current utility to the discounted continuation value, which is the choice value

$$
Q(m,c)=u(c)+\beta\,W(m-c),
$$

where $W$ is the continuation function on the wire `𝑉[>]`. With the policy in place of the control, `c = 𝑐(m)`, this is the decision value `𝑉`, which the evaluation returns under its name. On the arrival builder the pullback reads the decision value at `R*k/(Γ*ψ) + ξ`, an aggregation applies the map the value statement writes inside its expectation, and the expectation integrates over `ψ` and `ξ`; the derivative line of the arrival value in `methods.bl`, appended to the arrival builder's block, `D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)`, keeps the factor `R/(Γ*ψ)` of the law `m = R*k/(Γ*ψ) + ξ`. [From syntax to a mathematical problem](../Bellman-Sym/09-from-syntax-to-formal-problem-definition.md) writes the same equations with their state arguments explicit.

The Bellman equation needs analytic conditions that the construction does not establish: that each expectation is finite, that the maximum is attained and that a measurable maximizer exists. The stage lists the first among its **obligations**, the conditions it states, each under its name with its formula or sentence, and a mark where the declarations or the calibration settle one; it states nothing about the second or the third.

## 5 The forward builders

In the **forward builders graph** each wire carries a finite measure over the states of a perch, the distribution of the population, whose total mass need not be one; a shock's own distribution remains a probability measure. Each box carries a measure forward through the same equations. Only the two forward blocks appear. The **distribution extension** extends a measure over the states by the distribution of a shock, giving the joint measure of the states and the shock; this stage has two, one for `ψ` and one for `ξ`. The **push-forward** carries the joint measure through the law of motion `m = R*k/(Γ*ψ) + ξ`.

The second forward builder is one push-forward at the policy: it carries the decision measure through `a = m − 𝑐(m)` to the continuation measure `μ[>]`, referring to the policy as the decision builder does, and no wire joins it to the policy builder. The forward graph can therefore be evaluated only once a policy has been chosen, by the backward graph or by the user. The two graphs are two readings of one set of equations, on functions and on measures, and [Operators and builders](../bellman-calculus/05-Operators%20and%20builders.md) states the duality that relates them.

## 6 Specifying the stage

Three steps **specify** a stage. **Calibration** supplies a value for every declared parameter. **Methodization** types a numerical method at a **place** of the stage, the written address of one of its operators: a block, a named statement, an operator occurrence such as the expectation `E_ψ_ξ`, a definition, or the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that closes a builder, such as `policy.evaluate`, where a representation is written. **Configuration** supplies the [settings](../wiki/settings.md) the attached methods read, such as the size of a grid. We make them in that order, and each adds its binding to the stage it is called on and returns that stage; nothing is copied, and a later binding replaces the earlier one of its kind ([The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md)). The equations keep the names of the parameters, so a sweep over `β` binds each value in turn to the one stage, whose graphs no binding changes. The buffer-stock methods file, `methods.bl` beside the stage file, names the endogenous grid method on the policy builder and appends the method's three lines to the policy block under the method `!egm`, so that the operative builder's operations are the three lines of the method while the stage keeps the maximization as the builder it declares, and appends one derivative line to each of the decision and arrival builders' blocks, which is recorded at that builder's Evaluation as the stated derivative of the value. The stage lists the condition under which the method's lines give the policy the maximization defines, `egm-eligibility`, and the reading of each derivative line, `marginal-reading`, among its obligations, and checks neither.

For a trellis, the three trellis verbs bind every stage occurrence from the mappings its record holds ([Workflow](06-workflow.md) §1). A **specified stage** is the result: constructed, calibrated, methodized and configured. #specification

## 7 What a specified stage is not

Nothing above has solved the household's problem, and a specified stage does not contain a solution. It contains no numerical routine: an entry of a methods file names a technique and a routine without running them. It contains no terminal data: the continuation value `𝑉[>]` is an input the stage leaves open, supplied by the next period or by a terminal value function. And it has established none of the analytic conditions of §4. Solving requires the routines, the composed model and the continuation or terminal data. [Methodization](../Bellman-Sym/04-methodization.md) describes the routines, and [Trellises](../Bellman-Sym/07-trellis.md) the terminal data.
