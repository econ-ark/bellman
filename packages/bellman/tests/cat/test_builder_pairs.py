"""A builder is reached by the ordered pair of perches it joins,
`stage.builder["cntn", "dcsn"]` (the brief `builder-names-pair-base.md`),
and the perch paths are each defined as one pair: `stage.dcsn.builder.bwd`
is `stage.builder["cntn", "dcsn"]`.

`builder_pairs_base.json` beside this file is a fixed record of what the
retired paths `stage.build.sol.<perch>` and `stage.build.sim.<perch>`
answered for each builder of `cons.bl`, `port.bl` and `ret_choice.bl` at
commit f3b36071d, before the pair mapping was added: the block id of the
builder, and the first sixteen hexadecimal digits of the SHA-256 digest of
its printed `signature()` and of its printed `denote()` below the first
line, the card's title. A script made it from the symbolic stage,
`elaborate_stage(load_stage(path))`, following each dotted path,
`build.sol.dcsn` and the other four, with `getattr`; it would have written
a path that raised `AttributeError` as its refusal, and none raised. The
record was written a second time for commit e15b0381d of task 3 of the plan
of 29 September 2026, "The builders reached by the pair of perches they join",
with the digest of each card taken below its title: that task gave a backward
or a forward builder's card a title that prints the pair of perches it joins
and changed no other line of a card, so the text below the title is the text at
f3b36071d, and the block ids and the signature digests were written again
unchanged. The record is not re-recorded: the paths it was made from are
deleted, and the script with them, and item 1 compares what the pair mapping
answers now with what they answered."""
import hashlib
import json
import re
from pathlib import Path

import pytest

import bellman.stage
from bellman.stage import arvl, cntn, dcsn, elaborate_stage, load_stage
from bellman.display.drawing import to_drawing
from bellman.display.printed_records import NamedListing
from bellman.refusal_catalogue import refusal_of
from bellman.refusal_examples import EXAMPLES
from bellman.refusals import ConstructionError, NotConstructed
from bellman.stage.builder_pairs import builder_pairs
from bellman.stage.grains import graph_of
from bellman.stage.pieces import BuilderPairs, PerchBuilders

ROOT = Path(__file__).resolve().parents[4]
BASE = json.loads(Path(__file__).with_name("builder_pairs_base.json").read_text(encoding="utf-8"))
# the retired path under which the record holds each builder, and the pair
# that reads the builder now
PAIRS = {"build.sol.dcsn": ("cntn", "dcsn"), "build.sol.arvl": ("dcsn", "arvl"),
         "build.sim.arvl": ("arvl", "dcsn"), "build.sim.dcsn": ("dcsn", "cntn")}

# the joint-choice stage of `conftest.py` with its policy written as one block
# for each control, `policy_c` and `policy_l`: two backward builders write the
# controls, so the policy key names no one builder. It is the stage
# `two_policies` of `test_builder_names.py` item 3, copied and not imported.
TWO_ON_ONE_PAIR = """@stage: joint_choice
[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=dcsn_to_cntn, (x_d, c : ℝ @ !ctrl, l : ℝ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d + c + l
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c, l) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
 V = -c^2-4*l^2+V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
 V[<] = V
}
[id=policy_c, (V[>] : ℝ @ !vlu) -> (c : ℝ @ !ctrl) : !dcsn] {
 c = argmax_{c}(-c^2+V[>]) :: [id=choice]
}
[id=policy_l, (V[>] : ℝ @ !vlu) -> (l : ℝ @ !ctrl) : !dcsn] {
 l = argmax_{l}(-4*l^2+V[>]) :: [id=choice]
}
"""

# a stage with two forward blocks from arrival to decision, which the
# construction accepts, while it refuses two backward blocks on one pair
# (rule forward-composite)
TWO_FORWARD_ON_ONE_PAIR = """@stage: two_forward
[id=first, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=second, (y : ℝ) : !arvl -> (y_d : ℝ) : !dcsn] {
 y_d = y
}
[id=dcsn_to_cntn, (x_d, y_d) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d + y_d
}
"""

# a stage with two forward blocks and no backward block: the construction
# refuses its backward builders graph, "no backward builder", under the rule
# not-constructed, and constructs its forward builders graph
BACKWARD_REFUSED = """@stage: forward_only
[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=dcsn_to_cntn, (x_d) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d
}
"""

# a stage with two backward blocks and no forward block: the construction
# refuses its forward builders graph, "no forward builder", under the rule
# not-constructed, and constructs its backward builders graph
FORWARD_REFUSED = """@stage: backward_only
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu) : !dcsn] {
 V = V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
 V[<] = V
}
"""

# a stage with two forward blocks from decision to continuation, which the
# construction accepts
TWO_FORWARD_FROM_DECISION = """@stage: two_forward_from_decision
[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=first, (x_d) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d
}
[id=second, (x_d) : !dcsn -> (b : ℝ) : !cntn] {
 b = x_d
}
"""

# each perch path, by its perch and its direction word, and the pair of
# `stage.builder` that defines it
PERCH_PATHS = {("arvl", "fwd"): ("arvl", "dcsn"), ("arvl", "bwd"): ("dcsn", "arvl"),
               ("dcsn", "fwd"): ("dcsn", "cntn"), ("dcsn", "bwd"): ("cntn", "dcsn")}

# each block id of `cons.bl` and the id that replaces it, which names no
# perch, so that a builder can be found only by the perches its header writes
RENAMED = {"arvl_to_dcsn": "first", "dcsn_to_cntn": "second", "cntn_to_dcsn": "third",
           "dcsn_to_arvl": "fourth", "policy": "choose"}
# a retired path, which no refusal text writes
RETIRED = re.compile(r"\bstage\.build\b")
# the stage files of the core applications, each in its stage folder
# `declaration/stages/<key>/`, as the corpus test of `tests/sym/test_corpus.py`
# reads them
CORE_STAGES = sorted((ROOT / "applications").glob("*/declaration/stages/*/*.bl"))


def elaborated(relative):
    return elaborate_stage(load_stage(str(ROOT / relative)))


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def denote_digest(handle):
    """The digest the record holds for `handle.denote()`: that of the card
    below its first line, the title, which a backward or a forward builder
    now prints with the pair of perches it joins (the plan of 29 September
    2026, "The builders reached by the pair of perches they join", task 3),
    so the comparison this file makes does not fail on the one line that task
    changed."""
    return digest("\n".join(str(handle.denote()).splitlines()[1:]))


@pytest.mark.parametrize("relative", sorted(BASE["stages"]))
def test_item_1_each_pair_answers_what_the_retired_path_answered(relative):
    stage = elaborated(relative)
    for path, pair in PAIRS.items():
        recorded = BASE["stages"][relative][path]
        if isinstance(recorded, str):          # the path was refused at the base
            with pytest.raises(KeyError):
                stage.builder[pair]
            continue
        handle = stage.builder[pair]
        assert handle.box.name == recorded["box"]
        assert denote_digest(handle) == recorded["denote"]
        assert digest(str(handle.signature())) == recorded["signature"]
    recorded = BASE["stages"][relative]["build.sol.policy"]
    policy = stage.builder.policy
    assert policy.box.name == recorded["box"]
    assert denote_digest(policy) == recorded["denote"]
    assert digest(str(policy.signature())) == recorded["signature"]
    # no builder joins decision to decision, so that pair is refused like any
    # absent pair; the policy builder is read by its own key alone
    with pytest.raises(KeyError, match="no builder joins dcsn → dcsn"):
        stage.builder["dcsn", "dcsn"]


def test_item_2_the_listing_names_every_pair_once_forward_first():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    listed = stage.builder.list()
    # a printed record keyed by the block identifier, as every other
    # level's `list()` answers
    assert isinstance(listed, NamedListing)
    assert [pair for pair, _ in listed.values()] == ["arvl → dcsn", "dcsn → cntn", "cntn → dcsn",
                                                     "dcsn → arvl", "policy"]
    # five distinct block identifiers, the keys
    assert list(listed) == ["arvl_to_dcsn", "dcsn_to_cntn", "cntn_to_dcsn",
                            "dcsn_to_arvl", "policy"]
    assert [word for _, word in listed.values()] == ["fwd", "fwd", "bwd", "bwd", "bwd"]
    # iteration gives the keys in the order of the listing
    assert list(stage.builder) == [("arvl", "dcsn"), ("dcsn", "cntn"), ("cntn", "dcsn"),
                                   ("dcsn", "arvl"), "policy"]
    assert len(stage.builder) == 5 and repr(stage.builder) == "Builders('cons', 5 by their perches)"
    printed = stage.builder.view().splitlines()
    assert len(printed) == 5 and printed[0] == "arvl_to_dcsn   arvl → dcsn, fwd"
    assert stage.builder.view() == str(listed) == repr(listed)


def test_item_3_an_absent_pair_is_refused_naming_the_pairs_that_exist():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    with pytest.raises(KeyError) as refusal:
        stage.builder["cntn", "arvl"]
    assert "no builder joins cntn → arvl" in str(refusal.value)
    assert "arvl → dcsn" in str(refusal.value) and "cntn → dcsn" in str(refusal.value)
    with pytest.raises(KeyError) as bad_word:
        stage.builder["arvl", "somewhere"]
    assert "'somewhere' is no perch" in str(bad_word.value)


def test_item_4_the_two_graphs_and_the_constants(cons_methodized):
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    assert stage.builder.bwd.direction == "backward" and stage.builder.fwd.direction == "forward"
    assert stage.builder[cntn, dcsn].box is stage.builder["cntn", "dcsn"].box
    assert (arvl, dcsn, cntn) == ("arvl", "dcsn", "cntn")
    assert {"arvl", "dcsn", "cntn"} <= set(bellman.stage.__all__)
    # the lazy resolver serves each perch word from the module that defines it
    assert [bellman.stage.__getattr__(word) for word in ("arvl", "dcsn", "cntn")] == ["arvl", "dcsn", "cntn"]
    # the methods bound within the builders are those bound within the two graphs
    bound = cons_methodized.builder
    assert dict(bound.methods) and dict(bound.methods) == {**bound.bwd.methods, **bound.fwd.methods}


def test_a_pair_read_through_a_chain_holds_the_chained_version():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    calibration = str(ROOT / "applications/cons-port/declaration/calibration/portfolio.yml")
    chained = stage.calibrate(calibration)
    handle = chained.builder["cntn", "dcsn"]
    # `calibrate` binds the stage it is called on and returns it
    # (specification 0.6 decision 1 and R4)
    assert handle.version is chained and chained is stage
    # a version bound to no name holds the calibration it was given
    assert stage.calibrate(calibration).builder["cntn", "dcsn"].version.par["ρ"].value == 6.0


def test_two_builders_on_one_pair_are_refused_with_both_ids(elaborate_text):
    two = elaborate_text(TWO_ON_ONE_PAIR)
    # the attributes are refused as attributes, the keys as keys
    for read, expected in ((lambda: two.builder.policy, AttributeError),
                           (lambda: two.dcsn.builder.policy, AttributeError),
                           (lambda: two.builder["policy"], KeyError)):
        with pytest.raises(expected) as refusal:
            read()
        message = str(refusal.value)
        assert "two builders" in message, message
        assert "stage.builder.bwd['policy_c']" in message, message
        assert "stage.builder.bwd['policy_l']" in message, message
    # decision to decision is no key of the policy builders
    with pytest.raises(KeyError, match="no builder joins dcsn → dcsn"):
        two.builder["dcsn", "dcsn"]
    # the key the refusal names reads each builder
    assert two.builder.bwd["policy_c"].box.name == "policy_c"
    # the listing names each policy builder under its own block identifier
    assert [block for block, (pair, _) in two.builder.list().items() if pair == "policy"] == [
        "policy_c", "policy_l"]
    assert not hasattr(two.builder, "policy")
    # two builders on one pair of perches, each named with its direction word
    forward = elaborate_text(TWO_FORWARD_ON_ONE_PAIR)
    with pytest.raises(KeyError) as refusal:
        forward.builder["arvl", "dcsn"]
    message = str(refusal.value)
    assert "two builders join arvl → dcsn" in message, message
    assert "stage.builder.fwd['first']" in message and "stage.builder.fwd['second']" in message


def test_a_stage_without_a_policy_builder_answers_hasattr_false_and_refuses_the_key():
    stage = elaborated("applications/durables/declaration/stages/bequest/bequest.bl")
    assert not hasattr(stage.builder, "policy")
    with pytest.raises(KeyError) as refusal:
        stage.builder["policy"]
    assert "no policy builder" in str(refusal.value)
    assert "policy" not in stage.builder
    # the attribute is refused with the message of the key, without the quotation
    # marks that `str` of a KeyError adds
    with pytest.raises(AttributeError) as attribute:
        stage.builder.policy
    assert str(attribute.value) == refusal.value.args[0]


def test_a_refused_direction_is_reported_at_its_pairs(elaborate_text):
    broken = elaborate_text(BACKWARD_REFUSED)
    with pytest.raises(NotConstructed):                  # the premise of the fixture
        graph_of(broken, "builders", "backward")
    graph_of(broken, "builders", "forward")              # constructed, so no refusal
    for key in (("cntn", "dcsn"), ("dcsn", "arvl"), "policy"):
        with pytest.raises(NotConstructed) as refusal:
            broken.builder[key]
        assert "no backward builder" in str(refusal.value), key
    # each perch path of the refused direction raises the same refusal
    for read in (lambda: broken.dcsn.builder.bwd, lambda: broken.arvl.builder.bwd,
                 lambda: broken.dcsn.builder.policy):
        with pytest.raises(NotConstructed) as refusal:
            read()
        assert "no backward builder" in str(refusal.value)
    assert broken.builder["arvl", "dcsn"].box.name == "arvl_to_dcsn"
    assert broken.builder["dcsn", "cntn"].box.name == "dcsn_to_cntn"
    assert broken.dcsn.builder.fwd.box is broken.builder["dcsn", "cntn"].box
    # the listing, the keys and the methods answer for the forward side
    assert list(broken.builder.list()) == ["arvl_to_dcsn", "dcsn_to_cntn"]
    assert list(broken.builder) == [("arvl", "dcsn"), ("dcsn", "cntn")] and len(broken.builder) == 2
    bound = broken.methodize({"methods": [{"on": "arvl_to_dcsn", "method": "deterministic"}]})
    assert {str(place): method.tag for place, method in bound.builder.methods.items()} == {
        "arvl_to_dcsn": "deterministic"}


def test_a_refused_forward_direction_is_reported_at_its_pairs(elaborate_text):
    broken = elaborate_text(FORWARD_REFUSED)
    with pytest.raises(NotConstructed):                  # the premise of the fixture
        graph_of(broken, "builders", "forward")
    graph_of(broken, "builders", "backward")             # constructed, so no refusal
    for read in (lambda: broken.builder["arvl", "dcsn"], lambda: broken.builder["dcsn", "cntn"],
                 lambda: broken.arvl.builder.fwd, lambda: broken.dcsn.builder.fwd):
        with pytest.raises(NotConstructed) as refusal:
            read()
        assert "no forward builder" in str(refusal.value)
    assert broken.dcsn.builder.bwd.box is broken.builder["cntn", "dcsn"].box
    assert broken.arvl.builder.bwd.box.name == "dcsn_to_arvl"
    # the listing, the keys and the methods answer for the backward side
    assert list(broken.builder.list()) == ["cntn_to_dcsn", "dcsn_to_arvl"]
    assert list(broken.builder) == [("cntn", "dcsn"), ("dcsn", "arvl")] and len(broken.builder) == 2
    grid = {"grid": "!Cartesian", "orders": {"V": "n_V"}, "bounds": {"V": ["V_min", "V_max"]}}
    bound = broken.methodize({"methods": [{"on": "cntn_to_dcsn.evaluate.value", "method": "Linear",
                                           "settings": grid}]})
    assert {str(place): method.tag for place, method in bound.builder.methods.items()} == {
        "cntn_to_dcsn:Evaluation": "Linear"}


def test_the_keys_are_those_the_mapping_answers_and_the_listing_names_every_builder(
        elaborate_text, monkeypatch):
    two = elaborate_text(TWO_ON_ONE_PAIR)
    assert "policy" not in two.builder and "policy" not in list(two.builder)
    assert list(two.builder) == [("arvl", "dcsn"), ("dcsn", "cntn"), ("cntn", "dcsn"), ("dcsn", "arvl")]
    assert len(two.builder) == len(list(two.builder)) == len(dict(two.builder))
    # the listing keeps an entry for each of the two policy builders, which
    # no key reads
    assert len(two.builder.list()) == len(two.builder) + 2
    # the short form counts the builders the listing names, not the keys
    assert repr(two.builder) == "Builders('joint_choice', 6 by their perches)"
    # a pair that two builders join is no key either
    forward = elaborate_text(TWO_FORWARD_ON_ONE_PAIR)
    assert list(dict(forward.builder)) == [("dcsn", "cntn")] and len(forward.builder.list()) == 3
    # no builder joins decision to decision, so that pair is no key and is
    # refused like any absent pair
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    assert ("dcsn", "dcsn") not in list(stage.builder) and ("dcsn", "dcsn") not in stage.builder
    with pytest.raises(KeyError, match="no builder joins dcsn → dcsn"):
        stage.builder["dcsn", "dcsn"]
    # the pair has no special case: a builder other than the policy builder
    # that joined decision to decision, which no stage file yields, would be
    # read by that pair and iterated as a key, before `policy`
    pairs, policies, refused = builder_pairs(stage)
    joined = object()
    monkeypatch.setattr(BuilderPairs, "_table",
                        lambda self: ({**pairs, ("dcsn", "dcsn"): [joined]}, policies, refused))
    assert list(stage.builder)[-2:] == [("dcsn", "dcsn"), "policy"]
    assert stage.builder["dcsn", "dcsn"].box is joined


@pytest.mark.parametrize("src", CORE_STAGES,
                         ids=lambda path: path.relative_to(ROOT / "applications").as_posix())
def test_item_5_each_perch_path_answers_its_pair_by_identity(src):
    """Acceptance item 2 of the brief, on every core stage the construction
    accepts: each perch path of `PERCH_PATHS` answers the box its pair
    answers, and `stage.dcsn.builder.policy` the box of
    `stage.builder.policy`; a path the stage refuses is refused with its
    pair. A stage file the construction refuses is skipped, and the corpus
    test of `tests/sym/test_corpus.py` records why."""
    try:
        stage = elaborate_stage(load_stage(str(src)))
    except ConstructionError as refusal:
        pytest.skip(f"the construction refuses the stage under {refusal.rule}")
    answered = 0
    for (perch, word), pair in PERCH_PATHS.items():
        try:
            reached = getattr(getattr(stage, perch).builder, word)
        except (AttributeError, NotConstructed):
            with pytest.raises((KeyError, NotConstructed)):
                stage.builder[pair]
            continue
        assert reached.box is stage.builder[pair].box, (perch, word)
        answered += 1
    try:
        policy = stage.builder.policy
    except (AttributeError, NotConstructed):
        with pytest.raises((AttributeError, NotConstructed)):
            stage.dcsn.builder.policy
    else:
        assert stage.dcsn.builder.policy.box is policy.box
        answered += 1
    assert answered, "the stage answers no perch path"


def test_item_6_the_continuation_perch_refuses_both_directions_with_the_reason():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    with pytest.raises(AttributeError) as bwd:
        stage.cntn.builder.bwd
    assert "no value is built at continuation" in str(bwd.value)
    assert "next stage's arrival value" in str(bwd.value)
    with pytest.raises(AttributeError) as fwd:
        stage.cntn.builder.fwd
    assert "leaves the stage at continuation" in str(fwd.value)
    for perch in (stage.arvl, stage.cntn):
        with pytest.raises(AttributeError) as policy:
            perch.builder.policy
        assert "the policy builder stands at the decision perch" in str(policy.value), perch


def test_each_perch_lists_its_paths_with_the_key_each_reads():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    # a printed record keyed by the path, in the order of the paths
    assert isinstance(stage.dcsn.builder.list(), NamedListing)
    assert list(stage.arvl.builder.list().items()) == [("stage.arvl.builder.fwd", "arvl → dcsn"),
                                                       ("stage.arvl.builder.bwd", "dcsn → arvl")]
    assert list(stage.dcsn.builder.list().items()) == [("stage.dcsn.builder.fwd", "dcsn → cntn"),
                                                       ("stage.dcsn.builder.bwd", "cntn → dcsn"),
                                                       ("stage.dcsn.builder.policy", "policy")]
    assert (str(stage.dcsn.builder.list()).splitlines()[0]
            == "stage.dcsn.builder.fwd      dcsn → cntn")
    assert len(stage.cntn.builder.list()) == 0 and str(stage.cntn.builder.list()) == "none"
    # two handles of one perch, each made when it is read, compare equal
    assert stage.dcsn == stage.dcsn and stage.dcsn != stage.arvl
    assert repr(stage.dcsn) == "Perch('cons', 'dcsn')"


def test_a_word_that_names_no_perch_is_refused_naming_the_three():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    nowhere = PerchBuilders(stage, "somewhere")
    for word in ("fwd", "bwd", "policy"):
        with pytest.raises(AttributeError) as refusal:
            getattr(nowhere, word)
        assert str(refusal.value) == "'somewhere' is no perch; the perches are arvl, dcsn, cntn", word
    assert len(nowhere.list()) == 0


def test_a_terminal_stage_has_no_forward_decision_builder():
    stage = elaborated("applications/durables/declaration/stages/bequest/bequest.bl")
    with pytest.raises(AttributeError) as refusal:
        stage.dcsn.builder.fwd
    assert "terminal stage" in str(refusal.value) or "no decision edge" in str(refusal.value)
    with pytest.raises(KeyError, match="no builder joins dcsn → cntn"):
        stage.builder["dcsn", "cntn"]
    assert stage.arvl.builder.fwd.box.name == "arvl_to_dcsn"


def test_two_forward_builders_from_decision_are_refused_as_two_not_as_a_terminal_stage(elaborate_text):
    two = elaborate_text(TWO_FORWARD_FROM_DECISION)
    with pytest.raises(AttributeError) as refusal:
        two.dcsn.builder.fwd
    message = str(refusal.value)
    assert "two builders join dcsn → cntn" in message and "terminal" not in message, message
    assert "stage.builder.fwd['first']" in message and "stage.builder.fwd['second']" in message


def test_a_branching_stage_has_one_forward_decision_builder():
    stage = elaborated(
        "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl")
    listed = [block for block, (pair, _) in stage.builder.list().items() if pair == "dcsn → cntn"]
    assert len(listed) == 1
    assert stage.dcsn.builder.fwd.box is stage.builder["dcsn", "cntn"].box


def test_a_builder_is_read_by_the_perches_it_joins_whatever_its_block_id(elaborate_text, text_of):
    text = text_of("cons")
    for old, new in RENAMED.items():
        assert text.count(f"[id={old},") == 1, old
        text = text.replace(f"[id={old},", f"[id={new},")
    stage = elaborate_text(text, "cons.bl")
    joined = {("arvl", "dcsn"): "first", ("dcsn", "cntn"): "second",
              ("cntn", "dcsn"): "third", ("dcsn", "arvl"): "fourth"}
    for pair, block in joined.items():
        assert stage.builder[pair].box.name == block, pair
    for (perch, word), pair in PERCH_PATHS.items():
        assert getattr(getattr(stage, perch).builder, word).box.name == joined[pair], (perch, word)
    assert stage.builder.policy.box.name == stage.dcsn.builder.policy.box.name == "choose"
    assert list(stage.builder.list()) == ["first", "second", "third", "fourth", "choose"]


def test_the_refusals_that_name_a_builders_graph_name_its_path_under_stage_builder():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    # a target that names no box, and a kernel asked of a block's line
    not_found = refusal_of(EXAMPLES["target-not-found"])
    assert not_found.rule == "target-not-found"
    with pytest.raises(ConstructionError) as not_a_kernel:
        stage.initial.backward["cntn_to_dcsn"]["cntn_to_dcsn.value"].kernel()
    assert not_a_kernel.value.rule == "kernel-target"
    for refusal in (not_found, not_a_kernel.value):
        message = str(refusal)
        assert "stage.builder.bwd.primitives.list() or stage.builder.fwd.primitives.list()" in message, message
    # a drawing asked of an object that is no graph
    with pytest.raises(TypeError) as not_a_graph:
        to_drawing("no graph")
    assert "stage.builder.bwd.graph" in str(not_a_graph.value)
    # the kernels asked of a block of an initial diagram
    with pytest.raises(TypeError) as a_block:
        stage.initial.backward["cntn_to_dcsn"].kernels()
    assert "stage.builder.bwd or stage.builder.fwd answers kernels()" in str(a_block.value)
    for refusal in (not_found, not_a_kernel.value, not_a_graph.value, a_block.value):
        assert RETIRED.search(str(refusal)) is None, str(refusal)


def test_the_stage_listing_names_each_builder_with_its_pair_and_direction_word():
    stage = elaborated("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    section = stage.list()["builder"]
    assert list(section) == ["arvl_to_dcsn", "dcsn_to_cntn", "cntn_to_dcsn", "dcsn_to_arvl", "policy"]
    # the section is the listing `stage.builder.list()` answers
    assert section == stage.builder.list() and list(section) == list(stage.builder.list())
    assert section["cntn_to_dcsn"] == ("cntn → dcsn", "bwd") and section["policy"] == ("policy", "bwd")
    assert "  cntn_to_dcsn   cntn → dcsn, bwd" in str(stage.list()).splitlines()
