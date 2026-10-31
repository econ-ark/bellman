// The text minimap (model interface specification 0.4, §5.4; unit R,
// brief rule 5; review 4; R-D35): a strip at the editor's right edge that
// holds one mark per line of the document, in the lines' order. theme.js
// draws the strip, its marks and their colors; this module holds no color.
//
// A mark is the element `bl-minimap-mark`, with its line's number, counted
// from one, as `data-line` and the line's kind as `data-kind`: `stage`, the
// line of the stage name (stageName of bl_language.js); `header`, a line
// whose first character that is no white space opens a group that
// GROUP_HEAD of hidden_types.js matches, so that a statement's annotation
// does not make its line a header; `line`, any other line. A mark is
// PX_PER_CHARACTER wide per character of its line, up to WIDEST. The strip
// reads the lines of the editor's document and its syntax tree, and parses
// nothing of its own.
//
// The marks are made again, at most once per frame, when the document
// changes or a change of the syntax tree moves the stage name's line; a
// move of the cursor leaves them as they are. Where the marks are higher
// than the strip, the strip shows the part of them at the fraction of the
// editor's own scroll position.
//
// A press of the pointer on a mark, or between two marks on the nearer one,
// puts the cursor at the start of that line and scrolls the line to the
// middle of the editor. The strip changes no character of the document. It
// is hidden from assistive technology and takes no place in the order of
// Tab (R-D35); the keyboard reaches a line through the editor.
import { syntaxTree } from "@codemirror/language";
import { EditorView, ViewPlugin } from "@codemirror/view";

import { stageName } from "./bl_language.js";
import { GROUP_HEAD } from "./hidden_types.js";

// The width of a mark per character of its line, in pixels (§5.4).
const PX_PER_CHARACTER = 0.6;
// The greatest width of a mark, in pixels (§5.4): the strip's 60 px less
// its 4 px inside its left edge and 12 px inside its right, so that the
// longest marks end on the column's right text edge, under `Save`, a line
// of more than 73 characters drawn at this width (design pass 13 §4; D17;
// the fix wave Q3b, item 18).
const WIDEST = 44;

// The number of characters of `text`, counted in code points, as the
// package counts a line's columns.
function characters(text) {
  let count = 0;
  for (let i = 0; i < text.length; i += text.codePointAt(i) > 0xffff ? 2 : 1) count++;
  return count;
}

// The number, counted from one, of the stage name's line of the editor
// state `state`; null where it has none.
function stageLine(state) {
  const name = stageName(state);
  return name === null ? null : name.line;
}

// The kind of the line `text` numbered `number`, where `stage` is the
// number of the stage name's line or null.
function kindOf(text, number, stage) {
  if (number === stage) return "stage";
  return GROUP_HEAD.test(text.trimStart()) ? "header" : "line";
}

// The width of the mark of the line `text`, as a CSS length.
function widthOf(text) {
  const pixels = Math.min(characters(text) * PX_PER_CHARACTER, WIDEST);
  return `${Number(pixels.toFixed(1))}px`;
}

class Minimap {
  constructor(view) {
    this.view = view;
    // The number of the stage name's line the marks were made with.
    this.stage = stageLine(view.state);
    // Whether the marks are to be made again at the next measure.
    this.stale = true;
    this.dom = document.createElement("div");
    this.dom.className = "bl-minimap";
    this.dom.setAttribute("aria-hidden", "true");
    this.dom.addEventListener("mousedown", (event) => this.press(event));
    view.dom.appendChild(this.dom);
    // One request of the editor's measure cycle, which runs at most once per
    // frame however often it is asked for.
    this.request = {
      read: (view) => this.read(view),
      write: (measured) => this.write(measured),
    };
    view.requestMeasure(this.request);
  }

  update(update) {
    const parsed = syntaxTree(update.startState) !== syntaxTree(update.state);
    const stage = update.docChanged || parsed ? stageLine(update.state) : this.stage;
    if (update.docChanged || stage !== this.stage) {
      this.stage = stage;
      this.stale = true;
    }
    if (this.stale || update.geometryChanged || update.viewportChanged) {
      this.view.requestMeasure(this.request);
    }
  }

  // The top of the editor's scroller below the editor's own top and its
  // height, in pixels, and the fraction of its scrollable height that is
  // scrolled.
  read(view) {
    const scroller = view.scrollDOM;
    const box = scroller.getBoundingClientRect();
    const range = scroller.scrollHeight - scroller.clientHeight;
    return {
      top: box.top - view.dom.getBoundingClientRect().top,
      height: box.height,
      fraction: range > 0 ? scroller.scrollTop / range : 0,
    };
  }

  // The marks made again where they are stale, and the strip set at the
  // scroller's top and height and scrolled to the scroller's fraction.
  write({ top, height, fraction }) {
    if (this.stale) {
      this.draw();
      this.stale = false;
    }
    this.dom.style.top = `${top}px`;
    this.dom.style.height = `${height}px`;
    this.dom.scrollTop = Math.round(fraction * (this.dom.scrollHeight - this.dom.clientHeight));
  }

  // One mark per line of the document: the existing marks are kept and
  // changed only where their kind or their width differs, a mark is added
  // for each new line and removed for each line gone.
  draw() {
    const marks = this.dom.children;
    let number = 0;
    for (const text of this.view.state.doc.iterLines()) {
      number++;
      let mark = marks[number - 1];
      if (!mark) {
        mark = document.createElement("div");
        mark.className = "bl-minimap-mark";
        mark.dataset.line = String(number);
        this.dom.appendChild(mark);
      }
      const kind = kindOf(text, number, this.stage);
      const width = widthOf(text);
      if (mark.dataset.kind !== kind) mark.dataset.kind = kind;
      if (mark.style.width !== width) mark.style.width = width;
    }
    while (marks.length > number) this.dom.lastChild.remove();
  }

  // A press of the pointer's main button on the strip: the cursor at the
  // start of the line of the nearest mark, the line scrolled into the
  // editor and the focus in the editor.
  press(event) {
    if (event.button !== 0) return;
    event.preventDefault();
    const number = this.lineAt(event.clientY);
    if (number === null) return;
    const line = this.view.state.doc.line(number);
    this.view.dispatch({
      selection: { anchor: line.from },
      effects: EditorView.scrollIntoView(line.from, { y: "center" }),
      userEvent: "select.pointer",
    });
    this.view.focus();
  }

  // The line of the mark whose middle is nearest to the height `y` of the
  // viewport, the later of two at the same distance, within the document;
  // null where the strip holds no mark.
  lineAt(y) {
    const marks = this.dom.children;
    if (marks.length === 0) return null;
    const middle = (index) => {
      const box = marks[index].getBoundingClientRect();
      return (box.top + box.bottom) / 2;
    };
    let low = 0;
    let high = marks.length - 1;
    while (low < high) {
      const index = (low + high) >> 1;
      if (middle(index) < y) low = index + 1;
      else high = index;
    }
    if (low > 0 && y - middle(low - 1) < middle(low) - y) low--;
    return Math.min(Number(marks[low].dataset.line), this.view.state.doc.lines);
  }

  destroy() {
    this.dom.remove();
  }
}

// The extension that draws the text minimap.
export const minimap = ViewPlugin.fromClass(Minimap, {
  eventObservers: {
    // A scroll of the editor moves the strip's marks with it.
    scroll() {
      this.view.requestMeasure(this.request);
    },
  },
});
