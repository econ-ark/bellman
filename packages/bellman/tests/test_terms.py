"""The parsed term of a stage file: its JSON form read back, the .bl text of a
term, and the spans and addresses of the items of a text."""

import collections.abc
import copy
import functools
import json
import pathlib
import re
from dataclasses import fields, is_dataclass
from operator import attrgetter

import pytest
from application_files import CORPUS, ROOT, STAGE_FILES, STAGES_WITH_BINDINGS, stage_file_id
from snapshot.record import recording_path
from stage_texts import corpus_text

import bellman.stage
from bellman.refusals import ConstructionError
from bellman.stage import ROLE_WORD, source_spans, to_source
from bellman.syntax import terms
from bellman.syntax.decode import TermDecodeError, from_json
from bellman.syntax.lower import SourceSpan, item_addresses, parse_with_spans, to_json

PORTFOLIO = ROOT / "applications/portfolio-choice/declaration/stages"


RETIREMENT = ROOT / "applications/retirement-choice/declaration/stages"


CONS_FILE = ROOT / CORPUS["cons"]


PORT_FILE = PORTFOLIO / "port/port.bl"


RET_CHOICE_FILE = RETIREMENT / "ret_choice/ret_choice.bl"


def text_at(text, span):
    """The source text a span covers: `column` is the 1-based column of the
    first character and `end_column` the column just after the last one."""
    lines = text.splitlines()
    if span.line == span.end_line:
        return lines[span.line - 1][span.column - 1 : span.end_column - 1]
    first = lines[span.line - 1][span.column - 1 :]
    middle = lines[span.line : span.end_line - 1]
    last = lines[span.end_line - 1][: span.end_column - 1]
    return "\n".join([first, *middle, last])


def entry_value(annotation, key):
    """The value of the first `key=` entry of an Annotation, else None."""
    if annotation is None:
        return None
    for entry in annotation.entries:
        if isinstance(entry, terms.KeyValue) and entry.key == key:
            return str(entry.value)
    return None


def expected_addresses(term):
    """The addresses of the authored items of a term, computed from the term
    alone: an item at file level is its 1-based position in the file; a
    block with an `id=` entry in its header is that id, and a nested block
    its `label=`; a line or a declaration inside a block is
    `<block address>.<id>` when its annotation carries `id=`, and otherwise
    `<block address>.<n>`, with n its 1-based position in the block."""
    out = []

    def walk(items, prefix):
        for n, item in enumerate(items, 1):
            if isinstance(item, terms.Block):
                head = entry_value(item.tag, "id") or (
                    entry_value(item.tag, "label") if prefix else None
                )
            elif prefix and isinstance(item, (terms.Statement, terms.Declare)):
                head = entry_value(item.annot, "id")
            else:
                head = None
            address = prefix + (head or str(n))
            out.append(address)
            if isinstance(item, terms.Block):
                walk(item.body, address + ".")

    walk(term.items, "")
    return out


def with_line_replaced(text, number, line):
    """`text` with its line `number`, counted from 1, replaced by `line`."""
    lines = text.split("\n")
    lines[number - 1] = line
    return "\n".join(lines)


UNDECLARED = (
    "@stage: probe\n"
    "\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = V[>] + undeclared_symbol\n"
    "}\n"
)


DUPLICATE = (
    "@stage: probe\n"
    "\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = V[>]        :: [id=value]\n"
    "    V = 2 * V[>]    :: [id=value]\n"
    "}\n"
)


# the recording of the parsed term of cons.bl, as JSON
RECORDED_CONS_TERM = recording_path(CONS_FILE, ".ast.json")


# A valid encoded item and the FILE encoding around a list of items.
METADATA = {"__class__": "Metadata", "key": "stage", "value": "cons"}


def file_of(*items):
    """The encoding of a FILE whose items are the encodings `items`."""
    return {"__class__": "FILE", "items": list(items)}


def instance_of(constructor):
    """An instance of `constructor` with an empty tuple in each sequence slot
    and a string in every other slot."""
    return constructor(
        **{
            field.name: () if field.type is tuple else f"<{field.name}>"
            for field in fields(constructor)
        }
    )


@functools.cache
def names_of_the_term_module():
    """The names of the constructors and of the sorts of the term module, read
    from its source text: a constructor is a frozen dataclass with a base,
    and a sort is a class with no base whose slots are empty."""
    source = pathlib.Path(terms.__file__).read_text(encoding="utf-8")
    constructors = re.findall(
        r"^@dataclass\(frozen=True, slots=True\)\nclass (\w+)\(\w+\):", source, flags=re.MULTILINE
    )
    sorts = re.findall(r"^class (\w+):\n    __slots__ = \(\)$", source, flags=re.MULTILINE)
    return tuple(constructors), tuple(sorts)


# The optional slots of the term module, each encoded by hand with null and
# compared with the term built the way the lowering builds it; a Variable is
# written with its name, its time and its shift in time, 1 for the next period.
OPTIONAL_SLOT_CASES = {
    "Statement.annot": (
        {
            "__class__": "Statement",
            "core": {"__class__": "Residual", "form": {"__class__": "Number", "value": 0}},
            "annot": None,
        },
        terms.Statement(terms.Residual(terms.Number(0)), None),
    ),
    "PathAssignment.bound": (
        {
            "__class__": "PathAssignment",
            "target": {
                "__class__": "Variable",
                "name": "k",
                "when": {"__class__": "T"},
                "shift": 1,
            },
            "bound": None,
            "value": {"__class__": "Number", "value": 2},
        },
        terms.PathAssignment(terms.Variable("k", terms.T(), 1), None, terms.Number(2)),
    ),
    "Range.left and Range.right": (
        {
            "__class__": "Range",
            "left": None,
            "lower": {"__class__": "Number", "value": 0},
            "upper": {"__class__": "Number", "value": 1},
            "right": None,
        },
        terms.Range(None, terms.Number(0), terms.Number(1), None),
    ),
    "Declaration.value": (
        {
            "__class__": "Declaration",
            "subject": {"__class__": "Subject", "coordinates": []},
            "classifiers": [],
            "value": None,
        },
        terms.Declaration(terms.Subject(()), (), None),
    ),
    "Coordinate.at": (
        {"__class__": "Coordinate", "stem": "c", "at": None, "classifiers": []},
        terms.Coordinate("c", None, ()),
    ),
    "Comprehension.base": (
        {
            "__class__": "Comprehension",
            "bound": {"__class__": "Subject", "coordinates": []},
            "base": None,
            "conds": [],
        },
        terms.Comprehension(terms.Subject(()), None, ()),
    ),
}


# the values of the one slot of a Number that the tests encode by hand, each
# a JSON value of another kind
PRIMITIVE_VALUES = [
    pytest.param("x", id="a string"),
    pytest.param("𝑢", id="a string outside ASCII"),
    pytest.param("", id="the empty string"),
    pytest.param(3, id="an integer"),
    pytest.param(-7, id="a negative integer"),
    pytest.param(0.5, id="a float"),
    pytest.param(True, id="true, which equals the integer 1"),
    pytest.param(False, id="false, which equals the integer 0"),
]


# each FILE that the tests encode by hand: the empty file, a file whose item
# has an optional slot written as null, and a file whose item is a Number
HAND_ENCODED_FILES = [
    pytest.param(file_of(), id="an empty file"),
    *(
        pytest.param(file_of(encoded), id=f"{slot} written as null")
        for slot, (encoded, _) in OPTIONAL_SLOT_CASES.items()
    ),
    *(
        pytest.param(
            file_of({"__class__": "Number", "value": row.values[0]}), id=f"a number, {row.id}"
        )
        for row in PRIMITIVE_VALUES
    ),
]


# the class names that name no constructor, each in an item: names that a
# decoder that looked names up in a module or in the builtins would find
OUTSIDE_CLASS_NAMES = [
    pytest.param({"__class__": "Bogus", "x": 1}, id="an unknown name, with a field"),
    pytest.param({"__class__": "PosixPath"}, id="a class of the standard library"),
    pytest.param({"__class__": "Tree"}, id="the class Tree of the parser library"),
    pytest.param({"__class__": "Lark"}, id="the class Lark of the parser library"),
    pytest.param({"__class__": "Token"}, id="the class Token of the parser library"),
    pytest.param({"__class__": "Transformer"}, id="the class Transformer of the parser library"),
    pytest.param({"__class__": "MappingProxyType"}, id="the read-only mapping type"),
    pytest.param({"__class__": "dataclass"}, id="dataclass, which the term module imports"),
    pytest.param({"__class__": "field"}, id="field, a function of the dataclasses module"),
    pytest.param({"__class__": "dict"}, id="the builtin dict"),
    pytest.param({"__class__": "list"}, id="the builtin list"),
    pytest.param({"__class__": "object"}, id="the builtin object"),
    pytest.param({"__class__": "str"}, id="the builtin str"),
    pytest.param({"__class__": "FILE.items"}, id="a slot of a constructor"),
    pytest.param({"__class__": "bellman.syntax.terms.FILE"}, id="the full name of a constructor"),
    pytest.param({"__class__": ""}, id="the empty name"),
]


def pytest_generate_tests(metafunc):
    """The rows of the tests that read `constructor_name` or
    `refused_class`: the constructors of the term module, and the class
    names that name no constructor with each sort of the term module, read
    from its source text when pytest collects the tests."""
    constructors, sorts = names_of_the_term_module()
    if "constructor_name" in metafunc.fixturenames:
        metafunc.parametrize("constructor_name", constructors)
    if "refused_class" in metafunc.fixturenames:
        metafunc.parametrize(
            "refused_class",
            [
                *OUTSIDE_CLASS_NAMES,
                *(pytest.param({"__class__": sort}, id=f"the sort {sort}") for sort in sorts),
            ],
        )


@pytest.fixture(scope="module")
def recorded_cons_term():
    """The text of the recording of the parsed term of cons.bl."""
    return RECORDED_CONS_TERM.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def undeclared_spans():
    """The span table of the text `UNDECLARED`, read with no file name."""
    _, spans = parse_with_spans(UNDECLARED)
    return spans


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(CONS_FILE, id="the consumption stage"),
        pytest.param(PORT_FILE, id="the portfolio stage"),
        pytest.param(RET_CHOICE_FILE, id="the retirement choice"),
    ],
)
def test_every_span_of_a_stage_file_names_the_file_by_its_path_from_the_repository(
    path, parsed_source
):
    """Each span of the span table of a stage file names the file by its path
    from the root of the repository."""
    _, spans = parsed_source(path)
    assert {span.file for span in spans.values()} == {path.relative_to(ROOT).as_posix()}


@pytest.mark.parametrize(
    ("path", "address", "position"),
    [
        # (line, column, end line, end column) of each span
        pytest.param(CONS_FILE, "1", (1, 1, 1, 13), id="the metadata line"),
        pytest.param(CONS_FILE, "2", (3, 1, 3, 10), id="the definition of a set"),
        pytest.param(CONS_FILE, "4", (6, 1, 6, 13), id="a declaration"),
        pytest.param(
            CONS_FILE, "5", (8, 1, 8, 49), id="the definition of a function with its annotation"
        ),
        pytest.param(CONS_FILE, "cntn_to_dcsn", (20, 1, 23, 2), id="a block"),
        pytest.param(
            CONS_FILE,
            "cntn_to_dcsn.value",
            (21, 5, 21, 50),
            id="a line of a block named by its id",
        ),
        pytest.param(
            CONS_FILE,
            "arvl_to_dcsn.1",
            (13, 5, 13, 12),
            id="a line of a block named by its position",
        ),
        pytest.param(CONS_FILE, "policy", (29, 1, 31, 2), id="the policy block"),
        pytest.param(PORT_FILE, "10", (13, 1, 15, 43), id="a distribution on three lines"),
        pytest.param(RET_CHOICE_FILE, "dcsn_to_cntn", (9, 1, 12, 2), id="a branching block"),
        pytest.param(RET_CHOICE_FILE, "dcsn_to_cntn.work", (10, 5, 10, 59), id="a nested block"),
        pytest.param(
            RET_CHOICE_FILE, "dcsn_to_cntn.work.1", (10, 48, 10, 57), id="a line of a nested block"
        ),
    ],
)
def test_the_span_of_an_authored_item_holds_the_line_and_column_where_it_starts_and_ends(
    path, address, position, parsed_source
):
    """The span of an authored item of a stage file holds the line and the
    column of the item's first character and those just after its last."""
    _, spans = parsed_source(path)
    span = spans[address]
    assert (span.line, span.column, span.end_line, span.end_column) == position


@pytest.mark.parametrize(
    ("path", "address", "excerpt"),
    [
        pytest.param(CONS_FILE, "1", "@stage: cons", id="the metadata line"),
        pytest.param(CONS_FILE, "2", "Xm := ℝ₊₊", id="the definition of a set"),
        pytest.param(CONS_FILE, "4", "ρ : [1, inf)", id="a declaration"),
        pytest.param(
            CONS_FILE,
            "5",
            "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]",
            id="the definition of a function with its annotation",
        ),
        pytest.param(
            CONS_FILE,
            "cntn_to_dcsn.value",
            "V        = 𝑢(c) + V[>]          :: [id=value]",
            id="a line of a block named by its id",
        ),
        pytest.param(
            CONS_FILE, "arvl_to_dcsn.1", "m_d = m", id="a line of a block named by its position"
        ),
        pytest.param(
            RET_CHOICE_FILE, "dcsn_to_cntn.work.1", "a_w = a_d", id="a line of a nested block"
        ),
    ],
)
def test_the_span_of_an_authored_item_written_on_one_line_covers_its_text(
    path, address, excerpt, parsed_source
):
    """The span of an authored item written on one line of a stage file covers
    the text of the item, its annotation included."""
    text = path.read_text(encoding="utf-8")
    _, spans = parsed_source(path)
    assert text_at(text, spans[address]) == excerpt


def test_the_span_of_a_block_of_the_consumption_stage_covers_the_lines_of_the_block(
    parsed_source,
):
    """The span of the block `cntn_to_dcsn` of cons.bl covers the block from
    its header to its closing brace."""
    text = CONS_FILE.read_text(encoding="utf-8")
    _, spans = parsed_source(CONS_FILE)
    covered = text_at(text, spans["cntn_to_dcsn"])
    assert covered.startswith("[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c)")
    assert covered.endswith("[id=marginal]\n}")
    # lines 20 to 23 of cons.bl
    assert covered == "\n".join(text.splitlines()[19:23])


def test_the_span_table_of_the_consumption_stage_lists_its_items_then_39_header_components(
    parsed_source,
):
    """The span table of cons.bl lists the addresses of its 18 authored items
    in the order of the text, then 39 entries, the components of its block
    headers."""
    term, spans = parsed_source(CONS_FILE)
    # 7 items at file level, 5 blocks, 6 lines of blocks, and 39 components
    assert len(spans) == 7 + 5 + 6 + 39
    assert list(spans)[:18] == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "arvl_to_dcsn",
        "arvl_to_dcsn.1",
        "dcsn_to_cntn",
        "dcsn_to_cntn.1",
        "cntn_to_dcsn",
        "cntn_to_dcsn.value",
        "cntn_to_dcsn.marginal",
        "dcsn_to_arvl",
        "dcsn_to_arvl.value",
        "policy",
        "policy.optimality",
    ]
    items = [address for address, _ in item_addresses(term)]
    assert len(spans) == len(items) + 39


def test_the_span_of_a_distribution_declaration_written_on_three_lines_covers_the_three_lines(
    parsed_source,
):
    """The span of the distribution declaration of `(Ψ, θ)` of port.bl, which
    is written on three lines, covers it from its subject to its last
    bracket."""
    text = PORT_FILE.read_text(encoding="utf-8")
    _, spans = parsed_source(PORT_FILE)
    covered = text_at(text, spans["10"])
    assert covered.startswith("(Ψ, θ) ~ LogNormal((μ_Ψ, μ_θ),")
    assert covered.endswith("(ρ_ζ*σ_Ψ*σ_θ, σ_θ^2)))")
    assert covered.count("\n") == 2


def test_the_second_nested_block_of_a_branching_block_starts_at_its_line(parsed_source):
    """The span of the nested block `retire` of the block `dcsn_to_cntn` of
    ret_choice.bl starts at line 11."""
    _, spans = parsed_source(RET_CHOICE_FILE)
    assert spans["dcsn_to_cntn.retire"].line == 11


@pytest.mark.parametrize(
    "path",
    [*(path for path in STAGE_FILES if path.parent.parent == PORTFOLIO), RET_CHOICE_FILE],
    ids=stage_file_id,
)
def test_addresses_follow_authored_identifiers_and_item_positions(path, parsed_source):
    """The span table of each stage file of the portfolio application and of
    the retirement choice begins with the address of each authored item,
    given by its id, by its label for a nested block, or by its position."""
    term, spans = parsed_source(path)
    addresses = expected_addresses(term)
    assert list(spans)[: len(addresses)] == addresses


def test_the_span_table_of_a_stage_file_is_a_read_only_mapping(parsed_source):
    """The span table of cons.bl is a mapping that refuses the assignment and
    the deletion of an entry."""
    _, spans = parsed_source(CONS_FILE)
    assert isinstance(spans, collections.abc.Mapping)
    with pytest.raises(TypeError):
        spans["1"] = spans["2"]
    with pytest.raises(TypeError):
        del spans["1"]


def test_a_line_that_names_an_undeclared_symbol_has_a_span_at_its_place(undeclared_spans):
    """The parser records the span of a line of a block that names a symbol
    that no line declares, under the line's address, with no file name, at
    the line's place and covering its text."""
    # refusing the undeclared symbol is the task of the elaboration; the
    # line is line 4, after four spaces of indent, and holds 28 code points
    assert "cntn_to_dcsn.1" in undeclared_spans
    span = undeclared_spans["cntn_to_dcsn.1"]
    assert span.file is None
    assert (span.line, span.column, span.end_line, span.end_column) == (4, 5, 4, 33)
    assert text_at(UNDECLARED, span) == "V = V[>] + undeclared_symbol"


@pytest.mark.parametrize(
    ("address", "span"),
    [
        pytest.param(
            "cntn_to_dcsn",
            SourceSpan(file=None, line=3, column=1, end_line=5, end_column=2),
            id="the block, from its header to its closing brace",
        ),
        pytest.param(
            "1",
            SourceSpan(file=None, line=1, column=1, end_line=1, end_column=14),
            id="the metadata line",
        ),
    ],
)
def test_an_item_of_a_text_read_with_no_file_name_has_its_span_with_no_file(
    address, span, undeclared_spans
):
    """The span of an item of a text read with no file name names no file and
    holds the line and the column where the item starts and ends."""
    assert undeclared_spans[address] == span


def test_the_span_table_of_a_text_lists_the_components_of_a_header_after_the_items(
    undeclared_spans,
):
    """The span table of a text of one block lists the metadata line, the block
    and its line, and then each side of the block's header, each field the
    side lists and the set and the role word of that field."""
    assert list(undeclared_spans) == [
        "1",
        "cntn_to_dcsn",
        "cntn_to_dcsn.1",
        # the components of the header, after the items
        "cntn_to_dcsn.in",
        "cntn_to_dcsn.in.V[>]",
        "cntn_to_dcsn.in.V[>].domain",
        "cntn_to_dcsn.in.V[>].role",
        "cntn_to_dcsn.out",
        "cntn_to_dcsn.out.V",
        "cntn_to_dcsn.out.V.domain",
        "cntn_to_dcsn.out.V.role",
    ]


def test_the_span_of_the_set_of_a_field_on_a_side_covers_the_set_alone(undeclared_spans):
    """The span of the set `ℝ` of the field `V[>]` on the input side of the
    header covers the one character of the set."""
    domain = undeclared_spans["cntn_to_dcsn.in.V[>].domain"]
    assert (domain.column, domain.end_column) == (27, 28)


def test_two_lines_of_a_block_with_one_id_are_refused_with_the_address_and_both_lines():
    """A span table maps each address to one span, so two lines of one block
    annotated `id=value` are refused, with a message that names the
    address and the place of both lines."""
    with pytest.raises(ValueError) as caught:
        parse_with_spans(DUPLICATE, "probe.bl")
    phrases = ("cntn_to_dcsn.value", "probe.bl:4", "probe.bl:5")
    assert [phrase for phrase in phrases if phrase not in str(caught.value)] == []


def test_an_empty_file_reads_from_its_json_encoding():
    """`from_json` reads the encoding of a FILE with no item as the empty
    FILE."""
    assert from_json(file_of()) == terms.FILE(())


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [pytest.param(*case, id=slot) for slot, case in OPTIONAL_SLOT_CASES.items()],
)
def test_an_optional_slot_written_as_null_reads_as_the_term_with_no_value_in_it(encoded, expected):
    """`from_json` reads a file whose item writes an optional slot as null as
    the FILE of the item with `None` in that slot."""
    term = from_json(file_of(copy.deepcopy(encoded)))
    assert isinstance(term, terms.FILE)
    (item,) = term.items
    assert item == expected


@pytest.mark.parametrize("value", PRIMITIVE_VALUES)
def test_a_primitive_value_of_a_slot_reads_with_its_value_and_its_type(value):
    """`from_json` reads the value of a slot that holds a string, a number or a
    boolean as that value, of the same type."""
    term = from_json(file_of({"__class__": "Number", "value": value}))
    assert isinstance(term, terms.FILE)
    (item,) = term.items
    assert (item.value is value or item.value == value) and type(item.value) is type(value)


@pytest.mark.parametrize("encoded", HAND_ENCODED_FILES)
def test_to_json_writes_back_each_encoding_that_from_json_reads(encoded):
    """`to_json` writes the term that `from_json` reads of an encoding of a
    FILE as that encoding."""
    assert to_json(from_json(copy.deepcopy(encoded))) == encoded


@pytest.mark.parametrize("encoded", HAND_ENCODED_FILES)
def test_from_json_leaves_each_encoding_it_reads_unchanged(encoded):
    """`from_json` changes nothing in the encoding of a FILE that it reads."""
    data = copy.deepcopy(encoded)
    from_json(data)
    assert data == encoded


def test_an_instance_of_each_constructor_makes_an_exact_round_trip_through_its_json_encoding(
    constructor_name,
):
    """The encoding that `to_json` writes of an instance of a constructor of
    the term module reads back, by `from_json`, as an equal instance of that
    constructor, which `to_json` writes as the same encoding; the decoder
    checks the kinds of the slots and not their sorts."""
    constructor = getattr(terms, constructor_name)
    instance = instance_of(constructor)
    data = file_of(to_json(instance))
    before = copy.deepcopy(data)
    term = from_json(data)
    assert isinstance(term, terms.FILE)
    (item,) = term.items
    assert item == instance and type(item) is constructor
    assert to_json(term) == before


def test_the_names_read_from_the_source_of_the_term_module_are_its_classes():
    """The constructors and the sorts that `names_of_the_term_module` reads
    from the source text of the term module are the dataclasses and the
    other classes that the module defines, so that no constructor and no
    sort goes without its rows."""
    constructors, sorts = names_of_the_term_module()
    defined = [
        (name, is_dataclass(value))
        for name, value in vars(terms).items()
        if isinstance(value, type) and value.__module__ == terms.__name__
    ]
    assert (sorted(constructors), sorted(sorts)) == (
        sorted(name for name, dataclass in defined if dataclass),
        sorted(name for name, dataclass in defined if not dataclass),
    )


def test_from_json_leaves_the_encoding_of_an_instance_of_each_constructor_unchanged(
    constructor_name,
):
    """`from_json` changes nothing in the encoding of an instance of a
    constructor of the term module that it reads."""
    data = file_of(to_json(instance_of(getattr(terms, constructor_name))))
    before = copy.deepcopy(data)
    from_json(data)
    assert data == before


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(
            {"items": [], "__class__": "FILE"},
            terms.FILE(()),
            id="the keys of the file in another order",
        ),
        pytest.param(
            file_of({"value": "cons", "__class__": "Metadata", "key": "stage"}),
            terms.FILE((terms.Metadata("stage", "cons"),)),
            id="the keys of an item in another order",
        ),
    ],
)
def test_from_json_reads_the_keys_of_an_object_whatever_their_order(encoded, expected):
    """`from_json` reads an object by the set of its keys and not by their
    order, since the keys of a JSON object have no order."""
    assert from_json(encoded) == expected


def test_a_class_name_that_names_no_constructor_is_refused_at_its_path(refused_class):
    """`from_json` refuses an item whose class name names no constructor of the
    term module, with a message that names the path of the item and the
    class name."""
    with pytest.raises(TermDecodeError) as refused:
        from_json(file_of(refused_class))
    message = str(refused.value)
    assert "items[0]" in message and repr(refused_class["__class__"]) in message


@pytest.mark.parametrize(
    ("data", "path", "detail"),
    [
        pytest.param(
            file_of({**METADATA, "extra": 1}), "items[0]", "'extra'", id="an unknown field"
        ),
        pytest.param(
            file_of({"__class__": "Metadata", "key": "stage"}),
            "items[0]",
            "'value'",
            id="a missing required field",
        ),
        pytest.param(
            file_of(
                {
                    "__class__": "Statement",
                    "core": {
                        "__class__": "Residual",
                        "form": {"__class__": "Number", "value": 0},
                    },
                }
            ),
            "items[0]",
            "'annot'",
            id="a missing optional field",
        ),
    ],
)
def test_an_object_that_lacks_a_field_or_holds_another_is_refused_at_its_path(data, path, detail):
    """`from_json` refuses an object whose fields are not the fields of its
    constructor, with a message that names the path of the object and the
    field."""
    with pytest.raises(TermDecodeError) as refused:
        from_json(data)
    message = str(refused.value)
    assert path in message and detail in message


@pytest.mark.parametrize(
    ("data", "path"),
    [
        pytest.param({"items": []}, "root", id="the root"),
        pytest.param(
            file_of(
                {
                    "__class__": "Statement",
                    "core": {
                        "lhs": {"__class__": "Number", "value": 1},
                        "rhs": {"__class__": "Number", "value": 1},
                    },
                    "annot": None,
                }
            ),
            "items[0].core",
            id="an object inside an item",
        ),
    ],
)
def test_an_object_with_no_class_name_is_refused_at_its_path(data, path):
    """`from_json` refuses an object that names no class, at the root or inside
    an item, with a message that names the path of the object and the key
    `__class__`."""
    with pytest.raises(TermDecodeError) as refused:
        from_json(data)
    message = str(refused.value)
    assert path in message and "__class__" in message


@pytest.mark.parametrize(
    ("data", "path"),
    [
        pytest.param(
            file_of({**METADATA, "key": ["stage"]}), "items[0].key", id="a list in a slot"
        ),
        pytest.param(
            {"__class__": "FILE", "items": METADATA}, "items", id="an object as the items"
        ),
        pytest.param(
            file_of(
                {
                    "__class__": "Block",
                    "tag": {"__class__": "Annotation", "entries": []},
                    "body": METADATA,
                }
            ),
            "items[0].body",
            id="an object as the body of a block",
        ),
        pytest.param({"__class__": "FILE", "items": None}, "items", id="null as the items"),
        pytest.param(file_of([METADATA]), "items[0]", id="a list as an item"),
        pytest.param(
            file_of({**METADATA, "key": ("stage",)}), "items[0].key", id="a value that is no JSON"
        ),
    ],
)
def test_a_slot_that_holds_a_value_of_another_kind_is_refused_at_its_path(data, path):
    """`from_json` refuses a slot that holds a value of another kind than its
    own, a sequence, one term or a primitive value, with a message that
    names the path of the slot."""
    with pytest.raises(TermDecodeError) as refused:
        from_json(data)
    assert path in str(refused.value)


def test_a_refusal_of_the_decoder_is_a_value_error():
    """The class of the refusals of `from_json` is a kind of `ValueError`, so
    that its refusal of an empty list is caught as a `ValueError`."""
    assert issubclass(TermDecodeError, ValueError)
    with pytest.raises(ValueError):
        from_json([])


@pytest.mark.parametrize(
    ("root", "phrases"),
    [
        # a value that is no object cannot encode a term
        pytest.param([file_of()], ("root", "cannot encode a term"), id="a list that holds a file"),
        pytest.param([], ("root", "cannot encode a term"), id="an empty list"),
        pytest.param("FILE", ("root", "cannot encode a term"), id="the string FILE"),
        pytest.param(3, ("root", "cannot encode a term"), id="an integer"),
        pytest.param(0.5, ("root", "cannot encode a term"), id="a float"),
        pytest.param(True, ("root", "cannot encode a term"), id="a boolean"),
        pytest.param(None, ("root", "cannot encode a term"), id="null"),
        pytest.param(METADATA, ("root", "Metadata", "FILE"), id="an item that is no file"),
    ],
)
def test_a_root_that_is_no_encoding_of_a_file_is_refused_at_the_root(root, phrases):
    """`from_json` refuses a root that is no object of the class `FILE`, with a
    message that names the root and says what the root is."""
    with pytest.raises(TermDecodeError) as refused:
        from_json(root)
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(3, id="an integer"),
        pytest.param(None, id="null"),
        pytest.param(True, id="a boolean"),
        pytest.param(0.5, id="a float"),
        pytest.param(["FILE"], id="a list"),
        pytest.param(file_of(), id="an object"),
    ],
)
@pytest.mark.parametrize(
    ("place", "phrase"),
    [
        pytest.param("item", "items[0]", id="in an item"),
        pytest.param("root", "root", id="at the root"),
    ],
)
def test_a_class_name_that_is_no_string_is_refused_at_its_place(value, place, phrase):
    """`from_json` refuses a class name that is no string, in an item or at the
    root, with a message that names that place and says that a class name
    is a string."""
    data = file_of({"__class__": value}) if place == "item" else {"__class__": value, "items": []}
    with pytest.raises(TermDecodeError) as refused:
        from_json(data)
    assert [text for text in (phrase, "must be a string") if text not in str(refused.value)] == []


def test_a_declaration_with_a_list_as_its_subject_is_refused_at_its_path_in_a_recorded_term(
    recorded_cons_term,
):
    """`from_json` refuses the recorded term of cons.bl with the subject of its
    first declaration replaced by a list, with a message that names the
    path of the subject."""
    data = json.loads(recorded_cons_term)
    k = next(index for index, item in enumerate(data["items"]) if item["__class__"] == "Declare")
    data["items"][k]["declaration"]["subject"] = []
    with pytest.raises(TermDecodeError) as refused:
        from_json(data)
    assert f"items[{k}].declaration.subject" in str(refused.value)


def test_a_misspelled_class_of_a_line_is_refused_at_its_path_in_a_recorded_term(
    recorded_cons_term,
):
    """`from_json` refuses the recorded term of cons.bl with the class of the
    first line of its first block misspelled, with a message that names the
    path of the line and the misspelled class."""
    data = json.loads(recorded_cons_term)
    b = next(index for index, item in enumerate(data["items"]) if item["__class__"] == "Block")
    j = next(
        index
        for index, item in enumerate(data["items"][b]["body"])
        if item["__class__"] == "Statement"
    )
    data["items"][b]["body"][j]["core"]["__class__"] = "Equatoin"
    with pytest.raises(TermDecodeError) as refused:
        from_json(data)
    message = str(refused.value)
    assert f"items[{b}].body[{j}].core" in message and "'Equatoin'" in message


@pytest.mark.parametrize("name", STAGES_WITH_BINDINGS)
def test_every_statement_of_a_corpus_stage_prints_to_a_line_that_lowers_to_an_equal_term(name):
    """Each statement of a corpus stage, distribution declarations included,
    prints to a line that lowers, in the same place, to a term whose
    encoding equals that of the statement."""
    term, _ = parse_with_spans(corpus_text(name))
    statements = [
        (address, item)
        for address, item in item_addresses(term)
        if isinstance(item, terms.Statement)
    ]
    assert statements
    for address, item in statements:
        printed = to_source(item.core)
        if "." in address:
            # a line of a block, read back as the one line of a block
            text = "@stage: x\n[id=b, (x) : !dcsn -> (y) : !dcsn] {\n    " + printed + "\n}\n"
            relowered = parse_with_spans(text).term.items[1].body[0].core
        else:
            # a declaration, a definition or an assignment, read back as the
            # one item after the metadata line
            relowered = parse_with_spans("@stage: x\n" + printed + "\n").term.items[1].core
        assert to_json(relowered) == to_json(item.core), (address, printed)


@pytest.mark.parametrize("name", STAGES_WITH_BINDINGS)
def test_source_spans_answers_the_span_table_of_the_lowering(name):
    """`source_spans` answers, for a corpus stage, the span table that the
    lowering makes of its text."""
    spans = source_spans(corpus_text(name), CORPUS[name])
    assert dict(spans) == dict(parse_with_spans(corpus_text(name), filename=CORPUS[name]).spans)


def test_source_spans_places_the_policy_block_of_the_consumption_stage_on_lines_29_to_31():
    """The span that `source_spans` gives the policy block of cons.bl names the
    file and runs from line 29, column 1, to line 31, column 2."""
    policy = source_spans(corpus_text("cons"), CORPUS["cons"])["policy"]
    assert (policy.file, policy.line, policy.column, policy.end_line, policy.end_column) == (
        CORPUS["cons"],
        29,
        1,
        31,
        2,
    )


def test_source_spans_places_the_line_of_the_policy_block_of_the_consumption_stage_at_line_30():
    """The span that `source_spans` gives the line `optimality` of the policy
    block of cons.bl is on line 30."""
    spans = source_spans(corpus_text("cons"), CORPUS["cons"])
    assert spans["policy.optimality"].line == 30


def test_the_span_table_that_source_spans_answers_refuses_the_assignment_of_an_entry():
    """The span table that `source_spans` answers for cons.bl, which holds the
    entry of the policy block, refuses the assignment of an entry."""
    spans = source_spans(corpus_text("cons"), CORPUS["cons"])
    assert "policy" in spans
    with pytest.raises(TypeError):
        spans["policy"] = None


def test_source_spans_refuses_a_text_the_parser_stops_at_where_it_stops():
    """`source_spans` refuses cons.bl with the line `a = m_d - c` written
    `a = m_d - - c` under `syntax`, at the line and the column of the
    second minus sign."""
    # line 17 of cons.bl is the line `a = m_d - c` of the block dcsn_to_cntn
    unreadable = with_line_replaced(corpus_text("cons"), 17, "    a = m_d - - c")
    with pytest.raises(ConstructionError) as refused:
        source_spans(unreadable, CORPUS["cons"])
    assert (refused.value.rule, refused.value.file, refused.value.line, refused.value.column) == (
        "syntax",
        CORPUS["cons"],
        17,
        15,
    )


def test_source_spans_refuses_one_id_on_two_lines_with_the_sentence_of_the_lowering():
    """`source_spans` refuses cons.bl with a second line `id=value` in the
    block `cntn_to_dcsn` under `syntax`, with the lowering's sentence on an
    address that names two items as the first line of its message."""
    # line 22 of cons.bl is the line `marginal` of the block cntn_to_dcsn, and
    # line 21 its line `value`
    id_on_two_lines = with_line_replaced(
        corpus_text("cons"), 22, "    D_{m_d}V = 𝑑𝑢(c)                :: [id=value]"
    )
    with pytest.raises(ConstructionError) as refused:
        source_spans(id_on_two_lines, CORPUS["cons"])
    assert refused.value.rule == "syntax"
    assert refused.value.message.startswith(
        f"the address 'cntn_to_dcsn.value' names two items, the first at {CORPUS['cons']}:21:5 "
        "and the second here; an id names one block, one line of a block or one nested block, "
        "and a label one nested block\n"
    )


@pytest.mark.parametrize(
    ("number", "line"),
    [
        # line 17 of cons.bl is the line `a = m_d - c`
        pytest.param(17, "    a = m_d - - c", id="a text the parser stops at"),
        # line 22 of cons.bl is the line `marginal` after the line `value`
        pytest.param(
            22,
            "    D_{m_d}V = 𝑑𝑢(c)                :: [id=value]",
            id="one id on two lines",
        ),
    ],
)
def test_elaborate_text_refuses_a_text_with_the_rule_place_and_message_of_source_spans(
    number, line
):
    """`elaborate_text` refuses a text that `source_spans` refuses, with the
    same rule, the same place and the same message."""
    text = with_line_replaced(corpus_text("cons"), number, line)
    rule_place_and_message = attrgetter(
        "rule", "file", "line", "column", "end_line", "end_column", "message"
    )
    with pytest.raises(ConstructionError) as refused:
        source_spans(text, CORPUS["cons"])
    with pytest.raises(ConstructionError) as elaborated:
        bellman.stage.elaborate_text(text, CORPUS["cons"])
    assert rule_place_and_message(elaborated.value) == rule_place_and_message(refused.value)


def test_the_span_of_each_component_of_a_header_of_the_consumption_stage_covers_its_text():
    """The span of each side of a block header of cons.bl, of a field that the
    side lists, and of the set and the role word of that field covers the
    text written there."""
    text = corpus_text("cons")
    _, spans = parse_with_spans(text, filename=CORPUS["cons"])
    addresses = (
        "cntn_to_dcsn.in",
        "cntn_to_dcsn.in.V[>]",
        "cntn_to_dcsn.in.V[>].domain",
        "cntn_to_dcsn.in.V[>].role",
        "cntn_to_dcsn.in.c",
        "policy.in.V[>].domain",
        "dcsn_to_cntn.in.c.role",
        "dcsn_to_cntn.in.c.domain",
        "dcsn_to_cntn.out",
    )
    assert {address: text_at(text, spans[address]) for address in addresses} == {
        "cntn_to_dcsn.in": "(V[>] : [-inf, inf) @ !vlu, c) : !cntn",
        "cntn_to_dcsn.in.V[>]": "V[>] : [-inf, inf) @ !vlu",
        "cntn_to_dcsn.in.V[>].domain": "[-inf, inf)",
        "cntn_to_dcsn.in.V[>].role": "!vlu",
        "cntn_to_dcsn.in.c": "c",
        "policy.in.V[>].domain": "[-inf, inf)",
        # the control `c` of the block dcsn_to_cntn writes its role word
        # before its set
        "dcsn_to_cntn.in.c.role": "!ctrl",
        "dcsn_to_cntn.in.c.domain": "ℝ₊₊",
        "dcsn_to_cntn.out": "(a : Xa) : !cntn",
    }


def test_the_span_of_the_set_of_the_continuation_value_of_the_consumption_stage_names_its_place():
    """The span of the set of `V[>]` on the input side of the block
    `cntn_to_dcsn` of cons.bl names the file, line 20, and columns 27 to
    38."""
    _, spans = parse_with_spans(corpus_text("cons"), filename=CORPUS["cons"])
    domain = spans["cntn_to_dcsn.in.V[>].domain"]
    assert (domain.file, domain.line, domain.column, domain.end_line, domain.end_column) == (
        CORPUS["cons"],
        20,
        27,
        20,
        38,
    )


def test_a_field_listed_without_a_set_or_a_role_word_has_no_span_of_either():
    """The control `c`, listed bare on the input side of the block
    `cntn_to_dcsn` of cons.bl, has no span of a set and none of a role
    word, where its listing with both on the input side of the block
    `dcsn_to_cntn` has a span of each."""
    _, spans = parse_with_spans(corpus_text("cons"), filename=CORPUS["cons"])
    assert {"dcsn_to_cntn.in.c.domain", "dcsn_to_cntn.in.c.role"} <= set(spans)
    assert not {"cntn_to_dcsn.in.c.domain", "cntn_to_dcsn.in.c.role"} & set(spans)


def test_the_span_table_of_every_stage_file_lists_its_items_then_the_components_of_its_headers():
    """The span table of each stage file of the applications lists its
    authored items in their order, then entries that are each a side of a
    header, a field, a set, a role word, the word `!cnst` of a constant or a
    perch word, each covering the text written for it and each but a side on
    one line."""
    roles = {"!" + word for word in ROLE_WORD.values()}
    assert len(STAGE_FILES) > 30
    for path in STAGE_FILES:
        text = path.read_text(encoding="utf-8")
        term, spans = parse_with_spans(text, filename=str(path.relative_to(ROOT)))
        items = [address for address, _ in item_addresses(term)]
        assert list(spans)[: len(items)] == items, path
        for address in list(spans)[len(items) :]:
            parts = address.split(".")
            span = spans[address]
            text_written = text_at(text, span)
            assert {"in", "out"} & set(parts), (path, address)
            # a stage file may write a side of a header over several lines,
            # as tenure.bl of the durables application does
            side = parts[-1] in ("in", "out")
            assert side or span.line == span.end_line, (path, address)
            if parts[-1] == "domain":
                assert text_written and not text_written.startswith("!"), (path, address)
            elif parts[-1] == "role":
                assert text_written in roles, (path, address)
            elif parts[-1] == "constancy":
                assert text_written == "!cnst", (path, address)
            elif parts[-1] == "perch":
                assert text_written in {"!arvl", "!dcsn", "!cntn"}, (path, address)
            elif not side:
                assert text_written.startswith(parts[-1]), (path, address)
