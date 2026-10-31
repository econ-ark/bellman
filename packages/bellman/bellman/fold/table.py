"""The construction table and its rows.

`ConstructionTable` holds a stage's definitions, its rows with every
sub-builder open (`primitive_rows`, the primitive grain), the rows of each
backward block with its sub-builders closed (`sub_builder_rows`), and the
obligations the conditions raise. `BlockRows` holds the rows of one block at
those two grains. `OperatorRow` is one row: the operator a box of a builder
denotes, of a kind in `KINDS`, with its wires, the identities its kind
references, the statements it realizes, its map as a reduced term, the
parameters, shocks and policy functions its terms name, and the properties
attached to its line by a dotted id.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import NamedTuple


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstructionTable:
    """The construction table: the definitions, the rows with every
    sub-builder open (``primitive_rows``, the primitive grain), the rows of
    each backward block with its sub-builders closed (``sub_builder_rows``,
    block → rows), and the obligations the conditions raise. A forward
    block's rows are one tuple at both grains, which ``sub_builder_rows``
    does not hold; ``sub_builder_rows`` holds a backward block's rows even
    where it has no sub-builder, since its primitive grain also merges
    parallel boxes on one value bundle."""

    stage: str
    definitions: tuple
    primitive_rows: tuple
    obligations: tuple  # condition, identities, sentence, optional local names
    sub_builder_rows: tuple = ()  # (block, rows) pairs

    def by_builder(self, builder, *, grain="primitive"):
        """The rows of one builder at a grain: at the sub-builder grain
        (`node`), its rows with the sub-builders closed where the table holds
        them; otherwise, and for a forward builder, its rows at the primitive
        grain."""
        if grain == "node":
            for block, rows in self.sub_builder_rows:
                if block == builder:
                    return rows
        return tuple(op for op in self.primitive_rows if op.builder == builder)


class BlockRows(NamedTuple):
    """The rows of one block at two grains: `primitive`, every sub-builder
    opened, and `sub_builder`, each sub-builder one box. A forward block's
    rows are one object held at both."""

    primitive: tuple
    sub_builder: tuple


# The kinds of a row: the constituent operations of the catalogue, the
# pullback, the pointwise aggregation, the expectation, the evaluation and the
# maximization `Argmax`, and the three forward operations.
KINDS = (
    "Pullback",
    "Aggregation",
    "Expectation",
    "Evaluation",
    "Argmax",
    "Pushforward",
    "PolicyInsertion",
    "DistributionExtension",
)


@dataclass(frozen=True, slots=True)
class OperatorRow:
    """One row of the construction table: the operator a box of a builder
    denotes. ``references`` is the box's data, the identities its kind
    takes; ``node`` names the sub-builder the row sits in at the sub-builder
    grain, None at the block level. The other fields serve the construction of
    the graphs and the queries: the wires, the bound coordinates of the
    functions the operator defines (``arguments``), the statements it
    realizes, its map as a reduced term with wire symbols in place of its value
    inputs (``maps``, one per output, for an aggregation whose rule is an
    explicit equation) and the parameters the terms name.

    ``unknowns`` are the fields a row's rule holds on both of its sides, the
    outputs its rule states a relation in, and are empty on a row whose rule
    defines its outputs explicitly: the `Argmax` of an operative maximization,
    the `Aggregation` of a relational line and the `Pullback` of the
    identification hold them. The ``maps`` of an `Aggregation` with unknowns
    are the explicit side of its relation where the line writes one, the
    candidate's `𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻)`, or the residuals of a `solve`, and none for a
    system of candidate statements. ``properties`` are the addresses of the
    lines a dotted id attaches to the line the row realizes, `optimality.euler`
    to `optimality`, which the row holds and does not realize. Every field
    after the identity is given by keyword."""

    identity: str
    _: KW_ONLY
    kind: str
    builder: str
    direction: str  # backward | forward
    statements: tuple
    inputs: tuple
    outputs: tuple
    references: tuple = ()
    parameters: tuple = ()
    definition: str | None = None  # identity of the g or G referenced
    distribution: str | None = None  # identity of the distribution referenced
    unknowns: tuple = ()
    arguments: tuple = ()
    node: str | None = None
    maps: tuple = ()
    equations: tuple = ()  # the authored terms of the row, which its card prints
    conditions: tuple = ()  # membership and definedness predicates of those terms
    integrated: tuple = ()  # the shocks an expectation integrates, in the edge's order
    given: tuple | None = (
        None  # the shocks its selected conditional conditions on; None outside a value fold
    )
    policy: tuple = ()  # the policy functions the row is held at (AMD-SG-013 §2)
    section: str | None = None  # the label of the branch whose section a Pullback composes with
    properties: tuple = ()  # the lines attached to the row's line by a dotted id
    # the derivatives of the value an Evaluation writes that the block's derivative
    # lines state (AMD-MB-001 §4.3, D4): one entry per line, the tuple
    # (coordinate identity, right-side term, line address, source text)
    derivatives: tuple = ()

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown operator kind {self.kind!r}")
