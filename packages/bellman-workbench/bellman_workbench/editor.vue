<template>
  <div class="bl-editor" ref="host" :style="{ height: height }"></div>
</template>

<script>
// CodeMirror 6 in a Vue 3 component of Solara's component_vue, over the
// bundle bellman_workbench/public/codemirror/bellman-workbench.js, which Solara serves at
// /static/assets/codemirror/bellman-workbench.js (specification 0.3, §2.2).
//
// Properties, each set from Python:
//   path          the open file's path, relative to the folder; with
//                 `revision` it identifies the document the editor holds
//   revision      an integer Python increments on each file open or reload
//   text          the document of the open file; it is applied when the
//                 pair (path, revision) differs from the pair applied last,
//                 so the text being typed is never replaced by an older
//                 copy of itself
//   diagnostics   the refusals of the buffer, a list of records
//                 {line, column, end_line, end_column, message, severity},
//                 the positions counted from one in code points; the
//                 stage loop's, and the trellis's refusal of its reading
//                 at a line of this file, whose record may carry `action`,
//                 {name, edits, expected}: a button of that name in the
//                 refusal's tooltip applies the edits when the document is
//                 `expected` (`take the line out`, spec 0.4 §3.3)
//   goto          {line, column, n}: a change moves the cursor there and
//                 gives the editor the focus; with end_line and end_column
//                 it selects the text from there to that place, to the end
//                 of end_line where end_column is null, and with focus false
//                 the focus stays where it is (J-D40; amendment 02 ruling 9)
//   save_request  an integer: a change sends the current document with the
//                 `save` event, which is how the save button reads it
//   flush_request an integer: a change sends the current document with the
//                 `change` event at once, under the path and revision
//                 applied last, which is how Python reads the typing of the
//                 last pause before it opens another file
//   hide_types    true draws every bracket group that carries an identity as
//                 its name alone, the lines of the cursor and of a refusal in
//                 full (specification 0.3, §2.2 rule 5); the text is unchanged
//   show_notes    true draws every note, the quoted explanation of an
//                 annotation, as written; false, the first value, draws each
//                 as a note glyph with its preview, the lines of the cursor
//                 and of a refusal in full (design pass 10 §9); the text is
//                 unchanged
//   edit          {edits, expected, n, gesture, history}: a change applies
//                 the replacements Python asks for, each {line, column,
//                 end_line, end_column, text} counted in code points, as one
//                 edit, one step of the undo history, when the document is
//                 `expected` (unit T, rule 3), and is answered by the event
//                 `applied`; with no edits it changes nothing, and its
//                 answer says whether the document is `expected` (spec 0.4
//                 §3.3). `gesture`, where given, is the key of a gesture that
//                 edits several files, which marks the step as that
//                 gesture's; `history` false keeps the edit out of the undo
//                 history (unit L, Task 17)
//   shortcuts     the Unicode shortcuts of the VS Code extension, prefix to
//                 body, which Tab expands (unit T, rule 6)
//   role_words    the marked tags the editor draws as role tags (spec 0.4
//                 §5.2; R-D18), read once, when the editor is made
//   indent        the number of spaces of one indent (R-D33), read once,
//                 when the editor is made
//   height        the CSS height of the editor
// Events, each a call of a Python function, each carrying the `path` and the
// `revision` of the document the editor held when the event was made, so
// that Python drops an event of a document no longer open (§2.2 rule 1):
//   change({path, revision, text})           the whole document, 750 ms
//                                            after the last edit
//   save({path, revision, text})             the current document, on Mod-s
//                                            or a save request
//   cursor({path, revision, line, column})   the cursor's position, counted
//                                            from one, the column in code
//                                            points
//   applied({path, revision, n, applied})    the answer to one change of
//                                            `edit`: `n` the request's
//                                            counter, `applied` whether its
//                                            edits applied, false where no
//                                            editor is created yet (brief
//                                            rule 7, J-D12)
//   gesture_undo({path, revision, gesture,   an undo or a redo of the step
//                 redo, text})               a gesture's key marks, with
//                                            that key, or Mod-z with no step
//                                            of the history to undo, with
//                                            `gesture` null; `text` the
//                                            document then (unit L, Task 17)
// The DOM event `input-edited`, a CustomEvent on `document` with the detail
// {path}, is dispatched at the first change of the document after the last
// `change` event or the last document Python gave; a document Python gives
// dispatches none (spec 0.4 §3.3; brief rule 6). It is no message to
// Python; brief rule 6 gives it to the graph region.
// The host element, `.bl-editor`, carries `bellmanEditor`, the handle that
// window.bellmanEditor.create answers, which goto.vue and the page tests
// read for a preview (R-D29), until the component is disposed.
module.exports = {
  async mounted() {
    this.linkMathematicsStylesheet();
    await this.loadBundle();
    this.appliedPath = this.path;
    this.appliedRevision = this.revision;
    this.appliedText = this.text;
    // true once `input-edited` was dispatched for a change Python has not read
    this.inputNotified = false;
    this.handle = window.bellmanEditor.create(this.$refs.host, {
      doc: this.text || "",
      path: this.path == null ? null : this.path,
      revision: this.revision || 0,
      pauseMs: 750,
      hideTypes: Boolean(this.hide_types),
      showNotes: Boolean(this.show_notes),
      shortcuts: this.plain(this.shortcuts) || {},
      roleWords: this.plain(this.role_words) || [],
      indent: this.indent,
      onChange: (event) => this.sendChange(event),
      onSave: (event) => this.save(event),
      onCursor: (event) => this.cursor(event),
      onInput: (event) => this.notifyInput(event),
      onUndo: (event) => this.gesture_undo(event),
    });
    this.handle.setDiagnostics(this.plain(this.diagnostics) || []);
    this.hostElement = this.$refs.host;
    this.hostElement.bellmanEditor = this.handle;
    this.hostElement.dataset.path = this.appliedPath == null ? "" : this.appliedPath;
  },
  unmounted() {
    this.dispose();
  },
  watch: {
    path() {
      this.applyDocument();
    },
    revision() {
      this.applyDocument();
    },
    text() {
      this.applyDocument();
    },
    diagnostics(value) {
      if (this.handle) this.handle.setDiagnostics(this.plain(value) || []);
    },
    goto(value) {
      if (this.handle && value && value.line) {
        this.handle.gotoLine(
          value.line, value.column || 1, value.end_line, value.end_column, value.focus !== false,
        );
      }
    },
    save_request() {
      if (this.handle) {
        this.save({
          path: this.appliedPath == null ? null : this.appliedPath,
          revision: this.appliedRevision || 0,
          text: this.handle.getDoc(),
        });
      }
    },
    // Before the bundle has loaded, no document was applied and nothing was
    // typed, so the event carries the properties' own document.
    flush_request() {
      const applied = this.handle != null;
      const path = applied ? this.appliedPath : this.path;
      this.sendChange({
        path: path == null ? null : path,
        revision: (applied ? this.appliedRevision : this.revision) || 0,
        text: applied ? this.handle.getDoc() : this.text || "",
      });
    },
    hide_types(value) {
      if (this.handle) this.handle.setHideTypes(Boolean(value));
    },
    show_notes(value) {
      if (this.handle) this.handle.setShowNotes(Boolean(value));
    },
    // Each request is answered once with `applied`, a request with no
    // edits included; before the bundle has loaded, nothing is applied and
    // the answer is false, under the properties' own document.
    edit(value) {
      if (!value || !value.edits) return;
      const created = this.handle != null;
      const path = created ? this.appliedPath : this.path;
      const options = { gesture: value.gesture, history: value.history };
      this.applied({
        path: path == null ? null : path,
        revision: (created ? this.appliedRevision : this.revision) || 0,
        n: value.n,
        applied:
          created && this.handle.replaceSpans(this.plain(value.edits), value.expected, options),
      });
    },
    shortcuts(value) {
      if (this.handle) this.handle.setShortcuts(this.plain(value) || {});
    },
  },
  methods: {
    // The URL of a file of the package's public/ folder: Solara serves that
    // folder at <root path>/static/assets/.
    staticUrl(path) {
      const root = (window.solara && window.solara.rootPath) || "";
      return `${root}/static/assets/${path}`;
    },
    // KaTeX's stylesheet, whose faces the preview of a note sets its
    // mathematics in, linked once per page from the package's own files,
    // never from a network (G-D12): one link element with an id.
    linkMathematicsStylesheet() {
      const id = "bellman-katex-stylesheet";
      if (document.getElementById(id)) return;
      const link = document.createElement("link");
      link.id = id;
      link.rel = "stylesheet";
      link.href = this.staticUrl("codemirror/katex/katex.min.css");
      document.head.appendChild(link);
    },
    // The bundle is loaded once per page: one script element with an id,
    // and one promise on window that every editor on the page awaits.
    loadBundle() {
      if (window.bellmanEditor) return Promise.resolve();
      if (!window.bellmanEditorLoading) {
        window.bellmanEditorLoading = new Promise((resolve, reject) => {
          const id = "bellman-workbench-script";
          let script = document.getElementById(id);
          if (!script) {
            script = document.createElement("script");
            script.id = id;
            script.src = this.staticUrl("codemirror/bellman-workbench.js");
            document.head.appendChild(script);
          }
          script.addEventListener("load", () => resolve());
          script.addEventListener("error", () => reject(new Error(`${script.src} did not load`)));
        });
      }
      return window.bellmanEditorLoading;
    },
    // The document is given to the editor, with its path and revision, when
    // the pair (path, revision) differs from the pair applied last, whichever
    // of the three properties the browser received first. Within an applied
    // pair, a `text` that differs from the text applied with it is the pair's
    // own text received after the pair, and is applied; a re-sent equal text
    // changes nothing. The editor replaces its text only when it differs.
    applyDocument() {
      if (!this.handle) return;
      const samePair = this.path === this.appliedPath && this.revision === this.appliedRevision;
      if (samePair && this.text === this.appliedText) return;
      this.appliedPath = this.path;
      this.appliedRevision = this.revision;
      this.appliedText = this.text;
      this.inputNotified = false;
      this.handle.setDocument(
        this.path == null ? null : this.path,
        this.revision || 0,
        this.text || "",
      );
      this.hostElement.dataset.path = this.appliedPath == null ? "" : this.appliedPath;
    },
    // The event `change`; the next change of the document then dispatches
    // `input-edited` again.
    sendChange(event) {
      this.inputNotified = false;
      this.change(event);
    },
    // A change of the document that Python did not make: `input-edited`
    // with the document's path, where none was dispatched since the last
    // `change` event or the last document Python gave.
    notifyInput(event) {
      if (this.inputNotified) return;
      this.inputNotified = true;
      document.dispatchEvent(new CustomEvent("input-edited", { detail: { path: event.path } }));
    },
    // A plain copy of a value: the properties are reactive proxies.
    plain(value) {
      return value == null ? value : JSON.parse(JSON.stringify(value));
    },
    dispose() {
      if (this.hostElement) {
        delete this.hostElement.bellmanEditor;
        this.hostElement = null;
      }
      if (this.handle) {
        this.handle.destroy();
        this.handle = null;
      }
    },
  },
};
</script>
