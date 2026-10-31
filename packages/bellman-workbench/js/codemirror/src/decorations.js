// The decorations of the stage name and of the annotations (model
// interface specification 0.4, §5.4; unit R, brief rule 5; R-D26, R-D34).
// They are drawn only: none replaces, inserts or hides a character, so that
// the document, the undo history and the places of the refusals are those
// of the text as written. theme.js draws the classes.
//
// The stage name is the value of the line whose `metadataName` token reads
// `@stage` (stageName of bl_language.js): the mark `bl-stage-name` on the
// line `bl-stage-line`, whose gutter elements carry the class
// `bl-stage-line` too (L-D3).
//
// A line that holds an `annotation` token of the language's syntax tree is
// the line `bl-annotated`, which theme.js draws as a flex row: the mark
// `bl-statement` from the line's start to its `::`, and the mark
// `bl-annotation` from the `::` to the line's end. The two marks cover the
// whole line, since a flex row does not draw a child that is white space
// alone. They are outer decorations, which wrap every other decoration of
// the line, so that each stays one element, a child of the line. The mark
// `bl-annotation` includes its end, so that it also wraps a widget that
// replaces the text up to the line's end, the glyph of a bare note `:: "…"`
// (notes.js): CodeMirror wraps such a widget in a mark that ends where it
// ends only if the mark includes its end, and would otherwise draw the
// glyph after the mark, as an item of the line's flex row.
//
// The module also answers two questions that the decorations which do
// hide text ask: where a line's annotation starts (annotationStart, which
// notes.js reads), and which lines are drawn in full (linesInFull, which
// the hidden types of editor.js and the notes of notes.js read).
import { syntaxTree } from "@codemirror/language";
import { forEachDiagnostic } from "@codemirror/lint";
import { Prec, RangeSet, StateField } from "@codemirror/state";
import { Decoration, EditorView, GutterMarker, ViewPlugin, gutterLineClass } from "@codemirror/view";

import { stageName } from "./bl_language.js";

const stageLine = Decoration.line({ class: "bl-stage-line" });
const stageNameMark = Decoration.mark({ class: "bl-stage-name" });
const annotatedLine = Decoration.line({ class: "bl-annotated" });
const statementMark = Decoration.mark({ class: "bl-statement" });
const annotationMark = Decoration.mark({ class: "bl-annotation", inclusiveEnd: true });

// The decorations of the stage name of the editor state `state`.
function stageNameDecorations(state) {
  const name = stageName(state);
  if (name === null) return Decoration.none;
  return Decoration.set([
    stageLine.range(state.doc.line(name.line).from),
    stageNameMark.range(name.from, name.to),
  ]);
}

// The gutter marker of the stage name's line, which gives each of its
// gutter elements the class `bl-stage-line`; theme.js sets the line number
// there on the name's baseline (L-D3).
const stageLineMarker = new (class extends GutterMarker {
  constructor() {
    super();
    this.elementClass = "bl-stage-line";
  }
})();

// The offset at which the stage name's line of the editor state `state`
// starts; null where the state writes no stage name.
function stageLineStart(state) {
  const name = stageName(state);
  return name === null ? null : state.doc.line(name.line).from;
}

// The start of the stage name's line, found again when the document or the
// syntax tree changes, and the class of its gutter elements.
const stageLineGutter = StateField.define({
  create: stageLineStart,
  update(from, tr) {
    const parsed = syntaxTree(tr.startState) !== syntaxTree(tr.state);
    return tr.docChanged || parsed ? stageLineStart(tr.state) : from;
  },
  provide: (field) =>
    gutterLineClass.from(field, (from) =>
      from === null ? RangeSet.empty : RangeSet.of([stageLineMarker.range(from)]),
    ),
});

// The offset of the `::` of the line `line` of the syntax tree `tree`: the
// start of the line's first `annotation` token, since the tokenizer gives
// that token first to the `::` of its line; null where the line holds none.
export function annotationStart(tree, line) {
  let start = null;
  tree.iterate({
    from: line.from,
    to: line.to,
    enter(node) {
      if (start === null && node.name === "annotation" && node.from >= line.from) {
        start = node.from;
      }
    },
  });
  return start;
}

// The lines of `state`, counted from zero, drawn in full while the types or
// the notes are hidden: every line a selection range touches, as the VS
// Code extension leaves the lines of its selections, and every line a
// refusal's range touches, so that a refusal inside a hidden span is drawn
// at its position (design pass 10 §9).
export function linesInFull(state) {
  const lines = new Set();
  const add = (from, to) => {
    const last = state.doc.lineAt(to).number - 1;
    for (let line = state.doc.lineAt(from).number - 1; line <= last; line++) lines.add(line);
  };
  for (const range of state.selection.ranges) add(range.from, range.to);
  forEachDiagnostic(state, (_, from, to) => add(from, to));
  return lines;
}

// The decorations of the annotated lines among the lines the editor `view`
// draws, each line once.
function annotationDecorations(view) {
  const { state } = view;
  const tree = syntaxTree(state);
  const ranges = [];
  let last = 0;
  for (const { from, to } of view.visibleRanges) {
    for (let line = state.doc.lineAt(from); ; line = state.doc.line(line.number + 1)) {
      if (line.number > last) {
        last = line.number;
        const marker = annotationStart(tree, line);
        if (marker !== null) {
          ranges.push(annotatedLine.range(line.from));
          if (marker > line.from) ranges.push(statementMark.range(line.from, marker));
          ranges.push(annotationMark.range(marker, line.to));
        }
      }
      if (line.to >= to || line.number === state.doc.lines) break;
    }
  }
  return Decoration.set(ranges);
}

// The extension that draws the stage name and the annotations: two
// decoration sets, made again when the document, the drawn lines or the
// syntax tree change, and the class of the stage name's gutter elements
// (stageLineGutter). The stage name's are decorations of the highest
// precedence, inside the highlighting's, so that its mark is the element
// nearest the text and its color is not the token's.
export const decorations = ViewPlugin.fromClass(
  class {
    constructor(view) {
      this.stageName = stageNameDecorations(view.state);
      this.annotations = annotationDecorations(view);
    }

    update(update) {
      const parsed = syntaxTree(update.startState) !== syntaxTree(update.state);
      if (update.docChanged || parsed) this.stageName = stageNameDecorations(update.state);
      if (update.docChanged || parsed || update.viewportChanged) {
        this.annotations = annotationDecorations(update.view);
      }
    }
  },
  {
    provide: (plugin) => [
      Prec.highest(
        EditorView.decorations.of((view) => view.plugin(plugin)?.stageName ?? Decoration.none),
      ),
      EditorView.outerDecorations.of((view) => view.plugin(plugin)?.annotations ?? Decoration.none),
      stageLineGutter,
    ],
  },
);
