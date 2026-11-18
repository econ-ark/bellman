# The example on paper: `applications/durables/declaration/stages/tenure/tenure.bl` under the first build of branching

23 September 2026. Written before any code, from `tenure.bl`, `applications/durables/economics.md`, `applications/durables/declaration/period.yml` and `applications/durables/declaration/trellis.yml`, in the form the package prints today for `keeper_cons.bl` and `adjuster_cons.bl` at commit 6abcac863; §§3, 4 and 6 revised the same evening under E3, E15, E16, E25 and E26 of `branching-unified.md`, whose §4 the E-numbers cite.

## 1 The fields at the perches, as the file declares them

| Perch | State fields | Value fields | Other |
|---|---|---|---|
| ≺ arrival (`tenure.bl:16,40`) | `a : ℝ₊`, `h : ℝ₊₊`, `z : ℝ₊₊` | `V[<] : ℝ`, `dV_a[<] : ℝ₊₊`, `dV_h[<] : ℝ₊₊` | `ε : ℝ`, `ε ~ N(0, 1)`, drawn on the arrival edge (`:11-12`) |
| ∼ decision (`:16,22,34`) | `a_d : ℝ₊`, `h_d : ℝ₊₊`, `z_d : ℝ₊₊` | `V : ℝ`, `dV_a : ℝ₊₊`, `dV_h : ℝ₊₊` | `d : !ctrl @ {keep, adjust}` |
| ≻ keep (`:23,34`) | `w_kp : ℝ₊₊`, `h_kp : ℝ₊₊`, `z_kp : ℝ₊₊` | `V_kp[>] : ℝ`, `dV_w_kp[>] : ℝ₊₊`, `dV_h_kp[>] : ℝ₊₊` | |
| ≻ adjust (`:28,34`) | `w_adj : ℝ₊₊`, `z_adj : ℝ₊₊` | `V_adj[>] : ℝ`, `dV_w_adj[>] : ℝ₊₊` | |

The continuation state space is X_keep ⊔ X_adjust, X_keep = ℝ₊₊ × ℝ₊₊ × ℝ₊₊ and X_adjust = ℝ₊₊ × ℝ₊₊ (E1, E24). Each continuation value's base is the summand at its position in the selection tuples of `tenure.bl:35-37,47`: position one keep, position two adjust (E6).

## 2 The two branches and what selects them

The block `dcsn_to_cntn` (`tenure.bl:22-32`) reads `(a_d, h_d, z_d)` at the coordinate `d`. Read at `d = keep`: `w_kp = R*a_d + 𝑦(z_d)`, `h_kp = (1 − δ)*h_d`, `z_kp = z_d`. Read at `d = adjust`: `w_adj = R*a_d + R_H*(1 − δ)*h_d + 𝑦(z_d)`, `z_adj = z_d`. The policy 𝑑 : ℝ₊ × ℝ₊₊ × ℝ₊₊ → {keep, adjust}, defined by the operative line `d = argmax_{d}(V_kp[>], V_adj[>])` (`:47`), selects the branch; every label is feasible everywhere (E7). 𝑑 routes the forward measure (E3) and selects the backward values (E2).

## 3 The records the fold would write

**Definitions.** One law, `tenure:g:dcsn_to_cntn`, 𝑔≻ : ℝ₊ × ℝ₊₊ × ℝ₊₊ × {keep, adjust} → X_keep ⊔ X_adjust, holding the five nested lines with their labels as conditions, `d = keep` or `d = adjust` (E4); its sections 𝑔_keep≻ and 𝑔_adjust≻ are abbreviations of the builders that read them (E5). Five line records at the addresses of `item_addresses`: `dcsn_to_cntn.keep.cash_on_hand`, `dcsn_to_cntn.keep.housing_kept`, `dcsn_to_cntn.keep.3`, `dcsn_to_cntn.adjust.total_wealth`, `dcsn_to_cntn.adjust.2`. The aggregator `tenure:G:cntn_to_dcsn` is the pairing of the three selection kernels of `tenure.bl:35-37`, each a tuple indexed by `d`. `BlockData.branch_labels = ("keep", "adjust")`; `branches(stage)` answers `{keep: (w_kp, h_kp, z_kp), adjust: (w_adj, z_adj)}` (E12).

**Operations.** Backward `cntn_to_dcsn`: `Pullback:keep`, `Pullback:adjust`, `Aggregation`, `Evaluation` at 𝑑 (see the cards of §4). Backward `dcsn_to_arvl`: `Pullback` along 𝑔≺, one `Expectation` over ε at the primitive grain (three occurrences at the sub-builder grain, AMD-SG-011 §3), `Aggregation`, `Evaluation`. Policy: the two pullbacks, `choice:Aggregation`, `choice:Solution`, `Evaluation`. Forward `arvl_to_dcsn`: `DistributionExtension:ε`, `Pushforward`, as `buffer_stock.bl` prints. Forward `dcsn_to_cntn`: one `Pushforward` at 𝑑 with two outputs.

**Conditions, as terms.** On the Aggregation, K49's memberships (§4). On the Pushforward, each nested line's range at the source point (K65): `R · a_d + 𝑦(z_d) ∈ ℝ₊₊` is not established, a_d ∈ ℝ₊ and 𝑦 valued in ℝ₊, and prints; the other four are established by the declared sets and stay on `obligations()`, as does the conservation identity μ_keep≻(X_keep) + μ_adjust≻(X_adjust) = μ(ℝ₊ × ℝ₊₊ × ℝ₊₊), established by the exhaustive label set (E3, E7). The label conditions stand on the line records. On the Solution, its rule alone and no tie rule (E9).

## 4 The cards at 78 columns

On 28 September 2026 the three cards below were replaced by the cards the package prints, in the card's form of the internal developer release 0.01 (`card-redesign.md`), printed and not drawn by hand; the drawings on paper they replace were in the form of AMD-SG-034, and the sentences under each card were written for those drawings. The build prints these from the records and the run report lists each difference (AMD-SG-034 §5); long rules are broken as the layout engine breaks them (§4 item 10), one admissible breaking shown.

```text
STAGE tenure / BACKWARD BUILDER cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_kp≻      : ℝ₊₊ × ℝ₊₊ × ℝ₊₊ → ℝ
       𝑉_adj≻     : ℝ₊₊ × ℝ₊₊ → ℝ
       𝑑𝑉_w_kp≻   : ℝ₊₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊
       𝑑𝑉_h_kp≻   : ℝ₊₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊
       𝑑𝑉_w_adj≻  : ℝ₊₊ × ℝ₊₊ → ℝ₊₊
       ───────────────────────────────────────────────────────────
  out  𝑉          : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ
       𝑑𝑉_a       : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊
       𝑑𝑉_h       : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊

At
  𝑑  : ℝ₊ × ℝ₊₊ × ℝ₊₊ → {keep, adjust}

Where
  𝑔_keep≻    : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊ × ℝ₊₊,
               𝑔_keep≻(a_d, h_d, z_d) = 𝑔≻(a_d, h_d, z_d, keep)
  𝑔_adjust≻  : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊,
               𝑔_adjust≻(a_d, h_d, z_d) = 𝑔≻(a_d, h_d, z_d, adjust)

Operations
  1  Pullback:keep
     in: 𝑉_kp≻, 𝑑𝑉_w_kp≻, 𝑑𝑉_h_kp≻      out: 𝑉_kp≻ ∘ 𝑔_keep≻,
                                             𝑑𝑉_w_kp≻ ∘ 𝑔_keep≻,
                                             𝑑𝑉_h_kp≻ ∘ 𝑔_keep≻
     ─────────────────────────────────────────────────────────────
     rule: (𝑉_kp≻ ∘ 𝑔_keep≻)(a_d, h_d, z_d) = 𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d))
           (𝑑𝑉_w_kp≻ ∘ 𝑔_keep≻)(a_d, h_d, z_d)
             = 𝑑𝑉_w_kp≻(𝑔_keep≻(a_d, h_d, z_d))
           (𝑑𝑉_h_kp≻ ∘ 𝑔_keep≻)(a_d, h_d, z_d)
             = 𝑑𝑉_h_kp≻(𝑔_keep≻(a_d, h_d, z_d))

  2  Pullback:adjust
     in: 𝑉_adj≻, 𝑑𝑉_w_adj≻              out: 𝑉_adj≻ ∘ 𝑔_adjust≻,
                                             𝑑𝑉_w_adj≻ ∘ 𝑔_adjust≻
     ─────────────────────────────────────────────────────────────
     rule: (𝑉_adj≻ ∘ 𝑔_adjust≻)(a_d, h_d, z_d)
             = 𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d))
           (𝑑𝑉_w_adj≻ ∘ 𝑔_adjust≻)(a_d, h_d, z_d)
             = 𝑑𝑉_w_adj≻(𝑔_adjust≻(a_d, h_d, z_d))

  3  Aggregation
     in: (1), (2)                       out: 𝑉, 𝑑𝑉_a, 𝑑𝑉_h
     ─────────────────────────────────────────────────────────────
     rule: 𝑉
             = (𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d)),
                𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[𝑑]
           on (a_d, h_d, z_d) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊
           𝑑𝑉_a
             = (R · 𝑑𝑉_w_kp≻(𝑔_keep≻(a_d, h_d, z_d)),
                R · 𝑑𝑉_w_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[𝑑]
           on (a_d, h_d, z_d) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊
           𝑑𝑉_h
             = ((1 − δ) · 𝑑𝑉_h_kp≻(𝑔_keep≻(a_d, h_d, z_d)),
                R_H · (1 − δ) · 𝑑𝑉_w_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[𝑑]
           on (a_d, h_d, z_d) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊

  4  Evaluation
     in: 𝑉, 𝑑𝑉_a, 𝑑𝑉_h                  out: 𝑉, 𝑑𝑉_a, 𝑑𝑉_h
     ─────────────────────────────────────────────────────────────
     rule: 𝑉 : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ
           𝑑𝑉_a : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊
           𝑑𝑉_h : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊

Conditions
  Aggregation  𝑉(a_d, h_d, z_d) ∈ ℝ
  Aggregation  𝑑𝑉_a(a_d, h_d, z_d) ∈ ℝ₊₊
  Aggregation  𝑑𝑉_h(a_d, h_d, z_d) ∈ ℝ₊₊
──────────────────────────────────────────────────────────────────────────────
Source  tenure.bl
  35  V    = (V_kp[>], V_adj[>])[d]
        :: [id=choice_value]
  36  dV_a = (R*dV_w_kp[>], R*dV_w_adj[>])[d]
        :: [id=marginal_assets]
  37  dV_h = ((1 - δ)*dV_h_kp[>], R_H*(1 - δ)*dV_w_adj[>])[d]
        :: [id=marginal_housing]

Definitions referenced
  R     tenure:parameter:R
  R_H   tenure:parameter:R_H
  δ     tenure:parameter:δ
  𝑔≻    tenure:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The signature lists each branch's values on that branch's set (E6); `at` types the policy plainly (E7); `where` states the two sections of the one law (E4, E5); rows 1 and 2 are the pullbacks, keyed by label; row 3 is the selection, an Aggregation whose rules are the file's three lines at the point with the label read as the policy (E2).

```text
STAGE tenure / FORWARD BUILDER dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ          : finite measure on ℝ₊ × ℝ₊₊ × ℝ₊₊
       ────────────────────────────────────────────────────────
  out  μ_keep≻    : finite measure on ℝ₊₊ × ℝ₊₊ × ℝ₊₊
       μ_adjust≻  : finite measure on ℝ₊₊ × ℝ₊₊

At
  𝑑  : ℝ₊ × ℝ₊₊ × ℝ₊₊ → {keep, adjust}

Where
  𝑔_keep≻    : ℝ₊ × ℝ₊₊ × ℝ₊₊ × Age → ℝ₊₊ × ℝ₊₊ × ℝ₊₊,
               𝑔_keep≻(a_d, h_d, z_d, age_kp) =
                 (R · a_d + Y[age_kp] · z_d + y_R[age_kp], (1 − δ) · h_d, z_d)
  𝑔_adjust≻  : ℝ₊ × ℝ₊₊ × ℝ₊₊ × Age → ℝ₊₊ × ℝ₊₊,
               𝑔_adjust≻(a_d, h_d, z_d, age_adj)
                 = (R · a_d
                      + R_H · (1 − δ) · h_d
                      + Y[age_adj] · z_d
                      + y_R[age_adj],
                    z_d)

Operations
  1  Pushforward
     in: μ                              out: μ_keep≻, μ_adjust≻
     ──────────────────────────────────────────────────────────
     rule: μ_keep≻(B)
             = μ({a_d, h_d, z_d ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊ |
                   𝑑(a_d, h_d, z_d) = keep
                     ∧ 𝑔_keep≻(a_d, h_d, z_d, 𝑎𝑔𝑒_kp≻()) ∈ B})
           μ_adjust≻(B)
             = μ({a_d, h_d, z_d ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊ |
                   𝑑(a_d, h_d, z_d) = adjust
                     ∧ 𝑔_adjust≻(a_d, h_d, z_d, 𝑎𝑔𝑒_adj≻()) ∈ B})

Conditions
  Pushforward  R · a_d + Y[age_kp] · z_d + y_R[age_kp] ∈ ℝ₊₊
──────────────────────────────────────────────────────────────────────────────
Source  tenure.bl
  24  w_kp = R*a_d + Y[age_kp[>]]*z_d + y_R[age_kp[>]]
        :: [id=cash_on_hand]
  25  h_kp = (1 - δ)*h_d
        :: [id=housing_kept]
  26  z_kp = z_d
  29  w_adj = R*a_d + R_H*(1 - δ)*h_d + Y[age_adj[>]]*z_d + y_R[age_adj[>]]
        :: [id=total_wealth]
  30  z_adj = z_d

Definitions referenced
  Age   tenure:set:Age
  R     tenure:parameter:R
  R_H   tenure:parameter:R_H
  δ     tenure:parameter:δ
  Y     tenure:parameter:Y
  y_R   tenure:parameter:y_R
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Row 1 is the fork (E3): one push-forward at 𝑑, one output measure per label, each the mass of the event's preimage on the states the policy sends to that label; the two masses sum to μ's, a condition the record holds as established and the card does not print (E3). The measure's letter follows the open notation brief.

```text
STAGE tenure / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉_kp≻   : ℝ₊₊ × ℝ₊₊ × ℝ₊₊ → ℝ
       𝑉_adj≻  : ℝ₊₊ × ℝ₊₊ → ℝ
       ────────────────────────────────────────────────────────
  out  𝑑       : ℝ₊ × ℝ₊₊ × ℝ₊₊ → {keep, adjust}

Where
  𝑔_keep≻    : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊ × ℝ₊₊,
               𝑔_keep≻(a_d, h_d, z_d) = 𝑔≻(a_d, h_d, z_d, keep)
  𝑔_adjust≻  : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊,
               𝑔_adjust≻(a_d, h_d, z_d) = 𝑔≻(a_d, h_d, z_d, adjust)

Operations
  1  Pullback:keep
     in: 𝑉_kp≻                          out: 𝑉_kp≻ ∘ 𝑔_keep≻
     ──────────────────────────────────────────────────────────
     rule: (𝑉_kp≻ ∘ 𝑔_keep≻)(a_d, h_d, z_d) = 𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d))

  2  Pullback:adjust
     in: 𝑉_adj≻                         out: 𝑉_adj≻ ∘ 𝑔_adjust≻
     ──────────────────────────────────────────────────────────
     rule: (𝑉_adj≻ ∘ 𝑔_adjust≻)(a_d, h_d, z_d)
             = 𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d))

  3  choice:Aggregation
     in: (1), (2)
     out: (a_d, h_d, z_d, d)
            ↦ (𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d)),
               𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[d]
     ──────────────────────────────────────────────────────────
     rule: (a_d, h_d, z_d, d)
             ↦ (𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d)),
                𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[d]

  4  choice:Argmax
     in: (3)                            out: 𝑑
     ──────────────────────────────────────────────────────────
     rule: 𝑑(a_d, h_d, z_d)
             ∈ argmax_{d ∈ {keep, adjust}}
                 [(𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d)),
                   𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[d]]

  5  Evaluation
     in: 𝑑                              out: 𝑑
     ──────────────────────────────────────────────────────────
     rule: 𝑑 : ℝ₊ × ℝ₊₊ × ℝ₊₊ → {keep, adjust}
──────────────────────────────────────────────────────────────────────────────
Source  tenure.bl
  47  d = argmax_{d}(V_kp[>], V_adj[>])  :: [id=choice]

Definitions referenced
  𝑔≻    tenure:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The line is operative, not `!doc`, so it forms a Solution whose rule is the complete line at the point (K66, K69) and no `declared` block; row 3's output falls below its row (K72); the rule states the set of maximisers and no tie rule (E9). The stage card prints both directions' signatures, the two sections and the law lines `(w_kp, h_kp, z_kp) = 𝑔_keep≻(a_d, h_d, z_d)` and `(w_adj, z_adj) = 𝑔_adjust≻(a_d, h_d, z_d)` under `where`, and one row per builder.

## 5 The initial diagrams and the builders graphs

**Forward initial diagram.** Inputs `a≺`, `h≺`, `z≺`, `ε`. Block `arvl_to_dcsn`: line boxes `arvl_to_dcsn.1` (`a≺` → `a_d`), `.2` (`h≺` → `h_d`), `.income_state` (`z≺`, `ε` → `z_d`). Block `dcsn_to_cntn`, coordinate `d`, holding two bubbles (E23): `dcsn_to_cntn.keep` with `cash_on_hand` (`a_d`, `z_d` → `w_kp≻`), `housing_kept` (`h_d` → `h_kp≻`), `3` (`z_d` → `z_kp≻`); `dcsn_to_cntn.adjust` with `total_wealth` (`a_d`, `h_d`, `z_d` → `w_adj≻`), `2` (`z_d` → `z_adj≻`); `a_d`, `h_d`, `z_d` copied to both. Outputs the five branch fields; no decision state, since no backward line reads one.

**Backward initial diagram.** Inputs the five branch values. Block `cntn_to_dcsn`, coordinate `d`: `choice_value` (`V_kp≻`, `V_adj≻` → `V`), `marginal_assets` (`dV_w_kp≻`, `dV_w_adj≻` → `dV_a`), `marginal_housing` (`dV_h_kp≻`, `dV_w_adj≻` → `dV_h`). Block `dcsn_to_arvl`: `value`, `marginal_assets`, `marginal_housing` (`V`, `dV_a`, `dV_h` → `V≺`, `dV_a≺`, `dV_h≺`). Block `policy`: `choice` (`V_kp≻`, `V_adj≻` → `d`), delivered at the boundary (AMD-SG-013 §3). `V_kp≻`, `V_adj≻`, `dV_w_adj≻` are each read twice and copied.

**Backward builders graph** (builder grain). `cntn_to_dcsn`: `Pullback:keep`, `Pullback:adjust`, `Aggregation`, `Evaluation`; the pullbacks' five output wires meet the Aggregation, drawn as two labelled groups and never as one bundle (E17). `dcsn_to_arvl`: `Pullback` along 𝑔≺, `Expectation` over ε, `Aggregation`, `Evaluation`, its input the bundle (𝑉, 𝑑𝑉_a, 𝑑𝑉_h). `policy`: the two pullbacks, `choice:Aggregation`, `choice:Solution`, `Evaluation`, 𝑑 at the boundary, no wire into a backward builder. 𝑉_kp≻ and 𝑉_adj≻ each enter two bubbles.

**Forward builders graph.** `arvl_to_dcsn`: `DistributionExtension:ε`, `Pushforward`. `dcsn_to_cntn`: `Pushforward` at 𝑑, label `𝑔≻,𝑑∗μ`, two output wires to the boundary, μ_keep≻ and μ_adjust≻, on different bases and never bundled.

## 6 The joins of the terminal period, the inter-period connector and the drawing of three periods

Under E15 the bequest's arrival fields are renamed and the terminal period is its own entry of `applications/durables/declaration/trellis.yml`, its connector to the bequest one flat mapping; `period.yml` lists the three other stages with `connectors: []`, and the one inter-period mapping stands for every adjacent pair (A38; `packages/bellman/bellman/bindings/recipe.py:598-599`):

```yaml
periods:
  - stages: [tenure, keeper_cons, adjuster_cons, bequest]
    connectors:
      - {a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}
  - {template: period.yml, repeat: 50}
inter_connectors:
  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}
```

`applications/durables/declaration/stages/bequest/bequest.bl:11-12` then reads `[id=arvl_to_dcsn, (a_bq : ℝ₊, h_bq : ℝ₊₊, z_bq : ℝ₊₊) : !arvl -> (x : ℝ₊₊) : !dcsn]` with `x = R*a_bq + R_H*(1 - δ)*h_bq`; nothing else in the file changes.

**`period_joins(periods[0])`** (`packages/bellman/bellman/stage/joins.py:74-141`) records eleven joins, sorted by source, and no output:

```text
adjuster_cons:a_nxt_adj → bequest:a_bq      keeper_cons:a_nxt_kp → bequest:a_bq
adjuster_cons:h_nxt_adj → bequest:h_bq      keeper_cons:h_nxt_kp → bequest:h_bq
adjuster_cons:z_nxt_adj → bequest:z_bq      keeper_cons:z_nxt_kp → bequest:z_bq
tenure:h_kp → keeper_cons:h_kp              tenure:w_adj → adjuster_cons:w_adj
tenure:w_kp → keeper_cons:w_kp              tenure:z_adj → adjuster_cons:z_adj
tenure:z_kp → keeper_cons:z_kp
```

The six connector joins come from the flat mapping, whose sources no equal-name join reads (A51); the five equal-name joins answer their label, keep or adjust, through `branches(tenure)` (E26). Every continuation field is joined once, E16's fan-out rule; the two sources of each bequest field are the keepers and the adjusters of the terminal period, disjoint sub-populations, and the bequest's arrival measure is their sum (E25). `computable_together` answers `[[tenure], [adjuster_cons, keeper_cons], [bequest]]`, `forward_order` `[tenure, adjuster_cons, keeper_cons, bequest]`, `backward_order` its reverse; there is no cycle, since no stage of the period continues to `a`, `h` or `z`. A period `periods[h]`, h ≥ 1, records the five equal-name joins and the six outputs `adjuster_cons:{a,h,z}_nxt_adj`, `keeper_cons:{a,h,z}_nxt_kp`, with the layers `[[tenure], [adjuster_cons, keeper_cons]]`.

**`inter_period_joins(inter_connectors[h], periods[h + 1], periods[h])`** (`joins.py:218-245`) records six joins for every h, h = 0 included, in the mapping's order: `keeper_cons:a_nxt_kp → tenure:a`, `keeper_cons:h_nxt_kp → tenure:h`, `keeper_cons:z_nxt_kp → tenure:z`, `adjuster_cons:a_nxt_adj → tenure:a`, `adjuster_cons:h_nxt_adj → tenure:h`, `adjuster_cons:z_nxt_adj → tenure:z`, both routes in the one mapping (`docs/Bellman-Sym/07-trelis.md` §2). In period 0 the name `a` is `tenure`'s alone, so the mapping reaches the bequest nowhere and no boundary rule is needed; `tenure:a` takes two sources, the keepers and the adjusters of the period before, and its arrival measure is their sum (E25). Under today's names the same call would record twelve joins for h = 0, six of them into the bequest, the fan-out E16 refuses.

**`draw_trellis(trellis, periods=[0, 1, 2])`** (`packages/bellman/bellman/display/trellis.py:81-140`) writes, under the head of `dot_head` with `rankdir="LR"` and the title naming the two directions, the three clusters in the order 2, 1, 0 and then the twelve inter-period wires; the age in a cluster's label is `last_age − h` where the loaded trellis's `registry.calibration` holds `last_age` = 70 (`applications/durables/declaration/calibration/wage_schedule.yml:24`), and `periods[2]: h = 2` alone otherwise:

```text
  subgraph "cluster_2" {
    graph [label="periods[2]: h = 2, age 68", labelloc="t", labeljust="l"];
    "2:tenure" [label="tenure"];
    "2:adjuster_cons" [label="adjuster_cons"];
    "2:keeper_cons" [label="keeper_cons"];
    "2:tenure" -> "2:keeper_cons" [label="h_kp"];
    "2:tenure" -> "2:adjuster_cons" [label="w_adj"];
    "2:tenure" -> "2:keeper_cons" [label="w_kp"];
    "2:tenure" -> "2:adjuster_cons" [label="z_adj"];
    "2:tenure" -> "2:keeper_cons" [label="z_kp"];
  }
  subgraph "cluster_1" {
    graph [label="periods[1]: h = 1, age 69", labelloc="t", labeljust="l"];
    "1:tenure" [label="tenure"];
    "1:adjuster_cons" [label="adjuster_cons"];
    "1:keeper_cons" [label="keeper_cons"];
    "1:tenure" -> "1:keeper_cons" [label="h_kp"];
    "1:tenure" -> "1:adjuster_cons" [label="w_adj"];
    "1:tenure" -> "1:keeper_cons" [label="w_kp"];
    "1:tenure" -> "1:adjuster_cons" [label="z_adj"];
    "1:tenure" -> "1:keeper_cons" [label="z_kp"];
  }
  subgraph "cluster_0" {
    graph [label="periods[0]: h = 0, age 70", labelloc="t", labeljust="l"];
    "0:tenure" [label="tenure"];
    "0:adjuster_cons" [label="adjuster_cons"];
    "0:keeper_cons" [label="keeper_cons"];
    "0:bequest" [label="bequest"];
    "0:adjuster_cons" -> "0:bequest" [label="a_nxt_adj → a_bq"];
    "0:adjuster_cons" -> "0:bequest" [label="h_nxt_adj → h_bq"];
    "0:adjuster_cons" -> "0:bequest" [label="z_nxt_adj → z_bq"];
    "0:keeper_cons" -> "0:bequest" [label="a_nxt_kp → a_bq"];
    "0:keeper_cons" -> "0:bequest" [label="h_nxt_kp → h_bq"];
    "0:keeper_cons" -> "0:bequest" [label="z_nxt_kp → z_bq"];
    "0:tenure" -> "0:keeper_cons" [label="h_kp"];
    "0:tenure" -> "0:adjuster_cons" [label="w_adj"];
    "0:tenure" -> "0:keeper_cons" [label="w_kp"];
    "0:tenure" -> "0:adjuster_cons" [label="z_adj"];
    "0:tenure" -> "0:keeper_cons" [label="z_kp"];
  }
  "2:keeper_cons" -> "1:tenure" [label="inter_connectors[1]\na_nxt_kp → a"];
  "2:keeper_cons" -> "1:tenure" [label="inter_connectors[1]\nh_nxt_kp → h"];
  "2:keeper_cons" -> "1:tenure" [label="inter_connectors[1]\nz_nxt_kp → z"];
  "2:adjuster_cons" -> "1:tenure" [label="inter_connectors[1]\na_nxt_adj → a"];
  "2:adjuster_cons" -> "1:tenure" [label="inter_connectors[1]\nh_nxt_adj → h"];
  "2:adjuster_cons" -> "1:tenure" [label="inter_connectors[1]\nz_nxt_adj → z"];
  "1:keeper_cons" -> "0:tenure" [label="inter_connectors[0]\na_nxt_kp → a"];
  "1:keeper_cons" -> "0:tenure" [label="inter_connectors[0]\nh_nxt_kp → h"];
  "1:keeper_cons" -> "0:tenure" [label="inter_connectors[0]\nz_nxt_kp → z"];
  "1:adjuster_cons" -> "0:tenure" [label="inter_connectors[0]\na_nxt_adj → a"];
  "1:adjuster_cons" -> "0:tenure" [label="inter_connectors[0]\nh_nxt_adj → h"];
  "1:adjuster_cons" -> "0:tenure" [label="inter_connectors[0]\nz_nxt_adj → z"];
}
```

No plain-label sink is drawn, every output of `periods[1]` and `periods[2]` being read by a wire and `periods[0]` having none, and no invisible edge, each adjacent pair having wires. Laid out, the three clusters stand left to right with `periods[0]` at the right, each holding `tenure` at its left and the two consumption stages beside one another, the bequest at the far right of `periods[0]`, and the twelve wires running from the consumption boxes of one cluster to the `tenure` box of the next. `str(drawing)` lists the ten boxes, `periods[0] tenure: tenure`, `periods[0] adjuster_cons: adjuster_cons`, `periods[0] keeper_cons: keeper_cons`, `periods[0] bequest: bequest`, then the three of `periods[1]` and the three of `periods[2]`. In the first build the label F05 adds to the five equal-name arrows, `keep: h_kp`, is not printed (E26). `draw_period(trellis, 0)` writes the statements of `cluster_0` alone, the nodes named without the `0:` prefix.

## 7 What the present package prints instead today

```text
applications/durables/declaration/stages/tenure/tenure.bl:23:5-27:6: make_stage cannot construct this nested block: task B02 (branching construction) adds its construction rule (address 'dcsn_to_cntn.keep'; rule not-constructed)
```

`load_recipe` of `spec.yml` loads the 51 periods and 50 mappings, since loading elaborates nothing (A46); `elaborate_trellis` refuses at the first `tenure` occurrence with the line above, which `applications/durables/economics.md:243-252` records.
