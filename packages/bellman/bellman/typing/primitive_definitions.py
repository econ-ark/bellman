"""The exact definition of each primitive operator, function and
distribution a stage file may name, with its conditions.

Notation and interpretation
---------------------------
X, Y, Z, H, D and C are formal measurable spaces, with specified sigma
algebras; L and Lout are formal subsets of the extended reals, except that
Aggregation admits an arbitrary measurable carrier L, including a product
of value carriers. No formal set name implies a real domain. Products have
product sigma algebras, subsets have trace sigma algebras, and explicit real
sets have Borel sigma algebras. Function spaces have no implicit sigma
algebra. FunctionSet means all total functions; MeasurableMapSet adds
measurability. Measures are positive.

Sup is the extended supremum, including -infinity for the empty set.
Integral is extended Lebesgue integration: the integral of a nonnegative
function is the supremum of the integrals of nonnegative simple functions
below it; the signed integral subtracts the negative-part integral from the
positive-part integral only when they are not both infinite. Guard clauses
are read in order, before a later clause uses a possibly partial expression.
Membership of a returned Lambda in MeasurableMapSet(U, Lout) requires
definedness and Lout membership at every point of U, as well as
measurability.

Three literal mathematical assignments are axiomatic bases, not providers
or numerical routines: external:exp(x) is sum(x**n/n!, n=0,1,...) on the
reals; external:Lebesgue is Lebesgue measure on the real Borel sets; and
external:counting(I)(B) is the cardinality of B for B subset of finite I.
external:pi is the usual circle constant. No other uninterpreted analytical
head is used. forall and exists are ordinary bounded quantifiers. Indicators,
measurable subsets, kernels, derivatives and inverses are defined below.

Contract
--------
Definition.coordinates declares free names. A None domain marks a formal
measurable-space parameter, not an unknown real value. Other entries give
the exact carrier of a free mathematical datum. Data references are
Sym(Constant(name)); set references are Named(name). The primitive names
and their free declarations are:

* Pullback: D, Y, L, g.
* Aggregation: D, L, Lout, Q_G, G.
* Expectation: H, Z, L, Lout, mu (mu is free only in equation 1).
* Evaluation: F, Fout (the derived and declared carriers).
* PolicyInsertion: X, C, H, pi.
* Pushforward: D, Y, g; DistributionExtension: H, Z, mu.
* Argmax: X, C, H, L, Gamma.
* Relation: W, X, C, D, F, A, h, R.
  W is an arbitrary input set; D is the set of the pairs a relation may
  admit; F is a set of joint candidate functions.

The kinds of the operator rows are the keys Pullback, Aggregation,
Expectation, Evaluation, Argmax, Pushforward, PolicyInsertion and
DistributionExtension; Argmax is keyed apart from `argmax`, the operator head
a statement writes, which names no definition here. Relation is the
definition of no kind: every row whose output is its own unknown reads it,
whatever its kind, the identification of a policy block (a Pullback) and an
Aggregation whose line holds its output in a relation or a residual system.
At the inputs w it is the set of the candidate functions f that satisfy the
relation R at every pair d the inputs admit, A(w), with f read at the point
h(w, d) of its domain. The identification `c = c[>]` reads it with A(w) the
pairs (a, x) of a saving and a value the candidate admits there,
h(w, (a, x)) the grid line at that value and R(w, (a, x), y) the truth of
y = x; a residual system reads it with A(w) the decision states, h the
identity and R the truth of the residuals equal to zero. The set may be
empty: no definition asserts that a function satisfies the relation.

Equation 0 is the defining Lambda, except that Expectation also has its
fixed-distribution section in equation 1. Later equations are existing
Condition records with structured predicates and required status.
instantiated_definition uses that section for Expectation. It substitutes free
references only; it does not apply the resulting Lambda. The parent can
replace bound input references in its body and bind the complete stage
input tuple, retaining unused inputs without evaluating them.

The named functions and distributions are limited to real exp and log,
extrema of nonempty finite real families, real partial differentiation on an
open real coordinate C with remaining coordinates Y, inverses of specified
real bijections X -> Y, scalar N(m,v) with variance v >= 0, LogNormal(m,s)
with logarithmic standard deviation s >= 0, Uniform(a,b) on [a,b] with
a < b, TruncatedNormal(m,s,l,u), the normal law of mean m and standard
deviation s > 0 conditional on [l,u] with extended-real l < u,
TruncatedLogNormal(m,s,l,u), the lognormal law whose logarithm has mean m
and standard deviation s > 0, conditional on the interval [l,u] of the draw
with 0 <= l < u, TypeIExtremeValue(m,s), the maximum type-I extreme-value
law of location m and scale s > 0, and finite probability mixtures. Zero v
or s of N and LogNormal denotes a point mass. Extrema and Mixture use
I={0,...,n-1}, n a positive integer. Mixture components are probability
measures; point_mass
gives the exact meaning of a numeric component. Multivariate normal
distributions and inverses on nonnumeric sets are outside these definitions
and must remain unresolved.

The version and structural digest belong only to PRIMITIVE_DEFINITIONS. The
module stores no stage or provenance information.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import NamedTuple

from bellman.distributions.families import (
    EXTREME_VALUE,
    LOGNORMAL,
    MIXTURE,
    NORMAL,
    TRUNCATED_LOGNORMAL,
    TRUNCATED_NORMAL,
    UNIFORM,
)
from bellman.native import predicates as P
from bellman.native.identity import Identity
from bellman.native.records import Condition, Definition, ResolvedName
from bellman.syntax import terms as T
from bellman.typing import typed_expressions as S

# --- the lookups ---


def primitive_definition(name) -> Definition | None:
    """The primitive definition `name` names, or None where it names none; a
    stage file is accepted or refused the same either way."""
    return PRIMITIVE_DEFINITIONS["definitions"].get(name)


def instantiated_definition(name, replacements):
    """The defining Lambda of the primitive definition `name`, for
    `Expectation` its section at a fixed distribution, with each free name
    replaced as `replacements` gives; the Lambda is not applied."""
    definition = PRIMITIVE_DEFINITIONS["definitions"][name]
    equation = definition.equations[1 if name == "Expectation" else 0]
    return S.substitute(equation, replacements)


# --- the table of the definitions ---


def _rules():
    definitions = (
        _pullback(),
        _aggregation(),
        _expectation(),
        _evaluation(),
        _argmax(),
        _relation(),
        _pushforward(),
        _policy_insertion(),
        _distribution_extension(),
        *_elementary(),
        _extremum("min"),
        _extremum("max"),
        _derivative(),
        _inverse(),
        _normal(NORMAL),
        _normal(LOGNORMAL),
        _uniform(),
        _truncated_normal(),
        _truncated_lognormal(),
        _extreme_value(),
        _mixture(),
    )
    version = "internal-dev-0.01"
    contents = [version, [_canonical(definition) for definition in definitions]]
    digest = sha256(
        json.dumps(contents, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode(
            "ascii"
        )
    ).hexdigest()
    return MappingProxyType(
        {
            "version": version,
            "digest": digest,
            "definitions": MappingProxyType({d.identity.field: d for d in definitions}),
        }
    )


# --- the definitions, in the table's order ---

_REAL = T.Named("\u211d")
_EXTENDED = T.Named("\u211d\u0304")
_ZERO, _ONE = T.Number(0), T.Number(1)
_INF = T.Number(float("inf"))
_BOOL = T.FiniteSet((_ZERO, _ONE))
_POSITIVE = T.Interval(T.Range(left=T.Open(), lower=_ZERO, upper=_INF, right=T.Open()))
_NONNEGATIVE = T.Interval(T.Range(left=T.Closed(), lower=_ZERO, upper=_INF, right=T.Open()))
_UNIT = T.Interval(T.Range(left=T.Closed(), lower=_ZERO, upper=_ONE, right=T.Closed()))
_LEBESGUE = T.Sym(T.Constant(Identity("external", field="Lebesgue")))


def _pullback():
    dset, yset, low = map(T.Named, ("D", "Y", "L"))
    v, d = (
        bound_variable("Pullback", "v", S.MeasurableMapSet(yset, low)),
        bound_variable("Pullback", "d", dset),
    )
    result = S.Lambda((d,), _at(_sym(v.variable), _at(_sym("g"), _sym(d.variable))))
    return _definition(
        "Pullback",
        S.Lambda((v,), result),
        coordinates=(
            ("D", None),
            ("Y", None),
            ("L", S.PowerSet(_EXTENDED)),
            ("g", S.MeasurableMapSet(dset, yset)),
        ),
        output=S.MeasurableMapSet(dset, low),
    )


def _aggregation():
    dset, low, out, qg = map(T.Named, ("D", "L", "Lout", "Q_G"))
    w, d = (
        bound_variable("Aggregation", "w", S.MeasurableMapSet(dset, low)),
        bound_variable("Aggregation", "d", dset),
    )
    args = (_at(_sym(w.variable), _sym(d.variable)), _sym(d.variable))
    result = S.Lambda((d,), _at(_sym("G"), *args))
    guard = _subset(
        w, _forall(d, P.Member(T.Tuple(args), qg)), P.Member(result, S.MeasurableMapSet(dset, out))
    )
    return _definition(
        "Aggregation",
        S.Lambda(((w.variable, guard),), result),
        coordinates=(
            ("D", None),
            ("L", None),
            ("Lout", S.PowerSet(_EXTENDED)),
            ("Q_G", S.PowerSet(T.Product((low, dset)))),
            ("G", S.FunctionSet(qg, out)),
        ),
        requirements=(
            (
                "aggregation-admissibility",
                _forall((w.variable, guard), P.Member(result, S.MeasurableMapSet(dset, out))),
            ),
        ),
        output=S.MeasurableMapSet(dset, out),
    )


def _expectation():
    name = "Expectation"
    hset, zset, low, out = map(T.Named, ("H", "Z", "L", "Lout"))
    domain = T.Product((hset, zset))
    kernel = _kernel(name, hset, zset)
    wspace = S.MeasurableMapSet(domain, low)
    p = bound_variable(name, "p", T.Product((kernel, wspace)))
    h, z = bound_variable(name, "h", hset), bound_variable(name, "z", zset)
    law = _at(_part(_sym(p.variable), 0), _sym(h.variable))
    value = _at(_part(_sym(p.variable), 1), _sym(h.variable), _sym(z.variable))
    integral = S.Integral(z, law, value)
    positive = S.Integral(z, law, _positive_part(name, value))
    negative = S.Integral(z, law, _positive_part(name, T.Neg(value)))
    exists = _forall(h, P.Or(P.Compare(positive, "<", _INF), P.Compare(negative, "<", _INF)))
    result = S.Lambda((h,), integral)
    qe = _subset(
        p,
        exists,
        _forall(h, P.Member(integral, out)),
        P.Member(result, S.MeasurableMapSet(hset, out)),
    )
    paired = S.Lambda(((p.variable, qe),), result)
    w = bound_variable(name, "w", wspace)
    pair = T.Tuple((_sym("mu"), _sym(w.variable)))
    section = _subset(w, P.Member(pair, qe))
    fixed = S.Lambda(
        ((w.variable, section),), S.substitute(paired.body, {p.variable.identity: pair})
    )
    coords = (
        ("H", None),
        ("Z", None),
        ("L", S.PowerSet(_EXTENDED)),
        ("Lout", S.PowerSet(_EXTENDED)),
        ("mu", kernel),
    )
    return _definition(
        name,
        paired,
        coordinates=coords,
        extra=(fixed,),
        requirements=(
            ("expectation-integrability", _forall((w.variable, section), P.Member(pair, qe))),
        ),
        output=S.MeasurableMapSet(hset, out),
    )


def _evaluation():
    source, target = T.Named("F"), T.Named("Fout")
    value = bound_variable("Evaluation", "f", source)
    belongs = P.Member(_sym(value.variable), target)
    return _definition(
        "Evaluation",
        S.Lambda(((value.variable, _subset(value, belongs)),), _sym(value.variable)),
        coordinates=(("F", None), ("Fout", None)),
        requirements=(("range-compatibility", belongs),),
        output=target,
    )


def _argmax():
    """The set of the measurable maximizing selections of an objective `q` on
    the graph of the feasibility correspondence `Gamma`: the policies `pi`
    with `pi(x)` in `Gamma(x)` and `q(x, pi(x)) >= q(x, c)` for every
    feasible `c`, at every state `x`. The set may be empty or hold several
    policies."""
    name = "Argmax"
    xset, cset, hset, low = map(T.Named, ("X", "C", "H", "L"))
    x, c = bound_variable(name, "x", xset), bound_variable(name, "c", cset)
    gamma = _at(_sym("Gamma"), _sym(x.variable))
    h = bound_variable(name, "h", T.Product((xset, cset)))
    graph = _subset(
        h, P.Member(_part(_sym(h.variable), 1), _at(_sym("Gamma"), _part(_sym(h.variable), 0)))
    )
    pi = bound_variable(name, "pi", S.MeasurableMapSet(xset, cset))
    policy_value = _at(_sym(pi.variable), _sym(x.variable))
    policies = _subset(pi, _forall(x, P.Member(policy_value, gamma)))
    q = bound_variable(name, "q", S.MeasurableMapSet(hset, low))
    comparison = P.Compare(
        _at(_sym(q.variable), T.Tuple((_sym(x.variable), policy_value))),
        ">=",
        _at(_sym(q.variable), T.Tuple((_sym(x.variable), _sym(c.variable)))),
    )
    candidates = _subset(
        (pi.variable, policies), _forall(x, _forall((c.variable, gamma), comparison))
    )
    return _definition(
        name,
        S.Lambda(((q.variable, _subset(q, P.Compare(hset, "=", graph))),), candidates),
        coordinates=(
            ("X", None),
            ("C", None),
            ("H", S.PowerSet(T.Product((xset, cset)))),
            ("L", S.PowerSet(_EXTENDED)),
            ("Gamma", S.FunctionSet(xset, S.PowerSet(cset))),
        ),
        output=S.PowerSet(policies),
    )


def _relation():
    """The one relation definition, read by every row whose output is its own
    unknown: at the inputs `w`, the candidate functions `f` of `F` that
    satisfy the relation `R` at every pair `d` of `D` the inputs admit,
    `A(w)`, the function read at the point `h(w, d)` of its domain,
    `{f ∈ F | ∀ d ∈ {d ∈ D | d ∈ A(w)}: R(w, d, f(h(w, d))) = 1}`. The pair
    ranges over `D` restricted by `A(w)`, so that a caller binds it to its
    own coordinates by the set `D`, as it binds the point of a Pullback. With
    `R` the truth of an equality `y = z(w, d)` it is the set of the functions
    whose pullback along `h` equals `z` on the admitted pairs, which is empty
    where two admitted pairs reach one point with different values."""
    name = "Relation"
    wset, xset, cset, pairs, candidates = map(T.Named, ("W", "X", "C", "D", "F"))
    w, f, d = (
        bound_variable(name, "w", wset),
        bound_variable(name, "f", S.MeasurableMapSet(xset, cset)),
        bound_variable(name, "d", pairs),
    )
    point = _at(_sym("h"), _sym(w.variable), _sym(d.variable))
    holds = P.Compare(
        _at(_sym("R"), _sym(w.variable), _sym(d.variable), _at(_sym(f.variable), point)),
        "=",
        _ONE,
    )
    admitted = _subset(d, P.Member(_sym(d.variable), _at(_sym("A"), _sym(w.variable))))
    result = _subset((f.variable, candidates), _forall((d.variable, admitted), holds))
    return _definition(
        name,
        S.Lambda((w,), result),
        coordinates=(
            ("W", None),
            ("X", None),
            ("C", None),
            ("D", None),
            ("F", S.PowerSet(S.MeasurableMapSet(xset, cset))),
            ("A", S.FunctionSet(wset, S.PowerSet(pairs))),
            ("h", S.FunctionSet(T.Product((wset, pairs)), xset)),
            ("R", S.FunctionSet(T.Product((wset, pairs, cset)), _BOOL)),
        ),
        output=S.PowerSet(candidates),
    )


def _pushforward():
    source, target = T.Named("D"), T.Named("Y")
    lam = bound_variable("Pushforward", "lambda", S.FiniteMeasureSet(source))
    result = _push_measure("Pushforward", source, target, _sym("g"), _sym(lam.variable))
    return _definition(
        "Pushforward",
        S.Lambda((lam,), result),
        coordinates=(("D", None), ("Y", None), ("g", S.MeasurableMapSet(source, target))),
        output=S.FiniteMeasureSet(target),
    )


def _policy_insertion():
    name = "PolicyInsertion"
    xset, cset, hset = map(T.Named, ("X", "C", "H"))
    x = bound_variable(name, "x", xset)
    pair = T.Tuple((_sym(x.variable), _at(_sym("pi"), _sym(x.variable))))
    insertion = S.Lambda((x,), pair)
    feasible = P.Member(insertion, S.MeasurableMapSet(xset, hset))
    coordinates = (
        ("X", None),
        ("C", None),
        ("H", S.PowerSet(T.Product((xset, cset)))),
        ("pi", S.MeasurableMapSet(xset, cset)),
    )
    lam = bound_variable(name, "lambda", S.FiniteMeasureSet(xset))
    result = _push_measure(name, xset, hset, insertion, _sym(lam.variable))
    return _definition(
        name,
        S.Lambda(((lam.variable, _subset(lam, feasible)),), result),
        coordinates=coordinates,
        requirements=(("feasibility", feasible),),
        output=S.FiniteMeasureSet(hset),
    )


def _distribution_extension():
    name = "DistributionExtension"
    hset, zset = T.Named("H"), T.Named("Z")
    domain = T.Product((hset, zset))
    lam, h, z = (
        bound_variable(name, "lambda", S.FiniteMeasureSet(hset)),
        bound_variable(name, "h", hset),
        bound_variable(name, "z", zset),
    )
    b = bound_variable(name, "B", measurable_sets(domain, name))
    section = _subset(z, P.Member(T.Tuple((_sym(h.variable), _sym(z.variable))), _sym(b.variable)))
    value = _at(_at(_sym("mu"), _sym(h.variable)), section)
    result = S.Measure(domain, b, S.Integral(h, _sym(lam.variable), value))
    kernel = _kernel(name, hset, zset)
    admissible = _subset(lam, P.Member(_sym("mu"), kernel))
    return _definition(
        name,
        S.Lambda(((lam.variable, admissible),), result),
        coordinates=(("H", None), ("Z", None), ("mu", kernel)),
        output=S.FiniteMeasureSet(domain),
    )


def _elementary():
    x = bound_variable("exp", "x", _REAL)
    exponential = _definition("exp", S.Lambda((x,), _exp(_sym(x.variable))), output=_POSITIVE)
    x, t = bound_variable("log", "x", _POSITIVE), bound_variable("log", "t", _REAL)
    inverse = _subset(t, P.Compare(_exp(_sym(t.variable)), "<=", _sym(x.variable)))
    logarithm = _definition(
        "log", S.Lambda((x,), S.Sup((t.variable, inverse), _sym(t.variable))), output=_REAL
    )
    return exponential, logarithm


def _extremum(name):
    indices, coords = _indices(name)
    a, i = (
        bound_variable(name, "a", S.FunctionSet(indices, _REAL)),
        bound_variable(name, "i", indices),
    )
    value = _at(_sym(a.variable), _sym(i.variable))
    result = S.Sup(i, value if name == "max" else T.Neg(value))
    return _definition(
        name,
        S.Lambda((a,), result if name == "max" else T.Neg(result)),
        coordinates=coords,
        output=_REAL,
    )


def _derivative():
    name = "D"
    cset, yset = T.Named("C"), T.Named("Y")
    domain = T.Product((cset, yset))
    f = bound_variable(name, "f", S.MeasurableMapSet(domain, _REAL))
    c, y, a = (
        bound_variable(name, "c", cset),
        bound_variable(name, "y", yset),
        bound_variable(name, "a", _REAL),
    )
    eps, delta, t = (
        bound_variable(name, "epsilon", _POSITIVE),
        bound_variable(name, "delta", _POSITIVE),
        bound_variable(name, "t", _REAL),
    )
    cv, yv, tv = _sym(c.variable), _sym(y.variable), _sym(t.variable)
    quotient = T.Div(
        T.Sub(_at(_sym(f.variable), T.Add(cv, tv), yv), _at(_sym(f.variable), cv, yv)), tv
    )
    small = _subset(
        t,
        P.Compare(_abs(tv), ">", _ZERO),
        P.Compare(_abs(tv), "<", _sym(delta.variable)),
        P.Member(T.Add(cv, tv), cset),
    )
    limit = _forall(
        eps,
        _exists(
            delta,
            _forall(
                (t.variable, small),
                P.Compare(_abs(T.Sub(quotient, _sym(a.variable))), "<", _sym(eps.variable)),
            ),
        ),
    )
    slopes = _subset(a, limit)
    result = S.Lambda((c, y), S.Sup((a.variable, slopes), _sym(a.variable)))
    neighborhood = _subset(t, P.Compare(_abs(tv), "<", _sym(delta.variable)))
    open_domain = _forall(
        c, _exists(delta, _forall((t.variable, neighborhood), P.Member(T.Add(cv, tv), cset)))
    )
    exists = _forall(c, _forall(y, _exists(a, limit)))
    guard = _subset(f, open_domain, exists, P.Member(result, S.MeasurableMapSet(domain, _REAL)))
    return _definition(
        name,
        S.Lambda(((f.variable, guard),), result),
        coordinates=(("C", S.PowerSet(_REAL)), ("Y", None)),
        requirements=(
            (
                "arithmetic-definedness",
                _forall((f.variable, guard), P.Member(result, S.MeasurableMapSet(domain, _REAL))),
            ),
        ),
        output=S.MeasurableMapSet(domain, _REAL),
    )


def _inverse():
    name = "Inv"
    xset, yset = T.Named("X"), T.Named("Y")
    f = bound_variable(name, "f", S.FunctionSet(xset, yset))
    x, other, y = (
        bound_variable(name, "x", xset),
        bound_variable(name, "other", xset),
        bound_variable(name, "y", yset),
    )
    equal = P.Compare(_at(_sym(f.variable), _sym(x.variable)), "=", _sym(y.variable))
    unique = _forall(
        other,
        P.Or(
            P.Not(P.Compare(_at(_sym(f.variable), _sym(other.variable)), "=", _sym(y.variable))),
            P.Compare(_sym(other.variable), "=", _sym(x.variable)),
        ),
    )
    bijective = _forall(y, _exists(x, P.And(equal, unique)))
    result = S.Lambda((y,), S.Sup((x.variable, _subset(x, equal)), _sym(x.variable)))
    guard = _subset(f, bijective)
    return _definition(
        name,
        S.Lambda(((f.variable, guard),), result),
        coordinates=(("X", S.PowerSet(_REAL)), ("Y", S.PowerSet(_REAL))),
        requirements=(("inverse-function-domain", _forall((f.variable, guard), bijective)),),
        output=S.FunctionSet(yset, xset),
    )


def _normal(name):
    m = bound_variable(name, "m", _REAL)
    scale = bound_variable(name, "v" if name == NORMAL else "s", _NONNEGATIVE)
    z = bound_variable(name, "z", _REAL)
    target = _REAL if name == NORMAL else _POSITIVE
    b = bound_variable(name, "B", measurable_sets(target, name))
    deviation = (
        T.Pow(_sym(scale.variable), T.Div(_ONE, T.Number(2)))
        if name == NORMAL
        else _sym(scale.variable)
    )
    affine = T.Add(_sym(m.variable), T.Mul(deviation, _sym(z.variable)))
    image = affine if name == NORMAL else _exp(affine)
    preimage = _subset(z, P.Member(image, _sym(b.variable)))
    measure = S.Measure(
        target, b, S.Integral((z.variable, preimage), _LEBESGUE, _standard_normal(z))
    )
    return _definition(name, S.Lambda((m, scale), measure), output=S.ProbabilityMeasureSet(target))


def _uniform():
    """The uniform law on [a, b]: the mass of an event B is the Lebesgue
    measure of B ∩ [a, b] divided by b − a. It is a probability measure
    exactly where a < b."""
    name = UNIFORM
    a, b = bound_variable(name, "a", _REAL), bound_variable(name, "b", _REAL)
    x = bound_variable(name, "x", _REAL)
    event = bound_variable(name, "B", measurable_sets(_REAL, name))
    low, high, point = _sym(a.variable), _sym(b.variable), _sym(x.variable)
    region = _subset(
        x,
        P.Member(point, _sym(event.variable)),
        P.Compare(low, "<=", point),
        P.Compare(point, "<=", high),
    )
    measure = S.Measure(
        _REAL, event, S.Integral((x.variable, region), _LEBESGUE, T.Div(_ONE, T.Sub(high, low)))
    )
    ordered = _subset(b, P.Compare(low, "<", high))
    admitted = _forall(
        a, _forall((b.variable, ordered), P.Member(measure, S.ProbabilityMeasureSet(_REAL)))
    )
    return _definition(
        name,
        S.Lambda((a, b), measure),
        requirements=(("distribution-parameters-in-domain", admitted),),
        output=S.ProbabilityMeasureSet(_REAL),
        domain=_admitted_arguments((a, b), P.Compare(low, "<", high)),
    )


def _truncated_normal():
    """The normal law of mean m and standard deviation s conditional on
    [l, u]: with x = m + s·z and z a standard normal coordinate, the mass of
    an event B is the standard normal mass of the z with x in B and in
    [l, u], divided by the standard normal mass of the z with x in [l, u].
    The endpoints are extended reals; the law is a probability measure
    exactly where l < u, and the normalizing mass is the denominator, not a
    number the definition computes."""
    name = TRUNCATED_NORMAL
    m, s = bound_variable(name, "m", _REAL), bound_variable(name, "s", _POSITIVE)
    low, high = bound_variable(name, "l", _EXTENDED), bound_variable(name, "u", _EXTENDED)
    z = bound_variable(name, "z", _REAL)
    event = bound_variable(name, "B", measurable_sets(_REAL, name))
    image = T.Add(_sym(m.variable), T.Mul(_sym(s.variable), _sym(z.variable)))
    inside = (
        P.Compare(_sym(low.variable), "<=", image),
        P.Compare(image, "<=", _sym(high.variable)),
    )
    preimage = _subset(z, P.Member(image, _sym(event.variable)), *inside)
    window = _subset(z, *inside)
    density = _standard_normal(z)
    measure = S.Measure(
        _REAL,
        event,
        T.Div(
            S.Integral((z.variable, preimage), _LEBESGUE, density),
            S.Integral((z.variable, window), _LEBESGUE, density),
        ),
    )
    order = P.Compare(_sym(low.variable), "<", _sym(high.variable))
    admitted = _forall(
        m,
        _forall(
            s,
            _forall(
                low,
                _forall(
                    (high.variable, _subset(high, order)),
                    P.Member(measure, S.ProbabilityMeasureSet(_REAL)),
                ),
            ),
        ),
    )
    return _definition(
        name,
        S.Lambda((m, s, low, high), measure),
        requirements=(("distribution-parameters-in-domain", admitted),),
        output=S.ProbabilityMeasureSet(_REAL),
        domain=_admitted_arguments((m, s, low, high), order),
    )


def _truncated_lognormal():
    """The lognormal law whose logarithm has mean m and standard deviation s,
    conditional on the interval [l, u] of the draw: with x = exp(m + s·z) and
    z a standard normal coordinate, the mass of an event B of (0, ∞) is the
    standard normal mass of the z with x in B and in [l, u], divided by the
    standard normal mass of the z with x in [l, u]. The lower endpoint is a
    nonnegative real and the upper an extended real; the law is a
    probability measure exactly where l < u, and the normalizing mass is the
    denominator, not a number the definition computes (AMD-SG-036 §3)."""
    name = TRUNCATED_LOGNORMAL
    m, s = bound_variable(name, "m", _REAL), bound_variable(name, "s", _POSITIVE)
    low = bound_variable(name, "l", _NONNEGATIVE)
    high = bound_variable(name, "u", _EXTENDED)
    z = bound_variable(name, "z", _REAL)
    event = bound_variable(name, "B", measurable_sets(_POSITIVE, name))
    image = _exp(T.Add(_sym(m.variable), T.Mul(_sym(s.variable), _sym(z.variable))))
    inside = (
        P.Compare(_sym(low.variable), "<=", image),
        P.Compare(image, "<=", _sym(high.variable)),
    )
    preimage = _subset(z, P.Member(image, _sym(event.variable)), *inside)
    window = _subset(z, *inside)
    density = _standard_normal(z)
    measure = S.Measure(
        _POSITIVE,
        event,
        T.Div(
            S.Integral((z.variable, preimage), _LEBESGUE, density),
            S.Integral((z.variable, window), _LEBESGUE, density),
        ),
    )
    order = P.Compare(_sym(low.variable), "<", _sym(high.variable))
    admitted = _forall(
        m,
        _forall(
            s,
            _forall(
                low,
                _forall(
                    (high.variable, _subset(high, order)),
                    P.Member(measure, S.ProbabilityMeasureSet(_POSITIVE)),
                ),
            ),
        ),
    )
    return _definition(
        name,
        S.Lambda((m, s, low, high), measure),
        requirements=(("distribution-parameters-in-domain", admitted),),
        output=S.ProbabilityMeasureSet(_POSITIVE),
        domain=_admitted_arguments((m, s, low, high), order),
    )


def _extreme_value():
    """The maximum type-I extreme-value law of location m and scale s: with
    x = m + s·z, the mass of an event B is the integral of the standard
    density exp(−z − exp(−z)) over the z with x in B. The factor 1/s of the
    density in x is the Jacobian of the substitution, so that the cumulative
    distribution is exp(−exp(−(x − m)/s))."""
    name = EXTREME_VALUE
    m, s = bound_variable(name, "m", _REAL), bound_variable(name, "s", _POSITIVE)
    z = bound_variable(name, "z", _REAL)
    event = bound_variable(name, "B", measurable_sets(_REAL, name))
    image = T.Add(_sym(m.variable), T.Mul(_sym(s.variable), _sym(z.variable)))
    preimage = _subset(z, P.Member(image, _sym(event.variable)))
    reflected = T.Neg(_sym(z.variable))
    density = _exp(T.Sub(reflected, _exp(reflected)))
    measure = S.Measure(_REAL, event, S.Integral((z.variable, preimage), _LEBESGUE, density))
    return _definition(name, S.Lambda((m, s), measure), output=S.ProbabilityMeasureSet(_REAL))


def _mixture():
    name = MIXTURE
    zset = T.Named("Z")
    indices, coords = _indices(name)
    p = bound_variable(name, "p", S.FunctionSet(indices, _UNIT))
    nu = bound_variable(name, "nu", S.FunctionSet(indices, S.ProbabilityMeasureSet(zset)))
    i = bound_variable(name, "i", indices)
    counting = T.Call(Identity("external", field="counting"), (T.Space(indices),))
    total = S.Integral(i, counting, _at(_sym(p.variable), _sym(i.variable)))
    weights = _subset(p, P.Compare(total, "=", _ONE))
    b = bound_variable(name, "B", measurable_sets(zset, name))
    summand = T.Mul(
        _at(_sym(p.variable), _sym(i.variable)),
        _at(_at(_sym(nu.variable), _sym(i.variable)), _sym(b.variable)),
    )
    result = S.Measure(zset, b, S.Integral(i, counting, summand))
    return _definition(
        name,
        S.Lambda(((p.variable, weights), nu), result),
        coordinates=(*coords, ("Z", None)),
        requirements=(
            (
                "distribution-weights-are-a-probability-vector",
                _forall((p.variable, weights), P.Compare(total, "=", _ONE)),
            ),
        ),
        output=S.ProbabilityMeasureSet(zset),
    )


def _definition(
    name, expression, *, coordinates=(), extra=(), requirements=(), output, domain=None
):
    """The definition `name` with its defining expression and conditions; its
    range compatibility is stated on `domain`, the set of the admitted
    arguments where it is smaller than the product of the bindings' sets."""
    identity = Identity("function", stage="bellman", field=name)
    if domain is None:
        domains = tuple(held for _, held in expression.bindings)
        domain = domains[0] if len(domains) == 1 else T.Product(domains)
    requirements = (
        *requirements,
        ("range-compatibility", P.Member(expression, S.FunctionSet(domain, output))),
    )
    obligations = tuple(
        Condition(code, (identity, predicate), status="required")
        for code, predicate in requirements
    )
    return Definition(
        identity=identity,
        kind="function",
        coordinates=tuple(coordinates),
        equations=(expression, *extra, *obligations),
        tags=(),
        address="",
    )


# --- the terms the definitions are built from ---


class BoundVariable(NamedTuple):
    """A variable a definition binds and the set it ranges over, the pair a
    `Lambda`, an `Integral`, a `Sup` or a `Measure` binds."""

    variable: ResolvedName
    domain: object


def bound_variable(owner, name, carrier, position=0, role="bound", perch=None):
    """A bound variable of a definition and its set: the variable is the input
    of the function-parameter identity `name` of `owner`, typed by
    `semantic_type_of(carrier)`, and the carrier stands beside it, since a
    compound carrier states more than its type. A string owner names a
    primitive definition; a stage caller gives its defining or occurrence
    identity.
    """
    if not isinstance(carrier, T.setexpr):
        raise TypeError("a binding carrier must be a structured set expression")
    if isinstance(owner, str):
        owner = Identity("function", stage="bellman", field=owner)
    identity = Identity("function-parameter", owner=owner, field=name, occurrence=position)
    return BoundVariable(
        ResolvedName(
            identity=identity, value_type=S.semantic_type_of(carrier), role=role, perch=perch
        ),
        carrier,
    )


def _at(function, *args):
    return S.Apply(function, tuple(args))


def _sym(value):
    return T.Sym(T.Constant(value.identity if isinstance(value, ResolvedName) else value))


def _subset(bound, *conditions):
    variable, domain = bound
    return T.Comprehension(T.Subject((variable,)), domain, tuple(conditions))


def _admitted_arguments(bindings, condition):
    """The arguments of a definition, bound as one point of the product of
    their sets, that satisfy `condition`."""
    return T.Comprehension(
        T.Subject(tuple(variable for variable, _ in bindings)),
        T.Product(tuple(domain for _, domain in bindings)),
        (condition,),
    )


def _forall(bound, body):
    return T.Operator("forall", (T.In(*bound),), (body,))


def _kernel(owner, domain, codomain):
    mu = bound_variable(owner, "kernel", S.FunctionSet(domain, S.ProbabilityMeasureSet(codomain)))
    b = bound_variable(owner, "kernel-set", measurable_sets(codomain, owner))
    h = bound_variable(owner, "kernel-point", domain)
    values = S.Lambda((h,), _at(_at(_sym(mu.variable), _sym(h.variable)), _sym(b.variable)))
    return _subset(mu, _forall(b, P.Member(values, S.MeasurableMapSet(domain, _UNIT))))


def measurable_sets(domain, owner):
    """The set of the measurable subsets of `domain`: the subsets whose
    indicators are measurable."""
    b = bound_variable(owner, "measurable-set", S.PowerSet(domain))
    x = bound_variable(owner, "set-point", domain)
    indicator = S.Lambda((x,), _indicator(owner, _sym(x.variable), _sym(b.variable)))
    return _subset(b, P.Member(indicator, S.MeasurableMapSet(domain, _BOOL)))


def _indicator(owner, point, subset):
    r = bound_variable(owner, "indicator-value", _BOOL)
    member = P.Member(point, subset)
    domain = _subset(
        r,
        P.Or(
            P.And(P.Compare(_sym(r.variable), "=", _ONE), member),
            P.And(P.Compare(_sym(r.variable), "=", _ZERO), P.Not(member)),
        ),
    )
    return S.Sup((r.variable, domain), _sym(r.variable))


def _part(value, index):
    return T.Select(value, T.Pos(index + 1))


def _positive_part(owner, value):
    r = bound_variable(owner, "positive-part", T.FiniteSet((_ZERO, value)))
    return S.Sup(r, _sym(r.variable))


def _push_measure(owner, source, target, function, measure):
    b = bound_variable(owner, "B", measurable_sets(target, owner))
    d = bound_variable(owner, "measure-point", source)
    preimage = _subset(d, P.Member(_at(function, _sym(d.variable)), _sym(b.variable)))
    return S.Measure(target, b, _at(measure, preimage))


def _exp(value):
    return T.Call(Identity("external", field="exp"), (value,))


def _standard_normal(z):
    """The standard normal density at the bound variable `z`,
    exp(−z²/2)/(2·pi)^(1/2)."""
    pi = _sym(Identity("external", field="pi"))
    return T.Div(
        _exp(T.Neg(T.Div(T.Pow(_sym(z.variable), T.Number(2)), T.Number(2)))),
        T.Pow(T.Mul(T.Number(2), pi), T.Div(_ONE, T.Number(2))),
    )


def _indices(name):
    n = bound_variable(name, "n", _POSITIVE)
    positive_integers = _subset(n, P.IsInteger(_sym(n.variable)))
    i = bound_variable(name, "i", _NONNEGATIVE)
    indices = _subset(
        i, P.IsInteger(_sym(i.variable)), P.Compare(_sym(i.variable), "<", _sym("n"))
    )
    return indices, (("n", positive_integers),)


def _abs(value):
    return T.Pow(T.Pow(value, T.Number(2)), T.Div(_ONE, T.Number(2)))


def _exists(bound, body):
    return T.Operator("exists", (T.In(*bound),), (body,))


def point_mass(point, domain):
    """The point mass at `point`, a probability measure on `domain`: the
    Dirac map on the domain applied to the point."""
    x = bound_variable(MIXTURE, "atom", domain)
    b = bound_variable(MIXTURE, "atom-set", measurable_sets(domain, MIXTURE))
    measure = S.Measure(domain, b, _indicator(MIXTURE, _sym(x.variable), _sym(b.variable)))
    return S.Apply(S.Lambda((x,), measure), (point,))


# --- the digest and the table ---


def _canonical(value):
    """The structural encoding of a value that the digest is computed from,
    independent of displays and provenance."""
    if is_dataclass(value):
        return [
            type(value).__name__,
            [[f.name, _canonical(getattr(value, f.name))] for f in fields(value)],
        ]
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, float) and value in (float("inf"), -float("inf")):
        return ["infinity", 1 if value > 0 else -1]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"no canonical semantic-rule encoding for {type(value).__name__}")


PRIMITIVE_DEFINITIONS = _rules()
