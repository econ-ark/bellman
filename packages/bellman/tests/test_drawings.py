"""What a drawing shows, and how large it is (the design of P21-1).

Two properties, one test each.

The first is the property the redesign of the presentation had to keep: a
drawing shows exactly the boxes, the wires and the incidences of the graph it
draws. It is read at every grain of both builders graphs and of both initial
diagrams of the five corpus stages — 60 drawings — with a wire the drawing
folds into the label of one arrow counted from that arrow, and a value bundle
counted as the one wire its label stands on, which is how the drawing has
counted a bundle since AMD-SG-011 §5.

The second is the size check of the brief: every drawing of the three models
that carry a whole economic problem fits a notebook cell and a page of the
documentation at its natural size, at most 7.0 inches wide and 13.5 inches
tall, with no `size` and no `ratio` to shrink the type with the drawing. The
layout program is Graphviz's `dot` where it is installed and otherwise the
WebAssembly build of Graphviz the package runs through Node
(`bellman.display.graphviz_layout`); where neither is installed the test is
skipped, since the package installs no layout program.
"""
from __future__ import annotations

import re

import pytest

from bellman.display import graphviz_layout
from bellman.display.graphviz_layout import layout_command, node_package_root, node_program
from bellman.native.identity import box_identity
from bellman.native.labels import is_wiring
from bellman.graphs.builders_graphs import bundles
from bellman.stage.grains import graph_of
from bellman.stage.pieces import GraphHandle

from discopy.frobenius import Bubble, Hypergraph

# the twelve drawings of one stage: the two initial diagrams and the two
# builders graphs at the five grains
GRAINS = ("builder", "node", "primitive", "combined", "factored")
DRAWINGS = ([("initial", direction, "builder") for direction in ("backward", "forward")]
            + [("builders", direction, grain) for direction in ("backward", "forward") for grain in GRAINS])
# the three models that carry a whole economic problem, by the stage name the
# corpus fixtures give them
MODELS = ("cons", "cons_savings_iid", "sa_savings")
WIDTH_LIMIT, HEIGHT_LIMIT = 7.0, 13.5
# the drawings that stand taller than a page on main, each with the height in
# inches that the WebAssembly build of Graphviz the root package.json pins
# (Graphviz 14.1.3) gives it. A listed drawing that grows taller fails as an
# unlisted one does, and one that comes to fit fails until its entry is
# deleted, so that the list shrinks with the work that redraws them. The three
# backward drawings of `sa_savings`, taller than 13.5 inches since the build
# entered the package (e8efbb29c, 27 September 2026), fit since the stage has
# no arrival builders (decision MB-V49), and none is listed
OVER_THE_PAGE_TODAY = {}

NODE = re.compile(r'^\s*"(\w+)"\s*\[(.*)\];$')
EDGE = re.compile(r'^\s*"(\w+)"\s*->\s*"(\w+)"\s*(?:\[(.*)\])?;$')
ATTRIBUTE = re.compile(r'(\w+)="((?:[^"\\]|\\.)*)"')
SIZE = re.compile(r'<svg width="([\d.]+)pt" height="([\d.]+)pt"')


def _named(attributes):
    """The identity a tooltip names: what stands before the em dash that
    separates it from the sentence the card prints."""
    return attributes.get("tooltip", "").split(" — ", 1)[0]


def _shown(source):
    """The boxes, the wires and the incidences one drawing shows, read back
    from its DOT text: each box and each wire by the identity its tooltip
    names, and each incidence as (box, wire, `in` or `out`). An arrow carrying
    a label is a wire folded into it and stands for both of its incidences."""
    nodes = {found.group(1): dict(ATTRIBUTE.findall(found.group(2)))
             for found in (NODE.match(line) for line in source.splitlines())
             if found and not EDGE.match(found.string)}
    boxes = {_named(attributes) for name, attributes in nodes.items() if name.startswith("b")}
    wires = {_named(attributes) for name, attributes in nodes.items() if name.startswith("w")}
    incidences = set()
    for line in source.splitlines():
        found = EDGE.match(line)
        if not found:
            continue
        source_name, target_name = found.group(1), found.group(2)
        attributes = dict(ATTRIBUTE.findall(found.group(3) or ""))
        if not attributes:
            if source_name.startswith("w"):
                incidences.add((_named(nodes[target_name]), _named(nodes[source_name]), "in"))
            else:
                incidences.add((_named(nodes[source_name]), _named(nodes[target_name]), "out"))
            continue
        folded = _named(attributes)
        wires.add(folded)
        incidences.add((_named(nodes[source_name]), folded, "out"))
        incidences.add((_named(nodes[target_name]), folded, "in"))
    return boxes, wires, incidences


def _held(graph):
    """The boxes, the wires and the incidences one graph holds, in the same
    three sets: every operator box at every depth, and every wire by the
    spelling of the identities it carries, a value bundle by its components in
    order, which is the one wire the drawing gives it."""
    bundled = bundles(graph)

    def spelled(sort):
        return ", ".join(str(member) for member in bundled.get(sort.identity, (sort.identity,)))

    boxes, wires, incidences = set(), set(), set()

    def walk(part):
        inside = part if isinstance(part, Hypergraph) else Hypergraph.from_diagram(part)
        for spider in inside.spider_types:
            for ob in spider.inside:
                wires.add(spelled(ob))
        for box in (part.to_diagram().boxes if isinstance(part, Hypergraph) else part.boxes):
            if is_wiring(box):
                continue
            if isinstance(box, Bubble):
                for ob in box.dom.inside + box.cod.inside:
                    wires.add(spelled(ob))
                walk(box.arg)
                continue
            boxes.add(str(box_identity(box)))
            for ob in box.dom.inside:
                wires.add(spelled(ob))
                incidences.add((str(box_identity(box)), spelled(ob), "in"))
            for ob in box.cod.inside:
                wires.add(spelled(ob))
                incidences.add((str(box_identity(box)), spelled(ob), "out"))

    for ob in graph.dom.inside + graph.cod.inside:
        wires.add(spelled(ob))
    walk(graph)
    return boxes, wires, incidences


def test_a_drawing_shows_the_boxes_the_wires_and_the_incidences_of_its_graph(
        cons, port, ez_savings, cons_savings_iid, sa_savings):
    """The presentation of a drawing carries its whole structure: at every
    grain of every graph of the five corpus stages the drawing's boxes, wires
    and incidences are the graph's own, a folded wire read from the arrow that
    carries it (the acceptance check of P21-1, item 1)."""
    differ = []
    for stage in (cons, port, ez_savings, cons_savings_iid, sa_savings):
        for level, direction, grain in DRAWINGS:
            graph = graph_of(stage, level, direction, grain)
            drawing = GraphHandle(stage, level, direction, grain).diagram()
            shown, held = _shown(drawing.source), _held(graph)
            if shown != held:
                parts = [word for word, one, two in zip(("boxes", "wires", "incidences"), shown, held)
                         if one != two]
                differ.append(f"{stage.name} {level} {direction} {grain}: {', '.join(parts)}")
    assert differ == []


def test_every_drawing_of_the_three_models_fits_a_notebook_cell_and_a_page(
        cons, cons_savings_iid, sa_savings, monkeypatch):
    """No drawing of the three models is wider than 7.0 inches or taller than
    13.5 inches at its natural size, those of `OVER_THE_PAGE_TODAY` excepted
    up to their recorded heights, and none is scaled: the drawing sets no
    `size` and no `ratio`, so a 10-point label is 10 points (the acceptance
    check of P21-1, items 2 and 3). Where the Node package that the root
    package.json pins is installed, the drawings are measured with it and not
    with a `dot` on the PATH, whose version the repository does not fix, so
    that every machine measures as the lessons are drawn."""
    if node_program() is not None and node_package_root() is not None:
        monkeypatch.setattr(graphviz_layout, "dot_program", lambda: None)
    if layout_command() is None:
        pytest.skip("no Graphviz layout program: neither `dot` on the PATH nor the Node package the root package.json names")
    over, fitting = [], []
    smallest = None
    for stage in (cons, cons_savings_iid, sa_savings):
        for level, direction, grain in DRAWINGS:
            name = f"{stage.name} {level} {direction} {grain}"
            svg = GraphHandle(stage, level, direction, grain).diagram().svg()
            width, height = (float(value) / 72 for value in SIZE.search(svg).groups())
            listed = OVER_THE_PAGE_TODAY.get(name)
            if width > WIDTH_LIMIT or height > HEIGHT_LIMIT:
                if listed is None or width > WIDTH_LIMIT or round(height, 2) > listed:
                    over.append(f"{name}: {width:.2f} × {height:.2f} inches")
            elif listed is not None:
                fitting.append(f"{name} now fits, {width:.2f} × {height:.2f} inches; "
                               "delete it from OVER_THE_PAGE_TODAY")
            sizes = [float(value) for value in re.findall(r'font-size="([\d.]+)"', svg)]
            smallest = min([smallest] + sizes) if smallest is not None else min(sizes, default=None)
            assert "scale(1 1)" in svg or "scale(" not in svg, (stage.name, level, direction, grain)
    assert over == [] and fitting == []
    assert smallest == 9.0
