"""The acceptance file of the brief "named integer domains with retained
category meanings" (Bellman-SYM specification 0.5; the second layer of the
tests, `packages/bellman/README.md` §8): one test for each of the brief's
acceptance items 1 to 6, the first five through the public calls of
construction, binding, denotation, export and connection, and the sixth on
the executed notebook. Every stage text is written here, since no corpus
stage is marked.

The rule. A named set written as a comprehension over ℤ or ℕ with integer
bounds and marked `!categories`, with an optional identifier and one
`name=code` entry for each member, is the set I of its members with the
category map m_I: `HouseholdStatus` of `HOUSEHOLD` below is I = {0, 1} with
0 ↦ newborn and 1 ↦ old. The set's `Definition` holds m_I as `categories`,
a `CategoryCodes` of the identifier and the (code, name) pairs in code
order. The set's denotation holds I and m_I as two denoted objects, which
the supporting definitions of the stage and of a builder repeat, and the
stage's encoding and the answer encodings write the codes. A marker in any
other form or on any other item, and a field declared on a coded set at one
site and on another set at another, are refused under `category-codes` at
the item's position; an unmarked set keeps its meaning. A connection copies
values between coded domains when every code written stands for the same
category where it is read. The category named c is (κ, c), κ the identifier
or, without one, the stage text's digest with the set's name.

Not checked here: the documents that item 6 updates at merge; and the corpus
stages' printed snapshot and recorded encodings, which items 2 and 5 require
unchanged except for the grammar's digest, and which `test_snapshot.py` and
`test_snapshot.py` compare.
"""

import json
from typing import NamedTuple

import pytest
from conftest import ROOT, stage_from_text

from bellman.display.encoding_checks import validate_encoding
from bellman.native import records
from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.stage import make_stage
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.syntax.source import to_source
from bellman.trellis import connection_report, elaborate_trellis

ORIGIN = "household_status.bl"
SET = "household_status:set:HouseholdStatus"
# the comprehension and the annotation of the set as the brief's §2 writes
# them, and the map the set's record holds, as `CategoryCodes` arguments
RANGE = "{i : ℤ | i >= 0, i <= 1}"
CODES = "[!categories household_status, newborn=0, old=1]"
HOUSEHOLD_CODES = ("household_status", ((0, "newborn"), (1, "old")))

# The household stage of the brief's §2: `household_status.bl` of the
# example, its three bounded-integer typings replaced by the named set. The
# status at decision, n, is the status at arrival, n_pre; the status next
# period is n_next = 1, old; the value is the payment 100 − 120·n plus the
# discounted continuation value.
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

# the three kinds of pair item 4 reads, in the order `connected` answers them
KINDS = ("authored", "inferred", "inter-period")


def changed(text, *changes):
    """`text` with each `(written, replacement)` pair applied; a written
    fragment the text does not hold exactly once is refused, so that no
    change is lost."""
    for written, replacement in changes:
        assert text.count(written) == 1, written
        text = text.replace(written, replacement)
    return text


def household(codes=CODES, body=RANGE):
    """The household stage with the annotation `codes` and the body `body`
    in place of the set's."""
    return changed(HOUSEHOLD, (CODES, codes), (RANGE, body))


def added(lines, after=CODES):
    """The household stage with `lines` written after the line that ends
    with `after`, the set's line unless another is named."""
    return changed(HOUSEHOLD, (after + "\n", f"{after}\n{lines}\n"))


class Refused(NamedTuple):
    """The refusal of an item 2 case: each of its texts is refused under
    `category-codes` with one message, at the line that holds `at` and at
    `address`, the file position of that line where `address` is None; the
    message holds each of `words`."""

    at: str
    words: tuple
    address: str | None = None


class Kept(NamedTuple):
    """An item 2 text that elaborates: the tags of its set as written, the
    arguments of the set's `CategoryCodes` or None, and the set as its card
    prints it."""

    tags: tuple
    codes: tuple | None
    rule: str


def set_fault(case, *words, **change):
    """An item 2 case of a fault of the marked set: the household stage with
    `change` made by `household`, refused at the set's line with a message
    that names the set and each of `words`."""
    refusal = Refused("HouseholdStatus :=", ("HouseholdStatus", *words))
    return pytest.param((household(**change),), refusal, id=case)


ITEM_2 = [
    # the entries and the marker of the set
    set_fault(
        "a-code-outside-the-range",
        "`old=2`",
        "outside",
        "the member 1 has no category",
        codes=CODES.replace("old=1", "old=2"),
    ),
    set_fault(
        "a-reserved-key",
        "`!categories=household_status`",
        codes=CODES.replace("!categories ", "!categories="),
    ),
    set_fault("a-bare-tag", "`retired`", codes=CODES.replace("]", ", retired]")),
    set_fault("a-single-quoted-entry", "`'retired'`", codes=CODES.replace("]", ", 'retired']")),
    set_fault("minus-0-repeats-0", "`old=-0`", codes=CODES.replace("old=1", "old=-0")),
    set_fault(
        "a-second-marker",
        "`!categories age`",
        codes=CODES.replace(", newborn", ", !categories age, newborn"),
    ),
    set_fault(
        "a-marker-of-two-words",
        "`!categories household status`",
        codes=CODES.replace("household_status", "household status"),
    ),
    set_fault("a-code-that-is-no-integer", "`newborn=zero`", codes=CODES.replace("=0", "=zero")),
    set_fault(
        "a-tab-after-the-marker",
        "U+0009",
        codes=CODES.replace("!categories ", "!categories\t"),
    ),
    # the marker alone lowers to one tag however it is written, so the three
    # are refused alike, for the codes they do not write
    pytest.param(
        tuple(
            household(codes=alone) for alone in ("[!categories]", "!categories", '"!categories"')
        ),
        Refused("HouseholdStatus :=", ("HouseholdStatus", "writes no category")),
        id="the-marker-without-codes-bracketed-bare-or-quoted",
    ),
    # the set the marker stands on
    set_fault("the-natural-numbers-from-0", "ℕ", body="{i : ℕ | i >= 0, i <= 1}"),
    set_fault("a-binder-over-the-reals", "`ℝ`", body="{i : ℝ | i >= 0, i <= 1}"),
    set_fault("one-bound", "upper bound", body="{i : ℤ | i >= 0}"),
    set_fault("an-equality-condition", "`i = 1`", body="{i : ℤ | i >= 0, i = 1}"),
    set_fault("an-empty-range", "leave no integer", body="{i : ℤ | i > 0, i < 1}"),
    set_fault("the-integers", "`ℤ`", body="ℤ"),
    set_fault("an-interval", "`[0, 1]`", body="[0, 1]"),
    set_fault("an-integer-range", "`{0, …, 1}`", body="{0, …, 1}"),
    set_fault("listed-integers", "`{0, 1}`", body="{0, 1}"),
    pytest.param(
        (changed(household(body="{i : ℤ | i >= 0, i <= J}"), ("β : (0,1)", "J : ℕ\nβ : (0,1)")),),
        Refused("HouseholdStatus :=", ("HouseholdStatus", "`i <= J`")),
        id="a-parameter-bound",
    ),
    # a set of names and a restriction of the coded set, each marked beside it
    pytest.param(
        (added(f"Labels := {{newborn, old}} :: {CODES}"),),
        Refused("Labels :=", ("Labels", "`{newborn, old}`")),
        id="a-set-of-names",
    ),
    pytest.param(
        (added("Old := {j : HouseholdStatus | j >= 1} :: [!categories household_status, old=1]"),),
        Refused("Old :=", ("Old", "`HouseholdStatus`")),
        id="a-restricted-coded-set",
    ),
    # the marker on another item, and a coded field's site naming another set
    pytest.param(
        (
            changed(
                HOUSEHOLD, ("n      : HouseholdStatus\n", f"n      : HouseholdStatus :: {CODES}\n")
            ),
        ),
        Refused("n      : HouseholdStatus ::", ("`!categories household_status`",)),
        id="a-marker-on-a-field-declaration",
    ),
    pytest.param(
        (
            added(
                f"𝑝(m : HouseholdStatus) := 100 - 120*m :: {CODES}",
                after="n_next : HouseholdStatus",
            ),
        ),
        Refused("𝑝(m", ("𝑝", "`!categories household_status`")),
        id="a-marker-on-a-function",
    ),
    pytest.param(
        (changed(HOUSEHOLD, (":: [id=ageing]", ":: [id=ageing, !categories household_status]")),),
        Refused("n_next = 1", ("`!categories household_status`",), "dcsn_to_cntn.ageing"),
        id="a-marker-on-a-line",
    ),
    pytest.param(
        (changed(HOUSEHOLD, ("[id=dcsn_to_cntn, (n)", "[id=dcsn_to_cntn, !categories, (n)")),),
        Refused("[id=dcsn_to_cntn", ("`!categories`",), "dcsn_to_cntn"),
        id="a-marker-on-a-block-header",
    ),
    pytest.param(
        (changed(HOUSEHOLD, ("[id=dcsn_to_cntn, (n)", "[id=dcsn_to_cntn, (n : ℤ)")),),
        Refused("[id=dcsn_to_cntn", ("`HouseholdStatus`", "`ℤ`"), "dcsn_to_cntn"),
        id="a-field-site-naming-another-set",
    ),
    # texts that elaborate
    pytest.param(
        (household(codes='["!categories household_status", "newborn=0", "old=1"]', body="ℤ"),),
        Kept(('"!categories household_status"', '"newborn=0"', '"old=1"'), None, "ℤ"),
        id="double-quoted-entries-on-an-unmarked-set",
    ),
    pytest.param(
        (household(codes="[!categories_status]", body="ℤ"),),
        Kept(("!categories_status",), None, "ℤ"),
        id="a-longer-word-than-the-marker",
    ),
    pytest.param(
        (
            changed(
                HOUSEHOLD,
                (" :: " + CODES, ""),
                (RANGE, "{i : ℤ | i >= 0, i <= J}"),
                ("β : (0,1)", "J : ℕ\nβ : (0,1)"),
            ),
        ),
        Kept((), None, "{i ∈ ℤ | i ≥ 0 ∧ i ≤ J}"),
        id="an-unmarked-comprehension-with-a-parameter-bound",
    ),
    pytest.param(
        (household(codes=CODES.replace(", newborn", ', id=status, "the status", newborn')),),
        Kept(
            ("!categories household_status", "id=status", '"the status"', "newborn=0", "old=1"),
            HOUSEHOLD_CODES,
            "{i ∈ ℤ | i ≥ 0 ∧ i ≤ 1}",
        ),
        id="an-id-and-a-description-beside-the-codes",
    ),
    # the bounds −1 and 0, written either way round, strictly and with signs;
    # the transition's 1 lies outside them and stays a recorded condition
    pytest.param(
        (
            household(
                codes="[!categories household_status, newborn=-1, old=0]",
                body="{i : ℤ | -1 <= i, i > -2, i < 1}",
            ),
        ),
        Kept(
            ("!categories household_status", "newborn=-1", "old=0"),
            ("household_status", ((-1, "newborn"), (0, "old"))),
            "{i ∈ ℤ | −1 ≤ i ∧ i > −2 ∧ i < 1}",
        ),
        id="bounds-written-either-way-strict-or-negative",
    ),
]


def connected(writer, reader):
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


def test_item_1_the_household_stage_elaborates_and_its_denotations_hold_the_set_and_its_map():
    """The household stage, with the displayed domain, `n_next = 1` and
    `V = 100 − 120·n + β·V≻`, elaborates. The set's record holds the map
    0 ↦ newborn, 1 ↦ old under the identifier `household_status` and keeps
    the annotation as written. The set's denotation holds two objects, the
    set I as written and the map m_I, printed as `0 ↦ newborn, 1 ↦ old
    (categories household_status)`; the supporting definitions of the stage
    and of the builder from dcsn to cntn hold the same two. The domain of
    each state field is the named set."""
    stage = stage_from_text(HOUSEHOLD, ORIGIN)
    record = stage.definitions[SET]
    assert record.categories == records.CategoryCodes(*HOUSEHOLD_CODES)
    assert record.tags == ("!categories household_status", "newborn=0", "old=1")
    denoted = stage.definitions.denote(SET).denoted
    assert [(d.symbol, d.expression) for d in denoted] == [
        ("HouseholdStatus", record.equations[0]),
        ("HouseholdStatus", record.categories),
    ]
    assert [d.rule for d in denoted] == [
        "{i ∈ ℤ | i ≥ 0 ∧ i ≤ 1}",
        "0 ↦ newborn, 1 ↦ old (categories household_status)",
    ]
    for answer in (stage.denote(), stage.builder["dcsn", "cntn"].denote()):
        assert [d for d in answer.definitions if d.identity == SET] == list(denoted)
    domains = {
        str(identity): to_source(sort.domain)
        for identity, sort in stage.fields().items()
        if sort.role == "state"
    }
    assert domains == dict.fromkeys(
        ("household_status:arvl:n_pre", "household_status:dcsn:n", "household_status:cntn:n_next"),
        "HouseholdStatus",
    )


@pytest.mark.parametrize("texts, expected", ITEM_2)
def test_item_2_category_codes_refuses_each_invalid_form_and_unmarked_sets_keep_their_meaning(
    texts, expected
):
    """Each text of a `Refused` case is refused under `category-codes` at
    the position of the item that writes the fault, a fault of the marked
    set at the set's file position: a code outside the range together with
    the member it leaves without a category; a reserved key; a bare tag,
    single-quoted or not; `-0` repeating `0`; a second marker and a marker
    of two words; a code that is no integer; the marker without codes,
    bracketed, bare or quoted, refused alike; the ℕ bound, a binder over ℝ,
    one bound, an empty range and a parameter bound; ℤ, an interval,
    `{0, …, 1}`, `{0, 1}`, a set of names and a restriction of the coded
    set; the marker on a field declaration, a function, a line and a block
    header; and a site of a coded field naming another set. Each `Kept` text
    elaborates, its set's record holding the tags as written and the codes
    or None, its denotation the set alone or the set and the codes:
    double-quoted entries on an unmarked set and a longer word than the
    marker mark nothing; an unmarked comprehension with a parameter bound
    keeps its meaning; an `id=` entry and a description stand beside the
    codes; and bounds written either way round, strict or negative, give the
    range they bound."""
    if isinstance(expected, Kept):
        (text,) = texts
        stage = stage_from_text(text, ORIGIN)
        record = stage.definitions[SET]
        assert record.tags == expected.tags
        codes = None if expected.codes is None else records.CategoryCodes(*expected.codes)
        assert record.categories == codes
        denoted = stage.definitions.denote(SET).denoted
        assert [d.expression for d in denoted] == [record.equations[0]] + (
            [] if codes is None else [codes]
        )
        assert denoted[0].rule == expected.rule
        return
    refusals = []
    for text in texts:
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(text, ORIGIN)
        refusals.append(refused.value)
    line = texts[0][: texts[0].index(expected.at)].count("\n") + 1
    address = expected.address or f"{ORIGIN}:{line}"
    message = refusals[0].message
    for error in refusals:
        assert (error.rule, error.address, error.line, error.message) == (
            "category-codes",
            address,
            line,
            message,
        )
    for word in expected.words:
        assert word in message, (word, message)


def test_item_3_kernels_read_through_the_denoted_map_keep_their_outcomes_under_a_full_recoding():
    """After `calibrate({"β": 0.96})`, the compiled law of motion gives the
    next status 1 at the codes 0 and 1, and the compiled aggregation of the
    value line at V≻ = 0 gives the payment 100 at 0 and −20 at 1. Read
    through the map the stage's denotation holds for the set that the
    kernels' argument n and the next status lie in, the newborn household
    and the old one both become old and are paid 100 and −20. The stage with
    its codes, its transition and its payment swapped together, `old=0,
    newborn=1`, `n_next = 0` and `V = −20 + 120·n + β·V≻`, has the same
    outcomes; the stage with its codes alone swapped has others."""

    def categories(stage, domain):
        """The category of each code of the named set `domain`: the map the
        set's denotation holds as its second object."""
        _, coded = stage.definitions.denote(f"household_status:set:{domain.name}").denoted
        return dict(coded.expression.codes)

    def outcomes(text):
        """The kernels' numbers at each code, and each category's next
        category and payment."""
        stage = stage_from_text(text, ORIGIN).calibrate({"β": 0.96})
        law = stage.builder.fwd["dcsn_to_cntn"].primitives["Pushforward"]
        value = stage.builder.bwd["cntn_to_dcsn"].primitives["Aggregation"]
        # the law reads n, the aggregation V≻ and then n, in the same set
        (status,) = law.kernel().arguments
        assert status[0] == "n" and value.kernel().arguments[1] == status
        now = categories(stage, status[1])
        then = categories(stage, stage.fields()["household_status:cntn:n_next"].domain)
        g, G = law.compile_kernel(), value.compile_kernel()
        laws, values = law.kernel().parameter_values, value.kernel().parameter_values
        numbers = {code: (int(g(code, *laws)), float(G(0.0, code, *values))) for code in now}
        return numbers, {now[code]: (then[after], paid) for code, (after, paid) in numbers.items()}

    numbers, decoded = outcomes(HOUSEHOLD)
    assert numbers == {0: (1, 100.0), 1: (1, -20.0)}
    assert decoded == {"newborn": ("old", 100.0), "old": ("old", -20.0)}
    swapped_codes = "[!categories household_status, old=0, newborn=1]"
    swapped = changed(
        household(codes=swapped_codes),
        ("n_next = 1 ", "n_next = 0 "),
        ("V = 100 - 120*n", "V = -20 + 120*n"),
    )
    assert outcomes(swapped)[1] == decoded
    relabelled = household(codes=swapped_codes)
    assert outcomes(relabelled)[1] == {"old": ("newborn", 100.0), "newborn": ("newborn", -20.0)}


def test_item_4_authored_inferred_and_inter_period_pairs_join_coded_domains_whose_maps_agree():
    """Through an authored, an inferred and an inter-period pair alike: two
    domains of integers without codes are compatible, as before; one
    identifier with agreeing maps is compatible, the entries reversed
    included; another identifier, opposite codes, and a coded domain against
    an uncoded one either way are incompatible; the restriction of the coded
    set to old is compatible into the set, and the set is not compatible
    into it; a product whose coded factor agrees is compatible, and one
    whose coded factor has opposite codes is not; a reading restriction
    whose condition names a parameter is not established, and so is a
    writing one into the opposite codes, since it may be empty; a
    restriction by an equality, `j = 1`, is the restriction to old, and a
    restriction by a literal bound and a parameter has the codes within the
    literal bound; two texts
    with equal maps and no identifier are incompatible; and a recoding
    stage, `n_next = 1 − n` from the codes into the opposite codes, is
    compatible on both sides, where the direct pair into the opposite codes
    is not. One restriction by the parameter k on both sides is one set
    within a period and not established between periods, where k names two
    parameters, or under two identifiers; a restriction whose condition
    calls a function is not established on both sides, since the names
    alone do not fix its members. One text without an identifier joined to
    its next-period occurrence is compatible, and a stage made from a term,
    which holds no text digest, is not established against itself; the
    reason of an incompatible pair names both maps."""

    def statuses(writer, reader):
        return {kind: status for kind, (status, _) in connected(writer, reader).items()}

    opposite = "[!categories household_status, newborn=1, old=0]"
    opposite_codes = household(codes=opposite)
    entries_reversed = household(codes="[!categories household_status, old=1, newborn=0]")
    another_identifier = household(codes=CODES.replace("household_status", "age_group"))
    uncoded = changed(HOUSEHOLD, (" :: " + CODES, ""))
    old = added("Old := {j : HouseholdStatus | j >= 1}")
    old_written = changed(old, ("n_next : HouseholdStatus", "n_next : Old"))
    old_read = changed(old, ("n_pre  : HouseholdStatus", "n_pre  : Old"))
    fields = "n_pre  : HouseholdStatus\nn      : HouseholdStatus\nn_next : HouseholdStatus\n"
    product = changed(
        HOUSEHOLD,
        (fields, fields.replace("HouseholdStatus\n", "HouseholdStatus × ℝ₊\n")),
        ("n_next = 1 ", "n_next = n "),
        ("100 - 120*n + β*V[>]", "β*V[>]"),
    )
    product_opposite = changed(product, (CODES, opposite))
    eligible = changed(
        added("k : ℤ\nEligible := {j : HouseholdStatus | j >= k}"),
        ("n_pre  : HouseholdStatus", "n_pre  : Eligible"),
    )
    eligible_written = changed(eligible, ("n_next : HouseholdStatus", "n_next : Eligible"))
    eligible_elsewhere = changed(
        eligible_written, (CODES, CODES.replace("household_status", "age_group"))
    )
    one = added("One := {j : HouseholdStatus | j = 1}")
    one_written = changed(one, ("n_next : HouseholdStatus", "n_next : One"))
    one_read = changed(one, ("n_pre  : HouseholdStatus", "n_pre  : One"))
    bounded = changed(
        added("k : ℤ\nBounded := {j : HouseholdStatus | j >= 1, j <= k}"),
        ("n_next : HouseholdStatus", "n_next : Bounded"),
    )
    called = changed(
        added("k : ℤ\n𝑓(x : ℤ) := x + k\nCalled := {j : HouseholdStatus | j >= 𝑓(0)}"),
        ("n_pre  : HouseholdStatus", "n_pre  : Called"),
        ("n_next : HouseholdStatus", "n_next : Called"),
    )
    local = household(codes="[!categories, newborn=0, old=1]")
    local_elsewhere = changed(local, ("discount", "the discount"))
    recoding = changed(
        added(f"Recoded := {RANGE} :: {opposite}"),
        ("n_next : HouseholdStatus", "n_next : Recoded"),
        ("n_next = 1 ", "n_next = 1 - n "),
    )
    integers = changed(HOUSEHOLD, (f"{RANGE} :: {CODES}", "ℤ"))
    assert statuses(integers, integers) == dict.fromkeys(KINDS, "compatible")
    for case, writer, reader, status in (
        ("one identifier", HOUSEHOLD, HOUSEHOLD, "compatible"),
        ("entries reversed", HOUSEHOLD, entries_reversed, "compatible"),
        ("another identifier", HOUSEHOLD, another_identifier, "incompatible"),
        ("opposite codes", HOUSEHOLD, opposite_codes, "incompatible"),
        ("coded into uncoded", HOUSEHOLD, uncoded, "incompatible"),
        ("uncoded into coded", uncoded, HOUSEHOLD, "incompatible"),
        ("restriction into the set", old_written, HOUSEHOLD, "compatible"),
        ("set into the restriction", HOUSEHOLD, old_read, "incompatible"),
        ("agreeing products", product, product, "compatible"),
        ("a conflicting product factor", product, product_opposite, "incompatible"),
        ("a restriction by a parameter", HOUSEHOLD, eligible, "not-established"),
        ("a restriction that may be empty", eligible_written, opposite_codes, "not-established"),
        ("an equality into the set", one_written, HOUSEHOLD, "compatible"),
        ("the set into an equality", HOUSEHOLD, one_read, "incompatible"),
        ("a literal bound beside a parameter", bounded, old_read, "compatible"),
        (
            "one restriction under two identifiers",
            eligible_written,
            eligible_elsewhere,
            "not-established",
        ),
        ("a condition that calls a function", called, called, "not-established"),
        ("two texts without an identifier", local, local_elsewhere, "incompatible"),
        ("into the recoding stage", HOUSEHOLD, recoding, "compatible"),
        ("out of the recoding stage", recoding, opposite_codes, "compatible"),
    ):
        assert statuses(writer, reader) == dict.fromkeys(KINDS, status), case
    assert statuses(eligible_written, eligible_written) == {
        "authored": "compatible",
        "inferred": "compatible",
        "inter-period": "not-established",
    }
    assert connected(local, local)["inter-period"][0] == "compatible"
    without_text = make_stage(*parse_with_spans(local, ORIGIN))
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
    _, reason = connected(HOUSEHOLD, opposite_codes)["authored"]
    assert "0 ↦ newborn, 1 ↦ old" in reason and "0 ↦ old, 1 ↦ newborn" in reason, reason


def test_item_5_the_assignment_round_trips_its_codes_are_exported_and_each_version_holds_them():
    """The new assignment prints to source as the brief writes it, without
    its annotation, and the printed text parses to an equal core; the
    annotated AST of the stage round-trips through `to_json` and
    `from_json`. The stage's encoding passes the package's encoding checks;
    its stored entry of the set, and no other, writes `categories`, and the
    encoded answer of the set's card writes the codes as its second denoted
    object. The checks refuse a stored map whose codes decrease, a map on a
    parameter's entry and an answer node whose names repeat. Two
    calibrations and two trellis occurrences of the text hold four distinct
    records equal to the map, which a refused construction under the same
    identifier leaves as they were."""
    term, _ = parse_with_spans(HOUSEHOLD, ORIGIN)
    statement = term.items[2]  # the item after `@stage` and the declaration of β
    printed = to_source(statement.core)
    assert printed == "HouseholdStatus := {i : ℤ | i >= 0, i <= 1}"
    reparsed = parse_with_spans("@stage: x\n" + printed + "\n").term.items[1]
    assert to_json(reparsed.core) == to_json(statement.core)
    assert from_json(json.loads(json.dumps(to_json(term)))) == term

    stage = stage_from_text(HOUSEHOLD, ORIGIN)
    encoding = validate_encoding(json.loads(json.dumps(stage.encoding())))
    written = {"identifier": "household_status", "codes": [[0, "newborn"], [1, "old"]]}
    stored = {entry["identity"]: entry for entry in encoding["definitions"]}
    assert [identity for identity, entry in stored.items() if "categories" in entry] == [SET]
    assert stored[SET]["categories"] == written
    card = encoding["derived"]["definitions"][list(stored).index(SET)]
    denoted = [item["fields"]["expression"] for item in card["value"]["fields"]["denoted"]]
    assert [expression["node"] for expression in denoted] == [
        "terms.Comprehension",
        "records.CategoryCodes",
    ]
    assert denoted[1]["fields"] == written
    # a stored map whose codes decrease, a map on the entry of the parameter
    # β, and an encoded map whose names repeat are refused
    order = list(stored)
    for fault in ("decreasing", "on a parameter", "repeated names"):
        broken = json.loads(json.dumps(encoding))
        entries = broken["definitions"]
        node = broken["derived"]["definitions"][order.index(SET)]["value"]["fields"]
        if fault == "decreasing":
            entries[order.index(SET)]["categories"]["codes"].reverse()
        elif fault == "on a parameter":
            entries[order.index("household_status:parameter:β")]["categories"] = written
        else:
            node["denoted"][1]["fields"]["expression"]["fields"]["codes"][1][1] = "newborn"
        words = {
            "decreasing": "increase strictly",
            "on a parameter": "writes no category map",
            "repeated names": "names must be distinct",
        }[fault]
        with pytest.raises(ValueError, match=words):
            validate_encoding(broken)

    occurrence = {
        "stage": {"text": HOUSEHOLD, "origin": ORIGIN},
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
    # each calibration binds a stage of its own (specification 0.6
    # decision 1 and R4)
    versions = [
        copy_native(stage).calibrate({"β": 0.96}),
        copy_native(stage).calibrate({"β": 0.9}),
    ] + [period["stages"]["H"] for period in trellis["periods"]]
    held = [version.definitions[SET].categories for version in versions]
    assert held == [records.CategoryCodes(*HOUSEHOLD_CODES)] * 4
    assert len({id(codes) for codes in held}) == 4
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(household(codes=CODES.replace("old=1", "old=2")), ORIGIN)
    assert refused.value.rule == "category-codes"
    assert all(
        version.definitions[SET].categories is codes for version, codes in zip(versions, held)
    )
    assert held == [records.CategoryCodes(*HOUSEHOLD_CODES)] * 4


def test_item_6_the_notebook_is_executed_and_keeps_its_two_reserved_cells():
    """The notebook of the brief stands in the verification folder of the
    internal records, executed: every code cell ran; an error output stands
    only in a cell tagged `raises-exception`, one per such cell; no output
    prints `False`, so every comparison of the notebook held when it was
    executed; and the last four cells are the reserved `### Observation` and
    `### Decision` cells, which record no personal acceptance. The notebook
    is found by its folder name, since no file outside the internal folder
    names a path under it; the test is skipped in a checkout without that
    folder."""
    found = sorted(
        ROOT.glob(
            "*/operations/verification/*/spec_0.5/2026-10-20-category-codes/category-codes.ipynb"
        )
    )
    if not found:
        pytest.skip("the notebook's folder is not in this checkout")
    (path,) = found
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    code = [cell for cell in cells if cell["cell_type"] == "code"]
    assert code and all(cell["execution_count"] for cell in code)
    refused = [cell for cell in code if "raises-exception" in cell["metadata"].get("tags", [])]
    assert len(refused) == 11
    for cell in code:
        errors = [output for output in cell["outputs"] if output["output_type"] == "error"]
        assert len(errors) == (1 if cell in refused else 0), "".join(cell["source"])
        for output in cell["outputs"]:
            shown = "".join(output.get("text", "")) + "".join(
                output.get("data", {}).get("text/plain", "")
            )
            assert "False" not in shown, "".join(cell["source"])
    assert [cell["cell_type"] for cell in cells[-4:]] == ["markdown"] * 4
    assert "".join(cells[-4]["source"]).strip() == "### Observation"
    assert "".join(cells[-2]["source"]).strip() == "### Decision"
