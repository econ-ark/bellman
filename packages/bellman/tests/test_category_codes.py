"""Category codes: a finite set of integers whose members carry names, read
through their codes in kernels and across periods."""

import json
from typing import NamedTuple

import pytest
from stage_builders import stage_from_text
from stage_texts import changed, line_of

from bellman.display.encoding_checks import validate_encoding
from bellman.native import records
from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.stage import make_stage, to_source
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.trellis import connection_report, elaborate_trellis

# the origin under which each stage text of this file is elaborated
ORIGIN = "household_status.bl"


# the identity of the named set `HouseholdStatus` among the definitions of the
# household stage
SET_IDENTITY = "household_status:set:HouseholdStatus"


# the comprehension that defines the set of the household's status
COMPREHENSION = "{i : ℤ | i >= 0, i <= 1}"


# the annotation of that set: the marker `!categories`, the identifier
# `household_status` and the category of each code
ANNOTATION = "[!categories household_status, newborn=0, old=1]"


# the same codes as the arguments of `records.CategoryCodes`: the identifier,
# then each code with its category
HOUSEHOLD_CODES = ("household_status", ((0, "newborn"), (1, "old")))


# The household stage of the documentation of stages, with its three status
# fields declared on the named set. The status at decision, n, is the status
# at arrival, n_pre; the status next period is n_next = 1, old; the value is
# the payment 100 − 120·n plus the discounted continuation value.
HOUSEHOLD = """@stage: household_status

β : (0,1)              :: ["discount factor"]

HouseholdStatus := {i : ℤ | i >= 0, i <= 1} :: [!categories household_status, newborn=0, old=1]

n_pre  : HouseholdStatus
n      : HouseholdStatus
n_next : HouseholdStatus

[id=arvl_to_dcsn, (n_pre) : !arvl -> (n) : !dcsn] {
    n = n_pre                    :: [id=status]
}
[id=dcsn_to_cntn, (n) : !dcsn -> (n_next) : !cntn] {
    n_next = 1                   :: [id=ageing]
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 100 - 120*n + β*V[>]     :: [id=value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                     :: [id=value]
}
"""


# The forward household stage: the household stage cut before its block
# `cntn_to_dcsn`, with its declarations and its two forward blocks, which read
# n_pre and write n and n_next. Its connections are those of the whole stage,
# and its encoding is smaller.
HOUSEHOLD_FORWARD = HOUSEHOLD[: HOUSEHOLD.index("[id=cntn_to_dcsn")]


# the three kinds of pair that `compatibility_by_kind` answers, in its order
KINDS = ("authored", "inferred", "inter-period")


def household_with(codes=ANNOTATION, body=COMPREHENSION, text=HOUSEHOLD):
    """The household stage, or the stage `text`, with the annotation `codes`
    and the body `body` in place of the set's."""
    return changed(text, (ANNOTATION, codes), (COMPREHENSION, body))


def household_with_lines(lines, after=ANNOTATION, text=HOUSEHOLD):
    """The household stage, or the stage `text`, with `lines` written after
    the line that ends with `after`, the set's line unless another is
    named."""
    return changed(text, (after + "\n", f"{after}\n{lines}\n"))


# the annotation of the set with the codes the other way round: 0 is old and
# 1 is newborn
OPPOSITE_ANNOTATION = "[!categories household_status, newborn=1, old=0]"


# the forward household stage with the codes the other way round
OPPOSITE_CODES = household_with(codes=OPPOSITE_ANNOTATION, text=HOUSEHOLD_FORWARD)


# the forward household stage whose annotation writes no identifier, so that
# its categories belong to the set of this one stage text
LOCAL = household_with(codes="[!categories, newborn=0, old=1]", text=HOUSEHOLD_FORWARD)


@pytest.fixture(scope="module")
def household_stage():
    """The symbolic household stage."""
    return stage_from_text(HOUSEHOLD, ORIGIN)


@pytest.fixture(scope="module")
def forward_stage():
    """The symbolic stage of the household stage with its two forward blocks
    alone."""
    return stage_from_text(HOUSEHOLD_FORWARD, ORIGIN)


@pytest.fixture(scope="module")
def forward_term():
    """The parsed term of the household stage with its two forward blocks
    alone."""
    term, _ = parse_with_spans(HOUSEHOLD_FORWARD, ORIGIN)
    return term


@pytest.fixture(scope="module")
def forward_encoding(forward_stage):
    """The encoding of the forward household stage, written to JSON and read
    back, which `validate_encoding` admits."""
    return validate_encoding(json.loads(json.dumps(forward_stage.encoding())))


# the set's denotation and the domains of its fields


def test_the_denotation_of_a_set_with_category_codes_holds_the_set_and_its_map_of_codes(
    household_stage,
):
    """The denotation of the household set holds two objects, the set as
    written and its map of codes, printed as the comprehension and as
    `0 ↦ newborn, 1 ↦ old (categories household_status)`."""
    record = household_stage.definitions[SET_IDENTITY]
    denoted = household_stage.definitions.denote(SET_IDENTITY).denoted
    assert [(d.symbol, d.expression) for d in denoted] == [
        ("HouseholdStatus", record.equations[0]),
        ("HouseholdStatus", record.categories),
    ]
    assert [d.rule for d in denoted] == [
        "{i ∈ ℤ | i ≥ 0 ∧ i ≤ 1}",
        "0 ↦ newborn, 1 ↦ old (categories household_status)",
    ]


@pytest.mark.parametrize(
    "denotation_of",
    [
        pytest.param(lambda stage: stage.denote(), id="the-stage"),
        pytest.param(
            lambda stage: stage.builder["dcsn", "cntn"].denote(),
            id="the-builder-from-decision-to-continuation",
        ),
    ],
)
def test_the_definitions_referenced_by_a_denotation_hold_the_denotation_of_the_coded_set(
    household_stage, denotation_of
):
    """The definitions referenced by the denotation of the household stage,
    and by that of its builder from decision to continuation, hold the two
    objects of the denotation of the household set."""
    denoted = household_stage.definitions.denote(SET_IDENTITY).denoted
    # the set as written and its map of codes, so that the comparison below
    # is not one of two empty lists
    assert len(denoted) == 2
    referenced = denotation_of(household_stage).definitions
    assert [d for d in referenced if d.identity == SET_IDENTITY] == list(denoted)


def test_each_state_field_declared_on_a_set_with_category_codes_has_that_set_as_its_domain(
    household_stage,
):
    """The domain of each state field of the household stage is the named
    set `HouseholdStatus`."""
    domains = {
        str(identity): to_source(sort.domain)
        for identity, sort in household_stage.fields().items()
        if sort.role == "state"
    }
    assert domains == dict.fromkeys(
        ("household_status:arvl:n_pre", "household_status:dcsn:n", "household_status:cntn:n_next"),
        "HouseholdStatus",
    )


# the forms that the marker `!categories` admits and refuses


class RefusedAt(NamedTuple):
    """A row whose text is refused under `category-codes` at the line that
    holds `at` and at `address`, the file position of that line where
    `address` is None, with a message that holds each of `phrases`."""

    at: str
    phrases: tuple
    address: str | None = None


class ElaboratesWith(NamedTuple):
    """A row whose text elaborates: the tags of its set as written, the
    arguments of the set's `CategoryCodes` or None, and the set as its card
    prints it."""

    tags: tuple
    codes: tuple | None
    printed_set: str


# the household stage whose marked set is bounded above by a parameter J,
# which the marker refuses; without its annotation the set elaborates
BOUNDED_BY_A_PARAMETER = changed(
    household_with(body="{i : ℤ | i >= 0, i <= J}"), ("β : (0,1)", "J : ℕ\nβ : (0,1)")
)


def refused_marked_set(case, *phrases, **change):
    """A row of a fault of the marked set: the household stage with `change`
    made by `household_with`, refused at the set's line with a message that
    names the set and each of `phrases`."""
    expected = RefusedAt("HouseholdStatus :=", ("HouseholdStatus", *phrases))
    return pytest.param(household_with(**change), expected, id=case)


MARKED_SETS = [
    # the entries and the marker of the set
    refused_marked_set(
        "a-code-outside-the-range",
        "`old=2`",
        "outside",
        "the member 1 has no category",
        codes=ANNOTATION.replace("old=1", "old=2"),
    ),
    refused_marked_set(
        "a-reserved-key",
        "`!categories=household_status`",
        codes=ANNOTATION.replace("!categories ", "!categories="),
    ),
    refused_marked_set("a-bare-tag", "`retired`", codes=ANNOTATION.replace("]", ", retired]")),
    refused_marked_set(
        "a-single-quoted-entry", "`'retired'`", codes=ANNOTATION.replace("]", ", 'retired']")
    ),
    refused_marked_set(
        "minus-0-repeats-0", "`old=-0`", codes=ANNOTATION.replace("old=1", "old=-0")
    ),
    refused_marked_set(
        "a-second-marker",
        "`!categories age`",
        codes=ANNOTATION.replace(", newborn", ", !categories age, newborn"),
    ),
    refused_marked_set(
        "a-marker-of-two-words",
        "`!categories household status`",
        codes=ANNOTATION.replace("household_status", "household status"),
    ),
    refused_marked_set(
        "a-code-that-is-no-integer", "`newborn=zero`", codes=ANNOTATION.replace("=0", "=zero")
    ),
    refused_marked_set(
        "a-tab-after-the-marker",
        "U+0009",
        codes=ANNOTATION.replace("!categories ", "!categories\t"),
    ),
    # the set the marker stands on
    refused_marked_set("the-natural-numbers-from-0", "ℕ", body="{i : ℕ | i >= 0, i <= 1}"),
    refused_marked_set("a-binder-over-the-reals", "`ℝ`", body="{i : ℝ | i >= 0, i <= 1}"),
    refused_marked_set("one-bound", "upper bound", body="{i : ℤ | i >= 0}"),
    refused_marked_set("an-equality-condition", "`i = 1`", body="{i : ℤ | i >= 0, i = 1}"),
    refused_marked_set("an-empty-range", "leave no integer", body="{i : ℤ | i > 0, i < 1}"),
    refused_marked_set("the-integers", "`ℤ`", body="ℤ"),
    refused_marked_set("an-interval", "`[0, 1]`", body="[0, 1]"),
    refused_marked_set("an-integer-range", "`{0, …, 1}`", body="{0, …, 1}"),
    refused_marked_set("listed-integers", "`{0, 1}`", body="{0, 1}"),
    pytest.param(
        BOUNDED_BY_A_PARAMETER,
        RefusedAt("HouseholdStatus :=", ("HouseholdStatus", "`i <= J`")),
        id="a-parameter-bound",
    ),
    # a set of names and a restriction of the coded set, each marked beside it
    pytest.param(
        household_with_lines(f"Labels := {{newborn, old}} :: {ANNOTATION}"),
        RefusedAt("Labels :=", ("Labels", "`{newborn, old}`")),
        id="a-set-of-names",
    ),
    pytest.param(
        household_with_lines(
            "Old := {j : HouseholdStatus | j >= 1} :: [!categories household_status, old=1]"
        ),
        RefusedAt("Old :=", ("Old", "`HouseholdStatus`")),
        id="a-restricted-coded-set",
    ),
    # texts that elaborate
    pytest.param(
        HOUSEHOLD,
        ElaboratesWith(
            ("!categories household_status", "newborn=0", "old=1"),
            HOUSEHOLD_CODES,
            "{i ∈ ℤ | i ≥ 0 ∧ i ≤ 1}",
        ),
        id="the-household-set-as-written",
    ),
    pytest.param(
        household_with(codes='["!categories household_status", "newborn=0", "old=1"]', body="ℤ"),
        ElaboratesWith(('"!categories household_status"', '"newborn=0"', '"old=1"'), None, "ℤ"),
        id="double-quoted-entries-on-an-unmarked-set",
    ),
    pytest.param(
        household_with(codes="[!categories_status]", body="ℤ"),
        ElaboratesWith(("!categories_status",), None, "ℤ"),
        id="a-longer-word-than-the-marker",
    ),
    pytest.param(
        changed(BOUNDED_BY_A_PARAMETER, (" :: " + ANNOTATION, "")),
        ElaboratesWith((), None, "{i ∈ ℤ | i ≥ 0 ∧ i ≤ J}"),
        id="an-unmarked-comprehension-with-a-parameter-bound",
    ),
    pytest.param(
        household_with(
            codes=ANNOTATION.replace(", newborn", ', id=status, "the status", newborn')
        ),
        ElaboratesWith(
            ("!categories household_status", "id=status", '"the status"', "newborn=0", "old=1"),
            HOUSEHOLD_CODES,
            "{i ∈ ℤ | i ≥ 0 ∧ i ≤ 1}",
        ),
        id="an-id-and-a-description-beside-the-codes",
    ),
    # the bounds −1 and 0, written either way round, strictly and with signs;
    # the transition's 1 lies outside them and stays a recorded condition
    pytest.param(
        household_with(
            codes="[!categories household_status, newborn=-1, old=0]",
            body="{i : ℤ | -1 <= i, i > -2, i < 1}",
        ),
        ElaboratesWith(
            ("!categories household_status", "newborn=-1", "old=0"),
            ("household_status", ((-1, "newborn"), (0, "old"))),
            "{i ∈ ℤ | −1 ≤ i ∧ i > −2 ∧ i < 1}",
        ),
        id="bounds-written-either-way-strict-or-negative",
    ),
]


@pytest.mark.parametrize("text, expected", MARKED_SETS)
def test_a_marked_set_elaborates_only_in_its_admitted_form_and_an_unmarked_set_keeps_its_meaning(
    text, expected
):
    """A set definition elaborates with the tags and the codes of its row
    where its annotation and its set take a form that the marker
    `!categories` admits, or where it writes no marker and keeps the meaning
    of its set, and is refused under `category-codes` at its line
    otherwise."""
    if isinstance(expected, ElaboratesWith):
        stage = stage_from_text(text, ORIGIN)
        record = stage.definitions[SET_IDENTITY]
        assert record.tags == expected.tags
        codes = None if expected.codes is None else records.CategoryCodes(*expected.codes)
        assert record.categories == codes
        denoted = stage.definitions.denote(SET_IDENTITY).denoted
        assert [d.expression for d in denoted] == [record.equations[0]] + (
            [] if codes is None else [codes]
        )
        assert denoted[0].rule == expected.printed_set
    else:
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(text, ORIGIN)
        line = line_of(text, expected.at)
        address = expected.address or f"{ORIGIN}:{line}"
        assert (refused.value.rule, refused.value.address, refused.value.line) == (
            "category-codes",
            address,
            line,
        )
        message = refused.value.message
        assert [phrase for phrase in expected.phrases if phrase not in message] == []


def test_the_marker_of_categories_written_alone_is_refused_alike_bracketed_bare_or_quoted():
    """The marker `!categories` written as the whole annotation of the set,
    in brackets, bare or in double quotes, is refused alike under
    `category-codes` at the set's line, with one message that says that it
    writes no category."""
    bracketed, bare, quoted = (
        household_with(codes=alone) for alone in ("[!categories]", "!categories", '"!categories"')
    )
    with pytest.raises(ConstructionError) as refused_bracketed:
        stage_from_text(bracketed, ORIGIN)
    with pytest.raises(ConstructionError) as refused_bare:
        stage_from_text(bare, ORIGIN)
    with pytest.raises(ConstructionError) as refused_quoted:
        stage_from_text(quoted, ORIGIN)
    refusals = [refused_bracketed.value, refused_bare.value, refused_quoted.value]
    line = line_of(bracketed, "HouseholdStatus :=")
    message = refusals[0].message
    assert [(error.rule, error.address, error.line, error.message) for error in refusals] == [
        ("category-codes", f"{ORIGIN}:{line}", line, message)
    ] * 3
    phrases = ("HouseholdStatus", "writes no category")
    assert [phrase for phrase in phrases if phrase not in message] == []


MARKER_ON_ANOTHER_ITEM = [
    pytest.param(
        changed(
            HOUSEHOLD,
            ("n      : HouseholdStatus\n", f"n      : HouseholdStatus :: {ANNOTATION}\n"),
        ),
        RefusedAt("n      : HouseholdStatus ::", ("`!categories household_status`",)),
        id="a-field-declaration",
    ),
    pytest.param(
        household_with_lines(
            f"𝑝(m : HouseholdStatus) := 100 - 120*m :: {ANNOTATION}",
            after="n_next : HouseholdStatus",
        ),
        RefusedAt("𝑝(m", ("𝑝", "`!categories household_status`")),
        id="a-function",
    ),
    pytest.param(
        changed(HOUSEHOLD, (":: [id=ageing]", ":: [id=ageing, !categories household_status]")),
        RefusedAt("n_next = 1", ("`!categories household_status`",), "dcsn_to_cntn.ageing"),
        id="a-line",
    ),
    pytest.param(
        changed(HOUSEHOLD, ("[id=dcsn_to_cntn, (n)", "[id=dcsn_to_cntn, !categories, (n)")),
        RefusedAt("[id=dcsn_to_cntn", ("`!categories`",), "dcsn_to_cntn"),
        id="a-block-header",
    ),
]


@pytest.mark.parametrize("text, expected", MARKER_ON_ANOTHER_ITEM)
def test_the_marker_of_categories_is_refused_on_a_field_declaration_a_function_a_line_or_a_header(
    text, expected
):
    """The marker `!categories` written on a field declaration, a function,
    a line or a block header is refused under `category-codes` at that
    item, with a message that quotes the marker."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, ORIGIN)
    line = line_of(text, expected.at)
    address = expected.address or f"{ORIGIN}:{line}"
    assert (refused.value.rule, refused.value.address, refused.value.line) == (
        "category-codes",
        address,
        line,
    )
    message = refused.value.message
    assert [phrase for phrase in expected.phrases if phrase not in message] == []


def test_a_block_header_that_writes_another_set_for_a_coded_field_is_refused_at_the_block():
    """A block header that writes `ℤ` for the field `n`, which is declared on
    the coded set `HouseholdStatus`, is refused under `category-codes` at
    the block, with a message that names both sets."""
    text = changed(HOUSEHOLD, ("[id=dcsn_to_cntn, (n)", "[id=dcsn_to_cntn, (n : ℤ)"))
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, ORIGIN)
    line = line_of(text, "[id=dcsn_to_cntn")
    assert (refused.value.rule, refused.value.address, refused.value.line) == (
        "category-codes",
        "dcsn_to_cntn",
        line,
    )
    message = refused.value.message
    assert [phrase for phrase in ("`HouseholdStatus`", "`ℤ`") if phrase not in message] == []


# the kernels, which compute with the codes


def category_of_each_code(stage, domain):
    """The category of each code of the named set `domain`: the map that the
    set's denotation holds as its second object."""
    _, coded = stage.definitions.denote(f"household_status:set:{domain.name}").denoted
    return dict(coded.expression.codes)


def calibrated_kernels(text):
    """The stage `text` calibrated at β = 0.96, with the push-forward of its
    law of motion and the aggregation of its value line."""
    stage = stage_from_text(text, ORIGIN).calibrate({"β": 0.96})
    law = stage.builder.fwd["dcsn_to_cntn"].primitives["Pushforward"]
    value = stage.builder.bwd["cntn_to_dcsn"].primitives["Aggregation"]
    return stage, law, value


def kernel_outcomes(stage, law, value):
    """The next status and the value at V≻ = 0 that the compiled kernels give
    at each code of the set of the argument n of the law, and the next
    category and the payment of each category, read through the maps that
    the denotations of the sets of n and of n_next hold."""
    (status,) = law.kernel().arguments
    now = category_of_each_code(stage, status[1])
    then = category_of_each_code(stage, stage.fields()["household_status:cntn:n_next"].domain)
    law_kernel, value_kernel = law.compile_kernel(), value.compile_kernel()
    law_parameters = law.kernel().parameter_values
    value_parameters = value.kernel().parameter_values
    # the law reads n alone; the aggregation reads V≻, here 0, and then n
    numbers = {
        code: (
            int(law_kernel(code, *law_parameters)),
            float(value_kernel(0.0, code, *value_parameters)),
        )
        for code in now
    }
    decoded = {now[code]: (then[after], paid) for code, (after, paid) in numbers.items()}
    return numbers, decoded


def test_the_compiled_law_of_motion_and_value_aggregation_compute_with_the_integer_codes():
    """After calibration at β = 0.96, the compiled law of motion of the
    household stage gives the next status 1 at each of the codes 0 and 1,
    where the compiled aggregation of its value line at V≻ = 0 gives the
    payment 100 at 0 and −20 at 1."""
    stage, law, value = calibrated_kernels(HOUSEHOLD)
    # the law reads n alone, and the aggregation reads n, in the same set,
    # as its second argument, as `kernel_outcomes` calls them
    (status,) = law.kernel().arguments
    assert status[0] == "n" and value.kernel().arguments[1] == status
    numbers, _ = kernel_outcomes(stage, law, value)
    assert numbers == {0: (1, 100.0), 1: (1, -20.0)}


def test_through_the_map_of_codes_the_kernels_give_each_category_its_next_category_and_payment():
    """Read through the maps that the denotations of the sets of n and of
    n_next hold, the kernels of the household stage take the newborn
    household and the old one both to old, with the payments 100 and −20."""
    stage, law, value = calibrated_kernels(HOUSEHOLD)
    # the law reads n alone, and the aggregation reads n, in the same set,
    # as its second argument, as `kernel_outcomes` calls them
    (status,) = law.kernel().arguments
    assert status[0] == "n" and value.kernel().arguments[1] == status
    _, decoded = kernel_outcomes(stage, law, value)
    assert decoded == {"newborn": ("old", 100.0), "old": ("old", -20.0)}


def test_full_recoding_keeps_the_outcome_of_each_category_and_recoding_the_codes_alone_does_not():
    """The household stage with its codes, its law of motion and its payment
    swapped together, `old=0, newborn=1`, `n_next = 0` and
    `V = −20 + 120·n + β·V≻`, gives each category the next category and the
    payment of the household stage, where the stage with its codes alone
    swapped gives others."""
    swapped_codes = "[!categories household_status, old=0, newborn=1]"
    recoded = changed(
        household_with(codes=swapped_codes),
        ("n_next = 1 ", "n_next = 0 "),
        ("V = 100 - 120*n", "V = -20 + 120*n"),
    )
    relabelled = household_with(codes=swapped_codes)
    # in each stage the law reads n alone, and the aggregation reads n, in the
    # same set, as its second argument, as `kernel_outcomes` calls them
    stage, law, value = calibrated_kernels(HOUSEHOLD)
    (status,) = law.kernel().arguments
    assert status[0] == "n" and value.kernel().arguments[1] == status
    _, decoded = kernel_outcomes(stage, law, value)
    stage, law, value = calibrated_kernels(recoded)
    (status,) = law.kernel().arguments
    assert status[0] == "n" and value.kernel().arguments[1] == status
    assert kernel_outcomes(stage, law, value)[1] == decoded
    stage, law, value = calibrated_kernels(relabelled)
    (status,) = law.kernel().arguments
    assert status[0] == "n" and value.kernel().arguments[1] == status
    assert kernel_outcomes(stage, law, value)[1] == {
        "old": ("newborn", 100.0),
        "newborn": ("newborn", -20.0),
    }


# the compatibility of two coded domains joined by a pair


def compatibility_by_kind(writer, reader):
    """The compatibility and the reason of the pair that copies the
    continuation field `n_next` of the household text `writer` into the
    arrival field of the household text `reader`, for each of `KINDS`:
    authored within a period, into `n_pre`; inferred within a period, into
    the reader's arrival field renamed `n_next`, its continuation field
    renamed `n_after`; and authored between periods by `inter_connectors[0]`,
    which joins the writer in `periods[1]` to the reader in `periods[0]`. An
    inferred candidate that is not selected answers the status its rule
    names."""
    writing = stage_from_text(writer, ORIGIN)
    reading = stage_from_text(reader, ORIGIN)
    by_name = stage_from_text(
        reader.replace("n_next", "n_after").replace("n_pre", "n_next"), ORIGIN
    )
    trellises = (
        ([{"stages": {"W": writing, "R": reading}, "connectors": [{"W.n_next": "R.n_pre"}]}], []),
        ([{"stages": {"W": writing, "R": by_name}, "connectors": []}], []),
        (
            [
                {"stages": {"R": reading}, "connectors": []},
                {"stages": {"W": writing}, "connectors": []},
            ],
            [{"n_next": "n_pre"}],
        ),
    )
    found = {}
    for kind, (periods, inter_connectors) in zip(KINDS, trellises):
        report = connection_report(
            elaborate_trellis({"periods": periods, "inter_connectors": inter_connectors})
        )
        (found[kind],) = [
            (pair.compatibility, pair.reason) for pair in report.pairs if pair.reading.key == "R"
        ] + [
            (rejected.rule.removeprefix("candidate-"), rejected.message)
            for rejected in report.rejected
            if rejected.reading.key == "R"
        ]
    return found


def coded_domain_pairs():
    """The rows of the table of pairs: a writing and a reading text, each a
    change of the forward household stage, and the compatibility of the
    pair for each of `KINDS`, in that order."""
    forward = HOUSEHOLD_FORWARD
    fields = "n_pre  : HouseholdStatus\nn      : HouseholdStatus\nn_next : HouseholdStatus\n"
    integers = changed(forward, (f"{COMPREHENSION} :: {ANNOTATION}", "ℤ"))
    entries_reversed = household_with(
        codes="[!categories household_status, old=1, newborn=0]", text=forward
    )
    another_identifier = household_with(
        codes=ANNOTATION.replace("household_status", "age_group"), text=forward
    )
    uncoded = changed(forward, (" :: " + ANNOTATION, ""))
    # the restriction of the coded set to old, written into and read from
    old = household_with_lines("Old := {j : HouseholdStatus | j >= 1}", text=forward)
    written_into_old = changed(old, ("n_next : HouseholdStatus", "n_next : Old"))
    read_from_old = changed(old, ("n_pre  : HouseholdStatus", "n_pre  : Old"))
    # the product of the coded set and the positive reals, on all three fields
    product = changed(
        forward,
        (fields, fields.replace("HouseholdStatus\n", "HouseholdStatus × ℝ₊\n")),
        ("n_next = 1 ", "n_next = n "),
    )
    product_with_opposite_codes = changed(product, (ANNOTATION, OPPOSITE_ANNOTATION))
    # the restriction by the parameter k, read; then read and written
    read_from_eligible = changed(
        household_with_lines("k : ℤ\nEligible := {j : HouseholdStatus | j >= k}", text=forward),
        ("n_pre  : HouseholdStatus", "n_pre  : Eligible"),
    )
    eligible_on_both_sides = changed(
        read_from_eligible, ("n_next : HouseholdStatus", "n_next : Eligible")
    )
    eligible_under_another_identifier = changed(
        eligible_on_both_sides, (ANNOTATION, ANNOTATION.replace("household_status", "age_group"))
    )
    # the restriction by the equality j = 1, written into and read from
    one = household_with_lines("One := {j : HouseholdStatus | j = 1}", text=forward)
    written_into_one = changed(one, ("n_next : HouseholdStatus", "n_next : One"))
    read_from_one = changed(one, ("n_pre  : HouseholdStatus", "n_pre  : One"))
    bounded = changed(
        household_with_lines(
            "k : ℤ\nBounded := {j : HouseholdStatus | j >= 1, j <= k}", text=forward
        ),
        ("n_next : HouseholdStatus", "n_next : Bounded"),
    )
    called = changed(
        household_with_lines(
            "k : ℤ\n𝑓(x : ℤ) := x + k\nCalled := {j : HouseholdStatus | j >= 𝑓(0)}",
            text=forward,
        ),
        ("n_pre  : HouseholdStatus", "n_pre  : Called"),
        ("n_next : HouseholdStatus", "n_next : Called"),
    )
    local_in_another_text = changed(LOCAL, ("discount", "the discount"))
    # a stage that writes n_next = 1 − n into the set with the opposite codes
    recoding = changed(
        household_with_lines(f"Recoded := {COMPREHENSION} :: {OPPOSITE_ANNOTATION}", text=forward),
        ("n_next : HouseholdStatus", "n_next : Recoded"),
        ("n_next = 1 ", "n_next = 1 - n "),
    )
    compatible = ("compatible",) * 3
    incompatible = ("incompatible",) * 3
    not_established = ("not-established",) * 3
    return [
        pytest.param(integers, integers, compatible, id="two-domains-of-integers-without-codes"),
        pytest.param(forward, forward, compatible, id="one-identifier"),
        pytest.param(forward, entries_reversed, compatible, id="entries-reversed"),
        pytest.param(forward, another_identifier, incompatible, id="another-identifier"),
        pytest.param(forward, OPPOSITE_CODES, incompatible, id="opposite-codes"),
        pytest.param(forward, uncoded, incompatible, id="coded-into-uncoded"),
        pytest.param(uncoded, forward, incompatible, id="uncoded-into-coded"),
        pytest.param(written_into_old, forward, compatible, id="restriction-into-the-set"),
        pytest.param(forward, read_from_old, incompatible, id="set-into-the-restriction"),
        pytest.param(product, product, compatible, id="agreeing-products"),
        pytest.param(
            product, product_with_opposite_codes, incompatible, id="a-conflicting-product-factor"
        ),
        pytest.param(
            forward, read_from_eligible, not_established, id="a-restriction-by-a-parameter"
        ),
        pytest.param(
            eligible_on_both_sides,
            OPPOSITE_CODES,
            not_established,
            id="a-restriction-that-may-be-empty",
        ),
        pytest.param(written_into_one, forward, compatible, id="an-equality-into-the-set"),
        pytest.param(forward, read_from_one, incompatible, id="the-set-into-an-equality"),
        pytest.param(bounded, read_from_old, compatible, id="a-literal-bound-beside-a-parameter"),
        pytest.param(
            eligible_on_both_sides,
            eligible_under_another_identifier,
            not_established,
            id="one-restriction-under-two-identifiers",
        ),
        pytest.param(called, called, not_established, id="a-condition-that-calls-a-function"),
        pytest.param(
            LOCAL, local_in_another_text, incompatible, id="two-texts-without-an-identifier"
        ),
        pytest.param(forward, recoding, compatible, id="into-the-recoding-stage"),
        pytest.param(recoding, OPPOSITE_CODES, compatible, id="out-of-the-recoding-stage"),
        # one set within a period; between periods k names two parameters
        pytest.param(
            eligible_on_both_sides,
            eligible_on_both_sides,
            ("compatible", "compatible", "not-established"),
            id="one-restriction-by-a-parameter-on-both-sides",
        ),
    ]


@pytest.mark.parametrize("writer, reader, statuses", coded_domain_pairs())
def test_the_compatibility_of_two_domains_follows_from_their_maps_of_codes_and_their_restrictions(
    writer, reader, statuses
):
    """The connection report finds the domains of the writing and the reading
    text of each row compatible, incompatible or not established, as the
    row states for an authored, an inferred and an inter-period pair, from
    their maps of codes and their restrictions."""
    found = {kind: status for kind, (status, _) in compatibility_by_kind(writer, reader).items()}
    assert found == dict(zip(KINDS, statuses))


def test_a_set_whose_categories_carry_no_identifier_joins_its_next_period_occurrence_by_its_text():
    """A set whose annotation writes no identifier is compatible with its
    occurrence in the next period of the same stage text, and not
    established where the stage is made from a term, which holds no digest
    of a text."""
    assert compatibility_by_kind(LOCAL, LOCAL)["inter-period"][0] == "compatible"
    without_text = make_stage(*parse_with_spans(LOCAL, ORIGIN))
    report = connection_report(
        elaborate_trellis(
            {
                "periods": [
                    {"stages": {"R": without_text}, "connectors": []},
                    {"stages": {"W": without_text}, "connectors": []},
                ],
                "inter_connectors": [{"n_next": "n_pre"}],
            }
        )
    )
    (pair,) = [pair for pair in report.pairs if pair.reading.key == "R"]
    assert pair.compatibility == "not-established" and "no digest" in pair.reason, pair.reason


def test_the_reason_of_an_incompatible_pair_of_coded_domains_writes_the_map_of_each_side():
    """The reason that the connection report gives for the incompatible
    authored pair into the opposite codes writes the map of codes of each
    side."""
    status, reason = compatibility_by_kind(HOUSEHOLD_FORWARD, OPPOSITE_CODES)["authored"]
    # the pair is incompatible, the case whose reason this test reads
    assert status == "incompatible"
    maps = ("0 ↦ newborn, 1 ↦ old", "0 ↦ old, 1 ↦ newborn")
    assert [phrase for phrase in maps if phrase not in reason] == [], reason


# the printed source, the abstract syntax and the encoding


def test_the_definition_of_a_coded_set_prints_to_source_without_its_annotation(forward_term):
    """The definition of the household set prints to source as the
    comprehension it writes, without its annotation."""
    statement = forward_term.items[2]  # the item after `@stage` and the declaration of β
    assert to_source(statement.core) == "HouseholdStatus := {i : ℤ | i >= 0, i <= 1}"


def test_the_printed_definition_of_a_coded_set_parses_to_an_equal_core(forward_term):
    """The source that the definition of the household set prints parses to
    a statement equal to the core of the definition, its statement without
    its annotation."""
    statement = forward_term.items[2]  # the item after `@stage` and the declaration of β
    printed = to_source(statement.core)
    # the item after `@stage`
    reparsed = parse_with_spans("@stage: x\n" + printed + "\n").term.items[1]
    assert to_json(reparsed.core) == to_json(statement.core)


def test_the_parsed_term_of_a_stage_with_category_codes_is_read_back_equal_from_its_json(
    forward_term,
):
    """The parsed term of the forward household stage, written by `to_json`
    to JSON text and read back by `from_json`, is equal to the term."""
    assert from_json(json.loads(json.dumps(to_json(forward_term)))) == forward_term


def test_the_entry_of_the_coded_set_alone_holds_its_codes_in_the_definitions_of_the_encoding(
    forward_encoding,
):
    """Among the definitions of the encoding of the forward household stage,
    the entry of the household set, and no other entry, holds the key
    `categories`, which holds its identifier and its codes."""
    entries = {entry["identity"]: entry for entry in forward_encoding["definitions"]}
    assert [identity for identity, entry in entries.items() if "categories" in entry] == [
        SET_IDENTITY
    ]
    assert entries[SET_IDENTITY]["categories"] == {
        "identifier": "household_status",
        "codes": [[0, "newborn"], [1, "old"]],
    }


def test_the_card_of_the_coded_set_under_derived_holds_its_codes_as_its_second_denoted_object(
    forward_encoding,
):
    """In the encoding of the forward household stage, the card of the
    household set under `derived` denotes a comprehension and then the
    category codes, which hold the identifier and the codes of the set."""
    order = [entry["identity"] for entry in forward_encoding["definitions"]]
    card = forward_encoding["derived"]["definitions"][order.index(SET_IDENTITY)]
    denoted = [item["fields"]["expression"] for item in card["value"]["fields"]["denoted"]]
    assert [expression["node"] for expression in denoted] == [
        "terms.Comprehension",
        "records.CategoryCodes",
    ]
    assert denoted[1]["fields"] == {
        "identifier": "household_status",
        "codes": [[0, "newborn"], [1, "old"]],
    }


def codes_that_decrease(encoding):
    """Reverse the codes in the entry of the household set among the
    definitions of `encoding`."""
    order = [entry["identity"] for entry in encoding["definitions"]]
    encoding["definitions"][order.index(SET_IDENTITY)]["categories"]["codes"].reverse()


def codes_on_a_parameter(encoding):
    """Write a map of codes into the entry of the parameter β among the
    definitions of `encoding`."""
    order = [entry["identity"] for entry in encoding["definitions"]]
    encoding["definitions"][order.index("household_status:parameter:β")]["categories"] = {
        "identifier": "household_status",
        "codes": [[0, "newborn"], [1, "old"]],
    }


def a_category_written_twice(encoding):
    """Write the category `newborn` for the code 1 in the map of codes of the
    card of the household set under `derived` in `encoding`."""
    order = [entry["identity"] for entry in encoding["definitions"]]
    card = encoding["derived"]["definitions"][order.index(SET_IDENTITY)]["value"]["fields"]
    card["denoted"][1]["fields"]["expression"]["fields"]["codes"][1][1] = "newborn"


@pytest.mark.parametrize(
    "fault, phrase",
    [
        pytest.param(codes_that_decrease, "increase strictly", id="codes-that-decrease"),
        pytest.param(codes_on_a_parameter, "writes no category map", id="codes-on-a-parameter"),
        pytest.param(
            a_category_written_twice,
            "names must be distinct",
            id="a-category-written-twice-on-the-card",
        ),
    ],
)
def test_validate_encoding_refuses_a_map_of_codes_out_of_order_misplaced_or_with_repeated_names(
    forward_encoding, fault, phrase
):
    """`validate_encoding`, which admits the encoding of the forward
    household stage, refuses a copy of it with the fault of the row: codes
    that decrease in the entry of the set, codes in the entry of a
    parameter, or a category written twice in the map of the card."""
    broken = json.loads(json.dumps(forward_encoding))
    fault(broken)
    with pytest.raises(ValueError, match=phrase):
        validate_encoding(broken)


# the versions of a stage, each of which holds its own record of the codes


def four_versions(stage):
    """Four versions of the forward household stage: two copies of `stage`
    calibrated at β = 0.96 and at β = 0.9, and the occurrences of its text in
    the two periods of a trellis."""
    occurrence = {
        "stage": {"text": HOUSEHOLD_FORWARD, "origin": ORIGIN},
        "calibration": {},
        "settings": {},
        "methods": {},
    }
    trellis = elaborate_trellis(
        {
            "periods": [{"stages": {"H": occurrence}, "connectors": []} for _ in range(2)],
            "inter_connectors": [{"n_next": "n_pre"}],
        }
    )
    # calibrate binds the stage it is called on, so each calibration binds a
    # copy of its own
    calibrated = [
        copy_native(stage).calibrate({"β": 0.96}),
        copy_native(stage).calibrate({"β": 0.9}),
    ]
    return calibrated + [period["stages"]["H"] for period in trellis["periods"]]


def test_two_calibrations_and_two_trellis_occurrences_of_a_stage_hold_four_records_of_its_codes(
    forward_stage,
):
    """Two calibrations of the forward household stage and the occurrences
    of its text in two periods of a trellis hold four distinct records, each
    equal to the map of codes of the household set."""
    held = [
        version.definitions[SET_IDENTITY].categories for version in four_versions(forward_stage)
    ]
    assert held == [records.CategoryCodes(*HOUSEHOLD_CODES)] * 4
    assert len({id(codes) for codes in held}) == 4


def test_a_refused_construction_under_the_same_identifier_leaves_the_records_of_other_versions(
    forward_stage,
):
    """A stage text refused under `category-codes` with the identifier
    `household_status` leaves each of four versions of the forward household
    stage holding its own record of the map of codes, unchanged."""
    versions = four_versions(forward_stage)
    held = [version.definitions[SET_IDENTITY].categories for version in versions]
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            household_with(codes=ANNOTATION.replace("old=1", "old=2"), text=HOUSEHOLD_FORWARD),
            ORIGIN,
        )
    assert refused.value.rule == "category-codes"
    assert all(
        version.definitions[SET_IDENTITY].categories is codes
        for version, codes in zip(versions, held)
    )
    assert held == [records.CategoryCodes(*HOUSEHOLD_CODES)] * 4
