"""Hand-derived AST expectations for the ten stages of the Cagetti and De
Nardi (2006) example.

Every expected node below is derived from the surface text of the `.bl`
files of the model's stage folders, `declaration/stages/<key>/`, and from
the generated term constructors
(bellman.sym.terms), not copied from their recordings `*.ast.json` under
`packages/bellman/tests/snapshot/corpus/cagetti-denardi-2006/`. Each
file is parsed fresh through the Lark route (stage.lark, then the ToAst
lowering). The tests cover the constructs this example adds to the corpus:
the occupational branches, the repay-or-default branches with the joint
maximisation and the enforcement inequality, the demographic branches keyed
by a shock, and the Markov and invariant laws of the two abilities.
Runnable under pytest or directly:

    venv/bin/python applications/cagetti-denardi-2006/tests/test_cagetti_denardi_ast.py
"""

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "packages" / "bellman" / "tests" / "tools"))

import pytest

from stage_ast import arvl, check, cntn, describes, parsed, run_checks, sym
from stage_types import (
    Add, Annotation, Assignment, At, Block, Call, Closed, Constant,
    Continuation, Control, Coordinate, CorrDef, Decision, Domain, Equation,
    FiniteSet, Ge, In, Inequality, Infoset, Interval, Key, KeyValue, Law,
    Metadata, Mul, Named, Number, Open, Operator, Pow, Range, Role, Select,
    Signature, Space, Statement, Sub, Subject, Tuple, Typer, Value, Var,
)


# the folder of the model's stage folders
STAGE_FOLDERS = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "stages"
STAGES = ("young_choice", "young_entrepreneur", "worker", "worker_ageing",
          "entrepreneur_ageing", "old_choice", "old_entrepreneur", "retiree",
          "entrepreneur_death", "retiree_death")
ITEMS = {name: parsed(STAGE_FOLDERS / name / f"{name}.bl").items for name in STAGES}


def coord(stem, space=None):
    return Coordinate(stem, None, [Domain(Named(space))] if space else [])


def value_coord(stem, perch):
    return Coordinate(stem, At(perch()) if perch else None,
                      [Domain(Named("ℝ")), Role(Value(0))])


def statement(lhs, rhs, ident=None):
    return Statement(Equation(lhs, rhs),
                     Annotation([KeyValue("id", ident)]) if ident else None)


def block(tag_entries, body):
    return Block(Annotation(tag_entries), body)


def test_file_shapes():
    # Metadata, the named sets, the parameters, the function and
    # correspondence definitions, the shock declarations with their laws,
    # and the blocks: four for a stage without a policy block, five with one.
    sets2 = ["Statement"] * 2
    sets3 = ["Statement"] * 3
    sets4 = ["Statement"] * 4
    shocks = ["Declare", "Statement"] * 3
    expected = {
        "young_choice": ["Metadata"] + sets3 + ["Block"] * 5,
        "old_choice": ["Metadata"] + sets2 + ["Block"] * 5,
        "worker": ["Metadata"] + sets4 + ["Declare"] * 4 + ["Statement"] * 2 + ["Block"] * 5,
        "retiree": ["Metadata"] + sets2 + ["Declare"] * 3 + ["Statement"] * 2 + ["Block"] * 5,
        "young_entrepreneur": ["Metadata"] + sets3 + ["Declare"] * 5 + ["Statement"] * 2 + ["Block"] * 5,
        "old_entrepreneur": ["Metadata"] + sets2 + ["Declare"] * 5 + ["Statement"] * 2 + ["Block"] * 5,
        "worker_ageing": ["Metadata"] + sets3 + ["Declare"] * 7 + shocks + ["Block"] * 4,
        "entrepreneur_ageing": ["Metadata"] + sets3 + ["Declare"] * 7 + shocks + ["Block"] * 4,
        "entrepreneur_death": ["Metadata"] + sets3 + ["Declare"] * 8 + shocks + ["Block"] * 4,
        "retiree_death": ["Metadata"] + sets3 + ["Declare"] * 8 + shocks + ["Block"] * 4,
    }
    for name in STAGES:
        kinds = [type(item).__name__ for item in ITEMS[name]]
        assert kinds == expected[name], (name, kinds)


def test_metadata_names_the_stage_as_its_file():
    for name in STAGES:
        check(ITEMS[name][0], Metadata("stage", name), f"{name}.items[0]")


def test_stand_in_sets():
    # `Y := ℝ₊₊` and `Θ := ℝ₊` are space-defining assignments; the sets stand
    # in for the finite grid of working ability and the two ability levels.
    # The description each carries is kept on the assignment's annotation
    # slot (AMD-SG-017 §3).
    check(ITEMS["worker"][3],
          Statement(Assignment(Constant("Y"), Space(Named("ℝ₊₊"))),
                    describes("working ability; the positive reals stand in for its "
                              "finite grid, whose number of points is a numerical choice")),
          "worker.items[3]")
    check(ITEMS["worker"][4],
          Statement(Assignment(Constant("Θ"), Space(Named("ℝ₊"))),
                    describes("entrepreneurial ability; the nonnegative reals stand in "
                              "for its two levels, 0 and θ_e")),
          "worker.items[4]")


def test_young_choice_branching_block():
    # Equation (2): the control d over the ordered labels, an empty output
    # side, and one nested block per occupation copying the decision state.
    def branch(label, names):
        outputs = Subject([coord(names[0], "Xa"), coord(names[1], "Y"), coord(names[2], "Θ")])
        body = [statement(sym(names[0]), sym("a")), statement(sym(names[1]), sym("y")),
                statement(sym(names[2]), sym("θ"))]
        return block([KeyValue("label", label),
                      Typer(Signature(Subject([]), [], outputs, [Infoset(Continuation())]))], body)

    want = block(
        [KeyValue("id", "dcsn_to_cntn"),
         Typer(Signature(
             Subject([coord("a"), coord("y"), coord("θ"),
                      Coordinate("d", None, [Role(Control()),
                                             Domain(FiniteSet(["entrepreneur", "worker"]))])]),
             [Infoset(Decision())], Subject([]), []))],
        [branch("entrepreneur", ("a_ye", "y_ye", "θ_ye")),
         branch("worker", ("a_yc_wk", "y_yc_wk", "θ_yc_wk"))])
    check(ITEMS["young_choice"][5], want, "young_choice.items[5]")


def test_occupational_values_and_choices():
    # V = (V_e[>], V_w[>])[d] and d = argmax_{d}(V_e[>], V_w[>]) in the young
    # choice; the old choice writes W_e and W_r in the same places.
    for name, first, second in (("young_choice", "V_e", "V_w"), ("old_choice", "W_e", "W_r")):
        items = ITEMS[name]
        check(items[-3].body,
              [statement(sym("V"), Select(Tuple([cntn(first), cntn(second)]), Key("d")), "choice_value")],
              f"{name}.cntn_to_dcsn.body")
        check(items[-1].body,
              [statement(sym("d"), Operator("argmax", [Var("d")], [cntn(first), cntn(second)]), "choice")],
              f"{name}.policy.body")


def test_worker_and_retiree_cash_on_hand():
    # Equation (9), m = (1 + r)*a_wk + (1 - τ)*w*y_wk, and equation (14),
    # m = (1 + r)*a_rt + p; both sums associate to the left.
    worker = Add(Mul(Add(Number(1), sym("r")), sym("a_wk")),
                 Mul(Mul(Sub(Number(1), sym("τ")), sym("w")), sym("y_wk")))
    check(ITEMS["worker"][11].body[0], statement(sym("m"), worker, "cash_on_hand"),
          "worker.arvl_to_dcsn.body[0]")
    retiree = Add(Mul(Add(Number(1), sym("r")), sym("a_rt")), sym("p"))
    check(ITEMS["retiree"][8].body[0], statement(sym("m"), retiree, "cash_on_hand"),
          "retiree.arvl_to_dcsn.body[0]")


def test_consumption_maximisation_over_the_feasible_set():
    # Γ(x : ℝ₊₊) := (0, x] and c = argmax_{c : Γ(m)}(𝑢(c) + V[>]).
    for name, at in (("worker", 10), ("retiree", 7)):
        check(ITEMS[name][at],
              Statement(CorrDef("Γ", [coord("x", "ℝ₊₊")],
                                Interval(Range(Open(), Number(0), sym("x"), Closed()))),
                        Annotation([KeyValue("id", "feasible")])),
              f"{name}.items[{at}]")
        objective = Add(Call("𝑢", [sym("c")]), cntn("V"))
        check(ITEMS[name][-1].body,
              [statement(sym("c"), Operator("argmax", [In("c", Call("Γ", [sym("m")]))], [objective]),
                         "choice")],
              f"{name}.policy.body")


def test_entrepreneur_budget_and_default():
    # Equation (4) on the repay branch and the kept capital f*k on the
    # default branch, for the young and the old entrepreneur.
    budget = Sub(Sub(Add(Mul(Sub(Number(1), sym("δ")), sym("k")),
                         Mul(sym("θ"), Pow(sym("k"), sym("ν")))),
                     Mul(Add(Number(1), sym("r")), Sub(sym("k"), sym("a")))),
                 sym("c"))
    for name, repay, default in (("young_entrepreneur", "a_ye_ea", "a_ye_wk"),
                                 ("old_entrepreneur", "a_oe_ed", "a_oe_rt")):
        branches = ITEMS[name][-4].body
        assert [b.tag.entries[0] for b in branches] == [KeyValue("label", "repay"),
                                                        KeyValue("label", "default")]
        check(branches[0].body[0], statement(sym(repay), budget, "budget"), f"{name}.repay.body[0]")
        check(branches[1].body[0], statement(sym(default), Mul(sym("f"), sym("k")), "kept_capital"),
              f"{name}.default.body[0]")


def test_entrepreneur_value_and_policy():
    # The value of the chosen branch, (𝑢(c) + V_repay[>], V_w[>])[d]; the
    # joint maximisation over capital and consumption with a tuple left
    # side; the enforcement constraint (5) or (12) as an inequality
    # statement; and the repayment choice over the same two values.
    for name, outside in (("young_entrepreneur", "V_w"), ("old_entrepreneur", "W_r")):
        items = ITEMS[name]
        honour = Add(Call("𝑢", [sym("c")]), cntn("V_repay"))
        check(items[-3].body, [statement(sym("V"), Select(Tuple([honour, cntn(outside)]), Key("d")), "value")],
              f"{name}.cntn_to_dcsn.body")
        want_signature = Signature(
            Subject([value_coord("V_repay", Continuation), value_coord(outside, Continuation)]),
            [Infoset(Continuation())],
            Subject([Coordinate("k", None, [Domain(Named("ℝ₊")), Role(Control())]),
                     Coordinate("c", None, [Domain(Named("ℝ₊₊")), Role(Control())]),
                     Coordinate("d", None, [Domain(FiniteSet(["repay", "default"])), Role(Control())])]),
            [Infoset(Decision())])
        check(items[-1].tag, Annotation([KeyValue("id", "policy"), Typer(want_signature)]),
              f"{name}.policy.tag")
        joint = Operator("argmax", [Var("k"), In("c", Call("Γ", [sym("a"), sym("θ"), sym("k")]))], [honour])
        check(items[-1].body, [
            statement(Tuple([sym("k"), sym("c")]), joint, "optimality"),
            Statement(Inequality(honour, Ge(), cntn(outside)), Annotation([KeyValue("id", "enforcement")])),
            statement(sym("d"), Operator("argmax", [Var("d")], [honour, cntn(outside)]), "repayment"),
        ], f"{name}.policy.body")


P_THETA = Tuple([Tuple([sym("ρ_θ0"), Sub(Number(1), sym("ρ_θ0"))]),
                 Tuple([Sub(Number(1), sym("ρ_θ1")), sym("ρ_θ1")])])
LEVELS = Tuple([Number(0), sym("θ_e")])


def law_of(items, subject):
    found = [item.core for item in items
             if isinstance(item, Statement) and isinstance(item.core, Law) and item.core.subjects == (subject,)]
    assert len(found) == 1, subject
    return found[0].law


def test_ageing_laws():
    # The abilities follow independent Markov chains whose laws name last
    # period's ability; the demographic label s has probabilities in the
    # order of its declared labels.
    for name, tag in (("worker_ageing", "wa"), ("entrepreneur_ageing", "ea")):
        items = ITEMS[name]
        check(law_of(items, "y_n"), Call("MarkovChain", [sym("P_y"), sym("y_grid"), sym(f"y_{tag}")]),
              f"{name}.law(y_n)")
        check(law_of(items, "θ_n"), Call("MarkovChain", [P_THETA, LEVELS, sym(f"θ_{tag}")]),
              f"{name}.law(θ_n)")
        check(law_of(items, "s"), Call("Categorical", [Tuple([sym("π_y"), Sub(Number(1), sym("π_y"))])]),
              f"{name}.law(s)")


def test_death_laws():
    # An offspring's working ability is drawn from the invariant distribution
    # of P_y; its entrepreneurial ability follows the parent's when the parent
    # was an entrepreneur and the invariant distribution otherwise.
    for name in ("entrepreneur_death", "retiree_death"):
        items = ITEMS[name]
        check(law_of(items, "y_n"), Call("Invariant", [sym("P_y"), sym("y_grid")]), f"{name}.law(y_n)")
        check(law_of(items, "s"), Call("Categorical", [Tuple([sym("π_o"), Sub(Number(1), sym("π_o"))])]),
              f"{name}.law(s)")
    check(law_of(ITEMS["entrepreneur_death"], "θ_n"), Call("MarkovChain", [P_THETA, LEVELS, sym("θ_ed")]),
          "entrepreneur_death.law(θ_n)")
    check(law_of(ITEMS["retiree_death"], "θ_n"), Call("Invariant", [P_THETA, LEVELS]),
          "retiree_death.law(θ_n)")


def test_demographic_branches_are_keyed_by_the_shock():
    # The fork lists the shock s on its decision side, and the value is the
    # expectation over s of the branch value s selects, discounted by β and,
    # for an offspring, weighted by η; the arrival value integrates the new
    # abilities.
    cases = (
        ("worker_ageing", ("young", "old"), cntn("V_young"), cntn("W_r")),
        ("entrepreneur_ageing", ("young", "old"), cntn("V_young"), cntn("W_old")),
        ("entrepreneur_death", ("survive", "die"), cntn("W_old"), Mul(sym("η"), cntn("V_young"))),
        ("retiree_death", ("survive", "die"), cntn("W_r"), Mul(sym("η"), cntn("V_young"))),
    )
    for name, labels, first, second in cases:
        fork, backward, arrival = ITEMS[name][-3], ITEMS[name][-2], ITEMS[name][-1]
        signature = fork.tag.entries[1].typing
        check(signature.source, Subject([coord("a"), coord("y"), coord("θ"), coord("s")]),
              f"{name}.dcsn_to_cntn.source")
        check(signature.target, Subject([]), f"{name}.dcsn_to_cntn.target")
        assert [b.tag.entries[0] for b in fork.body] == [KeyValue("label", label) for label in labels]
        expectation = Operator("E", [Var("s")], [Select(Tuple([first, second]), Key("s"))])
        check(backward.body, [statement(sym("V"), Mul(sym("β"), expectation), "value")],
              f"{name}.cntn_to_dcsn.body")
        check(arrival.body,
              [statement(arvl("V"), Operator("E", [Var("y_n"), Var("θ_n")], [sym("V")]), "value")],
              f"{name}.dcsn_to_arvl.body")


if __name__ == "__main__":
    sys.exit(run_checks(globals(), "on the ten stages"))
