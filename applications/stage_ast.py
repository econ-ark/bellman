"""Functions that the structural tests of the applications use to parse a stage
file and compare its term with the term the test writes."""

import pathlib
import re
from dataclasses import fields, is_dataclass

from bellman.syntax.lower import ToAst
from bellman.syntax.lower import unlowered_parse_nodes as unlowered_parse_nodes
from bellman.syntax.parse import build_parser
from bellman.syntax.terms import (
    Annotation,
    Arrival,
    At,
    Block,
    Closed,
    Constant,
    Continuation,
    Domain,
    Interval,
    KeyValue,
    Named,
    Neg,
    Number,
    Open,
    Range,
    Role,
    Sub,
    Sym,
    Tag,
    Value,
    Variable,
)


def first_diff(a, b, path="FILE"):
    """The first place where two terms differ, as (path, left, right), and
    None where they are equal. The path names the field it is reached by,
    `FILE.items[3].annot`, so that a test says where a term written by hand
    and the parsed term part company."""
    # A term holds its children in a tuple; a written expectation may spell
    # the same children as a list, so the two sequences are compared
    # element-wise before the constructors are compared by type.
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return path, f"list of {len(a)}", f"list of {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            hit = first_diff(x, y, f"{path}[{i}]")
            if hit:
                return hit
        return None
    if type(a) is not type(b):
        return path, a, b
    if is_dataclass(a):
        for f in fields(a):
            hit = first_diff(getattr(a, f.name), getattr(b, f.name),
                             f"{path}.{f.name}")
            if hit:
                return hit
        return None
    return None if a == b else (path, a, b)


def check(actual, expected, label):
    """Assert that a parsed term equals a term written by hand, naming the
    first place where they part company."""
    hit = first_diff(actual, expected, label)
    assert hit is None, (
        f"divergence at {hit[0]}: parsed {_inline(hit[1])}"
        f" vs expected {_inline(hit[2])}")


VLU = Role(Value(0))          # !vlu


def parsed(path):
    """The lowered tree of the stage file at `path`."""
    return ToAst().transform(build_parser().parse(pathlib.Path(path).read_text(encoding="utf-8")))


def sym(name):
    """A plain occurrence of a name."""
    return Sym(Constant(name))


def at_var(name, perch):
    """An occurrence at a perch, `name[<]` or `name[>]`, for the perch class
    `perch`: a perch-indexed Variable with shift 0."""
    return Sym(Variable(name, At(perch()), 0))


def perched(name, perch):
    """An occurrence at the perch `perch`, an instance of a perch class."""
    return Sym(Variable(name, At(perch), 0))


def cntn(name):
    """A continuation occurrence, `name[>]`."""
    return at_var(name, Continuation)


def arvl(name):
    """An arrival occurrence, `name[<]`."""
    return at_var(name, Arrival)


def dom(name):
    return Domain(Named(name))


def annotation(*entries):
    return Annotation(list(entries))


def one_minus(name):
    return Sub(Number(1), sym(name))


def describes(text):
    """The `:: ["…"]` description an author writes after a declaration or an
    assignment, kept on the item's annotation slot (AMD-SG-014 §3,
    AMD-SG-017 §3)."""
    return Annotation([Tag(f'"{text}"')])


def extended_real():
    """`[-inf, inf)`: a closed lower end at minus the name `inf` and an open
    upper end at that name. Log utility is unbounded below."""
    return Domain(Interval(Range(Closed(), Neg(sym("inf")), sym("inf"), Open())))


def block(items, identifier):
    """The block of a parsed file carrying `id=<identifier>`."""
    for item in items:
        if isinstance(item, Block):
            entries = {e.key: e.value for e in item.tag.entries
                       if isinstance(e, KeyValue)}
            if entries.get("id") == identifier:
                return item
    raise AssertionError(f"no block with id={identifier}")


def run_checks(namespace, what):
    """Run each `test_` function of a module's `namespace` outside pytest,
    printing each result and the count passed, followed by `what`: the
    exit status, 1 if any failed."""
    names = [n for n, f in list(namespace.items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name in names:
        try:
            namespace[name]()
            print(f"pass  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {name}: {exc}")
    print(f"{len(names) - failed} of {len(names)} checks passed {what}")
    return 1 if failed else 0


# ── rendering ───────────────────────────────────────────────────────
_IDENT = re.compile(r"^[^\s()\[\]{},'\"]+$")   # bare unless delimiters inside


def _trimmed(node):
    vals = [getattr(node, f.name) for f in fields(node)]
    while vals and (vals[-1] is None or vals[-1] == ()):
        vals.pop()
    return vals


def _inline(node):
    if is_dataclass(node):
        vals = _trimmed(node)
        if not vals:
            return type(node).__name__
        return f"{type(node).__name__}({', '.join(_inline(v) for v in vals)})"
    if isinstance(node, (list, tuple)):
        return "[" + ", ".join(_inline(v) for v in node) + "]"
    if isinstance(node, str):
        return node if _IDENT.match(node) else repr(node)
    return repr(node)
