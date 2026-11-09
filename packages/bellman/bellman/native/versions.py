"""One version of a stage: the base class `StageVersion`, the answers kept for
a version and those it passes on, the accessor of its three stored records,
the making of the next version, and `WorkingStage`, the stage while it is
constructed.

A version is one `ElaboratedStage`: the stage as elaborated, which a binding
verb binds in place (specification 0.6 §4.1). `stored` reads and `store`
writes the five records held under the attributes of `STORED`; the two are
the only readers and writers of the instance dictionary the descriptor of
`pieces.py` stores in, save `StageVersion.__getstate__`, which reads it whole
for the standard pickle. `bind_in_place` writes what a binding verb binds
through `store` and discards the kept answers the binding changes.
`replace_stage` builds the next version through the constructor, as
`dataclasses.replace` builds it from the instance. `CARRIED` names the answers
a version passes on to a version made from it. A reader of a stage tells a
constructed version by the class `StageVersion` and the stage under
construction by `WorkingStage`.
"""

from __future__ import annotations

import dataclasses
from contextvars import ContextVar
from functools import cached_property

from bellman.native.hypergraphs import BellmanHypergraph

# The answers a version passes on to a version made from it, by
# `hypergraphs.copy_native` or by `replace_stage`, and keeps through a binding
# that adds no row (`StageVersion._discard`), named by the first entry of the
# key the query keeps them under. Each is determined by the definitions table
# and the stored graphs, which such a binding leaves unchanged, and by answers
# of this set; an answer that reads a binding or the provenance is computed
# again: `obligations` and a graph's `record`
# read the calibration, and `spans` the text the provenance holds. The cache of
# declared sets that `inventory.py` keeps is filled as it is read and is left
# behind as well.
CARRIED = frozenset(
    (
        "table",  # the construction table: `fold_stage` reads the definitions table and the blocks
        "wire_table",  # the wire table: the sorts of the wires, the blocks and the declared sets
        # of the parameters, with the table
        "graph",  # one graph at a grain: the stored graph, or the graph the wire table builds at
        # that grain
        "bubble",  # one piece at a grain: the interior of a box of a graph, which the wire table
        # builds
        "places",  # every box of the graphs at every grain, with where it stands
        "diagnostics",  # nine answers about the completeness of the stage: from the block
        # headers, their lines and the stored builders graphs
        "wire-expression",  # what a wire denotes: its producer's row in the wire table and
        # the definitions
        "wire-rules",  # the rules the operation writing a wire declares on it, from that row
        "wire-lines",  # the lines an unnamed input of a solve is made from, from the rows
        "wire carrier",  # a wire's mathematical carrier: the declared sets of its coordinates
        # and value
        "definition carrier",  # the carrier of a function or of a g or G segment:
        # the declared sets
        "selection",  # the conditional distribution an expectation selects: the declared
        # distributions and the row
    )
)


class StageVersion:
    """The base class of a constructed version of a stage; `ElaboratedStage`
    is its one subclass.

    It holds the cache of the answers a query derived from one version. The
    cache is an attribute of the version, so it is collected with the version
    and holds nothing of another version. It holds what a query reads, the
    construction table, the sorts of the wires, the definitions, the graphs
    of each grain and the conditions, and no object that holds the version,
    so that Python frees a version once nothing refers to it.

    A reader that must tell a constructed version from the stage under
    construction tests against this class.
    """

    @cached_property
    def _kept(self):
        """The answers kept for this version, by the key the query names.

        A `cached_property` writes into the instance dictionary and a frozen
        dataclass admits that, since it is the dictionary and not the
        attribute that is written. A version made from this one by
        `hypergraphs.copy_native` starts with copies of the answers
        kept under the keys of `CARRIED`, which the definitions table and the
        graphs determine and no binding changes, the copies referring to its
        own boxes and wires; a version `replace_stage` makes, which holds the
        same records, starts with the same answers and a wire table of its own
        (`_carry`), and a version holding the very same records as another
        can be given that version's answers under those keys
        (`carry_answers`). Every other answer a new version computes again.
        `__getstate__` leaves the answers out, so a version the standard pickle
        reads back starts with none.
        """
        return {}

    def _carry(self, successor, copier):
        """Give `successor`, a version holding the records of this one, the
        answers this version kept under the keys of `CARRIED`, each made by
        `copier`: the copier of the walk of `hypergraphs.copy_native` that made
        `successor`, so that the answers refer to its objects, or the identity
        where `replace_stage` gave `successor` these very records. The wire
        table, kept under `wire_table`, names its version by a weak reference
        and is made again for `successor`
        (`wire_sorts.WireTable.for_version`)."""
        kept = self.__dict__.get("_kept")
        if not kept:
            return
        successor.__dict__["_kept"] = {
            copier(key): answer.for_version(successor, copier)
            if key == "wire_table"
            else copier(answer)
            for key, answer in kept.items()
            if (key if isinstance(key, str) else key[0]) in CARRIED
        }

    def _discard(self, rows_changed):
        """Discard the answers kept for this version that a binding changes
        (specification 0.6 §7; implementation plan §4). A binding that adds no
        row keeps the answers under the keys of `CARRIED`, which the
        definitions table and the graphs determine, as a version made by a
        binding verb was given them; a binding that adds a block's rows keeps
        the declared construction table and the initial-level graphs alone,
        since the wire table, the builders-level graphs and bubbles, the
        places, the diagnostics and the wire answers read the bound rows.
        Every other answer reads the bindings or the provenance and is
        computed again."""
        kept = self.__dict__.get("_kept")
        if not kept:
            return

        def stays(key):
            if rows_changed:
                initial = isinstance(key, tuple) and key[:2] == ("graph", "initial")
                return key == "table" or initial
            return (key if isinstance(key, str) else key[0]) in CARRIED

        for key in [key for key in kept if not stays(key)]:
            del kept[key]

    def __getstate__(self):
        """What the standard pickle writes of a version and `copy.deepcopy`
        copies: the instance dictionary without the kept answers. The wire
        table among them holds a weak reference to the version, which no
        pickle writes; the version read back computes its answers again when
        asked. The unpickler writes the dictionary back directly, as a frozen
        dataclass admits, so no `__setstate__` is needed."""
        return {name: value for name, value in self.__dict__.items() if name != "_kept"}


def kept_answer(stage, key, compute):
    """The answer of a query, kept for the version it is asked of, so that a
    query whose cost measurement shows to be high is computed once per
    version and the reader sees the same answer. A `WorkingStage` keeps no
    answer, since its graph changes while the stage is constructed."""
    if not isinstance(stage, StageVersion):
        return compute()
    kept = stage._kept
    if key not in kept:
        kept[key] = compute()
    return kept[key]


@dataclasses.dataclass(frozen=True, kw_only=True)
class WorkingStage:
    """The stage while it is constructed: what the fold, the construction of
    the graphs and the queries read of it before the stage object exists.
    `hypergraph` holds the builder boxes with their working `BlockData`;
    `field_sorts` the sort of every field wire (the fields and the shocks the
    block headers list, in first-listing order) and `sorts` the sort of every
    wire, the local aliases of the builders' interiors included;
    `parameter_sets` the declared set of every parameter as a retained term
    and `setting_sets` that of every setting, a top-level declaration of a
    methods file (specification 0.7, S1); `law_terms` every law by its
    subjects; `data` the working annotation, of
    which the constructed stage keeps only what no query answers. It is built
    once, after the typing call, and is read and not written by the fold and
    the construction of the graphs; a working stage exists only inside
    `make_stage` and is stored nowhere. A reader of a stage below
    `ElaboratedStage` reads it from this or from a `StageVersion`, the base of
    a constructed version."""

    name: str
    kind: str
    hypergraph: BellmanHypergraph
    symbols: dict
    data: dict
    field_sorts: dict
    sorts: dict
    parameter_sets: dict
    law_terms: dict
    setting_sets: dict = dataclasses.field(default_factory=dict)


# The two attributes holding the stored graphs: `initial`, the
# `InitialDiagrams` record, and `_builders`, the `Builders` record.
GRAPH_RECORDS = ("initial", "_builders")

# The five attributes whose stored value is a record of this version.
# Reading `definitions` or `initial` gives a navigation object of
# `pieces.py`, and reading `_builders`, `bindings` or `provenance` gives the
# record itself; the package reads each record with `stored`. The bindings
# and the provenance are stored, so that a binding verb writes them through
# `store` into the stage it is called on (specification 0.6 §4.1).
STORED = ("definitions",) + GRAPH_RECORDS + ("bindings", "provenance")


def stored(stage, attribute):
    """The record held under one of the five attributes of `STORED`: the
    definitions table, the initial diagrams, the builders graphs, the
    bindings or the provenance. Reading
    `definitions` or `initial` gives a navigation object of `pieces.py`, and
    this gives what it was built from; the package reads the builders record
    with this function and never through the attribute `_builders`. A
    `WorkingStage`, which holds its own values, answers with the value it
    holds.

    This is the one accessor of a stored record: the instance dictionary is
    the descriptor's own storage and is read here and nowhere else, and
    `vars` is read nowhere.
    """
    return (
        stage.__dict__[attribute] if isinstance(stage, StageVersion) else getattr(stage, attribute)
    )


def store(stage, attribute, value):
    """Hold `value` under one of the five attributes of `STORED`. The
    descriptor of `pieces.py` writes through this function, so that the
    instance dictionary is written in this module alone, as it is read here
    alone."""
    stage.__dict__[attribute] = value


def bind_in_place(stage, *, rows_changed=False, **records):
    """`stage` itself with the records a binding verb binds written under
    their attributes of `STORED` through `store`, the bindings and the
    provenance and, where a method block adds definitions, the definitions
    table; the kept answers the binding changes are discarded
    (`StageVersion._discard`), all but the declared construction table and
    the initial-level graphs where `rows_changed` says that a block's rows
    were bound. Nothing is copied (specification 0.6 §4.1)."""
    unknown = set(records) - set(STORED)
    if unknown:
        raise ValueError(f"a binding writes the records of {STORED}; got {sorted(unknown)}")
    for attribute, record in records.items():
        store(stage, attribute, record)
    stage._discard(rows_changed)
    return stage


def rebuild_in_place(stage, fresh, **records):
    """`stage` itself holding the stored records of `fresh`, a version made
    anew of the same stage from another tree, with the records given written
    over them, the bindings and the provenance among them; every kept answer
    is discarded, since the definitions and the graphs change. `methodize`
    rebinds a stage occurrence this way (specification 0.7 §6)."""
    for attribute in STORED:
        store(stage, attribute, records.get(attribute, stored(fresh, attribute)))
    kept = stage.__dict__.get("_kept")
    if kept:
        kept.clear()
    return stage


def replace_stage(stage, **changes):
    """A new version of `stage` differing in the attributes named, built
    through the constructor as `dataclasses.replace` builds it. The three
    attributes of `STORED` are passed as the records `stored` reads under
    them, since reading `definitions` or `initial` gives a navigation object.
    Where `stage` is a constructed version, the constructor holds each record
    passed as it is, without freezing it again (`passed_from_version`). Where
    the changes name the bindings and the provenance alone, the new version
    holds the same records and starts with the same answers of `stage` under
    the keys of `CARRIED`, with a wire table of its own. Each version it
    makes is copied by `hypergraphs.copy_native` before the call of the
    package that made it returns, or takes the place of `stage`, which that
    call then discards."""
    held = {name: stored(stage, name) for name in STORED if name not in changes}
    token = _PASSED.set(tuple(held.values()) if isinstance(stage, StageVersion) else ())
    try:
        successor = dataclasses.replace(stage, **held, **changes)
    finally:
        _PASSED.reset(token)
    if changes.keys() <= {"bindings", "provenance"}:
        stage._carry(successor, lambda value: value)
    return successor


# The stored records `replace_stage` passes from a constructed version, held
# while the constructor of the new version runs. It is a `ContextVar`, so
# that two constructions at once, in two threads or two tasks, each read
# their own.
_PASSED = ContextVar("bellman_records_passed", default=())


def passed_from_version(record):
    """Whether `record` is one of the stored records `replace_stage` passes
    from a constructed version to the version whose constructor is running.
    A constructed version holds each stored record in its frozen form, made
    by its constructor (`ElaboratedStage.__post_init__`), by the copier
    (`copy_native`) or read back by the standard pickle, so the record is not
    frozen again."""
    return any(record is held for held in _PASSED.get())


def same_records(left, right):
    """Whether two versions hold the very same stored records: the same two
    graph records, and definitions tables holding the same records under the
    same identities, as every version `replace_stage` makes from one version
    does."""
    if any(stored(left, name) is not stored(right, name) for name in GRAPH_RECORDS):
        return False
    first, second = stored(left, "definitions"), stored(right, "definitions")
    return len(first) == len(second) and all(
        a is b and first[a] is second[b] for a, b in zip(first, second)
    )


def carry_answers(source, version):
    """Give `version` the answers `source` kept under the keys of `CARRIED`,
    in place of those `version` kept, where the two versions hold the very
    same records (`same_records`), as `replace_stage` gives them to the
    version it makes (`StageVersion._carry`): the objects `source` holds, and
    a wire table made again for `version`. Those answers are determined by
    the records, so `version` would compute the same ones."""
    if same_records(source, version):
        source._carry(version, lambda value: value)
