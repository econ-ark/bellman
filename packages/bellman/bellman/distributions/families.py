"""The shock families a stage may declare and what their arguments mean.

`N(μ, v)` has variance `v`; a tuple subject `N((μ₁, …), ((Σ₁₁, …), …))` has
covariance matrix Σ; `LogNormal(μ, σ)` has `σ` the standard deviation of the
logarithm; `Uniform(a, b)` is the uniform law on the interval [a, b], with
`a < b` finite; `TruncatedNormal(μ, σ, l, u)` is the normal law of mean `μ`
and standard deviation `σ > 0` conditional on the interval [l, u], with
extended-real endpoints `l < u`, `-inf` and `inf` admitted;
`TruncatedLogNormal(μ, σ, l, u)` is the lognormal law whose logarithm has
mean `μ` and standard deviation `σ > 0`, conditional on the interval [l, u]
of the draw itself, with endpoints `0 ≤ l < u`, `0` and `inf` admitted;
`TypeIExtremeValue(μ, s)` is the maximum type-I extreme-value law with
location `μ` and scale `s > 0`, whose cumulative distribution is
exp(−exp(−(x − μ)/s)). `Mixture((f₁, J₁), …)` draws the component `Jᵢ`
with probability `fᵢ`; `Categorical((f₁, …))` draws the label in position i
of its subject's declared finite set with probability `fᵢ`; `Bernoulli(p)`
draws the second of two points with probability `p`.
`DiscreteMarkov(Π, points)` and `MarkovChain(Π, points)` draw the subject from
the chain with transition probabilities `Π` over `points`, and with a third
argument, `DiscreteMarkov(Π, points, z_pre)`, from the row of `Π` that the
previous state `z_pre` selects, so that the declaration denotes a stochastic
kernel in that field. The weights of a mixture and of a categorical each lie
in the unit interval and sum to one; the condition is retained symbolically
(`weights_condition`) and decided when the calibration gives the numbers
(`check_weights`). The distribution of a label shock gives each label one
weight in label order (`label_weights`).

`FAMILY_ARGUMENTS` is the one table of the arguments each family takes.
`check_argument_count` refuses a call of another number of arguments. The fold,
the graphs and the stage read the admitted families from the table.
`check_real_parameter_shapes` refuses a uniform, truncated normal, truncated
lognormal or type-I extreme-value law of several subjects or of a parameter
declared on a collection, and `parameter_condition` states the condition on
such a law's parameters that the fold retains where an argument has no value.
`law_support` gives the support of a declared law where the package knows
it, for the condition `law-support` decided at calibration.
`product_law` says whether the law of a declaration on a collection is the
product of one scalar law over its index set.
`numeric_value` gives the number a term takes at the calibration's values.
`drop_zeros_and_ones` writes a term without its additions and subtractions of
zero and its multiplications and divisions by one, for printing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import NamedTuple

import numpy

from bellman.distributions import truncation
from bellman.syntax import terms as T
from bellman.syntax.source import to_source

NORMAL = "N"
LOGNORMAL = "LogNormal"
# the four real-parameter families: the three added on 20 October 2026 (the
# brief `additional-continuous-shock-distributions.md`), the uniform law on
# an interval, the normal law conditional on an interval, and the maximum
# type-I extreme-value law, and the lognormal law conditional on an interval
# of the draw (AMD-SG-036, requested by CDC on 18 October 2026 and spelled
# as the truncated normal is on CDC's ruling of 20 October). Each takes real
# numbers alone: a tuple argument, a tuple subject and a collection-valued
# parameter are refused
UNIFORM = "Uniform"
TRUNCATED_NORMAL = "TruncatedNormal"
TRUNCATED_LOGNORMAL = "TruncatedLogNormal"
EXTREME_VALUE = "TypeIExtremeValue"
REAL_PARAMETER_FAMILIES = (UNIFORM, TRUNCATED_NORMAL, TRUNCATED_LOGNORMAL, EXTREME_VALUE)
# the scalar families: those whose definition the table of definitions holds
# and whose declaration of one real subject denotes the measure at the
# written arguments
SCALAR_FAMILIES = (NORMAL, LOGNORMAL, *REAL_PARAMETER_FAMILIES)
# the two families whose declaration carries weights: a mixture writes one
# (weight, component) pair per component, a categorical one weight per
# declared label
MIXTURE = "Mixture"
CATEGORICAL = "Categorical"
# the family whose support is two points: `Bernoulli(p)` draws the second of
# its subject's two points with probability p and the first with 1 - p. The
# result set of the extension is the subject's declared set, as the parser
# reads it; that the subject takes only those two points is the family's
# obligation
BERNOULLI = "Bernoulli"
# the two families of a finite chain, which differ in name alone: the subject
# is drawn from the chain's transition probabilities over its states, and from
# the one row the previous state selects where a third argument writes that
# state
DISCRETE_MARKOV = "DiscreteMarkov"
MARKOV_CHAIN = "MarkovChain"


# --- each family's arguments, and the conditions on them ---


def check_family_conditions(owner, values, refuse, *, indexed=False, dimension=None) -> bool:
    """The family conditions of one declaration, refused under the rule
    distribution-domain. A normal declaration's mean and covariance have the
    dimension of its subject. Where `values` makes the terms numbers, a scalar
    variance is nonnegative, a covariance matrix is symmetric positive
    semidefinite, a lognormal standard deviation is nonnegative, the weights
    of a mixture or a categorical lie in the unit interval and sum to one, and
    a Bernoulli probability lies in the unit interval. The endpoints of a
    uniform law are finite and in order, a < b; a truncated normal has a
    finite mean, a finite positive standard deviation and extended-real
    endpoints in order, l < u; a truncated lognormal has a finite mean and a
    finite positive standard deviation of the logarithm and endpoints of the
    draw in order, 0 ≤ l < u; a type-I extreme-value law has a finite
    location and a finite positive scale; every argument of these four is a
    real number (`_real_argument`). Every component of a mixture that is a
    call of a scalar family is checked as a declaration of that family, its
    messages naming the component. `values` binds parameter names; a
    condition on a term that names another value is not decided here. The
    fold records such a condition on weights, on a covariance matrix or on
    the parameters of the four families as an obligation; a scalar variance
    and a lognormal standard deviation are decided only at the calibration.
    Returns whether every condition was decided.

    `indexed` says that the one subject is a collection on an index set, one
    random vector whose components are the members of that set, and
    `dimension` the number of its components at the values, or the number of
    members of a subject declared on a finite set, None where the values do
    not decide it (`subject_dimension`). A law written for a vector of another
    size, and a named mean, covariance or transition row whose value has
    another size, are refused at that dimension.

    The number of arguments is checked first, so that a call of the wrong
    number of arguments is refused before any condition is read off its
    arguments."""
    check_argument_count(owner, refuse)
    term = owner.term
    if (
        weights_of(owner)
        or weight_matrix_text(owner) is not None
        or bernoulli_probability(owner) is not None
    ):
        decided = check_weights(owner, values, refuse, dimension=dimension)
        if isinstance(term, T.Call) and term.fun == MIXTURE:
            for law, named in _scalar_laws(owner):
                decided = _check_scalar_law(law, values, refuse, named) and decided
        return decided
    if isinstance(term, T.Call) and term.fun in SCALAR_FAMILIES:
        return _check_scalar_law(owner, values, refuse, indexed=indexed, dimension=dimension)
    return True


def _check_scalar_law(owner, values, refuse, named=None, *, indexed=False, dimension=None) -> bool:
    """The conditions of a declaration, or of a mixture's component, whose
    term is a call of a family in `SCALAR_FAMILIES`. `named` names a
    component in the messages; a declaration is named as its family's check
    names it. Returns whether every condition was decided."""
    fun = owner.term.fun
    if fun == NORMAL:
        return _check_normal(
            owner, values, refuse, indexed=indexed, dimension=dimension, named=named
        )
    if fun == LOGNORMAL:
        return len(owner.term.args) != 2 or _check_lognormal(owner, values, refuse, named=named)
    named = named or declaration_text(owner)
    if fun == UNIFORM:
        return _check_uniform(owner, values, refuse, named)
    if fun == TRUNCATED_NORMAL:
        return _check_truncated_normal(owner, values, refuse, named)
    if fun == TRUNCATED_LOGNORMAL:
        return _check_truncated_lognormal(owner, values, refuse, named)
    return _check_extreme_value(owner, values, refuse, named)


@dataclass(frozen=True)
class ArgumentShape:
    """The arguments one admitted family takes: the fewest it admits, the most
    it admits (None where any number above the fewest is admitted), and the
    words naming them, which the refusal of a call of another number quotes."""

    fewest: int
    most: int | None
    named: str

    def admits(self, count) -> bool:
        """Whether the family admits a call of `count` arguments."""
        return self.fewest <= count and (self.most is None or count <= self.most)

    def in_words(self) -> str:
        """How many arguments the family takes, in words."""
        if self.most is None:
            return f"{self.fewest} or more arguments"
        if self.most == self.fewest:
            return _counted(self.fewest)
        return f"{self.fewest} or {self.most} arguments"


# the words naming the arguments of the two families of a finite chain
_CHAIN_ARGUMENTS = (
    "the transition probabilities, written as a matrix, named or a tuple of rows, or as the "
    "one row the previous state selects; the chain's states, written as a tuple of points, a "
    "named vector, a set or a tuple of the subjects' sets; and, where a third is written, the "
    "previous state, a field of the stage on whose value the draw is conditioned"
)
# the arguments each admitted family takes, in the conventions at the head of
# this module: the one table of each family's arguments. `check_argument_count`
# reads it; so do the refusal of a family the table does not name, in
# `graphs/wire_sorts.py`, and the readers of a stage's external calls in the
# fold and the stage, for which a family's call is no external call. The keys
# are the admitted families.
FAMILY_ARGUMENTS = {
    NORMAL: ArgumentShape(
        fewest=2,
        most=2,
        named="a mean and a variance, or for a tuple subject a mean vector and a "
        "covariance matrix",
    ),
    LOGNORMAL: ArgumentShape(
        fewest=2,
        most=2,
        named="a location and a scale, the mean and the standard deviation of the logarithm",
    ),
    UNIFORM: ArgumentShape(
        fewest=2, most=2, named="the two endpoints of the interval, finite and in order, a < b"
    ),
    TRUNCATED_NORMAL: ArgumentShape(
        fewest=4,
        most=4,
        named="the mean and the standard deviation of the underlying normal and the two "
        "endpoints of the truncation interval, l < u, with -inf and inf admitted",
    ),
    TRUNCATED_LOGNORMAL: ArgumentShape(
        fewest=4,
        most=4,
        named="the mean and the standard deviation of the logarithm and the two endpoints "
        "of the truncation interval in the draw's own units, 0 ≤ l < u, with 0 and inf "
        "admitted",
    ),
    EXTREME_VALUE: ArgumentShape(
        fewest=2, most=2, named="a location and a scale, the scale positive"
    ),
    DISCRETE_MARKOV: ArgumentShape(fewest=2, most=3, named=_CHAIN_ARGUMENTS),
    MARKOV_CHAIN: ArgumentShape(fewest=2, most=3, named=_CHAIN_ARGUMENTS),
    MIXTURE: ArgumentShape(
        fewest=2, most=None, named="one pair of a weight and a component for each component"
    ),
    CATEGORICAL: ArgumentShape(
        fewest=1,
        most=1,
        named="the weights, written as a tuple, as the rows of a matrix or as the "
        "one row a previous state selects",
    ),
    BERNOULLI: ArgumentShape(fewest=1, most=1, named="one probability"),
}


def check_argument_count(owner, refuse) -> None:
    """The number of arguments each family call of one declaration writes,
    against the arguments its family takes in `FAMILY_ARGUMENTS`. A call of
    another number is refused under the rule readable-form, the message naming
    the family and the arguments it takes. A call of a family the table does
    not name is not checked: it is an author's own provider, whose signature
    the stage does not fix. A declaration that is no call is not checked
    either."""
    for term in _family_calls(owner.term):
        declared = FAMILY_ARGUMENTS[term.fun]
        if declared.admits(len(term.args)):
            continue
        refuse(
            "readable-form",
            owner.address,
            f"{declaration_text(owner)} writes {to_source(term)}, a call of "
            f"{_counted(len(term.args))}; `{term.fun}` takes {declared.in_words()}, "
            f"{declared.named}; write the call with the arguments the family takes",
            write=f"Write the call of `{term.fun}` with {declared.in_words()}, {declared.named}",
        )


def _family_calls(term):
    """Every call of an admitted family within a declaration's term, the head
    call first and then the calls its arguments hold, in the order the term is
    written: a component of a mixture may itself be a family's call, and a
    call of another number of arguments is refused wherever it stands."""
    if isinstance(term, T.Call) and term.fun in FAMILY_ARGUMENTS:
        yield term
    for part in _subterms(term):
        yield from _family_calls(part)


def _subterms(term):
    """The retained terms a term holds directly, in the order of its fields."""
    if isinstance(term, (tuple, list)):
        for item in term:
            yield item
        return
    if not is_dataclass(term):
        return
    for field in fields(term):
        value = getattr(term, field.name)
        if isinstance(value, (tuple, list)) or is_dataclass(value):
            yield value


def check_weights(owner, values, refuse, dimension=None) -> bool:
    """The weight condition of a declaration where `values` decides it,
    refused under the rule distribution-domain. Each written probability
    vector of a mixture or a categorical lies in the unit interval and sums to
    one. A categorical that selects a row of a written matrix carries one
    vector per row. A categorical that selects from a matrix the file does not
    write out is decided once the values bind the matrix, or each named row:
    every row has one entry per member of the subject's set, `dimension`,
    where that count is known, lies in the unit interval and sums to one; the
    refusal names the row. The p of a `Bernoulli(p)` lies in the unit
    interval. Returns whether every condition was decided."""
    decided = True
    probability = bernoulli_probability(owner)
    if probability is not None:
        number = numeric_value(probability, values)
        if number is None:
            return False
        if not 0.0 <= number <= 1.0:
            refuse(
                "distribution-domain",
                owner.address,
                f"{declaration_text(owner)} has the probability {to_source(probability)} = "
                f"{number!r}, which is not a probability; `Bernoulli(p)` takes p in [0, 1]",
            )
        return True
    if weight_matrix_text(owner) is not None:
        # the file does not write the rows: the values bind them, or the
        # obligation the fold records remains required
        rows = _named_rows(owner, values)
        if rows is None:
            return False
        matrix = weight_matrix_text(owner)
        for key, row in rows:
            if dimension is not None and len(row) != dimension:
                refuse(
                    "distribution-domain",
                    owner.address,
                    f"the row at {key} of {matrix}, the matrix {declaration_text(owner)} selects "
                    f"from, has {len(row)} entries where the subject's set has {dimension} "
                    f"members at the values; write one probability "
                    f"per member",
                    write=f"Write {dimension} probabilities in the row at {key}, one per member",
                )
            outside = [number for number in row if not 0.0 <= number <= 1.0]
            if outside:
                refuse(
                    "distribution-domain",
                    owner.address,
                    f"the row at {key} of {matrix}, the matrix {declaration_text(owner)} selects "
                    f"from, has the entry {outside[0]!r}, which is not a probability; each entry "
                    f"lies in [0, 1]",
                )
            total = math.fsum(row)
            if abs(total - 1.0) > tolerance([total]):
                refuse(
                    "distribution-domain",
                    owner.address,
                    f"the row at {key} of {matrix}, the matrix {declaration_text(owner)} selects "
                    f"from, sums to {total!r}, not to one; write rows that sum to one",
                    write=f"Write the row at {key} with entries that sum to one",
                )
        return True
    for weights in weights_of(owner):
        numbers = [numeric_value(term, values) for term in weights]
        if any(number is None for number in numbers):
            decided = False
            continue
        written = ", ".join(to_source(term) for term in weights)
        if dimension is not None and len(weights) != dimension:
            refuse(
                "distribution-domain",
                owner.address,
                f"{declaration_text(owner)} writes {len(weights)} weights, {written}, where the "
                f"subject's set has {dimension} members at the values; "
                f"write one weight per member",
                write=f"Write {dimension} weights, one per member",
            )
        outside = [
            (term, number) for term, number in zip(weights, numbers) if not 0.0 <= number <= 1.0
        ]
        if outside:
            term, number = outside[0]
            refuse(
                "distribution-domain",
                owner.address,
                f"{declaration_text(owner)} has the weight {_value_text(term, number)}, which "
                f"is not a probability; each weight of {written} lies in [0, 1] and they sum to "
                f"one; "
                f"write weights in the unit interval",
                write=_value_action(term, "a weight", "lies in the unit interval"),
            )
        total = math.fsum(numbers)
        if abs(total - 1.0) > tolerance([total]):
            refuse(
                "distribution-domain",
                owner.address,
                f"the weights {written} of {declaration_text(owner)} sum to {total!r}, not to "
                f"one; write weights that sum to one",
                write="Write weights that sum to one",
            )
    return decided


def _named_rows(owner, values):
    """The rows of the matrix a categorical selects a row of, read from the
    values: for a named matrix, `Categorical(Π[z_prev])`, each row of the
    value of `Π` with its position counted from one; for a tuple of named
    rows, `Categorical((Q_h, Q_m, Q_l)[e_c])`, the value of each name with the
    name. None where a value is missing or is no sequence of numbers."""
    argument = owner.term.args[0]
    family = argument.family
    if isinstance(family, T.Sym) and isinstance(family.symbol, T.Constant):
        matrix = values.get(family.symbol.name)
        if not _is_sequence(matrix) or not all(_is_sequence(row) for row in matrix):
            return None
        rows = [(f"position {index + 1}", row) for index, row in enumerate(matrix)]
    elif isinstance(family, T.Tuple) and all(
        isinstance(item, T.Sym) and isinstance(item.symbol, T.Constant) for item in family.items
    ):
        rows = [(item.symbol.name, values.get(item.symbol.name)) for item in family.items]
        if not all(_is_sequence(row) for _, row in rows):
            return None
    else:
        return None
    read = []
    for key, row in rows:
        numbers = [_number_of(entry) for entry in row]
        if any(number is None for number in numbers):
            return None
        read.append((key, numbers))
    return read


def _is_sequence(value) -> bool:
    """Whether a calibration value is a sequence of entries, a list or a
    tuple and no string."""
    return isinstance(value, (list, tuple))


def _number_of(value):
    """A calibration entry as a float, or None where it is no number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def weights_condition(owner) -> str:
    """The weight condition of a declaration in words, the sentence of the
    obligation the fold records: each written probability vector lies in the
    unit interval and sums to one; the rows of a named transition matrix
    likewise; and the two points of a `Bernoulli` have the probabilities
    1 - p (the first) and p (the second), with p in the unit interval. The
    complement is the term 1 - p, which the printer writes with a compound p
    in brackets."""
    probability = bernoulli_probability(owner)
    if probability is not None:
        complement = T.Sub(T.Number(1), probability)
        return (
            f"{declaration_identity_text(owner)} gives its subject the value 1 with probability "
            f"{to_source(probability)} and the value 0 with probability {to_source(complement)}, "
            f"both in its declared set, and {to_source(probability)} lies in [0, 1]"
        )
    written_matrix = weight_matrix_text(owner)
    if written_matrix is not None:
        return (
            f"each row of {written_matrix}, the matrix {declaration_identity_text(owner)} selects "
            f"from, lies in [0, 1] and sums to one"
        )
    lists = weights_of(owner)
    written = "; ".join(
        "(" + ", ".join(to_source(term) for term in weights) + ")" for weights in lists
    )
    return (
        f"the weights {written} of {declaration_identity_text(owner)} each lie in [0, 1] and sum "
        f"to one"
    )


def weights_of(owner):
    """The retained weight lists of a declaration that carries weights, one
    list per probability vector the declaration writes: the first item of each
    pair of a `Mixture`; the items of the tuple of a `Categorical`; and, where
    a `Categorical` selects a row of a written matrix, as a Markov chain is
    written, one list per row. Empty for another family or another shape,
    including a `Bernoulli(p)`, whose two weights are p and 1 - p and sum to
    one by construction. That p lies in the unit interval is stated by
    `weights_condition` and decided by `check_weights`."""
    term = owner.term
    if not isinstance(term, T.Call):
        return ()
    if term.fun == MIXTURE:
        pairs = list(term.args)
        if not pairs or any(
            not (isinstance(item, T.Tuple) and len(item.items) == 2) for item in pairs
        ):
            return ()
        return (tuple(item.items[0] for item in pairs),)
    if term.fun == CATEGORICAL and len(term.args) == 1:
        argument = term.args[0]
        if isinstance(argument, T.Tuple):
            if all(isinstance(item, T.Tuple) for item in argument.items):
                return tuple(tuple(row.items) for row in argument.items)
            return (tuple(argument.items),)
        # a row selected from a written matrix (`T.Select` of a `T.Tuple` of
        # rows, as a Markov chain is written): every row is a probability
        # vector
        matrix = argument.family if isinstance(argument, T.Select) else None
        if (
            isinstance(matrix, T.Tuple)
            and matrix.items
            and all(isinstance(row, T.Tuple) for row in matrix.items)
        ):
            return tuple(tuple(row.items) for row in matrix.items)
    return ()


def weight_matrix_text(owner):
    """The matrix a `Categorical` selects a row of, as it is written, where
    its rows are not written out in the file: a declared name, as
    `z ~ Categorical(Π[z_prev])` writes a Markov chain, or a tuple of named
    rows, as `e_n ~ Categorical((Q_h, Q_m, Q_l)[e_c])` writes one. None where
    the rows are written out, which `weights_of` reads, and for another family
    or another shape. That each row is a probability vector is a condition no
    number in the file decides, so the fold records it as an obligation, which
    stays undecided until the calibration binds the rows."""
    term = owner.term
    if not isinstance(term, T.Call) or term.fun != CATEGORICAL or len(term.args) != 1:
        return None
    argument = term.args[0]
    if not isinstance(argument, T.Select):
        return None
    family = argument.family
    if (
        isinstance(family, T.Tuple)
        and family.items
        and all(isinstance(row, T.Tuple) for row in family.items)
    ):
        return None
    return to_source(family)


def bernoulli_probability(owner):
    """The retained term p of a `Bernoulli(p)` declaration, or None for
    another family or another shape."""
    term = owner.term
    if isinstance(term, T.Call) and term.fun == BERNOULLI and len(term.args) == 1:
        return term.args[0]
    return None


def _check_normal(owner, values, refuse, *, indexed=False, dimension=None, named=None) -> bool:
    """The conditions of a normal declaration: its mean and covariance have
    the dimension of its subject; where `values` makes every entry of the
    covariance a number, a scalar variance is nonnegative and a covariance
    matrix is symmetric positive semidefinite. For an indexed subject the
    dimension is `dimension`, the count of its index set at the values: a law
    written for another number of components, and a named mean or covariance
    whose value has another size, are refused. `named` names the declaration,
    or the mixture's component, in the messages of a law of one subject.
    Returns whether the conditions at numbers were decided."""
    term = owner.term
    parts = normal_mean_and_covariance(owner, indexed=indexed)
    if parts is None:
        declaration = declaration_text(owner)
        refuse(
            "distribution-domain",
            owner.address,
            f"{named or declaration} writes N({', '.join(to_source(a) for a in term.args)}), "
            f"whose mean and covariance do not have the dimension {len(owner.subjects)} of its "
            f"subject; `N(μ, v)` of one shock takes a mean and a variance, "
            f"`N((μ₁, …), ((Σ₁₁, …), …))` of a tuple a mean tuple and a covariance matrix",
        )
    covariance = parts.covariance
    if isinstance(parts, NamedMeanAndCovariance):
        mean_name, covariance_name = parts.means[0].symbol.name, covariance[0][0].symbol.name
        if mean_name not in values or covariance_name not in values:
            return False
        mean, matrix = values[mean_name], values[covariance_name]
        if not (
            _is_sequence(mean) and _is_sequence(matrix) and all(_is_sequence(r) for r in matrix)
        ):
            refuse(
                "distribution-domain",
                owner.address,
                f"{named or declaration_text(owner)} names "
                f"{mean_name} as its mean vector and {covariance_name} as its covariance "
                f"matrix, but their "
                f"calibration values do not have those shapes; "
                f"write one mean entry and one covariance row per component",
                write=(
                    f"Write one mean entry in {mean_name} and one covariance row in "
                    f"{covariance_name} per component"
                ),
            )
        rows = [[_number_of(entry) for entry in row] for row in matrix]
        means = [_number_of(entry) for entry in mean]
        if any(entry is None for row in rows for entry in row) or any(m is None for m in means):
            return False
        sizes = {len(means), len(rows), *(len(row) for row in rows)}
        if dimension is not None:
            sizes.add(dimension)
        if len(sizes) != 1:
            refuse(
                "distribution-domain",
                owner.address,
                f"the mean {mean_name} of {named or declaration_text(owner)} "
                f"has {len(means)} entries and the covariance {covariance_name} {len(rows)} "
                f"rows of {', '.join(str(len(row)) for row in rows)} entries, where "
                f"{names_text(owner.subjects)} has "
                f"{dimension if dimension is not None else 'one component per member'}"
                f"{' components at the values' if dimension is not None else ''}; write one "
                f"mean entry and one covariance row per component",
                write=(
                    f"Write one mean entry in {mean_name} and one covariance row in "
                    f"{covariance_name} per component"
                ),
            )
        matrix = rows
    else:
        if indexed and dimension is not None and len(covariance) != dimension:
            declaration = declaration_text(owner)
            refuse(
                "distribution-domain",
                owner.address,
                f"{named or declaration} is written for {len(covariance)} component"
                f"{'s' if len(covariance) != 1 else ''}, where {names_text(owner.subjects)} has "
                f"{dimension} components at the values; write the law "
                f"with one mean entry and one covariance row per component",
                write=(
                    f"Write the law with one mean entry and one covariance row for each of the "
                    f"{dimension} components"
                ),
            )
        matrix = number_matrix(covariance, values)
        if matrix is None:
            return False
    within = tolerance(entry for row in matrix for entry in row)
    n = len(matrix)
    asymmetric = [
        (i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if abs(matrix[i][j] - matrix[j][i]) > within
    ]
    if n == 1 and matrix[0][0] < 0:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named or declaration_text(owner)} has the variance "
            f"{_value_text(covariance[0][0], matrix[0][0])}, which is negative; `N(μ, v)` "
            f"takes the variance v ≥ 0; "
            f"write a nonnegative variance",
            write=_value_action(covariance[0][0], "a variance", "is nonnegative"),
        )
    if asymmetric:
        i, j = asymmetric[0]
        refuse(
            "distribution-domain",
            owner.address,
            f"the covariance of {named or declaration_text(owner)} is not "
            f"symmetric: entry ({i + 1}, {j + 1}) is {matrix[i][j]!r} and entry "
            f"({j + 1}, {i + 1}) is {matrix[j][i]!r}; "
            f"write a "
            f"symmetric covariance matrix",
            write=(
                f"Write a symmetric covariance matrix, whose entries ({i + 1}, {j + 1}) and "
                f"({j + 1}, {i + 1}) are equal"
            ),
        )
    if n > 1:
        lowest = smallest_eigenvalue(matrix)
        if lowest < -within:
            refuse(
                "distribution-domain",
                owner.address,
                f"the covariance "
                f"{to_source(T.Tuple(tuple(T.Tuple(tuple(row)) for row in covariance)))} of "
                f"{named or declaration_text(owner)} is not positive semidefinite: its "
                f"smallest eigenvalue is {lowest!r}; write a symmetric positive semidefinite "
                f"covariance matrix",
                write="Write a symmetric positive semidefinite covariance matrix",
            )
    return True


def _check_lognormal(owner, values, refuse, named=None) -> bool:
    """The condition of a lognormal declaration `LogNormal(μ, σ)`: where
    `values` makes σ a number, σ is nonnegative. `named` names the
    declaration, or the mixture's component, in the message. Returns whether
    it was decided."""
    term = owner.term
    named = named or declaration_text(owner)
    deviation = numeric_value(term.args[1], values)
    if deviation is None:
        return False
    if deviation < 0:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the standard deviation of the "
            f"logarithm {to_source(term.args[1])} = {deviation!r}, which is negative; "
            f"`LogNormal(μ, σ)` takes σ ≥ 0",
        )
    return True


# the arguments of the four real-parameter families in order, each as the
# letter of the family's written form and the words naming it in a message
_PARAMETERS = {
    UNIFORM: (("a", "the lower endpoint"), ("b", "the upper endpoint")),
    TRUNCATED_NORMAL: (
        ("μ", "the mean"),
        ("σ", "the standard deviation"),
        ("l", "the lower endpoint"),
        ("u", "the upper endpoint"),
    ),
    TRUNCATED_LOGNORMAL: (
        ("μ", "the mean of the logarithm"),
        ("σ", "the standard deviation of the logarithm"),
        ("l", "the lower endpoint"),
        ("u", "the upper endpoint"),
    ),
    EXTREME_VALUE: (("μ", "the location"), ("s", "the scale")),
}
# the condition on the parameters of each of the four families, the
# sentence `parameter_condition` completes with the written arguments, one
# `letter = term` per position
_DOMAIN_CONDITIONS = {
    UNIFORM: "a < b, with {0} and {1}, both finite",
    TRUNCATED_NORMAL: "σ > 0 and l < u, with {0} and {1} finite, {2} and {3}",
    TRUNCATED_LOGNORMAL: "σ > 0 and 0 ≤ l < u, with {0} and {1} finite, {2} and {3}",
    EXTREME_VALUE: "s > 0, with {0} and {1}, both finite",
}


def _check_uniform(owner, values, refuse, named) -> bool:
    """The conditions of `Uniform(a, b)`: two real endpoints, both finite, in
    order, a < b. Returns whether they were decided."""
    lower = _real_argument(owner, 0, values, refuse, named)
    upper = _real_argument(owner, 1, values, refuse, named)
    if lower is None or upper is None:
        return False
    if not lower < upper:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the endpoints a = {_value_text(owner.term.args[0], lower)} and "
            f"b = {_value_text(owner.term.args[1], upper)}, which are not in order; "
            f"`Uniform(a, b)` takes a < b",
        )
    return True


def _check_truncated_normal(owner, values, refuse, named) -> bool:
    """The conditions of `TruncatedNormal(μ, σ, l, u)`: a finite real mean, a
    finite positive standard deviation, and extended-real endpoints in order,
    l < u, so that `-inf` and `inf` are admitted as endpoints and two equal
    endpoints, infinite ones included, are refused. Returns whether they were
    decided."""
    mean = _real_argument(owner, 0, values, refuse, named)
    deviation = _real_argument(owner, 1, values, refuse, named)
    if deviation is not None and not deviation > 0:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the standard deviation σ = "
            f"{_value_text(owner.term.args[1], deviation)}, which is not positive; "
            f"`TruncatedNormal(μ, σ, l, u)` takes σ > 0",
        )
    lower = _real_argument(owner, 2, values, refuse, named, endpoint=True)
    upper = _real_argument(owner, 3, values, refuse, named, endpoint=True)
    if lower is not None and upper is not None and not lower < upper:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the truncation endpoints l = {_value_text(owner.term.args[2], lower)} "
            f"and u = {_value_text(owner.term.args[3], upper)}, which are not in order; "
            f"`TruncatedNormal(μ, σ, l, u)` takes l < u",
        )
    return None not in (mean, deviation, lower, upper)


def _check_truncated_lognormal(owner, values, refuse, named) -> bool:
    """The conditions of `TruncatedLogNormal(μ, σ, l, u)`: a finite real mean
    and a finite positive standard deviation of the logarithm, and endpoints
    of the draw in order with the lower one nonnegative, 0 ≤ l < u, so that
    `0` is admitted as the lower endpoint and `inf` as the upper, two equal
    endpoints are refused, and a negative lower endpoint, `-inf` included, is
    refused, since the draw is positive. Returns whether they were decided."""
    mean = _real_argument(owner, 0, values, refuse, named)
    deviation = _real_argument(owner, 1, values, refuse, named)
    if deviation is not None and not deviation > 0:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the standard deviation of the logarithm σ = "
            f"{_value_text(owner.term.args[1], deviation)}, which is not positive; "
            f"`TruncatedLogNormal(μ, σ, l, u)` takes σ > 0",
        )
    lower = _real_argument(owner, 2, values, refuse, named, endpoint=True)
    upper = _real_argument(owner, 3, values, refuse, named, endpoint=True)
    if lower is not None and lower < 0:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the lower endpoint l = {_value_text(owner.term.args[2], lower)}, "
            f"which is negative; `TruncatedLogNormal(μ, σ, l, u)` takes 0 ≤ l < u, the draw "
            f"being positive, with 0 for no lower bound",
        )
    if lower is not None and upper is not None and not lower < upper:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the truncation endpoints l = {_value_text(owner.term.args[2], lower)} "
            f"and u = {_value_text(owner.term.args[3], upper)}, which are not in order; "
            f"`TruncatedLogNormal(μ, σ, l, u)` takes l < u",
        )
    return None not in (mean, deviation, lower, upper)


def law_support(owner, values):
    """The support of a declared law at the numbers `values` gives its
    arguments, as a `truncation.Support`, where the package knows it: for a
    truncated lognormal whose four arguments are numbers that satisfy its
    conditions, the interval [l, u] of the draw, open at a lower endpoint 0
    and at an upper endpoint inf (AMD-SG-036 §4). None for another family,
    a mixture with a truncated component included, and where a number is
    missing."""
    term = owner.term
    if not (isinstance(term, T.Call) and term.fun == TRUNCATED_LOGNORMAL and len(term.args) == 4):
        return None
    numbers = [numeric_value(argument, values) for argument in term.args]
    if any(number is None for number in numbers):
        return None
    mean, deviation, lower, upper = numbers
    if math.isinf(mean) or math.isinf(deviation) or not deviation > 0 or not 0 <= lower < upper:
        return None
    return truncation.support(lower, upper)


def _check_extreme_value(owner, values, refuse, named) -> bool:
    """The conditions of `TypeIExtremeValue(μ, s)`: a finite real location
    and a finite positive scale. Returns whether they were decided."""
    location = _real_argument(owner, 0, values, refuse, named)
    scale = _real_argument(owner, 1, values, refuse, named)
    if scale is not None and not scale > 0:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has the scale s = {_value_text(owner.term.args[1], scale)}, which is not "
            f"positive; `TypeIExtremeValue(μ, s)` takes s > 0",
        )
    return location is not None and scale is not None


def _real_argument(owner, position, values, refuse, named, *, endpoint=False):
    """The number the argument at `position` of a uniform, truncated normal or
    type-I extreme-value call takes at `values`, or None where the argument
    has no number at `values`. An argument that reads a parameter `values`
    does not bind keeps its condition until a calibration binds it. An
    argument that is a call or any other term outside the arithmetic
    `numeric_value` evaluates, or that reads a state, a control or a parent
    shock, keeps its condition as the obligation
    distribution-parameters-in-domain, which no calibration decides.
    Refused under the rule distribution-domain: a tuple; a name bound to a
    value that is no real number, a list or a boolean; arithmetic of valued
    names that has no number, a division by zero, a power with no real value
    or a power beyond the floating-point range; the number NaN, as
    `inf - inf` gives; and an infinite number, except at a truncation
    endpoint (`endpoint`). `inf`, `∞` and `-inf` are numbers. The binder
    refuses a value that is no real number for a parameter declared on a
    real set before this check is made, so the refusal of such a bound value
    here decides only a value that reaches this function by another path."""
    call = owner.term
    term = call.args[position]
    letter, words = _PARAMETERS[call.fun][position]
    form = _written_form(call.fun)
    if isinstance(term, T.Tuple):
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} writes {words} {letter} as {to_source(term)}, which is not a real number; "
            f"`{form}` takes real arguments",
        )
        return None
    names = _names_read(term)
    if names is None:
        return None
    if any(name not in values for name in names):
        return None
    for name in sorted(names):
        if _number_of(values[name]) is None:
            refuse(
                "distribution-domain",
                owner.address,
                f"{named} has {words} {letter} = {to_source(term)}, where {name} = "
                f"{values[name]!r}, which is not a real number; `{form}` takes real arguments",
            )
            return None
    number = numeric_value(term, values)
    if number is None:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has {words} {letter} = {to_source(term)}, which has no number: a "
            f"division by zero, a power with no real value or a power beyond the "
            f"floating-point range; `{form}` takes real arguments",
        )
        return None
    if math.isnan(number):
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has {words} {letter} = {to_source(term)}, which is not a number; "
            f"`{form}` takes real arguments",
        )
        return None
    if math.isinf(number) and not endpoint:
        refuse(
            "distribution-domain",
            owner.address,
            f"{named} has {words} {letter} = {_value_text(term, number)}, which is not finite; "
            f"`{form}` takes a finite {letter}",
        )
        return None
    return number


def _value_action(term, noun, held):
    """The action of a condition that the number of `term` fails, `noun`
    what the term is, `a weight`, and `held` the condition in words, `lies
    in the unit interval`. A term written as a number is replaced in the
    declaration, `Write a weight that lies in the unit interval in place of
    1.5`; a term that reads parameters is given a value in the calibration
    file, `Give π a value in the calibration file at which 1 - π lies in the
    unit interval`, so that the term as written tells the two files apart."""
    names = sorted(_names_read(term) or ())
    written = to_source(term)
    if not names:
        return f"Write {noun} that {held} in place of {written}"
    return (
        f"Give {' and '.join(names)} {'a value' if len(names) == 1 else 'values'} in the "
        f"calibration file at which {'it' if written in names else written} {held}"
    )


def _value_text(term, number):
    """A term and the number it takes, `b_y = 1.0`, or the term alone where
    it is written as that number."""
    written = to_source(term)
    try:
        same = float(written.replace("∞", "inf")) == number
    except ValueError:
        same = False
    return written if same else f"{written} = {number!r}"


def _written_form(family):
    """The written form of a real-parameter family's call, `Uniform(a, b)`."""
    return f"{family}({', '.join(letter for letter, _ in _PARAMETERS[family])})"


def _scalar_laws(owner, text=None):
    """The calls of a family in `SCALAR_FAMILIES` a declaration writes, each
    as a declaration of its own with the words naming it in a message: the
    declaration itself with None where its term is such a call, the
    declaration's words then standing, and each such component of a mixture
    with the words `the <family> component of the <family> declaration …`,
    the declaration named by `text`, `declaration_text` where none is given."""
    for call in _family_calls(owner.term):
        if call.fun not in SCALAR_FAMILIES:
            continue
        if call is owner.term:
            yield owner, None
        else:
            yield replace(owner, term=call), _component_text(owner, call, text or declaration_text)


def check_real_parameter_shapes(owner, non_real, refuse) -> None:
    """The shapes a uniform, truncated normal or type-I extreme-value law
    admits, as the declaration or as a component of a mixture, refused under
    the rule distribution-domain at the declaration's address: the
    declaration has one subject, real or a collection of real components,
    and no argument reads a parameter whose value is no real number.
    `non_real` maps the name of each such parameter to its declared set and
    the words naming that set's kind, `a collection` for `μ : I_J → ℝ` and
    `a product set` for `b : ℝ × ℝ`."""
    for law, named in _scalar_laws(owner):
        family = law.term.fun
        if family not in REAL_PARAMETER_FAMILIES:
            continue
        named = named or declaration_text(owner)
        if len(owner.subjects) != 1:
            refuse(
                "distribution-domain",
                owner.address,
                f"{named} has the subjects {names_text(owner.subjects)}; "
                f"`{_written_form(family)}` is the law of one real subject, or of each component "
                f"of a collection",
            )
        for argument, (letter, words) in zip(law.term.args, _PARAMETERS[family]):
            for name in sorted(_names_read(argument) or ()):
                if name in non_real:
                    declared, kind = non_real[name]
                    refuse(
                        "distribution-domain",
                        owner.address,
                        f"{named} has {words} {letter} = {to_source(argument)}, which reads the "
                        f"parameter {name}, declared on {to_source(declared)}, {kind}; "
                        f"`{_written_form(family)}` takes real numbers",
                    )


def product_law(term) -> bool:
    """Whether the law `term` of a declaration on a collection is the product
    of one scalar law over the collection's index set: a call of `LogNormal`
    or of a family in `REAL_PARAMETER_FAMILIES` with no tuple argument. A
    scalar `N` on a collection is the joint normal law, no such product."""
    return (
        isinstance(term, T.Call)
        and term.fun in (LOGNORMAL, *REAL_PARAMETER_FAMILIES)
        and not any(isinstance(argument, T.Tuple) for argument in term.args)
    )


def parameter_condition(owner) -> str | None:
    """The condition on the parameters of each uniform, truncated normal and
    type-I extreme-value law a declaration writes, as the declaration or as
    a component of a mixture, whose arguments are not all numbers: the
    sentence of the obligation `distribution-parameters-in-domain` the fold
    records, decided at the calibration by `check_family_conditions`. The
    parameters of `Uniform(a_y, b_y)` lie in the family's domain where
    a < b, with a = a_y and b = b_y, both finite. None where every such law's
    arguments are numbers, or the declaration writes none."""
    clauses = []
    for law, named in _scalar_laws(owner, declaration_identity_text):
        call = law.term
        if call.fun not in REAL_PARAMETER_FAMILIES:
            continue
        if all(numeric_value(argument, {}) is not None for argument in call.args):
            continue
        written = [
            f"{letter} = {to_source(argument)}"
            for argument, (letter, _) in zip(call.args, _PARAMETERS[call.fun])
        ]
        clauses.append(
            f"the parameters of {named or declaration_identity_text(owner)} lie in the "
            f"family's domain: " + _DOMAIN_CONDITIONS[call.fun].format(*written)
        )
    return "; ".join(clauses) or None


class MeanAndCovariance(NamedTuple):
    """The mean vector and the covariance matrix of a normal distribution:
    `means` holds n entries and `covariance` n rows of n entries, each entry
    a retained term or a number."""

    means: tuple
    covariance: tuple


class NamedMeanAndCovariance(MeanAndCovariance):
    """The law of an indexed subject whose mean and covariance are two named
    parameters, `N(μ_ε, Σ_ε)`: `means` holds the one mean term and
    `covariance` the one covariance term, their entries being the values the
    calibration binds. It unpacks as a `MeanAndCovariance`."""


def normal_mean_and_covariance(owner, indexed=False) -> MeanAndCovariance | None:
    """The mean and covariance of a normal declaration as retained terms:
    `N(μ, v)` of one shock gives ((μ,), ((v,),)); `N((μ₁, …), ((Σ₁₁, …), …))`
    of a tuple subject gives its items. For one subject that is a collection
    on an index set (`indexed`), a law written as tuples of any one size gives
    its items, and a law naming two parameters gives the named record. None
    for another family or another shape."""
    term = owner.term
    if not (isinstance(term, T.Call) and term.fun == NORMAL and len(term.args) == 2):
        return None
    mean, covariance = term.args
    n = len(owner.subjects)
    if n == 1 and indexed:
        if isinstance(mean, T.Tuple) and isinstance(covariance, T.Tuple):
            size = len(mean.items)
            if len(covariance.items) == size and all(
                isinstance(row, T.Tuple) and len(row.items) == size for row in covariance.items
            ):
                return MeanAndCovariance(
                    means=tuple(mean.items),
                    covariance=tuple(tuple(row.items) for row in covariance.items),
                )
            return None
        if isinstance(mean, T.Tuple) or isinstance(covariance, T.Tuple):
            return None
        named = all(
            isinstance(part, T.Sym) and isinstance(part.symbol, T.Constant)
            for part in (mean, covariance)
        )
        record = NamedMeanAndCovariance if named else MeanAndCovariance
        return record(means=(mean,), covariance=((covariance,),))
    if n == 1:
        if isinstance(mean, T.Tuple) or isinstance(covariance, T.Tuple):
            return None
        return MeanAndCovariance(means=(mean,), covariance=((covariance,),))
    if not (
        isinstance(mean, T.Tuple)
        and len(mean.items) == n
        and isinstance(covariance, T.Tuple)
        and len(covariance.items) == n
        and all(isinstance(row, T.Tuple) and len(row.items) == n for row in covariance.items)
    ):
        return None
    return MeanAndCovariance(
        means=tuple(mean.items), covariance=tuple(tuple(row.items) for row in covariance.items)
    )


# --- the numbers a term takes, and a term's printed form ---


def number_matrix(rows, values) -> list | None:
    """The numbers the entries of a matrix of retained terms take at `values`,
    as a list of rows, or None where some entry is not a number."""
    matrix = [[numeric_value(entry, values) for entry in row] for row in rows]
    return None if any(entry is None for row in matrix for entry in row) else matrix


def numeric_value(term, values):
    """The number a retained arithmetic term denotes when every name it reads
    is bound by `values` (parameter name → number); None otherwise. The names
    `inf` and `∞` denote infinity. A division by zero, a power that overflows
    or is not a real number, and a name bound to a boolean give None."""
    values = values or {}
    if isinstance(term, T.Number):
        return float(term.value)
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        if term.symbol.name in ("inf", "∞"):
            return math.inf
        value = values.get(term.symbol.name)
        return (
            float(value)
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        )
    if isinstance(term, T.Neg):
        inner = numeric_value(term.operand, values)
        return None if inner is None else -inner
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div)):
        left, right = numeric_value(term.left, values), numeric_value(term.right, values)
        if left is None or right is None:
            return None
        if isinstance(term, T.Add):
            return left + right
        if isinstance(term, T.Sub):
            return left - right
        if isinstance(term, T.Mul):
            return left * right
        return None if right == 0 else left / right
    if isinstance(term, T.Pow):
        base, exponent = numeric_value(term.base, values), numeric_value(term.exponent, values)
        if base is None or exponent is None:
            return None
        try:
            result = base**exponent
        except (OverflowError, ZeroDivisionError):
            return None
        return result if isinstance(result, float) else None
    return None


def _names_read(term):
    """The names an arithmetic term of numbers and named constants reads, the
    terms `numeric_value` evaluates; None where the term holds any other
    node, such as a call, a field or a selection."""
    if isinstance(term, T.Number):
        return frozenset()
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        if term.symbol.name in ("inf", "∞"):
            return frozenset()  # infinity, a number to `numeric_value`, is no name read
        return frozenset((term.symbol.name,)) if isinstance(term.symbol.name, str) else None
    if isinstance(term, T.Neg):
        return _names_read(term.operand)
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div, T.Pow)):
        parts = (term.base, term.exponent) if isinstance(term, T.Pow) else (term.left, term.right)
        left, right = (_names_read(part) for part in parts)
        return None if left is None or right is None else left | right
    return None


# the tolerance of the conditions decided from numbers, relative to the largest
# magnitude a comparison reads
RELATIVE_TOLERANCE = 1e-12


def tolerance(numbers) -> float:
    """The absolute tolerance of a comparison among `numbers`: the relative
    tolerance times the largest magnitude among them, or times one where no
    magnitude exceeds one."""
    return RELATIVE_TOLERANCE * max([1.0] + [abs(number) for number in numbers])


def smallest_eigenvalue(matrix) -> float:
    """The smallest eigenvalue of a symmetric matrix of numbers."""
    return float(numpy.linalg.eigvalsh(numpy.array(matrix, dtype=float)).min())


def drop_zeros_and_ones(term):
    """A term with each addition of zero, subtraction of zero, multiplication
    by one and division by one replaced by the other operand: `0 + x`, `x + 0`,
    `x - 0`, `1*x`, `x*1` and `x/1` are written `x`. Used for printed formulas
    only."""

    def number(node):
        return node.value if isinstance(node, T.Number) else None

    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div)):
        left, right = drop_zeros_and_ones(term.left), drop_zeros_and_ones(term.right)
        a, b = number(left), number(right)
        if isinstance(term, T.Add):
            if a == 0:
                return right
            if b == 0:
                return left
        elif isinstance(term, T.Sub):
            if b == 0:
                return left
        elif isinstance(term, T.Mul):
            if a == 1:
                return right
            if b == 1:
                return left
        elif b == 1:
            return left
        return type(term)(left, right)
    return term


# --- the weights of a label shock ---


def weighted_case(law, entries):
    """The weighted case operation Σ_j p_j · Q_j as a term, for the tuple of
    branch values `entries` read under the expectation over a label shock
    whose declared family term is `law` (the weighted case operation of
    `docs/bellman-calculus/09-branching.md` §4). None where the term gives the
    labels no weights, or a number of weights other than the number of
    entries."""
    weights = label_weights(law)
    if weights is None or len(weights) != len(entries):
        return None
    total = None
    for weight, entry in zip(weights, entries):
        summand = T.Mul(weight, entry)
        total = summand if total is None else T.Add(total, summand)
    return total


def label_weights(law):
    """The probabilities the distribution of a label shock gives the labels
    of its declared finite set, in the set's order, as written: the entries of
    `Categorical((p₁, …, pₙ))`, and `(1 − p, p)` for `Bernoulli(p)`, which
    draws the second point with probability p. None for any other family or
    form, a `Categorical` selecting a row of a matrix among them. `law` is the
    family term of a declaration."""
    if not isinstance(law, T.Call) or len(law.args) != 1:
        return None
    if law.fun == BERNOULLI:
        return (T.Sub(T.Number(1), law.args[0]), law.args[0])
    written = law.args[0]
    if (
        law.fun == CATEGORICAL
        and isinstance(written, T.Tuple)
        and not any(isinstance(item, T.Tuple) for item in written.items)
    ):
        return tuple(written.items)
    return None


# --- the words of the messages ---


def names_text(names):
    """Names as text: one name bare, several in brackets, none empty."""
    names = tuple(names)
    return names[0] if len(names) == 1 else "(" + ", ".join(names) + ")" if names else ""


def family_name(owner):
    """The family a declaration calls, or the word "declared" where its term
    is no call."""
    return owner.term.fun if isinstance(owner.term, T.Call) else "declared"


def declaration_text(owner):
    """The words naming a declaration in a refusal: its family, the normal
    family by the word `normal`, and the declaration as the file writes it,
    `the normal declaration `y ~ N(0, 1)``."""
    family = family_name(owner)
    return (
        f"the {'normal' if family == NORMAL else family} declaration "
        f"`{names_text(owner.subjects)} ~ {to_source(owner.term)}`"
    )


def declaration_identity_text(owner):
    """The words naming a declaration in the sentence of an obligation: its
    family, its identity and its subjects, `the N declaration t:distribution:y
    of y`, the form the recordings of the corpus hold."""
    return f"the {family_name(owner)} declaration {owner.identity} of {names_text(owner.subjects)}"


def _component_text(owner, component, text=declaration_text):
    """The words naming a component of a mixture declaration in a message:
    the component's family and the declaration's words, by `text`."""
    return f"the {component.fun} component of {text(owner)}"


def _counted(number):
    """A number of arguments in words."""
    return f"{number} argument" if number == 1 else f"{number} arguments"
