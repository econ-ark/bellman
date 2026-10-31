#!/usr/bin/env python3
"""Generate the period DAG for the retirement choice model.

Black-and-white, horizontal layout. Uses only actual model labels
(stage instance names, field names, branch keys).
"""

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ── Palette: black & white ────────────────────────────────────────────
BLACK    = "#000000"
DARK     = "#333333"
MID      = "#888888"
LIGHT    = "#e0e0e0"
WHITE    = "#ffffff"
FILL_STG = "#f5f5f5"   # very light gray for stages

G = nx.DiGraph()

# Nodes: prestates, stages, poststates — using actual model names
G.add_node("a",           label="$a$",                    kind="field")
G.add_node("a_ret",       label="$a_{\\mathrm{ret}}$",    kind="field")
G.add_node("branch",      label="labour_mkt_decision",    kind="stage")
G.add_node("work",        label="work_cons",              kind="stage")
G.add_node("retire",      label="retire_cons",            kind="stage")
G.add_node("a_nxt",       label="$a_{\\mathrm{nxt}}$",    kind="field")
G.add_node("a_ret_nxt",   label="$a_{\\mathrm{ret,nxt}}$", kind="field")

# Edges with branch keys
G.add_edge("a",         "branch",    label="")
G.add_edge("branch",    "work",      label="work")
G.add_edge("branch",    "retire",    label="retire")
G.add_edge("a_ret",     "retire",    label="")
G.add_edge("work",      "a_nxt",     label="")
G.add_edge("retire",    "a_ret_nxt", label="")

# ── Layout (left → right) ────────────────────────────────────────────
pos = {
    "a":          (0.0,   0.6),
    "a_ret":      (0.0,  -0.8),
    "branch":     (1.8,   0.6),
    "work":       (3.8,   1.4),
    "retire":     (3.8,  -0.4),
    "a_nxt":      (5.6,   1.4),
    "a_ret_nxt":  (5.6,  -0.4),
}

# ── Node styles ───────────────────────────────────────────────────────
style_field = dict(node_color=WHITE, node_shape="s", node_size=1600,
                   edgecolors=BLACK, linewidths=1.5)
style_stage = dict(node_color=FILL_STG, node_shape="o", node_size=2800,
                   edgecolors=BLACK, linewidths=1.5)

# ── Figure ────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4.2), facecolor=WHITE)
ax.set_facecolor(WHITE)

# Draw field nodes (squares)
fields = [n for n, d in G.nodes(data=True) if d["kind"] == "field"]
nx.draw_networkx_nodes(G, pos, nodelist=fields, ax=ax, **style_field)

# Draw stage nodes (circles)
stages = [n for n, d in G.nodes(data=True) if d["kind"] == "stage"]
nx.draw_networkx_nodes(G, pos, nodelist=stages, ax=ax, **style_stage)

# Labels
labels = {n: d["label"] for n, d in G.nodes(data=True)}
nx.draw_networkx_labels(G, pos, labels, ax=ax,
                        font_size=10, font_color=BLACK,
                        font_family="sans-serif")

# Edges
nx.draw_networkx_edges(
    G, pos, ax=ax,
    edge_color=DARK, width=1.4,
    arrows=True, arrowstyle="-|>", arrowsize=14,
    connectionstyle="arc3,rad=0.06",
    min_source_margin=20, min_target_margin=20,
)

# Edge labels (branch keys only)
elabels = {(u, v): d["label"] for u, v, d in G.edges(data=True) if d["label"]}
nx.draw_networkx_edge_labels(
    G, pos, elabels, ax=ax,
    font_size=9, font_color=DARK, font_family="sans-serif",
    font_weight="bold",
    bbox=dict(boxstyle="round,pad=0.1", fc=WHITE, ec="none"),
)

# ── Period boundary (dashed rectangle) ────────────────────────────────
rect = FancyBboxPatch(
    (-0.6, -1.35), 6.85, 3.45,
    boxstyle="round,pad=0.15", linewidth=1.2,
    edgecolor=MID, facecolor="none", linestyle=(0, (5, 3)),
)
ax.add_patch(rect)
ax.text(-0.4, 1.95, "LifecyclePeriod", fontsize=9,
        color=MID, fontfamily="sans-serif", fontstyle="italic")

ax.axis("off")
ax.set_xlim(-1.0, 6.6)
ax.set_ylim(-1.55, 2.25)
fig.tight_layout(pad=0.3)

out = "retirement_choice_period_dag.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=WHITE)
print(f"Saved {out}")
