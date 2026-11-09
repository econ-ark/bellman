---
audience: user
type: example
topic: [applications]
---
# Examples

The examples below include individual stages and applications that compose several stages into periods. A stage is one decision episode, with its arrival state, shocks, transitions, constraints and preferences. An application specifies one or more stage occurrences, each a stage file placed at one position of a [period](../wiki/period.md), and the [connectors](../wiki/connector.md) that join them by identifying or renaming the quantities one stage passes to the next.

Each stage is structured around three **perches** — information sets at which the agent's state is observed:

- **Arrival** — the agent enters with the states of the arrival perch (e.g., beginning-of-period assets before shocks resolve).
- **Decision** — shocks have resolved; the agent observes states and chooses controls.
- **Continuation** — the decision has been made; the states of the continuation perch (e.g., end-of-period savings) carry forward.

Current stages are authored in `.bl` stage files. Application files place those stages in periods and supply their calibration, settings and methods. Several pages in this directory record the earlier dolo-plus YAML design; they remain as historical examples and do not state the current source format.

The table therefore distinguishes three kinds of source page:

- **Stage** describes one current `.bl` stage file.
- **Application** describes a composition of stage occurrences.
- **Historical YAML** preserves an earlier source design for reference.

The formal MDP pages state selected examples as Markov decision processes (MDPs) in mathematical notation. They are not generated round trips from the historical YAML pages. See also the [Concept wiki](../wiki/index.md) for one-page definitions of stages, perches and builders.

## Model files

- [Model directory layout](../Bellman-Sym/reference/model-directory-layout.md) — the files of a current model, its `.bl` stage files and the YAML files beside them, and where each is kept.

## Examples

| Model | Description | Stages | Source page | Formal MDP |
|:------|:-----------|:-------|:------------|:-----------|
| **Consumption-Savings IID** | Single-stage consumption choice with IID income shock, solved by the endogenous grid method (EGM) | 1 | [Historical YAML](cons-iid/consumption_savings_iid.md) | [MDP](formal-mdps/cons_savings_iid_mdp.md) |
| **Buffer Stock (Normalized)** | Carroll (2024) buffer stock model normalized by permanent income; permanent and transitory shocks with unemployment risk | 1 | [Stage](buffer-stock/buffer_stock.md) | — |
| **Housing adjustment** | Keep or adjust housing, followed by consumption and saving; adjustment also chooses the new housing stock | 3 + terminal | [Application](housing-frictions/index.md) | — |
| **Pensions and retirement** | Consumption and pension contributions precede the choice of whether to retire next period | 3 + terminal | [Application](pension-retirement/index.md) | — |
| **Housing Owner** | Two-stage discrete housing choice + continuous consumption; branching stage | 2 | [Historical YAML](housing_renting/housing_owner.md) | [housing](housing_renting/housing_choice_mdp.md), [cons](housing_renting/housing_cons_choice_mdp.md) |
| **Retirement Choice (DCEGM)** | Branching model with discrete retirement decision and continuous consumption; EGM for discrete-continuous choice (DC-EGM) with the fast upper envelope scan (FUES) | 3 | [Application](retirement/retirement_choice.md) | — |
| **Smooth-Ambiguity Savings** | Savings with an uncertain mean log return: risk aversion, ambiguity aversion and intertemporal substitution are separate parameters, with two nested certainty equivalents | 1 | [Stage](smooth-ambiguity/smooth_ambiguity_savings.md) | — |
| **Unemployment Branching Portfolio-Consumption** | Exogenous employment branching into worker and unemployed portfolio stages with fan-in to a shared consumption stage | 4 | [Historical YAML](unemployment/index.md) | [MDP](unemployment_branching_mdp.md) |

### Portfolio-consumption stages

The portfolio-consumption family illustrates the core idea of Bellman calculus: the same stage building blocks compose into [four period configurations](cons-port-stages/port_with_shocks.md), each a valid economic model. Only the wiring changes.

| Stage | Description | Historical source page | Formal MDP |
|:------|:-----------|:-----------------------|:-----------|
| **cons_stage** | Deterministic consumption choice (EGM-compatible) | [Historical YAML](cons-port-stages/cons_stage.md) | [MDP](formal-mdps/cons_stage_mdp.md) |
| **port_stage** | Portfolio allocation with correlated shocks | [Historical YAML](cons-port-stages/port_stage.md) | [MDP](port_stage_mdp.md) |
| **noport_stage** | No-portfolio-choice income stage | [Historical YAML](cons-port-stages/noport_stage.md) | [MDP](noport_stage_mdp.md) |

See also: [Solving via conjugation](cons-port-stages/solving-conjugates.md) — how semi-conjugacy relates the four period configurations.

## Notebooks

| Notebook | Description |
|:---------|:-----------|
| the lesson `tutorials/models/cons-port/03-solving-the-two-orders.ipynb` of the repository | The portfolio–consumption model solved in both orders of its stages, with a method chosen for each stage, and one order's value recovered from the other's |
