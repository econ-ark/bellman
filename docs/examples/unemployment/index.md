---
audience: user
type: example
topic: [applications]
---
# Unemployment Branching Portfolio-Consumption

> [!note] Source reconcile (2026-05-23)
> This prose describes a **cons-port-based branching sketch** aligned with the
> port-with-shocks stage library. The canonical branching registry was
> `applications/unemployment-branching/registry/` (dolo-plus multi-stage layout),
> which is no longer in the repository; no stage file of this model stands
> under `applications/`.

A branching variant of the `port-with-shocks` example in which employment status is realized first, portfolio choice is branch-specific, and both branches fan in to a shared consumption stage.

> [!note]
> This example uses `branch_control: nature`, so the branching stage is a weighted-sum builder rather than a discrete choice.
> It also uses allowed fan-in at the arrival perch: both portfolio branches produce the common cash-on-hand quantity `m`, which is then consumed by the shared `cons_stage`.

## Stage graph

```text
employment_status -> worker_port      -> cons_stage
employment_status -> unemployed_port  -> cons_stage
```

## Model

The agent enters the period with investable assets `k`. With probability `p_e` the employed branch is realized and the agent solves `worker_port`, choosing risky share `ς` before the joint shocks `(Ψ_w, θ_w)` realize. With probability `1-p_e` the unemployed branch is realized and the agent solves `unemployed_port`, choosing risky share `ς` before a single placeholder return shock `Ψ_u` realizes. In both branches the continuation quantity is cash-on-hand `m`, so the period then fans in to a common `cons_stage` where the agent chooses `c` and carries assets `a = m - c` forward.

The unemployed branch is intentionally simple: it removes labour income and replaces the worker branch's richer post-decision shock structure with a single return shock whose first two moments are matched to the worker branch as a first-pass approximation.

In the syntax-semantic reading, each stage is interpreted as implicit transition maps $\mathrm{g}_{\prec\sim}$ and $\mathrm{g}_{\sim\succ}$ together with backward builders on the perch value objects $\mathrm{v}_{\prec}$, $\mathrm{v}$, and $\mathrm{v}_{\succ}$. The formal MDP page uses that notation explicitly.

## Stage library

| Stage | Role | Mapping |
|---|---|---|
| `employment_status` | exogenous branching stage | `k -> {k_w, k_u}` |
| `worker_port` | employed portfolio choice | `k_w -> m` |
| `unemployed_port` | unemployed portfolio choice | `k_u -> m` |
| `cons_stage` | common consumption stage | `m -> a` |

The source YAMLs were in the folder `unemployment_branching_doloplus/stages/` of the earlier dolo-plus design; the folder is no longer in the repository.

Method attachments are stage-local, matching the current `docs/Bellman-Sym` direction that methodization/configuration/calibration attach to stage objects rather than to a separate period-level branching artifact.

## Period

```yaml
name: unemployment_port_period

stages:
  - employment_status: !stage
  - worker_port: !stage
  - unemployed_port: !stage
  - cons_stage: !stage
```

No intra-period connector is needed here. `worker_port` and `unemployed_port` both expose the same continuation field `m`, which matches the arrival field of `cons_stage`, so the fan-in is an identity composition on a common arrival space. The inter-period connector is the usual rename `{a: k}`, i.e. $\tau : a \mapsto k$ in the formal notation.

## Files

```text
unemployment_branching_doloplus/
├── stages/
│   ├── employment_status.yaml
│   ├── employment_status_methods.yml
│   ├── worker_port.yaml
│   ├── worker_port_methods.yml
│   ├── unemployed_port.yaml
│   ├── unemployed_port_methods.yml
│   ├── cons_stage.yaml
│   └── cons_stage_methods.yml
├── period.yaml
├── trellis.yaml
├── calibration.yaml
└── settings.yaml
```

## Formal problem

See [Formal MDP](unemployment_branching_mdp.md) for the problem-level perch-value Bellman factorization and the stage decomposition.
