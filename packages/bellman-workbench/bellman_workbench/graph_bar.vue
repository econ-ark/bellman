<template>
  <span hidden></span>
</template>

<script>
// The measure of the graph bar (design pass 13 §4; the fix wave Q3b of
// unit Q, item 16; D22), in a Vue 3 component of Solara's component_vue,
// rendered as the last child of the graph bar's .bl-graph-tools, an
// element not displayed, which is no item of the bar's row and leaves
// Problems the bar's last element. Python knows no
// width, so the browser measures whether the bar's items, the region's
// name `Semantic graph` among them, fit one row: with the name drawn, the
// items of .bl-graph-tools wrap where they do not, an item then standing
// a row below the others. Where they do not fit, the bar carries
// data-crowded, and brand.css then draws no name, which stays the
// region's heading for assistive technology, so that the bar keeps one
// row of 36 px and the canvas begins under it; the items that still do
// not fit wrap as before (amendment 02 ruling 5). One measure draws the
// name, reads the rows and sets the attribute in one task, before the
// browser paints, so that the name is never seen to wrap. The measure is
// taken again at each change of the graph column's size, of the size of
// an item or of Problems beside them, of the bar's items, and once the
// page's fonts have loaded; the name's own size is not observed, since
// the measure changes it.
module.exports = {
  mounted() {
    this.resizes = new ResizeObserver(() => this.measure());
    this.changes = new MutationObserver(() => this.observe());
    const tools = this.tools();
    if (tools) {
      this.changes.observe(tools, { subtree: true, childList: true, characterData: true });
    }
    this.observe();
    if (document.fonts) document.fonts.ready.then(() => this.measure());
  },
  unmounted() {
    this.resizes.disconnect();
    this.changes.disconnect();
  },
  methods: {
    // The bar, .bl-graph-bar, that holds this component.
    bar() {
      return this.$el && this.$el.closest ? this.$el.closest(".bl-graph-bar") : null;
    },
    // The bar's .bl-graph-tools, which holds its items but Problems.
    tools() {
      const bar = this.bar();
      return bar ? bar.querySelector(".bl-graph-tools") : null;
    },
    // The items of the bar's row as its flex layout places them: each
    // child of .bl-graph-tools, a child displayed as contents counted by
    // its own children, and none displayed as none.
    items(tools) {
      const found = [];
      const walk = (element) => {
        for (const child of element.children) {
          const display = getComputedStyle(child).display;
          if (display === "contents") walk(child);
          else if (display !== "none") found.push(child);
        }
      };
      walk(tools);
      return found;
    },
    // The graph column, Problems and every item but the name observed for
    // their sizes, then the measure taken.
    observe() {
      const bar = this.bar();
      const tools = this.tools();
      this.resizes.disconnect();
      if (!bar || !tools) return;
      this.resizes.observe(bar.closest(".bl-view") || bar);
      const problems = bar.querySelector(":scope > .bl-errors");
      if (problems) this.resizes.observe(problems);
      for (const item of this.items(tools)) {
        if (!item.classList.contains("bl-graph-name")) this.resizes.observe(item);
      }
      this.measure();
    },
    // Whether the items fit one row with the name drawn: the attribute
    // removed, the items' middles read, which lays the bar out, and the
    // attribute set again where one middle stands half a row or more from
    // another.
    measure() {
      const bar = this.bar();
      const tools = this.tools();
      if (!bar || !tools) return;
      bar.removeAttribute("data-crowded");
      const middles = this.items(tools).map((item) => {
        const box = item.getBoundingClientRect();
        return (box.top + box.bottom) / 2;
      });
      const half = bar.getBoundingClientRect().height > 0 ? 18 : 0;
      if (middles.length > 1 && half && Math.max(...middles) - Math.min(...middles) >= half) {
        bar.setAttribute("data-crowded", "");
      }
    },
  },
};
</script>
