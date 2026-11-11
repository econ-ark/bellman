"""The normalized `.bl` text of a term, which the refusals and the printed
forms of a stage quote.

`to_source(term)` writes an expression or a set expression of a stage — a
function body, the right side of a statement, a declared domain — as `.bl`
text that lowers back to an equal term. The text is for display: nothing in
the package parses it again, and the elaboration reads the terms. The form is
normalized. Whitespace and the choice among spellings the grammar treats alike
are not kept: `**` prints as `^`, the glyph `∞` as `inf`, and the decision
mark `x[~]` as the bare `x`. Parentheses are the fewest the grammar's
precedence allows (`grammars/stage.lark`): a sum is a sum of products, a
product a product of molecules, a power a power of two atoms, and a unary
minus applies to a product. A set with conditions that bound its own name
prints as a declaration writes it, the base and one interval for each bound
with `@` between them (`Tau @ [1, 10]`). A coupled condition prints with its
binder and base set, as a correspondence body
(`{u : ℝ × ℝ | u[1] + u[2] < x}`).

A top-level statement prints as the grammar writes it: a distribution
declaration as its subject or tuple of subjects, a tilde, and the family call
(`θ ~ LogNormal(μ_θ, σ_θ)`; `(Ψ, θ) ~ N((μ_Ψ, μ_θ), (…))`, the joint
distribution of the portfolio return and the income shock with its covariance
matrix as nested tuples); a function
definition as its name, its typed parameters, `:=`, and its body
(`𝑢(c : ℝ₊₊) := c^(1 - ρ)/(1 - ρ)`); a correspondence definition likewise with
a set body (`Γ(x : ℝ₊) := (0, x]`); an assignment as its name, `:=`, and its
value, a reserved set glyph (`Y := ℝ₊`), a finite set (`D := {work, retire}`),
a comprehension (`H := {i : ℤ | i >= 0, i <= 1}`), or an expression
(`𝑑𝑢 := D_{c}(𝑢)`).

The parts of a typing entry print as the entry writes them: the path of a
component (`policy.evaluate[V[<]].method`), a word with its keyword arguments
(`!egm(tol=tol_v)`), a grid as its one outer grid word with its arguments
(`!Cartesian(a=(a_min, a_max, n_a, !expmult))`, `!Points(nodes=P)`,
`!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))`), the
predicate words after `require` printed last, and the method or the grid
classifier as that word or grid.

The forms printed are those the corpus under `applications/` uses. A generated
constructor outside them raises `NotImplementedError` naming the constructor.
"""

from __future__ import annotations

import math
from itertools import zip_longest

from bellman.syntax import terms as T
from bellman.syntax.vocabulary import EXTENDED_REAL, PRIMITIVE_SETS

# The precedence levels of the grammar's expression ladder, lowest first: a
# position that requires at least a product parenthesizes a sum, and so on.
_SUM, _PRODUCT, _MOLECULE, _ATOM = 0, 1, 2, 3


def to_source(term) -> str:
    """The normalized `.bl` text of an expression, a set expression, or a
    block statement term.

    Lowering the text again (`bellman.syntax.lower.ToAst`) yields a term equal
    to `term`, for a term the lowering gives. A set with conditions is
    written as a declaration writes it, several sets with `@` between them,
    so its text is a type and is read as one after the colon of a
    declaration (`_intersection_text`). A constructor the corpus does not use
    raises `NotImplementedError` naming it. A statement is the core of a
    `Statement` item — an `Equation`, `lhs = rhs`; a `Slack`, an equation
    with its complementary-slackness clause
    `lhs = rhs ⟂ left <relation> right` or
    `lhs = rhs ⟂ lower <relation> middle <relation> upper`; a
    `Law`; a `FuncDef`; a `CorrDef`; an `Assignment` — and prints without its
    annotation, which the statement record keeps as tags; `PathAssignment`
    and `Residual`, which no stage file writes, are refused by name. A bound
    alone prints as the clause writes it, `a >= 0` or `0 <= c_p <= w_d`, and a
    multiplier declared in a block body as its declaration with its clause,
    `μ[>] : ℝ₊ ⟂ a >= 0`.
    """
    if isinstance(term, T.expr):
        return _expr(term, _SUM)
    if isinstance(term, T.setexpr):
        return set_text(term)
    if isinstance(term, T.stmt):
        return _statement(term)
    if isinstance(term, T.cond):
        return _clause(term)
    if isinstance(term, T.Complementary):
        return _complementary(term)
    if isinstance(term, T.Path):
        return _path(term)
    if isinstance(term, T.word):
        return _word(term)
    if isinstance(term, T.keyword):
        return _keyword(term)
    if isinstance(term, T.argument):
        return _argument(term)
    if isinstance(term, T.grid):
        return _grid(term)
    if isinstance(term, T.factor):
        return _factor(term)
    if isinstance(term, T.Method):
        return _word(term.m)
    if isinstance(term, T.Grid):
        return _grid(term.g)
    raise NotImplementedError(
        f"to_source prints an expression, a set expression, a block "
        f"statement, a bound, a declared multiplier, or a part of a typing entry; a "
        f"{type(term).__name__} is none of these"
    )


# --- the parts of a typing entry ---


def _path(path) -> str:
    """The path of a component as written, `policy.evaluate[V[<]].method`:
    its segments joined by dots, each with its selectors in brackets."""
    return ".".join(
        segment.name + "".join(f"[{_selector(sel)}]" for sel in segment.selectors)
        for segment in path.segments
    )


def _word(word) -> str:
    """A `!`-word with its keyword arguments, `!egm(tol=tol_v)`; a word
    without arguments prints bare, `!Linear`."""
    if not word.arguments:
        return "!" + word.name
    return "!" + word.name + "(" + ", ".join(_keyword(k) for k in word.arguments) + ")"


def _keyword(keyword) -> str:
    return f"{keyword.key}={_argument(keyword.value)}"


def _argument(value) -> str:
    """The value of a keyword argument: a name, a number, a quoted string, a
    tuple of values, or a nested word with its own arguments."""
    if isinstance(value, T.Name):
        return value.name
    if isinstance(value, T.Literal):
        return _number(value.value)
    if isinstance(value, T.Quoted):
        return f'"{value.text}"'
    if isinstance(value, T.Values):
        return "(" + ", ".join(_argument(item) for item in value.items) + ")"
    if isinstance(value, T.Nested):
        return _word(value.word)
    raise NotImplementedError(
        f"to_source has no rule for the argument constructor {type(value).__name__}"
    )


def _grid(grid) -> str:
    """A grid as its one outer grid word with its arguments, the predicate
    words after `require` last: `!Cartesian(a=(a_min, a_max, n_a))`,
    `!Points(nodes=P)`, `!Points` alone for the empty grid, and
    `!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))`."""
    if isinstance(grid, T.Cartesian):
        arguments = [_factor(factor) for factor in grid.factors]
    elif isinstance(grid, T.PointGrid):
        arguments = [] if grid.nodes is None else [f"nodes={grid.nodes}"]
    elif isinstance(grid, T.Fibred):
        arguments = [f"base={_grid(grid.base)}", f"fibre={_grid(grid.fibre)}"]
    else:
        raise NotImplementedError(
            f"to_source has no rule for the grid constructor {type(grid).__name__}"
        )
    if grid.require:
        words = [f"!{name}" for name in grid.require]
        arguments.append("require=" + (words[0] if len(words) == 1 else f"({', '.join(words)})"))
    return grid_word(grid) + (f"({', '.join(arguments)})" if arguments else "")


# The source word of each grid constructor, by its term class, in the order
# Cartesian, Points, Fibred; `!Points` is held by the term PointGrid, since
# the set expression Points holds that name. The records of the grid
# constructors, `stage/grids.py`, read their words from this table.
GRID_WORDS = {T.Cartesian: "Cartesian", T.PointGrid: "Points", T.Fibred: "Fibred"}


def grid_word(grid) -> str:
    """The outer grid word of a grid term as a stage file writes it, with
    its `!`: `!Cartesian`, `!Points` or `!Fibred`."""
    return "!" + GRID_WORDS[type(grid)]


def _factor(factor) -> str:
    """One factor of a grid as written: the triple with its optional spacing
    word, the pair of a feasible set and a count, or the name of the nodes."""
    if isinstance(factor, T.Spaced):
        items = [_argument(factor.lower), _argument(factor.upper), _argument(factor.count)]
        if factor.spacing is not None:
            items.append(_word(factor.spacing))
        return f"{factor.coordinate}=({', '.join(items)})"
    if isinstance(factor, T.Listed):
        return f"{factor.coordinate}={factor.nodes}"
    if isinstance(factor, T.Feasible):
        return f"{factor.coordinate}=({factor.set}, {_argument(factor.count)})"
    raise NotImplementedError(
        f"to_source has no rule for the factor constructor {type(factor).__name__}"
    )


# --- statements ---

# keyed by constructor name so that the parsed and the retained forms
# print alike
_SYMBOL_OF_RELATION = {"Lt": "<", "Le": "<=", "Gt": ">", "Ge": ">="}


def _statement(statement) -> str:
    if isinstance(statement, T.Equation):
        return f"{_expr(statement.lhs, _SUM)} = {_expr(statement.rhs, _SUM)}"
    if isinstance(statement, T.Inequality):
        return _comparison(statement.lhs, statement.op, statement.rhs)
    if isinstance(statement, T.Slack):
        return _statement(statement.core) + _slack_clause(statement)
    if isinstance(statement, T.Law):
        return f"{distribution_subject_text(statement.subjects)} ~ {_expr(statement.law, _SUM)}"
    if isinstance(statement, T.FuncDef):
        return f"{statement.name}({_parameters(statement)}) := {_expr(statement.body, _SUM)}"
    if isinstance(statement, T.CorrDef):
        return (
            f"{statement.name}({_parameters(statement)}) := {_correspondence_body(statement.body)}"
        )
    if isinstance(statement, T.Assignment):
        return f"{_assignment_target(statement.target)} := {_assignment_value(statement.value)}"
    raise NotImplementedError(
        f"to_source has no rule for the statement constructor "
        f"{type(statement).__name__}; no stage file writes one"
    )


def _comparison(left, relation, right) -> str:
    """`left <sign> right`, each side printed at the level of a sum."""
    return f"{_expr(left, _SUM)} {_sign(relation)} {_expr(right, _SUM)}"


def _sign(relation) -> str:
    """The sign of an equality or ordered comparison; a `KeyError` for any
    other relation."""
    if isinstance(relation, T.Eq):
        return "="
    return _SYMBOL_OF_RELATION[type(relation).__name__]


def _ordered(relation) -> bool:
    """Whether a relation is one of the four ordered comparisons."""
    return type(relation).__name__ in _SYMBOL_OF_RELATION


def _slack_clause(statement) -> str:
    """The complementary-slackness clause of a `Slack`, ` ⟂ left <relation>
    right` or ` ⟂ lower <relation> middle <relation> upper`, which follows the
    core the statement holds."""
    if not isinstance(statement.core, (T.Equation, T.Inequality)):
        raise NotImplementedError(
            f"a Slack whose core is a {type(statement.core).__name__} has no "
            f"spelling in the grammar; the ⟂ clause follows an equality or an inequality "
            f"(rule `statement`)"
        )
    return " ⟂ " + _clause(statement.bound)


def _clause(bound) -> str:
    """The bound of a clause as the file writes it, `a >= 0` or
    `0 <= c_p <= w_d`."""
    if isinstance(bound, T.Between):
        return (
            f"{_expr(bound.lower, _SUM)} {_sign(bound.lo)} "
            f"{_comparison(bound.middle, bound.hi, bound.upper)}"
        )
    if not _ordered(bound.op):
        raise NotImplementedError("a bound is written with <, <=, > or >=; `=` has no spelling")
    return _comparison(bound.left, bound.op, bound.right)


def _complementary(term) -> str:
    """A multiplier declared in a block body with its clause, `μ[>] : ℝ₊ ⟂ a
    >= 0` (grammar rule `block_declaration`): one coordinate, bare or marked,
    typed by one set, then the clause."""
    declaration = term.declaration
    coordinates = (
        declaration.subject.coordinates
        if isinstance(declaration, T.Declaration) and isinstance(declaration.subject, T.Subject)
        else ()
    )
    domains = [c for c in getattr(declaration, "classifiers", ()) if isinstance(c, T.Domain)]
    if (
        len(coordinates) != 1
        or not isinstance(coordinates[0], T.Coordinate)
        or coordinates[0].classifiers
        or len(domains) != 1
        or len(declaration.classifiers) != 1
        or declaration.value is not None
    ):
        raise NotImplementedError(
            "a Complementary whose declaration is not one coordinate typed by one set "
            "has no spelling in the grammar (rule `block_declaration`)"
        )
    coordinate = coordinates[0]
    subject = (
        coordinate.stem
        if coordinate.at is None
        else _symbol(T.Variable(coordinate.stem, coordinate.at, 0))
    )
    return f"{subject} : {set_text(domains[0].space)} ⟂ {_clause(term.bound)}"


def distribution_subject_text(subjects) -> str:
    """The subject of a distribution declaration: one name bare, several as a
    tuple (grammar rule
    `law`: `single_subject "~" formula | tuple_subject "~" formula`)."""
    if not subjects or not all(isinstance(s, str) for s in subjects):
        named = ", ".join(type(s).__name__ for s in subjects) or "none"
        raise NotImplementedError(
            f"a Law whose subjects are not names ({named}) has no spelling; "
            f"the lowering writes the subject names"
        )
    if len(subjects) == 1:
        return subjects[0]
    return "(" + ", ".join(subjects) + ")"


def _parameters(definition) -> str:
    """The typed parameters of a definition, `c : ℝ₊₊` each (grammar rule
    `function_parameter`: a name and its typing; a definition lists
    at least one)."""
    name, params = definition.name, definition.params
    if not params:
        raise NotImplementedError(
            f"a {type(definition).__name__} of {name!r} with no parameter has "
            f"no spelling in the grammar (rule `function_definition`); an assignment "
            f"`{name} := …` writes a parameterless definition"
        )
    out = []
    for parameter in params:
        domains = (
            [c for c in parameter.classifiers if isinstance(c, T.Domain)]
            if isinstance(parameter, T.Coordinate)
            else []
        )
        if (
            not isinstance(parameter, T.Coordinate)
            or parameter.at is not None
            or len(domains) != 1
            or len(parameter.classifiers) != 1
        ):
            raise NotImplementedError(
                f"a parameter of {name!r} that is not a bare name with one set "
                f"({type(parameter).__name__}) has no spelling in this printer"
            )
        out.append(f"{parameter.stem} : {set_text(domains[0].space)}")
    return ", ".join(out)


def _correspondence_body(body) -> str:
    """The set body of a correspondence definition: an interval other than
    the open-open one, a finite set, a product or a comprehension (grammar
    rule `function_body`)."""
    if isinstance(body, T.Interval):
        bounds = body.bounds
        if (
            isinstance(bounds, T.Range)
            and isinstance(bounds.left, T.Open)
            and isinstance(bounds.right, T.Open)
        ):
            raise NotImplementedError(
                "an open-open interval body of a correspondence has no "
                "spelling (the grammar reads `(a, b)` as a tuple)"
            )
        return _range(bounds)
    if isinstance(body, (T.FiniteSet, T.Product)):
        return set_text(body)
    if isinstance(body, T.Comprehension):
        return comprehension_text(body)
    raise NotImplementedError(
        f"a correspondence body that is a {type(body).__name__} has no "
        f"spelling in the grammar (rule `function_body`)"
    )


def comprehension_text(comprehension) -> str:
    """A correspondence body written by comprehension, `{c : ℝ₊₊ | c < x}`:
    one bare binder typed by its base set, then the conditions in order
    (grammar rule `comprehension`)."""
    coordinates = (
        comprehension.bound.coordinates if isinstance(comprehension.bound, T.Subject) else []
    )
    if (
        len(coordinates) != 1
        or not isinstance(coordinates[0], T.Coordinate)
        or coordinates[0].at is not None
        or coordinates[0].classifiers
        or comprehension.base is None
        or not comprehension.conds
        or not all(
            isinstance(cond, T.Rel) and (_ordered(cond.op) or isinstance(cond.op, T.Eq))
            for cond in comprehension.conds
        )
    ):
        raise NotImplementedError(
            "a correspondence comprehension whose binder is not one bare name "
            "over a base set, or whose conditions are not equalities or inequalities, has no "
            "spelling (grammar rule `comprehension`)"
        )
    conditions = ", ".join(condition_text(cond) for cond in comprehension.conds)
    return "{" + f"{coordinates[0].stem} : {set_text(comprehension.base)} | {conditions}" + "}"


def _assignment_target(target) -> str:
    if isinstance(target, T.Constant):
        return target.name
    raise NotImplementedError(
        f"an Assignment whose target is a {type(target).__name__} has no "
        f"spelling; the lowering writes a name"
    )


def _assignment_value(value) -> str:
    """The value of an assignment: a primitive set by its own spelling, a
    finite set as a set, an interval other than the open-open one, or a
    comprehension as `{i : ℤ | i >= 0, i <= 1}` (grammar rule
    `assigned_value`), otherwise an expression. A comprehension is written by
    `comprehension_text`, as a correspondence body is; `set_text` writes it
    as a declaration does, as several sets with `@` between them, which no
    assignment admits.

    The spellings the grammar's tokens `BBSET` and `RPLUS` admit are the keys
    of `vocabulary.PRIMITIVE_SETS`, and this test reads that table, so the
    thirteen spellings stand in one place."""
    if isinstance(value, T.Space):
        if isinstance(value.set, T.Named) and value.set.name in PRIMITIVE_SETS:
            return value.set.name
        if isinstance(value.set, T.FiniteSet):
            return set_text(value.set)
        if isinstance(value.set, T.Comprehension):
            return comprehension_text(value.set)
        if isinstance(value.set, T.Interval):
            bounds = value.set.bounds
            if (
                isinstance(bounds, T.Range)
                and isinstance(bounds.left, T.Open)
                and isinstance(bounds.right, T.Open)
            ):
                raise NotImplementedError(
                    "an open-open interval as the body of a named set has no "
                    "spelling (the grammar reads `(a, b)` as a tuple)"
                )
            return _range(bounds)
        raise NotImplementedError(
            f"an assignment of a {type(value.set).__name__} set has no spelling in "
            f"`to_source`, which writes a reserved set glyph, a finite set, an "
            f"interval or a comprehension after `:=` (rule `assigned_value`)"
        )
    if isinstance(value, T.expr):
        return _expr(value, _SUM)
    raise NotImplementedError(
        f"an Assignment whose value is a {type(value).__name__} has no spelling"
    )


# --- expressions ---


def _expr(expression, need: int) -> str:
    """`e` printed for a position that requires level `need` or higher, in
    parentheses when `e` binds more loosely than that."""
    text = _expression_text(expression)
    return f"({text})" if _level(expression) < need else text


def _level(expression) -> int:
    if isinstance(expression, (T.Add, T.Sub, T.Neg)):
        return _SUM
    if isinstance(expression, (T.Mul, T.Div)):
        return _PRODUCT
    if isinstance(expression, T.Pow):
        return _MOLECULE
    return _ATOM


def _expression_text(expression) -> str:
    if isinstance(expression, T.Number):
        return _number(expression.value)
    if isinstance(expression, T.Sym):
        return _symbol(expression.symbol)
    if isinstance(expression, T.Add):
        return f"{_expr(expression.left, _SUM)} + {_expr(expression.right, _PRODUCT)}"
    if isinstance(expression, T.Sub):
        return f"{_expr(expression.left, _SUM)} - {_expr(expression.right, _PRODUCT)}"
    if isinstance(expression, T.Neg):
        return f"-{_expr(expression.operand, _PRODUCT)}"
    if isinstance(expression, T.Mul):
        return f"{_expr(expression.left, _PRODUCT)}*{_expr(expression.right, _MOLECULE)}"
    if isinstance(expression, T.Div):
        return f"{_expr(expression.left, _PRODUCT)}/{_expr(expression.right, _MOLECULE)}"
    if isinstance(expression, T.Pow):
        return f"{_expr(expression.base, _ATOM)}^{_expr(expression.exponent, _ATOM)}"
    if isinstance(expression, T.Call):
        if not expression.args:
            raise NotImplementedError(
                f"a Call with no argument ({expression.fun!r}) has no spelling in the "
                f"grammar; a call lists at least one argument"
            )
        return f"{expression.fun}({_arguments(expression.args)})"
    if isinstance(expression, T.Operator):
        if not expression.subs or not expression.args:
            raise NotImplementedError(
                f"an Operator with no subscript or no argument ({expression.head!r}) has "
                f"no spelling in the grammar (rule `operator_call`)"
            )
        subscripts = ", ".join(_subscript(s) for s in expression.subs)
        argument = expression.args[0] if len(expression.args) == 1 else None
        if (
            expression.head == "D"
            and isinstance(argument, T.Sym)
            and isinstance(argument.symbol, T.Variable)
        ):
            # a derivative of a perch-marked field is printed as written,
            # `D_{a}V[>]` (AMD-MB-001 §4.2, D2); a bare name may be a function,
            # `D_{c}(𝑢)`, and keeps its parentheses
            return f"{expression.head}_{{{subscripts}}}{to_source(argument)}"
        return f"{expression.head}_{{{subscripts}}}({_arguments(expression.args)})"
    if isinstance(expression, T.Tuple):
        if len(expression.items) < 2:
            raise NotImplementedError(
                f"a Tuple of {len(expression.items)} item(s) has no spelling in the "
                f"grammar; a tuple lists at least two"
            )
        return f"({_arguments(expression.items)})"
    if isinstance(expression, T.Select):
        if not isinstance(expression.family, (T.Sym, T.Tuple, T.Select)):
            raise NotImplementedError(
                f"a Select whose family is a {type(expression.family).__name__} has no "
                f"spelling in the grammar; selection indexes a name, a marked "
                f"name, a tuple, or a selection"
            )
        return f"{_expr(expression.family, _ATOM)}[{_selector(expression.sel)}]"
    if isinstance(expression, T.Space):
        return set_text(expression.set)
    raise NotImplementedError(
        f"to_source has no rule for the expression constructor "
        f"{type(expression).__name__}; the corpus does not use it"
    )


def _arguments(items) -> str:
    return ", ".join(_expr(item, _SUM) for item in items)


def _number(value) -> str:
    """A number as the lowering's `number_value` reads it: an int prints as
    an int, a float as Python's shortest repr, which the NUMBER terminal
    reads back."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NotImplementedError(f"a Number holding a {type(value).__name__} has no spelling")
    if value < 0 or (isinstance(value, float) and not math.isfinite(value)):
        raise NotImplementedError(
            f"the Number {value!r} has no spelling: the grammar writes a sign "
            f"as Neg and infinity as the constant inf"
        )
    return str(value) if isinstance(value, int) else repr(value)


def _symbol(symbol) -> str:
    if isinstance(symbol, T.Constant):
        return symbol.name
    if isinstance(symbol, T.Variable):
        if symbol.shift != 0:
            raise NotImplementedError(
                f"a Variable with shift {symbol.shift!r} ({symbol.name!r}) has no "
                f"spelling in the stage grammar"
            )
        if isinstance(symbol.when, T.At):
            if isinstance(symbol.when.side, T.Arrival):
                return f"{symbol.name}[<]"
            if isinstance(symbol.when.side, T.Continuation):
                return f"{symbol.name}[>]"
        raise NotImplementedError(
            f"a Variable indexed by {type(symbol.when).__name__} "
            f"({symbol.name!r}) has no spelling in the stage grammar; a field is "
            f"written bare at the decision perch and marked [<] or [>]"
        )
    raise NotImplementedError(
        f"to_source has no rule for the symbol constructor "
        f"{type(symbol).__name__}; the corpus does not use it"
    )


def _subscript(subscript) -> str:
    if isinstance(subscript, T.Var):
        return subscript.name
    if isinstance(subscript, T.In):
        return f"{subscript.var} : {_expr(subscript.set, _SUM)}"
    raise NotImplementedError(
        f"to_source has no rule for the subscript constructor {type(subscript).__name__}"
    )


def _selector(sel) -> str:
    if isinstance(sel, (T.Key, T.Pos)):
        return str(sel.at)
    if isinstance(sel, T.Term):
        return _expr(sel.at, _SUM)
    raise NotImplementedError(
        f"to_source has no rule for the selector constructor {type(sel).__name__}"
    )


# --- set expressions ---


def _factor_text(set_expression) -> str:
    """The text of a set standing as a factor of a product or as the set the
    members of a listed set lie in: a set of functions has no spelling at that
    place, since the arrow binds looser than the product."""
    if isinstance(set_expression, T.Functions):
        raise NotImplementedError(
            "a Functions set has no spelling as a factor of a product or as the set listed "
            "members lie in: the arrow binds looser than the product"
        )
    return set_text(set_expression)


def set_text(set_expression) -> str:
    if isinstance(set_expression, T.Named):
        return set_expression.name
    if isinstance(set_expression, T.Interval):
        return _range(set_expression.bounds)
    if isinstance(set_expression, T.FiniteSet):
        if not set_expression.members:
            raise NotImplementedError("an empty FiniteSet has no spelling in the grammar")
        return (
            "{"
            + ", ".join(
                member if isinstance(member, str) else _expr(member, _SUM)
                for member in set_expression.members
            )
            + "}"
        )
    if isinstance(set_expression, T.IntegerRange):
        return f"{{{_expr(set_expression.lower, _SUM)}, …, {_expr(set_expression.upper, _SUM)}}}"
    if isinstance(set_expression, T.Points):
        if not set_expression.members:
            raise NotImplementedError("an empty Points set has no spelling in the grammar")
        listed = "{" + ", ".join(_expr(member, _SUM) for member in set_expression.members) + "}"
        if set_expression.superset is None:
            return listed
        return f"{listed} ⊂ {_factor_text(set_expression.superset)}"
    if isinstance(set_expression, T.Functions):
        if isinstance(set_expression.domain, T.Functions):
            raise NotImplementedError(
                "a Functions set whose domain is a Functions set has no spelling: the arrow "
                "associates to the right"
            )
        return f"{set_text(set_expression.domain)} → {set_text(set_expression.codomain)}"
    if isinstance(set_expression, T.Product):
        if len(set_expression.factors) < 2 or any(
            isinstance(factor, T.Product) for factor in set_expression.factors
        ):
            raise NotImplementedError(
                "a Product of fewer than two factors, or with a Product as a "
                "factor, has no spelling: the lowering writes one flat Product"
            )
        return " × ".join(_factor_text(factor) for factor in set_expression.factors)
    if isinstance(set_expression, T.Comprehension):
        return _intersection_text(set_expression)
    raise NotImplementedError(
        f"to_source has no rule for the set constructor {type(set_expression).__name__}; "
        f"the corpus does not use it"
    )


def is_interval(set_expression) -> bool:
    """Whether a set is an interval written with both brackets, `(0, 1]`."""
    return isinstance(set_expression, T.Interval) and _bracketed(set_expression.bounds)


def _bracketed(bounds) -> bool:
    """Whether the bounds of an interval carry both brackets."""
    return isinstance(bounds, T.Range) and bounds.left is not None and bounds.right is not None


def _range(bounds) -> str:
    if not _bracketed(bounds):
        raise NotImplementedError("an interval without both end markers has no spelling")
    left = "[" if isinstance(bounds.left, T.Closed) else "("
    right = "]" if isinstance(bounds.right, T.Closed) else ")"
    return f"{left}{_expr(bounds.lower, _SUM)}, {_expr(bounds.upper, _SUM)}{right}"


def bound_name(subject):
    """The name a subject binds, as the term a condition on it writes, where
    the subject binds one name that carries no type of its own: `β` for `β`,
    and `V[>]` with its perch mark for `V[>]`. None for a tuple of names and
    for a name typed inside its parentheses."""
    coordinates = subject.coordinates if isinstance(subject, T.Subject) else ()
    if (
        len(coordinates) != 1
        or not isinstance(coordinates[0], T.Coordinate)
        or coordinates[0].classifiers
    ):
        return None
    name = coordinates[0]
    return T.Sym(T.Constant(name.stem) if name.at is None else T.Variable(name.stem, name.at, 0))


def _intersection_text(comprehension) -> str:
    """A declared set with conditions as a declaration writes it, several
    sets with `@` between them (AMD-GRAM-004 §3; `intersection_of_sets` in
    bellman.syntax.lower): `{x ∈ B | x ≥ 1, x ≤ 10}` is written `B @ [1, 10]`
    after `x :`.

    The base is written first, then one interval for each bound. The lower
    bounds and the upper bounds are paired in their order. A bound left
    without a partner is the interval from it to the base's own endpoint on
    the other side, with the base's bracket; where the base is no interval,
    to `-inf` or `inf`, with a closed bracket where the base may hold that
    infinity, since an open one would exclude it. The lowering reads no
    condition from such an endpoint, and it reads the endpoints of each side
    whatever intervals hold them, so the text of a set the lowering keeps is
    read back as the same term. A condition that is no ordered comparison of
    the bound name with a term has no interval, and the set is then written
    with a bar by `comprehension_text`."""
    name = bound_name(comprehension.bound)
    base = comprehension.base
    if name is None or base is None:
        raise NotImplementedError(
            "a Comprehension whose bound is not one name over a base set has no spelling; a "
            "declaration writes a set with conditions as sets with `@` between them"
        )
    conds = comprehension.conds
    for cond in conds:
        if not isinstance(cond, T.Rel) or cond.left != name or not _ordered(cond.op):
            return comprehension_text(comprehension)
    held = base.bounds if is_interval(base) else None
    infinity = T.Sym(T.Constant("inf"))

    def free(negative):
        """The endpoint and the bracket of a side that a bound leaves free."""
        if held is not None:
            return (held.lower, held.left) if negative else (held.upper, held.right)
        bracket = T.Closed() if may_hold_infinity(base, negative) else T.Open()
        return (T.Neg(infinity) if negative else infinity), bracket

    lower = [(cond.right, bracket_of(cond.op)) for cond in conds if _lower(cond.op)]
    upper = [(cond.right, bracket_of(cond.op)) for cond in conds if not _lower(cond.op)]
    parts = [set_text(base)]
    for low, high in zip_longest(lower, upper):
        low, left = low or free(negative=True)
        high, right = high or free(negative=False)
        parts.append(_range(T.Range(left, low, high, right)))
    return " @ ".join(parts)


def is_infinity(endpoint, negative) -> bool:
    """Whether an interval's endpoint is `-inf`, with `negative`, or `inf`."""
    if negative:
        return isinstance(endpoint, T.Neg) and is_infinity(endpoint.operand, negative=False)
    return (
        isinstance(endpoint, T.Sym)
        and isinstance(endpoint.symbol, T.Constant)
        and endpoint.symbol.name == "inf"
    )


def may_hold_infinity(set_expression, negative) -> bool:
    """Whether a set, as it is written, may hold `-inf`, with `negative`, or
    `inf`. An interval holds it where it is closed at that infinite
    endpoint, and an extended real set where it reaches that side, `ℝ̄` or
    `ℝ_{+∞}`. A real set, an integer set, a range of integers and a list of
    finite numbers hold neither infinity. Every other set may hold it: a set
    the file names, whose members are not known from its name, and a list
    with a member that is no finite number as written."""
    if isinstance(set_expression, T.Interval):
        if not is_interval(set_expression):
            return False
        bounds = set_expression.bounds
        end, bracket = (bounds.lower, bounds.left) if negative else (bounds.upper, bounds.right)
        return is_infinity(end, negative) and isinstance(bracket, T.Closed)
    if isinstance(set_expression, T.Named):
        primitive = PRIMITIVE_SETS.get(set_expression.name)
        if primitive is None:
            return True
        if primitive.kind != EXTENDED_REAL:
            return False
        return primitive.glyph != ("ℝ_{+∞}" if negative else "ℝ_{-∞}")
    if isinstance(set_expression, T.IntegerRange):
        return False
    if isinstance(set_expression, T.Points):
        return not all(is_number(member) for member in set_expression.members)
    return True


def is_number(term) -> bool:
    """Whether a term is a number as written, `1` or `-0.5`."""
    return isinstance(term, T.Number) or (
        isinstance(term, T.Neg) and isinstance(term.operand, T.Number)
    )


def condition_text(condition) -> str:
    """One condition of a set as a set with a bar writes it, `x < R` or
    `x = 5`: an equality or an ordered comparison of two terms."""
    if not isinstance(condition, T.Rel) or not (
        _ordered(condition.op) or isinstance(condition.op, T.Eq)
    ):
        raise NotImplementedError(
            f"a condition that is no equality or ordered comparison of two terms, a "
            f"{type(condition).__name__}, has no spelling in a set with a bar"
        )
    return _comparison(condition.left, condition.op, condition.right)


def _lower(relation) -> bool:
    """Whether an ordered comparison `x > b` or `x >= b` bounds its left side
    from below."""
    return isinstance(relation, (T.Gt, T.Ge))


def bracket_of(relation):
    """The bracket of the interval endpoint an ordered comparison gives:
    closed for `>=` and `<=`, open for `>` and `<`."""
    return T.Closed() if isinstance(relation, (T.Ge, T.Le)) else T.Open()
