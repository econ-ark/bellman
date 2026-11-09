---
title: "Smooth-ambiguity savings"
audience: developer
type: model-note
topic: [applications]
---
# Smooth-ambiguity savings

A consumption–savings stage with three curvatures, written on 14 September 2026 for AMD-SG-009 §6 as the test of nested expectations under a hierarchical shock distribution. Risk aversion γ, ambiguity aversion η and the elasticity of intertemporal substitution 1/ρ are separate, as in Ju and Miao (2012); the uncertain normal mean ν of the log return and the lognormal return given ν adapt the ambiguous-mean example of Backus, Ferrière and Zin (2015). The methods file `methods.bl` beside the stage file, an addition to it, selects value function iteration on the decision value builder, Gauss–Hermite quadrature at its four expectations, the representations of the value, of its derivative and of the two certainty equivalents, and Monte Carlo draws for the forward builder; `declaration/settings/sa_savings.yml` gives the values of the settings it declares. Its two calibrations are those of AMD-SG-009 §6. The lesson [Expectations and nested aggregation](../../../../../tutorials/topics/expectations.ipynb) of the tutorials collection constructs this stage and reads its two expectations.

## Model

The household enters the decision perch with resources $m_d$ and chooses $c$ with $0 < c < m_d$, the strict feasible set `{c : ℝ₊₊ | c < x}`. Savings earn the gross return Ψ drawn after the decision, $a = (m_d - c)\,\Psi$, with $\nu \sim N(\kappa_1, \sigma_\nu^2)$ and $\Psi \mid \nu \sim \mathrm{LogNormal}(\nu, \sigma_\Psi)$. Uncertainty about ν is resolved within the period; there is no learning across periods. The forward signature lists Ψ only; ν is drawn on the same edge because Ψ's declaration names it.

## Bellman equation

$$
V(m_d) = \sup_{0<c<m_d} \Bigl( (1-\beta)\,c^{1-\rho} + \beta\,\mathrm{AMB}^{1-\rho} \Bigr)^{\frac{1}{1-\rho}},\quad
\mathrm{AMB} = \mathbb E_\nu\bigl[\mathrm{CE}^{1-\eta}\bigr]^{\frac{1}{1-\eta}},\quad
\mathrm{CE} = \mathbb E\bigl[V_\succ(a)^{1-\gamma}\mid\nu\bigr]^{\frac{1}{1-\gamma}}.
$$

CE is the risk certainty equivalent and AMB the ambiguity certainty equivalent, a certainty equivalent being the sure value that a curvature ranks equal to a random one.

## What the stage tests

The two `!node` lines give two sub-builders of `cntn_to_dcsn`, whose results have the coordinates $(m_d, c, \nu)$ and $(m_d, c)$: the first expectation uses Ψ given ν, the second the marginal of ν. At the primitive grain the root of CE and the power of AMB merge into $q \mapsto (q^{1/(1-\gamma)})^{1-\eta}$, and the box stays at η = γ. The forward view inserts the policy, extends the measure on $(m_d, c)$ by ν and then by Ψ given the same ν, and pushes the measure on $(m_d, c, ν, Ψ)$ forward through g to the measure on $a$, in which ν no longer appears. The reversed order, ν inside and Ψ outside, is refused under `conditional-not-declared`. The acceptance checks are `packages/bellman/tests/cat/test_amd_sg_009.py` items 4 to 6.
