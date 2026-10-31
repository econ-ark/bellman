"""The predicate records: the conditions under which a retained equation is
read.

A condition is a membership of a retained expression in a retained set, a
comparison, a negation, a conjunction, a disjunction, an integrality
statement, or a relation held with its bound. A predicate is an immutable
value, held among the entries of a condition (`records.Condition`)
and as the statement of a card's rule.

A predicate holds no printed text. `typing.typed_expressions.predicate_text`
writes the sentence a card prints for it.
"""

from dataclasses import dataclass


class Predicate:
    """The base of the predicate records, which holds no field."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Member(Predicate):
    """`subject ∈ set`: a retained expression lies in a retained set."""

    subject: object  # a retained expression
    set: object  # a retained set expression


@dataclass(frozen=True, slots=True)
class Compare(Predicate):
    """`left relation right`: a comparison of two retained expressions."""

    left: object
    relation: str  # one of < <= = >= >
    right: object


@dataclass(frozen=True, slots=True)
class Not(Predicate):
    """The negation of a predicate."""

    operand: Predicate


@dataclass(frozen=True, slots=True)
class And(Predicate):
    """The conjunction of two predicates."""

    left: Predicate
    right: Predicate


@dataclass(frozen=True, slots=True)
class Or(Predicate):
    """The disjunction of two predicates."""

    left: Predicate
    right: Predicate


@dataclass(frozen=True, slots=True)
class IsInteger(Predicate):
    """The statement that a retained expression takes integer values."""

    operand: object


@dataclass(frozen=True, slots=True)
class Complementarity(Predicate):
    """A relation and its bound held together, `core ⟂ bound`. `core` is the
    relation read at a point, a `Compare`, or a `Member` for a maximization.
    `bound` is the bound read at the same point, a `Rel` or a `Between` of
    the terms. The condition the pair states is
    `term_operations.kuhn_tucker(core, bound)`."""

    core: Predicate
    bound: object
