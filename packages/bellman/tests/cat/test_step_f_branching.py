"""The acceptance file of the first build of branching, step F (the second
layer of the tests, `packages/bellman/README.md` §8): one test for each of
items 1 to 5 of §6 of `branching-unified.md`; item 6 is AAS's reading of
notebook 10.
Deleted when the next amendment is accepted."""
from collections import Counter
from pathlib import Path

import pytest

from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import (
    assemble_trellis,
    calibrate_trellis,
    configure_trellis,
    elaborate_trellis,
    load_recipe,
    methodize_trellis,
)
from bellman.factory.trellis import positions
from bellman.factory.joins import computable_together, inter_period_joins, period_joins
from bellman.stage.stage_answers import branches, kind
from bellman.stage.stage_answers import fields
from bellman.refusals import ConstructionError
from conftest import (DURABLES, HOUSING, PENSION, PENSION_FILL, PRELIMINARY, RETIREMENT, ROOT,
                      flat, rules, section, wage_schedule)
from sheets_parse import parse_every_sheet


def named(fields):
    return tuple(identity.field for identity in fields)


def test_item_1_both_stages_are_branching_stages_with_their_branches_and_their_law(tenure, ret_choice):
    assert (kind(tenure), kind(ret_choice)) == ("branching", "branching")
    assert {label: named(fields) for label, fields in branches(tenure).items()} == {
        "keep": ("w_kp", "h_kp", "z_kp"), "adjust": ("w_adj", "z_adj")}
    assert {label: named(fields) for label, fields in branches(ret_choice).items()} == {
        "work": ("a_w",), "retire": ("a_r",)}
    law = tenure.definitions["tenure:g:dcsn_to_cntn"]
    assert [name for name, _ in law.coordinates] == ["a_d", "h_d", "z_d", "d"]
    assert [str(line) for line in law.equations] == [
        "dcsn_to_cntn.keep.cash_on_hand", "dcsn_to_cntn.keep.housing_kept", "dcsn_to_cntn.keep.3",
        "dcsn_to_cntn.adjust.total_wealth", "dcsn_to_cntn.adjust.2"]
    # the decision builder's signature: each branch value on its branch's fields,
    # in the header's order (E6, E33), white space collapsed
    for stage, expected in ((tenure, [
            "in 𝑉_kp≻ : ℝ₊₊ × ℝ₊₊ × ℝ₊₊ → ℝ", "in 𝑉_adj≻ : ℝ₊₊ × ℝ₊₊ → ℝ",
            "out 𝑉 : ℝ₊ × ℝ₊₊ × ℝ₊₊ → ℝ"]), (ret_choice, [
            "in 𝑉_w≻ : ℝ₊ → [−∞, ∞)", "in 𝑉_r≻ : ℝ₊ → [−∞, ∞)",
            "out 𝑉 : ℝ₊ → [−∞, ∞)"])):
        printed = [" ".join(line.split()) for line in str(stage.builder.bwd["cntn_to_dcsn"].signature()).splitlines()]
        assert printed == expected
    # the law's own definition: the tuple of its sections' values indexed by the
    # label coordinate (E1, E4)
    denoted = "".join(ch for ch in str(tenure.definitions.denote("tenure:g:dcsn_to_cntn")) if not ch.isspace() and ch != "│")
    assert "((R·a_d+𝑦(z_d),(1−δ)·h_d,z_d),(R·a_d+R_H·(1−δ)·h_d+𝑦(z_d),z_d))[d]" in denoted


# the examples of the branching run of 23 September 2026 that the tests read, copied into the corpus;
# the cards of their fenced blocks that the package prints are printed by it, in the card's form of
# the internal developer release 0.01
RUN = ROOT / PRELIMINARY / "branching"


def drawn(title):
    """The ```text block of `example-tenure.md` §4 that opens with `title`."""
    lines = (RUN / "example-tenure.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line == title)
    closed = next(i for i in range(start, len(lines)) if lines[i].strip() == "```")
    return "\n".join(lines[start:closed])


def cells(lines):
    """The rows of the entries of an `Operations` section, each entry's
    number and key and its `in:` and `out:` lines above its short line,
    flattened; `lines` is the section as `section` gives it, its heading
    first."""
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


# the three cards of `tenure` as example-tenure.md §4 shows them (item 2): the title, the keys of
# the operations, and the maps and composites that the `out:` of an entry prints
CARDS = {
    ("backward", "cntn_to_dcsn"): ("STAGE tenure / BACKWARD BUILDER cntn_to_dcsn",
        ["Pullback:keep", "Pullback:adjust", "Aggregation", "Evaluation"],
        ["𝑉_kp≻ ∘ 𝑔_keep≻", "𝑉_adj≻ ∘ 𝑔_adjust≻"]),
    ("forward", "dcsn_to_cntn"): ("STAGE tenure / FORWARD BUILDER dcsn_to_cntn", ["Pushforward"],
        ["μ_keep≻, μ_adjust≻"]),
    ("backward", "policy"): ("STAGE tenure / POLICY BUILDER policy",
        ["Pullback:keep", "Pullback:adjust", "choice:Aggregation", "choice:Argmax", "Evaluation"],
        ["(a_d, h_d, z_d, d) ↦ (𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d)), 𝑉_adj≻(𝑔_adjust≻(a_d, h_d, z_d)))[d]"]),
}
DRAWN = {key: drawn(title) for key, (title, _, _) in CARDS.items()}


@pytest.mark.parametrize("key", list(CARDS), ids=lambda key: key[1])
def test_item_2_the_three_cards_of_tenure_state_what_the_example_draws(tenure, key):
    direction, name = key
    builder = {"backward": tenure.builder.bwd, "forward": tenure.builder.fwd}[direction][name]
    card, example = str(builder), DRAWN[key]
    _, keys, fragments = CARDS[key]
    assert [str(k) for k in builder.primitives.list()] == keys
    # E33: the header's order and the columns are the known differences, so the signature is a set
    # of lines with white space collapsed; the policy's `out` line carries the powerset of the
    # plain type (P20), so it is compared as a fragment
    drawn_lines = {flat(line) for line in section(example, "Signature")[1:]}
    printed_lines = {flat(line) for line in section(card, "Signature")[1:]}
    if name == "policy":
        out = next(line for line in printed_lines if line.startswith("out"))
        assert "𝑑:ℝ₊×ℝ₊₊×ℝ₊₊→{keep,adjust}" in out
        drawn_lines, printed_lines = drawn_lines - {flat("out 𝑑 : ℝ₊ × ℝ₊₊ × ℝ₊₊ → {keep, adjust}")}, printed_lines - {out}
    assert printed_lines == drawn_lines
    for heading in ("At", "Where", "Conditions", "Source", "Definitions referenced"):
        assert flat("\n".join(section(card, heading))) == flat("\n".join(section(example, heading))), heading
    assert rules(section(card, "Operations")) == rules(section(example, "Operations"))
    for fragment in fragments:
        assert flat(fragment) in cells(section(card, "Operations")), fragment
    report = parse_every_sheet(tenure)
    assert report["unparsed"] == [] and report["over_width"] == []


DOBRESCU = f"{PRELIMINARY}/dobrescu-etal-2018/"
CAGETTI = "applications/cagetti-denardi-2006/declaration/stages/"
# the files the first build refuses at recognition (E14, E30): the path, the
# rule, the address and the words the refusal names
REFUSED = [(DOBRESCU + name, "branch-tuple-mismatch", "cntn_to_dcsn.value", ("policy.choice", "no tuple"))
           for name in ("plan_choice.bl", "contrib.bl", "invest.bl")] + [
          (CAGETTI + name, "not-constructed", "dcsn_to_cntn", ("beside its branches", "one control"))
           for name in ("young_entrepreneur/young_entrepreneur.bl",
                        "old_entrepreneur/old_entrepreneur.bl")]


@pytest.mark.parametrize("case", REFUSED, ids=lambda case: Path(case[0]).name)
def test_item_3_the_forms_the_first_build_does_not_construct_are_refused_at_recognition(case):
    path, rule, address, words = case
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(load_stage(ROOT / path))
    assert (refused.value.rule, refused.value.address) == (rule, address)
    assert all(word in str(refused.value) for word in words), str(refused.value)


def test_item_5_the_encoding_of_tenure_validates_against_the_one_schema(tenure):
    """Item 5: the reader validates the encoding of `tenure` against the
    package's one schema (decision S3 of the structure review's cleanup) and
    checks its references, its scopes and its wires; the branching stage's
    recording stands beside the others."""
    import json
    from bellman.display.encoding_checks import validate_encoding
    validate_encoding(json.loads(json.dumps(tenure.encoding())))
    assert (Path(__file__).parents[1] / "snapshot" / "tenure.json").is_file()


def arrow(join):
    return f"{join['from'][0]}:{join['from'][1]} → {join['to'][0]}:{join['to'][1]}"


# the branches of tenure and house_choice join the decision states of the
# stages they enter, which declare no arrival perch (decisions MB-U24, MB-U40)
TENURE_WITHIN = ["tenure:h_kp → keeper_cons:h_d", "tenure:w_adj → adjuster_cons:m",
                 "tenure:w_kp → keeper_cons:w_d", "tenure:z_adj → adjuster_cons:z_d", "tenure:z_kp → keeper_cons:z_d"]
RET_WITHIN = ["ret_choice:a_r → retiree_cons:a_ret", "ret_choice:a_w → worker_cons:a_w"]
PENSION_WITHIN = ["worker_saving:y_f → retire_choice:y_f", "worker_saving:y_p → retire_choice:y_p"]
HOUSE_WITHIN = ["house_choice:h_kp → keeper_saving:h_d", "house_choice:w_adj → adjuster_saving:m",
                "house_choice:w_kp → keeper_saving:m_d"]
# for each registry (examples/<key>/expected.md §6): the periods, the occurrences, the joins and
# layers of periods[0] and of every later period, the outputs, the inter-period joins
WHOLE = {
    "durables": dict(n=51, occurrences=154, terminal=sorted(
        [f"{s}:{f}_nxt_{t} → bequest:{f}_bq" for s, t in (("adjuster_cons", "adj"), ("keeper_cons", "kp"))
         for f in "ahz"]) + TENURE_WITHIN, layers=[["tenure"], ["adjuster_cons", "keeper_cons"], ["bequest"]],
        within=TENURE_WITHIN, outputs=["adjuster_cons:a_nxt_adj", "adjuster_cons:h_nxt_adj", "adjuster_cons:z_nxt_adj",
                                       "keeper_cons:a_nxt_kp", "keeper_cons:h_nxt_kp", "keeper_cons:z_nxt_kp"],
        later=[["tenure"], ["adjuster_cons", "keeper_cons"]],
        inter=[f"{s}:{f}_nxt_{t} → tenure:{f}" for s, t in (("keeper_cons", "kp"), ("adjuster_cons", "adj")) for f in "ahz"]),
    "retirement-choice": dict(n=20, occurrences=61,
        terminal=RET_WITHIN + ["retiree_cons:b_ret → bequest:a_bq", "worker_cons:b → bequest:a_bq"],
        layers=[["ret_choice"], ["retiree_cons", "worker_cons"], ["bequest"]],
        within=RET_WITHIN, outputs=["retiree_cons:b_ret", "worker_cons:b"],
        later=[["ret_choice"], ["retiree_cons", "worker_cons"]],
        inter=["worker_cons:b → ret_choice:a", "retiree_cons:b_ret → retiree_cons:a_ret"]),
    "pension-retirement": dict(n=15, occurrences=46,
        terminal=[f"retire_choice:y_{a}_{b} → terminal:y_{a}_T" for a, b in (("f", "rt"), ("f", "wk"), ("p", "rt"), ("p", "wk"))]
        + ["retiree_saving:y_f_ret → terminal:y_f_T", "retiree_saving:y_p_ret → terminal:y_p_T"] + PENSION_WITHIN,
        layers=[["retiree_saving", "worker_saving"], ["retire_choice"], ["terminal"]],
        within=PENSION_WITHIN, outputs=["retire_choice:y_f_rt", "retire_choice:y_f_wk", "retire_choice:y_p_rt",
                                        "retire_choice:y_p_wk", "retiree_saving:y_f_ret", "retiree_saving:y_p_ret"],
        later=[["retiree_saving", "worker_saving"], ["retire_choice"]],
        inter=["retire_choice:y_f_wk → worker_saving:y_f_w", "retire_choice:y_p_wk → worker_saving:y_p_w",
               "retire_choice:y_f_rt → retiree_saving:y_f_r", "retire_choice:y_p_rt → retiree_saving:y_p_r",
               "retiree_saving:y_f_ret → retiree_saving:y_f_r", "retiree_saving:y_p_ret → retiree_saving:y_p_r"]),
    "housing-frictions": dict(n=60, occurrences=181, terminal=sorted(
        [f"{s}:y_{f}_{t} → terminal:y_{f}_T" for s, t in (("adjuster_saving", "adj"), ("keeper_saving", "kp")) for f in "fh"]
        + HOUSE_WITHIN), layers=[["house_choice"], ["adjuster_saving", "keeper_saving"], ["terminal"]],
        within=HOUSE_WITHIN, outputs=["adjuster_saving:y_f_adj", "adjuster_saving:y_h_adj",
                                      "keeper_saving:y_f_kp", "keeper_saving:y_h_kp"],
        later=[["house_choice"], ["adjuster_saving", "keeper_saving"]],
        inter=["keeper_saving:y_f_kp → house_choice:y_f", "keeper_saving:y_h_kp → house_choice:y_h",
               "adjuster_saving:y_f_adj → house_choice:y_f", "adjuster_saving:y_h_adj → house_choice:y_h"]),
}


def whole_trellis(key):
    """The trellis of one registry by its route (E36): durables with the wage
    schedule written between the load and the verbs; retirement through the
    calibration and the methods, the worker's endogenous grid entry binding at
    the Evaluation that closes its policy block, which writes the grid line
    `w[>] = b + c[>]` (lane K of the internal developer release 0.01; the entry
    was refused before); pension with its fill; housing by
    `assemble_trellis`."""
    if key == "durables":
        with pytest.raises(ValueError, match="'Y'"):
            assemble_trellis(DURABLES, "spec.yml")
        syntactic = wage_schedule()(load_recipe(DURABLES, "spec.yml"))
        return configure_trellis(methodize_trellis(calibrate_trellis(
            elaborate_trellis(syntactic), syntactic), syntactic), syntactic)
    if key == "retirement-choice":
        syntactic = load_recipe(RETIREMENT, "spec.yml")
        methodized = methodize_trellis(calibrate_trellis(elaborate_trellis(syntactic), syntactic), syntactic)
        worker = methodized["periods"][0]["stages"]["worker_cons"]
        assert [(str(place), method.handler) for place, method in worker.methods.items()
                if method.tag == "egm"] == [("policy:Evaluation", "asva:make_egm_1d")]
        return methodized
    if key == "pension-retirement":
        return assemble_trellis(PENSION, "spec.yml", fill=PENSION_FILL)
    return assemble_trellis(HOUSING, "spec.yml")


# each registry elaborated as a whole trellis of fifteen to sixty periods: one
# of the sweeps
@pytest.mark.sweep
@pytest.mark.parametrize("key", list(WHOLE))
def test_item_4_each_registry_elaborates_as_a_whole_trellis_with_its_joins(key):
    expected = WHOLE[key]
    trellis = whole_trellis(key)
    periods, mappings = trellis["periods"], trellis["inter_connectors"]
    assert (len(periods), len(positions(trellis))) == (expected["n"], expected["occurrences"])
    terminal = period_joins(periods[0])
    assert [arrow(join) for join in terminal["joins"]] == expected["terminal"] and terminal["outputs"] == []
    assert computable_together(periods[0]) == expected["layers"]
    for h in range(1, expected["n"]):
        within = period_joins(periods[h])
        assert [arrow(join) for join in within["joins"]] == expected["within"]
        assert [f"{k}:{f}" for k, f in within["outputs"]] == expected["outputs"]
        assert computable_together(periods[h]) == expected["later"]
        assert [arrow(join) for join in inter_period_joins(mappings[h - 1], periods[h], periods[h - 1])] == expected["inter"]
    # E16: every continuation state field of every occurrence joins exactly one arrival field,
    # within its period or across its pair (561 for durables, examples/durables/expected.md §6)
    sources = Counter((h, join["from"]) for h in range(expected["n"]) for join in period_joins(periods[h])["joins"])
    sources += Counter((h + 1, join["from"]) for h in range(expected["n"] - 1)
                       for join in inter_period_joins(mappings[h], periods[h + 1], periods[h]))
    continuations = sum(1 for period in periods for stage in period["stages"].values()
                        for sort in fields(stage).values() if sort.perch == "cntn" and sort.role == "state")
    assert set(sources.values()) == {1} and len(sources) == continuations
