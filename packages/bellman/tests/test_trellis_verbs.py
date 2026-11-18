"""The binding of a trellis: the trellis verbs calibrate_trellis,
methodize_trellis and configure_trellis, specify_trellis, respecify_trellis and
assemble_trellis, and periods accreted from stages bound one by one."""

import functools
import hashlib
import pickle
import re
import shutil
from copy import deepcopy
from pathlib import Path

import pytest
from application_files import (
    CONS_METHODS,
    CONS_PORT,
    CONS_SETTINGS,
    DURABLES,
    DURABLES_RECIPE_WITHOUT_TENURE,
    PENSION,
    RETIREMENT,
    ROOT,
)
from stage_builders import differing_graph_triples, without_addresses
from stage_texts import changed, corpus_text
from trellises import ADDED_REGISTRY_FILES, BEQUEST_CONNECTOR

import bellman.factory.trellis as trellis_module
from bellman.factory.trellis import copy_trellis, positions
from bellman.native.versions import stored
from bellman.refusal_examples import REGISTRY_FILES, write_registry
from bellman.refusals import FactoryError
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.kernels import compile_kernel, kernel
from bellman.stage.sources import load_settings
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
    respecify_trellis,
    specify_trellis,
)

# The small registry is the registry of `bellman.refusal_examples`, its files
# `REGISTRY_FILES` with the files of `ADDED_REGISTRY_FILES` added, which the
# session fixture `two_nodes_registry` writes: one stage file, the two-node
# stage `two_nodes` of `bellman.refusal_examples.TWO_NODES`, with its methods
# file, over three periods, the terminal period with a calibration file of its
# own.

# the three trellis verbs, in the order in which they bind
TRELLIS_VERBS = (calibrate_trellis, methodize_trellis, configure_trellis)


# the number of periods to which these tests cut a trellis file, so that a
# model of fifty periods binds in a few seconds
PERIODS = 3


# the stage occurrences of the cut two-stage durables trellis: the keeper and
# the adjuster at each period, and the bequest at the terminal period
TWO_STAGE_OCCURRENCES = 2 * PERIODS + 1


# the recipe of the durables folder copied by `cut_durables` that adds to the
# adjuster's methods a file typing value function iteration, `!vfi`, at its
# backward decision builder
VFI_RECIPE = "spec.two-stages.vfi.yml"


# the folder of the within-life model of Benhabib, Bisin and Luo (2019)
BENHABIB = ROOT / "applications/benhabib-2019/declaration"


# two registries cut to PERIODS periods, each with its recipe and the number
# of its stage occurrences
CUT_REGISTRIES = {
    # ret_choice, worker_cons and retiree_cons at each period, and the bequest
    # at the terminal period
    "retirement-choice": (RETIREMENT, "spec.yml", 3 * PERIODS + 1),
    # the bequest at the terminal period and the within-life stage at each of
    # the two other periods, each of which binds the one wage table on the ages
    # that the calibration file calibration/wage holds
    "benhabib-2019": (BENHABIB, "spec.yml", PERIODS),
}


# one of the six trellis files of the cons-port application that write each
# stage as a record, which `load_trellis` reads; the two other trellis files
# of its folder, trellis.cons-port.yml and trellis.port-cons.yml, list the
# keys of a recipe, which `load_trellis` does not read
PORT_CONS = CONS_PORT / "trellis.port-cons-vfi.yml"


def cut_trellis_text(file):
    """The text of the trellis file `file` cut to PERIODS periods: its
    template repeated for the periods that the file does not write out, and,
    where it lists one inter-period mapping for each pair of adjacent periods,
    its first PERIODS - 1 mappings. A file that does not write exactly one
    template is refused with a ValueError, since the cut reads that layout."""
    text = Path(file).read_text(encoding="utf-8")
    # the periods that the file writes out before its template
    written = text.count("\n  - stages:")
    text, templates = re.subn(
        r"(\{template: [^}]*repeat: )\d+", rf"\g<1>{PERIODS - written}", text
    )
    if templates != 1:
        raise ValueError(f"{file} writes {templates} templates, and the cut reads one")
    head, _, tail = text.partition("\ninter_connectors:\n")
    mappings = [line for line in tail.splitlines(keepends=True) if line.startswith("  - ")]
    if len(mappings) > 1:
        text = head + "\ninter_connectors:\n" + "".join(mappings[: PERIODS - 1])
    return text


def texts_of_cut_trellis(directory):
    """The argument `texts` of `load_recipe` that gives the recipe of the
    folder `directory` the text of its trellis file trellis.yml cut to
    PERIODS periods in place of the text on disk."""
    file = (directory / "trellis.yml").resolve()
    return {str(file): cut_trellis_text(file)}


def stage_bound_by_hand(registry, key, settings):
    """The stage of the stage file of `key` in the durables folder
    `registry`, elaborated and bound by the stage's own verbs with the
    folder's calibration file, the stage's methods file and `settings`."""
    stage = elaborate_stage(load_stage(registry / f"stages/{key}/{key}.bl"))
    return (
        stage.calibrate(str(registry / "calibration/durables.yml"))
        .methodize(str(registry / f"stages/{key}/methods.bl"))
        .configure(settings)
    )


def counting(calls, kind, verb):
    """The stage verb `verb` of the kind `kind`, adding one to `calls[kind]`
    at each call."""

    # the entry of the settings in the package's table of stage verbs takes
    # the record's settings files as a keyword
    def bind(stage, mapping, **options):
        calls[kind] += 1
        return verb(stage, mapping, **options)

    return bind


def as_plain_containers(value):
    """`value` with every mapping in it written as a dictionary in its own
    order and every list or tuple as a list."""
    if hasattr(value, "items"):
        return {key: as_plain_containers(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_plain_containers(item) for item in value]
    return value


def printed_provenance_and_bindings(stage):
    """The provenance of a version, which holds the methods files read, and
    its calibration and settings, as `repr` writes them."""
    return repr(
        as_plain_containers(
            {
                "provenance": stage.provenance,
                "calibration": stage.bindings.calibration,
                "settings": stage.bindings.settings,
            }
        )
    )


def trellis_before(syntactic, kind):
    """The trellis to which the trellis verb of `kind` is applied: the
    elaborated trellis of `syntactic` for the calibration, and that trellis
    calibrated and methodized for the settings."""
    trellis = elaborate_trellis(syntactic)
    if kind == "settings":
        trellis = methodize_trellis(calibrate_trellis(trellis, syntactic), syntactic)
    return trellis


def edited(syntactic, edit):
    """A copy of the syntactic trellis `syntactic` with the function `edit`
    applied to the stages of each period."""
    copied = deepcopy(syntactic)
    for period in copied["periods"]:
        edit(period["stages"])
    return copied


def with_cons_settings_changed(stages):
    """Sets the setting n_m of the record of cons to 32000."""
    stages["cons"]["settings"] = {**stages["cons"]["settings"], "n_m": 32000}


def with_disc_text_changed(stages):
    """Ends the stage text of the record of disc with one more line break and
    records the digest of the new text."""
    written = stages["disc"]["stage"]["text"] + "\n"
    stages["disc"]["stage"] = {**stages["disc"]["stage"], "text": written}
    digest = hashlib.sha256(written.encode("utf-8")).hexdigest()
    stages["disc"]["provenance"] = {**stages["disc"]["provenance"], "sha256": digest}


def with_a_refused_method_for_cons(stages):
    """Adds to each methods file of the record of cons a line that types the
    method `!root_find` at the arrival builder, which the construction of cons
    refuses."""
    stages["cons"]["methods"] = [
        {**entry, "text": entry["text"] + "\narvl_to_dcsn.method : !root_find\n"}
        for entry in stages["cons"]["methods"]
    ]


def pickled(trellis):
    """The bytes that the standard pickle writes of a trellis: of the trellis
    with the stages of each period replaced by their keys in order, the keys
    of each period in order, and the bytes of each stage occurrence by its
    position."""
    rest = {
        **trellis,
        "periods": [{**period, "stages": list(period["stages"])} for period in trellis["periods"]],
    }
    return (
        pickle.dumps(rest),
        [list(period) for period in trellis["periods"]],
        {(place.h, place.key): pickle.dumps(place.stage) for place in positions(trellis)},
    )


@pytest.fixture(scope="module")
def cut_durables(tmp_path_factory):
    """A copy of the durables folder whose two-stage trellis file is cut to
    PERIODS periods, beside VFI_RECIPE, whose methods file of value
    iteration the copy holds."""
    registry = tmp_path_factory.mktemp("durables") / "durables"
    shutil.copytree(DURABLES, registry)
    file = registry / "trellis.two-stages.yml"
    file.write_text(cut_trellis_text(file), encoding="utf-8")
    addition = "stages/adjuster_cons/methods.vfi.bl"
    (registry / addition).write_text(
        "@methods: adjuster_cons\n"
        "cntn_to_dcsn.method : !vfi\n"
        'cntn_to_dcsn.handler : "fues-durables:make_adjuster_vfi"\n',
        encoding="utf-8",
    )
    text = (registry / DURABLES_RECIPE_WITHOUT_TENURE).read_text(encoding="utf-8")
    before = "methods: {all: [stages/adjuster_cons/methods.bl]}"
    if text.count(before) != 1:
        raise ValueError(
            f"{DURABLES_RECIPE_WITHOUT_TENURE} does not name the adjuster's methods list once"
        )
    after = f"methods: {{all: [stages/adjuster_cons/methods.bl, {addition}]}}"
    (registry / VFI_RECIPE).write_text(text.replace(before, after), encoding="utf-8")
    return registry


@pytest.fixture(scope="module")
def durables_steps(cut_durables):
    """The syntactic trellis of the cut two-stage durables recipe, its four
    stopping points by name, and a copy of the specified trellis taken when
    it was made."""
    syntactic = load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE)
    elaborated = elaborate_trellis(syntactic)
    calibrated = calibrate_trellis(elaborated, syntactic)
    methodized = methodize_trellis(calibrated, syntactic)
    specified = configure_trellis(methodized, syntactic)
    return {
        "syntactic": syntactic,
        "elaborated": elaborated,
        "calibrated": calibrated,
        "methodized": methodized,
        "specified": specified,
        "copy": copy_trellis(specified),
    }


@pytest.fixture(scope="module")
def refilled_durables(cut_durables, durables_steps):
    """The specified durables trellis, by name, and that trellis bound again
    from the recipe with the fill β = 0.93 and n_a = 500: after
    calibrate_trellis, and after configure_trellis."""
    fill = {"calibration": {"β": 0.93}, "settings": {"n_a": 500}}
    syntactic = load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE, fill=fill)
    calibrated = calibrate_trellis(durables_steps["specified"], syntactic)
    return {
        "specified": durables_steps["specified"],
        "recalibrated": calibrated,
        "reconfigured": configure_trellis(calibrated, syntactic),
    }


@pytest.fixture(scope="module")
def durables_with_vfi(cut_durables, durables_steps):
    """The trellis of VFI_RECIPE, elaborated with the specified durables
    trellis as the previous trellis and bound by the three verbs."""
    syntactic = load_recipe(cut_durables, VFI_RECIPE)
    trellis = elaborate_trellis(syntactic, durables_steps["specified"])
    for verb in TRELLIS_VERBS:
        trellis = verb(trellis, syntactic)
    return trellis


@pytest.fixture(scope="module")
def syntactic_cases(cut_durables):
    """For each case that specify_trellis and the verbs bind, by name, its
    syntactic trellis and the case whose specified trellis is given as the
    previous trellis, or None: each registry cut to PERIODS periods, each
    again with its own specified trellis as the previous one, and the
    durables recipe with a fill and with value function iteration."""
    durables = load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE)
    cut = {
        name: load_recipe(directory, recipe, texts_of_cut_trellis(directory))
        for name, (directory, recipe, _) in CUT_REGISTRIES.items()
    }
    fill = {"calibration": {"β": 0.93}, "settings": {"n_a": 500}}
    return {
        "durables": (durables, None),
        "retirement-choice": (cut["retirement-choice"], None),
        "benhabib-2019": (cut["benhabib-2019"], None),
        "durables-given-again": (durables, "durables"),
        "retirement-choice-given-again": (cut["retirement-choice"], "retirement-choice"),
        "benhabib-2019-given-again": (cut["benhabib-2019"], "benhabib-2019"),
        "durables-refilled": (
            load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE, fill=fill),
            "durables",
        ),
        "durables-with-vfi": (load_recipe(cut_durables, VFI_RECIPE), "durables"),
    }


@pytest.fixture(scope="module")
def both_routes(syntactic_cases):
    """`both_routes(case)`: the trellis that specify_trellis answers for a
    case of `syntactic_cases`, the trellis that elaborate_trellis and the
    three verbs answer, and the number of stage occurrences that each route
    copies, the copies of elaborate_trellis itself not counted."""
    copy = trellis_module.copy_native

    @functools.cache
    def routes(case):
        syntactic, previous_case = syntactic_cases[case]
        previous = routes(previous_case)[0] if previous_case else None
        copies = []
        with pytest.MonkeyPatch.context() as patch:
            # each copy of a stage occurrence is counted by its stage's name
            patch.setattr(
                trellis_module,
                "copy_native",
                lambda stage: copies.append(stage.name) or copy(stage),
            )
            specified = specify_trellis(syntactic, previous)
            once = len(copies)
            trellis = elaborate_trellis(syntactic, previous)
            copies.clear()
            for verb in TRELLIS_VERBS:
                trellis = verb(trellis, syntactic)
        return specified, trellis, (once, len(copies))

    return routes


@pytest.fixture(scope="module")
def port_cons_records():
    """The syntactic trellis that load_trellis reads from PORT_CONS."""
    return load_trellis(PORT_CONS)


@pytest.fixture(scope="module")
def port_cons_methodized_and_configured(port_cons_records):
    """The trellis that elaborate_trellis, methodize_trellis and
    configure_trellis answer, in that order, for `port_cons_records`."""
    trellis = elaborate_trellis(port_cons_records)
    for verb in (methodize_trellis, configure_trellis):
        trellis = verb(trellis, port_cons_records)
    return trellis


@pytest.fixture(scope="module")
def port_cons_recipe():
    """The syntactic trellis of the recipe spec.port-cons.yml of the
    portfolio-consumption application, its trellis file shortened from six
    repetitions of its template to two, and the trellis that specify_trellis
    answers for it."""
    file = CONS_PORT / "trellis.port-cons.yml"
    text = file.read_text(encoding="utf-8").replace("    repeat: 6\n", "    repeat: 2\n")
    before = load_recipe(CONS_PORT, "spec.port-cons.yml", {str(file.resolve()): text})
    return before, specify_trellis(before)


@pytest.fixture(scope="module")
def respecified(port_cons_recipe):
    """`respecified(edit)`: the syntactic trellis of `port_cons_recipe`
    edited by `edit`, and the trellis that respecify_trellis answers for it
    from the specified trellis."""
    before, specified = port_cons_recipe

    @functools.cache
    def answer(edit):
        syntactic = edited(before, edit)
        return syntactic, respecify_trellis(specified, before, syntactic)

    return answer


@pytest.fixture(scope="module")
def small_steps(two_nodes_recipe):
    """The syntactic trellis of the small registry's recipe and its four
    stopping points, by name."""
    elaborated = elaborate_trellis(two_nodes_recipe)
    calibrated = calibrate_trellis(elaborated, two_nodes_recipe)
    methodized = methodize_trellis(calibrated, two_nodes_recipe)
    return {
        "syntactic": two_nodes_recipe,
        "elaborated": elaborated,
        "calibrated": calibrated,
        "methodized": methodized,
        "specified": configure_trellis(methodized, two_nodes_recipe),
    }


@pytest.fixture(scope="module")
def partly_recalibrated(two_nodes_recipe, two_nodes_trellis):
    """The small trellis calibrated again from its recipe with the
    calibration of period 1 changed to β = 0.5."""
    changed = deepcopy(two_nodes_recipe)
    changed["periods"][1]["stages"]["two_nodes"]["calibration"] = {"β": 0.5, "R": 1.02}
    return calibrate_trellis(two_nodes_trellis, changed)


@pytest.fixture(scope="module")
def list_valued_registry(tmp_path_factory):
    """A copy of the small registry whose two-node stage declares the
    parameter w over ℝ × ℝ, which its calibration file supplies as the list
    [1.0, 2.0], and the trellis that assemble_trellis answers for it."""
    path = "stages/two_nodes/two_nodes.bl"
    stage = REGISTRY_FILES[path].replace("R : ℝ₊₊\n", "R : ℝ₊₊\nw : ℝ × ℝ\n")
    calibration = "calibration:\n  β: 0.96\n  R: 1.02\n  w: [1.0, 2.0]\n"
    files = {**ADDED_REGISTRY_FILES, path: stage, "calibration/main.yml": calibration}
    directory = write_registry(tmp_path_factory.mktemp("listed"), files)
    return directory, assemble_trellis(directory, "spec.yml")


@pytest.fixture(scope="module")
def other_selection(tmp_path_factory, two_nodes_trellis):
    """The syntactic trellis of a copy of the small registry whose recipe
    names the methods file methods.other.bl in place of methods.bl, and the
    trellis that specify_trellis answers for it with the small trellis as
    the previous trellis."""
    spec = ADDED_REGISTRY_FILES["spec.yml"].replace(
        "stages/two_nodes/methods.bl", "stages/two_nodes/methods.other.bl"
    )
    folder = write_registry(
        tmp_path_factory.mktemp("switched"), {**ADDED_REGISTRY_FILES, "spec.yml": spec}
    )
    switched = load_recipe(folder, "spec.yml")
    return switched, specify_trellis(switched, two_nodes_trellis)


@pytest.fixture(scope="module")
def verb_variants(two_nodes_recipe, two_nodes_registry):
    """Three syntactic trellises of the small registry, by name: its recipe,
    whose terminal period holds another calibration; the recipe with the
    terminal slot filled with R = 1.02, so that the three records differ in
    their source lists alone; and that trellis with the settings of the last
    period written in another order."""
    filled = load_recipe(two_nodes_registry, "spec.yml", terminal={"R": 1.02})
    reordered = deepcopy(filled)
    settings = ({"n_k": 10, "extra": 1}, {"n_k": 10, "extra": 1}, {"extra": 1, "n_k": 10})
    for period, written in zip(reordered["periods"], settings):
        period["stages"]["two_nodes"]["settings"] = written
    return {"recipe": two_nodes_recipe, "filled": filled, "reordered": reordered}


@pytest.fixture(scope="module")
def counted_verbs(verb_variants):
    """`counted_verbs(elaborated_from, bound_with)`: the trellis of
    `verb_variants` named `elaborated_from` elaborated and bound by the three
    verbs from the one named `bound_with`, with the stage verbs counted by
    kind: the stopping points by name, and the counts after each verb."""

    @functools.cache
    def bound(elaborated_from, bound_with):
        syntactic = verb_variants[bound_with]
        calls = dict.fromkeys(trellis_module._VERBS, 0)
        with pytest.MonkeyPatch.context() as patch:
            for kind, verb in dict(trellis_module._VERBS).items():
                patch.setitem(trellis_module._VERBS, kind, counting(calls, kind, verb))
            elaborated = elaborate_trellis(verb_variants[elaborated_from])
            calibrated = calibrate_trellis(elaborated, syntactic)
            after_calibration = dict(calls)
            methodized = methodize_trellis(calibrated, syntactic)
            after_methods = dict(calls)
            specified = configure_trellis(methodized, syntactic)
        return {
            "calibrated": calibrated,
            "methodized": methodized,
            "specified": specified,
            "after calibrate_trellis": after_calibration,
            "after methodize_trellis": after_methods,
            "calibration": after_calibration["calibration"],
            "settings": calls["settings"] - after_methods["settings"],
        }

    return bound


@pytest.mark.parametrize(
    ("before", "after", "bound"),
    [
        pytest.param("elaborated", "calibrated", TWO_STAGE_OCCURRENCES, id="calibrate_trellis"),
        # each occurrence holds the methods read with its stage text
        pytest.param("calibrated", "methodized", 0, id="methodize_trellis"),
        pytest.param("methodized", "specified", TWO_STAGE_OCCURRENCES, id="configure_trellis"),
    ],
)
def test_calibrate_and_configure_trellis_bind_every_occurrence_and_methodize_trellis_none(
    durables_steps, before, after, bound
):
    """Applied in turn to the elaborated cut durables trellis, each trellis
    verb binds this number of its seven stage occurrences: all for the
    calibration and the settings, none for the methods."""
    assert len(changed_positions(durables_steps[before], durables_steps[after])) == bound


def test_the_three_verbs_specify_the_keeper_and_the_adjuster_and_configure_the_calibrated_bequest(
    durables_steps,
):
    """After the three verbs, each keeper and adjuster of the cut durables
    trellis prints as specified, and each bequest as holding its calibration
    and its settings."""
    for _, key, _, stage in positions(durables_steps["specified"]):
        status = "calibration, settings" if key == "bequest" else "specified"
        assert repr(stage) == f"ElaboratedStage({key!r}, {status})"


def test_the_bound_adjuster_holds_the_values_of_the_calibration_file(durables_steps):
    """The adjuster of the specified durables trellis holds the six values
    of the durables calibration file."""
    adjuster = durables_steps["specified"]["periods"][0]["stages"]["adjuster_cons"]
    assert dict(adjuster.bindings.calibration) == {
        "β": 0.945,
        "α": 0.7,
        "γ_c": 3.5,
        "γ_h": 1.5,
        "κ": 0.06,
        "τ": 0.12,
    }


@pytest.mark.parametrize(
    "verb",
    [
        pytest.param(calibrate_trellis, id="calibrate_trellis"),
        pytest.param(configure_trellis, id="configure_trellis"),
    ],
)
def test_a_verb_given_the_mappings_that_its_trellis_holds_binds_no_stage_occurrence(
    durables_steps, verb
):
    """A trellis verb given the syntactic trellis from which the specified
    durables trellis was bound binds none of its stage occurrences."""
    specified = durables_steps["specified"]
    assert changed_positions(specified, verb(specified, durables_steps["syntactic"])) == []


@pytest.mark.parametrize(
    ("before", "after"),
    [
        pytest.param(
            "specified", "recalibrated", id="calibrate_trellis-and-the-bequest-declares-no-beta"
        ),
        pytest.param(
            "recalibrated", "reconfigured", id="configure_trellis-and-the-bequest-has-no-settings"
        ),
    ],
)
def test_a_fill_of_beta_and_n_a_binds_again_every_stage_occurrence_but_the_bequest(
    refilled_durables, before, after
):
    """A fill of β and n_a binds again the keeper and the adjuster at every
    period, and not the bequest, which neither declares β nor has a list of
    settings."""
    changed = changed_positions(refilled_durables[before], refilled_durables[after])
    assert changed == [
        (h, key) for h in range(PERIODS) for key in ("keeper_cons", "adjuster_cons")
    ]


def test_a_fill_keeps_the_graphs_and_the_definitions_of_every_stage_occurrence(
    refilled_durables,
):
    """Each stage occurrence that a fill of β and n_a binds again has the
    graphs and the definitions of the occurrence at its position before."""
    specified, reconfigured = refilled_durables["specified"], refilled_durables["reconfigured"]
    # The fill binds the keeper and the adjuster again, so that the
    # comparison below is about new versions.
    assert changed_positions(specified, reconfigured) == [
        (h, key) for h in range(PERIODS) for key in ("keeper_cons", "adjuster_cons")
    ]
    for (_, _, _, old), (_, _, _, new) in zip(positions(specified), positions(reconfigured)):
        assert differing_graph_triples(old, new) == [] and old.definitions == new.definitions


def test_a_fill_of_beta_binds_its_value_at_the_adjuster(refilled_durables):
    """The adjuster bound again from the fill β = 0.93 holds that value."""
    adjuster = refilled_durables["reconfigured"]["periods"][0]["stages"]["adjuster_cons"]
    assert adjuster.bindings.calibration["β"] == 0.93


def test_a_fill_of_names_that_the_bequest_does_not_declare_leaves_the_bequest_equal(
    refilled_durables,
):
    """The bequest of the trellis bound again from a fill of β and n_a
    equals the bequest of the trellis before."""
    stages = [
        refilled_durables[name]["periods"][0]["stages"] for name in ("reconfigured", "specified")
    ]
    assert stages[0]["bequest"] == stages[1]["bequest"]


def test_a_fill_changes_the_parameter_values_of_a_kernel_and_neither_its_code_nor_a_compiled_one(
    cut_durables, durables_steps
):
    """After a fill of β, the aggregation kernel of the adjuster has the code
    of the kernel before and parameter values that give another value, while
    the kernel compiled before still gives its own value."""
    specified = durables_steps["specified"]
    adjuster = specified["periods"][0]["stages"]["adjuster_cons"]
    aggregation = compile_kernel(adjuster, "cntn_to_dcsn:Aggregation")
    values = kernel(adjuster, "cntn_to_dcsn:Aggregation").parameter_values
    # the arguments of the kernel: the inputs of its block's header, V[>] =
    # 1.0 and the age 50, the decision states m = 1.0 and z_d = 1.0, and the
    # controls c = 0.5 and h_choice = 0.5, then the parameters that it reads;
    # the kernel returns the value V and the age, and the test reads V
    point = (1.0, 50, 1.0, 1.0, 0.5, 0.5)
    before = float(aggregation(*point, *values)[0])
    fill = {"calibration": {"β": 0.93}, "settings": {"n_a": 500}}
    syntactic = load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE, fill=fill)
    refilled = configure_trellis(calibrate_trellis(specified, syntactic), syntactic)
    assert float(aggregation(*point, *values)[0]) == before
    changed = kernel(refilled["periods"][0]["stages"]["adjuster_cons"], "cntn_to_dcsn:Aggregation")
    assert changed.python == kernel(adjuster, "cntn_to_dcsn:Aggregation").python
    after = float(aggregation(*point, *changed.parameter_values)[0])
    assert after != before


@pytest.mark.parametrize(
    ("fill", "bound"),
    [
        pytest.param(
            {"τ": 0.2}, [(h, "adjuster_cons") for h in range(PERIODS)], id="tau-at-the-adjuster"
        ),
        pytest.param({"θ": 2.0}, [(0, "bequest")], id="theta-at-the-bequest"),
    ],
)
def test_a_fill_binds_again_only_the_stage_occurrences_that_declare_the_parameter(
    cut_durables, durables_steps, fill, bound
):
    """A fill of one parameter binds again only the stage occurrences that
    declare it: τ the adjuster at every period, and θ the bequest."""
    specified = durables_steps["specified"]
    filled = calibrate_trellis(
        specified, load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE, fill=fill)
    )
    assert changed_positions(specified, filled) == bound


def test_a_recipe_that_adds_a_methods_file_to_the_adjuster_binds_the_adjuster_alone_anew(
    durables_steps, durables_with_vfi
):
    """The recipe that names one more methods file for the adjuster gives a
    new version of the adjuster at every period and of no other stage."""
    changed = changed_positions(durables_steps["specified"], durables_with_vfi)
    assert changed == [(h, "adjuster_cons") for h in range(PERIODS)]


def test_the_adjuster_takes_vfi_at_its_decision_builder_and_keeps_egm_at_its_policy(
    durables_with_vfi,
):
    """At every period the adjuster's backward decision builder takes the
    method `!vfi` of the added methods file, and its policy keeps `!egm`."""
    for period in durables_with_vfi["periods"]:
        adjuster = period["stages"]["adjuster_cons"]
        assert [
            (place, held.word, held.handler)
            for place, held in adjuster.methods.items()
            if place == "cntn_to_dcsn" or place.startswith("policy")
        ] == [
            ("cntn_to_dcsn", "!vfi", "fues-durables:make_adjuster_vfi"),
            ("policy", "!egm", "fues-durables:make_adjuster_ops"),
        ]


def test_a_methods_file_added_to_the_adjuster_leaves_the_keepers_policy_method(
    durables_with_vfi,
):
    """At every period the keeper's policy keeps the method `!egm` when the
    recipe adds a methods file to the adjuster alone."""
    for period in durables_with_vfi["periods"]:
        keeper = period["stages"]["keeper_cons"]
        assert [
            (place, held.word)
            for place, held in keeper.methods.items()
            if place.startswith("policy")
        ] == [("policy", "!egm")]


def test_the_adjuster_made_anew_with_vfi_is_specified_with_its_earlier_calibration(
    durables_steps, durables_with_vfi
):
    """At every period the adjuster made anew from the recipe with value
    function iteration is specified, with the calibration of the adjuster
    before."""
    pairs = zip(durables_with_vfi["periods"], durables_steps["specified"]["periods"])
    for period, earlier in pairs:
        adjuster = period["stages"]["adjuster_cons"]
        assert repr(adjuster) == "ElaboratedStage('adjuster_cons', specified)"
        assert dict(adjuster.bindings.calibration) == dict(
            earlier["stages"]["adjuster_cons"].bindings.calibration
        )


def test_assemble_trellis_of_the_recipe_with_vfi_holds_the_methods_bindings_and_graphs_bound_anew(
    cut_durables, durables_with_vfi
):
    """assemble_trellis of the recipe with value function iteration holds at
    every position the methods, the bindings and the graphs of the trellis
    bound from it with the earlier trellis as the previous trellis."""
    assembled = assemble_trellis(cut_durables, VFI_RECIPE)
    pairs = zip(positions(durables_with_vfi), positions(assembled))
    for (_, _, _, made), (_, _, _, again) in pairs:
        assert tuple(made.methods.items()) == tuple(again.methods.items())
        assert made.bindings == again.bindings
        assert differing_graph_triples(made, again) == []


def test_the_verbs_leave_the_trellis_that_they_bind_from_unchanged(
    cut_durables, durables_steps, refilled_durables, durables_with_vfi
):
    """After the fills of β and n_a, of τ and of θ and the recipe with value
    function iteration are bound from the specified durables trellis, its
    adjuster keeps β = 0.945 and every stage occurrence of it equals the copy
    taken when it was made."""
    specified = durables_steps["specified"]
    with_tau = calibrate_trellis(
        specified, load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE, fill={"τ": 0.2})
    )
    with_theta = calibrate_trellis(
        specified, load_recipe(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE, fill={"θ": 2.0})
    )
    # Each of the four bindings gives new versions at the positions of the
    # stages that it concerns, so that the comparison below is about verbs
    # that bound something.
    assert changed_positions(specified, with_tau) == [(h, "adjuster_cons") for h in range(PERIODS)]
    assert changed_positions(specified, with_theta) == [(0, "bequest")]
    refilled = refilled_durables["reconfigured"]["periods"][0]["stages"]["adjuster_cons"]
    assert refilled.bindings.calibration["β"] == 0.93
    assert changed_positions(specified, durables_with_vfi) == [
        (h, "adjuster_cons") for h in range(PERIODS)
    ]
    assert specified["periods"][0]["stages"]["adjuster_cons"].bindings.calibration["β"] == 0.945
    for (_, _, _, held), (_, _, _, kept) in zip(
        positions(specified), positions(durables_steps["copy"])
    ):
        assert held == kept


def test_periods_accreted_from_stages_bound_one_by_one_equal_those_of_the_assembled_trellis(
    cut_durables,
):
    """Two periods accreted from stages that their own verbs bound equal the
    first two periods of the trellis that assemble_trellis answers: their
    mapping, keys, connectors, graphs, definitions, bindings and methods."""
    model = assemble_trellis(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE)
    settings = str(cut_durables / "settings/durables.yml")
    keeper = stage_bound_by_hand(cut_durables, "keeper_cons", settings)
    adjuster = stage_bound_by_hand(cut_durables, "adjuster_cons", settings)
    bequest = stage_bound_by_hand(cut_durables, "bequest", {})
    terminal = {"keeper_cons": keeper, "adjuster_cons": adjuster, "bequest": bequest}
    trellis = accrete(
        {"periods": [], "inter_connectors": []},
        {"stages": terminal, "connectors": [BEQUEST_CONNECTOR]},
    )
    earlier = {"stages": {"keeper_cons": keeper, "adjuster_cons": adjuster}, "connectors": []}
    trellis = accrete(trellis, earlier, {})
    assert len(trellis["periods"]) == 2
    assert trellis["inter_connectors"] == model["inter_connectors"][:1] == [{}]
    for h, period in enumerate(trellis["periods"]):
        assert set(period["stages"]) == set(model["periods"][h]["stages"])
        assert period["connectors"] == model["periods"][h]["connectors"]
        for key, by_hand in period["stages"].items():
            assembled = model["periods"][h]["stages"][key]
            assert differing_graph_triples(by_hand, assembled) == []
            assert without_addresses(by_hand.definitions) == without_addresses(
                assembled.definitions
            )
            assert dict(by_hand.bindings.calibration) == dict(assembled.bindings.calibration)
            assert dict(by_hand.bindings.settings) == dict(assembled.bindings.settings)
            assert tuple(by_hand.methods.items()) == tuple(assembled.methods.items())


# the cases that specify_trellis and the verbs bind, with the number of stage
# occurrences of each
SPECIFIED_CASES = {
    "durables": TWO_STAGE_OCCURRENCES,
    "retirement-choice": 3 * PERIODS + 1,
    "benhabib-2019": PERIODS,
    "durables-given-again": TWO_STAGE_OCCURRENCES,
    "retirement-choice-given-again": 3 * PERIODS + 1,
    "benhabib-2019-given-again": PERIODS,
    "durables-refilled": TWO_STAGE_OCCURRENCES,
    "durables-with-vfi": TWO_STAGE_OCCURRENCES,
}


@pytest.mark.parametrize("case", list(SPECIFIED_CASES))
def test_specify_trellis_answers_the_trellis_of_elaborate_trellis_and_the_three_verbs(
    both_routes, case
):
    """specify_trellis answers, with or without a previous trellis, the
    trellis that elaborate_trellis and the three verbs answer, with no
    position changed between the two."""
    specified, by_the_verbs, _ = both_routes(case)
    assert specified == by_the_verbs and changed_positions(by_the_verbs, specified) == []


@pytest.mark.parametrize(
    ("case", "occurrences"), list(SPECIFIED_CASES.items()), ids=list(SPECIFIED_CASES)
)
def test_specify_trellis_copies_each_stage_occurrence_once_and_the_verbs_three_times(
    both_routes, case, occurrences
):
    """specify_trellis copies each stage occurrence once, where the three
    verbs after elaborate_trellis copy each three times."""
    _, _, counts = both_routes(case)
    assert counts == (occurrences, 3 * occurrences)


@pytest.mark.parametrize(
    ("case", "previous", "bound"),
    [
        pytest.param("durables-given-again", "durables", [], id="durables-given-again"),
        pytest.param(
            "retirement-choice-given-again",
            "retirement-choice",
            [],
            id="retirement-choice-given-again",
        ),
        pytest.param(
            "benhabib-2019-given-again", "benhabib-2019", [], id="benhabib-2019-given-again"
        ),
        pytest.param(
            "durables-refilled",
            "durables",
            [(h, key) for h in range(PERIODS) for key in ("keeper_cons", "adjuster_cons")],
            id="durables-fill-of-beta-and-n_a",
        ),
        pytest.param(
            "durables-with-vfi",
            "durables",
            [(h, "adjuster_cons") for h in range(PERIODS)],
            id="durables-recipe-with-vfi",
        ),
    ],
)
def test_specify_trellis_with_a_previous_trellis_binds_anew_only_the_changed_records(
    both_routes, case, previous, bound
):
    """specify_trellis given a specified trellis as the previous one binds
    anew only the positions whose records changed: none for the same
    recipe, the keeper and the adjuster for a fill of β and n_a, and the
    adjuster for the recipe with value function iteration."""
    assert changed_positions(both_routes(previous)[0], both_routes(case)[0]) == bound


def test_assemble_trellis_answers_specify_trellis_of_its_recipe_with_one_copy_of_each_occurrence(
    cut_durables, both_routes, monkeypatch
):
    """assemble_trellis of the cut durables recipe answers the trellis that
    specify_trellis answers for it, copying each stage occurrence once."""
    specified = both_routes("durables")[0]
    copies, copy = [], trellis_module.copy_native
    monkeypatch.setattr(
        trellis_module, "copy_native", lambda stage: copies.append(stage.name) or copy(stage)
    )
    assembled = assemble_trellis(cut_durables, DURABLES_RECIPE_WITHOUT_TENURE)
    assert assembled == specified and len(copies) == TWO_STAGE_OCCURRENCES


@pytest.mark.parametrize(
    ("directory", "key", "recipe_change"),
    [
        # the recipe of durables with the file of the income tables left out
        # of the calibration list of the tenure stage, so that no source
        # supplies a value for the tenure stage's parameter Y
        pytest.param(
            DURABLES,
            "tenure",
            (
                "calibration: {all: [calibration/durables, calibration/wage_schedule, $fill]}",
                "calibration: {all: [calibration/durables, $fill]}",
            ),
            id="durables-without-y-of-the-tenure-stage",
        ),
        # the slots of the pension recipe are not filled, so its
        # worker_saving holds no β
        pytest.param(PENSION, "worker_saving", None, id="pension-retirement-without-beta"),
    ],
)
def test_specify_trellis_raises_the_refusal_of_the_verbs_naming_the_occurrence_and_kind(
    directory, key, recipe_change
):
    """Where the verbs refuse a calibration, specify_trellis raises the same
    refusal, its notes naming the stage occurrence and the kind of the
    binding."""
    texts = texts_of_cut_trellis(directory)
    if recipe_change is not None:
        recipe = (directory / "spec.yml").resolve()
        texts[str(recipe)] = changed(recipe.read_text(encoding="utf-8"), recipe_change)
    syntactic = load_recipe(directory, "spec.yml", texts)
    with pytest.raises(ValueError) as by_the_verbs:
        trellis = elaborate_trellis(syntactic)
        for verb in TRELLIS_VERBS:
            trellis = verb(trellis, syntactic)
    with pytest.raises(ValueError) as by_specify_trellis:
        specify_trellis(syntactic)
    refusal, again = by_the_verbs.value, by_specify_trellis.value
    assert (type(again), str(again), again.__notes__) == (
        type(refusal),
        str(refusal),
        refusal.__notes__,
    )
    assert again.__notes__ == [
        f"Stage occurrence: periods[0].stages[{key!r}]",
        "Binding kind: calibration",
    ]


@pytest.mark.parametrize(
    "kinds",
    [("methods", "settings"), ("settings", "methods")],
    ids=["methods-then-settings", "settings-then-methods"],
)
def test_specify_trellis_binds_the_kinds_it_is_given_in_the_order_of_the_verbs(
    port_cons_records, port_cons_methodized_and_configured, kinds
):
    """specify_trellis given the methods and the settings, in either order,
    answers the trellis that elaborate_trellis, methodize_trellis and
    configure_trellis answer in that order."""
    expected = port_cons_methodized_and_configured
    assert specify_trellis(port_cons_records, kinds=kinds) == expected


def test_specify_trellis_refuses_a_kind_that_is_none_of_calibration_methods_and_settings(
    port_cons_records,
):
    """specify_trellis refuses the kind `solution` with a ValueError that
    names the three kinds that it binds."""
    with pytest.raises(ValueError, match="one of calibration, methods, settings"):
        specify_trellis(port_cons_records, kinds=("methods", "solution"))


def test_a_stage_occurrence_with_methods_passes_the_four_stopping_points_in_the_verbs_order():
    """A stage occurrence whose record names a methods file holds its methods
    once elaborated, is methodized once calibrated, gains no new version from
    methodize_trellis, and is specified once configured."""
    addition = {"text": CONS_METHODS.read_text(encoding="utf-8"), "origin": str(CONS_METHODS)}
    occurrence = {
        "stage": {"text": corpus_text("cons"), "origin": "cons.bl"},
        "methods": [addition],
        "settings": load_settings(CONS_SETTINGS),
        "calibration": {"ρ": 6.0},
    }
    trellis = {
        "periods": [{"stages": {"cons": occurrence}, "connectors": []}],
        "inter_connectors": [],
    }
    elaborated = elaborate_trellis(trellis)
    calibrated = calibrate_trellis(elaborated, trellis)
    methodized = methodize_trellis(calibrated, trellis)
    specified = configure_trellis(methodized, trellis)
    steps = (elaborated, calibrated, methodized, specified)
    assert [repr(step["periods"][0]["stages"]["cons"]) for step in steps] == [
        "ElaboratedStage('cons', methods)",
        "ElaboratedStage('cons', methodized)",
        "ElaboratedStage('cons', methodized)",
        "ElaboratedStage('cons', specified)",
    ]
    assert changed_positions(calibrated, methodized) == []


# the two edits of the recipe of the portfolio-consumption application, by
# id, each with the key of the stage whose record it changes
EDITS = {
    "settings-of-cons": (with_cons_settings_changed, "cons"),
    "text-of-disc": (with_disc_text_changed, "disc"),
}


@pytest.mark.parametrize("edit", [edit for edit, _ in EDITS.values()], ids=list(EDITS))
def test_respecify_trellis_answers_byte_for_byte_what_specify_trellis_answers(respecified, edit):
    """respecify_trellis after an edit of a record answers the trellis that
    specify_trellis answers for the edited recipe, each stage occurrence and
    every other entry as the standard pickle writes them."""
    syntactic, again = respecified(edit)
    assert pickled(again) == pickled(specify_trellis(syntactic))


@pytest.mark.parametrize(("edit", "key"), list(EDITS.values()), ids=list(EDITS))
def test_respecify_trellis_binds_anew_only_the_positions_whose_record_changed(
    port_cons_recipe, respecified, edit, key
):
    """respecify_trellis gives a new version at the two positions of the
    stage whose record changed and at no other."""
    _, specified = port_cons_recipe
    _, again = respecified(edit)
    renewed = [(place.h, place.key) for place in positions(again) if place.key == key]
    assert changed_positions(specified, again) == renewed and len(renewed) == 2


@pytest.mark.parametrize(("edit", "key"), list(EDITS.values()), ids=list(EDITS))
def test_respecify_trellis_keeps_the_very_occurrence_at_each_position_whose_record_is_unchanged(
    port_cons_recipe, respecified, edit, key
):
    """respecify_trellis holds at each position whose record is unchanged
    the very stage occurrence of the trellis specified before, and at each
    other position another object."""
    _, specified = port_cons_recipe
    _, again = respecified(edit)
    for place in positions(again):
        held = specified["periods"][place.h]["stages"][place.key]
        assert (place.stage is held) == (place.key != key), (place.h, place.key)


def test_respecify_trellis_of_an_unchanged_recipe_answers_the_specified_trellis_itself(
    port_cons_recipe,
):
    """respecify_trellis of an unchanged copy of the recipe answers the
    specified trellis byte for byte, holding its very stage occurrences."""
    before, specified = port_cons_recipe
    unchanged = respecify_trellis(specified, before, deepcopy(before))
    assert pickled(unchanged) == pickled(specified)
    pairs = zip(positions(unchanged), positions(specified))
    assert all(place.stage is held.stage for place, held in pairs)


def test_respecify_trellis_refuses_a_changed_methods_file_as_specify_trellis_refuses_it(
    port_cons_recipe,
):
    """A methods file that the construction of cons refuses is refused by
    respecify_trellis as specify_trellis refuses it, the notes naming every
    occurrence of cons."""
    before, specified = port_cons_recipe
    syntactic = edited(before, with_a_refused_method_for_cons)
    with pytest.raises(Exception) as whole:
        specify_trellis(syntactic)
    with pytest.raises(Exception) as alone:
        respecify_trellis(specified, before, syntactic)
    assert (type(alone.value), str(alone.value), alone.value.__notes__) == (
        type(whole.value),
        str(whole.value),
        whole.value.__notes__,
    )
    occurrences = ", ".join(f"periods[{h}].stages['cons']" for h in range(len(before["periods"])))
    assert alone.value.__notes__ == ["Affected stage occurrences: " + occurrences]


def test_respecify_trellis_refuses_two_syntactic_trellises_that_differ_in_a_connector(
    port_cons_recipe,
):
    """respecify_trellis refuses under `trellis-file-shape`, at the period,
    a syntactic trellis whose period writes other connectors than the one
    that the trellis was specified from."""
    before, specified = port_cons_recipe
    connectors = deepcopy(before)
    connectors["periods"][0]["connectors"] = []
    with pytest.raises(FactoryError) as refused:
        respecify_trellis(specified, before, connectors)
    assert (refused.value.rule, refused.value.address) == ("trellis-file-shape", "periods[0]")


def test_respecify_trellis_refuses_a_trellis_bound_under_other_kinds_than_it_is_given(
    port_cons_recipe,
):
    """respecify_trellis refuses under `record-shape` a trellis specified for
    the methods and the settings alone, where it is given every kind."""
    before, _ = port_cons_recipe
    methods_and_settings = specify_trellis(before, kinds=("methods", "settings"))
    with pytest.raises(FactoryError) as refused:
        respecify_trellis(methods_and_settings, before, edited(before, with_cons_settings_changed))
    assert (refused.value.rule, refused.value.address) == (
        "record-shape",
        "periods[0].stages['port']",
    )


def test_an_elaborated_occurrence_whose_record_names_a_methods_file_prints_as_holding_methods(
    small_steps,
):
    """Each elaborated stage occurrence of the small registry, whose record
    names a methods file, prints as holding its methods before any verb binds
    it."""
    elaborated = small_steps["elaborated"]
    assert [repr(stage) for _, _, _, stage in positions(elaborated)] == [
        "ElaboratedStage('two_nodes', methods)"
    ] * 3


def test_calibrate_trellis_binds_at_each_position_the_calibration_that_its_record_names(
    small_steps,
):
    """calibrate_trellis binds every position of the small registry, each
    with the values of its own record: R = 1.04 at the terminal period."""
    calibrated = small_steps["calibrated"]
    assert [dict(stage.bindings.calibration) for _, _, _, stage in positions(calibrated)] == [
        {"β": 0.96, "R": 1.04},
        {"β": 0.96, "R": 1.02},
        {"β": 0.96, "R": 1.02},
    ]
    assert changed_positions(small_steps["elaborated"], calibrated) == [
        (0, "two_nodes"),
        (1, "two_nodes"),
        (2, "two_nodes"),
    ]


def test_configure_trellis_specifies_each_position_with_the_settings_of_its_record(small_steps):
    """configure_trellis after the other two verbs makes every position of
    the small registry specified, with the setting n_k = 10."""
    specified = small_steps["specified"]
    assert [repr(stage) for _, _, _, stage in positions(specified)] == [
        "ElaboratedStage('two_nodes', specified)"
    ] * 3
    assert dict(specified["periods"][0]["stages"]["two_nodes"].bindings.settings) == {"n_k": 10}


def test_the_specified_version_records_the_ordered_sources_of_its_calibration(small_steps):
    """The terminal occurrence of the specified small trellis records the
    sources of its calibration in the order of its record."""
    stage = small_steps["specified"]["periods"][0]["stages"]["two_nodes"]
    lists = stage.provenance["source_lists"]["calibration"]
    assert [entry.get("source", entry.get("slot")) for entry in lists] == [
        "calibration/main",
        "fill",
        "calibration/terminal",
        "terminal",
    ]


def test_configure_trellis_binds_the_settings_of_an_elaborated_trellis_with_no_calibration(
    two_nodes_recipe, small_steps
):
    """configure_trellis binds the setting n_k = 10 on the elaborated small
    trellis, which no verb has calibrated."""
    alone = configure_trellis(small_steps["elaborated"], two_nodes_recipe)
    assert dict(alone["periods"][0]["stages"]["two_nodes"].bindings.settings) == {"n_k": 10}


def test_a_verb_places_a_new_object_at_a_position_that_it_does_not_bind(
    two_nodes_recipe, small_steps
):
    """calibrate_trellis given the recipe from which the small trellis was
    specified binds no position, and places at the terminal position another
    object than the one held there."""
    specified = small_steps["specified"]
    again = calibrate_trellis(specified, two_nodes_recipe)
    assert changed_positions(specified, again) == []
    held = specified["periods"][0]["stages"]["two_nodes"]
    assert again["periods"][0]["stages"]["two_nodes"] is not held


def test_assemble_trellis_holds_the_occurrence_that_the_three_verbs_bind(
    two_nodes_trellis, small_steps
):
    """assemble_trellis of the small registry holds at the last period the
    stage occurrence that elaborate_trellis and the three verbs bind there."""
    assembled = two_nodes_trellis
    specified = small_steps["specified"]
    assert (
        assembled["periods"][2]["stages"]["two_nodes"]
        == specified["periods"][2]["stages"]["two_nodes"]
    )


def test_a_verb_binds_anew_only_the_position_whose_mapping_differs(
    two_nodes_trellis, partly_recalibrated
):
    """calibrate_trellis given a recipe whose record of period 1 holds
    another calibration binds that position alone, which holds the new
    values and stays specified."""
    assert changed_positions(two_nodes_trellis, partly_recalibrated) == [(1, "two_nodes")]
    bound = partly_recalibrated["periods"][1]["stages"]["two_nodes"]
    assert dict(bound.bindings.calibration) == {"β": 0.5, "R": 1.02}
    assert repr(bound) == "ElaboratedStage('two_nodes', specified)"


def test_a_verb_keeps_the_calibration_of_its_argument_at_the_position_that_it_binds_anew(
    two_nodes_trellis, partly_recalibrated
):
    """The small trellis keeps β = 0.96 at period 1 after calibrate_trellis
    binds another value there."""
    # calibrate_trellis binds β = 0.5 at period 1, so that the comparison
    # below is about a position that the verb bound anew.
    bound = partly_recalibrated["periods"][1]["stages"]["two_nodes"]
    assert dict(bound.bindings.calibration) == {"β": 0.5, "R": 1.02}
    stage = two_nodes_trellis["periods"][1]["stages"]["two_nodes"]
    assert dict(stage.bindings.calibration) == {"β": 0.96, "R": 1.02}


def test_a_verb_copies_a_position_at_which_the_syntactic_trellis_holds_a_stage_object(
    two_nodes_recipe, two_nodes_trellis
):
    """A trellis verb copies a position at which the syntactic trellis holds
    a stage object in place of a record, since no mapping stands there to
    bind with."""
    placed = two_nodes_trellis["periods"][2]["stages"]["two_nodes"]
    by_hand = {
        **two_nodes_recipe,
        "periods": [
            *two_nodes_recipe["periods"][:2],
            {"stages": {"two_nodes": placed}, "connectors": []},
        ],
    }
    assert (
        changed_positions(two_nodes_trellis, calibrate_trellis(two_nodes_trellis, by_hand)) == []
    )


def test_a_verb_refuses_a_syntactic_trellis_of_other_positions(two_nodes_recipe, small_steps):
    """calibrate_trellis refuses under `trellis-file-shape` a second argument
    of fewer periods than the trellis that it binds."""
    shorter = {"periods": two_nodes_recipe["periods"][:2], "inter_connectors": [{}]}
    with pytest.raises(FactoryError) as refused:
        calibrate_trellis(small_steps["elaborated"], shorter)
    assert refused.value.rule == "trellis-file-shape" and "second argument" in str(refused.value)


def test_a_verb_refuses_a_first_argument_that_holds_records(two_nodes_recipe):
    """calibrate_trellis refuses under `record-shape` a first argument that
    holds records in place of stage occurrences."""
    with pytest.raises(FactoryError) as refused:
        calibrate_trellis(two_nodes_recipe, two_nodes_recipe)
    assert refused.value.rule == "record-shape"


def test_a_version_bound_from_a_fill_records_which_of_its_slots_are_bound(
    two_nodes_registry, two_nodes_trellis
):
    """A version that calibrate_trellis binds from a fill records in its
    source lists the calibration slot as bound and the settings slot of the
    elaboration as unbound."""
    filled = load_recipe(two_nodes_registry, "spec.yml", fill={"β": 0.9})
    recalibrated = calibrate_trellis(two_nodes_trellis, filled)
    lists = recalibrated["periods"][1]["stages"]["two_nodes"].provenance["source_lists"]
    assert [
        (entry.get("source", entry.get("slot")), entry.get("bound"))
        for entry in lists["calibration"]
    ] == [("calibration/main", None), ("fill", True)]
    assert [entry["bound"] for entry in lists["settings"] if "slot" in entry] == [False]


def test_a_list_valued_parameter_is_held_as_a_tuple(list_valued_registry):
    """A parameter over a product of sets, written in the calibration file
    as a list, is held as a tuple."""
    # the parameter R_vec of the Benhabib stage is of this kind
    _, model = list_valued_registry
    assert model["periods"][0]["stages"]["two_nodes"].bindings.calibration["w"] == (1.0, 2.0)


def test_a_list_valued_parameter_is_bound_again_only_when_a_fill_changes_its_entries(
    list_valued_registry,
):
    """A fill of a list-valued parameter with the entries that it holds binds
    no position again, and a fill with other entries binds all three."""
    directory, model = list_valued_registry
    same = load_recipe(directory, "spec.yml", fill={"w": [1.0, 2.0]})
    assert changed_positions(model, calibrate_trellis(model, same)) == []
    other = load_recipe(directory, "spec.yml", fill={"w": [1.0, 3.0]})
    assert len(changed_positions(model, calibrate_trellis(model, other))) == 3


def test_methodize_trellis_refuses_other_methods_files_and_accepts_the_occurrence_made_with_them(
    two_nodes_trellis, other_selection
):
    """methodize_trellis refuses under `record-shape` a record that names
    other methods files than those with which its occurrence was constructed,
    and gives no new version of the occurrence constructed with them."""
    switched, rebuilt = other_selection
    with pytest.raises(FactoryError) as refused:
        methodize_trellis(two_nodes_trellis, switched)
    assert refused.value.rule == "record-shape" and "other additions" in refused.value.message
    assert changed_positions(rebuilt, methodize_trellis(rebuilt, switched)) == []


def test_specify_trellis_constructs_anew_every_position_whose_record_names_another_file(
    two_nodes_trellis, other_selection
):
    """specify_trellis with the small trellis as the previous trellis makes
    anew every position whose record names another methods file."""
    _, rebuilt = other_selection
    assert changed_positions(two_nodes_trellis, rebuilt) == [
        (0, "two_nodes"),
        (1, "two_nodes"),
        (2, "two_nodes"),
    ]


def test_an_occurrence_made_anew_with_another_methods_file_differs_only_in_its_handler(
    two_nodes_trellis, other_selection
):
    """Each occurrence made anew from the other methods file is specified and
    keeps the graphs, the calibration, the settings and the position of the
    earlier one, its backward decision builder taking the other handler."""
    _, rebuilt = other_selection
    for (_, _, _, old), (_, _, _, new) in zip(positions(two_nodes_trellis), positions(rebuilt)):
        assert repr(new) == "ElaboratedStage('two_nodes', specified)"
        assert differing_graph_triples(old, new) == []
        assert dict(new.bindings.calibration) == dict(old.bindings.calibration)
        assert dict(new.bindings.settings) == dict(old.bindings.settings)
        handlers = (old.methods["cntn_to_dcsn"].handler, new.methods["cntn_to_dcsn"].handler)
        assert handlers == ("test:backward", "test:other")
        assert dict(new.provenance["position"]) == dict(old.provenance["position"])


def test_specify_trellis_given_again_the_trellis_made_with_another_methods_file_binds_nothing(
    other_selection,
):
    """specify_trellis given again the recipe that names the other methods
    file, with the trellis made from it as the previous trellis, gives no new
    version at any position."""
    switched, rebuilt = other_selection
    assert changed_positions(rebuilt, specify_trellis(switched, rebuilt)) == []


@pytest.mark.parametrize(
    ("elaborated_from", "bound_with", "kind", "count"),
    [
        # the terminal period holds another calibration: two pairs
        pytest.param("recipe", "recipe", "calibration", 2, id="calibration-of-the-recipe"),
        # the versions of the terminal period hold another calibration
        pytest.param("recipe", "recipe", "settings", 2, id="settings-of-the-recipe"),
        # the three records differ in their source lists alone: one pair
        pytest.param("filled", "filled", "calibration", 1, id="calibration-filled"),
        pytest.param("filled", "filled", "settings", 1, id="settings-filled"),
        pytest.param("reordered", "reordered", "calibration", 1, id="calibration-reordered"),
        # the settings of the last period, written in another order, which
        # its version prints: two pairs
        pytest.param("reordered", "reordered", "settings", 2, id="settings-reordered"),
        # the versions of the recipe meet one mapping at the three positions
        # of the filled trellis, but the version of the terminal period
        # records another calibration source: two pairs
        pytest.param("recipe", "filled", "calibration", 2, id="recipe-versions-bound-filled"),
    ],
)
def test_a_trellis_verb_applies_the_stage_verb_once_for_each_distinct_version_and_mapping(
    counted_verbs, elaborated_from, bound_with, kind, count
):
    """A trellis verb applies the stage verb once for each distinct pair of
    the version at a position and the mapping that the syntactic trellis
    holds there."""
    # the counts read the calibration and settings verbs of this table
    assert set(trellis_module._VERBS) == {"calibration", "settings"}
    assert counted_verbs(elaborated_from, bound_with)[kind] == count


@pytest.mark.parametrize("variant", ["recipe", "filled", "reordered"])
@pytest.mark.parametrize(
    ("kind", "verb_name", "trellis_verb"),
    [
        pytest.param("calibration", "calibrate", calibrate_trellis, id="calibration"),
        pytest.param("settings", "configure", configure_trellis, id="settings"),
    ],
)
def test_each_position_that_a_trellis_verb_binds_equals_the_stage_verb_applied_there_alone(
    verb_variants, variant, kind, verb_name, trellis_verb
):
    """Each position that a trellis verb binds equals the stage verb applied
    to the version there alone with its record's mapping, provenance
    included, and is written alike, the order of each mapping's keys and the
    type of each value counting."""
    syntactic = verb_variants[variant]
    records = {(h, key): record for h, key, _, record in positions(syntactic)}
    trellis = trellis_before(syntactic, kind)
    bound = trellis_verb(trellis, syntactic)
    for h, key, _, stage in positions(trellis):
        alone = getattr(stage, verb_name)(records[h, key][kind])
        held = bound["periods"][h]["stages"][key]
        written = (printed_provenance_and_bindings(held), printed_provenance_and_bindings(alone))
        assert held == alone and written[0] == written[1], (kind, h)


@pytest.mark.parametrize("variant", ["recipe", "filled", "reordered"])
def test_methodize_trellis_applies_no_stage_verb_and_binds_no_position(counted_verbs, variant):
    """methodize_trellis applies no stage verb to an occurrence whose methods
    were read with its stage text, and gives no new version."""
    # the counts read the calibration and settings verbs
    assert set(trellis_module._VERBS) == {"calibration", "settings"}
    counted = counted_verbs(variant, variant)
    assert (
        changed_positions(counted["calibrated"], counted["methodized"]) == []
        and counted["after methodize_trellis"] == counted["after calibrate_trellis"]
    )


@pytest.mark.parametrize("variant", ["recipe", "filled", "reordered"])
def test_each_stage_occurrence_bound_by_the_trellis_verbs_holds_builders_of_its_own(
    counted_verbs, variant
):
    """Each of the three stage occurrences that the trellis verbs bind holds
    its own object of builders."""
    specified = counted_verbs(variant, variant)["specified"]
    builders = {id(stored(stage, "_builders")) for _, _, _, stage in positions(specified)}
    assert len(builders) == 3


@pytest.mark.parametrize(
    "bind",
    [
        pytest.param(calibrate_trellis, id="calibrate_trellis"),
        pytest.param(
            lambda held, syntactic: specify_trellis(
                syntactic, previous=held, kinds=("calibration",)
            ),
            id="specify_trellis-with-the-trellis-as-previous",
        ),
    ],
)
def test_binding_a_stage_object_placed_at_two_positions_keeps_what_its_denote_returns(
    two_nodes_recipe, bind
):
    """One stage object placed at two positions whose records hold different
    calibrations is bound at each with its own values, and its `denote()`
    returns afterwards the object that it returned before."""
    first, second = (two_nodes_recipe["periods"][h]["stages"]["two_nodes"] for h in (0, 1))
    assert first["calibration"] != second["calibration"]
    small = {
        "periods": [
            {"stages": {"two_nodes": record}, "connectors": []} for record in (first, second)
        ],
        "inter_connectors": [{}],
    }
    # the occurrence as the record constructs it, its methods file read and
    # nothing bound
    stage = elaborate_stage({**first, "calibration": {}, "settings": {}})
    denotation = stage.denote()
    held = {
        "periods": [{"stages": {"two_nodes": stage}, "connectors": []}] * 2,
        "inter_connectors": [{}],
    }
    bound = bind(held, small)
    assert [dict(place.stage.bindings.calibration) for place in positions(bound)] == [
        first["calibration"],
        second["calibration"],
    ]
    assert stage.denote() is denotation


def test_a_verb_reads_each_record_at_its_position_whatever_the_order_of_the_keys_of_a_period(
    corpus_path, tmp_path
):
    """calibrate_trellis binds each stage occurrence with the record at its
    key when the syntactic trellis lists the keys of the period in another
    order."""
    record = load_stage(corpus_path("cons"))
    other = tmp_path / "other.bl"
    other.write_text(
        corpus_path("cons").read_text(encoding="utf-8").replace("ρ", "σ"), encoding="utf-8"
    )
    first = {**record, "calibration": {"ρ": 6.0}}
    second = {**load_stage(other), "calibration": {"σ": 2.0}}
    elaborated = elaborate_trellis(
        {
            "periods": [{"stages": {"first": first, "second": second}, "connectors": []}],
            "inter_connectors": [],
        }
    )
    reordered = {
        "periods": [{"stages": {"second": second, "first": first}, "connectors": []}],
        "inter_connectors": [],
    }
    calibrated = calibrate_trellis(elaborated, reordered)
    assert [
        (key, dict(stage.bindings.calibration)) for _, key, _, stage in positions(calibrated)
    ] == [
        ("first", {"ρ": 6.0}),
        ("second", {"σ": 2.0}),
    ]
