<template>
  <span class="bl-restriction-group" ref="group" @keydown="pressKey" @focusout="left">
    <vscode-button secondary ref="select"
                   class="bl-view-select bl-restriction" :class="{ 'bl-refusal-mark': refused }"
                   :title="title" aria-haspopup="dialog" :aria-expanded="opened ? 'true' : 'false'"
                   @click="toggle"><span class="bl-restriction-text">{{ text }}</span><i
                   class="codicon codicon-chevron-down bl-restriction-chevron"
                   aria-hidden="true"></i></vscode-button>
    <div v-if="opened" class="bl-restriction-menu" ref="menu" role="dialog" :aria-label="title">
      <div class="bl-restriction-ranges" role="radiogroup" aria-label="periods">
        <button v-for="item in ranges" :key="'range ' + item.label" type="button" role="radio"
                class="bl-row bl-restriction-item bl-restriction-range" :data-text="item.text"
                :aria-checked="item.chosen ? 'true' : 'false'" @click="choose(item.text, true)">
          <span class="bl-restriction-mark bl-radio" :class="{ 'bl-on': item.chosen }"
                aria-hidden="true"></span>{{ item.label }}
        </button>
      </div>
      <div v-if="stages.length" class="bl-restriction-rule" role="separator"></div>
      <div v-if="stages.length" class="bl-restriction-stages" role="group" aria-label="stages">
        <button v-for="item in stages" :key="'stage ' + item.label" type="button" role="checkbox"
                class="bl-row bl-restriction-item bl-restriction-stage" :data-key="item.label"
                :aria-checked="item.chosen ? 'true' : 'false'"
                :aria-disabled="item.text === null ? 'true' : 'false'"
                @click="item.text !== null && choose(item.text, false)">
          <span class="bl-restriction-mark bl-check" :class="{ 'bl-on': item.chosen }"
                aria-hidden="true"><i v-if="item.chosen" class="codicon codicon-check"
                aria-hidden="true"></i></span><span class="bl-code">{{ item.label }}</span>
        </button>
      </div>
      <div class="bl-restriction-rule" role="separator"></div>
      <div class="bl-restriction-foot">
        <vscode-textfield class="bl-restriction-field" ref="field" :value="field"
                          aria-label="restriction" placeholder="periods 0–2, stages cons, port"
                          autocomplete="off" spellcheck="false"
                          @input="field = $event.target.value"
                          @keydown.enter.prevent="choose(field, true)"></vscode-textfield>
      </div>
    </div>
  </span>
</template>

<script>
// The restriction of the trellis view chosen from a list (spec 0.4 §2.6;
// unit K, K-D17 and K-D18; design pass 2 §3), in a Vue 3 component of
// Solara's component_vue, rendered in the view's bar while the trellis view
// is shown. The select is VSCode Elements' secondary button drawn as the
// system's select (design pass 8 §§4 and 5.3), 26 px on the raised ground
// within the control border, in the form of the library's own select
// (design pass 13 §4; D9): its text 5 px inside the border, then, 4 px
// after it, the Codicon `chevron-down` at the page's 16 px, whose box ends
// 7 px inside the border, so that its ink ends 10 px inside, as the
// select's chevron of the same path does; it prints the
// restriction as written, `periods 0–2`, or `all` for
// the whole trellis; a click on it opens its menu and a second click
// closes it. The menu, an overlay of the system (§5.5), lists the ranges,
// each a row with a ring, then the stage keys, each a row with a check,
// then VSCode Elements' text field, which holds the restriction as
// written, for any other text of the grammar.
// Python gives each item the text its choice writes, so that every choice
// is one text that the event `chosen` carries to `apply_restriction`, as
// Enter in the field does. A range or the field closes the menu, and a
// check leaves it open, so that several keys are ticked or unticked in
// turn. Escape, a press outside the menu and the focus leaving it close the
// menu with nothing chosen; the arrow keys move the focus between the
// menu's items and its field.
//
// Properties, each set from Python:
//   text     the select's text
//   refused  whether the refusal of the restriction stands, which draws
//            the select in the refusal's color
//   title    the select's hover text
//   ranges   the ranges, then `all`, each {label, text, chosen}
//   stages   the stage keys, each {label, text, chosen}, `text` null for
//            the one key ticked, which cannot be unticked
//   typed    the restriction as written, which the field holds; a change
//            of it from Python writes the field again
// Events, each a call of a Python function:
//   chosen(text)  the restriction chosen, as the item gives it or as typed
module.exports = {
  data() {
    return { opened: false, field: "" };
  },
  watch: {
    typed(value) {
      this.field = value || "";
    },
  },
  created() {
    this.field = this.typed || "";
  },
  mounted() {
    // a press outside the group, read in the capture phase of the browser's
    // window, before the element pressed reads it
    this.pressed = (event) => {
      const group = this.$refs.group;
      if (this.opened && group && !group.contains(event.target)) this.close(false);
    };
    window.addEventListener("pointerdown", this.pressed, true);
  },
  unmounted() {
    window.removeEventListener("pointerdown", this.pressed, true);
  },
  methods: {
    // The menu opened, its field holding the restriction as written and the
    // focus on the range chosen, else on the first item; or closed.
    toggle() {
      if (this.opened) {
        this.close(true);
        return;
      }
      this.field = this.typed || "";
      this.opened = true;
      this.$nextTick(() => {
        const menu = this.$refs.menu;
        if (!menu) return;
        const first = menu.querySelector('.bl-restriction-range[aria-checked="true"]') ||
          menu.querySelector(".bl-restriction-item");
        if (first) first.focus({ preventScroll: true });
      });
    },
    // The menu closed, the focus returned to the select where `focus`
    // holds.
    close(focus) {
      if (!this.opened) return;
      this.opened = false;
      if (focus && this.$refs.select) this.$refs.select.focus({ preventScroll: true });
    },
    // The restriction `chosen` sent to Python; the menu closed where
    // `closing` holds.
    choose(chosen, closing) {
      if (closing) this.close(true);
      this.chosen(chosen == null ? "" : chosen);
    },
    // Escape closes the menu; the arrow keys move the focus to the next or
    // the previous item of the menu, the field among them, and ArrowDown on
    // the select opens the menu.
    pressKey(event) {
      if (event.key === "Escape" && this.opened) {
        event.preventDefault();
        event.stopPropagation();
        this.close(true);
        return;
      }
      if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
      if (event.target === this.$refs.select) {
        if (!this.opened && event.key === "ArrowDown") {
          event.preventDefault();
          this.toggle();
        }
        return;
      }
      const menu = this.$refs.menu;
      if (!menu) return;
      const stops = Array.from(menu.querySelectorAll(".bl-restriction-item, .bl-restriction-field"));
      const at = stops.indexOf(event.target);
      if (at < 0) return;
      event.preventDefault();
      const next = stops[Math.min(Math.max(at + (event.key === "ArrowDown" ? 1 : -1), 0), stops.length - 1)];
      next.focus({ preventScroll: true });
    },
    // The focus leaving the group for an element outside it closes the
    // menu and leaves the focus where it went.
    left(event) {
      const group = this.$refs.group;
      const to = event.relatedTarget;
      if (this.opened && group && to instanceof Element && !group.contains(to)) this.close(false);
    },
  },
};
</script>
