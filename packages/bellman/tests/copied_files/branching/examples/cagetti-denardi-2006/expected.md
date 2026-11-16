# The example on paper: `applications/cagetti-denardi-2006/` under the first and second builds of branching

23 September 2026. Written from the ten stage files of `applications/cagetti-denardi-2006/`, its `declaration/period.yml`, `declaration/trellis.yml`, `economics.md`, `declaration/calibration/cagetti-denardi-2006.yml`, `declaration/settings/cagetti-denardi-2006.yml` and methods files, under [branching-unified.md](../../branching-unified.md) (the unification, whose §4 the E-numbers cite) and in the form of [example-tenure.md](../../example-tenure.md) (the durables example), which this page cites where it settles a point. The probes are the Python files of [probes/](probes/), run at commit 4d976498e from the repository root, each with its output beside it (`probes/*.out`). Every card, join, order and drawing below that the package prints today is the package's output; the rest is on paper and says so. A card is the printed statement of one [[builder]] of a [[stage]] (AMD-SG-034 §1); a [[perch]] is one of a stage's three information sets, marked ≺ for arrival and ≻ for continuation, the decision perch unmarked; a [[connector]] identifies a continuation field of one stage with an arrival field of another and computes nothing.

## 0 The trellis, its length and the registry

**n = 3.** The model is stationary: "The stationary model of Cagetti and De Nardi (2006) repeats one period. A trellis of H years has H copies of the period below" (`applications/cagetti-denardi-2006/declaration/trellis.yml:2-4`), and the paper's value functions are "the fixed point of the year's backward operator" (`economics.md:135`). No file states H; the one length the folder has elaborated is "two years long" (`economics.md:187`). This example takes n = 3, the smallest trellis in which both patterns of inter-period join occur, into the terminal period (h = 0) and between two periods of the template (h = 1), and in which `draw_trellis(trellis, periods=[0, 1, n − 1])` draws three distinct periods. Every larger n adds copies of the second pattern (§6), and the `repeat` count of [registry/trellis.yml](registry/trellis.yml) is the one number to change.

**The registry** is [registry/](registry/), arranged as `applications/durables/` is (AMD-FAC-002 §5 and F15). Each edit, with the rule that asks for it:

| File | Edit | Rule |
|---|---|---|
| `stages/` the ten stage files | none; each is byte-identical to the application's (digests compared when copied) | §2 item 1 names `young_choice.bl` and `old_choice.bl` as conforming; §2 item 2 fixes the four demographic files' form, "so the four files need no change"; §2 item 1 and E14 leave `young_entrepreneur.bl` and `old_entrepreneur.bl` to wait |
| `stages/terminal_worker.bl`, `terminal_young_entrepreneur.bl`, `terminal_old_entrepreneur.bl`, `terminal_retiree.bl` | new: one terminal stage for each household whose problem ends the year, in the pattern of `applications/durables/declaration/stages/bequest/bequest.bl`: the household's end-of-year fields as arrival fields, an identity `arvl_to_dcsn`, `V = V[>]` with `V[>]` the terminal boundary data, zero, and `V[<] = V` | R12 and A33 (the terminal value is a stage, its `V[>]` declared); E15 (the arrival names renamed, the tags `tw`, `ty`, `to` and `tr` in place of the `wa`, `ea`, `ed` and `rd` of the stages they stand for; the spelling is [open: E15, AAS's spelling]) |
| `period.yml` | none | E15: the template lists the ten stages and never listed a terminal stage |
| `trellis.yml` | rewritten: the terminal period written out with fourteen stages and thirteen connectors, the twelve of `period.yml` and one flat connector to the terminal stages; then `{template: period.yml, repeat: 2}`; the application's one inter-period mapping, standing for both pairs | E15 and A38 (the terminal connector in the terminal period's own entry, since a connector to a stage absent from a period is refused); D15 (`periods[0]` terminal); E16, E25 |
| `spec.yml` | new: for each of the ten stages the three source lists, with the slot `$fill` in the calibration and settings lists and one methods slot per stage; the four terminal stages `{periods: [0, 0]}`; the `registry` block | AMD-FAC-002 §5; A55 |
| `calibration/cagetti_denardi.yml` | `declaration/calibration/cagetti-denardi-2006.yml` less `α` and `A`, two words of its comments in American spelling | AMD-FAC-002 §5; F15's split of the durables calibration |
| `calibration/corporate_sector.yml` | `α` and `A`, the two names no stage declares | the `registry` block of AMD-FAC-002 §5 |
| `settings/cagetti_denardi.yml`, `methods/*_methods.yml` | moved; content unchanged | F15 |

An entry of a trellis file that writes `connectors` replaces the template's (`packages/bellman/bellman/bindings/loading.py:112`), so the terminal entry writes the twelve connectors of `period.yml` again beside its own.

**Why four terminal stages.** The files name one terminal continuation value for each of the four households whose problems end the year (`trellis.yml:4-6`; `economics.md:135`): the worker's end-of-year state `(a_wk_wa, y_wk_wa, θ_wk_wa)`, the young entrepreneur's repay branch `(a_ye_ea, y_ye_ea, θ_ye_ea)`, the old entrepreneur's repay branch `(a_oe_ed, θ_oe_ed)` and the retiree's `a_rt_rd`. They lie on three sets. The worker and the young entrepreneur share one, Xa × Y × Θ, but not a continuation value: in the paper the worker's continuation is β π_y E V + β (1 − π_y) W_r and the young entrepreneur's β π_y E V + β (1 − π_y) E W (`economics.md:37, 59`). E29 makes a provenance that matters after a join a state field the author writes, so the two are separate stages and not one stage with two sources. This is the application's answer to §7 item 11 of the unification, offered as a proposal.

**Why the rename.** A terminal stage stands where next year's demographic stage stands. Under that stage's arrival names, `a_wa, y_wa, θ_wa` for the worker, two stages of `periods[0]` would arrive at one name, and the terminal period would contain a cycle. Probe 8 ([p08_without_rename.py](probes/p08_without_rename.py)) writes `terminal_worker` at `a_wa, y_wa, θ_wa`, and `elaborate_trellis` refuses it under `period-join-cycle`: "worker_ageing continues to 'a_wa_yc' and young_choice arrives at 'a_yc'; young_choice continues to 'a_yc_wk' and worker arrives at 'a_wk'; worker continues to 'a_wk_wa' and worker_ageing arrives at 'a_wa'". The new names carry the terminal stage's own tag, the folder's convention that an arrival field carries its own stage's tag (`economics.md:114`).

**The terminal value is a constant.** In the bequest's pattern `V[>]` stands on the one-point set, `𝑉≻ : {()} → ℝ` (probe 10), so each terminal stage's value is the constant boundary data, zero (A33), whatever the end-of-year state. That is the usual starting value of value function iteration and suffices for a truncated trellis; a terminal value that depends on the state, such as the paper's stationary values, has no place in this form (the finding on E15 returned with this example).

**What `load_recipe(registry, "spec.yml")` returns** (probe 4): three periods and two inter-period mappings, equal to each other; `periods[0]` holds the fourteen stages and thirteen connectors, `periods[1]` and `periods[2]` the ten stages and twelve connectors; `registry` is `{'calibration': {'α': 0.33, 'A': 1.0}}`; each terminal stage's record holds an empty calibration and settings, the empty methods mapping and `provenance["active"] = [0, 0]`; the worker's calibration holds no `w` and no `τ`, which a fill supplies (§7).

## 1 The fields at the perches, as the files declare them

All eight files declare `Xa := ℝ₊` and `Θ := ℝ₊`, and all but `old_choice.bl` and `old_entrepreneur.bl` declare `Y := ℝ₊₊`; the cards print carriers by these names, as the package prints the worker's (probe 1). Each continuation perch is a disjoint union with one summand per label (E1, E24), and each branch value's base is the summand at its position in the selection tuple (E6); the position is given in the table.

**`young_choice.bl`**, selected by a control:

| Perch | State fields | Value fields | Other |
|---|---|---|---|
| ≺ arrival (`:7`) | `a_yc : Xa`, `y_yc : Y`, `θ_yc : Θ` | `V[<] : ℝ` (`:30`) | |
| ∼ decision (`:7, 13`) | `a : Xa`, `y : Y`, `θ : Θ` | `V : ℝ` (`:26`) | `d : !ctrl @ {entrepreneur, worker}` (`:13`) |
| ≻ entrepreneur (`:14`) | `a_ye : Xa`, `y_ye : Y`, `θ_ye : Θ` | `V_e[>] : ℝ` (`:26`), position 1 | |
| ≻ worker (`:19`) | `a_yc_wk : Xa`, `y_yc_wk : Y`, `θ_yc_wk : Θ` | `V_w[>] : ℝ` (`:26`), position 2 | |

The continuation state space is X_entrepreneur ⊔ X_worker with both summands Xa × Y × Θ. Among the Cagetti files this is the stage whose two summands are one set, so the base of a value, and not its carrier, tells the two branch values apart (E6, E17; §4.1).

**`old_choice.bl`**, selected by a control:

| Perch | State fields | Value fields | Other |
|---|---|---|---|
| ≺ arrival (`:6`) | `a_oc : Xa`, `θ_oc : Θ` | `V[<] : ℝ` (`:25`) | |
| ∼ decision (`:6, 11`) | `a : Xa`, `θ : Θ` | `V : ℝ` (`:21`) | `d : !ctrl @ {entrepreneur, retiree}` (`:11`) |
| ≻ entrepreneur (`:12`) | `a_oe : Xa`, `θ_oe : Θ` | `W_e[>] : ℝ` (`:21`), position 1 | |
| ≻ retiree (`:16`) | `a_oc_rt : Xa` | `W_r[>] : ℝ` (`:21`), position 2 | |

**The four demographic stages**, selected by the shock `s` (E13, the second build). The shocks `y_n` and `θ_n` are drawn on the arrival edge and `s` on the decision edge; none is a state field (`fields()` answers them at the perch `shck` with the role `shock`, probe 5), so no join reads them (`economics.md:114`).

| Stage | ≺ arrival | ∼ decision | ≻ first label, position 1 | ≻ second label, position 2 | Laws |
|---|---|---|---|---|---|
| `entrepreneur_death.bl` | `a_ed : Xa`, `θ_ed : Θ` (`:23`); `V[<]` (`:45`) | `a, y, θ`; `V` (`:41`) | survive: `a_ed_oc : Xa`, `θ_ed_oc : Θ` (`:30`); `W_old[>]` | die: `a_ed_yc : Xa`, `y_ed_yc : Y`, `θ_ed_yc : Θ` (`:34`); `V_young[>]` | `y_n ~ Invariant(P_y, y_grid)`, `θ_n ~ MarkovChain(((ρ_θ0, 1 - ρ_θ0), (1 - ρ_θ1, ρ_θ1)), (0, θ_e), θ_ed)`, `s : {survive, die}`, `s ~ Categorical((π_o, 1 - π_o))` (`:16-21`) |
| `retiree_death.bl` | `a_rd : Xa` (`:23`); `V[<]` (`:44`) | `a, y, θ`; `V` (`:40`) | survive: `a_rd_rt : Xa` (`:30`); `W_r[>]` | die: `a_rd_yc, y_rd_yc, θ_rd_yc` (`:33`); `V_young[>]` | `y_n ~ Invariant(P_y, y_grid)`, `θ_n ~ Invariant(((ρ_θ0, 1 - ρ_θ0), (1 - ρ_θ1, ρ_θ1)), (0, θ_e))`, `s ~ Categorical((π_o, 1 - π_o))` (`:16-21`) |
| `worker_ageing.bl` | `a_wa : Xa`, `y_wa : Y`, `θ_wa : Θ` (`:22`); `V[<]` (`:43`) | `a, y, θ`; `V` (`:39`) | young: `a_wa_yc, y_wa_yc, θ_wa_yc` (`:29`); `V_young[>]` | old: `a_wa_rt : Xa` (`:34`); `W_r[>]` | `y_n ~ MarkovChain(P_y, y_grid, y_wa)`, `θ_n ~ MarkovChain(…, θ_wa)`, `s : {young, old}`, `s ~ Categorical((π_y, 1 - π_y))` (`:15-20`) |
| `entrepreneur_ageing.bl` | `a_ea : Xa`, `y_ea : Y`, `θ_ea : Θ` (`:22`); `V[<]` (`:43`) | `a, y, θ`; `V` (`:39`) | young: `a_ea_yc, y_ea_yc, θ_ea_yc` (`:29`); `V_young[>]` | old: `a_ea_oc : Xa`, `θ_ea_oc : Θ` (`:34`); `W_old[>]` | `y_n ~ MarkovChain(P_y, y_grid, y_ea)`, `θ_n ~ MarkovChain(…, θ_ea)`, `s ~ Categorical((π_y, 1 - π_y))` (`:15-20`) |

**The two entrepreneur stages**, selected by a control chosen beside two continuous controls (E14):

| Stage | ≺ arrival | ∼ decision | ≻ repay, position 1 | ≻ default, position 2 |
|---|---|---|---|---|
| `young_entrepreneur.bl` | `a_ye : Xa`, `y_ye : Y`, `θ_ye : Θ` (`:16`); `V[<]` (`:39`) | `a, y, θ`; `V` (`:35`); `k : ℝ₊ @ !ctrl`, `c : ℝ₊₊ @ !ctrl`, `d : !ctrl @ {repay, default}` (`:22`) | `a_ye_ea, y_ye_ea, θ_ye_ea` (`:23`); `V_repay[>]` | `a_ye_wk, y_ye_wk, θ_ye_wk` (`:28`); `V_w[>]` |
| `old_entrepreneur.bl` | `a_oe : Xa`, `θ_oe : Θ` (`:15`); `V[<]` (`:34`) | `a, θ`; `V` (`:30`); `k`, `c`, `d` as above (`:20`) | `a_oe_ed : Xa`, `θ_oe_ed : Θ` (`:21`); `V_repay[>]` | `a_oe_rt : Xa` (`:25`); `W_r[>]` |

## 2 The branches and what selects them

**`young_choice`.** The block `dcsn_to_cntn` (`young_choice.bl:13-24`) reads `(a, y, θ)` at the coordinate `d`. Read at `d = entrepreneur`: `a_ye = a`, `y_ye = y`, `θ_ye = θ`. Read at `d = worker`: `a_yc_wk = a`, `y_yc_wk = y`, `θ_yc_wk = θ`. The policy 𝑑 : Xa × Y × Θ → {entrepreneur, worker}, defined by the operative line `d = argmax_{d}(V_e[>], V_w[>])` (`:35`), selects the branch; every label is feasible at every state (E7). This is the paper's (2), V = max{V_e, V_w} (`economics.md:32-34`).

**`old_choice`.** The block (`old_choice.bl:11-19`) reads `(a, θ)` at `d`: at `entrepreneur`, `a_oe = a`, `θ_oe = θ`; at `retiree`, `a_oc_rt = a`. The policy 𝑑 : Xa × Θ → {entrepreneur, retiree} is defined by `d = argmax_{d}(W_e[>], W_r[>])` (`:30`), the paper's (10).

**The four demographic stages.** The label is the shock `s`, drawn on the decision edge by a law on the labels alone, `Categorical((π_o, 1 - π_o))` in the two death stages and `Categorical((π_y, 1 - π_y))` in the two ageing stages, the probabilities in the order of the labels (`economics.md:108`). The law reads neither the state nor a policy, as §1 of the unification chooses (E19; `retiree_death.bl:20-21` is the file that §1 cites). There is no policy and no policy block. Every nested line is an identity; the survivor, the ageing worker and the ageing entrepreneur keep only the fields their successor reads (`a_rd_rt`, `a_wa_rt`, `a_ea_oc, θ_ea_oc`, `a_ed_oc, θ_ed_oc`).

**The two entrepreneur stages.** The label `d` is a control chosen beside `k` and `c`. The repay branch's law reads both, the budget (4) (`young_entrepreneur.bl:24`); the default branch's reads `k`, the capital kept on default (`:29`). The policy block writes three lines: a joint maximization over `(k, c)` whose binder `k, c : Γ(a, θ, k)` sets the feasible set of `c` by `k` (`:44`); the enforcement inequality (5) (`:45`); and the choice of `d` over the tuple of the value line (`:46`). Every label is feasible at every state (E7). Where (5) binds, repaying and defaulting are worth the same to a positive share of households, and the paper's rule is that an indifferent household repays, so that no household defaults (`economics.md:103`); E9 leaves that choice to the method.

## 3 The records the fold would write

**`young_choice` and `old_choice`, the first build.**

*Definitions.* For `young_choice`, one law `young_choice:g:dcsn_to_cntn`, 𝑔≻ : Xa × Y × Θ × {entrepreneur, worker} → (Xa × Y × Θ) ⊔ (Xa × Y × Θ), holding the six nested lines with their labels as conditions, `d = entrepreneur` or `d = worker` (E4); its sections 𝑔_entrepreneur≻ and 𝑔_worker≻ are abbreviations of the builders that read them (E5). Six line records at the addresses `item_addresses` gives (probe 6): `dcsn_to_cntn.entrepreneur.1`, `.2`, `.3` and `dcsn_to_cntn.worker.1`, `.2`, `.3`, no nested line carrying an id. The aggregator `young_choice:G:cntn_to_dcsn` is the selection kernel of `:27`, the tuple indexed by `d`. `BlockData.branch_labels = ("entrepreneur", "worker")`; `branches(stage)` answers `{entrepreneur: (a_ye, y_ye, θ_ye), worker: (a_yc_wk, y_yc_wk, θ_yc_wk)}`, `kind(stage)` answers `branching`, and E27's third query answers the choice, the key `d` being a `!ctrl` coordinate (E12, E27). For `old_choice`, 𝑔≻ : Xa × Θ × {entrepreneur, retiree} → (Xa × Θ) ⊔ Xa; three line records, `dcsn_to_cntn.entrepreneur.1`, `.2` and `dcsn_to_cntn.retiree.1`; `branch_labels = ("entrepreneur", "retiree")`; `branches` answers `{entrepreneur: (a_oe, θ_oe), retiree: (a_oc_rt,)}`.

*Operations.* Backward `cntn_to_dcsn`: `Pullback:<label>` for each label, `Aggregation`, `Evaluation` at 𝑑 (§4). Backward `dcsn_to_arvl`: `Pullback` along 𝑔≺, `Aggregation`, `Evaluation`, as `worker.bl` prints it (probe 1), with no expectation. Policy: the two pullbacks, `choice:Aggregation`, `choice:Solution`, `Evaluation`. Forward `arvl_to_dcsn`: one `Pushforward`. Forward `dcsn_to_cntn`: one `Pushforward` at 𝑑 with two outputs.

*Conditions, as terms.* On the Aggregation, K49's membership 𝑉(·) ∈ ℝ. On the Pushforward, each nested line's range at the source point (K65), `a ∈ Xa`, `y ∈ Y` and `θ ∈ Θ`, all established by the declared sets and kept on `obligations()`, as is the conservation identity, μ_entrepreneur≻(Xa × Y × Θ) + μ_worker≻(Xa × Y × Θ) = μ(Xa × Y × Θ) for `young_choice`, established by the exhaustive label set (E3, E7); so no condition prints on the forward card. The label conditions stand on the line records. On the Solution, its rule alone and no tie rule (E9).

**The four demographic stages, the second build (E13).**

*Definitions.* For `entrepreneur_death`, one law `entrepreneur_death:g:dcsn_to_cntn`, 𝑔≻ : Xa × Y × Θ × {survive, die} → (Xa × Θ) ⊔ (Xa × Y × Θ), its nested lines conditioned on `s = survive` or `s = die` (§3 item 3 conditions each line on the label of its block; here the label's variable is the shock), with the sections 𝑔_survive≻ and 𝑔_die≻. Five line records: `dcsn_to_cntn.survive.1`, `.2` and `dcsn_to_cntn.die.1`, `.2`, `.3`. The aggregator `entrepreneur_death:G:cntn_to_dcsn` holds `:42`, `V = β*E_{s}((W_old[>], η*V_young[>])[s])`, which E13 folds to the weighted case operation, V = β · Σ_j p(j) Q_j. `branch_labels = ("survive", "die")`; `branches` answers `{survive: (a_ed_oc, θ_ed_oc), die: (a_ed_yc, y_ed_yc, θ_ed_yc)}`; E27's third query answers the expectation, the key `s` being a declared shock under `E_{s}`. For `retiree_death`, 𝑔≻ : Xa × Y × Θ × {survive, die} → Xa ⊔ (Xa × Y × Θ), four line records (`dcsn_to_cntn.survive.1`, `dcsn_to_cntn.die.1`, `.2`, `.3`), `branches` `{survive: (a_rd_rt,), die: (a_rd_yc, y_rd_yc, θ_rd_yc)}`. For `worker_ageing`, 𝑔≻ : Xa × Y × Θ × {young, old} → (Xa × Y × Θ) ⊔ Xa, four line records (`dcsn_to_cntn.young.1`, `.2`, `.3`, `dcsn_to_cntn.old.1`), `branches` `{young: (a_wa_yc, y_wa_yc, θ_wa_yc), old: (a_wa_rt,)}`. For `entrepreneur_ageing`, 𝑔≻ : Xa × Y × Θ × {young, old} → (Xa × Y × Θ) ⊔ (Xa × Θ), five line records, `branches` `{young: (a_ea_yc, y_ea_yc, θ_ea_yc), old: (a_ea_oc, θ_ea_oc)}`.

*Operations.* Backward `cntn_to_dcsn`: `Pullback:<label>` for each label, one `Aggregation` of rank (Q_j)_j → v whose kernel is the weighted case operation, and `Evaluation`; there is no `at` block, since the stage has no policy. Probe 7 ([p07_shock_tuple_today.py](probes/p07_shock_tuple_today.py)) shows what the present fold makes of the same value line when the two nested blocks are written as one: one `Pullback` along the whole 𝑔≻, `value:Aggregation:1` forming the tuple, `value:Expectation:1` over `s`, `Aggregation` and `Evaluation`, with both value inputs typed on the product of every branch field, `Xa × Θ × Xa × Y × Θ → ℝ`. E6 replaces that product by the summand of each tuple position, and E13 replaces the Expectation over one base by the weighted case operation. Backward `dcsn_to_arvl`: `Pullback` along 𝑔≺, one `Expectation` over `(y_n, θ_n)`, `Aggregation`, `Evaluation`, as the stand-ins of probe 5 print it; the branching build changes nothing there. Forward `arvl_to_dcsn`: `DistributionExtension:y_n`, `DistributionExtension:θ_n`, `Pushforward`, as probe 5 prints it for the two ageing stages; for the two death stages the forward builders graph is refused, the law of `y_n` (and in `retiree_death.bl` that of `θ_n`) being written with the family `Invariant`, which the package does not admit (§7). Forward `dcsn_to_cntn`: `DistributionExtension:s`, which the package prints today (probe 7), and one `Pushforward` with two outputs, whose rule is [open: E13].

*Conditions.* On the Aggregation, 𝑉(a, y, θ) ∈ ℝ. On the Pushforward, the nested lines' ranges, all established by the declared sets; the conservation identity Σ_j μ_j≻(X_j) = μ(Xa × Y × Θ), established here by P_s being a probability on the labels and not by E7's exhaustive label set [open: E13].

*The expectation E13 states.* The nested lines give 𝑔_survive≻(a, y, θ) = (a, θ) in `entrepreneur_death` and a in `retiree_death`, 𝑔_die≻(a, y, θ) = 𝑔_young≻(a, y, θ) = (a, y, θ), and 𝑔_old≻(a, y, θ) = a in `worker_ageing` and (a, θ) in `entrepreneur_ageing`. The weighted case operation Σ_j p(j) Q_j of `docs/bellman-calculus/09-branching.md:77` then reads:

- `entrepreneur_death`: 𝑉(a, y, θ) = β · [π_o · 𝑊_old≻(a, θ) + (1 − π_o) · η · 𝑉_young≻(a, y, θ)];
- `retiree_death`: 𝑉(a, y, θ) = β · [π_o · 𝑊_r≻(a) + (1 − π_o) · η · 𝑉_young≻(a, y, θ)];
- `worker_ageing`: 𝑉(a, y, θ) = β · [π_y · 𝑉_young≻(a, y, θ) + (1 − π_y) · 𝑊_r≻(a)];
- `entrepreneur_ageing`: 𝑉(a, y, θ) = β · [π_y · 𝑉_young≻(a, y, θ) + (1 − π_y) · 𝑊_old≻(a, θ)].

*The hand derivation on `retiree_death.bl`* that §6 of the unification asks of the second build. The arrival builder gives 𝑉≺(a_rd) = E_{y_n, θ_n}[𝑉(a_rd, y_n, θ_n)] (probe 5's card of `dcsn_to_arvl`), so

𝑉≺(a_rd) = β · π_o · 𝑊_r≻(a_rd) + β · (1 − π_o) · η · E_{y_n, θ_n}[𝑉_young≻(a_rd, y_n, θ_n)],

the survivor's term leaving the expectation because 𝑊_r≻ reads the assets alone (`economics.md:106`). With 𝑊_r≻ the retiree's arrival value, the paper's W_r, and 𝑉_young≻ the young choice's arrival value, the paper's V (the joins of §6), this is the continuation in the paper's (13), β π_o W_r(a′) + η β (1 − π_o) E V(a′, y′, θ′), with the offspring's abilities drawn from the invariant distributions (`economics.md:79-82`). The same substitution gives the continuations in (11), (8) and (3) from the other three stages.

**The two entrepreneur stages (E14).** E14 leaves them out of the first build, "continuous controls or an inequality inside a branching block", each "its own amendment", so no fold writes their records in the first or the second build, and the refusal they meet is not stated (the finding on E14 returned with this example). Once that amendment admits them, the rules of §3 would determine: one law 𝑔≻ : Xa × Y × Θ × ℝ₊ × ℝ₊₊ × {repay, default} → (Xa × Y × Θ) ⊔ (Xa × Y × Θ) for `young_entrepreneur`, its six nested lines (`young_entrepreneur.bl:24-26, 29-31`) conditioned on the label and reading `k` and `c`; line records at `dcsn_to_cntn.repay.budget`, `.2`, `.3` and `dcsn_to_cntn.default.kept_capital`, `.2`, `.3` (probe 6); the value selection of `:36` folded to E2's Aggregation at the policy; the bases of `V_repay[>]` and `V_w[>]` from their tuple positions (E6); `branches` `{repay: (a_ye_ea, y_ye_ea, θ_ye_ea), default: (a_ye_wk, y_ye_wk, θ_ye_wk)}`. The rules leave open whether the policy is one, (𝑘, 𝑐, 𝑑), or two; the joint maximization whose binder reads a control it binds; the enforcement inequality; the reads of `V_repay[>]` outside a selection tuple (`:44-45`); and the spelling of a section at a label and at a policy.

## 4 The cards at 78 columns

On 28 September 2026 every card of this section that the package prints was replaced by its print, in the card's form of the internal developer release 0.01 (`card-redesign.md`), printed and not drawn by hand; the cards it refuses, the forward cards of `entrepreneur_death` and `retiree_death` and the five cards of §4.4, keep their drawings on paper in the form of AMD-SG-034, and the sentences under each card were written for those drawings. The cards of this section are composed on paper by [compose_cards.py](probes/compose_cards.py), which sets the blocks in the columns the package uses on the cards it prints today (probe 1) and checks that no line passes 78 columns. Long rules are broken as the layout engine would break them (AMD-SG-034 §4 item 10), one admissible breaking shown. The measures' letter follows the open notation brief (§7 item 1 of the unification); the sections' spelling follows E5 (§7 item 8).

### 4.1 `young_choice`

```text
STAGE young_choice / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_e≻  : Xa × Y × Θ → ℝ
       𝑉_w≻  : Xa × Y × Θ → ℝ
       ────────────────────────────────────────────────────────────
  out  𝑉     : Xa × Y × Θ → ℝ

At
  𝑑  : Xa × Y × Θ → {entrepreneur, worker}

Where
  𝑔_entrepreneur≻  : Xa × Y × Θ → Xa × Y × Θ,
                     𝑔_entrepreneur≻(a, y, θ) = 𝑔≻(a, y, θ, entrepreneur)
  𝑔_worker≻        : Xa × Y × Θ → Xa × Y × Θ,
                     𝑔_worker≻(a, y, θ) = 𝑔≻(a, y, θ, worker)

Operations
  1  Pullback:entrepreneur
     in: 𝑉_e≻                           out: 𝑉_e≻ ∘ 𝑔_entrepreneur≻
     ──────────────────────────────────────────────────────────────
     rule: (𝑉_e≻ ∘ 𝑔_entrepreneur≻)(a, y, θ) = 𝑉_e≻(𝑔_entrepreneur≻(a, y, θ))

  2  Pullback:worker
     in: 𝑉_w≻                           out: 𝑉_w≻ ∘ 𝑔_worker≻
     ──────────────────────────────────────────────────────────────
     rule: (𝑉_w≻ ∘ 𝑔_worker≻)(a, y, θ) = 𝑉_w≻(𝑔_worker≻(a, y, θ))

  3  Aggregation
     in: (1), (2)                       out: 𝑉
     ──────────────────────────────────────────────────────────────
     rule: 𝑉 = (𝑉_e≻(𝑔_entrepreneur≻(a, y, θ)), 𝑉_w≻(𝑔_worker≻(a, y, θ)))[𝑑]
           on (a, y, θ) ∈ Xa × Y × Θ

  4  Evaluation
     in: 𝑉                              out: 𝑉
     ──────────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Y × Θ → ℝ

Conditions
  Aggregation  𝑉(a, y, θ) ∈ ℝ
──────────────────────────────────────────────────────────────────────────────
Source  young_choice.bl
  27  V = (V_e[>], V_w[>])[d]  :: [id=choice_value]

Definitions referenced
  Xa    young_choice:set:Xa
  Y     young_choice:set:Y
  Θ     young_choice:set:Θ
  𝑔≻    young_choice:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The signature lists each branch's value on that branch's set (E6); `at` types the policy plainly (E7); `where` states the two sections of the one law (E4, E5); rows 1 and 2 are the pullbacks, keyed by label; row 3 is the selection, an Aggregation whose rule is the file's line at the point with the label read as the policy (E2). The two branch values stand on one set and on two bases. `bundled_sorts` (`packages/bellman/bellman/display/printers.py:819-832`) bundles value wires only where their coordinates agree, so under E6 they are two wires, and `young_choice.builders.cntn_to_dcsn.signature()` prints each on its own line (§6 item 1 of the unification):

```text
in         𝑉_e≻ : Xa × Y × Θ → ℝ
in         𝑉_w≻ : Xa × Y × Θ → ℝ
out        𝑉 : Xa × Y × Θ → ℝ
```

Under the rule E6 replaces, a declared input function is free in every state of its perch, the two carry one domain and print as one bundle, as `(𝑊_old≻, 𝑉_young≻) : Xa × Θ × Xa × Y × Θ → ℝ × ℝ` prints on the one-block variant of probe 7.

```text
STAGE young_choice / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ                : finite measure on Xa × Y × Θ
       ────────────────────────────────────────────────────────────────
  out  μ_entrepreneur≻  : finite measure on Xa × Y × Θ
       μ_worker≻        : finite measure on Xa × Y × Θ

At
  𝑑  : Xa × Y × Θ → {entrepreneur, worker}

Where
  𝑔_entrepreneur≻  : Xa × Y × Θ → Xa × Y × Θ,
                     𝑔_entrepreneur≻(a, y, θ) = 𝑔≻(a, y, θ, entrepreneur)
  𝑔_worker≻        : Xa × Y × Θ → Xa × Y × Θ,
                     𝑔_worker≻(a, y, θ) = 𝑔≻(a, y, θ, worker)

Operations
  1  Pushforward
     in: μ                              out: μ_entrepreneur≻, μ_worker≻
     ──────────────────────────────────────────────────────────────────
     rule: μ_entrepreneur≻(B)
             = μ({a, y, θ ∈ Xa × Y × Θ |
                   𝑑(a, y, θ) = entrepreneur ∧ 𝑔_entrepreneur≻(a, y, θ) ∈ B})
           μ_worker≻(B)
             = μ({a, y, θ ∈ Xa × Y × Θ |
                   𝑑(a, y, θ) = worker ∧ 𝑔_worker≻(a, y, θ) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  young_choice.bl
  15  a_ye = a
  16  y_ye = y
  17  θ_ye = θ
  20  a_yc_wk = a
  21  y_yc_wk = y
  22  θ_yc_wk = θ

Definitions referenced
  Xa    young_choice:set:Xa
  Y     young_choice:set:Y
  Θ     young_choice:set:Θ
  𝑔≻    young_choice:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Row 1 is the fork (E3), one push-forward at 𝑑 with one output measure per label; the two masses sum to μ's, a condition the record holds as established and the card does not print.

```text
STAGE young_choice / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_e≻  : Xa × Y × Θ → ℝ
       𝑉_w≻  : Xa × Y × Θ → ℝ
       ────────────────────────────────────────────────────────────────────
  out  𝑑     : Xa × Y × Θ → {entrepreneur, worker}

Where
  𝑔_entrepreneur≻  : Xa × Y × Θ → Xa × Y × Θ,
                     𝑔_entrepreneur≻(a, y, θ) = 𝑔≻(a, y, θ, entrepreneur)
  𝑔_worker≻        : Xa × Y × Θ → Xa × Y × Θ,
                     𝑔_worker≻(a, y, θ) = 𝑔≻(a, y, θ, worker)

Operations
  1  Pullback:entrepreneur
     in: 𝑉_e≻                           out: 𝑉_e≻ ∘ 𝑔_entrepreneur≻
     ──────────────────────────────────────────────────────────────────────
     rule: (𝑉_e≻ ∘ 𝑔_entrepreneur≻)(a, y, θ) = 𝑉_e≻(𝑔_entrepreneur≻(a, y, θ))

  2  Pullback:worker
     in: 𝑉_w≻                           out: 𝑉_w≻ ∘ 𝑔_worker≻
     ──────────────────────────────────────────────────────────────────────
     rule: (𝑉_w≻ ∘ 𝑔_worker≻)(a, y, θ) = 𝑉_w≻(𝑔_worker≻(a, y, θ))

  3  choice:Aggregation
     in: (1), (2)
     out: (a, y, θ, d)
            ↦ (𝑉_e≻(𝑔_entrepreneur≻(a, y, θ)), 𝑉_w≻(𝑔_worker≻(a, y, θ)))[d]
     ──────────────────────────────────────────────────────────────────────
     rule: (a, y, θ, d)
             ↦ (𝑉_e≻(𝑔_entrepreneur≻(a, y, θ)), 𝑉_w≻(𝑔_worker≻(a, y, θ)))[d]

  4  choice:Argmax
     in: (3)                            out: 𝑑
     ──────────────────────────────────────────────────────────────────────
     rule: 𝑑(a, y, θ)
             ∈ argmax_{d ∈ {entrepreneur, worker}}
                 [(𝑉_e≻(𝑔_entrepreneur≻(a, y, θ)),
                   𝑉_w≻(𝑔_worker≻(a, y, θ)))[d]]

  5  Evaluation
     in: 𝑑                              out: 𝑑
     ──────────────────────────────────────────────────────────────────────
     rule: 𝑑 : Xa × Y × Θ → {entrepreneur, worker}
──────────────────────────────────────────────────────────────────────────────
Source  young_choice.bl
  35  d = argmax_{d}(V_e[>], V_w[>])  :: [id=choice]

Definitions referenced
  Xa    young_choice:set:Xa
  Y     young_choice:set:Y
  Θ     young_choice:set:Θ
  𝑔≻    young_choice:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

As on tenure's policy card (`example-tenure.md` §4): the line is operative, so it forms a Solution whose rule is the complete line at the point (K66, K69); row 3's output falls below its row (K72); the rule states the set of maximizers and no tie rule (E9).

### 4.2 `old_choice`

```text
STAGE old_choice / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑊_e≻  : Xa × Θ → ℝ
       𝑊_r≻  : Xa → ℝ
       ────────────────────────────────────────────────────────────
  out  𝑉     : Xa × Θ → ℝ

At
  𝑑  : Xa × Θ → {entrepreneur, retiree}

Where
  𝑔_entrepreneur≻  : Xa × Θ → Xa × Θ,
                     𝑔_entrepreneur≻(a, θ) = 𝑔≻(a, θ, entrepreneur)
  𝑔_retiree≻       : Xa × Θ → Xa,  𝑔_retiree≻(a, θ) = 𝑔≻(a, θ, retiree)

Operations
  1  Pullback:entrepreneur
     in: 𝑊_e≻                           out: 𝑊_e≻ ∘ 𝑔_entrepreneur≻
     ──────────────────────────────────────────────────────────────
     rule: (𝑊_e≻ ∘ 𝑔_entrepreneur≻)(a, θ) = 𝑊_e≻(𝑔_entrepreneur≻(a, θ))

  2  Pullback:retiree
     in: 𝑊_r≻                           out: 𝑊_r≻ ∘ 𝑔_retiree≻
     ──────────────────────────────────────────────────────────────
     rule: (𝑊_r≻ ∘ 𝑔_retiree≻)(a, θ) = 𝑊_r≻(𝑔_retiree≻(a, θ))

  3  Aggregation
     in: (1), (2)                       out: 𝑉
     ──────────────────────────────────────────────────────────────
     rule: 𝑉 = (𝑊_e≻(𝑔_entrepreneur≻(a, θ)), 𝑊_r≻(𝑔_retiree≻(a, θ)))[𝑑]
           on (a, θ) ∈ Xa × Θ

  4  Evaluation
     in: 𝑉                              out: 𝑉
     ──────────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Θ → ℝ

Conditions
  Aggregation  𝑉(a, θ) ∈ ℝ
──────────────────────────────────────────────────────────────────────────────
Source  old_choice.bl
  22  V = (W_e[>], W_r[>])[d]  :: [id=choice_value]

Definitions referenced
  Xa    old_choice:set:Xa
  Θ     old_choice:set:Θ
  𝑔≻    old_choice:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE old_choice / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ                : finite measure on Xa × Θ
       ─────────────────────────────────────────────────────────────────
  out  μ_entrepreneur≻  : finite measure on Xa × Θ
       μ_retiree≻       : finite measure on Xa

At
  𝑑  : Xa × Θ → {entrepreneur, retiree}

Where
  𝑔_entrepreneur≻  : Xa × Θ → Xa × Θ,
                     𝑔_entrepreneur≻(a, θ) = 𝑔≻(a, θ, entrepreneur)
  𝑔_retiree≻       : Xa × Θ → Xa,  𝑔_retiree≻(a, θ) = 𝑔≻(a, θ, retiree)

Operations
  1  Pushforward
     in: μ                              out: μ_entrepreneur≻, μ_retiree≻
     ───────────────────────────────────────────────────────────────────
     rule: μ_entrepreneur≻(B)
             = μ({a, θ ∈ Xa × Θ |
                   𝑑(a, θ) = entrepreneur ∧ 𝑔_entrepreneur≻(a, θ) ∈ B})
           μ_retiree≻(B)
             = μ({a, θ ∈ Xa × Θ | 𝑑(a, θ) = retiree ∧ 𝑔_retiree≻(a, θ) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  old_choice.bl
  13  a_oe = a
  14  θ_oe = θ
  17  a_oc_rt = a

Definitions referenced
  Xa    old_choice:set:Xa
  Θ     old_choice:set:Θ
  𝑔≻    old_choice:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE old_choice / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑊_e≻  : Xa × Θ → ℝ
       𝑊_r≻  : Xa → ℝ
       ───────────────────────────────────────────────────────────────────────
  out  𝑑     : Xa × Θ → {entrepreneur, retiree}

Where
  𝑔_entrepreneur≻  : Xa × Θ → Xa × Θ,
                     𝑔_entrepreneur≻(a, θ) = 𝑔≻(a, θ, entrepreneur)
  𝑔_retiree≻       : Xa × Θ → Xa,  𝑔_retiree≻(a, θ) = 𝑔≻(a, θ, retiree)

Operations
  1  Pullback:entrepreneur
     in: 𝑊_e≻                           out: 𝑊_e≻ ∘ 𝑔_entrepreneur≻
     ─────────────────────────────────────────────────────────────────────────
     rule: (𝑊_e≻ ∘ 𝑔_entrepreneur≻)(a, θ) = 𝑊_e≻(𝑔_entrepreneur≻(a, θ))

  2  Pullback:retiree
     in: 𝑊_r≻                           out: 𝑊_r≻ ∘ 𝑔_retiree≻
     ─────────────────────────────────────────────────────────────────────────
     rule: (𝑊_r≻ ∘ 𝑔_retiree≻)(a, θ) = 𝑊_r≻(𝑔_retiree≻(a, θ))

  3  choice:Aggregation
     in: (1), (2)
     out: (a, θ, d) ↦ (𝑊_e≻(𝑔_entrepreneur≻(a, θ)), 𝑊_r≻(𝑔_retiree≻(a, θ)))[d]
     ─────────────────────────────────────────────────────────────────────────
     rule: (a, θ, d)
             ↦ (𝑊_e≻(𝑔_entrepreneur≻(a, θ)), 𝑊_r≻(𝑔_retiree≻(a, θ)))[d]

  4  choice:Argmax
     in: (3)                            out: 𝑑
     ─────────────────────────────────────────────────────────────────────────
     rule: 𝑑(a, θ)
             ∈ argmax_{d ∈ {entrepreneur, retiree}}
                 [(𝑊_e≻(𝑔_entrepreneur≻(a, θ)), 𝑊_r≻(𝑔_retiree≻(a, θ)))[d]]

  5  Evaluation
     in: 𝑑                              out: 𝑑
     ─────────────────────────────────────────────────────────────────────────
     rule: 𝑑 : Xa × Θ → {entrepreneur, retiree}
──────────────────────────────────────────────────────────────────────────────
Source  old_choice.bl
  30  d = argmax_{d}(W_e[>], W_r[>])  :: [id=choice]

Definitions referenced
  Xa    old_choice:set:Xa
  Θ     old_choice:set:Θ
  𝑔≻    old_choice:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

`old_choice.builders.cntn_to_dcsn.signature()` prints `in 𝑊_e≻ : Xa × Θ → ℝ`, `in 𝑊_r≻ : Xa → ℝ` and `out 𝑉 : Xa × Θ → ℝ`, each on its own line.

### 4.3 The four demographic stages

The decision builder prints the weighted case operation in the file's form, the expectation over the tuple, since that is what the line writes and the printer rewrites no term (AMD-SG-034 §2 item 0). Whether the record holds that form or the weighted sum is [open: E13]; the sum would print, for `entrepreneur_death`, 𝑉(a, y, θ) = β · (π_o · 𝑊_old≻(𝑔_survive≻(a, y, θ)) + (1 − π_o) · η · 𝑉_young≻(𝑔_die≻(a, y, θ))), with π_o in the definitions in place of `s`. The forward decision builder's first row is the package's own (probe 7). Its Pushforward reads the label from the measure extended by P_s, where E3 reads it from the policy; that rule is [open: E13].

```text
STAGE entrepreneur_death / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑊_old≻    : Xa × Θ → ℝ
       𝑉_young≻  : Xa × Y × Θ → ℝ
       ─────────────────────────────────────────────────────────
  out  𝑉         : Xa × Y × Θ → ℝ

Where
  𝑔_survive≻  : Xa × Y × Θ → Xa × Θ,
                𝑔_survive≻(a, y, θ) = 𝑔≻(a, y, θ, survive)
  𝑔_die≻      : Xa × Y × Θ → Xa × Y × Θ,  𝑔_die≻(a, y, θ) = 𝑔≻(a, y, θ, die)

Operations
  1  Pullback:survive
     in: 𝑊_old≻                         out: 𝑊_old≻ ∘ 𝑔_survive≻
     ───────────────────────────────────────────────────────────
     rule: (𝑊_old≻ ∘ 𝑔_survive≻)(a, y, θ) = 𝑊_old≻(𝑔_survive≻(a, y, θ))

  2  Pullback:die
     in: 𝑉_young≻                       out: 𝑉_young≻ ∘ 𝑔_die≻
     ───────────────────────────────────────────────────────────
     rule: (𝑉_young≻ ∘ 𝑔_die≻)(a, y, θ) = 𝑉_young≻(𝑔_die≻(a, y, θ))

  3  Aggregation
     in: (1), (2)                       out: 𝑉
     ───────────────────────────────────────────────────────────
     rule: 𝑉
             = β · E_{s}[(𝑊_old≻(𝑔_survive≻(a, y, θ)),
                          η · 𝑉_young≻(𝑔_die≻(a, y, θ)))[s]]
           on (a, y, θ) ∈ Xa × Y × Θ

  4  Evaluation
     in: 𝑉                              out: 𝑉
     ───────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Y × Θ → ℝ

Conditions
  Aggregation  𝑉(a, y, θ) ∈ ℝ
──────────────────────────────────────────────────────────────────────────────
Source  entrepreneur_death.bl
  42  V = β*E_{s}((W_old[>], η*V_young[>])[s])  :: [id=value]

Definitions referenced
  Xa    entrepreneur_death:set:Xa
  Y     entrepreneur_death:set:Y
  Θ     entrepreneur_death:set:Θ
  β     entrepreneur_death:parameter:β
  η     entrepreneur_death:parameter:η
  s     entrepreneur_death:distribution:s
  𝑔≻    entrepreneur_death:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE entrepreneur_death / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature         wire          carrier
              in  μ           : finite measure on Xa × Y × Θ
              out μ_survive≻  : finite measure on Xa × Θ
                  μ_die≻      : finite measure on Xa × Y × Θ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
where         (the two sections, as on the decision builder's card)
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
operations    #  operation                in   out
              1  DistributionExtension:s  μ    μ⊗P_s
                                          │ μ⊗P_s(B)
                                          │   = ∫_{(a, y, θ) ∈ Xa × Y × Θ}
                                          │   [P_s({s ∈ {survive, die} |
                                          │     (a, y, θ, s) ∈ B})]
                                          │     μ(d(a, y, θ))
              2  Pushforward              (1)  μ_survive≻, μ_die≻
                                          │ μ_survive≻(B)
                                          │   = μ⊗P_s({a, y, θ, s ∈
                                          │     Xa × Y × Θ × {survive, die} |
                                          │     s = survive
                                          │       ∧ 𝑔_survive≻(a, y, θ) ∈ B})
                                          │ μ_die≻(B)
                                          │   = μ⊗P_s({a, y, θ, s ∈
                                          │     Xa × Y × Θ × {survive, die} |
                                          │     s = die
                                          │       ∧ 𝑔_die≻(a, y, θ) ∈ B})
══════════════════════════════════════════════════════════════════════════════
source        position                  statement
              entrepreneur_death.bl:31  a_ed_oc = a
              entrepreneur_death.bl:32  θ_ed_oc = θ
              entrepreneur_death.bl:35  a_ed_yc = a
              entrepreneur_death.bl:36  y_ed_yc = y
              entrepreneur_death.bl:37  θ_ed_yc = θ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
definitions   name  key
              Xa    entrepreneur_death:set:Xa
              Y     entrepreneur_death:set:Y
              Θ     entrepreneur_death:set:Θ
              s     entrepreneur_death:distribution:s
              P_s   entrepreneur_death:distribution:s
              𝑔≻    entrepreneur_death:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE retiree_death / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑊_r≻      : Xa → ℝ
       𝑉_young≻  : Xa × Y × Θ → ℝ
       ───────────────────────────────────────────────────────
  out  𝑉         : Xa × Y × Θ → ℝ

Where
  𝑔_survive≻  : Xa × Y × Θ → Xa,  𝑔_survive≻(a, y, θ) = 𝑔≻(a, y, θ, survive)
  𝑔_die≻      : Xa × Y × Θ → Xa × Y × Θ,  𝑔_die≻(a, y, θ) = 𝑔≻(a, y, θ, die)

Operations
  1  Pullback:survive
     in: 𝑊_r≻                           out: 𝑊_r≻ ∘ 𝑔_survive≻
     ─────────────────────────────────────────────────────────
     rule: (𝑊_r≻ ∘ 𝑔_survive≻)(a, y, θ) = 𝑊_r≻(𝑔_survive≻(a, y, θ))

  2  Pullback:die
     in: 𝑉_young≻                       out: 𝑉_young≻ ∘ 𝑔_die≻
     ─────────────────────────────────────────────────────────
     rule: (𝑉_young≻ ∘ 𝑔_die≻)(a, y, θ) = 𝑉_young≻(𝑔_die≻(a, y, θ))

  3  Aggregation
     in: (1), (2)                       out: 𝑉
     ─────────────────────────────────────────────────────────
     rule: 𝑉
             = β · E_{s}[(𝑊_r≻(𝑔_survive≻(a, y, θ)),
                          η · 𝑉_young≻(𝑔_die≻(a, y, θ)))[s]]
           on (a, y, θ) ∈ Xa × Y × Θ

  4  Evaluation
     in: 𝑉                              out: 𝑉
     ─────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Y × Θ → ℝ

Conditions
  Aggregation  𝑉(a, y, θ) ∈ ℝ
──────────────────────────────────────────────────────────────────────────────
Source  retiree_death.bl
  41  V = β*E_{s}((W_r[>], η*V_young[>])[s])  :: [id=value]

Definitions referenced
  Xa    retiree_death:set:Xa
  Y     retiree_death:set:Y
  Θ     retiree_death:set:Θ
  β     retiree_death:parameter:β
  η     retiree_death:parameter:η
  s     retiree_death:distribution:s
  𝑔≻    retiree_death:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE retiree_death / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature         wire          carrier
              in  μ           : finite measure on Xa × Y × Θ
              out μ_survive≻  : finite measure on Xa
                  μ_die≻      : finite measure on Xa × Y × Θ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
where         (the two sections, as on the decision builder's card)
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
operations    #  operation                in   out
              1  DistributionExtension:s  μ    μ⊗P_s
                                          │ μ⊗P_s(B)
                                          │   = ∫_{(a, y, θ) ∈ Xa × Y × Θ}
                                          │   [P_s({s ∈ {survive, die} |
                                          │     (a, y, θ, s) ∈ B})]
                                          │     μ(d(a, y, θ))
              2  Pushforward              (1)  μ_survive≻, μ_die≻
                                          │ μ_survive≻(B)
                                          │   = μ⊗P_s({a, y, θ, s ∈
                                          │     Xa × Y × Θ × {survive, die} |
                                          │     s = survive
                                          │       ∧ 𝑔_survive≻(a, y, θ) ∈ B})
                                          │ μ_die≻(B)
                                          │   = μ⊗P_s({a, y, θ, s ∈
                                          │     Xa × Y × Θ × {survive, die} |
                                          │     s = die
                                          │       ∧ 𝑔_die≻(a, y, θ) ∈ B})
══════════════════════════════════════════════════════════════════════════════
source        position             statement
              retiree_death.bl:31  a_rd_rt = a
              retiree_death.bl:34  a_rd_yc = a
              retiree_death.bl:35  y_rd_yc = y
              retiree_death.bl:36  θ_rd_yc = θ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
definitions   name  key
              Xa    retiree_death:set:Xa
              Y     retiree_death:set:Y
              Θ     retiree_death:set:Θ
              s     retiree_death:distribution:s
              P_s   retiree_death:distribution:s
              𝑔≻    retiree_death:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE worker_ageing / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_young≻  : Xa × Y × Θ → ℝ
       𝑊_r≻      : Xa → ℝ
       ─────────────────────────────────────────────────────────
  out  𝑉         : Xa × Y × Θ → ℝ

Where
  𝑔_young≻  : Xa × Y × Θ → Xa × Y × Θ,  𝑔_young≻(a, y, θ) = 𝑔≻(a, y, θ, young)
  𝑔_old≻    : Xa × Y × Θ → Xa,  𝑔_old≻(a, y, θ) = 𝑔≻(a, y, θ, old)

Operations
  1  Pullback:young
     in: 𝑉_young≻                       out: 𝑉_young≻ ∘ 𝑔_young≻
     ───────────────────────────────────────────────────────────
     rule: (𝑉_young≻ ∘ 𝑔_young≻)(a, y, θ) = 𝑉_young≻(𝑔_young≻(a, y, θ))

  2  Pullback:old
     in: 𝑊_r≻                           out: 𝑊_r≻ ∘ 𝑔_old≻
     ───────────────────────────────────────────────────────────
     rule: (𝑊_r≻ ∘ 𝑔_old≻)(a, y, θ) = 𝑊_r≻(𝑔_old≻(a, y, θ))

  3  Aggregation
     in: (1), (2)                       out: 𝑉
     ───────────────────────────────────────────────────────────
     rule: 𝑉
             = β · E_{s}[(𝑉_young≻(𝑔_young≻(a, y, θ)),
                          𝑊_r≻(𝑔_old≻(a, y, θ)))[s]]
           on (a, y, θ) ∈ Xa × Y × Θ

  4  Evaluation
     in: 𝑉                              out: 𝑉
     ───────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Y × Θ → ℝ

Conditions
  Aggregation  𝑉(a, y, θ) ∈ ℝ
──────────────────────────────────────────────────────────────────────────────
Source  worker_ageing.bl
  40  V = β*E_{s}((V_young[>], W_r[>])[s])  :: [id=value]

Definitions referenced
  Xa    worker_ageing:set:Xa
  Y     worker_ageing:set:Y
  Θ     worker_ageing:set:Θ
  β     worker_ageing:parameter:β
  s     worker_ageing:distribution:s
  𝑔≻    worker_ageing:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE worker_ageing / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ         : finite measure on Xa × Y × Θ
       ──────────────────────────────────────────────────────
  out  μ_young≻  : finite measure on Xa × Y × Θ
       μ_old≻    : finite measure on Xa

Where
  𝑔_young≻  : Xa × Y × Θ → Xa × Y × Θ,  𝑔_young≻(a, y, θ) = 𝑔≻(a, y, θ, young)
  𝑔_old≻    : Xa × Y × Θ → Xa,  𝑔_old≻(a, y, θ) = 𝑔≻(a, y, θ, old)

Operations
  1  DistributionExtension:s
     in: μ                              out: μ⊗P_s
     ────────────────────────────────────────────────────────
     rule: μ⊗P_s(B)
             = ∫_{(a, y, θ) ∈ Xa × Y × Θ}
                 [P_s({s ∈ {young, old} | (a, y, θ, s) ∈ B})] μ(d(a, y, θ))

  2  Pushforward
     in: (1)                            out: μ_young≻, μ_old≻
     ────────────────────────────────────────────────────────
     rule: μ_young≻(B)
             = μ⊗P_s({a, y, θ, s ∈ Xa × Y × Θ × {young, old} |
                       s = young ∧ 𝑔_young≻(a, y, θ) ∈ B})
           μ_old≻(B)
             = μ⊗P_s({a, y, θ, s ∈ Xa × Y × Θ × {young, old} |
                       s = old ∧ 𝑔_old≻(a, y, θ) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  worker_ageing.bl
  30  a_wa_yc = a
  31  y_wa_yc = y
  32  θ_wa_yc = θ
  35  a_wa_rt = a

Definitions referenced
  Xa    worker_ageing:set:Xa
  Y     worker_ageing:set:Y
  Θ     worker_ageing:set:Θ
  s     worker_ageing:distribution:s
  P_s   worker_ageing:distribution:s
  𝑔≻    worker_ageing:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE entrepreneur_ageing / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_young≻  : Xa × Y × Θ → ℝ
       𝑊_old≻    : Xa × Θ → ℝ
       ─────────────────────────────────────────────────────────
  out  𝑉         : Xa × Y × Θ → ℝ

Where
  𝑔_young≻  : Xa × Y × Θ → Xa × Y × Θ,  𝑔_young≻(a, y, θ) = 𝑔≻(a, y, θ, young)
  𝑔_old≻    : Xa × Y × Θ → Xa × Θ,  𝑔_old≻(a, y, θ) = 𝑔≻(a, y, θ, old)

Operations
  1  Pullback:young
     in: 𝑉_young≻                       out: 𝑉_young≻ ∘ 𝑔_young≻
     ───────────────────────────────────────────────────────────
     rule: (𝑉_young≻ ∘ 𝑔_young≻)(a, y, θ) = 𝑉_young≻(𝑔_young≻(a, y, θ))

  2  Pullback:old
     in: 𝑊_old≻                         out: 𝑊_old≻ ∘ 𝑔_old≻
     ───────────────────────────────────────────────────────────
     rule: (𝑊_old≻ ∘ 𝑔_old≻)(a, y, θ) = 𝑊_old≻(𝑔_old≻(a, y, θ))

  3  Aggregation
     in: (1), (2)                       out: 𝑉
     ───────────────────────────────────────────────────────────
     rule: 𝑉
             = β · E_{s}[(𝑉_young≻(𝑔_young≻(a, y, θ)),
                          𝑊_old≻(𝑔_old≻(a, y, θ)))[s]]
           on (a, y, θ) ∈ Xa × Y × Θ

  4  Evaluation
     in: 𝑉                              out: 𝑉
     ───────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Y × Θ → ℝ

Conditions
  Aggregation  𝑉(a, y, θ) ∈ ℝ
──────────────────────────────────────────────────────────────────────────────
Source  entrepreneur_ageing.bl
  41  V = β*E_{s}((V_young[>], W_old[>])[s])  :: [id=value]

Definitions referenced
  Xa    entrepreneur_ageing:set:Xa
  Y     entrepreneur_ageing:set:Y
  Θ     entrepreneur_ageing:set:Θ
  β     entrepreneur_ageing:parameter:β
  s     entrepreneur_ageing:distribution:s
  𝑔≻    entrepreneur_ageing:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE entrepreneur_ageing / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ         : finite measure on Xa × Y × Θ
       ──────────────────────────────────────────────────────
  out  μ_young≻  : finite measure on Xa × Y × Θ
       μ_old≻    : finite measure on Xa × Θ

Where
  𝑔_young≻  : Xa × Y × Θ → Xa × Y × Θ,  𝑔_young≻(a, y, θ) = 𝑔≻(a, y, θ, young)
  𝑔_old≻    : Xa × Y × Θ → Xa × Θ,  𝑔_old≻(a, y, θ) = 𝑔≻(a, y, θ, old)

Operations
  1  DistributionExtension:s
     in: μ                              out: μ⊗P_s
     ────────────────────────────────────────────────────────
     rule: μ⊗P_s(B)
             = ∫_{(a, y, θ) ∈ Xa × Y × Θ}
                 [P_s({s ∈ {young, old} | (a, y, θ, s) ∈ B})] μ(d(a, y, θ))

  2  Pushforward
     in: (1)                            out: μ_young≻, μ_old≻
     ────────────────────────────────────────────────────────
     rule: μ_young≻(B)
             = μ⊗P_s({a, y, θ, s ∈ Xa × Y × Θ × {young, old} |
                       s = young ∧ 𝑔_young≻(a, y, θ) ∈ B})
           μ_old≻(B)
             = μ⊗P_s({a, y, θ, s ∈ Xa × Y × Θ × {young, old} |
                       s = old ∧ 𝑔_old≻(a, y, θ) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  entrepreneur_ageing.bl
  30  a_ea_yc = a
  31  y_ea_yc = y
  32  θ_ea_yc = θ
  35  a_ea_oc = a
  36  θ_ea_oc = θ

Definitions referenced
  Xa    entrepreneur_ageing:set:Xa
  Y     entrepreneur_ageing:set:Y
  Θ     entrepreneur_ageing:set:Θ
  s     entrepreneur_ageing:distribution:s
  P_s   entrepreneur_ageing:distribution:s
  𝑔≻    entrepreneur_ageing:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The arrival builders of the four stages are not changed by the branching build and print as probe 5 prints them on stand-ins that keep each file's arrival block, laws and `dcsn_to_arvl` line: `arvl_to_dcsn` as `DistributionExtension:y_n`, `DistributionExtension:θ_n` and `Pushforward`, the laws printed as kernels conditioned on last year's ability, `P_{y_n|y_wa}` and `P_{θ_n|θ_wa}` in `worker_ageing`; and `dcsn_to_arvl` as `Pullback`, `1:Expectation:1`, `Aggregation` and `Evaluation`, with the rule 𝑉≺(a_wa, y_wa, θ_wa) = E_{y_n, θ_n}[𝑉(𝑔≺(a_wa, y_wa, θ_wa, y_n, θ_n))]. In the two death stages the forward `arvl_to_dcsn` is refused (§7).

### 4.4 The two entrepreneur stages, as far as the rules determine them

What E14 leaves open is marked on each card; the spelling 𝑔_repay≻,𝑘,𝑐 joins E5's section at a label to AMD-SG-034's abbreviation at a policy (§4 item 11) and is [open: E5, E14].

```text
STAGE young_entrepreneur / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature         wire        carrier
              in  𝑉_repay≻  : Xa × Y × Θ → ℝ
                  𝑉_w≻      : Xa × Y × Θ → ℝ
              out 𝑉         : Xa × Y × Θ → ℝ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
at            𝑘  : Xa × Y × Θ → ℝ₊
              𝑐  : Xa × Y × Θ → ℝ₊₊,  𝑐(a, y, θ) ∈ Γ(a, θ, 𝑘(a, y, θ))
              𝑑  : Xa × Y × Θ → {repay, default}
              [open: E14] one policy (𝑘, 𝑐, 𝑑) or two; 𝑐's feasibility
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
where         𝑔_repay≻,𝑘,𝑐    : Xa × Y × Θ → Xa × Y × Θ,
                              𝑔_repay≻,𝑘,𝑐(a, y, θ)
                                = 𝑔≻(a, y, θ, 𝑘(a, y, θ), 𝑐(a, y, θ), repay)
              𝑔_default≻,𝑘,𝑐  : Xa × Y × Θ → Xa × Y × Θ,
                              𝑔_default≻,𝑘,𝑐(a, y, θ)
                                = 𝑔≻(a, y, θ, 𝑘(a, y, θ), 𝑐(a, y, θ),
                                     default)
              [open: E5, E14] a section at a label and at a policy
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
operations    #  operation         in        out
              1  Pullback:repay    𝑉_repay≻  𝑉_repay≻ ∘ 𝑔_repay≻,𝑘,𝑐
              2  Pullback:default  𝑉_w≻      𝑉_w≻ ∘ 𝑔_default≻,𝑘,𝑐
              3  Aggregation       (1), (2)  𝑉
                                   │ 𝑉(a, y, θ)
                                   │   = (𝑢(𝑐(a, y, θ))
                                   │        + 𝑉_repay≻(𝑔_repay≻,𝑘,𝑐(a, y, θ)),
                                   │      𝑉_w≻(𝑔_default≻,𝑘,𝑐(a, y, θ)))
                                   │     [𝑑(a, y, θ)]
              4  Evaluation        𝑉         𝑉
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
conditions    Aggregation  𝑉(a, y, θ) ∈ ℝ
══════════════════════════════════════════════════════════════════════════════
source        position                  statement
              young_entrepreneur.bl:36  V = (𝑢(c) + V_repay[>], V_w[>])[d]
                                        │ :: [id=value]
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
definitions   name  key
              Xa    young_entrepreneur:set:Xa
              Y     young_entrepreneur:set:Y
              Θ     young_entrepreneur:set:Θ
              𝑢     young_entrepreneur:function:𝑢
              Γ     young_entrepreneur:correspondence:Γ
              𝑔≻    young_entrepreneur:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE young_entrepreneur / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature         wire          carrier
              in  μ           : finite measure on Xa × Y × Θ
              out μ_repay≻    : finite measure on Xa × Y × Θ
                  μ_default≻  : finite measure on Xa × Y × Θ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
at            (as on the decision builder's card)
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
where         (as on the decision builder's card)
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
operations    #  operation    in  out
              1  Pushforward  μ   μ_repay≻, μ_default≻
                              │ μ_repay≻(B)
                              │   = μ({a, y, θ ∈ Xa × Y × Θ |
                              │         𝑑(a, y, θ) = repay
                              │           ∧ 𝑔_repay≻,𝑘,𝑐(a, y, θ) ∈ B})
                              │ μ_default≻(B)
                              │   = μ({a, y, θ ∈ Xa × Y × Θ |
                              │         𝑑(a, y, θ) = default
                              │           ∧ 𝑔_default≻,𝑘,𝑐(a, y, θ) ∈ B})
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
conditions    Pushforward  (1 − δ) · 𝑘(a, y, θ) + θ · 𝑘(a, y, θ)^ν
                             − (1 + r) · (𝑘(a, y, θ) − a) − 𝑐(a, y, θ)
                           ∈ Xa
              [open: E14] printed unless 𝑐's feasibility, read at
              the point, establishes it
══════════════════════════════════════════════════════════════════════════════
source        position                  statement
              young_entrepreneur.bl:24  a_ye_ea = (1 - δ)*k + θ*k^ν
                                        │ - (1 + r)*(k - a) - c
                                        │ :: [id=budget]
              young_entrepreneur.bl:25  y_ye_ea = y
              young_entrepreneur.bl:26  θ_ye_ea = θ
              young_entrepreneur.bl:29  a_ye_wk = f*k  :: [id=kept_capital]
              young_entrepreneur.bl:30  y_ye_wk = y
              young_entrepreneur.bl:31  θ_ye_wk = θ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
definitions   name  key
              Xa    young_entrepreneur:set:Xa
              Y     young_entrepreneur:set:Y
              Θ     young_entrepreneur:set:Θ
              δ     young_entrepreneur:parameter:δ
              ν     young_entrepreneur:parameter:ν
              r     young_entrepreneur:parameter:r
              𝑔≻    young_entrepreneur:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE young_entrepreneur / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature         wire        carrier
              in  𝑉_repay≻  : Xa × Y × Θ → ℝ
                  𝑉_w≻      : Xa × Y × Θ → ℝ
              out 𝑘         : Xa × Y × Θ → ℝ₊
                  𝑐         : Xa × Y × Θ → ℝ₊₊
                  𝑑         : Xa × Y × Θ → {repay, default}
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
where         𝑔_repay≻    : Xa × Y × Θ × ℝ₊ × ℝ₊₊ → Xa × Y × Θ,
                          𝑔_repay≻(a, y, θ, k, c) = 𝑔≻(a, y, θ, k, c, repay)
              𝑔_default≻  : Xa × Y × Θ × ℝ₊ × ℝ₊₊ → Xa × Y × Θ,
                          𝑔_default≻(a, y, θ, k, c)
                            = 𝑔≻(a, y, θ, k, c, default)
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
operations    #  operation              in        out
              1  Pullback:repay         𝑉_repay≻  𝑉_repay≻ ∘ 𝑔_repay≻
              2  Pullback:default       𝑉_w≻      𝑉_w≻ ∘ 𝑔_default≻
              …  optimality:…           (1)       𝑘, 𝑐
                                        │ [open: E14]
              …  enforcement:…          (1), (2)
                                        │ [open: E14]
              …  repayment:Aggregation  (1), (2)
                (a, y, θ, k, c, d)
                  ↦ (𝑢(c) + 𝑉_repay≻(𝑔_repay≻(a, y, θ, k, c)),
                     𝑉_w≻(𝑔_default≻(a, y, θ, k, c)))[d]
              …  repayment:Solution     (…)       𝑑
                                        │ [open: E14] 𝑑 at (𝑘, 𝑐): the set of
                                        │ maximizers of the tuple over
                                        │ {repay, default}
              …  Evaluation             𝑘, 𝑐, 𝑑   𝑘, 𝑐, 𝑑
══════════════════════════════════════════════════════════════════════════════
source        position                  statement
              young_entrepreneur.bl:44  (k, c) = argmax_{k, c : Γ(a, θ, k)}(
                                        │ 𝑢(c) + V_repay[>])
                                        │ :: [id=optimality]
              young_entrepreneur.bl:45  𝑢(c) + V_repay[>] >= V_w[>]
                                        │ :: [id=enforcement]
              young_entrepreneur.bl:46  d = argmax_{d}(𝑢(c) + V_repay[>],
                                        │ V_w[>])
                                        │ :: [id=repayment]
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
definitions   name  key
              Xa    young_entrepreneur:set:Xa
              Y     young_entrepreneur:set:Y
              Θ     young_entrepreneur:set:Θ
              𝑢     young_entrepreneur:function:𝑢
              Γ     young_entrepreneur:correspondence:Γ
              𝑔≻    young_entrepreneur:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE old_entrepreneur / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature         wire        carrier
              in  𝑉_repay≻  : Xa × Θ → ℝ
                  𝑊_r≻      : Xa → ℝ
              out 𝑉         : Xa × Θ → ℝ
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
at            𝑘  : Xa × Θ → ℝ₊
              𝑐  : Xa × Θ → ℝ₊₊,  𝑐(a, θ) ∈ Γ(a, θ, 𝑘(a, θ))
              𝑑  : Xa × Θ → {repay, default}
              [open: E14] one policy (𝑘, 𝑐, 𝑑) or two; 𝑐's feasibility
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
where         𝑔_repay≻,𝑘,𝑐    : Xa × Θ → Xa × Θ,
                              𝑔_repay≻,𝑘,𝑐(a, θ)
                                = 𝑔≻(a, θ, 𝑘(a, θ), 𝑐(a, θ), repay)
              𝑔_default≻,𝑘,𝑐  : Xa × Θ → Xa,
                              𝑔_default≻,𝑘,𝑐(a, θ)
                                = 𝑔≻(a, θ, 𝑘(a, θ), 𝑐(a, θ), default)
              [open: E5, E14] a section at a label and at a policy
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
operations    #  operation         in        out
              1  Pullback:repay    𝑉_repay≻  𝑉_repay≻ ∘ 𝑔_repay≻,𝑘,𝑐
              2  Pullback:default  𝑊_r≻      𝑊_r≻ ∘ 𝑔_default≻,𝑘,𝑐
              3  Aggregation       (1), (2)  𝑉
                                   │ 𝑉(a, θ)
                                   │   = (𝑢(𝑐(a, θ))
                                   │        + 𝑉_repay≻(𝑔_repay≻,𝑘,𝑐(a, θ)),
                                   │      𝑊_r≻(𝑔_default≻,𝑘,𝑐(a, θ)))[𝑑(a, θ)]
              4  Evaluation        𝑉         𝑉
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
conditions    Aggregation  𝑉(a, θ) ∈ ℝ
══════════════════════════════════════════════════════════════════════════════
source        position                statement
              old_entrepreneur.bl:31  V = (𝑢(c) + V_repay[>], W_r[>])[d]
                                      │ :: [id=value]
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
definitions   name  key
              Xa    old_entrepreneur:set:Xa
              Θ     old_entrepreneur:set:Θ
              𝑢     old_entrepreneur:function:𝑢
              Γ     old_entrepreneur:correspondence:Γ
              𝑔≻    old_entrepreneur:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```text
STAGE old_entrepreneur / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature         wire          carrier
              in  μ           : finite measure on Xa × Θ
              out μ_repay≻    : finite measure on Xa × Θ
                  μ_default≻  : finite measure on Xa
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
at            (as on the decision builder's card)
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
where         (as on the decision builder's card)
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
operations    #  operation    in  out
              1  Pushforward  μ   μ_repay≻, μ_default≻
                              │ μ_repay≻(B)
                              │   = μ({a, θ ∈ Xa × Θ |
                              │         𝑑(a, θ) = repay
                              │           ∧ 𝑔_repay≻,𝑘,𝑐(a, θ) ∈ B})
                              │ μ_default≻(B)
                              │   = μ({a, θ ∈ Xa × Θ |
                              │         𝑑(a, θ) = default
                              │           ∧ 𝑔_default≻,𝑘,𝑐(a, θ) ∈ B})
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
conditions    Pushforward  (1 − δ) · 𝑘(a, θ) + θ · 𝑘(a, θ)^ν
                             − (1 + r) · (𝑘(a, θ) − a) − 𝑐(a, θ) ∈ Xa
              [open: E14] printed unless 𝑐's feasibility, read at
              the point, establishes it
══════════════════════════════════════════════════════════════════════════════
source        position                statement
              old_entrepreneur.bl:22  a_oe_ed = (1 - δ)*k + θ*k^ν
                                      │ - (1 + r)*(k - a) - c
                                      │ :: [id=budget]
              old_entrepreneur.bl:23  θ_oe_ed = θ
              old_entrepreneur.bl:26  a_oe_rt = f*k  :: [id=kept_capital]
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
definitions   name  key
              Xa    old_entrepreneur:set:Xa
              Θ     old_entrepreneur:set:Θ
              δ     old_entrepreneur:parameter:δ
              ν     old_entrepreneur:parameter:ν
              r     old_entrepreneur:parameter:r
              𝑔≻    old_entrepreneur:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The policy card of `old_entrepreneur` is that of `young_entrepreneur` with the decision state (a, θ) ∈ Xa × Θ, the default value 𝑊_r≻ : Xa → ℝ and the lines `old_entrepreneur.bl:39-41`.

### 4.5 The stages the build does not change

`worker.bl` and `retiree.bl` print today as probe 1 records them, and the build changes no card of theirs (E18). The four terminal stages construct today and print as probe 10 records them: `arvl_to_dcsn` one `Pushforward` of the identity map; `cntn_to_dcsn` one `Aggregation`, 𝑉(a, y, θ) = 𝑉≻ with `in 𝑉≻ : {()} → ℝ`, and its `Evaluation`; `dcsn_to_arvl` a `Pullback` along 𝑔≺, an `Aggregation` and an `Evaluation`, as the durables bequest prints them (probe 2).

## 5 The initial diagrams and the builders graphs

**Forward initial diagrams.** `young_choice`: inputs `a_yc≺`, `y_yc≺`, `θ_yc≺`; block `arvl_to_dcsn` with the line boxes `arvl_to_dcsn.1`, `.2` and `.3`; block `dcsn_to_cntn` with the coordinate `d`, holding two bubbles (E23), `dcsn_to_cntn.entrepreneur` with the line boxes `.1` (`a` → `a_ye≻`), `.2` (`y` → `y_ye≻`) and `.3` (`θ` → `θ_ye≻`), and `dcsn_to_cntn.worker` with `.1`, `.2` and `.3` (→ `a_yc_wk≻`, `y_yc_wk≻`, `θ_yc_wk≻`); `a`, `y` and `θ` are copied to both bubbles. The outputs are the six branch fields and no decision state, since no backward line reads one. `old_choice` is the same with `(a_oc≺, θ_oc≺)`, the bubbles `entrepreneur` (`a_oe≻`, `θ_oe≻`) and `retiree` (`a_oc_rt≻`). The four demographic stages have the inputs `a_ed≺, θ_ed≺` and the like with the shocks `y_n`, `θ_n` and `s`; block `dcsn_to_cntn` holds the two bubbles of the labels, and whether `s` enters the block as a wire, as a shock of the forward initial diagram does (ε in `tenure`), or is the coordinate at which the bubbles are read, as `d` is, is [open: E13, E23].

**Backward initial diagrams.** `young_choice`: inputs `V_e≻` and `V_w≻`; block `cntn_to_dcsn`, coordinate `d`, with `choice_value` (`V_e≻`, `V_w≻` → `V`); block `dcsn_to_arvl` with `value` (`V` → `V≺`); block `policy` with `choice` (`V_e≻`, `V_w≻` → `d`), `d` delivered at the boundary (AMD-SG-013 §3); `V_e≻` and `V_w≻` are each read twice and copied. `old_choice` likewise with `W_e≻` and `W_r≻`. The demographic stages: inputs the two branch values; block `cntn_to_dcsn` with `value`, `s` bound by the expectation and no input; block `dcsn_to_arvl` with `value`; no policy block.

**Backward builders graphs.** `cntn_to_dcsn`: `Pullback:<label>` twice, `Aggregation`, `Evaluation`; the two pullbacks' output wires meet the Aggregation as two groups and never as one bundle (E17), which in `young_choice` rests on the bases alone. `dcsn_to_arvl`: `Pullback` along 𝑔≺, then, in the demographic stages only, `Expectation` over `(y_n, θ_n)`, `Aggregation`, `Evaluation`. `policy` of the two choice stages: the two pullbacks, `choice:Aggregation`, `choice:Solution`, `Evaluation`, 𝑑 at the boundary and no wire into a backward builder.

**Forward builders graphs.** `arvl_to_dcsn`: `Pushforward` in the choice stages; `DistributionExtension:y_n`, `DistributionExtension:θ_n`, `Pushforward` in the ageing stages; refused in the death stages (§7). `dcsn_to_cntn`: in the choice stages, `Pushforward` at 𝑑, labeled `𝑔≻,𝑑∗μ` as in `example-tenure.md` §5, with two output wires to the boundary on different bases, never bundled; in the demographic stages, `DistributionExtension:s` and then one `Pushforward` with two output wires.

## 6 The period joins, the orders, the inter-period joins and the drawing of three periods

Probe 4 ([p04_registry.py](probes/p04_registry.py)) computes everything in this section with the package's own functions on the registry of §0, loaded by `load_recipe`, after replacing the eight branching texts by standard stand-ins that declare the same state fields at the arrival and continuation perches, the branch fields of every branch together at the continuation perch and the shocks with their laws. Those fields are all that `period_joins` and `inter_period_joins` read (`packages/bellman/bellman/stage/joins.py:32-46`), and they are what `fields()` answers for a branching stage under §3 item 9 of the unification. The lists below are therefore the build's output; only the label of a join from a branch field, which the first build does not print (E26), is added by hand.

**`period_joins(periods[h])` for h ≥ 1** records 31 joins and 9 outputs. Every join comes from a branch field, so every join answers a label through `branches(stage)` (E26):

| Source stage | Label | Joins |
|---|---|---|
| `worker_ageing` | young | `a_wa_yc → young_choice:a_yc`, `y_wa_yc → young_choice:y_yc`, `θ_wa_yc → young_choice:θ_yc` |
| `worker_ageing` | old | `a_wa_rt → retiree:a_rt` |
| `entrepreneur_ageing` | young | `a_ea_yc → young_choice:a_yc`, `y_ea_yc → young_choice:y_yc`, `θ_ea_yc → young_choice:θ_yc` |
| `entrepreneur_ageing` | old | `a_ea_oc → old_choice:a_oc`, `θ_ea_oc → old_choice:θ_oc` |
| `entrepreneur_death` | survive | `a_ed_oc → old_choice:a_oc`, `θ_ed_oc → old_choice:θ_oc` |
| `entrepreneur_death` | die | `a_ed_yc → young_choice:a_yc`, `y_ed_yc → young_choice:y_yc`, `θ_ed_yc → young_choice:θ_yc` |
| `retiree_death` | survive | `a_rd_rt → retiree:a_rt` |
| `retiree_death` | die | `a_rd_yc → young_choice:a_yc`, `y_rd_yc → young_choice:y_yc`, `θ_rd_yc → young_choice:θ_yc` |
| `young_choice` | entrepreneur | `a_ye → young_entrepreneur:a_ye`, `y_ye → young_entrepreneur:y_ye`, `θ_ye → young_entrepreneur:θ_ye` (equal names) |
| `young_choice` | worker | `a_yc_wk → worker:a_wk`, `y_yc_wk → worker:y_wk`, `θ_yc_wk → worker:θ_wk` |
| `old_choice` | entrepreneur | `a_oe → old_entrepreneur:a_oe`, `θ_oe → old_entrepreneur:θ_oe` (equal names) |
| `old_choice` | retiree | `a_oc_rt → retiree:a_rt` |
| `young_entrepreneur` | default | `a_ye_wk → worker:a_wk`, `y_ye_wk → worker:y_wk`, `θ_ye_wk → worker:θ_wk` |
| `old_entrepreneur` | default | `a_oe_rt → retiree:a_rt` |

The five equal-name joins need no connector; the other 26 come from the twelve connectors of `period.yml`. The outputs are `old_entrepreneur:a_oe_ed`, `old_entrepreneur:θ_oe_ed` (repay), `retiree:a_rt_rd`, `worker:a_wk_wa`, `worker:y_wk_wa`, `worker:θ_wk_wa` and `young_entrepreneur:a_ye_ea`, `young_entrepreneur:y_ye_ea`, `young_entrepreneur:θ_ye_ea` (repay). Several sources reach one arrival field at four stages: four at each of `young_choice:a_yc`, `y_yc` and `θ_yc`, four at `retiree:a_rt`, two at each of `old_choice:a_oc` and `θ_oc`, two at each of `worker:a_wk`, `y_wk` and `θ_wk`. No continuation field joins two arrival fields, E16's fan-out rule, so the sources of each arrival field are disjoint sub-populations and its arrival measure is their sum (E25).

**`period_joins(periods[0])`** records the same 31 joins and 9 more from the terminal connector, 40 in all, and no output: `worker:a_wk_wa → terminal_worker:a_tw`, `worker:y_wk_wa → terminal_worker:y_tw`, `worker:θ_wk_wa → terminal_worker:θ_tw`, `young_entrepreneur:a_ye_ea → terminal_young_entrepreneur:a_ty`, `young_entrepreneur:y_ye_ea → terminal_young_entrepreneur:y_ty`, `young_entrepreneur:θ_ye_ea → terminal_young_entrepreneur:θ_ty` (repay), `old_entrepreneur:a_oe_ed → terminal_old_entrepreneur:a_to`, `old_entrepreneur:θ_oe_ed → terminal_old_entrepreneur:θ_to` (repay) and `retiree:a_rt_rd → terminal_retiree:a_tr`. Each terminal stage takes one source, so no terminal arrival measure is a sum.

**The orders** (`computable_together`, `forward_order`, `backward_order`). For h ≥ 1 the layers are

```text
[[entrepreneur_ageing, entrepreneur_death, retiree_death, worker_ageing],
 [old_choice, young_choice],
 [old_entrepreneur, young_entrepreneur],
 [retiree, worker]]
```

the forward order their concatenation and the backward order its reverse, `worker, retiree, young_entrepreneur, old_entrepreneur, young_choice, old_choice, worker_ageing, retiree_death, entrepreneur_death, entrepreneur_ageing`. For h = 0 the layers are

```text
[[entrepreneur_ageing, entrepreneur_death, retiree_death, worker_ageing],
 [old_choice, young_choice],
 [old_entrepreneur, young_entrepreneur],
 [retiree, terminal_old_entrepreneur, terminal_young_entrepreneur, worker],
 [terminal_retiree, terminal_worker]]
```

and the backward order is `terminal_worker, terminal_retiree, worker, terminal_young_entrepreneur, terminal_old_entrepreneur, retiree, young_entrepreneur, old_entrepreneur, young_choice, old_choice, worker_ageing, retiree_death, entrepreneur_death, entrepreneur_ageing`. The two terminal entrepreneur stages stand in the fourth layer beside the worker and the retiree, because the entrepreneurs, whose repay branches they take, are computed a layer before the stages their default branches reach. There is no cycle: no stage of the year continues to a field a demographic stage arrives at (`economics.md:135` found the same with the deleted period factory).

**`inter_period_joins(inter_connectors[h], periods[h + 1], periods[h])`** records the same nine joins for every h, h = 0 included, in the mapping's order:

```text
worker:a_wk_wa             → worker_ageing:a_wa
worker:y_wk_wa             → worker_ageing:y_wa
worker:θ_wk_wa             → worker_ageing:θ_wa
young_entrepreneur:a_ye_ea → entrepreneur_ageing:a_ea
young_entrepreneur:y_ye_ea → entrepreneur_ageing:y_ea
young_entrepreneur:θ_ye_ea → entrepreneur_ageing:θ_ea
old_entrepreneur:a_oe_ed   → entrepreneur_death:a_ed
old_entrepreneur:θ_oe_ed   → entrepreneur_death:θ_ed
retiree:a_rt_rd            → retiree_death:a_rd
```

Each key is one of the nine outputs of `periods[h + 1]`, the fields that leave that period, which the present `inter_period_joins` requires (commit 721f09226 of step D); each value is an arrival field of a demographic stage of `periods[h]`, which no join within `periods[h]` supplies; no key joins two arrival fields (E16). In `periods[0]` the names `a_wa`, `a_ea`, `a_ed`, `a_rd` and the rest are the demographic stages' alone, the terminal stages arriving at `a_tw`, `a_ty`, `a_to` and `a_tr`, so the mapping reaches no terminal stage. The earliest period, `periods[n − 1]`, has its demographic stages' arrival fields supplied by no join: they carry the initial distribution a forward computation needs (`economics.md:135`).

**`draw_trellis(trellis, periods=[0, 1, 2])`** (`packages/bellman/bellman/display/trellis.py:81-140`) writes the head of `dot_head` with `rankdir="LR"` and the title naming the two directions, the three clusters in the order 2, 1, 0, and then the eighteen inter-period wires. The registry holds no `last_age`, so a cluster's label is `periods[h]: h = h` alone. The text, as probe 4 prints it:

```text
digraph {
  graph [rankdir="LR", bgcolor="white", pad="0.12", nodesep="0.18", ranksep="0.22", fontname="Inter,Helvetica Neue,Helvetica,Arial,sans-serif", fontsize="9", fontcolor="#64717d", splines="spline", compound="true", label="economic time runs left to right, the backward computation right to left;\nthe terminal period periods[0] stands at the right", labelloc="t", labeljust="l", fontsize="10.5", fontcolor="#1f476b"];
  node [fontname="Inter,Helvetica Neue,Helvetica,Arial,sans-serif", fontsize="10", shape="box", style="rounded", color="#1f476b", fontcolor="#1f476b", penwidth="1.1", margin="0.09,0.045", height="0.30"];
  edge [fontname="Inter,Helvetica Neue,Helvetica,Arial,sans-serif", fontsize="9", fontcolor="#64717d", color="#8a96a3", penwidth="0.9", arrowsize="0.6", arrowhead="normal"];
  subgraph "cluster_2" {
    graph [label="periods[2]: h = 2", labelloc="t", labeljust="l"];
    "2:entrepreneur_ageing" [label="entrepreneur_ageing"];
    "2:entrepreneur_death" [label="entrepreneur_death"];
    "2:retiree_death" [label="retiree_death"];
    "2:worker_ageing" [label="worker_ageing"];
    "2:old_choice" [label="old_choice"];
    "2:young_choice" [label="young_choice"];
    "2:old_entrepreneur" [label="old_entrepreneur"];
    "2:young_entrepreneur" [label="young_entrepreneur"];
    "2:retiree" [label="retiree"];
    "2:worker" [label="worker"];
    "2:entrepreneur_ageing" -> "2:old_choice" [label="a_ea_oc → a_oc"];
    "2:entrepreneur_ageing" -> "2:young_choice" [label="a_ea_yc → a_yc"];
    "2:entrepreneur_ageing" -> "2:young_choice" [label="y_ea_yc → y_yc"];
    "2:entrepreneur_ageing" -> "2:old_choice" [label="θ_ea_oc → θ_oc"];
    "2:entrepreneur_ageing" -> "2:young_choice" [label="θ_ea_yc → θ_yc"];
    "2:entrepreneur_death" -> "2:old_choice" [label="a_ed_oc → a_oc"];
    "2:entrepreneur_death" -> "2:young_choice" [label="a_ed_yc → a_yc"];
    "2:entrepreneur_death" -> "2:young_choice" [label="y_ed_yc → y_yc"];
    "2:entrepreneur_death" -> "2:old_choice" [label="θ_ed_oc → θ_oc"];
    "2:entrepreneur_death" -> "2:young_choice" [label="θ_ed_yc → θ_yc"];
    "2:old_choice" -> "2:retiree" [label="a_oc_rt → a_rt"];
    "2:old_choice" -> "2:old_entrepreneur" [label="a_oe"];
    "2:old_choice" -> "2:old_entrepreneur" [label="θ_oe"];
    "2:old_entrepreneur" -> "2:retiree" [label="a_oe_rt → a_rt"];
    "2:retiree_death" -> "2:retiree" [label="a_rd_rt → a_rt"];
    "2:retiree_death" -> "2:young_choice" [label="a_rd_yc → a_yc"];
    "2:retiree_death" -> "2:young_choice" [label="y_rd_yc → y_yc"];
    "2:retiree_death" -> "2:young_choice" [label="θ_rd_yc → θ_yc"];
    "2:worker_ageing" -> "2:retiree" [label="a_wa_rt → a_rt"];
    "2:worker_ageing" -> "2:young_choice" [label="a_wa_yc → a_yc"];
    "2:worker_ageing" -> "2:young_choice" [label="y_wa_yc → y_yc"];
    "2:worker_ageing" -> "2:young_choice" [label="θ_wa_yc → θ_yc"];
    "2:young_choice" -> "2:worker" [label="a_yc_wk → a_wk"];
    "2:young_choice" -> "2:young_entrepreneur" [label="a_ye"];
    "2:young_choice" -> "2:worker" [label="y_yc_wk → y_wk"];
    "2:young_choice" -> "2:young_entrepreneur" [label="y_ye"];
    "2:young_choice" -> "2:worker" [label="θ_yc_wk → θ_wk"];
    "2:young_choice" -> "2:young_entrepreneur" [label="θ_ye"];
    "2:young_entrepreneur" -> "2:worker" [label="a_ye_wk → a_wk"];
    "2:young_entrepreneur" -> "2:worker" [label="y_ye_wk → y_wk"];
    "2:young_entrepreneur" -> "2:worker" [label="θ_ye_wk → θ_wk"];
  }
  subgraph "cluster_1" {
    graph [label="periods[1]: h = 1", labelloc="t", labeljust="l"];
    "1:entrepreneur_ageing" [label="entrepreneur_ageing"];
    "1:entrepreneur_death" [label="entrepreneur_death"];
    "1:retiree_death" [label="retiree_death"];
    "1:worker_ageing" [label="worker_ageing"];
    "1:old_choice" [label="old_choice"];
    "1:young_choice" [label="young_choice"];
    "1:old_entrepreneur" [label="old_entrepreneur"];
    "1:young_entrepreneur" [label="young_entrepreneur"];
    "1:retiree" [label="retiree"];
    "1:worker" [label="worker"];
    "1:entrepreneur_ageing" -> "1:old_choice" [label="a_ea_oc → a_oc"];
    "1:entrepreneur_ageing" -> "1:young_choice" [label="a_ea_yc → a_yc"];
    "1:entrepreneur_ageing" -> "1:young_choice" [label="y_ea_yc → y_yc"];
    "1:entrepreneur_ageing" -> "1:old_choice" [label="θ_ea_oc → θ_oc"];
    "1:entrepreneur_ageing" -> "1:young_choice" [label="θ_ea_yc → θ_yc"];
    "1:entrepreneur_death" -> "1:old_choice" [label="a_ed_oc → a_oc"];
    "1:entrepreneur_death" -> "1:young_choice" [label="a_ed_yc → a_yc"];
    "1:entrepreneur_death" -> "1:young_choice" [label="y_ed_yc → y_yc"];
    "1:entrepreneur_death" -> "1:old_choice" [label="θ_ed_oc → θ_oc"];
    "1:entrepreneur_death" -> "1:young_choice" [label="θ_ed_yc → θ_yc"];
    "1:old_choice" -> "1:retiree" [label="a_oc_rt → a_rt"];
    "1:old_choice" -> "1:old_entrepreneur" [label="a_oe"];
    "1:old_choice" -> "1:old_entrepreneur" [label="θ_oe"];
    "1:old_entrepreneur" -> "1:retiree" [label="a_oe_rt → a_rt"];
    "1:retiree_death" -> "1:retiree" [label="a_rd_rt → a_rt"];
    "1:retiree_death" -> "1:young_choice" [label="a_rd_yc → a_yc"];
    "1:retiree_death" -> "1:young_choice" [label="y_rd_yc → y_yc"];
    "1:retiree_death" -> "1:young_choice" [label="θ_rd_yc → θ_yc"];
    "1:worker_ageing" -> "1:retiree" [label="a_wa_rt → a_rt"];
    "1:worker_ageing" -> "1:young_choice" [label="a_wa_yc → a_yc"];
    "1:worker_ageing" -> "1:young_choice" [label="y_wa_yc → y_yc"];
    "1:worker_ageing" -> "1:young_choice" [label="θ_wa_yc → θ_yc"];
    "1:young_choice" -> "1:worker" [label="a_yc_wk → a_wk"];
    "1:young_choice" -> "1:young_entrepreneur" [label="a_ye"];
    "1:young_choice" -> "1:worker" [label="y_yc_wk → y_wk"];
    "1:young_choice" -> "1:young_entrepreneur" [label="y_ye"];
    "1:young_choice" -> "1:worker" [label="θ_yc_wk → θ_wk"];
    "1:young_choice" -> "1:young_entrepreneur" [label="θ_ye"];
    "1:young_entrepreneur" -> "1:worker" [label="a_ye_wk → a_wk"];
    "1:young_entrepreneur" -> "1:worker" [label="y_ye_wk → y_wk"];
    "1:young_entrepreneur" -> "1:worker" [label="θ_ye_wk → θ_wk"];
  }
  subgraph "cluster_0" {
    graph [label="periods[0]: h = 0", labelloc="t", labeljust="l"];
    "0:entrepreneur_ageing" [label="entrepreneur_ageing"];
    "0:entrepreneur_death" [label="entrepreneur_death"];
    "0:retiree_death" [label="retiree_death"];
    "0:worker_ageing" [label="worker_ageing"];
    "0:old_choice" [label="old_choice"];
    "0:young_choice" [label="young_choice"];
    "0:old_entrepreneur" [label="old_entrepreneur"];
    "0:young_entrepreneur" [label="young_entrepreneur"];
    "0:retiree" [label="retiree"];
    "0:terminal_old_entrepreneur" [label="terminal_old_entrepreneur"];
    "0:terminal_young_entrepreneur" [label="terminal_young_entrepreneur"];
    "0:worker" [label="worker"];
    "0:terminal_retiree" [label="terminal_retiree"];
    "0:terminal_worker" [label="terminal_worker"];
    "0:entrepreneur_ageing" -> "0:old_choice" [label="a_ea_oc → a_oc"];
    "0:entrepreneur_ageing" -> "0:young_choice" [label="a_ea_yc → a_yc"];
    "0:entrepreneur_ageing" -> "0:young_choice" [label="y_ea_yc → y_yc"];
    "0:entrepreneur_ageing" -> "0:old_choice" [label="θ_ea_oc → θ_oc"];
    "0:entrepreneur_ageing" -> "0:young_choice" [label="θ_ea_yc → θ_yc"];
    "0:entrepreneur_death" -> "0:old_choice" [label="a_ed_oc → a_oc"];
    "0:entrepreneur_death" -> "0:young_choice" [label="a_ed_yc → a_yc"];
    "0:entrepreneur_death" -> "0:young_choice" [label="y_ed_yc → y_yc"];
    "0:entrepreneur_death" -> "0:old_choice" [label="θ_ed_oc → θ_oc"];
    "0:entrepreneur_death" -> "0:young_choice" [label="θ_ed_yc → θ_yc"];
    "0:old_choice" -> "0:retiree" [label="a_oc_rt → a_rt"];
    "0:old_choice" -> "0:old_entrepreneur" [label="a_oe"];
    "0:old_choice" -> "0:old_entrepreneur" [label="θ_oe"];
    "0:old_entrepreneur" -> "0:terminal_old_entrepreneur" [label="a_oe_ed → a_to"];
    "0:old_entrepreneur" -> "0:retiree" [label="a_oe_rt → a_rt"];
    "0:old_entrepreneur" -> "0:terminal_old_entrepreneur" [label="θ_oe_ed → θ_to"];
    "0:retiree" -> "0:terminal_retiree" [label="a_rt_rd → a_tr"];
    "0:retiree_death" -> "0:retiree" [label="a_rd_rt → a_rt"];
    "0:retiree_death" -> "0:young_choice" [label="a_rd_yc → a_yc"];
    "0:retiree_death" -> "0:young_choice" [label="y_rd_yc → y_yc"];
    "0:retiree_death" -> "0:young_choice" [label="θ_rd_yc → θ_yc"];
    "0:worker" -> "0:terminal_worker" [label="a_wk_wa → a_tw"];
    "0:worker" -> "0:terminal_worker" [label="y_wk_wa → y_tw"];
    "0:worker" -> "0:terminal_worker" [label="θ_wk_wa → θ_tw"];
    "0:worker_ageing" -> "0:retiree" [label="a_wa_rt → a_rt"];
    "0:worker_ageing" -> "0:young_choice" [label="a_wa_yc → a_yc"];
    "0:worker_ageing" -> "0:young_choice" [label="y_wa_yc → y_yc"];
    "0:worker_ageing" -> "0:young_choice" [label="θ_wa_yc → θ_yc"];
    "0:young_choice" -> "0:worker" [label="a_yc_wk → a_wk"];
    "0:young_choice" -> "0:young_entrepreneur" [label="a_ye"];
    "0:young_choice" -> "0:worker" [label="y_yc_wk → y_wk"];
    "0:young_choice" -> "0:young_entrepreneur" [label="y_ye"];
    "0:young_choice" -> "0:worker" [label="θ_yc_wk → θ_wk"];
    "0:young_choice" -> "0:young_entrepreneur" [label="θ_ye"];
    "0:young_entrepreneur" -> "0:terminal_young_entrepreneur" [label="a_ye_ea → a_ty"];
    "0:young_entrepreneur" -> "0:worker" [label="a_ye_wk → a_wk"];
    "0:young_entrepreneur" -> "0:terminal_young_entrepreneur" [label="y_ye_ea → y_ty"];
    "0:young_entrepreneur" -> "0:worker" [label="y_ye_wk → y_wk"];
    "0:young_entrepreneur" -> "0:terminal_young_entrepreneur" [label="θ_ye_ea → θ_ty"];
    "0:young_entrepreneur" -> "0:worker" [label="θ_ye_wk → θ_wk"];
  }
  "2:worker" -> "1:worker_ageing" [label="inter_connectors[1]\na_wk_wa → a_wa"];
  "2:worker" -> "1:worker_ageing" [label="inter_connectors[1]\ny_wk_wa → y_wa"];
  "2:worker" -> "1:worker_ageing" [label="inter_connectors[1]\nθ_wk_wa → θ_wa"];
  "2:young_entrepreneur" -> "1:entrepreneur_ageing" [label="inter_connectors[1]\na_ye_ea → a_ea"];
  "2:young_entrepreneur" -> "1:entrepreneur_ageing" [label="inter_connectors[1]\ny_ye_ea → y_ea"];
  "2:young_entrepreneur" -> "1:entrepreneur_ageing" [label="inter_connectors[1]\nθ_ye_ea → θ_ea"];
  "2:old_entrepreneur" -> "1:entrepreneur_death" [label="inter_connectors[1]\na_oe_ed → a_ed"];
  "2:old_entrepreneur" -> "1:entrepreneur_death" [label="inter_connectors[1]\nθ_oe_ed → θ_ed"];
  "2:retiree" -> "1:retiree_death" [label="inter_connectors[1]\na_rt_rd → a_rd"];
  "1:worker" -> "0:worker_ageing" [label="inter_connectors[0]\na_wk_wa → a_wa"];
  "1:worker" -> "0:worker_ageing" [label="inter_connectors[0]\ny_wk_wa → y_wa"];
  "1:worker" -> "0:worker_ageing" [label="inter_connectors[0]\nθ_wk_wa → θ_wa"];
  "1:young_entrepreneur" -> "0:entrepreneur_ageing" [label="inter_connectors[0]\na_ye_ea → a_ea"];
  "1:young_entrepreneur" -> "0:entrepreneur_ageing" [label="inter_connectors[0]\ny_ye_ea → y_ea"];
  "1:young_entrepreneur" -> "0:entrepreneur_ageing" [label="inter_connectors[0]\nθ_ye_ea → θ_ea"];
  "1:old_entrepreneur" -> "0:entrepreneur_death" [label="inter_connectors[0]\na_oe_ed → a_ed"];
  "1:old_entrepreneur" -> "0:entrepreneur_death" [label="inter_connectors[0]\nθ_oe_ed → θ_ed"];
  "1:retiree" -> "0:retiree_death" [label="inter_connectors[0]\na_rt_rd → a_rd"];
}
```

No plain-label sink is drawn: every output of `periods[1]` and `periods[2]` is read by a wire and `periods[0]` has none; no invisible edge is drawn, each adjacent pair having wires. `str(drawing)` lists the 34 boxes, the fourteen of `periods[0]` in the forward order and then the ten of `periods[1]` and of `periods[2]`. In the first build the label E26 adds to an arrow from a branch field, `young: a_wa_yc → a_yc`, is not printed. `draw_period(trellis, 0)` writes the statements of `cluster_0` alone, the nodes named without the `0:` prefix, under the title `periods[0]`.

## 7 What the present package prints instead today

Each of the eight branching files is refused at its first nested block (probe 1):

```text
young_choice.bl:14:5-18:6        (address 'dcsn_to_cntn.entrepreneur')
old_choice.bl:12:5-15:6          (address 'dcsn_to_cntn.entrepreneur')
young_entrepreneur.bl:23:5-27:6  (address 'dcsn_to_cntn.repay')
old_entrepreneur.bl:21:5-24:6    (address 'dcsn_to_cntn.repay')
entrepreneur_death.bl:30:5-33:6  (address 'dcsn_to_cntn.survive')
retiree_death.bl:30:5-32:6       (address 'dcsn_to_cntn.survive')
worker_ageing.bl:29:5-33:6       (address 'dcsn_to_cntn.young')
entrepreneur_ageing.bl:29:5-33:6 (address 'dcsn_to_cntn.young')
```

each with the sentence "make_stage cannot construct this nested block: task B02 (branching construction) adds its construction rule (…; rule not-constructed)". `load_recipe` of [registry/spec.yml](registry/spec.yml) loads the three periods (§0), since loading elaborates nothing (A46); `elaborate_trellis` refuses at the first distinct text in the order of positions, `worker_ageing.bl:29:5-33:6`, with the note "Affected stage occurrences: periods[0].stages['worker_ageing'], periods[1].stages['worker_ageing'], periods[2].stages['worker_ageing']" (probe 4).

Four refusals that no branching build removes, found by the probes on the stages that construct and on the stand-ins, which keep the files' declarations:

- **The two death stages' forward builders.** `y_n ~ Invariant(P_y, y_grid)` (`entrepreneur_death.bl:17`, `retiree_death.bl:17`) and `θ_n ~ Invariant(…)` (`retiree_death.bl:19`): "the forward measures are not constructed: the distribution of y_n is written with the family 'Invariant', whose result set is not declared …; under the rule not-constructed the forward measure is extended only by the families N, LogNormal, Uniform, TruncatedNormal, TruncatedLogNormal, TypeIExtremeValue, DiscreteMarkov, MarkovChain, Mixture, Categorical, Bernoulli" (probe 5). The backward builders construct; `elaborate_trellis` admits the stage with its forward builders graph refused (probe 4 elaborates the stand-ins that keep these laws).
- **Calibration of the unreported prices.** Without a fill, `calibrate` refuses `w` on the worker and `p` on the retiree, "the calibration source supplies no value for it"; with `fill={"calibration": {"w": …, "τ": …, "p": …}}` both bind (probe 5).
- **Calibration of `P_y` and `y_grid`.** The four demographic stages declare `P_y : [0,1]` and `y_grid : ℝ₊₊`, standing in for the matrix and the vector (`economics.md:107`), and `calibrate` refuses the matrix: "the value [[0.7376, …]] lies outside the declared set [0, 1]" (probe 5, on the stand-ins, whose declarations are the files').
- **Configuration of the null settings.** `configure` refuses the worker's and the retiree's methods, "option 'orders': {'m': None} does not give positive integers …; write positive integer orders at actual coordinates (rule method-option-value)", the settings file giving `n_a: null` as the paper reports no value (probe 5).

The four terminal stages construct (probe 10), and `terminal_worker` calibrates, methodizes and configures with its empty mappings (probe 5).

Four statements of `economics.md` are older than the package. `economics.md:182` and `entrepreneur_ageing.md:73` report the law of `s` refused for `Categorical`; `Categorical` is now an admitted family, and only `Invariant` refuses. `economics.md:182` reports that the conditioning on last year's abilities "is written but not read"; the stand-ins print the kernels `P_{y_n|y_wa}` and `P_{θ_n|θ_wa}`. `economics.md:194` reports that "every method target resolved and the settings were bound"; configuration now refuses the null orders. `economics.md:183` reports the entrepreneurs refused at `policy.optimality` because "this statement has a Tuple as its left side"; written with one forward block, they are now refused there under `output-defined`, "the equation depends on k, but no input or earlier equation supplies that field" (probe 9).
