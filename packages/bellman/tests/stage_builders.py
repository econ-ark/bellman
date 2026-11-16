"""Functions that make a stage from a text or an application file, bind it,
read its places and the methods bound at them, read the term of a name or of
a declared set, and compare two stages."""

import functools

import pytest
from application_files import (
    CONTROL_BRANCHING_STAGE_FILES,
    CORPUS,
    PERFECT_FORESIGHT_MODULE,
    ROOT,
    SAVING_STAGE_FILES,
    SHOCK_BRANCHING_STAGE_FILES,
)
from stage_graphs import GRAPH_TRIPLES
from stage_texts import two_nodes_text_with_parameter_sets

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.source import to_source
from bellman.syntax.terms import Constant, Domain, Sym

# the condition that the value a calibration gives a parameter lies in the
# parameter's declared set
MEMBERSHIP_CONDITION = "calibration-domain-membership"


def undecided_memberships(stage):
    """The explanations of the membership conditions that a calibrated stage
    leaves undecided, those whose status is `required`."""
    return [
        item.explanation
        for item in stage.obligations()
        if item.condition == MEMBERSHIP_CONDITION and item.status == "required"
    ]


def declared_set_of(declaration):
    """The declared set that the parser keeps for the last declaration in the
    text `declaration`, read from the parsed text without building a
    stage."""
    term, _ = parse_with_spans(declaration + "\n", "t.bl")
    (domain,) = [c for c in term.items[-1].declaration.classifiers if isinstance(c, Domain)]
    return domain.space


def name_term(name):
    """The term of the name `name`."""
    return Sym(Constant(name))


def calibration_refusal_sentence(stage, values):
    """The sentence with which a copy of `stage` refuses the calibration
    `values`; the test fails where the copy accepts it."""
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate(values)
    return str(refused.value)


def construction_refusal(call):
    """The `ConstructionError` that `call()` raises; the test fails where the
    call raises none."""
    with pytest.raises(ConstructionError) as refused:
        call()
    return refused.value


def boxes_inside_bubble(graph, name):
    """The boxes inside the bubble `name` of a graph, by name; `graph` is the
    handle of a graph, such as `stage.builder.bwd`, or the DisCoPy diagram
    that the handle holds."""
    boxes = getattr(graph, "graph", graph).boxes
    return {box.name: box for box in next(box for box in boxes if box.name == name).arg.boxes}


def places_of(stage):
    """The addresses that `stage.places()` lists, in its order."""
    return [row["address"] for row in stage.places()]


def method_argument(components, name):
    """The value of the keyword argument `name` of the method word typed at a
    place, as the file writes it; `components` is what `stage.methods[place]`
    gives for that place."""
    return next(
        to_source(keyword.value) for keyword in components.method.arguments if keyword.key == name
    )


# the origin that `stage_from_text` gives a stage text by default
DEFAULT_ORIGIN = "t.bl"


def stage_from_text(text, origin=DEFAULT_ORIGIN):
    """The symbolic stage `elaborate_stage` makes of a stage text whose source
    is named `origin`."""
    from bellman.stage import elaborate_stage

    return elaborate_stage(
        {
            "stage": {"text": text, "origin": origin},
            "calibration": {},
            "settings": {},
            "methods": {},
        }
    )


def corpus_stage(name):
    """The symbolic stage of the corpus stage `name`, elaborated anew from its
    stage file."""
    return stage_from_file(CORPUS[name])


def origin_of(path):
    """The origin given to the stage file at `path`, a path absolute or
    relative to the repository: the file's path relative to the repository,
    written with forward slashes."""
    return (ROOT / path).resolve().relative_to(ROOT).as_posix()


def stage_from_file(path):
    """The symbolic stage of the stage file at `path`, a path absolute or
    relative to the repository, elaborated anew at each call from the file's
    text with `origin_of(path)` as its origin. The fixture
    `read_only_stage_from_file` keeps one stage of each file; a test that binds
    methods on a stage calls this."""
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), origin_of(path))


def methodized_copy(stage, *additions):
    """A copy of `stage` (`copy_native`) methodized in one call of
    `methodize` by `additions`, in their order. A string is the text of an
    addition to the stage: it is read after the line `@methods: <the stage's
    name>`, with the origin `addition-<n>.bl`, n its position among the
    additions. Any other addition, a mapping holding a text and its origin
    or the `Path` of a file, is read as it is given."""
    read = [
        {"text": f"@methods: {stage.name}\n{held}", "origin": f"addition-{n}.bl"}
        if isinstance(held, str)
        else held
        for n, held in enumerate(additions, start=1)
    ]
    return copy_native(stage).methodize(read)


def two_nodes_stage_with_declared_sets(declarations, addition=None):
    """The two-node stage with its declaration of β replaced by
    `declarations`, methodized by the methods text `addition` where one is
    given."""
    stage = stage_from_text(two_nodes_text_with_parameter_sets(declarations))
    return stage if addition is None else methodized_copy(stage, addition)


def saving_stage(name):
    """The symbolic stage of the stage file `name` of `SAVING_STAGE_FILES`."""
    return stage_from_file(SAVING_STAGE_FILES[name])


def control_branching_stage(name):
    """The symbolic stage of the stage file `name` of
    `CONTROL_BRANCHING_STAGE_FILES`, a branching stage whose branches a control
    selects."""
    return stage_from_file(CONTROL_BRANCHING_STAGE_FILES[name])


def shock_branching_stage(name):
    """The symbolic stage of the stage file `name` of
    `SHOCK_BRANCHING_STAGE_FILES`, a branching stage whose branches a shock
    selects."""
    return stage_from_file(SHOCK_BRANCHING_STAGE_FILES[name])


def without_addresses(table):
    """A definitions table with the address of every record set to the empty
    string.

    The address of a record of a top-level item is the position in the file
    at which the item is written. It names the file as the caller of the
    parser named it, and a term decoded from a saved AST has none. Two stages
    of one file therefore agree in every other field of every record,
    whatever name each gives the file."""
    import dataclasses

    return {
        identity: dataclasses.replace(record, address="") for identity, record in table.items()
    }


def differing_graph_triples(stage, other):
    """The triples (level, direction, grain) of `GRAPH_TRIPLES` at which the
    graphs of two stages differ, a refused graph counting as equal to a
    refusal under the same rule at the same term address.

    The tests of the recordings compare the text that `graphs_text` writes of
    the graphs of each corpus stage with the text stored in that stage's
    `.graphs.txt` file. A stage whose graphs equal those of a corpus stage at
    every triple therefore has the graphs that the stored text describes."""
    from bellman.refusals import NotConstructed
    from bellman.stage.grains import graph_of

    def outcome(version, selection):
        level, direction, grain = selection
        try:
            return graph_of(version, level, direction, grain)
        except NotConstructed as refusal:
            return (refusal.rule, refusal.address)

    return [
        selection
        for selection in GRAPH_TRIPLES
        if outcome(stage, selection) != outcome(other, selection)
    ]


@functools.cache
def closed_form_check():
    """The numerical module of the perfect-foresight application, loaded
    once from its file, so that the tests call the functions that the
    application's notebook calls."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("closed_form_check", PERFECT_FORESIGHT_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
