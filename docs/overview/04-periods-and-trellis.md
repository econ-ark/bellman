---
title: Periods and trellis
tags:
  - bellman-sym
  - user-facing
  - period
  - trellis
  - connector
status: Draft
related:
  - "[[06-period]]"
  - "[[07-trellis]]"
  - "[[08-periods-and-trellis]]"
date: 2026-09-19
audience: user
type: overview
---

# Periods and trellis

> [!summary]
> A period connects stage fields; a trellis connects periods. We introduce the consumption, discounting and investment stages, then inspect a runnable reference variant with investment and discounting in each of six periods.

A model with more than one decision is several stage files joined by connectors. The repository's portfolio application has three.

| Stage file | Contents |
|---|---|
| `cons.bl` | Chooses consumption from resources `m` and leaves assets `a`. |
| `disc.bl` | Discounts value and passes assets through. |
| `port.bl` | Chooses the risky share before the return and next income are drawn, and produces next resources `m_next`. |

Within a period, field names belong to their own stage. Consumption's continuation assets `a` and discounting's arrival assets `a` are distinct fields, selected as one connection only if they are the unique compatible, globally consistent same-name pair. An authored **connector** selects fields whether their names agree or differ: `{"disc.a": "k"}` specifies discounting's continuation assets and investment's arrival capital. The stage-key prefix identifies the source when several stages have an outgoing `a`; it does not rename the field. [Periods](../Bellman-Sym/06-period.md#2-connectors) gives the complete rule.

Between periods, `inter_connectors[h]` joins the outgoing fields of period `h+1` to the incoming fields of period `h`, where `h` counts backwards from the terminal period, `h = 0`.

The checked reference variant below contains a portfolio stage and a discount stage in each of six periods. It shows one connection within the terminal period and one from the period before it. Its trellis file carries each stage's source and bindings, so `load_trellis` reads the model as written and `specify_trellis` elaborates, calibrates, methodizes and configures every occurrence. `connection_report` reads the selected connections; `periods=[0]` keeps pairs touching the terminal period. Run this listing from the repository root:

```python
from bellman.trellis import connection_report, load_trellis, specify_trellis

source = load_trellis("applications/cons-port/declaration/trellis.reference-port-only.yml")
model = specify_trellis(source)
report = connection_report(model, periods=[0])

print(len(model["periods"]), len(report.pairs), len(report.routes), len(report.diagnostics))
for pair in report.pairs:
    print(f"{pair.writing} -> {pair.reading} ({pair.origin}, {pair.compatibility})")
```

```text
6 2 2 0
periods[0].port.w -> periods[0].disc.a (authored, compatible)
periods[1].disc.a -> periods[0].port.k (authored, compatible)
```

The first pair joins the portfolio stage to discounting inside the terminal period. The second joins the preceding period's discount stage to the terminal period's portfolio stage. The stage keys and period indices identify the fields; the pair changes neither stage's local name. The report also checks complete state and value routes, including the forward joint law, as [Periods](../Bellman-Sym/06-period.md#2-connectors) explains. The four numbers and two pair lines above were checked against the package in this checkout.

A trellis is also built one period at a time. `bellman.trellis.accrete(trellis, period, inter_connector=None)` appends a period, the one earlier in time, to a trellis that starts as `{"periods": [], "inter_connectors": []}`, the terminal period first. A hand-written trellis can use `accrete` once for the terminal period and again for each earlier period, passing that pair's inter-period connector with the later call. [Periods](../Bellman-Sym/06-period.md) and [Trellises](../Bellman-Sym/07-trellis.md) explain the period boundary and the terminal continuation value that the trellis needs.
