---
title: Methods
short_title: Methods
status: not yet drafted — stub notes only
tags:
  - bellman-calculus
  - methodization
  - method
  - status/stub
audience: user
type: theory
topic: [calculus]
---

# Methods

> [!summary]
> These unfinished notes distinguish a mathematical operation from the numerical method and handler used to approximate it. Method choice requires compatible domains and applicability conditions.

> [!info]- Relationship with other documents
> **Builds on** — [Operators and builders](./05-Operators%20and%20builders.md) defines evaluation and selection.
> **Used by** — [Method types](../Bellman-Sym/reference/methods.md): the method types a methods file names, each with the operation it realizes; [Methodization](../Bellman-Sym/04-methodization.md): the source attachments, with their supported addresses and entry fields.

> [!note] Not yet drafted — stub notes only
> Structural outline only; the full method table is not yet written.

**Methodization** assigns a numerical procedure to a supported computation in the declared model. A **handler** is a routine that computes that procedure. Selection and evaluation remain distinct mathematical operations; the method must apply to the equations and domains supplied by the stage.

## 1. The methodization step

The choice-value function supplies the objective; a policy selects a feasible action; evaluation gives the value under that policy. Numerical methods may approximate different parts of this calculation:

- a function representation, such as a grid with interpolation, polynomial coefficients, or another approximation with stated accuracy conditions;
- a policy calculation, such as feasible-action search, first-order inversion, or Euler-equation time iteration, under the conditions making it applicable.

A method can evaluate an entire block or a supported operation within it. Numerical interpolation and candidate comparisons may be internal steps; assigning a method does not create authored `evaluate` or `upper_env` equations. An implicit relation still requires existence and a specified selection, with optimality checked separately. Two methods need not use the same numerical representation or choose the same policy at a tie.

*(Placeholder.)* Develop the map from mathematical operators to numerical procedures. Stage equations remain `.bl`, and methods, settings and calibration remain YAML. Supported addresses and entry fields are defined by Bellman-SYM's rules for [methodization](../wiki/methodization.md); this unfinished chapter does not duplicate that source specification.

## 2. Forward methods

*(Placeholder.)* Describe Monte Carlo simulation and histogram approximation for the declared discrete-time transition law and a supplied policy. Forward probability propagation pairs with undiscounted transition expectation, not with the reward-bearing Bellman update. A continuous-time Kolmogorov or Fokker–Planck equation requires its own model and assumptions. [Operators and builders](./05-Operators%20and%20builders.md) §9 defines the forward operation.

<a id="see-also"></a>

## 3. Related documents

- **Across:** [Operators and builders](./05-Operators%20and%20builders.md), [Ingredients](./ingredients.md)

[Next → 07. Stage composition](./07-stage-composition.md)
