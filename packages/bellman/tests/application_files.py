"""The paths of the application files that the tests read, the list of every
stage file of the applications, the calibrations, settings and methods of the
corpus stages, the market resources at which the tests evaluate the explicit
policy of the perfect-foresight stage and its consumption, and the
environment of an interpreter that a test starts."""

import os
from pathlib import Path

import numpy

# the four corpus stages for which this module gives two calibrations, a
# methods file or the text of an addition, and settings
STAGES_WITH_BINDINGS = ("cons", "port", "ez_savings", "cons_savings_iid")


# the root of the repository
ROOT = Path(__file__).resolve().parents[3]


# the folder `fixtures` beside the tests: stage files and a methods file
# written for the tests, which no application holds
FIXTURES_FOLDER = "packages/bellman/tests/fixtures"


# the retirement choice of the pension model written with arrival builders, for
# the trellis of the fixture `pension_trellis_with_arrival_builders`. Its
# arrival states have the same names as the worker's continuation states, so
# that the trellis joins them without a connector. The application's own stage
# file starts at its decision perch, and a connector joins it.
RETIRE_CHOICE_WITH_ARRIVAL = ROOT / FIXTURES_FOLDER / "retire_choice_with_arrival.bl"


# the stage file of the buffer-stock application
BUFFER_STOCK_FILE = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"


def checkout_environment():
    """The environment of this process with the folders of the packages bellman
    and asva of this checkout first on PYTHONPATH, for a new interpreter that a
    test starts, which then imports them whatever copy is installed."""
    folders = [str(ROOT / "packages" / "bellman"), str(ROOT / "packages" / "asva")]
    if os.environ.get("PYTHONPATH"):
        folders.append(os.environ["PYTHONPATH"])
    return {**os.environ, "PYTHONPATH": os.pathsep.join(folders)}


# the folder of copies of files that the tests read, kept beside the tests so
# that the tests read no file outside the package and the applications. It
# holds stage files of several models that `applications/` does not hold, the
# registry of the childbearing model of de la Croix and Pommeret (2021), and
# three stage files of Dobrescu et al. (2018) that the package refuses. Its
# subfolder branching/ holds the drawings and a registry that the tests of
# branching compare.
COPIED_FILES_FOLDER = "packages/bellman/tests/copied_files"


# the folder of the two models written for the tests, which no application
# holds: a buffer-stock model and a retirement choice, each with a pension
# account that an addition adds
MODELS_FOR_THE_TESTS_FOLDER = "packages/bellman/tests/additions/models-for-the-tests"


# the folder of the buffer-stock model with a pension account, written for
# the tests: its stage file, its additions and its trellis file
BUFFER_STOCK_PENSION_FOLDER = f"{MODELS_FOR_THE_TESTS_FOLDER}/buffer-stock-pension"


# the folder of the retirement choice with a pension account, written for the
# tests: its stage file, its additions and its trellis file
RETIREMENT_CHOICE_PENSION_FOLDER = f"{MODELS_FOR_THE_TESTS_FOLDER}/retirement-choice-pension"


# the folder of the copied example pages of the branching models, each of
# which shows the cards that the package prints for the stages of its model
BRANCHING_EXAMPLES_FOLDER = ROOT / COPIED_FILES_FOLDER / "branching"


# the eight corpus stages: the stage files whose graphs the tests store as
# text, `<stage>.bl.graphs.txt`, by stage name, as paths in the repository
CORPUS = {
    "cons": "applications/portfolio-choice/declaration/stages/cons/cons.bl",
    # the consumption stage whose policy block declares the multiplier of the
    # borrowing constraint at each saving, the second of the three spellings
    # of the Kuhn–Tucker condition
    "cons_obs": "applications/portfolio-choice/declaration/stages/cons_obs/cons_obs.bl",
    "port": "applications/portfolio-choice/declaration/stages/port/port.bl",
    "ez_savings": "applications/epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl",
    "cons_savings_iid": (
        "applications/consumption-savings-iid/declaration/stages/"
        "cons_savings_iid/cons_savings_iid.bl"
    ),
    "sa_savings": (
        "applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl"
    ),
    # a branching stage whose branches a control selects
    "tenure": "applications/durables/declaration/stages/tenure/tenure.bl",
    # a branching stage whose branches a shock selects
    "retiree_death": (
        "applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl"
    ),
}


# the stage files of the applications, listed once; the tests and the hook
# docs/_hooks/reference_pages.py read this list. A stage file is a .bl file
# whose first line is `@stage:` and which stands in a folder
# applications/<model>/declaration/stages/<key>/, the layout of the public
# page docs/Bellman-Sym/reference/model-directory-layout.md. An addition beside
# a stage file, methods.bl, opens with `@methods:` and is not a stage file.
# The list is read from the folders, not from what git tracks: a stage file in
# the layout that git does not track is listed, and a copy of the repository
# without git gives the same list. A scratch folder elsewhere under
# applications/ is outside the layout and is not read. The files are ordered
# by their paths from the repository's root.
STAGE_FILES = sorted(
    (
        path
        for path in (ROOT / "applications").glob("*/declaration/stages/*/*.bl")
        if path.read_text(encoding="utf-8").startswith("@stage:")
    ),
    key=lambda path: path.relative_to(ROOT).as_posix(),
)


def stage_file_id(path):
    """The test identifier of a stage file: its path under `applications/`."""
    return path.relative_to(ROOT / "applications").as_posix()


# two calibrations of the smooth-ambiguity stage; the second sets the
# ambiguity aversion η equal to the risk aversion γ and changes nothing else
SA_SAVINGS_CALIBRATIONS = (
    {"β": 0.96, "ρ": 2.0, "γ": 5.0, "η": 8.0, "κ_1": 0.02, "σ_ν": 0.05, "σ_Ψ": 0.15},
    {"β": 0.96, "ρ": 2.0, "γ": 5.0, "η": 5.0, "κ_1": 0.02, "σ_ν": 0.05, "σ_Ψ": 0.15},
)


# the methods file of the consumption stage, the application's addition
CONS_METHODS = ROOT / "applications/portfolio-choice/declaration/stages/cons/methods.bl"


# a methods file of the portfolio stage that types value function iteration
# on the backward decision builder, quadrature on its expectation and on the
# expectation of the policy's first-order condition, and a linear
# representation on the builder's Evaluation, with no solution method of the
# policy
PORT_METHODS = ROOT / FIXTURES_FOLDER / "port.methods.bl"


# the calibration file of `cons` and `port`, among the reference files of the
# portfolio-consumption application
CONS_CALIBRATION = ROOT / "applications/cons-port/reference/legacy/syntax/calibration.yaml"


# the settings file of `cons` and `port`, among the reference files of the
# portfolio-consumption application
CONS_SETTINGS = ROOT / "applications/cons-port/reference/legacy/syntax/settings.yaml"


# the adjuster's consumption stage of the durables model with the lines of
# the endogenous grid method and the joint solution in its policy block,
# beside the maximization marked `!doc`; the application's own stage file
# leaves those lines to its methods file
ADJUSTER_CONS_WITH_EGM_LINES_FILE = f"{FIXTURES_FOLDER}/adjuster_cons_with_egm_lines.bl"


# the four saving stages of the pension and housing applications, each
# written with the complementary-slackness clause `⟂` and a law of motion
# with two outputs; `worker_saving` and `adjuster_saving` choose two controls
SAVING_STAGE_FILES = {
    "worker_saving": (
        "applications/pension-retirement/declaration/stages/worker_saving/worker_saving.bl"
    ),
    "retiree_saving": (
        "applications/pension-retirement/declaration/stages/retiree_saving/retiree_saving.bl"
    ),
    "keeper_saving": (
        "applications/housing-frictions/declaration/stages/keeper_saving/keeper_saving.bl"
    ),
    "adjuster_saving": (
        "applications/housing-frictions/declaration/stages/adjuster_saving/adjuster_saving.bl"
    ),
}


# four more branching stages whose branches a control selects
CONTROL_BRANCHING_STAGE_FILES = {
    "ret_choice": "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
    "house_choice": (
        "applications/housing-frictions/declaration/stages/house_choice/house_choice.bl"
    ),
    "young_choice": (
        "applications/cagetti-denardi-2006/declaration/stages/young_choice/young_choice.bl"
    ),
    "old_choice": "applications/cagetti-denardi-2006/declaration/stages/old_choice/old_choice.bl",
}


# four more branching stages whose branches a shock selects
SHOCK_BRANCHING_STAGE_FILES = {
    "worker_ageing": (
        "applications/cagetti-denardi-2006/declaration/stages/worker_ageing/worker_ageing.bl"
    ),
    "entrepreneur_death": (
        "applications/cagetti-denardi-2006/declaration/stages/"
        "entrepreneur_death/entrepreneur_death.bl"
    ),
    "entrepreneur_ageing": (
        "applications/cagetti-denardi-2006/declaration/stages/"
        "entrepreneur_ageing/entrepreneur_ageing.bl"
    ),
    "fecundity": f"{COPIED_FILES_FOLDER}/de-la-croix-pommeret-2021/stages/fecundity.bl",
}


# the declaration folder of the portfolio-consumption application
CONS_PORT = ROOT / "applications/cons-port/declaration"


# the declaration folder of the portfolio-choice application
PORTFOLIO = ROOT / "applications/portfolio-choice/declaration"


# a complete calibration of each of the four corpus stages of
# `STAGES_WITH_BINDINGS`, for the tests of the binding verbs: cons and port
# take values of the file
# applications/cons-port/reference/legacy/syntax/calibration.yaml, and the two
# stages whose folders hold no calibration file take values inside their
# declared sets
FIRST_CALIBRATIONS = {
    "cons": {"ρ": 6.0},
    "port": {
        "R": 1.02,
        "μ_Ψ": 0.028927,
        "σ_Ψ": 0.143486,
        "μ_θ": -0.01125,
        "σ_θ": 0.15,
        "ρ_ζ": 0.0,
    },
    "ez_savings": {"β": 0.96, "ρ": 2.0, "γ": 5.0, "μ_Ψ": 0.0, "σ_Ψ": 0.1},
    "cons_savings_iid": {"β": 0.96, "γ": 2.0, "R": 1.02, "μ_y": 0.0, "σ_y": 0.1, "p_zero": 0.3},
}


# a second calibration of each of the four stages, which differs from the
# first in one value
SECOND_CALIBRATIONS = {
    "cons": {"ρ": 2.0},
    "port": {**FIRST_CALIBRATIONS["port"], "R": 1.04},
    "ez_savings": {**FIRST_CALIBRATIONS["ez_savings"], "β": 0.95},
    "cons_savings_iid": {**FIRST_CALIBRATIONS["cons_savings_iid"], "β": 0.95},
}


# the declaration folder of the durables model, whose recipe `spec.yml`
# lists every stage of the model, the branching stage `tenure` among them
DURABLES = ROOT / "applications/durables/declaration"


# the second recipe of the durables model, which leaves out `tenure` and
# names the trellis file of the two consumption stages and the bequest
DURABLES_RECIPE_WITHOUT_TENURE = "spec.two-stages.yml"


# the registries of three other models, each the folder `declaration/` of its
# model folder
RETIREMENT = ROOT / "applications/retirement-choice/declaration"


PENSION = ROOT / "applications/pension-retirement/declaration"


HOUSING = ROOT / "applications/housing-frictions/declaration"


# a methods file and a settings source for each of the four corpus stages of
# `STAGES_WITH_BINDINGS`, for the tests of the binding verbs: cons and port
# take their methods files and the settings of the portfolio-consumption
# application, and the two stages whose folders hold no methods file take the
# text of an addition that represents the decision value, and one setting
METHODS_SOURCES_BY_STAGE = {
    "cons": CONS_METHODS,
    "port": PORT_METHODS,
    "ez_savings": {
        "text": "@methods: ez_savings\ncntn_to_dcsn.evaluate.method : !Linear\n",
        "origin": "ez_savings.methods.bl",
    },
    "cons_savings_iid": {
        "text": "@methods: cons_savings_iid\ncntn_to_dcsn.evaluate.method : !Linear\n",
        "origin": "cons_savings_iid.methods.bl",
    },
}


# the settings source of each of the four stages
SETTINGS_SOURCES_BY_STAGE = {
    "cons": CONS_SETTINGS,
    "port": CONS_SETTINGS,
    "ez_savings": {"n_m": 8},
    "cons_savings_iid": {"n_m": 8},
}


# the origin of the perfect-foresight stage of the module
# `bellman.refusal_examples`, whose consumption function and values are known
# as expressions
PERFECT_FORESIGHT_ORIGIN = "perfect_foresight.bl"


# the baseline calibration of the perfect-foresight stage, r = ϑ = 0.04,
# g = 0.02 and ρ = 2, at which human wealth h = 1/(1 - Γ/R) is 52 and the
# marginal propensity to consume κ is 0.04/1.04
PERFECT_FORESIGHT_CALIBRATION = {"β": 1 / 1.04, "ρ": 2.0, "R": 1.04, "Γ": 1.02}


# the baseline calibration of the buffer-stock stage, which supplies no
# value of the derived parameter μ_ξ
BUFFER_STOCK_BASELINE_CALIBRATION = {
    "R": 1.03,
    "β": 0.96,
    "Γ": 1.03,
    "ρ": 2.0,
    "σ_ψ": 0.1,
    "σ_ξ": 0.1,
    "p_zero": 0.005,
}


# a calibration of the buffer-stock stage that gives a value to each declared
# parameter and differs from `BUFFER_STOCK_BASELINE_CALIBRATION` in R alone,
# 1.04 in place of 1.03; μ_ξ, which the stage defines from σ_ξ and p_zero,
# takes its value from that definition
BUFFER_STOCK_CALIBRATION_AT_R_1_04 = {
    "β": 0.96,
    "ρ": 2.0,
    "R": 1.04,
    "Γ": 1.03,
    "σ_ψ": 0.1,
    "σ_ξ": 0.1,
    "p_zero": 0.005,
}


# the numerical module of the perfect-foresight application, which the tests
# load from its file, since the folder of an application is no package
PERFECT_FORESIGHT_MODULE = (
    ROOT / "applications" / "consumption-perfect-foresight-crra" / "code" / "closed_form_check.py"
)


# the levels of resources at which the gridded solution is compared with the
# closed form: 401 levels from -30 to 50, the arguments of numpy.linspace
PERFECT_FORESIGHT_RESOURCES = (-30.0, 50.0, 401)


# the market resources at which the tests evaluate the consumption of the
# explicit policy of the perfect-foresight stage of `bellman.refusal_examples`
MARKET_RESOURCES = numpy.array([0.0, 1.0, 10.0])


def consumption_at_human_wealth(wealth):
    """The consumption of the explicit policy, (1 - (Rβ)^(1/ρ)/R)(m - 1 + h),
    at `MARKET_RESOURCES` and h = `wealth`, where Rβ = 1 and R = 1.04."""
    return 0.04 / 1.04 * (MARKET_RESOURCES - 1 + numpy.asarray(wealth))


# the second calibration of the perfect-foresight application, at which
# human wealth is 1/(1 - 1.01/1.04)
PERFECT_FORESIGHT_ALTERNATIVE_CALIBRATION = {"β": 0.90, "ρ": 2.0, "R": 1.04, "Γ": 1.01}


# the folder of the stage file of the perfect-foresight application and of
# its methods files
PERFECT_FORESIGHT_FOLDER = (
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight"
)


# the stage file of the perfect-foresight application, which declares β on
# ℝ₊₊ @ (0, R^(ρ-1)) and defines the return patience factor q on the
# declared set (0,1)
PERFECT_FORESIGHT_FILE = f"{PERFECT_FORESIGHT_FOLDER}/perfect_foresight.bl"


# a calibration of the perfect-foresight stage at which the return
# impatience condition fails: q = (βR)^(1/ρ)/R is (0.99 × 0.9)^(1/2)/0.9,
# about 1.049, above one
RETURN_IMPATIENCE_FAILING_CALIBRATION = {"β": 0.99, "ρ": 2.0, "R": 0.9, "Γ": 0.85}


# the grid of savings of the gridded stage near the natural borrowing limit
# L: from just above L, by these two offsets, with this many points, so that
# its endogenous grid covers total wealth from about 1e-4 to about 2
PERFECT_FORESIGHT_NEAR_LIMIT_GRID = (1e-4, 2.0, 50)


# the files of the buffer-stock application beside its stage file
# `BUFFER_STOCK_FILE`, as its README and its example page name them: the
# methods file, an addition to the stage file; the settings file; and the
# example page, which quotes the three files
BUFFER_STOCK_METHODS = "applications/buffer-stock/declaration/stages/buffer_stock/methods.bl"


BUFFER_STOCK_SETTINGS = "applications/buffer-stock/declaration/settings/buffer_stock.yml"


BUFFER_STOCK_PAGE = "docs/examples/buffer-stock/buffer_stock.md"


# the stage file of the application benhabib-2019, whose wage is a parameter
# on a product of ten factors that a label selects
BENHABIB_STAGE_FILE = (
    "applications/benhabib-2019/declaration/stages/benhabib_bellman/benhabib_bellman.bl"
)


# the worker's consumption stage of the retirement-choice application, whose
# methods file writes the four lines of the endogenous grid method on the
# policy builder, the last of them an upper envelope, and types that
# envelope by the fast upper-envelope scan in the part `WORKER_CONS_ENVELOPE`
WORKER_CONS_FILE = "applications/retirement-choice/declaration/stages/worker_cons/worker_cons.bl"
