"""The grid constructors of the language, their records, the checks that read
those records, and the numerical construction of a grid at the bound values
(AMD-MT-003 build contract §§2, 7).

A grid is the finite set of points at which a method computes and stores a
function. A typing entry writes it at an operator's place as one outer grid
word: `!Cartesian(a=(a_min, a_max, n_a))`, the product of one node set per
coordinate of the place; `!Points(nodes=P)`, the finite support of declared
points, and `!Points` alone, the empty grid; and `!Fibred(base=…, fibre=…)`,
each state of a finite base paired with the points of its control's feasible
set, a grid of feasible pairs of states and controls. Each word may carry,
after `require`, the predicate words its grid satisfies, `!Empty`,
`!Cartesian`, `!NonCartesian` and `!UniformCartesian`.

`GRID_CONSTRUCTORS` holds one `GridConstructor` record per word, in the order
Cartesian, Points, Fibred, with its arguments, its explanation, its exact
declaration forms and the sites it may stand at, and Cartesian's factor forms
as `FactorForm` records; `PREDICATES` holds the predicate words with their
meanings. These records are the one statement of the grid words and their
arguments: the checks below and those of `components.py` read them, and the
generated reference prints them. The source words are read from the syntax
layer's table, `GRID_WORDS` of `syntax/source.py`.

A grid is checked in three steps. At binding, where an entry is read into a
stage, `check_grid_at_binding` refuses a constructor at a site its record
does not admit, an argument its record requires that the entry leaves out, a
base or a fibre of another form than its record states, an unknown or a
contradictory predicate word, and declared points that are no setting or
finite set of the place's shape. At configuration,
`check_grid_at_configuration` checks the configured points and decides each
requirement the bound values decide, by constructing the grid. A requirement
or a feasibility condition the bound values do not decide, and a coordinate no
factor names, remain obligations and refuse nothing there; the numerical
construction (`grid_records`) establishes them before the grid is used and
reports what it cannot establish, never supplying a default.

The domain a grid discretizes is read from the stage (`grid_domain`): the
coordinates of the function the place holds, or the continuation states for a
word whose row names that perch, with the controls and the shocks of the
stage. The builder's `kernels()` holds realized grids and handler inputs
(`grid_records`), and `same_grid` compares two realized grids exactly.
"""

from __future__ import annotations

import dataclasses
import itertools
import math
from collections.abc import Mapping
from fractions import Fraction
from types import MappingProxyType
from typing import NamedTuple

from bellman.fold.block_lines import (
    blocks_in_file_order,
    fields_of,
    header_of,
    header_wire_sorts,
    setting_sets,
)
from bellman.fold.derived_parameters import derived_values
from bellman.fold.stage_names import StageNames, lines_of
from bellman.fold.wire_terms import (
    spelled_with_mark,
    symbol_occurrences,
    term_nodes,
    term_of_name,
)
from bellman.native.frozen import freeze
from bellman.native.identity import Identity
from bellman.native.records import (
    EntryText,
    MethodOption,
    Refusal,
    TypeParameter,
    entry_position,
    grid_factors,
    refuse_at_entry,
    typing_text,
)
from bellman.refusals import ConstructionError
from bellman.stage.boxes import builder_rows_of
from bellman.stage.calibration_requirements import membership
from bellman.stage.input_requirements import _checking_value, continuation_inputs
from bellman.stage.method_rows import OUTPUT_PERCH
from bellman.stage.places import block_box, components_by_place, typings
from bellman.stage.representations import _exact, bound_row, supports_equal
from bellman.syntax import terms as T
from bellman.syntax.source import GRID_WORDS, grid_word, to_source
from bellman.syntax.vocabulary import (
    CONTINUATION,
    CONTROL,
    EXTENDED_REAL,
    INTEGER,
    REAL,
    SHOCK,
    STATE,
)
from bellman.typing import sets
from bellman.typing.ranges import substituted

# --- the records of the grid constructors ---

# the reader of a grid at a place whose entries name no method word: the
# handler the place binds
HANDLER = "handler"

# the readers a site may name: the two values of a method row's `grid` and
# the handler of a place with no method word
_READERS = (OUTPUT_PERCH, CONTINUATION, HANDLER)

# the domain a constructor's sites compare: the coordinates of the function
# the place holds, or the product of the occurrence's named states and the
# controls of the fibre
FUNCTION_DOMAIN = "function"
STATE_CONTROL_DOMAIN = "state-control"


@dataclasses.dataclass(frozen=True)
class GridSites:
    """The places a grid constructor may stand at (build contract §§2, 7):
    `readers`, the readers of the grid at those places, among
    `method_rows.OUTPUT_PERCH` and `vocabulary.CONTINUATION`, the values of a
    method row's `grid`, and `HANDLER`, a place whose entries name no method
    word; `domain`, `FUNCTION_DOMAIN`, the coordinates of the function the
    place holds, or `STATE_CONTROL_DOMAIN`, the product of the occurrence's
    named states and the fibre's controls; and `condition`, the sentence that
    states the rule. The record governs the outer word of an entry; a word
    nested in the base or the fibre of `!Fibred` is restricted by that
    argument's record."""

    readers: tuple
    domain: str
    condition: str

    def __post_init__(self):
        object.__setattr__(self, "readers", tuple(self.readers))
        unknown = [reader for reader in self.readers if reader not in _READERS]
        if unknown:
            raise ValueError(f"GridSites.readers are among {', '.join(_READERS)}; got {unknown}")
        if self.domain not in (FUNCTION_DOMAIN, STATE_CONTROL_DOMAIN):
            raise ValueError(
                f"GridSites.domain is {FUNCTION_DOMAIN!r} or {STATE_CONTROL_DOMAIN!r}; "
                f"got {self.domain!r}"
            )


@dataclasses.dataclass(frozen=True, eq=False)
class FactorForm:
    """One form of a factor of `!Cartesian`, keyed in an entry by its
    coordinate's name: `written`, the form as a stage file writes it for the
    coordinate `a`, `m`, `ν` or `c`; `term`, the factor's term class;
    `meaning`, one sentence; and `arguments`, a read-only mapping from the name
    of each part of the factor, the field of its term that holds it, to its
    `MethodOption`. A part of the kind `SETTING` names a setting a methods
    file declares; the spacing word of a spaced factor keeps its own keyword
    arguments for its handler."""

    written: str
    term: type
    meaning: str
    arguments: Mapping

    def __post_init__(self):
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))


@dataclasses.dataclass(frozen=True, eq=False)
class GridConstructor:
    """The record of one grid constructor (build contract §§2, 7): `word`, its
    source word without the `!`; `term`, its term class; `arguments`, a
    read-only mapping from each argument's name to its `MethodOption`, the
    coordinate factors of `!Cartesian` under the name `<coordinate>`; `text`,
    the `EntryText` its reference entry prints, whose type parameters hold the
    grid's domain, inferred from the site; `syntax`, the exact declaration
    forms, source templates with `<place>` for the site, each of which may also
    carry `require=<predicate word or tuple of them>`, printed last; `sites`,
    the `GridSites` it may stand at; and `forms`, the `FactorForm` records of
    the factors of `!Cartesian`."""

    word: str
    term: type
    arguments: Mapping
    text: EntryText
    syntax: tuple
    sites: GridSites
    forms: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        object.__setattr__(self, "syntax", tuple(self.syntax))
        object.__setattr__(self, "forms", tuple(self.forms))


# the kinds of value the parts of a factor take: a setting a methods file
# declares, the spacing word of a spaced factor, the node set of a listed
# factor, the expectation operator of a quadrature factor, and the feasible
# set of a control
SETTING = "setting"
SPACING = "spacing word"
NODE_SET = "node set"
EXPECTATION = "expectation operator"
FEASIBLE_SET = "feasible set"

# The predicate words a grid may require, each with its meaning on a grid of
# fixed named coordinates (the typing appendix of AMD-MT-003, §5): Empty,
# Cartesian and NonCartesian divide the grids on a fixed product between
# them, and UniformCartesian is a property of some Cartesian grids. A word is
# a condition on the resulting grid and no component of the entry.
PREDICATES = MappingProxyType(
    {
        "Empty": "The grid holds no point.",
        "Cartesian": (
            "The grid is nonempty and holds every combination of its projected coordinate values."
        ),
        "NonCartesian": (
            "The grid is nonempty and misses some combination of its projected coordinate values."
        ),
        "UniformCartesian": (
            "The grid is Cartesian on at least one real coordinate, with at least two "
            "distinct, equally spaced values in every coordinate."
        ),
    }
)


def _predicate_words():
    """The predicate words as a sentence lists them, each with its `!`."""
    words = [f"!{word}" for word in PREDICATES]
    return ", ".join(words[:-1]) + " and " + words[-1]


# the argument every grid constructor takes after its own
_REQUIRE = MethodOption(
    "predicate words",
    conditions=(
        f"one of {_predicate_words()}, or a tuple of them, of which no two contradict each other",
    ),
    description=(
        "The properties the resulting grid satisfies, decided at configuration where the "
        "bound values decide them and established before numerical use; inside the fibre of "
        "!Fibred they concern each fibre."
    ),
)

# the four factor forms of !Cartesian, each part named by the field of its
# term that holds it
_FACTOR_FORMS = (
    FactorForm(
        "a=(a_min, a_max, n_a)",
        T.Spaced,
        "Equally spaced nodes from the lower bound to the upper bound, both included; with a "
        "spacing word written as a fourth item, `a=(a_min, a_max, n_a, !expmult)`, the nodes "
        "that word's handler places between the bounds.",
        {
            "lower": MethodOption(
                SETTING,
                required=True,
                conditions=(
                    "a finite real inside the coordinate's declared set, below the upper bound",
                ),
                description="The setting whose value is the lowest node.",
            ),
            "upper": MethodOption(
                SETTING,
                required=True,
                conditions=(
                    "a finite real inside the coordinate's declared set, above the lower bound",
                ),
                description="The setting whose value is the highest node.",
            ),
            "count": MethodOption(
                SETTING,
                required=True,
                conditions=("an integer of at least two",),
                description="The setting whose value is the number of nodes.",
            ),
            "spacing": MethodOption(
                SPACING,
                conditions=(
                    "each bare name among its keyword arguments is a declared setting; a "
                    "number is refused and quoted text is retained",
                ),
                description=(
                    "A word naming an uneven spacing, such as `!expmult`, whose keyword "
                    "arguments are retained for its handler; when it is left out the nodes are "
                    "equally spaced."
                ),
            ),
        },
    ),
    FactorForm(
        "m=M_nodes",
        T.Listed,
        "The listed nodes, in their order.",
        {
            "nodes": MethodOption(
                NODE_SET,
                required=True,
                conditions=(
                    "a setting valued by a strictly increasing sequence of at least two finite "
                    "reals inside the coordinate's declared set, or a set the stage defines by "
                    "its members",
                ),
                description="The setting or the defined set that lists the nodes.",
            ),
        },
    ),
    FactorForm(
        "ν=E_ν",
        T.Listed,
        "The quadrature nodes of the expectation operator that integrates the shock coordinate.",
        {
            "nodes": MethodOption(
                EXPECTATION,
                required=True,
                conditions=(
                    "an expectation operator the lines of the stage write, for a shock coordinate",
                ),
                description=(
                    "The stage-wide name of the expectation operator, `E_ν`, whose handler "
                    "computes the nodes."
                ),
            ),
        },
    ),
    FactorForm(
        "c=(Γ_c, n_c)",
        T.Feasible,
        "A grid of the control's feasible set at each state, a family of grids indexed by the "
        "states; `!Fibred` pairs it with the states of a base to make one joint grid.",
        {
            "set": MethodOption(
                FEASIBLE_SET,
                required=True,
                conditions=(
                    "a correspondence or a set the stage defines, the control's feasible values "
                    "at each state",
                ),
                description="The feasible set of the control.",
            ),
            "count": MethodOption(
                SETTING,
                required=True,
                conditions=("an integer of at least two",),
                description=(
                    "The setting whose value is the number of control nodes at each state."
                ),
            ),
        },
    ),
)

# the formal definition of a grid, a page of the documentation with its
# section, written relative to the folder `docs/`
_DEFINITION = "bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain"

# the type parameter of a grid on the domain of the place's function
_DOMAIN = TypeParameter(
    "X",
    "It is the domain of the grid, whose coordinates are those of the function the place "
    "holds, in their declared order, or the continuation states for !egm.",
)

# The arguments, the explanation, the declaration forms and the sites of
# each grid constructor, by its term class; the word of each is the syntax
# layer's (`GRID_WORDS`).
_DEFINED = {
    T.Cartesian: dict(
        arguments={
            # The factor of each coordinate is optional: a coordinate no
            # factor names keeps its obligation and is admitted. The lowering
            # refuses a grid that writes no factor at all.
            "<coordinate>": MethodOption(
                "factor",
                conditions=(
                    "names a coordinate of the place, a control of the stage for a "
                    "feasible-control factor or a shock for an expectation factor",
                    "written in one of the four factor forms; at least one factor is written, "
                    "and a coordinate no factor names keeps its obligation",
                ),
                description="At most one factor per coordinate, keyed by the coordinate's name.",
            ),
            "require": _REQUIRE,
        },
        text=EntryText(
            meaning=(
                "The product of one finite node set per coordinate of the place, holding every "
                "combination of the coordinates' nodes."
            ),
            compatibility=(
                "Stands at the grid of a representation, of a solution method on the states of "
                "its output perch, of !egm on the continuation states, and of a place with no "
                "method word for its handler. Bounds, counts and listed nodes are settings; "
                "configuration checks the bounds in order and inside the coordinate's declared "
                "set, each count at least two, listed nodes strictly increasing, and the "
                "requirements the bound values decide. A coordinate no factor names keeps its "
                "obligation, which numerical construction reports before the grid is used."
            ),
            example="policy.grid : !Cartesian(a=(a_min, a_max, n_a), require=!UniformCartesian)",
            example_meaning=(
                "The grid of savings of !egm: n_a equally spaced points from a_min to a_max, "
                "both included, required to be uniform, which the construction establishes."
            ),
            implementation=(
                "The core constructs equally spaced and listed nodes at the configured "
                "settings, which a builder's `kernels().grids` holds. A spacing word is "
                "retained for its handler, of which the cons-port application implements the "
                "argument-free !expmult, and quadrature nodes come from the expectation's "
                "handler."
            ),
            definition=_DEFINITION,
            type_parameters=(_DOMAIN,),
            related=("Points", "Fibred"),
        ),
        syntax=("<place>.grid : !Cartesian(<coordinate>=<factor form>, …)",),
        sites=GridSites(
            (OUTPUT_PERCH, CONTINUATION, HANDLER),
            FUNCTION_DOMAIN,
            "Each factor names a coordinate of the place, a control of the stage for a "
            "feasible-control factor or a shock for an expectation factor.",
        ),
        forms=_FACTOR_FORMS,
    ),
    T.PointGrid: dict(
        arguments={
            "nodes": MethodOption(
                "declared points",
                conditions=(
                    "a set the stage defines by its finite members, or a setting declared on a "
                    "fixed finite product of points of the place's domain",
                    "each point has one coordinate for each coordinate of the domain, in its "
                    "declared order, each a finite real inside the coordinate's declared set",
                ),
                description=(
                    "The name of the declared points; when it is left out, the grid is empty."
                ),
            ),
            "require": _REQUIRE,
        },
        text=EntryText(
            meaning=(
                "The finite support of declared points of the place's domain, each point given "
                "in the domain's declared coordinate order; !Points alone is the empty grid."
            ),
            compatibility=(
                "Stands where !Cartesian stands. The points are a set the stage defines by its "
                "finite members, or a setting declared on a fixed finite product of points, "
                "`X2 := ℝ × ℝ` and `P : X2 × X2 × X2`; configuration checks each point's shape, "
                "its finite real coordinates, its membership of the coordinates' declared sets "
                "where that is decided, and the requirements. Repeated points collapse in the "
                "support, and an interpolation procedure may still require at least two nodes."
            ),
            example="policy.grid : !Points(nodes=A_points)",
            example_meaning=(
                "The grid of savings of !egm is the set of the configured points of the setting "
                "A_points, declared `A_points : ℝ₊ × ℝ₊ × ℝ₊`: three points of the one "
                "coordinate a."
            ),
            implementation=(
                "The core constructs the support at the configured settings, which a builder's "
                "`kernels().grids` holds."
            ),
            definition=_DEFINITION,
            type_parameters=(_DOMAIN,),
            related=("Cartesian", "Fibred"),
        ),
        syntax=("<place>.grid : !Points(nodes=<declared points>)", "<place>.grid : !Points"),
        sites=GridSites(
            (OUTPUT_PERCH, CONTINUATION, HANDLER),
            FUNCTION_DOMAIN,
            "The points lie in the domain of the place, in its declared coordinate order.",
        ),
    ),
    T.Fibred: dict(
        arguments={
            "base": MethodOption(
                "grid word",
                required=True,
                conditions=(
                    "!Points or a !Cartesian term without feasible-control factors, on the "
                    "states of the occurrence",
                    "complete before numerical construction; a state no factor names keeps its "
                    "obligation",
                ),
                description=(
                    "The grid of the states at which the control's feasible set is sampled."
                ),
            ),
            "fibre": MethodOption(
                "grid word",
                required=True,
                conditions=(
                    "a !Cartesian term whose factors are feasible-control factors, `c=(Γ_c, n_c)`",
                    "one control in the numerical construction; several controls or a coupled "
                    "restriction report unsupported joint sampling",
                ),
                description=(
                    "The grid of the control at each base state, sampled from its feasible set."
                ),
            ),
            "require": _REQUIRE,
        },
        text=EntryText(
            meaning=(
                "Each state of a finite base paired with the finite feasible grid of the "
                "control at that state: a grid of feasible pairs of states and controls."
            ),
            compatibility=(
                "Stands at a solution method whose grid lies on the states of its output perch; "
                "such a method chooses or solves over the place's states and the stage's "
                "controls. Fibred stands at a representation or at a place with no method word "
                "only for a function whose coordinates are the base's states followed by the "
                "fibre's controls, and a representation of a function of states alone refuses it. "
                "The base is !Points or a !Cartesian term without feasible-control factors and "
                "must be complete before numerical construction; the fibre is a !Cartesian term "
                "of feasible-control factors. An outer requirement concerns the joint grid, and a "
                "requirement inside the fibre concerns each fibre."
            ),
            example=(
                "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), "
                "fibre=!Cartesian(c=(Γ_c, n_c)))"
            ),
            example_meaning=(
                "With B = {1, 2}, Γ_c(m) = [0, m] and n_c = 2, the grid of value function "
                "iteration is the four pairs (1, 0), (1, 1), (2, 0) and (2, 2)."
            ),
            implementation=(
                "The core constructs the case of one control: at each base state it evaluates "
                "the control's feasible interval at the arguments the stage applies it to and "
                "places the declared count of equally spaced points, both closed finite "
                "endpoints included. An open or unbounded interval reports an unresolved "
                "numerical requirement, and several controls or a coupled restriction report "
                "unsupported joint sampling."
            ),
            definition=_DEFINITION,
            type_parameters=(
                TypeParameter(
                    "X",
                    "It is the set of states of the occurrence, on which the base lies.",
                ),
                TypeParameter(
                    "C",
                    "It is the declared set of the fibre's control; the grid lies in the graph of "
                    "the control's feasible set, a subset of X × C.",
                ),
            ),
            related=("Points", "Cartesian"),
        ),
        syntax=(
            "<place>.grid : !Fibred(base=<!Points or !Cartesian term>, "
            "fibre=!Cartesian(<control>=(<feasible set>, <count>), …))",
        ),
        sites=GridSites(
            (OUTPUT_PERCH, HANDLER),
            STATE_CONTROL_DOMAIN,
            "The domain of the occurrence is the product of the base's states and the fibre's "
            "controls; a place of any other coordinate domain refuses.",
        ),
    ),
}

if set(_DEFINED) != set(GRID_WORDS):
    raise RuntimeError(
        "the grid constructors defined here and the grid words of the syntax layer differ: "
        f"{sorted(cls.__name__ for cls in set(_DEFINED) ^ set(GRID_WORDS))}"
    )

# The one table of the grid constructors, by word, in the order of the syntax
# layer's words: Cartesian, Points, Fibred.
GRID_CONSTRUCTORS = MappingProxyType(
    {word: GridConstructor(word, term, **_DEFINED[term]) for term, word in GRID_WORDS.items()}
)


def constructor_of(grid):
    """The `GridConstructor` record of a grid term, a `Cartesian`, a
    `PointGrid` or a `Fibred`."""
    word = GRID_WORDS.get(type(grid))
    if word is None:
        raise TypeError(f"constructor_of reads a grid term; got {type(grid).__name__}")
    return GRID_CONSTRUCTORS[word]


def factor_form_of(factor, expectations=frozenset()):
    """The `FactorForm` record of a factor of `!Cartesian`: the spaced, the
    listed, the quadrature or the feasible form, read by the factor's term; a
    listed factor whose node set is among `expectations`, the stage-wide names
    of the expectation operators, has the quadrature form."""
    found = [
        form for form in GRID_CONSTRUCTORS["Cartesian"].forms if isinstance(factor, form.term)
    ]
    if len(found) > 1:
        quadrature = factor.nodes in expectations
        found = [
            form for form in found if (form.arguments["nodes"].kind == EXPECTATION) == quadrature
        ]
    if len(found) != 1:
        raise TypeError(f"factor_form_of reads a factor of a grid; got {type(factor).__name__}")
    return found[0]


# --- the domain a grid discretizes ---


class GridDomain(NamedTuple):
    """The coordinates a grid at one place may discretize: `states`, the
    coordinates of the function the place holds, each with its declared set,
    in declared order, for each of which a grid may name a factor;
    `controls`, the controls of the stage with their declared sets, for a
    feasible factor; `shocks`, the shocks of the stage, for a quadrature
    factor; and `expectations`, the stage-wide names of the expectation
    operators, `E_ψ_ξ`, whose nodes a quadrature factor takes."""

    states: Mapping
    controls: Mapping
    shocks: tuple
    expectations: frozenset


def grid_domain(stage, box, block, row):
    """The `GridDomain` of the box `box` in the builder `block`, for a word
    whose row is `row`, None for a place with no method word: the states
    are those of the continuation perch for a word whose row names it,
    `!egm`, and otherwise the coordinates of the function the box holds
    (`place_coordinates`)."""
    states = (
        _perch_states(stage, CONTINUATION)
        if row is not None and row.grid == CONTINUATION
        else place_coordinates(stage, box, block)
    )
    # the controls of the stage, which stand at the decision perch, for a
    # feasible factor; the shocks of the stage for a quadrature factor
    declared, _ = fields_of(stage)
    controls = {}
    for identity, sort in header_wire_sorts(stage).items():
        if sort.role == CONTROL:
            controls.setdefault(identity.field, sort.domain)
    shocks = tuple(dict.fromkeys(i.field for i, sort in declared.items() if sort.role == SHOCK))
    return GridDomain(states, controls, shocks, expectation_names(stage))


def place_coordinates(stage, box, block):
    """The coordinates of the function the box `box` holds, each with its
    declared set, in declared order: the arguments of the retained row at
    the box, the one Evaluation of the builder where the box is the builder
    itself, the coordinates of a declared function, and otherwise the states
    of the perch at which the outputs of the builder `block` stand, the
    output perch of a forward builder."""
    row = place_row(stage, box)
    declared, _ = fields_of(stage)
    if row is not None and row.arguments:
        return {
            identity.field: declared[identity].domain
            for identity in row.arguments
            if identity in declared
        }
    definition = stage.definitions.get(box) if isinstance(box, Identity) else None
    if definition is not None:
        return _definition_coordinates(stage, definition)
    return _perch_states(stage, _output_perch(stage, block))


def _definition_coordinates(stage, definition, seen=frozenset()):
    """The coordinates of a declared function with their sets; for a function
    alias, those of the function its body refers to or differentiates,
    `𝑑𝑢 := D_{c}(𝑢)`, and none for an alias of another form, such as an
    inverse, whose argument is no named coordinate."""
    if definition.coordinates or definition.kind != "function_alias" or not definition.equations:
        return dict(definition.coordinates)
    body = definition.equations[0]
    if isinstance(body, T.Operator) and body.head == "D" and len(body.args) == 1:
        body = body.args[0]
    name = (
        body.symbol.name
        if isinstance(body, T.Sym) and isinstance(body.symbol, T.Constant)
        else None
    )
    if name is None or name in seen:
        return {}
    referred = next(
        (
            d
            for d in stage.definitions.values()
            if d.kind in ("function", "function_alias") and d.identity.field == name
        ),
        None,
    )
    return {} if referred is None else _definition_coordinates(stage, referred, seen | {name})


def place_row(stage, box):
    """The retained operator row at a box, where there is one: the row whose
    identity is the box, or the one Evaluation of the builder for a box that
    is the builder itself; None otherwise, and for a builder whose rows the
    construction refuses."""
    block = box if isinstance(box, str) else getattr(box, "block", None)
    if block is None:
        return None
    try:
        rows = builder_rows_of(stage, block).closed
    except (KeyError, TypeError, ValueError, ConstructionError):
        return None
    found = tuple(row for row in rows if row.identity == box)
    if len(found) == 1:
        return found[0]
    evaluations = tuple(row for row in rows if row.kind == "Evaluation")
    return evaluations[0] if len(evaluations) == 1 else None


def _output_perch(stage, block):
    """The perch at which the outputs of the builder `block` stand, read
    from the sort of its first output wire; None for no such builder."""
    ports = header_wire_sorts(stage)
    held = next((b for b in blocks_in_file_order(stage) if b.name == block), None)
    if held is None:
        return None
    for wire in header_of(held).outputs:
        if wire.identity in ports:
            return wire.identity.perch
    return None


def _perch_states(stage, perch):
    """The declared states of the perch `perch` with their declared sets, in
    first-listing order."""
    declared, _ = fields_of(stage)
    return {
        identity.field: declared[identity].domain
        for identity, sort in header_wire_sorts(stage).items()
        if identity.perch == perch and sort.role == STATE and identity in declared
    }


def expectation_names(stage):
    """The stage-wide names of the expectation operators the lines of the
    stage write, `E_ψ_ξ`, which a quadrature factor names."""
    return frozenset(
        occurrence.stage_wide_name
        for block in blocks_in_file_order(stage)
        for _, record in lines_of(stage, block)
        for occurrence in record.operators
        if occurrence.head == "E"
    )


def point_in_declared_set(stage, value, declared, calibration=None):
    """True, False, or None for the membership of a number in a declared
    set, decided by the set algebra through the sets the stage defines.
    Where the set algebra leaves it undecided and `calibration` holds
    parameter values, as it does for a set whose endpoint is a parameter,
    `Xa := [a_Art, inf)`, the membership is decided at those values as the
    value of a setting is (`calibration_requirements.membership`), so that a
    setting and a grid bound of one value in one set receive one answer."""
    point = T.Interval(
        T.Range(left=T.Closed(), lower=T.Number(value), upper=T.Number(value), right=T.Closed())
    )
    member = sets.within(point, declared, _set_definitions(stage))
    if member is None and calibration:
        try:
            status, _ = membership(stage, dict(stage.definitions), declared, value, calibration)
        except ValueError:
            # a bound of the set has no value at the calibration, `[1/k_lo,
            # inf)` at k_lo = 0, so nothing decides the membership
            return None
        if status is True or status is False:
            return status
    return member


def parameters_read_at(stage, declared, calibration):
    """The values of the parameters a declared set reads, ` at a_Art = 0.5`,
    for the sentence that refuses a point judged at them; nothing for a set
    that reads no parameter `calibration` values. A set the stage defines by
    name is read through its definition."""
    if not calibration or declared is None:
        return ""
    definitions = _set_definitions(stage)
    read, followed, pending = [], set(), [declared]
    while pending:
        for node in term_nodes(pending.pop(0)):
            if isinstance(node, T.Named) and node.name in definitions:
                if node.name not in followed:
                    followed.add(node.name)
                    pending.append(definitions[node.name])
            elif isinstance(node, T.Sym) and isinstance(node.symbol, T.Constant):
                name = node.symbol.name
                if name in calibration and name not in read:
                    read.append(name)
    return " at " + ", ".join(f"{name} = {calibration[name]!r}" for name in read) if read else ""


def _set_definitions(stage):
    """The sets the stage defines, each name with its defining term."""
    return {
        definition.identity.field: definition.equations[0]
        for definition in stage.definitions.values()
        if definition.kind == "set" and definition.equations
    }


# --- the checks at binding ---


def check_grid_at_binding(stage, place, held, row, record):
    """The checks of the grid typed at `place`, whose components are `held`,
    its method's row `row` (None for a place with no method word) and its
    typing record `record`, that bind before configuration; each reads the
    records of the constructors. A constructor at a reader or a domain its
    record's `sites` do not admit is refused under `grid-coordinate`, quoting
    the record's condition, with the first form of a constructor that stands
    there as the correction. An argument its record requires and the entry
    leaves out is refused under `syntax`; a base of `!Fibred` other than
    `!Points` or a `!Cartesian` term without feasible-control factors, and a
    fibre other than a `!Cartesian` term of feasible-control factors, under
    `grid-coordinate`; a predicate word `PREDICATES` does not hold, and two
    words no grid satisfies together, under `grid-requirement`. The declared
    points of `!Points` are a setting a methods file declares or a set the
    stage defines (`grid-setting-declared`), whose points have the shape of
    the place's domain (`grid-coordinate`). The coordinates and the names of
    the factors are checked by `components.py`."""
    grid = held.grid
    reader = HANDLER if row is None else row.grid
    domains = [grid_domain(stage, box, place.block, row) for box in place.boxes]
    _check_arguments(stage, place, record, grid)
    for domain in domains:
        _check_site(stage, place, record, grid, held, row, reader, domain)
    for domain in domains:
        for term, coordinates in _point_terms(grid, domain):
            if term.nodes is not None:
                _check_declared_points(stage, place, record, grid, term, coordinates)


def grid_sum_operands(stage, place, argument):
    """A grid sum's constant and setting at its attachment place."""

    if place.block is None or not isinstance(argument.value, T.Add):
        return None
    operands = tuple(symbol_occurrences(argument.value))
    if len(operands) != 2:
        return None
    block = block_box(stage, place.block)
    listed = dict(zip(block.data.input_spellings, header_of(block).inputs))
    external = {sort.identity for sort in continuation_inputs(stage).values()}
    declared = setting_sets(stage)
    definitions = _set_definitions(stage)

    def scalar(term):
        term = sets.resolved(term, definitions)
        primitive = sets.primitive_of(term)
        return (
            primitive is not None and primitive.kind == EXTENDED_REAL
            or sets.numeric(term, definitions) is True
            and sets.kind_without_numbers(term, definitions) is None
        )

    candidates = []
    for setting, field in (operands, operands[::-1]):
        name, side = setting
        written = spelled_with_mark(field)
        sort = listed.get(written)
        if (
            side is None and name in declared and scalar(declared[name])
            and sort is not None and sort.constant and sort.identity in external
            and scalar(sort.domain)
        ):
            candidates.append((written, sort.identity, name))
    return candidates[0] if len(candidates) == 1 else None


def _clause(sentence):
    """A record's sentence as a clause of a refusal: its first letter in
    lower case and its full stop removed."""
    return sentence[:1].lower() + sentence[1:].rstrip(".")


def _check_site(stage, place, record, grid, held, row, reader, domain):
    """The rule of the constructor's `sites` at one box of the place: its
    reader is among the readers the record names, and for a constructor of
    the domain `STATE_CONTROL_DOMAIN`, `!Fibred`, the occurrence's domain is
    the base's states followed by the fibre's controls. At a solution method
    whose grid lies on the states of its output perch, the occurrence's
    domain is the place's coordinates and the stage's controls, the domain
    the method chooses or solves over; at a representation and at a place
    with no method word it is the place's coordinates alone."""
    sites = constructor_of(grid).sites
    if reader not in sites.readers:
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-coordinate",
            f"the grid {to_source(grid)} stands at {_reader_text(held, reader)}, where the "
            f"record of {grid_word(grid)} admits it at no place; {_clause(sites.condition)}",
            write=_correction(place, reader),
        )
    if sites.domain != STATE_CONTROL_DOMAIN:
        return
    occurrence = tuple(domain.states) + (
        tuple(domain.controls) if row is not None and row.kind == "solution" else ()
    )
    controls = _fibre_controls(grid)
    states = tuple(name for name in domain.states if name not in controls)
    if not (
        len(occurrence) == len(states) + len(controls)
        and occurrence[: len(states)] == states
        and sorted(occurrence[len(states) :]) == sorted(controls)
    ):
        word = f"!{held.method.name}" if held.method is not None else "the place's handler"
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-coordinate",
            f"{word} at {place.address} reads a grid on "
            f"({', '.join(occurrence) or 'no coordinate'}), and the grid {to_source(grid)} "
            f"constructs pairs on ({', '.join(states + controls)}); {_clause(sites.condition)}",
            write=_correction(place, reader),
        )


def _reader_text(held, reader):
    """The place of a grid in words, by its reader."""
    if reader == CONTINUATION:
        return f"the grid of !{held.method.name}, on the states of the continuation perch"
    if reader == OUTPUT_PERCH:
        return f"the grid of !{held.method.name}, on the coordinates of its place"
    return "a place with no method word, whose handler reads the grid"


def _correction(place, reader):
    """The action of a refusal of a constructor at its site: the first form
    of a constructor whose sites admit the place's reader on the domain of
    its function, written at the place."""
    for constructor in GRID_CONSTRUCTORS.values():
        sites = constructor.sites
        if reader in sites.readers and sites.domain == FUNCTION_DOMAIN:
            form = constructor.syntax[0].replace("<place>", place.address)
            return f"Write a grid that stands at this place, `{form}`"
    return f"Remove the grid entry of `{place.address}`"


def _fibre_controls(grid):
    """The controls the fibre of a fibred grid names, in written order."""
    return tuple(dict.fromkeys(factor.coordinate for factor in grid_factors(grid.fibre)))


# the field of a grid term that holds an argument whose name is not the
# field's: the factors of !Cartesian, keyed by their coordinates
_ARGUMENT_FIELD = {"<coordinate>": "factors"}


def _check_arguments(stage, place, record, grid, where=""):
    """The arguments of one grid term and of the terms nested in it, read
    from the records: each argument its record requires is written, the
    base and the fibre of `!Fibred` have the forms their records state, and
    the predicate words after `require` are known and consistent. `where`
    places a nested term in the words of a refusal."""
    constructor = constructor_of(grid)
    for name, option in constructor.arguments.items():
        value = getattr(grid, _ARGUMENT_FIELD.get(name, name))
        if option.required and (value is None or value == ()):
            refuse_at_entry(
                stage,
                place.address,
                record,
                "syntax",
                f"the grid {grid_word(grid)}{where} of the entry `{typing_text(record)}` leaves "
                f"out {name}, which its record requires: {option.description[:1].lower()}"
                f"{option.description[1:].rstrip('.')}",
                write=f"Write the grid in the form `{constructor.syntax[0]}`",
            )
    _check_requirement_words(stage, place, record, grid, where)
    if not isinstance(grid, T.Fibred):
        return
    base, fibre = grid.base, grid.fibre
    if not isinstance(base, (T.PointGrid, T.Cartesian)) or any(
        isinstance(factor, T.Feasible) for factor in grid_factors(base)
    ):
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-coordinate",
            f"the base of the grid {to_source(grid)} is {to_source(base)}; the base of "
            f"{grid_word(grid)} is {constructor.arguments['base'].conditions[0]}",
            write="Write the base on the states, `base=!Points(nodes=B)` or "
            "`base=!Cartesian(m=(m_min, m_max, n_m))`",
        )
    if not isinstance(fibre, T.Cartesian) or not all(
        isinstance(factor, T.Feasible) for factor in fibre.factors
    ):
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-coordinate",
            f"the fibre of the grid {to_source(grid)} is {to_source(fibre)}; the fibre of "
            f"{grid_word(grid)} is {constructor.arguments['fibre'].conditions[0]}",
            write="Write the fibre as the control's feasible set with a count, "
            "`fibre=!Cartesian(c=(Γ_c, n_c))`",
        )
    _check_arguments(stage, place, record, base, " in the base of !Fibred")
    _check_arguments(stage, place, record, fibre, " in the fibre of !Fibred")


def _check_requirement_words(stage, place, record, grid, where):
    """The predicate words one grid term writes after `require`: each is a
    key of `PREDICATES`, and no two contradict each other. A word
    `PREDICATES` holds with no checker here is a fault of the package, raised
    as such."""
    words = tuple(grid.require)
    unknown = tuple(word for word in words if word not in PREDICATES)
    if unknown:
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-requirement",
            f"the grid {grid_word(grid)}{where} requires "
            f"{', '.join(f'!{word}' for word in unknown)}, which "
            f"{'is no predicate word' if len(unknown) == 1 else 'are no predicate words'}; a "
            f"grid may require {_predicate_words()}, or a tuple of them",
            write=f"Write predicate words among {_predicate_words()}",
        )
    for word in words:
        if word not in _PREDICATE_CHECKS:
            raise RuntimeError(f"the predicate word !{word} has no checker in stage/grids.py")
    pair = _contradiction(words)
    if pair:
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-requirement",
            f"the grid {grid_word(grid)}{where} requires !{pair[0]} and !{pair[1]}, which "
            f"contradict each other: no grid satisfies both, since !Empty, !Cartesian and "
            f"!NonCartesian hold of disjoint grids and a !UniformCartesian grid is Cartesian",
            write="Write the requirements one grid can satisfy together",
        )


def _point_terms(grid, domain):
    """Each `!Points` term of a grid with the coordinates of its points: the
    outer word on the states of the domain, and the base of `!Fibred` on the
    states other than the fibre's controls."""
    if isinstance(grid, T.PointGrid):
        return ((grid, tuple(domain.states)),)
    if isinstance(grid, T.Fibred) and isinstance(grid.base, T.PointGrid):
        controls = _fibre_controls(grid)
        return ((grid.base, tuple(name for name in domain.states if name not in controls)),)
    return ()


def _check_declared_points(stage, place, record, grid, term, coordinates):
    """The declared points of one `!Points` term: a setting a methods file
    declares on a fixed finite product of points, or a set the stage defines
    by its finite members, each point with one coordinate for each of
    `coordinates`."""
    name = term.nodes
    settings = setting_sets(stage)
    definitions = _set_definitions(stage)
    shown = ", ".join(coordinates) or "no coordinate"
    hint = (
        "declare the points as a fixed finite product of points of the domain, "
        "`P : ℝ × ℝ × ℝ` for three points of one coordinate or `X2 := ℝ × ℝ` and "
        "`P : X2 × X2 × X2` for three points of two coordinates, or define a finite set by "
        "its members, `P := {1, 2, 3}`"
    )
    if not coordinates:
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-coordinate",
            f"the grid {to_source(grid)} names the points {name}, and the place has no "
            "coordinate for them to lie in",
            write=f"Remove the grid entry of `{place.address}`",
        )
    if name in settings:
        shape = _product_shape(settings[name], definitions)
        if shape is None:
            declared = "no set" if settings[name] is None else to_source(settings[name])
            reason = f"declared on {declared}, which is no fixed finite product of points"
        elif shape[1] != len(coordinates):
            reason = (
                f"declared on {to_source(settings[name])}, whose points have {shape[1]} "
                f"coordinate{'' if shape[1] == 1 else 's'} each"
            )
        else:
            return
    elif name in definitions:
        points = _defined_points(definitions[name], definitions)
        if points is None:
            reason = (
                f"defined as {to_source(definitions[name])}, which is no finite set of points "
                "written by its members"
            )
        elif any(len(point) != len(coordinates) for point in points):
            reason = (
                f"defined as {to_source(definitions[name])}, whose points do not have one "
                "coordinate for each coordinate of the domain"
            )
        else:
            return
    else:
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-setting-declared",
            f"the grid {to_source(grid)} names {name!r} as its points, which is no setting a "
            f"methods file declares and no set the stage defines; {hint}",
            write=f"Declare {name!r} as a setting on a fixed finite product of points",
        )
    refuse_at_entry(
        stage,
        place.address,
        record,
        "grid-coordinate",
        f"the grid {to_source(grid)} names the points {name}, {reason}, and the domain of the "
        f"place has the coordinates ({shown}); each point has one coordinate for each "
        f"coordinate of the domain, in its declared order; {hint}",
    )


def _product_shape(setexpr, definitions):
    """The number of points a fixed finite product of points holds and the
    number of coordinates of each, read from the set a setting is declared
    on: `ℝ × ℝ × ℝ`, three points of one coordinate, and `X2 × X2 × X2` with
    `X2 := ℝ × ℝ`, three points of two coordinates; None for a set of another
    form and for points of unequal widths."""
    if setexpr is None:
        return None
    held = sets.defined(setexpr, definitions)
    if not isinstance(held, T.Product):
        return None
    widths = set()
    for factor in held.factors:
        point = sets.defined(factor, definitions)
        widths.add(len(point.factors) if isinstance(point, T.Product) else 1)
    return (len(held.factors), widths.pop()) if len(widths) == 1 else None


def _defined_points(setexpr, definitions):
    """The points of a set the stage defines by its finite members, each a
    tuple of numbers in the order of the product's factors: a finite set of
    numbers, `{1, 2}`, a range of integers, or a product of such sets; None
    for a set of another form."""
    held = sets.defined(setexpr, definitions)
    if isinstance(held, T.Product):
        factors = [_members(sets.defined(factor, definitions)) for factor in held.factors]
        if any(members is None for members in factors):
            return None
        return tuple(itertools.product(*factors))
    members = _members(held)
    return None if members is None else tuple((member,) for member in members)


def _members(setexpr):
    """The numbers a finite set lists, in written order: the members of
    `{1, 2}` and the integers of a range with numeric bounds; None for a set
    of labels and for a set of another form."""
    if isinstance(setexpr, T.Points):
        values = tuple(sets.number_at(member, {}).value for member in setexpr.members)
        return None if any(value is None for value in values) else values
    if isinstance(setexpr, T.IntegerRange):
        lower, upper = (sets.number_at(end, {}).value for end in (setexpr.lower, setexpr.upper))
        if type(lower) is int and type(upper) is int:
            return tuple(range(lower, upper + 1))
    return None


# --- the checks at configuration ---


def check_grid_at_configuration(stage, place, held, values, domain):
    """The checks of the grid typed at `place` at the settings `values`, which
    `configure` makes, on the `GridDomain` `domain` of one box of the place:
    each configured point of `!Points` has the shape of the domain's
    coordinates, finite real coordinates and, where the set algebra or the
    calibration that is bound decides it, membership of each coordinate's
    declared set (`grid-bounds`); and each requirement written after
    `require` holds of the grid constructed at the bound values
    (`grid-requirement`), where those values decide it. Where construction
    cannot establish the grid, its omitted factors, an undecided membership
    or a feasible set without a sampler among them, the requirement remains
    an obligation and nothing is refused here."""
    grid = held.grid
    calibration = calibration_values(stage)
    for term, coordinates in _point_terms(grid, domain):
        _check_point_values(stage, place, held, values, term, coordinates, domain, calibration)
    if not _requirements(grid):
        return
    try:
        constructed = _construct(stage, grid, domain, values, calibration)
    except _Unresolved:
        return
    failure = _requirement_failure(grid, constructed)
    if failure is not None:
        record = next(
            typing.record
            for typing in typings(stage)
            if typing.place.address == place.address and typing.component == "grid"
        )
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-requirement",
            f"the grid {to_source(grid)}, constructed at the bound values: {failure}; a "
            "requirement written after `require` holds of the grid its construction gives",
            write="Write the requirements the constructed grid satisfies, or change the "
            "settings of its construction",
        )


def _requirements(grid):
    """Whether a grid term or a term nested in it writes a predicate word."""
    if grid.require:
        return True
    return isinstance(grid, T.Fibred) and (bool(grid.base.require) or bool(grid.fibre.require))


def calibration_values(stage):
    """The parameter values the version's calibration binds, joined by the
    value of each derived parameter at them (`derived_values`), so that a
    feasible set, a bound or a declared set that reads a parameter or a
    derived parameter is read at its value, while the stored calibration
    keeps the declared parameters alone (shared contract §8); empty on a
    symbolic version."""
    calibration = dict(stage.bindings.calibration or {})
    if not calibration:
        return calibration
    return {**calibration, **derived_values(stage, calibration)}


def _check_point_values(stage, place, held, values, term, coordinates, domain, calibration):
    """The configured or defined points of one `!Points` term: one finite
    real coordinate for each of `coordinates`, and each coordinate inside its
    declared set where the set algebra, or the parameter values
    `calibration`, decide the membership."""
    if term.nodes is None:
        return

    def refuse(reason, write):
        raise ConstructionError(
            f"stage {stage.name!r}, place {place.address!r}, grid {to_source(held.grid)}: the "
            f"points {term.nodes} {reason}; configure requires each point of !Points to have "
            "one finite real coordinate for each coordinate of the domain, in its declared "
            f"order, inside the coordinate's declared set; {write}",
            stage=stage.name,
            file=stage.provenance.get("origin"),
            address=place.address,
            rule="grid-bounds",
        )

    if term.nodes in values:
        rows = _point_rows(values[term.nodes], len(coordinates))
        if rows is None:
            refuse(
                f"= {values[term.nodes]!r} are no sequence of points of "
                f"{len(coordinates)} coordinate{'' if len(coordinates) == 1 else 's'} each",
                "write one entry for each point",
            )
    else:
        rows = _defined_points(_set_definitions(stage).get(term.nodes), _set_definitions(stage))
        if rows is None:
            return
    for row in rows:
        for name, value in zip(coordinates, row):
            if not _finite_real(value):
                refuse(
                    f"hold the point {row!r}, whose coordinate {name} is {value!r}",
                    "write finite reals",
                )
            declared = domain.states.get(name)
            if declared is None:
                continue
            if point_in_declared_set(stage, value, declared, calibration) is False:
                refuse(
                    f"hold the point {row!r}, whose coordinate {name} = {value!r} lies outside "
                    f"the declared set {to_source(declared)}"
                    f"{parameters_read_at(stage, declared, calibration)}",
                    "write points inside the declared sets",
                )


def _point_rows(value, width):
    """The points a configured value lists, each a tuple of `width`
    coordinates: a sequence of numbers for points of one coordinate, a
    sequence of sequences of `width` entries otherwise; None for a value of
    another shape."""
    if not isinstance(value, (list, tuple)):
        return None
    if width == 1:
        if any(isinstance(item, (list, tuple)) for item in value):
            return None
        return tuple((item,) for item in value)
    if not all(isinstance(item, (list, tuple)) and len(item) == width for item in value):
        return None
    return tuple(tuple(item) for item in value)


def _finite_real(value):
    """Whether a value is an integer that is no boolean or a finite float."""
    return type(value) is int or type(value) is float and math.isfinite(value)


# --- the numerical construction ---


class _Unresolved(Exception):
    """A requirement of a grid's numerical construction that the bound values
    and the identified procedures do not establish; its argument is the
    clause that says which."""


@dataclasses.dataclass(frozen=True)
class _Constructed:
    """A grid constructed in exact arithmetic: its source word, its
    coordinates, its points as tuples of `Fraction` without repetition in
    construction order, and for `!Fibred` its constructed base and each base
    point with the nodes of its fibre."""

    word: str
    coordinates: tuple
    points: tuple
    base: object = None
    fibres: tuple = ()


def _construct(stage, grid, domain, values, calibration):
    """The grid `grid` constructed on the `GridDomain` `domain` at the
    settings `values` and the parameter values `calibration`, or `_Unresolved`
    naming what cannot be established."""
    return _construct_on(stage, grid, dict(domain.states), domain, values, calibration)


def _construct_on(stage, grid, states, domain, values, calibration):
    """The construction of one grid term on the coordinates `states`, each
    with its declared set, in declared order."""
    if isinstance(grid, T.Fibred):
        return _fibred(stage, grid, domain, values, calibration)
    if isinstance(grid, T.PointGrid):
        return _points(stage, grid, states, values, calibration)
    return _cartesian(stage, grid, states, domain, values, calibration)


def _cartesian(stage, grid, states, domain, values, calibration):
    """The product, in the declared order of `states`, of the nodes of one
    factor per coordinate. A feasible factor is a family of grids indexed by
    the states, a quadrature factor's nodes come from its handler and a
    spacing word's from its handler, and a coordinate no factor names has
    no nodes: each is unresolved."""
    by_coordinate = {}
    for factor in grid.factors:
        if isinstance(factor, T.Feasible):
            raise _Unresolved(
                f"its factor {to_source(factor)} is a family of grids of the control "
                f"{factor.coordinate}, one at each state, and no one grid; "
                f"!Fibred(base=…, fibre=!Cartesian({to_source(factor)})) constructs the joint "
                "grid of states and controls"
            )
        if isinstance(factor, T.Listed) and factor.nodes in domain.expectations:
            raise _Unresolved(
                f"its factor {to_source(factor)} takes the quadrature nodes of "
                f"{factor.nodes}, which the expectation's handler computes, and the core "
                "identifies no construction of them"
            )
        by_coordinate[factor.coordinate] = factor
    nodes = []
    for name, declared in states.items():
        if name not in by_coordinate:
            raise _Unresolved(
                f"it names no factor for the coordinate {name}, and numerical construction "
                f"requires one for each coordinate of its domain, ({', '.join(states)})"
            )
        nodes.append(_coordinate_nodes(stage, by_coordinate[name], declared, values, calibration))
    return _Constructed(GRID_WORDS[T.Cartesian], tuple(states), tuple(itertools.product(*nodes)))


def _coordinate_nodes(stage, factor, declared, values, calibration):
    """The exact nodes of one spaced or listed factor at the settings, each
    inside the coordinate's declared set at the parameter values
    `calibration`, in order and without repetition."""
    if isinstance(factor, T.Spaced):
        if factor.spacing is not None:
            raise _Unresolved(
                f"its factor {to_source(factor)} names the spacing word "
                f"{to_source(factor.spacing)}, whose nodes its handler places, and the core "
                "identifies no construction of them"
            )
        lower, upper, count = (
            _setting_value(part, values) for part in (factor.lower, factor.upper, factor.count)
        )
        if not (sets.is_number(lower) and sets.is_number(upper) and lower < upper):
            raise _Unresolved(f"the bounds of its factor {to_source(factor)} are not in order")
        if type(count) is not int or count < 2:
            raise _Unresolved(f"the count of its factor {to_source(factor)} is below two")
        found = _spaced(Fraction(lower), Fraction(upper), count)
    else:
        if factor.nodes in values:
            listed = values[factor.nodes]
        else:
            listed = _members(sets.defined(T.Named(factor.nodes), _set_definitions(stage)))
            if listed is None:
                raise _Unresolved(
                    f"its factor {to_source(factor)} names {factor.nodes}, which no setting "
                    "values and no set the stage defines lists by its members"
                )
        if not isinstance(listed, (list, tuple)) or not all(_finite_real(v) for v in listed):
            raise _Unresolved(f"the nodes of its factor {to_source(factor)} are not finite reals")
        found = tuple(Fraction(value) for value in listed)
    _check_membership(stage, factor.coordinate, found, declared, calibration)
    return tuple(dict.fromkeys(found))


def _setting_value(part, values):
    """The value of a setting a factor names, unresolved where the settings
    bind none."""
    if isinstance(part, T.Literal):
        return part.value
    if isinstance(part, T.ExpressionArgument):
        if part not in values:
            raise _Unresolved(f"the sum {to_source(part)} needs a supplied continuation field")
        return values[part]
    if part.name not in values:
        raise _Unresolved(f"the setting {part.name} has no value")
    return values[part.name]


def _spaced(lower, upper, count):
    """`count` equally spaced exact nodes from `lower` to `upper`, both
    included, for `lower < upper`; the one node `lower` where the two are
    equal, and none where the interval is empty."""
    if lower > upper:
        return ()
    if lower == upper:
        return (lower,)
    return tuple(lower + (upper - lower) * Fraction(k, count - 1) for k in range(count))


def _check_membership(stage, name, nodes, declared, calibration):
    """Each node of the coordinate `name` lies in its declared set, as the
    set algebra decides or, where it does not, the parameter values
    `calibration`; a membership that is false or not decided is
    unresolved."""
    if declared is None:
        return
    for node in nodes:
        member = point_in_declared_set(stage, _number(node), declared, calibration)
        if member is not True:
            word = "lies outside" if member is False else "is not decidably inside"
            raise _Unresolved(
                f"its node {name} = {_number(node)} {word} the declared set {to_source(declared)}"
                f"{parameters_read_at(stage, declared, calibration)}"
            )


def _points(stage, grid, states, values, calibration):
    """The support of the declared points of `!Points`, each point in the
    declared order of `states`, without repetition; the empty grid where no
    points are named."""
    coordinates = tuple(states)
    if grid.nodes is None:
        return _Constructed(GRID_WORDS[T.PointGrid], coordinates, ())
    if grid.nodes in values:
        rows = _point_rows(values[grid.nodes], len(coordinates))
    else:
        definitions = _set_definitions(stage)
        rows = _defined_points(definitions.get(grid.nodes), definitions)
    if rows is None or any(len(row) != len(coordinates) for row in rows):
        raise _Unresolved(
            f"its points {grid.nodes} have no value of one coordinate for each of "
            f"({', '.join(coordinates)})"
        )
    for row in rows:
        if not all(_finite_real(value) for value in row):
            raise _Unresolved(f"its point {row!r} has a coordinate that is no finite real")
    exact = tuple(tuple(Fraction(value) for value in row) for row in rows)
    for index, (name, declared) in enumerate(states.items()):
        _check_membership(
            stage, name, tuple(point[index] for point in exact), declared, calibration
        )
    return _Constructed(GRID_WORDS[T.PointGrid], coordinates, tuple(dict.fromkeys(exact)))


class _Feasible(NamedTuple):
    """The feasible set of a fibre's control as the sampler reads it: its
    `name`, the names of its `parameters`, the `arguments` at which the stage
    applies it, one term per parameter, and the `bounds` of its interval."""

    name: str
    parameters: tuple
    arguments: tuple
    bounds: object


def _fibred(stage, grid, domain, values, calibration):
    """The joint grid of `!Fibred`: the base constructed on the states of the
    domain other than the fibre's control, and at each base state the
    declared count of equally spaced points of the control's feasible
    interval, both closed finite endpoints included, each paired with the
    state. A fibre of several controls, a coupled restriction, an open or
    unbounded interval and an interval the bound values do not decide are
    unresolved; an empty base gives the empty joint grid."""
    controls = _fibre_controls(grid)
    if len(grid.fibre.factors) != 1:
        raise _Unresolved(
            f"its fibre {to_source(grid.fibre)} names the controls {', '.join(controls)}, and "
            "the construction samples the feasible set of one control; a joint feasible set "
            "needs an identified joint sampler and membership check, so joint sampling is "
            "unsupported"
        )
    (factor,) = grid.fibre.factors
    control = factor.coordinate
    states = {name: held for name, held in domain.states.items() if name not in controls}
    base = _construct_on(stage, grid.base, states, domain, values, calibration)
    count = _setting_value(factor.count, values)
    if type(count) is not int or count < 2:
        raise _Unresolved(f"the count of its fibre {to_source(factor)} is below two")
    feasible = _feasible_interval(stage, factor.set, tuple(states), domain)
    declared = domain.controls.get(control)
    fibres, points = [], []
    for state in base.points:
        lower, upper = _interval_at(feasible, tuple(states), state, calibration)
        nodes = _spaced(lower, upper, count)
        _check_membership(stage, control, nodes, declared, calibration)
        fibres.append((state, nodes))
        points.extend(state + (node,) for node in nodes)
    return _Constructed(
        GRID_WORDS[T.Fibred],
        tuple(states) + (control,),
        tuple(dict.fromkeys(points)),
        base=base,
        fibres=tuple(fibres),
    )


def _feasible_interval(stage, name, states, domain):
    """The `_Feasible` record of the feasible set `name` of a fibre's control,
    read once for every base state: an interval written with its two
    endpoints, both finite and closed, applied by the stage's choices at one
    list of arguments that read the states alone; a set the stage defines
    has no parameters. A correspondence no choice applies is evaluated with
    its parameters read as the states of the same names."""
    _, parameters, body = _feasible_definition(stage, name)
    names = tuple(parameter.stem for parameter in parameters)
    bounds = body.bounds if isinstance(body, T.Interval) else None
    if not isinstance(bounds, T.Range) or bounds.left is None or bounds.right is None:
        raise _Unresolved(
            f"the feasible set {name} is {to_source(body)}, which is no interval written with "
            "its two endpoints; the scalar sampler reads such an interval, and another set "
            "needs an explicitly supplied finite node set or an identified sampler"
        )
    for end, mark, side in (
        (bounds.lower, bounds.left, "lower"),
        (bounds.upper, bounds.right, "upper"),
    ):
        if _infinite(end):
            raise _Unresolved(
                f"the feasible set {name} = {to_source(body)} is unbounded at its {side} end; "
                "the scalar sampler includes admissible finite endpoints, an unbounded interval "
                "needs an explicitly supplied finite node set or an identified sampler, and no "
                "truncation bound is invented"
            )
        if not isinstance(mark, T.Closed):
            raise _Unresolved(
                f"the feasible set {name} = {to_source(body)} is open at its {side} end, which "
                "is then no admissible endpoint; the scalar sampler includes admissible finite "
                "endpoints, an open interval needs an explicitly supplied finite node set or an "
                "identified sampler, and no truncation bound is invented"
            )
    arguments = _feasible_arguments(stage, name, names, states, domain)
    return _Feasible(name, names, arguments, bounds)


def _feasible_definition(stage, name):
    """The declaration, formal parameters and formula of a feasible set."""
    definition = next(
        (
            d
            for d in stage.definitions.values()
            if d.kind in ("correspondence", "set") and d.identity.field == name
        ),
        None,
    )
    if definition is None or not definition.equations:
        raise _Unresolved(f"the feasible set {name} is no correspondence or set the stage defines")
    if definition.kind == "set":
        parameters, body = (), sets.defined(definition.equations[0], _set_definitions(stage))
    else:
        held = definition.equations[0]
        parameters, body = held.params, held.body
    return definition, parameters, body


def _feasible_arguments(stage, name, parameters, states, domain):
    """The authored arguments of a feasible set as applied at the grid."""
    arguments = _applied_arguments(stage, name, len(parameters))
    if arguments is None:
        missing = [parameter for parameter in parameters if parameter not in states]
        if missing:
            raise _Unresolved(
                f"no choice of the stage applies {name}, and its coordinates "
                f"{', '.join(missing)} are no states of the grid's base, so the states at which "
                "it is evaluated are not determined"
            )
        arguments = tuple(T.Sym(T.Constant(parameter)) for parameter in parameters)
    coupled = sorted(
        {
            node.symbol.name
            for argument in arguments
            for node in term_nodes(argument)
            if isinstance(node, T.Sym) and isinstance(node.symbol, T.Constant)
        }
        & set(domain.controls)
    )
    if coupled:
        raise _Unresolved(
            f"the stage applies {name} at the control{'s' if len(coupled) > 1 else ''} "
            f"{', '.join(coupled)}, a restriction coupled with another control; a coupled "
            "restriction needs an identified joint sampler and membership check, so joint "
            "sampling is unsupported"
        )
    return arguments


def _infinite(end):
    """Whether an interval endpoint is infinity or its negation."""
    if isinstance(end, T.Neg):
        return _infinite(end.operand)
    return (
        isinstance(end, T.Sym) and isinstance(end.symbol, T.Constant) and end.symbol.name == "inf"
    )


def _applied_arguments(stage, name, arity):
    """The arguments at which the choices of the stage apply the
    correspondence `name`, `argmax_{c : Γ_c(m)}`, as terms; None where no
    choice applies it, and unresolved where choices apply it at different
    arguments or at another number of them than it declares."""
    found = []
    for block in blocks_in_file_order(stage):
        for _, line in lines_of(stage, block):
            if line.core is None:
                continue
            for node in term_nodes(line.core):
                if (
                    isinstance(node, T.In)
                    and isinstance(node.set, T.Call)
                    and node.set.fun == name
                ):
                    found.append(tuple(node.set.args))
    distinct = tuple(dict.fromkeys(found))
    if not distinct:
        return None
    if len(distinct) > 1 or len(distinct[0]) != arity:
        raise _Unresolved(
            f"the choices of the stage apply {name} at "
            f"{'; '.join(', '.join(to_source(a) for a in arguments) for arguments in distinct)}, "
            f"and {name} declares {arity} coordinate{'' if arity == 1 else 's'}, so the states at "
            "which the fibre samples it are not determined"
        )
    return distinct[0]


def _interval_at(feasible, states, state, calibration):
    """The exact endpoints of a feasible interval at one base state: its
    arguments read at the state's coordinates and the calibration, then its
    endpoints read at those arguments and the calibration, through the one
    arithmetic interpretation of the package (`typing.sets.number_at`)."""
    at = {**calibration, **dict(zip(states, state))}
    bound = {}
    shown = ", ".join(f"{name} = {_number(value)}" for name, value in zip(states, state))
    for parameter, argument in zip(feasible.parameters, feasible.arguments):
        value = sets.number_at(argument, at).value
        if value is None:
            raise _Unresolved(
                f"the argument {to_source(argument)} at which the stage applies {feasible.name} "
                f"is not decided at the state {shown} and the calibration"
            )
        bound[parameter] = value
    reading = {**calibration, **bound}
    ends = tuple(
        sets.number_at(end, reading).value
        for end in (feasible.bounds.lower, feasible.bounds.upper)
    )
    if None in ends:
        raise _Unresolved(
            f"the endpoints of {feasible.name} at the state {shown} are not decided at the "
            "calibration; calibrate the parameters they read"
        )
    return tuple(Fraction(end) for end in ends)


def _number(value):
    """An exact number as a Python number: an `int` where it is an integer
    and the nearest `float` otherwise."""
    value = Fraction(value)
    return int(value) if value.denominator == 1 else float(value)


# --- the requirements of a constructed grid ---


def _requirement_failure(grid, constructed):
    """The clause that says which requirement of a constructed grid fails,
    None where all hold: the base's own requirements on the base of
    `!Fibred`, the requirements inside its fibre on each fibre, and the
    outer requirements on the whole grid, the joint grid of `!Fibred`."""
    if isinstance(grid, T.Fibred):
        failure = _requirement_failure(grid.base, constructed.base)
        if failure is not None:
            return f"its base {to_source(grid.base)}: {failure}"
        control = constructed.coordinates[-1]
        states = constructed.base.coordinates
        for state, nodes in constructed.fibres:
            for word in grid.fibre.require:
                reason = _failure(word, (control,), tuple((node,) for node in nodes))
                if reason is not None:
                    shown = ", ".join(
                        f"{name} = {_number(value)}" for name, value in zip(states, state)
                    )
                    return (
                        f"its fibre at the base state {shown} does not satisfy !{word}, the "
                        f"requirement inside the fibre: {reason}"
                    )
    for word in grid.require:
        reason = _failure(word, constructed.coordinates, constructed.points)
        if reason is not None:
            return f"the grid does not satisfy !{word}: {reason}"
    return None


def _failure(word, coordinates, points):
    """The clause that says why a finite grid of exact points on the named
    `coordinates` does not satisfy the predicate word `word`, None where it
    does."""
    return _PREDICATE_CHECKS[word](coordinates, points)


def _empty_failure(coordinates, points):
    if not points:
        return None
    plural = "" if len(points) == 1 else "s"
    return f"it holds {len(points)} point{plural}, the first {_shown(points[0])}"


def _cartesian_failure(coordinates, points):
    if not points:
        return "it holds no point"
    missing = _missing_combination(coordinates, points)
    if missing is None:
        return None
    return (
        f"the product of its projections, {_hull(coordinates, points)}, holds "
        f"{_shown(missing)}, which the grid does not hold"
    )


def _noncartesian_failure(coordinates, points):
    if not points:
        return "it holds no point"
    if _missing_combination(coordinates, points) is None:
        return "it holds every combination of its projected coordinate values"
    return None


def _uniform_failure(coordinates, points):
    failure = _cartesian_failure(coordinates, points)
    if failure is not None:
        return failure
    if not coordinates:
        return "it has no coordinate"
    for index, name in enumerate(coordinates):
        values = sorted({point[index] for point in points})
        if len(values) < 2:
            return f"its coordinate {name} takes the one value {_number(values[0])}"
        if len({right - left for left, right in zip(values, values[1:])}) > 1:
            return (
                f"the values of its coordinate {name}, {_listed(values)}, are not equally spaced"
            )
    return None


# The checker of each predicate word: the clause that says why a grid does
# not satisfy it, None where it does. A word of `PREDICATES` with no checker
# is refused as a fault of the package (`_check_requirement_words`).
_PREDICATE_CHECKS = {
    "Empty": _empty_failure,
    "Cartesian": _cartesian_failure,
    "NonCartesian": _noncartesian_failure,
    "UniformCartesian": _uniform_failure,
}

# One grid of each class into which the predicate words divide the grids on a
# fixed product: the empty grid, a uniform Cartesian grid and a non-Cartesian
# grid. Two words contradict each other where no witness satisfies both:
# Empty, Cartesian and NonCartesian hold of disjoint grids, and every
# UniformCartesian grid is Cartesian.
_WITNESSES = (
    (("x",), ()),
    (("x",), ((Fraction(0),), (Fraction(1),))),
    (("x", "y"), ((Fraction(0), Fraction(0)), (Fraction(1), Fraction(1)))),
)


def _contradiction(words):
    """The first two of `words` that no grid satisfies together, or the empty
    tuple."""
    for first, second in itertools.combinations(dict.fromkeys(words), 2):
        if not any(
            _failure(first, *witness) is None and _failure(second, *witness) is None
            for witness in _WITNESSES
        ):
            return (first, second)
    return ()


def _missing_combination(coordinates, points):
    """A combination of the projected coordinate values that a nonempty grid
    does not hold, None where it holds every one, the grid being Cartesian."""
    projections = [sorted({point[index] for point in points}) for index in range(len(coordinates))]
    if len(points) == math.prod(len(values) for values in projections):
        return None
    held = set(points)
    return next(
        combination for combination in itertools.product(*projections) if combination not in held
    )


def _hull(coordinates, points):
    """The product of a grid's projections as a sentence writes it,
    `{1, 2} × {0, 1, 2}`."""
    return " × ".join(
        _listed(sorted({point[index] for point in points}), braces=True)
        for index in range(len(coordinates))
    )


def _listed(values, braces=False):
    """Exact values as a sentence lists them, the middle of a long list
    elided."""
    shown = [str(_number(value)) for value in values]
    if len(shown) > 6:
        shown = shown[:3] + ["…"] + shown[-1:]
    text = ", ".join(shown)
    return "{" + text + "}" if braces else "(" + text + ")"


def _shown(point):
    """An exact point as a sentence writes it, `(1, 2)`."""
    return "(" + ", ".join(str(_number(value)) for value in point) + ")"


# --- the realized grids of a builder ---


class RealizedGrid(NamedTuple):
    """The numerical construction of one place's grid at the bound settings
    and calibration (build contract §2): `word`, the source word of its outer
    constructor without the `!`; `coordinates`, the names of its coordinates
    in the domain's declared order, for `!Fibred` the states and then the
    control; and `points`, its finite support exactly as constructed, one
    tuple of `fractions.Fraction` per point, in construction order with
    repeated points removed. The construction keeps these exact points
    whatever their floating-point values are, so that two distinct points
    remain distinct; the conversion of the points to floating-point numbers
    belongs to numerical preparation, which refuses a conversion that makes
    two distinct points one (build contract §4). The record prints each
    coordinate as an `int` where it is an integer and as its nearest `float`
    otherwise. It holds strings, tuples and numbers, and refers to no
    stage."""

    word: str
    coordinates: tuple
    points: tuple

    def __str__(self):
        count = len(self.points)
        points = self.points if count <= 6 else self.points[:3] + self.points[-1:]
        shown = [str(tuple(_number(value) for value in point)) for point in points]
        if count > 6:
            shown.insert(3, "…")
        listed = f": {', '.join(shown)}" if count else ""
        return (
            f"!{self.word} on ({', '.join(self.coordinates)}), {count} "
            f"point{'' if count == 1 else 's'}{listed}"
        )

    __repr__ = __str__


class SpacedGridFactor(NamedTuple):
    """Bound arguments of a spacing word applied by a handler."""

    coordinate: str
    domain: object
    lower: Fraction
    upper: Fraction
    count: int
    spacing: str
    options: tuple
    requirements: tuple


class FeasibleGridFactor(NamedTuple):
    """The control's feasible interval at the grid's state coordinates."""

    coordinate: str
    domain: object
    count: int
    correspondence: Identity
    coordinates: tuple
    arguments: tuple
    argument_sets: tuple
    interval: T.Interval
    requirements: tuple


def _bound_grid_term(term, values):
    """A numerical term with its known finite subexpressions evaluated."""
    bound = {}
    for node in term_nodes(term):
        if not isinstance(node, T.expr):
            continue
        value = sets.number_at(node, values).value
        if value is not None:
            bound[node] = T.Number(_exact(value))
    return substituted(term, bound)


def _grid_interval_bounds(interval, values):
    """Endpoints and inclusion of an interval, when they are decided."""
    bounds = interval.bounds if isinstance(interval, T.Interval) else None
    if not isinstance(bounds, T.Range) or bounds.left is None or bounds.right is None:
        return None

    def endpoint(term):
        if _infinite(term):
            return -math.inf if isinstance(term, T.Neg) else math.inf
        return sets.number_at(term, values).value

    lower, upper = endpoint(bounds.lower), endpoint(bounds.upper)
    if lower is None or upper is None:
        return None
    return sets.Bounds(
        lower, isinstance(bounds.left, T.Closed), upper, isinstance(bounds.right, T.Closed)
    )


def _grid_member(value, domain):
    """Decidable membership in a detached scalar grid domain."""
    primitive = sets.primitive_of(domain)
    if primitive is not None:
        if primitive.kind == EXTENDED_REAL:
            return True
        if primitive.kind == INTEGER:
            if value.denominator != 1:
                return False
            if primitive.glyph == "ℕ":
                return None if value == 0 else value > 0
            return True
    bounds = (
        sets.endpoints(domain) if primitive is not None and primitive.kind == REAL
        else _grid_interval_bounds(domain, {})
    )
    if bounds is not None:
        return _inside_bounds(value, bounds)
    members = sets.finite_members(domain, {}, {})
    if members is not None and not isinstance(domain, T.FiniteSet):
        return value in members
    return None


def _inside_bounds(point, bounds):
    lower = point >= bounds.lower if bounds.lower_closed else point > bounds.lower
    upper = point <= bounds.upper if bounds.upper_closed else point < bounds.upper
    return lower and upper


def _require_grid_member(value, domain, name):
    member = _grid_member(value, domain)
    if member is not True:
        relation = "lies outside" if member is False else "is not decidably inside"
        raise ValueError(f"{name} = {value} {relation} the declared set {to_source(domain)}")


def feasible_interval(factor, at):
    """The exact feasible bounds at a handler's state point."""
    values = {}
    for name, domain in factor.coordinates:
        if name not in at:
            raise ValueError(f"the feasible grid requires the coordinate {name}")
        value = _exact(at[name])
        _require_grid_member(value, domain, name)
        values[name] = value
    for argument, domain in zip(factor.arguments, factor.argument_sets, strict=True):
        value = sets.number_at(argument, values).value
        if value is None:
            raise ValueError(f"the feasible argument {to_source(argument)} is not decided")
        _require_grid_member(_exact(value), domain, to_source(argument))
    bounds = _grid_interval_bounds(factor.interval, values)
    if bounds is None or not all(
        sets.is_number(end) for end in (bounds.lower, bounds.upper)
    ):
        raise ValueError(
            f"the feasible interval {to_source(factor.interval)} has no finite bounds"
        )
    if bounds.lower > bounds.upper or (
        bounds.lower == bounds.upper and not (bounds.lower_closed and bounds.upper_closed)
    ):
        raise ValueError(f"the feasible interval {to_source(factor.interval)} is empty")
    return bounds


def check_grid_factor_points(factor, points, *, at=None):
    """A finite grid after checking its shape, domains and requirements."""
    values = tuple(_exact(point) for point in points)
    if len(values) != factor.count:
        raise ValueError(f"the grid on {factor.coordinate} requires count {factor.count}")
    if any(left >= right for left, right in zip(values, values[1:])):
        raise ValueError(f"the points on {factor.coordinate} must be strictly increasing")
    if isinstance(factor, SpacedGridFactor):
        bounds = sets.Bounds(factor.lower, True, factor.upper, True)
        rejected = "lies outside the spacing bounds"
    elif isinstance(factor, FeasibleGridFactor):
        bounds = feasible_interval(factor, {} if at is None else at)
        rejected = "is outside the feasible interval"
    else:
        raise TypeError(f"unsupported handler grid factor {type(factor).__name__}")
    for value in values:
        if not _inside_bounds(value, bounds):
            raise ValueError(f"{factor.coordinate} = {value} {rejected}")
        _require_grid_member(value, factor.domain, factor.coordinate)
    coordinates = (factor.coordinate,)
    rows = tuple((point,) for point in values)
    for word in factor.requirements:
        failure = _failure(word, coordinates, rows)
        if failure is not None:
            raise ValueError(f"the grid does not satisfy !{word}: {failure}")
    return RealizedGrid("Cartesian", coordinates, rows)


def _spacing_options(word, values):
    """The bound values of a spacing word's ordered keywords."""
    def bound(argument):
        if isinstance(argument, T.Name):
            return freeze(_setting_value(argument, values))
        if isinstance(argument, T.Quoted):
            return argument.text
        if isinstance(argument, T.Values):
            return tuple(bound(item) for item in argument.items)
        if isinstance(argument, T.Nested):
            return (argument.word.name, _spacing_options(argument.word, values))
        return _setting_value(argument, values)

    return tuple((keyword.key, bound(keyword.value)) for keyword in word.arguments)


def _handler_grid_factor(stage, place, grid, domain, values, calibration, constants):
    """The detached data a handler needs to place grid points."""
    if not isinstance(grid, T.Cartesian) or len(grid.factors) != 1:
        return None
    (factor,) = grid.factors
    if not isinstance(factor, T.Feasible) and (
        not isinstance(factor, T.Spaced) or factor.spacing is None
    ):
        return None
    definitions = _set_definitions(stage)

    def declared(term):
        resolved = _bound_grid_term(sets.resolved(term, definitions), calibration)
        primitive = sets.primitive_of(resolved)
        if _grid_interval_bounds(resolved, {}) is not None or (
            primitive is not None and primitive.kind in (REAL, INTEGER, EXTENDED_REAL)
        ) or isinstance(resolved, (T.IntegerRange, T.Points)) and (
            sets.finite_members(resolved, {}, {}) is not None
        ):
            return resolved
        raise _Unresolved("the handler factor's declared set is not a decided scalar set")

    if isinstance(factor, T.Spaced) and factor.spacing is not None:
        if tuple(domain.states) != (factor.coordinate,):
            return None
        lower, upper, count = (
            _setting_value(part, values) for part in (factor.lower, factor.upper, factor.count)
        )
        if not (sets.is_number(lower) and sets.is_number(upper) and lower < upper):
            raise _Unresolved(f"the bounds of its factor {to_source(factor)} are not in order")
        if type(count) is not int or count < 2:
            raise _Unresolved(f"the count of its factor {to_source(factor)} is below two")
        held = declared(domain.states[factor.coordinate])
        for endpoint in (lower, upper):
            try:
                _require_grid_member(_exact(endpoint), held, factor.coordinate)
            except ValueError as error:
                raise _Unresolved(str(error)) from None
        return SpacedGridFactor(
            factor.coordinate, held, _exact(lower), _exact(upper), count,
            factor.spacing.name, _spacing_options(factor.spacing, values), grid.require,
        )

    count = _setting_value(factor.count, values)
    if type(count) is not int or count < 2:
        raise _Unresolved(f"the count of its factor {to_source(factor)} is below two")
    definition, parameters, body = _feasible_definition(stage, factor.set)
    if not isinstance(body, T.Interval) or not isinstance(body.bounds, T.Range):
        raise _Unresolved(f"the feasible set {factor.set} is not a scalar interval")
    if body.bounds.left is None or body.bounds.right is None:
        raise _Unresolved(f"the feasible interval {factor.set} does not specify both endpoints")
    if _infinite(body.bounds.lower) or _infinite(body.bounds.upper):
        raise _Unresolved(f"the feasible interval {factor.set} has an infinite endpoint")
    names = tuple(parameter.stem for parameter in parameters)
    ctx = StageNames(stage)
    supplied = {} if constants is None else constants

    def at_stage(term, local=()):
        replacements = {}
        for name, side in symbol_occurrences(term):
            if name in local or name in domain.states or name == "inf":
                continue
            identity = ctx.resolve(name, place.block, side)
            if identity in supplied:
                value = _checking_value(supplied[identity])
            else:
                value = calibration.get(name) if side is None else None
            if not sets.is_number(value):
                raise _Unresolved(
                    f"the feasible interval {factor.set} needs a numerical value for {name}"
                )
            replacements[term_of_name(name, side)] = T.Number(_exact(value))
        return _bound_grid_term(substituted(term, replacements), {})

    arguments = tuple(
        at_stage(term) for term in _feasible_arguments(
            stage, factor.set, names, tuple(domain.states), domain
        )
    )
    interval = substituted(
        at_stage(body, names),
        {term_of_name(name, None): argument for name, argument in zip(names, arguments)},
    )
    terms = (*arguments, interval.bounds.lower, interval.bounds.upper)
    reads = tuple(sets.parameters_read(term) for term in terms)
    if any(names is None for names in reads):
        raise _Unresolved(f"the feasible interval {factor.set} needs unsupported arithmetic")
    read = {name for names in reads for name in names}
    if read - set(domain.states):
        raise _Unresolved(f"the feasible interval {factor.set} reads an unresolved coordinate")
    coordinates = tuple(
        (name, declared(domain.states[name])) for name in domain.states if name in read
    )
    argument_sets = tuple(
        declared(next(
            (item.space for item in parameter.classifiers if isinstance(item, T.Domain)), None
        ))
        for parameter in parameters
    )
    return FeasibleGridFactor(
        factor.coordinate, declared(domain.controls[factor.coordinate]), count,
        definition.identity, coordinates, arguments, argument_sets, interval, grid.require,
    )


def _grid_records(stage, place, held, row, record, values, calibration, *, constants=None):
    """A place's realized grid or refusal, and its detached handler inputs."""
    file, line, column = entry_position(record.address)
    factor = None
    try:
        domains = [grid_domain(stage, box, place.block, row) for box in place.boxes]
        if any(tuple(domain.states) != tuple(domains[0].states) for domain in domains[1:]):
            raise _Unresolved("the place holds functions of different coordinates")
        supplied = dict(values)
        for part in term_nodes(held.grid):
            if not isinstance(part, T.ExpressionArgument):
                continue
            operands = grid_sum_operands(stage, place, part)
            if operands is None:
                raise _Unresolved(f"the sum {to_source(part)} has no scalar field and setting")
            field, identity, setting = operands
            if constants is None or identity not in constants:
                raise _Unresolved(
                    f"the sum {to_source(part)} requires the continuation field {field}"
                )
            value, offset = _checking_value(constants[identity]), values[setting]
            if not (sets.is_number(value) and sets.is_number(offset)):
                raise _Unresolved(
                    f"the sum {to_source(part)} needs finite numbers, and has "
                    f"{field} = {value!r} and {setting} = {offset!r}"
                )
            total = Fraction(value) + Fraction(offset)
            supplied[part] = int(total) if total.denominator == 1 else total
        factor = _handler_grid_factor(
            stage, place, held.grid, domains[0], supplied, calibration, constants
        )
        constructed = _construct(stage, held.grid, domains[0], supplied, calibration)
        failure = _requirement_failure(held.grid, constructed)
    except _Unresolved as unresolved:
        failure = (
            f"{unresolved}; numerical construction establishes the finite points of a grid and "
            "every property it requires before the grid is used, and supplies no default"
        )
        constructed = None
    if failure is not None:
        return Refusal(
            reason=(
                f"stage {stage.name!r}, place {place.address!r}, grid {to_source(held.grid)}: "
                f"{failure}"
            ),
            diagnostic={
                "stage": stage.name,
                "address": place.address,
                "rule": "grid-requirement",
                "file": file if line is not None else stage.provenance.get("origin"),
                "line": line,
                "column": column,
            },
        ), factor
    return RealizedGrid(constructed.word, constructed.coordinates, constructed.points), factor


def grid_records(stage, builder, *, constants=None):
    """Read-only mappings of grid results and handler inputs by place.

    Only places of the builder or sub-builder are included. Without bound
    settings both mappings are None.
    """
    if stage.bindings.settings is None:
        return None, None
    values = dict(stage.bindings.settings)
    calibration = calibration_values(stage)
    entries = {
        typing.place.address: typing
        for typing in typings(stage)
        if typing.component == "grid" and _within(typing.place, builder)
    }
    found, factors = {}, {}
    for address, held in components_by_place(stage).items():
        typing = entries.get(address)
        if typing is None:
            continue
        row = bound_row(stage, held.method.name) if held.method is not None else None
        found[address], factor = _grid_records(
            stage, typing.place, held, row, typing.record, values, calibration, constants=constants
        )
        if factor is not None:
            factors[address] = factor
    return MappingProxyType(found), MappingProxyType(factors)


def _within(place, builder):
    """Whether a place lies within the builder or the sub-builder named
    `builder`: every place of the block for a builder, and the node's own
    place and the places under its address for a sub-builder."""
    if place.block is None:
        return False
    if builder == place.block:
        return True
    address = place.address
    return (
        address == builder
        or address.startswith(builder + ".")
        or address.startswith(builder + "[")
    )


# --- the equality of two grids ---


def same_grid(first, second):
    """Whether two realized grids hold the same finite support, compared
    exactly in a common valid context (build contract §2): each is a
    `RealizedGrid`, whose construction established it, and the two have the
    same named coordinates in the same order. The exact points of the two
    supports are compared by `representations.supports_equal`, the one exact
    comparison of finite supports, so that signed zeros are equal, distinct
    large integers remain distinct, a constructed node is never replaced by
    its nearest floating-point number and no tolerance applies; the
    constructions and the orders of their points are not compared."""
    for grid in (first, second):
        if isinstance(grid, Refusal):
            raise ValueError(
                "a grid whose construction is refused is valid in no context, and equality is "
                f"defined between valid grids: {grid.reason}"
            )
        if not isinstance(grid, RealizedGrid):
            raise TypeError(f"same_grid compares realized grids; got {type(grid).__name__}")
    if tuple(first.coordinates) != tuple(second.coordinates):
        raise ValueError(
            f"the grids lie on ({', '.join(first.coordinates)}) and on "
            f"({', '.join(second.coordinates)}); equality is defined in a common valid "
            "context, on the same named coordinates in the same order"
        )
    return supports_equal(first.points, second.points)
