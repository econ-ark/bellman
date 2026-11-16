"""The entries of a model's YAML files as text: find, read, replace, append,
insert, split and remove one entry, every other character of the file kept."""

import sys
import time

import pytest
from application_files import CONS_PORT, PENSION
from trellises import TWO_PERIOD_TRELLIS_TEXT

from bellman.trellis import (
    append_to_mapping,
    append_to_sequence,
    entry_span,
    entry_value,
    insert_in_sequence,
    remove_from_mapping,
    remove_from_sequence,
    replace_entry,
    split_entry,
)

# the slot `$fill` of the calibration of the pension model's worker stage
WORKER_SLOT = "stages.worker_saving.calibration.all[0]"

# a float written in base 60 with 175 parts, whose constructor multiplies its
# first part by 60**174, more than a float holds
BASE_60_FLOAT = "1" + ":0" * 174 + "."

# the calibration, the settings and the methods of a stage in one text
BINDINGS = (
    "calibration:\n"
    "  R: 1.045  # the gross return\n"
    '  β: "0.95"\n'
    "settings:\n"
    "  n_a: 300\n"
    "  tol: 0.001\n"
    "  verbose: false\n"
    "methods:\n"
    "  - on: cntn_to_dcsn.value\n"
    "    method: !Linear\n"
)

# two block mappings, each followed by a comment line
STAGE_SOURCES = (
    "worker:\n"
    "  calibration: calibration/worker.yml\n"
    "  methods: methods/worker.yml\n"
    "# the retiree's sources\n"
    "retiree:\n"
    "  calibration: calibration/retiree.yml\n"
    "# no methods file is written yet\n"
)

# a list written at its key's indentation, and a text after "|" followed by
# a blank line, each followed by a comment line
STAGES_AND_LABEL = (
    "stages:\n- worker\n- retiree\n# the stages\nlabel: |\n  the pension model\n\n# the label\n"
)

# a block mapping whose last entry is a text after "|", which ends before its
# line breaks, and a key after the mapping
NOTED = "stages:\n  a: 1\n  note: |\n    a note\nregistry: 2\n"


# a list of stages in block style with a comment after its first item and a
# comment line above its last
BLOCK_STAGES = (
    "!period\nname: p\nstages:\n  - a  # the first\n  - b\n  # before c\n  - c\n"
    "connectors:\n  - {}\n"
)

# the same list with a comment line above its first item as well
COMMENTED_STAGES = (
    "!period\nname: p\nstages:\n  # the list\n  - a  # the first\n  - b\n  # before c\n"
    "  - c\nconnectors:\n  - {}\n"
)

# a list nested in an item of a list, whose dashes follow another dash
NESTED_LIST = "stages:\n  - - a\n    - b\n"

# a list of stages in flow style with a comment after it
FLOW_STAGES = "stages: [a, b, c]  # three\n"

# a trellis file whose one period entry, written in flow style, repeats six
# times
FLOW_ENTRY = (
    "!trellis\nperiods:\n  - {template: period.yml, repeat: 6}\ninter_connectors:\n  - {a: k}\n"
)

# a mapping in block style with a comment after its first key and a comment
# line above its second
FIELDS = "fields:\n  a: k  # the first\n  # the second\n  m_next: m\n  h: h\nname: p\n"

# a mapping in block style that begins on the dash of a list
ON_DASH = "inter_connectors:\n  - a: k  # a\n    m_next: m\n"

# a mapping in flow style on one line with a comment after it
FLOW_FIELDS = "inter_connectors:\n  - {a: k, m_next: m, h: h}  # three\n"


@pytest.fixture(scope="module")
def pension_recipe():
    """The text of the pension model's recipe, `spec.yml`."""
    return (PENSION / "spec.yml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pension_period():
    """The text of the pension model's period file."""
    return (PENSION / "period.yml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def port_cons_trellis():
    """The text of cons-port's trellis file `trellis.port-cons.yml`."""
    return (CONS_PORT / "trellis.port-cons.yml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def port_cons_records():
    """The text of cons-port's trellis file of records, whose one period
    entry is written in block style."""
    return (CONS_PORT / "trellis.port-cons-vfi.yml").read_text(encoding="utf-8")


def nested_text(depth):
    """A flow mapping nested `depth` levels deep, `{a: {a: ... 1}}`."""
    return "{a: " * depth + "1" + "}" * depth


def shared_levels(count):
    """A list of `count` lists, the first of ten ones and each other of ten
    copies of the list before it, as the reader builds a list whose levels
    are read through aliases, its text growing tenfold with each level."""
    nested = [[1] * 10]
    while len(nested) < count:
        nested.append([nested[-1]] * 10)
    return nested


@pytest.mark.parametrize(
    ("fixture", "address", "value"),
    [
        pytest.param("pension_recipe", WORKER_SLOT, "$fill", id="a-slot-of-the-recipe"),
        pytest.param(
            "pension_trellis_text",
            "periods[1]",
            {"template": "period.yml", "repeat": 14},
            id="a-period-entry-of-the-trellis-file",
        ),
    ],
)
def test_entry_value_reads_the_value_at_an_address_as_written(request, fixture, address, value):
    """`entry_value` reads the value at an address of a file of the pension
    model as the file writes it."""
    assert entry_value(request.getfixturevalue(fixture), address) == value


def test_entry_value_reads_the_tag_of_a_document_under_the_key_yaml_tag(pension_trellis_text):
    """`entry_value` reads the tag `!trellis` of the pension model's trellis
    file under the key `__yaml_tag__` of the document."""
    assert entry_value(pension_trellis_text)["__yaml_tag__"] == "trellis"


# the reader's constructors raise KeyError, IndexError, AttributeError,
# TypeError and OverflowError for the last five texts
@pytest.mark.parametrize(
    "text",
    [
        pytest.param("a: [1, 2", id="an-unclosed-flow-list"),
        pytest.param("!!bool abc", id="a-boolean-tag-on-a-word"),
        pytest.param("!!int ''", id="an-integer-tag-on-an-empty-string"),
        pytest.param("!!timestamp abc", id="a-timestamp-tag-on-a-word"),
        pytest.param("!!set [1]", id="a-set-tag-on-a-list"),
        pytest.param(BASE_60_FLOAT, id="a-float-in-base-60-too-large-to-hold"),
    ],
)
def test_entry_value_refuses_a_text_that_does_not_read_as_yaml(text):
    """`entry_value` refuses with a ValueError a text that does not read as
    YAML, among them a text with a value that its tag cannot build."""
    with pytest.raises(ValueError, match="^the text does not read as YAML"):
        entry_value(text)


@pytest.mark.parametrize(
    ("read", "address"),
    [
        pytest.param(entry_value, (), id="entry_value"),
        pytest.param(entry_span, "a", id="entry_span"),
    ],
)
def test_a_text_nested_deeper_than_the_reader_can_follow_does_not_read(read, address):
    """`entry_value` and `entry_span` refuse with a ValueError a text nested as
    many levels deep as the interpreter's recursion limit, which the YAML
    reader cannot follow, since it calls itself at least once for each
    level."""
    with pytest.raises(ValueError, match="^the text does not read as YAML"):
        read(nested_text(sys.getrecursionlimit()), address)


def test_entry_span_gives_the_line_and_the_columns_of_a_value(pension_recipe):
    """`entry_span` gives the line and the columns between which the pension
    recipe writes the slot `$fill`, the value ending on the line where it
    begins."""
    span = entry_span(pension_recipe, WORKER_SLOT)
    line = pension_recipe.split("\n")[span.line - 1]
    assert span.end_line == span.line and line[span.column - 1 : span.end_column - 1] == "$fill"


# line 20 of the pension model's trellis file writes the first connector of
# the terminal period, `- {y_f_wk: y_f_T, ...}`, and line 31 the inter-period
# mapping, `- {y_f_wk: y_f_w, ...}`
@pytest.mark.parametrize(
    ("address", "line"),
    [
        pytest.param("periods[0].connectors[0]", 20, id="a-connector-of-the-terminal-period"),
        pytest.param("inter_connectors[0]", 31, id="the-inter-period-mapping"),
    ],
)
def test_entry_span_gives_the_line_of_a_connector_of_the_pension_trellis(
    pension_trellis_text, address, line
):
    """`entry_span` gives the line at which the pension model's trellis file
    writes a connector."""
    assert entry_span(pension_trellis_text, address).line == line


# a span is (line, column, end line, end column), each counted from one, the
# end standing just after the value's last character
@pytest.mark.parametrize(
    ("text", "address", "span"),
    [
        pytest.param(STAGE_SOURCES, "worker", (2, 3, 3, 30), id="a-mapping-before-a-comment-line"),
        pytest.param(STAGE_SOURCES, "retiree", (6, 3, 6, 39), id="the-last-mapping-of-the-file"),
        pytest.param(
            STAGES_AND_LABEL, "stages", (2, 1, 3, 10), id="a-list-at-its-keys-indentation"
        ),
        pytest.param(
            STAGES_AND_LABEL, "label", (5, 8, 6, 20), id="a-text-after-a-bar-and-a-blank-line"
        ),
    ],
)
def test_entry_span_ends_a_block_style_value_at_its_last_character(text, address, span):
    """`entry_span` ends a value written in block style at its last character,
    before the line breaks, the comment line or the key that follow it."""
    assert entry_span(text, address) == span


def test_entry_span_refuses_an_address_that_the_text_does_not_hold(pension_trellis_text):
    """`entry_span` refuses with a KeyError an address that the pension
    model's trellis file does not hold."""
    with pytest.raises(KeyError):
        entry_span(pension_trellis_text, "periods[0].nothing")


def test_a_string_written_over_a_slot_of_the_recipe_changes_that_slot_alone_and_reads_back(
    pension_recipe,
):
    """`replace_entry` writes a string over the slot `$fill` of the pension
    recipe on that slot's line and columns alone, so that the string reads
    back and the retiree's slot still reads `$fill`."""
    span = entry_span(pension_recipe, WORKER_SLOT)
    line = pension_recipe.split("\n")[span.line - 1]
    written = replace_entry(pension_recipe, WORKER_SLOT, "calibration/worker")
    before, after = pension_recipe.split("\n"), written.split("\n")
    assert len(before) == len(after)
    assert [n for n, (old, new) in enumerate(zip(before, after)) if old != new] == [span.line - 1]
    assert after[span.line - 1] == (
        line[: span.column - 1] + "calibration/worker" + line[span.end_column - 1 :]
    )
    assert entry_value(written, WORKER_SLOT) == "calibration/worker"
    assert entry_value(written, "stages.retiree_saving.calibration.all[0]") == "$fill"


@pytest.mark.parametrize(
    ("address", "string"),
    [
        pytest.param("stages.worker_saving.methods.all[0]", "null", id="null"),
        pytest.param(WORKER_SLOT, "!!timestamp abc", id="a-tagged-value-its-tag-cannot-build"),
        pytest.param(WORKER_SLOT, BASE_60_FLOAT, id="a-float-too-large-to-hold"),
    ],
)
def test_a_string_that_would_read_otherwise_is_written_in_double_quotes_and_reads_back(
    pension_recipe, address, string
):
    """`replace_entry` writes in double quotes a string whose plain form would
    read as another value or would not read, and the string reads back."""
    written = replace_entry(pension_recipe, address, string)
    assert entry_value(written, address) == string and f'"{string}"' in written


def test_a_deeply_nested_string_is_written_in_double_quotes_and_reads_back():
    """`replace_entry` writes in double quotes a string whose plain form is
    nested deeper than the reader can follow, the comment after the value
    kept, and the string reads back."""
    text = "settings:\n  upper_envelope: FUES  # the method\n"
    deep = nested_text(sys.getrecursionlimit())
    written = replace_entry(text, "settings.upper_envelope", deep)
    assert written == text.replace("FUES", f'"{deep}"')
    assert entry_value(written, "settings.upper_envelope") == deep


def test_replace_entry_judges_values_that_merge_mappings_through_aliases_within_one_second():
    """`replace_entry` writes in double quotes a string whose plain form merges
    10**8 entries through aliases, and refuses a tag whose value would write
    such mappings, the five calls taking less than one second together."""
    # seven levels of ten aliases: read as YAML, the flow mapping `merged`
    # merges 10**8 entries, which take a reader that builds them some 15
    # seconds and 2 GB of memory
    levels = ["l0: &l0 {" + ", ".join(f"k{i}: {i}" for i in range(10)) + "}"]
    levels += [f"l{k}: &l{k} {{<<: [" + ", ".join([f"*l{k - 1}"] * 10) + "]}" for k in range(1, 8)]
    merged = "{" + ", ".join(levels) + "}"
    text = "settings:\n  upper_envelope: FUES  # the method\n  outer: !egm\n"
    started = time.perf_counter()
    written = replace_entry(text, "settings.upper_envelope", merged)
    assert written == text.replace("FUES", f'"{merged}"')
    assert entry_value(written, "settings.upper_envelope") == merged
    with pytest.raises(ValueError, match="cannot be written as a tag at 'settings.outer'$"):
        replace_entry(text, "settings.outer", {"__yaml_tag__": "egm", "value": merged})
    # the levels written after a line break, as keys of the document
    beside = {"__yaml_tag__": "egm", "value": "x\n" + "\n".join(levels)}
    with pytest.raises(ValueError, match="cannot be written as a tag at 'settings.outer'$"):
        replace_entry(text, "settings.outer", beside)
    # the levels written after a comma of a flow mapping, as keys beside the
    # entry
    flow = "settings: {upper_envelope: FUES, outer: !egm grid}\n"
    beside = {"__yaml_tag__": "egm", "value": "x, " + ", ".join(levels)}
    with pytest.raises(ValueError, match="cannot be written as a tag at 'settings.outer'$"):
        replace_entry(flow, "settings.outer", beside)
    assert time.perf_counter() - started < 1.0


@pytest.mark.parametrize(
    ("text", "address", "string", "replaced", "read", "value"),
    [
        pytest.param(
            STAGE_SOURCES,
            "retiree",
            "sources/retiree.yml",
            "calibration: calibration/retiree.yml",
            "retiree",
            "sources/retiree.yml",
            id="the-last-entry-of-the-file",
        ),
        pytest.param(
            STAGE_SOURCES,
            "worker",
            "sources/worker.yml",
            "calibration: calibration/worker.yml\n  methods: methods/worker.yml",
            # the empty address reads the whole document
            "",
            {
                "worker": "sources/worker.yml",
                "retiree": {"calibration": "calibration/retiree.yml"},
            },
            id="an-entry-in-mid-file",
        ),
        pytest.param(
            STAGES_AND_LABEL,
            "label",
            "pension",
            "|\n  the pension model",
            "label",
            "pension",
            id="a-text-after-a-bar",
        ),
    ],
)
def test_a_string_over_a_block_style_value_keeps_the_comment_after_it_and_reads_back(
    text, address, string, replaced, read, value
):
    """`replace_entry` writes a string over the characters of a value written
    in block style alone, the comment, the line break and the key after them
    kept, and the text reads back with the string."""
    written = replace_entry(text, address, string)
    assert written == text.replace(replaced, string)
    assert entry_value(written, read) == value


# the rows of the next test: a text, an address, a string and the text that
# `replace_entry` answers
STRING_REPLACEMENTS = [
    pytest.param(
        "trellis: 't.yml'  # quoted\n",
        "trellis",
        "u.yml",
        "trellis: 'u.yml'  # quoted\n",
        id="single-quotes-and-a-comment-kept",
    ),
    pytest.param(
        "trellis: 't.yml'  # quoted\n",
        "trellis",
        "it's.yml",
        "trellis: 'it''s.yml'  # quoted\n",
        id="a-quote-within-single-quotes-doubled",
    ),
    pytest.param(
        'a: "x"\r\nb: 1\r\n',
        "a",
        "y",
        'a: "y"\r\nb: 1\r\n',
        id="double-quotes-and-carriage-returns-kept",
    ),
    pytest.param(
        "trellis: t.yml\n",
        "trellis",
        "2026",
        'trellis: "2026"\n',
        id="a-number-in-double-quotes",
    ),
    pytest.param(
        "trellis: 't.yml'\n",
        "trellis",
        "2026",
        "trellis: '2026'\n",
        id="a-number-within-single-quotes",
    ),
    pytest.param(
        "trellis: t\n  u.yml\nstages: {}\n",
        "trellis",
        "v.yml",
        "trellis: v.yml\nstages: {}\n",
        id="a-plain-value-of-two-lines-replaced-whole",
    ),
    pytest.param(
        "a: {}\nb: 1\n", "a", "x.yml", "a: x.yml\nb: 1\n", id="a-flow-mapping-replaced-whole"
    ),
    pytest.param(
        'trellis: "t\\u0041.yml"\n',
        "trellis",
        "v.yml",
        'trellis: "v.yml"\n',
        id="an-escape-written-anew-within-double-quotes",
    ),
    pytest.param(
        "trellis: !path t.yml\n",
        "trellis",
        "v.yml",
        "trellis: v.yml\n",
        id="a-tagged-value-replaced-without-its-tag",
    ),
]


@pytest.mark.parametrize(
    ("text", "address", "string", "expected"),
    STRING_REPLACEMENTS,
)
def test_replace_entry_writes_a_string_in_the_layout_of_the_value_it_replaces(
    text, address, string, expected
):
    """`replace_entry` writes a string over a value in the layout of that
    value: within its quotes, with its line ends, in double quotes where the
    plain form would read as a number, and plain over a value that it
    replaces whole."""
    assert replace_entry(text, address, string) == expected


@pytest.mark.parametrize(
    ("fixture", "address", "string", "old", "new"),
    [
        pytest.param(
            "pension_recipe",
            "trellis",
            "trellis.x.yml",
            "trellis: trellis.yml\n",
            "trellis: trellis.x.yml\n",
            id="the-trellis-file-of-the-recipe",
        ),
        pytest.param(
            "pension_trellis_text",
            "periods[1].template",
            "period.x.yml",
            "{template: period.yml,",
            "{template: period.x.yml,",
            id="the-template-of-a-flow-style-entry",
        ),
    ],
)
def test_replace_entry_changes_one_value_of_a_file_of_the_pension_model_alone(
    request, fixture, address, string, old, new
):
    """`replace_entry` writes a string over one value of a file of the pension
    model and keeps every other character of the file."""
    text = request.getfixturevalue(fixture)
    assert replace_entry(text, address, string) == text.replace(old, new)


def test_replace_entry_writes_a_string_in_place_of_a_whole_block_mapping(pension_recipe):
    """`replace_entry` writes a string in place of the block mapping `stages`
    of the pension recipe, from its first key to the end of its last entry,
    the comments before it and the line end after it kept."""
    assert replace_entry(pension_recipe, "stages", "x") == (
        pension_recipe[: pension_recipe.index("worker_saving:  {")] + "x\n"
    )


@pytest.mark.parametrize(
    ("text", "address", "value", "refusal"),
    [
        pytest.param(
            "trellis: &t t.yml\nother: *t\n",
            "trellis",
            "v.yml",
            "cannot be written as a string at 'trellis'",
            id="a-string",
        ),
        pytest.param(
            "a: &x 1\nb: *x\n", "a", 2, "cannot be written as a number at 'a'", id="a-number"
        ),
    ],
)
def test_replace_entry_refuses_to_write_over_a_value_that_an_alias_reads(
    text, address, value, refusal
):
    """`replace_entry` refuses with a ValueError to write over a value marked
    with an anchor that an alias reads, since the text would not read back
    with that value alone replaced."""
    with pytest.raises(ValueError, match=refusal):
        replace_entry(text, address, value)


def test_replace_entry_refuses_an_address_that_the_text_does_not_hold(pension_recipe):
    """`replace_entry` refuses with a KeyError an address that the pension
    recipe does not hold."""
    with pytest.raises(KeyError, match="no key 'registry'"):
        replace_entry(pension_recipe, "registry", "x")


@pytest.mark.parametrize(
    ("address", "value", "old", "new"),
    [
        pytest.param("calibration.R", 1.05, "R: 1.045", "R: 1.05", id="a-number-its-comment-kept"),
        pytest.param(
            "calibration.β", 0.95, 'β: "0.95"', "β: 0.95", id="a-number-over-a-quoted-value"
        ),
        pytest.param("settings.n_a", 400, "n_a: 300", "n_a: 400", id="an-integer"),
        pytest.param(
            "settings.tol", 1e-05, "tol: 0.001", "tol: 1.0e-05", id="a-float-as-yaml-writes-it"
        ),
        pytest.param("settings.verbose", True, "false", "true", id="a-boolean"),
        pytest.param(
            "methods[0].method",
            {"__yaml_tag__": "pchip", "value": ""},
            "!Linear",
            "!pchip",
            id="a-tag-over-a-tag",
        ),
        pytest.param(
            "methods[0].method",
            {"__yaml_tag__": "path", "value": "grid.yml"},
            "!Linear",
            "!path grid.yml",
            id="a-tag-with-a-value-after-one-space",
        ),
    ],
)
def test_replace_entry_writes_a_number_a_boolean_or_a_tag_plain_and_it_reads_back(
    address, value, old, new
):
    """`replace_entry` writes a number, a boolean or a tag, given as
    `entry_value` reads it, plain over a value, and it reads back as given."""
    written = replace_entry(BINDINGS, address, value)
    assert written == BINDINGS.replace(old, new)
    assert entry_value(written, address) == value


@pytest.mark.parametrize(
    ("value", "kind"),
    [
        pytest.param([1.05], "a list", id="a-list"),
        pytest.param(shared_levels(6), "a list", id="a-list-of-six-levels-of-shared-lists"),
        pytest.param({"a": 1}, "a mapping", id="a-mapping"),
        pytest.param(
            {"__yaml_tag__": "egm", "value": [[1]]},
            "a tag on a collection",
            id="a-tag-on-a-list",
        ),
    ],
)
def test_replace_entry_refuses_a_collection_with_a_message_that_names_its_kind(value, kind):
    """`replace_entry` refuses a list, a mapping or a tag on a list with a
    ValueError that names the value's kind and not its text."""
    with pytest.raises(ValueError) as refused:
        replace_entry(BINDINGS, "calibration.R", value)
    assert str(refused.value) == (
        f"{kind} is no string, int, float, boolean or tag, and cannot be written at "
        "'calibration.R'"
    )


@pytest.mark.parametrize(
    ("fixture", "append", "address", "entry", "last", "new"),
    [
        pytest.param(
            "pension_recipe",
            append_to_mapping,
            ("stages",),
            ("x", "{methods: {all: [stages/x/methods.bl]}}"),
            # the line of the recipe that writes its terminal stage
            "  terminal:       {stage: stages/terminal/terminal.bl,             "
            "methods: {all: [stages/terminal/methods.bl]}, periods: [0, 0]}",
            "  x: {methods: {all: [stages/x/methods.bl]}}",
            id="a-stage-of-the-recipe",
        ),
        pytest.param(
            "pension_period",
            append_to_sequence,
            ("stages",),
            ("x",),
            "  - retiree_saving",
            "  - x",
            id="a-stage-of-the-period-file",
        ),
        pytest.param(
            "pension_trellis_text",
            append_to_sequence,
            ("periods",),
            ("{template: p.yml, repeat: 1}",),
            "  - {template: period.yml, repeat: 14}",
            "  - {template: p.yml, repeat: 1}",
            id="a-period-of-the-trellis-file",
        ),
    ],
)
def test_an_entry_appended_to_a_file_of_the_pension_model_follows_the_last_entry(
    request, fixture, append, address, entry, last, new
):
    """`append_to_mapping` and `append_to_sequence` write an entry on a line
    of its own after the last entry of a collection of a file of the pension
    model, every other line kept."""
    text = request.getfixturevalue(fixture)
    old = text.split("\n")
    at = old.index(last) + 1
    assert append(text, address, *entry).split("\n") == old[:at] + [new] + old[at:]


@pytest.mark.parametrize(
    ("text", "append", "address", "entry", "expected"),
    [
        pytest.param(
            "connectors: []\n",
            append_to_sequence,
            "connectors",
            ("{m_next: m}",),
            "connectors: [{m_next: m}]\n",
            id="an-empty-flow-list",
        ),
        pytest.param(
            "stages: [a, b]  # two\n",
            append_to_sequence,
            "stages",
            ("c",),
            "stages: [a, b, c]  # two\n",
            id="a-flow-list-and-its-comment",
        ),
        pytest.param(
            "stages: {a: 1}\n",
            append_to_mapping,
            "stages",
            ("b", "2"),
            "stages: {a: 1, b: 2}\n",
            id="a-flow-mapping",
        ),
        pytest.param(
            NOTED,
            append_to_mapping,
            "stages",
            ("b", "2"),
            NOTED.replace("a note\n", "a note\n  b: 2\n"),
            id="a-block-mapping-whose-last-entry-is-a-text-after-a-bar",
        ),
    ],
)
def test_an_appended_entry_stands_at_the_end_of_its_collection(
    text, append, address, entry, expected
):
    """`append_to_sequence` and `append_to_mapping` write an entry before the
    closing bracket or brace of a collection in flow style, after a comma
    where the collection holds an entry, and on the line after the last line
    of a block mapping."""
    assert append(text, address, *entry) == expected


def test_an_appended_item_ends_its_line_as_the_text_does_and_the_list_reads_back():
    """An item appended to a list of a period file whose lines end with a
    carriage return and a line feed ends its line the same way, and the list
    reads back with the item."""
    period_text = "!period\r\nname: p\r\nstages:\r\n  - a\r\n  - b\r\nconnectors:\r\n  - {}\r\n"
    new = append_to_sequence(period_text, "stages", "c")
    assert new == period_text.replace("  - b\r\n", "  - b\r\n  - c\r\n")
    assert entry_value(new, "stages") == ["a", "b", "c"]


def test_a_key_appended_to_a_tagged_trellis_file_reads_back_with_the_tag():
    """A key appended to the document of a trellis file stands after its last
    line, and the document reads back with its tag `!trellis`."""
    new = append_to_mapping(TWO_PERIOD_TRELLIS_TEXT, (), "inter_connectors", "[{a: k}]")
    assert new == TWO_PERIOD_TRELLIS_TEXT + "inter_connectors: [{a: k}]\n"
    assert entry_value(new) == {
        "__yaml_tag__": "trellis",
        "periods": [{"stages": ["worker"]}, {"stages": ["worker"]}],
        "inter_connectors": [{"a": "k"}],
    }


def test_an_item_appended_after_a_list_of_tagged_entries_keeps_their_tags():
    """An item appended to a list of tagged entries stands after the list's
    last entry, before the comment lines that close the file, and the list
    reads back with each tag of its entries."""
    # three tagged entries, the tags with no value, followed by a blank line
    # and the comment lines that close the file
    tagged = (
        "name: tagged\n"
        "# three tagged entries\n"
        "entries:\n"
        "  - on: policy\n"
        "    method: !egm\n"
        "    settings: {grid: !Cartesian, orders: {a: n_a}, bounds: {a: [a_min, a_max]}}\n"
        "  - on: cntn_to_dcsn\n"
        "    method: !vfi\n"
        "  - on: cntn_to_dcsn.evaluate\n"
        "    method: !Linear\n"
        "    settings: {grid: !Cartesian, orders: {m: n_m}, bounds: {m: [m_min, m_max]}}\n"
        "\n"
        "# the comment lines that close the file\n"
        "# stand after the list\n"
    )
    new = append_to_sequence(tagged, "entries", "{on: dcsn_to_cntn}")
    # the entry stands after the list's last entry, before the comment lines
    last = "    settings: {grid: !Cartesian, orders: {m: n_m}, bounds: {m: [m_min, m_max]}}\n"
    assert tagged.count(last) == 1
    assert new == tagged.replace(last, last + "  - {on: dcsn_to_cntn}\n")
    read = entry_value(new, "entries")
    assert read == [*entry_value(tagged, "entries"), {"on": "dcsn_to_cntn"}]
    assert [entry["method"]["__yaml_tag__"] for entry in read[:-1]] == ["egm", "vfi", "Linear"]


@pytest.mark.parametrize(
    ("fixture", "append", "address", "entry", "refusal", "match"),
    [
        pytest.param(
            "pension_recipe",
            append_to_mapping,
            ("stages",),
            ("worker_saving", "{}"),
            ValueError,
            "holds the key 'worker_saving'",
            id="a-key-that-the-mapping-holds",
        ),
        pytest.param(
            "pension_period",
            append_to_mapping,
            ("stages",),
            ("x", "1"),
            ValueError,
            "is no mapping",
            id="a-list-taken-for-a-mapping",
        ),
        pytest.param(
            "pension_recipe",
            append_to_sequence,
            ("registry",),
            ("x",),
            KeyError,
            "no key 'registry'",
            id="an-address-that-the-text-does-not-hold",
        ),
        pytest.param(
            "pension_recipe",
            append_to_sequence,
            ("stages",),
            ("x",),
            ValueError,
            "is no list",
            id="a-mapping-taken-for-a-list",
        ),
    ],
)
def test_an_entry_that_the_collection_at_the_address_cannot_take_is_refused(
    request, fixture, append, address, entry, refusal, match
):
    """`append_to_mapping` and `append_to_sequence` refuse a key that the
    mapping holds, a collection of the other kind and an address that the
    text does not hold."""
    with pytest.raises(refusal, match=match):
        append(request.getfixturevalue(fixture), address, *entry)


@pytest.mark.parametrize(
    ("text", "append", "entry"),
    [
        pytest.param(
            "stages:\n  a: 1\n  note: |+\n    a note\n\nregistry: 2\n",
            append_to_mapping,
            ("b", "2"),
            id="a-last-text-that-keeps-its-blank-line",
        ),
        pytest.param(
            "stages: [\n  a,\n  b,\n]\n",
            append_to_sequence,
            ("c",),
            id="a-flow-list-of-lines-with-a-trailing-comma",
        ),
        pytest.param(
            "defaults: &d\n  x: 1\nstages:\n  a: 1\n  b: *d\n",
            append_to_mapping,
            ("c", "3"),
            id="an-alias-as-the-last-entry",
        ),
    ],
)
def test_an_append_whose_result_does_not_read_back_as_the_entries_and_the_new_one_is_refused(
    text, append, entry
):
    """`append_to_mapping` and `append_to_sequence` refuse with a ValueError
    that names the address an append whose result does not read back as the
    former entries of the collection and then the new one."""
    with pytest.raises(ValueError, match="at stages cannot be extended as text"):
        append(text, ("stages",), *entry)


# the rows of the next test: a text, the address of a list, an index, an item
# and the text that `insert_in_sequence` answers
INSERTIONS = [
    pytest.param(
        BLOCK_STAGES,
        "stages",
        0,
        "x",
        BLOCK_STAGES.replace("  - a  #", "  - x\n  - a  #"),
        id="the-first-item-and-its-comment",
    ),
    pytest.param(
        BLOCK_STAGES,
        "stages",
        1,
        "x",
        BLOCK_STAGES.replace("  - b\n", "  - x\n  - b\n"),
        id="a-middle-item-of-a-block-list",
    ),
    pytest.param(
        BLOCK_STAGES,
        "stages",
        2,
        "x",
        BLOCK_STAGES.replace("  - c\n", "  - x\n  - c\n"),
        id="an-item-below-a-comment-line",
    ),
    pytest.param(
        BLOCK_STAGES.replace("\n", "\r\n"),
        "stages",
        1,
        "x",
        BLOCK_STAGES.replace("\n", "\r\n").replace("  - b\r\n", "  - x\r\n  - b\r\n"),
        id="lines-that-end-with-a-carriage-return",
    ),
    pytest.param(
        "stages:\n- a\n- b\n",
        "stages",
        1,
        "x",
        "stages:\n- a\n- x\n- b\n",
        id="a-list-at-its-keys-indentation",
    ),
    pytest.param(
        FLOW_STAGES,
        "stages",
        0,
        "x",
        "stages: [x, a, b, c]  # three\n",
        id="a-flow-list-first",
    ),
    pytest.param(
        FLOW_STAGES,
        "stages",
        2,
        "x",
        "stages: [a, b, x, c]  # three\n",
        id="a-flow-list-middle",
    ),
    pytest.param(
        FLOW_STAGES, "stages", 3, "x", "stages: [a, b, c, x]  # three\n", id="a-flow-list-end"
    ),
    pytest.param(
        "connectors: []\n",
        "connectors",
        0,
        "{m_next: m}",
        "connectors: [{m_next: m}]\n",
        id="an-empty-flow-list",
    ),
]


@pytest.mark.parametrize(
    ("text", "address", "index", "item", "expected"),
    INSERTIONS,
)
def test_insert_in_sequence_places_an_item_at_an_index_of_a_list(
    text, address, index, item, expected
):
    """`insert_in_sequence` places an item before the item at an index, on a
    line of its own in a block list and before that item in a flow list, or at
    the end where the index is the length of the list, every other character
    kept."""
    assert insert_in_sequence(text, address, index, item) == expected


def test_insert_in_sequence_at_the_length_of_a_block_list_appends_the_item():
    """`insert_in_sequence` at the length of a block list writes the text that
    `append_to_sequence` writes."""
    assert insert_in_sequence(BLOCK_STAGES, "stages", 3, "x") == append_to_sequence(
        BLOCK_STAGES, "stages", "x"
    )


def test_an_item_inserted_in_a_block_list_reads_back_at_its_index():
    """A list with an item inserted at index 1 reads back with the item in
    second place."""
    inserted = insert_in_sequence(BLOCK_STAGES, "stages", 1, "x")
    assert entry_value(inserted, "stages") == ["a", "x", "b", "c"]


def test_a_period_inserted_in_the_pension_trellis_stands_before_the_entry_at_its_index(
    pension_trellis_text,
):
    """A period entry inserted at index 1 of the pension model's trellis file
    stands on a line of its own before the second entry, every other line
    kept."""
    old = pension_trellis_text.split("\n")
    at = old.index("  - {template: period.yml, repeat: 14}")
    new = insert_in_sequence(
        pension_trellis_text, "periods", 1, "{template: period.new.yml, repeat: 1}"
    )
    assert new.split("\n") == old[:at] + ["  - {template: period.new.yml, repeat: 1}"] + old[at:]


# the rows of the next test: a text, an address, an index, an item, and the
# class and the start of the message of the refusal
REFUSED_INSERTIONS = [
    pytest.param(
        BLOCK_STAGES, "name", 0, "x", ValueError, "the entry name is no list", id="no-list"
    ),
    pytest.param(
        BLOCK_STAGES,
        "registry",
        0,
        "x",
        KeyError,
        "no key 'registry'",
        id="an-address-that-the-text-does-not-hold",
    ),
    *[
        pytest.param(
            BLOCK_STAGES,
            "stages",
            index,
            "x",
            ValueError,
            "lies outside the list stages of length 3",
            id=f"the-index-{index!r}",
        )
        for index in (-1, 4, 1.0, True)
    ],
    pytest.param(
        BLOCK_STAGES,
        "stages",
        1,
        "[x",
        ValueError,
        "does not read as YAML",
        id="an-item-that-does-not-read",
    ),
    pytest.param(
        NESTED_LIST,
        "stages[0]",
        0,
        "x",
        ValueError,
        r"at stages\[0\] cannot be extended as text",
        id="a-dash-after-another-dash",
    ),
    # alone, `x: 1, y` is one mapping; within a flow list, two items
    pytest.param(
        FLOW_STAGES,
        "stages",
        1,
        "x: 1, y",
        ValueError,
        "at stages cannot be extended as text",
        id="an-item-that-reads-otherwise-in-the-list",
    ),
]


@pytest.mark.parametrize(
    ("text", "address", "index", "item", "refusal", "match"),
    REFUSED_INSERTIONS,
)
def test_insert_in_sequence_refuses_an_item_that_it_cannot_place_as_text(
    text, address, index, item, refusal, match
):
    """`insert_in_sequence` refuses an address of no list or not in the text,
    an index that is no whole number within the list, and an item that does
    not read or that the list would read otherwise."""
    with pytest.raises(refusal, match=match):
        insert_in_sequence(text, address, index, item)


@pytest.mark.parametrize(
    ("text", "at", "expected"),
    [
        pytest.param(
            FLOW_ENTRY,
            3,
            FLOW_ENTRY.replace(
                "  - {template: period.yml, repeat: 6}\n",
                "  - {template: period.yml, repeat: 3}\n  - {template: period.yml, repeat: 3}\n",
            ),
            id="a-flow-entry-in-a-block-list",
        ),
        pytest.param(
            "periods: [{template: period.yml, repeat: 6}, {template: last.yml}]  # two\n",
            1,
            "periods: [{template: period.yml, repeat: 1}, {template: period.yml, repeat: 5}, "
            "{template: last.yml}]  # two\n",
            id="a-flow-entry-in-a-flow-list",
        ),
    ],
)
def test_split_entry_writes_a_repeated_entry_twice_with_two_repeats(text, at, expected):
    """`split_entry` writes the entry `periods[0]` twice in its place, the
    first with `repeat: at` and the second with the rest of its repeat, every
    other character kept."""
    assert split_entry(text, "periods[0]", at) == expected


def test_a_split_entry_reads_back_as_two_entries_whose_repeats_sum_to_its_own():
    """The entry `repeat: 6` split at 2 reads back as two entries of the same
    template with the repeats 2 and 4."""
    assert entry_value(split_entry(FLOW_ENTRY, "periods[0]", 2), "periods") == [
        {"template": "period.yml", "repeat": 2},
        {"template": "period.yml", "repeat": 4},
    ]


def test_a_split_block_style_entry_is_written_twice_with_all_its_lines_and_reads_back(
    port_cons_records,
):
    """The period entry of cons-port's trellis file of records, written in
    block style, is written twice with all its lines when split, and reads
    back as two copies with the repeats 2 and 4."""
    start = port_cons_records.index("  - stages:\n")
    end = port_cons_records.index("    repeat: 6\n") + len("    repeat: 6\n")
    entry = port_cons_records[start:end]
    new = split_entry(port_cons_records, "periods[0]", 2)
    assert new == (
        port_cons_records[:start]
        + entry.replace("repeat: 6", "repeat: 2")
        + entry.replace("repeat: 6", "repeat: 4")
        + port_cons_records[end:]
    )
    read = entry_value(port_cons_records, "periods[0]")
    assert entry_value(new, "periods") == [{**read, "repeat": 2}, {**read, "repeat": 4}]


def test_the_split_of_the_last_entry_of_the_pension_trellis_keeps_the_comment_lines_after_it(
    pension_trellis_text,
):
    """The last entry of the pension model's trellis file, followed by comment
    lines, is written twice when split, the comment lines after the second
    entry."""
    assert split_entry(pension_trellis_text, "periods[1]", 4) == pension_trellis_text.replace(
        "  - {template: period.yml, repeat: 14}\n",
        "  - {template: period.yml, repeat: 4}\n  - {template: period.yml, repeat: 10}\n",
    )


@pytest.mark.parametrize(
    ("text", "address", "at", "refusal"),
    [
        pytest.param(
            FLOW_ENTRY, "periods", 3, "the entry periods is no item of a list", id="no-item"
        ),
        pytest.param(
            FLOW_ENTRY,
            "periods[1]",
            3,
            r"index 1 lies outside the list periods of length 1",
            id="an-index-outside-the-list",
        ),
        pytest.param("name: p\n", "name[0]", 3, "the entry name is no list", id="a-scalar"),
        *[
            pytest.param(
                text, "periods[0]", 1, r"the entry periods\[0\] writes no integer repeat", id=name
            )
            for text, name in (
                ("periods:\n  - {template: period.yml}\n", "a-repeat-from-its-period-file"),
                ("periods:\n  - {template: period.yml, repeat: six}\n", "a-repeat-of-a-word"),
                ("periods:\n  - period.yml\n", "an-entry-that-is-a-string"),
            )
        ],
        *[
            pytest.param(
                FLOW_ENTRY,
                "periods[0]",
                at,
                r"writes repeat: 6, which cannot be split at",
                id=f"split-at-{at!r}",
            )
            for at in (0, 6, 7, 2.5)
        ],
        pytest.param(
            "periods:\n  - - {template: p.yml, repeat: 6}\n",
            "periods[0][0]",
            3,
            r"at periods\[0\] cannot be extended as text",
            id="a-dash-after-another-dash",
        ),
    ],
)
def test_split_entry_refuses_an_entry_that_it_cannot_split(text, address, at, refusal):
    """`split_entry` refuses with a ValueError an address that names no item
    of a list or an item outside it, an entry that writes no integer
    `repeat`, an `at` that is no whole number from one to the repeat less
    one, and a dash after another dash."""
    with pytest.raises(ValueError, match=refusal):
        split_entry(text, address, at)


# the rows of the next test: a text, the address of a list, an index and the
# text that `remove_from_sequence` answers
ITEM_REMOVALS = [
    pytest.param(
        COMMENTED_STAGES,
        "stages",
        0,
        COMMENTED_STAGES.replace("  - a  # the first\n", ""),
        id="the-first-item-the-comment-line-above-it-kept",
    ),
    pytest.param(
        COMMENTED_STAGES,
        "stages",
        1,
        COMMENTED_STAGES.replace("  - b\n", ""),
        id="a-middle-item",
    ),
    pytest.param(
        COMMENTED_STAGES,
        "stages",
        2,
        COMMENTED_STAGES.replace("  # before c\n  - c\n", ""),
        id="the-last-item-with-the-comment-line-above-it",
    ),
    pytest.param(
        COMMENTED_STAGES.replace("\n", "\r\n"),
        "stages",
        1,
        COMMENTED_STAGES.replace("\n", "\r\n").replace("  - b\r\n", ""),
        id="lines-that-end-with-a-carriage-return",
    ),
    pytest.param(
        "stages:\n- a\n- {from: port, to: cons,\n   fields: {m_next: m}}\n- b\n",
        "stages",
        1,
        "stages:\n- a\n- b\n",
        id="an-item-of-two-lines-at-its-keys-indentation",
    ),
    pytest.param(
        "stages:\n  - a\n  - b",
        "stages",
        1,
        "stages:\n  - a\n",
        id="the-last-line-of-a-text-with-no-line-break-at-its-end",
    ),
    pytest.param(FLOW_STAGES, "stages", 0, "stages: [b, c]  # three\n", id="a-flow-list-first"),
    pytest.param(FLOW_STAGES, "stages", 1, "stages: [a, c]  # three\n", id="a-flow-list-middle"),
    pytest.param(FLOW_STAGES, "stages", 2, "stages: [a, b]  # three\n", id="a-flow-list-end"),
    pytest.param(
        "connectors: [{m_next: m}]\n",
        "connectors",
        0,
        "connectors: []\n",
        id="the-only-item-of-a-flow-list",
    ),
    pytest.param(
        "connectors:\n  # one\n  - {m_next: m}  # the join\nrepeat: 6\n",
        "connectors",
        0,
        "connectors:\n  # one\n  []  # the join\nrepeat: 6\n",
        id="the-only-item-of-a-block-list-its-comments-kept",
    ),
]


@pytest.mark.parametrize(
    ("text", "address", "index", "expected"),
    ITEM_REMOVALS,
)
def test_remove_from_sequence_takes_the_item_at_an_index_out(text, address, index, expected):
    """`remove_from_sequence` takes out the lines of an item of a block list,
    with the comment line above an item after the first, or an item of a flow
    list with its comma, and writes `[]` for a list's only item."""
    assert remove_from_sequence(text, address, index) == expected


def test_an_item_removed_from_a_block_list_reads_back_without_it():
    """A list with its item at index 1 removed reads back without that
    item."""
    removed = remove_from_sequence(COMMENTED_STAGES, "stages", 1)
    assert entry_value(removed, "stages") == ["a", "c"]


def test_the_removal_of_the_one_connector_of_the_port_cons_trellis_leaves_an_empty_list(
    port_cons_trellis,
):
    """The one connector of the period of `trellis.port-cons.yml`, removed,
    leaves its list written `[]`, which reads back empty."""
    new = remove_from_sequence(port_cons_trellis, "periods[0].connectors", 0)
    assert new == port_cons_trellis.replace(
        "    connectors:\n      - {w: m}\n", "    connectors:\n      []\n"
    )
    assert entry_value(new, "periods[0].connectors") == []


@pytest.mark.parametrize(
    ("text", "address", "index", "refusal", "match"),
    [
        pytest.param(
            COMMENTED_STAGES, "name", 0, ValueError, "the entry name is no list", id="no-list"
        ),
        pytest.param(
            COMMENTED_STAGES,
            "registry",
            0,
            KeyError,
            "no key 'registry'",
            id="an-address-that-the-text-does-not-hold",
        ),
        *[
            pytest.param(
                COMMENTED_STAGES,
                "stages",
                index,
                ValueError,
                "the list stages of length 3 holds no item",
                id=f"the-index-{index!r}",
            )
            for index in (-1, 3, 1.0, True)
        ],
        pytest.param(
            NESTED_LIST,
            "stages[0]",
            0,
            ValueError,
            r"at stages\[0\] does not admit the removal as text",
            id="a-dash-after-another-dash",
        ),
    ],
)
def test_remove_from_sequence_refuses_an_item_that_it_cannot_take_out_as_text(
    text, address, index, refusal, match
):
    """`remove_from_sequence` refuses an address of no list or not in the
    text, an index that is no whole number within the list, and a dash after
    another dash."""
    with pytest.raises(refusal, match=match):
        remove_from_sequence(text, address, index)


# the rows of the next test: a text, the address of a mapping, a key and the
# text that `remove_from_mapping` answers
KEY_REMOVALS = [
    pytest.param(
        FIELDS, "fields", "a", FIELDS.replace("  a: k  # the first\n", ""), id="the-first-key"
    ),
    pytest.param(
        FIELDS,
        "fields",
        "m_next",
        FIELDS.replace("  # the second\n  m_next: m\n", ""),
        id="a-key-with-the-comment-line-above-it",
    ),
    pytest.param(FIELDS, "fields", "h", FIELDS.replace("  h: h\n", ""), id="the-last-key"),
    pytest.param(
        FIELDS.replace("\n", "\r\n"),
        "fields",
        "h",
        FIELDS.replace("\n", "\r\n").replace("  h: h\r\n", ""),
        id="lines-that-end-with-a-carriage-return",
    ),
    pytest.param(
        ON_DASH,
        "inter_connectors[0]",
        "a",
        "inter_connectors:\n  - m_next: m\n",
        id="the-first-key-on-a-dash-the-next-key-moved-there",
    ),
    pytest.param(
        ON_DASH,
        "inter_connectors[0]",
        "m_next",
        "inter_connectors:\n  - a: k  # a\n",
        id="the-second-key-of-a-mapping-on-a-dash",
    ),
    pytest.param(
        FLOW_FIELDS,
        "inter_connectors[0]",
        "a",
        FLOW_FIELDS.replace("a: k, ", ""),
        id="a-flow-mapping-first",
    ),
    pytest.param(
        FLOW_FIELDS,
        "inter_connectors[0]",
        "m_next",
        FLOW_FIELDS.replace("m_next: m, ", ""),
        id="a-flow-mapping-middle",
    ),
    pytest.param(
        FLOW_FIELDS,
        "inter_connectors[0]",
        "h",
        FLOW_FIELDS.replace(", h: h", ""),
        id="a-flow-mapping-last",
    ),
    pytest.param(
        "inter_connectors:\n  - {a: k, m_next: m,\n     h: h}\n",
        "inter_connectors[0]",
        "h",
        "inter_connectors:\n  - {a: k, m_next: m}\n",
        id="a-flow-mapping-across-two-lines",
    ),
    pytest.param(
        "connectors:\n  - {from: port, to: cons, fields: {m_next: m}}\n",
        "connectors[0].fields",
        "m_next",
        "connectors:\n  - {from: port, to: cons, fields: {}}\n",
        id="the-only-key-of-a-flow-mapping",
    ),
    pytest.param(
        "inter_connectors:\n  - a: k  # a\n",
        "inter_connectors[0]",
        "a",
        "inter_connectors:\n  - {}  # a\n",
        id="the-only-key-of-a-block-mapping",
    ),
]


@pytest.mark.parametrize(
    ("text", "address", "key", "expected"),
    KEY_REMOVALS,
)
def test_remove_from_mapping_takes_one_key_out_with_its_value(text, address, key, expected):
    """`remove_from_mapping` takes out a key with its value, the lines of the
    entry in block style with the comment line above a key after the first,
    the entry and its comma in flow style, and writes `{}` for a mapping's
    only key."""
    assert remove_from_mapping(text, address, key) == expected


def test_removing_the_one_key_of_the_port_cons_inter_period_mapping_leaves_the_mapping_in_its_list(
    port_cons_trellis,
):
    """The one key of the inter-period mapping of `trellis.port-cons.yml`,
    removed, leaves the mapping written `{}` in its list, which keeps its
    length."""
    new = remove_from_mapping(port_cons_trellis, "inter_connectors[0]", "disc.a")
    assert new == port_cons_trellis.replace(
        "inter_connectors:\n  - {disc.a: k}\n", "inter_connectors:\n  - {}\n"
    )
    assert entry_value(new, "inter_connectors") == [{}]


@pytest.mark.parametrize(
    ("text", "address", "key", "refusal", "match"),
    [
        pytest.param(
            FIELDS, "name", "a", ValueError, "the entry name is no mapping", id="no-mapping"
        ),
        pytest.param(
            FIELDS,
            "fields",
            "z",
            ValueError,
            "the mapping fields holds no key 'z'",
            id="a-key-that-the-mapping-does-not-hold",
        ),
        pytest.param(
            FIELDS,
            "registry",
            "a",
            KeyError,
            "no key 'registry'",
            id="an-address-that-the-text-does-not-hold",
        ),
        # each key written after a question mark, the value on the line below
        pytest.param(
            "fields:\n  ? a\n  : k\n  ? b\n  : c\n",
            "fields",
            "b",
            ValueError,
            "at fields does not admit the removal as text",
            id="a-key-that-does-not-begin-its-line",
        ),
    ],
)
def test_remove_from_mapping_refuses_a_key_that_it_cannot_take_out_as_text(
    text, address, key, refusal, match
):
    """`remove_from_mapping` refuses an address of no mapping or not in the
    text, a key that the mapping does not hold, and a key after the first
    that does not begin its line."""
    with pytest.raises(refusal, match=match):
        remove_from_mapping(text, address, key)
