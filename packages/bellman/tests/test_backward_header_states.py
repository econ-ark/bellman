"""The acceptance file of the brief "a backward block's header lists no state
of its output perch" (AAS's ruling of 12 October 2026; the second layer of the
tests, `packages/bellman/README.md` §8): one test for each of the six items of
the brief's §7.

The rule: a backward block's header lists the value fields it reads and
writes, and the controls at which its lines are read. A state of the perch at
which its output stands is a coordinate of that output and is not listed; a
listed state is refused under `header-coordinate`. A state of its input perch
is refused unless reached through the law of motion; a direct read of one
across an edge that draws no shock is refused under `input-perch-state`
(AAS's decision BH-4). Forward headers are unchanged,
and a value field a backward line reads is still listed under
`signature-complete`.

The six corrected corpus headers and the housing-renting files are carried by
the snapshot guard and the corpus test; item 6 reads the recordings and the
printed stage of `keeper_cons`. The durables keeper and discounting stage are
read as their stage files stood with their arrival blocks, from fixtures,
since several items read a state two perches from the decision perch or at
the arrival perch (decision MB-U26).
"""
from pathlib import Path

import pytest

from bellman.refusals import ConstructionError
from bellman.stage import inventory
from conftest import ROOT, flat
from snapshot.record import recording_path
from snapshot.corpus_cases import KNOWN_UNELABORATABLE

HOUSING_RENTING = ROOT / "applications/housing-renting/declaration/stages"
FIXTURES = Path(__file__).parent / "fixtures" / "spec_0_6"
# the durables keeper and discounting stage written with their arrival blocks,
# as the application's stage files stood before the degenerate arrival blocks
# were removed (decision MB-U26)
KEEPER_CONS = FIXTURES / "keeper_cons_with_arrival.bl"
KEEPER_SAVING = ROOT / "applications/housing-frictions/declaration/stages/keeper_saving/keeper_saving.bl"
WORKER_CONS = ROOT / "applications/retirement-choice/declaration/stages/worker_cons/worker_cons.bl"
DISC = FIXTURES / "disc_with_arrival.bl"
# the header of the value block of `keeper_cons.bl` as the repository holds it
KEEPER_HEADER = "(V[>] : ℝ @ !vlu, c) ->"
# the policy header of `renter_cons.bl` and the value header of `disc.bl`
RENTER_POLICY = "[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn ->"
DISC_HEADER = "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn ->"


def stage_file(path):
    return path.read_text(encoding="utf-8")


def replaced(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def test_item_1_owner_cons_elaborates_and_its_value_builder_carries_no_state(elaborate_text):
    """`owner_cons.bl`, unchanged, elaborates: its value line reads the
    decision state `H_d` as a coordinate of the value it defines, and the
    printed signature of its value builder carries 𝑉≻ in, 𝑉 out and no
    state."""
    path = HOUSING_RENTING / "owner_cons/owner_cons.bl"
    stage = elaborate_text(stage_file(path), path.relative_to(ROOT).as_posix())
    printed = str(stage.builder["cntn", "dcsn"].signature())
    assert flat(printed) == flat(
        "in   𝑉≻ : ℝ₊ × ℝ₊ × ℝ₊₊ → [−∞, ∞)\n"
        "out  𝑉 : ℝ₊₊ × ℝ₊ × ℝ₊₊ → [−∞, ∞)"
    )
    assert not any(state in printed for state in ("H_d", "w_d", "y_d"))


def test_item_2_a_state_listed_on_a_backward_header_is_refused_at_its_own_perch(elaborate_text):
    """`keeper_cons.bl` with `h_d : !dcsn` kept in its value header is
    refused under `header-coordinate`, the message naming `h_d` as a
    coordinate of the output; the same header listing the continuation state
    `h_nxt_kp` is refused under the same rule, the message naming the
    continuation perch and the law of motion, not the output perch."""
    text = stage_file(KEEPER_CONS)
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(text, KEEPER_HEADER, KEEPER_HEADER.replace("c) ->", "c, h_d : !dcsn) ->")),
                       "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("header-coordinate", "cntn_to_dcsn")
    message = refused.value.message
    assert "lists h_d" in message
    assert "h_d is a state of the dcsn perch, the perch at which the block's output stands" in message
    assert "coordinate of the output function" in message
    assert "`(V[>] : ℝ @ !vlu, c) -> (V : ℝ @ !vlu) : !dcsn`" in message

    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(text, KEEPER_HEADER, KEEPER_HEADER.replace("c) ->", "c, h_nxt_kp : !cntn) ->")),
                       "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("header-coordinate", "cntn_to_dcsn")
    message = refused.value.message
    assert "h_nxt_kp is a state of the cntn perch, the perch the block reads its value fields at" in message
    assert "through the forward law of motion" in message
    assert "h_nxt_kp is a state of the dcsn perch" not in message

    output = "(V : ℝ @ !vlu) : !dcsn"
    mixed = replaced(text, output, output.replace(") : !dcsn", ", h_d : ℝ₊₊ @ !state) : !dcsn"))
    mixed = replaced(
        mixed,
        "    V = 𝑢(c, h_d) + β*V[>]                             :: [id=value]",
        "    h_d = 1                                         :: [id=alien]\n"
        "    V = 𝑢(c, h_d) + β*V[>]                             :: [id=value]",
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(mixed, "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("header-coordinate", "cntn_to_dcsn")
    assert "lists h_d on its output side" in refused.value.message
    assert f"Remove the state output, `{KEEPER_HEADER} {output}`" in refused.value.message

    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(mixed, KEEPER_HEADER, "() ->"), "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("header-coordinate", "cntn_to_dcsn")
    assert "lists h_d on its output side" in refused.value.message

    # a policy header whose input side carries no perch word lists the
    # decision state `S_d` of `renter_cons.bl`: refused under the same rule,
    # before the perch word's absence is read, at the perch the block's output
    # stands at
    renter = stage_file(HOUSING_RENTING / "renter_cons/renter_cons.bl")
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(renter, RENTER_POLICY, RENTER_POLICY.replace(") : !cntn ->", ", S_d) ->")),
                       "renter_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("header-coordinate", "policy")
    assert "S_d is a state of the dcsn perch, the perch at which the block's output stands" in refused.value.message

    # the stem `a` of `disc.bl` stands at two perches, `a` at arrival and
    # `a[>]` at continuation: a listing of either is read by its own mark
    disc = stage_file(DISC)
    for listing, perch, reason in (
        ("a[>]", "cntn", "the perch the block reads its value fields at"),
        ("a[<]", "arvl", "a perch the block neither stands at nor reads from"),
    ):
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(replaced(disc, DISC_HEADER, DISC_HEADER.replace(") : !cntn ->", f", {listing}) : !cntn ->")),
                           "disc.bl")
        assert (refused.value.rule, refused.value.address) == ("header-coordinate", "cntn_to_dcsn")
        assert f"{listing} is a state of the {perch} perch, {reason}" in refused.value.message


def test_item_3_a_value_field_read_and_not_listed_is_refused_with_a_correction_of_value_fields_alone(
        elaborate_text):
    """The value block of `keeper_cons.bl` reading the continuation value
    `V[>]` without listing it is refused under `signature-complete`; the
    correction lists `V[>]` and no state, and the rule's sentence for a
    backward block names value fields. (`cons.bl` of portfolio-choice, the brief's example,
    stands refused under `output-defined` by AAS's decision of 12 October
    2026 and is read by no test here.)"""
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(stage_file(KEEPER_CONS), KEEPER_HEADER, "(c) ->"), "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("signature-complete", "cntn_to_dcsn.value")
    message = refused.value.message
    assert "reads V[>]" in message and "the value fields its lines read" in message
    assert "`(c, V[>]) -> (V : ℝ @ !vlu) : !dcsn`" in message
    assert not any(state in message for state in ("w_d", "h_d", "z_d"))


def test_item_4_a_state_of_the_input_perch_read_directly_is_refused(elaborate_text, text_of):
    """A value line that reads the continuation state `m_next` of `port.bl`
    outside the expectation over the shocks Ψ and θ, which the edge from the
    decision perch to the continuation perch draws, is refused under
    `shock-observed` as before. The value line of `keeper_cons.bl` reading
    `h_nxt_kp`, the continuation state of a deterministic edge, is refused
    under `input-perch-state`, the message naming the authored law
    `h_nxt_kp = h_d` and the correction `h_d`. The rule also checks the left
    expression of a relation and each bound after `⟂`, including a relation
    with no named output. A law whose right side uses a forward-block alias
    is quoted without recommending that alias on the backward line. If a
    forward block is absent, the refusal names the missing relation and
    claims no replacement expression. An empty backward input header cannot
    make a direct continuation-state read legal. A policy's own continuation-marked
    candidate remains readable, but a continuation state cannot be made a
    candidate by repeating its name on a policy line. A marked or local
    alien line in a value block cannot avoid the state-read check.
    The arrival value block reading `h_nxt_kp`, two perches away, is refused
    under the same rule with the chain named; and the bare name `a` of
    `disc.bl`, a state at two perches, is refused under `name-in-scope`."""
    value = "V        = E_{Ψ,θ}(V[>])                            :: [id=value]"
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(text_of("port"), value, "V        = E_{Ψ,θ}(V[>]) + m_next                   :: [id=value]"),
                       "port.bl")
    assert (refused.value.rule, refused.value.address) == ("shock-observed", "cntn_to_dcsn.value")
    assert "mentions m_next" in refused.value.message and "E_{Ψ,θ}" in refused.value.message

    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(text_of("port"), value,
                                "V = E_{Ψ,θ}(V[>]) ⟂ m_next >= 0       :: [id=value]"),
                       "port.bl")
    assert (refused.value.rule, refused.value.address) == ("shock-observed", "cntn_to_dcsn.value")

    text = stage_file(KEEPER_CONS)
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(text, "V = 𝑢(c, h_d) + β*V[>]", "V = 𝑢(c, h_nxt_kp) + β*V[>]"),
                       "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "cntn_to_dcsn.value")
    message = refused.value.message
    assert "mentions h_nxt_kp, a state of the cntn perch" in message
    assert "The forward block 'dcsn_to_cntn' defines it" in message
    assert "`h_nxt_kp = h_d`" in message and "Write `h_d` in its place" in message

    value_line = "    V = 𝑢(c, h_d) + β*V[>]                             :: [id=value]"
    for alien in (
        "    V[<] = h_nxt_kp                              :: [id=alien]",
        "    local_a[<] = h_nxt_kp                        :: [id=alien]",
        "    local = h_nxt_kp                             :: [id=alien]",
    ):
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(replaced(text, value_line, alien + "\n" + value_line), "keeper_cons.bl")
        assert (refused.value.rule, refused.value.address) == ("input-perch-state", "cntn_to_dcsn.alien")
        assert "mentions h_nxt_kp, a state of the cntn perch" in refused.value.message

    marked_alias = replaced(
        text,
        value_line,
        "    local[>] = h_nxt_kp                           :: [id=alias]\n"
        "    V    = 𝑢(c, local[>]) + β*V[>]                :: [id=value]",
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(marked_alias, "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "cntn_to_dcsn.alias")
    assert "`h_nxt_kp = h_d`. Write `h_d` in its place" in refused.value.message

    empty_header = replaced(text, KEEPER_HEADER, "() ->")
    empty_header = replaced(
        empty_header,
        "V = 𝑢(c, h_d) + β*V[>]                             :: [id=value]",
        "V = h_nxt_kp                                       :: [id=value]",
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(empty_header, "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "cntn_to_dcsn.value")
    assert "no input perch named in the block's header" in refused.value.message
    assert "`h_nxt_kp = h_d`. Write `h_d` in its place" in refused.value.message

    # the arrival value block reading the continuation state two perches
    # away, through two forward blocks that draw no shock, is refused under
    # the same rule, the message naming the chain and the block that defines
    # the state
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(text, "V[<]    = V                                        :: [id=value]",
                                "V[<]    = V + h_nxt_kp                             :: [id=value]"),
                       "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "dcsn_to_arvl.value")
    message = refused.value.message
    assert "a state of the cntn perch, a perch after the one the block reads its inputs at" in message
    assert "reached through 'arvl_to_dcsn' then 'dcsn_to_cntn'" in message
    assert "The forward block 'dcsn_to_cntn' defines it at keeper_cons.bl:23:5" in message
    assert "`h_nxt_kp = h_d`, whose right side is read in turn through the earlier blocks of the chain" in message

    forward_start = text.index("[id=arvl_to_dcsn")
    forward_end = text.index("[id=dcsn_to_cntn")
    missing_law = text[:forward_start] + text[forward_end:]
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(missing_law,
                                "V[<]    = V                                        :: [id=value]",
                                "V[<]    = V + h_nxt_kp                             :: [id=value]"),
                       "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "dcsn_to_arvl.value")
    assert "no forward block from arvl to dcsn" in refused.value.message
    assert "supplies no arvl-perch expression for h_nxt_kp" in refused.value.message
    assert "Write `h_d`" not in refused.value.message

    saving = stage_file(KEEPER_SAVING)
    euler = "𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ m_d - c >= 0"
    for line in (
        "𝑢_c(c) + y_f_kp = β*D_{y_f_kp}V[>] ⟂ m_d - c >= 0",
        "𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ y_f_kp >= 0",
        "𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ 0 <= c <= y_f_kp",
    ):
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(replaced(saving, euler, line), "keeper_saving.bl")
        assert (refused.value.rule, refused.value.address) == (
            "input-perch-state", "policy.euler_financial"
        )
        assert "`y_f_kp = m_d - c`. Write `m_d - c` in its place" in refused.value.message

    # An inequality has no named output, including when its left expression
    # consists of one state name.
    operative = replaced(saving, ":: [id=optimality, !doc]", ":: [id=optimality]")
    for line in ("y_f_kp >= 0", "y_f_kp + 0 >= 0"):
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(replaced(operative, euler, line), "keeper_saving.bl")
        assert (refused.value.rule, refused.value.address) == (
            "input-perch-state", "policy.euler_financial"
        )

    fake_candidate = replaced(
        saving,
        "    𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ m_d - c >= 0",
        "    y_f_kp[>] = y_f_kp[>]                 :: [id=fake_candidate]\n"
        "    𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ y_f_kp[>] >= 0",
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(fake_candidate, "keeper_saving.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "policy.fake_candidate")
    assert "`y_f_kp = m_d - c`. Write `m_d - c` in its place" in refused.value.message
    # a candidate line names a control or a decision state at the candidate
    # points (rule candidate-coordinate) and is read by a later line (rule
    # candidate-read): the candidate of the control, read by the grid line
    policy_candidate = replaced(
        saving, "    𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ m_d - c >= 0",
        "    c[>] = 𝑢_c(y_f_kp)                           :: [id=candidate]\n"
        "    m_d[>] = y_f_kp + c[>]                       :: [id=grid]\n"
        "    𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ m_d - c >= 0",
    )
    assert elaborate_text(policy_candidate, "keeper_saving.bl").name == "keeper_saving"
    assert elaborate_text(stage_file(WORKER_CONS), "worker_cons.bl").name == "worker_cons"

    alias_law = replaced(text, "h_nxt_kp = h_d", "local_h = h_d\n    h_nxt_kp = local_h")
    alias_read = replaced(alias_law, "V = 𝑢(c, h_d) + β*V[>]", "V = 𝑢(c, h_nxt_kp) + β*V[>]")
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(alias_read, "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "cntn_to_dcsn.value")
    assert "`h_nxt_kp = local_h`" in refused.value.message
    assert "Express it using names in scope at the dcsn perch" in refused.value.message
    assert "Write `local_h`" not in refused.value.message

    # the bare name `a` of `disc.bl` names a state at two perches, so a value
    # line that mentions it is refused under `name-in-scope` with the two
    # marks that choose between them
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(stage_file(DISC), "V  = β*V[>]                     :: [id=value]",
                                "V  = a + β*V[>]                 :: [id=value]"),
                       "disc.bl")
    assert (refused.value.rule, refused.value.address) == ("name-in-scope", "cntn_to_dcsn.value")
    message = refused.value.message
    assert "mentions a, a state the stage places at 2 perches, arvl and cntn" in message
    assert "Write `a[<]` for the arvl state, `a[>]` for the cntn state" in message


def test_item_5_a_forward_line_reading_an_unlisted_state_is_refused_under_signature_complete(elaborate_text):
    """Forward headers are unchanged: the law of motion of `keeper_cons.bl`
    reading `z_d` without listing it is refused under `signature-complete`,
    with the correction listing `z_d`."""
    forward = "(w_d, h_d, z_d, c : ℝ₊₊ @ !ctrl) : !dcsn"
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(replaced(stage_file(KEEPER_CONS), forward, "(w_d, h_d, c : ℝ₊₊ @ !ctrl) : !dcsn"),
                       "keeper_cons.bl")
    assert (refused.value.rule, refused.value.address) == ("signature-complete", "dcsn_to_cntn.income_state")
    message = refused.value.message
    assert "reads z_d" in message and "every field its lines read" in message
    assert "`(w_d, h_d, c : ℝ₊₊ @ !ctrl, z_d) : !dcsn -> " in message


def test_item_6_the_housing_renting_files_elaborate_and_keeper_cons_prints_no_state(elaborate_text):
    """`owner_cons.bl`, `renter_cons.bl` and `tenure_choice.bl` elaborate and
    have their stage encodings recorded; `owner_housing.bl` and
    `renter_housing.bl` stand in the corpus test's table under
    `not-constructed` at their grid constructors; and the printed BLOCKS and
    DIRECTIONS lines of the corrected `keeper_cons.bl` show no state."""
    for name in ("owner_cons", "renter_cons", "tenure_choice"):
        path = HOUSING_RENTING / name / f"{name}.bl"
        assert elaborate_text(stage_file(path), path.relative_to(ROOT).as_posix()).name == name
        assert recording_path(path, ".stage.json").is_file(), name
    for name in ("owner_housing", "renter_housing"):
        path = HOUSING_RENTING / name / f"{name}.bl"
        relative = path.relative_to(ROOT / "applications").as_posix()
        assert KNOWN_UNELABORATABLE[relative] == ("not-constructed", "grid constructor")
        with pytest.raises(ConstructionError) as refused:
            elaborate_text(stage_file(path), relative)
        assert refused.value.rule == "not-constructed" and "grid constructor" in refused.value.message

    keeper = elaborate_text(stage_file(KEEPER_CONS), "keeper_cons.bl")
    assert inventory.directions(keeper, "backward") == (
        "backward   ≺ V≺  ←  ∼ V  ←  ≻ V≻",
        "policy     ∼ c  ←  ≻ V≻",
    )
    blocks = [line for line in str(keeper).splitlines() if line.strip().startswith("← ")]
    assert flat(blocks[0]) == flat("← cntn_to_dcsn   (V≻) : !cntn, at c -> (V) : !dcsn")
    assert not any("h_d" in line for line in blocks)


def test_item_4_an_inequality_whose_left_side_is_a_continuation_state_is_refused(elaborate_text):
    """A backward line written as an inequality is read at the perch of its
    left side only where that side is a continuation-marked policy
    candidate (unit B's decision SB-1); `a[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`,
    whose left side is the continuation state `a`, is read at the decision
    perch and refused under `input-perch-state` (the review of unit B,
    finding 6; decision SA-19)."""
    fixture = Path(__file__).parent / "fixtures" / "spec_0_6" / "cons.bl"
    text = replaced(
        fixture.read_text(encoding="utf-8"),
        "Γ(x : ℝ₊₊) := (0, x]\n",
        "Γ(x : ℝ₊₊) := (0, x]\n𝑑𝑢 := D_{c}(𝑢)\n𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\n",
    )
    text = replaced(
        text,
        "[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {\n"
        "    c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>]) :: [id=optimality]\n}",
        "[id=policy, (V[>]) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
        "    a[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]\n"
        "    m_d[>] = a + a[>]                    :: [id=grid]\n"
        "    c      = a[>]                        :: [id=identification]\n}",
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text, "cons.bl")
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", "policy.InvEuler")
