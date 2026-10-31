"""The pair of perches a builder joins, the classification of a stage's
builders by that pair, and the word of each direction in the paths that read
a builders graph.

Held apart from :mod:`bellman.stage.pieces`, which builds `stage.builder`
from `builder_pairs`, and from :mod:`bellman.stage.denotations`, which reads
a builder's pair for its card's title: `pieces` already imports
`denotations`, since a builder's `denote()` composes its record there, so a
module either of them imports back would close a cycle. This module
imports neither of them, so both may import it, and so may
:mod:`bellman.stage.inventory`, which `pieces` imports and which reads a
builders graph by the word of its direction.
"""

from __future__ import annotations

from bellman.fold.block_lines import perches_of
from bellman.native.labels import is_wiring
from bellman.refusals import NotConstructed
from bellman.stage.grains import DIRECTIONS, graph_of, wire_table
from bellman.syntax.vocabulary import ARRIVAL, CONTINUATION, DECISION

# the pairs a forward builder may join, in the order the listing prints
FORWARD_PAIRS = ((ARRIVAL, DECISION), (DECISION, CONTINUATION))
# the pairs a backward builder may join, in the order the listing prints
BACKWARD_PAIRS = ((CONTINUATION, DECISION), (DECISION, ARRIVAL))

# the word of each direction (AAS, 29 September 2026), as
# `stage.builder.list()` prints it and as a refusal writes the key that reads
# a builder by its block id, `stage.builder.bwd['policy_c']`; the stage sheet
# and the dossier read a builders graph through it,
# `getattr(stage.builder, DIRECTION_WORDS[direction])`. If AAS chooses `sol`
# and `sim`, the rename also changes by hand the properties `bwd` and `fwd`
# of `BuilderPairs` and `PerchBuilders` in `pieces.py`; the literals "fwd"
# and "bwd" in `PerchBuilders._pair`, `_reach` and `list()`; the refusal
# texts that write `stage.builder.bwd` or `stage.builder.fwd`, those of
# `target-not-found` and `kernel-target` in `boxes.py`, of `to_drawing` in
# `display/drawing.py` and of `builder_kernels` in `pieces.py`; the refusal
# texts that name `stage.cntn.builder.fwd`, `stage.cntn.builder.bwd` and
# `stage.dcsn.builder.fwd`; and their tests
DIRECTION_WORDS = {"backward": "bwd", "forward": "fwd"}


def arrow(pair):
    """`cntn → dcsn`, the printed form of a pair of perches."""
    return f"{pair[0]} → {pair[1]}"


def builder_pairs(stage):
    """Every builder of both builders graphs by the ordered pair of perches
    it joins, read from the wire table (`perches_of`), never from the block
    id: a mapping from `(source, target)` to the boxes that join them,
    normally one; the policy builders, the backward builders whose outputs
    are controls (`policy_blocks`), apart, in a list that normally holds
    one; and, for a direction the construction refused, the refusal, so that
    a pair of that direction can report it."""
    wires = wire_table(stage)
    pairs, policies, refused = {}, [], {}
    for direction in DIRECTIONS:
        try:
            boxes = graph_of(stage, "builders", direction).boxes
        except NotConstructed as refusal:
            refused[direction] = refusal
            continue
        for box in boxes:
            if is_wiring(box):
                continue
            # the wire table reads a policy block as joining the pair of the
            # decision builder, `cntn → dcsn`, so it is read by its own key
            if direction == "backward" and box.name in wires.policy_blocks:
                policies.append(box)
                continue
            pairs.setdefault(perches_of(wires.box_of[box.name], wires.ports), []).append(box)
    return pairs, policies, refused
