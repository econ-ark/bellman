"""The fixtures of the package's tests: the stages, trellises and sources that
the tests elaborate."""

import functools
import hashlib
import types

import pytest
from application_files import (
    ADJUSTER_CONS_WITH_EGM_LINES_FILE,
    BENHABIB_STAGE_FILE,
    CONS_CALIBRATION,
    CONS_METHODS,
    CONS_SETTINGS,
    COPIED_FILES_FOLDER,
    CORPUS,
    DURABLES,
    PENSION,
    PERFECT_FORESIGHT_ALTERNATIVE_CALIBRATION,
    PERFECT_FORESIGHT_NEAR_LIMIT_GRID,
    PERFECT_FORESIGHT_RESOURCES,
    RETIRE_CHOICE_WITH_ARRIVAL,
    ROOT,
)
from shared_stage_fixtures import (
    bound_port_cons_trellis,
    buffer_stock,
    buffer_stock_application,
    cache_folder,
    catalogue_entries,
    cons,
    cons_argmax,
    cons_argmax_text,
    cons_methodized,
    cons_methodized_without_calibration,
    cons_obs,
    cons_savings_iid,
    cons_sources,
    cons_with_egm_lines,
    cons_with_egm_lines_text,
    derived_parameter_stages,
    example_additions,
    example_shocks,
    ez_savings,
    grid_stage_with_one_addition,
    model_explorer_package,
    perfect_foresight,
    perfect_foresight_explicit,
    port,
    retiree_death,
    sa_savings,
    tenure,
    two_nodes_registry,
    worker_cons,
)
from stage_builders import (
    closed_form_check,
    control_branching_stage,
    corpus_stage,
    origin_of,
    saving_stage,
    shock_branching_stage,
    stage_from_file,
    stage_from_text,
)
from stage_texts import (
    BOUNDED,
    DISC_WITH_K_NEXT_TEXT,
    DURABLES_CANDIDATE_LINE,
    DURABLES_CLAUSE_LINE,
    EGM_STAGE,
    FIRST_ORDER_CONDITION_LINE,
    LOCATION_TEXT,
    PARENT_CHAIN_TEXT,
    SAVINGS_GRID_SETTINGS,
    TWO_FIELDS,
    UNCHANGED,
    UNIFORM_ENDPOINTS_TEXT,
    buffer_stock_text,
    chain_text_with_law_of_epsilon,
    changed,
    cons_text_with_policy_lines,
    corpus_text,
    methods_addition,
    two_nodes_text_with_changes,
)
from two_sets import pytest_addoption, pytest_collection_modifyitems, pytest_report_header

from bellman.native.hypergraphs import copy_native
from bellman.trellis import elaborate_trellis, load_recipe

# pytest finds the fixtures of shared_stage_fixtures.py, which the root
# tests/conftest.py also imports, and the hooks imported above by their names
# in this module; the list also tells the linter that the imports are used.
__all__ = [
    "bound_port_cons_trellis",
    "buffer_stock",
    "buffer_stock_application",
    "cache_folder",
    "catalogue_entries",
    "cons",
    "cons_argmax",
    "cons_argmax_text",
    "cons_methodized",
    "cons_methodized_without_calibration",
    "cons_obs",
    "cons_savings_iid",
    "cons_sources",
    "cons_with_egm_lines",
    "cons_with_egm_lines_text",
    "derived_parameter_stages",
    "example_additions",
    "example_shocks",
    "ez_savings",
    "grid_stage_with_one_addition",
    "model_explorer_package",
    "perfect_foresight",
    "perfect_foresight_explicit",
    "port",
    "pytest_addoption",
    "pytest_collection_modifyitems",
    "pytest_report_header",
    "retiree_death",
    "sa_savings",
    "tenure",
    "two_nodes_registry",
    "worker_cons",
]


@pytest.fixture(scope="module")
def two_state_identity_stage():
    """The symbolic stage `two_fields`, whose arrival states are `a` and `b`
    and whose continuation states are `a` and `b`."""
    return stage_from_text(TWO_FIELDS, "two_fields.bl")


@pytest.fixture(scope="module")
def identity_stage():
    """The symbolic stage `unchanged`, which carries `a` unchanged from its
    arrival perch to its continuation perch and discounts its value."""
    return stage_from_text(UNCHANGED, "unchanged.bl")


@pytest.fixture(scope="module")
def strictly_positive_identity_stage():
    """The symbolic stage `unchanged` with its state declared in ℝ₊₊ in place
    of ℝ₊."""
    return stage_from_text(UNCHANGED.replace("ℝ₊", "ℝ₊₊"), "positive.bl")


@pytest.fixture(scope="module")
def bounded_identity_stage():
    """The symbolic stage `bounded`, which carries `a` in the interval
    [a_min, ∞) from its arrival perch to its continuation perch."""
    return stage_from_text(BOUNDED, "bounded.bl")


@pytest.fixture(scope="module")
def disc_with_k_next():
    """The symbolic discounting stage `disc` of `DISC_WITH_K_NEXT_TEXT`, whose
    arrival state is `a` and whose continuation state is `k_next`."""
    return stage_from_text(DISC_WITH_K_NEXT_TEXT, "disc.bl")


@pytest.fixture(scope="module")
def pension_trellis_with_arrival_builders():
    """The trellis of the pension model with the retirement choice of each
    period read from `RETIRE_CHOICE_WITH_ARRIVAL` and the period's connector
    mapping `{"y_f": "y_f_d", "y_p": "y_p_d"}` removed, an empty mapping
    standing where it was the only one, so that the trellis joins the
    retirement choice's arrival states to the worker's continuation states of
    the same names."""
    syntactic = load_recipe(PENSION, "spec.yml")
    text = RETIRE_CHOICE_WITH_ARRIVAL.read_text(encoding="utf-8")
    for period in syntactic["periods"]:
        record = period["stages"]["retire_choice"]
        record["stage"] = {"text": text, "origin": "retire_choice_with_arrival.bl"}
        record["provenance"] = {
            **record["provenance"],
            "origin": "retire_choice_with_arrival.bl",
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        period["connectors"] = [
            mapping
            for mapping in period["connectors"]
            if mapping != {"y_f": "y_f_d", "y_p": "y_p_d"}
        ] or [{}]
    return elaborate_trellis(syntactic)


@pytest.fixture(scope="module")
def pension_trellis_text():
    """The text of the pension model's trellis file."""
    return (PENSION / "trellis.yml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def view_of(model_explorer_package):
    """`view_of(stage)`: the view in Model Explorer of a stage that the tests
    read and do not change, made once for the module."""
    from bellman.stage import to_model_explorer

    return functools.cache(to_model_explorer)


@pytest.fixture(scope="session")
def cons_kt_text():
    """The text of the consumption stage, named `cons_kt`, for Kuhn–Tucker, in
    which the first-order condition with its clause,
    `FIRST_ORDER_CONDITION_LINE`, is the operative line that states the policy
    and the maximization is marked `!doc`: the first spelling of the
    Kuhn–Tucker condition written as a line of its own, as section 4.1 of the
    public page docs/Bellman-Sym/10-constraints.md describes it."""
    return cons_text_with_policy_lines("cons_kt", FIRST_ORDER_CONDITION_LINE)


@pytest.fixture(scope="session")
def cons_kt(cons_kt_text):
    """The symbolic stage `cons_kt` of the text `cons_kt_text`, whose
    first-order condition with its clause is the operative line that states
    the policy, beside the maximization marked `!doc`; the origin written for
    it names no file."""
    return stage_from_text(
        cons_kt_text, "applications/portfolio-choice/declaration/stages/cons_kt/cons_kt.bl"
    )


@pytest.fixture(scope="session")
def adjuster_cons_with_egm_lines():
    """The symbolic stage of the stage file
    `ADJUSTER_CONS_WITH_EGM_LINES_FILE`, the adjuster's consumption stage of
    the durables model with two controls, whose policy block holds, after the
    maximization marked `!doc`, an inverse Euler line, a grid line and the
    joint solution of the two controls."""
    return stage_from_file(ADJUSTER_CONS_WITH_EGM_LINES_FILE)


@pytest.fixture(scope="session")
def adjuster_cons_with_clause_on_candidate_line():
    """The adjuster's consumption stage of the durables model with the clause
    `⟂ a_nxt_adj >= 0` on its inverse Euler line, under which the first
    residual of its line `solve_{c, h_choice}` reads as the membership of the
    consumption in the values that the inverse Euler line admits."""
    path = ADJUSTER_CONS_WITH_EGM_LINES_FILE
    text = (ROOT / path).read_text(encoding="utf-8")
    return stage_from_text(changed(text, (DURABLES_CANDIDATE_LINE, DURABLES_CLAUSE_LINE)), path)


@pytest.fixture(scope="module")
def read_only_stage_from_text():
    """`read_only_stage_from_text(text)`: the symbolic stage of a stage text,
    elaborated once for the module, which the tests read and of which they
    calibrate copies, since a calibration binds the stage that it is called on.
    """
    return functools.cache(stage_from_text)


@pytest.fixture(scope="module")
def location_stage(read_only_stage_from_text):
    """The symbolic location stage, read from `read_only_stage_from_text`."""
    return read_only_stage_from_text(LOCATION_TEXT)


@pytest.fixture
def benhabib_stage():
    """The symbolic stage of the stage file of the application benhabib-2019,
    elaborated for each test, since a calibration binds it."""
    return stage_from_file(BENHABIB_STAGE_FILE)


@pytest.fixture(scope="module")
def buffer_stock_file_text():
    """The text of the buffer-stock stage file, which `buffer_stock_text()` of
    stage_texts.py returns."""
    return buffer_stock_text()


@pytest.fixture(scope="module")
def two_nodes_stage():
    """The two-node stage as written, the stage `two_nodes` of the module
    `bellman.refusal_examples`, whose shocks y and z each have the law
    N(0, 1)."""
    return stage_from_text(two_nodes_text_with_changes())


@pytest.fixture(scope="module")
def uniform_text():
    """The two-node stage text with `y ~ Uniform(a_y, b_y)`, the constant
    `UNIFORM_ENDPOINTS_TEXT` of stage_texts.py."""
    return UNIFORM_ENDPOINTS_TEXT


@pytest.fixture(scope="module")
def two_nodes_trellis(two_nodes_registry):
    """The trellis that `assemble_trellis` gives for the recipe `spec.yml` of
    the two-node registry, before any test queries its stages."""
    from bellman.trellis import assemble_trellis

    return assemble_trellis(two_nodes_registry, "spec.yml")


@pytest.fixture(scope="module")
def two_nodes_recipe(two_nodes_registry):
    """The syntactic trellis of the recipe `spec.yml` of the two-node
    registry, loaded with no slot bound: three periods of the two-node stage,
    the terminal period with a calibration file of its own."""
    return load_recipe(two_nodes_registry, "spec.yml")


@pytest.fixture(scope="module")
def extreme_value_chain():
    """The chain stage with ε ~ TypeIExtremeValue(0, 1) on I_J."""
    return stage_from_text(chain_text_with_law_of_epsilon("TypeIExtremeValue(0, 1)"), "chain.bl")


@pytest.fixture(scope="module")
def tuple_argument_chain():
    """The chain stage with ε ~ LogNormal((0, 1), 1) on I_J, whose tuple
    argument makes the law no scalar law."""
    return stage_from_text(chain_text_with_law_of_epsilon("LogNormal((0, 1), 1)"), "chain.bl")


@pytest.fixture(scope="module")
def parent_chain():
    """The stage of `PARENT_CHAIN_TEXT`."""
    return stage_from_text(PARENT_CHAIN_TEXT, "chain.bl")


@pytest.fixture(scope="module")
def cons_portfolio():
    """The portfolio stage of the corpus, whose shock Adjust is drawn from a
    `Bernoulli` law."""
    path = f"{COPIED_FILES_FOLDER}/ConsPortfolio/cons.bl"
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


@pytest.fixture(scope="module")
def cons_obs_file_text():
    """The text of the stage file `cons_obs.bl` of the portfolio-choice
    application, whose policy block declares the multiplier μ[>]."""
    return corpus_text("cons_obs")


@pytest.fixture(scope="module")
def egm_stage_with_savings_grid_settings(stage_with_one_addition):
    """The stage `EGM_STAGE`, the inverse Euler form of the consumption stage
    with the endogenous grid method on its policy builder, read with the
    methods file `SAVINGS_GRID_SETTINGS`, which declares the seven settings of
    its two grids and values none of them."""
    return stage_with_one_addition(EGM_STAGE, SAVINGS_GRID_SETTINGS)


@pytest.fixture(scope="module")
def port_with_one_node_count(port):
    """`port` with a quadrature at its expectation whose node counts of the
    two shocks both name the setting `nodes`."""
    return copy_native(port).methodize(
        methods_addition(
            "port", "nodes : ℕ", "E_Ψ_θ.method : !gauss_hermite(n_Ψ=nodes, n_θ=nodes)"
        )
    )


@pytest.fixture(scope="module")
def one_period_cons_trellis(cons):
    """A trellis of one period, with no registry, that holds the consumption
    stage `cons` under the key `consumption`."""
    from bellman.trellis import accrete

    return accrete(
        {"periods": [], "inter_connectors": []},
        {"stages": {"consumption": cons}, "connectors": []},
    )


@pytest.fixture(scope="session")
def worker_saving():
    """The symbolic stage `worker_saving` of the pension model."""
    return saving_stage("worker_saving")


@pytest.fixture(scope="session")
def retiree_saving():
    """The symbolic stage `retiree_saving` of the pension model."""
    return saving_stage("retiree_saving")


@pytest.fixture(scope="session")
def keeper_saving():
    """The symbolic stage `keeper_saving` of the housing model with
    frictions."""
    return saving_stage("keeper_saving")


@pytest.fixture(scope="session")
def adjuster_saving():
    """The symbolic stage `adjuster_saving` of the housing model with
    frictions."""
    return saving_stage("adjuster_saving")


@pytest.fixture(scope="session")
def ret_choice():
    """The symbolic stage `ret_choice` of the retirement-choice model, a
    branching stage whose branches a control selects."""
    return control_branching_stage("ret_choice")


@pytest.fixture(scope="session")
def house_choice():
    """The symbolic stage `house_choice` of the housing model with frictions,
    a branching stage whose branches a control selects."""
    return control_branching_stage("house_choice")


@pytest.fixture(scope="session")
def young_choice():
    """The symbolic stage `young_choice` of the model of Cagetti and De Nardi
    (2006), a branching stage whose branches a control selects."""
    return control_branching_stage("young_choice")


@pytest.fixture(scope="session")
def old_choice():
    """The symbolic stage `old_choice` of the model of Cagetti and De Nardi
    (2006), a branching stage whose branches a control selects."""
    return control_branching_stage("old_choice")


@pytest.fixture(scope="session")
def worker_ageing():
    """The symbolic stage `worker_ageing` of the model of Cagetti and De Nardi
    (2006), a branching stage whose branches a shock selects."""
    return shock_branching_stage("worker_ageing")


@pytest.fixture(scope="session")
def entrepreneur_death():
    """The symbolic stage `entrepreneur_death` of the model of Cagetti and De
    Nardi (2006), a branching stage whose branches a shock selects."""
    return shock_branching_stage("entrepreneur_death")


@pytest.fixture(scope="session")
def entrepreneur_ageing():
    """The symbolic stage `entrepreneur_ageing` of the model of Cagetti and De
    Nardi (2006), a branching stage whose branches a shock selects."""
    return shock_branching_stage("entrepreneur_ageing")


@pytest.fixture(scope="session")
def fecundity():
    """The symbolic stage `fecundity` of the childbearing model of de la Croix
    and Pommeret (2021), a branching stage whose branches a shock selects."""
    return shock_branching_stage("fecundity")


# The bound versions of `cons` follow the order of the binding verbs:
# calibrate, then methodize, then configure. A binding verb changes the stage
# it is called on, so each fixture binds a stage of its own, and none binds
# the stage of the fixture `cons`.
@pytest.fixture(scope="session")
def cons_calibrated():
    """A stage of `cons.bl` of its own, calibrated by `CONS_CALIBRATION`."""
    from bellman.stage.binding_verbs import calibrate

    return calibrate(corpus_stage("cons"), CONS_CALIBRATION)


@pytest.fixture(scope="session")
def cons_configured():
    """A stage of `cons.bl` of its own, calibrated by `CONS_CALIBRATION`,
    methodized by `CONS_METHODS` and configured by `CONS_SETTINGS`."""
    from bellman.stage.binding_verbs import calibrate, configure, methodize

    return configure(
        methodize(calibrate(corpus_stage("cons"), CONS_CALIBRATION), CONS_METHODS), CONS_SETTINGS
    )


@pytest.fixture(scope="session")
def encoding_validator():
    """A validator of the JSON schema of a stage's encoding, the schema itself
    checked first."""
    import json
    from importlib.resources import files

    from jsonschema import Draft202012Validator

    schema = json.loads(
        files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="session")
def parsed_source():
    """`parsed_source(path)`: the parsed term of a stage file with the
    positions of its source, read once for each path."""
    from bellman.syntax.lower import parse_with_spans

    @functools.cache
    def read(path):
        return parse_with_spans((ROOT / path).read_text(encoding="utf-8"), origin_of(path))

    return read


@pytest.fixture(scope="session")
def read_only_stage_from_file():
    """`read_only_stage_from_file(path)`: the symbolic stage of a stage file,
    elaborated once for each path, for the tests that read a stage and bind
    nothing, since a binding verb changes the stage it is called on."""
    return functools.cache(stage_from_file)


@pytest.fixture(scope="session")
def corpus_path():
    """`corpus_path(name)`: the path of the stage file of the corpus stage
    `name`."""
    return lambda name: ROOT / CORPUS[name]


@pytest.fixture(scope="session")
def stage_with_one_addition():
    """`stage_with_one_addition(text, addition)`: the stage of the stage text
    `text`, with the addition `addition` read into it.

    The stage file is named `t.bl` and the addition `methods.bl`. The
    declarations of the addition are the stage's settings, and its entries
    type the places of the stage's builders."""
    from bellman.stage import elaborate_stage

    return lambda text, addition: elaborate_stage(
        {
            "stage": {"text": text, "origin": "t.bl"},
            "calibration": {},
            "settings": {},
            "methods": [{"text": addition, "origin": "methods.bl"}],
        }
    )


@pytest.fixture(scope="session")
def durables_trellis():
    """The life-cycle trellis of the durables model, its 51 periods elaborated
    once from the recipe `spec.yml`, which the tests read and do not bind."""
    return elaborate_trellis(load_recipe(DURABLES, "spec.yml"))


@pytest.fixture(scope="session")
def perfect_foresight_solutions():
    """The solutions of the perfect-foresight application that several tests
    compare, each computed once, as a record whose fields the comments below
    name."""
    import numpy as np

    check = closed_form_check()
    closed = check.closed_form_stage()
    resources = np.linspace(*PERFECT_FORESIGHT_RESOURCES)
    alternative = {"calibration": PERFECT_FORESIGHT_ALTERNATIVE_CALIBRATION}
    limit = closed.par["L"].value
    lower, upper, count = PERFECT_FORESIGHT_NEAR_LIMIT_GRID
    near = check.gridded_stage(count, limit + lower, limit + upper)
    return types.SimpleNamespace(
        # the numerical module of the application
        check=check,
        # the closed-form stage at the baseline calibration
        closed=closed,
        # the closed-form stage at the second calibration
        alternative=check.closed_form_stage(alternative),
        # the levels of resources of the comparisons
        resources=resources,
        # by the number of levels of savings, the comparison of the gridded
        # solution, which the application's function `gridded_route`
        # computes, with the closed form on grids of 5, 50 and 500 levels of
        # savings from -40 to 60, at the baseline calibration
        comparisons={n: check.comparison(n, -40.0, 60.0, resources) for n in (5, 50, 500)},
        # the same comparison on a grid of 50 levels of savings from -33 to
        # 60, at the second calibration
        alternative_comparison=check.comparison(
            50, -33.0, 60.0, resources, calibration=alternative
        ),
        # the gridded stage whose grid of savings starts just above the
        # natural borrowing limit, and its gridded solution
        near=near,
        near_route=check.gridded_route(near),
    )
