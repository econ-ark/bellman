"""The category codes of a named set: the marker `!categories` on a set
written as a range of integers, and the codes of a declared domain.

A named set written as a comprehension over the integers, with the marker and
one category name for each member in its annotation,

    H := {i : ℤ | i >= 0, i <= 1} :: [!categories household, newborn=0, old=1]

is the set I = {0, 1} with its category map m_I, the bijection from I onto the
categories the annotation names. `category_codes` checks the annotation and
the set and answers the map as one `records.CategoryCodes`, which the fold
keeps on the set's `Definition` as `categories`; `reserved_entries` answers
the entries the marker reserves, by which the fold refuses the marker on any
other item. `describe` writes a map as the cards and the connection reasons
print it. `coded_meaning` answers the codes of a declared domain: a
marked set's own, an unmarked named set's through its definition, a
restriction's restricted to the members its conditions keep, and a product's
factor by factor. `compared` decides whether values of one coded domain may
be copied into another.

The category named c of a set marked with the identifier κ is the pair (κ, c).
Without an identifier, κ is the pair of the stage text's SHA-256 digest and the
set's name, so that the occurrences of one text share their categories and
different texts share categories only through an identifier; equal names and
equal members establish nothing. A stage made from a term rather than a text
holds no digest, and the identity of its local categories is not established.
A category name is a string, never a term.
"""

from __future__ import annotations

import dataclasses
import itertools
import re

from bellman.native.records import CategoryCodes
from bellman.syntax import terms as T
from bellman.syntax.source import comprehension_text, to_source
from bellman.syntax.vocabulary import PRIMITIVE_SETS

MARKER = "!categories"

# A stage identifier as the grammar's terminal NAME spells it
# (`syntax/grammars/stage.lark`): a letter other than ℝ, ℕ and ℤ, then
# letters, decimal digits and `_`.
_LETTER = r"[^\W\d_\$ℝℕℤ]"
_IDENTIFIER = re.compile(rf"{_LETTER}(?:_|{_LETTER}|[0-9])*")
# A character that continues a stage identifier.
_CONTINUES = re.compile(rf"_|{_LETTER}|[0-9]")
# A code: an optional sign and decimal digits.
_CODE = re.compile(r"[+-]?[0-9]+")

# The glyphs of the two integer sets a coded range may range over.
_INTEGER_GLYPHS = ("ℤ", "ℕ")


class CategoryCodesFault(ValueError):
    """The annotation of the set `name`, marked `!categories`, fails checks of
    `category_codes`. `problems` holds one sentence for each failed check, in
    the order the checks are made, and `message` the refusal's sentence, which
    names the set and every problem."""

    def __init__(self, name, problems):
        self.name = name
        self.problems = tuple(problems)
        head = (
            f"the set {name} is marked `{MARKER}`, and its definition and its annotation give "
            f"no category map"
        )
        self.message = ". ".join((head,) + self.problems)
        super().__init__(self.message)


# --- the marker and the map of a marked set ---


def reserved_entries(annotation) -> tuple:
    """The entries of an annotation the marker reserves, in the order
    written: a tag whose text is `!categories` followed by nothing or by a
    character that cannot continue a stage identifier, and a key-value entry
    whose key is such a text. A double-quoted tag of a statement or a
    declaration keeps its quotes and reserves nothing; the lowering removes
    the quotes of a block header's tags (`syntax/lower.py`), so a quoted
    marker there is reserved. `()` where there is no annotation."""
    if annotation is None:
        return ()
    return tuple(entry for entry in annotation.entries if _reserved(entry))


def category_codes(set_term, annotation, name):
    """The category map of the set `name`, defined as `set_term` and
    annotated with `annotation`, as one `CategoryCodes`; None where the
    annotation reserves no entry, so that an unmarked set keeps its meaning.

    The annotation holds one marker, `!categories` alone or followed by
    spaces and one stage identifier, and one `name=code` entry for each member
    of the set: the name a stage identifier and the code an optional sign with
    decimal digits, read as an integer, so that `0`, `-0` and `00` are one
    code. An `id=` entry and a double-quoted description are passed over;
    every other entry is malformed. Repeated entries, names and codes are
    found by sorting the entries, before any mapping is built. The set is a
    comprehension with one binder typed by ℤ or ℕ, each condition comparing
    the binder with an integer, `k` or `-k`, by a strict or a weak
    inequality written either way round; the bounds are intersected, a
    strict bound is read as the weak bound on the next integer, both bounds
    are required, the range is not empty, and under ℕ, whose least member
    the language leaves undecided, the lower bound is at least 1. The codes
    are the members of the range [a, b] exactly when each lies in it and
    b − a + 1 of them are distinct, so no range is enumerated.

    Every failed check is named in one `CategoryCodesFault`."""
    reserved = reserved_entries(annotation)
    if not reserved:
        return None
    problems = []
    identifier = _identifier(reserved, problems)
    entries, written = _entries(annotation, problems)
    if not entries and not written:
        problems.append(
            f"The annotation writes no category; write one `name=code` entry for each member "
            f"of {name}, as in `[{MARKER}, newborn=0, old=1]`"
        )
    entries = _without_repetitions(entries, problems)
    members = _members(set_term, name, problems)
    if members is not None and entries:
        _cover(entries, members, name, problems)
    if problems:
        raise CategoryCodesFault(name, problems)
    return CategoryCodes(
        identifier, tuple(sorted((code, category) for code, category, _ in entries))
    )


def _reserved(entry) -> bool:
    """Whether an annotation entry is reserved by the marker."""
    if isinstance(entry, T.Tag):
        text = entry.tag
    elif isinstance(entry, T.KeyValue):
        text = entry.key
    else:
        return False
    return (
        isinstance(text, str)
        and text.startswith(MARKER)
        and _CONTINUES.match(text, len(MARKER)) is None
    )


def _identifier(reserved, problems):
    """The identifier the one marker writes, or None; a problem for each
    reserved entry that is not the marker, for a second marker, and for an
    identifier that is not a stage identifier."""
    markers = []
    for entry in reserved:
        if isinstance(entry, T.KeyValue):
            problems.append(
                f"The entry `{entry.key}={entry.value}` writes the marker as a key; write the "
                f"marker alone or followed by a space and one identifier, as in "
                f"`{MARKER} household_status`"
            )
            continue
        rest = entry.tag[len(MARKER) :]
        word = rest.strip(" ")
        if not rest or (rest[0] == " " and word and not re.search(r"\s", word)):
            markers.append((entry.tag, word or None))
            continue
        advice = (
            f"an annotation without brackets is one tag, so write the marker and the entries "
            f"in brackets, `:: [{MARKER}, newborn=0, old=1]`"
            if "," in rest or "=" in rest
            else f"write the marker alone or followed by a space and one identifier, as in "
            f"`{MARKER} household_status`"
        )
        other = next((c for c in rest if c.isspace() and c != " "), None)
        if other is not None:
            advice = f"it holds the character U+{ord(other):04X} where a space stands; {advice}"
        problems.append(f"The tag `{entry.tag}` is not the marker; {advice}")
    if len(markers) > 1:
        problems.append(
            f"The annotation writes the marker {len(markers)} times, "
            + _listing(f"`{tag}`" for tag, _ in markers)
            + "; write it once"
        )
    for tag, word in markers:
        if word is not None and _IDENTIFIER.fullmatch(word) is None:
            problems.append(
                f"The identifier `{word}` after `{MARKER}` is not a stage identifier, which "
                f"begins with a letter and continues with letters, digits and `_`; write one, "
                f"as in `{MARKER} household_status`"
            )
    if len(markers) != 1 or markers[0][1] is None:
        return None
    word = markers[0][1]
    return word if _IDENTIFIER.fullmatch(word) else None


def _entries(annotation, problems):
    """The well-formed category entries of a marked annotation as (code,
    name, entry as written) triples in the order written, and whether any
    category entry was written at all; a problem for each malformed entry."""
    entries, written = [], False
    for entry in annotation.entries:
        if _reserved(entry):
            continue
        if isinstance(entry, T.KeyValue):
            if entry.key == "id":
                continue
            written = True
            text = f"{entry.key}={entry.value}"
            quoted = (
                "; single quotes do not protect an entry, so write a description in double quotes"
                if text.startswith("'")
                else ""
            )
            named = isinstance(entry.key, str) and _IDENTIFIER.fullmatch(entry.key) is not None
            coded = _CODE.fullmatch(str(entry.value)) is not None
            if not named:
                problems.append(
                    f"The entry `{text}` names the category `{entry.key}`, which is not a stage "
                    f"identifier; a category name begins with a letter and continues with "
                    f"letters, digits and `_`{quoted}"
                )
            if not coded:
                problems.append(
                    f"The entry `{text}` gives the code `{entry.value}`, which is not an "
                    f"integer; a code is decimal digits with an optional sign, as in `old=1`"
                    f"{quoted if named else ''}"
                )
            if named and coded:
                entries.append((int(str(entry.value)), entry.key, text))
        elif isinstance(entry, T.Tag) and isinstance(entry.tag, str) and entry.tag.startswith('"'):
            continue
        else:
            written = True
            text = _entry_text(entry)
            quoted = (
                "; single quotes do not protect an entry, so write a description in double quotes"
                if text.startswith("'")
                else ""
            )
            problems.append(
                f"The entry `{text}` is neither a category written `name=code` nor a "
                f"description in double quotes; write each category as `name=code`{quoted}"
            )
    return entries, written


def _entry_text(entry) -> str:
    """An annotation entry as the author wrote it."""
    if isinstance(entry, T.Tag):
        return str(entry.tag)
    if entry == T.Typer(T.Marked(T.Node())):
        return "!node"
    return type(entry).__name__


def _without_repetitions(entries, problems):
    """The entries with an entry written twice kept once, and a problem for
    each entry written twice, each name given two codes and each code given
    to two names. The entries are sorted and neighbours compared, so no
    mapping is built."""
    kept = []
    for _, group in itertools.groupby(
        sorted(entries, key=lambda e: (e[0], e[1])), key=lambda e: e[:2]
    ):
        group = list(group)
        if len(group) > 1:
            texts = [text for _, _, text in group]
            problems.append(
                f"The entry `{texts[0]}` is written {len(group)} times; write it once"
                if len(set(texts)) == 1
                else "The entries "
                + _listing(f"`{text}`" for text in texts)
                + f" give the category {group[0][1]} the code {group[0][0]} "
                f"{len(group)} times; write it once"
            )
        kept.append(group[0])
    for category, group in itertools.groupby(sorted(kept, key=lambda e: e[1]), key=lambda e: e[1]):
        group = list(group)
        if len(group) > 1:
            problems.append(
                f"The category {category} is given {len(group)} codes, "
                + _listing(f"`{text}`" for _, _, text in group)
                + "; give each category one code"
            )
    for code, group in itertools.groupby(kept, key=lambda e: e[0]):
        group = list(group)
        if len(group) > 1:
            problems.append(
                f"The code {code} is given to {len(group)} categories, "
                + _listing(f"`{text}`" for _, _, text in group)
                + "; give each code one category"
            )
    order = {id(entry): place for place, entry in enumerate(entries)}
    return sorted(kept, key=lambda e: order[id(e)])


def _members(set_term, name, problems):
    """The bounds (a, b) of the integers the set `name` holds, read from
    `set_term`; None, with a problem for each failed check, where the set is
    not a range of integers written as a comprehension over ℤ or ℕ with
    integer bounds."""
    term = set_term.set if isinstance(set_term, T.Space) else set_term
    if not isinstance(term, T.Comprehension):
        problems.append(
            f"The set {name} is defined as `{_set_text(term)}`; a set with category codes is a "
            f"range of integers written as a comprehension, `{name} := "
            f"{{i : ℤ | i >= 0, i <= 1}}`"
        )
        return None
    coordinates = term.bound.coordinates if isinstance(term.bound, T.Subject) else ()
    if not (
        len(coordinates) == 1
        and isinstance(coordinates[0], T.Coordinate)
        and coordinates[0].at is None
        and not coordinates[0].classifiers
    ):
        problems.append(
            f"The comprehension `{_set_text(term)}` of {name} does not bind one name; write one "
            f"binder, as in `{{i : ℤ | i >= 0, i <= 1}}`"
        )
        return None
    binder = coordinates[0].stem
    found = len(problems)
    base = PRIMITIVE_SETS.get(term.base.name) if isinstance(term.base, T.Named) else None
    glyph = base.glyph if base is not None else None
    if glyph not in _INTEGER_GLYPHS:
        problems.append(
            f"The binder {binder} of {name} ranges over `{_set_text(term.base)}`; a set with "
            f"category codes ranges over ℤ or ℕ, as in `{{{binder} : ℤ | {binder} >= 0, "
            f"{binder} <= 1}}`"
        )
    lowers, uppers = [], []
    for condition in term.conds:
        bound = _literal_bound(condition, binder)
        if bound is None:
            problems.append(
                f"The condition `{_condition_text(condition)}` of {name} does not compare "
                f"{binder} with an integer by an inequality; each condition of a set with "
                f"category codes compares its binder with an integer by <, <=, > or >=, as in "
                f"`{binder} >= 0`"
            )
        elif bound[0] == "lower":
            lowers.append(bound[1])
        else:
            uppers.append(bound[1])
    lower = max(lowers) if lowers else None
    upper = min(uppers) if uppers else None
    if lower is None:
        least = 1 if glyph == "ℕ" else 0
        problems.append(
            f"The set {name} has no lower bound; write one, as in `{binder} >= {least}`"
        )
    if upper is None:
        problems.append(f"The set {name} has no upper bound; write one, as in `{binder} <= 1`")
    if lower is not None and upper is not None and lower > upper:
        problems.append(
            f"The bounds of {name}, {binder} >= {lower} and {binder} <= {upper}, leave no "
            f"integer; write a lower bound no greater than the upper bound"
        )
    if glyph == "ℕ" and lower is not None and lower < 1:
        problems.append(
            f"The set {name} ranges over ℕ from {lower}, and the language does not decide "
            f"whether 0 is a natural number; range over ℤ, or write a lower bound of at least 1"
        )
    return (lower, upper) if len(problems) == found else None


def _literal_bound(condition, binder):
    """The bound a condition places on the binder, `("lower", a)` for
    `binder >= a` and `("upper", b)` for `binder <= b`, a strict bound read as
    the weak bound on the next integer, the binder on either side; None where
    the condition does not compare the binder with an integer, `k` or `-k`."""
    if not isinstance(condition, T.Rel):
        return None
    relation = type(condition.op).__name__
    if _is_binder(condition.left, binder):
        value, flipped = _integer(condition.right), False
    elif _is_binder(condition.right, binder):
        value, flipped = _integer(condition.left), True
    else:
        return None
    if value is None or relation not in ("Ge", "Gt", "Le", "Lt"):
        return None
    if flipped:
        relation = {"Ge": "Le", "Gt": "Lt", "Le": "Ge", "Lt": "Gt"}[relation]
    return {
        "Ge": ("lower", value),
        "Gt": ("lower", value + 1),
        "Le": ("upper", value),
        "Lt": ("upper", value - 1),
    }[relation]


def _is_binder(term, binder) -> bool:
    """Whether a term is the binder, written bare."""
    return isinstance(term, T.Sym) and term.symbol == T.Constant(binder)


def _integer(term):
    """The integer a term writes as `k` or `-k`, k an integer literal; None for
    any other term, a decimal number included."""
    if isinstance(term, T.Neg):
        value = _integer(term.operand) if isinstance(term.operand, T.Number) else None
        return None if value is None else -value
    if isinstance(term, T.Number) and type(term.value) is int:
        return term.value
    return None


def _cover(entries, members, name, problems):
    """A problem for the codes outside the range `members`, (a, b), and for
    the members no category is given: the distinct codes inside the range
    are b − a + 1 exactly when they are all its members."""
    lower, upper = members
    outside = [text for code, _, text in entries if not lower <= code <= upper]
    if outside:
        subject = (
            f"The entry `{outside[0]}` gives a code"
            if len(outside) == 1
            else "The entries " + _listing(f"`{text}`" for text in outside) + " give codes"
        )
        problems.append(
            f"{subject} outside {name}, {_range_text(lower, upper)}; give each category a code "
            f"from {lower} to {upper}"
        )
    inside = sorted({code for code, _, _ in entries if lower <= code <= upper})
    count = upper - lower + 1
    if len(inside) == count:
        return
    first = lower
    for code in inside:
        if code != first:
            break
        first += 1
    missing = count - len(inside)
    which = (
        f"the member {first} has no category"
        if missing == 1
        else f"{missing} of its members have no category, the least of them {first}"
    )
    problems.append(
        f"The set {name} holds {_range_text(lower, upper)}, and {which}; give each member one "
        f"category"
    )


def _range_text(lower, upper) -> str:
    """The integers from `lower` to `upper`, in words."""
    return f"the integer {lower}" if lower == upper else f"the integers from {lower} to {upper}"


def _listing(items) -> str:
    """Items in a sentence: `a`, `a and b`, `a, b and c`."""
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _set_text(term) -> str:
    """A set term as `.bl` text, a comprehension written as an assignment
    writes it."""
    try:
        return comprehension_text(term) if isinstance(term, T.Comprehension) else to_source(term)
    except NotImplementedError:
        return type(term).__name__


# the signs of the relations a comprehension's condition writes
_SIGNS = {"Lt": "<", "Le": "<=", "Gt": ">", "Ge": ">=", "Eq": "="}


def _condition_text(condition) -> str:
    """A condition of a comprehension as `.bl` text, `i >= 0` or `j = 1`."""
    try:
        if isinstance(condition, T.Rel) and type(condition.op).__name__ in _SIGNS:
            sign = _SIGNS[type(condition.op).__name__]
            return f"{to_source(condition.left)} {sign} {to_source(condition.right)}"
        return to_source(condition)
    except NotImplementedError:
        return type(condition).__name__


# --- the printed form of a map ---


def describe(codes, name) -> str:
    """The printed form of the category map `codes`, a `CategoryCodes`, of the
    set `name`, which the cards and the connection reasons print:
    `0 ↦ newborn, 1 ↦ old (categories household_status)`, and
    `(categories local to HouseholdStatus)` where no identifier is written."""
    return f"{_pairs_text(codes.codes)} ({_categories_text(codes.identifier, name)})"


def _pairs_text(pairs) -> str:
    """The (code, name) pairs as `0 ↦ newborn, 1 ↦ old`; `no code` for none."""
    return ", ".join(f"{code} ↦ {category}" for code, category in pairs) or "no code"


def _categories_text(identifier, name) -> str:
    """`categories household_status` for an identifier, and `categories local
    to <set>` without one."""
    return f"categories {identifier}" if identifier is not None else f"categories local to {name}"


# --- the codes of a declared domain ---


@dataclasses.dataclass(frozen=True, slots=True)
class CodedMeaning:
    """The codes of a declared domain. `codes` holds the (code, category)
    pairs in increasing code order, each category the pair of its identity κ
    and its name: κ is the identifier written after the marker, or
    `("local", digest, set)` without one, the digest None for a stage that
    holds none. `exact` says whether the domain's members are these codes;
    where a condition of a restriction compares the binder with anything but
    an integer, the members are an undetermined part of them, `exact` is
    False, and `conditions` holds those conditions as written. `description`
    is the map as `describe` writes it, followed by those conditions, for a
    reason."""

    codes: tuple
    exact: bool
    description: str
    conditions: str = ""


def coded_meaning(term, sets, categories, digest):
    """The codes of the declared domain `term`, read before any name is
    resolved to its set: a `CodedMeaning`, a tuple of the meanings of a
    product's factors, or None for a domain without codes.

    `sets` maps each set name of the stage to its retained term,
    `categories` each marked set's name to its `CategoryCodes`, and `digest`
    is the stage text's SHA-256 digest, which keys the categories of a set
    marked without an identifier, or None for a stage that holds none. A
    marked name has its set's codes
    exactly; a name defined without a marker has the codes of its
    definition, and a chain of definitions that returns to a name has none;
    a primitive set and an undefined name have none. A product has a tuple
    of its factors' meanings, a factor that names a product a tuple in turn,
    and None where no factor has codes. A comprehension over a coded base
    has the base's codes within the bounds its literal conditions place on
    the binder, each comparing the binder with an integer by an inequality
    or an equality; these are its members exactly where every condition is
    literal, and otherwise an undetermined part of them, `exact` False. Every
    other term has none."""
    return _meaning(term, sets, categories, digest, ())


def _meaning(term, sets, categories, digest, active):
    """`coded_meaning` of a term, `active` holding the names whose definitions
    are being read."""
    if isinstance(term, T.Space):
        term = term.set
    if isinstance(term, T.Named):
        if term.name in categories:
            codes = categories[term.name]
            kappa = (
                codes.identifier if codes.identifier is not None else ("local", digest, term.name)
            )
            return CodedMeaning(
                codes=tuple((code, (kappa, category)) for code, category in codes.codes),
                exact=True,
                description=describe(codes, term.name),
            )
        if term.name in sets and term.name not in active:
            return _meaning(sets[term.name], sets, categories, digest, active + (term.name,))
        return None
    if isinstance(term, T.Product):
        factors = tuple(_meaning(f, sets, categories, digest, active) for f in term.factors)
        return factors if any(factor is not None for factor in factors) else None
    if isinstance(term, T.Comprehension) and term.base is not None:
        base = _meaning(term.base, sets, categories, digest, active)
        if base is None:
            return None
        if isinstance(base, tuple):
            return _undetermined(base, term)
        coordinates = term.bound.coordinates if isinstance(term.bound, T.Subject) else ()
        binder = (
            coordinates[0].stem
            if len(coordinates) == 1 and isinstance(coordinates[0], T.Coordinate)
            else None
        )
        bounds, others = [], []
        for condition in term.conds:
            found = None if binder is None else _restriction_bounds(condition, binder)
            if found is None:
                others.append(condition)
            else:
                bounds.extend(found)
        lower = max((value for side, value in bounds if side == "lower"), default=None)
        upper = min((value for side, value in bounds if side == "upper"), default=None)
        kept = tuple(
            (code, category)
            for code, category in base.codes
            if (lower is None or code >= lower) and (upper is None or code <= upper)
        )
        conditions = ", ".join(
            [_condition_text(condition) for condition in others]
            + ([base.conditions] if base.conditions else [])
        )
        return CodedMeaning(
            codes=kept,
            exact=base.exact and not others,
            description=_description(kept, conditions),
            conditions=conditions,
        )
    return None


def _restriction_bounds(condition, binder):
    """The bounds a condition of a restriction places on its binder: the one
    `_literal_bound` reads, or both bounds c for `binder = c` with c an
    integer; None where the condition compares the binder with no integer."""
    if isinstance(condition, T.Rel) and isinstance(condition.op, T.Eq):
        for this, other in ((condition.left, condition.right), (condition.right, condition.left)):
            if _is_binder(this, binder):
                value = _integer(other)
                return None if value is None else (("lower", value), ("upper", value))
        return None
    bound = _literal_bound(condition, binder)
    return None if bound is None else (bound,)


def _undetermined(meaning, comprehension):
    """A meaning with `exact` False, factor by factor: the members of a
    restriction of a product, whose conditions the codes of a factor do not
    decide."""
    if meaning is None:
        return None
    if isinstance(meaning, tuple):
        return tuple(_undetermined(factor, comprehension) for factor in meaning)
    conditions = ", ".join(_condition_text(condition) for condition in comprehension.conds)
    if meaning.conditions:
        conditions = f"{conditions}, {meaning.conditions}"
    return CodedMeaning(
        codes=meaning.codes,
        exact=False,
        description=_description(meaning.codes, conditions),
        conditions=conditions,
    )


def _description(codes, conditions="") -> str:
    """The description of a meaning's codes, as `describe` writes a map,
    followed by the conditions that leave its members undetermined."""
    if codes:
        kappa = codes[0][1][0]
        identifier = kappa if isinstance(kappa, str) else None
        name = None if isinstance(kappa, str) else kappa[2]
        text = (
            f"{_pairs_text((code, category[1]) for code, category in codes)} "
            f"({_categories_text(identifier, name)})"
        )
    else:
        text = _pairs_text(())
    return f"{text}, restricted by {conditions}" if conditions else text


def compared(writing, reading):
    """Whether values of a domain coded `writing` may be copied into a domain
    coded `reading`, both `CodedMeaning`, as a status and its reason: True
    when every code the writing domain may hold is a member of the reading
    domain with the same category; False when a code the writing domain holds
    exactly is no member of the reading domain or stands there for another
    category; None where the answer depends on the members of a restriction
    the conditions leave undetermined, which may be empty, and where a side
    has local categories of a stage that holds no text digest, whose identity
    is not established. The reason names both maps and the first code that
    decides the answer."""
    maps = (
        f"where the values are written, {writing.description}, and where they are read, "
        f"{reading.description}"
    )
    if not (identified(writing) and identified(reading)):
        return None, (
            f"categories without an identifier are local to a stage text, and a stage made "
            f"without a text holds no digest of one, so whether the categories of the two "
            f"sides are one is not established; write one identifier after `{MARKER}` in both: "
            f"{maps}"
        )
    read = {code: category for code, category in reading.codes}
    refused = [(code, category) for code, category in writing.codes if read.get(code) != category]
    if refused and writing.exact:
        return False, _refusal_reason(refused[0], read, writing, reading)
    if refused:
        code = refused[0][0]
        return None, (
            f"the code {code} may be a member of the domain written and is not accepted where "
            f"the values are read; the members written are undetermined and may be none: {maps}"
        )
    if not reading.exact and writing.codes:
        return None, (
            f"the members of the domain read are undetermined, so whether it holds the code "
            f"{writing.codes[0][0]} is not established: {maps}"
        )
    return True, f"every code written stands for the same category where it is read: {maps}"


def identified(meaning) -> bool:
    """Whether the identity of every category of a meaning is established:
    an identifier, or a local identity under the digest of a stage text."""
    return not any(
        isinstance(kappa, tuple) and kappa[1] is None for _, (kappa, _) in meaning.codes
    )


def _refusal_reason(refused, read, writing, reading) -> str:
    """The reason a code written is not accepted where it is read."""
    code, category = refused
    written = (
        f"where the values are written, {writing.description}, "
        f"and where they are read, {reading.description}"
    )
    if code not in read:
        return f"the code {code} is written and is no member of the domain read: {written}"
    other = read[code]
    if (
        other[1] == category[1]
        and isinstance(other[0], tuple)
        and isinstance(category[0], tuple)
        and other[0][2] == category[0][2]
    ):
        return (
            f"the code {code} stands for {category[1]} on both sides, but the categories are "
            f"local to the set {category[0][2]} of two different stage texts; write one "
            f"identifier after `{MARKER}` in both: {written}"
        )
    return (
        f"the code {code} stands for {_category_words(category)} where the values are written "
        f"and for {_category_words(other)} where they are read: {written}"
    )


def _category_words(category) -> str:
    """A category in words: `newborn of household_status`, or `newborn local
    to HouseholdStatus`."""
    kappa, name = category
    return f"{name} of {kappa}" if isinstance(kappa, str) else f"{name} local to {kappa[2]}"
