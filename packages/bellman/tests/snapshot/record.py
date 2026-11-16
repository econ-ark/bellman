"""Write the recordings that the tests of the recordings compare, or the
encodings of the stage files for a comparison between two commits.

Run from `packages/bellman` with the project interpreter, at the commit the
files are to describe. Run as a script, the file reads the package `bellman`
of the checkout that holds it, whatever copy the environment has installed.
The script has two uses. Run with neither option, it prints its usage and
exits with a non-zero status.

1. With `--corpus` it writes the recordings of the stage files under
   `applications/` that the tests of the recordings, in
   `tests/test_applications.py`, collect:

       python tests/snapshot/record.py --corpus

   It writes them in `tests/snapshot/corpus/<application>/`, at the path that
   `recording_path` gives, one for each suffix that `compared_suffixes` gives:
   for each file the parsed term `<file>.bl.ast.json`; unless the mapping
   `REFUSED_STAGE_FILES` of `corpus_cases.py` holds the file as refused, the
   printed text of the elaborated stage `<file>.bl.printed.txt`; and, for the
   stage file of each of the eight corpus stages of `CORPUS` in
   `application_files.py`, the text of the stage's graphs
   `<file>.bl.graphs.txt` that `graphs_text` returns. It also writes the
   printed text of the adjuster stage, the adjuster's consumption stage of the
   durables model in the file `ADJUSTER_CONS_WITH_EGM_LINES_FILE`, in the
   folder `fixtures` of the folder of the recordings, at
   `ADJUSTER_CONS_PRINTED_TEXT_PATH`. `--corpus FOLDER` writes the same files
   in FOLDER, at the same paths relative to FOLDER, for a comparison with the
   stored ones.

2. With `--encodings FOLDER` it writes the encoding of every stage file
   that elaborates in FOLDER, so that a person can compare the encodings of
   two commits:

       python tests/snapshot/record.py --encodings FOLDER

   Each encoding stands at `<application>/<file>.bl.stage.json`, as the
   text that `encoding_as_stored` returns. FOLDER must lie outside the
   repository. The tests store no encoding; `validate_encodings.py` records
   the digests of each.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
if __name__ == "__main__":
    from snapshot import put_this_checkout_first

    put_this_checkout_first()

from application_files import (  # noqa: E402
    ADJUSTER_CONS_WITH_EGM_LINES_FILE,
    CORPUS,
    ROOT,
    STAGE_FILES,
)
from printed_text import PrintedStage, refusal_text  # noqa: E402
from stage_builders import origin_of, stage_from_file  # noqa: E402
from stage_graphs import (  # noqa: E402
    GRAINS,
    boxes_with_wires,
    graph_handle,
    graphs_inside,
    graphs_of,
    interior_of,
    port_wires,
    wire_sorts,
)

from snapshot.corpus_cases import REFUSED_STAGE_FILES  # noqa: E402

APPLICATIONS = ROOT / "applications"
# the folder of the recordings that the tests of the recordings compare, with
# one folder per application and the folder `fixtures` for the adjuster stage
CORPUS_RECORDINGS = HERE / "corpus"
# the path, relative to the folder of the recordings, of the printed text of
# the adjuster stage, the stage file that `ADJUSTER_CONS_WITH_EGM_LINES_FILE`
# names
ADJUSTER_CONS_PRINTED_TEXT_PATH = Path("fixtures") / (
    Path(ADJUSTER_CONS_WITH_EGM_LINES_FILE).name + ".printed.txt"
)
# the command, run from packages/bellman, that writes every recording under
# the folder of the recordings
WRITE_RECORDINGS_COMMAND = "python tests/snapshot/record.py --corpus"
# the command, run from packages/bellman, that writes the encodings of the
# stage files of a commit in FOLDER, outside the repository
WRITE_ENCODINGS_COMMAND = "python tests/snapshot/record.py --encodings FOLDER"
# the instruction for a file under the folder of the recordings that no test
# compares
DELETE_BY_HAND_INSTRUCTION = (
    f"The command {WRITE_RECORDINGS_COMMAND} writes files and removes none: delete each of these "
    "files by hand."
)


def _within_applications(stage_path):
    """The path of the stage file `stage_path` relative to `applications/`;
    `stage_path` is absolute or relative to the repository."""
    path = Path(stage_path)
    return path.relative_to(APPLICATIONS if path.is_absolute() else "applications")


def recording_path(stage_path, suffix):
    """The path of a recording of the stage file `stage_path`, a file under
    `applications/`, of the kind `suffix` names: `.ast.json`, the parsed term,
    `.printed.txt`, the printed text of the elaborated stage, or
    `.graphs.txt`, the text of the graphs of the elaborated stage. It is the
    file's name followed by `suffix`, in the folder of the file's application
    under `tests/snapshot/corpus/`:
    `applications/durables/declaration/stages/tenure/tenure.bl` with
    `.printed.txt` has `tests/snapshot/corpus/durables/tenure.bl.printed.txt`.
    The path depends on the application's folder name and the file's name
    alone, not on the folder the file stands in within its application.
    `write_encodings` writes an encoding under the folder it is given, at
    the path that this function gives with `.stage.json` relative to the
    folder of the recordings."""
    within = _within_applications(stage_path)
    return CORPUS_RECORDINGS / within.parts[0] / (within.name + suffix)


def elaborates(stage_path):
    """Whether the tests of the recordings elaborate the stage file
    `stage_path`, a file under `applications/`: whether the mapping
    `REFUSED_STAGE_FILES` of `corpus_cases.py` does not hold it as
    refused."""
    return _within_applications(stage_path).as_posix() not in REFUSED_STAGE_FILES


# the suffix of the text of the graphs of a corpus stage
GRAPHS_SUFFIX = ".graphs.txt"
# the stage files of the eight corpus stages, in the order of `CORPUS`
CORPUS_STAGE_FILES = [ROOT / path for path in CORPUS.values()]


def compared_suffixes(stage_path):
    """The suffixes of the recordings of the stage file `stage_path` that the
    tests of the recordings compare: `.ast.json`; `.printed.txt` when the file
    elaborates; and `.graphs.txt` when the file elaborates and is one of
    `CORPUS_STAGE_FILES`."""
    if not elaborates(stage_path):
        return (".ast.json",)
    suffixes = (".ast.json", ".printed.txt")
    if APPLICATIONS / _within_applications(stage_path) in CORPUS_STAGE_FILES:
        suffixes += (GRAPHS_SUFFIX,)
    return suffixes


# the stage files that the tests of the recordings elaborate
ELABORATED_FILES = [src for src in STAGE_FILES if elaborates(src)]


def left_over_files(folder=CORPUS_RECORDINGS):
    """The files under `folder` that are no recording the tests compare, by
    their paths relative to `folder` with forward slashes, sorted.

    A recording the tests compare is the recording of a stage file of
    `STAGE_FILES` under a suffix that `compared_suffixes` gives, at the path
    that `recording_path` gives relative to the folder of the recordings, or
    the printed text of the adjuster stage, at
    `ADJUSTER_CONS_PRINTED_TEXT_PATH`. A file whose name begins with a dot,
    such as the `.DS_Store` that the macOS Finder writes, is left out, and so
    is a file inside a folder whose name begins with a dot, since no recording
    has such a name or stands in such a folder."""
    compared = {
        recording_path(src, suffix).relative_to(CORPUS_RECORDINGS)
        for src in STAGE_FILES
        for suffix in compared_suffixes(src)
    }
    compared.add(ADJUSTER_CONS_PRINTED_TEXT_PATH)
    folder = Path(folder)
    return sorted(
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(folder).parts)
        and path.relative_to(folder) not in compared
    )


def parsed_term_text(text, origin):
    """The stored text of the parsed term of a stage text whose source is
    named `origin`: `to_json` of the term `parse_with_spans` answers,
    indented by two spaces."""
    from bellman.syntax.lower import parse_with_spans, to_json

    term = parse_with_spans(text, origin).term
    return json.dumps(to_json(term), indent=2, ensure_ascii=False) + "\n"


def encoding_as_stored(stage):
    """The text of the encoding of a version of a stage, which
    `write_encodings` writes and whose digests `validate_encodings.py`
    records: `stage.encoding()` on one line, its keys sorted."""
    return json.dumps(stage.encoding(), ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"


# the line that opens the section of one card in a printed text is the
# card's title between these two marks
SECTION_MARKS = ("==== ", " ====")
# that line, read back with the title as its one group
SECTION_LINE = re.compile("(.*)".join(re.escape(mark) for mark in SECTION_MARKS))
# the one line that `graphs_text` writes as the body of a section whose body
# equals that of an earlier section, read back with the earlier section's
# title as its one group
SAME_AS_LINE = re.compile("the same as (.*)")


def stage_printed_text(stage):
    """The printed text of a stage: `str(stage)`, then for each card that
    `PrintedStage(stage).cards` gives, a blank line, the line
    `==== <title> ====` and the card's text as printed. The text ends with
    one newline."""
    before, after = SECTION_MARKS
    lines = [str(stage)]
    for title, text, _ in PrintedStage(stage).cards:
        lines += ["", f"{before}{title}{after}", text]
    return "\n".join(lines).rstrip("\n") + "\n"


def graphs_text(stage) -> str:
    """The text of the graphs of a stage, which `graphs_of` gives.

    The text is a sequence of sections, separated by blank lines. Each
    section opens with the line `==== <title> ====`. The first section,
    `wires`, holds `repr` of each distinct sort of a wire of the stage's
    graphs, the graphs inside bubbles included, in the order in which
    `graphs_of` first gives it. The second, `conditions of the stage`,
    holds the conditions of the whole stage. Then, for each level and
    direction, the section `<level> <direction>: conditions` holds the
    conditions of that level and direction, and for each grain the section
    `<level> <direction> <grain>: listing` holds the listing that the
    package prints for the graph, and the section
    `<level> <direction> <grain>: wiring` holds the wiring that
    `wiring_lines` writes. A graph that the package refuses has the one
    section `<level> <direction> <grain>: refused` in place of those two,
    holding the line that `refusal_text` writes of its refusal. A section
    whose body equals the body of an earlier section holds the line
    `the same as <title of the earliest section with that body>`. The text
    ends with one newline."""
    from bellman.refusals import NotConstructed

    graphs = list(graphs_of(stage))
    # the sorts as the keys of a mapping, kept in the order first met
    sorts = {}
    for *_, graph in graphs:
        if not isinstance(graph, NotConstructed):
            for _, held in graphs_inside(graph, ""):
                for sort in wire_sorts(held):
                    sorts.setdefault(repr(sort))
    sections = [
        ("wires", list(sorts)),
        ("conditions of the stage", condition_lines(stage.obligations())),
    ]
    for level, direction, grain, graph in graphs:
        where = f"{level} {direction}"
        # the conditions of a level and direction stand before its first grain
        if grain == GRAINS[0]:
            conditions = graph_handle(stage, level, direction).obligations()
            sections.append((f"{where}: conditions", condition_lines(conditions)))
        if isinstance(graph, NotConstructed):
            sections.append((f"{where} {grain}: refused", [refusal_text(graph)]))
        else:
            sections.append((f"{where} {grain}: listing", str(graph).split("\n")))
            sections.append((f"{where} {grain}: wiring", wiring_lines(graph)))
    before, after = SECTION_MARKS
    # the title of the earliest section with each body, by the body
    earliest = {}
    lines = []
    for title, body in sections:
        text = "\n".join(body)
        first = earliest.setdefault(text, title)
        written = text if first == title else f"the same as {first}"
        lines += ["", f"{before}{title}{after}", written]
    return "\n".join(lines[1:]) + "\n"


def condition_lines(conditions):
    """The lines that write the conditions `conditions`, which the package
    returns for a stage or for one of its graphs. Each condition is the line
    `<condition> (<status>): <entries>`, its entries joined by "; ", followed
    by its explanation, where it has one, on a line indented by four spaces.
    An empty list of conditions or of entries is written `none`."""
    from bellman.typing.typed_expressions import obligation_entry

    lines = []
    for item in conditions:
        entries = "; ".join(obligation_entry(entry) for entry in item.entries)
        lines.append(f"{item.condition} ({item.status}): {entries or 'none'}")
        if item.explanation:
            lines.append(f"    {item.explanation}")
    return lines or ["none"]


def wiring_lines(graph, indent=""):
    """The lines that write the wiring of a graph, each line after `indent`.

    The first two lines are `inputs:` and `outputs:`, each followed by the
    identities of the wires at the graph's ports. Each box of the graph then
    has the line `<name> [<kind>]`, with `kind_of(box)` as its kind and no
    bracket when the kind is None, and, indented by four spaces, the line
    `reads:` and the line `writes:`, followed by the identities of the wires
    at its input ports and at its output ports. A box whose data are a
    tuple of references has the line `refers to:`, followed by those
    references. A block of an initial diagram has the line `declares:`,
    followed by the names of the inputs that its author declared. A bubble
    has the line `inside:`, followed by the lines of the graph inside it,
    indented by four more spaces. An empty list is written `none`."""
    from bellman.stage.grains import kind_of

    sorts = wire_sorts(graph)

    def listed(names):
        return ", ".join(names) or "none"

    def identities(wires):
        return listed(str(sorts[wire].identity) for wire in wires)

    inputs, outputs = port_wires(graph)
    lines = [f"{indent}inputs: {identities(inputs)}", f"{indent}outputs: {identities(outputs)}"]
    for box, read, written in boxes_with_wires(graph):
        kind = kind_of(box)
        lines.append(f"{indent}{box.name}" + ("" if kind is None else f" [{kind}]"))
        lines.append(f"{indent}    reads: {identities(read)}")
        lines.append(f"{indent}    writes: {identities(written)}")
        data = getattr(box, "data", None)
        if isinstance(data, tuple) and data:
            lines.append(f"{indent}    refers to: {listed(str(reference) for reference in data)}")
        elif hasattr(data, "inputs"):
            # a block of an initial diagram, whose data hold its header
            lines.append(f"{indent}    declares: {listed(sort.name for sort in data.inputs)}")
        interior = interior_of(box)
        if interior is not None:
            lines.append(f"{indent}    inside:")
            lines += wiring_lines(interior, indent + "        ")
    return lines


def _section_of_line(lines, index):
    """The section of a text, given as its `lines`, that holds the line at
    `index`: the title of the last line `==== <title> ====` at or before
    it, or the stage's own text when no such line comes before it."""
    for line in reversed(lines[: index + 1]):
        opening = SECTION_LINE.fullmatch(line)
        if opening:
            return f'the section "{opening.group(1)}"'
    return "the stage's own text"


def text_difference(recorded: str, live: str) -> str:
    """A message that names the first line at which the recorded text
    `recorded` and the live text `live` differ, each a printed text or a
    text of the graphs.

    Before the lines are compared, each section of a text of the graphs that
    is written as the one line `the same as <title>` is written out, in each
    text, as the body of the section that it names, so that a section that
    stops being equal to the section it names shows its changed line. The
    message gives the line's number in the recorded text and the section
    that holds the line: the title of the last line `==== <title> ====` at
    or before it, or the stage's own text when no such line comes before it.
    A line of a section written out has the number of the line
    `the same as <title>` in the recorded text. The message shows the
    recorded line and the live line. When one text is the other with lines
    added at its end, the message says which text has more lines and shows
    the first of those lines, with its number in that text. The message ends
    with the command that writes the recordings again, to be run once the
    difference has been read. Two equal texts give an empty message."""
    if recorded == live:
        return ""
    return (
        f"{_where_the_texts_differ(recorded, live)}\n"
        "After reading the difference, run from packages/bellman the command that writes "
        f"the recordings again: {WRITE_RECORDINGS_COMMAND}"
    )


def _numbered_lines(text):
    """`(line, number)` for each line of a text, numbered from 1."""
    return [(line, number) for number, line in enumerate(text.removesuffix("\n").split("\n"), 1)]


def _written_out(text):
    """The lines of a text as `_numbered_lines` gives them, with the body of
    each section that is the one line `the same as <title>` replaced by the
    lines of the body of the earlier section titled `<title>`, each with the
    number of the line it replaces. The body of a section is the lines after
    its line `==== <title> ====` up to the next such line, without the blank
    line before it."""
    lines = _numbered_lines(text)
    starts = [index for index, (line, _) in enumerate(lines) if SECTION_LINE.fullmatch(line)]
    if not starts:
        return lines
    written = lines[: starts[0]]
    bodies = {}
    for start, end in zip(starts, starts[1:] + [len(lines)]):
        body, separator = lines[start + 1 : end], []
        if end < len(lines) and body and body[-1][0] == "":
            body, separator = body[:-1], body[-1:]
        same = SAME_AS_LINE.fullmatch(body[0][0]) if len(body) == 1 else None
        if same is not None and same.group(1) in bodies:
            body = [(line, body[0][1]) for line, _ in bodies[same.group(1)]]
        bodies[SECTION_LINE.fullmatch(lines[start][0]).group(1)] = body
        written += [lines[start], *body, *separator]
    return written


def _where_the_texts_differ(recorded, live):
    """The lines of the message of `text_difference` that say where two
    different texts differ."""
    for held, now in (
        (_written_out(recorded), _written_out(live)),
        (_numbered_lines(recorded), _numbered_lines(live)),
    ):
        for index, ((old, number), (new, _)) in enumerate(zip(held, now)):
            if old != new:
                return (
                    f"The texts differ at line {number}, "
                    f"in {_section_of_line([line for line, _ in held], index)}.\n"
                    f"recorded: {old!r}\n"
                    f"live:     {new!r}"
                )
        if len(held) != len(now):
            break
    else:
        ending = "recorded" if recorded.endswith("\n") else "live"
        return (
            f"The texts differ only at their end: the {ending} text ends "
            "with a newline and the other does not."
        )
    if len(held) > len(now):
        longer, name, other = held, "recorded", "live"
    else:
        longer, name, other = now, "live", "recorded"
    index = min(len(held), len(now))
    count = len(longer) - index
    line, number = longer[index]
    return (
        f"The {name} text has {count} more {'line' if count == 1 else 'lines'} than the "
        f"{other} text, from line {number}, "
        f"in {_section_of_line([text for text, _ in longer], index)}.\n"
        f"{name + ':':<10}{line!r}"
    )


def corpus_recordings(stage_path):
    """The recordings `--corpus` writes of the stage file `stage_path`, one for
    each suffix that `compared_suffixes` gives, each as the text stored and
    compared by the tests of the recordings: the parsed term; when the file
    elaborates, the printed text of the stage that `stage_from_file`
    elaborates; and, when the file is one of `CORPUS_STAGE_FILES`, the text of
    the graphs of that same stage."""
    path = APPLICATIONS / _within_applications(stage_path)
    text = path.read_text(encoding="utf-8")
    recordings = {".ast.json": parsed_term_text(text, origin_of(path))}
    suffixes = compared_suffixes(stage_path)
    if ".printed.txt" in suffixes:
        stage = stage_from_file(path)
        recordings[".printed.txt"] = stage_printed_text(stage)
        if GRAPHS_SUFFIX in suffixes:
            recordings[GRAPHS_SUFFIX] = graphs_text(stage)
    return recordings


def missing_recordings_message(missing):
    """The failure message for recordings that are missing, given as pairs
    `(stage file, recording)` of paths: one line for each pair, naming the
    stage file and the recording by their paths in the repository, then the
    command that writes the recordings."""
    lines = [
        f"The stage file {origin_of(src)} has no recording {origin_of(path)}."
        for src, path in missing
    ]
    lines.append(
        "Run from packages/bellman the command that writes the recordings: "
        f"{WRITE_RECORDINGS_COMMAND}"
    )
    return "\n".join(lines)


def write_recording(path, text):
    """Write `text` at `path` in UTF-8 with `\\n` line ends, making its
    folder if it is missing, and return `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def write_corpus_recordings(stage_path, folder=CORPUS_RECORDINGS):
    """Write the recordings `corpus_recordings` makes of the stage file
    `stage_path`, one for each suffix that `compared_suffixes` gives, in
    `folder`, each at its `recording_path` relative to
    `tests/snapshot/corpus/`, and answer the paths written, by suffix."""
    written = {}
    for suffix, text in corpus_recordings(stage_path).items():
        path = Path(folder) / recording_path(stage_path, suffix).relative_to(CORPUS_RECORDINGS)
        written[suffix] = write_recording(path, text)
    return written


def adjuster_cons_printed_text():
    """The printed text of the adjuster stage, elaborated by `stage_from_file`
    from the file that `ADJUSTER_CONS_WITH_EGM_LINES_FILE` names."""
    return stage_printed_text(stage_from_file(ADJUSTER_CONS_WITH_EGM_LINES_FILE))


def write_adjuster_cons_printed_text(folder=CORPUS_RECORDINGS):
    """Write the printed text of the adjuster stage in `folder` at
    `ADJUSTER_CONS_PRINTED_TEXT_PATH`, and return the path written."""
    return write_recording(
        Path(folder) / ADJUSTER_CONS_PRINTED_TEXT_PATH, adjuster_cons_printed_text()
    )


# the suffix of the file of an encoding that `write_encodings` writes
ENCODING_SUFFIX = ".stage.json"


class FolderInsideTheRepository(ValueError):
    """The refusal of a folder for the encodings that is the repository's
    root or lies under it."""


def folder_outside_the_repository(folder):
    """`folder` as a path, when it lies outside the repository. A folder that
    is the repository's root or lies under it raises a
    `FolderInsideTheRepository`, a `ValueError`, so that no encoding is
    written among the files of the repository.

    The folder and each folder above it that exists are compared with the
    repository's root as files, not as strings, so that a path written with
    the case of its letters changed is refused too on a file system that
    ignores case. A path that the user may not search counts as absent:
    `os.path.exists` answers False for it, where `Path.exists` raises a
    `PermissionError` under Python 3.12 and 3.13."""
    folder = Path(folder)
    resolved = folder.resolve()
    if any(os.path.exists(path) and path.samefile(ROOT) for path in (resolved, *resolved.parents)):
        raise FolderInsideTheRepository(
            f"The folder {folder} lies inside the repository {ROOT}. Name a folder "
            "outside the repository for the encodings."
        )
    return folder


def write_encodings(folder, stage_files=ELABORATED_FILES):
    """Write the encoding of each stage file of `stage_files` in `folder`, at
    `<application>/<file>.bl.stage.json`, and answer the paths written.

    Each stage is elaborated anew by `stage_from_file`, and its encoding is
    written as the text that `encoding_as_stored` returns, whose SHA-256
    digest `encoding_digests.json` records under `encoding`. A `folder`
    inside the repository raises the `FolderInsideTheRepository` of
    `folder_outside_the_repository` before any stage is elaborated."""
    folder = folder_outside_the_repository(folder)
    written = []
    for src in stage_files:
        relative = recording_path(src, ENCODING_SUFFIX).relative_to(CORPUS_RECORDINGS)
        written.append(
            write_recording(folder / relative, encoding_as_stored(stage_from_file(src)))
        )
    return written


if __name__ == "__main__":
    options = argparse.ArgumentParser(
        description="Write with --corpus the recordings of the stage files that the tests of the "
        "recordings collect, or with --encodings the encoding of every stage file that elaborates."
    )
    choice = options.add_mutually_exclusive_group(required=True)
    choice.add_argument(
        "--corpus",
        nargs="?",
        const=CORPUS_RECORDINGS,
        type=Path,
        metavar="FOLDER",
        help="write the recordings of the stage files that the tests of the recordings "
        "collect and the printed text of the adjuster stage, in FOLDER where one is named",
    )
    choice.add_argument(
        "--encodings",
        type=Path,
        metavar="FOLDER",
        help="write the encoding of every stage file that elaborates in FOLDER, which must "
        "lie outside the repository",
    )
    arguments = options.parse_args()
    if arguments.encodings is not None:
        try:
            written = write_encodings(arguments.encodings)
        except FolderInsideTheRepository as refusal:
            # the refusal of a folder inside the repository ends the script
            # with its message and the exit status 1, without a traceback
            sys.exit(str(refusal))
        for path in written:
            print(path.relative_to(arguments.encodings).as_posix(), path.stat().st_size, "bytes")
    else:
        for stage_file in STAGE_FILES:
            for path in write_corpus_recordings(stage_file, arguments.corpus).values():
                print(path.relative_to(arguments.corpus).as_posix(), path.stat().st_size, "bytes")
        path = write_adjuster_cons_printed_text(arguments.corpus)
        print(path.relative_to(arguments.corpus).as_posix(), path.stat().st_size, "bytes")
