<!-- notebook cell 21 | id: cell-7 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

<div style="border-top: 2px solid rgba(0,0,0,0.15); margin: 2.5em 0 1em;"></div>

## Build periods

A **period** in dolo-plus is two things: a shared namespace of random variables (the shocks that drive uncertainty within the period) and an ordered list of **stage occurrences**. The ordering matters: when we solve backward we recurse from the last stage to the first, passing continuation-value functions from one stage to the one before it; when we simulate forward we walk the list in the opposite direction. (We discuss branching stages in a seperate notebook.)

The wiring rule between stages is simple: **stages compose when the continuation variable of one stage is the arrival variable of the next**. Think of a directed graph in which each stage maps an arrival node to a continuation node — the arrival perch is the in-plug, the continuation perch is the out-plug. If the consumption stage produces a continuation variable $a$ (post-decision savings) and the next stage expects an arrival variable also called $a$, the two stages snap together with no extra machinery. This identity wiring is the default and can be left implicit — in graph terms the two edges share a common interior node labelled $a$, and composition is just path concatenation. Names don't always line up, however. The consumption stage may call its continuation variable $a$ while the portfolio stage expects an arrival variable $k$. A **connector** bridges the gap: a plain dictionary `{"a": "k"}` that renames the out-plug of one stage to match the in-plug of the next. In `dolo-plus` syntax a connector is simply `{a: k}` — a YAML dict of source-to-target variable names. Stages never need to know what comes before or after them.

The same mechanism works across periods, but with one important difference in namespace scope. Within a single period every variable name refers to exactly one quantity, so a connector `{"a": "k"}` is unambiguous. Between periods the namespace is *not* shared — both $\mathcal{P}_t$ and $\mathcal{P}_{t-1}$ may each contain a variable called $a$. An **inter-period connector** `{"a": "m"}` sitting between $\mathcal{P}_t$ and $\mathcal{P}_{t-1}$ therefore adopts a directional convention aligned with the backward sweep: **keys name variables in the backward-preceding period** (the later period $\mathcal{P}_t$, whose continuation value we already have) **and values name variables in the backward-successive period** ($\mathcal{P}_{t-1}$, whose arrival perch we are about to enter). In the common case where the last stage of period $t$ produces continuation savings $a$ and the first stage of the same period structure at $t-1$ expects arrival cash-on-hand $m$, the inter-period connector is simply `{"a": "m"}`.

The **period operator** $\mathbb{T}$ is the composition of its stage operators $\mathbb{S}$ in backward order. For beginning-returns, $\mathbb{T}_{\text{beg}} = \mathbb{S}_{\text{port}} \circ \mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{disc}}$.

Finally, in the model we are studying a **discount stage** $\mathbb{S}_{\text{disc}}$ sits at the end of each period. It is a thin standalone operator $\mathbb{S}_{\text{disc}}(v) = \beta\, v$ that scales the continuation value (and its derivative) by the discount factor. Because it is the last stage in forward time it is applied *first* in the backward sweep, ensuring that all upstream economic stages — consumption, portfolio, income — remain $\beta$-free and therefore reusable across configurations with different discount factors.

#### Data structure

Since connectors, periods, and nests are straightforward declarative syntax — just names, orderings, and renaming dicts — we represent them directly as plain Python dicts without introducing any special objects. A **period** is a collection of stages and connectors:

```python
period = {
    "stages":     {"cons_stage": ..., "port_stage": ...},   # configured stage objects
    "connectors": [{"a": "k"}],                              # intra-period connectors
}
```

The `"stages"` dict holds the configured stage objects (output of `bind_stage`). The `"connectors"` list holds connector dicts interleaved between consecutive stages — an empty list means all stage boundaries are identity wiring (matching variable names).

A **nest** is a collection of periods and inter-period connectors:

```python
nest = {
    "periods":          [period_H, period_H1, ..., period_0],  # one per horizon step
    "inter_connectors": [{"a": "k"}, {"a": "k"}, ...],         # one between each pair
}
```

At each backward step we build a fresh period (with fresh stage instances), append it to the nest, and record the inter-period connector that wires it to the previous period. The solver walks this list, applying each period's operators in sequence.
