"""The method table, `METHOD_TYPES`: one row per method word, the one place a
method is named (AMD-SG-005 §4; AMD-SG-006 §4; specification 0.7 §5). The
page `docs/Bellman-Sym/reference/methods.md` is printed from `METHOD_TYPES`
and from `GRID_CONSTRUCTORS` of `stage/grids.py`: one entry for each method
word, then one for each grid constructor.

The rows of the methods that name no representation family, the record of a
row and what each of its columns states stand in `stage/method_rows.py`. The
function representations, `!Linear`, `!pchip` and `!closed_form` among them,
are no rows there: each is a family of the registry of
`stage/representations.py`, and `METHOD_TYPES` reads the registry each time
it is read, one row per registered family built by `family_row` where the
representations stand, so that a family registered later has its row and a
family removed has none (AMD-MT-003 build contract §3). The rows stand below
the registry, which reads them, and this table stands above both.

A hyphenated word keeps its tag, `gauss-hermite`, and is written in a stage
file with an underscore, `!gauss_hermite`, which `row_of` reads as the same
word; no other alias exists.
"""

from collections.abc import Mapping

from bellman.stage.method_rows import ROWS_AFTER, ROWS_BEFORE, family_row
from bellman.stage.representations import families

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


# --- the table ---


class _MethodTable(Mapping):
    """The method table, `METHOD_TYPES`, as a read-only mapping from each tag
    to its row: the solution methods of a builder, then one row for each
    family the registry of `stage/representations.py` holds when the table
    is read, in registration order, then every other method (AMD-MT-003
    build contract §3). A family's word names no row of
    `stage/method_rows.py`, which `representations.register` refuses."""

    def __getitem__(self, tag):
        row = ROWS_BEFORE.get(tag) or ROWS_AFTER.get(tag)
        if row is not None:
            return row
        family = families().get(tag) if isinstance(tag, str) else None
        if family is None:
            raise KeyError(tag)
        return family_row(family)

    def __iter__(self):
        yield from ROWS_BEFORE
        yield from (word for word in families() if word not in ROWS_BEFORE)
        yield from (tag for tag in ROWS_AFTER if tag not in families())

    def __len__(self):
        return sum(1 for _ in self)

    def __str__(self):
        return "\n".join(self)

    __repr__ = __str__


METHOD_TYPES = _MethodTable()


class _MethodTypes(Mapping):
    """The one method table, `METHOD_TYPES`, as a read-only mapping, each
    row read by its tag with its `!`, `method_types["!egm"]`, or by the
    underscore spelling of a hyphenated tag; a representation family that
    `bellman.stage.representations.register` adds is listed and read by its
    tag as the package's own rows are."""

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
