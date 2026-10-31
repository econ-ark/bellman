<template>
  <span hidden></span>
</template>

<script>
// The desktop application supplies only a file, line and optional box.
// Python validates the request and opens the file through the page's
// ordinary buffer and elaboration operations.
module.exports = {
  mounted() {
    // Read the actual document when native code asks. A save acknowledgement
    // can precede a newer edit's delayed Python event, including an edit made
    // by undo or indentation without a native input event.
    Object.defineProperty(window, "__bellmanDirty", {
      configurable: true,
      get: () => {
        const acknowledged = this.acknowledged;
        if (!acknowledged || acknowledged.dirty) return true;
        const host = document.querySelector(".bl-editor");
        const editor = host && host.bellmanEditor;
        if (acknowledged.path == null) return editor != null;
        if (!editor || host.dataset.path !== acknowledged.path) return true;
        return editor.getDoc() !== (acknowledged.text || "").replace(/\r\n?/g, "\n");
      },
    });
    window.__bellmanFolder = this.folder;
    this.receiveOpen = (event) => this.open(event.detail);
    window.addEventListener("bellman-open", this.receiveOpen);
    window.__bellmanOpenReady = true;
    const queued = window.__bellmanOpenQueue || [];
    window.__bellmanOpenQueue = [];
    if (queued.length) {
      this.open(queued[queued.length - 1]);
    } else {
      const query = new URLSearchParams(window.location.search);
      const requested = ["file", "line", "box"].some((key) => query.has(key));
      this.open(requested ? {
        file: query.get("file"),
        line: query.has("line") ? query.get("line") : 1,
        box: query.get("box"),
      } : null);
    }
  },
  beforeUnmount() {
    window.removeEventListener("bellman-open", this.receiveOpen);
    delete window.__bellmanDirty;
    window.__bellmanOpenReady = false;
  },
  watch: {
    folder(value) { window.__bellmanFolder = value; },
  },
};
</script>
