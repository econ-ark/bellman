"""The catalogue of the methods: one row per method word, the one place a
method is named (AMD-SG-005 §4; AMD-SG-006 §4; specification 0.7 §5). The
page `docs/Bellman-Sym/reference/methods.md` is printed from `METHOD_TYPES`,
one row for each method word.

A row states the kinds of place the word admits (`admits`, the admission of
specification 0.7 §5); the keyword arguments the package reads (`keywords`),
each a `MethodOption` with the domain of its value and whether the word
requires it, a keyword written `n_<shock>` standing for one keyword per
shock the expectation at the place integrates; the perch on whose states the
word's grid lies where it reads one (`grid`); whether the word is a solution
method whose lines open a builder (`takes_block`, the two levels of D8); the
condition its construction requires, which `stage.obligations()` lists; the
derivatives a representation evaluates; and the kind of the word, a solution
method or a representation. A method word takes keyword arguments and no
positional ones (D1): `!vfi(tol=tol_v, n_c=n_c)`, `!gauss_hermite(n_ψ=n_ψ_nodes)`.
A keyword the row does not list is admitted and kept for the handler that
realizes the word, which reads it or refuses it. A method is written as the
typing of an operator's method component at its place, `policy.method : !egm`,
and stands where it is written: the reading of the entries is
`stage/places.py`, their checks against the rows are `stage/components.py`,
and no row places a word. A hyphenated word keeps its tag, `gauss-hermite`,
and is written in a stage file with an underscore, `!gauss_hermite`, which
`row_of` reads as the same word; no other alias exists.

The grid of an operator is a classifier component of its signature beside the
method, the discretized domain, written by its own typing entry in the one
kind built, `!Cartesian(a=(a_min, a_max, n_a))` (D5): one factor per
coordinate of the function the place holds, keyed by the coordinate's name,
in one of four shapes, a spaced factor of a lower bound, an upper bound and a
count with an optional spacing word, a listed node set, a quadrature factor
naming the expectation operator whose nodes the coordinate takes, and a
feasible factor naming a control's feasible set with a count. The sparse
kind `!Smolyak` is reserved by name and not built. Where a place writes no
grid, and for a coordinate no factor names (decision S7-C17), the default is
the product over the states of the function's domain, on the perch the
word's row names: the output perch of the place, and the continuation perch
for `!egm`, whose exogenous grid lies on the input perch of the policy
builder.
"""

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType

from bellman.display.cards import method_card
from bellman.native.records import MethodOption
from bellman.syntax.vocabulary import CONTINUATION

# --- the rows read by their words ---


def row_of(word):
    """The row of the catalogue for a method word as written, without its
    `!`: the row of that tag, or of the tag with each underscore read as a
    hyphen, `gauss-hermite` for `gauss_hermite` (D1); None where no row
    holds it, and for None."""
    if not isinstance(word, str):
        return None
    return METHOD_TYPES.get(word) or METHOD_TYPES.get(word.replace("_", "-"))


def is_solution_method(word):
    """Whether a method word names a solution method, one whose row admits a
    builder and makes a solution binding: with such a word in a block's
    method component, the lines an addition appends to the block are the
    method's rows at the operative level (specification 0.7 D8)."""
    row = row_of(word)
    return row is not None and row.kind == "solution" and "builder" in row.admits


# --- the method table, its parts first ---


@dataclasses.dataclass(frozen=True)
class _MethodType(Mapping):
    """One row of the method table, the catalogue entry of one method word.

    The mapping exposes the two public parts of AMD-SG-025, `admits`, the
    kinds of place the word stands at, and `keywords`, the keyword arguments
    the package reads, each a `MethodOption` with the domain of its value and
    whether the word requires it (specification 0.7, D1). A keyword written
    `n_<shock>` stands for one keyword per shock the expectation at the place
    integrates.
    """

    admits: tuple
    keywords: Mapping
    _tag: str
    # the columns of specification 0.6 decision 2 as AMD-MB-001 §5.2 amends
    # them, read as attributes and not among the two parts of the mapping:
    # whether the method takes a block, the name of the condition its
    # construction requires, which `stage.obligations()` lists, and the
    # derivatives a representation evaluates, by order, with the sentence
    # that says what they are; what a method reads is read from the rows
    # of the block it binds (`stage_answers.derivative_reads`)
    takes_block: bool = False
    condition: str | None = None
    derivatives: tuple = ()
    evaluates: str | None = None
    # the kind of binding the method makes, of which a place holds one
    # (decision SD-15): `solution` or `representation`
    kind: str = "solution"
    # the perch on whose states the word's grid lies, where it reads one
    # (specification 0.7, D5): `output`, the perch at which the function the
    # place holds stands, or the continuation perch, the input perch of the
    # policy builder, on which the exogenous grid of `!egm` lies; None for a
    # word that reads no grid
    grid: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "admits", tuple(self.admits))
        object.__setattr__(self, "keywords", MappingProxyType(dict(self.keywords)))

    def __getitem__(self, key):
        if key not in ("admits", "keywords"):
            raise KeyError(key)
        return getattr(self, key)

    def __iter__(self):
        return iter(("admits", "keywords"))

    def __len__(self):
        return 2

    def __hash__(self):
        return hash(
            (
                self.admits,
                frozenset(self.keywords.items()),
                self._tag,
                self.takes_block,
                self.condition,
                self.derivatives,
                self.evaluates,
                self.kind,
                self.grid,
            )
        )

    def __str__(self):
        return method_card(self)

    __repr__ = __str__


def _method_type(
    tag,
    admits,
    keywords=None,
    *,
    block=False,
    condition=None,
    kind="solution",
    derivatives=(),
    evaluates=None,
    grid=None,
):
    """One named row of the method table, `(tag, _MethodType)`, the tag
    written once, with the columns of specification 0.6 decision 2 as
    AMD-MB-001 §5.2 amends them: whether the method's lines open a builder,
    the condition its construction requires, and for a representation the
    derivatives it evaluates, by order, with the sentence that says what
    they are; the kind of the word, a `solution` method or a
    `representation` (decision SD-15); and the perch on whose states its
    grid lies, where it reads one."""
    return tag, _MethodType(
        admits=admits,
        keywords=keywords or {},
        _tag=tag,
        takes_block=block,
        condition=condition,
        kind=kind,
        derivatives=tuple(derivatives),
        evaluates=evaluates,
        grid=grid,
    )


# the one kind of grid built, a product of one node set per coordinate, and
# the kind reserved by name for a later specification, a sparse grid with
# its own interpolant (specification 0.7, D5; the grid note §3)
GRID_KIND = "Cartesian"
RESERVED_GRID_KIND = "Smolyak"

# the perch word of a row's `grid` for a grid on the states of the perch at
# which the function the place holds stands
OUTPUT_PERCH = "output"

# the keywords of a word that reads one positive integer per shock the
# expectation at its place integrates, `n_ψ=n_ψ_nodes` (D1, F4)
_NODES_PER_SHOCK = {"n_<shock>": MethodOption("positive integer", required=True)}


# the places a representation is typed at: the Evaluation of a builder or of
# a `!node` line and each object it stores, an authored `evaluate` occurrence,
# a `!node` line, a line and a declared function; not a builder (AMD-MB-002)
_REPRESENTATION_ADMITS = (
    "node",
    "statement",
    "definition",
    ("operator", "evaluate"),
)


# Operator entries include the retained head. Each call names its method once
# and carries both public parts in the same authoritative row.
METHOD_TYPES = dict(
    (
        # the endogenous grid method reads its exogenous grid of savings on
        # the states of the continuation perch (AMD-MB-003 §1; D5)
        _method_type(
            "egm",
            ("builder", ("operator", "argmax")),
            block=True,
            condition="egm-eligibility",
            grid=CONTINUATION,
        ),
        # value function iteration on the backward decision builder, its
        # grid on the states of the decision perch and, where written, a
        # feasible factor for the control it searches over; `n_c`, the
        # number of candidate levels of the search, named as the
        # applications' settings name it
        _method_type(
            "vfi",
            ("builder",),
            keywords={
                "tol": MethodOption("positive real"),
                "n_c": MethodOption("positive integer"),
            },
            grid=OUTPUT_PERCH,
        ),
        # time iteration solves the first-order condition a method's lines
        # write, which read the continuation value's derivative, on the grid
        # of the decision states (resolution SA-12 of 22 October 2026;
        # AMD-MB-001 §4.2; F40)
        _method_type(
            "time-iteration",
            ("builder", "node", ("operator", "solve")),
            block=True,
            grid=OUTPUT_PERCH,
        ),
        # a representation names its basis as the method and its grid by the
        # place's grid component, on the coordinates of the function it
        # stores (D5); the derivatives it evaluates, by order, are
        # information for the stage that reads them and checked by nothing
        # (AMD-MB-001 §5.2, D6); what it does outside the grid, such as
        # extrapolation, is a keyword its handler reads
        _method_type(
            "Linear",
            _REPRESENTATION_ADMITS,
            kind="representation",
            derivatives=(1,),
            evaluates=(
                "the first derivative, piecewise constant between its nodes and so a step "
                "function, which an inverse Euler step that reads it turns into a step "
                "candidate; the second derivative is zero and is not offered"
            ),
            grid=OUTPUT_PERCH,
        ),
        _method_type(
            "pchip",
            _REPRESENTATION_ADMITS,
            kind="representation",
            derivatives=(1, 2),
            evaluates="the first and second derivatives its basis admits",
            grid=OUTPUT_PERCH,
        ),
        _method_type("gauss-hermite", (("operator", "E"),), keywords=_NODES_PER_SHOCK),
        _method_type("quadrature", (("operator", "E"),)),
        _method_type("exact", (("operator", "E"),)),
        _method_type("exact-markov", (("operator", "E"),)),
        _method_type("markov", (("operator", "E"),)),
        _method_type("markov-expectation", (("operator", "E"),)),
        _method_type("sum", (("operator", "E"),)),
        _method_type(
            "tauchen",
            (("operator", "E"),),
            keywords={
                "n_states": MethodOption("positive integer"),
                "n_income_states": MethodOption("positive integer"),
                "n_std": MethodOption("positive real"),
                "min_prob": MethodOption("positive real"),
            },
        ),
        # the methods of a forward builder represent its measure
        # (decision SD-15); a histogram keeps it on a grid of the states of
        # the builder's output perch
        _method_type("deterministic", ("builder",), kind="representation"),
        _method_type("histogram", ("builder",), kind="representation", grid=OUTPUT_PERCH),
        _method_type("identity", ("builder",), kind="representation"),
        _method_type(
            "monte-carlo",
            ("builder", ("operator", "E")),
            keywords={
                "n_paths": MethodOption("positive integer", required=True),
                "seed": MethodOption("seed"),
            },
        ),
        _method_type("max", ("builder", ("operator", "argmax"))),
        _method_type("discrete-choice", ("builder", ("operator", "argmax"))),
        _method_type(
            "golden_section",
            (("operator", "argmax"),),
            keywords={"n_sections": MethodOption("positive integer")},
        ),
        _method_type("scipy-bounded", (("operator", "argmax"),)),
        # a root finder on a grid of the states of the perch at which the
        # policy it computes stands
        _method_type(
            "root-find",
            (("operator", "solve"), ("operator", "argmax")),
            grid=OUTPUT_PERCH,
        ),
        _method_type("newton", (("operator", "solve"),)),
        _method_type("analytic-inverse", ("node", "definition", ("operator", "solve"))),
        _method_type("FUES", ("node", ("operator", "upper_env"))),
    )
)


class _MethodTypes(Mapping):
    """The one method table, `METHOD_TYPES`, as a read-only mapping, each
    row read by its tag with its `!`, `method_types["!egm"]`, or by the
    underscore spelling of a hyphenated tag."""

    def __getitem__(self, tag):
        if not isinstance(tag, str) or not tag.startswith("!"):
            raise KeyError(tag)
        row = row_of(tag[1:])
        if row is None:
            raise KeyError(tag)
        return row

    def __iter__(self):
        return (f"!{name}" for name in METHOD_TYPES)

    def __len__(self):
        return len(METHOD_TYPES)

    def __str__(self):
        return "\n".join(self)

    __repr__ = __str__


method_types = _MethodTypes()
