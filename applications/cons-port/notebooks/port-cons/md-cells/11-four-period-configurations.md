<!-- notebook cell 25 | id: cell-9-3460a1a5 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

<div style="border-top: 2px solid rgba(0,0,0,0.15); margin: 2.5em 0 1em;"></div>

## Four period configurations

The same stage building blocks compose into four period configurations, each a valid economic model:

| Config | Stages (forward) | Period operator $\mathbb{T}$ | Intra-period connector | Inter-period connector |
|--------|------------------|-------------------------------|------------------------|------------------------|
| **Cons-only** | noport $\to$ cons $\to$ disc | $\mathbb{S}_{\text{noport}} \circ \mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{disc}}$ | — | $\{a \mapsto k\}$ |
| **Beg-returns** | port $\to$ cons $\to$ disc | $\mathbb{S}_{\text{port}} \circ \mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{disc}}$ | — | $\{a \mapsto k\}$ |
| **End-returns** | cons $\to$ port $\to$ disc | $\mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{port}} \circ \mathbb{S}_{\text{disc}}$ | $\{a \mapsto k\}$ | $\{m \mapsto m\}$ |
| **Port-only** | port $\to$ disc (Merton) | $\mathbb{S}_{\text{port}} \circ \mathbb{S}_{\text{disc}}$ | — | $\{m \mapsto k\}$ |

All four end with a **disc stage** that scales the continuation by $\beta$. The economic stages (cons, port, noport) are $\beta$-free — they see a continuation that has already been discounted.

The two multi-stage configurations illustrate the connector mechanism. In **beginning-returns**, portfolio returns are realized before consumption: port outputs cash-on-hand $m$, and cons expects arrival $m$ — names match, so no intra-period connector is needed. But between periods, cons outputs savings $a$ while port expects wealth $k$, so the inter-period connector $\{a \mapsto k\}$ bridges the gap. In **end-returns** the stages swap order and so does the wiring: cons outputs $a$ but port expects $k$ *within* the same period, requiring an intra-period connector $\{a \mapsto k\}$; between periods, port outputs $m$ and cons expects $m$, so the inter-period connector is identity.

<div style="display:flex; flex-wrap:wrap; gap:1rem; justify-content:center; align-items:flex-start; margin:0.9em 0 0.4em;">

  <figure style="margin:0; text-align:center;">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 96" style="width:400px; max-width:100%; height:auto;">
      <defs>
        <marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#fff"/>
        </marker>
        <marker id="arrF1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#fff" opacity="0.55"/>
        </marker>
      </defs>
      <circle cx="26" cy="42" r="3.5" fill="#fff"/>
      <text x="26" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">k</text>
      <line x1="30" y1="42" x2="112" y2="42" style="stroke:#fff; stroke-width:1.1;" marker-end="url(#arr1)"/>
      <text x="71" y="36" text-anchor="middle" style="font-family:Inter,Helvetica,sans-serif; font-size:9.2px; fill:#fff; font-weight:600;">port</text>
      <circle cx="116" cy="42" r="3.5" fill="#fff"/>
      <text x="116" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">m</text>
      <line x1="120" y1="42" x2="202" y2="42" style="stroke:#fff; stroke-width:1.1;" marker-end="url(#arr1)"/>
      <text x="161" y="36" text-anchor="middle" style="font-family:Inter,Helvetica,sans-serif; font-size:9.2px; fill:#fff; font-weight:600;">cons</text>
      <circle cx="206" cy="42" r="3.5" fill="#fff"/>
      <text x="206" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">a</text>
      <line x1="210" y1="42" x2="292" y2="42" style="stroke:#fff; stroke-width:1.1;" marker-end="url(#arr1)"/>
      <text x="251" y="36" text-anchor="middle" style="font-family:Inter,Helvetica,sans-serif; font-size:9.2px; fill:#fff; font-weight:600;">disc</text>
      <circle cx="296" cy="42" r="3.5" fill="#fff"/>
      <text x="296" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">a</text>
      <path d="M 296 46 C 308 88 14 88 26 46" style="stroke:#fff; stroke-width:1; stroke-dasharray:5 3; fill:none; opacity:0.55;" marker-end="url(#arrF1)"/>
      <text x="161" y="84" text-anchor="middle" style="font-family:Inter,sans-serif; font-size:8.6px; fill:#fff; opacity:0.62;">{a ↦ k}  connector</text>
    </svg>
    <figcaption style="font-size:11px; opacity:0.5; margin-top:0.25rem;">
      Beginning-returns — no intra-period connector (port.m = cons.m)
    </figcaption>
  </figure>

  <figure style="margin:0; text-align:center;">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 96" style="width:425px; max-width:100%; height:auto;">
      <defs>
        <marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#fff"/>
        </marker>
        <marker id="arrF2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#fff" opacity="0.55"/>
        </marker>
      </defs>
      <circle cx="26" cy="42" r="3.5" fill="#fff"/>
      <text x="26" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">m</text>
      <line x1="30" y1="42" x2="112" y2="42" style="stroke:#fff; stroke-width:1.1;" marker-end="url(#arr2)"/>
      <text x="71" y="36" text-anchor="middle" style="font-family:Inter,Helvetica,sans-serif; font-size:9.2px; fill:#fff; font-weight:600;">cons</text>
      <circle cx="116" cy="42" r="3.5" fill="#fff"/>
      <text x="116" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">a</text>
      <line x1="120" y1="42" x2="152" y2="42" style="stroke:#fff; stroke-width:1; stroke-dasharray:5 3; opacity:0.55;" marker-end="url(#arrF2)"/>
      <text x="136" y="36" text-anchor="middle" style="font-family:Inter,sans-serif; font-size:8.6px; fill:#fff; opacity:0.62;">{a↦k}</text>
      <circle cx="156" cy="42" r="3.5" fill="#fff"/>
      <text x="156" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">k</text>
      <line x1="160" y1="42" x2="244" y2="42" style="stroke:#fff; stroke-width:1.1;" marker-end="url(#arr2)"/>
      <text x="202" y="36" text-anchor="middle" style="font-family:Inter,Helvetica,sans-serif; font-size:9.2px; fill:#fff; font-weight:600;">port</text>
      <circle cx="248" cy="42" r="3.5" fill="#fff"/>
      <text x="248" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">m</text>
      <line x1="252" y1="42" x2="332" y2="42" style="stroke:#fff; stroke-width:1.1;" marker-end="url(#arr2)"/>
      <text x="292" y="36" text-anchor="middle" style="font-family:Inter,Helvetica,sans-serif; font-size:9.2px; fill:#fff; font-weight:600;">disc</text>
      <circle cx="336" cy="42" r="3.5" fill="#fff"/>
      <text x="336" y="30" text-anchor="middle" style="font-family:Georgia,serif; font-style:italic; font-size:11px; fill:#fff;">m</text>
      <path d="M 336 46 C 350 88 12 88 26 46" style="stroke:#fff; stroke-width:1; stroke-dasharray:5 3; fill:none; opacity:0.55;" marker-end="url(#arrF2)"/>
      <text x="181" y="84" text-anchor="middle" style="font-family:Inter,sans-serif; font-size:8.6px; fill:#fff; opacity:0.62;">{m ↦ m}  connector (identity)</text>
    </svg>
    <figcaption style="font-size:11px; opacity:0.5; margin-top:0.25rem;">
      End-returns — connector {a ↦ k} bridges cons→port
    </figcaption>
  </figure>

</div>

The diagrams read left-to-right in forward time. Nodes are random variables; edges are stages; dashed lines are connectors. The same three stages appear in both configurations — only the wiring changes.
