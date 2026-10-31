/* The layout of one exported graph for the pane.

   Input: one graph of the collection the package's exporter writes
   (`to_model_explorer`, the graph format of Model Explorer): nodes with a
   namespace, attributes, ports and the wires each reads (`incomingEdges`). Output: an ELK graph, and,
   from ELK's answer, the place of every box and the route of every wire.

   Every layer is laid out on its own, in the direction the exporter gives it
   (groupNodeConfigs), and a wire that crosses the border of an open layer is
   cut there, so that each piece runs inside one layer. A closed layer's box
   carries a port for each wire that crosses its border, and a port for each
   port of a node inside it that the exporter marks `unjoined`, under that
   port's own id (model interface specification 0.4, §3.4). The box of a
   closed stage occurrence of a trellis graph also carries every field port
   of the occurrence's own `Inputs` and `Outputs` (unit K's decision
   K-D15), and is drawn as a card (AAS, L-D16 and L-D25; design pass 7 §3,
   `frameGeometry`): the name's row, and a row for each field port no join
   reaches, every other port standing as a mark on its edge; an open
   occurrence's own `Inputs` and `Outputs` print their field ports' labels
   beside their ports, in the face of their own name, laid out in the
   direction of the occurrence's frame (unit K, Task 21). An open
   occurrence none of whose builders is open is drawn compact (AAS, L-D7):
   ELK lays it out as the card of a closed occurrence, with the same ports,
   and a strip of its builders under its name, one segment of equal width
   for each, which ELK does not lay out, in the order of the pair of
   perches each joins as the caller's records give it (`options.builders`,
   by the builder layer's namespace). A card whose namespace
   `options.unfold` names, or every card where it is true, prints every
   field's name in a row of its own, its strip the band of Task 24 (AAS,
   L-D19 as L-D25 amends it). Within an open period, the wires from one
   card to another are one bundle where they are two or more, unless
   `options.split` names either card or the bundle (AAS, L-D25); the wires
   that carry a value, as a backward trellis graph's do, are one cable for
   each route, within a period or from one period to the next, from a card
   to a card or between a card and a boundary marker, which nothing splits,
   each leaving its writer's card at a plug of its own (design pass 12 §2).
   In a stage's builders graph a value is one wire, drawn as a line of its
   own with the arrowhead a stage graph's wire keeps, and nothing is
   bundled (AMD-MB-001 §5.4): a value carries its derivatives, which a
   port's hover lists under the wire's label, one per line, `D_{m_d}𝑉`
   for each coordinate the value's stated derivative lines name
   (`derivativeLabels`); a measure, a control or a field wire is likewise
   a line of its own, and an initial diagram, whose boxes are fields and
   blocks, bundles nothing (design pass 14 §1; S-D2 to S-D4).
   A card, a period's head, the graph's own `Inputs` and `Outputs` and a
   wire's label take the sizes of design pass 8's mock (M-D15). A wire
   that carries joins prints a label (`wireLabel`): in a backward trellis
   graph the name of the value it carries, as its reading
   port's label names that function, and a bundle the names its wires
   carry (AAS, L-D26); otherwise the label of its joins (unit K's decision
   K-D4). Two or
   more wires from one open period to one reading port in another open period
   share their piece at the graph's root, the bundle of unit K's decision
   K-D5. A `+ period` control the caller names (`options.adds`, §3.6)
   prints its two words, `+ period` (unit K's decision K-D14). Between two
   periods it is placed after the layout in the gap between their layers,
   past the pieces of the root that cross the gap, each of which keeps the
   control's room, or past an edge of the root that keeps that room where no
   piece crosses it, which ELK lays out and no wire draws (K-D13). At the
   earliest end it is a box of the root before the earliest period's layer,
   held there by such an edge. With `options.adds`, a period's open layer
   is wide enough for its control `+ stage` beside its name (K-D14). In the
   stage view, a graph with no period's layer, a box's label is cut at
   G.labelMax, and in a stage's builders graph laid out downward the open
   frames of its builders are aligned (AAS, L-D20; `arrange`): the boxes
   of every open frame stand centered on its vertical axis, every open
   frame of a builder takes the width of the widest, and the builders that
   wires join one to another stand in one column with the stage's `Inputs`
   and `Outputs`, on one axis, their open frames of one left edge, every
   other builder, the policy builder among them, beside the column. A
   card's ports are the cables' (design pass 10 §6; unit N, Task 7): one
   per continuation branch on its writing side, the port of the wire that
   leaves by the branch or one of the card's own, and one for the arrival
   tuple on its reading side (`frameGeometry`); a boundary node of the
   root, a marker, is a box of its mark and its label, the mark at the end
   nearer the card (`markerGeometry`); a wire between two cards, or between
   a card and a marker, is a cable, whose label is its route's branch or
   the count of its wires (`cableLabel`), the count its record carries,
   `count`, and whose stub to an `outside` marker is dashed. No DOM is
   touched: the caller supplies `measure(text, role)`, the width of a text
   in pixels. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.BellmanFlowLayout = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var LAYER_ENDING = '___group___';
  var G = {                  // the geometry of a box, in pixels at zoom 1; brand.css places the rows by the same numbers
    padX: 9, padTop: 6, padBottom: 7,
    // Changes to --bl-graph-label-size or --bl-graph-port-size also change these line heights.
    labelH: 17, subH: 12, portH: 12,
    // the graph's own `Inputs` and `Outputs` (design pass 8's mock; AAS, M-D15): 64 by 24, the name in the
    // face of a frame's name on a line of frameLine, centered in the box
    minW: 140, minH: 32, boundaryW: 64, boundaryH: 24, layerW: 172, portGap: 12, portMin: 12, sideRow: 15,
    // the line of a frame's name, 11 px, and of a stage's name, 12.5 px, as brand.css's .bf-t-frame and
    // .bf-t-stage set them; the room above and below a period's name in its head; and the widest a stage's
    // name makes its card, past which the name is cut with an ellipsis (design pass 10 §5)
    frameLine: 16, stageLine: 18, periodPad: 4, frameNameMax: 180,
    layerPad: 8, toggle: 40,
    // an `add` control, `Stage` in a period's head or `Period` in the gap between two periods (design pass 13
    // §2, rule 8): its height, the Codicon `add` before its word, drawn at 12 px with its center on the middle of
    // the word's cap height (design pass 14 §8; S-D15), the room between the glyph and the word, and the room at
    // each side
    addH: 24, addIcon: 12, addGap: 4, addPad: 4,
    // the space between a period's name and its control `Stage` (K-D14)
    stageGap: 12,
    // the height of a row of an open occurrence's own `Inputs` or `Outputs`, which holds a port and its label
    // in the face of the box's name, and the least space between a reading label and a writing label of one
    // row (K-D15; unit K, Task 21)
    fieldRow: 19, fieldGap: 16,
    // the card of a stage occurrence (design pass 13 §2; AAS, L-D16 and L-D25), every y from the card's outer
    // top edge, its 1-px border included: the card at rest is cardH high; its axis, on which the socket, a
    // single plug, the chevron's middle and the middle of the name's x-height stand; the top of the name's
    // line box, stageLine high; the inset of the name, of a row's text and of the strip's left end; the room
    // between the name's end and the chevron's glyph box, the glyph box itself, 16 px drawn at 0.75, and its
    // room to the card's right edge, so that the name takes at most the width less cardChrome; the chevron's
    // press target, 24 px square (spec 0.4 §5.8); the strip of builders, from cardStripY, cardStripH high,
    // ending cardStripRight before the right edge, its segments cardSegmentGap apart; the band a selected
    // card draws in its place, cardBandH high from cardBandLeft, ending by cardBandRight before the right
    // edge, each segment its id with cardIdPad, plus its signs with cardSignsPad where it has signs, rounded
    // up to cardStep; a row of a field's name, frameRow high; the fill under the last row or the strip; the
    // least width; and the step every width takes, w = max(frameW, cardStep·⌈(name + cardChrome)/cardStep⌉),
    // at most frameNameMax, past which the name is cut
    cardH: 32, cardAxis: 14, cardNameTop: 3, cardInset: 9, cardNameGap: 4, cardChevron: 12, cardChevronEdge: 10,
    cardChevronTarget: 24, cardStripY: 24, cardStripH: 3, cardStripRight: 29, cardSegmentGap: 2,
    cardBandH: 20, cardBandLeft: 1, cardBandRight: 8, cardIdPad: 12, cardSignsPad: 4, cardStep: 8,
    frameRow: 12, framePad: 4, frameW: 80,
    // the widest a box's label stands in the stage view; a longer label is cut with an ellipsis (AAS, L-D20)
    labelMax: 320,
    // the line of a wire's label, in STIX Two Math, upright, at 9.5 px, set over its wire (design pass 10 §5)
    joinLine: 12,
    // a port's mark in both graphs, a 6-px square whose center stands on its box's edge, its transparent
    // press target of 10 px, and the space between the centers of two plugs of one edge (design pass 13 §1,
    // rules 1 to 3)
    portMark: 6, portTarget: 10, cablePitch: 12,
    // a boundary marker (design pass 13 §1, rule 6): the 8-px circle of a terminal marker, where data enter or
    // leave the drawn range, the space between a mark and its label, the room between a mark's near face and
    // the border of the frame it joins, the least space between the centers of two marks of one frame's side,
    // laid out to the right, and laid out downward at least the widest label of the group with markerGap at each
    // side (design pass 14 §3; S-D7), and the room between the frame's border and the vertical run of a stub
    // that bends, outside the frame (the fix wave Q3a, item 6); an outside marker draws the far card's port, a
    // mark of portMark
    marker: 8, markerGap: 4, markerClear: 24, markerPitch: 28, markerBend: 8,
    // the bus mark of a cable of two or more wires (design pass 13 §1, rule 5): the least length of a cable's
    // first run from its plug, the slash's length, the slash's center from the plug's outer face, the room
    // between the slash's end and the count's left edge, the count's baseline below a cable's line where the
    // count stands under it, and the room a first run keeps past the count's right edge
    firstRun: 24, slash: 6, slashAlong: 8, countGap: 1, countBelow: 9.7, countRoom: 4
  };
  // The width a card's name adds to its own: its inset, the room before the chevron's glyph box, the box and
  // its room to the edge, 35 px (design pass 13 §2, rule 6).
  G.cardChrome = G.cardInset + G.cardNameGap + G.cardChevron + G.cardChevronEdge;
  // The pair the caller's record of a builder gives the policy builder
  // (`trellis.builder_records`; AAS, L-D7).
  var POLICY = 'policy';
  // The prefix of the id of the bundle of an ordered pair of stage
  // occurrences within a period, followed by the two namespaces joined by
  // `|`, the writer's first (AAS, L-D25).
  var PAIR_BUNDLE = 'stages::';
  // A 40-pixel control is 24 screen pixels at the reading scale of 0.6 (§5.8).
  G.layerHeader = G.toggle + 5;
  // The head of a period's open layer, its name's line with G.periodPad above and below it (design pass 10
  // §5): the toggle keeps its target of G.toggle, standing on the head's foot and over the layer's top edge,
  // on the ground of the graph's root, where nothing else stands (AAS, M-D15).
  G.periodHeader = G.frameLine + 2 * G.periodPad;
  // The spacing of a period's layer (design pass 13 §2, rule 9; §1, rule 4): two cards of one column stand
  // periodSpread apart; two columns periodColumns apart with one slot of vertical runs between them, periodSlot
  // more for each further slot, every vertical run periodEdge from the cards on both sides, so that a cable's
  // first run from its plug is at least G.firstRun; the frame's paddings, its head and periodTop above the
  // first card, periodLeft at the reading side, periodRight at the writing side, where a bus mark and its
  // count stand inside the frame, and periodBottom under the last card; and at the graph's root, periods
  // periodGap apart, a vertical run between them rootEdge from either frame.
  G.periodSpread = 24;
  G.periodColumns = 48;
  G.periodEdge = 24;
  G.periodSlot = 8;
  G.periodTop = 8;
  G.periodLeft = 8;
  G.periodRight = 24;
  G.periodBottom = 16;
  G.periodGap = 40;
  G.rootEdge = 20;

  // The word of the control that adds a period, in the gap between two
  // periods, and of the control that adds a stage, in a period's head, each
  // after the Codicon `add` (design pass 13 §2, rule 8; unit K's decision K-D14).
  var PERIOD_WORDS = 'Period', STAGE_WORDS = 'Stage';

  // The prefix of the id of a `+ period` control's box, followed by its target.
  var ADD_PERIOD = 'add-period::';
  var BETWEEN = /^between periods\[(\d+)\] and periods\[(\d+)\]$/;

  /* The namespaces of the period layers a `+ period` control stands
     between, in time order (§3.6): `earlier`, the period before it, none
     at the earliest end, and `later`, the period after it, read from its
     target and, at the earliest end, from `after`, the earliest period's
     layer id. */
  function addPeriods(add) {
    var found = BETWEEN.exec(add.target);
    if (found) return { earlier: 'periods[' + found[1] + ']', later: 'periods[' + found[2] + ']' };
    var later = add.after && add.after.slice(-LAYER_ENDING.length) === LAYER_ENDING ? add.after.slice(0, -LAYER_ENDING.length) : null;
    return { earlier: null, later: later };
  }

  function attrsOf(list) {
    var out = {};
    (list || []).forEach(function (a) { if (a.key !== '__tensor_tag') out[a.key] = a.value; });
    return out;
  }

  /* The configuration of a layer, from the graph's groupNodeConfigs: the
     first whose pattern matches the namespace. */
  function configOf(graph, namespace) {
    var configs = graph.groupNodeConfigs || [];
    for (var i = 0; i < configs.length; i++) if (new RegExp(configs[i].namespaceRegex).test(namespace)) return configs[i];
    return {};
  }
  function directionOf(graph, namespace, override) {
    if (override) return override;
    return configOf(graph, namespace).layoutDirection === 1 ? 'RIGHT' : 'DOWN';
  }

  // The kinds of the boundary nodes the exporter writes at a trellis graph's
  // root, where data enter or leave the drawn range (the package's
  // BOUNDARY_KINDS; design pass 10 §6; unit N, Task 6).
  var BOUNDARY_KINDS = ['start', 'end', 'outside'];

  /* The graph as the pane reads it: nodes by id, layers by namespace, wires.
     A node of the root whose `kind` is a boundary kind is a marker,
     `marker` its kind (design pass 10 §6); a wire carries the attributes
     of its edge, the record of its route among them (unit N, Task 6). */
  function model(graph) {
    var nodes = {}, layers = {}, order = [];
    function layer(ns) {
      if (ns === '') return null;
      if (!layers[ns]) {
        var cut = ns.lastIndexOf('/');
        var parent = cut < 0 ? '' : ns.slice(0, cut);
        layers[ns] = { id: ns + LAYER_ENDING, namespace: ns, name: cut < 0 ? ns : ns.slice(cut + 1), parent: parent,
                       attrs: (graph.groupNodeAttributes || {})[ns] || {}, config: configOf(graph, ns) };
        if (parent) layer(parent);
      }
      return layers[ns];
    }
    graph.nodes.forEach(function (n) {
      var ns = n.namespace || '';
      var attrs = attrsOf(n.attrs);
      nodes[n.id] = {
        id: n.id, label: n.label, namespace: ns, attrs: attrs, style: n.style || {},
        marker: !ns && BOUNDARY_KINDS.indexOf(attrs.kind) >= 0 ? attrs.kind : null,
        inputs: (n.inputsMetadata || []).map(function (p) { return { id: p.id, attrs: attrsOf(p.attrs) }; }),
        outputs: (n.outputsMetadata || []).map(function (p) { return { id: p.id, attrs: attrsOf(p.attrs) }; }),
        incoming: n.incomingEdges || []
      };
      order.push(n.id);
      if (ns) layer(ns);
    });
    var wires = [];
    order.forEach(function (id) {
      nodes[id].incoming.forEach(function (e) {
        wires.push({ from: e.sourceNodeId, out: e.sourceNodeOutputId, to: id, into: e.targetNodeInputId, attrs: attrsOf(e.attrs) });
      });
      // an input of a builder a method block opens that no operation inside it reads, which the graph JSON names
      // as `<writer>::<output>` under `unread` on the reading port of the line that enters the builder from the
      // same writer: one more wire of that line, so that the line is the bundle of the wires the builder's header
      // lists (specification 0.6 §9; the controller's first ruling on design pass 15, SE-19)
      nodes[id].inputs.forEach(function (p) {
        (p.attrs.unread ? String(p.attrs.unread).split('; ') : []).forEach(function (named) {
          var cut = named.indexOf('::');
          wires.push({ from: named.slice(0, cut), out: named.slice(cut + 2), to: id, into: p.id, attrs: {} });
        });
      });
    });
    return { graph: graph, nodes: nodes, layers: layers, order: order, wires: wires };
  }

  /* The namespaces above a namespace, outermost first, itself last. */
  function chain(ns) {
    if (!ns) return [];
    var parts = ns.split('/'), out = [];
    for (var i = 1; i <= parts.length; i++) out.push(parts.slice(0, i).join('/'));
    return out;
  }

  /* What stands on the pane for a node: itself where every layer above it is
     open, else the outermost closed layer above it. */
  function shown(m, id, open) {
    var above = chain(m.nodes[id].namespace);
    for (var i = 0; i < above.length; i++) if (!open.has(above[i])) return { layer: above[i] };
    return { node: id };
  }

  /* The place of each output port of the graph among all its output ports,
     by `<node>|<output>`: the nodes in the graph JSON's order and each
     node's outputs in their own order (unit K's decision K-D12). */
  function outputRanks(m) {
    var rank = Object.create(null), count = 0;
    m.order.forEach(function (id) { m.nodes[id].outputs.forEach(function (p) { rank[id + '|' + p.id] = count++; }); });
    return rank;
  }
  /* The comparison of two keys `<node>|<output>` by their ranks; a key with
     no rank stands after every ranked key. */
  function byRank(rank) {
    return function (p, q) {
      var a = p in rank ? rank[p] : Infinity, b = q in rank ? rank[q] : Infinity;
      return a < b ? -1 : a > b ? 1 : 0;
    };
  }

  // The namespace of a period layer of a trellis graph (spec 0.4 §3.1).
  var PERIOD = /^periods\[\d+\]$/;
  // The namespace of a stage occurrence's layer of a trellis graph, `periods[h]/<key>` (spec 0.4 §2.6).
  var OCCURRENCE = /^periods\[\d+\]\/[^/]+$/;
  // The id of a trellis's initial diagram, `backward initial diagram` or
  // `forward initial diagram` (the package's INITIAL_IDS), whose occurrences
  // hold the perches' layers of field boxes and the blocks, and no builder
  // (design pass 14 §7, rule 5; S-D13).
  var INITIAL_GRAPH = /initial diagram$/;
  function initialDiagram(m) { return INITIAL_GRAPH.test((m.graph && m.graph.id) || ''); }

  /* The stage occurrences of a trellis graph drawn compact with the layers
     of `open` open (AAS, L-D7): each open occurrence, every layer above it
     open, that holds a builder's layer and no open layer. In a trellis's
     initial diagram an occurrence's layers are perches, not builders, so
     no occurrence is drawn compact: a closed one is its card with no
     strip, and an open one its layer with its perches (design pass 14 §7,
     rule 5; S-D13). */
  function compactOccurrences(m, open) {
    var children = {}, found = new Set();
    if (initialDiagram(m)) return found;
    Object.keys(m.layers).forEach(function (ns) {
      var parent = m.layers[ns].parent;
      (children[parent] = children[parent] || []).push(ns);
    });
    Object.keys(m.layers).forEach(function (ns) {
      var kids = children[ns] || [];
      if (!OCCURRENCE.test(ns) || !open.has(ns) || !kids.length) return;
      if (!chain(m.layers[ns].parent).every(function (a) { return open.has(a); })) return;
      if (!kids.some(function (k) { return open.has(k); })) found.add(ns);
    });
    return found;
  }

  /* The namespace of the period layer in which a node stands, `periods[h]`,
     or null for a node outside every period. */
  function periodOf(m, id) {
    var outer = chain(m.nodes[id].namespace)[0] || '';
    return PERIOD.test(outer) ? outer : null;
  }

  /* The rank of each stage key of a trellis graph, by which every period
     stands its occurrences in rows, the same in every period of both
     graphs (the fix wave Q3a, item 2, which amends K-D12: the ports follow
     the readers' rank, not the readers the writer's ports): its place in
     `order`, the recipe's `stages:` list as the page gives it, then the
     keys `order` does not name in the order the graph JSON first names
     their occurrences. */
  function stageRanks(m, order) {
    var rank = Object.create(null), n = 0;
    (order || []).forEach(function (key) { if (!(key in rank)) rank[key] = n++; });
    Object.keys(m.layers).forEach(function (ns) {
      if (!OCCURRENCE.test(ns)) return;
      var key = ns.split('/')[1];
      if (!(key in rank)) rank[key] = n++;
    });
    return rank;
  }

  // The id of a port the exporter adds to a stage occurrence of the forward
  // trellis graph for one state field, `periods[h]/<key>/unjoined:<identity>`
  // or `periods[h]/<key>/joined:<identity>` (specification 0.4 §3.4, J-D16).
  var FIELD_PORT = /\/(?:un)?joined:[^/]+$/;
  // The id of such a port for a field no join reaches (J-D16).
  var UNJOINED_FIELD = /\/unjoined:[^/]+$/;
  // The perch's sign at the end of a field's label, which the side of the
  // field's port on a card says (design pass 5 §2).
  var PERCH_SIGN = /[≺≻]$/;

  /* The words a card prints for the field whose label the graph JSON
     writes `label` (design pass 5 §2): `branch`, the branch of a branching
     stage the field leaves by, the text before `: `, or nothing; and
     `name`, the rest without the perch's sign, `keep: w_kp≻` giving
     `keep` and `w_kp`. */
  function fieldWords(label) {
    var cut = label.indexOf(': ');
    return { branch: cut < 0 ? '' : label.slice(0, cut), name: (cut < 0 ? label : label.slice(cut + 2)).replace(PERCH_SIGN, '') };
  }

  /* The text printed at an output port of a box other than those
     `frameGeometry` and `fieldsGeometry` lay out, a stage occurrence's card
     and an open occurrence's own `Inputs` and `Outputs`: its field's label for a field
     port of the forward trellis graph, which a closed period carries
     (J-D47), and nothing for every other port, whose label stands in its
     handle's title (R-D49). */
  function portLabel(port) {
    return FIELD_PORT.test(port.id) ? port.attrs.label || '' : '';
  }

  // The most characters a label printed on a wire takes (spec 0.4 §2.1).
  var LABEL_MOST = 22;

  /* The label a wire prints for the joins it carries (unit K's decision
     K-D4), from the reading port's attribute `join`, whose entries,
     `[mapping ]field[ → arrival]`, the exporter joins by `; `: that text
     where it has at most 22 characters; else the arrival fields its entries
     reach, each once, in the entries' order, joined by `, `, where those
     have at most 22 characters; else the number of its entries, `6 joins`.
     Characters are counted as code points. */
  function joinLabel(text) {
    if (!text || Array.from(text).length <= LABEL_MOST) return text || '';
    var entries = text.split('; '), fields = [];
    entries.forEach(function (entry) {
      var arrow = entry.lastIndexOf(' → ');
      var field = arrow < 0 ? entry.slice(entry.lastIndexOf(' ') + 1) : entry.slice(arrow + 3);
      if (fields.indexOf(field) < 0) fields.push(field);
    });
    var named = fields.join(', ');
    if (Array.from(named).length <= LABEL_MOST) return named;
    return entries.length + (entries.length === 1 ? ' join' : ' joins');
  }

  // The one role of a wire that carries a function of the state, as the
  // exporter writes it on a port: the value, the field a stage file marks
  // `!vlu`; a value's derivatives are a property of the value and no wire
  // (AMD-MB-001 §3).
  var VALUE_ROLES = ['value'];
  // The perch's sign or the opening of the coordinates, which end a
  // function's name in a port's label.
  var NAME_END = /[≺≻(]/;

  /* The name of the function a join carries into the reading port `port`
     where the port's role is a value role (AAS, L-D26; design pass 7 §3):
     the port's label as the exporter writes it, `𝑑𝑉_a≻(a_nxt_kp, h_nxt_kp,
     z_nxt_kp)`, up to the perch's sign or the coordinates, `𝑑𝑉_a`, in the
     mathematical italic the exporter writes a function in. The empty text
     for a port that carries no value role. */
  function valueName(port) {
    var attrs = port.attrs || {};
    return VALUE_ROLES.indexOf(attrs.role) >= 0 ? (attrs.label || '').split(NAME_END)[0] : '';
  }

  /* The derivatives the value wire read at `port` carries by a stated line,
     as the port's hover lists them under the wire's label (AMD-MB-001
     §5.4): the exporter's `derivatives`, the coordinates named, each as
     `D_{m_d}𝑉`, the operator roman and the function's name as `valueName`
     gives it; none for a port whose value states no derivative. */
  function derivativeLabels(port) {
    var attrs = port.attrs || {};
    if (!attrs.derivatives) return [];
    var name = valueName(port);
    return attrs.derivatives.split(', ').map(function (x) { return 'D_{' + x + '}' + name; });
  }

  /* The label a cable prints while it is hovered (design pass 13 §1, rule
     7): the name of its branch, `keep`, and nothing where the branch has no
     name, since the count of its wires stands at its plug (Q-D17). */
  function cableLabel(branch, count) {
    return branch || '';
  }

  /* The label a wire prints for the joins its reading port `port` names,
     the empty text where it names none: in a backward trellis graph, whose
     joins carry values, the name of the function the
     wire carries (`valueName`; AAS, L-D26), so that no state field labels a
     backward wire; for every other wire the label of the joins
     (`joinLabel`, K-D4). */
  function wireLabel(port) {
    var attrs = port.attrs || {};
    if (!attrs.join) return '';
    return VALUE_ROLES.indexOf(attrs.role) >= 0 ? valueName(port) : joinLabel(attrs.join);
  }

  /* The size of the own `Inputs` or `Outputs` of an open stage occurrence
     of a trellis graph and the places of its ports (`spec.fields`; unit K,
     Task 21, which builds K-D15 for an occurrence drawn in full). The box
     prints its name at its head and, beside every port, the port's label as
     the graph JSON writes it (`attrs.label`), in the face of its name,
     `face`, which is the role of `spec`; each port keeps its label in its
     handle's title. Laid out to the right (`dir` RIGHT), the reading ports
     stand on the left edge and the writing ports on the right edge, one row
     of G.fieldRow for each port under the head, each side from the first
     row, each reading label at the left and each writing label at the
     right; the box is as high as the head and the rows of its fuller side,
     and as wide as the larger of its least width, its head and its widest
     reading label, its widest writing label and G.fieldGap between them,
     with G.padX at each side. Laid out downward, the reading ports stand on
     the top edge and the writing ports on the bottom edge, each side's
     labels in one row along its edge, the head between the two rows, at
     `nameTop`. */
  function fieldsGeometry(spec, dir, measure) {
    var face = spec.role;
    function port(p) {
      var full = p.attrs.label || '';
      return { id: p.id, text: full, w: full ? measure(full, face) : 0, full: full, attrs: p.attrs, wire: !!p.wire };
    }
    var ins = spec.inputs.map(port), outs = spec.outputs.map(port);
    // the name and the two one-pixel borders
    var labelW = measure(spec.label, face) + 2;
    var head = G.labelH;
    // the least size of a graph's own `Inputs` or `Outputs`
    var minW = G.boundaryW, minH = G.boundaryH;
    var w, h, nameTop = G.padTop;
    function widest(list) { return list.reduce(function (a, p) { return Math.max(a, p.w); }, 0); }
    if (dir === 'DOWN') {
      // each side's ports in one row along its edge, each as wide as its label, its center the port's place
      var row = function (list) {
        var slots = list.map(function (p) { return Math.max(p.w, G.portMin); });
        return { slots: slots, width: slots.reduce(function (a, b) { return a + b; }, 0) + Math.max(0, list.length - 1) * G.portGap,
                 height: list.some(function (p) { return p.text; }) ? G.fieldRow : 0 };
      };
      var top = row(ins), bottom = row(outs);
      nameTop = G.padTop + top.height;
      w = Math.max(minW, labelW + 2 * G.padX, top.width + 2 * G.padX, bottom.width + 2 * G.padX);
      h = Math.max(minH, nameTop + head + 2 + bottom.height + G.padBottom);
      [[ins, top, 0, 'NORTH'], [outs, bottom, h, 'SOUTH']].forEach(function (side) {
        var x = (w - side[1].width) / 2;
        side[0].forEach(function (p, i) {
          p.x = Math.round(x + side[1].slots[i] / 2); p.y = side[2]; p.side = side[3];
          x += side[1].slots[i] + G.portGap;
        });
      });
    } else {
      var inW = widest(ins), outW = widest(outs);
      var columns = inW + outW + (inW && outW ? G.fieldGap : 0);
      var first = G.padTop + head + 2, rows = Math.max(ins.length, outs.length);
      w = Math.max(minW, labelW + 2 * G.padX, columns + 2 * G.padX);
      h = Math.max(minH, first + rows * G.fieldRow + G.padBottom);
      [[ins, 0, 'WEST'], [outs, w, 'EAST']].forEach(function (side) {
        side[0].forEach(function (p, i) {
          p.x = side[1]; p.y = Math.round(first + i * G.fieldRow + G.fieldRow / 2); p.side = side[2];
        });
      });
    }
    return { width: Math.ceil(w), height: Math.ceil(h), ins: ins, outs: outs, face: face, nameTop: nameTop };
  }

  /* The card of a stage occurrence of a trellis graph, closed or drawn
     compact (AAS, L-D7, L-D16 and L-D25; design pass 7 §3), one drawing
     for both (design pass 13 §2), and the places of its ports. Every y is
     measured from the card's outer top edge, its 1-px border included. At
     rest the card is G.cardH high: the name's line box, G.stageLine high,
     from G.cardNameTop, G.cardInset from the left edge, in the face of a
     stage's name, cut with an ellipsis where the name is wider than the
     width less G.cardChrome, the card then answering `cut`; the chevron's
     glyph box, G.cardChevron, centered at (w − 16, axis) in a press target
     of G.cardChevronTarget; the strip of its builders from G.cardStripY,
     G.cardStripH high, from x = G.cardInset to w − G.cardStripRight, one
     segment for each of `spec.builders` at equal widths G.cardSegmentGap
     apart, which the card answers in `builders` from left to right; under
     the strip a row of G.frameRow for each row of printed text, reading at
     the left edge and writing at the right edge, and G.framePad of fill
     under the last. A field's name is printed only where no join reaches
     it (the id `unjoined:`), in a row of its own, with no perch's sign,
     the unjoined writing fields of one branch on one row after their
     branch word, which `branch` answers once for the row. The card's
     ports are the cables' (design pass 10 §6): on its writing side one
     port for each continuation branch, the port of the wire that leaves
     the card on that branch where one does, `joined` where the wire
     reaches another card, by which a drag from it moves the cable, and
     not `open` whether the wire reaches a card or a marker, so that its
     plug is drawn filled (the fix wave Q3a, item 1), the ports of the
     wires standing in the order of the ends they reach, by the rank of
     each end's stage key (`reach`; item 2), and else a port of its own,
     named `branch:<label>`, for a branch no wire leaves by, `open`; on its
     reading side one port for the arrival tuple, the ports of the wires
     that reach the card standing at one point, the first of them drawn and
     the rest `hidden`, and, where no wire reaches it, a port of its own
     named `arrival`. A port answers the field ports of its branch or of
     the tuple in `fields`, and a wire's port the branch of its route,
     `branch`. The socket's center and a single plug's center stand on the
     axis, G.cardAxis, and two plugs G.cablePitch apart about it; a card
     with more than two plugs grows G.cablePitch for each further plug,
     the axis at the middle of the stack and the name's row and the strip
     one block centered on it, `axis` answered with `stripY` and `nameTop`.
     The width is w = max(G.frameW, G.cardStep·⌈(name + G.cardChrome)/
     G.cardStep⌉), at most G.frameNameMax, widened to its rows of text with
     G.cardInset at each side and G.fieldGap between them, and to
     `spec.width` where the caller imposes one, the widest of the card's
     column (design pass 13 §2, rule 6; `columnWidths`); the card answers
     the width it takes at rest in `restWidth`. With `spec.unfold` (the
     selected card; L-D19 as L-D25 amends it), the strip is the band of
     G.cardBandH from G.cardStripY, whose segments, from x = G.cardBandLeft
     and ending by w − G.cardBandRight, each as wide as its id with
     G.cardIdPad, plus its signs with G.cardSignsPad where
     `spec.builderRecords` gives it signs, rounded up to G.cardStep, hold
     the pair's signs and the builder's id; every field has a row of its
     own under the band, a branch's word on the first row of its branch
     alone (the fix wave Q3a, item 12); the card widens to its band where
     the band is wider, and its ports stay on the axis. Laid out downward, the reading
     ports stand on the top edge and the writing ports on the bottom edge
     about the card's middle, each side's texts in one row along its edge,
     the name's row and the strip between the two. Each row of printed
     text is answered in `texts`: its side, `writes`, its center `x` or
     `y`, its `branch` word and its `text`, and the card answers whether it
     is unfolded, `unfolded`. */
  function frameGeometry(spec, dir, measure) {
    var count = spec.builders || 0, unfold = !!spec.unfold;
    function port(p) {
      var full = p.attrs.label || '', field = FIELD_PORT.test(p.id), words = fieldWords(full);
      return { id: p.id, full: full, attrs: p.attrs, wire: !!p.wire, field: field, marker: !!p.marker, reach: p.reach,
               open: field ? UNJOINED_FIELD.test(p.id) : !!p.attrs.unjoined,
               branch: field ? words.branch : (p.branch == null ? '' : String(p.branch)), name: field ? words.name : full };
    }
    var given = { ins: spec.inputs.map(port), outs: spec.outputs.map(port) };
    // a row's width in the port face: its branch word with a colon and one space before its fields
    function textWidth(t) { return measure((t.branch ? t.branch + ': ' : '') + t.text, 'port'); }
    /* One side's rows of printed text in their order, each `{ports,
       branch, text}`: a row for each field no join reaches, and, with
       `all`, for every field (the selected card); a wire's port prints no
       row, its label standing in its hover (design pass 7 §3). */
    function side(list, writes, all) {
      var rows = [];
      list.forEach(function (p) {
        if (p.field && (all || p.open)) {
          // the unjoined writing fields of one branch on one row, separated by commas
          var group = writes && !all && p.branch ? p.branch : null;
          var joined = group ? rows.filter(function (r) { return r.group === group; })[0] : null;
          // every field on a row of its own, the branch's word on the first row of its branch alone (B26)
          var headed = all && rows.length && rows[rows.length - 1].head === p.branch;
          if (joined) { joined.ports.push(p); joined.text += ', ' + p.name; }
          else rows.push({ ports: [p], branch: headed ? '' : p.branch, head: p.branch, text: p.name, group: group });
        }
      });
      return { rows: rows, writes: writes };
    }
    /* The cables' ports of one side (design pass 10 §6): the wires' ports,
       each `joined` where its wire joins the card to another card, the
       meaning a drag reads (a wire to a marker joins no other card), and
       none of them `open`, so that a plug a cable leaves, to a card or to
       a marker, is drawn filled (the fix wave Q3a, item 1; A9), the
       writing side's in the order of the ends they reach (`reach`, the
       rank of the end's stage key; item 2); and a port of the card's own
       for each branch no wire leaves by, or for the arrival tuple no wire
       reaches, `open`. */
    function cablePorts(list, writes) {
      var wires = list.filter(function (p) { return p.wire; }), fields = list.filter(function (p) { return p.field; });
      var found = [];
      if (writes) {
        var branches = [], covered = {};
        fields.forEach(function (p) { if (branches.indexOf(p.branch) < 0) branches.push(p.branch); });
        var reach = function (w) { return w.reach == null ? Infinity : w.reach; };
        wires.slice().sort(function (a, b) { return reach(a) - reach(b) || wires.indexOf(a) - wires.indexOf(b); }).forEach(function (w) {
          // the branch's fields leave by the wire, to a card or to a marker; a wire to a marker joins no other card
          covered[w.branch] = true;
          found.push({ id: w.id, attrs: w.attrs, wire: true, joined: !w.marker, open: false, marker: !!w.marker, branch: w.branch, full: w.full,
                       fields: fields.filter(function (p) { return p.branch === w.branch; }) });
        });
        branches.forEach(function (b) {
          if (covered[b]) return;
          found.push({ id: 'branch:' + b, attrs: {}, wire: false, joined: false, open: true, branch: b, full: b || 'continuation',
                       fields: fields.filter(function (p) { return p.branch === b; }) });
        });
      } else {
        wires.forEach(function (w, i) {
          found.push({ id: w.id, attrs: w.attrs, wire: true, joined: !w.marker, open: false, marker: !!w.marker, branch: '', full: w.full, fields: fields, hidden: i > 0 });
        });
        if (!wires.length && fields.length) {
          found.push({ id: 'arrival', attrs: {}, wire: false, joined: false, open: true, branch: '', full: 'arrival', fields: fields });
        }
      }
      return found;
    }
    var left = side(given.ins, false, unfold), right = side(given.outs, true, unfold);
    var rest = unfold ? { left: side(given.ins, false, false), right: side(given.outs, true, false) } : { left: left, right: right };
    var ins = cablePorts(given.ins, false), outs = cablePorts(given.outs, true);
    function widest(s) { return s.rows.reduce(function (a, t) { return Math.max(a, textWidth(t)); }, 0); }
    // the width the name takes with the card's chrome, on the step, at least the least width and at most the
    // widest a name makes a card, past which the name is cut (design pass 13 §2, rule 6)
    var named = measure(spec.label, 'stage');
    var byName = Math.min(G.frameNameMax, Math.max(G.frameW, G.cardStep * Math.ceil((named + G.cardChrome) / G.cardStep)));
    var cut = named > byName - G.cardChrome;
    // the band's segments of the unfolded card, each as wide as its id with G.cardIdPad, plus its signs with
    // G.cardSignsPad where it has signs, rounded up to G.cardStep (design pass 13 §2, rule 7)
    var segments = [];
    if (unfold) {
      for (var k = 0; k < count; k++) {
        var record = (spec.builderRecords || [])[k], signs = record && record.signs ? record.signs : '';
        var id = (spec.builderNames || [])[k] || '';
        segments.push(G.cardStep * Math.ceil((measure(id, 'mark') + G.cardIdPad + (signs ? measure(signs, 'mark') + G.cardSignsPad : 0)) / G.cardStep));
      }
    }
    var bandW = segments.length
      ? G.cardBandLeft + segments.reduce(function (a, b) { return a + b; }, 0) + G.cardSegmentGap * (segments.length - 1) + G.cardBandRight : 0;
    // the width the card's rows of text need, at rest and as drawn
    function byRows(s) { return s.left.rows.length || s.right.rows.length ? widest(s.left) + widest(s.right) + 2 * G.cardInset + G.fieldGap : 0; }
    var restWidth = Math.ceil(Math.max(byName, byRows(rest)));
    var w = Math.max(byName, byRows({ left: left, right: right }), bandW, spec.width || 0);
    var h, nameTop, axis, stripY, texts = [];
    // the places of `n` plugs about `at`, G.cablePitch apart; the reading ports, the arrival tuple's, at one point
    function places(n, at, apart) {
      var out = [];
      for (var i = 0; i < n; i++) out.push(at + (apart ? (i - (n - 1) / 2) * G.cablePitch : 0));
      return out;
    }
    // the block of the name's row and the strip grows G.cablePitch for each plug past two, the axis at the
    // middle of the stack (design pass 13 §2, rule 2)
    var extra = Math.max(0, outs.length - 2) * G.cablePitch;
    // the height of the strip or the band with the room under it before the first row
    var strip = unfold ? G.cardBandH : G.cardStripH + 1;
    if (dir === 'DOWN') {
      // each side's rows in one row along its edge, each as wide as its text, its center the place of its text
      var row = function (s) {
        var slots = s.rows.map(function (t) { return Math.max(textWidth(t), G.portMin); });
        return { slots: slots, width: slots.reduce(function (a, b) { return a + b; }, 0) + Math.max(0, slots.length - 1) * G.portGap,
                 height: s.rows.length ? G.frameRow : 0 };
      };
      var top = row(left), bottom = row(right);
      nameTop = top.height + G.cardNameTop;
      axis = top.height + G.cardAxis;
      stripY = top.height + G.cardStripY;
      w = Math.max(w, top.width + 2 * G.cardInset, bottom.width + 2 * G.cardInset, (outs.length - 1) * G.cablePitch + G.portMark + 2 * G.cardInset);
      h = stripY + strip + bottom.height + G.framePad;
      [[left, top, G.frameRow / 2], [right, bottom, h - G.framePad - G.frameRow / 2]].forEach(function (s) {
        var x = (w - s[1].width) / 2;
        s[0].rows.forEach(function (t, slot) {
          texts.push({ writes: s[0].writes, x: x + s[1].slots[slot] / 2, y: s[2], branch: t.branch, text: t.text });
          x += s[1].slots[slot] + G.portGap;
        });
      });
      places(ins.length, w / 2, false).forEach(function (at, i) { ins[i].x = at; ins[i].y = 0; ins[i].side = 'NORTH'; });
      places(outs.length, w / 2, true).forEach(function (at, i) { outs[i].x = at; outs[i].y = h; outs[i].side = 'SOUTH'; });
    } else {
      var rows = Math.max(left.rows.length, right.rows.length);
      nameTop = G.cardNameTop + extra / 2;
      axis = G.cardAxis + extra / 2;
      stripY = G.cardStripY + extra;
      var rowsTop = stripY + strip;
      h = rowsTop + rows * G.frameRow + G.framePad;
      places(ins.length, axis, false).forEach(function (at, i) { ins[i].x = 0; ins[i].y = at; ins[i].side = 'WEST'; });
      places(outs.length, axis, true).forEach(function (at, i) { outs[i].x = w; outs[i].y = at; outs[i].side = 'EAST'; });
      [left, right].forEach(function (s) {
        s.rows.forEach(function (t, r) {
          texts.push({ writes: s.writes, y: rowsTop + r * G.frameRow + G.frameRow / 2, branch: t.branch, text: t.text });
        });
      });
    }
    // the strip's segments at equal widths G.cardSegmentGap apart from x = G.cardInset to w − G.cardStripRight,
    // or the band's from x = G.cardBandLeft, each of its own width, G.cardSegmentGap apart
    var builders = [], x = G.cardBandLeft;
    for (var i = 0; i < count; i++) {
      if (unfold) {
        builders.push({ x: x, y: stripY, width: segments[i], height: G.cardBandH });
        x += segments[i] + G.cardSegmentGap;
      } else {
        var span = w - G.cardInset - G.cardStripRight + G.cardSegmentGap;
        var x0 = G.cardInset + Math.round(i * span / count), x1 = G.cardInset + Math.round((i + 1) * span / count) - G.cardSegmentGap;
        builders.push({ x: x0, y: stripY, width: x1 - x0, height: G.cardStripH });
      }
    }
    return { width: Math.ceil(w), height: Math.ceil(h), ins: ins, outs: outs, face: 'port', nameTop: nameTop, axis: axis, stripY: stripY,
             builders: builders, texts: texts, card: true, unfolded: unfold, cut: cut, restWidth: restWidth };
  }

  /* The box of a boundary marker (design pass 13 §1, rule 6; design pass 10
     §6), where data enter or leave the drawn range: `spec.marker` is its
     kind, `start` or `end`, the circle of G.marker, or `outside`, the far
     card's port, a square of G.portMark, for a connection to an occurrence
     outside the drawn periods. The box holds the mark and, G.markerGap from it on its far
     side, the label as the exporter writes it, `starting data μ≺` or
     `periods[3]/keeper_cons`, measured in the face of a frame's name, Code
     small: laid out to the right, the mark stands at the end nearer the
     card its wire joins, at the right end where the wire leaves the box
     (an output port) and at the left end where it enters it (an input
     port), the label at the other end, the box as high as the label's
     line; laid out downward, the mark at the bottom where the wire leaves
     and at the top where it enters, the label above or below it, the box as
     wide as the label. The one port stands on the mark's edge that faces
     the card. The mark's place and size are answered in `mark`, and the
     label's place in `labelAt`, so that the pane draws the mark as the
     node's box and the label beside it. */
  function markerGeometry(spec, dir, measure) {
    var size = spec.marker === 'outside' ? G.portMark : G.marker;
    var labelW = Math.ceil(measure(spec.label, 'frame')), line = G.frameLine;
    var leaves = spec.outputs.length > 0;
    function port(p) { return { id: p.id, full: p.attrs.label || '', attrs: p.attrs, wire: !!p.wire }; }
    var ins = spec.inputs.map(port), outs = spec.outputs.map(port);
    var w, h, mark, labelAt;
    if (dir === 'DOWN') {
      w = Math.max(size, labelW);
      h = size + G.markerGap + line;
      mark = { x: (w - size) / 2, y: leaves ? h - size : 0, size: size };
      labelAt = { x: 0, y: leaves ? 0 : size + G.markerGap, width: w, height: line };
      ins.forEach(function (p) { p.x = mark.x + size / 2; p.y = 0; p.side = 'NORTH'; });
      outs.forEach(function (p) { p.x = mark.x + size / 2; p.y = h; p.side = 'SOUTH'; });
    } else {
      w = size + G.markerGap + labelW;
      h = Math.max(size, line);
      mark = { x: leaves ? w - size : 0, y: (h - size) / 2, size: size };
      labelAt = { x: leaves ? 0 : size + G.markerGap, y: (h - line) / 2, width: labelW, height: line };
      ins.forEach(function (p) { p.x = 0; p.y = mark.y + size / 2; p.side = 'WEST'; });
      outs.forEach(function (p) { p.x = w; p.y = mark.y + size / 2; p.side = 'EAST'; });
    }
    return { width: Math.ceil(w), height: Math.ceil(h), ins: ins, outs: outs, face: null, nameTop: 0,
             mark: mark, labelAt: labelAt, kind: spec.marker };
  }

  /* The box of a closed period of a trellis graph's root, the period's
     frame closed (the fix wave Q3a, item 10; B22): as wide as an open
     period's head needs, its name in the face of a frame's name with
     G.layerPad at each side and the toggle of G.toggle, at least G.layerW,
     and G.cardH high, G.cablePitch more for each port past two on its
     fuller side; its name's line stands at (G.cardInset, G.periodPad + 1)
     and its chevron, which the region draws, at (w − 14, G.cardAxis), as
     an open period's head draws them; its reading ports, laid out to the
     right, on its left edge and its writing ports on its right edge, each
     side G.cablePitch apart about the axis, the axis at the middle of the
     taller stack, as a card's plugs stand, so that a cable between two
     closed periods runs straight; laid out downward, its reading ports on
     its top edge and its writing ports on its bottom edge, about its
     middle. The box answers `period`. A closed period that prints a
     writing field's label at its port (J-D47) keeps the box of
     `boxGeometry`, which holds the label. */
  function periodGeometry(spec, dir, measure) {
    function port(p) { return { id: p.id, full: p.attrs.label || '', attrs: p.attrs, wire: !!p.wire }; }
    var ins = spec.inputs.map(port), outs = spec.outputs.map(port);
    var w = Math.ceil(Math.max(G.layerW, measure(spec.label, 'frame') + 2 * G.layerPad + G.toggle + 6));
    var extra = Math.max(0, Math.max(ins.length, outs.length) - 2) * G.cablePitch;
    var h = G.cardH + extra, axis = G.cardAxis + extra / 2;
    function places(list, at) { return list.map(function (p, i) { return at + (i - (list.length - 1) / 2) * G.cablePitch; }); }
    if (dir === 'DOWN') {
      places(ins, w / 2).forEach(function (at, i) { ins[i].x = at; ins[i].y = 0; ins[i].side = 'NORTH'; });
      places(outs, w / 2).forEach(function (at, i) { outs[i].x = at; outs[i].y = h; outs[i].side = 'SOUTH'; });
    } else {
      places(ins, axis).forEach(function (at, i) { ins[i].x = 0; ins[i].y = at; ins[i].side = 'WEST'; });
      places(outs, axis).forEach(function (at, i) { outs[i].x = w; outs[i].y = at; outs[i].side = 'EAST'; });
    }
    return { width: w, height: h, ins: ins, outs: outs, face: null, nameTop: G.periodPad + 1, axis: axis, period: true };
  }


  /* The size of a box and the places of its ports. `dir` is the direction of
     the layer the box stands in: wires enter at the top and leave at the
     bottom when it is DOWN, enter at the left and leave at the right when RIGHT.
     A box prints its label, a field's box its set under it, and an output
     port of the forward trellis graph its field's label (J-D47); every other
     port's label stands in its handle's title, not on the box (R-D49), so
     the label, the printed field labels and the ports' places decide the
     box's size. With `spec.cut`, a box's label wider than G.labelMax takes
     G.labelMax, the box answering `cut` (AAS, L-D20). A stage occurrence
     of a trellis graph, closed or compact, is a card (`spec.occurrence`,
     `frameGeometry`; K-D15, L-D16), and an open occurrence's own `Inputs`
     or `Outputs` prints its fields beside its ports (`spec.fields`,
     `fieldsGeometry`; unit K, Task 21). The graph's own `Inputs` and
     `Outputs` (`spec.boundary`) are G.boundaryW by G.boundaryH at least,
     their name centered in the box where no port's label is printed, on a
     line of G.frameLine in a trellis graph, whose boundary is set in the
     face of a frame's name, `frame`, as design pass 8's mock draws them
     (AAS, M-D15). */
  function boxGeometry(spec, dir, measure) {
    if (spec.occurrence) return frameGeometry(spec, dir, measure);
    // a closed period that prints no writing field's label is its frame closed (the fix wave Q3a, item 10); one that
    // prints one (J-D47) keeps the box that holds the label beside its port
    if (spec.period && !spec.outputs.some(function (p) { return portLabel(p); })) return periodGeometry(spec, dir, measure);
    if (spec.marker) return markerGeometry(spec, dir, measure);
    if (spec.fields) return fieldsGeometry(spec, dir, measure);
    var text = measure(spec.label, spec.role || 'label'), cut = !!spec.cut && !spec.toggle && text > G.labelMax;
    // The two one-pixel borders stand outside the measured text and padding.
    var labelW = (cut ? G.labelMax : text) + (spec.toggle ? G.toggle + 6 : 0) + 2;
    var subW = spec.sub ? measure(spec.sub, 'port') + 2 : 0;
    var outs = spec.outputs.map(function (p) {
      var t = portLabel(p);
      return { id: p.id, text: t, w: t ? measure(t, 'port') : 0, full: p.attrs.label || '', attrs: p.attrs, wire: !!p.wire };
    });
    var ins = spec.inputs.map(function (p) { return { id: p.id, full: p.attrs.label || '', attrs: p.attrs, wire: !!p.wire }; });
    var anyOut = outs.some(function (o) { return o.text; });
    // a boundary's name stands with the same room above and below it, on a line of G.frameLine in the face of a
    // frame's name, in a trellis graph, and of G.labelH in the boundary's own face, in the stage view (M-D15)
    var line = spec.boundary && spec.role === 'frame' ? G.frameLine : G.labelH;
    var padTop = spec.boundary ? (G.boundaryH - G.frameLine) / 2 : G.padTop;
    var padBottom = spec.boundary ? padTop : G.padBottom;
    var head = Math.max(line, spec.toggle ? G.toggle + 1 : 0) + (spec.sub ? 1 + G.subH : 0);
    var minW = spec.boundary ? G.boundaryW : (spec.toggle ? G.layerW : G.minW);
    var minH = spec.boundary ? G.boundaryH : G.minH;
    var w, h;
    if (dir === 'DOWN') {
      var slots = outs.map(function (o) { return Math.max(o.w, G.portMin); });
      var rowW = slots.reduce(function (a, b) { return a + b; }, 0) + Math.max(0, outs.length - 1) * G.portGap;
      w = Math.max(minW, labelW + 2 * G.padX, subW + 2 * G.padX, rowW + 2 * G.padX, ins.length * 14 + 2 * G.padX);
      h = Math.max(minH, padTop + head + (anyOut ? 3 + G.portH : 0) + padBottom);
      var x = (w - rowW) / 2;
      outs.forEach(function (o, i) { o.x = Math.round(x + slots[i] / 2); o.y = h; o.side = 'SOUTH'; x += slots[i] + G.portGap; });
      ins.forEach(function (p, i) { p.x = Math.round(w * (i + 1) / (ins.length + 1)); p.y = 0; p.side = 'NORTH'; });
    } else {
      var colW = outs.reduce(function (a, o) { return Math.max(a, o.w); }, 0);
      w = Math.max(minW, G.padX + Math.max(labelW, subW) + (anyOut ? 14 + colW : 0) + G.padX);
      h = Math.max(minH, padTop + head + padBottom, (anyOut ? outs.length * G.sideRow : 0) + 10, ins.length * 12 + 10, outs.length * 12 + 10);
      var top = (h - outs.length * G.sideRow) / 2;
      outs.forEach(function (o, i) { o.x = w; o.y = Math.round(top + i * G.sideRow + G.sideRow / 2); o.side = 'EAST'; });
      ins.forEach(function (p, i) { p.x = 0; p.y = Math.round(h * (i + 1) / (ins.length + 1)); p.side = 'WEST'; });
    }
    var nameTop = spec.boundary && !anyOut ? (Math.ceil(h) - line) / 2 : padTop;
    return { width: Math.ceil(w), height: Math.ceil(h), ins: ins, outs: outs, face: null, nameTop: nameTop, cut: cut };
  }

  /* The ELK graph of what stands on the pane with the layers of `opened`
     opened, and the records the pane draws from, among them `compact`, the
     occurrences drawn compact (AAS, L-D7). A compact occurrence is laid out
     as a closed occurrence's card, so that `open`, the layers ELK lays out
     open, leaves it out; its box is `{type: 'layer', open: true, compact:
     true}`, and each of its builders is a box `{type: 'builder', parent,
     at, record}` at the place and size `at` in the card's band, which ELK
     does not lay out, `record` being the caller's record of the builder, by
     its layer's namespace, in `options.builders`, or null. The cards whose
     namespaces the list `options.unfold` holds, or every card where it is
     true, print every field's name (AAS, L-D19 as L-D25 amends it). The
     wires from one card to another of one open period are one wire of the
     pair's bundle, `pairBundles`, where they are two or more and the list
     `options.split` names neither card nor the bundle (AAS, L-D25). In the
     stage view, a
     graph with no period's layer, a box's label is cut at G.labelMax; in a
     stage's builders graph, which holds no field's box, laid out downward
     with a builder's layer open, `stage` holds what `arrange` aligns
     (AAS, L-D20): `column`, the ids of the boxes and layers of the graph's
     root that stand in one column, and `frames`, the least width of each
     open layer of the root by its id; ELK places the boxes of every open
     layer of such a graph centered in it (`SIMPLE`), and an open layer of
     its root takes no least width, which `arrange` gives it. */
  function build(m, opened, options, measure) {
    options = options || {};
    var override = options.direction || null, records = options.builders || {};
    function unfolded(ns) {
      return options.unfold === true || (Array.isArray(options.unfold) && options.unfold.indexOf(ns) >= 0);
    }
    var compact = compactOccurrences(m, opened);
    var open = new Set(Array.from(opened).filter(function (ns) { return !compact.has(ns); }));
    var boxes = {}, elkNodes = {};
    // the rank of each output port (K-D12, row K-I9); the rank of each stage key, its place in the recipe's
    // `stages:` list, `options.order` (`stageRanks`), and of each occurrence's namespace or the namespace of the
    // occurrence that holds a node, Infinity for none; and the open periods whose occurrences ELK receives in that
    // rank (the fix wave Q3a, item 2, which amends K-D12)
    var rank = outputRanks(m), ordered = {}, keyRank = stageRanks(m, options.order);
    function rankOf(ns) {
      var key = String(ns || '').split('/')[1];
      return key != null && key in keyRank ? keyRank[key] : Infinity;
    }
    function dirOf(ns) { return directionOf(m.graph, ns, override); }
    // the stage view: a graph with no period's layer (AAS, L-D20)
    var stageView = !Object.keys(m.layers).some(function (ns) { return PERIOD.test(ns); });
    // a graph with no field's box: a stage's builders graph, where an initial diagram holds fields and blocks
    var fieldless = !m.order.some(function (id) { return m.nodes[id].attrs.kind === 'field'; });
    // a stage's builders graph, every layer laid out downward, with a builder's layer open, which `arrange` aligns
    var aligned = stageView && dirOf('') === 'DOWN' &&
      Object.keys(m.layers).every(function (ns) { return dirOf(ns) === 'DOWN'; }) && fieldless &&
      Object.keys(m.layers).some(function (ns) { return !m.layers[ns].parent && open.has(ns); });
    // a stage's builders graph, whose value wires from one box to one box are one bundle where they are two or more
    // (design pass 14 §1, rule 1; S-D2); an initial diagram bundles nothing
    var boxed = stageView && fieldless;
    function childLayers(ns) { return Object.keys(m.layers).filter(function (k) { return m.layers[k].parent === ns; }); }
    /* A layer whose direction differs from that of an open layer inside it
       sets its boxes in line and not by the straightness of the wires, which
       leave an inner layer at its end and enter the next at its start. */
    function mixed(ns) {
      var mine = dirOf(ns);
      return childLayers(ns).some(function (k) { return open.has(k) && dirOf(k) !== mine; });
    }
    // the height of the head of the open layer `ns`: a period's of the graph's root, G.periodHeader (M-D15), and
    // G.layerHeader for every other
    function headerOf(ns) { return PERIOD.test(ns) && !m.layers[ns].parent ? G.periodHeader : G.layerHeader; }
    function layerOptions(ns, isRoot) {
      var o = {
        'elk.algorithm': 'layered',
        'elk.direction': dirOf(ns),
        'elk.hierarchyHandling': 'SEPARATE_CHILDREN',
        'elk.edgeRouting': 'ORTHOGONAL',
        'elk.layered.spacing.nodeNodeBetweenLayers': '24',
        'elk.spacing.nodeNode': '12',
        'elk.spacing.edgeNode': '11',
        'elk.spacing.edgeEdge': '8',
        'elk.layered.spacing.edgeNodeBetweenLayers': '11',
        'elk.layered.spacing.edgeEdgeBetweenLayers': '8',
        // an open layer of a graph `arrange` aligns centers each of ELK's layers in it (AAS, L-D20); a period's
        // layer places each card balanced between the cards its wires join, as design pass 8's mock draws a
        // period (AAS, M-D15)
        'elk.layered.nodePlacement.strategy': mixed(ns) || (aligned && !isRoot) ? 'SIMPLE'
          : PERIOD.test(ns) ? 'BRANDES_KOEPF' : 'NETWORK_SIMPLEX'
      };
      if (o['elk.layered.nodePlacement.strategy'] === 'BRANDES_KOEPF') o['elk.layered.nodePlacement.bk.fixedAlignment'] = 'BALANCED';
      // a period's cards of one column stand G.periodSpread apart and its columns G.periodColumns apart with
      // one slot of vertical runs between them, G.periodSlot more for each further slot, every vertical run
      // G.periodEdge from the cards on both sides (design pass 13 §1, rule 4; §2, rule 9)
      if (PERIOD.test(ns)) {
        o['elk.spacing.nodeNode'] = String(G.periodSpread);
        o['elk.layered.spacing.nodeNodeBetweenLayers'] = String(G.periodColumns);
        o['elk.layered.spacing.edgeNodeBetweenLayers'] = String(G.periodEdge);
        o['elk.layered.spacing.edgeEdgeBetweenLayers'] = String(G.periodSlot);
      }
      // the periods of a trellis graph stand G.periodGap apart, a cable's vertical run between two of them
      // G.rootEdge from either (design pass 13 §2, rule 9)
      if (isRoot && !stageView) {
        o['elk.layered.spacing.nodeNodeBetweenLayers'] = String(G.periodGap);
        o['elk.layered.spacing.edgeNodeBetweenLayers'] = String(G.rootEdge);
      }
      // a period keeps its occurrences in every column in the order ELK receives them, the rank of their stage
      // keys (the fix wave Q3a, item 2, which amends K-D12)
      if (ordered[ns]) {
        o['elk.layered.considerModelOrder.strategy'] = 'NODES_AND_EDGES';
        o['elk.layered.crossingMinimization.forceNodeModelOrder'] = 'true';
      }
      if (isRoot) {
        o['org.eclipse.elk.json.edgeCoords'] = 'ROOT';
        o['elk.padding'] = '[top=2,left=2,bottom=2,right=2]';
      } else if (PERIOD.test(ns) && !m.layers[ns].parent) {
        // a period's frame: its head and G.periodTop above the first card, G.periodLeft at the reading side,
        // G.periodRight at the writing side, where a bus mark and its count stand inside the frame, and
        // G.periodBottom under the last card (design pass 13 §2, rule 8)
        o['elk.portConstraints'] = 'FIXED_SIDE';
        o['elk.padding'] = '[top=' + (headerOf(ns) + G.periodTop) + ',left=' + G.periodLeft + ',bottom=' + G.periodBottom + ',right=' + G.periodRight + ']';
      } else {
        o['elk.portConstraints'] = 'FIXED_SIDE';
        o['elk.padding'] = '[top=' + (headerOf(ns) + G.layerPad) + ',left=' + G.layerPad + ',bottom=' + G.layerPad + ',right=' + G.layerPad + ']';
      }
      return o;
    }
    var elkRoot = { id: 'root', children: [], edges: [], layoutOptions: layerOptions('', true) };
    function container(ns) { return ns ? elkNodes[ns + LAYER_ENDING] : elkRoot; }

    // the ELK port of each reading handle: a reading port of a card that stands at one point with the first,
    // `hidden`, shares the first's ELK port, so that the cables into one socket are routed to one port and
    // meet on one vertical run (design pass 13 §1, rule 4; A8); the hidden port is still a port of ELK's
    // graph, at the same point, so that every port of the card's geometry is returned (spec 0.4 §4)
    var elkPortOf = {};
    // ELK's record of a port at the place (x, y) on the side `side` of its box: a point of no size, so that the
    // port adds nothing to the box's margin and the spacing ELK keeps from the box holds from its edge, where a
    // port of 1 px stood outside the edge and widened every gap by a pixel (design pass 13 §1, rule 4)
    function elkPort(id, x, y, side) {
      return { id: id, width: 0, height: 0, x: x, y: y, layoutOptions: { 'elk.port.side': side } };
    }
    function addPorts(elk, geom, id) {
      elk.ports = [];
      var shared = null;
      geom.ins.forEach(function (p) {
        p.handle = id + '::in::' + p.id;
        elkPortOf[p.handle] = p.hidden && shared ? shared : p.handle;
        if (shared === null) shared = p.handle;
        elk.ports.push(elkPort(p.handle, p.x, p.y, p.side));
      });
      geom.outs.forEach(function (p) {
        p.handle = id + '::out::' + p.id;
        elk.ports.push(elkPort(p.handle, p.x, p.y, p.side));
      });
      elk.layoutOptions = { 'elk.portConstraints': 'FIXED_POS' };
    }

    // the layers on the pane, outermost first: open ones as containers, closed ones noted
    var namespaces = Object.keys(m.layers).sort(function (a, b) { return a.split('/').length - b.split('/').length; });
    // an open period's occurrences take the places they held, in the rank of their stage keys, the recipe's order
    // (the fix wave Q3a, item 2; A17, B15)
    namespaces.filter(function (ns) { return PERIOD.test(ns) && open.has(ns); }).forEach(function (period) {
      var slots = [], kids = [];
      namespaces.forEach(function (ns, i) { if (m.layers[ns].parent === period) { slots.push(i); kids.push(ns); } });
      var ranked = kids.slice().sort(function (a, b) { return rankOf(a) - rankOf(b) || kids.indexOf(a) - kids.indexOf(b); });
      ordered[period] = true;
      ranked.forEach(function (ns, i) { namespaces[slots[i]] = ns; });
    });
    var closed = {};
    namespaces.forEach(function (ns) {
      var L = m.layers[ns];
      if (chain(L.parent).some(function (a) { return !open.has(a); })) return;   // inside a closed layer
      if (!open.has(ns)) { closed[ns] = { ins: [], outs: [], seenIn: {}, seenOut: {} }; return; }
      var elk = { id: L.id, children: [], edges: [], ports: [], layoutOptions: layerOptions(ns, false) };
      // the name in its face, a stage's name for a stage occurrence of a trellis graph and a frame's name, the
      // period style, for every other layer of either graph (design pass 10 §5; design pass 13 §3, Q-D22), the
      // toggle and the paddings
      var face = !stageView && OCCURRENCE.test(ns) ? 'stage' : 'frame';
      var least = measure(L.name, face) + 2 * G.layerPad + G.toggle + 6;
      // a period's layer of a graph with `add` controls holds `Stage` after the Codicon `add` between its name
      // and its toggle (K-D14; design pass 13 §2, rule 8)
      if (options.adds && PERIOD.test(ns)) least += G.addIcon + G.addGap + measure(STAGE_WORDS, 'small') + 2 * G.addPad + G.stageGap;
      least = Math.ceil(Math.max(G.layerW, least));
      // an open layer of the root of a graph `arrange` aligns is as wide as its content, which `arrange` widens
      var minimum = aligned && !L.parent ? 0 : least;
      elk.layoutOptions['elk.nodeSize.constraints'] = 'MINIMUM_SIZE';
      elk.layoutOptions['elk.nodeSize.minimum'] = '(' + minimum + ',' + (headerOf(ns) + 2 * G.layerPad) + ')';
      elkNodes[L.id] = elk;
      container(L.parent).children.push(elk);
      boxes[L.id] = { id: L.id, type: 'layer', open: true, namespace: ns, name: L.name, layer: L, parent: L.parent ? L.parent + LAYER_ENDING : null,
                      least: least };
    });

    /* The bundles of AAS's decision L-D25 (design pass 7 §3): the wires
       from one stage occurrence drawn as a card, closed or compact, to
       another of the same open period, where they come from two or more
       outputs. Each bundle is `{id, from, to, keys, split, whole}`: its id,
       PAIR_BUNDLE followed by its ends' names; the namespaces of the
       writing and the reading occurrence; the outputs `<node>|<output>` its
       wires come from; whether `options.split` names either occurrence or
       the bundle, which leaves its wires apart; and whether it is a cable
       of a route's values, which nothing splits. A bundle not split is
       drawn as one wire between one port of each card, named by its id,
       which carries `members`, each of its wires as {from, out, to, into,
       label, join, value}, the label of its writing port, the join text of
       its reading port and the name of the function it carries
       (`valueName`); `joins`, those texts' entries, each once, joined by
       `; `; and `label`: in a backward trellis graph the names of the
       functions its wires carry, each once, in the order of its wires,
       joined by `, `, `𝑉, 𝑑𝑉_h, 𝑑𝑉_a` (AAS, L-D26), and otherwise the label
       its joins' entries print (K-D4).
       The wires that carry a value role, as every wire between two stage
       occurrences of a backward trellis graph does, are bundled by the
       route they belong to, within a period and from one period to the
       next alike (design pass 12 §2): the wires of one route from a card
       to another card, or between a card and a boundary marker of the
       graph's root, are one cable, `whole`, which `options.split` never
       splits, from one plug of the writer's card to one socket of the
       reader's, so that a writer whose routes reach two readers carries
       two plugs, G.cablePitch apart, as a forward graph's writer of two
       branches does. Its id is PAIR_BUNDLE followed by the namespace of
       each card or the id of the marker, the writer's first, and by the
       branch of its route where the route has one,
       `stages::periods[0]/keeper_cons|periods[0]/tenure|keep`; it counts
       the value functions it carries, the outputs its wires come from,
       which a backward graph drew one by one before (design pass 12 §§2
       and 3), where a forward cable counts its route's pairs. A closed
       period's box stands for the occurrence inside it that holds the
       wire's node, as a forward graph draws one wire for each route into a
       closed period.
       In a stage's builders graph (`boxed`) no wire belongs to a bundle: a
       value is one wire, and its derivatives are listed in its ports'
       hovers (AMD-MB-001 §5.4). */
    var split = options.split || [];
    var pairBundles = [], pairOf = {};
    // the port of the graph JSON that the wire `w` reaches
    function readingPort(w) {
      return m.nodes[w.to].inputs.filter(function (p) { return p.id === w.into; })[0] || { id: w.into, attrs: {} };
    }
    // whether the wire `w` carries a value role, as a backward trellis graph's wires do
    function carriesValue(w) { return VALUE_ROLES.indexOf((readingPort(w).attrs || {}).role) >= 0; }
    // the name of the end of a wire that stands on the pane as `at` (`shown`), the node `id` of the graph JSON,
    // that a bundle joins: a card's namespace, a stage occurrence closed or compact; for a wire that carries a
    // value role, also a closed period's box, named by the occurrence inside it that holds the node, as a
    // forward graph draws one wire for each route into a closed period, and a boundary marker's id (design pass
    // 12 §2); null for any other end
    function bundleEnd(at, id, value) {
      if (at.layer && OCCURRENCE.test(at.layer)) return at.layer;
      if (!value) return null;
      if (at.layer) return PERIOD.test(at.layer) ? chain(m.nodes[id].namespace)[1] || null : null;
      return m.nodes[id].marker ? id : null;
    }
    // the key of the bundle of the wire `w`, whose ends stand on the pane as `a` and `b`, or null for a wire no
    // bundle holds: within a period, the names of its two cards, and, for a wire that carries a value role,
    // within a period or between two, the names of its two ends and the branch of its route (design pass 12 §2)
    function bundleKey(w, a, b) {
      // in a stage's builders graph a value is one wire and no wire belongs to a bundle (AMD-MB-001 §5.4)
      if (boxed) return null;
      var value = carriesValue(w), from = bundleEnd(a, w.from, value), to = bundleEnd(b, w.to, value);
      if (!from || !to || from === to) return null;
      if (!value) return a.layer && b.layer && m.layers[a.layer].parent === m.layers[b.layer].parent ? from + '|' + to : null;
      var route = w.attrs.route || null;
      return from + '|' + to + (route && route.branch != null ? '|' + route.branch : '');
    }
    m.wires.forEach(function (w) {
      var a = shown(m, w.from, open), b = shown(m, w.to, open);
      var ends = bundleKey(w, a, b), key = w.from + '|' + w.out;
      if (ends === null) return;
      if (!pairOf[ends]) {
        var id = PAIR_BUNDLE + ends, whole = carriesValue(w);
        pairOf[ends] = { id: id, from: bundleEnd(a, w.from, whole),
                         to: bundleEnd(b, w.to, whole), keys: [], whole: whole,
                         out: w.out, into: w.into,
                         split: !whole && [a.layer, b.layer, id].some(function (name) { return split.indexOf(name) >= 0; }) };
        pairBundles.push(pairOf[ends]);
      }
      if (pairOf[ends].keys.indexOf(key) < 0) pairOf[ends].keys.push(key);
    });
    pairBundles = pairBundles.filter(function (u) { return u.keys.length > 1; });
    pairBundles.forEach(function (u) { u.bundled = true; u.members = []; u.attrs = {}; });

    // the wires on the pane, each from the port of what stands for its writer to the port of what stands for its reader
    // `outward` names each closed layer that writes a wire read in another period
    // `writtenBy` names the node that writes each wire, by `<node>|<output>`, and the first that writes a bundle's
    var seen = {}, wires = [], outward = {}, writtenBy = {};
    // the ports of a stage's builders graph (design pass 14 §1, rules 4 and 5; S-D4): `kept`, each port of a node
    // at which a wire of it is drawn, by the port's handle; `moved`, each port of a node whose wire is drawn at
    // another port, its bundle's; and `hovers`, the labels of the wires drawn at each port of the pane, a node's
    // or a closed layer's, by the port's handle
    var kept = {}, moved = {}, hovers = {};
    function drawnAt(own, at) { if (own === at) kept[own] = true; else moved[own] = true; }
    // whether the port of a node whose handle is `handle` is neither drawn nor laid out: a wire of it is drawn at
    // another port, its bundle's, and none at itself (design pass 14 §1, rule 4)
    function dropped(handle) { return !!moved[handle] && !kept[handle]; }
    /* The rank of the end the wire into the node `id` reaches: the rank of
       the occurrence that holds the node, or of the occurrence an
       `outside` marker names, Infinity for a terminal marker (the fix wave
       Q3a, item 2). */
    function reachOf(id) {
      var n = m.nodes[id];
      if (n.marker) return n.attrs.target ? rankOf(n.attrs.target) : Infinity;
      return rankOf(chain(n.namespace)[1]);
    }
    m.wires.forEach(function (w) {
      var a = shown(m, w.from, open), b = shown(m, w.to, open);
      var aId = a.node || (a.layer + LAYER_ENDING), bId = b.node || (b.layer + LAYER_ENDING);
      if (aId === bId) return;
      var outPort = m.nodes[w.from].outputs.filter(function (p) { return p.id === w.out; })[0] || { id: w.out, attrs: {} };
      var inPort = m.nodes[w.to].inputs.filter(function (p) { return p.id === w.into; })[0] || { id: w.into, attrs: {} };
      var wireKey = w.from + '|' + w.out;
      writtenBy[wireKey] = w.from;
      if (a.layer && periodOf(m, w.from) !== periodOf(m, w.to)) outward[a.layer] = true;
      // the bundle the wire belongs to, or null; a wire of a bundle not split crosses the two cards' borders at the
      // bundle's ports, and a boundary marker at the port of the bundle's first wire (design pass 12 §2)
      var ends = bundleKey(w, a, b), pair = ends === null ? null : pairOf[ends] || null;
      if (pair && !pair.bundled) pair = null;
      var drawn = pair && !pair.split ? pair : null;
      var crossing = drawn ? drawn.id : wireKey, leaving = drawn ? drawn.id : wireKey;
      // the route the wire's edge carries, where one does (unit N, Task 6): its branch and its pairs
      var route = w.attrs.route || null, branch = route && route.branch != null ? String(route.branch) : null;
      if (drawn) {
        if (!writtenBy[drawn.id]) writtenBy[drawn.id] = w.from;
        if (drawn.branch === undefined) drawn.branch = branch;
        drawn.members.push({ from: w.from, out: w.out, to: w.to, into: w.into, label: outPort.attrs.label || '',
                             join: inPort.attrs.join || '', value: valueName(inPort),
                             valued: VALUE_ROLES.indexOf((inPort.attrs || {}).role) >= 0 });
      }
      // a port that a wire crosses the border at, named by the wire's writer and output, or by its bundle; a
      // writing port carries the branch of the wire's route (design pass 10 §6); each carries the rank of the end
      // the wire reaches, by which a card's plugs and a closed period's ports stand in order (`reachOf`; the fix
      // wave Q3a, items 2 and 10), and whether a boundary marker is the wire's other end
      var markerA = m.nodes[w.from].marker, markerB = m.nodes[w.to].marker;
      if (a.layer && !closed[a.layer].seenOut[leaving]) {
        closed[a.layer].seenOut[leaving] = true;
        closed[a.layer].outs.push({ id: leaving, attrs: drawn ? drawn.attrs : outPort.attrs, wire: true, branch: branch, marker: !!markerB,
                                    reach: reachOf(w.to) });
      }
      if (b.layer && !closed[b.layer].seenIn[crossing]) {
        closed[b.layer].seenIn[crossing] = true;
        closed[b.layer].ins.push({ id: crossing, attrs: drawn ? drawn.attrs : inPort.attrs, wire: true, marker: !!markerA,
                                   reach: reachOf(w.to) });
      }
      var sp = aId + '::out::' + (a.layer ? leaving : drawn ? drawn.out : w.out);
      var tp = bId + '::in::' + (b.layer ? crossing : drawn ? drawn.into : w.into);
      var key = sp + '>>' + tp;
      if (boxed) {
        // the wire's label, its writing port's, which the hover of the port it is drawn at lists (design pass 14 §1,
        // rule 5); the port of a node it leaves or reaches and the port it is drawn at, its bundle's or its own
        var label = outPort.attrs.label || inPort.attrs.label || '';
        if (a.node) drawnAt(w.from + '::out::' + w.out, sp);
        if (b.node) drawnAt(w.to + '::in::' + w.into, tp);
        (hovers[sp] = hovers[sp] || []).push(label);
        (hovers[tp] = hovers[tp] || []).push(label);
        // the derivatives the value carries by statement, under its label (AMD-MB-001 §5.4)
        derivativeLabels(outPort.attrs.derivatives ? outPort : inPort).forEach(function (line) {
          hovers[sp].push(line);
          hovers[tp].push(line);
        });
      }
      if (seen[key]) return;
      seen[key] = true;
      // a cable (design pass 10 §6): a wire between two stage occurrences' cards, or between a card and a boundary
      // marker, whose stub to an `outside` marker is dashed; the count of the wires it carries, the pairs of its
      // route where it carries a measure, and one where it carries one value function (design pass 12 §3); and its
      // branch
      var cable = (!!a.layer && OCCURRENCE.test(a.layer) || !!markerA) && (!!b.layer && OCCURRENCE.test(b.layer) || !!markerB);
      // in a trellis's initial diagram a wire counts the wires drawn as one line, one for a single field wire and
      // its bundle's members for a bundle, where a measure wire of the builders graph counts its route's pairs
      // (design pass 14 §7, rule 5)
      var count = route && !carriesValue(w) && !initialDiagram(m) ? (route.pairs || []).length : 1;
      // `from`, `out`, `to` and `into` name the wire by its nodes and ports in the graph JSON, those of the first
      // wire of a bundle; `join` is the label it prints: a cable's label, its branch or the count of its wires
      // (`cableLabel`; design pass 10 §6), else the label of the joins its reading port names (`wireLabel`), a
      // bundle's label set once its wires are known; `pairBundle` is the bundle it draws and `pairOf` the id of
      // the split bundle it belongs to
      // `closed` marks a wire that leaves or reaches a closed period's box, which draws no arrowhead (the fix wave
      // Q3a, item 10)
      wires.push({ id: key, source: aId, sourceHandle: sp, target: bId, targetHandle: tp, label: drawn ? '' : outPort.attrs.label || '',
                   join: drawn ? '' : cable ? cableLabel(branch, count) : wireLabel(inPort),
                   reading: drawn ? drawn.attrs : inPort.attrs, writing: drawn ? drawn.attrs : outPort.attrs,
                   from: w.from, out: w.out, to: w.to, into: w.into, cable: cable, count: count, branch: branch,
                   closed: !!a.layer && PERIOD.test(a.layer) || !!b.layer && PERIOD.test(b.layer),
                   // the layer the writer's box stands in, the graph's root as '', which a stage graph's bundle spaces
                   // (design pass 14 §1, rule 3)
                   within: a.layer ? m.layers[a.layer].parent : m.nodes[w.from].namespace,
                   dashed: markerA === 'outside' || markerB === 'outside',
                   pairBundle: drawn || undefined, pairOf: pair && pair.split ? pair.id : undefined });
    });
    // a bundle's joins and its label, which its wire prints and its ports' hovers name: where a wire of it
    // carries a value role, the names of the functions its wires carry, the empty text where none is named,
    // so that no state field labels it (L-D26; unit L's final judgment, §6 item 9); else the label of its
    // joins (K-D4)
    // a bundle between two cards is a cable whose label is its branch or the count of its wires (design pass 10
    // §6); its hover keeps the names of the functions its wires carry, or the label of its joins
    pairBundles.forEach(function (u) {
      if (u.split) return;
      var entries = [], names = [], valued = false;
      u.members.forEach(function (member) {
        (member.join ? member.join.split('; ') : []).forEach(function (entry) { if (entries.indexOf(entry) < 0) entries.push(entry); });
        if (member.value && names.indexOf(member.value) < 0) names.push(member.value);
        valued = valued || member.valued;
      });
      u.joins = entries.join('; ');
      u.names = valued ? names.join(', ') : joinLabel(u.joins);
      // a cable of a route's values counts the value functions it carries, the outputs its wires come from (design
      // pass 12 §§2 and 3); any other bundle its wires
      u.count = u.whole ? u.keys.length : u.members.length;
      u.label = cableLabel(u.branch || null, u.count);
      u.attrs.label = u.names;
      u.attrs.join = u.joins;
    });
    wires.forEach(function (w) {
      if (!w.pairBundle) return;
      w.join = w.pairBundle.label;
      w.count = w.pairBundle.count;
      w.branch = w.pairBundle.branch || null;
    });
    /* The first run from a plug is G.firstRun, or the count's right edge
       with G.countRoom beyond it where the count is wider (design pass 13
       §1, rule 5; check 21): the slash's center G.slashAlong from the
       plug's outer face, the count G.countGap right of the slash's end. A
       period one of whose cables carries such a count spaces its columns
       by that run and pads its writing side by it, so that every first run
       of the period clears the count. */
    function firstRunOf(count) {
      var right = G.portMark / 2 + G.slashAlong + G.slash / 2 * Math.SQRT1_2 + G.countGap + measure(String(count), 'mark');
      return Math.max(G.firstRun, Math.ceil(right + G.countRoom));
    }
    var runs = {};
    wires.forEach(function (w) {
      var writer = boxes[w.source];
      if (!w.cable || !(w.count > 1) || !writer || writer.type !== 'layer') return;
      var period = chain(writer.namespace)[0];
      if (!period || !PERIOD.test(period) || !open.has(period)) return;
      runs[period] = Math.max(runs[period] || G.firstRun, firstRunOf(w.count));
    });
    Object.keys(runs).forEach(function (period) {
      var frame = elkNodes[period + LAYER_ENDING];
      if (!frame || runs[period] <= G.firstRun) return;
      frame.layoutOptions['elk.layered.spacing.edgeNodeBetweenLayers'] = String(runs[period]);
      frame.layoutOptions['elk.layered.spacing.nodeNodeBetweenLayers'] = String(2 * runs[period]);
      frame.layoutOptions['elk.padding'] = '[top=' + (G.periodHeader + G.periodTop) + ',left=' + G.periodLeft + ',bottom=' + G.periodBottom + ',right=' + runs[period] + ']';
    });
    /* In a stage's builders graph the open layer a bundle's writer stands
       in, or the graph's root, spaces ELK's layers by the bundle's first
       run, `elk.layered.spacing.edgeNodeBetweenLayers` the run and
       `elk.layered.spacing.nodeNodeBetweenLayers` twice the run, as a
       period's frame does, so that every first run of the layer clears
       its count (design pass 14 §1, rule 3). */
    var boxRuns = {};
    if (boxed) wires.forEach(function (w) {
      if (!(w.count > 1)) return;
      boxRuns[w.within] = Math.max(boxRuns[w.within] || G.firstRun, firstRunOf(w.count));
    });
    Object.keys(boxRuns).forEach(function (ns) {
      var frame = ns ? elkNodes[ns + LAYER_ENDING] : elkRoot;
      if (!frame) return;
      frame.layoutOptions['elk.layered.spacing.edgeNodeBetweenLayers'] = String(boxRuns[ns]);
      frame.layoutOptions['elk.layered.spacing.nodeNodeBetweenLayers'] = String(2 * boxRuns[ns]);
    });
    /* A closed layer's ports for the wires it writes, each named
       `<node>|<output>`, stand in the order of its nodes' outputs where
       every such wire is read in the layer's own period; a layer that
       writes into another period keeps the order in which its wires are
       read (K-D12, row K-I9). */
    var outputOrder = byRank(rank);
    Object.keys(closed).forEach(function (ns) {
      if (!outward[ns]) closed[ns].outs.sort(function (p, q) { return outputOrder(p.id, q.id); });
    });
    // a closed period's box has its reading and its writing ports in the rank of the occurrences their wires
    // reach, inside it and beyond it, so that the cables into it and out of it keep the order of the rows (the fix
    // wave Q3a, items 2 and 10)
    function byReach(list) {
      var given = list.slice();
      function at(p) { return p.reach == null ? Infinity : p.reach; }
      list.sort(function (p, q) { return at(p) - at(q) || given.indexOf(p) - given.indexOf(q); });
    }
    Object.keys(closed).forEach(function (ns) {
      if (PERIOD.test(ns) && !m.layers[ns].parent) { byReach(closed[ns].ins); byReach(closed[ns].outs); }
    });
    /* The place of each layer among its parent's children as ELK receives
       them: the open layers in the order of `namespaces`, then the closed
       layers in the same order; an ordered period's occurrences, open or
       closed, in the order of `namespaces`, their rank (the fix wave Q3a,
       item 2). */
    var place = {};
    namespaces.forEach(function (ns, i) { place[ns] = (open.has(ns) || ordered[m.layers[ns].parent] ? 0 : namespaces.length) + i; });
    /* The occurrence that writes the wire `<node>|<output>` `key` where it
       stands in an open period, whose occurrences ELK receives in the rank
       of their stage keys (the fix wave Q3a, item 2), else null. */
    function orderedWriter(key) {
      var above = chain(m.nodes[writtenBy[key]].namespace);
      return ordered[above[0]] && above[1] ? above[1] : null;
    }
    /* The layers a wire from a node in the layer `from` to a node in the
       layer `to` runs through, in its course: `from` and the layers above
       it up to the innermost layer that holds both, or the graph's root
       `''` where no layer does, then the layers below that one down to
       `to`. */
    function course(from, to) {
      var a = chain(from), b = chain(to), d = 0;
      while (d < a.length && d < b.length && a[d] === b[d]) d++;
      return a.slice(d).reverse().concat([d ? a[d - 1] : ''], b.slice(d));
    }
    /* Whether the layers `layers` are, in order, one or more laid out to
       the right and then one or more laid out downward. */
    function turnsDownOnce(layers) {
      var dirs = layers.map(dirOf), turn = dirs.indexOf('DOWN');
      return turn > 0 && dirs.slice(turn).every(function (d) { return d === 'DOWN'; });
    }
    /* A closed layer inside a layer laid out downward has its reading ports
       on its top edge, from left to right. Occurrences of a period laid out
       to the right that ELK places in one column stand one above another,
       in the order ELK receives them. A wire from one of them that runs
       through layers laid out to the right and then through layers laid
       out downward turns down once; two such wires do not cross where the
       one from the lower writer turns down, and reaches its port, farther
       left. So where every wire such a layer reads is written by another
       occurrence of one open period, whose occurrences ELK receives in the
       rank of their stage keys, and runs that course, its reading ports
       stand in the reverse of that rank; the wires of one writer keep the order in
       which they are read. A closed layer, or a compact occurrence's frame,
       whose wires run through layers laid out to the right alone has its
       reading ports on its left edge, from top to bottom, and two such
       wires do not cross where the one from the upper writer reaches its
       port higher; its reading ports then stand in that order (AAS, L-D7,
       whose compact frames stand where the closed builders of an open
       occurrence stood). In every other case, as where the direction
       button lays every layer out downward and the writers stand side by
       side, the reading ports keep the order in which their wires are read
       (K-D12, row K-I14). */
    Object.keys(closed).forEach(function (ns) {
      var own = chain(ns)[1], period = null, writer = {};
      var fits = closed[ns].ins.every(function (p) {
        var occurrence = orderedWriter(p.id);
        if (!occurrence || occurrence === own) return false;
        if (period !== null && m.layers[occurrence].parent !== period) return false;
        period = m.layers[occurrence].parent;
        writer[p.id] = occurrence;
        return true;
      });
      if (!fits || period === null) return;
      var route = course(period, m.layers[ns].parent);
      if (turnsDownOnce(route)) {
        closed[ns].ins.sort(function (p, q) { return place[writer[q.id]] - place[writer[p.id]]; });
      } else if (route.every(function (layer) { return dirOf(layer) === 'RIGHT'; })) {
        closed[ns].ins.sort(function (p, q) { return place[writer[p.id]] - place[writer[q.id]]; });
      }
    });

    // An unjoined port of a node inside a closed layer, which no wire
    // carries across the border, stands on the closed layer's box as itself,
    // under its own id and with its own attributes (§3.4). A closed stage
    // occurrence's frame also carries, in the same way, every field port of
    // its own `Inputs` and `Outputs`, joined or not, so that it prints every
    // arrival and continuation field (K-D15).
    m.order.forEach(function (id) {
      var at = shown(m, id, open), n = m.nodes[id];
      if (!at.layer) return;
      var own = OCCURRENCE.test(at.layer) && n.namespace === at.layer;
      function stands(p) { return p.attrs.unjoined || (own && FIELD_PORT.test(p.id)); }
      n.inputs.forEach(function (p) { if (stands(p)) closed[at.layer].ins.push({ id: p.id, attrs: p.attrs }); });
      n.outputs.forEach(function (p) { if (stands(p)) closed[at.layer].outs.push({ id: p.id, attrs: p.attrs }); });
    });

    /* The builders of the compact occurrence `ns` in the order its frame
       draws them (L-D7): by the place of the pair each joins in the order
       of its direction, the policy builder after those, then every builder
       the caller's records do not place, each group in the graph JSON's
       order. None in a trellis's initial diagram, whose occurrences hold
       perches and no builder, so that a card there carries no strip
       (design pass 14 §7, rule 5; S-D13). */
    function builderLayers(ns) {
      if (initialDiagram(m)) return [];
      function rank(k) {
        var record = records[k];
        if (record && record.place != null) return record.place;
        return record && record.pair === POLICY ? 2 : 3;
      }
      return childLayers(ns).map(function (k, i) { return { ns: k, rank: rank(k), i: i }; })
        .sort(function (a, b) { return a.rank - b.rank || a.i - b.i; })
        .map(function (k) { return k.ns; });
    }

    // the closed layers as boxes, a stage occurrence's as a card (K-D15, L-D16), closed or compact, with the
    // segments of its builders in its strip (L-D7; design pass 13 §2, one drawing for both), at the width its
    // column imposes where the caller gives one (`options.widths`, by the occurrence's namespace)
    namespaces.forEach(function (ns) {
      if (!closed[ns]) return;
      var L = m.layers[ns], dir = dirOf(L.parent), held = OCCURRENCE.test(ns) ? builderLayers(ns) : [];
      var spec = { label: L.name, role: 'layer', toggle: true, inputs: closed[ns].ins, outputs: closed[ns].outs,
                   occurrence: OCCURRENCE.test(ns), period: PERIOD.test(ns) && !L.parent, builders: held.length, unfold: unfolded(ns),
                   builderNames: held.map(function (k) { return m.layers[k].name; }),
                   builderRecords: held.map(function (k) { return records[k] || null; }),
                   width: (options.widths || {})[ns] || 0 };
      var geom = boxGeometry(spec, dir, measure);
      var elk = { id: L.id, width: geom.width, height: geom.height };
      addPorts(elk, geom, L.id);
      elkNodes[L.id] = elk;
      container(L.parent).children.push(elk);
      boxes[L.id] = { id: L.id, type: 'layer', open: compact.has(ns), compact: compact.has(ns), namespace: ns, name: L.name, layer: L,
                      spec: spec, geom: geom, dir: dir, parent: L.parent ? L.parent + LAYER_ENDING : null };
      held.forEach(function (k, i) {
        var B = m.layers[k];
        boxes[B.id] = { id: B.id, type: 'builder', namespace: k, name: B.name, layer: B, parent: L.id,
                        at: geom.builders[i], record: records[k] || null };
      });
    });

    /* Whether the node `n` is the own `Inputs` or `Outputs` of a stage
       occurrence that carries the occurrence's field ports (§3.4): it
       stands directly in the occurrence's layer and one of its ports is a
       field's. */
    function carriesFields(n) {
      return OCCURRENCE.test(n.namespace) && n.inputs.concat(n.outputs).some(function (p) { return FIELD_PORT.test(p.id); });
    }

    // the nodes; an open occurrence's own `Inputs` or `Outputs` that carries its field ports is laid out in the
    // direction of the period the occurrence stands in, as the occurrence's frame is (unit K, Task 21)
    m.order.forEach(function (id) {
      var n = m.nodes[id];
      if (!shown(m, id, open).node) return;
      var dir = dirOf(n.namespace), kind = n.attrs.kind || '';
      // in the stage view a label wider than G.labelMax is cut (AAS, L-D20); in a stage's builders graph a port
      // whose wires are drawn at their bundle's port is neither drawn nor laid out (design pass 14 §1, rule 4; S-D4)
      var spec = { label: n.label, cut: stageView,
                   inputs: boxed ? n.inputs.filter(function (p) { return !dropped(id + '::in::' + p.id); }) : n.inputs,
                   outputs: boxed ? n.outputs.filter(function (p) { return !dropped(id + '::out::' + p.id); }) : n.outputs };
      var type = 'operator';
      if (kind === 'field') { type = 'field'; spec.sub = n.attrs.set || ''; }
      else if (kind === 'block') { type = 'block'; spec.role = 'layer'; }
      // a boundary marker of a trellis graph's root, where data enter or leave the drawn range (design pass 10 §6)
      else if (n.marker) { type = 'marker'; spec.marker = n.marker; spec.role = 'frame'; spec.target = n.attrs.target || ''; }
      // an occurrence's own Inputs and Outputs, in the face of a frame's name in a trellis graph (M-D15)
      else if (!kind) { type = 'boundary'; spec.role = stageView ? 'boundary' : 'frame'; spec.boundary = true; }
      if (!kind && carriesFields(n)) { spec.fields = true; dir = dirOf(m.layers[n.namespace].parent); }
      var geom = boxGeometry(spec, dir, measure);
      var elk = { id: id, width: geom.width, height: geom.height };
      addPorts(elk, geom, id);
      elkNodes[id] = elk;
      container(n.namespace).children.push(elk);
      boxes[id] = { id: id, type: type, node: n, spec: spec, geom: geom, dir: dir, parent: n.namespace ? n.namespace + LAYER_ENDING : null,
                    rank: n.marker ? reachOf(id) : undefined };
    });
    // the hover of a port of a stage's builders graph, a node's or a closed layer's: the labels of the wires drawn
    // at it, each once, one per line, a bundle's members among them (design pass 14 §1, rule 5)
    if (boxed) Object.keys(boxes).forEach(function (id) {
      var b = boxes[id];
      if (!b.geom) return;
      b.geom.ins.concat(b.geom.outs).forEach(function (p) {
        var labels = hovers[p.handle] || [];
        var once = labels.filter(function (label, i) { return label && labels.indexOf(label) === i; });
        if (once.length) p.hover = once.join('\n');
      });
    });

    // the open layers that hold a box, outermost first
    function layersAbove(boxId) {
      var b = boxes[boxId];
      return chain(b.type === 'layer' ? b.layer.parent : b.node.namespace);
    }
    /* The bundles of unit K's decision K-D5: the wires that run from boxes
       inside one open period layer to one reading port, the same port of
       the same node of the graph JSON, inside another open period layer,
       where they are two or more. Each bundle is `{id, key, from, to,
       reader, into, wires, join}`: `key`, which names the one port at the
       reading period's border its wires share; `from` and `to`, the
       namespaces of the writers' period and the reader's; `reader` and
       `into`, the reading port's node and port in the graph JSON; the ids
       of its wires; and the label they print. Each wire leaves the
       writers' period at a border port of its own, so that its first run
       is straight, and the wires' pieces at the graph's root, `pieces`,
       set where the wires are cut, are routed to the one reading port and
       meet on one vertical run in the gap, from which they share the run
       into the reading period (design pass 13 §1, rule 4; check 27). */
    var bundles = [], bundleOf = {};
    (function () {
      var groups = {}, order = [];
      wires.forEach(function (w) {
        var A = layersAbove(w.source), B = layersAbove(w.target);
        if (!A.length || !B.length || A[0] === B[0] || !PERIOD.test(A[0]) || !PERIOD.test(B[0])) return;
        var key = 'pair:' + A[0] + '|' + B[0] + '|' + w.to + '|' + w.into;
        if (!groups[key]) {
          groups[key] = { id: 'pair::' + A[0] + '|' + w.to + '|' + w.into, key: key, from: A[0], to: B[0],
                          reader: w.to, into: w.into, wires: [], join: w.join, cable: !!w.cable, count: 0 };
          order.push(key);
        }
        groups[key].wires.push(w.id);
        groups[key].count += w.count || 1;
        groups[key].cable = groups[key].cable && !!w.cable;
      });
      order.forEach(function (key) {
        if (groups[key].wires.length < 2) return;
        // the shared piece of cables prints the count of the wires of them all (design pass 10 §6)
        if (groups[key].cable) groups[key].join = cableLabel(null, groups[key].count);
        bundles.push(groups[key]);
        groups[key].wires.forEach(function (id) { bundleOf[id] = groups[key]; });
      });
    })();
    wires.forEach(function (w) { if (bundleOf[w.id]) w.bundle = bundleOf[w.id].id; });

    /* The `+ period` controls (§3.6), each as wide as its words with
       G.addPad at each side and G.addH high (design pass 2, §2). A control
       between two periods is no box of ELK's graph: `read` places it in the
       gap between the two period layers, past the pieces of the root that
       cross the gap, whose labels keep the room for it, or past the edge
       that keeps that room where no piece crosses (K-D13). The control at
       the earliest end is a box of the root, with an edge from it to the
       earliest period's layer, at ports on the sides the root's direction
       gives, so that ELK sets it before that layer; the edge is laid out
       and drawn by no wire. A control whose later period's layer is not on
       the root is left out. */
    var rootDir = dirOf('');
    // the Codicon `add`, G.addGap, and its word in Small, with G.addPad at each side (design pass 13 §2, rule 8;
    // design pass 14 §8)
    var addSize = { width: Math.ceil(G.addIcon + G.addGap + measure(PERIOD_WORDS, 'small') + 2 * G.addPad), height: G.addH };
    // the controls between two periods, by `<earlier>|<later>`, and the ids of those whose gap a piece of the root crosses
    var gapControls = {}, crossed = {};
    // the control in the gap between the period layers `a` and `b`, or null
    function gapBetween(a, b) { return gapControls[a + '|' + b] || gapControls[b + '|' + a] || null; }
    // the namespace of the outermost layer that holds the box `id`, the open layers above it being `above`,
    // or of the box itself where it is a closed layer of the root; null for a box of the root that is no layer
    function outermost(id, above) {
      return above.length ? above[0] : boxes[id].type === 'layer' ? boxes[id].namespace : null;
    }
    function addPort(boxId, way) {
      var elk = elkNodes[boxId], box = boxes[boxId];
      var side = way === 'out' ? (rootDir === 'DOWN' ? 'SOUTH' : 'EAST') : (rootDir === 'DOWN' ? 'NORTH' : 'WEST');
      var port = { id: boxId + '::' + way + '::add', width: 0, height: 0, layoutOptions: { 'elk.port.side': side } };
      if (!box.open) {   // a closed layer's box, whose ports stand at fixed places
        port.x = side === 'EAST' ? box.geom.width : side === 'WEST' ? 0 : box.geom.width / 2;
        port.y = side === 'SOUTH' ? box.geom.height : side === 'NORTH' ? 0 : box.geom.height / 2;
      }
      elk.ports.push(port);
      return port.id;
    }
    function onRoot(ns) { return !!ns && !!boxes[ns + LAYER_ENDING] && !m.layers[ns].parent; }
    (options.adds || []).forEach(function (add) {
      var between = addPeriods(add);
      if (!onRoot(between.later) || (between.earlier && !onRoot(between.earlier))) return;
      var id = ADD_PERIOD + add.target;
      if (between.earlier) {
        boxes[id] = { id: id, type: 'add', target: add.target, name: add.name, parent: null, later: between.later,
                      size: addSize, gap: { earlier: between.earlier, later: between.later } };
        gapControls[between.earlier + '|' + between.later] = boxes[id];
        return;
      }
      var inside = rootDir === 'DOWN' ? ['NORTH', 'SOUTH'] : ['WEST', 'EAST'];
      var elk = { id: id, width: addSize.width, height: addSize.height, layoutOptions: { 'elk.portConstraints': 'FIXED_SIDE' },
        ports: [{ id: id + '::in', width: 1, height: 1, layoutOptions: { 'elk.port.side': inside[0] } },
                { id: id + '::out', width: 1, height: 1, layoutOptions: { 'elk.port.side': inside[1] } }] };
      elkNodes[id] = elk;
      elkRoot.children.push(elk);
      elkRoot.edges.push({ id: id + '::to', sources: [id + '::out'], targets: [addPort(between.later + LAYER_ENDING, 'in')] });
      boxes[id] = { id: id, type: 'add', target: add.target, name: add.name, parent: null, later: between.later, size: addSize };
    });

    /* A wire that crosses the border of an open layer is cut there: each open
       layer it leaves or enters gains a port for it, and each piece is an
       edge, ELK's record of a wire, in the layer it runs in. The wires of a
       bundle cross the border of the reading period at the bundle's one
       port, and the writing period's border each at a port of its own, so
       that their pieces at the root meet on one vertical run in the gap
       and share the run into the reading period (K-D5; design pass 13 §1,
       rule 4). No piece of a cable keeps room for a label at rest (B4). */
    var portsMade = {}, piecesMade = {};
    // the room of a `+ period` control in the gap between two periods, along the root's direction, the
    // control with G.layerPad at each side (K-D13): the periods of a graph with controls stand that far
    // apart, where it is more than G.periodGap, so that every gap holds its control and no piece of a cable
    // keeps room for a label (design pass 13 §2, rule 9; B4)
    var room = (rootDir === 'DOWN' ? addSize.height : addSize.width) + 2 * G.layerPad;
    if (options.adds && !stageView) elkRoot.layoutOptions['elk.layered.spacing.nodeNodeBetweenLayers'] = String(Math.max(G.periodGap, room));
    function layerPort(ns, way, key) {
      var id = ns + LAYER_ENDING + '::' + way + '::' + key;
      if (!portsMade[id]) {
        portsMade[id] = true;
        var outer = dirOf(m.layers[ns].parent);
        var side = way === 'hin' ? (outer === 'DOWN' ? 'NORTH' : 'WEST') : (outer === 'DOWN' ? 'SOUTH' : 'EAST');
        elkNodes[ns + LAYER_ENDING].ports.push({ id: id, width: 0, height: 0, layoutOptions: { 'elk.port.side': side } });
      }
      return id;
    }
    wires.forEach(function (w) {
      var A = layersAbove(w.source), B = layersAbove(w.target);
      var d = 0;
      while (d < A.length && d < B.length && A[d] === B[d]) d++;
      // a bundle's wires run from one period to another, so that d is 0 and A[0] and B[0] are the two periods;
      // the wires that enter an open period from a box of the graph's root, a boundary marker or a closed period,
      // into one socket cross the period's border at one port, the socket's, so that they meet outside the frame
      // and share one run across its border into the socket, and the frame keeps its padding (the fix wave Q3a,
      // item 6; A22, B20)
      var bundle = bundleOf[w.id] || null, pieces = [], from = w.sourceHandle, i;
      var fromRoot = !A.length && B.length > 0 && PERIOD.test(B[0]);
      function keyAt(depth) {
        if (bundle && depth === 0) return bundle.key;
        if (fromRoot && depth === 0) return 'into:' + (elkPortOf[w.targetHandle] || w.targetHandle);
        return w.sourceHandle;
      }
      for (i = A.length - 1; i >= d; i--) {
        var pOut = layerPort(A[i], 'hout', w.sourceHandle);
        pieces.push({ container: A[i], source: from, target: pOut });
        from = pOut;
      }
      var into = [];
      for (i = d; i < B.length; i++) into.push(layerPort(B[i], 'hin', keyAt(i)));
      // the control in the gap that the wire's piece at the root crosses, between two periods' layers, open or
      // closed, or null
      var gap = d === 0 ? gapBetween(outermost(w.source, A), outermost(w.target, B)) : null;
      if (gap) crossed[gap.id] = true;
      // the reading end's ELK port, the one port of a card's socket (A8)
      var last = elkPortOf[w.targetHandle] || w.targetHandle;
      // a piece of a wire of the stage graph prints the label of its joins, and a piece of a cable none (B4)
      var label = w.cable ? '' : bundle ? bundle.join : w.join;
      pieces.push({ container: d ? A[d - 1] : '', source: from, target: into.length ? into[0] : last,
                    join: label, bundle: bundle });
      for (i = 0; i < into.length; i++) pieces.push({ container: B[d + i], source: into[i], target: i + 1 < into.length ? into[i + 1] : last });
      w.pieces = pieces.map(function (p) {
        var id = p.source + '>>' + p.target;
        if (p.bundle) (p.bundle.pieces = p.bundle.pieces || []).push(id);
        if (!piecesMade[id]) {
          piecesMade[id] = true;
          // an edge of no thickness, so that the spacing ELK keeps between a vertical run and the boxes beside
          // it is the spacing named and not that spacing and the edge's own pixel
          var edge = { id: id, sources: [p.source], targets: [p.target], layoutOptions: { 'elk.edge.thickness': '0' } };
          // a join's label stands beside its wire, over it, in the layer where the two stage occurrences stand, in the
          // face of a wire's label, `join`; ELK keeps its room, a line of G.joinLine on either side of the wire, so
          // that the label's line over the wire is clear (AAS, M-D15)
          if (p.join) {
            var width = Math.ceil(measure(p.join, 'join')) + 8, height = 2 * G.joinLine;
            edge.labels = [{ id: id + '::join', text: p.join, width: width, height: height,
                             layoutOptions: { 'elk.edgeLabels.inline': 'true', 'elk.edgeLabels.placement': 'CENTER' } }];
          }
          container(p.container).edges.push(edge);
        }
        return id;
      });
    });
    /* A gap that holds a `+ period` control and that no piece of the root
       crosses is held by an edge of the root from the earlier period's
       layer to the later one's, which keeps the two layers in their order
       and the root's spacing between them, the control's room; ELK lays it
       out while no wire draws it (K-D13). */
    Object.keys(gapControls).forEach(function (pair) {
      var box = gapControls[pair];
      if (crossed[box.id]) return;
      elkRoot.edges.push({ id: box.id + '::room', sources: [addPort(box.gap.earlier + LAYER_ENDING, 'out')],
        targets: [addPort(box.gap.later + LAYER_ENDING, 'in')] });
    });
    // every open period's ELK node receives its occurrences in the rank of their stage keys, an occurrence drawn
    // in full and a card alike, so that ELK keeps one row order in every period (the fix wave Q3a, item 2)
    Object.keys(ordered).forEach(function (period) {
      var frame = elkNodes[period + LAYER_ENDING];
      if (!frame) return;
      var given = frame.children.slice();
      function rankOfChild(child) { var b = boxes[child.id]; return rankOf(b && b.type === 'layer' ? b.namespace : ''); }
      frame.children.sort(function (a, b) { return rankOfChild(a) - rankOfChild(b) || given.indexOf(a) - given.indexOf(b); });
    });
    return { elk: elkRoot, boxes: boxes, wires: wires, bundles: bundles, pairBundles: pairBundles, compact: compact,
             stage: aligned ? stageColumn(m, namespaces, boxes, wires) : null };
  }

  /* What `arrange` aligns in a stage's builders graph (AAS, L-D20), from
     the boxes `boxes` and the wires `wires` that `build` lays out:
     `column`, the ids of the boxes of the graph's root that stand in one
     column, from top to bottom, the stage's `Inputs`, a box of the root
     that only writes, then the longest chain of builders, open or closed,
     in which a wire joins each builder to the next, then the stage's
     `Outputs`, a box of the root that only reads; and `frames`, the least
     width of each open layer of the root by its id. Of two chains of equal
     length, or two writers of one builder, the one whose builder comes
     first in `namespaces`, the order of the graph JSON, is taken; a wire
     that would close a cycle extends no chain. */
  function stageColumn(m, namespaces, boxes, wires) {
    var builders = namespaces.filter(function (ns) { return !m.layers[ns].parent && boxes[m.layers[ns].id]; })
      .map(function (ns) { return m.layers[ns].id; });
    // the box of the root that stands for the box `id`: itself, or the layer of the root above it
    function rootOf(id) {
      var b = boxes[id], ns = b.type === 'layer' ? b.namespace : b.node ? b.node.namespace : '';
      return ns ? chain(ns)[0] + LAYER_ENDING : id;
    }
    var writers = {};
    builders.forEach(function (id) { writers[id] = []; });
    wires.forEach(function (w) {
      var a = rootOf(w.source), b = rootOf(w.target);
      if (a !== b && writers[a] && writers[b] && writers[b].indexOf(a) < 0) writers[b].push(a);
    });
    builders.forEach(function (id) { writers[id].sort(function (a, b) { return builders.indexOf(a) - builders.indexOf(b); }); });
    // the number of builders of the longest chain that ends at each builder, and the builder before it there
    var length = {}, before = {};
    function longest(id, seen) {
      if (id in length) return length[id];
      var best = 0, from = null;
      writers[id].forEach(function (w) {
        if (seen.indexOf(w) >= 0) return;
        var n = longest(w, seen.concat([id]));
        if (n > best) { best = n; from = w; }
      });
      length[id] = best + 1;
      before[id] = from;
      return length[id];
    }
    var end = null;
    builders.forEach(function (id) { if (end === null || longest(id, []) > length[end]) end = id; });
    var path = [];
    for (var at = end; at; at = before[at]) path.unshift(at);
    // the stage's own `Inputs` and `Outputs`, the boxes of the root that only write or only read
    var top = null, bottom = null, frames = {};
    Object.keys(boxes).forEach(function (id) {
      var b = boxes[id];
      if (b.parent || b.type !== 'boundary') return;
      if (!b.node.inputs.length && b.node.outputs.length && top === null) top = id;
      if (b.node.inputs.length && !b.node.outputs.length && bottom === null) bottom = id;
    });
    builders.forEach(function (id) { if (boxes[id].open) frames[id] = boxes[id].least; });
    return { column: (top ? [top] : []).concat(path, bottom ? [bottom] : []), frames: frames };
  }

  /* The route that the routes `routes` share from their common first
     point, each a list of points, as `{points, rests}`: `points`, the
     shared route, which ends where the first of them turns away from the
     others; and `rests`, each route from that point on. Two routes share a
     segment to a point that both reach next, and share a segment along one
     axis, in one direction, as far as the nearer of their next points. The
     shared route stops short of any route's last point, so that each rest
     holds a segment. */
  function sharedStart(routes) {
    var here = routes[0][0], points = [here], at = routes.map(function () { return 0; });
    function same(a, b) { return Math.abs(a.x - b.x) < 0.01 && Math.abs(a.y - b.y) < 0.01; }
    // whether every step `own` along one axis has one sign while every step `other` along the other is none
    function along(own, other) {
      return other.every(function (d) { return Math.abs(d) < 0.01; }) &&
        (own.every(function (d) { return d > 0.01; }) || own.every(function (d) { return d < -0.01; }));
    }
    for (;;) {
      var next = routes.map(function (route, k) { return route[at[k] + 1]; });
      if (next.some(function (point) { return !point; })) break;
      // whether each route's next point is its last
      var last = routes.map(function (route, k) { return at[k] + 2 >= route.length; });
      if (next.every(function (point) { return same(point, next[0]); })) {
        if (last.some(Boolean)) break;
        here = next[0];
        points.push(here);
        at = at.map(function (n) { return n + 1; });
        continue;
      }
      var dx = next.map(function (point) { return point.x - here.x; });
      var dy = next.map(function (point) { return point.y - here.y; });
      var horizontal = along(dx, dy);
      if (!horizontal && !along(dy, dx)) break;
      var lengths = (horizontal ? dx : dy).map(Math.abs), least = Math.min.apply(null, lengths);
      if (lengths.some(function (length, k) { return last[k] && length - least < 0.01; })) break;
      here = horizontal ? { x: here.x + Math.sign(dx[0]) * least, y: here.y } : { x: here.x, y: here.y + Math.sign(dy[0]) * least };
      points.push(here);
      lengths.forEach(function (length, k) { if (length - least < 0.01) at[k] += 1; });
    }
    var rests = routes.map(function (route, k) {
      var rest = route.slice(at[k] + 1);
      return Math.abs(route[at[k]].x - here.x) < 0.01 && Math.abs(route[at[k]].y - here.y) < 0.01
        ? [route[at[k]]].concat(rest) : [here].concat(rest);
    });
    return { points: points, rests: rests };
  }

  // The ending of the id of an undrawn edge, or of its ports: an edge of ELK's graph between the middles of two
  // boxes of the column, which `arrange` lays out and no wire draws.
  var UNDRAWN = '::undrawn';
  // The priority of an undrawn edge's straightness over every wire's, which ELK's placement of the root honors.
  var STRAIGHT = '1000';
  // The distance in pixels within which a route's end meets the edge of a box.
  var NEAR = 1.5;

  /* The points of the one section of the edge `edge` of an answer of ELK,
     on the pane. */
  function pointsOf(edge) {
    var s = (edge.sections || [])[0];
    return s ? [s.startPoint].concat(s.bendPoints || [], [s.endPoint]) : [];
  }

  /* Moves every route inside the box `node` of an answer of ELK, its own
     and those of the boxes inside it, by `dx` and `dy` on the pane. */
  function moveRoutes(node, dx, dy) {
    (node.edges || []).forEach(function (e) {
      pointsOf(e).forEach(function (p) { p.x += dx; p.y += dy; });
      (e.labels || []).forEach(function (l) { l.x += dx; l.y += dy; });
    });
    (node.children || []).forEach(function (c) { moveRoutes(c, dx, dy); });
  }

  /* The route of the edge `edge`, laid out downward, after the boxes of
     the bands `bands` have moved across by each band's `shift` (AAS,
     L-D20). A vertical segment moves with the band it passes, from the
     band's `top` to its `bottom`, relative to the frame whose top stands at
     `top` on the pane, or meets at its end; one that passes or meets bands
     of different shifts turns across at the middle of the gap between
     them; a horizontal segment keeps its height and joins the segments
     before and after it. A route with a segment that is neither is left as
     it stands. */
  function reroute(edge, bands, top) {
    var s = (edge.sections || [])[0], pts = pointsOf(edge), out = [];
    if (!s || pts.length < 2) return;
    function emit(x, y) {
      var last = out[out.length - 1];
      if (!last || Math.abs(last.x - x) > 0.01 || Math.abs(last.y - y) > 0.01) out.push({ x: x, y: y });
    }
    for (var i = 0; i + 1 < pts.length; i++) {
      var a = pts[i], b = pts[i + 1];
      if (Math.abs(a.x - b.x) > 0.01) {
        if (Math.abs(a.y - b.y) > 0.01) return;
        // a horizontal segment's ends are those of the vertical segments beside it, or its own at the route's ends
        if (i === 0) emit(a.x, a.y);
        if (i + 2 === pts.length) emit(b.x, b.y);
        continue;
      }
      var down = b.y >= a.y, low = Math.min(a.y, b.y) - top, high = Math.max(a.y, b.y) - top;
      var met = bands.filter(function (band) { return low <= band.bottom + NEAR && high >= band.top - NEAR; });
      if (!down) met.reverse();
      if (!met.length) { emit(a.x, a.y); emit(b.x, b.y); continue; }
      emit(a.x + met[0].shift, a.y);
      for (var k = 0; k + 1 < met.length; k++) {
        if (met[k].shift === met[k + 1].shift) continue;
        var upper = down ? met[k] : met[k + 1], lower = down ? met[k + 1] : met[k];
        var gap = top + (upper.bottom + lower.top) / 2;
        emit(a.x + met[k].shift, gap);
        emit(a.x + met[k + 1].shift, gap);
      }
      emit(b.x + met[met.length - 1].shift, b.y);
    }
    if (out.length < 2) return;
    s.startPoint = out[0];
    s.endPoint = out[out.length - 1];
    s.bendPoints = out.slice(1, -1);
  }

  /* Ends the route of the edge `edge`, laid out downward, at the abscissa
     `x` on the pane, at its first point where `first` holds and at its last
     otherwise: the vertical segment that meets that end moves across to
     `x`, and a route that is one vertical line turns across at its middle,
     so that its other end stays where it stands. */
  function meet(edge, x, first) {
    var s = (edge.sections || [])[0], pts = pointsOf(edge);
    if (!s || pts.length < 2) return;
    if (!first) pts.reverse();
    if (Math.abs(pts[0].x - x) < 0.01) return;
    // the points of the vertical segment, one line, that meets the end
    var run = 1;
    while (run < pts.length && Math.abs(pts[run].x - pts[0].x) < 0.01) run++;
    if (run < pts.length) for (var i = 0; i < run; i++) pts[i] = { x: x, y: pts[i].y };
    else {
      var middle = (pts[0].y + pts[pts.length - 1].y) / 2, other = pts[pts.length - 1];
      pts = [{ x: x, y: pts[0].y }, { x: x, y: middle }, { x: other.x, y: middle }, other];
    }
    if (!first) pts.reverse();
    s.startPoint = pts[0];
    s.endPoint = pts[pts.length - 1];
    s.bendPoints = pts.slice(1, -1);
  }

  /* Centers the boxes of the open layer `frame` of an answer of ELK, laid
     out downward, whose top stands at `top` on the pane, on its vertical
     axis, the middle of its width (AAS, L-D20). ELK's SIMPLE placement
     centers each of its layers in what the frame holds, the routes of the
     wires that pass a layer included, and a frame wider than what it holds
     keeps that at its left. The boxes of each band, the boxes that one of
     ELK's layers holds, are moved across together so that they stand
     centered on the axis, with the routes that pass the band, and each
     route is drawn again by `reroute`; the frame's own ports stand where
     ELK placed them. */
  function centerBands(frame, top) {
    var kids = (frame.children || []).slice().sort(function (a, b) { return a.y - b.y; });
    var axis = frame.width / 2, bands = [];
    kids.forEach(function (k) {
      var band = bands[bands.length - 1];
      if (band && k.y < band.bottom - 0.01) { band.boxes.push(k); band.bottom = Math.max(band.bottom, k.y + k.height); }
      else bands.push({ boxes: [k], top: k.y, bottom: k.y + k.height });
    });
    var moved = false;
    bands.forEach(function (band) {
      var l = Infinity, r = -Infinity;
      band.boxes.forEach(function (k) { l = Math.min(l, k.x); r = Math.max(r, k.x + k.width); });
      // a whole pixel, so that every box and its ports stay on whole pixels (design pass 13 §1, rule 1)
      band.shift = Math.round(axis - (l + r) / 2);
      if (band.shift) moved = true;
    });
    if (!moved) return;
    bands.forEach(function (band) {
      if (band.shift) band.boxes.forEach(function (k) { k.x += band.shift; moveRoutes(k, band.shift, 0); });
    });
    // the frame's own ports, above its first band and under its last, which do not move
    var fixed = [{ top: -Infinity, bottom: 0, shift: 0 }].concat(bands, [{ top: frame.height, bottom: Infinity, shift: 0 }]);
    (frame.edges || []).forEach(function (e) { reroute(e, fixed, top); });
  }

  /* ELK's answer `answer` to the graph of `built`, aligned where `built`
     holds a stage's builders graph (`built.stage`; AAS, L-D20), with `elk`,
     ELK's layout object; a promise of the answer, which `read` reads.
     First the boxes of every open layer are centered on its vertical axis,
     the deepest layer first (`centerBands`). Then ELK lays out the graph's
     root again, each box of its root as one box with its ports at the
     places the first answer gives, every open layer of the root, those of
     the column of `built.stage` and those beside it, the policy builder's
     among them, as wide as the widest of them, and each at least as wide
     as its name and its toggle need; an edge of ELK's graph that no wire
     draws, UNDRAWN, joins the middle of the lower edge of each box of the
     column to the middle of the upper edge of the next, its straightness
     taking the priority STRAIGHT, so that ELK's placement stands the column
     on one axis. The second answer's places and routes of the root replace
     the first's, each open layer's content moved with it and centered in
     its width; the undrawn edges are left out. */
  function arrange(built, answer, elk) {
    var stage = built.stage;
    if (!stage) return Promise.resolve(answer);
    // each box of the answer, deepest first among the open layers, with its top on the pane
    var found = [];
    (function walk(node, top) {
      (node.children || []).forEach(function (c) {
        found.push({ node: c, top: top + c.y, depth: (built.boxes[c.id] && built.boxes[c.id].namespace || '').split('/').length });
        walk(c, top + c.y);
      });
    })(answer, 0);
    found.filter(function (f) { var b = built.boxes[f.node.id]; return b && b.type === 'layer' && b.open; })
      .sort(function (a, b) { return b.depth - a.depth; })
      .forEach(function (f) { centerBands(f.node, f.top); });
    var inColumn = {};
    stage.column.forEach(function (id) { inColumn[id] = true; });
    // the width of every open layer of the root, the policy builder's included: the widest of their widths, each
    // taken at least at its least width
    var widest = 0;
    answer.children.forEach(function (c) { if (c.id in stage.frames) widest = Math.max(widest, c.width, stage.frames[c.id]); });
    var root = { id: 'root', layoutOptions: JSON.parse(JSON.stringify(built.elk.layoutOptions)), children: [], edges: [] };
    var shifts = {};
    answer.children.forEach(function (c) {
      var width = c.width, shift = 0;
      if (c.id in stage.frames) {
        width = widest;
        // a whole pixel, so that the boxes inside the frame stay on whole pixels
        shift = Math.round((width - c.width) / 2);
      }
      shifts[c.id] = shift;
      // where a route inside an open layer meets each of its ports, so that ELK's route at the root, which meets
      // a port at its middle, meets it there
      var meets = {};
      (c.edges || []).forEach(function (e) {
        var pts = pointsOf(e);
        if (pts.length) { meets[e.sources[0]] = pts[0].x; meets[e.targets[0]] = pts[pts.length - 1].x; }
      });
      var ports = (c.ports || []).map(function (p) {
        var x = p.id in meets ? meets[p.id] - c.x - p.width / 2 : p.x;
        return { id: p.id, width: p.width, height: p.height, x: x + shift, y: p.y };
      });
      if (inColumn[c.id]) {
        ports.push({ id: c.id + UNDRAWN + '-in', width: 1, height: 1, x: width / 2 - 0.5, y: -0.5 });
        ports.push({ id: c.id + UNDRAWN + '-out', width: 1, height: 1, x: width / 2 - 0.5, y: c.height - 0.5 });
      }
      root.children.push({ id: c.id, width: width, height: c.height, ports: ports, layoutOptions: { 'elk.portConstraints': 'FIXED_POS' } });
    });
    (answer.edges || []).forEach(function (e) {
      root.edges.push({ id: e.id, sources: e.sources.slice(), targets: e.targets.slice(),
        labels: (e.labels || []).map(function (l) { return { id: l.id, text: l.text, width: l.width, height: l.height, layoutOptions: l.layoutOptions }; }) });
    });
    for (var i = 0; i + 1 < stage.column.length; i++) {
      root.edges.push({ id: stage.column[i] + UNDRAWN, sources: [stage.column[i] + UNDRAWN + '-out'], targets: [stage.column[i + 1] + UNDRAWN + '-in'],
                        layoutOptions: { 'elk.layered.priority.straightness': STRAIGHT } });
    }
    // ELK takes its own copy, since it writes into the graph it lays out
    return elk.layout(JSON.parse(JSON.stringify(root))).then(function (second) {
      var placed = {};
      second.children.forEach(function (c) { placed[c.id] = c; });
      answer.children.forEach(function (c) {
        var at = placed[c.id], shift = shifts[c.id];
        moveRoutes(c, at.x + shift - c.x, at.y - c.y);
        (c.children || []).forEach(function (k) { k.x += shift; });
        (c.ports || []).forEach(function (p) { p.x += shift; });
        c.x = at.x; c.y = at.y; c.width = at.width;
      });
      answer.edges = second.edges.filter(function (e) { return e.id.slice(-UNDRAWN.length) !== UNDRAWN; });
      // each route of the root meets the route inside an open layer at the layer's port, which ELK may have
      // placed up to half a pixel across from where it was given
      var leaving = {}, reaching = {};
      answer.children.forEach(function (c) {
        (c.edges || []).forEach(function (e) {
          var pts = pointsOf(e);
          if (pts.length) { leaving[e.sources[0]] = pts[0]; reaching[e.targets[0]] = pts[pts.length - 1]; }
        });
      });
      answer.edges.forEach(function (e) {
        if (leaving[e.targets[0]]) meet(e, leaving[e.targets[0]].x, false);
        if (reaching[e.sources[0]]) meet(e, reaching[e.sources[0]].x, true);
      });
      answer.width = second.width;
      answer.height = second.height;
      return answer;
    });
  }

  /* The points of the route `points` snapped (design pass 13 §1, rule 4;
     A7, check 29): the route begins at `start` and ends at `end`, the
     exact places of its two ports; every run is horizontal or vertical,
     a step of less than a pixel across a run taken into the run, which
     keeps the coordinate of its first point, the first run the writing
     port's and the last run the reading port's; a run shorter than 2 px
     between two parallel runs is removed, those taking the coordinate of
     the one nearer a port; and a point between two others on one line
     adds nothing. */
  function snapRoute(points, start, end) {
    if (points.length < 2) return points;
    var out = [{ x: start.x, y: start.y }];
    function push(p) {
      var last = out[out.length - 1];
      if (Math.abs(last.x - p.x) > 0.01 || Math.abs(last.y - p.y) > 0.01) out.push(p);
      return out[out.length - 1];
    }
    var here = out[0];
    for (var i = 1; i < points.length; i++) {
      var p = points[i], dx = p.x - here.x, dy = p.y - here.y;
      if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) continue;
      if (Math.abs(dy) < 1 && Math.abs(dx) >= Math.abs(dy)) here = push({ x: p.x, y: here.y });
      else if (Math.abs(dx) < 1) here = push({ x: here.x, y: p.y });
      else { push({ x: p.x, y: here.y }); here = push({ x: p.x, y: p.y }); }
    }
    if (out.length < 2) out.push({ x: end.x, y: end.y });
    // a route of one run joins the two ports straight where they stand in line, and else by two runs, the first
    // along the axis the ports are farther apart on
    if (out.length === 2) {
      var s = out[0], e = { x: end.x, y: end.y };
      if (Math.abs(s.x - e.x) < 0.01 || Math.abs(s.y - e.y) < 0.01) return [s, e];
      return Math.abs(e.y - s.y) >= Math.abs(e.x - s.x) ? [s, { x: s.x, y: e.y }, e] : [s, { x: e.x, y: s.y }, e];
    }
    // the last run ends at the reading port and takes its coordinate, a vertical run the port's x and a
    // horizontal run the port's y
    var n = out.length, last = out[n - 1], before = out[n - 2];
    if (Math.abs(last.x - before.x) < 0.01) { before.x = end.x; last.x = end.x; last.y = end.y; }
    else { before.y = end.y; last.y = end.y; last.x = end.x; }
    // a run shorter than 2 px between two parallel runs is removed, those taking the coordinate of the one
    // nearer a port; a run that ends at a port keeps its coordinate, and a step between two such runs stays
    for (var k = 1; k + 2 < out.length;) {
      var a = out[k], b = out[k + 1];
      if (Math.hypot(a.x - b.x, a.y - b.y) >= 2) { k++; continue; }
      var toStart = k - 1, toEnd = out.length - 3 - k;
      if (toStart === 0 && toEnd === 0) { k++; continue; }
      var earlier = toEnd !== 0 && (toStart === 0 || toStart <= toEnd);
      var vertical = Math.abs(out[k - 1].x - a.x) < 0.01;
      if (earlier) { if (vertical) out[k + 2].x = a.x; else out[k + 2].y = a.y; }
      else if (vertical) out[k - 1].x = b.x; else out[k - 1].y = b.y;
      out.splice(k, 2);
      if (k > 1) k--;
    }
    // a point between two others on one line adds nothing
    var kept = [];
    out.forEach(function (p, i) {
      var a = kept[kept.length - 1], b = out[i + 1];
      if (a && b && ((Math.abs(a.x - p.x) < 0.01 && Math.abs(p.x - b.x) < 0.01) || (Math.abs(a.y - p.y) < 0.01 && Math.abs(p.y - b.y) < 0.01))) return;
      kept.push(p);
    });
    return kept;
  }

  /* The points of the one section of the edge `edge` set to `points`. */
  function setPoints(edge, points) {
    var s = (edge.sections || [])[0];
    if (!s) return;
    s.startPoint = points[0];
    s.endPoint = points[points.length - 1];
    s.bendPoints = points.slice(1, -1);
  }

  /* ELK's answer `answer` to the graph of `built` settled as design pass
     13 draws a trellis graph, before `read` reads it; a graph with no
     period's layer at its root is left as it stands. Every period frame
     of the root, open or closed, the box of a closed period being its
     frame closed, shares one top edge, laid out to the right, or one left
     edge, laid out downward (D13; the fix wave Q3a, item 10): each frame
     moves to the least with the routes inside it, and each card inside
     an open frame stands on whole pixels (item 12; B21). A piece of the
     root between two frames is drawn again from its moved ends: straight
     where they stand level, else with one run across the gap, so that a
     cable between periods whose ends differ in height takes its vertical
     run in the gap; the pieces into one port are one net and share one
     run (K-D5), and the runs of the nets whose spans meet stand
     G.periodSlot apart about the gap's middle, on whole pixels, in an
     order in which no two of them cross (`slotted`; item 2; A17); a
     piece's label moves with it, centered on its longest run along the
     root's direction (item 10). Each
     boundary marker then stands with its mark's near face G.markerClear
     outside the border of the frame it joins, level with its port where
     one marker joins that side of the frame, and markers that would stand
     nearer than the pitch spread about their mean at that pitch,
     G.markerPitch laid out to the right and, laid out downward, at least
     the widest label of the group with G.markerGap at each side (design
     pass 14 §3; S-D7), in
     the order of their ports and, at one port, of the occurrences they
     name; its stub is drawn again, straight where the mark is level with
     the port, else with its vertical run G.markerBend outside the frame's
     border (§1, rule 6, as item 6 amends it; check 20). Last, the drawing
     is moved so that its top left corner stands at the root's padding,
     and the answer's size is set from what it holds. */
  function settle(built, answer) {
    var children = answer.children || [], edges = answer.edges || [];
    var down = ((built.elk.layoutOptions || {})['elk.direction']) === 'DOWN';
    function boxOf(c) { return built.boxes[c.id] || null; }
    var frames = children.filter(function (c) { var b = boxOf(c); return !!b && b.type === 'layer' && PERIOD.test(b.namespace || '') && !b.layer.parent; });
    if (!frames.length) return answer;
    // one top edge, or one left edge laid out downward
    var least = Math.min.apply(null, frames.map(function (c) { return down ? c.x : c.y; }));
    frames.forEach(function (c) {
      if (down && c.x > least) { moveRoutes(c, least - c.x, 0); c.x = least; }
      else if (!down && c.y > least) { moveRoutes(c, 0, least - c.y); c.y = least; }
    });
    // each card inside an open frame on whole pixels, as ELK may center a card in a column widened by an unfolded
    // card on a half pixel (the fix wave Q3a, item 12; B21); `read` snaps the routes to its ports
    frames.forEach(function (frame) {
      (frame.children || []).forEach(function (c) {
        var b = boxOf(c);
        if (!b || !b.geom || !b.geom.card) return;
        var x = Math.round(c.x), y = Math.round(c.y);
        if (x !== c.x || y !== c.y) { moveRoutes(c, x - c.x, y - c.y); c.x = x; c.y = y; }
      });
    });
    // the anchor of every port of the root's children, the point a route meets it at
    var anchors = {};
    children.forEach(function (c) {
      (c.ports || []).forEach(function (p) { anchors[p.id] = { x: c.x + p.x + p.width / 2, y: c.y + p.y + p.height / 2, node: c }; });
    });
    function isFrame(node) { return frames.indexOf(node) >= 0; }
    // the pieces between two frames, by the pair of frames, drawn again from their moved ends, the pieces into one
    // port one net (`slotted`)
    var groups = {};
    edges.forEach(function (e) {
      var s = anchors[e.sources[0]], t = anchors[e.targets[0]];
      if (!s || !t || !isFrame(s.node) || !isFrame(t.node) || !pointsOf(e).length) return;
      var key = s.node.id + '>>' + t.node.id;
      (groups[key] = groups[key] || []).push({ edge: e, s: s, t: t, target: e.targets[0] });
    });
    Object.keys(groups).forEach(function (key) {
      var group = groups[key], s = group[0].s, t = group[0].t;
      // the gap's middle across the root's direction, on a whole pixel, and the side of the gap the writers stand on
      var middle = Math.round(down ? (s.y + t.y) / 2 : (s.x + t.x) / 2), toward = (down ? t.y - s.y : t.x - s.x) >= 0 ? 1 : -1;
      var across = slotted(group, down);
      group.forEach(function (g) {
        var s = g.s, t = g.t, run = middle + toward * across[g.target];
        var level = down ? Math.abs(s.x - t.x) < 0.01 : Math.abs(s.y - t.y) < 0.01;
        setPoints(g.edge, level ? [{ x: s.x, y: s.y }, { x: t.x, y: t.y }]
          : down ? [{ x: s.x, y: s.y }, { x: s.x, y: run }, { x: t.x, y: run }, { x: t.x, y: t.y }]
          : [{ x: s.x, y: s.y }, { x: run, y: s.y }, { x: run, y: t.y }, { x: t.x, y: t.y }]);
        labelOnRoute(g.edge, down);
      });
    });
    settleMarkers(built, answer, frames, anchors, down);
    // the drawing's top left corner at the root's padding
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    children.forEach(function (c) {
      minX = Math.min(minX, c.x); minY = Math.min(minY, c.y);
      maxX = Math.max(maxX, c.x + c.width); maxY = Math.max(maxY, c.y + c.height);
    });
    var dx = 2 - minX, dy = 2 - minY;
    if (Math.abs(dx) > 0.01 || Math.abs(dy) > 0.01) {
      children.forEach(function (c) { c.x += dx; c.y += dy; moveRoutes(c, dx, dy); });
      edges.forEach(function (e) {
        pointsOf(e).forEach(function (p) { p.x += dx; p.y += dy; });
        (e.labels || []).forEach(function (l) { l.x += dx; l.y += dy; });
      });
    }
    answer.width = maxX - minX + 4;
    answer.height = maxY - minY + 4;
    return answer;
  }

  /* The label of the piece `edge` of the root, a join's on a wire between
     two closed periods or on a stub, moved with the piece `settle` drew
     again: centered on its longest run along the root's direction, over
     whose line the canvas sets it (M-D15; the fix wave Q3a, item 10). */
  function labelOnRoute(edge, down) {
    (edge.labels || []).forEach(function (l) {
      var pts = pointsOf(edge), best = null;
      for (var i = 1; i < pts.length; i++) {
        var a = pts[i - 1], b = pts[i], along = down ? Math.abs(a.x - b.x) < 0.01 : Math.abs(a.y - b.y) < 0.01;
        var length = Math.hypot(b.x - a.x, b.y - a.y);
        if (along && (!best || length > best.length)) best = { length: length, x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
      }
      if (best) { l.x = best.x - l.width / 2; l.y = best.y - l.height / 2; }
    });
  }

  /* The offset from the gap's middle, toward the readers' side, of the run
     across the gap of each net of the pieces `group` between two frames,
     by the port the net's pieces reach, laid out downward where `down`
     holds (the fix wave Q3a, item 2; A17, B15): the pieces into one port
     are one net; a net whose pieces all run level takes no run; the
     others' runs take slots G.periodSlot apart, centered on the middle, so
     that two nets whose spans meet, their ends' places across the root's
     direction, never share a run, and in an order in which they do not
     cross: a net one of whose writers stands inside another net's span
     turns before it, nearer the writers, and a net whose reader stands
     inside another's span turns after it, the order of the pieces kept
     where neither holds. */
  function slotted(group, down) {
    var nets = [], netOf = {};
    group.forEach(function (g) {
      var net = netOf[g.target];
      if (!net) nets.push(net = netOf[g.target] = { target: g.target, from: [], to: down ? g.t.x : g.t.y });
      net.from.push(down ? g.s.x : g.s.y);
    });
    nets.forEach(function (net) {
      net.lo = Math.min.apply(null, net.from.concat([net.to]));
      net.hi = Math.max.apply(null, net.from.concat([net.to]));
    });
    var bending = nets.filter(function (net) { return net.from.some(function (v) { return Math.abs(v - net.to) > 0.01; }); });
    function inside(v, net) { return v > net.lo + 0.01 && v < net.hi - 0.01; }
    function meet(a, b) { return Math.min(a.hi, b.hi) - Math.max(a.lo, b.lo) > -0.01; }
    // whether the net `a` turns before the net `b`
    function before(a, b) { return meet(a, b) && (a.from.some(function (v) { return inside(v, b); }) || inside(b.to, a)); }
    // the nets in an order in which each turns after every net it must follow, the pieces' order kept among the rest
    var order = [], left = bending.slice();
    while (left.length) {
      var next = left.filter(function (a) { return !left.some(function (b) { return b !== a && before(b, a) && !before(a, b); }); })[0] || left[0];
      order.push(next);
      left.splice(left.indexOf(next), 1);
    }
    var slot = {}, most = -1;
    order.forEach(function (a) {
      var placed = order.slice(0, order.indexOf(a)).filter(function (b) { return meet(a, b); });
      var at = 0;
      placed.forEach(function (b) { if (before(b, a)) at = Math.max(at, slot[b.target] + 1); });
      while (placed.some(function (b) { return slot[b.target] === at; })) at++;
      slot[a.target] = at;
      most = Math.max(most, at);
    });
    var across = {};
    nets.forEach(function (net) { across[net.target] = net.target in slot ? (slot[net.target] - most / 2) * G.periodSlot : 0; });
    return across;
  }

  /* The boundary markers of the root placed after the layout (design pass
     13 §1, rule 6): see `settle`. A marker's stub is the one edge of the
     root that joins it, between its port and a frame's border port. */
  function settleMarkers(built, answer, frames, anchors, down) {
    var children = answer.children || [], edges = answer.edges || [];
    var markers = children.filter(function (c) { var b = built.boxes[c.id]; return !!b && b.type === 'marker'; });
    if (!markers.length) return;
    // the exact place on the pane of each port of a card inside a frame, by its handle, which a stub's end
    // takes in place of the frame's border port, whose anchor ELK may set half a pixel across
    var cardPorts = {};
    frames.forEach(function (frame) {
      (frame.children || []).forEach(function (c) {
        var b = built.boxes[c.id];
        if (!b || !b.geom) return;
        b.geom.ins.concat(b.geom.outs).forEach(function (p) { if (p.handle) cardPorts[p.handle] = { x: frame.x + c.x + p.x, y: frame.y + c.y + p.y }; });
      });
    });
    // each marker with its stub and the frame's port the stub joins
    var placed = [];
    markers.forEach(function (c) {
      var box = built.boxes[c.id], geom = box.geom;
      var stub = edges.filter(function (e) {
        var s = anchors[e.sources[0]], t = anchors[e.targets[0]];
        return (s && s.node === c && t && frames.indexOf(t.node) >= 0) || (t && t.node === c && s && frames.indexOf(s.node) >= 0);
      })[0];
      if (!stub) return;
      var leaves = anchors[stub.sources[0]].node === c;
      var port = leaves ? anchors[stub.targets[0]] : anchors[stub.sources[0]];
      var frame = port.node;
      // the card's port at the stub's far end, through the wire the stub is a piece of
      var wire = built.wires.filter(function (w) { return w.pieces.indexOf(stub.id) >= 0; })[0];
      var exact = wire ? cardPorts[leaves ? wire.targetHandle : wire.sourceHandle] : null;
      // the side of the frame the marker stands at, before or after it along the root's direction
      var before = down ? c.y + c.height / 2 < frame.y + frame.height / 2 : c.x + c.width / 2 < frame.x + frame.width / 2;
      placed.push({ node: c, geom: geom, stub: stub, leaves: leaves, port: port, frame: frame, before: before,
                    // the place of the mark's center along the frame's side, the card port's
                    at: exact ? (down ? exact.x : exact.y) : (down ? port.x : port.y) });
    });
    // markers of one side of one frame nearer than G.markerPitch spread about their mean at that pitch
    var groups = {};
    placed.forEach(function (m) { (groups[m.frame.id + (m.before ? '<' : '>')] = groups[m.frame.id + (m.before ? '<' : '>')] || []).push(m); });
    Object.keys(groups).forEach(function (key) {
      // in the order of their ports, and at one port in the rank of the occurrences they name (the fix wave Q3a, item 2)
      var rankOf = function (m) { var r = built.boxes[m.node.id].rank; return r == null ? Infinity : r; };
      var group = groups[key].sort(function (a, b) { return a.at - b.at || rankOf(a) - rankOf(b); });
      // laid out downward the labels stand under the marks, so the pitch is at least the widest label of the
      // group with G.markerGap at each side, so that no marker's label meets another's; laid out to the right
      // the labels stand beside the marks and the pitch stays G.markerPitch (design pass 14 §3; S-D7)
      var widest = group.reduce(function (w, m) { return Math.max(w, m.geom.labelAt.width); }, 0);
      var pitch = down ? Math.max(G.markerPitch, widest + 2 * G.markerGap) : G.markerPitch;
      var crowded = group.some(function (m, i) { return i > 0 && m.at - group[i - 1].at < pitch; });
      if (!crowded) return;
      var mean = group.reduce(function (sum, m) { return sum + m.at; }, 0) / group.length;
      group.forEach(function (m, i) { m.at = mean + (i - (group.length - 1) / 2) * pitch; });
    });
    placed.forEach(function (m) {
      var c = m.node, mark = m.geom.mark, size = mark.size;
      if (down) {
        // the mark's near face G.markerClear from the frame's top or bottom border, its center at `at`
        c.y = m.before ? m.frame.y - G.markerClear - (mark.y + size) : m.frame.y + m.frame.height + G.markerClear - mark.y;
        c.x = m.at - (mark.x + size / 2);
      } else {
        c.x = m.before ? m.frame.x - G.markerClear - (mark.x + size) : m.frame.x + m.frame.width + G.markerClear - mark.x;
        c.y = m.at - (mark.y + size / 2);
      }
      // the marker's port, on the mark's face toward the frame
      var portAt = down ? { x: m.at, y: m.before ? c.y + c.height : c.y } : { x: m.before ? c.x + c.width : c.x, y: m.at };
      (c.ports || []).forEach(function (p) { p.x = portAt.x - c.x - p.width / 2; p.y = portAt.y - c.y - p.height / 2; });
      // the frame's border port the stub joins, which the stubs into one socket share (`build`), and the stub,
      // straight where the mark is level with that port, else with its vertical run G.markerBend outside the
      // frame's border, its run into the mark or from it G.markerClear − G.markerBend, so that no stub runs on
      // the border or inside the frame and the frame keeps its paddings (the fix wave Q3a, item 6; A22, B20)
      var level = down ? Math.abs(m.at - m.port.x) < 0.01 : Math.abs(m.at - m.port.y) < 0.01;
      var border = down ? { x: m.port.x, y: m.before ? m.frame.y : m.frame.y + m.frame.height } : { x: m.before ? m.frame.x : m.frame.x + m.frame.width, y: m.port.y };
      var away = (m.before ? -1 : 1) * G.markerBend;
      var route = level ? [portAt, border] : down
        ? [portAt, { x: portAt.x, y: border.y + away }, { x: border.x, y: border.y + away }, border]
        : [portAt, { x: border.x + away, y: portAt.y }, { x: border.x + away, y: border.y }, border];
      if (!m.leaves) route.reverse();
      setPoints(m.stub, route);
      labelOnRoute(m.stub, down);
    });
  }

  /* The width each card of a period's column takes so that the column's
     cards share both edges (design pass 13 §2, rule 6; D14; Q-D25): from
     ELK's answer `answer` to the graph of `built`, the cards of each open
     period grouped by the center ELK gave them across the period's
     direction, ELK centering the cards of one of its layers; each card's
     width at rest, `restWidth`, and the widest of its column; the map of
     each card's namespace to the width it takes, the widest of its column
     or its own where that is wider, the selected card's among them, or
     null where every card has its column's width already, so that the
     caller lays the graph out again with `options.widths` only where a
     column is ragged. */
  function columnWidths(built, answer) {
    var widths = {}, changed = false;
    (answer.children || []).forEach(function (frame) {
      var b = built.boxes[frame.id];
      if (!b || b.type !== 'layer' || !b.open || !PERIOD.test(b.namespace || '')) return;
      var cards = (frame.children || []).filter(function (c) { var k = built.boxes[c.id]; return !!k && !!k.geom && !!k.geom.card; });
      if (!cards.length) return;
      var down = built.boxes[cards[0].id].dir === 'DOWN', columns = [];
      cards.forEach(function (c) {
        var center = down ? c.y + c.height / 2 : c.x + c.width / 2;
        var column = columns.filter(function (col) { return Math.abs(col.center - center) < 1; })[0];
        if (!column) columns.push(column = { center: center, cards: [] });
        column.cards.push(c);
      });
      columns.forEach(function (col) {
        var widest = Math.max.apply(null, col.cards.map(function (c) { return built.boxes[c.id].geom.restWidth; }));
        col.cards.forEach(function (c) {
          var k = built.boxes[c.id], want = Math.max(widest, k.geom.width);
          if (want !== k.geom.width) changed = true;
          widths[k.namespace] = want;
        });
      });
    });
    return changed ? widths : null;
  }

  /* ELK's answer read back: each box's place relative to its parent and on
     the pane, and each wire's route on the pane, its pieces joined end to
     end and snapped (`snapRoute`). A wire of a bundle (K-D5) is also drawn
     in `parts`, its own route up to the point from which the bundle's
     wires share theirs, the shared route drawn once, in `bundles`; a `+
     period` control between two periods takes its place in their gap
     (K-D13); and the segment of each builder of a card takes its place in
     its card, in `builders` (L-D7, L-D16). */
  function read(built, answer) {
    var place = {};
    (function walk(node, ax, ay) {
      (node.children || []).forEach(function (c) {
        place[c.id] = { x: c.x, y: c.y, width: c.width, height: c.height, ax: ax + c.x, ay: ay + c.y };
        walk(c, ax + c.x, ay + c.y);
      });
    })(answer, 0, 0);
    var pieces = {}, names = {}, labels = {};
    (function walkEdges(node) {
      (node.edges || []).forEach(function (e) {
        (e.labels || []).forEach(function (l) {
          names[e.id] = { x: l.x + l.width / 2, y: l.y + l.height / 2, text: l.text };
          labels[e.id] = l;
        });
        var pts = [];
        (e.sections || []).forEach(function (s) { pts.push(s.startPoint); (s.bendPoints || []).forEach(function (b) { pts.push(b); }); pts.push(s.endPoint); });
        pieces[e.id] = pts;
      });
      (node.children || []).forEach(walkEdges);
    })(answer);
    // the route of the pieces `ids`, joined end to end
    function joined(ids) {
      var pts = [];
      ids.forEach(function (id) {
        (pieces[id] || []).forEach(function (p) {
          var last = pts[pts.length - 1];
          if (!last || Math.abs(last.x - p.x) > 0.01 || Math.abs(last.y - p.y) > 0.01) pts.push({ x: p.x, y: p.y });
        });
      });
      // a point between two others on one straight line adds nothing
      var out = [];
      pts.forEach(function (p, i) {
        var a = out[out.length - 1], b = pts[i + 1];
        if (a && b && ((Math.abs(a.x - p.x) < 0.01 && Math.abs(p.x - b.x) < 0.01) || (Math.abs(a.y - p.y) < 0.01 && Math.abs(p.y - b.y) < 0.01))) return;
        out.push(p);
      });
      return out;
    }
    // the label of a piece that prints one: a label of a bundle without joins' text prints nothing
    function printed(id) { return names[id] && names[id].text.trim() ? names[id] : null; }
    // the exact place on the pane of every port of a box, by its handle (design pass 13 §1, rule 1)
    var portAt = {};
    Object.keys(built.boxes).forEach(function (id) {
      var b = built.boxes[id], at = place[id];
      if (!b.geom || !at) return;
      b.geom.ins.concat(b.geom.outs).forEach(function (p) { if (p.handle) portAt[p.handle] = { x: at.ax + p.x, y: at.ay + p.y }; });
    });
    var routes = {}, parts = {}, bundles = {};
    built.wires.forEach(function (w) {
      var pts = joined(w.pieces);
      routes[w.id] = pts.length >= 2 && portAt[w.sourceHandle] && portAt[w.targetHandle] ? snapRoute(pts, portAt[w.sourceHandle], portAt[w.targetHandle]) : pts;
    });
    (built.bundles || []).forEach(function (u) {
      // the route the bundle's wires share, from the reading port back to the point where the last of them
      // joins the others, drawn once, and each wire's own route up to that point (K-D5)
      var own = u.wires.map(function (id) { return routes[id].slice().reverse(); });
      if (own.some(function (r) { return r.length < 2; })) return;
      var shared = sharedStart(own);
      bundles[u.id] = { points: shared.points.slice().reverse(), join: null };
      u.wires.forEach(function (id, k) { parts[id] = [shared.rests[k].slice().reverse()]; });
    });
    // the place of each wire's label
    var joins = {};
    built.wires.forEach(function (w) {
      w.pieces.forEach(function (id) {
        if (printed(id)) joins[w.id] = printed(id);
      });
    });
    var width = answer.width, height = answer.height;
    /* A `+ period` control between two periods (K-D13): centered in the gap
       between its two period layers, and, across the root's direction, past
       every edge of the root that runs from the one layer to the other, a
       wire's piece or the edge that keeps the control's room, and past its
       label, by a layer's padding. */
    var down = ((built.elk.layoutOptions || {})['elk.direction']) === 'DOWN';
    Object.keys(built.boxes).forEach(function (id) {
      var box = built.boxes[id], size = box.size;
      if (box.type !== 'add' || !box.gap) return;
      var a = place[box.gap.earlier + LAYER_ENDING], b = place[box.gap.later + LAYER_ENDING];
      if (!a || !b) return;
      var first = (down ? a.ay <= b.ay : a.ax <= b.ax) ? a : b, second = first === a ? b : a;
      // the prefix of the ids of the ports of each of the two layers
      var ends = [box.gap.earlier + LAYER_ENDING + '::', box.gap.later + LAYER_ENDING + '::'];
      // the farthest coordinate across the root's direction that such a piece or its label reaches
      var past = null;
      function reach(value) { past = past === null ? value : Math.max(past, value); }
      (answer.edges || []).forEach(function (e) {
        var s = e.sources[0], t = e.targets[0];
        var crosses = (s.indexOf(ends[0]) === 0 && t.indexOf(ends[1]) === 0) || (s.indexOf(ends[1]) === 0 && t.indexOf(ends[0]) === 0);
        if (!crosses) return;
        (pieces[e.id] || []).forEach(function (p) { reach(down ? p.x : p.y); });
        var l = labels[e.id];
        if (l) reach(down ? l.x + l.width : l.y + l.height);
      });
      if (past === null) past = down ? Math.min(a.ax, b.ax) : Math.min(a.ay, b.ay);
      var x, y;
      if (down) { y = (first.ay + first.height + second.ay) / 2 - size.height / 2; x = past + G.layerPad; }
      else { x = (first.ax + first.width + second.ax) / 2 - size.width / 2; y = past + G.layerPad; }
      place[id] = { x: x, y: y, width: size.width, height: size.height, ax: x, ay: y };
      width = Math.max(width, x + size.width + 2);
      height = Math.max(height, y + size.height + 2);
    });
    /* The place of each builder's segment of a compact occurrence (L-D7,
       L-D16), at its place in the band of the occurrence's card, kept apart
       from `place`, which holds the boxes ELK lays out. */
    var builders = {};
    Object.keys(built.boxes).forEach(function (id) {
      var box = built.boxes[id], frame = box.type === 'builder' ? place[box.parent] : null;
      if (!frame) return;
      builders[id] = { x: box.at.x, y: box.at.y, width: box.at.width, height: box.at.height,
                       ax: frame.ax + box.at.x, ay: frame.ay + box.at.y };
    });
    return { place: place, routes: routes, parts: parts, bundles: bundles, joins: joins, width: width, height: height,
             builders: builders };
  }

  return { model: model, build: build, arrange: arrange, settle: settle, columnWidths: columnWidths, read: read, shown: shown, chain: chain, configOf: configOf, directionOf: directionOf,
           compactOccurrences: compactOccurrences, cableLabel: cableLabel, BOUNDARY_KINDS: BOUNDARY_KINDS,
           attrsOf: attrsOf, addPeriods: addPeriods, joinLabel: joinLabel, G: G, LAYER_ENDING: LAYER_ENDING, ADD_PERIOD: ADD_PERIOD,
           PERIOD_WORDS: PERIOD_WORDS, STAGE_WORDS: STAGE_WORDS, OCCURRENCE: OCCURRENCE, POLICY: POLICY,
           PAIR_BUNDLE: PAIR_BUNDLE };
});
