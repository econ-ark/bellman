"""The pages of the documentation and the files of the repository checked
against the package: each states what the package does, in the names that the
package answers. The applications and the lesson that the documentation shows
are checked in `test_documented_applications_and_lessons.py`."""

import dataclasses
import importlib
import inspect
import json
import posixpath
import re

import pytest
from application_files import ROOT
from documentation_paths import DOCS, HOOKS, METHODS_PAGE
from model_explorer_views import needs_viewer
from refusal_rules import (
    class_of,
    every_rule,
    patterns_found,
    problem_lines,
    rules_in_order,
    unchecked_rows,
)
from skips import require_package

import bellman.period
import bellman.trellis
from bellman.display import cards, drawing, printed_records, sheets
from bellman.factory.model_explorer import PALETTE, REFUSAL_STYLE
from bellman.native.hypergraphs import copy_native
from bellman.semantic_rules import (
    APPENDIX,
    RULES_STATED_ELSEWHERE,
    SEMANTIC_RULES,
    UNCHECKED_ELSEWHERE,
)
from bellman.stage import (
    LAYER_COLORS,
    NODE_STYLE,
    OUTPUT_STYLE,
    PERCH_COLORS,
    pieces,
    write_model_explorer,
)
from bellman.stage.denotations import card
from bellman.stage.encoding import StageEncoding
from bellman.stage.kernels import Kernel, kernel

# the nine pages of the API of the stage object, one for each level of the
# way in, whose listings `docs/_hooks/stage_object_page.py` prints from the
# package
STAGE_OBJECT_PAGES = tuple(
    f"docs/Bellman-Sym/API/stage/{name}.md"
    for name in (
        "01-the-stage",
        "02-initial",
        "03-build",
        "04-builder",
        "05-piece",
        "06-par-and-settings",
        "07-methods",
        "08-definitions",
        "09-binding-verbs",
    )
)


# the nine pages of the stage object, with the page of the language on a stage
# and the overview of the semantics
STAGE_PAGES_WITH_OVERVIEWS = STAGE_OBJECT_PAGES + (
    "docs/Bellman-Sym/01-stage.md",
    "docs/overview/05-semantics.md",
)


# four pages of the wiki of the concepts
WIKI_PAGES = tuple(
    f"docs/wiki/{name}.md" for name in ("semgraph", "builder", "operator", "elaborated_stage")
)


# the four pages of the calculus that write functions and fields, and the page
# of its symbols
CALCULUS_PAGES = (
    "docs/bellman-calculus/02-Illustrative example.md",
    "docs/bellman-calculus/03-Stages and perches.md",
    "docs/bellman-calculus/04-fields, functions and types.md",
    "docs/bellman-calculus/05-Operators and builders.md",
    "docs/Bellman-Sym/reference/symbols-conventions.md",
)


def page_id(path):
    """The id of a row of a table over files: the file's path from the folder
    `docs/`, without the ending `.md`, with a hyphen for each space and no
    comma."""
    name = path.removeprefix("docs/").removesuffix(".md")
    return name.replace(" ", "-").replace(",", "")


# --- the retired names of the stage object ---


def test_no_piece_of_the_stage_object_answers_a_retired_name(cons):
    """No piece of the stage object, and neither the namespace of periods nor
    that of trellises, answers a name that the package has retired."""
    graphs = (cons.builder.bwd, cons.builder.fwd)
    handles = (
        cons.builder,
        *graphs,
        cons.dcsn.builder.bwd,
        cons.dcsn.builder.bwd["Pullback"],
        cons.initial,
        cons.initial.backward,
        cons.initial.backward["cntn_to_dcsn"],
        cons.definitions,
    )
    stage_names = ("builders", "initial_diagrams", "parameters", "denotation", "build")
    held = [(cons, name) for name in (*stage_names, "operators_of")]
    held += [(handle, name) for handle in handles for name in ("denotation", "draw")]
    held += [(graph, name) for graph in graphs for name in ("arvl", "dcsn", "policy")]
    # the grain named by a string, which an attribute now opens
    held += [(cons.builder.bwd, "at"), (cons.dcsn.builder.bwd, "at")]
    held += [
        (namespace, name)
        for namespace in (bellman.period, bellman.trellis)
        for name in ("draw_trellis", "draw_period")
    ]
    assert [(holder, name) for holder, name in held if hasattr(holder, name)] == []


# --- the colors of the view ---

# The palette is the set of the colors of the view. Each color is a token: the
# value of a custom property of `docs/_stylesheets/bellman.css`, under whose
# name `PALETTE` holds it.


def colors_in(document):
    """Every color a JSON document holds, as `(key, value)`: the value of
    each key that names a color, `backgroundColor`, `edgeColor` and the
    like, where it is set."""
    if isinstance(document, dict):
        for key, value in document.items():
            if key.endswith("Color"):
                if value is not None:
                    yield key, value
            else:
                yield from colors_in(value)
    elif isinstance(document, list):
        for item in document:
            yield from colors_in(item)


def contrast(first, second):
    """The contrast ratio of two colors written `#RRGGBB`, as WCAG 2.2
    defines it: the lighter relative luminance plus 0.05 over the darker
    plus 0.05."""

    def luminance(color):
        channels = [int(color[at : at + 2], 16) / 255 for at in (1, 3, 5)]
        red, green, blue = (
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        )
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_each_token_of_the_palette_has_the_value_that_the_stylesheet_gives_it(text_of):
    """Each token of the palette of the view has the value that the stylesheet
    of the documentation site gives the custom property of its name."""
    stylesheet = text_of("docs/_stylesheets/bellman.css")
    assert [name for name, value in PALETTE.items() if f"{name}:{value}" not in stylesheet] == []


@needs_viewer
def test_every_color_in_the_files_of_the_view_is_a_token_of_the_palette(
    cons_methodized_without_calibration, bound_port_cons_trellis, tmp_path
):
    """Every color that the files of the view of a stage with its methods and
    of a trellis write, for their nodes, layers and overlays, is a token of the
    palette."""
    written = []
    for view, folder in (
        (cons_methodized_without_calibration, "stage"),
        (bound_port_cons_trellis, "trellis"),
    ):
        for path in write_model_explorer(view, tmp_path / folder):
            written += colors_in(json.loads(path.read_text(encoding="utf-8")))
    # the files hold each of the five keys of a color
    assert {key for key, _ in written} == {
        "backgroundColor",
        "borderColor",
        "hoveredBorderColor",
        "textColor",
        "edgeColor",
    }
    assert {value for _, value in written} <= set(PALETTE.values())


def test_every_color_of_the_styles_of_the_view_is_a_token_of_the_palette():
    """Every color of the styles of the nodes, the node of a refused graph
    among them, of the layers and of the perch overlays is a token of the
    palette."""
    styles = [NODE_STYLE, OUTPUT_STYLE, REFUSAL_STYLE]
    tables = [
        *(dataclasses.astuple(style) for style in styles),
        *LAYER_COLORS.values(),
        PERCH_COLORS.values(),
    ]
    assert {color for table in tables for color in table} <= set(PALETTE.values())


def test_the_three_perch_overlays_have_three_different_colors():
    """The overlays of the arrival, the decision and the continuation perch
    are drawn in three different colors."""
    assert len(set(PERCH_COLORS.values())) == 3


@pytest.mark.parametrize(
    ("fill", "label"),
    [
        *(
            pytest.param(style.backgroundColor, style.textColor, id=f"{name}-node")
            for name, style in (
                ("operator", NODE_STYLE),
                ("output", OUTPUT_STYLE),
                ("refusal", REFUSAL_STYLE),
            )
        ),
        *(
            pytest.param(fill, label, id=f"{level}-layer")
            for level, (fill, _, label) in LAYER_COLORS.items()
        ),
    ],
)
def test_every_label_of_the_view_can_be_read_on_its_fill(fill, label):
    """The label of each style of a node and of each layer of the view stands
    on its fill at the contrast ratio of 4.5 that WCAG 2.2 asks of text."""
    assert contrast(fill, label) >= 4.5


@pytest.mark.parametrize("perch", list(PERCH_COLORS))
def test_the_edges_of_each_perch_overlay_can_be_seen_on_the_white_page(perch):
    """The color of a perch's overlay, in which its edges are drawn, stands on
    the white of the page at the contrast ratio of 3 that WCAG 2.2 asks of a
    graphical object."""
    white = PALETTE["--bf-face"]
    assert contrast(PERCH_COLORS[perch], white) >= 3


# --- the generated reference pages ---


# the types page, which the same script prints from the tables of types
TYPES_PAGE = "docs/Bellman-Sym/reference/types.md"


@pytest.fixture(scope="module")
def reference_pages():
    """The script that prints the reference pages, imported with its folder
    `docs/_hooks` at the front of the module path, or a skip of the test
    where the package markdown of the extra `docs` is not installed."""
    require_package("markdown", extra="docs")
    with pytest.MonkeyPatch.context() as patch:
        patch.syspath_prepend(str(HOOKS))
        yield importlib.import_module("reference_pages")


@pytest.fixture(scope="module")
def printed_methods_table(reference_pages):
    """The table of the methods page as the script prints it from the records
    of the package."""
    return reference_pages.methods_table(METHODS_PAGE)


def test_no_entry_of_the_methods_table_links_a_source_on_github(printed_methods_table):
    """No entry of the methods table links a source on GitHub, since no
    exported revision of the public repository holds the definitions."""
    assert "github.com" not in printed_methods_table


def test_the_types_page_holds_the_tables_that_the_script_prints(reference_pages, text_of):
    """The types page holds, between its two markers, the tables that the
    script prints from the tables of types of the package."""
    page = text_of(TYPES_PAGE)
    start, end = reference_pages.region(page)
    # the script writes its tables after one empty line, and ends them with
    # a newline
    assert page[start:end] == "\n\n" + reference_pages.types_table(TYPES_PAGE) + "\n"


# --- the words of the pages ---


@pytest.mark.parametrize("path", STAGE_PAGES_WITH_OVERVIEWS, ids=page_id)
def test_no_page_of_the_stage_writes_a_call_that_the_stage_object_no_longer_answers(text_of, path):
    """No page of the stage object, the page of the language on a stage or
    the overview of the semantics writes a call that the stage object no
    longer answers."""
    # the grain named by a string, the stage's query of its operators, the ten
    # questions that the stage no longer answers and the three verbs of a
    # handle merged into the verbs that state their facts, each written as a
    # reader would call it; a name that could stand in ordinary prose, such as
    # `kind(`, is written with the dot of its receiver
    retired_names = (
        ".at(",
        "at(grain)",
        "operators_of",
        "transition_map(",
        "aggregator(",
        "policy_relation(",
        "methods_of(",
        "definitions_of(",
        "expectations(",
        ".selection(",
        ".symbols(",
        ".kind(",
        ".branches(",
        ".origins(",
        ".affine(",
        ".directions(",
    )
    shown = text_of(path)
    assert [retired for retired in retired_names if retired in shown] == []


@pytest.mark.parametrize("path", CALCULUS_PAGES, ids=page_id)
def test_no_page_of_the_calculus_writes_a_function_in_the_roman_type_of_a_field(text_of, path):
    """No page of the calculus applies a roman letter to arguments, since a
    function is written in italic and a field in roman."""
    shown = text_of(path)
    forms = (
        r"\mathrm v(",
        r"\mathrm v_\succ(",
        r"\mathrm g(",
        r"\mathrm G(",
        r"\mathrm r(",
        r"\mathrm u(",
    )
    assert [form for form in forms if form in shown] == []


def test_the_illustrative_example_states_that_a_function_is_italic_and_a_field_roman(
    text_of,
):
    """The illustrative example of the calculus states the types in which a
    function, a field and a variable are written, and not the former sentence
    that roman letters denote functions."""
    note = text_of("docs/bellman-calculus/02-Illustrative example.md")
    assert "roman letters denote functions" not in note
    phrases = (
        "A function is italic",
        "A field is a roman capital",
        "A variable is italic",
    )
    assert [phrase for phrase in phrases if phrase not in note] == []


# the phrases that read a parameter or the policy as a parameter of a builder,
# which the documentation no longer writes: a parameter is named in the
# definitions, and the policy is typed once, on the output of the policy
# builder
PARAMETER_READINGS = (
    "parameter of a builder",
    "parameterised builder",
    "parameter of this box",
    "parameter of the builder",
    "as parameters",
    "in Γ(",
)


@pytest.mark.parametrize(
    "path", STAGE_PAGES_WITH_OVERVIEWS + WIKI_PAGES + ("AGENTS.md",), ids=page_id
)
def test_no_page_reads_a_parameter_or_the_policy_as_a_parameter_of_a_builder(text_of, path):
    """No page of the stage, no page of the wiki and not AGENTS.md reads a
    parameter or the policy as a parameter of a builder, in a sentence or in a
    row of a listing."""
    text = text_of(path)
    # the labels of the two rows that a listing of a builder no longer prints
    labelled = [
        line for line in text.splitlines() if line.startswith(("parameters  ", "defined in  "))
    ]
    assert labelled == []
    assert [reading for reading in PARAMETER_READINGS if reading in text] == []


def test_agents_md_states_how_the_package_names_and_draws_the_semgraph(text_of):
    """AGENTS.md, the instructions of the repository for its coding
    assistants, holds each passage that states how the package names, types
    and draws the pieces of the semgraph."""
    agents = text_of("AGENTS.md")
    passages = (
        "Pullback of the function 𝑉 along the law of motion 𝑔",
        "n initial diagram, a builders graph, a grain or a value bundle",
        "`signature()` answers one record with two parts, `inputs` and `outputs`; a decision "
        "builder's or a decision push-forward's is the signature of the operator at a policy",
        "the policy is typed once, on the policy builder's output; a decision builder or a "
        "decision push-forward is the operator at a policy",
        "Construct this in the native semgraph: the parameters and the policy are references "
        "in a box's data and are drawn as no wire, and the renderer draws what the graph holds.",
    )
    assert [passage for passage in passages if passage not in agents] == []


@pytest.mark.parametrize(
    ("path", "passages"),
    [
        pytest.param(
            "docs/bellman-calculus/03-Stages and perches.md",
            (
                "the family $\\pi \\mapsto \\mathbb T_{\\succ,\\pi}$ is a map "
                "$\\Pi_\\Gamma \\to [\\mathsf V_\\succ \\to \\mathsf V_\\sim]$",
                "the family $\\pi \\mapsto \\mathbb M_{\\succ,\\pi}$ is a map "
                "$\\Pi_\\Gamma \\to [\\mathsf M_\\sim \\to \\mathsf M_\\succ]$",
            ),
            id="stages-and-perches",
        ),
        pytest.param(
            "docs/bellman-calculus/05-Operators and builders.md",
            (
                "**The builder at a policy and the policy layer.**",
                "the decision builder is the operator at a policy, its signature the inputs "
                "and outputs of $\\mathbb T_{\\succ,\\pi}$",
            ),
            id="operators-and-builders",
        ),
        pytest.param(
            "docs/Bellman-Sym/reference/symbols-conventions.md",
            ("The policy is written as a subscript",),
            id="symbols-conventions",
        ),
    ],
)
def test_each_page_of_the_calculus_writes_the_policy_of_an_operator_as_a_subscript(
    text_of, path, passages
):
    """The page of stages and perches, the page of operators and builders and
    the page of the symbols each state the operator at a policy with the
    policy as its subscript."""
    text = text_of(path)
    assert [passage for passage in passages if passage not in text] == []


@pytest.mark.parametrize(
    "path",
    [
        "docs/bellman-calculus/03-Stages and perches.md",
        "docs/bellman-calculus/05-Operators and builders.md",
    ],
    ids=page_id,
)
def test_no_page_of_the_calculus_writes_a_dot_in_place_of_the_policy_of_an_operator(text_of, path):
    """Neither the page of stages and perches nor the page of operators and
    builders writes an operator at a policy with a dot in place of the
    policy."""
    text = text_of(path)
    forms = (r"\mathbb T_{\succ,\cdot}", r"\mathbb M_{\succ,\cdot}")
    assert [form for form in forms if form in text] == []


# the label `read at` and the phrases "selection condition" and "the argmax
# binder of", which the printed views no longer write; the word "binder"
# alone stays, since a listing states that the range of a correspondence is
# read from the binder that applies it
RETIRED_PRINTED_WORDS = ("`read at`", "selection condition", "the argmax binder of")


# the two of those that the modules of the package do not write either; the
# settings query keeps `read at` as the key of a row
RETIRED_IN_SOURCE = ("selection condition", "the argmax binder of")


# a line that begins with the label `read at`, or with a signature written
# `signature (…) -> (`, two forms of a printed row that the views no longer
# write
RETIRED_LABELS = (re.compile(r"^read at +\S"), re.compile(r"^signature +\(.*\) -> \("))


@pytest.mark.parametrize(
    "path",
    STAGE_OBJECT_PAGES + ("docs/overview/05-semantics.md",) + WIKI_PAGES + ("docs/wiki/perch.md",),
    ids=page_id,
)
def test_no_page_writes_a_word_or_a_row_label_that_the_printed_views_no_longer_use(text_of, path):
    """No page of the stage object, the overview of the semantics or a page
    of the wiki writes a word or the label of a row that the printed views no
    longer use."""
    text = text_of(path)
    assert [word for word in RETIRED_PRINTED_WORDS if word in text] == []
    labelled = [
        line for line in text.splitlines() if any(label.match(line) for label in RETIRED_LABELS)
    ]
    assert labelled == []


@pytest.fixture(scope="module")
def package_sources():
    """The text of each module of the package, by its path from the root of
    the repository."""
    folder = ROOT / "packages" / "bellman" / "bellman"
    return {
        path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(folder.rglob("*.py"))
    }


def test_no_module_of_the_package_writes_a_phrase_or_a_row_label_that_the_views_no_longer_use(
    package_sources,
):
    """No module of the package writes a phrase or the label of a row that the
    printed views no longer use."""
    phrases = [
        (path, phrase)
        for path, text in package_sources.items()
        for phrase in RETIRED_IN_SOURCE
        if phrase in text
    ]
    assert phrases == []
    labelled = [
        (path, line)
        for path, text in package_sources.items()
        for line in text.splitlines()
        if any(label.match(line) for label in RETIRED_LABELS)
    ]
    assert labelled == []


# the former names of verbs and of operators: the verbs `face` and `compile`,
# now `view` and `compile_kernel`, the attribute `views`, the queries of the
# inputs and outputs of a view, the builders graph and the initial diagram as
# functions, and the operator that the pullback along the law of motion
# replaced
FORMER_NAMES_OF_VERBS_AND_OPERATORS = (
    "Substitution of the law of motion",
    "face(",
    "compile(",
    ".views",
    "semgraph.view(",
    "view_boundary",
    "graph_boundary",
    "builders_graph",
    "initial_diagram(",
)


@pytest.mark.parametrize("path", ("AGENTS.md",) + WIKI_PAGES, ids=page_id)
def test_neither_agents_md_nor_a_page_of_the_wiki_writes_a_former_name_of_a_verb_or_an_operator(
    text_of, path
):
    """Neither AGENTS.md nor a page of the wiki writes a former name of a
    verb or of an operator, that of a sub-builder among them."""
    text = text_of(path)
    words = FORMER_NAMES_OF_VERBS_AND_OPERATORS + ("Function maker",)
    assert [word for word in words if word in text] == []


def test_the_changelog_names_the_folder_of_the_pages_of_the_stage_object(text_of):
    """The changelog names the folder of the pages of the stage object's
    API."""
    assert "docs/Bellman-Sym/API/stage/" in text_of("docs/changelog.md")


def test_the_entry_of_the_changelog_that_released_the_stage_object_writes_no_former_name(
    text_of,
):
    """The entry of the changelog that released the stage object writes no
    former name of a verb or of an operator and no reading of the policy as a
    parameter of a builder."""
    changelog = text_of("docs/changelog.md")
    # each dated entry keeps the names of its day: the entry of the day before
    # says that its names were renamed, so only the entry that released the
    # stage object is read
    assert "The names in this entry were renamed on 15 September" in changelog
    entry = changelog.partition("### 2026-09-15 — The stage object")[2].split("\n### ", 1)[0]
    assert entry and "initial_diagrams" in entry  # the entry is found
    assert [
        word for word in FORMER_NAMES_OF_VERBS_AND_OPERATORS + PARAMETER_READINGS if word in entry
    ] == []


# --- the navigation of the stage object ---


def test_a_builder_reached_from_its_perch_prints_its_card(cons):
    """The backward builder reached from the decision perch prints the card
    of its box."""
    builder = cons.dcsn.builder.bwd
    assert str(builder) == card(cons, builder.box)


def test_an_operation_of_a_builder_read_by_its_name_prints_its_card_and_its_kernel(
    cons,
):
    """An operation of a builder read by its name as a key prints the card and
    the kernel of its box."""
    box = cons.dcsn.builder.bwd["pullback"]
    assert (str(box), box.kernel()) == (card(cons, box.box), kernel(cons, box.box))


def test_the_pullback_of_a_calibrated_stage_compiles_its_law_of_motion(cons):
    """The pullback of a calibrated copy of `cons` compiles the law of motion
    along which it pulls the continuation value back."""
    calibrated = copy_native(cons).calibrate({"ρ": 2.0})
    # 𝑔(m_d, c) = m_d − c at m_d = 2 and c = 0.5
    assert float(calibrated.dcsn.builder.bwd["pullback"].compile_kernel()(2, 0.5)) == 1.5


def test_a_node_id_reaches_a_sub_builder_as_a_key_and_not_as_an_attribute(sa_savings):
    """A pair of keys, the node id of a sub-builder and the name of an
    operation inside it, reaches that operation, and the node id read as an
    attribute is refused."""
    nested = sa_savings.dcsn.builder.bwd["risk_ce", "expectation:1"]
    assert nested.kernel() == kernel(sa_savings, nested.box)
    with pytest.raises(AttributeError):
        sa_savings.dcsn.builder.bwd.risk_ce


def test_a_key_that_names_no_operation_of_a_builder_is_refused_with_the_key(cons):
    """A key that names no operation of a builder is refused, with the key in
    the message."""
    with pytest.raises(KeyError) as missing:
        cons.dcsn.builder.bwd["no_such_box"]
    assert "no_such_box" in str(missing.value)


def test_a_line_of_a_block_of_the_initial_diagram_prints_its_card(cons):
    """A line of a block of the initial backward diagram, read by its name,
    prints the card of the line."""
    block = cons.initial.backward["cntn_to_dcsn"]
    assert str(block["cntn_to_dcsn.value"]) == card(cons, "cntn_to_dcsn.value")


def test_two_handles_compare_equal_where_they_name_one_piece_of_one_version(cons, cons_methodized):
    """A handle is made when it is asked for, so that two handles of one piece
    of one version are two objects that compare equal, while handles of two
    pieces or of two versions compare unequal."""
    assert cons.dcsn.builder.bwd is not cons.dcsn.builder.bwd
    assert cons.dcsn.builder.bwd == cons.dcsn.builder.bwd
    assert cons.builder.bwd == cons.builder.bwd
    assert cons.initial.backward["cntn_to_dcsn"] != cons.dcsn.builder.bwd
    assert cons_methodized.builder.bwd != cons.builder.bwd  # a different version


def test_the_definitions_list_the_laws_of_motion_of_the_stage_by_their_identities(cons):
    """The listing of the definitions holds, under the kind `g`, the
    identities of the two laws of motion of `cons`."""
    assert cons.definitions.list()["g"] == (
        "cons:g:arvl_to_dcsn",
        "cons:g:dcsn_to_cntn",
    )


def test_the_definitions_print_the_card_of_a_record_named_by_its_identity(cons):
    """The definitions print, for the identity of a record, the card of that
    record."""
    identity = "cons:G:cntn_to_dcsn"
    assert str(cons.definitions.denote(identity)) == card(cons, cons.definitions[identity])


def test_a_builder_and_an_operation_of_a_stage_without_methods_hold_no_methods(cons):
    """A builder and an operation of a stage whose methods are not bound hold
    no methods."""
    builder = cons.dcsn.builder.bwd
    assert builder.methods == {} and builder["pullback"].methods == {}


def test_each_handle_of_a_methodized_stage_holds_the_methods_bound_within_it(
    cons_methodized,
):
    """Each handle of `cons` with its methods file holds the methods of the
    places within it, by place, and an operation with no method holds
    none."""
    stage = cons_methodized
    assert {name: held.word for name, held in stage.dcsn.builder.bwd.methods.items()} == {
        "cntn_to_dcsn.evaluate": "!Linear"
    }
    assert {name: held.word for name, held in stage.builder.policy.methods.items()} == {
        "policy": "!egm"
    }
    assert stage.builder.policy["Evaluation"].methods == {}
    assert {name: held.word for name, held in stage.arvl.builder.fwd.methods.items()} == {
        "arvl_to_dcsn": "!deterministic"
    }


@pytest.mark.parametrize("path", STAGE_OBJECT_PAGES, ids=page_id)
def test_no_page_of_the_stage_object_shows_a_query_that_takes_a_box_as_its_argument(text_of, path):
    """No page of the stage object calls a function that takes a stage and a
    box, or a verb of the stage with an argument."""
    text = text_of(path)
    calls = (
        "to_drawing(",
        "builders_graph(",
        "initial_diagram(",
        "graph_of(",
        "semgraph.record(",
        "card(stage",
        "kernel(stage",
        "compile_kernel(stage",
        "stage.origins(",
        "stage.affine(",
    )
    assert [call for call in calls if call in text] == []
    # the names under which the pages hold a stage; `stage.view()` prints the
    # stage, and `stage.view(box)` is the form that the stage no longer answers
    names = (
        "stage",
        "cons",
        "sa",
        "iid",
        "joint",
        "calibrated",
        "methodized",
        "equal",
        "halved",
    )
    with_argument = [
        text[match.start() : match.end() + 40]
        for name in names
        for verb in ("view", "kernel", "compile_kernel")
        for match in re.finditer(re.escape(f"{name}.{verb}("), text)
        if text[match.end()] != ")"
    ]
    assert with_argument == []


# --- the docstrings of the public answers ---

# the pages of the API that document the stage object: its nine pages and the
# index of the API
DOCUMENTING_PAGES = STAGE_OBJECT_PAGES + ("docs/Bellman-Sym/API/index.md",)


@pytest.fixture(scope="module")
def public_docstrings(cons):
    """`(name, docstring)` of each public record, handle and verb of a stage:
    the printed records and the records of a card, the classes of the stage,
    of its parts and of its pieces, their public functions and properties
    with a docstring, and the verbs of `cons`."""
    # the printed records: the sheets and the listings that a stage prints, and
    # the records of a card, which a card and an encoding present
    listings = "Rows Listing NamedListing SectionedListing Obligations Signature"
    records = [sheets.Sheet, drawing.Drawing]
    records += [getattr(printed_records, name) for name in listings.split()]
    card_records = (
        "TitleBlock Wire Statement Denoted Hypothesis KernelClause ImageByName ImageAtPoint"
        " ImageSet OperatorCard Piece Composite AuthoredCard DefinitionCard StageDenotation"
    )
    records += [getattr(cards, name) for name in card_records.split()]
    parts = [type(cons), type(cons.metadata), type(cons.provenance), type(cons.bindings)]
    handles = "Definitions Graphs GraphHandle BubbleHandle BoxHandle LineHandle"
    answering = [getattr(pieces, name) for name in handles.split()]
    answering += [printed_records.Fields, printed_records.Diagnostics, printed_records.Methods]
    public = records + parts + answering + [Kernel, StageEncoding]
    answers = [(held.__name__, held) for held in public]
    for held in public:
        answers.extend(
            (held.__name__ + "." + name, member)
            for name, member in vars(held).items()
            if not name.startswith("_")
            and (inspect.isfunction(member) or isinstance(member, property))
            and inspect.getdoc(member)
        )
    answers.extend(
        ("stage." + name, getattr(cons, name))
        for name in dir(cons)
        if not name.startswith("_") and callable(getattr(cons, name))
    )
    return [(name, inspect.getdoc(answer)) for name, answer in answers]


def test_the_docstring_of_each_public_answer_names_its_page_of_the_api_and_a_section(
    public_docstrings,
):
    """The docstring of each public record, handle and verb of a stage names
    the index of the API or a page of the stage object, with a section."""
    assert [
        name
        for name, wording in public_docstrings
        if not (wording and any(page in wording for page in DOCUMENTING_PAGES) and "§" in wording)
    ] == []


def test_no_docstring_of_a_public_answer_holds_the_code_of_a_change_record(
    public_docstrings,
):
    """No docstring of a public record, handle or verb of a stage holds the
    code of a change record of the package's development."""
    # `AMD-` begins the code of such a record
    assert [name for name, wording in public_docstrings if "AMD-" in (wording or "")] == []


def test_no_docstring_of_a_public_answer_writes_a_call_that_the_stage_no_longer_answers(
    public_docstrings,
):
    """No docstring of a public record, handle or verb of a stage writes a
    call that the stage object no longer answers."""
    retired = ("definitions.view(", "piece.view(", "operators_of(", "at(grain)")
    assert [
        (name, form)
        for name, wording in public_docstrings
        for form in retired
        if form in (wording or "")
    ] == []


def test_the_docstring_of_the_stage_names_each_of_its_attributes(cons):
    """The docstring of the class of the stage names each of its seven
    attributes."""
    docstring = inspect.getdoc(type(cons))
    attributes = (
        "name",
        "metadata",
        "definitions",
        "initial",
        "_builders",
        "bindings",
        "provenance",
    )
    assert [attribute for attribute in attributes if f"`{attribute}`" not in docstring] == []


# --- the page of the rules ---

# Appendix C, the page that relates the syntax to its semantics: the page of
# the rules, by its path from the root
RULES_PAGE = f"docs/{APPENDIX}"


# the pages of the language, among which the test of the pointers looks
LANGUAGE_PAGES = DOCS / "Bellman-Sym"


# the heading of a numbered section 2.1 to 2.5, or of a numbered rule, of the
# page of the rules
SECTION_HEADING = re.compile(r"^### (2\.\d+|R\d+) ", re.MULTILINE)


# a numbered heading of the page, of the second or the third level, with its
# number: `## 3 The rules`, `### 1.1 Stages, perches, and fields` or the
# heading of a numbered rule
NUMBERED_HEADING = re.compile(r"^(##|###) (\d+(?:\.\d+)?|R\d+) ")


# the marker that opens the printed table of the rules not yet checked
OPENING_MARKER = "<!-- reference-table -->"


def page_sections(text):
    """The text of each numbered section of `text`, the page of the rules, by
    its number, on one line, and the number of the section that holds the
    printed table of the rules not yet checked, None where no section holds
    it. A section runs from its heading to the next numbered heading, and a
    heading inside a fenced block is no heading."""
    sections, label, fenced, table = {}, None, False, None
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        heading = None if fenced else NUMBERED_HEADING.match(line)
        if heading is not None:
            label = heading.group(2)
            sections[label] = []
        elif label is not None:
            sections[label].append(line)
            if line.strip() == OPENING_MARKER:
                table = label
    return {label: " ".join(" ".join(lines).split()) for label, lines in sections.items()}, table


def test_the_rows_of_the_rules_name_exactly_the_numbered_sections_and_rules_of_appendix_c(
    text_of,
):
    """The sections that the rows of `SEMANTIC_RULES` name are the numbered
    sections 2.1 to 2.5 and the numbered rules of Appendix C."""
    page = text_of(RULES_PAGE)
    on_the_page = set(SECTION_HEADING.findall(page))
    assert on_the_page, f"{RULES_PAGE} holds no heading of a section 2.n or of a rule Rn"
    in_the_table = {row.section for row in SEMANTIC_RULES}
    assert in_the_table == on_the_page, (
        f"sections of the page with no row: {sorted(on_the_page - in_the_table)}; "
        f"sections of rows that the page does not hold: {sorted(in_the_table - on_the_page)}"
    )


def test_each_rule_of_the_three_vocabularies_stands_in_a_row_or_among_the_rules_stated_elsewhere():
    """Each rule of the three vocabularies of refusals stands in a row of
    `SEMANTIC_RULES`, or `RULES_STATED_ELSEWHERE` names a page for it."""
    in_rows = {rule for row in SEMANTIC_RULES for rule in row.refusals}
    problems = [
        f"the rule {rule!r} stands in no row and RULES_STATED_ELSEWHERE names no page for it"
        for rule in sorted(every_rule() - in_rows - set(RULES_STATED_ELSEWHERE))
    ]
    assert not problems, problem_lines(problems)


def test_each_rule_stated_elsewhere_is_a_rule_of_the_three_vocabularies():
    """Each rule that `RULES_STATED_ELSEWHERE` names is a rule of the three
    vocabularies of refusals."""
    problems = [
        f"RULES_STATED_ELSEWHERE names {rule!r}, which is no rule of the three vocabularies"
        for rule in sorted(set(RULES_STATED_ELSEWHERE) - every_rule())
    ]
    assert not problems, problem_lines(problems)


def test_each_page_on_which_a_rule_is_stated_elsewhere_stands():
    """Each page that `RULES_STATED_ELSEWHERE` names for a rule stands under
    `docs/`."""
    problems = [
        f"RULES_STATED_ELSEWHERE names the page {page} for {rule!r}, and docs/ holds no such page"
        for rule, page in RULES_STATED_ELSEWHERE.items()
        if not (DOCS / page).is_file()
    ]
    assert not problems, problem_lines(problems)


def test_each_rule_that_a_numbered_section_of_appendix_c_names_stands_in_a_row(text_of):
    """Each rule that a numbered section 2.1 to 2.5 or a numbered rule of
    Appendix C names in a code span stands in a row of `SEMANTIC_RULES`, not
    among the rules stated elsewhere alone."""
    rules = every_rule()
    in_rows = {rule for row in SEMANTIC_RULES for rule in row.refusals}
    page = text_of(RULES_PAGE)
    sections, _ = page_sections(page)
    problems = []
    for label in sorted(set(SECTION_HEADING.findall(page))):
        named = set(re.findall(r"`([a-z][a-z-]*)`", sections[label])) & rules
        problems += [
            f"section {label} of {RULES_PAGE} names the rule {rule!r}, which stands in no row"
            for rule in sorted(named - in_rows)
        ]
    assert not problems, problem_lines(problems)


def test_each_section_and_page_that_a_rule_not_yet_checked_names_stands(text_of):
    """Each section of Appendix C and each page, with its section, that a row
    of a rule not yet checked names stands."""
    sections, _ = page_sections(text_of(RULES_PAGE))
    problems = []
    for where, row in unchecked_rows():
        for label in row.sections:
            if label not in sections:
                problems.append(f"{where}: {RULES_PAGE} holds no section {label}")
        for path, section in row.see_also:
            page = DOCS / path
            if not page.is_file():
                problems.append(f"{where}: docs/ holds no page {path}")
            elif not re.search(
                rf"^#+ {re.escape(section)} ",
                page.read_text(encoding="utf-8"),
                re.MULTILINE,
            ):
                problems.append(f"{where}: docs/{path} holds no section {section}")
    assert not problems, problem_lines(problems)


def test_no_rule_not_yet_checked_that_another_page_states_names_a_numbered_rule_of_appendix_c(
    text_of,
):
    """No row of `UNCHECKED_ELSEWHERE` names a numbered section 2.1 to 2.5 or a
    numbered rule of Appendix C, whose rules are rows of `SEMANTIC_RULES`."""
    in_the_rule_sections = set(SECTION_HEADING.findall(text_of(RULES_PAGE)))
    problems = [
        f"{row.item!r}: a rule of {', '.join(sorted(set(row.sections) & in_the_rule_sections))} "
        f"is a row of SEMANTIC_RULES, and UNCHECKED_ELSEWHERE holds the rules that those "
        f"sections do not state"
        for row in UNCHECKED_ELSEWHERE
        if set(row.sections) & in_the_rule_sections
    ]
    assert not problems, problem_lines(problems)


def test_each_rule_not_yet_checked_that_another_page_states_names_its_section_or_its_page():
    """Each row of `UNCHECKED_ELSEWHERE` names a section or a page that states
    its rule."""
    problems = [
        f"{row.item!r}: the row names no section and no page that states it"
        for row in UNCHECKED_ELSEWHERE
        if not row.sections and not row.see_also
    ]
    assert not problems, problem_lines(problems)


def test_each_section_of_appendix_c_that_points_to_the_table_of_rules_not_yet_checked_is_named(
    text_of,
):
    """Each section of Appendix C that points to its own table of the rules not
    yet checked is named by a row of such a rule."""
    sections, table = page_sections(text_of(RULES_PAGE))
    assert table is not None, (
        f"no numbered section of {RULES_PAGE} holds the marker {OPENING_MARKER} of the "
        f"printed table of the rules not yet checked"
    )
    named_sections = {label for _, row in unchecked_rows() for label in row.sections}
    # a parenthesis that cites the table's section after the other sections
    # that it cites
    own = re.compile(r"\((?:(?:§\d+(?:\.\d+)?|R\d+), )*§" + re.escape(table) + r"\)")
    problems = [
        f"section {label} of {RULES_PAGE} points to §{table} for a rule not yet "
        f"checked, and no row names that section"
        for label, text in sections.items()
        if label != table and own.search(text) and label not in named_sections
    ]
    assert not problems, problem_lines(problems)


def test_each_page_of_the_language_that_points_to_the_table_of_rules_not_yet_checked_is_named(
    text_of,
):
    """Each page of the language that points to the table of the rules not yet
    checked in Appendix C is named by a row of such a rule."""
    _, table = page_sections(text_of(RULES_PAGE))
    assert table is not None, (
        f"no numbered section of {RULES_PAGE} holds the marker {OPENING_MARKER} of the "
        f"printed table of the rules not yet checked"
    )
    named_pages = {path for _, row in unchecked_rows() for path, _ in row.see_also}
    # a parenthesis that links the page of the rules and cites the table's
    # section
    other = re.compile(
        r"\(\[Appendix C\]\([^)]*"
        + re.escape(posixpath.basename(APPENDIX))
        + r"[^)]*\) §"
        + re.escape(table)
        + r"\)"
    )
    pointing, problems = 0, []
    for page in sorted(LANGUAGE_PAGES.rglob("*.md")):
        path = page.relative_to(DOCS).as_posix()
        if path == APPENDIX or not other.search(" ".join(page.read_text("utf-8").split())):
            continue
        pointing += 1
        if path not in named_pages:
            problems.append(
                f"docs/{path} points to §{table} of the page of the rules for a rule not yet "
                f"checked, and no row names that page"
            )
    assert not problems, problem_lines(problems)
    assert pointing, "no page of the language points to the table, so the test finds no pointer"


# --- the refusals ---

# the seven rules whose sentence addresses a Python caller and keeps the names
# of the calls that raise it
PUBLIC_API = (
    "continuation-input",
    "law-requirement",
    "kernel-form",
    "kernel-target",
    "target-not-found",
    "target-ambiguous",
    "target-version",
)


# what no sentence that an author reads holds, each a pattern with its name:
# the codes of the records of the package's development, a section sign, a
# path under the documentation, an em dash
CODES = (
    (r"AMD-", "an amendment code"),
    (r"§", "a section sign"),
    (r"\b[A-Z]\d\d\b", "a decision or an evidence code"),
    (r"\bspec(?:ification)? 0\.\d", "a specification number"),
    (r"docs/", "a documentation path"),
    (r"—", "an em dash"),
)


# what no such sentence holds either where a Python caller does not read it:
# the name of a module, a type, a call or an attribute of Python, an identity
# of the package, and the former vocabulary of the targets of a method
PYTHON = (
    (r"\.py\b", "a module name"),
    (r"\b(?:str|dict|int|float|bool|NoneType)\b", "a Python type name"),
    (r"\bStatement\(|\b(?:FuncDef|CorrDef|Typer)\b", "a term class name"),
    (r"\[\x27|\{\x27", "a Python list or mapping as printed"),
    (
        r"\bload_stage\b|\belaborate_stage\b|\bkernel\(|\bcompile_kernel\b|\.calibration\b"
        r"|\.list\(\)",
        "a Python call or attribute",
    ),
    (
        r"\b\w+:(?:arvl|dcsn|cntn|shck|distribution|function|typing|G|g):\w",
        "an internal identity",
    ),
    (
        r":(?:Expectation|Evaluation|Aggregation|Pullback|Substitution|Derivative|Argmax)\b",
        "an internal identity",
    ),
    (r"Method target", "the retired target vocabulary"),
)


# the Refusals page, which anchors every rule by its name
REFUSALS_PAGE = "docs/Bellman-Sym/reference/refusals.md"


def test_no_refusal_sentence_for_authors_holds_a_code_a_path_a_dash_or_a_python_or_package_name(
    catalogue_entries,
):
    """No sentence of the catalogue of refusals that an author reads holds a
    code of the development or a section sign, a path under `docs/`, an em
    dash, a name of Python or an identity of the package."""
    held = {}
    for each in catalogue_entries:
        if each.rule in PUBLIC_API:
            continue
        # an action of the Bellman factory may name the keyword argument that a
        # Python caller writes, `fill={...}`; every other part is read by an
        # author
        factory = each.vocabulary == "the Bellman factory"
        parts = (
            ("why", each.why, CODES + PYTHON),
            ("write", each.write, CODES if factory else CODES + PYTHON),
        )
        for part, text, patterns in parts:
            for name, matched in patterns_found(text, patterns):
                held[(each.rule, part, name)] = matched
    assert held == {}


def test_the_refusals_page_anchors_every_rule_by_its_name_in_the_order_of_the_vocabularies(
    text_of,
):
    """The Refusals page anchors every rule of the three vocabularies by its
    name, in their order, and nothing else."""
    page = text_of(REFUSALS_PAGE)
    assert re.findall(r'<a id="([^"]+)"></a>', page) == rules_in_order()


def test_the_rules_that_a_python_caller_meets_are_the_seven_whose_sentence_names_a_call():
    """The rules of the class `public-API`, which a Python caller meets, are
    the seven whose sentences may name a call of Python."""
    classes = {rule: class_of(rule) for rule in rules_in_order()}
    assert {rule for rule, held in classes.items() if held == "public-API"} == set(PUBLIC_API)
