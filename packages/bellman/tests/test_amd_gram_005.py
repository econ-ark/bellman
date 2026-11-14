"""The acceptance file of AMD-GRAM-005, union and difference of sets and a
declared set on a derived parameter: one test for each acceptance item that
the snapshot does not carry, named `test_item_<n>_<claim>`.

1. A set expression writes a union with `\\/` and a difference with `\\`;
   `∪` and `∖` are second spellings; the product binds before them and the
   arrow after them; the printed form writes `\\/` and `\\`; and the two
   signs are read in the set of a parameter, of a derived parameter and of a
   setting, and refused in every other set.
2. Calibration decides membership in a union and in a difference, and leaves
   it open only where no member decides it.
3. A derived parameter may carry a declared set, `q : (0,1) := e`, and
   calibration holds its value to that set.
4. A membership that reads a derived parameter is decided once the derived
   values are known.
5. The corrections of the amendment's §4 hold, each under its rule and with
   its words: two different perch words in one type; several sets of one
   type with no number in common; the advice of the refusal `field-perch`;
   two equal sets in one type; a declared set that reads a name the stage
   does not declare; a parameter, a setting or a derived parameter that a
   line of a block writes; a declared set that reads a field; a bound of a
   declared set that has no value at the calibration; and an interval of
   numbers or a difference of sets that holds no number.

Item 6, the recordings, is carried by the snapshot: they change only in the
hashes of the grammar files. What the public operations answer for a union
and a difference beside the items is checked in `test_behaviour.py`: the
answers of the set algebra, the encoding of a stage and the printed forms.
The refusal of a parameter that two stages of one period declare in two
unions is checked in `test_refusals.py`.
"""

import math
import tempfile
from pathlib import Path

import pytest
from conftest import (
    PERFECT_FORESIGHT_CALIBRATION,
    ROOT,
    corpus_text,
    joint_normal,
    methodized,
    stage_from_text,
    two_nodes,
)

from bellman.factory.recipe import declared_parameters
from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import TWO_NODES
from bellman.refusals import ConstructionError
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.source import to_source
from bellman.syntax.terms import (
    Comprehension,
    Domain,
    Functions,
    Named,
    Product,
    SetDifference,
    SetUnion,
)

MEMBERSHIP = "calibration-domain-membership"
PERFECT_FORESIGHT = (
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/"
    "perfect_foresight.bl"
)
# a calibration at which q = (βR)^(1/ρ)/R is 1.049, above one
IMPATIENT = {"β": 0.99, "ρ": 2.0, "R": 0.9, "Γ": 0.85}
# the definition of q without a declared set, as the perfect-foresight stage
# file wrote it until 12 November 2026, as a replacement `_perfect_foresight`
# reads; the file now writes `q : (0,1) := (β*R)^(1/ρ)/R`
Q_WITHOUT_A_SET = {"q : ": "q := (β*R)^(1/ρ)/R"}
# what the set of each of the three may name, as the refusal of a field says it
PARAMETER_SET = "a parameter's set names parameters, derived parameters, named sets and numbers"
SETTING_SET = (
    "a setting's set names settings, parameters, derived parameters, named sets and numbers"
)
DERIVED_SET = (
    "a derived parameter's set names parameters, derived parameters, named sets and numbers"
)


def _two_nodes(declaration, interest="R : ℝ₊₊"):
    """The two-node stage, the declaration of β replaced by `declaration`
    and that of R by `interest`."""
    text = TWO_NODES
    for written, changed in (("β : ℝ₊₊\n", declaration + "\n"), ("R : ℝ₊₊\n", interest + "\n")):
        assert text.count(written) == 1
        text = text.replace(written, changed)
    return text


def _lowered(declaration):
    """The set the lowering keeps for the one declaration, read from the
    parsed line with no stage built."""
    term, _ = parse_with_spans(declaration + "\n", "t.bl")
    (domain,) = [c for c in term.items[-1].declaration.classifiers if isinstance(c, Domain)]
    return domain.space


def _open_memberships(stage):
    return [
        item.explanation
        for item in stage.obligations()
        if item.condition == MEMBERSHIP and item.status == "required"
    ]


def _perfect_foresight(replacements):
    """The committed perfect-foresight stage text with each line that begins
    with a key of `replacements` replaced by its value."""
    text = (ROOT / PERFECT_FORESIGHT).read_text(encoding="utf-8")
    for start, line in replacements.items():
        (old,) = [row for row in text.split("\n") if row.startswith(start)]
        text = text.replace(old, line)
    return text


def _refused(read):
    """The refusal that the call `read` raises when it reads a file."""
    with pytest.raises(ConstructionError) as refused:
        read()
    return refused.value


def _refused_calibration(stage, values):
    """The sentence with which `stage` refuses the calibration `values`."""
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate(values)
    return str(refused.value)


def _conditions(stage, condition):
    """The explanations of the conditions of one name that a stage holds."""
    return [item.explanation for item in stage.obligations() if item.condition == condition]


def _statuses(stage, condition):
    """The status of each condition of one name that a stage holds."""
    return [item.status for item in stage.obligations() if item.condition == condition]


def _keyed(declared, declarations=""):
    """The two-node stage with a collection δ on {1, …, 5}, which its law of
    motion reads at the key j, a parameter declared in `declared` after the
    lines `declarations`."""
    text = two_nodes(transition="    a = k_d*δ[j] + z\n")
    return text.replace(
        "β : ℝ₊₊\n", f"β : ℝ₊₊\n{declarations}δ : {{1, …, 5}} → ℝ\nj : {declared}\n"
    )


def test_item_1_a_set_expression_writes_a_union_and_a_difference():
    union = _lowered("β : (0,1) \\/ (1, inf)")
    assert isinstance(union, SetUnion) and to_source(union) == "(0, 1) \\/ (1, inf)"
    # the second spelling, the order written and a repeated member change
    # nothing
    assert _lowered("β : (0,1) ∪ (1, inf)") == union
    assert _lowered("β : (1, inf) \\/ (0,1)") == union
    assert _lowered("β : (0,1) \\/ (1, inf) \\/ (0,1)") == union
    assert to_source(_lowered("β : (0,1) \\/ (0,1)")) == "(0, 1)"
    # nor does the spelling of a number: `2` and `2.0` are one number, so the
    # two intervals are one member and the two unions one term
    assert to_source(_lowered("β : (0, 2) \\/ (0, 2.0)")) == "(0, 2)"
    assert _lowered("β : (0, 2.0) \\/ (0, 2*R)") == _lowered("β : (0, 2) \\/ (0, 2*R)")
    difference = _lowered("β : ℝ₊₊ \\ {1}")
    assert isinstance(difference, SetDifference) and to_source(difference) == "ℝ₊₊ \\ {1}"
    assert _lowered("β : ℝ₊₊ ∖ {1}") == difference
    # the two signs are read from left to right: a difference stands first
    # in a union, and a union first in a difference
    chain = _lowered("β : ℝ \\ {0} \\/ {5}")
    assert isinstance(chain, SetUnion) and to_source(chain) == "ℝ \\ {0} \\/ {5}"
    assert chain.members[0] == _lowered("β : ℝ \\ {0}")
    removed = _lowered("β : (2,3) \\/ (0,1) \\ {5}")
    assert isinstance(removed, SetDifference) and removed.left == _lowered("β : (0,1) \\/ (2,3)")
    assert to_source(removed) == "(0, 1) \\/ (2, 3) \\ {5}"
    # the printed form of each is read back as the same term
    for kept in (union, difference, chain, removed):
        assert _lowered(f"β : {to_source(kept)}") == kept
    # neither is a factor of a product, where no parentheses set it apart
    for kept in (union, difference):
        with pytest.raises(NotImplementedError, match="no spelling as a factor"):
            to_source(Product((kept, Named("ℝ"))))
    # a term that only a saved AST can hold has no printed form: a union or
    # a difference after the first operand, a set of functions as an
    # operand, a union of one member and a union with a union as a member
    for unwritten, words in (
        (SetDifference(Named("ℝ"), union), "a later operand"),
        (SetUnion((Named("ℝ"), difference)), "a later operand"),
        (SetDifference(Functions(Named("ℤ"), Named("ℝ")), Named("ℝ")), "spelling as an operand"),
        (SetUnion((Named("ℝ"),)), "fewer than two members"),
        (SetUnion((union, Named("ℝ"))), "with a SetUnion as a member"),
    ):
        with pytest.raises(NotImplementedError, match=words):
            to_source(unwritten)
    # the arrow binds after the union: a set of functions into a union
    functions = _lowered("β : {1, …, 2} → (0,1) \\/ (1, 2)")
    assert isinstance(functions, Functions) and isinstance(functions.codomain, SetUnion)
    assert to_source(functions) == "{1, …, 2} → (0, 1) \\/ (1, 2)"
    # a union among several sets of one type is the base the intervals bound
    kept = _lowered("β : (0,1) \\/ (1, inf) @ (0, R)")
    assert isinstance(kept, Comprehension) and kept.base == union
    assert [to_source(c) for c in kept.conds] == ["β > 0", "β < R"]
    assert _lowered(f"β : {to_source(kept)}") == kept
    # an open infinite endpoint restricts a union one of whose members may
    # hold the infinity, and a difference whose left side may hold it
    restricted = {
        "(0,1) \\/ (1, inf) @ (0, inf)": ["β > 0"],
        "(0,1) \\/ [1, inf] @ (0, inf)": ["β > 0", "β < inf"],
        "ℝ \\ {0} @ (0, inf)": ["β > 0"],
        "ℝ̄ \\ {0} @ (0, inf)": ["β > 0", "β < inf"],
    }
    for written, conditions in restricted.items():
        kept = _lowered(f"β : {written}")
        assert [to_source(c) for c in kept.conds] == conditions, written
        assert _lowered(f"β : {to_source(kept)}") == kept, written
    # at most one of several sets is no interval, as before
    for written in ("(0,1) \\/ (2,3) @ ℝ₊₊", "(0,1) \\/ (2,3) @ (4,5) \\/ (6,7)"):
        with pytest.raises(ConstructionError, match="are no intervals"):
            _lowered(f"β : {written}")
    # the product binds before the two signs, so a product is a member; a
    # member or a side that is no set of numbers is refused where it is
    # written, with the place it stands in and the sets to write
    numbers = (
        "an interval, a reserved set, a list of integers, `{1, 2}`, or a named set of numbers"
    )
    for written, whole, place, part, kind in (
        ("{a, b} \\/ (0, 1)", "union", "member", "{a, b}", "a set of labels"),
        ("ℝ × ℝ \\/ (0, 1)", "union", "member", "ℝ × ℝ", "a product"),
        ("(0, 1) \\ {a, b}", "difference", "right side", "{a, b}", "a set of labels"),
        ("ℝ × ℝ \\ (0, 1)", "difference", "left side", "ℝ × ℝ", "a product"),
    ):
        with pytest.raises(ConstructionError) as refused:
            _lowered(f"β : {written}")
        sentence = f"the {whole} `{written}` has the {place} `{part}`, which is {kind}; "
        assert refused.value.rule == "syntax" and sentence in refused.value.message, written
        assert "formed among sets of numbers" in refused.value.message, written
        assert refused.value.write.endswith(f"on each side of the sign: {numbers}"), written
    # a list in a union or in a difference holds integers, as every listed
    # set does
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("β : ℝ₊₊ \\ {0.5}"))
    assert refused.value.rule == "readable-form"
    assert "the set {0.5} lists 0.5, which is no integer" in refused.value.message
    # a member or a side that names a set of labels is refused where the
    # stage is typed, the union quoted in the order it is kept in, whether
    # a line reads the parameter, as `W = β*V[>]` reads β, or none does
    labels = "which the file defines as `{low, high}`, a set of labels; "
    for declaration, words in (
        ("β : ℝ₊₊\nw : Xl \\/ (0, 1)", "the union `(0, 1) \\/ Xl` has the member `Xl`, "),
        ("β : Xl \\/ (0, 1)", "the union `(0, 1) \\/ Xl` has the member `Xl`, "),
        ("β : (0, 1) \\ Xl", "the difference `(0, 1) \\ Xl` has the right side `Xl`, "),
        ("β : Xl \\ {1}", "the difference `Xl \\ {1}` has the left side `Xl`, "),
    ):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_two_nodes("Xl := {low, high}\n" + declaration))
        assert refused.value.rule == "readable-form", declaration
        assert words + labels in refused.value.message, declaration
        assert "formed among sets of numbers" in refused.value.message, declaration
        assert refused.value.write.endswith(f"on each side of the sign: {numbers}"), declaration
    # a name inside a member or a side is found: an undeclared name and an
    # undefined set are refused as in any declared set
    for declaration, word in (
        ("β : (0, n) \\/ (2, 3)", "reads the name 'n'"),
        ("β : ℝ₊₊ \\ (0, n)", "reads the name 'n'"),
        ("β : Foo \\/ (2, 3)", "names the set 'Foo'"),
        ("β : ℝ₊₊ \\ Foo", "names the set 'Foo'"),
        ("β : Foo \\ {1}", "names the set 'Foo'"),
    ):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_two_nodes(declaration))
        assert refused.value.rule == "name-in-scope" and word in refused.value.message, declaration
    # each member and each side is typed as a set of its own: an end of an
    # interval and a bound of a range that is a function are refused there
    for declaration, rule, words in (
        ("w : (0, 𝑓) \\/ (2, 3)", "well-typed", "`(0, 𝑓)` reads it as a number"),
        ("w : ℝ₊₊ \\ (0, 𝑓)", "well-typed", "`(0, 𝑓)` reads it as a number"),
        ("w : {1, …, 𝑓} \\/ (5, 6)", "readable-form", "reads 𝑓, which is no number"),
    ):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_two_nodes("β : ℝ₊₊\n𝑓(x : ℝ) := x^2\n" + declaration))
        assert refused.value.rule == rule and words in refused.value.message, declaration
    # a union and a difference are read in the set of a parameter, as above,
    # of a derived parameter and of a setting, each typed with its stage
    both = "β : ℝ₊₊\nR : ℝ₊₊\n"
    assert TWO_NODES.count(both) == 1
    typed = stage_from_text(TWO_NODES.replace(both, both + "q : (0,1) \\/ (2, 3) := β*R\n"))
    assert to_source(typed.par["q"].domain) == "(0, 1) \\/ (2, 3)"
    added = methodized(stage_from_text(TWO_NODES), "tol : (0, 1) \\/ (2, 3)\n")
    assert to_source(added.settings["tol"].domain) == "(0, 1) \\/ (2, 3)"
    # and refused in every other set, where the declaration is read: the
    # sentence begins with what the set is declared for or defined as, and
    # ends with why the set is the set of a field; a block and a line of a
    # block are the address
    side, shock, function = "(k : ℝ) : !arvl", "y : ℝ\n", "Γ(k : ℝ) := [0,1]"
    multiplier, first = "μ[>]   : ℝ₊ ⟂ a >= 0", "β : ℝ₊₊\n"
    cons_obs = corpus_text("cons_obs")
    declared = "is declared in the set `ℝ \\ {0}`"
    refused_positions = {
        "a field on a side of a block": (
            TWO_NODES.replace(side, "(k : ℝ \\ {0}) : !arvl"),
            f"k in block 'arvl_to_dcsn' {declared}",
            None,
            "arvl_to_dcsn",
        ),
        "a name with a role word": (
            TWO_NODES.replace("z : ℝ\n", "z : ℝ \\ {0} @ !shck\n"),
            f"z at the top level {declared}",
            "the word `!shck` belongs to a field",
            None,
        ),
        "a name with a perch word": (
            TWO_NODES.replace(first, first + "w : ℝ \\ {0} @ !dcsn\n"),
            f"w at the top level {declared}",
            "the word `!dcsn` belongs to a field",
            None,
        ),
        "a shock, a name with a law": (
            TWO_NODES.replace(shock, "y : ℝ \\ {0}\n"),
            f"y at the top level {declared}",
            "y has a distribution, which makes it a shock, a field of the stage",
            None,
        ),
        "a field declared at the top level": (
            TWO_NODES.replace(first, first + "k_d : ℝ \\ {0}\n"),
            f"k_d at the top level {declared}",
            "a block header lists k_d, which makes it a field",
            None,
        ),
        "a multiplier": (
            cons_obs.replace(multiplier, "μ[>]   : ℝ \\ {0} ⟂ a >= 0"),
            f"the multiplier μ[>] in block 'policy' {declared}",
            "a multiplier is a field of the continuation perch",
            "policy.slackness",
        ),
        "an argument of a function": (
            TWO_NODES.replace(first, first + "𝑓(x : ℝ \\ {0}) := x^2\n"),
            f"the argument x of the function 𝑓 {declared}",
            "an argument of a function takes the values of fields",
            None,
        ),
        "an argument of a correspondence": (
            TWO_NODES.replace(function, "Γ(k : ℝ \\ {0}) := [0,1]"),
            f"the argument k of the correspondence Γ {declared}",
            "an argument of a correspondence takes the values of fields",
            None,
        ),
        "the value of a named set": (
            TWO_NODES.replace(first, first + "Xq := {1, …, 2} → ℝ \\ {0}\n"),
            "the set Xq is defined as `{1, …, 2} → ℝ \\ {0}`",
            "a named set may type a field",
            None,
        ),
        "the binder of a named set": (
            TWO_NODES.replace(first, first + "H := {i : ℝ \\ {0} | i >= 1}\n"),
            "the set H is defined as `{i : ℝ \\ {0} | i >= 1}`",
            "a named set may type a field",
            None,
        ),
        "the binder of a correspondence": (
            TWO_NODES.replace(function, "Γ(k : ℝ) := {x : ℝ \\ {0} | x <= 1}"),
            "the correspondence Γ is defined as `{x : ℝ \\ {0} | x <= 1}`",
            "a correspondence restricts a control, which is a field",
            None,
        ),
    }
    why = (
        "; a union and a difference are written in the set of a parameter, of a derived "
        "parameter or of a setting alone, since the set of a field is read by the grids and the "
        "connections, which read no union and no difference"
    )
    for position, (text, subject, reason, address) in refused_positions.items():
        assert text not in (TWO_NODES, cons_obs), position
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(text)
        error = refused.value
        assert error.rule == "readable-form", position
        sentence = f"{subject}, which holds a difference{why}"
        assert error.message == sentence + (f", and {reason}" if reason else ""), position
        assert address is None or error.address == address, position
        assert error.write == "Write the left side, `ℝ`, in place of `ℝ \\ {0}`", position
    # the advice names a set to write in place of the union or the
    # difference: its left side, its first set, or one set that holds every
    # member of a union
    one_set = (
        "Write one set that holds every member of `(0, 1) \\/ (2, 3)`, an interval or a listed "
        "set, in "
    )
    for written, kept, held, write in (
        ("(0,1) \\/ (2,3)", "(0, 1) \\/ (2, 3)", "a union", f"{one_set}its place"),
        (
            "(0,1) \\/ (2,3) \\ {5}",
            "(0, 1) \\/ (2, 3) \\ {5}",
            "a union and a difference",
            f"{one_set}place of `(0, 1) \\/ (2, 3) \\ {{5}}`",
        ),
        (
            "ℝ \\ {0} \\ {1}",
            "ℝ \\ {0} \\ {1}",
            "a difference",
            "Write the first set, `ℝ`, in place of `ℝ \\ {0} \\ {1}`",
        ),
    ):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(TWO_NODES.replace(side, f"(k : {written}) : !arvl"))
        error = refused.value
        assert (error.rule, error.address) == ("readable-form", "arvl_to_dcsn"), written
        subject = f"k in block 'arvl_to_dcsn' is declared in the set `{kept}`"
        assert error.message == f"{subject}, which holds {held}{why}", written
        assert error.write == write, written
    # a law names its shocks, and the lowering reads no term from a type
    # inside the parentheses of its subject: a set written there, a
    # difference or any other, is refused where it is written
    joint = joint_normal()
    assert joint.count("(y, z) ~") == 1
    for typed in ("y : ℝ \\ {0}", "y : ℝ₊"):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(joint.replace("(y, z) ~", f"({typed}, z) ~"))
        error = refused.value
        assert error.rule == "syntax", typed
        assert (
            "the distribution is declared for (y, z), and its subject types y inside the "
            "parentheses; a `~` line names its shocks"
        ) in error.message, typed
        assert error.write == (
            "write the names alone, `(y, z) ~ …`, and the type of each shock on a line of its "
            "own, as in `y : ℝ`"
        ), typed
    # a limit the amendment records and this change leaves as it was: after
    # `:=` a set expression that begins a named set's value is read as
    # before, so a union there is no spelling of the language
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(TWO_NODES.replace(first, first + "Xρ := (0,1) \\/ (1, inf)\n"))
    assert refused.value.rule == "syntax"
    # where a set may continue, a refusal of the parser names the two signs
    # among the forms the language admits
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("β : (0,1) (0, R)"))
    assert refused.value.rule == "syntax"
    assert "`×`, `\\/`, `\\`, `:=`" in refused.value.parts.why
    # the conditions a stage records read a union and a difference: a
    # divisor's condition is recorded unless its set excludes zero, and an
    # argument's unless its set lies in the set the function declares; a
    # union and a difference of sets of numbers hold numbers
    recorded = {
        "ℝ": (True, True),
        "ℝ \\ {0}": (False, True),
        "ℝ₊₊ \\ {1}": (False, False),
        "(0,1) \\/ (1, inf)": (False, False),
        "(-1, 0) \\/ (0, 1)": (False, True),
        "(-1, 1) \\/ (2, 3)": (True, True),
        "ℝ \\ {1}": (True, True),
    }
    line = "    W = β*V[>]\n"
    for declared, (divisor, argument) in recorded.items():
        text = two_nodes(transition="    a = k_d/β + z\n")
        assert text.count(line) == 1
        text = text.replace("β : ℝ₊₊\n", f"β : {declared}\n𝑓(x : ℝ₊₊) := x^2\n")
        stage = stage_from_text(text.replace(line, "    W = 𝑓(β)*V[>]\n"))
        assert bool(_conditions(stage, "arithmetic-definedness")) == divisor, declared
        assert bool(_conditions(stage, "function-argument-domain-inclusion")) == argument, declared
        assert _conditions(stage, "numeric-domain-compatibility") == [], declared
    # a key in a union lies in an index set where each member does, and a key
    # in a difference where its left side does; another difference is
    # recorded as an inclusion to establish
    for declared in ("{1, 2} \\/ {5}", "{1, …, 5} \\ {3}"):
        assert _conditions(stage_from_text(_keyed(declared)), "set-inclusion") == [], declared
    for declared in ("{1, …, 9} \\ {6, 7, 8, 9}", "{1, 2} \\/ {7} \\ {7}", "ℕ \\ (5, inf)"):
        (inclusion,) = _conditions(stage_from_text(_keyed(declared)), "set-inclusion")
        assert inclusion.startswith(
            f"The set {declared} of j must lie within the index set {{1, …, 5}} of δ"
        )
    # a union with a member outside the index set is refused, and so is a
    # set of infinitely many numbers: a set that is no index set, and such a
    # set less the members of an index set
    for declared in ("{1, 2} \\/ {7}", "ℝ", "ℝ \\ {0}", "ℕ \\ {9}", "(0, 9) \\ {3}"):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_keyed(declared))
        assert refused.value.rule == "family-selection", declared
        assert (
            f"declared in {declared}, which is not within the index set" in refused.value.message
        ), declared


def test_item_2_calibration_decides_a_union_and_a_difference():
    stage = stage_from_text(_two_nodes("β : (0,1) \\/ (1, inf)"))
    for inside in (0.5, 2.0):
        assert _open_memberships(copy_native(stage).calibrate({"β": inside, "R": 0.9})) == []
    for outside in (1.0, -1.0):
        with pytest.raises(ValueError, match=r"outside the declared set \(0, 1\) \\/ \(1, inf\)"):
            copy_native(stage).calibrate({"β": outside, "R": 0.9})
    stage = stage_from_text(_two_nodes("β : ℝ₊₊ \\ {1}"))
    assert _open_memberships(copy_native(stage).calibrate({"β": 2.0, "R": 0.9})) == []
    for outside in (1.0, -1.0):
        with pytest.raises(ValueError, match=r"outside the declared set ℝ₊₊ \\ \{1\}"):
            copy_native(stage).calibrate({"β": outside, "R": 0.9})
    # one member that holds decides a union; a member that is not decided
    # leaves the membership open only where no other member holds
    stage = stage_from_text(_two_nodes("β : (0,1) \\/ (2, E_{y}(y^2))"))
    assert _open_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    assert _open_memberships(copy_native(stage).calibrate({"β": 1.5, "R": 0.9})) == [
        "The value 1.5 of β must belong to (0, 1) \\/ (2, E_{y}(y^2))."
    ]
    # a side that is not decided leaves a difference open where the other
    # side does not decide it, and the other side decides it where it can
    stage = stage_from_text(_two_nodes("β : (0, 3) \\ (2, E_{y}(y^2))"))
    assert len(_open_memberships(copy_native(stage).calibrate({"β": 1.0, "R": 0.9}))) == 1
    with pytest.raises(ValueError, match=r"outside the declared set \(0, 3\) \\ \(2, E_\{y\}"):
        copy_native(stage).calibrate({"β": 5.0, "R": 0.9})
    # a member that reads another parameter is read at its value
    stage = stage_from_text(_two_nodes("β : (0, R) \\/ (2*R, inf)"))
    assert _open_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    with pytest.raises(ValueError, match="parameter 'β'"):
        copy_native(stage).calibrate({"β": 1.0, "R": 0.9})
    # a union that several sets of one type bound is judged by the union and
    # by each bound, and the sentence names the part the value breaks
    stage = stage_from_text(_two_nodes("β : (0,1) \\/ (1, inf) @ (0, R)"))
    assert _open_memberships(copy_native(stage).calibrate({"β": 0.5, "R": 0.9})) == []
    with pytest.raises(ValueError, match=r"outside the declared set \(0, 1\) \\/ \(1, inf\)"):
        copy_native(stage).calibrate({"β": 1.0, "R": 2.0})
    with pytest.raises(ValueError, match="does not satisfy the condition β < R"):
        copy_native(stage).calibrate({"β": 0.95, "R": 0.9})
    # each entry of a collection whose entries lie in a union is held to it
    keyed = stage_from_text(_two_nodes("β : ℝ₊₊\nδ : {1, …, 2} → (0,1) \\/ (1, 2)"))
    values = {"β": 1.0, "R": 1.0}
    assert _open_memberships(copy_native(keyed).calibrate({**values, "δ": [0.5, 1.5]})) == []
    with pytest.raises(
        ValueError, match=r"the entry at the key 2 1\.0 lies outside \(0, 1\) \\/ \(1, 2\);"
    ):
        copy_native(keyed).calibrate({**values, "δ": [0.5, 1.0]})
    # the value of a derived parameter is held to a union as a parameter's is
    both = "β : ℝ₊₊\nR : ℝ₊₊\n"
    typed = stage_from_text(TWO_NODES.replace(both, both + "q : (0,1) \\/ (2, 3) := β*R\n"))
    for at in ({"β": 0.5, "R": 1.0}, {"β": 0.5, "R": 5.0}):
        assert _open_memberships(copy_native(typed).calibrate(at)) == []
    with pytest.raises(ValueError) as refused:
        copy_native(typed).calibrate({"β": 0.5, "R": 3.0})
    assert "derived parameter 'q'" in str(refused.value)
    assert "lies outside the declared set (0, 1) \\/ (2, 3) at β = 0.5, R = 3.0" in str(
        refused.value
    )
    # and so is the value of a setting, at configuration
    added = methodized(stage_from_text(TWO_NODES), "tol : (0, 1) \\/ (2, 3)\n")
    for inside in (0.5, 2.5):
        copy_native(added).configure({"tol": inside})
    with pytest.raises(ConstructionError) as refused:
        copy_native(added).configure({"tol": 1.5})
    assert refused.value.rule == "setting-outside-set"
    assert "the value 1.5 lies outside the declared set (0, 1) \\/ (2, 3)" in refused.value.message
    # the inclusion of a key's set in the index set of its collection, where
    # the terms leave it open, is decided once the members are known: those
    # of a union are the members of each member, and those of a difference
    # the members of its left side that its right side does not hold
    values = {"β": 0.9, "R": 1.0, "δ": [1, 2, 3, 4, 5], "j": 2}
    ranged = stage_from_text(_keyed("{1, …, J} \\/ {2}", "J : ℕ\n"))
    for stage, at in (
        (ranged, {"J": 4}),
        (stage_from_text(_keyed("{1, …, J} \\ (5, inf)", "J : ℕ\n")), {"J": 9}),
        (stage_from_text(_keyed("{1, …, 9} \\ {6, 7, 8, 9}")), {}),
        (stage_from_text(_keyed("{1, 2} \\/ {7} \\ {7}")), {}),
    ):
        bound = copy_native(stage).calibrate({**values, **at})
        assert _statuses(bound, "set-inclusion") == ["established"], bound.par["j"]
    for stage, at, made_false in (
        (ranged, {"J": 9}, r"J = 9 makes \{1, …, J\} \\/ \{2\} ⊆ \{1, …, 5\} false"),
        (
            stage_from_text(_keyed("{1, …, 9} \\ {6, 7, 8}")),
            {},
            r"\(no parameters\) makes \{1, …, 9\} \\ \{6, 7, 8\} ⊆ \{1, …, 5\} false",
        ),
    ):
        with pytest.raises(ValueError, match=f"calibration {made_false}"):
            copy_native(stage).calibrate({**values, **at})
    # a left side with infinitely many members leaves the inclusion open,
    # and so does a right side with an end that is a parameter
    for declared, declarations, at in (
        ("ℕ \\ (5, inf)", "", {}),
        ("{1, …, 9} \\ (5, K)", "K : ℝ\n", {"K": 20.0}),
    ):
        stage = stage_from_text(_keyed(declared, declarations))
        bound = copy_native(stage).calibrate({**values, **at})
        assert _statuses(bound, "set-inclusion") == ["required"], declared


def test_item_3_a_derived_parameter_may_carry_a_declared_set():
    text = _perfect_foresight(
        {"β : ": "β : (0,1)", "q : ": "q : (0,1) := (β*R)^(1/ρ)/R"}
    )
    stage = stage_from_text(text)
    assert "q" in list(stage.par)
    # `<-` is a second spelling of `:=`, so the two lines are one term
    spellings = [
        parse_with_spans(f"q : (0,1) {sign} (β*R)^(1/ρ)/R\n", "t.bl").term for sign in (":=", "<-")
    ]
    assert spellings[0] == spellings[1]
    # it is no declared parameter, which a calibration would have to supply
    assert declared_parameters(text, "t.bl") == ("β", "ρ", "R", "Γ")
    # the record answers the set, and the table prints it before the
    # definition, in the column of the sets
    assert stage.par["q"].derived and to_source(stage.par["q"].domain) == "(0, 1)"
    assert str(stage.par["q"]) == "q : (0, 1) := (β*R)^(1/ρ)/R, unbound"
    (row,) = [line for line in str(stage.par).split("\n") if line.startswith("q ")]
    assert row.split("  unbound")[0].split(maxsplit=1)[1] == "(0, 1) := (β*R)^(1/ρ)/R"
    # a row of the table holds what the record holds, the set under `domain`
    # and the definition under `definition`, each a term or None
    rows = {row["name"]: row for row in stage.par.list()}
    for name in ("β", "q", "h"):
        record, row = stage.par[name], rows[name]
        assert (row["domain"], row["definition"]) == (record.domain, record.definition)
    assert to_source(rows["q"]["definition"]) == "(β*R)^(1/ρ)/R"
    # a derived parameter whose definition declares no set has none, and its
    # row prints the definition alone
    assert stage.par["h"].domain is None and to_source(stage.par["h"].definition) == "1/(1 - Γ/R)"
    (row,) = [line for line in str(stage.par).split("\n") if line.startswith("h ")]
    assert row.split("  unbound")[0].split(maxsplit=1)[1].strip() == "1/(1 - Γ/R)"
    assert str(stage.par.list()) == str(stage.par) and ":=" not in str(stage.par).split("\n")[0]
    # the stage's sheet, the definition's card and the kernel of a line that
    # reads the derived parameter print its set
    assert "q : (0, 1) := (β*R)^(1/ρ)/R" in stage.view()
    (identity,) = [each for each in stage.definitions if str(each).endswith(":derived:q")]
    assert "q  ∈ (0, 1),  := (β · R)^(1/ρ)/R" in str(stage.definitions.denote(identity))
    read = stage_from_text(
        _perfect_foresight({"q : ": "q : ℝ₊₊ := R/Γ", "    m = ": "    m = q*k + 1"})
    )
    kernel = read.builder["arvl", "dcsn"]["Pushforward"].kernel()
    assert "# derived parameter: q : ℝ₊₊ := R/Γ\n" in kernel.python
    # the set is no argument: a line that differentiates the derived
    # parameter is read as it is where the definition declares no set
    differentiated = [
        str(
            stage_from_text(
                _perfect_foresight({"    V = ": "    V = 𝑢(c) + β*V[>] + D_{c}(q)", **definition})
            )
            .builder["cntn", "dcsn"]
            .denote()
        )
        for definition in (Q_WITHOUT_A_SET, {"q : ": "q : ℝ₊₊ := (β*R)^(1/ρ)/R"})
    ]
    assert differentiated[0] == differentiated[1] and "q(c)" not in differentiated[1]
    bound = copy_native(stage).calibrate(PERFECT_FORESIGHT_CALIBRATION)
    assert bound.par["q"].value == pytest.approx(0.9615384615384615)
    assert _open_memberships(bound) == []
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate(IMPATIENT)
    words = ("derived parameter 'q'", "(β*R)^(1/ρ)/R", "(0, 1)", "β = 0.99", "R = 0.9", "ρ = 2.0")
    assert all(word in str(refused.value) for word in words), str(refused.value)
    # the sentence names the parameters the definition reads, in the order of
    # the file, then the reason and what to write
    assert str(refused.value).endswith(
        "lies outside the declared set (0, 1) at β = 0.99, ρ = 2.0, R = 0.9; a derived "
        "parameter's value lies in the set its definition declares; write values of β, ρ and R "
        "at which q lies in (0, 1)"
    ), str(refused.value)
    # the calibration supplies no value for it, as for every derived parameter
    with pytest.raises(ConstructionError) as refused:
        copy_native(stage).calibrate({**PERFECT_FORESIGHT_CALIBRATION, "q": 0.5})
    assert refused.value.rule == "derived-parameter"
    # AAS's example of 11 November: two free parameters and a condition on
    # their product
    both = "β : ℝ₊₊\nR : ℝ₊₊\n"
    assert TWO_NODES.count(both) == 1
    product = stage_from_text(TWO_NODES.replace(both, both + "q : (1, inf) := β*R\n"))
    assert _open_memberships(copy_native(product).calibrate({"β": 2.0, "R": 3.0})) == []
    with pytest.raises(ValueError, match="derived parameter 'q'"):
        copy_native(product).calibrate({"β": 0.5, "R": 1.0})
    # a set whose bound no calibration decides leaves the membership open
    open_set = stage_from_text(TWO_NODES.replace(both, both + "q : (0, E_{y}(y^2)) := β*R\n"))
    assert _open_memberships(copy_native(open_set).calibrate({"β": 2.0, "R": 3.0})) == [
        "The value 6.0 of q must belong to (0, E_{y}(y^2))."
    ]
    # a set may read another derived parameter: a faulty value is refused at
    # its own definition, in whatever order the file writes the two, and the
    # sentence gives the value the set reads
    chained = stage_from_text(
        TWO_NODES.replace(both, both + "q : (0, h) := 2*β*R\nh : (0, 10) := β*R\n")
    )
    with pytest.raises(ValueError, match="derived parameter 'h'"):
        copy_native(chained).calibrate({"β": 4.0, "R": 3.0})
    with pytest.raises(ValueError) as refused:
        copy_native(chained).calibrate({"β": 1.0, "R": 3.0})
    assert "derived parameter 'q'" in str(refused.value)
    assert (
        "lies outside the declared set (0, h) at β = 1.0, R = 3.0, where h = 3.0 (the derived "
        "parameter h := β*R); "
    ) in str(refused.value), str(refused.value)
    # where the set has conditions, the sentence names the one the value breaks
    conditioned = stage_from_text(
        TWO_NODES.replace(both, both + "h := β/R\nq : (0, 1) @ (0, 1/h) := β*R\n")
    )
    with pytest.raises(ValueError) as refused:
        copy_native(conditioned).calibrate({"β": 1.2, "R": 0.5})
    assert (
        "at β = 1.2, R = 0.5: the value 0.6 does not satisfy the condition q < 1/h of the "
        "declared set at h = 2.4 (the derived parameter h := β/R); "
    ) in str(refused.value), str(refused.value)
    # a fault of a declared value is refused first, at its own parameter:
    # before a derived value outside its set, and before a definition that
    # has no value
    for definition in ("q : (0,1) := β*b", "q := 1/b"):
        ordered = stage_from_text(_two_nodes(f"β : (0,1)\nb : ℝ\n{definition}"))
        with pytest.raises(ValueError, match="parameter 'β'"):
            copy_native(ordered).calibrate({"β": 2.0, "b": 0.0, "R": 1.0})
    # a definition without a set restricts nothing, as before
    constant = stage_from_text(_perfect_foresight({"β : ": "β : (0,1)", "q : ": "q := 1"}))
    assert copy_native(constant).calibrate(IMPATIENT).par["q"].value == 1
    # a methods file declares a set on a derived parameter it defines, which
    # is no setting; the stage defines q without a set, so that the value of
    # κ is the first that lies outside a set
    plain = stage_from_text(_perfect_foresight({"β : ": "β : (0,1)", **Q_WITHOUT_A_SET}))
    added = methodized(plain, "κ : (0,1) := 1 - q\n")
    assert to_source(added.par["κ"].domain) == "(0, 1)" and "κ" not in added.settings
    with pytest.raises(ValueError, match="derived parameter 'κ'"):
        copy_native(added).calibrate(IMPATIENT)
    # and an addition read after the calibration is judged at the values bound
    with pytest.raises(ValueError, match="derived parameter 'κ'"):
        methodized(copy_native(plain).calibrate(IMPATIENT), "κ : (0,1) := 1 - q\n")
    # where q declares a set too, a value of q outside it is refused at q
    with pytest.raises(ValueError, match="derived parameter 'q'"):
        methodized(stage, "κ : (0,1) := 1 - q\n").calibrate(IMPATIENT)
    # calibration judges the set before any setting has a value, so the set
    # of a derived parameter that reads a setting is refused
    with pytest.raises(ConstructionError) as refused:
        methodized(plain, "n : ℝ₊₊\nκ : (0, n) := 1 - q\n")
    assert refused.value.rule == "derived-parameter"
    assert "declares the set `(0, n)`, which reads n, a setting" in refused.value.message
    # the forms that stay refused
    refused_forms = {
        "q : (0,1)\nq := (β*R)^(1/ρ)/R": "one-name-one-meaning",
        "q : (0,1) @ !shck := (β*R)^(1/ρ)/R": "readable-form",
        "q : (0,1) @ !ctrl := (β*R)^(1/ρ)/R": "readable-form",
        "q : (0,1) @ !dcsn := (β*R)^(1/ρ)/R": "readable-form",
        "(q, s) : (0,1) := (β*R)^(1/ρ)/R": "readable-form",
        "q : (0,1) := 2": "readable-form",
        # `inf` is a number word and no name, so these values are numbers too
        "q : (0,1) := inf": "readable-form",
        "q : (0,1) := -inf": "readable-form",
        "q : (0,1) := 2*inf": "readable-form",
        "q : (0,1) := 𝑢": "readable-form",
        "q : (0,1) := 2*m": "derived-parameter",
        # the value is one real number, which lies in no set of labels, no
        # product and no set of functions
        "q : {low, high} := (β*R)^(1/ρ)/R": "derived-parameter",
        "q : Xa × Xm := (β*R)^(1/ρ)/R": "derived-parameter",
        "q : {1, …, 2} → ℝ := (β*R)^(1/ρ)/R": "derived-parameter",
        "q : Foo := (β*R)^(1/ρ)/R": "name-in-scope",
        "q : (0, n) := (β*R)^(1/ρ)/R": "name-in-scope",
        "q : (0, 𝑢) := (β*R)^(1/ρ)/R": "well-typed",
    }
    for lines, rule in refused_forms.items():
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_perfect_foresight({"β : ": "β : (0,1)", "q : ": lines}))
        assert refused.value.rule == rule, lines
    # a value that reads a shock is refused as a field is
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(TWO_NODES.replace(both, both + "q : (0,1) := β*y\n"))
    assert refused.value.rule == "derived-parameter" and "a shock" in refused.value.message
    # two definitions that name each other are refused as a cycle is
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(TWO_NODES.replace(both, both + "q : (0,1) := p\np : (0,1) := q\n"))
    assert refused.value.rule == "definition-order"
    # a value that reads a name and defines no derived parameter is refused
    # with the forms such a definition takes; a number, with the advice to
    # write it in the calibration file
    for value, words in (
        ("sqrt(β)", "defines no derived parameter"),
        ("𝑢", "defines no derived parameter"),
        ("2", "the calibration file supplies its value, `q: 2`"),
    ):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(
                _perfect_foresight({"β : ": "β : (0,1)", "q : ": f"q : (0,1) := {value}"})
            )
        assert refused.value.rule == "readable-form" and words in refused.value.message, value
        assert ("calibration file" in refused.value.message) == (value == "2"), value


def test_item_4_a_membership_that_reads_a_derived_parameter_is_decided():
    # the stage defines q without a set: where the definition declares one,
    # as the stage file does, a value of q outside it is refused at q first
    text = _perfect_foresight({"β : ": "β : (0,1) @ (0, 1/q)", **Q_WITHOUT_A_SET})
    stage = stage_from_text(text)
    assert _open_memberships(copy_native(stage).calibrate(PERFECT_FORESIGHT_CALIBRATION)) == []
    with pytest.raises(ValueError) as refused:
        copy_native(stage).calibrate(IMPATIENT)
    assert "parameter 'β'" in str(refused.value) and "β < 1/q" in str(refused.value)
    # the sentence says that q is a derived parameter, with its definition
    assert "(the derived parameter q := (β*R)^(1/ρ)/R); " in str(refused.value)
    # a membership that no value decides stays open in a stage that defines
    # a derived parameter
    undecided = stage_from_text(_two_nodes("β : ℝ₊₊ @ (0, E_{y}(y^2))\nh := β*R"))
    assert _open_memberships(copy_native(undecided).calibrate({"β": 2.0, "R": 3.0})) == [
        "The value 2.0 of β must belong to ℝ₊₊ @ (0, E_{y}(y^2))."
    ]
    # a setting whose set reads a derived parameter is judged at its value
    bounded = methodized(stage_from_text(_perfect_foresight({})), "tol : (0, 1) @ (0, q)\n")
    bounded.calibrate(PERFECT_FORESIGHT_CALIBRATION)
    copy_native(bounded).configure({"tol": 0.5})
    with pytest.raises(ConstructionError) as refused:
        copy_native(bounded).configure({"tol": 0.97})
    assert refused.value.rule == "setting-outside-set"
    assert "the condition tol < q of the declared set at q = 0.96" in refused.value.message


def test_item_5_the_corrections_hold():
    side = "(k : ℝ) : !arvl"
    assert TWO_NODES.count(side) == 1
    # two different perch words in one type are refused, in either order
    for words in ("!arvl @ !dcsn", "!dcsn @ !arvl"):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(TWO_NODES.replace(side, f"(k : ℝ @ {words}) : !arvl"))
        assert refused.value.rule == "field-perch"
        assert "`!arvl`" in refused.value.message and "`!dcsn`" in refused.value.message
        assert "in place of `k`" not in (refused.value.write or "")
    # the same word twice is read
    stage_from_text(TWO_NODES.replace(side, "(k : ℝ @ !arvl @ !arvl) : !arvl"))
    # a declaration at the top level is refused in the same words
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("β : ℝ₊₊ @ !arvl @ !dcsn"))
    assert refused.value.rule == "field-perch"
    assert "β at the top level carries two perch words" in refused.value.message
    # a perch word that disagrees with the word of its side is called a
    # perch word, and the advice is to remove it
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(TWO_NODES.replace(side, "(k : ℝ @ !dcsn) : !arvl"))
    error = refused.value
    assert (error.rule, error.address) == ("field-perch", "arvl_to_dcsn")
    assert "the perch word `!dcsn` on k" in error.message and "the mark" not in error.message
    assert error.write == "Remove `!dcsn` from the listing of k in block 'arvl_to_dcsn'"
    # two intervals of numbers with no common point are refused where they
    # are written
    for declaration in ("β : (0,1) @ (2,3)", "β : (0,1) @ [1, 2]"):
        with pytest.raises(ConstructionError) as refused:
            _lowered(declaration)
        assert refused.value.rule == "syntax" and "no number in common" in refused.value.message
    assert to_source(_lowered("β : [0,1] @ [1, 2]")) == "[1, 1]"
    # so are several sets whose endpoints written as ratios of two integers
    # leave no number, and the sentence quotes the sets and the two endpoints
    # as the file writes them
    no_number = {
        "(0,1) @ (1/2, 1/3)": ("`(0, 1)` and `(1/2, 1/3)`", "above 1/2 and below 1/3"),
        "(0,1) @ (1/2, 1) @ (0, 1/3)": (
            "`(0, 1)`, `(1/2, 1)` and `(0, 1/3)`",
            "above 1/2 and below 1/3",
        ),
        "ℝ₊₊ @ [1/2, 1/2)": ("`ℝ₊₊` and `[1/2, 1/2)`", "at least 1/2 and below 1/2"),
        # of two spellings of one endpoint, the open one bounds the sets
        "[0, 0.5] @ (1/4, 1/2) @ [1/2, 1]": (
            "`[0, 0.5]`, `(1/4, 1/2)` and `[1/2, 1]`",
            "at least 1/2 and below 1/2",
        ),
        "[0.5, 1] @ (1/2, 3/4) @ [0, 1/2]": (
            "`[0.5, 1]`, `(1/2, 3/4)` and `[0, 1/2]`",
            "above 1/2 and at most 1/2",
        ),
    }
    for written, (carried, between) in no_number.items():
        with pytest.raises(ConstructionError) as refused:
            _lowered(f"β : {written}")
        assert refused.value.rule == "syntax", written
        assert (
            f"the declaration of β carries the sets {carried}, which have no number in common: "
            f"no number is {between}; "
        ) in refused.value.message, written
    # ratios that leave a number are read as before, and so is an endpoint
    # that reads a parameter
    assert to_source(_lowered("β : (0,1) @ (1/4, 1/2)")) == "(0, 1) @ (1/4, 1/2)"
    assert to_source(_lowered("β : (0,1) @ (1/2, R)")) == "(0, 1) @ (1/2, R)"
    # a decimal and a ratio of one value are one number, which the two sets
    # below have in common
    assert to_source(_lowered("β : [0.1, 1] @ [0, 1/10]")) == "[0.1, 1] @ [0.1, 1/10]"
    # two equal sets in one type are one set
    assert to_source(_lowered("β : ℝ₊₊ @ ℝ₊₊")) == "ℝ₊₊"
    assert to_source(_lowered("β : ℝ₊₊ @ (0, R) @ ℝ₊₊")) == "ℝ₊₊ @ (0, R)"
    # equal sets are one set on a declaration of several names as well, and
    # two different sets there are refused as before
    assert to_source(_lowered("(a, b) : ℝ₊₊ @ ℝ₊₊")) == "ℝ₊₊"
    with pytest.raises(ConstructionError, match="declares more than one"):
        _lowered("(a, b) : ℝ₊₊ @ (0,1)")
    # a declared set that reads a name the stage does not declare is refused
    # where it is written
    for declaration in ("β : (0, n)", "β : ℝ₊₊ @ (0, n)", "β : (0, E_{y}(n*y^2))"):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_two_nodes(declaration))
        error = refused.value
        assert (error.rule, error.address) == ("name-in-scope", "2"), declaration
        assert "reads the name 'n', which the stage does not declare" in error.message
        assert error.write.startswith("Write one of the names in scope here: Γ, β, R, y, z")
    # a name declared at the top level that no header lists is a parameter,
    # and a line of a block that writes it is refused
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(_two_nodes("β : ℝ₊₊\nW : ℝ"))
    error = refused.value
    assert (error.rule, error.address) == ("parameter-or-field", "cntn_to_dcsn.1")
    assert "writes W" in error.message and "a parameter is written by no line" in error.message
    # a derived parameter, with or without a declared set, is written by no
    # line either
    for definition in ("W : ℝ₊₊ := β*R", "W := β*R"):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(_two_nodes("β : ℝ₊₊\n" + definition))
        error = refused.value
        assert (error.rule, error.address) == ("parameter-or-field", "cntn_to_dcsn.1")
        assert "a derived parameter is written by no line" in error.message, definition
    # nor is a setting, which a methods file declares
    with pytest.raises(ConstructionError) as refused:
        methodized(stage_from_text(TWO_NODES), "W : ℝ\n")
    error = refused.value
    assert (error.rule, error.address) == ("parameter-or-field", "cntn_to_dcsn.1")
    assert "a setting is written by no line" in error.message

    # the two-node stage as it stands, which the methods files below extend
    plain = stage_from_text(TWO_NODES)
    # the set of a parameter reads no field: a state, a control, a value, a
    # field under arithmetic, a field in a second set of the type and a field
    # under an expectation are refused where the set is written
    fields = {
        "β : (0, k_d)": "the name 'k_d', a field of the stage, in the set `(0, k_d)`",
        "β : (0, c)": "the name 'c', a field of the stage, in the set `(0, c)`",
        "β : (a, 1)": "the name 'a', a field of the stage, in the set `(a, 1)`",
        "β : (0, V)": "the name 'V', a field of the stage, in the set `(0, V)`",
        "β : (0, 2*k_d + 1)": "the name 'k_d', a field of the stage, in the set `(0, 2*k_d + 1)`",
        "β : ℝ₊₊ @ (0, k_d)": "the name 'k_d', a field of the stage, in the set `ℝ₊₊ @ (0, k_d)`",
        "β : (0, E_{y}(k_d*y))": (
            "the name 'k_d', a field of the stage, in the set `(0, E_{y}(k_d*y))`"
        ),
        # an expectation binds a shock, and a state it names is read
        "β : (0, E_{k_d}(k_d^2))": (
            "the name 'k_d', a field of the stage, in the set `(0, E_{k_d}(k_d^2))`"
        ),
        # a field written with a perch mark is a field, also where the stage
        # lists none at that perch
        "β : (0, V[>])": "the field `V[>]` in the set `(0, V[>])`",
        "β : (0, k_d[<])": "the field `k_d[<]` in the set `(0, k_d[<])`",
    }
    for declaration, read in fields.items():
        error = _refused(lambda: stage_from_text(_two_nodes(declaration)))
        assert (error.rule, error.address) == ("readable-form", "2"), declaration
        assert f"the declaration of 'β' reads {read}; {PARAMETER_SET}; " in error.message
        assert error.message.endswith(
            "calibration judges the value of β against that set before any field has a value"
        ), declaration
        assert error.write == (
            "Write the set of 'β' from numbers, parameters, derived parameters and named sets"
        ), declaration
    # a shock is a field too, where no expectation over it binds it
    unbound = (
        "β : (0, y)",
        "β : (0, E_{y}(y*z))",
        # the subscript of a derivative binds no shock
        "β : (0, D_{y}(y^2))",
    )
    for declaration in unbound:
        error = _refused(lambda: stage_from_text(_two_nodes(declaration)))
        shock = "z" if "z" in declaration else "y"
        assert error.rule == "readable-form", declaration
        assert (
            f"reads the name {shock!r}, a shock of the stage, outside an expectation over it, "
            "in the set `"
        ) in error.message, declaration
        assert PARAMETER_SET in error.message, declaration
        assert error.write.endswith(f"or read {shock} inside `E_{{{shock}}}(…)`"), declaration
    # a field that a named set of the declaration reads is refused at the
    # declaration; the named set alone, which a field may be typed by, is read
    stage_from_text(_two_nodes("Xb := [0, k_d]\nβ : ℝ₊₊"))
    error = _refused(lambda: stage_from_text(_two_nodes("Xb := [0, k_d]\nβ : Xb")))
    assert (error.rule, error.address) == ("readable-form", "3")
    assert (
        "the declaration of 'β' reads the name 'k_d', a field of the stage, in the set `Xb`, "
        "which is defined at t.bl:2:1 (term address '2') as `[0, k_d]`; "
    ) in error.message
    assert tuple(error.related[0])[:3] == ("original declaration", "t.bl", 2)
    # the definition is quoted as the file writes it, at the file that holds it
    error = _refused(lambda: stage_from_text(_two_nodes("Xb := {x : ℝ | x < k_d}\nβ : Xb")))
    assert (
        "in the set `Xb`, which is defined at t.bl:2:1 (term address '2') as `{x : ℝ | x < k_d}`; "
    ) in error.message
    error = _refused(lambda: methodized(plain, "Xs := [0, k_d]\ntol : Xs\n"))
    assert (
        "in the set `Xs`, which is defined at addition-1.bl:2:1 (term address '14') as "
        "`[0, k_d]`; "
    ) in error.message
    # an expectation reads the law of each shock it integrates, so a field
    # that the law reads is read by the bound
    laws = "y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\n"
    assert TWO_NODES.count(laws) == 1

    def with_laws(declaration, y, z="N(0,1)"):
        return _two_nodes(declaration).replace(laws, f"y ~ {y}\nz : ℝ\nz ~ {z}\n")

    through = {
        # the law of the shock reads a state
        ("β : (0, E_{y}(y^2))", "N(k_d, 1)", "N(0,1)"): (
            "the name 'k_d', a field of the stage, through the law `N(k_d, 1)` of the shock 'y',"
        ),
        # the law of a second shock that the expectation integrates reads one
        ("β : (0, E_{y, z}(y*z))", "N(z, 1)", "N(k_d, 1)"): (
            "the name 'k_d', a field of the stage, through the law `N(k_d, 1)` of the shock 'z',"
        ),
        # the law reads a shock that no expectation integrates
        ("β : (0, E_{y}(y^2))", "N(z, 1)", "N(0,1)"): (
            "the name 'z', a shock of the stage, outside an expectation over it, through the "
            "law `N(z, 1)` of the shock 'y',"
        ),
    }
    for (declaration, y, z), read in through.items():
        error = _refused(lambda: stage_from_text(with_laws(declaration, y, z)))
        assert error.rule == "readable-form", (declaration, y, z)
        assert (
            f"the declaration of 'β' reads {read} in the set `{declaration[4:]}`; "
            f"{PARAMETER_SET}; "
        ) in error.message, (declaration, y, z)
    # a law that reads parameters, or a shock that the expectation
    # integrates, leaves the bound a number
    for declaration, y in (
        ("β : (0, E_{y}(y^2))", "N(0, R)"),
        ("β : (0, E_{y,z}(y*z))", "N(z, 1)"),
        ("β : (0, E_{z}(E_{y}(y*z)))", "N(z, 1)"),
    ):
        stage_from_text(with_laws(declaration, y))
    # a law that integrates its own shock is read once, and the refusal of
    # the law stands
    error = _refused(lambda: stage_from_text(with_laws("β : (0, E_{y}(y^2))", "N(E_{y}(y), 1)")))
    assert error.rule == "distribution-dependency"
    # a setting's set and a derived parameter's set read no field either
    error = _refused(lambda: methodized(plain, "tol : (0, k_d)\n"))
    assert error.rule == "readable-form"
    assert "the declaration of 'tol' reads the name 'k_d', a field of the stage" in error.message
    assert SETTING_SET in error.message
    error = _refused(lambda: stage_from_text(_two_nodes("β : ℝ₊₊\nq : (0, k_d) := β*R")))
    assert error.rule == "readable-form"
    assert "the declaration of 'q' reads the name 'k_d', a field of the stage" in error.message
    assert DERIVED_SET in error.message
    # a name the stage does not declare is refused under its own rule
    error = _refused(lambda: stage_from_text(_two_nodes("β : (0, zz)")))
    assert (error.rule, error.address) == ("name-in-scope", "2")
    assert "reads the name 'zz', which the stage does not declare" in error.message
    # an expectation over a name without a distribution, a name the stage
    # does not declare or a parameter, is refused as it is on a line
    for name in ("w", "R"):
        error = _refused(lambda: stage_from_text(_two_nodes(f"β : (0, E_{{{name}}}({name}^2))")))
        assert (error.rule, error.address) == ("not-constructed", "2"), name
        assert error.message == f"the expectation over {name!r} needs a declared distribution"
        assert error.write == (
            f"Declare the distribution of {name}, `{name} ~ …`, or write the set without the "
            f"expectation over {name}"
        ), name
    # an argmax and a solve stand in no set, and the refusal that the typing
    # of the set gives stands for them
    for declaration in ("β : (0, argmax_{y}(y))", "β : (0, solve_{y}(y - R))"):
        error = _refused(lambda: stage_from_text(_two_nodes(declaration)))
        assert error.rule == "well-typed", declaration
    # what stays read: a parameter, a derived parameter, a named set, and a
    # shock under an expectation over it, whose value is a number
    for declarations in (
        "β : (0, R)",
        "β : (0, h)\nh := 2*R",
        "Xn := [0, 9]\nβ : Xn",
        "β : (0, E_{y}(y^2))",
        "β : ℝ₊₊ @ (0, E_{y}(y^2))",
        "β : (0, E_{y,z}(y*z))",
        "β : (0, E_{y}(E_{z}(y*z)))",
        "β : ℝ₊₊\nq : (0, E_{y}(y^2)) := β*R",
    ):
        stage_from_text(_two_nodes(declarations))
    # a setting's set reads a setting, a parameter and a derived parameter
    methodized(
        stage_from_text(_two_nodes("β : ℝ₊₊\nh := 2*R")),
        "n : ℝ₊₊\ntol : (0, n) @ (0, R) @ (0, h)\n",
    )

    # a bound whose arithmetic has no value at the values refuses the
    # calibration, with the reason that refuses a derived parameter's
    # definition there: a division by zero
    zero = "the divisor `{}` is 0.0 at {}, and a division by zero has no value; "
    defined = "a declared set is defined at the values only where each of its bounds has a value; "
    divided = stage_from_text(_two_nodes("β : (0, 1/(R-2))"))
    assert _open_memberships(copy_native(divided).calibrate({"β": 0.2, "R": 3.0})) == []
    for two in (2.0, 2):
        assert _refused_calibration(divided, {"β": 0.2, "R": two}) == (
            "stage 'two_nodes', parameter 'β' (address 't.bl:2'): the bound `1/(R - 2)` of the "
            f"declared set (0, 1/(R - 2)) has no value at R = {two!r}: "
            + zero.format("R - 2", f"R = {two!r}")
            + defined
            + "write values at which `1/(R - 2)` has a value, or another bound"
        )
    # a negative base under a fractional power
    rooted = stage_from_text(_two_nodes("β : (0, R^(1/2))", interest="R : ℝ"))
    assert _open_memberships(copy_native(rooted).calibrate({"β": 0.2, "R": 4.0})) == []
    assert (
        "parameter 'β' (address 't.bl:2'): the bound `R^(1/2)` of the declared set "
        "(0, R^(1/2)) has no value at R = -1.0: the power `R^(1/2)` has the base -1.0 and the "
        "exponent 0.5, which is no integer at R = -1.0; a power with a noninteger exponent "
        "requires a positive base; " + defined
    ) in _refused_calibration(rooted, {"β": 0.2, "R": -1.0})
    # a result beyond the floating-point numbers
    beyond = {
        ("β : (0, 10^R)", 400.0): (
            "the power `10^R` at R = 400.0 exceeds the largest finite floating-point number; "
        ),
        ("β : (0, 1/R)", 1e-320): (
            "the value of `1/R` at R = 1e-320 is inf, which is no finite real number; "
        ),
    }
    for (declaration, interest), reason in beyond.items():
        sentence = _refused_calibration(
            stage_from_text(_two_nodes(declaration)), {"β": 0.2, "R": interest}
        )
        assert f"has no value at R = {interest!r}: {reason}{defined}" in sentence, declaration
    # a bound of written numbers alone has no value at any calibration
    assert _refused_calibration(
        stage_from_text(_two_nodes("β : (0, 1/0)")), {"β": 0.2, "R": 2.0}
    ) == (
        "stage 'two_nodes', parameter 'β' (address 't.bl:2'): the bound `1/0` of the declared "
        "set (0, 1/0) has no value: the divisor `0` is 0.0, and a division by zero has no "
        "value; " + defined + "write another bound"
    )
    # a bound calls log and exp as a derived parameter's definition does: it
    # is valued, and refused where the call has no value
    called = stage_from_text(_two_nodes("β : (0, log(R-2))"))
    assert _open_memberships(copy_native(called).calibrate({"β": 0.2, "R": 4.0})) == []
    assert (
        "the bound `log(R - 2)` of the declared set (0, log(R - 2)) has no value at R = 2.0: "
        "the argument `R - 2` of log is 0.0 at R = 2.0, and log is defined at positive numbers "
        "alone; " + defined
    ) in _refused_calibration(called, {"β": 0.2, "R": 2.0})
    closed = stage_from_text(_two_nodes("β : (0, exp(R-1))"))
    assert _open_memberships(copy_native(closed).calibrate({"β": 0.2, "R": 1.0})) == []
    outside = _refused_calibration(closed, {"β": 1.5, "R": 1.0})
    assert "the value 1.5 lies outside the declared set (0, exp(R - 1))" in outside
    # a side of a condition that reads the name the set binds is no bound of
    # the set: where it has no value, the condition stays undecided
    barred = stage_from_text(_two_nodes("Xb := {x : ℝ | log(x) < R}\nβ : Xb"))
    assert _open_memberships(copy_native(barred).calibrate({"β": -1.0, "R": 2.0})) == [
        "The value -1.0 of β must belong to Xb."
    ]
    # the lower endpoint, and the bound that a second set of the type gives
    for declaration, declared in (
        ("β : (1/(R-2), 5)", "(1/(R - 2), 5)"),
        ("β : ℝ₊₊ @ (0, 1/(R-2))", "ℝ₊₊ @ (0, 1/(R - 2))"),
    ):
        sentence = _refused_calibration(
            stage_from_text(_two_nodes(declaration)), {"β": 0.2, "R": 2.0}
        )
        assert (
            f"the bound `1/(R - 2)` of the declared set {declared} has no value at R = 2.0: "
            + zero.format("R - 2", "R = 2.0")
        ) in sentence, declaration
    # a value outside its own set is refused first, at its own parameter
    ordered = stage_from_text(_two_nodes("β : (0, 1/(R-2))", interest="R : (3, inf)"))
    assert "parameter 'R'" in _refused_calibration(ordered, {"β": 0.2, "R": 2.0})
    # a set with a bound without a value is refused at its own parameter,
    # and not at a parameter whose set reads that one
    behind = stage_from_text(_two_nodes("β : (0, 1/(R-2))\nγ : (0, β)"))
    assert _refused_calibration(behind, {"β": 0.2, "γ": 0.5, "R": 2.0}).startswith(
        "stage 'two_nodes', parameter 'β' (address 't.bl:2'): the bound `1/(R - 2)` of"
    )
    # a bound that reads a derived parameter is not decided before the
    # derived values are known, and is judged at them
    chained = stage_from_text(_two_nodes("β : (0, 1/(q-1))\nq := R/2"))
    assert _open_memberships(copy_native(chained).calibrate({"β": 0.2, "R": 4.0})) == []
    assert (
        "parameter 'β' (address 't.bl:2'): the bound `1/(q - 1)` of the declared set "
        "(0, 1/(q - 1)) has no value at q = 1.0 (the derived parameter q := R/2): "
        + zero.format("q - 1", "q = 1.0")
    ) in _refused_calibration(chained, {"β": 0.2, "R": 2.0})
    # the set that a derived parameter's definition declares is judged so too
    typed = stage_from_text(_two_nodes("β : ℝ₊₊\nq : (0, 1/(R-2)) := β*R"))
    assert _open_memberships(copy_native(typed).calibrate({"β": 0.1, "R": 3.0})) == []
    assert (
        "derived parameter 'q' (address 't.bl:3'): the bound `1/(R - 2)` of the declared set "
        "(0, 1/(R - 2)) has no value at R = 2.0: " + zero.format("R - 2", "R = 2.0")
    ) in _refused_calibration(typed, {"β": 0.1, "R": 2.0})
    # a bound that reads an expectation has no number at any calibration,
    # and its membership stays the open requirement
    expected = stage_from_text(_two_nodes("β : (0, E_{y}(y^2))"))
    assert _open_memberships(copy_native(expected).calibrate({"β": 0.2, "R": 2.0})) == [
        "The value 0.2 of β must belong to (0, E_{y}(y^2))."
    ]
    # a bound that is the bare name of a parameter declared on the extended
    # reals and valued at an infinity is read as that infinity, so the
    # membership is decided: 0.2 lies in (0, ∞). Until 12 November 2026 this
    # membership stayed open; AAS ruled on that day that an infinite endpoint
    # has one reading, whatever supplies the value (AMD-GRAM-006)
    extended = stage_from_text(_two_nodes("β : (0, T)\nT : ℝ̄"))
    infinite = copy_native(extended).calibrate({"β": 0.2, "R": 2.0, "T": math.inf})
    assert _open_memberships(infinite) == []
    assert "the value -1.0 lies outside the declared set (0, T)" in _refused_calibration(
        extended, {"β": -1.0, "R": 2.0, "T": math.inf}
    )
    # a setting's set is judged so at configuration, from a mapping and from
    # a settings file
    bounded = methodized(plain, "n : ℝ₊₊\ntol : (0, 1/(n-2))\n")
    copy_native(bounded).configure({"n": 3.0, "tol": 0.5})
    with tempfile.TemporaryDirectory() as folder:
        settings = Path(folder) / "settings.yml"
        settings.write_text("settings:\n  n: 2.0\n  tol: 0.5\n", encoding="utf-8")
        for source in ({"n": 2.0, "tol": 0.5}, settings):
            with pytest.raises(ConstructionError) as refused:
                copy_native(bounded).configure(source)
            error = refused.value
            assert (error.rule, error.address) == ("setting-outside-set", "addition-1.bl:3")
            assert error.message == (
                "stage 'two_nodes', setting 'tol': the bound `1/(n - 2)` of the declared set "
                "(0, 1/(n - 2)) has no value at n = 2.0: "
                + zero.format("n - 2", "n = 2.0")
                + defined
                + "write values at which `1/(n - 2)` has a value, or another bound"
            )
        # the refusal names the key of the setting that the bound reads
        key = ("rejected setting", str(settings), 2, 3, None, None, "n")
        assert tuple(error.related[0]) == key

    # an interval of numbers that holds no number is refused where the file
    # is read, in the set of a parameter, a setting and a derived parameter
    # alike
    above = "has the lower endpoint {} above the upper endpoint {}, so it is empty; "
    equal = (
        "has the lower endpoint {} equal to the upper endpoint {} and an open end, so it is "
        "empty; "
    )
    empty = {
        "(2, 1)": above.format(2, 1),
        "[2, 1]": above.format(2, 1),
        "(1/2, 1/3)": above.format("1/2", "1/3"),
        "(1, -inf)": above.format(1, "-inf"),
        "(1, 1)": equal.format(1, 1),
        "[1, 1)": equal.format(1, 1),
        "(1, 1]": equal.format(1, 1),
    }

    def readings(written):
        """The calls that read a stage in which a parameter, a setting and a
        derived parameter are declared in the set `written`, each under the
        words for what is declared."""
        return {
            "a parameter": lambda: stage_from_text(_two_nodes(f"β : {written}")),
            "a setting": lambda: methodized(plain, f"tol : {written}\n"),
            "a derived parameter": lambda: stage_from_text(
                _two_nodes(f"β : ℝ₊₊\nq : {written} := β*R")
            ),
        }

    for interval, fault in empty.items():
        for what, read in readings(interval).items():
            error = _refused(read)
            assert error.rule == "readable-form", (interval, what)
            assert f"the set {interval} {fault}" in error.message, (interval, what)
            assert "an interval of numbers holds at least one number" in error.message
            assert error.write.startswith("Write the smaller endpoint first"), (interval, what)
    # a decimal and a ratio of two integers that write one number are one
    # endpoint, so the interval between them holds that number where both
    # ends are closed and no number where one is open
    assert stage_from_text(_two_nodes("β : [0.1, 1/10]")).par["β"].domain is not None
    assert stage_from_text(_two_nodes("β : [1/10, 0.1]")).par["β"].domain is not None
    error = _refused(lambda: stage_from_text(_two_nodes("β : (0.1, 1/10]")))
    assert error.rule == "readable-form"
    assert "the set (0.1, 1/10] " + equal.format("0.1", "1/10") in error.message
    # the check stands where every set is typed, so a field's set is held to
    # it, on a header and at the top level, where the refusal stands at the
    # declaration
    shock = "y : ℝ\n"
    assert TWO_NODES.count(shock) == 1
    error = _refused(lambda: stage_from_text(TWO_NODES.replace(side, "(k : (2, 1)) : !arvl")))
    assert error.rule == "readable-form" and "so it is empty" in error.message
    error = _refused(lambda: stage_from_text(TWO_NODES.replace(shock, "y : (2, 1)\n")))
    assert (error.rule, error.address, error.line) == ("readable-form", "4", 4)
    assert "the set (2, 1) has the lower endpoint 2 above the upper endpoint 1" in error.message
    # an interval of one number, closed at both ends, is read in each of the
    # three
    one = stage_from_text(_two_nodes("β : [1, 1]\nq : [2, 2] := β*R"))
    assert _open_memberships(copy_native(one).calibrate({"β": 1.0, "R": 2.0})) == []
    copy_native(methodized(plain, "tol : [1, 1]\n")).configure({"tol": 1.0})
    # an endpoint that reads a parameter is decided at calibration, as before
    late = stage_from_text(_two_nodes("β : (R, 1)"))
    assert "parameter 'β'" in _refused_calibration(late, {"β": 0.5, "R": 2.0})

    # a difference holds no number where its left side lies within its right
    # side, and is refused as an empty interval is, in each of the three
    emptied = {
        "ℝ \\ ℝ": "the set ℝ \\ ℝ has the left side ℝ within the right side ℝ",
        "(0,1) \\ ℝ₊": "the set (0, 1) \\ ℝ₊ has the left side (0, 1) within the right side ℝ₊",
        "{1} \\ {1}": "the set {1} \\ {1} has the left side {1} within the right side {1}",
    }
    for difference, fault in emptied.items():
        for what, read in readings(difference).items():
            error = _refused(read)
            assert error.rule == "readable-form", (difference, what)
            assert error.message == (
                f"{fault}, so it is empty; a difference holds at least one number, so its left "
                "side holds a number that its right side does not hold"
            ), (difference, what)
            assert error.write == (
                "Write a left side that holds a number outside the right side"
            ), (difference, what)
    # the refusal stands at the declaration, and a named set is read as the
    # set that the stage defines
    error = _refused(lambda: stage_from_text(_two_nodes("Xb := [0, 1)\nβ : Xb \\ ℝ₊")))
    assert (error.rule, error.address, error.line) == ("readable-form", "3", 3)
    assert "the set Xb \\ ℝ₊ has the left side Xb within the right side ℝ₊" in error.message
    # a difference whose emptiness the rules of inclusion do not decide is
    # read as before, and so is one that is a member of a union, since
    # another member of the union may hold a number
    for declared in ("ℝ₊ \\ {1}", "(0, R) \\ (0, 1)", "(0,1) \\ ℝ₊ \\/ (2, 3)"):
        stage_from_text(_two_nodes(f"β : {declared}"))
