"""The builders of a stage: each read by the pair of perches that it joins, by
a perch path or by the key of the policy builder; their listing and short
form; the refusals of a key that no builder or two builders answer; and the
primitive operations of a builders graph."""

import re

import pytest
from application_files import CONTROL_BRANCHING_STAGE_FILES, ROOT, stage_file_id
from model_explorer_views import FORWARD_ONLY_STAGE
from snapshot.record import ELABORATED_FILES
from stage_builders import stage_from_text
from stage_texts import UNADMITTED_FAMILY_AT_ARRIVAL, corpus_text
from two_sets import one_row_by_default

import bellman.stage
from bellman.display.drawing import to_drawing
from bellman.display.printed_records import NamedListing
from bellman.refusal_catalogue import refusal_of
from bellman.refusal_examples import EXAMPLES
from bellman.refusals import ConstructionError, NotConstructed
from bellman.stage import arvl, cntn, dcsn
from bellman.stage.grains import block_id_of, operators_of
from bellman.stage.pieces import PerchBuilders

# the terminal stage of the durables application, which has no policy
# builder and no forward block from decision to continuation
BEQUEST = ROOT / "applications/durables/declaration/stages/bequest/bequest.bl"


# the retirement choice, a branching stage
RET_CHOICE = ROOT / CONTROL_BRANCHING_STAGE_FILES["ret_choice"]


# a stage of two controls with its policy written as one block for each
# control, `policy_c` and `policy_l`: two backward builders write the
# controls, so that the key `policy` names no one builder. Each block
# maximizes the right side of the value V over its own control, read at the
# other control, which its header lists
TWO_POLICY_BLOCKS = """@stage: joint_choice
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
[id=policy_c, (V[>] : ℝ @ !vlu, l) -> (c : ℝ @ !ctrl) : !dcsn] {
 c = argmax_{c}(-c^2-4*l^2+V[>]) :: [id=choice]
}
[id=policy_l, (V[>] : ℝ @ !vlu, c) -> (l : ℝ @ !ctrl) : !dcsn] {
 l = argmax_{l}(-c^2-4*l^2+V[>]) :: [id=choice]
}
"""


# a stage with two forward blocks from arrival to decision, which the
# construction accepts, so that the pair from arrival to decision names no
# one builder
TWO_FORWARD_BLOCKS_INTO_DECISION = """@stage: two_forward
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
TWO_FORWARD_BLOCKS_FROM_DECISION = """@stage: two_forward_from_decision
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
PERCH_PATHS = {
    ("arvl", "fwd"): ("arvl", "dcsn"),
    ("arvl", "bwd"): ("dcsn", "arvl"),
    ("dcsn", "fwd"): ("dcsn", "cntn"),
    ("dcsn", "bwd"): ("cntn", "dcsn"),
}


# the attribute of `stage.builder` that answers the builders graph of each
# direction, and the attribute that answers the graph of the other direction
GRAPH_WORDS = {"backward": ("bwd", "fwd"), "forward": ("fwd", "bwd")}


# the test id of each perch path
PERCH_PATH_IDS = [f"stage.{perch}.builder.{word}" for perch, word in PERCH_PATHS]


# each block id of `cons.bl` and the id that replaces it; no new id names a
# perch, so that a builder can be found only by the perches that the header
# of its block joins
NEW_BLOCK_IDS = {
    "arvl_to_dcsn": "first",
    "dcsn_to_cntn": "second",
    "cntn_to_dcsn": "third",
    "dcsn_to_arvl": "fourth",
    "policy": "choose",
}


# the path `stage.build`, which the package does not answer: a refusal names
# the builders under `stage.builder`, and the pattern does not match that
# longer word
STAGE_BUILD = re.compile(r"\bstage\.build\b")


@pytest.fixture(scope="module")
def two_policy_builders():
    """The stage of `TWO_POLICY_BLOCKS`, whose controls two backward
    builders write."""
    return stage_from_text(TWO_POLICY_BLOCKS)


@pytest.fixture(scope="module")
def two_forward_builders():
    """The stage of `TWO_FORWARD_BLOCKS_INTO_DECISION`, in which two forward
    builders join arrival to decision."""
    return stage_from_text(TWO_FORWARD_BLOCKS_INTO_DECISION)


@pytest.fixture(scope="module")
def stage_without_backward_blocks():
    """The stage of `FORWARD_ONLY_STAGE`, whose backward builders graph the
    construction refuses."""
    return stage_from_text(FORWARD_ONLY_STAGE)


@pytest.fixture(scope="module")
def stage_without_forward_blocks():
    """The stage of `FORWARD_REFUSED`, whose forward builders graph the
    construction refuses."""
    return stage_from_text(FORWARD_REFUSED)


@pytest.fixture(scope="module")
def stage_with_new_block_ids():
    """The consumption stage with each block id replaced by its new id of
    `NEW_BLOCK_IDS`."""
    text = corpus_text("cons")
    for old, new in NEW_BLOCK_IDS.items():
        text = text.replace(f"[id={old},", f"[id={new},")
    return stage_from_text(text, "cons.bl")


def test_the_listing_of_the_builders_names_each_by_its_block_id_with_its_pair_and_direction_word(
    cons,
):
    """The listing of the builders of the consumption stage names each
    builder by the id of its block, with its pair and its direction word, the
    forward builders first."""
    listed = cons.builder.list()
    # a printed record keyed by the id of the block, as `list()` answers at
    # every level
    assert isinstance(listed, NamedListing)
    assert [pair for pair, _ in listed.values()] == [
        "arvl → dcsn",
        "dcsn → cntn",
        "cntn → dcsn",
        "dcsn → arvl",
        "policy",
    ]
    # five distinct block ids, the keys
    assert list(listed) == [
        "arvl_to_dcsn",
        "dcsn_to_cntn",
        "cntn_to_dcsn",
        "dcsn_to_arvl",
        "policy",
    ]
    assert [word for _, word in listed.values()] == ["fwd", "fwd", "bwd", "bwd", "bwd"]


def test_the_keys_of_the_builders_are_their_pairs_and_policy_in_the_order_of_the_listing(cons):
    """Iteration over the builders of the consumption stage gives the pair of
    each builder and the key `policy`, in the order of the listing, and the
    length of the builders counts these five keys."""
    assert list(cons.builder) == [
        ("arvl", "dcsn"),
        ("dcsn", "cntn"),
        ("cntn", "dcsn"),
        ("dcsn", "arvl"),
        "policy",
    ]
    assert len(cons.builder) == 5


@pytest.mark.parametrize(
    ("stage_name", "short_form"),
    [
        pytest.param(
            "cons", "Builders('cons', 5 by their perches)", id="one builder for each key"
        ),
        # four keys, and six builders in the listing
        pytest.param(
            "two_policy_builders",
            "Builders('joint_choice', 6 by their perches)",
            id="two policy builders that no key reads",
        ),
    ],
)
def test_the_short_form_of_the_builders_counts_the_builders_that_the_listing_names(
    stage_name, short_form, request
):
    """The short form of the builders names the stage and counts the builders
    that the listing names, not the keys."""
    assert repr(request.getfixturevalue(stage_name).builder) == short_form


def test_the_view_of_the_builders_prints_the_listing_one_line_for_each_builder(cons):
    """The view of the builders of the consumption stage is the printed
    listing, one line for each of its five builders."""
    listed = cons.builder.list()
    printed = cons.builder.view().splitlines()
    assert len(printed) == 5 and printed[0] == "arvl_to_dcsn   arvl → dcsn, fwd"
    assert cons.builder.view() == str(listed) == repr(listed)


@pytest.mark.parametrize(
    ("stage_name", "pair", "phrase"),
    [
        pytest.param(
            "cons",
            ("cntn", "arvl"),
            "no builder joins cntn → arvl",
            id="continuation to arrival",
        ),
        pytest.param(
            "cons",
            ("dcsn", "dcsn"),
            "no builder joins dcsn → dcsn",
            id="decision to decision",
        ),
        # the two policy builders stand at the decision perch and join no
        # pair of perches
        pytest.param(
            "two_policy_builders",
            ("dcsn", "dcsn"),
            "no builder joins dcsn → dcsn",
            id="decision to decision in a stage of two policy builders",
        ),
    ],
)
def test_a_pair_that_no_builder_joins_is_no_key_and_is_refused_naming_the_builders(
    stage_name, pair, phrase, request
):
    """A pair that no builder joins is no key of the builders, and reading it
    raises a `KeyError` that names the pair and, among the builders of the
    stage, those from arrival to decision and from continuation to
    decision."""
    stage = request.getfixturevalue(stage_name)
    assert pair not in list(stage.builder) and pair not in stage.builder
    with pytest.raises(KeyError) as refusal:
        stage.builder[pair]
    phrases = [phrase, "arvl → dcsn", "cntn → dcsn"]
    assert [held for held in phrases if held not in str(refusal.value)] == []


def test_a_pair_with_a_word_that_names_no_perch_is_refused_naming_the_word(cons):
    """Reading the builders by a pair with a word that names no perch raises a
    `KeyError` that names the word."""
    with pytest.raises(KeyError) as refusal:
        cons.builder["arvl", "somewhere"]
    assert "'somewhere' is no perch" in str(refusal.value)


def test_the_builders_answer_the_backward_graph_as_bwd_and_the_forward_graph_as_fwd(cons):
    """`stage.builder.bwd` is the backward builders graph and
    `stage.builder.fwd` the forward builders graph."""
    assert cons.builder.bwd.direction == "backward" and cons.builder.fwd.direction == "forward"


def test_the_perch_words_that_bellman_stage_exports_read_the_builders_as_the_strings_do(cons):
    """`bellman.stage` exports the perch words `arvl`, `dcsn` and `cntn`,
    which are the strings of the three perches, so that a pair written with
    them reads the builder that the strings read."""
    assert {"arvl", "dcsn", "cntn"} <= set(bellman.stage.__all__)
    assert (arvl, dcsn, cntn) == ("arvl", "dcsn", "cntn")
    assert cons.builder[cntn, dcsn].box is cons.builder["cntn", "dcsn"].box


def test_the_methods_bound_within_the_builders_are_those_bound_within_the_two_graphs(
    cons_methodized,
):
    """On the methodized consumption stage, the methods bound within the
    builders are the methods bound within the backward graph and the forward
    graph together, and there are some."""
    bound = cons_methodized.builder
    assert dict(bound.methods) and dict(bound.methods) == {
        **bound.bwd.methods,
        **bound.fwd.methods,
    }


def test_a_builder_read_through_calibrate_holds_the_calibrated_stage_itself():
    """A builder read from what `calibrate` returns holds the stage that
    `calibrate` was called on, which it binds and returns, with the values
    of the calibration."""
    stage = stage_from_text(corpus_text("cons"), "cons.bl")
    calibration = str(ROOT / "applications/cons-port/declaration/calibration/portfolio.yml")
    chained = stage.calibrate(calibration)
    handle = chained.builder["cntn", "dcsn"]
    # `calibrate` binds the stage that it is called on and returns that stage
    assert handle.version is chained and chained is stage
    # a version bound to no name holds the calibration that it was given;
    # portfolio.yml gives ρ the value 6.0
    assert stage.calibrate(calibration).builder["cntn", "dcsn"].version.par["ρ"].value == 6.0


@pytest.mark.parametrize(
    ("read", "error"),
    [
        pytest.param(
            lambda stage: stage.builder.policy, AttributeError, id="the attribute of the builders"
        ),
        pytest.param(
            lambda stage: stage.dcsn.builder.policy,
            AttributeError,
            id="the perch path stage.dcsn.builder.policy",
        ),
        pytest.param(lambda stage: stage.builder["policy"], KeyError, id="the key policy"),
    ],
)
def test_two_policy_builders_are_refused_at_the_policy_builder_naming_the_key_of_each(
    read, error, two_policy_builders
):
    """Where two backward builders write the controls, each read of the policy
    builder is refused, an attribute with an `AttributeError` and the key
    with a `KeyError`, naming for each builder the key of the backward graph
    that reads it by the id of its block."""
    with pytest.raises(error) as refusal:
        read(two_policy_builders)
    phrases = ["two builders", "stage.builder.bwd['policy_c']", "stage.builder.bwd['policy_l']"]
    assert [phrase for phrase in phrases if phrase not in str(refusal.value)] == []


def test_the_keys_that_the_refusal_of_two_policy_builders_names_read_each_builder(
    two_policy_builders,
):
    """Where two backward builders write the controls, the key of the backward
    graph by the id of each block, which the refusal of the policy builder
    names, reads that builder."""
    graph = two_policy_builders.builder.bwd
    assert [graph[block].box.name for block in ("policy_c", "policy_l")] == [
        "policy_c",
        "policy_l",
    ]


def test_where_two_builders_write_the_controls_the_keys_are_the_four_pairs_without_policy(
    two_policy_builders,
):
    """Where two backward builders write the controls, the keys of the
    builders are the four pairs of perches without `policy`, and the length
    of the builders counts them."""
    builders = two_policy_builders.builder
    assert "policy" not in builders and "policy" not in list(builders)
    assert list(builders) == [
        ("arvl", "dcsn"),
        ("dcsn", "cntn"),
        ("cntn", "dcsn"),
        ("dcsn", "arvl"),
    ]
    assert len(builders) == len(list(builders)) == len(dict(builders))


def test_the_listing_names_each_of_two_policy_builders_under_its_block_id(two_policy_builders):
    """Where two backward builders write the controls, the listing names each
    under the id of its block, with the key `policy`, although no key reads
    either."""
    listed = two_policy_builders.builder.list()
    assert [block for block, (pair, _) in listed.items() if pair == "policy"] == [
        "policy_c",
        "policy_l",
    ]
    # an entry for each of the two policy builders beyond the keys
    assert len(listed) == len(two_policy_builders.builder) + 2


def test_a_pair_that_two_forward_builders_join_is_refused_naming_each_by_its_block_id(
    two_forward_builders,
):
    """Reading a pair that two forward builders join raises a `KeyError` that
    names the pair and, for each builder, the key of the forward graph that
    reads it by the id of its block."""
    with pytest.raises(KeyError) as refusal:
        two_forward_builders.builder["arvl", "dcsn"]
    phrases = [
        "two builders join arvl → dcsn",
        "stage.builder.fwd['first']",
        "stage.builder.fwd['second']",
    ]
    assert [phrase for phrase in phrases if phrase not in str(refusal.value)] == []


def test_a_pair_that_two_forward_builders_join_is_no_key_while_the_listing_names_all_three(
    two_forward_builders,
):
    """Where two forward builders join arrival to decision, the one key of the
    builders is the pair from decision to continuation, while the listing
    names all three builders of the stage."""
    builders = two_forward_builders.builder
    assert list(dict(builders)) == [("dcsn", "cntn")] and len(builders.list()) == 3


def test_a_stage_without_a_policy_builder_refuses_the_policy_key_and_attribute_with_one_message(
    read_only_stage_from_file,
):
    """The bequest stage of the durables application, which has no policy
    builder, refuses the key `policy` with a `KeyError` and the attribute
    `policy` with an `AttributeError` of the same message."""
    stage = read_only_stage_from_file(BEQUEST)
    assert not hasattr(stage.builder, "policy")
    with pytest.raises(KeyError) as refusal:
        stage.builder["policy"]
    assert "no policy builder" in str(refusal.value)
    assert "policy" not in stage.builder
    # the attribute is refused with the message of the key, without the
    # quotation marks that `str` of a KeyError adds
    with pytest.raises(AttributeError) as attribute:
        stage.builder.policy
    assert str(attribute.value) == refusal.value.args[0]


@pytest.mark.parametrize(
    ("stage_name", "refused", "read"),
    [
        pytest.param(
            "stage_without_backward_blocks",
            "backward",
            lambda stage: stage.builder["cntn", "dcsn"],
            id="no backward block, the pair cntn → dcsn",
        ),
        pytest.param(
            "stage_without_backward_blocks",
            "backward",
            lambda stage: stage.builder["dcsn", "arvl"],
            id="no backward block, the pair dcsn → arvl",
        ),
        pytest.param(
            "stage_without_backward_blocks",
            "backward",
            lambda stage: stage.builder["policy"],
            id="no backward block, the key policy",
        ),
        pytest.param(
            "stage_without_backward_blocks",
            "backward",
            lambda stage: stage.dcsn.builder.bwd,
            id="no backward block, the path stage.dcsn.builder.bwd",
        ),
        pytest.param(
            "stage_without_backward_blocks",
            "backward",
            lambda stage: stage.arvl.builder.bwd,
            id="no backward block, the path stage.arvl.builder.bwd",
        ),
        pytest.param(
            "stage_without_backward_blocks",
            "backward",
            lambda stage: stage.dcsn.builder.policy,
            id="no backward block, the path stage.dcsn.builder.policy",
        ),
        pytest.param(
            "stage_without_forward_blocks",
            "forward",
            lambda stage: stage.builder["arvl", "dcsn"],
            id="no forward block, the pair arvl → dcsn",
        ),
        pytest.param(
            "stage_without_forward_blocks",
            "forward",
            lambda stage: stage.builder["dcsn", "cntn"],
            id="no forward block, the pair dcsn → cntn",
        ),
        pytest.param(
            "stage_without_forward_blocks",
            "forward",
            lambda stage: stage.arvl.builder.fwd,
            id="no forward block, the path stage.arvl.builder.fwd",
        ),
        pytest.param(
            "stage_without_forward_blocks",
            "forward",
            lambda stage: stage.dcsn.builder.fwd,
            id="no forward block, the path stage.dcsn.builder.fwd",
        ),
    ],
)
def test_a_read_of_a_builder_of_a_refused_direction_raises_the_refusal_of_that_direction(
    stage_name, refused, read, request
):
    """Where the construction refuses the builders graph of one direction and
    constructs that of the other, each pair, key and perch path of the
    refused direction raises the refusal `NotConstructed`, which names that
    direction."""
    stage = request.getfixturevalue(stage_name)
    refused_word, other_word = GRAPH_WORDS[refused]
    with pytest.raises(NotConstructed):
        getattr(stage.builder, refused_word).graph
    # the graph of the other direction is constructed, so it raises no refusal
    getattr(stage.builder, other_word).graph
    with pytest.raises(NotConstructed) as refusal:
        read(stage)
    assert f"no {refused} builder" in str(refusal.value)


def test_a_stage_whose_backward_builders_graph_is_refused_reads_its_forward_builders(
    stage_without_backward_blocks,
):
    """Where the construction refuses the backward builders graph, the pairs
    and the perch path of the forward direction read the forward builders."""
    stage = stage_without_backward_blocks
    with pytest.raises(NotConstructed):
        stage.builder.bwd.graph
    assert stage.builder["arvl", "dcsn"].box.name == "arvl_to_dcsn"
    assert stage.builder["dcsn", "cntn"].box.name == "dcsn_to_cntn"
    assert stage.dcsn.builder.fwd.box is stage.builder["dcsn", "cntn"].box


def test_a_stage_whose_forward_builders_graph_is_refused_reads_its_backward_builders(
    stage_without_forward_blocks,
):
    """Where the construction refuses the forward builders graph, the perch
    paths of the backward direction read the backward builders."""
    stage = stage_without_forward_blocks
    with pytest.raises(NotConstructed):
        stage.builder.fwd.graph
    assert stage.dcsn.builder.bwd.box is stage.builder["cntn", "dcsn"].box
    assert stage.arvl.builder.bwd.box.name == "dcsn_to_arvl"


@pytest.mark.parametrize(
    ("stage_name", "refused", "blocks", "pairs"),
    [
        pytest.param(
            "stage_without_backward_blocks",
            "backward",
            ["arvl_to_dcsn", "dcsn_to_cntn"],
            [("arvl", "dcsn"), ("dcsn", "cntn")],
            id="no backward block",
        ),
        pytest.param(
            "stage_without_forward_blocks",
            "forward",
            ["cntn_to_dcsn", "dcsn_to_arvl"],
            [("cntn", "dcsn"), ("dcsn", "arvl")],
            id="no forward block",
        ),
    ],
)
def test_the_listing_and_the_keys_of_a_stage_with_a_refused_direction_are_those_of_the_other(
    stage_name, refused, blocks, pairs, request
):
    """Where the construction refuses the builders graph of one direction, the
    listing and the keys of the builders hold the builders of the other
    direction alone."""
    stage = request.getfixturevalue(stage_name)
    with pytest.raises(NotConstructed):
        getattr(stage.builder, GRAPH_WORDS[refused][0]).graph
    assert list(stage.builder.list()) == blocks
    assert list(stage.builder) == pairs and len(stage.builder) == 2


@pytest.mark.parametrize(
    ("text", "refused", "addition", "methods"),
    [
        pytest.param(
            FORWARD_ONLY_STAGE,
            "backward",
            {
                "text": "@methods: forward_only\narvl_to_dcsn.method : !deterministic\n",
                "origin": "forward_only.methods.bl",
            },
            {"arvl_to_dcsn": "!deterministic"},
            id="no backward block",
        ),
        pytest.param(
            FORWARD_REFUSED,
            "forward",
            {
                "text": "@methods: backward_only\ncntn_to_dcsn.evaluate.method : !Linear\n",
                "origin": "backward_only.methods.bl",
            },
            {"cntn_to_dcsn.evaluate": "!Linear"},
            id="no forward block",
        ),
    ],
)
def test_the_methods_of_a_stage_with_a_refused_direction_are_those_bound_within_the_other(
    text, refused, addition, methods
):
    """Where the construction refuses the builders graph of one direction, the
    methods of the builders are the methods that a methods file binds within
    the builders of the other direction."""
    # the stage is built here, since a methodization binds the stage that it
    # is called on
    stage = stage_from_text(text)
    with pytest.raises(NotConstructed):
        getattr(stage.builder, GRAPH_WORDS[refused][0]).graph
    bound = stage.methodize(addition)
    assert {place: str(held) for place, held in bound.builder.methods.items()} == methods


@pytest.mark.parametrize(("perch", "word"), list(PERCH_PATHS), ids=PERCH_PATH_IDS)
@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_a_perch_path_reads_the_builder_of_its_pair_or_is_refused_with_it(
    src, perch, word, read_only_stage_from_file
):
    """On each stage file that elaborates, a perch path reads the builder that
    the pair defining it reads where that pair is a key of the builders, and
    the path and the pair are both refused where it is not."""
    stage = read_only_stage_from_file(src)
    pair = PERCH_PATHS[perch, word]
    keys = list(stage.builder)
    # the stage has a key of some perch path, so that the rows of each stage
    # file read at least one builder
    assert [key for key in keys if key in PERCH_PATHS.values()] != []
    if pair in keys:
        assert getattr(getattr(stage, perch).builder, word).box is stage.builder[pair].box
    else:
        with pytest.raises((AttributeError, NotConstructed)):
            getattr(getattr(stage, perch).builder, word)
        with pytest.raises((KeyError, NotConstructed)):
            stage.builder[pair]


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_policy_path_reads_the_policy_builder_or_is_refused_with_it(
    src, read_only_stage_from_file
):
    """On each stage file that elaborates, `stage.dcsn.builder.policy` reads
    the builder that `stage.builder.policy` reads where `policy` is a key of
    the builders, and both are refused where it is not."""
    stage = read_only_stage_from_file(src)
    if "policy" in list(stage.builder):
        assert stage.dcsn.builder.policy.box is stage.builder.policy.box
    else:
        with pytest.raises((AttributeError, NotConstructed)):
            stage.builder.policy
        with pytest.raises((AttributeError, NotConstructed)):
            stage.dcsn.builder.policy


@pytest.mark.parametrize(
    ("word", "phrases"),
    [
        pytest.param(
            "bwd",
            ["no value is built at continuation", "next stage's arrival value"],
            id="the backward path",
        ),
        pytest.param("fwd", ["leaves the stage at continuation"], id="the forward path"),
    ],
)
def test_the_continuation_perch_refuses_each_direction_with_its_reason(word, phrases, cons):
    """The continuation perch, which no edge of the stage leaves, refuses the
    backward path and the forward path, each with an `AttributeError` that
    gives its reason."""
    with pytest.raises(AttributeError) as refusal:
        getattr(cons.cntn.builder, word)
    assert [phrase for phrase in phrases if phrase not in str(refusal.value)] == []


@pytest.mark.parametrize(
    "perch",
    ["dcsn", "arvl", "cntn"],
    ids=["decision, which reads the policy builder", "arrival", "continuation"],
)
def test_the_policy_path_reads_the_policy_builder_at_decision_and_is_refused_at_the_other_perches(
    perch, cons
):
    """The path `policy` of the decision perch reads the policy builder, and
    the arrival perch and the continuation perch refuse it with an
    `AttributeError` that says that the policy builder stands at the decision
    perch."""
    if perch == "dcsn":
        assert cons.dcsn.builder.policy.box.name == "policy"
    else:
        with pytest.raises(AttributeError) as refusal:
            getattr(cons, perch).builder.policy
        assert "the policy builder stands at the decision perch" in str(refusal.value)


@pytest.mark.parametrize(
    ("perch_builders", "paths"),
    [
        pytest.param(
            lambda stage: stage.arvl.builder,
            [("stage.arvl.builder.fwd", "arvl → dcsn"), ("stage.arvl.builder.bwd", "dcsn → arvl")],
            id="arrival",
        ),
        pytest.param(
            lambda stage: stage.dcsn.builder,
            [
                ("stage.dcsn.builder.fwd", "dcsn → cntn"),
                ("stage.dcsn.builder.bwd", "cntn → dcsn"),
                ("stage.dcsn.builder.policy", "policy"),
            ],
            id="decision",
        ),
        pytest.param(
            lambda stage: stage.cntn.builder, [], id="continuation, which no edge leaves"
        ),
        pytest.param(
            lambda stage: PerchBuilders(stage, "somewhere"), [], id="a word that names no perch"
        ),
    ],
)
def test_the_listing_of_the_paths_of_a_perch_names_each_path_with_the_key_that_it_reads(
    perch_builders, paths, cons
):
    """The listing of the paths of a perch is a printed record keyed by each
    path, in order, with the key of `stage.builder` that the path reads; it is
    empty at continuation and at a word that names no perch."""
    listed = perch_builders(cons).list()
    assert isinstance(listed, NamedListing)
    assert list(listed.items()) == paths


def test_the_printed_listing_of_the_paths_of_a_perch_writes_a_line_for_each_path_or_none(cons):
    """The printed listing of the paths of the decision perch writes one line
    for each of its three paths, with the key that the path reads, and that
    of the continuation perch is `none`."""
    assert str(cons.dcsn.builder.list()).splitlines() == [
        "stage.dcsn.builder.fwd      dcsn → cntn",
        "stage.dcsn.builder.bwd      cntn → dcsn",
        "stage.dcsn.builder.policy   policy",
    ]
    assert str(cons.cntn.builder.list()) == "none"


def test_two_handles_of_one_perch_compare_equal_and_those_of_two_perches_do_not(cons):
    """Two handles of one perch, each made when it is read, compare equal,
    while the handles of two perches do not."""
    assert cons.dcsn == cons.dcsn and cons.dcsn != cons.arvl


def test_the_short_form_of_a_perch_names_the_stage_and_the_perch(cons):
    """The short form of a perch names the stage and the perch."""
    assert repr(cons.dcsn) == "Perch('cons', 'dcsn')"


@pytest.mark.parametrize(
    "word",
    ["fwd", "bwd", "policy"],
    ids=["the forward path", "the backward path", "the policy path"],
)
def test_a_word_that_names_no_perch_refuses_each_path_naming_the_three_perches(word, cons):
    """The builders of a word that names no perch refuse each path with an
    `AttributeError` that names the word and the three perches."""
    nowhere = PerchBuilders(cons, "somewhere")
    with pytest.raises(AttributeError) as refusal:
        getattr(nowhere, word)
    assert str(refusal.value) == "'somewhere' is no perch; the perches are arvl, dcsn, cntn"


def test_a_terminal_stage_refuses_the_forward_builder_from_decision_and_reads_the_one_from_arrival(
    read_only_stage_from_file,
):
    """The bequest stage of the durables application, a terminal stage,
    refuses `stage.dcsn.builder.fwd` and the pair from decision to
    continuation, while `stage.arvl.builder.fwd` reads its forward builder
    from arrival to decision."""
    stage = read_only_stage_from_file(BEQUEST)
    with pytest.raises(AttributeError) as refusal:
        stage.dcsn.builder.fwd
    assert "terminal stage" in str(refusal.value) or "no decision edge" in str(refusal.value)
    with pytest.raises(KeyError, match="no builder joins dcsn → cntn"):
        stage.builder["dcsn", "cntn"]
    assert stage.arvl.builder.fwd.box.name == "arvl_to_dcsn"


def test_the_path_refuses_two_forward_builders_from_decision_naming_both_and_no_terminal_stage():
    """Where two forward builders join decision to continuation,
    `stage.dcsn.builder.fwd` raises an `AttributeError` that names the two
    builders, each by the key of the forward graph that reads it, and that
    does not call the stage terminal."""
    two = stage_from_text(TWO_FORWARD_BLOCKS_FROM_DECISION)
    with pytest.raises(AttributeError) as refusal:
        two.dcsn.builder.fwd
    message = str(refusal.value)
    phrases = [
        "two builders join dcsn → cntn",
        "stage.builder.fwd['first']",
        "stage.builder.fwd['second']",
    ]
    assert [phrase for phrase in phrases if phrase not in message] == []
    assert "terminal" not in message


def test_a_branching_stage_has_one_forward_builder_from_decision_which_its_perch_path_reads(
    read_only_stage_from_file,
):
    """The retirement choice, a branching stage, has one forward builder from
    decision to continuation, which `stage.dcsn.builder.fwd` reads."""
    stage = read_only_stage_from_file(RET_CHOICE)
    listed = [block for block, (pair, _) in stage.builder.list().items() if pair == "dcsn → cntn"]
    assert len(listed) == 1
    assert stage.dcsn.builder.fwd.box is stage.builder["dcsn", "cntn"].box


@pytest.mark.parametrize(
    ("perch", "word", "block"),
    [
        pytest.param("arvl", "fwd", "first", id="stage.arvl.builder.fwd"),
        pytest.param("arvl", "bwd", "fourth", id="stage.arvl.builder.bwd"),
        pytest.param("dcsn", "fwd", "second", id="stage.dcsn.builder.fwd"),
        pytest.param("dcsn", "bwd", "third", id="stage.dcsn.builder.bwd"),
    ],
)
def test_a_builder_is_read_by_the_pair_that_its_header_joins_whatever_its_block_id(
    perch, word, block, stage_with_new_block_ids
):
    """In the consumption stage with new block ids, none of which names a
    perch, a builder is read by the pair of perches that the header of its
    block joins and by the perch path of that pair."""
    # each block id stands once in the stage file, so that its replacement
    # takes effect
    assert [old for old in NEW_BLOCK_IDS if corpus_text("cons").count(f"[id={old},") != 1] == []
    stage = stage_with_new_block_ids
    assert stage.builder[PERCH_PATHS[perch, word]].box.name == block
    assert getattr(getattr(stage, perch).builder, word).box.name == block


def test_the_policy_builder_is_read_by_the_policy_key_whatever_its_block_id(
    stage_with_new_block_ids,
):
    """In the consumption stage with new block ids, the policy builder, whose
    block is `choose`, is read by the attribute `policy` of the builders and
    by the perch path `stage.dcsn.builder.policy`."""
    # each block id stands once in the stage file, so that its replacement
    # takes effect
    assert [old for old in NEW_BLOCK_IDS if corpus_text("cons").count(f"[id={old},") != 1] == []
    stage = stage_with_new_block_ids
    assert stage.builder.policy.box.name == stage.dcsn.builder.policy.box.name == "choose"


def test_the_listing_of_the_builders_names_each_by_the_block_id_that_the_file_writes(
    stage_with_new_block_ids,
):
    """In the consumption stage with new block ids, the listing of the
    builders names each builder by its new id."""
    # each block id stands once in the stage file, so that its replacement
    # takes effect
    assert [old for old in NEW_BLOCK_IDS if corpus_text("cons").count(f"[id={old},") != 1] == []
    listed = stage_with_new_block_ids.builder.list()
    assert list(listed) == ["first", "second", "third", "fourth", "choose"]


def test_the_refusal_of_a_target_that_names_no_piece_names_the_listings_of_the_primitives():
    """The refusal of the example of `target-not-found`, a query by a name
    that names no piece, names the listings of the primitives of the two
    builders graphs under `stage.builder`, and not the path `stage.build`."""
    refusal = refusal_of(EXAMPLES["target-not-found"])
    assert refusal.rule == "target-not-found"
    message = str(refusal)
    assert "stage.builder.bwd.primitives.list() or stage.builder.fwd.primitives.list()" in message
    assert STAGE_BUILD.search(message) is None


def test_the_refusal_of_a_kernel_asked_of_a_line_names_the_listings_of_the_primitives(cons):
    """A kernel asked of a line of a block of the backward initial diagram is
    refused under `kernel-target`, naming the listings of the primitives of
    the two builders graphs under `stage.builder`, and not the path
    `stage.build`."""
    with pytest.raises(ConstructionError) as refusal:
        cons.initial.backward["cntn_to_dcsn"]["cntn_to_dcsn.value"].kernel()
    assert refusal.value.rule == "kernel-target"
    message = str(refusal.value)
    assert "stage.builder.bwd.primitives.list() or stage.builder.fwd.primitives.list()" in message
    assert STAGE_BUILD.search(message) is None


@pytest.mark.parametrize(
    ("ask", "phrase"),
    [
        pytest.param(
            lambda stage: to_drawing("no graph"),
            "stage.builder.bwd.graph",
            id="a drawing of an object that is no graph",
        ),
        pytest.param(
            lambda stage: stage.initial.backward["cntn_to_dcsn"].kernels(),
            "stage.builder.bwd or stage.builder.fwd answers kernels()",
            id="the kernels of a block of an initial diagram",
        ),
    ],
)
def test_a_verb_asked_of_an_object_that_does_not_answer_it_is_refused_naming_the_builders_graph(
    ask, phrase, cons
):
    """A drawing asked of an object that is no graph, and the kernels asked
    of a block, are refused with a `TypeError` that names the builders graph
    under `stage.builder` that answers them, and not the path
    `stage.build`."""
    with pytest.raises(TypeError) as refusal:
        ask(cons)
    assert phrase in str(refusal.value)
    assert STAGE_BUILD.search(str(refusal.value)) is None


def test_the_section_builder_of_the_stage_listing_is_the_listing_of_the_builders(cons):
    """The section `builder` of the listing of the consumption stage is the
    listing of its builders: the ids of the blocks, each with its pair and its
    direction word."""
    section = cons.list()["builder"]
    assert list(section) == [
        "arvl_to_dcsn",
        "dcsn_to_cntn",
        "cntn_to_dcsn",
        "dcsn_to_arvl",
        "policy",
    ]
    # the section is the listing that `stage.builder.list()` answers
    assert section == cons.builder.list() and list(section) == list(cons.builder.list())
    assert section["cntn_to_dcsn"] == ("cntn → dcsn", "bwd")
    assert section["policy"] == ("policy", "bwd")


def test_the_printed_stage_listing_writes_a_builder_with_its_pair_and_direction_word(cons):
    """The printed listing of the consumption stage writes the backward
    builder from continuation to decision with its pair and its direction
    word."""
    assert "  cntn_to_dcsn   cntn → dcsn, bwd" in str(cons.list()).splitlines()


def test_the_primitive_operations_of_the_decision_builder_are_pullback_aggregation_and_evaluation(
    cons,
):
    """`operators_of` lists the primitive operations of the backward builder
    from continuation to decision of the consumption stage as one pullback,
    one aggregation and one evaluation, which acts on the value bundle and
    not once for each of its components."""
    assert [box.name for box in operators_of(cons) if block_id_of(box) == "cntn_to_dcsn"] == [
        "cntn_to_dcsn:Pullback",
        "cntn_to_dcsn:Aggregation",
        "cntn_to_dcsn:Evaluation",
    ]


def test_operators_of_reads_the_direction_backward_or_forward_and_refuses_any_other(cons):
    """`operators_of` with no direction lists the operations of the backward
    graph and then those of the forward graph, each of which it lists for the
    direction `backward` or `forward`, and it refuses any other direction."""
    assert operators_of(cons) == operators_of(cons, "backward") + operators_of(cons, "forward")
    with pytest.raises(ValueError, match="no direction, 'backward' or 'forward'"):
        operators_of(cons, "initial")


def test_operators_of_a_stage_whose_forward_graph_is_refused_lists_the_backward_operations_alone():
    """For a stage whose forward builders graph the construction refuses,
    `operators_of` raises that refusal for the direction `forward`, and with
    no direction lists the operations of the backward graph alone."""
    opaque = stage_from_text(UNADMITTED_FAMILY_AT_ARRIVAL)
    with pytest.raises(NotConstructed):
        operators_of(opaque, "forward")
    assert operators_of(opaque) == operators_of(opaque, "backward")
