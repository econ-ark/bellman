"""The acceptance file of unit U2 of the build of specification 0.7, the
union of a stage file and its additions: one test for each of the five
acceptance items of §U2 of the implementation specification, named
`test_item_<n>_<claim>`. The corpus is the sixteen pre-implementation case
studies of the specification, whose addition and refusal files stand under
`tests/additions/` with the stage files of the two new applications;
`tests/additions/expected.json` records, for each run the checker of the
case studies made, the stage file, the addition files, the count of places
the elaborated union gives and the names the addition created, read from the
check report of the case study.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import ROOT

from bellman.fold.block_lines import symbol_groups
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_stage, load_stage
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.union import union

ADDITIONS = ROOT / "packages/bellman/tests/additions"
RUNS = json.loads((ADDITIONS / "expected.json").read_text(encoding="utf-8"))


def run_id(run):
    return f"{run['study']}: {' + '.join(Path(a).name for a in run['additions'])}"


def places_of(stage, from_message=False):
    """The addresses `stage.places()` lists. For a run whose check report
    counted the places of a refusal's message, on a branching stage whose
    branch lines carry ids, where `places()` was refused before unit U3c, the
    addresses without the definitions, which the message did not list."""
    addresses = [row["address"] for row in stage.places()]
    if not from_message:
        return addresses
    functions = set(symbol_groups(stage).get("functions", ()))
    return [address for address in addresses if address not in functions]


def application_stage(stage):
    """The stage file of an application, `<application>/<key>/<key>.bl`."""
    application, key, name = stage.split("/")
    return ROOT / "applications" / application / "declaration/stages" / key / name


def stage_and_alone(run):
    """The elaborated union of a recorded run and its stage file alone."""
    stage = ROOT / run["stage"]
    additions = [ROOT / addition for addition in run["additions"]]
    return elaborate_stage(load_stage(stage, additions)), elaborate_stage(load_stage(stage))


# --- the acceptance items ---


@pytest.mark.parametrize("run", RUNS, ids=run_id)
def test_item_1_every_case_study_union_elaborates_to_the_places_its_check_records(run):
    stage, alone = stage_and_alone(run)
    found = places_of(stage, run["from_message"])
    before = places_of(alone, run["from_message"])
    assert sorted(set(found) - set(before)) == sorted(run["created"])
    if run["from_message"]:
        # the check report counted the places of the refusal's message, which
        # lists no definition; the count it gives is the stage's plus the
        # addition's, so the difference is what is compared
        assert len(found) - len(before) == len(run["created"])
    else:
        assert len(found) == run["places"]


# the refusals files of the case studies (aspect A24 of the writer's sheet):
# each with its stage, the rule its first refusal fires under, the words the
# sentence holds, and the file whose position the sentence names beside the
# refused item's own
A24 = [
    (
        "benhabib-2019",
        "benhabib-2019/benhabib_bellman/benhabib_bellman.bl",
        "declared-twice",
        ("`method : !egm`", "`policy.method : !vfi`"),
        "refusals.bl",
    ),
    (
        "cagetti-denardi-2006",
        "cagetti-denardi-2006/retiree/retiree.bl",
        "type-conflict",
        ("'V'", "`ℝ @ !vlu`", "`ℝ₊ @ !vlu`"),
        "retiree.bl",
    ),
    ("cons-port", "cons-port/cons/cons.bl", "declared-twice", ("'Xa'",), "cons.bl"),
    (
        "consumption-savings-iid",
        "consumption-savings-iid/cons_savings_iid/cons_savings_iid.bl",
        "declared-twice",
        ("'𝑑𝑢𝑖𝑛𝑣'",),
        "cons_savings_iid.bl",
    ),
    (
        "durables",
        "durables/tenure/tenure.bl",
        "type-conflict",
        ("'a_d'", "`ℝ₊`", "`ℝ₊₊`"),
        "tenure.bl",
    ),
    (
        "epstein-zin-savings",
        "epstein-zin-savings/ez_savings/ez_savings.bl",
        "label-not-in-parent",
        ("`policy.evaluate.method`", "'cntn_to_dcsn'", "'policy'"),
        "ez_savings.bl",
    ),
    (
        "housing-frictions",
        "housing-frictions/house_choice/house_choice.bl",
        "declared-twice",
        ("'choice'", "'policy'"),
        "house_choice.bl",
    ),
    (
        "housing-owner",
        "housing-owner/consumption_choice/consumption_choice.bl",
        "label-not-in-parent",
        ("`cntn_to_dcsn.evaluate[D_{w_d}(V)].method`", "'policy'"),
        "consumption_choice.bl",
    ),
    (
        "housing-renting",
        "housing-renting/tenure_choice/tenure_choice.bl",
        "declared-twice",
        ("'value'", "'dcsn_to_arvl'"),
        "tenure_choice.bl",
    ),
    (
        "pension-retirement",
        "pension-retirement/worker_saving/worker_saving.bl",
        "type-conflict",
        ("'c_p'", "`ℝ₊ @ !ctrl`", "`ℝ₊₊ @ !ctrl`"),
        "worker_saving.bl",
    ),
    (
        "portfolio-choice",
        "portfolio-choice/cons/cons.bl",
        "declared-twice",
        (
            "`grid`",
            "`grid : !Cartesian(a=(a_min, a_max, n_a))`",
            "`policy.grid : !Cartesian(a=(m_min, m_max, n_m))`",
        ),
        "refusals.bl",
    ),
    (
        "retirement-choice",
        "retirement-choice/ret_choice/ret_choice.bl",
        "label-not-in-parent",
        ("`policy.evaluate.method`", "'dcsn_to_arvl'"),
        "ret_choice.bl",
    ),
    (
        "smooth-ambiguity-savings",
        "smooth-ambiguity-savings/sa_savings/sa_savings.bl",
        "type-conflict",
        ("'V[>]'", "`ℝ₊₊ @ !vlu`", "`ℝ @ !vlu`"),
        "sa_savings.bl",
    ),
]


@pytest.mark.parametrize("case", A24, ids=lambda case: case[0])
def test_item_2_the_refusals_of_the_sheet_fire_with_the_rule_name_and_both_positions(case):
    study, stage, rule, words, other = case
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(load_stage(application_stage(stage), [ADDITIONS / study / "refusals.bl"]))
    error = refused.value
    assert error.rule == rule
    assert Path(error.file).name == "refusals.bl" and error.line is not None
    assert all(word in error.message for word in words), (words, error.message)
    # the sentence names the earlier item's position, in its file
    assert f"{other}:" in error.message


# the runs whose declared level is compared with the stage alone: one stage
# with rows under a solution method, two additions in order, a branching
# stage, a stage with two added builders and a replacing selection
DECLARED = [
    run
    for run in RUNS
    if run_id(run)
    in (
        "buffer-stock: methods.bl",
        "consumption-savings-iid: methods.bl + methods.additions.bl",
        "durables: methods.tenure.bl",
        "B-retirement-choice-pension: pension_choice.bl",
        "cons-port: methods.cons.vfi.bl",
        "pension-retirement: methods.worker_saving.bl",
    )
]


@pytest.mark.parametrize("run", DECLARED, ids=run_id)
def test_item_3_the_declared_level_of_a_unioned_stage_is_the_stage_file_elaborated_alone(run):
    stage, alone = stage_and_alone(run)
    assert str(stage.declared.list()) == str(alone.builder.list())
    for direction in ("bwd", "fwd"):
        assert str(getattr(stage.declared, direction).signature()) == str(
            getattr(alone.builder, direction).signature()
        )
        assert str(getattr(stage.declared, direction).denote()) == str(
            getattr(alone.builder, direction).denote()
        )
    assert str(stage.declared.policy.denote()) == str(alone.builder.policy.denote())
    assert "additions" in stage.provenance and "additions" not in alone.provenance


def test_item_4_two_additions_in_order_equal_one_file_and_a_component_typed_by_both_is_refused():
    stage = (
        ROOT
        / "applications/consumption-savings-iid/declaration/stages"
        / "cons_savings_iid/cons_savings_iid.bl"
    )
    first = ADDITIONS / "consumption-savings-iid/methods.bl"
    second = ADDITIONS / "consumption-savings-iid/methods.additions.bl"
    parsed = parse_with_spans(stage.read_text(encoding="utf-8"), str(stage))
    two = union(
        parsed,
        [
            parse_with_spans(first.read_text(encoding="utf-8"), str(first)),
            parse_with_spans(second.read_text(encoding="utf-8"), str(second)),
        ],
    )
    # one file holding both additions, the second's metadata line left out
    both = first.read_text(encoding="utf-8") + "".join(
        line
        for line in second.read_text(encoding="utf-8").splitlines(keepends=True)
        if not line.startswith("@methods:")
    )
    one = union(parsed, [parse_with_spans(both, "both.bl")])
    assert two.term == one.term
    assert {span.file for span in two.spans.values()} == {str(stage), str(first), str(second)}
    # the deliberate conflict of application A: a third addition typing the
    # policy builder's method component a second time
    folder = ADDITIONS / "new-applications/A-buffer-stock-pension"
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(
            load_stage(
                folder / "stage/buffer_stock.bl",
                [
                    folder / "additions/pension.bl",
                    folder / "additions/egm.bl",
                    folder / "additions/conflict_slot.bl",
                ],
            )
        )
    error = refused.value
    # the conflicting line is the second item of its file, on its seventh line
    assert (error.rule, error.address, Path(error.file).name) == (
        "declared-twice",
        "2",
        "conflict_slot.bl",
    )
    assert error.line == 7
    assert "egm.bl:" in error.message and "`policy.method : !egm`" in error.message
    assert "`policy.method : !vfi`" in error.message


def test_item_5_application_b_merges_nested_blocks_by_label_and_keeps_two_added_builders_whole():
    folder = ADDITIONS / "new-applications/B-retirement-choice-pension"
    stage = elaborate_stage(
        load_stage(folder / "stage/choice.bl", [folder / "additions/pension_choice.bl"])
    )
    found = places_of(stage)
    # the lines postpended inside the branches, under the stage's labels
    assert {
        "dcsn_to_cntn.work.pension_if_working",
        "dcsn_to_cntn.retire.pension_if_retiring",
    } <= set(found)
    # the two arrival builders added whole, entering the stage at arrival
    assert {"arvl_to_dcsn", "dcsn_to_arvl", "dcsn_to_arvl.survival_value"} <= set(found)
    assert set(stage.builder) >= {
        ("arvl", "dcsn"),
        ("dcsn", "arvl"),
        ("dcsn", "cntn"),
        ("cntn", "dcsn"),
    }
    assert "arvl_to_dcsn" in str(stage.list()) and "dcsn_to_arvl" in str(stage.list())
    # the balance prepended to the branching block's domain and postpended to
    # each branch: the measures of the forward builder lie on ℝ₊ × Xp, where
    # the stage alone has them on ℝ₊
    signature = str(stage.builder["dcsn", "cntn"].signature())
    assert signature.count("finite measure on ℝ₊ × Xp") == 3
    # the conflict: a line id written in both files
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(
            load_stage(
                folder / "stage/choice.bl",
                [folder / "additions/pension_choice.bl", folder / "additions/conflict_line.bl"],
            )
        )
    error = refused.value
    assert (error.rule, error.address, Path(error.file).name) == (
        "declared-twice",
        "cntn_to_dcsn.choice_value",
        "conflict_line.bl",
    )
    assert "choice.bl:" in error.message and "'choice_value'" in error.message
