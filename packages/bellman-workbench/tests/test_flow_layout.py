"""The layout script `js/flow/src/flow-layout.js`, run under Node: the label
a join wire prints (unit K's decision K-D4), the order of a period's
readers (K-D12), the one wire of an adjacent pair of periods (K-D5,
K-D13) and the frame of a closed stage occurrence (K-D15).

The script names each join on its wire by `joinLabel` of the join's text,
the reading port's attribute `join` as the package's exporter writes it:
entries `[mapping ]field[ → arrival]` joined by `; `. Its `build` orders by
the writer's outputs the ports of a closed layer whose wires are read in its
own period and an open period's occurrences, orders the reading ports of a
closed layer by its writers' occurrences, and gives the wires from one
period to one reading port in the next one piece between the two periods;
its `read` places a `+ period` control in the gap under that piece. A
stage occurrence, closed or compact, is a card that carries every field
port of its own `Inputs` and `Outputs` and prints a field's name where no
join reaches it, every name where it is unfolded (AAS, L-D16, L-D19 and
L-D25); the wires of an ordered pair of stage occurrences within a period
are one bundle, split while either occurrence or the bundle is selected
(AAS, L-D25); a wire that carries a value, as the
backward trellis graph's wires do, prints the name of that function, and a
bundle of such wires their names (AAS, L-D26). In
the stage view a box's label is cut at G.labelMax, and in a stage's
builders graph `arrange` stands the boxes of each open frame on its axis,
gives every open frame of a builder one width, and stands the builders
joined by wires in one column with the stage's `Inputs` and `Outputs`,
their frames of one left edge, the policy builder beside them (AAS,
L-D20). The value wires from one box to another of a stage's builders
graph are one line with the count of its wires at its plug, drawn from
the ports of its first wire (design pass 14 §1); two markers laid out
downward stand their widest label and 8 px apart (§3); and a trellis's
initial diagram draws a card with no strip and one cable between two
cards (§7, rule 5). The script is run in a context of its own, where it defines
`BellmanFlowLayout` on its `self`, as it does on a page's window. The
tests are skipped when `node` is not on the PATH.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from workbench_support import (
    CONS,
    KEEPER_CONS,
    PORTFOLIO_CHOICE,
    bound_as_the_recipe_binds,
    node_output,
)
from workbench_support import DURABLES as DURABLES_MODEL

from bellman_workbench import model, recipe, trellis

ROOT = Path(__file__).resolve().parents[3]
LAYOUT = ROOT / "packages/bellman-workbench/js/flow/src/flow-layout.js"
# ELK's unchanged file, which the page loads beside the bundle
ELK = ROOT / "packages/bellman-workbench/bellman_workbench/public/flow/elk.bundled.js"

# the Node module: runs the layout script, reads the join texts on standard
# input and prints the label of each
NODE_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const texts = JSON.parse(readFileSync(0, "utf8"));
console.log(JSON.stringify(texts.map((text) => context.BellmanFlowLayout.joinLabel(text))));
"""

# the join texts of the durables model's forward trellis graph and the label
# each prints: the six entries of an inter-period mapping, 205 characters;
# the six entries into the bequest stage of the terminal period, 103
# characters; and two joins by equal names inside a period, of at most 22
# characters, printed as they stand
DURABLES = {
    "inter_connectors[1] a_nxt_kp → a; inter_connectors[1] h_nxt_kp → h; "
    "inter_connectors[1] z_nxt_kp → z; inter_connectors[1] a_nxt_adj → a; "
    "inter_connectors[1] h_nxt_adj → h; inter_connectors[1] z_nxt_adj → z": "a, h, z",
    "a_nxt_adj → a_bq; h_nxt_adj → h_bq; z_nxt_adj → z_bq; "
    "a_nxt_kp → a_bq; h_nxt_kp → h_bq; z_nxt_kp → z_bq": "a_bq, h_bq, z_bq",
    "w_adj; z_adj": "w_adj; z_adj",
    "h_kp; w_kp; z_kp": "h_kp; w_kp; z_kp",
}
# further texts: one entry longer than 22 characters; joins by equal names
# after a mapping's index; arrival fields that together exceed 22
# characters, counted; one such field alone; and no join
FURTHER = {
    "inter_connectors[0] a_nxt_kp → a": "a",
    "inter_connectors[2] y_f_r; inter_connectors[2] y_p_r": "y_f_r, y_p_r",
    "inter_connectors[0] wealth_next → wealth; inter_connectors[0] income_next → income; "
    "inter_connectors[0] housing_next → housing": "3 joins",
    "inter_connectors[0] income_next → permanent_income_component": "1 join",
    "": "",
}


def test_a_join_label_names_the_arrival_fields_or_counts_the_joins(node):
    """A join's text of at most 22 characters is printed as it stands;
    a longer one prints the arrival fields its entries reach, each once, in
    the entries' order, joined by `, `, where those take at most 22
    characters, and otherwise the number of its entries (K-D4; spec 0.4
    §2.1, the port-label rule of 22 characters)."""
    cases = {**DURABLES, **FURTHER}
    script = NODE_SCRIPT % {"script": json.dumps(str(LAYOUT))}
    labels = node_output(node, script, list(cases))
    assert labels == list(cases.values())


# the Node module: runs the layout script, builds the graph JSON read on
# standard input with every layer open but the builders, so that every
# occurrence is drawn compact (AAS, L-D7), and with the further layers the
# test names open, in the direction the test names for every layer or,
# where it names none, in the directions the graph configures, and prints
# the writing and the reading ports of each closed layer's box and of each
# compact occurrence's frame, and each open period's occurrences in the
# order ELK receives them with the model-order options it is given; the
# stage keys' order the test names, the recipe's `stages:` list, or none
# (the fix wave Q3a of unit Q, item 2)
BUILD_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const m = L.model(JSON.parse(readFileSync(0, "utf8")));
const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length < 3)
  .concat(%(further)s));
const options = { direction: %(direction)s, order: %(order)s };
const built = L.build(m, open, options, (text) => Array.from(text || "").length * 7);
const ports = {}, reads = {}, periods = {};
for (const box of Object.values(built.boxes)) {
  if (box.type !== "layer" || (box.open && !box.compact)) continue;
  ports[box.namespace] = box.geom.outs.map((p) => p.id);
  reads[box.namespace] = box.geom.ins.map((p) => p.id);
}
for (const period of built.elk.children) {
  periods[period.id] = {
    children: period.children.map((child) => child.id),
    modelOrder: period.layoutOptions["elk.layered.considerModelOrder.strategy"] || null,
    forced: period.layoutOptions["elk.layered.crossingMinimization.forceNodeModelOrder"] || null,
  };
}
console.log(JSON.stringify({ ports, reads, periods }));
"""


def _node(node_id: str, outputs=(), reads=()) -> dict:
    """A node of the graph JSON in the namespace its id names before its
    last `/`, with one input port `in` and the output ports `outputs`;
    `reads` are the (writer, output) pairs whose wires its input port
    reads."""
    return {
        "id": node_id,
        "label": node_id,
        "namespace": node_id.rsplit("/", 1)[0],
        "attrs": [{"key": "kind", "value": "operator"}],
        "inputsMetadata": [{"id": "in", "attrs": []}],
        "outputsMetadata": [{"id": output, "attrs": []} for output in outputs],
        "incomingEdges": [
            {"sourceNodeId": writer, "sourceNodeOutputId": output, "targetNodeInputId": "in"}
            for writer, output in reads
        ],
    }


# three periods of a forward trellis graph in the shape of the durables
# model's: in periods[0] and periods[1], the builder `push` of `tenure`
# writes `adjuster_cons` from its second output, `adjust`, and `keeper_cons`
# from its first, `keep`, while the graph JSON lists `adjuster_cons` first;
# in periods[0], `bequest` is written by both, and the builder `arrive` of
# `tenure` reads the two occurrences of periods[1], `keeper_cons` before
# `adjuster_cons`; in periods[2], `sink` is written by two occurrences and no
# other occurrence is written; the builder `push` of `left` in periods[2]
# writes its outputs `first` and `second` into the builder `arrive` of
# `tenure` in periods[1], which reads `second`, then the output of `right`,
# then `first`
PERIODS = {
    "groupNodeConfigs": [
        {"namespaceRegex": "^$", "layoutDirection": 1},
        {"namespaceRegex": "^periods\\[\\d+\\]$", "layoutDirection": 1},
        {"namespaceRegex": "^periods\\[\\d+\\]/[^/]+$", "layoutDirection": 0},
        {"namespaceRegex": "^periods\\[\\d+\\]/[^/]+/", "layoutDirection": 0},
    ],
    "nodes": [
        _node("periods[0]/tenure/push/g", outputs=("keep", "adjust")),
        _node(
            "periods[0]/tenure/arrive/g",
            reads=(
                ("periods[1]/keeper_cons/pull/g", "out"),
                ("periods[1]/adjuster_cons/pull/g", "out"),
            ),
        ),
        _node(
            "periods[0]/adjuster_cons/pull/g",
            outputs=("out",),
            reads=(("periods[0]/tenure/push/g", "adjust"),),
        ),
        _node(
            "periods[0]/keeper_cons/pull/g",
            outputs=("out",),
            reads=(("periods[0]/tenure/push/g", "keep"),),
        ),
        _node(
            "periods[0]/bequest/pull/g",
            reads=(
                ("periods[0]/adjuster_cons/pull/g", "out"),
                ("periods[0]/keeper_cons/pull/g", "out"),
            ),
        ),
        _node("periods[1]/tenure/push/g", outputs=("keep", "adjust")),
        _node(
            "periods[1]/tenure/arrive/g",
            reads=(
                ("periods[2]/left/push/g", "second"),
                ("periods[2]/right/push/g", "out"),
                ("periods[2]/left/push/g", "first"),
            ),
        ),
        _node(
            "periods[1]/adjuster_cons/pull/g",
            outputs=("out",),
            reads=(("periods[1]/tenure/push/g", "adjust"),),
        ),
        _node(
            "periods[1]/keeper_cons/pull/g",
            outputs=("out",),
            reads=(("periods[1]/tenure/push/g", "keep"),),
        ),
        _node("periods[2]/left/push/g", outputs=("first", "second", "out")),
        _node("periods[2]/right/push/g", outputs=("out",)),
        _node(
            "periods[2]/sink/pull/g",
            reads=(("periods[2]/left/push/g", "out"), ("periods[2]/right/push/g", "out")),
        ),
    ],
}


# the builder `push` of `tenure` in periods[0] and periods[1], whose opening
# draws those two occurrences in full, their builder `arrive` closed
TENURE_PUSH = ("periods[0]/tenure/push", "periods[1]/tenure/push")


# the recipe's order of the durables model's stages, `stages:` (the fix wave
# Q3a of unit Q, item 2)
RECIPE_ORDER = ["tenure", "keeper_cons", "adjuster_cons", "bequest"]


def _build_script(direction: str | None, further=(), order=None) -> str:
    """BUILD_SCRIPT in the direction `direction`, None for the directions
    the graph configures, with the layers `further` open and the stage keys'
    order `order`, the recipe's, or none."""
    return BUILD_SCRIPT % {
        "script": json.dumps(str(LAYOUT)),
        "direction": json.dumps(direction),
        "further": json.dumps(list(further)),
        "order": json.dumps(order),
    }


def test_a_period_hands_its_occurrences_to_elk_in_the_recipe_s_order_and_a_writer_s_ports_follow_its_readers(node):
    """The fix wave Q3a of unit Q, item 2, which amends K-D12 (A17, B15):
    every open period hands its occurrences to ELK in the rank of their
    stage keys, their places in the recipe's `stages:` list
    (`options.order`), the keys the list does not name after them in the
    order the graph JSON first names them, with ELK's model-order option
    and its forced node order, so that one row order stands in every period
    of both graphs, `keeper_cons` above `adjuster_cons`; with no order
    given, the graph JSON's order alone ranks them, `adjuster_cons` first.
    A card's plugs follow its readers' rank: `tenure`'s port `keep`, which
    reaches `keeper_cons`, before its port `adjust`. A closed layer, or the
    frame of a compact occurrence (AAS, L-D7), whose wires are all read in
    its own period has its ports in the order of its nodes' outputs among
    the plugs of one rank, and one that writes into another period keeps
    the order in which its wires are read (row K-I9). The frame of a
    compact occurrence, laid out to the right as its period is, reads the
    occurrences of a period, one above another, on its left edge in their
    rank from top to bottom, `keeper_cons` before `adjuster_cons`, where
    they are read in that order, by `tenure` in the next period, and where
    they are read in the other, by `bequest` in their own period, and the
    writers `left` and `right` of periods[2] in their rank (AAS, L-D7).
    With `tenure`'s builder `push` open, so that the occurrence is drawn in
    full, its closed builder `arrive`, inside the occurrence laid out
    downward, has its reading ports, left to right, in the reverse of that
    rank, `adjuster_cons` before `keeper_cons` and `right` before `left`
    (row K-I14)."""
    built = node_output(node, _build_script(None, order=RECIPE_ORDER), PERIODS)
    for h in (0, 1):
        assert built["ports"][f"periods[{h}]/tenure"] == [
            f"periods[{h}]/tenure/push/g|keep",
            f"periods[{h}]/tenure/push/g|adjust",
        ]
    assert built["ports"]["periods[2]/left"] == [
        "periods[2]/left/push/g|second",
        "periods[2]/left/push/g|first",
        "periods[2]/left/push/g|out",
    ]
    assert built["reads"]["periods[0]/tenure"] == [
        "periods[1]/keeper_cons/pull/g|out",
        "periods[1]/adjuster_cons/pull/g|out",
    ]
    assert built["reads"]["periods[1]/tenure"] == [
        "periods[2]/left/push/g|second",
        "periods[2]/left/push/g|first",
        "periods[2]/right/push/g|out",
    ]
    assert built["reads"]["periods[0]/bequest"] == [
        "periods[0]/keeper_cons/pull/g|out",
        "periods[0]/adjuster_cons/pull/g|out",
    ]
    full = node_output(node, _build_script(None, TENURE_PUSH, order=RECIPE_ORDER), PERIODS)
    assert full["reads"]["periods[0]/tenure/arrive"] == [
        "periods[1]/adjuster_cons/pull/g|out",
        "periods[1]/keeper_cons/pull/g|out",
    ]
    assert full["reads"]["periods[1]/tenure/arrive"] == [
        "periods[2]/right/push/g|out",
        "periods[2]/left/push/g|second",
        "periods[2]/left/push/g|first",
    ]
    for h, bequest in ((0, ["periods[0]/bequest___group___"]), (1, [])):
        assert built["periods"][f"periods[{h}]___group___"] == {
            "children": [
                f"periods[{h}]/tenure___group___",
                f"periods[{h}]/keeper_cons___group___",
                f"periods[{h}]/adjuster_cons___group___",
                *bequest,
            ],
            "modelOrder": "NODES_AND_EDGES",
            "forced": "true",
        }
    assert built["periods"]["periods[2]___group___"] == {
        "children": [
            "periods[2]/left___group___",
            "periods[2]/right___group___",
            "periods[2]/sink___group___",
        ],
        "modelOrder": "NODES_AND_EDGES",
        "forced": "true",
    }
    # with no order given, the graph JSON's order ranks the keys, `adjuster_cons` first
    unordered = node_output(node, _build_script(None), PERIODS)
    assert unordered["ports"]["periods[0]/tenure"] == [
        "periods[0]/tenure/push/g|adjust",
        "periods[0]/tenure/push/g|keep",
    ]
    assert unordered["periods"]["periods[0]___group___"]["children"] == [
        "periods[0]/tenure___group___",
        "periods[0]/adjuster_cons___group___",
        "periods[0]/keeper_cons___group___",
        "periods[0]/bequest___group___",
    ]


def test_laid_out_downward_a_closed_layer_keeps_the_order_its_wires_are_read(node):
    """Where the graph's direction button lays every layer out downward
    (`options.direction` `DOWN`), the occurrences of a period stand side by
    side and their wires turn to no other direction on the way to a reading
    port; every compact occurrence's frame (AAS, L-D7), and with `tenure`'s
    builder `push` open every closed layer, then has its reading ports in
    the order in which its wires are read, the builder `arrive` of `tenure`
    in periods[0] reading `keeper_cons` before `adjuster_cons` (row
    K-I14)."""
    built = node_output(node, _build_script("DOWN"), PERIODS)
    # each occurrence's frame reads the wires of its builders' nodes, in the
    # order of the nodes and of each node's incoming edges
    expected = {}
    for entry in PERIODS["nodes"]:
        expected.setdefault(entry["namespace"].rsplit("/", 1)[0], []).extend(
            f"{edge['sourceNodeId']}|{edge['sourceNodeOutputId']}"
            for edge in entry["incomingEdges"]
        )
    assert built["reads"] == expected
    full = node_output(node, _build_script("DOWN", TENURE_PUSH), PERIODS)
    assert full["reads"]["periods[0]/tenure/arrive"] == [
        "periods[1]/keeper_cons/pull/g|out",
        "periods[1]/adjuster_cons/pull/g|out",
    ]


# the Node module: runs the layout script, builds the graph JSON read on
# standard input with every layer open but the builders, a `+ period`
# control at the earliest end and one between each two of its three
# periods, lays it out with ELK and reads ELK's answer; prints the pieces of
# the graph's root between two period layers, each [writer's period, reader's
# period, whether it carries a label, the label's width], the edges of the
# root that keep a control's room with their label's width, the bundles, the
# ids of the root's boxes, and the places of the period layers, of the
# controls, of each bundle's route and label and of each bundled wire's two
# drawn parts; a text is 7 px wide for each of its characters
BUNDLE_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const m = L.model(JSON.parse(readFileSync(0, "utf8")));
const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length < 3));
const earliest = { target: "earliest end", after: "periods[2]___group___", name: "add a period" };
const adds = [earliest].concat(
  [2, 1].map((h) => ({
    target: `between periods[${h}] and periods[${h - 1}]`,
    after: `periods[${h}]___group___`,
    name: "add a period",
  })));
const built = L.build(m, open, { adds }, (text) => Array.from(text || "").length * 7);
const read = L.read(built, await new ELK().layout(JSON.parse(JSON.stringify(built.elk))));
const period = (id) => id.replace(/___group___::.*$/, "");
const between = /^periods\\[\\d+\\]___group___::hout::/;
const wires = Object.fromEntries(built.wires.map((w) => [w.id, w]));
const width = (e) => (e.labels && e.labels.length ? e.labels[0].width : null);
console.log(JSON.stringify({
  root: built.elk.edges.filter((e) => between.test(e.sources[0]))
    .map((e) => [
      period(e.sources[0]), period(e.targets[0]), !!(e.labels && e.labels.length), width(e),
    ]),
  room: built.elk.edges.filter((e) => /::room$/.test(e.id)).map((e) => [e.id, width(e)]),
  bundles: built.bundles.map((u) => ({
    from: u.from, to: u.to, wires: u.wires.length,
    shared: u.pieces.length === u.wires.length && u.wires.every((id, k) => wires[id].pieces.includes(u.pieces[k])),
    route: read.bundles[u.id].points, label: read.bundles[u.id].join,
    parts: u.wires.map((id) => read.parts[id]),
  })),
  children: built.elk.children.map((child) => child.id),
  places: read.place,
  words: [L.PERIOD_WORDS, L.STAGE_WORDS],
  spacing: Number(built.elk.layoutOptions["elk.layered.spacing.nodeNodeBetweenLayers"]),
}));
"""
# the size of the control that adds a period under that measure: the Codicon
# `add`, 16 px, the 6 characters of `Period` and 4 px at each side, 24 px
# high (design pass 13 §2, rule 8); and the control's room in the gap
# between two periods, the control's width and a layer's padding of 8 px at
# each side, which the root's spacing between its periods keeps (K-D13;
# design pass 13 §2, rule 9)
CONTROL = {"width": 66, "height": 24}
ROOM = 82


def _joined(graph: dict, join: str) -> dict:
    """A copy of the graph JSON `graph` whose reading port `in` of each
    builder `arrive` carries the join text `join`, as the exporter writes it
    on a port that joins between periods reach."""
    copy = json.loads(json.dumps(graph))
    for entry in copy["nodes"]:
        if entry["id"].endswith("/arrive/g"):
            entry["inputsMetadata"] = [{"id": "in", "attrs": [{"key": "join", "value": join}]}]
    return copy


def _in_the_gap(places: dict, earlier: str, later: str, route=None) -> None:
    """Asserts that the `+ period` control between the period layers
    `earlier` and `later` has the size `CONTROL` and stands wholly in the gap
    between their places, and, where `route` is given, below every point of
    it."""
    left, right = places[f"{earlier}___group___"], places[f"{later}___group___"]
    control = places[f"add-period::between {earlier} and {later}"]
    assert {key: control[key] for key in CONTROL} == CONTROL
    assert left["ax"] + left["width"] < control["ax"]
    assert control["ax"] + control["width"] < right["ax"]
    if route is not None:
        assert control["ay"] > max(point["y"] for point in route)


JOIN_GEOMETRY_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const graph = JSON.parse(readFileSync(0, "utf8"));
const elk = new ELK();
const measure = (text) => Array.from(text || "").length * 7;
const results = [];
for (const [depth, closeWriter] of [[2, false], [3, false], [3, true]]) {
  const m = L.model(graph);
  const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length <= depth
    && (!closeWriter || ns.split("/")[0] !== "periods[1]")));
  for (const direction of ["RIGHT", "DOWN"]) {
    const options = { direction, order: ["tenure", "keeper_cons", "adjuster_cons", "bequest"] };
    let built = L.build(m, open, options, measure);
    let answer = await elk.layout(structuredClone(built.elk));
    const widths = L.columnWidths(built, answer);
    if (widths) {
      built = L.build(m, open, { ...options, widths }, measure);
      answer = await elk.layout(structuredClone(built.elk));
    }
    answer = await L.arrange(built, answer, elk);
    L.settle(built, answer);
    const r = L.read(built, answer);
    const from = "periods[1]", to = "periods[0]";
    const writer = r.place[from + L.LAYER_ENDING], reader = r.place[to + L.LAYER_ENDING];
    const down = direction === "DOWN";
    const byId = Object.fromEntries(built.wires.map((w) => [w.id, w]));
    results.push({
      name: [graph.id, depth, closeWriter, direction],
      axis: down ? "y" : "x",
      gap: down ? [writer.ay + writer.height, reader.ay] : [writer.ax + writer.width, reader.ax],
      joins: built.bundles.filter((u) => u.from === from && u.to === to).map((u) => ({
        reader: u.reader,
        input: u.into,
        count: u.count,
        shared: r.bundles[u.id].points,
        legs: u.wires.map((id) => {
          const w = byId[id];
          const box = r.place[w.target];
          const port = built.boxes[w.target].geom.ins.find((p) => p.handle === w.targetHandle);
          return { writer: w.from, points: r.parts[id][0],
                   socket: { x: box.ax + port.x, y: box.ay + port.y } };
        }),
      })),
    });
  }
}
console.log(JSON.stringify(results));
"""


def test_durables_writers_join_once_in_the_gap_and_share_the_route_to_each_input(node):
    folder = model.open_folder(DURABLES_MODEL)
    source = recipe.Source("recipe", "declaration/spec.yml")
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, source, restriction).shown
    forward = next(graph for graph in shown.collection["graphs"] if graph["id"] == "forward")
    script = JOIN_GEOMETRY_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    for result in node_output(node, script, forward):
        axis = result["axis"]
        near, far = result["gap"]
        joins = result["joins"]
        assert len(joins) == 1, result
        assert len({(join["reader"], join["input"]) for join in joins}) == len(joins), result
        for join in joins:
            shared = join["shared"]
            assert len(shared) >= 2 and near < shared[0][axis] < far, result
            assert join["count"] == 6, result
            legs = join["legs"]
            assert len(legs) == 2, result
            assert {leg["writer"].split("/")[1] for leg in legs} == {"keeper_cons", "adjuster_cons"}, result
            for leg in legs:
                points = leg["points"]
                assert len(points) >= 2 and points[-1] == shared[0], result
                assert all(p[axis] < far for p in points), result
                assert shared[-1] == leg["socket"], result
                route = points + shared[1:]
                assert all(
                    (abs(a["x"] - b["x"]) < 0.01) != (abs(a["y"] - b["y"]) < 0.01)
                    for a, b in zip(route, route[1:])
                ), result


WIRE_OVERLAP_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const cases = JSON.parse(readFileSync(0, "utf8"));
const elk = new ELK();
const measure = (text) => Array.from(text || "").length * 7;
const results = [];
for (const spec of cases) {
  let built, answer;
  if (spec.graph) {
    const m = L.model(spec.graph);
    const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length <= spec.depth));
    const options = { direction: spec.direction, order: spec.order };
    built = L.build(m, open, options, measure);
    answer = await elk.layout(structuredClone(built.elk));
    const widths = L.columnWidths(built, answer);
    if (widths) {
      built = L.build(m, open, { ...options, widths }, measure);
      answer = await elk.layout(structuredClone(built.elk));
    }
    answer = await L.arrange(built, answer, elk);
    L.settle(built, answer);
  } else {
    const wires = Object.keys(spec.paths).map((id) => ({ id, pieces: [id] }));
    built = { elk: {}, boxes: {}, wires, bundles: [], samePeriod: spec.groups };
    if (spec.initial) {
      built.initialRoutes = wires.map((w) => {
        Object.assign(w, { initialStart: 0, initialEnd: 1 });
        return { id: 'route:' + w.id, wires: [w.id], count: 1, route: { source: w.id } };
      });
    }
    const edges = Object.entries(spec.paths).map(([id, path]) => {
      const points = path.map(([x, y]) => ({x, y}));
      return {id, sections: [{startPoint: points[0], bendPoints: points.slice(1, -1), endPoint: points.at(-1)}]};
    });
    answer = {edges};
  }
  const r = L.read(built, answer);
  const wires = built.wires.filter((w) => !spec.reader || w.to.startsWith(spec.reader));
  const ids = new Set(wires.map((w) => w.id));
  results.push({
    wires: wires.map((w) => ({ id: w.id, from: w.from, into: w.into, pieces: w.pieces,
      route: r.routes[w.id], paint: r.paint?.[w.id] ?? r.parts[w.id] ?? [r.routes[w.id]] })),
    shared: (r.sharedRuns || []).filter((run) => run.members.some((id) => ids.has(id))),
    bundles: built.bundles.filter((u) => r.bundles[u.id] && u.wires.some((id) => ids.has(id)))
      .map((u) => ({ members: u.wires, points: r.bundles[u.id].points })),
    initial: {
      routes: (r.initialRoutes || []).map((u) => ({ id: u.id, source: u.route.source,
        paths: [u.points, ...u.wires.flatMap((id) => r.parts[id])],
        paint: (r.paint[u.id] ?? [u.points]).concat(u.wires.flatMap((id) => r.paint[id] ?? r.parts[id])) })),
      shared: r.initialSharedRuns || [],
    },
  });
}
console.log(JSON.stringify(results));
"""


def _wire_overlaps(node, cases):
    script = WIRE_OVERLAP_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    return node_output(node, script, cases)


def _covered_intervals(paths, *, once=False):
    """The union of intervals along each line of the routes, with no repeated stroke if asked."""
    spans = {}
    for points in paths:
        for p, q in zip(points, points[1:]):
            x, y = round(p["x"], 3), round(p["y"], 3)
            u, v = round(q["x"], 3), round(q["y"], 3)
            assert (x == u) != (y == v), (p, q)
            line, span = (("y", y), (x, u)) if y == v else (("x", x), (y, v))
            spans.setdefault(line, []).append(sorted(span))
    covered = {}
    for line, segments in spans.items():
        runs = []
        for lo, hi in sorted(segments):
            if runs and lo <= runs[-1][1]:
                assert not once or lo == runs[-1][1], (line, segments)
                runs[-1][1] = max(runs[-1][1], hi)
            else:
                runs.append([lo, hi])
        covered[line] = runs
    return covered


def _assert_paint_preserves_routes(result):
    common = result["shared"] + result["bundles"]
    painted = [path for wire in result["wires"] for path in wire["paint"]]
    painted.extend(run["points"] for run in common)
    assert _covered_intervals(painted, once=True) == _covered_intervals(
        [wire["route"] for wire in result["wires"]]
    )
    for wire in result["wires"]:
        paths = wire["paint"] + [run["points"] for run in common if wire["id"] in run["members"]]
        assert _covered_intervals(paths, once=True) == _covered_intervals([wire["route"]])


def _assert_initial_paint_preserves_routes(initial):
    routes, shared = initial["routes"], initial["shared"]
    painted = [path for route in routes for path in route["paint"]]
    painted.extend(run["points"] for run in shared)
    assert _covered_intervals(painted, once=True) == _covered_intervals(
        [path for route in routes for path in route["paths"]]
    )
    for route in routes:
        pieces = route["paint"] + [run["points"] for run in shared if route["id"] in run["routes"]]
        assert _covered_intervals(pieces, once=True) == _covered_intervals(route["paths"])


def test_forward_initial_draws_overlapping_route_segments_once(node):
    folder = model.open_folder(DURABLES_MODEL)
    source = recipe.Source("recipe", "declaration/spec.yml")
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, source, restriction, initial=True).shown
    graph = next(graph for graph in shown.collection["graphs"] if graph["id"] == "forward initial diagram")
    cases = [
        {"graph": graph, "direction": direction, "depth": depth,
         "order": ["tenure", "keeper_cons", "adjuster_cons", "bequest"]}
        for depth in (0, 1, 2, 3) for direction in ("RIGHT", "DOWN")
    ]
    for result in _wire_overlaps(node, cases):
        _assert_initial_paint_preserves_routes(result["initial"])


def test_forward_initial_shared_run_names_only_its_participating_routes(node):
    paths = {"a": [[0, 0], [10, 0]], "b": [[5, 0], [20, 0]], "c": [[8, 0], [25, 0]]}
    (result,) = _wire_overlaps(node, [{"paths": paths, "initial": True}])
    initial = result["initial"]
    _assert_initial_paint_preserves_routes(initial)
    assert [(run["points"][0]["x"], run["points"][-1]["x"], set(run["routes"])) for run in initial["shared"]] == [
        (5, 8, {"route:a", "route:b"}),
        (8, 10, {"route:a", "route:b", "route:c"}),
        (10, 20, {"route:b", "route:c"}),
    ]


def test_bequest_writers_share_one_receiving_entrance_and_painted_tail(node):
    folder = model.open_folder(DURABLES_MODEL)
    source = recipe.Source("recipe", "declaration/spec.yml")
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, source, restriction).shown
    graph = next(graph for graph in shown.collection["graphs"] if graph["id"] == "forward")
    cases = [
        {"graph": graph, "direction": direction, "depth": depth,
         "order": ["tenure", "keeper_cons", "adjuster_cons", "bequest"],
         "reader": "periods[0]/bequest/arvl_to_dcsn:Pushforward"}
        for depth in (2, 3) for direction in ("RIGHT", "DOWN")
    ]
    for case, result in zip(cases, _wire_overlaps(node, cases), strict=True):
        wires = result["wires"]
        assert {wire["from"].split("/")[1] for wire in wires} == {"adjuster_cons", "keeper_cons"}
        assert len(wires) == 2 and not result["bundles"], result
        if case["depth"] == 3:
            entrances = [
                [piece for piece in wire["pieces"]
                 if piece.startswith("periods[0]/bequest___group___::hin::")]
                for wire in wires
            ]
            assert entrances[0] and entrances[0] == entrances[1], entrances
        (tail,) = [run for run in result["shared"] if run["terminal"]]
        assert set(tail["members"]) == {wire["id"] for wire in wires}
        assert all(wire["route"][-1] in (tail["points"][0], tail["points"][-1]) for wire in wires)
        _assert_paint_preserves_routes(result)


def test_three_writers_share_only_their_own_runs_before_the_period_mapping(node):
    writers = [f"periods[1]/source_{i}/push/g" for i in range(3)]
    reader = "periods[0]/reader/pull/g"
    graph = {
        "id": "forward",
        "groupNodeConfigs": PERIODS["groupNodeConfigs"],
        "nodes": [
            *[_node(writer, outputs=("out",)) for writer in writers],
            _node(reader, reads=[(writer, "out") for writer in writers]),
        ],
    }
    cases = [
        {"graph": graph, "direction": direction, "depth": 1,
         "order": ["source_0", "source_1", "source_2", "reader"], "reader": reader}
        for direction in ("RIGHT", "DOWN")
    ]
    for result in _wire_overlaps(node, cases):
        wires = result["wires"]
        assert len(wires) == 3
        ids = {wire["id"] for wire in wires}
        (mapping,) = result["bundles"]
        assert set(mapping["members"]) == ids
        assert all(wire["route"][-1] == mapping["points"][-1] for wire in wires)
        assert result["shared"]
        assert all(len(run["members"]) == 2 and set(run["members"]) < ids
                   and not run["terminal"] for run in result["shared"])
        _assert_paint_preserves_routes(result)


def test_shared_paths_can_cover_a_whole_wire_and_ignore_point_contacts(node):
    paths = {
        "a": [[0, 0], [10, 0]],
        "b": [[0, 0], [10, 0]],
        "separate input": [[0, 0], [10, 0]],
        "touch from left": [[0, 20], [10, 20], [10, 25], [20, 25]],
        "touch from below": [[0, 30], [20, 30], [20, 25]],
    }
    groups = [["a", "b"], ["touch from left", "touch from below"]]
    (result,) = _wire_overlaps(node, [{"paths": paths, "groups": groups}])
    (shared,) = result["shared"]
    assert set(shared["members"]) == {"a", "b"} and shared["terminal"]
    assert {wire["id"] for wire in result["wires"] if not wire["paint"]} == {"a", "b"}
    unaffected = [wire for wire in result["wires"] if wire["id"] not in shared["members"]]
    assert all(wire["paint"] == [wire["route"]] for wire in unaffected)
    # The coincident path into a different input still represents its own wire.
    result["wires"] = [wire for wire in result["wires"] if wire["id"] != "separate input"]
    _assert_paint_preserves_routes(result)


def test_the_wires_of_an_adjacent_pair_share_one_piece_and_the_control_stands_under_it(node):
    """Two or more wires from occurrences of one period to one reading port
    in the next are a bundle: each leaves the writing period at a border
    port of its own, on a piece of the root of its own, the pieces meet on
    one vertical run in the gap and share the run into the reading period,
    which is drawn once, printing no label; each wire's own route ends
    where the wires meet (K-D5; design pass 13 §1, rule 4). The control
    that adds a period, between two periods, is no box of ELK's graph and
    prints the Codicon `add` and `Period`, as wide as the icon and its word
    with 4 px at each side and 24 px high (design pass 13 §2, rule 8; unit
    K's decision K-D14): it stands in the gap between the two period
    layers, under the shared route; the root's spacing between its periods
    keeps the control's room in every gap, so that no piece keeps room for
    a label (K-D13; design pass 13 §2, rule 9); the control at the
    earliest end is a box of ELK's graph of the same size. Where one wire
    alone joins two periods, its piece is its own and has the control in
    the gap under it; where no wire joins them, an edge of the root that no
    wire draws keeps the two periods' order and the control stands under
    it; a bundle whose port carries no join text prints no label."""
    script = BUNDLE_SCRIPT % {
        "script": json.dumps(str(LAYOUT)),
        "elk": json.dumps(str(ELK)),
    }
    built = node_output(node, script, _joined(PERIODS, "a_nxt_kp → a; a_nxt_adj → a"))
    assert built["words"] == ["Period", "Stage"]
    # one piece of the root for each wire, none keeping room for a label; the root's spacing is the room
    assert sorted(built["root"]) == [
        ["periods[1]", "periods[0]", False, None],
        ["periods[1]", "periods[0]", False, None],
        ["periods[2]", "periods[1]", False, None],
        ["periods[2]", "periods[1]", False, None],
        ["periods[2]", "periods[1]", False, None],
    ]
    assert built["room"] == [] and built["spacing"] == ROOM
    assert "add-period::earliest end" in built["children"]
    earliest = built["places"]["add-period::earliest end"]
    assert {key: earliest[key] for key in CONTROL} == CONTROL
    assert earliest["ax"] + earliest["width"] < built["places"]["periods[2]___group___"]["ax"]
    by_pair = {(bundle["from"], bundle["to"]): bundle for bundle in built["bundles"]}
    assert set(by_pair) == {("periods[2]", "periods[1]"), ("periods[1]", "periods[0]")}
    assert by_pair["periods[2]", "periods[1]"]["wires"] == 3
    assert by_pair["periods[1]", "periods[0]"]["wires"] == 2
    places = built["places"]
    for (earlier, later), bundle in by_pair.items():
        # each wire's own route ends where the bundle's wires meet, from which the
        # shared route, drawn once and printing no label, runs into the reader's
        # one arrival port (design pass 13 §1, rule 4)
        assert bundle["shared"] and bundle["label"] is None
        route, first = bundle["route"], bundle["route"][0]
        assert all(len(part) == 1 and part[0][-1] == first for part in bundle["parts"])
        assert f"add-period::between {earlier} and {later}" not in built["children"]
        _in_the_gap(places, earlier, later, route)

    alone = json.loads(json.dumps(PERIODS))
    arrive = next(n for n in alone["nodes"] if n["id"] == "periods[0]/tenure/arrive/g")
    arrive["incomingEdges"] = arrive["incomingEdges"][:1]
    built = node_output(node, script, alone)
    # the fixture's reading ports carry no join text; no piece keeps room for a
    # label, the root's spacing keeping the control's room in every gap
    # (design pass 13 §2, rule 9)
    assert sorted(built["root"]) == [
        ["periods[1]", "periods[0]", False, None],
        ["periods[2]", "periods[1]", False, None],
        ["periods[2]", "periods[1]", False, None],
        ["periods[2]", "periods[1]", False, None],
    ]
    assert built["spacing"] == ROOM
    (bundle,) = built["bundles"]
    assert (bundle["from"], bundle["to"], bundle["label"]) == ("periods[2]", "periods[1]", None)
    _in_the_gap(built["places"], "periods[2]", "periods[1]", bundle["route"])
    assert not any(child.startswith("add-period::between") for child in built["children"])
    # the control between periods[1] and periods[0], whose gap the piece of
    # the one wire alone crosses
    _in_the_gap(built["places"], "periods[1]", "periods[0]")

    apart = json.loads(json.dumps(PERIODS))
    arrive = next(n for n in apart["nodes"] if n["id"] == "periods[0]/tenure/arrive/g")
    arrive["incomingEdges"] = []
    built = node_output(node, script, apart)
    # no wire joins periods[1] to periods[0]: an edge of the root keeps the
    # control's room and the two periods' order, and the control stands in
    # the gap under it
    assert sorted(built["root"]) == [["periods[2]", "periods[1]", False, None]] * 3
    assert built["room"] == [["add-period::between periods[1] and periods[0]::room", None]]
    assert built["spacing"] == ROOM
    _in_the_gap(built["places"], "periods[1]", "periods[0]")


# the Node module: runs the layout script, builds the graph JSON read on
# standard input with the layers it names open, in the direction it names
# for every layer or, where it names none, in the directions the graph
# configures, every card unfolded as it says, and prints the layout's
# geometry `G` and, for each closed layer's box, the face its port labels
# are printed in, the top of its name, its size, each reading and writing
# port as [id, printed text, x, y, side, whether no join reaches its field],
# and the texts a card prints; a text is 7 px wide for each of its
# characters
FRAME_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const built = L.build(m, new Set(given.open), { direction: given.direction, unfold: given.unfold },
                      (text) => Array.from(text || "").length * 7);
const port = (p) => [p.id, p.text || "", p.x, p.y, p.side, !!p.open];
const boxes = {};
for (const box of Object.values(built.boxes)) {
  if (box.type !== "layer" || box.open) continue;
  const g = box.geom;
  boxes[box.namespace] = { face: g.face, nameTop: g.nameTop, width: g.width, height: g.height,
                           ins: g.ins.map(port), outs: g.outs.map(port), texts: g.texts || null };
}
console.log(JSON.stringify({ G: L.G, boxes }));
"""


def _port(port_id: str, label: str, unjoined: bool = False) -> dict:
    """A port of the graph JSON with the label `label`, marked `unjoined`
    where `unjoined` holds, as the exporter marks a field no join reaches."""
    attrs = [{"key": "label", "value": label}]
    parts = port_id.rsplit("/", 1)[-1].split(":")
    if len(parts) == 4 and parts[0] in ("joined", "unjoined"):
        attrs.extend({"key": key, "value": value} for key, value in
                     (("role", "state"), ("perch", parts[2]), ("field", parts[3])))
    if unjoined:
        attrs.append({"key": "unjoined", "value": "true"})
    return {"id": port_id, "attrs": attrs}


def _occurrence(h: int, cntn_label: str, reads=None, b_unjoined: bool = False) -> list[dict]:
    """The nodes of the stage occurrence `periods[h]/cons` of a forward
    trellis graph, as the exporter writes them (spec 0.4 §3.4): its own
    `Inputs`, whose field port is the arrival field `m`; its builder `push`,
    which reads the arrival perch's measure, from the output `reads` names,
    and writes the continuation perch's, labeled `cntn_label`; and its own
    `Outputs`, whose field ports are the continuation fields `a` and `b`,
    `b` marked unjoined where `b_unjoined` holds."""
    at = f"periods[{h}]/cons"
    b = "unjoined" if b_unjoined else "joined"
    return [
        {
            "id": f"{at}/GraphInputs",
            "label": "Inputs",
            "namespace": at,
            "inputsMetadata": [_port(f"{at}/joined:cons:arvl:m", "m≺")],
        },
        {
            "id": f"{at}/push:Pushforward",
            "label": "𝑔≻∗μ",
            "namespace": f"{at}/push",
            "attrs": [{"key": "kind", "value": "operator"}],
            "inputsMetadata": [_port(f"{at}/cons:measure:arvl", "μ≺(m_now)")],
            "outputsMetadata": [_port(f"{at}/cons:measure:cntn", cntn_label)],
            "incomingEdges": [
                {
                    "sourceNodeId": writer,
                    "sourceNodeOutputId": output,
                    "targetNodeInputId": f"{at}/cons:measure:arvl",
                }
                for writer, output in ([reads] if reads else [])
            ],
        },
        {
            "id": f"{at}/GraphOutputs",
            "label": "Outputs",
            "namespace": at,
            "outputsMetadata": [
                _port(f"{at}/joined:cons:cntn:a", "a≻"),
                _port(f"{at}/{b}:cons:cntn:b", "b≻", unjoined=b_unjoined),
            ],
        },
    ]


# two periods of a forward trellis graph in the directions the exporter
# configures, each holding the occurrence `cons`, the builder of periods[0]
# reading the continuation measure of periods[1], whose label is the longest
# label of the graph, and the field `b` of periods[0] unjoined
FRAMES = {
    "groupNodeConfigs": PERIODS["groupNodeConfigs"],
    "nodes": [
        *_occurrence(1, "μ≻(a_next, b_next)"),
        *_occurrence(
            0,
            "μ≻(a, b)",
            reads=("periods[1]/cons/push:Pushforward", "periods[1]/cons/cons:measure:cntn"),
            b_unjoined=True,
        ),
    ],
}
# the wire port by which the measure of periods[1] crosses into periods[0]
CROSSING = "periods[1]/cons/push:Pushforward|periods[1]/cons/cons:measure:cntn"


# the occurrence `fork` of a forward trellis graph's one period, whose stage
# branches: its own `Inputs` reads `a`, which no join reaches, and `h`; its
# own `Outputs` writes, by the branch `keep`, `w_kp` and `h_kp`, which no join
# reaches, and, by the branch `adjust`, `w_adj`, which no join reaches, and
# `z_adj`
FORK = {
    "groupNodeConfigs": PERIODS["groupNodeConfigs"],
    "nodes": [
        {
            "id": "periods[0]/fork/GraphInputs",
            "label": "Inputs",
            "namespace": "periods[0]/fork",
            "inputsMetadata": [
                _port("periods[0]/fork/unjoined:fork:arvl:a", "a≺", unjoined=True),
                _port("periods[0]/fork/joined:fork:arvl:h", "h≺"),
            ],
        },
        {
            "id": "periods[0]/fork/GraphOutputs",
            "label": "Outputs",
            "namespace": "periods[0]/fork",
            "outputsMetadata": [
                _port("periods[0]/fork/unjoined:fork:cntn:w_kp", "keep: w_kp≻", unjoined=True),
                _port("periods[0]/fork/unjoined:fork:cntn:h_kp", "keep: h_kp≻", unjoined=True),
                _port("periods[0]/fork/unjoined:fork:cntn:w_adj", "adjust: w_adj≻", unjoined=True),
                _port("periods[0]/fork/joined:fork:cntn:z_adj", "adjust: z_adj≻"),
            ],
        },
    ],
}


def _cards(node, graph: dict, opened: list, direction=None, unfold=None) -> dict:
    """The closed layers of `graph` laid out with the layers `opened` open
    and the cards `unfold` names unfolded (FRAME_SCRIPT), with the layout's
    geometry under `G`."""
    script = FRAME_SCRIPT % {"script": json.dumps(str(LAYOUT))}
    given = {"graph": graph, "open": opened, "direction": direction, "unfold": unfold}
    return node_output(node, script, given)


def _texts(card: dict) -> list:
    """The texts the card `card` prints, each [writes, place, branch, text],
    the place the text's center across its rows, or along its edge where
    the card is laid out downward."""
    return [
        [t["writes"], t["x"] if "x" in t else t["y"], t["branch"], t["text"]]
        for t in card["texts"]
    ]


def test_a_closed_occurrence_is_a_card_that_prints_a_field_s_name_where_no_join_reaches_it(node):
    """A closed stage occurrence of a trellis graph is a card (AAS, L-D16
    and L-D25; design pass 7 §3): it carries, beside the ports of the wires
    that cross its border, every field port of its own `Inputs` and
    `Outputs` (K-D15), the cables' ports standing on its edges in their
    place (design pass 10 §6): on its writing side one port per
    continuation branch, the port of the wire that leaves by the branch or
    a port of the card's own, `branch:<label>`, where no wire does, and on
    its reading side one port for the arrival tuple, the wire's or the
    card's own, `arrival`. Laid out to the
    right, the card is G.cardH high at rest, its socket and its plugs on
    the axis G.cardAxis; under its strip each side's rows, G.frameRow high,
    one for each field no join reaches, printing its name with no perch's
    sign, the writing fields of one branch on one row after their branch
    word and a colon, `keep: w_kp, h_kp`; no count is printed. The card's
    ports stand on its axis, their labels in their hovers. The card is as
    high as its rows under the strip and G.framePad, and as wide as its
    name with G.cardChrome on the step of G.cardStep, its rows with
    G.cardInset at each side and G.fieldGap between them, and G.frameW
    (design pass 13 §2). Unfolded, every field port has a row with its name
    under the band, its branch word on the first row of its branch alone
    (the fix wave Q3a of unit Q, item 12; B26), a wire's label standing in
    its port's hover alone (design pass 7 §3). Laid out downward,
    each side's texts stand in one row along its edge, the name under the
    reading row. A closed period keeps the unjoined ports of its
    occurrences alone and prints a writing field's label (J-D47)."""
    periods = ["periods[0]", "periods[1]"]
    found = _cards(node, FRAMES, periods)
    G, boxes = found["G"], found["boxes"]
    assert set(boxes) == {"periods[0]/cons", "periods[1]/cons"}
    late, early = boxes["periods[0]/cons"], boxes["periods[1]/cons"]
    axis, row, pad, inset = G["cardAxis"], G["frameRow"], G["framePad"], G["cardInset"]
    # the rows of printed text start under the strip and the room beneath it
    rows_top = G["cardStripY"] + G["cardStripH"] + 1
    middle = rows_top + row / 2
    assert "namesScale" not in G
    # the reading wire's port, the arrival tuple's, at the middle of the
    # name's row, the card's part above its first row; one port of the card's
    # own for its one continuation branch, which no wire leaves by, and the
    # unjoined `b` in a row
    assert [p[0] for p in late["ins"]] == [CROSSING]
    assert [p[2:] for p in late["ins"]] == [[0, axis, "WEST", False]]
    assert [p[0] for p in late["outs"]] == ["branch:"]
    width = late["width"]
    assert [p[2:] for p in late["outs"]] == [[width, axis, "EAST", True]]
    assert _texts(late) == [[True, middle, "", "b"]]
    assert late["height"] == rows_top + row + pad
    # the name `cons` with the card's chrome, on the step of 8 px, at least the
    # least width (design pass 13 §2, rule 6)
    name = G["cardStep"] * math.ceil((4 * 7 + G["cardChrome"]) / G["cardStep"])
    assert width == max(G["frameW"], name) == G["frameW"] == 80
    # no row: the writing wire's port, the branch's, at the middle of the
    # whole card, which is its name's row and its padding, and the card's
    # own arrival port, which no wire reaches
    assert early["height"] == G["cardH"] == rows_top + pad
    assert [p[3] for p in early["outs"]] == [axis]
    assert [(p[0], p[3], p[5]) for p in early["ins"]] == [("arrival", axis, True)]
    assert _texts(early) == []

    # unfolded, every field's name in a row under the band, a wire's label
    # standing in its port's hover alone (design pass 7 §3; design pass 13 §2,
    # rule 7)
    unfolded = _cards(node, FRAMES, periods, unfold=True)["boxes"]
    late, early = unfolded["periods[0]/cons"], unfolded["periods[1]/cons"]
    band_middle = G["cardStripY"] + G["cardBandH"] + row / 2
    assert _texts(late) == [
        [False, band_middle, "", "m"],
        [True, band_middle, "", "a"],
        [True, band_middle + row, "", "b"],
    ]
    assert [p[3] for p in early["outs"]] == [axis]
    assert early["height"] == G["cardStripY"] + G["cardBandH"] + 2 * row + pad
    # the rows of one-letter names leave the card at its least width
    assert early["width"] == G["frameW"]
    # one card unfolded by its namespace, the other folded
    one = _cards(node, FRAMES, periods, unfold=["periods[1]/cons"])["boxes"]
    assert one["periods[1]/cons"]["height"] == early["height"]
    assert one["periods[0]/cons"]["height"] == rows_top + row + pad

    # a branching stage's unjoined writing fields, one row per branch with its
    # branch word once; one port per branch, G.cablePitch apart or closer
    # where the name's row is shorter, and one arrival port (design pass 10
    # §6)
    fork = _cards(node, FORK, ["periods[0]"])["boxes"]["periods[0]/fork"]
    assert _texts(fork) == [
        [False, middle, "", "a"],
        [True, middle, "keep", "w_kp, h_kp"],
        [True, middle + row, "adjust", "w_adj"],
    ]
    pitch = G["cablePitch"]
    assert [(p[0], p[3], p[5]) for p in fork["outs"]] == [
        ("branch:keep", axis - pitch / 2, True),
        ("branch:adjust", axis + pitch / 2, True),
    ]
    assert [(p[0], p[3], p[5]) for p in fork["ins"]] == [("arrival", axis, True)]
    assert fork["height"] == rows_top + 2 * row + pad
    # the widest rows, `a` and the branch `keep` with its colon and its two
    # fields, with the inset at each side and the room between a reading and a
    # writing text
    assert fork["width"] == max(G["frameW"], 7 + len("keep: w_kp, h_kp") * 7 + 2 * inset + G["fieldGap"])
    unfolded_fork = _cards(node, FORK, ["periods[0]"], unfold=True)["boxes"]["periods[0]/fork"]
    assert [t[2:4] for t in _texts(unfolded_fork) if t[0]] == [
        ["keep", "w_kp"],
        ["", "h_kp"],
        ["adjust", "w_adj"],
        ["", "z_adj"],
    ]

    # laid out downward, each side's texts in one row along its edge, the
    # name under the reading row, the marks with no row on the edge
    down = _cards(node, FRAMES, periods, direction="DOWN")["boxes"]
    late, early = down["periods[0]/cons"], down["periods[1]/cons"]
    assert early["nameTop"] == G["cardNameTop"] and early["height"] == G["cardH"]
    assert [p[3:5] for p in early["ins"]] == [[0, "NORTH"]]
    assert [p[3:5] for p in early["outs"]] == [[early["height"], "SOUTH"]]
    assert _texts(early) == []
    assert late["nameTop"] == G["cardNameTop"] and late["height"] == G["cardH"] + row
    assert [p[3:5] for p in late["ins"]] == [[0, "NORTH"]]
    assert [[t[0], t[3]] for t in _texts(late)] == [[True, "b"]]

    # a closed period keeps the unjoined ports of the occurrences inside it
    # alone, with J-D47's label in the port face
    closed = _cards(node, FRAMES, ["periods[1]", "periods[1]/cons"])["boxes"]
    assert closed["periods[0]"]["face"] is None
    assert [(p[0], p[1]) for p in closed["periods[0]"]["outs"]] == [
        ("periods[0]/cons/unjoined:cons:cntn:b", "b≻")
    ]


# the Node module: runs the layout script, builds the graph JSON read on
# standard input with the layers it names open, in the direction it names
# for every layer or, where it names none, in the directions the graph
# configures, and prints the layout's geometry `G` and, for each node's
# box, the direction the box is laid out in, the face its port labels are
# printed in, the top of its name, its size and each reading and writing
# port as [id, printed text, x, y, side]; a text is 7 px wide for each of
# its characters
BOXES_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const built = L.build(m, new Set(given.open), { direction: given.direction },
                      (text) => Array.from(text || "").length * 7);
const port = (p) => [p.id, p.text || "", p.x, p.y, p.side];
const boxes = {};
for (const box of Object.values(built.boxes)) {
  if (!box.node) continue;
  const g = box.geom;
  boxes[box.id] = { dir: box.dir, face: g.face, nameTop: g.nameTop, width: g.width,
                    height: g.height, ins: g.ins.map(port), outs: g.outs.map(port) };
}
console.log(JSON.stringify({ G: L.G, boxes }));
"""
# the two periods of FRAMES with a backward occurrence's own `Outputs` added
# to periods[0]/cons, which reads the policy that its builder `push` writes
# at a port that is no field's (the backward trellis graph's own
# `Outputs`), and a stage graph's own `Inputs` at the root, whose output
# port is no field's
OWN_BOXES = {
    "groupNodeConfigs": FRAMES["groupNodeConfigs"],
    "nodes": [
        *FRAMES["nodes"],
        {
            "id": "periods[0]/cons/GraphPolicy",
            "label": "Outputs",
            "namespace": "periods[0]/cons",
            "inputsMetadata": [_port("policy:Evaluation:c:result", "𝑐(m)")],
            "incomingEdges": [
                {
                    "sourceNodeId": "periods[0]/cons/push:Pushforward",
                    "sourceNodeOutputId": "periods[0]/cons/cons:measure:cntn",
                    "targetNodeInputId": "policy:Evaluation:c:result",
                }
            ],
        },
        {
            "id": "GraphInputs",
            "label": "Inputs",
            "namespace": "",
            "outputsMetadata": [_port("cons:measure:arvl", "μ≺(m)")],
        },
    ],
}


def test_an_open_occurrence_s_inputs_and_outputs_print_its_fields_one_row_per_port(node):
    """The own `Inputs` and `Outputs` of an open stage occurrence of the
    forward trellis graph drawn in full, a builder of it open, which an
    occurrence whose builders are all closed is not (AAS, L-D7), print its
    arrival and its continuation fields as
    its closed frame prints them (unit K, Task 21; K-D15, row K-I105): the
    label the graph JSON gives each field port, in the face of the box's
    name, a frame's name, `frame`, in a trellis graph (AAS, M-D15), laid
    out in the direction of the period the occurrence stands in. To the right, as the exporter configures a
    period, each port has a row of G.fieldRow under the name, the reading
    ports on the left edge and the writing ports on the right edge, the box
    as high as its name and its rows and as wide as the larger of its least
    width, its name and its widest label, with the padding; laid out
    downward, each side's labels stand in one row along its edge. A builder
    inside the occurrence, an occurrence's own `Outputs` that holds no
    field's port and a stage graph's own `Inputs` print no port label, the
    two boundaries among them, the occurrence's `Outputs` and the graph's
    `Inputs`, their names centered on their lines (M-D15)."""
    script = BOXES_SCRIPT % {"script": json.dumps(str(LAYOUT))}
    # the two occurrences open, each with its builder `push` open, so that
    # neither is drawn compact
    opened = [
        "periods[0]",
        "periods[1]",
        "periods[0]/cons",
        "periods[1]/cons",
        "periods[0]/cons/push",
        "periods[1]/cons/push",
    ]
    found = node_output(node, script, {"graph": OWN_BOXES, "open": opened, "direction": None})
    G, boxes = found["G"], found["boxes"]
    first = G["padTop"] + G["labelH"] + 2
    rows = [round(first + i * G["fieldRow"] + G["fieldRow"] / 2 + 1e-9) for i in range(2)]
    inputs, outputs = boxes["periods[0]/cons/GraphInputs"], boxes["periods[1]/cons/GraphOutputs"]
    for box in (inputs, outputs):
        assert (box["dir"], box["face"], box["nameTop"]) == ("RIGHT", "frame", G["padTop"])
    assert inputs["ins"] == [["periods[0]/cons/joined:cons:arvl:m", "m≺", 0, rows[0], "WEST"]]
    assert inputs["outs"] == []
    assert inputs["height"] == first + G["fieldRow"] + G["padBottom"]
    # the name `Inputs` and its two borders, under the least width of a
    # graph's own `Inputs`
    assert 6 * 7 + 2 + 2 * G["padX"] < G["boundaryW"] == inputs["width"]
    assert outputs["ins"] == []
    assert outputs["outs"] == [
        ["periods[1]/cons/joined:cons:cntn:a", "a≻", outputs["width"], rows[0], "EAST"],
        ["periods[1]/cons/joined:cons:cntn:b", "b≻", outputs["width"], rows[1], "EAST"],
    ]
    assert outputs["height"] == first + 2 * G["fieldRow"] + G["padBottom"]
    # the builder inside the occurrence, the occurrence's `Outputs` that
    # reads its policy, and the stage graph's `Inputs` are unchanged
    builder = boxes["periods[0]/cons/push:Pushforward"]
    policy, graph_inputs = boxes["periods[0]/cons/GraphPolicy"], boxes["GraphInputs"]
    assert builder["dir"] == policy["dir"] == "DOWN" and graph_inputs["dir"] == "RIGHT"
    for box in (builder, policy, graph_inputs):
        assert box["face"] is None
        assert [p[1] for p in box["ins"] + box["outs"]] == [""] * len(box["ins"] + box["outs"])
    assert builder["nameTop"] == G["padTop"]
    for box in (policy, graph_inputs):
        assert box["nameTop"] == (box["height"] - G["frameLine"]) / 2, box
    assert [p[4] for p in policy["ins"]] == ["NORTH"]

    # laid out downward, each side's labels stand in one row along its edge,
    # the name of `Inputs` under its row
    down = node_output(node, script, {"graph": OWN_BOXES, "open": opened, "direction": "DOWN"})
    inputs = down["boxes"]["periods[0]/cons/GraphInputs"]
    outputs = down["boxes"]["periods[1]/cons/GraphOutputs"]
    for box in (inputs, outputs):
        assert (box["dir"], box["face"]) == ("DOWN", "frame")
    assert inputs["nameTop"] == G["padTop"] + G["fieldRow"] and outputs["nameTop"] == G["padTop"]
    assert [p[1:] for p in inputs["ins"]] == [["m≺", inputs["width"] // 2, 0, "NORTH"]]
    assert [p[1] for p in outputs["outs"]] == ["a≻", "b≻"]
    assert {(p[3], p[4]) for p in outputs["outs"]} == {(outputs["height"], "SOUTH")}


def _two_builders(h: int, reads=None) -> list[dict]:
    """The nodes of the stage occurrence `periods[h]/cons` of a forward
    trellis graph with two builders, the graph JSON listing `solve`, which
    joins decision to continuation, before `arrive`, which joins arrival to
    decision: its own `Inputs`, whose field port is `m`; `solve`, reading
    the decision measure `arrive` writes and writing the continuation
    measure; `arrive`, reading the arrival measure from the output `reads`
    names; and its own `Outputs`, whose field ports are `a` and `b`."""
    at = f"periods[{h}]/cons"
    return [
        {
            "id": f"{at}/GraphInputs",
            "label": "Inputs",
            "namespace": at,
            "inputsMetadata": [_port(f"{at}/joined:cons:arvl:m", "m≺")],
        },
        {
            "id": f"{at}/solve:Pushforward",
            "label": "𝑔≻∗μ",
            "namespace": f"{at}/solve",
            "attrs": [{"key": "kind", "value": "operator"}],
            "inputsMetadata": [_port(f"{at}/cons:measure:dcsn", "μ(m_d)")],
            "outputsMetadata": [_port(f"{at}/cons:measure:cntn", "μ≻(a, b)")],
            "incomingEdges": [
                {
                    "sourceNodeId": f"{at}/arrive:Pushforward",
                    "sourceNodeOutputId": f"{at}/cons:measure:dcsn",
                    "targetNodeInputId": f"{at}/cons:measure:dcsn",
                }
            ],
        },
        {
            "id": f"{at}/arrive:Pushforward",
            "label": "𝑔≺∗μ",
            "namespace": f"{at}/arrive",
            "attrs": [{"key": "kind", "value": "operator"}],
            "inputsMetadata": [_port(f"{at}/cons:measure:arvl", "μ≺(m)")],
            "outputsMetadata": [_port(f"{at}/cons:measure:dcsn", "μ(m_d)")],
            "incomingEdges": [
                {
                    "sourceNodeId": writer,
                    "sourceNodeOutputId": output,
                    "targetNodeInputId": f"{at}/cons:measure:arvl",
                }
                for writer, output in ([reads] if reads else [])
            ],
        },
        {
            "id": f"{at}/GraphOutputs",
            "label": "Outputs",
            "namespace": at,
            "outputsMetadata": [
                _port(f"{at}/joined:cons:cntn:a", "a≻"),
                _port(f"{at}/joined:cons:cntn:b", "b≻"),
            ],
        },
    ]


# two periods of a forward trellis graph, each holding the occurrence `cons`
# with two builders, the builder `arrive` of periods[0] reading the
# continuation measure of periods[1]
COMPACT = {
    "groupNodeConfigs": PERIODS["groupNodeConfigs"],
    "nodes": [
        *_two_builders(1),
        *_two_builders(
            0, reads=("periods[1]/cons/solve:Pushforward", "periods[1]/cons/cons:measure:cntn")
        ),
    ],
}
# the records Python gives of the builders' pairs (`trellis.builder_records`)
COMPACT_RECORDS = {
    f"periods[{h}]/cons/{name}": record
    for h in (0, 1)
    for name, record in (
        (
            "arrive",
            {"pair": "arvl,dcsn", "place": 0, "signs": "≺∼", "words": "arrival to decision"},
        ),
        (
            "solve",
            {"pair": "dcsn,cntn", "place": 1, "signs": "∼≻", "words": "decision to continuation"},
        ),
    )
}
# the Node module: runs the layout script, builds the graph JSON read on
# standard input with the layers it names open, in the direction it names
# for every layer or, where it names none, in the directions the graph
# configures, with the builders' records it gives, lays it out with ELK and
# reads ELK's answer; prints the geometry `G`, the occurrences drawn
# compact, each frame, compact or closed, with its size, the top of its
# name, its ports as [id, printed text, x, y, side], the places of its
# builders' segments and whether it is open, the face of a closed layer's
# labels, each builder's segment with its frame, its place and size in the
# frame and its record's pair, the boxes ELK lays out, the places `read`
# answers for the boxes ELK lays out and for the builders' segments, and
# each wire's two ends; a text is 7 px wide for each of its characters
COMPACT_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const options = { direction: given.direction, builders: given.builders, unfold: given.unfold };
const measure = (text) => Array.from(text || "").length * 7;
const built = L.build(m, new Set(given.open), options, measure);
const read = L.read(built, await new ELK().layout(JSON.parse(JSON.stringify(built.elk))));
const port = (p) => [p.id, p.text || "", p.x, p.y, p.side];
const frames = {}, builders = {};
for (const box of Object.values(built.boxes)) {
  if (box.type === "builder") {
    const pair = box.record && box.record.pair;
    builders[box.namespace] = { parent: box.parent, at: box.at, pair };
  } else if (box.type === "layer" && (box.compact || !box.open)) {
    const g = box.geom;
    frames[box.namespace] = { open: box.open, face: g.face, width: g.width, height: g.height,
                              nameTop: g.nameTop, ins: g.ins.map(port), outs: g.outs.map(port),
                              builders: g.builders || [] };
  }
}
const laid = [];
(function walk(node) {
  for (const child of node.children || []) { laid.push(child.id); walk(child); }
})(built.elk);
console.log(JSON.stringify({ G: L.G, compact: Array.from(built.compact).sort(), frames, builders,
                             laid, places: read.place, builderPlaces: read.builders,
                             wires: built.wires.map((w) => [w.source, w.target]) }));
"""


def _compact_layout(node, opened, direction=None, builders=COMPACT_RECORDS, unfold=None) -> dict:
    """The layout of COMPACT with the layers `opened` open and the cards
    `unfold` names unfolded (COMPACT_SCRIPT)."""
    script = COMPACT_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    given = {
        "graph": COMPACT,
        "open": opened,
        "direction": direction,
        "builders": builders,
        "unfold": unfold,
    }
    return node_output(node, script, given)


def test_an_open_occurrence_whose_builders_are_closed_is_drawn_compact(node):
    """An open stage occurrence of a trellis graph none of whose builders is
    open is drawn compact (AAS, L-D7): ELK lays it out as its closed card,
    with the same ports, and stands for every node inside it, so that the
    wires between occurrences end at its card. Under its name stands the
    strip of its builders, G.cardStripH high at G.cardStripY (design pass 13
    §2; AAS, L-D25; design pass 7 §3): one segment for each builder, which
    ELK does not lay out, the segments of equal width G.cardSegmentGap
    apart from G.cardInset inside the card's left edge to G.cardStripRight
    inside its right edge; a card whose fields are all joined is G.cardH
    high, 32 px, and its closed card is the same drawing, strip and ports
    alike. While the card is unfolded, the strip is the band of
    G.cardBandH, each segment as wide as its id with G.cardIdPad and its
    signs with G.cardSignsPad, rounded up to G.cardStep, the card as wide
    as its band, and every field in a row of its own. The segments stand in the order of the
    places of their pairs in the caller's records, `arrive` (`arvl,dcsn`)
    before `solve` (`dcsn,cntn`) though the graph JSON lists `solve` first,
    and in the graph JSON's order where no record is given; `read` places
    each segment in its card, apart from the boxes ELK lays out. Laid out
    downward, the strip stands under the name. An occurrence one of whose
    builders is open is drawn in full, its other builder a closed layer
    that prints no port label (R-D49)."""
    periods = ["periods[0]", "periods[1]"]
    occurrences = ["periods[0]/cons", "periods[1]/cons"]
    closed = _compact_layout(node, periods)
    found = _compact_layout(node, [*periods, *occurrences])
    G_ = found["G"]
    assert found["compact"] == occurrences
    assert set(found["builders"]) == {
        f"{at}/{name}" for at in occurrences for name in ("arrive", "solve")
    }
    strip, strip_y, pad = G_["cardStripH"], G_["cardStripY"], G_["framePad"]
    assert strip_y + strip + 1 + pad == G_["cardH"] == 32
    for at in occurrences:
        frame, shut = found["frames"][at], closed["frames"][at]
        assert frame["open"] and not shut["open"]
        assert (frame["face"], frame["nameTop"]) == (shut["face"], shut["nameTop"]) == ("port", G_["cardNameTop"])
        # every field joined: the card 32 px high, its closed card the same
        # drawing, each card's ports on the axis (design pass 13 §2)
        assert frame["height"] == shut["height"] == G_["cardH"]
        for side in ("ins", "outs"):
            assert [(p[0], p[2], p[4]) for p in frame[side]] == [
                (p[0], p[2] if side == "ins" else frame["width"], p[4]) for p in shut[side]
            ]
            assert [p[3] for p in frame[side]] == [p[3] for p in shut[side]] == [G_["cardAxis"]] * len(shut[side])
        assert frame["width"] == shut["width"] == G_["frameW"]
        first, second = (found["builders"][f"{at}/{name}"] for name in ("arrive", "solve"))
        assert (first["pair"], second["pair"]) == ("arvl,dcsn", "dcsn,cntn")
        assert first["parent"] == second["parent"] == f"{at}___group___"
        assert [first["at"], second["at"]] == frame["builders"]
        # two segments of equal width G.cardSegmentGap apart, from G.cardInset
        # inside the card's left edge to G.cardStripRight inside its right edge
        # (design pass 13 §2, rule 5)
        for box in (first["at"], second["at"]):
            assert (box["y"], box["height"]) == (strip_y, strip), (at, box)
        assert first["at"]["x"] == G_["cardInset"]
        assert first["at"]["x"] + first["at"]["width"] + G_["cardSegmentGap"] == second["at"]["x"]
        assert second["at"]["x"] + second["at"]["width"] == frame["width"] - G_["cardStripRight"]
        assert abs(first["at"]["width"] - second["at"]["width"]) <= 1
        for name, box in (("arrive", first["at"]), ("solve", second["at"])):
            # `read` places the segment in its card, apart from ELK's boxes
            segment = f"{at}/{name}___group___"
            place = found["builderPlaces"][segment]
            frame_place = found["places"][f"{at}___group___"]
            assert (place["width"], place["height"]) == (box["width"], box["height"])
            assert (place["ax"], place["ay"]) == (
                frame_place["ax"] + box["x"],
                frame_place["ay"] + box["y"],
            )
            assert segment not in found["places"] and segment not in found["laid"]
    # the nodes inside a compact occurrence are no boxes of ELK's graph, and
    # the wire between the two periods runs from card to card
    assert not any(box.startswith("periods[0]/cons/") for box in found["laid"])
    assert found["wires"] == [["periods[1]/cons___group___", "periods[0]/cons___group___"]]

    # with no records the segments keep the graph JSON's order
    plain = _compact_layout(node, [*periods, *occurrences], builders=None)
    assert (
        plain["frames"]["periods[0]/cons"]["builders"][0]
        == plain["builders"]["periods[0]/cons/solve"]["at"]
    )
    assert plain["builders"]["periods[0]/cons/solve"]["pair"] is None

    # unfolded, the strip is the band of G.cardBandH, each segment as wide as
    # its id with G.cardIdPad and its signs with G.cardSignsPad, rounded up to
    # G.cardStep, the card as wide as its band, and each field in a row of its
    # own, `m` at the left, `a` and `b` at the right, the card's ports on the
    # axis; the other card stays folded (design pass 13 §2, rule 7)
    band, row, step = G_["cardBandH"], G_["frameRow"], G_["cardStep"]
    unfolded = _compact_layout(node, [*periods, *occurrences], unfold=["periods[0]/cons"])
    frame, other = unfolded["frames"]["periods[0]/cons"], unfolded["frames"]["periods[1]/cons"]
    assert frame["height"] == strip_y + band + 2 * row + pad
    widths = [
        step * math.ceil((len(name) * 7 + G_["cardIdPad"] + 2 * 7 + G_["cardSignsPad"]) / step)
        for name in ("arrive", "solve")
    ]
    assert [box["width"] for box in frame["builders"]] == widths == [72, 72]
    assert frame["width"] == G_["cardBandLeft"] + sum(widths) + G_["cardSegmentGap"] + G_["cardBandRight"]
    assert [(box["x"], box["y"], box["height"]) for box in frame["builders"]] == [
        (G_["cardBandLeft"], strip_y, band),
        (G_["cardBandLeft"] + widths[0] + G_["cardSegmentGap"], strip_y, band),
    ]
    # one port for the card's one continuation branch, on the axis (design pass 13 §2, rule 7)
    assert [p[3] for p in frame["outs"]] == [G_["cardAxis"]]
    assert (other["height"], other["builders"][0]["height"]) == (G_["cardH"], strip)

    # laid out downward, the strip under the name
    down, shut = (
        _compact_layout(node, opened, "DOWN")["frames"]["periods[1]/cons"]
        for opened in ([*periods, *occurrences], periods)
    )
    first, second = down["builders"]
    assert first["y"] == second["y"] == down["nameTop"] - G_["cardNameTop"] + strip_y
    assert down["height"] == shut["height"]

    # one builder open: the occurrence is drawn in full, its other builder a
    # closed layer whose ports print no label
    full = _compact_layout(node, [*periods, *occurrences, "periods[0]/cons/arrive"])
    assert full["compact"] == ["periods[1]/cons"]
    solve = full["frames"]["periods[0]/cons/solve"]
    assert solve["face"] is None and not solve["open"]
    assert [p[1] for p in solve["ins"] + solve["outs"]] == [""] * len(solve["ins"] + solve["outs"])


# the join text the exporter writes on the reading ports of `keeper` that
# `bequest`'s three wires reach, and on that of `tenure` that `keeper`'s one
# wire reaches, as in the durables model's backward trellis graph
BEQUEST_JOINS = "a_nxt_kp → a_bq; h_nxt_kp → h_bq; z_nxt_kp → z_bq"
KEEPER_JOINS = "h_kp; w_kp; z_kp"
# The reading ports of `keeper` that `bequest`'s three wires reach, by the
# output each wire comes from, and the reading port of `tenure` that
# `keeper`'s wire reaches, each as (its id, its label, its role) as the
# exporter writes them in the durables model's backward trellis graph: the
# function the wire carries at the continuation perch, in mathematical
# italic with the perch's sign and its coordinates, and the role `value`,
# the one role of a wire that carries a function (AMD-MB-001 §5.4); the
# fixture keeps the durables model's names of 21 October for its three
# value wires.
KEEPER_PORTS = {
    "V": ("V", "𝑉≻(a_nxt_kp, h_nxt_kp, z_nxt_kp)", "value"),
    "dV_a": ("dV_a", "𝑑𝑉_a≻(a_nxt_kp, h_nxt_kp, z_nxt_kp)", "value"),
    "dV_h": ("dV_h", "𝑑𝑉_h≻(a_nxt_kp, h_nxt_kp, z_nxt_kp)", "value"),
}
TENURE_PORTS = {"V": ("V_kp", "𝑉_kp≻(w_kp, h_kp, z_kp)", "value")}


def _reading(node: dict, join: str, ports: dict) -> dict:
    """The node `node` with one reading port for each wire it reads, given
    by the output the wire comes from in `ports`, `{output: (id, label,
    role)}`, each port carrying its label, its role and the join text
    `join`."""
    edges = [
        {**edge, "targetNodeInputId": ports[edge["sourceNodeOutputId"]][0]}
        for edge in node["incomingEdges"]
    ]
    inputs = [
        {
            "id": port,
            "attrs": [
                {"key": "label", "value": label},
                {"key": "role", "value": role},
                {"key": "join", "value": join},
            ],
        }
        for port, label, role in ports.values()
    ]
    return {**node, "inputsMetadata": inputs, "incomingEdges": edges}


def _pair_graph(role: str | None = None, label: str | None = None) -> dict:
    """One period of a backward trellis graph in the shape of the durables
    model's: the builder `eval` of `bequest` writes three values,
    `V`, `dV_a` and `dV_h`, which the builder `pull` of
    `keeper` reads, three wires of one ordered pair of stage occurrences;
    `pull` writes `V`, which the builder `pull` of `tenure` reads as `V_kp`,
    one wire of another pair. Each reading port has the role and the label
    KEEPER_PORTS and TENURE_PORTS give it, or `role` and `label` in their
    places where they are given."""

    def ports(given: dict) -> dict:
        return {
            output: (port, written if label is None else label, held if role is None else role)
            for output, (port, written, held) in given.items()
        }

    return {
        "groupNodeConfigs": PERIODS["groupNodeConfigs"],
        "nodes": [
            _node("periods[0]/bequest/eval/g", outputs=("V", "dV_a", "dV_h")),
            _reading(
                _node(
                    "periods[0]/keeper/pull/g",
                    outputs=("V",),
                    reads=tuple(
                        ("periods[0]/bequest/eval/g", out) for out in ("V", "dV_a", "dV_h")
                    ),
                ),
                BEQUEST_JOINS,
                ports(KEEPER_PORTS),
            ),
            _reading(
                _node("periods[0]/tenure/pull/g", reads=(("periods[0]/keeper/pull/g", "V"),)),
                KEEPER_JOINS,
                ports(TENURE_PORTS),
            ),
        ],
    }


PAIRS = _pair_graph()
# the bundle of the ordered pair `bequest`, `keeper`, by its id
PAIR_BUNDLE = "stages::periods[0]/bequest|periods[0]/keeper"
# the Node module: runs the layout script, builds the graph JSON read on
# standard input with every period and occurrence open and every builder
# closed, so that every occurrence is drawn compact, and the bundles it
# names split, lays it out with ELK and reads ELK's answer; prints each
# wire's boxes and ports, the label `read` answers for it, the outputs of
# the wires a bundle draws and the bundle a split wire belongs to; each
# bundle of the layout with its two occurrences, whether it is split and
# its number of wires; and each card's ports and height
PAIR_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length < 3));
const measure = (text) => Array.from(text || "").length * 7;
const built = L.build(m, open, { split: given.split }, measure);
const read = L.read(built, await new ELK().layout(JSON.parse(JSON.stringify(built.elk))));
const cards = {};
for (const box of Object.values(built.boxes)) {
  if (box.type === "layer" && box.geom && box.geom.card) {
    const ids = (ports) => ports.map((p) => p.id);
    const g = box.geom;
    cards[box.namespace] = { ins: ids(g.ins), outs: ids(g.outs), height: g.height };
  }
}
console.log(JSON.stringify({
  wires: built.wires.map((w) => ({
    source: w.source, target: w.target, sourceHandle: w.sourceHandle, targetHandle: w.targetHandle,
    label: read.joins[w.id] ? read.joins[w.id].text : null, count: w.count,
    members: w.pairBundle ? w.pairBundle.members.map((member) => member.out) : null,
    split: w.pairOf || null })),
  bundles: built.pairBundles.map((u) => ({ id: u.id, from: u.from, to: u.to, split: u.split,
                                          wires: u.keys.length })),
  cards,
}));
"""


def _pair_layout(node, split=None, graph=PAIRS) -> dict:
    """The layout of `graph`, PAIRS unless another is given, with the
    bundles `split` names split (PAIR_SCRIPT)."""
    script = PAIR_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    return node_output(node, script, {"graph": graph, "split": split})


def test_an_ordered_pair_s_wires_within_a_period_are_one_cable_that_selection_splits_for_measures_alone(
    node,
):
    """Within a period, the wires from one stage occurrence drawn as a card
    to another are one bundle, where they are two or more (AAS, L-D25;
    design pass 7 §3): one wire between one port of each card, the
    bundle's, whose id names the ordered pair, with one label, so that the
    period holds one label for each ordered pair; a pair of one wire keeps
    its wire. In a backward trellis graph a wire that carries a value or a
    value prints the name of that function as its reading port's
    label gives it, without the perch's sign and the coordinates, `𝑑𝑉_a`,
    and a bundle of such wires their names, each once, in the order of its
    wires, `𝑉, 𝑑𝑉_a, 𝑑𝑉_h`, and no state field, in its hover (AAS, L-D26;
    design pass 7 §3); the cable's label, which it prints while hovered, is
    its route's branch, and nothing where the route has none, its count
    standing at its plug (design pass 13 §1, rule 7; Q-D17), for the wires
    of the role `measure`, as a forward graph's wires are, too. The wires that carry
    values are one cable of their route that nothing splits (design pass
    12 §2): while the caller names, in `options.split`, either occurrence
    or the bundle, as the region names the selected occurrence and the
    selected bundle, the cable stands as it stood, its one label and its
    two ports kept. The wires of the role `measure` are split so named,
    each with its own ports and its own label, and each such wire names the
    bundle it belongs to; naming another occurrence leaves the bundle
    standing. Every card of the period, its fields all joined and no field
    port carried, is 32 px high (design pass 13 §2)."""
    bequest, keeper, tenure = (
        f"periods[0]/{key}___group___" for key in ("bequest", "keeper", "tenure")
    )
    joined = "periods[0]/keeper/pull/g|V"
    whole = _pair_layout(node)
    assert whole["bundles"] == [
        {
            "id": PAIR_BUNDLE,
            "from": "periods[0]/bequest",
            "to": "periods[0]/keeper",
            "split": False,
            "wires": 3,
        }
    ]
    assert whole["wires"] == [
        {
            "source": bequest,
            "target": keeper,
            "sourceHandle": f"{bequest}::out::{PAIR_BUNDLE}",
            "targetHandle": f"{keeper}::in::{PAIR_BUNDLE}",
            "count": 3,
            "label": None,
            "members": ["V", "dV_a", "dV_h"],
            "split": None,
        },
        {
            "source": keeper,
            "target": tenure,
            "sourceHandle": f"{keeper}::out::{joined}",
            "targetHandle": f"{tenure}::in::{joined}",
            "count": 1,
            "label": None,
            "members": None,
            "split": None,
        },
    ]
    cards = whole["cards"]
    assert cards["periods[0]/bequest"]["outs"] == [PAIR_BUNDLE]
    assert cards["periods[0]/keeper"] == {"ins": [PAIR_BUNDLE], "outs": [joined], "height": 32}
    assert {card["height"] for card in cards.values()} == {32}

    # the cable of values stands whole while `keeper`, `bequest` or the
    # bundle is named: its one wire between the bundle's two ports, its
    # count, its members and the cards' ports as they stood (design pass 12
    # §2)
    for split in (["periods[0]/keeper"], ["periods[0]/bequest"], [PAIR_BUNDLE]):
        apart = _pair_layout(node, split)
        assert apart["bundles"] == whole["bundles"], split
        assert apart["wires"] == whole["wires"], split
        assert apart["cards"] == whole["cards"], split
    # naming another occurrence leaves the bundle standing
    assert _pair_layout(node, ["periods[0]/tenure"])["wires"] == whole["wires"]

    # the same wires of the role `measure` print the same counts, and are
    # split while `keeper`, `bequest` or the bundle is named: three wires,
    # each with its own ports and its own count, each naming the bundle
    measures = _pair_graph("measure")
    measured = _pair_layout(node, graph=measures)
    assert [w["label"] for w in measured["wires"]] == [None, None]
    for split in (["periods[0]/keeper"], ["periods[0]/bequest"], [PAIR_BUNDLE]):
        apart = _pair_layout(node, split, graph=measures)
        assert [bundle["split"] for bundle in apart["bundles"]] == [True], split
        wires = [w for w in apart["wires"] if w["target"] == keeper]
        assert [w["sourceHandle"] for w in wires] == [
            f"{bequest}::out::periods[0]/bequest/eval/g|{out}" for out in ("V", "dV_a", "dV_h")
        ], split
        assert [(w["label"], w["members"], w["split"]) for w in wires] == [
            (None, None, PAIR_BUNDLE)
        ] * 3, split
        assert len(apart["cards"]["periods[0]/bequest"]["outs"]) == 3, split
        assert apart["wires"][-1] == measured["wires"][-1], split


def test_a_bundle_of_wires_that_carry_values_and_no_name_counts_its_wires_at_its_plug(node):
    """Wires of a backward trellis graph whose reading ports carry a value
    but no label to name the function by are cables
    like any other (design pass 10 §6): the bundle of `bequest` and `keeper`
    counts its three wires and the wire of `keeper` and `tenure` one, the
    count a cable's bus mark draws at its plug, neither printing a label,
    and no state field labels either (AAS, L-D26; unit L's final judgment,
    §6 item 9; design pass 13 §1, rule 5); named in `options.split`, the
    bundle stays one cable of three wires (design pass 12 §2)."""
    keeper = "periods[0]/keeper___group___"
    unnamed = _pair_graph(label="")
    whole = _pair_layout(node, graph=unnamed)
    assert [(w["count"], w["label"], w["members"]) for w in whole["wires"]] == [
        (3, None, ["V", "dV_a", "dV_h"]),
        (1, None, None),
    ]
    apart = _pair_layout(node, [PAIR_BUNDLE], graph=unnamed)
    assert [(w["count"], w["label"], w["members"]) for w in apart["wires"] if w["target"] == keeper] == [
        (3, None, ["V", "dV_a", "dV_h"])
    ]


# The three values a stage writes at its arrival and its reader reads at
# its continuation in a backward trellis graph in the shape of the durables
# model's, each as its name, its printed name and its one role (AMD-MB-001
# §5.4); the fixture keeps the names of 21 October.
VALUE_WIRES = (
    ("V", "𝑉", "value"),
    ("dV_a", "𝑑𝑉_a", "value"),
    ("dV_h", "𝑑𝑉_h", "value"),
)


def _value_writer(occurrence: str) -> dict:
    """The builder `eval` of the stage occurrence `occurrence`, which writes
    the three wires of VALUE_WIRES at its arrival perch."""
    return {
        "id": f"{occurrence}/eval/g", "label": "g", "namespace": f"{occurrence}/eval",
        "attrs": [{"key": "kind", "value": "operator"}],
        "outputsMetadata": [
            {"id": f"{occurrence}/arvl:{name}",
             "attrs": [{"key": "label", "value": f"{shown}≺(a, h, z)"}, {"key": "role", "value": role}]}
            for name, shown, role in VALUE_WIRES
        ],
    }


def _value_reader(occurrence: str, writer: str, fields: str) -> dict:
    """The builder `pull` of the stage occurrence `occurrence`, which reads
    the three wires of VALUE_WIRES from the builder `eval` of `writer` at
    its continuation perch, each edge carrying the record of the route from
    `occurrence` into `writer`, with no branch and one pair for each letter
    of `fields`, as the exporter writes a backward edge's record."""
    route = {
        "branch": None, "source": occurrence, "destination": writer,
        "source_fields": [f"{x}_nxt" for x in fields], "destination_fields": list(fields),
        "pairs": [{"source_field": f"{x}_nxt", "destination_field": x, "origin": "authored",
                   "address": "inter_connectors[0]"} for x in fields],
        "status": "certified", "law": None,
    }
    return {
        "id": f"{occurrence}/pull/g", "label": "g", "namespace": f"{occurrence}/pull",
        "attrs": [{"key": "kind", "value": "operator"}],
        "inputsMetadata": [
            {"id": f"{occurrence}/cntn:{name}",
             "attrs": [{"key": "label", "value": f"{shown}≻({', '.join(f'{x}_nxt' for x in fields)})"},
                       {"key": "role", "value": role}]}
            for name, shown, role in VALUE_WIRES
        ],
        "incomingEdges": [
            {"sourceNodeId": f"{writer}/eval/g", "sourceNodeOutputId": f"{writer}/arvl:{name}",
             "targetNodeInputId": f"{occurrence}/cntn:{name}", "attrs": [{"key": "route", "value": route}]}
            for name, _, _ in VALUE_WIRES
        ],
    }


# A backward trellis graph of two periods in the shape of the durables
# model's (design pass 12 §2): `tenure` of periods[0] writes the three wires
# of VALUE_WIRES, which `keeper` and `adjuster` of periods[1] read, each by
# its own route of no branch, `keeper`'s of three pairs and `adjuster`'s of
# two; `tenure` of periods[1] writes the same three wires into the
# `outside` node of that occurrence and `keeper` of periods[2], whose three
# ports they are, as the exporter writes it.
OUTSIDE_KEEPER = "outside:periods[1]/tenure:periods[2]/keeper"
ROUTES = {
    "groupNodeConfigs": PERIODS["groupNodeConfigs"],
    "nodes": [
        _value_writer("periods[0]/tenure"),
        _value_writer("periods[1]/tenure"),
        _value_reader("periods[1]/keeper", "periods[0]/tenure", "ahz"),
        _value_reader("periods[1]/adjuster", "periods[0]/tenure", "az"),
        {
            "id": OUTSIDE_KEEPER, "label": "periods[2]/keeper", "namespace": "",
            "attrs": [{"key": "kind", "value": "outside"}, {"key": "label", "value": "periods[2]/keeper"},
                      {"key": "target", "value": "periods[2]/keeper"}],
            "inputsMetadata": [
                {"id": f"periods[1]/tenure/arvl:{name}",
                 "attrs": [{"key": "label", "value": f"{shown}≺(a, h, z)"}, {"key": "role", "value": role},
                           {"key": "outside", "value": "periods[2]/keeper"}]}
                for name, shown, role in VALUE_WIRES
            ],
            "incomingEdges": [
                {"sourceNodeId": "periods[1]/tenure/eval/g", "sourceNodeOutputId": f"periods[1]/tenure/arvl:{name}",
                 "targetNodeInputId": f"periods[1]/tenure/arvl:{name}"}
                for name, _, _ in VALUE_WIRES
            ],
        },
    ],
}
# the Node module: builds the graph JSON read on standard input with its
# periods and occurrences open, but the layers it names in `closed` and the
# layers inside them, and its builders closed, so that every occurrence of
# an open period is a card, and the layers or bundles it names in `split`
# named to the layout, lays it out with ELK and reads ELK's answer; prints
# the geometry `G`, each closed layer's box, a card among them, with its
# height and ports, each with its id, its place
# on the card's edge and whether a wire joins it to another card and
# whether it is hidden, each wire's boxes, ports, count, branch, label as
# `read` answers it, whether it is a cable and dashed, and the outputs of
# the wires its bundle carries; the number of bundles that share a piece
# between two periods (K-D5); and each edge of the root as the two boxes it
# joins, a period's layer by its namespace
ROUTE_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const closed = (ns) => (given.closed || []).some((layer) => ns === layer || ns.startsWith(layer + "/"));
const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length < 3 && !closed(ns)));
const built = L.build(m, open, { split: given.split }, (text) => Array.from(text || "").length * 7);
const read = L.read(built, await new ELK().layout(JSON.parse(JSON.stringify(built.elk))));
const cards = {};
for (const box of Object.values(built.boxes)) {
  if (box.type === "layer" && box.geom) {
    const port = (p) => ({ id: p.id, y: p.y, joined: !!p.joined, hidden: !!p.hidden });
    cards[box.namespace] = { height: box.geom.height, ins: box.geom.ins.map(port), outs: box.geom.outs.map(port) };
  }
}
const box = (port) => port.split("::")[0].replace(/___group___$/, "");
console.log(JSON.stringify({
  G: L.G,
  cards,
  wires: built.wires.map((w) => ({
    source: w.source, target: w.target, sourceHandle: w.sourceHandle, targetHandle: w.targetHandle,
    count: w.count, branch: w.branch, label: read.joins[w.id] ? read.joins[w.id].text : null,
    cable: !!w.cable, dashed: !!w.dashed,
    members: w.pairBundle ? w.pairBundle.members.map((member) => member.out) : null })),
  shared: built.bundles.length,
  root: built.elk.edges.map((e) => [box(e.sources[0]), box(e.targets[0])]),
}));
"""


def test_a_backward_route_is_one_cable_from_a_plug_of_its_own_and_one_stub_reaches_its_outside_marker(
    node,
):
    """Design pass 12 §2. In ROUTES, laid out with its periods and its
    occurrences open and its builders closed, every occurrence a card: the
    three wires of each route from `tenure` of periods[0] into periods[1]
    are one cable from a plug of its own on `tenure`'s card into the one
    socket of its reader's card, the two plugs G.cablePitch apart about the
    card's axis, as two branches' plugs stand in the forward graph; the
    cable counts the value functions it carries, the wires a backward graph
    drew one by one, three for `keeper` and for `adjuster` alike, whatever
    its route pairs, two fields for `adjuster`'s, the count standing at its
    plug and no label printed (design pass 13 §1, rule 5); no piece is shared between the two
    periods, each cable crossing on a piece of its own. The three wires
    `tenure` of periods[1] writes into the `outside` marker of `keeper` of
    periods[2] are one dashed cable from one plug, which counts the three
    wires it carries. Whatever `options.split` names, a writer, a reader or
    a cable, every cable stands as it stood. With periods[1] closed, its box
    stands for its occurrences: each route that reaches or leaves it is one
    wire, at a port of the box of its own, and `tenure` of periods[0] keeps
    one plug for each of its two routes, as a forward graph draws one wire
    for each route into a closed period."""
    script = ROUTE_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    laid = node_output(node, script, {"graph": ROUTES, "split": None})
    G, cards = laid["G"], laid["cards"]
    tenure = "periods[0]/tenure"
    cables = [f"stages::{tenure}|periods[1]/{key}" for key in ("keeper", "adjuster")]
    # one plug for each route, joined, G.cablePitch apart about the middle of the edge
    plugs = cards[tenure]["outs"]
    assert [(p["id"], p["joined"], p["hidden"]) for p in plugs] == [(cable, True, False) for cable in cables]
    assert plugs[1]["y"] - plugs[0]["y"] == G["cablePitch"], plugs
    assert (plugs[0]["y"] + plugs[1]["y"]) / 2 == G["cardAxis"], (plugs, cards[tenure])
    # one socket on each reader, the cable's
    for key, cable in zip(("keeper", "adjuster"), cables):
        assert [(p["id"], p["hidden"]) for p in cards[f"periods[1]/{key}"]["ins"]] == [(cable, False)], key
    # one cable for each route, its count the functions it carries, its label that count
    drawn = [w for w in laid["wires"] if w["source"] == f"{tenure}___group___"]
    outputs = [f"{tenure}/arvl:{name}" for name, _, _ in VALUE_WIRES]
    assert [
        (w["target"], w["sourceHandle"], w["count"], w["branch"], w["label"], w["cable"], w["members"])
        for w in drawn
    ] == [
        (f"periods[1]/{key}___group___", f"{tenure}___group___::out::{cable}", count, None, None, True, outputs)
        for key, cable, count in zip(("keeper", "adjuster"), cables, (3, 3))
    ]
    # each cable crosses from periods[0] to periods[1] on a piece of its own
    assert laid["shared"] == 0, laid
    assert laid["root"].count(["periods[0]", "periods[1]"]) == 2, laid["root"]
    # the stub into the `outside` marker: one dashed cable from one plug, counting its three wires
    writer = "periods[1]/tenure"
    stub = [w for w in laid["wires"] if w["target"] == OUTSIDE_KEEPER]
    assert [(w["source"], w["count"], w["label"], w["dashed"], w["cable"]) for w in stub] == [
        (f"{writer}___group___", 3, None, True, True)
    ]
    assert stub[0]["members"] == [f"{writer}/arvl:{name}" for name, _, _ in VALUE_WIRES]
    assert [p["id"] for p in cards[writer]["outs"]] == [f"stages::{writer}|{OUTSIDE_KEEPER}"]
    for split in ([tenure], ["periods[1]/keeper"], [cables[0]], [writer]):
        assert node_output(node, script, {"graph": ROUTES, "split": split})["wires"] == laid["wires"], split

    # periods[1] closed: one wire for each route into its box and out of it
    shut = node_output(node, script, {"graph": ROUTES, "split": None, "closed": ["periods[1]"]})
    box, stub = "periods[1]___group___", f"stages::{writer}|{OUTSIDE_KEEPER}"
    assert [p["id"] for p in shut["cards"][tenure]["outs"]] == cables, shut["cards"][tenure]
    assert [p["id"] for p in shut["cards"]["periods[1]"]["ins"]] == cables, shut["cards"]["periods[1]"]
    assert [p["id"] for p in shut["cards"]["periods[1]"]["outs"]] == [stub], shut["cards"]["periods[1]"]
    assert [
        (w["source"], w["sourceHandle"], w["target"], w["targetHandle"], w["count"], w["members"])
        for w in shut["wires"]
    ] == [
        (f"{tenure}___group___", f"{tenure}___group___::out::{cable}", box, f"{box}::in::{cable}", count, outputs)
        for cable, count in zip(cables, (3, 3))
    ] + [
        (box, f"{box}::out::{stub}", OUTSIDE_KEEPER, f"{OUTSIDE_KEEPER}::in::{writer}/arvl:V", 3,
         [f"{writer}/arvl:{name}" for name, _, _ in VALUE_WIRES])
    ]


# the Node module: runs the layout script, builds the graph JSON read on
# standard input with the layers it names open, or every layer where it
# names none, in the direction it names for every layer or, where it names
# none, in the directions the graph configures, lays it out with ELK,
# aligns ELK's answer (`arrange`) and reads it; prints the geometry `G`,
# what `arrange` aligns (`stage`), each box with its type, whether it is an
# open layer, its parent, its label, the width of its label, whether the
# layout cut its label and its place on the pane, each wire's route and its
# two boxes; a text is 7 px wide for each of its characters. ELK receives a
# copy of each graph made in this module's own context, since it reads an
# array made in the script's context as empty.
STAGE_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const open = new Set(given.open || Object.keys(m.layers));
const measure = (text) => Array.from(text || "").length * 7;
const built = L.build(m, open, { direction: given.direction }, measure);
const elk = { layout: (graph) => new ELK().layout(JSON.parse(JSON.stringify(graph))) };
const read = L.read(built, await L.arrange(built, await elk.layout(built.elk), elk));
const boxes = {};
for (const [id, box] of Object.entries(built.boxes)) {
  const place = read.place[id] || read.builders[id];
  const label = box.spec ? box.spec.label : box.name;
  boxes[id] = { type: box.type, open: !!box.open, parent: box.parent, label,
                labelW: measure(label), cut: !!(box.geom && box.geom.cut),
                x: place.ax, y: place.ay, width: place.width, height: place.height };
}
const wires = built.wires.map(
  (w) => ({ id: w.id, source: w.source, target: w.target, route: read.routes[w.id] }));
console.log(JSON.stringify({ G: L.G, stage: built.stage, boxes, wires }));
"""
# the column of a stage's backward and forward builders graphs, from top to
# bottom: the stage's `Inputs`, the builders a wire joins one to the next,
# and the stage's `Outputs` (AAS, L-D20)
STAGE_COLUMNS = {
    "backward": [
        "GraphInputs",
        "cntn_to_dcsn___group___",
        "dcsn_to_arvl___group___",
        "GraphOutputs",
    ],
    "forward": [
        "GraphInputs",
        "arvl_to_dcsn___group___",
        "dcsn_to_cntn___group___",
        "GraphOutputs",
    ],
}
# the boxes whose labels the layout cuts, by stage and graph: the two value
# outputs of `keeper_cons`, whose heads name three fields over three
# arguments, 59 and 60 characters wide
STAGE_CUT = {
    ("keeper_cons", "backward"): {"cntn_to_dcsn:Evaluation", "dcsn_to_arvl:Evaluation"},
}


def _stage_graphs() -> dict:
    """The backward and the forward builders graphs of `keeper_cons` of the
    durables model and of `cons` of the portfolio model, bound as the page
    binds a stage file opened from the tree (`bound_as_the_recipe_binds`),
    by (stage, graph id)."""
    found = {}
    for name, folder, relpath in (
        ("keeper_cons", DURABLES_MODEL, KEEPER_CONS),
        ("cons", PORTFOLIO_CHOICE, CONS),
    ):
        text = (folder / relpath).read_text(encoding="utf-8")
        collection = model.collection(bound_as_the_recipe_binds(folder, text, relpath))
        for graph in collection["graphs"]:
            if graph["id"] in STAGE_COLUMNS:
                found[(name, graph["id"])] = graph
    return found


def _stage_layout(node, graph: dict, opened=None, direction=None) -> dict:
    """The layout of `graph` with the layers `opened` open, every layer
    where None, in the direction `direction` (STAGE_SCRIPT)."""
    script = STAGE_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    given = {"graph": graph, "open": opened, "direction": direction}
    return node_output(node, script, given)


def _center(box: dict) -> float:
    """The abscissa of the middle of the box `box` on the pane."""
    return box["x"] + box["width"] / 2


def _crossed(laid: dict) -> list[tuple[str, str]]:
    """Each wire of the layout `laid` (STAGE_SCRIPT) that runs through a box
    which is neither one of its two ends nor an open layer, with that box;
    and each wire whose route turns at an angle other than a right angle,
    with the word `angle`."""
    found = []
    for wire in laid["wires"]:
        route = wire["route"]
        for a, b in zip(route, route[1:]):
            if abs(a["x"] - b["x"]) > 0.01 and abs(a["y"] - b["y"]) > 0.01:
                found.append((wire["id"], "angle"))
            for box_id, box in laid["boxes"].items():
                if box_id in (wire["source"], wire["target"]) or (
                    box["type"] == "layer" and box["open"]
                ):
                    continue
                if (
                    max(a["x"], b["x"]) > box["x"] + 0.5
                    and min(a["x"], b["x"]) < box["x"] + box["width"] - 0.5
                    and max(a["y"], b["y"]) > box["y"] + 0.5
                    and min(a["y"], b["y"]) < box["y"] + box["height"] - 0.5
                ):
                    found.append((wire["id"], box_id))
    return found


def test_the_stage_view_stands_its_frames_and_boxes_on_one_axis(node):
    """In a stage's builders graph laid out downward, every builder open as
    the page opens them (AAS, L-D20): the stage's `Inputs`, the builders a
    wire joins one to the next and the stage's `Outputs` stand in one
    column, the frames of those builders of one width and one left edge,
    within 1 px, and the centers of `Inputs` and `Outputs` on their axis,
    within 2 px; the policy builder, which no wire joins to another builder,
    stands beside the column, its frame of the column's width within 1 px;
    every box of every open frame stands centered on the frame's vertical
    axis, within 2 px; a box's label wider than G.labelMax is cut, the box
    no wider than G.labelMax and its padding, and a shorter one is not;
    every route turns at right angles and runs through no box but its two
    ends. On `keeper_cons` of the durables model and `cons` of the
    portfolio model, each bound as the page binds it. On `cons` with a box
    of the policy builder given a label of 60 characters, the policy's
    frame is the widest, and the column's frames take its width. With
    `cntn_to_dcsn` closed its box stands in the column on the same axis.
    The graph turned to the right, and a trellis graph, are not aligned;
    the trellis cuts no label."""
    graphs = _stage_graphs()
    # the width of the column's frames, by stage and graph
    widths = {}
    for (name, graph_id), graph in graphs.items():
        laid = _stage_layout(node, graph)
        G, boxes, stage = laid["G"], laid["boxes"], laid["stage"]
        assert stage["column"] == STAGE_COLUMNS[graph_id], (name, graph_id, stage)
        frames = [boxes[box_id] for box_id in stage["column"] if boxes[box_id]["type"] == "layer"]
        for frame in frames:
            assert abs(frame["x"] - frames[0]["x"]) <= 1, (name, graph_id, frames)
            assert abs(frame["width"] - frames[0]["width"]) <= 1, (name, graph_id, frames)
        axis = _center(frames[0])
        for box_id in (stage["column"][0], stage["column"][-1]):
            assert abs(_center(boxes[box_id]) - axis) <= 2, (name, graph_id, box_id)
        left, right = frames[0]["x"], frames[0]["x"] + frames[0]["width"]
        beside = [
            box
            for box_id, box in boxes.items()
            if box["type"] == "layer" and not box["parent"] and box_id not in stage["column"]
        ]
        assert [box["label"] for box in beside] == (["policy"] if graph_id == "backward" else [])
        for box in beside:
            assert box["x"] >= right or box["x"] + box["width"] <= left, (name, box)
            assert abs(box["width"] - frames[0]["width"]) <= 1, (name, box, frames[0])
        widths[(name, graph_id)] = frames[0]["width"]
        for box_id, box in boxes.items():
            if box["parent"]:
                frame = boxes[box["parent"]]
                assert abs(_center(box) - _center(frame)) <= 2, (name, graph_id, box_id)
            if box["type"] != "layer":
                assert box["cut"] == (box["labelW"] > G["labelMax"]), (name, box_id, box)
                if box["cut"]:
                    assert box["width"] <= G["labelMax"] + 2 * G["padX"] + 2, (name, box_id, box)
        cut = {box_id for box_id, box in boxes.items() if box["cut"]}
        assert cut == STAGE_CUT.get((name, graph_id), set()), (name, graph_id, cut)
        assert _crossed(laid) == [], (name, graph_id)
        extent = max(b["x"] + b["width"] for b in boxes.values())
        print(
            f"stage view: {name} {graph_id}: the column's frames {frames[0]['width']:.1f} wide "
            f"at {frames[0]['x']:.1f}, the graph {extent:.1f} wide"
        )

    # `cons` with a box of the policy builder given a label of 60 characters,
    # which the layout cuts: the policy's frame is the widest, and the
    # column's frames take its width, their left edge one
    widened = json.loads(json.dumps(graphs[("cons", "backward")]))
    first = next(item for item in widened["nodes"] if item.get("namespace") == "policy")
    first["label"] = "𝑉" * 60
    laid = _stage_layout(node, widened)
    boxes, stage = laid["boxes"], laid["stage"]
    assert stage["column"] == STAGE_COLUMNS["backward"]
    assert {box_id for box_id, box in boxes.items() if box["cut"]} == {first["id"]}
    policy = boxes["policy___group___"]
    frames = [boxes[box_id] for box_id in stage["column"] if boxes[box_id]["type"] == "layer"]
    assert policy["width"] > widths[("cons", "backward")] + 1, (policy, widths)
    for frame in frames:
        assert abs(frame["x"] - frames[0]["x"]) <= 1, frames
        assert abs(frame["width"] - policy["width"]) <= 1, (frame, policy)
    for box_id in (stage["column"][0], stage["column"][-1]):
        assert abs(_center(boxes[box_id]) - _center(frames[0])) <= 2, box_id
    for box_id, box in boxes.items():
        if box["parent"]:
            assert abs(_center(box) - _center(boxes[box["parent"]])) <= 2, box_id
    assert _crossed(laid) == []

    # `cntn_to_dcsn` closed: its box in the column, on the axis of the
    # column's one open frame, whose width the policy's frame takes
    backward = graphs[("keeper_cons", "backward")]
    opened = ["dcsn_to_arvl", "policy"]
    laid = _stage_layout(node, backward, opened)
    boxes, stage = laid["boxes"], laid["stage"]
    assert stage["column"] == STAGE_COLUMNS["backward"]
    assert boxes["cntn_to_dcsn___group___"]["open"] is False
    axis = _center(boxes["dcsn_to_arvl___group___"])
    for box_id in stage["column"]:
        assert abs(_center(boxes[box_id]) - axis) <= 2, box_id
    pair = [boxes[box_id]["width"] for box_id in ("dcsn_to_arvl___group___", "policy___group___")]
    assert abs(pair[0] - pair[1]) <= 1, pair
    assert _crossed(laid) == []

    # turned to the right, the graph is not aligned and still cuts its labels
    turned = _stage_layout(node, backward, direction="RIGHT")
    assert turned["stage"] is None
    assert {box_id for box_id, box in turned["boxes"].items() if box["cut"]} == STAGE_CUT[
        ("keeper_cons", "backward")
    ]

    # a trellis graph is not aligned and cuts no label, however wide
    wide = "𝑉" * 60
    trellis = json.loads(json.dumps(COMPACT))
    for item in trellis["nodes"]:
        if item["id"] == "periods[0]/cons/solve:Pushforward":
            item["label"] = wide
    layers = ["periods[0]", "periods[1]", "periods[0]/cons", "periods[1]/cons"]
    every = [*layers, "periods[0]/cons/arrive", "periods[0]/cons/solve"]
    laid = _stage_layout(node, trellis, every)
    solve = laid["boxes"]["periods[0]/cons/solve:Pushforward"]
    assert laid["stage"] is None and not solve["cut"]
    assert solve["width"] == len(wide) * 7 + 2 + 2 * laid["G"]["padX"]


# The cards and the open layers of a trellis graph laid out under a measure
# that sets each face at its own width per character, as brand.css sets
# their sizes (design pass 10 §5): a stage's name, `stage`, 7.5 px; a
# frame's name, `frame`, 6.6 px; every other text 7 px. The script prints
# the geometry `G`, each card's width and whether its name is cut, and each
# open layer's least width.
TYPE_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const per = { stage: 7.5, frame: 6.6 };
const measure = (text, role) => Array.from(text || "").length * (per[role] || 7);
const built = L.build(L.model(given.graph), new Set(given.open), {}, measure);
const cards = {}, least = {};
for (const box of Object.values(built.boxes)) {
  if (box.type !== "layer") continue;
  const g = box.geom;
  if (g && g.card) cards[box.namespace] = { width: g.width, cut: !!g.cut };
  else if (box.open) least[box.namespace] = box.least;
}
console.log(JSON.stringify({ G: L.G, cards, least }));
"""
# the brand stylesheet, whose faces of a frame's name and of a stage's name
# set the lines the layout's measures name
BRAND = ROOT / "packages/bellman-workbench/bellman_workbench/brand.css"


def _line_height(rule: str) -> float:
    """The line height in pixels that brand.css's rule `rule` sets."""
    text = BRAND.read_text(encoding="utf-8")
    body = text[text.index(rule + " {") :].split("}", 1)[0]
    return float(body.split("line-height:", 1)[1].split("px", 1)[0])


def test_a_card_widens_to_its_name_up_to_180_px_and_a_period_s_head_fits_its_line(node):
    """Design pass 10 §5 (unit N, Task 3): a stage card's name is measured
    in the stage's face, `stage`, and the card is as wide as its name with
    G.frameInset before it, its chevron and its borders, up to
    G.frameNameMax, 180 px, past which the card answers that its name is
    cut; a card no wider than its least width keeps G.frameW. An open
    occurrence's layer measures its name in the stage's face, a period's
    layer in the frame's face. A period's head is the line of a frame's
    name with G.periodPad above and below it, and a card's name's line box
    the line of a stage's name, from G.cardNameTop above the strip at
    G.cardStripY, each line the one brand.css sets for its face; a card's
    width is its name with G.cardChrome on the step of G.cardStep (design
    pass 13 §2, rule 6)."""
    script = TYPE_SCRIPT % {"script": json.dumps(str(LAYOUT))}
    G = node_output(node, script, {"graph": FRAMES, "open": []})["G"]
    assert G["frameNameMax"] == 180
    assert G["frameLine"] == _line_height(".bf-t-frame") == 16
    assert G["stageLine"] == _line_height(".bf-t-stage") == 18
    assert G["periodHeader"] == G["frameLine"] + 2 * G["periodPad"]
    assert G["cardNameTop"] + G["stageLine"] <= G["cardStripY"]
    chrome, step = G["cardChrome"], G["cardStep"]
    for key, width, cut in (
        ("cons", G["frameW"], False),
        ("keeper_consumer", step * math.ceil((15 * 7.5 + chrome) / step), False),
        ("k" * 40, G["frameNameMax"], True),
    ):
        graph = json.loads(json.dumps(FRAMES).replace("cons", key))
        opened = ["periods[0]", "periods[1]", f"periods[1]/{key}", f"periods[1]/{key}/push"]
        laid = node_output(node, script, {"graph": graph, "open": opened})
        card = laid["cards"][f"periods[0]/{key}"]
        assert card == {"width": math.ceil(width), "cut": cut}, (key, card)
        least = laid["least"]
        room = 2 * G["layerPad"] + G["toggle"] + 6
        named = len(key) * 7.5 + room
        assert least[f"periods[1]/{key}"] == math.ceil(max(G["layerW"], named)), key
        assert least["periods[0]"] == math.ceil(max(G["layerW"], len("periods[0]") * 6.6 + room))


# unit N, Task 7 (design pass 10 §6): a forward trellis graph of one period
# whose occurrence `S` writes the branch `keep` into `T` by a route of two
# pairs, where `starting data` enters `S` at a `start` marker, `T`'s measure
# leaves at an `end` marker, and `S` also reads a connection from
# `periods[1]/S`, outside the drawn period, at an `outside` marker; `S`'s
# branch `adjust` and `T`'s field `q` are unjoined
def _route_edge(source: str, out: str, into: str, branch, pairs) -> dict:
    return {
        "sourceNodeId": source, "sourceNodeOutputId": out, "targetNodeInputId": into,
        "attrs": [{"key": "route", "value": {"branch": branch, "source": "periods[0]/S", "destination": "periods[0]/T",
                                              "source_fields": [p[0] for p in pairs], "destination_fields": [p[1] for p in pairs],
                                              "pairs": [{"source_field": a, "destination_field": b, "origin": "inferred", "address": "periods[0]"} for a, b in pairs],
                                              "status": "certified", "law": "S:measure:cntn:keep"}}],
    }


CABLES = {
    "groupNodeConfigs": PERIODS["groupNodeConfigs"],
    "nodes": [
        {"id": "start:periods[0]/S/S:measure:arvl", "label": "starting data μ≺", "namespace": "",
         "attrs": [{"key": "kind", "value": "start"}, {"key": "label", "value": "starting data μ≺"}],
         "outputsMetadata": [_port("periods[0]/S/S:measure:arvl", "μ≺")]},
        {"id": "outside:periods[0]/S:periods[1]/S", "label": "periods[1]/S", "namespace": "",
         "attrs": [{"key": "kind", "value": "outside"}, {"key": "label", "value": "periods[1]/S"}, {"key": "target", "value": "periods[1]/S"}],
         "outputsMetadata": [_port("periods[0]/S/S:measure:arvl", "μ≺")]},
        {"id": "periods[0]/S/GraphInputs", "label": "Inputs", "namespace": "periods[0]/S",
         "inputsMetadata": [_port("periods[0]/S/joined:S:arvl:x", "x≺")]},
        {"id": "periods[0]/S/push:Pushforward", "label": "𝑔≻∗μ", "namespace": "periods[0]/S/push",
         "attrs": [{"key": "kind", "value": "operator"}],
         "inputsMetadata": [_port("periods[0]/S/S:measure:arvl", "μ≺")],
         "outputsMetadata": [_port("periods[0]/S/S:measure:cntn:keep", "μ_keep≻"), _port("periods[0]/S/S:measure:cntn:adjust", "μ_adjust≻")],
         "incomingEdges": [
             {"sourceNodeId": "start:periods[0]/S/S:measure:arvl", "sourceNodeOutputId": "periods[0]/S/S:measure:arvl", "targetNodeInputId": "periods[0]/S/S:measure:arvl"},
             {"sourceNodeId": "outside:periods[0]/S:periods[1]/S", "sourceNodeOutputId": "periods[0]/S/S:measure:arvl", "targetNodeInputId": "periods[0]/S/S:measure:arvl"},
         ]},
        {"id": "periods[0]/S/GraphOutputs", "label": "Outputs", "namespace": "periods[0]/S",
         "outputsMetadata": [_port("periods[0]/S/joined:S:cntn:a_kp", "keep: a_kp≻"), _port("periods[0]/S/joined:S:cntn:b_kp", "keep: b_kp≻"),
                             _port("periods[0]/S/unjoined:S:cntn:a_adj", "adjust: a_adj≻", unjoined=True)]},
        {"id": "periods[0]/T/GraphInputs", "label": "Inputs", "namespace": "periods[0]/T",
         "inputsMetadata": [_port("periods[0]/T/joined:T:arvl:a", "a≺"), _port("periods[0]/T/joined:T:arvl:b", "b≺"),
                            _port("periods[0]/T/unjoined:T:arvl:q", "q≺", unjoined=True)]},
        {"id": "periods[0]/T/push:Pushforward", "label": "𝑔≻∗μ", "namespace": "periods[0]/T/push",
         "attrs": [{"key": "kind", "value": "operator"}],
         "inputsMetadata": [_port("periods[0]/T/T:measure:arvl", "μ≺")],
         "outputsMetadata": [_port("periods[0]/T/T:measure:cntn", "μ≻")],
         "incomingEdges": [_route_edge("periods[0]/S/push:Pushforward", "periods[0]/S/S:measure:cntn:keep", "periods[0]/T/T:measure:arvl", "keep", [("a_kp", "a"), ("b_kp", "b")])]},
        {"id": "periods[0]/T/GraphOutputs", "label": "Outputs", "namespace": "periods[0]/T",
         "outputsMetadata": [_port("periods[0]/T/joined:T:cntn:y", "y≻")]},
        {"id": "end:periods[0]/T/T:measure:cntn", "label": "terminal μ≻", "namespace": "",
         "attrs": [{"key": "kind", "value": "end"}, {"key": "label", "value": "terminal μ≻"}],
         "inputsMetadata": [_port("periods[0]/T/T:measure:cntn", "μ≻")],
         "incomingEdges": [{"sourceNodeId": "periods[0]/T/push:Pushforward", "sourceNodeOutputId": "periods[0]/T/T:measure:cntn", "targetNodeInputId": "periods[0]/T/T:measure:cntn"}]},
    ],
}

# the Node module: builds CABLES with the period open and its occurrences
# closed, and prints each card's ports with their branches, each marker's
# geometry and each wire's cable record
CABLE_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const built = L.build(m, new Set(given.open), {}, (text) => Array.from(text || "").length * 7);
const port = (p) => ({ id: p.id, branch: p.branch === undefined ? null : p.branch, joined: !!p.joined, open: !!p.open, hidden: !!p.hidden,
                       fields: (p.fields || []).map((f) => f.id), x: p.x, y: p.y, side: p.side });
const cards = {}, markers = {};
for (const box of Object.values(built.boxes)) {
  if (box.type === "layer" && !box.open) {
    cards[box.namespace] = { width: box.geom.width, height: box.geom.height, ins: box.geom.ins.map(port), outs: box.geom.outs.map(port),
                             texts: box.geom.texts.map((t) => [t.writes, t.branch, t.text]) };
  }
  if (box.type === "marker") {
    const g = box.geom;
    markers[box.id] = { kind: g.kind, width: g.width, height: g.height, mark: g.mark, labelAt: g.labelAt,
                        ins: g.ins.map(port), outs: g.outs.map(port), label: box.spec.label, target: box.spec.target };
  }
}
const wires = built.wires.map((w) => ({ id: w.id, cable: !!w.cable, dashed: !!w.dashed, count: w.count, branch: w.branch, join: w.join }));
console.log(JSON.stringify({ G: L.G, cards, markers, wires }));
"""


def test_a_card_carries_one_port_per_branch_and_one_arrival_port_and_a_marker_is_its_mark(node):
    """Unit N, Task 7 (design pass 10 §6). In CABLES, laid out to the right
    with its period open and its occurrences closed: `S`'s card carries two
    writing ports, the port of the wire that leaves by the branch `keep`,
    joined, with its two field ports, and a port of its own for the branch
    `adjust`, which no wire leaves by, with its one field port, 12 px
    apart; `T`'s card carries one reading port, the wire's, with its three
    arrival field ports, and no port for a field; the unjoined fields
    `a_adj` and `q` stay printed as rows. A port whose wire's other end is a
    boundary marker joins the card to no other card, the meaning a drag
    reads, and is not open, as no wire's port is, so that a plug a cable
    leaves is drawn filled (the fix wave Q3a of unit Q, item 1; A9). The
    `start` marker is a box of the
    10-px circle and its label 4 px from it, the circle at the end nearer
    the card, with its one port on the circle's edge facing the card; the
    `end` marker's circle stands at its left end; the `outside` marker is
    an 8-px square. The wire from `S` to `T` is a cable of two wires on the
    branch `keep`, whose label is the branch; the stub from the `outside`
    marker is dashed, and the stubs from the markers are cables too."""
    script = CABLE_SCRIPT % {"script": json.dumps(str(LAYOUT))}
    laid = node_output(node, script, {"graph": CABLES, "open": ["periods[0]"]})
    G = laid["G"]
    s, t = laid["cards"]["periods[0]/S"], laid["cards"]["periods[0]/T"]
    assert [(p["branch"], p["joined"], p["side"]) for p in s["outs"]] == [("keep", True, "EAST"), ("adjust", False, "EAST")]
    assert s["outs"][0]["id"] == "periods[0]/S/push:Pushforward|periods[0]/S/S:measure:cntn:keep"
    assert s["outs"][0]["fields"] == ["periods[0]/S/joined:S:cntn:a_kp", "periods[0]/S/joined:S:cntn:b_kp"]
    assert s["outs"][1]["id"] == "branch:adjust" and s["outs"][1]["fields"] == ["periods[0]/S/unjoined:S:cntn:a_adj"]
    assert abs(s["outs"][1]["y"] - s["outs"][0]["y"]) == G["cablePitch"]
    assert all(p["x"] == s["width"] for p in s["outs"])
    # S reads its measure from the two markers at one arrival port, the second hidden; a wire from a marker joins
    # the card to no other card, so that the port is not joined, and no wire's port is open (the fix wave Q3a, item 1)
    assert [(p["joined"], p["open"], p["hidden"], p["side"]) for p in s["ins"]] == [(False, False, False, "WEST"), (False, False, True, "WEST")]
    assert s["ins"][0]["y"] == s["ins"][1]["y"] and s["ins"][0]["fields"] == ["periods[0]/S/joined:S:arvl:x"]
    assert [(p["joined"], p["hidden"]) for p in t["ins"]] == [(True, False)]
    assert t["ins"][0]["fields"] == ["periods[0]/T/joined:T:arvl:a", "periods[0]/T/joined:T:arvl:b", "periods[0]/T/unjoined:T:arvl:q"]
    # T's measure leaves at the `end` marker, which joins it to no other card: its one branch port is not joined,
    # and not open, so that its plug is drawn filled since a cable leaves it (the fix wave Q3a, item 1; A9)
    assert [(p["branch"], p["joined"], p["open"]) for p in t["outs"]] == [("", False, False)]
    # the branch `adjust`, which no wire leaves by, stands open
    assert [(p["branch"], p["open"]) for p in s["outs"]] == [("keep", False), ("adjust", True)]
    assert not any("joined:" in p["id"] for card in (s, t) for p in card["ins"] + card["outs"])
    assert s["texts"] == [[True, "adjust", "a_adj"]] and t["texts"] == [[False, "", "q"]]
    start = laid["markers"]["start:periods[0]/S/S:measure:arvl"]
    label = len("starting data μ≺") * 7
    assert (start["kind"], start["width"], start["height"]) == ("start", G["marker"] + G["markerGap"] + label, G["frameLine"])
    assert start["mark"] == {"x": start["width"] - G["marker"], "y": (G["frameLine"] - G["marker"]) / 2, "size": G["marker"]}
    assert start["labelAt"]["x"] == 0 and start["outs"][0]["x"] == start["width"] and start["outs"][0]["side"] == "EAST"
    end = laid["markers"]["end:periods[0]/T/T:measure:cntn"]
    assert end["kind"] == "end" and end["mark"]["x"] == 0 and end["labelAt"]["x"] == G["marker"] + G["markerGap"]
    assert end["ins"][0]["x"] == 0 and end["ins"][0]["side"] == "WEST"
    outside = laid["markers"]["outside:periods[0]/S:periods[1]/S"]
    assert (outside["kind"], outside["mark"]["size"], outside["target"]) == ("outside", G["portMark"], "periods[1]/S")
    wires = {w["id"].split(">>")[0].split("::out::")[0] + " → " + w["id"].split(">>")[1].split("::in::")[0]: w for w in laid["wires"]}
    cable = wires["periods[0]/S___group___ → periods[0]/T___group___"]
    assert (cable["cable"], cable["count"], cable["branch"], cable["join"], cable["dashed"]) == (True, 2, "keep", "keep", False)
    stubs = {key: w for key, w in wires.items() if key.startswith(("start:", "outside:")) or key.endswith("end:periods[0]/T/T:measure:cntn")}
    assert len(stubs) == 3 and all(w["cable"] for w in stubs.values())
    assert [w["dashed"] for key, w in sorted(stubs.items())] == [False, True, False] or sum(w["dashed"] for w in stubs.values()) == 1


# --- design pass 14 ---

# ROUTES with a second `outside` node: `tenure` of periods[1] writes its
# three wires into the markers of `keeper` and of `adjuster` of periods[2],
# whose labels are 17 and 19 characters, 119 and 133 px at 7 px each.
OUTSIDE_ADJUSTER = "outside:periods[1]/tenure:periods[2]/adjuster"
TWO_OUTSIDE = {
    **ROUTES,
    "nodes": ROUTES["nodes"] + [
        {
            "id": OUTSIDE_ADJUSTER, "label": "periods[2]/adjuster", "namespace": "",
            "attrs": [{"key": "kind", "value": "outside"}, {"key": "label", "value": "periods[2]/adjuster"},
                      {"key": "target", "value": "periods[2]/adjuster"}],
            "inputsMetadata": [
                {"id": f"periods[1]/tenure/arvl:{name}",
                 "attrs": [{"key": "label", "value": f"{shown}≺(a, h, z)"}, {"key": "role", "value": role},
                           {"key": "outside", "value": "periods[2]/adjuster"}]}
                for name, shown, role in VALUE_WIRES
            ],
            "incomingEdges": [
                {"sourceNodeId": "periods[1]/tenure/eval/g", "sourceNodeOutputId": f"periods[1]/tenure/arvl:{name}",
                 "targetNodeInputId": f"periods[1]/tenure/arvl:{name}"}
                for name, _, _ in VALUE_WIRES
            ],
        },
    ],
}


# the Node module: builds the graph JSON read on standard input with its
# periods and occurrences open and its builders closed, in the direction it
# names for every layer, lays it out with ELK, settles ELK's answer as the
# page does (`settle`) and reads it; prints the geometry `G`, each boundary
# marker's place with its mark and its label, and each period frame's place
MARKERS_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length < 3));
const built = L.build(m, open, { direction: given.direction }, (text) => Array.from(text || "").length * 7);
const answer = L.settle(built, await new ELK().layout(JSON.parse(JSON.stringify(built.elk))));
const read = L.read(built, answer);
const markers = {}, frames = {};
for (const [id, box] of Object.entries(built.boxes)) {
  const at = read.place[id];
  if (box.type === "marker") markers[id] = { at, mark: box.geom.mark, labelAt: box.geom.labelAt, label: box.spec.label };
  if (box.type === "layer" && box.open && !box.layer.parent) frames[box.namespace] = at;
}
console.log(JSON.stringify({ G: L.G, markers, frames }));
"""


def _mark_center(marker: dict) -> tuple[float, float]:
    """The center of the mark of the marker `marker` (MARKERS_SCRIPT) on the pane."""
    at, mark = marker["at"], marker["mark"]
    return at["ax"] + mark["x"] + mark["size"] / 2, at["ay"] + mark["y"] + mark["size"] / 2


def test_two_markers_laid_out_downward_stand_their_widest_label_and_8_px_apart(node):
    """Design pass 14 §3 (S-D7). In TWO_OUTSIDE, laid out downward, the two
    `outside` markers under the frame of periods[1], whose labels are 119 and
    133 px wide, stand with their marks' centers at least the widest label
    plus 2 · G.markerGap apart, exactly that pitch, so that the labels,
    centered under the marks, do not meet; laid out to the right the same
    two markers stand G.markerPitch apart, their labels beside the marks."""
    script = MARKERS_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    down = node_output(node, script, {"graph": TWO_OUTSIDE, "direction": "DOWN"})
    G = down["G"]
    keeper, adjuster = down["markers"][OUTSIDE_KEEPER], down["markers"][OUTSIDE_ADJUSTER]
    widest = max(keeper["labelAt"]["width"], adjuster["labelAt"]["width"])
    assert widest == len("periods[2]/adjuster") * 7, (keeper["labelAt"], adjuster["labelAt"])
    (kx, ky), (ax, ay) = _mark_center(keeper), _mark_center(adjuster)
    assert abs(kx - ax) >= widest + 2 * G["markerGap"] - 0.01, (kx, ax, widest)
    assert abs(abs(kx - ax) - max(G["markerPitch"], widest + 2 * G["markerGap"])) <= 0.01, (kx, ax, widest)
    assert abs(ky - ay) <= 0.01, (ky, ay)
    # the labels, each centered under its mark, stand apart
    labels = sorted(
        (m["at"]["ax"] + m["labelAt"]["x"], m["at"]["ax"] + m["labelAt"]["x"] + m["labelAt"]["width"])
        for m in (keeper, adjuster)
    )
    assert labels[0][1] <= labels[1][0], labels
    # both stand under the frame of periods[1], which `tenure` of periods[1] writes them from
    frame = down["frames"]["periods[1]"]
    assert min(ky, ay) >= frame["ay"] + frame["height"] + G["markerClear"] - 0.01, (ky, ay, frame)
    right = node_output(node, script, {"graph": TWO_OUTSIDE, "direction": "RIGHT"})
    (kx, ky), (ax, ay) = _mark_center(right["markers"][OUTSIDE_KEEPER]), _mark_center(right["markers"][OUTSIDE_ADJUSTER])
    assert abs(abs(ky - ay) - G["markerPitch"]) <= 0.01, (ky, ay)
    assert abs(kx - ax) <= 0.01, (kx, ax)


# A trellis's initial diagram of two occurrences in two periods (design pass
# 14 §7, rule 5; S-D13), its id INITIAL_IDS' backward one: each occurrence
# holds the three perch layers of its field boxes, `kind` field, and one
# block, `kind` block, in the occurrence's layer, which reads its
# continuation and decision fields and writes its arrival fields; two join
# wires run from the arrival value fields of `S` of periods[1] to the
# continuation value fields of `T` of periods[0], each carrying the route's
# record of two pairs, as the builders graph's edges do. FORWARD_INITIAL
# draws the two state-field pairs of that route in the forward direction.
INITIAL_ROUTE = {
    "branch": None, "source": "periods[0]/T", "destination": "periods[1]/S",
    "source_fields": ["a_nxt", "h_nxt"], "destination_fields": ["a", "h"],
    "pairs": [{"source_field": f"{x}_nxt", "destination_field": x, "origin": "authored", "address": "inter_connectors[0]"}
              for x in "ah"],
    "status": "certified", "law": None,
}


def _initial_field(node_id: str, namespace: str, label: str, role: str, reads=(), writes=()) -> dict:
    """A field box of INITIAL_DIAGRAM in the perch layer `namespace`: its set
    ℝ, a reading port for each (writer, output, input, route) of `reads`,
    and a writing port for each port of `writes`, every port carrying `role`."""
    def port(name: str) -> dict:
        return {"id": name, "attrs": [{"key": "label", "value": label}, {"key": "role", "value": role}]}

    return {
        "id": node_id, "label": label, "namespace": namespace,
        "attrs": [{"key": "kind", "value": "field"}, {"key": "set", "value": "ℝ"}],
        "inputsMetadata": [port(into) for _, _, into, _ in reads],
        "outputsMetadata": [port(name) for name in writes],
        "incomingEdges": [
            {"sourceNodeId": writer, "sourceNodeOutputId": out, "targetNodeInputId": into,
             **({"attrs": [{"key": "route", "value": route}]} if route else {})}
            for writer, out, into, route in reads
        ],
    }


def _initial_block(node_id: str, namespace: str, reads=(), writes=()) -> dict:
    """A block of INITIAL_DIAGRAM in the occurrence's layer `namespace`,
    reading each (writer, port, role) of `reads` and writing each (port,
    role) of `writes`."""
    def port(name: str, role: str) -> dict:
        return {"id": name, "attrs": [{"key": "label", "value": name}, {"key": "role", "value": role}]}

    return {
        "id": node_id, "label": "blk", "namespace": namespace,
        "attrs": [{"key": "kind", "value": "block"}],
        "inputsMetadata": [port(name, role) for _, name, role in reads],
        "outputsMetadata": [port(name, role) for name, role in writes],
        "incomingEdges": [
            {"sourceNodeId": writer, "sourceNodeOutputId": name, "targetNodeInputId": name} for writer, name, _ in reads
        ],
    }


INITIAL_DIAGRAM = {
    "id": "backward initial diagram",
    "groupNodeConfigs": PERIODS["groupNodeConfigs"],
    "nodes": [
        _initial_field("periods[1]/S/S:cntn:V", "periods[1]/S/cntn", "𝑉≻", "value", writes=("S:cntn:V",)),
        _initial_field("periods[1]/S/S:dcsn:c", "periods[1]/S/dcsn", "c", "control", writes=("S:dcsn:c",)),
        _initial_block("periods[1]/S/blk", "periods[1]/S",
                       reads=(("periods[1]/S/S:cntn:V", "S:cntn:V", "value"), ("periods[1]/S/S:dcsn:c", "S:dcsn:c", "control")),
                       writes=(("S:arvl:V", "value"), ("S:arvl:dV", "value"))),
        _initial_field("periods[1]/S/S:arvl:V", "periods[1]/S/arvl", "𝑉≺", "value",
                       reads=(("periods[1]/S/blk", "S:arvl:V", "S:arvl:V", None),), writes=("S:arvl:V",)),
        _initial_field("periods[1]/S/S:arvl:dV", "periods[1]/S/arvl", "𝑑𝑉≺", "value",
                       reads=(("periods[1]/S/blk", "S:arvl:dV", "S:arvl:dV", None),), writes=("S:arvl:dV",)),
        _initial_field("periods[0]/T/T:cntn:V", "periods[0]/T/cntn", "𝑉≻", "value",
                       reads=(("periods[1]/S/S:arvl:V", "S:arvl:V", "S:arvl:V", INITIAL_ROUTE),), writes=("T:cntn:V",)),
        _initial_field("periods[0]/T/T:cntn:dV", "periods[0]/T/cntn", "𝑑𝑉≻", "value",
                       reads=(("periods[1]/S/S:arvl:dV", "S:arvl:dV", "S:arvl:dV", INITIAL_ROUTE),), writes=("T:cntn:dV",)),
        _initial_field("periods[0]/T/T:dcsn:c", "periods[0]/T/dcsn", "c", "control", writes=("T:dcsn:c",)),
        _initial_block("periods[0]/T/blk", "periods[0]/T",
                       reads=(("periods[0]/T/T:cntn:V", "T:cntn:V", "value"), ("periods[0]/T/T:cntn:dV", "T:cntn:dV", "value"),
                              ("periods[0]/T/T:dcsn:c", "T:dcsn:c", "control")),
                       writes=(("T:arvl:V", "value"),)),
        _initial_field("periods[0]/T/T:arvl:V", "periods[0]/T/arvl", "𝑉≺", "value",
                       reads=(("periods[0]/T/blk", "T:arvl:V", "T:arvl:V", None),), writes=("T:arvl:V",)),
    ],
}



FORWARD_FIELD_PAIRS = [
    (f"periods[0]/T/T:cntn:{field}_nxt", f"periods[1]/S/S:arvl:{field}")
    for field in ("a", "h")
]
FORWARD_INITIAL = {
    **INITIAL_DIAGRAM,
    "id": "forward initial diagram",
    "nodes": [
        node
        for field, (source, target) in zip(("a", "h"), FORWARD_FIELD_PAIRS, strict=True)
        for node in (
            _initial_field(source, "periods[0]/T/cntn", f"{field}_nxt", "state", writes=(source,)),
            _initial_field(target, "periods[1]/S/arvl", field, "state",
                           reads=((source, source, target, INITIAL_ROUTE),), writes=(target,)),
        )
    ] + [
        _initial_block("periods[1]/S/blk", "periods[1]/S",
                       reads=tuple((target, target, "state") for _, target in FORWARD_FIELD_PAIRS)),
    ],
}

# the Node module: builds the graph JSON read on standard input with the
# layers it names open, lays it out with ELK and reads
# ELK's answer; prints the occurrences drawn compact, each box with its
# type, whether it is open and the segments of its strip, and each wire's
# boxes, whether it is a cable, its count and the outputs its bundle
# carries
INITIAL_SCRIPT = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const ELK = createRequire(import.meta.url)(%(elk)s);
const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const given = JSON.parse(readFileSync(0, "utf8"));
const m = L.model(given.graph);
const built = L.build(m, new Set(given.open), { direction: given.direction || "DOWN" }, (text) => Array.from(text || "").length * 7);
const read = L.read(built, await new ELK().layout(JSON.parse(JSON.stringify(built.elk))));
const boxes = {};
for (const [id, box] of Object.entries(built.boxes)) {
  boxes[id] = { type: box.type, open: !!box.open, compact: !!box.compact, card: !!(box.geom && box.geom.card),
                segments: box.geom && box.geom.builders ? box.geom.builders.length : null, placed: !!read.place[id] };
}
console.log(JSON.stringify({
  compact: Array.from(built.compact),
  boxes,
  wires: built.wires.map((w) => ({ id: w.id, source: w.source, target: w.target, cable: !!w.cable, count: w.count,
                                   handle: w.sourceHandle, members: w.pairBundle ? w.pairBundle.members.map((member) => member.out) : null,
                                   from: w.from, out: w.out, to: w.to, into: w.into, initialRoute: w.initialRoute || null,
                                   points: read.routes[w.id], parts: read.parts[w.id] || [] })),
  initialRoutes: read.initialRoutes || [],
}));
"""


def test_a_trellis_initial_diagram_draws_a_card_with_no_strip_and_one_cable_between_two_cards(node):
    """Design pass 14 §7, rule 5 (S-D13). In INITIAL_DIAGRAM, with its
    periods open and its occurrences closed, no occurrence is drawn compact,
    each occurrence is a card with no segment in its strip, since its layers
    are perches and not builders, and the two join wires from `S`'s arrival
    fields to `T`'s continuation fields are one cable of count 2 from one
    plug of `S`'s card into one socket of `T`'s, as the builders graph
    draws a route's values (design pass 12 §2). With every layer open, the
    occurrences and their perches open, the layout holds a box for each
    field and each block, no occurrence is compact, and the ten wires,
    the two joins and the eight between the fields and the blocks, are laid
    out without error."""
    script = INITIAL_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    closed = node_output(node, script, {"graph": INITIAL_DIAGRAM, "open": ["periods[0]", "periods[1]"]})
    assert closed["compact"] == []
    s, t = closed["boxes"]["periods[1]/S___group___"], closed["boxes"]["periods[0]/T___group___"]
    for card in (s, t):
        assert (card["type"], card["open"], card["compact"], card["card"], card["segments"], card["placed"]) == ("layer", False, False, True, 0, True), card
    assert not [id for id, box in closed["boxes"].items() if box["type"] == "builder"]
    assert [(w["source"], w["target"], w["cable"], w["count"], w["members"]) for w in closed["wires"]] == [
        ("periods[1]/S___group___", "periods[0]/T___group___", True, 2, ["S:arvl:V", "S:arvl:dV"])
    ]
    assert closed["wires"][0]["handle"] == "periods[1]/S___group___::out::stages::periods[1]/S|periods[0]/T"
    every = node_output(node, script, {"graph": INITIAL_DIAGRAM, "open": list({node["namespace"] for node in INITIAL_DIAGRAM["nodes"]} | {"periods[0]", "periods[1]"})})
    assert every["compact"] == []
    types = {}
    for box in every["boxes"].values():
        types[box["type"]] = types.get(box["type"], 0) + 1
    assert types["field"] == 8 and types["block"] == 2 and "builder" not in types, types
    assert all(box["placed"] for box in every["boxes"].values()), every["boxes"]
    assert all(box["open"] and not box["compact"] for id, box in every["boxes"].items() if box["type"] == "layer"), every["boxes"]
    assert len(every["wires"]) == 10 and not any(w["cable"] for w in every["wires"]), every["wires"]
    # every wire counts the wires drawn as its line, one: a join wire's route of two pairs gives it no count of
    # two, which a measure wire of the builders graph takes from its route (design pass 14 §7, rule 5)
    assert {w["count"] for w in every["wires"]} == {1}, every["wires"]


def test_forward_initial_route_groups_the_field_pairs_in_both_canvas_orientations(node):
    """A route across two periods has one cable, with individual connections at open fields."""
    script = INITIAL_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    periods = ["periods[0]", "periods[1]"]
    writer = ["periods[0]/T", "periods[0]/T/cntn"]
    reader = ["periods[1]/S", "periods[1]/S/arvl"]
    writer_card, reader_card = "periods[0]/T___group___", "periods[1]/S___group___"
    for direction in ("DOWN", "RIGHT"):
        for writer_open, reader_open in ((False, False), (True, False), (False, True), (True, True)):
            opened = periods + (writer if writer_open else []) + (reader if reader_open else [])
            answer = node_output(node, script, {"graph": FORWARD_INITIAL, "open": opened, "direction": direction})
            assert len(answer["initialRoutes"]) == 1, answer["initialRoutes"]
            cable = answer["initialRoutes"][0]
            assert cable["route"] == INITIAL_ROUTE and cable["count"] == 2
            assert len(cable["points"]) >= 2
            joined = [w for w in answer["wires"] if w["initialRoute"] == cable["id"]]
            assert set(cable["wires"]) == {w["id"] for w in joined}
            if not writer_open and not reader_open:
                assert [(w["source"], w["target"], w["parts"]) for w in joined] == [(writer_card, reader_card, [])]
                continue
            assert {(w["source"], w["out"], w["target"], w["into"]) for w in joined} == {
                (source if writer_open else writer_card, source, target if reader_open else reader_card, target)
                for source, target in FORWARD_FIELD_PAIRS
            }
            for wire in joined:
                parts = wire["parts"]
                assert len(parts) == sum((writer_open, reader_open))
                assert all(len(part) >= 2 for part in parts)
                if writer_open:
                    assert parts[0][0] == wire["points"][0]
                if reader_open:
                    assert parts[-1][-1] == wire["points"][-1]
            local_writers = {w["source"] for w in answer["wires"] if w["initialRoute"] is None}
            assert local_writers == ({target for _, target in FORWARD_FIELD_PAIRS} if reader_open else set())


def test_forward_operator_keeps_a_native_measure_from_a_stage_named_joined(node):
    occurrence = "periods[0]/cons"
    inputs, operator, outputs = _occurrence(0, "μ≻(a)")
    measure = _port(f"{occurrence}/joined:measure:arvl", "μ≺(m)")
    measure["attrs"].append({"key": "role", "value": "measure"})
    inputs["outputsMetadata"] = [measure]
    operator["inputsMetadata"] = [measure]
    operator["incomingEdges"] = [{"sourceNodeId": inputs["id"], "sourceNodeOutputId": measure["id"],
                                  "targetNodeInputId": measure["id"]}]
    graph = {**FRAMES, "id": "forward", "nodes": [inputs, operator, outputs]}
    script = INITIAL_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    answer = node_output(node, script, {"graph": graph, "open": ["periods[0]", occurrence, f"{occurrence}/push"]})
    assert answer["boxes"][inputs["id"]]["placed"]
    assert outputs["id"] not in answer["boxes"]
    (wire,) = answer["wires"]
    assert (wire["source"], wire["out"], wire["target"], wire["into"]) == (
        inputs["id"], measure["id"], operator["id"], measure["id"],
    )


def test_durables_forward_initial_draws_separate_routes_to_the_same_stage(node):
    folder = model.open_folder(DURABLES_MODEL)
    source = recipe.Source("recipe", "declaration/spec.yml")
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, source, restriction, initial=True).shown
    graph = next(graph for graph in shown.collection["graphs"] if graph["id"] == "forward initial diagram")
    script = INITIAL_SCRIPT % {"script": json.dumps(str(LAYOUT)), "elk": json.dumps(str(ELK))}
    answer = node_output(node, script, {"graph": graph, "open": ["periods[0]", "periods[1]", "periods[2]"]})
    for destination, writing_period in (("periods[0]/tenure", 1), ("periods[0]/bequest", 0)):
        cables = [cable for cable in answer["initialRoutes"] if cable["route"]["destination"] == destination]
        assert {(cable["route"]["source"], cable["count"]) for cable in cables} == {
            (f"periods[{writing_period}]/keeper_cons", 3),
            (f"periods[{writing_period}]/adjuster_cons", 3),
        }
        first, second = cables
        assert first["points"] != second["points"]
        assert set(first["wires"]).isdisjoint(second["wires"])
