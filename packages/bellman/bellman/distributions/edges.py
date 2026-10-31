"""Where a shock is drawn.

Each authored `~` declaration is the `DistributionDeclaration` of its shocks.
`dependency_order` places a declaration after the declarations of its parents,
the shocks among its arguments. `shock_builders` gives each shock the edge of
one forward builder: the builder whose signature lists it, or else the edge of
another shock of its declaration or of a shock whose declaration reads it as an
argument.
`drawn_edges` composes `distribution_declarations`, `dependency_order` and
`shock_builders` for a stage's definitions. A `JointDistribution` is the joint
distribution of the declarations drawn on the edge of one forward builder, the
product of their conditional distributions in dependency order, and
`joint_distribution` builds it.
`factorization_obligation` writes that product as one sentence per declaration,
with the independence of the components of a declaration on a collection
whose law is the product of one scalar law.
Everything is computed from the retained `distribution` records and the
signatures of the forward builders when it is asked for; nothing is stored
beside the definitions table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from bellman.distributions.families import names_text
from bellman.native.identity import Identity, piece_identity
from bellman.syntax.source import to_source


@dataclass(frozen=True, kw_only=True)
class DistributionDeclaration:
    """An authored distribution declaration as the owner of its shocks: the
    identity of its `distribution` record, the address of the line, the shocks
    of its subject in tuple order, the family term, the shocks among its
    arguments (its parents), and all its state, control and shock arguments,
    each in order of first occurrence."""

    identity: Identity
    address: str
    subjects: tuple
    term: object
    parents: tuple
    arguments: tuple


@dataclass(frozen=True, kw_only=True)
class JointDistribution:
    """The joint distribution of the shocks drawn on the edge of one forward
    builder: the builder, its base coordinates (the identities of its source
    states, then of its controls), the shocks in declaration order, and their
    owners in dependency order, parents first. `block` is None for the joint
    distribution the fold assembles from the owners of an expectation's
    shocks where no one forward builder's edge is at hand: on the grid of a
    perch, or where no one edge draws all of those shocks."""

    block: str | None
    base: tuple
    shocks: tuple
    declarations: tuple

    def declaration_of(self, shock):
        """The owner of `shock` among the edge's owners, or None."""
        return next((owner for owner in self.declarations if shock in owner.subjects), None)


class DrawnEdges(NamedTuple):
    """The answer of `drawn_edges`: the owners in declaration order, the
    owners in dependency order, and the forward builder each shock is drawn
    on, as a mapping from shock name to builder."""

    in_file_order: tuple
    in_dependency_order: tuple
    shock_edges: dict


def drawn_edges(definitions, is_shock, listed_shocks, refuse) -> DrawnEdges:
    """The forward builder each declared shock is drawn on, with the owners of
    the shocks in declaration order and in dependency order: the one
    composition of `distribution_declarations`, `dependency_order` and
    `shock_builders` that the fold reads for the edges of its plan and
    `stage.fields()` reads for the edge it prints, so that a shock a
    declaration names is drawn on one edge by one rule. `definitions` is the
    definitions table, `is_shock(name)` decides whether an argument of a
    declaration is a shock, `listed_shocks` holds (builder, listed shock names)
    pairs in file order, and `refuse(rule, address, message)` raises the
    refusal of a cycle, a parent without a declaration, or two builders
    claiming one shock."""
    owners = distribution_declarations(definitions, is_shock)
    ordered = dependency_order(owners, refuse)
    return DrawnEdges(
        in_file_order=owners,
        in_dependency_order=ordered,
        shock_edges=shock_builders(owners, listed_shocks, refuse),
    )


def distribution_declarations(definitions, is_shock) -> tuple:
    """The owners of a definitions table in declaration order: one for each
    `distribution` record, whose single equation is the retained `Law`."""
    found = []
    for definition in definitions:
        if definition.kind != "distribution":
            continue
        law = definition.equations[0]
        arguments = tuple(name for name, _ in definition.coordinates)
        found.append(
            DistributionDeclaration(
                identity=definition.identity,
                address=definition.address,
                subjects=tuple(law.subjects),
                term=law.law,
                parents=tuple(name for name in arguments if is_shock(name)),
                arguments=arguments,
            )
        )
    return tuple(found)


def dependency_order(owners, refuse) -> tuple:
    """The owners with every parent's owner before its child, declaration order
    breaking ties. A declaration that reads one of its own subject components,
    a cycle of declarations and a parent shock no declaration owns are refused
    through `refuse(rule, address, message)`."""
    owner_of = _owners_by_shock(owners)
    for owner in owners:
        own = [parent for parent in owner.parents if parent in owner.subjects]
        if own:
            refuse(
                "distribution-dependency",
                owner.address,
                f"the distribution of {names_text(owner.subjects)} reads its own subject "
                f"component {names_text(own)} as an argument; a declaration is a conditional "
                f"distribution of its subject given its other arguments, so the dependency "
                f"between declarations is acyclic (AMD-SG-009 §2, rule distribution-dependency); "
                f"declare that component's distribution separately, or write the joint "
                f"distribution without it as an argument",
            )
        for parent in owner.parents:
            if parent not in owner_of:
                refuse(
                    "name-in-scope",
                    owner.address,
                    f"the distribution of {names_text(owner.subjects)} reads the shock {parent}, "
                    f"which no distribution declaration owns; every shock has exactly one "
                    f"declared distribution (AMD-SG-009 §2); declare `{parent} ~ …`",
                )
    ordered, placed, remaining = [], set(), list(owners)
    while remaining:
        ready = [
            owner
            for owner in remaining
            if all(owner_of[parent].identity in placed for parent in owner.parents)
        ]
        if not ready:
            cycle = ", ".join(
                f"{owner.identity} (at {owner.address}) reads {names_text(owner.parents)}"
                for owner in remaining
            )
            refuse(
                "distribution-dependency",
                remaining[0].address,
                f"the distribution declarations form a cycle: {cycle}; the joint distribution of "
                f"an edge is the product of declared conditional distributions in a dependency "
                f"order, which a cycle does not have (AMD-SG-009 §§2–3, rule "
                f"distribution-dependency); remove one of the shock arguments, or write the "
                f"dependent shocks as one joint declaration",
            )
        ordered.append(ready[0])
        placed.add(ready[0].identity)
        remaining.remove(ready[0])
    return tuple(ordered)


def shock_builders(owners, listed_shocks, refuse) -> dict:
    """The forward builder each shock is drawn on, as a mapping from shock
    name to builder: first every shock a forward builder's signature lists,
    then, until nothing changes, the other subject components of an assigned
    shock's declaration and the shock arguments of that declaration.
    `listed_shocks` holds (builder, listed shock names) pairs in file order.
    Two builders claiming one shock are refused under the rule
    distribution-edge, and so is a declaration whose shocks would be drawn on
    two edges."""
    owner_of = _owners_by_shock(owners)
    edge, reason = {}, {}
    for block, listed in listed_shocks:
        for shock in listed:
            if shock in edge and edge[shock] != block:
                owner = owner_of.get(shock)
                refuse(
                    "distribution-edge",
                    owner.address if owner else block,
                    f"the shock {shock} is listed by the forward builders {edge[shock]!r} and "
                    f"{block!r}; a shock is drawn on one edge, the edge of the one forward "
                    f"builder whose signature lists it (AMD-SG-009 §2, rule distribution-edge); "
                    f"list it on one forward builder",
                )
            edge.setdefault(shock, block)
            reason.setdefault(shock, f"listed by {block!r}")
    pending = list(edge)
    while pending:
        shock = pending.pop(0)
        owner = owner_of.get(shock)
        if owner is None:
            continue
        for other in owner.subjects + owner.parents:
            why = (
                f"a component of the declaration of {names_text(owner.subjects)}"
                if other in owner.subjects
                else f"an argument of the declaration of {names_text(owner.subjects)}"
            )
            if other in edge:
                if edge[other] != edge[shock]:
                    refuse(
                        "distribution-edge",
                        owner.address,
                        f"the shock {other} is drawn on the edge of {edge[other]!r} "
                        f"({reason[other]}) and is also {why} ({owner.identity}), whose shock "
                        f"{shock} is drawn on the edge of {edge[shock]!r} ({reason[shock]}); "
                        f"connected declarations are drawn on one edge (AMD-SG-009 §2, rule "
                        f"distribution-edge); list the connected shocks on one forward builder",
                    )
                continue
            edge[other] = edge[shock]
            reason[other] = f"{why}, whose shock {shock} is {reason[shock]}"
            pending.append(other)
    return edge


def _owners_by_shock(owners):
    """Each shock's owner, as a mapping from shock name to owner."""
    return {shock: owner for owner in owners for shock in owner.subjects}


def joint_distribution(
    *, block, base, in_file_order, in_dependency_order, shock_edges
) -> JointDistribution:
    """The joint distribution of the edge of forward builder `block`: its base
    coordinates, its shocks in declaration order and its owners in
    dependency order. `in_file_order`, `in_dependency_order` and
    `shock_edges` are the three parts of the answer of `drawn_edges`."""
    shocks = tuple(
        shock
        for owner in in_file_order
        for shock in owner.subjects
        if shock_edges.get(shock) == block
    )
    return JointDistribution(
        block=block,
        base=tuple(base),
        shocks=shocks,
        declarations=tuple(
            owner for owner in in_dependency_order if any(s in shocks for s in owner.subjects)
        ),
    )


def factorization_obligation(edge, base_names, products=frozenset()) -> tuple[str, tuple, str]:
    """The obligation that the edge's joint distribution is the product of its
    declared conditionals, as the fold records an obligation: its name,
    `joint-distribution-factorization`, the identities it concerns and its
    sentence. The identities are the owners in dependency order and the
    builder. Independence is stated only among owners without parents, and
    never between the components of one joint declaration, except for an
    owner in `products`, the identities of the declarations on a collection
    whose law is the product of one scalar law: its components are stated
    independent, conditionally on the declaration's arguments where it reads
    any, each with that law."""
    given = f"({', '.join(base_names)})" if base_names else "the source coordinates"
    parts = []
    for owner in edge.declarations:
        condition = f"{names_text(owner.parents)} and {given}" if owner.parents else given
        parts.append(f"{names_text(owner.subjects)} given {condition} by {owner.identity}")
    explanation = (
        f"The joint distribution for {edge.block} is assumed to be the product of the declared "
        "conditional distributions given their named parents and the source coordinates: "
        + "; ".join(parts)
    )
    roots = [owner for owner in edge.declarations if not owner.parents]
    if len(roots) > 1:
        names = [names_text(owner.subjects) for owner in roots]
        listed = ", ".join(names[:-1]) + " and " + names[-1]
        explanation += f"; {listed} are conditionally independent given {given}"
    for owner in edge.declarations:
        if owner.identity in products:
            # the components of a product law are independent draws of one
            # scalar law, conditionally on the arguments the law reads
            independence = (
                f"conditionally independent given {names_text(owner.arguments)}"
                if owner.arguments
                else "independent"
            )
            explanation += (
                f"; the components of {names_text(owner.subjects)} are {independence}, each "
                f"with the law {to_source(owner.term)}"
            )
    return (
        "joint-distribution-factorization",
        tuple(owner.identity for owner in edge.declarations) + (piece_identity(edge.block),),
        explanation + ".",
    )
