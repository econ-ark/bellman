---
audience: user
type: example
topic: [applications]
---
# Smooth-ambiguity savings

> [!summary]
> The household chooses consumption under uncertainty about the mean of its log return. Risk aversion, ambiguity aversion and the elasticity of intertemporal substitution are separate parameters. Two nested certainty equivalents—the sure continuation values the household regards as equivalent to the uncertain ones—distinguish return risk from uncertainty about its mean.

> [!info]- Relationship with other documents
> The separation of the three curvatures follows Ju and Miao (2012). The uncertain normal mean of the log return and the lognormal return given that mean adapt the ambiguous-mean example of Backus, Ferrière and Zin (2015). The stage file is `applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl`; beside it stands its methods file, `methods.bl`, an addition to the stage file, and `declaration/settings/sa_savings.yml` gives the values of the settings that file declares. The rules the stage file relies on are in [Appendix C](../../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md), R7.

## 1 The model

The household begins its decision with resources $m_d > 0$ and chooses consumption $c$ in the open interval $(0, m_d)$. Savings $m_d - c$ earn a gross return $\Psi$, so the continuation state is $a = (m_d - c)\,\Psi$. The log return is normal with an uncertain mean $\nu$:

$$
\nu \sim N(\kappa_1, \sigma_\nu^2), \qquad \log \Psi \mid \nu \sim N(\nu, \sigma_\Psi^2).
$$

Both shocks are drawn after the decision. Uncertainty is resolved within the period, and there is no learning about $\nu$ across periods.

## 2 Bellman equation

With $\beta \in (0, 1)$ the discount factor, $1/\rho$ the elasticity of intertemporal substitution, $\gamma$ relative risk aversion and $\eta$ ambiguity aversion,

$$
V(m_d) = \sup_{0 < c < m_d} \Bigl( (1-\beta)\, c^{1-\rho} + \beta\, \mathrm{AMB}(m_d, c)^{1-\rho} \Bigr)^{\frac{1}{1-\rho}},
$$

$$
\mathrm{CE}(m_d, c, \nu) = \Bigl( \mathbb E\bigl[ V_\succ(a)^{1-\gamma} \mid \nu \bigr] \Bigr)^{\frac{1}{1-\gamma}}, \qquad
\mathrm{AMB}(m_d, c) = \Bigl( \mathbb E_\nu\bigl[ \mathrm{CE}(m_d, c, \nu)^{1-\eta} \bigr] \Bigr)^{\frac{1}{1-\eta}} .
$$

The inner certainty equivalent CE evaluates return risk conditional on its mean; the outer one AMB evaluates uncertainty about the mean. When $\eta = \gamma$ the two powers cancel and the recursion is Epstein–Zin under the predictive distribution of the return. When $\eta > \gamma$ the household dislikes uncertainty about the mean more than risk.

## 3 The stage file

The stage file is `applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl`:

```bl
@stage: sa_savings

β : (0,1) :: ["discount factor"]
ρ : (1,inf) :: ["1/ρ is the elasticity of intertemporal substitution"]
γ : (1,inf) :: ["relative risk aversion"]
η : (1,inf), > γ :: ["ambiguity aversion"]
κ_1 : ℝ
σ_ν : ℝ₊
σ_Ψ : ℝ₊

ν : ℝ
ν ~ N(κ_1, σ_ν^2)
Ψ : ℝ₊₊
Ψ ~ LogNormal(ν, σ_Ψ)

Γ(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}

[id=dcsn_to_cntn, (m_d : ℝ₊₊, c : !ctrl @ ℝ₊₊, Ψ) : !dcsn -> (a : ℝ₊₊) : !cntn] {
    a = (m_d - c)*Ψ :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ₊₊ @ !vlu, c) : !cntn -> (V : ℝ₊₊ @ !vlu) : !dcsn] {
    CE = E_{Ψ}(V[>]^(1-γ))^(1/(1-γ)) :: [id=risk_ce, !node]
    AMB = E_{ν}(CE^(1-η))^(1/(1-η)) :: [id=ambiguity_ce, !node]
    V = ((1-β)*c^(1-ρ) + β*AMB^(1-ρ))^(1/(1-ρ)) :: [id=value]
}

[id=policy, (V[>]) : !cntn -> c] {
    c = argmax_{c : Γ(m_d)}(((1-β)*c^(1-ρ) + β*E_{ν}(E_{Ψ}(V[>]^(1-γ))^((1-η)/(1-γ)))^((1-ρ)/(1-η)))^(1/(1-ρ))) :: [id=objective]
}
```

`N(κ_1, σ_ν^2)` is written with its variance and `LogNormal(ν, σ_Ψ)` with the standard deviation of the logarithm. The declaration of `η` adds the condition `> γ`: ambiguity aversion exceeds risk aversion, the case $\eta > \gamma$ of §2. The feasible set `{c : ℝ₊₊ | c < x}` is open at both ends: at $c = m_d$ the continuation state is zero and its negative powers are undefined. Each group of equations between braces is a **block**, and its **header**, the bracketed list before the braces, names its inputs and outputs. The header of the forward block `dcsn_to_cntn` names only the shock the law of motion reads, `Ψ`; the mean `ν` is drawn on the same edge because the declaration of `Ψ` names it.

## 4 What elaboration constructs

Elaboration, `elaborate_stage(load_stage(path))` for the file at `path`, with both functions imported from `bellman.stage`, constructs the [stage object](../../wiki/elaborated_stage.md) from the stage file. The block `cntn_to_dcsn` denotes the [backward builder](../../wiki/backward_builder.md) that constructs the value at the decision [perch](../../wiki/perch.md), the information set at which the household chooses, reached as `stage.dcsn.builder.bwd`. The builder is stated at a policy $c$, a consumption function of $m_d$ with values in the feasible set, and $c$ is not an argument of the functions below. Each builder and each of its operations answers `denote()` with its **card**, a printed statement of what it denotes; the builder's card, `stage.dcsn.builder.bwd.denote()`, names the policy under the heading `At`.

The two `!node` statements define two [sub-builders](../../wiki/sub_builder.md), named groups of operations within that builder. The first composes $V_\succ$ with the law of motion at the policy, raises it to $1-\gamma$, integrates $\Psi$ under its declared distribution given $\nu$ and takes the root, so CE is a function of $(m_d, \nu)$. The second raises CE to $1-\eta$, integrates $\nu$ under its own distribution and takes the root, so AMB is a function of $m_d$. The last [aggregation](../../wiki/aggregation.md) applies the aggregator of the first equation of §2 at the policy. The last operation of each sub-builder and of the builder is an evaluation, the identity map from the function computed into the set of functions its card prints: `𝐶𝐸 : ℝ₊₊ × ℝ → ℝ₊₊`, `𝐴𝑀𝐵 : ℝ₊₊ → ℝ₊₊` and, for $V$, the set the file declares, the functions from $\mathbb R_{++}$ to $\mathbb R_{++}$. `stage.dcsn.builder.bwd.list()` prints the builder's operations in the order of application, each a primitive operator, a step the construction does not divide further, with the name of each sub-builder above its operations:

```text
    risk_ce          sub-builder  → 𝐶𝐸(m_d, ν)
 1    Pullback       primitive
 2    Aggregation:1  primitive
 3    Expectation:1  primitive
 4    Aggregation    primitive
 5    Evaluation     primitive    → 𝐶𝐸
    ambiguity_ce     sub-builder  → 𝐴𝑀𝐵(m_d)
 6    Aggregation:1  primitive
 7    Expectation:1  primitive
 8    Aggregation    primitive
 9    Evaluation     primitive    → 𝐴𝑀𝐵
10  Aggregation      primitive    → 𝑉
11  Evaluation       primitive    → 𝑉
```

The card of an operation names under `Source` the lines of the file it comes from, and for an expectation these include the line that declares the distribution it integrates. The card of the expectation over $\Psi$, `stage.dcsn.builder.bwd.primitives["risk_ce:Expectation:1"].denote()`, prints its rule and its sources as:

```text
Rule
  risk_ce:Expectation:1(m_d, ν) = E_{Ψ}[risk_ce:Aggregation:1(m_d, Ψ)]
──────────────────────────────────────────────────────────────────────────────
Source  sa_savings.bl
  14  Ψ ~ LogNormal(ν, σ_Ψ)
  27  CE = E_{Ψ}(V[>]^(1-γ))^(1/(1-γ))  :: [id=risk_ce, !node]
```

The card of the expectation over $\nu$, `ambiguity_ce:Expectation:1`, cites line 12, `ν ~ N(κ_1, σ_ν^2)`, and integrates at each $m_d$.

The [forward builder](../../wiki/forward_builder.md) from the decision perch, `stage.dcsn.builder.fwd`, extends the measure on the decision state $m_d$ first by the distribution of $\nu$ and then by the distribution of $\Psi$ given the same $\nu$, and pushes the measure on $(m_d, \nu, \Psi)$ forward through the law of motion at the policy, $(m_d, \nu, \Psi) \mapsto (m_d - c(m_d))\,\Psi$, to a measure on $a$, in which $\nu$ no longer appears.

Writing the expectations in the reverse order, $\nu$ inside and $\Psi$ outside, would need the distribution of $\nu$ given $\Psi$, which the file does not declare; the elaboration refuses the file under the rule [`conditional-not-declared`](../../Bellman-Sym/reference/refusals.md#conditional-not-declared).

## 5 Closed-form checks

With continuation value $v(a) = a$ and $s = m_d - c$, the lognormal moments give

$$
\mathrm{CE} = s\, e^{\nu + (1-\gamma)\sigma_\Psi^2/2}, \qquad
\mathrm{AMB} = s\, e^{\kappa_1 + (1-\eta)\sigma_\nu^2/2 + (1-\gamma)\sigma_\Psi^2/2}.
$$

Under the predictive distribution of the return the Epstein–Zin certainty equivalent is $s\, e^{\kappa_1 + (1-\gamma)(\sigma_\nu^2 + \sigma_\Psi^2)/2}$, so the ratio of AMB to it is $e^{(\gamma-\eta)\sigma_\nu^2/2}$. The ratio is one when $\eta = \gamma$ or $\sigma_\nu = 0$, and below one when $\eta > \gamma$ and $\sigma_\nu > 0$. At $\beta = 0.96$, $\rho = 2$, $\gamma = 5$, $\eta = 8$, $\kappa_1 = 0.02$, $\sigma_\nu = 0.05$ and $\sigma_\Psi = 0.15$ it is approximately 0.996257. The package's tests compare these values with the compiled kernels of the builder's pullback and aggregations, the plain Python functions that `compile_kernel()` makes from each operation's pointwise map, given the two expectations as analytic inputs. Those tests do not compute an integral, optimize the policy or solve the Bellman equation.

## 6 References

- Backus, D., A. Ferrière and S. Zin (2015). "Risk and ambiguity in models of business cycles." *Journal of Monetary Economics*. doi:10.1016/j.jmoneco.2014.12.005. The nested certainty equivalents are equation (19) of the August 2014 author draft, and the ambiguous-mean example follows it on pp. 17–18 of that draft; the draft's random mean $s_2$ is $\nu$ here, and its variance parameters $\kappa_2$ and $\nu$ are $\sigma_\Psi^2$ and $\sigma_\nu^2$.
- Ju, N. and J. Miao (2012). "Ambiguity, learning, and asset returns." *Econometrica*. doi:10.3982/ECTA7618.
