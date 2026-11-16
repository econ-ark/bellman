"""The command `python -m bellman`, the period line of the dossier, and the
full and the compact dossier of a stage."""

import functools
import re
import shutil
import subprocess
import sys
from collections import Counter

import pytest
from application_files import (
    BUFFER_STOCK_FILE,
    CORPUS,
    DURABLES,
    ROOT,
    checkout_environment,
    stage_file_id,
)
from snapshot.record import ELABORATED_FILES
from stage_builders import stage_from_text
from two_sets import one_row_by_default

from bellman.dossier import (
    RULE_CHARACTERS,
    compact_dossier_lines,
    condition_key,
    condition_rows,
    dossier,
    dossier_lines,
    period_lines,
)
from bellman.refusal_catalogue import catalogue
from bellman.refusal_catalogue import text_of as example_text
from bellman.refusal_examples import EXAMPLES
from bellman.refusals import ConstructionError

# The dossier of a stage is the numbered text of its printed answers. The
# full dossier, which `dossier_lines` answers, prints every card of the stage;
# `python -m bellman --dossier` prints it with the stage's source. The compact
# dossier, which `compact_dossier_lines` answers, states each fact once and
# leaves out the cards that repeat another. A rule line is a line drawn with
# the characters of `RULE_CHARACTERS` alone, such as the heavy line under the
# title of a card. The period line is the last line of the dossier of a
# period file, which says whether the stages that the period names elaborate
# as one period.


# a numbered line of a dossier: four digits, then two spaces and the text, or
# nothing
NUMBERED_LINE = re.compile(r"^(\d{4})(?:  (.*))?$")


# the stage files whose compact dossier prints a condition under a builders
# graph
FILES_WITH_CONDITIONS_UNDER_BUILDERS = [
    ROOT / "applications" / relative
    for relative in (
        "benhabib-2019/declaration/stages/benhabib_bellman/benhabib_bellman.bl",
        "benhabib-2019/declaration/stages/bequest/bequest.bl",
        "consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/"
        "perfect_foresight.bl",
        "epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl",
        "smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl",
    )
]


# the arguments of each call of the command that prints, and the fixture that
# gives the text it prints, by the word that names each in a test id
PRINTED = {
    "view": ([CORPUS["cons"]], "printed_view"),
    "encoding": ([CORPUS["cons"], "--encoding"], "printed_encoding"),
    "dossier": ([CORPUS["cons"], "--dossier"], "printed_dossier"),
    "refusals": (["--refusals"], "printed_refusal_catalogue"),
}


# the three output options of the command line, by the word that names each
# in a test id
OUTPUT_OPTIONS = {"view": [], "encoding": ["--encoding"], "dossier": ["--dossier"]}


# the argument lists that the command line refuses, by the words that name
# each in a test id
INVALID_ARGUMENTS = {
    "no-source": [],
    "encoding-without-source": ["--encoding"],
    "unknown-option": [CORPUS["cons"], "--unknown"],
    "two-output-options": [CORPUS["cons"], "--encoding", "--dossier"],
    "period-option": [CORPUS["cons"], "--period", "period.yml"],
}


def run_command(*arguments):
    """The answer of `python -m bellman` with `arguments`, run from the root of
    the repository in a new interpreter that imports the package of this
    checkout."""
    return subprocess.run(
        [sys.executable, "-m", "bellman", *arguments],
        cwd=ROOT,
        env=checkout_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def numbers_and_texts(lines):
    """The number and the text of each line of a dossier, the number None for
    a line that does not open with four digits."""
    pairs = []
    for line in lines:
        matched = NUMBERED_LINE.match(line)
        pairs.append((int(matched.group(1)), matched.group(2) or "") if matched else (None, line))
    return pairs


def line_texts(lines):
    """The text of each line of a dossier, without its number."""
    return [text for _, text in numbers_and_texts(lines)]


@pytest.fixture(scope="module")
def command_answer():
    """`command_answer(*arguments)`: the answer of `python -m bellman` with the
    arguments, run once in the module for each list of arguments."""
    return functools.cache(run_command)


@pytest.fixture
def printed_view(cons):
    """The view of the consumption stage, as the command prints it."""
    return cons.view() + "\n"


@pytest.fixture
def printed_encoding(cons):
    """The encoding of the consumption stage, as the command prints it."""
    return str(cons.encoding()) + "\n"


@pytest.fixture
def printed_dossier():
    """The dossier of the consumption stage's file with its source, as the
    command prints it."""
    return "\n".join(dossier(ROOT / CORPUS["cons"], with_source=True)) + "\n"


@pytest.fixture
def printed_refusal_catalogue():
    """The catalogue of refusals, as the command prints it."""
    return str(catalogue()) + "\n"


@pytest.fixture(scope="module")
def both_dossiers(read_only_stage_from_file):
    """`both_dossiers(path)`: the full and the compact dossier of the stage of
    the stage file at `path`, each a list of numbered lines, made once for
    each file."""

    @functools.cache
    def make(path):
        stage = read_only_stage_from_file(path)
        return dossier_lines(stage, path), compact_dossier_lines(stage, path)

    return make


@pytest.fixture(scope="module")
def buffer_stock_dossiers(both_dossiers):
    """The texts of the lines of the full and of the compact dossier of the
    buffer-stock stage."""
    full, compact = both_dossiers(ROOT / BUFFER_STOCK_FILE)
    return line_texts(full), line_texts(compact)


@pytest.fixture
def period_files(tmp_path):
    """A folder that holds the stage file `disc.bl` of the portfolio-choice
    application under `stages/disc/` and two period files that name its
    stage: `once.yml`, which writes each key once, and `twice.yml`, which
    writes the key `connectors` twice."""
    (tmp_path / "stages" / "disc").mkdir(parents=True)
    shutil.copy(
        ROOT / "applications/portfolio-choice/declaration/stages/disc/disc.bl",
        tmp_path / "stages" / "disc" / "disc.bl",
    )
    (tmp_path / "once.yml").write_text("stages: [disc]\nconnectors: []\n", encoding="utf-8")
    (tmp_path / "twice.yml").write_text(
        "stages: [disc]\nconnectors: []\nconnectors: []\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def durables_with_moved_stage_files(tmp_path):
    """A copy of the folder `declaration/` of the durables application in
    which the stage folders stand under `stage_files/` in place of `stages/`,
    and the two recipes write the new paths."""
    folder = tmp_path / "declaration"
    shutil.copytree(DURABLES, folder)
    (folder / "stages").rename(folder / "stage_files")
    for recipe in ("spec.yml", "spec.two-stages.yml"):
        path = folder / recipe
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("stages/", "stage_files/"), encoding="utf-8")
    return folder


# each row runs `python -m bellman` once, in a new process that imports the
# package; the row that prints the public view is in the default set
@pytest.mark.parametrize("output", one_row_by_default(PRINTED, default="view"))
def test_the_command_prints_the_view_the_encoding_the_dossier_or_the_refusal_catalogue(
    request, command_answer, output
):
    """`python -m bellman` prints, with status zero and nothing on the error
    stream, the view, the encoding or the dossier of a stage file, or the
    catalogue of refusals, in a new interpreter that the test starts since
    the command is a program of its own."""
    arguments, printed = PRINTED[output]
    answer = command_answer(*arguments)
    assert answer.returncode == 0, answer.stderr
    assert not answer.stderr
    assert answer.stdout == request.getfixturevalue(printed)


@pytest.mark.parametrize(
    ("period", "ending"),
    [
        pytest.param("once.yml", "the stages the period names elaborate", id="each-key-once"),
        pytest.param(
            "twice.yml",
            "the period is refused under the rule trellis-file-shape",
            id="a-key-twice",
        ),
    ],
)
def test_the_period_line_of_the_dossier_refuses_a_period_file_only_where_it_writes_a_key_twice(
    period_files, period, ending
):
    """The period line of the dossier says that a period file that writes a
    key twice is refused, and that the same file with each key once
    elaborates."""
    # the package's one reader of YAML refuses a key written twice, which YAML
    # alone reads as its last value
    assert period_lines(period_files / period)[-1].endswith(ending)


@pytest.mark.parametrize(
    "period",
    [
        pytest.param("period.yml", id="the-period-of-tenure-and-the-two-consumption-stages"),
        pytest.param("period.two-stages.yml", id="the-period-of-the-two-consumption-stages"),
    ],
)
def test_the_dossier_reads_the_stage_files_of_a_period_at_the_paths_that_its_recipe_writes(
    durables_with_moved_stage_files, period
):
    """The period line of the dossier says that the stages of a period file of
    the durables application elaborate, where their files stand only at the
    paths that the recipe naming the period file writes."""
    folder = durables_with_moved_stage_files
    stage_files = [
        folder / "stage_files" / key / f"{key}.bl"
        for key in ("tenure", "keeper_cons", "adjuster_cons")
    ]
    # the stage files stand neither beside the period file nor in `stages/`
    assert all(path.is_file() and not (folder / path.name).exists() for path in stage_files)
    assert not (folder / "stages").exists()
    assert period_lines(folder / period)[-1].endswith("the stages the period names elaborate")


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_full_and_the_compact_dossier_number_their_lines_from_one_without_a_gap(
    both_dossiers, path
):
    """The full and the compact dossier of a stage number their lines from one,
    without a gap."""
    full, compact = both_dossiers(path)
    assert [number for number, _ in numbers_and_texts(full)] == list(range(1, len(full) + 1))
    assert [number for number, _ in numbers_and_texts(compact)] == list(range(1, len(compact) + 1))


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_compact_dossier_has_fewer_lines_than_the_full_one_and_under_half_its_characters(
    both_dossiers, path
):
    """The compact dossier of a stage has fewer lines than the full one, and
    less than half its characters."""
    full, compact = both_dossiers(path)
    assert len(compact) < len(full)
    assert len("\n".join(compact)) < len("\n".join(full)) / 2


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_compact_dossier_holds_no_line_of_rule_characters_alone_where_the_full_one_does(
    both_dossiers, path
):
    """The compact dossier of a stage holds no line drawn with rule characters
    alone, where the full one holds such lines."""
    full, compact = (line_texts(lines) for lines in both_dossiers(path))
    assert any(text.strip() and set(text.strip()) <= RULE_CHARACTERS for text in full)
    assert not any(text.strip() and set(text.strip()) <= RULE_CHARACTERS for text in compact)


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_compact_dossier_holds_the_sections_of_a_stage(both_dossiers, path):
    """The compact dossier of a stage holds the sections of the view, the
    fields, the definitions, the obligations, and the builders and the
    initial diagram in each direction."""
    compact = line_texts(both_dossiers(path)[1])
    headings = (
        "## stage",
        "## fields",
        "## definitions",
        "## obligations",
        "## builders, backward",
        "## initial diagram, backward",
        "## builders, forward",
        "## initial diagram, forward",
    )
    assert [heading for heading in headings if heading not in compact] == []


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_compact_dossier_prints_the_card_of_each_block_once(
    both_dossiers, read_only_stage_from_file, path
):
    """The compact dossier of a stage prints the card of each block of its two
    initial diagrams once."""
    stage, compact = read_only_stage_from_file(path), line_texts(both_dossiers(path)[1])
    blocks = [
        name
        for direction in ("backward", "forward")
        for name in getattr(stage.initial, direction).list()
    ]
    assert blocks
    assert [name for name in blocks if compact.count(f"### the block {name}") != 1] == []


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_compact_dossier_leaves_out_the_cards_of_the_builders_that_the_full_one_prints(
    both_dossiers, read_only_stage_from_file, path
):
    """The compact dossier of a stage prints neither the heading of the list of
    the primitives of a builder nor the title of the card of a primitive of a
    backward builder, which the full dossier prints."""
    stage = read_only_stage_from_file(path)
    full, compact = (line_texts(lines) for lines in both_dossiers(path))
    builder_card = f"STAGE {stage.name} / BACKWARD BUILDER"
    assert any(text.startswith("### the primitives of") for text in full)
    assert any(text.startswith(builder_card) for text in full)
    assert not any(text.startswith("### the primitives of") for text in compact)
    assert not any(text.startswith(builder_card) for text in compact)


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_every_condition_of_the_full_dossier_is_a_condition_of_the_compact_one(
    both_dossiers, path
):
    """Every condition that the full dossier of a stage prints is a condition
    of the compact one."""
    full, compact = (line_texts(lines) for lines in both_dossiers(path))
    full_keys = {condition_key(row) for row in condition_rows(full)}
    assert full_keys
    assert full_keys <= {condition_key(row) for row in condition_rows(compact)}


@pytest.mark.complete_set
@pytest.mark.parametrize("path", FILES_WITH_CONDITIONS_UNDER_BUILDERS, ids=stage_file_id)
def test_a_condition_printed_under_a_builders_graph_is_printed_once_and_under_no_definition(
    both_dossiers, path
):
    """A condition that the compact dossier of a stage prints under either of
    its builders graphs stands there once and under no definition."""
    compact = line_texts(both_dossiers(path)[1])
    definitions = compact[compact.index("## definitions") : compact.index("## builders, backward")]
    builders = compact[
        compact.index("## builders, backward") : compact.index("## initial diagram, backward")
    ]
    under_definitions = {condition_key(row) for row in condition_rows(definitions)}
    under_builders = Counter(condition_key(row) for row in condition_rows(builders))
    assert under_builders
    assert not (set(under_builders) & under_definitions)
    # the package holds each condition once at two places: the stage keeps one
    # condition where two have one term, and the compact dossier prints a
    # condition once under a builders graph however many of its primitives
    # state it; this count fails only where both are removed, and then in the
    # row of the Epstein-Zin savings stage
    assert all(count == 1 for count in under_builders.values())


@pytest.mark.parametrize("path", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_compact_dossier_hides_the_name_of_its_stage_before_a_colon_and_in_its_first_line(
    both_dossiers, read_only_stage_from_file, path
):
    """The compact dossier of a stage writes `stage` in place of the stage's
    name in its first line and where the name stands before a colon."""
    stage, compact = read_only_stage_from_file(path), line_texts(both_dossiers(path)[1])
    hidden = re.compile(rf"(?<![0-9A-Za-z_.]){re.escape(stage.name)}(?=:)")
    assert not any(hidden.search(text) for text in compact)
    assert compact[0] == "stage"


def test_the_full_dossier_prints_the_card_of_the_backward_initial_diagram_and_the_compact_none(
    buffer_stock_dossiers,
):
    """The full dossier of the buffer-stock stage prints the card of its
    backward initial diagram, which the compact one leaves out."""
    full, compact = buffer_stock_dossiers
    assert any(text.endswith("/ BACKWARD INITIAL DIAGRAM") for text in full)
    assert not any(text.endswith("/ BACKWARD INITIAL DIAGRAM") for text in compact)


def test_the_compact_dossier_prints_the_table_of_fields_that_the_full_one_leaves_out(
    buffer_stock_dossiers,
):
    """The compact dossier of the buffer-stock stage prints the section of its
    fields, which the full one leaves out."""
    full, compact = buffer_stock_dossiers
    assert "## fields" not in full and "## fields" in compact


def test_the_compact_dossier_prints_the_value_line_of_the_buffer_stock_stage_under_its_address(
    buffer_stock_dossiers,
):
    """The compact dossier of the buffer-stock stage prints the line of its
    block `cntn_to_dcsn` under the address `cntn_to_dcsn.value`."""
    _, compact = buffer_stock_dossiers
    source = [text for text in compact if text.startswith("  cntn_to_dcsn.value")]
    assert source and all("𝑢(c) + β*V[>]" in text for text in source)


def test_the_full_and_the_compact_dossier_hide_the_name_of_the_buffer_stock_stage_before_a_colon(
    buffer_stock_dossiers,
):
    """Neither the full nor the compact dossier of the buffer-stock stage
    writes the stage's name before a colon."""
    full, compact = buffer_stock_dossiers
    # each form hides the name where it begins an identity, such as
    # `stage:dcsn:m`; the titles of the cards still print it
    assert not any("buffer_stock:" in text for text in full + compact)


# each row runs `python -m bellman` once, in a new process that imports the
# package; the row without an output option is in the default set
@pytest.mark.parametrize("output", one_row_by_default(OUTPUT_OPTIONS))
def test_the_command_prints_the_refusal_that_elaboration_gives_a_text_that_does_not_parse(
    tmp_path, output
):
    """`python -m bellman` answers a stage file that the parser cannot read,
    with each output option, with status one and the text of the refusal
    that elaboration raises, in a new interpreter that the test starts since
    the command is a program of its own."""
    refused_path = tmp_path / "refused.bl"
    refused_text = example_text(EXAMPLES["syntax"])
    refused_path.write_text(refused_text, encoding="utf-8")
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(refused_text, origin=str(refused_path))
    answer = run_command(str(refused_path), *OUTPUT_OPTIONS[output])
    assert answer.returncode == 1
    assert not answer.stderr
    assert answer.stdout == str(refused.value) + "\n"
    # the refusal is the parser's: its rule, the caret under the place of the
    # fault, and the two tokens that the parser expected there
    phrases = ("rule syntax", "^", "`)`", "`,`")
    assert [phrase for phrase in phrases if phrase not in answer.stdout] == []


# each row runs `python -m bellman` once, on a missing file or on a folder,
# with one output option; the missing file without an output option is in
# the default set
@pytest.mark.parametrize(
    "case",
    one_row_by_default(
        (place, output) for place in ("missing", "folder") for output in OUTPUT_OPTIONS
    ),
    ids="-".join,
)
def test_the_command_refuses_an_unreadable_path_in_four_lines_where_what_why_and_write(
    tmp_path, case
):
    """`python -m bellman` refuses a missing file or a folder, with each output
    option, with status one and four lines, `where`, `what`, `why` and
    `write`, that name the path and ask for a readable stage file, in a new
    interpreter that the test starts since the command is a program of its
    own."""
    place, output = case
    unreadable = {"missing": tmp_path / "missing.bl", "folder": tmp_path}[place]
    answer = run_command(str(unreadable), *OUTPUT_OPTIONS[output])
    assert answer.returncode == 1 and not answer.stderr
    lines = answer.stdout.splitlines()
    assert [line.split()[0] for line in lines] == ["where", "what", "why", "write"]
    assert str(unreadable) in lines[0] and "readable .bl file" in lines[-1]


# each row runs `python -m bellman` once; the row with no argument is in the
# default set
@pytest.mark.parametrize("invalid", one_row_by_default(INVALID_ARGUMENTS))
def test_the_command_refuses_invalid_arguments_with_its_usage_line(invalid):
    """`python -m bellman` refuses a list of arguments that it does not admit
    with status two, nothing on the output stream and its usage line on the
    error stream, in a new interpreter that the test starts since the
    command is a program of its own."""
    answer = run_command(*INVALID_ARGUMENTS[invalid])
    assert answer.returncode == 2
    assert not answer.stdout
    assert answer.stderr.startswith("usage:")
