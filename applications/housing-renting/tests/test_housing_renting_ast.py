"""Hand-derived AST expectations for the five housing-renting stages.

Every expected node below is derived from the surface text of
`tenure_choice.bl`, `owner_housing.bl`, `owner_cons.bl`, `renter_housing.bl`
and `renter_cons.bl`, of the methods file `methods.bl` beside each, the
addition that holds the stage's derivative line, the inverse Euler lines of
the two consumption stages and the typing entries of their methods, of the
owner's second addition `methods.vfi.bl`, and from the generated term constructors
(`bellman.sym.terms`, generated from `dynspec_full.asdl`), not copied from
their recorded encodings `*.ast.json` under
`packages/bellman/tests/snapshot/corpus/housing-renting/`. Each file is parsed
fresh through the Lark route (`stage.lark`, then the `ToAst` lowering) and the
items under test are compared with their expectations. Runnable under pytest
or directly:

    venv/bin/python applications/housing-renting/tests/test_housing_renting_ast.py

The spellings asserted here are the ones that carry rulings or that this model
introduces: the shock law that names the state it is conditional on, the tax
families declared as products of ten sets and selected by position, the
discrete sets written with the grid constructor (D21), the nested branch
blocks of the tenure choice and the tuple selections of a branch value and of
the derivatives of the branch values (D02, D03), the declarative maximization
the stage file states (D19), the inverse Euler statement, in the addition's
block of the policy builder, written as an inequality (D20), the policy input
sides, which carry continuation objects and no continuation state (D22), and
the typing entries of the additions, the refined and the unrefined form of a
representation's entries and a grid that names the cash coordinate alone. The claim that the
maximization is marked `!doc` is deleted: the mark stood while the inverse
Euler lines shared the policy block (decision MB-V22).
"""

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "applications"))

import stage_ast
from stage_ast import (VLU, at_var, block, check, describes, dom, extended_real,
                       parsed, run_checks, sym)
from bellman.syntax.terms import (
    Add, Annotation, Arrival, Assignment, At, Block, Call, Cartesian, Closed,
    Constant, Continuation, Control, Coordinate, CorrDef, Declaration, Declare,
    Decision, Div, Domain, Equation, Feasible, FiniteSet, FuncDef, Grid, In,
    Inequality, Infoset, Interval, Key, KeyValue, Keyword, Law, Le, Metadata,
    Method, Mul, Name, Named, Number, Open, Operator, Pos, Product, Range, Role,
    Segment, Select, Signature, Spaced, Statement, Sub, Subject, Tag, Term,
    Tuple, Typer, Var, Word,
)
from bellman.syntax.terms import Path as TermPath

# the folder of the model's stage folders
STAGE_FOLDERS = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "stages"
TENURE = parsed(STAGE_FOLDERS / "tenure_choice" / "tenure_choice.bl")
OWNER_H = parsed(STAGE_FOLDERS / "owner_housing" / "owner_housing.bl")
OWNER_C = parsed(STAGE_FOLDERS / "owner_cons" / "owner_cons.bl")
RENTER_H = parsed(STAGE_FOLDERS / "renter_housing" / "renter_housing.bl")
RENTER_C = parsed(STAGE_FOLDERS / "renter_cons" / "renter_cons.bl")
# the additions: the methods file beside each stage file, whose block
# `cntn_to_dcsn` holds the stage's derivative line and whose block `policy`,
# in the two consumption stages, holds the lines of the endogenous grid
# method; and the owner's second addition, the alternative by value function
# iteration, which replaces the first
ADDITIONS = {name: parsed(STAGE_FOLDERS / name / "methods.bl")
             for name in ("tenure_choice", "owner_housing", "owner_cons",
                          "renter_housing", "renter_cons")}
VFI = parsed(STAGE_FOLDERS / "owner_cons" / "methods.vfi.bl")


# --- local helpers ----------------------------------------------------------


def unit_open():
    # `(0,1)`, the declared set of β and of α.
    return Domain(Interval(Range(Open(), Number(0), Number(1), Open())))


def rate():
    # `[0,1)`, the declared set of the transaction cost and of a tax rate.
    return Domain(Interval(Range(Closed(), Number(0), Number(1), Open())))


def ids(body):
    """The `id=` of each statement of a block body, in order."""
    return [e.value for statement in body for e in statement.annot.entries
            if isinstance(e, KeyValue) and e.key == "id"]


def marginal_lines(name):
    """The lines the addition of `name` appends to the decision value builder."""
    return block(ADDITIONS[name].items, "cntn_to_dcsn").body


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


def word(name, **keywords):
    """A method word with its keyword arguments, each valued by a name."""
    return Method(Word(name=name, arguments=tuple(
        Keyword(key=key, value=Name(name=value)) for key, value in keywords.items())))


def spaced(coordinate, lower, upper, count):
    """A factor of a grid, a triple of declared settings."""
    return Spaced(coordinate=coordinate, lower=Name(name=lower), upper=Name(name=upper),
                  count=Name(name=count), spacing=None)


def cartesian(*factors):
    return Grid(Cartesian(factors=tuple(factors)))


def selection(subject, classifier):
    """A typing line at file level, routed by its path to the node it names."""
    return Declare(Declaration(subject=subject, classifiers=(classifier,), value=None), None)


def typing_lines(items):
    """The typing lines of an addition, the Declare items whose subject is a
    path, in order."""
    return [item for item in items
            if isinstance(item, Declare) and isinstance(item.declaration.subject, TermPath)]


CASH = cartesian(spaced("w_d", "w_min", "w_max", "w_points"))
EGM = word("egm", upper_envelope="upper_envelope",
           c_max="c_max",
           n_constraint_points="n_constraint_points",
           n_constraint_points_nxt="n_constraint_points_nxt",
           fues_m_bar="fues_m_bar",
           fues_lb="fues_lb",
           fues_include_intersections="fues_include_intersections",
           fues_return_intersections_separately="fues_return_intersections_separately",
           fues_single_intersection="fues_single_intersection",
           fues_endog_mbar="fues_endog_mbar",
           fues_padding_mbar="fues_padding_mbar",
           fues_no_double_jumps="fues_no_double_jumps",
           fues_disable_jump_checks="fues_disable_jump_checks",
           fues_use_post_state_jump_test="fues_use_post_state_jump_test",
           fues_left_turn_no_jump_strict="fues_left_turn_no_jump_strict",
           fues_post_clean_double_jumps="fues_post_clean_double_jumps",
           fues_detect_decreasing_policy="fues_detect_decreasing_policy",
           fues_post_clean_passes="fues_post_clean_passes",
           fues_jump_check_tol="fues_jump_check_tol",
           fues_correct_jumps="fues_correct_jumps",
           fues_min_segment_length="fues_min_segment_length",
           fues_eps_d="fues_eps_d",
           fues_eps_sep="fues_eps_sep",
           fues_eps_fwd_back="fues_eps_fwd_back",
           fues_parallel_guard="fues_parallel_guard",
           tax_enabled="tax_enabled",
           tax_c_lb_pct="tax_c_lb_pct",
           tax_c_ub_pct="tax_c_ub_pct",
           tax_n_points_per_node="tax_n_points_per_node")


# --- the five files ---------------------------------------------------------


def test_file_shapes():
    # tenure_choice: metadata, six parameters, the shock declaration, its law,
    # the tax function and its derivative, and the five blocks.
    assert [type(i).__name__ for i in TENURE.items] == (
        ["Metadata"] + ["Declare"] * 7 + ["Statement"] * 3 + ["Block"] * 5)
    # owner_housing: metadata, the housing set, eight parameters, the tax
    # function, its derivative, the housing expense, and three blocks: the
    # two housing stages and the two consumption stages have no arrival perch
    # and are entered at their decision perch (decision MB-V30).
    assert [type(i).__name__ for i in OWNER_H.items] == (
        ["Metadata", "Statement"] + ["Declare"] * 8 + ["Statement"] * 3
        + ["Block"] * 3)
    # renter_housing: metadata, the services set, four parameters, three blocks.
    assert [type(i).__name__ for i in RENTER_H.items] == (
        ["Metadata", "Statement"] + ["Declare"] * 4 + ["Block"] * 3)
    # the two consumption stages: metadata, the preference parameters, the
    # three utility definitions, the feasible correspondence, three blocks.
    assert [type(i).__name__ for i in OWNER_C.items] == (
        ["Metadata"] + ["Declare"] * 4 + ["Statement"] * 4 + ["Block"] * 3)
    assert [type(i).__name__ for i in RENTER_C.items] == (
        ["Metadata"] + ["Declare"] * 5 + ["Statement"] * 4 + ["Block"] * 3)
    for name, ast in (("tenure_choice", TENURE), ("owner_housing", OWNER_H),
                      ("owner_cons", OWNER_C), ("renter_housing", RENTER_H),
                      ("renter_cons", RENTER_C)):
        assert stage_ast.unlowered_parse_nodes(ast) == [], name
        check(ast.items[0], Metadata("stage", name), f"{name}.items[0]")


# --- tenure_choice.bl -------------------------------------------------------


def test_income_law_names_the_state_it_conditions_on():
    # `y : ℝ₊₊` declares the income level, and the following line is its law.
    check(TENURE.items[7],
          Declare(Declaration(Subject([Coordinate("y", None, [])]),
                              [dom("ℝ₊₊")], None)),
          "tenure_choice.items[7]")
    # `y ~ MarkovChain(Π, z, y_pre)`: a Law item whose subject is the shock and
    # whose law is an ordinary call. Its three arguments are the transition
    # matrix, the levels and last period's income, so the declaration is the
    # conditional law of the draw given the arrival state; a law naming no
    # state would be constant in the arrival information. The written note is
    # a tag of the same annotation.
    law = TENURE.items[8]
    check(law.core,
          Law(["y"], Call("MarkovChain", [sym("Π"), sym("z"), sym("y_pre")])),
          "tenure_choice.items[8].core")
    assert isinstance(law.annot.entries[0], Tag)


def test_tax_families_are_products_of_ten_sets():
    # The number of brackets is model content, so each family is declared with
    # a product of that many sets and calibration accepts a list of ten values.
    check(TENURE.items[4],
          Declare(Declaration(Subject([Coordinate("a0_T", None, [])]),
                              [Domain(Product([Named("ℝ₊")] * 10))], None),
                  describes("lower asset threshold of each of the ten tax"
                            " brackets, in increasing order")),
          "tenure_choice.items[4]")
    check(TENURE.items[5],
          Declare(Declaration(Subject([Coordinate("B_T", None, [])]),
                              [Domain(Product([Named("ℝ")] * 10))], None),
                  describes("tax due at the lower threshold of each bracket")),
          "tenure_choice.items[5]")
    check(TENURE.items[6],
          Declare(Declaration(Subject([Coordinate("τ_T", None, [])]),
                              [Domain(Product([rate().space] * 10))], None),
                  describes("marginal tax rate on assets within each bracket")),
          "tenure_choice.items[6]")


def test_tax_function_selects_a_bracket_by_position_and_is_differentiated():
    tax = TENURE.items[9]
    assert isinstance(tax.core, FuncDef) and tax.core.name == "𝑇"
    check(tax.core.params, [Coordinate("x", None, [dom("ℝ₊")])],
          "tenure_choice.tax.params")
    # The body is a sum of ten summands. The first is the indicator of the
    # first bracket, `step(x - a0_T[1]) - step(x - a0_T[2])`, times the tax
    # `B_T[1] + τ_T[1]*(x - a0_T[1])` charged in it; `step` is an external
    # call, since the language has no relational expression, and a bracket
    # bound is a positional selection from the declared family.
    def entry(name, at):
        return Select(sym(name), Pos(at))
    def indicator(lo, hi):
        return Sub(Call("step", [Sub(sym("x"), entry("a0_T", lo))]),
                   Call("step", [Sub(sym("x"), entry("a0_T", hi))]))
    first = Mul(indicator(1, 2),
                Add(entry("B_T", 1),
                    Mul(entry("τ_T", 1), Sub(sym("x"), entry("a0_T", 1)))))
    body = tax.core.body
    for _ in range(9):            # the sum associates to the left
        body = body.left
    check(body, first, "tenure_choice.tax.body.first_bracket")
    assert [e.value for e in tax.annot.entries if isinstance(e, KeyValue)] == ["tax"]
    # `𝑑𝑇 := D_{x}(𝑇)`: the derivative of the declared function in its own
    # argument. The lowering keeps the identifier and the description the line
    # carries on the assignment's annotation slot (AMD-SG-017 §3).
    check(TENURE.items[10],
          Statement(Assignment(Constant("𝑑𝑇"),
                               Operator("D", [Var("x")], [sym("𝑇")])),
                    Annotation([KeyValue("id", "marginal_tax"),
                                Tag('"the marginal tax rate, the derivative of the tax '
                                    'away from the bracket thresholds"')])),
          "tenure_choice.items[10]")


def test_tenure_branches_are_nested_blocks_under_an_empty_output_side():
    outer = block(TENURE.items, "dcsn_to_cntn")
    check(outer.tag,
          Annotation([
              KeyValue("id", "dcsn_to_cntn"),
              Typer(Signature(
                  Subject([Coordinate("a_d", None, []),
                           Coordinate("H_d", None, []),
                           Coordinate("y_d", None, []),
                           Coordinate("d", None, [Role(Control()),
                                                  Domain(FiniteSet(["own", "rent"]))])]),
                  [Infoset(Decision())],
                  Subject([]),
                  [])),
          ]),
          "tenure_choice.dcsn_to_cntn.tag")
    assert len(outer.body) == 2
    # The own branch carries assets, the house and income through unchanged.
    check(outer.body[0],
          Block(
              Annotation([
                  KeyValue("label", "own"),
                  Typer(Signature(
                      Subject([]), [],
                      Subject([Coordinate("a_o", None, [dom("ℝ₊")]),
                               Coordinate("H_o", None, [dom("ℝ₊")]),
                               Coordinate("y_o", None, [dom("ℝ₊₊")])]),
                      [Infoset(Continuation())])),
              ]),
              [Statement(Equation(sym("a_o"), sym("a_d")), None),
               Statement(Equation(sym("H_o"), sym("H_d")), None),
               Statement(Equation(sym("y_o"), sym("y_d")), None)]),
          "tenure_choice.dcsn_to_cntn.own")
    # The rent branch sells the house: wealth is assets after the return and
    # the tax plus the proceeds. Income is added in the rental stage.
    rent = outer.body[1]
    check(rent.tag,
          Annotation([
              KeyValue("label", "rent"),
              Typer(Signature(
                  Subject([]), [],
                  Subject([Coordinate("w_r", None, [dom("ℝ₊")]),
                           Coordinate("y_r", None, [dom("ℝ₊₊")])]),
                  [Infoset(Continuation())])),
          ]),
          "tenure_choice.dcsn_to_cntn.rent.tag")
    check(rent.body[0].core,
          Equation(sym("w_r"),
                   Add(Sub(Mul(Add(Number(1), sym("r")), sym("a_d")),
                           Call("𝑇", [sym("a_d")])),
                       sym("H_d"))),
          "tenure_choice.dcsn_to_cntn.rent.liquidation")


def test_tenure_value_and_marginal_are_tuple_selections():
    body = block(TENURE.items, "cntn_to_dcsn").body + marginal_lines("tenure_choice")
    assert ids(block(TENURE.items, "cntn_to_dcsn").body) == ["choice_value"]
    assert ids(body) == ["choice_value", "choice_marginal"]
    # V = (V_o[>], V_r[>])[d]: a two-item tuple in the order of the label set,
    # selected by the control's name.
    check(body[0].core,
          Equation(sym("V"), Select(Tuple([at_var("V_o", Continuation),
                                           at_var("V_r", Continuation)]),
                                    Key("d"))),
          "tenure_choice.cntn_to_dcsn.choice_value")
    # The derivatives are not symmetric: the owner's branch derivative is
    # already taken with respect to assets, D_{a_o}V_o[>], while the renter's
    # is taken with respect to the wealth the branch computes, D_{w_r}V_r[>],
    # so the derivative of that law of motion, 1 + r less the marginal tax
    # rate, multiplies it here.
    check(body[1].core,
          Equation(Operator("D", [Var("a_d")], [sym("V")]),
                   Select(Tuple([Operator("D", [Var("a_o")],
                                          [at_var("V_o", Continuation)]),
                                 Mul(Sub(Add(Number(1), sym("r")),
                                         Call("𝑑𝑇", [sym("a_d")])),
                                     Operator("D", [Var("w_r")],
                                              [at_var("V_r", Continuation)]))]),
                          Key("d"))),
          "tenure_choice.cntn_to_dcsn.choice_marginal")


def test_tenure_arrival_block_integrates_the_income_draw():
    # The decision states are the arrival states unchanged, so the file
    # writes no derivative line here.
    body = block(TENURE.items, "dcsn_to_arvl").body
    assert ids(body) == ["value"]
    check(body[0].core, Equation(at_var("V", Arrival),
                                 Operator("E", [Var("y")], [sym("V")])),
          "tenure_choice.dcsn_to_arvl.value")


def test_tenure_policy_compares_the_two_branch_values():
    policy = block(TENURE.items, "policy")
    sig = policy.tag.entries[1].typing
    # The inputs are the two branch values and no continuation state (D22);
    # the output is the control on its finite set.
    check(sig.source,
          Subject([Coordinate("V_o", At(Continuation()), [extended_real(), VLU]),
                   Coordinate("V_r", At(Continuation()), [extended_real(), VLU])]),
          "tenure_choice.policy.source")
    check(sig.target,
          Subject([Coordinate("d", None, [Domain(FiniteSet(["own", "rent"])),
                                          Role(Control())])]),
          "tenure_choice.policy.target")
    # The two arguments of the maximisation are the two values in the order of
    # the tuple of the value equation.
    check(policy.body[0].core,
          Equation(sym("d"),
                   Operator("argmax", [Var("d")],
                            [at_var("V_o", Continuation),
                             at_var("V_r", Continuation)])),
          "tenure_choice.policy.choice")


# --- owner_housing.bl and renter_housing.bl ---------------------------------


def test_discrete_sets_are_written_with_the_grid_constructor():
    # `XH := linspace(H_min, H_max, n_H)`: the value is an ordinary call, and
    # its three arguments are parameters of the stage. The sizes are model
    # content, so the count is a parameter and not a numerical setting (D21).
    check(OWNER_H.items[1],
          Statement(Assignment(Constant("XH"),
                               Call("linspace", [sym("H_min"), sym("H_max"),
                                                 sym("n_H")])),
                    describes("the housing sizes an owner may hold; a discrete set of "
                              "the model, not a numerical grid")),
          "owner_housing.items[1]")
    check(RENTER_H.items[1],
          Statement(Assignment(Constant("XS"),
                               Call("linspace", [sym("S_min"), sym("S_max"),
                                                 sym("n_S")])),
                    describes("the quantities of housing services a renter may rent; a "
                              "discrete set of the model, not a numerical grid")),
          "renter_housing.items[1]")
    check(OWNER_H.items[3],
          Declare(Declaration(Subject([Coordinate("φ", None, [])]),
                              [rate()], None),
                  describes("transaction cost per unit of housing bought,"
                            " paid only when the stock changes")),
          "owner_housing.items[3]")


def test_housing_expense_is_an_indicator_times_the_net_price():
    # 𝛷(h, h_n) = (step(h_n - h) + step(h - h_n))*((1 + φ)*h_n - h): the two
    # step terms are the indicator that the stock changes, so the expense is
    # the purchase price with its transaction cost less the value of the stock
    # sold, and zero when the stock is kept.
    expense = OWNER_H.items[12]
    check(expense.core,
          FuncDef("𝛷",
                  [Coordinate("h", None, [dom("ℝ₊")]),
                   Coordinate("h_n", None, [dom("ℝ₊")])],
                  Mul(Add(Call("step", [Sub(sym("h_n"), sym("h"))]),
                          Call("step", [Sub(sym("h"), sym("h_n"))])),
                      Sub(Mul(Add(Number(1), sym("φ")), sym("h_n")),
                          sym("h")))),
          "owner_housing.housing_expense")
    assert [e.value for e in expense.annot.entries
            if isinstance(e, KeyValue)] == ["housing_expense"]
    assert isinstance(expense.annot.entries[1], Tag)


def test_owner_budget_and_its_derivative():
    # w_own = (1 + r)*a_d - 𝑇(a_d) + y_d - 𝛷(H_d, H_new)
    transition = block(OWNER_H.items, "dcsn_to_cntn")
    # The decision states are typed here, the first header that lists them.
    check(transition.tag.entries[1].typing.source,
          Subject([Coordinate("a_d", None, [dom("ℝ₊")]),
                   Coordinate("H_d", None, [dom("ℝ₊")]),
                   Coordinate("y_d", None, [dom("ℝ₊₊")]),
                   Coordinate("H_new", None, [Domain(Named("XH")), Role(Control())])]),
          "owner_housing.dcsn_to_cntn.source")
    check(transition.body[0].core,
          Equation(sym("w_own"),
                   Sub(Add(Sub(Mul(Add(Number(1), sym("r")), sym("a_d")),
                               Call("𝑇", [sym("a_d")])),
                           sym("y_d")),
                       Call("𝛷", [sym("H_d"), sym("H_new")]))),
          "owner_housing.dcsn_to_cntn.owner_budget")
    # The backward block passes the value through, and the derivative line
    # the addition appends to it, in the block `cntn_to_dcsn` of `methods.bl`,
    # turns the derivative in cash into a derivative in assets with the
    # derivative of that budget.
    body = block(OWNER_H.items, "cntn_to_dcsn").body + marginal_lines("owner_housing")
    assert ids(block(OWNER_H.items, "cntn_to_dcsn").body) == ["value"]
    assert ids(body) == ["value", "marginal"]
    check(body[0].core, Equation(sym("V"), at_var("V", Continuation)),
          "owner_housing.cntn_to_dcsn.value")
    check(body[1].core,
          Equation(Operator("D", [Var("a_d")], [sym("V")]),
                   Mul(Sub(Add(Number(1), sym("r")),
                           Call("𝑑𝑇", [sym("a_d")])),
                       Operator("D", [Var("w_own")], [at_var("V", Continuation)]))),
          "owner_housing.cntn_to_dcsn.marginal")


def test_renter_budget_and_the_two_discrete_policies():
    # w_rent = w_d + y_d - P_r*S: the renter adds income and pays the rent.
    check(block(RENTER_H.items, "dcsn_to_cntn").body[0].core,
          Equation(sym("w_rent"),
                   Sub(Add(sym("w_d"), sym("y_d")), Mul(sym("P_r"), sym("S")))),
          "renter_housing.dcsn_to_cntn.renter_budget")
    # Both discrete policies maximise the continuation value over the control's
    # declared set, with the continuation value as the only input.
    for ast, name, control, space in ((OWNER_H, "owner_housing", "H_new", "XH"),
                                      (RENTER_H, "renter_housing", "S", "XS")):
        policy = block(ast.items, "policy")
        sig = policy.tag.entries[1].typing
        check(sig.source,
              Subject([Coordinate("V", At(Continuation()), [extended_real(), VLU])]),
              f"{name}.policy.source")
        check(sig.target,
              Subject([Coordinate(control, None, [Domain(Named(space)),
                                                  Role(Control())])]),
              f"{name}.policy.target")
        check(policy.body[0].core,
              Equation(sym(control),
                       Operator("argmax", [Var(control)],
                                [at_var("V", Continuation)])),
              f"{name}.policy.choice")


# --- owner_cons.bl and renter_cons.bl ---------------------------------------


def test_utility_and_the_feasible_set():
    # 𝑢(c, h) = α*log(c) + (1 - α)*log(κ*(h + ι)), with its derivative in
    # consumption and that derivative's inverse written in closed form, and Γ
    # the feasible set of consumption at cash x (D19).
    for ast, name in ((OWNER_C, "owner_cons"), (RENTER_C, "renter_cons")):
        first = 5 if name == "owner_cons" else 6
        check(ast.items[first].core,
              FuncDef("𝑢", [Coordinate("c", None, [dom("ℝ₊₊")]),
                            Coordinate("h", None, [dom("ℝ₊")])],
                      Add(Mul(sym("α"), Call("log", [sym("c")])),
                          Mul(Sub(Number(1), sym("α")),
                              Call("log", [Mul(sym("κ"),
                                               Add(sym("h"), sym("ι")))])))),
              f"{name}.util")
        check(ast.items[first + 1].core,
              FuncDef("𝑑𝑢", [Coordinate("c", None, [dom("ℝ₊₊")])],
                      Div(sym("α"), sym("c"))),
              f"{name}.marg_util")
        check(ast.items[first + 2].core,
              FuncDef("𝑑𝑢𝑖𝑛𝑣", [Coordinate("x", None, [dom("ℝ₊₊")])],
                      Div(sym("α"), sym("x"))),
              f"{name}.inv_marg_util")
        check(ast.items[first + 3].core,
              CorrDef("Γ", [Coordinate("x", None, [dom("ℝ₊₊")])],
                      Interval(Range(Open(), Number(0), sym("x"), Closed()))),
              f"{name}.feasible")
    # Only the renter's stage declares the services scale.
    check(RENTER_C.items[5],
          Declare(Declaration(Subject([Coordinate("ϑ", None, [])]),
                              [dom("ℝ₊₊")], None),
                  describes("housing enjoyed per unit of rented services;"
                            " the printed model is the case ϑ = 1")),
          "renter_cons.items[5]")
    check(OWNER_C.items[1],
          Declare(Declaration(Subject([Coordinate("β", None, [])]),
                              [unit_open()], None),
                  describes("discount factor")),
          "owner_cons.items[1]")


def test_consumption_budgets_and_backward_blocks():
    # The owner keeps the house; the renter writes the zero stock it carries
    # forward, which is an equation of the stage and not a value in a
    # connector.
    check(block(OWNER_C.items, "dcsn_to_cntn").body,
          [Statement(Equation(sym("a_nxt_o"), Sub(sym("w_d"), sym("c"))),
                     Annotation([KeyValue("id", "savings")])),
           Statement(Equation(sym("H_nxt_o"), sym("H_d")), None),
           Statement(Equation(sym("y_nxt_o"), sym("y_d")), None)],
          "owner_cons.dcsn_to_cntn.body")
    renter = block(RENTER_C.items, "dcsn_to_cntn").body
    check(renter[0].core, Equation(sym("a_nxt_r"), Sub(sym("w_d"), sym("c"))),
          "renter_cons.dcsn_to_cntn.savings")
    check(renter[1].core, Equation(sym("H_nxt_r"), Number(0)),
          "renter_cons.dcsn_to_cntn.no_housing")
    # The Bellman line and the envelope condition, the second in the marginal
    # block of the decision value builder. The continuation value is the
    # arrival value of the next period's tenure stage, which already holds the
    # expectation over income, so no expectation is written here. The
    # renter's services enter utility scaled by ϑ.
    check(block(OWNER_C.items, "cntn_to_dcsn").body + marginal_lines("owner_cons"),
          [Statement(Equation(sym("V"),
                              Add(Call("𝑢", [sym("c"), sym("H_d")]),
                                  Mul(sym("β"), at_var("V", Continuation)))),
                     Annotation([KeyValue("id", "value")])),
           Statement(Equation(Operator("D", [Var("w_d")], [sym("V")]),
                              Call("𝑑𝑢", [sym("c")])),
                     Annotation([KeyValue("id", "marginal")]))],
          "owner_cons.cntn_to_dcsn.body")
    assert len(block(OWNER_C.items, "cntn_to_dcsn").body) == 1
    check(block(RENTER_C.items, "cntn_to_dcsn").body[0].core,
          Equation(sym("V"),
                   Add(Call("𝑢", [sym("c"), Mul(sym("ϑ"), sym("S_d"))]),
                       Mul(sym("β"), at_var("V", Continuation)))),
          "renter_cons.cntn_to_dcsn.value")


def test_consumption_policy_blocks():
    for ast, name, services, saving in (
            (OWNER_C, "owner_cons", sym("H_d"), "a_nxt_o"),
            (RENTER_C, "renter_cons", Mul(sym("ϑ"), sym("S_d")), "a_nxt_r")):
        policy = block(ast.items, "policy")
        sig = policy.tag.entries[1].typing
        # The input is the continuation value and no continuation state
        # (D22).
        check(sig.source,
              Subject([Coordinate("V", At(Continuation()), [extended_real(), VLU])]),
              f"{name}.policy.source")
        check(sig.target,
              Subject([Coordinate("c", None, [dom("ℝ₊₊"), Role(Control())])]),
              f"{name}.policy.target")
        # The stage file's policy block holds the maximization, and the
        # addition's block of the same id holds the three lines of the method.
        body = policy.body + block(ADDITIONS[name].items, "policy").body
        assert ids(policy.body) == ["optimality"]
        assert ids(body) == ["optimality", "InvEuler", "endoggrid",
                             "cons_choice"]
        # The declarative maximization binds the control's own name to its
        # feasible set (D19).
        check(body[0],
              Statement(Equation(sym("c"),
                                 Operator("argmax",
                                          [In("c", Call("Γ", [sym("w_d")]))],
                                          [Add(Call("𝑢", [sym("c"), services]),
                                               Mul(sym("β"),
                                                   at_var("V", Continuation)))])),
                        Annotation([KeyValue("id", "optimality")])),
              f"{name}.policy.optimality")
        # The inverse Euler statement is an inequality: the candidate is single
        # valued at a positive saving and a segment where the borrowing
        # constraint binds (D20).
        check(body[1],
              Statement(Inequality(at_var("c", Continuation), Le(),
                                   Call("𝑑𝑢𝑖𝑛𝑣", [Mul(sym("β"),
                                                      Operator("D", [Var(saving)],
                                                               [at_var("V", Continuation)]))])),
                        Annotation([KeyValue("id", "InvEuler")])),
              f"{name}.policy.InvEuler")
        # The endogenous grid and the identification of the control with the
        # candidate at the saving the budget implies.
        check(body[2].core,
              Equation(at_var("w_d", Continuation),
                       Add(sym(saving), at_var("c", Continuation))),
              f"{name}.policy.endoggrid")
        check(body[3].core,
              Equation(sym("c"), at_var("c", Continuation)),
              f"{name}.policy.cons_choice")


# --- the typing entries of the additions ------------------------------------


def test_additions_type_the_methods_at_their_places():
    # The owner's addition writes the absolute subjects and one refined entry
    # per stored object; the renter's the relative subjects and one unrefined
    # pair for both. Each grid names the cash or the savings coordinate alone:
    # the housing, the rented services and the income take the default.
    for name, file in ADDITIONS.items():
        check(file.items[0], Metadata("methods", name), f"{name}/methods.bl items[0]")
    savings = {"owner_cons": "a_nxt_o", "renter_cons": "a_nxt_r"}
    check(block(ADDITIONS["owner_cons"].items, "policy").tag,
          Annotation([KeyValue("id", "policy"),
                      typed(path("policy", "method"), EGM),
                      typed(path("policy", "grid"),
                            cartesian(spaced(savings["owner_cons"], "a_nxt_min", "a_nxt_max", "a_nxt_points")))]),
          "owner_cons/methods.bl policy.tag")
    check(block(ADDITIONS["renter_cons"].items, "policy").tag,
          Annotation([KeyValue("id", "policy"),
                      typed(path("method"), EGM),
                      typed(path("grid"),
                            cartesian(spaced(savings["renter_cons"], "a_nxt_min", "a_nxt_max", "a_nxt_points")))]),
          "renter_cons/methods.bl policy.tag")
    value_at = Key("V")
    marginal_at = Term(Operator("D", [Var("w_d")], [sym("V")]))
    refined = [typed(path("evaluate", "method", at=value_at), word("Linear")),
               typed(path("evaluate", "grid", at=value_at), CASH),
               typed(path("evaluate", "method", at=marginal_at), word("Linear")),
               typed(path("evaluate", "grid", at=marginal_at), CASH)]
    check(block(ADDITIONS["owner_cons"].items, "cntn_to_dcsn").tag,
          Annotation([KeyValue("id", "cntn_to_dcsn")] + refined),
          "owner_cons/methods.bl cntn_to_dcsn.tag")
    check(block(ADDITIONS["renter_cons"].items, "cntn_to_dcsn").tag,
          Annotation([KeyValue("id", "cntn_to_dcsn"),
                      typed(path("evaluate", "method"), word("Linear")),
                      typed(path("evaluate", "grid"), CASH)]),
          "renter_cons/methods.bl cntn_to_dcsn.tag")
    # The housing stages and the tenure choice type their discrete choice at
    # file level, since the policy builder gains no line; the tenure choice
    # names the expectation over the income chain through the line `value`.
    check(typing_lines(ADDITIONS["owner_housing"].items),
          [selection(path("policy", "method"), word("discrete_choice"))],
          "owner_housing/methods.bl typing lines")
    check(typing_lines(ADDITIONS["tenure_choice"].items),
          [selection(path("policy", "method"), word("discrete_choice")),
           selection(path("dcsn_to_arvl", "value", "E_y", "method"), word("markov"))],
          "tenure_choice/methods.bl typing lines")
    check(block(ADDITIONS["tenure_choice"].items, "cntn_to_dcsn").tag,
          Annotation([KeyValue("id", "cntn_to_dcsn"),
                      typed(path("evaluate", "method"), word("Linear")),
                      typed(path("evaluate", "grid"),
                            cartesian(spaced("a_d", "a_min", "a_max", "a_points")))]),
          "tenure_choice/methods.bl cntn_to_dcsn.tag")
    # The alternative by value function iteration stands on the decision
    # value builder with the count of its dense grid as a feasible factor of
    # the control, and restates the two representations.
    check(VFI.items[0], Metadata("methods", "owner_cons"), "methods.vfi.bl items[0]")
    check(block(VFI.items, "cntn_to_dcsn").tag,
          Annotation([KeyValue("id", "cntn_to_dcsn"),
                      typed(path("method"), word("vfi")),
                      typed(path("grid"), Grid(Cartesian(factors=(
                          Feasible(coordinate="c", set="Γ", count=Name(name="N_arg_grid_vfi")),))))]
                     + refined),
          "methods.vfi.bl cntn_to_dcsn.tag")
    assert ids(block(VFI.items, "cntn_to_dcsn").body) == ["marginal"]


if __name__ == "__main__":
    sys.exit(run_checks(globals(), "on the five housing-renting stages and their additions"))
