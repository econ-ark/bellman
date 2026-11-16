"""Methods: the catalogue of method words, the places of a stage that admit
each word, `methodize` and the sources and entries that it refuses, the
pieces, cards and signatures that hold a bound method, the settings that
configure a method, and the typing entries of a methods file."""

from dataclasses import FrozenInstanceError

import pytest
from application_files import ROOT
from stage_builders import method_argument, places_of, stage_from_text
from stage_texts import (
    CONDITIONAL_PLACE,
    addition_of_text,
    branching_text,
    bundles_text,
    methods_addition,
)

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError, TargetError
from bellman.stage import (
    admitted_methods,
    elaborate_stage,
    load_stage,
    method_types,
    typing_entries,
    write_typing_entry,
)

# the methods file of the consumption stage of the cons-port application,
# whose header types the policy builder's method, grid and handler
CONS_PORT_METHODS = ROOT / "applications/cons-port/declaration/stages/cons/methods.bl"


# The catalogue of method words


def test_the_catalogue_holds_linear_root_find_and_vfi_and_no_other_spelling_of_them():
    """The catalogue holds the tags `!Linear`, `!root-find` and `!vfi`, and
    none of `!linear`, `!rootfind` and `!value-iteration`."""
    tags = tuple(method_types)
    assert {"!Linear", "!root-find", "!vfi"} <= set(tags)
    assert not {"!linear", "!rootfind", "!value-iteration"}.intersection(tags)


@pytest.mark.parametrize("tag", list(method_types))
def test_a_row_of_the_catalogue_is_a_mapping_of_what_it_admits_and_its_keywords(tag):
    """The row of each tag, a word that begins with `!`, is a mapping of
    `admits` and `keywords`, read by key or by attribute, that admits at least
    one kind of place."""
    rule = method_types[tag]
    assert tag.startswith("!")
    assert tuple(rule) == ("admits", "keywords")
    assert dict(rule) == {"admits": rule.admits, "keywords": rule.keywords}
    assert rule.admits


@pytest.mark.parametrize("tag", list(method_types))
def test_a_row_of_the_catalogue_is_a_frozen_value(tag):
    """The row of each tag hashes, and refuses a change of what it admits and
    of its keywords."""
    rule = method_types[tag]
    assert isinstance(hash(rule), int)
    with pytest.raises((AttributeError, FrozenInstanceError, TypeError)):
        rule.admits = ()
    with pytest.raises(TypeError):
        rule.keywords["other"] = object()


@pytest.mark.parametrize("tag", list(method_types))
def test_the_card_of_a_row_of_the_catalogue_is_at_most_78_characters_wide(tag):
    """Every line of the printed row of each tag holds at most 78
    characters."""
    rule = method_types[tag]
    assert all(len(line) <= 78 for line in str(rule).splitlines())


@pytest.mark.parametrize("tag", [tag for tag in method_types if method_types[tag].keywords])
def test_each_keyword_of_a_row_prints_alike_by_repr_and_by_str(tag):
    """Each keyword of a row that lists keywords prints the same text under
    `repr` and under `str`."""
    rule = method_types[tag]
    assert all(repr(keyword) == str(keyword) for keyword in rule.keywords.values())


@pytest.mark.parametrize(
    "written, tag",
    [("!gauss_hermite", "!gauss-hermite"), ("!monte_carlo", "!monte-carlo")],
    ids=("gauss-hermite", "monte-carlo"),
)
def test_a_tag_written_with_an_underscore_reads_the_row_of_its_hyphenated_tag(written, tag):
    """The catalogue reads a hyphenated tag written with underscores, as a
    stage file writes it, as the row of the hyphenated tag."""
    assert method_types[written] is method_types[tag]


# `n_<shock>` is one keyword for each shock of the expectation at which the
# quadrature is typed, `n_Ψ` and `n_θ` at `E_Ψ_θ`
@pytest.mark.parametrize(
    "tag, keywords",
    [
        ("!gauss-hermite", [("n_<shock>", "positive integer", True)]),
        ("!monte-carlo", [("n_paths", "positive integer", True), ("seed", "seed", False)]),
        ("!vfi", [("tol", "positive real", False), ("n_c", "positive integer", False)]),
    ],
    ids=("gauss-hermite", "monte-carlo", "vfi"),
)
def test_a_row_lists_each_keyword_with_its_kind_and_whether_it_is_required(tag, keywords):
    """The row of a tag lists the keywords that the package reads, each with
    its kind and with whether an entry must write it."""
    listed = method_types[tag].keywords.items()
    assert [(name, keyword.kind, keyword.required) for name, keyword in listed] == keywords


# the condition that a method needs, such as the grid line that `!egm`
# needs, is checked where the method is typed, so a card holds no derivation
# or statement of it
@pytest.mark.parametrize(
    "tag, printed, not_printed",
    [
        (
            "!gauss-hermite",
            ("METHOD !gauss-hermite", "\nAdmits\n", "\nKeywords\n", "\nGrid\n"),
            ("requires", "claim"),
        ),
        ("!egm", ("\nAdmits\n", "argmax"), ("Derivation", "Theorem 2")),
    ],
    ids=("gauss-hermite", "egm"),
)
def test_the_card_of_a_row_prints_what_the_method_admits_and_no_derivation(
    tag, printed, not_printed
):
    """The printed row of a tag holds its sections and what the method admits,
    and no derivation, requirement or claim of the method."""
    card = str(method_types[tag])
    assert [phrase for phrase in printed if phrase not in card] == []
    assert [word for word in not_printed if word in card] == []


# The places of a stage and the words that each admits


def test_the_places_of_cons_are_its_builders_lines_operators_and_definitions_with_kinds(cons):
    """`places()` lists each builder of `cons` with its named lines and their
    operators, the Evaluation of each builder with every object it stores,
    the operators of the stage and each definition, each with its kind."""
    addresses = places_of(cons)
    assert addresses == [
        "arvl_to_dcsn",
        "dcsn_to_cntn",
        "cntn_to_dcsn",
        "cntn_to_dcsn.value",
        "cntn_to_dcsn.marginal",
        "cntn_to_dcsn.evaluate",
        "cntn_to_dcsn.evaluate[V]",
        "cntn_to_dcsn.evaluate[D_{m_d}V]",
        "dcsn_to_arvl",
        "dcsn_to_arvl.value",
        "dcsn_to_arvl.evaluate",
        "dcsn_to_arvl.evaluate[V[<]]",
        "policy",
        "policy.optimality",
        "policy.optimality.argmax",
        "policy.argmax",
        "policy.evaluate",
        "policy.evaluate[c]",
        "argmax",
        "𝑢",
        "𝑑𝑢",
        "Γ",
    ]
    kinds = {row["address"]: row["kind"] for row in cons.places()}
    assert (
        kinds["cntn_to_dcsn"],
        kinds["policy"],
        kinds["policy.optimality.argmax"],
        kinds["policy.evaluate[c]"],
        kinds["𝑢"],
    ) == ("builder", "builder", "operator argmax", "operator evaluate", "definition")


def test_a_place_that_a_stage_lists_is_a_frozen_mapping_of_its_address_and_kind(cons):
    """A row of `places()` is a mapping of the place's address and its kind
    that refuses a change."""
    rows = cons.places()
    assert rows and {"address", "kind"} == set(rows[0])
    with pytest.raises(TypeError):
        rows[0]["kind"] = "changed"


@pytest.mark.parametrize(
    "stage_name, address",
    [
        ("tenure", "dcsn_to_cntn.keep.cash_on_hand"),
        ("house_choice", "dcsn_to_cntn.adjust.total_resources"),
    ],
    ids=("tenure", "house_choice"),
)
def test_a_line_of_a_branch_is_a_place_under_the_label_of_its_branch(request, stage_name, address):
    """A named line inside a branch of a block is the place
    `<block>.<branch>.<line>`."""
    assert address in places_of(request.getfixturevalue(stage_name))


@pytest.mark.parametrize(
    "stage_name, address",
    [("retiree_death", "cntn_to_dcsn.value.E_s"), ("ret_choice", "policy.choice.argmax")],
    ids=("retiree_death", "ret_choice"),
)
def test_an_operator_in_a_named_line_is_a_place_under_the_address_of_the_line(
    request, stage_name, address
):
    """The occurrence of an operator in a named line of a block is the place
    `<block>.<line>.<operator>`."""
    assert address in places_of(request.getfixturevalue(stage_name))


# a builder of a stage, a method word that it admits, and two words that it
# does not admit, each of which admits only an operator
@pytest.mark.parametrize(
    "stage_name, place, admitted, not_admitted",
    [
        ("cons", "arvl_to_dcsn", ("!deterministic",), ("!Linear", "!gauss_hermite")),
        ("cons", "policy", ("!egm",), ("!Linear", "!gauss_hermite")),
        ("cons", "cntn_to_dcsn", ("!vfi",), ("!Linear", "!gauss_hermite")),
        ("tenure", "policy", ("!max",), ("!Linear", "!gauss_hermite")),
    ],
    ids=("cons-arrival", "cons-policy", "cons-decision", "tenure-policy"),
)
def test_admitted_methods_answers_at_a_builder_the_words_whose_row_admits_a_builder(
    request, stage_name, place, admitted, not_admitted
):
    """`admitted_methods` answers at a builder the words whose row admits a
    builder, and no word whose row admits only an operator."""
    words = admitted_methods(request.getfixturevalue(stage_name), place)
    assert [word for word in admitted if word not in words] == []
    assert set(not_admitted).isdisjoint(words)


def test_admitted_methods_answers_the_representations_at_an_object_of_an_evaluation(cons):
    """At an object that an Evaluation stores, `admitted_methods` answers the
    three representations of the catalogue, the closed form among them."""
    assert admitted_methods(cons, "cntn_to_dcsn.evaluate[V]") == (
        "!Linear",
        "!pchip",
        "!closed_form",
    )


def test_admitted_methods_answers_at_an_expectation_each_word_that_admits_its_operator(tenure):
    """At the expectation of the branching stage `tenure`, `admitted_methods`
    answers each word whose row admits the operator `E`, spelled with
    underscores and in the order of the catalogue, `!gauss_hermite` among
    them."""
    expectations = tuple(
        tag.replace("-", "_")
        for tag in method_types
        if ("operator", "E") in method_types[tag]["admits"]
    )
    assert admitted_methods(tenure, "E_ε") == expectations
    assert "!gauss_hermite" in admitted_methods(tenure, "E_ε")


@pytest.fixture(scope="module")
def branching_with_two_derivatives():
    """The branching stage text whose decision value line is followed by a
    marginal line that holds the derivative operator twice."""
    choice_value = "    V = (V_w[>], V_r[>])[d]                :: [id=choice_value]\n"
    marginal = "    D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]  :: [id=marginal]\n"
    return stage_from_text(branching_text((choice_value, choice_value + marginal)))


def test_a_line_that_holds_the_derivative_operator_twice_is_one_place_admitting_none(
    branching_with_two_derivatives,
):
    """A line that holds the derivative operator `D` twice is one place,
    listed once, at which `admitted_methods` answers no word."""
    stage = branching_with_two_derivatives
    assert admitted_methods(stage, "cntn_to_dcsn.marginal.D") == ()
    assert places_of(stage).count("cntn_to_dcsn.marginal.D") == 1


def test_admitted_methods_answers_at_a_line_of_a_branch_and_refuses_a_name_that_is_no_place(
    branching_with_two_derivatives,
):
    """On one branching stage, `admitted_methods` answers a tuple at a named
    line of a branch and refuses a name that is no place of the stage."""
    stage = branching_with_two_derivatives
    assert isinstance(admitted_methods(stage, "dcsn_to_cntn.work.working"), tuple)
    with pytest.raises(TargetError):
        admitted_methods(stage, "no_such_block")


# Methodize: the stage it binds, the selection it replaces and the sources it
# refuses


def test_methodize_binds_the_stage_it_is_called_on(cons, cons_sources):
    """`methodize` returns the stage that it is called on, which then prints
    its stopping point `methods`."""
    stage = copy_native(cons)
    assert stage.methodize(cons_sources["methods"]) is stage
    assert repr(stage) == "ElaboratedStage('cons', methods)"


def test_a_second_call_of_methodize_replaces_the_whole_selection(cons, cons_sources):
    """A second `methodize` with an addition that types one place leaves that
    place alone typed, and the rows of the first solution method gone."""
    stage = copy_native(cons).methodize(cons_sources["methods"])
    assert list(stage.methods) == [
        "arvl_to_dcsn",
        "dcsn_to_cntn",
        "cntn_to_dcsn.evaluate",
        "policy",
    ]
    stage.methodize(methods_addition("cons", "cntn_to_dcsn.method : !vfi"))
    assert list(stage.methods) == ["cntn_to_dcsn"]
    assert str(stage.methods["cntn_to_dcsn"]) == "!vfi"
    assert list(stage.builder.policy.list()) == list(stage.declared.policy.list())


def test_a_second_call_of_methodize_types_a_place_anew_on_the_same_stage(cons):
    """A second `methodize` that types the representation of one Evaluation
    again replaces the first representation, on the stage that both calls
    bind."""
    grid = (
        "n_m : ℕ",
        "m_min : ℝ₊",
        "m_max : ℝ₊",
        "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))",
    )
    stage = copy_native(cons)
    linear = methods_addition("cons", "cntn_to_dcsn.evaluate.method : !Linear", *grid)
    pchip = methods_addition("cons", "cntn_to_dcsn.evaluate.method : !pchip", *grid)
    methodized = stage.methodize(linear)
    assert methodized.methodize(pchip) is stage
    assert (
        str(stage.methods)
        == "cntn_to_dcsn.evaluate   !pchip   !Cartesian(m_d=(m_min, m_max, n_m))"
    )


def test_methodize_refuses_an_addition_that_names_another_stage(cons):
    """An addition whose first line names another stage is refused under
    `metadata-mismatch` at that line, naming both stages and the form of the
    line."""
    with pytest.raises(ConstructionError) as refused:
        copy_native(cons).methodize({"text": "@methods: port\n", "origin": "port.methods.bl"})
    assert refused.value.rule == "metadata-mismatch"
    assert str(refused.value).startswith("port.methods.bl:1:1")
    phrases = (
        "the addition names the stage 'port', and the stage file names itself 'cons'",
        "an addition's first line is `@methods: <stage>`",
    )
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


@pytest.fixture(scope="module")
def cons_methods_text(cons_sources):
    """The text of the methods file of `cons`."""
    return cons_sources["methods"].read_text(encoding="utf-8")


# an entry of the methods file of `cons` as written, the entry or entries
# that replace it, and the rule and the words of the refusal
@pytest.mark.parametrize(
    "written, rewritten, rule, phrases",
    [
        pytest.param(
            "arvl_to_dcsn.method : !deterministic\n",
            "nowhere.method : !deterministic\n",
            "name-in-scope",
            (
                "'nowhere' is no block, no definition and no operator",
                "the blocks are arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy",
            ),
            id="a-name-that-is-no-block-definition-or-operator",
        ),
        pytest.param(
            "cntn_to_dcsn.evaluate.method : !Linear\n",
            "cntn_to_dcsn.nowhere.method : !Linear\n",
            "name-in-scope",
            ("`cntn_to_dcsn.nowhere`, which is no place of the block 'cntn_to_dcsn'",),
            id="no-place-of-a-block",
        ),
        pytest.param(
            "arvl_to_dcsn.method : !deterministic\n",
            "arvl_to_dcsn.method : !deterministic\narvl_to_dcsn.method : !identity\n",
            "declared-twice",
            ("the component `method` of block 'arvl_to_dcsn' is written twice",),
            id="one-component-written-twice",
        ),
    ],
)
def test_methodize_refuses_an_entry_at_no_place_or_a_component_written_twice(
    cons, cons_methods_text, tmp_path, written, rewritten, rule, phrases
):
    """`methodize` refuses a methods file with an entry that names no place,
    or that writes one component twice, under its rule and in its own
    file."""
    assert cons_methods_text.count(written) == 1
    path = tmp_path / "methods.bl"
    path.write_text(cons_methods_text.replace(written, rewritten), encoding="utf-8")
    with pytest.raises(ConstructionError) as refused:
        copy_native(cons).methodize(path)
    assert (refused.value.rule, refused.value.file) == (rule, str(path))
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


def test_methodize_refuses_a_mapping_that_holds_no_text_of_an_addition(cons):
    """`methodize` refuses a mapping of a stage name and a list of methods,
    since an addition is a `.bl` file or a mapping of its text and origin."""
    with pytest.raises(TypeError, match="an addition is the path of a `.bl` file"):
        copy_native(cons).methodize(
            {"stage": "cons", "methods": [{"on": "policy", "method": "egm"}]}
        )


@pytest.mark.parametrize(
    "name, text, phrase",
    [
        ("methods.yml", "methods: [{on: policy, method: egm}]\n", "is no `.bl` file"),
        ("absent.bl", None, "cannot be read"),
    ],
    ids=("a-yaml-file", "a-file-that-does-not-exist"),
)
def test_methodize_refuses_a_file_that_is_no_readable_addition(cons, tmp_path, name, text, phrase):
    """`methodize` refuses a YAML file, and a path at which no file stands,
    under `readable-form`, naming the path."""
    path = tmp_path / name
    if text is not None:
        path.write_text(text, encoding="utf-8")
    with pytest.raises(ConstructionError, match=phrase) as refused:
        copy_native(cons).methodize(path)
    assert refused.value.rule == "readable-form" and str(path) in str(refused.value)


# an entry that types a method word at a place of a kind that the word's row
# does not admit, and the words of the refusal: the place, its kind and the
# kinds that the row admits
@pytest.mark.parametrize(
    "entry, words",
    [
        pytest.param(
            "policy.method : !gauss_hermite",
            ("`policy`", "kind builder", "admits operator E"),
            id="a-quadrature-at-a-builder",
        ),
        pytest.param(
            "cntn_to_dcsn.value.method : !egm",
            ("`cntn_to_dcsn.value`", "kind statement", "admits builder, operator argmax"),
            id="egm-at-a-line",
        ),
        pytest.param(
            "cntn_to_dcsn.evaluate.method : !vfi",
            ("`cntn_to_dcsn.evaluate`", "kind operator evaluate", "admits builder"),
            id="vfi-at-an-evaluation",
        ),
    ],
)
def test_a_method_word_at_a_place_of_a_kind_that_its_row_does_not_admit_is_refused(
    cons, entry, words
):
    """A method word typed at a place of a kind that its row of the catalogue
    does not admit is refused under `method-admission`, naming the place,
    its kind and the kinds that the row admits."""
    with pytest.raises(ConstructionError) as refused:
        copy_native(cons).methodize(methods_addition("cons", entry))
    assert (refused.value.rule, refused.value.stage) == ("method-admission", cons.name)
    assert [word for word in words if word not in str(refused.value)] == []


@pytest.mark.parametrize(
    "word",
    ["unknown_method", "linear", "rootfind", "value_iteration"],
    ids=(
        "a-word-of-no-row",
        "linear-in-lower-case",
        "root-find-without-its-hyphen",
        "vfi-spelled-out",
    ),
)
def test_a_method_word_that_no_row_of_the_catalogue_holds_is_refused(cons, word):
    """A method word that no row of the catalogue holds is refused under
    `syntax`, which names the word."""
    with pytest.raises(ConstructionError) as refused:
        copy_native(cons).methodize(methods_addition("cons", f"policy.method : !{word}"))
    assert refused.value.rule == "syntax"
    assert f"`!{word}`, which no row of the catalogue holds" in str(refused.value)


def test_policy_lines_added_without_a_solution_method_cannot_define_the_policy_again(corpus_path):
    """Policy lines that an addition writes without a solution method stand
    beside the declared maximization, so a second definition of the policy
    is refused under `defined-once`."""
    again = {
        "text": "@methods: cons\n[id=policy] {\n    c = 𝑑𝑢(1)    :: [id=again]\n}\n",
        "origin": "again.bl",
    }
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(load_stage(corpus_path("cons"), [again]))
    assert refused.value.rule == "defined-once"
    assert refused.value.address == "policy.again"
    assert "policy" in refused.value.message


# a line of an addition to the perfect-foresight stage that the parser cannot
# read, the words of the reason of its refusal, and whether the line writes
# the word `if`, at which the refusal gives the advice on where a conditional
# stands
UNREADABLE_LINES = {
    "a-conditional-inside-a-formula": (
        "κ := 1 + if Γ < R then 1 else 2\n",
        "the file writes `Γ` here",
        True,
    ),
    "a-conditional-without-else": (
        "κ := if Γ < R then 1\n",
        "the language admits `else` at this place",
        True,
    ),
    "a-formula-that-ends-early": ("κ := 1 +\n", "the line ends here", False),
}


@pytest.mark.parametrize(
    "line, reason, conditional", list(UNREADABLE_LINES.values()), ids=list(UNREADABLE_LINES)
)
def test_methodize_refuses_an_addition_that_the_parser_cannot_read_at_its_line(
    derived_parameter_stages, line, reason, conditional
):
    """`methodize` refuses an addition that the parser cannot read under
    `syntax`, in the addition's file at the marked line, with the reason
    and, at a conditional, the advice on where a conditional stands."""
    methods = {"text": f"@methods: perfect_foresight\n{line}", "origin": "m.bl"}
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage().methodize(methods)
    error = refused.value
    assert (error.rule, error.file, error.line) == ("syntax", "m.bl", 2)
    assert reason in error.parts.why and line.rstrip("\n") in error.parts.what
    assert (error.write == CONDITIONAL_PLACE) == conditional


@pytest.mark.parametrize(
    "line", [line for line, _, _ in UNREADABLE_LINES.values()], ids=list(UNREADABLE_LINES)
)
def test_methodize_refuses_an_unreadable_addition_in_the_words_of_elaborate_stage(
    derived_parameter_stages, line
):
    """`elaborate_stage` refuses the perfect-foresight stage file with an
    addition that the parser cannot read in the words in which `methodize`
    refuses the addition."""
    methods = {"text": f"@methods: perfect_foresight\n{line}", "origin": "m.bl"}
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage().methodize(methods)
    error = refused.value
    with pytest.raises(ConstructionError) as elaborated:
        elaborate_stage(
            {
                "stage": {
                    "text": derived_parameter_stages.text,
                    "origin": derived_parameter_stages.origin,
                },
                "calibration": {},
                "settings": {},
                "methods": [methods],
            }
        )
    assert str(elaborated.value) == str(error)


@pytest.fixture(scope="module")
def accepted_options(cons):
    """`cons` with the keyword `option` of `!Linear` at `policy.evaluate`
    written as the declared setting `choice`, and `cons` with it written as
    the quoted string `"literal"`."""
    declared = copy_native(cons).methodize(
        {
            "text": (
                "@methods: cons\nchoice : ℕ\npolicy.evaluate.method : !Linear(option=choice)\n"
            ),
            "origin": "keywords.methods.bl",
        }
    )
    allowed = copy_native(cons).methodize(
        {
            "text": '@methods: cons\npolicy.evaluate.method : !Linear(option="literal")\n',
            "origin": "keywords.methods.bl",
        }
    )
    return declared, allowed


# the value of the keyword `option` of `!Linear` at `policy.evaluate`, and
# the rule and the words of its refusal
@pytest.mark.parametrize(
    "value, rule, phrase",
    [
        pytest.param("missing", "name-in-scope", "missing", id="an-undeclared-name"),
        pytest.param(
            '("a", !foo(inner=missing))',
            "name-in-scope",
            "missing",
            id="an-undeclared-name-inside-a-method-word",
        ),
        pytest.param("2", "method-setting-declared", "writes the number 2", id="a-number"),
        pytest.param(
            '("a", 2)', "method-setting-declared", "writes the number 2", id="a-number-in-a-tuple"
        ),
        pytest.param(
            "!foo(inner=2)",
            "method-setting-declared",
            "writes the number 2",
            id="a-number-inside-a-method-word",
        ),
    ],
)
def test_a_keyword_argument_reads_declared_names_and_quoted_strings_and_no_number(
    cons, accepted_options, value, rule, phrase
):
    """The value of a keyword argument is refused at its line where it names
    an undeclared setting or writes a number, at any depth, while a declared
    setting and a quoted string at the same place are read as written."""
    declared, allowed = accepted_options
    addition = {
        "text": f"@methods: cons\npolicy.evaluate.method : !Linear(option={value})\n",
        "origin": "keywords.methods.bl",
    }
    with pytest.raises(ConstructionError) as caught:
        copy_native(cons).methodize(addition)
    error = caught.value
    assert error.rule == rule
    assert error.file == "keywords.methods.bl" and error.line == 2
    assert error.address == "policy.evaluate"
    assert error.column is not None and error.write
    assert phrase in error.message
    assert method_argument(declared.methods["policy.evaluate"], "option") == "choice"
    assert "policy.evaluate" in allowed.methods
    assert method_argument(allowed.methods["policy.evaluate"], "option") == '"literal"'


# Where a bound method stands: the pieces, the cards and the signatures


def test_a_method_typed_at_the_argmax_of_a_policy_line_is_held_by_the_box_of_that_argmax(
    ez_savings,
):
    """A method typed at the argmax of the line `objective` of the policy
    block is held under the address that the entry writes and by the box
    `objective:Argmax`, whose card prints it."""
    # the box that realizes the argmax of a named line is the row `Argmax`
    # that the line forms, and the table of methods reads the box from that
    # row, so the entry's address and the box name one place
    bound = copy_native(ez_savings).methodize(
        methods_addition("ez_savings", "policy.objective.argmax.method : !golden_section")
    )
    assert list(bound.methods) == ["policy.objective.argmax"]
    argmax = bound.builder.policy["objective:Argmax"]
    assert [str(held) for held in argmax.methods.values()] == ["!golden_section"]
    assert "!golden_section" in str(argmax)
    assert "policy.objective.argmax" in str(bound.view())


# a piece of `cons` with its methods file, and the places of the methods
# typed within it, in their order
@pytest.mark.parametrize(
    "piece, places",
    [
        pytest.param(
            lambda stage: stage.builder.bwd,
            ["cntn_to_dcsn.evaluate", "policy"],
            id="the-backward-builders-graph",
        ),
        pytest.param(
            lambda stage: stage.builder.fwd,
            ["arvl_to_dcsn", "dcsn_to_cntn"],
            id="the-forward-builders-graph",
        ),
        pytest.param(
            lambda stage: stage.builder["cntn", "dcsn"],
            ["cntn_to_dcsn.evaluate"],
            id="the-decision-builder",
        ),
        pytest.param(
            lambda stage: stage.initial.backward["cntn_to_dcsn"],
            ["cntn_to_dcsn.evaluate"],
            id="the-block-of-the-decision-builder",
        ),
        pytest.param(
            lambda stage: stage.builder["cntn", "dcsn"].primitives["cntn_to_dcsn:Evaluation"],
            ["cntn_to_dcsn.evaluate"],
            id="the-evaluation-of-the-decision-builder",
        ),
        pytest.param(
            lambda stage: stage.builder.bwd["cntn_to_dcsn"]["Aggregation"],
            [],
            id="the-aggregation-of-the-decision-builder",
        ),
        pytest.param(
            lambda stage: stage.initial.backward["cntn_to_dcsn"]["cntn_to_dcsn.value"],
            [],
            id="the-value-line-of-the-block",
        ),
        pytest.param(
            lambda stage: stage.initial.backward["cntn_to_dcsn"]["cntn_to_dcsn.marginal"],
            [],
            id="the-marginal-line-of-the-block",
        ),
        pytest.param(
            lambda stage: stage.builder["dcsn", "arvl"], [], id="the-backward-arrival-builder"
        ),
        pytest.param(
            lambda stage: stage.arvl.builder.bwd["Aggregation"],
            [],
            id="the-aggregation-of-the-backward-arrival-builder",
        ),
        pytest.param(lambda stage: stage.declared.policy, [], id="the-declared-policy-builder"),
    ],
)
def test_each_piece_of_a_stage_answers_the_methods_typed_within_it(cons_methodized, piece, places):
    """A graph, a builder, a block, a primitive or a line of `cons` with its
    methods answers the places of the methods typed within it, and no
    other."""
    assert list(piece(cons_methodized).methods) == places


def test_the_policy_method_is_held_by_its_builder_and_the_initial_diagrams_and_by_no_row(
    cons_methodized,
):
    """The method typed on the policy builder of `cons` is held by the
    builder and by the initial diagrams, and by none of the builder's
    rows."""
    stage = cons_methodized
    assert str(stage.builder.policy.methods["policy"]) == (
        '!egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"'
    )
    assert stage.initial.methods["policy"].word == "!egm"
    assert all(stage.builder.policy[key].methods == {} for key in stage.builder.policy.list())


def test_a_configured_representation_prints_its_grid_by_the_names_of_its_settings(
    cons_configured,
):
    """The representation typed at the Evaluation of the decision builder
    prints its word, its grid by the names of its settings and its handler,
    while the settings bind `n_m` to 8000."""
    evaluation = cons_configured.builder.bwd["cntn_to_dcsn"]["Evaluation"]
    held = evaluation.methods["cntn_to_dcsn.evaluate"]
    assert str(held) == '!Linear   !Cartesian(m_d=(m_min, m_max, n_m))   "cons-port:_make_interp"'
    assert cons_configured.bindings.settings["n_m"] == 8000


def test_the_signature_of_an_evaluation_prints_its_method_grid_and_handler(cons_methodized):
    """The signature of the Evaluation of the decision builder prints the
    method, the grid and the handler typed at it after its fields."""
    stage = cons_methodized
    evaluation = stage.builder["cntn", "dcsn"].primitives["cntn_to_dcsn:Evaluation"]
    assert str(evaluation.signature()).splitlines()[2:] == [
        "method     !Linear",
        "grid       !Cartesian(m_d=(m_min, m_max, n_m))",
        'handler    "cons-port:_make_interp"',
    ]


def test_a_method_is_read_by_its_address_or_by_the_name_of_the_box_that_realizes_it(
    cons_methodized,
):
    """The methods of a stage answer one record at the address of a place and
    at the name of the box that realizes it."""
    stage = cons_methodized
    assert stage.methods["cntn_to_dcsn:Evaluation"] is stage.methods["cntn_to_dcsn.evaluate"]


def test_the_methods_of_a_stage_hold_no_place_at_which_no_method_is_typed(cons_methodized):
    """The methods of `cons` refuse, and do not hold, the address of a
    builder at which no method is typed."""
    stage = cons_methodized
    with pytest.raises(KeyError):
        stage.methods["dcsn_to_arvl"]
    assert "dcsn_to_arvl" not in stage.methods


def test_the_methods_file_of_cons_binds_a_handler_beside_the_method_where_one_is_written(
    cons_methodized,
):
    """The methods file of `cons` binds a handler alone at the forward
    decision builder and beside the method and grid at the policy
    builder."""
    assert str(cons_methodized.methods["dcsn_to_cntn"]) == '"cons-port:transition_fwd"'
    assert str(cons_methodized.methods["policy"]) == (
        '!egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"'
    )


def test_a_keyword_argument_prints_the_value_of_the_setting_that_it_names(cons):
    """The policy card prints a keyword argument of `!vfi` with the
    configured value of the setting that it names, and not with the value of
    a setting whose name is the keyword's own."""
    configured = (
        copy_native(cons)
        .methodize(
            methods_addition(
                "cons",
                "points : ℕ",
                "tolerance : ℝ₊₊",
                "policy.method : !vfi(n_c=points, tol=tolerance)",
            )
        )
        .configure({"n_c": 17, "points": 8000, "tol": 3, "tolerance": 1e-06})
    )
    card = str(configured.builder.policy.denote())
    assert "n_c = 8000" in card and "tol = 1e-06" in card
    assert "n_c = 17" not in card and "tol = 3" not in card


def test_a_setting_that_no_method_names_leaves_the_grid_on_the_card_as_written(cons_configured):
    """A configured setting that no method names is not printed on the card
    of the decision builder, whose grid stays as the methods file writes
    it."""
    gridded = copy_native(cons_configured).configure({"orders": 17})
    card = str(gridded.builder.bwd["cntn_to_dcsn"].denote())
    assert "!Cartesian(m_d=(m_min, m_max, n_m))" in card and "orders = 17" not in card


# The stage `bundles` of the support module `stage_texts` is a small stage
# whose arrival builder takes the expectation over two shocks `y` and `z`.
# The two value lines below replace the lines of its arrival builder: both
# take the expectation over the pair of shocks, the second also as an
# iterated expectation, so that the places `E_y_z`, `E_y` and `E_z` reach one
# merged box. A derivative line forms no box, so the stage carries a second
# value `W`, with a value line in the decision builder too.
TWO_VALUE_LINES = {
    "arrival": (
        "    V[<] = E_{y,z}(V)                     :: [id=value]\n"
        "    W[<] = E_{y,z}(R*W) + E_{y}(E_{z}(W)) :: [id=second]\n"
    ),
    "decision": (
        "    V = c + β*V[>]                  :: [id=value]\n"
        "    W = c + β*W[>]                  :: [id=second]\n"
    ),
}


# the header of the decision builder and of the arrival builder, each as the
# stage `bundles` writes it and as it reads the second value `W`
TWO_VALUE_HEADERS = (
    (
        "(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
        "(V[>] : ℝ @ !vlu, W[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu, W : ℝ @ !vlu) : !dcsn]",
    ),
    (
        "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl]",
        "[id=dcsn_to_arvl, (V, W) : !dcsn -> (V[<] : ℝ @ !vlu, W[<] : ℝ @ !vlu) : !arvl]",
    ),
)


@pytest.fixture(scope="module")
def two_values():
    """The stage `bundles` with the lines of `TWO_VALUE_LINES` and the
    headers of `TWO_VALUE_HEADERS`."""
    text = bundles_text(**TWO_VALUE_LINES)
    for written, read in TWO_VALUE_HEADERS:
        text = text.replace(written, read)
    return stage_from_text(text, "bundles.bl")


# entries of an addition to the stage `bundles` that type two places
# reaching one box, and the words of the refusal
@pytest.mark.parametrize(
    "entries, phrases",
    [
        pytest.param(
            (
                "dcsn_to_arvl.value.E_y_z.method : !quadrature",
                "dcsn_to_arvl.second.E_y_z.method : !exact",
            ),
            (
                "which both reach the operator `E` of block 'dcsn_to_arvl'",
                "dcsn_to_arvl.value.E_y_z.method : !quadrature",
                "dcsn_to_arvl.second.E_y_z.method : !exact",
            ),
            id="the-expectations-of-two-lines-merged-into-one-box",
        ),
        pytest.param(
            (
                "n_golden : ℕ",
                "policy.argmax.method : !max",
                "policy.objective.argmax.method : !golden_section(n_sections=n_golden)",
            ),
            ("which both reach the operator `argmax` of block 'policy';",),
            id="the-argmax-of-the-block-and-of-its-named-line",
        ),
        pytest.param(
            ("E_y_z.method : !quadrature", "E_y.method : !exact"),
            (
                "at `E_y_z` and at `E_y`, which both reach the operator `E` of block "
                "'dcsn_to_arvl';",
            ),
            id="two-places-of-the-stage-that-name-no-block",
        ),
    ],
)
def test_two_entries_whose_places_reach_one_box_are_refused(two_values, entries, phrases):
    """Two entries whose places reach one box are refused under
    `component-typed-twice`, with the box's operator and block."""
    bundles_text_with_two_value_lines = bundles_text(**TWO_VALUE_LINES)
    assert [
        written
        for written, _ in TWO_VALUE_HEADERS
        if bundles_text_with_two_value_lines.count(written) != 1
    ] == []
    with pytest.raises(ConstructionError) as refused:
        copy_native(two_values).methodize(methods_addition("bundles", *entries))
    assert refused.value.rule == "component-typed-twice"
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []


def test_an_entry_at_the_head_of_a_block_types_the_one_merged_box_of_its_lines(two_values):
    """An entry at the head of the arrival block types the one box into which
    the expectations of its two value lines merge, which holds and prints
    that one method."""
    bundles_text_with_two_value_lines = bundles_text(**TWO_VALUE_LINES)
    assert [
        written
        for written, _ in TWO_VALUE_HEADERS
        if bundles_text_with_two_value_lines.count(written) != 1
    ] == []
    bound = copy_native(two_values).methodize(
        methods_addition("bundles", "dcsn_to_arvl.E_y_z.method : !quadrature")
    )
    merged = bound.builder.bwd.primitives["dcsn_to_arvl:Expectation"]
    assert {place: str(held) for place, held in merged.methods.items()} == {
        "dcsn_to_arvl.E_y_z": "!quadrature"
    }
    assert str(merged.signature()).splitlines()[-1] == "method     !quadrature"


def test_an_evaluation_and_one_of_its_objects_cannot_both_be_typed_while_its_objects_can(
    port,
):
    """A method typed at the whole of an Evaluation and again at one object
    that it stores is refused under `component-typed-twice`, while the two
    objects, the value and its stated derivative, take a representation
    each."""
    with pytest.raises(ConstructionError) as refused:
        copy_native(port).methodize(
            methods_addition(
                "port",
                "cntn_to_dcsn.evaluate.method : !Linear",
                "cntn_to_dcsn.evaluate[V].method : !pchip",
            )
        )
    assert refused.value.rule == "component-typed-twice"
    phrases = (
        "the method component is typed twice",
        "the object `V` stored at the operator `evaluate` of block 'cntn_to_dcsn'",
    )
    assert [phrase for phrase in phrases if phrase not in str(refused.value)] == []
    apart = copy_native(port).methodize(
        methods_addition(
            "port",
            "cntn_to_dcsn.evaluate[V].method : !Linear",
            "cntn_to_dcsn.evaluate[D_{k_d}V].method : !pchip",
        )
    )
    assert {place: str(held) for place, held in apart.methods.items()} == {
        "cntn_to_dcsn.evaluate[V]": "!Linear",
        "cntn_to_dcsn.evaluate[D_{k_d}V]": "!pchip",
    }


# Configure: the settings that a method reads


@pytest.fixture(scope="module")
def cons_with_vfi_settings(cons):
    """`cons` with `!vfi` and two keyword arguments typed on its policy
    builder, the settings declared on the sets ℝ and [-inf, inf], so that the
    keyword's own kind, and not the declared set, refuses a value."""
    return copy_native(cons).methodize(
        methods_addition(
            "cons",
            "points : ℝ",
            "tolerance : [-inf, inf]",
            "policy.method : !vfi(n_c=points, tol=tolerance)",
        )
    )


# the settings of the stage `cons_with_vfi_settings`, and the rule, the
# words and the address of their refusal; a setting with no value is
# addressed by the line of the addition that declares it
@pytest.mark.parametrize(
    "settings, rule, phrase, address",
    [
        pytest.param(
            {"tolerance": 1e-6},
            "setting-unvalued",
            "points",
            "cons.methods.bl:2",
            id="a-count-without-a-value",
        ),
        pytest.param(
            {"points": -5, "tolerance": 1e-6},
            "method-option-value",
            "positive integer",
            "policy",
            id="a-negative-count",
        ),
        pytest.param(
            {"points": 8, "tolerance": float("inf")},
            "method-option-value",
            "positive real",
            "policy",
            id="an-infinite-tolerance",
        ),
        pytest.param(
            {"points": 8, "tolerance": -1.0},
            "method-option-value",
            "positive real",
            "policy",
            id="a-negative-tolerance",
        ),
    ],
)
def test_configure_takes_only_a_value_of_its_kind_for_each_keyword_argument_of_vfi(
    cons_with_vfi_settings, settings, rule, phrase, address
):
    """`configure` refuses a setting that a keyword argument of `!vfi` names
    and the source does not value, or values outside the keyword's kind,
    while a positive count and a positive tolerance configure."""
    methodized = cons_with_vfi_settings
    with pytest.raises(ConstructionError, match=phrase) as refused:
        methodized.configure({"settings": settings})
    assert (refused.value.rule, refused.value.stage, refused.value.address) == (
        rule,
        "cons",
        address,
    )
    configured = copy_native(methodized).configure({"settings": {"points": 8, "tolerance": 1e-6}})
    assert configured.bindings.settings["points"] == 8


@pytest.fixture(scope="module")
def cons_with_a_grid_of_resources(cons):
    """`cons` with a representation and its grid of resources typed at the
    Evaluation of the decision builder, the settings declared on ℤ and ℝ, so
    that the checks of the grid, and not the declared sets, refuse a count or
    a bound."""
    return copy_native(cons).methodize(
        methods_addition(
            "cons",
            "n_m : ℤ",
            "m_min : ℝ",
            "m_max : ℝ",
            "cntn_to_dcsn.evaluate.method : !Linear",
            "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))",
        )
    )


# the settings of the stage `cons_with_a_grid_of_resources`, and the rule,
# the words and the address of their refusal; a bound that is no number of ℝ
# is refused at its declaration, on line 3 or 4 of the addition, before the
# grid is read
@pytest.mark.parametrize(
    "settings, rule, phrase, address",
    [
        pytest.param(
            {"n_m": -5, "m_min": 0.1, "m_max": 10.0},
            "grid-bounds",
            "count -5",
            "cntn_to_dcsn.evaluate",
            id="a-count-below-two",
        ),
        pytest.param(
            {"n_m": 8, "m_min": 10.0, "m_max": 1.0},
            "grid-bounds",
            "in order",
            "cntn_to_dcsn.evaluate",
            id="bounds-out-of-order",
        ),
        pytest.param(
            {"n_m": 8, "m_min": -1.0, "m_max": 10.0},
            "grid-bounds",
            "declared set",
            "cntn_to_dcsn.evaluate",
            id="a-bound-outside-the-declared-set-of-its-coordinate",
        ),
        pytest.param(
            {"n_m": 8, "m_min": float("nan"), "m_max": 10.0},
            "setting-outside-set",
            "nan",
            "cons.methods.bl:3",
            id="a-bound-that-is-no-number",
        ),
        pytest.param(
            {"n_m": 8, "m_min": 0.1, "m_max": float("inf")},
            "setting-outside-set",
            "inf",
            "cons.methods.bl:4",
            id="an-infinite-bound",
        ),
    ],
)
def test_configure_refuses_a_grid_count_below_two_or_a_bound_out_of_order_or_outside_its_set(
    cons_with_a_grid_of_resources, settings, rule, phrase, address
):
    """`configure` refuses a grid whose count is below two, or whose bounds
    are out of order, outside the declared set of the coordinate or not
    finite numbers."""
    gridded = cons_with_a_grid_of_resources
    with pytest.raises(ConstructionError, match=phrase) as refused:
        gridded.configure({"settings": settings})
    assert (refused.value.rule, refused.value.stage, refused.value.address) == (
        rule,
        "cons",
        address,
    )


def test_methodize_refuses_a_grid_factor_on_a_coordinate_that_the_function_lacks(cons):
    """A grid factor on a coordinate that the function at the place lacks is
    refused under `grid-coordinate` where the entry is read."""
    with pytest.raises(ConstructionError, match="'m'.*no coordinate.*m_d") as refused:
        copy_native(cons).methodize(
            methods_addition(
                "cons",
                "n_m : ℕ",
                "m_min : ℝ₊",
                "m_max : ℝ₊",
                "cntn_to_dcsn.evaluate.method : !Linear",
                "cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_min, m_max, n_m))",
            )
        )
    assert refused.value.rule == "grid-coordinate"


@pytest.fixture(scope="module")
def port_with_two_node_counts(port):
    """`port` with a quadrature at its expectation whose node counts of the
    two shocks name the settings `nodes_Ψ` and `nodes_θ`, declared on ℝ."""
    return copy_native(port).methodize(
        methods_addition(
            "port",
            "nodes_Ψ : ℝ",
            "nodes_θ : ℝ",
            "E_Ψ_θ.method : !gauss_hermite(n_Ψ=nodes_Ψ, n_θ=nodes_θ)",
        )
    )


# a value of the node count `nodes_Ψ` of the stage
# `port_with_two_node_counts`, and the rule and the words of its refusal; a
# list and a truth value are no numbers of ℝ and are refused at the
# declaration
@pytest.mark.parametrize(
    "value, rule, phrase",
    [
        pytest.param(0, "method-option-value", "n_Ψ.*positive integer", id="zero"),
        pytest.param([7], "setting-outside-set", "nodes_Ψ", id="a-list"),
        pytest.param(7.5, "method-option-value", "n_Ψ.*positive integer", id="a-fraction"),
        pytest.param(True, "setting-outside-set", "nodes_Ψ", id="a-truth-value"),
    ],
)
def test_configure_refuses_a_node_count_of_a_quadrature_that_is_no_positive_integer(
    port_with_two_node_counts, value, rule, phrase
):
    """`configure` refuses a node count of a quadrature that is no positive
    integer."""
    quadrature = port_with_two_node_counts
    with pytest.raises(ConstructionError, match=phrase) as refused:
        quadrature.configure({"settings": {"nodes_Ψ": value, "nodes_θ": 7}})
    assert refused.value.rule == rule


def test_a_setting_that_both_node_counts_of_a_quadrature_name_is_read_as_a_node_count(
    port_with_one_node_count,
):
    """A setting that both node counts of a quadrature name is refused at
    zero as the count `n_Ψ`, and is configured at seven as a setting that
    `!gauss_hermite` reads at the expectation."""
    quadrature = port_with_one_node_count
    with pytest.raises(ConstructionError, match="keyword 'n_Ψ': 0 is not a positive integer"):
        quadrature.configure({"settings": {"nodes": 0}})
    configured = copy_native(quadrature).configure({"settings": {"nodes": 7}})
    assert configured.bindings.settings["nodes"] == 7
    assert str(configured.settings["nodes"]) == "nodes = 7 : ℕ, read at E_Ψ_θ by !gauss_hermite"


@pytest.mark.parametrize(
    "entries, keyword",
    [
        pytest.param(
            ("nodes_Ψ : ℝ", "E_Ψ_θ.method : !gauss_hermite(n_Ψ=nodes_Ψ)"),
            "n_θ",
            id="the-node-count-of-one-shock-of-two",
        ),
        pytest.param(("dcsn_to_cntn.method : !monte_carlo",), "n_paths", id="the-count-of-paths"),
    ],
)
def test_methodize_refuses_an_entry_that_omits_a_keyword_its_row_requires(port, entries, keyword):
    """An entry that omits a keyword that the row of its word requires is
    refused under `method-admission`, naming the keyword."""
    with pytest.raises(ConstructionError, match=f"without the keyword {keyword}") as refused:
        copy_native(port).methodize(methods_addition("port", *entries))
    assert refused.value.rule == "method-admission"


def test_configure_refuses_an_infinite_minimum_probability_of_tauchen(port):
    """`configure` refuses an infinite value of the keyword `min_prob` of
    `!tauchen`, which is a finite positive real."""
    positive_real = copy_native(port).methodize(
        methods_addition(
            "port",
            "minimum_probability : [-inf, inf]",
            "E_Ψ_θ.method : !tauchen(min_prob=minimum_probability)",
        )
    )
    with pytest.raises(ConstructionError, match="finite value"):
        positive_real.configure({"settings": {"minimum_probability": float("inf")}})


@pytest.fixture(scope="module")
def monte_carlo_port(port):
    """`port` with `!monte_carlo` and a keyword that its row does not list on
    the forward decision builder, and a quadrature at its expectation."""
    return copy_native(port).methodize(
        methods_addition(
            "port",
            "n_sim : ℕ",
            "n_Ψ_nodes : ℕ",
            "n_θ_nodes : ℕ",
            'dcsn_to_cntn.method : !monte_carlo(n_paths=n_sim, antithetic="yes")',
            "E_Ψ_θ.method : !gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)",
        )
    )


def test_a_keyword_that_the_row_does_not_list_is_kept_for_the_handler(monte_carlo_port):
    """A keyword argument that the row of `!monte_carlo` does not list is
    admitted and kept as written."""
    row = method_types["!monte_carlo"]
    assert method_argument(monte_carlo_port.methods["dcsn_to_cntn"], "antithetic") == '"yes"'
    assert "antithetic" not in row.keywords


def test_a_method_word_written_with_underscores_binds_the_row_of_its_hyphenated_tag(
    monte_carlo_port,
):
    """A method word that an addition writes with underscores binds the row
    of its hyphenated tag."""
    bound = monte_carlo_port
    assert (
        method_types["!" + bound.methods["dcsn_to_cntn"].method.name]
        is method_types["!monte-carlo"]
    )
    assert method_types["!" + bound.methods["E_Ψ_θ"].method.name] is method_types["!gauss-hermite"]


def test_the_configured_settings_are_listed_in_order_and_a_node_count_names_its_method(
    monte_carlo_port,
):
    """The settings of a configured stage are listed in the order of their
    declarations, and the node count `n_Ψ_nodes` names `!gauss_hermite`, the
    method that reads it."""
    configured = copy_native(monte_carlo_port).configure(
        {"settings": {"n_sim": 100, "n_Ψ_nodes": 7, "n_θ_nodes": 5}}
    )
    assert list(configured.settings) == ["n_sim", "n_Ψ_nodes", "n_θ_nodes"]
    assert str(configured.settings["n_Ψ_nodes"]).endswith("by !gauss_hermite")


# a configured value, the declarations of a later addition, the rule of the
# refusal of that addition, and the value that corrects the configuration
@pytest.mark.parametrize(
    "values, declarations, rule, corrected",
    [
        ({"n_k": -1}, "n_k : ℕ\n", "setting-outside-set", {"n_k": 3}),
        ({}, "n_k : ℕ\n", "setting-unvalued", {"n_k": 3}),
        (
            {"k_min": 0.1, "k_max": 1, "n_k": 1},
            "k_min : ℝ\nk_max : ℝ\nn_k : ℕ\n"
            "dcsn_to_arvl.evaluate.method : !Linear\n"
            "dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))\n",
            "grid-bounds",
            {"n_k": 3},
        ),
        (
            {"tol": -1},
            "tol : ℝ\ndcsn_to_arvl.method : !vfi(tol=tol)\n",
            "method-option-value",
            {"tol": 1e-6},
        ),
    ],
    ids=("outside-set", "unvalued", "grid-count", "method-option"),
)
def test_methodize_checks_the_settings_configured_before_against_a_new_addition(
    buffer_stock, values, declarations, rule, corrected
):
    """`methodize` refuses an addition whose declarations or methods the
    settings configured before do not meet, leaving the stage as it was, and
    reads it once the settings are corrected."""
    stage = copy_native(buffer_stock)
    stage.configure(values)
    before = stage.encoding()
    source = addition_of_text("@methods: buffer_stock\n" + declarations)
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(source)
    assert refused.value.rule == rule
    assert stage.encoding() == before
    stage.configure(corrected)
    stage.methodize(source)
    assert dict(stage.bindings.settings) == {**values, **corrected}


@pytest.fixture(scope="module")
def arrival_signatures(buffer_stock):
    """The signature of the backward arrival builder of buffer-stock before
    an addition types `!vfi` on it, after, and after the same addition is
    read a second time."""
    stage = copy_native(buffer_stock)
    bare = stage.builder["dcsn", "arvl"].signature()
    source = addition_of_text("@methods: buffer_stock\ndcsn_to_arvl.method : !vfi\n")
    stage.methodize(source)
    typed = stage.builder["dcsn", "arvl"].signature()
    stage.methodize(source)
    equal = stage.builder["dcsn", "arvl"].signature()
    return bare, typed, equal


def test_two_signatures_are_equal_when_their_fields_and_typed_components_are(arrival_signatures):
    """Two signatures of one builder with the same fields are equal, and hash
    alike, when the same components are typed at the builder, and differ
    when they are not."""
    bare, typed, equal = arrival_signatures
    assert bare != typed
    assert not bare == typed
    assert (bare.inputs, bare.outputs) == (typed.inputs, typed.outputs)
    assert equal == typed
    assert len({bare, typed, equal}) == 2


def test_a_signature_unpacks_into_its_inputs_and_its_outputs(arrival_signatures):
    """A signature unpacks into its inputs and its outputs."""
    _, typed, _ = arrival_signatures
    inputs, outputs = typed
    assert (inputs, outputs) == (typed.inputs, typed.outputs)


def test_a_signature_refuses_an_assignment_to_its_components(arrival_signatures):
    """A signature refuses an assignment to its typed components."""
    _, typed, _ = arrival_signatures
    with pytest.raises(AttributeError):
        typed.components = ()


# The typing entries of a methods file


@pytest.fixture(scope="module")
def cons_port_methods_text():
    """The text of the methods file of the cons-port consumption stage."""
    return CONS_PORT_METHODS.read_text(encoding="utf-8")


def test_typing_entries_answers_each_entry_of_a_methods_file_by_the_address_it_types(
    cons_port_methods_text,
):
    """`typing_entries` answers each typing entry and handler binding of a
    methods file, an entry in the bracket of a block under that block, with
    its subject, its value and its line."""
    entries = typing_entries(cons_port_methods_text, str(CONS_PORT_METHODS))
    assert list(entries) == [
        "policy.method",
        "policy.handler",
        "policy.grid",
        "cntn_to_dcsn.evaluate.method",
        "cntn_to_dcsn.evaluate.grid",
    ]
    # line 38 of the file is the entry `| evaluate.method : !Linear` in the
    # bracket of the block `cntn_to_dcsn`
    evaluation = entries["cntn_to_dcsn.evaluate.method"]
    assert (evaluation.subject, evaluation.value, evaluation.span.line) == (
        "evaluate.method",
        "!Linear",
        38,
    )


def test_write_typing_entry_replaces_the_value_of_one_entry_and_keeps_every_other_character(
    cons_port_methods_text,
):
    """`write_typing_entry` answers the text with the value of one entry
    replaced and every other character kept."""
    text = cons_port_methods_text
    written = write_typing_entry(
        text, str(CONS_PORT_METHODS), "cntn_to_dcsn.evaluate", "method", "!pchip"
    )
    assert written.count("evaluate.method : !pchip") == 1
    assert written.replace("evaluate.method : !pchip", "evaluate.method : !Linear", 1) == text


def test_write_typing_entry_appends_an_entry_at_file_level_where_the_text_writes_none(
    cons_port_methods_text,
):
    """`write_typing_entry` appends an entry at file level where the text
    writes none, and `typing_entries` reads it back."""
    text = cons_port_methods_text
    appended = write_typing_entry(
        text, str(CONS_PORT_METHODS), "arvl_to_dcsn", "method", "!deterministic"
    )
    assert appended == text + "arvl_to_dcsn.method : !deterministic\n"
    assert typing_entries(appended)["arvl_to_dcsn.method"].value == "!deterministic"


def test_write_typing_entry_refuses_a_value_that_the_grammar_does_not_read(
    cons_port_methods_text,
):
    """`write_typing_entry` refuses a value that the grammar does not read
    under `syntax`."""
    with pytest.raises(ConstructionError) as refused:
        write_typing_entry(
            cons_port_methods_text, str(CONS_PORT_METHODS), "policy", "method", "!egm("
        )
    assert refused.value.rule == "syntax"


def test_write_typing_entry_refuses_an_entry_whose_place_the_parser_does_not_record(
    cons_port_methods_text,
):
    """`write_typing_entry` refuses an entry whose place the parser does not
    record, with the advice to write it in the editor."""
    text = cons_port_methods_text
    entries = typing_entries(text, str(CONS_PORT_METHODS))
    # the line `m[>] = a + c[>] :: [id=grid]` of the block `policy` carries
    # the address of the entry `grid` in the bracket of that block, so the
    # entry's place is not recorded
    assert entries["policy.grid"].span is None
    with pytest.raises(ValueError, match="write the entry in the editor"):
        write_typing_entry(
            text, str(CONS_PORT_METHODS), "policy", "grid", "!Cartesian(a=(a_min, a_max, n_a))"
        )
