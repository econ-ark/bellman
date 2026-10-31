<template>
  <div class="bl-field" :class="classes" :title="hover || null">
    <label v-if="label" class="bl-field-label" :for="id">{{ label }}</label>
    <vscode-single-select v-if="kind === 'select'" :id="id" :value="text"
                          :label="named || null" :disabled="disabled || null"
                          :position="above ? 'above' : 'below'"
                          @change="choose($event)">
      <vscode-option v-for="option in options" :key="option" :value="option"
                     :description="(descriptions && descriptions[option]) || null"
                     :selected="option === text || null">{{ option }}</vscode-option>
    </vscode-single-select>
    <vscode-textarea v-else-if="kind === 'area'" :id="id" :value="text" :rows="grows ? null : 2"
                     :placeholder="placeholder || null" :aria-label="named || null"
                     :disabled="disabled || null" @input="typed($event)"
                     @change="committed($event)" @keydown.enter="submit($event)"></vscode-textarea>
    <vscode-textfield v-else :id="id" :value="text" :type="kind === 'number' ? 'number' : 'text'"
                      :placeholder="placeholder || null" :aria-label="named || null"
                      :disabled="disabled || null" @input="typed($event)"
                      @change="committed($event)" @keydown.enter="submit($event)"></vscode-textfield>
  </div>
</template>

<script>
// One field of a form, or one control of the Recipe tab, drawn by
// VSCode Elements (design pass 8 §§4 and 6; AAS, M-D4, M-D11): a text
// field, `vscode-textfield`, a number field, the same of type number, a
// text area of two lines, or of one line growing to eight where `grows`
// holds, `vscode-textarea`, or a select of one, `vscode-single-select`
// with one `vscode-option` per option; each 26 px high with a radius of 4
// px, which brand.css and the library's theme variables give. The label,
// where one is given, stands above the control in Small, linked to it, so
// that a screen reader reads it as the control's name. The wrapper carries
// the classes Python gives, by which the page and its tests find the
// field, and the hover.
//
// A text area that grows (amendment 07 §2 item 2) carries no `rows`
// attribute, since the library's rule for `rows` makes its inner element
// ignore the control's height. One style sheet adopted into the control's
// open shadow root, or a <style> element appended there where the browser
// adopts no sheet, gives the inner element, the control's `wrappedElement`,
// the metrics of the library's text field: lines of 18 px and padding of 3
// px above and below and 4 px at the sides, so that one line stands
// centered in 26 px. The text area's height is its inner element's scroll
// height plus the inner element's border, measured once the library has
// drawn the text, at each change of the text, typed or set by Python, at
// each change of the control's width and once the page's fonts are loaded,
// and written on the control as the custom property
// --bl-field-text-height, from which brand.css sizes it.
//
// The text the field shows is its own while the author types: each text
// typed is sent to Python, on each keystroke for a field of continuous
// update and on Enter or when the field is left otherwise, and a value
// Python sends back is taken only where it is no text this field sent and
// Python has not yet answered, so that an answer to an earlier keystroke
// never replaces what was typed after it. A value Python sets of its own,
// as a click on an entry of a folder chooser does, is taken at once.
//
// Python's answer to a change that leaves the value as it was, a choice
// refused or a choice taken back before Python read it, is a new
// `answered`: the texts sent and not answered are then dropped and the
// field shows `value`, the element kept, so that an open list stays open;
// a text field that holds the focus keeps the text being typed (unit M,
// Task 10, fix round 1).
//
// Properties, each set from Python:
//   kind        `text`, `number`, `area` or `select`
//   value       the field's value, or the option chosen
//   options     the options of a select, each its text and its value
//   above       whether a select opens its list above it, as the
//               selects of Matsya's composer at the window's foot do;
//               otherwise below it, which the library opens only for
//               the position `below`, not for none (SE-31)
//   grows       whether a text area's height follows its text, one line
//               when empty and one more for each further line, measured on
//               its inner element and written on the control (amendment 07
//               §2 item 2); false for the commit form's message, a text
//               area of two lines
//   descriptions  a select's description of each option, by the option,
//               which the library shows under the list for the option
//               under the pointer or the keys; none where empty (design
//               pass 16, the output levels named by their files)
//   label       the words above the control, none where empty
//   hover       the wrapper's hover, none where empty
//   classes     the wrapper's classes
//   autofocus   whether the field takes the focus when it is drawn
//   continuous  whether each keystroke is sent, else Enter or leaving it
//   disabled    whether the field takes no text
//   placeholder the words the empty field shows, none where empty
//   named       the control's accessible name where it has no label, the
//               select's `label`, which names its list
//   submits     whether Enter in a text area or a text field sends its text
//               as `submitted`, in a text area in place of a new line,
//               Shift+Enter still beginning one, and Enter during an input
//               method's composition, which confirms the candidate, sending
//               nothing; Matsya's composer is such a text area, one line
//               when empty (amendment 07)
//   answered    a text Python changes at each answer to the field's
//               changes, the empty text where it gives none
// Events, each a call of a Python function:
//   entered(text)     the text typed or the option chosen
//   submitted(text)   the text of a text area or a text field that `submits`, on Enter
module.exports = {
  // The metrics of the library's text field, which a text area that grows
  // takes into its shadow root, read as this.$options.metrics (amendment 07
  // §2 item 2, D-9).
  metrics: "textarea { line-height: 18px; padding: 3px 4px; }",
  data() {
    return {
      // the text the control shows
      text: "",
      // the texts sent to Python and not yet answered, in the order sent
      pending: [],
      // the id that links the label to the control
      id: "bl-field-" + Math.random().toString(36).slice(2),
    };
  },
  // the properties Python sets are this component's data, which stand
  // once it is created
  created() {
    this.text = this.value == null ? "" : String(this.value);
  },
  watch: {
    value(given) {
      const text = given == null ? "" : String(given);
      const at = this.pending.indexOf(text);
      if (at >= 0) {
        // Python's answer to a text this field sent: the texts sent before
        // it are answered too
        this.pending = this.pending.slice(at + 1);
        return;
      }
      this.pending = [];
      this.text = text;
    },
    answered() {
      // a text field the author is typing in keeps the text typed
      const typing = this.kind !== "select" && this.$el.contains(document.activeElement);
      if (typing) return;
      this.pending = [];
      this.text = this.value == null ? "" : String(this.value);
    },
    // a text area that grows is measured once Vue has drawn its new text
    text() {
      if (this.grows) this.$nextTick(() => this.grow());
    },
  },
  mounted() {
    if (this.kind === "area" && this.grows) this.startGrowing();
    if (!this.autofocus) return;
    // the control takes the focus once the library has defined it, its
    // shadow root passing the focus to its input
    const control = this.$el.querySelector("vscode-textfield, vscode-textarea, vscode-single-select");
    const tag = control ? control.tagName.toLowerCase() : null;
    if (!tag || !window.customElements) return;
    window.customElements.whenDefined(tag).then(() => {
      this.$nextTick(() => control.focus());
    });
  },
  unmounted() {
    if (this.resizes) this.resizes.disconnect();
  },
  methods: {
    send(text) {
      this.text = text;
      if (text === this.value && this.pending.length === 0) return;
      this.pending = [...this.pending, text];
      this.entered(text);
    },
    // a keystroke: the text sent at once in a field of continuous update
    typed(event) {
      const text = event.target.value;
      this.text = text;
      if (this.continuous) this.send(text);
    },
    // Enter or the field left: the text sent where each keystroke is not
    committed(event) {
      if (!this.continuous) this.send(event.target.value);
    },
    choose(event) {
      this.send(event.target.value);
    },
    // Enter in a text area or a text field that `submits`: its text sent as
    // `submitted` and no new line begun; Shift+Enter begins one, and Enter
    // during an input method's composition, which confirms the candidate,
    // sends nothing (amendment 07 §2 item 1). The key code 229 is that of a
    // key the input method reads, which WebKit, the desktop shell's engine,
    // gives the Enter that ends a composition, after the composition's end
    // has cleared `isComposing`.
    submit(event) {
      if (!this.submits || event.shiftKey) return;
      if (event.isComposing || event.keyCode === 229) return;
      event.preventDefault();
      this.submitted(event.target.value);
    },
    // The text area of a field that grows; null for any other field.
    area() {
      if (this.kind !== "area" || !this.grows || !this.$el.querySelector) return null;
      return this.$el.querySelector("vscode-textarea");
    },
    // A text area that grows, once the library has defined and drawn it:
    // the text field's metrics adopted into its shadow root, its width
    // observed, and its height measured, again once the fonts are loaded.
    async startGrowing() {
      const control = this.area();
      if (!control || !window.customElements) return;
      await window.customElements.whenDefined("vscode-textarea");
      await control.updateComplete;
      this.adoptMetrics(control.shadowRoot);
      // the control's width at the last measure, none before the first
      this.measuredWidth = null;
      this.resizes = new ResizeObserver((entries) => this.resized(entries));
      this.resizes.observe(control);
      if (document.fonts) document.fonts.ready.then(() => this.grow());
      this.grow();
    },
    // The text field's metrics given to the inner element of the shadow
    // root `root`: one style sheet adopted into it, or, where the browser
    // adopts no sheet, a <style> element appended to it, after the
    // library's own styles.
    adoptMetrics(root) {
      if (!root) return;
      const metrics = this.$options.metrics;
      if ("adoptedStyleSheets" in root && window.CSSStyleSheet && "replaceSync" in CSSStyleSheet.prototype) {
        const sheet = new CSSStyleSheet();
        sheet.replaceSync(metrics);
        root.adoptedStyleSheets = [...root.adoptedStyleSheets, sheet];
        return;
      }
      const style = document.createElement("style");
      style.textContent = metrics;
      root.append(style);
    },
    // At a change of the control's width, `grow` measures the height in
    // the next animation frame, since a height written while the observer
    // reports would be a change of size it reports again in the same frame;
    // a change of the height alone, which a measure or a drag makes, starts
    // no measure.
    resized(entries) {
      const width = entries[entries.length - 1].contentRect.width;
      if (width === this.measuredWidth) return;
      this.measuredWidth = width;
      window.requestAnimationFrame(() => this.grow());
    },
    // The height of a text area that grows, written on the control as
    // --bl-field-text-height: the inner element's scroll height, read once
    // the library has drawn the text and while the inner element's own
    // height is held at zero, so that it counts the lines of the text, a
    // wrapped line for each line it takes, and not the height the control
    // gives it, plus the inner element's border of 2 px. A control that is
    // not drawn, as in a folded column, is not measured.
    async grow() {
      const control = this.area();
      if (!control || !control.updateComplete) return;
      await control.updateComplete;
      const inner = control.wrappedElement;
      if (!inner || control.getClientRects().length === 0) return;
      const style = getComputedStyle(inner);
      const border = parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
      const { height, overflow } = inner.style;
      const scrolled = inner.scrollTop;
      inner.style.height = "0px";
      inner.style.overflow = "hidden";
      const lines = inner.scrollHeight;
      inner.style.height = height;
      inner.style.overflow = overflow;
      inner.scrollTop = scrolled;
      control.style.setProperty("--bl-field-text-height", `${lines + border}px`);
    },
  },
};
</script>
