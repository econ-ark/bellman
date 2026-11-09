---
title: Core concepts
tags:
  - bellman-sym
  - user-facing
  - semgraph
  - workflow
status: Draft
related:
  - "[[01-stage]]"
  - "[[01-the-stage]]"
date: 2026-09-22
audience: user
type: overview
---
# How Bellman-SYM works


> [!summary]
> A model is written as stages, which are joined into periods and a trellis. Bellman-SYM elaborates the stage files into a semantic graph, a record of the model's operations and of their mathematical meaning that a person and a machine can read and that depends on no solver. The graph makes solver code verifiable, since every routine has a stated mathematical operation to compute, and a change of numerical method leaves the stage files unchanged.

Bellman-SYM is a highly expressive declarative functional programming system for dynamic recursive problems.

## 1 What Bellman-SYM does

Consider a household that arrives with assets, receives income, chooses consumption, and saves what remains. In [Bellman-SYM](../wiki/sym.md), this decision problem is written as a modular **[stage](../wiki/stage.md)** in a stage file, a `.bl` file. Although an economist first describes the problem as relations between economic quantities such as consumption and income, its solution and simulation are **higher-order** operations, that is, operations on functions rather than on numbers. In the Bellman equation of such a problem, for instance, the expected continuation value function is combined with current utility and maximized over the feasible choices to obtain the decision value function. These operations define the stage's **Bellman operator**, but how they compose, and the numerical assumptions under which they are approximated, are usually left implicit or embedded in numerical procedures.

Bellman-SYM makes the structure of solution and simulation explicit through **elaboration**, which turns the stage files into a **[semantic graph](../wiki/semgraph.md)** that depends on no solver and that a person and a machine can both read. The semantic graph is a typed record of the **meaning** of the written model: it records the functional operations, the mathematical objects on which they act and which they produce, and how they compose[^backus] (in the terms of universal algebra, a many-sorted algebra[^adj]). The map that takes the stage files to their elaborated meaning is what we call the **meaning map**, [Υ](../wiki/upsilon.md) (Upsilon, see Figure 1). The graph is then a single source from which the model can be implemented, in different numerical implementations and under different calibrations and settings, or its theoretical structure written out. 

<figure markdown="span">
  --8<-- "overview/img/meaning-map.svg"
  <figcaption id="fig-meaning-map">Figure 1. The meaning map Υ: elaboration turns the stage files into the semantic graph, whose denotations are the formal mathematics; the representation map Ρ (Rho) compiles the graph into code, a step outside Bellman-SYM.</figcaption>
</figure>

#rdp 

**Expressive power** 

Bellman-SYM can express [recursive decision processes](../wiki/recursive_decision_process.md) in the sense of Sargent and Stachurski,[^ss] a class of dynamic programs more general than Markov decision processes. It includes life-cycle and infinite-horizon models, models with discrete choices and [branches](../wiki/branch.md), and the individual problems of heterogeneous-agent models together with the distributions they generate.

## 2 Modularity

#periods #trellis

A stage represents a single decision problem as a **Bellman operator**, that is, as one recursive program. In the household's consumption and saving problem, the stage states what the household knows before its income is drawn, what it learns when the income is realized, what it chooses, and how its **continuation value** is formed. The three points at which its information is fixed, arrival, decision and continuation, are the stage's [perches](../wiki/perch.md).

The internal structure of a stage follows the information available within its decision problem, not the model around it: *a stage is a self-contained program that refers neither to the rest of the model nor to its position in time.* Modularity means that stages can be joined into a [period](../wiki/period.md), the stages that together make up one step of the horizon, such as one year of a life cycle, and periods can be joined in turn into a [trellis](../wiki/trellis.md), the sequence of periods across the horizon. Provided that their inputs and outputs agree in type, stages can be rearranged or replaced within a period and reused across models, so a richer model is built by adding stages to an existing one rather than by rewriting it.
<figure markdown="span">
  --8<-- "overview/img/modularity.svg"
  <figcaption id="fig-modularity">Figure 2. The housing tenure model assembled from its stages, with a period drawn as a plate: the <em>tenure choice</em> stage forks into an owner's lane and a renter's lane, a portfolio stage from another model is added where the lanes rejoin, and six of the twenty periods of the life cycle are stacked into the trellis.</figcaption>
</figure>

## 3 Layers of meaning and computational representation 

#semantics #semantic-graph #elaboration #specification

### 3.1 Specifying a stage

The semantic graph denotes the mathematical operations required to solve and simulate the model, and a numerical implementation must approximate them. Bellman-SYM lets you declare the numerical assumptions explicitly as **methods**, such as linear interpolation, Monte Carlo simulation and the endogenous grid method.[^carroll] Because the theory of the stage is written first and the methods are declared separately, the same stage can be implemented in different toolkits and with different numerical approaches, and each implementation can be checked against the mathematical model that it approximates.

Each method is declared in a methods file and attached to a place in the stage: to a whole block, as the endogenous grid method is attached to the policy block; to an operation inside a block, as a quadrature rule is attached to an expectation; or to a named function that is to be stored, as linear interpolation is. The numerical options of a method, such as the size of a grid, are its **settings**, whose values are supplied separately.

Settings are distinct from the model's **parameters**, the exogenous economic quantities that enter its theoretical description rather than its numerical methods. Parameter values are also supplied separately from the symbolic model, so that the theoretical model, its calibration and its numerical approximation remain distinct. Even without parameter values, methods or settings, elaboration produces a **symbolic stage**, whose semantic graph represents the theory with the parameters left symbolic. The stage is then **specified** by supplying parameter values through **calibration**, attaching methods through **methodization**, and supplying their settings through **configuration**, in that order (Figure 3).

<figure markdown="span">
  --8<-- "overview/img/specification.svg"
  <figcaption id="fig-specification">Figure 3. Calibration, methodization and configuration produce successive versions of a stage, each leaving the preceding version unchanged; parameter values enter the stage itself because they determine the economic problem, whereas methods and settings can be changed without altering it.</figcaption>
</figure>

### 3.2 From semantics to code

Once a stage has been specified, you can use its semantic graph to assemble code that solves and simulates the model. This step, **realization**, is the representation map [Ρ](../wiki/rho.md) (Rho) of Figure 1, and it lies outside Bellman-SYM. The graph identifies the mathematical operation that each routine must implement, the method chosen for it, and how its inputs and outputs connect to the rest of the calculation, so you can draw on the routines of an existing toolkit or write your own while keeping an explicit account of the model that they are intended to approximate.

The **Rosetta stone** supports this step by recording which operations and methods are realized by routines in toolkits such as HARK, Dolo and QuantEcon, together with the conventions under which each correspondence holds. Its cards are being rebuilt one at a time from routines that have been checked.

### 3.3 Matsya

#matsya #rosetta-stone

Project Bellman's AI assistant, matsya, which is to draft stage files from a prose description and to assemble solver code from the semantic graph and the Rosetta stone, is not part of this release; its page returns when it is written.

## 4 Workflow

#workflow

The workflow separates the description of the economic problem from the choices made to compute its solution.

1. **Write the stages.** Describe each decision problem in a stage file, stating its timing, information, choices and equations, and state how the stages join into periods and how the periods form the model's trellis.
2. **Elaborate and inspect the model.** Bellman-SYM produces a semantic graph that makes the functional operations and their composition explicit. The resulting **symbolic stage** lets you check the mathematical problem before supplying parameter values, numerical methods or settings.
3. **Specify the stages.** Supply parameter values through **calibration**, attach numerical methods through **methodization**, and supply their settings through **configuration**, in that order. Each step adds its binding to the stage; the **specified stage**, the stage after the three, records the choices needed for implementation but is not yet solver code.
4. **Realize and check the model.** Implement the graph's operations with routines from the chosen toolkit or with your own code, and compose them to solve and simulate the model. Then check the numerical approximation against the mathematical description that the graph retains.

[^carroll]: Carroll, C. D. (2006). The method of endogenous gridpoints for solving dynamic stochastic optimization problems. *Economics Letters*, 91(3), 312–320. The end-of-period value function is equation (11), p. 314.

[^adj]: Goguen, J. A., Thatcher, J. W., Wagner, E. G. and Wright, J. B. (1977). Initial algebra semantics and continuous algebras. *Journal of the ACM*, 24(1), 68–95, §2, pp. 71–75.

[^backus]: Backus, J. (1978). Can programming be liberated from the von Neumann style? A functional style and its algebra of programs. *Communications of the ACM*, 21(8), 613–641, §12, pp. 625–630.

[^ss]: Sargent, T. J. and Stachurski, J. (2025). *Dynamic Programming, Volume I: Finite States*. Cambridge University Press, Chapter 8, "Recursive Decision Processes"; and *Dynamic Programming, Volume II: General States*, forthcoming, online draft edition at dp.quantecon.org, Chapter 7.
