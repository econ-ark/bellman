/* The graph region (model interface specification 0.4, §§2 and 4).
   collection is the graph JSON, or null; graph names the graph shown.
   layers names the deepest open namespaces, as a list or by graph id.
   scope identifies the file and view: a change forgets each graph's open
   layers, seen layers and selection. The layout's direction is the page's,
   one for every graph of every stage and of the trellis in every tab: DOWN
   unless the browser's storage holds `horizontal` under `bellman-workbench
   layout`, read once at the script's load, which the foot's button turns,
   writing `horizontal` or removing the key, so that a reload, a later tab
   and the desktop app's next start open in the kept direction; a field
   diagram no longer turns on its own (design pass 14 §2; S-D5). A new collection under
   the same scope preserves that state and opens newly seen layers named
   by layers; a trellis graph that newly shows one period alone opens that
   period's occurrences and opens the view on it at the reading scale
   (unit L, Task 22). select {nodeId, graphId, n} opens and selects once by n.
   place {graph, layers, nodeId, n} restores layers and selection once by n,
   centering the selected box at the opening scale. A change of the
   region's size that finds the view still where the graph shown opened
   opens that graph again at the new size; any other change of the region's
   size fits the graph (§2.3). stale dims the Vue host.
   overlays_request gives perch lines; styles identify exported styles.
   selected {nodeId, graphId, origin} distinguishes page requests from clicks;
   opened {nodeId, graphId} reports a double click; processed reports graphId,
   boxes, wires and layout time ms; refused {graphId, sentence} reports a
   layout or build refusal (G-D9). The test handle's report precedes events.
   unjoined, given in the forward trellis graph alone, lists the ports a drag
   can take, records of which the region reads id, side, h, key, field, set,
   the field's declared set (unit K's decision K-D25), periods and
   periods_between, and, for a reading port that joins reach, sources and
   title, its hover (J-D41, J-D42); reading is the record of the elaboration
   drawn (§3.2). A drag goes from an unjoined writing port to a reading port,
   joined or not, of another stage occurrence in its period or the next,
   periods[h − 1] (§3.1, as J-D41 amends it); while it lasts the period
   layers its line would reach and the reading ports that would take it are
   marked, and its release dispatches on the host the DOM
   event connected {reading, source, target, sourceHandle, targetHandle},
   bubbling, whose handles are the ports' ids in the graph JSON (J-D17). The
   region draws no wire of a drag, and a change of unjoined or reading ends
   a drag in progress (§3.3). A port a drag can take keeps on the screen at
   every smaller scale the 9 px across it measures at scale 1, at least 8
   px, the region holding the view's scale in the property --bf-scale
   (unit K's decision K-D9). Of the ports a drag can take whose squares
   hold the pointer, the one whose center is nearest it is marked
   data-nearest and alone takes the pointer's press, drop and hover, so
   that ports that cover one another at a small scale are each taken at
   their own center (row K-I165).
   The frame of a stage occurrence, its open layer or its closed box, that
   holds an unjoined writing port is a drag's start in place of the view's
   pan: a drag from it to the frame of another stage occurrence of its
   period or of the next, periods[h − 1], that holds a reading port draws
   a line while it lasts, marks the frame it would reach .bf-frame-target,
   and at its release opens the list of the writer's unjoined continuation
   fields, each ticked where its record's pairs, which Python gives, name
   an arrival field of the reader, and each with a select of the reader's
   reading ports, every field printed with its declared set,
   `m_next : ℝ₊₊`, and ticked by name alone (K-D25); its button `Join`
   dispatches the event connected {reading, source, target, pairs}, source
   and target the two frames' layer ids and pairs the ticked rows'
   {sourceHandle, targetHandle} (unit K's decision K-D8). A change of
   unjoined or reading ends that drag and closes the list. A click on the
   graph's ground closes the list.
   stages, given with unjoined, is the stage list's record {heading, items,
   entries}, and adds the `+ period` controls, each {target, after, name}
   (§§3.5, 3.6); each item is printed on one line, its key and the name
   of its model's folder, its model's title and its parameters in its hover
   (AAS, L-D9); an item of the kind `folder`, `from a folder…`, prints
   its words alone (unit K's decision K-D26), and the item's section, which
   Python gives, `this folder's stages`, `templates` or `library`, is
   printed as one heading line before the section's first item (AAS, L-D6,
   L-D9). The controls stand between
   the period layers and before the earliest, each printing `+ period`
   with name as its hover; the button
   `stages` stands in head(), the graph's head, and opens the list over the
   graph, headed by the heading Python gives, else by `stages`, and its
   second press closes it; each period's open layer carries the control
   `+ stage` at the right of its name, which opens the list for that
   period; either list stands beside the button that opened it, within the
   region, 280 px wide (design pass 10 §7), the period's list headed by the
   period's name, an item its list holds dimmed with
   the word `listed` (unit K's decision K-D14), the control keeping 24 px
   of height and its words 11 px on the screen at every scale, which
   brand.css reads from --bf-scale (AAS, L-D5). A click outside the stage
   list, but on `stages`, closes it, and a click inside it closes nothing;
   the stage list and the list of a drag between frames each carry at the
   right of their first line the control `×`, with the hover `close`, which
   closes the list as Escape does (unit K's decision K-D24). An item
   dragged by the browser's own drag-and-drop onto a period's layer or a
   control, or chosen with Enter and
   sent with the arrow keys and Enter, an item of a period's list clicked or
   chosen with Enter, Enter on a control, and the item `from a folder…` of
   the list the button `stages` opens clicked or chosen with Enter,
   dispatch on the host the DOM event dropped {item, kind, target,
   reading}, bubbling, item and kind null for Enter on a control (J-D17),
   and target null for that item, for which Python opens the form with a
   select of the period (AAS, L-D5). While the item is dragged the layers of
   the periods its period's list writes are marked, and a layer whose list
   holds a folder stage takes no drop. The region writes and draws nothing
   from a drop. Backspace or Delete, while the region holds the focus, on
   the layer of a stage occurrence of a period selected, its card closed or
   compact, dispatches removed {reading, occurrence}, occurrence the
   layer's id (K-D14), where a drop can be made, and with reading null in
   the backward trellis graph, Python then listing the sentence that says
   why (unit N, Task 5; N-D12); in a forward graph where no drop can be
   made it dispatches nothing (N-I273). While Python withholds stages, the controls last
   given for the graph stay laid out and do not act. Where Python gives
   stages and reading but withholds adds, as it does while a reading stands
   refused and the last graph constructed is drawn (unit L, Task 14), the
   stage list opens from `stages` and from a period's `+ stage`, and an
   item is sent to a period or dropped on its layer as before, while the
   `+ period` controls stay laid out and do not act and no stage
   occurrence is removed.
   joins, given with unjoined, lists the join wires of the forward trellis
   graph, records of which the region reads source, sourceHandle, target and
   targetHandle, the wire's nodes and ports in the graph JSON, from, to,
   writing, reading, between, movable, the ends a drag can move, writing
   and reading, fields, the wire's field pairs, each {writing, reading,
   field, arrival, field_set, arrival_set, readers, writers} (J-D33, J-D39;
   unit K's decisions K-D23 and K-D25), others, the writer's other unjoined
   continuation fields, each {writing, field, field_set, readers}, which
   the list of a move of the reading end offers as rows (unit L, Task 19),
   and removable, whether an entry of
   a file writes it, false for a wire whose joins are all by equal names
   (unit L, Task 15). A click selects a join wire, drawn
   in ultramarine-light and after every other wire, each end it can move
   drawn as a square of WIRE_END px in ultramarine-light, and dispatches on
   the host the DOM event join-chosen {reading, join}, join the record, or
   null once the selection leaves it; Backspace or Delete, while the region
   holds the focus, dispatches removed {reading, join} for a removable
   wire and nothing for any other. An end of a join
   wire, taken in React Flow's circle of radius RECONNECT px beside its
   port, from the port's center out on the side the port faces, the square
   and the circle of an end of the selected wire keeping those sizes on the
   screen at every scale (unit K's decision K-D27), and dragged to a port of
   its side a drag can take, a reading port joined or not and an unjoined writing port, in
   the period of the end it replaces and, within a period, of another stage
   occurrence than the end kept, dispatches, for a wire of one field pair,
   moved {reading, join, end, handle}, end reading or writing and handle
   the new port's id; for a wire of several, it opens the list of the
   wire's field pairs, each with a select of the ports of the moved end's
   side of the stage occurrence dropped on, ticked where its record's
   readers, for a reading end, or writers, for a writing end, name one
   there, then, for a reading end, a row for each record of others, ticked
   where its readers name a port there, the line before the foot naming
   the entries the ticked field pairs take from the occurrence the end
   leaves; its button `Join` dispatches moved {reading, join, end, pairs},
   pairs the ticked rows' {sourceHandle, targetHandle, replaced}, replaced
   the id of the port the row's pair leaves and absent for a row of others
   (K-D23; unit L, Task 19); join names the wire by
   its four ids. The wires of one adjacent pair of periods that read one
   port share their piece between the two periods, drawn once as a wire of
   its own with their label (unit K's decision K-D5); it takes the record
   whose source is the writers' period, `periods[h]`, whose sourceHandle is
   null and whose target and targetHandle are the reading port's, a click
   on it selecting the pair's joins, whose reading end alone a drag moves,
   through the list, while the pieces inside a period keep selecting one
   writer's join. Every other wire takes no click, no key and no drag, and
   the region removes and moves no wire itself.
   builders, given in either trellis graph, is the record of each builder of
   a stage occurrence by its layer's namespace, {pair, place, signs, words},
   which Python reads from the pair of perches the builder's signature joins
   and never from its id (AAS, L-D7). A stage occurrence, closed or open
   with none of its builders open, is drawn as one card of 32 px (design
   pass 13 §2; AAS, L-D16 and L-D25; design pass 7 §3): its name, the
   card's one text, with the chevron whose click opens the occurrence with
   every builder open, the open layer then closing back to the card by its
   own chevron; the strip of its builders at y 24 to 27, one segment of
   equal width for each, 2 px apart, in the order of their pairs, each
   tinted by its pair's place in its direction, the policy builder in a
   third tint, with no text, its pair in words and its id as its hover; a
   click on a segment opens the builder in place, the occurrence drawn in
   full with it, and a double click on it sends opened as a closed builder
   does. Under the strip stand the rows of the fields no join reaches,
   each printing its name, a branch's fields on one row after their branch
   word; the card's ports are the cables', below, each a 6-px mark on the
   card's edge on the axis y = 14, a joined field's name in its port's
   hover at every scale. The card selected prints every field's name in a
   row of its own and its strip as the band of the pair's signs and the
   builder's id, the layout run again as the selection changes, its ports
   kept on the axis. Within a period, the wires from one card to another
   are one bundle where they are two or more, drawn as one wire,
   .bf-pair-bundle, with one label and a hover that lists its wires'
   labels and their joins; a click on it selects it, and while it or
   either of its cards is selected, or a join wire of its pair, the layout
   is run with the bundle split into its wires, those of the bundle
   selected drawn in ultramarine-light; a click on the graph's ground,
   Escape or a click on a box ends the bundle's selection (AAS, L-D25).
   The wires that carry values, as a backward trellis graph's do, are one
   cable for each route, within a period or between two, which nothing
   splits, each leaving its writer at a plug of its own; a click on it
   selects it as a join wire, by the record Python gives its first wire
   (design pass 12 §2). In a stage's builders graph the value wires from
   one box to another are one line, with the count of its wires at its
   plug and the arrowhead a stage graph's wire keeps, which no click
   selects, its title the labels of its wires one per line, lit with a
   selected box together with its ports (design pass 14 §1; S-D3). The drawing takes the sizes of
   design pass 8's mock, opens a trellis graph on its terminal period at up
   to scale 1 (`begin`) and sets a wire's label in STIX Two Math, upright,
   beside its line (M-D15; design pass 10 §5).
   stage_order, given in either trellis graph, lists the stage keys in the
   recipe's order, by which the layout stands every period's occurrences
   in rows, the same in every period of both graphs, and a card's plugs in
   the order of the cards their cables reach (the fix wave Q3a, item 2,
   which amends K-D12).
   The cables (design pass 10 §§6 and 7; unit N, Task 7): a wire between
   two stage occurrences' cards, or between a card and a boundary marker,
   is a cable, drawn as one stroke at a wire's weight from a plug into a
   socket, with no arrowhead, dashed to an `outside` marker (design pass
   11 §1a; design pass 12 §1), with no label, its route's branch first in
   its title and in Details and the count of its wires at its plug (the
   fix wave Q3a, item 4), and the ordered wires in Details; a card's handles are the
   cables' ports alone, one per continuation branch on its writing side
   and one for the arrival tuple on its reading side (`cablePort`); a
   boundary node of the graph's root, where data enter or leave the drawn
   range, is drawn as its mark with its label beside it (`Marker`). A drag
   from a joined branch port, or from a reading port one cable reaches, is
   the move of that cable's reading end, and a drag from an unjoined
   branch port a new cable; released on the arrival port of another
   occurrence of the writer's period or the next, it opens the cable's
   list beside the port dropped on (`placeList`), one row per arrival
   field of the destination with a select of the
   branch's continuation fields, pre-filled with the equal names Python
   gives as `equal`, and the count line `2 of 3 fields paired`; the ends
   of a selected cable, its ports ringed in the accent and taken in React
   Flow's circles beside them (the fix wave Q3a, item 5), open the same
   list, a writing end at a
   branch port, joined or not, of another occurrence of the reader's
   period or the one before. Its `Join` dispatches moved {reading, join,
   end, pairs, cable} or connected {reading, source, target, pairs, cable},
   `cable` marking the whole cable's write, which releases every pair of
   the route. Every record of `unjoined` holds `branch` and `joined`, and a
   writing record `equal`, the arrival field of its own name by occurrence.
   Every icon the region draws is a Codicon, VS Code's glyph that the
   page's stylesheet of Codicons draws by its name at 16 px (design pass 8
   §3; AAS, M-D4): each list's head draws the icon of its kind,
   `symbol-structure` for the stage list and `link` for the pairing list,
   the stage list draws the icon of an item's kind before its key
   (KIND_ICONS), the control that closes either list draws `close`, and a
   card's chevron draws `chevron-right` or `chevron-down` (AAS, L-D16). The
   foot's controls, the layout and the zoom, are VSCode Elements' toolbar
   buttons drawing their Codicons, in the element the property `controls`
   answers, which floats inside the canvas's lower left.
   The layout is flow-layout.js with ELK; labels and ports come from the JSON. */
(function () {
  'use strict';
  if (!window.React || !window.ReactDOM || !window.ReactFlow) return;   // the libraries did not load; the page keeps its picture
  var R = window.React, RD = window.ReactDOM, RF = window.ReactFlow, L = window.BellmanFlowLayout;
  var h = R.createElement;
  var useState = R.useState, useEffect = R.useEffect, useMemo = R.useMemo, useRef = R.useRef, useCallback = R.useCallback;
  var G = L.G;
  /* The place of the drawing in the opening and the fitted view (design pass 13 §2, rule 10; D3): its top TOP
     px below the bar, the region's top, its nearer end on the text edge, TEXT_EDGE inside the region's side, and,
     where it is fitted, ROOM at the region's right and bottom edges, so that the fitted drawing ends on the right
     text edge (the fix wave Q3a, item 9; D20); the least room CLEAR inside the region's side that a frame the
     region's far edge cuts keeps, its border; and the room REVEAL a selected card keeps inside each side of the
     region once the view pans to it (item 8; A18, B19, D23). */
  var TOP = 24, TEXT_EDGE = 12, ROOM = 12, CLEAR = 24, REVEAL = 12;
  var MIN_ZOOM = 0.05;
  // the pixel the layout keeps for a box's border inside its outer edge, at which a box's rows stand from that
  // edge now that the box draws its edge as an inset shadow, which takes no layout width (the fix wave Q3a, item 3)
  var EDGE = 1;
  var READS = 0.6;   // the least opening scale of a trellis graph
  var STAGE_READS = 0.8;   // the reading scale at which the stage view opens, so that Code labels print at 10 px (Q-D7)
  var SMALL = 0.75;   // the scale below which no count is drawn and no card unfolds (design pass 13 §1, rule 3)
  // the hover text and spoken name of a period's control `+ stage` (unit K's decision K-D14)
  var ADD_STAGE = 'add a stage to this period';
  // the radius in px of the circle beside each end of a join wire, from its port's center out, that takes the press of its drag, on the screen while the wire is selected (unit K's decisions K-D23 and K-D27)
  var RECONNECT = 16;
  // the side in px on the screen of the square drawn at each end of a selected join wire that a drag can move (K-D23, K-D27)
  var WIRE_END = 10;
  // the hover text and spoken name of the control `×` that closes the stage list and the pairing list (unit K's decision K-D24)
  var CLOSE = 'close';
  // the name the pairing list's head prints, the word of its primary button, in sentence case as the page's words
  // (design pass 4 §4; design pass 13 §3; the fix wave Q3b of unit Q, item 19, C12)
  var JOIN = 'Join';
  // the word of the button that closes a list as `×` does, in sentence case (design pass 4 §4; C12)
  var CANCEL = 'Cancel';
  // the word of the button `Stages` at the graph's bar, which also names the list it opens and a period's list in their head (K-D24; design pass 8 §§6 and 8, item 1)
  var STAGES = 'Stages';
  // the Codicon of each kind of item of the stage list, by the item's kind (design pass 8 §3): a stage `symbol-structure`, a template `layers`, a stage of the library `library`, the item `from a folder…` `folder`
  var KIND_ICONS = { stage: 'symbol-structure', template: 'layers', library: 'library', folder: 'folder' };
  // the Codicon of each list's head, by the list (design pass 8 §3): the stage list and the pairing list of a join
  var LIST_ICONS = { stages: 'symbol-structure', join: 'link' };
  // the Codicon and the accessible name of each control at the canvas's foot, by its word (design pass 8 §§3 and 6): the two layouts, which a click turns to, and the zoom
  var FOOT_CONTROLS = {
    vertical: ['split-vertical', 'Lay out from top to bottom'],
    horizontal: ['split-horizontal', 'Lay out from left to right'],
    'zoom in': ['zoom-in', 'Zoom in'],
    'zoom out': ['zoom-out', 'Zoom out'],
    fit: ['screen-full', 'Fit']
  };
  // The key in the browser's storage of the page's layout direction (design pass 14 §2, rule 2; S-D5): the value
  // `horizontal` where the layout is turned to the right, nothing where it is laid out downward, the default; kept
  // as window.vue keeps the contrast setting (R-D16).
  var LAYOUT_KEY = 'bellman-workbench layout';
  /* The page's layout direction, one for every graph of every stage and of
     the trellis in every tab (design pass 14 §2, rules 1 and 2; S-D5): DOWN
     unless the browser's storage holds `horizontal` under LAYOUT_KEY, read
     once at the script's load; `turnPage` turns it, writes `horizontal` to
     the storage or removes the key, and calls every listener, one for each
     region mounted, which lays its graph out again. The storage is read
     and written in try/catch, as window.vue reads the contrast setting:
     where it refuses, the direction holds for the page's life. */
  var pageLayout = { direction: 'DOWN', listeners: [] };
  try {
    if (window.localStorage.getItem(LAYOUT_KEY) === 'horizontal') pageLayout.direction = 'RIGHT';
  } catch (error) {
    // the storage refused the reading; the layout is vertical
  }
  function turnPage() {
    pageLayout.direction = pageLayout.direction === 'RIGHT' ? 'DOWN' : 'RIGHT';
    try {
      if (pageLayout.direction === 'RIGHT') window.localStorage.setItem(LAYOUT_KEY, 'horizontal');
      else window.localStorage.removeItem(LAYOUT_KEY);
    } catch (error) {
      // the storage refused the setting; it holds for the page's life
    }
    pageLayout.listeners.slice().forEach(function (listener) { listener(); });
  }

  /* The width of a text in the face its role is set in (brand.css, .bf-t-*). */
  var measurer = null, widths = {};
  function measure(text, role) {
    var key = role + '\u0001' + text;
    if (widths[key] != null) return widths[key];
    if (!measurer) {
      measurer = document.createElement('div');
      measurer.className = 'bf-measure';
      document.body.appendChild(measurer);
    }
    var span = document.createElement('span');
    span.className = 'bf-t-' + role;
    span.textContent = text;
    measurer.appendChild(span);
    var w = span.getBoundingClientRect().width;
    measurer.removeChild(span);
    return (widths[key] = Math.ceil(w * 10) / 10);
  }

  /* The port's complete attributes, in the order read aloud (§2.1). */
  function portDescription(port) {
    var attrs = port.attrs;
    var words = ['label', 'perch', 'role', 'type'].map(function (key) { return attrs[key]; }).filter(Boolean);
    ['paired by', 'outside'].forEach(function (key) { if (attrs[key]) words.push(key + ' ' + attrs[key]); });
    return words.join(', ');
  }

  /* What the gestures of §3.2 give the boxes and layers: the ports a drag
     can take by id; the record of the writing port of the drag in
     progress, or null; the periods whose layers the line of the drag in
     progress, or the item dragged or sent, would reach, or null; the target
     of the `+ period` control the item would reach, or null; whether a drop
     can be made now; whether the stage list opens and an item can be sent
     to a period, which holds also while a reading stands refused (unit L,
     Task 14); the function that sends the event dropped; and, for
     the drag between two frames (unit K's decision K-D8), the ports of each
     stage occurrence by its namespace (`framePorts`), the function a press
     on a frame calls, and the namespace of the frame the drag in progress
     would reach, or null. */
  var Gesture = R.createContext({ enabled: new Map(), source: null, reached: null, control: null, live: false,
    listing: false, send: null, frames: new Map(), pressFrame: null, frameTarget: null, cable: null, portStarts: null, lit: new Set(),
    moving: new Set() });
  var PERIOD = /^periods\[(\d+)\]$/;
  // the type under which an item of the stage list is dragged
  var DRAG_TYPE = 'application/x-bellman-stage';

  /* Whether the layer of `namespace` is a period's layer that the line of
     the drag in progress would reach (§3.2). */
  function isReached(gesture, namespace) {
    var match = gesture.reached ? PERIOD.exec(namespace || '') : null;
    return !!match && gesture.reached.has(Number(match[1]));
  }

  /* The key of a wire by its nodes and ports in the graph JSON, under
     which the region finds the record of a join wire (J-D33). */
  function wireKey(from, out, to, into) { return JSON.stringify([from, out, to, into]); }
  /* The four ids of a join wire's record, by which an event names it. */
  function idsOf(record) {
    return { source: record.source, sourceHandle: record.sourceHandle, target: record.target, targetHandle: record.targetHandle };
  }
  /* The ends of the join wire of `record` that a drag can move, its
     `movable`, as React Flow's edge names them: true for both ends,
     'target' for the reading end alone, 'source' for the writing end
     alone, false for none or for a wire that is no join wire (unit K's
     decision K-D23). */
  function reconnectEnds(record) {
    var ends = (record && record.movable) || [];
    var writing = ends.indexOf('writing') >= 0, reading = ends.indexOf('reading') >= 0;
    return writing && reading ? true : reading ? 'target' : writing ? 'source' : false;
  }

  /* The id in the graph JSON of the port whose handle is `handleId` on the
     box `nodeId`, `type` being the handle's, source or target; null for a
     handle of another form. */
  function portOf(nodeId, handleId, type) {
    var head = nodeId + (type === 'source' ? '::out::' : '::in::');
    return handleId && handleId.indexOf(head) === 0 ? handleId.slice(head.length) : null;
  }

  /* Whether the drag from the writing port `s` can end at the port `t`,
     each a record of the ports a drag can take: a reading port, joined or
     not, of another stage occurrence in the same period or of any stage
     occurrence in the next, periods[h − 1] (§3.1, as J-D41 amends it). */
  function takesDrag(s, t) {
    return s.side === 'writing' && t.side === 'reading' && ((t.h === s.h && t.key !== s.key) || t.h === s.h - 1);
  }

  /* A port's handle. A port among the ports a drag can take, on the side
     its record names, is one a drag can take: a drag starts at an unjoined
     writing port and ends at a reading port (§3.1), and the moved end of a
     join wire ends at a port of its own side (J-D33). Such a port is
     .bf-unjoined where no join reaches it and .bf-joined where joins reach
     a reading port, whose hover counts them, and .bf-admitted while it
     would take the drag in progress (J-D41, J-D42). data-port is the port's
     id in the graph JSON where the handle stands for one port of it. On a
     stage occurrence's card (`card`) the handle is the port's mark,
     .bf-mark, and .bf-open where no join reaches its field (AAS, L-D16). A
     port of a line lit with the selected box is .bf-lit, a writing port
     then filled in the accent (design pass 14 §1, rule 6). Its hover is
     the labels of the wires drawn at it in a stage's builders graph, one
     per line, a bundle's members among them (`p.hover`; §1, rule 5), and
     otherwise the port's own label (R-D49). */
  function portHandle(p, writes, down, gesture, card) {
    var record = p.wire ? null : gesture.enabled.get(p.id);
    var takes = !!record && record.side === (writes ? 'writing' : 'reading');
    var position = writes ? (down ? RF.Position.Bottom : RF.Position.Right) : (down ? RF.Position.Top : RF.Position.Left);
    var lit = !!gesture.lit && gesture.lit.has(p.handle);
    var classes = [!takes ? '' : (record.sources ? 'bf-joined' : 'bf-unjoined') +
      (gesture.source && takesDrag(gesture.source, record) ? ' bf-admitted' : ''),
      card ? 'bf-mark' + (p.open ? ' bf-open' : '') : '', lit ? 'bf-lit' : ''].filter(Boolean).join(' ') || undefined;
    return h(RF.Handle, { key: (writes ? 'o' : 'i') + p.handle, type: writes ? 'source' : 'target', id: p.handle, position: position,
      style: down ? { left: p.x } : { top: p.y }, isConnectable: takes, isConnectableStart: takes && writes, isConnectableEnd: takes,
      className: classes, 'data-port': p.wire ? undefined : p.id,
      title: (takes && record.title) || p.hover || p.full, 'aria-description': portDescription(p) });
  }

  /* The namespace of the stage occurrence whose layer's id is `nodeId`,
     `periods[h]/<key>`; null for any other node. */
  function occurrenceOf(nodeId) {
    if (!nodeId || nodeId.slice(-L.LAYER_ENDING.length) !== L.LAYER_ENDING) return null;
    var ns = nodeId.slice(0, -L.LAYER_ENDING.length);
    return L.OCCURRENCE.test(ns) ? ns : null;
  }

  /* Whether the cable port `port`, a record of `cablePorts`, of the stage
     occurrence at `ns` would take the cable drag in progress, `cable`
     (design pass 10 §7): a reading port of another occurrence of the
     writer's period, or of the next in time, periods[h − 1], for a drag
     from a branch port or of a reading end, and a writing port of another
     occurrence of the reader's period, or of the one before, periods[h +
     1], for a drag of a writing end. */
  function cableAdmits(cable, ns, port) {
    if (!cable || !ns) return false;
    var match = /^periods\[(\d+)\]\/(.+)$/.exec(ns);
    if (!match) return false;
    var h = Number(match[1]), key = match[2];
    if (cable.end === 'writing') {
      // a writing end lands in the reader's period or the one before, periods[h + 1]
      var reading = cable.record.reading;
      return port.side === 'writing' && ((h === reading.h && key !== reading.key) || h === reading.h + 1);
    }
    if (port.side !== 'reading') return false;
    // a reading end, or a new cable, lands in the writer's period or the next, periods[h − 1]
    var writer = cable.record ? cable.record.writing : { h: cable.h, key: cable.key };
    return (h === writer.h && key !== writer.key) || h === writer.h - 1;
  }

  /* A cable's port on a card (design pass 13 §1): .bf-cable-port, a
     transparent press target of 10 px whose mark, drawn by brand.css, is a
     6-px square centered on the card's edge, a socket, the closed hollow
     square, for the arrival tuple, .bf-cable-arrival, and a plug for a
     continuation branch, .bf-cable-branch, filled where a cable leaves by
     it, .bf-cable-joined, to a card or to a marker, the layout's port not
     `open` (the fix wave Q3a, item 1), and hollow with the accent's border
     where none does, .bf-cable-open; its record's `joined`, which a drag
     reads, holds where its cable joins another card; a reading port that
     stands at one point with the first one, .bf-cable-hidden, is not drawn
     and takes no pointer; the plug of a selected cable or of a lit cable
     of a selected card, .bf-lit, is filled in the accent (rule 7); and the
     port of an end of the selected cable that a drag can move,
     .bf-moving, takes the accent ring of a port that would take a drag,
     where K-D23 drew a square on the cable (the fix wave Q3a, item 5).
     It carries the port's id in data-port, a reading port's prefixed
     `in:` and a port of the card's own prefixed by its occurrence's
     namespace, its side in data-side, a writing port's branch in data-branch,
     the ids of the field ports it stands for in data-fields and those of
     them that no join reaches in data-unjoined. A drag starts at a writing port,
     from a joined branch as the move of its cable's reading end and from
     an unjoined branch as a new cable, and at a reading port that one
     cable reaches, as the move of that cable's reading end (design pass 10
     §7; `portStarts`); .bf-admitted marks a port that would take the drag
     in progress (`cableAdmits`). */
  function cablePort(p, writes, down, gesture, ns) {
    var side = writes ? 'writing' : 'reading';
    // the port's field ports by their ids, which `portStarts` compares with the frame's writing ports
    var record = { id: p.id, side: side, branch: p.branch || '', joined: !!p.joined,
      fields: (p.fields || []).map(function (f) { return f.id; }) };
    var starts = !p.hidden && !!gesture.portStarts && gesture.portStarts(ns, record);
    var admitted = !p.hidden && cableAdmits(gesture.cable, ns, record);
    var position = writes ? (down ? RF.Position.Bottom : RF.Position.Right) : (down ? RF.Position.Top : RF.Position.Left);
    // the port of a selected cable, or of a lit cable of a selected card, is lit with it (design pass 13 §1, rule 7)
    var lit = !!gesture.lit && gesture.lit.has(p.handle);
    // an end of the selected cable that a drag can move (the fix wave Q3a, item 5)
    var moving = !p.hidden && !!gesture.moving && gesture.moving.has(p.handle);
    var classes = ['bf-cable-port', writes ? 'bf-cable-branch' : 'bf-cable-arrival', p.open ? 'bf-cable-open' : 'bf-cable-joined',
      p.hidden ? 'bf-cable-hidden' : '', admitted ? 'bf-admitted' : '', lit ? 'bf-lit' : '', moving ? 'bf-moving' : ''].filter(Boolean).join(' ');
    return h(RF.Handle, { key: (writes ? 'o' : 'i') + p.handle, type: writes ? 'source' : 'target', id: p.handle, position: position,
      style: down ? { left: p.x } : { top: p.y }, isConnectable: !p.hidden, isConnectableStart: starts, isConnectableEnd: !p.hidden,
      // a reading port's data-port is prefixed `in:`, since the wire's port on the reader's card bears the id of
      // the writer's, so that the two are told apart
      // a port of the card's own, `arrival` or `branch:<label>`, is named after its occurrence, so that one element
      // of the region answers to each id
      className: classes, 'data-port': (writes ? '' : 'in:') + (p.wire ? p.id : ns + '/' + p.id), 'data-side': side,
      'data-branch': writes ? (p.branch || '') : undefined,
      // the ids of the field ports the port stands for, and of those among them that no join reaches
      'data-fields': record.fields.join(' '),
      'data-unjoined': (p.fields || []).filter(function (f) { return f.open; }).map(function (f) { return f.id; }).join(' '),
      title: p.wire ? p.full : undefined, 'aria-description': p.wire ? portDescription(p) : (writes ? (p.branch ? 'branch ' + p.branch : 'continuation') : 'arrival') });
  }

  /* The record of the stage occurrence whose layer has the namespace `ns`,
     `periods[h]/<key>`, among the frames a drag between frames can join
     (`framePorts`), where it holds an unjoined writing port, from which
     such a drag starts; null otherwise (unit K's decision K-D8). */
  function frameStart(gesture, ns) {
    var frame = ns ? gesture.frames.get(ns) : null;
    return frame && frame.writes.length ? frame : null;
  }

  /* The properties that make the element of the frame of the stage
     occurrence `ns` a drag's start: the class nopan, by which React Flow
     leaves the press to the frame, and the press's handler; and the class
     .bf-frame-target while the drag in progress would reach it (unit K's
     decision K-D8). */
  function frameProps(gesture, ns, className) {
    var starts = !!frameStart(gesture, ns) && !!gesture.pressFrame;
    var cls = className + (starts ? ' nopan' : '') + (ns && gesture.frameTarget === ns ? ' bf-frame-target' : '');
    return { className: cls, onPointerDown: starts ? function (event) { gesture.pressFrame(ns, event); } : undefined };
  }

  /* The label printed beside the port `p` of a closed stage occurrence's
     frame (unit K's decision K-D15), or of an open occurrence's own Inputs
     or Outputs (unit K, Task 21), in the face of the box's name,
     `face`: laid out to the right, a reading label at the left edge and a
     writing label at the right edge, each centered on its port's row; laid
     out downward, each centered on its port, the reading labels under the
     top edge and the writing labels over the bottom edge. */
  function frameLabel(p, writes, down, face) {
    // every place from the box's outer edge, where a border of one pixel stood inside it (the fix wave Q3a, item 3)
    var style = down ? { left: p.x + EDGE, transform: 'translateX(-50%)' } : { top: p.y - G.labelH / 2 + EDGE };
    if (down) style[writes ? 'bottom' : 'top'] = (writes ? G.padBottom : G.padTop) + EDGE;
    else style[writes ? 'right' : 'left'] = G.padX + EDGE;
    return h('span', { key: (writes ? 'l' : 'r') + p.handle, className: (writes ? 'bf-out' : 'bf-in') + ' bf-t-' + face, style: style }, p.text);
  }

  /* A box: a primitive operator, a field, a block, the graph's own Inputs or
     Outputs, or a closed layer. Its rows stand where flow-layout.js sized them.
     A label the layout cut at G.labelMax (`geom.cut`; AAS, L-D20) is
     .bf-cut: its symbol ends in an ellipsis before the method mark, which
     stands whole; the box's hover holds the label whole, and while the box
     is selected brand.css prints the label whole, centered on the box. A
     closed layer's box carries after its name the toggle that opens it,
     the Codicon `chevron-right`, as a closed card's chevron is (design pass
     8 §3; the delegated acceptance of unit M, D2). */
  function Box(props) {
    var d = props.data, g = d.geom, down = d.dir === 'DOWN', gesture = R.useContext(Gesture);
    var cls = 'bf-box bf-' + d.type + (props.selected ? ' selected' : '') + (d.closed ? ' bf-closed' : '') + (d.perch ? ' bf-perch-layer' : '') +
      (d.closed && isReached(gesture, d.namespace) ? ' bf-reached' : '') + (d.trellis ? ' bf-trellis' : '') + (g.period ? ' bf-period-closed' : '');
    // a closed stage occurrence is drawn as its card (AAS, L-D16)
    if (g.card) return card(props, gesture, { background: d.colors[d.level] || d.colors.period }, cls, 'bf-name', true);
    // a closed period is its frame closed (the fix wave Q3a, item 10)
    if (g.period) return closedPeriod(props, gesture, cls);
    // a closed stage occurrence's box is its frame (unit K's decision K-D8)
    var frame = frameProps(gesture, d.closed ? d.namespace : null, cls);
    var style = {};
    // the box's edge, an inset shadow in --bf-edge, which takes no layout width (the fix wave Q3a, item 3)
    if (d.closed) style.background = d.colors[d.level] || d.colors.period;
    else if (d.style === 'output' || d.style === 'refused') style['--bf-edge'] = d.colors[d.style];
    // the layout places a box's rows inside a border of one pixel, which the box no longer draws (item 3)
    var nameTop = g.nameTop + EDGE;
    var split = d.label.indexOf(' · !');
    var symbol = split < 0 ? d.label : d.label.slice(0, split);
    var mark = split < 0 ? '' : d.label.slice(split);
    var parts = [];
    g.ins.forEach(function (p) { parts.push(portHandle(p, false, down, gesture)); });
    parts.push(h('div', { key: 'n', className: 'bf-name bf-t-' + d.role + (g.cut ? ' bf-cut' : ''), style: { top: nameTop } },
      h('span', { className: 'bf-symbol' }, symbol), mark ? h('span', { className: 'bf-mark' }, mark) : null));
    if (d.sub) parts.push(h('div', { key: 's', className: 'bf-sub bf-t-port', style: { top: nameTop + G.labelH + 1 } }, d.sub));
    if (d.closed) parts.push(h('button', { key: 't', type: 'button', className: 'bf-toggle nodrag nopan', tabIndex: -1, title: 'open ' + d.label, 'aria-label': 'open ' + d.label,
      style: { left: G.padX + EDGE + measure(d.label, d.role) + 6, right: 'auto', top: nameTop + 1, width: G.toggle, height: G.toggle },
      onClick: function (e) { e.stopPropagation(); d.onToggle(d.namespace, e.currentTarget); } },
      codicon('chevron-right')));
    // every port's label on an open occurrence's own Inputs or Outputs (K-D15; unit K, Task 21); else the field's
    // label printed at an output port of the forward trellis graph (J-D47)
    if (g.face) {
      g.ins.forEach(function (p) { if (p.text) parts.push(frameLabel(p, false, down, g.face)); });
      g.outs.forEach(function (o) { if (o.text) parts.push(frameLabel(o, true, down, g.face)); });
    } else g.outs.forEach(function (o) {
      if (o.text) parts.push(h('span', { key: 'l' + o.handle, className: 'bf-out bf-t-port',
        style: down ? { left: o.x + EDGE, bottom: 6 + EDGE, transform: 'translateX(-50%)' } : { right: 9 + EDGE, top: o.y - 6 + EDGE } }, o.text));
    });
    g.outs.forEach(function (p) { parts.push(portHandle(p, true, down, gesture)); });
    return h('div', { className: frame.className, style: style, tabIndex: -1, role: 'group', onPointerDown: frame.onPointerDown,
      title: d.description || (g.cut ? d.label : undefined),
      'aria-label': d.closed ? 'closed layer ' + d.label : d.label }, parts);
  }

  /* A closed period of a trellis graph's root (the fix wave Q3a, item 10;
     B22), the period's frame closed, as `periodGeometry` lays it out: its
     name in the face of a frame's name, Code small, in ink-3 at (9, 5),
     and the toggle that opens it, the Codicon `chevron-right` in its
     target of G.toggle, its glyph centered at (w − 14, 14), as an open
     period's head draws them; its ports on its axis, and no arrowhead at
     them (`Wire`). */
  function closedPeriod(props, gesture, cls) {
    var d = props.data, g = d.geom, down = d.dir === 'DOWN', parts = [];
    var frame = frameProps(gesture, null, cls);
    g.ins.forEach(function (p) { parts.push(portHandle(p, false, down, gesture)); });
    parts.push(h('span', { key: 'n', className: 'bf-name bf-period-name bf-t-frame', style: { top: g.nameTop } },
      h('span', { className: 'bf-symbol' }, d.label)));
    parts.push(h('button', { key: 't', type: 'button', className: 'bf-toggle bf-period-toggle nodrag nopan', tabIndex: -1,
      title: 'open ' + d.label, 'aria-label': 'open ' + d.label,
      style: { width: G.toggle, height: G.toggle, top: G.periodHeader - G.toggle + EDGE },
      onClick: function (e) { e.stopPropagation(); d.onToggle(d.namespace, e.currentTarget); } },
      codicon('chevron-right')));
    g.outs.forEach(function (p) { parts.push(portHandle(p, true, down, gesture)); });
    return h('div', { className: frame.className, style: { background: d.colors[d.level] || d.colors.period }, tabIndex: -1, role: 'group',
      onPointerDown: frame.onPointerDown, 'aria-label': 'closed layer ' + d.label }, parts);
  }

  /* An open layer: a builder, a sub-builder, a perch, a period or a stage
     occurrence. Its head carries at its right the toggle that closes it,
     the Codicon `chevron-down`, as a compact card's chevron is (design pass
     8 §3; the delegated acceptance of unit M, D2), level with its name, the
     face of a frame's name in a trellis graph; a period's layer of the
     graph's root, .bf-period, has the head of G.periodHeader, on whose foot
     its toggle of G.toggle stands, over the layer's top edge, as design
     pass 8's mock draws a period's head (AAS, M-D15). A period's layer of a
     graph with `+ period` controls, whose
     index is `period`, carries the control `+ stage` between its name and
     its toggle, which, while the stage list can open, a reading that stands
     refused included (unit L, Task 14), opens the stage list for that
     period beside itself (unit K's decision K-D14; design pass 10 §7), and
     which is drawn pressed, aria-expanded, while that list is open; its
     right edge stands G.toggle
     + 11 px from the layer's right side in the flow's units, beside the
     toggle, and brand.css scales it about the middle of that edge, at the
     middle of the header row, to 24 px of height on the screen (AAS,
     L-D5). A stage occurrence's open layer
     is its frame (unit K's decision K-D8), drawn compact, as its card with
     the band of its builders, where the layout gives its geometry (`card`;
     AAS, L-D7 and L-D16); drawn in full, its name is in the face of a
     stage's name, `face` (design pass 10 §5). */
  function Layer(props) {
    var d = props.data, gesture = R.useContext(Gesture);
    var style = { background: d.colors[d.level] || d.colors.period };
    if (d.geom) {
      return card(props, gesture, style, 'bf-layer bf-compact' + (props.selected ? ' selected' : '') +
        (isReached(gesture, d.namespace) ? ' bf-reached' : ''), 'bf-layer-name', false);
    }
    // a period's layer of the graph's root has the head of G.periodHeader, on whose foot its toggle stands (M-D15)
    var toggleAt = { width: G.toggle, height: G.toggle };
    // from the layer's outer top, where a border of one pixel stood inside it (the fix wave Q3a, item 3)
    if (d.periodHead) toggleAt.top = G.periodHeader - G.toggle + EDGE;
    var parts = [
      // the layer's name in its face, a stage's name or a frame's name in a trellis graph (design pass 10 §5)
      h('span', { key: 'n', className: 'bf-layer-name bf-t-' + d.face }, d.label),
      h('button', { key: 't', type: 'button', className: 'bf-toggle nodrag nopan', tabIndex: -1, title: 'close ' + d.label, 'aria-label': 'close ' + d.label,
        style: toggleAt,
        onClick: function (e) { e.stopPropagation(); d.onToggle(d.namespace, e.currentTarget); } },
        codicon('chevron-down'))
    ];
    if (d.period != null) {
      // pressed while the stage list it opened is open (design pass 10 §7)
      // the Codicon `add` and the word `Stage` in Small (design pass 13 §2, rule 8)
      parts.push(h('button', { key: 's', type: 'button', className: 'bf-add-stage bf-t-small nodrag nopan', tabIndex: -1,
        title: ADD_STAGE, 'aria-label': ADD_STAGE, 'aria-disabled': gesture.listing ? undefined : 'true',
        'aria-expanded': gesture.listFor === d.period ? 'true' : 'false',
        style: { right: G.toggle + 11 + EDGE },
        onClick: function (e) { e.stopPropagation(); if (gesture.listing) d.onAddStage(d.period, e.currentTarget); } },
        codicon('add'), h('span', { className: 'bf-add-word' }, L.STAGE_WORDS)));
    }
    var frame = frameProps(gesture, d.namespace, 'bf-layer' + (d.perch ? ' bf-perch-layer' : '') + (d.periodHead ? ' bf-period' : '') +
      (props.selected ? ' selected' : '') + (isReached(gesture, d.namespace) ? ' bf-reached' : ''));
    return h('div', { className: frame.className, style: style, onPointerDown: frame.onPointerDown,
      tabIndex: -1, role: 'group', 'aria-label': 'layer ' + d.label }, parts);
  }

  /* The card of a stage occurrence of a trellis graph (design pass 13 §2;
     AAS, L-D16 and L-D25; design pass 7 §3), closed (`closed`, a box,
     .bf-box.bf-closed) or drawn compact (an open layer,
     .bf-layer.bf-compact), one drawing for both, as `frameGeometry` lays
     it out, .bf-card, on the step of its level (`style`) with the classes
     `classes`: the name from y = 3, the element of the class `name` in
     the face of a stage's name, which on a closed card holds the symbol
     .bf-symbol as a closed layer's box does, the whole name in the card's
     hover where the layout cut it (design pass 10 §5); the chevron, the
     Codicon `chevron-right` in a target of 24 px centered on the axis,
     whose click opens the occurrence with every builder open (`onOpen`);
     each row of printed text, a reading field's name .bf-in at the left,
     a writing field's .bf-out at the right, its branch word with a colon
     .bf-branch before it; and each cable's port on its edge (`cablePort`).
     The segments of the card's builders are nodes of their own inside it
     (`BuilderBox`). */
  function card(props, gesture, style, classes, name, closed) {
    var d = props.data, g = d.geom, down = d.dir === 'DOWN', parts = [];
    // the card draws its edge as an inset shadow, which takes no layout width, so that its children stand at the
    // places the layout measures from the card's outer edge at every zoom (the fix wave Q3a, item 3; A19)
    var words = 'open ' + d.label;
    g.ins.forEach(function (p) { parts.push(cablePort(p, false, down, gesture, d.namespace)); });
    // a closed card's name holds its symbol, as a closed layer's box does, in the face of a stage's name (design pass
    // 10 §5); the card's hover holds the whole name wherever the name overflows its box (`wholeName`; §2, rule 3)
    parts.push(h('span', { key: 'n', className: name + ' bf-t-stage', style: { top: g.nameTop }, ref: wholeName(d.label, g.cut) },
      closed ? h('span', { className: 'bf-symbol' }, d.label) : d.label));
    // the chevron, the Codicon `chevron-right` in a target of G.cardChevronTarget centered on the axis, whose
    // click opens the occurrence with every builder open (design pass 13 §2, rule 4)
    parts.push(h('button', { key: 't', type: 'button', className: 'bf-toggle bf-chevron nodrag nopan', tabIndex: -1,
      title: words, 'aria-label': words, style: { top: g.axis - G.cardChevronTarget / 2 },
      onClick: function (e) { e.stopPropagation(); d.onOpen(d.namespace, e.currentTarget); } },
      codicon('chevron-right')));
    g.texts.forEach(function (t, i) {
      var at = down ? { left: t.x, right: 'auto', top: t.y - G.frameRow / 2, transform: 'translateX(-50%)' }
        : { top: t.y - G.frameRow / 2 };
      var given = { key: 'x' + i, className: (t.writes ? 'bf-out' : 'bf-in') + ' bf-t-port', style: at };
      parts.push(t.branch ? h('span', given, h('span', { className: 'bf-branch' }, t.branch + ':'), ' ' + t.text) : h('span', given, t.text));
    });
    g.outs.forEach(function (p) { parts.push(cablePort(p, true, down, gesture, d.namespace)); });
    var frame = frameProps(gesture, d.namespace, classes + ' bf-card');
    return h('div', { className: frame.className, style: style, onPointerDown: frame.onPointerDown,
      tabIndex: -1, role: 'group', 'aria-label': (closed ? 'closed layer ' : 'layer ') + d.label }, parts);
  }

  /* The ref of a card's name that gives the card, the name's parent, the
     whole name `label` as its hover wherever the name overflows its box,
     its scroll width past its client width, and not only where the layout
     cut it (`cut`), and takes that hover away where the name fits again
     (the fix wave Q3a, item 3; §2, rule 3; B16, C18). */
  function wholeName(label, cut) {
    return function (element) {
      if (!element || !element.parentElement) return;
      var holder = element.parentElement;
      if (cut || element.scrollWidth > element.clientWidth) holder.setAttribute('title', label);
      else if (holder.getAttribute('title') === label) holder.removeAttribute('title');
    };
  }

  /* The segment of a builder in the strip of a compact stage occurrence's
     card (AAS, L-D7 and L-D25; design pass 7 §3), .bf-builder, coded by the
     pair of perches its signature joins as Python's record gives it, never
     by its id: `data-pair`, the pair, `arvl,dcsn`, or `policy`; its ground
     .bf-pair-cntn, orange, for the builder that joins the continuation
     perch, `cntn_to_dcsn` backward and `dcsn_to_cntn` forward,
     .bf-pair-arvl, mint, for the one that joins the arrival perch,
     `dcsn_to_arvl` and `arvl_to_dcsn`, the perch read from the pair as the
     perch besides the decision perch, or .bf-pair-policy, a tint of ice,
     2 px of the card's fill between two segments (design pass 14 §9,
     which amends design pass 13 §2, rule 5; S-D14). The whole segment is its toggle,
     `.bf-builder-toggle`, whose click opens the builder in place as a
     closed layer's toggle does, the occurrence then drawn in full (§2.1);
     it prints no text, and the segment's hover names the pair in words and
     the id, `arrival to decision · arvl_to_dcsn`, or the id alone where
     the words are the id, `policy` (unit L's final judgment, §6 item 9).
     In the band of the unfolded card (`unfolded`), the selected card's, it
     prints the pair's signs, `≺∼`, and the builder's id, the box's label,
     .bf-name, on one line, cut where the segment is narrower. A builder
     Python gives no record of is drawn on the builder's step of §5.3, with
     no signs, its hover its id. */
  function BuilderBox(props) {
    var d = props.data, record = d.record;
    // the perch the pair joins besides the decision perch, `cntn` or `arvl`, read from the record's pair, `dcsn,cntn`
    // (design pass 14 §9; S-D14)
    var perches = record && record.pair !== L.POLICY ? String(record.pair).split(',') : [];
    var tint = !record ? '' : record.pair === L.POLICY ? ' bf-pair-policy'
      : perches.indexOf('cntn') >= 0 ? ' bf-pair-cntn' : perches.indexOf('arvl') >= 0 ? ' bf-pair-arvl' : '';
    var hover = record && record.words !== d.label ? record.words + ' · ' + d.label : d.label;
    // the signs stand before the id where the builder has signs; a builder with none, the policy builder,
    // prints its id alone, so that the segment's gap is not taken (design pass 13 §2, rule 7)
    var printed = d.unfolded ? [
      record && record.signs ? h('span', { key: 's', className: 'bf-builder-signs', 'aria-hidden': true }, record.signs) : null,
      h('span', { key: 'n', className: 'bf-builder-id bf-name' }, d.label)] : null;
    return h('div', { className: 'bf-builder' + tint + (props.selected ? ' selected' : ''),
      tabIndex: -1, role: 'group', 'data-pair': record ? record.pair : undefined, title: hover,
      'aria-label': 'closed layer ' + d.label },
      h('button', { type: 'button', className: 'bf-toggle bf-builder-toggle nodrag nopan', tabIndex: -1,
        title: hover, 'aria-label': 'open ' + d.label,
        onClick: function (e) { e.stopPropagation(); d.onToggle(d.namespace, e.currentTarget); } }, printed));
  }

  /* A boundary marker of a trellis graph's root (design pass 13 §1, rule
     6; design pass 10 §6), where data enter or leave the drawn range: its
     node's box, .bf-marker, is the mark's box and is not painted; the mark
     is its first child, .bf-marker-paint, a name of its own (N-I276), of
     the box's size: an 8-px circle filled in the port ink, .bf-boundary-
     mark, for a `start` or an `end` node, a terminal marker, the one round
     mark; and for an `outside` node, a connection to an occurrence outside
     the drawn periods, the far card's port, .bf-outside-mark, a socket
     where the stub ends at an outside reader and a plug, .bf-outside-
     writer, where it begins at an outside writer. Its label, the
     exporter's, `starting data μ≺` or `periods[3]/keeper_cons`, a sibling
     of the mark, stands beside it on its far side in the face of a frame's
     name, Code small, .bf-boundary-label, outside the box, where the
     layout kept its room (`markerGeometry`), so that the label stands on
     the region's ground and not on the mark's fill; an `outside` marker's
     hover names the drawn periods, `Outside periods 0–2`. Its one port
     stands on the mark's face toward the card. */
  function Marker(props) {
    var d = props.data, g = d.geom, down = d.dir === 'DOWN', outside = g.kind === 'outside';
    var label = { position: 'absolute', width: g.labelAt.width, height: g.labelAt.height, lineHeight: g.labelAt.height + 'px',
      left: g.labelAt.x - g.mark.x, top: g.labelAt.y - g.mark.y, textAlign: down ? 'center' : (g.labelAt.x < g.mark.x ? 'right' : 'left') };
    var paint = outside ? 'bf-outside-mark' + (g.outs.length ? ' bf-outside-writer' : '') : 'bf-boundary-mark';
    var parts = [h('div', { key: 'm', className: 'bf-marker-paint ' + paint })];
    g.ins.forEach(function (p) {
      parts.push(h(RF.Handle, { key: 'i' + p.handle, type: 'target', id: p.handle, position: down ? RF.Position.Top : RF.Position.Left,
        style: down ? { left: p.x - g.mark.x } : { top: p.y - g.mark.y }, isConnectable: false, className: 'bf-marker-port',
        'data-port': p.id, title: p.full }));
    });
    g.outs.forEach(function (p) {
      parts.push(h(RF.Handle, { key: 'o' + p.handle, type: 'source', id: p.handle, position: down ? RF.Position.Bottom : RF.Position.Right,
        style: down ? { left: p.x - g.mark.x } : { top: p.y - g.mark.y }, isConnectable: false, className: 'bf-marker-port',
        'data-port': p.id, title: p.full }));
    });
    parts.push(h('span', { key: 'l', className: 'bf-boundary-label bf-t-frame', style: label }, d.label));
    return h('div', { className: 'bf-marker' + (props.selected ? ' selected' : ''),
      tabIndex: -1, role: 'group', 'aria-label': d.label, 'data-kind': g.kind, 'data-target': d.target || undefined,
      title: outside ? d.hover : undefined }, parts);
  }

  // The bus mark of a cable that carries more than one wire (design pass 13 §1, rule 5): the length of its slash,
  // the distance along the cable's first run from the plug's center, on the card's edge, to the slash's middle,
  // the plug's half and G.slashAlong from its outer face, the room between the slash's end and the count's left
  // edge and above the slash's upper end, and the count's baseline below the cable's line where the count stands
  // under the cable
  var BUS = { length: G.slash, along: G.portMark / 2 + G.slashAlong, gap: G.countGap, below: G.countBelow };

  /* The bus mark on the route `points`, its writing end first (design
     pass 13 §1, rule 5, the schematic's mark of a line that carries
     several signals): `slash`, the path of a segment BUS.length px long at
     45 degrees to the route's first run, turned so that across a run that
     goes to the right it rises to the right, its middle on the run
     BUS.along px from the plug's center, 8 px from the plug's outer face;
     and `at`, the place of the count's baseline, its left edge BUS.gap right
     of the slash's end and its baseline BUS.gap above the slash's upper
     end, or, with `below`, for a cable in the lower half of a stack of
     plugs, BUS.below under the cable's line, so that no count stands
     between two cables of one stack (A2). The layout gives every first run
     at least G.firstRun, so the mark has no other place. Null where the
     route has no run. */
  function busMark(points, below) {
    var start = points[0], next = null;
    for (var i = 1; i < points.length && !next; i++) {
      if (points[i].x !== start.x || points[i].y !== start.y) next = points[i];
    }
    if (!next) return null;
    var dx = next.x - start.x, dy = next.y - start.y, length = Math.hypot(dx, dy);
    var ux = dx / length, uy = dy / length;
    var cx = start.x + ux * BUS.along, cy = start.y + uy * BUS.along, half = BUS.length / 2;
    // the run's direction turned by 45 degrees toward the screen's top
    var vx = Math.SQRT1_2 * (ux + uy), vy = Math.SQRT1_2 * (uy - ux);
    var one = { x: cx - vx * half, y: cy - vy * half }, other = { x: cx + vx * half, y: cy + vy * half };
    var upper = other.y < one.y || (other.y === one.y && other.x > one.x) ? other : one;
    var right = Math.max(one.x, other.x) + BUS.gap;
    return { slash: 'M' + one.x + ',' + one.y + 'L' + other.x + ',' + other.y,
             at: below ? { x: right, y: cy + BUS.below } : { x: right, y: upper.y - BUS.gap } };
  }

  /* A wire follows ELK's route, or a path at right angles between its ports.
     `parts` are the routes it draws: one for a wire; two for a wire of a
     bundle, whose shared route the bundle draws; and one for a bundle,
     which draws no arrow (unit K's decision K-D5). A wire ends in an
     arrowhead at its reader, 6.5 px long and wide with its point half a
     pixel past the route's end, and prints its label over its line, as
     design pass 8's mock draws them (AAS, M-D15). A cable that carries
     more than one wire draws their count at its writing end, the bus mark
     (`busMark`; design pass 12 §3), and no label, its branch standing
     first in its title (the fix wave Q3a, item 4, which amends Q-D17); a
     bundle of a stage's builders graph draws the same mark at its plug and
     keeps its arrowhead (design pass 14 §1, rule 3; S-D3); a wire that
     leaves or reaches a closed period's box draws no arrowhead (item
     10). */
  function Wire(props) {
    var d = props.data || {}, path, at = null;
    var routes = (d.parts || []).filter(function (points) { return points && points.length > 1; });
    var last = routes.length ? routes[routes.length - 1] : null;
    if (last || d.paint) {
      path = (d.paint || routes).map(function (points) {
        return 'M' + points.map(function (p) { return p.x + ',' + p.y; }).join('L');
      }).join('');
      if (d.join) at = d.joinAt;        // where the layout kept room for the join's label
    } else {
      var step = RF.getSmoothStepPath({ sourceX: props.sourceX, sourceY: props.sourceY, sourcePosition: props.sourcePosition,
        targetX: props.targetX, targetY: props.targetY, targetPosition: props.targetPosition, borderRadius: 0 });
      path = step[0];
      if (d.join) at = { x: step[1], y: step[2] };
    }
    var lit = d.lit ? ' bf-lit' : '', parts = [];
    if (path) {
      var cls = d.cable ? ' bf-cable-outer bf-cable' +
        (d.bundle || (d.pairBundle && d.count > 1 && !d.branch) ? ' bf-cable-bundle' : '') +
        (d.dashed ? ' bf-cable-dashed' : '') : '';
      parts.push(h('path', { key: 'p', d: path, fill: 'none', className: 'react-flow__edge-path' + cls + lit }));
      parts.push(h('path', { key: 'i', d: path, fill: 'none', stroke: 'transparent', strokeWidth: d.cable ? 12 : 9,
        className: d.members ? 'bf-shared-hit' : undefined,
        style: d.initialTrunk ? { pointerEvents: 'stroke' } : undefined }, h('title', null, d.title)));
    }
    // the count of the wires a cable, or a bundle of a stage's builders graph, carries where it carries more than
    // one, at its plug (design pass 13 §1, rule 5; design pass 14 §1, rule 3; S-D3): the slash across its first run
    // in the port ink (brand.css, .bf-cable-bus) and the count at the Mark step (.bf-cable-count), above the line,
    // or below it for a plug in the lower half of its box's stack of plugs, `below`; the piece the wires of a pair
    // of periods share has no plug and draws none, and a wire that is neither a cable nor a bundle, as a measure
    // wire of an open occurrence that counts its route's pairs, draws none; a lit cable's slash keeps the port
    // ink, a selected cable's alone taking the accent (the fix wave Q3a, item 7)
    var bus = last && !d.pair && d.count > 1 && (d.cable || d.pairBundle) ? busMark(routes[0], !!d.below) : null;
    if (bus) {
      parts.push(h('path', { key: 'b', d: bus.slash, fill: 'none', className: 'bf-cable-bus' }));
      parts.push(h('text', { key: 'bc', x: bus.at.x, y: bus.at.y, className: 'bf-cable-count' }, String(d.count)));
    }
    // a cable runs from its plug into its socket and draws no arrowhead (design pass 11 §1a), and a wire at a closed
    // period's box none (the fix wave Q3a, item 10; design pass 13 §1, rule 4). A branch of a shared route
    // ends at the junction, where there is no reading port.
    if (last && !d.shared && !d.sharedInput && !d.cable && !d.closed) {
      var end = last[last.length - 1];
      var before = last.slice(0, -1).reverse().find(function (point) { return point.x !== end.x || point.y !== end.y; });
      // a wire's arrowhead is 6.5 px long and wide (M-D15)
      var head = 'M0.5,0L-6,-3.25L-6,3.25Z';
      if (before && !d.dashed) parts.push(h('path', { key: 'a', d: head,
        transform: 'translate(' + end.x + ',' + end.y + ') rotate(' + Math.atan2(end.y - before.y, end.x - before.x) * 180 / Math.PI + ')',
        className: 'bf-arrow' + lit }));
    }
    // a cable draws no label: its branch stands first in its title and in Details, and its count at its plug in
    // every state (the fix wave Q3a, item 4, which amends Q-D17 and design pass 13 §1, rule 7)
    if (d.join && at && !d.cable) {
      // the join's label (K-D4) in the wire's own drawing, so that it stands over the layer the wire runs in: centered
      // where ELK kept its room, in STIX Two Math, upright, ringed in the canvas's color where it crosses a line
      // (brand.css, .bf-join), beside its wire as design pass 8's mock sets it (AAS, M-D15): its baseline 11 px under
      // a run that lies below either end of the wire, as the lower of two branches does, and 5 px over any other
      // level run; on an upright run, centered on the wire; a cable's label 5 px over its longest horizontal run
      var start = last ? routes[0][0] : { x: props.sourceX, y: props.sourceY };
      var finish = last ? last[last.length - 1] : { x: props.targetX, y: props.targetY };
      var upright = routes.some(function (points) { return onUpright(points, at); });
      var baseline = upright ? at.y + 3 : at.y > Math.min(start.y, finish.y) + 0.5 ? at.y + 11 : at.y - 5;
      parts.push(h('text', { key: 'jt', x: at.x, y: baseline, textAnchor: 'middle',
        className: 'bf-join' + (d.lit ? ' lit' : '') }, d.join));
    }
    // the ends of the selected join wire that a drag can move (unit K's decision K-D23): a wire's square, and a
    // cable's unpainted anchor, whose ports take the accent ring instead (the fix wave Q3a, item 5)
    var movable = props.selected && d.record ? d.record.movable || [] : [];
    if (movable.indexOf('writing') >= 0) parts.push(wireEnd('writing', props.sourceX, props.sourceY, props.sourcePosition, d.cable));
    if (movable.indexOf('reading') >= 0) parts.push(wireEnd('reading', props.targetX, props.targetY, props.targetPosition, d.cable));
    return h(R.Fragment, null, parts);
  }

  /* Whether the point `at` lies on an upright part of the route `points`,
     to a pixel. */
  function onUpright(points, at) {
    for (var i = 1; i < points.length; i++) {
      var a = points[i - 1], b = points[i];
      if (Math.abs(a.x - b.x) < 0.5 && Math.abs(at.x - a.x) < 1 &&
          at.y >= Math.min(a.y, b.y) - 1 && at.y <= Math.max(a.y, b.y) + 1) return true;
    }
    return false;
  }

  /* The end `end`, writing or reading, of a selected join wire that a drag
     can move, at the port at (x, y) facing `position` (unit K's decision
     K-D23): a square of WIRE_END px, .bf-wire-end, whose center stands
     RECONNECT / 2 px out from the port on the side the port faces, inside
     the circle of radius RECONNECT, centered RECONNECT px out, in which
     React Flow takes the press of the end's drag. The square carries the
     side the port faces, data-faces, and the port's place as the origin
     about which brand.css scales it, and the circle that follows it, by the
     inverse of the view's scale, so that both keep those sizes on the
     screen at every scale (unit K's decision K-D27). On a cable, `cable`,
     the square is .bf-wire-anchor, of the same place and size and not
     painted, so that the circle keeps its place and its size and a drag
     its press while the cable draws no square over its slash and its
     count, its ports taking the accent ring (the fix wave Q3a, item 5,
     which amends K-D23's squares for cables). */
  function wireEnd(end, x, y, position, cable) {
    var out = RECONNECT / 2;
    var cx = position === RF.Position.Left ? x - out : position === RF.Position.Right ? x + out : x;
    var cy = position === RF.Position.Top ? y - out : position === RF.Position.Bottom ? y + out : y;
    return h('rect', { key: 'end-' + end, className: cable ? 'bf-wire-anchor' : 'bf-wire-end', 'data-end': end, 'data-faces': position,
      x: cx - WIRE_END / 2, y: cy - WIRE_END / 2, width: WIRE_END, height: WIRE_END,
      style: { transformOrigin: x + 'px ' + y + 'px' } });
  }

  /* The control that adds a period (§3.6): the Codicon `add` and the word
     `Period` in Small (design pass 13 §2, rule 8; unit K's decision
     K-D14), with its name, `add a period`, as its hover text and spoken
     name. While a drop can be made, a click sends the event dropped with
     no item, as Enter on it in the region's order does; an item dragged
     or sent to it marks it. */
  function PeriodControl(props) {
    var d = props.data, gesture = R.useContext(Gesture);
    return h('button', { type: 'button', tabIndex: -1, title: d.name, 'aria-label': d.name, 'data-target': d.target,
      className: 'bf-add-period bf-t-small nodrag nopan' + (gesture.control === d.target ? ' bf-reached' : ''),
      'aria-disabled': gesture.live ? undefined : 'true',
      onClick: function (event) { event.stopPropagation(); if (gesture.live) gesture.send(null, d.target); } },
      codicon('add'), h('span', { className: 'bf-add-word' }, L.PERIOD_WORDS));
  }

  /* The Codicon `name`, the element the page's stylesheet of Codicons
     draws at 16 px in the color of its text (design pass 8 §3), hidden
     from assistive technology, since the element that holds it carries
     the name or the words. */
  function codicon(name) {
    return h('i', { key: 'icon ' + name, className: 'codicon codicon-' + name, 'aria-hidden': 'true' });
  }

  /* The control at the right end of a list's head that closes the list,
     as Escape does (`onClose`): the button holding the Codicon `close`,
     with CLOSE as its hover text and spoken name, reached by Tab (unit K's
     decision K-D24; AAS, L-D8; design pass 8 §3). */
  function closeControl(onClose) {
    return h('button', { key: 'close', type: 'button', className: 'bf-list-close', title: CLOSE, 'aria-label': CLOSE,
      onClick: function () { onClose(); } }, codicon('close'));
  }

  /* The head of a list over the graph, the forms' head (design pass 4
     §§2 and 4): one line 28 px high over a hairline, the Codicon `glyph`,
     the element `named`, the list's name in .bf-list-name, then `context`,
     an element or null, and the control that closes the list at its right
     end (`closeControl`). */
  function listHead(glyph, named, context, onClose) {
    return h('div', { key: 'head', className: 'bf-list-head' }, codicon(glyph), named, context,
      closeControl(onClose));
  }

  /* The text of the hover of an item of the stage list (AAS, L-D9): its
     model's title and, after ` · `, the parameters its calibration gives,
     `The durables model: … · R, R_H, δ`; the title alone where it gives
     none, and null for an item with neither. */
  function itemHover(item) {
    var parts = [item.title, item.calibration.join(', ')].filter(Boolean);
    return parts.length ? parts.join(' · ') : null;
  }

  /* The place of the list `list` opened by the button `anchor`, or by a
     drop on the port `anchor`, within the
     element `region` that holds the list (design pass 10 §7): its top-left
     at the button's bottom-left; flipped above the button where it would
     pass the region's bottom edge and the room above is the larger, and
     shifted left where it would pass the region's right edge; at most
     LIST_SHARE of the region's height, and no higher than the room on the
     side it stands, so that the whole list stands within the region. With
     no anchor in the page the list stands at the region's top-left. The
     place is written into the list's style, `top`, `left` and
     `max-height`, in px from the region's top-left corner. */
  var LIST_SHARE = 0.6;
  function placeList(list, anchor, region) {
    if (!list || !region) return;
    var room = region.getBoundingClientRect();
    var at = anchor && anchor.isConnected ? anchor.getBoundingClientRect() : null;
    var below = at ? room.bottom - at.bottom : room.height, above = at ? at.top - room.top : 0;
    list.style.maxHeight = Math.floor(room.height * LIST_SHARE) + 'px';
    var height = list.getBoundingClientRect().height, width = list.getBoundingClientRect().width;
    var flipped = at !== null && height > below && above > below;
    var fits = Math.max(0, Math.floor(flipped ? above : below));
    if (at !== null && height > fits) {
      list.style.maxHeight = Math.min(fits, Math.floor(room.height * LIST_SHARE)) + 'px';
      height = list.getBoundingClientRect().height;
    }
    var top = at === null ? 0 : flipped ? at.top - room.top - height : at.bottom - room.top;
    var left = at === null ? 0 : at.left - room.left;
    list.style.top = Math.round(Math.max(0, Math.min(top, room.height - height))) + 'px';
    list.style.left = Math.round(Math.max(0, Math.min(left, room.width - width))) + 'px';
  }

  /* The element in `region` of the handle a drop ended at, `drop`, {node,
     handle}, by React Flow's attributes of the handle, data-nodeid and
     data-handleid; null where the region no longer draws it. */
  function dropElement(region, drop) {
    if (!region || !drop) return null;
    var handles = region.querySelectorAll('.react-flow__handle');
    for (var i = 0; i < handles.length; i++) {
      if (handles[i].dataset.nodeid === drop.node && handles[i].dataset.handleid === drop.handle) return handles[i];
    }
    return null;
  }

  /* The stage list of §3.5, over the graph: its head (`listHead`; design
     pass 4 §4), the Codicon of the stage list, the name STAGES in .bf-list-name, in a
     period's list the period as its context, and the control `×` at its
     right end (`closeControl`); under it the heading Python gives,
     .bf-stage-heading, where it gives one; then one item for
     each stage of the folder, each template and each stage of the library,
     each on one line (AAS, L-D9): its key after the icon of its kind
     (KIND_ICONS; AAS, L-D15), .bf-stage-model, the name of the folder of its
     model, and its model's title and the parameters its calibration gives
     as its hover (`itemHover`); the first item of each section Python
     names, `this folder's stages`, `templates` or `library`, after a
     heading line .bf-stage-section that prints the section's name (AAS,
     L-D6, L-D9), and, last where Python gives
     it, the item of the kind `folder`, .bf-stage-folder, which prints its
     words, `from a folder…`, alone and is sent or dropped as any item is,
     Python then opening the form that copies a stage folder of the disk
     (unit K's decision K-D26). An item is dragged by the browser's own
     drag-and-drop, or chosen with Enter for the keyboard's
     route (`onPick`); ArrowDown and ArrowUp move among the items, passing
     over the sections' heading lines, and Escape
     anywhere in the list closes it (`onClose`), as `×` does. The first item
     takes the focus when the list opens. Opened by a period's `+ stage`,
     the head's context is the period's name, .bf-stage-period,
     `periods[1]`, an item whose stage the period's list holds (`listed`)
     is dimmed with the word `listed` at the line's end, and a click or
     Enter on any other item sends it to that period (`onSend`), as a drop
     there does (unit K's decision K-D14).
     Opened by `stages`, a click or Enter on the item `from a folder…`
     sends it with no period (`onFolder`), Python then opening the form
     with a select of the period (AAS, L-D5). The list's element is held in
     `holder`, by which the region tells a click inside the list from a
     click outside it (K-D24), and `place` writes its place beside the
     button that opened it before each paint (`placeList`; design pass 10
     §7). The item last chosen from the list, `chosen`, `<kind> <id>`, is
     marked .bf-chosen with aria-current. */
  function StageList(props) {
    var stages = props.stages, period = props.period, first = useRef(null);
    // the list's place beside the button that opened it, before it is painted (design pass 10 §7)
    R.useLayoutEffect(function () { if (props.holder.current) props.place(props.holder.current); });
    useEffect(function () { if (first.current) first.current.focus({ preventScroll: true }); }, []);
    // A click or Enter on the item `item`: sent to the list's period; for
    // the item `from a folder…` of the list the button `stages` opens, sent
    // with no period (L-D5); else shown on the keyboard's route.
    function choose(item) {
      if (period !== null) props.onSend(item);
      else if (item.kind === 'folder') props.onFolder(item);
      else props.onPick(item);
    }
    function keyDown(event, item) {
      var next = event.currentTarget;
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        // the next item in the key's direction, past a section's heading line
        do {
          next = event.key === 'ArrowDown' ? next.nextElementSibling : next.previousElementSibling;
        } while (next && !next.classList.contains('bf-stage-item'));
        if (next) next.focus();
      } else if (event.key === 'Enter') choose(item);
      else return;
      event.preventDefault();
      event.stopPropagation();
    }
    function escape(event) {
      if (event.key !== 'Escape') return;
      event.preventDefault();
      event.stopPropagation();
      props.onClose();
    }
    // the head: the Codicon of the stage list, the name STAGES and, in a
    // period's list, the period as its context (design pass 4 §4)
    var parts = [listHead(LIST_ICONS.stages, h('span', { key: 'name', className: 'bf-list-name', role: 'heading', 'aria-level': 2 }, STAGES),
      period === null ? null : h('span', { key: 'period', className: 'bf-stage-period' }, 'periods[' + period + ']'),
      props.onClose)];
    if (stages.heading) {
      parts.push(h('div', { key: 'heading', className: 'bf-stage-heading', role: 'heading', 'aria-level': 3 }, stages.heading));
    }
    var section = null;
    stages.items.forEach(function (item, i) {
      // the section's heading line before its first item (L-D6)
      if (item.section && item.section !== section) {
        parts.push(h('div', { key: 'section ' + item.section, className: 'bf-stage-section',
          role: 'heading', 'aria-level': 3 }, item.section));
      }
      section = item.section || null;
      var listed = period !== null && props.listed(item, period);
      // the item `from a folder…`, which prints its words alone, Python
      // giving it no folder name and no title (unit K's decision K-D26)
      var folder = item.kind === 'folder';
      // the item last chosen from the list (design pass 10 §7)
      var chosen = props.chosen === item.kind + ' ' + item.id;
      parts.push(h('div', { key: item.kind + ' ' + item.id, ref: i === 0 ? first : undefined,
        className: 'bf-stage-item' + (listed ? ' bf-listed' : '') + (folder ? ' bf-stage-folder' : '') +
          (chosen ? ' bf-chosen' : ''),
        'aria-disabled': listed ? 'true' : undefined, 'aria-current': chosen ? 'true' : undefined,
        title: itemHover(item),
        role: 'button', tabIndex: 0, draggable: true, 'data-item': item.id, 'data-kind': item.kind,
        onClick: period === null && !folder ? undefined : function () { choose(item); },
        onDragStart: function (event) {
          event.dataTransfer.setData(DRAG_TYPE, item.id);
          event.dataTransfer.effectAllowed = 'copy';
          props.onDrag(item);
        },
        onDragEnd: function () { props.onDrag(null); },
        onKeyDown: function (event) { keyDown(event, item); } },
        h('span', { className: 'bf-stage-key' }, codicon(KIND_ICONS[item.kind]), item.key),
        item.model_folder ? h('span', { className: 'bf-stage-model' }, item.model_folder) : null,
        listed ? h('span', { className: 'bf-stage-listed' }, 'listed') : null));
    });
    return h('div', { ref: props.holder, className: 'bf-stage-list' + (props.dragging ? ' bf-dragging' : ''), role: 'group',
      'aria-label': 'stages', onKeyDown: escape }, parts);
  }

  /* The text of a port in the select of a pairing list: the field's name,
     its declared set after ` : ` where Python gives one, as the stage file
     writes it (unit K's decision K-D25), and where joins reach the port the
     count of its sources as its hover writes it (J-D42),
     `a_bq : ℝ₊ · 2 sources`. */
  function portText(record) {
    var at = record.title ? record.title.indexOf(' · ') : -1;
    return record.field + (record.set ? ' : ' + record.set : '') + (at < 0 ? '' : record.title.slice(at));
  }

  /* The list that a drag between the frames of two stage occurrences opens
     (unit K's decision K-D8), and the list that the move of an end of a
     join wire of several field pairs opens (K-D23): its head (`listHead`;
     design pass 4 §4), the Codicon of a join, the name JOIN and as its context
     `head`, `periods[2]/port → periods[2]/cons`, in .bf-pair-head, cut with
     an ellipsis and whole in its hover; one row for each record of `rows`,
     {id, field, set, proposed, replaced, lost}, .bf-pair-row with data-port, the
     row's id, holding a tick, the row's field and a select of the ports of
     `options`, records of the ports a drag can take, `—` choosing none,
     the field of the writer's side .bf-pair-from and of the reader's
     .bf-pair-to, the select standing on the side `end` names, the
     reader's for `reading` and the writer's for `writing`; a select of
     the writer's ports offers no port another row has chosen, since a
     continuation field joins one arrival field (J-D41), so that no two
     rows name one writing port (unit K's final judgment, §6 item 12),
     while a select of the reader's ports offers each, since an arrival
     field may take several sources; and the button
     `Join`. The row's field is printed with its declared set,
     `m_next : ℝ₊₊`, the set in .bf-pair-set, and each port of the select
     likewise (`portText`), so that the author reads the two sets before
     the tick; the list compares no sets (unit K's decision K-D25). A row
     whose `proposed` names a port has that port chosen and is ticked, a
     proposal the author may untick; Python proposes a reading port that
     joins reach on a move and never on a drag between two frames (J-D41;
     unit L, Task 19). Choosing a port ticks its row, and every tick acts:
     a tick on a row with no port chosen puts the focus on its select
     (unit L, Task 19; defect 13 of the UX simulation). Each row with
     `lost`, the entry its field pair writes now, `a_s: a_bq`, ticked with a
     port chosen, is named before the foot in one line .bf-pair-loses,
     `<leaves> loses <lost>, …`, `leaves` the stage occurrence the moved end
     leaves, whole in its hover, so that the author reads which stage loses
     which entries before `Join`. The foot holds CANCEL and `Join`. `Join`,
     pressed while a row is ticked with a port chosen and no ticked row
     waits for one, or the primary modifier with Enter, gives `onJoin` the
     ticked rows' pairs, each {sourceHandle, targetHandle}, the row's id
     and the port chosen in the order of the writer's and the reader's
     side, with `replaced` where the row has one; its hover names what it
     waits for while it does not act. Escape closes the list (`onClose`),
     as CANCEL and the control `×` at the right of its head do
     (`closeControl`; unit K's decision K-D24). The list keeps every key from
     the graph's region, and its first control that acts, a tick or else a
     select, takes the focus when it opens. A list opened by a drop on a
     port, the cable's list and the list of the piece the wires of a pair of
     periods share, stands beside that port, its place written by `place`
     before each paint (`placeList`; design pass 10 §7); the list of a drag
     between two frames, which no port opens, has no `place` and stands at
     the region's top-left (K-D8). */
  function PairList(props) {
    var given = props.rows, reads = props.end === 'reading', list = useRef(null);
    // the list's place beside the port it was dropped on, before it is painted (design pass 10 §7)
    R.useLayoutEffect(function () { if (props.place && list.current) props.place(list.current); });
    var _rows = useState(function () {
      return given.map(function (row) { return { to: row.proposed || '', ticked: !!row.proposed }; });
    }), rows = _rows[0], setRows = _rows[1];
    useEffect(function () {
      var control = list.current && list.current.querySelector('.bf-pair-tick, .bf-pair-row select');
      if (control) control.focus({ preventScroll: true });
    }, []);
    function change(i, row) {
      setRows(rows.map(function (was, j) { return j === i ? Object.assign({}, was, row) : was; }));
    }
    var ticked = given.map(function (row, i) {
      if (!rows[i].ticked || !rows[i].to) return null;
      var pair = reads ? { sourceHandle: row.id, targetHandle: rows[i].to } : { sourceHandle: rows[i].to, targetHandle: row.id };
      // the port the pair leaves: in a cable's list, the old port of the chosen continuation field, for a reading
      // end, or of the row's arrival field, for a writing end (design pass 10 §7)
      var replaced = props.cable ? (props.replacedBy || {})[props.replacedOf === 'source' ? rows[i].to : row.id] : row.replaced;
      if (replaced) pair.replaced = replaced;
      return pair;
    }).filter(Boolean);
    // the rows ticked with no port chosen, for which `Join` waits
    var waiting = rows.filter(function (row) { return row.ticked && !row.to; }).length;
    var acts = ticked.length > 0 && !waiting;
    // the entries the ticked rows take from the stage occurrence the moved end leaves; a cable's move takes every
    // entry of its route (design pass 10 §7)
    var lost = props.cable ? (props.lost || []) : given.filter(function (row, i) { return row.lost && rows[i].ticked && rows[i].to; })
      .map(function (row) { return row.lost; });
    function keyDown(event) {
      // the primary modifier, Command on macOS and Control elsewhere, as
      // window.vue's keys of a form read it (unit L's final judgment, §6
      // item 12)
      var mac = navigator.platform.indexOf('Mac') === 0;
      var primary = mac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey;
      if (event.key === 'Escape') { event.preventDefault(); props.onClose(); }
      // the primary modifier with Enter presses `Join` (design pass 4 §2a)
      else if (event.key === 'Enter' && primary) {
        event.preventDefault();
        if (acts) props.onJoin(ticked);
      }
      event.stopPropagation();
    }
    // A tick on a row with no port chosen puts the focus on the row's
    // select (unit L, Task 19).
    function tick(i, checked) {
      change(i, { ticked: checked });
      var select = list.current && list.current.querySelectorAll('.bf-pair-row select')[i];
      if (checked && !rows[i].to && select) select.focus({ preventScroll: true });
    }
    // the head: the Codicon of a join, the name JOIN and the two stage
    // occurrences as its context, whole in its hover (design pass 4 §4)
    var parts = [listHead(LIST_ICONS.join, h('span', { key: 'name', className: 'bf-list-name' }, JOIN),
      h('span', { key: 'context', className: 'bf-pair-head', role: 'heading', 'aria-level': 2, title: props.head }, props.head),
      props.onClose)];
    given.forEach(function (row, i) {
      var state = rows[i];
      // the writing ports the other rows have chosen, which this row's
      // select of writing ports does not offer unless it holds one
      var taken = new Set(reads ? [] : rows.filter(function (other, j) { return j !== i && other.to; })
        .map(function (other) { return other.to; }));
      var offered = props.options.filter(function (record) {
        return record.id === state.to || !taken.has(record.id);
      });
      var options = [h('option', { key: '', value: '' }, '—')].concat(offered.map(function (record) {
        return h('option', { key: record.id, value: record.id }, portText(record));
      }));
      var choice = h('select', { key: 'choice', className: reads ? 'bf-pair-to' : 'bf-pair-from', value: state.to,
        'aria-label': reads ? row.field + ' →' : '→ ' + row.field,
        onChange: function (event) { change(i, { to: event.target.value, ticked: !!event.target.value }); } }, options);
      var field = h('span', { key: 'field', className: reads ? 'bf-pair-from' : 'bf-pair-to' }, row.field,
        row.set ? h('span', { className: 'bf-pair-set' }, ' : ' + row.set) : null);
      parts.push(h('div', { key: i + ' ' + row.id, className: 'bf-pair-row', 'data-port': row.id },
        h('input', { key: 'tick', type: 'checkbox', className: 'bf-pair-tick', checked: state.ticked,
          'aria-label': row.field, onChange: function (event) { tick(i, event.target.checked); } }),
        reads ? field : choice,
        h('span', { key: 'arrow', className: 'bf-pair-arrow', 'aria-hidden': 'true' }, '→'),
        reads ? choice : field));
    });
    // the count of the destination's fields paired, in a cable's list (design pass 10 §7)
    if (props.cable) {
      var counted = ticked.length + ' of ' + given.length + (given.length === 1 ? ' field' : ' fields') + ' paired';
      parts.push(h('div', { key: 'count', className: 'bf-pair-count' }, counted));
    }
    // the line that names the entries the move takes from the stage
    // occurrence it leaves, before `Join` (unit L, Task 19)
    if (lost.length && props.leaves) {
      var loses = props.leaves + ' loses ' + lost.join(', ');
      parts.push(h('div', { key: 'loses', className: 'bf-pair-loses', title: loses }, loses));
    }
    // the foot: CANCEL, which closes the list as `×` does, then the primary
    // `Join` (design pass 4 §§2 and 4)
    parts.push(h('div', { key: 'foot', className: 'bf-list-foot' },
      h('button', { key: 'cancel', type: 'button', className: 'bf-pair-cancel', onClick: function () { props.onClose(); } }, CANCEL),
      h('button', { key: 'join', type: 'button', className: 'bf-pair-join', disabled: !acts,
        title: acts ? undefined : waiting ? 'choose a field' : 'tick a field',
        onClick: function () { if (acts) props.onJoin(ticked); } }, JOIN)));
    return h('div', { ref: list, className: 'bf-pair-list', role: 'group', 'aria-label': 'join', onKeyDown: keyDown }, parts);
  }

  var nodeTypes = { box: Box, layer: Layer, add: PeriodControl, builder: BuilderBox, marker: Marker }, edgeTypes = { wire: Wire };

  /* The ports a drag can take, `enabled`, by the stage occurrence that
     holds them: for each namespace `periods[h]/<key>`, {ns, h, key, writes,
     reads}, the records of its writing and of its reading ports in their
     order (unit K's decision K-D8). */
  function framePorts(enabled) {
    var frames = new Map();
    enabled.forEach(function (record) {
      var ns = 'periods[' + record.h + ']/' + record.key;
      if (!frames.has(ns)) frames.set(ns, { ns: ns, h: record.h, key: record.key, writes: [], reads: [], fields: [] });
      var frame = frames.get(ns);
      // the continuation fields of each branch, joined or not, which a cable's list offers (design pass 10 §7),
      // and the unjoined ones, from which a drag between frames starts (K-D8)
      if (record.side === 'writing') {
        frame.fields.push(record);
        if (!record.joined) frame.writes.push(record);
      } else frame.reads.push(record);
    });
    return frames;
  }

  /* Whether a drag between frames joins the frame `writer` to the frame
     `reader`, each a record of `framePorts`: the writer holds an unjoined
     writing port, and the reader, another stage occurrence of the writer's
     period or one of the next, periods[h − 1], a reading port (§3.1, as
     J-D41 amends it; unit K's decision K-D8). */
  function framesJoin(writer, reader) {
    return !!writer && !!reader && writer.writes.length > 0 && reader.reads.length > 0 &&
      ((reader.h === writer.h && reader.key !== writer.key) || reader.h === writer.h - 1);
  }

  /* The named namespaces and every namespace that contains them. */
  function opening(layers) {
    var out = new Set();
    (layers || []).forEach(function (ns) { L.chain(ns).forEach(function (a) { out.add(a); }); });
    return out;
  }

  /* The id of the terminal period's layer where every layer of the graph's
     root is a period's, as in a trellis graph: the layer placed in `place`
     of the period of least h, `periods[0]` unless a restriction leaves it
     out; null for any other graph (unit K's decision K-D6). */
  function terminalLayer(m, place) {
    var roots = Object.keys(m.layers).filter(function (ns) { return !m.layers[ns].parent; });
    if (!roots.length || !roots.every(function (ns) { return PERIOD.test(ns); })) return null;
    var least = null;
    roots.forEach(function (ns) {
      var h = Number(PERIOD.exec(ns)[1]), id = m.layers[ns].id;
      if (place[id] && (least === null || h < least.h)) least = { h: h, id: id };
    });
    return least ? least.id : null;
  }

  /* The namespace of the one period a graph shows, `periods[40]`, where the
     graph's root holds one layer and that layer is a period's, as a trellis
     graph restricted to one period does; null for any other graph (unit L,
     Task 22). */
  function periodAlone(m) {
    var roots = Object.keys(m.layers).filter(function (ns) { return !m.layers[ns].parent; });
    return roots.length === 1 && PERIOD.test(roots[0]) ? roots[0] : null;
  }

  /* The exported style's name, with neutral styling for an unknown style (§5.3). */
  function styleOf(node, graph, styles) {
    if (graph.nodes.length === 1 && node.id === graph.id + ':refused') return 'refused';
    return ['output', 'node'].find(function (name) {
      var expected = (styles || {})[name];
      return expected && Object.keys(node.style).length === Object.keys(expected).length &&
        Object.keys(expected).every(function (key) { return node.style[key] === expected[key]; });
    }) || 'neutral';
  }

  /* The level whose three exported colors equal the layer's configuration (§5.3). */
  function levelOf(layer, styles) {
    var config = layer.config, levels = (styles || {}).layers || {};
    var colors = [config.backgroundColor, config.borderColor, config.textColor];
    return Object.keys(levels).find(function (level) {
      return levels[level].length === colors.length && levels[level].every(function (color, i) { return color === colors[i]; });
    }) || 'neutral';
  }

  /* The graph JSON order, with each layer and its toggle before its first
     node, and a closed layer in place of its contents (§2.4); each `+
     period` control of `controls`, {id, later}, stands before the layer of
     the period after it in time, in the order of the periods (§3.6);
     where `stages` holds, the control `+ stage` of an open period's layer
     stands after its toggle (unit K's decision K-D14). Use the drawing to
     include compact builder segments and skip layers with no visible box. */
  function traversal(m, open, controls, stages, drawing) {
    var order = [], placed = new Set(), before = {};
    (controls || []).forEach(function (c) { (before[c.later] = before[c.later] || []).push(c.id); });
    m.order.forEach(function (id) {
      var above = L.chain(m.nodes[id].namespace);
      for (var i = 0; i < above.length; i++) {
        var layer = above[i] + L.LAYER_ENDING;
        if (!drawing.place[layer] && !drawing.builders[layer]) return;
        if (!placed.has(layer)) {
          placed.add(layer);
          (before[above[i]] || []).forEach(function (box) { order.push({ box: box }); });
          order.push({ box: layer }, { toggle: layer });
          if (stages && open.has(above[i]) && PERIOD.test(above[i])) order.push({ stage: layer });
        }
      }
      if (drawing.place[id]) order.push({ box: id });
    });
    return order;
  }

  function Pane(props) {
    var p = props.p, colors = props.colors, rf = RF.useReactFlow();
    var graph = useMemo(function () {
      return ((p.collection && p.collection.graphs) || []).filter(function (g) { return g.id === p.graph; })[0] || null;
    }, [p.collection, p.graph]);
    var m = useMemo(function () { return graph ? L.model(graph) : null; }, [graph]);
    var kept = useRef(null);
    if (!kept.current || kept.current.scope !== p.scope) {
      kept.current = { scope: p.scope, sets: {}, seen: {}, chosen: {}, bundles: {}, adds: {}, alone: {}, opens: {} };
    }
    // The `+ period` controls laid out: those Python gives, else the last it
    // gave for this graph of this scope, so that a graph whose input differs
    // from the text read keeps its layout and its controls do not act.
    if (p.adds) kept.current.adds[p.graph] = p.adds;
    var laidAdds = p.adds || kept.current.adds[p.graph] || null;
    var addsKey = laidAdds ? JSON.stringify(laidAdds) : '';
    // the key of the recipe's order of the stages the layout drawn ranks by (the fix wave Q3a, item 2)
    var orderKey = p.stage_order ? p.stage_order.join(' ') : '';
    // Whether a drop can be made: Python gives the stage list, the controls
    // and the record of the reading only while the inputs hold the text read.
    var live = !!(p.stages && p.adds && p.reading);
    // Whether the graph shown is the backward graph of the trellis, whose
    // graph id is its direction (`backward` or `forward`), where Backspace
    // or Delete sends the occurrence or the cable selected with no reading
    // (N-D12, N-I192); in a forward graph that is not live the keys send
    // nothing (N-I273).
    var backward = !!graph && graph.id === 'backward';
    // Whether the stage list opens and an item can be sent to a period:
    // Python also gives the list and the record, with no controls, while a
    // reading stands refused and the last graph constructed is drawn (unit
    // L, Task 14).
    var listing = !!(p.stages && p.reading);
    var _tick = useState(0), tick = _tick[0], setTick = _tick[1];
    var _choice = useState(0), setChoice = _choice[1];
    var appliedSelect = useRef(), appliedPlace = useRef();
    // Whether a pointer press within the region stands, from its pointerdown
    // to its pointerup anywhere, a key press or the end of its task (AAS,
    // M-D16): the press's own focus arrives between the two, and a focus a
    // click's or a key's handler gives, as the stage list's close does, after.
    var pressed = useRef(false);
    useEffect(function () {
      function release() { pressed.current = false; }
      document.addEventListener('pointerup', release, true);
      document.addEventListener('pointercancel', release, true);
      return function () {
        document.removeEventListener('pointerup', release, true);
        document.removeEventListener('pointercancel', release, true);
      };
    }, []);
    var pendingToggle = useRef(null), focusFrame = useRef(null);
    var _inside = useState(false), inside = _inside[0], setInside = _inside[1];
    function openSet() {
      var state = kept.current;
      var given = Array.isArray(p.layers) ? p.layers : (p.layers && p.layers[p.graph]);
      var defaults = opening(given || (m ? Object.keys(m.layers) : []));
      if (!state.sets[p.graph]) {
        state.sets[p.graph] = defaults;
        state.seen[p.graph] = new Set();
      }
      Object.keys(m ? m.layers : {}).forEach(function (ns) {
        if (!state.seen[p.graph].has(ns)) {
          state.seen[p.graph].add(ns);
          if (defaults.has(ns)) state.sets[p.graph].add(ns);
        }
      });
      return state.sets[p.graph];
    }
    var toggle = useCallback(function (ns, outgoing) {
      var open = new Set(openSet());
      if (open.has(ns)) open.delete(ns); else open.add(ns);
      pendingToggle.current = { scope: p.scope, graph: p.graph, namespace: ns,
        item: { toggle: ns + L.LAYER_ENDING }, open: open.has(ns), outgoing: outgoing };
      kept.current.sets[p.graph] = open;
      setTick(function (n) { return n + 1; });
    }, [p.scope, p.graph, m]);
    /* The opening of the layers `names`, each with every layer above it,
       as one change, the focus then going to the toggle of the layer `ns`
       (design pass 13 §2, rule 4): a card's chevron opens its occurrence
       with every builder open (`openWhole`), and a segment of its strip
       opens that builder in place, its occurrence with it (`openBuilder`);
       the open occurrence's layer closes back to the card by its own
       chevron (`toggle`). */
    var openLayers = useCallback(function (names, ns, outgoing) {
      var open = new Set(openSet());
      names.forEach(function (name) { L.chain(name).forEach(function (above) { open.add(above); }); });
      pendingToggle.current = { scope: p.scope, graph: p.graph, namespace: ns,
        item: { toggle: ns + L.LAYER_ENDING }, open: true, outgoing: outgoing };
      kept.current.sets[p.graph] = open;
      setTick(function (n) { return n + 1; });
    }, [p.scope, p.graph, m]);
    var openWhole = useCallback(function (ns, outgoing) {
      var inside = Object.keys(m.layers).filter(function (k) { return m.layers[k].parent === ns; });
      openLayers([ns].concat(inside), ns, outgoing);
    }, [openLayers, m]);
    var openBuilder = useCallback(function (ns, outgoing) { openLayers([ns], ns, outgoing); }, [openLayers]);
    // the page's direction, one for every graph of every stage and of the trellis in every tab, which `turn` turns
    // and the browser's storage keeps (design pass 14 §2; S-D5); every region mounted lays its graph out again at
    // a turn
    var flows = pageLayout.direction;
    useEffect(function () {
      function turned() { setTick(function (n) { return n + 1; }); }
      pageLayout.listeners.push(turned);
      return function () { pageLayout.listeners.splice(pageLayout.listeners.indexOf(turned), 1); };
    }, []);
    var _nodes = RF.useNodesState([]), nodes = _nodes[0], setNodes = _nodes[1], onNodesChange = _nodes[2];
    var _edges = RF.useEdgesState([]), edges = _edges[0], setEdges = _edges[1], onEdgesChange = _edges[2];
    var host = useRef(null), fit = useRef(null), parents = useRef({});
    // The key and geometry of the layout drawn.
    var shown = useRef(null);
    // The key, restored box and viewport of the opening last applied, or null.
    var lastOpening = useRef(null);
    // The opening a layout is to apply, {at}, the box it centers or null, from
    // the layout that asks for it until begin applies it; null where none is due.
    var openingDue = useRef(null);
    // The card the layout drawn last unfolded, by its namespace, or null, by which the view pans to a card once,
    // after the layout that unfolds it (the fix wave Q3a, item 8).
    var lastUnfold = useRef(null);
    // The key of the layout drawn and of its opening: the scope, the graph and the direction.
    var layoutKey = p.scope + '|' + p.graph + '|' + flows;
    var selection = kept.current.chosen[p.graph] || null;
    // The bundle of an ordered pair of stage occurrences selected, by its id,
    // or null (AAS, L-D25).
    var bundleChosen = kept.current.bundles[p.graph] || null;
    var _layout = useState(null), laid = _layout[0], setLaid = _layout[1];
    /* The card that prints every field's name (AAS, L-D19 as L-D25 amends
       it; design pass 7 §3), which the layout gives a row for each field:
       the card of the stage occurrence selected, which grows while it is
       selected, so that the drags and the pairing list see every field;
       null for none. No scale prints a joined field's name. */
    // Whether the view's scale is below SMALL, where no count is drawn and no card unfolds (design pass 13 §1,
    // rule 3), set where the scale crosses it.
    var _small = useState(false), small = _small[0], setSmall = _small[1];
    var unfold = useMemo(function () {
      if (!m || small) return null;
      var ns = selection && selection.slice(-L.LAYER_ENDING.length) === L.LAYER_ENDING ? selection.slice(0, -L.LAYER_ENDING.length) : null;
      return ns && L.OCCURRENCE.test(ns) ? [ns] : null;
    }, [m, selection, small]);
    var unfoldKey = unfold ? unfold[0] : '';

    // The drag of §3.2, read from React Flow's store: the region's unjoined
    // ports by id, empty where the property is absent; whether a drag is in
    // progress; the id of its writing port; and the period whose layer
    // stands under the pointer, found among the places of the period layers
    // laid out (`periodPlaces`).
    var store = RF.useStoreApi();
    var enabled = useMemo(function () {
      var map = new Map();
      (p.unjoined || []).forEach(function (port) { map.set(port.id, port); });
      return map;
    }, [p.unjoined]);
    var periodPlaces = useRef([]);
    var dragging = RF.useStore(function (s) { return s.connection.inProgress; });
    var from = RF.useStore(function (s) {
      var f = s.connection.inProgress ? s.connection.fromHandle : null;
      return f ? portOf(f.nodeId, f.id, f.type) : null;
    });
    var over = RF.useStore(function (s) {
      var c = s.connection;
      if (!c.inProgress || !c.pointer) return null;
      var t = s.transform, x = (c.pointer.x - t[0]) / t[2], y = (c.pointer.y - t[1]) / t[2];
      var found = periodPlaces.current.find(function (at) {
        return x >= at.ax && x <= at.ax + at.width && y >= at.ay && y <= at.ay + at.height;
      });
      return found ? found.h : null;
    });
    var source = from ? enabled.get(from) || null : null;

    // The view's scale, held on the region as --bf-scale, by which brand.css
    // keeps a port a drag can take at least 8 px across on the screen (unit
    // K's decision K-D9); and beside it --bf-line, the least width of whole
    // device pixels in the flow's own pixels at or above 1 px on the screen,
    // max(1px, ⌈devicePixelRatio / scale⌉ / devicePixelRatio px), at which
    // every edge and every hollow mark's border is drawn (the fix wave Q3a,
    // item 3; E8); both are set where the scale changes, with no render.
    useEffect(function () {
      var last = null;
      function scale(s) {
        var zoom = s.transform[2];
        if (zoom === last || !host.current) return;
        last = zoom;
        host.current.style.setProperty('--bf-scale', String(zoom));
        var ratio = window.devicePixelRatio || 1;
        host.current.style.setProperty('--bf-line', Math.max(1, Math.ceil(ratio / zoom - 1e-9) / ratio) + 'px');
        // below SMALL the region is .bf-small, where brand.css draws no count, and no card unfolds
        host.current.classList.toggle('bf-small', zoom < SMALL);
        setSmall(zoom < SMALL);
      }
      scale(store.getState());
      return store.subscribe(scale);
    }, []);

    // The port a drag can take that the pointer's press, drop and hover
    // reach, marked data-nearest: of the ports whose squares hold the
    // pointer, the one whose center is nearest it, or none; brand.css lets
    // no other such port take the pointer (unit K's decision K-D9; row
    // K-I165). It is found again at each move of the pointer over the
    // region, before React Flow's own listener for the move reads the
    // element under the pointer.
    var nearest = useRef(null), nearestEnd = useRef(null);
    function markNearest(port) {
      if (port === nearest.current) return;
      if (nearest.current) nearest.current.removeAttribute('data-nearest');
      if (port) port.setAttribute('data-nearest', '');
      nearest.current = port;
    }
    function pointerOverPorts(event) {
      var x = event.clientX, y = event.clientY, found = null, least = Infinity;
      host.current.querySelectorAll('.react-flow__handle.bf-unjoined, .react-flow__handle.bf-joined, .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)').forEach(function (port) {
        var at = port.getBoundingClientRect();
        if (x < at.left || x > at.right || y < at.top || y > at.bottom) return;
        var dx = x - (at.left + at.right) / 2, dy = y - (at.top + at.bottom) / 2;
        if (dx * dx + dy * dy < least) { least = dx * dx + dy * dy; found = port; }
      });
      markNearest(found);
      // On a short selected arrow the two press circles overlap. The
      // visible square nearest the pointer determines the end it moves.
      var end = null, distance = Infinity;
      host.current.querySelectorAll('.bf-join-wire.selected .react-flow__edgeupdater').forEach(function (circle) {
        var box = circle.getBoundingClientRect();
        var dx = x - (box.left + box.right) / 2, dy = y - (box.top + box.bottom) / 2;
        if (dx * dx + dy * dy > box.width * box.width / 4) return;
        var side = circle.classList.contains('react-flow__edgeupdater-source') ? 'writing' : 'reading';
        var square = circle.parentElement.querySelector('.bf-wire-end[data-end="' + side + '"], .bf-wire-anchor[data-end="' + side + '"]');
        if (!square) return;
        box = square.getBoundingClientRect();
        dx = x - (box.left + box.right) / 2; dy = y - (box.top + box.bottom) / 2;
        if (dx * dx + dy * dy < distance) { distance = dx * dx + dy * dy; end = circle; }
      });
      if (nearestEnd.current !== end) {
        if (nearestEnd.current) nearestEnd.current.removeAttribute('data-nearest');
        if (end) end.setAttribute('data-nearest', '');
        nearestEnd.current = end;
      }
    }

    // The drag between two frames (unit K's decision K-D8): the ports of
    // each stage occurrence (`framePorts`); the places of the frames laid
    // out, each {ns, ax, ay, width, height}; the press on a frame, {from, x,
    // y, at, moved}, from its press to its release; the line drawn while the
    // drag lasts, {from, to} in the flow's coordinates; the frame the drag
    // would reach; and the list its release opens, {writer, reader}, the two
    // namespaces, or the list the move of an end of a join wire of several
    // field pairs opens, {record, end, at}, the wire's record, the end moved
    // and the namespace of the stage occurrence it was dropped on (unit K's
    // decision K-D23). `frameState` holds what the pointer's listeners read.
    var frames = useMemo(function () { return framePorts(enabled); }, [enabled]);
    var occurrencePlaces = useRef([]);
    // The cables' ports of the cards drawn, by handle (`cablePorts` of the
    // layout effect), and the cable drag in progress, {end, record, h, key,
    // branch, port} (design pass 10 §7): from a joined branch port or from
    // a reading port one cable reaches, the move of that cable's reading
    // end, `record` the cable's; from an unjoined branch port, a new cable
    // from the branch `branch` of the occurrence at (h, key), `record` null.
    var cablePorts = useRef({});
    // the drawn socket of each hidden reading port of a card, the first port of its arrival tuple, by handle
    var portAlias = useRef({});
    var cableDrag = useRef(null);
    var _cableState = useState(null), cableState = _cableState[0], setCableState = _cableState[1];
    var framePress = useRef(null);
    var _frameLine = useState(null), frameLine = _frameLine[0], setFrameLine = _frameLine[1];
    var _frameTarget = useState(null), frameTarget = _frameTarget[0], setFrameTarget = _frameTarget[1];
    var _pairing = useState(null), pairing = _pairing[0], setPairing = _pairing[1];
    var frameState = useRef(null);
    frameState.current = { frames: frames, rf: rf };
    // The press on a frame, and the end of the drag it begins, as functions
    // made once, so that the pointer's listeners on the window are the same
    // functions from the press to the release.
    var frameDrag = useRef(null);
    if (!frameDrag.current) frameDrag.current = (function () {
      // the namespace of the frame laid out under the pointer, or null
      function frameAt(event) {
        var at = frameState.current.rf.screenToFlowPosition({ x: event.clientX, y: event.clientY });
        var found = occurrencePlaces.current.find(function (o) {
          return at.x >= o.ax && at.x <= o.ax + o.width && at.y >= o.ay && at.y <= o.ay + o.height;
        });
        return found ? found.ns : null;
      }
      function end() {
        framePress.current = null;
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', release);
        window.removeEventListener('pointercancel', end);
        setFrameLine(null);
        setFrameTarget(null);
      }
      // the drag begins once the pointer has moved 4 px from the press
      function move(event) {
        var press = framePress.current;
        if (!press) return;
        if (!press.moved && Math.abs(event.clientX - press.x) + Math.abs(event.clientY - press.y) < 4) return;
        press.moved = true;
        var state = frameState.current, ns = frameAt(event);
        setFrameLine({ from: press.at, to: state.rf.screenToFlowPosition({ x: event.clientX, y: event.clientY }) });
        var target = framesJoin(state.frames.get(press.from), state.frames.get(ns)) ? ns : null;
        setFrameTarget(function (was) { return was === target ? was : target; });
      }
      // a release on a frame the drag joins opens the list, in place of the stage list
      function release(event) {
        var press = framePress.current;
        end();
        if (!press || !press.moved) return;
        var state = frameState.current, ns = frameAt(event);
        if (!framesJoin(state.frames.get(press.from), state.frames.get(ns))) return;
        setListOpen(false);
        setSending(null);
        setPairing({ writer: press.from, reader: ns });
      }
      // a press of the main button on a frame that starts a drag, not on a port or a button of it
      function press(ns, event) {
        var state = frameState.current, frame = state.frames.get(ns);
        if (event.button !== 0 || framePress.current || !frame || !frame.writes.length ||
            event.target.closest('.react-flow__handle, button')) return;
        framePress.current = { from: ns, x: event.clientX, y: event.clientY, moved: false,
          at: state.rf.screenToFlowPosition({ x: event.clientX, y: event.clientY }) };
        window.addEventListener('pointermove', move);
        window.addEventListener('pointerup', release);
        window.addEventListener('pointercancel', end);
      }
      return { press: press, end: end };
    })();
    // A change of the ports or of the reading ends a drag between frames
    // and closes its list (§3.3), as the region's removal does.
    useEffect(function () {
      frameDrag.current.end();
      setPairing(null);
    }, [enabled, p.reading]);
    useEffect(function () { return function () { frameDrag.current.end(); }; }, []);

    // The join wires of J-D33: their records by the key of the wire
    // (`wireKey`); the id of the edge of the join wire selected, and its
    // record; and the end of a join wire whose drag is in progress,
    // {record, end}.
    var joinsByKey = useMemo(function () {
      var map = new Map();
      (p.joins || []).forEach(function (j) { map.set(wireKey(j.source, j.sourceHandle, j.target, j.targetHandle), j); });
      return map;
    }, [p.joins]);
    var _joinChosen = useState(null), joinChosen = _joinChosen[0], setJoinChosen = _joinChosen[1];
    var _sharedChoice = useState(null), sharedChoice = _sharedChoice[0], setSharedChoice = _sharedChoice[1];
    var sharedList = useRef(null), sharedPress = useRef(null);
    var chosenRecord = useRef(null);
    var moving = useRef(null);
    /* What the layout splits into its wires (AAS, L-D25; design pass 7
       §3): the bundles of the stage occurrence selected, the bundle
       selected, and the bundle, where the layout drawn holds one, of the
       pair whose join wire is selected within a period, so that the wire
       selected and its gestures stand once its card's selection ends. The
       layout names a pair's bundle by the occurrences its wires leave and
       reach, the writer before the reader in the forward graph and the
       reader before the writer in the backward graph, whose wires carry the
       values from the reading occurrence to the writing one; a record names
       the route's writer as `from` in both (unit N, Task 7, N-I192). */
    var joinRecord = chosenRecord.current;
    var joined = null;
    if (joinChosen && joinRecord && !joinRecord.between && joinRecord.writing.key && laid && laid.pairs) {
      joined = [L.PAIR_BUNDLE + joinRecord.from + '|' + joinRecord.to, L.PAIR_BUNDLE + joinRecord.to + '|' + joinRecord.from]
        .find(function (id) { return laid.pairs.has(id); }) || null;
    }
    var split = [unfold ? unfold[0] : null, bundleChosen, joined].filter(Boolean);
    var splitKey = split.join(' ');
    // The selection of the bundle `id`, or of none, which a later click on a
    // box or on the graph's ground, or Escape, ends.
    function chooseBundle(id) {
      if ((kept.current.bundles[p.graph] || null) === id) return;
      kept.current.bundles[p.graph] = id;
      setChoice(function (n) { return n + 1; });
    }

    // The drops of §3.2: whether the list is open; the item the pointer
    // drags, held at once in `dragged` and after the drag's start in
    // `dragItem`, which hides the list; the item the keyboard sends and the
    // index of the candidate it stands on, {item, index}; the place an item
    // would reach, {h} for a period's layer or {control} for a control's
    // target; and the places of the controls laid out. The list opened by a
    // period's `+ stage` is that period's, `listPeriod` its index, null for
    // the list the button `stages` opens (unit K's decision K-D14).
    var _open = useState(false), listOpen = _open[0], setListOpen = _open[1];
    var _listPeriod = useState(null), listPeriod = _listPeriod[0], setListPeriod = _listPeriod[1];
    var _dragItem = useState(null), dragItem = _dragItem[0], setDragItem = _dragItem[1];
    var dragged = useRef(null);
    var _sending = useState(null), sending = _sending[0], setSending = _sending[1];
    var _dropAt = useState(null), dropAt = _dropAt[0], setDropAt = _dropAt[1];
    var addPlaces = useRef([]);
    var latest = useRef(p);
    latest.current = p;
    // The event of a drop (J-D17): an item, or none for Enter on a control,
    // and the target, a period's layer id or a control's target, or none for
    // the item `from a folder…` chosen in the list the button `stages` opens
    // (L-D5).
    var sendDrop = useCallback(function (item, target) {
      var q = latest.current;
      q.host.dispatchEvent(new CustomEvent('dropped', { bubbles: true, detail: {
        item: item ? item.id : null, kind: item ? item.kind : null, target: target, reading: q.reading } }));
    }, []);
    // The periods a period's list writes with it, which a drop there reaches.
    function entryOf(period) {
      var entries = (p.stages && p.stages.entries) || [];
      return entries.find(function (periods) { return periods.indexOf(period) >= 0; }) || [period];
    }
    // Whether the period's list already holds the folder stage `item`, which
    // a drop there then writes nothing for (§3.5).
    function listedIn(item, period) {
      return item.kind === 'stage' && (item.periods_listed || []).indexOf(period) >= 0;
    }
    // The button that opened the stage list, a period's `+ stage` or the
    // button `stages`, beside which the list stands (design pass 10 §7); and
    // the item last chosen from the list, `<kind> <id>`, which the list
    // marks when it opens again.
    var listAnchor = useRef(null);
    var _lastChosen = useState(null), lastChosen = _lastChosen[0], setLastChosen = _lastChosen[1];
    // A period's `+ stage`, the element `button`: the stage list opens for
    // the period `period` beside it (unit K's decision K-D14; design pass 10 §7).
    var openForPeriod = useCallback(function (period, button) {
      listAnchor.current = button || null;
      setSending(null);
      setPairing(null);
      setListPeriod(period);
      setListOpen(true);
    }, []);
    // A click or Enter on the item `item` of a period's list: the list
    // closes, the graph takes the focus, and the item is sent to the period
    // as a drop on its layer sends it; an item the period lists sends nothing.
    function sendToPeriod(item) {
      if (listPeriod === null || listedIn(item, listPeriod)) return;
      if (host.current) host.current.focus({ preventScroll: true });
      setListOpen(false);
      setLastChosen(item.kind + ' ' + item.id);
      sendDrop(item, 'periods[' + listPeriod + ']' + L.LAYER_ENDING);
    }
    // A click or Enter on the item `from a folder…` of the list the button
    // `stages` opens, which names no period: the list closes, the graph
    // takes the focus, and the item is sent with no target, Python then
    // opening the form with a select of the period (AAS, L-D5).
    function sendFolder(item) {
      if (host.current) host.current.focus({ preventScroll: true });
      setListOpen(false);
      setLastChosen(item.kind + ' ' + item.id);
      sendDrop(item, null);
    }

    // The line reaches the periods of the writing port's connectors list
    // while the pointer stands in its period, and the periods its pair's
    // inter-period mapping reaches while the pointer stands in the next
    // (ruling J-P7); an item reaches the periods of its period's list. A
    // frame starts a drag while the region holds the record of a reading
    // (unit K's decision K-D8).
    // The ports of the selected cable and of the lit cables of the selected card, by handle, which brand.css
    // draws in the accent (design pass 13 §1, rule 7): a hidden reading port lights the drawn socket of its tuple.
    var litPorts = useMemo(function () {
      var found = new Set();
      edges.forEach(function (e) {
        if (!e.selected && !(e.data && e.data.lit)) return;
        ((e.data && e.data.handles) || []).forEach(function (pair) {
          found.add(pair[0]);
          found.add(portAlias.current[pair[1]] || pair[1]);
        });
      });
      return found;
    }, [edges]);
    // The ports of the ends of the selected cable that a drag can move, by handle, which brand.css rings in the
    // accent, where K-D23 drew a square on the cable (the fix wave Q3a, item 5): its plug for a writing end and its
    // drawn socket for a reading end.
    var movingPorts = useMemo(function () {
      var found = new Set();
      edges.forEach(function (e) {
        if (!e.selected || !e.data || !e.data.cable || !e.data.record) return;
        var movable = e.data.record.movable || [];
        (e.data.handles || []).forEach(function (pair) {
          if (movable.indexOf('writing') >= 0) found.add(pair[0]);
          if (movable.indexOf('reading') >= 0) found.add(portAlias.current[pair[1]] || pair[1]);
        });
      });
      return found;
    }, [edges]);
    var gesture = useMemo(function () {
      var periods = !source || over === null ? null
        : over === source.h ? source.periods : over === source.h - 1 ? source.periods_between : null;
      if (!periods && dropAt && dropAt.h != null) periods = entryOf(dropAt.h);
      return { enabled: enabled, source: source, reached: periods ? new Set(periods) : null,
        control: dropAt ? dropAt.control || null : null, live: live, listing: listing, send: sendDrop,
        frames: frames, pressFrame: p.reading ? frameDrag.current.press : null, frameTarget: frameTarget,
        // the period whose `+ stage` opened the list that is open (design pass 10 §7)
        listFor: listOpen && listing ? listPeriod : null,
        // the cable drag in progress and the rule of a cable port's drag (design pass 10 §7)
        cable: cableState, portStarts: p.reading && p.joins ? portStarts : null, lit: litPorts, moving: movingPorts };
    }, [enabled, source, over, dropAt, live, listing, p.stages, frames, frameTarget, p.reading, listOpen, listPeriod, cableState, p.joins, litPorts, movingPorts]);
    // A list that can no longer open, or a new graph, ends the list and the
    // keyboard's route.
    useEffect(function () {
      if (listing) return;
      setListOpen(false);
      setSending(null);
      endDrag();
    }, [listing]);
    useEffect(function () { setSending(null); setDropAt(null); }, [m]);
    // Whether the region ended the drag in progress, whose release then sends nothing.
    var ended = useRef(false);
    useEffect(function () {
      cableDrag.current = null;
      setCableState(null);
      if (!store.getState().connection.inProgress) return;
      ended.current = true;
      store.getState().cancelConnection();
    }, [enabled, p.reading]);
    // The selection of a join wire, the edge `id` with its record, or of
    // none, given to Python by the event join-chosen where it changes.
    function chooseJoin(id, record) {
      if (nearestEnd.current) nearestEnd.current.removeAttribute('data-nearest');
      nearestEnd.current = null;
      setJoinChosen(id);
      if (record || chosenRecord.current) {
        var q = latest.current;
        q.host.dispatchEvent(new CustomEvent('join-chosen', { bubbles: true, detail: { reading: q.reading, join: record } }));
      }
      chosenRecord.current = record;
    }
    // A new list of join wires, given at a reading or taken away by an input
    // edit, ends the selection of a join wire.
    useEffect(function () { chooseJoin(null, null); }, [p.joins]);
    useEffect(function () { setSharedChoice(null); }, [p.joins, p.graph, p.reading]);
    function openShared(edge) {
      var keys = new Set();
      edge.data.members.forEach(function (id) {
        var branch = edges.find(function (e) { return e.id === id; });
        if (branch && joinsByKey.has(branch.data.key)) keys.add(branch.data.key);
      });
      if (!keys.size) return;
      choose(null); chooseJoin(null, null); chooseBundle(null); setPairing(null);
      setSharedChoice({ edge: edge.id, keys: Array.from(keys) });
    }
    function edgeElement(id) {
      return host.current && host.current.querySelector('.react-flow__edge[data-id="' + CSS.escape(id) + '"]');
    }
    function focusEdge(id) {
      var element = edgeElement(id) || host.current;
      if (element) element.focus({ preventScroll: true });
    }
    function closeShared() {
      setSharedChoice(null);
      focusEdge(sharedChoice.edge);
    }
    R.useLayoutEffect(function () {
      if (sharedChoice && sharedList.current) placeList(sharedList.current, edgeElement(sharedChoice.edge), host.current);
    }, [sharedChoice, laid]);
    useEffect(function () {
      if (!sharedChoice) return;
      var button = sharedList.current && sharedList.current.querySelector('.bf-stage-item');
      if (button) button.focus({ preventScroll: true });
      function outside(event) {
        if (sharedList.current && !sharedList.current.contains(event.target)) setSharedChoice(null);
      }
      document.addEventListener('click', outside, true);
      return function () { document.removeEventListener('click', outside, true); };
    }, [sharedChoice]);
    function chooseEdge(edge) {
      if (edge.data.members) openShared(edge);
      else if (edge.data.record) { choose(null); chooseJoin(edge.id, edge.data.record); }
      else if (edge.data.bundle) { choose(null); chooseJoin(null, null); chooseBundle(edge.data.bundle); }
    }
    function pressInRegion(event) {
      pressed.current = true;
      setTimeout(function () { pressed.current = false; }, 0);
      sharedPress.current = null;
      if (!event.target.closest('.react-flow__edgeupdater')) return;
      var branch = event.target.closest('.bf-join-wire.selected');
      if (!branch) return;
      // A click can select the line under a drag target. A drag still uses the selected connector.
      var hits = document.elementsFromPoint(event.clientX, event.clientY);
      var run = hits.map(function (hit) { return hit.closest('.bf-shared-run, .bf-join-pair'); })
        .filter(Boolean).map(function (hit) { return edges.find(function (e) { return e.id === hit.dataset.id; }); })
        .find(function (edge) {
          return edge && (edge.data.members || edge.data.branches || []).includes(branch.dataset.id);
        });
      if (run) sharedPress.current = { id: run.id, members: run.data.members || run.data.branches };
    }
    function clickInRegion(event) {
      var press = sharedPress.current;
      sharedPress.current = null;
      if (!press || !event.target.closest('.react-flow__edgeupdater')) return;
      var edge = edges.find(function (e) { return e.id === press.id; });
      if (!edge || (edge.data.members || edge.data.branches) !== press.members) return;
      event.stopPropagation();
      chooseEdge(edge);
    }
    // The join wires that leave or reach the cable port `port`, a record
    // of `cablePorts`, of the stage occurrence at `ns`: a wire's record
    // names its writing port by its node and its port, which the card's
    // port id joins by `|` (flow-layout.js, `build`).
    function recordsAt(ns, port) {
      return (p.joins || []).filter(function (record) {
        if (record.sourceHandle === null) return false;
        var same = record.source + '|' + record.sourceHandle === port.id;
        return same && (port.side === 'writing' ? record.from === ns : record.to === ns);
      });
    }
    // Whether the cable port `port` of the occurrence at `ns` starts a drag
    // (design pass 10 §7): a joined branch port that one cable leaves, as
    // the move of its reading end; an unjoined branch port whose branch
    // holds an unjoined continuation field, as a new cable; a reading port
    // that one cable reaches, as the move of that cable's reading end.
    function portStarts(ns, port) {
      var records = recordsAt(ns, port);
      if (port.side === 'writing' && !port.joined) {
        var frame = frames.get(ns);
        return !!frame && frame.writes.some(function (w) { return port.fields.indexOf(w.id) >= 0; });
      }
      return records.length === 1 && records[0].movable.indexOf('reading') >= 0;
    }
    // The cable drag that begins at the handle `handleId` of the node
    // `nodeId`, or null where the handle is no cable port that starts one
    // (`portStarts`).
    function cableDragFrom(nodeId, handleId) {
      var port = cablePorts.current[handleId], ns = occurrenceOf(nodeId);
      if (!port || !ns || !portStarts(ns, port)) return null;
      var match = /^periods\[(\d+)\]\/(.+)$/.exec(ns), records = recordsAt(ns, port);
      if (port.side === 'writing' && !port.joined) {
        return { end: 'reading', record: null, h: Number(match[1]), key: match[2], ns: ns, branch: port.branch, port: port };
      }
      return { end: 'reading', record: records[0], h: Number(match[1]), key: match[2], ns: ns, branch: port.branch, port: port };
    }
    // The cable port a connection ends at on the side `end`, {ns, port},
    // the port's record of `cablePorts` and its occurrence, or null.
    function cableEnd(connection, end) {
      var handle = end === 'reading' ? connection.targetHandle : connection.sourceHandle;
      var node = end === 'reading' ? connection.target : connection.source;
      var port = cablePorts.current[handle], ns = occurrenceOf(node);
      return port && ns && port.side === end && !port.hidden ? { ns: ns, port: port } : null;
    }
    // The handle a connection ends at on the side `end`, {node, handle},
    // beside which the list its drop opens stands (`dropElement`; design
    // pass 10 §7).
    function dropOf(connection, end) {
      return end === 'reading' ? { node: connection.target, handle: connection.targetHandle }
        : { node: connection.source, handle: connection.sourceHandle };
    }
    // The moved end of a join wire `at`, {record, end}, admitted at a
    // cable port of the connection (design pass 10 §7; J-D33): a reading
    // end at the arrival port of another occurrence of the period of the
    // end it replaces, and a writing end at a branch port, joined or not,
    // of another occurrence of the writing period, since the write releases
    // the old pair; within a period, another occurrence than the end kept.
    function admitsMove(at, connection) {
      var found = cableEnd(connection, at.end);
      return !!found && cableAdmits({ end: at.end, record: at.record }, found.ns, found.port);
    }
    // The list a cable's move opens (`pairProps`), {cable, end, record,
    // source: {ns, branch}, destination}: for a reading end, the cable's
    // branch to the occurrence dropped on; for a writing end, the branch
    // dropped on to the cable's reading occurrence.
    function cableListing(record, end, found) {
      var source = end === 'reading' ? { ns: record.from, branch: record.branch || '' } : { ns: found.ns, branch: found.port.branch };
      var destination = end === 'reading' ? found.ns : record.to;
      return { cable: true, end: end, record: record, source: source, destination: destination };
    }
    // A join wire's end released on a cable port the rule admits (design
    // pass 10 §7; K-D23): where the cable carries one wire and the side
    // dropped on holds one field, the event moved with that field's port
    // (J-D33); otherwise the list of the destination's arrival fields
    // against the branch's continuation fields, in place of the stage list.
    // The piece the wires of a pair of periods share, whose writer is a
    // period and not an occurrence, moves by its reading end alone through
    // the list of its field pairs (K-D5, K-D23).
    function move(_oldEdge, connection) {
      var at = moving.current;
      if (ended.current || !at || !at.record || !p.reading || !admitsMove(at, connection)) return;
      var found = cableEnd(connection, at.end), drop = dropOf(connection, at.end);
      if (at.record.sourceHandle === null) {
        setListOpen(false);
        setSending(null);
        setPairing({ record: at.record, end: at.end, at: found.ns, drop: drop });
        return;
      }
      var listing = cableListing(at.record, at.end, found);
      var alone = singleField(listing);
      if ((at.record.fields || []).length === 1 && alone) {
        p.host.dispatchEvent(new CustomEvent('moved', { bubbles: true, detail: {
          reading: p.reading, join: idsOf(at.record), end: at.end, handle: alone } }));
        return;
      }
      setListOpen(false);
      setSending(null);
      setPairing(Object.assign(listing, { drop: drop }));
    }
    // The one field port of the moved side of the list `listing`, the
    // destination's one arrival field for a reading end and the branch's
    // one continuation field for a writing end; null where there are
    // several or none.
    function singleField(listing) {
      var frame = frames.get(listing.end === 'reading' ? listing.destination : listing.source.ns);
      if (!frame) return null;
      var held = listing.end === 'reading' ? frame.reads
        : frame.fields.filter(function (f) { return (f.branch || '') === listing.source.branch; });
      return held.length === 1 ? held[0].id : null;
    }
    // The rule of a drag from a cable port (`cableAdmits`; design pass 10
    // §7); for the moved end of a join wire, `admitsMove`; for a drag from
    // an unjoined port of a closed period's box, the rule of §3.1, as
    // J-D41 amends it (`takesDrag`).
    function admits(connection) {
      if (moving.current) return !!moving.current.record && admitsMove(moving.current, connection);
      if (cableDrag.current) {
        var found = cableEnd(connection, 'reading');
        return !!found && cableAdmits(cableDrag.current, found.ns, found.port);
      }
      var s = enabled.get(portOf(connection.source, connection.sourceHandle, 'source'));
      var t = enabled.get(portOf(connection.target, connection.targetHandle, 'target'));
      return !!s && !!t && takesDrag(s, t);
    }
    // The event of a drag released on a port the rule admits (J-D17). A
    // drag from a cable port opens the list of the destination's arrival
    // fields against the branch's continuation fields (design pass 10 §7):
    // from a joined branch port or a reading port, the move of the cable's
    // reading end, and from an unjoined branch port, a new cable.
    function connect(connection) {
      if (ended.current || !admits(connection)) return;
      var cable = cableDrag.current;
      if (cable) {
        var found = cableEnd(connection, 'reading');
        setListOpen(false);
        setSending(null);
        setPairing(Object.assign(cable.record ? cableListing(cable.record, 'reading', found)
          : { cable: true, end: 'reading', record: null, source: { ns: cable.ns, branch: cable.branch }, destination: found.ns },
          { drop: dropOf(connection, 'reading') }));
        return;
      }
      p.host.dispatchEvent(new CustomEvent('connected', { bubbles: true, detail: {
        reading: p.reading, source: connection.source, target: connection.target,
        sourceHandle: portOf(connection.source, connection.sourceHandle, 'source'),
        targetHandle: portOf(connection.target, connection.targetHandle, 'target') } }));
    }

    // The place under the pointer of a drag event: a control's box, else a
    // period's layer, each found among the places laid out, the pointer
    // converted to the flow's coordinates (`screenToFlowPosition`).
    function dropPlace(event) {
      var at = rf.screenToFlowPosition({ x: event.clientX, y: event.clientY });
      function holds(r) { return at.x >= r.ax && at.x <= r.ax + r.width && at.y >= r.ay && at.y <= r.ay + r.height; }
      var control = addPlaces.current.find(holds);
      if (control) return { control: control.target };
      var period = periodPlaces.current.find(holds);
      return period ? { h: period.h } : null;
    }
    function samePlace(a, b) { return a === b || (!!a && !!b && a.h === b.h && a.control === b.control); }
    // The target the event dropped names for a place.
    function targetOf(place) { return place.control || 'periods[' + place.h + ']' + L.LAYER_ENDING; }
    // The place a drag event would drop the item dragged at: none where no
    // drop can be made, none on a layer whose list holds the folder stage,
    // which is not marked valid (§3.5), and none on a control while a
    // reading stands refused, when the controls do not act (unit L, Task 14).
    function validPlace(event) {
      var item = dragged.current, place = item && listing ? dropPlace(event) : null;
      if (place && place.control && !live) return null;
      return place && place.h != null && listedIn(item, place.h) ? null : place;
    }
    // The place the item dragged would reach, marked when the pointer enters
    // an element and at each move over it; the browser admits the drop only
    // where that place is valid.
    function dragOver(event) {
      var place = validPlace(event);
      setDropAt(function (was) { return samePlace(was, place) ? was : place; });
      if (!place) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
    }
    function dropItem(event) {
      var item = dragged.current, place = validPlace(event);
      endDrag();
      if (!place) return;
      event.preventDefault();
      setListOpen(false);
      setLastChosen(item.kind + ' ' + item.id);
      sendDrop(item, targetOf(place));
    }
    function leaveDrag(event) {
      if (!event.currentTarget.contains(event.relatedTarget)) setDropAt(null);
    }
    // The start of a drag of an item, which hides the list once the browser
    // has taken the drag's image, and its end.
    function dragList(item) {
      if (!item) { endDrag(); return; }
      dragged.current = item;
      setTimeout(function () { if (dragged.current === item) setDragItem(item); }, 0);
    }
    function endDrag() {
      dragged.current = null;
      setDragItem(null);
      setDropAt(null);
    }

    // The keyboard's route (§3.5): the candidates of the item `item`, in time
    // order, each control before the layer of the period after it, and the
    // period layers drawn but those whose list holds the folder stage, each
    // {box, control} or {box, h}; no control while a reading stands refused
    // (unit L, Task 14).
    function candidatesFor(item) {
      var controls = (live && laid && laid.controls) || [], out = [];
      var periods = periodPlaces.current.map(function (at) { return at.h; }).sort(function (a, b) { return b - a; });
      periods.forEach(function (period) {
        var ns = 'periods[' + period + ']';
        controls.filter(function (c) { return c.later === ns; }).forEach(function (c) {
          out.push({ box: c.id, control: c.target });
        });
        if (!listedIn(item, period)) out.push({ box: ns + L.LAYER_ENDING, h: period });
      });
      return out;
    }
    // The candidate shown: marked as an item dragged there would mark it, and
    // its element focused, the view moved to it.
    function showCandidate(candidate) {
      setDropAt(candidate.control ? { control: candidate.control } : { h: candidate.h });
      focusItem({ box: candidate.box }, laid);
    }
    // Enter on an item of the list: the list closes and the first candidate
    // is shown.
    function pickItem(item) {
      if (!laid || laid.model !== m) return;
      var candidates = candidatesFor(item);
      if (!candidates.length) return;
      setListOpen(false);
      setLastChosen(item.kind + ' ' + item.id);
      setSending({ item: item, index: 0 });
      showCandidate(candidates[0]);
    }
    function endSending() {
      setSending(null);
      setDropAt(null);
    }
    // Escape in the list, or its control `×`: the list closes and the graph
    // takes the focus (unit K's decision K-D24).
    function closeList() {
      if (host.current) host.current.focus({ preventScroll: true });
      setListOpen(false);
    }
    // The element of the stage list while it is drawn, and the button
    // `stages`, which opens and closes the list by its own press.
    var listElement = useRef(null), stagesElement = useRef(null);
    // A click outside the stage list closes it: on the graph's ground, a box,
    // a layer, a control or elsewhere on the page, but not on the button
    // `stages`; a click inside the list, its heading included, closes
    // nothing, and a drag from the list makes no click (unit K's decision
    // K-D24). The document takes the click in its capture phase, before any
    // control can stop the click's propagation.
    useEffect(function () {
      if (!listOpen) return;
      function outside(event) {
        var at = event.target;
        if ((listElement.current && listElement.current.contains(at)) ||
            (stagesElement.current && stagesElement.current.contains(at))) return;
        setListOpen(false);
      }
      document.addEventListener('click', outside, true);
      return function () { document.removeEventListener('click', outside, true); };
    }, [listOpen]);

    // Every layer of every graph takes the direction named by the button, the page's, which the browser keeps
    // (§2.2; design pass 14 §2; S-D5).
    function turn() { turnPage(); }
    /* The box on the graph of the card `id`, unfolded, of the layout `r`
       of `built`, with its ring, 7 px outside it, and the first runs of its
       cables, at whose ends their counts stand (`firstRunOf`), which the
       view pans to (the fix wave Q3a, item 8); null where no card of that
       id is laid out. */
    function grownCard(built, r, id) {
      var b = built.boxes[id], at = r.place[id];
      if (!b || !b.geom || !b.geom.card || !at) return null;
      var ring = 7, box = { left: at.ax - ring, top: at.ay - ring, right: at.ax + at.width + ring, bottom: at.ay + at.height + ring };
      var plugs = b.geom.outs.map(function (p) { return p.handle; });
      built.wires.forEach(function (w) {
        var route = r.routes[w.id];
        if (plugs.indexOf(w.sourceHandle) < 0 || !route || route.length < 2) return;
        box.left = Math.min(box.left, route[1].x); box.right = Math.max(box.right, route[1].x);
        box.top = Math.min(box.top, route[1].y); box.bottom = Math.max(box.bottom, route[1].y);
      });
      return box;
    }
    /* The view panned at its scale by the least distance that brings the
       box `box` on the graph inside the region less REVEAL px at each
       side, a box wider or taller than that standing on the region's text
       edge, its left or its top REVEAL inside; a box already inside gives
       no pan (the fix wave Q3a, item 8; A18, B19, D23). */
    function panTo(box) {
      var el = host.current;
      if (!el) return;
      var v = rf.getViewport(), z = v.zoom;
      function shift(lo, hi, size, offset) {
        var a = lo * z + offset, b = hi * z + offset;
        if (b - a > size - 2 * REVEAL) return REVEAL - a;
        if (a < REVEAL) return REVEAL - a;
        if (b > size - REVEAL) return size - REVEAL - b;
        return 0;
      }
      var dx = shift(box.left, box.right, el.clientWidth, v.x), dy = shift(box.top, box.bottom, el.clientHeight, v.y);
      if (Math.abs(dx) > 0.01 || Math.abs(dy) > 0.01) rf.setViewport({ x: v.x + dx, y: v.y + dy, zoom: z }, { duration: 0 });
    }
    function fitGraph() {
      var el = host.current;
      if (!el) return;
      var width = el.clientWidth, height = el.clientHeight;
      if (!(width > 0 && height > 0)) return;
      var nodes = rf.getNodes().filter(function (node) { return !node.hidden; });
      if (!nodes.length) return;
      var bounds = rf.getNodesBounds(nodes);
      // a boundary marker's node is its mark alone; its label stands beside the mark in the room the layout keeps
      // for it, and the fit shows that label whole (N-I277)
      nodes.forEach(function (node) {
        var g = node.type === 'marker' && node.data ? node.data.geom : null;
        if (!g) return;
        var x = node.position.x + g.labelAt.x - g.mark.x, y = node.position.y + g.labelAt.y - g.mark.y;
        var left = Math.min(bounds.x, x), top = Math.min(bounds.y, y);
        var right = Math.max(bounds.x + bounds.width, x + g.labelAt.width);
        var bottom = Math.max(bounds.y + bounds.height, y + g.labelAt.height);
        bounds = { x: left, y: top, width: right - left, height: bottom - top };
      });
      if (!(bounds.width > 0 && bounds.height > 0)) return;
      // the drawing whole, at most at scale 1, its top TOP below the bar and its left edge on the text edge, ROOM
      // kept at the region's right and bottom edges, so that a drawing as wide as the region ends on the right text
      // edge (design pass 13 §2, rule 10; D3; Q-D12; the fix wave Q3a, item 9)
      var zoom = Math.max(MIN_ZOOM, Math.min(1, (width - TEXT_EDGE - ROOM) / bounds.width, (height - TOP - ROOM) / bounds.height));
      return rf.setViewport({ x: TEXT_EDGE - bounds.x * zoom, y: TOP - bounds.y * zoom, zoom: zoom }, { duration: 0 });
    }
    useEffect(function () {
      var last = null;
      var observer = new ResizeObserver(function (entries) {
        var size = entries[0].contentRect;
        if (last && (size.width !== last.width || size.height !== last.height)) {
          // A viewport still at the kept opening of the layout drawn opens that layout again (G-R76).
          var o = lastOpening.current, s = shown.current, v = rf.getViewport();
          if (o && s && o.key === s.key && (!o.at || s.place[o.at]) &&
              v.x === o.view.x && v.y === o.view.y && v.zoom === o.view.zoom) begin(s, o.at);
          else fitGraph();
        }
        last = { width: size.width, height: size.height };
      });
      if (host.current) observer.observe(host.current);
      return function () { observer.disconnect(); };
    }, []);

    function reveal(nodeId, open) {
      var ns = m.nodes[nodeId] ? m.nodes[nodeId].namespace : null;
      if (ns === null) {
        var layer = Object.keys(m.layers).find(function (name) { return m.layers[name].id === nodeId; });
        ns = layer || '';
      }
      L.chain(ns).forEach(function (name) { open.add(name); });
    }

    // A refused layout or absent graph has no geometry or pending focus.
    function clearDrawing() {
      setNodes([]); setEdges([]); setLaid(null);
      parents.current = {}; shown.current = null; lastOpening.current = null; periodPlaces.current = []; addPlaces.current = [];
      occurrencePlaces.current = [];
      p.report.open = []; p.report.selection = null;
      pendingToggle.current = null;
      if (focusFrame.current !== null) cancelAnimationFrame(focusFrame.current);
      focusFrame.current = null;
    }

    useEffect(function () {
      if (!m) { clearDrawing(); return; }
      var cancelled = false, frame = null, started = performance.now();
      var state = kept.current, open = openSet();
      // A period the graph newly shows alone opens with the layers of its
      // occurrences open, and the region opens on it (unit L, Task 22):
      // those layers join the open layers once, which the reader's toggles
      // then change as any others, and a new reading of the same period
      // alone keeps the view (§2.3).
      var alone = periodAlone(m);
      if (alone && alone !== state.alone[p.graph]) {
        open.add(alone);
        Object.keys(m.layers).forEach(function (ns) { if (m.layers[ns].parent === alone) open.add(ns); });
        state.opens[p.graph] = true;
      }
      state.alone[p.graph] = alone;
      var place = p.place && p.place.n !== appliedPlace.current && p.place.graph === p.graph ? p.place : null;
      var asked = p.select && p.select.n !== appliedSelect.current && (!p.select.graphId || p.select.graphId === p.graph) ? p.select : null;
      if (place) {
        var visible = opening(place.layers), previous = open;
        open = new Set(visible);
        // A restored visible state keeps expansion choices hidden under its closed layers.
        previous.forEach(function (ns) {
          if (m.layers[ns] && !L.chain(m.layers[ns].parent).every(function (ancestor) { return visible.has(ancestor); })) open.add(ns);
        });
        state.sets[p.graph] = open;
        state.chosen[p.graph] = place.nodeId || null;
        if (place.nodeId) reveal(place.nodeId, open);
      } else if (asked) {
        state.chosen[p.graph] = asked.nodeId || null;
        if (asked.nodeId) reveal(asked.nodeId, open);
      }
      var chosen = state.chosen[p.graph] || null;
      function refused(err) {
        if (cancelled) return;
        clearDrawing();
        var sentence = 'the graph ' + p.graph + ' was not laid out: ' + (err && err.message ? err.message : err);
        if (p.refused) p.refused({ graphId: p.graph, sentence: sentence });
      }
      try {
        // the recipe's order of the stage keys, by which every period stands its occurrences in rows (the fix wave
        // Q3a, item 2)
        var options = { direction: flows, adds: laidAdds, builders: p.builders, unfold: unfold, split: split, order: p.stage_order || null };
        var built = L.build(m, open, options, measure);
        var elk = new window.ELK();
        // a trellis graph whose columns are ragged is laid out a second time with every card of a column at
        // the widest width of its column (design pass 13 §2, rule 6; Q-D25); a stage's builders graph is laid
        // out a second time by `arrange`, which aligns its frames (AAS, L-D20)
        elk.layout(built.elk).then(function (first) {
          var widths = L.columnWidths(built, first);
          if (!widths) return first;
          built = L.build(m, open, Object.assign({}, options, { widths: widths }), measure);
          return elk.layout(built.elk);
        }).then(function (laidOut) { return L.arrange(built, laidOut, elk); }).then(function (answer) {
          if (cancelled) return;
          // the controls the layout holds, each {id, target, later}
          var controls = Object.keys(built.boxes).filter(function (id) { return built.boxes[id].type === 'add'; })
            .map(function (id) { return { id: id, target: built.boxes[id].target, later: built.boxes[id].later }; });
          // the frames on one top edge, the markers 24 px outside them and the drawing at the root's padding
          // (design pass 13 §1, rule 6; D13)
          L.settle(built, answer);
          var r = L.read(built, answer);
          // a field diagram first shown too wide at the reading size no longer turns on its own (spec 0.4 §2.3); the
          // page's direction holds for every graph (design pass 14 §2, rule 3; S-D5)
          // the bundles a selection splits (L-D25), a cable of a route's values standing whole (design pass 12 §2)
          setLaid({ model: m, open: new Set(open), read: r, controls: controls, stages: !!laidAdds, compact: built.compact,
            pairs: new Set(built.pairBundles.filter(function (u) { return !u.whole; }).map(function (u) { return u.id; })) });
          periodPlaces.current = Object.keys(m.layers).map(function (ns) {
            var match = PERIOD.exec(ns), at = r.place[m.layers[ns].id];
            return match && at ? { h: Number(match[1]), ax: at.ax, ay: at.ay, width: at.width, height: at.height } : null;
          }).filter(Boolean);
          addPlaces.current = controls.map(function (c) {
            var at = r.place[c.id];
            return { target: c.target, ax: at.ax, ay: at.ay, width: at.width, height: at.height };
          });
          // the frames of the stage occurrences drawn, those of the open periods (K-D8)
          occurrencePlaces.current = Object.keys(m.layers).map(function (ns) {
            var at = L.OCCURRENCE.test(ns) && open.has(ns.split('/')[0]) ? r.place[m.layers[ns].id] : null;
            return at ? { ns: ns, ax: at.ax, ay: at.ay, width: at.width, height: at.height } : null;
          }).filter(Boolean);
          // the cables' ports of every card, by the port's handle: its occurrence, its side, its branch, whether a
          // wire joins it and the ids of its field ports (design pass 10 §§6 and 7)
          var index = {}, alias = {};
          Object.keys(built.boxes).forEach(function (id) {
            var b = built.boxes[id];
            if (b.type !== 'layer' || !b.geom || !b.geom.card) return;
            [[b.geom.ins, 'reading'], [b.geom.outs, 'writing']].forEach(function (pair) {
              pair[0].forEach(function (port) {
                index[port.handle] = { ns: b.namespace, side: pair[1], id: port.id, branch: port.branch || '', joined: !!port.joined,
                  hidden: !!port.hidden, fields: (port.fields || []).map(function (f) { return f.id; }) };
                if (port.hidden && b.geom.ins[0]) alias[port.handle] = b.geom.ins[0].handle;
              });
            });
          });
          cablePorts.current = index;
          portAlias.current = alias;
          // the periods drawn, by which an `outside` marker's hover names the range outside them (design pass 10 §6)
          var drawnPeriods = periodPlaces.current.map(function (at) { return at.h; });
          var outsideHover = drawnPeriods.length ? 'Outside periods ' + Math.min.apply(null, drawnPeriods) + '\u2013' + Math.max.apply(null, drawnPeriods) : 'Outside the drawn periods';
          var ids = Object.keys(built.boxes).sort(function (a, b) {
            var A = built.boxes[a], B = built.boxes[b];
            var da = A.type === 'layer' ? A.namespace.split('/').length : 99;
            var db = B.type === 'layer' ? B.namespace.split('/').length : 99;
            return da - db;
          });
          parents.current = {};
          // whether the graph is a trellis graph, which holds a period's layer
          var trellis = Object.keys(m.layers).some(function (ns) { return PERIOD.test(ns); });
          var next = ids.map(function (id) {
            // a builder's box of a compact occurrence takes its place in the occurrence's frame (L-D7)
            var b = built.boxes[id], at = r.place[id] || r.builders[id];
            parents.current[id] = b.parent;
            var node = { id: id, position: { x: at.x, y: at.y }, width: at.width, height: at.height,
              style: { width: at.width, height: at.height }, selected: id === chosen, focusable: false };
            if (b.parent) { node.parentId = b.parent; node.extent = 'parent'; }
            var perch = false;
            if (b.type === 'layer') {
              var direct = m.order.filter(function (id) { return m.nodes[id].namespace === b.namespace; });
              perch = direct.length > 0 && direct.every(function (id) { return m.nodes[id].attrs.kind === 'field'; });
            }
            if (b.type === 'add') {
              node.type = 'add';
              node.selectable = false;
              node.data = { target: b.target, name: b.name };
            } else if (b.type === 'marker') {
              // a boundary marker's node is its mark alone, placed where the layout set the mark within the room it
              // kept for the mark and the label (design pass 10 §6)
              node.type = 'marker';
              node.position = { x: at.x + b.geom.mark.x, y: at.y + b.geom.mark.y };
              node.width = node.height = b.geom.mark.size;
              node.style = { width: b.geom.mark.size, height: b.geom.mark.size };
              node.data = { label: b.spec.label, target: b.spec.target, geom: b.geom, dir: b.dir, hover: outsideHover };
            } else if (b.type === 'layer' && b.open) {
              node.type = 'layer';
              // the index of a period whose layer carries `+ stage`, in a graph with `+ period` controls (K-D14)
              var period = laidAdds && PERIOD.test(b.namespace) ? Number(PERIOD.exec(b.namespace)[1]) : null;
              // a compact occurrence's frame takes its geometry and its direction (L-D7)
              node.data = { type: 'layer', label: b.name, namespace: b.namespace, level: levelOf(b.layer, p.styles), colors: colors,
                perch: perch, onToggle: toggle, onOpen: openWhole, period: period, onAddStage: openForPeriod,
                geom: b.compact ? b.geom : null, dir: b.dir,
                // a period's layer of the graph's root, whose head is G.periodHeader, and the face of the layer's
                // name: a stage's name for a stage occurrence of a trellis graph, and a frame's name, the period
                // style, for every other layer of either graph (design pass 10 §5; design pass 13 §3, Q-D22)
                periodHead: PERIOD.test(b.namespace) && !b.layer.parent,
                face: trellis && L.OCCURRENCE.test(b.namespace) ? 'stage' : 'frame' };
            } else if (b.type === 'builder') {
              node.type = 'builder';
              // a segment of the selected card's band prints its pair's signs and its id (AAS, L-D25); its click
              // opens the builder in place, the occurrence with it (design pass 13 §2, rule 5)
              node.data = { label: b.name, namespace: b.namespace, record: b.record, onToggle: openBuilder,
                unfolded: !!built.boxes[b.parent].geom.unfolded };
            } else if (b.type === 'layer') {
              node.type = 'box';
              node.data = { type: 'layer', closed: true, label: b.name, role: 'layer', perch: perch, level: levelOf(b.layer, p.styles), colors: colors,
                namespace: b.namespace, geom: b.geom, dir: b.dir, onToggle: toggle, onOpen: openWhole };
            } else {
              node.type = 'box';
              // a box of a trellis graph, its own Inputs and Outputs among them, whose joined ports' marks are drawn as a
              // card's are (AAS, M-D15)
              node.data = { type: b.type, label: b.spec.label, description: b.node.description,
                role: b.spec.role || 'label', style: styleOf(b.node, graph, p.styles), colors: colors, sub: b.spec.sub || '', geom: b.geom, dir: b.dir,
                trellis: trellis };
            }
            return node;
          });
          // whether a cable leaves its card in the lower half of the card's stack of plugs, where its count
          // stands under the cable (design pass 13 §1, rule 5)
          function lowerHalf(w) {
            var writer = built.boxes[w.source], outs = writer && writer.geom ? writer.geom.outs : null;
            if (!outs || outs.length < 2) return false;
            var index = outs.map(function (p) { return p.handle; }).indexOf(w.sourceHandle);
            return index >= 0 && index >= outs.length / 2;
          }
          var sharedInputs = new Set(), sharedControls = new Set(Object.keys(r.paint));
          built.bundles.forEach(function (u) {
            if (!u.wires.some(function (id) { return !!r.paint[id]; })) return;
            sharedControls.add(u.id);
            u.wires.forEach(function (id) { sharedControls.add(id); });
          });
          r.sharedRuns.forEach(function (run) {
            if (run.terminal) run.members.forEach(function (id) { sharedInputs.add(id); });
          });
          var wires = built.wires.map(function (w) {
            // the title of a wire that carries joins holds, after its label, the joins' text as the exporter writes
            // it (K-D4); a bundle's, the labels of its wires, each once, one a line, then their joins (AAS, L-D25)
            var u = w.pairBundle || null;
            var labels = u ? u.members.map(function (member) { return member.label; })
              .filter(function (label, i, all) { return label && all.indexOf(label) === i; }) : [];
            var title = u ? labels.concat(u.joins ? [u.joins] : []).join('\n')
              : w.reading.join ? w.label + '\n' + w.reading.join : w.label;
            // a cable's branch stands first in its title, the cable drawing no label (the fix wave Q3a, item 4)
            if (w.cable && w.branch) title = [w.branch, title].filter(Boolean).join('\n');
            var ends = [[w.source, w.target]];
            // a wire of a bundle of K-D5 draws its pieces inside the two periods, and the bundle its label; the
            // bundle of a pair within a period is a wire of its own, which a click selects and no record names
            // (AAS, L-D25); a wire of the bundle selected, split, is drawn lit. A cable of a route's values, which
            // nothing splits, is a join wire, named by its first wire, whose record Python gives (design pass 12
            // §2), its label the labels of its wires, which its title keeps once the record is found
            var pair = u && !u.whole ? u : null, shared = !!r.bundles[w.bundle];
            var initialLeg = !!w.initialRoute && Object.hasOwn(r.parts, w.id);
            return { id: w.id, type: 'wire', source: w.source, target: w.target, sourceHandle: w.sourceHandle,
              targetHandle: w.targetHandle, selectable: !!pair, focusable: false, reconnectable: false,
              // a wire of a bundle of a pair of periods, whose own route ends where the bundle's wires meet and
              // whose run into the socket the shared piece draws, is .bf-cable-shared (K-D5)
              className: [pair ? 'bf-pair-bundle' : '', w.cable && !initialLeg ? 'bf-cable-edge' : '',
                shared ? 'bf-cable-shared' : '', initialLeg ? 'bf-initial-route-leg' : ''].filter(Boolean).join(' ') || undefined,
              domAttributes: pair ? { 'data-from': pair.from, 'data-to': pair.to } : undefined,
              data: { parts: r.parts[w.id] || [r.routes[w.id]],
                paint: initialLeg ? r.paint[w.id] || r.parts[w.id] || [] : r.paint[w.id],
                sharedInput: sharedInputs.has(w.id) || (initialLeg && !r.initialArrows[w.id]),
                sharedControl: sharedControls.has(w.id),
                label: pair ? w.label : u ? labels.join('\n') : w.label,
                title: title, join: shared || initialLeg ? '' : w.join, joinAt: shared ? null : r.joins[w.id] || null,
                key: pair || initialLeg ? null : wireKey(w.from, w.out, w.to, w.into), record: null, shared: shared,
                bundle: pair ? pair.id : null, pairOf: w.pairOf || null, pairBundle: !!u,
                // a cable's body, its dashed stub, the count of its wires, its place in its card's stack of plugs
                // and its branch (design pass 10 §6; design pass 13 §1, rule 5)
                cable: !initialLeg && !!w.cable, dashed: !!w.dashed, count: initialLeg ? 1 : w.count || 1,
                below: lowerHalf(w), branch: w.branch || null,
                // a wire at a closed period's box, which draws no arrowhead (the fix wave Q3a, item 10)
                closed: !initialLeg && !!w.closed,
                // the handles of its two ports, which are lit with it (design pass 13 §1, rule 7)
                handles: [[w.sourceHandle, w.targetHandle]],
                ends: ends, lit: lights(ends, chosen) || (!!w.pairOf && w.pairOf === bundleChosen) } };
          });
          /* The bundles of K-D5: one wire each, the route its wires share
             across the gap between the two periods, with their label and
             their title, attached to the boxes and ports of its first
             wire, which React Flow requires; its key is the writers'
             period and the reading port, under which Python gives the
             record of the pair (`trellis.join_wires`). */
          var byId = {};
          built.wires.forEach(function (w) { byId[w.id] = w; });
          function pairEdge(u, drawn) {
            var first = byId[u.wires[0]];
            var ends = u.wires.map(function (id) { return [byId[id].source, byId[id].target]; });
            var title = first.reading.join ? u.join + '\n' + first.reading.join : u.join;
            return { id: u.id, type: 'wire', source: first.source, target: first.target, sourceHandle: first.sourceHandle,
              targetHandle: first.targetHandle, selectable: false, focusable: false, reconnectable: false,
              className: u.cable ? 'bf-cable-edge' : undefined,
              data: { parts: [drawn.points], label: u.join, title: title, join: u.join, joinAt: drawn.join, pair: true,
                branches: u.wires, sharedControl: sharedControls.has(u.id),
                cable: !!u.cable, closed: !!first.closed, count: u.count || u.wires.length, branch: null,
                handles: u.wires.map(function (id) { return [byId[id].sourceHandle, byId[id].targetHandle]; }),
                key: wireKey(u.from, null, u.reader, u.into), record: null, ends: ends, lit: lights(ends, chosen) } };
          }
          var byPair = Object.fromEntries(built.bundles.map(function (u) { return [u.id, u]; }));
          var pairs = built.bundles.filter(function (u) { return !!r.bundles[u.id]; })
            .map(function (u) { return pairEdge(u, r.bundles[u.id]); });
          var sharedRuns = r.sharedRuns.map(function (run) {
            if (run.pair && byPair[run.pair]) return pairEdge(byPair[run.pair], { points: run.points, join: null });
            var members = run.members.map(function (id) { return byId[id]; }), first = members[0];
            var ends = members.map(function (w) { return [w.source, w.target]; });
            var writers = members.map(function (w) { return L.chain(m.nodes[w.from].namespace)[1] || w.from; });
            var title = 'Shared connection\n' + Array.from(new Set(writers)).join('\n');
            return { id: run.id, type: 'wire', source: first.source, target: first.target,
              sourceHandle: first.sourceHandle, targetHandle: first.targetHandle,
              className: 'bf-shared-run', ariaLabel: title, selectable: true, focusable: true, reconnectable: false,
              data: { parts: [run.points], title: title, members: run.members,
                cable: members.every(function (w) { return w.cable; }), closed: members.some(function (w) { return w.closed; }),
                shared: !run.terminal, ends: ends, lit: lights(ends, chosen) } };
          });
          var initialRoutes = r.initialRoutes.map(function (route) {
            var members = route.wires.map(function (id) { return byId[id]; }), first = members[0];
            var ends = members.map(function (w) { return [w.source, w.target]; });
            var record = route.route;
            var title = [record.source + ' → ' + record.destination, record.branch]
              .concat((record.pairs || []).map(function (pair) {
                return pair.source_field + ' → ' + pair.destination_field;
              })).filter(Boolean).join('\n');
            return { id: route.id, type: 'wire', source: first.source, target: first.target,
              sourceHandle: first.sourceHandle, targetHandle: first.targetHandle,
              className: 'bf-initial-route bf-cable-edge', selectable: false, focusable: false, reconnectable: false,
              domAttributes: { 'data-route-source': record.source, 'data-route-destination': record.destination,
                'data-route-branch': record.branch || '', 'data-route-count': route.count },
              data: { parts: [route.points], paint: r.paint[route.id], title: title, cable: true, initialTrunk: true,
                count: route.count, below: lowerHalf(first),
                ends: ends, lit: lights(ends, chosen) } };
          });
          var initialById = new Map(initialRoutes.map(function (edge) { return [edge.id, edge]; }));
          var initialShared = r.initialSharedRuns.map(function (run) {
            var routes = run.routes.map(function (id) { return initialById.get(id); }), first = routes[0];
            var ends = routes.flatMap(function (edge) { return edge.data.ends; });
            var title = 'Shared connection\n\n' + routes.map(function (edge) { return edge.data.title; }).join('\n\n');
            return { id: run.id, type: 'wire', source: first.source, target: first.target,
              sourceHandle: first.sourceHandle, targetHandle: first.targetHandle,
              className: 'bf-initial-shared-run', selectable: false, focusable: false, reconnectable: false,
              data: { parts: [run.points], title: title, shared: true, cable: run.cable, initialTrunk: true,
                ends: ends, lit: lights(ends, chosen) } };
          });
          setNodes(next); setEdges(wires.concat(pairs, sharedRuns, initialShared, initialRoutes));
          // Hidden descendants retain their expansion preference, but are not open in the drawing.
          p.report.open = Array.from(open).filter(function (ns) {
            return !!m.layers[ns] && L.chain(ns).every(function (ancestor) { return open.has(ancestor); });
          });
          p.report.selection = chosen;
          p.report.layouts += 1;
          if (place) appliedPlace.current = place.n;
          if (asked) appliedSelect.current = asked.n;
          var key = layoutKey;
          // the extent of what is drawn: the boxes as the pane draws them, a boundary marker with its label, which
          // stands beside its mark in the room the layout keeps for it, so that the opening (`begin`) shows the
          // label whole (N-I277, which amends N-I175)
          var extent = { left: Infinity, right: 0, bottom: 0 };
          Object.keys(built.boxes).forEach(function (id) {
            var at = r.place[id];
            if (!at) return;
            extent.left = Math.min(extent.left, at.ax);
            extent.right = Math.max(extent.right, at.ax + at.width);
            extent.bottom = Math.max(extent.bottom, at.ay + at.height);
          });
          // the frames whose borders the opening keeps clear of the region's far edge, a trellis graph's periods and
          // the stage view's open layers, each [left, right]; and every segment of the routes drawn, by which the
          // stage view's opening finds the top of what stands within the region's width (the fix wave Q3a, item 9)
          var frameSpans = Object.keys(built.boxes).filter(function (id) {
            var b = built.boxes[id];
            return b.type === 'layer' && b.open && !b.compact && r.place[id] && (!trellis || (PERIOD.test(b.namespace) && !b.layer.parent));
          }).map(function (id) { return [r.place[id].ax, r.place[id].ax + r.place[id].width]; });
          var segments = [];
          Object.keys(r.routes).concat(Object.keys(r.bundles)).forEach(function (id) {
            var points = r.routes[id] || (r.bundles[id] && r.bundles[id].points) || [];
            for (var i = 1; i < points.length; i++) segments.push([points[i - 1], points[i]]);
          });
          var drawn = { key: key, width: Math.min(r.width, extent.right + 2), height: Math.min(r.height, extent.bottom + 2), dir: flows,
            place: r.place, terminal: terminalLayer(m, r.place), left: isFinite(extent.left) ? extent.left : 0, right: extent.right,
            frames: frameSpans, segments: segments };
          shown.current = drawn;
          // the selected card unfolded by this layout, which the view pans to (the fix wave Q3a, item 8)
          var unfolded = unfold && unfold[0] !== lastUnfold.current ? grownCard(built, r, unfold[0] + L.LAYER_ENDING) : null;
          lastUnfold.current = unfold ? unfold[0] : null;
          if (place || fit.current !== key || state.opens[p.graph] || openingDue.current) {
            fit.current = key;
            state.opens[p.graph] = false;
            lastOpening.current = null;   // no opening is kept until begin applies this layout's opening
            // the opening stays due, with the box it centers, until begin applies it: a layout run
            // again before then, as a card unfolded by a selection runs it (AAS, L-D19), applies it
            if (!openingDue.current || place) openingDue.current = { at: place && chosen ? chosen : null };
            frame = requestAnimationFrame(function () {
              frame = requestAnimationFrame(function () {
                if (cancelled) return;
                var at = openingDue.current ? openingDue.current.at : null;
                openingDue.current = null;
                begin(drawn, at);
                if (unfolded) panTo(unfolded);
              });
            });
          } else if (unfolded) panTo(unfolded);
          if ((place || asked) && chosen && p.selected) p.selected({ nodeId: chosen, graphId: p.graph, origin: 'page' });
          if (p.processed) p.processed({ graphId: p.graph, boxes: next.length, wires: wires.length, ms: Math.round(performance.now() - started) });
        }).catch(refused);
      } catch (err) {
        refused(err);
      }
      return function () { cancelled = true; if (frame !== null) cancelAnimationFrame(frame); };
    }, [m, tick, flows, p.scope, p.select && p.select.n, p.place && p.place.n, addsKey, p.builders, unfoldKey, splitKey, orderKey]);

    /* The opening of the layout drawn (AAS, M-D15, which amends unit K's
       decisions K-D6 and K-D22 and unit L's Task 22; design pass 13 §2,
       rule 10, as the fix wave Q3a, item 9, amends it). A trellis graph
       that can be read whole, at READS or more, is fitted (`fitGraph`), its
       top TOP below the bar and its left edge on the text edge; otherwise
       the view shows its terminal period's layer, the layer of a period the
       graph shows alone among them, with what stands between that layer
       and the graph's nearer end, the boundary markers and their labels,
       so that each of those labels stands whole (N-I277): that box at the
       largest scale, at most 1 and at least READS, the trellis's reading
       scale, at which it fills the region's width less 10 px at each side,
       its top TOP below the bar, and its nearer end on the column's text
       edge: the drawing's left end, a backward graph's terminal-condition
       label, TEXT_EDGE inside the region's left, for a box in the graph's
       left half, and the drawing's right end, a forward graph's
       terminal-marker label, TEXT_EDGE inside the region's right, for a box
       in its right half (D20, D3); where the box is wider than the region
       less TEXT_EDGE at each side, its left edge TEXT_EDGE inside the
       region's, cut at the right: the marker's label in the left half, the
       layer's left edge, which holds its name, in the right half. Where the
       region's far edge would cut a frame with its border less than CLEAR
       px inside the region, the scale rises, at most to 1, by the least
       amount that puts that border outside (`clearOfCuts`). Any other
       graph, the stage view's, opens at the largest scale, at most 1 and at
       least STAGE_READS, the stage view's reading scale (Q-D7), at which
       its width fits the region less 10 px at each side, centered across
       where it fits whole and otherwise with its left edge 10 px inside the
       region's, the scale raised where a layer's frame would be so cut, and
       its top TOP below the bar, taken from the boxes and the wires that
       stand within the region's width at that scale (`visibleTop`; D26)
       (§2.3). A restored place centers its box, whose id is at, at the
       scale the graph opens at. The layout drawn holds the cards folded
       but for the selected one, since no scale unfolds a card (AAS, L-D25).
       The opening is kept with the viewport it set, which the size observer
       compares with the current one. */
    function begin(drawn, at) {
      var el = host.current;
      if (!el) return;
      var width = drawn.width, height = drawn.height, box = at ? drawn.place[at] : null;
      var W = el.clientWidth - 20, H = el.clientHeight - 20;
      var whole = Math.min(W / width, H / height);
      var terminal = drawn.terminal ? drawn.place[drawn.terminal] : null;
      // the box the opening shows: the terminal period's layer with what stands between it and the graph's nearer
      // end, the boundary markers and their labels, so that each of those labels stands whole (N-I277)
      if (terminal) {
        terminal = terminal.ax + terminal.width / 2 <= width / 2
          ? { ax: 0, ay: terminal.ay, width: terminal.ax + terminal.width, height: terminal.height }
          : { ax: terminal.ax, ay: terminal.ay, width: width - terminal.ax, height: terminal.height };
      }
      var fits = !!terminal && whole >= READS;
      // a trellis graph opens at the least READS, the stage view at the least STAGE_READS (Q-D7)
      var zoom = fits ? Math.min(1, whole) : Math.max(terminal ? READS : STAGE_READS, Math.min(1, W / (terminal ? terminal.width : width)));
      if (box) rf.setCenter(box.ax + box.width / 2, box.ay + box.height / 2, { zoom: zoom, duration: 0 });
      else if (fits) fitGraph();
      else if (terminal) {
        // the box keeps its scale and its top TOP below the bar, and its nearer end stands on the column's text edge:
        // a box in the graph's left half begins TEXT_EDGE inside the region's left with the drawing's left end, the
        // terminal condition's label, as `fitGraph` places its left edge, and one in the right half ends TEXT_EDGE
        // inside the region's right with the drawing's right end, the terminal marker's label; a box wider than the
        // region less TEXT_EDGE at each side has its left edge TEXT_EDGE inside the region's, cut at the right (the
        // fix wave Q3a, item 9; D20, D3)
        var nearer = terminal.ax + terminal.width / 2 <= width / 2, cut = terminal.width * zoom > el.clientWidth - 2 * TEXT_EDGE;
        var anchor = nearer ? drawn.left : cut ? terminal.ax : drawn.right, at = nearer || cut ? TEXT_EDGE : el.clientWidth - TEXT_EDGE;
        zoom = clearOfCuts(drawn.frames, anchor, at, zoom, el.clientWidth);
        rf.setViewport({ x: at - anchor * zoom, y: TOP - terminal.ay * zoom, zoom: zoom });
      } else {
        // the stage view, its top TOP below the bar, taken from the boxes and the wires that stand within the
        // region's width at the opening scale (the fix wave Q3a, item 9; D26), the scale raised where the far edge
        // would cut a layer's frame within CLEAR of its border
        var wide = width * zoom > W, right = drawn.dir === 'RIGHT', tall = height * zoom > H;
        var x = wide || (tall && right) ? 10 : el.clientWidth / 2 - width * zoom / 2;
        if (wide || (tall && right)) { zoom = clearOfCuts(drawn.frames, 0, 10, zoom, el.clientWidth); x = 10; }
        rf.setViewport({ x: x, y: TOP - visibleTop(drawn, x, zoom, el.clientWidth) * zoom, zoom: zoom });
      }
      // The setters above change React Flow's viewport before they return.
      lastOpening.current = { key: drawn.key, at: box ? at : null, view: rf.getViewport() };
    }

    /* The opening scale `zoom`, raised, at most to 1, by the least amount
       that puts outside the region the border of each frame of `frames`,
       each [left, right] on the graph, that the region's far edge would cut
       with that border less than CLEAR px inside it, the graph's point
       `anchor` held at `at` px from the region's left; the scale as it
       stands where no frame is so cut or the rise would pass 1 (the fix
       wave Q3a, item 9; D20, D26). */
    function clearOfCuts(frames, anchor, at, zoom, size) {
      for (var round = 0; round < 8; round++) {
        var raised = zoom;
        (frames || []).forEach(function (f) {
          var left = at + (f[0] - anchor) * zoom, right = at + (f[1] - anchor) * zoom;
          // cut by the right edge, its left border inside it by less than CLEAR, or by the left edge, its right border so
          if (left < size && right > size && left > size - CLEAR && f[0] > anchor) raised = Math.max(raised, (size - at) / (f[0] - anchor) + 1e-4);
          if (left < 0 && right > 0 && right < CLEAR && f[1] < anchor) raised = Math.max(raised, at / (anchor - f[1]) + 1e-4);
        });
        if (raised <= zoom + 1e-9 || raised > 1) return zoom;
        zoom = raised;
      }
      return zoom;
    }
    /* The top on the graph of what the drawing `drawn` shows within the
       region's width `size` with its left at `x` and its scale `zoom`: the
       least top of its boxes and of its wires' segments that stand within
       that width (the fix wave Q3a, item 9; D26). */
    function visibleTop(drawn, x, zoom, size) {
      var lo = -x / zoom, hi = (size - x) / zoom, top = Infinity;
      Object.keys(drawn.place).forEach(function (id) {
        var at = drawn.place[id];
        if (at.ax < hi && at.ax + at.width > lo) top = Math.min(top, at.ay);
      });
      (drawn.segments || []).forEach(function (seg) {
        if (Math.max(seg[0].x, seg[1].x) >= lo && Math.min(seg[0].x, seg[1].x) <= hi) top = Math.min(top, seg[0].y, seg[1].y);
      });
      return isFinite(top) ? top : 2;
    }

    function within(id, chosen) {
      for (var k = id; k; k = parents.current[k]) if (k === chosen) return true;
      return false;
    }
    // Whether a wire whose writing and reading boxes are `ends`, each
    // [source, target], one for a wire and one for each wire of a bundle,
    // crosses the border of the box `chosen`.
    function lights(ends, chosen) {
      return !!chosen && ends.some(function (end) { return within(end[0], chosen) !== within(end[1], chosen); });
    }
    useEffect(function () {
      setNodes(function (list) { return list.map(function (n) {
        return n.selected === (n.id === selection) ? n : Object.assign({}, n, { selected: n.id === selection });
      }); });
      setEdges(function (list) { return list.map(function (e) {
        var lit = lights(e.data.ends, selection) || (!!e.data.pairOf && e.data.pairOf === bundleChosen) ||
          !!(e.data.members && e.data.members.includes(joinChosen));
        return e.data.lit === lit ? e : Object.assign({}, e, { data: Object.assign({}, e.data, { lit: lit }) });
      }); });
    }, [selection, bundleChosen, joinChosen, nodes.length, edges.length]);
    // A wire whose record Python gives is a join wire: it takes a click and
    // focus, and each end its record names movable takes a drag (J-D33;
    // unit K's decision K-D23); the one selected is marked selected and
    // drawn after every other wire, so that where wires share a port the
    // press at that end takes the selected one, and every other wire takes
    // none. A bundle's wire whose record Python gives is the pair's (K-D5).
    // The bundle of a pair within a period keeps its own click (AAS, L-D25).
    useEffect(function () {
      setEdges(function (list) {
        var next = list.map(function (e) {
          if (e.data.bundle || e.data.members || e.data.initialTrunk) return e;
          var record = joinsByKey.get(e.data.key) || null;
          var chosen = !!record && e.id === joinChosen;
          if (e.data.record === record && !!e.selected === chosen) return e;
          return Object.assign({}, e, {
            selectable: !!record, focusable: !!record, selected: chosen,
            // Select a connector before exposing the drag targets on a shared path.
            reconnectable: chosen || !e.data.sharedControl ? reconnectEnds(record) : false,
            // a cable keeps its class beside a join wire's, and a wire of a bundle of a pair of periods its own
            // (design pass 10 §6; K-D5)
            className: [e.data.cable ? 'bf-cable-edge' : '', e.data.shared ? 'bf-cable-shared' : '',
              record ? (e.data.pair ? 'bf-join-wire bf-join-pair' : 'bf-join-wire') : ''].filter(Boolean).join(' ') || undefined,
            domAttributes: record ? { 'data-from': record.from, 'data-to': record.to } : undefined,
            // A target port may receive several branch laws; each selectable
            // arrow names only the pairs in its native record.
            data: Object.assign({}, e.data, { record: record }, record ? {
              // a cable's branch first, the cable drawing no label (the fix wave Q3a, item 4)
              title: [e.data.cable ? e.data.branch : null, e.data.label, record.join].filter(Boolean).join('\n'),
              // a cable keeps its label, its branch or the count of its wires (design pass 10 §6)
              join: e.data.cable ? e.data.join : e.data.join ? L.joinLabel(record.join) : ''
            } : {}) });
        });
        var at = next.findIndex(function (e) { return e.selected; });
        return at < 0 || at === next.length - 1 ? next : next.slice(0, at).concat(next.slice(at + 1), [next[at]]);
      });
    }, [joinsByKey, joinChosen, laid]);
    /* The join wire whose element holds the focus, by its edge's id, or
       null: a click on the wire gives its element the focus, a press or a
       focus elsewhere ends it. The layout drawn again for the pair's bundle
       once the click has selected the wire, and the wire drawn after every
       other, move its element among the wires, which takes the focus to the
       page's body; for 30 frames after each drawing of the wires the focus
       that stands on the body returns to the selected wire's element, so
       that Backspace or Delete reaches the region's handler (N-I274). */
    var focusedWire = useRef(null);
    useEffect(function () {
      function wireOf(event) {
        var target = event.target, edge = target && target.closest ? target.closest('.react-flow__edge.bf-join-wire') : null;
        return edge && host.current && host.current.contains(edge) ? edge.getAttribute('data-id') : null;
      }
      function focusIn(event) { focusedWire.current = wireOf(event); }
      function pressDown(event) { if (wireOf(event) !== focusedWire.current) focusedWire.current = null; }
      document.addEventListener('focusin', focusIn, true);
      document.addEventListener('pointerdown', pressDown, true);
      return function () {
        document.removeEventListener('focusin', focusIn, true);
        document.removeEventListener('pointerdown', pressDown, true);
      };
    }, []);
    useEffect(function () {
      var id = focusedWire.current, frames = 0, frame = null;
      if (!id || id !== joinChosen) return;
      function hold() {
        frame = null;
        if (!host.current || focusedWire.current !== id) return;
        var active = document.activeElement;
        if (!active || active === document.body) {
          var element = host.current.querySelector('.react-flow__edge.bf-join-wire[data-id="' + CSS.escape(id) + '"]');
          if (element) element.focus({ preventScroll: true });
        }
        if (++frames < 30) frame = requestAnimationFrame(hold);
      }
      hold();
      return function () { if (frame !== null) cancelAnimationFrame(frame); };
    }, [edges, laid, joinChosen]);

    function choose(nodeId) {
      if (!laid || laid.model !== m) return;
      kept.current.chosen[p.graph] = nodeId;
      p.report.selection = nodeId;
      setChoice(function (n) { return n + 1; });
      if (p.selected) p.selected({ nodeId: nodeId, graphId: p.graph, origin: 'user' });
    }

    /* The view of the graph shown, which the handle's view() and setView()
       read and restore for a preview (spec 0.4 §5.8; R-D29): React Flow's
       viewport and the selection. setView sets the viewport without
       animation and the selection as choose() sets it, a selection of null
       clearing it, and sends no event and begins no layout. */
    useEffect(function () {
      p.report.view = function () {
        var v = rf.getViewport();
        return { viewport: { x: v.x, y: v.y, zoom: v.zoom }, selection: p.report.selection };
      };
      p.report.setView = function (record) {
        var v = record.viewport;
        if (v) rf.setViewport({ x: v.x, y: v.y, zoom: v.zoom }, { duration: 0 });
        var nodeId = record.selection || null;
        kept.current.chosen[p.graph] = nodeId;
        p.report.selection = nodeId;
        setChoice(function (n) { return n + 1; });
      };
    });

    /* Reveal the target without animation, then wait at most 30 frames
       for React Flow to render it before focusing its own element (§2.4). */
    function focusItem(item, layout, pending) {
      if (!layout || layout.model !== m || !host.current) return;
      if (focusFrame.current !== null) cancelAnimationFrame(focusFrame.current);
      var id = item.box || item.toggle || item.stage, at = layout.read.place[id] || layout.read.builders[id];
      if (!at) return;
      var view = rf.getViewport(), el = host.current;
      var left = at.ax * view.zoom + view.x, top = at.ay * view.zoom + view.y;
      var pan = left < 0 || top < 0 || left + at.width * view.zoom > el.clientWidth || top + at.height * view.zoom > el.clientHeight;
      if (pan) rf.setCenter(at.ax + at.width / 2, at.ay + at.height / 2, { zoom: rf.getZoom(), duration: 0 });
      var frames = 0;
      function focus() {
        focusFrame.current = null;
        if (!host.current || (pending && pendingToggle.current !== pending)) return;
        var node = host.current.querySelector('.react-flow__node[data-id="' + CSS.escape(id) + '"]');
        var target = node && node.querySelector(item.stage ? '.bf-add-stage' : item.toggle ? '.bf-toggle'
          : ':scope > .bf-box, :scope > .bf-layer, :scope > .bf-builder, :scope > .bf-add-period, :scope > .bf-marker');
        // React Flow may still hold the outgoing Box or Layer after layout.
        var ready = target && (!pending || (target !== pending.outgoing &&
          target.getAttribute('aria-label') === (pending.open ? 'close ' : 'open ') + m.layers[pending.namespace].name));
        if (ready) {
          target.focus({ preventScroll: true });
          if (document.activeElement === target) {
            if (pending) pendingToggle.current = null;
            return;
          }
        }
        if (++frames < 30) focusFrame.current = requestAnimationFrame(focus);
      }
      if (pan || pending) focusFrame.current = requestAnimationFrame(focus); else focus();
    }
    useEffect(function () {
      var pending = pendingToggle.current;
      if (pending && pending.scope === p.scope && pending.graph === p.graph && laid && laid.model === m &&
          laid.open.has(pending.namespace) === pending.open) {
        focusItem(pending.item, laid, pending);
      }
    }, [laid]);
    useEffect(function () {
      return function () {
        if (focusFrame.current !== null) cancelAnimationFrame(focusFrame.current);
        pendingToggle.current = null;
      };
    }, [p.scope, p.graph]);

    function enterRegion(event) {
      if (!event.currentTarget.contains(event.target)) return;
      setInside(true);
      if (event.target !== event.currentTarget || !laid || laid.model !== m) return;
      // A focus that arrives by a pointer press, on the empty ground or on a
      // part of a card that takes no focus, focuses no item and moves the
      // view not at all (AAS, M-D16); one that arrives by the keyboard
      // focuses the selected box or the first item and reveals it (§2.4).
      if (pressed.current) return;
      var order = traversal(m, laid.open, laid.controls, laid.stages, laid.read);
      var first = order.find(function (item) { return item.box === selection; }) || order[0];
      if (first) focusItem(first, laid);
    }
    function leaveRegion(event) {
      if (!event.currentTarget.contains(event.relatedTarget)) setInside(false);
    }
    // Whether the box `id` is the layer of a stage occurrence of an open
    // period, `periods[h]/<key>___group___`, in the layout drawn, its card
    // closed or compact or the occurrence opened in full, which Backspace or
    // Delete removes from its period where a drop can be made (unit K's
    // decision K-D14; unit N, Task 5: the page draws every card compact,
    // which the layout counts among its open layers).
    function occurrenceLayer(id) {
      if (!id || !laid || laid.model !== m || id.slice(-L.LAYER_ENDING.length) !== L.LAYER_ENDING) return false;
      var ns = id.slice(0, -L.LAYER_ENDING.length), parts = ns.split('/');
      return parts.length === 2 && PERIOD.test(parts[0]) && !!m.layers[ns] && laid.open.has(parts[0]);
    }
    function keyInRegion(event) {
      if (event.altKey || event.ctrlKey || event.metaKey || !event.currentTarget.contains(event.target)) return;
      var node = event.target.closest('.react-flow__node');
      var isToggle = event.target.classList.contains('bf-toggle');
      var isStage = event.target.classList.contains('bf-add-stage');
      var control = event.target.classList.contains('bf-add-period') ? event.target : null;
      var sharedEdge = event.target.closest('.bf-shared-run');
      if (sharedEdge && ['Enter', ' ', 'Delete', 'Backspace'].includes(event.key)) {
        event.preventDefault();
        if (event.key === 'Enter' || event.key === ' ') {
          var edge = edges.find(function (e) { return e.id === sharedEdge.dataset.id; });
          if (edge) openShared(edge);
        }
        return;
      }
      // The keyboard's route of an item (§3.5): the arrow keys move among
      // the candidates, Enter sends the event dropped and Escape leaves;
      // any other key leaves and acts as it does outside the route.
      if (sending) {
        var candidates = candidatesFor(sending.item);
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
          event.preventDefault();
          var step = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : -1;
          var at = Math.max(0, Math.min(candidates.length - 1, sending.index + step));
          setSending({ item: sending.item, index: at });
          if (candidates[at]) showCandidate(candidates[at]);
          return;
        }
        endSending();
        if (event.key === 'Enter' || event.key === 'Escape') {
          event.preventDefault();
          var chosen = candidates[sending.index];
          if (event.key === 'Enter' && chosen && (chosen.control ? live : listing)) {
            sendDrop(sending.item, chosen.control || chosen.box);
          }
          return;
        }
      }
      if ((event.key === 'Backspace' || event.key === 'Delete') && chosenRecord.current) {
        // Backspace or Delete in the region removes the join wire selected
        // (J-D33; amendment 02, ruling 12); the record selected is one of
        // the list given with the reading, since a new list ends the
        // selection. A wire whose joins are all by equal names is not
        // removable, no entry writing it, and the keys do nothing there
        // (unit L, Task 15). A cable of the backward graph, where no gesture
        // acts (N-I192), is sent with no reading, as an occurrence selected
        // there is, and Python lists why under Problems (N-D12); in a
        // forward graph the keys send no cable with no reading (N-I273).
        event.preventDefault();
        if (p.reading && p.joins && chosenRecord.current.removable) {
          p.host.dispatchEvent(new CustomEvent('removed', { bubbles: true, detail: {
            reading: p.reading, join: idsOf(chosenRecord.current) } }));
        } else if (backward) {
          p.host.dispatchEvent(new CustomEvent('removed', { bubbles: true, detail: {
            reading: null, join: idsOf(chosenRecord.current) } }));
        }
      } else if ((event.key === 'Backspace' || event.key === 'Delete') && occurrenceLayer(selection) && (live || backward)) {
        // Backspace or Delete in the region removes the stage occurrence
        // selected from its period where a drop can be made (unit K's
        // decision K-D14); in the backward graph it sends the occurrence
        // with no reading, and Python lists why under Problems (unit N,
        // Task 5; N-D12); in a forward graph where no drop can be made the
        // keys send nothing, as before unit N (N-I273)
        event.preventDefault();
        p.host.dispatchEvent(new CustomEvent('removed', { bubbles: true, detail: {
          reading: live ? p.reading : null, occurrence: selection } }));
      } else if (event.key === 'Tab' && laid && laid.model === m) {
        var order = traversal(m, laid.open, laid.controls, laid.stages, laid.read);
        var index = order.findIndex(function (item) {
          return node && item[isStage ? 'stage' : isToggle ? 'toggle' : 'box'] === node.dataset.id;
        });
        if (index < 0 && event.target !== event.currentTarget) return;
        var next = index + (event.shiftKey ? -1 : 1);
        if (next >= 0 && next < order.length) { event.preventDefault(); focusItem(order[next], laid); }
      } else if (event.key === 'Enter' && control) {
        // Enter on a `+ period` control sends the event dropped with no item (§3.2)
        event.preventDefault();
        if (live) sendDrop(null, control.dataset.target);
      } else if (event.key === 'Enter' && node && !isToggle && !isStage) {
        event.preventDefault(); choose(node.dataset.id);
      } else if (event.key === 'Escape') {
        event.preventDefault(); choose(null); chooseJoin(null, null); chooseBundle(null); setPairing(null);
      } else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) event.preventDefault();
    }

    // Perch lines join the centers of the boxes that stand for their endpoints (§2.1).
    var lines = [];
    if (laid && laid.model === m && p.overlays_request) {
      var seen = new Set();
      (p.overlays_request.overlays || []).forEach(function (overlay) {
        (overlay.edges || []).forEach(function (edge) {
          var ends = [edge.sourceNodeId, edge.targetNodeId];
          if (!ends.every(function (id) { return !!m.nodes[id]; })) return;
          var ids = ends.map(function (id) {
            var at = L.shown(m, id, laid.open);
            return at.node || m.layers[at.layer].id;
          });
          var key = JSON.stringify([overlay.name, ids[0], ids[1]]);
          if (ids[0] === ids[1] || seen.has(key)) return;
          seen.add(key);
          var a = laid.read.place[ids[0]], b = laid.read.place[ids[1]];
          if (!a || !b) return;
          lines.push(h('line', { key: key, className: 'bf-perch', 'data-perch': overlay.name,
            x1: a.ax + a.width / 2, y1: a.ay + a.height / 2,
            x2: b.ax + b.width / 2, y2: b.ay + b.height / 2, stroke: colors[overlay.name] }));
        });
      });
    }
    // the line of a drag between two frames, while it lasts (K-D8)
    if (frameLine) {
      lines.push(h('line', { key: 'frame-line', className: 'bf-frame-line',
        x1: frameLine.from.x, y1: frameLine.from.y, x2: frameLine.to.x, y2: frameLine.to.y }));
    }
    var direction = flows === 'RIGHT' ? 'vertical' : 'horizontal';
    var target = p.controls && p.controls();
    var controls = target ? RD.createPortal(h(R.Fragment, null,
      iconButton(direction, turn),
      iconButton('zoom in', function () { rf.zoomIn({ duration: 0 }); }),
      iconButton('zoom out', function () { rf.zoomOut({ duration: 0 }); }),
      iconButton('fit', fitGraph)), target) : null;
    // The button `stages` at the graph's head (§3.5), drawn where the graph
    // lays out the `+ period` controls and pressed while the stage list can
    // open, a reading that stands refused included (unit L, Task 14).
    var head = laidAdds && p.head ? p.head() : null;
    // the head's list is open, and not a period's (unit K's decision K-D14)
    var headList = listOpen && listPeriod === null;
    var stagesButton = head ? RD.createPortal(h('button', { ref: stagesElement, type: 'button', disabled: !listing,
      className: 'bl-text-button bl-stages-button' + (headList ? ' bl-active' : ''), 'aria-expanded': headList,
      onClick: function () {
        listAnchor.current = stagesElement.current;
        setSending(null); setPairing(null); setListPeriod(null); setListOpen(!headList);
      } }, STAGES), head) : null;
    // a list opened for another period is a new list, whose first item takes
    // the focus; it stands beside the button that opened it, within the
    // region (design pass 10 §7)
    var list = listOpen && listing ? h(StageList, { key: listPeriod === null ? 'head' : 'periods[' + listPeriod + ']',
      stages: p.stages, period: listPeriod, listed: listedIn, dragging: !!dragItem, holder: listElement,
      chosen: lastChosen, place: function (element) { placeList(element, listAnchor.current, host.current); },
      onPick: pickItem, onSend: sendToPeriod, onFolder: sendFolder, onClose: closeList, onDrag: dragList }) : null;
    // The list of a drag between two frames (K-D8), drawn while both frames
    // hold the ports it lists and the region holds the record of a reading;
    // its button `Join` sends the event connected with the ticked pairs.
    // The list of the move of an end of a join wire of several field pairs
    // (K-D23), drawn while the stage occurrence the end was dropped on holds
    // ports of the end's side and the region holds the record of a reading:
    // a row for each field pair of the wire, the field of the end kept
    // beside a select of that occurrence's ports, ticked where the pair's
    // `readers` or `writers` name one, and for a moved reading end a row
    // for each record of the wire's `others`, the writer's other unjoined
    // continuation fields, ticked where its `readers` name a port (unit L,
    // Task 19); its button `Join` sends the event moved with the ticked
    // pairs, each field pair's with the port it leaves and each other row's
    // with none.
    function pairProps(at) {
      if (!at || !p.reading) return null;
      if (at.cable) {
        // the cable's list (design pass 10 §7): one row for each arrival field the destination holds, with a select
        // of the branch's continuation fields, each offered in one row, since a continuation field joins one
        // arrival field; a row is pre-filled where the package would select the pair on its own, the one candidate
        // its selection names for the arrival field (`equal`, which Python gives); the ticked rows are counted
        // before the foot
        var sourceFrame = frames.get(at.source.ns), destinationFrame = frames.get(at.destination);
        if (!sourceFrame || !destinationFrame) return null;
        var branchFields = sourceFrame.fields.filter(function (f) { return (f.branch || '') === (at.source.branch || ''); });
        var byReading = {}, byWriting = {};
        ((at.record && at.record.fields) || []).forEach(function (f) { byReading[f.reading] = f.writing; byWriting[f.writing] = f.reading; });
        // a cable dropped on the occurrence its moved end already stands on keeps its pairs: each row is pre-filled
        // with the continuation field the cable pairs to it now, which the package selects (design pass 10 §7)
        var own = !!at.record && (at.end === 'reading' ? at.destination === at.record.to
          : at.source.ns === at.record.from && (at.source.branch || '') === (at.record.branch || ''));
        var rows = destinationFrame.reads.map(function (r) {
          var proposed = branchFields.filter(function (f) { return (f.equal || {})[at.destination] === r.id; });
          var held = own && byReading[r.id] && branchFields.some(function (f) { return f.id === byReading[r.id]; }) ? byReading[r.id] : '';
          return { id: r.id, field: r.field, set: r.set || '', proposed: held || (proposed.length === 1 ? proposed[0].id : ''), replaced: byReading[r.id] || null };
        });
        var lost = ((at.record && at.record.fields) || []).map(function (f) { return f.field + ': ' + f.arrival; });
        return { key: 'cable ' + at.source.ns + ' ' + at.source.branch + ' ' + at.destination + ' ' + at.end,
          head: at.source.ns + ' → ' + at.destination, end: 'writing', cable: true, options: branchFields, rows: rows,
          // what the moved end's pairs leave: for a reading end the old reading ports of the branch's fields, and
          // for a writing end the old writing ports of the destination's fields
          replacedBy: at.end === 'reading' ? byWriting : byReading, replacedOf: at.end === 'reading' ? 'source' : 'row',
          leaves: at.record ? (at.end === 'reading' ? at.record.to : at.record.from) : '', lost: at.record ? lost : [] };
      }
      if (!at.record) {
        var writer = frames.get(at.writer), reader = frames.get(at.reader);
        return writer && reader ? { key: at.writer + ' ' + at.reader, head: at.writer + ' → ' + at.reader, end: 'reading',
          options: reader.reads, rows: writer.writes.map(function (w) {
            return { id: w.id, field: w.field, set: w.set || '', proposed: (w.pairs || {})[at.reader] || '' };
          }) } : null;
      }
      var record = at.record, frame = frames.get(at.at), reading = at.end === 'reading';
      var options = frame ? (reading ? frame.reads : frame.writes) : [];
      // the wire's field pairs, each with the entry it writes now, then, for
      // a moved reading end, the writer's other unjoined continuation fields
      // (unit L, Task 19)
      var moved = (record.fields || []).map(function (f) {
        var lost = f.field + ': ' + f.arrival;
        return reading ? { id: f.writing, field: f.field, set: f.field_set || '', proposed: (f.readers || {})[at.at] || '', replaced: f.reading, lost: lost }
          : { id: f.reading, field: f.arrival, set: f.arrival_set || '', proposed: (f.writers || {})[at.at] || '', replaced: f.writing, lost: lost };
      });
      var others = reading ? (record.others || []).map(function (o) {
        return { id: o.writing, field: o.field, set: o.field_set || '', proposed: (o.readers || {})[at.at] || '' };
      }) : [];
      return options.length ? { key: wireKey(record.source, record.sourceHandle, record.target, record.targetHandle) + ' ' + at.end + ' ' + at.at,
        head: reading ? record.from + ' → ' + at.at : at.at + ' → ' + record.to, end: at.end, options: options,
        leaves: reading ? record.to : record.from, rows: moved.concat(others) } : null;
    }
    function closePairs() {
      if (host.current) host.current.focus({ preventScroll: true });
      setPairing(null);
    }
    function joinPairs(pairs) {
      var q = latest.current, at = pairing;
      closePairs();
      if (!at || !q.reading) return;
      var detail;
      if (at.cable) {
        // the whole cable's write (design pass 10 §7): a move names the cable and releases every pair of its route,
        // `cable`; a new cable from an unjoined branch is the join of two frames (K-D8)
        detail = at.record ? { reading: q.reading, join: idsOf(at.record), end: at.end, pairs: pairs, cable: true }
          : { reading: q.reading, source: at.source.ns + L.LAYER_ENDING, target: at.destination + L.LAYER_ENDING, pairs: pairs, cable: true };
      } else {
        detail = at.record ? { reading: q.reading, join: idsOf(at.record), end: at.end, pairs: pairs }
          : { reading: q.reading, source: at.writer + L.LAYER_ENDING, target: at.reader + L.LAYER_ENDING, pairs: pairs };
      }
      q.host.dispatchEvent(new CustomEvent(at.record ? 'moved' : 'connected', { bubbles: true, detail: detail }));
    }
    var pairListProps = pairProps(pairing);
    // a list a drop on a port opened stands beside that port, within the region, and where the region no longer
    // draws the port, at the region's top-left as the list of a drag between frames does (design pass 10 §7; K-D8)
    var drop = pairing && pairing.drop;
    var placePairs = drop ? function (element) {
      var port = dropElement(host.current, drop);
      if (port) placeList(element, port, host.current);
      else element.style.top = element.style.left = element.style.maxHeight = '';
    } : null;
    var pairList = pairListProps ? h(PairList, Object.assign({ onJoin: joinPairs, onClose: closePairs, place: placePairs }, pairListProps)) : null;
    var sharedOptions = (sharedChoice ? sharedChoice.keys : []).map(function (key) {
      return { key: key, record: joinsByKey.get(key), edge: edges.find(function (e) { return e.data.key === key; }) };
    }).filter(function (choice) { return choice.record && choice.edge; });
    var sharedDialog = sharedOptions.length ? h('div', { ref: sharedList, className: 'bf-stage-list bf-shared-list',
      role: 'dialog', 'aria-label': 'Shared connection', onKeyDown: function (event) {
        event.stopPropagation();
        if (event.key === 'Escape') { event.preventDefault(); closeShared(); }
      } },
      listHead(LIST_ICONS.join, h('span', { className: 'bf-list-name' }, 'Shared connection'), null, closeShared),
      sharedOptions.map(function (choice) {
        var record = choice.record, route = record.from + ' → ' + record.to;
        var detail = [record.branch, record.join].filter(Boolean).join(' · ');
        return h('button', { key: choice.key, type: 'button', className: 'bf-stage-item',
          title: [route, detail].filter(Boolean).join('\n'), onClick: function () {
            setSharedChoice(null);
            chooseJoin(choice.edge.id, record);
            focusEdge(choice.edge.id);
          } }, h('span', { className: 'bf-stage-key' }, route),
          detail ? h('span', { className: 'bf-stage-model' }, detail) : null);
      })) : null;

    return h('div', { ref: host, className: 'bf-region' + (dragging || frameLine ? ' bf-connecting' : ''), style: { position: 'absolute', inset: 0 },
      tabIndex: inside ? -1 : 0, onFocus: enterRegion, onBlur: leaveRegion, onKeyDown: keyInRegion,
      onPointerDownCapture: pressInRegion, onClickCapture: clickInRegion,
      onKeyDownCapture: function () { pressed.current = false; },
      onPointerMoveCapture: pointerOverPorts, onPointerLeave: function () {
        markNearest(null);
        if (nearestEnd.current) nearestEnd.current.removeAttribute('data-nearest');
        nearestEnd.current = null;
      } },
      h(Gesture.Provider, { value: gesture }, h(RF.ReactFlow, {
        nodes: nodes, edges: edges, nodeTypes: nodeTypes, edgeTypes: edgeTypes,
        onNodesChange: function (changes) { onNodesChange(changes.filter(function (c) { return c.type !== 'select'; })); },
        // React Flow selects a join wire or the bundle of a pair within a
        // period on its click; the region keeps the selection itself and
        // selects no other wire
        onEdgesChange: function (changes) {
          changes.forEach(function (c) {
            var edge = c.type === 'select' && c.selected ? edges.find(function (e) { return e.id === c.id; }) : null;
            if (edge) chooseEdge(edge);
          });
          onEdgesChange(changes.filter(function (c) { return c.type !== 'select'; }));
        },
        // Each port's handle says whether a drag can take it. nodesConnectable
        // holds only while the region holds unjoined ports, since React Flow
        // draws the line of a drag only while it holds; the boxes read
        // nothing else that it sets.
        nodesDraggable: false, nodesConnectable: enabled.size > 0, nodesFocusable: false, disableKeyboardA11y: true,
        isValidConnection: admits, onConnect: connect, connectOnClick: false,
        // a drag from a cable port is the cable drag of design pass 10 §7 until it ends
        onConnectStart: function (_event, params) {
          ended.current = false;
          cableDrag.current = cableDragFrom(params.nodeId, params.handleId);
          setCableState(cableDrag.current);
        },
        onConnectEnd: function () { cableDrag.current = null; setCableState(null); },
        // an end of a join wire dragged: React Flow names the end kept
        onReconnectStart: function (_event, edge, kept) {
          sharedPress.current = null;
          ended.current = false;
          moving.current = { record: edge.data && edge.data.record, end: kept === 'target' ? 'writing' : 'reading' };
        },
        onReconnect: move,
        onReconnectEnd: function () { moving.current = null; },
        // an end of a join wire is taken in a circle of radius RECONNECT px beside its port,
        // in the flow's units, and on the screen while its wire is selected (K-D23, K-D27)
        reconnectRadius: RECONNECT,
        ariaLabelConfig: {
          'node.a11yDescription.default': 'Press Enter to select a box or Escape to clear the selection.',
          'edge.a11yDescription.default': ''
        },
        elementsSelectable: true, edgesFocusable: false,
        edgesReconnectable: false, deleteKeyCode: null, selectionKeyCode: null, multiSelectionKeyCode: null,
        selectionOnDrag: false, zoomOnDoubleClick: false, minZoom: MIN_ZOOM, maxZoom: 1,
        attributionPosition: 'bottom-right', onlyRenderVisibleElements: nodes.length > 150,
        // a `+ period` control is no box of the graph JSON: a click on it
        // selects nothing and a double click opens nothing
        onNodeClick: function (_e, node) { if (node.type !== 'add') { choose(node.id); chooseJoin(null, null); chooseBundle(null); } },
        // a click on the graph's ground closes the list of a drag between frames (K-D8) and ends the selection
        // of a bundle (AAS, L-D25)
        onPaneClick: function () { setPairing(null); chooseBundle(null); },
        onNodeDoubleClick: function (_e, node) {
          if (node.type !== 'add' && laid && laid.model === m && p.opened) p.opened({ nodeId: node.id, graphId: p.graph });
        },
        onDragEnter: dragOver, onDragOver: dragOver, onDrop: dropItem, onDragLeave: leaveDrag
      }, h(RF.ViewportPortal, null, h('svg', { style: { position: 'absolute', overflow: 'visible', pointerEvents: 'none' } }, lines)))),
      list, pairList, sharedDialog, controls, stagesButton);
  }

  /* One control of the canvas's foot by its word (FOOT_CONTROLS; design
     pass 8 §§3 and 6): VSCode Elements' toolbar button drawing its Codicon
     in a 24-pixel target, with its accessible name as its hover; a layout's
     button, .bl-layout-button, carries in data-layout the layout a click
     turns to, and a zoom's, .bl-zoom-button, its word in data-zoom. */
  function iconButton(word, action) {
    var layout = word === 'horizontal' || word === 'vertical', control = FOOT_CONTROLS[word];
    return h('vscode-toolbar-button', { key: layout ? 'direction' : word,
      class: 'bl-graph-icon ' + (layout ? 'bl-layout-button' : 'bl-zoom-button'),
      'data-zoom': layout ? undefined : word, 'data-layout': layout ? word : undefined,
      icon: control[0], label: control[1], title: control[1], onClick: action });
  }

  function mount(hostElement, props) {
    var properties = {
      period: '--bl-graph-period', stage: '--bl-graph-stage', builder: '--bl-graph-builder', 'sub-builder': '--bl-graph-sub-builder',
      arrival: '--bl-graph-arrival', decision: '--bl-graph-decision', continuation: '--bl-graph-continuation',
      output: '--bl-graph-output', refused: '--bl-graph-refusal', ring: '--bl-graph-ring'
    };
    var computed = getComputedStyle(hostElement), colors = {};
    Object.keys(properties).forEach(function (name) { colors[name] = computed.getPropertyValue(properties[name]).trim(); });
    var report = { open: [], selection: null, layouts: 0 };
    var current = Object.assign({}, props);
    var root = RD.createRoot(hostElement);
    function draw() {
      root.render(h(RF.ReactFlowProvider, null, h(Pane, { p: Object.assign({}, current, { report: report, host: hostElement }), colors: colors })));
    }
    draw();
    return {
      update: function (changes) { current = Object.assign({}, current, changes); draw(); },
      unmount: function () { root.unmount(); },
      collection: function () { return current.collection ? JSON.parse(JSON.stringify(current.collection)) : null; },
      reading: function () { return current.reading ? JSON.parse(JSON.stringify(current.reading)) : null; },
      joins: function () { return current.joins ? JSON.parse(JSON.stringify(current.joins)) : null; },
      // the recipe's order of the stage keys the page gives, by which the layout ranks every period's occurrences (the
      // fix wave Q3a, item 2), or null
      stageOrder: function () { return current.stage_order ? current.stage_order.slice() : null; },
      openLayers: function () { return report.open.slice(); },
      selection: function () { return report.selection; },
      layouts: function () { return report.layouts; },
      // {viewport: {x, y, zoom}, selection} of the graph shown, null before the region draws
      view: function () { return report.view ? report.view() : null; },
      // restores such a record with no event and no layout (R-D29)
      setView: function (record) { if (report.setView && record) report.setView(record); }
    };
  }

  window.BellmanFlow = { mount: mount, measure: measure };
})();
