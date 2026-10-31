<template>
  <span class="bl-copy">
    <button type="button" :class="['bl-text-button', 'bl-copy-button', button_class]" :title="title"
            @click="copy">{{ copied ? "Copied" : label }}</button>
    <details v-if="refused" class="bl-copy-fallback">
      <summary>{{ label }}: the browser refused the clipboard</summary>
      <pre class="bl-copy-text bl-code-small">{{ text }}</pre>
    </details>
  </span>
</template>

<script>
// A button that copies a text to the clipboard, in a Vue 3 component of
// Solara's component_vue, the system's text button (design pass 8 §§4 and
// 5.3): the clipboard is written in the browser, at the click. Where the
// browser refuses the clipboard, the text is shown under the button in a
// collapsed block, which opens on a click on its summary.
//
// Properties, each set from Python:
//   text          the text the button copies
//   label         the button's word, `Card` in the panel
//   title         the button's tooltip
//   button_class  a class name the button carries besides bl-copy-button
module.exports = {
  data() {
    return { copied: false, refused: false };
  },
  watch: {
    text() {
      this.copied = false;
      this.refused = false;
    },
  },
  methods: {
    // The text to the clipboard; the button reads `Copied` for 1.5 seconds,
    // and a refusal, or a browser without a clipboard, opens the fallback.
    async copy() {
      try {
        await navigator.clipboard.writeText(this.text || "");
        this.refused = false;
        this.copied = true;
        clearTimeout(this.copiedTimer);
        this.copiedTimer = setTimeout(() => {
          this.copied = false;
        }, 1500);
      } catch (error) {
        this.copied = false;
        this.refused = true;
      }
    },
  },
  unmounted() {
    clearTimeout(this.copiedTimer);
  },
};
</script>
