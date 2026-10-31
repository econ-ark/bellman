<template>
  <span hidden></span>
</template>

<script>
// The behavior of the window as a whole, in a Vue 3 component of Solara's
// component_vue, rendered once inside .bl-window by `Page`: the columns'
// widths, the folds of the regions and the handles on the regions' edges
// (spec 0.4 §5.1; AMD-MI-002 §6 rule 2; AAS, L-D12), the keys of the tab's
// history (§3 rule 4), the key of Goto Anything and the key Escape of a
// wide panel, each read on the browser's window, and the high-contrast
// setting (spec 0.4 §5.8).
//
// The columns (spec 0.4 §5.1; R-D30, R-D31): one function, `columns`, gives
// each column its width at every size of the window, and writes the widths
// to .bl-window as custom properties, which brand.css reads. A column
// stands for each region of `columns` that is a child of .bl-window, but
// Matsya's while it is folded, which takes no width and has no column gap
// before it (unit K's decision K-D19). The
// base widths are the frame's for the folder's state, frame 7b with the
// folder open and frame 7a with it folded, each replaced by the reader's
// dragged width where one is kept; a folder the reader folds is its rail.
// The available width is the window's, the width of the document's root,
// less the side paddings and the column gaps of .bl-window. Above the base
// widths' sum, the text and the graph share the rest in the proportion of
// their frame widths, in whole pixels. Below it, Matsya gives up width to its least width,
// then the graph to its own; then the function folds the folder to its
// rail, the text taking what is left over; then the text narrows to its
// least width; below that the window scrolls sideways. A fold the function
// makes is not kept. A click on the folder's button opens a folder the
// function folded, until the window's size next changes, the text giving
// up the width to its least width.
//
// The trellis view (unit K's decisions K-D6 and K-D19): while the trellis
// view is drawn, an open Matsya is folded, and the graph takes the width of
// Matsya's column and of the column gap before it, the text and the folder
// keeping the widths the function gives them with Matsya open. Python
// sends the message of the graph bar's tab `Trellis`, .bl-trellis-button,
// whose aria-pressed it sets with the view, before the view's other
// messages, the trellis graph's among them, and the message of the
// property `trellis_view` after them, since `Window` follows the regions in
// `Page`. The trellis view is taken to be drawn from the earlier of the
// two, the tab pressed or the property, so that Matsya folds before the
// trellis view is drawn and does not stand open beside it until the
// property arrives; it is taken to be left when both say so, the property
// arriving once the other view is drawn, so that Matsya does not open, and
// narrow the trellis graph, just before that graph is replaced. Each
// change of the tab's attribute and of the property is read. The fold is
// not kept. A click on a button of Matsya opens it until the view drawn
// next changes.
//
// The handles: a handle is an element .bl-handle whose data-handle names
// its region; `app.py` renders it, `matsya_window.Composer` the handle
// `composer` on the top edge of Matsya's composer, and brand.css draws it.
// A drag on the handle of a column sizes the column and stops where the
// column, the text or the graph reaches its least width (R-D14), or where
// Matsya and the graph reach theirs; a drag on the handle of a region in a
// column sizes its height, which keeps the least height, or the least its
// entry names, and stops where the region that gives up the space reaches
// the least height. A double click on a handle removes its region's size,
// and the region returns to the size the frame or brand.css gives it; the
// composer's field returns to the height of its text (amendment 07 of spec
// 0.4, §2 item 5).
//
// The folds (spec 0.4 §5.1; brief rule 3; R-D3; AAS, L-D12; design pass 10
// §3): a click on an element .bl-fold, whose data-fold names a region of
// `folded`, the folder, the Inspector, the panel under the editor on the
// recipe or on a stage's types (N-D4), Details or Matsya, and a change of
// the property `fold_request` fold an open region and open a folded one; a
// .bl-fold that carries aria-disabled, the Inspector's toggle while the
// open file gives the panel nothing to show, folds nothing. Each region
// has its toggle at the right of the main bar; the two panels have their
// head's `×` too, and Matsya the button at the right end of its head. The
// state is written to .bl-window as data-folded-<region>, which brand.css
// reads, and to each fold button as aria-expanded. The panel under the
// editor appears for the open file only while `lower_panel` names it, so
// that the Inspector's toggle is drawn and announced open only then.
//
// The record: the dragged sizes and the reader's folds are kept in the
// browser's localStorage under the folder's path (R-D16), so that the
// folder opened again, and a page that opens another file of it, finds its
// regions as they were left (L-D12: the fold remembered per panel);
// nothing of the graph is kept.
//
// The keys of the tab's history (AMD-MI-002 §3 rule 4, A2-D4): Alt+← asks
// Python for a step back and Alt+→ for a step forward, the browser's own
// reading of the keys prevented. They are read in the capture phase,
// before CodeMirror's handlers, and only where the key event arose outside
// a text field: in an input, a textarea, a select or an element inside a
// contenteditable element, which holds CodeMirror's text, the keys keep
// the field's word movement on macOS, as a macOS text field gives them.
// On every other platform, Windows and Linux among them, where the browser
// reads Alt+← in a text field as a step back in its own history, which
// would leave the page, the keys do nothing in a text field: the browser's
// reading is prevented, and CodeMirror, which reads no event already
// prevented, moves nothing.
//
// The key of Goto Anything (spec 0.4 §5.8; unit R, brief rule 9): P with
// the primary modifier, Command on macOS and Ctrl on every other platform,
// read in the capture phase wherever the focus stands, asks Python to open
// the palette, the browser's printing prevented.
//
// The key Escape of a wide panel (AAS, L-D11): while the property
// `wide_panel` holds, a region's wide panel standing over the window, or
// while a panel is drawn wide, `.bl-wide`, Escape, read in the capture
// phase wherever the focus stands, asks Python to close it. The panel's
// class can arrive in an earlier message from Python than the property,
// some tens of milliseconds before it, and Escape acts on the panel drawn.
// Vuetify's dialog, which draws the panel, does not read Escape on this
// page, where no overlay of Vuetify takes the key.
//
// The key Escape in Matsya's composer (amendment 07 of spec 0.4, §2 item
// 7), read in the capture phase: Escape whose path passes through the
// composer's field, .bl-matsya-field, moves the focus to the conversation,
// .bl-matsya-exchanges, and the field keeps its text. During an input
// method's composition the key is the input method's and moves nothing.
//
// The keys of a form open over the window (AAS, L-D15; design pass 4
// §2a), read in the capture phase wherever the focus stands: Escape
// presses the form's `cancel`, unless a select of the form holds its menu
// open, a Vuetify select by aria-expanded and a select of VSCode Elements
// by its attribute `open` (unit M, Task 6), which takes the key; the
// primary modifier with Enter presses the form's primary button while it
// acts; ArrowDown and ArrowUp move the
// focus among the rows of the list or the choice that holds it,
// `.bl-list-item`; and Enter or Space on a row that is no button presses
// it.
//
// The Recipe tab's open row (design pass 11 §2), read in the capture
// phase wherever the focus stands: Escape whose path passes through the
// open row closes it and returns the focus to the row, unless a select of
// the row holds its list open, which takes the key; and a click outside
// the tab's table closes it, the focus staying where the click put it. A
// click on another row opens that row, which Python reads. Escape is read
// here, not on the row, since VSCode Elements' select stops Escape at its
// own element.
//
// The high-contrast setting (spec 0.4 §5.8; R-D10, R-D24): kept for the
// browser in localStorage under one key, `bellman-workbench contrast`,
// which holds `high` while the setting is on and is removed while it is
// off; written to .bl-window as data-contrast="high" at the page's load and
// at each change, brand.css then drawing the line numbers in opaque ice-3.
// Where the storage is refused, the setting holds for the page's life.
//
// Properties, each set from Python:
//   folder            the path of the tab's model folder, under which the
//                     record is kept; a change applies the record kept for
//                     the new folder
//   fold_request      {region, n}: the fold of `region`, a region of
//                     `folded`, asked by a command; `n` makes each request
//                     new
//   contrast_request  a count, which Python raises to turn the
//                     high-contrast setting on where it is off and off
//                     where it is on
//   trellis_view      whether the view shows a trellis, during which
//                     Matsya is folded (K-D6); the trellis view is taken to
//                     be drawn while it or the tab `Trellis` says so
//   wide_panel        whether a region's wide panel stands over the window
//                     (L-D11, L-D12)
//   lower_panel       the fold of the panel under the editor while it
//                     shows the open file, `inspector`, or null where it
//                     does not appear (design pass 10 §3)
// Events, each a call of a Python function:
//   back()           on Alt+← outside a text field
//   forward()        on Alt+→ outside a text field
//   goto()           on P with the primary modifier
//   escape()         on Escape while wide_panel holds or a panel is drawn
//                    wide
//   region_folded(region)  on the fold of `region`, a region of `folded`,
//                    so that a panel folded while it stands in its wide
//                    panel leaves no ground over the window (unit L's
//                    final judgment, §6 item 11)
//   close_recipe_row()  on Escape in the Recipe tab's open row or a click
//                    outside the tab's table (design pass 11 §2)
module.exports = {
  // The key in the browser's storage of the high-contrast setting (R-D24).
  contrastKey: "bellman-workbench contrast",
  // The least widths in pixels (spec 0.4 §5.1; R-D14), read as
  // this.$options.leasts: the open folder's, the graph's, Matsya's and the
  // text's.
  leasts: { folder: 170, view: 300, matsya: 300, text: 300 },
  // The least height in rem of a region in a column (AMD-MI-002 §6 rule 2),
  // written to .bl-window as --bl-least-height, which brand.css reads.
  leastHeight: 5,
  // The width in pixels of a folded folder's rail (spec 0.4 §5.1).
  rail: 48,
  // The regions the reader folds and opens, read as this.$options.folded,
  // each by its data-fold: the folder, the two panels and Matsya (spec 0.4
  // §5.1; AAS, L-D12; design pass 10 §3).
  folded: ["folder", "inspector", "details", "matsya"],
  // The columns' widths in pixels in frame 7b, the folder open, and in
  // frame 7a, the folder folded (spec 0.4 §5.1), by column.
  frames: {
    open: { folder: 170, file: 568, view: 314, matsya: 320 },
    folded: { folder: 48, file: 640, view: 336, matsya: 348 },
  },
  // The columns in their order on the grid, read as this.$options.columns:
  // the region that is the column where it is a child of .bl-window; the
  // custom property of .bl-window that holds its width; the name of its
  // least width in `leasts`. A column's name is its name in `frames`, and
  // the name of the handle that sizes its width, where one does.
  columns: [
    { name: "folder", region: ".bl-folder", property: "--bl-folder-width", least: "folder" },
    { name: "file", region: ".bl-file", property: "--bl-file-width", least: "text" },
    { name: "view", region: ".bl-view", property: "--bl-view-width", least: "view" },
    { name: "matsya", region: ".bl-matsya", property: "--bl-matsya-width", least: "matsya" },
  ],
  // The six handles, by their data-handle, read as this.$options.handles:
  // the region each one sizes; the axis of the size; the sign of the
  // pointer's motion that enlarges the region, -1 for a handle on a top
  // edge, which enlarges its region upward, or on a left edge, which
  // enlarges its region leftward. A handle on the x axis sizes the column
  // of its name, whose custom property `columns` names. A handle on the y
  // axis names the custom property of .bl-window that holds the height, and
  // the regions that give up the space. The sixth, `composer`, on the y
  // axis, sizes the field of Matsya's composer, the conversation giving
  // the space, and names its own least height in pixels, `least`, the field
  // at one line, which a drag reads in place of the least height of a
  // region (amendment 07 of spec 0.4, §2 item 5).
  handles: {
    folder: { region: ".bl-folder", axis: "x", sign: 1 },
    file: { region: ".bl-file", axis: "x", sign: 1 },
    matsya: { region: ".bl-matsya", axis: "x", sign: -1 },
    classification: {
      region: ".bl-classification",
      property: "--bl-classification-height",
      axis: "y",
      sign: -1,
      giving: [".bl-editor-frame"],
    },
    panel: {
      region: ".bl-panel",
      property: "--bl-panel-height",
      axis: "y",
      sign: -1,
      giving: [".bl-view-host"],
    },
    composer: {
      region: ".bl-matsya-field",
      property: "--bl-matsya-field-height",
      axis: "y",
      sign: -1,
      giving: [".bl-matsya-exchanges"],
      least: 26,
    },
  },
  mounted() {
    // the dragged sizes in pixels, by handle; the reader's folds, by
    // region; whether the width function folded the folder at its last
    // run; whether the reader opened the folder since the window's size
    // last changed; whether the reader opened Matsya since the view drawn
    // last changed; whether the view drawn at that change was the trellis
    // view; the width in pixels of Matsya's column, which the graph holds
    // with the column gap before it while the trellis view folds Matsya
    // (K-D6, K-D19); the drag under way
    this.sizes = {};
    this.folds = this.noFolds();
    this.forced = false;
    this.opened = false;
    this.matsyaOpened = false;
    this.trellisDrawn = this.trellisShown();
    this.lent = 0;
    this.drag = null;
    // the high-contrast setting where the browser's storage refuses it
    this.contrast = false;
    // the listeners of the window, each [event type, function], added in
    // the capture phase of the browser's window, so that no element of the
    // page stops an event before they read it
    this.listeners = [
      ["pointerdown", (event) => this.startDrag(event)],
      ["pointermove", (event) => this.moveDrag(event)],
      ["pointerup", (event) => this.endDrag(event)],
      ["pointercancel", (event) => this.endDrag(event)],
      ["dblclick", (event) => this.restore(event)],
      ["click", (event) => this.pressFold(event)],
      ["resize", () => this.resized()],
      ["keydown", (event) => this.step(event)],
      ["keydown", (event) => this.palette(event)],
      ["keydown", (event) => this.closeProblems(event)],
      ["pointerdown", (event) => this.outsideProblems(event)],
      ["keydown", (event) => this.closeRecipeRow(event)],
      ["click", (event) => this.outsideRecipeRow(event)],
      ["keydown", (event) => this.closePanel(event)],
      ["keydown", (event) => this.leaveComposer(event)],
      ["keydown", (event) => this.formKeys(event)],
    ];
    for (const [type, listener] of this.listeners) window.addEventListener(type, listener, true);
    // the changes of aria-pressed in the window, that of the tab `Trellis`
    // among them, each read as a possible change of the view drawn (K-D6)
    this.viewObserver = new MutationObserver(() => this.viewDrawn());
    const frame = this.frame();
    if (frame) {
      this.viewObserver.observe(frame, {
        subtree: true,
        attributes: true,
        attributeFilter: ["aria-pressed"],
      });
    }
    this.applyLayout();
    this.applyContrast();
  },
  unmounted() {
    for (const [type, listener] of this.listeners) window.removeEventListener(type, listener, true);
    this.viewObserver.disconnect();
    this.drag = null;
  },
  watch: {
    folder() {
      this.applyLayout();
    },
    fold_request(request) {
      if (request && request.region) this.fold(request.region);
    },
    contrast_request(value) {
      if (value) this.toggleContrast();
    },
    // The property read as a change of the view drawn (K-D6).
    trellis_view() {
      this.viewDrawn();
    },
    // A change of the panel under the editor's content marks the
    // Inspector's toggle again (design pass 10 §3).
    lower_panel() {
      this.columns();
    },
  },
  methods: {
    // Each region of `folded` open.
    noFolds() {
      return Object.fromEntries(this.$options.folded.map((region) => [region, false]));
    },
    // The element .bl-window that holds this component.
    frame() {
      return this.$el && this.$el.closest ? this.$el.closest(".bl-window") : null;
    },
    // The key of the folder's record in the browser's storage (R-D16).
    storageKey() {
      return `bellman-workbench layout ${this.folder}`;
    },
    // The record kept for the folder: the dragged sizes, each a positive
    // number of pixels under the name of a handle, a column's width no less
    // than its least width, and the reader's folds; no size and no fold
    // where the storage is refused or holds no record.
    keptLayout() {
      let record = null;
      try {
        record = JSON.parse(window.localStorage.getItem(this.storageKey()));
      } catch (error) {
        record = null;
      }
      const sizes = {};
      const folds = this.noFolds();
      if (record === null || typeof record !== "object") return { sizes, folds };
      for (const name of Object.keys(this.$options.handles)) {
        const size = record.sizes ? record.sizes[name] : undefined;
        // a column's width below its least width, which no drag writes, such
        // as an earlier build's height of Matsya's window, is not read
        const column = this.$options.columns.find((entry) => entry.name === name);
        const least = column ? this.$options.leasts[column.least] : 0;
        if (typeof size === "number" && Number.isFinite(size) && size > 0 && size >= least) {
          sizes[name] = size;
        }
      }
      for (const region of Object.keys(folds)) {
        folds[region] = Boolean(record.folds) && record.folds[region] === true;
      }
      return { sizes, folds };
    },
    // The record of the folder applied: the least height and the heights
    // kept set on .bl-window, and the columns' widths given.
    applyLayout() {
      const kept = this.keptLayout();
      this.sizes = kept.sizes;
      this.folds = kept.folds;
      this.opened = false;
      this.matsyaOpened = false;
      const frame = this.frame();
      if (!frame) return;
      frame.style.setProperty("--bl-least-height", `${this.$options.leastHeight}rem`);
      for (const [name, handle] of Object.entries(this.$options.handles)) {
        if (handle.axis !== "y") continue;
        if (name in this.sizes) frame.style.setProperty(handle.property, `${this.sizes[name]}px`);
        else frame.style.removeProperty(handle.property);
      }
      this.columns();
    },
    // The record written to the browser's storage under the folder's path,
    // {sizes, folds}, and removed when it holds no size and no fold. Where
    // the storage is refused, the regions keep their sizes and folds for
    // the page's life alone.
    keepLayout() {
      try {
        if (Object.keys(this.sizes).length || Object.values(this.folds).some(Boolean)) {
          const record = { sizes: this.sizes, folds: this.folds };
          window.localStorage.setItem(this.storageKey(), JSON.stringify(record));
        } else {
          window.localStorage.removeItem(this.storageKey());
        }
      } catch (error) {
        // the storage refused the record; nothing more is written
      }
    },
    // Whether the trellis view is taken to be drawn: the graph bar's tab
    // `Trellis` pressed, whose message comes before the view's, or the
    // property `trellis_view`, whose message comes after it (K-D6).
    trellisShown() {
      const frame = this.frame();
      const tab = frame ? frame.querySelector(".bl-trellis-button") : null;
      return (tab !== null && tab.getAttribute("aria-pressed") === "true") || Boolean(this.trellis_view);
    },
    // A change of the view drawn ends the reader's opening of Matsya and
    // gives the columns their widths (K-D6); the tab's change and the
    // property's later arrival are one change.
    viewDrawn() {
      const shown = this.trellisShown();
      if (shown === this.trellisDrawn) return;
      this.trellisDrawn = shown;
      this.matsyaOpened = false;
      this.columns();
    },
    // The frame's widths for the folder's state, as the reader left it.
    frameWidths() {
      return this.$options.frames[this.folds.folder ? "folded" : "open"];
    },
    // Whether the column `name` holds a width dragged on its handle.
    dragged(name) {
      const handle = this.$options.handles[name];
      return handle !== undefined && handle.axis === "x" && name in this.sizes;
    },
    // The columns that stand: those whose region is a child of `frame`.
    present(frame) {
      return this.$options.columns.filter((column) =>
        frame.querySelector(`:scope > ${column.region}`)
      );
    },
    // The width function (spec 0.4 §5.1; R-D30, R-D31): each column's
    // width, written to .bl-window as its custom property; the folds, the
    // reader's, the function's and the trellis view's, written as
    // data-folded-<region> on .bl-window for every region of `folded` and
    // as aria-expanded on each fold button. A folded Matsya has no column
    // and no custom property (K-D19).
    // The fold of the folder that the function makes is held in `forced`,
    // the width of the Matsya the trellis view folds in `lent`; neither is
    // kept.
    columns() {
      const frame = this.frame();
      if (!frame) return;
      const { leasts, rail } = this.$options;
      // the columns that take width, of which a Matsya the reader folded is
      // none (K-D19)
      const present = this.present(frame).filter(
        (column) => column.name !== "matsya" || !this.folds.matsya
      );
      const style = getComputedStyle(frame);
      const sides = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
      const gap = parseFloat(style.columnGap);
      const gaps = gap * Math.max(0, present.length - 1);
      // the window's width, read from the document's root, since a
      // .bl-window wider than the window keeps the width of its columns
      const available = document.documentElement.clientWidth - sides - gaps;
      const frameWidths = this.frameWidths();
      const width = {};
      for (const { name } of present) {
        if (this.folds[name]) width[name] = rail;
        else width[name] = this.dragged(name) ? this.sizes[name] : frameWidths[name];
      }
      let rest = available - Object.values(width).reduce((sum, value) => sum + value, 0);
      let forced = false;
      if (rest >= 0) {
        // the text and the graph that hold no dragged width share the rest
        // in the proportion of their frame widths, in whole pixels, the last
        // taking what the rounding leaves, so that the columns' edges stand
        // on whole pixels (unit N, Task 1)
        const sharing = ["file", "view"].filter((name) => name in width && !this.dragged(name));
        const weight = sharing.reduce((sum, name) => sum + frameWidths[name], 0);
        let given = 0;
        sharing.forEach((name, index) => {
          if (weight <= 0) return;
          const share = index === sharing.length - 1
            ? rest - given
            : Math.round((rest * frameWidths[name]) / weight);
          width[name] += share;
          given += share;
        });
      } else {
        // Matsya, then the graph, give up width to their least widths
        for (const name of ["matsya", "view"]) {
          if (!(name in width)) continue;
          const given = Math.min(-rest, Math.max(0, width[name] - leasts[name]));
          width[name] -= given;
          rest += given;
        }
        // then the folder folds to its rail, unless the reader opened it
        // since the window's size last changed; half a pixel is no deficit
        if (rest < -0.5 && "folder" in width && !this.folds.folder && !this.opened) {
          forced = true;
          rest += width.folder - rail;
          width.folder = rail;
        }
        // the text takes what is left over, and gives up no more than
        // what keeps its least width
        if ("file" in width) width.file = Math.max(leasts.text, width.file + rest);
      }
      // while the trellis view is drawn, an open Matsya that the reader has
      // not opened in it is folded, and the graph takes the width of its
      // column and of the column gap before it (K-D6, K-D19)
      let lent = 0;
      if (this.trellisShown() && "matsya" in width && "view" in width && !this.matsyaOpened) {
        lent = width.matsya;
        width.view += lent + gap;
        delete width.matsya;
      }
      for (const column of this.$options.columns) {
        if (column.name in width) frame.style.setProperty(column.property, `${width[column.name]}px`);
        else frame.style.removeProperty(column.property);
      }
      this.forced = forced;
      this.lent = lent;
      const folded = { ...this.folds };
      folded.folder = this.folds.folder || forced;
      folded.matsya = this.folds.matsya || lent > 0;
      for (const [region, state] of Object.entries(folded)) {
        frame.toggleAttribute(`data-folded-${region}`, state);
      }
      // the Inspector is shown open only while it shows the open file
      const away = (region) => region === "inspector" && !this.lower_panel;
      for (const button of frame.querySelectorAll(".bl-fold[data-fold]")) {
        const region = button.dataset.fold;
        if (region in folded) {
          button.setAttribute("aria-expanded", String(!folded[region] && !away(region)));
        }
      }
    },
    // A change of the window's size ends the reader's opening of a folder
    // the function folded (R-D31) and gives the columns their widths.
    resized() {
      this.opened = false;
      this.columns();
    },
    // The reader's fold of `region`, a region of `folded`: a region shown
    // folded opens, and an open one folds; the record keeps the fold. A
    // folder opened stays open until the window's size next changes,
    // though the width function would fold it (R-D31); Matsya opened stays
    // open until the view drawn next changes, though the trellis view would
    // fold it (K-D6).
    fold(region) {
      if (!(region in this.folds)) return;
      const shownFolded =
        this.folds[region] ||
        (region === "folder" && this.forced) ||
        (region === "matsya" && this.lent > 0);
      this.folds[region] = !shownFolded;
      if (region === "folder") this.opened = shownFolded;
      else if (region === "matsya") this.matsyaOpened = shownFolded;
      this.keepLayout();
      this.columns();
      if (!shownFolded) this.region_folded(region);
    },
    // A click on a fold button of the window, .bl-fold, folds or opens the
    // region its data-fold names; a disabled one, aria-disabled, does
    // nothing (design pass 10 §3).
    pressFold(event) {
      const button = event.target instanceof Element ? event.target.closest(".bl-fold") : null;
      const frame = this.frame();
      if (!button || !frame || !frame.contains(button)) return;
      if (button.getAttribute("aria-disabled") === "true") return;
      this.fold(button.dataset.fold);
    },
    // The size of `element` along `axis`, in pixels.
    extent(element, axis) {
      const box = element.getBoundingClientRect();
      return axis === "x" ? box.width : box.height;
    },
    // The pointer's coordinate on `axis`, in pixels.
    coordinate(event, axis) {
      return axis === "x" ? event.clientX : event.clientY;
    },
    // The width, in pixels, that the column `name` can take under a drag
    // (R-D14): what the graph and Matsya hold above their least widths, a
    // folded Matsya giving none, and what the text, where it is not the
    // column dragged, holds above the width it keeps, its dragged width or
    // the frame's, since the width function folds the folder before the
    // text narrows. The folder gives up no width to a drag. Under a drag of
    // Matsya, which gives up width first, the graph gives only what it
    // holds above the frame's width, since the width function would take
    // any more back from Matsya. The width the graph holds of Matsya's
    // column and of the column gap before it while the trellis view folds
    // Matsya counts as Matsya's, so that a drag takes what it takes with
    // Matsya open (K-D6, K-D19).
    widthRoom(name, frame) {
      const { leasts } = this.$options;
      const gap = parseFloat(getComputedStyle(frame).columnGap);
      let room = 0;
      for (const column of this.present(frame)) {
        if (column.name === name || column.name === "folder") continue;
        // a Matsya the reader folded takes no width and gives none (K-D19)
        if (column.name === "matsya" && this.folds.matsya) continue;
        let kept = leasts[column.least];
        if (column.name === "file") kept = this.dragged("file") ? this.sizes.file : this.frameWidths().file;
        else if (name === "matsya" && column.name === "view") kept = this.frameWidths().view;
        const element = frame.querySelector(`:scope > ${column.region}`);
        let extent = this.extent(element, "x");
        if (this.lent > 0 && column.name === "view") extent -= this.lent + gap;
        else if (this.lent > 0 && column.name === "matsya") extent = this.lent;
        room += Math.max(0, extent - kept);
      }
      return room;
    },
    // The height, in pixels, that the region of the handle `name` can take
    // from the regions beside it: what those regions hold above the least
    // height.
    room(name, frame, rem) {
      let room = 0;
      for (const selector of this.$options.handles[name].giving) {
        const element = frame.querySelector(selector);
        if (!element) continue;
        room += Math.max(0, this.extent(element, "y") - this.$options.leastHeight * rem);
      }
      return room;
    },
    // The handle that `event` is on, with its name, .bl-window and the
    // region it sizes; null where the event is on no handle.
    pressed(event) {
      const handles = this.$options.handles;
      const element = event.target instanceof Element ? event.target.closest(".bl-handle") : null;
      const name = element ? element.dataset.handle : null;
      const frame = this.frame();
      if (!frame || !Object.prototype.hasOwnProperty.call(handles, name)) return null;
      const region = frame.querySelector(handles[name].region);
      return region ? { element, name, frame, region } : null;
    },
    // A press on a handle starts a drag: the region's size and the
    // pointer's coordinate at the press, and the least and the greatest
    // size the drag may give the region, the least of a region in a column
    // being the least height or the least its entry names. The page's own
    // reading of the press, a text selection or a change of the focus, is
    // prevented.
    startDrag(event) {
      if (event.button !== 0 || this.drag) return;
      const found = this.pressed(event);
      if (!found) return;
      event.preventDefault();
      const handle = this.$options.handles[found.name];
      const start = this.extent(found.region, handle.axis);
      let least;
      let most;
      if (handle.axis === "x") {
        const column = this.$options.columns.find((entry) => entry.name === found.name);
        least = this.$options.leasts[column.least];
        most = start + this.widthRoom(found.name, found.frame);
      } else {
        const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
        least = handle.least !== undefined ? handle.least : this.$options.leastHeight * rem;
        most = start + this.room(found.name, found.frame, rem);
      }
      this.drag = {
        name: found.name,
        element: found.element,
        pointerId: event.pointerId,
        origin: this.coordinate(event, handle.axis),
        start,
        least,
        most,
        size: null,
      };
      found.element.setPointerCapture(event.pointerId);
    },
    // The pointer's motion sets the region's size, the size at the press
    // changed by the motion, held between the least and the greatest size;
    // a column's size gives the columns their widths.
    moveDrag(event) {
      const drag = this.drag;
      const frame = this.frame();
      if (!drag || !frame || event.pointerId !== drag.pointerId) return;
      const handle = this.$options.handles[drag.name];
      const wanted = drag.start + handle.sign * (this.coordinate(event, handle.axis) - drag.origin);
      const size = Math.min(Math.max(wanted, drag.least), Math.max(drag.most, drag.least));
      this.sizes[drag.name] = size;
      if (handle.axis === "x") this.columns();
      else frame.style.setProperty(handle.property, `${size}px`);
      drag.size = size;
    },
    // The release ends the drag and keeps its size for the folder.
    endDrag(event) {
      const drag = this.drag;
      if (!drag || event.pointerId !== drag.pointerId) return;
      this.drag = null;
      if (drag.element.hasPointerCapture(drag.pointerId)) {
        drag.element.releasePointerCapture(drag.pointerId);
      }
      if (drag.size === null) return;
      this.keepLayout();
    },
    // Whether the key event `event` arose in a text field: the element it
    // arose in, read through the shadow roots the event crossed, is an
    // input, a textarea or a select, or stands inside a contenteditable
    // element.
    inTextField(event) {
      const origin = event.composedPath ? event.composedPath()[0] : event.target;
      if (!(origin instanceof Element)) return false;
      return origin.isContentEditable || origin.closest("input, textarea, select") !== null;
    },
    // Alt+← asks for a step back and Alt+→ for a step forward, outside a
    // text field, with the browser's own reading of the keys prevented. In
    // a text field the keys keep the field's word movement on macOS; on
    // every other platform, where the browser reads them as a step in its
    // own history, they do nothing.
    step(event) {
      if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      if (this.inTextField(event)) {
        if (!navigator.platform.startsWith("Mac")) event.preventDefault();
        return;
      }
      event.preventDefault();
      if (event.key === "ArrowLeft") this.back();
      else this.forward();
    },
    // P with the primary modifier, Command on macOS and Ctrl elsewhere,
    // with no other modifier, asks Python to open Goto Anything, the
    // browser's printing prevented (spec 0.4 §5.8).
    palette(event) {
      const mac = navigator.platform.startsWith("Mac");
      const primary = mac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey;
      if (!primary || event.altKey || event.shiftKey) return;
      if (event.key !== "p" && event.key !== "P") return;
      event.preventDefault();
      this.goto();
    },
    // Escape closes Problems before other panels and returns focus to its button.
    closeProblems(event) {
      if (event.key !== "Escape") return;
      const button = document.querySelector('.bl-error-mark[aria-expanded="true"]');
      if (!button) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      button.click();
      button.focus();
    },
    // A pointer action outside Problems closes its list without moving focus.
    outsideProblems(event) {
      const button = document.querySelector('.bl-error-mark[aria-expanded="true"]');
      if (!button || event.composedPath().some(item => item.classList?.contains("bl-errors"))) return;
      button.click();
    },
    // Escape in the Recipe tab's open row closes it before other panels
    // and returns the focus to the row, unless a select of the row holds
    // its list open (design pass 11 §2).
    closeRecipeRow(event) {
      if (event.key !== "Escape") return;
      const row = event.composedPath().find(item => item.classList?.contains("bl-recipe-row"));
      if (!row || row.getAttribute("aria-expanded") !== "true") return;
      if (row.querySelector("vscode-single-select[open]")) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      row.focus({ preventScroll: true });
      this.close_recipe_row();
    },
    // A click outside the Recipe tab's table closes its open row without
    // moving focus (design pass 11 §2); a click the page dispatches itself,
    // as outsideProblems does, closes nothing.
    outsideRecipeRow(event) {
      if (!event.isTrusted) return;
      if (!document.querySelector('.bl-recipe-row[aria-expanded="true"]')) return;
      if (event.composedPath().some(item => item.classList?.contains("bl-recipe-table"))) return;
      this.close_recipe_row();
    },
    // Escape while a region's wide panel stands over the window asks Python
    // to close it (AAS, L-D11): while `wide_panel` holds, or while a panel
    // is drawn wide, whose class can come before the property.
    closePanel(event) {
      if (event.key !== "Escape") return;
      if (!this.wide_panel && document.querySelector(".bl-wide") === null) return;
      event.preventDefault();
      this.escape();
    },
    // Escape in the field of Matsya's composer moves the focus to the
    // conversation, the field keeping its text (amendment 07 §2 item 7).
    // During an input method's composition, or for the key code 229 that
    // WebKit gives a key the input method reads, the key is the input
    // method's.
    leaveComposer(event) {
      if (event.key !== "Escape" || event.isComposing || event.keyCode === 229) return;
      const path = event.composedPath();
      if (!path.some((item) => item.classList?.contains("bl-matsya-field"))) return;
      const conversation = document.querySelector(".bl-matsya-exchanges");
      if (conversation) conversation.focus({ preventScroll: true });
    },
    // The keys of the form open over the window, where one is open (AAS,
    // L-D15): Escape, the primary modifier with Enter, the arrows and Enter
    // or Space on a row of a list.
    formKeys(event) {
      const form = document.querySelector(".bl-forms .bl-form");
      if (!form) return;
      const origin = event.composedPath ? event.composedPath()[0] : event.target;
      const mac = navigator.platform.startsWith("Mac");
      const primary = mac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey;
      if (event.key === "Escape") {
        if (form.querySelector('[aria-expanded="true"], vscode-single-select[open]')) return;
        const cancel = form.querySelector(".bl-form-cancel");
        if (!cancel) return;
        event.preventDefault();
        cancel.click();
        return;
      }
      if (event.key === "Enter" && primary) {
        const button = form.querySelector(".bl-form-buttons .bl-primary");
        event.preventDefault();
        if (button && !button.disabled) button.click();
        return;
      }
      const item = origin instanceof Element ? origin.closest(".bl-list-item") : null;
      if (!item || !form.contains(item)) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        const list = item.closest(".bl-form-list, .bl-checks");
        const items = Array.from(list.querySelectorAll(".bl-list-item"));
        const next = items[items.indexOf(item) + (event.key === "ArrowDown" ? 1 : -1)];
        event.preventDefault();
        if (next) next.focus();
      } else if ((event.key === "Enter" || event.key === " ") && item.tagName !== "BUTTON") {
        event.preventDefault();
        item.click();
      }
    },
    // Whether the browser keeps the high-contrast setting on: its storage's
    // value under `contrastKey`, else the page's own value where the
    // storage is refused.
    contrastOn() {
      try {
        return window.localStorage.getItem(this.$options.contrastKey) === "high";
      } catch (error) {
        return this.contrast;
      }
    },
    // The setting written to .bl-window as data-contrast.
    applyContrast() {
      const frame = this.frame();
      if (!frame) return;
      if (this.contrastOn()) frame.setAttribute("data-contrast", "high");
      else frame.removeAttribute("data-contrast");
    },
    // The setting turned off where it is on and on where it is off, kept in
    // the browser's storage and written to .bl-window.
    toggleContrast() {
      const on = !this.contrastOn();
      this.contrast = on;
      try {
        if (on) window.localStorage.setItem(this.$options.contrastKey, "high");
        else window.localStorage.removeItem(this.$options.contrastKey);
      } catch (error) {
        // the storage refused the setting; it holds for the page's life
      }
      this.applyContrast();
    },
    // A double click on a handle removes its region's size from the window
    // and from the storage; a column takes the width the function gives
    // it, and a region in a column the height brand.css gives it.
    restore(event) {
      const found = this.pressed(event);
      if (!found || !(found.name in this.sizes)) return;
      delete this.sizes[found.name];
      const handle = this.$options.handles[found.name];
      if (handle.axis === "x") this.columns();
      else found.frame.style.removeProperty(handle.property);
      this.keepLayout();
    },
  },
};
</script>
