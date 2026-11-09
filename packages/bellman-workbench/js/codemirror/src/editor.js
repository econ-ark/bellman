// The editor bundle's interface, window.bellmanEditor.
//
//   const handle = window.bellmanEditor.create(parent, {doc, path, revision, pauseMs,
//                                                       hideTypes, showNotes, shortcuts,
//                                                       roleWords, indent, onChange, onSave,
//                                                       onCursor, onInput, onUndo});
//   handle.setDocument(path, revision, text); handle.setDoc(text); handle.getDoc();
//   handle.setDiagnostics([...]); handle.setHideTypes(on); handle.setShowNotes(on);
//   handle.gotoLine(line, column, endLine, endColumn, focus);
//   handle.replaceSpans(edits, expected, {gesture, history}); handle.setShortcuts(table);
//   handle.focus(); handle.previewLine(line);
//   handle.findText(text); handle.view(); handle.setView(view); handle.destroy();
//   window.bellmanEditor.documentOf(element);
//   window.bellmanEditor.replaceSpansOf(element, edits, expected);
//   window.bellmanEditor.expandShortcut(before, table);
//   window.bellmanEditor.noteMarkersOf(text); window.bellmanEditor.notePreview(note);
//   window.bellmanEditor.version
//
// The document the editor holds is identified by `path` and `revision`, two
// values the host gives at create() and replaces with setDocument(path,
// revision, text); the editor reads neither. Every event carries them.
// onChange({path, revision, text}) is called once per pause: pauseMs (750
// by default) after the last edit, with the whole document. onSave({path,
// revision, text}) is called at once on Mod-s. onCursor({path, revision,
// line, column}) is called about 120 ms after the cursor last moved, with
// 1-based positions, the column counted in code points as the package
// counts it. onInput({path, revision}) is called at once at each change of
// the document that setDocument or setDoc did not make: typing, an undo,
// replaceSpans and a refusal's action (spec 0.4 §3.3). setDocument replaces
// the document without calling onChange or onInput; setDoc(text) does the
// same and keeps the path and the revision. Where either replaces the text,
// or setDocument is given another path than the document's, the editor's
// undo history begins again with the new document, so that an undo never
// restores one file's text into another file's tab (R-D45) nor a text the
// host replaced, which may hold several gestures (unit L, Task 17; defect 6
// of the UX simulation); with the same path and the same text the history
// stays.
// setDiagnostics takes the refusals Python found, with 1-based positions
// counted in code points, converts them to the code units the document
// counts, and sets them through @codemirror/lint; no linter runs in the
// browser. Each record is {line, column, end_line, end_column, message,
// severity, rule}: the underline runs over the range the package reports,
// and stands at the position alone where the record carries no end, since
// the editor guesses none; the hover shows the message and, after it, the
// rule as the diagnostic's source. A refusal with an `action`,
// {name, edits, expected}, has one button of that name in its tooltip,
// which applies `edits` as replaceSpans does, when the document is
// `expected` (`take the line out`, spec 0.4 §3.3). setHideTypes(true) draws
// every bracket group that carries an identity as its name alone, by the
// rule of hidden_types.js, and setHideTypes(false) draws the text in full;
// `hideTypes` is the first value. The quoted explanation of an annotation,
// a note, is drawn as a note glyph with its preview (notes.js; design pass
// 10 §9); setShowNotes(true) draws every note as written and
// setShowNotes(false) as its glyph again; `showNotes` is the first value,
// false where it is not given. noteMarkersOf(text) answers the spans the
// glyphs replace in `text`, and notePreview(note) the preview's HTML.
// Neither the types nor the notes change the document, the undo history or
// the unsaved state. documentOf(element) is the document of the
// editor that holds `element`, or null. Lines wrap at the column theme.js
// sets, and a wrapped line hangs by four characters; the wrap is drawn
// only, and inserts no newline. `roleWords` is the list of marked tags the
// tokenizer draws as role tags (setRoleWords of bl_language.js), none
// where it is not given; `indent` is the number of spaces of one indent,
// CodeMirror's own two where it is not given. Both are read once, at
// create().
// replaceSpans(edits, expected, options) applies the replacements the
// classification table or a gesture asks for, each {line, column, end_line,
// end_column, text} with 1-based positions in code points, as one
// transaction when the document is `expected`, and onChange follows as after
// typing; the transaction is one step of the undo history, joined to no
// edit before or after it. `options.gesture`, the key of a gesture that
// edits several files, marks that step as the gesture's; `options.history`
// false keeps the transaction out of the history, for the step of a gesture
// that an undo of the gesture asked of the host takes back (unit L, Task
// 17). replaceSpansOf(element, edits, expected) does the same for the editor
// that holds `element`, with no options.
// onUndo({path, revision, gesture, redo, text}) is called when an undo or a
// redo of the editor's history takes back or makes again the step that a
// gesture's key marks, with that key and `redo` true for a redo, so that
// the host does the same in the gesture's other files; and when Mod-z is
// pressed while the history holds no step to undo, with `gesture` null, so
// that the host may take back the last gesture that left this file's text
// (unit L, Task 17; amendment 02 of spec 0.4, principle 1 and ruling 15).
// `text` is the document after the undo or the redo, or as it stands.
// `shortcuts` is the table of the Unicode shortcuts, prefix to body, which
// setShortcuts replaces; Tab replaces the shortcut that ends the text before
// the cursor by its body (shortcuts.js) and indents where none ends there.
// gotoLine(line, column, endLine, endColumn, focus) places the cursor at
// (line, column), counted from one, the column in code points, and brings
// it into view; where endLine is given it selects the text from there to
// (endLine, endColumn), to the end of endLine where endColumn is null, and
// it gives the editor the focus unless `focus` is false. One function
// selects a line for adding a field (amendment 02 ruling 9) and for a
// gesture's line (unit J's decision J-D40).
// The four functions of a preview (spec 0.4 §5.8; unit R, brief rule 9)
// move neither the cursor nor the focus, and call neither onCursor nor
// onChange. previewLine(line) scrolls `line`, counted from one, to the
// middle of the editor and gives it the class `bl-preview-line`, which
// theme.js draws; previewLine(null), or a line the document does not hold,
// removes the class. findText(text) answers the lines of the document that
// hold `text`, the case ignored, in order and at most fifty, each {line,
// column, text}: the line counted from one, the column of the first match
// counted from one in code points, and the line's text; an empty `text`
// answers none. view() answers {top, left, anchor, head, line, column}:
// the scroll position in pixels, the main selection's anchor and head as
// offsets of the document, and the line and the column of its head as
// onCursor counts them. setView(view) restores the scroll position and the
// main selection of such a record, and removes the class of the preview;
// a selection equal to the editor's is left as it stands.
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
  isolateHistory,
  redoDepth,
  undoDepth,
} from "@codemirror/commands";
import { bracketMatching, indentUnit, syntaxHighlighting } from "@codemirror/language";
import {
  lintGutter,
  lintKeymap,
  setDiagnostics as lintSetDiagnostics,
  setDiagnosticsEffect,
} from "@codemirror/lint";
import { search, searchKeymap } from "@codemirror/search";
import {
  Annotation,
  Compartment,
  EditorState,
  Prec,
  StateEffect,
  StateField,
  Transaction,
} from "@codemirror/state";
import {
  Decoration,
  EditorView,
  drawSelection,
  highlightActiveLine,
  highlightActiveLineGutter,
  keymap,
  lineNumbers,
} from "@codemirror/view";
import { classHighlighter } from "@lezer/highlight";
import versions from "bellman-workbench-versions";

import { blLanguage, setRoleWords } from "./bl_language.js";
import { decorations, linesInFull } from "./decorations.js";
import { hiddenRanges } from "./hidden_types.js";
import { minimap } from "./minimap.js";
import { noteMarkersOf, notePreview, notes, setShowNotesEffect } from "./notes.js";
import { expandShortcut } from "./shortcuts.js";
import { brandHighlight, brandTheme, previewedLine, selectedLines, setPreviewedLine } from "./theme.js";

// A transaction of setDocument or setDoc carries this annotation; the update
// listener then schedules no onChange.
const externalChange = Annotation.define();

// A transaction of replaceSpans for a gesture that edits several files
// carries this annotation, whose value is the gesture's key (unit L, Task
// 17).
const gestureEdit = Annotation.define();

const DEFAULT_PAUSE_MS = 750;
const CURSOR_PAUSE_MS = 120;

// One code point of `text` at the code-unit offset `offset` is two code
// units when it is above 0xffff (𝑢 is U+1D462), else one.
function unitsAt(text, offset) {
  return text.codePointAt(offset) > 0xffff ? 2 : 1;
}

// The offset in `doc` of a 1-based line and column from Python, clamped
// to the document. Python counts a column in code points; the document
// counts offsets in UTF-16 code units. The offset advances over
// `column - 1` code points of the line, and a column past the line's end
// is the line's end.
function offsetOf(doc, line, column) {
  const lineNumber = Math.min(Math.max(1, line || 1), doc.lines);
  const lineText = doc.line(lineNumber);
  const text = lineText.text;
  let offset = 0;
  for (let left = Math.max(1, column || 1) - 1; left > 0 && offset < text.length; left--) {
    offset += unitsAt(text, offset);
  }
  return lineText.from + offset;
}

// The 1-based column, counted in code points, of the offset `offset` on the
// line `lineText` of the document: the inverse of offsetOf.
function columnOf(lineText, offset) {
  const text = lineText.text;
  const end = Math.min(offset - lineText.from, text.length);
  let column = 1;
  for (let i = 0; i < end; i += unitsAt(text, i)) column++;
  return column;
}

// The 1-based line and column of the main cursor of `state`, the column
// counted in code points.
function cursorOf(state) {
  const head = state.selection.main.head;
  const line = state.doc.lineAt(head);
  return { line: line.number, column: columnOf(line, head) };
}

// --- the edits of the classification table ---

// The replacements `edits` applied to the document of `view` as one
// transaction, when the document is `expected`, the text the classification
// table was read from: each {line, column, end_line, end_column, text}, the
// positions counted from one in code points, as the package counts them,
// converted by offsetOf to the code units the document counts. The
// transaction carries no externalChange annotation, so the update listener
// schedules onChange and the loop runs as after typing, and one undo
// reverts it: it is isolated in the history, so that no typing and no other
// replacement joins its step (unit L, Task 17). With `options.gesture` it
// carries that gesture's key (`gestureEdit`), and with `options.history`
// false it stands in no step of the history. Answers false, and changes
// nothing, where the document is not `expected`, so that no edit lands on
// text the table did not read.
function applySpans(view, edits, expected, options = {}) {
  const doc = view.state.doc;
  if (expected != null && doc.toString() !== expected) return false;
  const changes = (edits ?? []).map((edit) => ({
    from: offsetOf(doc, edit.line, edit.column),
    to: offsetOf(doc, edit.end_line, edit.end_column),
    insert: edit.text ?? "",
  }));
  if (changes.length > 0) {
    const annotations = [isolateHistory.of("full")];
    if (options.gesture != null) annotations.push(gestureEdit.of(options.gesture));
    if (options.history === false) annotations.push(Transaction.addToHistory.of(false));
    view.dispatch({ changes, userEvent: "input", annotations });
  }
  return true;
}

// applySpans for the editor whose DOM holds `element`; false where none
// does. The page's tests drive the write-back through it.
export function replaceSpansOf(element, edits, expected) {
  const view = element ? EditorView.findFromDOM(element) : null;
  return view ? applySpans(view, edits, expected) : false;
}

// --- the hidden types ---

// The effect that turns the hidden types on (true) or off (false).
const setHideTypesEffect = StateEffect.define();

// The decoration of one hidden span: its text is not drawn.
const hiddenSpan = Decoration.replace({});

// The hidden spans of the document `doc`, from hiddenRanges over its lines,
// each {line, from, to} with `line` counted from zero and `from` and `to`
// offsets in the document.
function hiddenSpansOf(doc) {
  return hiddenRanges(doc.toJSON()).map(({ line, from, to }) => {
    const start = doc.line(line + 1).from;
    return { line, from: start + from, to: start + to };
  });
}

// The decorations of the hidden spans `spans` outside the lines drawn in
// full (linesInFull of decorations.js).
function hiddenDecorations(spans, state) {
  const inFull = linesInFull(state);
  return Decoration.set(
    spans.filter((span) => !inFull.has(span.line)).map((span) => hiddenSpan.range(span.from, span.to)),
    true,
  );
}

// The toggle of the hidden types, the hidden spans of the document, found
// again at every change of the document, and their decorations, made again
// at every change of the document, the selection, the refusals or the
// toggle.
const hiddenTypes = StateField.define({
  create() {
    return { on: false, spans: [], decorations: Decoration.none };
  },
  update(value, tr) {
    let on = value.on;
    for (const effect of tr.effects) if (effect.is(setHideTypesEffect)) on = effect.value;
    if (!on) return value.on ? { on, spans: [], decorations: Decoration.none } : value;
    const spans = tr.docChanged || !value.on ? hiddenSpansOf(tr.state.doc) : value.spans;
    const refusals = tr.effects.some((effect) => effect.is(setDiagnosticsEffect));
    if (spans === value.spans && !tr.selection && !refusals) return value;
    return { on, spans, decorations: hiddenDecorations(spans, tr.state) };
  },
  provide: (field) => EditorView.decorations.from(field, (value) => value.decorations),
});

// The document of the editor whose DOM holds `element`, or null; a hidden
// span is not in the DOM, so a reader of the text asks here.
export function documentOf(element) {
  const view = element ? EditorView.findFromDOM(element) : null;
  return view ? view.state.doc.toString() : null;
}

// The rule of the Unicode shortcuts, for the set cells of the
// classification table, which expand as the editor does.
export { expandShortcut };

// The two functions of the notes (notes.js), which the tests run under
// Node: the spans the editor draws as note glyphs in a text, and the HTML
// of a note's preview.
export { noteMarkersOf, notePreview };

// The key Tab: the shortcut that ends the text before the cursor replaced
// by its body (shortcuts.js); false where the selection is not empty or no
// shortcut ends there, so that Tab indents as before.
function expandAtCursor(view, shortcuts) {
  const range = view.state.selection.main;
  if (!range.empty) return false;
  const line = view.state.doc.lineAt(range.head);
  const found = expandShortcut(line.text.slice(0, range.head - line.from), shortcuts);
  if (found === null) return false;
  const from = range.head - found.length;
  view.dispatch({
    changes: { from, to: range.head, insert: found.insert },
    selection: { anchor: from + found.insert.length },
    userEvent: "input",
  });
  return true;
}

export function create(parent, options = {}) {
  const pauseMs = options.pauseMs ?? DEFAULT_PAUSE_MS;
  const onChange = options.onChange ?? (() => {});
  const onSave = options.onSave ?? (() => {});
  const onCursor = options.onCursor ?? (() => {});
  const onInput = options.onInput ?? (() => {});
  const onUndo = options.onUndo ?? (() => {});
  // The table of the Unicode shortcuts, prefix to body, which setShortcuts
  // replaces; the key Tab reads it at each press.
  let shortcuts = options.shortcuts ?? {};
  const shortcutKeymap = Prec.high(
    keymap.of([{ key: "Tab", run: (view) => expandAtCursor(view, shortcuts) }]),
  );
  // The role words, set before the document is tokenized (R-D18).
  setRoleWords(options.roleWords ?? []);
  // One indent, `indent` spaces, which Tab inserts where no shortcut ends
  // (R-D33); CodeMirror's own where `indent` is not given.
  const indent = options.indent ? [indentUnit.of(" ".repeat(options.indent))] : [];
  // The compartment of the undo history, which replaceDocument empties when
  // another file's document replaces the current one (R-D45).
  const undoHistory = new Compartment();

  // The identity of the document the editor holds, as the host gave it.
  let path = options.path ?? null;
  let revision = options.revision ?? 0;
  // An event's record: the document's identity and the event's own fields.
  const event = (fields) => ({ path, revision, ...fields });

  let changeTimer = null;
  let cursorTimer = null;

  // The steps of the undo history that a gesture's key marks (unit L, Task
  // 17): `done`, each {gesture, depth}, the step that undoDepth counts as
  // `depth` once it was made or made again; `undone`, each {gesture, depth},
  // the step that redoDepth counts as `depth` once an undo took it back. A
  // step is isolated in the history, so that the depth names it alone.
  let marks = { done: [], undone: [] };

  // The marks after the transaction `tr`: an undo that takes back the
  // marked step at the top of the history moves its mark to `undone` and
  // calls onUndo with its key, and a redo that makes such a step again
  // moves it back and calls onUndo with `redo` true; a new step of the
  // history empties `undone`, as the history empties its redo branch, and
  // a step of replaceSpans with a gesture's key adds its mark. Where the
  // history dropped its oldest steps, past its depth limit, every depth
  // falls by the steps dropped, and a mark whose step was dropped goes.
  function followMarks(tr) {
    const record = (gesture, redo) =>
      onUndo(event({ gesture, redo, text: tr.state.doc.toString() }));
    if (tr.isUserEvent("undo")) {
      const top = marks.done[marks.done.length - 1];
      if (top && top.depth === undoDepth(tr.startState)) {
        marks.done.pop();
        marks.undone.push({ gesture: top.gesture, depth: redoDepth(tr.state) });
        record(top.gesture, false);
      }
      return;
    }
    if (tr.isUserEvent("redo")) {
      const top = marks.undone[marks.undone.length - 1];
      if (top && top.depth === redoDepth(tr.startState)) {
        marks.undone.pop();
        marks.done.push({ gesture: top.gesture, depth: undoDepth(tr.state) });
        record(top.gesture, true);
      }
      return;
    }
    const stepped =
      tr.docChanged &&
      !tr.annotation(externalChange) &&
      tr.annotation(Transaction.addToHistory) !== false;
    if (!stepped) return;
    marks.undone = [];
    const before = undoDepth(tr.startState);
    const after = undoDepth(tr.state);
    if (after < before) {
      const dropped = before + 1 - after;
      marks.done = marks.done
        .map((mark) => ({ ...mark, depth: mark.depth - dropped }))
        .filter((mark) => mark.depth > 0);
    }
    const gesture = tr.annotation(gestureEdit);
    if (gesture != null) marks.done.push({ gesture, depth: after });
  }

  // Mod-z while the history holds no step to undo: onUndo with no key,
  // the host then taking back the last gesture that left this file's
  // text, where one did (unit L, Task 17). With a step to undo, the
  // history's own Mod-z acts.
  const undoKeymap = Prec.high(
    keymap.of([
      {
        key: "Mod-z",
        run: (view) => {
          if (undoDepth(view.state) > 0) return false;
          onUndo(event({ gesture: null, redo: false, text: view.state.doc.toString() }));
          return true;
        },
      },
    ]),
  );

  const saveKeymap = Prec.highest(
    keymap.of([
      {
        key: "Mod-s",
        preventDefault: true,
        run: (view) => {
          onSave(event({ text: view.state.doc.toString() }));
          return true;
        },
      },
    ]),
  );

  const listener = EditorView.updateListener.of((update) => {
    for (const tr of update.transactions) followMarks(tr);
    if (update.docChanged) {
      const external = update.transactions.some((tr) => tr.annotation(externalChange));
      if (changeTimer !== null) {
        clearTimeout(changeTimer);
        changeTimer = null;
      }
      if (!external) {
        onInput(event({}));
        changeTimer = setTimeout(() => {
          changeTimer = null;
          onChange(event({ text: update.view.state.doc.toString() }));
        }, pauseMs);
      }
    }
    if (update.selectionSet || update.docChanged) {
      if (cursorTimer !== null) clearTimeout(cursorTimer);
      cursorTimer = setTimeout(() => {
        cursorTimer = null;
        onCursor(event(cursorOf(update.view.state)));
      }, CURSOR_PAUSE_MS);
    }
  });

  const state = EditorState.create({
    doc: options.doc ?? "",
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightActiveLine(),
      selectedLines,
      previewedLine,
      undoHistory.of(history()),
      drawSelection(),
      bracketMatching(),
      search({ top: true }),
      lintGutter(),
      hiddenTypes,
      notes,
      decorations,
      minimap,
      EditorView.lineWrapping,
      blLanguage,
      syntaxHighlighting(brandHighlight),
      syntaxHighlighting(classHighlighter),
      brandTheme,
      indent,
      saveKeymap,
      undoKeymap,
      shortcutKeymap,
      keymap.of([...defaultKeymap, ...historyKeymap, ...searchKeymap, ...lintKeymap, indentWithTab]),
      listener,
    ],
  });

  const view = new EditorView({ state, parent });
  if (options.hideTypes) view.dispatch({ effects: setHideTypesEffect.of(true) });
  if (options.showNotes) view.dispatch({ effects: setShowNotesEffect.of(true) });

  // The document is replaced by `text` when it differs; a pending onChange
  // of the replaced document is dropped, and the replacement calls none.
  // Where the text differs, or `otherFile` is true, another file's document
  // or a text the host gives replaces the current one: the undo history is
  // removed before the replacement and given again empty after it, with
  // the gestures' marks, so that the replacement and the earlier
  // document's edits stand in no history (R-D45). A file's properties may
  // reach the editor in two steps, an earlier text under the new revision
  // first, and a replacement kept in the history would then undo every
  // edit since that earlier text at once (unit L, Task 17; defect 6 of the
  // UX simulation).
  function replaceDocument(text, otherFile = false) {
    if (changeTimer !== null) {
      clearTimeout(changeTimer);
      changeTimer = null;
    }
    const next = text ?? "";
    const differs = view.state.doc.toString() !== next;
    const fresh = otherFile || differs;
    if (fresh) view.dispatch({ effects: undoHistory.reconfigure([]) });
    if (differs) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: next },
        annotations: externalChange.of(true),
      });
    }
    if (fresh) {
      view.dispatch({ effects: undoHistory.reconfigure(history()) });
      marks = { done: [], undone: [] };
    }
  }

  return {
    setDocument(nextPath, nextRevision, text) {
      const otherFile = (nextPath ?? null) !== path;
      path = nextPath ?? null;
      revision = nextRevision ?? 0;
      replaceDocument(text, otherFile);
    },
    setDoc(text) {
      replaceDocument(text);
    },
    getDoc() {
      return view.state.doc.toString();
    },
    replaceSpans(edits, expected, options) {
      return applySpans(view, edits, expected, options ?? {});
    },
    setShortcuts(table) {
      shortcuts = table ?? {};
    },
    setDiagnostics(diagnostics) {
      const doc = view.state.doc;
      const list = (diagnostics ?? []).map((d) => {
        const from = offsetOf(doc, d.line, d.column);
        const to =
          d.end_line == null || d.end_column == null
            ? from
            : Math.max(from, offsetOf(doc, d.end_line, d.end_column));
        const diagnostic = { from, to, severity: d.severity ?? "error", message: d.message ?? "" };
        // the rule, which the lint tooltip prints after the message as the
        // diagnostic's source (Model Interface 0.9 §3)
        if (d.rule) diagnostic.source = d.rule;
        // A refusal's action: one button, which applies its edits while the
        // document is its `expected` text (spec 0.4 §3.3, J-D19).
        if (d.action) {
          const { name, edits, expected } = d.action;
          diagnostic.actions = [{ name, apply: (target) => applySpans(target, edits, expected) }];
        }
        return diagnostic;
      });
      view.dispatch(lintSetDiagnostics(view.state, list));
    },
    setHideTypes(on) {
      view.dispatch({ effects: setHideTypesEffect.of(Boolean(on)) });
    },
    setShowNotes(on) {
      view.dispatch({ effects: setShowNotesEffect.of(Boolean(on)) });
    },
    // The cursor at (line, column), counted from one, the column in code
    // points; where endLine is given, the text from there to (endLine,
    // endColumn) selected, to the end of endLine where endColumn is null
    // (unit J's decision J-D40; amendment 02 ruling 9). The editor takes the
    // focus unless `focus` is false.
    gotoLine(line, column, endLine, endColumn, focus = true) {
      const doc = view.state.doc;
      const pos = offsetOf(doc, line, column);
      let head = pos;
      if (endLine) {
        head =
          endColumn == null
            ? doc.line(Math.min(Math.max(1, endLine), doc.lines)).to
            : offsetOf(doc, endLine, endColumn);
      }
      view.dispatch({
        selection: { anchor: pos, head },
        effects: EditorView.scrollIntoView(pos, { y: "center" }),
      });
      if (focus) view.focus();
    },
    focus() {
      view.focus();
    },
    // The four functions of a preview (spec 0.4 §5.8). Within them, as in
    // every function of this object, `view` is the EditorView; a method's
    // name binds nothing in its body.
    previewLine(line) {
      const doc = view.state.doc;
      if (!(line >= 1 && line <= doc.lines)) {
        view.dispatch({ effects: setPreviewedLine.of(null) });
        return;
      }
      const from = doc.line(line).from;
      view.dispatch({
        effects: [setPreviewedLine.of(from), EditorView.scrollIntoView(from, { y: "center" })],
      });
    },
    findText(text) {
      if (!text) return [];
      // `text` as a pattern of its own characters, matched with the case
      // ignored over code points, so that a match's offset is an offset of
      // the line's text
      const pattern = new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "iu");
      const doc = view.state.doc;
      const found = [];
      for (let number = 1; number <= doc.lines && found.length < 50; number++) {
        const line = doc.line(number);
        const at = line.text.search(pattern);
        if (at >= 0) found.push({ line: number, column: columnOf(line, line.from + at), text: line.text });
      }
      return found;
    },
    view() {
      const { anchor, head } = view.state.selection.main;
      const { scrollTop: top, scrollLeft: left } = view.scrollDOM;
      return { top, left, anchor, head, ...cursorOf(view.state) };
    },
    setView(record) {
      const length = view.state.doc.length;
      const within = (offset) => Math.min(Math.max(0, offset ?? 0), length);
      const anchor = within(record.anchor);
      const head = within(record.head);
      const main = view.state.selection.main;
      view.scrollDOM.scrollTop = record.top ?? 0;
      view.scrollDOM.scrollLeft = record.left ?? 0;
      // The snapshot of the position just set replaces a scroll a preview
      // asked for and the editor has not yet made.
      const spec = { effects: [setPreviewedLine.of(null), view.scrollSnapshot()] };
      if (main.anchor !== anchor || main.head !== head) spec.selection = { anchor, head };
      view.dispatch(spec);
    },
    destroy() {
      if (changeTimer !== null) clearTimeout(changeTimer);
      if (cursorTimer !== null) clearTimeout(cursorTimer);
      view.destroy();
    },
  };
}

export const version = versions;
