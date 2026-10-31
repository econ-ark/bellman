<!-- notebook cell 0 | id: zm5f1s5z2r -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

# Modular portfolio choice and consumption

## 1 Overview

This notebook provides a self-contained walkthrough of **Bellman calculus** and the `dolo-plus` declarative syntax, focusing on how to use `dolo-plus` to declare a model, rather than the functional-programming machinery. We solve a finite-horizon **portfolio–consumption** problem by composing modular stages into four within-period configurations. Each period has two decisions—**portfolio allocation** ($\varsigma \in [0,1]$) and **consumption–savings** ($c>0$)—declared in separate stages and composed via connectors.

We explore two ideas: **modularity** and **semi-conjugacy**.

>**Modularity**
 Each stage implements an operator $\mathbb{S}$ that takes a **continuation value function** as input and returns an **arrival value function**—i.e., a well-defined Bellman operator. From the stage's perspective, the rest of the model is irrelevant. Stages are composed—rather than merged—within a period using intra-period **connectors**, and periods are linked via inter-period connectors. This lets us build and modify models one stage at a time: swap components, reorder decisions, and reuse a small set of template stage recipes.

>**Semi-conjugacy**
Because the four configurations share the same stage components, their iterated value functions are related by **order semi-conjugacy** (Sargent and Stachurski, 2026). Rearranging the order of the same operators produces period operators that are equivalent up to a transformation. The upshot: we can write the problem in the ordering that best matches economic intuition, but solve a different configuration for numerical reasons (or because a solver is available for that configuration) and then recover the solution to the original problem.

### Declarative syntax

**Bellman calculus** is a system of rules that tells us how to map declarative syntax into the formal definition of Bellman operators.  `dolo-plus` (a fork of `dolo`) is a declarative syntax for modular stages and representation of that syntax in Python (the `dolo-plus` `.mod` file). 

The goal of declarative syntax is to write *what* the computational model is—states, controls, constraints, expectations, methods —rather than *how* to solve it. Following Backus (1978), the same syntax serves two roles:

1. it defines the **mathematical model** (as in a paper), and  
2. it defines (but does not implement) a **computational object** (what a solver executes).

As we will show, almost all of the syntax declarations for a stochastic recursive program boil down to stage syntax.  `dolo-plus`  is simply a collection of declarations—symbols, equation blocks, space constructors—written in `dolo-plus` syntax and serialized in YAML.
#### Stage as meaning and representation

So, `dolo-plus` syntax represents a stage -- a Bellman operator. Bellman gives us rules to implement two maps:

- $\Upsilon$ (**meaning**): interprets stage syntax as  the Bellman operator of a well-defined stochastic program (spaces, transitions, and the stage Bellman operator, including any implied kernels/policies).

$$
\text{Stage syntax} \overset{\Upsilon}{\longrightarrow} \text{Math model}
$$


- $\mathrm{P}$ (**representation**): produces an executable representation (e.g., grids, interpolants, and **callables**) that can be applied as numerical approximations of the Bellman operator.

$$
\text{Stage syntax}
\overset{\mathrm{P},\;\Upsilon}{\longrightarrow}
\text{Callables}
\overset{\text{solve}}{\longrightarrow}
\text{Value fns \& policies}
$$

Bellman calculus (and, in principle, `dolo-plus`) is **language-agnostic**. Everything beyond the syntax—solvers, storage, numerical plumbing—is handled by user code, the *whisperer*, which reads syntax through $\Upsilon$ and applies $\mathrm{P}$ to obtain executable objects. 

Note that the map $\Upsilon$ should be "isomorphic" in some sense, if we translate a stage syntax using $\Upsilon$ to a stochastic program (i.e, map the syntax to  math), the stochastic program should map back onto the the same syntax.\footnote{Strictly, $\Upsilon$ will map to equivalence classes of stochastic programs -- sets of english language model descriptions that represent the same problem.}

> [!note] AI-assisted parsing and verification
>
> Usually,  $\Upsilon$  is instantiated via documentation or is "in our heads". As part of the Bellman calculus project, we also use an explicit implementation of $\Upsilon$ called **Matsya**, an LLM-powered operator that parses  `dolo-plus` into english language problem definitions using retrieval over Bellman calculus semantic rules, a training dataset, with iterative refinement.
>
> We can think of Matsya as implementing and approximation of $\Upsilon$ in both directions:
>
> 1. **Forward** ($\hat{\Upsilon}$): stage syntax $\to$ a formal stochastic program (spaces, transitions, Bellman equation).
> 2. **Inverse** ($\hat{\Phi}$): a stochastic program $\to$ the corresponding stage syntax.
>
> A well-defined stage should survive the round trip $\hat{\Phi}\circ \hat{\Upsilon}(\mathsf{Stg})$. That is, a well-defined stage is a fixed point $\hat{\Phi}\circ \hat{\Upsilon}\mathsf{Stg}=\mathsf{Stg}$.
>
> Matsya's `--refine` mode automates the process of finding such a fixed point by initializing $\hat{\Phi}$ with high temperature and iterating lower and lower tempratures. If refinement does not converge, the remaining differences typically point to genuine ambiguities that require judgement—mirroring **CEGAR** (counterexample-guided abstraction refinement), where each diff tightens the specification.