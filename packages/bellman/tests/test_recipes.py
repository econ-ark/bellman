"""load_recipe and the trellis files that name additions: the records of a
recipe, the source lists and their merge, slots and fills, the registry block,
the stages active at some periods only, the refusals of a recipe, and the
additions and methods that each stage occurrence of a trellis holds."""

import functools
import hashlib
import shutil

import pytest
from application_files import (
    BUFFER_STOCK_PENSION_FOLDER,
    CONS_PORT,
    DURABLES,
    DURABLES_RECIPE_WITHOUT_TENURE,
    RETIREMENT_CHOICE_PENSION_FOLDER,
    ROOT,
)
from stage_builders import stage_from_text
from stage_texts import two_nodes_text_with_changes
from trellises import ADDED_REGISTRY_FILES
from two_sets import one_row_by_default

from bellman.factory.recipe import declared_parameters
from bellman.refusal_examples import TWO_NODES, write_registry
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.stage_answers import entry_perch
from bellman.trellis import (
    derivative_missing,
    elaborate_trellis,
    load_recipe,
    load_trellis,
    methodize_trellis,
    specify_trellis,
    trellis_selection,
)

# the recipe of the two-node stage with its trellis file and its stage file
# named by their paths from the recipe's folder and one calibration source;
# the tests of the two paths remove or change one of the two path lines, and
# `recipe_reading_calibration` replaces its calibration source
ONE_STAGE_RECIPE = (
    "trellis: trellis.yml\nstages:\n  two_nodes:\n"
    "    stage: stages/two_nodes/two_nodes.bl\n"
    "    calibration: {all: [calibration/main]}\n"
)

# the stage `other`, a copy of the two-node stage under another name
OTHER_STAGE = TWO_NODES.replace("two_nodes", "other")

# the folders of the two trellises whose stages take a pension account by an
# addition: the buffer-stock stage over six periods, and the retirement
# choice over fifteen periods with its terminal stage
BUFFER_STOCK_PENSION = ROOT / BUFFER_STOCK_PENSION_FOLDER
RETIREMENT_CHOICE_PENSION = ROOT / RETIREMENT_CHOICE_PENSION_FOLDER

# the addition `methods.bl` that each stage folder of cons-port holds, and the
# three additions that replace it in some trellis files
ADDITION = "methods.bl"
VFI_ADDITION = "methods.vfi.bl"
REFERENCE_ADDITION = "methods.reference.bl"
VFI_REFERENCE_ADDITION = "methods.vfi_reference.bl"

# the two recipes of cons-port and its six trellis files that write each
# record out, each with the addition that it names beside each stage file
CONS_PORT_ADDITIONS = {
    "spec.cons-port.yml": {"cons": ADDITION, "disc": ADDITION, "port": ADDITION},
    "spec.port-cons.yml": {"cons": ADDITION, "disc": ADDITION, "port": ADDITION},
    "trellis.port-cons-vfi.yml": {"cons": VFI_ADDITION, "disc": ADDITION, "port": ADDITION},
    "trellis.reference-cons-only.yml": {
        "cons": REFERENCE_ADDITION,
        "disc": ADDITION,
        "noport": ADDITION,
    },
    "trellis.reference-cons-port.yml": {
        "cons": REFERENCE_ADDITION,
        "disc": ADDITION,
        "port": REFERENCE_ADDITION,
    },
    "trellis.reference-port-cons.yml": {
        "cons": REFERENCE_ADDITION,
        "disc": ADDITION,
        "port": REFERENCE_ADDITION,
    },
    "trellis.reference-port-cons-vfi.yml": {
        "cons": VFI_REFERENCE_ADDITION,
        "disc": ADDITION,
        "port": REFERENCE_ADDITION,
    },
    "trellis.reference-port-only.yml": {"disc": ADDITION, "port": REFERENCE_ADDITION},
}

# the default row is the file trellis.reference-port-cons-vfi.yml, which
# names a different addition for each of its three stages; the other seven
# files are in the complete set
CONS_PORT_FILES = one_row_by_default(
    CONS_PORT_ADDITIONS, default="trellis.reference-port-cons-vfi.yml"
)


def recipe_reading_calibration(source):
    """The recipe of the two-node stage with `source` as its one calibration
    source, beside the settings file and the addition of the small
    registry."""
    return ONE_STAGE_RECIPE.replace("calibration/main", source) + (
        "    settings: {all: [settings/main]}\n    methods: {all: [stages/two_nodes/methods.bl]}\n"
    )


def recipe_restricting_the_stage_to(periods):
    """The recipe of the small registry with the entry of the two-node stage
    restricted to the periods `periods`, written `[lo, hi]`."""
    return ADDED_REGISTRY_FILES["spec.yml"].replace(
        "  two_nodes:\n", f"  two_nodes:\n    periods: {periods}\n"
    )


def occurrences(trellis):
    """`(h, key, stage)` of every position of a trellis, period by period."""
    return [
        (h, key, stage)
        for h, period in enumerate(trellis["periods"])
        for key, stage in period["stages"].items()
    ]


def versions(trellis):
    """The version that the short form of each stage occurrence prints, by
    position `(h, key)`: `symbolic`, `methods` or `specified`."""
    return {(h, key): repr(stage).split(", ", 1)[1][:-1] for h, key, stage in occurrences(trellis)}


def additions_of(stage):
    """The file names of the additions read into a stage occurrence."""
    return [held["path"].rsplit("/", 1)[1] for held in stage.provenance.get("additions", ())]


@pytest.fixture(scope="module")
def syntactic_with_two_slots_bound(two_nodes_registry):
    """The syntactic trellis of the small registry with the slot `$fill`
    bound by a fill keyed by kind and the slot `$terminal` by a calibration
    of R."""
    return load_recipe(
        two_nodes_registry,
        "spec.yml",
        fill={"calibration": {"β": 0.9}, "settings": {"n_k": 20}},
        terminal={"calibration": {"R": 1.05}},
    )


@pytest.fixture(scope="module")
def syntactic_with_a_calibration_fill(two_nodes_registry):
    """The syntactic trellis of the small registry with the slot `$fill`
    bound by a calibration of β and the slot `$terminal` left unbound."""
    return load_recipe(two_nodes_registry, "spec.yml", fill={"calibration": {"β": 0.9}})


@pytest.fixture(scope="module")
def registry_with_a_registry_block(tmp_path_factory):
    """The small registry whose recipe names the source `calibration/ages`
    under its `registry` block, a file that assigns `first_age` and
    `last_age`, names that no stage declares."""
    return write_registry(
        tmp_path_factory.mktemp("registry_block"),
        {
            **ADDED_REGISTRY_FILES,
            "spec.yml": ADDED_REGISTRY_FILES["spec.yml"]
            + "registry:\n  calibration: [calibration/ages]\n",
            "calibration/ages.yml": "calibration:\n  first_age: 20\n  last_age: 70\n",
        },
    )


@pytest.fixture(scope="module")
def syntactic_with_a_registry_block(registry_with_a_registry_block):
    """The syntactic trellis of `registry_with_a_registry_block`, loaded with
    no slot bound."""
    return load_recipe(registry_with_a_registry_block, "spec.yml")


@pytest.fixture(scope="module")
def filled_flat_with_a_registry_name(registry_with_a_registry_block):
    """The syntactic trellis of `registry_with_a_registry_block` with a flat
    fill of `first_age`, a name of the registry block, and of the parameter
    β."""
    return load_recipe(
        registry_with_a_registry_block, "spec.yml", fill={"first_age": 25, "β": 0.9}
    )


@pytest.fixture(scope="module")
def filled_by_kind_with_a_registry_name(registry_with_a_registry_block):
    """The syntactic trellis of `registry_with_a_registry_block` with a fill
    keyed by kind of `first_age`, a name of the registry block."""
    return load_recipe(
        registry_with_a_registry_block, "spec.yml", fill={"calibration": {"first_age": 30}}
    )


@pytest.fixture(scope="module")
def durables_filled_by_kind():
    """The syntactic trellis of the durables route without the tenure stage,
    with a fill keyed by kind of the parameter β and the setting n_a."""
    return load_recipe(
        DURABLES,
        DURABLES_RECIPE_WITHOUT_TENURE,
        fill={"calibration": {"β": 0.93}, "settings": {"n_a": 500}},
    )


@pytest.fixture(scope="module")
def syntactic_with_a_restricted_stage(tmp_path_factory):
    """The syntactic trellis of the small registry with the two-node stage
    restricted to the periods 0 and 1 of the three."""
    directory = write_registry(
        tmp_path_factory.mktemp("interval"),
        {**ADDED_REGISTRY_FILES, "spec.yml": recipe_restricting_the_stage_to([0, 1])},
    )
    return load_recipe(directory, "spec.yml")


@pytest.fixture(scope="module")
def buffer_stock_syntactic():
    """The syntactic trellis of the buffer-stock stage with a pension account:
    six periods of one stage file, the last working period with the additions
    `pension.bl` and `vfi.bl` and the five earlier periods with `pension.bl`
    and `egm.bl`."""
    return load_trellis(BUFFER_STOCK_PENSION / "trellis.yml")


@pytest.fixture(scope="module")
def buffer_stock_elaborated(buffer_stock_syntactic):
    """The elaborated trellis of `buffer_stock_syntactic`."""
    return elaborate_trellis(buffer_stock_syntactic)


@pytest.fixture(scope="module")
def buffer_stock_selection(buffer_stock_elaborated):
    """The selection of the connections of `buffer_stock_elaborated`."""
    return trellis_selection(buffer_stock_elaborated)


@pytest.fixture(scope="module")
def retirement_choice_elaborated():
    """The elaborated trellis of the retirement choice with a pension: fifteen
    periods of the worker's saving stage, the choice stage and the retiree's
    saving stage, and the terminal stage in the terminal period."""
    return elaborate_trellis(load_trellis(RETIREMENT_CHOICE_PENSION / "trellis.yml"))


@pytest.fixture(scope="module")
def retirement_choice_selection(retirement_choice_elaborated):
    """The selection of the connections of `retirement_choice_elaborated`."""
    return trellis_selection(retirement_choice_elaborated)


@pytest.fixture(scope="module")
def choice_occurrence(retirement_choice_elaborated):
    """The occurrence of the choice stage at `periods[1]` of
    `retirement_choice_elaborated`, unioned with its addition
    `pension_choice.bl`."""
    return retirement_choice_elaborated["periods"][1]["stages"]["ret_choice"]


@pytest.fixture(scope="module")
def choice_stage_alone():
    """The choice stage elaborated from its stage file without its
    addition."""
    return elaborate_stage(load_stage(RETIREMENT_CHOICE_PENSION / "stage/choice.bl"))


@pytest.fixture(scope="module")
def specified_cons_port():
    """`specified_cons_port(name)`: the specified trellis of the cons-port
    file `name`, read by `load_recipe` for a recipe and by `load_trellis`
    for a trellis file, made once for each file."""

    def specified(name):
        if name.startswith("spec."):
            return specify_trellis(load_recipe(CONS_PORT, name))
        return specify_trellis(load_trellis(CONS_PORT / name))

    return functools.cache(specified)


@pytest.fixture(scope="module")
def cons_port_selection(specified_cons_port):
    """`cons_port_selection(name)`: the selection of the connections of
    `specified_cons_port(name)`, made once for each file."""
    return functools.cache(lambda name: trellis_selection(specified_cons_port(name)))


# The records of a recipe

# the small registry: its trellis file repeats a period template of the
# two-node stage three times; calibration/main assigns β = 0.96 and R = 1.02,
# calibration/terminal, the source of the range list 0-0, assigns R = 1.04,
# and settings/main assigns n_k = 10


def test_load_recipe_writes_one_period_for_each_repeat_of_the_period_template(
    two_nodes_recipe,
):
    """The trellis file of the small registry repeats its period template three
    times, and the syntactic trellis has three periods."""
    assert len(two_nodes_recipe["periods"]) == 3


def test_load_recipe_repeats_a_single_inter_period_connector_for_each_adjacent_pair(
    two_nodes_recipe,
):
    """The one inter-period connector `{a: k}` of the small registry's trellis
    file stands for each of the two pairs of adjacent periods."""
    assert two_nodes_recipe["inter_connectors"] == [{"a": "k"}, {"a": "k"}]


def test_the_keys_of_a_record_are_its_stage_its_three_mappings_and_its_provenance_in_order(
    two_nodes_recipe,
):
    """A record holds the keys `stage`, `calibration`, `settings`, `methods`
    and `provenance`, in that order."""
    record = two_nodes_recipe["periods"][0]["stages"]["two_nodes"]
    assert list(record) == ["stage", "calibration", "settings", "methods", "provenance"]


def test_without_fills_a_range_list_stands_over_the_all_list_at_the_periods_of_its_range_alone(
    two_nodes_recipe,
):
    """With no slot bound, the range source `calibration/terminal`, read after
    the `all` list, gives its R at the terminal period alone."""
    terminal, later = (two_nodes_recipe["periods"][h]["stages"]["two_nodes"] for h in (0, 1))
    assert (terminal["calibration"], later["calibration"]) == (
        {"β": 0.96, "R": 1.04},
        {"β": 0.96, "R": 1.02},
    )


def test_the_settings_of_a_record_are_those_of_the_files_of_its_settings_list(
    two_nodes_recipe,
):
    """The settings of a record are those of `settings/main`, the one file of
    its settings list."""
    record = two_nodes_recipe["periods"][0]["stages"]["two_nodes"]
    assert record["settings"] == {"n_k": 10}


def test_the_methods_of_a_record_are_the_text_and_the_origin_of_each_addition_of_its_list(
    two_nodes_registry, two_nodes_recipe
):
    """The methods of a record are the additions that its methods list names,
    each as its text and its origin."""
    record = two_nodes_recipe["periods"][0]["stages"]["two_nodes"]
    addition = two_nodes_registry / "stages/two_nodes/methods.bl"
    assert record["methods"] == [
        {"text": addition.read_text(encoding="utf-8"), "origin": str(addition)}
    ]


def test_the_provenance_of_a_record_names_each_addition_of_its_methods_list(
    two_nodes_recipe,
):
    """The methods source list in a record's provenance names the addition
    `stages/two_nodes/methods.bl` of the recipe's methods list."""
    record = two_nodes_recipe["periods"][0]["stages"]["two_nodes"]
    listed = record["provenance"]["source_lists"]["methods"]
    assert [entry["source"] for entry in listed] == ["stages/two_nodes/methods.bl"]


def test_the_provenance_of_a_record_holds_the_path_of_its_stage_file_and_the_digest_of_its_text(
    two_nodes_registry, two_nodes_recipe
):
    """The origin of a record's stage text and of its provenance is the path
    of the stage file in the registry, and the provenance holds the SHA-256
    digest of the text."""
    record = two_nodes_recipe["periods"][0]["stages"]["two_nodes"]
    assert record["stage"]["origin"] == str(two_nodes_registry / "stages/two_nodes/two_nodes.bl")
    assert record["provenance"]["origin"] == record["stage"]["origin"]
    digest = hashlib.sha256(record["stage"]["text"].encode("utf-8")).hexdigest()
    assert record["provenance"]["sha256"] == digest


def test_a_change_to_the_record_of_one_period_changes_the_record_of_no_other(two_nodes_registry):
    """Each record is a dictionary of its own, so that a value changed in the
    calibration of `periods[1]` leaves that of `periods[2]` as it was."""
    syntactic = load_recipe(two_nodes_registry, "spec.yml")
    syntactic["periods"][1]["stages"]["two_nodes"]["calibration"]["β"] = 0.5
    assert syntactic["periods"][2]["stages"]["two_nodes"]["calibration"] == {
        "β": 0.96,
        "R": 1.02,
    }


# The merge of the source lists, slots and fills


def test_each_fill_stands_in_its_slot_over_the_sources_before_it_at_the_periods_of_its_list(
    syntactic_with_two_slots_bound,
):
    """The fill of `$fill` gives β over `calibration/main` at every period, and
    the fill of `$terminal`, which follows `calibration/terminal` in the range
    list `0-0`, gives R at the terminal period alone."""
    terminal, later = (
        syntactic_with_two_slots_bound["periods"][h]["stages"]["two_nodes"] for h in (0, 1)
    )
    assert (terminal["calibration"], later["calibration"]) == (
        {"β": 0.9, "R": 1.05},
        {"β": 0.9, "R": 1.02},
    )


def test_the_settings_part_of_a_fill_keyed_by_kind_stands_in_the_settings_list(
    syntactic_with_two_slots_bound,
):
    """The settings part of a fill keyed by kind stands in the settings list,
    over the value of `settings/main`."""
    record = syntactic_with_two_slots_bound["periods"][0]["stages"]["two_nodes"]
    assert record["settings"] == {"n_k": 20}


def test_a_calibration_file_with_a_parent_is_merged_over_its_parent(tmp_path):
    """The source `calibration/child`, which assigns R beside its key `parent:
    calibration/main`, gives its own R and the parent's β, and its key
    `parent` assigns nothing."""
    directory = write_registry(
        tmp_path / "chained",
        {**ADDED_REGISTRY_FILES, "spec.yml": recipe_reading_calibration("calibration/child")},
    )
    record = load_recipe(directory, "spec.yml")["periods"][0]["stages"]["two_nodes"]
    # calibration/main assigns β = 0.96 and R = 1.02; calibration/child
    # assigns R = 1.03
    assert record["calibration"] == {"β": 0.96, "R": 1.03}


def test_a_settings_file_in_a_calibration_list_is_refused_under_recipe_source(tmp_path):
    """The settings file `settings/main` named in a calibration list is
    refused under `recipe-source`, the message naming the file and the
    list's kind."""
    directory = write_registry(
        tmp_path / "kinds",
        {**ADDED_REGISTRY_FILES, "spec.yml": recipe_reading_calibration("settings/main")},
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert refused.value.rule == "recipe-source"
    assert [
        phrase
        for phrase in ("settings/main", "calibration")
        if phrase not in refused.value.message
    ] == []
    assert str(refused.value).endswith("(rule recipe-source)")


def test_the_calibration_source_list_of_a_record_is_the_all_list_then_the_range_list_of_its_period(
    syntactic_with_a_calibration_fill,
):
    """A record's calibration source list names, in order, the sources and the
    slots of the `all` list and, at the terminal period alone, those of the
    range list `0-0`, each entry of the range list with its range."""
    periods = syntactic_with_a_calibration_fill["periods"]
    terminal = periods[0]["stages"]["two_nodes"]["provenance"]["source_lists"]["calibration"]
    assert [entry.get("source", entry.get("slot")) for entry in terminal] == [
        "calibration/main",
        "fill",
        "calibration/terminal",
        "terminal",
    ]
    assert [entry.get("range") for entry in terminal] == [None, None, "0-0", "0-0"]
    later = periods[1]["stages"]["two_nodes"]["provenance"]["source_lists"]["calibration"]
    assert [entry.get("source", entry.get("slot")) for entry in later] == [
        "calibration/main",
        "fill",
    ]


def test_the_entry_of_each_slot_in_a_source_list_says_whether_a_fill_was_bound_to_it(
    syntactic_with_a_calibration_fill,
):
    """With `$fill` bound and `$terminal` not, the entries of the two slots in
    the terminal record's calibration source list are marked bound and not
    bound."""
    record = syntactic_with_a_calibration_fill["periods"][0]["stages"]["two_nodes"]
    listed = record["provenance"]["source_lists"]["calibration"]
    assert [entry["bound"] for entry in listed if "slot" in entry] == [True, False]


def test_the_entry_of_a_file_in_a_source_list_holds_the_digest_of_the_file(
    two_nodes_registry, syntactic_with_a_calibration_fill
):
    """The entry of `calibration/main` in a record's calibration source list
    holds the SHA-256 digest of the file."""
    record = syntactic_with_a_calibration_fill["periods"][0]["stages"]["two_nodes"]
    entry = record["provenance"]["source_lists"]["calibration"][0]
    digest = hashlib.sha256((two_nodes_registry / "calibration/main.yml").read_bytes()).hexdigest()
    assert entry["sha256"] == digest


def test_the_provenance_of_the_syntactic_trellis_names_the_paths_of_the_recipe_and_trellis_file(
    two_nodes_registry, syntactic_with_a_calibration_fill
):
    """The provenance of the syntactic trellis names the path of the recipe
    and that of the trellis file that the recipe names."""
    provenance = syntactic_with_a_calibration_fill["provenance"]
    assert provenance["recipe"]["path"] == str(two_nodes_registry / "spec.yml")
    assert provenance["trellis"]["path"] == str(two_nodes_registry / "trellis.yml")


@pytest.mark.parametrize(
    "fill, calibration, settings",
    [
        pytest.param({"β": 0.9}, {"β": 0.9, "R": 1.02}, {"n_k": 10}, id="a parameter"),
        pytest.param({"n_k": 4}, {"β": 0.96, "R": 1.02}, {"n_k": 4}, id="a setting"),
    ],
)
def test_a_flat_fill_goes_to_the_lists_of_the_kind_that_the_receiving_stage_declares(
    two_nodes_registry, fill, calibration, settings
):
    """A flat fill of a name that the two-node stage declares as a parameter
    reaches its calibration, and one that it declares as a setting reaches
    its settings."""
    record = load_recipe(two_nodes_registry, "spec.yml", fill=fill)["periods"][1]["stages"][
        "two_nodes"
    ]
    assert record["calibration"] == calibration
    assert record["settings"] == settings


def test_a_flat_fill_of_a_setting_is_read_against_the_selection_of_each_period(tmp_path):
    """Where the portfolio stage's methods list names `methods.bl` at the
    periods 0 to 2 and `methods.reference.bl` at 3 to 5, a flat fill of the
    setting n_k, which each file declares and no period reads together with
    the other, reaches the record of every period, each record naming its
    own selection."""
    cons_port_copy = shutil.copytree(CONS_PORT, tmp_path / "declaration")
    recipe = (cons_port_copy / "spec.port-cons.yml").read_text(encoding="utf-8")
    ranged = recipe.replace(
        "settings: {all: [settings/port_wide]}, methods: {all: [stages/port/methods.bl]}",
        "settings: {all: [settings/port_wide, $fill]}, "
        "methods: {all: [], '0-2': [stages/port/methods.bl], "
        "'3-5': [stages/port/methods.reference.bl]}",
    )
    assert ranged != recipe
    (cons_port_copy / "spec.ranged.yml").write_text(ranged, encoding="utf-8")
    filled = load_recipe(cons_port_copy, "spec.ranged.yml", fill={"n_k": 30})
    ports = [period["stages"]["port"] for period in filled["periods"]]
    assert [record["settings"]["n_k"] for record in ports] == [30] * 6
    named = [
        [entry["source"] for entry in record["provenance"]["source_lists"]["methods"]]
        for record in ports
    ]
    assert named == [["stages/port/methods.bl"]] * 3 + [["stages/port/methods.reference.bl"]] * 3


def test_the_parameters_that_the_recipe_reads_from_a_stage_text_are_those_that_stage_par_lists():
    """The recipe reads a fill against the parameters that `stage.par` lists,
    so that `k_d`, declared at the top of the two-node stage and listed by a
    header as a field, is not among them (rule `parameter-or-field`)."""
    text = two_nodes_text_with_changes()
    assert text.count("R : ℝ₊₊\n") == 1
    text = text.replace("R : ℝ₊₊\n", "R : ℝ₊₊\nk_d : ℝ\n")
    stage = stage_from_text(text, "declared_field.bl")
    assert [row["name"] for row in stage.par.list()] == ["β", "R"]
    assert tuple(declared_parameters(text, "declared_field.bl")) == ("β", "R")


def test_a_fill_of_a_slot_in_a_range_list_stands_at_the_periods_of_its_range_alone(
    two_nodes_registry,
):
    """The fill of `$terminal`, a slot of the range list `0-0` alone, gives R
    at the terminal period and at no other."""
    filled = load_recipe(two_nodes_registry, "spec.yml", terminal={"R": 2.0})
    values_of_r = [
        period["stages"]["two_nodes"]["calibration"]["R"] for period in filled["periods"]
    ]
    assert values_of_r == [2.0, 1.02, 1.02]


@pytest.mark.parametrize(
    "fills, rule, phrases",
    [
        pytest.param(
            {"fill": "β: 0.9"}, "slot-value-not-a-mapping", ("'fill'",), id="a text for a mapping"
        ),
        pytest.param(
            {"fill": {"beta": 0.9}}, "fill-names-nothing", ("'beta'",), id="an undeclared name"
        ),
        pytest.param(
            {"fill": {"β": 0.9, "n_k": 4}},
            "fill-mixes-kinds",
            ("n_k",),
            id="a parameter and a setting in one flat fill",
        ),
        pytest.param(
            {"filling": {"β": 0.9}},
            "recipe-slot-unknown",
            ("'filling'",),
            id="a keyword that names no slot",
        ),
        # the slot $fill stands in no methods list, so a methods part given
        # to it is bound to no stage
        pytest.param(
            {"fill": {"methods": [{"on": "cntn_to_dcsn", "handler": "test:other"}]}},
            "fill-names-nothing",
            ("methods list",),
            id="a methods part",
        ),
        # the slot $terminal stands in a calibration list alone, so a
        # setting names nothing there; a flat key of no kind is answered
        # with the declarations of both kinds
        pytest.param(
            {"terminal": {"n_k": 4}},
            "fill-names-nothing",
            (
                "n_k",
                "as a parameter (two_nodes declares β, R)",
                "as a setting (no stage receives it in a settings list)",
            ),
            id="a setting for a slot of calibration lists alone",
        ),
    ],
)
def test_a_fill_that_is_no_mapping_names_nothing_mixes_kinds_or_names_no_slot_is_refused(
    two_nodes_registry, fills, rule, phrases
):
    """`load_recipe` refuses each fill of the table under its rule, with a
    message that holds the row's phrases and a correction to write."""
    with pytest.raises(FactoryError) as refused:
        load_recipe(two_nodes_registry, "spec.yml", **fills)
    assert refused.value.rule == rule
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []
    assert refused.value.write


# The registry block


def test_the_names_of_the_registry_block_stand_under_the_registry_key_and_in_no_record(
    syntactic_with_a_registry_block,
):
    """The assignments of the source that the recipe's `registry` block names
    stand under the syntactic trellis's `registry` key, and the record of no
    period holds them."""
    assert syntactic_with_a_registry_block["registry"] == {
        "calibration": {"first_age": 20, "last_age": 70}
    }
    held = [
        (h, name)
        for h, period in enumerate(syntactic_with_a_registry_block["periods"])
        for name in ("first_age", "last_age")
        if name in period["stages"]["two_nodes"]["calibration"]
    ]
    assert held == []


def test_the_provenance_of_the_syntactic_trellis_names_the_sources_of_the_registry_block(
    syntactic_with_a_registry_block,
):
    """The provenance of the syntactic trellis names `calibration/ages`, the
    source of the `registry` block."""
    listed = syntactic_with_a_registry_block["provenance"]["registry"]["calibration"]
    assert listed[0]["source"] == "calibration/ages"


@pytest.mark.parametrize(
    "syntactic_fixture, registry_mapping, calibrations",
    [
        pytest.param(
            "filled_flat_with_a_registry_name",
            {"calibration": {"first_age": 25, "last_age": 70}},
            [{"β": 0.9, "R": 1.04}, {"β": 0.9, "R": 1.02}, {"β": 0.9, "R": 1.02}],
            id="a flat fill with a parameter",
        ),
        pytest.param(
            "filled_by_kind_with_a_registry_name",
            {"calibration": {"first_age": 30, "last_age": 70}},
            [{"β": 0.96, "R": 1.04}, {"β": 0.96, "R": 1.02}, {"β": 0.96, "R": 1.02}],
            id="a fill keyed by kind",
        ),
    ],
)
def test_a_fill_of_a_name_of_the_registry_block_changes_the_registry_mapping_and_no_record(
    request, syntactic_fixture, registry_mapping, calibrations
):
    """A fill of `first_age`, a name that the `registry` block admits, changes
    that name in the `registry` mapping, and the calibration of the record of
    each period holds the parameters alone."""
    filled = request.getfixturevalue(syntactic_fixture)
    assert filled["registry"] == registry_mapping
    assert [
        period["stages"]["two_nodes"]["calibration"] for period in filled["periods"]
    ] == calibrations


def test_the_provenance_of_the_registry_block_names_the_slot_whose_fill_gave_a_registry_name(
    filled_flat_with_a_registry_name,
):
    """After a flat fill of `first_age`, the provenance of the `registry` block
    ends with the bound entry of the slot `$fill`, which names `first_age`."""
    listed = filled_flat_with_a_registry_name["provenance"]["registry"]["calibration"]
    assert listed[-1] == {"slot": "fill", "bound": True, "names": ["first_age"]}


# the slot $fill stands second in each list, after the list's file
@pytest.mark.parametrize(
    "syntactic_fixture, key, kind, names",
    [
        pytest.param(
            "durables_filled_by_kind",
            "bequest",
            "calibration",
            [],
            id="the bequest, which declares neither name",
        ),
        pytest.param(
            "durables_filled_by_kind",
            "adjuster_cons",
            "calibration",
            ["β"],
            id="the parameter of a fill keyed by kind",
        ),
        pytest.param(
            "durables_filled_by_kind",
            "adjuster_cons",
            "settings",
            ["n_a"],
            id="the setting of a fill keyed by kind",
        ),
        pytest.param(
            "filled_flat_with_a_registry_name",
            "two_nodes",
            "calibration",
            ["β"],
            id="the parameter of a flat fill with a name of the registry block",
        ),
    ],
)
def test_the_entry_of_a_bound_slot_lists_the_names_of_the_fill_that_its_stage_declares(
    request, syntactic_fixture, key, kind, names
):
    """The entry of the bound slot `$fill` in the terminal record's source
    list of one kind lists, as a list, the names of the fill that the stage
    declares in that kind."""
    record = request.getfixturevalue(syntactic_fixture)["periods"][0]["stages"][key]
    entry = record["provenance"]["source_lists"][kind][1]
    assert entry == {"slot": "fill", "bound": True, "names": names}
    assert type(entry["names"]) is list


# The stages active at some periods only


def test_a_stage_restricted_to_periods_by_its_entry_stands_in_the_records_of_those_alone(
    syntactic_with_a_restricted_stage,
):
    """The two-node stage, which its entry restricts to the periods 0 and 1,
    has a record at those periods and none at `periods[2]`."""
    periods = syntactic_with_a_restricted_stage["periods"]
    assert [list(period["stages"]) for period in periods] == [["two_nodes"], ["two_nodes"], []]


def test_the_provenance_of_a_record_names_an_interval_only_where_the_entry_restricts_its_stage(
    two_nodes_recipe, syntactic_with_a_restricted_stage
):
    """The provenance of a record of a stage that the recipe does not restrict
    holds no key `active`, and that of a restricted stage holds its interval
    under it."""
    unrestricted = two_nodes_recipe["periods"][0]["stages"]["two_nodes"]
    assert "active" not in unrestricted["provenance"]
    restricted = syntactic_with_a_restricted_stage["periods"][0]["stages"]["two_nodes"]
    assert restricted["provenance"]["active"] == [0, 1]


def test_a_stage_restricted_to_periods_that_the_trellis_does_not_hold_is_refused(tmp_path):
    """A stage restricted to the periods 5 to 9 of a trellis of three periods
    is refused under `recipe-template-agreement`, the message naming the
    interval and the number of periods."""
    directory = write_registry(
        tmp_path / "beyond",
        {**ADDED_REGISTRY_FILES, "spec.yml": recipe_restricting_the_stage_to([5, 9])},
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert refused.value.rule == "recipe-template-agreement"
    assert [phrase for phrase in ("5-9", "3 periods") if phrase not in refused.value.message] == []


# The refusals of a recipe and of its period template


def test_a_stage_key_listed_twice_in_a_period_template_is_refused_under_recipe_shape(tmp_path):
    """A period template that lists the stage key `two_nodes` twice is refused
    under `recipe-shape` at the address of the template's stages."""
    directory = write_registry(
        tmp_path / "twice",
        {
            **ADDED_REGISTRY_FILES,
            "period.yml": "name: one_stage\nstages: [two_nodes, two_nodes]\nconnectors: []\n",
        },
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.address, refused.value.written) == (
        "recipe-shape",
        "periods[0].stages",
        "two_nodes",
    )


@pytest.mark.parametrize(
    "listed, rule",
    [
        pytest.param("methods/two_nodes", "recipe-source", id="a YAML file of methods"),
        pytest.param("$method_switch", "recipe-shape", id="a slot"),
    ],
)
def test_a_methods_list_that_names_anything_but_an_addition_is_refused_at_the_list(
    tmp_path, listed, rule
):
    """A methods list names `.bl` additions alone, so the YAML file
    `methods/two_nodes.yml` named in it is refused under `recipe-source` and
    a slot under `recipe-shape`, each at the list's address with a message
    that names an addition and a correction."""
    directory = write_registry(
        tmp_path / "registry",
        {
            **ADDED_REGISTRY_FILES,
            "methods/two_nodes.yml": "stage: two_nodes\nmethods:\n  - on: cntn_to_dcsn\n",
            "spec.yml": ADDED_REGISTRY_FILES["spec.yml"].replace(
                "stages/two_nodes/methods.bl", listed
            ),
        },
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.address, refused.value.written) == (
        rule,
        "stages.two_nodes.methods.all",
        listed,
    )
    assert "addition" in refused.value.message and refused.value.write


def test_a_stage_that_the_recipe_names_and_no_period_holds_is_refused_with_both_files(tmp_path):
    """A recipe entry for the stage `other`, which no period of the trellis
    file holds, is refused under `recipe-template-agreement` at the entry,
    naming the trellis file and the recipe."""
    recipe = ADDED_REGISTRY_FILES["spec.yml"] + (
        "  other:\n    stage: stages/other.bl\n    calibration: {all: [calibration/main]}\n"
    )
    directory = write_registry(
        tmp_path / "named_by_no_period",
        {**ADDED_REGISTRY_FILES, "spec.yml": recipe, "stages/other.bl": OTHER_STAGE},
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.address) == ("recipe-template-agreement", "other")
    assert "trellis.yml" in refused.value.message and "spec.yml" in str(refused.value)


def test_a_stage_that_a_period_template_holds_and_the_recipe_omits_is_refused_with_its_template(
    tmp_path,
):
    """A stage `other` that the period template `period.yml` holds and the
    recipe does not name is refused under `recipe-template-agreement` at its
    position, naming the template, the trellis file and the recipe."""
    directory = write_registry(
        tmp_path / "held_by_a_period",
        {
            **ADDED_REGISTRY_FILES,
            "period.yml": "name: one_stage\nstages: [two_nodes, other]\nconnectors: []\n",
            "stages/other.bl": OTHER_STAGE,
        },
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.address) == (
        "recipe-template-agreement",
        "periods[0].other",
    )
    phrases = (
        f"periods[0] of {directory / 'period.yml'}, named by {directory / 'trellis.yml'}",
        str(directory / "spec.yml"),
    )
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


# The paths that a recipe writes


def test_a_recipe_that_names_no_trellis_file_is_refused_although_its_folder_holds_trellis_yml(
    tmp_path,
):
    """A recipe without the key `trellis:` is refused under `recipe-shape`,
    and the file `trellis.yml` of the recipe's folder is not read in its
    place."""
    directory = write_registry(
        tmp_path / "registry",
        {"spec.yml": ONE_STAGE_RECIPE.replace("trellis: trellis.yml\n", "")},
    )
    assert (directory / "trellis.yml").is_file()
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.file, refused.value.address) == (
        "recipe-shape",
        str(directory / "spec.yml"),
        "trellis",
    )
    assert str(refused.value).endswith(
        ": the recipe names no trellis file; write `trellis: trellis.yml`, the path from this "
        "folder (rule recipe-shape)"
    )


# the small registry holds the stage file at stages/two_nodes/two_nodes.bl,
# and the second row adds a copy at stages/two_nodes.bl
@pytest.mark.parametrize(
    "added, places",
    [
        pytest.param({}, ("stages/two_nodes/two_nodes.bl",), id="the stage's own folder"),
        pytest.param(
            {"stages/two_nodes.bl": TWO_NODES},
            ("stages/two_nodes.bl", "stages/two_nodes/two_nodes.bl"),
            id="the stage's own folder and the folder of the stages",
        ),
    ],
)
def test_an_entry_that_names_no_stage_file_is_refused_although_the_key_names_one_in_the_registry(
    tmp_path, added, places
):
    """A recipe entry without the key `stage:` is refused under `recipe-shape`
    at the entry's address, with the line to write, although the registry
    holds the key's stage file at each place of the row."""
    directory = write_registry(
        tmp_path / "registry",
        {
            "spec.yml": ONE_STAGE_RECIPE.replace("    stage: stages/two_nodes/two_nodes.bl\n", ""),
            **added,
        },
    )
    assert [place for place in places if not (directory / place).is_file()] == []
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.file, refused.value.address) == (
        "recipe-shape",
        str(directory / "spec.yml"),
        "stages.two_nodes",
    )
    assert str(refused.value).endswith(
        ": the entry `stages.two_nodes` names no stage file; write "
        "`stage: stages/two_nodes/two_nodes.bl`, the path from this folder (rule recipe-shape)"
    )


def test_a_stage_file_is_read_at_the_path_that_its_entry_writes_whatever_its_name(tmp_path):
    """The entry `stage: models/saving.bl` is read as written, although the
    file's name is not the stage key, and the record's origin is that
    path."""
    elsewhere = write_registry(
        tmp_path / "elsewhere",
        {
            "spec.yml": ONE_STAGE_RECIPE.replace(
                "stage: stages/two_nodes/two_nodes.bl", "stage: models/saving.bl"
            ),
            "models/saving.bl": TWO_NODES,
        },
    )
    record = load_recipe(elsewhere, "spec.yml")["periods"][0]["stages"]["two_nodes"]
    assert record["stage"]["origin"] == str(elsewhere / "models/saving.bl")


@pytest.mark.parametrize(
    "folder, written",
    [
        pytest.param("absent", "stages/absent.bl", id="a path that names no file"),
        pytest.param("yaml", "calibration/main.yml", id="a path that names a YAML file"),
    ],
)
def test_a_stage_path_that_names_no_stage_file_is_refused_as_load_stage_refuses_it(
    tmp_path, folder, written
):
    """An entry whose `stage:` names no file, or no `.bl` file, is refused
    under `readable-file` at the address of the path, with the message and
    the correction of `load_stage`'s refusal of the same path."""
    directory = write_registry(
        tmp_path / folder,
        {
            "spec.yml": ONE_STAGE_RECIPE.replace(
                "stage: stages/two_nodes/two_nodes.bl", f"stage: {written}"
            )
        },
    )
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    with pytest.raises(FactoryError) as direct:
        load_stage(directory / written)
    assert (
        refused.value.rule,
        refused.value.file,
        refused.value.address,
        refused.value.written,
    ) == ("readable-file", str(directory / "spec.yml"), "stages.two_nodes.stage", written)
    assert (refused.value.message, refused.value.write) == (
        direct.value.message,
        direct.value.write,
    )


# The buffer-stock trellis with a pension account


def test_each_occurrence_of_the_buffer_stock_pension_trellis_prints_the_version_methods(
    buffer_stock_elaborated,
):
    """Each of the six elaborated occurrences prints the version `methods`,
    that of an occurrence constructed with its additions and not yet
    calibrated."""
    assert versions(buffer_stock_elaborated) == {(h, "buffer_stock"): "methods" for h in range(6)}


def test_each_occurrence_of_the_buffer_stock_pension_trellis_holds_its_additions_in_order(
    buffer_stock_elaborated,
):
    """The last working period holds the additions `pension.bl` and `vfi.bl`,
    in that order, and each of the five earlier periods `pension.bl` and
    `egm.bl`."""
    stages = [buffer_stock_elaborated["periods"][h]["stages"]["buffer_stock"] for h in range(6)]
    assert additions_of(stages[0]) == ["pension.bl", "vfi.bl"]
    assert all(additions_of(stage) == ["pension.bl", "egm.bl"] for stage in stages[1:])


def test_each_occurrence_of_the_buffer_stock_pension_trellis_holds_the_methods_of_its_additions(
    buffer_stock_elaborated,
):
    """The last working period holds `!vfi` on its decision builder
    `cntn_to_dcsn` and no policy method, each earlier period `!egm` on its
    policy builder and no method on `cntn_to_dcsn`."""
    stages = [buffer_stock_elaborated["periods"][h]["stages"]["buffer_stock"] for h in range(6)]
    assert stages[0].methods["cntn_to_dcsn"].word == "!vfi" and "policy" not in stages[0].methods
    assert all(
        stage.methods["policy"].word == "!egm" and "cntn_to_dcsn" not in stage.methods
        for stage in stages[1:]
    )


def test_the_inter_period_connector_reaches_the_pension_balance_only_where_its_addition_is_read(
    buffer_stock_syntactic, buffer_stock_selection
):
    """The connector `{a: k, q: p}` pairs both fields and nothing is reported
    while `pension.bl`, which adds the balance `p`, is read at every
    occurrence, and the connector is reported under `endpoint-unresolved`
    once the last working period's record names no addition."""
    pairs = {(pair.writing.field, pair.reading.field) for pair in buffer_stock_selection.pairs}
    assert pairs == {("a", "k"), ("q", "p")}
    assert buffer_stock_selection.diagnostics == ()
    periods = [dict(period) for period in buffer_stock_syntactic["periods"]]
    record = periods[0]["stages"]["buffer_stock"]
    periods[0] = {**periods[0], "stages": {"buffer_stock": {**record, "methods": []}}}
    partial = {**buffer_stock_syntactic, "periods": periods}
    unresolved = [
        diagnostic
        for diagnostic in trellis_selection(elaborate_trellis(partial)).diagnostics
        if diagnostic.rule == "endpoint-unresolved"
    ]
    assert [diagnostic.address for diagnostic in unresolved] == ["inter_connectors[0]"]
    assert "'p' names no arrival state field of periods[0]" in unresolved[0].message


def test_every_route_of_the_buffer_stock_pension_trellis_is_certified(buffer_stock_selection):
    """Each of the five routes between the six periods is certified."""
    assert [route.status for route in buffer_stock_selection.routes] == ["certified"] * 5


def test_every_derivative_that_a_line_of_the_buffer_stock_pension_trellis_reads_is_stated(
    buffer_stock_elaborated, buffer_stock_selection
):
    """The derivative `D_{a}V[>]` that the line of the endogenous grid method
    reads is stated by the occurrence that supplies it, so that
    `derivative_missing`, which follows each route, reports nothing."""
    assert buffer_stock_selection.routes
    assert derivative_missing(buffer_stock_elaborated, buffer_stock_selection) == ()


def test_methodize_trellis_returns_a_trellis_equal_to_the_elaborated_buffer_stock_trellis(
    buffer_stock_syntactic, buffer_stock_elaborated
):
    """`methodize_trellis` returns a trellis equal to the elaborated trellis,
    whose occurrences hold the additions that their records name."""
    assert methodize_trellis(buffer_stock_elaborated, buffer_stock_syntactic) == (
        buffer_stock_elaborated
    )


# The retirement choice with a pension


def test_the_retirement_choice_pension_trellis_holds_forty_six_stage_occurrences(
    retirement_choice_elaborated,
):
    """The trellis holds three stages in each of its fifteen periods and the
    terminal stage in the terminal period: 3 × 15 + 1 = 46 occurrences."""
    assert len(occurrences(retirement_choice_elaborated)) == 46


def test_each_occurrence_of_the_retirement_choice_trellis_but_the_terminal_stage_prints_methods(
    retirement_choice_elaborated,
):
    """Every elaborated occurrence prints the version `methods` apart from the
    terminal stage, which prints `symbolic`."""
    printed = versions(retirement_choice_elaborated)
    assert {
        printed_version for (h, key), printed_version in printed.items() if key != "terminal"
    } == {"methods"}
    assert printed[0, "terminal"] == "symbolic"


def test_the_trellis_enters_the_choice_stage_at_the_arrival_perch_that_its_addition_adds(
    choice_stage_alone, choice_occurrence
):
    """The choice stage alone is entered at its decision perch, and its
    occurrence with the addition `pension_choice.bl` at its arrival
    perch."""
    # `entry_perch` answers the perch at which a trellis joins a stage to the
    # stage before it: the arrival perch where the stage's header names one,
    # and the decision perch otherwise
    assert (entry_perch(choice_stage_alone), entry_perch(choice_occurrence)) == ("dcsn", "arvl")


def test_the_choice_occurrence_holds_the_backward_arrival_builder_that_the_stage_alone_lacks(
    choice_stage_alone, choice_occurrence
):
    """The backward builder `dcsn_to_arvl` stands in the choice occurrence with
    the addition `pension_choice.bl` and not in the choice stage alone."""
    assert "dcsn_to_arvl" in choice_occurrence.builder.bwd.list()
    assert "dcsn_to_arvl" not in choice_stage_alone.builder.bwd.list()


def test_the_choice_occurrence_holds_the_one_addition_that_its_record_names(choice_occurrence):
    """The choice occurrence at `periods[1]` holds the addition
    `pension_choice.bl` and no other."""
    assert additions_of(choice_occurrence) == ["pension_choice.bl"]


def test_the_period_connector_reaches_the_arrival_fields_that_the_choice_stage_addition_adds(
    retirement_choice_selection,
):
    """The connector `{y_f: a, y_p: p}` reaches the arrival fields `a` and `p`
    of the choice stage, which its addition adds."""
    into_choice = {
        pair.reading.field
        for pair in retirement_choice_selection.pairs
        if pair.reading.key == "ret_choice"
    }
    assert into_choice == {"a", "p"}


def test_the_three_routes_into_the_terminal_stage_from_the_choice_and_the_retiree_are_certified(
    retirement_choice_selection,
):
    """The routes into the terminal stage, one from each branch of the choice
    and one from the retiree's saving stage, are certified."""
    terminal = [
        route
        for route in retirement_choice_selection.routes
        if route.destination == (0, "terminal")
    ]
    assert [route.status for route in terminal] == ["certified"] * 3
    assert {route.source[1] for route in terminal} == {"ret_choice", "retiree_saving"}


# The trellis files and the recipes of cons-port


@pytest.mark.parametrize("name", CONS_PORT_FILES)
def test_every_occurrence_of_a_cons_port_file_is_specified(specified_cons_port, name):
    """Every occurrence of the specified trellis of each cons-port file prints
    the version `specified`."""
    assert set(versions(specified_cons_port(name)).values()) == {"specified"}


@pytest.mark.parametrize("name", CONS_PORT_FILES)
def test_each_occurrence_of_a_cons_port_file_holds_the_addition_that_the_file_names_for_it(
    specified_cons_port, name
):
    """Each occurrence of the specified trellis holds the one addition that
    the file names beside its stage file, and each stage of the table has
    an occurrence."""
    held = {
        (key, tuple(additions_of(stage)))
        for _, key, stage in occurrences(specified_cons_port(name))
    }
    assert held == {(key, (addition,)) for key, addition in CONS_PORT_ADDITIONS[name].items()}


@pytest.mark.parametrize("name", CONS_PORT_FILES)
def test_every_route_of_a_cons_port_file_is_certified(cons_port_selection, name):
    """Every route of the specified trellis of each cons-port file is
    certified."""
    assert {route.status for route in cons_port_selection(name).routes} == {"certified"}


@pytest.mark.parametrize("name", CONS_PORT_FILES)
def test_the_selection_of_the_connections_of_a_cons_port_file_reports_nothing(
    cons_port_selection, name
):
    """The selection of the connections of each cons-port file's specified
    trellis, which holds the routes of the trellis, holds no diagnostic."""
    assert cons_port_selection(name).routes
    assert cons_port_selection(name).diagnostics == ()


@pytest.mark.parametrize("name", CONS_PORT_FILES)
def test_every_derivative_that_a_line_of_a_cons_port_file_reads_is_stated(
    specified_cons_port, cons_port_selection, name
):
    """`derivative_missing`, which follows each route of the selection,
    reports nothing for the specified trellis of each cons-port file."""
    assert cons_port_selection(name).routes
    assert derivative_missing(specified_cons_port(name), cons_port_selection(name)) == ()


@pytest.mark.parametrize(
    "name, builder, word",
    [
        pytest.param(
            "trellis.port-cons-vfi.yml",
            "cntn_to_dcsn",
            "!vfi",
            id="the trellis file with value function iteration",
        ),
        pytest.param(
            "spec.port-cons.yml",
            "policy",
            "!egm",
            id="the recipe with the endogenous grid method",
        ),
    ],
)
def test_the_consumption_stage_of_a_cons_port_file_holds_the_method_that_its_addition_types(
    specified_cons_port, name, builder, word
):
    """At `periods[0]`, the consumption stage of `trellis.port-cons-vfi.yml`
    holds `!vfi` on its decision builder `cntn_to_dcsn`, and that of
    `spec.port-cons.yml` holds `!egm` on its policy builder."""
    stage = specified_cons_port(name)["periods"][0]["stages"]["cons"]
    assert stage.methods[builder].word == word


def test_a_portfolio_selection_that_states_no_derivative_is_reported_at_each_supplying_period(
    tmp_path,
):
    """With `methods.without_marginals.bl`, which states no derivative of the
    value, in place of `methods.reference.bl` at every portfolio occurrence,
    the reading `D_{a}V[>]` of the consumption stage's policy block is
    reported under `derivative-missing` at each portfolio occurrence that
    supplies it, and refused nowhere."""
    cons_port_copy = shutil.copytree(CONS_PORT, tmp_path / "declaration")
    without_marginals = cons_port_copy / "trellis.reference-port-cons.yml"
    without_marginals.write_text(
        without_marginals.read_text(encoding="utf-8").replace(
            "stages/port/methods.reference.bl", "stages/port/methods.without_marginals.bl"
        ),
        encoding="utf-8",
    )
    reported = derivative_missing(specify_trellis(load_trellis(without_marginals)))
    # the portfolio stage of periods[h], for h from 0 to 4, supplies the value
    # that the consumption stage of periods[h + 1] reads; the consumption
    # stage of the terminal period reads the boundary data of that period
    assert [(item.rule, item.address) for item in reported] == [
        ("derivative-missing", f"periods[{h}].stages['port']") for h in range(5)
    ]
    # disc, the stage between the two, passes the value through
    phrases = ("block 'policy' reads `D_{a}V[>]`", "through the pass-through of disc")
    assert [
        (item.address, phrase)
        for item in reported
        for phrase in phrases
        if phrase not in item.message
    ] == []
    # the candidate is the decision value of the portfolio stage at k
    assert {item.candidates for item in reported} == {("port:function:dcsn:V", "k")}


def test_two_selections_of_the_portfolio_stage_stacked_at_one_stage_are_refused_with_both_files():
    """The portfolio stage read with `methods.bl` and `methods.reference.bl`
    together is refused under `declared-twice`, the refusal naming the line
    of each file."""
    port = CONS_PORT / "stages/port"
    stacked = [port / "methods.bl", port / "methods.reference.bl"]
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(load_stage(port / "port.bl", stacked))
    assert refused.value.rule == "declared-twice"
    # line 26 of methods.bl and line 20 of methods.reference.bl each give the
    # handler of the policy builder
    places = ("methods.bl:26", "methods.reference.bl:20")
    assert [place for place in places if place not in str(refused.value)] == []


def test_two_selections_of_the_portfolio_stage_stacked_through_a_recipe_are_refused_at_each_period(
    tmp_path,
):
    """A recipe whose portfolio methods list names `methods.bl` and
    `methods.reference.bl` together is refused under `declared-twice` by
    `elaborate_trellis`, the refusal naming the second file and, in its
    notes, every portfolio occurrence."""
    cons_port_copy = shutil.copytree(CONS_PORT, tmp_path / "declaration")
    recipe = (cons_port_copy / "spec.port-cons.yml").read_text(encoding="utf-8")
    (cons_port_copy / "spec.stacked.yml").write_text(
        recipe.replace(
            "methods: {all: [stages/port/methods.bl]}",
            "methods: {all: [stages/port/methods.bl, stages/port/methods.reference.bl]}",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_trellis(load_recipe(cons_port_copy, "spec.stacked.yml"))
    assert refused.value.rule == "declared-twice" and "methods.reference.bl" in str(refused.value)
    occurrences_named = ", ".join(f"periods[{h}].stages['port']" for h in range(6))
    assert refused.value.__notes__ == ["Affected stage occurrences: " + occurrences_named]
