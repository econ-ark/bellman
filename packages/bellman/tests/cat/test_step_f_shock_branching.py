"""The acceptance file of the second build of branching, step F, a branch a
shock selects (the second layer of the tests, `packages/bellman/README.md`
§8): items 1 to 5 of `runs/2026-09-23-branching/second-build/plan.md`;
item 6 is AAS's reading of notebook 11. Deleted when the next amendment is
accepted."""
import copy
import hashlib
import json
import re
from collections import Counter

import pytest

from bellman.native.hypergraphs import copy_native

from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import assemble_trellis, elaborate_trellis, load_recipe
from bellman.factory.trellis import positions
from bellman.display.encoding_checks import validate_encoding
from bellman.factory.joins import computable_together, inter_period_joins, period_joins
from bellman.stage.stage_answers import branches, combination, kind
from bellman.stage.stage_answers import fields
from bellman.refusals import NotConstructed
from conftest import (CHILDBEARING, CHILDBEARING_FILL, ENTREPRENEUR_STANDINS, PRELIMINARY, ROOT, drawn_card, flat,
                      rules, section)
from sheets_parse import operations_entries

# the examples and the Cagetti registry of the branching run of 23 September 2026 that the tests read,
# copied into the corpus; the cards of the examples' fenced blocks that the package prints are printed
# by it, in the card's form of the internal developer release 0.01
RUN = ROOT / PRELIMINARY / "branching"
CAGETTI_EXAMPLE = RUN / "examples/cagetti-denardi-2006/expected.md"
# each file's branches with the fields its nested blocks write, and the definition of its law
# (examples/cagetti-denardi-2006/expected.md §3; examples/de-la-croix-pommeret-2021/expected.md §3.3)
BRANCHES = {
    "retiree_death": ({"survive": ("a_rd_rt",), "die": ("a_rd_yc", "y_rd_yc", "θ_rd_yc")},
                      "(a,y,θ,s)↦(a,(a,y,θ))[s]"),
    "worker_ageing": ({"young": ("a_wa_yc", "y_wa_yc", "θ_wa_yc"), "old": ("a_wa_rt",)},
                      "(a,y,θ,s)↦((a,y,θ),a)[s]"),
    "entrepreneur_death": ({"survive": ("a_ed_oc", "θ_ed_oc"), "die": ("a_ed_yc", "y_ed_yc", "θ_ed_yc")},
                           "(a,y,θ,s)↦((a,θ),(a,y,θ))[s]"),
    "entrepreneur_ageing": ({"young": ("a_ea_yc", "y_ea_yc", "θ_ea_yc"), "old": ("a_ea_oc", "θ_ea_oc")},
                            "(a,y,θ,s)↦((a,y,θ),(a,θ))[s]"),
    "fecundity": ({"mother": ("a_mth",), "childless": ("a_chl",)}, "(a_fecd,age_fecd,s)↦(a_fecd,a_fecd)[s]"),
}


@pytest.mark.parametrize("name", list(BRANCHES))
def test_item_1_each_file_constructs_a_stage_whose_branches_the_shock_s_selects(name, request):
    stage = request.getfixturevalue(name)
    held, law = BRANCHES[name]
    assert (kind(stage), combination(stage)) == ("branching", "expectation")
    assert {label: tuple(i.field for i in fields) for label, fields in branches(stage).items()} == held
    # E4: the label shock is the last argument of the law of motion although no line reads it
    record = stage.definitions[f"{name}:g:dcsn_to_cntn"]
    assert [n for n, _ in record.coordinates][-1] == "s"
    assert law in flat(str(stage.definitions.denote(f"{name}:g:dcsn_to_cntn")))
    # E34: `s` is a wire of the forward block that draws it and of no backward block
    listed = lambda handle: [line.split()[1] for line in str(handle.signature()).splitlines() if line.startswith("in")]
    assert "s" in listed(stage.initial.forward["dcsn_to_cntn"])
    assert "s" not in listed(stage.initial.backward["cntn_to_dcsn"])
    if name == "retiree_death":
        # the reader validates the document against the package's one schema
        # (decision S3 of the structure review's cleanup)
        validate_encoding(json.loads(json.dumps(stage.encoding())))


# the hand derivation's values of β, η and π_o; the five other parameters take values in their
# declared sets, which no line of the decision builder reads
HAND = {"β": 0.95, "η": 0.5, "π_o": 0.9, "P_y": 0.5, "y_grid": 1.0, "ρ_θ0": 0.9, "ρ_θ1": 0.8, "θ_e": 1.0}


def differences(builder, drawn):
    """The sections in which a printed card differs from the one the example
    shows, compared as the first build's item 2 compares (P10): the keys of
    the operations, the signature as a set of flattened lines, the five other
    sections flattened, the rules of the operations joined; `[]` where none
    differs."""
    card = str(builder)
    keys = [m.group(1) for line in section(drawn, "Operations")
            for m in [re.match(r"^\s+\d+\s+(\S+)$", line)] if m]
    found = [] if [str(key) for key in builder.primitives.list()] == keys else ["keys"]
    if {flat(line) for line in section(card, "Signature")[1:]} != {flat(line) for line in section(drawn, "Signature")[1:]}:
        found.append("signature")
    found += [heading for heading in ("At", "Where", "Conditions", "Source", "Definitions referenced")
              if flat("\n".join(section(card, heading))) != flat("\n".join(section(drawn, heading)))]
    return found + ([] if rules(section(card, "Operations")) == rules(section(drawn, "Operations")) else ["rules"])


def test_item_2_the_decision_builder_of_retiree_death_prints_the_hand_derivation(retiree_death):
    decision = retiree_death.builder.bwd["cntn_to_dcsn"]
    assert differences(decision, drawn_card(CAGETTI_EXAMPLE, "STAGE retiree_death / BACKWARD BUILDER cntn_to_dcsn")) == []
    # the aggregator's definition states the weighted case operation with the law's weights (E13)
    assert "↦β·(π_o·W_r≻+(1−π_o)·(η·V_young≻))" in flat(str(retiree_death.definitions.denote("retiree_death:G:cntn_to_dcsn")))
    # the law as the file writes it (P31)
    assert "s~Categorical(π_o,1−π_o)" in flat(str(retiree_death.definitions.denote("retiree_death:distribution:s")))
    # the arrival builder integrates the offspring's abilities: with the decision card, the derivation's step 5
    assert flat("𝑉≺(a_rd) = E_{y_n, θ_n}[𝑉(𝑔≺(a_rd, y_n, θ_n))]") in rules(
        section(str(retiree_death.builder.bwd["dcsn_to_arvl"]), "Operations"))
    # the compiled aggregation at the derivation's point: 0.95 · (0.9 · 3 + 0.1 · 0.5 · 7) = 2.8975
    aggregation = copy_native(retiree_death).calibrate(HAND).builder.bwd["cntn_to_dcsn"].primitives["Aggregation"]
    G, values = aggregation.compile_kernel(), aggregation.kernel().parameter_values
    assert G(3.0, 7.0, 1.0, 1.0, 1.0, *values) == pytest.approx(0.95 * (0.9 * 3.0 + 0.1 * 0.5 * 7.0))


def test_item_3_the_forward_builder_of_a_draw_extends_the_measure_by_the_law_and_routes_by_the_label(
        worker_ageing, retiree_death):
    forward = worker_ageing.builder.fwd["dcsn_to_cntn"]
    assert [str(key) for key in forward.primitives.list()] == ["DistributionExtension:s", "Pushforward"]
    assert differences(forward, drawn_card(CAGETTI_EXAMPLE, "STAGE worker_ageing / FORWARD BUILDER dcsn_to_cntn")) == []
    # retiree_death draws the offspring's abilities with the family `Invariant`, which the package does
    # not admit, so its forward builders are refused (P32); its conservation waits on the law of s
    with pytest.raises(NotConstructed, match="'Invariant'"):
        retiree_death.builder.fwd["dcsn_to_cntn"]
    held = [item for item in retiree_death.obligations() if item.condition == "mass-conservation"]
    assert [item.status for item in held] == ["required"]
    assert "retiree_death:distribution:s" in [str(subject) for subject in held[0].named_identities]


CHILDBEARING_EXAMPLE = RUN / "examples/de-la-croix-pommeret-2021/expected.md"
TITLE = {"backward/cntn_to_dcsn": "BACKWARD BUILDER cntn_to_dcsn", "forward/dcsn_to_cntn": "FORWARD BUILDER dcsn_to_cntn",
         "backward/policy": "POLICY BUILDER policy"}


def arrow(join):
    return f"{join['from'][0]}:{join['from'][1]} → {join['to'][0]}:{join['to'][1]}"


# the joins, outputs and layers of examples/de-la-croix-pommeret-2021/expected.md §6
WITHIN = ["attempt:a_try → fecundity:a_fec", "attempt:age_try → fecundity:age_fec",
          "cons_wait:age_c → attempt:age_att", "cons_wait:b_wait → attempt:a_att",
          "fecundity:a_chl → cons_childless:a_childless", "fecundity:a_mth → cons_mother:a_mother"]
TERMINAL = sorted(WITHIN + ["attempt:a_next → terminal_wait:a_tw", "attempt:age_next → terminal_wait:age_tw",
                            "cons_childless:b_childless → terminal_childless:a_tc",
                            "cons_mother:b_mother → terminal_mother:a_tm"])
INTER = ["attempt:a_next → cons_wait:a_wait", "attempt:age_next → cons_wait:age",
         "cons_mother:b_mother → cons_mother:a_mother", "cons_childless:b_childless → cons_childless:a_childless"]
OUTPUTS = [("attempt", "a_next"), ("attempt", "age_next"), ("cons_childless", "b_childless"), ("cons_mother", "b_mother")]
# the terminal period's outputs, the boundary data of the three routes (P35)
OUTPUTS_0 = [("terminal_childless", "b_tc"), ("terminal_mother", "b_tm"), ("terminal_wait", "age_twc"),
             ("terminal_wait", "b_tw")]
LAYERS = [["cons_wait"], ["attempt"], ["fecundity"], ["cons_childless", "cons_mother"]]
LAYERS_0 = [["cons_wait"], ["attempt"], ["fecundity", "terminal_wait"], ["cons_childless", "cons_mother"],
            ["terminal_childless", "terminal_mother"]]
# the rules of the Aggregation of fecundity's decision card under E13, the row that the drawing on
# paper of 23 September drew as `[open: E13]` (P36)
FECUNDITY_RULES = ("𝑉 "
                   "= E_{s}[(𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd)) + ω, "
                   "𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd)))[s]] "
                   "on (a_fecd, age_fecd) ∈ Xa × Xt "
                   "𝑑𝑉 "
                   "= E_{s}[(𝑑𝑉_mth≻(𝑔_mother≻(a_fecd, age_fecd)), "
                   "𝑑𝑉_chl≻(𝑔_childless≻(a_fecd, age_fecd)))[s]] "
                   "on (a_fecd, age_fecd) ∈ Xa × Xt")
FECUNDITY_CASE = ("(𝜋(age_fecd) · (V_mth≻ + ω) + (1 − 𝜋(age_fecd)) · V_chl≻, "
                  "𝜋(age_fecd) · dV_mth≻ + (1 − 𝜋(age_fecd)) · dV_chl≻)")


# the registry elaborated as a whole trellis of 36 periods: one of the sweeps
@pytest.mark.sweep
def test_item_4_the_childbearing_registry_elaborates_as_a_whole_trellis_with_its_joins_and_cards():
    with pytest.raises(ValueError, match="'ω'"):
        assemble_trellis(CHILDBEARING, "spec.yml")
    trellis = assemble_trellis(CHILDBEARING, "spec.yml", fill=CHILDBEARING_FILL)
    periods, mappings = trellis["periods"], trellis["inter_connectors"]
    assert (len(periods), len(mappings), len(positions(trellis))) == (36, 35, 183)
    terminal = period_joins(periods[0])
    assert [arrow(join) for join in terminal["joins"]] == TERMINAL and terminal["outputs"] == OUTPUTS_0
    assert computable_together(periods[0]) == LAYERS_0
    for h in range(1, 36):
        within = period_joins(periods[h])
        assert [arrow(join) for join in within["joins"]] == WITHIN and within["outputs"] == OUTPUTS
        assert computable_together(periods[h]) == LAYERS
        assert [arrow(join) for join in inter_period_joins(mappings[h - 1], periods[h], periods[h - 1])] == INTER
    # E16: every continuation state field joins one arrival field, but the four of the terminal stages
    sources = Counter((h, join["from"]) for h in range(36) for join in period_joins(periods[h])["joins"])
    sources += Counter((h + 1, join["from"]) for h in range(35)
                       for join in inter_period_joins(mappings[h], periods[h + 1], periods[h]))
    continuations = sum(1 for period in periods for stage in period["stages"].values()
                        for sort in fields(stage).values() if sort.perch == "cntn" and sort.role == "state")
    assert set(sources.values()) == {1} and len(sources) == continuations - len(OUTPUTS_0)
    # the five branching cards (examples/de-la-croix-pommeret-2021/expected.md §§2.4, 3.4)
    stages = {name: elaborate_stage(load_stage(CHILDBEARING / "stages" / f"{name}.bl")) for name in ("attempt", "fecundity")}
    for name, key in (("attempt", "backward/cntn_to_dcsn"), ("attempt", "forward/dcsn_to_cntn"),
                      ("attempt", "backward/policy"), ("fecundity", "forward/dcsn_to_cntn")):
        direction, builder = key.split("/")
        graph = {"backward": stages[name].builder.bwd, "forward": stages[name].builder.fwd}[direction]
        assert differences(graph[builder],
                           drawn_card(CHILDBEARING_EXAMPLE, f"STAGE {name} / {TITLE[key]}")) == [], (name, key)
    # the decision card of fecundity: the signature, `Where` and `Source` the example shows; the rules E13
    # prints at the Aggregation; the aggregator's definition the weighted sum the example wrote
    decision = stages["fecundity"].builder.bwd["cntn_to_dcsn"]
    card, drawn = str(decision), drawn_card(CHILDBEARING_EXAMPLE, "STAGE fecundity / BACKWARD BUILDER cntn_to_dcsn")
    assert [str(key) for key in decision.primitives.list()] == ["Pullback:mother", "Pullback:childless", "Aggregation", "Evaluation"]
    assert {flat(line) for line in section(card, "Signature")[1:]} == {flat(line) for line in section(drawn, "Signature")[1:]}
    for heading in ("Where", "Source"):
        assert flat("\n".join(section(card, heading))) == flat("\n".join(section(drawn, heading))), heading
    [aggregation] = [entry for entry in operations_entries(section(card, "Operations")[1:])
                     if entry["key"] == "Aggregation"]
    assert flat("\n".join(aggregation["rule"])) == flat(FECUNDITY_RULES)
    assert flat(FECUNDITY_CASE) in flat(str(stages["fecundity"].definitions.denote("fecundity:G:cntn_to_dcsn")))


EXAMPLE = CAGETTI_EXAMPLE.read_text(encoding="utf-8").splitlines()
# the two forward cards the family `Invariant` of the arrival shocks refuses (P32)
REFUSED_CARDS = {"STAGE entrepreneur_death / FORWARD BUILDER dcsn_to_cntn",
                 "STAGE retiree_death / FORWARD BUILDER dcsn_to_cntn"}


@pytest.mark.parametrize("name", ["young_choice", "old_choice", "entrepreneur_death", "retiree_death",
                                  "worker_ageing", "entrepreneur_ageing"])
def test_item_5_the_cards_of_the_six_cagetti_stages_state_what_the_example_draws(name, request):
    stage = request.getfixturevalue(name)
    titles = [line for line in EXAMPLE if line.startswith(f"STAGE {name} / ")]
    assert len(titles) == (3 if name.endswith("_choice") else 2)
    for title in titles:
        word, builder = title.split(" / ")[1].split(" BUILDER ")
        graph = stage.builder.fwd if word == "FORWARD" else stage.builder.bwd
        if title in REFUSED_CARDS:
            with pytest.raises(NotConstructed, match="'Invariant'"):
                graph[builder]
            continue
        assert differences(graph[builder], drawn_card(CAGETTI_EXAMPLE, title)) == [], title


CAGETTI_REGISTRY = RUN / "examples/cagetti-denardi-2006/registry"
# the arrival fields several branch fields join, with the number of their sources
# (examples/cagetti-denardi-2006/expected.md §6; probes/p04_registry.out)
SOURCES = {"young_choice:a_yc": 4, "young_choice:y_yc": 4, "young_choice:θ_yc": 4, "retiree:a_rt": 4,
           "old_choice:a_oc": 2, "old_choice:θ_oc": 2, "worker:a_wk": 2, "worker:y_wk": 2, "worker:θ_wk": 2}


def test_item_5_a_cagetti_period_joins_its_branch_fields_with_the_entrepreneurs_stood_in():
    syntactic = copy.deepcopy(load_recipe(CAGETTI_REGISTRY, "spec.yml"))
    for period in syntactic["periods"]:
        for key, text in ENTREPRENEUR_STANDINS.items():
            record = period["stages"][key]
            record["stage"] = {"text": text, "origin": f"standin:{key}"}
            # a stand-in text replaces the stage and takes no addition of the stage it replaces
            record["methods"] = []
            record["provenance"] = {**record["provenance"], "origin": f"standin:{key}",
                                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    found = [period_joins(period) for period in elaborate_trellis(syntactic)["periods"]]
    assert [(len(joins["joins"]), len(joins["outputs"])) for joins in found] == [(40, 0), (31, 9), (31, 9)]
    for joins in found:
        # E16: four sources at each arrival field of the young's choice and at the retiree's
        counted = Counter(f"{join['to'][0]}:{join['to'][1]}" for join in joins["joins"])
        assert {target: n for target, n in counted.items() if n > 1} == SOURCES
