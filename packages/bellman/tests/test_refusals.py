"""The refusal file, in the third layer of the tests
(`packages/bellman/README.md` §8).

One test per rule name of `RULES`, `TARGET_RULES` and `FACTORY_RULES` of
`bellman.refusals`: the smallest example that breaks the
rule is provoked and refused under that rule, at that address, with a message
that names the objects involved. The examples themselves stand in the package,
`bellman.refusal_examples.EXAMPLES`, which the catalogue of the rules reads as
well, so that the package and its test state one fact one way (AMD-SG-022 §2,
§11 item 6); this file reads the table and provokes each. Each refusal of graph
construction prints its file and its line and column range, or its address when
it has no position, before the message, and its rule after it.
"""
import pytest

from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import EXAMPLES, INVERSE_EULER
from bellman.stage import admitted_methods, load_stage
from bellman.trellis import load_recipe
from bellman.refusal_catalogue import catalogue, refusal_of
from bellman.refusals import (FACTORY_RULES, RULE_B_C, RULES, TARGET_RULES, ConstructionError, FactoryError,
                              NotConstructed, TargetError)
from bellman.stage.grains import graph_of
from conftest import CORPUS, branching, cons_obs_text, corpus_text, shock_branching, stage_from_text

# the value line of the branching fixture, after which its tests write a
# derivative line of the choice value
CHOICE_VALUE = "    V = (V_w[>], V_r[>])[d]                :: [id=choice_value]\n"
# the grid line and the identification of the inverse Euler form, which the
# tests of the candidate rules change
GRID_LINE = "    m[>] = a + c[>]        :: [id=grid]\n"
IDENTIFICATION = "    c = c[>]               :: [id=identification]\n"


def cons_with(written, changed):
    """The consumption stage's text with one line changed, elaborated."""
    text = corpus_text("cons")
    assert text.count(written) == 1, written
    return stage_from_text(text.replace(written, changed), CORPUS["cons"])


def printed(error):
    """The refusal as `ConstructionError.__str__` writes it: the position, or
    the file and the address where it has none, then the message, then the
    address and the rule."""
    if error.line is None:
        return f"{error.file}: address {error.address!r}: {error.message} (rule {error.rule})"
    where = f"{error.file}:{error.line}:{error.column}"
    if error.end_line is not None:
        where += f"-{error.end_line}:{error.end_column}"
    if error.address is None:
        return f"{where}: {error.message} (rule {error.rule})"
    return f"{where}: {error.message} (address {error.address!r}; rule {error.rule})"


@pytest.mark.parametrize("rule", RULES)
def test_the_smallest_example_breaking_a_rule_of_construction_is_refused_under_it(rule, elaborate_text):
    example = EXAMPLES[rule]
    error = refusal_of(example)
    assert isinstance(error, ConstructionError), rule
    assert (error.rule, error.address) == (rule, example.address)
    assert error.file == example.origin
    if example.provokes == "compile_kernel":
        assert error.line is None
    for word in example.words:
        assert word in error.message, (word, error.message)
    assert str(error) == printed(error)
    if rule == "syntax":
        from bellman.refusal_catalogue import text_of

        assert (error.file, error.line, error.column) == ("cons.bl", 16, 40)
        assert str(error).startswith("cons.bl:16:")
        assert text_of(example).splitlines()[15] in str(error)
        assert "\n" + " " * (4 + error.column - 1) + "^" in str(error)
        with pytest.raises(ConstructionError) as refused:
            elaborate_text("@stage: t\n[id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n")
        word = refused.value
        assert (word.rule, word.line, word.column) == ("syntax", 2, 18)
        assert "!contrl" in word.message
        for refusal in (error, word):
            for internal in ("Error trying to process rule", "word_type", "TAGBANG"):
                assert internal not in str(refusal)
    if rule == "typing-entry-unattached":
        # the same refusal for an entry of a block's header, a typing entry
        # before the signature and a handler binding in a group, at the
        # block's address
        for header in ("[id=b, policy.method : !egm, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn]",
                       '[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn | handler : "cons-port:egm"]'):
            with pytest.raises(ConstructionError) as refused:
                elaborate_text(f"@stage: t\n{header} {{\n    y = x\n}}\n")
            assert (refused.value.rule, refused.value.address) == (rule, "b")
        # and for an entry of a nested branch block's header, at the branch's address
        written = "[label=work, () -> (a_w : ℝ₊) : !cntn]"
        for nested in ("[label=work, () -> (a_w : ℝ₊) : !cntn | method : !egm]",
                       '[label=work, () -> (a_w : ℝ₊) : !cntn | handler : "cons-port:egm"]',
                       "[label=work, policy.method : !egm, () -> (a_w : ℝ₊) : !cntn]"):
            with pytest.raises(ConstructionError) as refused:
                elaborate_text(branching((written, nested)))
            assert (refused.value.rule, refused.value.address) == (rule, "dcsn_to_cntn.work")
    if rule == "defined-once":
        assert (error.line, error.column) == (4, 5)
        entry = next(item for item in catalogue() if item.rule == rule)
        assert entry.where == "t.bl, line 4, column 5 (address 'b.second')"
        assert "W = 2*V[>]" in entry.what and "^" in entry.what
        assert entry.why == error.message
        assert "t.bl:3:5 (term address 'b.first')" in entry.why
        assert entry.write == example.write
        assert all(word in entry.write
                   for word in ("Remove one definition", "another name", "`!doc`"))
        documentary = example.text.replace("[id=first, !node]", "[id=first, !doc]")
        assert elaborate_text(documentary).name == "t"
        # a derivative term stated twice in one block, the housing-frictions
        # probe (F68): refused at the second line naming the first
        marginal = "    D_{m_d}V = 𝑑𝑢(c)                :: [id=marginal]\n"
        with pytest.raises(ConstructionError) as refused:
            cons_with(marginal, marginal + "    D_{m_d}V = 2*𝑑𝑢(c)              :: [id=marginal2]\n")
        assert (refused.value.rule, refused.value.address) == (rule, "cntn_to_dcsn.marginal2")
        assert "block 'cntn_to_dcsn' already states D_{m_d}V at" in refused.value.message
        assert "(term address 'cntn_to_dcsn.marginal')" in refused.value.message
    if rule == "name-in-scope":
        # a set a typing names that the stage does not define, the three forms
        # of the cons-port probe (F35) and a product in a set's definition,
        # each refused at the item that names it with the sets in scope; an
        # undefined function stays an external callable, recorded as an
        # obligation and refused by no rule
        for written, changed, address, what in (
            ("ρ : [1, inf)\n", "ρ : [1, inf)\nn_m : Foo\n", "5", "the declaration of 'n_m'"),
            ("(m_d, c : !ctrl @ ℝ₊₊) : !dcsn", "(m_d, c : !ctrl @ Foo) : !dcsn", "dcsn_to_cntn",
             "the header of block 'dcsn_to_cntn', which types c"),
            ("𝑑𝑢(c : ℝ₊₊) := c^(-ρ)", "𝑑𝑢(c : Foo) := c^(-ρ)", "6",
             "the argument 'c' of the function '𝑑𝑢'"),
            ("Xa := ℝ₊\n", "Xa := ℝ₊\nXq := Xm × Foo\n", "4", "the definition of the set 'Xq'"),
        ):
            with pytest.raises(ConstructionError) as refused:
                cons_with(written, changed)
            assert (refused.value.rule, refused.value.address) == (rule, address)
            assert f"{what} names the set 'Foo'" in refused.value.message
            assert "the sets in scope here: Xm, Xa" in refused.value.message
            assert "ℝ, ℝ₊, ℝ₊₊, ℤ, ℕ" in refused.value.message
        # a function of the stage written where a set stands, defined with a
        # parameter list or as the inverse of a function, is refused under
        # the same rule, naming the function and its definition
        for written, changed, address, what, function in (
            ("ρ : [1, inf)\n", "ρ : [1, inf)\nn_m : 𝑑𝑢\n", "5", "the declaration of 'n_m'", "𝑑𝑢"),
            ("Xa := ℝ₊\n", "Xa := ℝ₊\nXq := Xm × 𝑑𝑢\n", "4",
             "the definition of the set 'Xq'", "𝑑𝑢"),
            ("Γ(x : ℝ₊₊) := (0, x]\n", "Γ(x : ℝ₊₊) := (0, x]\n𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\nn_m : 𝑑𝑢𝑖𝑛𝑣\n",
             "9", "the declaration of 'n_m'", "𝑑𝑢𝑖𝑛𝑣"),
        ):
            with pytest.raises(ConstructionError) as refused:
                cons_with(written, changed)
            assert (refused.value.rule, refused.value.address) == (rule, address)
            assert (
                f"{what} names the set {function!r}, which the stage defines as a function at"
                in refused.value.message
            )
            assert "and as no set" in refused.value.message
        marginal = "    D_{m_d}V = 𝑑𝑢(c)                :: [id=marginal]\n"
        stage = cons_with(marginal, marginal.replace("𝑑𝑢(c)", "𝑓𝑜𝑜(c)"))
        assert "external-callable-signature-and-provider" in {
            item.condition for item in stage.obligations()
        }
    if rule == "derivative-coordinate":
        # the value of a branch is a function of that branch's states alone:
        # the pension-retirement probe, a coordinate of the other branch in a
        # derivative of the work value, is refused naming the branch and its
        # coordinates, and the branch's own coordinate is admitted
        def with_marginal(term):
            return branching((CHOICE_VALUE, CHOICE_VALUE
                              + f"    D_{{a_d}}V = ({term}, D_{{a_r}}V_r[>])[d]  :: [id=marginal]\n"))

        with pytest.raises(ConstructionError) as refused:
            elaborate_text(with_marginal("D_{a_r}V_w[>]"))
        assert (refused.value.rule, refused.value.address) == (rule, "cntn_to_dcsn.marginal")
        assert ("names 'a_r', which is no state coordinate of the branch 'work' of the cntn perch"
                in refused.value.message)
        assert "the coordinates of the branch 'work' of the cntn perch are a_w" in refused.value.message
        assert elaborate_text(with_marginal("D_{a_w}V_w[>]")).name == "t"
    if rule == "candidate-coordinate":
        # admitted: the control at the candidates, the decision state (the grid
        # line) and the value candidate an upper envelope compares, as the
        # worker's block of retirement-choice writes them; the value candidate
        # is refused where no envelope reads it (F39)
        value_candidate = GRID_LINE + "    v[>] = 𝑢(c[>]) + V[>]    :: [id=cand_value]\n"
        envelope = "    c = upper_env(m[>], c[>], v[>])    :: [id=envelope]\n"
        with_envelope = INVERSE_EULER.replace(GRID_LINE, value_candidate).replace(IDENTIFICATION, envelope)
        assert elaborate_text(with_envelope).name == "t"
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(INVERSE_EULER.replace(GRID_LINE, value_candidate))
        assert (refused.value.rule, refused.value.address) == (rule, "policy.cand_value")
        assert "writes v[>], a candidate of 'v'" in refused.value.message
        assert "no upper envelope of block 'policy' compares it" in refused.value.message
    if rule == "candidate-read":
        # the grid line, a decision state at the candidates, is read by the
        # Evaluation as the knots of the policy and needs no reader among the
        # lines; the control's candidate is read by the grid line
        closed = "    c = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])     :: [id=closed]\n"
        assert elaborate_text(INVERSE_EULER.replace(IDENTIFICATION, closed)).name == "t"
    if rule == "one-builder-per-output":
        # a second value builder and a second forward builder with the same
        # outputs and perches are refused under this rule and not under
        # `forward-composite` (F17, continued)
        for block, address, first in (
            ("[id=value2, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
             "    V = 2*𝑢(c) + V[>]    :: [id=value]\n}\n", "value2", "cntn_to_dcsn"),
            ("[id=step2, (m, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n    a = m - 2*c\n}\n",
             "step2", "dcsn_to_cntn"),
        ):
            with pytest.raises(ConstructionError) as refused:
                elaborate_text(INVERSE_EULER + block)
            assert (refused.value.rule, refused.value.address) == (rule, address)
            assert f"which block '{first}' already writes" in refused.value.message


def test_a_grid_line_is_compared_with_the_law_of_motion_solved_for_its_decision_state(cons, elaborate_text):
    # the rule grid-line-consistency: the right side of a grid line and the law
    # of motion solved for the decision state at the candidates reduce to one
    # expression by algebraic simplification, every function read as an opaque
    # symbol; the refusal names the line as written and the law of motion so
    # solved (RL5)
    from conftest import ROOT
    from bellman.refusal_examples import INVERSE_EULER

    # the inverse Euler form of the consumption stage, whose policy block writes
    # the grid line `m[>] = a + c[>]` (the corpus writes the maximization alone)
    text = INVERSE_EULER
    grid = "    m[>] = a + c[>]        :: [id=grid]"
    assert text.count(grid) == 1

    def with_grid(right):
        return text.replace(grid, f"    m[>] = {right}    :: [id=grid]")

    # a grid line is read by its value, not by its spelling
    for right in ("c[>] + a", "(a + c[>])*1", "2*(a + c[>]) - a - c[>]"):
        assert elaborate_text(with_grid(right)).name == "t"
    # a decimal literal is read as the rational number its spelling denotes,
    # so 0.9 and 10/9 are reciprocal in the comparison
    law = "    a = m - c\n"
    assert text.count(law) == 1
    assert elaborate_text(with_grid("10*a/9 + c[>]").replace(law, "    a = 0.9*(m - c)\n")).name == "t"
    # a grid line that agrees with the law of motion only under an identity
    # among declared functions is refused, and the message says so
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(with_grid("a + 𝑑𝑢𝑖𝑛𝑣(𝑑𝑢(c[>]))"))
    assert (refused.value.rule, refused.value.address) == ("grid-line-consistency", "policy.grid")
    for words in ("the grid line m[>] = a + 𝑑𝑢𝑖𝑛𝑣(𝑑𝑢(c[>]))", "the law of motion gives m[>] = a + c[>]",
                  "it applies the functions 𝑑𝑢, 𝑑𝑢𝑖𝑛𝑣", "assumes no identity"):
        assert words in refused.value.message, (words, refused.value.message)
    # a law of motion with several outputs is solved through its other lines:
    # on the durables adjuster the housing line gives the control without a
    # candidate
    adjuster = (ROOT / "applications/durables/declaration/stages/adjuster_cons/adjuster_cons.bl"
                ).read_text(encoding="utf-8")
    line = "m[>]          = a_nxt_adj + c[>] + (1 + τ)*h_nxt_adj"
    assert adjuster.count(line) == 1
    assert elaborate_text(adjuster).name == "adjuster_cons"
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(adjuster.replace(line, "m[>]          = a_nxt_adj + c[>] + h_nxt_adj         "))
    assert (refused.value.rule, refused.value.address) == ("grid-line-consistency", "policy.endoggrid")
    for words in ("the grid line m[>] = a_nxt_adj + c[>] + h_nxt_adj",
                  "its lines a_nxt_adj = m - c - (1 + τ)*h_choice and h_nxt_adj = h_choice "
                  "solved for m and h_choice at the candidate c[>]",
                  "the law of motion gives m[>] = a_nxt_adj + c[>] + (1 + τ)*h_nxt_adj",
                  "does not reduce to"):
        assert words in refused.value.message, (words, refused.value.message)
    # a law of motion in which the decision state occurs other than once and
    # affinely is not solved: the grid line is not checked, and no kind of
    # condition is added in the place of the check
    unsolved = elaborate_text(with_grid("a + 5*c[>]").replace("    a = m_d - c\n", "    a = m_d*m_d - c\n"))
    assert ({item.condition for item in unsolved.obligations()}
            == {item.condition for item in cons.obligations()})


@pytest.mark.parametrize("rule", TARGET_RULES)
def test_the_smallest_example_breaking_a_rule_of_the_identity_table_is_refused_under_it(rule):
    example = EXAMPLES[rule]
    error = refusal_of(example)
    assert isinstance(error, TargetError), rule
    assert (error.rule, error.target) == (rule, example.address)
    if example.corpus:
        assert error.stage == example.corpus
    for word in example.words:
        assert word in str(error), (word, str(error))
    if rule == RULE_B_C:
        # a line of a branch is addressed under its label and an occurrence in
        # it by the operator after that (F12), and a line that holds one head
        # twice is one address answering both occurrences, listed once among
        # the places (F62): on the branching stage with a derivative line of
        # the choice value, each target answers its admitted methods, where
        # it was refused under a TargetError before
        stage = stage_from_text(branching((CHOICE_VALUE, CHOICE_VALUE
                                           + "    D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]  :: [id=marginal]\n")))
        assert isinstance(admitted_methods(stage, "dcsn_to_cntn.work.working"), tuple)
        assert isinstance(admitted_methods(stage, "cntn_to_dcsn.marginal.D"), tuple)
        assert [row["address"] for row in stage.places()].count("cntn_to_dcsn.marginal.D") == 1


@pytest.mark.parametrize("rule", FACTORY_RULES)
def test_the_smallest_planted_case_breaking_a_rule_of_the_factory_is_refused_under_it(rule):
    example = EXAMPLES[rule]
    error = refusal_of(example)
    assert isinstance(error, FactoryError), rule
    assert (error.rule, error.address) == (rule, example.address)
    for word in example.words:
        assert word in error.message, (word, error.message)
    assert error.written and error.write, rule
    assert str(error).endswith(f"(rule {rule})")


def test_diagram_period_refuses_an_index_the_trellis_does_not_hold(cons):
    # as `diagram_trellis` refuses one, where Python's own IndexError, or a
    # negative index counted from the end, reached the reader (S11)
    from bellman.period import diagram_period
    trellis = {"periods": [{"stages": {"cons": cons}, "connectors": []}], "inter_connectors": []}
    for index in (5, -1, "0"):
        with pytest.raises(FactoryError) as refused:
            diagram_period(trellis, index)
        assert (refused.value.rule, refused.value.address, refused.value.written) == (
            "trellis-file-shape", "periods", repr(index))
        assert "the trellis holds 1 periods" in refused.value.message
        assert refused.value.write == "an index between 0 and 0"


def test_a_key_written_twice_is_refused_on_every_path_that_reads_a_yaml_file(cons, cons_sources, path_of, tmp_path):
    # one reader reads every YAML file; before it, a calibration or a settings
    # file given by its path took the last value silently, and a methods file
    # raised a bare DuplicateKey (map/bindings B1; S11)
    from bellman.trellis import load_recipe, load_trellis
    from bellman.refusal_examples import write_registry
    calibration = tmp_path / "calibration.yml"
    calibration.write_text("calibration:\n  ρ: 2.0\n  ρ: 3.0\n", encoding="utf-8")
    settings = tmp_path / "settings.yml"
    written = cons_sources["settings"].read_text(encoding="utf-8")
    assert written.count("  n_m: 8000") == 1
    settings.write_text(written.replace("  n_m: 8000", "  n_m: 8000\n  n_m: 10"), encoding="utf-8")
    methods = tmp_path / "methods.yml"
    methods.write_text("stage: cons\nstage: cons\nmethods: []\n", encoding="utf-8")
    trellis = tmp_path / "trellis.yml"
    trellis.write_text(f"periods:\n  - stages:\n      cons: {{stage: {path_of('cons')}, calibration: calibration.yml}}\n"
                       "    connectors: []\ninter_connectors: []\n", encoding="utf-8")
    methodized = copy_native(cons).methodize(cons_sources["methods"])
    for call, path, key, line in ((lambda: copy_native(cons).calibrate(calibration), calibration, "ρ", 3),
                                  (lambda: methodized.configure(settings), settings, "n_m", 7),
                                  (lambda: copy_native(cons).methodize(methods), methods, "stage", 2),
                                  (lambda: load_trellis(trellis), calibration, "ρ", 3)):
        with pytest.raises(FactoryError) as refused:
            call()
        assert (refused.value.rule, refused.value.file, refused.value.written, refused.value.write) == (
            "readable-file", str(path), f"{key!r} at line {line}", "each key once")
        assert f"the key {key!r} is written twice" in refused.value.message
    registry = write_registry(tmp_path / "registry", {"calibration/main.yml": "calibration:\n  β: 0.96\n  β: 0.5\n"})
    with pytest.raises(FactoryError) as refused:
        load_recipe(registry, "spec.yml")
    assert (refused.value.rule, refused.value.write) == ("recipe-source", "each key once")


# the smallest registry's recipe as a recipe writes it, its trellis file and its
# one stage's file named by their paths from the recipe's folder (AAS, 2 October
# 2026); the three tests below remove or change one of the two lines
EXPLICIT_RECIPE = ("trellis: trellis.yml\nstages:\n  two_nodes:\n"
                   "    stage: stages/two_nodes/two_nodes.bl\n"
                   "    calibration: {all: [calibration/main]}\n")


def test_a_recipe_that_names_no_trellis_file_is_refused(tmp_path):
    """A recipe names its trellis file under `trellis:`; a recipe without the
    key is refused under `recipe-shape`, and the file `trellis.yml`, which
    stands in the recipe's folder, is not read in its place."""
    import bellman
    from bellman.refusal_examples import write_registry
    directory = write_registry(tmp_path / "registry",
                               {"spec.yml": EXPLICIT_RECIPE.replace("trellis: trellis.yml\n", "")})
    assert (directory / "trellis.yml").is_file()
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.file, refused.value.address) == (
        "recipe-shape", str(directory / "spec.yml"), "trellis")
    assert str(refused.value).endswith(
        ": the recipe names no trellis file; write `trellis: trellis.yml`, the path from this folder "
        "(rule recipe-shape)")


def test_a_stage_entry_that_names_no_stage_file_is_refused(tmp_path):
    """Each entry of a recipe names its stage file under `stage:`; an entry
    without the key is refused under `recipe-shape` at the entry's address."""
    import bellman
    from bellman.refusal_examples import write_registry
    directory = write_registry(tmp_path / "registry",
                               {"spec.yml": EXPLICIT_RECIPE.replace("    stage: stages/two_nodes/two_nodes.bl\n", "")})
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.file, refused.value.address) == (
        "recipe-shape", str(directory / "spec.yml"), "stages.two_nodes")
    assert str(refused.value).endswith(
        ": the entry `stages.two_nodes` names no stage file; write "
        "`stage: stages/two_nodes/two_nodes.bl`, the path from this folder (rule recipe-shape)")


def test_a_stage_file_is_read_at_the_path_its_entry_writes_and_never_found_by_its_key(tmp_path):
    """No stage file is found by its key: an entry without `stage:` is refused
    although the key's file stands at both places the retired reading by name
    looked, `stages/<key>.bl` and `stages/<key>/<key>.bl`; a written path is
    read as written, here a file whose name is not the key; and a path that
    names no file, or no `.bl` file, is refused as `load_stage` refuses it, at
    the recipe's address of the path."""
    import bellman
    from bellman.refusal_examples import TWO_NODES, write_registry
    unnamed = write_registry(tmp_path / "unnamed", {
        "spec.yml": EXPLICIT_RECIPE.replace("    stage: stages/two_nodes/two_nodes.bl\n", ""),
        "stages/two_nodes.bl": TWO_NODES})
    assert (unnamed / "stages/two_nodes.bl").is_file() and (unnamed / "stages/two_nodes/two_nodes.bl").is_file()
    with pytest.raises(FactoryError) as refused:
        load_recipe(unnamed, "spec.yml")
    assert (refused.value.rule, refused.value.address) == ("recipe-shape", "stages.two_nodes")
    elsewhere = write_registry(tmp_path / "elsewhere", {
        "spec.yml": EXPLICIT_RECIPE.replace("stage: stages/two_nodes/two_nodes.bl", "stage: models/saving.bl"),
        "models/saving.bl": TWO_NODES})
    record = load_recipe(elsewhere, "spec.yml")["periods"][0]["stages"]["two_nodes"]
    assert record["stage"]["origin"] == str(elsewhere / "models/saving.bl")
    for name, written in (("absent", "stages/absent.bl"), ("yaml", "calibration/main.yml")):
        directory = write_registry(tmp_path / name, {
            "spec.yml": EXPLICIT_RECIPE.replace("stage: stages/two_nodes/two_nodes.bl", f"stage: {written}")})
        with pytest.raises(FactoryError) as refused:
            load_recipe(directory, "spec.yml")
        with pytest.raises(FactoryError) as direct:
            load_stage(directory / written)
        assert (refused.value.rule, refused.value.file, refused.value.address, refused.value.written) == (
            "readable-file", str(directory / "spec.yml"), "stages.two_nodes.stage", written)
        assert (refused.value.message, refused.value.write) == (direct.value.message, direct.value.write)


def test_a_parameter_two_stages_of_a_period_declare_is_refused_where_their_sets_or_values_disagree(shared_registry, tmp_path):
    """The refusals of `period-parameter-agreement` beyond the planted case
    (AMD-COMP-001 §2.3), each naming the period, the parameter, the stages
    and their sources: two declared sets whose intersection the package does
    not read, ℝ₊₊ and ℤ, at the elaboration; two sources supplying two
    values, with the notes of a refused binding naming the discounting
    stage's position and the kind; and a value a source supplies that lies
    outside the set another declaring stage writes, 0 in the two-node
    stage's ℝ₊₊ though in the discounting stage's own set."""
    from bellman.refusal_examples import write_registry
    from bellman.trellis import assemble_trellis, elaborate_trellis
    from conftest import SHARED_REGISTRY
    integers = write_registry(tmp_path / "integers", {
        **SHARED_REGISTRY, "stages/disc/disc.bl": SHARED_REGISTRY["stages/disc/disc.bl"].replace("β : (0,1)", "β : ℤ")})
    with pytest.raises(FactoryError) as refused:
        elaborate_trellis(load_recipe(integers, "spec.yml"))
    assert (refused.value.rule, refused.value.address) == ("period-parameter-agreement", "periods[0]")
    assert refused.value.written == "β : ℝ₊₊ in two_nodes; β : ℤ in disc"
    for word in ("two_nodes", "disc", "'β'", "reads no intersection"):
        assert word in refused.value.message
    assert not hasattr(refused.value, "__notes__")
    with pytest.raises(FactoryError) as refused:
        assemble_trellis(shared_registry, "spec.yml", disc_fill={"β": 0.5})
    assert (refused.value.rule, refused.value.address) == ("period-parameter-agreement", "periods[0]")
    assert refused.value.written == "β: 0.96 (calibration/main, $fill); 0.5 ($disc_fill)"
    assert "supply the parameter 'β' with the values 0.96 and 0.5" in refused.value.message
    assert refused.value.__notes__ == ["Stage occurrence: periods[0].stages['disc']", "Binding kind: calibration"]
    widened = write_registry(tmp_path / "widened", {
        **SHARED_REGISTRY, "stages/disc/disc.bl": SHARED_REGISTRY["stages/disc/disc.bl"].replace("β : (0,1)", "β : ℝ₊")})
    with pytest.raises(FactoryError) as refused:
        assemble_trellis(widened, "spec.yml", fill={"β": 0.0}, disc_fill={"β": 0.0})
    assert refused.value.written == "β: 0.0 (calibration/main, $fill); β : ℝ₊₊ in two_nodes"
    assert "the value 0.0 of the parameter 'β', supplied by two_nodes, lies outside the set ℝ₊₊" in refused.value.message
    assert refused.value.__notes__ == ["Stage occurrence: periods[0].stages['two_nodes']", "Binding kind: calibration"]


def test_a_method_the_target_does_not_admit_is_refused_at_its_attachment(cons):
    for target, tag, settings, words in (
        ("policy", "gauss-hermite", {},
         ("Method target 'policy' in stage 'cons'", "builder", "admits", "operator", "E")),
        ("cntn_to_dcsn.value", "egm", {}, ("cntn_to_dcsn.value",)),
        ("policy.cons_choice.solve", "Linear", {}, ("operator", "solve")),
        ("Γ", "Linear", {}, ("representation method", "definition", "correspondence")),
    ):
        with pytest.raises(TargetError) as refused:
            copy_native(cons).methodize({"methods": [{"on": target, "method": tag,
                                           "settings": settings}]})
        error = refused.value
        assert error.rule == "method-attachment"
        assert error.target == target and error.stage == cons.name
        assert all(word in str(error) for word in words)
    for tag in ("unknown-method", "linear", "rootfind", "value-iteration"):
        with pytest.raises(TargetError, match=rf"unknown method !{tag}.*`method_types` of bellman.stage") as refused:
            copy_native(cons).methodize({"methods": [{"on": "policy", "method": tag}]})
        assert refused.value.rule == "method-attachment"
        assert refused.value.target == "policy" and refused.value.stage == cons.name


def test_method_options_refuse_invalid_authored_or_configured_values(cons, port):
    typo = {"methods": [{"on": "cntn_to_dcsn.value", "method": "Linear",
                          "handler": "test:interpolate",
                          "settings": {"grid": "!Cartesian", "ordrs": {"m_d": "n_m"},
                                       "bounds": {"m_d": ["m_min", "m_max"]}}}]}
    with pytest.raises(TargetError) as refused:
        copy_native(cons).methodize(typo)
    assert all(word in str(refused.value)
               for word in ("cntn_to_dcsn.value", "!Linear", "orders", "ordrs"))
    unknown = {"methods": [{"on": "cntn_to_dcsn.value", "method": "Linear",
                             "settings": {"grid": "!Cartesian", "orders": {"m_d": "n_m"},
                                          "bounds": {"m_d": ["m_min", "m_max"]},
                                          "vendor_flag": True}}]}
    with pytest.raises(TargetError, match="unknown option.*vendor_flag.*handler"):
        copy_native(cons).methodize(unknown)

    source = {"stage": "cons", "methods": [{
        "on": "cntn_to_dcsn.value", "method": "Linear",
        "settings": {"grid": "!Cartesian", "orders": {"m_d": "n_m"},
                     "bounds": {"m_d": ["m_min", "m_max"]}},
    }]}
    # each binding binds a stage of its own (specification 0.6 decision 1 and R4)
    methodized = copy_native(cons).methodize(source)
    with pytest.raises(ValueError, match="n_m"):
        methodized.configure({"settings": {"m_min": 0.1, "m_max": 10.0}})
    for settings, message in (
        ({"n_m": -5, "m_min": 0.1, "m_max": 10.0}, "positive integer"),
        ({"n_m": 8, "m_min": 10.0, "m_max": 1.0}, "ordered pair"),
        ({"n_m": 8, "m_min": float("nan"), "m_max": 10.0}, "ordered pair"),
        ({"n_m": 8, "m_min": 0.1, "m_max": float("inf")}, "ordered pair"),
        ({"n_m": 8, "m_min": -1.0, "m_max": 10.0}, "declared set"),
    ):
        with pytest.raises(ConstructionError, match=message) as refused:
            methodized.configure({"settings": settings})
        assert (refused.value.rule, refused.value.stage,
                refused.value.address) == (
                    "method-option-value", "cons", "cntn_to_dcsn:Evaluation")

    wrong_coordinate = copy_native(cons).methodize({"stage": "cons", "methods": [{
        "on": "cntn_to_dcsn.value", "method": "Linear",
        "settings": {"grid": "!Cartesian", "orders": {"m": "n_m"},
                     "bounds": {"m": ["m_min", "m_max"]}},
    }]})
    with pytest.raises(ValueError, match="coordinate.*m_d"):
        wrong_coordinate.configure({"settings": {
            "n_m": 8, "m_min": 0.1, "m_max": 10.0,
        }})

    quadrature = copy_native(port).methodize({"stage": "port", "methods": [{
        "on": "E_Ψ_θ", "method": "gauss-hermite",
        "settings": {"n_nodes": "nodes"},
    }]})
    for value in (49, [7], [7, 0], [7, True]):
        with pytest.raises(ConstructionError, match="n_nodes"):
            quadrature.configure({"settings": {"nodes": value}})

    positive_real = copy_native(port).methodize({"stage": "port", "methods": [{
        "on": "E_Ψ_θ", "method": "tauchen",
        "settings": {"min_prob": "minimum_probability"},
    }]})
    with pytest.raises(ConstructionError, match="finite value"):
        positive_real.configure({"settings": {"minimum_probability": float("inf")}})



def test_every_rule_of_the_three_vocabularies_has_an_example_in_the_catalogue():
    """A rule with no example is a gap in the catalogue and fails here
    (AMD-SG-022 §2). Each entry names its rule, the place the refusal is
    raised and the refusal as printed."""
    without = [entry.rule for entry in catalogue() if not entry.refusal]
    assert without == [], without
    assert [entry.rule for entry in catalogue()] == list(RULES) + list(TARGET_RULES) + list(FACTORY_RULES)


# the forms a branching block may not take (B02's six, E28's four, E8, E30),
# each beside the example of its rule in the package's table: the case, the
# changes, the rule, the address (None where the parse refuses and names it in
# the message) and the words the refusal names
BRANCHING_REFUSALS = [
    ("B02 1: fewer than two labels", (("d : !ctrl @ {work, retire}", "d : !ctrl @ {work}"),),
     "branch-labels", "dcsn_to_cntn", ("'d'", "1 label")),
    ("B02 2: a label written twice", (("[label=retire,", "[label=work,"),),
     "syntax", None, ("dcsn_to_cntn.work",)),
    ("B02 3 and E8: the branches in another order than the set",
     (("d : !ctrl @ {work, retire}", "d : !ctrl @ {retire, work}"),),
     "branch-labels", "dcsn_to_cntn", ("{retire, work}", "order")),
    ("B02 4: a field written by two branches",
     (("[label=retire, () -> (a_r : ℝ₊) : !cntn]", "[label=retire, () -> (a_w : ℝ₊) : !cntn]"),
      ("a_r = a_d", "a_w = a_d")),
     "declared-once", "dcsn_to_cntn.retire", ("'a_w'", "'work'", "'retire'")),
    ("B02 5 and E28: a nested block without a label", (("[label=retire, ", "[name=retire, "),),
     "branch-form", "dcsn_to_cntn.2", ("label=",)),
    ("E28: a line beside the nested blocks", (("    [label=work,", "    a_x = a_d\n    [label=work,"),),
     "branch-form", "dcsn_to_cntn.1", ("beside",)),
    ("E28: a nested block outside the forward block from the decision perch",
     (("    V = (V_w[>], V_r[>])[d]",
       "    [label=work, () -> (x : ℝ) : !cntn] {\n        x = 1\n    }\n    V = (V_w[>], V_r[>])[d]"),),
     "branch-form", "cntn_to_dcsn.work", ("decision perch",)),
    ("B02 6 and E30: a value line with no tuple indexed by the label coordinate",
     (("V = (V_w[>], V_r[>])[d]", "V = V_w[>]"),),
     "branch-tuple-mismatch", "cntn_to_dcsn.choice_value", ("policy.choice", "no tuple")),
    ("E6: a value read at two positions",
     (("V = (V_w[>], V_r[>])[d]", "V = (V_w[>], V_w[>] + V_r[>])[d]"),
      ("argmax_{d}(V_w[>], V_r[>])", "argmax_{d}(V_w[>], V_w[>] + V_r[>])")),
     "branch-value-position", "cntn_to_dcsn.choice_value", ("V_w[>]", "'work'", "'retire'")),
]


@pytest.mark.parametrize("case", BRANCHING_REFUSALS, ids=lambda case: case[0])
def test_a_malformed_branching_block_is_refused_under_its_rule(case, elaborate_text):
    _, changes, rule, address, words = case
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(branching(*changes))
    error = refused.value
    assert error.rule == rule and (address is None or error.address == address), (error.rule, error.address)
    assert all(word in str(error) for word in words), (words, str(error))


POLICY = ("[id=policy, (V_y[>], V_o[>]) : !cntn -> (c : ℝ₊ @ !ctrl) : !dcsn] {\n"
          "    c = argmax_{c}(E_{s}((V_y[>], V_o[>])[s]))  :: [id=choice]\n}\n")
# the forms a branch a shock selects may not take (E13, E14): the case, the
# changes to `SHOCK_BRANCHING`, the rule, the address and the words the refusal
# names; a top-level item is addressed by its ordinal in the declaration pass,
# so the law at line 4 is the address `4`, as the catalogue's example of
# `distribution-edge` is `3`, and the file position stands in the message
SHOCK_REFUSALS = [
    ("the label shock not listed", (("(a_d, s) : !dcsn -> ()", "(a_d) : !dcsn -> ()"),),
     "branch-labels", "dcsn_to_cntn", ("neither a control nor a shock",)),
    ("the label declared with no law and no role", (("s ~ Categorical((π, 1 - π))\n", ""),),
     "branch-labels", "dcsn_to_cntn", ("neither a control nor a shock", "s ~ Categorical")),
    ("the labels in another order than the branches", (("s : {young, old}", "s : {old, young}"),),
     "branch-labels", "dcsn_to_cntn", ("{old, young}", "order")),
    ("a label shock without a law",
     (("s : {young, old}\ns ~ Categorical((π, 1 - π))\n", "s : {young, old} @ !shck\n"),),
     "branch-law", "dcsn_to_cntn", ("'s'", "has no distribution", "Categorical((p_young, p_old))")),
    ("three weights for two labels", (("Categorical((π, 1 - π))", "Categorical((π, 1 - π, 0))"),),
     "branch-law", "4", ("3 probabilities", "2 labels", "t.bl:4")),
    ("a law that gives the labels no weights", (("Categorical((π, 1 - π))", "N(0, 1)"),),
     "branch-law", "4", ("N(0, 1)", "no probability for each label", "Bernoulli(p)")),
    ("numeric weights that do not sum to one", (("(π, 1 - π)", "(0.3, 0.6)"),),
     "distribution-domain", "t.bl:4", ("0.3, 0.6", "not to one")),
    ("a selection by the shock outside its expectation",
     (("E_{s}((V_y[>], V_o[>])[s])", "(V_y[>], V_o[>])[s]"),),
     "branch-tuple-mismatch", "cntn_to_dcsn.value", ("outside an expectation over it alone",)),
    ("an expectation over the shock of no tuple",
     (("E_{s}((V_y[>], V_o[>])[s])", "E_{s}(V_y[>] + V_o[>])"),),
     "branch-tuple-mismatch", "cntn_to_dcsn.value", ("of no tuple indexed by it",)),
    ("three entries for two labels",
     (("E_{s}((V_y[>], V_o[>])[s])", "E_{s}((V_y[>], V_o[>], V_o[>])[s])"),),
     "branch-tuple-mismatch", "cntn_to_dcsn.value", ("3 entries", "{young, old}")),
    ("a branch value read at two positions",
     (("E_{s}((V_y[>], V_o[>])[s])", "E_{s}((V_y[>], V_y[>] + V_o[>])[s])"),),
     "branch-value-position", "cntn_to_dcsn.value", ("V_y[>]", "'young'", "'old'")),
    ("a control listed beside the drawn label",
     (("(a_d, s) : !dcsn -> ()", "(a_d, c : !ctrl @ ℝ₊, s) : !dcsn -> ()"),),
     "not-constructed", "dcsn_to_cntn", ("the shock 's' selects", "chooses 'c'")),
    ("a policy block beside the draw", (("[id=dcsn_to_arvl", POLICY + "[id=dcsn_to_arvl"),),
     "not-constructed", "dcsn_to_cntn", ("the shock 's' selects", "chooses 'c'")),
]


@pytest.mark.parametrize("case", SHOCK_REFUSALS, ids=lambda case: case[0])
def test_a_malformed_branch_a_shock_selects_is_refused_under_its_rule(case, elaborate_text):
    _, changes, rule, address, words = case
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(shock_branching(*changes))
    error = refused.value
    assert (error.rule, error.address) == (rule, address), (error.rule, error.address)
    assert all(word in str(error) for word in words), (words, str(error))


# the weights of a mixture and of a categorical (AMD-SG-010 §3): the condition
# is retained symbolically and decided when calibration supplies the numbers
MIXTURE_WEIGHTS = ("y ~ Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_y, σ_y)))",
                   "q : [0,1]\ny ~ Mixture((p_zero, 0), (q, LogNormal(μ_y, σ_y)))")
MIXTURE_VALUES = {"β": 0.96, "γ": 2.0, "R": 1.02, "μ_y": 0.0, "σ_y": 0.1, "p_zero": 0.3, "q": 0.7}


def test_mixture_weights_that_do_not_sum_to_one_are_refused_when_calibration_decides_them(
        elaborate_text, text_of):
    written, changed = MIXTURE_WEIGHTS
    text = text_of("cons_savings_iid")
    assert text.count(written) == 1
    stage = elaborate_text(text.replace(written, changed))
    assert [item.condition for item in stage.obligations()
            if item.condition == "distribution-weights-are-a-probability-vector"]
    stage.calibrate(MIXTURE_VALUES)                     # 0.3 and 0.7 sum to one
    with pytest.raises(ConstructionError) as refused:
        stage.calibrate({**MIXTURE_VALUES, "q": 0.5})
    error = refused.value
    assert error.rule == "distribution-domain"
    for word in ("p_zero, q", "cons_savings_iid:distribution:y", "sum to 0.8", "not to one"):
        assert word in error.message, (word, error.message)


def test_a_shock_that_bears_the_name_of_a_named_space_is_refused_where_it_is_written(elaborate_text):
    """A name has one meaning in a stage: a shock declared by its distribution
    alone, under the name of a named space, is refused at the shock's line, the
    message giving the position of the space's definition."""
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\nZ := ℝ₊₊\nZ ~ N(0, 1)\n"
                       "[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n")
    assert refused.value.rule == "one-name-one-meaning"
    for word in ("'Z' is a shock", "named space", "t.bl:2"):
        assert word in refused.value.message, (word, refused.value.message)


def test_a_control_listed_at_a_perch_that_is_neither_the_decision_perch_nor_its_side_s_is_refused(
        text_of, elaborate_text):
    """A perch word on a control's own listing places nothing, so it is
    admitted where it names the decision perch, on any side, or where it names
    the perch of its side, and refused under `field-perch` otherwise
    (AMD-SG-017 §2). On the input side of `cntn_to_dcsn` of `cons.bl`, marked
    `: !cntn`, `c : !cntn` and `c : !dcsn` are admitted and `c : !arvl`, which
    names neither, keeps the refusal of the base with its message."""
    written = "(V[>] : [-inf, inf) @ !vlu, c) : !cntn ->"
    text = text_of("cons")
    assert text.count(written) == 1
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text.replace(written, written.replace(", c)", ", c : !arvl)")), "cons.bl")
    assert refused.value.rule == "field-perch"
    assert refused.value.address == "cntn_to_dcsn"
    for word in ("c on the input side of block 'cntn_to_dcsn'", "a control placed at the arvl perch",
                 "a control is at the decision perch wherever it is listed"):
        assert word in refused.value.message, (word, refused.value.message)


def test_a_control_carried_by_a_perch_mark_is_refused_as_before_the_rule_of_the_perch_word(
        text_of, elaborate_text):
    """AMD-SG-017 §2 admits a perch word on a control's own listing and says
    nothing of a perch mark, which D06 reads as the field at the perch the mark
    names. A control marked for any perch but the decision perch therefore
    keeps the refusal it carried before the rule: on the input side of
    `cntn_to_dcsn` of `cons.bl`, `c[>]` and `c[<]` are refused under
    `field-perch` with the message of a control placed away from the decision
    perch, where `c : !cntn` and `c : !dcsn`, which name a perch of that side
    and the decision perch, elaborate."""
    written = "(V[>] : [-inf, inf) @ !vlu, c) : !cntn ->"
    text = text_of("cons")
    assert text.count(written) == 1
    for marked, perch in (("c[>]", "cntn"), ("c[<]", "arvl")):
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(text.replace(written, written.replace(", c)", f", {marked})")), "cons.bl")
        assert refused.value.rule == "field-perch"
        assert refused.value.address == "cntn_to_dcsn"
        for word in (f"{marked} on the input side of block 'cntn_to_dcsn'",
                     f"a control placed at the {perch} perch"):
            assert word in refused.value.message, (word, refused.value.message)


def test_a_weight_the_declaration_itself_fixes_outside_the_unit_interval_is_refused_where_it_is_written(
        elaborate_text):
    """A weight the file writes as a number is decided at construction, not at
    calibration: a mixture whose first weight is 1.5 is refused where it is
    written, under the same rule."""
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\ny : ℝ\ny ~ Mixture((1.5, 0), (-0.5, N(0, 1)))\n"
                       "[id=b, (x : ℝ, y) : !dcsn -> (w : ℝ) : !dcsn] {\n    w = x + y\n}\n")
    assert refused.value.rule == "distribution-domain"
    for word in ("t:distribution:y", "1.5", "not a probability"):
        assert word in refused.value.message, (word, refused.value.message)


# a chain declaration on a stage whose one block reads the shock, with the
# family term replaced: two arguments and three are the shape `DiscreteMarkov`
# declares, one and four are not (AMD-SG-017 §5.2)
CHAIN_STAGE = ("@stage: t\nz_lo : ℝ\nz_hi : ℝ\nΠ : [0,1]\nz : ℝ\nDECLARATION\n"
               "[id=b, (x : ℝ, z) : !dcsn -> (w : ℝ) : !dcsn] {\n    w = x + z\n}\n")
CHAIN_SHAPES = {
    "z ~ DiscreteMarkov((z_lo, z_hi))": "a call of 1 argument",
    "z ~ DiscreteMarkov(Π, (z_lo, z_hi), x, x)": "a call of 4 arguments",
}


def test_a_distribution_call_of_another_number_of_arguments_than_its_family_takes_is_refused(
        elaborate_text):
    """Every admitted family declares the arguments it takes, and a call of
    another number is refused where it is written, the message naming the
    family and the arguments it takes (AMD-SG-017 §5.2). The declaration as the
    family takes it, with two arguments and with three, elaborates."""
    for declaration, counted in CHAIN_SHAPES.items():
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(CHAIN_STAGE.replace("DECLARATION", declaration))
        assert refused.value.rule == "readable-form"
        # the declaration's address is its file position (AMD-SG-017 §4), so the
        # refusal names the line the declaration is written at
        assert refused.value.address == "t.bl:6"
        for word in ("t:distribution:z", counted, "`DiscreteMarkov` takes 2 or 3 arguments",
                     "the transition probabilities", "the chain's states", "the previous state"):
            assert word in refused.value.message, (declaration, word, refused.value.message)
    for admitted in ("z ~ DiscreteMarkov(Π, (z_lo, z_hi))", "z ~ DiscreteMarkov(Π, (z_lo, z_hi), x)"):
        elaborate_text(CHAIN_STAGE.replace("DECLARATION", admitted))


def test_two_lines_merged_into_one_box_bind_one_method(elaborate_text):
    """A merged box is one operator, so it holds one method (AMD-SG-011 §3);
    the author keeps two methods by keeping the two computations apart with
    `!node`. The two lines are the arrival builder's two value lines, which
    integrate the same pair of shocks; under AMD-MB-001 a derivative line
    forms no box, so the stage carries a second value `W` (MB-T215)."""
    from bellman.stage.binding_verbs import methodize
    from conftest import bundles
    text = bundles(backward="    V[<] = E_{y,z}(V)               :: [id=value]\n"
                            "    W[<] = E_{y,z}(R*W)             :: [id=second]\n",
                   decision="    V = c + β*V[>]                  :: [id=value]\n"
                            "    W = c + β*W[>]                  :: [id=second]\n")
    for old, new in (("(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
                      "(V[>] : ℝ @ !vlu, W[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu, W : ℝ @ !vlu) : !dcsn]"),
                     ("[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl]",
                      "[id=dcsn_to_arvl, (V, W) : !dcsn -> (V[<] : ℝ @ !vlu, W[<] : ℝ @ !vlu) : !arvl]")):
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    stage = elaborate_text(text, "bundles.bl")
    entries = [{"on": "dcsn_to_arvl.value.E_y_z", "method": "!quadrature"},
               {"on": "dcsn_to_arvl.second.E_y_z", "method": "!exact"}]
    with pytest.raises(TargetError) as refused:
        methodize(stage, {"stage": "bundles", "methods": entries})
    assert str(refused.value) == (
        "Method target 'dcsn_to_arvl.second.E_y_z' in stage 'bundles': the lines dcsn_to_arvl.value and "
        "dcsn_to_arvl.second are one box, dcsn_to_arvl:Expectation, at the primitive grain, and the targets "
        "'dcsn_to_arvl.value.E_y_z' and 'dcsn_to_arvl.second.E_y_z' bind two methods to it; a box holds one "
        "method (AMD-SG-006 §4, rule 9). Write one method for both lines, or write `!node` in the annotation of "
        "one of them, so that the two computations stay two boxes.")
    # one method for both lines is admitted, and the merged box answers with it
    for entry in entries:
        entry["method"] = "!quadrature"
    bound = methodize(stage, {"stage": "bundles", "methods": entries})
    merged = bound.builder.bwd.primitives["dcsn_to_arvl:Expectation"]
    assert sorted(merged.methods) == ["dcsn_to_arvl.second:Expectation:1", "dcsn_to_arvl.value:Expectation:1"]
    assert {method.tag for method in merged.methods.values()} == {"quadrature"}


# --- the two second cases of the retired acceptance files --------------------
# The test-only pass of 18 September 2026 retires the acceptance files of
# AMD-SG-006 to AMD-SG-010. Two of their refusals are no second reading of a
# case above: a `!doc` line of a value block, which the policy block's
# exemption does not reach, and the two expectations of `sa_savings.bl` written
# in the reverse order, where the case above is a singular conditioning block.


def test_a_doc_line_of_a_value_block_may_read_a_decision_state(elaborate_text, text_of, cons_obs):
    # a state of the perch at which a backward block's output stands is a
    # coordinate of the output and needs no listing, on a `!doc` line as on an
    # operative one (AAS, 12 October 2026); the documentary line changes no wire
    value_line = '    V        = 𝑢(c) + V[>]          :: [id=value]\n'
    with_doc = value_line + "    V  = 𝑢(m_d)                     :: [id=note, !doc]\n"
    text = text_of("cons_obs")
    assert text.count(value_line) == 1
    noted = elaborate_text(text.replace(value_line, with_doc), "cons_obs.bl")
    assert str(noted.builder["cntn", "dcsn"].signature()) == str(cons_obs.builder["cntn", "dcsn"].signature())


# a candidate statement with two candidates: one equation cannot determine two
# unknowns, and the refusal names both counts and the solve_{…} spelling
# (AMD-SG-017 §1)
TWO_CANDIDATES = """@stage: two

Xa := ℝ₊₊

β : (0,1)
γ : (1, inf)

𝑢(c : ℝ₊₊) := c^(1-γ)/(1-γ)
𝑑𝑢(c : ℝ₊₊) := c^(-γ)
Γ(m : ℝ₊₊) := (0, m]

[id=arvl_to_dcsn, (m : ℝ₊₊) : !arvl -> (m_d : ℝ₊₊) : !dcsn] {
    m_d = m
}

[id=dcsn_to_cntn, (m_d, c : ℝ₊₊ @ !ctrl, h : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m_d - c - h
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c, h) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + 𝑢(h) + β*V[>]
}

[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl, h : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(m_d)}(𝑢(c) + β*V[>])   :: [id=optimality, !doc]
    𝑑𝑢(c) + 𝑑𝑢(h) = β*D_{a}V[>]              :: [id=euler]
}
"""


def test_a_system_with_fewer_statements_than_unknowns_is_refused(elaborate_text):
    # the one equation of the block mentions the two outputs c and h and no
    # other statement defines either, so the system has one statement and two
    # unknowns and determines neither
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(TWO_CANDIDATES, "two.bl")
    error = refused.value
    assert (error.rule, error.address) == ("not-constructed", "policy.euler")
    assert "1 statements of builder 'policy' (policy.euler)" in error.message
    assert "a relation in 2 unknowns (c, h)" in error.message
    assert "`c, h = solve_{c, h}(…)`" in error.message


def test_the_reversed_order_of_the_expectations_is_refused_naming_the_undeclared_conditional(path_of):
    text = path_of("sa_savings").read_text(encoding="utf-8")
    reversed_order = text.replace("CE = E_{Ψ}(V[>]^(1-γ))^(1/(1-γ))", "CE = E_{ν}(V[>]^(1-γ))^(1/(1-γ))").replace(
        "AMB = E_{ν}(CE^(1-η))^(1/(1-η))", "AMB = E_{Ψ}(CE^(1-η))^(1/(1-η))")
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(reversed_order)
    error = refused.value
    assert (error.rule, error.address) == ("conditional-not-declared", "cntn_to_dcsn.risk_ce")
    assert "the expectation cntn_to_dcsn.risk_ce:Expectation:1 needs the distribution of ν given Ψ" in error.message


# --- the malformed clauses of the retired acceptance file of AMD-SG-035 -------
# Item 5 of AMD-SG-035 §9, moved here when lane C of the internal developer
# release 0.01 retired the file (BN1 of the release's decisions): a declared
# multiplier (spelling B, `cons_obs.bl`) written without its clause, with two
# bounds, at the arrival perch, without a mark, bounding the control or a
# decision state, declared twice, its bound written with the number first, or
# listed on the header of its block; and a clause of spelling A (the twin text
# `cons_kt` of `conftest.py`) whose chain descends, is strict or is mixed, or
# whose one bound is written with the number first, which the sign table
# would read with the reversed sign (E33, E37). Each case is the case's name,
# the twin it changes, the line or the header as changed, and the rule.
MULTIPLIER_LINE = "    μ[>]   : ℝ₊ ⟂ a >= 0"
MALFORMED_MULTIPLIERS = [
    ("the clause missing", "μ[>]   : ℝ₊", "syntax"),
    ("two bounds on a declaration", "μ[>]   : ℝ₊ ⟂ 0 <= a <= 1", "multiplier-declaration"),
    ("the arrival mark", "μ[<]   : ℝ₊ ⟂ a >= 0", "multiplier-declaration"),
    ("no mark", "μ      : ℝ₊ ⟂ a >= 0", "multiplier-declaration"),
    ("a bound naming the control", "μ[>]   : ℝ₊ ⟂ c >= 0", "multiplier-declaration"),
    ("a bound naming a decision state", "μ[>]   : ℝ₊ ⟂ m_d >= 0", "multiplier-declaration"),
    ("declared twice", "μ[>]   : ℝ₊ ⟂ a >= 0\n    μ[>]   : ℝ₊ ⟂ a >= 0", "multiplier-declaration"),
    ("a declaration's bound written with the number first", "μ[>]   : ℝ₊ ⟂ 0 <= a", "readable-form"),
]
MALFORMED_CHAINS = [("a descending chain", "1 >= a >= 0"), ("a strict chain", "0 < a <= 1"),
                    ("a mixed chain", "0 <= a >= 1"), ("a bound written with the number first", "0 <= a")]
LISTED_MULTIPLIER = ("inf) @ !vlu) : !cntn ->", "inf) @ !vlu, μ[>] : ℝ₊) : !cntn ->")
MALFORMED_CLAUSES = ([(name, "cons_obs", written, rule) for name, written, rule in MALFORMED_MULTIPLIERS]
                     + [("a header listing the multiplier", "header", LISTED_MULTIPLIER, "multiplier-declaration")]
                     + [(name, "cons_kt", written, "readable-form") for name, written in MALFORMED_CHAINS])


@pytest.mark.parametrize("case", MALFORMED_CLAUSES, ids=lambda case: case[0])
def test_a_malformed_declaration_of_a_multiplier_or_clause_of_a_line_is_refused_under_its_rule(case, cons_kt_text):
    _, twin, written, rule = case
    if twin == "cons_obs":
        assert cons_obs_text().count(MULTIPLIER_LINE) == 1
        text = cons_obs_text().replace(MULTIPLIER_LINE, "    " + written)
    elif twin == "header":
        assert cons_obs_text().count(written[0]) == 1
        text = cons_obs_text().replace(*written)
    else:
        assert cons_kt_text.count("⟂ a >= 0") == 1
        text = cons_kt_text.replace("⟂ a >= 0", "⟂ " + written)
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, twin + ".bl")
    assert refused.value.rule == rule


# a stage whose forward measures cannot be built: the law of its shock names a
# family the extension does not admit, so the graph is refused where the law is
# written
OPAQUE_LAW = """@stage: opaque_law
z : ℝ₊
z ~ Weird(0.2, 0.8)
[id=flow, (x:ℝ₊,z):!arvl -> (y:ℝ₊):!dcsn] { y=x+z }
[id=value, (W:ℝ @ !vlu):!dcsn -> (V:ℝ @ !vlu):!arvl] {
 V=E_{z}(W) :: [id=average]
}
"""


def test_a_forward_graph_the_construction_refused_names_its_file_its_position_and_its_rule(elaborate_text):
    """A refused graph says where, what happened, the address and the rule
    (AMD-SG-001 §2, kept). The behaviour file states that the refusal is
    raised; its file, line, column and rule stand here. The refusal is raised
    at the distribution record, whose address is the file position of its
    declaration (AMD-SG-017 §4), and its position is the item's own."""
    with pytest.raises(NotConstructed) as refused:
        graph_of(elaborate_text(OPAQUE_LAW), "builders", "forward")
    error = refused.value
    assert (error.stage, error.address, error.rule, error.line, error.column) == (
        "opaque_law", "t.bl:3", "not-constructed", 3, 1)
    assert str(error).startswith("t.bl:3:1-3:20: the forward measures are not constructed: the distribution of z "
                                 "is written with the family 'Weird'")
    assert str(error).endswith("(address 't.bl:3'; rule not-constructed)")


def test_methodize_replaces_a_second_binding_and_refuses_a_source_naming_another_stage_and_two_targets_at_one_box(
        cons, port):
    """A second `methodize` of a target replaces the method its first bound
    there, of the same kind, on the stage both are called on (specification
    0.6 decision 1 and R4, which retire the refusal of a second binding); and
    the two refusals of `methodize` the behaviour file does not read: it
    covers the unknown target, the positional address, the duplicate target and
    the malformed source. Each names the stage and the place, what happened,
    the rule and what to write."""
    from bellman.stage.binding_verbs import methodize
    stage = copy_native(cons)
    grid = {"grid": "!Cartesian", "orders": {"m_d": "n_m"}, "bounds": {"m_d": ["m_min", "m_max"]}}
    methodized = methodize(stage, {"stage": "cons", "methods": [
        {"on": "cntn_to_dcsn.value", "method": "!Linear", "settings": grid}]})
    assert methodize(methodized, {"stage": "cons", "methods": [
        {"on": "cntn_to_dcsn.value", "method": "!pchip", "settings": grid}]}) is stage
    assert str(stage.methods) == "cntn_to_dcsn:Evaluation   !pchip"
    with pytest.raises(ValueError) as refused:
        methodize(copy_native(cons), {"stage": "port", "methods": []})
    assert str(refused.value) == (
        "stage 'cons': the methods source names the stage 'port'; a methods file binds the stage it names "
        "(spec 0.3c §4.3); write `stage: cons` in the source or apply it to the stage 'port'")
    # the value and its stated derivative are two written addresses of one
    # Evaluation, which holds one representation (AMD-MB-002)
    with pytest.raises(ValueError) as refused:
        methodize(copy_native(port), {"stage": "port", "methods": [
            {"on": "cntn_to_dcsn.evaluate.value", "method": "!Linear", "handler": "h"},
            {"on": "cntn_to_dcsn.evaluate.marginal", "method": "!pchip", "handler": "h"}]})
    assert str(refused.value) == (
        "stage 'port', box 'cntn_to_dcsn:Evaluation': the targets 'cntn_to_dcsn.evaluate.value' and "
        "'cntn_to_dcsn.evaluate.marginal' conflict, both reaching it with a method; a box holds one method "
        "(AMD-SG-006 §4, rule 9); write one entry for that box")


# the names that would collide with the spelling of an identity (AMD-SG-016 §3),
# each as the stage text that writes it and the address the refusal names
COLLIDING_NAMES = {
    "a field named result": (
        "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (result : ℝ) : !dcsn] {\n    result = x\n}\n",
        "b", "the field 'result'"),
    "a block named merged": (
        "@stage: t\n[id=merged, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        "merged", "the block id 'merged'"),
    "a field named declared": (
        "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (declared : ℝ) : !dcsn] {\n    declared = x\n}\n",
        "b", "the field 'declared'"),
    "a statement named merged": (
        "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x :: [id=merged]\n}\n",
        "b.merged", "the statement id 'merged'"),
    "a stage name with a colon": (
        "@stage: t:u\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        "1", "the stage name 't:u'"),
    # the subjects of a distribution are spelled joined by '_', a separator a
    # shock name may contain, so two declarations that join alike would carry
    # one identity; the constructor cannot see the two, and this check can
    "two distribution declarations joining alike": (
        "@stage: t\na_b : ℝ\na : ℝ\nb : ℝ\na_b ~ N(0,1)\n(a, b) ~ N((0,0), ((1,0),(0,1)))\n"
        "[id=blk, (k : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = k\n}\n",
        "6", "spelled 'a_b' joined"),
}


@pytest.mark.parametrize("written", COLLIDING_NAMES)
def test_a_name_that_would_collide_with_the_spelling_of_an_identity_is_refused_where_it_is_written(
        written, elaborate_text):
    """AMD-SG-016 §3: an identity is built in one place and never parsed, and a
    name that would collide with its spelling is refused there, once, under
    `identity-collision` — a name containing the colon that separates the
    segments, and a name equal to one of the three words a reader tests for in
    the last segment, `result`, `declared` and `merged`."""
    source, address, named = COLLIDING_NAMES[written]
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(source)
    error = refused.value
    assert (error.rule, error.address) == ("identity-collision", address)
    assert named in error.message
    assert str(error).endswith(f"(address {address!r}; rule identity-collision)")


def test_the_two_collisions_the_delegated_review_names_that_do_not_collide_are_not_refused(elaborate_text):
    """The delegated review of AMD-SG-016 named three further collisions for
    this brief to verify (§3). A name containing a dot is refused by the
    grammar, which admits no dot in a block id, a statement id or a field name,
    so no identity is ever built from one. A shock name containing an underscore
    does not collide: the subjects of a distribution and of an extended measure
    are spelled joined by `_`, and nothing reads that join apart again, so the
    corpus's own `z_shock`, `ε_p` and `W_F` stay admitted. The third, a field
    named `declared`, does collide with the reserved word and is refused above.
    """
    from lark.exceptions import UnexpectedInput
    for dotted in ("@stage: t\n[id=a.b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
                   "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y.z : ℝ) : !dcsn] {\n    y.z = x\n}\n"):
        with pytest.raises((ValueError, UnexpectedInput)) as refused:
            elaborate_text(dotted)
        assert "Unexpected token" in str(refused.value) or "identity-collision" not in str(refused.value)
    stage = elaborate_text(
        "@stage: t\nz_1 : ℝ\nz_1 ~ N(0,1)\n"
        "[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (k_d : ℝ) : !dcsn] {\n    k_d = k\n}\n"
        "[id=dcsn_to_cntn, (k_d, z_1) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d + z_1\n}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = E_{z_1}(V[>])\n}\n"
        "[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n")
    assert "t:shck:z_1" in {str(identity) for identity in stage.fields()}


@pytest.mark.parametrize("selected, column, remedy", [
    ("v[keep][~]", 17, "v[~][keep]"),
    ("v[<][>]", 14, "v[>]"),
])
def test_a_perch_mark_after_a_selector_is_a_positioned_syntax_refusal(
        elaborate_text, selected, column, remedy):
    source = "@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {\n    w = " + selected + "\n}\n"
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(source, "selectors.bl")
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "selectors.bl", 4, column)
    assert "perch mark" in error.message and "first selector" in error.message
    assert "write" in error.parts.write and remedy in error.parts.write
    assert "\n" + " " * (column + 3) + "^" in error.message
    assert "VisitError" not in str(error) and "Error trying to process rule" not in str(error)


# the forms the grammar admits and the lowering reads no term from, each
# refused under `syntax` at its line and column, its sentence quoting the text
# as written and its advice saying what to write: the case, the text after the
# `@stage` line, the position, the words of the sentence and of the advice
LOWERING_REFUSALS = [
    ("a computed selector",
     "k : ℝ\n[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = (1, 2)[k + 1]\n}\n", (4, 9),
     ("`(1, 2)[k + 1]`", "selects by `k + 1`", "a position or a name"), "`(1, 2)[1]`"),
    ("a selection on the side of a header",
     "[id=b, (x[1] : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n", (2, 9),
     ("`x[1]`", "a selection from x", "by its name"), "`x[>]`"),
    ("a selection declared", "x[1] : ℝ\n", (2, 1), ("`x[1]`", "a selection from x"), "`x : …`"),
    ("a selection given a distribution", "x : ℝ\nx[1] ~ N(0, 1)\n", (3, 1),
     ("`x[1]`", "names its shocks by name"), "`x ~ …`"),
    ("a comprehension binder typed by a role word", "Γ(x : ℝ) := {c : !ctrl | c < x}\n", (2, 13),
     ("`{c : !ctrl | c < x}`", "typed by `!ctrl`", "one set"), "`{c : ℝ₊ | …}`"),
    ("a condition tail after no set", "γ : !shck, < 2\n", (2, 1), ("`γ < 2`", "declares no set"),
     "`γ : ℝ₊, < 2`"),
    ("two lines under one id",
     "[id=b, (x : ℝ) : !dcsn -> (y : ℝ, w : ℝ) : !dcsn] {\n    y = x :: [id=same]\n    w = x :: [id=same]\n}\n",
     (4, 5), ("'b.same'", "the first at t.bl:3:5"), "another id"),
]


# the faults the typing walk finds, each refused where it is found, at the
# line's position, under its rule: the case, the text after the `@stage` line,
# the rule, the line and the words of the sentence. The first two are audit
# M4's, which reached the modeller as a sentence matched by its words and as a
# plain ValueError.
_ONE_FUNCTION = ("𝑓(x : ℝ₊) := x + 1\n𝑔(x : ℝ × ℝ) := x[1]\nβ : ℝ₊₊\n"
                 "[id=b, (v : ℝ₊) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = LINE\n}\n")
_ONE_SHOCK = ("y : ℝ\ny ~ N(0, 1)\n[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (k_d : ℝ) : !dcsn] {\n    k_d = k\n}\n"
              "[id=dcsn_to_cntn, (k_d, y) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d + y\n}\n"
              "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n    V = LINE\n}\n"
              "[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n")
TYPING_REFUSALS = [
    ("a function used as a number", _ONE_FUNCTION.replace("LINE", "𝑓 + 1"), "well-typed", 6,
     ("`𝑓` is a function", "`𝑓 + 1` reads it as a number", "`𝑓(…)`")),
    ("a binder named twice", _ONE_SHOCK.replace("LINE", "E_{y, y}(V[>])"), "declared-once", 11,
     ("`E_{y, y}(V[>])` names y twice", "`E_{y}(…)`")),
    ("Inv of a number", _ONE_FUNCTION.replace("LINE", "Inv(β)"), "well-typed", 6,
     ("`Inv(β)` inverts a number", "one function")),
    ("a function of a pair applied to a number", _ONE_FUNCTION.replace("LINE", "𝑔(v)"), "well-typed", 6,
     ("argument 1 of the call to 𝑔 is a number", "a tuple of values")),
    ("the two sides of a line of two kinds", _ONE_FUNCTION.replace("LINE", "𝑓"), "well-typed", 6,
     ("the right side of `w = 𝑓` is a function", "the left side a number")),
    ("arithmetic on a label",
     "[id=b, (d : {keep, adjust}) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = d + 1\n}\n", "well-typed", 3,
     ("`d` is a label", "`d + 1` reads it as a number")),
]


@pytest.mark.parametrize("case", TYPING_REFUSALS, ids=lambda case: case[0])
def test_a_fault_the_typing_walk_finds_is_refused_where_it_is_found(case, elaborate_text):
    _, body, rule, line, words = case
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\n" + body)
    error = refused.value
    assert (error.rule, error.line, error.column) == (rule, line, 5), (error.rule, error.line)
    assert all(word in error.message for word in words), (words, error.message)
    assert "requires scalar operands" not in error.message and "task file" not in error.message


def test_a_written_zero_divisor_in_a_function_body_is_refused_at_the_definition(elaborate_text):
    # the example of `divisor-nonzero` divides in a line; a function body is
    # refused at the file position of its definition record (AMD-SG-017 §4)
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\n𝑓(x : ℝ₊) := x/0\n"
                       "[id=b, (v : ℝ₊) : !arvl -> (w : ℝ) : !dcsn] {\n    w = 𝑓(v)\n}\n")
    error = refused.value
    assert (error.rule, error.address, error.line, error.column) == ("divisor-nonzero", "t.bl:2", 2, 1)
    assert "`x/0` divides by zero" in error.message


@pytest.mark.parametrize("case", LOWERING_REFUSALS, ids=lambda case: case[0])
def test_a_form_the_lowering_reads_no_term_from_is_refused_where_it_is_written(case, elaborate_text):
    _, body, (line, column), words, write = case
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\n" + body)
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", line, column)
    assert all(word in error.parts.why for word in words), (words, error.parts.why)
    assert write in error.parts.write and "^" in error.parts.what
    for internal in ("@in", "Select(", "Sym(", "NotImplementedError"):
        assert internal not in str(error), internal


def test_calibration_refuses_a_parameter_value_making_utility_undefined(cons):
    with pytest.raises(ValueError) as refused:
        copy_native(cons).calibrate({"ρ": 1.0})
    assert all(word in str(refused.value) for word in ("ρ", "1.0", "1 - ρ = 0"))


# fourteen runs of `python -m bellman`, each a new process that imports the
# package, so the test is one of the sweeps
@pytest.mark.sweep
def test_command_refuses_malformed_sources_unreadable_paths_and_invalid_arguments(path_of, elaborate_text, tmp_path):
    import subprocess
    import sys

    from bellman.refusal_catalogue import text_of
    from conftest import ROOT

    command = [sys.executable, "-m", "bellman"]
    refused_path = tmp_path / "refused.bl"
    refused_text = text_of(EXAMPLES["syntax"])
    refused_path.write_text(refused_text, encoding="utf-8")
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(refused_text, origin=str(refused_path))
    for option in ([], ["--encoding"], ["--dossier"]):
        answer = subprocess.run(command + [str(refused_path)] + option, cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert answer.returncode == 1
        assert not answer.stderr
        assert answer.stdout == str(refused.value) + "\n"
        assert "rule syntax" in answer.stdout and "^" in answer.stdout
        assert "`)`" in answer.stdout and "`,`" in answer.stdout
    for unreadable in (tmp_path / "missing.bl", tmp_path):
        for option in ([], ["--encoding"], ["--dossier"]):
            answer = subprocess.run(command + [str(unreadable)] + option, cwd=ROOT,
                                    capture_output=True, text=True, encoding="utf-8", timeout=60)
            assert answer.returncode == 1 and not answer.stderr
            lines = answer.stdout.splitlines()
            assert [line.split()[0] for line in lines] == ["where", "what", "why", "write"]
            assert str(unreadable) in lines[0] and "readable .bl file" in lines[-1]
    path = path_of("cons").relative_to(ROOT)
    for arguments in ([], ["--encoding"], [str(path), "--unknown"],
                      [str(path), "--encoding", "--dossier"], [str(path), "--period", "period.yml"]):
        answer = subprocess.run(command + arguments, cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", timeout=60)
        assert answer.returncode == 2
        assert not answer.stdout
        assert answer.stderr.startswith("usage:")
