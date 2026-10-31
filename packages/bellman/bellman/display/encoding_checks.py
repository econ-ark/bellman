"""The check of a Bellman-SYM stage encoding, read as plain JSON, against the
one schema, `stage-encoding-2.6.schema.json` beside this module
(`validate_encoding`), and the operator rows an encoding holds (`operators`).
The kinds it names, `terms.Operator`, `records.Condition`, are the
schema's kinds and name no module of the package; the module imports nothing
of the package, so that a second tool can run it alone."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import namedtuple
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

# --- the check of an encoding ---


def validate_encoding(document):
    """The encoding, unchanged, once it has been checked: against the schema;
    the category map a stored definition writes, on a set alone; the
    identities of its bundles against one another; each value tree against
    the schema's kinds and the scopes around it; and the wiring of each
    graph. A `ValueError` naming the place and the fault otherwise."""
    schema = _schema()
    try:
        Draft202012Validator(schema).validate(document)
    except ValidationError as error:
        location = "/".join(str(part) for part in error.absolute_path)
        message = f"schema {error.validator} check failed"
        raise ValueError(f"{location}: {message}" if location else message) from None
    for index, entry in enumerate(document["definitions"]):
        if "categories" in entry:
            path = ("definitions", index, "categories")
            if entry["kind"] != "set":
                _fail(f"a {entry['kind']} writes no category map", path)
            _check_category_map(
                entry["categories"]["identifier"], entry["categories"]["codes"], path
            )
    identities = {}
    bundles = tuple(_bundles(document))
    for path, bundle in bundles:
        for index, entry in enumerate(bundle["identities"]):
            identity = entry["id"]
            previous = identities.setdefault(identity, entry["fields"])
            if previous != entry["fields"]:
                _fail(
                    f"document identity {identity!r} has conflicting fields",
                    (*path, "identities", index),
                )
    tables = _TreeTables(identities=identities, constructors=schema["x-constructors"])
    for path, bundle in bundles:
        for index, entry in enumerate(bundle["identities"]):
            for name, value in entry["fields"].items():
                _check_tree(value, (), tables, (*path, "identities", index, "fields", name))
        _check_tree(bundle["value"], (), tables, (*path, "value"))
    _validate_graphs(document)
    return document


_SCHEMA_PATH = Path(__file__).with_name("stage-encoding-2.6.schema.json")


@lru_cache(maxsize=1)
def _schema():
    """The schema beside this module, read once and checked as a JSON Schema of
    draft 2020-12."""
    with _SCHEMA_PATH.open(encoding="utf-8") as source:
        schema = json.load(source)
    Draft202012Validator.check_schema(schema)
    return schema


def _bundles(document):
    """Each bundle of the encoding's derived answers, a value and the
    identities it refers to, with its place in the document: the stage's, the
    two initial diagrams', each definition's, and the primitives' of the two
    directions."""
    derived = document["derived"]
    yield ("derived", "stage"), derived["stage"]
    for direction in ("backward", "forward"):
        yield ("derived", "initial_diagrams", direction), derived["initial_diagrams"][direction]
    for index, bundle in enumerate(derived["definitions"]):
        yield ("derived", "definitions", index), bundle
    for direction in ("backward", "forward"):
        yield ("derived", "primitives", direction), derived["primitives"][direction]


# --- the check of a value tree ---


# The two tables a value tree is checked against: the fields of each document
# identity the encoding defines, and the fields of each kind the schema lists.
_TreeTables = namedtuple("_TreeTables", "identities constructors")


def _check_tree(tree, frames, tables, path=()):
    """The check of one value tree and of every tree inside it, by the form of
    each node: a node with fields, a scoped node, a reference, a mapping or a
    set. `frames` holds the number of variables each enclosing scope binds,
    the innermost last; `path` is the place of `tree` in the document, which a
    refusal names."""
    if tree is None or isinstance(tree, (bool, int, str)):
        return
    if isinstance(tree, float):
        if not math.isfinite(tree):
            _fail("non-finite numbers use the explicit float form", path)
        return
    if isinstance(tree, list):
        for index, item in enumerate(tree):
            _check_tree(item, frames, tables, (*path, index))
    elif "node" in tree and "fields" in tree:
        _check_fields(tree, frames, tables, path)
    elif "node" in tree:
        _check_scope(tree, frames, tables, path)
    elif "ref" in tree:
        _check_reference(tree, frames, tables, path)
    elif "mapping" in tree:
        for index, pair in enumerate(tree["mapping"]):
            _check_tree(pair[0], frames, tables, (*path, "mapping", index, 0))
            _check_tree(pair[1], frames, tables, (*path, "mapping", index, 1))
    elif "set" in tree:
        for index, value in enumerate(tree["set"]):
            _check_tree(value, frames, tables, (*path, "set", index))


def _check_fields(tree, frames, tables, path):
    """A node with fields: the fields its kind lists in the schema, the
    record checks of its kind, an unscoped operator's head and subscripts, and
    each field's tree."""
    node = tree["node"]
    expected = set(tables.constructors[node])
    actual = set(tree["fields"])
    if actual != expected:
        _fail(f"{node} fields are {sorted(actual)}; expected {sorted(expected)}", path)
    fields = tree["fields"]
    _check_record_fields(node, fields, path)
    if node == "terms.Operator":
        _check_unscoped_operator(fields, path)
    for name, value in fields.items():
        _check_tree(value, frames, tables, (*path, "fields", name))


def _check_record_fields(node, fields, path):
    """The evidence of a condition, which is textual records; the
    declarations of a typed answer, which are pairs of a document or
    unresolved reference and a carrier; and a category map
    (`_check_category_map`)."""
    if node == "records.Condition":
        evidence = fields["evidence"]
        if not isinstance(evidence, list) or any(
            not isinstance(item, dict) or set(item) != {"textual"} for item in evidence
        ):
            _fail("Condition evidence must contain textual records", (*path, "fields", "evidence"))
    if node == "records.WireType":
        declarations = fields["declarations"]
        if not isinstance(declarations, list):
            _fail("WireType declarations must be pairs", (*path, "fields", "declarations"))
        for index, pair in enumerate(declarations):
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or not isinstance(pair[0], dict)
                or pair[0].get("ref") not in ("document", "unresolved")
            ):
                _fail(
                    "a declaration must be [document or unresolved reference, carrier]",
                    (*path, "fields", "declarations", index),
                )
    if node == "records.CategoryCodes":
        _check_category_map(fields["identifier"], fields["codes"], (*path, "fields"))


def _check_category_map(identifier, codes, path):
    """A category map as `records.CategoryCodes` admits one: the identifier a
    nonempty string or null, and at least one pair of an integer code and a
    nonempty name, the codes increasing strictly and the names distinct. The
    schema's JSON types admit `1.0` as an integer and say nothing of order or
    repetition, so the record's checks are made here."""
    if identifier is not None and (not isinstance(identifier, str) or not identifier):
        _fail(
            "a category map's identifier must be a nonempty string or null", (*path, "identifier")
        )
    if (
        not isinstance(codes, list)
        or not codes
        or any(
            not isinstance(pair, list)
            or len(pair) != 2
            or type(pair[0]) is not int
            or not isinstance(pair[1], str)
            or not pair[1]
            for pair in codes
        )
    ):
        _fail("a category map's codes must be [integer, name] pairs", (*path, "codes"))
    numbers = [code for code, _ in codes]
    if any(first >= second for first, second in zip(numbers, numbers[1:])):
        _fail("a category map's codes must increase strictly", (*path, "codes"))
    if len({name for _, name in codes}) != len(codes):
        _fail("a category map's names must be distinct", (*path, "codes"))


def _check_scope(tree, frames, tables, path):
    """A scoped node: its arity and shape, a scoped operator's head, and its
    trees, the bindings and domains of an operator each in the scope of the
    variables bound before it, the bodies and the shape in the scope of all
    its variables."""
    _scope_arity(tree, path)
    _validate_shape(tree, path)
    if tree["node"] == "terms.Operator":
        _scoped_operator(tree, path)
        _check_tree(tree["outside"][0], frames, tables, (*path, "outside", 0))
        for index, (binding, domain) in enumerate(zip(tree["bindings"], tree["outside"][1:])):
            partial = (*frames, index)
            _check_tree(binding, partial, tables, (*path, "bindings", index))
            _check_tree(domain, partial, tables, (*path, "outside", index + 1))
    else:
        for name in ("bindings", "outside"):
            for index, value in enumerate(tree[name]):
                _check_tree(value, frames, tables, (*path, name, index))
    inner = (*frames, len(tree["bindings"]))
    for index, value in enumerate(tree["body"]):
        _check_tree(value, inner, tables, (*path, "body", index))
    _check_tree(tree["shape"], inner, tables, (*path, "shape"))


def _check_reference(tree, frames, tables, path):
    """A reference: a bound variable within the scopes around it, a document
    identity the encoding defines, or an unresolved reference's target."""
    reference = tree["ref"]
    if reference == "bound":
        depth, position = tree["depth"], tree["position"]
        if depth >= len(frames) or position >= frames[-1 - depth]:
            _fail(f"bound reference ({depth}, {position}) is outside its scope", path)
    elif reference == "document" and tree["id"] not in tables.identities:
        _fail(f"document identity {tree['id']!r} is not defined", path)
    elif reference == "unresolved":
        _check_tree(tree["target"], frames, tables, (*path, "target"))


def _check_unscoped_operator(fields, path):
    """The head and subscripts of an operator whose subscripts select declared
    names: a primitive head, and each subscript a `Var` or an `In` whose
    selected name is a document, primitive or unresolved reference. `forall`,
    `exists`, and an `argmax` or a `solve` over explicit domains are written as
    scopes instead."""
    head = _primitive_head(fields["head"], (*path, "fields", "head"))
    subs = fields["subs"]
    if not isinstance(subs, list) or not isinstance(fields["args"], list):
        _fail("ordinary operator subs and args must be lists", (*path, "fields"))
    kinds = []
    for index, sub in enumerate(subs):
        if (
            not isinstance(sub, dict)
            or sub.get("node") not in ("terms.Var", "terms.In")
            or "fields" not in sub
        ):
            _fail(
                "an ordinary operator subscript must be Var or In",
                (*path, "fields", "subs", index),
            )
        kinds.append(sub["node"])
        key = "name" if sub["node"] == "terms.Var" else "var"
        reference = sub["fields"].get(key)
        if not isinstance(reference, dict) or reference.get("ref") not in (
            "document",
            "primitive",
            "unresolved",
        ):
            _fail(
                "a selected name must be a document, primitive or unresolved reference",
                (*path, "fields", "subs", index, "fields", key),
            )
    if head in ("forall", "exists"):
        _fail(f"{head} must use a bound scope", path)
    if head in ("argmax", "solve") and all(kind == "terms.In" for kind in kinds):
        _fail(f"explicit-domain {head} must use a bound scope", path)


def _primitive_head(value, path):
    """The name of an operator's head, which is a primitive reference."""
    if not isinstance(value, dict) or value.get("ref") != "primitive":
        _fail("an operator head must be a primitive reference", path)
    return value["name"]


# The number of bound variables (at least), of outside terms and of bodies of
# a scoped node of each of these kinds.
_ScopeArity = namedtuple("_ScopeArity", "bindings outside bodies")
_SCOPE_ARITIES = {
    "semantic.Integral": _ScopeArity(bindings=1, outside=2, bodies=1),
    "semantic.Sup": _ScopeArity(bindings=1, outside=1, bodies=1),
    "semantic.Measure": _ScopeArity(bindings=1, outside=2, bodies=1),
    "semantic.ProductMeasure": _ScopeArity(bindings=1, outside=1, bodies=1),
}


def _scope_arity(tree, path):
    """The numbers of bound variables, outside terms and bodies of a scoped
    node, against those its kind requires."""
    node = tree["node"]
    bindings, bodies = len(tree["bindings"]), len(tree["body"])
    counts = (bindings, len(tree["outside"]), bodies)
    if node == "semantic.Lambda":
        expected = (bindings, bindings, 1)
    elif node in _SCOPE_ARITIES:
        # an integral, a supremum, a measure or a product of measures binds
        # one variable, or several coordinates as one `Subject`
        arity = _SCOPE_ARITIES[node]
        expected = (max(bindings, arity.bindings), arity.outside, arity.bodies)
    elif node == "terms.Comprehension":
        expected = (bindings, 1, bodies)
    elif node == "terms.Operator":
        expected = (bindings, bindings + 1, bodies)
    elif node in ("terms.FuncDef", "terms.CorrDef"):
        expected = (bindings, 1, 1)
    else:  # protected by the schema
        return
    if counts != expected:
        _fail(f"{node} has scope arity {counts}; expected {expected}", path)


def _validate_shape(tree, path):
    """The shape of a scoped node: none for a function, an integral, a
    supremum, a measure, a product of measures or a definition; one
    subscript form per binding for an operator; and for a comprehension a
    pattern that refers to each of its variables once, in order."""
    node, shape = tree["node"], tree["shape"]
    if node in (
        "semantic.Lambda",
        "semantic.Integral",
        "semantic.Sup",
        "semantic.Measure",
        "semantic.ProductMeasure",
        "terms.FuncDef",
        "terms.CorrDef",
    ):
        if shape != []:
            _fail(f"{node} has no bound-subject shape", (*path, "shape"))
    elif node == "terms.Operator":
        if (
            not isinstance(shape, list)
            or len(shape) != len(tree["bindings"])
            or any(kind not in ("terms.Var", "terms.In") for kind in shape)
        ):
            _fail("operator shape must name one subscript form per binding", (*path, "shape"))
    elif node == "terms.Comprehension":
        positions = _shape_positions(shape)
        expected = list(range(len(tree["bindings"])))
        if positions != expected:
            _fail(
                f"comprehension shape binds positions {positions}; expected {expected}",
                (*path, "shape"),
            )


def _shape_positions(value, nesting=0):
    """The positions of the variables of the scope at `nesting` that a shape
    refers to, in the order it names them; a scope inside the shape counts one
    deeper."""
    positions = []
    if isinstance(value, list):
        for item in value:
            positions.extend(_shape_positions(item, nesting))
    elif isinstance(value, dict):
        if value.get("ref") == "bound":
            if value["depth"] == nesting:
                positions.append(value["position"])
        elif "node" in value and "bindings" in value:
            if value["node"] == "terms.Operator":
                positions.extend(_shape_positions(value["outside"][0], nesting))
                for binding, domain in zip(value["bindings"], value["outside"][1:]):
                    positions.extend(_shape_positions(binding, nesting + 1))
                    positions.extend(_shape_positions(domain, nesting + 1))
            else:
                for name in ("bindings", "outside"):
                    positions.extend(_shape_positions(value[name], nesting))
            for item in value["body"]:
                positions.extend(_shape_positions(item, nesting + 1))
            positions.extend(_shape_positions(value["shape"], nesting + 1))
        else:
            for item in value.values():
                positions.extend(_shape_positions(item, nesting))
    return positions


def _scoped_operator(tree, path):
    """A scoped operator: a `forall` or an `exists`, or an `argmax` or a
    `solve` whose every subscript is `x ∈ X`."""
    head = _primitive_head(tree["outside"][0], (*path, "outside", 0))
    if head in ("forall", "exists"):
        return
    shape = tree["shape"]
    if (
        head not in ("argmax", "solve")
        or not isinstance(shape, list)
        or any(kind != "terms.In" for kind in shape)
    ):
        _fail(f"{head} is not a scoped operator", path)


# --- the check of the graphs' wiring ---


def _validate_graphs(document):
    """The wiring of each of the four graphs the encoding holds; a refused
    graph holds no structural source."""
    for section in ("initial_diagrams", "builders"):
        for direction in ("backward", "forward"):
            graph = document[section][direction]
            sources = document["derived"]["structural_sources"][section][direction]
            if "rule" in graph:  # retained refusal
                if sources:
                    _fail(
                        "a refused graph cannot have structural sources",
                        (section, direction, "structural_sources"),
                    )
                continue
            path = (section, direction)
            wires = {wire["identity"] for wire in graph["wires"]}
            _validate_source_paths(graph["boxes"], sources, wires, path)
            _validate_wiring(
                graph["boxes"],
                inputs=graph["inputs"],
                outputs=graph["outputs"],
                wires=wires,
                sources=sources,
                path=path,
            )


def _validate_source_paths(boxes, sources, wires, path):
    """Each structural source of a graph: its path names a composite box, and
    its outputs are wires of the graph."""
    for index, source in enumerate(sources):
        held = boxes
        for depth, place in enumerate(source["path"]):
            if place >= len(held) or "pieces" not in held[place]:
                _fail(
                    f"structural source path {source['path']} does not name a composite",
                    (*path, "structural_sources", index, "path", depth),
                )
            held = held[place]["pieces"]
        if missing := set(source["outputs"]) - wires:
            _fail(
                "structural source outputs are absent from the graph wire table: "
                f"{sorted(missing)}",
                (*path, "structural_sources", index, "outputs"),
            )


def _validate_wiring(boxes, *, inputs, outputs, wires, sources, path, source_path=()):
    """The wiring of the boxes of one level of a graph: the level's inputs and
    outputs, the wires its boxes produce and every box's ports stand in the
    graph's wire table; every box input is an input of the level, a structural
    source's output or another box's output; every output of the level is
    produced; and each composite box's pieces are checked as a level of their
    own."""
    producer_boxes = {}
    for index, box in enumerate(boxes):
        for wire in box["out"]:
            producer_boxes.setdefault(wire, set()).add(index)
    structural = {
        wire
        for source in sources
        if tuple(source["path"]) == source_path
        for wire in source["outputs"]
    }
    producers = set(producer_boxes) | structural
    for name, values in (("inputs", inputs), ("outputs", outputs), ("producers", producers)):
        unknown = set(values) - wires
        if unknown:
            _fail(f"graph {name} are absent from its wire table: {sorted(unknown)}", path)
    for index, box in enumerate(boxes):
        box_path = (*path, "boxes", index)
        ports = set(box["in"]) | set(box["out"])
        if missing := ports - wires:
            _fail(f"box ports are absent from the graph wire table: {sorted(missing)}", box_path)
        available = (
            set(inputs)
            | structural
            | {wire for wire, owners in producer_boxes.items() if owners - {index}}
        )
        if dangling := set(box["in"]) - available:
            _fail(f"box inputs have no producer in this graph: {sorted(dangling)}", box_path)
        if "pieces" in box:
            _validate_wiring(
                box["pieces"],
                inputs=box["in"],
                outputs=box["out"],
                wires=wires,
                sources=sources,
                path=(*box_path, "pieces"),
                source_path=(*source_path, index),
            )
    if dangling := set(outputs) - (set(inputs) | producers):
        _fail(f"graph outputs have no producer in this graph: {sorted(dangling)}", path)


def _fail(message, path=()):
    """A `ValueError` naming the place in the document and the fault."""
    location = "/".join(str(part) for part in path)
    raise ValueError(f"{location}: {message}" if location else message)


# --- the operator rows and the command line ---


def operators(document):
    """The row of each primitive operator the encoding's stage and primitives
    hold, its address, kind, rule, inputs, outputs and conditions, one row per
    address, once `validate_encoding` has checked the encoding."""
    validate_encoding(document)
    found = []
    derived = document["derived"]
    for bundle in (
        derived["stage"],
        derived["primitives"]["backward"],
        derived["primitives"]["forward"],
    ):
        _find_operators(bundle["value"], found)
    unique = {}
    for row in found:
        unique[row["address"]] = row
    return list(unique.values())


def _find_operators(tree, found):
    """The rows of the operator nodes within a tree, appended to `found`, depth
    first."""
    if isinstance(tree, list):
        for value in tree:
            _find_operators(value, found)
    elif isinstance(tree, dict):
        if tree.get("node") == "records.OperatorCard" and "fields" in tree:
            found.append(_operator(tree))
        for value in tree.values():
            _find_operators(value, found)


def _operator(value):
    """The row of one operator node: its address, kind, rule, inputs, outputs
    and conditions."""
    fields = value["fields"]
    return {
        "address": _address(fields["title"]),
        "kind": fields["kind"],
        "rule": fields["expression"],
        "inputs": fields["inputs"],
        "outputs": fields["outputs"],
        "conditions": fields["conditions"],
    }


def _address(title):
    """The address of a title block, or None where the title is none."""
    if isinstance(title, dict) and title.get("node") == "records.TitleBlock":
        return title["fields"]["address"]
    return None


def main(argv=None):
    """The command line: the operator rows of the encoding at a path, written
    as JSON to standard output."""
    parser = argparse.ArgumentParser(description="List operators in a Bellman-SYM encoding")
    parser.add_argument("path", type=Path)
    arguments = parser.parse_args(argv)
    with arguments.path.open(encoding="utf-8") as source:
        document = json.load(source)
    json.dump(
        operators(document),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    print()


if __name__ == "__main__":
    main()
