<template>
  <span hidden></span>
</template>

<script>
// The measure of the trellis view's status line (spec 0.4 §5.7; design
// pass §1 item 10 and §5 item 6; unit K, Task 6), in a Vue 3 component of
// Solara's component_vue, rendered in the foot, .bl-status, while the
// trellis view is shown. Python knows no width, so the browser measures
// which of the texts in `lines` fit in the room the visible status line,
// .bl-status-summary, leaves the trellis's line, .bl-trellis-status: the
// summary's width less the widths of its other children and the gaps
// between its children. Each text's width is that of a probe, an element
// outside the window drawn in the face of .bl-trellis-status that holds the
// text, its first part, the file, in the face of the file's words, and each
// separator ` · ` counted as the gap the line draws between two parts in
// its place (design pass 8 §6), so that the measure is the same whatever
// the visible line holds.
// Another child's width is the larger of its box and its content, since
// the note of `paper` or `notebook` narrows while the line overflows. The
// answer is sent to Python where it changes. The measure is taken again at
// each change of `lines`, of the foot's size and of the summary's contents,
// and once the page's fonts have loaded.
//
// Properties, each set from Python:
//   lines       the texts the visible line would print, each longer than
//               the one before: the line with the bindings applied, then
//               the whole line; the last gesture's note included in each
// Events, each a call of a Python function:
//   fit(count)  the number of the texts of `lines`, counted from the first,
//               that fit, where the answer changes
module.exports = {
  watch: {
    lines() {
      this.$nextTick(() => this.measure());
    },
  },
  mounted() {
    // the probe, outside the window and not drawn
    this.probe = document.createElement("span");
    this.probe.setAttribute("aria-hidden", "true");
    Object.assign(this.probe.style, {
      position: "absolute",
      left: "-100000px",
      top: "0",
      visibility: "hidden",
      whiteSpace: "pre",
    });
    document.body.append(this.probe);
    // the answer last sent to Python, none before the first measure
    this.sent = null;
    this.resizes = new ResizeObserver(() => this.measure());
    this.changes = new MutationObserver(() => this.measure());
    const foot = this.foot();
    if (foot) {
      this.resizes.observe(foot);
      const summary = foot.querySelector(".bl-status-summary");
      if (summary) {
        this.changes.observe(summary, { subtree: true, childList: true, characterData: true });
      }
    }
    if (document.fonts) document.fonts.ready.then(() => this.measure());
    this.measure();
  },
  unmounted() {
    this.resizes.disconnect();
    this.changes.disconnect();
    this.probe.remove();
  },
  methods: {
    // The foot, .bl-status, that holds this component.
    foot() {
      return this.$el && this.$el.closest ? this.$el.closest(".bl-status") : null;
    },
    // The number of the texts of `lines`, counted from the first, that fit
    // in the room, sent to Python where the answer changes; nothing is sent
    // while the trellis's line is absent.
    measure() {
      const foot = this.foot();
      const summary = foot && foot.querySelector(".bl-status-summary");
      const own = summary && summary.querySelector(":scope > .bl-trellis-status");
      if (!own) return;
      const others = Array.from(summary.children).filter((child) => child !== own);
      const style = getComputedStyle(summary);
      const gap = parseFloat(style.columnGap) || 0;
      const taken = others.reduce(
        (sum, child) => sum + Math.max(child.getBoundingClientRect().width, child.scrollWidth),
        0
      );
      const sides = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
      const room = summary.clientWidth - sides - taken - gap * others.length;
      // The line draws no separator: each " · " of a text stands as the gap
      // between two of its parts (design pass 8 §6), and its first part, the
      // trellis's file, is set in the face of the file's words.
      const parts = parseFloat(getComputedStyle(own).columnGap) || 0;
      const file = own.querySelector(".bl-code-small");
      const width = (text, element) => {
        const face = getComputedStyle(element);
        for (const property of ["fontFamily", "fontSize", "fontWeight", "fontStyle", "letterSpacing"]) {
          this.probe.style[property] = face[property];
        }
        this.probe.textContent = text;
        return this.probe.getBoundingClientRect().width;
      };
      let count = 0;
      for (const text of this.lines || []) {
        const [first, ...rest] = text.split(" · ");
        const drawn = width(first, file || own) + width(rest.join(""), own) + parts * rest.length;
        if (drawn > room + 0.5) break;
        count += 1;
      }
      if (count !== this.sent) {
        this.sent = count;
        this.fit(count);
      }
    },
  },
};
</script>
