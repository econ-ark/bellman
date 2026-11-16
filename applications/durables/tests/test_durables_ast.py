"""Hand-derived AST expectations for three of the four stages of the durables
model and for their methods files, the additions `methods.bl` beside them,
which hold their derivative lines, their endogenous grid lines and the typing
entries of their methods; the terminal stage `bequest.bl` is compared by the
corpus test alone.

Every expectation below is derived from the surface text of
`declaration/stages/tenure/tenure.bl`, `declaration/stages/keeper_cons/keeper_cons.bl`
and `declaration/stages/adjuster_cons/adjuster_cons.bl`, of the methods file
`methods.bl` in each of those folders and of the adjuster's second addition
`methods.adjuster_method.bl`, and from the generated term constructors
(bellman.sym.terms, generated from dynspec_full.asdl), not copied from their
recordings `*.ast.json` under `packages/bellman/tests/snapshot/corpus/durables/`.
Each file is parsed fresh through the Lark route (stage.lark, then the ToAst
lowering) and compared item by item.

Constructs particular to this model, asserted deliberately: the branching
transition of `tenure.bl`, whose output side is empty and whose body is two
labeled blocks with no shared field name; the selection of a branch value,
and of the derivatives of the branch values, by the control, `(…, …)[d]`,
which lowers to a Select of a Tuple by a name key; the inequality statement of
both consumption stages' endogenous grid lines, which writes the borrowing
constraint as a correspondence; the joint maximization of `adjuster_cons.bl`,
whose left side is a tuple and whose two binders carry feasible sets, the
second reading the first binder; the joint solution statement of the adjuster's
addition, with two unknowns and two residuals; and the typing entries of the
additions, a method word with its keyword arguments, a handler binding and a
grid entry, in a block's header and at file level. The tuple left side
constructs as a joint choice. All the files parse, which is what this test
checks.

Runnable under pytest or directly:

    venv/bin/python applications/durables/tests/test_durables_ast.py
"""

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "applications"))

import pytest

import stage_ast
from stage_ast import arvl, block, check, cntn, dom, one_minus, parsed, run_checks, sym
from bellman.syntax.terms import (
    Add, Annotation, Arrival, Assignment, At, Block, Call, Cartesian, Closed, Constancy, Constant,
    Continuation, Control, Coordinate, CorrDef, Declaration, Declare, Decision,
    Div, Domain, Equation, FiniteSet, FuncDef, Functions, Grid, Handler, In, Inequality,
    Infoset, IntegerRange, Interval, Key, KeyValue, Keyword, Law, Le, Metadata, Method, Mul,
    Name, Named, Neg, Number, Open, Operator, Points, Pow, Range, Role, Segment,
    Select, Signature, Space, Spaced, Statement, Sub, Subject, Sym, Tag, Term, Tuple,
    Typer, Value, Var, Word,
)
from bellman.syntax.terms import Path as TermPath

STAGES = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "stages"
TENURE = parsed(STAGES / "tenure" / "tenure.bl")
KEEPER = parsed(STAGES / "keeper_cons" / "keeper_cons.bl")
ADJUSTER = parsed(STAGES / "adjuster_cons" / "adjuster_cons.bl")
# the additions beside the three stage files, each a metadata line, the
# declarations of its settings, its typing lines and its blocks, whose lines
# the union appends to the stage's blocks of the same id
ADDITIONS = {key: parsed(STAGES / key / "methods.bl")
             for key in ("tenure", "keeper_cons", "adjuster_cons")}
ADJUSTER_METHOD = parsed(STAGES / "adjuster_cons" / "methods.adjuster_method.bl")


def addition(stage):
    """The items of the addition of `stage`, whose first item is the metadata
    line `@methods: <stage>`."""
    items = ADDITIONS[stage].items
    check(items[0], Metadata("methods", stage), "items[0]")
    return items


# --- spellings shared by the three files -------------------------------------

def ident(name):
    return Annotation([KeyValue("id", name)])


def coord(stem, at=None, classifiers=()):
    return Coordinate(stem, at, list(classifiers))


def value(space="ℝ"):
    """The classifiers of a value field, domain then role as written."""
    return [dom(space), Role(Value(0))]


AGE = Statement(Assignment(Constant("Age"), Space(IntegerRange(Number(20), Number(71)))), None)
CONSTANT_AGE = [*value("Age"), Constancy()]


def derivative(coordinate, field):
    """The derivative term `D_{coordinate}` of the value field `field`, an
    operator term whose one argument is the field as the line writes it."""
    return Operator("D", [Var(coordinate)], [field])


def sig(source, source_types, target, target_types):
    return Typer(Signature(Subject(source), source_types,
                           Subject(target), target_types))


def header(block_id, signature):
    return Annotation([KeyValue("id", block_id), signature])


# --- the typing entries of an addition ----------------------------------------

def path(*names, at=None):
    """The path of a typing entry's subject, `evaluate.method`; `at` refines
    the first segment by the object it evaluates, `evaluate[V].method`."""
    segments = [Segment(name=name, selectors=()) for name in names]
    if at is not None:
        segments[0] = Segment(name=names[0], selectors=(at,))
    return TermPath(segments=tuple(segments))


def typed(subject, classifier):
    """A typing entry of a header or a group, `<path> : <method or grid>`."""
    return Typer(Declaration(subject=subject, classifiers=(classifier,), value=None))


def bound_to(subject, program):
    """A handler binding, `<path> : "<program>"`."""
    return Typer(Handler(subject=subject, program=program))


def word(name, **keywords):
    """A method word with its keyword arguments, each valued by a name."""
    return Method(Word(name=name, arguments=tuple(
        Keyword(key=key, value=Name(name=value)) for key, value in keywords.items())))


def spaced(coordinate, lower, upper, count, spacing=None):
    """A factor of a grid, a triple of declared settings, with an optional
    spacing word."""
    return Spaced(coordinate=coordinate, lower=Name(name=lower), upper=Name(name=upper),
                  count=Name(name=count),
                  spacing=None if spacing is None else Word(name=spacing, arguments=()))


def cartesian(*factors):
    return Grid(Cartesian(factors=tuple(factors)))


def selection(subject, classifier):
    """A typing line at file level, routed by its path to the node it names."""
    return Declare(Declaration(subject=subject, classifiers=(classifier,), value=None), None)


def binding(subject, program):
    """A handler binding at file level."""
    return Declare(Handler(subject=subject, program=program), None)


def typing_lines(items):
    """The typing lines of an addition, the Declare items whose subject is a
    path, in order."""
    return [item for item in items
            if isinstance(item, Declare) and isinstance(item.declaration.subject, TermPath)]


LINEAR = word("Linear", extrapolate="extrap_policy", clamp_factor="clamp_max_factor")


def scalar_declarations(items, offset, expected):
    """`name : <set>` lines: the domain sits on the Declaration and the
    coordinate carries none; a written `:: ["…"]` description is kept on
    the Declare item's annotation slot (AMD-SG-014 §3)."""
    for index, (stem, space, described) in enumerate(expected, start=offset):
        annot = None if described is None else Annotation([Tag(f'"{described}"')])
        want = Declare(Declaration(
            Subject([coord(stem)]), [Domain(space)], None), annot)
        check(items[index], want, f"items[{index}]")


# --- tenure.bl ---------------------------------------------------------------

def test_tenure_file_shape():
    # Metadata, the set of ages, seven parameters, the innovation and its law,
    # then five blocks.
    kinds = [type(item).__name__ for item in TENURE.items]
    assert kinds == (["Metadata", "Statement"] + ["Declare"] * 8 + ["Statement"]
                     + ["Block"] * 5), kinds
    assert stage_ast.unlowered_parse_nodes(TENURE) == []


def test_tenure_declarations():
    check(TENURE.items[0], Metadata("stage", "tenure"), "items[0]")
    # `δ : [0,1)` is closed at zero and open at one; `ρ_z : (0,1)` is open at
    # both ends. Each trailing `:: [...]` explanation is a Tag on the
    # declaration's annotation; the innovation `ε : ℝ` is written without one.
    check(TENURE.items[1], AGE, "items[1]")
    scalar_declarations(TENURE.items, 2, [
        ("R", Named("ℝ₊₊"), "gross return on financial assets"),
        ("R_H", Named("ℝ₊₊"),
         "gross return on housing, received when the house is sold"),
        ("δ", Interval(Range(Closed(), Number(0), Number(1), Open())),
         "depreciation rate of housing"),
        ("ρ_z", Interval(Range(Open(), Number(0), Number(1), Open())),
         "persistence of log income"),
        ("σ_z", Named("ℝ₊"),
         "standard deviation of the innovation to log income"),
        ("Y", Functions(Named("Age"), Named("ℝ₊")),
         "earnings per unit of the income state at the age of the period"),
        ("y_R", Functions(Named("Age"), Named("ℝ₊")),
         "income that does not depend on the income state at the age of"
         " the period"),
        ("ε", Named("ℝ"), None),
    ])


def test_tenure_innovation_law():
    check(TENURE.items[10],
          Statement(Law(["ε"], Call("N", [Number(0), Number(1)])), None),
          "items[10]")


def test_tenure_arrival_transition():
    # The innovation rides on the arrival side as an argument of the
    # transition; `z^ρ_z*exp(σ_z*ε)` is the autoregression in levels, with the
    # power binding before the multiplication.
    want = Block(
        header("arvl_to_dcsn", sig(
            [coord("a", None, [dom("ℝ₊")]),
             coord("h", None, [dom("ℝ₊₊")]),
             coord("z", None, [dom("ℝ₊₊")]),
             coord("ε")],
            [Infoset(Arrival())],
            [coord("a_d", None, [dom("ℝ₊")]),
             coord("h_d", None, [dom("ℝ₊₊")]),
             coord("z_d", None, [dom("ℝ₊₊")])],
            [Infoset(Decision())])),
        [Statement(Equation(sym("a_d"), sym("a")), None),
         Statement(Equation(sym("h_d"), sym("h")), None),
         Statement(Equation(sym("z_d"),
                            Mul(Pow(sym("z"), sym("ρ_z")),
                                Call("exp", [Mul(sym("σ_z"), sym("ε"))]))),
                   ident("income_state"))])
    check(TENURE.items[11], want, "items[11]")


def test_tenure_branching_transition():
    # The branch control is typed by the ordered set of labels, the output side
    # is empty, and the body is one labelled block per branch, each defining
    # its own fields. No field name is shared between the branches.
    keep = Block(
        Annotation([KeyValue("label", "keep"),
                    sig([], [],
                        [coord("w_kp", None, [dom("ℝ₊₊")]),
                         coord("h_kp", None, [dom("ℝ₊₊")]),
                         coord("z_kp", None, [dom("ℝ₊₊")])],
                        [Infoset(Continuation())])]),
        [Statement(Equation(sym("w_kp"),
                            Add(Add(Mul(sym("R"), sym("a_d")),
                                    Mul(Select(sym("Y"), Term(cntn("age_kp"))), sym("z_d"))),
                                Select(sym("y_R"), Term(cntn("age_kp"))))),
                   ident("cash_on_hand")),
         Statement(Equation(sym("h_kp"), Mul(one_minus("δ"), sym("h_d"))),
                   ident("housing_kept")),
         Statement(Equation(sym("z_kp"), sym("z_d")), None)])
    adjust = Block(
        Annotation([KeyValue("label", "adjust"),
                    sig([], [],
                        [coord("w_adj", None, [dom("ℝ₊₊")]),
                         coord("z_adj", None, [dom("ℝ₊₊")])],
                        [Infoset(Continuation())])]),
        [Statement(Equation(sym("w_adj"),
                            Add(Add(Add(Mul(sym("R"), sym("a_d")),
                                        Mul(Mul(sym("R_H"), one_minus("δ")), sym("h_d"))),
                                    Mul(Select(sym("Y"), Term(cntn("age_adj"))), sym("z_d"))),
                                Select(sym("y_R"), Term(cntn("age_adj"))))),
                   ident("total_wealth")),
         Statement(Equation(sym("z_adj"), sym("z_d")), None)])
    want = Block(
        header("dcsn_to_cntn", sig(
            [coord("a_d"), coord("h_d"), coord("z_d"),
             coord("age_kp", At(Continuation())), coord("age_adj", At(Continuation())),
             coord("d", None, [Role(Control()),
                               Domain(FiniteSet(["keep", "adjust"]))])],
            [Infoset(Decision())], [], [])),
        [keep, adjust])
    check(TENURE.items[12], want, "items[12]")


def test_tenure_branch_selection():
    # Each backward line selects from a tuple by the control: the value, in
    # the stage file, and the derivatives of the decision value in a_d and
    # h_d, in the addition's block cntn_to_dcsn, each a selection of
    # derivatives of the branch values with the derivative of the branch
    # transition as the factor. Tuple positions are in label order, keep
    # first.
    want = Block(
        header("cntn_to_dcsn", sig(
            [coord("V_kp", At(Continuation()), value()),
             coord("V_adj", At(Continuation()), value()),
             coord("age_kp", At(Continuation()), CONSTANT_AGE),
             coord("age_adj", At(Continuation()), CONSTANT_AGE),
             coord("d")],
            [Infoset(Continuation())],
            [coord("V", None, value()), coord("age", None, CONSTANT_AGE)],
            [Infoset(Decision())])),
        [Statement(Equation(sym("V"),
                            Select(Tuple([cntn("V_kp"), cntn("V_adj")]),
                                   Key("d"))),
                   ident("choice_value")),
         Statement(Equation(sym("age"), Sub(cntn("age_kp"), Number(1))), ident("age"))])
    check(TENURE.items[13], want, "items[13]")
    # The addition's block of the same id carries no signature: its header
    # types the representation of the value at the Evaluation, with its
    # handler and its grid of assets and housing, and its two lines are
    # appended to the value builder's body by the union.
    marginal = block(addition("tenure"), "cntn_to_dcsn")
    want = Block(
        Annotation([
            KeyValue("id", "cntn_to_dcsn"),
            typed(path("evaluate", "method", at=Key("V")), LINEAR),
            bound_to(path("evaluate", "handler", at=Key("V")), "dcsmm:interp_as_scalar"),
            typed(path("evaluate", "grid", at=Key("V")),
                  cartesian(spaced("a_d", "a_min", "a_max", "n_a"),
                            spaced("h_d", "h_min", "h_max", "n_h")))]),
        [Statement(Equation(derivative("a_d", sym("V")),
                            Select(Tuple([Mul(sym("R"), derivative("w_kp", cntn("V_kp"))),
                                          Mul(sym("R"), derivative("w_adj", cntn("V_adj")))]),
                                   Key("d"))),
                   ident("marginal_assets")),
         Statement(Equation(derivative("h_d", sym("V")),
                            Select(Tuple([Mul(one_minus("δ"), derivative("h_kp", cntn("V_kp"))),
                                          Mul(Mul(sym("R_H"), one_minus("δ")),
                                              derivative("w_adj", cntn("V_adj")))]),
                                   Key("d"))),
                   ident("marginal_housing"))])
    check(marginal, want, "tenure/methods.bl cntn_to_dcsn")


def test_tenure_arrival_expectation():
    # The value is integrated over the innovation: one Operator, its head "E"
    # with the lexed underscore stripped. The laws `a_d = a` and `h_d = h`
    # are the identity in the two coordinates of the derivatives, so the
    # file writes no derivative line here.
    want = Block(
        header("dcsn_to_arvl", sig(
            [coord("V"), coord("age")],
            [Infoset(Decision())],
            [coord("V", At(Arrival()), value()), coord("age")],
            [Infoset(Arrival())])),
        [Statement(Equation(arvl("V"), Operator("E", [Var("ε")], [sym("V")])),
                   ident("value"))])
    check(TENURE.items[14], want, "items[14]")


def test_tenure_policy():
    # The policy block compares the same two alternatives as the value line and
    # returns the label; its inputs are the two continuation values alone.
    want = Block(
        header("policy", sig(
            [coord("V_kp", At(Continuation()), value()),
             coord("V_adj", At(Continuation()), value())],
            [Infoset(Continuation())],
            [coord("d", None, [Domain(FiniteSet(["keep", "adjust"])),
                               Role(Control())])],
            [Infoset(Decision())])),
        [Statement(Equation(sym("d"),
                            Operator("argmax", [Var("d")],
                                     [cntn("V_kp"), cntn("V_adj")])),
                   ident("choice"))])
    check(TENURE.items[15], want, "items[15]")


# --- keeper_cons.bl ----------------------------------------------------------

UTILITY = Add(
    Div(Mul(sym("α"), Pow(sym("c"), one_minus("γ_c"))), one_minus("γ_c")),
    Div(Mul(one_minus("α"), Pow(Mul(sym("κ"), sym("h")), one_minus("γ_h"))),
        one_minus("γ_h")))

MARGINAL_CONSUMPTION = Mul(sym("α"), Pow(sym("c"), Neg(sym("γ_c"))))

MARGINAL_HOUSING = Mul(Mul(one_minus("α"), Pow(sym("κ"), one_minus("γ_h"))),
                       Pow(sym("h"), Neg(sym("γ_h"))))

INVERSE_MARGINAL = Pow(Div(sym("α"), sym("x")), Div(Number(1), sym("γ_c")))

CONSUMPTION_PARAMS = [coord("c", None, [dom("ℝ₊₊")])]
HOUSING_PARAMS = [coord("h", None, [dom("ℝ₊₊")])]
UTILITY_PARAMS = CONSUMPTION_PARAMS + HOUSING_PARAMS


def preference_functions(items, offset):
    """The four closed forms both consumption stages write, in source order."""
    check(items[offset],
          Statement(FuncDef("𝑢", UTILITY_PARAMS, UTILITY), ident("util")),
          f"items[{offset}]")
    check(items[offset + 1],
          Statement(FuncDef("𝑢_c", CONSUMPTION_PARAMS, MARGINAL_CONSUMPTION),
                    ident("marg_util_cons")),
          f"items[{offset + 1}]")
    check(items[offset + 2],
          Statement(FuncDef("𝑢_h", HOUSING_PARAMS, MARGINAL_HOUSING),
                    ident("marg_util_housing")),
          f"items[{offset + 2}]")
    check(items[offset + 3],
          Statement(FuncDef("𝑢_c_inv", [coord("x", None, [dom("ℝ₊₊")])],
                            INVERSE_MARGINAL),
                    ident("inv_marg_util_cons")),
          f"items[{offset + 3}]")


def test_keeper_file_shape():
    # One metadata line, five parameters, four function definitions and one
    # correspondence definition, then the three blocks: the decision perch is
    # the stage's entry perch, and no arrival block stands before it.
    kinds = [type(item).__name__ for item in KEEPER.items]
    assert kinds == (["Metadata", "Statement"] + ["Declare"] * 5 + ["Statement"] * 5
                     + ["Block"] * 3), kinds
    assert stage_ast.unlowered_parse_nodes(KEEPER) == []
    check(KEEPER.items[0], Metadata("stage", "keeper_cons"), "items[0]")


def test_keeper_declarations():
    # Both curvatures are declared above one: at one the written expression
    # divides by zero.
    check(KEEPER.items[1], AGE, "items[1]")
    scalar_declarations(KEEPER.items, 2, [
        ("β", Interval(Range(Open(), Number(0), Number(1), Open())),
         "discount factor"),
        ("α", Interval(Range(Open(), Number(0), Number(1), Open())),
         "weight of consumption in utility"),
        ("γ_c", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from consumption"),
        ("γ_h", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from housing services"),
        ("κ", Named("ℝ₊₊"), "housing services per unit of the housing stock"),
    ])


def test_keeper_functions_and_feasible_set():
    preference_functions(KEEPER.items, 7)
    # A definition whose body is a set is a correspondence definition: from
    # cash on hand to the interval of feasible consumption.
    check(KEEPER.items[11],
          Statement(CorrDef("Γ", [coord("x", None, [dom("ℝ₊₊")])],
                            Interval(Range(Open(), Number(0), sym("x"),
                                           Closed()))),
                    ident("feasible")),
          "items[10]")


def test_keeper_transitions():
    # The budget: savings are the declared non-negative output, so the equation
    # and the declared sets state that consumption cannot exceed cash on hand.
    # The header types the decision states, the stage having no arrival block
    # whose output would type them.
    budget = Block(
        header("dcsn_to_cntn", sig(
            [coord("w_d", None, [dom("ℝ₊₊")]), coord("h_d", None, [dom("ℝ₊₊")]),
             coord("z_d", None, [dom("ℝ₊₊")]),
             coord("c", None, [dom("ℝ₊₊"), Role(Control())])],
            [Infoset(Decision())],
            [coord("a_nxt_kp", None, [dom("ℝ₊")]),
             coord("h_nxt_kp", None, [dom("ℝ₊₊")]),
             coord("z_nxt_kp", None, [dom("ℝ₊₊")])],
            [Infoset(Continuation())])),
        [Statement(Equation(sym("a_nxt_kp"), Sub(sym("w_d"), sym("c"))),
                   ident("savings")),
         Statement(Equation(sym("h_nxt_kp"), sym("h_d")), ident("housing")),
         Statement(Equation(sym("z_nxt_kp"), sym("z_d")),
                   ident("income_state"))])
    check(KEEPER.items[12], budget, "items[11]")


def test_keeper_values():
    # Current utility plus the discounted continuation value. The inputs name
    # the continuation value and the control and no side word; the decision
    # state h_d the line reads is a coordinate of the output and is not
    # listed (the backward-header rule of 12 October 2026).
    want = Block(
        header("cntn_to_dcsn", sig(
            [coord("V", At(Continuation()), value()),
             coord("age", None, CONSTANT_AGE), coord("c")],
            [Infoset(Continuation())],
            [coord("V", None, value()), coord("age")],
            [Infoset(Decision())])),
        [Statement(Equation(sym("V"),
                            Add(Call("𝑢", [sym("c"), sym("h_d")]),
                                Mul(sym("β"), cntn("V")))),
                   ident("value"))])
    check(KEEPER.items[13], want, "items[12]")
    # The addition's block of the same id: the derivative of the decision
    # value in cash, the marginal utility of consumption; and its derivative
    # in housing, the housing services of the period plus the discounted
    # derivative of the continuation value in housing. Its header types one
    # representation of the value and both derivatives, with its handler and
    # its grid of cash on hand and housing, and carries no signature.
    marginal = block(addition("keeper_cons"), "cntn_to_dcsn")
    want = Block(
        Annotation([
            KeyValue("id", "cntn_to_dcsn"),
            typed(path("evaluate", "method"), LINEAR),
            bound_to(path("evaluate", "handler"), "dcsmm:interp_as"),
            typed(path("evaluate", "grid"),
                  cartesian(spaced("w_d", "a_min", "a_max", "n_a"),
                            spaced("h_d", "h_min", "h_max", "n_h")))]),
        [Statement(Equation(derivative("w_d", sym("V")), Call("𝑢_c", [sym("c")])),
                   ident("marginal_cash")),
         Statement(Equation(derivative("h_d", sym("V")),
                            Add(Call("𝑢_h", [sym("h_d")]),
                                Mul(sym("β"), derivative("h_nxt_kp", cntn("V"))))),
                   ident("marginal_housing"))])
    check(marginal, want, "keeper_cons/methods.bl cntn_to_dcsn")


def test_keeper_policy():
    # The stage file's policy block states the maximisation alone: it binds
    # the control on its feasible set. The addition's block of the same id
    # types the endogenous grid method on the builder, with the routine's
    # keyword arguments, its handler and its grid of savings, and holds the
    # method's lines: the inverse Euler line is an inequality, which defines
    # candidate consumption as a correspondence; the second line inverts the
    # budget; the third identifies the control with the candidate.
    objective = Add(Call("𝑢", [sym("c"), sym("h_d")]),
                    Mul(sym("β"), cntn("V")))
    signature = sig(
        [coord("V", At(Continuation()), value())],
        [Infoset(Continuation())],
        [coord("c", None, [dom("ℝ₊₊"), Role(Control())])],
        [Infoset(Decision())])
    want = Block(
        header("policy", signature),
        [Statement(Equation(sym("c"),
                            Operator("argmax",
                                     [In("c", Call("Γ", [sym("w_d")]))],
                                     [objective])),
                   ident("optimality"))])
    check(KEEPER.items[14], want, "items[13]")
    method = block(addition("keeper_cons"), "policy")
    want = Block(
        Annotation([
            KeyValue("id", "policy"),
            typed(path("policy", "method"), word(
                "egm", spacing="grid_phi", savings_floor="b",
                upper_envelope="keeper_upper_envelope", jump_threshold="m_bar",
                lookback="fues_lb", eps_d="fues_eps_d", eps_sep="fues_eps_sep",
                eps_fwd_back="fues_eps_fwd_back", parallel_guard="fues_parallel_guard",
                include_intersections="keeper_include_intersections",
                no_double_jumps="keeper_no_double_jumps",
                single_intersection="keeper_single_intersection",
                disable_jump_checks="keeper_disable_jump_checks")),
            bound_to(path("policy", "handler"), "fues-durables:make_keeper_ops"),
            typed(path("policy", "grid"), cartesian(spaced("a_nxt_kp", "a_min", "a_max", "n_a")))]),
        [Statement(Inequality(cntn("c"), Le(),
                              Call("𝑢_c_inv",
                                   [Mul(sym("β"), derivative("a_nxt_kp", cntn("V")))])),
                   ident("InvEuler")),
         Statement(Equation(cntn("w_d"),
                            Add(sym("a_nxt_kp"), cntn("c"))),
                   ident("endoggrid")),
         Statement(Equation(sym("c"), cntn("c")), ident("cons_choice"))])
    check(method, want, "keeper_cons/methods.bl policy")


# --- adjuster_cons.bl --------------------------------------------------------

def test_adjuster_file_shape():
    # One metadata line, six parameters, four function definitions and two
    # correspondence definitions, then the three blocks: the decision perch is
    # the stage's entry perch, and no arrival block stands before it.
    kinds = [type(item).__name__ for item in ADJUSTER.items]
    assert kinds == (["Metadata", "Statement"] + ["Declare"] * 6 + ["Statement"] * 6
                     + ["Block"] * 3), kinds
    assert stage_ast.unlowered_parse_nodes(ADJUSTER) == []
    check(ADJUSTER.items[0], Metadata("stage", "adjuster_cons"), "items[0]")


def test_adjuster_declarations_and_functions():
    check(ADJUSTER.items[1], AGE, "items[1]")
    scalar_declarations(ADJUSTER.items, 2, [
        ("β", Interval(Range(Open(), Number(0), Number(1), Open())),
         "discount factor"),
        ("α", Interval(Range(Open(), Number(0), Number(1), Open())),
         "weight of consumption in utility"),
        ("γ_c", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from consumption"),
        ("γ_h", Interval(Range(Open(), Number(1), Sym(Constant("inf")),
                               Open())),
         "curvature of utility from housing services"),
        ("κ", Named("ℝ₊₊"), "housing services per unit of the housing stock"),
        ("τ", Named("ℝ₊₊"),
         "cost of adjusting housing, per unit of housing bought"),
    ])
    # The same four closed forms as the keeper's stage: one household, one
    # period, one utility function.
    preference_functions(ADJUSTER.items, 8)


def test_adjuster_feasible_sets():
    # Two correspondences, read in the order the maximisation binds them:
    # consumption up to total wealth, then housing up to what is left, divided
    # by the unit price of housing.
    check(ADJUSTER.items[12],
          Statement(CorrDef("Γ_c", [coord("x", None, [dom("ℝ₊₊")])],
                            Interval(Range(Open(), Number(0), sym("x"),
                                           Closed()))),
                    ident("feasible_consumption")),
          "items[11]")
    check(ADJUSTER.items[13],
          Statement(CorrDef("Γ_h", [coord("x", None, [dom("ℝ₊")])],
                            Interval(Range(Open(), Number(0),
                                           Div(sym("x"),
                                               Add(Number(1), sym("τ"))),
                                           Closed()))),
                    ident("feasible_housing")),
          "items[12]")


def test_adjuster_transitions():
    # Two controls on the decision side; the budget subtracts consumption and
    # then the cost of the new house, so the sum associates to the left. The
    # header types the decision states, the stage having no arrival block
    # whose output would type them.
    budget = Block(
        header("dcsn_to_cntn", sig(
            [coord("m", None, [dom("ℝ₊₊")]), coord("z_d", None, [dom("ℝ₊₊")]),
             coord("c", None, [dom("ℝ₊₊"), Role(Control())]),
             coord("h_choice", None, [dom("ℝ₊₊"), Role(Control())])],
            [Infoset(Decision())],
            [coord("a_nxt_adj", None, [dom("ℝ₊")]),
             coord("h_nxt_adj", None, [dom("ℝ₊₊")]),
             coord("z_nxt_adj", None, [dom("ℝ₊₊")])],
            [Infoset(Continuation())])),
        [Statement(Equation(sym("a_nxt_adj"),
                            Sub(Sub(sym("m"), sym("c")),
                                Mul(Add(Number(1), sym("τ")),
                                    sym("h_choice")))),
                   ident("savings")),
         Statement(Equation(sym("h_nxt_adj"), sym("h_choice")),
                   ident("housing")),
         Statement(Equation(sym("z_nxt_adj"), sym("z_d")),
                   ident("income_state"))])
    check(ADJUSTER.items[14], budget, "items[13]")


def test_adjuster_values():
    # Utility is over consumption and the new house. The one derivative the
    # addition's block cntn_to_dcsn states is that of the
    # decision value in cash on hand m, which the tenure stage reads on this
    # branch, its total wealth `w_adj` joined to `m`.
    want = Block(
        header("cntn_to_dcsn", sig(
            [coord("V", At(Continuation()), value()),
             coord("age", None, CONSTANT_AGE), coord("c"), coord("h_choice")],
            [Infoset(Continuation())],
            [coord("V", None, value()), coord("age")],
            [Infoset(Decision())])),
        [Statement(Equation(sym("V"),
                            Add(Call("𝑢", [sym("c"), sym("h_choice")]),
                                Mul(sym("β"), cntn("V")))),
                   ident("value"))])
    check(ADJUSTER.items[15], want, "items[14]")
    # The addition's block of the same id types the value and its stated
    # derivative at their own Evaluations, each with the handler and the grid
    # of total wealth, and appends the envelope line.
    marginal = block(addition("adjuster_cons"), "cntn_to_dcsn")
    value_at, marginal_at = Key("V"), Term(derivative("m", sym("V")))
    want = Block(
        Annotation([
            KeyValue("id", "cntn_to_dcsn"),
            typed(path("evaluate", "method", at=value_at), LINEAR),
            bound_to(path("evaluate", "handler", at=value_at), "dcsmm:interp_as_3"),
            typed(path("evaluate", "grid", at=value_at), cartesian(spaced("m", "w_min", "w_max", "n_w"))),
            typed(path("evaluate", "method", at=marginal_at), LINEAR),
            bound_to(path("evaluate", "handler", at=marginal_at), "dcsmm:interp_as_3"),
            typed(path("evaluate", "grid", at=marginal_at), cartesian(spaced("m", "w_min", "w_max", "n_w")))]),
        [Statement(Equation(derivative("m", sym("V")), Call("𝑢_c", [sym("c")])),
                   ident("marginal_wealth"))])
    check(marginal, want, "adjuster_cons/methods.bl cntn_to_dcsn")


def test_adjuster_policy():
    # The stage file's policy block states the joint maximisation alone: a
    # tuple on the left, and two binders each carrying a feasible set, the
    # second reading the first binder. The addition's block of the same id
    # types the method, its handler and its grid by the relative subjects, and
    # holds the inverse Euler inequality, the inverted budget, and the two
    # first-order conditions as one solution statement in two unknowns.
    objective = Add(Call("𝑢", [sym("c"), sym("h_choice")]),
                    Mul(sym("β"), cntn("V")))
    housing_residual = Sub(
        Sub(Mul(Add(Number(1), sym("τ")), Call("𝑢_c", [sym("c")])),
            Call("𝑢_h", [sym("h_choice")])),
        Mul(sym("β"), derivative("h_nxt_adj", cntn("V"))))
    signature = sig(
        [coord("V", At(Continuation()), value())],
        [Infoset(Continuation())],
        [coord("c", None, [dom("ℝ₊₊"), Role(Control())]),
         coord("h_choice", None, [dom("ℝ₊₊"), Role(Control())])],
        [Infoset(Decision())])
    want = Block(
        header("policy", signature),
        [Statement(Equation(Tuple([sym("c"), sym("h_choice")]),
                            Operator("argmax",
                                     [In("c", Call("Γ_c", [sym("m")])),
                                      In("h_choice",
                                         Call("Γ_h", [Sub(sym("m"),
                                                          sym("c"))]))],
                                     [objective])),
                   ident("optimality"))])
    check(ADJUSTER.items[16], want, "items[15]")
    method = block(addition("adjuster_cons"), "policy")
    want = Block(
        Annotation([
            KeyValue("id", "policy"),
            typed(path("method"), word(
                "egm", spacing="grid_phi", savings_floor="b",
                roots_per_housing_point="egm_n", root_scan_step="root_eps",
                upper_envelope="adj_upper_envelope", jump_threshold="m_bar",
                lookback="fues_lb", eps_d="fues_eps_d", eps_sep="fues_eps_sep",
                eps_fwd_back="fues_eps_fwd_back", parallel_guard="fues_parallel_guard",
                include_intersections="adj_include_intersections",
                no_double_jumps="adj_no_double_jumps",
                single_intersection="adj_single_intersection",
                disable_jump_checks="adj_disable_jump_checks",
                correct_jumps="correct_jumps", search_sections="n_sections")),
            bound_to(path("handler"), "fues-durables:make_adjuster_ops"),
            typed(path("grid"), cartesian(spaced("a_nxt_adj", "a_min", "a_max", "n_a"),
                                          spaced("h_nxt_adj", "h_min", "h_max", "n_h")))]),
        [Statement(Inequality(cntn("c"), Le(),
                              Call("𝑢_c_inv",
                                   [Mul(sym("β"), derivative("a_nxt_adj", cntn("V")))])),
                   ident("InvEuler")),
         Statement(Equation(cntn("m"),
                            Add(Add(sym("a_nxt_adj"), cntn("c")),
                                Mul(Add(Number(1), sym("τ")),
                                    sym("h_nxt_adj")))),
                   ident("endoggrid")),
         Statement(Equation(Tuple([sym("c"), sym("h_choice")]),
                            Operator("solve", [Var("c"), Var("h_choice")],
                                     [Sub(sym("c"), cntn("c")),
                                      housing_residual])),
                   ident("choice"))])
    check(method, want, "adjuster_cons/methods.bl policy")


# --- the additions as files --------------------------------------------------

def test_addition_file_shapes():
    # Each addition is the metadata line, the declarations of its settings,
    # then its typing lines and its blocks: tenure declares fourteen settings
    # and writes two typing lines before its one block and four after it;
    # the keeper declares twenty-one settings and the adjuster twenty-eight,
    # each followed by its two blocks.
    assert [type(item).__name__ for item in addition("tenure")] == (
        ["Metadata"] + ["Declare"] * 16 + ["Block"] + ["Declare"] * 4)
    assert [type(item).__name__ for item in addition("keeper_cons")] == (
        ["Metadata"] + ["Declare"] * 21 + ["Block"] * 2)
    assert [type(item).__name__ for item in addition("adjuster_cons")] == (
        ["Metadata"] + ["Declare"] * 28 + ["Block"] * 2)
    for key, items in ADDITIONS.items():
        assert stage_ast.unlowered_parse_nodes(items) == [], key


def test_tenure_addition_declares_its_settings():
    # A setting is declared as a parameter is, with its set and a
    # description: the rule at a tie in the control's own set of labels, a
    # count in ℕ, a bound in the set of its coordinate, a flag in {0, 1} and
    # a probability floor in the open unit interval.
    scalar_declarations(addition("tenure"), 1, [
        ("tie_break", FiniteSet(["keep", "adjust"]),
         "branch chosen when the values of keeping and adjusting are equal"),
        ("n_a", Named("ℕ"), "number of points of the asset grid"),
        ("a_min", Named("ℝ₊"), "lower bound of the asset grid"),
        ("a_max", Named("ℝ₊"), "upper bound of the asset grid"),
        ("n_h", Named("ℕ"), "number of points of the housing grid"),
        ("h_min", Named("ℝ₊₊"), "lower bound of the housing grid"),
        ("h_max", Named("ℝ₊₊"), "upper bound of the housing grid"),
        ("extrap_policy", Points([Number(0), Number(1)], None),
         "zero clamps a tabulated function at the boundary, one extrapolates linearly"),
        ("clamp_max_factor", Named("ℝ₊₊"),
         "bound on a policy read above the grid, as a factor of the grid's upper end"),
        ("N_wage", Named("ℕ"), "number of states of Tauchen's chain for the income state"),
        ("tauchen_n_std", Named("ℝ₊₊"),
         "number of unconditional standard deviations the chain spans"),
        ("tauchen_min_prob", Interval(Range(Open(), Number(0), Number(1), Open())),
         "floor on the transition probabilities of the chain"),
        ("n_sim", Named("ℕ"), "number of simulated households"),
        ("sim_seed", Named("ℕ"), "seed of the simulation"),
    ])


def test_tenure_addition_types_the_builders_at_file_level():
    # The policy builder, the arrival value builder's expectation and the
    # arrival builder gain no line, so their methods and handlers are typing
    # lines at file level, each routed by its path: the discrete maximum with
    # the rule at a tie, Tauchen's chain at the expectation named through the
    # line `value`, and the Monte Carlo draw on the arrival edge.
    check(typing_lines(addition("tenure")), [
        selection(path("policy", "method"), word("max", tie_break="tie_break")),
        binding(path("policy", "handler"), "fues-durables:make_tenure_ops"),
        selection(path("dcsn_to_arvl", "value", "E_ε", "method"),
                  word("tauchen", n_income_states="N_wage", n_std="tauchen_n_std",
                       min_prob="tauchen_min_prob")),
        binding(path("dcsn_to_arvl", "value", "E_ε", "handler"), "fues-durables:make_conditioners"),
        selection(path("arvl_to_dcsn", "method"), word("monte_carlo", n_paths="n_sim", seed="sim_seed")),
        binding(path("arvl_to_dcsn", "handler"), "fues-durables:make_tenure_forward"),
    ], "tenure/methods.bl typing lines")


def test_adjuster_second_addition_types_the_nested_method():
    # The second addition of the adjuster, named by no recipe of the folder,
    # is the metadata line and two typing lines: value function iteration on
    # the decision value builder and the routine that realizes it.
    check(ADJUSTER_METHOD.items[0], Metadata("methods", "adjuster_cons"), "items[0]")
    check(ADJUSTER_METHOD.items[1:], [
        selection(path("cntn_to_dcsn", "method"), word("vfi")),
        binding(path("cntn_to_dcsn", "handler"), "fues-durables:make_adjuster_vfi"),
    ], "methods.adjuster_method.bl items[1:]")


if __name__ == "__main__":
    sys.exit(run_checks(globals(), "on the three durables stages and their additions"))
