"""Candidate clauses, their admitted values, and policy identification.

The explicit consumption fixture reads the authored inverse Euler equation
with its complementarity clause. Numerical checks retain the admitted pairs,
the empty-solution counterexample, every one-sided and chained bound, and the
durable-adjustment membership conditions. The shared `at_numbers` fixture
reads supplied derivatives and evaluates relations; it differentiates nothing.
Printed checks retain carriers, clause placement and source statements. The
application's complete `cons_obs` card is also held by the snapshot guard.
"""
import itertools
import re
from fractions import Fraction

import pytest

from bellman.native.hypergraphs import copy_native
from bellman.native.predicates import Member
from bellman.refusals import ConstructionError
from bellman.stage.boxes import kind_of
from bellman.stage.stage_answers import obligations
from bellman.stage.term_operations import kuhn_tucker
from bellman.typing import typed_expressions as S
from conftest import (GRID_LINE, ROOT, STAGE_FILES, builder_cards, candidate_text, flat,
                      grid_line_text, name_at_numbers, reads, section, stage_from_text,
                      terms_inside)
from sheets_parse import operations_entries

# --- item 1 ---

# the relation the identification's `signature()` answers, without its white
# space: the saving over Xa, each value the candidate admits there, and the
# grid line read at that value; one quantifier or two, the parentheses of its
# statement written or not
OVER_THE_ADMITTED_PAIRS = re.compile(r"∀a∈Xa,(∀)?x∈𝑐≻\(a\):\(?f\(a\+x\)=x\)?")

# the moved item 1 of AMD-SG-035: a representation of the policy at the
# Evaluation that closes the policy builder, which binds on every spelling and
# leaves every rule as it was
LINEAR = {"text": "@methods: cons_kt\npolicy.evaluate.method : !Linear\n",
          "origin": "cons_kt.methods.bl"}

def test_item_1_the_policy_card_of_cons_prints_as_drawn_and_the_identification_answers_the_relation_over_the_admitted_pairs(
        cons_candidate, cons_kt, cons_obs):
    cons = cons_candidate
    policy = cons.builder.policy
    assert [str(key) for key in policy.primitives.list()] == [
        "InvEuler:Aggregation", "endoggrid:Aggregation", "cons_choice:Pullback", "Evaluation"]
    # the candidate and the cash on hand are correspondences of the saving:
    # at zero saving each takes every value the clause admits; the candidate
    # is typed so on its piece card and in its signature (the ruling on the
    # carrier of 𝑐≻, 27 September 2026)
    assert flat("out 𝑐≻ : Xa ⇉ ℝ₊₊") in flat(str(policy["InvEuler:Aggregation"]))
    assert flat("out 𝑐≻ : Xa ⇉ ℝ₊₊") in flat(str(policy["InvEuler:Aggregation"].signature()))
    assert flat("out 𝑚_d≻ : Xa ⇉ Xm") in flat(str(policy["endoggrid:Aggregation"]))
    # the identification relates the policy and the candidate over the
    # admitted pairs, the grid line read at each admitted value, and not over
    # the images of the two correspondences
    relation = flat(str(policy["cons_choice:Pullback"].signature()))
    assert OVER_THE_ADMITTED_PAIRS.search(relation), relation
    assert "f(𝑚_d≻(a))" not in relation

    # spelling A, `cons_kt`: one Aggregation after the Pullback, its rule the
    # clause read at the point, no Where section and no optimality condition;
    # a representation bound at the Evaluation changes no rule
    policy = cons_kt.builder.policy
    assert [str(key) for key in policy.primitives.list()] == ["Pullback", "euler:Aggregation", "Evaluation"]
    printed = "\n".join(section(str(policy), "Operations"))
    assert flat("𝑑𝑢(𝑐(m_d))") in flat(printed)
    assert flat("⟂ m_d − 𝑐(m_d) ≥ 0") in flat(printed)
    clause = next(line for line in printed.splitlines() if "⟂" in line)
    assert clause.rstrip().endswith("on Xm") and section(str(policy), "Where") == []
    assert "optimality" not in [item.condition for item in obligations(cons_kt)]
    methodized = copy_native(cons_kt).methodize(LINEAR)
    assert [box for box, method in methodized.methods.items() if method.word == "!Linear"] == [
        "policy.evaluate"]
    assert "\n".join(section(str(methodized.builder.policy), "Operations")) == printed
    assert [item.condition for item in obligations(methodized)] == [item.condition for item in obligations(cons_kt)]

    # spelling B, `cons_obs`: typed on the observable set and printed as
    # drawn; its identification quantifies once over the observable set and,
    # at each of its pairs, over the consumption that 𝑐≻ gives there
    policy = cons_obs.builder.policy
    aggregation = str(policy.primitives["endoggrid:Aggregation"])
    assert "𝑉≻" in aggregation
    assert aggregation.count("{a, μ ∈ Xa × ℝ₊ | a ≥ 0 ∧ μ · a = 0} → ") == 2
    relation = S.format_expression(policy.primitives["cons_choice:Pullback"].denote().expression, width=None)
    assert "∀ (a, μ) ∈ {a, μ ∈ Xa × ℝ₊ | a ≥ 0 ∧ μ · a = 0}, x ∈ " in relation
    assert "∈ Xa × ℝ₊:" not in relation and "μ ∈ ℝ₊:" not in relation


# --- items 2 and 3: the relation and the clause at numbers ---

# the calibration of items 2 and 3, ρ = 2 (with the continuation marginal
# value D_{a}𝑉≻ ≡ 1, the interior value 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) is 1 at every saving: 𝑐≻(a)
# is 1 and 𝑚_d≻(a) is a + 1 at a positive saving, and at zero saving the two
# take every value of the segment (0, 1] together)
RHO = {"ρ": 2}
# the pairs (cash on hand, consumption) that item 2 names, each at its saving,
# with whether the relation of `cons.bl` holds it and whether the relation of
# the file without the clause holds it. The sixth, (1/2, 1/4), is the value of
# 𝑐(x) = x²/m̄ at x = 1/2 with m̄ = 1: 1/2 is the cash on hand of an admitted
# value at zero saving and 1/4 an admitted value there, so the relation read
# over the images of the two correspondences would hold it, and the relation
# over the admitted pairs does not
PAIRS = (
    (0, (Fraction(1, 2), Fraction(1, 2)), True, False),
    (0, (Fraction(1, 4), Fraction(1, 4)), True, False),
    (0, (1, 1), True, True),
    (1, (2, 1), True, True),
    (1, (Fraction(3, 2), Fraction(1, 2)), False, False),
    (0, (Fraction(1, 2), Fraction(1, 4)), False, False),
    (0, (Fraction(3, 2), Fraction(3, 2)), False, False),
)


def identification(stage):
    """The relation the identification of a stage's policy builder holds, the
    set of policies its `signature()` answers."""
    return stage.builder.policy["cons_choice:Pullback"].denote().outputs[0].expression


def test_item_2_the_relation_holds_exactly_the_admitted_pairs_and_its_solution_set_can_be_empty(
        cons_candidate, cons_head, at_numbers):
    cons = cons_candidate
    for stage, column in ((cons, 2), (cons_head, 3)):
        numbers = at_numbers.rows(stage.builder.policy, at_numbers.stage(stage, {**RHO, "D_{a}V≻": lambda a: 1}))
        relation = identification(stage)
        held = [at_numbers.demand(relation, {**numbers, "a": a, "x": pair[1]}) == pair for a, pair, *_ in PAIRS]
        assert held == [case[column] for case in PAIRS], stage.name
    # the counterexample of the independent review of the plan (correction 2):
    # at ρ = 2 and D_{a}𝑉≻(a) = (1 − 2a)⁻² on [0, 1/4], the interior value at the
    # saving 1/8 is 3/4 and the corner at zero saving admits 7/8; both give the
    # cash on hand 7/8, and the relation demands 𝑐(7/8) = 3/4 and 𝑐(7/8) = 7/8,
    # which no function meets
    numbers = at_numbers.rows(cons.builder.policy, at_numbers.stage(
        cons, {**RHO, "D_{a}V≻": lambda a: (1 - 2 * Fraction(a)) ** -2}))
    demands = [at_numbers.demand(identification(cons), {**numbers, "a": a, "x": x})
               for a, x in ((Fraction(1, 8), Fraction(3, 4)), (0, Fraction(7, 8)))]
    assert demands == [(Fraction(7, 8), Fraction(3, 4)), (Fraction(7, 8), Fraction(7, 8))]
    assert not at_numbers.one_function(demands) and at_numbers.one_function(demands[:1])


# the cores and the bounds of item 3, each written on the candidate line of
# `cons.bl`: the five relations of a core, with the four one-bound clauses of
# the saving and its cap 2, and, after an equation, the two-bound chain
# ascending and with its endpoints reversed; a chain after an inequality is
# refused under `readable-form` and has no reading
CORES = ("=", "<=", ">=", "<", ">")
ONE_BOUND = ("a >= 0", "a > 0", "a <= 2", "a < 2")
CHAINS = ("0 <= a <= 2", "2 <= a <= 1")
# the savings and the consumptions item 3 reads each clause at: the slack of
# each bound takes both signs and zero, and so does the residual, the
# consumption less the interior value 1
SAVINGS = (-1, 0, 1, 2, 3)
CONSUMPTIONS = (Fraction(1, 2), 1, Fraction(3, 2), 2)


def clause_condition(stage):
    """The Kuhn–Tucker condition of the clause of the candidate line, as the
    definitions table holds the line written, and its regions."""
    # the split of a clause into its regions, read here alone
    from bellman.typing.ranges import clause_regions

    line = stage.definitions["policy.InvEuler"].equations[0]
    condition = kuhn_tucker(line.core, line.bound)
    return condition, clause_regions(condition)


def test_item_3_the_split_of_a_clause_and_its_kuhn_tucker_condition_agree_at_numbers(cons_cap, at_numbers):
    written = [(core, bound) for core in CORES for bound in ONE_BOUND] + [("=", chain) for chain in CHAINS]
    for core, bound in written:
        line = f"    c[>]   {core} 𝑑𝑢𝑖𝑛𝑣(D_{{a}}V[>]) ⟂ {bound}           :: [id=InvEuler]\n"
        stage = stage_from_text(candidate_text("clause", line), "clause.bl")
        numbers = at_numbers.stage(stage, {**RHO, "D_{a}V≻": 1})
        condition, regions = clause_condition(stage)
        for a, x in itertools.product(SAVINGS, CONSUMPTIONS):
            point = {**numbers, "a": a, "c≻": x}
            assert at_numbers(regions, point) == at_numbers(condition, point), (core, bound, a, x)
        if (core, bound) == ("<", "a >= 0"):
            # a strict core admits no zero residual and so has no interior
            # region: at the residual 0 and the slack 1 both forms reject, and
            # the regions admit no point of positive saving
            point = {**numbers, "a": 1, "c≻": 1}
            assert not at_numbers(condition, point) and not at_numbers(regions, point)
            assert not any(at_numbers(regions, {**numbers, "a": a, "c≻": x})
                           for a, x in itertools.product((1, 2, 3), CONSUMPTIONS))
        if bound == "2 <= a <= 1":
            # the chain with its endpoints reversed, the lower bound 2 above
            # the upper bound 1: at the bounded quantity 2 and the residual 1
            # the lower slack is zero and the upper slack negative, and both
            # forms reject; no saving meets both bounds, so neither form
            # admits any point
            point = {**numbers, "a": 2, "c≻": 2}
            assert not at_numbers(condition, point) and not at_numbers(regions, point)
            assert not any(at_numbers(regions, {**numbers, "a": a, "c≻": x})
                           for a, x in itertools.product(SAVINGS, CONSUMPTIONS))
    # the cap written as the chain on the bounded quantity −a, the fourth
    # trial of the two-sided bound (`cap-v3-reversed.bl`): at ā = 2 and the
    # saving 2 the cap binds, the residual is nonnegative, and the value 3 is
    # admitted and the value 1/2 is not
    numbers = at_numbers.stage(cons_cap, {**RHO, "ā": 2, "D_{a}V≻": 1})
    for form in clause_condition(cons_cap):
        assert at_numbers(form, {**numbers, "a": 2, "c≻": 3})
        assert not at_numbers(form, {**numbers, "a": 2, "c≻": Fraction(1, 2)})


# --- item 4: the durables membership ---

# the durables adjuster with the clause `⟂ a_nxt_adj >= 0` on its candidate
# line, read at numbers under which every value of the item is exact: the
# utility of the file with α = 1/2, γ_c = γ_h = 2 and κ = 1, so that
# 𝑢_c(c) = 1/(2c²), 𝑢_h(h) = 1/(2h²) and 𝑢_c_inv(x) = (1/(2x))^(1/2); the
# adjustment cost τ = 1; the discount factor β = 1/2; the borrowing limit
# b = 0 the clause writes; and the continuation value
# 𝑉≻(a, h, z) = ln(1 + a) + ln h, so that its derivatives, under the names
# the held terms give them, are D_{a_nxt_adj}V≻(a, h, z) = 1/(1 + a) and
# D_{h_nxt_adj}V≻(a, h, z) = 1/h
DURABLES = {"α": Fraction(1, 2), "γ_c": 2, "γ_h": 2, "κ": 1, "τ": 1, "β": Fraction(1, 2),
            "D_{a_nxt_adj}V≻": lambda a, h, z: 1 / (1 + Fraction(a)),
            "D_{h_nxt_adj}V≻": lambda a, h, z: 1 / Fraction(h)}
BORROWING_LIMIT = 0
# the two housing choices h′ of the item at the borrowing limit, each with the
# consumption c* at which the housing condition
# (1 + τ)·𝑢_c(c) = 𝑢_h(h′) + β·𝑑𝑉_h≻(b, h′, z′) holds, the decision point
# (m, z_d, c, h_choice) whose saving is b, m = c* + b + (1 + τ)·h′, and
# whether c* passes the test of line 469 of AAS's durables solver,
# 𝑢_c(c*) ≥ β·𝑑𝑉_a≻(b, h′, z′): at h′ = 1/8, c* = 1/6 lies in the segment
# (0, 1] and passes; at h′ = 7/2, c* = 7/3 lies above it and fails
HOUSING_CHOICES = (
    (Fraction(1, 8), Fraction(1, 6), (Fraction(5, 12), 1, Fraction(1, 6), Fraction(1, 8)), True),
    (Fraction(7, 2), Fraction(7, 3), (Fraction(28, 3), 1, Fraction(7, 3), Fraction(7, 2)), False),
)


def test_item_4_the_first_residual_of_the_durables_solve_reads_as_membership_in_the_admitted_set(
        adjuster_cons_clause, at_numbers):
    policy = adjuster_cons_clause.builder.policy
    numbers = at_numbers.rows(policy, at_numbers.stage(adjuster_cons_clause, DURABLES))
    admitted = numbers["c≻"]
    # at a positive saving the candidate alone is admitted,
    # 𝑢_c_inv(β·𝑑𝑉_a≻(3, h′, z′)) = 𝑢_c_inv(1/8) = 2; at the borrowing limit the
    # segment (0, 𝑢_c_inv(β)] = (0, 1]
    assert [admitted(3, Fraction(1, 8), 1)(x) for x in (1, 2, 3)] == [False, True, False]
    assert [admitted(BORROWING_LIMIT, Fraction(1, 8), 1)(x) for x in (Fraction(1, 6), 1, Fraction(7, 3))] == [
        True, True, False]
    # the first residual, read as the membership of the control in the
    # candidate's admitted values, wherever the solve's rules hold it, and the
    # second, the rule whose left side is r₂
    rules = policy["choice:Aggregation"].denote().outputs[0].rules
    memberships = [term for rule in rules for term in terms_inside(rule)
                   if isinstance(term, Member) and reads(term, "c≻")]
    assert memberships and all(term == memberships[0] for term in memberships)
    (housing,) = [rule for rule in rules if name_at_numbers(getattr(rule.statement, "left", None)) == "r₂"]

    def at(m, z_d, c, h_choice):
        """The numbers at a decision point, with the outputs of the law of
        motion there under the names the line under Where gives them."""
        a, h, z = numbers["dcsn_to_cntn"](m, z_d, c, h_choice)
        return {**numbers, "m": m, "z_d": z_d, "c": c, "h_choice": h_choice,
                "a_nxt_adj": a, "h_nxt_adj": h, "z_nxt_adj": z}

    for h, c_star, (m, z_d, c, h_choice), passes in HOUSING_CHOICES:
        assert numbers["dcsn_to_cntn"](m, z_d, c, h_choice) == (BORROWING_LIMIT, h, z_d)
        # the housing condition holds at c*: the second residual is zero
        assert at_numbers.rule(housing, {**at(m, z_d, c, h_choice), "r₂": 0})
        # the test of line 469 and the membership agree: the constrained
        # point is added where the test passes and not where it fails
        test = numbers["𝑢_c"](c_star) >= numbers["β"] * DURABLES["D_{a_nxt_adj}V≻"](BORROWING_LIMIT, h, z_d)
        assert test is passes and at_numbers(memberships[0], at(m, z_d, c, h_choice)) is passes, h
    # at a positive saving the membership holds at the candidate alone
    for c, holds in ((2, True), (1, False)):
        point = at(c + 3 + 2 * Fraction(1, 8), 1, c, Fraction(1, 8))
        assert at_numbers(memberships[0], point) is holds
    # the residual is printed through the names of the law's outputs, which
    # the line under Where gives once
    card = str(policy)
    assert flat("\n".join(section(card, "Where"))) == flat(
        "Where (a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔≻(m, z_d, c, h_choice)")
    operations = flat("\n".join(section(card, "Operations")))
    assert flat("c ∈ 𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)") in operations
    assert flat("D_{h_nxt_adj}𝑉≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)") in operations


# --- item 5: the names of a law's outputs, the pension card and the grid lines ---

# the stage fixtures of `conftest.py` whose builder cards item 5 reads: the
# corpus stages, the saving stages of Dobrescu and Shanker (2024), the
# durables adjuster with and without its clause, the branching stages, the
# stages of the preliminary applications the suite reads, and the twin texts
# of the clause
CARD_STAGES = ("cons", "cons_obs", "port", "ez_savings", "cons_savings_iid", "sa_savings", "tenure",
               "retiree_death", "worker_saving", "retiree_saving", "keeper_saving", "adjuster_saving",
               "adjuster_cons", "adjuster_cons_clause", "ret_choice", "house_choice", "young_choice",
               "old_choice", "worker_ageing", "entrepreneur_death", "entrepreneur_ageing", "fecundity",
               "buffer_stock", "mckenzie", "cons_kt", "cons_argmax", "cons_head", "cons_cap")
# a grid line: a line whose left side names a field under the continuation
# mark, other than a value, a marginal value or the candidate, and whose right
# side reads the candidate `c[>]`
GRID = re.compile(r"^\s*(?!(?:V|dV\w*|v|c)\[)(?P<field>\w+)\[>\]\s*=(?!=)[^:]*c\[>\]")
# the grid lines under `applications/` whose files elaborate, by file and line;
# buffer-stock, the two consumption stages of retirement-choice,
# consumption-savings-iid, benhabib-2019 and the two consumption stages of
# housing-renting and of durables write theirs in their methods files, the
# additions beside the stage files or the block files under
# `declaration/methods/`, which STAGE_FILES does not read (decisions MB-S18,
# MB-V7, MB-U12)
GRID_LINES = {
    "applications/portfolio-choice/declaration/stages/cons_obs/cons_obs.bl": 34,
}
# the files with a grid line that stand refused under a rule of an earlier
# amendment, before the construction reads their grid lines, by file, line
# and rule; none since the grid line of the housing owner's consumption stage
# moved to the method block of consumption_choice_egm.bl (decision MB-U47)
REFUSED_BEFORE = {}


@pytest.mark.sweep
def test_item_5_only_a_pullback_writes_the_law_on_a_card_with_a_where_line_and_every_grid_line_agrees_with_its_law(
        request, worker_saving):
    # on every card with a Where line, no entry but a Pullback writes the law
    # of motion
    written = []
    for name in CARD_STAGES:
        for builder, card in builder_cards(request.getfixturevalue(name)):
            if not section(card, "Where"):
                continue
            # the kind of each entry, read from the builder and not from the printed key
            kinds = {str(key): kind_of(builder.primitives[str(key)].box) for key in builder.primitives.list()}
            for entry in operations_entries(section(card, "Operations")[1:]):
                if kinds.get(entry["key"]) != "Pullback" and "𝑔≻(" in "\n".join(entry["lines"]):
                    written.append((name, card.splitlines()[0], entry["key"]))
    assert written == []

    # the pension worker's card: the first clause's bound by the name of the
    # law's output, `y_f ≥ 0`, with the law's line once under Where and no
    # projection; its two lines one Aggregation, each clause printed once.
    # The law's line is read at the policy, whose controls print bare at the
    # point of several coordinates, `𝑔≻(m_f, m_p, w_d, 𝑐, 𝑐_p)` (card-redesign
    # §2 change 4 and §3; CL151 and CL155 of the release's decisions)
    bound_worker = copy_native(worker_saving).methodize(
        ROOT / "applications/pension-retirement/declaration/stages/worker_saving/methods.bl")
    policy = bound_worker.builder.policy
    card = str(policy)
    where = "\n".join(section(card, "Where"))
    assert flat(where) == flat("Where (y_f, y_p) = 𝑔≻(m_f, m_p, w_d, 𝑐, 𝑐_p)") and where.count("𝑔≻(") == 1
    operations = "\n".join(section(card, "Operations"))
    assert flat("⟂ m_f − 𝑐 − 𝑐_p ≥ 0") in flat(operations) and "[1]" not in card
    keys = [str(key) for key in policy.primitives.list()]
    assert [key for key in keys if key.startswith("euler")] == ["euler_financial:Aggregation"]
    assert not any(key.endswith(("Inversion", "Solution")) for key in keys)
    assert operations.count("⟂") == 2 and "∧" in operations
    # the controls at the point of several coordinates print bare, with the
    # point in the region note (card-redesign §2, change 4)
    assert flat("⟂ 0 ≤ 𝑐_p ≤ w_d") in flat(operations)
    assert flat("on (m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊") in flat(operations)

    # every grid line under `applications/` is its law of motion solved for
    # the decision state at the candidate: its file elaborates, or stands
    # refused under a rule of an earlier amendment, and none is refused under
    # `grid-line-consistency`
    found = {str(path.relative_to(ROOT)): number for path in STAGE_FILES
             for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if GRID.match(line)}
    assert found == {**GRID_LINES, **{path: line for path, (line, _) in REFUSED_BEFORE.items()}}
    for path in found:
        text = (ROOT / path).read_text(encoding="utf-8")
        if path in REFUSED_BEFORE:
            with pytest.raises(ConstructionError) as refused:
                stage_from_text(text, path)
            assert refused.value.rule == REFUSED_BEFORE[path][1], path
        else:
            assert stage_from_text(text, path).name, path

    # the grid line of `cons.bl` with its terms in the other order elaborates;
    # with the candidate doubled it is refused, and the message names the
    # line as written and the law solved for the decision state
    assert GRID_LINE == "    m_d[>] = a + c[>]                :: [id=endoggrid]\n"
    commuted = grid_line_text("cons_grid", GRID_LINE.replace("a + c[>]", "c[>] + a"))
    assert stage_from_text(commuted, "cons_grid.bl").name == "cons_grid"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(grid_line_text("cons_grid", GRID_LINE.replace("a + c[>]", "a + 2*c[>]")), "cons_grid.bl")
    assert (refused.value.rule, refused.value.address) == ("grid-line-consistency", "policy.endoggrid")
    assert flat("m_d[>] = a + 2*c[>]") in flat(refused.value.message)
    assert flat("m_d[>] = a + c[>]") in flat(refused.value.message)


# --- item 6: the correspondence carriers ---

def test_item_6_the_inverse_euler_example_types_candidate_and_cash_as_correspondences(elaborate_text):
    from bellman.refusal_examples import INVERSE_EULER
    stage = elaborate_text(INVERSE_EULER, "t.bl")
    signatures = flat(str(stage.builder.policy["InvEuler:Aggregation"].signature()) +
                      str(stage.builder.policy["grid:Aggregation"].signature()))
    assert flat("𝑐≻ : ℝ₊ ⇉ ℝ₊₊") in signatures
    assert flat("𝑚≻ : ℝ₊ ⇉ ℝ₊") in signatures
    assert flat("𝑐≻ : ℝ₊ → ℝ₊₊") not in signatures
    assert flat("𝑚≻ : ℝ₊ → ℝ₊") not in signatures


# --- the fixture that reads a held term at numbers ---

def test_the_fixture_reads_a_held_term_at_numbers(cons_candidate, adjuster_cons, at_numbers):
    """The fixture `at_numbers` of `conftest.py`, on the definitions of two
    stages, which lane C does not change, and on terms written here: the
    functions, the correspondence and the laws of motion of the files, the
    arithmetic exact where the roots are rational, a clause read as its
    Kuhn–Tucker condition, a relation's demand at one point of its
    quantifier, and a name the numbers do not give refused."""
    from bellman.native.predicates import Compare, Complementarity
    from bellman.syntax import terms as T

    def name(written):
        return T.Sym(T.Constant(written))

    cons = cons_candidate
    numbers = at_numbers.stage(cons, RHO)
    assert numbers["𝑑𝑢𝑖𝑛𝑣"](Fraction(16, 9)) == Fraction(3, 4) and numbers["𝑑𝑢𝑖𝑛𝑣"](1) == 1
    assert numbers["𝑑𝑢"](Fraction(1, 2)) == 4 and numbers["dcsn_to_cntn"](2, Fraction(1, 2)) == Fraction(3, 2)
    assert [numbers["Γ"](1)(x) for x in (0, Fraction(1, 2), 1, 2)] == [False, True, True, False]
    durables = at_numbers.stage(adjuster_cons, {**DURABLES, "τ": Fraction(1, 10)})
    assert durables["dcsn_to_cntn"](3, 1, 1, 1) == (Fraction(9, 10), 1, 1)
    assert durables["𝑢_c_inv"](Fraction(1, 8)) == 2 and durables["𝑢_h"](2) == Fraction(1, 8)
    # the clause `x ≤ 1 ⟂ a ≥ 0` admits 1 alone at a positive saving and every
    # value up to 1 at zero saving
    clause = Complementarity(Compare(name("x"), "<=", T.Number(1)), T.Rel(name("a"), T.Ge(), T.Number(0)))
    assert [at_numbers(clause, {"a": a, "x": x}) for a, x in ((1, 1), (1, Fraction(1, 2)), (0, Fraction(1, 2)),
                                                           (0, 2))] == [True, False, True, False]
    # the relation {f | ∀ a ∈ ℝ₊, ∀ x ∈ S(a): f(a + x) = x} demands f(a + x) = x
    # at each admitted pair and nothing elsewhere
    relation = T.Comprehension(T.Subject((name("f"),)), None, (T.Operator(
        "forall", (T.In(name("a"), T.Named("ℝ₊")), T.In(name("x"), S.Apply(name("S"), (name("a"),)))),
        (Compare(S.Apply(name("f"), (T.Add(name("a"), name("x")),)), "=", name("x")),)),))
    segment = {"S": lambda a: (lambda x: 0 < x <= 1 if a == 0 else x == 1)}
    assert at_numbers.demand(relation, {**segment, "a": 0, "x": Fraction(1, 2)}) == (Fraction(1, 2), Fraction(1, 2))
    assert at_numbers.demand(relation, {**segment, "a": 1, "x": Fraction(1, 2)}) is None
    assert at_numbers.demand(relation, {**segment, "a": -1, "x": 1}) is None
    assert at_numbers.one_function([(1, 1), (2, 1), None]) and not at_numbers.one_function([(1, 1), (1, 2)])
    with pytest.raises(KeyError):
        at_numbers(name("ρ"), {})
