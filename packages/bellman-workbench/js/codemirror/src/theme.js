// The editor's theme. Every color is a custom property of brand.css,
// written `var(--bl-…)`, so that one table decides the page and the
// high-contrast setting reaches the editor (spec 0.4 §5.2; unit R, brief
// rule 5, review 5). The text is set in Code, IBM Plex Mono at 12.5 px, on
// lines of 17.9 px, with no weight and no slant the browser makes for a
// face that does not hold it (design pass 13 §3; C13); the tokens take the
// colors of §5.2 and Design brief 7 §8, and the lines the treatments of
// §5.4. No radius and no shadow, but the lint tooltip's, an overlay of the
// system (design pass 13 §5; the fix wave Q3b, item 20, N8).
import { HighlightStyle } from "@codemirror/language";
import { RangeSet, StateEffect, StateField } from "@codemirror/state";
import { Decoration, EditorView, GutterMarker, gutterLineClass } from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

import { perchTagName, roleTagName } from "./bl_language.js";

// The color of the custom property `property` at `percent` percent
// opacity: a wash, or a muted color.
const faded = (property, percent) =>
  `color-mix(in srgb, var(${property}) ${percent}%, transparent)`;

// The column at which a line wraps, the width of the project's printed
// cards (R-D5). The wrap is CodeMirror's line wrapping
// (EditorView.lineWrapping in editor.js), drawn only: no newline is
// inserted, and a refusal keeps its position. A line has a left padding of
// LINE_PADDING and HANG characters of the monospaced face (`ch`), a right
// padding of LINE_PADDING and a text indent of minus HANG characters,
// which its first visual line alone takes: the first visual line holds at
// most WRAP_COLUMN characters, and each further visual line hangs HANG
// characters to its right (spec 0.4 §5.4). No guide is drawn after the
// column. LINE_PADDING is 8 px, so that a line number stands 32 px from
// its line's text: the numbers' right padding of 8 px, the refusals'
// gutter of 16 px and the line's padding (design pass 13 §3; D19).
export const WRAP_COLUMN = 78;
const HANG = 4;
const LINE_PADDING = "8px";

// The stage name and its line (L-D3): the Title step, Archivo 400 at 18 px
// on a line of 24 px, the size spec 0.4 §5.2 gives the thread title
// (design pass 13 §3).
const STAGE_NAME_FONT = "var(--bl-t-title)";

// The width of the text minimap (minimap.js; spec 0.4 §5.4), which the
// editor's scroller leaves free at its right, so that the strip stands
// beside the text and the text keeps its measure of WRAP_COLUMN.
const MINIMAP_WIDTH = "60px";

// The colors and sizes of the editor's own parts: ground, gutter, cursor,
// the current line and the selected lines, the matching bracket, the
// search and lint panels, the refusal's marks. The text has no letter
// spacing, so that a character of the monospaced face is one `ch` wide;
// the page's body would otherwise give it 0.5 px. The line numbers are in
// Code small, 11 px, each on its line's baseline, where an empty box in the
// source's face and line before the number places the baseline of the
// number's line, in --bl-line-number, 42 percent ice-3 unless the
// high-contrast setting makes them opaque (Design brief 7 §8; spec 0.4
// §5.8; design pass 13 §3, C7, D19).
export const brandTheme = EditorView.theme(
  {
    "&": {
      backgroundColor: "var(--bl-navy)",
      color: "var(--bl-ice)",
      font: "var(--bl-t-code)",
      fontSynthesis: "none",
      letterSpacing: "normal",
      height: "100%",
      borderRadius: "0",
      boxShadow: "none",
    },
    ".cm-scroller": {
      fontFamily: "var(--bl-mono)",
      lineHeight: "17.9px",
      marginRight: MINIMAP_WIDTH,
    },
    ".cm-content": {
      caretColor: "var(--bl-ice)",
      padding: "8px 0",
      maxWidth: `calc(${WRAP_COLUMN}ch + 2 * ${LINE_PADDING})`,
    },
    ".cm-line": {
      padding: `0 ${LINE_PADDING} 0 calc(${LINE_PADDING} + ${HANG}ch)`,
      textIndent: `-${HANG}ch`,
    },
    // The wrap breaks a line at a space or after a hyphen, never inside an
    // operator such as `->`, `:=` or `<=`.
    ".tok-operator": { whiteSpace: "nowrap" },
    // The stage name (decorations.js): STAGE_NAME_FONT, in ice, at the
    // width --bl-stage-name-stretch gives (spec 0.4 §5.2; R-D2; L-D3). Its
    // line, `bl-stage-line`, is the Title step's 24 px high, since the
    // 17.9 px of the line's own text stand within the stage name's line
    // height.
    ".bl-stage-name": {
      color: "var(--bl-ice)",
      font: STAGE_NAME_FONT,
      fontStretch: "var(--bl-stage-name-stretch)",
    },
    // A line number stands on its line's baseline: an empty box in the
    // source's face, size and line height before the number places the
    // baseline of the number's line where the text places that of its own
    // (D19); and the number of the stage name's line (decorations.js) on
    // the name's baseline (L-D3), the box in the name's face.
    ".cm-lineNumbers .cm-gutterElement::before": {
      content: '""',
      font: "var(--bl-t-code)",
      lineHeight: "inherit",
    },
    ".cm-lineNumbers .cm-gutterElement.bl-stage-line::before": {
      content: '""',
      font: STAGE_NAME_FONT,
      fontStretch: "var(--bl-stage-name-stretch)",
    },
    // An annotated line (decorations.js) is a flex row: the statement,
    // then its annotation at the right edge of the line's content, or
    // below the statement where the two do not fit on one row (spec 0.4
    // §5.4; R-D26). The statement takes the line's text indent and wraps
    // with its hang; the annotation takes none, and wraps within itself
    // only where it is wider than the line, so that the editor's content
    // is never wider than the scroller and no text stands under the
    // minimap (unit L, Task 22).
    ".cm-line.bl-annotated": { display: "flex", flexWrap: "wrap", columnGap: "16px" },
    ".bl-statement": { flex: "0 1 auto", minWidth: "0", whiteSpace: "pre-wrap" },
    ".bl-annotation": { marginLeft: "auto", minWidth: "0", whiteSpace: "pre-wrap", textIndent: "0" },
    // A note's glyph (notes.js): the 16-px Codicon `note` in ink-3, and in
    // ink-1 under the pointer and with the focus; the focus from the
    // keyboard also draws the 1-px accent ring of the page's controls
    // (design pass 10 §§3 and 9).
    ".bl-note-marker": { color: "var(--bl-ink-3)", cursor: "pointer", verticalAlign: "text-bottom" },
    ".bl-note-marker:hover, .bl-note-marker:focus": { color: "var(--bl-ink-1)" },
    ".bl-note-marker:focus-visible": { outline: "1px solid var(--bl-accent)", outlineOffset: "1px" },
    // The text minimap (minimap.js): a strip MINIMAP_WIDTH wide at the
    // editor's right edge with no ground of its own, so that the current
    // line's wash does not run into it (design pass 13 §4; Q-D23), its
    // marks 2 px high and 1 px apart, the first on the text's first line,
    // 8 px inside the strip's top as the content's padding, 4 px inside its
    // left edge and 12 px inside its right, so that the longest marks end
    // on the column's right text edge, under `Save` (D17; the fix wave Q3b,
    // item 18), a header's in 60 percent ice, the
    // stage name's in 80 percent ultramarine-light and any other line's in
    // 22 percent ice (spec 0.4 §5.4; Design brief 7 §8 and its frame 7a).
    // minimap.js sets the strip at the scroller's top and height.
    ".bl-minimap": {
      position: "absolute",
      top: "0",
      bottom: "0",
      right: "0",
      width: MINIMAP_WIDTH,
      boxSizing: "border-box",
      padding: "8px 12px 2px 4px",
      overflow: "hidden",
    },
    ".bl-minimap-mark": { height: "2px", marginBottom: "1px" },
    '.bl-minimap-mark[data-kind="header"]': { backgroundColor: faded("--bl-ice", 60) },
    '.bl-minimap-mark[data-kind="stage"]': {
      backgroundColor: faded("--bl-ultramarine-light", 80),
    },
    '.bl-minimap-mark[data-kind="line"]': { backgroundColor: faded("--bl-ice", 22) },
    "&.cm-focused": { outline: "none" },
    // The current line: a 1.5 px ice caret, a 4 percent ice wash and its
    // number in ice-2 (spec 0.4 §§5.4 and 5.8).
    ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--bl-ice)", borderLeftWidth: "1.5px" },
    ".cm-activeLine": { backgroundColor: faded("--bl-ice", 4) },
    ".cm-gutters": {
      backgroundColor: "var(--bl-navy)",
      color: "var(--bl-line-number)",
      border: "none",
      borderRadius: "0",
    },
    // The number column at least 36 px, so that the refusals' gutter and
    // the text after it begin on whole pixels (the fix wave Q3b, item 18;
    // D29).
    ".cm-gutter.cm-lineNumbers .cm-gutterElement": {
      padding: "0 8px 0 14px",
      minWidth: "36px",
      font: "var(--bl-t-code-small)",
      lineHeight: "inherit",
    },
    ".cm-activeLineGutter": { backgroundColor: faded("--bl-ice", 4), color: "var(--bl-ice-2)" },
    // A selected line (selectedLines below): a 5 percent ice wash, its
    // number in ice-2 and the common 3 px ultramarine-light bar at the
    // gutter's left edge (spec 0.4 §§5.2 and 5.4). The selected text keeps
    // its own ground over the wash. The line a preview marks (previewedLine
    // below) is drawn as a selected line, since the preview selects it in
    // the text (Design brief 7 §15).
    ".cm-line.bl-selected-line, .cm-gutterElement.bl-selected-line, .cm-line.bl-preview-line, .cm-gutterElement.bl-preview-line":
      { backgroundColor: faded("--bl-ice", 5) },
    ".cm-gutterElement.bl-selected-line, .cm-gutterElement.bl-preview-line": {
      color: "var(--bl-ice-2)",
    },
    ".cm-lineNumbers .cm-gutterElement.bl-selected-line, .cm-lineNumbers .cm-gutterElement.bl-preview-line":
      { boxShadow: "inset 3px 0 0 var(--bl-ultramarine-light)" },
    "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection":
      { backgroundColor: faded("--bl-ice-2", 22) },
    // Selected text keeps the color of its token; the page's own selection
    // rule in brand.css would otherwise draw it in navy.
    ".cm-line ::selection, .cm-line::selection": { color: "currentColor" },
    ".cm-matchingBracket, &.cm-focused .cm-matchingBracket": {
      backgroundColor: "transparent",
      outline: "1px solid var(--bl-ice-3)",
    },
    ".cm-nonmatchingBracket, &.cm-focused .cm-nonmatchingBracket": {
      outline: "1px solid var(--bl-orange)",
    },
    ".cm-searchMatch": { backgroundColor: faded("--bl-number", 30), outline: "none" },
    ".cm-searchMatch.cm-searchMatch-selected": { backgroundColor: faded("--bl-number", 55) },
    ".cm-selectionMatch": { backgroundColor: faded("--bl-ice-2", 14) },
    // The refusal's underline and its gutter mark, the one orange piece.
    // The mark is a 3 px orange bar, the ground of the marker's own
    // element over the line's height (Design brief 7 §14; ruling R-P5), in
    // place of the lint package's image, which can read no custom property.
    ".cm-lintRange-error": {
      backgroundImage: "none",
      borderBottom: "2px solid var(--bl-orange)",
      paddingBottom: "1px",
    },
    ".cm-lintPoint-error:after": { borderBottomColor: "var(--bl-orange)" },
    // the refusals' gutter, 16 px wide, its bar 4 px in
    ".cm-gutter-lint": { width: "16px" },
    ".cm-gutter-lint .cm-gutterElement": { padding: "0 4px 0 4px" },
    ".cm-lint-marker": { width: ".7em", height: ".7em", margin: ".35em 0 0 0" },
    ".cm-lint-marker-error": {
      content: "normal",
      width: "3px",
      height: "100%",
      margin: "0",
      backgroundColor: "var(--bl-orange)",
    },
    // The search and lint panels stand on the chrome in ice, their fields
    // on the raised surface (spec 0.4 §5.2); the lint tooltip, an overlay,
    // stands in the overlay form of the system, raised within the control
    // border, with the library's radius of 4 px and the overlays' shadow,
    // as Goto Anything and the lists over the graph (design pass 13 §5,
    // E3, Q-D11; the fix wave Q3b, item 20, N8); the panels' fields and
    // buttons, controls, take the edge value, the control border.
    ".cm-tooltip": {
      backgroundColor: "var(--bl-raised)",
      color: "var(--bl-ice)",
      border: "1px solid var(--bl-control-border)",
      borderRadius: "var(--bl-radius)",
      boxShadow: "var(--bl-overlay-shadow)",
      fontFamily: "var(--bl-mono)",
    },
    ".cm-tooltip.cm-tooltip-lint .cm-diagnostic": { borderLeftColor: "var(--bl-orange)" },
    ".cm-diagnostic-error": { borderLeftColor: "var(--bl-orange)" },
    ".cm-diagnosticText": { whiteSpace: "pre-wrap" },
    ".cm-panels": {
      backgroundColor: "var(--bl-chrome)",
      color: "var(--bl-ice)",
      borderTop: "1px solid var(--bl-hairline)",
      fontFamily: "var(--bl-mono)",
    },
    ".cm-panels.cm-panels-top": { borderBottom: "1px solid var(--bl-hairline)" },
    ".cm-panel.cm-panel-lint ul [aria-selected], .cm-panel.cm-panel-lint ul:focus [aria-selected]": {
      backgroundColor: "var(--bl-navy-2)",
      color: "var(--bl-ice)",
    },
    ".cm-panel.cm-panel-lint ul li:hover": { backgroundColor: "var(--bl-navy-2)" },
    ".cm-panel button, .cm-panel input": {
      borderRadius: "0",
      fontFamily: "var(--bl-text)",
    },
    ".cm-textfield": {
      border: "1px solid var(--bl-control-border)",
      backgroundColor: "var(--bl-navy-2)",
      color: "var(--bl-ice)",
    },
    ".cm-button": {
      backgroundImage: "none",
      backgroundColor: "transparent",
      border: "1px solid var(--bl-control-border)",
      color: "var(--bl-ice-2)",
    },
  },
  { dark: true },
);

// The gutter marker of a selected line, which gives each of its gutter
// elements the class `bl-selected-line`.
const selectedLineMarker = new (class extends GutterMarker {
  constructor() {
    super();
    this.elementClass = "bl-selected-line";
  }
})();

// The line decoration of a selected line.
const selectedLine = Decoration.line({ class: "bl-selected-line" });

// The start offsets, in order and each once, of the lines that the
// non-empty ranges of the selection of `state` touch; a range that ends at
// the start of a line does not touch that line.
function selectedLineStarts(state) {
  const starts = new Set();
  for (const range of state.selection.ranges) {
    if (range.empty) continue;
    const first = state.doc.lineAt(range.from).number;
    let last = state.doc.lineAt(range.to).number;
    if (last > first && state.doc.line(last).from === range.to) last--;
    for (let number = first; number <= last; number++) starts.add(state.doc.line(number).from);
  }
  return Array.from(starts).sort((a, b) => a - b);
}

// The selected lines of spec 0.4 §5.4, the lines a selection covers: each
// carries the class `bl-selected-line` on its line and on its gutter
// elements, which brandTheme draws, made again at every change of the
// selection.
export const selectedLines = [
  EditorView.decorations.compute(["selection"], (state) =>
    Decoration.set(selectedLineStarts(state).map((from) => selectedLine.range(from))),
  ),
  gutterLineClass.compute(["selection"], (state) =>
    RangeSet.of(selectedLineStarts(state).map((from) => selectedLineMarker.range(from))),
  ),
];

// The effect that marks the line a preview of Goto Anything shows, by the
// offset at which the line starts, or that removes the mark (null) (spec
// 0.4 §5.8; unit R, brief rule 9).
export const setPreviewedLine = StateEffect.define();

// The gutter marker of the previewed line, which gives each of its gutter
// elements the class `bl-preview-line`.
const previewLineMarker = new (class extends GutterMarker {
  constructor() {
    super();
    this.elementClass = "bl-preview-line";
  }
})();

// The line decoration of the previewed line.
const previewLine = Decoration.line({ class: "bl-preview-line" });

// The previewed line: the offset at which it starts, or null where no line
// is marked, kept on its line through a change of the document. It carries
// the class `bl-preview-line` on its line and on its gutter elements, which
// brandTheme draws. The mark changes neither the selection nor the focus.
export const previewedLine = StateField.define({
  create() {
    return null;
  },
  update(from, tr) {
    let next = from === null || !tr.docChanged ? from : tr.newDoc.lineAt(tr.changes.mapPos(from)).from;
    for (const effect of tr.effects) if (effect.is(setPreviewedLine)) next = effect.value;
    return next;
  },
  provide: (field) => [
    EditorView.decorations.from(field, (from) =>
      from === null ? Decoration.none : Decoration.set([previewLine.range(from)]),
    ),
    gutterLineClass.from(field, (from) =>
      from === null ? RangeSet.empty : RangeSet.of([previewLineMarker.range(from)]),
    ),
  ],
});

// The colors of the tokens, by highlighting tag (spec 0.4 §5.2; Design
// brief 7 §8): a keyword, `argmax` among them, and any marked tag but a
// perch or a role tag in periwinkle; a perch tag in periwinkle at 600 and
// a role tag in mint at 600; a set in mint; a number in light orange and a
// parameter in light orange at 500; a function in ice and italic; a
// block's id in ice at 600; punctuation, a key, an annotation and a
// comment in ice-3; an operator in ice-2. A token §5.2 does not name keeps
// one of these colors: a classifier such as `@in` light orange, a string
// ice-2, a bound or declared name and a selector such as `[>]` ice.
export const brandHighlight = HighlightStyle.define([
  { tag: [t.keyword, t.tagName], color: "var(--bl-periwinkle)" },
  { tag: perchTagName, color: "var(--bl-periwinkle)", fontWeight: "600" },
  { tag: roleTagName, color: "var(--bl-mint)", fontWeight: "600" },
  { tag: t.typeName, color: "var(--bl-mint)" },
  { tag: [t.number, t.annotation], color: "var(--bl-number)" },
  { tag: t.constant(t.variableName), color: "var(--bl-number)", fontWeight: "500" },
  { tag: t.function(t.variableName), color: "var(--bl-ice)", fontStyle: "italic" },
  { tag: t.labelName, color: "var(--bl-ice)", fontWeight: "600" },
  { tag: [t.punctuation, t.propertyName, t.meta, t.lineComment], color: "var(--bl-ice-3)" },
  { tag: [t.operator, t.string], color: "var(--bl-ice-2)" },
  { tag: [t.atom, t.definition(t.variableName), t.local(t.variableName)], color: "var(--bl-ice)" },
]);
