<template>
  <div class="bl-goto" v-show="opened" ref="palette" role="dialog" aria-label="go to"
       :style="place" @keydown="pressKey" @focusout="left">
    <input class="bl-goto-input" ref="input" v-model="query" type="text" aria-label="go to"
           autocomplete="off" spellcheck="false" />
    <div class="bl-goto-results" ref="results">
      <button v-for="(result, n) in results" :key="n + ' ' + result.kind + ' ' + result.text"
              type="button" class="bl-goto-result" :class="{ 'bl-active': n === current }"
              @focus="show(n)" @click="choose(n)">
        <span class="bl-goto-text">{{ result.text }}</span>
        <span class="bl-goto-kind">{{ result.kind }}</span>
        <span class="bl-goto-address">{{ result.address }}</span>
      </button>
    </div>
  </div>
</template>

<script>
// Goto Anything (spec 0.4 §5.8; unit R, brief rule 9; review 1), in a Vue 3
// component of Solara's component_vue, rendered once inside .bl-window by
// `Page`. The palette opens when `open_request` changes, which Python raises
// on P with the primary modifier, read by window.vue, and on the button
// `go to`. At its opening it takes the editor's view(), the graph's view(),
// Python's selection and the element that holds the focus; its input then
// holds the focus until the palette closes.
//
// The text typed chooses the results by its first character (R-D35): `:n`
// gives one result of kind `line`; `#text` the lines of the editor's own
// document that hold the text (the handle's findText), of kind `text`; `>`
// the entries of kind `command` whose word holds the text; `@`, or text with
// no prefix, the entries of kinds `block` and `box` whose text, block or
// node holds the text, the case ignored in every filter. The entries whose
// text begins with the text typed come first, each group in the order
// Python gives. Nothing typed gives no result. At most fifty results are
// listed.
//
// The current result, the first until the arrow keys, the pointer or the
// focus choose another, is previewed: a line, a text or a block by the
// editor's previewLine of its line, which moves neither the cursor nor the
// focus; a box by the event `preview`, on which Python selects the box. A
// result of no other kind removes a line's mark. Enter, or a click on a
// result, chooses it: the palette closes, the mark goes, the focus returns
// to the element that held it, and the event `chosen` carries the entry. A
// command first restores both views as Escape does. Escape, a click outside
// the palette, or the focus leaving it by Tab closes it with nothing chosen:
// both handles' setView restore the records taken at the opening, the focus
// returns to the element that held it (but where Tab moved it on), and the
// event `cancelled` carries Python's selection taken at the opening. Tab
// moves from the input to the results and on out of the palette, so that no
// focus is trapped. No preview, no choice and no cancel changes the text.
//
// Properties, each set from Python:
//   open_request  a count, which Python raises to open the palette
//   entries       the entries of `@` and `>`, each {prefix, kind, text,
//                 address, block?, node?, graph?, line?, command?}
//   selection     Python's selection, {nodeId, graphId} or null
// Events, each a call of a Python function:
//   preview({nodeId, graphId})     a box previewed
//   chosen({...entry, selection, previewed})
//                                  a result chosen; `selection` is Python's
//                                  selection at the opening and `previewed`
//                                  whether a box was previewed since
//   cancelled({selection, previewed})
//                                  the palette closed with nothing chosen
module.exports = {
  // The most results the palette lists.
  most: 50,
  // The palette's width in pixels, and its distance in pixels from the
  // window's top and from each side (spec 0.4 §5.8).
  width: 600,
  top: 84,
  side: 16,
  data() {
    return { opened: false, query: "", current: 0, place: {} };
  },
  computed: {
    // The results of the text typed, by its first character.
    results() {
      if (!this.opened) return [];
      const typed = this.query;
      const first = typed.charAt(0);
      const rest = typed.slice(1).trim();
      if (!typed.trim()) return [];
      if (first === ":") {
        const line = /^[0-9]+$/.test(rest) ? parseInt(rest, 10) : 0;
        return line >= 1 ? [{ kind: "line", text: String(line), address: `${line}:1`, line }] : [];
      }
      if (first === "#") {
        const editor = this.editor();
        if (!editor || !rest) return [];
        return editor.findText(rest).map((row) => ({
          kind: "text",
          text: row.text,
          address: `${row.line}:${row.column}`,
          line: row.line,
          column: row.column,
        }));
      }
      const command = first === ">";
      const wanted = (command || first === "@" ? rest : typed.trim()).toLowerCase();
      const holds = (value) => typeof value === "string" && value.toLowerCase().includes(wanted);
      const found = (this.entries || [])
        .filter((entry) => entry.prefix === (command ? ">" : "@"))
        .filter((entry) => holds(entry.text) || holds(entry.block) || holds(entry.node));
      const begins = (entry) => entry.text.toLowerCase().startsWith(wanted);
      return found
        .filter(begins)
        .concat(found.filter((entry) => !begins(entry)))
        .slice(0, this.$options.most);
    },
  },
  watch: {
    open_request(value) {
      if (value) this.open();
    },
    query() {
      this.current = 0;
      this.previewCurrent();
    },
    results() {
      if (this.current >= this.results.length) this.current = 0;
      this.previewCurrent();
    },
  },
  mounted() {
    // a press outside the palette, read in the capture phase of the
    // browser's window, before the element pressed reads it
    this.pressed = (event) => {
      const palette = this.$refs.palette;
      if (this.opened && palette && !palette.contains(event.target)) this.cancel(true);
    };
    window.addEventListener("pointerdown", this.pressed, true);
    // Escape with the focus outside the palette while it is open, so that
    // Escape always closes it
    this.escaped = (event) => {
      if (this.opened && event.key === "Escape") this.cancel(true);
    };
    window.addEventListener("keydown", this.escaped);
    this.kept = null;
    this.previewed = false;
    this.shown = null;
    this.marked = false;
  },
  unmounted() {
    window.removeEventListener("pointerdown", this.pressed, true);
    window.removeEventListener("keydown", this.escaped);
  },
  methods: {
    // The editor's handle on .bl-editor and the graph's on .bl-view-host
    // (R-D29), or null where the region holds none.
    editor() {
      const host = document.querySelector(".bl-editor");
      return host && host.bellmanEditor ? host.bellmanEditor : null;
    },
    graph() {
      const host = document.querySelector(".bl-view-host");
      return host && host.bellmanFlow ? host.bellmanFlow : null;
    },
    // A plain copy of a value: the properties are reactive proxies.
    plain(value) {
      return value == null ? null : JSON.parse(JSON.stringify(value));
    },
    // The palette opened, or, where it is open, its input focused with its
    // text selected. The records of the opening are taken first, and the
    // palette stands centered over the text's column, limited to the
    // window's width (spec 0.4 §5.8).
    open() {
      if (!this.opened) {
        const editor = this.editor();
        const graph = this.graph();
        this.kept = {
          editor: editor ? editor.view() : null,
          graph: graph ? graph.view() : null,
          selection: this.plain(this.selection),
          focused: document.activeElement,
        };
        this.previewed = false;
        this.shown = null;
        this.marked = false;
        const { width, top, side } = this.$options;
        const room = document.documentElement.clientWidth;
        const wide = Math.min(width, room - 2 * side);
        const text = document.querySelector(".bl-file");
        const box = text ? text.getBoundingClientRect() : { left: 0, width: room };
        const left = Math.min(Math.max(side, box.left + box.width / 2 - wide / 2), room - side - wide);
        this.place = { top: `${top}px`, left: `${left}px`, width: `${wide}px` };
        this.query = "";
        this.current = 0;
        this.opened = true;
      }
      this.$nextTick(() => {
        const input = this.$refs.input;
        if (input) {
          input.focus({ preventScroll: true });
          input.select();
        }
      });
    },
    // The current result previewed, once for each result made current.
    previewCurrent() {
      const result = this.opened ? this.results[this.current] : undefined;
      const shown = result
        ? `${result.kind} ${result.text} ${result.node || ""} ${result.line || ""}`
        : null;
      if (shown === this.shown) return;
      this.shown = shown;
      const editor = this.editor();
      if (result && ["line", "text", "block"].includes(result.kind)) {
        if (editor) editor.previewLine(result.line);
        this.marked = true;
        return;
      }
      if (this.marked && editor) editor.previewLine(null);
      this.marked = false;
      if (result && result.kind === "box") {
        this.previewed = true;
        this.preview({ nodeId: result.node, graphId: result.graph });
      }
    },
    // The result `n` made current and previewed, as the arrow keys, the
    // pointer or the focus make it.
    show(n) {
      if (n >= 0 && n < this.results.length && n !== this.current) {
        this.current = n;
        this.previewCurrent();
      }
    },
    // The palette's keys: the arrow keys in the input move the current
    // result, which the list scrolls into view, and on a result move the
    // focus to the next or the previous one; Enter in the input chooses the
    // current result; Escape closes the palette wherever the focus stands
    // in it.
    pressKey(event) {
      const input = event.target === this.$refs.input;
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        this.cancel(true);
      } else if (event.key === "Enter" && input) {
        event.preventDefault();
        this.choose(this.current);
      } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        const step = event.key === "ArrowDown" ? 1 : -1;
        const list = this.$refs.results;
        const buttons = list ? list.querySelectorAll(".bl-goto-result") : [];
        const at = input ? this.current : Array.prototype.indexOf.call(buttons, event.target);
        const next = Math.min(Math.max(at + step, 0), this.results.length - 1);
        if (!buttons[next]) return;
        if (input) {
          this.show(next);
          buttons[next].scrollIntoView({ block: "nearest" });
        } else {
          buttons[next].focus();
        }
      }
    },
    // The focus leaving the palette for an element outside it, as Tab after
    // the last result moves it, closes the palette with nothing chosen and
    // leaves the focus where it went. Where the focus goes to no element,
    // the palette closes once the page is seen to hold the focus outside
    // it, so that a window that loses the focus to another one keeps the
    // palette open.
    left(event) {
      const palette = this.$refs.palette;
      const to = event.relatedTarget;
      if (!this.opened || !palette) return;
      if (to instanceof Element) {
        if (!palette.contains(to)) this.cancel(false);
        return;
      }
      setTimeout(() => {
        const outside = !palette.contains(document.activeElement);
        if (this.opened && document.hasFocus() && outside) this.cancel(false);
      });
    },
    // The palette closed: the mark of a line removed, or, with `restore`,
    // both handles given the records of the opening; the focus returned to
    // the element that held it where `focus` holds.
    close(restore, focus) {
      if (!this.opened) return null;
      this.opened = false;
      const kept = this.kept;
      this.kept = null;
      this.shown = null;
      if (focus) {
        const element = kept.focused;
        if (element && element !== document.body && element.isConnected) {
          element.focus({ preventScroll: true });
        } else if (this.$refs.input) {
          this.$refs.input.blur();
        }
      }
      const editor = this.editor();
      const graph = this.graph();
      if (restore) {
        if (editor && kept.editor) editor.setView(kept.editor);
        if (graph && kept.graph) graph.setView(kept.graph);
      } else if (editor) {
        editor.previewLine(null);
      }
      this.marked = false;
      return kept;
    },
    // Escape, a press outside the palette, or the focus leaving it: both
    // views restored and the event `cancelled`.
    cancel(focus) {
      const previewed = this.previewed;
      const kept = this.close(true, focus);
      if (kept) this.cancelled({ selection: kept.selection, previewed });
    },
    // The result `n` chosen: a command after both views are restored, any
    // other result with the mark of its line removed; then the event
    // `chosen` with the entry.
    choose(n) {
      const result = this.results[n];
      if (!result) return;
      const previewed = this.previewed;
      const kept = this.close(result.kind === "command", true);
      if (kept) this.chosen({ ...this.plain(result), selection: kept.selection, previewed });
    },
  },
};
</script>
