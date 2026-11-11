"""The rows of the method table that name no representation family, one
row per method word, with the record of a row, the row of a representation
family and the domains of a keyword's value (AMD-SG-005 §4; AMD-SG-006 §4;
specification 0.7 §5; AMD-MT-003 build contract §§3, 7). The table itself,
`METHOD_TYPES` of `stage/method_table.py`, reads these rows with one row for
each family of the representation registry between them.

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
positional ones (D1): `!vfi(tol=tol_v, n_c=n_c)`,
`!gauss_hermite(n_ψ=n_ψ_nodes)`. A keyword the row does not list is admitted
and kept for the handler that realizes the word, which reads it or refuses
it; the kind of a keyword's value is one of `KEYWORD_DOMAINS`, which configure
checks. A method is written as the typing of an operator's method component
at its place, `policy.method : !egm`, and stands where it is written: the
reading of the entries is `stage/places.py`, their checks against the rows
are `stage/components.py`, and no row places a word.

The grid of an operator is a classifier component of its signature beside the
method, the discretized domain, written by its own typing entry as one outer
grid word (D5; AMD-MT-003 build contract §2): `!Cartesian(a=(a_min, a_max,
n_a))`, at most one factor per coordinate of the function the place holds,
keyed by the coordinate's name, in one of four shapes, a spaced factor of a
lower bound, an upper bound and a count with an optional spacing word, a listed
node set, a quadrature factor naming the expectation operator whose nodes the
coordinate takes, and a feasible factor naming a control's feasible set with
a count; `!Points(nodes=P)`, the finite support of declared points; and
`!Fibred(base=…, fibre=…)`, each base state paired with its feasible
controls. The records of the three grid constructors, their arguments and
their checks stand in `stage/grids.py`. Where a place writes no grid, and for
a coordinate no factor names (decision S7-C17), the default is the product
over the states of the function's domain, on the perch the word's row names:
the output perch of the place, and the continuation perch for `!egm`, whose
exogenous grid lies on the input perch of the policy builder.

Each row may carry `text`, the `EntryText` of `native/records.py` that its
generated reference entry prints: the one-sentence meaning, the
compatibility, a small example with its meaning, the identified numerical
implementation and the links (AMD-MT-003 build contract §7). The text stands
beside the row and nowhere else.

These rows stand below the registry of the representation families,
`stage/representations.py`, which reads them where `register` refuses a
family's word that names one of them and where `bound_row` answers the row
a version reads for a word that names no family; the table that joins the
rows and the registry, `stage/method_table.py`, stands above both.
"""

import dataclasses
import math
from collections.abc import Mapping
from types import MappingProxyType

from bellman.display.cards import method_card
from bellman.native.records import EntryText, MethodOption, TypeParameter
from bellman.syntax.vocabulary import CONTINUATION

# --- the record of a row ---


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
    # the explanation the word's generated reference entry prints, an
    # `EntryText`, or None for a row that carries none (AMD-MT-003 build
    # contract §7)
    text: EntryText | None = None

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
                self.text,
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
    text=None,
):
    """One named row of the method table, `(tag, _MethodType)`, the tag
    written once, with the columns of specification 0.6 decision 2 as
    AMD-MB-001 §5.2 amends them: whether the method's lines open a builder,
    the condition its construction requires, and for a representation the
    derivatives it evaluates, by order, with the sentence that says what
    they are; the kind of the word, a `solution` method or a
    `representation` (decision SD-15); the perch on whose states its grid
    lies, where it reads one; and the `EntryText` its reference entry
    prints."""
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
        text=text,
    )


# the perch word of a row's `grid` for a grid on the states of the perch at
# which the function the place holds stands
OUTPUT_PERCH = "output"

# the keywords of a word that reads one positive integer per shock the
# expectation at its place integrates, `n_ψ=n_ψ_nodes` (D1, F4)
_NODES_PER_SHOCK = {
    "n_<shock>": MethodOption(
        "positive integer",
        required=True,
        description=(
            "The number of quadrature nodes for the shock named after `n_`, one keyword for each "
            "shock the expectation at the place integrates."
        ),
    )
}

# the formal definitions an entry links: the method as a type over the kind
# of operator, the two levels a solution method's lines open, and the grid as
# the discretized domain (docs/bellman-calculus/06-Methods.md)
_METHOD_TYPE = "bellman-calculus/06-Methods.md#4-the-method-as-a-type-over-the-kind-of-operator"
_TWO_LEVELS = "bellman-calculus/06-Methods.md#9-the-two-levels-of-a-stage"
_THE_GRID = "bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain"

# the type parameters the attachment site supplies; each meaning is one
# sentence whose subject, "It", is the parameter, since the reference entry
# prints the parameter's name in the sentence before it
_GRID_STATES = TypeParameter(
    "X",
    "It is the set of states on which the method's grid lies; the place and the method's row "
    "determine it.",
)
_SHOCKS = TypeParameter(
    "Z", "It stands for the shocks that the expectation at the place integrates."
)

# the sentence of a method no handler of the package or of an application
# realizes
_NO_IMPLEMENTATION = (
    "No numerical implementation is identified: the package solves nothing, and the handler a "
    "methods file names realizes the method."
)


# Operator entries include the retained head. Each call names its method once
# and carries both public parts in the same authoritative row, with the text
# its reference entry prints beside it. The rows stand in two tables, the
# solution methods of a builder before the representation families of the
# registry and every other method after them; `METHOD_TYPES` reads the
# families between the two each time it is read.
ROWS_BEFORE = dict(
    (
        # the endogenous grid method reads its exogenous grid of savings on
        # the states of the continuation perch (AMD-MB-003 §1; D5)
        _method_type(
            "egm",
            ("builder", ("operator", "argmax")),
            block=True,
            condition="egm-eligibility",
            grid=CONTINUATION,
            text=EntryText(
                meaning=(
                    "In the endogenous grid method, the lines of the method's block invert the "
                    "first-order condition on a grid of end-of-period savings to give the policy "
                    "pairs, each a choice and the decision state at which it is chosen."
                ),
                compatibility=(
                    "Its grid lies on the continuation states, written by the builder's grid "
                    "entry or taken as the default product over those states. Its block's lines "
                    "stand in place of the declared lines at the operative level. A "
                    "representation at the builder's closing Evaluation reads the pairs it "
                    "selects and takes no grid there. A block of explicit formulas that reads no "
                    "value input is refused, naming `!explicit`. The condition `egm-eligibility` "
                    "is listed among the obligations and checked by nothing."
                ),
                example=("policy.method : !egm\npolicy.grid : !Cartesian(a=(a_min, a_max, n_a))"),
                example_meaning=(
                    "The policy builder is solved by the endogenous grid method on `n_a` evenly "
                    "spaced savings from `a_min` to `a_max`."
                ),
                implementation=(
                    "Application handlers realize it, such as `cons-port:egm` of the "
                    "consumption-portfolio application and `asva:make_egm_1d` of the asva "
                    "package; the package itself solves nothing."
                ),
                definition=_TWO_LEVELS,
                type_parameters=(_GRID_STATES,),
                related=("explicit", "time-iteration", "vfi", "Linear"),
            ),
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
                "tol": MethodOption(
                    "positive real",
                    description="The tolerance at which the iteration of the value stops.",
                    omission="handler",
                ),
                "n_c": MethodOption(
                    "positive integer",
                    description=(
                        "The number of candidate levels of the control the search compares at "
                        "each point of the grid."
                    ),
                    omission="handler",
                ),
            },
            grid=OUTPUT_PERCH,
            text=EntryText(
                meaning=(
                    "In value function iteration, the value of a backward builder is updated by "
                    "maximizing over the control at each point of its grid, given the "
                    "continuation value."
                ),
                compatibility=(
                    "Its grid lies on the states of the builder's output perch and may write a "
                    "feasible factor for the control it searches over; where no grid is written "
                    "the default product over those states stands. The values of `tol` and "
                    "`n_c` are checked at configuration."
                ),
                example="cntn_to_dcsn.method : !vfi(n_c=n_c)",
                example_meaning=(
                    "The decision value builder is solved by value function iteration, comparing "
                    "`n_c` candidate levels of the control at each point."
                ),
                implementation=(
                    "Application handlers realize it, such as `cons-port:share_search`; the "
                    "package itself solves nothing."
                ),
                definition=_METHOD_TYPE,
                type_parameters=(_GRID_STATES,),
                related=("egm", "time-iteration", "max"),
            ),
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
            text=EntryText(
                meaning=(
                    "In time iteration, the policy is updated by solving, at each point of its "
                    "grid, the first-order condition the method's lines write, which reads the "
                    "derivative of the continuation value."
                ),
                compatibility=(
                    "Its grid lies on the states of the output perch, or takes the default "
                    "product over them. On a builder its block's lines stand in place of the "
                    "declared lines. A block of explicit formulas that reads no value input is "
                    "refused, naming `!explicit`."
                ),
                example="policy.method : !time_iteration",
                example_meaning=(
                    "The policy builder is solved by time iteration on the first-order condition "
                    "its appended lines state."
                ),
                implementation=(
                    "Application handlers realize it, such as `cons-port:share_search`; the "
                    "package itself solves nothing."
                ),
                definition=_TWO_LEVELS,
                type_parameters=(_GRID_STATES,),
                related=("egm", "explicit", "root-find"),
            ),
        ),
        # the explicit solution of a policy or backward value builder: the
        # lines of its block write every output as an authored expression of
        # the states of the builder's output perch, the parameters and the
        # block's earlier local names, and stand in place of the declared
        # lines at the operative level; the closed form represents the
        # builder's Evaluation where no entry names a representation there
        # (AMD-MT-003 build contract §5; `stage/explicit.py`)
        _method_type(
            "explicit",
            ("builder",),
            block=True,
            text=EntryText(
                meaning=(
                    "In the explicit solution of a policy or backward value builder, the lines of "
                    "the method's block define every output by an authored expression of the "
                    "states of the output perch, the parameters and earlier local names."
                ),
                compatibility=(
                    "The method admits the policy builder and backward value builders and refuses "
                    "a forward builder and a grid. Each line defines one name by "
                    "`name = expression`, reads no value input or its derivative, states no "
                    "relation, applies no "
                    "`argmax`, `solve` or `upper_env`, and defines or reads no field at another "
                    "perch; every output has such a line and a compiled kernel. The declared "
                    "optimization problem stays at the declared level. The builder's Evaluation "
                    "takes the closed form generated from this entry unless an entry names "
                    "another representation there."
                ),
                example=(
                    "[id=policy, policy.method : !explicit] {\n"
                    "    c = (1 - (R*β)^(1/ρ)/R)*(m - 1 + 1/(1 - Γ/R))    :: [id=consumption]\n"
                    "}"
                ),
                example_meaning=(
                    "Consumption is the authored expression of resources and the parameters, "
                    "which stands in place of the declared maximization when the stage is "
                    "solved."
                ),
                implementation=(
                    "The compiled kernels of the block's lines evaluate the solution; compiling "
                    "establishes an evaluator and no optimality."
                ),
                definition=_TWO_LEVELS,
                related=("closed-form", "egm", "time-iteration"),
            ),
        ),
    )
)

# the representation families stand here, one row for each family of the
# registry (`stage/representations.py`), read when the table is read: a
# representation names its family as the method and its grid by the place's
# grid component, on the coordinates of the function it stores (D5); the
# derivatives it evaluates, by order, are information for the stage that
# reads them and checked by nothing (AMD-MB-001 §5.2, D6); what it does
# outside the grid, such as extrapolation, is a keyword its handler reads
ROWS_AFTER = dict(
    (
        _method_type(
            "gauss-hermite",
            (("operator", "E"),),
            keywords=_NODES_PER_SHOCK,
            text=EntryText(
                meaning=(
                    "In Gauss-Hermite quadrature, the expectation over normally or lognormally "
                    "distributed shocks is approximated by weighted values at quadrature nodes."
                ),
                compatibility=(
                    "The method stands at an expectation and takes no grid. It requires one node "
                    "count `n_<shock>` for each shock the expectation integrates, a positive "
                    "integer checked at configuration; a point mass of a mixture is carried "
                    "exactly."
                ),
                example="E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)",
                example_meaning=(
                    "The expectation over the shocks ψ and ξ uses `n_ψ_nodes` and `n_ξ_nodes` "
                    "quadrature nodes."
                ),
                implementation=(
                    "Application handlers realize it, such as `cons-port:gauss_hermite`; the "
                    "package computes no nodes or weights."
                ),
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("quadrature", "monte-carlo"),
            ),
        ),
        _method_type(
            "quadrature",
            (("operator", "E"),),
            text=EntryText(
                meaning=(
                    "In a quadrature rule for an expectation, the integral is approximated by "
                    "weighted values of the integrand, by a rule the method does not name."
                ),
                compatibility=(
                    "The method stands at an expectation and takes no grid; the handler "
                    "identifies the rule and its nodes."
                ),
                example="E_y.method : !quadrature",
                example_meaning=(
                    "The expectation over the shock y is computed by a quadrature rule."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("gauss-hermite",),
            ),
        ),
        _method_type(
            "exact",
            (("operator", "E"),),
            text=EntryText(
                meaning=(
                    "The method evaluates an expectation exactly where the law of the shocks "
                    "allows it and names no further numerical rule."
                ),
                compatibility="The method stands at an expectation and takes no grid.",
                example="E_y.method : !exact",
                example_meaning="The expectation over the shock y is evaluated exactly.",
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("sum", "exact-markov"),
            ),
        ),
        _method_type(
            "exact-markov",
            (("operator", "E"),),
            text=EntryText(
                meaning=(
                    "The method computes the expectation exactly under the declared Markov "
                    "transition probabilities of the shocks."
                ),
                compatibility="The method stands at an expectation and takes no grid.",
                example="E_z.method : !exact_markov",
                example_meaning=(
                    "The expectation over the Markov state z sums its transition probabilities "
                    "exactly."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("markov", "markov-expectation"),
            ),
        ),
        _method_type(
            "markov",
            (("operator", "E"),),
            text=EntryText(
                meaning=(
                    "The method computes the expectation under a Markov law of the shocks and "
                    "names no further numerical rule."
                ),
                compatibility="The method stands at an expectation and takes no grid.",
                example="E_z.method : !markov",
                example_meaning="The expectation over the Markov state z uses its Markov law.",
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("exact-markov", "markov-expectation"),
            ),
        ),
        _method_type(
            "markov-expectation",
            (("operator", "E"),),
            text=EntryText(
                meaning=(
                    "The method computes the expectation under a Markov law of the shocks and "
                    "names no further numerical rule; its word is distinct from `!markov`, with "
                    "the same admission."
                ),
                compatibility="The method stands at an expectation and takes no grid.",
                example="E_z.method : !markov_expectation",
                example_meaning="The expectation over the Markov state z uses its Markov law.",
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("markov", "exact-markov"),
            ),
        ),
        _method_type(
            "sum",
            (("operator", "E"),),
            text=EntryText(
                meaning=(
                    "The method computes the expectation as the probability-weighted sum over "
                    "the points of a finite law of the shocks."
                ),
                compatibility=(
                    "The method stands at an expectation over shocks with a finite law and takes "
                    "no grid."
                ),
                example="E_d.method : !sum",
                example_meaning=(
                    "The expectation over the discrete shock d sums its values weighted by their "
                    "probabilities."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("exact",),
            ),
        ),
        _method_type(
            "tauchen",
            (("operator", "E"),),
            keywords={
                "n_states": MethodOption(
                    "positive integer",
                    description="The number of states of the approximating Markov chain.",
                    omission="handler",
                ),
                "n_income_states": MethodOption(
                    "positive integer",
                    description=(
                        "The number of states of the chain of the income process, where the "
                        "handler reads it apart from `n_states`."
                    ),
                    omission="handler",
                ),
                "n_std": MethodOption(
                    "positive real",
                    description=(
                        "The number of standard deviations the states of the chain span on each "
                        "side of the mean."
                    ),
                    omission="handler",
                ),
                "min_prob": MethodOption(
                    "positive real",
                    description="The smallest transition probability the chain keeps.",
                    omission="handler",
                ),
            },
            text=EntryText(
                meaning=(
                    "In Tauchen's method, a Gaussian autoregressive law of a shock is "
                    "approximated by a finite-state Markov chain."
                ),
                compatibility=(
                    "The method stands at an expectation and takes no grid; the values of its "
                    "keywords are checked at configuration."
                ),
                example="E_ε.method : !tauchen(n_states=n_ε)",
                example_meaning=(
                    "The expectation over the autoregressive shock ε uses a Markov chain of "
                    "`n_ε` states."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_SHOCKS,),
                related=("markov",),
            ),
        ),
        # the methods of a forward builder represent its measure
        # (decision SD-15); a histogram keeps it on a grid of the states of
        # the builder's output perch
        _method_type(
            "deterministic",
            ("builder",),
            kind="representation",
            text=EntryText(
                meaning=(
                    "The method pushes a measure forward through the law of motion of a forward "
                    "builder without sampling and names no further numerical rule."
                ),
                compatibility="The method stands at a builder and takes no grid.",
                example="arvl_to_dcsn.method : !deterministic",
                example_meaning=(
                    "The measure of the arrival states is pushed forward through the law of "
                    "motion to the decision states."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("histogram", "monte-carlo"),
            ),
        ),
        _method_type(
            "histogram",
            ("builder",),
            kind="representation",
            grid=OUTPUT_PERCH,
            text=EntryText(
                meaning=(
                    "The method represents a measure by its masses on a grid of the states of the "
                    "forward builder's output perch."
                ),
                compatibility=(
                    "The method stands at a builder; its grid lies on the states of the builder's "
                    "output perch, or takes the default product over them."
                ),
                example=(
                    "arvl_to_dcsn.method : !histogram\n"
                    "arvl_to_dcsn.grid : !Cartesian(m=(m_min, m_max, n_m))"
                ),
                example_meaning=(
                    "The measure of the decision states is kept as masses on `n_m` evenly spaced "
                    "points from `m_min` to `m_max`."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_THE_GRID,
                type_parameters=(_GRID_STATES,),
                related=("deterministic", "monte-carlo"),
            ),
        ),
        _method_type(
            "identity",
            ("builder",),
            kind="representation",
            text=EntryText(
                meaning=(
                    "The method `!identity` computes a forward measure and names no further "
                    "numerical rule; the word is distinct from the identity label of an "
                    "unassigned component."
                ),
                compatibility="The method stands at a builder and takes no grid.",
                example="arvl_to_dcsn.method : !identity",
                example_meaning=(
                    "The forward builder's measure is computed by the method `!identity`."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("deterministic",),
            ),
        ),
        _method_type(
            "monte-carlo",
            ("builder", ("operator", "E")),
            keywords={
                "n_paths": MethodOption(
                    "positive integer",
                    required=True,
                    description="The number of simulated draws or paths.",
                ),
                "seed": MethodOption(
                    "seed",
                    description="The seed of the random number generator, a nonnegative integer.",
                    omission="handler",
                ),
            },
            text=EntryText(
                meaning=(
                    "In the Monte Carlo method, random draws approximate an expectation, or "
                    "simulate the forward outcomes of a builder."
                ),
                compatibility=(
                    "The method stands at a builder or an expectation and takes no grid. It "
                    "requires `n_paths`; the values of its keywords are checked at configuration."
                ),
                example="dcsn_to_cntn.method : !monte_carlo(n_paths=n_paths)",
                example_meaning=(
                    "The forward builder's measure is simulated by `n_paths` random paths."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("deterministic", "gauss-hermite"),
            ),
        ),
        _method_type(
            "max",
            ("builder", ("operator", "argmax")),
            text=EntryText(
                meaning="The method selects maximizing controls and names no search rule.",
                compatibility="The method stands at a builder or an `argmax` and takes no grid.",
                example="policy.method : !max",
                example_meaning="The policy is the maximizing control the handler selects.",
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("discrete-choice", "golden_section", "vfi"),
            ),
        ),
        _method_type(
            "discrete-choice",
            ("builder", ("operator", "argmax")),
            text=EntryText(
                meaning=(
                    "The method compares discrete alternatives to select the maximizing one and "
                    "names no further rule."
                ),
                compatibility="The method stands at a builder or an `argmax` and takes no grid.",
                example="policy.method : !discrete_choice",
                example_meaning="The policy selects the alternative of highest value.",
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("max",),
            ),
        ),
        _method_type(
            "golden_section",
            (("operator", "argmax"),),
            keywords={
                "n_sections": MethodOption(
                    "positive integer",
                    description="The number of golden-section steps of the search.",
                    omission="handler",
                )
            },
            text=EntryText(
                meaning="The method is golden-section search for a scalar maximum on an interval.",
                compatibility=(
                    "The method stands at an `argmax` and takes no grid; the value of "
                    "`n_sections` is checked at configuration."
                ),
                example="policy.argmax.method : !golden_section(n_sections=n_sections)",
                example_meaning=(
                    "The maximization over the control narrows its interval by `n_sections` "
                    "golden-section steps."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("scipy-bounded", "max"),
            ),
        ),
        _method_type(
            "scipy-bounded",
            (("operator", "argmax"),),
            text=EntryText(
                meaning=(
                    "The method is a bounded scalar search for a maximum within finite bounds, as "
                    "SciPy's bounded `minimize_scalar` performs it."
                ),
                compatibility="The method stands at an `argmax` and takes no grid.",
                example="policy.argmax.method : !scipy_bounded",
                example_meaning=(
                    "The maximization over the control is a bounded scalar search between the "
                    "bounds of its feasible set."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("golden_section", "max"),
            ),
        ),
        # a root finder on a grid of the states of the perch at which the
        # policy it computes stands
        _method_type(
            "root-find",
            (("operator", "solve"), ("operator", "argmax")),
            grid=OUTPUT_PERCH,
            text=EntryText(
                meaning=(
                    "The method finds a root of the residual equations a `solve` or a first-order "
                    "condition writes, at each point of a grid of the output perch's states, and "
                    "names no particular algorithm."
                ),
                compatibility=(
                    "The method stands at a `solve` or an `argmax`; its grid lies on the states "
                    "of the output perch, or takes the default product over them."
                ),
                example="policy.solve.method : !root_find",
                example_meaning=(
                    "The residual equations of the policy's `solve` are solved by a root finder "
                    "at each point of the default grid."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                type_parameters=(_GRID_STATES,),
                related=("newton", "time-iteration"),
            ),
        ),
        _method_type(
            "newton",
            (("operator", "solve"),),
            text=EntryText(
                meaning=(
                    "In Newton's method, the residual equations of a `solve` are solved by "
                    "successive local linear approximations."
                ),
                compatibility="The method stands at a `solve` and takes no grid.",
                example="policy.solve.method : !newton",
                example_meaning=(
                    "The residual equations of the policy's `solve` are solved by Newton's method."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("root-find",),
            ),
        ),
        _method_type(
            "analytic-inverse",
            ("node", "definition", ("operator", "solve")),
            text=EntryText(
                meaning=(
                    "The method uses an analytic inverse to solve a defining equation at a "
                    "`!node` line, a declared function or a `solve`."
                ),
                compatibility=(
                    "The method stands at a `!node` line, a declared function or a `solve` and "
                    "takes no grid."
                ),
                example="𝑑𝑢𝑖𝑛𝑣.method : !analytic_inverse",
                example_meaning=(
                    "The inverse of the marginal utility, declared as `Inv(𝑑𝑢)`, is evaluated by "
                    "its analytic inverse."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("newton",),
            ),
        ),
        _method_type(
            "FUES",
            ("node", ("operator", "upper_env")),
            text=EntryText(
                meaning=(
                    "In the fast upper-envelope scan, competing policy candidates are scanned to "
                    "construct their upper value envelope."
                ),
                compatibility=(
                    "The method stands at a `!node` line or an `upper_env` and takes no grid."
                ),
                example="policy.upper_env.method : !FUES",
                example_meaning=(
                    "The upper envelope of the policy's candidates is constructed by the fast "
                    "upper-envelope scan."
                ),
                implementation=_NO_IMPLEMENTATION,
                definition=_METHOD_TYPE,
                related=("egm",),
            ),
        ),
    )
)


# the row of each representation family, by the family, built once for each
# family that is equal to no family met before
_FAMILY_ROWS = {}


def family_row(family):
    """The row of the method table of the representation family `family`, a
    `RepresentationFamily` of `stage/representations.py`: the places it
    admits, its typed arguments as keywords, the derivatives it offers, the
    perch of its grid and its text, of the kind `representation`. The row of
    a family equal to one met before is the row built then."""
    row = _FAMILY_ROWS.get(family)
    if row is None:
        _, row = _method_type(
            family.word,
            family.admits,
            keywords=dict(family.parameters),
            kind="representation",
            derivatives=family.derivatives,
            evaluates=family.evaluates,
            grid=family.grid,
            text=family.text,
        )
        _FAMILY_ROWS[family] = row
    return row


def fixed_row(word):
    """The row of `ROWS_BEFORE` or `ROWS_AFTER` for a method word as written,
    without its `!`, or with each underscore read as a hyphen, `gauss-hermite`
    for `gauss_hermite` (D1); None where neither holds it, and for a word
    that is no string. A representation family's word names none of these
    rows (`representations.register`)."""
    if not isinstance(word, str):
        return None
    for tag in (word, word.replace("_", "-")):
        row = ROWS_BEFORE.get(tag) or ROWS_AFTER.get(tag)
        if row is not None:
            return row
    return None


# --- the domains of a keyword's value ---

# The domain of a keyword's value, by the kind its `MethodOption` names, each
# a check that answers the reason a value lies outside it, or None: the kinds
# configure checks (`components.check_bound_values`) and the only kinds the
# typed argument of a registered representation family may name
# (`representations.register`).
KEYWORD_DOMAINS = MappingProxyType(
    {
        "positive integer": lambda value: (
            None if type(value) is int and value > 0 else f"{value!r} is not a positive integer"
        ),
        "positive real": lambda value: (
            None
            if (type(value) is int or type(value) is float and math.isfinite(value)) and value > 0
            else f"{value!r} is not a positive real"
        ),
        "seed": lambda value: (
            None if type(value) is int and value >= 0 else f"{value!r} is not a seed"
        ),
    }
)
