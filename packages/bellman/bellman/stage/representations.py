"""The function representations of a stage (AMD-MT-003 build contract §§3,
4): the registry of the representation families, the data a representation
reads at its place, and the exact comparison of two finite supports.

A representation family states the numerical form of a function, such as
piecewise linear interpolation. Its record, `RepresentationFamily`, holds the
word a methods file writes, its typed standardized arguments, the data
sources it accepts among `DATA_SOURCES`, the derivatives it offers, what it
stores, the places it admits and the rule of its independent grid. The
method table (`stage/method_table.py`) reads the registry each time it is
read, so a family registered after this module is imported has its row;
`register` refuses a word that another family or another method already
names, and `unregister` removes a family. A record describes data and
arguments and makes no evaluator: a numerical procedure is a handler's or an
application's.

A version keeps the record of each family its entries name as the record
stood when the version was bound (`records.Bindings.families`), so that a
later registration or unregistration changes later bindings and the answers
of the catalogue and leaves the meaning of a version already made as it was;
`bound_row` answers the row a version reads.

The data source of a representation is decided from the combined declarations
of the version, in the order of build contract §3 (`selected_source`): an
authored `evaluate(knots, values, x)` supplies its table, at its occurrence
and at a `!node` line that defines its name by the table alone; the closing
Evaluation of a builder whose method is `!egm`, and each object it stores,
supplies the policy pairs the method selects; the Evaluation of a builder
whose method is `!explicit`, or a line or a declared function with a complete
authored expression, supplies that expression to a family that accepts one;
and otherwise a family samples the function on its own grid. Data that is
missing, or that fails its check, never selects another case: the checks of
the selected data, at binding and at configuration, stand in
`stage/representation_checks.py`, which compares an authored table's
optional grid with the table by `supports_equal`.

This module stands below the places (`stage/places.py`), which read the
selection, and below the method table (`stage/method_table.py`), which reads
the registry; it reads the rows of the methods that name no family from
`stage/method_rows.py`, which stands below it, and the typing record of a
builder's method from the definitions table (`explicit.method_entry`).
"""

from __future__ import annotations

import dataclasses
import itertools
import math
import numbers
from collections.abc import Mapping
from fractions import Fraction
from types import MappingProxyType

from bellman.fold.wire_terms import term_nodes
from bellman.native.identity import Identity
from bellman.native.records import EntryText, MethodOption, TypeParameter
from bellman.stage.explicit import CHOICES, method_entry
from bellman.stage.method_rows import (
    KEYWORD_DOMAINS,
    OUTPUT_PERCH,
    ROWS_AFTER,
    ROWS_BEFORE,
    family_row,
    fixed_row,
)
from bellman.syntax import terms as T

__all__ = (
    "CLOSED_FORM",
    "DATA_SOURCES",
    "EXPLICIT",
    "REPRESENTATION_ADMITS",
    "RepresentationFamily",
    "bound_families",
    "bound_family",
    "bound_row",
    "data_site",
    "declared_functions",
    "evaluation_of_builder",
    "evaluation_of_node",
    "families",
    "function_body",
    "grid_support",
    "line_record",
    "register",
    "selected_source",
    "supports_equal",
    "table_support",
    "unregister",
)

# --- the records ---

# The four sources of the data a representation is built from, in the order
# selection reads them (build contract §3): an authored table
# `evaluate(knots, values, x)`, the policy pairs the endogenous grid method
# selects at the closing Evaluation of its builder, a complete authored
# expression with an explicit kernel, and the nodes of the representation's
# own grid, on which the represented function is sampled.
DATA_SOURCES = ("table", "pairs", "expression", "own nodes")

# The places a function representation is typed at: a `!node` line, a line
# with an id, a declared function, and the operator `evaluate`, which is an
# authored `evaluate(...)` occurrence, the Evaluation of a `!node` line or the
# Evaluation that closes a builder with each object it stores; not a builder
# (AMD-MB-002).
REPRESENTATION_ADMITS = (
    "node",
    "statement",
    "definition",
    ("operator", "evaluate"),
)


@dataclasses.dataclass(frozen=True)
class RepresentationFamily:
    """One representation family. `word` is the method word without its
    `!`, a hyphen standing for the underscore a stage file writes;
    `parameters` maps the name of each standardized argument to its
    `MethodOption`; `sources` lists the data sources the family accepts,
    among `DATA_SOURCES`, in that order; `derivatives` lists the orders of
    the derivatives it offers and `evaluates` states their coordinate, shape
    and region; `stored` states the data a fitted representation stores;
    `admits` lists the kinds of place it is typed at; `grid` is the rule of
    its independent grid, the perch word `output`
    (`method_rows.OUTPUT_PERCH`) of the grid on which it samples a function
    or reads an optional grid, or None for a family that refuses a
    representation grid; and `text` is the `EntryText` its reference entry
    prints. The record describes and implements nothing."""

    word: str
    parameters: Mapping
    sources: tuple
    derivatives: tuple
    stored: str
    evaluates: str | None = None
    admits: tuple = REPRESENTATION_ADMITS
    grid: str | None = OUTPUT_PERCH
    text: EntryText | None = None

    def __post_init__(self):
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "derivatives", tuple(self.derivatives))
        object.__setattr__(self, "admits", tuple(self.admits))
        written = self.word.replace("-", "_") if isinstance(self.word, str) else ""
        if not (written[:1].isalpha() and written.replace("_", "a").isalnum()):
            raise ValueError(
                f"a family's word is a method word without its `!`, a letter followed by letters, "
                f"digits, hyphens or underscores; got {self.word!r}"
            )
        if not all(isinstance(option, MethodOption) for option in self.parameters.values()):
            raise TypeError(f"!{self.word}: each standardized argument is a MethodOption")
        unknown = tuple(source for source in self.sources if source not in DATA_SOURCES)
        if not self.sources or unknown:
            raise ValueError(
                f"!{self.word} accepts at least one data source, each one of "
                f"{', '.join(DATA_SOURCES)}; got {self.sources!r}"
            )
        if self.sources != tuple(source for source in DATA_SOURCES if source in self.sources):
            raise ValueError(
                f"!{self.word} lists its data sources once each, in the order "
                f"{', '.join(DATA_SOURCES)}; got {self.sources!r}"
            )
        if self.grid not in (OUTPUT_PERCH, None):
            raise ValueError(
                f"!{self.word}: the grid rule is {OUTPUT_PERCH!r} or None; got {self.grid!r}"
            )
        if "own nodes" in self.sources and self.grid is None:
            raise ValueError(
                f"!{self.word} samples a function on its own nodes, which lie on its grid, and "
                "refuses a grid; a family that accepts its own nodes reads a grid"
            )
        if not all(isinstance(order, int) and order >= 1 for order in self.derivatives):
            raise ValueError(f"!{self.word}: each derivative order is a positive integer")
        if not isinstance(self.stored, str) or not self.stored:
            raise ValueError(f"!{self.word}: the stored data are stated in one sentence")
        if self.text is not None and not isinstance(self.text, EntryText):
            raise TypeError(f"!{self.word}: the text of a family is an EntryText")

    def __hash__(self):
        return hash(
            (
                self.word,
                frozenset(self.parameters.items()),
                self.sources,
                self.derivatives,
                self.stored,
                self.evaluates,
                self.admits,
                self.grid,
                self.text,
            )
        )


# --- the registry ---

_FAMILIES = {}


def register(family):
    """Register `family` under its word, so that the method table has its row
    and a methods file may name it, and answer the family. A word another
    registered family names is refused with a ValueError, and so is a word
    that names a method of the table that is no registered family, a row of
    `stage/method_rows.py`, spelled with a hyphen or with an underscore; and
    so is a typed argument of a kind configure does not check, which is no
    key of `method_rows.KEYWORD_DOMAINS`."""
    if not isinstance(family, RepresentationFamily):
        raise TypeError(f"register takes a RepresentationFamily, not {type(family).__name__}")
    if family.word in _FAMILIES:
        raise ValueError(
            f"the word !{family.word} already names a registered representation family"
        )
    spelled = family.word.replace("_", "-")
    for tag in (*ROWS_BEFORE, *_FAMILIES, *ROWS_AFTER):
        if tag.replace("_", "-") != spelled:
            continue
        if tag in _FAMILIES:
            raise ValueError(
                f"the word !{family.word} is the registered representation family !{tag} spelled "
                "with an underscore for a hyphen, which a stage file reads as one word"
            )
        raise ValueError(
            f"the word !{family.word} names the method !{tag} of the method table, which is no "
            "registered representation family; a family's word names no other method"
        )
    for name, option in family.parameters.items():
        if option.kind not in KEYWORD_DOMAINS:
            raise ValueError(
                f"!{family.word}: the argument {name!r} takes the kind {option.kind!r}, and "
                f"configure checks the kinds {', '.join(KEYWORD_DOMAINS)}"
            )
    _FAMILIES[family.word] = family
    return family


def unregister(word):
    """Remove the family registered under `word` and answer it; a word that
    names no registered family is refused with a KeyError. A version bound
    while the family was registered keeps its record."""
    if word not in _FAMILIES:
        raise KeyError(f"!{word} names no registered representation family")
    return _FAMILIES.pop(word)


def families():
    """The registered families by word, in registration order, as a
    read-only mapping that follows later registrations."""
    return MappingProxyType(_FAMILIES)


def _family_named(held, word):
    """The family of the mapping `held` that the method word `word` names, as
    written or with each underscore read as a hyphen; None for no such
    family."""
    if not isinstance(word, str):
        return None
    return held.get(word) or held.get(word.replace("_", "-"))


def bound_family(stage, word):
    """The family record the version `stage` reads for the method word
    `word`: the record kept at binding (`Bindings.families`), and otherwise
    the registered family; None where the word names no family."""
    kept = getattr(stage.bindings, "families", None) or {}
    return _family_named(kept, word) or _family_named(_FAMILIES, word)


def bound_row(stage, word):
    """The row of the method table that the version `stage` reads for the
    method word `word`: the row of the family the version reads
    (`bound_family`), the record kept at binding before the registered one,
    where the word names one, and otherwise the row of the method the word
    names among those that are no family (`method_rows.fixed_row`); None
    where the word names no method. It answers as `method_table.row_of`
    does, save that a family kept at binding stands before the registry."""
    family = bound_family(stage, word)
    return family_row(family) if family is not None else fixed_row(word)


def bound_families(definitions):
    """The family records a version keeps at binding, by word, as a read-only
    mapping: those its typing entries name among the definitions
    `definitions`, and the closed form where an entry types `!explicit` on a
    builder, whose Evaluation the closed form represents unless an entry
    names another representation there."""
    words = []
    for record in definitions.values():
        if record.kind != "typing" or not isinstance(record.equations[0], T.Word):
            continue
        words.append(record.equations[0].name)
        if record.identity.field == "method" and record.equations[0].name == "explicit":
            words.append(CLOSED_FORM)
    kept = {}
    for word in words:
        family = _family_named(_FAMILIES, word)
        if family is not None:
            kept.setdefault(family.word, family)
    return MappingProxyType(kept)


# --- the data source of a representation ---

# the word of the base family that represents a function by its authored
# expression, and of the solution method whose builder it closes by default
CLOSED_FORM = "closed-form"
EXPLICIT = "explicit"
_EGM = "egm"
_EVALUATE = "evaluate"


def evaluation_of_builder(place):
    """Whether `place`, a place of `places.inventory`, is the Evaluation that
    closes its builder, whole or one object it stores."""
    return (
        place.head == _EVALUATE
        and bool(place.keys)
        and all(
            isinstance(box, Identity) and box.kind == "Evaluation" and box.address == place.block
            for box in place.boxes
        )
    )


def _holds_authored_table(place):
    """Whether `place` holds occurrences of an authored `evaluate(knots,
    values, x)`: an `evaluate` place whose boxes are lines, not the
    Evaluation of a builder or of a node."""
    return place.head == _EVALUATE and any(
        not (isinstance(box, Identity) and box.kind == "Evaluation") for box in place.boxes
    )


def _node_table(stage, place):
    """The authored table that is the function of a `!node` line, read at
    the line's head `place` or at its Evaluation: the call `evaluate(knots,
    values, x)` by which alone the line defines its one name, `V =
    evaluate(K, Y, m)`. None at any other place, and where the table is one
    term of the node's expression, `W = β*V[>] + evaluate(K, Y, m)`, since
    the table then gives the values of that term and not of the node's
    function."""
    if place.kind != "node" and not evaluation_of_node(place):
        return None
    address = place.address if place.kind == "node" else place.boxes[0].address
    record = line_record(stage, address)
    core = record.equations[0] if record is not None and record.equations else None
    if (
        isinstance(core, T.Equation)
        and isinstance(core.lhs, T.Sym)
        and isinstance(core.rhs, T.Call)
        and core.rhs.fun == _EVALUATE
    ):
        return core.rhs
    return None


def evaluation_of_node(place):
    """Whether `place`, a place of `places.inventory`, is the Evaluation of a
    `!node` line."""
    return (
        place.head == _EVALUATE
        and bool(place.keys)
        and all(
            isinstance(box, Identity) and box.kind == "Evaluation" and box.address != place.block
            for box in place.boxes
        )
    )


def builder_method(stage, block):
    """The method word typed at the builder `block`, without its `!` and with
    each underscore read as a hyphen, `time-iteration`; None where none is
    typed. The word is read from the typing record of the builder's method
    component (`explicit.method_entry`), which `places.typings` resolves to
    the builder's place."""
    record = method_entry(stage, block)
    if record is None or not isinstance(record.equations[0], T.Word):
        return None
    return record.equations[0].name.replace("_", "-")


def data_site(stage, place):
    """The data the place `place` supplies to a representation, the case of
    build contract §3 it stands in: `table` for an authored `evaluate`
    occurrence, and for the head and the Evaluation of a `!node` line whose
    function the table is (`_node_table`), so that the two addresses of the
    node read one source; `pairs` for the closing Evaluation of a builder
    whose method is `!egm`, whole or one object it stores; `expression` for
    the closing Evaluation of a builder whose method is `!explicit`, and for
    a line, the Evaluation of a `!node` line or a declared function whose
    defining expression is complete (`_complete_expression`); and None for a
    place that supplies none of them, whose representation samples the
    function on its own grid. A table that is one term of a node's
    expression supplies no data of the node's function. A label, a method
    word with no expression behind it, supplies no expression."""
    if _holds_authored_table(place) or _node_table(stage, place) is not None:
        return "table"
    if evaluation_of_builder(place):
        word = builder_method(stage, place.block)
        if word == _EGM:
            return "pairs"
        if word == EXPLICIT:
            return "expression"
        return None
    if _complete_expression(stage, place) is not None:
        return "expression"
    return None


def selected_source(stage, place, held):
    """The data source the function representation typed at `place`, whose
    components are `held`, reads, one word of `DATA_SOURCES`; None where the
    method component names no representation family. The case is that of
    the place (`data_site`), read from the combined declarations of the
    version: an authored table is read as a table; at the closing
    Evaluation of an `!egm` builder a family that accepts pairs reads the
    selected pairs and another reads its own nodes, sampled from those
    pairs; a family that accepts an expression reads the complete authored
    expression of its place where the place supplies one; and otherwise the
    family samples the function on its own grid. A source the family does
    not accept is refused by `representation_checks.check_sources` and
    selects no other case."""
    if held.method is None:
        return None
    family = bound_family(stage, held.method.name)
    if family is None:
        return None
    site = data_site(stage, place)
    if site == "table":
        return "table"
    if site == "pairs":
        if "pairs" in family.sources or "own nodes" not in family.sources:
            return "pairs"
        return "own nodes"
    if site == "expression" and "expression" in family.sources:
        return "expression"
    return "own nodes"


# --- the complete expression of a local computation ---


def line_record(stage, address):
    """The definition record of the line at `address`, or None."""
    record = stage.definitions.get(address)
    return record if record is not None and record.kind == "line" else None


def _complete_expression(stage, place):
    """The complete authored expression the place `place` holds, or None: for
    a line with an id and for the Evaluation of a `!node` line, the line's
    equation where it defines one name by an expression that applies no
    `argmax`, `solve`, `upper_env` or `evaluate`; for a declared function,
    its authored body (`function_body`). `representation_checks.check_sources`
    then requires the explicit kernel of the expression. A relation, a
    choice and an alias of a derivative or of an inverse hold none."""
    if place.kind in ("statement", "node") or evaluation_of_node(place):
        address = place.address if place.kind in ("statement", "node") else place.boxes[0].address
        record = line_record(stage, address)
        if record is None or not record.equations:
            return None
        core = record.equations[0]
        if not isinstance(core, T.Equation) or not isinstance(core.lhs, T.Sym):
            return None
        if any(
            isinstance(node, T.Operator) and node.head in CHOICES for node in term_nodes(core.rhs)
        ) or any(
            isinstance(node, T.Call) and node.fun == _EVALUATE for node in term_nodes(core.rhs)
        ):
            return None
        return core.rhs
    if place.kind == "definition":
        definition = stage.definitions.get(place.boxes[0])
        if definition is None:
            return None
        return function_body(declared_functions(stage), definition.identity.field)
    return None


def declared_functions(stage):
    """The declared functions of `stage`, the aliases of their names and its
    correspondences, by name, the definitions a term may call, as
    `fold/stage_names.StageNames.functions` holds them."""
    return {
        d.identity.field: d
        for d in stage.definitions.values()
        if d.kind in ("function", "function_alias", "correspondence")
    }


def function_body(functions, name):
    """The authored body of the function `name` among the declared functions
    `functions`: the body of its definition in closed form, `𝑢(c) :=
    c^(1-ρ)/(1-ρ)`, where an alias of a function's name, `𝑓 := 𝑢`, is
    followed to the function it names, as the kernel compiler follows it.
    None for a name no definition declares, for a correspondence, whose body
    is a set and no expression, for an alias of a derivative or of an
    inverse, which is a label without an expression, and for a body that
    applies an operator, a choice, an expectation or a derivative, or calls
    `Inv` or `evaluate`. Whether the compiler writes the body is decided by
    `representation_checks.check_sources`."""
    seen = set()
    while name in functions and name not in seen:
        definition = functions[name]
        core = definition.equations[0] if definition.equations else None
        if definition.kind == "correspondence":
            return None
        if isinstance(core, T.FuncDef):
            if any(
                isinstance(node, T.Operator)
                or (isinstance(node, T.Call) and node.fun in ("Inv", _EVALUATE))
                for node in term_nodes(core.body)
            ):
                return None
            return core.body
        if not (
            definition.kind == "function_alias"
            and isinstance(core, T.Sym)
            and isinstance(core.symbol, T.Constant)
        ):
            return None
        seen.add(name)
        name = core.symbol.name
    return None


# --- the authored table and its optional grid ---


def _named_value(term, values):
    """The bound value of the name `term`, a setting among `values` or a
    parameter of the calibration they hold, or None for no bound value."""
    if not (isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant)):
        return None
    name = term.symbol.name
    return values.get(name)


def table_support(stage, call, values):
    """The knots of the authored table `call` as a tuple of points, where its
    first argument names a setting or a parameter whose value is bound among
    `values`, and None otherwise: a runtime argument of the table is an
    explicit input and has no value before preparation."""
    held = _named_value(call.args[0], values) if call.args else None
    return None if held is None else tuple(held)


def grid_support(grid, values, coordinates):
    """The finite support of a grid term whose points are given exactly, at
    the bound `values`, as a tuple of points on `coordinates`, the names the
    grid discretizes in their order, and None for a grid whose points a
    numerical construction makes: the declared points of `!Points`, which
    lie in the domain's declared coordinate order, none for `!Points` with
    no argument, and the product of the node sets of a `!Cartesian` whose
    every coordinate is named by a factor that lists one, taken in the order
    of `coordinates` whatever the order of the factors. A coordinate no
    factor names takes the symbolic default with no numbers; it, a spaced, a
    feasible or a quadrature factor, and a fibred grid, are constructed
    before numerical use and compared then."""
    if isinstance(grid, T.PointGrid):
        if grid.nodes is None:
            return ()
        held = values.get(grid.nodes)
        return None if held is None else tuple(held)
    if isinstance(grid, T.Cartesian):
        factors = {factor.coordinate: factor for factor in grid.factors}
        listed = []
        for coordinate in coordinates:
            factor = factors.get(coordinate)
            if not isinstance(factor, T.Listed) or factor.nodes not in values:
                return None
            listed.append(tuple(values[factor.nodes]))
        if len(listed) == 1:
            return listed[0]
        return tuple(itertools.product(*listed))
    return None


# --- the exact comparison of finite supports ---


def supports_equal(first, second):
    """Whether two finite supports hold the same points, each an iterable of
    points, a point a real number or a tuple, list or one-dimensional array
    of real numbers (build contract §4). Each coordinate is converted to a
    `fractions.Fraction`, exactly for an `int`, a `float` and a NumPy integer
    or floating scalar, so that distinct large integers stay distinct and no
    tolerance applies; the two signed zeros are one point. A coordinate that
    is not finite, or not a real number, raises a ValueError naming it. The
    answer compares the two sets of points; the caller keeps the order of a
    table and the alignment of its values."""
    return _exact_support(first) == _exact_support(second)


def _exact_support(points):
    """The set of the exact points of a support."""
    found = set()
    for point in points:
        if isinstance(point, (tuple, list)):
            coordinates = tuple(point)
        elif getattr(point, "shape", ()) not in ((), None) and hasattr(point, "tolist"):
            coordinates = tuple(point.tolist())
        else:
            coordinates = (point,)
        found.add(tuple(_exact(coordinate) for coordinate in coordinates))
    return frozenset(found)


def _exact(value):
    """A real coordinate as a `Fraction`, converted exactly; a ValueError
    for a value that is no finite real number."""
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"the coordinate {value!r} is not a real number")
    if isinstance(value, numbers.Integral):
        return Fraction(int(value))
    if isinstance(value, Fraction):
        return value
    if not math.isfinite(value):
        raise ValueError(f"the coordinate {value!r} is not finite")
    try:
        numerator, denominator = value.as_integer_ratio()
    except (AttributeError, OverflowError, ValueError):
        raise ValueError(f"the coordinate {value!r} has no exact rational value") from None
    return Fraction(numerator, denominator)


# --- the base families, registered as this module is imported ---

# the domain and the codomain of a represented function, which the attachment
# site supplies; each meaning is one sentence whose subject, "It", is the
# parameter, since the reference entry prints the parameter's name in the
# sentence before it
_DOMAIN = TypeParameter(
    "X",
    "It is the domain of the represented function, whose coordinates are those of the place in "
    "their declared order.",
)
_CODOMAIN = TypeParameter("Y", "It is the set of the represented function's values.")

register(
    RepresentationFamily(
        "Linear",
        {},
        ("table", "pairs", "own nodes"),
        derivatives=(1,),
        evaluates=(
            "the first derivative, piecewise constant between its nodes and so a step "
            "function, which an inverse Euler step that reads it turns into a step "
            "candidate; the second derivative is zero and is not offered"
        ),
        stored="The values at the nodes, aligned with the nodes in increasing order.",
        text=EntryText(
            meaning=(
                "The family represents a function on one real coordinate by continuous piecewise "
                "linear interpolation through strictly increasing nodes and the values aligned "
                "with them."
            ),
            compatibility=(
                "The family reads an authored table `evaluate(knots, values, x)`, the policy "
                "pairs `!egm` selects at the closing Evaluation of its builder, where a grid is "
                "refused, or its own nodes on the grid of its place, the default product over the "
                "function's coordinates where no grid is written. An optional grid beside a "
                "table discretizes the coordinates at which the table is evaluated, written as a "
                "name or as a tuple of names in the order of the grid's coordinates, and has "
                "exactly the table's finite support, compared at configuration "
                "where both are given exactly and otherwise before numerical preparation. "
                "Numerical use needs at least two finite strictly increasing nodes with aligned "
                "finite values, and an identified extension outside the node interval."
            ),
            example=(
                "cntn_to_dcsn.evaluate.method : !Linear\n"
                "cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_min, m_max, n_m))"
            ),
            example_meaning=(
                "The decision value is represented by linear interpolation between its values "
                "at `n_m` evenly spaced points of cash on hand from `m_min` to `m_max`."
            ),
            implementation=(
                "The scalar evaluator `consumption-perfect-foresight-crra:Linear`, the class "
                "`Linear` of the perfect-foresight application's module "
                "`code/closed_form_check.py`, evaluates it and its first derivative and "
                "refuses a point outside the node interval; the package itself supplies no "
                "evaluator."
            ),
            definition="bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain",
            type_parameters=(_DOMAIN, _CODOMAIN),
            related=("pchip", "closed-form", "egm"),
            source="bellman.stage.representations",
        ),
    )
)

register(
    RepresentationFamily(
        "pchip",
        {},
        ("table", "pairs", "own nodes"),
        derivatives=(1, 2),
        evaluates=(
            "the first derivative, continuous across its nodes, and the second derivative "
            "between its nodes, which may jump at a node"
        ),
        stored="The values at the nodes, aligned with the nodes in increasing order.",
        text=EntryText(
            meaning=(
                "The family represents a function on one real coordinate by piecewise cubic "
                "Hermite interpolation, with the shape-preserving slopes of PCHIP, through "
                "strictly increasing nodes and the values aligned with them."
            ),
            compatibility=(
                "The family reads the same data as `!Linear`: an authored table, the policy "
                "pairs of an `!egm` builder's closing Evaluation, where a grid is refused, or "
                "its own nodes on the grid of its place. Numerical use needs at least two finite "
                "strictly increasing nodes with aligned finite values; evaluation outside the "
                "node interval is refused."
            ),
            example=(
                "dcsn_to_arvl.evaluate.method : !pchip\n"
                "dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))"
            ),
            example_meaning=(
                "The arrival value is represented by the shape-preserving cubic between its "
                "values at `n_k` evenly spaced points of assets from `k_min` to `k_max`."
            ),
            implementation=(
                "The scalar evaluator `consumption-perfect-foresight-crra:Pchip`, the class "
                "`Pchip` of the perfect-foresight application's module "
                "`code/closed_form_check.py`, evaluates it and its first and second "
                "derivatives with the slopes that SciPy's `PchipInterpolator` defines and "
                "refuses a point outside the node interval; the package itself supplies no "
                "evaluator."
            ),
            definition="bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain",
            type_parameters=(_DOMAIN, _CODOMAIN),
            related=("Linear", "closed-form"),
            source="bellman.stage.representations",
        ),
    )
)

register(
    RepresentationFamily(
        "closed-form",
        {},
        ("expression",),
        derivatives=(),
        evaluates=(
            "no derivative of its own: a derivative is offered only where an authored "
            "expression or an identified evaluator states it, and nothing is differentiated "
            "automatically"
        ),
        stored="The authored expression, with its parameters read at the calibration.",
        grid=None,
        text=EntryText(
            meaning=(
                "The family represents a function by its complete authored expression, "
                "evaluated through the compiled kernel of that expression at the calibration."
            ),
            compatibility=(
                "The family reads a complete authored expression with an explicit kernel: the "
                "lines of an `!explicit` builder at its closing Evaluation, where it stands by "
                "default, or "
                "the expression of a line, a `!node` line or a declared function. It refuses a "
                "representation grid, a table and the pairs of `!egm`. The expression owes its "
                "stated conditions on the domain where the function is evaluated."
            ),
            example="policy.evaluate.method : !closed_form",
            example_meaning=(
                "The consumption function is read from the expression the lines of the "
                "`!explicit` policy builder write, with no grid and no fitted data."
            ),
            implementation=(
                "The compiled kernel of the authored expression, `compile_kernel()` of the row "
                "that holds it, evaluates the function; no other procedure is needed."
            ),
            definition="bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain",
            type_parameters=(_DOMAIN, _CODOMAIN),
            related=("explicit", "Linear", "pchip"),
            source="bellman.stage.representations",
        ),
    )
)
