"""The pieces of a stage, each reached from the piece that contains it
(AMD-SG-010 §4).

One root, the stage, and the same verbs at every level where they make sense:
`denote()`, `list()`, `diagram()`, `kernel()`, `compile_kernel()`,
`signature()`, `methods`, with `graph` and `box` giving the DisCoPy object,
and `kernels()` on a builder, the record of its pieces' kernels.
Below the stage `denote()` is the one verb that says what a piece is and what
it denotes, and `view` is no verb of these objects (AMD-SG-021 §2.1); the
stage keeps both, being an occurrence with an inventory and not a phrase.

`stage.initial` holds the two initial diagrams, `backward` and `forward`, and
`stage.builder` the builders, each read by the ordered pair of perches it
joins: `stage.builder["cntn", "dcsn"]` is the backward builder from
continuation to decision, and `stage.builder["arvl", "dcsn"]` the forward
builder from arrival to decision. `stage.builder.policy` is the policy
builder, the backward builder that writes the controls. `stage.builder.bwd`
and `stage.builder.fwd` are the two builders graphs: the backward builders a
solution applies, and the forward builders a simulation applies. The pair is
read from the perches the wire table holds for the block a builder denotes
(`builder_pairs.builder_pairs`), and never from the block id the author
wrote, which may be any name. The perch handles `stage.arvl`, `stage.dcsn`
and `stage.cntn` reach the builders of the edge that leaves each perch, each
path defined as one key of `stage.builder`: `stage.dcsn.builder.bwd` is
`stage.builder["cntn", "dcsn"]`, `stage.dcsn.builder.fwd` is
`stage.builder["dcsn", "cntn"]`, and `stage.dcsn.builder.policy` is
`stage.builder.policy`. A block or a builder is also a key of the graph that
holds it, `stage.initial.backward["cntn_to_dcsn"]` and
`stage.builder.bwd["cntn_to_dcsn"]`; `["pullback"]` is the primitive box
inside a builder, `["risk_ce", "expectation:1"]` a box inside the sub-builder
of a node, and `.primitives` the same graph or piece with its bubbles opened.

Each of these is a navigation object: a frozen record holding the version and
the object it addresses, and nothing else. Its verbs forward to the module
functions, `denotations.denotation_of(stage, box)`,
`kernels.kernel(stage, box)`, `kernels.compile_kernel(stage, box)`,
`grains.graph_of(stage, level, direction, grain)`,
`drawing.to_drawing(graph)` with the arguments `drawing_arguments(stage,
graph)` of this module gives it, and `builder_kernels(stage, builder)` of
this module, which are the implementation beneath the object forms and are
bound as no method of the stage. Nothing is stored and nothing is
cached: the box a handle holds is the box the stored graph holds, and the
handle is made when it is asked for. The tables `stage.par` and
`stage.settings` and the methods every piece answers are read-only mappings
of the same kind: each reads the one place the version holds what it answers,
the definitions table and the bindings, and keeps no copy.

A record of `records.py` cannot hold its stage: a field pointing back at the
stage would be a cycle, and `hypergraphs.copy_native`, which every binding verb
applies, refuses one. The stage is therefore bound when the attribute is read.
`stage.definitions`, `stage.initial` and `stage._builders` are descriptors
(`StoredAttribute`), each of which stores the record it is given. The first
two answer with the navigation object made at that moment from the version and
that record. `_builders` answers the record itself, but the package reads that
record with `stored(stage, "_builders")` and never through the attribute; the
builders are reached through the property `stage.builder`, a `BuilderPairs`
made from the version when it is read. A version reached through a chain,
`stage.calibrate(values).builder["cntn", "dcsn"]`, is therefore read as easily
as one bound to a name, because the navigation object holds its version while
it lives.
"""

from __future__ import annotations

import dataclasses
import keyword
import unicodedata
from collections.abc import Mapping

from discopy.frobenius import Bubble

from bellman.display.drawing import drawing_title, to_drawing
from bellman.display.printed_records import (
    BuilderKernels,
    Listing,
    Methods,
    NamedListing,
    PieceKernel,
)
from bellman.fold.wire_terms import term_nodes
from bellman.native.hypergraphs import BellmanHypergraph
from bellman.native.identity import Identity, IdentityCollision
from bellman.native.labels import is_wiring
from bellman.native.records import Definition, bound_at
from bellman.native.versions import store, stored
from bellman.refusals import ConstructionError, NotConstructed, TargetError
from bellman.stage.boxes import (
    box_obligations,
    boxes_inside,
    bubble_at,
    bubble_listing,
    graph_listing,
    is_block,
    level_listing,
    lines_with_no_wire,
    methods_bound_within,
    methods_of_line,
    methods_within,
    piece_and_place,
    piece_named,
    piece_word,
    row_of,
)
from bellman.stage.builder_pairs import (
    BACKWARD_PAIRS,
    DIRECTION_WORDS,
    FORWARD_PAIRS,
    arrow,
    builder_pairs,
)
from bellman.stage.defining_expressions import (
    drawn_laws,
    drawn_wire_names,
    state_choice_measure,
    wire_name,
)
from bellman.stage.denotations import (
    box_signature,
    denotation_of,
    denotation_of_block,
    denotation_of_builder,
    denotation_of_definition,
    denotation_of_graph,
    graph_signature,
)
from bellman.stage.grains import (
    DIRECTIONS,
    derived_graph_at_grain,
    graph_of,
    is_relation,
    kind_of,
    stored_graph,
    wire_table,
)
from bellman.stage.inventory import definitions_listing
from bellman.stage.kernels import compile_kernel, derivative_pieces, kernel
from bellman.stage.method_blocks import declared_version
from bellman.stage.method_table import attachment_places
from bellman.stage.method_targets import resolve_target
from bellman.stage.stage_answers import (
    UNBOUND,
    obligations,
    parameter_rows,
    parameters_of,
    setting_rows,
    settings_of,
)
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import ARRIVAL, CONTINUATION, DECISION, PERCH_WORD

# --- the three stored attributes of a stage ---


class StoredAttribute:
    """One of the five attributes whose stored value is a record of this
    version: `definitions` and `initial`, whose read is a navigation object
    (AMD-SG-010 §4), and `_builders`, `bindings` and `provenance`, whose read
    is the record itself. The
    package reads that record with `stored(stage, "_builders")`, never through
    the attribute, and `stage.builder` is the public attribute that reads the
    builders.

    The record itself holds no reference to the stage: a field pointing back
    at it would be a cycle, which `hypergraphs.copy_native` refuses. The
    descriptor keeps the record under its own name in the object's dictionary
    and, for `definitions` and `initial`, builds the navigation object, which
    holds the version, when the attribute is read. So a version reached
    through a chain, `stage.calibrate(values).initial.backward`, is read as
    easily as one bound to a name, and nothing outside the object is
    consulted. Code inside the package that wants the record reads it with
    `stored(stage, name)`.
    """

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, stage, owner=None):
        if stage is None:
            # read on the class: the attribute has no default value
            raise AttributeError(self.name)
        return navigation_of(stage, self.name, stored(stage, self.name))

    def __set__(self, stage, value):
        store(stage, self.name, value)


def navigation_of(stage, attribute, record):
    """The navigation object for a stored attribute: the definitions table or
    the initial diagrams; the builders record is stored under `_builders` and
    is read inside the package by `stored(stage, "_builders")`, the public
    attribute that reads it being `stage.builder` (`BuilderPairs`)."""
    if attribute == "definitions":
        return Definitions(stage, record)
    if attribute == "initial":
        return Initial(stage, record)
    return record


class _Handle:
    """What every navigation object shares: it is made when it is asked for,
    so two of them for one piece of one version are two objects and must
    compare equal. Equality is the same version — the same object, not a stage
    equal to it — and the same piece of it."""

    def _addresses(self):
        raise NotImplementedError

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self.version is other.version and self._addresses() == other._addresses()

    def __hash__(self):
        return hash((type(self).__name__, id(self.version), self._addresses()))


@dataclasses.dataclass(frozen=True, eq=False)
class Definitions(Mapping):
    """The version's read-only definitions table, from each identity to its
    record in file order. `list()` groups identities by kind and
    `denote(identity)` answers a declaration or authored line's card.
    `version` is the stage whose definitions are read. Tables compare by
    contents and are not hashable.

    See `docs/Bellman-Sym/API/stage/08-definitions.md` §1."""

    version: object
    _table: Mapping

    @property
    def table(self):
        raise AttributeError(
            "the stored table is read inside the package with "
            "versions.stored(stage, 'definitions'); this object answers a record by its "
            "identity, list() and denote(identity)"
        )

    def __repr__(self):
        return f"Definitions({self.version.name!r}, {len(self._table)} records)"

    def __getitem__(self, identity):
        return self._table[identity]

    def __iter__(self):
        return iter(self._table)

    def __len__(self):
        return len(self._table)

    def list(self):
        """The identities grouped by definition kind, in table order, displayed
        with each declaration's map or relation and cited rule.

        See `docs/Bellman-Sym/API/stage/08-definitions.md` §1."""
        return definitions_listing(self.version, self._table)

    def denote(self, identity):
        """One definition's denotation: its positioned declaration, denoted
        objects and cited rules, descriptions, conditions and bindings. An
        authored line answers its statement, tags, control and methods.

        See `docs/Bellman-Sym/API/stage/08-definitions.md` §3."""
        return denotation_of_definition(self.version, self._table[identity])


# --- the two graphs of a level ---


@dataclasses.dataclass(frozen=True, eq=False)
class Graphs(_Handle):
    """The collection of the two initial diagrams of a `version`, whose one
    subclass is `Initial`, the class of `stage.initial`: `list()` names their
    blocks and `methods` answers the bindings within both directions. The two
    builders graphs form no such collection; they are `stage.builder.bwd` and
    `stage.builder.fwd`.

    See `docs/Bellman-Sym/API/stage/02-initial.md` §1."""

    version: object
    _record: object

    # the attribute that answers the graph of each direction
    MEMBERS = {"backward": "backward", "forward": "forward"}

    @property
    def record(self):
        raise AttributeError(
            "the stored record is read inside the package with versions.stored(stage, name); "
            f"this object answers {', '.join(self.MEMBERS.values())}, list() and methods"
        )

    @property
    def level(self):
        """The level of the graphs this collection holds, `initial`.

        See `docs/Bellman-Sym/API/stage/02-initial.md` §1."""
        return "initial"

    def _addresses(self):
        return (id(self._record),)

    def __repr__(self):
        members = ", ".join(self.MEMBERS.values())
        return f"{type(self._record).__name__}({self.version.name!r}, {members})"

    def list(self):
        """The names of the blocks in the two directions, each with its kind
        and direction.

        See `docs/Bellman-Sym/API/stage/02-initial.md` §1."""
        return level_listing(self._record)

    @property
    def methods(self):
        """The read-only methods mapping for pieces within both directions,
        empty before methodization.

        See `docs/Bellman-Sym/API/stage/07-methods.md` §3."""
        bound = set()
        for direction in self._record.MEMBERS:
            bound |= set(GraphHandle(self.version, self.level, direction).methods)
        return BoundMethods(self.version, methods_bound_within(self.version, bound))


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Initial(Graphs):
    """The two initial diagrams of a `version`, `stage.initial`: `backward`
    and `forward` answer the diagrams, and a block is read by its block id as
    a key of the diagram that holds it, `stage.initial.backward["policy"]`.

    See `docs/Bellman-Sym/API/stage/02-initial.md` §1."""

    @property
    def backward(self):
        """The backward initial diagram.

        See `docs/Bellman-Sym/API/stage/02-initial.md` §2."""
        return GraphHandle(self.version, "initial", "backward")

    @property
    def forward(self):
        """The forward initial diagram.

        See `docs/Bellman-Sym/API/stage/02-initial.md` §2."""
        return GraphHandle(self.version, "initial", "forward")


# --- a graph and the pieces inside it ---


@dataclasses.dataclass(frozen=True, eq=False)
class GraphHandle(_Handle):
    """One graph of a `version`, identified by `level`, `direction` and
    `grain`. `graph` answers its DisCoPy hypergraph. The builder grain keeps
    builders closed; `sub_builders` shows the authored decomposition and
    `primitives` opens it. A box of the graph is read by its whole name as a
    key.

    See `docs/Bellman-Sym/API/stage/03-build.md` §3."""

    version: object
    level: str
    direction: str
    grain: str = "builder"

    def _addresses(self):
        return (self.level, self.direction, self.grain)

    def __repr__(self):
        """The short form: the project's word for the graph, read from its
        level, with the stage and the direction, and the grain where it is not
        the builder grain (AMD-SG-021 §4.6), named by the attribute that
        reaches it, `BuildersGraph('cons', 'backward', sub_builders)`."""
        word = "BuildersGraph" if self.level == "builders" else "InitialDiagram"
        return f"{word}({self.version.name!r}, {self.direction!r}{_grain_named(self.grain)})"

    def __str__(self):
        return str(self.denote())

    @property
    def graph(self):
        """The DisCoPy hypergraph at this level, direction and grain.
        A refused graph raises `NotConstructed`.

        See `docs/Bellman-Sym/API/stage/03-build.md` §5."""
        return graph_of(self.version, self.level, self.direction, self.grain)

    def list(self):
        """The graph's pieces in order of application, each under its whole
        name, with the kind column, what it produces and its number: a builder
        its position among the builders, a primitive its position among the
        primitives of its own builder.

        See `docs/Bellman-Sym/API/stage/03-build.md` §3."""
        return graph_listing(self.graph)

    @property
    def primitives(self):
        """The same graph with all sub-builders opened and compatible primitive
        operations merged.

        See `docs/Bellman-Sym/API/stage/03-build.md` §4."""
        return GraphHandle(
            version=self.version, level=self.level, direction=self.direction, grain="primitive"
        )

    @property
    def sub_builders(self):
        """The same graph at the authored decomposition, with each `!node`
        retained as a sub-builder.

        See `docs/Bellman-Sym/API/stage/03-build.md` §4."""
        return GraphHandle(
            version=self.version, level=self.level, direction=self.direction, grain="node"
        )

    def diagram(self):
        """The drawing of this graph, separately for each direction.

        See `docs/Bellman-Sym/API/stage/03-build.md` §3."""
        return _drawing(
            self.version,
            self.graph,
            drawing_title(self.version.name, self.level, self.direction, self.grain),
        )

    def signature(self):
        """The typed inputs and outputs of this graph.

        See `docs/Bellman-Sym/API/stage/03-build.md` §3."""
        return graph_signature(
            self.version, level=self.level, direction=self.direction, grain=self.grain
        )

    def denote(self):
        """The graph's mathematical record. A builders graph answers its typed
        wires and composed builders; an initial diagram answers its authored
        relation and blocks. A refused graph answers its refusal card.

        See `docs/Bellman-Sym/API/stage/03-build.md` §3."""
        return denotation_of_graph(
            self.version, level=self.level, direction=self.direction, grain=self.grain
        )

    def obligations(self):
        """Conditions owned by this graph's builders together with those of the
        whole stage, retaining their statuses and evidence.

        See `docs/Bellman-Sym/API/stage/03-build.md` §3."""
        return obligations(self.version, self.level, self.direction)

    @property
    def methods(self):
        """The bindings at pieces within this graph and the authored lines they
        represent, as a read-only mapping.

        See `docs/Bellman-Sym/API/stage/07-methods.md` §3."""
        return BoundMethods(
            self.version,
            methods_within(self.version, [box for box in self.graph.boxes if not is_wiring(box)]),
        )

    def __getitem__(self, key):
        """One box of this graph by its whole name,
        `stage.builder.bwd.primitives["cntn_to_dcsn:Aggregation"]`. At a
        grain that opens the bubbles this is the only route to a box the grain
        merges, which no builder then contains."""
        boxes = [box for box in self.graph.boxes if not is_wiring(box)]
        if isinstance(key, tuple):
            if not key:
                raise KeyError("a key is a name or a tuple of names, one per level")
            return _walk(
                _handle_named(self.version, None, key[0], boxes, "this graph"), key[1:], key[0]
            )
        return _handle_named(self.version, None, key, boxes, "this graph")


# the key of `stage.builder` that reads the policy builder
POLICY = "policy"

# the perch each edge leads to, read forward
NEXT_PERCH = {ARRIVAL: DECISION, DECISION: CONTINUATION}


def _no_perch(word):
    """The refusal text for a word that names none of the three perches."""
    return f"{word!r} is no perch; the perches are {', '.join(PERCH_WORD)}"


def _perch_pair(key):
    """The `(source, target)` a key of `stage.builder` names, each a perch
    word; `"policy"` is accepted as the policy builder's own key."""
    if isinstance(key, str) and key == POLICY:
        return POLICY
    if not (isinstance(key, tuple) and len(key) == 2):
        raise KeyError(
            'a key of stage.builder is a pair of perches, `stage.builder["cntn", "dcsn"]`, '
            f'or "policy"; {key!r} is neither'
        )
    for word in key:
        if not isinstance(word, str) or word not in PERCH_WORD:
            raise KeyError(_no_perch(word))
    return key


def _direction_of(pair):
    """The direction whose builders join `pair`: `forward` for a pair of
    `FORWARD_PAIRS`, `backward` for a pair of `BACKWARD_PAIRS`, and None for
    any other pair."""
    if pair in FORWARD_PAIRS:
        return "forward"
    return "backward" if pair in BACKWARD_PAIRS else None


def _direction_word(stage, box):
    """`bwd` or `fwd`: the word of the direction the wire table gives the
    block that `box` denotes, which is the direction of the builders graph
    holding `box`."""
    return DIRECTION_WORDS[wire_table(stage).direction[box.name]]


def _two_or_more(stage, boxes, what):
    """The refusal of a key that two or more builders answer, `boxes`, each
    named with the key that reads it by its block id; `what` says what the
    builders share."""
    count = "two" if len(boxes) == 2 else len(boxes)
    ids = " and ".join(
        f"stage.builder.{_direction_word(stage, box)}[{box.name!r}]" for box in boxes
    )
    return KeyError(
        f"stage {stage.name!r}: {count} builders {what}, "
        f"{' and '.join(box.name for box in boxes)}; read each by its block id, {ids}"
    )


@dataclasses.dataclass(frozen=True, eq=False)
class BuilderPairs(_Handle, Mapping):
    """The builders of a `version` by the ordered pair of perches each joins,
    `stage.builder`: `stage.builder["cntn", "dcsn"]` is the backward builder
    from continuation to decision, `stage.builder["arvl", "dcsn"]` the
    forward builder from arrival to decision, and `stage.builder.policy` the
    policy builder, which the key `"policy"` also reads. `bwd` and `fwd`
    answer the two builders graphs. A pair no builder joins, or two or more
    builders join, is refused with the reason, and a pair of a direction the
    construction refused raises that refusal. Iteration gives the keys the
    mapping answers, and `list()` names every builder.

    See `docs/Bellman-Sym/API/stage/03-build.md` §1."""

    version: object

    def _addresses(self):
        return ("builder",)

    def __repr__(self):
        # the builders `list()` names, which exceed the keys where two or
        # more builders join one pair or write the controls
        return f"Builders({self.version.name!r}, {len(self.list())} by their perches)"

    def _table(self):
        return builder_pairs(self.version)

    def __getitem__(self, key):
        """The builder that joins the ordered pair of perches
        `(source, target)`. The key `"policy"` answers the policy builder.

        See `docs/Bellman-Sym/API/stage/03-build.md` §1."""
        pair = _perch_pair(key)
        pairs, policies, refused = self._table()
        if pair == POLICY:
            return self._policy(policies, refused)
        boxes = pairs.get(pair, [])
        if len(boxes) == 1:
            return BubbleHandle(self.version, boxes[0])
        if boxes:
            raise _two_or_more(self.version, boxes, f"join {arrow(pair)}")
        direction = _direction_of(pair)
        if direction in refused:
            raise refused[direction]
        listed = [arrow(p) for p in self._ordered(pairs)] + ([POLICY] if policies else [])
        raise KeyError(
            f"stage {self.version.name!r}: no builder joins {arrow(pair)}; the builders are "
            f"{', '.join(listed) or 'none'}"
        )

    def _policy(self, policies, refused):
        """The policy builder, the one backward builder that writes the
        controls; the refusal of the backward builders graph where the
        construction refused it; and a refusal where no builder, or two or
        more builders, write the controls."""
        if "backward" in refused:
            raise refused["backward"]
        if len(policies) == 1:
            return BubbleHandle(self.version, policies[0])
        if policies:
            raise _two_or_more(self.version, policies, "write the controls")
        raise KeyError(
            f"stage {self.version.name!r}: no backward builder writes the controls, "
            "so there is no policy builder"
        )

    @staticmethod
    def _ordered(pairs):
        """The pairs of `pairs` in the order the listing prints them: the
        forward pairs, the backward pairs, then any other pair."""
        usual = FORWARD_PAIRS + BACKWARD_PAIRS
        return [p for p in usual if p in pairs] + sorted(
            (p for p in pairs if p not in usual), key=str
        )

    def _keys(self):
        """The keys `__getitem__` answers, in the order of the listing: each
        pair of two perches that exactly one builder joins, then `policy`
        where exactly one backward builder writes the controls."""
        pairs, policies, _ = self._table()
        keys = [
            pair
            for pair in self._ordered(pairs)
            if len(pairs[pair]) == 1 and all(side in PERCH_WORD for side in pair)
        ]
        return keys + ([POLICY] if len(policies) == 1 else [])

    def __iter__(self):
        return iter(self._keys())

    def __len__(self):
        return len(self._keys())

    @property
    def policy(self):
        """The policy builder: the backward builder that writes the controls.

        See `docs/Bellman-Sym/API/stage/03-build.md` §2."""
        try:
            return self[POLICY]
        except KeyError as absent:
            # `hasattr` catches only AttributeError, so a stage with no policy
            # builder, or two or more, would otherwise raise from inside
            # `hasattr`
            raise AttributeError(absent.args[0]) from absent

    @property
    def bwd(self):
        """The backward builders graph, on value functions.

        See `docs/Bellman-Sym/API/stage/03-build.md` §3."""
        return GraphHandle(self.version, "builders", "backward")

    @property
    def fwd(self):
        """The forward builders graph, on measures.

        See `docs/Bellman-Sym/API/stage/03-build.md` §3."""
        return GraphHandle(self.version, "builders", "forward")

    def list(self):
        """One line per builder, forward pairs first, whose key is the block
        identifier, by which the builder is read from its graph,
        `stage.builder.bwd[identifier]` or `stage.builder.fwd[identifier]`,
        and whose value is the pair, printed `source → target`, by which it
        is read from the mapping, `stage.builder[pair]`, or for the policy
        builder its key, `policy`, with the direction word. The record is a
        `NamedListing`, the section `builder` of `stage.list()`, and prints
        as `cntn_to_dcsn   cntn → dcsn, bwd`.

        See `docs/Bellman-Sym/API/stage/03-build.md` §1."""
        pairs, policies, _ = self._table()
        # a block identifier names one block of the stage, which the
        # construction checks, so no builder shares its key with another
        entries = {
            box.name: (arrow(pair), _direction_word(self.version, box))
            for pair in self._ordered(pairs)
            for box in pairs[pair]
        }
        entries.update({box.name: (POLICY, DIRECTION_WORDS["backward"]) for box in policies})
        return NamedListing(entries)

    def view(self):
        """The listing printed, one line per builder.

        See `docs/Bellman-Sym/API/stage/03-build.md` §1."""
        return str(self.list())

    @property
    def methods(self):
        """The read-only methods mapping for the pieces within both builders
        graphs, empty before methodization; a graph the construction refused
        holds none.

        See `docs/Bellman-Sym/API/stage/07-methods.md` §3."""
        boxes = []
        for direction in DIRECTIONS:
            try:
                graph = graph_of(self.version, "builders", direction)
            except NotConstructed:
                continue
            boxes += [box for box in graph.boxes if not is_wiring(box)]
        return BoundMethods(self.version, methods_within(self.version, boxes))


@dataclasses.dataclass(frozen=True, eq=False)
class PerchBuilders(_Handle):
    """The builders of the edge that leaves one perch of a `version`,
    `stage.dcsn.builder`: `fwd` is the forward builder of that edge, `bwd`
    its backward builder, and at the decision perch `policy` is the policy
    builder. `fwd` and `bwd` are each defined as one pair of
    `stage.builder`, and `policy` as its key `"policy"`, so the two forms
    never disagree: `stage.dcsn.builder.bwd` is
    `stage.builder["cntn", "dcsn"]`. No edge of the stage leaves the
    continuation perch, so `stage.cntn.builder` refuses both directions with
    the reason.

    See `docs/Bellman-Sym/API/stage/03-build.md` §2."""

    version: object
    perch: str

    def _addresses(self):
        return ("builder", self.perch)

    def __repr__(self):
        return f"PerchBuilders({self.version.name!r}, {self.perch!r})"

    def _pair(self, word):
        """The pair of `stage.builder` that the path `word`, `fwd` or `bwd`,
        reads at this perch; at continuation, the refusal with the reason, and
        at a word that names no perch, the refusal naming the three."""
        if self.perch == CONTINUATION:
            if word == "fwd":
                raise AttributeError(
                    f"stage {self.version.name!r}: the forward pass leaves the stage at "
                    "continuation, so `stage.cntn.builder.fwd` names no builder; the connector "
                    "identifies the measure at continuation with the next stage's arrival measure"
                )
            raise AttributeError(
                f"stage {self.version.name!r}: no value is built at continuation, so "
                "`stage.cntn.builder.bwd` names no builder; the connector identifies the "
                "continuation value with the next stage's arrival value"
            )
        if self.perch not in NEXT_PERCH:
            raise AttributeError(_no_perch(self.perch))
        following = NEXT_PERCH[self.perch]
        return (self.perch, following) if word == "fwd" else (following, self.perch)

    def _reach(self, word):
        """The builder that the path `word` names, `stage.builder[pair]`; a
        key the mapping refuses is refused as an attribute, and a direction
        the construction refused raises its refusal."""
        pair = self._pair(word)
        try:
            return self.version.builder[pair]
        except KeyError as absent:
            # only a pair that no builder joins has the terminal reason
            joined = pair in builder_pairs(self.version)[0]
            if word == "fwd" and self.perch == DECISION and not joined:
                raise AttributeError(
                    f"stage {self.version.name!r}: no builder joins dcsn → cntn; like a terminal "
                    "stage, the stage writes no forward block from decision to continuation, "
                    "so `stage.dcsn.builder.fwd` names no builder"
                ) from absent
            raise AttributeError(absent.args[0]) from absent

    @property
    def fwd(self):
        """The forward builder of the edge that leaves this perch, which maps
        the measure at this perch to the measure at the next perch.

        See `docs/Bellman-Sym/API/stage/03-build.md` §2."""
        return self._reach("fwd")

    @property
    def bwd(self):
        """The backward builder of the edge that leaves this perch, which
        constructs the value functions at this perch from those at the next
        perch.

        See `docs/Bellman-Sym/API/stage/03-build.md` §2."""
        return self._reach("bwd")

    @property
    def policy(self):
        """The policy builder, at the decision perch alone:
        `stage.builder.policy`.

        See `docs/Bellman-Sym/API/stage/03-build.md` §2."""
        if self.perch not in PERCH_WORD:
            raise AttributeError(_no_perch(self.perch))
        if self.perch != DECISION:
            raise AttributeError(
                f"stage {self.version.name!r}: the policy builder stands at the decision perch, "
                f"`stage.dcsn.builder.policy`, not at {PERCH_WORD[self.perch]}"
            )
        return self.version.builder.policy

    def list(self):
        """The paths of this perch, each with the key of `stage.builder` it
        reads: two at arrival, three at decision with `policy`, and none at
        continuation. The record is a `NamedListing` keyed by the
        path, `stage.dcsn.builder.bwd`, whose value is the pair as
        `source → target` or the key `policy`. A path is listed whether or
        not the stage has the builder it names.

        See `docs/Bellman-Sym/API/stage/03-build.md` §2."""
        entries = {}
        if self.perch in NEXT_PERCH:
            for word in ("fwd", "bwd"):
                entries[f"stage.{self.perch}.builder.{word}"] = arrow(self._pair(word))
        if self.perch == DECISION:
            entries[f"stage.{self.perch}.builder.policy"] = POLICY
        return NamedListing(entries)


@dataclasses.dataclass(frozen=True, eq=False)
class PerchHandle(_Handle):
    """One perch of a `version`, `stage.arvl`, `stage.dcsn` or `stage.cntn`:
    an information set, from which `builder` reaches the builders of the edge
    that leaves it, `fwd` and `bwd` at arrival and at decision with `policy`
    beside them at decision, and none at continuation, which no edge of the
    stage leaves.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""

    version: object
    perch: str

    def _addresses(self):
        return ("perch", self.perch)

    def __repr__(self):
        return f"Perch({self.version.name!r}, {self.perch!r})"

    @property
    def builder(self):
        """The builders of the edge that leaves this perch, `fwd` and `bwd`,
        and at decision `policy`.

        See `docs/Bellman-Sym/API/stage/03-build.md` §2."""
        return PerchBuilders(self.version, self.perch)


# the attribute of a graph, a builder or a block that opens it at each finer
# grain, by which a short form names the grain
_GRAIN_ATTRIBUTES = {"primitive": "primitives", "node": "sub_builders"}


def _grain_named(grain):
    """`, primitives` or `, sub_builders` for a piece at a finer grain, named
    by the attribute that reaches it; nothing at the builder grain. A grain no
    attribute reaches, which the snapshot recorder alone asks for, is named by
    its token."""
    if grain == "builder":
        return ""
    return f", {_GRAIN_ATTRIBUTES.get(grain, repr(grain))}"


def drawing_arguments(stage, graph) -> dict:
    """The two arguments that the drawing of one graph of `stage` is given
    beside the graph, by the names of `to_drawing`'s parameters: the name the
    stage gives each wire (`wire_names`, `drawn_wire_names`) and the law or
    the aggregator each box applies where the box does not name it (`laws`,
    `drawn_laws`). The drawing of a piece and the interactive view
    (`factory/model_explorer.py`) read the same two."""
    return {"wire_names": drawn_wire_names(stage, graph), "laws": drawn_laws(stage, graph)}


def _drawing(stage, graph, title=None):
    """The `Drawing` of one graph of `stage` (AMD-SG-007 §7), which a graph's
    or a bubble's `diagram()` answers: its wires and its pullbacks named as
    the stage names them, and the title a graph's level, direction and grain
    give it; the interior of one bubble names no graph and carries no title."""
    return to_drawing(graph, title=title, **drawing_arguments(stage, graph))


def _handle_named(stage, holder, key, choices, where):
    """The one box among `choices` that `key` names, as a handle. `where`
    names the object searched, for the refusal."""
    if not isinstance(key, str):
        # a `for` loop over a handle asks for the key 0, which names no box;
        # the names are what `list()` returns
        raise TypeError(
            f"a key of {where} is a box name, not {type(key).__name__}; "
            f"`list()` gives the names and each of them is a key"
        )
    chosen = [box for box in choices if _matches(box, holder, key)]
    if len(chosen) != 1:
        # a block's authored line that reads no wire is in no graph and is
        # reached by its name from the block, as every other line is
        # (AMD-SG-021 §4.5)
        wireless = {} if holder is None else lines_with_no_wire(stage, holder)
        if len(chosen) == 0 and key in wireless:
            return LineHandle(stage, wireless[key])
        names = ", ".join(
            [box.name for box in choices]
            + [definition.address for definition in wireless.values()]
        )
        raise KeyError(
            f"stage {stage.name!r}: {key!r} names {len(chosen)} pieces of {where}; "
            f"they are {names or 'none'}"
        )
    box = chosen[0]
    return BubbleHandle(stage, box) if isinstance(box, Bubble) else BoxHandle(stage, box)


def _matches(box, holder, key):
    """Whether `key` names `box`. Inside a bubble the key may be the part of
    the name after the holder's segment, its kind compared without regard to
    case (`"pullback"` names `cntn_to_dcsn:Pullback`); at a graph, where
    the boxes of several builders stand together, the key is the whole name
    (AMD-SG-010 §4)."""
    if box.name == key:
        return True
    if holder is None or not isinstance(key, str):
        return False
    held = getattr(box, "identity", None)
    inner = None if held is None else held.key_within(holder.name)
    return inner is not None and inner.lower() == key.lower()


def _walk(found, key, holder):
    """A tuple of keys walks one level down per element after the first."""
    for step in key:
        if not isinstance(found, BubbleHandle):
            raise KeyError(f"{holder!r}: {step!r} has no bubble to look inside")
        found = found[step]
    return found


@dataclasses.dataclass(frozen=True, eq=False)
class BubbleHandle(_Handle):
    """A builder, block, sub-builder or node group with an interior.
    `version` is its stage version; `box` is the DisCoPy bubble. Its name
    is the authored block or node name.

    See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""

    version: object
    box: object

    def _addresses(self):
        return (id(self.box),)

    def __repr__(self):
        """The short form: the project's word for the piece, read from the
        class of the box and the kind of its identity (AMD-SG-021 §4.6), and,
        for a piece opened at a finer grain, the grain it was opened at, named
        by the attribute that reaches it, `Builder('cons', 'cntn_to_dcsn',
        primitives)`."""
        place = derived_graph_at_grain(self.version, self.box)
        grain = _grain_named(place.grain) if place is not None else ""
        return f"{piece_word(self.box)}({self.version.name!r}, {self.box.name!r}{grain})"

    def __str__(self):
        return str(self.denote())

    def list(self):
        """The tree of the interior's pieces in order of application, each
        under the key that reaches it from this handle, with the kind column
        and what it produces: a builder's or a sub-builder's
        primitives numbered as the `operations` block of its card numbers
        them, a sub-builder's row unnumbered with its primitives under it;
        `primitives.list()` opens the sub-builders and lists the primitives
        alone with the same numbers; a block's lines, the `!doc` line among
        them, unnumbered.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""
        return bubble_listing(self._lines_read_on(), self.box)

    def denote(self):
        """This piece's mathematical record, with typed wires and contained
        pieces. An authored block also retains its positioned statements,
        header, control and bindings.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""
        return (
            denotation_of_block(self.version, self.box)
            if is_block(self.box)
            else denotation_of_builder(self.version, self.box)
        )

    @property
    def primitives(self):
        """This piece with every sub-builder opened and compatible primitive
        operations merged.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §4."""
        return BubbleHandle(self.version, self._grain("primitive"))

    @property
    def sub_builders(self):
        """This piece at its authored sub-builder decomposition.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §4."""
        return BubbleHandle(self.version, self._grain("node"))

    def _grain(self, grain):
        return bubble_at(self.version, self.box, grain)

    def diagram(self):
        """The drawing of this piece's interior.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""
        return _drawing(self.version, BellmanHypergraph.from_diagram(self.box.arg))

    def signature(self):
        """The typed inputs and outputs of this piece.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §1."""
        return box_signature(self.version, self.box)

    def kernels(self):
        """The kernels of this builder as one `BuilderKernels` record, from
        which a numerical operator is constructed with no stage in hand: for
        each primitive operator in order of application, the function its
        `compile_kernel()` answers with the names of its arguments and its
        outputs, the parameters it reads with the values the calibration
        binds, the wires it reads and writes and its printed kernel, and for
        a row with no explicit function its printed relation in place of a
        function; then the builder's parameters with their values and the
        sets its pieces are read on. A block of an initial diagram applies no
        kernel and is refused; its builder answers.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §5."""
        return builder_kernels(self.version, self)

    def state_choice_measure(self):
        """The joint measure of state and choice for a forward
        decision builder.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §3.
        """
        return state_choice_measure(self.version, self.box)

    def obligations(self):
        """The stage's authored conditions and type checks concerning
        this piece.

        See `docs/Bellman-Sym/API/stage/04-builder.md` §1.
        """
        return box_obligations(self.version, self.box)

    @property
    def methods(self):
        """Bindings at this piece, inside it, and at the authored lines of the
        block it is built from.

        See `docs/Bellman-Sym/API/stage/07-methods.md` §3."""
        return BoundMethods(self.version, methods_within(self.version, self.box))

    def __getitem__(self, key):
        """One box inside it by name, the kind compared without regard to
        case; a tuple of keys walks one level down per element."""
        inside, version = boxes_inside(self.box), self._lines_read_on()
        if isinstance(key, tuple):
            if not key:
                raise KeyError("a key is a name or a tuple of names, one per level")
            return _walk(
                _handle_named(version, self.box, key[0], inside, repr(self.box.name)),
                key[1:],
                key[0],
            )
        return _handle_named(version, self.box, key, inside, repr(self.box.name))

    def _lines_read_on(self):
        """The version this piece's lines are read on: for a block of an
        initial diagram the stage as declared (`method_blocks.
        declared_version`), so that a block file's lines stand in no block of
        the stage file and no binding changes a line's card (decision
        SC-22); the version itself otherwise."""
        return declared_version(self.version) if is_block(self.box) else self.version


@dataclasses.dataclass(frozen=True, eq=False)
class BoxHandle(_Handle):
    """A primitive operator or authored line with no interior.
    `version` is its stage version and `box` the retained DisCoPy box.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    version: object
    box: object

    def _addresses(self):
        return (id(self.box),)

    def __repr__(self):
        """The short form: the project's word for the piece, read from the
        class of the box and the kind of its identity (AMD-SG-021 §4.6)."""
        return f"{piece_word(self.box)}({self.version.name!r}, {self.box.name!r})"

    def __str__(self):
        return str(self.denote())

    def list(self):
        """The pieces below this box: none, since a primitive operator or an
        authored line has no interior, so the listing prints `none`; the same
        verb at every level.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""
        return Listing(())

    def denote(self):
        """This box's mathematical record and card: an operator's mapping,
        typed wires, kernel and conditions, or an authored line's positioned
        statement, tags, control and methods.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""
        return denotation_of(self.version, self.box)

    def kernel(self, *, across_expectation=False):
        """The kernel applied by this operator, with its defining records in
        `origins`. `across_expectation` requests the supported extension across
        an expectation.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §2."""
        return kernel(self.version, self.box, across_expectation=across_expectation)

    def compile_kernel(self):
        """The kernel as one plain Python function, the text `kernel().python`
        executed, on a symbolic or a calibrated version: its arguments are the
        kernel's own and then the parameters it reads, whose values
        `kernel().parameter_values` holds.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §2."""
        return compile_kernel(self.version, self.box)

    def signature(self):
        """The typed inputs and outputs of this box.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""
        return box_signature(self.version, self.box)

    def obligations(self):
        """The conditions this box owns. A box merged across authored lines
        retains the conditions of its member occurrences.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §3."""
        return box_obligations(self.version, self.box)

    @property
    def methods(self):
        """The read-only bindings at this box and the authored lines it
        represents. Merged lines bind one compatible method; conflicts
        refuse methodization.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §3."""
        return BoundMethods(self.version, methods_within(self.version, self.box))


@dataclasses.dataclass(frozen=True, eq=False)
class LineHandle(_Handle):
    """An authored line that reads no wire, reached by name from its block.
    `version` is its stage version and `definition` its retained line record.
    A `!doc` line has no graph box but retains its statement and annotation.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §4."""

    version: object
    definition: object

    def _addresses(self):
        return (self.definition.identity,)

    def __repr__(self):
        return f"Line({self.version.name!r}, {self.definition.address!r})"

    def __str__(self):
        return str(self.denote())

    def denote(self):
        """The authored relation, positioned statement and annotations of this
        line, as the same record a line with a box answers.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §4."""
        return denotation_of_definition(self.version, self.definition)

    @property
    def methods(self):
        """The read-only methods mapping at this line. It is empty before
        methodization and for a `!doc` line, which no method solves.

        See `docs/Bellman-Sym/API/stage/05-piece.md` §4."""
        return BoundMethods(self.version, methods_of_line(self.version, self.definition))


# --- the kernels of a builder ---


def builder_kernels(stage, builder):
    """The `BuilderKernels` record of one builder or sub-builder handle of
    `stage`, which its `kernels()` answers. The pieces are the primitive
    operators its `list()` numbers, in that order, each read through its own
    handle with `kernel()` and `compile_kernel()`. A piece that
    `compile_kernel()` refuses under `kernel-target` has no explicit function
    and holds its printed kernel alone, and a row among them that states a
    relation holds that text as its relation; every other refusal is raised.
    The parameters of the record are those its pieces read, in the order the
    stage declares them (`parameters_of`), with the values the pieces are
    called with. Nothing is stored on the stage, and the record refers to no
    object of the stage."""
    if is_block(builder.box):
        raise TypeError(
            f"stage {stage.name!r}: {builder.box.name!r} is a block of an initial diagram, "
            "which applies no kernel; the builder of the same name in stage.builder.bwd or "
            "stage.builder.fwd answers kernels()"
        )
    pieces, arguments = [], []
    for entry in builder.list().entries:
        if entry.kind != "primitive":
            continue
        piece, declared = _piece_kernel(stage, entry.key, builder[entry.key], builder.box.name)
        pieces.append(piece)
        arguments.extend(declared)
    for name in derivative_pieces(stage, builder.box.name):
        piece, declared = _derivative_piece_kernel(stage, name)
        pieces.append(piece)
        arguments.extend(declared)
    bound, unbound = {}, set()
    for piece in pieces:
        if piece.parameter_values is None:
            unbound.update(piece.parameters)
        else:
            bound.update(zip(piece.parameters, piece.parameter_values))
    read = {name for piece in pieces for name in piece.parameters}
    names = tuple(name for name in parameters_of(stage) if name in read)
    return BuilderKernels(
        builder=builder.box.name,
        inputs=tuple(wire_name(stage, sort) for sort in builder.box.dom.inside),
        outputs=tuple(wire_name(stage, sort) for sort in builder.box.cod.inside),
        pieces=tuple(pieces),
        parameters=names,
        parameter_values=None if unbound else tuple(bound[name] for name in names),
        sets=_declared_sets(stage, arguments),
    )


def _piece_kernel(stage, key, piece, holder):
    """The `PieceKernel` of one primitive operator handle, reached by `key`
    from its builder, whose box is named `holder`, and the pairs of argument
    name and declared set term of its kernel. Its name relative to the
    builder is the one `piece_named` answers, which the identity of its box
    writes. `compile_kernel()` is asked once; its refusal under
    `kernel-target` leaves the piece with no function."""
    record = piece.kernel()
    try:
        function = piece.compile_kernel()
    except ConstructionError as refusal:
        if refusal.rule != "kernel-target":
            raise
        function = None
    box, values = piece.box, record.parameter_values
    made = PieceKernel(
        key=key,
        relative_name=piece_named(box, holder),
        name=box.name,
        kind=kind_of(box),
        function=function,
        arguments=tuple(name for name, _ in record.arguments),
        outputs=tuple(record.outputs),
        parameters=tuple(record.parameters),
        parameter_values=None if values is None else tuple(values),
        reads=tuple(wire_name(stage, sort) for sort in box.dom.inside),
        writes=tuple(wire_name(stage, sort) for sort in box.cod.inside),
        kernel=str(record),
        relation=str(record) if function is None and is_relation(row_of(stage, box)) else None,
        python=None if function is None else record.python,
    )
    return made, record.arguments


def _derivative_piece_kernel(stage, name):
    """The `PieceKernel` of one derivative piece of a builder, `<line
    id>:Derivative:1`, the stated derivative of a value builder compiled
    from the author's right side (AMD-MB-001 §4.3; decision MB-A14), and the
    pairs of argument name and declared set of its kernel. Its function is
    None where the right side holds a form the text cannot write."""
    record = kernel(stage, name)
    function = None if record.python is None else compile_kernel(stage, name)
    made = PieceKernel(
        key=name,
        relative_name=name,
        name=name,
        kind="Derivative",
        function=function,
        arguments=tuple(argument for argument, _ in record.arguments),
        outputs=tuple(record.outputs),
        parameters=tuple(record.parameters),
        parameter_values=record.parameter_values,
        reads=tuple(argument for argument, _ in record.arguments),
        writes=tuple(record.outputs),
        kernel=str(record),
        relation=None,
        python=record.python,
        integrated=record.integrated,
    )
    return made, record.arguments


def _declared_sets(stage, arguments):
    """The declared sets the pieces of a builder are read on, as pairs of a
    name and the set's source text: each argument of a piece's function with
    the set the stage declares for it, once and in order of first appearance,
    an argument with no declared set left out; then each named set those
    sets name, followed through the definitions it names in turn, with its
    definition."""
    definitions = {
        record.identity.field: record.equations[0]
        for record in stage.definitions.values()
        if record.kind == "set" and record.equations
    }
    pairs, named, seen = [], [], set()
    for name, declared in arguments:
        if declared is None or name in seen:
            continue
        seen.add(name)
        pairs.append((name, to_source(declared)))
        named.append(declared)
    listed = {}
    while named:
        for node in term_nodes(named.pop(0)):
            if isinstance(node, T.Named) and node.name in definitions and node.name not in listed:
                listed[node.name] = to_source(definitions[node.name])
                named.append(definitions[node.name])
    return tuple(pairs) + tuple(listed.items())


# --- the methods, the parameters and the settings ---


class BoundMethods(Methods):
    """The methods bound within one piece of a version, the `Methods` record
    every level's `methods` answers, printed one line to an entry. A method is
    read by the target it is bound at, `methods["cntn_to_dcsn:Evaluation"]`,
    or by the target as a methods file writes it, `methods["policy"]` or
    `methods["cntn_to_dcsn.value"]`: the one method bound within the place
    that target names (`method_bound_at`). Every entry is read from the
    version's `bindings.methods` and none is copied.

    See `docs/Bellman-Sym/API/stage/07-methods.md` §2."""

    def __init__(self, version, entries):
        super().__init__(entries)
        self._version = version

    def __getitem__(self, target):
        return method_bound_at(self._version, self._entries, target)


def method_bound_at(stage, bound, target):
    """The method record `bound`, the bindings within one piece of `stage`,
    holds for `target`: the entry bound under that target; for the target as
    a methods file writes it, the one method bound within the place the
    target names, read through the resolution the methods file's own targets
    go through (`resolve_target`, `attachment_places`); and for the whole name
    of a box of the stage's graphs, the one method bound within that box
    (`piece_and_place`). A target that names no bound method, or names several
    different ones, is refused with the reason as a `KeyError`, which a
    membership test reads as absence."""
    if target in bound:
        # a box's identity equals its spelling, so this reads either
        return bound[target]
    held = (
        "the methods here are bound at "
        + ", ".join(
            f"{key} ({f'!{method.tag}' if method.tag else 'handler only'})"
            for key, method in bound.items()
        )
        if bound
        else "no method is bound here"
    )
    if not isinstance(target, str):
        raise KeyError(
            f"stage {stage.name!r}: a method is read by the target it is bound at or by the "
            f"target as a methods file writes it, not by {type(target).__name__}; {held}"
        )
    try:
        within = _bound_within_target(stage, target)
    except (TargetError, IdentityCollision) as refusal:
        raise KeyError(
            f"stage {stage.name!r}: {target!r} is no target a methods file writes and no box "
            f"of the stage's graphs ({refusal}); {held}"
        ) from refusal
    within = set(within)
    found = {key: method for key, method in bound.items() if bound_at(key) in within}
    methods = list(dict.fromkeys(found.values()))
    if len(methods) == 1:
        return methods[0]
    if methods:
        raise KeyError(
            f"stage {stage.name!r}: {target!r} names a place within which "
            f"{len(methods)} different methods are bound, at "
            f"{', '.join(str(key) for key in found)}; read one by the target it is bound at"
        )
    raise KeyError(f"stage {stage.name!r}: no method is bound within {target!r}; {held}")


def _bound_within_target(stage, target):
    """The targets a method bound within the place `target` names stands
    under: the places a methods file's target resolves to, or, for a name no
    methods file writes, the box of the stage's graphs of that whole name. A
    name that is neither is refused by the second resolution."""
    try:
        places = attachment_places(
            stage, target, resolve_target(stage, target), False, representation=True
        )
    except (TargetError, IdentityCollision):
        piece, _ = piece_and_place(stage, target)
        return tuple(methods_within(stage, piece)) if not isinstance(piece, Definition) else ()
    return tuple(key for place in places for key in _bound_within_place(stage, place))


def _bound_within_place(stage, place):
    """The targets a method bound at one place of a methods file stands under:
    those within the builder a block id or a `!node` line names; the closing
    Evaluation of the builder whose boundary representation the target names,
    the one target `methodize` binds that representation's method at
    (`method_table._representation_place`); those of the line a line address
    names; and the target itself for an operator occurrence or a definition."""
    if place.kind == "boundary":
        return (Identity("Evaluation", address=place.block),)
    if place.kind in ("builder", "node"):
        builder = _stored_builder(stage, place.block)
        if builder is None:
            return ()
        if place.kind == "node":
            builder = next(
                (box for box in builder.arg.boxes if box.name == place.address), builder
            )
        return tuple(methods_within(stage, builder))
    if place.kind == "statement":
        return tuple(methods_of_line(stage, stored(stage, "definitions")[place.address]))
    return (place.box,)


def _stored_builder(stage, name):
    """The builder box of that name in the stored builders graphs, or None
    where the graph that would hold it was refused."""
    for direction in DIRECTIONS:
        graph = stored_graph(stage, "builders", direction)
        for box in () if graph is None else graph.boxes:
            if box.name == name:
                return box
    return None


def _is_protocol_name(name):
    """Whether `name` is written as Python writes the names of its own
    protocols, with two underscores before and after it, `__deepcopy__`: a
    copy, a pickle and a display ask a table for such names, and no parameter
    or setting is read by one."""
    return name.startswith("__") and name.endswith("__")


def _is_attribute_name(name):
    """Whether `name`, written after a dot in Python source, reaches
    `__getattr__` as written: a string that is an identifier, no keyword of
    Python, such as `lambda`, no name of Python's protocols, and its own
    normal form NFKC, the form in which Python reads a name of the source,
    so that `ℓ`, read as `l`, is no such name."""
    return (
        isinstance(name, str)
        and name.isidentifier()
        and not keyword.iskeyword(name)
        and not _is_protocol_name(name)
        and unicodedata.normalize("NFKC", name) == name
    )


class _NamedRecords(Mapping):
    """The reading `Parameters` and `Settings` share: a read-only mapping over
    the records `_records_of` reads from the version, by name, printed as the
    table `list()` answers."""

    def __dir__(self):
        """The table's own attributes and the name of each entry that can be
        written after a dot, an identifier that is no keyword of Python and no
        name that Python rewrites when it reads the source, so that completing
        `stage.par.` offers the parameters and `stage.settings.` the settings.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §3."""
        return sorted(
            set(object.__dir__(self))
            | set(filter(_is_attribute_name, self._records_of(self.version)))
        )

    def __iter__(self):
        return iter(self._records_of(self.version))

    def __len__(self):
        return len(self._records_of(self.version))

    def __repr__(self):
        return str(self.list())

    __str__ = __repr__


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Parameters(_NamedRecords):
    """The version's parameters, `stage.par`: a read-only mapping from each
    parameter's name, as the file declares it, to its record, in declaration
    order. `stage.par["ρ"]` prints as one line, `ρ = 6.0 : [1, inf)`, or
    `ρ : [1, inf), unbound` where no calibration binds it, and its `value` is
    the number a calibration binds, which `stage.par.ρ` answers alone. Each
    record is read from the parameter's declaration in the definitions table
    and the value in the version's bindings, and none is kept. `list()`
    answers the table the mapping prints.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §1."""

    version: object
    _records_of = staticmethod(parameters_of)

    def __getitem__(self, name):
        found = parameters_of(self.version)
        if name not in found:
            raise KeyError(
                f"stage {self.version.name!r}: {name!r} is no parameter of the stage; a "
                f"parameter is read by the name the file declares, and the parameters are "
                f"{', '.join(found) or 'none'}"
            )
        return found[name]

    def __getattr__(self, name):
        """The value alone of one parameter, read by its name as an attribute,
        `stage.par.ρ`: the `value` of the record `stage.par["ρ"]`, the number
        a calibration binds. The name is looked up as the key is, and a name
        that is no parameter is refused with the key's reason as an
        `AttributeError`, so that `hasattr` and completion read it as absent.
        A parameter that no calibration binds on this version has no value,
        and reading it so is refused, as an `AttributeError` that names the
        record's key and the verb `calibrate`; the record, which prints
        `unbound`, is read by the key. The table's own attributes, `version`,
        `list`, `view`, `keys`, `items`, `values` and `get`, answer before any
        parameter, so a parameter of one of these names is read by the key
        alone, and so is a parameter whose name cannot be written after a dot:
        a keyword of Python, such as `lambda`, or a name that Python rewrites
        when it reads the source, such as `ℓ`, which it reads as `l`.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §3."""
        if "version" not in vars(self) or _is_protocol_name(name):
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
        try:
            record = self[name]
        except KeyError as refusal:
            raise AttributeError(refusal.args[0]) from None
        if isinstance(record.value, str) and record.value == UNBOUND:
            raise AttributeError(
                f"stage {self.version.name!r}: the parameter {name!r} has no value on this "
                f'version, which no calibration has bound; stage.par["{name}"] answers its '
                f"record, and calibrate(stage, source) binds its value"
            )
        return record.value

    def list(self):
        """The parameters as a table, one row each with `name`, `domain`,
        `value` and `describes`: the declared set, printed under `set`, and the
        bound value or the word `unbound`.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §1."""
        return parameter_rows(self.version)

    def view(self):
        """The table of the parameters as printed text.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §1."""
        return str(self)


@dataclasses.dataclass(frozen=True, eq=False, repr=False)
class Settings(_NamedRecords):
    """The version's settings, `stage.settings`: a read-only mapping from each
    setting a configuration binds, by its name, to its record, in binding
    order. `stage.settings["n_a"]` prints as one line, `n_a = 800`, with the
    places and the methods that read the setting after it, and its `value` is
    the configured value, which `stage.settings.n_a` answers alone. A setting
    has no declaration in the definitions table, so each record is read from
    the configured value in `stage.bindings.settings` and the bound methods
    that name the setting, and none is kept; a version no configuration has
    bound holds no setting. `list()` answers the table the mapping prints.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §2."""

    version: object
    _records_of = staticmethod(settings_of)

    def __getitem__(self, name):
        found = settings_of(self.version)
        if name not in found:
            bound = self.version.bindings.settings is not None
            read = ", ".join(self.version.bindings.settings_readers())
            raise KeyError(
                f"stage {self.version.name!r}: {name!r} is no setting of this version"
                + (
                    f"; its settings are {', '.join(found) or 'none'}"
                    if bound
                    else ", which binds no settings; configure(stage, source) binds them"
                )
                + (f"; the bound methods read {read}" if read else "")
            )
        return found[name]

    def __getattr__(self, name):
        """The value alone of one setting, read by its name as an attribute,
        `stage.settings.n_a`: the `value` of the record
        `stage.settings["n_a"]`, the configured value. The name is looked up
        as the key is, and a name that is no setting of this version is
        refused with the key's reason as an `AttributeError`, so that
        `hasattr` and completion read it as absent. The table's own
        attributes, `version`, `list`, `view`, `keys`, `items`, `values` and
        `get`, answer before any setting, so a setting of one of these names
        is read by the key alone, and so is a setting whose name cannot be
        written after a dot: one that is no Python identifier, such as
        `n-points`, a keyword of Python, a name with two underscores before
        and after it, which Python keeps for its own protocols, or a name
        that Python rewrites when it reads the source.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §3."""
        if "version" not in vars(self) or _is_protocol_name(name):
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
        try:
            return self[name].value
        except KeyError as refusal:
            raise AttributeError(refusal.args[0]) from None

    def list(self):
        """The settings as a table, one row for each method that reads a
        setting, with `name`, `value`, `read at` and `by`; a setting no method
        reads has one row with the last two empty.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §2."""
        return setting_rows(self.version)

    def view(self):
        """The table of the settings as printed text.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §2."""
        return str(self)
