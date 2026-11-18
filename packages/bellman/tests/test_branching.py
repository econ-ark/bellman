"""Branching stages and branches that a shock selects: their kinds, laws of
motion, sections, kernels and cards, the conservation of mass, and the
refusals of malformed branches."""

from pathlib import Path

import numpy
import pytest
from application_files import BRANCHING_EXAMPLES_FOLDER, COPIED_FILES_FOLDER, ROOT
from printed_text import (
    COMPARED_CARD_SECTIONS,
    card_section_lines,
    card_shown_on_the_page,
    differing_card_sections,
    flat,
    operation_rules,
    operations_entries,
    parse_card,
    parse_every_sheet,
)
from stage_builders import corpus_stage, stage_from_text
from stage_texts import branching_text, changed

from bellman.native.identity import Identity
from bellman.refusal_examples import SHOCK_BRANCHING
from bellman.refusals import ConstructionError, NotConstructed
from bellman.stage import branches, elaborate_stage, load_stage, to_source
from bellman.stage.stage_answers import combination, kind

TENURE_EXAMPLE = BRANCHING_EXAMPLES_FOLDER / "example-tenure.md"


# the example page of the model of Cagetti and De Nardi (2006), which this file
# calls the Cagetti–De Nardi model afterwards
CAGETTI_DE_NARDI_EXAMPLE = BRANCHING_EXAMPLES_FOLDER / "examples/cagetti-denardi-2006/expected.md"


def cells(lines):
    """The rows of the entries of an `Operations` section, each entry's number
    and key and its `in:` and `out:` lines above its short line, flattened;
    `lines` is the section as `card_section_lines` gives it, its heading first.
    """
    kept, row = [], True
    for line in lines[1:]:
        body = line.strip()
        if not body:
            row = True
        elif set(body) == {"─"}:
            row = False
        elif row:
            kept.append(body)
    return flat("\n".join(kept))


# the two cards of tenure whose rows carry a strict mark of expected failure,
# as the example page draws them: the title, the keys of the operations, and
# the maps and composites that the `out:` of an entry prints
CARDS = {
    ("backward", "cntn_to_dcsn"): (
        "STAGE tenure / BACKWARD BUILDER cntn_to_dcsn",
        ["Pullback:keep", "Pullback:adjust", "Aggregation", "Evaluation"],
        ["𝑉_kp≻ ∘ 𝑔_keep≻", "𝑉_adj≻ ∘ 𝑔_adjust≻"],
    ),
    ("backward", "policy"): (
        "STAGE tenure / POLICY BUILDER policy",
        ["Pullback:keep", "Pullback:adjust", "choice:Aggregation", "choice:Argmax", "Evaluation"],
        [
            "(a_d, h_d, z_d, d) ↦ (𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d)), "
            "𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[d]"
        ],
    ),
}


class DrawnCards(dict):
    """The cards of `CARDS` as the example page of tenure draws them, each
    read from the page when a test first asks for it."""

    def __missing__(self, key):
        self[key] = card_shown_on_the_page(TENURE_EXAMPLE, CARDS[key][0])
        return self[key]


DRAWN = DrawnCards()


CARDS_KNOWN_FAILURES = {
    ("backward", "cntn_to_dcsn"): pytest.mark.xfail(
        strict=True,
        reason="The test expects the printed card of the decision builder `cntn_to_dcsn` of "
        "`tenure` to state what the example page draws. The page was written for an earlier "
        "`tenure.bl`, which stated the derivatives 𝑑𝑉 in this block: its signature lists those "
        "derivatives and neither the ages `age_kp[>]` and `age_adj[>]` that the builder now "
        "takes in nor the age `age` that it now writes, its sections `Where`, `Operations`, "
        "`Conditions`, `Source` and `Definitions referenced` were written before the law read "
        "those ages, and its sections `Operations`, `Conditions` and `Source` also state the "
        "derivative lines. Today `tenure.bl` states the value and the age alone, and the "
        "derivative lines of the builder stand in its methods file, which the symbolic stage "
        "of the fixture `tenure` does not read.",
    ),
    ("backward", "policy"): pytest.mark.xfail(
        strict=True,
        reason="The test expects the printed card of the policy builder of `tenure` to state "
        "what the example page draws. The page was written for an earlier `tenure.bl`: its "
        "signature does not list the ages `age_kp[>]` and `age_adj[>]` that the builder now "
        "takes in, its sections `Where`, `Operations` and `Definitions referenced` were written "
        "before the law read those ages, and its section `Source` cites the line "
        "`d = argmax_{d}(V_kp[>], V_adj[>])` at another number than the line at which "
        "`tenure.bl` writes it today.",
    ),
}


# the five stages of the Cagetti–De Nardi model and of the childbearing model
# of de la Croix and Pommeret (2021) whose branches a shock selects: the fields
# that the nested block of each branch writes, and the tuple of the sections of
# the law of motion indexed by the shock s
BRANCHES_OF_DRAWS = {
    "retiree_death": (
        {"survive": ("a_rd_rt",), "die": ("a_rd_yc", "y_rd_yc", "θ_rd_yc")},
        "(a,y,θ,s)↦(a,(a,y,θ))[s]",
    ),
    "worker_ageing": (
        {"young": ("a_wa_yc", "y_wa_yc", "θ_wa_yc"), "old": ("a_wa_rt",)},
        "(a,y,θ,s)↦((a,y,θ),a)[s]",
    ),
    "entrepreneur_death": (
        {"survive": ("a_ed_oc", "θ_ed_oc"), "die": ("a_ed_yc", "y_ed_yc", "θ_ed_yc")},
        "(a,y,θ,s)↦((a,θ),(a,y,θ))[s]",
    ),
    "entrepreneur_ageing": (
        {"young": ("a_ea_yc", "y_ea_yc", "θ_ea_yc"), "old": ("a_ea_oc", "θ_ea_oc")},
        "(a,y,θ,s)↦((a,y,θ),(a,θ))[s]",
    ),
    "fecundity": (
        {"mother": ("a_mth",), "childless": ("a_chl",)},
        "(a_fecd,age_fecd,s)↦(a_fecd,a_fecd)[s]",
    ),
}


# the values of β, η and π_o of the derivation by hand on the example page of
# the Cagetti–De Nardi model; the five other parameters take values in their
# declared sets, which no line of the decision builder reads
DERIVATION_VALUES = {
    "β": 0.95,
    "η": 0.5,
    "π_o": 0.9,
    "P_y": 0.5,
    "y_grid": 1.0,
    "ρ_θ0": 0.9,
    "ρ_θ1": 0.8,
    "θ_e": 1.0,
}


DOBRESCU = f"{COPIED_FILES_FOLDER}/dobrescu-etal-2018/"


CAGETTI_DE_NARDI_STAGES = "applications/cagetti-denardi-2006/declaration/stages/"


# the stage files that the package refuses when it elaborates them: the path,
# the rule, the address and the phrases of the refusal
REFUSED = [
    (DOBRESCU + name, "branch-tuple-mismatch", "cntn_to_dcsn.value", ("policy.choice", "no tuple"))
    for name in ("plan_choice.bl", "contrib.bl", "invest.bl")
] + [
    (
        CAGETTI_DE_NARDI_STAGES + name,
        "not-constructed",
        "dcsn_to_cntn",
        ("beside its branches", "one control"),
    )
    for name in (
        "young_entrepreneur/young_entrepreneur.bl",
        "old_entrepreneur/old_entrepreneur.bl",
    )
]


# the forms that a branching block may not take, each a change of the
# package's example of a branching block: the case, the changes, the rule,
# the address (None where the parse refuses and names the address in the
# message) and the phrases of the refusal
BRANCHING_REFUSALS = [
    (
        "fewer than two labels",
        (("d : !ctrl @ {work, retire}", "d : !ctrl @ {work}"),),
        "branch-labels",
        "dcsn_to_cntn",
        ("'d'", "1 label"),
    ),
    (
        "a label written twice",
        (("[label=retire,", "[label=work,"),),
        "syntax",
        None,
        ("dcsn_to_cntn.work",),
    ),
    (
        "the branches in another order than the set",
        (("d : !ctrl @ {work, retire}", "d : !ctrl @ {retire, work}"),),
        "branch-labels",
        "dcsn_to_cntn",
        ("{retire, work}", "order"),
    ),
    (
        "a field written by two branches",
        (
            (
                "[label=retire, () -> (a_r : ℝ₊) : !cntn]",
                "[label=retire, () -> (a_w : ℝ₊) : !cntn]",
            ),
            ("a_r = a_d", "a_w = a_d"),
        ),
        "declared-once",
        "dcsn_to_cntn.retire",
        ("'a_w'", "'work'", "'retire'"),
    ),
    (
        "a nested block without a label",
        (("[label=retire, ", "[name=retire, "),),
        "branch-form",
        "dcsn_to_cntn.2",
        ("label=",),
    ),
    (
        "a line beside the nested blocks",
        (("    [label=work,", "    a_x = a_d\n    [label=work,"),),
        "branch-form",
        "dcsn_to_cntn.1",
        ("beside",),
    ),
    (
        "a nested block outside the forward block from the decision perch",
        (
            (
                "    V = (V_w[>], V_r[>])[d]",
                "    [label=work, () -> (x : ℝ) : !cntn] {\n        x = 1\n    }\n"
                "    V = (V_w[>], V_r[>])[d]",
            ),
        ),
        "branch-form",
        "cntn_to_dcsn.work",
        ("decision perch",),
    ),
    (
        "a value line with no tuple indexed by the label coordinate",
        (("V = (V_w[>], V_r[>])[d]", "V = V_w[>]"),),
        "branch-tuple-mismatch",
        "cntn_to_dcsn.choice_value",
        ("policy.choice", "no tuple"),
    ),
    (
        "a value read at two positions",
        (
            ("V = (V_w[>], V_r[>])[d]", "V = (V_w[>], V_w[>] + V_r[>])[d]"),
            ("argmax_{d}(V_w[>], V_r[>])", "argmax_{d}(V_w[>], V_w[>] + V_r[>])"),
        ),
        "branch-value-position",
        "cntn_to_dcsn.choice_value",
        ("V_w[>]", "'work'", "'retire'"),
    ),
]


POLICY = (
    "[id=policy, (V_y[>], V_o[>]) : !cntn -> (c : ℝ₊ @ !ctrl) : !dcsn] {\n"
    "    c = argmax_{c}(E_{s}((V_y[>], V_o[>])[s]))  :: [id=choice]\n}\n"
)


# the forms that a branch a shock selects may not take, each a change of the
# package's example of a draw: the case, the changes, the rule, the address
# and the phrases of the refusal; a top-level item is addressed by its
# position among the top-level items of the file, so the law at line 4 is the
# address `4`, as the catalogue's example of `distribution-edge` is `3`, and
# the position in the file stands in the message
SHOCK_REFUSALS = [
    (
        "the label shock not listed",
        (("(a_d, s) : !dcsn -> ()", "(a_d) : !dcsn -> ()"),),
        "branch-labels",
        "dcsn_to_cntn",
        ("neither a control nor a shock",),
    ),
    (
        "the label declared with no law and no role",
        (("s ~ Categorical((π, 1 - π))\n", ""),),
        "branch-labels",
        "dcsn_to_cntn",
        ("neither a control nor a shock", "s ~ Categorical"),
    ),
    (
        "the labels in another order than the branches",
        (("s : {young, old}", "s : {old, young}"),),
        "branch-labels",
        "dcsn_to_cntn",
        ("{old, young}", "order"),
    ),
    (
        "a label shock without a law",
        (("s : {young, old}\ns ~ Categorical((π, 1 - π))\n", "s : {young, old} @ !shck\n"),),
        "branch-law",
        "dcsn_to_cntn",
        ("'s'", "has no distribution", "Categorical((p_young, p_old))"),
    ),
    (
        "three weights for two labels",
        (("Categorical((π, 1 - π))", "Categorical((π, 1 - π, 0))"),),
        "branch-law",
        "4",
        ("3 probabilities", "2 labels", "t.bl:4"),
    ),
    (
        "a law that gives the labels no weights",
        (("Categorical((π, 1 - π))", "N(0, 1)"),),
        "branch-law",
        "4",
        ("N(0, 1)", "no probability for each label", "Bernoulli(p)"),
    ),
    (
        "numeric weights that do not sum to one",
        (("(π, 1 - π)", "(0.3, 0.6)"),),
        "distribution-domain",
        "t.bl:4",
        ("0.3, 0.6", "not to one"),
    ),
    (
        "a selection by the shock outside its expectation",
        (("E_{s}((V_y[>], V_o[>])[s])", "(V_y[>], V_o[>])[s]"),),
        "branch-tuple-mismatch",
        "cntn_to_dcsn.value",
        ("outside an expectation over it alone",),
    ),
    (
        "an expectation over the shock of no tuple",
        (("E_{s}((V_y[>], V_o[>])[s])", "E_{s}(V_y[>] + V_o[>])"),),
        "branch-tuple-mismatch",
        "cntn_to_dcsn.value",
        ("of no tuple indexed by it",),
    ),
    (
        "three entries for two labels",
        (("E_{s}((V_y[>], V_o[>])[s])", "E_{s}((V_y[>], V_o[>], V_o[>])[s])"),),
        "branch-tuple-mismatch",
        "cntn_to_dcsn.value",
        ("3 entries", "{young, old}"),
    ),
    (
        "a branch value read at two positions",
        (("E_{s}((V_y[>], V_o[>])[s])", "E_{s}((V_y[>], V_y[>] + V_o[>])[s])"),),
        "branch-value-position",
        "cntn_to_dcsn.value",
        ("V_y[>]", "'young'", "'old'"),
    ),
    (
        "a control listed beside the drawn label",
        (("(a_d, s) : !dcsn -> ()", "(a_d, c : !ctrl @ ℝ₊, s) : !dcsn -> ()"),),
        "not-constructed",
        "dcsn_to_cntn",
        ("the shock 's' selects", "chooses 'c'"),
    ),
    (
        "a policy block beside the draw",
        (("[id=dcsn_to_arvl", POLICY + "[id=dcsn_to_arvl"),),
        "not-constructed",
        "dcsn_to_cntn",
        ("the shock 's' selects", "chooses 'c'"),
    ),
]


def inputs_listed(handle):
    """The names of the inputs that the signature of a block lists."""
    return [
        line.split()[1] for line in str(handle.signature()).splitlines() if line.startswith("in")
    ]


def mass_conservation(stage):
    """The obligations of `stage` under the condition mass-conservation, that
    the masses of the branch measures add up to the mass at the decision
    perch."""
    return [item for item in stage.obligations() if item.condition == "mass-conservation"]


@pytest.fixture(scope="module")
def cagetti_de_nardi_example():
    """The lines of the example page of the Cagetti–De Nardi model."""
    return CAGETTI_DE_NARDI_EXAMPLE.read_text(encoding="utf-8").splitlines()


@pytest.fixture(scope="module")
def example_draw():
    """The stage of the package's example of a branch that a shock selects:
    the shock s takes the labels young and old with the weights π and 1 − π."""
    return stage_from_text(SHOCK_BRANCHING)


@pytest.fixture(scope="module")
def bernoulli_draw():
    """The package's example of a draw with the law Bernoulli(π) in place of
    Categorical((π, 1 - π))."""
    return stage_from_text(changed(SHOCK_BRANCHING, ("Categorical((π, 1 - π))", "Bernoulli(π)")))


@pytest.fixture(scope="module")
def calibrated_draw_aggregation():
    """The aggregation of the decision builder of the package's example of a
    draw, on a stage of its own calibrated at π = 0.25."""
    stage = stage_from_text(SHOCK_BRANCHING).calibrate({"π": 0.25})
    return stage.builder.bwd["cntn_to_dcsn"].primitives["Aggregation"]


@pytest.fixture(scope="module")
def branching_example():
    """The stage of the package's example of a branching block, in which each
    branch line writes into the set of its field."""
    return stage_from_text(branching_text())


@pytest.fixture(scope="module")
def branching_with_a_line_outside_its_set():
    """The package's example of a branching block whose line of the branch
    work writes a_d − 1, which can lie outside the set ℝ₊ of its field."""
    return stage_from_text(branching_text(("a_w = a_d ", "a_w = a_d - 1 ")))


@pytest.fixture(scope="module")
def branching_with_one_id_twice():
    """The package's example of a branching block in which the line of each
    branch carries the one id assets."""
    return stage_from_text(
        branching_text(("[id=working]", "[id=assets]"), ("[id=retiring]", "[id=assets]"))
    )


@pytest.mark.parametrize(
    "name",
    ["tenure", "ret_choice", *BRANCHES_OF_DRAWS],
)
def test_a_stage_with_branches_is_of_the_kind_branching(name, request):
    """kind answers branching for a stage whose forward block splits into
    branches."""
    assert kind(request.getfixturevalue(name)) == "branching"


@pytest.mark.parametrize(
    ("name", "held"),
    [
        pytest.param(
            "tenure", {"keep": ("w_kp", "h_kp", "z_kp"), "adjust": ("w_adj", "z_adj")}, id="tenure"
        ),
        pytest.param("ret_choice", {"work": ("a_w",), "retire": ("a_r",)}, id="ret_choice"),
        *[pytest.param(name, held, id=name) for name, (held, _) in BRANCHES_OF_DRAWS.items()],
    ],
)
def test_branches_answers_the_fields_that_each_branch_writes(name, held, request):
    """branches answers each label of a stage with the continuation fields that
    the nested block of the label writes."""
    found = branches(request.getfixturevalue(name))
    assert {
        label: tuple(identity.field for identity in written) for label, written in found.items()
    } == held


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("tenure", "choice", id="tenure, whose label is a control"),
        *[pytest.param(name, "expectation", id=name) for name in BRANCHES_OF_DRAWS],
        pytest.param("cons", None, id="cons, a stage without branches"),
    ],
)
def test_combination_answers_how_the_branches_of_a_stage_combine(name, expected, request):
    """combination answers choice where a control selects the branch,
    expectation where a shock selects it, and None for a stage without
    branches."""
    assert combination(request.getfixturevalue(name)) == expected


def test_the_law_of_motion_of_tenure_is_defined_on_the_label_by_the_lines_of_both_branches(tenure):
    """The definition of the law of motion of tenure takes the decision states,
    the incoming age of each branch and then the label coordinate d, and its
    equations are the lines of the branches keep and adjust in order."""
    law = tenure.definitions["tenure:g:dcsn_to_cntn"]
    assert [name for name, _ in law.coordinates] == ["a_d", "h_d", "z_d", "age_kp", "age_adj", "d"]
    assert [str(line) for line in law.equations] == [
        "dcsn_to_cntn.keep.cash_on_hand",
        "dcsn_to_cntn.keep.housing_kept",
        "dcsn_to_cntn.keep.3",
        "dcsn_to_cntn.adjust.total_wealth",
        "dcsn_to_cntn.adjust.2",
    ]


@pytest.mark.parametrize("name", list(BRANCHES_OF_DRAWS))
def test_the_label_shock_is_the_last_coordinate_of_the_law_of_motion_of_a_draw(name, request):
    """The shock s that selects the branch is the last argument of the law of
    motion of a draw."""
    record = request.getfixturevalue(name).definitions[f"{name}:g:dcsn_to_cntn"]
    assert [coordinate for coordinate, _ in record.coordinates][-1] == "s"


@pytest.mark.parametrize(
    ("name", "tuple_of_sections"),
    [
        pytest.param(
            "tenure",
            "((R·a_d+Y[age_kp]·z_d+y_R[age_kp],(1−δ)·h_d,z_d),"
            "(R·a_d+R_H·(1−δ)·h_d+Y[age_adj]·z_d+y_R[age_adj],z_d))[d]",
            id="tenure",
        ),
        *[pytest.param(name, law, id=name) for name, (_, law) in BRANCHES_OF_DRAWS.items()],
    ],
)
def test_the_law_of_motion_denotes_the_tuple_of_its_sections_indexed_by_the_label(
    name, tuple_of_sections, request
):
    """The definition of the law of motion of a branching stage maps the
    decision states and the label to the tuple of the values of its sections,
    indexed by the label."""
    denoted = request.getfixturevalue(name).definitions.denote(f"{name}:g:dcsn_to_cntn")
    assert tuple_of_sections in flat(str(denoted))


@pytest.mark.parametrize("name", list(BRANCHES_OF_DRAWS))
def test_the_label_shock_is_an_input_of_the_forward_block_and_not_of_cntn_to_dcsn(name, request):
    """The shock s is an input of the forward block that draws it and not of
    the backward block cntn_to_dcsn."""
    stage = request.getfixturevalue(name)
    assert "s" in inputs_listed(stage.initial.forward["dcsn_to_cntn"])
    assert "s" not in inputs_listed(stage.initial.backward["cntn_to_dcsn"])


@pytest.mark.parametrize(
    ("name", "lines"),
    [
        pytest.param(
            "tenure",
            [
                "in 𝑉_kp≻ : ℝ₊₊ × ℝ₊₊ × ℝ₊₊ → ℝ",
                "in 𝑉_adj≻ : ℝ₊₊ × ℝ₊₊ → ℝ",
                "in (𝑎𝑔𝑒_kp≻, 𝑎𝑔𝑒_adj≻) : {()} → Age × Age",
                "out 𝑉 : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ",
                "out 𝑎𝑔𝑒 : {()} → Age",
            ],
            id="tenure",
        ),
        pytest.param(
            "ret_choice",
            ["in 𝑉_w≻ : ℝ₊ → [−∞, ∞)", "in 𝑉_r≻ : ℝ₊ → [−∞, ∞)", "out 𝑉 : ℝ₊ → [−∞, ∞)"],
            id="ret_choice",
        ),
    ],
)
def test_the_decision_builder_takes_each_branch_value_on_the_fields_of_its_branch(
    name, lines, request
):
    """The signature of the decision builder lists the value of each branch on
    the sets of the fields of the branch and then the constants that it takes
    in, in the order of the header, then the fields at the decision perch."""
    signature = request.getfixturevalue(name).builder.bwd["cntn_to_dcsn"].signature()
    # white space collapsed, since the printed signature aligns its columns
    assert [" ".join(line.split()) for line in str(signature).splitlines()] == lines


# the two rows of this test carry a strict mark of expected failure
@pytest.mark.parametrize(
    "key",
    [pytest.param(key, marks=CARDS_KNOWN_FAILURES.get(key, ())) for key in CARDS],
    ids=lambda key: key[1],
)
def test_the_decision_and_policy_cards_of_tenure_state_what_the_example_draws(tenure, key):
    """The printed card of the decision builder and that of the policy builder
    of `tenure` state the keys of the operations, the signature, the sections,
    the rules and the outputs that the example page shows, and `parse` reads
    every sheet of `tenure`, none of whose lines is wider than 78 columns."""
    direction, name = key
    builder = {"backward": tenure.builder.bwd, "forward": tenure.builder.fwd}[direction][name]
    card, example = str(builder), DRAWN[key]
    _, keys, fragments = CARDS[key]
    assert [str(k) for k in builder.primitives.list()] == keys
    # the signature as a set of lines without white space, since the order of
    # the header and the columns may differ; the `out` line of the policy
    # builder must hold the type of 𝑑, and it is then left out of both sets
    drawn_lines = {flat(line) for line in card_section_lines(example, "Signature")[1:]}
    printed_lines = {flat(line) for line in card_section_lines(card, "Signature")[1:]}
    if name == "policy":
        out = next(line for line in printed_lines if line.startswith("out"))
        assert "𝑑:ℝ₊×ℝ₊₊×ℝ₊₊→{keep,adjust}" in out
        drawn_lines, printed_lines = (
            drawn_lines - {flat("out 𝑑 : ℝ₊ × ℝ₊₊ × ℝ₊₊ → {keep, adjust}")},
            printed_lines - {out},
        )
    assert printed_lines == drawn_lines
    for heading in ("At", "Where", "Conditions", "Source", "Definitions referenced"):
        assert flat("\n".join(card_section_lines(card, heading))) == flat(
            "\n".join(card_section_lines(example, heading))
        ), heading
    assert operation_rules(card_section_lines(card, "Operations")) == operation_rules(
        card_section_lines(example, "Operations")
    )
    for fragment in fragments:
        assert flat(fragment) in cells(card_section_lines(card, "Operations")), fragment
    report = parse_every_sheet(tenure)
    assert report["unparsed"] == [] and report["over_width"] == []


def test_the_card_of_the_forward_builder_of_tenure_states_what_the_example_page_draws(tenure):
    """The card of the forward builder of tenure prints the operations, the
    signature, the sections, the rules and the outputs that the example page
    draws."""
    builder = tenure.builder.fwd["dcsn_to_cntn"]
    card = str(builder)
    example = card_shown_on_the_page(TENURE_EXAMPLE, "STAGE tenure / FORWARD BUILDER dcsn_to_cntn")
    assert [str(key) for key in builder.primitives.list()] == ["Pushforward"]
    # the signature as a set of lines without white space, since the order of
    # the header and the columns may differ
    assert {flat(line) for line in card_section_lines(card, "Signature")[1:]} == {
        flat(line) for line in card_section_lines(example, "Signature")[1:]
    }
    assert [
        heading
        for heading in COMPARED_CARD_SECTIONS
        if flat("\n".join(card_section_lines(card, heading)))
        != flat("\n".join(card_section_lines(example, heading)))
    ] == []
    assert operation_rules(card_section_lines(card, "Operations")) == operation_rules(
        card_section_lines(example, "Operations")
    )
    # the measures of the two branches that the push-forward writes
    assert flat("μ_keep≻, μ_adjust≻") in cells(card_section_lines(card, "Operations"))


def test_every_sheet_of_tenure_reads_back_within_the_width_of_a_card(tenure):
    """parse_every_sheet reads back every sheet that the package prints for
    tenure, and finds no line wider than a card."""
    report = parse_every_sheet(tenure)
    assert report["sheets"] > 0
    assert report["unparsed"] == [] and report["over_width"] == []


@pytest.mark.parametrize(
    ("name", "heading"),
    [
        pytest.param("young_choice", "BACKWARD BUILDER cntn_to_dcsn", id="young_choice backward"),
        pytest.param("young_choice", "FORWARD BUILDER dcsn_to_cntn", id="young_choice forward"),
        pytest.param("young_choice", "POLICY BUILDER policy", id="young_choice policy"),
        pytest.param("old_choice", "BACKWARD BUILDER cntn_to_dcsn", id="old_choice backward"),
        pytest.param("old_choice", "FORWARD BUILDER dcsn_to_cntn", id="old_choice forward"),
        pytest.param("old_choice", "POLICY BUILDER policy", id="old_choice policy"),
        pytest.param(
            "entrepreneur_death", "BACKWARD BUILDER cntn_to_dcsn", id="entrepreneur_death backward"
        ),
        pytest.param(
            "retiree_death", "BACKWARD BUILDER cntn_to_dcsn", id="retiree_death backward"
        ),
        pytest.param(
            "worker_ageing", "BACKWARD BUILDER cntn_to_dcsn", id="worker_ageing backward"
        ),
        pytest.param("worker_ageing", "FORWARD BUILDER dcsn_to_cntn", id="worker_ageing forward"),
        pytest.param(
            "entrepreneur_ageing",
            "BACKWARD BUILDER cntn_to_dcsn",
            id="entrepreneur_ageing backward",
        ),
        pytest.param(
            "entrepreneur_ageing", "FORWARD BUILDER dcsn_to_cntn", id="entrepreneur_ageing forward"
        ),
    ],
)
def test_each_card_of_a_cagetti_de_nardi_stage_states_what_the_example_page_draws(
    name, heading, cagetti_de_nardi_example, request
):
    """The card that the package prints for a builder of a stage of the
    Cagetti–De Nardi model differs in no section from the card that the
    example page draws."""
    # the example page draws three cards of a stage that chooses and two of a
    # stage whose branch a shock selects
    titles = [line for line in cagetti_de_nardi_example if line.startswith(f"STAGE {name} / ")]
    assert len(titles) == (3 if name.endswith("_choice") else 2)
    stage = request.getfixturevalue(name)
    word, builder = heading.split(" BUILDER ")
    graph = stage.builder.fwd if word == "FORWARD" else stage.builder.bwd
    assert (
        differing_card_sections(
            graph[builder],
            card_shown_on_the_page(CAGETTI_DE_NARDI_EXAMPLE, f"STAGE {name} / {heading}"),
        )
        == []
    )


@pytest.mark.parametrize("name", ["entrepreneur_death", "retiree_death"])
def test_the_forward_builder_of_a_draw_from_the_family_invariant_is_refused(name, request):
    """The forward builder of a stage that draws its arrival shocks from the
    family Invariant, which the package does not admit, is refused naming the
    family."""
    with pytest.raises(NotConstructed, match="'Invariant'"):
        request.getfixturevalue(name).builder.fwd["dcsn_to_cntn"]


@pytest.mark.parametrize(
    ("name", "identity", "weighted_sum"),
    [
        pytest.param(
            "retiree_death",
            "retiree_death:G:cntn_to_dcsn",
            "↦β·(π_o·W_r≻+(1−π_o)·(η·V_young≻))",
            id="a categorical law of two labels",
        ),
        pytest.param(
            "bernoulli_draw",
            "t:G:cntn_to_dcsn",
            "↦(1−π)·V_y≻+π·V_o≻",
            id="a Bernoulli law gives p to the second label",
        ),
    ],
)
def test_the_aggregation_of_a_draw_denotes_the_branch_values_weighted_by_its_law(
    name, identity, weighted_sum, request
):
    """The definition of the aggregation of a draw is the sum of the branch
    values, each weighted by the probability that the law gives its label."""
    assert weighted_sum in flat(str(request.getfixturevalue(name).definitions.denote(identity)))


def test_the_definition_of_the_shock_of_retiree_death_states_its_law_as_written(retiree_death):
    """The definition of the shock s of retiree_death states its law as the
    stage file writes it."""
    denoted = retiree_death.definitions.denote("retiree_death:distribution:s")
    assert "s~Categorical(π_o,1−π_o)" in flat(str(denoted))


def test_the_arrival_builder_of_retiree_death_integrates_over_the_draws_of_the_offspring(
    retiree_death,
):
    """The rule of the arrival builder of retiree_death is the expectation of
    the decision value over the income y_n and the ability θ_n of the
    offspring."""
    printed = str(retiree_death.builder.bwd["dcsn_to_arvl"])
    assert flat("𝑉≺(a_rd) = E_{y_n, θ_n}[𝑉(𝑔≺(a_rd, y_n, θ_n))]") in operation_rules(
        card_section_lines(printed, "Operations")
    )


def test_the_compiled_aggregation_of_retiree_death_gives_the_value_of_the_derivation():
    """The compiled aggregation of retiree_death, calibrated at the values of
    the derivation by hand, gives the value of that derivation."""
    calibrated = corpus_stage("retiree_death").calibrate(DERIVATION_VALUES)
    aggregation = calibrated.builder.bwd["cntn_to_dcsn"].primitives["Aggregation"]
    compiled, values = aggregation.compile_kernel(), aggregation.kernel().parameter_values
    # the arguments W_r≻, V_young≻, a, y and θ, then the values of β, η and
    # π_o: 0.95 · (0.9 · 3 + 0.1 · 0.5 · 7) = 2.8975
    assert compiled(3.0, 7.0, 1.0, 1.0, 1.0, *values) == pytest.approx(
        0.95 * (0.9 * 3.0 + 0.1 * 0.5 * 7.0)
    )


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("worker_ageing", id="worker_ageing"),
        pytest.param("example_draw", id="the package's example of a draw"),
    ],
)
def test_the_forward_builder_of_a_draw_extends_the_measure_by_the_law_then_pushes_it_forward(
    name, request
):
    """The forward builder of a draw extends the measure by the law of the
    shock s and then makes one push-forward."""
    builder = request.getfixturevalue(name).builder.fwd["dcsn_to_cntn"]
    assert [str(key) for key in builder.primitives.list()] == [
        "DistributionExtension:s",
        "Pushforward",
    ]


def test_the_push_forward_of_a_draw_gives_one_measure_for_each_label(example_draw):
    """The rules of the forward builder of the package's example of a draw give
    the measure of each label: the extended measure of the states that draw
    the label and whose section lands in the set B."""
    builder = example_draw.builder.fwd["dcsn_to_cntn"]
    entries = operations_entries(parse_card(str(builder))["sections"]["Operations"])
    printed_rules = "".join(flat("".join(entry["rule"])) for entry in entries)
    measures = (
        "μ_young≻(B)=μ⊗P_s({a_d,s∈ℝ₊×{young,old}|s=young∧𝑔_young≻(a_d)∈B})",
        "μ_old≻(B)=μ⊗P_s({a_d,s∈ℝ₊×{young,old}|s=old∧𝑔_old≻(a_d)∈B})",
    )
    assert [measure for measure in measures if measure not in printed_rules] == []


def test_the_conservation_of_mass_of_retiree_death_is_required_on_the_law_of_its_shock(
    retiree_death,
):
    """The conservation of mass of retiree_death is required, not established,
    and names the law of its shock s."""
    held = mass_conservation(retiree_death)
    assert [item.status for item in held] == ["required"]
    assert "retiree_death:distribution:s" in [str(subject) for subject in held[0].named_identities]


@pytest.mark.parametrize(
    ("name", "key", "text", "left_out"),
    [
        pytest.param(
            "tenure",
            "cntn_to_dcsn:Pullback:keep",
            "𝑔 of dcsn_to_cntn: 𝑔_keep≻(a_d, h_d, z_d, age_kp) = "
            "(R*a_d + Y[age_kp]*z_d + y_R[age_kp], (1 - δ)*h_d, z_d)\n"
            "outputs (w_kp≻, h_kp≻, z_kp≻); w_kp≻ reads a_d, z_d, age_kp; h_kp≻ reads h_d; "
            "z_kp≻ reads z_d",
            ("d", "age_adj"),
            id="keep of tenure",
        ),
        pytest.param(
            "ret_choice",
            "policy:Pullback:work",
            "𝑔 of dcsn_to_cntn: 𝑔_work≻(a_d) = a_d",
            ("d",),
            id="work of ret_choice",
        ),
        pytest.param(
            "old_choice",
            "cntn_to_dcsn:Pullback:retiree",
            "𝑔 of dcsn_to_cntn: 𝑔_retiree≻(a, θ) = a\nunused θ",
            ("d",),
            id="retiree of old_choice",
        ),
    ],
)
def test_the_section_of_a_pullback_of_one_branch_is_the_law_read_at_its_label(
    name, key, text, left_out, request
):
    """The kernel of a pullback of one branch holds under `section` the kernel
    of the law read at the label of the branch: the law's title, its arguments
    but d and a constant that another branch alone reads, a part of its
    outputs and its origins, with no Python text, no parameter and no section
    of its own."""
    piece = request.getfixturevalue(name).builder.bwd.primitives[key]
    whole, section_kernel = piece.kernel(), piece.kernel().section
    # the printed kernel of a section of one output has no line of outputs
    assert str(section_kernel) == text
    assert str(section_kernel).split(": ", 1)[0] == str(whole).split(": ", 1)[0]
    assert [argument for argument, _ in section_kernel.arguments] == [
        argument for argument, _ in whole.arguments if argument not in left_out
    ]
    assert set(section_kernel.outputs) < set(whole.outputs)
    assert section_kernel.origins == whole.origins
    assert (section_kernel.python, section_kernel.parameters, section_kernel.section) == (
        None,
        (),
        None,
    )


@pytest.mark.parametrize(
    ("name", "key"),
    [
        pytest.param("tenure", "cntn_to_dcsn:Pullback:keep", id="keep of tenure"),
        pytest.param("ret_choice", "policy:Pullback:work", id="work of ret_choice"),
        pytest.param("old_choice", "cntn_to_dcsn:Pullback:retiree", id="retiree of old_choice"),
    ],
)
def test_the_kernel_of_a_pullback_of_one_branch_prints_the_label_coordinate_unused(
    name, key, request
):
    """A pullback of one branch applies the complete law of motion, whose
    printed kernel lists the label coordinate d as unused."""
    piece = request.getfixturevalue(name).builder.bwd.primitives[key]
    assert "unused d" in str(piece.kernel())


@pytest.mark.parametrize(
    ("name", "key", "section_name"),
    [
        pytest.param("tenure", "cntn_to_dcsn:Pullback:keep", "𝑔_keep≻", id="keep of tenure"),
        pytest.param("ret_choice", "policy:Pullback:work", "𝑔_work≻", id="work of ret_choice"),
        pytest.param(
            "old_choice", "cntn_to_dcsn:Pullback:retiree", "𝑔_retiree≻", id="retiree of old_choice"
        ),
    ],
)
def test_the_card_of_a_pullback_of_one_branch_prints_the_name_of_its_section(
    name, key, section_name, request
):
    """The section that the kernel of a pullback of one branch holds is named
    for the label of the branch, and the card of the pullback prints that
    name."""
    piece = request.getfixturevalue(name).builder.bwd.primitives[key]
    assert str(piece.kernel().section).split(": ", 1)[1].split("(")[0] == section_name
    assert section_name in str(piece.denote())


@pytest.mark.parametrize(
    ("direction", "key"),
    [
        pytest.param("backward", "cntn_to_dcsn:Aggregation", id="the aggregation"),
        pytest.param("forward", "dcsn_to_cntn:Pushforward", id="the push-forward"),
    ],
)
def test_the_kernel_of_an_operator_of_tenure_that_is_no_pullback_holds_no_section(
    direction, key, tenure
):
    """The kernel of an operator of tenure that is not the pullback of one
    branch holds None under `section`, where the pullback of one branch holds
    a section."""
    pullback = tenure.builder.bwd.primitives["cntn_to_dcsn:Pullback:keep"]
    assert pullback.kernel().section is not None
    graph = {"backward": tenure.builder.bwd, "forward": tenure.builder.fwd}[direction]
    assert graph.primitives[key].kernel().section is None


def test_a_line_identity_reads_its_block_branch_and_key_from_its_address():
    """A line inside a nested block takes its block, the label of its branch
    and its key within the branch from its address, and a line outside a
    nested block has no branch."""
    line = Identity("line", address="dcsn_to_cntn.keep.cash_on_hand")
    assert (line.block, line.branch, line.key_within("dcsn_to_cntn.keep")) == (
        "dcsn_to_cntn",
        "keep",
        "cash_on_hand",
    )
    assert Identity("line", address="policy.choice").branch is None


def test_a_measure_on_one_branch_carries_the_label_in_its_field():
    """The identity of a measure on one branch carries the label of the branch
    in its field, and differs from the measure at the perch."""
    keep = Identity("measure", stage="s", perch="cntn", field="keep")
    assert str(keep) == "s:measure:cntn:keep" and keep != Identity(
        "measure", stage="s", perch="cntn"
    )


def test_a_nested_line_without_an_id_keeps_its_own_term_under_its_position(tenure):
    """The third line of the branch keep of tenure, which has no id, is
    addressed by its position under the label and keeps its own equation."""
    assert to_source(tenure.definitions["dcsn_to_cntn.keep.3"].equations[0]) == "z_kp = z_d"


@pytest.mark.parametrize(
    ("name", "addresses"),
    [
        pytest.param(
            "tenure",
            [
                "dcsn_to_cntn.keep.cash_on_hand",
                "dcsn_to_cntn.keep.housing_kept",
                "dcsn_to_cntn.keep.3",
                "dcsn_to_cntn.adjust.total_wealth",
                "dcsn_to_cntn.adjust.2",
            ],
            id="tenure",
        ),
        pytest.param(
            "branching_with_one_id_twice",
            ["dcsn_to_cntn.work.assets", "dcsn_to_cntn.retire.assets"],
            id="one id written in both branches",
        ),
    ],
)
def test_the_definitions_address_each_line_of_a_nested_block_under_its_label(
    name, addresses, request
):
    """The definitions table addresses each line of a nested block under the
    label of its branch, so that one id written in two branches gives two
    lines."""
    table = request.getfixturevalue(name).definitions
    assert [
        str(record.identity)
        for record in table.values()
        if record.kind == "line" and record.identity.block == "dcsn_to_cntn"
    ] == addresses


def test_a_branch_is_a_block_of_the_forward_initial_diagram_holding_its_lines_by_id(tenure):
    """A branch of tenure is a block of the forward initial diagram, reached by
    its label from its block, and its lines are reached from it by their
    ids."""
    block = tenure.initial.forward["dcsn_to_cntn"]
    assert [
        repr(block["keep"]),
        repr(block["keep"]["cash_on_hand"]),
        repr(block["adjust"]["2"]),
    ] == [
        "Block('tenure', 'dcsn_to_cntn.keep')",
        "Line('tenure', 'dcsn_to_cntn.keep.cash_on_hand')",
        "Line('tenure', 'dcsn_to_cntn.adjust.2')",
    ]


@pytest.mark.parametrize("grain", ["builder", "sub_builders", "primitives"])
@pytest.mark.parametrize("label", ["keep", "adjust"])
def test_the_forward_builder_of_tenure_holds_no_branch_at_any_grain(label, grain, tenure):
    """A label that names a block of the forward initial diagram names no part
    of the forward builder, of its sub-builders or of its primitives, whose
    wires and boxes carry the branches."""
    assert (
        repr(tenure.initial.forward["dcsn_to_cntn"][label])
        == f"Block('tenure', 'dcsn_to_cntn.{label}')"
    )
    builder = tenure.dcsn.builder.fwd
    handle = {
        "builder": builder,
        "sub_builders": builder.sub_builders,
        "primitives": builder.primitives,
    }[grain]
    with pytest.raises(KeyError):
        handle[label]


# the range condition of a branch line: the value that the line writes lies in
# the set of its field
@pytest.mark.parametrize(
    ("name", "status"),
    [
        pytest.param(
            "branching_example",
            "established",
            id="each branch line writes into the set of its field",
        ),
        pytest.param(
            "branching_with_a_line_outside_its_set",
            "required",
            id="a branch line can write outside the set of its field",
        ),
    ],
)
def test_the_conservation_of_mass_follows_the_range_conditions_of_the_branch_lines(
    name, status, request
):
    """The conservation of mass of a choice between branches is established
    where the range condition of every branch line is, and required where one
    is not."""
    stage = request.getfixturevalue(name)
    assert [item.status for item in mass_conservation(stage)] == [status]


def test_the_forward_card_prints_the_range_condition_of_a_branch_line_and_no_mass(
    branching_with_a_line_outside_its_set,
):
    """Where a branch line can write outside the set of its field, so that the
    conservation of mass is required, the card of the forward builder prints
    its range condition and no condition on the mass."""
    shifted = branching_with_a_line_outside_its_set
    assert [item.status for item in mass_conservation(shifted)] == ["required"]
    card = str(shifted.builder.fwd["dcsn_to_cntn"])
    assert "a_d − 1 ∈ ℝ₊" in card and "mass" not in card


@pytest.mark.parametrize(
    ("changes", "status"),
    [
        pytest.param((), "required", id="weights that are parameters"),
        pytest.param((("(π, 1 - π)", "(0.5, 0.5)"),), "established", id="numbers that sum to one"),
    ],
)
def test_the_conservation_of_mass_of_a_draw_on_its_law_follows_whether_its_weights_are_numbers(
    changes, status
):
    """The conservation of mass of a draw is required while a weight of its law
    is a parameter and established by numbers that sum to one, and it names
    the law."""
    stage = stage_from_text(changed(SHOCK_BRANCHING, *changes))
    assert [(item.status, str(item.named_identities[1])) for item in mass_conservation(stage)] == [
        (status, "t:distribution:s")
    ]


def test_weights_of_a_draw_that_do_not_sum_to_one_are_refused_at_calibration():
    """A law whose two weights are parameters is refused at a calibration whose
    values do not sum to one."""
    two = stage_from_text(
        changed(SHOCK_BRANCHING, ("π : [0,1]", "p : [0,1]\nq : [0,1]"), ("(π, 1 - π)", "(p, q)"))
    )
    with pytest.raises(ConstructionError) as refused:
        two.calibrate({"p": 0.3, "q": 0.6})
    assert refused.value.rule == "distribution-domain" and "not to one" in str(refused.value)


def test_the_forward_builders_graph_ends_at_the_branch_measures(tenure):
    """The outputs of the signature of the forward builders graph of tenure are
    the measures of its two branches, not the first of them alone."""
    assert [wire.name for wire in tenure.builder.fwd.signature().outputs] == [
        "μ_keep≻",
        "μ_adjust≻",
    ]


def test_the_kernel_of_the_aggregation_of_a_calibrated_draw_holds_the_value_of_its_weight(
    calibrated_draw_aggregation,
):
    """The kernel of the aggregation of a draw calibrated at π = 0.25 holds
    that value."""
    assert calibrated_draw_aggregation.kernel().parameter_values == (0.25,)


def test_the_compiled_aggregation_of_a_draw_evaluates_arrays_of_points(
    calibrated_draw_aggregation,
):
    """The compiled aggregation of a draw takes arrays of branch values and
    gives the weighted sum at each point."""
    compiled = calibrated_draw_aggregation.compile_kernel()
    values = calibrated_draw_aggregation.kernel().parameter_values
    # the arguments V_y≻, V_o≻ and a_d, then the value of π:
    # 0.25 · 4 + 0.75 · 8 = 7 and 0.25 · 8 + 0.75 · 4 = 5
    assert numpy.allclose(
        compiled(
            numpy.array([4.0, 8.0]), numpy.array([8.0, 4.0]), numpy.array([1.0, 1.0]), *values
        ),
        [7.0, 5.0],
    )


def test_the_printed_kernel_of_an_aggregation_counts_a_coordinate_that_the_law_reads(fecundity):
    """The output line of the printed kernel of the aggregation of fecundity
    lists a_fecd alone as unused, since the law of the shock reads
    age_fecd."""
    printed = str(fecundity.builder.bwd["cntn_to_dcsn"].primitives["Aggregation"].kernel())
    assert printed.splitlines()[1] == "output V; unused a_fecd"


@pytest.mark.parametrize("case", REFUSED, ids=lambda case: Path(case[0]).name)
def test_a_stage_file_of_a_branching_form_that_the_package_does_not_construct_is_refused(case):
    """Elaborating a stage file of an application whose branching form the
    package does not construct is refused under its rule, at its address,
    naming the cause."""
    path, rule, address, words = case
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(load_stage(ROOT / path))
    assert (refused.value.rule, refused.value.address) == (rule, address)
    assert [word for word in words if word not in str(refused.value)] == []


@pytest.mark.parametrize("case", BRANCHING_REFUSALS, ids=lambda case: case[0])
def test_a_malformed_branching_block_is_refused_under_its_rule(case):
    """A change of the package's example of a branching block into a form that
    the language does not admit is refused under its rule, at its address,
    with the phrases of its message."""
    _, changes, rule, address, words = case
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(branching_text(*changes))
    error = refused.value
    assert error.rule == rule and (address is None or error.address == address), (
        error.rule,
        error.address,
    )
    assert [word for word in words if word not in str(error)] == []


@pytest.mark.parametrize("case", SHOCK_REFUSALS, ids=lambda case: case[0])
def test_a_malformed_branch_a_shock_selects_is_refused_under_its_rule(case):
    """A change of the package's example of a draw into a form that the
    language does not admit is refused under its rule, at its address, with
    the phrases of its message."""
    _, changes, rule, address, words = case
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(SHOCK_BRANCHING, *changes))
    error = refused.value
    assert (error.rule, error.address) == (rule, address), (error.rule, error.address)
    assert [word for word in words if word not in str(error)] == []
