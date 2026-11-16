---
audience: user
type: example
topic: [applications]
---
# Buffer-stock consumption

> [!note] Source
> Application folder: [`applications/buffer-stock/`](https://github.com/econ-ark/bellman/tree/main/applications/buffer-stock), which holds the model's stage file, `declaration/stages/buffer_stock/buffer_stock.bl`, beside it its methods file, `methods.bl`, an addition to the stage file, and its settings file, `declaration/settings/buffer_stock.yml`, in the layout of [Model directory layout](../../Bellman-Sym/reference/model-directory-layout.md). A related single-stage model, whose income is drawn independently each period and has no permanent component, is the application [`applications/consumption-savings-iid/`](https://github.com/econ-ark/bellman/tree/main/applications/consumption-savings-iid).

This example presents the buffer stock saving model (Carroll, 2024) in its normalized (ratio) form. Normalizing by permanent income reduces the state from two variables $(\mathbf{m}, \mathbf{P})$ to one $(m = \mathbf{m}/\mathbf{P})$, yielding a stationary single-stage problem suitable for EGM.

> [!note] Source
> Based on Carroll (2024), "Theoretical Foundations of Buffer Stock Saving," Problem $\mathscr{P}_N$.

## Model Overview

| Feature | Description |
|---------|-------------|
| **Stages** | 1 (consumption-savings with expectation and maximization) |
| **Shocks** | Permanent ($\psi$) and transitory ($\xi$), IID |
| **Solution** | Endogenous Grid Method (EGM) |
| **State** | Normalized market resources $m$ |
| **Horizon** | Infinite (stationary) |

## Bellman Equation

$$
v(m) = \max_{0 < c < m} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta \,\mathbb{E}\!\left[(\Gamma \psi')^{1-\rho}\, v\!\left(\frac{R\,(m - c)}{\Gamma \psi'} + \xi'\right)\right] \right\}
$$

subject to:

$$
\begin{aligned}
a &= m - c \\
m' &= \frac{R}{\Gamma \psi'}\, a + \xi'
\end{aligned}
$$

Variables (all normalized by permanent income $P_t$):

- $m$ = market resources
- $c$ = consumption
- $a$ = end-of-period assets
- $\psi$ = permanent income shock ($\mathbb{E}[\psi] = 1$, $\psi > 0$)
- $\xi$ = transitory income shock ($\mathbb{E}[\xi] = 1$; equals zero with probability $\wp > 0$)
- $R$ = gross interest rate
- $\Gamma$ = deterministic permanent income growth factor
- $\beta$ = discount factor
- $\rho$ = coefficient of relative risk aversion ($\rho > 1$)

The weighting factor $(\Gamma \psi)^{1-\rho}$ arises from normalizing the value function: $v(m) \;=\; \mathbf{V}(\mathbf{m}, \mathbf{P})\,/\,\mathbf{P}^{1-\rho}$.

## First-Order Conditions

**Euler equation:**

$$
c^{-\rho} = R\,\beta\,\mathbb{E}\!\left[(\Gamma \psi')^{-\rho}\, c'(m')^{-\rho}\right]
$$

**Envelope condition:**

$$
v'(m) = c(m)^{-\rho}
$$

## State-Space Diagram

```
(k) ──shocks (ψ, ξ)──▶ (m) ──c──▶ (a)
```

A single stage per period: the arrival state $k$, the assets carried from the previous period, is transformed by two shocks into market resources $m$; consumption $c$ determines the end-of-period assets $a = m - c$.

## Stage File

The stage file states the income laws, utility, feasible consumption and the forward and backward equations. The bound `L` is a constant continuation input. The policy block maximizes the stated decision value.

```bl
@stage: buffer_stock

Xm := ℝ
Xa := ℝ

β : (0,1)        :: ["discount factor"]
ρ : (1, inf)     :: ["coefficient of relative risk aversion, greater than one"]
R : ℝ₊₊          :: ["gross interest rate"]
Γ : ℝ₊₊          :: ["deterministic permanent income growth factor"]
σ_ψ : ℝ₊         :: ["standard deviation of the log permanent shock"]
σ_ξ : ℝ₊         :: ["standard deviation of the log transitory shock, conditional on a positive draw"]
p_zero : (0,1)   :: ["probability ℘ of a zero transitory draw"]
μ_ξ := -log(1 - p_zero) - σ_ξ^2/2   :: ["log-mean of the positive transitory draw, at which E[ξ] = 1"]

ψ : ℝ₊₊
ψ ~ LogNormal(-(σ_ψ^2)/2, σ_ψ)
ξ : ℝ₊
ξ ~ Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_ξ, σ_ξ)))

𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]
𝑑𝑢(c : ℝ₊₊) := c^(-ρ)               :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(v : ℝ₊₊) := v^(-1/ρ)     :: [id=inv_marg_util]

Γ_c(x : Xm) := {c : ℝ₊₊ | c < x - L}   :: [id=feasible_consumption]

[id=arvl_to_dcsn, (k : Xa, ψ, ξ) : !arvl -> (m : Xm) : !dcsn] {
    m = R*k/(Γ*ψ) + ξ               :: [id=market_resources]
}

[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m - c                       :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L : (-inf, 0] @ !vlu @ !cnst, c) : !cntn -> (V : ℝ @ !vlu, L) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V, L) : !dcsn -> (V[<] : ℝ @ !vlu, L[<] : (-inf, 0] @ !vlu @ !cnst) : !arvl] {
    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]
    L[<] = if σ_ψ > 0 then 0 else Γ*L/R :: [id=borrowing_bound]
}

[id=policy, (V[>] : ℝ @ !vlu, L) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])     :: [id=optimality]
}
```

### Arrival Transition

The arrival block `arvl_to_dcsn` writes $m = R\,k/(\Gamma\psi) + \xi$, which combines two steps from the levels problem:

1. **Bank balances**: $b = R\,k/(\Gamma\psi)$, where the denominator $\Gamma\psi$ is the realized permanent income growth factor.
2. **Market resources**: $m = b + \xi$, adding transitory income.

### Builders

- `cntn_to_dcsn`, the decision value builder: $V = u(c) + \beta V^{>}$, at the consumption the policy chooses.
- `policy`, the policy builder: the maximization of $u(c') + \beta V^{>}$ over consumption $0 < c' < m-L$, with incoming bound $L$.
- `dcsn_to_arvl`, the arrival value builder: $V^{<} = \mathbb{E}_{\psi,\xi}[(\Gamma\psi)^{1-\rho}\, V]$, the decision value read at $m = R\,k/(\Gamma\psi) + \xi$.

The stage file authors marginal utility and its inverse in closed form. It states no value derivative and no numerical method: the methods file beside it states the derivatives and selects the methods, as the next section shows.

## Methods and Settings

The methods file adds numerical choices and equations to the stage ([Methodization](../../Bellman-Sym/04-methodization.md)). It chooses the endogenous grid method, `!egm`, on `policy`. Its savings grid is `!Cartesian(a=(L + extra_grid, a_max, n_a))`.

Three policy lines state the inverted Euler equation, the inverse transition and the chosen consumption. Linear interpolation at `policy.evaluate` uses the pairs computed by those lines. It takes no separate grid.

Each value builder gains an authored derivative equation. At the decision, marginal value equals marginal utility. At arrival, the expectation has weight $R(\Gamma\psi)^{-\rho}$, from the forward transition and value normalization.

Gauss–Hermite quadrature evaluates the income expectation with one node count per shock. Linear interpolation represents the arrival value and derivative on `!Cartesian(k=(k_min, k_max, n_k))`. The eight settings declare their counts, bounds and the nonnegative offset `extra_grid`; the settings file supplies their values.

```bl
@methods: buffer_stock
# The methods of the buffer-stock stage, an addition to buffer_stock.bl, the
# stage file beside this one. The endogenous grid method stands on the policy
# builder with its exogenous grid of savings a; its three lines, the inverted
# Euler equation, the inverted law of motion and the identification of the
# chosen consumption with the candidate, stand in place of the maximization
# when the stage is solved, and the maximization remains the stage's
# statement of the choice. The consumption function is read by linear
# interpolation at the policy builder's Evaluation, between the pairs the
# method computes, and that Evaluation takes no grid of its own, since the
# pairs give its nodes. Each value builder gains its derivative line: the
# envelope condition of the decision value, and the derivative of the
# arrival value, whose weight R*(Γ*ψ)^(-ρ) inside the
# expectation comes from the law m = R*k/(Γ*ψ) + ξ and the normalization
# (Γ*ψ)^(1-ρ) of the value. At the arrival builder the expectation over the
# two income shocks is taken by Gauss-Hermite quadrature with one node count
# per shock, the point mass of the transitory shock at zero exact, and the
# arrival value and its derivative are represented together, by linear
# interpolation on the grid of assets k, named once at that builder's
# Evaluation. The settings the entries read are declared first, with their
# sets: a count in ℕ, a bound a point of Xa, the set the stage declares for
# the savings and the assets, and extra_grid in ℝ₊, the distance from the
# bound L, the field the stage takes in, to the first savings point, so that
# the savings grid starts at L + extra_grid. Their values are recorded in
# declaration/settings/buffer_stock.yml and are those of the HARK solution of
# this model in the QuantEcon community library
# (projects/HARK/buffer-stock/tutorial.ipynb, HARK 0.17.1): seven nodes per
# shock and 960 points from 0.001 to 20 for the assets and, where the bound
# L is 0, for the savings.
# HARK's seven values per shock are equiprobable conditional means and its
# grid is exponentially nested; here the rule is Gauss-Hermite and each grid
# is stated by its bounds and its count.

n_a : ℕ              :: ["number of points of the savings grid"]
extra_grid : ℝ₊     :: ["distance from the borrowing bound to the first savings point"]
a_max : Xa           :: ["upper bound of the savings grid"]
n_k : ℕ              :: ["number of points of the asset grid"]
k_min : Xa           :: ["lower bound of the asset grid"]
k_max : Xa           :: ["upper bound of the asset grid"]
n_ψ_nodes : ℕ        :: ["quadrature nodes of the permanent shock"]
n_ξ_nodes : ℕ        :: ["quadrature nodes of the transitory shock"]

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(L + extra_grid, a_max, n_a))
    | policy.evaluate.method : !Linear] {
    c[>] = (β*D_{a}V[>])^(-1/ρ)       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{m}V = 𝑑𝑢(c)                                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)
    | evaluate.method : !Linear
    | evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))] {
    D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)    :: [id=marginal]
}
```

The settings file, `declaration/settings/buffer_stock.yml`, gives the numbers of quadrature nodes of the two shocks, the exogenous grid of savings and the grid of assets:

```yaml
# The buffer-stock stage's numerical settings: the quadrature nodes of the two
# income shocks at the arrival builder's expectation, the exogenous grid of
# savings a of the endogenous grid method, and the grid of assets k on which
# the arrival value and its derivative are represented. The values are those
# of the HARK solution of this model in the QuantEcon community library
# (projects/HARK/buffer-stock/tutorial.ipynb): seven points per shock, and 960
# asset points from 0.001 to 20, one grid in that solution for savings and for
# assets.
settings:
  n_ψ_nodes: 7
  n_ξ_nodes: 7
  n_a: 960
  extra_grid: 0.001
  a_max: 20.0
  n_k: 960
  k_min: 0.001
  k_max: 20.0
```

The four construction steps are explicit. The continuation value and the bound are checked before the policy grid is constructed:

```python
from pathlib import Path
from bellman.stage import elaborate_text

application = Path("applications/buffer-stock")
path = application / "declaration/stages/buffer_stock/buffer_stock.bl"
stage = elaborate_text(path.read_text(), str(path))
methodized = stage.methodize(path.with_name("methods.bl"))
calibrated = methodized.calibrate({
    "R": 1.03, "β": 0.96, "Γ": 1.03, "ρ": 2.0,
    "σ_ψ": 0.1, "σ_ξ": 0.1, "p_zero": 0.005,
})
configured = calibrated.configure(application / "declaration/settings/buffer_stock.yml")
inputs = {"V[>]": lambda a: -1 / (1 + a), "L": 0.0}
conditions = configured.check_inputs(inputs)
policy = configured.dcsn.builder.policy.kernels(inputs=inputs)
print(configured.settings)
```

The returned conditions retain any property of the supplied value function that the package cannot decide. The callable above is an illustrative continuation value, not a solved stationary value.

```text
name        set  value  read at                by              grid
n_a         ℕ    960    policy                 !egm            !Cartesian
extra_grid  ℝ₊   0.001  policy                 !egm            !Cartesian
a_max       Xa   20.0   policy                 !egm            !Cartesian
n_k         ℕ    960    dcsn_to_arvl.evaluate  !Linear         !Cartesian
k_min       Xa   0.001  dcsn_to_arvl.evaluate  !Linear         !Cartesian
k_max       Xa   20.0   dcsn_to_arvl.evaluate  !Linear         !Cartesian
n_ψ_nodes   ℕ    7      dcsn_to_arvl.E_ψ_ξ     !gauss_hermite
n_ξ_nodes   ℕ    7      dcsn_to_arvl.E_ψ_ξ     !gauss_hermite
```

## Period and trellis

Each repeated period holds the same stage declaration and calibration sources. The inter-period connector joins the end-of-period assets $a$ to the next period's arrival assets $k$; the resulting trellis is a diagram of periods joined by connections. A stationary solution requires every backward field at its fixed point, including the bound `L` as well as the value field. The user supplies terminal data for a finite recursion when realizing it. The application holds no recipe and no trellis file; [Trellises](../../Bellman-Sym/07-trellis.md) states how a trellis is written.

## Endogenous grid method

The Endogenous Grid Method solves this model by inverting the Euler equation:

1. **Start** with continuation marginal value $dV^{>}(a)$ on an exogenous grid of end-of-period assets $\{a_1, \dots, a_n\}$.
2. **Expectation** (the derivative line of `dcsn_to_arvl`): $dV^{<}(a_i) = R\,\mathbb{E}_{\psi,\xi}[(\Gamma\psi)^{-\rho}\, dV(Ra_i/(\Gamma\psi) + \xi)]$.
3. **InvEuler**: $c_i = (\beta \cdot dV^{<}(a_i))^{-1/\rho}$.
4. **Endogenous grid** (`g_cntn_to_dcsn`): $m_i = a_i + c_i$.
5. **Envelope** (the derivative line of `cntn_to_dcsn`): $dV_i = c_i^{-\rho}$.
6. **Iterate** until convergence.

The normalization weight $(\Gamma\psi)^{-\rho}$ in the marginal-value expectation (step 2) is the key difference from a model without permanent income growth.

## Calibration (Baseline)

The application holds no calibration file. A baseline calibration takes `R` = 1.03, `β` = 0.96, `Γ` = 1.03, `ρ` = 2, `σ_ψ` = 0.1, `σ_ξ` = 0.1 and `p_zero` = 0.005. The numerical settings are those of the settings file above.

The log-mean of the positive transitory draw, `μ_ξ := -log(1 - p_zero) - σ_ξ^2/2`, is a derived parameter: a constant that the stage file defines from its parameters with `:=`, which takes the value of that definition at each calibration. The calibration supplies no value for it, and a calibration that does is refused under [`derived-parameter`](../../Bellman-Sym/reference/refusals.md#derived-parameter). The definition makes the mean of the transitory draw one at every calibration, since the positive draw, `LogNormal(μ_ξ, σ_ξ)`, has mean $\exp(\mu_\xi + \sigma_\xi^2/2)$:

$$
\mathbb{E}[\xi] = \wp \cdot 0 + (1 - \wp)\, \exp\!\left(\mu_\xi + \tfrac{\sigma_\xi^2}{2}\right) = (1 - \wp)\, \exp\!\left(-\log(1 - \wp)\right) = 1 .
$$

At $\sigma_\xi = 0$ the positive draw is the point mass at $\exp(\mu_\xi) = 1/(1 - \wp)$, and the declared set $(0, 1)$ of `p_zero` keeps that point finite. `stage.par` lists the derived parameter after the declared ones, with its definition and, once the stage is calibrated, its value:

```python
calibrated = stage.calibrate({"R": 1.03, "β": 0.96, "Γ": 1.03, "ρ": 2.0, "σ_ψ": 0.1, "σ_ξ": 0.1, "p_zero": 0.005})
print(calibrated.par)
```

```text
name    set                         value                   describes
β       (0, 1)                      0.96                    discount factor
ρ       (1, inf)                    2.0                     coefficient of relative risk aversion, greater than one
R       ℝ₊₊                         1.03                    gross interest rate
Γ       ℝ₊₊                         1.03                    deterministic permanent income growth factor
σ_ψ     ℝ₊                          0.1                     standard deviation of the log permanent shock
σ_ξ     ℝ₊                          0.1                     standard deviation of the log transitory shock, conditional on a positive draw
p_zero  (0, 1)                      0.005                   probability ℘ of a zero transitory draw
μ_ξ     -log(1 - p_zero) - σ_ξ^2/2  1.2541823544285312e-05  log-mean of the positive transitory draw, at which E[ξ] = 1
```

## Key Features

### Permanent Income Normalization

Dividing by $P_t$ (for quantities) and $P_t^{1-\rho}$ (for the value function) eliminates the permanent income state. The cost is a growth-adjusted arrival transition and a normalization weight $(\Gamma\psi)^{1-\rho}$ inside the expectation operator.

### Natural Borrowing Constraint

The transitory shock $\xi$ has a point mass at zero (probability $\wp > 0$): the agent may receive zero income. With terminal bound $L=0$, the backward transition preserves that bound, so positive consumption requires assets strictly above zero. The stage takes the bound as a constant field and writes feasibility as $0<c<m-L$. The declared state sets are ℝ; the bound restricts the admissible resources and assets.

### Weighted Expectations in the Arrival Builder

The arrival builder `dcsn_to_arvl` writes the value, and its derivative line in the methods file states its derivative, each as a $(\Gamma\psi)$-weighted expectation. This weight is an artifact of the normalization, not an economic primitive: in the levels problem, the arrival builder would be a plain expectation $V^{<} = \mathbb{E}[V]$.

## Borrowing-bound check

For an incoming bound $L \le 0$, the arrival bound is the supremum of $\Gamma\psi(L-\xi)/R$ over the support of the authored income laws. If $\sigma_\psi>0$, positive permanent shocks approach zero and this supremum is zero. If $\sigma_\psi=0$, the permanent shock equals one and the zero transitory draw gives $\Gamma L/R$. The stage states these two cases explicitly.

At `L = 0`, the default `extra_grid = 0.001` preserves all 960 original savings points. With `extra_grid = 0`, the first point is zero. The power written in the Euler line maps an infinite marginal value to consumption zero. Infinity arithmetic applies to block lines; the named inverse marginal utility retains its finite positive domain. The inverse transition gives resources zero. This point is an interpolation endpoint; it is not an admissible positive-consumption choice.

The executed notebook `applications/buffer-stock/notebooks/borrowing-bound.ipynb` shows the four construction steps, the retained input conditions, both bound cases, and the endpoint calculation. It leaves space for the reader's observations.
