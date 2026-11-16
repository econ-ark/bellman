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

from dataclasses import dataclass, field
from typing import NamedTuple

from bellman.distributions.families import declaration_text, names_text
from bellman.native.identity import Identity, piece_identity
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.walk import nodes


@dataclass(frozen=True, kw_only=True)
class DistributionDeclaration:
    """An authored distribution declaration as the owner of its shocks: the
    identity of its `distribution` record, the address of the line, the shocks
    of its subject in tuple order, the family term, the shocks among its
    arguments (its parents), and all its state, control and shock arguments,
    each in order of first occurrence. A derived numerical declaration also
    holds any supplied values its term still reads, as (name, value, declared
    set) triples in binding order."""

    identity: Identity
    address: str
    subjects: tuple
    term: object
    parents: tuple
    arguments: tuple
    formals: tuple = ()
    actuals: tuple = ()
    bindings: tuple = field(default=(), hash=False)


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
    pairs in file order, and `refuse(rule, address, message, related=(),
    write=None)` raises the refusal of a cycle, a parent without a
    declaration, or two builders claiming one shock, `related` pairing a role
    with the address of each second item the sentence names and `write` the
    action."""
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
                formals=law.arguments if isinstance(law, T.ParameterizedLaw) else (),
            )
        )
    return tuple(found)


def shock_application(term, formals):
    """The name and arguments of one use of a parameterized shock."""
    if isinstance(term, T.Call) and term.fun in formals:
        return term.fun, term.args
    if (
        isinstance(term, T.Select)
        and isinstance(term.family, T.Sym)
        and isinstance(term.family.symbol, T.Constant)
        and term.family.symbol.name in formals
    ):
        if isinstance(term.sel, T.Key):
            return term.family.symbol.name, (T.Sym(T.Constant(term.sel.at)),)
        if isinstance(term.sel, T.Term):
            return term.family.symbol.name, (term.sel.at,)
    return None


def law_arguments(formals, edges, lines, resolve_constant, refuse):
    """The ordered external constant identities supplied to each shock's law."""
    if not formals:
        return {}
    actuals = {}
    for block, address, statement in lines:
        for term in nodes(statement):
            use = shock_application(term, formals)
            if use is None:
                continue
            shock, arguments = use
            edge = edges.get(shock)
            if block != edge:
                refuse(
                    "distribution-edge",
                    address,
                    f"{to_source(term)} gives arguments for {shock}, whose forward edge is "
                    f"{edge or 'undeclared'}. Write its arguments on the edge that draws it.",
                )
            if len(arguments) != len(formals[shock]):
                refuse(
                    "distribution-domain",
                    address,
                    f"{to_source(term)} supplies {len(arguments)} arguments for {shock}. "
                    f"Its law takes {len(formals[shock])}.",
                )
            fields = tuple(resolve_constant(argument, block, address) for argument in arguments)
            if any(field is None for field in fields):
                refuse(
                    "distribution-domain",
                    address,
                    f"{to_source(term)} must give {shock} incoming constant fields "
                    f"listed by {block}.",
                )
            written = tuple(to_source(argument) for argument in arguments)
            if shock in actuals:
                previous, first, first_address = actuals[shock]
                if fields != previous:
                    refuse(
                        "distribution-edge",
                        address,
                        f"{shock} uses both ({', '.join(first)}) and ({', '.join(written)}) "
                        f"on {block}. One draw has one ordered argument tuple.",
                        related=(("first use", first_address),),
                    )
            else:
                actuals[shock] = fields, written, address
    return {name: fields for name, (fields, _, _) in actuals.items()}


def dependency_order(owners, refuse) -> tuple:
    """The owners with every parent's owner before its child, declaration order
    breaking ties. A declaration that reads one of its own subject components,
    a cycle of declarations and a parent shock no declaration owns are refused
    through `refuse(rule, address, message, related=(), write=None)`; a cycle names the
    other declarations of the cycle as related items under the role
    `dependency`."""
    owner_of = _owners_by_shock(owners)
    for owner in owners:
        own = [parent for parent in owner.parents if parent in owner.subjects]
        if own:
            refuse(
                "distribution-dependency",
                owner.address,
                f"{declaration_text(owner)} reads its own subject component "
                f"{names_text(own)} as an argument; a declaration is a conditional "
                f"distribution of its subject given its other arguments, so the dependency "
                f"between declarations is acyclic; declare that component's distribution "
                f"separately, or write the joint distribution without it as an argument",
                write=(
                    f"Declare the distribution of {names_text(own)} separately, or write the "
                    f"joint distribution without {names_text(own)} as an argument"
                ),
            )
        for parent in owner.parents:
            if parent not in owner_of:
                refuse(
                    "name-in-scope",
                    owner.address,
                    f"the distribution of {names_text(owner.subjects)} reads the shock {parent}, "
                    f"which no distribution declaration owns; every shock has exactly one "
                    f"declared distribution",
                    write=f"Declare `{parent} ~ …`",
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
                f"`{names_text(owner.subjects)} ~ {to_source(owner.term)}` reads "
                f"{names_text(owner.parents)}"
                for owner in remaining
            )
            jointly = ", ".join(name for owner in remaining for name in owner.subjects)
            refuse(
                "distribution-dependency",
                remaining[0].address,
                f"the distribution declarations form a cycle: {cycle}; the joint distribution of "
                f"an edge is the product of the declared conditional distributions in a "
                f"dependency order, which a cycle does not have; remove one of the shock "
                f"arguments, or declare the dependent shocks jointly, such as "
                f"`({jointly}) ~ N(…)`",
                related=tuple(("dependency", owner.address) for owner in remaining[1:]),
                write=(
                    f"Remove one of the shock arguments, or declare {jointly} jointly, such as "
                    f"`({jointly}) ~ N(…)`"
                ),
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
    listed_shocks = list(listed_shocks)
    # the shocks a forward block's header lists, which a move from one block
    # to another can carry; a shock drawn on an edge through its declaration
    # alone stands on no header
    on_a_header = {shock for _, listed in listed_shocks for shock in listed}
    for block, listed in listed_shocks:
        for shock in listed:
            if shock in edge and edge[shock] != block:
                owner = owner_of.get(shock)
                refuse(
                    "distribution-edge",
                    owner.address if owner else block,
                    f"the shock {shock} is listed on the headers of the forward blocks "
                    f"{edge[shock]!r} and {block!r}; a shock is drawn on one edge, the edge of "
                    f"the one forward block whose header lists it; remove {shock} from the "
                    f"header and from the lines of one of the two blocks, which changes the law "
                    f"of motion of that block",
                    write=(
                        f"Remove {shock} from the header and from the lines of block "
                        f"{edge[shock]!r} or of block {block!r}, which changes the law of motion "
                        f"of that block"
                    ),
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
                    # the moves that pass: a shock is moved from the header
                    # and the lines of the block that lists it, so a shock no
                    # header lists is offered no move
                    moves = ", or ".join(
                        f"{moved} from the header and the lines of block {edge[moved]!r} "
                        f"to those of block {edge[kept]!r}"
                        for moved, kept in ((other, shock), (shock, other))
                        if moved in on_a_header
                    )
                    refuse(
                        "distribution-edge",
                        owner.address,
                        f"the shock {other} is drawn on the edge of {edge[other]!r} "
                        f"({reason[other]}) and is also {why}, whose shock "
                        f"{shock} is drawn on the edge of {edge[shock]!r} ({reason[shock]}); "
                        f"connected declarations are drawn on one edge; list the connected "
                        f"shocks on one forward block, by moving the listing and the reads "
                        f"of one of them to the header and the lines of the other's block, "
                        f"which changes the law of motion of each of the two blocks",
                        write=(
                            f"Move {moves}, which changes the law of motion of each of the two "
                            f"blocks"
                            if moves
                            else None
                        ),
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
