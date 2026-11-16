"""Joint choices of several controls: the one set of joint policies that the
outputs of a joint choice carry, the correspondences and binders it reads, the
order of its outputs whatever its spelling, a product control, and the joint
choice of the durables adjuster."""

import functools

import pytest
from stage_builders import stage_from_text
from stage_texts import JOINT_CHOICE

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.stage.kernels import compile_kernel, kernel
from bellman.syntax.terms import In, Operator, Var
from bellman.typing.typed_expressions import alpha_equivalent, format_expression

# the joint choice stage with its product control `u` written as two controls
# `c` and `l`, the second weighted by 4 in the objective
TWO_CONTROLS = (
    JOINT_CHOICE.replace("u : ℝ × ℝ @ !ctrl", "c : ℝ @ !ctrl, l : ℝ @ !ctrl")
    .replace("u[1]", "c")
    .replace("u[2]", "l")
    .replace(", u)", ", c, l)")
    .replace("u = argmax_{u}", "(c,l) = argmax_{c,l}")
    .replace("-c^2-l^2", "-c^2-4*l^2")
)


# the two controls with a correspondence declared for each
TWO_CORRESPONDENCES = TWO_CONTROLS.replace(
    "@stage: joint_choice", "@stage: joint_choice\nΓ(x : ℝ) := (0,1]\nΛ(x : ℝ) := (0,2]"
)


# the joint choice of the two controls with four binders: no set; a set on
# the second control alone; a set on each control, under letters of its own;
# and a set on the second control alone where a second correspondence is
# declared and read by no binder, which must not change the set of joint
# policies
BINDERS_OF_TWO_CONTROLS = {
    "no_set": TWO_CONTROLS,
    "a_set_on_the_second_control": TWO_CONTROLS.replace(
        "@stage: joint_choice", "@stage: joint_choice\nΓ(x : ℝ) := (0,1]"
    ).replace("argmax_{c,l}", "argmax_{c, l : Γ(x_d)}"),
    "a_set_on_each_control_under_other_letters": TWO_CORRESPONDENCES.replace(
        "argmax_{c,l}(-c^2-4*l^2+V[>])", "argmax_{cp : Γ(x_d), lp : Λ(x_d)}(-cp^2-4*lp^2+V[>])"
    ),
    "a_set_on_the_second_control_and_an_unused_correspondence": TWO_CORRESPONDENCES.replace(
        "argmax_{c,l}", "argmax_{c, l : Γ(x_d)}"
    ),
}


@pytest.fixture(scope="module")
def stage_of_binders():
    """`stage_of_binders(name)`: the symbolic stage of the text
    `BINDERS_OF_TWO_CONTROLS[name]`, elaborated once."""
    return functools.cache(
        lambda name: stage_from_text(BINDERS_OF_TWO_CONTROLS[name], f"{name}.bl")
    )


# `UNRESOLVED[…]` is how the package prints an object it does not construct,
# with the reason after the semicolon; `joint relation projection` is the
# reason where it gives one control of a joint choice no set of its own
@pytest.mark.parametrize("name", list(BINDERS_OF_TWO_CONTROLS))
def test_the_two_outputs_of_a_joint_choice_carry_one_set_of_joint_policies(stage_of_binders, name):
    """The policy builder of a joint choice of two controls has two outputs,
    each of the one set of joint policies that the `Argmax` determines and
    neither an unresolved projection of a joint relation."""
    outputs = stage_of_binders(name).builder.policy.signature().outputs
    assert len(outputs) == 2
    assert all("joint relation projection" not in str(wire.mathematical_type) for wire in outputs)
    assert alpha_equivalent(
        outputs[0].mathematical_type.carrier, outputs[1].mathematical_type.carrier
    )


@pytest.mark.parametrize(
    ("name", "symbol", "expression"),
    [
        ("a_set_on_the_second_control", "Γ", "x ↦ (0, 1]"),
        ("a_set_on_each_control_under_other_letters", "Γ", "x ↦ (0, 1]"),
        ("a_set_on_each_control_under_other_letters", "Λ", "x ↦ (0, 2]"),
    ],
    ids=[
        "a_set_on_the_second_control-gamma",
        "a_set_on_each_control_under_other_letters-gamma",
        "a_set_on_each_control_under_other_letters-lambda",
    ],
)
def test_a_correspondence_of_a_joint_choice_is_a_definition_of_the_stage(
    stage_of_binders, name, symbol, expression
):
    """A correspondence that a joint choice reads is a definition of the
    stage, of the type ℝ ⇉ ℝ and with the expression that the file writes."""
    [correspondence] = (
        stage_of_binders(name).definitions.denote(f"joint_choice:correspondence:{symbol}").denoted
    )
    assert str(correspondence.mathematical_type) == "ℝ ⇉ ℝ"
    assert str(correspondence.expression) == expression


@pytest.mark.parametrize(
    "name",
    ["a_set_on_the_second_control", "a_set_on_the_second_control_and_an_unused_correspondence"],
)
def test_the_choice_records_which_control_of_a_joint_choice_reads_the_set(stage_of_binders, name):
    """Where one control of a joint choice has a set, the right side of the
    choice binds the first control alone and the second in the set
    `Γ(x_d)`."""
    choice = stage_of_binders(name).definitions["policy.choice"].equations[0].rhs
    assert isinstance(choice, Operator) and choice.head == "argmax"
    assert isinstance(choice.subs[0], Var) and choice.subs[0].name == "c"
    assert isinstance(choice.subs[1], In) and choice.subs[1].var == "l"
    assert format_expression(choice.subs[1].set, width=None) == "Γ(x_d)"


def test_each_control_of_a_joint_choice_reads_the_set_in_its_own_position(stage_of_binders):
    """Where each control of a joint choice has a set, the set in a control's
    position of the subscript is that control's, whatever letter the
    subscript names."""
    stage = stage_of_binders("a_set_on_each_control_under_other_letters")
    choice = stage.definitions["policy.choice"].equations[0].rhs
    assert isinstance(choice, Operator) and choice.head == "argmax"
    assert [
        (sub.var, format_expression(sub.set, width=None))
        for sub in choice.subs
        if isinstance(sub, In)
    ] == [("cp", "Γ(x_d)"), ("lp", "Λ(x_d)")]


@pytest.mark.parametrize(
    ("direction", "block"), [("backward", "cntn_to_dcsn"), ("forward", "dcsn_to_cntn")]
)
def test_the_controls_of_a_joint_choice_are_coordinates_and_not_wires(
    stage_of_binders, direction, block
):
    """Both controls of a joint choice are the coordinates at which a block
    of an initial diagram is read, and neither is a wire of the block."""
    piece = getattr(stage_of_binders("no_set").initial, direction)[block]
    assert [(item.symbol, str(item.mathematical_type)) for item in piece.denote().coordinate] == [
        ("c", "ℝ"),
        ("l", "ℝ"),
    ]
    inputs = [identity for identity, _ in piece.signature().inputs]
    assert "joint_choice:dcsn:c" not in inputs and "joint_choice:dcsn:l" not in inputs


# four spellings of the joint choice of two controls: two declared controls,
# the two controls declared as one tuple `(c,l)` in the product `ℝ × ℝ`, the
# choice line marked `!node`, and other letters in the subscript
SPELLINGS = {
    "two_declared_controls": TWO_CONTROLS,
    "a_tuple_of_the_two_controls": TWO_CONTROLS.replace(
        "c : ℝ @ !ctrl, l : ℝ @ !ctrl", "(c,l) : !ctrl @ ℝ × ℝ"
    ),
    "a_node": TWO_CONTROLS.replace("id=choice", "id=choice, !node"),
    "other_letters": TWO_CONTROLS.replace(
        "argmax_{c,l}(-c^2-4*l^2+V[>])", "argmax_{cp,lp}(-cp^2-4*lp^2+V[>])"
    ),
}


@pytest.fixture(scope="module")
def stage_of_spelling():
    """`stage_of_spelling(name)`: the stage of the text `SPELLINGS[name]`
    with an empty calibration bound, elaborated once."""
    return functools.cache(lambda name: stage_from_text(SPELLINGS[name]).calibrate({}))


@pytest.mark.parametrize("name", list(SPELLINGS))
def test_a_joint_choice_writes_its_outputs_in_the_order_of_its_left_side(stage_of_spelling, name):
    """Each spelling of the joint choice of `c` and `l` gives the evaluation
    of the policy builder the outputs `𝑐(x_d)` and `𝑙(x_d)`, in the order of
    the left side."""
    evaluation = stage_of_spelling(name).builder.bwd.primitives["policy:Evaluation"].denote()
    assert tuple(output.identity.field for output in evaluation.outputs) == ("c", "l")
    assert tuple(output.name for output in evaluation.outputs) == ("𝑐(x_d)", "𝑙(x_d)")


@pytest.mark.parametrize("name", list(SPELLINGS))
def test_the_objective_of_a_joint_choice_does_not_depend_on_its_spelling(stage_of_spelling, name):
    """The kernel of the objective of each spelling of the joint choice gives
    the same value at one point."""
    objective = compile_kernel(stage_of_spelling(name), "policy.choice:Aggregation")
    # the kernel's arguments in order: the value 𝑉≻ = 10, the state x_d = 8
    # and the controls c = 1 and l = 2, so that −c² − 4·l² + 𝑉≻ = −7
    assert float(objective(10, 8, 1, 2)) == -7


@pytest.mark.parametrize("name", list(SPELLINGS))
def test_the_image_of_the_argmax_of_a_joint_choice_is_unresolved(stage_of_spelling, name):
    """The image of the `Argmax` of each spelling of the joint choice prints
    as `UNRESOLVED[…]`, since the package constructs no set of maximizing
    pairs of a joint choice."""
    # the spelling that marks the line `!node` puts the Argmax inside a
    # sub-builder; at the primitive grain its key is the same
    argmax = stage_of_spelling(name).builder.bwd.primitives["policy.choice:Argmax"]
    candidates = argmax.denote().image
    assert "UNRESOLVED" in str(candidates)


@pytest.mark.parametrize("grain", ["builders", "sub_builders", "primitives"])
@pytest.mark.parametrize("name", list(SPELLINGS))
def test_every_grain_of_the_backward_graph_of_a_joint_choice_is_constructed(
    stage_of_spelling, name, grain
):
    """The backward builders graph of each spelling of the joint choice
    constructs its graph at each grain, and the test fails where that
    construction raises."""
    backward = stage_of_spelling(name).builder.bwd
    handle = backward if grain == "builders" else getattr(backward, grain)
    # reading the attribute `graph` constructs the graph at the grain
    handle.graph


def test_a_subscript_in_another_order_than_the_left_side_is_refused():
    """A joint choice whose subscript names its controls in another order
    than its left side is refused at the choice line."""
    with pytest.raises(ConstructionError, match="different order") as refused:
        stage_from_text(TWO_CONTROLS.replace("argmax_{c,l}", "argmax_{l,c}"))
    assert refused.value.address == "policy.choice"


def test_a_product_control_retains_its_coupled_correspondence():
    """A correspondence that couples the two components of a product control
    keeps the coupling `u[1] + u[2] < x` in its definition."""
    source = JOINT_CHOICE.replace(
        "@stage: joint_choice",
        "@stage: joint_choice\nΓ(x : ℝ) := {u : ℝ × ℝ | u[1]+u[2] < x}",
    ).replace("argmax_{u}", "argmax_{u : Γ(x_d)}")
    stage = stage_from_text(source)
    assert "u[1] + u[2] < x" in str(
        stage.definitions.denote(stage.definitions.list()["correspondence"][0])
    )


def test_the_choice_sets_of_the_adjuster_establish_the_range_of_its_saving(
    adjuster_cons_with_egm_lines,
):
    """The obligation that the law of motion of the durables adjuster maps
    into the declared set of its saving is established from the two declared
    choice sets and an arithmetic inclusion."""
    [condition] = [
        item
        for item in adjuster_cons_with_egm_lines.obligations()
        if item.condition == "range-compatibility"
        and str(item.entries[0]) == "dcsn_to_cntn.savings"
    ]
    assert condition.status == "established"
    assert condition.evidence == (
        "declared choice set for adjuster_cons:dcsn:c: (0, m]",
        "declared choice set for adjuster_cons:dcsn:h_choice: (0, (m − c)/(1 + τ)]",
        "arithmetic range inclusion at dcsn_to_cntn.savings",
    )


def test_the_law_of_motion_of_the_adjuster_leaves_zero_saving_at_the_bound_of_the_housing_choice(
    adjuster_cons_with_egm_lines,
):
    """The compiled law of motion of the calibrated durables adjuster, whose
    one parameter is τ, gives the outputs (0, 3, 2) at the largest housing
    choice that the joint choice set admits, a saving of zero, and a negative
    saving beyond it."""
    tau, resources, consumption, housing = 1.0, 10.0, 4.0, 3.0
    assert 0 < consumption <= resources
    assert 0 < housing <= (resources - consumption) / (1 + tau)
    stage = copy_native(adjuster_cons_with_egm_lines).calibrate(
        {"β": 0.96, "α": 0.5, "γ_c": 2.0, "γ_h": 2.0, "κ": 1.0, "τ": tau}
    )
    law = compile_kernel(stage, "dcsn_to_cntn:Pushforward")
    assert kernel(stage, "dcsn_to_cntn:Pushforward").parameter_values == (tau,)
    # the law's arguments in order: the resources m, the income state z_d = 2,
    # the consumption c, the housing choice h_choice and the parameter τ; its
    # outputs in order: the saving m − c − (1 + τ)·h_choice = 10 − 4 − 2·3 = 0,
    # the housing h_choice = 3 and the income state z_d = 2
    assert tuple(map(float, law(resources, 2.0, consumption, housing, tau))) == (0.0, 3.0, 2.0)
    assert float(law(resources, 2.0, consumption, housing + 1.0, tau)[0]) < 0


def control_outputs(stage):
    """The outputs of the policy builder of `stage` that are controls."""
    return tuple(
        wire for wire in stage.builder.policy.signature().outputs if wire.sort.role == "control"
    )


def test_the_two_controls_of_the_adjuster_are_one_joint_policy(adjuster_cons_with_egm_lines):
    """Each of the two control outputs of the policy builder of the durables
    adjuster lists both controls and is resolved, and the two carry one
    set."""
    controls = control_outputs(adjuster_cons_with_egm_lines)
    assert len(controls) == 2
    for wire in controls:
        assert tuple(identity.field for identity in wire.controls) == ("c", "h_choice")
        assert "UNRESOLVED" not in str(wire.mathematical_type)
    assert alpha_equivalent(
        controls[0].mathematical_type.carrier, controls[1].mathematical_type.carrier
    )


@pytest.mark.parametrize(
    ("name", "control"),
    [("c", True), ("h_choice", True), ("not_a_control", False)],
    ids=["c", "h_choice", "refused-a-name-that-is-no-control"],
)
def test_the_adjusters_joint_policy_has_a_component_at_each_control_and_at_no_other_name(
    adjuster_cons_with_egm_lines, name, control
):
    """The joint policy of the durables adjuster answers at each of its
    controls a component that is resolved and quantifies the other control
    existentially, and raises `KeyError` at a name that is no control."""
    joint = control_outputs(adjuster_cons_with_egm_lines)[0]
    if control:
        projected = joint.component(name)
        assert "UNRESOLVED" not in str(projected) and "∃" in str(projected)
        return
    with pytest.raises(KeyError):
        joint.component(name)
