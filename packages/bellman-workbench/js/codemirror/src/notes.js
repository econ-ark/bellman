// The notes of a stage file (design pass 10 §9; AAS's brief of 12 October
// 2026, § Rendered annotation comments; unit N, Task 4). A note is the
// quoted explanation of a statement's annotation: a quoted entry of its
// brackets, `:: ["discount factor"]` or `:: [id=feasible, "empty at zero
// resources"]`, or a bare quoted annotation, `:: "…"`, which
// parse_annotation of packages/bellman/bellman/syntax/lower.py reads as a
// tag. The annotation's other entries, a `#` comment and a quoted string
// outside an annotation are drawn as written.
//
// While the notes are hidden, the editor's first state, each note, from its
// opening to its closing quote, is replaced by a widget, the 16-px Codicon
// `note`, focusable and named `note`. A line that holds the selection or a
// refusal is drawn in full (linesInFull of decorations.js), as the hidden
// types draw it. The pointer resting on a glyph for HOVER_MS, or the focus
// on it, opens the preview, a tooltip of the class `bl-note` that renders
// the explanation as Markdown with markdown-it and typesets its mathematics,
// `\(…\)` inline and `\[…\]` displayed, with KaTeX. The preview stays while
// the pointer is over the glyph or the preview, or the glyph holds the
// focus, and closes on Escape. Enter or a click on the glyph puts the
// cursor after the note's opening quote and gives the editor the focus, so
// that the line is drawn in full until the cursor leaves it. The glyph and
// the preview are decorations: the document, the undo history and the
// unsaved state are unchanged by them.
import { ensureSyntaxTree, syntaxTree } from "@codemirror/language";
import { setDiagnosticsEffect } from "@codemirror/lint";
import { EditorState, StateEffect, StateField } from "@codemirror/state";
import { Decoration, EditorView, ViewPlugin, WidgetType, showTooltip } from "@codemirror/view";
import katex from "katex";
import MarkdownIt from "markdown-it";

import { blLanguage } from "./bl_language.js";
import { annotationStart, linesInFull } from "./decorations.js";

// The time the pointer rests on a glyph before its preview opens (design
// pass 10 §9).
const HOVER_MS = 300;

// The time the pointer has to cross between a glyph and its preview before
// the preview closes.
const CROSSING_MS = 150;

// --- the notes of a text ---

// The notes of the text `text` that follows an annotation's `::`, each
// {from, to}, offsets in `text` from a note's opening quote to after its
// closing quote, by the rule of parse_annotation: the text without its
// white space and the colons that continue the `::`; where it is in
// brackets, each entry, divided at a comma outside double quotes and
// without its white space, that opens and closes with a double quote;
// otherwise the whole text where it opens and closes with one.
export function noteSpans(text) {
  const start = /^:*\s*/.exec(text)[0].length;
  const end = text.trimEnd().length;
  const quoted = (from, to) => to - from >= 2 && text[from] === '"' && text[to - 1] === '"';
  if (end - start < 2 || text[start] !== "[" || text[end - 1] !== "]") {
    return quoted(start, end) ? [{ from: start, to: end }] : [];
  }
  const spans = [];
  let entry = start + 1;
  let inQuotes = false;
  for (let i = start + 1; i < end; i++) {
    const last = i === end - 1;
    if (!last && text[i] === '"') inQuotes = !inQuotes;
    if (last || (text[i] === "," && !inQuotes)) {
      const part = text.slice(entry, i);
      const from = entry + part.length - part.trimStart().length;
      const to = entry + part.trimEnd().length;
      if (quoted(from, to)) spans.push({ from, to });
      entry = i + 1;
    }
  }
  return spans;
}

// The notes of the editor state `state`, read with the syntax tree `tree`:
// each {line, from, to, text}, `line` counted from zero, `from` and `to`
// the offsets in the document of the note's quotes, the closing one
// included, and `text` the explanation between them. A line the tree does
// not yet cover holds none.
function noteRanges(state, tree = syntaxTree(state)) {
  const ranges = [];
  for (let number = 1; number <= state.doc.lines; number++) {
    const line = state.doc.line(number);
    if (line.to > tree.length) break;
    const marker = annotationStart(tree, line);
    if (marker === null) continue;
    const after = marker + 2;
    for (const span of noteSpans(state.sliceDoc(after, line.to))) {
      const from = after + span.from;
      const to = after + span.to;
      ranges.push({ line: number - 1, from, to, text: state.sliceDoc(from + 1, to - 1) });
    }
  }
  return ranges;
}

// The decorations of the notes `ranges` of the editor state `state` outside
// the lines drawn in full: each note replaced by its glyph.
function noteDecorations(ranges, state) {
  const inFull = linesInFull(state);
  return Decoration.set(
    ranges
      .filter((range) => !inFull.has(range.line))
      .map((range) => Decoration.replace({ widget: new NoteGlyph(range.text) }).range(range.from, range.to)),
  );
}

// The notes of the document `text` as the editor draws them, with the
// cursor at the text's start: each {line, from, to, text}, `line` counted
// from one, `from` and `to` the offsets in the line, in UTF-16 code units,
// of the span a glyph replaces, and `text` that span as written. The tests
// run it under Node.
export function noteMarkersOf(text) {
  const state = EditorState.create({ doc: text, extensions: [blLanguage] });
  const tree = ensureSyntaxTree(state, state.doc.length, 5000) ?? syntaxTree(state);
  const markers = [];
  noteDecorations(noteRanges(state, tree), state).between(0, state.doc.length, (from, to) => {
    const line = state.doc.lineAt(from);
    markers.push({
      line: line.number,
      from: from - line.from,
      to: to - line.from,
      text: state.sliceDoc(from, to),
    });
  });
  return markers;
}

// --- the preview's text ---

// The inline rule of a note's mathematics (the delimiters of
// the explanatory-annotations note of the Matsya build area): `\(…\)` inline and
// `\[…\]` displayed, each up to its first closing delimiter. It stands
// before markdown-it's escapes, which would read `\(` as `(`.
function mathematics(state, silent) {
  const { src, pos } = state;
  const open = src.slice(pos, pos + 2);
  const close = open === "\\(" ? "\\)" : open === "\\[" ? "\\]" : null;
  if (close === null) return false;
  const end = src.indexOf(close, pos + 2);
  if (end < 0) return false;
  if (!silent) {
    const token = state.push("mathematics", "", 0);
    token.content = src.slice(pos + 2, end);
    token.markup = open;
  }
  state.pos = end + 2;
  return true;
}

// The Markdown of a note: markdown-it's default rules with no HTML of the
// text's own and no image, link or autolink, so that a preview fetches
// nothing and leaves the page where it is, and the mathematics typeset by
// KaTeX. The preview adds no hover and no color that design pass 10 §9
// does not give (the plan's texts rule). A formula KaTeX cannot typeset
// is drawn as written, delimiters included, in the preview's ink. A
// command KaTeX does not trust, such as `\href`, is drawn by KaTeX as its
// name in `errorColor`, here the preview's ink.
const markdown = new MarkdownIt({ html: false, linkify: false, typographer: false });
markdown.disable(["image", "link", "autolink"]);
markdown.inline.ruler.before("escape", "mathematics", mathematics);
markdown.renderer.rules.mathematics = (tokens, index) => {
  const { content, markup } = tokens[index];
  try {
    return katex.renderToString(content, {
      displayMode: markup === "\\[",
      throwOnError: true,
      errorColor: "currentColor",
      strict: false,
    });
  } catch {
    return markdown.utils.escapeHtml(`${markup}${content}${markup === "\\(" ? "\\)" : "\\]"}`);
  }
};

// The HTML of the preview of the note whose explanation is `note`.
export function notePreview(note) {
  return markdown.render(note);
}

// --- the glyphs, the toggle and the preview ---

// The effect that draws every note as written (true) or as its glyph
// (false).
export const setShowNotesEffect = StateEffect.define();

// The effect that opens the preview of a note, {pos, text}, the offset of
// its glyph and its explanation, or closes it (null).
const setPreview = StateEffect.define();

// The glyph of a note whose explanation is `text`: the 16-px Codicon
// `note`, focusable and named `note` for a screen reader (design pass 10
// §9). Two glyphs of one explanation are alike, so that the editor keeps
// the element, and its focus, when it draws the decorations again. The
// editor reads none of the glyph's events; the glyph's own listeners ask
// previewControl to open, close or reveal.
class NoteGlyph extends WidgetType {
  constructor(text) {
    super();
    this.text = text;
  }

  eq(other) {
    return other.text === this.text;
  }

  toDOM(view) {
    const glyph = document.createElement("span");
    glyph.className = "codicon codicon-note bl-note-marker";
    glyph.tabIndex = 0;
    glyph.setAttribute("role", "button");
    glyph.setAttribute("aria-label", "note");
    const control = () => view.plugin(previewControl);
    glyph.addEventListener("mouseenter", () => control()?.hover(glyph, this.text));
    glyph.addEventListener("mouseleave", () => control()?.leave());
    glyph.addEventListener("focus", () => control()?.open(glyph, this.text));
    glyph.addEventListener("blur", () => control()?.leave());
    // a press keeps the cursor and the focus where they are; the click
    // that follows reveals the line
    glyph.addEventListener("mousedown", (event) => event.preventDefault());
    glyph.addEventListener("click", () => control()?.reveal(glyph));
    glyph.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      control()?.reveal(glyph);
    });
    return glyph;
  }
}

// The notes: the toggle, true while every note is drawn as written; the
// notes of the document, found again when the document or its syntax tree
// changes; and their decorations, made again at every change of the notes,
// the selection, the refusals or the toggle.
const noteField = StateField.define({
  create(state) {
    const ranges = noteRanges(state);
    return { shown: false, ranges, decorations: noteDecorations(ranges, state) };
  },
  update(value, tr) {
    let shown = value.shown;
    for (const effect of tr.effects) if (effect.is(setShowNotesEffect)) shown = effect.value;
    const parsed = syntaxTree(tr.startState) !== syntaxTree(tr.state);
    const ranges = tr.docChanged || parsed ? noteRanges(tr.state) : value.ranges;
    const refusals = tr.effects.some((effect) => effect.is(setDiagnosticsEffect));
    if (shown === value.shown && ranges === value.ranges && !tr.selection && !refusals) {
      return value;
    }
    const decorations = shown ? Decoration.none : noteDecorations(ranges, tr.state);
    return { shown, ranges, decorations };
  },
  provide: (field) => EditorView.decorations.from(field, (value) => value.decorations),
});

// The preview of a note's glyph, a tooltip `.cm-tooltip.bl-note` under the
// glyph whose text is the explanation's Markdown (notePreview). Its element
// carries the role `tooltip` and describes the glyph for a screen reader
// while it stands.
let previews = 0;
function previewView(view, text) {
  const dom = document.createElement("div");
  dom.className = "bl-note";
  dom.id = `bl-note-preview-${++previews}`;
  dom.setAttribute("role", "tooltip");
  dom.innerHTML = notePreview(text);
  const control = view.plugin(previewControl);
  const glyph = control?.glyph ?? null;
  return {
    dom,
    getCoords: (pos) => (glyph?.isConnected ? glyph.getBoundingClientRect() : view.coordsAtPos(pos)),
    mount() {
      if (control) control.shown = dom;
      glyph?.setAttribute("aria-describedby", dom.id);
      dom.addEventListener("mouseleave", () => control?.leave());
    },
    destroy() {
      if (control?.shown === dom) control.shown = null;
      if (glyph?.getAttribute("aria-describedby") === dom.id) glyph.removeAttribute("aria-describedby");
    },
  };
}

// The open preview, {pos, text}, or null: closed by any change of the
// document or the selection and by the toggle that draws the notes as
// written.
const preview = StateField.define({
  create() {
    return null;
  },
  update(value, tr) {
    let next = tr.docChanged || tr.selection ? null : value;
    for (const effect of tr.effects) {
      if (effect.is(setPreview)) next = effect.value;
      if (effect.is(setShowNotesEffect) && effect.value) next = null;
    }
    return next;
  },
  provide: (field) =>
    showTooltip.from(field, (value) =>
      value === null
        ? null
        : { pos: value.pos, above: false, create: (view) => previewView(view, value.text) },
    ),
});

// The pointer and the focus of the editor's glyphs and preview, which open
// and close the preview (design pass 10 §9). `glyph` is the glyph whose
// preview is open, `shown` the preview's element while it is mounted. The
// preview closes CROSSING_MS after the pointer or the focus leaves where
// neither the pointer is over the glyph or the preview nor the glyph holds
// the focus, and at once on Escape wherever the focus stands.
const previewControl = ViewPlugin.fromClass(
  class {
    constructor(view) {
      this.view = view;
      this.glyph = null;
      this.shown = null;
      this.hoverTimer = -1;
      this.closeTimer = -1;
      this.escape = (event) => {
        if (event.key === "Escape" && this.view.state.field(preview) !== null) this.close();
      };
      view.dom.ownerDocument.addEventListener("keydown", this.escape, true);
    }

    update(update) {
      if (update.state.field(preview) === null) this.glyph = null;
    }

    // The pointer enters `glyph`: its preview opens once the pointer has
    // rested on it for HOVER_MS.
    hover(glyph, text) {
      clearTimeout(this.hoverTimer);
      if (this.glyph === glyph) return;
      this.hoverTimer = setTimeout(() => {
        if (glyph.isConnected && glyph.matches(":hover")) this.open(glyph, text);
      }, HOVER_MS);
    }

    // The pointer leaves a glyph or the preview, or the focus leaves a
    // glyph.
    leave() {
      clearTimeout(this.hoverTimer);
      clearTimeout(this.closeTimer);
      this.closeTimer = setTimeout(() => this.closeUnheld(), CROSSING_MS);
    }

    closeUnheld() {
      const glyph = this.glyph;
      if (glyph === null) return;
      const held =
        glyph.isConnected &&
        (glyph.matches(":hover") || glyph.ownerDocument.activeElement === glyph);
      if (!held && !this.shown?.matches(":hover")) this.close();
    }

    open(glyph, text) {
      clearTimeout(this.hoverTimer);
      clearTimeout(this.closeTimer);
      if (this.glyph === glyph) return;
      this.glyph = glyph;
      this.view.dispatch({ effects: setPreview.of({ pos: this.view.posAtDOM(glyph), text }) });
    }

    close() {
      clearTimeout(this.hoverTimer);
      clearTimeout(this.closeTimer);
      this.glyph = null;
      if (this.view.state.field(preview) !== null) this.view.dispatch({ effects: setPreview.of(null) });
    }

    // Enter or a click on `glyph`: the cursor after the note's opening
    // quote and the focus in the editor, so that the line is drawn in full
    // until the cursor leaves it.
    reveal(glyph) {
      const pos = this.view.posAtDOM(glyph);
      this.close();
      this.view.dispatch({ selection: { anchor: pos + 1 } });
      this.view.focus();
    }

    destroy() {
      clearTimeout(this.hoverTimer);
      clearTimeout(this.closeTimer);
      this.view.dom.ownerDocument.removeEventListener("keydown", this.escape, true);
    }
  },
);

// The extension of the notes: their decorations, the preview and its
// control.
export const notes = [noteField, preview, previewControl];
