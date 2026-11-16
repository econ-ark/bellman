# The example on paper: the childbearing model of de la Croix and Pommeret (2021) under the unification of branching

23 September 2026. Written from the five stage files of the application `de-la-croix-pommeret-2021`, its `period.yml`, `trellis.yml`, `calibration.yml` and `theory.md`, under [`branching-unified.md`](../../branching-unified.md) (the E-numbers are its §4) and in the form of [`example-tenure.md`](../../example-tenure.md), whose settled points are cited and not repeated. The model has two branching stages in one period, one of each kind: `attempt`, a choice between trying for a child now and waiting one date, selected by a control; and `fecundity`, the success or failure of the attempt, selected by a shock. The branching stages are refused today (§7), so their cards are on paper. The three consumption stages and the three terminal stages construct today. So do flattened stand-ins of the two branching stages: standard stages with the same state fields, not faithful to the model, since a woman would be in both branches at once. The joins, the orders and the drawing of §6 are the package's own output on those stand-ins. The probes are under [`probes/`](probes/), and every `.out` file there was written at commit 4d976498e. The checkout moved several times during the work; the only move that touched code these probes read is `inter_period_joins` at 1b643edc2, noted in §6.

## 1 The registry, the number of periods and the edits

**n = 36.** The paper's horizon is infinite (`theory.md:15`), and the application's trellis file writes one repeating period with "boundary data after the terminal one" (`trellis.yml:3-6`). The period repeats unchanged, age being a state field and not a period index (D15, "The index convention"), so the whole trellis is a finite truncation of a stationary model. The length chosen is the lattice of attempt dates 0, Δ, …, T with Δ = 1 year (`calibration.yml:7-10, 24`) and T = 35, the menopause age in model time (`calibration.yml:17-19`; `theory.md:143-146`; the paper, p. 15), above which the paper sets the fecundity schedule to zero (`theory.md:189-193`). That is T/Δ + 1 = 36 dates. `periods[h]` is model time 35 − h: `periods[35]` is date 0, where the forward recursion starts from initial wealth a0 (`calibration.yml:20-22`), and `periods[0]` is date T. The schedule 𝜋 of `fecundity.bl:18` has no cut-off at T (`theory.md:221-223`), so T enters the trellis's length and nothing else. The choice of the truncation is AAS's: question 2 of the findings returned with this example.

The registry is [`registry/`](registry/), in the layout of `applications/durables/` (AMD-FAC-002 §5):

| File | From the application | Edit and the rule that requires it |
|---|---|---|
| `stages/cons_wait.bl`, `stages/cons_mother.bl`, `stages/cons_childless.bl` | the files of the same name | none; byte for byte |
| `stages/attempt.bl` | `attempt.bl` | line 40: the policy's output `(n) : !dcsn` becomes `(n : {try, wait} @ !ctrl) : !dcsn`. §2 item 1 of the unification: the policy block "declares `(d : {l₁, …, lₙ} @ !ctrl) : !dcsn`", as `ret_choice.bl:24` and `tenure.bl:46` write it. The present package accepts the output without the declaration (probe 3, which found nothing else in the file refused), so the edit is of form alone. |
| `stages/fecundity.bl` | `fecundity.bl` | line 21: `s ~ Bernoulli(𝜋(age_fecd))` becomes `s ~ Categorical((𝜋(age_fecd), 1 - 𝜋(age_fecd)))`, its annotation saying that the probabilities are in the order of the labels. §2 item 2: the label is a shock with `s ~ Categorical((p, 1 − p))`, as `applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl:21` writes it. The edit also keeps the file's economics. Under the package's family convention (AMD-SG-010 §3; `family_convention` in `packages/bellman/bellman/distributions/shocks.py`), `Bernoulli(p)` draws "the second of the two declared points" with probability p, which here is `childless` (probe 4). That is the inverse of the file's own statement that success, the motherhood regime, has probability π (`fecundity.bl:3-6`). Line 20's role word, `s : {mother, childless} @ !shck`, is kept: the language admits `!shck` on any shock beside its law (`packages/bellman/bellman/stage/build.py:44`), and §2 item 2 does not exclude it. |
| `stages/terminal_wait.bl`, `stages/terminal_mother.bl`, `stages/terminal_childless.bl` | new | §5 (R12; E15) |
| `period.yml` | `period.yml` | none; the template of `periods[1]` to `periods[35]` |
| `trellis.yml` | `trellis.yml` | written afresh: `periods[0]` written out with the three terminal stages and one flat connector to them in the period's own entry (E15; A38), the template repeated 35 times, and the application's one inter-period mapping unchanged. The application's comment cites the ruling of 16 July 2026 in a file that does not exist; the registry's comment cites E16, E25 and the ruling's record. |
| `spec.yml` | new | one calibration list with the slot `$fill` for each of the five stages; the terminal stages `periods: [0, 0]`, with no source; no settings or methods source, since the paper reports no numerical scheme (`theory.md:147-148`) |
| `calibration/childbearing.yml` | `calibration.yml` | moved, unchanged. ω stays unbound, the paper giving the taste for children as a distribution across women (`calibration.yml:13-16`), so the verbs need `fill={"calibration": {"ω": …}}` (§6). |

## 2 `attempt`, selected by a control

### 2.1 The fields at the perches, as the file declares them

`Xa := ℝ₊₊` and `Xt := ℝ₊` (`attempt.bl:9-10`).

| Perch | State fields | Value fields | Other |
|---|---|---|---|
| ≺ arrival (`attempt.bl:14, 35`) | `a_att : Xa`, `age_att : Xt` | `V[<] : [-inf, inf)`, `dV[<] : ℝ₊₊` | |
| ∼ decision (`:14, 19, 30`) | `a_attd : Xa`, `age_attd : Xt` | `V : [-inf, inf)`, `dV : ℝ₊₊` | `n : !ctrl @ {try, wait}` |
| ≻ try (`:20, 30`) | `a_try : Xa`, `age_try : Xt` | `V_try[>] : [-inf, inf)`, `dV_try[>] : ℝ₊₊` | |
| ≻ wait (`:24, 30`) | `a_next : Xa`, `age_next : Xt` | `V_wait[>] : [-inf, inf)`, `dV_wait[>] : ℝ₊₊` | |

The continuation state space is X_try ⊔ X_wait, where X_try = X_wait = Xa × Xt as sets and the two summands are distinct (E1, E24). This is the case `example-tenure.md` does not meet: tenure's two summands have different dimensions, while attempt's have one set. Each continuation value's base is the summand at its position in the selection tuples of `attempt.bl:31-32, 41`, position one `try` and position two `wait` (E6). The equal sets make the position the only evidence for the base.

### 2.2 The two branches and what selects them

The block `dcsn_to_cntn` (`attempt.bl:19-28`) reads `(a_attd, age_attd)` at the coordinate `n`. Read at `n = try`: `a_try = a_attd`, `age_try = age_attd`. Read at `n = wait`: `a_next = a_attd`, `age_next = age_attd + Δ`. The policy 𝑛 : Xa × Xt → {try, wait} is defined by the operative line `n = argmax_{n}(V_try[>], V_wait[>])` (`:41`), and every label is feasible at every state (E7). The file's schedule has no cut-off, and in the paper trying above T is worthless, not infeasible. 𝑛 routes the forward measure (E3) and selects the backward values (E2). The value and the marginal value select the file's kernels at the policy (E10), `V = (V_try[>], V_wait[>])[n]` and `dV = (dV_try[>], dV_wait[>])[n]` (`:31-32`). The policy's maximand is the value line's tuple in label order, as E30 requires (`:31` and `:41`).

### 2.3 The records the fold would write

**Definitions.** One law, `attempt:g:dcsn_to_cntn`: 𝑔≻ : Xa × Xt × {try, wait} → (Xa × Xt) ⊔ (Xa × Xt). It holds the four nested lines with their labels as conditions, n = try or n = wait (E4). Its sections 𝑔_try≻ and 𝑔_wait≻ are abbreviations of the builders that read them (E5). There are four line records at the addresses `item_addresses` gives (probe 5, part 4): `dcsn_to_cntn.try.wealth`, `dcsn_to_cntn.try.age`, `dcsn_to_cntn.wait.wealth` and `dcsn_to_cntn.wait.age`. The file writes one statement id, `wealth` or `age`, in both branches, so only the label in the address tells the records apart. This is why §3 item 3 keys the records by `item_addresses`, after the layer audit's H2; tenure's ids differ across its branches, so tenure alone does not test it. The aggregator `attempt:G:cntn_to_dcsn` is the pairing of the two selection kernels, each a tuple indexed by n. On the stand-in the package already records it as `((V_try≻, V_wait≻)[n], (dV_try≻, dV_wait≻)[n])` (probe 7). `attempt:G:policy` is the maximand's kernel. `BlockData.branch_labels = ("try", "wait")`. `branches(attempt)` answers `{try: (a_try, age_try), wait: (a_next, age_next)}`, once corrected to each nested block's own outputs (E12). E27's classifier answers the choice, `n` being a `!ctrl` coordinate. The name of that query is not yet fixed.

**Operations.** Backward `cntn_to_dcsn`: `Pullback:try`, `Pullback:wait`, `Aggregation`, and `Evaluation` at 𝑛 (§2.4). Backward `dcsn_to_arvl`: `Pullback` along 𝑔≺, `Aggregation` and `Evaluation`, the identity 𝑔≺ carrying no shock, as the package prints it for `cons_wait` (probe 1). Policy: the two pullbacks, `choice:Aggregation`, `choice:Solution` and `Evaluation`. Forward `arvl_to_dcsn`: `Pushforward`. Forward `dcsn_to_cntn`: one `Pushforward` at 𝑛 with two outputs.

**Conditions, as terms.** On the Aggregation, the memberships of K49. On the Pushforward, each nested line's range at the source point (K65). All four are established by the declared sets and stay on `obligations()`: `a_attd ∈ Xa`, `age_attd ∈ Xt`, and `age_attd + Δ ∈ Xt`, since age_attd ∈ ℝ₊ and Δ ∈ ℝ₊₊. This sum is counted as established on the same ground as `w_adj`'s in `example-tenure.md` §3. So the forward card prints no condition. The conservation identity μ_try≻(Xa × Xt) + μ_wait≻(Xa × Xt) = μ(Xa × Xt) is established by the exhaustive label set (E3, E7) and stays on `obligations()`. The label conditions stand on the line records. On the Solution, its rule alone and no tie rule (E9).

### 2.4 The three cards at 78 columns

On 28 September 2026 the cards of this page were replaced by the cards the package prints, in the card's form of the internal developer release 0.01 (`card-redesign.md`), printed and not drawn by hand: the three below, the two of §3.4 and the terminal card of §5. The drawings on paper they replace were in the form of AMD-SG-034, and the sentences around each card were written for those drawings. Long rules are broken as the layout engine breaks them (AMD-SG-034 §4 item 10); one admissible breaking is shown. The wire columns follow the widths the package gives the stand-in's cards (probe 3).

```text
STAGE attempt / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_try≻    : Xa × Xt → [−∞, ∞)
       𝑑𝑉_try≻   : Xa × Xt → ℝ₊₊
       𝑉_wait≻   : Xa × Xt → [−∞, ∞)
       𝑑𝑉_wait≻  : Xa × Xt → ℝ₊₊
       ───────────────────────────────────────────────────────────────────────
  out  𝑉         : Xa × Xt → [−∞, ∞)
       𝑑𝑉        : Xa × Xt → ℝ₊₊

At
  𝑛  : Xa × Xt → {try, wait}

Where
  𝑔_try≻   : Xa × Xt → Xa × Xt,
             𝑔_try≻(a_attd, age_attd) = 𝑔≻(a_attd, age_attd, try)
  𝑔_wait≻  : Xa × Xt → Xa × Xt,
             𝑔_wait≻(a_attd, age_attd) = 𝑔≻(a_attd, age_attd, wait)

Operations
  1  Pullback:try
     in: 𝑉_try≻, 𝑑𝑉_try≻                out: 𝑉_try≻ ∘ 𝑔_try≻, 𝑑𝑉_try≻ ∘ 𝑔_try≻
     ─────────────────────────────────────────────────────────────────────────
     rule: (𝑉_try≻ ∘ 𝑔_try≻)(a_attd, age_attd)
             = 𝑉_try≻(𝑔_try≻(a_attd, age_attd))
           (𝑑𝑉_try≻ ∘ 𝑔_try≻)(a_attd, age_attd)
             = 𝑑𝑉_try≻(𝑔_try≻(a_attd, age_attd))

  2  Pullback:wait
     in: 𝑉_wait≻, 𝑑𝑉_wait≻              out: 𝑉_wait≻ ∘ 𝑔_wait≻,
                                             𝑑𝑉_wait≻ ∘ 𝑔_wait≻
     ─────────────────────────────────────────────────────────────────────────
     rule: (𝑉_wait≻ ∘ 𝑔_wait≻)(a_attd, age_attd)
             = 𝑉_wait≻(𝑔_wait≻(a_attd, age_attd))
           (𝑑𝑉_wait≻ ∘ 𝑔_wait≻)(a_attd, age_attd)
             = 𝑑𝑉_wait≻(𝑔_wait≻(a_attd, age_attd))

  3  Aggregation
     in: (1), (2)                       out: 𝑉, 𝑑𝑉
     ─────────────────────────────────────────────────────────────────────────
     rule: 𝑉
             = (𝑉_try≻(𝑔_try≻(a_attd, age_attd)),
                𝑉_wait≻(𝑔_wait≻(a_attd, age_attd)))[𝑛]
           on (a_attd, age_attd) ∈ Xa × Xt
           𝑑𝑉
             = (𝑑𝑉_try≻(𝑔_try≻(a_attd, age_attd)),
                𝑑𝑉_wait≻(𝑔_wait≻(a_attd, age_attd)))[𝑛]
           on (a_attd, age_attd) ∈ Xa × Xt

  4  Evaluation
     in: 𝑉, 𝑑𝑉                          out: 𝑉, 𝑑𝑉
     ─────────────────────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Xt → [−∞, ∞)
           𝑑𝑉 : Xa × Xt → ℝ₊₊

Conditions
  Aggregation  𝑉(a_attd, age_attd) ∈ [−∞, ∞)
  Aggregation  𝑑𝑉(a_attd, age_attd) ∈ ℝ₊₊
──────────────────────────────────────────────────────────────────────────────
Source  attempt.bl
  31  V  = (V_try[>], V_wait[>])[n]    :: [id=choice_value]
  32  dV = (dV_try[>], dV_wait[>])[n]  :: [id=marginal]

Definitions referenced
  Xa    attempt:set:Xa
  Xt    attempt:set:Xt
  𝑔≻    attempt:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The signature lists each branch's values on that branch's set (E6). The two sets print alike, so the wires' names are all that distinguishes the summands on the card. `at` types the policy plainly (E7). `where` states the two sections of the one law (E4, E5). Rows 1 and 2 are the pullbacks, keyed by label. Row 3 is the selection, an Aggregation whose rules are the file's two lines at the point, the label read as the policy (E2). On the stand-in the present fold writes one Pullback along 𝑔≻,𝑛 and the index as the free name `[n]` (probe 3). The build writes the sections and `[𝑛(a_attd, age_attd)]`, as `example-tenure.md` §4 prints.

```text
STAGE attempt / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ        : finite measure on Xa × Xt
       ─────────────────────────────────────────────────────
  out  μ_try≻   : finite measure on Xa × Xt
       μ_wait≻  : finite measure on Xa × Xt

At
  𝑛  : Xa × Xt → {try, wait}

Where
  𝑔_try≻   : Xa × Xt → Xa × Xt,
             𝑔_try≻(a_attd, age_attd) = 𝑔≻(a_attd, age_attd, try)
  𝑔_wait≻  : Xa × Xt → Xa × Xt,
             𝑔_wait≻(a_attd, age_attd) = 𝑔≻(a_attd, age_attd, wait)

Operations
  1  Pushforward
     in: μ                              out: μ_try≻, μ_wait≻
     ───────────────────────────────────────────────────────
     rule: μ_try≻(B)
             = μ({a_attd, age_attd ∈ Xa × Xt |
                   𝑛(a_attd, age_attd) = try ∧ 𝑔_try≻(a_attd, age_attd) ∈ B})
           μ_wait≻(B)
             = μ({a_attd, age_attd ∈ Xa × Xt |
                   𝑛(a_attd, age_attd) = wait
                     ∧ 𝑔_wait≻(a_attd, age_attd) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  attempt.bl
  21  a_try   = a_attd         :: [id=wealth]
  22  age_try = age_attd       :: [id=age]
  25  a_next   = a_attd        :: [id=wealth]
  26  age_next = age_attd + Δ  :: [id=age]

Definitions referenced
  Xa    attempt:set:Xa
  Xt    attempt:set:Xt
  𝑔≻    attempt:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Row 1 is the fork (E3). It is one push-forward at 𝑛 with one output measure per label, both on Xa × Xt and never bundled. No condition prints, since the four ranges are established (§2.3). The two masses sum to μ's, a condition the record holds as established and the card does not print. The same statement id, `wealth` or `age`, stands on both branches' lines; the source column shows the lines by position, and their records by address (§2.3).

```text
STAGE attempt / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_try≻   : Xa × Xt → [−∞, ∞)
       𝑉_wait≻  : Xa × Xt → [−∞, ∞)
       ───────────────────────────────────────────────────────
  out  𝑛        : Xa × Xt → {try, wait}

Where
  𝑔_try≻   : Xa × Xt → Xa × Xt,
             𝑔_try≻(a_attd, age_attd) = 𝑔≻(a_attd, age_attd, try)
  𝑔_wait≻  : Xa × Xt → Xa × Xt,
             𝑔_wait≻(a_attd, age_attd) = 𝑔≻(a_attd, age_attd, wait)

Operations
  1  Pullback:try
     in: 𝑉_try≻                         out: 𝑉_try≻ ∘ 𝑔_try≻
     ─────────────────────────────────────────────────────────
     rule: (𝑉_try≻ ∘ 𝑔_try≻)(a_attd, age_attd)
             = 𝑉_try≻(𝑔_try≻(a_attd, age_attd))

  2  Pullback:wait
     in: 𝑉_wait≻                        out: 𝑉_wait≻ ∘ 𝑔_wait≻
     ─────────────────────────────────────────────────────────
     rule: (𝑉_wait≻ ∘ 𝑔_wait≻)(a_attd, age_attd)
             = 𝑉_wait≻(𝑔_wait≻(a_attd, age_attd))

  3  choice:Aggregation
     in: (1), (2)
     out: (a_attd, age_attd, n)
            ↦ (𝑉_try≻(𝑔_try≻(a_attd, age_attd)),
               𝑉_wait≻(𝑔_wait≻(a_attd, age_attd)))[n]
     ─────────────────────────────────────────────────────────
     rule: (a_attd, age_attd, n)
             ↦ (𝑉_try≻(𝑔_try≻(a_attd, age_attd)),
                𝑉_wait≻(𝑔_wait≻(a_attd, age_attd)))[n]

  4  choice:Argmax
     in: (3)                            out: 𝑛
     ─────────────────────────────────────────────────────────
     rule: 𝑛(a_attd, age_attd)
             ∈ argmax_{n ∈ {try, wait}}
                 [(𝑉_try≻(𝑔_try≻(a_attd, age_attd)),
                   𝑉_wait≻(𝑔_wait≻(a_attd, age_attd)))[n]]

  5  Evaluation
     in: 𝑛                              out: 𝑛
     ─────────────────────────────────────────────────────────
     rule: 𝑛 : Xa × Xt → {try, wait}
──────────────────────────────────────────────────────────────────────────────
Source  attempt.bl
  41  n = argmax_{n}(V_try[>], V_wait[>])  :: [id=choice]

Definitions referenced
  Xa    attempt:set:Xa
  Xt    attempt:set:Xt
  𝑔≻    attempt:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The line is operative, not `!doc`, so it forms a Solution whose rule is the complete line at the point (K66, K69), with no `declared` block. Row 3's output falls below its row (K72), and the rule states the set of maximizers with no tie rule (E9). This card is where the stand-in informs the unverified step of §3 item 7. The present choice path accepts the tuple maximand: the stand-in constructs a `choice:Solution` (probe 3). But the rule it records is `argmax_{n ∈ {try, wait}} [𝑉_try≻(𝑔≻(a_attd, age_attd, n)), 𝑉_wait≻(𝑔≻(a_attd, age_attd, n))]`, a pair not read at the binder, and its `choice:Aggregation` maps to the pair. The build must write the tuple read at n, as above. On the stand-in, `policy_carrier` (`packages/bellman/bellman/stage/type_queries.py:334-360`) also adds the law's range, `𝑔≻(a_attd, age_attd, 𝑛(a_attd, age_attd)) ∈ …`, to the control's carrier. E7's plain typing, printed above, drops it for a label control.

## 3 `fecundity`, selected by a shock (the second build)

### 3.1 The fields at the perches, as the file declares them

`Xa := ℝ₊₊` and `Xt := ℝ₊` (`fecundity.bl:9-10`).

| Perch | State fields | Value fields | Other |
|---|---|---|---|
| ≺ arrival (`fecundity.bl:23, 42`) | `a_fec : Xa`, `age_fec : Xt` | `V[<] : [-inf, inf)`, `dV[<] : ℝ₊₊` | |
| ∼ decision (`:23, 28, 37`) | `a_fecd : Xa`, `age_fecd : Xt` | `V : [-inf, inf)`, `dV : ℝ₊₊` | the shock `s : {mother, childless} @ !shck`, drawn on the edge to the continuation perch (`:20-21, 28`) |
| ≻ mother (`:29, 37`) | `a_mth : Xa` | `V_mth[>] : [-inf, inf)`, `dV_mth[>] : ℝ₊₊` | |
| ≻ childless (`:32, 37`) | `a_chl : Xa` | `V_chl[>] : [-inf, inf)`, `dV_chl[>] : ℝ₊₊` | |

The continuation state space is X_mother ⊔ X_childless with both summands the set Xa (E1, E24). The bases are by position in `fecundity.bl:38-39`, position one `mother` and position two `childless` (E6). The file's parameters are ω, π_a, π_b, π_c and π_d (`:12-16`), and its function is 𝜋 : Xt → ℝ (`:18`; the package records its result set as ℝ, probe 7).

### 3.2 The two branches and what selects them

The block `dcsn_to_cntn` (`fecundity.bl:28-35`) reads `(a_fecd, age_fecd)` and the drawn label `s`. Read at `s = mother`: `a_mth = a_fecd`. Read at `s = childless`: `a_chl = a_fecd`. Nothing is chosen, and there is no policy block. After the edit of §1, the law is `s ~ Categorical((𝜋(age_fecd), 1 - 𝜋(age_fecd)))`, so p(mother | x) = 𝜋(age_fecd) and p(childless | x) = 1 − 𝜋(age_fecd). This is a law on the decision state alone, the form §1 of the unification admits for a label chosen by nature. The package records it today as the kernel P_{s|age_fecd} in `age_fecd`, and the forward view constructs (probes 3 and 7). The backward lines are `V = E_{s}((V_mth[>] + ω, V_chl[>])[s])` and `dV = E_{s}((dV_mth[>], dV_chl[>])[s])` (`:38-39`). The branch-specific payoff ω, the utility of the birth, is inside the tuple entry, as rule 4 of `bellman-sym.md` permits.

### 3.3 The records the fold would write

**Definitions.** One law, `fecundity:g:dcsn_to_cntn`: 𝑔≻ : Xa × Xt × {mother, childless} → Xa ⊔ Xa, holding the two nested lines with the drawn label as their condition, s = mother or s = childless (E4). The label argument is a shock, as `R2` is an argument of `cons_mother`'s 𝑔≻ (probe 1). Its sections are 𝑔_mother≻ and 𝑔_childless≻. There are two line records, `dcsn_to_cntn.mother.wealth` and `dcsn_to_cntn.childless.wealth` (probe 5, part 4): one statement id in both branches, as in `attempt`. The law of the label is `fecundity:distribution:s`, P_{s|age_fecd}, read under the family convention of the Categorical: "the label in position i of the declared set of s is drawn with probability fᵢ" (probe 4). The aggregator `fecundity:G:cntn_to_dcsn` is the pairing of the two kernels of `:38-39`. `branch_labels = ("mother", "childless")`. `branches(fecundity)` answers `{mother: (a_mth,), childless: (a_chl,)}` (E12). E27's classifier answers the expectation, `s` being a declared shock under `E_{s}`.

**Operations.** Backward `cntn_to_dcsn`: `Pullback:mother`, `Pullback:childless`, E13's weighted case operation, and `Evaluation`. Backward `dcsn_to_arvl`: `Pullback` along 𝑔≺, `Aggregation` and `Evaluation`. Forward `arvl_to_dcsn`: `Pushforward`. Forward `dcsn_to_cntn`: `DistributionExtension:s`, as the package prints it today (probe 3), then one `Pushforward` with two outputs. E13 names neither the kind of the case operation nor the forward split; §3.4 marks both. On the stand-in, today's fold writes `E_{s}((…)[s])` as an Aggregation per line followed by an Expectation over s (probe 3). That is the form E13 rejects, "an Expectation over one base".

**Conditions, as terms.** The memberships of K49 on the operation that writes V and dV. On the Pushforward, both line ranges are established (a_fecd ∈ Xa). On `obligations()` (probes 4, 8 and 9) stand three conditions. The first is the Categorical's weight condition, `distribution-weights-are-a-probability-vector`: "the weights (𝜋(age_fecd), 1 - 𝜋(age_fecd)) … each lie in [0, 1] and sum to one". It stays `required` after calibration, the weight reading `age_fecd`, although π_a ∈ (0, 1] and π_d ∈ ℝ₊₊ place 𝜋 in (0, π_a). The second is the definedness of 𝜋, ¬(π_d + exp(π_b − π_c · t) = 0). The third is the conservation identity μ_mother≻(Xa) + μ_childless≻(Xa) = μ(Xa × Xt). It rests on the weight condition, not on an exhaustive label set, a ground E3 states for the choice alone `[open: E13]`.

### 3.4 The two builders' cards and the expectation E13 states

The expectation E13 states, on this file. E13 cites `docs/bellman-calculus/09-branching.md:77`, whose weights are p(j | x), read at the decision state. E13's own text writes p(j), which here would drop the dependence on age.

```text
𝑉(a_fecd, age_fecd)
  = Σ_{j ∈ {mother, childless}} p(j | age_fecd) · 𝑄_j(a_fecd, age_fecd)
𝑑𝑉(a_fecd, age_fecd)
  = Σ_{j ∈ {mother, childless}} p(j | age_fecd) · 𝑑𝑄_j(a_fecd, age_fecd)
p(mother | age_fecd) = 𝜋(age_fecd),  p(childless | age_fecd) = 1 − 𝜋(age_fecd)
𝑄_mother    = 𝑉_mth≻ ∘ 𝑔_mother≻ + ω,     𝑑𝑄_mother    = 𝑑𝑉_mth≻ ∘ 𝑔_mother≻
𝑄_childless = 𝑉_chl≻ ∘ 𝑔_childless≻,     𝑑𝑄_childless = 𝑑𝑉_chl≻ ∘ 𝑔_childless≻
```

The marginal kernel is exact as authored because the law reads `age_fecd` and not `a_fecd`, so differentiating in wealth passes through the weights. That is the paper's condition (17), `theory.md:131-134`; nothing is differentiated (E10).

```text
STAGE fecundity / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_mth≻   : Xa → [−∞, ∞)
       𝑑𝑉_mth≻  : Xa → ℝ₊₊
       𝑉_chl≻   : Xa → [−∞, ∞)
       𝑑𝑉_chl≻  : Xa → ℝ₊₊
       ────────────────────────────────────────────────────────────
  out  𝑉        : Xa × Xt → [−∞, ∞)
       𝑑𝑉       : Xa × Xt → ℝ₊₊

Where
  𝑔_mother≻     : Xa × Xt → Xa,
                  𝑔_mother≻(a_fecd, age_fecd) = 𝑔≻(a_fecd, age_fecd, mother)
  𝑔_childless≻  : Xa × Xt → Xa,
                  𝑔_childless≻(a_fecd, age_fecd)
                    = 𝑔≻(a_fecd, age_fecd, childless)

Operations
  1  Pullback:mother
     in: 𝑉_mth≻, 𝑑𝑉_mth≻                out: 𝑉_mth≻ ∘ 𝑔_mother≻,
                                             𝑑𝑉_mth≻ ∘ 𝑔_mother≻
     ──────────────────────────────────────────────────────────────
     rule: (𝑉_mth≻ ∘ 𝑔_mother≻)(a_fecd, age_fecd)
             = 𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd))
           (𝑑𝑉_mth≻ ∘ 𝑔_mother≻)(a_fecd, age_fecd)
             = 𝑑𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd))

  2  Pullback:childless
     in: 𝑉_chl≻, 𝑑𝑉_chl≻                out: 𝑉_chl≻ ∘ 𝑔_childless≻,
                                             𝑑𝑉_chl≻ ∘ 𝑔_childless≻
     ──────────────────────────────────────────────────────────────
     rule: (𝑉_chl≻ ∘ 𝑔_childless≻)(a_fecd, age_fecd)
             = 𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd))
           (𝑑𝑉_chl≻ ∘ 𝑔_childless≻)(a_fecd, age_fecd)
             = 𝑑𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd))

  3  Aggregation
     in: (1), (2)                       out: 𝑉, 𝑑𝑉
     ──────────────────────────────────────────────────────────────
     rule: 𝑉
             = E_{s}[(𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd)) + ω,
                      𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd)))[s]]
           on (a_fecd, age_fecd) ∈ Xa × Xt
           𝑑𝑉
             = E_{s}[(𝑑𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd)),
                      𝑑𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd)))[s]]
           on (a_fecd, age_fecd) ∈ Xa × Xt

  4  Evaluation
     in: 𝑉, 𝑑𝑉                          out: 𝑉, 𝑑𝑉
     ──────────────────────────────────────────────────────────────
     rule: 𝑉 : Xa × Xt → [−∞, ∞)
           𝑑𝑉 : Xa × Xt → ℝ₊₊

Conditions
  Aggregation  𝑉(a_fecd, age_fecd) ∈ [−∞, ∞)
  Aggregation  𝑑𝑉(a_fecd, age_fecd) ∈ ℝ₊₊
──────────────────────────────────────────────────────────────────────────────
Source  fecundity.bl
  38  V  = E_{s}((V_mth[>] + ω, V_chl[>])[s])  :: [id=value]
  39  dV = E_{s}((dV_mth[>], dV_chl[>])[s])    :: [id=marginal]

Definitions referenced
  Xa    fecundity:set:Xa
  Xt    fecundity:set:Xt
  ω     fecundity:parameter:ω
  s     fecundity:distribution:s
  𝑔≻    fecundity:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

There is no `at` section, since there is no policy. Row 3 is `[open: E13]` in three respects. E13 fixes the operation's value but not its kind: an Aggregation, as E2 names the choice's, or an Expectation over s whose integrand reads each branch on its own base. E13 also does not say whether the card writes the weights as the Categorical writes them, as here, or through the law's printed name P_{s|age_fecd}. Nor does it say whether `s` then stands among the definitions.

```text
STAGE fecundity / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ             : finite measure on Xa × Xt
       ─────────────────────────────────────────────────────────────
  out  μ_mother≻     : finite measure on Xa
       μ_childless≻  : finite measure on Xa

Where
  𝑔_mother≻     : Xa × Xt → Xa,
                  𝑔_mother≻(a_fecd, age_fecd) = 𝑔≻(a_fecd, age_fecd, mother)
  𝑔_childless≻  : Xa × Xt → Xa,
                  𝑔_childless≻(a_fecd, age_fecd)
                    = 𝑔≻(a_fecd, age_fecd, childless)

Operations
  1  DistributionExtension:s
     in: μ                              out: μ⊗P_{s|age_fecd}
     ───────────────────────────────────────────────────────────────
     rule: μ⊗P_{s|age_fecd}(B)
             = ∫_{(a_fecd, age_fecd) ∈ Xa × Xt}
                 [P_{s|age_fecd}(age_fecd)({s ∈ {mother, childless} |
                               (a_fecd, age_fecd, s) ∈ B})]
               μ(d(a_fecd, age_fecd))

  2  Pushforward
     in: (1)                            out: μ_mother≻, μ_childless≻
     ───────────────────────────────────────────────────────────────
     rule: μ_mother≻(B)
             = μ⊗P_{s|age_fecd}({a_fecd, age_fecd, s ∈
                               Xa × Xt × {mother, childless} |
                               s = mother ∧ 𝑔_mother≻(a_fecd, age_fecd) ∈ B})
           μ_childless≻(B)
             = μ⊗P_{s|age_fecd}({a_fecd, age_fecd, s ∈
                               Xa × Xt × {mother, childless} |
                               s = childless
                               ∧ 𝑔_childless≻(a_fecd, age_fecd) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  fecundity.bl
  30  a_mth = a_fecd  :: [id=wealth]
  33  a_chl = a_fecd  :: [id=wealth]

Definitions referenced
  Xa              fecundity:set:Xa
  Xt              fecundity:set:Xt
  P_{s|age_fecd}  fecundity:distribution:s
  s               fecundity:distribution:s
  𝑔≻              fecundity:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Row 1 is the extension the package writes today on the stand-in, word for word (probe 3). Row 2 is the fork by nature, `[open: E13; E3]`. E3 states the routing at the policy, 𝑑(x) = j; here the drawn label takes its place, s = j, which is §3 item 6 applied to the edge's shock. No rule states this form. The two masses sum to μ's because the weights sum to one.

## 4 The initial diagrams and the builders graphs

**`attempt`, forward initial diagram.** Inputs `a_att≺`, `age_att≺`. Block `arvl_to_dcsn`: line boxes `arvl_to_dcsn.wealth` (`a_att≺` → `a_attd`) and `arvl_to_dcsn.age` (`age_att≺` → `age_attd`). Block `dcsn_to_cntn`, coordinate `n`, holds two bubbles (E23), addressed `stage.initial_diagrams.dcsn_to_cntn["try"]` and `["wait"]`. `dcsn_to_cntn.try` holds `wealth` (`a_attd` → `a_try≻`) and `age` (`age_attd` → `age_try≻`). `dcsn_to_cntn.wait` holds `wealth` (`a_attd` → `a_next≻`) and `age` (`age_attd` → `age_next≻`, Δ a parameter and no wire). `a_attd` and `age_attd` are copied to both bubbles. The outputs are the four branch fields; no decision state is an output, since no backward line reads one.

**`attempt`, backward initial diagram.** Inputs the four branch values. Block `cntn_to_dcsn`, coordinate `n`: `choice_value` (`V_try≻`, `V_wait≻` → `V`) and `marginal` (`dV_try≻`, `dV_wait≻` → `dV`). Block `dcsn_to_arvl`: `value` and `marginal` (`V`, `dV` → `V≺`, `dV≺`). Block `policy`: `choice` (`V_try≻`, `V_wait≻` → `n`), delivered at the boundary (AMD-SG-013 §3). `V_try≻` and `V_wait≻` are each read twice and copied.

**`attempt`, builders graphs.** Backward: `cntn_to_dcsn` holds `Pullback:try`, `Pullback:wait`, `Aggregation` and `Evaluation`. Its inputs form two bundles, (𝑉_try≻, 𝑑𝑉_try≻) on the try base and (𝑉_wait≻, 𝑑𝑉_wait≻) on the wait base. The pullbacks' four outputs meet the Aggregation as two groups, never one bundle (E17). `render.bundles` keys a bundle by its writer, its reader and the identities of its base coordinates (`packages/bellman/bellman/graphs/render.py:946-973`), and the identities differ although the two sets are equal. `dcsn_to_arvl` holds `Pullback`, `Aggregation` and `Evaluation`. `policy` holds the two pullbacks, `choice:Aggregation`, `choice:Solution` and `Evaluation`, with 𝑛 at the boundary and no wire into a backward builder. Forward: `arvl_to_dcsn` holds `Pushforward`; `dcsn_to_cntn` holds `Pushforward` at 𝑛 with two output wires to the boundary, μ_try≻ and μ_wait≻, never bundled.

**`fecundity`, initial diagrams.** Forward: inputs `a_fec≺`, `age_fec≺` and the shock `s`. Block `arvl_to_dcsn`: `wealth` and `age`. Block `dcsn_to_cntn`: two bubbles, `dcsn_to_cntn.mother` holding `wealth` (`a_fecd` → `a_mth≻`) and `dcsn_to_cntn.childless` holding `wealth` (`a_fecd` → `a_chl≻`). Whether `s` stands as the coordinate at which the block's lines are read, as a control does (AMD-SG-013 §2), or as the shock wire the block lists (the typing rule of shocks, `build.py:44-51`), is `[open: E13]`. Backward: block `cntn_to_dcsn` holds `value` (`V_mth≻`, `V_chl≻` → `V`) and `marginal` (`dV_mth≻`, `dV_chl≻` → `dV`), each reading the label under `E_{s}`. Block `dcsn_to_arvl` holds `value` and `marginal`. There is no policy block.

**`fecundity`, builders graphs.** Backward: `cntn_to_dcsn` holds `Pullback:mother`, `Pullback:childless`, E13's operation `[open: E13]` and `Evaluation`, with the inputs two bundles on the two bases. `dcsn_to_arvl` holds `Pullback`, `Aggregation` and `Evaluation`. Forward: `arvl_to_dcsn` holds `Pushforward`; `dcsn_to_cntn` holds `DistributionExtension:s`, then `Pushforward` with two output wires, μ_mother≻ and μ_childless≻, never bundled.

## 5 The terminal stages

Three routes leave the terminal period: the waiting woman's `(a_next, age_next)`, the mother's `b_mother` and the childless woman's `b_childless`. Each carries its own continuation problem. Joining them at one arrival field would need a state field recording the regime (E29), and the language reads an arrival value from the arrival state alone (E25). So the registry writes one terminal stage per route: [`terminal_wait.bl`](registry/stages/terminal_wait.bl) arrives at `(a_tw, age_tw)`, [`terminal_mother.bl`](registry/stages/terminal_mother.bl) at `a_tm` and [`terminal_childless.bl`](registry/stages/terminal_childless.bl) at `a_tc`. No other stage of `periods[0]` declares these names (E15). They stand in `periods[0]` alone, `periods: [0, 0]`, and are joined by one flat mapping in the period's own entry, `{a_next: a_tw, age_next: age_tw, b_mother: a_tm, b_childless: a_tc}` (A38).

Their content is where the rules and the model part. Under R12 with A33, a terminal stage reads a continuation value `V[>]` that is zero on an empty continuation perch. The bequest's prints as `𝑉≻ : {()} → ℝ`, a constant (probe 2), and the terminal value is then the stage's own lines, as `bequest.bl:17-18` writes it. This model states no terminal value (`theory.md:170`), and after the last date it needs a function of wealth, and of age on the waiting route, with a positive marginal value. The Euler root conditions of `cons_mother.bl:45` and `cons_childless.bl:38` read `dV[>] ∈ ℝ₊₊`, and they have no root at a zero marginal value, since 𝑑𝑢(c) = c^(−ε) > 0. The registry therefore keeps the application's own economics, "boundary data after the terminal one" (`trellis.yml:3-4`). Each terminal stage carries its route's state to a continuation perch by identities, and its value lines are `V = V[>]` and `dV = dV[>]`, the boundary data supplied at realization (D15). The stages compute nothing; each is a stage in form and D15's boundary data in content (the findings returned with this example: the row on R12 and A33, and question 1). They construct today (probe 6):

```text
STAGE terminal_mother / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻   : Xa → [−∞, ∞)
       𝑑𝑉≻  : Xa → ℝ₊₊
       ───────────────────────────────────────────────────────
  out  𝑉    : Xa → [−∞, ∞)
       𝑑𝑉   : Xa → ℝ₊₊

Operations
  1  Pullback
     in: 𝑉≻, 𝑑𝑉≻                        out: 𝑉≻ ∘ 𝑔≻, 𝑑𝑉≻ ∘ 𝑔≻
     ─────────────────────────────────────────────────────────
     rule: (𝑉≻ ∘ 𝑔≻)(m_tm) = 𝑉≻(𝑔≻(m_tm))
           (𝑑𝑉≻ ∘ 𝑔≻)(m_tm) = 𝑑𝑉≻(𝑔≻(m_tm))

  2  Aggregation
     in: (1)                            out: 𝑉, 𝑑𝑉
     ─────────────────────────────────────────────────────────
     rule: 𝑉(m_tm) = 𝑉≻(𝑔≻(m_tm))
           𝑑𝑉(m_tm) = 𝑑𝑉≻(𝑔≻(m_tm))

  3  Evaluation
     in: 𝑉, 𝑑𝑉                          out: 𝑉, 𝑑𝑉
     ─────────────────────────────────────────────────────────
     rule: 𝑉 : Xa → [−∞, ∞)
           𝑑𝑉 : Xa → ℝ₊₊

Conditions
  Aggregation  𝑉(m_tm) ∈ [−∞, ∞)
  Aggregation  𝑑𝑉(m_tm) ∈ ℝ₊₊
──────────────────────────────────────────────────────────────────────────────
Source  terminal_mother.bl
  23  V  = V[>]   :: [id=value]
  24  dV = dV[>]  :: [id=marginal]

Definitions referenced
  Xa    terminal_mother:set:Xa
  𝑔≻    terminal_mother:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

`terminal_childless` prints the same card on `a_tc`, and `terminal_wait` the same on Xa × Xt (probe 6). The terminal period's outputs are therefore the terminal stages' continuation fields, `b_tw`, `age_twc`, `b_tm` and `b_tc`, where the boundary data sits. In the durables example the terminal period has no output. The Benhabib registry, merged at a5bfb2349 while this example was written, puts its bequest alone in `periods[0]` with no rename (`applications/benhabib-2019/declaration/spec.yml:26-27`, `trellis.yml:3-13`). That is the other form §7 item 5 of the unification lists. This registry follows E15, as the brief directs.

## 6 The joins of the periods, the inter-period connector and the drawing of three periods

The trellis file is [`registry/trellis.yml`](registry/trellis.yml): `periods[0]` written out with eight stages and five connectors, then `{template: period.yml, repeat: 35}`, and one inter-period mapping standing for every adjacent pair. `load_recipe(registry, "spec.yml")` returns 36 periods and 35 mappings, all equal (probe 5, part 1). Every join below is the package's output on the stand-ins (probe 5, part 3). The joins read state fields alone (`packages/bellman/bellman/stage/joins.py:32-46`), so the branching stages will give the same joins once they construct (§3 item 9). This model has no equal-name join: every join passes through a connector.

**`period_joins(periods[0])`** records ten joins, sorted by source:

```text
attempt:a_next → terminal_wait:a_tw
attempt:a_try → fecundity:a_fec
attempt:age_next → terminal_wait:age_tw
attempt:age_try → fecundity:age_fec
cons_childless:b_childless → terminal_childless:a_tc
cons_mother:b_mother → terminal_mother:a_tm
cons_wait:age_c → attempt:age_att
cons_wait:b_wait → attempt:a_att
fecundity:a_chl → cons_childless:a_childless
fecundity:a_mth → cons_mother:a_mother
```

Its outputs are `terminal_childless:b_tc`, `terminal_mother:b_tm`, `terminal_wait:age_twc` and `terminal_wait:b_tw`. Six of the ten joins leave a branch field, and each answers its label through `branches(stage)` (E26). `attempt:a_try` and `attempt:age_try` answer `try`; `attempt:a_next` and `attempt:age_next` answer `wait`; `fecundity:a_mth` answers `mother` and `fecundity:a_chl` answers `childless`. `computable_together` answers `[[cons_wait], [attempt], [fecundity, terminal_wait], [cons_childless, cons_mother], [terminal_childless, terminal_mother]]`. `forward_order` answers `[cons_wait, attempt, fecundity, terminal_wait, cons_childless, cons_mother, terminal_childless, terminal_mother]`, and `backward_order` its reverse. There is no cycle.

**`period_joins(periods[h])`, h = 1 to 35**, every period of the template, records six joins, the last six above. The outputs are `attempt:a_next`, `attempt:age_next`, `cons_childless:b_childless` and `cons_mother:b_mother`. The layers are `[[cons_wait], [attempt], [fecundity], [cons_childless, cons_mother]]`, the forward order `[cons_wait, attempt, fecundity, cons_childless, cons_mother]`, and the backward order its reverse. Every continuation field is joined at most once in every period, so E16's fan-out rule holds, and the period fans out at the two branching stages' labels alone.

**`inter_period_joins(inter_connectors[h], periods[h + 1], periods[h])`**. There are two patterns, h = 0 (into the terminal period) and h = 1 to 34 (template to template). Both give the same four joins in the mapping's order (probe 5 computed h = 0, 1 and 34):

```text
attempt:a_next → cons_wait:a_wait
attempt:age_next → cons_wait:age
cons_mother:b_mother → cons_mother:a_mother
cons_childless:b_childless → cons_childless:a_childless
```

At h = 0 the names `a_wait`, `age`, `a_mother` and `a_childless` belong to the three period stages alone, the terminal stages arriving elsewhere, so no mapping reaches a terminal stage (E15). Each of the four keys leaves `periods[h + 1]`, as `inter_period_joins` requires since 1b643edc2 (`joins.py:218-262`, which now builds the continuation half of `docs/Bellman-Sym/07-trelis.md:43`). The two absorbing routes, `{b_mother: a_mother}` and `{b_childless: a_childless}`, reach arrival fields that a connector of `periods[h]` already supplies. The arrival half of that rule, which E15 leaves unbuilt, would refuse them. So `cons_mother:a_mother` in `periods[h]`, h ≤ 34, has two sources: `fecundity:a_mth` of the same period, the women whose attempt at that date succeeded, and `cons_mother:b_mother` of `periods[h + 1]`, the women who were already mothers. These are disjoint sub-populations, since the attempt is one-shot, and the arrival measure is their sum (E25). The sum is sound because the mother's value reads wealth alone (`theory.md:111-112`). The same holds for `cons_childless:a_childless`. In `periods[35]` each has its within-period source alone.

**`draw_trellis(trellis, periods=[0, 1, 35])`** (`packages/bellman/bellman/display/trellis.py:81-141`) writes the head of `dot_head` with `rankdir="LR"` and the title naming the two directions. It then writes the three clusters in the order 35, 1, 0, the four inter-period wires of `inter_connectors[0]` and four invisible edges, as probe 5 prints it. The trellis's `registry` holds no `last_age`, so a cluster's label names h alone. The drawing needs the second build as well as the first, since every period holds `fecundity`.

```text
  subgraph "cluster_35" {
    graph [label="periods[35]: h = 35", labelloc="t", labeljust="l"];
    "35:cons_wait" [label="cons_wait"];
    "35:attempt" [label="attempt"];
    "35:fecundity" [label="fecundity"];
    "35:cons_childless" [label="cons_childless"];
    "35:cons_mother" [label="cons_mother"];
    "35:attempt" -> "35:fecundity" [label="a_try → a_fec"];
    "35:attempt" -> "35:fecundity" [label="age_try → age_fec"];
    "35:cons_wait" -> "35:attempt" [label="age_c → age_att"];
    "35:cons_wait" -> "35:attempt" [label="b_wait → a_att"];
    "35:fecundity" -> "35:cons_childless" [label="a_chl → a_childless"];
    "35:fecundity" -> "35:cons_mother" [label="a_mth → a_mother"];
    "35:out0" [shape="plaintext" label="a_next"];
    "35:attempt" -> "35:out0";
    "35:out1" [shape="plaintext" label="age_next"];
    "35:attempt" -> "35:out1";
    "35:out2" [shape="plaintext" label="b_childless"];
    "35:cons_childless" -> "35:out2";
    "35:out3" [shape="plaintext" label="b_mother"];
    "35:cons_mother" -> "35:out3";
  }
  subgraph "cluster_1" {
    graph [label="periods[1]: h = 1", labelloc="t", labeljust="l"];
    "1:cons_wait" [label="cons_wait"];
    "1:attempt" [label="attempt"];
    "1:fecundity" [label="fecundity"];
    "1:cons_childless" [label="cons_childless"];
    "1:cons_mother" [label="cons_mother"];
    "1:attempt" -> "1:fecundity" [label="a_try → a_fec"];
    "1:attempt" -> "1:fecundity" [label="age_try → age_fec"];
    "1:cons_wait" -> "1:attempt" [label="age_c → age_att"];
    "1:cons_wait" -> "1:attempt" [label="b_wait → a_att"];
    "1:fecundity" -> "1:cons_childless" [label="a_chl → a_childless"];
    "1:fecundity" -> "1:cons_mother" [label="a_mth → a_mother"];
  }
  subgraph "cluster_0" {
    graph [label="periods[0]: h = 0", labelloc="t", labeljust="l"];
    "0:cons_wait" [label="cons_wait"];
    "0:attempt" [label="attempt"];
    "0:fecundity" [label="fecundity"];
    "0:terminal_wait" [label="terminal_wait"];
    "0:cons_childless" [label="cons_childless"];
    "0:cons_mother" [label="cons_mother"];
    "0:terminal_childless" [label="terminal_childless"];
    "0:terminal_mother" [label="terminal_mother"];
    "0:attempt" -> "0:terminal_wait" [label="a_next → a_tw"];
    "0:attempt" -> "0:fecundity" [label="a_try → a_fec"];
    "0:attempt" -> "0:terminal_wait" [label="age_next → age_tw"];
    "0:attempt" -> "0:fecundity" [label="age_try → age_fec"];
    "0:cons_childless" -> "0:terminal_childless" [label="b_childless → a_tc"];
    "0:cons_mother" -> "0:terminal_mother" [label="b_mother → a_tm"];
    "0:cons_wait" -> "0:attempt" [label="age_c → age_att"];
    "0:cons_wait" -> "0:attempt" [label="b_wait → a_att"];
    "0:fecundity" -> "0:cons_childless" [label="a_chl → a_childless"];
    "0:fecundity" -> "0:cons_mother" [label="a_mth → a_mother"];
    "0:out0" [shape="plaintext" label="b_tc"];
    "0:terminal_childless" -> "0:out0";
    "0:out1" [shape="plaintext" label="b_tm"];
    "0:terminal_mother" -> "0:out1";
    "0:out2" [shape="plaintext" label="age_twc"];
    "0:terminal_wait" -> "0:out2";
    "0:out3" [shape="plaintext" label="b_tw"];
    "0:terminal_wait" -> "0:out3";
  }
  "1:attempt" -> "0:cons_wait" [label="inter_connectors[0]\na_next → a_wait"];
  "1:attempt" -> "0:cons_wait" [label="inter_connectors[0]\nage_next → age"];
  "1:cons_mother" -> "0:cons_mother" [label="inter_connectors[0]\nb_mother → a_mother"];
  "1:cons_childless" -> "0:cons_childless" [label="inter_connectors[0]\nb_childless → a_childless"];
  "35:out0" -> "1:cons_wait" [style="invis"];
  "35:out1" -> "1:cons_wait" [style="invis"];
  "35:out2" -> "1:cons_wait" [style="invis"];
  "35:out3" -> "1:cons_wait" [style="invis"];
}
```

`periods[35]` and `periods[1]` are not adjacent, so no wire joins them. The outputs of `periods[35]` are drawn as plain-label sinks, and four invisible edges keep the two clusters in order. Every output of `periods[1]` is read by a wire of `inter_connectors[0]`, so it has no sink. The outputs of `periods[0]` are the terminal stages' continuation fields, drawn as sinks (§5). Laid out, the clusters stand left to right with `periods[0]` at the right. `str(drawing)` lists the eighteen boxes, the eight of `periods[0]` first, then the five of `periods[1]` and the five of `periods[35]`. In the first build the label that F05 adds to the six arrows leaving a branch field (`try: a_try → a_fec`, and the two inter-period arrows from `a_next` and `age_next`) is not printed (E26). `draw_period(trellis, 0)` writes the statements of `cluster_0` alone, the nodes named without the `0:` prefix (probe 5).

**The verbs.** On the stand-ins, `calibrate_trellis` refuses without a fill: "stage 'fecundity', parameter 'ω' (…): the calibration source supplies no value for it; every declared parameter is valued when values are bound (AMD-SG-006 §4, rule 8); write `ω: <value>` in the calibration source". With `fill={"calibration": {"ω": 1.0}}` the three verbs each bind all 183 stage occurrences, and `assemble_trellis(registry, "spec.yml", fill={"calibration": {"ω": 1.0}})` returns 36 periods and 183 stage occurrences (probe 5). The paper's population of women is then a sweep, one fill per value of ω.

## 7 What the package prints today

```text
attempt.bl:20:5-23:6: make_stage cannot construct this nested block: task B02
(branching construction) adds its construction rule (address 'dcsn_to_cntn.try';
rule not-constructed)
fecundity.bl:29:5-31:6: make_stage cannot construct this nested block: task B02
(branching construction) adds its construction rule (address
'dcsn_to_cntn.mother'; rule not-constructed)
```

Both the application's files and the registry's edited files are refused, at the same spans (probes 1 and 6). `load_recipe` of the registry loads the 36 periods and 35 mappings, since loading elaborates nothing (A46). `elaborate_trellis` refuses at the first `attempt` occurrence with the first message above (probe 5, part 2). After the first build it would refuse at the first `fecundity` occurrence under `not-constructed`, naming the second build (E13). The flattened stand-ins show what the refusal hides today (probe 3). Nothing else in either file is refused. The law of `s`, in either spelling, now passes the forward check that refused it on 15 September (`theory.md:303-308`), since AMD-SG-010 §3 admits `Bernoulli` and `Categorical`. The remaining obligation on the law's argument, `external-callable-result-domain`, concerns `exp` inside the definition of 𝜋, not 𝜋 itself (probe 9).
