"""The recording the snapshot guard compares against (the first layer of the
tests, `packages/bellman/README.md` §8).

For each corpus stage of `conftest.CORPUS` it records the stage itself (its
printed description, its card `str(stage.denote())`, its definitions table
with the printed view of each record, and every condition `obligations`
returns) and every graph at every grain: the initial diagrams and the builders
graphs, each read backward and forward, at the grains `builder`, `sub-builder`,
`primitive`, `combined` and `factored`. A graph is recorded with its printed
listing, its inputs and outputs, its wiring and the sort of every wire; a box
with its name, its kind, the definitions it references or, for a block of an
initial diagram, the inputs its author declared, its inputs and outputs, the
statement of what it denotes and, for a bubble, its interior and that
interior's wiring. A graph the construction refused is recorded as its refusal.
Only public names are read.

Run from `packages/bellman` with the project interpreter, at the commit the
recording is to describe:

    PYTHONPATH=. python tests/snapshot/record.py

It writes `tests/snapshot/<stage>.json`, pretty-printed with sorted keys. With
`--leaves` it writes nothing and prints every leaf at which the recording the
package makes now differs from the stored one, one line each: the stage, the
selection, the box and the field, separated by tabs, so that the list can be
compared with the differences a build record names before it re-records.

With `--corpus` it writes instead the recordings of the stage files under
`applications/` that the corpus test `tests/test_snapshot.py` collects, in
`tests/snapshot/corpus/<application>/`, at the path `recording_path` gives:
for each file the parsed term `<file>.bl.ast.json` and the encoding of the
elaborated stage `<file>.bl.stage.json`, which the corpus test compares. A
recording the corpus test's tables leave out is not written: the encoding of
a file the tables hold as not elaborating, and the parsed term of one they
hold as unparseable. `--corpus FOLDER` writes the same recordings in FOLDER,
for a comparison with the stored ones.
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from conftest import (  # noqa: E402
    CORPUS,
    ROOT,
    STAGE_FILES,
    corpus_stage,
    stage_from_text,
)

APPLICATIONS = ROOT / "applications"
# the folder of the recordings the corpus test compares, with one folder per
# application
CORPUS_RECORDINGS = HERE / "corpus"

LEVELS = ("initial", "builders")
DIRECTIONS = ("backward", "forward")
GRAINS = ("builder", "sub-builder", "primitive", "combined", "factored")
# the keys of a recording: the stage itself, then level/direction/grain
SELECTIONS = ("stage",) + tuple(f"{level}/{d}/{g}"
                                for level in LEVELS for d in DIRECTIONS for g in GRAINS)


def printed_denotation(stage, target):
    """What a box or a definition denotes, as its card prints it
    (AMD-SG-021 §3), or the refusal of the query. It is `str(denote())` of
    the piece, which `denotations.card` answers for a target of any kind."""
    from bellman.stage.denotations import card
    try:
        return card(stage, target)
    except Exception as refusal:  # the query's refusal is part of the recording
        return f"refused: {type(refusal).__name__}: {refusal}"


def stage_card(stage):
    """The stage's card, `str(stage.denote())`, one string per line, or
    the refusal of the query as one line: the sheet whose entries are the
    builders."""
    try:
        return str(stage.denote()).splitlines()
    except Exception as refusal:  # the query's refusal is part of the recording
        return [f"refused: {type(refusal).__name__}: {refusal}"]


def conditions(items):
    # every entry of an obligation is one of the five typed kinds of
    # AMD-SG-017 §4, and the one printer of the package writes each: an
    # identity by its spelling (AMD-SG-016 §3), save a function's parameter,
    # written by the parameter's name
    from bellman.typing.typed_expressions import obligation_entry
    return [[item.condition, [obligation_entry(entry) for entry in item.entries], item.status]
            + ([item.explanation] if item.explanation else []) for item in items]


def wiring(graph):
    """The wiring of a hypergraph: the spider of every input, box port and
    output, and the sort of every spider."""
    return {"inputs": [ob.name for ob in graph.dom.inside],
            "outputs": [ob.name for ob in graph.cod.inside],
            "spiders": [repr(ob) for sort in graph.spider_types for ob in sort.inside],
            "input_wires": list(graph.dom_wires),
            "box_wires": [[list(ins), list(outs)] for ins, outs in graph.box_wires],
            "output_wires": list(graph.cod_wires)}


def box_record(stage, box):
    from discopy.frobenius import Hypergraph
    from bellman.stage.grains import kind_of
    entry = {"name": box.name, "kind": kind_of(box),
             "inputs": [ob.name for ob in box.dom.inside], "outputs": [ob.name for ob in box.cod.inside],
             "denotation": printed_denotation(stage, box)}
    data = getattr(box, "data", None)
    if isinstance(data, tuple):
        entry["references"] = [str(reference) for reference in data]
    elif hasattr(data, "inputs"):
        # a block of an initial diagram carries the inputs its author declared,
        # which its box no longer determines; the declared outputs are the
        # box's own wires (AMD-SG-013 §3; AMD-SG-014 §2)
        entry["header"] = [sort.name for sort in data.inputs]
    interior = getattr(box, "arg", None)
    if interior is not None:
        entry["interior"] = [box_record(stage, inner) for inner in interior.boxes]
        entry["interior_wiring"] = wiring(Hypergraph.from_diagram(interior))
    return entry


def graph_record(stage, graph):
    return {"listing": str(graph).splitlines(), "wiring": wiring(graph),
            "boxes": [box_record(stage, box) for box in graph.boxes]}


def record(stage, selection):
    """The recording of one selection of a stage: `stage`, or
    `level/direction/grain`."""
    from bellman.refusals import NotConstructed
    from bellman.stage.stage_answers import obligations
    if selection == "stage":
        return {"description": str(stage).splitlines(), "card": stage_card(stage),
                "repr": repr(stage),
                "definitions": [[str(item.identity), item.kind, printed_denotation(stage, item)]
                                for item in stage.definitions.values()],
                "obligations": conditions(obligations(stage))}
    level, direction, grain = selection.split("/")
    # `graph_of` keeps the grain as an argument, and the recorder reads the two
    # grains no attribute of a handle names (AMD-SG-012 §1)
    from bellman.stage.grains import graph_of
    try:
        graph = graph_of(stage, level, direction, grain)
    except NotConstructed as refusal:
        return {"refused": {"rule": refusal.rule, "address": refusal.address, "file": refusal.file,
                            "line": refusal.line, "column": refusal.column, "message": refusal.message}}
    return {**graph_record(stage, graph), "obligations": conditions(obligations(stage, level, direction))}


def recording_of(stage):
    """Every selection of a stage, as plain JSON values."""
    return json.loads(json.dumps({selection: record(stage, selection) for selection in SELECTIONS},
                                 ensure_ascii=False))


@functools.lru_cache(maxsize=None)
def stored(name):
    """The stored recording of the corpus stage `name`."""
    return json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))


def first_difference(recorded, live, where="recording"):
    """The first place where two recordings differ, named by the box when
    the difference lies inside one."""
    if isinstance(recorded, dict) and isinstance(live, dict):
        for key in sorted(set(recorded) | set(live)):
            if recorded.get(key) != live.get(key):
                return first_difference(recorded.get(key), live.get(key), f"{where}.{key}")
    if isinstance(recorded, list) and isinstance(live, list):
        for index, (a, b) in enumerate(zip(recorded, live)):
            if a != b:
                label = a.get("name", index) if isinstance(a, dict) else index
                return first_difference(a, b, f"{where}[{label}]")
        if len(recorded) != len(live):
            return f"{where}: {len(recorded)} entries recorded, {len(live)} now"
    return f"{where}: recorded {recorded!r}, now {live!r}"


# the key of a value one recording holds and the other does not, told apart
# from a held `None`
ABSENT = object()
# the three entries of a definition in the recording of the stage
DEFINITION_FIELDS = ("identity", "kind", "denotation")


def differing_leaves(recorded, live):
    """Every leaf at which two recordings of one selection differ, as pairs
    `(box, field)` in the order of the keys and the boxes.

    A leaf is a value that is not a mapping: a string, a number, or a list of
    strings or of lists, as the lines of a listing and the wires of a box are
    recorded. `box` names the box that holds the leaf, an inner box after the
    bubble that holds it (`cntn_to_dcsn / cntn_to_dcsn:Aggregation`); for a
    definition of the stage's table it is the definition's identity, and for a
    leaf of the graph or of the stage itself it is empty. `field` is the path
    of keys from the box, or from the selection, to the leaf (`denotation`,
    `wiring.spiders`, `card`). A box or a definition that one recording holds
    and the other does not is one leaf with an empty field, and a list of
    boxes or definitions whose order alone differs is one leaf, the list's
    key. `first_difference` names only the first of these leaves."""
    found = []
    _compare(recorded, live, (), (), found)
    return found


def _compare(recorded, live, box, field, found):
    """Append to `found` the differing leaves of two values of a recording
    reached by `box` and `field`."""
    if recorded == live:
        return
    if not (isinstance(recorded, dict) and isinstance(live, dict)):
        found.append((" / ".join(box), ".".join(field)))
        return
    for key in sorted(set(recorded) | set(live)):
        held, now = recorded.get(key, ABSENT), live.get(key, ABSENT)
        if held == now:
            continue
        if isinstance(held, list) and isinstance(now, list) and key in ("boxes", "interior"):
            _compare_entries(held, now, lambda entry: entry["name"], box, field + (key,), found)
        elif isinstance(held, list) and isinstance(now, list) and key == "definitions":
            _compare_entries([dict(zip(DEFINITION_FIELDS, entry)) for entry in held],
                             [dict(zip(DEFINITION_FIELDS, entry)) for entry in now],
                             lambda entry: entry["identity"], box, field + (key,), found)
        else:
            _compare(held, now, box, field + (key,), found)


def _named(entries, name_of):
    """The entries of a list by their name; a second entry of one name is
    keyed by its name and its place among the entries of that name."""
    seen, named = {}, {}
    for entry in entries:
        name = name_of(entry)
        seen[name] = seen.get(name, 0) + 1
        named[name if seen[name] == 1 else f"{name} ({seen[name]})"] = entry
    return named


def _compare_entries(recorded, live, name_of, box, field, found):
    """Compare two lists of boxes, or of definitions, entry by entry, each
    entry matched by its name and not by its place."""
    held, now = _named(recorded, name_of), _named(live, name_of)
    for name in list(held) + [name for name in now if name not in held]:
        if name not in held or name not in now:
            found.append((" / ".join(box + (name,)), ""))
        else:
            _compare(held[name], now[name], box + (name,), (), found)
    if set(held) == set(now) and list(held) != list(now):
        found.append((" / ".join(box), ".".join(field)))


def leaves_of_the_corpus(names=tuple(CORPUS)):
    """`(stage, selection, box, field)` of every leaf at which the recording
    the package makes now of each corpus stage in `names` differs from the
    stored one, for comparison with the differences a build record names
    before its lane re-records. A selection that one recording holds and the
    other does not is one leaf with an empty box and field."""
    found = []
    for name in names:
        held, live = stored(name), recording_of(corpus_stage(name))
        for selection in list(SELECTIONS) + sorted(set(held) - set(SELECTIONS)):
            if selection not in held or selection not in live:
                found.append((name, selection, "", ""))
            else:
                found.extend((name, selection) + leaf
                             for leaf in differing_leaves(held[selection], live[selection]))
    return found


def _within_applications(stage_path):
    """The path of the stage file `stage_path` relative to `applications/`;
    `stage_path` is absolute or relative to the repository."""
    path = Path(stage_path)
    return path.relative_to(APPLICATIONS if path.is_absolute() else "applications")


def recording_path(stage_path, suffix):
    """The path of a recording of the stage file `stage_path`, a file under
    `applications/`, of the kind `suffix` names: `.ast.json`, the parsed term,
    or `.stage.json`, the encoding of the elaborated stage. It is the
    file's name followed by `suffix`, in the folder of the file's application
    under `tests/snapshot/corpus/`:
    `applications/durables/declaration/stages/tenure/tenure.bl` with
    `.stage.json` has `tests/snapshot/corpus/durables/tenure.bl.stage.json`.
    The path depends on the application's folder name and the file's name
    alone, not on the folder the file stands in within its application."""
    within = _within_applications(stage_path)
    return CORPUS_RECORDINGS / within.parts[0] / (within.name + suffix)


def compared_suffixes(stage_path):
    """The suffixes of the recordings of the stage file `stage_path` that the
    corpus test compares, as its tables decide: `.ast.json` unless they hold
    the file as unparseable or as committed without its parsed term, and
    `.stage.json` unless they hold it as not elaborating."""
    # the corpus test imports this module, so its tables are read when this
    # function is called and not when this module is imported
    from snapshot.corpus_cases import KNOWN_UNELABORATABLE
    within = _within_applications(stage_path)
    suffixes = []
    suffixes.append(".ast.json")
    if within.as_posix() not in KNOWN_UNELABORATABLE:
        suffixes.append(".stage.json")
    return tuple(suffixes)


def parsed_term_text(text, origin):
    """The stored text of the parsed term of a stage text whose source is
    named `origin`: `to_json` of the term `parse_with_spans` answers,
    indented by two spaces."""
    from bellman.syntax.lower import parse_with_spans, to_json
    term = parse_with_spans(text, origin).term
    return json.dumps(to_json(term), indent=2, ensure_ascii=False) + "\n"


def _stored_encoding(stage):
    """The stored text of the encoding of a version of a stage:
    `stage.encoding()` on one line, its keys sorted."""
    return json.dumps(stage.encoding(), ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"


def encoding_text(text, origin):
    """The stored text of the encoding of the stage elaborated from a stage
    text whose source is named `origin`."""
    return _stored_encoding(stage_from_text(text, origin))


# The function that writes each recording, by its suffix.
TEXT_OF_RECORDING = {".ast.json": parsed_term_text, ".stage.json": encoding_text}


def corpus_recordings(stage_path):
    """The recordings `--corpus` writes of the stage file `stage_path`, by
    suffix, each as the text stored and compared by the corpus test."""
    within = _within_applications(stage_path)
    text = (APPLICATIONS / within).read_text(encoding="utf-8")
    origin = "applications/" + within.as_posix()
    return {suffix: TEXT_OF_RECORDING[suffix](text, origin)
            for suffix in compared_suffixes(stage_path)}


def write_corpus_recordings(stage_path, folder=CORPUS_RECORDINGS):
    """Write the recordings `corpus_recordings` makes of the stage file
    `stage_path` in `folder`, each at its `recording_path` relative to
    `tests/snapshot/corpus/`, and answer the paths written, by suffix."""
    written = {}
    for suffix, text in corpus_recordings(stage_path).items():
        path = Path(folder) / recording_path(stage_path, suffix).relative_to(CORPUS_RECORDINGS)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written[suffix] = path
    return written


if __name__ == "__main__":
    options = argparse.ArgumentParser(description="Write the recordings of the snapshot guard, "
                                                  "or with --corpus those of the stage files "
                                                  "the corpus test collects.")
    choice = options.add_mutually_exclusive_group()
    choice.add_argument("--leaves", action="store_true",
                        help="print every leaf at which a stored recording of the snapshot "
                             "guard differs and write nothing")
    choice.add_argument("--corpus", nargs="?", const=CORPUS_RECORDINGS, type=Path,
                        metavar="FOLDER",
                        help="write the recordings of the stage files the corpus test "
                             "collects, in FOLDER where one is named")
    arguments = options.parse_args()
    if arguments.leaves:
        for leaf in leaves_of_the_corpus():
            print("\t".join(leaf))
    elif arguments.corpus is not None:
        for stage_file in STAGE_FILES:
            for path in write_corpus_recordings(stage_file, arguments.corpus).values():
                print(path.relative_to(arguments.corpus).as_posix(), path.stat().st_size, "bytes")
    else:
        for name in CORPUS:
            path = HERE / f"{name}.json"
            path.write_text(json.dumps(recording_of(corpus_stage(name)), indent=1, sort_keys=True,
                                       ensure_ascii=False) + "\n", encoding="utf-8")
            print(path.name, path.stat().st_size, "bytes")
