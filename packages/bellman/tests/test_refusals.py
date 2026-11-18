"""Refusals: the smallest example of each rule and the catalogue of the
rules, the position and the four parts of a refusal, and its related
locations, the earlier items or the files that a refusal names in its field
`related` beside its own position."""

import io
import re
from contextlib import redirect_stdout
from types import MappingProxyType

import pytest
from application_files import CORPUS, ROOT
from stage_builders import stage_from_text
from stage_texts import branching_text, changed, corpus_text, two_nodes_text_with_changes
from two_sets import one_row_by_default

from bellman import refusal_catalogue
from bellman.__main__ import main
from bellman.refusal_catalogue import VOCABULARIES, entry, refusal_of, text_of
from bellman.refusal_examples import EXAMPLES, INVERSE_EULER, Example, corrected
from bellman.refusals import (
    FACTORY_RULES,
    RULES,
    TARGET_RULES,
    ConstructionError,
    FactoryError,
    NotConstructed,
    TargetError,
)
from bellman.trellis import load_trellis, specify_trellis

# --- the stage texts and the helpers ---

# the value line of the branching stage, after which its tests write a
# derivative line of the choice value
CHOICE_VALUE = "    V = (V_w[>], V_r[>])[d]                :: [id=choice_value]\n"


# the grid line and the identification of the inverse Euler form, which the
# tests of the candidate lines change
GRID_LINE = "    m[>] = a + c[>]        :: [id=grid]\n"


IDENTIFICATION = "    c = c[>]               :: [id=identification]\n"


# the derivative line of the backward value block of the consumption stage
CONS_MARGINAL_LINE = "    D_{m_d}V = 𝑑𝑢(c)                :: [id=marginal]\n"


# a header that writes `!contrl`, a word the vocabulary of the language does
# not hold, in place of `!ctrl`
MISSPELLED_WORD = "@stage: t\n[id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n"


# a stage whose forward measures cannot be built: the distribution of its
# shock names a family that the package does not admit, so the graph is
# refused where the distribution is written
OPAQUE_LAW = """@stage: opaque_law
z : ℝ₊
z ~ Weird(0.2, 0.8)
[id=flow, (x:ℝ₊,z):!arvl -> (y:ℝ₊):!dcsn] { y=x+z }
[id=value, (W:ℝ @ !vlu):!dcsn -> (V:ℝ @ !vlu):!arvl] {
 V=E_{z}(W) :: [id=average]
}
"""


# a settings file whose value of a_min, -1.0, lies outside the declared set
# ℝ₊ of a_min; the key a_min stands on line 3, column 3 of the file
SETTINGS_OUTSIDE_THE_SET = "settings:\n  n_a: 30\n  a_min: -1.0\n  a_max: 20.0\n"


def cons_stage_with(line_as_written, line_as_changed):
    """The consumption stage's text with one line changed, elaborated."""
    text = changed(corpus_text("cons"), (line_as_written, line_as_changed))
    return stage_from_text(text, CORPUS["cons"])


def branching_with_marginal(term):
    """The branching stage with a derivative line of its choice value that
    reads `term` in the branch of work."""
    marginal = f"    D_{{a_d}}V = ({term}, D_{{a_r}}V_r[>])[d]  :: [id=marginal]\n"
    return branching_text((CHOICE_VALUE, CHOICE_VALUE + marginal))


def printed_from_fields(error):
    """The text that `ConstructionError.__str__` prints, built from the
    fields of the refusal: the position, or the file and the address where it
    has none, then the message, then the address and the rule, then one line
    for each related location and one for the action, where the refusal
    carries them."""
    if error.line is None:
        head = f"{error.file}: address {error.address!r}: {error.message} (rule {error.rule})"
    else:
        where = f"{error.file}:{error.line}:{error.column}"
        if error.end_line is not None:
            where += f"-{error.end_line}:{error.end_column}"
        if error.address is None:
            head = f"{where}: {error.message} (rule {error.rule})"
        else:
            head = f"{where}: {error.message} (address {error.address!r}; rule {error.rule})"
    after = "".join(f"\n  {location}" for location in error.related)
    if error.write:
        after += f"\n  write: {error.write}"
    return head + after


def position(error):
    """The file, the range and the address of a refusal."""
    return error.file, error.line, error.column, error.end_line, error.end_column, error.address


# --- the words of the refusals ---

# The phrases by which a sentence would misname a term of the documentation:
# `value block` or `value builder` for a backward block; `transition g`,
# `transition from`, `transition defines` or `forward transition` for the law
# of motion or for the edge on which a shock is drawn; and `law` or `laws`
# alone for the distribution of a shock. `law` in `law of motion` or `laws of
# motion`, and `law` joined by a hyphen to the word before it, are no such
# phrase, and the word `transition` in any other phrase, such as
# `transition block`, is not read.
MISNAMING_PHRASES = re.compile(
    r"value block|value builder|transition g\b|\btransition (?:from|defines)"
    r"|\bforward transition|(?<!-)\blaws?\b(?! of motion)"
)


@pytest.fixture(scope="module")
def sentence_by_rule(catalogue_entries):
    """The sentence of the refusal that the example of each rule provokes, by
    the rule, as the catalogue gives it, in a mapping that no test can
    change."""
    return MappingProxyType({item.rule: item.why for item in catalogue_entries})


def test_no_catalogue_sentence_misnames_a_backward_block_law_of_motion_edge_or_distribution(
    sentence_by_rule,
):
    """No sentence of a refusal that the catalogue provokes holds a phrase of
    `MISNAMING_PHRASES`: none calls a backward block a value block or a
    value builder, the law of motion or an edge a transition, or writes
    `law` alone, outside `law of motion`, as for a distribution."""
    assert [
        sentence for sentence in sentence_by_rule.values() if MISNAMING_PHRASES.search(sentence)
    ] == []


@pytest.mark.parametrize(
    "declarations, backward",
    [
        pytest.param(
            "y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\ny ~ N(0,2)\n",
            None,
            id="a-second-distribution-of-y",
        ),
        pytest.param(
            "y ~ N(0,1)\nz : ℝ\n(y, z) ~ N((0,0),((1,0),(0,1)))\n",
            None,
            id="y-again-in-a-joint-distribution",
        ),
        pytest.param(
            "y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\nq : ℝ\n",
            "    V = E_{q}(V[>]) :: [id=value]\n",
            id="an-expectation-over-q-which-has-no-distribution",
        ),
    ],
)
def test_a_distribution_refusal_misnames_no_backward_block_law_of_motion_edge_or_distribution(
    declarations, backward
):
    """The refusal of a shock given two distributions, or read in an
    expectation without one, holds no phrase of `MISNAMING_PHRASES`: it
    calls no backward block a value block or a value builder, neither the
    law of motion nor an edge a transition, and writes `law` alone nowhere,
    outside `law of motion`."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_changes(declarations=declarations, backward=backward))
    assert MISNAMING_PHRASES.findall(refused.value.message) == []


def test_the_refusal_of_a_transition_without_an_expectation_asks_for_a_backward_block(
    sentence_by_rule,
):
    """The sentence of the refusal under `transition-without-expectation`
    ends by naming the law of motion 𝑔 and a backward block."""
    assert sentence_by_rule["transition-without-expectation"].endswith(
        "through the law of motion 𝑔 and takes no expectation; "
        "write the integration in a backward block"
    )


@pytest.mark.parametrize(
    "rule, phrase",
    [
        pytest.param(
            "shock-observed",
            "; the edge from the arvl perch to the dcsn perch draws the shock y,",
            id="the-edge-that-draws-a-shock",
        ),
        pytest.param(
            "forward-composite",
            "Write the cntn-perch field the law of motion defines",
            id="the-law-of-motion",
        ),
        pytest.param(
            "branch-law",
            "has no distribution; the branches are weighted by the distribution of the shock",
            id="the-distribution-of-a-shock",
        ),
    ],
)
def test_a_refusal_names_the_edge_the_law_of_motion_or_the_distribution_of_a_shock(
    sentence_by_rule, rule, phrase
):
    """The sentence of the refusal of each of three rules names the edge on
    which a shock is drawn, the law of motion or a shock's distribution."""
    assert phrase in sentence_by_rule[rule]


# --- the smallest example of each rule ---


@pytest.mark.parametrize("rule", RULES)
def test_the_smallest_example_breaking_a_rule_of_construction_is_refused_under_it(rule):
    """The example of a rule of graph construction provokes a refusal under
    that rule, at the example's address in its file, whose sentence holds the
    example's words and whose printed text is the one its fields give."""
    example = EXAMPLES[rule]
    error = refusal_of(example)
    assert isinstance(error, ConstructionError), rule
    assert (error.rule, error.address) == (rule, example.address)
    assert error.file == example.origin
    assert [word for word in example.words if word not in error.message] == []
    assert str(error) == printed_from_fields(error)


# the rules whose example compiles a kernel of the built stage
COMPILATION_RULES = [rule for rule in RULES if EXAMPLES[rule].provokes == "compile_kernel"]


@pytest.mark.parametrize("rule", COMPILATION_RULES)
def test_a_refusal_of_compile_kernel_names_no_line_of_the_file(rule):
    """A refusal raised when a kernel of the built stage is compiled names
    no line of the file, since the stage keeps no position after its
    construction."""
    error = refusal_of(EXAMPLES[rule])
    assert error.rule == rule
    assert error.line is None


@pytest.mark.parametrize("rule", TARGET_RULES)
def test_the_smallest_example_breaking_a_rule_for_the_names_of_pieces_is_refused_under_it(rule):
    """The example of a rule for a name given to a query of the stage object
    is refused under that rule, naming the example's target and stage, with
    the example's words."""
    example = EXAMPLES[rule]
    error = refusal_of(example)
    assert isinstance(error, TargetError), rule
    assert (error.rule, error.target) == (rule, example.address)
    assert error.stage == example.corpus
    assert [word for word in example.words if word not in str(error)] == []


@pytest.mark.parametrize("rule", FACTORY_RULES)
def test_the_smallest_example_breaking_a_rule_of_the_factory_is_refused_under_it(rule):
    """The example of a rule of the Bellman factory provokes a refusal under
    that rule at the example's address, which holds the example's words,
    what stands there and what to write, and whose printed text closes with
    the rule."""
    example = EXAMPLES[rule]
    error = refusal_of(example)
    assert isinstance(error, FactoryError), rule
    assert (error.rule, error.address) == (rule, example.address)
    assert [word for word in example.words if word not in error.message] == []
    assert error.written and error.write, rule
    assert str(error).endswith(f"(rule {rule})")


# --- the catalogue ---


def test_the_catalogue_lists_every_rule_of_the_three_vocabularies_in_their_order(
    catalogue_entries,
):
    """The catalogue lists the rules of graph construction, then those of
    the names of the pieces, then those of the Bellman factory."""
    assert [item.rule for item in catalogue_entries] == (
        list(RULES) + list(TARGET_RULES) + list(FACTORY_RULES)
    )


def test_the_example_of_every_rule_is_refused_and_its_corrected_form_is_not(catalogue_entries):
    """The example of every rule of the catalogue provokes a refusal, and
    its corrected form passes the operation that refused the example."""
    without = [item.rule for item in catalogue_entries if not item.refusal]
    assert without == [], without
    assert {item.rule: item.corrected for item in catalogue_entries if item.corrected} == {}


@pytest.mark.parametrize("rule", FACTORY_RULES)
def test_the_entry_of_a_rule_of_the_factory_gives_the_four_parts_of_its_refusal(
    catalogue_entries, rule
):
    """The catalogue entry of a rule of the Bellman factory gives where,
    what, why and what to write of the refusal of its example."""
    (item,) = [item for item in catalogue_entries if item.rule == rule]
    assert all((item.where, item.what, item.why, item.write)), item.rule


def test_every_example_gives_an_edit():
    """Every example of the package gives an edit of its fields, `write`,
    which is not empty."""
    assert [name for name, example in EXAMPLES.items() if not example.write] == []


# the examples that are no rule's own example in the catalogue: a second
# example of a rule, which the catalogue does not run
SECOND_EXAMPLES = [name for name in EXAMPLES if name not in RULES + TARGET_RULES + FACTORY_RULES]


@pytest.mark.parametrize("name", SECOND_EXAMPLES)
def test_a_second_example_of_a_rule_is_refused_and_its_corrected_form_is_not(name):
    """A second example of a rule provokes a refusal, and its corrected form
    passes the operation that refused the example."""
    example = EXAMPLES[name]
    assert refusal_of(example) is not None
    refusal = refusal_of(corrected(example))
    assert refusal is None, str(refusal).splitlines()[0]


# the checkout row runs every example and takes over two seconds
@pytest.mark.parametrize(
    "installed", one_row_by_default([False, True], default=True), ids=["checkout", "installed"]
)
def test_entry_answers_every_rule_from_the_checkout_or_the_installed_package(
    installed, tmp_path, monkeypatch
):
    """`entry(rule)` answers each rule of the three vocabularies with its
    vocabulary, its operation, its condition and the refusal of its example
    under the rule, or, from the installed package, the reason that an
    example reading a stage file of the repository is not run."""
    # the installed package is outside the checkout: the repository's root,
    # from which an example reads a stage file, is an empty folder
    if installed:
        monkeypatch.setattr(refusal_catalogue, "ROOT", tmp_path)
    wrong = {}
    for _, _, table in VOCABULARIES:
        for rule in table:
            found = entry(rule)
            example = EXAMPLES[rule]
            if installed and (example.corpus or example.stages):
                answered = not found.refusal and bool(found.why)
            else:
                answered = bool(found.refusal) and refusal_of(example).rule == rule
            if not (found.vocabulary and found.operation and found.condition and answered):
                wrong[rule] = (found.operation, found.why)
    assert wrong == {}


def test_a_name_that_no_vocabulary_holds_has_no_entry():
    """`entry` answers None for a name that no vocabulary holds, such as
    `unread-input`, the rule of a diagnostic."""
    assert entry("unread-input") is None


# --- the position and the four parts of a refusal under syntax ---


def test_the_refusal_of_the_syntax_example_prints_its_line_with_a_mark_under_its_column():
    """The refusal of the consumption stage with `]` closing a side of a
    header is printed from line 16, column 40 of `cons.bl`, with the text of
    that line and a mark under the column."""
    example = EXAMPLES["syntax"]
    error = refusal_of(example)
    assert (error.file, error.line, error.column) == ("cons.bl", 16, 40)
    assert str(error).startswith("cons.bl:16:")
    # line 16 of the changed text
    assert text_of(example).splitlines()[15] in str(error)
    # the line is printed indented by four spaces, so the mark stands four
    # places to the right of its column
    assert "\n" + " " * (4 + error.column - 1) + "^" in str(error)


def test_a_syntax_refusal_gives_the_grammars_sentence_as_its_action_and_not_in_its_message():
    """The refusal of the syntax example gives the sentence that the grammar
    keeps for a side of a block header as its action, which its message does
    not repeat."""
    error = refusal_of(EXAMPLES["syntax"])
    assert "a side of a block header" in error.write and error.write not in error.message


def test_a_word_the_vocabulary_does_not_hold_is_refused_under_syntax_at_the_word():
    """A header that writes `!contrl` is refused under `syntax` over the
    columns of that word, in a sentence that names it."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(MISSPELLED_WORD)
    error = refused.value
    # the seven characters of `!contrl` stand on line 2 from column 18, and
    # the range ends at column 25
    assert (error.rule, position(error)) == ("syntax", ("t.bl", 2, 18, 2, 25, None))
    assert "!contrl" in error.message


# three texts of the parser that a refusal under `syntax` does not print: the
# opening of the error that the parsing library raises when a step of the
# reading fails, and the rule `word_type` and the token `TAGBANG` of the
# grammar of the language
PARSER_NAMES = ("Error trying to process rule", "word_type", "TAGBANG")


@pytest.mark.parametrize(
    "example",
    [
        EXAMPLES["syntax"],
        Example(rule="syntax", address=None, words=(), text=MISSPELLED_WORD),
    ],
    ids=["a-side-closed-by-a-bracket", "a-word-the-vocabulary-does-not-hold"],
)
def test_a_syntax_refusal_prints_neither_the_parsers_error_text_nor_two_names_of_its_grammar(
    example,
):
    """A refusal under `syntax` prints neither `Error trying to process
    rule`, the opening of an error of the parsing library, nor `word_type`
    and `TAGBANG`, two names of the grammar."""
    error = refusal_of(example)
    assert error.rule == "syntax"
    assert [name for name in PARSER_NAMES if name in str(error)] == []


# Forms that the parser reads and the language gives no meaning, each refused
# under `syntax` where it is written: the text after the `@stage: t` line,
# the line and the column of the refusal, the words of its sentence and the
# words of its action.
FORMS_REFUSED_UNDER_SYNTAX = [
    pytest.param(
        "k : ℝ\n[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = (1, 2)[k + 1]\n}\n",
        4,
        9,
        ("`(1, 2)[k + 1]`", "selects by `k + 1`", "a position or a name"),
        "`(1, 2)[1]`",
        id="a computed selector",
    ),
    pytest.param(
        "[id=b, (x[1] : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        2,
        9,
        ("`x[1]`", "a selection from x", "by its name"),
        "`x[>]`",
        id="a selection on the side of a header",
    ),
    pytest.param(
        "x[1] : ℝ\n",
        2,
        1,
        ("`x[1]`", "a selection from x"),
        "`x : …`",
        id="a selection declared",
    ),
    pytest.param(
        "x : ℝ\nx[1] ~ N(0, 1)\n",
        3,
        1,
        ("`x[1]`", "names its shocks by name"),
        "`x ~ …`",
        id="a selection given a distribution",
    ),
    pytest.param(
        "Γ(x : ℝ) := {c : !ctrl | c < x}\n",
        2,
        13,
        ("`{c : !ctrl | c < x}`", "typed by `!ctrl`", "one set"),
        "`{c : ℝ₊ | …}`",
        id="a comprehension binder typed by a role word",
    ),
    pytest.param(
        "γ : ℝ₊, < 2\n",
        2,
        1,
        ("`γ < 2`", "after a comma", "retired"),
        "`ℝ₊ @ (-inf, 2)`",
        id="a bound written after a comma",
    ),
    pytest.param(
        "γ : ℝ₊ @ ℤ\n",
        2,
        1,
        ("`ℝ₊`", "`ℤ`", "are no intervals"),
        "`γ : ℝ₊ @ (0, 1)`",
        id="two sets of one type that are no intervals",
    ),
    pytest.param(
        "γ : {a, b} @ (0, 1)\n",
        2,
        1,
        ("`{a, b}`", "a set of labels"),
        "the one set γ takes its values in",
        id="a set of labels with an interval",
    ),
    pytest.param(
        "(γ, δ) : ℝ₊ × ℝ₊, < 2\n",
        2,
        1,
        ("`< 2`", "after a comma", "retired"),
        "`γ : ℝ₊ @ (-inf, 2)`",
        id="a bound after a comma on two names",
    ),
    pytest.param(
        "(γ, δ) : ℝ₊ × ℝ₊ @ (0, 1)\n",
        2,
        1,
        ("of (γ, δ) carries", "one declared name"),
        "each name on its own line",
        id="several sets on a declaration of two names",
    ),
    pytest.param(
        "[id=b, (x : ℝ) : !dcsn -> (y : ℝ, w : ℝ) : !dcsn] {\n"
        "    y = x :: [id=same]\n    w = x :: [id=same]\n}\n",
        4,
        5,
        ("'b.same'", "the first at t.bl:3:5"),
        "another id",
        id="two lines under one id",
    ),
]


# four texts that a refusal under `syntax` does not print: `@in`, a spelling
# of membership that the language no longer reads and that no sentence of
# the package now writes; `Select(` and `Sym(`, the openings of the printed
# forms of two terms of the package; and `NotImplementedError`, an error of
# Python
INTERNAL_TEXTS = ("@in", "Select(", "Sym(", "NotImplementedError")


@pytest.mark.parametrize("body, line, column, words, write", FORMS_REFUSED_UNDER_SYNTAX)
def test_a_form_the_parser_reads_but_the_language_does_not_is_refused_where_it_is_written(
    body, line, column, words, write
):
    """A form that the parser reads and the language gives no meaning is
    refused under `syntax` at its line and column, in a sentence that quotes
    the text as written, an action that says what to write, a marked line,
    and none of the four texts of `INTERNAL_TEXTS`."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text("@stage: t\n" + body)
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", line, column)
    assert all(word in error.parts.why for word in words), (words, error.parts.why)
    assert write in error.write and "^" in error.parts.what
    assert [text for text in INTERNAL_TEXTS if text in str(error)] == []


# --- the refusals of graph construction beside their acceptances ---


def test_a_field_defined_twice_in_a_block_is_refused_unless_the_first_is_documentation():
    """A block that defines W on two lines marked `!node` is refused at the
    second line, and the same block with its first line marked `!doc` is
    admitted."""
    example = EXAMPLES["defined-once"]
    error = refusal_of(example)
    assert error.rule == "defined-once"
    # the second definition of W stands on line 4, indented by four spaces
    assert (error.line, error.column) == (4, 5)
    documentary = example.text.replace("[id=first, !node]", "[id=first, !doc]")
    assert stage_from_text(documentary).name == "t"


def test_the_entry_of_defined_once_gives_the_four_parts_of_the_refusal_of_its_example():
    """The catalogue entry of `defined-once` gives the position, the marked
    line, the sentence and the action of the refusal of its example."""
    error = refusal_of(EXAMPLES["defined-once"])
    held = entry("defined-once")
    assert held.where == "t.bl, line 4, column 5 (address 'b.second')"
    assert "W = 2*V[>]" in held.what and "^" in held.what
    assert held.why == error.message
    assert "t.bl:3:5 (term address 'b.first')" in held.why
    assert held.write == error.write
    phrases = ("Remove one of the two definitions of W", "another name", "`!doc`")
    assert [phrase for phrase in phrases if phrase not in held.write] == []


def test_a_derivative_stated_twice_in_one_block_is_refused_at_the_second_line_naming_the_first():
    """The consumption stage with a second derivative line for D_{m_d}V in its
    backward value block is refused at that line, in a sentence that names
    the first."""
    second = "    D_{m_d}V = 2*𝑑𝑢(c)              :: [id=marginal2]\n"
    with pytest.raises(ConstructionError) as refused:
        cons_stage_with(CONS_MARGINAL_LINE, CONS_MARGINAL_LINE + second)
    assert (refused.value.rule, refused.value.address) == (
        "defined-once",
        "cntn_to_dcsn.marginal2",
    )
    assert "block 'cntn_to_dcsn' already states D_{m_d}V at" in refused.value.message
    assert "(term address 'cntn_to_dcsn.marginal')" in refused.value.message


# Each address below is the term address of the item that names the set: for
# a top-level item, its order among the items of the consumption stage,
# counting the `@stage` line as the first.
@pytest.mark.parametrize(
    "line_as_written, line_as_changed, address, named_by",
    [
        pytest.param(
            "ρ : [1, inf)\n",
            "ρ : [1, inf)\nn_m : Foo\n",
            "5",
            "the declaration of 'n_m'",
            id="a-declaration",
        ),
        pytest.param(
            "(m_d, c : !ctrl @ ℝ₊₊) : !dcsn",
            "(m_d, c : !ctrl @ Foo) : !dcsn",
            "dcsn_to_cntn",
            "the header of block 'dcsn_to_cntn', which types c",
            id="a-block-header",
        ),
        pytest.param(
            "𝑑𝑢(c : ℝ₊₊) := c^(-ρ)",
            "𝑑𝑢(c : Foo) := c^(-ρ)",
            "6",
            "the argument 'c' of the function '𝑑𝑢'",
            id="an-argument-of-a-function",
        ),
        pytest.param(
            "Xa := ℝ₊\n",
            "Xa := ℝ₊\nXq := Xm × Foo\n",
            "4",
            "the definition of the set 'Xq'",
            id="a-factor-of-a-product-set",
        ),
    ],
)
def test_a_set_the_stage_does_not_define_is_refused_where_it_is_named_with_the_sets_in_scope(
    line_as_written, line_as_changed, address, named_by
):
    """The consumption stage with a set `Foo` that it does not define is
    refused under `name-in-scope` at the item that names the set, in a
    sentence that lists the sets in scope there and the primitive sets."""
    with pytest.raises(ConstructionError) as refused:
        cons_stage_with(line_as_written, line_as_changed)
    assert (refused.value.rule, refused.value.address) == ("name-in-scope", address)
    assert f"{named_by} names the set 'Foo'" in refused.value.message
    assert "the sets in scope here: Xm, Xa" in refused.value.message
    assert "ℝ, ℝ₊, ℝ₊₊, ℤ, ℕ" in refused.value.message


# The addresses are term addresses, counted as in the table above.
@pytest.mark.parametrize(
    "line_as_written, line_as_changed, address, named_by, function",
    [
        pytest.param(
            "ρ : [1, inf)\n",
            "ρ : [1, inf)\nn_m : 𝑑𝑢\n",
            "5",
            "the declaration of 'n_m'",
            "𝑑𝑢",
            id="a-declaration",
        ),
        pytest.param(
            "Xa := ℝ₊\n",
            "Xa := ℝ₊\nXq := Xm × 𝑑𝑢\n",
            "4",
            "the definition of the set 'Xq'",
            "𝑑𝑢",
            id="a-factor-of-a-product-set",
        ),
        pytest.param(
            "Γ(x : ℝ₊₊) := (0, x]\n",
            "Γ(x : ℝ₊₊) := (0, x]\n𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\nn_m : 𝑑𝑢𝑖𝑛𝑣\n",
            "9",
            "the declaration of 'n_m'",
            "𝑑𝑢𝑖𝑛𝑣",
            id="a-declaration-by-a-function-defined-as-an-inverse",
        ),
    ],
)
def test_a_function_of_the_stage_written_where_a_set_stands_is_refused_naming_its_definition(
    line_as_written, line_as_changed, address, named_by, function
):
    """The consumption stage with a function of its own written where a set
    stands is refused under `name-in-scope` at the item, in a sentence that
    names the function and its definition."""
    with pytest.raises(ConstructionError) as refused:
        cons_stage_with(line_as_written, line_as_changed)
    assert (refused.value.rule, refused.value.address) == ("name-in-scope", address)
    assert (
        f"{named_by} names the set {function!r}, which the stage defines as a function at"
        in refused.value.message
    )
    assert "and as no set" in refused.value.message


def test_a_call_to_a_function_the_file_does_not_declare_is_recorded_as_a_condition():
    """The consumption stage whose derivative line calls 𝑓𝑜𝑜, a function
    that the file does not declare, is admitted and states the condition
    `external-callable-signature-and-provider`."""
    stage = cons_stage_with(CONS_MARGINAL_LINE, CONS_MARGINAL_LINE.replace("𝑑𝑢(c)", "𝑓𝑜𝑜(c)"))
    assert "external-callable-signature-and-provider" in {
        obligation.condition for obligation in stage.obligations()
    }


def test_a_derivative_of_a_branch_value_is_taken_only_in_the_coordinates_of_that_branch():
    """In the branching stage, a derivative of the value of the branch of
    work in the coordinate a_r of the branch of retirement is refused,
    naming the branch and its coordinates, where the coordinate a_w of the
    branch of work is admitted."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(branching_with_marginal("D_{a_r}V_w[>]"))
    assert (refused.value.rule, refused.value.address) == (
        "derivative-coordinate",
        "cntn_to_dcsn.marginal",
    )
    assert (
        "names 'a_r', which is no state coordinate of the branch 'work' of the cntn perch"
        in refused.value.message
    )
    assert (
        "the coordinates of the branch 'work' of the cntn perch are a_w" in refused.value.message
    )
    assert stage_from_text(branching_with_marginal("D_{a_w}V_w[>]")).name == "t"


def test_a_value_candidate_is_admitted_only_where_an_upper_envelope_compares_it():
    """The inverse Euler form with a value candidate v[>] after its grid
    line is admitted where an upper envelope compares the candidates, and
    refused at the value candidate where none does."""
    value_candidate = GRID_LINE + "    v[>] = 𝑢(c[>]) + V[>]    :: [id=cand_value]\n"
    envelope = "    c = upper_env(m[>], c[>], v[>])    :: [id=envelope]\n"
    with_envelope = INVERSE_EULER.replace(GRID_LINE, value_candidate).replace(
        IDENTIFICATION, envelope
    )
    assert stage_from_text(with_envelope).name == "t"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(INVERSE_EULER.replace(GRID_LINE, value_candidate))
    assert (refused.value.rule, refused.value.address) == (
        "candidate-coordinate",
        "policy.cand_value",
    )
    assert "writes v[>], a candidate of 'v'" in refused.value.message
    assert "no upper envelope of block 'policy' compares it" in refused.value.message


def test_the_grid_line_reads_the_candidate_of_the_control_and_needs_no_reader_itself():
    """The inverse Euler form with its control in closed form is refused
    where no later line reads the candidate c[>], and admitted with the
    grid line, which reads c[>] and which no later line reads, since the
    Evaluation reads it as the knots of the policy."""
    closed = "    c = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])     :: [id=closed]\n"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(INVERSE_EULER.replace(GRID_LINE + IDENTIFICATION, closed))
    assert (refused.value.rule, refused.value.address) == ("candidate-read", "policy.InvEuler")
    assert stage_from_text(INVERSE_EULER.replace(IDENTIFICATION, closed)).name == "t"


@pytest.mark.parametrize(
    "block, address, first",
    [
        pytest.param(
            "[id=value2, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
            "    V = 2*𝑢(c) + V[>]    :: [id=value]\n}\n",
            "value2",
            "cntn_to_dcsn",
            id="a-second-backward-block-writing-the-value",
        ),
        pytest.param(
            "[id=step2, (m, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n    a = m - 2*c\n}\n",
            "step2",
            "dcsn_to_cntn",
            id="a-second-forward-block-writing-the-saving",
        ),
    ],
)
def test_a_second_block_writing_a_field_between_the_same_perches_is_refused(block, address, first):
    """The inverse Euler form with a second block that writes the output of
    one of its blocks between the same two perches is refused under
    `one-builder-per-output` at the second block, naming the first."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(INVERSE_EULER + block)
    assert (refused.value.rule, refused.value.address) == ("one-builder-per-output", address)
    assert f"which block '{first}' already writes" in refused.value.message


def test_a_forward_graph_the_construction_refused_names_its_file_its_position_and_its_rule():
    """The forward builders graph of a stage whose shock has a distribution
    of a family the package does not admit is refused at the line of that
    distribution, the address of its declaration and the rule
    `not-constructed`."""
    with pytest.raises(NotConstructed) as refused:
        stage_from_text(OPAQUE_LAW).builder.fwd.list()
    error = refused.value
    # the distribution `z ~ Weird(0.2, 0.8)` stands on line 3
    assert (error.stage, error.address, error.rule, error.line, error.column) == (
        "opaque_law",
        "t.bl:3",
        "not-constructed",
        3,
        1,
    )
    assert str(error).startswith(
        "t.bl:3:1-3:20: the forward measures are not constructed: the distribution of z "
        "is written with the family 'Weird'"
    )
    assert str(error).endswith("(address 't.bl:3'; rule not-constructed)")


def test_a_refusal_with_no_position_and_no_address_ends_its_text_with_its_rule():
    """The text of a refusal that names a rule ends with that rule in
    parentheses."""
    named = NotConstructed("no forward builder", rule="not-constructed")
    assert str(named).endswith("(rule not-constructed)")


# Two stage texts after their `@stage: t` line, each with a line `LINE` that
# the rows below replace: two functions 𝑓 and 𝑔 and a parameter β, read in
# the line of a forward block, which is line 6 of the file; and a shock y,
# read in the backward value line, which is line 11 of the file.
FUNCTIONS_AND_A_FORWARD_LINE = (
    "𝑓(x : ℝ₊) := x + 1\n𝑔(x : ℝ × ℝ) := x[1]\nβ : ℝ₊₊\n"
    "[id=b, (v : ℝ₊) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = LINE\n}\n"
)


SHOCK_AND_A_VALUE_LINE = (
    "y : ℝ\ny ~ N(0, 1)\n"
    "[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (k_d : ℝ) : !dcsn] {\n    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d, y) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d + y\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = LINE\n}\n"
    "[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
)


# The faults found when a line is typed, each refused at the line under its
# rule: the text after the `@stage: t` line, the rule, the line and the words
# of the sentence.
TYPING_REFUSALS = [
    pytest.param(
        FUNCTIONS_AND_A_FORWARD_LINE.replace("LINE", "𝑓 + 1"),
        "well-typed",
        6,
        ("`𝑓` is a function", "`𝑓 + 1` reads it as a number", "`𝑓(…)`"),
        id="a function used as a number",
    ),
    pytest.param(
        SHOCK_AND_A_VALUE_LINE.replace("LINE", "E_{y, y}(V[>])"),
        "declared-once",
        11,
        ("`E_{y, y}(V[>])` names y twice", "`E_{y}(…)`"),
        id="a binder named twice",
    ),
    pytest.param(
        FUNCTIONS_AND_A_FORWARD_LINE.replace("LINE", "Inv(β)"),
        "well-typed",
        6,
        ("`Inv(β)` inverts a number", "one function"),
        id="Inv of a number",
    ),
    pytest.param(
        FUNCTIONS_AND_A_FORWARD_LINE.replace("LINE", "𝑔(v)"),
        "well-typed",
        6,
        ("argument 1 of the call to 𝑔 is a number", "a tuple of values"),
        id="a function of a pair applied to a number",
    ),
    pytest.param(
        FUNCTIONS_AND_A_FORWARD_LINE.replace("LINE", "𝑓"),
        "well-typed",
        6,
        ("the right side of `w = 𝑓` is a function", "the left side a number"),
        id="the two sides of a line of two kinds",
    ),
    pytest.param(
        "[id=b, (d : {keep, adjust}) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = d + 1\n}\n",
        "well-typed",
        3,
        ("`d` is a label", "`d + 1` reads it as a number"),
        id="arithmetic on a label",
    ),
]


@pytest.mark.parametrize("body, rule, line, words", TYPING_REFUSALS)
def test_a_fault_found_when_a_line_is_typed_is_refused_at_the_line_under_its_rule(
    body, rule, line, words
):
    """A line whose terms are of kinds that its operations do not take, or
    that binds a name twice, is refused under its rule where the line
    begins, in the package's own sentence with the row's words, which holds
    neither `requires scalar operands` nor `task file`."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text("@stage: t\n" + body)
    error = refused.value
    # each line is indented by four spaces, so it begins at column 5
    assert (error.rule, error.line, error.column) == (rule, line, 5), (error.rule, error.line)
    assert all(word in error.message for word in words), (words, error.message)
    # the texts of two plain errors that the typing raised before it refused
    # a fault of a line under a rule; no code of the package writes either
    # text now, and a fault of a line is refused with the package's own
    # sentence
    assert "requires scalar operands" not in error.message and "task file" not in error.message


# --- the related locations of a refusal ---

# A related location is a `Location` of the field `related` of a refusal: an
# earlier item or a file that the refusal names beside the item it stands
# at, under a role that says what it is: `original declaration` for the
# earlier of two items written twice, `rejected setting` for the key of a
# settings file and `settings source` for the settings file itself. The
# refusal prints each related location on a line of its own after its
# sentence.


# The four refusals of the union of a stage file with a methods file, each
# raised at the later item and naming the earlier one as its original
# declaration: the rule, the later item's file, range and address, and the
# earlier item's file and address.
@pytest.mark.parametrize(
    "rule, later, file, address",
    [
        pytest.param(
            "declared-twice",
            ("m.bl", 2, 29, 2, 49, "policy.policy.method"),
            "m.bl",
            "policy.method",
            id="declared-twice",
        ),
        pytest.param(
            "label-not-in-parent",
            ("m.bl", 3, 5, 5, 6, "dcsn_to_cntn.rent"),
            "t.bl",
            "dcsn_to_cntn",
            id="label-not-in-parent",
        ),
        pytest.param(
            "type-conflict",
            ("m.bl", 2, 26, 2, 38, "cntn_to_dcsn.out.V"),
            "t.bl",
            "cntn_to_dcsn.out.V",
            id="type-conflict",
        ),
        pytest.param(
            "metadata-mismatch",
            ("m.bl", 1, 1, 1, 15, "1"),
            "t.bl",
            "1",
            id="metadata-mismatch",
        ),
    ],
)
def test_a_refusal_of_a_methods_file_names_the_earlier_item_as_its_original_declaration(
    rule, later, file, address
):
    """A refusal of the union of a stage file with a methods file stands at
    the later item and names the earlier item as its original declaration,
    by position in its sentence and on a line of its own after the first."""
    error = refusal_of(EXAMPLES[rule])
    assert (error.rule, position(error)) == (rule, later)
    (earlier,) = error.related
    assert (earlier.role, earlier.file, earlier.address) == ("original declaration", file, address)
    assert None not in (earlier.line, earlier.column, earlier.end_line, earlier.end_column)
    assert f"{earlier.file}:{earlier.line}:{earlier.column} (term address {address!r})" in (
        error.message
    )
    assert str(error).splitlines()[0].endswith(f"(address {later[-1]!r}; rule {rule})")
    assert f"\n  {earlier}" in str(error)


def test_a_refusal_prints_its_original_declaration_and_then_its_action_on_lines_of_their_own():
    """The refusal of a methods file that names the stage `port` for the
    consumption stage prints, after its first line, the `@stage` line as its
    original declaration and then its action."""
    error = refusal_of(EXAMPLES["metadata-mismatch"])
    # the line `@stage: cons`, of twelve characters, stands from column 1 to
    # column 13 of line 1
    assert tuple(error.related[0]) == ("original declaration", "t.bl", 1, 1, 1, 13, "1")
    assert error.write == "Write `@methods: cons`"
    assert str(error).endswith(
        "\n  original declaration: t.bl:1:1-1:13 (address '1')\n  write: Write `@methods: cons`"
    )


def test_a_key_written_twice_in_a_trellis_file_is_refused_at_the_second_naming_the_first(
    tmp_path,
):
    """A trellis file that writes the key `periods` twice is refused under
    `trellis-file-shape` at the second key, with the first as its original
    declaration."""
    trellis = tmp_path / "trellis.yml"
    trellis.write_text(
        f"periods:\n  - stages:\n      cons: {{stage: {ROOT / CORPUS['cons']}}}\n"
        "    connectors: []\nperiods: []\ninter_connectors: []\n",
        encoding="utf-8",
    )
    with pytest.raises(FactoryError) as refused:
        load_trellis(trellis)
    error = refused.value
    # the second key `periods` stands on line 5, the first on line 1
    assert (error.rule, error.file, error.line, error.column, error.address) == (
        "trellis-file-shape",
        str(trellis),
        5,
        1,
        "periods",
    )
    assert tuple(error.related[0]) == (
        "original declaration",
        str(trellis),
        1,
        1,
        None,
        None,
        "periods",
    )
    assert str(error).startswith(
        f"{trellis}:5:1: address 'periods': the key 'periods' is written twice"
    )
    assert str(error).endswith(f"\n  original declaration: {trellis}:1:1 (address 'periods')")


def test_a_setting_outside_its_set_is_refused_at_its_declaration_naming_its_key_in_the_file(
    tmp_path, stage_with_one_addition
):
    """A settings file whose value of a_min lies outside its declared set is
    refused at the declaration of a_min in the methods file, with the key
    a_min of the settings file as the rejected setting."""
    example = EXAMPLES["setting-outside-set"]
    stage = stage_with_one_addition(text_of(example), example.additions[0][1])
    settings = tmp_path / "settings.yml"
    settings.write_text(SETTINGS_OUTSIDE_THE_SET, encoding="utf-8")
    with pytest.raises(ConstructionError) as refused:
        stage.configure(settings)
    error = refused.value
    # a_min is declared on line 3 of the methods file
    assert (error.rule, error.file, error.line, error.address) == (
        "setting-outside-set",
        "methods.bl",
        3,
        "methods.bl:3",
    )
    assert tuple(error.related[0]) == (
        "rejected setting",
        str(settings),
        3,
        3,
        None,
        None,
        "a_min",
    )


def test_after_a_refused_configuration_a_file_without_a_value_is_refused_naming_that_file(
    tmp_path, stage_with_one_addition
):
    """A stage refused one settings file keeps none of its values, so a
    second file that gives no value of the declared setting n_a is refused
    under `setting-unvalued`, naming the second file as the settings
    source."""
    example = EXAMPLES["setting-outside-set"]
    stage = stage_with_one_addition(text_of(example), example.additions[0][1])
    settings = tmp_path / "settings.yml"
    settings.write_text(SETTINGS_OUTSIDE_THE_SET, encoding="utf-8")
    with pytest.raises(ConstructionError):
        stage.configure(settings)
    unvalued = tmp_path / "unvalued.yml"
    unvalued.write_text("settings:\n  a_min: 0.0\n  a_max: 20.0\n", encoding="utf-8")
    with pytest.raises(ConstructionError) as refused:
        stage.configure(unvalued)
    assert refused.value.rule == "setting-unvalued"
    assert tuple(refused.value.related[0]) == (
        "settings source",
        str(unvalued),
        None,
        None,
        None,
        None,
        None,
    )


def test_a_trellis_record_whose_setting_lies_outside_its_set_is_refused_naming_its_key(
    tmp_path,
):
    """A trellis record that names a stage file, its methods file and a
    settings file whose a_min lies outside its declared set is refused by
    `specify_trellis` with the key a_min of that settings file as the
    rejected setting."""
    example = EXAMPLES["setting-outside-set"]
    settings = tmp_path / "settings.yml"
    settings.write_text(SETTINGS_OUTSIDE_THE_SET, encoding="utf-8")
    (tmp_path / "t.bl").write_text(text_of(example), encoding="utf-8")
    (tmp_path / "methods.bl").write_text(example.additions[0][1], encoding="utf-8")
    bound = tmp_path / "bound.yml"
    bound.write_text(
        "periods:\n  - stages:\n"
        "      t: {stage: t.bl, methods: methods.bl, settings: settings.yml}\n"
        "    connectors: []\ninter_connectors: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ConstructionError) as refused:
        specify_trellis(load_trellis(bound))
    assert (refused.value.rule, refused.value.address) == (
        "setting-outside-set",
        f"{tmp_path / 'methods.bl'}:3",
    )
    assert tuple(refused.value.related[0]) == (
        "rejected setting",
        str(settings),
        3,
        3,
        None,
        None,
        "a_min",
    )


def test_a_typing_of_the_derivative_operator_is_refused_over_the_range_of_its_entry():
    """The entry `D.method : !Linear` is refused under
    `no-method-for-derivative` over its range on line 3, at its term
    address."""
    error = refusal_of(EXAMPLES["no-method-for-derivative"])
    # the entry, of eighteen characters, stands from column 1 to column 19;
    # its term address, 7, counts the items of the stage with the typing
    # entries after the blocks: the `@stage` line, β, the four blocks, then
    # the entry
    assert (error.rule, position(error)) == (
        "no-method-for-derivative",
        ("t.bl", 3, 1, 3, 19, "7"),
    )


def test_a_method_typed_twice_at_one_place_is_refused_at_the_second_naming_the_first():
    """The method of the value of `cntn_to_dcsn`, typed by `evaluate.method`
    and again by `evaluate[V].method`, is refused at the second typing,
    with the first as its original declaration, named in the sentence by
    position."""
    error = refusal_of(EXAMPLES["component-typed-twice"])
    # line 10 reads `    | evaluate.method : !Linear | evaluate[V].method :
    # !pchip] {`: the first typing, of 25 characters, stands from column 7 to
    # column 32, and the second, of 27 characters, from column 35 to column 62
    assert position(error) == ("t.bl", 10, 35, 10, 62, "cntn_to_dcsn.evaluate[V].method")
    assert tuple(error.related[0]) == (
        "original declaration",
        "t.bl",
        10,
        7,
        10,
        32,
        "cntn_to_dcsn.evaluate.method",
    )
    assert "at t.bl:10:7 and by" in error.message


def test_an_expectation_binder_already_bound_where_it_stands_is_refused_at_its_declaration():
    """A distribution whose parameter reads `E_{z}(E_{z}(z))` is refused
    under `declared-once` at its declaration, since the inner expectation
    binds z where the outer one already binds it."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text("@stage: t\nz ~ N(0,1)\nw ~ N(E_{z}(E_{z}(z)), 1)\n")
    error = refused.value
    # the declaration of w is the third item of the file, on its third line,
    # counting the `@stage` line as the first
    assert (error.rule, error.address, error.line) == ("declared-once", "3", 3)
    assert "binds 'z', a name already bound where it stands" in error.message


# --- the action of a refusal and the command line ---


def test_the_refusal_of_a_state_in_a_backward_header_writes_the_header_without_it():
    """The action of the refusal of a backward header that lists the state
    x_d is the header without x_d."""
    error = refusal_of(EXAMPLES["header-coordinate"])
    assert (
        error.write == "Remove x_d from the header: `(V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu) : !dcsn`"
    )


def test_the_command_line_prints_a_refusal_as_its_first_line_and_then_its_action(tmp_path):
    """On a refused stage file, `python -m bellman` prints the refusal's
    position, sentence, address and rule on its first line and the action
    on the next, exiting with status 1."""
    example = EXAMPLES["header-coordinate"]
    file = tmp_path / "t.bl"
    file.write_text(text_of(example), encoding="utf-8")
    error = refusal_of(example)
    out = io.StringIO()
    # `main` is the function that `python -m bellman` runs
    with redirect_stdout(out):
        assert main([str(file)]) == 1
    first, *after = out.getvalue().splitlines()
    # the refused block `cntn_to_dcsn` stands from line 5, column 1 to line
    # 7, column 2
    assert first == (
        f"{file}:5:1-7:2: {error.message} (address 'cntn_to_dcsn'; rule header-coordinate)"
    )
    assert after == [f"  write: {error.write}"]
