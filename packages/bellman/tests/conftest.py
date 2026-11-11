"""The corpus stages the tests read, each elaborated once per session.

A stage is built as the stage notebook builds it (`01-the-stage.ipynb`, code
cells 1 and 3): `elaborate_stage` on the record of the file's text. The stage
is given as its file's text with the file's path in the
repository as its origin, so that its printed face names the same source in
every checkout. The bound versions of `cons` apply `calibrate`, `methodize`
and `configure` to the calibration and settings files the notebook names and
to the addition `CONS_METHODS`.

`printed_cards(name)` is every card a stage prints, with its record, printed
once in a process and kept. A test marked `sweep` checks the corpus stages, refusal catalogue or a whole
trellis. Every test runs by default; `-m sweep` selects those checks alone.
"""
from __future__ import annotations

import functools
import math
import operator
import os
import tempfile
import shutil
import subprocess
import types
from fractions import Fraction
from pathlib import Path

import pytest

# Matplotlib imports during collection. Reuse only its font metadata.
_font_cache = Path(tempfile.gettempdir()) / "bellman-test-matplotlib"
_font_cache.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_font_cache))

# the two-node stage of AMD-SG-008 §2, whose backward block, transition line
# and shock declarations the tests of passes B replace; the smallest stage of
# the one form of D02 (branching-unified.md §2 item 1) and the smallest stage
# of a branch a shock selects, which the refusal tests change one line at a
# time: each text stands once, among the refusal examples of the package
from bellman.refusal_examples import BRANCHING, SHOCK_BRANCHING, TWO_NODES

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session", autouse=True)
def cache_folder(tmp_path_factory):
    """`XDG_CACHE_HOME`, the variable that names the user's cache folder,
    set to a temporary folder for the session and restored at its end, so
    that no test writes a stage view into the user's own cache folder; a
    process a test starts inherits it."""
    with pytest.MonkeyPatch.context() as patch:
        folder = tmp_path_factory.mktemp("cache")
        patch.setenv("XDG_CACHE_HOME", str(folder))
        yield folder


# the files of the preliminary applications that the tests read, copied into
# tests/corpus/ so that the tests read only files of the package and of the
# applications (PL13): the accumulation stage of mckenzie-1976, the portfolio
# stage of ConsRiskyAsset, the stage of HAFiscal and the childbearing registry
# of de-la-croix-pommeret-2021; the stage files that test_behaviour.py
# reads of ma-stachurski-toda-2020, benhabib-bisin-zhu-2011, bloom-2009,
# rendahl-2015, gourinchas-parker-2002, ConsPortfolio, AlganRagotMoney and
# consumer; the three stage files of dobrescu-etal-2018 that the first build
# of branching refuses; and, under branching/, the drawings and the Cagetti
# registry of the branching run of 23 September 2026 that the two acceptance
# files of step F read
PRELIMINARY = "packages/bellman/tests/corpus"

# the eight corpus stages, by stage name, as paths in the repository
CORPUS = {
    "cons": "applications/portfolio-choice/declaration/stages/cons/cons.bl",
    # spelling B of the consumption problem, the multiplier declared on the
    # policy block's continuation grid (AMD-SG-035 §7, D7)
    "cons_obs": "applications/portfolio-choice/declaration/stages/cons_obs/cons_obs.bl",
    "port": "applications/portfolio-choice/declaration/stages/port/port.bl",
    "ez_savings": "applications/epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl",
    "cons_savings_iid": ("applications/consumption-savings-iid/declaration/stages/"
                         "cons_savings_iid/cons_savings_iid.bl"),
    "sa_savings": ("applications/smooth-ambiguity-savings/declaration/stages/"
                   "sa_savings/sa_savings.bl"),
    # the branching stage of the first build of step F (E18)
    "tenure": "applications/durables/declaration/stages/tenure/tenure.bl",
    # the branching stage whose branches a shock selects, the second build of step F (E13)
    "retiree_death": ("applications/cagetti-denardi-2006/declaration/stages/"
                      "retiree_death/retiree_death.bl"),
}
# the stage files of the applications, the corpus the tests, the hook
# docs/_hooks/reference_pages.py and the tool elaboration_baseline.py read,
# listed once: every tracked .bl file in a stage folder of the one layout,
# applications/<model>/declaration/stages/<key>/, whose first line is
# `@stage:`, by path. An addition beside a stage file, methods.bl, whose
# first line is `@methods:`, is no stage file; the tracked files alone, since
# a checkout may hold an ignored scratch folder under applications/
STAGE_FILES = [
    ROOT / name
    for name in sorted(subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--", "applications/**/*.bl"],
        capture_output=True, text=True, check=True).stdout.split())
    if Path(name).match("applications/*/declaration/stages/*/*.bl")
    and (ROOT / name).read_text(encoding="utf-8").startswith("@stage:")
]
# the two calibrations of the smooth-ambiguity stage (AMD-SG-009 §6); the
# second changes only η, to γ
SA_SAVINGS_CALIBRATIONS = (
    {"β": 0.96, "ρ": 2.0, "γ": 5.0, "η": 8.0, "κ_1": 0.02, "σ_ν": 0.05, "σ_Ψ": 0.15},
    {"β": 0.96, "ρ": 2.0, "γ": 5.0, "η": 5.0, "κ_1": 0.02, "σ_ν": 0.05, "σ_Ψ": 0.15},
)

def two_nodes(backward=None, transition=None, declarations=None, header=None):
    """The two-node stage with its four backward lines, its transition line, its
    two shock declarations or its backward header replaced."""
    text = TWO_NODES
    for old, new in (("    W = β*V[>]\n    N1 = E_{y,z}(W) :: [id=first, !node]\n"
                      "    N2 = E_{y,z}(W) :: [id=second, !node]\n    V = N1 + N2\n", backward),
                     ("    a = k_d*(c*y + (1-c)*R) + z\n", transition),
                     ("y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\n", declarations),
                     ("(V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn]", header)):
        if new is not None:
            assert text.count(old) == 1
            text = text.replace(old, new)
    return text


def joint_normal(covariance="((1,r),(r,1))", backward="    V = E_{z}(E_{y}(V[>])) :: [id=value]\n", r_set="[-1,1]"):
    """The joint-normal fixture of AMD-SG-009 §4: the two-node stage with
    `(y,z) ~ N((0,0), covariance)`, `r : [-1,1]`, the transition `a = y` and
    one backward line."""
    return two_nodes(backward=backward, transition="    a = y\n",
                     declarations=f"z : ℝ\nr : {r_set}\n(y, z) ~ N((0,0),{covariance})\n")
# The consumption methods are the application's addition. The portfolio
# fixture types value function iteration on the backward decision builder,
# quadrature on its expectation and the policy's first-order condition,
# and linear representation on the Evaluation, with no policy solution method.
CONS_METHODS = ROOT / "applications/portfolio-choice/declaration/stages/cons/methods.bl"
PORT_METHODS = ROOT / "packages/bellman/tests/fixtures/spec_0_7/port.methods.bl"
CONS_CALIBRATION = ROOT / "applications/cons-port/reference/legacy/syntax/calibration.yaml"
CONS_SETTINGS = ROOT / "applications/cons-port/reference/legacy/syntax/settings.yaml"


def corpus_text(name):
    """The text of the corpus stage file `name`."""
    return (ROOT / CORPUS[name]).read_text(encoding="utf-8")


def stage_from_text(text, origin="t.bl"):
    """The symbolic stage `elaborate_stage` makes of a stage text whose source
    is named `origin`."""
    from bellman.stage import elaborate_stage
    return elaborate_stage({"stage": {"text": text, "origin": origin},
                            "calibration": {}, "settings": {}, "methods": {}})


def corpus_stage(name):
    """The symbolic stage of the corpus file `name`."""
    return stage_from_text(corpus_text(name), CORPUS[name])


def fresh_stage(path):
    """The symbolic stage of the stage file at `path`, a path in the
    repository, elaborated anew at each call for a test that binds methods on
    it."""
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


def methodized(stage, *additions):
    """A copy of `stage` (`copy_native`) methodized in one call of
    `methodize` by `additions`, in their order. A string is the text of an
    addition to the stage: it is read after the line `@methods: <the stage's
    name>`, with the origin `addition-<n>.bl`, n its position among the
    additions. Any other addition, a mapping holding a text and its origin
    or the `Path` of a file, is read as it is given."""
    from bellman.native.hypergraphs import copy_native

    read = [
        {"text": f"@methods: {stage.name}\n{held}", "origin": f"addition-{n}.bl"}
        if isinstance(held, str) else held
        for n, held in enumerate(additions, start=1)
    ]
    return copy_native(stage).methodize(read)


@pytest.fixture(scope="session")
def cons():
    return corpus_stage("cons")


@pytest.fixture(scope="session")
def port():
    return corpus_stage("port")


@pytest.fixture(scope="session")
def ez_savings():
    return corpus_stage("ez_savings")


@pytest.fixture(scope="session")
def cons_savings_iid():
    return corpus_stage("cons_savings_iid")


@pytest.fixture(scope="session")
def sa_savings():
    return corpus_stage("sa_savings")


# The alternative policy equations used by the clause tests: a candidate
# with a borrowing clause, an explicit multiplier, and an Euler equation.
# The inverse Euler equation now stands in the application's methods file.
C_LINES = ("    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0       :: [id=InvEuler]\n"
           "    m_d[>] = a + c[>]                :: [id=endoggrid]\n"
           "    c      = c[>]                    :: [id=cons_choice]\n")
CONS_OBS_LINES = ("    μ[>]   : ℝ₊ ⟂ a >= 0             :: [id=slackness]\n"
                  "    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>] + μ[>]) :: [id=InvEuler]\n"
                  "    m_d[>] = a + c[>]                :: [id=endoggrid]\n"
                  "    c      = c[>]                    :: [id=cons_choice]\n")
CONS_KT_LINE = "    𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0       :: [id=euler]\n"


def twin_text(name, lines):
    """The consumption stage with the alternative policy lines `lines`.

    The application declares the maximization in its stage file and the
    inverse Euler equation in its methods file. These alternative stages
    retain the maximization as documentation beside their own policy lines.
    """
    text = corpus_text("cons")
    assert text.count(ARGMAX_LINE) == 1
    inverse = "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)\n"
    return (text.replace("@stage: cons\n", f"@stage: {name}\n" + inverse, 1)
            .replace(ARGMAX_LINE, ARGMAX_DOC_LINE + lines, 1))


@pytest.fixture(scope="session")
def explicit_cons_text():
    """A policy candidate declared in the stage, independent of method bindings."""
    return twin_text("cons", C_LINES)


@pytest.fixture(scope="session")
def cons_explicit(explicit_cons_text):
    return stage_from_text(explicit_cons_text, "cons_explicit.bl")


@pytest.fixture(scope="session")
def cons_candidate():
    """The explicit candidate and identification used by the clause checks."""
    return stage_from_text(twin_text("cons_candidate", C_LINES), "cons_candidate.bl")


def cons_obs_text():
    return corpus_text("cons_obs")


@pytest.fixture(scope="session")
def cons_obs():
    return corpus_stage("cons_obs")


@pytest.fixture(scope="session")
def cons_kt_text():
    return twin_text("cons_kt", CONS_KT_LINE)


@pytest.fixture(scope="session")
def cons_kt(cons_kt_text):
    return stage_from_text(cons_kt_text,
                           "applications/portfolio-choice/declaration/stages/cons_kt/cons_kt.bl")


# spelling A restated (the sub-brief on the policy builder's operation,
# inv-Euler-functional-operation.md §2a; AAS, 27 September 2026): the argmax
# line of `cons.bl` is operative, no longer marked `!doc`, and the first-order
# condition with its clause is attached to it as its property by the dotted id
# `optimality.euler`, in place of the three inverse lines; the property forms
# no row, no address and no method place
ARGMAX_DOC_LINE = "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality, !doc]\n"
ARGMAX_LINE = "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality]\n"
EULER_PROPERTY_LINE = "    𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0                :: [id=optimality.euler]\n"

# the policy card of `cons.bl` as drawn: the four rows of the standard kinds,
# the candidate line's clause on the Aggregation that forms 𝑐≻, and the
# identification's printed rule, the grid relation on the image of the grid
CONS_POLICY_CARD = """\
STAGE cons / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻   : Xa → [−∞, ∞)
       𝑑𝑉≻  : Xa → ℝ₊₊
       ──────────────────────────────────────────
  out  𝑐    : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Declared
  𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]

Operations
  1  InvEuler:Aggregation
     in: 𝑑𝑉≻                            out: 𝑐≻
     ────────────────────────────────────────────
     rule: 𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) ⟂ a ≥ 0

  2  endoggrid:Aggregation
     in: 𝑐≻                             out: 𝑚_d≻
     ────────────────────────────────────────────
     rule: 𝑚_d≻(a) = a + 𝑐≻(a)

  3  cons_choice:Pullback
     in: 𝑐≻, 𝑚_d≻                       out: 𝑐
     ────────────────────────────────────────────
     rule: 𝑐(𝑚_d≻(a)) = 𝑐≻(a)                                      on 𝑚_d≻(Xa)

  4  Evaluation
     in: 𝑐                              out: 𝑐
     ────────────────────────────────────────────
     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)

Conditions
  endoggrid:Aggregation  𝑚_d≻(a) ∈ Xm
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  32  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality, !doc]
  33  c[>]   <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0              :: [id=InvEuler]
  34  m_d[>] = a + c[>]                            :: [id=endoggrid]
  35  c      = c[>]                                :: [id=cons_choice]

Definitions referenced
  Xm     cons:set:Xm
  Xa     cons:set:Xa
  𝑢      cons:function:𝑢
  𝑑𝑢𝑖𝑛𝑣  cons:function:𝑑𝑢𝑖𝑛𝑣
  Γ      cons:correspondence:Γ
  𝑔≻     cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


@pytest.fixture(scope="session")
def cons_argmax_text():
    """`cons.bl` renamed `cons_argmax`, its argmax line operative and the
    first-order condition attached to that line as its property."""
    text = twin_text("cons_argmax", EULER_PROPERTY_LINE)
    assert text.count(ARGMAX_DOC_LINE) == 1
    return text.replace(ARGMAX_DOC_LINE, ARGMAX_LINE)


@pytest.fixture(scope="session")
def cons_argmax(cons_argmax_text):
    return stage_from_text(cons_argmax_text,
                           "applications/portfolio-choice/declaration/stages/cons_argmax/cons_argmax.bl")


# the candidate line and the grid line of `cons.bl`, lines 33 and 34, which the
# texts of lane C of the internal developer release 0.01 replace one at a time
CANDIDATE_LINE, GRID_LINE, _ = C_LINES.splitlines(keepends=True)


def candidate_text(name, line, declarations=""):
    """`cons.bl` renamed `name`, its candidate line replaced by `line`, and
    the declarations `declarations` added after the declaration of `ρ`."""
    text = twin_text(name, C_LINES.replace(CANDIDATE_LINE, line))
    if declarations:
        assert text.count("ρ : [1, inf)\n") == 1
        text = text.replace("ρ : [1, inf)\n", "ρ : [1, inf)\n" + declarations)
    return text


def grid_line_text(name, line):
    """`cons.bl` renamed `name`, its grid line replaced by `line`."""
    return twin_text(name, C_LINES.replace(GRID_LINE, line))


@pytest.fixture(scope="session")
def cons_head():
    """`cons.bl` as it stood before the clause returned to its candidate line
    on 28 September 2026: the inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])` with no
    clause, which reads as the interior value at every saving (the ruling of
    22 September 2026)."""
    return stage_from_text(candidate_text("cons_head", CANDIDATE_LINE.replace(" ⟂ a >= 0", "")),
                           "applications/portfolio-choice/declaration/stages/cons_head/cons_head.bl")


@pytest.fixture(scope="session")
def cons_cap():
    """`cons.bl` with a cap `ā` on the saving beside the borrowing limit,
    written as the equation with the chain on the bounded quantity `−a`, the
    one writing of a two-sided bound in spelling C whose signs are right
    (the fourth trial of the two-sided bound, `cap-v3-reversed.bl`)."""
    line = "    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ -ā <= -a <= 0 :: [id=InvEuler]\n"
    return stage_from_text(candidate_text("cons_cap", line, "ā : ℝ₊₊\n"),
                           "applications/portfolio-choice/declaration/stages/cons_cap/cons_cap.bl")


@pytest.fixture(scope="session")
def mckenzie():
    """The accumulation stage of `mckenzie-1976`, whose value function takes
    the value −∞ at an infeasible point (AMD-SG-015 §5 item 6f)."""
    path = f"{PRELIMINARY}/mckenzie-1976/accumulation.bl"
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


@pytest.fixture(scope="session")
def buffer_stock():
    """The buffer-stock stage of `docs/overview/05-semantics.md`, whose
    parameter declarations carry the author's descriptions and whose inverse
    marginal utility is declared as `Inv(𝑑𝑢)`. It is not one of the six corpus
    stages and is not in the snapshot recording."""
    path = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


# the durables adjuster written the explicit way, its policy block holding the
# endogenous grid lines and the joint solution beside the maximization marked
# `!doc`, as the application's stage file stood before those lines moved to the
# method block of `declaration/methods/adjuster_cons_egm.bl` and its derivative
# line to a marginal block (decision MB-U10)
ADJUSTER_CONS_EXPLICIT = "packages/bellman/tests/fixtures/spec_0_6/adjuster_cons_explicit.bl"


@pytest.fixture(scope="session")
def adjuster_cons():
    """The two-control durable-adjustment stage used by AMD-SG-026, written
    the explicit way."""
    path = ADJUSTER_CONS_EXPLICIT
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


# the candidate line of the durables adjuster, line 39, and the same line with
# the clause at the borrowing limit that AAS's own durables solver requires
# (the main brief of lane C, §11; `spellings/durables-clause/adjuster_cons.bl`)
DURABLES_CANDIDATE_LINE = ("    c[>]          <= 𝑢_c_inv(β*D_{a_nxt_adj}V[>])"
                           "                                              :: [id=InvEuler]\n")
DURABLES_CLAUSE_LINE = "    c[>]          <= 𝑢_c_inv(β*D_{a_nxt_adj}V[>]) ⟂ a_nxt_adj >= 0  :: [id=InvEuler]\n"


@pytest.fixture(scope="session")
def adjuster_cons_clause():
    """The durables adjuster with the clause `⟂ a_nxt_adj >= 0` on its
    candidate line, under which the first residual of its joint solve reads
    as the membership of the consumption in the admitted set, written the
    explicit way."""
    path = ADJUSTER_CONS_EXPLICIT
    text = (ROOT / path).read_text(encoding="utf-8")
    assert text.count(DURABLES_CANDIDATE_LINE) == 1
    return stage_from_text(text.replace(DURABLES_CANDIDATE_LINE, DURABLES_CLAUSE_LINE), path)


# the four saving stages of the two applications of Dobrescu and Shanker
# (2024), written with the complementarity clause `⟂` (AMD-SG-034, plan
# addendum item 18): a two-control policy on `worker_saving` and
# `adjuster_saving`, a law of motion with two outputs on every one
SAVING_STAGES = {
    "worker_saving": ("applications/pension-retirement/declaration/stages/"
                      "worker_saving/worker_saving.bl"),
    "retiree_saving": ("applications/pension-retirement/declaration/stages/"
                       "retiree_saving/retiree_saving.bl"),
    "keeper_saving": ("applications/housing-frictions/declaration/stages/"
                      "keeper_saving/keeper_saving.bl"),
    "adjuster_saving": ("applications/housing-frictions/declaration/stages/"
                        "adjuster_saving/adjuster_saving.bl"),
}


def saving_stage(name):
    """The symbolic stage of the saving stage file `name`."""
    return stage_from_text((ROOT / SAVING_STAGES[name]).read_text(encoding="utf-8"),
                           SAVING_STAGES[name])


@pytest.fixture(scope="session")
def worker_saving():
    return saving_stage("worker_saving")


@pytest.fixture(scope="session")
def retiree_saving():
    return saving_stage("retiree_saving")


@pytest.fixture(scope="session")
def keeper_saving():
    return saving_stage("keeper_saving")


@pytest.fixture(scope="session")
def adjuster_saving():
    return saving_stage("adjuster_saving")


# the other branching stage files whose branches a control selects, which the first build
# constructs (step F)
BRANCHING_STAGES = {
    "ret_choice": "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
    "house_choice": ("applications/housing-frictions/declaration/stages/"
                     "house_choice/house_choice.bl"),
    "young_choice": ("applications/cagetti-denardi-2006/declaration/stages/"
                     "young_choice/young_choice.bl"),
    "old_choice": "applications/cagetti-denardi-2006/declaration/stages/old_choice/old_choice.bl",
}


def branching_stage(name):
    """The symbolic stage of the branching stage file `name`."""
    return stage_from_text((ROOT / BRANCHING_STAGES[name]).read_text(encoding="utf-8"),
                           BRANCHING_STAGES[name])


@pytest.fixture(scope="session")
def tenure():
    return corpus_stage("tenure")


@pytest.fixture(scope="session")
def ret_choice():
    return branching_stage("ret_choice")


@pytest.fixture(scope="session")
def house_choice():
    return branching_stage("house_choice")


@pytest.fixture(scope="session")
def young_choice():
    return branching_stage("young_choice")


@pytest.fixture(scope="session")
def old_choice():
    return branching_stage("old_choice")


@pytest.fixture(scope="session")
def retiree_death():
    return corpus_stage("retiree_death")


def branching(*changes):
    """`BRANCHING` with each `(line as written, line as changed)` pair applied;
    a line the text does not hold once is refused, so a change is never lost."""
    text = BRANCHING
    for written, changed in changes:
        assert text.count(written) == 1, written
        text = text.replace(written, changed)
    return text


def shock_branching(*changes):
    """`SHOCK_BRANCHING` with each `(line as written, line as changed)` pair
    applied; a line the text does not hold once is refused, so a change is
    never lost."""
    text = SHOCK_BRANCHING
    for written, changed in changes:
        assert text.count(written) == 1, written
        text = text.replace(written, changed)
    return text


# the four other stage files whose branches a shock selects (the second build of step F)
SHOCK_STAGES = {
    "worker_ageing": ("applications/cagetti-denardi-2006/declaration/stages/"
                      "worker_ageing/worker_ageing.bl"),
    "entrepreneur_death": ("applications/cagetti-denardi-2006/declaration/stages/"
                           "entrepreneur_death/entrepreneur_death.bl"),
    "entrepreneur_ageing": ("applications/cagetti-denardi-2006/declaration/stages/"
                            "entrepreneur_ageing/entrepreneur_ageing.bl"),
    "fecundity": f"{PRELIMINARY}/de-la-croix-pommeret-2021/stages/fecundity.bl",
}


def shock_stage(name):
    """The symbolic stage of the stage file `name` of `SHOCK_STAGES`."""
    return stage_from_text((ROOT / SHOCK_STAGES[name]).read_text(encoding="utf-8"), SHOCK_STAGES[name])


@pytest.fixture(scope="session")
def worker_ageing():
    return shock_stage("worker_ageing")


@pytest.fixture(scope="session")
def entrepreneur_death():
    return shock_stage("entrepreneur_death")


@pytest.fixture(scope="session")
def entrepreneur_ageing():
    return shock_stage("entrepreneur_ageing")


@pytest.fixture(scope="session")
def fecundity():
    return shock_stage("fecundity")


# the three bound versions in the order of D36: calibrate, then methodize, then
# configure, so that each fixture is the stopping point its name says; a
# binding verb binds the stage it is called on (specification 0.6 decision 1
# and R4), so each fixture binds a stage of its own and none binds `cons`
@pytest.fixture(scope="session")
def cons_calibrated():
    from bellman.stage.binding_verbs import calibrate
    return calibrate(corpus_stage("cons"), CONS_CALIBRATION)


@pytest.fixture(scope="session")
def cons_methodized():
    from bellman.stage.binding_verbs import calibrate, methodize
    return methodize(calibrate(corpus_stage("cons"), CONS_CALIBRATION), CONS_METHODS)


@pytest.fixture(scope="session")
def cons_configured():
    from bellman.stage.binding_verbs import calibrate, configure, methodize
    return configure(
        methodize(calibrate(corpus_stage("cons"), CONS_CALIBRATION), CONS_METHODS), CONS_SETTINGS
    )


@pytest.fixture(scope="session")
def cons_sources():
    """The methods, calibration and settings files the bound versions of
    `cons` read."""
    return {"methods": CONS_METHODS, "calibration": CONS_CALIBRATION, "settings": CONS_SETTINGS}


@pytest.fixture(scope="session")
def cons_methods_only(cons_sources):
    """A stage of `cons.bl` of its own with its methods bound and nothing
    else, the version whose encoding carries the word `methods`; `cons`
    itself stays symbolic, since a binding verb binds the stage it is called
    on (specification 0.6 decision 1 and R4)."""
    return corpus_stage("cons").methodize(cons_sources["methods"])


@pytest.fixture(scope="session")
def corpus_encodings(cons, port, ez_savings, cons_savings_iid, sa_savings):
    """The encoding of each of the five corpus stages, made once for the
    session; a test that changes an encoding copies it first (plan-addendum of
    AMD-SG-034, item 20)."""
    return {"cons": cons.encoding(), "port": port.encoding(), "ez_savings": ez_savings.encoding(),
            "cons_savings_iid": cons_savings_iid.encoding(), "sa_savings": sa_savings.encoding()}


@pytest.fixture(scope="session")
def encoding_validator():
    """A checked JSON schema validator for newly constructed encodings."""
    import json
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    schema = json.loads(files("bellman.display").joinpath(
        "stage-encoding-2.6.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="session")
def catalogue_entries():
    """The immutable public refusal entries shared by catalogue checks."""
    from bellman.refusal_catalogue import catalogue
    return catalogue()


@pytest.fixture(scope="session")
def parsed_source():
    """Parsed application terms and source positions, shared by corpus checks."""
    from bellman.syntax.lower import parse_with_spans

    @functools.cache
    def read(path):
        path = Path(path).resolve()
        return parse_with_spans(path.read_text(encoding="utf-8"),
                                path.relative_to(ROOT).as_posix())

    return read


@pytest.fixture(scope="session")
def application_stage():
    """Read-only application stages, constructed once for the session.

    Binding tests construct their own stages: a binding changes its argument.
    These objects are shared only by queries and recording comparisons.
    """
    @functools.cache
    def read(path):
        path = Path(path).resolve()
        return stage_from_text(path.read_text(encoding="utf-8"),
                               path.relative_to(ROOT).as_posix())

    return read


@pytest.fixture(scope="session")
def case_study_union():
    """Read-only unions and their stage files, shared across acceptance claims."""
    from bellman.stage import elaborate_stage, load_stage

    @functools.cache
    def read(path, additions=()):
        return elaborate_stage(load_stage(path, list(additions)))

    return read




@pytest.fixture(scope="session")
def path_of():
    """`path_of(name)`: the path of a corpus stage file."""
    return lambda name: ROOT / CORPUS[name]


@pytest.fixture(scope="session")
def elaborate_text():
    """`elaborate_text(text, origin)`: the symbolic stage of a stage text the
    corpus does not contain."""
    return stage_from_text


@pytest.fixture(scope="session")
def with_addition():
    """`with_addition(text, addition)`: the stage of a stage text unioned
    with a methods file, an addition whose file-level declarations are the
    stage's settings and whose entries type the components of its
    signatures, the stage text named `t.bl` and the addition `methods.bl`
    (`elaborate_stage` on a record that carries the addition)."""
    from bellman.stage import elaborate_stage

    return lambda text, addition: elaborate_stage({
        "stage": {"text": text, "origin": "t.bl"}, "calibration": {}, "settings": {},
        "methods": [{"text": addition, "origin": "methods.bl"}],
    })


@pytest.fixture(scope="session")
def text_of():
    """`text_of(name)`: the text of a corpus stage file, for a test that
    changes one line of it."""
    return corpus_text


class PrintedStage:
    """What one stage prints, each part computed when it is first read and
    then kept: `cards`, which iterating the object also gives, and
    `sheets`."""

    def __init__(self, stage):
        self.stage = stage

    @functools.cached_property
    def cards(self):
        """`(title, text, record)` of the stage's card, of each builder's, of
        each primitive's and of each definition's, in that order. Each record
        is computed once and its text is the record printed, which is what
        `str` of the handle prints."""
        stage = self.stage
        records = [("stage", stage.denote())]
        for direction, graph in (("backward", stage.builder.bwd), ("forward", stage.builder.fwd)):
            for name in graph.list():
                builder = graph[name]
                records.append((f"{direction} {name}", builder.denote()))
                pieces = builder.primitives
                for key in pieces.list():
                    records.append((f"{direction} {name} / {key}", pieces[key].denote()))
        listing = stage.definitions.list()
        for kind in listing:
            for identity in listing[kind]:
                records.append((str(identity), stage.definitions.denote(identity)))
        return tuple((title, str(record), record) for title, record in records)

    @functools.cached_property
    def sheets(self):
        """Every sheet of the stage by its address, as `sheets_parse.sheets_of`
        prints them; the mapping cannot be changed."""
        from sheets_parse import sheets_of
        return types.MappingProxyType(sheets_of(self.stage))

    def __iter__(self):
        return iter(self.cards)


@pytest.fixture(scope="session")
def printed_cards(request):
    """`printed_cards(name)`: the `PrintedStage` of the stage fixture `name`
    of this file, such as `cons` or `worker_saving`, made on the first request
    for `name` and kept for the session. A pytest-xdist worker is a process
    with a session of its own, so a worker prints a stage only when one of its
    tests asks for it, and prints it once."""
    printed = {}

    def printed_stage(name):
        if name not in printed:
            printed[name] = PrintedStage(request.getfixturevalue(name))
        return printed[name]
    return printed_stage


JOINT_CHOICE = """@stage: joint_choice
[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=dcsn_to_cntn, (x_d, u : ℝ × ℝ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d + u[1] + u[2]
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, u) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
 V = -u[1]^2-u[2]^2+V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
 V[<] = V
}
[id=policy, (V[>] : ℝ @ !vlu) -> (u : ℝ × ℝ @ !ctrl) : !dcsn] {
 u = argmax_{u}(-u[1]^2-u[2]^2+V[>]) :: [id=choice]
}
"""

FINITE_STATE = (JOINT_CHOICE.replace('@stage: joint_choice','@stage: joint_choice\nZ := {low, high}\nprices : ℝ × ℝ')
 .replace('(x : ℝ) : !arvl -> (x_d : ℝ)', '(x : ℝ, z : Z) : !arvl -> (x_d : ℝ, z_d : Z)')
 .replace(' x_d = x',' x_d = x\n z_d = z')
 .replace('(x_d, u :','(x_d, z_d, u :')
 .replace('x_d + u[1] + u[2]', 'x_d + prices[z_d] + u[1]'))


SEQUENTIAL_G = '@stage: g_output_read\n\nk : ℝ₊₊\n\nε : ℝ\nε ~ N(0, 1)\n\n[id=arvl_to_dcsn, (b : ℝ, ε) : !arvl -> (m : ℝ, n : ℝ) : !dcsn] {\n    m = k*b + ε                  :: [id=first_output]\n    n = m + b                    :: [id=second_output]\n}\n\n[id=dcsn_to_cntn, (m, n) : !dcsn -> (m_a : ℝ, n_a : ℝ) : !cntn] {\n    m_a = m\n    n_a = n\n}\n\n[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n    V = V[>]\n}\n\n[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = E_{ε}(V)\n}\n'

TARGET_STATE_G = '@stage: target_read\n\nk : ℝ₊₊\n\nε : ℝ\nε ~ N(0, 1)\n\n[id=arvl_to_dcsn, (b : ℝ, ε) : !arvl -> (m : ℝ) : !dcsn] {\n    m = k*b + ε\n}\n\n[id=dcsn_to_cntn, (m) : !dcsn -> (m_a : ℝ) : !cntn] {\n    m_a = m\n}\n\n[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n    V = m*V[>]                   :: [id=value]\n}\n\n[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = E_{ε}(m*V)            :: [id=value]\n}\n'

SELECTED_LAW = '@stage: key_selection_reads\n\nXk := ℝ₊\nXm := ℝ₊₊\nXa := ℝ₊\nS  := {lo, hi}\n\nβ : (0,1)\nγ : ℝ₊₊\nR : ℝ₊₊\nP : [0,1]\nσ : ℝ₊\n\ns : S\ns ~ MarkovChain(P, S)              :: ["a two-point state; an admitted family, so that the forward view is constructed"]\nη : ℝ\nη ~ N(0, 1)                        :: ["a parent read directly by the law of θ"]\nθ : ℝ₊₊\nθ ~ LogNormal(η, (σ, 0)[s])        :: ["a shock whose law reads η directly and s through a key selection"]\n\n𝑢(c : ℝ₊₊) := c^(1-γ)/(1-γ)         :: [id=util]\n𝑑𝑢(c : ℝ₊₊) := c^(-γ)               :: [id=marg_util]\n𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/γ)          :: [id=inv_marg_util]\n𝒞(x : ℝ₊₊) := (0, x]                 :: [id=feasible]\n\n[id=arvl_to_dcsn, (k : Xk, s, θ) : !arvl -> (m : Xm) : !dcsn] {\n    m = R*k + (1, 2)[s]*θ            :: [id=market_resources, "reads s only through a key selection"]\n}\n\n[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {\n    a = m - c                        :: [id=savings]\n}\n\n[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n    V      = 𝑢(c) + β*V[>]           :: [id=value]\n    D_{m}V = 𝑑𝑢(c)                   :: [id=marginal]\n}\n\n[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<]      = E_{s,θ,η}(V)         :: [id=value]\n    D_{k}V[<] = E_{s,θ,η}(R * D_{m}V) :: [id=marginal]\n}\n\n[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n    c    = argmax_{c : 𝒞(m)}(𝑢(c) + β*V[>])   :: [id=optimality, !doc]\n    c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])                 :: [id=InvEuler]\n    m[>] = a + c[>]                            :: [id=endoggrid]\n    c    = c[>]                                :: [id=cons_choice]\n}\n'

RISKY_PORT = (ROOT / PRELIMINARY / "ConsRiskyAsset/port.bl").read_text()

NAMED_CONTROLS = (JOINT_CHOICE.replace('u : ℝ × ℝ @ !ctrl', 'c : ℝ @ !ctrl, l : ℝ @ !ctrl')
    .replace('u[1]', 'c').replace('u[2]', 'l').replace(', u)', ', c, l)')
    .replace('u = argmax_{u}', '(c,l) = argmax_{c,l}').replace('-c^2-l^2', '-c^2-4*l^2'))
HAFISCAL = (ROOT / PRELIMINARY / "HAFiscal/HAFiscal.bl").read_text()

# The stage of AMD-SG-011: a value and its stated derivative on one arrival
# edge with two shocks, whose backward block and shock declarations the tests
# replace. `k_d = k + y + z` puts both shocks in the law of motion of
# `arvl_to_dcsn`, so the arrival edge integrates both.
BUNDLES = """@stage: bundles
β : ℝ₊₊
R : ℝ₊₊
y : ℝ
y ~ N(0,1)
z : ℝ
z ~ N(0,1)
Γ(k : ℝ) := (0,1]

[id=arvl_to_dcsn, (k : ℝ, y, z) : !arvl -> (k_d : ℝ) : !dcsn] {
    k_d = k + y + z
}
[id=dcsn_to_cntn, (k_d, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ) : !cntn] {
    a = k_d - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V        = c + β*V[>]           :: [id=value]
    D_{k_d}V = c                    :: [id=marginal]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<]     = E_{y,z}(V)           :: [id=value]
    D_{k}V[<] = E_{y,z}(R*D_{k_d}V)  :: [id=marginal]
}
[id=policy, (V[>] : ℝ @ !vlu) -> c] {
    c = argmax_{cp : Γ(k_d)}(cp + β*V[>]) :: [id=objective]
}
"""


def bundles(backward=None, declarations=None, decision=None):
    """The bundle stage with its arrival block, its shock declarations or its
    decision block replaced."""
    text = BUNDLES
    for old, new in (("""    V[<]     = E_{y,z}(V)           :: [id=value]
    D_{k}V[<] = E_{y,z}(R*D_{k_d}V)  :: [id=marginal]
""", backward),
                     ("y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\n", declarations),
                     ("""    V        = c + β*V[>]           :: [id=value]
    D_{k_d}V = c                    :: [id=marginal]
""", decision)):
        if new is not None:
            assert text.count(old) == 1
            text = text.replace(old, new)
    return text


# the files the tests add to the package's smallest registry
# (`bellman.refusal_examples.REGISTRY_FILES`): a range source, a calibration
# source with a parent beside its top key, a replacing selection of the
# two-node stage beside its addition, and a recipe naming its trellis file,
# its stage's file and two slots, one of them in a range list alone; a
# methods list takes no slot (specification 0.7, D3)
SMALL_REGISTRY = {
    "calibration/terminal.yml": "calibration:\n  R: 1.04\n",
    "calibration/child.yml": "parent: calibration/main\ncalibration:\n  R: 1.03\n",
    "stages/two_nodes/methods.other.bl": ("@methods: two_nodes\n"
                                          "n_k : ℕ              :: [\"number of candidate levels of the search\"]\n"
                                          "cntn_to_dcsn.method : !vfi(n_c=n_k)\n"
                                          "cntn_to_dcsn.handler : \"test:other\"\n"),
    "spec.yml": ("trellis: trellis.yml\nstages:\n  two_nodes:\n"
                         "    stage: stages/two_nodes/two_nodes.bl\n"
                         "    calibration: {all: [calibration/main, $fill], '0-0': [calibration/terminal, $terminal]}\n"
                         "    settings: {all: [settings/main, $fill]}\n"
                         "    methods: {all: [stages/two_nodes/methods.bl]}\n"),
}

# The application registries and the two small applications written for
# the tests. Each methods file stands beside the stage file it extends.
CONS_PORT = ROOT / "applications/cons-port/declaration"
PORTFOLIO = ROOT / "applications/portfolio-choice/declaration"
NEW_APPLICATIONS = ROOT / "packages/bellman/tests/additions/new-applications"


@pytest.fixture(scope="session")
def registry(tmp_path_factory):
    """The directory of the small registry: the two-node stage with its
    addition and a replacing selection, one source of each valued kind, a
    range source, a source with a parent, a period template, a trellis file
    of three periods and a recipe with two slots."""
    from bellman.refusal_examples import write_registry
    return write_registry(tmp_path_factory.mktemp("registry"), SMALL_REGISTRY)


@pytest.fixture(scope="session")
def port_cons():
    """The trellis of the lesson `05-periods-and-trellises.ipynb`, bound as
    the lesson binds it in its cell `trellis-c21`: six periods of the stages
    `port`, `cons` and `disc`, each occurrence calibrated, methodized and
    configured with the files its record names in the application's
    declaration folder. The consumption stage is the folder's own, which
    states no derivative until its addition appends the envelope line, so
    the trellis is read bound from its recipe: every route is then
    certified and the view draws both backward graphs (decision SD-63)."""
    from bellman.trellis import (
        calibrate_trellis,
        configure_trellis,
        elaborate_trellis,
        methodize_trellis,
    )
    from bellman.trellis import load_recipe
    syntactic = load_recipe(CONS_PORT, "spec.port-cons.yml")
    calibrated = calibrate_trellis(elaborate_trellis(syntactic), syntactic)
    return configure_trellis(methodize_trellis(calibrated, syntactic), syntactic)


# a complete calibration of each of the four corpus stages and a second one
# differing in one value, for the laws L1 to L3 of AMD-FAC-002 §3: cons and
# port from applications/cons-port/reference/legacy/syntax/calibration.yaml; the two applications
# whose folders hold no calibration file take the values of MIXTURE_VALUES in
# test_refusals.py (cons_savings_iid) and values inside the declared sets
# (ez_savings)
CORPUS_CALIBRATIONS = {
    "cons": {"ρ": 6.0},
    "port": {"R": 1.02, "μ_Ψ": 0.028927, "σ_Ψ": 0.143486, "μ_θ": -0.01125, "σ_θ": 0.15, "ρ_ζ": 0.0},
    "ez_savings": {"β": 0.96, "ρ": 2.0, "γ": 5.0, "μ_Ψ": 0.0, "σ_Ψ": 0.1},
    "cons_savings_iid": {"β": 0.96, "γ": 2.0, "R": 1.02, "μ_y": 0.0, "σ_y": 0.1, "p_zero": 0.3},
}
SECOND_CALIBRATIONS = {
    "cons": {"ρ": 2.0},
    "port": {**CORPUS_CALIBRATIONS["port"], "R": 1.04},
    "ez_savings": {**CORPUS_CALIBRATIONS["ez_savings"], "β": 0.95},
    "cons_savings_iid": {**CORPUS_CALIBRATIONS["cons_savings_iid"], "β": 0.95},
}

# the discounting stage of docs/Bellman-Sym/06-period.md §1.1, whose continuation
# field k_next joins the investment stage's k through the connector {k_next: k};
# the corpus holds no stage with that field, so the text stands here
DISC_TEXT = """@stage: disc
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d) : !dcsn -> (k_next : ℝ₊) : !cntn] {
    k_next = a_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""

# the stages of the provisional tests of AMD-COMP-001's selector (runs 2 and
# 3; the corpus holds no stage with two state fields that both leave and
# enter it, nor one that carries one field unchanged): `TWO_FIELDS`, a stage
# that arrives at `a` and `b` and continues to `a` and `b`, the two occurrences
# of the simultaneous swap of §3.1 and of a crossed authored pair; and
# `UNCHANGED`, a stage that carries `a` unchanged from arrival to continuation
# and discounts its value, the two occurrences of §4 whose direction no name
# settles. Each is written once here and read by name under distinct keys.
TWO_FIELDS = """@stage: two_fields
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ₊, b : ℝ₊) : !arvl -> (a_d : ℝ₊, b_d : ℝ₊) : !dcsn] {
    a_d = a
    b_d = b
}
[id=dcsn_to_cntn, (a_d, b_d) : !dcsn -> (a : ℝ₊, b : ℝ₊) : !cntn] {
    a = a_d
    b = b_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""
UNCHANGED = """@stage: unchanged
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = a_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""
# the three stage texts of run 3 of the same plan (route compatibility and
# transport): `THREE_FIELDS`, a stage that carries `a`, `b` and `c`
# unchanged, whose three-cycle of authored pairs tells the forward
# permutation of a point from the inverse that carries a derivative's
# components; `BOUNDED`, a stage whose state lies in `[a_min, inf)` with the
# bound a parameter, one parameter of a period in two occurrences of one
# period and two parameters in two periods; and `NO_LAW`, a stage whose
# law of motion draws a shock of a family the package does not construct, so
# that its forward builders graph is held as a refusal and no forward builder
# writes a joint law on its continuation state (a backward header lists no
# state since AAS's ruling of 12 October 2026, so a continuation state is
# declared by a forward block alone)
THREE_FIELDS = """@stage: three_fields
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ, b : ℝ, c : ℝ) : !arvl -> (a_d : ℝ, b_d : ℝ, c_d : ℝ) : !dcsn] {
    a_d = a
    b_d = b
    c_d = c
}
[id=dcsn_to_cntn, (a_d, b_d, c_d) : !dcsn -> (a : ℝ, b : ℝ, c : ℝ) : !cntn] {
    a = a_d
    b = b_d
    c = c_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""
BOUNDED = """@stage: bounded
a_min : ℝ
β : (0,1)
[id=arvl_to_dcsn, (a : [a_min, inf)) : !arvl -> (a_d : ℝ) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d) : !dcsn -> (a : [a_min, inf)) : !cntn] {
    a = a_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""
NO_LAW = """@stage: no_law
β : (0,1)
ε : ℝ
ε ~ Weird(0, 1)
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d, ε) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = a_d + ε
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*E_{ε}(V[>])
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# a branching stage whose two branches continue to `(x_up, y_up)` and
# `(x_dn, y_dn)` and whose decision value states its derivatives in the
# coordinates of the decision perch, so that two occurrences join both
# branches into one destination with every backward component paired through
# the route (run 3)
MERGE = """@stage: merge
β : (0,1)
[id=arvl_to_dcsn, (x : ℝ₊, y : ℝ₊) : !arvl -> (x_d : ℝ₊, y_d : ℝ₊) : !dcsn] {
    x_d = x
    y_d = y
}
[id=dcsn_to_cntn, (x_d, y_d, d : !ctrl @ {up, down}) : !dcsn -> ()] {
    [label=up,   () -> (x_up : ℝ₊, y_up : ℝ₊) : !cntn] {
        x_up = x_d
        y_up = y_d
    }
    [label=down, () -> (x_dn : ℝ₊, y_dn : ℝ₊) : !cntn] {
        x_dn = x_d
        y_dn = y_d
    }
}
[id=cntn_to_dcsn, (V_up[>] : ℝ @ !vlu, V_dn[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V          = (V_up[>], V_dn[>])[d]
    D_{x_d}V   = (D_{x_up}V_up[>], D_{x_dn}V_dn[>])[d]
    D_{y_d}V   = (D_{y_up}V_up[>], D_{y_dn}V_dn[>])[d]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V_up[>], V_dn[>]) : !cntn -> (d : {up, down} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_up[>], V_dn[>])
}
"""


def relay(name, arrivals, continuations):
    """The text of a stage named `name` that arrives at the state fields
    `arrivals`, sums them and continues to each of `continuations`, every
    field in ℝ₊, its value discounted: the stages of a relay whose
    inferred pairs form overlapping cycles (run 3)."""
    ins = ", ".join(f"{a} : ℝ₊" for a in arrivals)
    outs = ", ".join(f"{c} : ℝ₊" for c in continuations)
    lines = "\n".join(f"    {c} = s" for c in continuations)
    return (
        f"@stage: {name}\nβ : (0,1)\n"
        f"[id=arvl_to_dcsn, ({ins}) : !arvl -> (s : ℝ₊) : !dcsn] {{\n    s = {' + '.join(arrivals)}\n}}\n"
        f"[id=dcsn_to_cntn, (s) : !dcsn -> ({outs}) : !cntn] {{\n{lines}\n}}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n    V = β*V[>]\n}\n"
        "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
    )


# the registry of a period of two stages that declare one parameter name
# (AMD-COMP-001 §2.3): the two-node stage, whose `β` lies in ℝ₊₊ and whose
# calibration file supplies it, beside the discounting stage above, whose `β`
# lies in (0,1) and whose calibration list holds a slot alone; the two-node
# stage continues to `a`, at which the discounting stage arrives, and the
# discounting stage's `k_next` is the next period's `k`
SHARED_REGISTRY = {
    "stages/disc/disc.bl": DISC_TEXT,
    "period.yml": "name: two_stages\nstages: [two_nodes, disc]\nconnectors: []\n",
    "trellis.yml": "periods:\n  - {template: period.yml, repeat: 2}\n"
                   "inter_connectors:\n  - {k_next: k}\n",
    "spec.yml": ("trellis: trellis.yml\nstages:\n  two_nodes:\n"
                 "    stage: stages/two_nodes/two_nodes.bl\n"
                 "    calibration: {all: [calibration/main, $fill]}\n"
                 "    settings: {all: [settings/main, $fill]}\n"
                 "    methods: {all: [stages/two_nodes/methods.bl]}\n"
                 "  disc:\n    stage: stages/disc/disc.bl\n"
                 "    calibration: {all: [$disc_fill]}\n"),
}


@pytest.fixture(scope="session")
def shared_registry(tmp_path_factory):
    """The directory of the registry of two stages sharing `β`."""
    from bellman.refusal_examples import write_registry
    return write_registry(tmp_path_factory.mktemp("shared"), SHARED_REGISTRY)


# the durables registry of AMD-FAC-002 §5, the folder `declaration/` of the
# model folder, and its two recipes (F15): the full recipe lists tenure, which
# constructs since the first build of branching (step F); the two-stage recipe
# omits it and names the trellis file of the two consumption stages and the
# bequest
DURABLES = ROOT / "applications/durables/declaration"
TWO_STAGES = "spec.two-stages.yml"
# the registries of three other models, each the folder `declaration/` of its
# model folder
RETIREMENT = ROOT / "applications/retirement-choice/declaration"
PENSION = ROOT / "applications/pension-retirement/declaration"
HOUSING = ROOT / "applications/housing-frictions/declaration"
# the placeholder values of the pension registry's `$fill`, inside the declared
# sets and no calibration of the model (examples/pension-retirement/expected.md §7)
PENSION_FILL = {"calibration": {"β": 0.9, "ρ": 2.0, "r_f": 0.02, "r_p": 0.03, "χ_s": 0.1,
                                "μ_w": 0.0, "σ_w": 0.1, "w_R": 0.5}}
CHILDBEARING = ROOT / PRELIMINARY / "de-la-croix-pommeret-2021"
# the taste for children, which the paper gives as a distribution across women and does not
# report: a value inside its declared set and no calibration of the model
# (examples/de-la-croix-pommeret-2021/expected.md §1)
CHILDBEARING_FILL = {"calibration": {"ω": 1.0}}
# the two entrepreneur stages, which an amendment of their own constructs (E14), stood in by a
# standard stage declaring the same arrival and continuation fields, all that a period's joins read
ENTREPRENEUR_STANDINS = {
    "young_entrepreneur": """@stage: young_entrepreneur

Xa := ℝ₊
Y  := ℝ₊₊
Θ  := ℝ₊

[id=arvl_to_dcsn, (a_ye : Xa, y_ye : Y, θ_ye : Θ) : !arvl -> (a : Xa, y : Y, θ : Θ) : !dcsn] {
    a = a_ye
    y = y_ye
    θ = θ_ye
}

[id=dcsn_to_cntn, (a, y, θ) : !dcsn -> (a_ye_ea : Xa, y_ye_ea : Y, θ_ye_ea : Θ, a_ye_wk : Xa, y_ye_wk : Y, θ_ye_wk : Θ) : !cntn] {
    a_ye_ea = a
    y_ye_ea = y
    θ_ye_ea = θ
    a_ye_wk = a
    y_ye_wk = y
    θ_ye_wk = θ
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
""",
    "old_entrepreneur": """@stage: old_entrepreneur

Xa := ℝ₊
Y  := ℝ₊₊
Θ  := ℝ₊

[id=arvl_to_dcsn, (a_oe : Xa, θ_oe : Θ) : !arvl -> (a : Xa, θ : Θ) : !dcsn] {
    a = a_oe
    θ = θ_oe
}

[id=dcsn_to_cntn, (a, θ) : !dcsn -> (a_oe_ed : Xa, θ_oe_ed : Θ, a_oe_rt : Xa) : !cntn] {
    a_oe_ed = a
    θ_oe_ed = θ
    a_oe_rt = a
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
""",
}


def wage_schedule():
    """The writer of the durables application's wage schedule (A56), read from
    its file: the route of E36 runs it between `load_recipe` and the verbs."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("durables_wage_schedule",
                                                  DURABLES.parent / "code/wage_schedule.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.write_wage_schedule

# an addition and a settings source for each of the four corpus stages, for the laws
# L2 (K) and L3 (M, K): cons and port from their additions and the cons-port settings;
# the two stages whose folders hold no addition take an unsaved one that
# represents the decision value, and one setting
CORPUS_METHODS = {
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
CORPUS_SETTINGS = {
    "cons": CONS_SETTINGS,
    "port": CONS_SETTINGS,
    "ez_savings": {"n_m": 8},
    "cons_savings_iid": {"n_m": 8},
}

SELECTIONS = tuple((v, d, g) for v in ("initial", "builders") for d in ("backward", "forward")
                   for g in ("builder", "sub-builder", "primitive", "combined", "factored"))


def apart_from_the_address(table):
    """A definitions table with every record's address set aside.

    A record of a top-level item is addressed by the file position it was
    written at (AMD-SG-017 §4), which names the file as the caller of the
    parser named it and is absent from a term decoded from a saved AST, so two
    stages of one file agree in every other field of every record whatever each
    one names the file."""
    import dataclasses
    return {identity: dataclasses.replace(record, address="") for identity, record in table.items()}


def graphs_differ(stage, other):
    """The selections at which two stages' graphs differ, a refused graph
    counting as equal to a refusal under the same rule at the same term
    address. The snapshot holds each corpus stage fixture to its recording,
    so a stage whose graphs equal a fixture's has the recorded graphs."""
    from bellman.stage.grains import graph_of
    from bellman.refusals import NotConstructed

    def outcome(version, selection):
        level, direction, grain = selection
        try:
            return graph_of(version, level, direction, grain)
        except NotConstructed as refusal:
            return (refusal.rule, refusal.address)
    return [selection for selection in SELECTIONS if outcome(stage, selection) != outcome(other, selection)]


def flat(text):
    """A printed text without its white space, so that two breakings of one
    rule compare equal (AMD-SG-034 §4 item 10)."""
    return "".join(text.split())


def section(card, heading):
    """The lines of one section of a printed card: the line of its heading,
    which for `Source` names the file after two spaces, and the lines of its
    content, up to the next line at column zero, which is the next section's
    heading, the light line before the footer or the heavy line that closes
    the card, without the blank line before it; `[]` where the card has no
    such section. The blank lines between two entries of `Operations` are
    kept."""
    lines = card.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line == heading or line.startswith(heading + "  ")), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i][:1] not in ("", " ")), len(lines))
    while end > start + 1 and not lines[end - 1]:
        end -= 1
    return lines[start:end]


def builder_cards(stage):
    """Every builder of a stage with its card, as pairs `(builder, card)`,
    the backward builders and then the forward ones; a graph the
    construction refused has none."""
    from bellman.refusals import NotConstructed

    cards = []
    for graph in (stage.builder.bwd, stage.builder.fwd):
        try:
            names = graph.list()
        except NotConstructed:
            continue
        cards.extend((graph[name], str(graph[name])) for name in names)
    return cards


def rules(lines):
    """The rules of the entries of an `Operations` section, in order,
    flattened: in each entry, the lines from its label `rule:` to the blank
    line that closes the entry, the region note included, without the
    label."""
    kept, inside = [], False
    for line in lines:
        body = line.strip()
        if body.startswith("rule:"):
            inside = True
            kept.append(body[len("rule:"):])
        elif not body:
            inside = False
        elif inside:
            kept.append(body)
    return flat("\n".join(kept))


def drawn_card(path, title):
    """The fenced text block of the example `path` that opens with
    `title`."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    start = lines.index(title)
    return "\n".join(lines[start:next(i for i in range(start, len(lines)) if lines[i].strip() == "```")])


# --- a held term read at numbers (lane C of the internal developer release 0.01) ---

# the sets the language names by a word, each as the test a number passes to
# be a member
NUMBER_SETS = {
    "ℝ": lambda number: -math.inf < number < math.inf,
    "ℝ₊": lambda number: 0 <= number < math.inf,
    "ℝ₊₊": lambda number: 0 < number < math.inf,
}
# the mark after the name of a function read at the continuation or the
# arrival perch, as a card prints it, by the perch of an identity and by the
# perch a stage file's mark names, `c[>]`
PERCH_MARKS = {"cntn": "≻", "arvl": "≺", "Continuation": "≻", "Arrival": "≺"}
# the comparisons by the sign a predicate holds, and the signs of the written
# relations by their class name
COMPARISONS = {"<": operator.lt, "<=": operator.le, "=": operator.eq, ">=": operator.ge, ">": operator.gt}
SIGNS = {"Lt": "<", "Le": "<=", "Eq": "=", "Ge": ">=", "Gt": ">"}


def name_at_numbers(reference):
    """The name under which the numbers of `AtNumbers` give a reference its
    value: the name the file writes, with `≻` after a function read at the
    continuation perch and `≺` after one read at the arrival perch (`V≻`,
    `c≻`, `m_d≻`, `𝑑𝑢𝑖𝑛𝑣`, `ρ`, `a`), a field a stage file writes under a
    perch mark likewise (`c[>]` as `c≻`), and a law of motion by the block
    that writes it (`dcsn_to_cntn`)."""
    from bellman.native.identity import Identity
    from bellman.native.records import ResolvedName
    from bellman.syntax import terms as T

    if isinstance(reference, T.Sym):
        reference = reference.symbol
    if isinstance(reference, T.Variable):
        side = type(getattr(reference.when, "side", None)).__name__
        return f"{reference.name}{PERCH_MARKS.get(side, '')}"
    if isinstance(reference, (T.Constant, T.Var)):
        reference = reference.name
    if isinstance(reference, T.Coordinate):
        reference = reference.stem
    if isinstance(reference, ResolvedName):
        reference = reference.identity
    if not isinstance(reference, Identity):
        return str(reference)
    if reference.kind == "g":
        return reference.address
    mark = PERCH_MARKS.get(reference.perch, "") if reference.kind == "function" else ""
    return f"{reference.field}{mark}"


def exact(number):
    """A number as a fraction where it is finite, a decimal written in a
    file or a test read at its decimal value, so that the arithmetic of the
    tests is exact; an infinity as a float."""
    if isinstance(number, bool):
        raise TypeError("a truth value is no number")
    if isinstance(number, (int, Fraction)):
        return Fraction(number)
    if isinstance(number, float):
        return Fraction(str(number)) if math.isfinite(number) else number
    if number in ("inf", "-inf"):
        return float(number)
    raise TypeError(f"{number!r} is no number")


def _numbers(values):
    """The values with every number made exact; a function or a set is kept."""
    return {name: exact(value) if isinstance(value, (int, float, Fraction)) and not isinstance(value, bool)
            else value for name, value in values.items()}


def _integer_root(number, degree):
    """The integer whose `degree`-th power is `number`, or None."""
    guess = round(number ** (1 / degree))
    return next((k for k in (guess - 1, guess, guess + 1) if k >= 0 and k ** degree == number), None)


def _power(base, exponent):
    """`base` to the power `exponent`: exact where the exponent is an integer,
    or where the root it takes of a positive fraction is a fraction; a float
    otherwise."""
    if isinstance(base, Fraction) and isinstance(exponent, Fraction):
        if exponent.denominator == 1:
            return base ** exponent.numerator
        if base > 0:
            roots = [_integer_root(part, exponent.denominator) for part in (base.numerator, base.denominator)]
            if None not in roots:
                return Fraction(*roots) ** exponent.numerator
    return float(base) ** float(exponent)


def _spread(arguments):
    """The arguments of an application, one tuple spread into its items, as a
    function of several coordinates is applied to a point."""
    arguments = tuple(arguments)
    return arguments[0] if len(arguments) == 1 and isinstance(arguments[0], tuple) else arguments


def _named(reference, values):
    """The value `values` gives a name; infinity for `inf`."""
    name = name_at_numbers(reference)
    if name == "inf":
        return math.inf
    if name not in values:
        raise KeyError(f"the held term names {name}, and the numbers give it no value")
    value = values[name]
    return exact(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value


def _bound_names(bound):
    """The names a comprehension binds, in order."""
    from bellman.syntax import terms as T

    if isinstance(bound, T.Subject):
        return [name_at_numbers(item) for item in bound.coordinates]
    if isinstance(bound, T.Tuple):
        return [name_at_numbers(item) for item in bound.items]
    return [name_at_numbers(bound)]


def _sides(statement):
    """The two sides of an equation, held as a comparison or as a written
    equation."""
    if hasattr(statement, "relation"):
        assert statement.relation == "=", statement
        return statement.left, statement.right
    return statement.lhs, statement.rhs


def _member(element, held_set, values):
    """Whether a number, or a tuple of numbers, is a member of a held set: a
    set the language names by a word, a set the numbers give by name, an
    interval, a comprehension, a product, a finite set, or the value of a
    correspondence at a point, which the numbers give as the test of
    membership."""
    from bellman.syntax import terms as T

    if isinstance(held_set, T.Space):
        held_set = held_set.set
    if isinstance(held_set, T.Named):
        if held_set.name in NUMBER_SETS:
            return NUMBER_SETS[held_set.name](element)
        named = _named(held_set.name, values)
        return named(element) if callable(named) else _member(element, named, values)
    if isinstance(held_set, T.Interval):
        bounds = held_set.bounds
        lower = -math.inf if bounds.lower in (None, "-inf") else _value(bounds.lower, values)
        upper = math.inf if bounds.upper in (None, "inf") else _value(bounds.upper, values)
        above = element >= lower if isinstance(bounds.left, T.Closed) else element > lower
        below = element <= upper if isinstance(bounds.right, T.Closed) else element < upper
        return above and below
    if isinstance(held_set, T.Comprehension):
        names = _bound_names(held_set.bound)
        point = element if len(names) > 1 else (element,)
        inner = {**values, **dict(zip(names, point))}
        if held_set.base is not None and not _member(element, held_set.base, values):
            return False
        return all(_value(condition, inner) for condition in held_set.conds)
    if isinstance(held_set, T.Product):
        return len(element) == len(held_set.factors) and all(
            _member(item, factor, values) for item, factor in zip(element, held_set.factors))
    if isinstance(held_set, T.FiniteSet):
        return any(element == _value(member, values) for member in held_set.members)
    # the value of a correspondence at a point is the test of membership in
    # it; the value of a function at a point, a number, is the set that
    # holds that number alone
    test = _value(held_set, values)
    return test(element) if callable(test) else element == test


def _value(term, values):
    """The value of a held term at the numbers `values`: a number, a truth
    value, a tuple, or a function of numbers."""
    from bellman.native import predicates as P
    from bellman.native.identity import Identity
    from bellman.native.records import ResolvedName
    from bellman.stage.term_operations import kuhn_tucker
    from bellman.syntax import terms as T
    from bellman.typing import typed_expressions as S

    if isinstance(term, bool):
        return term
    if isinstance(term, (int, float, Fraction)):
        return exact(term)
    if isinstance(term, (str, Identity, ResolvedName, T.Sym, T.Constant, T.Variable)):
        return _named(term, values)
    if isinstance(term, T.Number):
        return exact(term.value)
    if isinstance(term, T.Neg):
        return -_value(term.operand, values)
    arithmetic = {T.Add: operator.add, T.Sub: operator.sub, T.Mul: operator.mul, T.Div: operator.truediv}
    if type(term) in arithmetic:
        return arithmetic[type(term)](_value(term.left, values), _value(term.right, values))
    if isinstance(term, T.Pow):
        return _power(_value(term.base, values), _value(term.exponent, values))
    if isinstance(term, T.Tuple):
        return tuple(_value(item, values) for item in term.items)
    if isinstance(term, (S.Apply, T.Call)):
        function = _value(term.function if isinstance(term, S.Apply) else term.fun, values)
        if not callable(function):
            raise TypeError(f"{term!r} applies a value that is no function")
        return function(*_spread(_value(argument, values) for argument in term.args))
    if isinstance(term, P.Compare):
        return COMPARISONS[term.relation](_value(term.left, values), _value(term.right, values))
    if isinstance(term, T.Rel):
        sign = SIGNS[type(term.op).__name__]
        return COMPARISONS[sign](_value(term.left, values), _value(term.right, values))
    if isinstance(term, T.Between):
        middle = _value(term.middle, values)
        return (COMPARISONS[SIGNS[type(term.lo).__name__]](_value(term.lower, values), middle)
                and COMPARISONS[SIGNS[type(term.hi).__name__]](middle, _value(term.upper, values)))
    if isinstance(term, (P.And, P.Or)):
        left, right = _value(term.left, values), _value(term.right, values)
        return (left and right) if isinstance(term, P.And) else (left or right)
    if isinstance(term, P.Not):
        return not _value(term.operand, values)
    if isinstance(term, P.Member):
        return _member(_value(term.subject, values), term.set, values)
    if isinstance(term, (P.Complementarity, T.Slack)):
        # a relation held with its bound states the Kuhn–Tucker system that
        # `kuhn_tucker` builds of the two, which defines the clause
        return _value(kuhn_tucker(term.core, term.bound), values)
    if isinstance(term, T.Operator) and term.head == "D" and len(term.args) == 1:
        # The derivative is supplied by the test; this evaluates no derivative.
        argument = term.args[0]
        applied = isinstance(argument, (S.Apply, T.Call))
        function = (argument.function if isinstance(argument, S.Apply) else argument.fun) if applied else argument
        name = "D_{" + ", ".join(name_at_numbers(item) for item in term.subs) + "}" + name_at_numbers(function)
        derivative = _named(name, values)
        if applied:
            return derivative(*_spread(_value(item, values) for item in argument.args))
        return derivative
    raise TypeError(f"a {type(term).__name__} is not read at numbers here: {term!r}")


def _function(definition, numbers):
    """The function a definition `𝑓(x : X) := body` writes, read at the
    numbers."""
    names = [name_at_numbers(parameter) for parameter in definition.params]
    return lambda *point: _value(definition.body, {**numbers, **dict(zip(names, _spread(point)))})


def _correspondence(definition, numbers):
    """The correspondence a definition `Γ(x : X) := set` writes, giving at a
    point the test of membership in its value."""
    names = [name_at_numbers(parameter) for parameter in definition.params]
    return lambda *point: (lambda element: _member(
        element, definition.body, {**numbers, **dict(zip(names, _spread(point)))}))


def _law(names, lines, numbers):
    """The law of motion whose lines are `lines`, a function of the
    coordinates `names`: each line's right side is read in turn and its left
    side named, and the outputs are given in the order the lines write them,
    one output alone as a number."""
    def law(*point):
        local = {**numbers, **dict(zip(names, _spread(point)))}
        outputs = []
        for line in lines:
            output = name_at_numbers(line.lhs)
            local[output] = _value(line.rhs, local)
            outputs.append(local[output])
        return outputs[0] if len(outputs) == 1 else tuple(outputs)
    return law


def _applies(term, name):
    """Whether a term is the function `name` applied at a point."""
    from bellman.typing import typed_expressions as S

    return isinstance(term, S.Apply) and name_at_numbers(term.function) == name


def _core(rule):
    """The relation a rule states, without its clause: a rule held with its
    bound, `r ⟂ s`, states `r` of its output."""
    from bellman.native import predicates as P

    statement = getattr(rule, "statement", rule)
    return statement.core if isinstance(statement, P.Complementarity) else statement


def terms_inside(term):
    """A held term and every term inside it, the term first."""
    yield term
    if isinstance(term, (tuple, list)):
        for item in term:
            yield from terms_inside(item)
    elif hasattr(term, "__dataclass_fields__") and not isinstance(term, type):
        for field in term.__dataclass_fields__:
            yield from terms_inside(getattr(term, field))


def reads(term, name):
    """Whether a held term reads the name `name`, as `name_at_numbers` writes
    it, anywhere inside it."""
    from bellman.native.identity import Identity
    from bellman.native.records import ResolvedName
    from bellman.syntax import terms as T

    references = (Identity, ResolvedName, T.Sym, T.Constant, T.Variable)
    return any(isinstance(item, references) and name_at_numbers(item) == name for item in terms_inside(term))


def _point_of(rule, name):
    """The names of the coordinates at which a rule reads the function
    `name`: the arguments of the first application of `name` in the rule's
    statement whose arguments are coordinates, `(a,)` of
    `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a))`; or, where the statement writes `name` bare and
    the rule's `on` is the membership of a point of several coordinates in
    its domain, `𝑐≻ ≤ 𝑢_c_inv(β · 𝑑𝑉_a≻) on (a_nxt_adj, h_nxt_adj, z_nxt_adj)
    ∈ …`, the coordinates of that point (`card-redesign.md` §2, change 4);
    None where the rule has neither."""
    from bellman.syntax import terms as T

    statement = getattr(rule, "statement", rule)
    for term in terms_inside(statement):
        if _applies(term, name):
            arguments = term.args[0].items if len(term.args) == 1 and isinstance(term.args[0], T.Tuple) else term.args
            if all(isinstance(argument, (T.Sym, T.Constant, str)) for argument in arguments):
                return [name_at_numbers(argument) for argument in arguments]
    point = _point_named(rule)
    if point is not None and name in _bare_names(statement):
        return point
    return None


def _point_named(rule):
    """The names of the coordinates of the point a rule's region note names,
    `(a_nxt_adj, h_nxt_adj, z_nxt_adj)` of `on (a_nxt_adj, h_nxt_adj,
    z_nxt_adj) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊`; None where the note names no point of
    several coordinates."""
    from bellman.native import predicates as P
    from bellman.syntax import terms as T

    region = getattr(rule, "on", None)
    if isinstance(region, P.Member) and isinstance(region.subject, T.Tuple):
        return [name_at_numbers(item) for item in region.subject.items]
    return None


def _bare_names(statement):
    """The names a statement writes bare, applied to no argument: every
    reference in it that stands in no function position of an application."""
    from bellman.native.identity import Identity
    from bellman.native.records import ResolvedName
    from bellman.syntax import terms as T
    from bellman.typing import typed_expressions as S

    references = (Identity, ResolvedName, T.Sym, T.Constant, T.Variable)
    # the function position of every application, with the terms inside it
    applied = {id(inner) for term in terms_inside(statement) if isinstance(term, (S.Apply, T.Call))
               for inner in terms_inside(term.function if isinstance(term, S.Apply) else term.fun)}
    names = {name_at_numbers(term) for term in terms_inside(statement)
             if isinstance(term, references) and id(term) not in applied}
    names.update("D_{" + ", ".join(name_at_numbers(item) for item in term.subs) + "}" + name_at_numbers(term.args[0])
                 for term in terms_inside(statement)
                 if isinstance(term, T.Operator) and term.head == "D" and len(term.args) == 1
                 and not isinstance(term.args[0], (S.Apply, T.Call)) and id(term) not in applied)
    return names


def _at_point(rule, numbers):
    """The numbers with the `Where` clauses of a rule read (`_where`) and,
    where the rule's region note names a point of several coordinates, every
    function the statement writes bare read at that point: a name whose
    value is a function of numbers is given its value at the point, so that
    `𝑐≻ ≤ 𝑢_c_inv(β · 𝑑𝑉_a≻)` reads `𝑐≻` and `𝑑𝑉_a≻` at
    `(a_nxt_adj, h_nxt_adj, z_nxt_adj)` (`card-redesign.md` §2, change 4)."""
    numbers = _where(rule, numbers)
    point = _point_named(rule)
    if point is None or any(name not in numbers for name in point):
        return numbers
    values = tuple(numbers[name] for name in point)
    for name in _bare_names(getattr(rule, "statement", rule)):
        if callable(numbers.get(name)):
            numbers[name] = numbers[name](*values)
    return numbers


def _where(rule, numbers):
    """The numbers with the names of the `Where` clauses of a rule added,
    each clause giving the names on its left side the values of its right
    side, `(a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔≻(m, z_d, c, h_choice)`."""
    from bellman.syntax import terms as T

    numbers = dict(numbers)
    for clause in getattr(rule, "where", ()):
        names, value = _sides(clause)
        targets = names.items if isinstance(names, T.Tuple) else (names,)
        point = _value(value, numbers)
        point = point if len(targets) > 1 else (point,)
        numbers.update({name_at_numbers(target): item for target, item in zip(targets, point)})
    return numbers


class AtNumbers:
    """A held term read at numbers: every name the term mentions is given
    the number, the function of numbers or the set that `values` gives it,
    under the name `name_at_numbers` writes, and the term is evaluated in
    exact rational arithmetic wherever the numbers allow. A relation held
    with its bound, `r ⟂ s`, reads as the Kuhn–Tucker system `kuhn_tucker`
    builds of the two, the language's definition of the clause.

    Calling the object gives the value of a term. `stage` adds the stage's
    own definitions to the numbers and `rows` the outputs a builder's rows
    define; `rule` reads a rule a card prints, its `Where` clauses first;
    `admitted` gives the values a rule admits for its output at one point;
    `demand` reads a relation on an unknown function at one point of its
    quantifier; `one_function` says whether one function meets a list of
    such demands."""

    def __call__(self, term, values):
        return _value(term, _numbers(values))

    def stage(self, stage, values):
        """`values` with the definitions of the stage added, each read at
        these numbers: a named set by its name (`Xa`), a function and a
        correspondence by theirs (`𝑑𝑢𝑖𝑛𝑣`, `Γ`), the correspondence giving at
        a point the test of membership in its value, and a law of motion by
        its block (`dcsn_to_cntn`), giving the outputs its lines write, in
        their order. A name `values` gives keeps the value given."""
        numbers = _numbers(values)
        for record in stage.definitions.values():
            name = name_at_numbers(record.identity)
            if name in numbers:
                continue
            if record.kind == "set":
                numbers[name] = record.equations[0]
            elif record.kind == "function":
                numbers[name] = _function(record.equations[0], numbers)
            elif record.kind == "correspondence":
                numbers[name] = _correspondence(record.equations[0], numbers)
            elif record.kind == "g":
                lines = [stage.definitions[address].equations[0] for address in record.equations]
                numbers[name] = _law([coordinate for coordinate, _ in record.coordinates], lines, numbers)
        return numbers

    def rows(self, builder, values):
        """`values` with each output that an Aggregation row of the builder
        defines at a point added, the rows read in order. An output whose
        rule holds it at a point of coordinates, `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) ⟂ a ≥ 0`
        or `𝑚_d≻(a) = a + 𝑐≻(a)`, is a correspondence where its rule carries a
        clause or its carrier is a correspondence (`Xa ⇉ ℝ₊₊`): at a point, the
        test a number passes where it lies in the carrier's codomain, where
        the carrier names one, and the rule holds with the output read as that
        number. It is a function otherwise, whose value at a point is the side
        of its rule opposite the output: the interior value, for an inequality
        without a clause, by the ruling of 22 September 2026. A name `values`
        gives keeps the value given."""
        from bellman.native.predicates import Complementarity
        from bellman.stage.boxes import kind_of
        from bellman.typing import typed_expressions as S

        numbers = _numbers(values)
        for key in builder.primitives.list():
            if kind_of(builder.primitives[str(key)].box) != "Aggregation":
                continue
            record = builder.primitives[str(key)].denote()
            for wire in record.outputs:
                name = name_at_numbers(wire.identity)
                rules = [rule for rule in wire.rules if _point_of(rule, name) is not None]
                if name in numbers or not rules:
                    continue
                clause = isinstance(getattr(rules[0], "statement", rules[0]), Complementarity)
                if clause or "⇉" in wire.type:
                    codomain = getattr(wire.mathematical_type.carrier, "codomain", None)
                    # a correspondence's carrier is a map into the power set
                    # of the set its values lie in, `Xa ⇉ ℝ₊₊`
                    if isinstance(codomain, S.PowerSet):
                        codomain = codomain.domain
                    numbers[name] = self.correspondence(rules[0], name, numbers, codomain)
                else:
                    numbers[name] = self.function(rules[0], name, numbers)
        return numbers

    def rule(self, rule, values):
        """The truth of a rule at numbers: its clauses under `Where` read
        first, each giving the names on its left side the values of its right
        side, then, where its region note names a point of several
        coordinates, every function its statement writes bare read at that
        point, then its statement. A rule is a `Rule` a card prints or a
        statement alone."""
        return _value(getattr(rule, "statement", rule), _at_point(rule, _numbers(values)))

    def admitted(self, rule, output, values):
        """The values a rule admits for its output at one point, as the test
        a number passes: a number `x` is admitted where the rule holds with
        the output named `output` (`c≻`) read as `x` at the point the numbers
        give."""
        return lambda x: self.rule(rule, {**values, output: lambda *point: x})

    def correspondence(self, rule, output, values, codomain=None):
        """The correspondence a rule holds its output to: at a point, the test
        a number `x` passes where it lies in `codomain` and the rule holds with
        the output read as `x` there; the point names the coordinates at which
        the rule reads the output."""
        names = _point_of(rule, output)

        def at(*point):
            numbers = {**values, **dict(zip(names, _spread(point)))}
            admitted = self.admitted(rule, output, numbers)
            return lambda x: (codomain is None or _member(x, codomain, numbers)) and admitted(x)
        return at

    def function(self, rule, output, values):
        """The function a rule holds its output to: at a point, the value of
        the side of the rule opposite the output, read there."""
        names, core = _point_of(rule, output), _core(rule)
        sides = (getattr(core, "left", None), getattr(core, "right", None))

        def is_output(side):
            """Whether a side is the output at the point, applied to it or
            written bare where the region note names the point."""
            return _applies(side, output) or (
                _point_named(rule) is not None and output in _bare_names(side))

        if not any(is_output(side) for side in sides):
            raise TypeError(f"the rule {rule!r} holds no side that is {output} at a point")
        other = sides[1] if is_output(sides[0]) else sides[0]
        return lambda *point: _value(other, _at_point(rule, {**values, **dict(zip(names, _spread(point)))}))

    def demand(self, relation, values):
        """What a relation on an unknown function demands at one point of its
        quantifier, the binders read at `values`: the pair `(argument, value)`
        of the equation `f(argument) = value` the relation states there, or
        None where the number of a binder lies outside the set it ranges
        over, so that the relation demands nothing there. `relation` is the
        set of functions a relation defines, as `signature()` answers it:
        `{f ∈ F | ∀ a ∈ Xa, ∀ x ∈ 𝑐≻(a): f(a + x) = x}`."""
        from bellman.syntax import terms as T

        numbers = _numbers(values)
        (unknown,) = _bound_names(relation.bound)
        (statement,) = relation.conds
        while isinstance(statement, T.Operator) and statement.head == "forall":
            for binder in statement.subs:
                name = name_at_numbers(binder.var)
                if name not in numbers:
                    raise KeyError(f"the relation binds {name}, and the numbers give it no value")
                if not _member(numbers[name], binder.set, numbers):
                    return None
            (statement,) = statement.args
        left, right = _sides(statement)
        applied, value = (left, right) if _applies(left, unknown) else (right, left)
        if not _applies(applied, unknown):
            raise TypeError(f"the statement of the relation applies no unknown {unknown}: {statement!r}")
        point = _spread(_value(argument, numbers) for argument in applied.args)
        return (point[0] if len(point) == 1 else point), _value(value, numbers)

    @staticmethod
    def one_function(demands):
        """Whether one function meets every demand: no two demands ask it for
        two values at one argument. A demand is a pair `(argument, value)`;
        None stands for no demand."""
        asked = {}
        for demand in demands:
            if demand is not None and asked.setdefault(demand[0], demand[1]) != demand[1]:
                return False
        return True


@pytest.fixture(scope="session")
def at_numbers():
    """`at_numbers(term, values)`: a held term read at numbers, with the
    readings `stage`, `rows`, `rule`, `admitted`, `correspondence`,
    `function`, `demand` and `one_function` of `AtNumbers`, so that an
    acceptance item states what a relation holds at points and not only how
    it prints."""
    return AtNumbers()


# --- unit J of the model interface specification 0.4: the copies the package's tests read ---


def declarations_copy(folder):
    """Copies under `folder` of the portfolio model's declaration folder and
    of cons-port's declaration folder (`PORTFOLIO`, `CONS_PORT`), each at
    the path of the application's `declaration/` in the repository; answers the copied
    registry and the copied trellis file of records
    `trellis.port-cons-vfi.yml`, the one trellis file of the two orders that
    is still written as records since the two cons-port folders became one
    on 28 October 2026 (the files of the orders themselves are recipes,
    which `load_trellis` does not read). Every file the trellis file names
    stands inside the copied `declaration/` (unit J's plan, Task 1, and
    ruling J-P12; decisions SD-33 and SD-53 before the consolidation)."""
    registry = Path(folder) / "applications/portfolio-choice/declaration"
    shutil.copytree(PORTFOLIO, registry)
    declaration = Path(folder) / "applications/cons-port/declaration"
    shutil.copytree(CONS_PORT, declaration)
    return registry, declaration / "trellis.port-cons-vfi.yml"


def _rewritten(path, old, new):
    """Writes the file `path` with its one occurrence of `old` replaced by
    `new`; a file that holds `old` other than once is refused, so that a
    change of the repository's file is seen in the copy's builder."""
    text = Path(path).read_text(encoding="utf-8")
    assert text.count(old) == 1, (path, old)
    Path(path).write_text(text.replace(old, new), encoding="utf-8")


def emptied_port_cons(folder):
    """The copy of `trellis.port-cons.yml` under `folder`
    (`declarations_copy`) with its connector and its one inter-period
    mapping each emptied to `{}`, so that no line joins `port`'s `m_next` to
    `cons`'s `m` or `disc`'s `a` to the next period's `k`; answers the
    copied trellis file (unit J's plan, Task 2, and ruling J-P12)."""
    _, trellis = declarations_copy(folder)
    _rewritten(trellis, "- {w: m}", "- {}")
    _rewritten(trellis, "- {disc.a: k}", "- {}")
    return trellis


def emptied_portfolio(folder):
    """The copy of the portfolio model's registry under `folder`
    (`declarations_copy`) with the connector of `period.yml` and the
    inter-period mapping of `trellis.yml` each emptied to `{}`; answers the
    copied registry (unit J's plan, Task 2)."""
    registry, _ = declarations_copy(folder)
    _rewritten(registry / "period.yml", "- {m_next: m}", "- {}")
    _rewritten(registry / "trellis.yml", "- {disc.a: k}", "- {}")
    return registry


def emptied_portfolio_entry(folder):
    """The copy `emptied_portfolio` whose entry of `trellis.yml` writes its
    own `connectors: [{}]`, which stands over the connectors of the period
    file the entry names; answers the copied registry (unit J's plan,
    Task 2)."""
    registry = emptied_portfolio(folder)
    _rewritten(
        registry / "trellis.yml",
        "- {template: period.yml, repeat: 6}",
        "- {template: period.yml, repeat: 6, connectors: [{}]}",
    )
    return registry


def five_mappings_port_cons(folder):
    """The copy of `trellis.port-cons.yml` under `folder` whose
    `inter_connectors` writes one empty mapping for each of its five
    adjacent pairs, its connector `{m_next: m}` kept; answers the copied
    trellis file (unit J's plan, Task 2)."""
    _, trellis = declarations_copy(folder)
    _rewritten(trellis, "  - {disc.a: k}\n", "  - {}\n" * 5)
    return trellis


def two_cons_period(folder):
    """The copy `emptied_port_cons` whose period holds `cons_one` and
    `cons_two` in place of `cons`, two occurrences of `cons.bl`, each with
    the record of `cons`, so that both arrive at `m` and both continue to
    `a`; answers the copied trellis file (unit J's plan, Task 2)."""
    trellis = emptied_port_cons(folder)
    lines = trellis.read_text(encoding="utf-8").splitlines(keepends=True)
    (first,) = [n for n, line in enumerate(lines) if line.startswith("      cons: {")]
    # the record of `cons` is written on two lines
    record = lines[first] + lines[first + 1]
    _rewritten(
        trellis,
        record,
        record.replace("cons: {", "cons_one: {", 1) + record.replace("cons: {", "cons_two: {", 1),
    )
    return trellis


def emptied_connector_port_cons(folder):
    """The copy of `trellis.port-cons.yml` under `folder`
    (`declarations_copy`) with its connector `{m_next: m}` emptied to `{}`
    and its inter-period mapping `{disc.a: k}` kept, so that in no period does a
    line join `port`'s `m_next` to `cons`'s `m`; answers the copied trellis
    file (unit J's plan, Task 4, and ruling J-P12)."""
    _, trellis = declarations_copy(folder)
    _rewritten(trellis, "- {w: m}", "- {}")
    return trellis


def emptied_pension(folder):
    """A copy under `folder` of the pension model's registry, at its path in
    the repository, whose one standing inter-period mapping is emptied to
    `{}`, so that in `periods[1]` and every earlier period no join reads
    `retiree_saving`'s two continuation states `y_f_ret` and `y_p_ret`;
    answers the copied registry (unit J's brief, J-D11; unit J's plan,
    Task 4, and ruling J-P12)."""
    registry = Path(folder) / "applications/pension-retirement/declaration"
    shutil.copytree(PENSION, registry)
    _rewritten(
        registry / "trellis.yml",
        "  - {y_f_wk: y_f_w, y_p_wk: y_p_w, y_f_rt: y_f_r, y_p_rt: y_p_r, "
        "y_f_ret: y_f_r, y_p_ret: y_p_r}\n",
        "  - {}\n",
    )
    return registry


@pytest.fixture(scope="session")
def three_value_outputs():
    """Three authored value outputs exercise multiline evaluation labels."""
    text = corpus_text("cons")
    replacements = (
        ("(V : [-inf, inf) @ !vlu) : !dcsn]",
         "(V : [-inf, inf) @ !vlu, W : ℝ @ !vlu, Z : ℝ @ !vlu) : !dcsn]"),
        ("V        = 𝑢(c) + V[>]          :: [id=value]",
         "V = 𝑢(c) + V[>]\n    W = V\n    Z = V"),
        ("(V) : !dcsn -> (V[<] : ℝ @ !vlu)",
         "(V, W, Z) : !dcsn -> (V[<] : ℝ @ !vlu, W[<] : ℝ @ !vlu, Z[<] : ℝ @ !vlu)"),
        ("V[<] = V                        :: [id=value]",
         "V[<] = V\n    W[<] = W\n    Z[<] = Z"),
    )
    for before, after in replacements:
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    return stage_from_text(text, "three_value_outputs.bl")


@pytest.fixture
def durables_vfi_recipe(tmp_path):
    """A copied registry adds value iteration to the adjuster's methods."""
    registry = tmp_path / "durables"
    shutil.copytree(DURABLES, registry)
    addition = "stages/adjuster_cons/methods.vfi.bl"
    (registry / addition).write_text(
        '@methods: adjuster_cons\n'
        'cntn_to_dcsn.method : !vfi\n'
        'cntn_to_dcsn.handler : "fues-durables:make_adjuster_vfi"\n',
        encoding="utf-8",
    )
    text = (registry / TWO_STAGES).read_text(encoding="utf-8")
    before = "methods: {all: [stages/adjuster_cons/methods.bl]}"
    assert text.count(before) == 1
    recipe = "spec.two-stages.vfi.yml"
    (registry / recipe).write_text(text.replace(before,
        f"methods: {{all: [stages/adjuster_cons/methods.bl, {addition}]}}"), encoding="utf-8")
    return registry, recipe


# --- AMD-MT-003: one labeled section for the fixtures of each unit of the
# build, so that the units write disjoint lines of this file ---

# --- AMD-MT-003 unit A: grids ---

# The stage of example E09 of the amendment's numerical examples: the state m
# on Xm, the control c whose feasible set at m is [0, m], and the finite set
# B = {1, 2} of resources; the tests type the backward decision builder
# cntn_to_dcsn with !vfi and a grid.
GRID_STAGE = """@stage: grids
B := {1, 2}
Xm := ℝ₊
Γ_c(m : Xm) := [0, m]
𝑢(c : ℝ₊) := c
[id=dcsn_to_cntn, (m : Xm, c : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + V[>]) :: [id=optimality]
}
"""

# The same choice with a second state z carried to the continuation perch,
# so that a grid on (m, z) can name a factor for m alone, and the product
# X2 on which points of two coordinates are declared.
TWO_STATE_GRID_STAGE = """@stage: grids
Xm := ℝ₊
X2 := ℝ × ℝ
Γ_c(m : Xm) := [0, m]
𝑢(c : ℝ₊) := c
[id=dcsn_to_cntn, (m : Xm, z : ℝ, c : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ₊, z_n : ℝ) : !cntn] {
    a = m - c
    z_n = z
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + V[>]) :: [id=optimality]
}
"""

# A choice of two controls, c on [0, m] and h on [0, m - c], whose joint
# feasible set is coupled, in the form of the durables application's
# adjuster_cons stage.
TWO_CONTROL_GRID_STAGE = """@stage: grids
B := {1, 2}
Xm := ℝ₊
Γ_c(m : Xm) := [0, m]
Γ_h(x : ℝ₊) := [0, x]
𝑢(c : ℝ₊, h : ℝ₊) := c + h
[id=dcsn_to_cntn, (m : Xm, c : ℝ₊ @ !ctrl, h : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m - c - h
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c, h) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c, h) + V[>]
}
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊ @ !ctrl, h : ℝ₊ @ !ctrl) : !dcsn] {
    (c, h) = argmax_{c : Γ_c(m), h : Γ_h(m - c)}(𝑢(c, h) + V[>]) :: [id=optimality]
}
"""

# the settings the grids of the tests name, declared as a methods file
# declares them, and their values: two control nodes, m in {1, 2} and z in
# {-1, 1}
GRID_SETTINGS = (
    "n_c : ℕ\nm_lo : ℝ₊\nm_hi : ℝ₊\nn_m : ℕ\nz_lo : ℝ\nz_hi : ℝ\nn_z : ℕ\n"
)
GRID_VALUES = {"n_c": 2, "m_lo": 1.0, "m_hi": 2.0, "n_m": 2, "z_lo": -1.0, "z_hi": 1.0, "n_z": 2}


@pytest.fixture(scope="session")
def grid_stage():
    """`grid_stage(entries, declarations="", text=GRID_STAGE)`: a stage named
    `grids`, the stage of example E09 unless `text` names another, unioned
    with a methods file that declares the settings `GRID_SETTINGS`, then
    `declarations`, then the typing `entries`; elaborated anew at each call,
    since `configure` and `methodize` bind the stage they are called on."""
    from bellman.stage import elaborate_stage

    def make(entries, declarations="", text=GRID_STAGE):
        methods = "@methods: grids\n" + GRID_SETTINGS + declarations + entries
        return elaborate_stage({
            "stage": {"text": text, "origin": "grids.bl"}, "calibration": {}, "settings": {},
            "methods": [{"text": methods, "origin": "methods.bl"}],
        })

    return make


# --- AMD-MT-003 unit B: representations and explicit blocks ---

# the origin of the perfect-foresight stage of the refusal examples, whose
# consumption function and values are known as expressions
PERFECT_FORESIGHT_ORIGIN = "perfect_foresight.bl"


def perfect_foresight_text(*changes, table=False):
    """The text of the perfect-foresight stage of the refusal examples, whose
    derived parameters are h and R_n, with each pair (line as written, line
    as changed) of `changes` replaced once; with `table`, two parameters `K`
    and `Y`, three numbers each, and a line of the arrival block that reads
    them as an authored table, `W = evaluate(K, Y, k)`, at the address
    `dcsn_to_arvl.table`. The explicit checks, the representation checks and
    the derived checks read this one stage."""
    from bellman.refusal_examples import PERFECT_FORESIGHT

    text = PERFECT_FORESIGHT
    for written, changed in changes:
        assert text.count(written) == 1, written
        text = text.replace(written, changed)
    if not table:
        return text
    growth = 'Γ : ℝ₊₊          :: ["permanent income growth factor"]\n'
    value = "    V[<] = Γ^(1-ρ) * V              :: [id=value]\n"
    assert text.count(growth) == 1 and text.count(value) == 1
    return text.replace(
        growth, growth + "K : ℝ × ℝ × ℝ    :: [\"the knots of the table\"]\n"
        "Y : ℝ × ℝ × ℝ    :: [\"the values of the table\"]\n"
    ).replace(value, value + "    W = evaluate(K, Y, k)            :: [id=table]\n")


# CDC's calibration of the perfect-foresight stage, r = ϑ = 0.04, g = 0.02
# and ρ = 2, at which human wealth h = 1/(1 - Γ/R) is 52 and the marginal
# propensity to consume κ is 0.04/1.04
PERFECT_FORESIGHT_CALIBRATION = {"β": 1 / 1.04, "ρ": 2.0, "R": 1.04, "Γ": 1.02}


@pytest.fixture(scope="session")
def perfect_foresight():
    """The symbolic perfect-foresight stage; a test that binds methods on it
    binds a copy (`copy_native`)."""
    return stage_from_text(perfect_foresight_text(), PERFECT_FORESIGHT_ORIGIN)


@pytest.fixture(scope="session")
def perfect_foresight_explicit(perfect_foresight):
    """The perfect-foresight stage with the explicit solution of its policy
    builder, the addition `EXPLICIT_POLICY` of the refusal examples, read
    once; a test that binds it further binds a copy."""
    from bellman.native.hypergraphs import copy_native
    from bellman.refusal_examples import EXPLICIT_POLICY

    return copy_native(perfect_foresight).methodize(
        {"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"})


@pytest.fixture
def nodal_family():
    """A representation family registered for the duration of one test,
    `!nodal`, which accepts only its own nodes and so samples a function on
    its grid, the endogenous grid method's pairs included; removed at the
    test's end where the test has not removed it."""
    from bellman.stage.representations import RepresentationFamily, families, register, unregister

    family = register(RepresentationFamily(
        "nodal", {}, ("own nodes",), derivatives=(),
        stored="The values at the nodes of its grid."))
    yield family
    if "nodal" in families():
        unregister("nodal")


# --- AMD-MT-003 unit C: derived parameters ---

# the methods addition that defines the marginal propensity to consume κ, the
# method's derived parameter, which stage.par lists once it is read
DERIVED_ADDITION = {
    "text": "@methods: perfect_foresight\n"
    'κ := 1 - (R*β)^(1/ρ)/R   :: ["the marginal propensity to consume"]\n',
    "origin": "closed_form.bl",
}
# the buffer-stock stage and its baseline calibration, which supplies no μ_ξ
DERIVED_BUFFER_STOCK = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
DERIVED_BUFFER_STOCK_CALIBRATION = {
    "R": 1.03, "β": 0.96, "Γ": 1.03, "ρ": 2.0, "σ_ψ": 0.1, "σ_ξ": 0.1, "p_zero": 0.005,
}


def derived_buffer_stock_text(scale="σ_ξ"):
    """The text of the buffer-stock stage file, which defines the log-mean
    μ_ξ := -log(1 - p_zero) - σ_ξ^2/2 of the positive transitory draw as a
    derived parameter, with `scale` the standard deviation of the logarithm
    of that draw. With `scale="μ_ξ"` it is the temporary variant of
    implementation §1, whose derived scale is negative where σ_ξ² exceeds
    −2 log(1 − p_zero)."""
    text = (ROOT / DERIVED_BUFFER_STOCK).read_text(encoding="utf-8")
    if scale != "σ_ξ":
        assert text.count("LogNormal(μ_ξ, σ_ξ)") == 1
        text = text.replace("LogNormal(μ_ξ, σ_ξ)", f"LogNormal(μ_ξ, {scale})")
    return text


@pytest.fixture(scope="session")
def derived_parameters():
    """The fixtures of the derived checks, as one record: `text`, the
    perfect-foresight stage text of unit B's section, and `stage(*changes)`,
    a symbolic stage of it made anew with each pair of
    `perfect_foresight_text` replaced; `origin`, the file name the stage
    carries; `addition`, the methods addition that defines κ; `calibration`,
    CDC's calibration; `buffer_stock(scale)`, the symbolic buffer-stock stage
    of `derived_buffer_stock_text`, made anew; and
    `buffer_stock_calibration`. Each stage is made at each call, since a
    binding verb binds the stage it is called on."""
    return types.SimpleNamespace(
        text=perfect_foresight_text(),
        stage=lambda *changes: stage_from_text(
            perfect_foresight_text(*changes), PERFECT_FORESIGHT_ORIGIN
        ),
        origin=PERFECT_FORESIGHT_ORIGIN,
        addition=DERIVED_ADDITION,
        calibration=PERFECT_FORESIGHT_CALIBRATION,
        buffer_stock=lambda scale="σ_ξ": stage_from_text(
            derived_buffer_stock_text(scale), DERIVED_BUFFER_STOCK
        ),
        buffer_stock_calibration=DERIVED_BUFFER_STOCK_CALIBRATION,
    )


# --- AMD-MT-003 unit D: the numerical applications ---

# the numerical module of the perfect-foresight application, which the tests
# load from its file, since the folder of an application is no package
PERFECT_FORESIGHT_MODULE = (
    ROOT / "applications" / "consumption-perfect-foresight-crra" / "code" / "closed_form_check.py"
)
# the documented baseline interval of the comparisons, 401 levels of resources
# from -30 to 50 (implementation §1), and the second calibration of CDC's
# application, at which human wealth is 1/(1 - 1.01/1.04)
PERFECT_FORESIGHT_RESOURCES = (-30.0, 50.0, 401)
PERFECT_FORESIGHT_ALTERNATIVE = {"β": 0.90, "ρ": 2.0, "R": 1.04, "Γ": 1.01}
# the grid of savings of the near-limit route, from just above the natural
# borrowing limit L, by these two offsets, with this many points, so that its
# endogenous grid covers total wealth from about 1e-4 to about 2
PERFECT_FORESIGHT_NEAR_LIMIT = (1e-4, 2.0, 50)


@functools.cache
def closed_form_check():
    """The numerical module of the perfect-foresight application, loaded
    once from its file, so that the tests read the functions the notebook
    reads."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("closed_form_check", PERFECT_FORESIGHT_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def perfect_foresight_solves():
    """The expensive solves of item 4 and of item 2's preparation, each made
    once: `check`, the module; `closed` and `alternative`, the closed-form
    stage at CDC's two calibrations; `resources`, the baseline interval;
    `comparisons`, the comparison of the gridded route with the closed form
    on 5, 50 and 500 savings from -40 to 60 at the first calibration, by the
    count, and `alternative_comparison`, on 50 savings from -33 to 60 at the
    second; and `near`, the near-limit route's gridded stage, with its route
    `near_route`."""
    import numpy as np

    check = closed_form_check()
    closed = check.closed_form_stage()
    resources = np.linspace(*PERFECT_FORESIGHT_RESOURCES)
    alternative = {"calibration": PERFECT_FORESIGHT_ALTERNATIVE}
    limit = closed.par["L"].value
    lower, upper, count = PERFECT_FORESIGHT_NEAR_LIMIT
    near = check.gridded_stage(count, limit + lower, limit + upper)
    return types.SimpleNamespace(
        check=check,
        closed=closed,
        alternative=check.closed_form_stage(alternative),
        resources=resources,
        comparisons={n: check.comparison(n, -40.0, 60.0, resources) for n in (5, 50, 500)},
        alternative_comparison=check.comparison(50, -33.0, 60.0, resources,
                                                calibration=alternative),
        near=near,
        near_route=check.gridded_route(near),
    )


# --- AMD-MT-003 unit D2: the buffer-stock application ---

# the files of the buffer-stock application beside its stage file
# `DERIVED_BUFFER_STOCK`, as its README and its example page name them: the
# methods file, an addition to the stage file; the settings file; and the
# example page, which quotes the three files
BUFFER_STOCK_METHODS = "applications/buffer-stock/declaration/stages/buffer_stock/methods.bl"
BUFFER_STOCK_SETTINGS = "applications/buffer-stock/declaration/settings/buffer_stock.yml"
BUFFER_STOCK_PAGE = "docs/examples/buffer-stock/buffer_stock.md"


@pytest.fixture(scope="session")
def buffer_stock_application(derived_parameters):
    """The buffer-stock application, as one record: `stage(calibration)`,
    the stage `derived_parameters.buffer_stock()` makes of the stage file,
    with its methods file read into it, calibrated by `calibration` and
    configured by its settings file, made anew at each call, since a
    binding verb binds the stage it is called on; `calibration`, the
    baseline calibration of unit C's section; and `methods`, `settings` and
    `page`, the methods file, the settings file and the example page, as
    paths in the repository."""

    def stage(calibration):
        made = derived_parameters.buffer_stock().methodize(ROOT / BUFFER_STOCK_METHODS)
        made.calibrate({"calibration": calibration})
        return made.configure(ROOT / BUFFER_STOCK_SETTINGS)

    return types.SimpleNamespace(
        stage=stage,
        calibration=derived_parameters.buffer_stock_calibration,
        methods=BUFFER_STOCK_METHODS,
        settings=BUFFER_STOCK_SETTINGS,
        page=BUFFER_STOCK_PAGE,
    )


# --- AMD-MT-003 unit E: inspection and the generated references ---

# --- AMD-MT-003 unit E1: the stages of the reference's declaration
# examples ---

# A stage whose arrival value integrates a Markov shock z, drawn from the row
# of its transition matrix that the arrival state z_pre selects, and a shock
# d with a finite law of two points, so that the places E_z and E_d, which
# the declaration examples of !exact_markov, !markov, !markov_expectation and
# !sum name, stand in it.
EXAMPLE_SHOCKS = """@stage: example_shocks

β   : (0,1)    :: ["discount factor"]
ρ_z : [0,1]    :: ["the probability that the Markov state z keeps its value"]
p_d : [0,1]    :: ["the probability of the second point of the shock d"]

z : ℝ₊₊
z ~ MarkovChain(((ρ_z, 1 - ρ_z), (1 - ρ_z, ρ_z)), (1, 2), z_pre)\
    :: ["a Markov state of two points"]
d : ℝ
d ~ Bernoulli(p_d)    :: ["a shock with a finite law of two points"]

[id=arvl_to_dcsn, (k : ℝ₊, z_pre : ℝ₊₊, z, d) : !arvl -> (m : ℝ₊) : !dcsn] {
    m = z*k + d                    :: [id=resources]
}

[id=dcsn_to_cntn, (m) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m                          :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]                     :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{z}(E_{d}(V))         :: [id=value]
}
"""
# the worker's consumption stage of the retirement-choice application, whose
# methods file writes the four lines of the endogenous grid method on the
# policy builder, the last of them an upper envelope, and types that
# envelope by the fast upper-envelope scan in the part `WORKER_CONS_ENVELOPE`
WORKER_CONS = "applications/retirement-choice/declaration/stages/worker_cons/worker_cons.bl"
WORKER_CONS_ENVELOPE = (
    '\n    | upper_env.method : !FUES(m_bar=m_bar) | upper_env.handler : "dcsmm:EGM_UE"]'
)


@pytest.fixture(scope="session")
def example_shocks():
    """The symbolic stage `EXAMPLE_SHOCKS`."""
    return stage_from_text(EXAMPLE_SHOCKS, "example_shocks.bl")


@pytest.fixture(scope="session")
def worker_cons():
    """The symbolic stage of the stage file `WORKER_CONS`."""
    return fresh_stage(WORKER_CONS)


@pytest.fixture(scope="session")
def example_additions():
    """The additions that precede a declaration example of the reference in
    the one call of `methodize` on a stage, by the name of the stage's
    fixture. A call replaces the additions read before, so an example whose
    place an addition writes is read in the same call as that addition: on
    `perfect_foresight_explicit`, the explicit solution of the policy
    builder, whose closing Evaluation the example of !closed_form types; on
    `worker_cons`, the methods file beside the stage file without the typing
    of its upper envelope, whose operator the example of !FUES types."""
    from bellman.refusal_examples import EXPLICIT_POLICY

    methods = ROOT / WORKER_CONS.replace("worker_cons.bl", "methods.bl")
    text = methods.read_text(encoding="utf-8")
    assert text.count(WORKER_CONS_ENVELOPE) == 1
    return {
        "perfect_foresight_explicit": ({"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"},),
        "worker_cons": (
            {"text": text.replace(WORKER_CONS_ENVELOPE, "]"), "origin": "methods.bl"},
        ),
    }
