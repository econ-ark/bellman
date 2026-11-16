"""The fixtures of stages and sources that the tests of this folder and the
documentation checks of the root folder request."""

import os
import tempfile
import types
from pathlib import Path

import pytest
from application_files import (
    BUFFER_STOCK_BASELINE_CALIBRATION,
    BUFFER_STOCK_FILE,
    BUFFER_STOCK_METHODS,
    BUFFER_STOCK_PAGE,
    BUFFER_STOCK_SETTINGS,
    CONS_CALIBRATION,
    CONS_METHODS,
    CONS_PORT,
    CONS_SETTINGS,
    PERFECT_FORESIGHT_CALIBRATION,
    PERFECT_FORESIGHT_ORIGIN,
    ROOT,
    WORKER_CONS_FILE,
)
from skips import require_package

# Matplotlib, which the package imports, reads the folder of its settings and
# of its font list from MPLCONFIGDIR when it is first imported. Both folders of
# tests import this module before the package, and so set the variable here, to
# one folder in the temporary folder that every run reuses, so that no run
# writes the font list into the user's home folder.
MATPLOTLIB_FOLDER = Path(tempfile.gettempdir()) / "bellman-test-matplotlib"


MATPLOTLIB_FOLDER.mkdir(exist_ok=True)


os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_FOLDER))


from stage_builders import corpus_stage, stage_from_file, stage_from_text  # noqa: E402
from stage_texts import (  # noqa: E402
    ARGMAX_DOC_LINE,
    ARGMAX_LINE,
    EGM_LINES,
    EXAMPLE_SHOCKS_TEXT,
    FIRST_ORDER_CONDITION_PROPERTY_LINE,
    GRID_SETTINGS,
    GRID_STAGE,
    MPC_ADDITION,
    WORKER_CONS_ENVELOPE,
    buffer_stock_text,
    changed,
    cons_text_with_policy_lines,
    perfect_foresight_text,
)
from trellises import ADDED_REGISTRY_FILES  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def cache_folder(tmp_path_factory):
    """A temporary folder for the session, named by the variable
    `XDG_CACHE_HOME` until the session ends, so that no test, and no process
    that a test starts, writes a stage view into the user's own cache
    folder."""
    with pytest.MonkeyPatch.context() as patch:
        folder = tmp_path_factory.mktemp("cache")
        patch.setenv("XDG_CACHE_HOME", str(folder))
        yield folder


@pytest.fixture(scope="session")
def model_explorer_package():
    """The viewer, the package `model_explorer` of the extra `explore`, or a
    skip of the test where it is not installed."""
    return require_package("model_explorer", extra="explore")


@pytest.fixture(scope="session")
def cons():
    """The symbolic stage of the consumption stage file `cons.bl` of the
    portfolio-choice application."""
    return corpus_stage("cons")


@pytest.fixture(scope="session")
def port():
    """The symbolic stage of the portfolio stage file `port.bl` of the
    portfolio-choice application."""
    return corpus_stage("port")


@pytest.fixture(scope="session")
def ez_savings():
    """The symbolic stage of the savings stage file `ez_savings.bl` of the
    application with Epstein-Zin preferences."""
    return corpus_stage("ez_savings")


@pytest.fixture(scope="session")
def cons_savings_iid():
    """The symbolic stage of the consumption-savings stage file
    `cons_savings_iid.bl`, whose income is independent from period to
    period."""
    return corpus_stage("cons_savings_iid")


@pytest.fixture(scope="session")
def sa_savings():
    """The symbolic stage of the savings stage file `sa_savings.bl` of the
    application with smooth ambiguity aversion."""
    return corpus_stage("sa_savings")


@pytest.fixture(scope="session")
def cons_with_egm_lines_text():
    """The text of the consumption stage, named `cons`, with the three lines of
    the endogenous grid method, `EGM_LINES`, after its maximization marked
    `!doc`, the third spelling of the Kuhn–Tucker condition."""
    return cons_text_with_policy_lines("cons", EGM_LINES)


@pytest.fixture(scope="session")
def cons_with_egm_lines(cons_with_egm_lines_text):
    """The symbolic stage of the text `cons_with_egm_lines_text`, whose origin
    `cons_with_egm_lines.bl` names no file."""
    return stage_from_text(cons_with_egm_lines_text, "cons_with_egm_lines.bl")


@pytest.fixture(scope="session")
def cons_obs():
    """The symbolic stage of the consumption stage file `cons_obs.bl`, whose
    policy block declares the multiplier of the borrowing constraint."""
    return corpus_stage("cons_obs")


@pytest.fixture(scope="session")
def cons_argmax_text():
    """The text of the consumption stage, named `cons_argmax`, in which the
    maximization statement is operative and the first-order condition with its
    clause, `FIRST_ORDER_CONDITION_PROPERTY_LINE`, is attached to it as its
    property: the first spelling of the Kuhn–Tucker condition written as a
    property, as section 4.1 of the public page
    docs/Bellman-Sym/10-constraints.md describes it."""
    return changed(
        cons_text_with_policy_lines("cons_argmax", FIRST_ORDER_CONDITION_PROPERTY_LINE),
        (ARGMAX_DOC_LINE, ARGMAX_LINE),
    )


@pytest.fixture(scope="session")
def cons_argmax(cons_argmax_text):
    """The symbolic stage `cons_argmax` of the text `cons_argmax_text`, whose
    operative maximization statement carries the first-order condition with
    its clause as its property; the origin written for it names no file."""
    # The public page docs/Bellman-Sym/10-constraints.md prints the card of the
    # stage `cons_argmax`, and the root test of the cards shown on pages
    # requests this fixture by that name.
    return stage_from_text(
        cons_argmax_text,
        "applications/portfolio-choice/declaration/stages/cons_argmax/cons_argmax.bl",
    )


@pytest.fixture(scope="session")
def buffer_stock():
    """The symbolic stage of the buffer-stock stage file, whose parameter
    declarations carry the author's descriptions and whose inverse marginal
    utility is declared as `Inv(𝑑𝑢)`."""
    # not one of the eight corpus stages of `CORPUS`, so no stored text of its
    # graphs describes it
    return stage_from_file(BUFFER_STOCK_FILE)


@pytest.fixture(scope="session")
def tenure():
    """The symbolic stage `tenure` of the durables model, a branching stage
    whose branches a control selects."""
    return corpus_stage("tenure")


@pytest.fixture(scope="session")
def retiree_death():
    """The symbolic stage `retiree_death` of the model of Cagetti and De Nardi
    (2006), a branching stage whose branches a shock selects."""
    return corpus_stage("retiree_death")


@pytest.fixture(scope="session")
def cons_methodized():
    """A stage of `cons.bl` of its own, calibrated by `CONS_CALIBRATION` and
    methodized by `CONS_METHODS`."""
    from bellman.stage.binding_verbs import calibrate, methodize

    return methodize(calibrate(corpus_stage("cons"), CONS_CALIBRATION), CONS_METHODS)


@pytest.fixture(scope="session")
def cons_sources():
    """The methods file, the calibration and the settings with which the
    fixtures bind `cons`, by the name of each binding."""
    return {"methods": CONS_METHODS, "calibration": CONS_CALIBRATION, "settings": CONS_SETTINGS}


@pytest.fixture(scope="session")
def cons_methodized_without_calibration(cons_sources):
    """A stage of `cons.bl` of its own with its methods file bound and no
    calibration or settings, the version whose encoding carries the word
    `methods`."""
    # a stage of its own, since a binding verb changes the stage it is called
    # on and the stage of the fixture `cons` stays symbolic
    return corpus_stage("cons").methodize(cons_sources["methods"])


@pytest.fixture(scope="session")
def catalogue_entries():
    """The entries of the package's catalogue of refusals, which the tests
    read and do not change."""
    from bellman.refusal_catalogue import catalogue

    return catalogue()


@pytest.fixture(scope="session")
def two_nodes_registry(tmp_path_factory):
    """The folder of the two-node registry that `write_registry` of the module
    `bellman.refusal_examples` writes with the files of `ADDED_REGISTRY_FILES`:
    the stage `two_nodes` with its addition and a replacing selection, one
    calibration source and one settings source, a range source, a source with a
    parent, a period template, a trellis file of three periods and a recipe
    with two slots."""
    # The stage `two_nodes` of `bellman.refusal_examples` writes, in its block
    # `cntn_to_dcsn`, two lines marked `!node`, each the expectation over the
    # two shocks y and z.
    from bellman.refusal_examples import write_registry

    return write_registry(tmp_path_factory.mktemp("registry"), ADDED_REGISTRY_FILES)


@pytest.fixture(scope="session")
def bound_port_cons_trellis():
    """The trellis of six periods of the stages `port`, `cons` and `disc` that
    the recipe `spec.port-cons.yml` of the portfolio-consumption application
    gives, each stage occurrence calibrated, methodized and configured by the
    files that the recipe names, as the lesson
    `05-periods-and-trellises.ipynb` binds it."""
    # The trellis is bound from its recipe. The consumption stage of the folder
    # states no derivative until its methods file adds the envelope condition.
    # Once the trellis is bound, the view of Model Explorer draws both backward
    # graphs.
    from bellman.trellis import (
        calibrate_trellis,
        configure_trellis,
        elaborate_trellis,
        load_recipe,
        methodize_trellis,
    )

    syntactic = load_recipe(CONS_PORT, "spec.port-cons.yml")
    calibrated = calibrate_trellis(elaborate_trellis(syntactic), syntactic)
    return configure_trellis(methodize_trellis(calibrated, syntactic), syntactic)


@pytest.fixture(scope="session")
def grid_stage_with_one_addition():
    """`grid_stage_with_one_addition(entries, declarations="",
    text=GRID_STAGE)`: the stage of `text` with one addition read into it.

    The addition declares the settings `GRID_SETTINGS`, then `declarations`,
    and then types the stage's places by `entries`. The stage is elaborated
    anew at each call, since `configure` and `methodize` change the stage
    they are called on."""
    from bellman.stage import elaborate_stage

    def make(entries, declarations="", text=GRID_STAGE):
        methods = "@methods: grids\n" + GRID_SETTINGS + declarations + entries
        return elaborate_stage(
            {
                "stage": {"text": text, "origin": "grids.bl"},
                "calibration": {},
                "settings": {},
                "methods": [{"text": methods, "origin": "methods.bl"}],
            }
        )

    return make


@pytest.fixture(scope="session")
def perfect_foresight():
    """The symbolic perfect-foresight stage of the module
    `bellman.refusal_examples`, which a test that binds methods on it copies
    first with `copy_native`."""
    return stage_from_text(perfect_foresight_text(), PERFECT_FORESIGHT_ORIGIN)


@pytest.fixture(scope="session")
def perfect_foresight_explicit(perfect_foresight):
    """A copy of the perfect-foresight stage methodized by the addition
    `EXPLICIT_POLICY` of `bellman.refusal_examples`, which solves its policy
    builder explicitly; a test that binds it further binds a copy."""
    from bellman.native.hypergraphs import copy_native
    from bellman.refusal_examples import EXPLICIT_POLICY

    return copy_native(perfect_foresight).methodize(
        {"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"}
    )


@pytest.fixture(scope="session")
def derived_parameter_stages():
    """The stage texts, the stages and the calibrations of the tests of
    derived parameters, as a record whose fields the comments below name."""
    # Each stage is made anew at each call, since a binding verb changes the
    # stage it is called on.
    return types.SimpleNamespace(
        # the text of the perfect-foresight stage
        text=perfect_foresight_text(),
        # `stage(*changes)`: a symbolic stage of that text, with each pair of
        # `changes` replaced as `perfect_foresight_text` replaces it
        stage=lambda *changes: stage_from_text(
            perfect_foresight_text(*changes), PERFECT_FORESIGHT_ORIGIN
        ),
        # the name of the file that the stage carries
        origin=PERFECT_FORESIGHT_ORIGIN,
        # the addition that defines the marginal propensity to consume κ
        addition=MPC_ADDITION,
        # the baseline calibration of the perfect-foresight stage
        calibration=PERFECT_FORESIGHT_CALIBRATION,
        # `buffer_stock(scale)`: the symbolic stage of the text that
        # `buffer_stock_text(scale)` gives
        buffer_stock=lambda scale="σ_ξ": stage_from_text(
            buffer_stock_text(scale), BUFFER_STOCK_FILE
        ),
        # the baseline calibration of the buffer-stock stage
        buffer_stock_calibration=BUFFER_STOCK_BASELINE_CALIBRATION,
    )


@pytest.fixture(scope="session")
def buffer_stock_application(derived_parameter_stages):
    """The buffer-stock application, as a record whose fields the comments
    below name."""

    def stage(calibration):
        made = derived_parameter_stages.buffer_stock().methodize(ROOT / BUFFER_STOCK_METHODS)
        made.calibrate({"calibration": calibration})
        return made.configure(ROOT / BUFFER_STOCK_SETTINGS)

    return types.SimpleNamespace(
        # `stage(calibration)`: the buffer-stock stage with its methods file
        # read into it, calibrated by `calibration` and configured by its
        # settings file, made anew at each call, since a binding verb changes
        # the stage it is called on
        stage=stage,
        # the baseline calibration of the stage
        calibration=derived_parameter_stages.buffer_stock_calibration,
        # the methods file, the settings file and the example page, as paths
        # in the repository
        methods=BUFFER_STOCK_METHODS,
        settings=BUFFER_STOCK_SETTINGS,
        page=BUFFER_STOCK_PAGE,
    )


@pytest.fixture(scope="session")
def example_shocks():
    """The symbolic stage of `EXAMPLE_SHOCKS_TEXT`, whose arrival value
    integrates a Markov shock and a shock with a finite law of two points."""
    return stage_from_text(EXAMPLE_SHOCKS_TEXT, "example_shocks.bl")


@pytest.fixture(scope="session")
def worker_cons():
    """The symbolic stage of the worker's consumption stage file
    `WORKER_CONS_FILE` of the retirement-choice model."""
    return stage_from_file(WORKER_CONS_FILE)


@pytest.fixture(scope="session")
def example_additions():
    """The additions read, in the same call of `methodize`, with a declaration
    example of the methods reference, the public page
    docs/Bellman-Sym/reference/methods.md, by the name of the fixture of the
    stage on which the example is read."""
    # The keys are fixture names; tests/test_documentation_structure.py reads
    # them by the names of its list EXAMPLE_STAGES.
    # A call of `methodize` replaces the additions read before, so an example
    # whose place an addition writes is read in the same call as that
    # addition: on `perfect_foresight_explicit`, the explicit solution of the
    # policy builder, whose closing Evaluation the example of !closed_form
    # types; on `worker_cons`, the methods file beside the stage file without
    # the typing of its upper envelope, whose operator the example of !FUES
    # types.
    from bellman.refusal_examples import EXPLICIT_POLICY

    methods = ROOT / WORKER_CONS_FILE.replace("worker_cons.bl", "methods.bl")
    text = changed(methods.read_text(encoding="utf-8"), (WORKER_CONS_ENVELOPE, "]"))
    return {
        "perfect_foresight_explicit": ({"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"},),
        "worker_cons": ({"text": text, "origin": "methods.bl"},),
    }
