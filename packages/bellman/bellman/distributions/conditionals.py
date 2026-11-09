"""The conditional distribution an expectation selects from the joint
distribution of an edge, and its printed form.

`conditioning_shocks` gives the shocks an occurrence conditions on: the shocks
active in its integrand that it does not integrate, and the parents and the
other subject components of the declarations it integrates, without the shocks
integrated before it. `select_conditional` gives the `ConditionalDistribution`:
one `Factor` for each declaration of the integrated shocks, in dependency
order, each a declared conditional or the marginal or conditional of a joint
normal declaration; the declarations of conditioning shocks only, whose
densities cancel; and the declarations marginalized whole, none of whose shocks
is integrated or conditioned on and no remaining declaration reads them, so
that each integrates to one. A conditional these rules do not derive, a
posterior among them, is refused under the rule conditional-not-declared.
`check_conditioning_covariance` decides from the calibration's numbers that the
conditioning covariance block of a joint normal conditional is positive
definite. `conditional_texts` writes each factor's formula, evaluated at the
numbers where they bind every name it reads.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy

from bellman.distributions.edges import DistributionDeclaration, JointDistribution
from bellman.distributions.families import (
    declaration_text,
    MeanAndCovariance,
    drop_zeros_and_ones,
    names_text,
    normal_mean_and_covariance,
    number_matrix,
    numeric_value,
    smallest_eigenvalue,
    tolerance,
)
from bellman.syntax import terms as T
from bellman.syntax.source import to_source

# the four forms of a factor, the values of `Factor.form`
DECLARED = "declared"
MARGINAL = "marginal"
CONDITIONAL = "conditional"
CONDITIONING = "conditioning"


@dataclass(frozen=True, kw_only=True)
class Factor:
    """One owner's part in a selected conditional: `integrated` its subject
    components the occurrence integrates, `given` those it conditions on,
    `marginalized` the rest. `form` is `declared` (the declaration itself),
    `marginal` or `conditional` (of a joint normal declaration), or
    `conditioning` (a declaration of conditioning shocks only, whose density
    appears in the numerator and the denominator of the conditional density
    and cancels)."""

    owner: DistributionDeclaration
    form: str
    integrated: tuple
    given: tuple
    marginalized: tuple


@dataclass(frozen=True, kw_only=True)
class ConditionalDistribution:
    """The conditional distribution of the integrated shocks given the base
    coordinates and the conditioning shocks, selected from an edge's joint
    distribution: the factors of the integrated shocks in dependency order;
    in `conditioning_shocks`, the factors of the declarations of conditioning
    shocks only; and in `leaves`, the owners marginalized whole, none of whose
    shocks is integrated or conditioned on and none of whose shocks a remaining
    declaration reads, so that each integrates to one."""

    edge: JointDistribution
    integrated: tuple
    given: tuple
    factors: tuple
    conditioning_shocks: tuple
    leaves: tuple

    @property
    def declarations(self):
        """The owners of the factors of the integrated shocks, in dependency
        order."""
        return tuple(factor.owner for factor in self.factors)


def conditioning_shocks(edge, integrated, active, history) -> tuple:
    """The conditioning shocks of an expectation over `integrated` whose
    integrand has the active shocks `active` and the already integrated shocks
    `history`: C = ((R ∖ S) ∪ A(S)) ∖ (S ∪ H), where A(S) holds
    the shock arguments and the other subject components of the owners of S;
    in the edge's shock order."""
    S, R_, H = set(integrated), set(active), set(history)
    related = set()
    for shock in S:
        owner = edge.declaration_of(shock)
        if owner is not None:
            related |= set(owner.parents) | set(owner.subjects)
    chosen = ((R_ - S) | related) - (S | H)
    return _ordered(edge, chosen)


def select_conditional(edge, integrated, given, occurrence, refuse) -> ConditionalDistribution:
    """The conditional distribution of `integrated` given `given` and the base
    from the edge's joint distribution, where these rules derive it: declared
    conditionals and their products in dependency order, marginals and
    conditionals of a joint normal declaration, and the declarations
    marginalized whole, none of whose shocks is integrated or conditioned on
    and none of whose shocks a remaining declaration reads, so that each
    integrates to one. A shock not drawn on the edge is refused under the rule
    distribution-edge. Anything else, a posterior among them, is refused under
    the rule conditional-not-declared."""
    S, C = set(integrated), set(given)
    base = ", ".join(i.field for i in edge.base)
    stranger = [shock for shock in S if shock not in edge.shocks]
    if stranger:
        refuse(
            "distribution-edge",
            occurrence,
            f"{expectation_words(occurrence, _ordered(edge, S))} integrates "
            f"{names_text(stranger)}, which is not drawn on the edge of {edge.block!r} whose "
            f"law of motion this block substitutes; the shocks of that edge are "
            f"{names_text(edge.shocks) or 'none'}; integrate a shock in the backward block "
            f"of the edge it is drawn on",
            write=(
                f"Integrate {names_text(stranger)} in the backward block of the edge that "
                f"draws {'it' if len(stranger) == 1 else 'them'}"
            ),
        )

    def unsupported(reason):
        declarations = "; ".join(
            f"{declaration_text(owner)} at {owner.address}" for owner in edge.declarations
        )
        refuse(
            "conditional-not-declared",
            occurrence,
            f"{expectation_words(occurrence, _ordered(edge, S))} needs the distribution of "
            f"{names_text(_ordered(edge, S))} given "
            f"{names_text(_ordered(edge, C)) + ' and ' if C else ''}the source coordinates "
            f"({base}), and {reason}; the declarations of the edge of {edge.block!r} are "
            f"{declarations}. The construction selects declared conditionals, their products in "
            f"dependency order, and marginals and conditionals of a joint normal declaration; it "
            f"derives no posterior. Integrate in the order of the declarations, parents last; an "
            f"order that changes a nonlinear aggregation is a different specification, not a "
            f"repair",
            write=(
                "Integrate in the order of the declarations, parents last; an order that "
                "changes a nonlinear aggregation is a different specification, not a repair"
            ),
        )

    kept, leaves = _leaf_declarations(edge.declarations, S | C)
    factors = [_factor_of(owner, S, C, unsupported) for owner in kept]
    return ConditionalDistribution(
        edge=edge,
        integrated=_ordered(edge, S),
        given=_ordered(edge, C),
        factors=tuple(factor for factor in factors if factor.form != CONDITIONING),
        conditioning_shocks=tuple(factor for factor in factors if factor.form == CONDITIONING),
        leaves=tuple(leaves),
    )


def _leaf_declarations(owners, wanted):
    """The declarations of an edge kept in a selected conditional, and those
    marginalized whole: a declaration none of whose shocks is in `wanted` and
    none of whose shocks another kept declaration reads is removed, until no
    more is removed. Answers the two lists: the kept declarations in the
    order of `owners`, the removed ones in the order they are removed."""
    kept, leaves = list(owners), []
    changed = True
    while changed:
        changed = False
        for owner in list(kept):
            if set(owner.subjects) & wanted:
                continue
            if any(
                set(owner.subjects) & set(other.parents) for other in kept if other is not owner
            ):
                continue
            kept.remove(owner)
            leaves.append(owner)
            changed = True
    return kept, leaves


def _factor_of(owner, S, C, unsupported) -> Factor:
    """The factor of one kept declaration in the conditional of the shocks `S`
    given the shocks `C`: the declaration itself, the marginal or the
    conditional of a joint normal declaration, or a declaration of
    conditioning shocks only. A factor the rules do not derive is refused
    through `unsupported(reason)`."""
    part_S = tuple(s for s in owner.subjects if s in S)
    part_C = tuple(s for s in owner.subjects if s in C)
    rest = tuple(s for s in owner.subjects if s not in S | C)
    outside = [p for p in owner.parents if p not in S | C]
    if outside:
        unsupported(
            f"{declaration_text(owner)} is conditional on {names_text(outside)}, which is "
            f"neither integrated nor conditioned on here, so the "
            f"distribution would integrate a parent out of its child"
        )
    if rest and normal_mean_and_covariance(owner) is None:
        unsupported(
            f"{declaration_text(owner)} is a joint distribution, whose marginal in "
            f"{names_text(part_S + part_C)} is not derived"
        )
    parents_in_S = [p for p in owner.parents if p in S]
    if part_S and part_C:
        if normal_mean_and_covariance(owner) is None:
            unsupported(
                f"the conditional of {names_text(part_S)} given {names_text(part_C)} within "
                f"{declaration_text(owner)} is not derived"
            )
        if parents_in_S:
            unsupported(
                f"{declaration_text(owner)} is conditional on the integrated shock "
                f"{names_text(parents_in_S)}, so the distribution given "
                f"{names_text(part_C)} is a posterior"
            )
        return Factor(
            owner=owner, form=CONDITIONAL, integrated=part_S, given=part_C, marginalized=rest
        )
    if part_S:
        return Factor(
            owner=owner,
            form=MARGINAL if rest else DECLARED,
            integrated=part_S,
            given=(),
            marginalized=rest,
        )
    if parents_in_S:
        unsupported(
            f"the conditioning shock {names_text(part_C)} is declared by "
            f"{declaration_text(owner)} conditional on the integrated shock "
            f"{names_text(parents_in_S)}, so the distribution "
            f"of {names_text(parents_in_S)} given {names_text(part_C)} is a posterior"
        )
    return Factor(owner=owner, form=CONDITIONING, integrated=(), given=part_C, marginalized=rest)


def _ordered(edge, names):
    """The shocks `names` in the edge's shock order, those the edge does not
    draw after them in alphabetical order."""
    return tuple(s for s in edge.shocks if s in names) + tuple(
        sorted(s for s in names if s not in edge.shocks)
    )


def check_conditioning_covariance(selection, values, occurrence, refuse) -> bool:
    """The check that the conditioning covariance block Σ_CC of each
    conditional factor of `selection` is positive definite, which the
    conditional of a joint normal declaration needs because it inverts Σ_CC.
    A block whose smallest eigenvalue is not above the tolerance is refused
    under the rule conditional-not-declared, naming Σ_CC. Returns whether
    every block was decided from the numbers in `values`."""
    decided = True
    for factor in selection.factors:
        if factor.form != CONDITIONAL:
            continue
        block = _covariance_block(factor, factor.given, factor.given)
        matrix = number_matrix(block, values)
        if matrix is None:
            decided = False
            continue
        lowest = smallest_eigenvalue(matrix)
        if lowest <= tolerance(entry for row in matrix for entry in row):
            jointly = ", ".join(factor.integrated + factor.given)
            refuse(
                "conditional-not-declared",
                occurrence,
                f"{expectation_words(occurrence, factor.integrated)} needs the distribution of "
                f"{names_text(factor.integrated)} given {names_text(factor.given)} from "
                f"{declaration_text(factor.owner)}, whose covariance block of "
                f"{names_text(factor.given)}, which is {_matrix_text(block)}, is singular "
                f"(smallest eigenvalue {lowest!r}); the conditional of a joint normal declaration "
                f"requires a positive definite block for the shocks conditioned on, and no "
                f"pseudoinverse is taken; condition on shocks whose covariance block is positive "
                f"definite, or integrate them jointly, `E_{{{jointly}}}(…)`",
                write=(
                    f"Condition on shocks whose covariance block is positive definite, or "
                    f"integrate {jointly} jointly, `E_{{{jointly}}}(…)`"
                ),
            )
    return decided


def expectation_words(occurrence, integrated):
    """The words naming one expectation in a message: the shocks it integrates
    and the line it stands on, read from the occurrence's identity, or the
    occurrence as given where it carries no line."""
    line = getattr(occurrence, "address", None)
    over = f"the expectation over {names_text(integrated)}"
    return f"{over} on line {line}" if line is not None else f"{over} at {occurrence}"


# --- the printed conditional ---


def conditional_texts(selection, values=None) -> tuple[str, ...] | None:
    """The printed formula of each factor of a selection, in dependency order,
    with named parameter expressions kept; with `values` binding every name its
    mean and covariance read, the formula evaluated at those values instead,
    or None when some term is not a number."""
    texts = []
    for factor in selection.factors:
        if factor.form == DECLARED:
            text = _declared_text(factor)
        elif factor.form == MARGINAL:
            text = _marginal_text(factor, values)
        else:
            text = _conditional_text(factor, values)
        if text is None:
            return None
        texts.append(text)
    return tuple(texts)


def _declared_text(factor) -> str:
    """The declaration of a factor as it is written, with its parents after a
    bar."""
    owner = factor.owner
    conditional = f" | {names_text(owner.parents)}" if owner.parents else ""
    return f"{names_text(factor.integrated)}{conditional} ~ {to_source(owner.term)}"


def _marginal_text(factor, values) -> str | None:
    """The normal marginal of the shocks a factor integrates, written with the
    declaration's terms where `values` is None and at `values` otherwise, or
    None where some entry is not a number there."""
    left = names_text(factor.integrated)
    mean, covariance = _normal_marginal(factor, factor.integrated)
    if values is None:
        return f"{left} ~ N({_vector_text(mean)}, {_matrix_text(covariance)})"
    numbers = _numbers(mean, covariance, values)
    if numbers is None:
        return None
    return (
        f"{left} ~ N({_vector_text(numbers.means, _number_text)}, "
        f"{_matrix_text(numbers.covariance, _number_text)})"
    )


def _conditional_text(factor, values) -> str | None:
    """The normal conditional of the shocks S a factor integrates given the
    shocks C it conditions on, N(μ_S + Σ_SC Σ_CC⁻¹ (z − μ_C), Σ_SS − Σ_SC
    Σ_CC⁻¹ Σ_CS): written with the declaration's terms where `values` is None,
    and with the coefficients Σ_SC Σ_CC⁻¹ computed at `values` otherwise, or
    None where some entry is not a number there."""
    left, given = names_text(factor.integrated), names_text(factor.given)
    mean_S, cov_SS = _normal_marginal(factor, factor.integrated)
    mean_C, cov_CC = _normal_marginal(factor, factor.given)
    cov_SC = _covariance_block(factor, factor.integrated, factor.given)
    if values is None:
        cov_CS = _covariance_block(factor, factor.given, factor.integrated)
        if len(factor.integrated) == 1 and len(factor.given) == 1:
            z = T.Sym(T.Constant(factor.given[0]))
            mean = drop_zeros_and_ones(
                T.Add(mean_S[0], T.Mul(T.Div(cov_SC[0][0], cov_CC[0][0]), T.Sub(z, mean_C[0])))
            )
            variance = drop_zeros_and_ones(
                T.Sub(cov_SS[0][0], T.Div(T.Mul(cov_SC[0][0], cov_CS[0][0]), cov_CC[0][0]))
            )
            return f"{left} | {given} ~ N({to_source(mean)}, {to_source(variance)})"
        z = _vector_text(tuple(T.Sym(T.Constant(name)) for name in factor.given))
        return (
            f"{left} | {given} ~ N({_vector_text(mean_S)} + {_matrix_text(cov_SC)} "
            f"{_matrix_text(cov_CC)}^(-1) ({z} - {_vector_text(mean_C)}), "
            f"{_matrix_text(cov_SS)} - {_matrix_text(cov_SC)} {_matrix_text(cov_CC)}^(-1) "
            f"{_matrix_text(cov_CS)})"
        )
    numbers = [_numbers(mean_S, cov_SS, values), _numbers(mean_C, cov_CC, values)]
    cross = number_matrix(cov_SC, values)
    if None in numbers or cross is None:
        return None
    (m_S, s_SS), (m_C, s_CC) = numbers
    B = numpy.array(cross, dtype=float) @ numpy.linalg.inv(numpy.array(s_CC, dtype=float))
    intercept = numpy.array(m_S, dtype=float) - B @ numpy.array(m_C, dtype=float)
    covariance = numpy.array(s_SS, dtype=float) - B @ numpy.array(cross, dtype=float).T
    means = []
    for row, constant in zip(B, intercept):
        pieces = [f"{float(constant)!r}"] if float(constant) != 0.0 else []
        pieces += [
            f"{float(coefficient)!r}*{name}" for coefficient, name in zip(row, factor.given)
        ]
        means.append(" + ".join(pieces) or "0.0")
    mean_text = means[0] if len(means) == 1 else "(" + ", ".join(means) + ")"
    return f"{left} | {given} ~ N({mean_text}, {_matrix_text(covariance.tolist(), _number_text)})"


def _normal_marginal(factor, names):
    """The mean and covariance of the shocks `names` within a factor's joint
    normal declaration."""
    means = normal_mean_and_covariance(factor.owner).means
    return MeanAndCovariance(
        means=tuple(means[factor.owner.subjects.index(name)] for name in names),
        covariance=_covariance_block(factor, names, names),
    )


def _covariance_block(factor, rows, columns):
    """The block of a factor's covariance matrix whose rows are the shocks
    `rows` and whose columns are the shocks `columns`."""
    covariance = normal_mean_and_covariance(factor.owner).covariance
    r = [factor.owner.subjects.index(name) for name in rows]
    c = [factor.owner.subjects.index(name) for name in columns]
    return tuple(tuple(covariance[i][j] for j in c) for i in r)


def _numbers(mean, covariance, values):
    """A mean and covariance of terms at `values`, or None where some entry is
    not a number there."""
    m = [numeric_value(entry, values) for entry in mean]
    s = number_matrix(covariance, values)
    if None in m or s is None:
        return None
    return MeanAndCovariance(means=m, covariance=s)


def _vector_text(items, spell=to_source):
    """A vector as text, each entry written by `spell`: one entry bare,
    several in brackets."""
    return (
        spell(items[0])
        if len(items) == 1
        else "(" + ", ".join(spell(item) for item in items) + ")"
    )


def _matrix_text(rows, spell=to_source):
    """A matrix as text, each entry written by `spell`: a 1 × 1 matrix as its
    entry, another as a tuple of rows."""
    if len(rows) == 1 and len(rows[0]) == 1:
        return spell(rows[0][0])
    return (
        "(" + ", ".join("(" + ", ".join(spell(entry) for entry in row) + ")" for row in rows) + ")"
    )


def _number_text(value):
    """A number as the text of its floating-point value."""
    return repr(float(value))
