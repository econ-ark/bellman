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
import math

import pytest

from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import EXAMPLES, INVERSE_EULER
from bellman.stage import load_stage
from bellman.trellis import load_recipe
from bellman.refusal_catalogue import catalogue, entry, refusal_of
from bellman.refusals import (FACTORY_RULES, RULES, TARGET_RULES, ConstructionError, FactoryError,
                              NotConstructed, TargetError)
from bellman.stage.grains import graph_of
from conftest import (CORPUS, GRID_STAGE, GRID_VALUES, PERFECT_FORESIGHT_ORIGIN,
                      TWO_STATE_GRID_STAGE, branching, closed_form_check, cons_obs_text,
                      corpus_text, perfect_foresight_text, shock_branching, stage_from_text)

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
    address and the rule, then one line per related location and one for
    the action, where the refusal carries them."""
    if error.line is None:
        head = f"{error.file}: address {error.address!r}: {error.message} (rule {error.rule})"
    else:
        where = f"{error.file}:{error.line}:{error.column}"
        if error.end_line is not None:
            where += f"-{error.end_line}:{error.end_column}"
        if error.address is None:
            head = f"{where}: {error.message} (rule {error.rule})"
        else:
            head = f"{where}: {error.message} (address {error.address!r}; rule {error.rule})"
    after = "".join(f"\n  {location}" for location in error.related)
    if error.write:
        after += f"\n  write: {error.write}"
    return head + after


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
    if rule in ("declared-twice", "label-not-in-parent", "type-conflict", "metadata-mismatch"):
        # the earlier item of the pair is a related location under the role
        # `original declaration`, with its file, its range and its term
        # address, and the sentence still names its position in words
        (earlier,) = error.related
        assert earlier.role == "original declaration"
        assert earlier.file in ("t.bl", "m.bl") and earlier.address is not None
        assert None not in (earlier.line, earlier.column, earlier.end_line, earlier.end_column)
        assert f"{earlier.file}:{earlier.line}:{earlier.column}" in error.message
        assert (earlier.file, earlier.address) != (error.file, error.address)
    if rule == "syntax":
        from bellman.refusal_catalogue import text_of

        assert (error.file, error.line, error.column) == ("cons.bl", 16, 40)
        assert str(error).startswith("cons.bl:16:")
        assert text_of(example).splitlines()[15] in str(error)
        assert "\n" + " " * (4 + error.column - 1) + "^" in str(error)
        # the grammar's sentence for the place is the action, held once
        assert "a side of a block header" in error.write and error.write not in error.message
        with pytest.raises(ConstructionError) as refused:
            elaborate_text("@stage: t\n[id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n")
        word = refused.value
        assert (word.rule, word.line, word.column) == ("syntax", 2, 18)
        assert "!contrl" in word.message
        for refusal in (error, word):
            for internal in ("Error trying to process rule", "word_type", "TAGBANG"):
                assert internal not in str(refusal)
    if rule == "defined-once":
        assert (error.line, error.column) == (4, 5)
        held = entry(rule)
        assert held.where == "t.bl, line 4, column 5 (address 'b.second')"
        assert "W = 2*V[>]" in held.what and "^" in held.what
        assert held.why == error.message
        assert "t.bl:3:5 (term address 'b.first')" in held.why
        assert held.write == error.write
        assert all(word in held.write
                   for word in ("Remove one of the two definitions of W", "another name", "`!doc`"))
        assert held.corrected == ""
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
    from conftest import ROOT, ADJUSTER_CONS_EXPLICIT
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
    adjuster = (ROOT / ADJUSTER_CONS_EXPLICIT).read_text(encoding="utf-8")
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
    unsolved = elaborate_text(with_grid("a + 5*c[>]").replace(law, "    a = m*m - c\n"))
    assert ({item.condition for item in unsolved.obligations()}
            == {item.condition for item in elaborate_text(text).obligations()})


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
    trellis = tmp_path / "trellis.yml"
    trellis.write_text(f"periods:\n  - stages:\n      cons: {{stage: {path_of('cons')}, calibration: calibration.yml}}\n"
                       "    connectors: []\ninter_connectors: []\n", encoding="utf-8")
    methodized = copy_native(cons).methodize(cons_sources["methods"])
    for call, path, key, line in ((lambda: copy_native(cons).calibrate(calibration), calibration, "ρ", 3),
                                  (lambda: methodized.configure(settings), settings, "n_m", 7),
                                  (lambda: load_trellis(trellis), calibration, "ρ", 3)):
        with pytest.raises(FactoryError) as refused:
            call()
        assert (refused.value.rule, refused.value.file, refused.value.written, refused.value.write) == (
            "readable-file", str(path), f"{key!r} at line {line}", f"one `{key}:` entry")
        written_twice = f"in {path.name}, at line {line - 1} and again at line {line}"
        assert f"the key {key!r} is written twice {written_twice}" in refused.value.message
    registry = write_registry(tmp_path / "registry", {"calibration/main.yml": "calibration:\n  β: 0.96\n  β: 0.5\n"})
    with pytest.raises(FactoryError) as refused:
        load_recipe(registry, "spec.yml")
    assert (refused.value.rule, refused.value.write) == ("recipe-source", "one `β:` entry")


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


def test_a_method_word_at_a_place_its_row_does_not_admit_and_a_word_no_row_holds_are_refused(cons):
    """A method word typed at a place of a kind its row of the catalogue does
    not admit is refused under `method-admission`, naming the place, its kind
    and the kinds the row admits; a word no row holds is refused under
    `syntax`, naming the words of the catalogue (specification 0.7 §5)."""
    for entry, words in (
        ("policy.method : !gauss_hermite", ("`policy`", "kind builder", "admits operator E")),
        ("cntn_to_dcsn.value.method : !egm",
         ("`cntn_to_dcsn.value`", "kind statement", "admits builder, operator argmax")),
        ("cntn_to_dcsn.evaluate.method : !vfi",
         ("`cntn_to_dcsn.evaluate`", "kind operator evaluate", "admits builder")),
    ):
        with pytest.raises(ConstructionError) as refused:
            copy_native(cons).methodize({"text": f"@methods: cons\n{entry}\n", "origin": "cons.methods.bl"})
        assert (refused.value.rule, refused.value.stage) == ("method-admission", cons.name)
        assert all(word in str(refused.value) for word in words), str(refused.value)
    for word in ("unknown_method", "linear", "rootfind", "value_iteration"):
        with pytest.raises(ConstructionError) as refused:
            copy_native(cons).methodize(
                {"text": f"@methods: cons\npolicy.method : !{word}\n", "origin": "cons.methods.bl"})
        assert refused.value.rule == "syntax"
        assert f"`!{word}`, which no row of the catalogue holds" in str(refused.value)


def test_method_options_refuse_invalid_authored_or_configured_values(cons, port):
    """`configure` refuses a setting a component names and the source does
    not value (`setting-unvalued`); a keyword argument of a method word whose
    value at the settings has not the kind the catalogue's row names
    (`method-option-value`), for `!vfi` `n_c` a positive integer and `tol` a
    positive real, for `!gauss_hermite` a node count per shock a positive
    integer and for `!tauchen` `min_prob` a finite positive real; and a grid
    whose count, bounds or node set at the settings are out of order
    (`grid-bounds`). At binding, a factor on a coordinate the function at
    the place lacks is refused (`grid-coordinate`), and a keyword the row
    requires and the entry omits (`method-admission`)."""
    # each binding binds a stage of its own (specification 0.6 decision 1 and R4)
    methodized = copy_native(cons).methodize({
        "text": "@methods: cons\npoints : ℝ\ntolerance : [-inf, inf]\npolicy.method : !vfi(n_c=points, tol=tolerance)\n",
        "origin": "cons.methods.bl"})
    with pytest.raises(ConstructionError, match="points") as refused:
        methodized.configure({"settings": {"tolerance": 1e-6}})
    assert refused.value.rule == "setting-unvalued"
    for settings, message in (
        ({"points": -5, "tolerance": 1e-6}, "positive integer"),
        ({"points": 8, "tolerance": float("inf")}, "positive real"),
        ({"points": 8, "tolerance": -1.0}, "positive real"),
    ):
        with pytest.raises(ConstructionError, match=message) as refused:
            methodized.configure({"settings": settings})
        assert (refused.value.rule, refused.value.stage, refused.value.address) == (
            "method-option-value", "cons", "policy")
    configured = methodized.configure({"settings": {"points": 8, "tolerance": 1e-6}})
    assert configured.bindings.settings["points"] == 8
    assert "n_c = 8" in str(configured.builder.policy.denote())

    # the grid of the value's representation at the settings: a count below
    # two, bounds out of order or not finite, and a bound outside the
    # coordinate's declared set
    gridded = copy_native(cons).methodize({
        "text": ("@methods: cons\nn_m : ℤ\nm_min : ℝ\nm_max : ℝ\n"
                 "cntn_to_dcsn.evaluate.method : !Linear\n"
                 "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))\n"),
        "origin": "cons.methods.bl"})
    for settings, rule, message in (
        ({"n_m": -5, "m_min": 0.1, "m_max": 10.0}, "grid-bounds", "count -5"),
        ({"n_m": 8, "m_min": 10.0, "m_max": 1.0}, "grid-bounds", "in order"),
        ({"n_m": 8, "m_min": -1.0, "m_max": 10.0}, "grid-bounds", "declared set"),
        # a bound that is no number of the declared set is refused at the
        # declaration before the grid is read
        ({"n_m": 8, "m_min": float("nan"), "m_max": 10.0}, "setting-outside-set", "nan"),
        ({"n_m": 8, "m_min": 0.1, "m_max": float("inf")}, "setting-outside-set", "inf"),
    ):
        with pytest.raises(ConstructionError, match=message) as refused:
            gridded.configure({"settings": settings})
        assert (refused.value.rule, refused.value.stage) == (rule, "cons")
        if rule == "grid-bounds":
            assert refused.value.address == "cntn_to_dcsn.evaluate"
    # a factor on a coordinate the function at the place lacks is refused
    # where the entry is read
    with pytest.raises(ConstructionError, match="'m'.*no coordinate.*m_d") as refused:
        copy_native(cons).methodize({
            "text": ("@methods: cons\nn_m : ℕ\nm_min : ℝ₊\nm_max : ℝ₊\n"
                     "cntn_to_dcsn.evaluate.method : !Linear\n"
                     "cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_min, m_max, n_m))\n"),
            "origin": "cons.methods.bl"})
    assert refused.value.rule == "grid-coordinate"

    # the node counts of a quadrature, one per shock, each a positive integer
    # and every one of them written
    quadrature = copy_native(port).methodize({
        "text": "@methods: port\nnodes_Ψ : ℝ\nnodes_θ : ℝ\nE_Ψ_θ.method : !gauss_hermite(n_Ψ=nodes_Ψ, n_θ=nodes_θ)\n",
        "origin": "port.methods.bl"})
    for value, rule, message in (
        (0, "method-option-value", "n_Ψ.*positive integer"),
        ([7], "setting-outside-set", "nodes_Ψ"),
        (7.5, "method-option-value", "n_Ψ.*positive integer"),
        (True, "setting-outside-set", "nodes_Ψ"),
    ):
        with pytest.raises(ConstructionError, match=message) as refused:
            quadrature.configure({"settings": {"nodes_Ψ": value, "nodes_θ": 7}})
        assert refused.value.rule == rule
    with pytest.raises(ConstructionError, match="without the keyword n_θ") as refused:
        copy_native(port).methodize({
            "text": "@methods: port\nnodes_Ψ : ℝ\nE_Ψ_θ.method : !gauss_hermite(n_Ψ=nodes_Ψ)\n",
            "origin": "port.methods.bl"})
    assert refused.value.rule == "method-admission"
    positive_real = copy_native(port).methodize({
        "text": "@methods: port\nminimum_probability : [-inf, inf]\nE_Ψ_θ.method : !tauchen(min_prob=minimum_probability)\n",
        "origin": "port.methods.bl"})
    with pytest.raises(ConstructionError, match="finite value"):
        positive_real.configure({"settings": {"minimum_probability": float("inf")}})


def test_every_rule_of_the_three_vocabularies_has_an_example_in_the_catalogue(catalogue_entries):
    """A rule with no example is a gap in the catalogue and fails here
    (AMD-SG-022 §2). Each entry names its rule, the place the refusal is
    raised and the refusal as printed."""
    without = [item.rule for item in catalogue_entries if not item.refusal]
    for item in catalogue_entries:
        if item.rule in FACTORY_RULES:
            assert all((item.where, item.what, item.why, item.write)), item.rule
    assert without == [], without
    assert [item.rule for item in catalogue_entries] == list(RULES) + list(TARGET_RULES) + list(FACTORY_RULES)


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
    for word in ("p_zero, q", "the Mixture declaration `y ~ Mixture(", "sum to 0.8", "not to one"):
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
    for word in ("the Mixture declaration `y ~ Mixture(", "1.5", "not a probability"):
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
        for word in ("the DiscreteMarkov declaration `z ~ DiscreteMarkov(", counted,
                     "`DiscreteMarkov` takes 2 or 3 arguments",
                     "the transition probabilities", "the chain's states", "the previous state"):
            assert word in refused.value.message, (declaration, word, refused.value.message)
    for admitted in ("z ~ DiscreteMarkov(Π, (z_lo, z_hi))", "z ~ DiscreteMarkov(Π, (z_lo, z_hi), x)"):
        elaborate_text(CHAIN_STAGE.replace("DECLARATION", admitted))


# the refusals of a derived parameter (AMD-MT-003, build contract §5), each the
# definition of h in the perfect-foresight stage of the derived checks as
# changed, the calibration that provokes it or None for a refusal at
# elaboration, and the words its message names; the catalogue's example holds
# the call of a function other than log and exp
DERIVED_REFUSALS = [
    ("a field", "h := 1/(1 - Γ/m)", None, ("the derived parameter h", "reads m, a field")),
    ("a set", "h := 1/(1 - Γ/R) + Xm", None, ("reads Xm, a set of the stage",)),
    ("a function", "h := 1 + 𝑢", None, ("reads 𝑢, a function of the stage",)),
    ("infinity", "h := 1/(1 - Γ/R) + inf", None, ("reads inf, which is no finite number",)),
    ("a number beyond the floating-point range", "h := 1/(1 - Γ/R) + 1" + "0" * 400, None,
     ("writes a number that exceeds the largest finite floating-point number",)),
    ("a decimal number beyond the floating-point range", "h := 1/(1 - Γ/R) + 1e400", None,
     ("writes a number that exceeds the largest finite floating-point number",
      "has no finite real value")),
    ("log of two arguments", "h := log(R, Γ)", None, ("calls log with 2 arguments",)),
    ("a tuple", "h := 1 + (R, Γ)", None, ("writes `(R, Γ)`, a form no derived parameter",)),
    ("a value for h", "h := 1/(1 - Γ/R)", {"h": 52.0},
     ("the calibration source supplies the value 52.0 for h", "`1/(1 - Γ/R)`")),
    ("a division by zero", "h := 1/(1 - Γ/R)", {"Γ": 1.04},
     ("the divisor `1 - Γ/R` is 0.0 at Γ = 1.04, R = 1.04", "a division by zero has no value")),
    ("a nonpositive logarithm", "h := log(1 - Γ/R)", {"Γ": 1.06},
     ("the argument `1 - Γ/R` of log is", "log is defined at positive numbers alone")),
    ("a noninteger power of a negative base", "h := (1 - Γ/R)^(1/2)", {"Γ": 1.06},
     ("which is no integer", "a noninteger exponent requires a positive base")),
    ("an undefined power of zero", "h := (1 - Γ/R)^(-1)", {"Γ": 1.04},
     ("has the base 0.0 and the exponent -1.0", "defined for a positive exponent alone")),
    ("a value beyond the floating-point range", "h := exp(1000*ρ)", {},
     ("`exp(1000*ρ)` at ρ = 2.0 exceeds the largest finite floating-point number",)),
    ("a positive argument lost to underflow", "h := log(exp(-1000*ρ))", {},
     ("is 0.0 by floating-point underflow", "which numeric underflow does not supply")),
]


@pytest.mark.parametrize("case", DERIVED_REFUSALS, ids=lambda case: case[0])
def test_a_derived_parameter_is_refused_at_its_definition(case, derived_parameters):
    """A derived parameter's definition that reads a name other than a
    declared parameter or a derived parameter, that calls a function other
    than log or exp of one argument or that writes another form is refused
    under `derived-parameter` where it is written, before any line is read;
    a calibration that supplies a value for it, or at which its arithmetic has
    no finite real value, is refused under the same rule at its definition's
    file position, naming the operation and the numbers it reads."""
    _, definition, values, words = case
    with pytest.raises(ConstructionError) as refused:
        stage = derived_parameters.stage(("h := 1/(1 - Γ/R)", definition))
        if values is not None:
            stage.calibrate({"calibration": {**derived_parameters.calibration, **values}})
    error = refused.value
    line = next(n for n, text in enumerate(derived_parameters.text.split("\n"), 1)
                if text.startswith("h :="))
    if values is None:
        assert (error.rule, error.file, error.line) == (
            "derived-parameter", derived_parameters.origin, line
        )
    else:
        assert (error.rule, error.address) == (
            "derived-parameter", f"{derived_parameters.origin}:{line}"
        )
    for word in words:
        assert word in error.message, (word, error.message)
    assert error.write


def test_a_derived_parameter_that_reads_a_setting_is_refused_in_its_methods_file(
        derived_parameters):
    """A setting takes its value at configuration, after the calibration that
    evaluates a derived parameter, so a definition that reads one is refused
    under `derived-parameter` in the methods file that writes it."""
    addition = {"text": "@methods: perfect_foresight\nn_a : ℕ\nκ := n_a/2\n", "origin": "m.bl"}
    with pytest.raises(ConstructionError) as refused:
        derived_parameters.stage().methodize(addition)
    error = refused.value
    assert (error.rule, error.file, error.line) == ("derived-parameter", "m.bl", 3)
    assert "reads n_a, a setting" in error.message


def test_two_lines_merged_into_one_box_bind_one_method(elaborate_text):
    """A merged box is one operator, so it holds one method (AMD-SG-011 §3);
    the author keeps two methods by keeping the two computations apart with
    `!node`. The two lines are the arrival builder's two value lines, which
    integrate the same pair of shocks, the second also as an iterated
    expectation, so that the stage-wide places `E_y_z`, `E_y` and `E_z` reach
    the one merged box; under AMD-MB-001 a derivative line forms no box, so
    the stage carries a second value `W` (MB-T215)."""
    from bellman.stage.binding_verbs import methodize
    from conftest import bundles
    text = bundles(backward="    V[<] = E_{y,z}(V)                     :: [id=value]\n"
                            "    W[<] = E_{y,z}(R*W) + E_{y}(E_{z}(W)) :: [id=second]\n",
                   decision="    V = c + β*V[>]                  :: [id=value]\n"
                            "    W = c + β*W[>]                  :: [id=second]\n")
    for old, new in (("(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
                      "(V[>] : ℝ @ !vlu, W[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu, W : ℝ @ !vlu) : !dcsn]"),
                     ("[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl]",
                      "[id=dcsn_to_arvl, (V, W) : !dcsn -> (V[<] : ℝ @ !vlu, W[<] : ℝ @ !vlu) : !arvl]")):
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    stage = elaborate_text(text, "bundles.bl")
    entries = ("dcsn_to_arvl.value.E_y_z.method : !quadrature\n",
               "dcsn_to_arvl.second.E_y_z.method : !exact\n")
    with pytest.raises(ConstructionError) as refused:
        methodize(stage, {"text": "@methods: bundles\n" + "".join(entries), "origin": "bundles.methods.bl"})
    assert refused.value.rule == "component-typed-twice"
    assert "which both reach the operator `E` of block 'dcsn_to_arvl'" in str(refused.value)
    assert "dcsn_to_arvl.value.E_y_z.method : !quadrature" in str(refused.value)
    assert "dcsn_to_arvl.second.E_y_z.method : !exact" in str(refused.value)
    # an occurrence of the maximization in a named line reaches the box the
    # line's row is, which the sentence names by the line's block
    with pytest.raises(ConstructionError) as refused:
        methodize(stage, {"text": "@methods: bundles\npolicy.argmax.method : !max\n"
                                  "policy.objective.argmax.method : !golden_section(n_sections=5)\n",
                          "origin": "bundles.methods.bl"})
    assert "which both reach the operator `argmax` of block 'policy';" in str(refused.value)
    # two stage-wide places of different names reach the one merged box, and
    # neither stands in a block, so the sentence reads the block from the
    # place of the block that holds the box
    with pytest.raises(ConstructionError) as refused:
        methodize(stage, {"text": "@methods: bundles\nE_y_z.method : !quadrature\n"
                                  "E_y.method : !exact\n",
                          "origin": "bundles.methods.bl"})
    assert refused.value.rule == "component-typed-twice"
    assert ("at `E_y_z` and at `E_y`, which both reach the operator `E` of block "
            "'dcsn_to_arvl';") in str(refused.value)
    # the head of the block names every occurrence in it, and the merged box
    # answers with the one component
    bound = methodize(stage, {"text": "@methods: bundles\ndcsn_to_arvl.E_y_z.method : !quadrature\n",
                              "origin": "bundles.methods.bl"})
    merged = bound.builder.bwd.primitives["dcsn_to_arvl:Expectation"]
    assert {place: str(held) for place, held in merged.methods.items()} == {"dcsn_to_arvl.E_y_z": "!quadrature"}
    assert str(merged.signature()).splitlines()[-1] == "method     !quadrature"


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
    assert "1 statement of builder 'policy' (policy.euler) states" in error.message
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
    assert "the expectation over ν on line cntn_to_dcsn.risk_ce needs the distribution of ν given Ψ" in error.message


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
        assert cons_kt_text.count("⟂ m_d - c >= 0") == 1
        text = cons_kt_text.replace("⟂ m_d - c >= 0", "⟂ " + written)
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

    def addition(method):
        return {"text": (f"@methods: cons\ncntn_to_dcsn.evaluate.method : {method}\n"
                         "n_m : ℕ\nm_min : ℝ₊\nm_max : ℝ₊\n"
                         "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))\n"),
                "origin": "cons.methods.bl"}
    methodized = methodize(stage, addition("!Linear"))
    assert methodize(methodized, addition("!pchip")) is stage
    assert str(stage.methods) == "cntn_to_dcsn.evaluate   !pchip   !Cartesian(m_d=(m_min, m_max, n_m))"
    with pytest.raises(ConstructionError) as refused:
        methodize(copy_native(cons), {"text": "@methods: port\n", "origin": "port.methods.bl"})
    assert refused.value.rule == "metadata-mismatch"
    assert str(refused.value).startswith("port.methods.bl:1:1")
    assert ("the addition names the stage 'port', and the stage file names itself 'cons'"
            in str(refused.value))
    assert "an addition's first line is `@methods: <stage>`" in str(refused.value)
    # the whole of an Evaluation and one of the objects it stores share a
    # key, so one component typed at both is typed twice (D4); the two
    # objects, the value and its stated derivative, are represented apart
    with pytest.raises(ConstructionError) as refused:
        methodize(copy_native(port), {
            "text": ("@methods: port\ncntn_to_dcsn.evaluate.method : !Linear\n"
                     "cntn_to_dcsn.evaluate[V].method : !pchip\n"),
            "origin": "port.methods.bl"})
    assert refused.value.rule == "component-typed-twice"
    assert "the object `V` stored at the operator `evaluate` of block 'cntn_to_dcsn'" in str(refused.value)
    apart = methodize(copy_native(port), {
        "text": ("@methods: port\ncntn_to_dcsn.evaluate[V].method : !Linear\n"
                 "cntn_to_dcsn.evaluate[D_{k_d}V].method : !pchip\n"),
        "origin": "port.methods.bl"})
    assert {place: str(held) for place, held in apart.methods.items()} == {
        "cntn_to_dcsn.evaluate[V]": "!Linear", "cntn_to_dcsn.evaluate[D_{k_d}V]": "!pchip"}


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
    assert "write" in error.write and remedy in error.write
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
    ("a bound written after a comma", "γ : ℝ₊, < 2\n", (2, 1),
     ("`γ < 2`", "after a comma", "retired"), "`ℝ₊ @ (-inf, 2)`"),
    ("two sets of one type that are no intervals", "γ : ℝ₊ @ ℤ\n", (2, 1),
     ("`ℝ₊`", "`ℤ`", "are no intervals"), "`γ : ℝ₊ @ (0, 1)`"),
    ("a set of labels with an interval", "γ : {a, b} @ (0, 1)\n", (2, 1),
     ("`{a, b}`", "a set of labels"), "the one set γ takes its values in"),
    ("a bound after a comma on two names", "(γ, δ) : ℝ₊ × ℝ₊, < 2\n", (2, 1),
     ("`< 2`", "after a comma", "retired"), "`γ : ℝ₊ @ (-inf, 2)`"),
    ("several sets on a declaration of two names", "(γ, δ) : ℝ₊ × ℝ₊ @ (0, 1)\n", (2, 1),
     ("of (γ, δ) carries", "one declared name"), "each name on its own line"),
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
    assert write in error.write and "^" in error.parts.what
    for internal in ("@in", "Select(", "Sym(", "NotImplementedError"):
        assert internal not in str(error), internal


def test_calibration_refuses_a_parameter_value_making_utility_undefined(cons):
    with pytest.raises(ValueError) as refused:
        copy_native(cons).calibrate({"ρ": 1.0})
    assert all(word in str(refused.value) for word in ("ρ", "1.0", "1 - ρ = 0"))


def test_calibration_decides_a_line_condition_at_the_value_of_a_derived_parameter(
        derived_parameters):
    """A parameter-only condition of a line that reads a derived parameter is
    decided at the value the derived parameter's definition takes, as one that
    reads a declared parameter is decided at its value (AMD-SG-022 §4;
    AMD-MT-003, build contract §5): with `z := R - 1.04`, the divisor of
    `m = k/z + 1` is refused where R = 1.04 makes z zero and established
    where R = 1.05 does not."""
    changes = (("R_n := R/Γ", "R_n := R/Γ\nz := R - 1.04"), ("m = R_n*k + 1", "m = k/z + 1"))
    with pytest.raises(ValueError) as refused:
        derived_parameters.stage(*changes).calibrate(
            {"calibration": {**derived_parameters.calibration, "R": 1.04}})
    assert all(word in str(refused.value) for word in ("z = 0.0", "¬(z = 0)", "false"))
    stage = derived_parameters.stage(*changes)
    stage.calibrate({"calibration": {**derived_parameters.calibration, "R": 1.05}})
    condition, = [item for item in stage.obligations()
                  if item.condition == "arithmetic-definedness"
                  and item.entries[0].block == "arvl_to_dcsn"]
    assert condition.status == "established"
    assert condition.evidence[0].startswith("calibration z = 0.01")


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


def test_method_keyword_names_must_be_declared_even_inside_nested_values(cons):
    """Method arguments read declared names; quoted strings remain literal."""
    for value in ("missing", "(2, !foo(inner=missing))"):
        addition = {"text": "@methods: cons\n"
                    f"policy.evaluate.method : !Linear(option={value})\n",
                    "origin": "keywords.methods.bl"}
        with pytest.raises(ConstructionError) as caught:
            copy_native(cons).methodize(addition)
        error = caught.value
        assert error.rule == "name-in-scope"
        assert error.file == "keywords.methods.bl" and error.line == 2
        assert error.address == "policy.evaluate"
        assert error.column is not None and error.write
        assert "missing" in error.message
    allowed = copy_native(cons).methodize({
        "text": '@methods: cons\npolicy.evaluate.method : !Linear(option="literal", count=2)\n',
        "origin": "keywords.methods.bl",
    })
    assert "policy.evaluate" in allowed.methods


# The grids a record of their constructors does not admit (AMD-MT-003 build
# contract §2): each case is its name, the stage text, the typing entries and
# the declarations of the methods file, the settings configured, the rule, the
# address and the file the refusal names, and the words its message holds. A
# stage that binds is configured, so that a refusal of the configured values
# is reached; an entry of a builder methodized by `!egm` stands in the stage
# text once the addition is unioned with it.
_FIBRED = "!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))"
_EGM_GRID = (
    INVERSE_EULER.replace("@stage: t\n", "@stage: grids\nA := {1, 2}\nΓ_c(x : ℝ₊) := [0, x]\n")
)
GRID_REFUSALS = [
    ("fibred at the grid of egm", _EGM_GRID,
     "policy.method : !egm\n"
     "policy.grid : !Fibred(base=!Points(nodes=A), fibre=!Cartesian(c=(Γ_c, n_c)))\n",
     "", {}, "grid-coordinate", ("policy", "grids.bl"),
     ("on the states of the continuation perch",
      "a place of any other coordinate domain refuses")),
    ("fibred at a function of states alone", GRID_STAGE,
     f"cntn_to_dcsn.evaluate.method : !Linear\ncntn_to_dcsn.evaluate.grid : {_FIBRED}\n",
     "", {}, "grid-coordinate", ("cntn_to_dcsn.evaluate", "methods.bl"),
     ("reads a grid on (m)", "constructs pairs on (m, c)")),
    ("a base of feasible factors", GRID_STAGE,
     "cntn_to_dcsn.method : !vfi\n"
     "cntn_to_dcsn.grid : !Fibred(base=!Cartesian(c=(Γ_c, n_c)), "
     "fibre=!Cartesian(c=(Γ_c, n_c)))\n",
     "", {}, "grid-coordinate", ("cntn_to_dcsn", "methods.bl"),
     ("the base of !Fibred is !Points or a !Cartesian term without feasible-control factors",)),
    ("a fibre of points", GRID_STAGE,
     "cntn_to_dcsn.method : !vfi\n"
     "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), fibre=!Points(nodes=B))\n",
     "", {}, "grid-coordinate", ("cntn_to_dcsn", "methods.bl"),
     ("the fibre of !Fibred is a !Cartesian term whose factors are feasible-control factors",)),
    ("a contradictory requirement", GRID_STAGE,
     "cntn_to_dcsn.method : !vfi\n"
     "cntn_to_dcsn.grid : !Points(nodes=B, require=(!Cartesian, !NonCartesian))\n",
     "", {}, "grid-requirement", ("cntn_to_dcsn", "methods.bl"),
     ("!Cartesian and !NonCartesian", "contradict each other")),
    ("points no file declares", GRID_STAGE,
     "cntn_to_dcsn.method : !vfi\ncntn_to_dcsn.grid : !Points(nodes=Z)\n",
     "", {}, "grid-setting-declared", ("cntn_to_dcsn", "methods.bl"),
     ("'Z' as its points", "no setting a methods file declares and no set the stage defines")),
    ("points of one coordinate on two", TWO_STATE_GRID_STAGE,
     "cntn_to_dcsn.evaluate.method : !Linear\ncntn_to_dcsn.evaluate.grid : !Points(nodes=P)\n",
     "P : ℝ × ℝ × ℝ\n", {}, "grid-coordinate", ("cntn_to_dcsn.evaluate", "methods.bl"),
     ("whose points have 1 coordinate each", "the coordinates (m, z)", "`X2 := ℝ × ℝ`")),
    ("a configured point outside the declared set", GRID_STAGE,
     "cntn_to_dcsn.method : !vfi\ncntn_to_dcsn.grid : !Points(nodes=Q)\n",
     "Q : ℝ × ℝ\n", {"Q": [-1.0, 1.0]}, "grid-bounds", ("cntn_to_dcsn", "grids.bl"),
     ("the point (-1.0,)", "lies outside the declared set Xm")),
    ("an outer requirement the joint grid does not satisfy", GRID_STAGE,
     f"cntn_to_dcsn.method : !vfi\ncntn_to_dcsn.grid : {_FIBRED[:-1]}, require=!Cartesian)\n",
     "", {}, "grid-requirement", ("cntn_to_dcsn", "methods.bl"),
     ("does not satisfy !Cartesian", "{1, 2} × {0, 1, 2}, holds (1, 2)")),
    ("an inner requirement a fibre does not satisfy", GRID_STAGE,
     "cntn_to_dcsn.method : !vfi\ncntn_to_dcsn.grid : "
     "!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c), require=!NonCartesian))\n",
     "", {}, "grid-requirement", ("cntn_to_dcsn", "methods.bl"),
     ("its fibre at the base state m = 1 does not satisfy !NonCartesian",)),
]


@pytest.mark.parametrize("case", GRID_REFUSALS, ids=lambda case: case[0])
def test_a_grid_the_record_of_its_constructor_does_not_admit_is_refused_under_its_rule(
        case, grid_stage):
    _, text, entries, declarations, settings, rule, (address, file), words = case
    with pytest.raises(ConstructionError) as refused:
        grid_stage(entries, declarations, text=text).configure({**GRID_VALUES, **settings})
    error = refused.value
    assert (error.rule, error.address, error.file) == (rule, address, file), str(error)
    assert all(word in error.message for word in words), (words, error.message)


# the perfect-foresight stage whose arrival block, a forward builder, defines
# cash on hand by an authored table on a `!node` line; a forward builder closes
# with no Evaluation and its law of motion is not split at a forward node, so
# the node's Evaluation has no row of its own, and a grid there discretizes the
# states of the builder's output perch, (m), while the table is evaluated at k
FORWARD_NODE = perfect_foresight_text(
    ("@stage: perfect_foresight\n", "@stage: forward_node\n"),
    ('Γ : ℝ₊₊          :: ["permanent income growth factor"]\n',
     'Γ : ℝ₊₊          :: ["permanent income growth factor"]\nK : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\n'),
    ("    m = R_n*k + 1                   :: [id=market_resources]\n",
     "    m = evaluate(K, Y, k)           :: [id=market_resources, !node]\n"),
)

# the refusals of a representation whose place supplies no data its family
# accepts, of a grid where the family reads none, of a grid beside an authored
# table that discretizes another coordinate domain than the table's, and of an
# expression the kernel compiler writes into no function (AMD-MT-003 build
# contract §3): each case is the addition's entries, the rule, the address the
# refusal names and words its message holds
REPRESENTATION_REFUSALS = (
    # the closed form refuses a representation grid
    ("perfect_foresight", "n : ℕ\nlo : Xm\nhi : Xm\n[id=policy, policy.method : !explicit "
     "| policy.evaluate.method : !closed_form "
     "| policy.evaluate.grid : !Cartesian(m=(lo, hi, n))] {\n"
     "    c = (1 - (R*β)^(1/ρ)/R)*(m - 1 + 1/(1 - Γ/R))    :: [id=consumption]\n}\n",
     "grid-coordinate", "policy.evaluate",
     ("!closed_form reads no grid", "remove the grid entry")),
    # the closed form at the Evaluation of an !egm builder, which supplies
    # pairs
    ("cons_savings_iid", "n_a : ℕ\na_min : ℝ₊\na_max : ℝ₊\n[id=policy, method : !egm "
     "| policy.grid : !Cartesian(a=(a_min, a_max, n_a)) | evaluate.method : !closed_form] {\n"
     "    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]\n"
     "    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]\n"
     "    c[~] = c[>]                     :: [id=cons_choice]\n}\n",
     "representation-source", "policy.evaluate", ("!egm selects policy pairs", "accepts neither")),
    # a family that reads the pairs of !egm, written with a grid there
    ("cons_savings_iid", "n_a : ℕ\na_min : ℝ₊\na_max : ℝ₊\nn_w : ℕ\nw_min : ℝ₊\nw_max : ℝ₊\n"
     "[id=policy, method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a)) "
     "| evaluate.method : !Linear | evaluate.grid : !Cartesian(w=(w_min, w_max, n_w))] {\n"
     "    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]\n"
     "    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]\n"
     "    c[~] = c[>]                     :: [id=cons_choice]\n}\n",
     "grid-coordinate", "policy.evaluate", ("reads the policy pairs", "the grid of !egm")),
    # the closed form at a declared function whose expression is a derivative
    ("cons_savings_iid", "𝑑𝑢.method : !closed_form\n", "representation-source", "𝑑𝑢",
     ("complete authored expression", "supplies none")),
    # a grid beside an authored table evaluated at an expression of the place's
    # coordinate, whose knots are points of that expression and not of the
    # coordinate the grid discretizes, a !Cartesian grid and a !Points grid
    ("perfect_foresight", "K : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\nKN : ℝ × ℝ × ℝ\n[id=dcsn_to_arvl] {\n"
     "    W = evaluate(K, Y, R*k/Γ + 1)    :: [id=table]\n}\n"
     "dcsn_to_arvl.table.evaluate.method : !Linear\n"
     "dcsn_to_arvl.table.evaluate.grid : !Cartesian(k=KN)\n",
     "representation-source", "dcsn_to_arvl.table.evaluate",
     ("is evaluated at `R*k/Γ + 1`", "!Cartesian(k=KN) discretizes (k)")),
    ("perfect_foresight", "K : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\nP : ℝ × ℝ × ℝ\n[id=dcsn_to_arvl] {\n"
     "    W = evaluate(K, Y, R*k/Γ + 1)    :: [id=table]\n}\n"
     "dcsn_to_arvl.table.evaluate.method : !Linear\n"
     "dcsn_to_arvl.table.evaluate.grid : !Points(nodes=P)\n",
     "representation-source", "dcsn_to_arvl.table.evaluate",
     ("is evaluated at `R*k/Γ + 1`", "!Points(nodes=P) discretizes (k)")),
    # a table on two coordinates written at them in another order than the
    # grid's, whose knots are points in that other order
    ("grids", "MN : ℝ × ℝ\nZN : ℝ × ℝ\nK2 : X2 × X2 × X2 × X2\nY2 : ℝ × ℝ × ℝ × ℝ\n"
     "[id=cntn_to_dcsn] {\n    W = evaluate(K2, Y2, (z, m))    :: [id=table]\n}\n"
     "cntn_to_dcsn.table.evaluate.method : !Linear\n"
     "cntn_to_dcsn.table.evaluate.grid : !Cartesian(m=MN, z=ZN)\n",
     "representation-source", "cntn_to_dcsn.table.evaluate",
     ("is evaluated at `(z, m)`", "discretizes (m, z)", "in the order of the grid's coordinates")),
    # the closed form at a declared function whose body calls a function no
    # definition declares, which the kernel compiler writes into no function
    ("perfect_foresight", "𝑓(x : ℝ₊₊) := log(x)    :: [id=f]\n𝑓.method : !closed_form\n",
     "representation-source", "𝑓",
     ("the declared function '𝑓'", "the call `log(x)` names a function no definition")),
    # the closed form at a declared function whose body calls a correspondence
    # the stage declares, whose definition is a set and no closed form
    ("perfect_foresight", "𝑓(x : Xm) := Γ_c(x)    :: [id=f]\n𝑓.method : !closed_form\n",
     "representation-source", "𝑓",
     ("the call `Γ_c(x)` names Γ_c", "whose definition is no expression in closed form")),
    # the closed form typed at a node's line with a grid typed at the node's
    # Evaluation, the two entries one assignment to the node's function
    ("perfect_foresight", "n : ℕ\nlo : Xm\nhi : Xm\n[id=cntn_to_dcsn] {\n"
     "    W = β*V[>]    :: [id=discounted, !node]\n}\n"
     "cntn_to_dcsn.discounted.method : !closed_form\n"
     "cntn_to_dcsn.discounted.evaluate.grid : !Cartesian(m=(lo, hi, n))\n",
     "grid-coordinate", "cntn_to_dcsn.discounted.evaluate", ("!closed_form reads no grid",)),
    # a grid beside the table of a forward node, which has no Evaluation of its
    # own: the grid discretizes the states of the output perch, (m)
    ("forward_node", "P : ℝ × ℝ × ℝ\narvl_to_dcsn.market_resources.evaluate.method : !Linear\n"
     "arvl_to_dcsn.market_resources.evaluate.grid : !Points(nodes=P)\n",
     "representation-source", "arvl_to_dcsn.market_resources.evaluate",
     ("is evaluated at `k`", "!Points(nodes=P) discretizes (m)")),
)


@pytest.mark.parametrize("case", REPRESENTATION_REFUSALS, ids=lambda case: f"{case[2]}:{case[3]}")
def test_a_representation_whose_place_supplies_no_data_its_family_accepts_is_refused(
        case, cons_savings_iid, perfect_foresight):
    """A representation is refused where its family does not accept the data
    its place supplies or the compiler writes no function of its expression,
    and a grid is refused where the family reads none, the grid at a node's
    Evaluation read with the representation typed at the node's line, or
    where it stands beside an authored table on another coordinate domain or
    on its coordinates in another order, each refusal positioned at the
    entry in the addition."""
    name, entries, rule, address, words = case
    texts = {"grids": (TWO_STATE_GRID_STAGE, "grids.bl"),
             "forward_node": (FORWARD_NODE, PERFECT_FORESIGHT_ORIGIN)}
    stage = (
        stage_from_text(*texts[name])
        if name in texts
        else {"cons_savings_iid": cons_savings_iid, "perfect_foresight": perfect_foresight}[name]
    )
    with pytest.raises(ConstructionError) as refused:
        copy_native(stage).methodize(
            {"text": f"@methods: {name}\n{entries}", "origin": "entries.bl"}
        )
    error = refused.value
    assert (error.rule, error.address, error.file) == (rule, address, "entries.bl")
    assert error.line is not None and error.write
    for word in words:
        assert word in error.message, (word, error.message)


# the refusals of an explicit solution (AMD-MT-003 build contract §5): the
# lines appended to a builder of the perfect-foresight stage under a method
# word, or an entry alone, with the rule, the address, the words of the
# refusal and the line of the addition at which it stands, the line at fault
# or, where no line is at fault, the typing entry on the second line; None
# where the refusal is checked where the version is bound
_SOLVING = "!egm or !time_iteration, whose block reads the continuation value"
EXPLICIT_REFUSALS = (
    ("policy.method : !explicit\n", "explicit-solution", "policy",
     ("no addition appends a line to the block", "`[id=policy, policy.method : !explicit]`"), 2),
    ("arvl_to_dcsn.method : !explicit\n", "explicit-solution", "arvl_to_dcsn",
     ("is a forward builder", "policy builder or on a backward value builder"), 2),
    ("[id=policy, policy.method : !explicit] {\n    c^(-ρ) = β*R*D_{a}V[>]    :: [id=euler]\n}\n",
     "explicit-solution", "policy", ("`policy.euler`", "states a relation", _SOLVING), 3),
    ("[id=policy, policy.method : !explicit] {\n"
     "    c = (β*D_{a}V[>])^(-1/ρ)    :: [id=inverse]\n}\n",
     "explicit-solution", "policy", ("reads V[>], a value input", _SOLVING), 3),
    ("[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit] {\n    V = 𝑢(c)/(1-β)\n}\n",
     "explicit-solution", "cntn_to_dcsn", ("reads c, a control input", _SOLVING), 3),
    ("[id=policy, policy.method : !explicit] {\n    κ = 1 - (R*β)^(1/ρ)/R    :: [id=mpc]\n"
     "    c = argmax_{cp : Γ_c(m)}(κ*𝑢(cp))    :: [id=chosen]\n}\n",
     "explicit-solution", "policy",
     ("`policy.chosen`", "applies argmax, an operator", _SOLVING), 4),
    ("[id=policy, policy.method : !explicit] {\n    c = D_{m}(m^2)    :: [id=slope]\n}\n",
     "explicit-solution", "policy", ("applies D, an operator", _SOLVING), 3),
    ("[id=policy, policy.method : !explicit] {\n    c[>] = (1 - (R*β)^(1/ρ)/R)*(a + 1)\n"
     "    c = c[>]\n}\n",
     "explicit-solution", "policy", ("defines c[>], a field at another perch", "under !egm"), 3),
    ("[id=policy, policy.method : !explicit] {\n    κ = 1 - (R*β)^(1/ρ)/R    :: [id=mpc]\n}\n",
     "explicit-solution", "policy",
     ("no line the addition appends writes c", "write a line `c = <expression>` in the block"), 2),
    ("[id=policy, policy.method : !time_iteration] {\n"
     "    c = (1 - (R*β)^(1/ρ)/R)*(m - 1 + 1/(1 - Γ/R))    :: [id=consumption]\n}\n",
     "explicit-solution", "policy", ("builder under !time_iteration", "type !explicit"), 2),
    # an output whose row the kernel compiler refuses, checked where the
    # version is bound, after the construction's exclusions
    ("[id=policy, policy.method : !explicit] {\n    c = log(m)    :: [id=consumption]\n}\n",
     "explicit-solution", "policy", ("has no executable compiled kernel", "under kernel-form"),
     None),
)


@pytest.mark.parametrize("case", EXPLICIT_REFUSALS, ids=lambda case: case[0].split("\n")[0][:40])
def test_an_explicit_solution_that_reads_a_value_states_a_relation_or_misses_an_output_is_refused(
        case, perfect_foresight):
    """An `!explicit` builder with no block of its id in an addition, a
    forward builder, a relation, a read of a value input's derivative or of
    the control at which a value builder's declared lines are read, an
    operator, a field at another perch, a missing output and an output the
    kernel compiler writes into no function are refused, and so is a
    formula-only block under `!time_iteration`, each naming its cause and
    the method under which such a line is written, at the line at fault or
    at the typing entry where no line is."""
    entries, rule, address, words, line = case
    with pytest.raises(ConstructionError) as refused:
        copy_native(perfect_foresight).methodize(
            {"text": "@methods: perfect_foresight\n" + entries, "origin": "explicit.bl"})
    error = refused.value
    assert (error.rule, error.address) == (rule, address)
    if line is not None:
        assert (error.file, error.line) == ("explicit.bl", line)
    for word in words:
        assert word in error.message, (word, error.message)


# --- AMD-MT-003 unit D: the refusals of the scalar evaluators ---

# each refusal of the scalar evaluators of the perfect-foresight
# application's module (build contract §4): the construction, given the
# module, and the words its message holds
EVALUATOR_REFUSALS = {
    "one node": (lambda check: check.Linear([0.0], [1.0]), "at least two nodes"),
    "a value missing": (lambda check: check.Pchip([0.0, 1.0, 2.0], [1.0, 2.0]),
                        "one value aligned with each node"),
    "values on two coordinates": (lambda check: check.Linear([0.0, 1.0], [[1.0, 2.0], [3.0, 4.0]]),
                                  "one-dimensional"),
    "nodes out of order": (lambda check: check.Linear([0.0, 2.0, 1.0], [1.0, 2.0, 3.0]),
                           "strictly increasing"),
    "a repeated node": (lambda check: check.Pchip([0.0, 1.0, 1.0], [1.0, 2.0, 3.0]),
                        "neither sorted nor merged"),
    "a node that is not finite": (lambda check: check.Linear([0.0, math.inf], [1.0, 2.0]),
                                  "not finite"),
    "a value that is not finite": (lambda check: check.Pchip([0.0, 1.0], [math.nan, 2.0]),
                                   "not finite"),
    "nodes the conversion merges": (lambda check: check.Linear([2**53, 2**53 + 1], [1.0, 2.0]),
                                    "merges distinct nodes"),
    "a point outside the nodes": (lambda check: check.Linear([0.0, 1.0], [1.0, 2.0])(1.5),
                                  "outside the closed node interval"),
    "a PCHIP extrapolation": (lambda check: check.Pchip([0.0, 1.0, 2.0], [1.0, 2.0, 4.0])(-0.5),
                              "PCHIP extrapolation is refused"),
    "a derivative not offered": (
        lambda check: check.Linear([0.0, 1.0], [1.0, 2.0]).derivative(0.5, 2),
        "offers the derivatives of orders 1"),
    "an extension below the limit": (
        lambda check: check.Linear([0.0, 1.0], [0.5, 1.0]).extend(
            [-2.0], check.EndpointSecant(-1.0)),
        "restricted to the economic domain"),
    "an infeasible extension": (
        lambda check: check.Linear([0.0, 1.0], [0.1, 2.0]).extend(
            [-0.5], check.EndpointSecant(-1.0)),
        "leaves the feasible set"),
}


@pytest.mark.parametrize("case", sorted(EVALUATOR_REFUSALS))
def test_a_scalar_evaluator_refuses_data_and_points_outside_its_rules(case):
    """The Linear and PCHIP evaluators of the perfect-foresight application
    refuse fewer than two nodes, values not aligned one to a node, nodes out
    of order or repeated, nodes or values that are not finite, a conversion
    to floating point that merges nodes, a point outside the closed node
    interval, a PCHIP extrapolation and a derivative order not offered; the
    endpoint-secant extension refuses a point at or below its limit and a
    value outside the feasible set. Each message names its condition."""
    construction, words = EVALUATOR_REFUSALS[case]
    with pytest.raises(ValueError) as refused:
        construction(closed_form_check())
    assert words in str(refused.value), str(refused.value)
