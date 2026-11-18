"""The binding verbs `calibrate`, `methodize` and `configure` and the function
`bind_stage`: the parameters and settings that they bind, the tables
`stage.par` and `stage.settings`, the versions of a stage, the answers that a
copy of a stage carries, and the settings that the stages of a period share."""

import copy
import gc
import types
from operator import attrgetter

import pytest
import yaml
from application_files import (
    FIRST_CALIBRATIONS,
    METHODS_SOURCES_BY_STAGE,
    SECOND_CALIBRATIONS,
    SETTINGS_SOURCES_BY_STAGE,
    STAGES_WITH_BINDINGS,
)
from discopy.frobenius import Bubble
from printed_text import cards_of_every_handle
from stage_builders import differing_graph_triples, stage_from_text
from stage_graphs import GRAPH_TRIPLES
from stage_texts import (
    EGM_STAGE,
    SAVINGS_GRID_SETTINGS,
    SAVINGS_GRID_VALUES,
    SMALL_CONS,
    SMALL_CONS_METHODS,
    changed,
    corpus_text,
)
from two_sets import one_row_by_default

from bellman.factory.period_parameters import period_settings, shared_parameters
from bellman.factory.trellis import positions
from bellman.fold.block_lines import symbols
from bellman.native.hypergraphs import copy_native
from bellman.native.labels import is_wiring
from bellman.native.versions import CARRIED, stored
from bellman.refusal_examples import INVERSE_EULER
from bellman.refusals import ConstructionError, FactoryError, NotConstructed
from bellman.stage import bind_stage, to_source
from bellman.stage.grains import graph_of, operators_of
from bellman.stage.kernels import kernel
from bellman.stage.levels import declared_version
from bellman.stage.sources import load_settings
from bellman.trellis import configure_trellis

# the names that the table of parameters answers itself and that `dir` lists
# beside the parameters: its attributes and one of Python's protocol names
TABLE_ATTRIBUTES = {"version", "list", "view", "keys", "items", "values", "get", "__getitem__"}


# the binding verbs in the order in which the tests of the verbs bind `cons`,
# each with the key of its source in `cons_sources`, which is also the name of
# the binding it adds
VERB_ORDER = ("methodize", "configure", "calibrate")
SOURCE_OF = {"methodize": "methods", "configure": "settings", "calibrate": "calibration"}


# a calibration of the tenure stage of the durables application, at values
# inside its declared sets taken from the durables calibration; the income
# level Y and the retirement income y_R are tables with one entry for each of
# the 52 ages of the set {20, …, 71} that the stage declares
TENURE_CALIBRATION = {
    "R": 1.045,
    "R_H": 1.0,
    "δ": 0.0,
    "ρ_z": 0.82,
    "σ_z": 0.11,
    "Y": [1.0] * 52,
    "y_R": [0.0] * 52,
}


@pytest.fixture(scope="module")
def cons_with_three_more_parameters():
    """The stage of `cons` with three more parameters, calibrated: `list`,
    the name of a verb of the table, at 2.0; `lambda`, a keyword of Python,
    at 3.0; and `ℓ`, which Python reads as `l` when it reads the source, at
    4.0."""
    declared = "ρ : [1, inf)\n"
    text = changed(
        corpus_text("cons"), (declared, declared + "list : ℝ₊₊\nlambda : ℝ₊₊\nℓ : ℝ₊₊\n")
    )
    stage = stage_from_text(text, "cons_named.bl")
    return stage.calibrate({"ρ": 6.0, "list": 2.0, "lambda": 3.0, "ℓ": 4.0})


@pytest.fixture(scope="module")
def cons_with_a_setting_named_n_points(cons_methodized, cons_configured):
    """A copy of the methodized `cons` configured with the settings of
    `cons_configured` and one more, `n-points` at 5, a name that is no
    Python identifier."""
    configured = {name: record.value for name, record in cons_configured.settings.items()}
    return copy_native(cons_methodized).configure({**configured, "n-points": 5})


@pytest.fixture(scope="module")
def egm_stage_configured(egm_stage_with_savings_grid_settings):
    """A copy of `egm_stage_with_savings_grid_settings` configured with values
    of its seven settings and of one more name, `n_k`, that no file
    declares."""
    return copy_native(egm_stage_with_savings_grid_settings).configure(
        {"settings": {**SAVINGS_GRID_VALUES, "n_k": 8}}
    )


@pytest.fixture(scope="module")
def cons_calibrated_from_a_mapping(cons_methodized, cons_sources):
    """A copy of the methodized `cons` calibrated from the mapping that the
    application's calibration file holds."""
    values = yaml.safe_load(cons_sources["calibration"].read_text(encoding="utf-8"))
    return copy_native(cons_methodized).calibrate(values)


@pytest.fixture(scope="module")
def cons_with_an_unread_setting(cons):
    """A copy of `cons` methodized by a methods file that declares the three
    settings of a grid of resources and types a linear representation on
    that grid at the decision builder's Evaluation, the methods file of the
    small stage `cons`, and configured with
    those settings and one more, `unused`, that nothing reads."""
    settings = {"n_m": 8, "m_min": 0.1, "m_max": 10.0, "unused": 99}
    return copy_native(cons).methodize(SMALL_CONS_METHODS).configure({"settings": settings})


@pytest.fixture(scope="module")
def calibrated_twice_and_once():
    """`calibrated_twice_and_once(name, stage)`: two copies of the corpus
    stage `stage` named `name`, the first calibrated by its corpus
    calibration and then by its second calibration, the other by the second
    alone; made once for each stage."""
    made = {}

    def make(name, stage):
        if name not in made:
            twice = (
                copy_native(stage)
                .calibrate(FIRST_CALIBRATIONS[name])
                .calibrate(SECOND_CALIBRATIONS[name])
            )
            once = copy_native(stage).calibrate(SECOND_CALIBRATIONS[name])
            made[name] = (twice, once)
        return made[name]

    return make


@pytest.fixture(scope="module")
def configured_twice_and_once():
    """`configured_twice_and_once(name, stage)`: three copies of the corpus
    stage `stage` named `name`, methodized by its corpus methods: the first
    configured by its corpus settings, the second configured by those
    settings and then by the same settings with `n_m` at 33, and the third
    by the second settings alone; made once for each stage."""
    made = {}

    def make(name, stage):
        if name not in made:
            methodized = copy_native(stage).methodize(METHODS_SOURCES_BY_STAGE[name])
            first = copy_native(methodized).configure(SETTINGS_SOURCES_BY_STAGE[name])
            changed = {**load_settings(SETTINGS_SOURCES_BY_STAGE[name]), "n_m": 33}
            twice = copy_native(first).configure(changed)
            once = copy_native(methodized).configure(changed)
            made[name] = (first, twice, once)
        return made[name]

    return make


def bound_before(stage, sources, verb):
    """A copy of `stage` bound by the verbs that come before `verb` in
    `VERB_ORDER`, each from its source in `sources`."""
    copied = copy_native(stage)
    for earlier in VERB_ORDER[: VERB_ORDER.index(verb)]:
        getattr(copied, earlier)(sources[SOURCE_OF[earlier]])
    return copied


def three_bindings(stage):
    """The calibration, the settings and the methods files that `stage`
    holds, by the name of each binding."""
    return {
        "calibration": stage.bindings.calibration,
        "settings": stage.bindings.settings,
        "methods": stage.provenance.get("additions"),
    }


# A version keeps the answers that it has computed, such as its graphs at each
# grain, the wire table that its drawings read, the construction table of its
# definitions, the places of its methods and the bubbles of its graphs, under
# the attribute `_kept`; `copy_native` carries them to the copy, rewritten to
# refer to the objects of the copy.
def ask_every_answer(version):
    """Ask `version` for every graph at every grain, the kernel of every
    primitive operator by its name, the primitive operators and the card of
    every builder, its conditions and its diagnostics, so that it keeps
    those answers. A graph whose construction is refused is left out."""
    for level, direction, grain in GRAPH_TRIPLES:
        try:
            graph_of(version, level, direction, grain)
        except NotConstructed:
            continue
    for box in operators_of(version):
        kernel(version, box.name)
    for graph in (version.builder.bwd, version.builder.fwd):
        try:
            builders = graph.graph.boxes
        except NotConstructed:
            continue
        for box in builders:
            graph[box.name].primitives.list()
            str(graph[box.name].denote())
    version.obligations()
    version.diagnostics()


@pytest.fixture(scope="module")
def tenure_and_its_bound_copy():
    """The tenure stage, asked for every answer and then calibrated, and the
    copy of it that `copy_native` makes, which carries those answers."""
    version = stage_from_text(corpus_text("tenure"), "tenure.bl")
    ask_every_answer(version)
    # `calibrate` binds the stage it is called on, so the bound version whose
    # answers the tests read is the copy of it
    return version, copy_native(version.calibrate(TENURE_CALIBRATION))


def ask_the_graphs_of_the_carried_places_and_bubbles(bound):
    """Ask the copy `bound` for its graph at the grain of each place and of
    each bubble that it carries, as the tests of the places and of the
    bubbles ask it, so that a test that reads the carried answers reads them
    after those calls."""
    kept = vars(bound)["_kept"]
    for place in kept["places"]:
        graph_of(bound, place.level, place.direction, place.grain)
    for key in [key for key in kept if isinstance(key, tuple) and key[0] == "bubble"]:
        graph_of(bound, key[1], key[2], key[4])


def boxes_with_those_in_bubbles(graph):
    """Every box of a graph, the boxes inside its bubbles included."""
    found, pending = [], list(graph.boxes)
    while pending:
        box = pending.pop()
        found.append(box)
        if isinstance(box, Bubble):
            pending.extend(box.arg.boxes)
    return found


def is_one_of(box, boxes):
    """Whether `box` is, as an object, one of `boxes`."""
    return any(box is other for other in boxes)


def objects_held(value):
    """The ids of the objects that `value` holds, itself included; strings,
    numbers, classes, functions, modules and the empty containers that
    Python shares excepted."""
    shared = (
        str,
        bytes,
        int,
        float,
        complex,
        type,
        type(None),
        types.FunctionType,
        types.BuiltinFunctionType,
        types.MethodType,
        types.ModuleType,
    )
    found, pending = set(), [value]
    while pending:
        item = pending.pop()
        if (
            isinstance(item, shared)
            or type(item) in (tuple, frozenset)
            and not item
            or id(item) in found
        ):
            continue
        found.add(id(item))
        pending.extend(gc.get_referents(item))
    return found


def small_cons_bound_after_printing():
    """The small stage `cons` with every card printed while it is symbolic
    and again once it is calibrated, and then methodized, with the cards
    printed while it was symbolic. The verbs bind the one stage in place."""
    stage = stage_from_text(SMALL_CONS, "cons.bl")
    before = cards_of_every_handle(stage)
    stage.calibrate(FIRST_CALIBRATIONS["cons"])
    cards_of_every_handle(stage)
    stage.methodize(SMALL_CONS_METHODS)
    return before, stage


def source_with_unvalued_settings(sources):
    """A source of `bind_stage` with the calibration file and the methods
    file of `sources` and settings that value none of the settings that the
    methods file declares."""
    return {
        "calibration": str(sources["calibration"]),
        "methods": str(sources["methods"]),
        "settings": {"nonsense": 1},
    }


@pytest.fixture(scope="module")
def binding_with_unvalued_settings(cons, cons_sources):
    """The report of `bind_stage` on `cons` from
    `source_with_unvalued_settings`."""
    return bind_stage(cons, source_with_unvalued_settings(cons_sources))


@pytest.fixture(scope="module")
def binding_with_on_refusal(cons, cons_sources):
    """The report of `bind_stage` on `cons` from
    `source_with_unvalued_settings` with a function `on_refusal` that records
    each call and answers one dictionary, with the list of the calls and
    that dictionary."""
    calls, answer = [], {}

    def on_refusal(error, verb):
        calls.append((error, verb))
        return answer

    source = source_with_unvalued_settings(cons_sources)
    return bind_stage(cons, source, on_refusal=on_refusal), calls, answer


def one_period(*placed):
    """The record of a trellis of one period whose stages, placed by hand
    under the keys `a`, `b` and so on, are `placed`, with no connector."""
    return {
        "periods": [{"stages": dict(zip("ab", placed)), "connectors": []}],
        "inter_connectors": [],
    }


# --- the tables stage.par and stage.settings ---


@pytest.mark.parametrize(
    "version, table, name, value",
    [
        ("cons_calibrated", "par", "ρ", 6.0),
        ("cons_configured", "par", "ρ", 6.0),
        ("cons_configured", "settings", "n_a", 800),
    ],
    ids=["parameter-calibrated", "parameter-specified", "setting-specified"],
)
def test_an_entry_read_as_an_attribute_answers_the_value_that_its_record_holds(
    request, version, table, name, value
):
    """`stage.par.ρ` and `stage.settings.n_a` answer the value, of its own
    type, that the record read by the key holds."""
    entries = getattr(request.getfixturevalue(version), table)
    assert getattr(entries, name) == entries[name].value == value
    assert isinstance(getattr(entries, name), type(value))


@pytest.mark.parametrize(
    "version, table, name, printed",
    [
        ("cons_calibrated", "par", "ρ", "ρ = 6.0 : [1, inf)"),
        (
            "cons_configured",
            "settings",
            "n_a",
            "n_a = 800 : ℕ, read at policy by !egm for its grid !Cartesian",
        ),
        (
            "egm_stage_with_savings_grid_settings",
            "settings",
            "n_a",
            "n_a : ℕ, unbound, read at policy by !egm for its grid !Cartesian",
        ),
    ],
    ids=["parameter-calibrated", "setting-configured", "setting-declared-and-unbound"],
)
def test_the_record_of_an_entry_prints_its_value_its_set_and_its_readers_on_one_line(
    request, version, table, name, printed
):
    """The record of a parameter or a setting prints on one line its name,
    its value or the word `unbound`, its declared set and, for a setting,
    the place, the method and the grid that read it."""
    entries = getattr(request.getfixturevalue(version), table)
    assert str(entries[name]) == printed


def test_reading_a_parameter_stores_nothing_on_the_table_or_the_stage(cons_calibrated):
    """Reading `stage.par.ρ`, the record `stage.par["ρ"]`, its value and its
    print adds no attribute to the table or to the stage."""
    table = cons_calibrated.par
    held = set(vars(cons_calibrated))
    # the reads whose effect the test checks
    table.ρ, table["ρ"].value, str(table["ρ"])
    assert vars(table) == {"version": cons_calibrated}
    assert set(vars(cons_calibrated)) == held


@pytest.mark.parametrize(
    "version", ["cons", "cons_methodized_without_calibration"], ids=["symbolic", "methods-alone"]
)
def test_an_unbound_parameter_is_refused_as_an_attribute_and_its_record_read_by_the_key(
    request, version
):
    """On a version that no calibration binds, `stage.par.ρ` raises an
    `AttributeError` that names the record's key and the verb that binds the
    value, which `hasattr` reads as absent, and the record that the key then
    reads prints the parameter unbound, as the refusal says."""
    table = request.getfixturevalue(version).par
    with pytest.raises(AttributeError) as refused:
        table.ρ
    assert str(refused.value) == (
        "stage 'cons': the parameter 'ρ' has no value on this version, which no calibration "
        'has bound; stage.par["ρ"] answers its record, and calibrate(stage, source) binds '
        "its value"
    )
    assert not hasattr(table, "ρ")
    assert str(table["ρ"]) == "ρ : [1, inf), unbound"


@pytest.mark.parametrize(
    "version, table, name, message",
    [
        (
            "cons_calibrated",
            "par",
            "rho",
            "stage 'cons': 'rho' is no parameter of the stage; a parameter is read by the "
            "name the file declares, and the parameters are ρ",
        ),
        (
            "cons",
            "settings",
            "n_a",
            "stage 'cons': 'n_a' is no setting of this version; its settings are none; a "
            "setting is declared in the methods file, and configure(stage, source) values it",
        ),
    ],
    ids=["no-such-parameter", "no-setting-on-a-stage-without-methods"],
)
def test_reading_a_name_that_a_table_lacks_raises_an_attribute_error_with_the_keys_reason(
    request, version, table, name, message
):
    """Reading as an attribute a name that the table does not hold raises an
    `AttributeError` with the reason that the key gives, so that `hasattr`
    and `getattr` with a default read the name as absent."""
    entries = getattr(request.getfixturevalue(version), table)
    with pytest.raises(AttributeError) as refused:
        getattr(entries, name)
    assert str(refused.value) == message
    assert not hasattr(entries, name)
    assert getattr(entries, name, None) is None


def test_a_shallow_copy_of_the_table_of_parameters_answers_as_the_table_does(cons_calibrated):
    """`copy.copy(stage.par)`, which asks the table for names of Python's
    protocols, answers `ρ` as the table does."""
    assert copy.copy(cons_calibrated.par).ρ == 6.0


def test_the_verb_list_answers_the_table_on_a_stage_with_a_parameter_named_list(
    cons_with_three_more_parameters,
):
    """On a stage that declares a parameter named `list`, `stage.par.list`
    stays the verb, which answers the table that the mapping prints."""
    table = cons_with_three_more_parameters.par
    assert str(table.list()) == str(table)


def test_a_parameter_named_list_is_read_by_its_key(cons_with_three_more_parameters):
    """The parameter named `list` is read by its key, whose record holds its
    value and prints it with its declared set."""
    table = cons_with_three_more_parameters.par
    assert table["list"].value == 2.0
    assert str(table["list"]) == "list = 2.0 : ℝ₊₊"


def test_the_docstring_of_the_attribute_read_of_a_parameter_names_each_table_attribute(
    cons_calibrated,
):
    """The docstring of the attribute read of `stage.par` names each
    attribute of the table, under whose name a parameter is read by its key
    alone."""
    table_type = type(cons_calibrated.par)
    own = {name for name in dir(table_type) if not name.startswith("_")} | {"version"}
    written = table_type.__getattr__.__doc__
    assert [name for name in sorted(own) if f"`{name}`" not in written] == []


@pytest.mark.parametrize(
    "version, table, name",
    [
        ("cons", "par", "ρ"),
        ("cons_calibrated", "par", "ρ"),
        ("cons_configured", "settings", "n_a"),
    ],
    ids=["parameter-symbolic", "parameter-calibrated", "setting-specified"],
)
def test_completion_lists_each_entry_beside_the_own_attributes_of_the_table(
    request, version, table, name
):
    """`dir` of a table, which completion in Jupyter reads, lists an entry
    whose name can be written after a dot beside the attributes and the
    protocol names of the table."""
    entries = getattr(request.getfixturevalue(version), table)
    listed = dir(entries)
    assert name in listed and set(object.__dir__(entries)) <= set(listed)


def test_completion_lists_the_table_attributes_on_a_stage_with_a_parameter_named_list(
    cons_with_three_more_parameters,
):
    """`dir(stage.par)` lists each attribute of the table and `ρ` on a stage
    that declares a parameter named `list`."""
    assert TABLE_ATTRIBUTES | {"ρ"} <= set(dir(cons_with_three_more_parameters.par))


@pytest.mark.parametrize(
    "version, table, written, left_out",
    [
        ("cons_with_three_more_parameters", "par", "ρ", "lambda"),
        ("cons_with_three_more_parameters", "par", "ρ", "ℓ"),
        ("cons_with_a_setting_named_n_points", "settings", "n_a", "n-points"),
    ],
    ids=["parameter-named-lambda", "parameter-that-python-reads-as-l", "setting-with-a-hyphen"],
)
def test_completion_lists_a_name_written_after_a_dot_and_leaves_out_one_that_cannot_be(
    request, version, table, written, left_out
):
    """`dir` of a table lists an entry whose name can be written after a dot
    and leaves out one whose name cannot: a keyword of Python, a name that
    Python rewrites when it reads the source, or a name that is no Python
    identifier."""
    listed = dir(getattr(request.getfixturevalue(version), table))
    assert written in listed
    assert left_out not in listed


@pytest.mark.parametrize(
    "version, table, name, value",
    [
        ("cons_with_three_more_parameters", "par", "lambda", 3.0),
        ("cons_with_three_more_parameters", "par", "ℓ", 4.0),
        ("cons_with_a_setting_named_n_points", "settings", "n-points", 5),
    ],
    ids=["parameter-named-lambda", "parameter-that-python-reads-as-l", "setting-with-a-hyphen"],
)
def test_getattr_reads_an_entry_whose_name_cannot_be_written_after_a_dot(
    request, version, table, name, value
):
    """`getattr` with the name as a string answers the value that the record
    of such an entry holds."""
    entries = getattr(request.getfixturevalue(version), table)
    assert getattr(entries, name) == entries[name].value == value


@pytest.mark.parametrize(
    "version, value",
    [("cons", "unbound"), ("cons_calibrated", 6.0)],
    ids=["symbolic", "calibrated"],
)
def test_the_parameter_listing_gives_each_parameter_its_set_and_its_value_or_unbound(
    request, version, value
):
    """The listing of `stage.par` gives `ρ` its declared set and the word
    `unbound` before calibration, and the bound value after it."""
    rows = request.getfixturevalue(version).par.list()
    assert [(row["name"], to_source(row["domain"]), row["value"]) for row in rows] == [
        ("ρ", "[1, inf)", value)
    ]


def test_the_settings_table_of_a_stage_without_methods_lists_no_setting(cons):
    """`stage.settings.list()` of a stage with no methods bound and no
    settings bound is empty."""
    assert cons.settings.list() == ()


def test_the_settings_listing_gives_declared_then_undeclared_names_with_their_values(
    cons_configured,
):
    """The settings listing gives the settings that the methods file
    declares, in declaration order, then the names that the configuration
    binds and no file declares, each with its bound value."""
    rows = cons_configured.settings.list()
    declared = ["n_a", "a_min", "a_max", "n_m", "m_min", "m_max"]
    bound = cons_configured.bindings.settings
    assert [row["name"] for row in rows] == declared + [
        name for name in bound if name not in declared
    ]
    assert all(row["value"] == bound[row["name"]] for row in rows)


def test_a_row_of_the_settings_listing_cannot_be_changed(cons_configured):
    """Writing a field of a row of the settings listing raises a
    `TypeError`."""
    rows = cons_configured.settings.list()
    with pytest.raises(TypeError):
        rows[0]["name"] = "renamed"


def test_the_settings_listing_gives_each_setting_its_readers_and_an_unread_one_none(
    cons_with_an_unread_setting,
):
    """The settings listing gives each declared setting the place, the
    method and the grid that read it, and leaves these three columns empty
    for a setting that nothing reads."""
    rows = cons_with_an_unread_setting.settings.list()
    assert [row["name"] for row in rows] == ["n_m", "m_min", "m_max", "unused"]
    assert [(row["read at"], row["by"], row["grid"]) for row in rows[:3]] == [
        ("cntn_to_dcsn.evaluate", "!Linear", "!Cartesian")
    ] * 3
    assert (rows[3]["read at"], rows[3]["by"], rows[3]["grid"]) == ("", "", "")


def test_the_card_of_a_configured_stage_names_each_setting_it_binds(cons_with_an_unread_setting):
    """The card of a configured stage names each setting that it binds, the
    one that nothing reads included."""
    card = str(cons_with_an_unread_setting)
    assert [name for name in ("n_m", "m_min", "m_max", "unused") if name not in card] == []


@pytest.mark.parametrize(
    "version, settings",
    [
        ("egm_stage_with_savings_grid_settings", list(SAVINGS_GRID_VALUES)),
        ("egm_stage_configured", [*SAVINGS_GRID_VALUES, "n_k"]),
    ],
    ids=["before-configuration", "after-configuration"],
)
def test_a_declared_setting_is_listed_by_settings_and_never_by_par(request, version, settings):
    """The settings that a methods file declares stand in `stage.settings`,
    and `stage.par` lists none of them, before configuration and after
    it."""
    stage = request.getfixturevalue(version)
    assert list(stage.par) == []
    assert list(stage.settings) == settings


def test_the_view_of_a_stage_shows_the_settings_that_its_methods_file_declares(
    egm_stage_with_savings_grid_settings,
):
    """The view of a stage read with a methods file has a section of
    settings, which shows `n_a` with its set."""
    view = egm_stage_with_savings_grid_settings.view()
    assert [text for text in ("settings", "n_a : ℕ") if text not in view] == []


def test_configure_binds_the_declared_settings_at_the_values_given(egm_stage_configured):
    """The listing of a configured stage gives the first two declared
    settings their sets and the values given, and `stage.settings.n_a`
    answers its value."""
    rows = egm_stage_configured.settings.list()
    assert [(row["name"], to_source(row["domain"]), row["value"]) for row in rows[:2]] == [
        ("n_a", "ℕ", 30),
        ("a_min", "ℝ₊", 0.0),
    ]
    assert egm_stage_configured.settings.n_a == 30


def test_a_value_for_a_name_that_no_file_declares_is_listed_with_no_set_and_no_reader(
    egm_stage_configured,
):
    """A value that the settings source gives for a name that no file
    declares is bound and listed last, with no set and no place that reads
    it, so that nothing is dropped."""
    rows = egm_stage_configured.settings.list()
    assert (rows[-1]["name"], rows[-1]["domain"], rows[-1]["read at"]) == ("n_k", None, "")


# --- calibrate and configure ---


def test_calibrate_binds_the_declared_parameters_alone_from_a_file_with_other_names(
    cons_calibrated,
):
    """Calibrated from the application's calibration file, which values
    other names too, `cons` binds its one declared parameter alone."""
    assert dict(cons_calibrated.bindings.calibration) == {"ρ": 6.0}


def test_a_mapping_with_the_content_of_the_calibration_file_binds_what_the_file_binds(
    cons_calibrated, cons_calibrated_from_a_mapping
):
    """A calibration from the mapping that the calibration file holds binds
    the values that the calibration from the file binds."""
    calibration = cons_calibrated_from_a_mapping.bindings.calibration
    assert calibration == cons_calibrated.bindings.calibration


def test_a_calibration_records_its_operation_and_its_source_alike_for_a_file_or_a_mapping(
    cons_calibrated, cons_calibrated_from_a_mapping
):
    """The provenance of a calibration names the operation `calibrate` and
    the digest of its source, the same for the file and for the mapping
    that the file holds."""
    from_file, from_mapping = cons_calibrated.provenance, cons_calibrated_from_a_mapping.provenance
    assert from_file["operation"] == from_mapping["operation"] == "calibrate"
    assert from_file["source"]["sha256"] == from_mapping["source"]["sha256"]


def test_calibrate_refuses_a_source_without_a_value_for_a_parameter_at_its_declaration(cons):
    """A calibration source with no value for `ρ` is refused at the record
    of the parameter, whose address is the position of its declaration in
    the stage file."""
    with pytest.raises(
        ValueError,
        match=r"parameter 'ρ' \(address "
        r"'applications/portfolio-choice/declaration/stages/cons/cons\.bl:6'\): "
        r"the calibration source supplies no value for it.*write `ρ: <value>`",
    ):
        copy_native(cons).calibrate({})


def test_calibrate_refuses_a_value_outside_the_declared_set_of_its_parameter(cons):
    """A value of `ρ` outside `[1, inf)`, the set that its declaration
    names, is refused."""
    with pytest.raises(
        ValueError,
        match=r"the value 0.5 lies outside the declared set \[1, inf\).*write a value in "
        r"\[1, inf\)",
    ):
        copy_native(cons).calibrate({"ρ": 0.5})


@pytest.mark.parametrize("name", one_row_by_default(STAGES_WITH_BINDINGS))
def test_calibrate_binds_a_complete_source_and_refuses_it_without_its_first_parameter(
    request, name
):
    """On a corpus stage, `calibrate` binds the values of a complete source,
    and refuses the same source without its first parameter at that
    parameter."""
    stage = request.getfixturevalue(name)
    values = FIRST_CALIBRATIONS[name]
    assert dict(copy_native(stage).calibrate(values).bindings.calibration) == values
    first = next(iter(values))
    with pytest.raises(ValueError, match=f"parameter '{first}'"):
        copy_native(stage).calibrate({key: value for key, value in values.items() if key != first})


@pytest.mark.parametrize("name", one_row_by_default(STAGES_WITH_BINDINGS))
def test_a_stage_calibrated_twice_equals_the_stage_calibrated_by_the_second_source(
    request, name, calibrated_twice_and_once
):
    """A corpus stage calibrated twice binds the values of the second
    source and holds the graphs and the definitions of the stage that the
    second source alone calibrates."""
    twice, once = calibrated_twice_and_once(name, request.getfixturevalue(name))
    assert (
        dict(twice.bindings.calibration)
        == dict(once.bindings.calibration)
        == SECOND_CALIBRATIONS[name]
    )
    assert differing_graph_triples(twice, once) == [] and twice.definitions == once.definitions


@pytest.mark.parametrize("name", one_row_by_default(STAGES_WITH_BINDINGS))
def test_a_stage_calibrated_twice_holds_no_methods_and_no_settings(
    request, name, calibrated_twice_and_once
):
    """A corpus stage calibrated twice holds no blocks of methods, no
    settings and no methods file."""
    twice, _ = calibrated_twice_and_once(name, request.getfixturevalue(name))
    assert (twice.bindings.blocks, twice.bindings.settings) == (None, None)
    assert not twice.provenance.get("additions")


def test_configure_binds_the_settings_that_the_methods_name(cons_configured):
    """`configure` from the application's settings file binds the three
    settings that the grid of the decision builder's Evaluation reads."""
    assert {"n_m", "m_min", "m_max"} <= set(cons_configured.bindings.settings)


def test_a_mapping_with_the_content_of_the_settings_file_binds_what_the_file_binds(
    cons_methodized, cons_configured, cons_sources
):
    """A configuration from the mapping that the settings file holds binds
    the settings that the configuration from the file binds."""
    values = yaml.safe_load(cons_sources["settings"].read_text(encoding="utf-8"))
    settings = copy_native(cons_methodized).configure(values).bindings.settings
    assert settings == cons_configured.bindings.settings


def test_configure_binds_the_values_given_to_a_stage_without_methods(cons):
    """On a stage with no methods bound and no settings declared,
    `configure` binds the values given and nothing else."""
    assert dict(copy_native(cons).configure({"n_k": 8}).bindings.settings) == {"n_k": 8}


def test_the_settings_of_the_methodized_cons_are_the_six_that_its_methods_declare(
    cons_methodized,
):
    """The settings that the methodized `cons` declares, and that the
    components of its signatures name, are `n_a`, `a_min`, `a_max`, `n_m`,
    `m_min` and `m_max`, in this order."""
    assert tuple(symbols(cons_methodized)["settings"]) == (
        "n_a",
        "a_min",
        "a_max",
        "n_m",
        "m_min",
        "m_max",
    )


@pytest.mark.parametrize(
    ("source", "first"),
    [
        ({"n_m": 10, "n_a": 10, "a_min": 0.1, "a_max": 1.0}, "m_min"),
        ({}, "n_a"),
    ],
    ids=["source-without-m-min-and-m-max", "empty-source"],
)
def test_configure_refuses_a_source_that_leaves_declared_settings_without_a_value(
    cons_methodized, source, first
):
    """A settings source that gives no value to some of the six settings
    that the methods file declares, to `m_min` and `m_max` or to all six, is
    refused at the first of them in the declared order, with the line to
    write."""
    with pytest.raises(
        ValueError,
        match=rf"setting '{first}': the settings source supplies no value for it.*"
        rf"write `{first}: <value>`",
    ):
        copy_native(cons_methodized).configure(source)


def test_a_refused_configuration_leaves_the_stage_without_settings(cons_methodized):
    """A configuration refused for a setting without a value leaves the
    stage that it was given with no settings bound."""
    stage = copy_native(cons_methodized)
    with pytest.raises(
        ValueError, match="setting 'm_max': the settings source supplies no value for it"
    ):
        stage.configure({"n_a": 10, "a_min": 0.0, "a_max": 5.0, "n_m": 10, "m_min": 0.1})
    assert stage.bindings.settings is None


def test_a_configuration_after_a_refused_one_binds_each_setting_with_its_readers(
    cons_methodized,
):
    """After a configuration refused for a setting without a value,
    `configure` binds each declared setting of the same stage, whose record
    prints its value with the place, the method and the grid that read it,
    and the listing gives `m_min` the decision builder's Evaluation as its
    reader."""
    stage = copy_native(cons_methodized)
    with pytest.raises(
        ValueError, match="setting 'm_max': the settings source supplies no value for it"
    ):
        stage.configure({"n_a": 10, "a_min": 0.0, "a_max": 5.0, "n_m": 10, "m_min": 0.1})
    stage.configure({"n_a": 10, "a_min": 0.0, "a_max": 5.0, "n_m": 10, "m_min": 0.1, "m_max": 9.0})
    assert (
        str(stage.settings["n_a"])
        == "n_a = 10 : ℕ, read at policy by !egm for its grid !Cartesian"
    )
    assert [row["read at"] for row in stage.settings.list() if row["name"] == "m_min"] == [
        "cntn_to_dcsn.evaluate"
    ]


@pytest.mark.parametrize("name", one_row_by_default(STAGES_WITH_BINDINGS))
def test_a_stage_configured_twice_equals_the_stage_configured_by_the_second_source(
    request, name, configured_twice_and_once
):
    """A methodized corpus stage configured twice binds the settings of the
    second source and holds the graphs and the definitions of the stage
    that the second source alone configures."""
    _, twice, once = configured_twice_and_once(name, request.getfixturevalue(name))
    settings = twice.bindings.settings
    assert dict(settings) == dict(once.bindings.settings) and settings["n_m"] == 33
    assert differing_graph_triples(twice, once) == [] and twice.definitions == once.definitions


@pytest.mark.parametrize("name", one_row_by_default(STAGES_WITH_BINDINGS))
def test_a_second_configuration_keeps_the_methods_bound_before(
    request, name, configured_twice_and_once
):
    """A methodized corpus stage configured a second time keeps the methods
    that it held after its first configuration."""
    first, twice, _ = configured_twice_and_once(name, request.getfixturevalue(name))
    assert str(twice.methods) == str(first.methods)


def test_a_second_configuration_keeps_the_blocks_of_lines_bound_before(
    cons, configured_twice_and_once
):
    """`cons`, whose methods file adds a block to the policy builder, keeps
    that block when it is configured a second time."""
    first, twice, _ = configured_twice_and_once("cons", cons)
    assert list(first.bindings.blocks) == ["policy"]
    assert list(twice.bindings.blocks or {}) == list(first.bindings.blocks or {})


@pytest.mark.parametrize(
    "boolean_set, accepted, refused",
    [
        ("{true, false}", False, 0),
        ("{true, false}", True, 1),
        ("{true}", True, False),
        ("{true}", True, 1),
    ],
    ids=[
        "true-or-false-binds-false-and-refuses-0",
        "true-or-false-binds-true-and-refuses-1",
        "true-alone-binds-true-and-refuses-false",
        "true-alone-binds-true-and-refuses-1",
    ],
)
def test_a_boolean_setting_binds_a_boolean_of_its_set_and_refuses_any_other_value(
    cons, boolean_set, accepted, refused
):
    """A setting declared on a set of booleans binds a boolean of the set
    and refuses a value outside it, a number equal to a boolean included,
    since Python's `False == 0` is no membership."""
    addition = {
        "text": f"@methods: cons\nflag : {boolean_set}\n"
        "policy.evaluate.method : !Linear(option=flag)\n",
        "origin": "booleans.methods.bl",
    }
    configured = copy_native(cons).methodize(addition).configure({"flag": accepted})
    assert configured.settings["flag"].value is accepted
    stage = copy_native(cons).methodize(addition)
    with pytest.raises(ConstructionError) as error:
        stage.configure({"flag": refused})
    assert error.value.rule == "setting-outside-set"
    assert "flag" in error.value.message


@pytest.mark.parametrize(
    "values, rule, line, words",
    [
        (
            {**SAVINGS_GRID_VALUES, "a_min": -1.0},
            "setting-outside-set",
            3,
            ("'a_min'", "-1.0", "ℝ₊"),
        ),
        ({**SAVINGS_GRID_VALUES, "n_a": 2.5}, "setting-outside-set", 2, ("'n_a'", "2.5", "ℕ")),
        (
            {name: value for name, value in SAVINGS_GRID_VALUES.items() if name != "n_m"},
            "setting-unvalued",
            6,
            ("'n_m'", "`n_m: <value>`"),
        ),
    ],
    ids=["negative-lower-bound", "count-that-is-no-natural-number", "count-without-a-value"],
)
def test_configure_refuses_a_setting_at_its_declaration_in_the_methods_file(
    egm_stage_with_savings_grid_settings, values, rule, line, words
):
    """`configure` refuses a value outside the declared set of a setting,
    or a declared setting without a value, at the line of its declaration
    in the methods file."""
    # the methods file declares n_a on its second line, a_min on its third
    # and n_m on its sixth
    with pytest.raises(ConstructionError) as refused:
        copy_native(egm_stage_with_savings_grid_settings).configure({"settings": values})
    error = refused.value
    assert (error.rule, error.file, error.line, error.address) == (
        rule,
        "methods.bl",
        line,
        f"methods.bl:{line}",
    )
    assert [word for word in words if word not in error.message] == []


# --- the versions of a stage ---


@pytest.mark.parametrize(
    "version, short_form",
    [
        ("cons", "ElaboratedStage('cons', symbolic)"),
        ("cons_calibrated", "ElaboratedStage('cons', calibrated)"),
        ("cons_methodized", "ElaboratedStage('cons', methodized)"),
        ("cons_configured", "ElaboratedStage('cons', specified)"),
        ("cons_methodized_without_calibration", "ElaboratedStage('cons', methods)"),
    ],
    ids=["symbolic", "calibrated", "methodized", "specified", "methods-alone"],
)
def test_the_short_form_of_a_version_names_what_it_binds(request, version, short_form):
    """The short form of a version of `cons` names its stopping point in
    the recommended order of the verbs, or the binding that it holds where
    it binds out of that order."""
    assert repr(request.getfixturevalue(version)) == short_form


@pytest.mark.parametrize("verb", VERB_ORDER)
def test_a_binding_verb_returns_the_stage_it_is_called_on_with_its_own_binding_changed(
    cons, cons_sources, verb
):
    """Each binding verb returns the stage that it is called on, of whose
    calibration, settings and methods files it changes its own binding
    alone."""
    stage = bound_before(cons, cons_sources, verb)
    before = three_bindings(stage)
    assert getattr(stage, verb)(cons_sources[SOURCE_OF[verb]]) is stage
    after = three_bindings(stage)
    assert [key for key in before if after[key] != before[key]] == [SOURCE_OF[verb]]


@pytest.mark.parametrize("verb", ["configure", "calibrate"])
def test_a_verb_that_binds_values_keeps_the_graphs_and_the_definition_records(
    cons, cons_sources, verb
):
    """`configure` and `calibrate` keep the four graphs and the definition
    records of the stage as the objects that it held before the call."""
    # the four graphs of a stage: its two initial diagrams and its two
    # builders graphs
    views = ("initial.backward", "initial.forward", "builder.bwd", "builder.fwd")
    stage = bound_before(cons, cons_sources, verb)
    graphs = [attrgetter(view)(stage).graph for view in views]
    records = tuple(stage.definitions.values())
    getattr(stage, verb)(cons_sources[SOURCE_OF[verb]])
    assert all(attrgetter(view)(stage).graph is graph for view, graph in zip(views, graphs))
    assert all(a is b for a, b in zip(stage.definitions.values(), records, strict=True))


def test_methodize_builds_declared_graphs_equal_to_those_of_the_symbolic_stage(cons, cons_sources):
    """`methodize` elaborates the stage file with its methods file anew,
    and the graphs of the declared version equal those of the symbolic
    stage."""
    stage = copy_native(cons).methodize(cons_sources["methods"])
    assert differing_graph_triples(declared_version(stage), cons) == []


def test_the_wire_table_that_a_copied_stage_carries_names_the_copy_and_holds_its_blocks(
    tenure_and_its_bound_copy,
):
    """The wire table among the answers that the copy of a calibrated stage
    carries names the copy and holds blocks that the copy stores."""
    _, bound = tenure_and_its_bound_copy
    rendering = vars(bound)["_kept"]["wire_table"]
    blocks = [
        box
        for direction in ("backward", "forward")
        for box in getattr(stored(bound, "initial"), direction).boxes
    ]
    assert rendering.stage is bound
    assert rendering.blocks and all(
        any(block is held for held in blocks) for block in rendering.blocks
    )


@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_the_builders_graph_that_a_copied_stage_carries_is_the_graph_it_stores(
    tenure_and_its_bound_copy, direction
):
    """The builders graph at the builder grain among the answers that the
    copy of a calibrated stage carries is the graph that the copy stores."""
    _, bound = tenure_and_its_bound_copy
    builders_graph = vars(bound)["_kept"][("graph", "builders", direction, "builder")]
    assert builders_graph is getattr(stored(bound, "_builders"), direction)


def test_the_construction_table_that_a_copied_stage_carries_holds_its_own_records(
    tenure_and_its_bound_copy,
):
    """The construction table among the answers that the copy of a
    calibrated stage carries holds the definition records that the copy
    stores."""
    _, bound = tenure_and_its_bound_copy
    definitions = stored(bound, "definitions")
    assert all(
        record is definitions[record.identity]
        for record in vars(bound)["_kept"]["table"].definitions
    )


def test_every_box_of_the_carried_places_is_a_box_of_the_copy_graph_at_that_grain(
    tenure_and_its_bound_copy,
):
    """Every box that the places carried by the copy of a calibrated stage
    list is a box of the copy's graph at the place's grain."""
    _, bound = tenure_and_its_bound_copy
    places = vars(bound)["_kept"]["places"]
    assert places and all(
        is_one_of(
            place.box,
            boxes_with_those_in_bubbles(
                graph_of(bound, place.level, place.direction, place.grain)
            ),
        )
        for place in places
    )


def test_every_box_inside_a_carried_bubble_is_a_box_of_the_copy_graph_at_its_grain(
    tenure_and_its_bound_copy,
):
    """Every box but the wiring inside a bubble that the copy of a
    calibrated stage carries is a box of the copy's graph at the bubble's
    grain."""
    _, bound = tenure_and_its_bound_copy
    bubbles = [
        (key, bubble)
        for key, bubble in vars(bound)["_kept"].items()
        if isinstance(key, tuple) and key[0] == "bubble"
    ]
    assert bubbles and all(
        is_one_of(box, boxes_with_those_in_bubbles(graph_of(bound, key[1], key[2], key[4])))
        for key, bubble in bubbles
        for box in bubble.arg.boxes
        if not is_wiring(box)
    )


@pytest.mark.parametrize("direction", ["backward", "forward"])
@pytest.mark.parametrize("grain", ["primitive", "node", "combined", "factored"])
def test_a_carried_initial_diagram_holds_as_many_boxes_of_its_stored_diagram_as_the_original(
    tenure_and_its_bound_copy, direction, grain
):
    """A carried initial diagram at a finer grain holds as many boxes of the
    initial diagram that the copy stores as the original's holds of the
    diagram that the original stores."""
    version, bound = tenure_and_its_bound_copy
    ask_the_graphs_of_the_carried_places_and_bubbles(bound)
    key = ("graph", "initial", direction, grain)
    ours = [
        box
        for box in boxes_with_those_in_bubbles(vars(bound)["_kept"][key])
        if is_one_of(
            box, boxes_with_those_in_bubbles(getattr(stored(bound, "initial"), direction))
        )
    ]
    theirs = [
        box
        for box in boxes_with_those_in_bubbles(vars(version)["_kept"][key])
        if is_one_of(
            box, boxes_with_those_in_bubbles(getattr(stored(version, "initial"), direction))
        )
    ]
    assert ours and len(ours) == len(theirs)


def test_no_object_that_the_carried_answers_hold_is_an_object_of_the_original(
    tenure_and_its_bound_copy,
):
    """No object that the answers carried by the copy of a calibrated stage
    hold is an object that the original holds."""
    version, bound = tenure_and_its_bound_copy
    ask_the_graphs_of_the_carried_places_and_bubbles(bound)
    assert objects_held(vars(bound)["_kept"]) & objects_held(vars(version)) == set()


def test_the_wire_table_of_the_original_still_names_the_original_after_the_copy(
    tenure_and_its_bound_copy,
):
    """After the copy, the wire table that the original keeps still names
    the original."""
    version, bound = tenure_and_its_bound_copy
    ask_the_graphs_of_the_carried_places_and_bubbles(bound)
    assert vars(version)["_kept"]["wire_table"].stage is version


def test_a_methodized_stage_keeps_only_the_answers_that_a_binding_carries():
    """A stage whose cards were printed before each binding keeps, after
    `methodize` and before it is asked anything, only answers of the kinds
    that a binding carries."""
    _, bound = small_cons_bound_after_printing()
    kept = vars(bound).get("_kept", {})
    assert {key if isinstance(key, str) else key[0] for key in kept} <= CARRIED


def test_a_bound_stage_prints_its_own_cards_as_a_fresh_elaboration_bound_alike():
    """A stage whose cards were printed before each binding prints every
    card as the same text elaborated afresh and bound alike prints it, with
    the bound value of ρ in its parameter's card, which the card printed
    before calibration lacks."""
    before, bound = small_cons_bound_after_printing()
    fresh = (
        stage_from_text(SMALL_CONS, "cons.bl")
        .calibrate(FIRST_CALIBRATIONS["cons"])
        .methodize(SMALL_CONS_METHODS)
    )
    printed = cards_of_every_handle(bound)
    assert printed == cards_of_every_handle(fresh)
    parameter = [text for title, text, _ in printed if title == "cons:parameter:ρ"]
    assert len(parameter) == 1 and "ρ  ∈ [1, ∞),  = 6.0" in parameter[0]
    assert [text for title, text, _ in before if title == "cons:parameter:ρ"] != parameter


def test_the_definitions_listing_of_cons_holds_one_correspondence_and_no_distribution(cons):
    """The definitions listing of `cons` holds the feasibility
    correspondence Γ under its kind and no section of distributions."""
    listing = cons.definitions.list()
    assert list(listing["correspondence"]) == ["cons:correspondence:Γ"]
    assert "distribution" not in listing


def test_each_function_of_the_definitions_listing_is_read_from_the_table_by_its_identity(
    cons,
):
    """Each identity in the section of functions of the definitions listing
    reads from the definitions table the record of that identity."""
    functions = cons.definitions.list()["function"]
    assert functions
    assert all(cons.definitions[identity].identity == identity for identity in functions)


# --- bind_stage ---


def test_bind_stage_reports_the_verbs_that_it_applied_skipped_and_failed(
    binding_with_unvalued_settings,
):
    """`bind_stage` applies the three verbs from a record's sources in their
    order and reports `calibrate` and `methodize` applied and `configure`
    failed."""
    report = binding_with_unvalued_settings
    assert (report.bound, report.skipped, list(report.failed)) == (
        ("calibrate", "methodize"),
        (),
        ["configure"],
    )


def test_bind_stage_reports_a_failed_configuration_with_its_rule_at_the_settings_declaration(
    binding_with_unvalued_settings, cons_sources
):
    """The failure of `configure` names the first setting that the methods
    file declares and the source leaves without a value, at the position of
    its declaration in the methods file, and the rule."""
    failed = binding_with_unvalued_settings.failed["configure"]
    # line 21 and column 1 of the methods file, where `n_a` is declared
    assert failed.startswith(
        f"{cons_sources['methods']}:21:1: stage 'cons', setting 'n_a': the settings source "
        "supplies no value for it; every setting the methods file declares is valued when "
        "settings are bound; write `n_a: <value>` in the settings source"
    )
    assert failed.endswith("; rule setting-unvalued)")


def test_the_stage_of_a_binding_report_holds_the_bindings_of_the_verbs_that_succeeded(
    binding_with_unvalued_settings, cons, cons_sources
):
    """The stage that the report of `bind_stage` answers is a new stage that
    holds the calibration and the methods file and no settings."""
    stage = binding_with_unvalued_settings.stage
    assert stage is not cons
    assert stage.bindings.calibration is not None
    assert stage.provenance.get("additions")
    assert stage.bindings.settings is None
    calibrated = copy_native(cons).calibrate(str(cons_sources["calibration"]))
    assert stage.bindings.calibration == calibrated.bindings.calibration


def test_bind_stage_gives_a_refusal_and_its_verb_to_the_function_on_refusal(
    binding_with_on_refusal, cons_sources
):
    """`bind_stage` calls the function given as `on_refusal` once, with the
    refusal of `configure` and the name of the verb."""
    _, calls, _ = binding_with_on_refusal
    assert len(calls) == 1
    ((error, verb),) = calls
    assert isinstance(error, ConstructionError) and error.rule == "setting-unvalued"
    # the methods file declares `n_a` on its line 21
    assert verb == "configure" and error.file == str(cons_sources["methods"]) and error.line == 21


def test_a_binding_report_holds_the_answer_of_on_refusal_as_the_failure_of_the_verb(
    binding_with_on_refusal,
):
    """The report holds what the function `on_refusal` answers as the
    failure of the verb that it was given."""
    report, _, answer = binding_with_on_refusal
    assert report.failed["configure"] is answer


def test_a_binding_with_on_refusal_binds_the_stage_as_one_without_it(
    binding_with_on_refusal, binding_with_unvalued_settings
):
    """With a function `on_refusal`, `bind_stage` applies and skips the
    verbs and binds the stage as it does without one."""
    with_record, _, _ = binding_with_on_refusal
    report = binding_with_unvalued_settings
    assert (with_record.bound, with_record.skipped) == (report.bound, report.skipped)
    assert with_record.stage.bindings == report.stage.bindings
    stage = with_record.stage
    assert stage.provenance.get("additions") and stage.bindings.settings is None


@pytest.mark.parametrize(
    "on_refusal",
    [None, lambda error, verb: str(error)],
    ids=["without-on-refusal", "with-on-refusal"],
)
def test_bind_stage_changes_neither_its_source_nor_the_stage_that_it_is_given(
    cons, cons_sources, on_refusal
):
    """`bind_stage` leaves the source and the stage that it is given as they
    were, with a function `on_refusal` or without one."""
    source = source_with_unvalued_settings(cons_sources)
    source_before, stage_before = copy.deepcopy(source), cons.encoding()
    bind_stage(cons, source, on_refusal=on_refusal)
    assert source == source_before and cons.encoding() == stage_before


@pytest.mark.parametrize("methods", [{}, []], ids=["empty-mapping", "empty-list"])
def test_bind_stage_from_empty_sources_answers_the_stage_itself_with_every_verb_skipped(
    cons, methods
):
    """From a calibration, methods and settings that supply nothing,
    `bind_stage` answers the stage itself with the three verbs skipped."""
    report = bind_stage(cons, {"calibration": {}, "methods": methods, "settings": {}})
    assert report == (cons, (), ("calibrate", "methodize", "configure"), {})
    # a stage compares equal to its copy, so the stage itself is checked by
    # identity
    assert report.stage is cons


def test_a_failed_calibration_leaves_the_stage_unbound_and_the_next_verb_is_applied(
    cons, cons_sources
):
    """Where `bind_stage` fails to calibrate, it still applies `methodize`,
    and the stage that it answers holds the methods file and no
    calibration."""
    broken = bind_stage(
        cons,
        {"calibration": {"ρ": 0.5}, "methods": str(cons_sources["methods"]), "settings": {}},
    )
    assert (broken.bound, broken.skipped, list(broken.failed)) == (
        ("methodize",),
        ("configure",),
        ["calibrate"],
    )
    assert broken.stage.bindings.calibration is None
    assert broken.stage.provenance.get("additions")


def test_bind_stage_configures_settings_without_methods(cons):
    """From settings alone, `bind_stage` applies `configure` to a new stage
    and binds the values given."""
    alone = bind_stage(cons, {"calibration": {}, "methods": {}, "settings": {"n_m": 8}})
    assert alone.stage is not cons and alone.failed == {}
    assert (alone.bound, alone.skipped) == (("configure",), ("calibrate", "methodize"))
    assert dict(alone.stage.bindings.settings) == {"n_m": 8}


def test_bind_stage_reports_a_methods_source_that_is_no_methods_file_and_keeps_the_stage(cons):
    """A methods source that is neither the path of a methods file nor its
    text is reported as the failure of `methodize`, and the report answers
    the stage as it was given."""
    malformed = bind_stage(
        cons, {"calibration": {}, "methods": {"methods": "nonsense"}, "settings": {}}
    )
    assert malformed.failed == {
        "methodize": "an addition is the path of a `.bl` file or a mapping {text, origin} "
        "holding its text; got dict"
    }
    assert malformed.stage is cons


# --- the settings of a period ---


def test_two_stages_of_a_period_share_a_setting_declared_alike_and_are_refused_otherwise(
    egm_stage_with_savings_grid_settings, stage_with_one_addition
):
    """Two stages of one period that declare `n_a` on the same set share one
    setting, and two that declare it on different sets are refused."""
    second = stage_with_one_addition(EGM_STAGE, SAVINGS_GRID_SETTINGS)
    shared = shared_parameters(
        {"a": egm_stage_with_savings_grid_settings, "b": second}, "periods[0]"
    )
    setting = shared["n_a"]
    assert (setting.kind, setting.keys, to_source(setting.domain)) == ("setting", ("a", "b"), "ℕ")
    other_set = stage_with_one_addition(
        EGM_STAGE, SAVINGS_GRID_SETTINGS.replace("n_a : ℕ", "n_a : [0, 1]")
    )
    with pytest.raises(FactoryError, match="n_a") as refused:
        shared_parameters({"a": egm_stage_with_savings_grid_settings, "b": other_set})
    assert refused.value.rule == "period-parameter-agreement"


def test_a_name_declared_as_a_parameter_in_one_stage_and_a_setting_in_another_is_refused(
    egm_stage_with_savings_grid_settings,
):
    """A name that one stage of a period declares as a parameter of the
    model and another as a setting names two things, which is refused."""
    parameter = stage_from_text(INVERSE_EULER.replace("@stage: t\n", "@stage: t\nn_a : ℕ\n"))
    with pytest.raises(FactoryError, match="as a parameter in one and as a setting in another"):
        shared_parameters({"a": egm_stage_with_savings_grid_settings, "b": parameter})


def test_a_shared_setting_is_valued_once_for_the_period(egm_stage_with_savings_grid_settings):
    """Two stages of one period configured with one value of a shared
    setting agree on it, and two configured with different values are
    refused at the second stage, with the kind of the binding."""
    first = copy_native(egm_stage_with_savings_grid_settings).configure(
        {"settings": SAVINGS_GRID_VALUES}
    )
    same = copy_native(egm_stage_with_savings_grid_settings).configure(
        {"settings": SAVINGS_GRID_VALUES}
    )
    agreed = one_period(first, same)
    settings = [place.stage.settings.n_a for place in positions(configure_trellis(agreed, agreed))]
    assert settings == [30, 30]
    second = copy_native(egm_stage_with_savings_grid_settings).configure(
        {"settings": {**SAVINGS_GRID_VALUES, "n_a": 40}}
    )
    differing = one_period(first, second)
    with pytest.raises(
        FactoryError, match="supply the setting 'n_a' with the values 30 and 40"
    ) as refused:
        configure_trellis(differing, differing)
    assert refused.value.rule == "period-parameter-agreement"
    assert refused.value.__notes__ == [
        "Stage occurrence: periods[0].stages['b']",
        "Binding kind: settings",
    ]


def test_a_stage_whose_settings_source_omits_a_shared_setting_takes_the_period_value(
    egm_stage_with_savings_grid_settings,
):
    """A record whose settings source gives no value for a setting that the
    period shares takes the value that the other stage of the period
    binds."""
    first = copy_native(egm_stage_with_savings_grid_settings).configure(
        {"settings": SAVINGS_GRID_VALUES}
    )
    unvalued = copy_native(egm_stage_with_savings_grid_settings)
    record = {
        "settings": {name: value for name, value in SAVINGS_GRID_VALUES.items() if name != "n_a"}
    }
    # each entry: the period, the key of the stage, its place and its record
    found = [(0, "a", "periods[0].stages['a']", first), (0, "b", "periods[0].stages['b']", record)]
    supplied = period_settings(found, {0: {"a": first, "b": unvalued}})
    assert supplied[0, "a"] is None and supplied[0, "b"]["n_a"] == 30
    assert unvalued.configure({"settings": supplied[0, "b"]}).settings.n_a == 30
