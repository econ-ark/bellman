<!-- notebook cell 23 | id: 8lyu33cq0hc -->

### De-sugaring: from stage YAML to solver expressions

We have bound every stage through the syntactic pipeline (parse → methodize → configure → calibrate). The next step is to cross from the **syntax layer** into the **computational layer** — building callable operators that a solver can apply.

Bellman calculus and `dolo-plus` define the syntax layer: perch-tagged equations, transition blocks, Bellman/Euler conditions. But the syntax says nothing about *how* to build a solver. That is the job of the **whisperer** — solver-specific code that reads stage syntax and constructs executable operators. In this notebook, our whisperer is `ffp_utils.py`.

To build its operators, the whisperer needs to translate the stage YAML's perch-tagged equations into plain Python expressions it can `eval` at solve time. Three things happen in this translation:

1. **Perch tags → Python names.** The YAML uses perch-tagged value functions — `V[>]` (continuation value) and `dV[>]` (continuation marginal value) — which are abstract functions on the continuation space. The whisperer maps these to callable Python objects with its own naming convention: `V_cont(·)` and `dV_cont(·)`. These names are a convention of *this* whisperer, not a `dolo-plus` requirement.

2. **Bare symbols → evaluated expressions.** The YAML writes `dV[>]` as a bare symbol (a function); the whisperer evaluates it at a concrete grid point, e.g. `dV_cont(a)` where `a` is the poststate grid array.

3. **$\beta$ is stripped.** The YAML declares `c[>] = (\beta \cdot \mathrm{dV}[\succ])^{-1/\rho}` with $\beta$ present. The whisperer deliberately drops $\beta$ because the disc stage handles discounting separately — keeping the consumption operator $\beta$-free and reusable across configurations. Similarly, `u` in the Bellman equation `V = \max_c\{u + \beta \, V[\succ]\}` is expanded into its explicit form `(c**(1-rho))/(1-rho)`.

For example:

| Stage YAML (syntax layer) | Whisperer expression (computational layer) | Key |
|---|---|---|
| $c[\succ] = (\beta \, \mathrm{dV}[\succ])^{-1/\rho}$ | `(dV_cont(a))**(-1/rho)` | `inv_euler` |
| $V = \max_c\{u + \beta \, V[\succ]\}$ | `(c**(1-rho))/(1-rho) + V_cont(a)` | `vfi_maximand` |
| $a = m_d - c$ | `m_d - c` | `dcsn_to_cntn_transition` |

The result is a plain dict mapping equation roles to expression strings. The operator factories in `ffp_utils` (`make_egm_cons_operator`, `make_vfi_cons_operator`) `eval` these expressions against concrete arrays (grid values, policy arrays) at each backward step.

This translation can be done by hand (the `FALLBACK_RECIPE` hardcoded in `ffp_utils` — a hand-verified set of expressions), or by Matsya — which reads the stage YAML, applies $\Upsilon$, and returns the expressions as JSON. Either way, the output is the same dict of strings; the only difference is whether a human or an LLM did the translation. This entire de-sugaring step is a whisperer concern — it is not part of Bellman calculus or `dolo-plus`.
