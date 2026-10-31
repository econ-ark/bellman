---
audience: user
type: example
topic: [applications]
---
# Matsya Prompt: Unemployment Branching Variant Of The `cons-port` Model

Start from the existing `cons-port` example in `explore/cons-port/port-cons` and the canonical stage YAMLs in `packages/dolo/examples/models/doloplus/port-with-shocks/library/`.

I want a branching unemployment variant of that model with the following within-period graph:

```text
employment_status  -> worker_port      -> cons_stage
employment_status  -> unemployed_port  -> cons_stage
```

Interpret this as an **exogenous employment-status branch**, not an agent choice:

- `employment_status` should be a `kind: branching` stage with `branch_control: nature`.
- The branch labels should be `worker` and `unemployed`.
- The branch sends the agent into a worker-specific portfolio stage or an unemployed-specific portfolio stage.

## Economic Intent

- Begin from the standard `port_stage -> cons_stage` logic.
- The `worker_port` branch is the employed version of the portfolio stage.
- The `unemployed_port` branch has **no labour income**.
- There is also a difference in the perceived portfolio return distribution across employment states.
- For now, keep that unemployment-side difference simple: use a **single placeholder return shock** for `unemployed_port`, calibrated so its mean and variance match the worker branch's portfolio-risk object as a first-pass approximation.
- After the branch-specific portfolio stage, both paths should feed a **common consumption stage** `cons_stage` that takes cash-on-hand `m` and outputs end-of-period assets `a`.

## What I Need

Please produce the following:

1. A clean **problem-level MDP writeup** in standard dynamic-programming language.
2. A **stage-by-stage decomposition** for:
   - `employment_status`
   - `worker_port`
   - `unemployed_port`
   - `cons_stage`
3. Strict **dolo-plus YAML** for those stages.
4. If the shared downstream `cons_stage` creates a fan-in / recombination issue under the current branching spec, then:
   - explain the issue clearly,
   - keep the stage YAMLs branch-safe with disjoint poststate names where needed,
   - and add the lightest valid **period-level wiring** needed to make the recombination explicit, using `connectors` for intra-period renames and `inter_connectors` for inter-period renames where appropriate.
5. Minimal **calibration / settings / methodization** scaffolding only if needed to make the example coherent. Prefer **stage-local** methodization files if that is more consistent with the current dev-specs.

## Syntax And Spec Constraints

- Use **strict dolo-plus stage YAML**, not generic YAML and not plain legacy dolo YAML.
- Use the canonical top-level groups under `symbols:`:
  - `spaces`
  - `prestate`
  - `states`
  - `poststates`
  - `controls`
  - `exogenous`
  - `values`
  - `values_marginal` when needed
  - `parameters`
- Use the canonical equation blocks:
  - `arvl_to_dcsn_transition`
  - `dcsn_to_cntn_transition`
  - `cntn_to_dcsn_builder`
  - `dcsn_to_arvl_builder`
- Use perch tags canonically:
  - arrival: `[<]`
  - decision: unmarked
  - continuation: `[>]`
- Keep branch poststates **disjoint** on the branching stage.
- Prefer a common `cons_stage` if that can be represented cleanly; otherwise, make the recombination explicit rather than silently relying on ambiguous implicit fan-in.
- Use canonical repo terminology:
  - `dolo-plus`
  - `stage`
  - `period`
  - `connector`
  - `branch_control`
  - `Bellman operator`

## Output Format

Please answer in this order:

1. **Assumptions you are making**
2. **Problem-level Bellman / MDP**
3. **Stage decomposition**
4. **Stage YAMLs**
5. **Period wiring / recombination**
6. **Open issues / ambiguities**

Be concrete and repo-compatible. Do not hand-wave the recombination step.