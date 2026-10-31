<template>
  <div class="bl-view-host" :class="{ 'bl-stale': stale }" ref="host"></div>
</template>

<script>
// The graph region (model interface specification 0.4, §§2 and 4) in a Vue 3
// component of Solara's component_vue: the graph JSON drawn by React Flow
// after ELK lays it out. The component loads, once per page, React Flow's
// base stylesheet, ELK's unchanged file and the graph's bundle from
// bellman_workbench/public/flow/, which Solara serves at /static/assets/flow/, waits for the
// page's fonts, and mounts window.BellmanFlow in its host; a later change of
// a property is given to the region mounted. flow-canvas.js states at its
// head what the region does with each property.
//
// Properties, each set from Python: collection, overlays_request, layers,
// graph, select, stale, scope, place and styles (G-D2); unjoined, reading,
// stages, adds and joins, which Python gives in the forward trellis graph
// alone (spec 0.4 §§3.2, 3.5, 3.6; J-D33); builders, the record of each
// builder's pair of perches, which Python gives in either trellis graph
// (AAS, L-D7); and stage_order, the recipe's order of the stage keys, which
// Python gives in either trellis graph and by which the region stands every
// period's occurrences in rows (the fix wave Q3a of unit Q, item 2).
// Events, each a call of a Python function and a DOM event of the same name
// dispatched on the host, whose detail is the record (G-D13):
//   selected({nodeId, graphId, origin})
//   processed({graphId, boxes, wires, ms})
//   opened({nodeId, graphId})
//   refused({graphId, sentence})
// The events connected({reading, source, target, sourceHandle, targetHandle}),
// or connected({reading, source, target, pairs}) for the join of two frames
// (unit K, K-D8), dropped({item, kind, target, reading}), join-chosen({reading, join}),
// removed({reading, join}) and moved({reading, join, end, handle}) are DOM
// events the region dispatches on the host, bubbling, which this component
// hears there and passes to Python, join-chosen as join_chosen (J-D17,
// J-D33).
// The DOM event input-edited, which the editor dispatches on the document
// with the path of the file typed in (brief rule 6), gives the region no
// unjoined ports, no stage list and no join wires where that path is among
// the inputs of reading, until Python gives reading again (spec 0.4 §3.3). The region
// draws the button `stages` in the element .bl-graph-head of the view's bar,
// the graph's head (spec 0.4 §3.5).
// The host carries `bellmanFlow`, the handle `mount` answers, which the page
// tests and goto.vue read (R-D29, which widens G-D13).

module.exports = {
  async mounted() {
    // the host the region's event connected is heard on
    this.eventHost = this.$refs.host;
    this.eventHost.addEventListener("connected", this.hearConnected);
    this.eventHost.addEventListener("dropped", this.hearDropped);
    this.eventHost.addEventListener("join-chosen", this.hearJoinChosen);
    this.eventHost.addEventListener("removed", this.hearRemoved);
    this.eventHost.addEventListener("moved", this.hearMoved);
    document.addEventListener("input-edited", this.hearInputEdited);
    try {
      await this.loadFiles();
    } catch (error) {
      this.loadRefusal = error.message;
      this.send("refused", { graphId: this.graph, sentence: this.loadRefusal });
      return;
    }
    // the faces the layout measures, a stage's name among them in IBM Plex Mono at weight 500 (design pass 10 §5)
    await Promise.allSettled([
      document.fonts.load('16px "IBM Plex Mono"'),
      document.fonts.load('500 16px "IBM Plex Mono"'),
      document.fonts.load('16px "STIX Two Math"', "𝑉≻∘"),
    ]);
    const host = this.$refs.host;
    this.region = window.BellmanFlow.mount(host, this.properties());
    host.bellmanFlow = this.region;
  },
  unmounted() {
    if (this.eventHost) {
      this.eventHost.removeEventListener("connected", this.hearConnected);
      this.eventHost.removeEventListener("dropped", this.hearDropped);
      this.eventHost.removeEventListener("join-chosen", this.hearJoinChosen);
      this.eventHost.removeEventListener("removed", this.hearRemoved);
      this.eventHost.removeEventListener("moved", this.hearMoved);
    }
    document.removeEventListener("input-edited", this.hearInputEdited);
    if (this.region) this.region.unmount();
    this.region = null;
  },
  watch: {
    collection(value) { this.give("collection", value); },
    overlays_request(value) { this.give("overlays_request", value); },
    layers(value) { this.give("layers", value); },
    graph(value) { this.give("graph", value); },
    select(value) { this.give("select", value); },
    stale(value) { this.give("stale", value); },
    scope(value) { this.give("scope", value); },
    place(value) { this.give("place", value); },
    styles(value) { this.give("styles", value); },
    unjoined(value) { this.give("unjoined", value); },
    stages(value) { this.give("stages", value); },
    adds(value) { this.give("adds", value); },
    joins(value) { this.give("joins", value); },
    builders(value) { this.give("builders", value); },
    stage_order(value) { this.give("stage_order", value); },
    // a new reading gives the region Python's ports, stage list and join
    // wires again, which an input edit took away
    reading(value) {
      if (this.region) {
        this.region.update({
          reading: this.plain(value),
          unjoined: this.plain(this.unjoined),
          stages: this.plain(this.stages),
          adds: this.plain(this.adds),
          joins: this.plain(this.joins),
        });
      }
    },
  },
  methods: {
    // The URL of a file of the package's public/ folder, which Solara serves
    // at <root path>/static/assets/.
    staticUrl(path) {
      const root = (window.solara && window.solara.rootPath) || "";
      return `${root}/static/assets/${path}`;
    },
    // The graph assets, loaded once per page: one promise on window, which
    // every region of the page awaits.
    loadFiles() {
      if (!window.bellmanFlowLoading) {
        window.bellmanFlowLoading = (async () => {
          this.loadStylesheet("bellman-flow-base", "flow/base.css");
          const preload = document.createElement("link");
          preload.rel = "preload";
          preload.as = "script";
          preload.href = this.staticUrl("flow/bellman-flow.js");
          document.head.appendChild(preload);
          const font = document.createElement("link");
          font.rel = "preload";
          font.as = "font";
          font.type = "font/woff2";
          font.crossOrigin = "anonymous";
          font.href = this.staticUrl("flow/stix-two-math-latin-400-normal.woff2");
          document.head.appendChild(font);
          await this.loadScript("bellman-elk-script", "flow/elk.bundled.js");
          await this.loadScript("bellman-flow-script", "flow/bellman-flow.js");
        })();
      }
      return window.bellmanFlowLoading;
    },
    loadStylesheet(id, path) {
      if (document.getElementById(id)) return;
      const link = document.createElement("link");
      link.id = id;
      link.rel = "stylesheet";
      link.href = this.staticUrl(path);
      document.head.appendChild(link);
    },
    // A script loaded with require.js's `define.amd` set aside: the UMD head
    // of elk.bundled.js would otherwise call an anonymous define, which
    // require.js refuses, and set no window.ELK.
    loadScript(id, path) {
      return new Promise((resolve, reject) => {
        const define = window.define;
        const amd = define ? define.amd : undefined;
        if (define) define.amd = undefined;
        const restore = () => {
          if (define) define.amd = amd;
        };
        const script = document.createElement("script");
        script.id = id;
        script.src = this.staticUrl(path);
        script.addEventListener("load", () => {
          restore();
          resolve();
        });
        script.addEventListener("error", () => {
          restore();
          reject(new Error(`${path} did not load`));
        });
        document.head.appendChild(script);
      });
    },
    // Every property as a plain value, and the four callbacks.
    properties() {
      const names = [
        "collection", "overlays_request", "layers", "graph", "select", "stale", "scope", "place", "styles",
        "unjoined", "reading", "stages", "adds", "joins", "builders", "stage_order",
      ];
      const values = {};
      for (const name of names) values[name] = this.plain(this[name]);
      values.selected = (record) => this.send("selected", record);
      values.processed = (record) => this.send("processed", record);
      values.opened = (record) => this.send("opened", record);
      values.refused = (record) => this.send("refused", record);
      values.controls = () => (this.$el && this.$el.closest(".bl-view")
        ? this.$el.closest(".bl-view").querySelector(".bl-graph-icons") : null);
      values.head = () => (this.$el && this.$el.closest(".bl-view")
        ? this.$el.closest(".bl-view").querySelector(".bl-graph-head") : null);
      return values;
    },
    give(name, value) {
      if (this.region) this.region.update({ [name]: this.plain(value) });
      // A later collection cannot draw while the same script is absent (G-D9).
      else if (name === "collection" && this.loadRefusal) {
        this.send("refused", { graphId: this.graph, sentence: this.loadRefusal });
      }
    },
    // The region's event connected, heard on the host: the call of the
    // Python function (J-D17).
    hearConnected(event) {
      this.connected(event.detail);
    },
    // The region's event dropped, heard on the host: the call of the Python
    // function (J-D17).
    hearDropped(event) {
      this.dropped(event.detail);
    },
    // The region's events of a join wire, heard on the host: the calls of
    // the Python functions (J-D33).
    hearJoinChosen(event) {
      this.join_chosen(event.detail);
    },
    hearRemoved(event) {
      this.removed(event.detail);
    },
    hearMoved(event) {
      this.moved(event.detail);
    },
    // An edit of an input of the reading drawn takes the region's unjoined
    // ports, its stage list and its join wires away at once, so that no
    // connector, no drop and no removal can be made (spec 0.4 §3.3).
    hearInputEdited(event) {
      const inputs = (this.reading && this.reading.inputs) || [];
      if (this.region && event.detail && inputs.includes(event.detail.path)) {
        this.region.update({ unjoined: [], stages: null, joins: [] });
      }
    },
    // An event: the call of the Python function, then the DOM event on the
    // host (G-D13).
    send(name, record) {
      this[name](record);
      this.$refs.host.dispatchEvent(new CustomEvent(name, { detail: record }));
    },
    // A plain copy of a value: the properties are reactive proxies.
    plain(value) {
      return value == null ? value : JSON.parse(JSON.stringify(value));
    },
  },
};
</script>
