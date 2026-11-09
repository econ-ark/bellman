"""The acceptance file of AMD-FAC-002 (the second layer of the tests,
`packages/bellman/README.md` §8): one test per item of its §9, on the
durables registry of §5 and the corpus stages. Deleted when the next
amendment is accepted; the laws L1 to L3 live in the behaviour file and the
refusals in the refusal file. The codes R3 to R23 and A2 onward are the
rulings and assumptions of the amendment's decisions record; F04 and F16
are units of AMD-FAC-002 §8. The last test is item 1 of §3 of the brief on
the trellis view's load time,
`trellis-load-time.md`, which adds
`specify_trellis` to the calls of AMD-FAC-002 §2."""
import hashlib
import re
from pathlib import Path

import pytest
import yaml

import bellman.factory.trellis as trellis_module
from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import (
    accrete,
    assemble_trellis,
    calibrate_trellis,
    changed_positions,
    configure_trellis,
    elaborate_trellis,
    load_recipe,
    load_trellis,
    methodize_trellis,
    specify_trellis,
)
from bellman.refusal_catalogue import catalogue
from bellman.factory.trellis import copy_trellis, positions
from bellman.factory.joins import forward_order, period_joins
from bellman.stage.kernels import compile_kernel, kernel
from bellman.stage.method_table import attached_methods
from bellman.refusals import FACTORY_RULES, FactoryError
from conftest import (DISC_TEXT, DURABLES, PENSION, RETIREMENT, ROOT, TWO_STAGES, apart_from_the_address,
                      graphs_differ)

# the terminal period's connector of the two-stage durables trellis, from both continuation sets to the
# bequest's arrival fields a_bq, h_bq and z_bq (E15 of the first build of branching, step F)
TO_BEQUEST = {"a_nxt_kp": "a_bq", "h_nxt_kp": "h_bq", "z_nxt_kp": "z_bq",
              "a_nxt_adj": "a_bq", "h_nxt_adj": "h_bq", "z_nxt_adj": "z_bq"}


def compared(trellis):
    """The fields of A54 of a syntactic trellis: each record's `stage`,
    `calibration`, `settings` and `methods`, each period's connectors and the
    inter-period mappings; the top-level `registry` and `provenance` and each
    record's `provenance` describe the route and are left out."""
    return {"periods": [{"stages": {key: {name: record[name] for name in ("stage", "calibration", "settings", "methods")}
                                    for key, record in period["stages"].items()},
                         "connectors": period["connectors"]} for period in trellis["periods"]],
            "inter_connectors": trellis["inter_connectors"]}


def test_item_1_load_recipe_returns_the_syntactic_trellis_and_load_trellis_returns_the_same_up_to_the_source_lists(tmp_path):
    syntactic = load_recipe(DURABLES, "spec.yml")
    assert len(syntactic["periods"]) == 51 and len(syntactic["inter_connectors"]) == 50
    assert list(syntactic["periods"][0]["stages"]) == ["tenure", "keeper_cons", "adjuster_cons", "bequest"]
    assert list(syntactic["periods"][1]["stages"]) == ["tenure", "keeper_cons", "adjuster_cons"]
    record = syntactic["periods"][0]["stages"]["adjuster_cons"]
    assert record["stage"]["origin"] == str(DURABLES / "stages/adjuster_cons/adjuster_cons.bl")
    assert {name: record["calibration"][name] for name in ("β", "α", "γ_c", "γ_h", "κ", "τ")} == {
        "β": 0.945, "α": 0.7, "γ_c": 3.5, "γ_h": 1.5, "κ": 0.06, "τ": 0.12}
    assert record["settings"]["n_a"] == 300
    entry = record["methods"]["methods"][0]
    assert (entry["on"], entry["handler"]) == ("policy", "fues-durables:make_adjuster_ops")
    lists = record["provenance"]["source_lists"]
    assert [item.get("source", item.get("slot")) for item in lists["calibration"]] == ["calibration/durables", "fill"]
    assert lists["calibration"][0]["sha256"] == hashlib.sha256((DURABLES / "calibration/durables.yml").read_bytes()).hexdigest()
    assert lists["calibration"][1] == {"slot": "fill", "bound": False, "names": []}
    assert record["provenance"]["sha256"] == hashlib.sha256(record["stage"]["text"].encode("utf-8")).hexdigest()
    assert set(syntactic["registry"]["calibration"]) == {
        "wage_coefficients", "tenure_cap", "tenure_origin", "earnings_scale", "retirement_income",
        "first_age", "retirement_age", "last_age"}
    # the two-stage model written out by hand from the registry's files: each record names its stage
    # file and its mappings as the registry's own files, the bequest with its calibration and its methods
    # file, which binds the marginal blocks of its derivatives (decision MB-U7), the
    # fifty equal periods as one template repeated; the two loaders agree on the fields of A54
    stages = {key: {"stage": str(DURABLES / f"stages/{key}/{key}.bl"), "calibration": str(DURABLES / "calibration/durables.yml"),
                    "settings": str(DURABLES / "settings/durables.yml"), "methods": str(DURABLES / f"stages/{key}/methods.yml")}
              for key in ("keeper_cons", "adjuster_cons")}
    bequest = {"stage": str(DURABLES / "stages/bequest/bequest.bl"), "calibration": str(DURABLES / "calibration/durables.yml"),
               "methods": str(DURABLES / "stages/bequest/methods.yml")}
    (tmp_path / "period-two-stages-written.yml").write_text(
        yaml.safe_dump({"stages": stages, "connectors": []}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    written = {"periods": [{"stages": {**stages, "bequest": bequest}, "connectors": [TO_BEQUEST]},
                           {"template": "period-two-stages-written.yml", "repeat": 50}],
               "inter_connectors": []}
    file = tmp_path / "trellis-two-stages-written.yml"
    file.write_text(yaml.safe_dump(written, allow_unicode=True, sort_keys=False), encoding="utf-8")
    assert compared(load_trellis(file)) == compared(load_recipe(DURABLES, TWO_STAGES))
    # the round trip: the records the recipe wrote, written out with their mappings inline, read back equal
    inline = {"periods": [{"stages": {key: {"stage": record["stage"]["origin"], "calibration": record["calibration"],
                                            "settings": record["settings"], "methods": record["methods"]}
                                      for key, record in period["stages"].items()},
                           "connectors": period["connectors"]} for period in syntactic["periods"]],
              "inter_connectors": syntactic["inter_connectors"]}
    (tmp_path / "trellis-written.yml").write_text(yaml.safe_dump(inline, allow_unicode=True, sort_keys=False), encoding="utf-8")
    assert compared(load_trellis(tmp_path / "trellis-written.yml")) == compared(syntactic)


# items 2 to 4 each elaborate the two-stage durables trellis whole, 103
# positions over 51 periods: they are among the sweeps
@pytest.mark.sweep
def test_item_2_elaborate_trellis_places_full_symbolic_copies_the_order_follows_the_fields_and_a_planted_cycle_is_refused(cons, text_of, path_of, monkeypatch):
    constructions, construct = [], trellis_module.construct_stage
    monkeypatch.setattr(trellis_module, "construct_stage", lambda text, origin, additions=(): constructions.append(origin) or construct(text, origin, additions))
    elaborated = elaborate_trellis(load_recipe(DURABLES, TWO_STAGES))
    assert len(elaborated["periods"]) == 51 and len(positions(elaborated)) == 103
    # three constructions, one per distinct stage text, for the 103 positions
    assert sorted(Path(origin).name for origin in constructions) == ["adjuster_cons.bl", "bequest.bl", "keeper_cons.bl"]
    terminal = elaborated["periods"][0]["stages"]
    for h, key, _, stage in positions(elaborated):
        assert repr(stage) == f"ElaboratedStage({key!r}, symbolic)"
        assert dict(stage.provenance["position"]) == {"h": h, "key": key}
        assert h == 0 or stage is not terminal[key]
        assert graphs_differ(stage, terminal[key]) == []
        assert apart_from_the_address(stage.definitions) == apart_from_the_address(terminal[key].definitions)
        assert stage.bindings == terminal[key].bindings
    # the portfolio period of docs/Bellman-Sym/06-period.md: port.bl continues to m_next (R3, step D)
    # the joins and the order are the same under the template [cons, disc, port] and its reverse
    port_next = elaborate_stage(load_stage(path_of("port")))
    disc = elaborate_stage({"stage": {"text": DISC_TEXT, "origin": "disc.bl"}, "calibration": {}, "settings": {}, "methods": {}})
    listed = {"stages": {"cons": cons, "disc": disc, "port": port_next}, "connectors": [{"k_next": "k"}]}
    reversed_listing = {"stages": {"port": port_next, "disc": disc, "cons": cons}, "connectors": [{"k_next": "k"}]}
    assert period_joins(listed) == period_joins(reversed_listing)
    assert period_joins(listed)["joins"] == [{"from": ("cons", "a"), "to": ("disc", "a")}, {"from": ("disc", "k_next"), "to": ("port", "k")}]
    assert forward_order(listed) == forward_order(reversed_listing) == ["cons", "disc", "port"]
    # the planted cycles, each under both list orders: a copy of port.bl continuing to m, where cons
    # arrives; with the connector {a: k} the two stages close a cycle through the inferred pair port.m → cons.m,
    # and with disc between them a cycle of three through two inferred pairs. Since AMD-COMP-001 §3 an inferred
    # pair on a cycle of the selected pairs is withdrawn and recorded as rejected, the authored pairs stand and
    # the trellis is admitted: a cycle refuses the reading only where authored pairs alone close it
    from bellman.trellis import connection_report
    cons_record = load_stage(path_of("cons"))
    port_record = {"stage": {"text": text_of("port").replace("m_next", "m"), "origin": "port.bl"},
                   "calibration": {}, "settings": {}, "methods": {}}
    for stages in ({"cons": cons_record, "port": port_record}, {"port": port_record, "cons": cons_record}):
        two = elaborate_trellis({"periods": [{"stages": stages, "connectors": [{"a": "k"}]}], "inter_connectors": []})
        report = connection_report(two)
        assert [(str(p.writing), str(p.reading)) for p in report.pairs] == [("periods[0].cons.a", "periods[0].port.k")]
        assert [(str(r.writing), str(r.reading), r.rule) for r in report.selection.rejected] == [
            ("periods[0].port.m", "periods[0].cons.m", "inference-cycle")]
        assert forward_order(two["periods"][0], "periods[0]") == ["cons", "port"]
    port = elaborate_stage(port_record)
    for stages in ({"cons": cons, "disc": disc, "port": port}, {"port": port, "disc": disc, "cons": cons}):
        three = {"stages": stages, "connectors": [{"k_next": "k"}]}
        assert period_joins(three, "periods[0]")["joins"] == [{"from": ("disc", "k_next"), "to": ("port", "k")}]
        assert forward_order(three, "periods[0]") == ["cons", "disc", "port"]
        rejected = connection_report(elaborate_trellis({"periods": [three], "inter_connectors": []})).selection.rejected
        assert sorted((str(r.writing), str(r.reading), r.rule) for r in rejected) == [
            ("periods[0].cons.a", "periods[0].disc.a", "inference-cycle"),
            ("periods[0].port.m", "periods[0].cons.m", "inference-cycle")]
    # two authored pairs in opposite directions close a cycle no withdrawal opens: refused, each pair named
    with pytest.raises(FactoryError) as refused:
        forward_order({"stages": {"cons": cons, "port": port}, "connectors": [{"a": "k"}, {"m": "m"}]}, "periods[0]")
    assert (refused.value.rule, refused.value.address) == ("period-join-cycle", "periods[0]")
    assert all(word in refused.value.message for word in (
        "cons continues to 'a'", "port arrives at 'k'", "port continues to 'm'", "cons arrives at 'm'"))
    assert "_next" in refused.value.write


@pytest.mark.sweep
def test_item_3_the_verbs_bind_where_the_mapping_differs_copy_elsewhere_and_a_fill_binds_again_only_the_stages_declaring_it():
    syntactic = load_recipe(DURABLES, TWO_STAGES)
    elaborated = elaborate_trellis(syntactic)
    calibrated = calibrate_trellis(elaborated, syntactic)
    assert len(changed_positions(elaborated, calibrated)) == 103                     # 51 keeper_cons, 51 adjuster_cons, 1 bequest
    methodized = methodize_trellis(calibrated, syntactic)
    model = configure_trellis(methodized, syntactic)
    assert len(changed_positions(calibrated, methodized)) == 103 and len(changed_positions(methodized, model)) == 103
    assert all(repr(stage) == f"ElaboratedStage({key!r}, specified)" for _, key, _, stage in positions(model))
    snapshot = copy_trellis(model)
    adjuster = model["periods"][0]["stages"]["adjuster_cons"]
    assert dict(adjuster.bindings.calibration) == {"β": 0.945, "α": 0.7, "γ_c": 3.5, "γ_h": 1.5, "κ": 0.06, "τ": 0.12}
    # the same mappings again: every verb copies every position
    assert changed_positions(model, calibrate_trellis(model, syntactic)) == []
    assert changed_positions(model, methodize_trellis(model, syntactic)) == []
    assert changed_positions(model, configure_trellis(model, syntactic)) == []
    # the aggregation kernel of the adjuster takes the inputs of its block in header order,
    # V[>], m, z_d, c and h_choice, then the parameters it reads; its value
    # is read with the values of the calibration before the fill and again
    # with those after it
    aggregation = compile_kernel(adjuster, "cntn_to_dcsn:Aggregation")
    values = kernel(adjuster, "cntn_to_dcsn:Aggregation").parameter_values
    before = float(aggregation(1.0, 1.0, 1.0, 0.5, 0.5, *values)[0])
    syntactic_b = load_recipe(DURABLES, TWO_STAGES, fill={"calibration": {"β": 0.93}, "settings": {"n_a": 500}})
    recalibrated = calibrate_trellis(model, syntactic_b)
    assert len(changed_positions(model, recalibrated)) == 102 and (0, "bequest") not in changed_positions(model, recalibrated)   # bequest declares no β
    model_b = configure_trellis(recalibrated, syntactic_b)
    assert len(changed_positions(recalibrated, model_b)) == 102                     # bequest has no settings list
    for (_, _, _, old), (_, _, _, new) in zip(positions(model), positions(model_b)):
        assert graphs_differ(old, new) == [] and old.definitions == new.definitions
    # a fill of τ binds again the adjuster alone, at every period; a fill of θ the bequest alone
    with_tau = calibrate_trellis(model, load_recipe(DURABLES, TWO_STAGES, fill={"τ": 0.2}))
    assert changed_positions(model, with_tau) == [(h, "adjuster_cons") for h in range(51)]
    with_theta = calibrate_trellis(model, load_recipe(DURABLES, TWO_STAGES, fill={"θ": 2.0}))
    assert changed_positions(model, with_theta) == [(0, "bequest")]
    assert adjuster.bindings.calibration["β"] == 0.945
    assert model_b["periods"][0]["stages"]["adjuster_cons"].bindings.calibration["β"] == 0.93
    assert model_b["periods"][0]["stages"]["bequest"] == model["periods"][0]["stages"]["bequest"]
    assert float(aggregation(1.0, 1.0, 1.0, 0.5, 0.5, *values)[0]) == before
    changed = kernel(model_b["periods"][0]["stages"]["adjuster_cons"], "cntn_to_dcsn:Aggregation")
    assert changed.python == kernel(adjuster, "cntn_to_dcsn:Aggregation").python
    after = float(aggregation(1.0, 1.0, 1.0, 0.5, 0.5, *changed.parameter_values)[0])
    assert after != before
    # a method choice through the adjuster's own slot (A55): the adjuster's positions are made anew with
    # their backward decision builder under !vfi, the one builder !vfi stands on, the keeper's copied with
    # its policy under !egm, which stores the policy at the Evaluation of a block that writes the grid line.
    # The recipe merges method entries on `on`, and no entry of stages/adjuster_cons/methods.yml
    # is on cntn_to_dcsn, so the choice adds to the file's entries and replaces none: the adjuster keeps the
    # file's !egm at its policy's Evaluation beside the !vfi on its backward decision builder. The same
    # choice given to assemble_trellis gives the same bindings and attachments at every position
    choice = {"methods": [{"on": "cntn_to_dcsn", "method": "!vfi", "handler": "fues-durables:make_adjuster_vfi"}]}
    switched = methodize_trellis(model, load_recipe(DURABLES, TWO_STAGES, adjuster_method=choice))
    assert changed_positions(model, switched) == [(h, "adjuster_cons") for h in range(51)]
    for h in range(51):
        keeper, adjuster_v = switched["periods"][h]["stages"]["keeper_cons"], switched["periods"][h]["stages"]["adjuster_cons"]
        assert [(str(box), method.tag) for box, method in attached_methods(keeper)
                if str(box).startswith("policy")] == [("policy:Evaluation", "egm")]
        assert [(str(box), method.tag, method.handler) for box, method in attached_methods(adjuster_v)
                if str(box) == "cntn_to_dcsn" or str(box).startswith("policy")] == [
            ("policy:Evaluation", "egm", "fues-durables:make_adjuster_ops"),
            ("cntn_to_dcsn", "vfi", "fues-durables:make_adjuster_vfi")]
        assert repr(adjuster_v) == "ElaboratedStage('adjuster_cons', specified)"
        assert dict(adjuster_v.bindings.calibration) == dict(model["periods"][h]["stages"]["adjuster_cons"].bindings.calibration)
    assembled = assemble_trellis(DURABLES, TWO_STAGES, adjuster_method=choice)
    for (_, _, _, made), (_, _, _, again) in zip(positions(switched), positions(assembled)):
        assert attached_methods(made) == attached_methods(again) and made.bindings == again.bindings
        assert graphs_differ(made, again) == []
    # the earlier trellis is unchanged at every position
    for (_, _, _, held), (_, _, _, kept) in zip(positions(model), positions(snapshot)):
        assert held == kept


@pytest.mark.sweep
def test_item_4_two_periods_accreted_by_hand_equal_the_assembled_ones_in_bindings_and_graphs():
    model = assemble_trellis(DURABLES, TWO_STAGES)
    calibration, settings = str(DURABLES / "calibration/durables.yml"), str(DURABLES / "settings/durables.yml")
    keeper = (elaborate_stage(load_stage(DURABLES / "stages/keeper_cons/keeper_cons.bl")).calibrate(calibration)
              .methodize(str(DURABLES / "stages/keeper_cons/methods.yml")).configure(settings))
    adjuster = (elaborate_stage(load_stage(DURABLES / "stages/adjuster_cons/adjuster_cons.bl")).calibrate(calibration)
                .methodize(str(DURABLES / "stages/adjuster_cons/methods.yml")).configure(settings))
    bequest = elaborate_stage(load_stage(DURABLES / "stages/bequest/bequest.bl")).calibrate(calibration).methodize({}).configure({})
    trellis = accrete({"periods": [], "inter_connectors": []},
                      {"stages": {"keeper_cons": keeper, "adjuster_cons": adjuster, "bequest": bequest}, "connectors": [TO_BEQUEST]})
    trellis = accrete(trellis, {"stages": {"keeper_cons": keeper, "adjuster_cons": adjuster}, "connectors": []}, {})
    assert len(trellis["periods"]) == 2 and trellis["inter_connectors"] == model["inter_connectors"][:1] == [{}]
    for h in (0, 1):
        assert set(trellis["periods"][h]["stages"]) == set(model["periods"][h]["stages"])
        assert trellis["periods"][h]["connectors"] == model["periods"][h]["connectors"]
        for key, by_hand in trellis["periods"][h]["stages"].items():
            assembled = model["periods"][h]["stages"][key]
            assert graphs_differ(by_hand, assembled) == []
            assert apart_from_the_address(by_hand.definitions) == apart_from_the_address(assembled.definitions)
            assert dict(by_hand.bindings.calibration) == dict(assembled.bindings.calibration)
            assert dict(by_hand.bindings.settings) == dict(assembled.bindings.settings)
            assert attached_methods(by_hand) == attached_methods(assembled)


def test_item_5_each_rule_of_the_factory_refuses_its_planted_case_with_the_four_parts():
    entries = {entry.rule: entry for entry in catalogue() if entry.vocabulary == "the Bellman factory"}
    assert list(entries) == list(FACTORY_RULES)
    for rule, entry in entries.items():
        assert entry.refusal and entry.where and entry.what and entry.why and entry.write, rule
        assert entry.refusal.endswith(f"(rule {rule})"), rule


# the removed names, swept over the code, the pages, the applications' prose and the notebooks
REMOVED = (re.compile(r"\bbellman\.elaborate\b(?!_)"), re.compile(r"\bupto\b"),
           re.compile(r"from bellman(\.\w+)? import[^\n]*\belaborate\b(?!_)"),
           re.compile(r"stage_factory\.load\("),
           re.compile(r"\bload_stage\([^)]*\)\.(calibrate|methodize|configure|fields|view|parameters|list)"))
# the retired terms, read in any case and with any spacing or hyphens between their words; a term inside a
# path segment, preceded by `/` or `-`, is a file name and not a use of the term
RETIRED = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"(?<![/\w-])specification[\s-]+functors?\b", r"(?<![/\w-])spec[\s-]+functors?\b",
    r"(?<![/\w-])resolved[\s-]+specification\b", r"(?<![/\w-])specgraph\b", r"(?<![/\w-])base[\s-]+trellis\b",
    r"\$draw\b"))
CODE = ("packages/bellman/**/*.py", "docs/_hooks/*.py", "tests/**/*.py", "docs/**/*.md", "applications/**/*.md",
        "applications/**/*.py", "**/*.ipynb")
# the pages the retired terms are swept over, the wiki's among them; the rule
# files and the specification are not read (PL13)
PROSE = ("docs/**/*.md",)
# the folders the sweep leaves out (A61): the internal folder AI, which holds the run records, the reference
# checkouts and AAS's working notebooks and which this sweep leaves out (PL13), the legacy folders and the environments;
# the decision records, which quote the retired terms as history (RH200), were left out as "decisions" while they
# stood under docs/decisions/, and since 29 September 2026 stand in the internal folder, which the sweep leaves out
EXCLUDED = ("AI", "legacy", "preliminary", ".ipynb_checkpoints", "venv", "node_modules", "site", ".git")


def _excluded(parts):
    return any(part in EXCLUDED for part in parts)


def _lines(patterns):
    """`(path, number, line)` of every line the sweep reads. A line inside a
    fenced ```text block is recorded output, kept verbatim, and is not read
    where the last prose line before the block carries "AMD-FAC-002" (A53)."""
    seen = set()
    for pattern in patterns:
        for path in sorted(ROOT.glob(pattern)):
            parts = path.relative_to(ROOT).parts
            if path in seen or _excluded(parts):
                continue
            seen.add(path)
            recorded, previous = False, ""
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if line.startswith("```"):
                    recorded = line.startswith("```text") and "AMD-FAC-002" in previous if not recorded else False
                    continue
                if line.strip():
                    previous = line
                if not recorded:
                    yield path.relative_to(ROOT), number, line


def test_item_6_the_removed_names_and_the_retired_terms_occur_nowhere_but_in_the_notes_f07_leaves():
    """The notebook of §11 is executed and inspected by AAS and the page of
    F12 is a later unit; this test covers the sweep alone. A line carrying
    the note `AMD-FAC-002` is a historical record and is admitted (A49)."""
    hits = [(path, number) for path, number, line in _lines(CODE)
            if any(pattern.search(line) for pattern in REMOVED) and "AMD-FAC-002" not in line]
    assert hits == []
    stale = [(path, number) for path, number, line in _lines(PROSE)
             if any(pattern.search(line) for pattern in RETIRED) and "AMD-FAC-002" not in line]
    assert stale == []


# item 1 of the brief on the trellis view's load time: the three registries
# whose recipes the three verbs bind, each with the number of its stage
# occurrences
BENHABIB = ROOT / "applications/benhabib-2019/declaration"
BOUND_BY_THE_VERBS = {"durables": (DURABLES, TWO_STAGES, 103), "retirement-choice": (RETIREMENT, "spec.yml", 61),
                      "benhabib-2019": (BENHABIB, "spec.yml", 37)}
VERBS = (calibrate_trellis, methodize_trellis, configure_trellis)


# the three registries elaborated and bound whole, several times each: one of
# the sweeps
@pytest.mark.sweep
def test_trellis_load_item_1_specify_trellis_answers_the_three_verbs_and_copies_each_stage_occurrence_once(monkeypatch):
    """`specify_trellis(syntactic, previous)` equals `elaborate_trellis`
    followed by the three verbs, by `==` on the whole trellis, no position
    changed between the two, and copies each stage occurrence once, where
    the verbs copy each three times after the elaboration's copy: on each
    registry elaborated anew and with its bound trellis given again as
    `previous`, and on durables with that trellis as `previous` for a fill of
    β and n_a and for the adjuster's method choice, which remakes the
    adjuster's 51 occurrences. `assemble_trellis`, `specify_trellis` of the
    recipe, copies each once. Where the verbs refuse, `specify_trellis`
    raises the same refusal, its notes naming the stage occurrence and the
    kind. The copies are counted by patching `copy_native` in the factory's
    module, as test_item_2 counts the constructions."""
    copies, copy = [], trellis_module.copy_native
    monkeypatch.setattr(trellis_module, "copy_native", lambda stage: copies.append(stage.name) or copy(stage))

    def both(syntactic, previous=None):
        """The trellis `specify_trellis` answers, once asserted equal to the
        trellis of the verbs, and the copies of each route: those of
        `specify_trellis`, and those of the three verbs after
        `elaborate_trellis`, whose own copies are not counted."""
        copies.clear()
        specified = specify_trellis(syntactic, previous)
        once = len(copies)
        trellis = elaborate_trellis(syntactic, previous)
        copies.clear()
        for verb in VERBS:
            trellis = verb(trellis, syntactic)
        assert specified == trellis and changed_positions(trellis, specified) == []
        return specified, (once, len(copies))

    for name, (directory, recipe, occurrences) in BOUND_BY_THE_VERBS.items():
        syntactic = load_recipe(directory, recipe)
        bound, counts = both(syntactic)
        assert counts == (occurrences, 3 * occurrences), name
        # the bound trellis given again: each text is taken from it and every
        # binding is already held, so nothing is bound anew
        again, counts = both(syntactic, bound)
        assert counts == (occurrences, 3 * occurrences) and changed_positions(bound, again) == [], name
        if name == "durables":
            durables = bound
    # the fill binds again the keeper and the adjuster at every period, the
    # bequest declaring neither name; the method choice of test_item_3 remakes
    # each of the adjuster's occurrences from its record
    filled, counts = both(load_recipe(DURABLES, TWO_STAGES, fill={"calibration": {"β": 0.93}, "settings": {"n_a": 500}}),
                          durables)
    assert counts == (103, 309)
    assert len(changed_positions(durables, filled)) == 102 and (0, "bequest") not in changed_positions(durables, filled)
    choice = {"methods": [{"on": "cntn_to_dcsn", "method": "!vfi", "handler": "fues-durables:make_adjuster_vfi"}]}
    switched, counts = both(load_recipe(DURABLES, TWO_STAGES, adjuster_method=choice), durables)
    assert counts == (103, 309)
    assert changed_positions(durables, switched) == [(h, "adjuster_cons") for h in range(51)]
    copies.clear()
    assert assemble_trellis(DURABLES, TWO_STAGES) == durables and len(copies) == 103
    # the recipes the verbs refuse: the calibration of durables supplies no
    # value for the tenure stage's Y, and pension's slots are unfilled, so
    # that its worker_saving holds no β
    for directory, key in ((DURABLES, "tenure"), (PENSION, "worker_saving")):
        syntactic = load_recipe(directory, "spec.yml")
        with pytest.raises(ValueError) as by_the_verbs:
            trellis = elaborate_trellis(syntactic)
            for verb in VERBS:
                trellis = verb(trellis, syntactic)
        with pytest.raises(ValueError) as by_specify_trellis:
            specify_trellis(syntactic)
        refusal, again = by_the_verbs.value, by_specify_trellis.value
        assert (type(again), str(again), again.__notes__) == (type(refusal), str(refusal), refusal.__notes__)
        assert again.__notes__ == [f"Stage occurrence: periods[0].stages[{key!r}]", "Binding kind: calibration"]


# the trellis file of the portfolio-consumption application, whose 18 stage
# occurrences the verbs methodize and configure bind
# the folder's trellis file of records with the stages and connectors of the
# portfolio-first order; trellis.port-cons.yml itself lists keys for the recipe
# since the consolidation of 28 October 2026 (decision MB-W11)
PORT_CONS = ROOT / "applications/cons-port/declaration/trellis.port-cons-vfi.yml"


def test_trellis_load_specify_trellis_binds_the_kinds_named_in_the_order_of_the_verbs():
    """`specify_trellis` given the kinds `("methods", "settings")`, and the
    same kinds in the other order, answers the trellis that
    `elaborate_trellis` and the verbs `methodize_trellis` and
    `configure_trellis` make, applied in that order, on the trellis file of
    records of the portfolio-consumption application; a kind that is none of
    `calibration`, `methods` and `settings` is refused with a ValueError
    that names the three."""
    syntactic = load_trellis(PORT_CONS)
    trellis = elaborate_trellis(syntactic)
    for verb in (methodize_trellis, configure_trellis):
        trellis = verb(trellis, syntactic)
    for kinds in (("methods", "settings"), ("settings", "methods")):
        assert specify_trellis(syntactic, kinds=kinds) == trellis, kinds
    with pytest.raises(ValueError, match="one of calibration, methods, settings"):
        specify_trellis(syntactic, kinds=("methods", "solution"))
