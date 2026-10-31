"""The Solara page of Bellman Workbench (model interface specification 0.3,
units A1 and M): the four regions over the stage files of one folder, the
loop with its four states named on screen, the refusals in the text, the
panel over every node of the view, the links from a box to the lines its
meaning reads, the legend, the sheets of the stage and the status line,
the error mark with the list of what stands refused (AMD-MI-002 §6a rule
1), and, in the window's right column, Matsya's column of
`matsya_window.py`, which the setting BELLMAN_WORKBENCH_MATSYA=off removes
(spec 0.4 §6; `MATSYA_OFF`).

The page holds its state in module-level reactive values, which Solara
stores once per browser tab (one virtual kernel per tab), and reads the
model folder through `bellman_workbench.model`. The folder is the one the
environment variable BELLMAN_WORKBENCH_FOLDER names, which the console
command sets, else the working directory. A tab shows that folder until
"new trellis" opens the folder it wrote, and every reader of the model
folder reads the tab's, `tab_folder`. A tab keeps one buffer per file
it has opened until the file is saved or reloaded, so opening another file
never discards unsaved text (specification §2.2 rule 3).

The tests' hook: when the environment variable BELLMAN_WORKBENCH_DELAY_MARKER
names a text and the buffer holds it, the loop waits 1.5 s before writing
its result, so a test of the discard knows that the marked revision's
result is the one that finishes last.

CSS class names the tests rely on:
  bl-main-bar        the main bar, the window's first row (design pass 10
                     §§2 and 3): .bl-main-start, holding .bl-mark, the
                     brand's mark, a link to the page of the Workbench in
                     the documentation, and .bl-back and .bl-forward, the
                     icon buttons Back and Forward (vscode-toolbar-button),
                     aria-disabled while no place stands behind or ahead;
                     .bl-main-path, holding .bl-crumbs, the path the tab
                     took, its title the whole path, its parts in
                     .bl-crumbs-text, one .bl-crumb per part, a button with
                     data-link (folder, recipe, period) for a part that is
                     a link, .bl-occurrence-crumb on the two parts that
                     name the selected occurrence, .bl-folder-crumb on the
                     model's folder, the parts parted by
                     .bl-crumb-separator, the Codicon chevron-right with
                     the text `›` unseen, then .bl-path-occurrence, what
                     the path does not name of the selected occurrence:
                     .bl-path-note, the occurrence the open file is bound
                     as, or the words that its source holds no occurrence
                     of it, then .bl-recipe-positions, the choice among
                     the file's positions in that source where it holds
                     several, or .bl-path-holders with a .bl-recipe-holder
                     button with data-path for each recipe that holds the
                     file where that source holds none; .bl-main-end,
                     holding .bl-goto-button (the icon button Go to, which
                     opens Goto Anything) and one .bl-toggle per panel, a
                     .bl-fold with data-fold (folder, inspector, details,
                     matsya), holding its icon .bl-toggle-icon, a Codicon,
                     a glyph .bl-toggle-glyph whose data-glyph names it, or
                     both, its aria-label and title the panel's name
                     (Files, Inspector, Details, Matsya), its
                     aria-expanded whether the panel is open, which for the
                     Inspector holds only while the panel shows the open
                     file, and aria-disabled on the Inspector while it
                     shows nothing, its title then `Nothing to inspect in
                     <file>`
  bl-region-head     the head of Details (L-D12; design pass 8 §5.5), also
                     .bl-head, data-panel details: .bl-region-name, the
                     name of its fold's toggle, Details,
                     .bl-region-context, the panel's context, then
                     .bl-head-actions, holding .bl-region-wide, the icon
                     button of the Codicon window, and .bl-region-close,
                     the icon button of the Codicon close, a .bl-fold with
                     data-fold details in the panel's column
  bl-inspector-strip the strip of the panel under the editor, its only
                     head (unit N, Task 2; design pass 10 §4): the view
                     tabs .bl-class-tabs, then .bl-inspector-file, the
                     open file's name, its path as its hover, then
                     .bl-region-wide, the icon button of the Codicon
                     window
  bl-window          the page, the grid of the main bar's row and the
                     regions (window.vue): the custom properties
                     --bl-folder-width, --bl-file-width, --bl-view-width
                     and --bl-matsya-width hold the columns' widths the
                     width function gives, --bl-classification-height and
                     --bl-panel-height the heights dragged on the handles,
                     and --bl-least-height the least height of a region in
                     a column; data-folded-folder stands while the folder
                     is folded, by the reader or by the width function,
                     and data-folded-matsya while Matsya's column is
                     folded, by the reader or while the trellis view is
                     shown (unit K's decision K-D6), during which the
                     column is not displayed and takes no width
                     (K-D19); data-folded-inspector and
                     data-folded-details while that panel is folded, by
                     the main bar's toggle or Details' close (L-D12;
                     design pass 10 §3), during which it is not displayed,
                     the first folding the panel under the editor whether
                     it shows the recipe or a stage (N-D4);
                     data-contrast="high"
                     while the high-contrast setting is on (spec 0.4 §5.8)
  bl-errors          the error mark and its list (AMD-MI-002 §6a rule 1):
                     .bl-error-mark, the button that opens and closes the
                     list, .bl-quiet while nothing stands refused and
                     .bl-active while the list is open, holding
                     .bl-error-icon and .bl-error-count, the count of what
                     stands refused or undone; .bl-error-list, the list
                     under it, .bl-hidden while closed, one .bl-error-line
                     per refusal, newest first, holding .bl-error-sentence
                     and, where the refusal names a file and a line,
                     .bl-error-place with data-path and data-line (opens
                     the file at that line), or .bl-error-file where it
                     names a file alone, and .bl-error-action, the text
                     button `open <name>` beside the note of a model's
                     declaration/ opened by itself (unit L, Task 28); or
                     .bl-error-none, `nothing refused`
  bl-refusal-mark    the mark, in the refusal's color, that a thing refused
                     keeps while its refusal stands and its sentence stands
                     in the list under the error mark: a cell or the box
                     `add field` of the classification table, the input or
                     the select of a value tab's row, or the tag of a
                     Methods row that offers no choice, the select, the
                     periods field or the button `New file` of a choice of
                     the Recipe tab refused, the
                     select of the trellis view's restriction, the button
                     of git's line whose command was refused
  bl-handle          a handle on a region's edge, data-handle naming the
                     region (folder, file, classification, panel, matsya,
                     a child of .bl-window on Matsya's left edge, and
                     composer, the first child of Matsya's composer
                     .bl-matsya-row on its top edge, which
                     `matsya_window.Composer` draws): a drag sizes the
                     region, a double click returns it to its default size
                     (AMD-MI-002 §6 rule 2; amendment 07 of spec 0.4)
  bl-folder          the folder region: .bl-folder-rail, the column's
                     head, also .bl-head, holding the h2 `Files`, the
                     folder's actions .bl-folder-bar (.bl-new-trellis,
                     .bl-new-variant, .bl-new-stage, .bl-notebook, icon
                     buttons of VSCode Elements) and .bl-rail-path, the
                     folder's name with .bl-rail-open, the open file's
                     path, drawn while the folder is folded; in .bl-tree
                     the root row .bl-tree-root, the folder's name; every
                     row of the tree and the checklist .bl-row; a folder
                     row is .bl-folder-row with
                     data-path, .bl-closed while its children are hidden,
                     every folder closed but those on the path of a file
                     opened, and a click opens or closes its children,
                     holding its twistie .bl-twistie, the Codicon
                     chevron-right or chevron-down; a
                     file row is .bl-tree-file with the attribute data-path
                     (relative to the folder), .bl-open on the open file,
                     .bl-tree-name for its name
                     and .bl-tree-mark for its mark, git's letters and the
                     word unsaved; a name of a folder or a file is
                     .bl-tree-name, holding .bl-name-word for each of its
                     words, so that it is cut at its end after a whole
                     word. The selected occurrence stands in the main
                     bar's path (.bl-main-bar), and the whole-model checks
                     in the graph bar's Problems list, not under the file
                     tree.
  bl-file            the file region: .bl-tab-row, the tabs' row, its
                     first row, holding
                     .bl-tabs with one .bl-tab-item per buffer in the
                     order opened, .bl-active on the open file's, holding
                     the button .bl-tab, data-path its path, .bl-active on
                     the open file's, whose name is .bl-file-name with
                     data-path, and .bl-modified (the mark unsaved, the
                     Codicon circle-filled), then .bl-tab-close (the icon
                     button of the Codicon close, named `Close <file>`,
                     aria-disabled while the buffer is unsaved), then
                     .bl-tab-actions, holding .bl-types-button (the text
                     button Types, aria-pressed while the types are
                     shown), .bl-notes-button (the text button Notes,
                     aria-pressed while the notes are shown) and .bl-save
                     (the primary button Save of VSCode Elements); .bl-editor (the editor's host),
                     .bl-no-stage (the sentence of a folder with no stage
                     file)
  bl-classification  the BellmanType panel under the editor, one height on
                     every tab, .bl-wide while it stands in its wide
                     panel: its .bl-inspector-strip, holding
                     .bl-class-tabs, VSCode Elements' tabs, with one
                     .bl-class-tab per tab
                     with data-tab (Fields, Parameters, Settings,
                     Methods), .bl-active on the tab shown; .bl-class-empty, the sentence
                     before the open file has elaborated; in the tab
                     Fields, .bl-class-tables
                     (.bl-stale while the buffer's text does not parse)
                     holding .bl-class-perch with data-perch, side by side,
                     .bl-class-perch-name, its title (`≺ Arrival`), its
                     hover a sentence, holding .bl-class-sign, the sign,
                     and .bl-class-perch-word, the word,
                     .bl-class-group with data-group
                     (`<perch>/<branch>`) and, in a branching stage,
                     .bl-class-branch, the group's heading
                     (`cntn · d = keep`), .bl-class-scroll, the table's
                     area that scrolls past eight rows, .bl-class-row with
                     data-identity (.bl-refusal-mark, with the refusal's
                     sentence as its title, while a refusal names the
                     field), .bl-class-field with data-line, the field's
                     button with the accessible description `line <n>`
                     (moves the editor to that line and selects the
                     field's box) where the last construction holds the
                     field, else its text, .bl-class-set in a cell
                     carrying the set as data-set, and .bl-class-role in a
                     cell carrying the role as data-role;
                     .bl-add-field, the table's last row, in its tfoot
                     (L-D21), with the entries [data-entry=field|set|role]
                     in the three columns and .bl-add-button, the icon
                     plus, in a fourth;
                     .bl-class-note, the sentence of a change written; in
                     the tabs Parameters, Settings and
                     Methods (values.vue), .bl-values with data-tab
                     (.bl-stale as .bl-class-tables) holding
                     .bl-values-file with data-path (the file the tab
                     writes), .bl-values-sentence, .bl-values-table with one
                     .bl-values-row per row, data-name naming its
                     parameter, setting or target, its cells
                     .bl-values-name, holding the name's button with
                     data-path and data-line and the accessible description
                     `<file>:<line>` (opens the file at that line) where a
                     file writes the row, .bl-values-detail (the set, the
                     kind, or the method bound, else .bl-values-refusal),
                     .bl-values-value (the input of a value) and
                     .bl-values-method (the select of the methods admitted)
                     or .bl-values-tag; the panel's data-panel is types on
                     these four tabs and recipe on the Recipe tab
  bl-recipe-table    the Recipe tab of the panel under the editor (AAS,
                     M-D17; design pass 9 §3), which stands while the open
                     file is the recipe the trellis is read under: the
                     .bl-classification (data-panel recipe) holds its
                     .bl-inspector-strip with one .bl-class-tab, data-tab
                     Recipe, then this table, role table, or
                     .bl-class-empty, `Not read`, before a reading
                     answers. It holds .bl-recipe-trellis-row, the key
                     `trellis` and the trellis file's select;
                     .bl-recipe-heads, the five column heads, each with
                     its hover; one .bl-recipe-row per stage, data-stage
                     its key, tabindex 0 and aria-expanded, "true" on the
                     one open row, which is also .bl-recipe-open, and
                     "false" on every row at rest (design pass 11 §2),
                     whose .bl-recipe-cell (data-kind stage,
                     calibration, settings, methods or periods) holds
                     .bl-recipe-line rows: in the stage's cell the line
                     .bl-recipe-key-line, the key .bl-recipe-key, with the
                     stage file's entry in the open row, and at rest a
                     second line with the file's name where it is not
                     `<key>.bl`; in a kind's cell one line per entry, the
                     first entry of a range list after its periods
                     .bl-recipe-range,
                     or .bl-recipe-none, `—`; in the periods cell the
                     periods. At rest each entry is .bl-recipe-text, the
                     entry as the table prints it, .bl-recipe-slot for a
                     slot, and the periods are .bl-recipe-text, `All`
                     also .bl-recipe-placeholder where the recipe writes
                     none. In the open row the periods are the field
                     .bl-recipe-periods, and each select stands in a
                     .bl-recipe-entry with data-address, the entry's
                     address in the recipe, holding a field of field.vue
                     (.bl-refusal-mark while its choice stands refused)
                     and, for a slot whose own file is missing,
                     .bl-new-file, the icon button of the Codicon new-file,
                     with data-address; each row's last child is
                     .bl-remove-stage (data-stage), in the table's last
                     column; after the table, in the panel,
                     .bl-recipe-add holding .bl-recipe-add-stage, the
                     text button `Stage`
  bl-view            the graph column (design pass 8 §6): its first row,
                     .bl-graph-bar, also .bl-bar, with data-graph the id of
                     the graph shown (design pass 10 §2) and data-crowded
                     while its items do not fit one row with its name,
                     which is then not drawn (graph_bar.vue), holds
                     .bl-graph-tools, holding the h2 .bl-graph-name,
                     `Semantic graph`, then .bl-graph-choice: in a
                     stage's view the select
                     .bl-view-kind (named Graph: Operator, Initial), then
                     the select .bl-view-direction (named Direction:
                     Backward, Forward), each a field of field.vue,
                     .bl-view-select, holding VSCode Elements' select, and
                     the view tabs .bl-view-switch (unit K, K-D20),
                     VSCode Elements' tabs holding the tab headers
                     .bl-stage-button and .bl-trellis-button, the one of
                     the graph shown .bl-active, each with aria-disabled
                     "true" while it does not act; in the
                     trellis view the bar also holds .bl-restriction-group
                     (restriction.vue) with .bl-restriction, the select of
                     the restriction, VSCode Elements' button, also
                     .bl-view-select, holding .bl-restriction-text, and
                     .bl-refusal-mark while the restriction's refusal
                     stands; while open, its menu
                     .bl-restriction-menu holds one .bl-restriction-item
                     per item, a range .bl-restriction-range with
                     data-text in .bl-restriction-ranges or a stage key
                     .bl-restriction-stage with data-key in
                     .bl-restriction-stages, each a .bl-row with
                     .bl-restriction-mark, the separators
                     .bl-restriction-rule and, at its foot,
                     .bl-restriction-foot with the field
                     .bl-restriction-field, VSCode Elements' text field
                     (unit K, K-D17 and K-D18); and .bl-graph-head, the
                     place in the bar where the forward trellis graph
                     draws .bl-stages-button, the text button `Stages`
                     that opens the stage list; then .bl-view-shown, `last
                     constructed <digest>`, drawn while a stage's graph is
                     dimmed; and after .bl-graph-tools, last, .bl-errors.
                     The canvas, .bl-canvas,
                     holds .bl-view-host and, floating inside its lower
                     left, .bl-graph-controls, holding .bl-graph-icons,
                     the toolbar buttons .bl-layout-button with
                     data-layout and .bl-zoom-button with data-zoom, and
                     Python's .bl-overlays-button. The host carries
                     .bl-stale while a refusal stands; its .bf-region holds
                     each .react-flow__node with data-id, containing .bf-box
                     and .bf-name, or .bf-layer and .bf-layer-name for an
                     open layer; a stage occurrence of a trellis graph,
                     closed (.bf-box) or compact (.bf-layer.bf-compact), is
                     a card, .bf-card, holding its chevron .bf-chevron, a
                     row of each printed field name, .bf-in at the left and
                     .bf-out at the right with its branch word .bf-branch,
                     its ports' marks .bf-mark, .bf-open where no join
                     reaches the field, and, compact, its builders'
                     segments .bf-builder with data-pair (AAS, L-D16 and
                     L-D25); two or more wires from one card to another of
                     a period are one .react-flow__edge.bf-pair-bundle with
                     data-from and data-to while neither card nor the
                     bundle is selected (AAS, L-D25); the .bf-box of an
                     open occurrence's own Inputs and Outputs holds the
                     label of each reading port, .bf-in, and of each
                     writing port, .bf-out (unit K, Task 21); in the
                     forward trellis graph a port a drag can take is
                     .bf-unjoined with data-port, its id in the
                     graph JSON, where no join reaches it and .bf-joined
                     where joins reach a reading port, and .bf-admitted
                     while it would take the drag in progress (J-D41); a
                     period's layer that the line of a drag would reach is
                     .bf-reached, and .bf-region is .bf-connecting while a
                     drag lasts; the frame of a stage occurrence, its
                     .bf-layer or its closed .bf-box, that a drag between
                     frames would reach is .bf-frame-target, the drag's
                     line .bf-frame-line, and the list its release opens
                     .bf-pair-list, with its head .bf-list-head (AAS,
                     L-D14), holding the Codicon `link`, .bf-list-name,
                     `join`, .bf-pair-head, the two occurrences, and the
                     button .bf-list-close, holding the Codicon `close`,
                     with the hover `close`, at its right (K-D24), and one
                     .bf-pair-row per continuation field, with data-port,
                     holding .bf-pair-tick, .bf-pair-from, .bf-pair-arrow
                     and the select .bf-pair-to, then the foot
                     .bf-list-foot with the buttons .bf-pair-cancel and
                     .bf-pair-join (unit K, K-D8), the field of the side
                     not chosen ending in .bf-pair-set, its declared set,
                     and each option printing its field's set (K-D25);
                     the same list opens
                     for an end of a join wire of several entries moved,
                     one row per field pair, the side moved its select,
                     .bf-pair-to for a reading end and .bf-pair-from for a
                     writing end (K-D23); the stage list over
                     the graph is .bf-stage-list, with its head
                     .bf-list-head, holding the Codicon
                     `symbol-structure`, .bf-list-name, `Stages`, and the
                     button .bf-list-close at its right, which closes the
                     list as Escape and a click outside the list do
                     (K-D24), then .bf-stage-heading where Python gives a
                     heading, and one .bf-stage-item per item with
                     data-item and data-kind, its .bf-stage-key holding
                     the Codicon of its kind (design pass 8 §3), the last of a
                     recipe's trellis, `From a
                     folder…`, being also .bf-stage-folder with data-kind
                     folder (K-D26); opened by a period's `+ stage`, the
                     head holds .bf-stage-period, the period's name, and
                     an item the period lists is .bf-listed, holding
                     .bf-stage-listed, the word listed (unit K, K-D14); a
                     `+ period` control is .bf-add-period with
                     data-target, .bf-reached while an item would reach
                     it, and a period's open layer holds .bf-add-stage,
                     the control `+ stage` (K-D14); a join wire is the
                     .react-flow__edge .bf-join-wire
                     with data-from and data-to, the addresses of its two
                     stage occurrences, .selected while selected, each
                     end a drag can move .react-flow__edgeupdater and,
                     while the wire is selected, drawn as .bf-wire-end
                     with data-end, writing or reading (K-D23), and
                     data-faces, the side its port faces, the square and
                     the end's circle then keeping one size on the screen
                     at every scale (K-D27); the piece
                     that the wires of one adjacent pair of periods share
                     between the two periods is also .bf-join-pair, its
                     data-from the writers' period, periods[h] (unit K,
                     K-D5), its reading end alone moved (K-D23)
  bl-legend          the legend of the graph shown, in Details:
                     .bl-legend-name (the collection's label: its name,
                     then the version's states in .bl-legend-states) and
                     one .bl-legend-group per group of the legend, with
                     data-group (levels, methods, marks, perches, roles)
                     and .bl-legend-title, each entry a .bl-legend-item
                     holding .bl-legend-swatch with data-level or data-perch
                     (.bl-legend-line for a perch), .bl-legend-text and
                     .bl-legend-sentence
  bl-panel           Details, under the view, .bl-wide while it stands in
                     its wide panel: its .bl-region-head (data-panel
                     details), whose context holds .bl-details-context,
                     the selected node's name and position; .bl-panel-body,
                     whose last element is
                     .bl-legend-details, the details element whose summary
                     .bl-fold-summary, a .bl-row, reads `Legend`, holding
                     .bl-legend, or, for a stage occurrence, the removal
                     row .bl-removal-buttons after it;
                     .bl-panel-head (.bl-panel-word, the kind of a period
                     or a builder after its identifier; .bl-panel-place, a
                     stage occurrence's period and age, or a join wire's
                     two occurrences;
                     for a box .bl-panel-kind, its kind, and the second
                     line .bl-panel-under, its identifier with
                     .bl-panel-perches, the perches its builder joins),
                     .bl-details-rows, the rows of a stage occurrence, of
                     a join wire and of the open stage file's uses, each a
                     .bl-details-row with data-key (file, refused, bound,
                     periods, also, from, to, fields, methods, sources;
                     for a join wire written, pairs or periods, measure,
                     fields and also), holding .bl-details-key and
                     .bl-details-value, one .bl-details-line per line,
                     holding .bl-details-head and one .bl-details-item per
                     part, holding the part: .bl-details-part, a text,
                     .bl-link with data-path and data-line (opens the file
                     at that line) or .bl-used-recipe (a recipe's periods,
                     see .bl-used-at); or, for a join wire's fields, the
                     table .bl-details-table, each of its rows a
                     .bl-details-line;
                     .bl-occurrence-details (a stage occurrence selected in
                     the trellis view: its head, its rows and its buttons),
                     .bl-attribute rows with data-key (.bl-attribute-key,
                     .bl-attribute-value, which wraps and is never cut,
                     holding one .bl-attribute-line per line where it has
                     several); .bl-box-details (a box selected: its head,
                     its rows, its blocks and its buttons); for a box the
                     rows at, method, lines
                     (.bl-lines-link with data-line), reads and
                     writes (one .bl-port per port: .bl-port-label, whose
                     hover is its type, .bl-port-perch, .bl-port-role and,
                     in the trellis view, .bl-port-join,
                     .bl-port-paired-by and .bl-port-outside), source (one
                     .bl-source-line per line) and uses (one
                     .bl-definition-link with data-line, or .bl-definition,
                     per definition), and .bl-math blocks, the rule's
                     .bl-rule and the kernel's .bl-kernel, each with its
                     .bl-math-label and one .bl-math-line per line holding
                     one .bl-math-part per part; .bl-signature,
                     .bl-card-button (copies the card), .bl-copy-fallback
                     (the card, where the browser refuses the clipboard),
                     .bl-paper-button (writes the stage's files under
                     paper/, drawn while it is offered),
                     .bl-block-button, .bl-item-button (to a refusal's
                     line); in the stage view a click on .bl-lines-link,
                     .bl-source-line or .bl-definition-link moves the
                     editor to its line, and in the trellis view, where
                     each carries data-path, opens that file there;
                     .bl-cursor-details, the details element whose summary
                     .bl-fold-summary reads `Cursor`, open while nothing is
                     selected,
                     holding .bl-cursor-block and .bl-block-record (the
                     block under the cursor and its record), the builder's
                     .bl-builder-rows, .bl-block-nodes (the boxes of that
                     block) and .bl-reading-nodes (the boxes whose kernels
                     read the cursor's line); .bl-name (the name
                     under the cursor, as written, standing above
                     .bl-cursor-details), .bl-name-occurrences (its
                     occurrences, each with data-line and data-column),
                     .bl-name-calibration (the line of the calibration that
                     sets it, a .bl-link) and .bl-name-boxes (the boxes
                     that depend on it), .bl-refusal (the mark of a refusal
                     of the open text: .bl-refusal-rule, its place and its
                     rule), .bl-empty-panel holding .bl-empty,
                     .bl-sheet-button with data-sheet
                     and .bl-sheet (the sheets of the stage), .bl-used-at
                     (where the shown stage file is used, AMD-MI-002 §3
                     rule 6: the rows periods and also, one
                     .bl-used-recipe with data-path per recipe that holds
                     the file, the tab's first, its text the recipe's
                     periods as ranges, its data-occurrence the occurrence
                     its link shows in that recipe's trellis),
                     .bl-occurrence-head, .bl-occurrence-open and
                     .bl-occurrence-block (an occurrence's buttons in the
                     trellis view), .bl-moved-ranges (for the terminal
                     period, one .bl-moved-range per range or range key of
                     the recipe a period typed first would move),
                     .bl-join-details (the join wire selected: its head,
                     its .bl-details-rows and its button .bl-join-remove),
                     .bl-unpaired with .bl-link items
                     carrying data-path and data-line (a refusing trellis
                     node's joins and their links), and the trellis's or
                     an occurrence's Inputs and Outputs, the rows inputs
                     and outputs of .bl-port items
  bl-trellis-refusal the mark of the trellis's refused reading in the panel,
                     its place and its rule, with .bl-address-button (opens
                     the file at the refusal's address)
  bl-status          the foot: .bl-status-lines, the details (.bl-hidden
                     while hidden), holding .bl-status-line with
                     .bl-refused (the refusal count, .bl-refused-some,
                     shown when it is not zero), .bl-state (the state of
                     the loop) and .bl-digests, and .bl-git-line; then
                     .bl-status-summary, the visible line, its separators
                     .bl-unseen: .bl-status-where holding .bl-status-place
                     (`8:33`), .bl-status-file and .bl-status-stage,
                     .bl-status-loop holding .bl-status-construction with
                     .bl-status-square (a Codicon) with data-state,
                     .bl-status-state (the state, focusable) and
                     .bl-status-digest, then .bl-status-refused,
                     .bl-status-indent and .bl-status-language, or in the
                     trellis view .bl-trellis-status, the trellis's line,
                     its parts .bl-status-part, holding
                     .bl-trellis-rest, its parts after the loop's
                     seconds, where the whole line fits, which the details'
                     line holds otherwise, headed there by the bindings
                     applied where the line with them does not fit, and
                     .bl-gesture-note, the line the last gesture of the
                     trellis graph wrote; .bl-pending; .bl-status-note (the
                     sentence of the file `paper` or `notebook` wrote); and
                     .bl-status-toggle, the icon button More or Less, with
                     aria-expanded
  bl-choice          the choice after a save met a changed file, drawn in
                     the refusal's color: .bl-choice-compare,
                     .bl-choice-overwrite, .bl-choice-reload, and .bl-diff
                     for the comparison
  bl-term            a printed term carrying its definition in its title
  bl-matsya          Matsya's column, the window's last column, from its
                     first row to its foot, absent with the setting off,
                     not displayed while folded, whose classes
                     `matsya_window.py` lists
  bl-goto            Goto Anything (goto.vue; spec 0.4 §5.8), the palette
                     over the text, hidden while closed: .bl-goto-input,
                     the field, and one .bl-goto-result per result, .bl-active
                     on the current one, holding .bl-goto-text,
                     .bl-goto-kind (block, box, line, text or command) and
                     .bl-goto-address
  bl-forms           the form open over the window: .bl-form with
                     data-form (`new trellis`, `new variant`, `new stage`,
                     `add stage`, `add period`, `commit`), also
                     .bl-form-wide for `new trellis` and the form from a
                     folder (AAS, L-D14); its .bl-form-top, holding its
                     .bl-form-head, also .bl-head, the Codicon of its
                     kind, .bl-form-icon, its h2, the form's name and its
                     .bl-form-context, and .bl-form-close, the icon
                     button of the Codicon close, then its .bl-form-note;
                     its fields, each a field of field.vue, .bl-field with
                     the field's class, two on one .bl-form-row in `new
                     trellis`, a list's .bl-form-label, .bl-form-error,
                     the refusal under the field it concerns, and
                     .bl-form-buttons, holding the text button
                     .bl-form-cancel, then the primary .bl-primary, a
                     button of VSCode Elements; each
                     row of a list or a choice .bl-list-item; in the
                     commit form one checkbox .bl-commit-path per change,
                     also .bl-commit-tick, with data-path and
                     aria-checked, also .bl-unticked where left out, the
                     message .bl-commit-message and .bl-commit-submit; in
                     the form new trellis .bl-create-name,
                     .bl-create-repeat, .bl-create-parent (unit L, Task
                     13), .bl-create-destination,
                     .bl-create-label, the list .bl-templates, also
                     .bl-form-list, holding .bl-template-refused where the
                     corpus cannot be read, and, with data-template and
                     its .bl-template-name, .bl-template-model and
                     .bl-template-refusal, in the place of each entry
                     whose template the package refuses, and one
                     .bl-template per
                     template with data-template, also .bl-active once
                     chosen, holding its .bl-template-button with
                     data-template, role and aria-checked, whose
                     .bl-template-name, .bl-template-model and
                     .bl-template-calibration print its key, its model's
                     folder and its parameters, and, once chosen, its
                     .bl-create-key and .bl-create-period, whose two
                     buttons carry data-period (every, terminal) and
                     .bl-active with aria-pressed true on the one chosen
                     (unit K, Task 12), and .bl-create-submit; in the
                     form add stage the templates as in new trellis
                     without .bl-create-period, the field .bl-create-key
                     under the list, and .bl-add-submit, with
                     .bl-add-period-file where the recipe's trellis file
                     names two period files; opened by `From a folder…`
                     (K-D26), the form add stage holds the field
                     .bl-folder-path, the chooser .bl-folder-chooser,
                     also .bl-form-list, holding .bl-form-list-head, the
                     name of the folder listed, and .bl-folder-choices
                     with one .bl-folder-entry per entry, each also
                     .bl-choice-file with data-path, the one the field
                     names also .bl-current, and either the stage's
                     .bl-template with .bl-create-key under it or
                     .bl-folder-reason, why the path names no stage, then
                     .bl-folder-period where it holds a select of the
                     period, and .bl-add-submit; in the form add period
                     .bl-period-label, the checkboxes .bl-checks, also
                     .bl-period-stages, one .bl-period-stage per stage of
                     the recipe with data-key and aria-checked, and
                     .bl-period-submit; in the form new variant
                     .bl-variant-name and .bl-variant-submit; in the form
                     new stage .bl-new-stage-key and .bl-new-stage-submit
  bl-git-line        git's line: git's summary, .bl-git-commit,
                     .bl-git-push, .bl-git-export, which writes the shown
                     view and its record, each with .bl-refusal-mark while
                     the refusal of its last command stands, and
                     .bl-git-sentence, git's own sentence of the last
                     command or the sentence of the last export, paper or
                     notebook, where it was not refused
"""

from __future__ import annotations

import dataclasses
import difflib
import functools
import hashlib
import importlib.metadata
import itertools
import logging
import os
import posixpath
import re
import shutil
import threading
import time
from pathlib import Path

import reacton.ipyvuetify as rv
import solara
import solara.lab
import solara.server.settings
from solara.components.head_tag import HeadTag

from bellman.stage import (
    INITIAL_IDS,
    LAYER_COLORS,
    LAYER_ID_ENDING,
    NODE_STYLE,
    OUTPUT_STYLE,
    layers_to_open,
    node_place,
    source_spans,
)
from bellman.syntax.vocabulary import ARRIVAL, CONTINUATION, DECISION, PERCH_SIGN, PERCH_WORD
from bellman_workbench import (
    creation,
    desktop,
    icons,
    matsya_client,
    matsya_window,
    matsya_work,
    model,
    navigation,
    recipe,
    returned,
    trellis,
)

HERE = Path(__file__).resolve().parent

# the one stylesheet of the application (specification §9), the brand's
BRAND_CSS = (HERE / "brand.css").read_text(encoding="utf-8")

# Solara serves package files at /static/assets/<folder>/<file> (G-D12).
# The second location supplies /static/assets/favicon.svg before Solara's.
PUBLIC_FOLDER = HERE / "public"
BRAND_FOLDER = PUBLIC_FOLDER / "brand"
for folder in (PUBLIC_FOLDER, BRAND_FOLDER):
    if str(folder) not in solara.server.settings.assets.extra_locations:
        solara.server.settings.assets.extra_locations.append(str(folder))

# the model folder of the process, read once at import: the folder a new
# tab shows (C-R7)
FOLDER = model.open_folder(os.environ.get("BELLMAN_WORKBENCH_FOLDER") or os.getcwd())

# The page's log, the server's standard error where nothing else configures
# it: an exception the package raises where a refusal was due is written
# there with its traceback, in the words of `model.EXCEPTION_LOGGED`, so that
# it can be filed against the package (unit L, Task 21; defect 18 of the UX
# simulation).
LOG = logging.getLogger(__name__)

# the tests' hook: the text whose presence in the buffer delays the loop
DELAY_MARKER = os.environ.get("BELLMAN_WORKBENCH_DELAY_MARKER")
DELAY_SECONDS = 1.5

# Whether the setting BELLMAN_WORKBENCH_MATSYA=off holds, read once at
# import, when the server starts: the page then renders neither Matsya's
# column nor its handle, and no client is called (spec 0.4 §6; R-D8).
MATSYA_OFF = matsya_client.switched_off()

# the seconds between two readings of the open file's digest on disk
WATCH_SECONDS = 2.0

# The lock under which the open path, the buffers and the choice change
# together, under which the loop compares its revision with the buffer's
# and replaces the result, and under which the watcher compares the file
# on disk with the buffer and acts. Each assignment of a reactive value
# renders synchronously, so without the lock a newer revision and its loop
# could run between the loop's comparison and its writes, and the watcher
# could read the buffer of a file that a reload was replacing.
LOOP_LOCK = threading.Lock()

# The lock under which a value typed in the Parameters or Settings tab is
# added to the queue of values to write (`value_queue`) or taken from it, so
# that no value is added or answered twice (unit L, Task 16).
VALUE_LOCK = threading.Lock()
# The lock that one writer of the queue holds from its first value to the
# follow-up of its last write (`write_queued`), so that the values are
# written in the order of their Enter, each once, and the buffers and the
# tree are brought to the files' last texts (unit L, Task 16).
WRITER_LOCK = threading.Lock()
# the number of ids of answered values that `value_queue` keeps
VALUE_ANSWERS = 64

# the depth of the namespaces the view opens for a stage, the lessons' depth
LAYER_DEPTH = 1

# The tables the region matches the exported styles against (spec 0.4 §2.1,
# G-D2): a node's style, NODE_STYLE or OUTPUT_STYLE, and a layer's fill,
# border and label by its level, LAYER_COLORS, each as the graph JSON
# writes them.
GRAPH_STYLES = {
    "node": dataclasses.asdict(NODE_STYLE),
    "output": dataclasses.asdict(OUTPUT_STYLE),
    "layers": {level: list(colors) for level, colors in LAYER_COLORS.items()},
}

# the documentation site, and the editor's page on it, which the title
# bar's mark links to
DOCS_URL = "https://econ-ark.github.io/bellman/"
WORKBENCH_PAGE = f"{DOCS_URL}overview/07-workbench/"

# the names of the sheets of the stage the panel reaches when nothing is
# selected, in the order of their buttons (`model.stage_sheets`)
SHEETS = ("view", "definitions", "fields", "obligations", "diagnostics")

# the word on screen for a rule of the package whose name is not a word
# (specification §2.4: one word per fact); every other rule is printed as
# the package names it
RULE_WORDS = {"not-constructed": "not constructed by this version"}

# The Unicode shortcuts of the VS Code extension, prefix to body, read once
# from its snippets file and passed to the editor and to the classification
# tables as their property `shortcuts`, expanded on Tab (unit T, rule 6).
SHORTCUTS = model.unicode_shortcuts()

# The number of spaces of one indent of the editor, which Tab inserts where
# no shortcut ends (R-D33).
INDENT = 4

# The terms the status line and the panel print, each with its definition
# in a few plain words, carried in the title of the printed word
# (specification §2.4: every term carries its definition on hover or a link
# to its page; AMD-MI-002 §6a rule 2: a hover carries at most one short
# sentence).
TERMS = {
    "elaborated": "parsed and constructed by the package as a stage object",
    "not parsed": "the parser refused the text",
    "parsed, refused": "the text parsed, and the construction refused it",
    # spec 0.4 §§5.6 and 5.7; unit R, brief §5; R-D19
    "constructed": "The language's check, not a verification of the economics.",
    "constructed, forward refused": "the stage object exists, its forward builders graph refused",
    "constructed, backward refused": (
        "the stage object exists, its backward builders graph refused"
    ),
    "builder": "the operator a block denotes, from one perch to the next",
    "sub-builder": "a builder inside a builder, authored by a !node line of the block",
    "wire": "a function or a measure one box writes and other boxes read",
    "block": "a bracketed group of lines of the file, from a block header to its brace",
    "refused": "the package refused what a file writes",
    "text": "the first seven characters of the SHA-256 digest of the editor's text",
    "calibration": "the sources that give a stage occurrence's parameters their values",
    "methods": "the sources that bind numerical methods within a stage occurrence",
    "settings": "the sources that give a stage occurrence's grid sizes and tolerances",
    "symbolic": "as the stage file alone defines it, with nothing bound",
    "bound": "with the calibration, methods or settings the recipe names applied",
    "loop": "the seconds the last reading took, from the text to the view",
    "kind": "the kind of the box's operator, or block or field in an initial diagram",
    "kernel": (
        "the equations the box realizes, as the package prints them, for its own branch "
        "where it has one"
    ),
    "rule": "the equation the box's operator states, or the rule of a refusal",
    "lines": "the lines of the file the box's record quotes",
    "method": "the numerical method bound within the piece, named by its tag",
    "requires": "the derivatives a bound method of the builder reads that no route supplies",
    "handler": "the program the bound method's tag names, as the methods file writes it",
    "option": "one option the methods file gives the bound method",
    "card": "the printed record of the piece, denote(), which the button copies",
    "perch": (
        "the perch of the field whose function the wire carries, with the function's domain "
        "in type"
    ),
    "role": "what the wire carries: a value, a measure or a control",
    "type": "the domain and the codomain of the function the wire carries",
    "label": "the wire's name as the drawing prints it",
    "inputs": "the wires a builder or a builders graph reads",
    "outputs": "the wires a builder or a builders graph writes",
    "signature": "the inputs and the outputs of a builder or of a builders graph",
    "feasible set": "the set a choice must lie in, as the file declares it",
    "parameter": "a named number of the model, declared with its set",
    "setting": "a numerical knob the settings source binds",
    "where": "a local abbreviation the block declares",
    "address": "the block or the line of the file an item was made at",
    "not constructed by this version": "a form this version of the package does not construct",
    "backward": (
        "the direction of the value functions, from the continuation perch to the arrival perch"
    ),
    "forward": "the direction of the measures, from the arrival perch to the continuation perch",
    "unsaved": "the editor's text differs from the file on disk",
    "source": "the lines of the file the card quotes",
    "Inputs": "the inputs of the builders graph, its signature's first part",
    "Outputs": "the outputs of the builders graph, its signature's second part",
    "box": "one primitive operator of a builders graph, drawn as one node of the view",
    "header": "the block's first line, in brackets: its id and the perches it joins",
    "statement": "one line of the block, as the file writes it",
    "edge": "the perches the field is carried between, in the direction of the diagram",
    "set": "the set the field takes its values in, as the file declares it",
    "trellis": "the model over its periods, each a frame of its stage occurrences",
    "occurrence": "one use of a stage file at one position of the trellis",
    "period": "one date of the model, numbered from the terminal period, periods[0]",
    "join": "a continuation field of one occurrence joined to an arrival field of another",
    "paired by": "the rule that paired a backward join's wire with the wire that supplies it",
    "outside": "the occurrence at the other end of a join, outside the view",
    "restriction": "the periods and the stage keys the trellis view holds",
    # the word `slots` under the recipe's blocks, before the keywords that
    # bind the recipe's slots when it is loaded (K-D29; the factory page,
    # §3.3)
    "slots": "the keywords that supply values to the recipe's slots when it is loaded",
    "declaration": "the line at which the stage file declares the name",
    "depends on": "the box's kernel, wires or definitions use the name",
    # the keys of the rows of Details for a stage occurrence (design pass
    # §2; unit K, K-D2)
    "file": "the file, relative to the model folder",
    "periods": "the periods at which the recipe shown uses the stage file",
    "also": "the folder's other recipes that use the stage file, with their periods",
    "from": "the occurrence a join comes from, whose continuation fields it joins",
    "to": "the occurrence a join goes to, whose arrival fields it joins",
    "route": "the branch of a cable and the two occurrences it joins",
    "status": "whether the package certifies the route for a complete composition",
    "wires": "the wires of a cable in the route's order, each with its set and its origin",
    "policies": "the controls of the occurrence's stage",
    "fields": "the stage's fields by perch, each with its set and, unless a state, its role",
    "sources": "the calibration, settings and methods files the recipe binds to the occurrence",
    # the keys of the rows of Details for a join wire (design pass §2;
    # unit K, Task 4), and the terms `JOIN_TERMS` names for its `periods`,
    # `fields` and `also`
    "written": "the file and the entry that write the join, or the equal names that make it",
    "pairs": "the adjacent pairs of periods for which the entry writes the join",
    "measure": "the writer's continuation measure and the reader's arrival measure",
    "join periods": "the periods in which the entry writes the join",
    "joined fields": "each continuation field and the arrival field it becomes, with its set",
    "same entry": "the other occurrences the same entry joins to the same reader",
    # the keys of the rows of Details for a box and the summary of the fold
    # that holds the block under the cursor (design pass §2, "An operator
    # box"; unit K, Task 5)
    "at": "the policies at which the box applies its operator",
    "reads": "the wires the box reads, each with its perch and its role",
    "writes": "the wires the box writes, each with its perch and its role",
    "uses": "the definitions the box's record names, each with the line that declares it",
    "cursor": "the block under the editor's cursor, its record and the boxes it concerns",
    # the label of the name under the cursor, outside the fold `cursor`
    # (design pass §1 item 8; unit K, Task 6)
    "name": "the name under the editor's cursor",
}

# the page of the documentation a term links to, under API/stage/
TERM_PAGES = {
    "builder": "04-builder",
    "sub-builder": "04-builder",
    "signature": "04-builder",
    "kernel": "05-piece",
    "card": "05-piece",
    "kind": "05-piece",
    "rule": "05-piece",
    "lines": "05-piece",
    "method": "07-methods",
    "parameter": "06-par-and-settings",
    "setting": "06-par-and-settings",
    "uses": "08-definitions",
    "calibration": "09-binding-verbs",
    "methods": "09-binding-verbs",
    "settings": "09-binding-verbs",
    "bound": "09-binding-verbs",
    "wire": "10-model-explorer",
    "perch": "10-model-explorer",
    "role": "10-model-explorer",
    "type": "10-model-explorer",
    "label": "10-model-explorer",
    "elaborated": "01-the-stage",
    "constructed": "01-the-stage",
    "block": "02-initial",
}

# the numbers given to the documents the editor holds, one per load,
# reload or switch of a file, unique within the process
_document_numbers = itertools.count(1)

# the numbers of the places asked of the view, one per request, unique
# within the process, so that the view shows a place again even where it
# equals the one asked before
_place_numbers = itertools.count(1)


@dataclasses.dataclass(eq=False)
class Shown:
    """The last buffer of a file that elaborated, which the view and the
    panel show: the file, its text and revision, the stage object (bound as
    the folder's recipe binds it), the collection of the view, the
    layers to open per graph, the block spans of the text, the
    counts, the seconds the loop took, the digest of the text, the notes of
    the bindings that did not apply, the occurrence the stage is bound as
    (None where no source binds the file), the version (`symbolic` or
    `bound`), the digests of the inputs by name (`model.input_digests`),
    and the digest of each binding source's file by its path, which the
    watcher compares; `position`, the occurrence `(h, key)` the stage is
    bound as, and `record`, its record, both None where no source binds
    the file; `source`, the source of the folder's trellis the stage was
    bound through, None where the folder offers none; `positions`, every
    position of the file in that source (`recipe.Found`), none where the
    source holds no occurrence of it; `uses`, each source of the folder
    with its positions of the file (`recipe.uses_of`), the source the stage
    was bound through first (AMD-MI-002 §3 rule 6); `made`, the moment
    the loop made it (`time.monotonic`), the moment of its binding notes in
    the list under the error mark (AMD-MI-002 §6a rule 1); and `refusal`,
    the `model.Diagnostic` of the refused reading of the source, whose
    sentence is then the one note, None where the source reads
    (`recipe.Found`; ruling R51); and `declared`, the collection of the
    declared builders where a bound method block opens a builder
    (`model.two_levels`), None where the two levels are one object, which
    the layers button switches to and from (specification 0.6 §9). Its
    property `places_refusal` is the package's refusal to list the places
    of the stage, read once."""

    path: str
    text: str
    revision: int
    stage: object
    collection: dict
    layers: dict
    spans: dict
    counts: dict
    seconds: float
    digest: str
    notes: list
    occurrence: str | None
    version: str
    digests: dict
    source_digests: dict
    position: tuple | None = None
    record: dict | None = None
    source: recipe.Source | None = None
    positions: tuple = ()
    uses: tuple = ()
    made: float = dataclasses.field(default_factory=time.monotonic)
    refusal: model.Diagnostic | None = None
    declared: dict | None = None

    @functools.cached_property
    def places_refusal(self) -> str | None:
        """The package's refusal to list the places of the stage at which
        methods are bound (`recipe.places_refusal`), None where it lists
        them (unit L, Task 18). It is read at the first read and kept, since
        the list under the error mark is read at every render and `places()`
        took up to 0.3 s on a stage of the applications."""
        return recipe.places_refusal(self.stage)


@dataclasses.dataclass(eq=False)
class Outcome:
    """What the loop answered for one buffer revision: the file and the
    revision; the state of the loop (`model.loop_state`, None for a file
    that is no stage); the counts of the object; the seconds; the digests
    of the inputs by name; the version, `symbolic` or `bound`, None where
    no stage exists; the diagnostics with a position for the editor; the
    refusals for the panel, each a record with the message, the rule, the
    address, the position and, for a refused builders graph, its
    direction; whether the view is stale; a note for a file opened as text;
    the block spans of this revision's text, None when the parser refuses
    it or the file is no stage; and `made`, the moment the loop answered
    (`time.monotonic`), the moment of its refusals in the list under the
    error mark (AMD-MI-002 §6a rule 1)."""

    path: str
    revision: int
    state: str | None
    counts: dict
    seconds: float
    digests: dict
    version: str | None
    diagnostics: list
    refusals: list
    stale: bool
    note: str | None
    spans: dict | None = None
    made: float = dataclasses.field(default_factory=time.monotonic)


# --- the state of one tab ---

tree = solara.reactive([])
# whether the folder has been read once, so that an empty folder is told
# apart from a folder not yet read
folder_read = solara.reactive(False)
git_line = solara.reactive("")
# the paths of the folders of the tree the tab has open: none when a
# folder opens, then those on the path of each file opened and those a click
# opens (R-D52)
open_folders = solara.reactive(())
# the file open in the editor, relative to the folder; None before one is
open_path = solara.reactive(None)
# One buffer per file the tab has opened, keyed by the file's path: `text`,
# the text the loop elaborates; `revision`, the number of texts the buffer
# has held; `digest`, the digest of the file's text as read from or last
# written to the disk; `document`, the text last given to the editor for
# the file; and `document_revision`, the number that text was given under,
# which every event of the editor carries back, so that an event of an
# older document is dropped (specification §2.2 rule 1).
buffers = solara.reactive({})
# the loop's results by path: {"outcome", "shown", "revision", "rebind"}
results = solara.reactive({})
# the stage the view draws: the last `Shown` written for the open file
shown = solara.reactive(None)
# a count the watcher raises when a binding source changed on disk, which
# makes the loop bind the open buffer again, and the digests of the sources
# as they stood when it last raised the count, so that one change on disk
# raises it once while the loop that answers it runs
rebind = solara.reactive(0)
rebind_sources = solara.reactive({})
# the file a click asked to open, while the editor's document is read back
# through a flush request, so that typing within the pause is kept
switching = solara.reactive(None)
flush_request = solara.reactive(0)
# the open file whose tab's `×` was pressed, while the editor's document is
# read back through a flush request, so that typing within the pause counts
# as unsaved before the tab closes (`close_file`); None otherwise
closing = solara.reactive(None)
graph = solara.reactive("backward")
selected = solara.reactive(None)
select_request = solara.reactive(None)
goto_request = solara.reactive(None)
save_request = solara.reactive(0)
# True while the next save is the overwrite chosen after a changed file
overwrite_pending = solara.reactive(False)
# The choice that stands for the open file after a save met a changed file,
# or after the file changed on disk under unsaved text: {"reason",
# "disk_text", "disk_digest", "buffer_text", "made"}, `made` the moment
# (`time.monotonic`); or None. Its reason stands in the list under the
# error mark (AMD-MI-002 §6a rule 1).
conflict = solara.reactive(None)
compare_open = solara.reactive(False)
# the block the cursor stands in, the cursor's line, and the view's nodes
# of that block
cursor_block = solara.reactive(None)
cursor_line = solara.reactive(None)
block_nodes = solara.reactive([])
# the cursor's place, `(line, column)` counted from one, the column in code
# points, at which the panel reads the name under the cursor in the shown
# object's own text; None until the cursor moves in a shown stage's text
cursor_place = solara.reactive(None)
# True from a reading that gives the view a new collection, a stage's
# (`_show`) or the trellis's (`run_trellis`), until the view reports it
# processed; a change of graph, of layout or of view mode sets no mark
drawing = solara.reactive(False)
# The graph region's refusal, with its sentence and time.monotonic moment
# `made`; None after a successful layout (G-D9).
layout_refusal = solara.reactive(None)
# An external file request waits for its own elaboration and graph.
desktop_pending = solara.reactive(None)
desktop_refusal = solara.reactive(None)
# True while the editor draws each bracket group that carries an identity as
# its name alone; the tab's own choice, kept across files and written nowhere
hide_types = solara.reactive(False)
# True while the editor draws every note, the quoted explanation of an
# annotation, as written; False, the first value, draws each as its note
# glyph (design pass 10 §§4 and 9; unit N, Task 4); the tab's own choice,
# kept across files and written nowhere
show_notes = solara.reactive(False)
# True while the view draws the perch overlays (the button `perch overlays`)
overlays_on = solara.reactive(False)
# True while the graph and Details show the operative builders,
# `stage.builder`; False, the first value, shows the declared builders,
# `stage.declared` (the layers button; specification 0.6 §9; SE-6); written
# nowhere, so that every page and every folder opens on the declared builders
builders_operative = solara.reactive(False)
# the sheet of the stage the panel shows when nothing is selected, or None
sheet_open = solara.reactive(None)
# True while the foot shows the status line's details, the line of the
# inputs' digests, the counts and the seconds, and git's line, which the
# button `more` shows and `less` hides (spec 0.4 §5.7; R-D9)
show_status = solara.reactive(False)
# Unit B (specification §3): the sources of the folder's trellis
# (`recipe.model_sources`), the one whose trellis is shown or last was, and
# whether the view shows the trellis or the open stage file
sources = solara.reactive([])
source = solara.reactive(None)
view_mode = solara.reactive("stage")
# the last trellis read, `trellis.TrellisShown`, and the last reading's
# outcome, a refusal among them
trellis_shown = solara.reactive(None)
trellis_outcome = solara.reactive(None)
# a count the watcher raises when a file of the trellis's last reading
# changes on disk, a file it read or, for a refused reading, one whose change
# reads it again; and the digests of those files, recorded by the reading as
# it read them (`trellis.show_trellis`) and by the watcher when it raises the
# count, so that one change reads the trellis again once
trellis_rebuild = solara.reactive(0)
trellis_seen = solara.reactive({})
# the occurrence the head of the recipe names, `(h, key)`; the open stage file
# is bound as it where it is one of the file's occurrences
head = solara.reactive(None)
# the text of the restriction as written last, chosen from the menu of the
# view's bar or typed at its foot, which the bar's select prints and the field
# at the menu's foot holds; the restriction applied last, a
# `trellis.Restriction` (None for the whole trellis); and the parser's refusal
# of a text, {"sentence", "made"}, `made` the moment of the refusal
# (`time.monotonic`), or None
restriction_text = solara.reactive("")
restriction = solara.reactive(None)
restriction_refusal = solara.reactive(None)
# the text the window itself last wrote into the bar, for a new source
# (`_use_source`), for a link into a position (`_draw_position`) or for a
# place shown again whose restriction was the window's opening text or a
# link's `periods h` (`_restore`): `periods 0–2`, `periods h` or the empty
# text
restriction_opening = solara.reactive("")
# True while `_use_source` writes a new source's opening text into the bar,
# before it sets the source
writing_opening = solara.reactive(False)
# The refusal of a change of the Recipe tab (design pass 9 §3),
# {"sentence", "address", "control", "file", "line", "made"}: the address of
# the entry or the periods changed; the control refused, `select`, `new
# file` (unit K's decision K-D7) or `periods`; the file that writes it, the
# entry's line there (None where none is found) and the moment of the
# refusal (`time.monotonic`); or None
choice_refusal = solara.reactive(None)
# The model folder the tab shows: the process's folder, FOLDER, until "new
# trellis" opens the folder it wrote (specification §4: the editor opens
# the recipe). Every reader of the model folder reads this value; "new
# trellis" writes, by default, in the folder that holds it (C-R7, amended
# by unit L, Task 13).
tab_folder = solara.reactive(FOLDER)
# the form open over the window, None for none: "new trellis", "new
# variant", "new stage", "add stage", "add period" or "commit"; and the
# sentence of the form's last refusal
form_open = solara.reactive(None)
form_error = solara.reactive("")
# the answer of the form "new trellis" that its last refusal concerns, the
# `field` of a `creation.AnswerRefusal`, `parent` for a parent that is no
# full path, None for a refusal that concerns no one answer, under which
# field the form draws the refusal (design pass 4 §2; unit L's final
# judgment, §6 item 10)
form_error_field = solara.reactive(None)
# the number of refusals of a form's gesture (`_refuse_form`), by whose
# change the form from a folder gives its key field the focus again (AAS,
# L-D5)
form_refusals = solara.reactive(0)
# The answer to the last command of git's line or of the buttons `paper`
# and `notebook` (R-D42), {"command", "sentence", "refused", "made"}, or
# None before any: the command, `commit`, `push`, `export`, `paper` or
# `notebook`; git's own sentence of a commit or a push, or, where git
# refused a commit and wrote none, a sentence that says so, or the sentence
# of the export, of `paper` or of `notebook`; whether the command was
# refused; and the moment of the answer (`time.monotonic`). Git's line
# prints the sentence of an answer not refused, and the status line's note
# that of `paper` or `notebook` (ruling R-P6); the list under the error
# mark holds that of a refused one.
git_answer = solara.reactive(None)
# the commit form: the changes git reported under the folder when it
# opened, the paths left out of the commit, and the message
commit_changes = solara.reactive(())
commit_unticked = solara.reactive(frozenset())
commit_message = solara.reactive("")
# the entries answers.yml marks in the tab's folder (`creation.checklist`),
# read with the tree and again at each change of a buffer, each unsaved
# buffer read in place of its file (`read_checklist`)
checklist = solara.reactive(())
# The panel, `recipe`, `types` or `details`, that stands in its wide panel
# over the window, or None (AAS, L-D12; design pass 3 §2; design pass 9
# §2); the tab's own choice,
# written nowhere. Whether a panel is open or closed is window.vue's, which
# keeps it for the folder in the browser's storage.
region_wide = solara.reactive(None)
# the place the editor moves to once the file being opened is open,
# {"path", "line", "column"}, with "end" where the editor selects the text
# up to `(end_line, end_column)` (J-D40), or None
pending_goto = solara.reactive(None)
# The last edit the classification table asked of the editor (unit T, rule
# 3): {"edits", "expected", "n"}, the replacements in code points, the text
# the tables were read from, and a count, so that each request is new.
edit_request = solara.reactive(None)
# The note of the last change of the Fields tab's tables, which stands while
# the stage shown when the change was made, the file's last construction, is
# shown: {"group", "kind", "identity", "sentence", "refused", "revision",
# "path", "made"}, `kind` and `identity` those of the change, `revision` and
# `path` that stage's, `refused` whether the change was refused and `made`
# the moment of the note (`time.monotonic`); or None. A refused change's
# sentence stands in the list under the error mark and its cell or box is
# marked; a change written is told in its sentence under its group.
table_note = solara.reactive(None)
# The tab of the BellmanType panel shown, Fields until another is chosen
# (AMD-MI-002 §5, A2-D7); the tab's own choice, written nowhere.
class_tab = solara.reactive("Fields")
# The last refused write of the Parameters, Settings or Methods tab, which
# stands while the panel shows the file, the occurrence and the source on
# which the write was asked: {"tab", "name", "sentence", "file", "line",
# "path", "position", "source", "made"}, `name` the row's, `file` and
# `line` the file the write would change and the row's line there (None
# where the row has none), `made` the moment of the refusal
# (`time.monotonic`); or None. Its sentence stands in the list under the
# error mark, and the row's input or select is marked on its tab.
value_note = solara.reactive(None)
# A count raised by each write of the Methods tab, so that the tab shown
# reads its files again at once and does not show the method it replaced
# until the loop has bound the stage again.
value_writes = solara.reactive(0)
# The values typed in the Parameters and Settings tabs (unit L, Task 16;
# defect 5 of the UX simulation): {"queue", "answered"}. `queue` holds the
# values typed and not yet written, in the order of their Enter, each
# {"id", "tab", "name", "shown", "typed", "current", "folder"}: `id` the
# text values.vue gave the Enter, `shown` the value the input showed,
# `typed` the text typed, `current` the stage shown at the Enter, at whose
# occurrence the value is written, and `folder` the tab's folder then.
# `answered` holds the ids of the last VALUE_ANSWERS values taken from the
# queue, written or refused: by its change the tab shown reads its files
# again, and values.vue stops holding the text typed under each id.
value_queue = solara.reactive({"queue": (), "answered": ()})
# The tab's history of places (AMD-MI-002 §3 rule 4), kept for the tab's
# life and emptied by `open_model` (A2-D5), and written nowhere (rule 7).
history = solara.reactive(navigation.History())
# The place the history last showed again, which the view is asked to show
# once its collection is the place's own (`view_request`): {"place", "n"},
# `n` a number no other request of the process carries; None where no place
# is asked.
place_request = solara.reactive(None)
# True while the list under the error mark is open (AMD-MI-002 §6a rule
# 1); the tab's own choice, written nowhere
errors_open = solara.reactive(False)
# The last fold a command asked of window.vue, which keeps the folds (spec
# 0.4 §5.1; brief rule 3): {"region", "n"}, `region` `folder` or `matsya`,
# the folds the commands of Goto Anything name, and `n` a count, so that
# each request is new; or None.
fold_request = solara.reactive(None)
# A count raised by each opening of Goto Anything, which goto.vue reads
# (`open_goto`; spec 0.4 §5.8; ruling R-P2).
goto_open_request = solara.reactive(0)
# A count raised by each run of the command `high contrast`, on which
# window.vue turns the setting on or off for the browser (R-D24).
contrast_request = solara.reactive(0)


def _digest(text: str) -> str:
    """The SHA-256 digest of the UTF-8 bytes of `text`, in hexadecimal."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _session() -> str:
    """The name of the tab's conversation with Matsya: the first twelve
    characters of the SHA-256 digest of the tab's folder's path, so that
    no question sends the folder's name off the machine (spec 0.4 §6,
    decision 32; R-D21)."""
    return _digest(str(tab_folder.value.root))[:12]


def matsya_context() -> matsya_window.Context:
    """The context beside Matsya's composer (amendment 06 §2 item 1): the
    file name of the recipe or trellis file the tab shows (`source`, or the
    folder's first source), else the open stage file; whether a file it
    reads holds unsaved text, by the files the trellis shown read where it
    is that source's, else by the source's own buffer; the folder's
    project session, named after the folder, as the client's `project
    init` names it, the column naming the job its conversation discusses
    (`matsya_window.discussed`); and the service's address, the project's
    where the folder is connected, else the one the client's settings name;
    the configuration is the service's default, since no configuration is
    chosen (item 10)."""
    # a connection made in the column reads the context again
    matsya_window.connections.value
    folder = tab_folder.value
    shown = source.value or (sources.value[0] if sources.value else None)
    path = shown.path if shown is not None else None
    if path is None and _is_stage(open_path.value):
        path = open_path.value
    dirty = _dirty_paths()
    held = trellis_shown.value
    if shown is not None and held is not None and held.source == shown:
        read = {recipe.relative(folder, file) for file in held.files}
    else:
        read = {path} if path else set()
    project = matsya_work.project(folder)
    service = project["server"].split("://", 1)[-1] if project else matsya_client.service_address()
    return matsya_window.Context(
        source=Path(path).name if path else None,
        unsaved=bool(dirty & read),
        session=folder.root.name if project else None,
        job=None,
        service=service,
        configuration=None,
    )


def _matsya_buffers() -> dict:
    """The editor's unsaved buffers as unit G2's `matsya_work.Buffer`, by
    the file's path from the folder."""
    return {
        path: matsya_work.Buffer(held["text"], held["digest"])
        for path, held in buffers.value.items()
        if _dirty(held)
    }


def _open_cited(path: str, line: int | None) -> None:
    """Opens the file `path` a citation names, at its line where it names
    one (amendment 06 §2 item 6)."""
    if line:
        open_at(path, line)
    else:
        open_from_tree(path)


# the page's functions Matsya's column calls (`matsya_window.Actions`)
MATSYA_ACTIONS = matsya_window.Actions(
    folder=lambda: tab_folder.value,
    open_file=lambda path, line: _open_cited(path, line),
    open_copy=lambda path: open_returned(path),
    buffers=lambda: _matsya_buffers(),
    open_commit=lambda record: open_adoption_commit(record),
    source=lambda: source.value or (sources.value[0] if sources.value else None),
)


def _is_stage(path: str | None) -> bool:
    """Whether `path` names a stage file."""
    return path is not None and path.endswith(".bl")


def _counter(value: dict | None) -> int:
    """The next value of the counter `n` of a request record."""
    return (value or {}).get("n", 0) + 1


def _dirty(held: dict | None) -> bool:
    """Whether the buffer `held` differs from its file on disk."""
    return held is not None and _digest(held["text"]) != held["digest"]


def _dirty_paths() -> set:
    """The paths of the buffers that differ from their files."""
    return {path for path, held in buffers.value.items() if _dirty(held)}


def _newlines_as_loaded(text: str, loaded: str) -> str:
    """The editor's document `text` with the line endings of the `loaded`
    document: CodeMirror joins lines with LF whatever the file holds, so
    a file read with CRLF is given CRLF back (specification §2.2 rule 3:
    the application reformats nothing)."""
    return text.replace("\n", "\r\n") if "\r\n" in loaded and "\r\n" not in text else text


def _is_position(address: str, line: int | None) -> bool:
    """Whether `address` is a position, `<file>:<line>`, of the line `line`
    rather than the address of a block or a line of the file; a position
    repeats what the line and the column already print."""
    return line is not None and address.endswith(f":{line}")


def _rule_word(rule: str | None) -> str:
    """The word on screen for the package's rule `rule`: `RULE_WORDS`
    where it has one, the rule's own name otherwise."""
    return RULE_WORDS.get(rule, rule) if rule else ""


# --- the folder ---


def refresh_folder() -> None:
    """Reads the tree, git's summary, the checklist and the sources of
    the trellis (`recipe.model_sources`) of the tab's folder again."""
    tree.value = model.folder_tree(tab_folder.value)
    git_line.value = model.git_summary(tab_folder.value)
    read_checklist()
    sources.value = recipe.model_sources(tab_folder.value, tree.value)
    folder_read.value = True


def first_stage(entries: list) -> str | None:
    """The path of the first stage file of the tree `entries`, in the
    tree's order, folders first and their files before the next entry,
    none from a folder named `model.OUTPUT_FOLDER`, whose saved copies are
    models of their own (amendment 06 §2 item 21); None where the tree holds
    none."""
    for entry in entries:
        if entry["kind"] == "folder" and entry["name"] == model.OUTPUT_FOLDER:
            continue
        if entry["kind"] == "folder":
            found = first_stage(entry["children"])
            if found is not None:
                return found
        elif entry["role"] == "stage":
            return entry["path"]
    return None


def first_file() -> str | None:
    """The file the folder opens on (specification §2 and §3.1): the file of
    its first source of a trellis where it holds one, else its first stage
    file; None where it holds neither."""
    if sources.value:
        return sources.value[0].path
    return first_stage(tree.value)


def open_first() -> None:
    """Reads the folder and opens it (specification §2 and §3.1): its first
    file (`first_file`) as a click in the tree opens it, the trellis with the
    source's file open as text, or the first stage file with its view; a
    folder with neither leaves no file open, and the file region says what
    to add. A model's `declaration/` opened by itself, as the desktop
    application opens a folder chosen in its dialog, opens the model folder
    above it instead (`open_model_above`; AAS, M-D14), so that the recipe at
    `declaration/spec.yml` is read and the trellis is drawn."""
    refresh_folder()
    if open_path.value is not None:
        return
    above = recipe.model_of_declaration(tab_folder.value)
    if above is not None:
        open_model_above(str(above))
        return
    first = first_file()
    if first is not None:
        open_from_tree(first)


def toggle_folder(path: str) -> None:
    """Closes the folder `path` of the tree when it is open, and opens it
    when it is closed."""
    opened = open_folders.value
    if path in opened:
        open_folders.value = tuple(p for p in opened if p != path)
    else:
        open_folders.value = (*opened, path)


def open_folders_of(path: str) -> None:
    """Opens each folder of the tree on the path of the file `path`, so
    that the file's row is seen (R-D52); the other folders keep their
    state. A file outside the folder, `../portfolio-choice/...`, has no row
    and opens none."""
    parts = path.split("/")[:-1]
    if ".." in parts:
        return
    above = ["/".join(parts[:end]) for end in range(1, len(parts) + 1)]
    opened = open_folders.value
    open_folders.value = (*opened, *(folder for folder in above if folder not in opened))


def _clear_trellis() -> None:
    """Clears the trellis shown and what depends on it: the trellis, the
    outcome of its last reading, the digests of the files its watcher
    compares, the occurrence the head names, the node selected in the view,
    whose id would name a node of another trellis, the refusal of a change
    of the Recipe tab and its open row (design pass 11 §2), and the wide
    panel of the panel under the editor or
    of Details (L-D12), which are closed so that they
    do not reopen over a later source and window.vue reads no Escape for
    a panel that is not drawn, and the gesture of the trellis graph that
    waits, with the note, the sentence and the text of the last gesture
    (`_clear_gestures`). The caller holds LOOP_LOCK, under which
    `run_trellis` records an outcome (a new source, `show_source`; a folder
    opened in the tab, `open_model`)."""
    trellis_shown.value = None
    trellis_outcome.value = None
    trellis_seen.value = {}
    head.value = None
    selected.value = None
    region_wide.value = None
    choice_refusal.value = None
    recipe_open_stage.value = None
    _clear_gestures()


def _use_source(found: recipe.Source) -> None:
    """Makes `found` the tab's source of a trellis, the view as it stands. A
    new source forgets the occurrence the head named and the node selected,
    and the trellis, the outcome and the file digests of the source before,
    so that it shows `reading` and an empty view until its own reading
    stands, and no trellis, note or refusal of another source stands for
    it; and it clears the refusal of a change of the Recipe tab and closes
    the wide panels.
    For a new source, while the bar's text is empty or is the text the
    window itself last wrote there (`restriction_opening`), the window
    writes the source's opening text into the bar and applies it
    (`apply_restriction`), as a reader would, before the source is set:
    `periods 0–2`, as `trellis.opening_restriction` answers it, for a
    syntactic trellis of more than `trellis.OPEN_PERIODS_WHOLE` periods;
    the empty text, the whole trellis, for a shorter trellis and for a
    source the package refuses to read, whose reading reports the refusal.
    The source is read through the mapping of the tab's unsaved texts
    (`unsaved_texts`; spec 0.4 §3.1). `writing_opening` stands while the
    window writes that text, so that the change of restriction starts no
    reading of the source before. A text the reader wrote stays in the bar
    for the new source."""
    if source.value != found:
        text = restriction_text.value
        if not text.strip() or text == restriction_opening.value:
            try:
                syntactic = recipe.read_source(
                    tab_folder.value, found, trellis.texts_of(unsaved_texts())
                )
            except (ValueError, LookupError, TypeError, OSError):
                # the factory's refusals, FactoryError and ConstructionError
                # among the ValueErrors, and a file that cannot be read
                syntactic = None
            opening = None if syntactic is None else trellis.opening_restriction(syntactic)
            # applied before the source is set, so that the source's first
            # reading is under it
            writing_opening.value = True
            try:
                apply_restriction(opening or "")
                restriction_opening.value = opening or ""
            finally:
                writing_opening.value = False
        # under the lock with which `run_trellis` records an outcome, so that
        # a reading of the source before records nothing after the clearing
        with LOOP_LOCK:
            _clear_trellis()
            # the new source last, so that no render names it over a trellis
            # of the source before
            source.value = found


def show_source(found: recipe.Source) -> None:
    """Shows the trellis of the source `found` (specification §3.1): `found`
    made the tab's source (`_use_source`), and the trellis view, on the
    graph `backward` unless a graph of a trellis is shown."""
    _use_source(found)
    if view_mode.value != "trellis":
        view_mode.value = "trellis"
        selected.value = None
    if graph.value not in ("backward", "forward"):
        graph.value = "backward"


def show_stage() -> None:
    """Shows the view of the open stage file. Where the trellis view is
    left, a gesture of the trellis graph that waits is withdrawn
    (`withdraw_gesture`; brief rule 6), since the graph shown changes even
    where the stage's graph has the trellis graph's id, `forward`."""
    if view_mode.value != "stage":
        view_mode.value = "stage"
        selected.value = None
        withdraw_gesture()


def _bound_position(current: Shown | None):
    """The occurrence `(h, key)` the shown stage `current` is bound as in
    the recipe it was bound through: the head where it is one of the
    stage's positions there, else the first of them, as the breadcrumb
    names it (`navigation.breadcrumb`); None where the recipe holds no
    occurrence of the stage or no stage is shown."""
    if current is None or not current.positions:
        return None
    return head.value if head.value in current.positions else current.positions[0]


def choose_trellis() -> None:
    """The view tab `Trellis` of the graph's bar (`ViewSwitch`; unit K,
    K-D20; design pass 2 §4; design pass 8 §§4 and 6; R-D54, R-D56;
    amendment 02 ruling 3). From a stage's view it shows the trellis of
    the recipe the shown stage is bound through, the place the breadcrumb's
    recipe shows (`show_source`), or, where no stage is shown, of the
    source last shown or the folder's first, in the direction shown; the
    occurrence the stage is bound as (`_bound_position`) is drawn as
    `_draw_position` draws it, selected, and its period and layer opened in
    the view (`_ask`). While the trellis is shown it does nothing. The
    place left is recorded, so that ← returns to it (AMD-MI-002 §3 rule
    4)."""
    if view_mode.value == "trellis":
        return
    left = _place()
    current = shown.value
    bound = current.source if current is not None else None
    found = bound or source.value or (sources.value[0] if sources.value else None)
    if found is None:
        return
    # read before `show_source`, since a new source clears the head
    position = _bound_position(current) if bound is not None else None
    direction = direction_of(graph.value)
    show_source(found)
    switch_graph(direction)
    if position is not None:
        _draw_position(position)
        h, key = position
        selected.value = {"nodeId": f"periods[{h}]/{key}{LAYER_ID_ENDING}", "graphId": graph.value}
    _record(left)
    if position is not None:
        _ask(_place())


def choose_stage() -> None:
    """The view tab `Stage` of the graph's bar (`ViewSwitch`; unit K,
    K-D20; design pass 2 §4; design pass 8 §§4 and 6): while the trellis
    is shown and the editor holds a stage file, the view of that file
    (`show_stage`), no file opened and the editor unchanged; nothing
    otherwise. The place left is recorded, so that ← returns to the
    trellis (AMD-MI-002 §3 rule 4)."""
    if view_mode.value != "trellis" or not _is_stage(open_path.value):
        return
    left = _place()
    show_stage()
    _record(left)


def open_from_tree(path: str) -> None:
    """A click on a file of the tree (specification §2.1): a recipe, a
    trellis file, or the trellis file a recipe reads shows the trellis and
    opens the file as text; a stage file opens with its view, the head
    cleared, so that the stage is bound as its first occurrence in the
    tab's recipe, no position chosen (AMD-MI-002 §3 rule 5, A2-D6), and the
    stage file already open keeps its head, the position chosen, since a
    click on the open file changes nothing (`open_file`; ruling R55); any
    other file opens as text with the view unchanged. The place left is
    recorded (rule 4)."""
    left = _place()
    found = recipe.source_of(tab_folder.value, path, sources.value)
    if found is not None:
        show_source(found)
    elif _is_stage(path):
        if path != open_path.value:
            head.value = None
        show_stage()
    open_file(path)
    _record(left)


def show_recipe(found: recipe.Source) -> None:
    """A click on a recipe of the folder's list or on the recipe of the
    breadcrumb (AMD-MI-002 §3 rules 1 and 3): the trellis of the recipe
    `found` (`show_source`), the open file as it stands. The place left is
    recorded (rule 4)."""
    left = _place()
    show_source(found)
    _record(left)


def show_period(found: recipe.Source, position) -> None:
    """A click on the period of the breadcrumb (AMD-MI-002 §3 rule 3), whose
    stage is shown at `position`, `(h, key)`: the trellis of the recipe
    `found`, as `show_recipe` shows it, drawn as `_draw_position` draws
    that occurrence, with the layer of `periods[h]` selected and opened in
    the view (`_ask`). The place left is recorded (rule 4)."""
    left = _place()
    show_source(found)
    _draw_position(position)
    selected.value = {"nodeId": f"periods[{position[0]}]{LAYER_ID_ENDING}", "graphId": graph.value}
    _record(left)
    _ask(_place())


def _draw_position(position) -> None:
    """Draws the occurrence at `position`, `(h, key)`, which a link shows in
    the trellis view: where the standing restriction omits it, the
    restriction becomes `periods h` (the brief of AMD-MI-002, rule 6,
    decided). That text is recorded as the window's (`restriction_opening`),
    so that a new source writes its own opening text over it (ruling R39).
    A step back restores the restriction that stood before, since the place
    the link leaves holds it (rule 4), and records it as the window's where
    it is the opening text of that place's recipe or `periods h` of that
    place's position (`_restore`, rulings R57 and R59); a step forward to
    the place the link reached records `periods h` as the window's again."""
    h, key = position
    if not trellis.selects(restriction.value, h, key):
        apply_restriction(f"periods {h}")
        restriction_opening.value = f"periods {h}"


def choose_position(position) -> None:
    """A position chosen after the main bar's path (AMD-MI-002 §3 rule 5): the
    occurrence at `position`, `(h, key)`, becomes the head, and the open
    stage file is bound as it, which fixes the context as a double click on
    that occurrence fixes it (rule 2). The place left is recorded (rule
    4)."""
    left = _place()
    set_head(position)
    _record(left)


def bind_through(found: recipe.Source) -> None:
    """A recipe that the main bar names where the tab's recipe holds
    no occurrence of the open stage file (AMD-MI-002 §3 rule 5; the brief's
    rule 2): `found` becomes the tab's recipe (`_use_source`), which clears
    the head, so that the file is bound as its first occurrence there, and
    the stage's view stays. The place left is recorded (rule 4)."""
    left = _place()
    _use_source(found)
    _record(left)


def show_occurrence(found: recipe.Source, position) -> None:
    """A link of the rows `periods` and `also` of Details (AMD-MI-002 §3
    rule 6; unit K's decision K-D2): the trellis of the recipe `found`, as
    `show_recipe` shows it, drawn as `_draw_position` draws the occurrence
    at `position`, `(h, key)`, which becomes the head; its layer is
    selected and opened in the view with its period (`_ask`), as a step
    back from its stage shows it. The place left is recorded (rule 4)."""
    left = _place()
    show_source(found)
    _draw_position(position)
    set_head(position)
    h, key = position
    selected.value = {"nodeId": f"periods[{h}]/{key}{LAYER_ID_ENDING}", "graphId": graph.value}
    _record(left)
    _ask(_place())


# --- the history of places (AMD-MI-002 §3 rule 4) ---


def _place() -> navigation.Place:
    """The tab's place now: its view, its recipe, its restriction, its head,
    the file open in the editor or the file a switch is opening, the graph
    the view shows, and the node selected."""
    return navigation.Place(
        view=view_mode.value,
        recipe=source.value,
        restriction=restriction.value,
        position=head.value,
        file=switching.value or open_path.value,
        graph=graph.value,
        selected=selected.value,
    )


def _record(left: navigation.Place) -> None:
    """Records `left`, the place a handler left, in the tab's history where
    the handler moved the tab (`navigation.visit`). Such a move withdraws
    the place last asked of the view (`_ask`), which the tab has left."""
    recorded = navigation.visit(history.value, left, _place())
    if recorded is not history.value:
        history.value = recorded
        place_request.value = None


def _ask(place: navigation.Place) -> None:
    """Asks the view to show `place` once its collection is the place's own
    (`view_request`): its graph, its selected node and the layers that show
    it, under a number no request has carried."""
    place_request.value = {"place": place, "n": next(_place_numbers)}


def _is_window_text(place: navigation.Place, text: str) -> bool:
    """Whether `text`, the restriction of `place` restored, is a text the
    window writes at that place: `periods h` for the period h of the
    place's position, the text `_draw_position` writes for a link (ruling
    R59), or the opening text of the place's recipe, as `_use_source`
    writes it, `periods 0–2` or the empty text (ruling R57). The recipe's
    opening text is that of the syntactic trellis the trellis shown holds,
    where it is of that recipe, and otherwise that of the recipe read again
    (`recipe.read_source`), through the mapping of the tab's unsaved texts
    (`unsaved_texts`; spec 0.4 §3.1)."""
    if place.position is not None and text == f"periods {place.position[0]}":
        return True
    if place.recipe is None:
        return False
    held = trellis_shown.value
    if held is not None and held.source == place.recipe:
        syntactic = held.syntactic
    else:
        try:
            syntactic = recipe.read_source(
                tab_folder.value, place.recipe, trellis.texts_of(unsaved_texts())
            )
        except (ValueError, LookupError, TypeError, OSError):
            # the exceptions `_use_source` catches, for a source that opens
            # whole
            syntactic = None
    opening = None if syntactic is None else trellis.opening_restriction(syntactic)
    return text == (opening or "")


def _restore(place: navigation.Place) -> None:
    """Shows `place` again and records no place in the history (AMD-MI-002
    §3 rule 4). The view is asked first to show the place, its selected
    node shown open (`_ask`), so that the render in which the view's
    collection becomes the place's own gives the view the request with it,
    and the view lays the collection out once. Then the place's recipe,
    through `show_source`, which clears the head and the selection, where
    the place is a trellis view or its recipe is not the tab's; then its
    restriction, its head, its view, its graph, its selection and its file.
    A restriction restored is recorded as the window's text
    (`restriction_opening`) in two cases (`_is_window_text`): where it is
    the opening text the window writes for the place's recipe,
    `periods 0–2` or the empty text (ruling R57), and where it is
    `periods h` for the period h of the place's position, the text a link
    writes there (ruling R59). The next new source then writes its own
    opening text over it, as it would had the tab not left the place. Any
    other restriction restored leaves that record as it stands, so that a
    text the reader wrote stays in the bar for the next source."""
    _ask(place)
    if place.recipe is not None and (place.view == "trellis" or place.recipe != source.value):
        show_source(place.recipe)
    if place.restriction != restriction.value:
        text = place.restriction.text if place.restriction is not None else ""
        apply_restriction(text)
        if text != restriction_opening.value and _is_window_text(place, text):
            restriction_opening.value = text
    head.value = place.position
    if place.view == "stage":
        show_stage()
    switch_graph(place.graph)
    selected.value = place.selected
    if place.file is not None:
        open_file(place.file)


def go_back(data=None) -> None:
    """The button ← and the keys Alt+← (AMD-MI-002 §3 rule 4, A2-D4): shows
    again the last place behind, the place left put first ahead; nothing
    where no place stands behind. `data` is the window's event, which
    carries nothing."""
    stepped = navigation.back(history.value, _place())
    if stepped is None:
        return
    history.value, place = stepped
    _restore(place)


def go_forward(data=None) -> None:
    """The button → and the keys Alt+→ (AMD-MI-002 §3 rule 4, A2-D4): undoes
    a step back, showing again the first place ahead, the place left put
    last behind; nothing where no place stands ahead. `data` is the
    window's event, which carries nothing."""
    stepped = navigation.forward(history.value, _place())
    if stepped is None:
        return
    history.value, place = stepped
    _restore(place)


# --- the files and the buffers ---


def _load_locked(path: str, text: str, digest: str | None) -> None:
    """The body of `load_text`, run with LOOP_LOCK held: the buffer of
    `path` takes `text` with `digest` as the file's, the editor takes
    `text` as the document under a new document revision, and the choice
    closes last, so that the watcher, which acts only while no choice
    stands, never reads the buffer this replaces."""
    held = buffers.value.get(path) or {"revision": 0}
    buffers.value = {
        **buffers.value,
        path: {
            "text": text,
            "revision": held["revision"] + 1,
            "digest": digest,
            "document": text,
            "document_revision": next(_document_numbers),
        },
    }
    compare_open.value = False
    overwrite_pending.value = False
    conflict.value = None


def load_text(path: str, text: str, digest: str | None) -> None:
    """Puts `text` into the editor as the document of the file `path`,
    remembers `digest` as the file's, and gives the loop the text as the
    buffer."""
    with LOOP_LOCK:
        _load_locked(path, text, digest)


def _switch_to(path: str) -> None:
    """Makes `path` the open file: a buffer the tab already holds is given
    to the editor as it stands, unsaved text included, under a new
    document revision; a file opened for the first time is read from the
    disk. The view shows the last object of `path` that elaborated, and
    nothing while a stage file has none, so that no graph of another file
    stands for it; a file that is no stage keeps the view as it is. The
    selection of a stage's view and the cursor's block, line and column are
    cleared; the trellis view keeps its selection, and a choice that stood
    for the file left closes; the next save of that file meets it again
    when the disk still differs. A place asked of the file before it
    opened (`open_at`) is applied once it is open. The folders on the
    file's path open in the tree (`open_folders_of`; R-D52)."""
    # the trellis view's selection stays while the editor changes file
    if view_mode.value != "trellis":
        selected.value = None
    cursor_block.value = None
    cursor_line.value = None
    cursor_place.value = None
    block_nodes.value = []
    sheet_open.value = None
    switching.value = None
    # the panel under the editor stands on its four tabs for a stage file
    # and on its Recipe tab for the recipe the trellis is read under, so its
    # wide panel closes where the file opened shows the other or none,
    # leaving no ground over the window (unit L's final judgment, §6 item
    # 11; design pass 9 §2)
    if region_wide.value in ("types", "recipe") and region_wide.value != inspector_content(path):
        region_wide.value = None
    open_folders_of(path)
    with LOOP_LOCK:
        held = buffers.value.get(path)
        if held is None:
            found = model.read_file(tab_folder.value, path)
            open_path.value = path
            _load_locked(path, found.text, found.digest)
        else:
            open_path.value = path
            buffers.value = {
                **buffers.value,
                path: {
                    **held,
                    "document": held["text"],
                    "document_revision": next(_document_numbers),
                },
            }
            compare_open.value = False
            overwrite_pending.value = False
            conflict.value = None
        existing = results.value.get(path)
        if existing is not None and existing["shown"] is not None:
            _show(existing["shown"])
        elif _is_stage(path):
            shown.value = None
            # the trellis view's mark is the trellis reading's, cleared by the
            # view once it has drawn the trellis
            if view_mode.value == "stage":
                drawing.value = False
    target = pending_goto.value
    if target is not None and target["path"] == path:
        pending_goto.value = None
        goto_line(target["line"], target["column"], target.get("end"))


def open_file(path: str) -> None:
    """Opens the file at `path`, relative to the folder, in the editor. The
    open file's document is first read back from the editor through a
    flush request, so that typing within the last pause is in its buffer
    before the editor's text is replaced; `on_change` then completes the
    switch. The file asked for last is the one the editor opens, since a
    step of the history may be asked while a switch still waits for the
    editor's answer (AMD-MI-002 §3 rule 4): a click on the open file
    withdraws such a switch to another file and otherwise changes nothing,
    and a place asked of another file than `path` (`pending_goto`) is
    withdrawn with its switch."""
    requested = desktop_pending.value
    if requested is not None and requested["file"] != path:
        desktop_pending.value = None
    target = pending_goto.value
    if target is not None and target["path"] != path:
        pending_goto.value = None
    if path == open_path.value:
        switching.value = None
        return
    if open_path.value is None:
        _switch_to(path)
        return
    switching.value = path
    flush_request.value = flush_request.value + 1


def close_file(path: str) -> None:
    """The control `×` of the tab of `path` (R-D53; amendment 02 rulings 1
    and 2): closes the tab where its buffer holds no unsaved text
    (`_close`). The open file's document is first read back from the
    editor through a flush request, as `open_file` reads it, so that typing
    within the last pause counts as unsaved; `on_change` then completes the
    close. Another file's buffer holds the document the editor gave back
    when it left that file, and closes at once."""
    if path != open_path.value:
        _close(path)
        return
    closing.value = path
    flush_request.value = flush_request.value + 1


def _close(path: str) -> None:
    """Closes the tab of `path` where its buffer holds no unsaved text
    (`_dirty`), so that nothing unsaved is lost (R-D53). Where the file is
    the open one, the tab to its left is opened, or the tab to its right
    where it stood first, as a click on that tab opens it (`_switch_to`);
    with no other tab, no file is open and the view keeps what it shows.
    The buffer and the loop's result of the file then leave the tab's
    state, as `_reload_held` drops them, so that the file's next opening
    reads the disk. The places of the history that name the file stay,
    and a step back to one opens the file from the disk again
    (amendment 02 ruling 2)."""
    held = buffers.value.get(path)
    if held is None or _dirty(held):
        return
    order = list(buffers.value)
    at = order.index(path)
    others = order[:at] + order[at + 1 :]
    if path == open_path.value:
        if others:
            _switch_to(others[at - 1] if at else others[0])
        else:
            # the state a switch clears, with no file to switch to
            if view_mode.value != "trellis":
                selected.value = None
            cursor_block.value = None
            cursor_line.value = None
            cursor_place.value = None
            block_nodes.value = []
            sheet_open.value = None
            switching.value = None
            open_path.value = None
            # no file open, no BellmanType panel (unit L's final judgment,
            # §6 item 11)
            if region_wide.value == "types":
                region_wide.value = None
    with LOOP_LOCK:
        buffers.value = {other: buffers.value[other] for other in buffers.value if other != path}
        results.value = {other: found for other, found in results.value.items() if other != path}


# --- the loop ---


def _diagnostic_record(diagnostic: model.Diagnostic) -> dict:
    """The record the editor's setDiagnostics takes for one refusal, its
    message the hover of the refusal's underline, with its paths printed
    from the folder as the list under the error mark prints it
    (`folder_relative`; K-D11)."""
    return {
        "line": diagnostic.line,
        "column": diagnostic.column,
        "end_line": diagnostic.end_line,
        "end_column": diagnostic.end_column,
        "message": folder_relative(diagnostic.message),
        "severity": "error",
    }


def _refusal_record(diagnostic: model.Diagnostic) -> dict:
    """The record the panel shows for one refusal of the text."""
    return {
        "message": diagnostic.message,
        "rule": diagnostic.rule,
        "address": diagnostic.address,
        "line": diagnostic.line,
        "column": diagnostic.column,
        "advice": diagnostic.advice,
        "direction": None,
    }


def _refusal_sentence(refusal: dict) -> str:
    """The sentence of one refusal record of the loop as the list under the
    error mark prints it (`standing_refusals`): its message, then on a line
    of its own the words it says to write, where it gives them."""
    advice = refusal.get("advice")
    return f"{refusal['message']}\n{advice}" if advice else refusal["message"]


def _direction_records(direction: str, refusal: dict) -> tuple[dict, dict | None]:
    """The panel's record and the editor's diagnostic of the refused
    builders graph of `direction` (`model.refused_directions`); the
    diagnostic is None where the refusal names no line, and carries the
    severity `warning`, since the file may be correct under the rule
    `not-constructed`, and its message has its paths printed from the
    folder (`folder_relative`; K-D11). The panel's record keeps the
    package's message, which `standing_refusals` compares."""
    record = {
        "message": refusal["message"],
        "rule": refusal["rule"],
        "address": refusal["address"],
        "line": refusal["line"],
        "column": refusal["column"],
        "advice": None,
        "direction": direction,
    }
    if refusal["line"] is None:
        return record, None
    diagnostic = {
        "line": refusal["line"],
        "column": refusal["column"],
        "end_line": refusal["end_line"],
        "end_column": refusal["end_column"],
        "message": folder_relative(refusal["message"]),
        "severity": "warning",
    }
    return record, diagnostic


def _spans_or_none(text: str, origin: str) -> dict | None:
    """The block spans of `text`, the package's `source_spans`; None where
    the package refuses the text."""
    try:
        return source_spans(text, origin)
    except ValueError:
        return None


def _source_digests(paths: list) -> dict:
    """The SHA-256 digest of each file of `paths`, keyed by the path as a
    string; a file that cannot be read is left out."""
    digests = {}
    for path in paths:
        try:
            digests[str(path)] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError:
            continue
    return digests


def elaborate(path: str, text: str, revision: int) -> tuple[Outcome, Shown | None]:
    """The outcome of elaborating the buffer `text` of the file `path`, and
    the new `Shown` when it elaborated: `model.elaborate_buffer` with the
    origin the occurrence's record writes (`recipe.find_occurrence`: the
    occurrence the head names where it is one of the file's, else the
    file's first), then the bindings of that occurrence
    (`recipe.bind_occurrence`), the collection, the counts, the refused
    directions, the layers, the block spans, the digests of the inputs, and
    the file's positions in each source of the folder, the tab's recipe
    first (`recipe.uses_of`). Every source is read through the mapping of
    the tab's unsaved texts (`unsaved_texts`; spec 0.4 §3.1). The seconds
    are those of the whole loop. An exception the package raises where a
    refusal was due is the outcome's one refusal, under the rule
    `package-exception`, at the line of the address its message names
    (`model.exception_diagnostic`), and is written with its traceback to the
    page's log (`LOG`; unit L, Task 21; defect 18 of the UX simulation)."""
    started = time.perf_counter()
    texts = trellis.texts_of(unsaved_texts())
    found = recipe.find_occurrence(tab_folder.value, source.value, path, head.value, texts)
    origin = found.origin
    try:
        elaboration = model.elaborate_buffer(text, origin, revision)
    except Exception as error:  # the package raised something other than a refusal
        LOG.error(model.EXCEPTION_LOGGED, path, exc_info=error)
        spans = _spans_or_none(text, origin)
        # the exception under its rule, at the line its message names, which
        # the editor marks as it marks a refusal (unit L, Task 21)
        refused = model.exception_diagnostic(error, path, spans)
        return (
            Outcome(
                path,
                revision,
                "parsed, refused" if spans is not None else "not parsed",
                {},
                time.perf_counter() - started,
                {"text": _digest(text)},
                None,
                [_diagnostic_record(refused)] if refused.line is not None else [],
                [_refusal_record(refused)],
                True,
                None,
                spans,
            ),
            None,
        )
    if elaboration.stage is None:
        # the spans of the refused text, so that the block links follow
        # the edits since the last elaborated revision; None when the
        # parser refuses the text
        spans = _spans_or_none(text, origin)
        diagnostics = [
            _diagnostic_record(d) for d in elaboration.diagnostics if d.line is not None
        ]
        return (
            Outcome(
                path,
                revision,
                model.loop_state(elaboration),
                elaboration.counts,
                time.perf_counter() - started,
                {"text": elaboration.digest},
                None,
                diagnostics,
                [_refusal_record(d) for d in elaboration.diagnostics],
                True,
                None,
                spans,
            ),
            None,
        )
    bound = recipe.bind_occurrence(elaboration.stage, found)
    stage = bound.stage
    collection = model.collection(stage)
    declared = model.collection(stage, operative=False) if model.two_levels(stage) else None
    counts = model.counts(stage, collection)
    state = model.loop_state(elaboration)
    refused = model.refused_directions(stage)
    layers = {
        entry["id"]: list(layers_to_open(collection, entry["id"], LAYER_DEPTH))
        for entry in collection["graphs"]
    }
    spans = source_spans(text, origin)
    digests = model.input_digests(stage, text)
    # the watcher compares the source, the trellis file it reads and the
    # binding sources of the occurrence's record (`recipe.watched_files`),
    # so that a slot filled in a recipe binds the shown stage anew
    # (specification §2.2 rule 1)
    source_digests = _source_digests(recipe.watched_files(tab_folder.value, found, texts))
    # where the file is used, the source it is bound through first, so that
    # the panel lists the tab's recipe first (AMD-MI-002 §3 rule 6)
    others = [each for each in sources.value if each != found.source]
    ordered = [found.source, *others] if found.source is not None else others
    uses = tuple(recipe.uses_of(tab_folder.value, ordered, path, texts))
    version = "bound" if set(digests) - {"text"} else "symbolic"
    refusals, diagnostics = [], []
    for direction, refusal in refused.items():
        record, diagnostic = _direction_records(direction, refusal)
        refusals.append(record)
        if diagnostic is not None:
            diagnostics.append(diagnostic)
    seconds = time.perf_counter() - started
    new_shown = Shown(
        path=path,
        text=text,
        revision=revision,
        stage=stage,
        collection=collection,
        layers=layers,
        spans=spans,
        counts=counts,
        seconds=seconds,
        digest=elaboration.digest,
        notes=bound.notes,
        occurrence=bound.occurrence,
        version=version,
        digests=digests,
        source_digests=source_digests,
        position=bound.position,
        record=bound.record,
        source=found.source,
        positions=found.positions,
        uses=uses,
        refusal=found.refusal,
        declared=declared,
    )
    result = Outcome(
        path,
        revision,
        state,
        counts,
        seconds,
        digests,
        version,
        diagnostics,
        refusals,
        False,
        None,
        spans,
    )
    return result, new_shown


def _delay_for_the_tests(text: str) -> None:
    """The tests' hook (specification §12, A1 item 5): when the environment
    variable BELLMAN_WORKBENCH_DELAY_MARKER names a text and `text` holds it,
    the loop waits DELAY_SECONDS before writing its result, so that a test
    of the discard knows the marked revision's result finishes last."""
    if DELAY_MARKER and DELAY_MARKER in text:
        time.sleep(DELAY_SECONDS)


def _show(new_shown: Shown) -> None:
    """Makes `new_shown` the stage the view draws, with LOOP_LOCK held; the
    view is marked as drawing only when the collection differs from the
    one shown, since an equal dictionary is not sent to the browser and no
    processed event would clear the mark. A stage's result marks the view
    only while the stage's view is shown: with the trellis shown, the
    browser holds the trellis's collection, so a stage's collection is not
    sent and no processed event would clear the mark."""
    previous = shown.value
    # the mark is set before the view is given the collection, so that the
    # view's processed event, which follows it, clears the mark
    if view_mode.value == "stage":
        drawing.value = previous is None or level_collection(previous) != level_collection(
            new_shown
        )
    shown.value = new_shown


def run_loop() -> Outcome | None:
    """The task of the loop: elaborates the buffer of the open file and,
    when that buffer is still at the revision elaborated, records the
    result for the file and, on success, makes the stage the one the view
    draws; the result of an older revision is dropped. A result the tab
    already holds for the revision is answered without elaborating. The
    comparison and the writes run under LOOP_LOCK, which every new
    revision of a buffer also takes, so that the buffer is given no newer
    revision between them. A file that is no stage is opened as text and
    the view stays. The result is held per revision, binding count, source
    and head."""
    path = open_path.value
    if path is None:
        return None
    held = buffers.value.get(path)
    if held is None:
        return None
    revision = held["revision"]
    rebound = (rebind.value, source.value, head.value)
    existing = results.value.get(path)
    if existing is not None and existing["revision"] == revision and existing["rebind"] == rebound:
        with LOOP_LOCK:
            if (
                open_path.value == path
                and existing["shown"] is not None
                and shown.value is not existing["shown"]
            ):
                _show(existing["shown"])
        return existing["outcome"]
    if _is_stage(path):
        result, new_shown = elaborate(path, held["text"], revision)
    else:
        result = Outcome(
            path,
            revision,
            None,
            {},
            0.0,
            {"text": _digest(held["text"])},
            None,
            [],
            [],
            False,
            f"{path} opened as text",
        )
        new_shown = None
    _delay_for_the_tests(held["text"])
    with LOOP_LOCK:
        current = buffers.value.get(path)
        if (
            current is None
            or current["revision"] != revision
            or (rebind.value, source.value, head.value) != rebound
        ):
            return result
        results.value = {
            **results.value,
            path: {"outcome": result, "shown": new_shown, "revision": revision, "rebind": rebound},
        }
        if new_shown is not None and open_path.value == path:
            _show(new_shown)
    return result


def run_trellis(
    values: tuple[recipe.Source | None, trellis.Restriction | None, int, tuple] | None = None,
) -> trellis.TrellisOutcome | None:
    """The task of the trellis (specification §3.1): reads the trellis of the
    source shown, with the trellis shown before as its `previous`, so that a
    changed stage text alone is constructed again, restricted as the view's
    bar asks, and given the tab's unsaved buffers (`unsaved_texts`), whose
    texts the package reads in place of the recipe, the trellis file and
    the period files (spec 0.4 §3.1); when the source, the restriction, the
    watcher's count and the unsaved inputs (`unsaved_inputs`) that stand at
    its end are the ones it read, records the outcome with the digests the
    watcher compares, those of the texts as the reading read them
    (`trellis.show_trellis`), and with the moment it answered,
    which orders its refusals in the list under the error mark (AMD-MI-002
    §6a rule 1), and makes a new trellis the one the view draws, a trellis
    of another elaboration number withdrawing a gesture of the trellis
    graph that waits (`withdraw_gesture`; brief rule 6). A refused
    reading keeps the last trellis, dimmed; a restriction the package
    refuses is drawn as the one it accepted last for the source, or as the
    whole trellis. The package raising something other than a refusal is
    shown as a refusal of the reading, in the source's file under the rule
    `package-exception` (`model.exception_diagnostic`) and written with its
    traceback to the page's log (`LOG`; unit L, Task 21), with the digests
    of the files `trellis.files_before_reading` names, taken once it has
    raised. Once
    the outcome is recorded, and outside the lock, the binding of a
    reading that was not refused and was given no trellis of the same
    source is kept on disk for a later start of the Workbench
    (`trellis.keep_binding`); an outcome not recorded keeps nothing.

    The source, the restriction, the count and the unsaved inputs it reads
    are `values` where they are given, and otherwise the values that stand
    when it runs. The page's effect calls the task with the values of its
    render as the call's argument, which the task's thread passes to this
    function, so that each run reads its own render's values: the first
    render's values name no source, since an effect of that render sets the
    folder's source, and its run reads nothing; the next render's run reads
    the trellis once. A change of an unsaved buffer of a file the last
    outcome names, which the reading can take, changes the fourth value and
    so starts the task again (brief rule 5)."""
    chosen, asked, rebuilt, inputs = (
        values
        if values is not None
        else (source.value, restriction.value, trellis_rebuild.value, unsaved_inputs())
    )
    if chosen is None:
        return None
    held = trellis_shown.value
    unsaved = unsaved_texts()
    try:
        # the trellis's initial diagrams are drawn while the view shows one
        # of them, having been computed when it was chosen (S-D30)
        outcome = trellis.show_trellis(
            tab_folder.value, chosen, asked, held, unsaved, initial=graph.value in INITIAL_IDS.values()
        )
    except Exception as error:  # the package raised something other than a refusal
        LOG.error(model.EXCEPTION_LOGGED, chosen.path, exc_info=error)
        named = trellis.files_before_reading(tab_folder.value, chosen, held)
        # the source, the first file named, compared with its buffer
        taken = (str(named[0]),)
        # the exception under its rule, in the source's file, whose text has
        # no span table (unit L, Task 21)
        refusal = model.exception_diagnostic(error, taken[0])
        outcome = trellis.TrellisOutcome(
            None,
            refusal,
            None,
            0.0,
            trellis.file_digests(named, _texts_within(unsaved, taken)),
            takeable=taken,
        )
    outcome = outcome._replace(made=time.monotonic())
    with LOOP_LOCK:
        standing = (source.value, restriction.value, trellis_rebuild.value, unsaved_inputs())
        if standing != (chosen, asked, rebuilt, inputs):
            return outcome
        trellis_outcome.value = outcome
        trellis_seen.value = outcome.files
        if outcome.shown is not None:
            previous = trellis_shown.value
            # the mark is set before the view is given the collection, so that
            # the view's processed event, which follows it, clears the mark
            if view_mode.value == "trellis":
                drawing.value = bool(outcome.shown.collection["graphs"]) and (
                    previous is None or previous.collection != outcome.shown.collection
                )
            if previous is None or previous.number != outcome.shown.number:
                withdraw_gesture()
            trellis_shown.value = outcome.shown
    # a reading begun before `Initial` was chosen answers without the
    # diagrams the view now shows: they are computed once more, outside
    # the lock, the cached views making it cheap (the acceptance's F1;
    # S-D31)
    if (
        outcome.shown is not None
        and graph.value in INITIAL_IDS.values()
        and not trellis.holds_initial_diagrams(outcome.shown)
    ):
        hold_initial_diagrams()
    # outside the lock, so that no other task waits for the write
    trellis.keep_binding(outcome.shown, held)
    return outcome


def _trellis_stale() -> bool:
    """Whether the trellis view is dimmed: the last reading was refused."""
    outcome = trellis_outcome.value
    return outcome is not None and outcome.refusal is not None


def _watch_trellis() -> None:
    """Raises `trellis_rebuild` once per state of the files `trellis_seen`
    names, those of the trellis's last reading, read or refused, when one
    differs from its digest there, and records the fresh digests in its
    place (specification §3.1: the trellis re-elaborates when any file the
    model reads is saved, by the Workbench or by another program). Each file
    the last outcome can take from a buffer is compared by the text of its
    unsaved buffer where the tab holds one, the effective text, and every
    other file, a stage or binding file among them, on disk (spec 0.4 §3.3;
    ruling J-P2), so that a buffer the reading took is not found different
    from its file at every tick. The files are read outside LOOP_LOCK; the
    comparison with the digests that stand and the action run under it."""
    seen = trellis_seen.value
    if not seen:
        return
    outcome = trellis_outcome.value
    takeable = outcome.takeable if outcome is not None else ()
    fresh = trellis.file_digests(seen, _texts_within(unsaved_texts(), takeable))
    if fresh == seen:
        return
    with LOOP_LOCK:
        # a reading or a new source has recorded digests of its own meanwhile
        if trellis_seen.value != seen:
            return
        trellis_seen.value = fresh
        trellis_rebuild.value = trellis_rebuild.value + 1


def apply_restriction(text: str | None) -> None:
    """The restriction chosen from the menu of the view's bar or typed at its
    foot (specification §3.1; unit K, K-D17): parsed by
    `trellis.parse_restriction` and given to the trellis's loop; a text the
    parser refuses keeps the view and the restriction as they stand, its
    refusal recorded with its moment (`restriction_refusal`): the list
    under the error mark holds its sentence, and the bar's select is marked
    (AMD-MI-002 §6a rule 1); an empty text shows the whole trellis. The
    restriction is the tab's and is written nowhere. A restriction other than
    the one that stands removes from the last outcome the package's sentence
    refusing the one before, and withdraws a gesture of the trellis graph
    that waits (`withdraw_gesture`)."""
    restriction_text.value = text or ""
    try:
        parsed = trellis.parse_restriction(restriction_text.value)
    except ValueError as refusal:
        restriction_refusal.value = {"sentence": str(refusal), "made": time.monotonic()}
        return
    if parsed != restriction.value:
        restriction.value = parsed
        withdraw_gesture()
        # under the lock with which `run_trellis` records an outcome, so that
        # a reading under the restriction before records nothing after the
        # clearing
        with LOOP_LOCK:
            outcome = trellis_outcome.value
            if outcome is not None and outcome.restricted is not None:
                trellis_outcome.value = outcome._replace(restricted=None)
    # the parser's sentence cleared last, so that no render shows in its place
    # the package's sentence refusing the restriction before
    restriction_refusal.value = None


# --- the watcher of the files on disk ---


def watch(cancel: threading.Event) -> None:
    """Every WATCH_SECONDS compares the digest of the open file on disk
    with the remembered one: a changed file replaces a clean buffer
    silently and raises the choice for a buffer with unsaved changes
    (specification §2.2 rule 3); and compares the digest of each binding
    source the shown object's provenance names with the one read when it
    elaborated, and raises `rebind` when one differs, once per state of
    the sources, so that the open buffer is bound again (rule 1) and the
    loop that answers is not superseded while it runs; and every
    WATCH_SECONDS the files of the trellis's last reading (`_watch_trellis`).
    It stops when `cancel` is set. The
    files are read outside LOOP_LOCK; the comparison and the action run
    under it, after a check that the open file and the absence of a choice
    still hold, so that a reload or a save in between is not undone."""
    while not cancel.wait(WATCH_SECONDS):
        _watch_trellis()
        path = open_path.value
        if path is None or conflict.value is not None:
            continue
        try:
            found = model.read_file(tab_folder.value, path)
        except OSError:
            continue
        current_shown = shown.value
        sources_changed = False
        if current_shown is not None and current_shown.path == path:
            fresh = _source_digests(current_shown.source_digests)
            sources_changed = (
                fresh != current_shown.source_digests and fresh != rebind_sources.value
            )
        with LOOP_LOCK:
            if open_path.value != path or conflict.value is not None:
                continue
            held = buffers.value.get(path)
            if held is None:
                continue
            if found.digest != held["digest"]:
                if _digest(held["text"]) == held["digest"]:
                    _load_locked(path, found.text, found.digest)
                else:
                    conflict.value = {
                        "reason": "the file changed on disk",
                        "disk_text": found.text,
                        "disk_digest": found.digest,
                        "buffer_text": held["text"],
                        "made": time.monotonic(),
                    }
            elif sources_changed:
                rebind_sources.value = fresh
                rebind.value = rebind.value + 1


# --- the handlers of the components' events ---


def _event_is_current(data: dict) -> bool:
    """Whether an event of the editor names the open file's document at its
    current revision (specification §2.2 rule 1): an event of another
    file, or of an older document of the open file, is dropped."""
    path = data.get("path")
    held = buffers.value.get(path) if path is not None else None
    return (
        held is not None
        and path == open_path.value
        and data.get("revision") == held["document_revision"]
    )


def on_change(data: dict) -> None:
    """The editor's document after a pause, or on a flush request: the
    loop's next buffer of the open file, when the event names the open
    file's document; a text equal to the buffer's adds no revision; the
    checklist is read again from the buffers (`read_checklist`). A
    switch waiting on the flush is then completed, then a close waiting on
    it (`close_file`), which an event of an older document of the file
    withdraws, and then a gesture of the trellis graph waiting for the
    editor's text continues (`continue_gesture`)."""
    current = _event_is_current(data)
    if current:
        path = data["path"]
        with LOOP_LOCK:
            held = buffers.value[path]
            text = _newlines_as_loaded(data["text"], held["document"])
            if text != held["text"]:
                buffers.value = {
                    **buffers.value,
                    path: {**held, "text": text, "revision": held["revision"] + 1},
                }
        read_checklist()
    if switching.value is not None and data.get("path") == open_path.value:
        _switch_to(switching.value)
    if closing.value is not None and data.get("path") == closing.value:
        closing.value = None
        if current:
            _close(data["path"])
    continue_gesture("change")


def on_save(data: dict) -> None:
    """The editor's current document, on Mod-s, the save button or the
    overwrite choice: the loop takes it at once and the file is written
    when its digest on disk is the remembered one, or the disk's own when
    the overwrite was chosen; otherwise the choice is raised. A save that
    writes the file clears the status line's note of the last gesture of
    the trellis graph (`gesture_note`; J-D20 as unit K, Task 13 amends it),
    and deletes the files a removal or the tree's `remove` listed that no
    file of the folder then names, the status line's note then naming them
    (`_delete_on_save`; unit L, Task 25). An event of another document is
    dropped. A file within a saved copy of a job's returned files is not
    written, and the reason stands in the list under the error mark with
    no choice to overwrite (`model.read_only`; amendment 06 §2 item 21)."""
    if not _event_is_current(data):
        return
    path = data["path"]
    refusal = model.read_only(tab_folder.value, path)
    if refusal is not None:
        gesture_refusal.value = {
            "sentence": refusal, "file": path, "line": None, "made": time.monotonic()
        }
        return
    held = buffers.value[path]
    text = _newlines_as_loaded(data["text"], held["document"])
    if overwrite_pending.value and conflict.value is not None:
        expected = conflict.value["disk_digest"] or None
    else:
        expected = held["digest"]
    overwrite_pending.value = False
    result = model.save_file(tab_folder.value, path, text, expected)
    digest = result.digest if result.saved else held["digest"]
    with LOOP_LOCK:
        held = buffers.value[path]
        buffers.value = {
            **buffers.value,
            path: {**held, "text": text, "revision": held["revision"] + 1, "digest": digest},
        }
        if result.saved:
            compare_open.value = False
            conflict.value = None
            gesture_note.value = None
        else:
            conflict.value = {
                "reason": result.reason,
                "disk_text": result.text,
                "disk_digest": result.digest,
                "buffer_text": text,
                "made": time.monotonic(),
            }
    if result.saved:
        note = _delete_on_save()
        if note is not None:
            gesture_note.value = {"sentence": note, "made": time.monotonic()}
        refresh_folder()


def _block_of(current: Shown | None, graph_id: str, node_id: str) -> str:
    """The block of a node or a layer of the view: the package's `node_place`
    on the shown collection; the empty text where nothing is shown, and
    where the shown collection holds no such graph or node, as for a
    selection whose node the last edit removed."""
    if current is None:
        return ""
    try:
        return node_place(level_collection(current), graph_id, node_id).block
    except (KeyError, ValueError):
        return ""


def _result_of(path: str | None) -> Outcome | None:
    """The loop's outcome for the file `path`, None where none is held."""
    found = results.value.get(path) if path is not None else None
    return found["outcome"] if found is not None else None


def _spans_of_the_text(current: Shown) -> dict | None:
    """The block spans that match the editor's text: those of the last
    outcome when its revision is at least the shown one's (a refusal that
    stands has spans of its own text, or None when the parser refused it,
    which disables the block links), else the shown object's; None when
    the open file is not the shown object's, since the spans of one file
    say nothing of the lines of another."""
    result = _result_of(open_path.value)
    if result is None or result.path != current.path:
        return None
    if result.revision >= current.revision:
        return result.spans
    return current.spans


def goto_line(
    line: int, column: int = 1, end: tuple[int, int | None] | None = None, focus: bool = False
) -> None:
    """Moves the editor's cursor to `line` and `column` of the editor's
    text, counted from one in code points, and gives the editor the focus;
    where `end`, `(line, column)`, is given, the editor selects the text
    from there to `end`, to the end of that line where its column is None,
    and the focus stays where it is unless `focus` is true, so that a key
    the reader presses next in the graph acts there and not on the selected
    text (J-D40; amendment 02, rulings 9 and 12)."""
    request = {"line": line, "column": column, "n": _counter(goto_request.value)}
    if end is not None:
        request.update(end_line=end[0], end_column=end[1], focus=focus)
    goto_request.value = request


def goto_block(block: str) -> None:
    """Moves the editor's cursor to the header line of `block` of the
    editor's text, and records that block as the cursor's, so that the
    cursor event that follows selects nothing anew."""
    current = shown.value
    if current is None:
        return
    spans = _spans_of_the_text(current)
    if spans is None:
        return
    span = spans.get(block)
    if span is None:
        return
    cursor_block.value = block
    cursor_line.value = span.line
    graph_id = (selected.value or {}).get("graphId", graph.value)
    block_nodes.value = model.nodes_of_block(level_collection(current), graph_id, block)
    goto_line(span.line, 1)


def _open_at(path: str, line: int, column: int = 1, end: tuple[int, int] | None = None) -> None:
    """The body of `open_at`, which records no place, for a handler that
    records its own (`open_occurrence`). In the open file the cursor moves
    at once, after `open_file` has withdrawn a switch to another file that
    still waits for the editor's answer; `end` selects the text up to it
    (`goto_line`)."""
    if path == open_path.value:
        open_file(path)
        goto_line(line, column, end)
        return
    pending_goto.value = {"path": path, "line": line, "column": column, "end": end}
    open_file(path)


def open_at(path: str, line: int, column: int = 1, end: tuple[int, int] | None = None) -> None:
    """Opens the file `path` of the tab's folder with the editor's cursor
    at `line` and `column`, counted from one, the text up to `end` selected
    where it is given: at once where the file is open, and otherwise once
    the switch, which first reads back the open file's typing, has opened it
    (`_switch_to`). Opening another file records the place left (AMD-MI-002
    §3 rule 4); a move within the open file records nothing."""
    left = _place()
    _open_at(path, line, column, end)
    _record(left)


def on_desktop_open(data: dict | None) -> None:
    """Open an external request without discarding unsaved buffers."""
    if data is None:
        open_first()
        return
    try:
        folder = tab_folder.value.root
        if isinstance(data, dict) and "folder" in data:
            requested_folder = data["folder"]
            requested = None
            if isinstance(requested_folder, str):
                requested = Path(requested_folder).resolve()
            # a link that names the model's declaration/, the folder the
            # window was opened on before the page opened the model folder
            # above it (`open_first`; AAS, M-D14), names the same file from
            # the model folder
            declaration = (folder / model.FACTORY_FOLDER).resolve()
            if requested == declaration and isinstance(data.get("file"), str):
                inside = f"{model.FACTORY_FOLDER}/{data['file']}"
                data = {**data, "folder": str(folder), "file": inside}
                requested = folder
            if requested != folder:
                raise ValueError("This window changed model folders. Open the link again.")
        request = desktop.navigation_request(folder, data)
        if not folder_read.value:
            refresh_folder()
        desktop_pending.value = request
        desktop_refusal.value = None
        if _is_stage(request["file"]):
            show_stage()
        open_at(request["file"], request["line"])
    except (OSError, ValueError) as error:
        desktop_pending.value = None
        desktop_refusal.value = {"sentence": str(error), "made": time.monotonic()}
        if open_path.value is None:
            open_first()


def apply_desktop_request() -> None:
    """Select the requested block after its current text has elaborated."""
    request = desktop_pending.value
    if request is None or request["file"] != open_path.value:
        return
    held = buffers.value.get(request["file"])
    result = _result_of(request["file"])
    if held is None or result is None or result.revision != held["revision"]:
        return
    current = shown.value
    if _is_stage(request["file"]) and not result.stale:
        if current is None or current.path != request["file"] or drawing.value:
            return
    desktop_pending.value = None
    goto_line(request["line"])
    if not _is_stage(request["file"]) or result.stale:
        return
    cursor_block.value = None
    on_cursor(
        {
            "path": request["file"],
            "revision": held["document_revision"],
            "line": request["line"],
            "column": 1,
        }
    )
    if request["box"] is not None:
        for entry in level_collection(current)["graphs"]:
            if any(node["id"] == request["box"] for node in entry["nodes"]):
                switch_graph(entry["id"])
                select_request.value = {
                    "nodeId": request["box"],
                    "graphId": entry["id"],
                    "n": _counter(select_request.value),
                }
                return
        desktop_refusal.value = {
            "sentence": f"The requested box does not exist: {request['box']}",
            "made": time.monotonic(),
        }


def open_external_editor(path: str, line: int) -> None:
    """Open a Details source line in the configured external editor."""
    try:
        desktop.open_in_editor(
            tab_folder.value.root, path, line, os.environ.get(desktop.EDITOR_VARIABLE, "")
        )
        desktop_refusal.value = None
    except (OSError, ValueError) as error:
        desktop_refusal.value = {"sentence": str(error), "made": time.monotonic()}


def set_head(position) -> None:
    """Makes the occurrence at `position`, `(h, key)`, the head, which the
    main bar's path names (specification §3.2); an open stage file that is
    one of that occurrence's is bound as it again."""
    head.value = tuple(position)


def open_occurrence(position, block: str | None = None) -> None:
    """Makes the occurrence at `position` the head and opens its stage file
    in the editor with the stage's view, the stage bound as that occurrence
    (specification §3.1: the stage view of the head's occurrence and the
    trellis's occurrence present one position); at the header of `block`
    where one is given. A file the trellis reads outside the folder opens
    under its path relative to the folder (decision B-D6). In the trellis
    view the occurrence becomes the head first, a choice there that records
    nothing, so that the place left, which is recorded, is the trellis at
    that occurrence, to which a step back returns (AMD-MI-002 §3 rule 4)."""
    held = trellis_shown.value
    if held is None:
        return
    if view_mode.value == "trellis":
        set_head(position)
    left = _place()
    set_head(position)
    path = trellis.occurrence_file(tab_folder.value, held, position)
    show_stage()
    line = None
    if block:
        h, key = position
        stage = held.trellis["periods"][h]["stages"][key]
        line = trellis.block_line(model.collection(stage), block)
    if line is not None:
        _open_at(path, line)
    else:
        open_file(path)
    _record(left)


def describe_trellis(selection: dict | None, held, views: dict):
    """What the trellis's panel shows for the selection
    (`trellis.describe_node`), or the sentence of a node the view does not
    hold; None where nothing is selected or no trellis stands."""
    if selection is None or held is None:
        return None
    try:
        return trellis.describe_node(held, selection["graphId"], selection["nodeId"], views)
    except KeyError as error:
        return error.args[0] if error.args else str(error)


# the address of a period of the trellis, `periods[3]`, as Details names a
# selected period
_PERIOD_WORD = re.compile(r"periods\[(\d+)\]")


def _after_write(path: str, written: recipe.Written) -> None:
    """The steps after the Workbench wrote the file `path` of the tab's
    folder, for a value or a method of the BellmanType panel (specification
    §3.2; AMD-MI-002 §5 rule 6): the file's buffer, where the tab holds one,
    takes the new text. Each saved state is read once (§3.1): the trellis's
    watcher compares every file of the last reading, the written file among
    them, and reads the trellis again; the open stage's watcher compares the
    files that bind it (`recipe.watched_files`) and binds it again, so that
    `rebind` is raised here only where the written file is not among those.
    The tree is read again, so that it marks the file changed."""
    if buffers.value.get(path) is not None:
        load_text(path, written.text, written.digest)
    current = shown.value
    compared = (
        current.source_digests if current is not None and current.path == open_path.value else {}
    )
    if str((tab_folder.value.root / path).resolve()) not in compared:
        rebind.value = rebind.value + 1
    refresh_folder()


# the controls of the Recipe tab whose change a refusal marks (design pass 9
# §3): an entry's select, the button that writes a slot's own file (unit K's
# decision K-D7) and a stage's periods field
SELECT = "select"
NEW_FILE = "new file"
PERIODS = "periods"


def _refuse_choice(entry, sentence: str, control: str) -> None:
    """Records the refusal of a change of the Recipe tab (`choice_refusal`;
    design pass 9 §3): `sentence`; the address of `entry`, the entry or the
    periods changed, and `control`, the control refused, `SELECT`,
    `NEW_FILE` or `PERIODS`, which the tab marks; the file that writes the
    entry and the entry's line there, counted in the text of its unsaved
    buffer (`trellis.address_place`), which the list under the error mark
    links (AMD-MI-002 §6a rule 1); and the moment. The gesture that waits,
    whose refusal this is, no longer waits."""
    place = trellis.address_place(
        tab_folder.value,
        tab_folder.value.root / entry.file,
        entry.address,
        expanded=False,
        texts=trellis.texts_of(unsaved_texts()),
    )
    choice_refusal.value = {
        "sentence": sentence,
        "address": entry.address,
        "control": control,
        "file": entry.file,
        "line": place[1] if place is not None else None,
        "made": time.monotonic(),
    }
    gesturing.value = None


def _recipe_gesture(write, entry, control: str, opens: str | None = None) -> None:
    """A change of the Recipe tab as a gesture of the page (spec 0.4 §3.3;
    AAS, M-D17; design pass 9 §4): `write`, a writer of the recipe's text as
    a function of the mapping of unsaved texts, which answers a
    `creation.Added`, becomes the gesture that waits, of the kind `recipe`,
    whose edit of the open recipe is asked of the editor as one replacement,
    so that it stands in the buffer at once, marks the tab unsaved and is
    taken back by one undo; nothing is written to disk but a new file the
    writer answers. A refusal of the writer, or an editor whose document no
    longer holds the text the writer read, ends the gesture with nothing
    written, the control `control` of `entry` marked and the sentence under
    the error mark (`_refuse_choice`). `opens` is the file, relative to the
    folder, that the editor opens once the gesture has written."""
    choice_refusal.value = None
    refuse = functools.partial(_refuse_choice, entry, control=control)
    _begin_gesture(write, "recipe", opens, refuse=refuse)


def _recipe_text(texts: dict, entry) -> tuple[str, str]:
    """The resolved path of the file that writes `entry`, the key of the
    mapping of unsaved texts `texts`, and its text there, else on disk
    (spec 0.4 §3.1); a file that cannot be read is refused with a ValueError
    in one sentence."""
    file = _resolved(entry.file)
    if file in texts:
        return file, texts[file]
    try:
        return file, model.read_file(tab_folder.value, entry.file).text
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"the file cannot be read: {error}") from None


def _recipe_added(entry, file: str, text: str, new: str, written: str, new_files=()):
    """The answer of a writer of the Recipe tab, a `creation.Added`: the
    recipe's text `text` edited to `new`, none where they are equal, so that
    a change that writes nothing asks nothing of the editor; the new files
    `new_files`; and the status line's note in the form of brief §5, the
    recipe by its name, the address and the text written,
    `spec.yml, stages.tenure.calibration.all[0]: calibration/wage_schedule
    written`, then the new files from the factory's folder."""
    notes = [f"{Path(entry.file).name}, {entry.address}: {written} written"]
    if new_files:
        named = ", ".join(posixpath.relpath(path, model.FACTORY_FOLDER) for path, _ in new_files)
        notes.append(f"new: {named}")
    edits, read = ({file: new}, {file: text}) if new != text else ({}, {})
    return creation.Added(tuple(new_files), edits, read, tuple(notes))


def choose_file(entry, chosen: str) -> None:
    """A choice in a select of the Recipe tab (specification §3.2; AAS,
    M-D17; design pass 9 §§3 and 4): `entry` replaced by `chosen`, a file
    relative to the folder, written by its name (`recipe.written_name`), or
    a slot `$<name>`, written as it is, in the recipe's unsaved text by
    `recipe.choose`, as one edit of its buffer with one undo
    (`_recipe_gesture`). Refused, with nothing written and the select
    marked, where the text no longer writes the entry the table showed or
    the package's writer cannot replace it."""
    folder, found = tab_folder.value, source.value

    def write(texts):
        file, text = _recipe_text(texts, entry)
        new = recipe.choose(folder, found, entry, chosen, text)
        named = (
            chosen if chosen.startswith("$") else recipe.written_name(folder, found, entry, chosen)
        )
        return _recipe_added(entry, file, text, new, named)

    _recipe_gesture(write, entry, SELECT)


def new_file_for(entry, key: str, kind: str) -> None:
    """The button `New file` beside the slot `entry` of the stage `key`'s
    cell of the kind `kind` in the Recipe tab (unit K's decision K-D7;
    design pass 9 §§3 and 4): the empty file of that kind for that stage, at
    the folder's conventional place (`creation.new_source_file`), written
    to disk as a file that does not exist, and its name written in the
    slot's place in the recipe's unsaved text as a choice writes a file
    (`recipe.choose`), in one gesture whose edit of the recipe one undo
    takes back (`_recipe_gesture`); the editor then opens the new file.
    Refused, with nothing written and the button marked, where the creation
    unit refuses the file, the file appears on disk first, or the recipe's
    edit is refused."""
    folder, found = tab_folder.value, source.value

    def write(texts):
        path, created = creation.new_source_file(folder.root, key, kind)
        file, text = _recipe_text(texts, entry)
        new = recipe.choose(folder, found, entry, path, text)
        named = recipe.written_name(folder, found, entry, path)
        return _recipe_added(entry, file, text, new, named, ((path, created),))

    _recipe_gesture(write, entry, NEW_FILE, opens=creation.source_path(key, kind))


def choose_periods(key: str, typed: str, shown) -> None:
    """The periods field of the stage `key`'s row in the Recipe tab, at
    Enter or when it is left (design pass 9 §§3 and 4): `typed` written as
    the stage's `periods: [lo, hi]` in the recipe's unsaved text by
    `recipe.write_periods`, the key taken out for an empty field, as one
    edit of its buffer with one undo (`_recipe_gesture`). `shown` is the
    `recipe.Entry` of the periods the field showed, None where the recipe
    writes none. Refused, with nothing written and the field marked, for a
    text that is no range of periods, a block that no longer writes what
    the field showed, or a layout the package's writers cannot change."""
    found = source.value
    entry = shown or recipe.Entry("", False, found.path, f"stages.{key}.periods", None)

    def write(texts):
        file, text = _recipe_text(texts, entry)
        new = recipe.write_periods(text, key, typed, shown.text if shown is not None else None)
        return _recipe_added(entry, file, text, new, typed.strip() or "no periods")

    _recipe_gesture(write, entry, PERIODS)


# The stage list of the Recipe tab's button `Stage` (unit N, Task 5; design
# pass 10 §7): whether it is open; the period file whose list it adds to,
# None for the first the recipe's trellis names; and the id of the item
# last chosen in it, which it marks when it opens again.
recipe_chooser = solara.reactive(False)
recipe_chooser_file = solara.reactive(None)
recipe_chosen_item = solara.reactive(None)


def add_stage_from_recipe() -> None:
    """The button `Stage` of the Recipe tab's last row (design pass 9 §3;
    design pass 10 §7): opens the stage list beside the button
    (`StageChooser`), the same list a period's `+ stage` opens over the
    graph, or closes it where it is open."""
    recipe_chooser.value = not recipe_chooser.value


def close_recipe_chooser() -> None:
    """Closes the Recipe tab's stage list, as Escape or its `×` does."""
    recipe_chooser.value = False


# The Recipe tab's open row (design pass 11 §2): the key of the one stage
# whose row draws its controls, None while every row stands at rest. It is
# None at first and after a reading of the trellis whose table holds no
# row of that key (`RecipeRegion`), and a new source or folder forgets it
# (`_clear_trellis`).
recipe_open_stage = solara.reactive(None)


def open_recipe_row(key: str) -> None:
    """Opens the Recipe tab's row of the stage `key` (design pass 11 §2), at
    a click on the row anywhere but on its trash, or at Enter or Space while
    the row has the focus; the row open before closes. Writes nothing."""
    recipe_open_stage.value = key


def close_recipe_row(data=None) -> None:
    """Closes the Recipe tab's open row (design pass 11 §2), at Escape in the
    row or a click outside the tab's table, which window.vue reads and sends
    with no data. Writes nothing."""
    recipe_open_stage.value = None


def choose_from_recipe(item: dict, period_file: str) -> None:
    """An item of the Recipe tab's stage list chosen (unit N, Task 5; design
    pass 10 §7): the list closes, and the item is added to the list of
    stages of the period file `period_file` as a drop of it on the first
    period that list writes adds it (`trellis.list_period`), a gesture of
    the kind `dropped` named by the reading the trellis view holds, so that
    its edits, its note and its refusal are the drop's (`trellis.drop_edits`):
    a template whose key the recipe holds opens the form "add stage" filled
    in, and the item `From a folder…` the form that copies a stage folder of
    the disk, as a drop opens them. Where no period has that list, as for a
    trellis that writes every list in its own entries, the form "add stage"
    opens, whose select names the period's list."""
    recipe_chooser.value = False
    held, folder = trellis_shown.value, tab_folder.value
    if held is None:
        return
    texts = trellis.texts_of(unsaved_texts())
    h = trellis.list_period(held, folder.root, period_file, "", texts)
    if h is None:
        open_form("add stage")
        return
    recipe_chosen_item.value = item["id"]
    event = {
        "item": item["id"],
        "kind": item["kind"],
        "target": f"periods[{h}]{LAYER_ID_ENDING}",
        "reading": trellis.reading_record(folder, held),
    }
    _begin_gesture(event, "dropped")



def on_selected(data: dict) -> None:
    """A selection links the view, panel and editor (spec 0.4 §2.5).
    A user click moves the editor; a user null selection clears the
    linked surfaces without changing the editor's text or cursor."""
    node_id = data.get("nodeId")
    if not node_id:
        if data.get("origin") == "user":
            selected.value = None
            cursor_block.value = None
            block_nodes.value = []
        return
    graph_id = data.get("graphId") or graph.value
    selected.value = {"nodeId": node_id, "graphId": graph_id}
    # a box selected ends the selection of a join wire (J-D39)
    chosen_join.value = None
    # in the trellis view a selection is described in the panel alone; its
    # buttons open an occurrence's stage file
    if data.get("origin") != "user" or view_mode.value == "trellis":
        return
    # a field of a field diagram has no block: the editor goes to the header
    # that first lists it, which its `lines` row names
    current = shown.value
    if current is not None and graph_id in INITIAL_IDS.values():
        try:
            attributes = model.node_attributes(level_collection(current), graph_id, node_id)
        except KeyError:
            attributes = {}
        if attributes.get("kind") == "field":
            line = model.header_line_of(attributes)
            if line is not None:
                goto_line(line, 1)
            return
    goto_block(_block_of(current, graph_id, node_id))


def on_opened(data: dict) -> None:
    """A double click on a node of the view (AMD-MI-002 §3 rule 2, A2-D2):
    in the trellis view, the stage file of the occurrence that holds the
    node opens bound as that occurrence (`open_occurrence`), at the header
    of the node's block where the package's `node_place` names one, as for
    a box or a builder of the occurrence, and at no block otherwise, as for
    the occurrence's own layer. The node is selected first, as the double
    click's first click selects it in the viewer, so that a step back
    returns to the trellis with that node selected (rule 4). A node that
    `node_place` places in no occurrence, as a period's own layer and a
    boundary marker of the trellis, where data enter or leave the drawn
    range (design pass 10 §6), changes nothing, and so do a node the view
    does not hold and a double click in a stage's view."""
    held = trellis_shown.value
    node_id = data.get("nodeId")
    if view_mode.value != "trellis" or held is None or not node_id:
        return
    graph_id = data.get("graphId") or graph.value
    try:
        place = node_place(held.collection, graph_id, node_id)
    except (KeyError, ValueError):
        return
    position = trellis.occurrence_positions(held).get(place.occurrence)
    if position is not None:
        selected.value = {"nodeId": node_id, "graphId": graph_id}
        open_occurrence(position, place.block)


def on_refused(data: dict) -> None:
    """The region's exact refusal stands until a successful layout (G-D9)."""
    layout_refusal.value = {"sentence": data["sentence"], "made": time.monotonic()}
    drawing.value = False


def on_select_field(data: dict) -> None:
    """A field's button in the Fields tab, clicked or given Enter (spec 0.4
    §§2.5 and 5.5; G-D7; unit R, review 13): the editor moves to `line`,
    the header that first lists the field, where the row names one, and
    the field's box is selected in the initial diagram shown, where it
    holds the box; the field's identity is the box's id. Before a box is
    selected, the block at that line is recorded as the cursor's, as
    `goto_block` records it, so that the cursor event that follows does not
    select that block's box in place of the field's."""
    current = shown.value
    identity = data.get("identity")
    line = data.get("line")
    held = (
        view_mode.value == "stage"
        and current is not None
        and graph.value in INITIAL_IDS.values()
        and any(
            diagram["id"] == graph.value and any(node["id"] == identity for node in diagram["nodes"])
            for diagram in level_collection(current)["graphs"]
        )
    )
    if line:
        spans = _spans_of_the_text(current) if held else None
        if spans is not None:
            block = model.block_at(spans, int(line))
            cursor_block.value = block
            cursor_line.value = int(line)
            shown_nodes = level_collection(current)
            block_nodes.value = (
                model.nodes_of_block(shown_nodes, graph.value, block) if block else []
            )
        goto_line(int(line), 1)
    if held:
        select_node(identity, graph.value)


def _selected_field() -> str | None:
    """The selected initial-diagram node's identity for the Fields row
    (spec 0.4 §2.5; G-D7), or None in another graph."""
    selection = selected.value
    if selection is not None and selection["graphId"] in INITIAL_IDS.values():
        return selection["nodeId"]
    return None


def on_processed(data: dict) -> None:
    """A successful layout ends drawing and clears the region's refusal (G-D9)."""
    layout_refusal.value = None
    drawing.value = False


def on_cursor(data: dict) -> None:
    """The editor's cursor moved. An event of another document is dropped,
    and so is an event while the view shows the trellis, or while the open
    file is no stage file or the view shows no object of it. Otherwise the
    line is recorded for the panel's list of the boxes that read it, and
    the line with the column for the panel's view of the name under the
    cursor (`NameView`), which the panel reads in the shown object's own
    text. When the cursor then enters a block of the spans that match the
    editor's text (`_spans_of_the_text`), the panel lists the block's nodes
    in the graph shown and the view selects the first of them, unless the
    block has none there or the selected node is one of them; when it
    leaves every block, the list is emptied. While the open file's last
    outcome is refused, the cursor stands in a text the shown object does
    not hold: the list is emptied and no node is selected (unit K, Task
    13)."""
    if not _event_is_current(data):
        return
    if view_mode.value == "trellis":
        return
    current = shown.value
    if current is None or not _is_stage(open_path.value) or current.path != open_path.value:
        return
    cursor_line.value = data["line"]
    cursor_place.value = (data["line"], data.get("column") or 1)
    result = _result_of(open_path.value)
    if result is not None and result.stale:
        block_nodes.value = []
        cursor_block.value = None
        return
    spans = _spans_of_the_text(current)
    if spans is None:
        return
    block = model.block_at(spans, data["line"])
    if block == cursor_block.value:
        return
    # the nodes are written before the block, so that no render lists the
    # nodes of a block the cursor has left
    if block is None:
        block_nodes.value = []
        cursor_block.value = None
        return
    nodes = model.nodes_of_block(level_collection(current), graph.value, block)
    block_nodes.value = nodes
    cursor_block.value = block
    chosen = selected.value
    outside = (
        chosen is None
        or chosen["graphId"] != graph.value
        or _block_of(current, chosen["graphId"], chosen["nodeId"]) != block
    )
    if nodes and outside:
        select_request.value = {
            "nodeId": nodes[0],
            "graphId": graph.value,
            "n": _counter(select_request.value),
        }


def select_node(node_id: str, graph_id: str | None = None) -> None:
    """Selects `node_id` in the view, in the graph `graph_id` or the graph
    shown; a node of another graph shows that graph first."""
    target = graph_id or graph.value
    if target != graph.value:
        switch_graph(target)
    select_request.value = {
        "nodeId": node_id,
        "graphId": target,
        "n": _counter(select_request.value),
    }


def switch_graph(name: str) -> None:
    """Shows the graph `name` in the view; a gesture of the trellis graph
    that waits is withdrawn (`withdraw_gesture`)."""
    if graph.value == name:
        return
    graph.value = name
    withdraw_gesture()
    selected.value = None
    cursor_block.value = None
    block_nodes.value = []


# the options of the graph's header's two selects, AAS's words (R-D56): the
# kind of graph of a stage's view, and the direction
GRAPH_KINDS = ("operator", "initial")
DIRECTIONS = ("backward", "forward")


def kind_of(graph_id: str) -> str:
    """R-D56. The kind of the graph `graph_id` of a stage's view: `initial`
    for a graph of INITIAL_IDS, the initial diagrams, `operator`
    otherwise."""
    return "initial" if graph_id in INITIAL_IDS.values() else "operator"


def direction_of(graph_id: str) -> str:
    """Spec 0.4 §2.1; G-D16. The direction of the graph `graph_id`, `backward` or `forward`: the
    key of INITIAL_IDS that names it, else the id itself."""
    return next((key for key, value in INITIAL_IDS.items() if value == graph_id), graph_id)


def graph_id_of(kind: str, direction: str) -> str:
    """R-D56. The id of the graph of the kind `kind` in `direction`, of a
    stage's view and of the trellis alike: the initial diagram of the
    direction for `initial` (design pass 14 §7) and the builders graph, the
    direction's own id, for `operator`."""
    return INITIAL_IDS[direction] if kind == "initial" else direction


def hold_initial_diagrams() -> None:
    """The trellis's two initial diagrams computed and held with the
    trellis shown, once the Initial view is chosen in the trellis
    (`trellis.with_initial_diagrams`; design pass 14 §7; S-D30): the view
    shown and the outcome that answered it take the extended view, so that
    the Problems mark keeps listing the reading's refusals; nothing where no
    trellis is shown or it holds them already."""
    held, outcome = trellis_shown.value, trellis_outcome.value
    if held is None or trellis.holds_initial_diagrams(held):
        return
    shown = trellis.with_initial_diagrams(held)
    trellis_shown.value = shown
    if outcome is not None and outcome.shown is held:
        trellis_outcome.value = outcome._replace(shown=shown)


def choose_kind(kind: str | None) -> None:
    """The header's select `graph` (R-D56; amendment 02 ruling 4), in a
    stage's view and in the trellis view (design pass 14 §7; S-D12): the
    graph of `kind` in the direction shown; in the trellis, `initial`
    first computes the trellis's initial diagrams where the view shown
    lacks them (`hold_initial_diagrams`; S-D30). The change is kept in the
    place shown and makes no place of the history, so that ← shows the
    place left before it."""
    if kind in GRAPH_KINDS:
        name = graph_id_of(kind, direction_of(graph.value))
        if view_mode.value == "trellis" and name in INITIAL_IDS.values():
            hold_initial_diagrams()
        switch_graph(name)


def choose_direction(direction: str | None) -> None:
    """The header's select `direction` (R-D56; amendment 02 ruling 4): the
    graph of the kind shown in `direction`, in a stage's view and in the
    trellis view alike (design pass 14 §7). The change makes no place of the
    history."""
    if direction in DIRECTIONS:
        switch_graph(graph_id_of(kind_of(graph.value), direction))


def request_save() -> None:
    """Asks the editor for its current document, which `on_save` writes."""
    save_request.value = save_request.value + 1


def toggle_types() -> None:
    """Hides the types when they are shown, and shows them when they are
    hidden."""
    hide_types.value = not hide_types.value


def toggle_notes() -> None:
    """Draws every note as written when the notes stand behind their
    glyphs, and draws each behind its glyph again when they are drawn as
    written (the tab row's `Notes`; design pass 10 §§4 and 9)."""
    show_notes.value = not show_notes.value



def toggle_overlays() -> None:
    """Draws the perch overlays when they are hidden, and hides them when
    they are drawn."""
    overlays_on.value = not overlays_on.value


def toggle_builders() -> None:
    """Shows the operative builders while the declared builders are shown,
    and the declared builders while the operative ones are (the layers
    button; SE-6). A selected node that the collection of the level now
    shown does not hold is replaced by the layer of its builder, which both
    levels hold, so that Details describes a node the graph holds (SE-7)."""
    builders_operative.value = not builders_operative.value
    current, chosen = shown.value, selected.value
    if current is None or current.declared is None or chosen is None:
        return
    graph_id, node_id = chosen["graphId"], chosen["nodeId"]
    # a layer is a builder's namespace, which both levels hold
    if node_id.endswith(LAYER_ID_ENDING):
        return
    held = {
        node["id"]
        for entry in level_collection(current)["graphs"]
        if entry["id"] == graph_id
        for node in entry["nodes"]
    }
    if node_id not in held:
        builder = node_id.split(":", 1)[0].split(".", 1)[0]
        select_node(f"{builder}{LAYER_ID_ENDING}", graph_id)


def level_collection(current: Shown | None) -> dict | None:
    """The collection the view shows of the stage `current`: the declared
    builders' (`Shown.declared`) while the layers button is off and a bound
    method block opens a builder, and otherwise its collection (SE-7)."""
    if current is None:
        return None
    if current.declared is not None and not builders_operative.value:
        return current.declared
    return current.collection


def level_stage(current: Shown):
    """The stage version whose builders the view shows of `current`
    (`model.at_level`): the version `stage.declared` reads while the
    declared builders of a stage with two levels are shown, and otherwise
    the stage."""
    return model.at_level(
        current.stage, builders_operative.value or current.declared is None
    )


def toggle_sheet(name: str) -> None:
    """Shows the sheet `name` of the stage in the panel, or hides it when
    it is the one shown."""
    sheet_open.value = None if sheet_open.value == name else name


def toggle_status() -> None:
    """Shows the status line's details when they are hidden (the button
    `more`), and hides them when they are shown (`less`)."""
    show_status.value = not show_status.value


def graph_of_node(collection: dict, node_id: str) -> str | None:
    """The id of the graph of `collection` that holds the node `node_id`,
    None where none does."""
    for entry in collection["graphs"]:
        if any(node["id"] == node_id for node in entry["nodes"]):
            return entry["id"]
    return None


def choose_compare() -> None:
    compare_open.value = not compare_open.value


def choose_overwrite() -> None:
    """The next save writes over the file as it stands on disk."""
    overwrite_pending.value = True
    request_save()


def choose_reload() -> None:
    """The disk's text replaces the open file's buffer."""
    found = conflict.value
    path = open_path.value
    if found is None or path is None:
        return
    load_text(path, found["disk_text"] or "", found["disk_digest"] or None)


def unified_diff(disk_text: str | None, buffer_text: str) -> str:
    """The unified diff from the text on disk to the text in the editor."""
    lines = difflib.unified_diff(
        (disk_text or "").splitlines(),
        buffer_text.splitlines(),
        fromfile="on disk",
        tofile="in the editor",
        lineterm="",
    )
    return "\n".join(lines) or "the two texts are equal"


# --- git and the forms (unit C, specification §4 and §5) ---


def open_form(kind: str, fill: dict | None = None) -> None:
    """Opens the form `kind` over the window, with no refusal standing, and
    with `fill`, what a drop on the trellis graph filled in, or none
    (`form_fill`; spec 0.4 §§3.5, 3.6)."""
    form_error.value = ""
    form_fill.value = fill
    form_open.value = kind


def close_form() -> None:
    """Closes the form open over the window, and forgets what a drop
    filled in."""
    form_open.value = None
    form_error.value = ""
    form_fill.value = None


def open_commit(message: str = "") -> None:
    """Opens the commit form over the tab's folder (specification §5): the
    changes git reports under the folder, each named, and `message` in the
    message box; the paths are listed before the commit runs."""
    commit_changes.value = model.git_changes(tab_folder.value)
    commit_unticked.value = frozenset()
    commit_message.value = message
    open_form("commit")


def open_adoption_commit(record: dict) -> None:
    """Opens the commit form after a recorded adoption of a job's returned
    files (amendment 06 §2 item 23): the message `returned.commit_offer`
    answers, and every change git reports but the files the adoption wrote
    left out; nothing is committed until `commit` is pressed. Does nothing
    for an adoption that is not recorded as adopted."""
    offer = returned.commit_offer(tab_folder.value, record)
    if offer is None:
        return
    message, paths = offer
    open_commit(message)
    commit_unticked.value = frozenset(
        change.path for change in commit_changes.value if change.path not in paths
    )


def commit_paths() -> list[str]:
    """The paths the commit form names, in git's order: each change not
    left out, a rename or a copy by its new path and then its original."""
    paths = []
    for change in commit_changes.value:
        if change.path in commit_unticked.value:
            continue
        paths.append(change.path)
        if change.original is not None:
            paths.append(change.original)
    return paths


def toggle_commit_path(path: str) -> None:
    """Leaves the change of `path` out of the commit, or names it again."""
    left = commit_unticked.value
    commit_unticked.value = left - {path} if path in left else left | {path}


@solara.lab.task
def git_task(kind: str, message: str = "", paths: tuple = ()) -> model.GitResult:
    """One git command for the tab's folder, run in a thread, so that
    git's line is blocked while it runs and the rest of the page is not
    (specification §5): `commit`, the path-limited commit of `paths` with
    `message`, or `push`, the push of the current branch. Git's own
    sentence is recorded afterwards as the answer to the command
    (`git_answer`), with whether git refused it, and the tree and git's
    summary are read again: git's line prints the sentence of a command
    git did not refuse, and the list under the error mark holds that of a
    refused one (AMD-MI-002 §6a rule 1). Where git refuses a commit without
    writing a reason, the answer holds the words that say so, whether the
    commit form is open or closed. For a commit, the commit form, where it
    is still open, closes when git answers ok; when git refuses, it stays
    open with the answer's sentence as its refusal (`form_error`), its
    message and its names kept. The result returned is git's, as
    `model.git_commit` or `model.git_push` answers it, its sentence empty
    where git wrote none."""
    folder = tab_folder.value
    if kind == "commit":
        result = model.git_commit(folder, message, list(paths))
    else:
        result = model.git_push(folder)
    sentence = result.sentence.strip()
    if kind == "commit" and not result.ok and not sentence:
        # where git refuses the commit and writes no reason, as when a hook
        # refuses it and prints nothing, the answer holds these words, and so
        # does the commit form where it is open
        sentence = "git refused the commit and wrote no reason"
    git_answer.value = {
        "command": kind,
        "sentence": sentence,
        "refused": not result.ok,
        "made": time.monotonic(),
    }
    if kind == "commit" and form_open.value == "commit":
        if result.ok:
            close_form()
        else:
            form_error.value = sentence
    refresh_folder()
    return result


def submit_commit() -> None:
    """Starts the commit of the paths the commit form names, with its
    message, and leaves the form open while git runs, with no refusal
    standing: `git_task` closes the form when git answers ok, and shows
    git's sentence in it when git refuses, or, where git wrote none, the
    sentence that says so."""
    form_error.value = ""
    git_task(kind="commit", message=commit_message.value, paths=tuple(commit_paths()))


def run_export() -> None:
    """Writes the held trellis in the trellis view, or the shown stage,
    under model-explorer/ with its record (specification §5; spec 0.4 §4;
    G-D10). The trellis record names its source, drawing restriction and
    held file digests, and marks each input the reading took from an
    unsaved buffer (brief rule 5); the whole trellis is exported. The stage
    record names its occurrence, held source digests and unsaved buffer
    state. Both records name the direction shown. Git's line names the
    source and record. An operating-system or missing-package refusal is
    recorded in `git_answer` for the error mark's list (AMD-MI-002 §6a rule
    1)."""
    current = shown.value
    held_trellis = trellis_shown.value if view_mode.value == "trellis" else None
    if view_mode.value == "trellis":
        if held_trellis is None:
            return
        source = held_trellis.source.path
    else:
        if current is None:
            return
        source = current.path
    try:
        if held_trellis is not None:
            record = model.export_trellis(
                tab_folder.value,
                held_trellis.trellis,
                source=source,
                restriction=(
                    held_trellis.restriction.text if held_trellis.restriction is not None else None
                ),
                direction=graph.value,
                files=held_trellis.files,
                buffered=held_trellis.buffered,
            )
        else:
            held = buffers.value.get(current.path)
            unsaved = held is None or _digest(current.text) != held["digest"]
            record = model.export_view(
                tab_folder.value,
                current.stage,
                current.text,
                current.path,
                unsaved=unsaved,
                occurrence=current.occurrence,
                direction=graph.value,
                source_digests=current.source_digests,
            )
    except (OSError, importlib.metadata.PackageNotFoundError) as error:
        sentence, refused = f"the view of {source} was not exported: {error}", True
    else:
        name = record.relative_to(tab_folder.value.root).as_posix()
        sentence = f"the view of {source} exported with its record {name}"
        refused = False
    git_answer.value = {
        "command": "export",
        "sentence": sentence,
        "refused": refused,
        "made": time.monotonic(),
    }


def _current_construction(current: Shown | None, result: Outcome | None) -> bool:
    """Whether `current`, the stage shown, is the construction of the open
    file's buffer at its current revision, and `result`, the loop's outcome
    for the open file, is of that revision and lists no refusal. The one
    statement of this condition, which `paper_offered` and `goto_entries`
    read (ruling R-P10)."""
    path = open_path.value
    held = buffers.value.get(path) if path is not None else None
    return (
        current is not None
        and held is not None
        and result is not None
        and current.path == path == result.path
        and (held["revision"], held["text"]) == (current.revision, current.text)
        and result.revision == current.revision
        and not result.refusals
    )


def paper_offered(current: Shown | None, result: Outcome | None) -> bool:
    """Whether Details offers `paper` (spec 0.4 §5.5; brief rule 7; R-D17,
    R-D25, R-D41): in the stage view, with a piece selected, while the
    stage shown is the construction of the open file's buffer at its
    current revision with no refusal standing (`_current_construction`),
    the buffer holds the file's saved text, the view is not dimmed, and the
    folder holds no `paper/<stage>.md`. Otherwise the button is omitted
    (spec 0.4 §6)."""
    if view_mode.value != "stage" or selected.value is None:
        return False
    if not _current_construction(current, result) or result.stale:
        return False
    if _dirty(buffers.value.get(current.path)):
        return False
    written = tab_folder.value.root / model.PAPER_FOLDER / f"{current.stage.name}.md"
    return not written.exists()


def run_paper() -> None:
    """Writes `paper/<stage>.md` and `paper/<stage>.svg` for the stage
    shown while `paper_offered` holds (`model.write_paper`; spec 0.4 §5.5;
    brief rule 7; R-D37), then reads the folder again, so that the tree
    lists the files and the button is omitted (R-D41). The answer is
    recorded in `git_answer` under the command `paper`, as `run_export`
    records its own (R-D42): `paper/<name>.md written with
    paper/<name>.svg`; or, where the package refuses the drawing or the
    operating system refuses the write, its sentence with nothing added,
    which stands in the list under the error mark (AMD-MI-002 §6a rule 1).
    Where the Markdown file exists already, nothing is written or
    recorded."""
    current = shown.value
    if not paper_offered(current, _result_of(open_path.value)):
        return
    answer = None
    try:
        written = model.write_paper(
            tab_folder.value, current.stage, current.path, current.text, current.source_digests
        )
    except (RuntimeError, OSError) as error:
        answer = (str(error), True)
    else:
        if written:
            answer = (f"{written[0]} written with {written[1]}", False)
        refresh_folder()
    if answer is not None:
        sentence, refused = answer
        git_answer.value = {
            "command": "paper",
            "sentence": sentence,
            "refused": refused,
            "made": time.monotonic(),
        }


def run_notebook() -> None:
    """Writes `notebooks/<folder>.ipynb` for the source of a trellis the
    tab shows or last showed, `source` (`creation.write_notebook`; spec 0.4
    §5.9; brief rule 7; R-D41), then reads the folder again, so that the
    tree lists the file and the button is omitted; it opens nothing and
    runs nothing. The answer is recorded in `git_answer` under the command
    `notebook`, as `run_paper` records its own (R-D42):
    `notebooks/<name>.ipynb written`, which the status line's note prints;
    or, where the operating system refuses the write, its sentence with
    nothing added, which stands in the list under the error mark
    (AMD-MI-002 §6a rule 1). Where the file exists already, nothing is
    written or recorded."""
    chosen = source.value
    if chosen is None:
        return
    answer = None
    try:
        written = creation.write_notebook(tab_folder.value.root, chosen.path, chosen.kind)
    except OSError as error:
        answer = (str(error), True)
    else:
        if written is not None:
            answer = (f"{written} written", False)
        refresh_folder()
    if answer is not None:
        sentence, refused = answer
        git_answer.value = {
            "command": "notebook",
            "sentence": sentence,
            "refused": refused,
            "made": time.monotonic(),
        }


def _unsaved_sentence(paths) -> str | None:
    """The refusal of an action while a buffer holds unsaved text, of a
    file of `paths`, or of any file where `paths` is None, naming the files,
    `cons.bl holds unsaved text`; None where no such buffer stands."""
    dirty = sorted(_dirty_paths() if paths is None else _dirty_paths() & set(paths))
    if not dirty:
        return None
    verb = "holds" if len(dirty) == 1 else "hold"
    return f"{', '.join(dirty)} {verb} unsaved text"


def open_model(path) -> None:
    """Makes the folder `path` the tab's model folder (specification §4:
    the editor opens the recipe of the folder "new trellis" wrote): the
    buffers, the loop's results, the view, the selection, the cursor's
    block, line and column, the choice, the tree's open folders, a close
    waiting on the editor, the Matsya window's exchanges, the
    classification table's note of its last change, the value tabs' refused
    write, the answer to the last command of git's line, the tab's gestures
    that edited several files (`gesture_steps`), the files listed to
    delete on save (`deleting`; unit L, Task 25), and the tab's
    history of places with the place it asked
    of the view (AMD-MI-002 §3 rule 4, A2-D5) of the folder left are
    cleared, and so are its trellis and what depends on it
    (`_clear_trellis`), the source, the restriction with its text and its
    refusal, and the digests the watcher recorded when it last bound the
    open file anew (`rebind_sources`); the view is the stage's again, and
    the count `trellis_rebuild` is raised, so that a reading of the folder
    left that is still running records nothing, even where the new folder's
    source has the same path. The tree, git's line, the checklist and the
    sources of the trellis are read from the new one. The caller refuses
    first while a buffer holds unsaved text, which this would discard."""
    with LOOP_LOCK:
        tab_folder.value = model.open_folder(path)
        open_path.value = None
        buffers.value = {}
        results.value = {}
        shown.value = None
        drawing.value = False
        conflict.value = None
        compare_open.value = False
        overwrite_pending.value = False
        # the gestures of the folder left, which name its files (unit L,
        # Task 17)
        gesture_steps.value = ()
        gesture_undoing.value = None
        # the files of the folder left that a save would delete (unit L,
        # Task 25)
        deleting.value = ()
        # the trellis of the folder left, and its source, view and
        # restriction (unit B)
        _clear_trellis()
        source.value = None
        view_mode.value = "stage"
        restriction_text.value = ""
        restriction.value = None
        restriction_refusal.value = None
        rebind_sources.value = {}
        # a reading of the folder left that is still running records
        # nothing: `run_trellis` records an outcome only while the count it
        # read at its start stands
        trellis_rebuild.value = trellis_rebuild.value + 1
    selected.value = None
    cursor_block.value = None
    cursor_line.value = None
    cursor_place.value = None
    block_nodes.value = []
    sheet_open.value = None
    open_folders.value = ()
    pending_goto.value = None
    closing.value = None
    git_answer.value = None
    # the Matsya window's conversation is named by a digest of the tab's
    # folder's path (`_session`), and its jobs are the folder's
    matsya_window.clear_conversation()
    # the sentences of the BellmanType panel name their files by their
    # paths in the folder left, which a file of the new folder may also
    # have (T-C8)
    table_note.value = None
    value_note.value = None
    # the places of the folder left
    history.value = navigation.History()
    place_request.value = None
    # the Recipe tab's stage list, which lists the folder left's stages
    recipe_chooser.value, recipe_chooser_file.value, recipe_chosen_item.value = False, None, None
    refresh_folder()


def submit_new_trellis(
    parent: str, name: str, destination: str, label: str, repeat, stages, terminal=()
) -> None:
    """Writes the folder of the form "new trellis" under the parent folder
    `parent`, the path the form's field holds, read without the spaces
    around it and from `~`, the home folder, which the form fills with the
    folder that holds the tab's, so that the new model stands beside the
    open one (unit L, Task 13; C-R7 amended) (`creation.create_trellis`),
    the stage keys `terminal` standing in the terminal period alone (unit
    K, Task 12), opens it in the tab (`open_model`) and opens its recipe as
    a click on it in the tree does (`open_from_tree`): the new folder's
    trellis in the view and the recipe's text in the editor (specification
    §3.1, §4); and offers the first commit: the commit form opens with the
    new folder's files and a message, and nothing is committed until
    `commit` is pressed (specification §4, C-R1). Refused, with the
    sentence in the form and nothing written, while a buffer holds unsaved
    text, for a parent that is not a full path, or where the creation
    refuses the answers, the answer the refusal concerns recorded
    (`form_error_field`), so that the form draws the sentence under its
    field."""
    refusal = _unsaved_sentence(None)
    if refusal is not None:
        form_error.value, form_error_field.value = refusal, None
        return
    typed = parent.strip()
    place = Path(typed).expanduser()
    if not place.is_absolute():
        form_error.value = f"{typed} is no full path: write it from / or from ~"
        form_error_field.value = "parent"
        return
    try:
        created = creation.create_trellis(
            place,
            name.strip(),
            list(stages),
            label.strip(),
            repeat,
            destination.strip() or None,
            terminal=tuple(terminal),
        )
    except (ValueError, OSError) as error:
        form_error.value = str(error)
        form_error_field.value = getattr(error, "field", None)
        return
    open_model(created.folder)
    open_from_tree(creation.factory_path(creation.RECIPE))
    templated = " from templates of the application corpus" if stages else ""
    open_commit(f"New trellis {created.folder.name}{templated}")


def open_model_above(path: str) -> None:
    """The button `open <name>` beside the note of a model's `declaration/`
    opened by itself (unit L, Task 28; AAS, L-D23): makes the model folder
    `path`, the folder above, the tab's folder (`open_model`), as "new
    trellis" makes the folder it wrote, closes the list under the error
    mark, whose line the change of folder removes, and opens the folder's
    first file (`first_file`), its recipe `declaration/spec.yml`, as a click
    on it in the tree does (`open_from_tree`): the recipe's trellis in the
    view and its text in the editor, the folders on its path open in the
    tree. The process's folder, the one the server was started on, is only
    the tab's first folder. Does nothing while a buffer holds unsaved text,
    which `open_model` would discard; the button then does not act
    (`OpenModelButton`)."""
    if _unsaved_sentence(None) is not None:
        return
    open_model(path)
    errors_open.value = False
    first = first_file()
    if first is not None:
        open_from_tree(first)


def open_returned(path: str) -> None:
    """Makes the saved copy of a job's returned files at `path`, relative
    to the tab's folder, under `model.OUTPUT_FOLDER`, the tab's model
    folder, a model of its own with its own recipe, dependencies and
    bindings (`open_model`), and opens its first file (`first_file`), as
    `open_model_above` opens a folder (amendment 06 §2 item 21); the copy is
    read-only (`model.read_only`). Does nothing while a buffer holds unsaved
    text, which `open_model` would discard, or for a path that is no saved
    copy."""
    root = tab_folder.value.root / path
    if _unsaved_sentence(None) is not None or not root.is_dir():
        return
    if model.read_only(model.open_folder(root)) is None:
        return
    open_model(root)
    first = first_file()
    if first is not None:
        open_from_tree(first)


def _recipe_shown() -> str | None:
    """The name, in the factory's folder, of the recipe the tab shows, the
    context of every view (spec 0.4 §3.5; AMD-MI-002 §3 rule 1): the tab's
    source, or the folder's first source where none is chosen yet, where
    that source is a recipe; None where it is a trellis file or the folder
    has no source."""
    shown = source.value or (sources.value[0] if sources.value else None)
    if shown is None or shown.kind != "recipe":
        return None
    return Path(shown.path).name


def _form_recipe() -> str:
    """The recipe the forms "add stage", "add period" and "new stage" edit:
    the recipe the tab shows (`_recipe_shown`), and the folder's recipe
    `declaration/spec.yml` where the tab shows none."""
    return _recipe_shown() or creation.RECIPE


def submit_add_stage(template, key: str, period_file: str, entry: str = "") -> None:
    """The button of the form "add stage" (spec 0.4 §3.5; brief rule 9): a
    gesture of the kind `form` (`_submit_form`) whose writer is
    `creation.add_stage` with the recipe the form edits (`_form_recipe`),
    so that the edits of the recipe, the period's list and, where the folder
    holds it, answers.yml go into their buffers by the steps of a gesture,
    and the template's stage file and companions are written to disk once
    those edits are applied. `template` is a template's id, or the template
    of a stage folder of the disk that the form from a folder read
    (`creation.folder_template`; unit K's decision K-D26), copied by the same
    writer. The period's list is the `stages` of the entry
    `entry` of `period_file`, the empty address for a period file, as a
    drop fills it in. The status line also names the joins that entries
    already written give the new stage by its fields' names, read on the
    trellis shown (`trellis.added_stage_joins`; unit L, Task 14; defect 16
    of the UX simulation). A refusal stands in the form, and nothing is
    written."""
    root, recipe_name, typed = tab_folder.value.root, _form_recipe(), key.strip()
    shown = trellis_shown.value

    def write(texts):
        added = creation.add_stage(
            root, typed, template, period_file, entry=entry, recipe=recipe_name, texts=texts
        )
        received = trellis.added_stage_joins(
            shown, root, period_file, entry, typed, template, texts
        )
        return added._replace(notes=added.notes + (received,)) if received else added

    _submit_form(write)


def submit_new_stage(key: str) -> None:
    """The button of the form "new stage" (unit K's decision K-D7): a
    gesture of the kind `form` whose writer is `creation.new_stage` with
    the recipe the form edits (`_form_recipe`), so that the stage's row
    goes into the recipe's buffer and, where the folder holds it, its slots
    into answers.yml's, by the steps of a gesture, as "add stage" writes
    them (spec 0.4 §3.5); the empty stage file is written to disk once
    those edits are applied, the edited files are then written to disk too,
    so that the stage file and its row are saved in one change, the author
    having asked for the file (unit L, Task 17; defect 22 of the UX
    simulation), and the editor then opens the stage file. Refused while a
    file the form edits holds unsaved text, which the save would write with
    the row (`_unsaved_sentence`). A refusal stands in the form, and nothing
    is written."""
    folder = tab_folder.value
    root, recipe_name, typed = folder.root, _form_recipe(), key.strip()

    def write(texts):
        added = creation.new_stage(root, typed, recipe=recipe_name, texts=texts)
        refusal = _unsaved_sentence([recipe.relative(folder, path) for path in added.edits])
        if refusal is not None:
            raise ValueError(refusal)
        return added

    _submit_form(write, creation.factory_path(creation.stage_file(typed)), saves=True)


def submit_add_period(label: str, keys, at: int | None = None) -> None:
    """The button of the form "add period" (spec 0.4 §3.6; brief rule 9): a
    gesture of the kind `form` whose writer is `creation.add_period` with
    the recipe the form edits, so that the edits of the trellis file, the
    recipe and, where the folder holds it, answers.yml go into their
    buffers, and the period file is written to disk once those edits are
    applied. The period is the earliest with `at` None, else it takes the
    index `at` between two periods, as the `+ period` control fills it in;
    the one inter-period mapping that stands for every pair is then kept
    where the package admits it at both new pairs of the trellis shown
    (`trellis.standing_mapping_joins`; unit L, Task 19). Refused as
    `submit_add_stage` is."""
    root, recipe_name = tab_folder.value.root, _form_recipe()
    chosen, shown = list(keys), trellis_shown.value

    def write(texts):
        def standing(h, period_keys):
            return trellis.standing_mapping_joins(shown, h, period_keys, texts)

        return creation.add_period(
            root, label.strip(), chosen, at=at, recipe=recipe_name, texts=texts, standing=standing
        )

    _submit_form(write)


def submit_new_variant(name: str) -> None:
    """Writes the variant of the form "new variant" beside the folder's
    recipe, `declaration/spec.yml` (`creation.create_variant`), closes the
    form, reads the tree and the folder's sources again, and opens the
    variant's recipe as a click on it in the tree does (`open_from_tree`):
    the variant's trellis in the view, the recipe list showing the variant
    beside the first (specification §4, new variant), and the recipe's text
    in the editor. Refused, with the sentence in the form and nothing written,
    while a buffer of a file the variant copies holds unsaved text
    (`creation.variant_sources`), since the variant copies the files as
    they stand on disk, where the creation refuses, or in a saved copy of a
    job's returned files (`model.read_only`; amendment 06 §2 item 21)."""
    root = tab_folder.value.root
    refusal = model.read_only(tab_folder.value)
    if refusal is not None:
        form_error.value = refusal
        return
    try:
        copied = creation.variant_sources(root, creation.RECIPE)
    except (ValueError, OSError) as error:
        form_error.value = str(error)
        return
    refusal = _unsaved_sentence(copied)
    if refusal is not None:
        form_error.value = refusal
        return
    try:
        written = creation.create_variant(root, name.strip(), creation.RECIPE)
    except (ValueError, OSError) as error:
        form_error.value = str(error)
        return
    close_form()
    refresh_folder()
    open_from_tree(written[0])


# --- the gestures of the trellis graph (unit J) ---


def unsaved_texts() -> dict[str, trellis.Unsaved]:
    """The tab's unsaved buffers as the trellis's reading is given them
    (spec 0.4 §3.1; brief rule 2, J-D2): for each buffer of `buffers` that
    differs from its file (`_dirty`), its text and revision, by the file's
    resolved path as a string. No file is read to fill the mapping."""
    root = tab_folder.value.root
    return {
        str((root / path).resolve()): trellis.Unsaved(held["text"], held["revision"])
        for path, held in buffers.value.items()
        if _dirty(held)
    }


def read_checklist() -> None:
    """Reads the checklist of the tab's folder again (`creation.checklist`),
    the text of each unsaved buffer read in place of its file, so that a
    connector typed into a buffer and not saved is no longer counted (spec
    0.4 §3.3; unit J's plan, Task 10, item 1): called by `refresh_folder`,
    by `on_change` and where a gesture edits the buffers of files the editor
    does not hold (`apply_edits`)."""
    texts = trellis.texts_of(unsaved_texts())
    checklist.value = creation.checklist(tab_folder.value.root, texts)


def _texts_within(unsaved: dict, paths) -> dict[str, str]:
    """The texts of the unsaved buffers `unsaved` whose resolved path, as a
    string, is one of `paths` (ruling J-P2)."""
    named = set(paths)
    return {path: held.text for path, held in unsaved.items() if path in named}


def unsaved_inputs() -> tuple:
    """The fourth value of the trellis's task (brief rule 5; ruling J-P2):
    the sorted `(path, revision)` of each unsaved buffer whose resolved path
    is among the files of the last outcome (`trellis_seen`) that the
    reading can take from a buffer (`TrellisOutcome.takeable`); while no
    outcome stands, of every unsaved buffer but a stage file's, which the
    trellis's reading never takes. A change of such a buffer starts the
    task again."""
    unsaved = unsaved_texts()
    outcome = trellis_outcome.value
    if outcome is None:
        named = {path for path in unsaved if not _is_stage(path)}
    else:
        named = set(trellis_seen.value) & set(outcome.takeable)
    return tuple(sorted((path, held.revision) for path, held in unsaved.items() if path in named))


# The file the last gesture of the trellis graph edited and its text before
# and after the edit, {"path", "before", "after"}, the path relative to the
# folder; or None (spec 0.4 §3.3; brief rule 8). The steps of a gesture set
# it once the editor has answered, and a change of source clears it;
# `_gesture_place` and `trellis_diagnostics` read it.
gesture_made = solara.reactive(None)

# the label of the button that restores the text before a gesture (brief §5)
TAKE_THE_LINE_OUT = "take the line out"


def _line_extent(text: str, line: int) -> tuple[int, int]:
    """The columns, counted from one in code points, at which the text of
    the line `line` of `text` begins after its indentation and ends; one and
    one where `text` holds no such line."""
    lines = text.split("\n")
    if not 1 <= line <= len(lines):
        return 1, 1
    written = lines[line - 1].rstrip()
    return len(written) - len(written.lstrip()) + 1, len(written) + 1


def _gesture_place() -> tuple[str, int] | None:
    """The file of the last gesture of the trellis graph (`gesture_made`),
    relative to the folder, and the line the gesture typed there, counted
    in the text the gesture made (`trellis.typed_line`), while the file's
    buffer holds that text and no trellis drawn was read from it; None
    otherwise. A refusal of the trellis's reading then stands at that line,
    whatever entry the package's address names, since spec 0.4 §3.1 links a
    refused drag to the typed line and places the button `take the line
    out` there (J-I53); once a reading of the gesture's text stood, a later
    refusal is that of another edit, and stands at the package's place."""
    made = gesture_made.value
    if made is None:
        return None
    held = buffers.value.get(made["path"])
    if held is None or held["text"] != made["after"]:
        return None
    drawn = trellis_shown.value
    if drawn is not None and drawn.files.get(_resolved(made["path"])) == _digest(made["after"]):
        return None
    return made["path"], trellis.typed_line(made["before"], made["after"])


def trellis_diagnostics(path: str | None) -> list[dict]:
    """The refusal of the trellis's reading as the editor's diagnostics of
    the file `path`, relative to the folder (spec 0.4 §3.1, §3.3; brief rule
    8; ruling J-P15): where the last outcome of the trellis holds a refusal
    whose place is `path` with a line, one record of `_diagnostic_record`'s
    form, the package's sentence with nothing added, that underlines the
    text of that line as the file's buffer holds it; empty otherwise. The
    place is the line the last gesture typed while its file's buffer holds
    the text the gesture made (`_gesture_place`), and the place of the
    package's address otherwise (`_trellis_refusal_place`). At a gesture's
    line the record carries the action `take the line out`: the one
    replacement that restores the text before the gesture
    (`trellis.restoring_edit`) and the text the gesture made as the
    document the editor must hold for the replacement to apply, each with
    the line ends the editor's document has (J-D19). At the next change
    event of another text the record returns to the package's place and the
    action is withdrawn."""
    outcome = trellis_outcome.value
    if path is None or outcome is None or outcome.refusal is None:
        return []
    typed = _gesture_place()
    file, line = typed or _trellis_refusal_place(outcome.refusal)
    if file != path or line is None:
        return []
    held = buffers.value.get(path)
    text = held["text"] if held is not None else ""
    column, end_column = _line_extent(text, line)
    refusal = outcome.refusal._replace(
        file=path, line=line, column=column, end_line=line, end_column=end_column
    )
    record = _diagnostic_record(refusal)
    if typed is not None:
        made = gesture_made.value
        # the editor's document holds "\n" where the file holds "\r\n"
        before, after = (made[key].replace("\r\n", "\n") for key in ("before", "after"))
        record["action"] = {
            "name": TAKE_THE_LINE_OUT,
            "edits": [trellis.restoring_edit(before, after)],
            "expected": after,
        }
    return [record]


# The editor's answer to the last change of its property `edit` (spec 0.4
# §3.3; brief rule 7): {"path", "n", "applied"}, the path of the document
# the editor held, the request's counter and whether the edit applied; or
# None before the first answer.
edit_answer = solara.reactive(None)


def on_applied(data: dict) -> None:
    """The editor's event `applied` (brief rule 7; J-D12, J-D30), sent once
    for each request of `edit_request`, a request with no edits included:
    its path, its counter `n` and its answer are recorded in `edit_answer`;
    the undo of a gesture that waits for the answer to its request takes it
    (`_follow_undoing`; unit L, Task 17), and so does the gesture that waits
    for the answer to its request (`continue_gesture`). The answer to a
    request of the classification table is recorded too, and nothing reads
    it (J-D13)."""
    edit_answer.value = {
        "path": data.get("path"),
        "n": data.get("n"),
        "applied": bool(data.get("applied")),
    }
    _follow_undoing(edit_answer.value)
    continue_gesture("applied")


def use_gesture_properties(in_trellis: bool, held) -> tuple:
    """The graph region's properties `unjoined`, `reading`, `stages`,
    `adds` and `joins` (spec 0.4 §§3.2, 3.3, 3.5, 3.6; unit J's plan, Tasks
    9, 15 and 19), for the component that calls it, since it holds a memo:
    where the view shows the forward graph of the trellis `held`
    (`in_trellis`), the last reading was not refused and every input of
    `held` holds the text the reading took, read with the tab's unsaved
    buffers (`trellis.inputs_current`), the ports a drag can take,
    `trellis.connectable_ports` answers with those buffers, the unjoined
    ports and the reading ports that joins reach (J-D41), the record
    `trellis.reading_record` gives, the records of the stage list and the `+
    period` controls (`_drop_properties`), and the join wires
    `trellis.join_wires` answers (J-D33). Where the last reading stands
    refused and every file it read holds the text it read
    (`_refused_standing`), `held` being the last graph the package
    constructed, the record of that graph's reading and the records of the
    stage list read with the tab's unsaved buffers, so that a period's `+
    stage` opens its list there and a drop edits the texts as any drop
    does (unit L, Task 14; defect 2 of the UX simulation), and no ports, no
    controls and no join wires. Where the view shows the backward graph
    under the same conditions, the records of its cables alone
    (`trellis.join_wires` with that graph), which a click selects for
    Details, and no ports, no reading, no list and no controls, so that no
    gesture acts there (design pass 10 §8). Five None otherwise, so that no
    other graph can be connected, take a drop or lose a join. The ports, the list, the
    controls and the join wires are computed once for each trellis held,
    and the list while a reading stands refused once for each refused
    reading, since while the inputs hold the texts read they are a
    function of the trellis and of that reading alone."""
    # the graph of the trellis shown, `forward` or `backward`; the backward
    # graph is given its cables' records alone, so that a selected cable
    # reveals its route in Details and no gesture acts there (design pass 10
    # §§6 and 8; unit N, Task 7)
    direction = (graph.value if in_trellis and held is not None and held.view_refusal is None
                 and graph.value in ("forward", "backward") else None)
    forward = direction == "forward"
    texts = trellis.texts_of(unsaved_texts()) if direction is not None else None
    standing = _refused_standing() if forward and texts is not None else None
    connectable = (
        texts is not None and not _trellis_stale() and trellis.inputs_current(held, texts)
    )
    listing = standing is not None
    ports = solara.use_memo(
        lambda: trellis.connectable_ports(held, texts) if forward and connectable else None,
        [held, connectable, forward],
    )
    drops = solara.use_memo(
        lambda: _drop_properties(held, texts) if forward and (connectable or listing) else None,
        [held, connectable, standing, forward],
    )
    wires = solara.use_memo(
        lambda: trellis.join_wires(held, texts, direction) if connectable else None,
        [held, connectable, direction],
    )
    if listing:
        return None, trellis.reading_record(tab_folder.value, held), drops[0], None, None
    if not connectable:
        return None, None, None, None, None
    if not forward:
        return None, None, None, None, wires
    return ports, trellis.reading_record(tab_folder.value, held), *drops, wires


def _refused_standing():
    """The outcome of the trellis's last reading where that reading was
    refused, a graph the package constructed earlier is shown, and every
    file the reading read holds the text it read, compared as the watcher
    compares them (`_watch_trellis`): the unsaved text of a file the
    reading can take from a buffer, and every other file on disk (unit L,
    Task 14). None otherwise, a reading of new texts pending among them."""
    outcome = trellis_outcome.value
    if outcome is None or outcome.refusal is None or trellis_shown.value is None:
        return None
    texts = _texts_within(unsaved_texts(), outcome.takeable)
    return outcome if trellis.file_digests(outcome.files, texts) == outcome.files else None


def _drop_properties(held, texts: dict) -> tuple[dict | None, list | None]:
    """The graph region's properties `stages` and `adds` for the trellis
    `held`, read with the mapping of unsaved texts `texts` (spec 0.4 §§3.5,
    3.6): the records of the stage list (`trellis.stage_items`) and the `+
    period` controls (`trellis.period_controls`), for a trellis written as
    records and for a trellis read from a recipe whose writers can extend it
    (`creation.can_add`, which asks for the recipe and the trellis file it
    names); None and None for a recipe they cannot extend, so that no drop
    is offered that only a refusal would answer."""
    if held.source.kind == "recipe" and not creation.can_add(
        tab_folder.value.root, Path(held.source.path).name, texts
    ):
        return None, None
    return trellis.stage_items(tab_folder.value, held, texts), trellis.period_controls(held)


# The gesture of the trellis graph between its events (spec 0.4 §3.3; brief
# rule 6, J-D12; ruling J-P6), as `switching` holds a file: {"event",
# "kind", "step", "gesture", "n", "open", "made"}, the event's record, or
# for a form's button the form's writer as a function of the mapping of
# unsaved texts (`_submit_form`); its kind, `connected` for a drag between
# two ports, `dropped` for a drop, `form` for a form's button, `removed`
# and `moved` for a join wire removed or one of its ends moved (J-D33),
# `occurrence removed` for a stage occurrence removed from its period (unit
# K's decision K-D14), `renamed` for the reading field of a join by
# equal names renamed (unit L, Task 15), and `stage removed` and `period
# removed` for a stage or a period removed from the model (unit L, Task
# 25); the step it waits at, `event`
# before the editor is asked for its text, `flushed` until the editor's
# change event, `confirming` until the editor's answer
# to a request that confirms the open document before the edits of closed
# files are applied (J-D36), and `asked` until the editor's answer to the
# request of the open document's edit, or of a confirmation where the open
# document takes no edit; the `trellis.Gesture` the query answered and the
# counter of the request asked of the editor, each None before it is
# asked; the open file, relative to the folder, when the editor was asked,
# None where none was open; and the moment of the event
# (`time.monotonic`). A gesture whose closed files' edits were applied
# before the open document's edit was asked also holds `undo`, what
# `_undo_closed` needs to take them back (J-D36); a gesture asked of the
# editor holds `standing`, the outcome of the refused reading on whose last
# constructed graph a drop was made, None for any other (unit L, Task 14;
# `_gesture_inputs_current`). None while no gesture waits.
gesturing = solara.reactive(None)
# The status line's text of the last gesture that wrote, {"sentence",
# "made"}, `made` the moment it was written; or None (brief rule 7; J-D20).
# A save that writes a file clears it (`on_save`; unit K, Task 13).
gesture_note = solara.reactive(None)
# The Workbench's sentence of the last gesture that wrote nothing,
# {"sentence", "file", "line", "made"}: the file the sentence names,
# relative to the folder, the line of the address it names there, None
# where it names none, and the moment of the refusal; or None. It stands in
# the list under the error mark and nowhere else (brief rule 8; J-D20).
gesture_refusal = solara.reactive(None)
# The gestures of the tab that wrote and edited several files, oldest first,
# at most GESTURE_STEPS (unit L, Task 17; defect 6 of the UX simulation):
# each {"key", "folder", "files", "undone"}, `key` the number with which the
# editor's undo history marks the gesture's step in the file that was open,
# `folder` the tab's model folder when the gesture wrote, `files` each file
# the gesture edited, relative to that folder, with its text before and
# after the gesture, and `undone` whether an undo took the gesture back.
# One undo in any of those files takes it back in all of them
# (`on_gesture_undo`).
gesture_steps = solara.reactive(())
# The undo of a gesture asked of the editor while its answer waits, {"n",
# "key", "path"}: the request's counter, the gesture's key and the open
# file; or None (`on_gesture_undo`).
gesture_undoing = solara.reactive(None)
# the keys of the gestures that edit several files, or that list files to
# delete on save
_gesture_keys = itertools.count(1)
# the most gestures `gesture_steps` keeps, the number of steps the editor's
# undo history keeps (CodeMirror's `minDepth`)
GESTURE_STEPS = 100
# The files and folders of the tab's folder that a save deletes from disk
# (unit L, Task 25; AAS, L-D18), each (path, key): the path relative to the
# folder in posix form, a folder's without "/" at its end, and the key of
# the gesture of `gesture_steps` that listed it, `remove stage` or `remove
# period`, whose undo withdraws it, or None for one the tree's `remove`
# marked. A save deletes each that no file of the folder then names, on
# disk or in a buffer (`_delete_on_save`); the tree draws each dimmed with
# `deleted on save`; `open_model` empties it.
deleting = solara.reactive(())
# the accessible name of the tree's control that marks a file to delete on
# the next save, the Codicon `trash`, and the words of the one that
# withdraws the mark, each with a capital (unit L, Task 25; design pass 8
# §§3 and 8, item 1)
REMOVE_FILE = "Remove"
KEEP_FILE = "Keep"


def withdraw_gesture() -> None:
    """Withdraws the gesture of the graph that waits between its events, so
    that no later event of the editor continues it (brief rule 6): called
    where the source, the graph or the restriction changes, the trellis view
    left for a stage's view included (`show_stage`), and where the trellis's
    task records a trellis of another elaboration number. A writer's
    gesture, a form's or the Recipe tab's (`WRITERS`), which reads no
    graph, is not withdrawn here, nor a gesture whose closed
    files' edits are applied and which waits for the editor's answer to the
    open document's edit, whose comparison with the graph is done (J-D36),
    since the reading of those edits gives the trellis another number;
    `_clear_gestures` withdraws both at a change of source, and takes back
    the closed files' edits and the new files of a gesture that holds
    `undo`. A removal withdrawn so leaves the sentence "An old graph",
    which asks for it to be made again, in the list under the error mark,
    since nothing was written (`_old_graph`; unit N, Task 5). The join wire
    selected, whose record names the graph left or an earlier reading, is no
    longer selected (`chosen_join`)."""
    chosen_join.value = None
    held = gesturing.value
    if held is not None and held["kind"] not in WRITERS and "undo" not in held:
        gesturing.value = None
        shown = trellis_shown.value
        if _removal(held) is not None and shown is not None:
            gesture_refusal.value = _gesture_refusal(*_old_graph(shown, held), None)


def _clear_gestures() -> None:
    """Withdraws the gesture that waits, a form's included, and clears the
    note, the sentence and the text of the last gesture and the join wire
    selected, which name files and lines of the source left: called at a
    change of source
    (`_clear_trellis`), whose caller holds LOOP_LOCK. A gesture whose closed
    files' edits are applied has them and its new files taken back first
    (`_undo_closed`; J-D36), so that it leaves nothing written."""
    held = gesturing.value
    if held is not None and "undo" in held:
        _undo_closed(held)
    gesturing.value = None
    gesture_note.value = None
    gesture_refusal.value = None
    gesture_made.value = None
    chosen_join.value = None


def _begin_gesture(
    event, kind: str, opens: str | None = None, saves: bool = False, refuse=None
) -> None:
    """Makes `event`, of the kind `kind`, the gesture that waits, in place
    of one that waits still (unit J's plan, review focus 5), clears the note
    and the sentence of the last gesture, and takes the gesture's first step
    (`continue_gesture`). `opens` is the file, relative to the folder, that
    the gesture opens in the editor once it has written, None for none
    (`_after_written`); `saves` true writes each file the gesture edits to
    disk once it has written (`_save_written`; unit L, Task 17); `refuse`,
    for a gesture of the kind `recipe`, is called with the sentence of its
    refusal (`_refuse_writer`; design pass 9 §4). A gesture
    replaced whose closed files' edits are applied has them and its new
    files taken back first (`_undo_closed`; J-D36), in the holding of
    LOOP_LOCK in which it is replaced, so that the editor's answer to its
    last request finds it withdrawn. In a saved copy of a job's returned
    files no gesture begins: the reason stands in the list under the error
    mark, in the form for a form's gesture, and at its control for the
    Recipe tab's (`refuse`) (`model.read_only`; amendment 06 §2 item 21)."""
    refusal = model.read_only(tab_folder.value)
    if refusal is not None:
        gesture_note.value = None
        gesture_refusal.value = {
            "sentence": refusal, "file": None, "line": None, "made": time.monotonic()
        }
        if kind == "form":
            form_error.value = refusal
        if refuse is not None:
            refuse(refusal)
        return
    with LOOP_LOCK:
        held = gesturing.value
        if held is not None and "undo" in held:
            _undo_closed(held)
        gesture_note.value = None
        gesture_refusal.value = None
        gesturing.value = {
            "event": event,
            "kind": kind,
            "step": "event",
            "gesture": None,
            "n": None,
            "open": None,
            "opens": opens,
            "saves": saves,
            "refuse": refuse,
            "made": time.monotonic(),
        }
    continue_gesture("event")


def on_connected(data: dict) -> None:
    """The graph region's event `connected` (spec 0.4 §3.2; J-D17): the
    record of a drag from an unjoined writing port to a reading port of the
    forward trellis graph, `{reading, source, target, sourceHandle,
    targetHandle}`, or of the button `join` of the list a drag between two
    frames opens, `{reading, source, target, pairs}` (unit K's decision
    K-D8), becomes the gesture that waits (`_begin_gesture`)."""
    _begin_gesture(data, "connected")


# What a drop on the forward trellis graph filled in of the form it opened
# (spec 0.4 §§3.5, 3.6; unit J's plan, Task 15): for "add stage" `{template,
# period, entry}`, the template, the name in the factory's folder of the file
# that writes the period's list and the entry's address there, or, opened by
# the item `From a folder…`, `{folder, period, entry}`, the folder of the
# disk its chooser opens on in place of the template (K-D26), and, opened by
# that item in the list the button `stages` opens, `{folder, periods}`, each
# period drawn as `{name, period, entry}`, the terminal period first, among
# which the form's select chooses the period's list (AAS, L-D5); for "add
# period" `{head, at, keys}`, the heading's place, `before periods[5]` or
# `between periods[3] and periods[2]`, the index the new period takes, None
# at the earliest end, and the stages chosen; None for a form opened
# otherwise. `open_form` sets it and `close_form` clears it.
form_fill = solara.reactive(None)


# The join wire of the forward trellis graph selected in the region (unit
# J's decisions J-D33 and J-D39; amendment 02, ruling 11): {"reading",
# "join"}, the record of the reading the region was given and the wire's
# record (`trellis.join_wires`), which Details shows; or None. The region's
# event `join-chosen` sets it, and a box selected, a change of graph, of
# restriction or of elaboration number and a change of source clear it.
chosen_join = solara.reactive(None)
# the label of the button of Details that removes the join wire selected
# (amendment 02, §6, the word of J-D33, with its capital; design pass 8 §8,
# item 1)
REMOVE = "Remove"
# the four ids by which an event names a join wire, its nodes and its ports
# in the graph JSON (J-D33)
JOIN_IDS = ("source", "sourceHandle", "target", "targetHandle")


def on_join_chosen(data: dict) -> None:
    """The graph region's event `join-chosen` (J-D33, J-D39): a join wire
    of the forward trellis graph, or a cable of the backward graph (design
    pass 10 §8), selected, `{reading, join}` with the wire's record, becomes
    the subject of Details, the box selected before no longer selected; a
    selection that left the wire, its `join` null, ends it."""
    join = data.get("join") if isinstance(data, dict) else None
    if not isinstance(join, dict):
        chosen_join.value = None
        return
    chosen_join.value = {"reading": data.get("reading"), "join": join}
    selected.value = None


def on_removed(data: dict) -> None:
    """The graph region's event `removed` (J-D33; amendment 02, ruling 12):
    Backspace or Delete on the join wire selected, while the region holds
    the focus, `{reading, join}`, becomes the gesture that waits
    (`_begin_gesture`), which takes the join's entry out of its file
    through the editor as a connector's line is typed
    (`trellis.removal_edit`); on the card of a stage occurrence selected,
    closed or compact, `{reading, occurrence}` (unit K's decision K-D14;
    unit N, Task 5), it becomes a gesture of the kind `occurrence removed`,
    which takes the stage's key out of the list that writes its period by
    the same route (`trellis.occurrence_removal_edit`). The region sends
    the occurrence, or the cable of the backward graph selected, `{reading,
    join}` (unit N, Task 7, N-I192), with no reading where the gesture
    cannot act, the graph shown being no live forward trellis graph;
    nothing is then written, and one sentence stands in the list under the
    error mark (`_refuse_backspace`; N-D12)."""
    occurrence = isinstance(data, dict) and "occurrence" in data
    if isinstance(data, dict) and not isinstance(data.get("reading"), dict):
        _refuse_backspace(data.get("occurrence"))
        return
    _begin_gesture(data, "occurrence removed" if occurrence else "removed")


# the sentence under the error mark where Backspace on a selected stage
# occurrence or cable cannot act, the graph shown not being the forward
# trellis graph (unit N, Tasks 5 and 7; N-D12)
BACKSPACE_FORWARD = "Backspace acts in the forward trellis view"


def _refuse_backspace(occurrence) -> None:
    """Backspace or Delete on the stage occurrence whose layer's id is
    `occurrence`, `periods[2]/port___group___`, or, `occurrence` None, on a
    cable of the backward graph (unit N, Task 7), where the region could
    not act (unit N, Task 5; N-D12): nothing is written, and one sentence
    stands in the list under the error mark in place of the note of the
    last gesture. In the forward trellis view, where the gesture waits for
    a reading that is not refused, the sentence of `remove stage` that
    cannot act (`stage_not_removed`) names the stage and why; in any other
    view, and for a cable, `Backspace acts in the forward trellis view`."""
    found = trellis.OCCURRENCE_LAYER.fullmatch(occurrence) if isinstance(occurrence, str) else None
    forward = view_mode.value == "trellis" and graph.value == "forward"
    if forward and found is not None:
        sentence = stage_not_removed(found[2])
    else:
        sentence = BACKSPACE_FORWARD
    gesture_note.value = None
    gesture_refusal.value = _gesture_refusal(sentence, None, None)


def remove_occurrence(position) -> None:
    """The control `Remove from periods` of Details of a stage occurrence
    (unit N, Task 5; design pass 10 §7): the occurrence `position`, `(h,
    key)`, taken out of the list that writes its period, as Backspace on
    its selected card takes it, a gesture of the kind `occurrence removed`
    named by the reading the trellis view holds
    (`trellis.occurrence_removal_edit`), whose list being the stage's last
    takes the recipe's row too (N-D8). Where the gesture cannot act, since
    the trellis view holds no reading or the last reading stands refused,
    nothing is written and the sentence `stage_not_removed` stands in the
    list under the error mark, as for `remove stage` (AAS, M-D2)."""
    h, key = position
    held = trellis_shown.value
    if held is None or _trellis_stale():
        gesture_note.value = None
        gesture_refusal.value = _gesture_refusal(stage_not_removed(key), None, None)
        return
    event = {
        "reading": trellis.reading_record(tab_folder.value, held),
        "occurrence": f"periods[{h}]/{key}{LAYER_ID_ENDING}",
    }
    _begin_gesture(event, "occurrence removed")


def on_moved(data: dict) -> None:
    """The graph region's event `moved` (J-D33; amendment 02, ruling 14): an
    end of a join wire of one entry dragged to another port of its side,
    `{reading, join, end, handle}`, or the button `join` of the list that
    such a drag of an end of a wire of several entries opens, `{reading,
    join, end, pairs}`, the field pairs ticked (unit K's decision K-D23),
    becomes the gesture that waits (`_begin_gesture`), which replaces the
    entries moved by the new lines in one edit of each buffer
    (`trellis.removal_edit`)."""
    _begin_gesture(data, "moved")


def remove_join() -> None:
    """The button `remove` of Details (J-D33; amendment 02, ruling 11): the
    join wire selected (`chosen_join`) removed as Backspace removes it, a
    gesture of the kind `removed` named by the wire's four ids."""
    held = chosen_join.value
    if held is None:
        return
    event = {"reading": held["reading"], "join": {name: held["join"][name] for name in JOIN_IDS}}
    _begin_gesture(event, "removed")


def remove_stage(key: str) -> None:
    """The button `remove stage` of a stage's row of the Recipe tab and of
    Details of one of its occurrences (unit L, Task 25; AAS, L-D18; design
    pass 9 §4):
    the stage `key` removed from the model, a gesture of the kind `stage
    removed` named by the reading the trellis view holds, which takes its
    row, its key in every period's list, its connectors and answers.yml's
    records out of the files' texts in one change of the buffers
    (`trellis.stage_removal_edit`), its folder and the files only its row
    named listed to delete on save. Where the gesture cannot act, since the
    trellis view holds no reading or the last reading stands refused,
    nothing is written, and the page's sentence `stage_not_removed` stands
    in the list under the error mark at the line of the stage's row in the
    recipe, in place of the note of the last gesture (AAS, M-D2)."""
    held = trellis_shown.value
    if held is None or _trellis_stale():
        chosen = source.value
        file = _resolved(chosen.path) if chosen is not None else None
        gesture_note.value = None
        gesture_refusal.value = _gesture_refusal(stage_not_removed(key), file, ("stages", key))
        return
    event = {"reading": trellis.reading_record(tab_folder.value, held), "stage": key}
    _begin_gesture(event, "stage removed")


def stage_not_removed(key: str) -> str:
    """The page's sentence where `remove stage` of the stage `key` cannot
    act (AAS, M-D2): the recipe shown, what was not done, why, and what to
    do, `spec.yml: bequest was not removed, since the trellis of spec.yml
    stands refused; remove bequest again once the trellis is drawn`, the
    reason `stands refused` while the last reading of the trellis is
    refused, whose refusal stands in the same list, and `is still being
    read` while no reading has answered."""
    chosen = source.value
    name = Path(chosen.path).name if chosen is not None else "the recipe"
    why = "stands refused" if _trellis_stale() else "is still being read"
    return (
        f"{name}: {key} was not removed, since the trellis of {name} {why}; "
        f"remove {key} again once the trellis is drawn"
    )


def remove_period(h: int) -> None:
    """The button `remove period` of Details of a selected period (unit L,
    Task 25; AAS, L-D18): periods[h] removed from the trellis, a gesture of
    the kind `period removed` named by the reading the trellis view holds,
    which takes its entry out of the trellis file's text, or lowers its
    repeat, and lowers the recipe's ranges in one change of the buffers
    (`trellis.period_removal_edit`), its period file listed to delete on
    save where no other entry names it."""
    held = trellis_shown.value
    if held is None:
        return
    event = {"reading": trellis.reading_record(tab_folder.value, held), "period": h}
    _begin_gesture(event, "period removed")


def rename_join(field: str, name: str) -> None:
    """The button `rename` of Details (unit L, Task 15; defect 3 of the UX
    simulation): the arrival field `field` of the join wire selected
    (`chosen_join`), which a join of the wire reaches by equal names,
    renamed `name`, the name typed in Details, in the reading stage's file,
    a gesture of the kind `renamed` named by the wire's four ids, which
    writes the file's unsaved text as every edit does
    (`trellis.rename_edit`)."""
    held = chosen_join.value
    if held is None:
        return
    event = {
        "reading": held["reading"],
        "join": {key: held["join"][key] for key in JOIN_IDS},
        "field": field,
        "name": name,
    }
    _begin_gesture(event, "renamed")


def on_dropped(data: dict) -> None:
    """The graph region's event `dropped` (spec 0.4 §3.2; J-D17; ruling
    J-P4): the record of a stage of the stage list dropped on a period or a
    `+ period` control, or of Enter on a control, `{item, kind, target,
    reading}`, becomes the gesture that waits (`_begin_gesture`), which
    calls `trellis.drop_edits` once the editor has given its text and
    applies its edits as a connector's, or opens the form it answers
    (`_ask_editor`)."""
    _begin_gesture(data, "dropped")


def _submit_form(write, opens: str | None = None, saves: bool = False) -> None:
    """A form's button as a gesture of the kind `form` (spec 0.4 §3.5,
    §3.6; brief rule 9; unit J's plan, Task 11): `write`, the creation
    unit's writer as a function of the mapping of unsaved texts, which
    answers a `creation.Added`, becomes the gesture that waits, with no
    refusal standing in the form. The writer is called once the editor has
    given its text (`_form_gesture`), so that it reads the open document as
    the reader typed it, and its edits meet the checks of a gesture: the
    open file's edit is asked of the editor with the text it was made from,
    each other file's is applied to its buffer where the buffer holds that
    text (`apply_edits`), and the new files are written to disk only after
    both. The form closes once the edits are applied, and every refusal
    stands in the form. Where `opens` names a file, relative to the folder,
    the editor opens it once the form has written, as "new stage" opens its
    stage file (unit K's decision K-D7); where `saves` is true, the files the
    form edits are written to disk with the new files, as "new stage" writes
    the recipe's row with its stage file (unit L, Task 17)."""
    form_error.value = ""
    _begin_gesture(write, "form", opens, saves)


def continue_gesture(at: str) -> None:
    """The seven steps of the gesture that waits (spec 0.4 §3.3; brief rule
    6, J-D6), called at each of its events, `at` naming the event: `event`,
    the region's event (`on_connected`) or a form's button
    (`_submit_form`); `change`, the editor's change event, once `on_change`
    has taken the editor's text; and `applied`, the editor's answer, once
    `on_applied` has recorded it. An event the gesture does not wait for
    changes nothing.

    1. At `event`, with a file open, the editor is asked for its text
       (`flush_request`); with none open, steps 2 to 7 follow at once.
    2 to 5. At the editor's change event, `_ask_editor`: the query, or a
       form's writer, answers the edits or a sentence; the inputs are
       compared again under LOOP_LOCK; and the edit is asked of the editor,
       or, with no file open, applied to the buffers with the new files
       written (`apply_edits`).
    6 and 7. At the editor's answer to that request, `_take_answer`: on a
       true answer the edits of closed files are applied to their buffers,
       the new files written, and the status line's note is written;
       otherwise nothing is written and the sentence stands in the list
       under the error mark, or in the form for a form's gesture. A gesture
       that edits the open document and closed files or writes new files
       asks the editor twice (J-D36): first to confirm the open document,
       on whose true answer the closed files' edits are applied and the new
       files written (`_take_confirmation`), then for the open document's
       own edit, last."""
    held = gesturing.value
    if held is None:
        return
    if at == "event" and held["step"] == "event":
        if open_path.value is None:
            _ask_editor(held)
            return
        gesturing.value = {**held, "step": "flushed"}
        flush_request.value = flush_request.value + 1
    elif at == "change" and held["step"] == "flushed":
        _ask_editor(held)
    elif at == "applied" and held["step"] in ("confirming", "asked"):
        answer = edit_answer.value
        if answer is not None and answer["n"] == held["n"]:
            _take_answer(held, answer["applied"])


def _resolved(path: str) -> str:
    """The resolved path, as a string, of the file `path`, relative to the
    folder: the key of the mapping of unsaved texts and of a `Gesture`'s
    edits (ruling J-P6)."""
    return str((tab_folder.value.root / path).resolve())


def _old_graph(shown, held: dict) -> tuple[str, str]:
    """The sentence "An old graph" of brief §5 and the file it names, the
    trellis file of the reading `shown`, by its resolved path, for the
    gesture `held`, whose last sentence asks for a removal to be made again
    where `held` removes a join or a stage occurrence (`_removal`), and for
    the field to be renamed again where `held` renames the reading field of
    a join by equal names (unit L, Task 15)."""
    file = str(Path(shown.trellis["provenance"]["trellis"]["path"]).resolve())
    place = trellis.Gesture(None, None, (), None, None, file, None)
    renamed = held["kind"] == "renamed"
    return trellis.gesture_sentence("old-graph", place, None, None, _removal(held), renamed), file


# what a gesture of each kind that removes removes, which its sentences ask
# to remove again: a join (J-D33), a stage occurrence (unit K's decision
# K-D14), or a stage or a period of the model (unit L, Task 25)
REMOVED = {
    "removed": "join",
    "occurrence removed": "stage",
    "stage removed": "stage",
    "period removed": "period",
}


def _removal(held: dict) -> str | None:
    """What the gesture `held` removes from the trellis, `join` for the
    kind `removed` (J-D33), `stage` for the kinds `occurrence removed`
    (unit K's decision K-D14) and `stage removed`, and `period` for the kind
    `period removed` (unit L, Task 25); None for a gesture of any other
    kind, a drag among them (unit J's plan, Task 17)."""
    return REMOVED.get(held["kind"])


def _refuse_gesture(sentence: str, file: str | None, address: str | None) -> None:
    """Ends the gesture that waits with the Workbench's `sentence`, which
    stands in the list under the error mark (`gesture_refusal`; brief rule
    8), at its file and line (`_gesture_refusal`); nothing is written."""
    gesture_refusal.value = _gesture_refusal(sentence, file, address)
    gesturing.value = None


def _gesture_refusal(sentence: str, file: str | None, address) -> dict:
    """The record of `gesture_refusal` for the Workbench's `sentence`,
    linked to the file `file`, a resolved path, at the line of the address
    `address` written there, a text or a sequence of keys and indices,
    counted in the text of the file's unsaved buffer where the tab holds
    one, with the moment it is made."""
    folder = tab_folder.value
    texts = trellis.texts_of(unsaved_texts())
    place = trellis.address_place(folder, file, address, False, texts=texts)
    return {
        "sentence": sentence,
        "file": recipe.relative(folder, file) if file else None,
        "line": place[1] if place is not None else None,
        "made": time.monotonic(),
    }


def apply_edits(edits: dict, read: dict, new_files=()) -> str | None:
    """With LOOP_LOCK held by its caller, in the one holding in which the
    caller compared the inputs, the edits of files the editor does not hold
    and the new files of a gesture (spec 0.4 §3.3: a destination not yet
    buffered is read and compared with the recorded disk input; §3.5; unit
    J's plan, Tasks 10 and 11; rulings J-P5 and J-P6): each new text of
    `edits`, by its file's resolved path, applied to the file's buffer,
    whose revision rises by one, where the buffer's text is the text the
    edit was made from, `read`; for a file not yet buffered, read from disk
    (`model.read_file`) and compared with that text, a new buffer holding
    the new text and the disk's digest, so that the tree marks it unsaved;
    and each new file of `new_files`, pairs (its path relative to the
    folder, its text), written to disk as a file that did not exist
    (`_write_new_files`). Every edit and every new file is checked before
    any edit is applied or any file written. Answers None where all were
    applied and written; otherwise nothing is applied or written, and the
    answer is the path, relative to the folder, of the first file that holds
    another text than its edit was made from or, for a new file, that stands
    on disk, the caller writing the sentence (`_not_written`). Once they are
    applied the checklist is read again from the buffers
    (`read_checklist`)."""
    folder = tab_folder.value
    taken = {}
    for path, text in edits.items():
        name = recipe.relative(folder, path)
        held = buffers.value.get(name)
        if held is not None:
            if held["text"] != read[path]:
                return name
            taken[name] = {**held, "text": text, "revision": held["revision"] + 1}
            continue
        try:
            found = model.read_file(folder, name)
        except OSError:
            return name
        if found.text != read[path]:
            return name
        taken[name] = {
            "text": text,
            "revision": 1,
            "digest": found.digest,
            "document": text,
            "document_revision": next(_document_numbers),
        }
    standing = next((name for name, _ in new_files if (folder.root / name).exists()), None)
    if standing is not None:
        return standing
    refused = _write_new_files(folder, new_files)
    if refused is not None:
        return refused
    buffers.value = {**buffers.value, **taken}
    read_checklist()
    return None


def _new_folders(root: Path, new_files) -> list[Path]:
    """The folders under the model folder `root` that hold a new file of
    `new_files`, pairs (its path relative to the folder, its text), and do
    not exist yet, which writing the files makes, the deepest first."""
    return sorted(
        {
            parent
            for name, _ in new_files
            for parent in (root / name).parents
            if parent.is_relative_to(root) and not parent.exists()
        },
        key=lambda parent: len(parent.parts),
        reverse=True,
    )


def _remove_new_files(root: Path, names, folders) -> None:
    """Removes the files `names`, by their paths relative to the model folder
    `root`, that a gesture wrote, and then each folder of `folders`, the
    deepest first, that the gesture made for them and that holds nothing
    else."""
    for name in names:
        (root / name).unlink(missing_ok=True)
    for parent in folders:
        try:
            parent.rmdir()
        except OSError:
            # a folder that holds a file this gesture did not write
            pass


def _write_new_files(folder: model.Folder, new_files) -> str | None:
    """Writes each new file of `new_files`, pairs (its path relative to the
    folder, its text), through `model.save_file` as a file that does not
    exist, the folders that hold it made; answers None where all were
    written. Where a file appears on disk before it is written, the files
    written before it and the folders made for them are removed and its
    path is answered, so that a refused gesture leaves no new file (unit J's
    plan, Task 11, review focus 2)."""
    made = _new_folders(folder.root, new_files)
    written = []
    for name, text in new_files:
        if not model.save_file(folder, name, text, None).saved:
            _remove_new_files(folder.root, written, made)
            return name
        written.append(name)
    return None


def _gesture_written(held: dict, gesture) -> str | None:
    """Step 7 of the gesture `held` that wrote: the status line's note
    (`gesture_note`); for a gesture of the graph that edits one file and
    writes no new file, a connector's line, or a key appended to a period's
    list or taken out of it, that file with its text before and after the edit
    (`gesture_made`), which the action `take the line out` reads, since its
    text before is then all the gesture changed; a form's gesture, and a
    drop that edits several files or writes new ones, naming no file; for a
    gesture that edits several files, its step among the tab's gestures
    (`gesture_steps`), under the key its request to the editor carried or a
    new one, so that one undo takes it back in all of them (unit L, Task
    17), and so for a removal that lists files to delete on save, whose
    files then join `deleting` under that key, so that its undo withdraws
    them, `take the line out` not standing for it (unit L, Task 25); and so
    for a gesture that edits one file the editor did not hold open, whose
    undo history then holds no step of it, so that Mod-z in that file once
    it opens takes the gesture back (`on_gesture_undo`; unit N, Task 5);
    for a gesture that `saves`, each file it edited written to disk
    (`_save_written`); and no gesture waiting. Answers the sentence of a
    file the gesture saves that could not be written, which the form then
    shows in place of the note, and None otherwise (unit L's final
    judgment, §6 item 6). Called with LOOP_LOCK held."""
    refusal = _save_written(gesture) if held.get("saves") else None
    if refusal is None:
        gesture_note.value = {"sentence": gesture.note, "made": time.monotonic()}
    single = len(gesture.edits) == 1 and not gesture.new_files and not gesture.deleted
    if held["kind"] not in WRITERS and single:
        gesture_made.value = {
            "path": recipe.relative(tab_folder.value, gesture.file),
            "before": gesture.read[gesture.file],
            "after": gesture.edits[gesture.file],
        }
    # a file the editor did not hold open when the gesture wrote, whose edit
    # its undo history therefore does not hold (unit N, Task 5)
    closed = any(
        recipe.relative(tab_folder.value, path) != held.get("open") for path in gesture.edits
    )
    if len(gesture.edits) > 1 or gesture.deleted or closed:
        folder = tab_folder.value
        step = {
            "key": held.get("key") or next(_gesture_keys),
            "folder": folder,
            "files": {
                recipe.relative(folder, path): (gesture.read[path], text)
                for path, text in gesture.edits.items()
            },
            "undone": False,
            "deleted": tuple(gesture.deleted),
        }
        gesture_steps.value = (*gesture_steps.value, step)[-GESTURE_STEPS:]
        _mark_deleted(step["deleted"], step["key"], True)
    gesturing.value = None
    return refusal


def _save_written(gesture) -> str | None:
    """With LOOP_LOCK held by its caller, once the gesture `gesture` wrote:
    each file it edited written to disk with the text the gesture made
    (`model.save_file`), where the file on disk is the one its buffer was
    read from, and its buffer then holding that text and the new digest,
    so that no tab reads `unsaved`; "new stage" saves the recipe's row with
    the stage file it writes (unit L, Task 17; defect 22 of the UX
    simulation), its writer refusing a file that held unsaved text. A file
    changed on disk meanwhile is not written, and its buffer stays
    unsaved; the answer is then the sentence `<file>: the file changed on
    disk` of the first such file, `model.save_file`'s reason, and None
    where every file was written (unit L's final judgment, §6 item 6)."""
    folder = tab_folder.value
    taken = dict(buffers.value)
    refusal = None
    for path, text in gesture.edits.items():
        name = recipe.relative(folder, path)
        held = taken.get(name)
        if held is None:
            continue
        result = model.save_file(folder, name, text, held["digest"])
        if result.saved:
            revision = held["revision"] + (held["text"] != text)
            taken[name] = {**held, "text": text, "revision": revision, "digest": result.digest}
        elif refusal is None:
            refusal = f"{name}: {result.reason}"
    buffers.value = taken
    return refusal


def _after_written(
    kind: str, gesture, opens: str | None = None, refusal: str | None = None
) -> None:
    """After the gesture `gesture` of the kind `kind` wrote, with LOOP_LOCK
    released: a form's gesture closes its form, unless a file it saves
    could not be written, `refusal`, the sentence that then stands in the
    form, which stays open and opens no file (`_save_written`; unit L's
    final judgment, §6 item 6); a form's gesture or a gesture that wrote new
    files has the folder read again (`refresh_folder`), so that the tree
    shows the new files and marks the edited ones unsaved; where the gesture
    added a period between two periods, the text its writer answered for
    the restriction's input, `periods 2–4` or the empty text, is written
    there and applied (spec 0.4 §3.6, decision 28; `apply_restriction`),
    since the indices a restriction names have moved; a gesture of the graph
    opens its file at its line (`_show_written`; J-D40), where a writer's
    gesture, whose edit stands in the open file, opens nothing of its own;
    a gesture of the Recipe tab asks the editor for its text at once
    (`flush_request`), so that the recipe's buffer and the trellis's reading
    take the edit now rather than after the editor's pause, and an undo
    pressed within that pause is a change the buffer takes, which the
    tab's selects then follow (design pass 9 §4); and where the gesture
    names a file to open, `opens`, relative to the folder, that file opens
    as a click on it in the tree opens it (`open_from_tree`; unit K's
    decision K-D7)."""
    form = kind == "form"
    if kind == "recipe" and open_path.value is not None:
        flush_request.value = flush_request.value + 1
    if form and refusal is not None:
        _refuse_form(refusal)
    elif form:
        close_form()
    if form or gesture.new_files:
        refresh_folder()
    if gesture.restriction is not None:
        apply_restriction(gesture.restriction)
    if kind not in WRITERS:
        _show_written(gesture)
    if opens is not None and refusal is None:
        open_from_tree(opens)


def _show_written(gesture) -> None:
    """After a gesture of the graph that wrote (unit J's decision J-D40;
    amendment 02, recommendation 16): the file of its line, `gesture.file`,
    opens in the text pane at the line the gesture typed, changed or
    removed, the first line of the text it made that differs from the text
    read (`trellis.typed_line`), that line's text selected and the graph as
    it stands, so that the reader sees the edit as text; the editor's undo
    reaches the edit where the file was open, and a file the gesture opened
    takes the edit as text and not into its undo history (R-D45), Mod-z
    there taking back the gesture's step among the tab's gestures
    (`_gesture_written`, `on_gesture_undo`; unit N, Task 5). A gesture
    that names no file, or does not edit the file it names, opens
    nothing."""
    if gesture.file is None or not gesture.edits or gesture.file not in gesture.edits:
        return
    # the editor's document holds "\n" where the file holds "\r\n"
    before, after = (
        texts[gesture.file].replace("\r\n", "\n") for texts in (gesture.read, gesture.edits)
    )
    line = trellis.typed_line(before, after)
    column, end_column = _line_extent(after, line)
    open_at(recipe.relative(tab_folder.value, gesture.file), line, column, (line, end_column))


def _form_gesture(held: dict):
    """Step 3 of a writer's gesture `held`, a form's (unit J's plan, Task
    11) or the Recipe tab's (design pass 9 §4): its writer (`_submit_form`,
    `_recipe_gesture`), given the tab's unsaved texts once the editor has
    given its text, and its answer, a `creation.Added`, as a
    `trellis.Gesture` with the writer's edits, texts read and new files,
    the status line its notes make joined by "; ", no file named, and the
    text for the restriction's input it answers; None where the writer
    refuses, its sentence then standing in the form or under the error mark
    (`_refuse_writer`)."""
    try:
        added = held["event"](trellis.texts_of(unsaved_texts()))
    except (ValueError, OSError) as error:
        _refuse_writer(held, str(error))
        return None
    note = "; ".join(added.notes)
    return trellis.Gesture(
        added.edits, added.read, added.new_files, note, None, None, None, added.restriction
    )


# the kinds of gesture whose writer, not a query of the graph, answers its
# edits: a form's (unit J's plan, Task 11) and the Recipe tab's (design pass
# 9 §4); such a gesture reads no graph, so that no change of the graph
# withdraws it and its inputs are compared where its edits are applied
WRITERS = ("form", "recipe")


def _refuse_writer(held: dict, sentence: str) -> None:
    """Ends the writer's gesture `held` with `sentence`, nothing written: a
    form's in the form (`_refuse_form`), the Recipe tab's under the error
    mark with its control marked (the gesture's `refuse`,
    `_refuse_choice`)."""
    if held["kind"] == "recipe":
        held["refuse"](sentence)
    else:
        _refuse_form(sentence)


def _refuse_form(sentence: str) -> None:
    """Ends the form's gesture that waits with `sentence`, which stands in
    the form (`form_error`), a form's own refusal standing there and nowhere
    else (A2-D13); nothing is written, apart from what a form that saves
    wrote before a file it saves was found changed on disk (`_save_written`),
    and the form stays open, the refusal counted (`form_refusals`; AAS,
    L-D5)."""
    form_error.value = sentence
    form_refusals.value += 1
    gesturing.value = None


def _not_written(held: dict, gesture, path: str) -> None:
    """Ends the gesture `held`, which wrote nothing because the file `path`,
    relative to the folder, held another text than its edit was made from:
    for a form's gesture, the sentence that names that file stands in the
    form; for a gesture of the graph, "An edit not applied" of brief §5 at
    the gesture's own file and address stands in the list under the error
    mark, in the words of a removal for a removal (`_not_applied`)."""
    if held["kind"] == "form":
        _refuse_form(
            f"{path}: nothing was written. The text changed after the form read it. "
            "Press the button again."
        )
    elif held["kind"] == "recipe":
        _refuse_writer(
            held,
            f"{path}: nothing was written. The text changed after the table read it. "
            "Make the change again.",
        )
    else:
        _refuse_gesture(_not_applied(gesture, held), gesture.file, gesture.address)


def _ask_editor(held: dict) -> None:
    """Steps 2 to 5 of the gesture `held` (spec 0.4 §3.3), at the editor's
    change event or, with no file open, at once. The query,
    `trellis.connector_edit` for a drag between two ports and
    `trellis.drop_edits` for a drop, given the trellis drawn and the tab's
    unsaved texts, compares every input with the event's reading and answers
    the edits or a sentence, or, for a drop, the form to open filled in,
    which ends the gesture (ruling J-P4); a sentence ends the gesture, and a
    gesture with neither writes and prints nothing (ruling J-P16). Under
    LOOP_LOCK the inputs are compared again with the texts that stand, a
    change answering the sentence "An old graph", and the edit is then
    asked, under the same holding: the one replacement that types the line
    where its file is the open file, with the text read as the document the
    editor must hold; no replacement and the open document otherwise, the
    editor's answer then saying whether that document still holds the text
    Python read (J-D6).
    With no file open the edits are applied to the buffers at once, and the
    new files written (`apply_edits`). For a form's gesture the writer takes
    the place of the query (`_form_gesture`), and since a form reads no
    graph, the comparison is that of each file the writer read, made where
    its edit is applied. A drop made while the last reading stands refused,
    on the last graph the package constructed (`_refused_standing`; unit L,
    Task 14), is asked of `trellis.drop_edits` with `refused`, and its
    comparison under LOOP_LOCK is that the same refused reading stands and
    every file it read still holds the text it read, since the texts differ
    from those the graph was drawn from."""
    # a writer's gesture, a form's or the Recipe tab's, reads no graph
    form = held["kind"] in WRITERS
    shown = None if form else trellis_shown.value
    standing = None
    if form:
        gesture = _form_gesture(held)
        if gesture is None:
            return
    elif shown is None:
        gesturing.value = None
        return
    else:
        texts = trellis.texts_of(unsaved_texts())
        if held["kind"] == "dropped":
            standing = _refused_standing()
            gesture = trellis.drop_edits(shown, held["event"], texts, refused=standing is not None)
        else:
            query = {
                "removed": trellis.removal_edit,
                "moved": trellis.removal_edit,
                "occurrence removed": trellis.occurrence_removal_edit,
                "renamed": trellis.rename_edit,
                "stage removed": trellis.stage_removal_edit,
                "period removed": trellis.period_removal_edit,
            }.get(held["kind"], trellis.connector_edit)
            gesture = query(shown, held["event"], texts)
        if isinstance(gesture, dict):
            # a drop that opens a form filled in (ruling J-P4)
            gesturing.value = None
            open_form(gesture["form"], gesture["fill"])
            return
        if gesture.sentence is not None:
            _refuse_gesture(gesture.sentence, gesture.file, gesture.address)
            return
    if not gesture.edits:
        gesturing.value = None
        return
    # what follows the holding of LOOP_LOCK: a refusal, or a form closed
    after = None
    with LOOP_LOCK:
        if gesturing.value is not held:
            # withdrawn while the query ran
            return
        if not form and (
            trellis_shown.value is not shown
            or not _gesture_inputs_current({**held, "standing": standing}, shown)
        ):
            after = functools.partial(_refuse_gesture, *_old_graph(shown, held), None)
        elif open_path.value is None:
            failed = apply_edits(gesture.edits, gesture.read, gesture.new_files)
            if failed is None:
                refusal = _gesture_written(held, gesture)
                after = functools.partial(
                    _after_written, held["kind"], gesture, held.get("opens"), refusal
                )
            else:
                after = functools.partial(_not_written, held, gesture, failed)
        else:
            opened = open_path.value
            own = gesture.edits.get(_resolved(opened))
            step = "asked"
            if own is None:
                edits, expected = [], buffers.value[opened]["text"].replace("\r\n", "\n")
            elif len(gesture.edits) > 1 or gesture.new_files:
                # the open document confirmed first and its own edit asked
                # last, after the closed files' edits (J-D36)
                edits, step = [], "confirming"
                expected = gesture.read[_resolved(opened)].replace("\r\n", "\n")
            else:
                expected = gesture.read[_resolved(opened)].replace("\r\n", "\n")
                edits = [trellis.restoring_edit(own.replace("\r\n", "\n"), expected)]
            n = _counter(edit_request.value)
            request = {"edits": edits, "expected": expected, "n": n}
            # the open document's own edit of a removal that lists files to
            # delete on save is marked with the gesture's key, so that its
            # undo withdraws them (unit L, Task 25)
            key = next(_gesture_keys) if edits and gesture.deleted else None
            if key is not None:
                request["gesture"] = key
            edit_request.value = request
            gesturing.value = {
                **held,
                "step": step,
                "gesture": gesture,
                "n": n,
                "open": opened,
                "standing": standing,
                "key": key,
            }
    if after is not None:
        after()


def _gesture_inputs_current(held: dict, shown) -> bool:
    """Whether the inputs of the graph's gesture `held` still hold the texts
    its query read, under LOOP_LOCK held by the caller (spec 0.4 §3.3): for
    a drop made on the last constructed graph while a reading stands
    refused, `held["standing"]` that reading's outcome (unit L, Task 14),
    that the same refused reading stands and every file it read holds the
    text it read (`_refused_standing`); otherwise that every input of the
    trellis `shown` holds the text its reading read
    (`trellis.inputs_current`)."""
    standing = held.get("standing")
    if standing is not None:
        return _refused_standing() is standing
    return trellis.inputs_current(shown, trellis.texts_of(unsaved_texts()))


def _not_applied(gesture, held: dict) -> str:
    """The sentence "An edit not applied" of brief §5 at the file and the
    address of `gesture`, for the gesture `held`, whose last sentence asks
    for a removal to be made again where `held` removes a join or a stage
    occurrence (`_removal`), and for the field to be renamed again where
    `held` renames the reading field of a join by equal names (unit L, Task
    15)."""
    renamed = held["kind"] == "renamed"
    return trellis.gesture_sentence("not-applied", gesture, None, None, _removal(held), renamed)


def _take_answer(held: dict, applied: bool) -> None:
    """Steps 6 and 7 of the gesture `held` (spec 0.4 §3.3; brief rule 7), at
    the editor's answer to its request. A false answer writes nothing, and
    the sentence that the open file's text changed stands
    (`_not_written`). On a true answer the edit of the file open when the
    editor was asked stands in the editor, which the buffer takes at the
    next change event; under one holding of LOOP_LOCK the inputs are
    compared once more with the texts that stand, where another file is
    edited and the gesture is the graph's, and each edit of another file is
    applied to its buffer and each new file written (`apply_edits`), a
    change of an input answering "An old graph" and a file that holds
    another text the sentence of `_not_written`, with nothing applied or
    written; then the status line's note is written (`_gesture_written`),
    a form closes and a period added between two periods writes the
    restriction's input (`_after_written`). The answer to a request that
    confirms the open document is `_take_confirmation`'s (J-D36); after it
    the closed files' edits stand applied, so that a true answer to the open
    document's edit writes the note alone, and a false answer takes those
    edits and the new files back (`_undo_closed`) before the sentence, so
    that nothing stands written."""
    gesture = held["gesture"]
    if held["step"] == "confirming":
        _take_confirmation(held, applied)
        return
    if not applied:
        if "undo" in held:
            with LOOP_LOCK:
                if gesturing.value is not held:
                    # withdrawn while the editor answered
                    return
                _undo_closed(held)
        _not_written(held, gesture, held["open"])
        return
    form = held["kind"] in WRITERS
    opened = _resolved(held["open"]) if held["open"] is not None else None
    # the edits of closed files and the new files, none where they were
    # applied before the open document's edit was asked (J-D36)
    closed = {path: text for path, text in gesture.edits.items() if path != opened}
    new_files = gesture.new_files
    if "undo" in held:
        closed, new_files = {}, ()
    after = None
    with LOOP_LOCK:
        if gesturing.value is not held:
            # withdrawn while the editor answered
            return
        # a change of source withdraws the gesture, so a trellis stands
        shown = trellis_shown.value
        if closed and not form and not _gesture_inputs_current(held, shown):
            after = functools.partial(_refuse_gesture, *_old_graph(shown, held), None)
        else:
            failed = None
            if closed or new_files:
                failed = apply_edits(closed, gesture.read, new_files)
            if failed is None:
                refusal = _gesture_written(held, gesture)
                after = functools.partial(
                    _after_written, held["kind"], gesture, held.get("opens"), refusal
                )
            else:
                after = functools.partial(_not_written, held, gesture, failed)
    if after is not None:
        after()


def _take_confirmation(held: dict, applied: bool) -> None:
    """Step 6 of a gesture that edits the open document and closed files or
    writes new files (J-D36; spec 0.4 §3.3, of a refusal nothing is
    written), at the editor's answer to the request that confirms the open
    document with no replacement. A false answer writes nothing
    (`_not_written`). On a true answer, under one holding of LOOP_LOCK, the
    inputs are compared once more for a gesture of the graph, a change
    answering "An old graph"; the closed files' edits are applied to their
    buffers and the new files written (`apply_edits`), a file that holds
    another text answering the sentence of `_not_written` with nothing
    applied or written; and the open document's own edit is then asked of
    the editor, last, the gesture keeping under `undo` the model folder, the
    buffers the closed files held, the new files and the folders made for
    them. Where the gesture edits several files, the request and the
    gesture carry the gesture's key, with which the editor marks the edit's
    step of its undo history (unit L, Task 17)."""
    gesture = held["gesture"]
    if not applied:
        _not_written(held, gesture, held["open"])
        return
    folder = tab_folder.value
    opened = _resolved(held["open"])
    closed = {path: text for path, text in gesture.edits.items() if path != opened}
    after = None
    with LOOP_LOCK:
        if gesturing.value is not held:
            # withdrawn while the editor answered
            return
        # a change of source withdraws the gesture, so a trellis stands
        shown = trellis_shown.value
        if held["kind"] not in WRITERS and not _gesture_inputs_current(held, shown):
            after = functools.partial(_refuse_gesture, *_old_graph(shown, held), None)
        else:
            names = [recipe.relative(folder, path) for path in closed]
            undo = {
                "folder": folder,
                "buffers": {name: buffers.value.get(name) for name in names},
                "files": [name for name, _ in gesture.new_files],
                "folders": _new_folders(folder.root, gesture.new_files),
            }
            failed = apply_edits(closed, gesture.read, gesture.new_files)
            if failed is not None:
                after = functools.partial(_not_written, held, gesture, failed)
            else:
                expected = gesture.read[opened].replace("\r\n", "\n")
                own = gesture.edits[opened].replace("\r\n", "\n")
                n = _counter(edit_request.value)
                edits = [trellis.restoring_edit(own, expected)]
                request = {"edits": edits, "expected": expected, "n": n}
                several = len(gesture.edits) > 1 or gesture.deleted
                key = next(_gesture_keys) if several else None
                if key is not None:
                    request["gesture"] = key
                edit_request.value = request
                gesturing.value = {**held, "step": "asked", "n": n, "undo": undo, "key": key}
    if after is not None:
        after()


def _undo_closed(held: dict) -> None:
    """With LOOP_LOCK held by its caller, takes back what the gesture `held`
    applied before the editor refused the open document's edit, or before
    the gesture was replaced or withdrawn at a change of source (J-D36), so
    that it leaves nothing written: each closed file's buffer that still
    holds the gesture's text holds again the text it held, its revision
    raised by one, or is removed where the gesture made it; each new file is
    removed from the gesture's own model folder, with the folders made for
    it (`_remove_new_files`), even where the tab has opened another folder
    (`open_model`), whose buffers hold none of the gesture's texts; and the
    checklist is read again (`read_checklist`)."""
    undo, gesture = held["undo"], held["gesture"]
    folder = undo["folder"]
    taken = dict(buffers.value)
    for path, text in gesture.edits.items():
        name = recipe.relative(folder, path)
        current = taken.get(name)
        if name not in undo["buffers"] or current is None or current["text"] != text:
            continue
        earlier = undo["buffers"][name]
        if earlier is None:
            del taken[name]
        else:
            taken[name] = {**current, "text": earlier["text"], "revision": current["revision"] + 1}
    buffers.value = taken
    _remove_new_files(folder.root, undo["files"], undo["folders"])
    read_checklist()


def on_gesture_undo(data: dict) -> None:
    """The editor's event `gesture_undo` (unit L, Task 17; defect 6 of the
    UX simulation: one undo per gesture, across all the files the gesture
    edited), dropped where it names a document no longer open. With a
    gesture's key, the editor's undo took that gesture's step back in the
    open file, or its redo made it again, and the gesture's other files
    follow (`_follow_step`). With none, Mod-z was pressed while the editor's
    history held no step to undo, as in a file the gesture edited while it
    was closed, or whose history a change of file began again (R-D45): the
    last gesture of `gesture_steps` not taken back that edited the open file
    is taken back, where the editor's text, `text`, is the text it left
    there; the editor is asked for the open file's part, kept out of its
    undo history, and the other files follow at its true answer
    (`_follow_undoing`). Nothing is asked while a gesture or another such
    undo waits for the editor."""
    if not _event_is_current(data):
        return
    path, key = data["path"], data.get("gesture")
    with LOOP_LOCK:
        folder = tab_folder.value
        if key is not None:
            back = not data.get("redo")
            step = next(
                (
                    step
                    for step in gesture_steps.value
                    if step["key"] == key and step["undone"] != back and step["folder"] == folder
                ),
                None,
            )
            if step is not None:
                _follow_step(step, path, back)
            return
        if gesturing.value is not None or gesture_undoing.value is not None:
            return
        text = _newlines_as_loaded(data.get("text") or "", buffers.value[path]["document"])
        step = next(
            (
                step
                for step in reversed(gesture_steps.value)
                if not step["undone"] and step["folder"] == folder and path in step["files"]
            ),
            None,
        )
        if step is None or step["files"][path][1] != text:
            return
        # the editor's document holds "\n" where the file holds "\r\n"
        before, after = (each.replace("\r\n", "\n") for each in step["files"][path])
        n = _counter(edit_request.value)
        edit_request.value = {
            "edits": [trellis.restoring_edit(before, after)],
            "expected": after,
            "n": n,
            "history": False,
        }
        gesture_undoing.value = {"n": n, "key": step["key"], "path": path}


def _follow_undoing(answer: dict) -> None:
    """The editor's answer to the undo of a gesture that `on_gesture_undo`
    asked (`gesture_undoing`): on a true answer for the file it named, the
    gesture's other files follow (`_follow_step`); an answer to another
    request changes nothing."""
    undoing = gesture_undoing.value
    if undoing is None or undoing["n"] != answer["n"]:
        return
    gesture_undoing.value = None
    if not answer["applied"] or answer["path"] != undoing["path"]:
        return
    with LOOP_LOCK:
        folder = tab_folder.value
        step = next(
            (
                step
                for step in gesture_steps.value
                if step["key"] == undoing["key"] and not step["undone"]
            ),
            None,
        )
        if step is not None and step["folder"] == folder:
            _follow_step(step, undoing["path"], True)


def _follow_step(step: dict, opened: str, back: bool) -> None:
    """With LOOP_LOCK held by its caller: the gesture `step` of
    `gesture_steps` taken back where `back` is true, or made again where it
    is false, in each of its files but the open file `opened`, whose text
    the editor holds (unit L, Task 17). Taken back, a file whose buffer
    holds the text the gesture left takes the text it held before the
    gesture; made again, a file whose buffer holds that earlier text takes
    the text the gesture left; the buffer's revision rises by one. A file
    the tab holds no buffer of is read from disk, and given a buffer where
    the disk holds that text. A file that holds another text, which a later
    edit wrote, is left as it stands, so that an undo never takes back two
    gestures. The step is then marked undone, or not, and the checklist is
    read again (`read_checklist`)."""
    folder = step["folder"]
    taken = dict(buffers.value)
    for name, (before, after) in step["files"].items():
        if name == opened:
            continue
        source, target = (after, before) if back else (before, after)
        held = taken.get(name)
        if held is not None:
            if held["text"] == source:
                taken[name] = {**held, "text": target, "revision": held["revision"] + 1}
            continue
        try:
            found = model.read_file(folder, name)
        except OSError:
            continue
        if found.text == source:
            taken[name] = {
                "text": target,
                "revision": 1,
                "digest": found.digest,
                "document": target,
                "document_revision": next(_document_numbers),
            }
    buffers.value = taken
    gesture_steps.value = tuple(
        {**held, "undone": back} if held is step else held for held in gesture_steps.value
    )
    # the files a removal listed to delete on save are withdrawn with its
    # undo and listed again with its redo (unit L, Task 25)
    _mark_deleted(step.get("deleted", ()), step["key"], not back)
    read_checklist()


def _mark_deleted(paths, key, marked: bool) -> None:
    """The files and folders `paths`, relative to the folder, that the
    gesture of key `key` listed to delete on save (unit L, Task 25; AAS,
    L-D18): where `marked`, each joins `deleting` under that key where it
    is not listed yet; otherwise every file listed under that key leaves
    it, as the gesture's undo takes its edits back."""
    held = deleting.value
    if marked:
        listed = {path for path, _ in held}
        added = tuple((path, key) for path in paths if path not in listed)
        if added:
            deleting.value = (*held, *added)
    elif any(listed_key == key for _, listed_key in held):
        deleting.value = tuple(item for item in held if item[1] != key)


def toggle_deletion(path: str) -> None:
    """The tree's control of the file or folder `path`, relative to the
    folder (unit L, Task 25; AAS, L-D18): `remove` marks a file that no
    file of the folder names to be deleted on the next save, and `keep`
    withdraws a file's mark, whichever gesture or control made it."""
    held = deleting.value
    if any(listed == path for listed, _ in held):
        deleting.value = tuple(item for item in held if item[0] != path)
    else:
        deleting.value = (*held, (path, None))


def _inside(name: str, path: str) -> bool:
    """Whether the file `name` is `path` or lies within the folder `path`,
    both relative to the folder in posix form."""
    return name == path or name.startswith(f"{path}/")


def _delete_on_save() -> str | None:
    """After a save that wrote a file (unit L, Task 25; AAS, L-D18): each
    file and folder of `deleting` that no file of the folder names, in a
    buffer or on disk (`creation.deletable`), and within which no buffer
    holds unsaved text, deleted from disk through the working tree alone,
    git staging nothing, its tabs that hold no unsaved text closed
    (`_close`), and the paths that stand no longer on disk left out of
    `deleting`; a file another file still names, as the recipe on disk
    names a removed stage's folder until the recipe is saved, stays listed
    for a later save. Answers the save's note, `deleted: stages/bequest/`,
    the files and folders deleted by their paths from the factory's folder
    (`creation.deletion_names`), or None where none was deleted."""
    folder = tab_folder.value
    pending = [path for path, _ in deleting.value]
    if folder is None or not pending:
        return None
    dirty = _dirty_paths()
    free = [
        path
        for path in creation.deletable(folder.root, pending, trellis.texts_of(unsaved_texts()))
        if not any(_inside(name, path) for name in dirty)
    ]
    names = dict(zip(free, creation.deletion_names(folder.root, free)))
    deleted = []
    for path in free:
        target = folder.root / path
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        except OSError:
            continue
        deleted.append(path)
    deleting.value = tuple(
        item
        for item in deleting.value
        if item[0] not in deleted and (folder.root / item[0]).exists()
    )
    for name in list(buffers.value):
        if any(_inside(name, path) for path in deleted):
            _close(name)
    if not deleted:
        return None
    return "deleted: " + ", ".join(names[path] for path in deleted)


# the label under which Details lists, for the terminal period, the ranges
# and range keys of the recipe a period typed at the head of `periods` would
# move (spec 0.4 §3.6; brief §5)
MOVED_BY_A_PERIOD_TYPED_FIRST = "Moved by a period typed first"


@solara.component
def MovedRanges():
    """In Details, for the terminal period's layer of the trellis view (spec
    0.4 §3.6, decision 28; brief §5): under the label `Moved by a period
    typed first`, in sentence case (design pass 13 §3; C12), in
    `ul.bl-moved-ranges`, one `li.bl-moved-range` for each
    range and range key of the tab's recipe that a period typed at the head
    of `periods` would move, read with the tab's unsaved texts
    (`trellis.moved_ranges`); an empty element where none would move."""
    held = trellis_shown.value
    texts = trellis.texts_of(unsaved_texts())
    moved = [] if held is None else trellis.moved_ranges(tab_folder.value, held, texts)
    with rv.Html(tag="div"):
        if moved:
            rv.Html(tag="div", class_="bl-block-label", children=[MOVED_BY_A_PERIOD_TYPED_FIRST])
            with rv.Html(tag="ul", class_="bl-moved-ranges bl-code-small"):
                for line in moved:
                    rv.Html(tag="li", class_="bl-moved-range", children=[line]).key(line)


@solara.component
def GestureNote():
    """The status line's text of the last gesture of the trellis graph that
    wrote (`gesture_note`; brief rule 7), after a separator kept in the
    line's text and not drawn (`status_dot`; design pass 8 §6), in
    `span.bl-gesture-note`; an empty element where none stands."""
    note = gesture_note.value
    with rv.Html(tag="span", class_="bl-status-gesture"):
        if note is not None:
            status_dot()
            rv.Html(tag="span", class_="bl-gesture-note", children=[note["sentence"]])


# --- what stands refused (AMD-MI-002 §6a rule 1, A2-D13) ---


@dataclasses.dataclass(frozen=True)
class Refusal:
    """One line of the list under the error mark: a refusal, or a step left
    undone, that stands in the tab. `sentence`, as the tab's state holds
    it, with nothing added, each absolute path it writes printed relative
    to the folder (`folder_relative`; K-D11); `file`, relative to the
    folder, and `line`, counted from one, where the refusal names them, None
    otherwise; `made`, the moment its source made it
    (`time.monotonic`), by which the list orders its lines; and `opens`,
    the path of the model folder that the line's button `open <name>`
    opens, where the line is the note of a model's `declaration/` opened
    by itself (`recipe.declaration_note`; unit L, Task 28, AAS, L-D23),
    None otherwise. `severity` distinguishes errors from checks that remain
    undecided; `places` retains all available source locations. `rule` is
    the rule the package names where the line is one of its diagnostics, a
    connection's rule for a connection to check and `unread-input` for a
    backward header that lists a value input no line of its block reads
    (`UNREAD_INPUT_RULE`), None otherwise."""

    sentence: str
    file: str | None
    line: int | None
    made: float
    opens: str | None = None
    severity: str = "error"
    places: tuple = ()
    rule: str | None = None


def folder_relative(sentence: str | None) -> str | None:
    """A sentence the page prints, from the package, the Workbench or git,
    with each absolute path it writes printed relative to the tab's folder
    and nothing else changed (`trellis.relative_sentence`; usability
    walkthrough §4 item 6; unit K's decision K-D11); as given where no
    folder is open or the sentence is empty or None."""
    folder = tab_folder.value
    if folder is None or not sentence:
        return sentence
    return trellis.relative_sentence(folder, sentence)


def _own_shown() -> Shown | None:
    """The stage shown where it is the open file's, the stage the
    BellmanType panel reads (`FileRegion`); None otherwise."""
    current = shown.value
    return current if current is not None and current.path == open_path.value else None


def _standing_table_note(current: Shown | None) -> dict | None:
    """The note of the last change of the Fields tab's tables while it
    stands under its group: while `current`, the stage the panel shows, is
    of the file and the revision of the stage shown when the change was
    made, the file's last construction; None otherwise."""
    note = table_note.value
    if note is None or current is None:
        return None
    if (note["path"], note["revision"]) != (current.path, current.revision):
        return None
    return note


def _standing_value_note(current: Shown | None) -> dict | None:
    """The value tabs' refused write while it stands: while `current`, the
    stage the panel shows, is of the file, the occurrence and the source on
    which the write was asked; None otherwise."""
    refused = value_note.value
    if refused is None or current is None:
        return None
    asked = (refused["path"], refused["position"], refused["source"])
    if asked != (current.path, current.position, current.source):
        return None
    return refused


def _trellis_refusal_place(refusal: model.Diagnostic) -> tuple[str | None, int | None]:
    """The file, relative to the folder, and the line at which the
    refusal of a trellis's reading stands, as the trellis view and a stage
    bound through that source hold it (specification §2.2 rule 2, D11;
    ruling R51): the file and the line the refusal names; else the file and the
    line of the entry its address names (`trellis.address_place`), counted
    in the text of the file's unsaved buffer where the tab holds one (spec
    0.4 §3.1); else the file it names and no line. Each part is None where
    none is found."""
    if refusal.line is not None and refusal.file:
        return recipe.relative(tab_folder.value, refusal.file), refusal.line
    place = trellis.address_place(
        tab_folder.value,
        refusal.file,
        refusal.address,
        refusal.rule != trellis.SHAPE_RULE,
        texts=trellis.texts_of(unsaved_texts()),
    )
    if place is not None:
        return place
    return (recipe.relative(tab_folder.value, refusal.file) if refusal.file else None), None


def _restriction_refused() -> dict | None:
    """The refusal of the restriction that stands, {"sentence", "made"}:
    the parser's refusal of the text typed (`restriction_refusal`), else
    the package's refusal of the restriction asked, which the last outcome
    holds, with that outcome's moment; None where neither stands."""
    if restriction_refusal.value is not None:
        return restriction_refusal.value
    outcome = trellis_outcome.value
    if outcome is None or outcome.restricted is None:
        return None
    return {"sentence": outcome.restricted, "made": outcome.made}


def _bound_as_read(current: Shown) -> bool:
    """Whether each file the binding of the stage shown `current` read, the
    source, its trellis file and the binding sources (`source_digests`),
    still has on disk the digest the binding read, so that the notes of
    that binding are those of the last reading (usability walkthrough §4
    item 15; unit K, Task 13). A changed file is bound again by the next
    reading of the stage."""
    return _source_digests(current.source_digests) == current.source_digests


# Presentation of native findings; compatibility is decided by the package.
CONNECTION_REVIEW_RULES = frozenset((
    "pair-not-established", "route-incomplete", "route-not-established", "route-no-law",
))
# The rule of the package's diagnostic of a backward header that lists a value
# input no line of its block reads (`stage.diagnostics()["unread_inputs"]`;
# AAS, 17 October 2026): the package elaborates the stage and leaves the input
# out of the block's builder, so the line is one to review and no error.
UNREAD_INPUT_RULE = "unread-input"


def standing_refusals() -> list[Refusal]:
    """What stands refused or undone in the tab, newest first (AMD-MI-002
    §6a rule 1, A2-D13; ruling R46), each line read from the state that
    holds it: the loop's refusals (`results`) of the open text and of the
    text of the stage shown where that stage is another file's, as while a
    file that is no stage is open as text and the view and the panel keep
    the last stage elaborated, each file read once and each refusal with
    its file, its line and the words the package says to write where it
    gives them; the refused builders graphs of the stage shown, read from
    that stage (`model.refused_directions`), where the outcome of its file
    did not make it, as after the loop refused an edit of its text while
    the view still draws it, each with its file and its line; the trellis's
    refusal of its reading (`trellis_outcome`), with its place, the line
    the last gesture typed while its text stands (`_gesture_place`), else
    the place of the package's address (`_trellis_refusal_place`); the
    Workbench's sentence of the last gesture of the trellis graph that
    wrote nothing (`gesture_refusal`), with its file and line; the
    sentence of each graph of the trellis shown that the package refused
    to draw (`trellis_shown`) and the notes of that trellis's binding, each
    the sentence of a verb the package refused (`trellis.binding_notes`),
    where the last reading answered that trellis, since the trellis a
    refused reading leaves drawn is an earlier reading's; the region's
    layout or file-loading refusal (`layout_refusal`, G-D9), with no file
    or line; the notes of the binding of the stage shown, each the sentence
    of a verb the package refused or the note of a source that does not
    read, at the place of its refusal (`_trellis_refusal_place`; ruling
    R51), while the files its binding read stand as it read them
    (`_bound_as_read`), the note of a model's `declaration/` opened by
    itself with the model folder its button opens
    (`recipe.model_of_declaration`; unit L, Task 28, AAS, L-D23); the
    package's refusal to list the places of the
    stage shown (`Shown.places_refusal`), with no file or line (unit L,
    Task 18); the classification table's refusal of a change and the value
    tabs' refusal of a write, while each stands (`_standing_table_note`,
    `_standing_value_note`), and the refusal of a change of the Recipe tab
    (`choice_refusal`); the refusal of the restriction
    (`_restriction_refused`); the refused answer to the last command of
    git's line (`git_answer`); and the choice after a save met a changed
    file (`conflict`), with the open file. So the list holds the refusals
    of the last reading alone, the rule of unit K's Task 13 (usability
    walkthrough §4 item 15) applied to every source of a line; a verb no
    record binds is no refusal and gives no line (K-D29). Then one line per
    refusal (`_one_line_per_refusal`; unit L, Task 21; defect 17 of the UX
    simulation). Lines made at one moment keep this order."""
    found = []
    current = shown.value
    # the open file, then the stage shown's file where it is another; a
    # path given twice is read once
    paths = dict.fromkeys((open_path.value, current.path if current is not None else None))
    for path in paths:
        result = _result_of(path)
        if result is None:
            continue
        for refusal in result.refusals:
            found.append(
                Refusal(_refusal_sentence(refusal), result.path, refusal["line"], result.made)
            )
    # The stage shown's refused graphs where the outcome of its file did not
    # make it: the panel of a refusing node of the stage drawn prints its
    # rows alone.
    entry = results.value.get(current.path) if current is not None else None
    if current is not None and (entry is None or entry["shown"] is not current):
        for refusal in model.refused_directions(current.stage).values():
            place = (current.path, refusal["line"])
            found.append(Refusal(refusal["message"], *place, current.made))
    # The value inputs a backward header of the stage shown lists and no line
    # of the block reads, which the package keeps as diagnostics and not as
    # refusals (AAS, 17 October 2026): one line to review each, with the
    # package's sentence, at the line of the block's header.
    if current is not None:
        for diagnostic in current.stage.diagnostics()["unread_inputs"]:
            span = current.spans.get(diagnostic.address) if current.spans else None
            found.append(Refusal(diagnostic.message, current.path,
                                 span.line if span is not None else None, current.made,
                                 severity="warning", rule=diagnostic.rule))
    outcome, held = trellis_outcome.value, trellis_shown.value
    if outcome is not None and outcome.refusal is not None:
        file, line = _gesture_place() or _trellis_refusal_place(outcome.refusal)
        found.append(Refusal(outcome.refusal.message, file, line, outcome.made))
    refused_gesture = gesture_refusal.value
    if refused_gesture is not None:
        place = (refused_gesture["file"], refused_gesture["line"])
        found.append(Refusal(refused_gesture["sentence"], *place, refused_gesture["made"]))
    # the refused graphs and the binding's notes of the trellis the last
    # reading answered; the trellis a refused reading leaves drawn is an
    # earlier reading's
    if held is not None and outcome is not None and outcome.shown is held:
        if held.view_refusal is not None:
            file, line = _trellis_refusal_place(held.view_refusal)
            found.append(Refusal(held.view_refusal.message, file, line, held.made))
        for drawn in held.collection["graphs"]:
            nodes = drawn["nodes"]
            # a graph the package refused to draw holds one node, which
            # states why under the attribute `refusal`; the trellis's
            # initial diagram of a refused direction (design pass 14 §7) is
            # refused with the builders graph's sentence and is not listed
            # twice, and the package pairs the joins of a direction alone
            if drawn["id"] not in DIRECTIONS:
                continue
            if len(nodes) == 1 and nodes[0]["id"] == f"{drawn['id']}:refused":
                unpaired = trellis.unpaired_joins(held.trellis, drawn["id"], selection=held.selection,
                                                 **trellis._selection(held.restriction))
                severity = "warning" if unpaired else "error"
                found.append(Refusal(_attribute(nodes[0], "refusal"), None, None,
                                     held.made, severity=severity))
        texts = trellis.texts_of(unsaved_texts())
        for binding in trellis.refused_bindings(tab_folder.value, held, texts):
            found.append(Refusal(binding["sentence"], binding["file"], binding["line"],
                                 held.made, places=binding["places"]))
        report = trellis.connection_report(held.trellis, selection=held.selection)
        origins = [
            [f"{address}[{key!r}]" if key is not None else address
             for address, key, value in diagnostic.source_entries] or [diagnostic.address]
            for diagnostic in report.diagnostics
        ]
        addresses = tuple(dict.fromkeys(address for group in origins for address in group))
        spans = trellis.written_spans(report.file, addresses, texts) if report.file else ()
        locations = {
            address: (recipe.relative(tab_folder.value, place[0]), place[1].line)
            for address, place in zip(addresses, spans) if place is not None
        }
        for diagnostic, addresses in zip(report.diagnostics, origins):
            places = tuple(dict.fromkeys(locations[address] for address in addresses
                                         if address in locations))
            place = places[0] if places else (None, None)
            severity = "warning" if diagnostic.rule in CONNECTION_REVIEW_RULES else "error"
            found.append(Refusal(diagnostic.message, *place, held.made,
                                 severity=severity, places=places, rule=diagnostic.rule))
        missing = set(report.unjoined["internal"]["reading"])
        rejected = [item for item in report.rejected
                    if (item.reading.h, item.reading.key, item.reading.field) in missing]
        locations = trellis.field_places(tab_folder.value, held,
                                        [use for item in rejected for use in (item.writing, item.reading)],
                                        texts)
        for item in rejected:
            places = tuple(dict.fromkeys(locations[use] for use in (item.writing, item.reading)))
            found.append(Refusal(item.message, *places[0], held.made,
                                 severity="warning", places=places))
    refused_desktop = desktop_refusal.value
    if refused_desktop is not None:
        found.append(Refusal(refused_desktop["sentence"], None, None, refused_desktop["made"]))
    layout = layout_refusal.value
    if layout is not None:
        found.append(Refusal(layout["sentence"], None, None, layout["made"]))
    if current is not None and _bound_as_read(current):
        # the one note of a source that does not read, at its refusal's place
        refused = current.refusal
        place = _trellis_refusal_place(refused) if refused is not None else (None, None)
        # the note of a model's declaration/ opened by itself carries the
        # model folder above, which its line's button opens (unit L, Task 28)
        above = recipe.model_of_declaration(tab_folder.value)
        offered = None if above is None else recipe.declaration_note(above)
        found += [
            Refusal(note, *place, current.made, str(above) if note == offered else None)
            for note in current.notes
        ]
    if current is not None and current.places_refusal is not None:
        found.append(Refusal(current.places_refusal, None, None, current.made))
    own = _own_shown()
    note = _standing_table_note(own)
    if note is not None and note["refused"]:
        found.append(Refusal(note["sentence"], note["path"], None, note["made"]))
    written = _standing_value_note(own)
    if written is not None:
        place = (written["file"], written["line"])
        found.append(Refusal(written["sentence"], *place, written["made"]))
    choice = choice_refusal.value
    if choice is not None:
        found.append(Refusal(choice["sentence"], choice["file"], choice["line"], choice["made"]))
    restricted = _restriction_refused()
    if restricted is not None:
        found.append(Refusal(restricted["sentence"], None, None, restricted["made"]))
    answer = git_answer.value
    if answer is not None and answer["refused"] and answer["sentence"]:
        found.append(Refusal(answer["sentence"], None, None, answer["made"]))
    met = conflict.value
    if met is not None:
        found.append(Refusal(met["reason"], open_path.value, None, met["made"]))
    # each sentence with its paths from the folder, the sentence otherwise
    # as its source wrote it (K-D11)
    found = [
        dataclasses.replace(refusal, sentence=folder_relative(refusal.sentence))
        for refusal in found
    ]
    return sorted(_one_line_per_refusal(found), key=lambda refusal: refusal.made, reverse=True)


def _one_line_per_refusal(found: list[Refusal]) -> list[Refusal]:
    """The lines `found`, in their order, one line per refusal (unit L,
    Task 21; defects 17 and 18 of the UX simulation): lines whose sentences
    are equal once the line naming the stage occurrence refused is taken
    out (`trellis.without_occurrence`) give one refusal where they name the
    same file or one of them names none, as a refusal of a
    binding that the stage shown's binding gives without that line and the
    trellis's binding with it, an exception that the loop meets in the
    open text and the trellis's reading meets in the same stage file, or
    the refusal of a recipe that the trellis's reading and the stage
    shown's source both give; lines in the same words that name two files
    stand as two, so that each file's link stands (unit L's final
    judgment, §6 item 8). The refusal stands once, as the line that names
    the occurrence where one does, else as a line that names a file, else
    as the first of them; no sentence is composed."""
    kept = []
    for refusal in found:
        key = trellis.without_occurrence(refusal.sentence)
        at = next(
            (
                n
                for n, standing in enumerate(kept)
                if trellis.without_occurrence(standing.sentence) == key
                and (standing.file == refusal.file or None in (standing.file, refusal.file))
            ),
            None,
        )
        if at is None:
            kept.append(refusal)
        else:
            previous = kept[at]
            chosen = refusal if _line_rank(refusal) > _line_rank(previous) else previous
            places = tuple(dict.fromkeys((*previous.places, *refusal.places)))
            kept[at] = dataclasses.replace(chosen, places=places)
    return kept


def _line_rank(refusal: Refusal) -> tuple[bool, bool]:
    """The order in which one of several lines of one refusal stands
    (`_one_line_per_refusal`): a line naming the stage occurrence before one
    that does not, then a line naming a file before one that names none."""
    named = trellis.without_occurrence(refusal.sentence) != refusal.sentence
    return named, refusal.file is not None


def toggle_errors() -> None:
    """Opens the list under the error mark when it is closed, and closes it
    when it is open."""
    errors_open.value = not errors_open.value


def request_fold(region: str) -> None:
    """Asks window.vue to fold the region `region`, `folder` or `matsya`,
    where it is open, and to open it where it is folded, as a click on its
    button `.bl-fold` does (spec 0.4 §5.1; brief rule 3)."""
    fold_request.value = {"region": region, "n": _counter(fold_request.value)}


# --- Goto Anything (spec 0.4 §5.8; unit R, brief rule 9) ---


def open_goto(data=None) -> None:
    """Opens Goto Anything: raises `goto_open_request`, which goto.vue reads
    (ruling R-P2), on P with the primary modifier, which window.vue reads
    and sends with no data, and on the button `go to`."""
    goto_open_request.value = goto_open_request.value + 1


def _box_entries(collection: dict, graph_id: str, lines: dict | None) -> list[dict]:
    """The entries of `@` for the nodes of the graph `graph_id` of
    `collection`, in node order (`goto_entries`): each `{prefix, kind
    "box", text, address, node, graph}`, its text the node's label and its
    place the package's `node_place`. In a stage's view, `lines` gives each
    block's header line, and an entry holds its block and that line as its
    address, `<line>:1`, the empty text where it has none; in the trellis
    view, `lines` None, its address is its occurrence and it holds no
    block. A node the package places nowhere is left out."""
    found = next((entry for entry in collection["graphs"] if entry["id"] == graph_id), None)
    entries = []
    for node in found["nodes"] if found is not None else []:
        try:
            place = node_place(collection, graph_id, node["id"])
        except (KeyError, ValueError):
            continue
        entry = {
            "prefix": "@",
            "kind": "box",
            "text": node.get("label") or node["id"],
            "address": place.occurrence,
            "node": node["id"],
            "graph": graph_id,
        }
        if lines is not None:
            line = lines.get(place.block)
            entry["address"] = f"{line}:1" if line is not None else ""
            if place.block:
                entry["block"] = place.block
        entries.append(entry)
    return entries


def goto_entries(current: Shown | None, result: Outcome | None) -> list[dict]:
    """The entries of `@` of Goto Anything (spec 0.4 §5.8; brief rule 9;
    review 1). In a stage's view: the blocks of the text, each `{prefix
    "@", kind "block", text, address, block, line}`, its header's line as
    its address, `<line>:1`, in the order of their lines, a block an
    address of the spans with no "." that is no number, as `model.block_at`
    reads one; the spans are those that match the editor's text
    (`_spans_of_the_text`), or, where no stage of the open file is shown,
    those of its last outcome, none where the parser refuses the text. Then
    the boxes of the graph shown (`_box_entries`), only while the stage
    shown is the construction of the buffer at its current revision and no
    refusal stands (`_current_construction`, ruling R-P10): while the graph
    shown is a previous construction, no box is listed, so that no address
    is guessed from old line numbers. In the trellis view, the nodes of the
    trellis's graph shown, each at its occurrence, and no block."""
    if view_mode.value == "trellis":
        held = trellis_shown.value
        return _box_entries(held.collection, graph.value, None) if held is not None else []
    path = open_path.value
    if current is not None and current.path == path:
        spans = _spans_of_the_text(current)
    elif result is not None and result.path == path:
        spans = result.spans
    else:
        spans = None
    lines = {
        name: span.line
        for name, span in (spans or {}).items()
        if "." not in name and not name.isdigit()
    }
    entries = [
        {
            "prefix": "@",
            "kind": "block",
            "text": name,
            "address": f"{line}:1",
            "block": name,
            "line": line,
        }
        for name, line in sorted(lines.items(), key=lambda item: item[1])
    ]
    if _current_construction(current, result):
        entries += _box_entries(level_collection(current), graph.value, lines)
    return entries


def goto_commands() -> list[dict]:
    """The entries of `>` of Goto Anything (spec 0.4 §5.8; brief rule 9),
    each `{prefix ">", kind "command", text, address, command}`, its text
    and its command the command's word and its address empty, each offered
    where its control is, in this order: `save` while a file is open, as
    `Save` is enabled; `hide types`, or `show types` while the types are
    hidden, the editor's collapse of spec 0.4 §5.4, which the tab row's
    toggle `Types` also does (design pass 10 §4); `fold folder` and
    `fold Matsya`, which the main bar's toggles `Files` and `Matsya` also
    do, the second absent with the setting off (`MATSYA_OFF`); `high contrast`
    (R-D10); `notebook` where
    `FolderActions` offers it; `new trellis` while no git command runs, as
    its button is enabled; `new variant` where `FolderActions` offers it;
    and `add
    stage` and `add period`, whose buttons unit J removed (spec 0.4 §3.6;
    J-D7), where `creation.can_add` admits the folder's recipe
    `declaration/spec.yml`, by one call with its defaults (spec 0.4 §5.1)."""
    # the folder's entries, read so that a render that reads the commands
    # is made again when the folder is read again, as after `notebook`
    tree.value
    root = tab_folder.value.root
    words = ["save"] if open_path.value is not None else []
    words.append("show types" if hide_types.value else "hide types")
    words.append("fold folder")
    if not MATSYA_OFF:
        words.append("fold Matsya")
    words.append("high contrast")
    if source.value is not None and not (root / creation.notebook_file(root)).exists():
        words.append("notebook")
    if not git_task.pending:
        words.append("new trellis")
    if (root / creation.factory_path(creation.RECIPE)).is_file():
        words.append("new variant")
    if creation.can_add(root):
        words += ["add stage", "add period"]
    return [
        {"prefix": ">", "kind": "command", "text": word, "address": "", "command": word}
        for word in words
    ]


def run_command(word: str) -> None:
    """Runs the command `word` of Goto Anything as its control does (spec
    0.4 §5.8: Enter on an explicit command performs that named action):
    `save` asks the editor for its document (`request_save`); `hide types`
    and `show types` turn the types (`toggle_types`); `fold folder` and
    `fold Matsya` ask window.vue for the fold (`request_fold`); `high
    contrast` raises `contrast_request`; `notebook` writes the notebook
    (`run_notebook`); the four others open their form (`open_form`). A
    command `goto_commands` does not offer does nothing."""
    if word not in {entry["command"] for entry in goto_commands()}:
        return
    if word == "save":
        request_save()
    elif word in ("hide types", "show types"):
        toggle_types()
    elif word == "fold folder":
        request_fold("folder")
    elif word == "fold Matsya":
        request_fold("matsya")
    elif word == "high contrast":
        contrast_request.value = contrast_request.value + 1
    elif word == "notebook":
        run_notebook()
    else:
        open_form(word)


def on_goto_preview(data: dict) -> None:
    """A box of Goto Anything previewed (spec 0.4 §5.8; review 1): the view
    selects the box `nodeId` of the graph shown (`select_node`), which
    moves neither the editor nor the focus and records no place of the
    history. A box of another graph is not previewed, since a cancel
    restores the graph's view and not the graph shown."""
    node_id = data.get("nodeId")
    if node_id and data.get("graphId") in (None, graph.value):
        select_node(node_id, graph.value)


def _restore_goto_selection(data: dict) -> None:
    """Python's selection at the palette's opening, `data["selection"]`,
    written back to `selected`. Where a box was previewed since,
    `data["previewed"]`, the view is asked to select that selection again,
    or none, so that a layout the preview asked for and the view has not
    finished is replaced, and the view's selection is Python's."""
    selection = data.get("selection") or None
    selected.value = selection
    if data.get("previewed"):
        shown_here = selection is not None and selection.get("graphId") == graph.value
        kept = selection.get("nodeId") if shown_here else None
        select_request.value = {
            "nodeId": kept,
            "graphId": graph.value,
            "n": _counter(select_request.value),
        }


def on_goto_chosen(data: dict) -> None:
    """A result of Goto Anything chosen by Enter or a click (spec 0.4 §5.8;
    brief rule 9): a line or a text moves the editor's cursor there
    (`goto_line`); a block to its header (`goto_block`); a box is selected
    (`select_node`) and the editor moves to its block's header; a command
    runs (`run_command`). For a result that is no box, a box previewed
    since the opening gives the selection back first
    (`_restore_goto_selection`). Nothing records a place of the history."""
    kind = data.get("kind")
    if kind != "box" and data.get("previewed"):
        _restore_goto_selection(data)
    if kind in ("line", "text") and data.get("line"):
        goto_line(int(data["line"]), int(data.get("column") or 1))
    elif kind == "block" and data.get("block"):
        goto_block(data["block"])
    elif kind == "box" and data.get("node") and data.get("graph") in (None, graph.value):
        select_node(data["node"], graph.value)
        if data.get("block"):
            goto_block(data["block"])
    elif kind == "command":
        run_command(data.get("command") or "")


def on_goto_cancelled(data: dict) -> None:
    """Goto Anything closed with nothing chosen, by Escape, a press outside
    it or the focus leaving it (spec 0.4 §5.8: Escape restores the prior
    selection, viewport and focus): goto.vue has restored the views and
    the focus, and Python's selection is written back
    (`_restore_goto_selection`)."""
    _restore_goto_selection(data)


# --- the Vue components ---


@solara.component_vue("desktop.vue")
def Desktop(folder: str = "", acknowledged: dict | None = None, event_open=None):
    """Receive the initial URL or a desktop file request; see desktop.vue."""


@solara.component_vue("editor.vue")
def Editor(
    path: str = None,
    text: str = "",
    revision: int = 0,
    diagnostics: list = [],
    goto: dict = None,
    save_request: int = 0,
    flush_request: int = 0,
    hide_types: bool = False,
    show_notes: bool = False,
    edit: dict = None,
    shortcuts: dict = {},
    height: str = "100%",
    event_change=None,
    event_save=None,
    event_cursor=None,
    event_applied=None,
    event_gesture_undo=None,
    role_words: list = [],
    indent: int = INDENT,
):
    """CodeMirror 6 over the editor bundle; see editor.vue."""


@solara.component_vue("graph.vue")
def Graph(
    collection: dict = None,
    overlays_request: dict = None,
    layers: dict = {},
    graph: str = "backward",
    select: dict = None,
    stale: bool = False,
    scope: str = "stage",
    place: dict = None,
    styles: dict = None,
    unjoined: list = None,
    reading: dict = None,
    stages: dict = None,
    adds: list = None,
    joins: list = None,
    builders: dict = None,
    stage_order: list = None,
    event_selected=None,
    event_processed=None,
    event_opened=None,
    event_refused=None,
    event_connected=None,
    event_dropped=None,
    event_join_chosen=None,
    event_removed=None,
    event_moved=None,
):
    """The graph region, the graph JSON drawn by React Flow after ELK lays it
    out (spec 0.4 §§2 and 4); see graph.vue."""


@solara.component_vue("copy.vue")
def CopyButton(text: str = "", label: str = "Copy", title: str = "", button_class: str = ""):
    """A button that copies `text` to the clipboard, and shows the text in
    a collapsed block where the browser refuses the clipboard; see
    copy.vue."""


@solara.component_vue("window.vue")
def Window(
    folder: str = "",
    fold_request: dict | None = None,
    event_back=None,
    event_forward=None,
    contrast_request: int = 0,
    event_goto=None,
    trellis_view: bool = False,
    wide_panel: bool = False,
    lower_panel: str | None = None,
    event_escape=None,
    event_region_folded=None,
    event_close_recipe_row=None,
):
    """The behavior of the window as a whole, rendered once in `Page`: the
    columns' widths at every size of the window (spec 0.4 §5.1; R-D30), the
    folds of the folder, of the two panels, the Inspector and Details, and
    of Matsya, asked by a click on a button `.bl-fold`, a toggle of the main
    bar or a panel's `×` (design pass 10 §3; AAS, L-D12), or by
    `fold_request`, a folded Matsya taking no width (unit K's decision
    K-D19), Matsya folded while the trellis view is shown, from the
    message of the graph bar's tab `Trellis`, which comes before the
    view's, or from `trellis_view`, which comes after them, whichever
    arrives first, until both say another view, the graph taking its width
    (K-D6), the handles that size the regions, the sizes and the
    folds kept in the browser's storage under the path `folder` (R-D16),
    the keys Alt+← and Alt+→ outside a text field, which step back and
    forward through the tab's history, P with the primary modifier, which
    opens Goto Anything (`event_goto`), Escape while `wide_panel` holds or
    a panel is drawn wide, which closes the wide panel that stands
    (`event_escape`; AAS, L-D11 and L-D12), the fold of a region, sent so
    that a panel folded while it stands wide closes its wide panel
    (`event_region_folded`; unit L's
    final judgment, §6 item 11), the fold of the panel under the editor
    while it shows the open file, `lower_panel`, `inspector` or None, by
    which the Inspector toggle is drawn open (design pass 10 §3), Escape in
    the Recipe tab's open row and a click outside the tab's table, each of
    which closes that row (`event_close_recipe_row`; design pass 11 §2),
    and the high-contrast setting, kept for the browser and turned by each
    change of `contrast_request` (spec 0.4 §5.8; R-D24); see window.vue."""


@solara.component_vue("status.vue")
def StatusFit(lines: list = [], event_fit=None):
    """The measure of the trellis view's status line (spec 0.4 §5.7; design
    pass §1 item 10 and §5 item 6; unit K, Task 6), rendered in the foot
    while the trellis view is shown: the browser measures how many of the
    texts of `lines`, the line with the bindings applied and then the whole
    line, each with the last gesture's note, fit in the width the visible
    status line leaves the trellis's line, counted from the first, at each
    change of `lines` and of the foot's size and contents, and calls
    `event_fit` with that number where it changes; see status.vue."""


@solara.component_vue("graph_bar.vue")
def GraphBarFit():
    """The measure of the graph bar (design pass 13 §4; the fix wave Q3b of
    unit Q, item 16, D22), rendered as the last child of `.bl-graph-tools`,
    an element not displayed, so that Problems stays the bar's last
    element: the browser marks
    the bar `data-crowded` while its items do not fit one row with the
    region's name `Semantic graph`, which brand.css then does not draw and
    which stays the region's heading, so that the bar keeps one row of 36
    px, at each change of the graph column's size, of the size of an item
    or of Problems and of the bar's items; see graph_bar.vue."""


@solara.component_vue("goto.vue")
def Goto(
    open_request: int = 0,
    entries: list = [],
    selection: dict = None,
    event_preview=None,
    event_chosen=None,
    event_cancelled=None,
):
    """Goto Anything, the palette over the text (spec 0.4 §5.8; unit R,
    brief rule 9), rendered once in `Page`: it opens at each change of
    `open_request`, lists the entries of `@` and `>` that `entries` holds
    (`goto_entries`, `goto_commands`) and the lines of `:` and `#` from the
    editor's own document, and gives back `selection`, Python's selection
    at its opening, when it closes; see goto.vue."""


# --- the printed terms ---


def Term(
    word: str,
    text: str | None = None,
    classes: str = "",
    focusable: bool = False,
    definition: str | None = None,
):
    """The element of a printed term: `text`, or the word itself, carrying
    the definition `TERMS` gives `word` in its title, as a link to the
    term's page of the documentation where `TERM_PAGES` names one, else
    as a span. A word `TERMS` does not hold is printed as a plain span.
    `definition`, where given, is carried in place of the one `TERMS`
    gives, for a word whose place narrows its meaning, as the word of a
    binding's word did in the recipe region of unit K (K-D21). With
    `focusable`, a defined term takes the keyboard's focus
    (`tabindex="0"`) and carries its definition as its accessible
    description too, so that the keyboard reaches the definition (spec 0.4
    §5.7; R-D39)."""
    definition = definition or TERMS.get(word)
    attributes = {"title": definition} if definition else {}
    if focusable and definition:
        attributes.update({"tabindex": "0", "aria-description": definition})
    class_ = f"bl-term {classes}".strip() if definition else classes
    page = TERM_PAGES.get(word)
    if page is not None:
        attributes.update({"href": f"{DOCS_URL}Bellman-Sym/API/stage/{page}/", "target": "_blank"})
        return rv.Html(tag="a", class_=class_, attributes=attributes, children=[text or word])
    return rv.Html(tag="span", class_=class_, attributes=attributes, children=[text or word])


def path_children(text: str) -> list:
    """The children that draw the path `text` with a break opportunity, an
    element `<wbr>`, after each slash, so that a narrow column wraps the
    path after a slash, or after a hyphen as the browser wraps any line, and
    not every few characters (specification §3.2: a cell showing the
    effective source); the element draws no text."""
    pieces = text.split("/")
    children = []
    for piece in pieces[:-1]:
        children += [f"{piece}/", rv.Html(tag="wbr")]
    if pieces[-1]:
        children.append(pieces[-1])
    return children


def _term_of_key(key: str) -> str:
    """The term of an attribute's key: the key without a trailing number,
    `parameter 2` giving `parameter`."""
    words = key.split(" ")
    if len(words) > 1 and words[-1].isdigit():
        return " ".join(words[:-1])
    return key


# --- the regions ---


def Handle(region: str):
    """The handle on the edge of the region `region`, one of `folder`,
    `file`, `classification`, `panel`, `matsya` and `composer` (AMD-MI-002
    §6 rule 2): an element `.bl-handle` whose `data-handle` names the
    region, which brand.css draws on the region's edge and window.vue
    reads, a drag sizing the region down to its least width of spec 0.4
    §5.1 or its least height, and a double click returning it to the width
    the frame gives it or to its default height. The handle `matsya` stands
    on Matsya's left edge and sizes the column's width, a drag to the left
    widening it; `Page` renders it beside the column, as a child of
    `.bl-window` (unit R, brief rule 2). The handle `composer` stands on
    the top edge of Matsya's composer and is drawn by
    `matsya_window.Composer`; a drag upward on it enlarges the composer's
    field, the conversation giving up the height, and a double click
    returns the field to the height of its text (amendment 07 of spec 0.4,
    §2 item 5)."""
    return rv.Html(tag="div", class_="bl-handle", attributes={"data-handle": region})


# The toggles at the right of the main bar (design pass 10 §3; N-D4,
# N-D10), in their order: the fold each toggles, window.vue's name of its
# region, which also names its icon (`icons.TOGGLE_ICONS`), mapped to the
# panel's name, which is the toggle's accessible name and its hover and the
# name a panel's head prints, so that the head and the toggle agree (AAS,
# L-D28). `inspector` is the panel under the editor, on a stage file's four
# tabs or on the Recipe tab (N-D4). Matsya's toggle stands only while
# Matsya's column does (`MATSYA_OFF`; spec 0.4 §6).
PANEL_NAMES = {
    "folder": "Files",
    "inspector": "Inspector",
    "details": "Details",
    "matsya": "Matsya",
}
# The panels whose toggles stand at each end of the main bar, the end of the
# window on which the panel opens (design pass 14 §10; S-D16): the Files
# column and the Inspector at the left, Details and Matsya at the right.
LEFT_PANELS = ("folder", "inspector")
RIGHT_PANELS = ("details", "matsya")
# The fold of each panel a head draws (`RegionHead`), by the panel's
# data-panel: the Recipe tab and the four tabs of a stage file are the two
# contents of the Inspector (design pass 10 §4).
PANEL_FOLDS = {"recipe": "inspector", "types": "inspector", "details": "details"}
# The hover of the brand's mark at the main bar's left, a link to the page
# of Bellman Workbench in the documentation (spec 0.4 §5.1; design pass 8
# §6).
MARK_HOVER = "The page of Bellman Workbench in the documentation"


def inspector_hover(path: str | None) -> str | None:
    """The hover of the disabled Inspector toggle while the open file `path`
    gives the panel nothing to show (design pass 10 §3), `Nothing to inspect
    in <file>`, the file by its name, or the folder's name where no file is
    open; None while the panel shows the file (`lower_panel`)."""
    if lower_panel(path) is not None:
        return None
    name = Path(path).name if path is not None else tab_folder.value.root.name
    return f"Nothing to inspect in {name}"


@solara.component
def Toggle(fold: str, waits: str | None = None):
    """One toggle of the main bar, at the end of the bar on the side its
    panel opens (design pass 10 §3; design pass 14 §10):
    `button.bl-fold.bl-toggle`, 26 × 26 px, with data-fold `fold`, which
    window.vue reads, so that a click or Enter folds the open panel and
    opens the folded one, and which window.vue marks open by
    `aria-expanded`; its accessible name and its hover the panel's name
    (`PANEL_NAMES`), and its icon at 16 px (`icons.toggle_icon`; N-D10).
    While `waits`, the hover of a panel with nothing to show, is given, it
    carries `aria-disabled`, which brand.css draws at 40 percent and
    window.vue does not fold, and `waits` is its hover."""
    name = PANEL_NAMES[fold]
    attributes = {"type": "button", "data-fold": fold, "title": waits or name, "aria-label": name}
    if waits is not None:
        attributes["aria-disabled"] = "true"
    return rv.Html(
        tag="button",
        class_="bl-fold bl-toggle",
        attributes=attributes,
        children=[icons.toggle_icon(fold)],
    )


def show_wide(panel: str) -> None:
    """Shows the panel `panel`, `recipe`, `types` or `details`, in its wide
    panel over the window (AAS, L-D12; design pass 9 §2), or, where it
    stands there, returns it to its column."""
    region_wide.value = None if region_wide.value == panel else panel


def close_wide(data=None) -> None:
    """Closes the panel that stands in its wide panel (L-D12): Escape, which
    window.vue reads and sends with no data, and a press on the ground under
    a panel's wide panel."""
    region_wide.value = None


def on_region_folded(region: str) -> None:
    """window.vue's fold of the region `region`, by the main bar's toggle, a
    panel's `×` or a command: a panel folded while it stands in its wide
    panel leaves it, so that no ground stands over the window with no panel
    on it (`WideGround`; unit L's final judgment, §6 item 11); the fold
    `inspector` folds the Recipe tab and the four tabs alike
    (`PANEL_FOLDS`)."""
    if region_wide.value is not None and PANEL_FOLDS[region_wide.value] == region:
        region_wide.value = None


@solara.component
def WideButton(panel: str):
    """The icon button `open wide` of the panel `panel`, in the strip of the
    panel under the editor, `recipe` or `types` (`InspectorStrip`), or in
    the head of `details` (AAS, L-D12; design pass 8 §§3 and 5.5), the
    Codicon `window` (`ToolbarButton`), `.bl-region-wide`, whose hover says
    what its click does, a click showing the panel in its wide panel over
    the window and, while it stands there, returning it to its column
    (`show_wide`); `aria-pressed` whether the panel stands wide."""
    wide = region_wide.value == panel
    words = f"Return {panel} to its column" if wide else f"Open {panel} in a wide panel"
    return ToolbarButton(
        "open wide",
        "Open wide",
        words,
        lambda: show_wide(panel),
        "bl-region-wide",
        {"aria-pressed": "true" if wide else "false"},
    )


@solara.component
def WideGround():
    """The ground under a panel's wide panel (AAS, L-D12), `.bl-wide-ground`,
    the forms' ground, the chrome at 70 percent over the window, drawn while
    `region_wide` names a panel; a press on it closes the wide panel
    (`close_wide`), as a press outside the recipe's wide panel closes
    that."""
    ground = rv.Html(tag="div", class_="bl-wide-ground")
    rv.use_event(ground, "click", lambda *_: close_wide())
    return ground


@solara.component
def CloseButton(panel: str, wide: bool = False):
    """The icon button `close` at the right end of the head of the panel
    `panel` (AAS, L-D12; design pass 8 §§3 and 5.5), the Codicon `close`
    (`ToolbarButton`), `.bl-region-close`, its hover and accessible name
    `Close <panel>`. In the panel's column it is a fold button, `.bl-fold`
    with `data-fold` naming the panel's fold (`PANEL_FOLDS`), which
    window.vue reads and so closes the panel, the main bar's toggle opening
    it again; with `wide`, standing in the panel's wide panel, its click
    closes the wide panel (`close_wide`), the panel returning to its
    column."""
    words = f"Close {panel}"
    # the fold button's click is window.vue's alone
    return ToolbarButton(
        "close",
        words,
        words,
        lambda: close_wide() if wide else None,
        "bl-region-close" if wide else "bl-fold bl-region-close",
        None if wide else {"data-fold": PANEL_FOLDS[panel]},
    )


def RegionHead(panel: str, context: list, wide=None, closing=None, classes: str = ""):
    """The head of the panel `panel`, `details`, the panel under the editor
    having its strip in place of a head (`InspectorStrip`; design pass 10
    §4); the one head of design pass 8 §5.5 for columns and panels alike:
    `.bl-head.bl-region-head` with `data-panel` and the classes `classes`,
    one line 28 px high on the region's own ground over a hairline, holding
    the panel's name `.bl-region-name` in Head, the name of its fold's
    toggle, `Details` (`PANEL_NAMES`; AAS, L-D28), its context
    `.bl-region-context` in Code small, the children `context`, then at the
    right end, in `.bl-head-actions`, `wide`, the button that shows the
    panel wide, where one is given, and `closing`, the panel's close button,
    by default its fold button (`CloseButton`). The toggle's icon is not
    repeated in the head (§5.5; §8 item 4)."""
    actions = [wide] if wide is not None else []
    actions.append(closing if closing is not None else CloseButton(panel))
    return rv.Html(
        tag="div",
        class_=f"bl-head bl-region-head {classes}".strip(),
        attributes={"data-panel": panel},
        children=[
            rv.Html(
                tag="h2", class_="bl-region-name", children=[PANEL_NAMES[PANEL_FOLDS[panel]]]
            ),
            rv.Html(tag="span", class_="bl-region-context bl-code-small", children=list(context)),
            rv.Html(tag="span", class_="bl-head-actions", children=actions),
        ],
    )


def crumbs(current: Shown | None) -> list[navigation.Crumb]:
    """The parts of the main bar's path, read from the tab's state
    (`navigation.breadcrumb`): in the trellis view, the trellis of the tab's
    recipe, ending in the selected occurrence, the head, as its period, a
    link, and its key where one is selected, so that the occurrence stands
    as the path's last parts (design pass 10 §§2 and 3), the recipe then no
    link, since its trellis is the one shown (specification §10: a control
    that does not act is not shown); in a stage's view,
    the stage shown, `current`, by its file, the recipe it was bound
    through, its positions there and the head, so that a file opened as
    text with the view unchanged leaves the parts as the view's; the folder
    alone while a stage's view shows no stage."""
    folder = tab_folder.value.root.name
    if view_mode.value == "trellis":
        chosen = source.value
        parts = navigation.breadcrumb(folder, chosen.path if chosen is not None else None)
        if chosen is None or not head.value:
            return parts
        h, key = head.value
        return [*parts, navigation.Crumb(f"periods[{h}]", "period"), navigation.Crumb(key, None)]
    if current is None:
        return navigation.breadcrumb(folder)
    bound = current.source.path if current.source is not None else None
    return navigation.breadcrumb(folder, bound, current.path, current.positions, head.value)


def _shows_first() -> bool:
    """Whether the tab shows what the folder opens on (`first_file`), so
    that the breadcrumb's folder, whose click opens it, would change
    nothing and is no link (specification §10: a control that does not act
    is not shown): the trellis of the folder's first source with that
    source's file open, or, where the folder offers no source, its first
    stage file in its view. A folder that holds neither answers True, since
    the click opens nothing there."""
    first = first_file()
    if first is None:
        return True
    if (switching.value or open_path.value) != first:
        return False
    if sources.value:
        return view_mode.value == "trellis" and source.value == sources.value[0]
    return view_mode.value == "stage"


def occurrence_named(parts: list) -> str:
    """The occurrence the main bar's path names in its last two parts, in
    the package's form of an occurrence, `periods[0] / tenure`: in the
    trellis view and at a chosen position the period, a link, then the key,
    `… › periods[3] › tenure`; in a stage's view at no position chosen the
    key, then the period of the occurrence the stage is bound as, `… ›
    tenure › periods[0]` (`navigation.breadcrumb`; the fix wave Q3b, item
    19, C19); the empty string where they name none."""
    if len(parts) < 2:
        return ""
    first, last = parts[-2], parts[-1]
    if first.link == "period":
        return f"{first.text} / {last.text}"
    if first.link is None and _PERIOD_WORD.fullmatch(last.text):
        return f"{last.text} / {first.text}"
    return ""


@solara.component
def CrumbItem(
    text: str,
    link: str | None,
    title: str = "",
    on_click=None,
    occurrence: bool = False,
    folder: bool = False,
):
    """One part of the main bar's path: its text, and, where `on_click` is
    given, a link that calls it, a button, so that Tab reaches it and Enter
    calls it, carrying `data-link`, the kind of the link, and `title`, what
    it shows; with `occurrence`, `.bl-occurrence-crumb`, one of the two
    parts that name the selected occurrence (design pass 10 §3); with
    `folder`, `.bl-folder-crumb`, the model's folder, which brand.css draws
    in ink-3 where every other part is ink-1 (design pass 13 §3; C4)."""
    classes = "bl-crumb" + (" bl-occurrence-crumb" if occurrence else "")
    classes += " bl-folder-crumb" if folder else ""
    children = [text]
    if on_click is None:
        item = rv.Html(tag="span", class_=classes, children=children)
    else:
        item = rv.Html(
            tag="button",
            class_=classes,
            attributes={"type": "button", "data-link": link, "title": title},
            children=children,
        )

    def click(*_):
        if on_click is not None:
            on_click()

    rv.use_event(item, "click", click)
    return item


@solara.component
def MainBar(current: Shown | None):
    """The main bar, the first row of the window (design pass 10 §§2 and 3;
    the brief's top bar; AMD-MI-002 §3 rules 3 to 5), `nav.bl-main-bar`, 36
    px, in three groups. At the left, `.bl-main-start`: the brand's mark,
    `a.bl-mark`, the silhouette at 20 px, a link to the page of Bellman
    Workbench in the documentation; then the icon buttons `Back` and
    `Forward` (`ToolbarButton`), which step back and forward through the
    tab's history as Alt+← and Alt+→ do, always drawn and disabled while no
    place stands behind or ahead. In the middle, `.bl-main-path`: the path
    the tab took, `.bl-crumbs` (`crumbs`), in Label, its parts parted by
    the Codicon `chevron-right`, the text `›` kept unseen in the path's
    text (design pass 13 §3), its
    hover the whole path, each part but the last a link: the folder to what
    the folder opens on (`first_file`), unless the tab shows it already, the
    recipe to its trellis, and the period to that trellis with the period
    open; the two parts that name the selected occurrence are marked
    (`occurrence_named`), a stage's view naming its occurrence there once,
    `durables › spec.yml › tenure › periods[0]` (the fix wave Q3b, item 19,
    C19); after it, what the occurrence line under the tree held that the
    path does not name, the select of the positions among it, its words in
    ink-2 at rest (`PathOccurrence`; N5). The toggles of the four panels
    (`Toggle`) stand at the end of the bar on the side of the window where
    their panels open (design pass 14 §10; S-D16): after `Forward` in
    `.bl-main-start` the Files column's and the Inspector's, the panels of
    the window's left and middle, the Inspector's disabled while the open
    file gives it nothing to show (`inspector_hover`); at the right,
    `.bl-main-end`, the icon button `Go to`, the Codicon `search`, which
    opens Goto Anything (`open_goto`; spec 0.4 §5.8; brief rule 9), then
    the toggles of Details and of Matsya, the window's right columns,
    Matsya's absent with the setting `off` (`MATSYA_OFF`)."""
    root = solara.use_router().root_path
    places = history.value
    parts = crumbs(current)
    # the recipe the parts name: the tab's in the trellis view, the shown
    # stage's in a stage's view
    named = source.value
    if view_mode.value == "stage" and current is not None:
        named = current.source
    first = first_file()
    links = {
        "folder": (
            f"the folder as it opens: {first}",
            None if _shows_first() else (lambda: open_from_tree(first)),
        ),
        "recipe": (
            f"the trellis of {named.path}" if named is not None else "",
            lambda: show_recipe(named),
        ),
        "period": (
            f"the trellis of {named.path} with this period open" if named is not None else "",
            lambda: show_period(named, head.value),
        ),
    }
    # the last two parts name the selected occurrence, its period and its
    # key in either order (`occurrence_named`)
    named_from = len(parts) - 2 if occurrence_named(parts) else len(parts)
    children = []
    for number, part in enumerate(parts):
        if number:
            # the separator is the Codicon `chevron-right`; its text stays in
            # the path's text, which the page's readers read, and is not drawn
            # (design pass 13 §3; C4)
            children.append(
                rv.Html(
                    tag="span",
                    class_="bl-crumb-separator",
                    children=[
                        UnseenText(navigation.SEPARATOR),
                        icons.codicon(icons.CODICONS["path separator"]),
                    ],
                ).key(f"{number} separator")
            )
        title, click = links.get(part.link, ("", None))
        children.append(
            CrumbItem(
                part.text, part.link, title, click, number >= named_from, number == 0
            ).key(f"{number} {part.link}")
        )
    path = navigation.SEPARATOR.join(part.text for part in parts)
    with rv.Html(tag="nav", class_="bl-main-bar", attributes={"aria-label": "main bar"}):
        with rv.Html(tag="div", class_="bl-main-start"):
            rv.Html(
                tag="a",
                class_="bl-mark",
                attributes={"href": WORKBENCH_PAGE, "target": "_blank", "title": MARK_HOVER},
                children=[
                    rv.Html(
                        tag="img",
                        attributes={
                            "src": f"{root}/static/assets/brand/favicon.svg",
                            "alt": "Bellman Workbench",
                        },
                    )
                ],
            )
            ToolbarButton("back", "Back", "Back", go_back, "bl-back", disabled=not places.behind)
            ToolbarButton(
                "forward",
                "Forward",
                "Forward",
                go_forward,
                "bl-forward",
                disabled=not places.ahead,
            )
            for fold in LEFT_PANELS:
                waits = inspector_hover(open_path.value) if fold == "inspector" else None
                Toggle(fold, waits).key(fold)
        with rv.Html(tag="div", class_="bl-main-path"):
            # the path is cut at its left (brand.css), the parts standing in
            # one element of their own direction
            rv.Html(
                tag="span",
                class_="bl-crumbs",
                attributes={"title": path},
                children=[rv.Html(tag="span", class_="bl-crumbs-text", children=children)],
            )
            PathOccurrence(current, open_path.value)
        with rv.Html(tag="div", class_="bl-main-end"):
            ToolbarButton("go to", "Go to", "Go to", open_goto, "bl-goto-button")
            for fold in RIGHT_PANELS:
                if fold == "matsya" and MATSYA_OFF:
                    continue
                Toggle(fold).key(fold)


@solara.component
def ToolbarButton(
    control: str,
    label: str,
    hover: str,
    act,
    classes: str,
    attributes=None,
    disabled: bool = False,
    stop: bool = False,
):
    """An icon button of VSCode Elements, `<vscode-toolbar-button>` (design
    pass 8 §4: the class `icon`), drawing the Codicon of the control
    `control` (`icons.CODICONS`) in a 24 × 24 px target, with the accessible
    name `label`, the hover `hover`, the classes `classes` and any further
    attributes `attributes`; a click, or Enter or Space on its button, calls
    `act`. A `disabled` button, which the library's toolbar button does not
    know, carries `aria-disabled`, which brand.css draws at 40 percent with
    the arrow pointer; its hover, which then names what it waits for, is
    still shown, and its click calls nothing (§5.5: disabled). Where `stop`,
    the click is stopped at the button, so that an element around it that
    answers a click, the Recipe tab's row, does not read it (design pass 11
    §2)."""
    marked = {"aria-disabled": "true"} if disabled else {}
    button = rv.Html(
        tag="vscode-toolbar-button",
        class_=classes,
        attributes={
            "icon": icons.CODICONS[control],
            "label": label,
            "title": hover,
            **(attributes or {}),
            **marked,
        },
    )
    rv.use_event(button, "click.stop" if stop else "click", lambda *_: None if disabled else act())
    return button


@solara.component
def TextButton(
    words: str,
    act,
    classes: str = "",
    hover: str | None = None,
    attributes=None,
    waits: str | None = None,
    icon: str | None = None,
):
    """A button of the class `text only` of design pass 8 §§4 and 5.3,
    `button.bl-text-button`, the page's own: its words `words` in Label in
    ink-2, 26 px high with a radius of 4 px, no border and no fill, with
    the classes `classes`, the hover `hover` and any further attributes
    `attributes`, and, where `icon` names a control of `icons.CODICONS`, its
    Codicon before the words; a click calls `act`. While `waits`, the few
    words that name what it waits for, is given, it carries
    `aria-disabled`, which brand.css draws at 40 percent with the arrow
    pointer, `waits` is its hover and its click calls nothing (§5.5:
    disabled)."""
    given = {"type": "button", **({"title": hover} if hover else {}), **(attributes or {})}
    if waits is not None:
        given.update({"title": waits, "aria-disabled": "true"})
    glyph = [icons.codicon(icons.CODICONS[icon])] if icon is not None else []
    button = rv.Html(
        tag="button",
        class_=f"bl-text-button {classes}".strip(),
        attributes=given,
        children=[*glyph, words],
    )
    rv.use_event(button, "click", lambda *_: None if waits is not None else act())
    return button


@solara.component
def CommandButton(
    words: str,
    act,
    classes: str = "",
    hover: str | None = None,
    waits: str | None = None,
    secondary: bool = False,
):
    """A button of VSCode Elements, `<vscode-button>` (design pass 8 §§4 and
    5.3), the primary, filled in the accent's fill, or with `secondary` the
    secondary, on raised-2: its words `words` in Label, 26 px high with a
    radius of 4 px, the classes `classes` and the hover `hover`. While
    `waits`, the few words that name what it waits for, is given, it is
    disabled at 40 percent with `waits` as its hover (§5.5: disabled), and
    `aria-disabled`, by which a reader of the page knows it does not act;
    else a click calls `act`."""
    attributes = {}
    if secondary:
        attributes["secondary"] = True
    if waits is not None:
        attributes.update({"disabled": True, "aria-disabled": "true", "title": waits})
    elif hover:
        attributes["title"] = hover
    button = rv.Html(
        tag="vscode-button", class_=classes, attributes=attributes, children=[words]
    )
    rv.use_event(button, "click", lambda *_: None if waits is not None else act())
    return button


@solara.component
def UnseenText(text: str):
    """The text `text` in `span.bl-unseen`, which brand.css does not draw: a
    separator that the system draws as a glyph or as a space (design pass 8
    §6) and that stays in the text of its line, which the page's readers and
    its tests read."""
    return rv.Html(tag="span", class_="bl-unseen", children=[text])


@solara.component
def ErrorMark():
    """One Problems control for current errors and whole-model checks: the
    errors, the connections to check and the headers to check, a backward
    header that lists a value input no line of its block reads
    (`UNREAD_INPUT_RULE`), which the package keeps as a diagnostic and the
    list counts among the problems to review."""
    standing = standing_refusals()
    texts = trellis.texts_of(unsaved_texts())
    items = lacking_items(checklist.value, trellis_outcome.value, trellis_shown.value,
                          tab_folder.value, texts)
    # Bindings already have one row in standing_refusals, with their source links.
    items = [item for item in items if item.kind != "refused"]
    errors = [item for item in standing if item.severity == "error"]
    review = [item for item in standing if item.severity != "error"]
    headers = [item for item in review if item.rule == UNREAD_INPUT_RULE]
    connections = [item for item in review if item.rule != UNREAD_INPUT_RULE]
    count = len(standing) + len(items)
    opened = errors_open.value
    with rv.Html(tag="span", class_="bl-errors"):
        ErrorButton(count, opened, len(errors))
        with rv.Html(tag="div", class_="bl-error-list" + ("" if opened else " bl-hidden"),
                     attributes={"id": "bl-problems-list", "aria-label": "Problems"}):
            if not count:
                rv.Html(tag="p", class_="bl-error-none", children=["No problems reported"])
            for label, records in (("Errors", errors), ("Connections to check", connections),
                                   ("Headers to check", headers)):
                if records:
                    with rv.Html(tag="section", class_="bl-problem-group"):
                        rv.Html(tag="h3", class_="bl-problem-heading", children=[label])
                        with rv.Html(tag="ul"):
                            for number, refusal in enumerate(records):
                                ErrorLine(refusal).key(f"{label} {number} {refusal.sentence}")
            for kind, label in (("unjoined", "Unjoined fields"), ("check", "Entries to check")):
                records = [item for item in items if item.kind == kind]
                if records:
                    with rv.Html(tag="section", class_=f"bl-problem-group bl-problem-{kind}",
                                 attributes={"data-count": str(len(records))}):
                        rv.Html(tag="h3", class_="bl-problem-heading", children=[label])
                        rv.Html(tag="span", class_="bl-problem-scope", children=["Whole model"])
                        with rv.Html(tag="ul", class_="bl-checklist-list"):
                            for item in records:
                                with rv.Html(tag="li").key(f"{item.kind}:{item.file}:{item.line}:{item.label}"):
                                    ChecklistItem(item)
                                    rv.Html(tag="span", class_="bl-problem-detail", children=[item.sentence])


@solara.component
def ErrorButton(count: int, opened: bool, errors: int | None = None):
    """A native button whose accessible name gives both kinds of count:
    the Codicon `error` while an error stands, or nothing is reported, and
    `warning` while only checks to review stand, the icon and the count in
    the alarm's orange (design pass 13 §5; Q-D8)."""
    errors = count if errors is None else errors
    glyph = "checks mark" if count and not errors else "error mark"
    children = [icons.codicon(icons.CODICONS[glyph], "bl-error-icon")]
    if count:
        children.append(rv.Html(tag="span", class_="bl-error-count", children=[str(count)]))
    classes = "bl-error-mark" + (" bl-has-errors" if errors else "")
    classes += ("" if count else " bl-quiet") + (" bl-active" if opened else "")
    label = "Problems: none reported" if not count else f"Problems: {errors} error" + ("" if errors == 1 else "s") + f", {count-errors} to review"
    item = rv.Html(tag="button", class_=classes, attributes={
        "type": "button", "title": label, "aria-label": label,
        "aria-expanded": "true" if opened else "false", "aria-controls": "bl-problems-list",
    }, children=children)
    rv.use_event(item, "click", lambda *_: toggle_errors())
    return item


@solara.component
def ErrorLine(refusal: Refusal):
    """The unchanged diagnostic sentence, followed by its source controls."""
    children = [rv.Html(tag="span", class_="bl-error-sentence", children=[refusal.sentence])]
    places = refusal.places or ((refusal.file, refusal.line),)
    for file, line in places:
        if file is not None and line is not None:
            children.append(ErrorPlace(file, line))
        elif file is not None:
            children.append(rv.Html(tag="span", class_="bl-error-file", children=[file]))
    if refusal.opens is not None:
        children.append(OpenModelButton(refusal.opens))
    return rv.Html(tag="li", class_="bl-error-line", attributes={"data-severity": refusal.severity}, children=children)


@solara.component
def OpenModelButton(path: str):
    """The button `open <name>`, `<name>` that of the model folder `path`,
    beside the note of a model's `declaration/` opened by itself (unit L,
    Task 28; AAS, L-D23): a click opens the model folder in the tab
    (`open_model_above`), a text button (design pass 8 §§5.3 and 6;
    M-I23). While a buffer holds unsaved text, which the change of folder
    would discard, it does not act, and its hover names the files
    (`_unsaved_sentence`). Its words stay in the lowercase of the list's
    other words (M-I19)."""
    return TextButton(
        f"open {Path(path).name}",
        lambda: open_model_above(path),
        "bl-error-action",
        waits=_unsaved_sentence(None),
    )


@solara.component
def ErrorPlace(path: str, line: int):
    """The source button of a line of the list under the error mark, `<file>:<line>`,
    carrying `data-path` and `data-line`; a click opens the file at that
    line and records the place left (`open_at`)."""
    item = rv.Html(
        tag="button",
        class_="bl-error-place",
        attributes={
            "type": "button",
            "data-path": path,
            "data-line": str(line),
            "title": f"open {path} at line {line}",
        },
        children=[f"{path}:{line}"],
    )
    rv.use_event(item, "click", lambda *_: open_at(path, line))
    return item


# the place before each separator of a name of the tree, `_`, `.`, `-` or a
# space, that follows a character other than a separator: a word of the
# name begins there, with its separators (unit L, Task 22)
WORD_START = re.compile(r"(?<=[^_.\- ])(?=[_.\- ])")


def name_words(name: str) -> list[str]:
    """The words of the name `name` of a file or a folder of the tree, each
    beginning at a separator with the separators before it, so that
    `period.pensions.yml` is `period`, `.pensions` and `.yml`, and
    `adjuster_cons_pa/` is `adjuster`, `_cons` and `_pa/` (unit L, Task
    22). The words' texts make the name."""
    return WORD_START.split(name)


def name_box(name: str):
    """The name `name` of a file or a folder of the tree as the box
    `.bl-tree-name`, one span `.bl-name-word` for each of its words
    (`name_words`), each an inline block, which brand.css lays on one line
    and cuts by `text-overflow` at its end, after its last word that fits,
    with an ellipsis, never within a word (unit L, Task 22; defect 23 of
    the UX simulation; the delegated acceptance of unit M, D1). The box is
    never narrower than its first word and, where other words follow, an
    ellipsis, measured in `ch`, the width of a digit of the row's face."""
    words = name_words(name)
    least = len(words[0]) + (1 if len(words) > 1 else 0)
    return rv.Html(
        tag="span",
        class_="bl-tree-name",
        style_=f"min-width: {least}ch",
        children=[rv.Html(tag="span", class_="bl-name-word", children=[word]) for word in words],
    )


def Twistie(folded: bool | None):
    """The twistie of a row of the tree or of the checklist's head, 16 px
    (design pass 8 §§3 and 5.2): the Codicon `chevron-right` while its rows
    are folded and `chevron-down` while they are unfolded, or, for `None`,
    a file's row, the empty box of the same width, so that every name of a
    level starts at one edge."""
    if folded is None:
        return rv.Html(tag="span", class_="bl-twistie")
    glyph = icons.CODICONS["folded" if folded else "unfolded"]
    return icons.codicon(glyph, "bl-twistie")


@solara.component
def FileRow(entry: dict, is_open: bool, is_dirty: bool, deleted: bool = False):
    """One file of the tree, a row of 24 px, `.bl-row` (design pass 8 §§5.2
    and 6): the empty twistie (`Twistie`), its name in Label, cut at its end
    after a whole word where the row is too narrow (`name_box`), and git's
    letters and the word `unsaved` for a buffer that differs from the file,
    in Small, which give up their room once the name holds no more than its
    first word; a click opens it. The open file's row is drawn selected.
    The row prints no count of the checklist (unit K's decision K-D28). A
    file listed to delete on save, `deleted`, is drawn dimmed,
    `.bl-deleting`, its mark `deleted on save` (unit L, Task 25)."""
    mark = entry["git"].strip()
    if is_dirty:
        mark = f"{mark} unsaved" if mark else "unsaved"
    if deleted:
        mark = creation.DELETED_ON_SAVE
    classes = f"bl-row bl-tree-file bl-role-{entry['role']}" + (" bl-open" if is_open else "")
    classes += " bl-deleting" if deleted else ""
    title = entry["path"] + (" (unsaved changes)" if is_dirty else "")
    children = [
        Twistie(None),
        name_box(entry["name"]),
        rv.Html(
            tag="span",
            class_="bl-tree-mark" + (" bl-dirty" if is_dirty else ""),
            children=[mark],
        ),
    ]
    row = rv.Html(
        tag="div",
        class_=classes,
        attributes={"data-path": entry["path"], "title": title},
        children=children,
    )
    rv.use_event(row, "click", lambda *_: open_from_tree(entry["path"]))
    return row


@solara.component
def FolderRow(entry: dict, closed: bool, deleted: bool = False):
    """One folder of the tree, a row of 24 px, `.bl-row` (design pass 8
    §§5.2 and 6): its twistie, the Codicon `chevron-right` while closed and
    `chevron-down` while open (`Twistie`), then its name in Label, with no
    slash after it (§8, item 9), cut at its end after a whole word where the
    row is too narrow (`name_box`); a click closes it or opens it. A folder
    listed to delete on save, `deleted`, is drawn dimmed, `.bl-deleting`,
    with the mark `deleted on save` at its right (unit L, Task 25)."""
    children = [Twistie(closed), name_box(entry["name"])]
    if deleted:
        children.append(
            rv.Html(tag="span", class_="bl-tree-mark", children=[creation.DELETED_ON_SAVE])
        )
    row = rv.Html(
        tag="div",
        class_="bl-row bl-folder-row"
        + (" bl-closed" if closed else "")
        + (" bl-deleting" if deleted else ""),
        attributes={"data-path": entry["path"], "title": entry["path"] + "/"},
        children=children,
    )
    rv.use_event(row, "click", lambda *_: toggle_folder(entry["path"]))
    return row


@solara.component
def RemoveControl(path: str, deleted: bool):
    """The tree's control at the right of the row of the file or folder
    `path`, relative to the folder (unit L, Task 25; AAS, L-D18), with
    data-path and the class `.bl-tree-remove`: for a period file or a stage
    folder that no file of the folder names, the icon button `Remove`, the
    Codicon `trash` (design pass 8 §3), its hover naming the deletion, which
    marks it to delete on the next save; for a file listed to delete on
    save, the text button `Keep`, which withdraws the mark
    (`toggle_deletion`). It stands beside the row and not within it, so
    that its click neither opens the file nor folds the folder."""
    if deleted:
        return TextButton(
            KEEP_FILE,
            lambda: toggle_deletion(path),
            "bl-tree-remove",
            f"Keep {path}",
            {"data-path": path},
        )
    return ToolbarButton(
        "remove",
        REMOVE_FILE,
        f"Delete {path} on the next save",
        lambda: toggle_deletion(path),
        "bl-tree-remove",
        {"data-path": path},
    )


@solara.component
def Tree(
    entries: list,
    open_relpath: str | None,
    dirty: set,
    opened: tuple,
    removable: tuple = (),
    deleted: frozenset = frozenset(),
    depth: int = 0,
):
    """The folder's entries at the level `depth`, folders first, each
    folder of `opened` with its children indented under its name, 8 px
    further in (design pass 8 §5.2), and every other folder closed (R-D52).
    Every row spans the column, its indent the row's left padding, which
    brand.css reads from the custom property --bl-tree-depth of its level,
    so that a row's wash and the open file's bar start at the column's edge
    (design pass 13 §4; D11). The row of a file or folder of
    `removable`, which no file of the folder names, or of `deleted`, listed
    to delete on save, stands in `div.bl-tree-entry` beside the control that
    marks it or withdraws its mark (`RemoveControl`; unit L, Task 25)."""
    with rv.Html(tag="div", class_="bl-tree-level", style_=f"--bl-tree-depth: {depth}"):
        for entry in entries:
            path = entry["path"]
            listed = path in deleted
            controlled = listed or path in removable
            if entry["kind"] == "folder":
                is_closed = path not in opened
                with rv.Html(tag="div", class_="bl-tree-folder").key(path):
                    if controlled:
                        with rv.Html(tag="div", class_="bl-tree-entry"):
                            FolderRow(entry, is_closed, listed)
                            RemoveControl(path, listed)
                    else:
                        FolderRow(entry, is_closed)
                    if not is_closed:
                        with rv.Html(tag="div", class_="bl-tree-children"):
                            Tree(
                                entry["children"],
                                open_relpath,
                                dirty,
                                opened,
                                removable,
                                deleted,
                                depth + 1,
                            )
            else:
                is_open = path == open_relpath
                if controlled:
                    with rv.Html(tag="div", class_="bl-tree-entry").key(path):
                        FileRow(entry, is_open, path in dirty, listed)
                        RemoveControl(path, listed)
                else:
                    FileRow(entry, is_open, path in dirty).key(path)


@dataclasses.dataclass(frozen=True)
class Lack:
    """One model check (unit K's decisions K-D10 and K-D28):
    `kind`, `refused` for a binding the package refused
    (`trellis.refused_bindings`), `unjoined` for an arrival field no join
    reaches (`trellis.missing_joins`) or `check` for an entry answers.yml
    marks (`creation.checklist`), an empty connector it requires or a
    mapping or a range to check; `label`, the words it prints; `file`,
    relative to the folder, `line` and `column`, where a click opens the
    file; `place`, the first line of its hover, the file and the line, with
    the address where one is written; and `sentence`, the hover's second
    line. A slot of the recipe is no item (K-D29)."""

    kind: str
    label: str
    file: str
    line: int
    column: int
    place: str
    sentence: str


# The class of the checklist's item of each kind.
LACK_CLASSES = {
    "refused": "bl-checklist-refused",
    "unjoined": "bl-checklist-unjoined",
    "check": "bl-checklist-entry",
}
def lacking_items(entries, outcome, held, folder, texts=None) -> list[Lack]:
    """The model checks (usability walkthrough §4 items 9 and
    16 and §5; unit K's decisions K-D10 and K-D28), each item with its file
    and line: where `held` is the trellis the last reading `outcome`
    answered, each binding the package refused
    (`trellis.refused_bindings`), `disc · calibration refused`, its hover
    the package's sentence with its paths printed from the folder
    (`trellis.relative_sentence`; K-D11), and each arrival field no join
    reaches but those of the earliest period (`trellis.missing_joins`),
    `cons · m unjoined`; then each entry of `entries`,
    `creation.checklist`'s, by its file's name and its address,
    `trellis.yml · inter_connectors[0]`. Each stands at its place in the
    folder `folder`, a `model.Folder`, the files read through `texts`, the
    mapping of unsaved texts. No slot of the recipe is listed, since a slot
    is a parameter of the load and no lack (K-D29)."""
    items = []
    if held is not None and outcome is not None and outcome.shown is held:
        for found in trellis.refused_bindings(folder, held, texts):
            named = f"{found['key']} · {found['kind']}" if found["key"] else found["kind"]
            place = f"{found['file']}:{found['line']}"
            # the package's sentence with its paths from the folder (K-D11)
            sentence = trellis.relative_sentence(folder, found["sentence"])
            label = f"{named} refused"
            items.append(Lack("refused", label, found["file"], found["line"], 1, place, sentence))
        for found in trellis.missing_joins(folder, held, texts):
            key, field, periods = found["key"], found["field"], found["periods"]
            sentence = f"no join reaches the arrival field {field} of {key} at periods {periods}"
            label = f"{key} · {field} unjoined"
            place = f"{found['file']}:{found['line']}"
            items.append(Lack("unjoined", label, found["file"], found["line"], 1, place, sentence))
    for entry in entries:
        label = f"{Path(entry.file).name} · {entry.address}"
        place = f"{entry.file}:{entry.line} {entry.address}"
        items.append(
            Lack("check", label, entry.file, entry.line, entry.column, place, entry.sentence)
        )
    return items


@solara.component
def ChecklistItem(item: Lack):
    """One model check (`Lack`), with the source control in the tree's form (design
    pass 8 §6), a button `.bl-row` in the class of its kind
    (`LACK_CLASSES`), with data-file and data-line: its label in Label,
    which wraps at a space and is never cut (design pass 2 §1 item 9; unit
    K, Task 6); on hover its place, `declaration/trellis.yml:10
    inter_connectors[0]`, and its sentence on a second line; a click opens
    the file with the editor there."""
    row = rv.Html(
        tag="button",
        class_=f"bl-row {LACK_CLASSES[item.kind]}",
        attributes={
            "type": "button",
            "data-file": item.file,
            "data-line": str(item.line),
            "title": f"{item.place}\n{item.sentence}",
        },
        children=[Twistie(None), rv.Html(tag="span", children=[item.label])],
    )
    rv.use_event(row, "click", lambda *_: open_at(item.file, item.line, item.column))
    return row


# The words that name what a control waits for while a git command runs,
# the hover of `New trellis` and of the commit form's `Commit` (design pass
# 8 §5.5: a disabled control's hover names what it waits for).
GIT_RUNNING = "git is running"


@solara.component
def FolderActions():
    """The folder's actions at the right end of its head `Files` (design
    pass 8 §6), each an icon button of VSCode Elements (`ToolbarButton`;
    specification §4): `New trellis`, the Codicon `new-folder`, which writes
    a model folder from templates under the folder the Workbench was started
    on, disabled while a git command runs, since it opens the new folder in
    the tab, its hover then `git is running` (§5.5); `New variant`,
    `versions`, which writes a second trellis of the model beside the
    first, where the tab's folder holds the recipe
    `declaration/spec.yml`; and `New stage`, `new-file`, which opens the
    form that writes an empty stage file of the author's own and its row in
    the recipe, where the tab's folder holds the recipe the forms edit
    (`_form_recipe`; unit K's decision K-D7). Each names its act as its
    accessible name and says what it writes in its hover. Last,
    `Notebook`, `notebook`, which writes `notebooks/<folder>.ipynb` for the
    source of a trellis shown (`run_notebook`), omitted while the tab has no
    source and once the file exists (spec 0.4 §5.9; R-D41)."""
    # the folder's entries, read so that the actions are drawn again when
    # the folder is read again, as after `notebook` writes its file (R-D41)
    tree.value
    root = tab_folder.value.root
    notebook = creation.notebook_file(root)
    with rv.Html(tag="span", class_="bl-head-actions bl-folder-bar"):
        # while git runs, the hover names what the button waits for (§5.5)
        ToolbarButton(
            "new trellis",
            "New trellis",
            GIT_RUNNING if git_task.pending else "Write a model folder beside this one",
            lambda: open_form("new trellis"),
            "bl-new-trellis",
            disabled=git_task.pending,
        )
        if (root / creation.factory_path(creation.RECIPE)).is_file():
            ToolbarButton(
                "new variant",
                "New variant",
                "Write a variant of the recipe beside it",
                lambda: open_form("new variant"),
                "bl-new-variant",
            )
        if (root / creation.factory_path(_form_recipe())).is_file():
            ToolbarButton(
                "new stage",
                "New stage",
                "Write an empty stage file and its row in the recipe",
                lambda: open_form("new stage"),
                "bl-new-stage",
            )
        if source.value is not None and not (root / notebook).exists():
            ToolbarButton(
                "notebook",
                "Notebook",
                f"Write {notebook}",
                run_notebook,
                "bl-notebook",
            )


def recipe_head(current: Shown | None, path: str | None) -> str:
    """The head, the selected occurrence (specification §2.1 and §3.2): in
    the trellis view, the occurrence selected, `periods[h] / <key>`, or the
    empty string while none is, since no sentence stands on the page (unit
    K's decision K-D30; design pass 2 §11); in a stage's view, the
    occurrence the shown stage is bound as, or the words that the source it
    was bound through, a recipe or a trellis file, holds no occurrence of
    the file; where it was bound through no source, that no recipe holds
    it where no source of the folder holds it (`current.uses`), and the
    empty string where one does, since the main bar then names those
    sources after `held by` (`PathOccurrence`; unit L's final judgment, §6
    item 3); and the empty string for a file that is no stage or before one
    elaborated."""
    if view_mode.value == "trellis":
        chosen = head.value
        return f"periods[{chosen[0]}] / {chosen[1]}" if chosen else ""
    if not _is_stage(path) or current is None or current.path != path:
        return ""
    if current.occurrence:
        return current.occurrence
    if current.source is None:
        return "" if any(held for _, held in current.uses) else "no recipe holds this file"
    return f"{current.source.path} holds no occurrence of this file"


@solara.component
def PathOccurrence(current: Shown | None, path: str | None):
    """The selected occurrence after the main bar's path, where the path
    does not name it (specification §2.1 and §3.2; AMD-MI-002 §3 rule 5;
    design pass 10 §§2 and 3: the occurrence line leaves the Files column
    for the path), `.bl-path-occurrence`, holding nothing, and not
    displayed, where the path's last two parts name it (`crumbs`): the text
    of `recipe_head`, where it is not empty, `.bl-path-note` (K-D30); in a
    stage's view, where the recipe the shown stage was bound through holds
    the open file at several positions, a choice among them, the head left
    out, that makes the position chosen the head (`choose_position`); and
    where that recipe holds none, each recipe of the folder that holds the
    file, a link that binds the file through it with the stage's view kept
    (`bind_through`), after `held by` in `.bl-path-holders`."""
    # the shown stage is the open file's, in a stage's view
    own = (
        view_mode.value == "stage"
        and _is_stage(path)
        and current is not None
        and current.path == path
    )
    positions = current.positions if own else ()
    text = recipe_head(current, path)
    # the occurrence the path's last two parts name, where they name one,
    # stands in the path alone (the fix wave Q3b, item 19, C19)
    if text and text == occurrence_named(crumbs(current)):
        text = ""
    parts = []
    if text:
        parts.append(rv.Html(tag="span", class_="bl-path-note bl-code-small", children=[text]))
    if len(positions) > 1:
        labels = {
            f"periods[{h}] / {key}": (h, key) for h, key in positions if (h, key) != head.value
        }

        def choose(label):
            if label in labels:
                choose_position(labels[label])

        # The choice holds no value, since the line's text names the
        # occurrence the file is bound as: its first option, the count of
        # the positions, stands chosen, and a choice changes the head,
        # whose new key draws the select again with that option chosen.
        count = f"{len(positions)} positions"
        parts.append(
            RegionSelect((count, *labels), count, choose, "bl-recipe-positions", "").key(
                f"positions {head.value}"
            )
        )
    elif own and not positions:
        holders = [found for found, held in current.uses if held]
        if holders:
            children = ["held by "]
            for number, found in enumerate(holders):
                if number:
                    children.append(", ")
                children.append(HolderItem(found).key(found.path))
            parts.append(rv.Html(tag="span", class_="bl-path-holders", children=children))
    return rv.Html(tag="span", class_="bl-path-occurrence", children=parts)


@solara.component
def HolderItem(found: recipe.Source):
    """One recipe after the main bar's path that holds the open stage file,
    by its path from the folder, a button, so that Tab reaches it; a click
    binds the file through it, as its first occurrence there, the stage's
    view kept (`bind_through`)."""
    item = rv.Html(
        tag="button",
        class_="bl-recipe-holder bl-code-small",
        attributes={
            "type": "button",
            "data-path": found.path,
            "title": f"bind this file as its first occurrence in {found.path}",
        },
        children=[found.path],
    )
    rv.use_event(item, "click", lambda *_: bind_through(found))
    return item


@solara.component
def FolderRegion(dirty: set):
    """The folder column (design pass 8 §6): the handle on its right edge;
    its head, `.bl-folder-rail`, the one head of §5.5, 28 px, holding the
    word `Files` in Head and at its right end the folder's actions
    (`FolderActions`), and, drawn alone while the folder is folded, the
    folder's name with the open file's path reading upward (spec 0.4 §5.1;
    brief rule 3), the toggle that folds the folder, `Files`, standing at
    the main bar's right (`MainBar`; design pass 10 §3); then the tree, from
    the model's folder as its root row in Head (`.bl-tree-root`) down, in
    rows of 24 px, with the git marks and the controls of the files no file
    of the folder names or listed to delete on save
    (`creation.removable_files`, `deleting`; unit L, Task 25), which fills
    the column. The recipe stands in the panel under the editor
    (`RecipeRegion`; AAS, M-D17; design pass 9 §5), and the selected
    occurrence in the main bar's path (`PathOccurrence`; design pass 10
    §2)."""
    name = tab_folder.value.root.name
    with rv.Html(tag="section", class_="bl-folder"):
        Handle("folder")
        with rv.Html(tag="div", class_="bl-head bl-folder-rail"):
            rv.Html(tag="h2", children=["Files"])
            FolderActions()
            rv.Html(
                tag="span",
                class_="bl-rail-path bl-code-small",
                children=[
                    name + "/",
                    rv.Html(tag="span", class_="bl-rail-open", children=[open_path.value or ""]),
                ],
            )
        # the period files and stage folders no file of the folder names,
        # which the tree offers to delete, read again when the tree changes
        # or the buffer of a recipe, a trellis file or a period file does,
        # the files that name them (unit L, Task 25); a save checks each
        # deletion again from every file (`_delete_on_save`)
        naming = tuple(
            (path, held["text"])
            for path, held in buffers.value.items()
            if model._role(Path(path)) in ("recipe", "trellis", "period")
        )
        removable = solara.use_memo(
            lambda: creation.removable_files(
                tab_folder.value.root, trellis.texts_of(unsaved_texts())
            ),
            [tree.value, naming],
        )
        deleted = frozenset(path for path, _ in deleting.value)
        with rv.Html(tag="div", class_="bl-tree"):
            rv.Html(
                tag="div",
                class_="bl-row bl-tree-root",
                attributes={"title": str(tab_folder.value.root)},
                children=[name],
            )
            Tree(tree.value, open_path.value, dirty, open_folders.value, removable, deleted)


@solara.component_vue("field.vue")
def Field(
    kind: str = "text",
    value: str = "",
    options: list = [],
    descriptions: dict = {},
    above: bool = False,
    label: str = "",
    hover: str = "",
    classes: str = "",
    autofocus: bool = False,
    continuous: bool = True,
    disabled: bool = False,
    placeholder: str = "",
    named: str = "",
    submits: bool = False,
    grows: bool = False,
    answered: str = "",
    event_entered=None,
    event_submitted=None,
):
    """A field of a form, a select or the periods field of the Recipe tab, a
    select after the main bar's path or of the graph's bar, or Matsya's
    composer, a text area that submits on Enter and begins a line on
    Shift+Enter (amendment 07), drawn by VSCode Elements at 26 px, a text
    area at two lines, or, where `grows` holds, of one line growing to
    eight (design pass 8 §§4 and 5.3; amendment 07 §2 item 2); see
    field.vue."""


def RegionSelect(options, shown: str, choose, classes: str, hover: str):
    """A select after the main bar's path (AMD-MI-002 §3 rule 5; design pass 8
    §6), a select of VSCode Elements (`Field`) in the wrapper `classes`,
    which carries the hover `hover`: its options `options`, the option
    `shown` chosen; a choice of another option calls `choose` with it."""

    def chosen(text):
        if text != shown:
            choose(text)

    return Field(
        kind="select",
        value=shown,
        options=list(options),
        hover=hover,
        classes=classes,
        event_entered=chosen,
    )


def block_text(text: str, key: str, kind: str | None = None) -> str:
    """The text an entry prints in the row of the stage `key` of the Recipe
    tab (unit K's decision K-D30; design pass 9 §3): the entry `text` as
    written, less the stage's own folder `stages/<key>/` or, for an entry of
    the binding `kind`, the kind's folder `<kind>/` at its start, since the
    row's key and the column's head name them; `stages/tenure/methods`
    prints `methods` and `calibration/durables` prints `durables`. The text
    stands as written where neither folder stands at its start, or where
    nothing would remain."""
    for folder in (f"stages/{key}/", f"{kind}/" if kind else None):
        if folder and text.startswith(folder) and len(text) > len(folder):
            return text[len(folder) :]
    return text


# the labels of the buttons that remove a stage and a period from the model
# (unit L, Task 25; AAS, L-D18)
REMOVE_STAGE = "Remove stage"
REMOVE_PERIOD = "Remove period"


@solara.component
def RemoveStage(key: str):
    """The button on the stage's row of the Recipe tab that removes the
    stage `key` from the model (`remove_stage`; unit L, Task 25; AAS, L-D18
    and M-D2; design pass 10 §7, the trash is `Remove stage`), with the
    class `.bl-remove-stage` and data-stage: the icon button of VSCode
    Elements, the Codicon `trash`, named `Remove stage`, the one control of
    a row at rest (design pass 11 §2), its hover `Remove <key> from this
    recipe` (design pass 10 §4). Its click is stopped at the button, so
    that it removes the stage and does not open the row. Details of an
    occurrence draws its own two controls (`RemovalButtons`)."""
    # the Recipe tab's trash names the recipe it acts in (design pass 10 §4)
    return ToolbarButton(
        "remove",
        REMOVE_STAGE,
        f"Remove {key} from this recipe",
        lambda: remove_stage(key),
        "bl-remove-stage",
        {"data-stage": key},
        stop=True,
    )


def remove_from_periods_words(runs: str) -> str:
    """The label of the control of Details that takes a selected stage
    occurrence out of the list that writes its period (design pass 10 §7):
    `Remove from periods 0–5`, `runs` the periods that list writes."""
    return f"Remove from periods {runs}"


def remove_from_periods_hover(key: str, file: str, runs: str) -> str:
    """The hover of `Remove from periods` for the stage `key` whose list of
    stages the file `file` writes for the periods `runs` (design pass 10
    §7): `Takes port out of period.yml, which writes periods 0–5`."""
    return f"Takes {key} out of {file}, which writes periods {runs}"


def remove_stage_scope_hover(key: str, recipe_name: str) -> str:
    """The hover of `Remove stage` in Details of an occurrence of the stage
    `key` read under the recipe `recipe_name` (design pass 10 §7), naming
    the scope of the removal."""
    return (
        f"Removes {key} from {recipe_name} and every period; its files are deleted on save "
        "unless another recipe names them"
    )


@solara.component
def RemovalButtons(position: tuple):
    """The last row of Details of the stage occurrence `position`, `(h,
    key)`, after its rows, its other buttons and the fold `Legend`, under a
    hairline (unit N, Task 5; design pass 10 §7; design pass 13 §5, Q-D15;
    the fix wave Q3b, item 17, D24):
    `div.bl-removal-buttons`, holding two text buttons with the Codicon
    `trash` before their words (`TextButton`), a destructive act being a
    text button last in its panel, each naming its scope.
    `Remove from periods 0–5`, `.bl-remove-occurrence`, takes the key out
    of the list that writes those periods (`remove_occurrence`), and is
    drawn where the package answers that list (`trellis.occurrence_list`);
    `Remove stage`, `.bl-remove-stage`, removes the stage from the recipe
    and every period (`remove_stage`), and is drawn for a trellis read from
    a recipe. Each hover is the pass's sentence. The list is read once for
    each occurrence and trellis held."""
    held = trellis_shown.value
    h, key = position
    scope = solara.use_memo(
        lambda: trellis.occurrence_list(held, position, trellis.texts_of(unsaved_texts()))
        if held is not None
        else None,
        [held, position],
    )
    with rv.Html(tag="div", class_="bl-removal-buttons"):
        if scope is not None:
            file, runs = scope
            TextButton(
                remove_from_periods_words(runs),
                lambda: remove_occurrence(position),
                "bl-remove-occurrence",
                remove_from_periods_hover(key, file, runs),
                icon="remove",
            ).key("occurrence")
        if held is not None and held.source.kind == "recipe":
            TextButton(
                REMOVE_STAGE,
                lambda: remove_stage(key),
                "bl-remove-stage",
                remove_stage_scope_hover(key, Path(held.source.path).name),
                icon="remove",
            ).key("stage")


# --- the Recipe tab of the panel under the editor (AAS, M-D3 and M-D17;
# design pass 9) ---

# The texts of the Recipe tab, each a label of a word or a few (design pass
# 9 §3): the view tab's name; the column heads, one per binding kind of a
# stage's block in the recipe, each with its hover (design pass 10 §4); the
# key of the trellis row as the recipe writes it; the periods field's
# placeholder, the periods the package reads where the recipe writes none;
# the add row's button, its accessible name and its hover; the label that
# stands before a reading answers; and the mark of a kind the recipe writes
# no list for, with its hover.
RECIPE_TAB = "Recipe"
RECIPE_HEADS = ("Stage", "Calibration", "Settings", "Methods", "Periods")
RECIPE_HEAD_HOVERS = (
    "The stage's file",
    "Parameter values",
    "Numerical choices",
    "Numerical routines for the stage's operations",
    "The periods the stage stands in",
)
TRELLIS_KEY = "trellis"
PERIODS_PLACEHOLDER = "All"
ADD_STAGE = "Stage"
ADD_STAGE_NAME = "Add stage"
ADD_STAGE_HOVER = "Add a stage from a template"
NOT_READ = "Not read"
NONE_WRITTEN = "—"
NONE_WRITTEN_HOVER = "The recipe writes none"
# the files a select of the Recipe tab offers, by the column's kind: each
# binding kind's sources, the stage files and the trellis files
CHOSEN_KINDS = (*recipe.KINDS, "stage", TRELLIS_KEY)
# a range list's key, `1-6`, which the tab prints with the page's dash
_RANGE_LIST = re.compile(r"(\d+)-(\d+)")


def shows_recipe(path: str | None) -> bool:
    """Whether the open file `path` is the recipe the trellis is read under,
    the tab's source, for which the panel under the editor stands on its
    Recipe tab (AAS, M-D3; design pass 9 §2); a recipe the trellis is not
    read under has no panel until a click in the tree shows its trellis."""
    chosen = source.value
    return (
        path is not None and chosen is not None and chosen.kind == "recipe" and chosen.path == path
    )


def inspector_content(path: str | None) -> str | None:
    """What the Inspector, the panel under the editor, shows for the open
    file `path` (design pass 10 §4; design pass 9 §2), by the data-panel of
    the region that draws it: `types`, the four tabs of a stage file;
    `recipe`, the Recipe tab of the recipe the trellis is read under; None
    for any other file, for which the panel does not appear."""
    if _is_stage(path):
        return "types"
    return "recipe" if shows_recipe(path) else None


def lower_panel(path: str | None) -> str | None:
    """The fold of the panel under the editor for the open file `path`
    (design pass 10 §§3 and 4; N-D4): `inspector` where the panel shows the
    file (`inspector_content`), None where it does not appear. window.vue
    draws the Inspector toggle open only while it is not None, and the
    toggle is disabled while it is None (`inspector_hover`)."""
    return "inspector" if inspector_content(path) is not None else None


def _printed(text: str, key: str, kind: str) -> str:
    """The text a select of the Recipe tab shows for the name `text` the
    recipe writes in the column `kind` of the stage `key` (`block_text`):
    the trellis file as written, a stage file less the stage's own folder,
    a source less its kind's folder or the stage's own folder."""
    if kind == TRELLIS_KEY:
        return text
    return block_text(text, key, kind if kind in recipe.KINDS else None)


def _probe_entry(chosen: recipe.Source, key: str, kind: str) -> recipe.Entry:
    """An entry of the recipe `chosen` in the column `kind` of the stage
    `key`, at the address such an entry has, by which `recipe.written_name`
    names a file there."""
    if kind == TRELLIS_KEY:
        address = TRELLIS_KEY
    elif kind == "stage":
        address = f"stages.{key}.stage"
    else:
        address = f"stages.{key}.{kind}.all[0]"
    return recipe.Entry("", False, chosen.path, address, None)


def offered_entries(folder, chosen: recipe.Source, files: dict, slots: dict, key: str, kind: str):
    """The options of a select of the Recipe tab in the column `kind` of the
    stage `key` (design pass 9 §3), a mapping from the text each option
    prints to what a choice of it writes (`choose_file`): each file of the
    folder an entry there may name (`files[kind]`, `recipe.choices`), its
    text the name the recipe writes for it (`recipe.written_name`) as the
    table prints it (`_printed`), mapped to its path from the folder; then
    each slot the recipe writes in that kind (`slots[kind]`), as written,
    mapped to itself. A file that cannot be read is offered as well, since
    a choice writes its name and the package's reading refuses it."""
    probe = _probe_entry(chosen, key, kind)
    offered = {}
    for choice in files.get(kind, ()):
        named = recipe.written_name(folder, chosen, probe, choice.path)
        offered.setdefault(_printed(named, key, kind), choice.path)
    for slot in slots.get(kind, ()):
        offered.setdefault(slot, slot)
    return offered


def recipe_slots(rows) -> dict:
    """The slots the recipe's rows `rows` write, by binding kind, each once
    in the order in which the recipe first writes it, `{"calibration":
    ["$fill"], …}`: the slots a select of that kind offers (K-D29; design
    pass 9 §3)."""
    found = {kind: [] for kind in recipe.KINDS}
    for row in rows:
        for kind in recipe.KINDS:
            for entries in row.cells[kind].lists.values():
                for entry in entries:
                    if entry.slot and entry.text not in found[kind]:
                        found[kind].append(entry.text)
    return found


def _marked(entry, control: str) -> bool:
    """Whether the refusal of a change of the Recipe tab that stands
    (`choice_refusal`) names the control `control` of `entry`."""
    refused = choice_refusal.value
    return (
        refused is not None
        and refused["address"] == entry.address
        and refused["control"] == control
    )


def _answered_at(marked: bool) -> str:
    """The `answered` of a field of the Recipe tab (field.vue): the moment
    of the last reading of the trellis (`trellis_outcome`) and, where
    `marked`, of the refusal of the field's change (`choice_refusal`). At
    each new one the field drops the texts it sent and Python has not
    answered and shows the value the table read, so that a choice refused,
    or taken back before its own reading answered, is not left shown; the
    element is kept, so that an open list stays open and a text being typed
    stays (unit M, Task 10, fix round 1)."""
    outcome = trellis_outcome.value
    refused = choice_refusal.value
    read = outcome.made if outcome is not None else 0.0
    refusal = refused["made"] if marked and refused is not None else 0.0
    return f"{read} {refusal}"


@solara.component
def RecipeEntry(entry, key: str, kind: str, offered: dict, new_file: bool = False):
    """One entry of the Recipe tab (design pass 9 §3), `.bl-recipe-entry`
    with data-address, the entry's address in the recipe, one line of 26
    px, drawn in the trellis row and in the open row (design pass 11 §2):
    a select of VSCode Elements (`Field`) in Code small, with its chevron,
    showing the entry as the table prints it (`_printed`)
    among the options `offered` (`offered_entries`), the entry first where
    it is none of them, its accessible name `Replace <text>` and its hover
    `Replace <name as written>`, which prints a value cut by the column
    whole; a choice of another option replaces the entry by it in the
    recipe's buffer (`choose_file`). It carries the refusal's mark while a
    choice of it stands refused (`choice_refusal`; AMD-MI-002 §6a rule 1).
    The field is answered at each reading of the trellis and at the refusal
    of a choice of it (`_answered_at`), so that it shows the entry the
    table read where a change was refused or taken back before its own
    reading answered. Where `new_file`, the icon button `New file`
    (`NewFileButton`) stands at the select's right; no word stands under
    the select (design pass 10 §4; N-D5)."""
    shown = _printed(entry.text, key, kind)
    options = list(offered) if shown in offered else [shown, *offered]

    def chosen(text):
        target = offered.get(text)
        if text != shown and target is not None:
            choose_file(entry, target)

    marked = _marked(entry, SELECT)
    mark = " bl-refusal-mark" if marked else ""
    select = Field(
        kind="select",
        value=shown,
        options=options,
        hover=f"Replace {entry.text}",
        named=f"Replace {shown}",
        classes="bl-code-small" + mark,
        answered=_answered_at(marked),
        event_entered=chosen,
    )
    children = [select, NewFileButton(entry, key, kind)] if new_file else [select]
    return rv.Html(
        tag="span",
        class_="bl-recipe-entry",
        attributes={"data-address": entry.address},
        children=children,
    )


@solara.component
def NewFileButton(entry, key: str, kind: str):
    """The icon button `New file` at the right of the select of a slot of
    the Recipe tab whose own file does not exist at its conventional place
    (unit K's decision K-D7; design pass 10 §4; N-D5), the Codicon
    `new-file` (`ToolbarButton`), `.bl-new-file` with data-address, its
    hover `Write <file>`, drawn in the open row alone (design pass 11 §2);
    a click writes that file and its name in the slot's place
    (`new_file_for`). It takes the refusal's color while that change stands
    refused."""
    own = creation.source_path(key, kind)
    mark = " bl-refusal-mark" if _marked(entry, NEW_FILE) else ""
    return ToolbarButton(
        "new file",
        NEW_FILE.capitalize(),
        f"Write {own}",
        lambda: new_file_for(entry, key, kind),
        "bl-new-file" + mark,
        {"data-address": entry.address},
    )


@solara.component
def PeriodsField(key: str, shown, listed: str | None):
    """The periods field of the stage `key`'s row of the Recipe tab (design
    pass 9 §3), drawn while the row is open (design pass 11 §2),
    `.bl-recipe-periods`, a text field of VSCode Elements in
    Code small holding the stage's own periods as `lo–hi`, `shown` the
    recipe's `periods` entry, empty with the placeholder `All` where the
    recipe writes none; its hover names the periods the trellis lists the
    stage in, `listed`. The text typed is written at Enter or when the field
    is left (`choose_periods`); it carries the refusal's mark while that
    change stands refused. It is answered at each reading of the trellis
    and at the refusal of its change, as an entry's select is
    (`_answered_at`)."""
    address = shown.address if shown is not None else f"stages.{key}.periods"
    probe = shown or recipe.Entry("", False, "", address, None)
    marked = _marked(probe, PERIODS)
    mark = " bl-refusal-mark" if marked else ""
    return Field(
        kind="text",
        value=shown.text if shown is not None else "",
        placeholder=PERIODS_PLACEHOLDER,
        named=f"Periods of {key}",
        hover=f"Listed in periods {listed}" if listed else "",
        classes="bl-recipe-periods bl-code-small" + mark,
        continuous=False,
        answered=_answered_at(marked),
        event_entered=lambda typed: choose_periods(key, typed, shown),
    )


def _range_word(name: str) -> str:
    """The periods of a range list of the recipe, `1-6`, as the Recipe tab
    prints them, `1–6`; any other key as written."""
    found = _RANGE_LIST.fullmatch(name)
    return name if found is None else f"{found[1]}–{found[2]}"


def _range_periods(name: str):
    """The periods of the range list `name`, `.bl-recipe-range` in Code
    small in ink-3, which stands at the left of the list's first select on
    its line (design pass 10 §4)."""
    return rv.Html(
        tag="span", class_="bl-recipe-range bl-code-small", children=[_range_word(name)]
    )


def _none_written():
    """The mark of a column the recipe writes nothing for, `—` in Code small
    in ink-3, `.bl-recipe-none`, with its hover."""
    return rv.Html(
        tag="span",
        class_="bl-recipe-none bl-code-small",
        attributes={"title": NONE_WRITTEN_HOVER},
        children=[NONE_WRITTEN],
    )


def _rest_text(text: str, hover: str | None, classes: str = ""):
    """A value of a row of the Recipe tab at rest (design pass 11 §2),
    `.bl-recipe-text` in Code small in ink-1, cut with an ellipsis where its
    column is narrower, its hover `hover` where one is given; `classes`
    adds `bl-recipe-slot` for a slot or `bl-recipe-placeholder` for the
    periods' `All`, each drawn in ink-3."""
    return rv.Html(
        tag="span",
        class_=f"bl-recipe-text bl-code-small {classes}".strip(),
        attributes={"title": hover} if hover else {},
        children=[text],
    )


def _entry_text(entry, key: str, kind: str):
    """The entry `entry` of the column `kind` in the row of the stage `key`
    at rest (design pass 11 §2): its text as the table prints it
    (`_printed`), whole in its hover, a slot `.bl-recipe-slot`."""
    shown = _printed(entry.text, key, kind)
    return _rest_text(shown, shown, "bl-recipe-slot" if entry.slot else "")


def _periods_text(shown, listed: str | None):
    """The periods cell of a row at rest (design pass 11 §2): the stage's
    own periods the recipe writes, `shown`, as `lo–hi`, or `All`
    (`PERIODS_PLACEHOLDER`) in ink-3 where it writes none; its hover, as
    the periods field's, the periods the trellis lists the stage in,
    `listed`."""
    hover = f"Listed in periods {listed}" if listed else None
    if shown is None:
        return _rest_text(PERIODS_PLACEHOLDER, hover, "bl-recipe-placeholder")
    return _rest_text(shown.text, hover)


@solara.component
def RecipeRow(row, offered: dict, listed: str | None, opened: bool = False):
    """One row of the Recipe tab, a stage of the recipe (design pass 9 §3;
    design pass 10 §4; design pass 11 §2), `.bl-recipe-row` with
    data-stage, role row, tabindex 0 and aria-expanded whether it is open,
    one `.bl-recipe-cell` per column (data-kind), each a column of
    `.bl-recipe-line` rows, then the icon button `Remove stage`
    (`RemoveStage`), the row's one control, in the table's last column
    (design pass 13 §4; D2). At rest the row is text, each line 16 px
    with no gap between the lines of a cell (Q-D21): the stage's cell its
    key in Code name, `.bl-recipe-key-line`, its hover the stage file's
    path, then, only where the file's name is not `<key>.bl`, the name
    (`.bl-recipe-text`), or `—` where the recipe writes no stage file (C10);
    each kind's cell one line per entry of the kind's lists, in the file's
    order, the entry as the table prints it, a slot `.bl-recipe-slot`, the
    first entry of a range list after the list's periods `.bl-recipe-range`
    on the same line, and `—` where the recipe writes no list; the periods
    cell the periods the recipe writes, or `All`. Open (`opened`), the row
    is `.bl-recipe-open` and draws its lines at 26 px with their
    controls, the stage's key and its file's select on one line: each
    entry a select (`RecipeEntry`), a slot whose own file is
    missing with its icon button `New file`, and the periods field
    (`PeriodsField`). A click on the row anywhere but on its trash, or
    Enter or Space while the row has the focus, opens it
    (`open_recipe_row`); window.vue closes it. `offered` maps each column's
    kind to its options (`offered_entries`)."""
    root = tab_folder.value.root

    def line(children, classes=""):
        return rv.Html(tag="div", class_=f"bl-recipe-line {classes}".strip(), children=children)

    def value(entry, kind: str):
        # the entry's select in the open row, else its text
        if not opened:
            return _entry_text(entry, row.key, kind)
        own = root / creation.source_path(row.key, kind)
        new_file = entry.slot and not own.exists()
        return RecipeEntry(entry, row.key, kind, offered[kind], new_file)

    attributes = {
        "data-stage": row.key,
        "role": "row",
        "tabindex": "0",
        "aria-expanded": "true" if opened else "false",
    }
    classes = "bl-recipe-row bl-recipe-open" if opened else "bl-recipe-row"
    with rv.Html(tag="div", class_=classes, attributes=attributes) as element:
        with rv.Html(
            tag="div", class_="bl-recipe-cell", attributes={"data-kind": "stage", "role": "cell"}
        ):
            # the key's hover is the stage file's path as the recipe writes
            # it, which the row at rest prints only where it differs from
            # `<key>.bl` (design pass 13 §§3 and 4; C10)
            key = rv.Html(
                tag="span",
                class_="bl-recipe-key bl-code-name",
                attributes={"title": row.stage.text if row.stage is not None else row.key},
                children=[row.key],
            )
            if opened:
                stage_file = (
                    value(row.stage, "stage") if row.stage is not None else _none_written()
                )
                line([key, stage_file], "bl-recipe-key-line")
            else:
                line([key], "bl-recipe-key-line")
                if row.stage is None:
                    line([_none_written()])
                elif _printed(row.stage.text, row.key, "stage") != f"{row.key}.bl":
                    line([_entry_text(row.stage, row.key, "stage")])
        for kind in recipe.KINDS:
            lists = row.cells[kind].lists
            with rv.Html(
                tag="div", class_="bl-recipe-cell", attributes={"data-kind": kind, "role": "cell"}
            ):
                if not lists:
                    line([_none_written()])
                for name, entries in lists.items():
                    if name != "all" and not entries:
                        line([_range_periods(name)]).key(f"range {name}")
                    for at, entry in enumerate(entries):
                        drawn = [value(entry, kind)]
                        if name != "all" and at == 0:
                            drawn.insert(0, _range_periods(name))
                        line(drawn).key(entry.address)
        with rv.Html(
            tag="div", class_="bl-recipe-cell", attributes={"data-kind": "periods", "role": "cell"}
        ):
            periods = (
                PeriodsField(row.key, row.periods, listed)
                if opened
                else _periods_text(row.periods, listed)
            )
            line([periods])
        # the row's one act, its trash, in the table's last column of 24 px
        # (design pass 13 §4; D2)
        RemoveStage(row.key)
    # The trash's own click stops at the trash (`RemoveStage`), and a key
    # pressed in a control of the open row is the control's. ipyvue binds
    # one handler for each event name on an element, so Enter is read when
    # the key is released and Space when it is pressed, Space's scroll of
    # the table prevented.
    rv.use_event(element, "click", lambda *_: open_recipe_row(row.key))
    rv.use_event(element, "keyup.enter.self", lambda *_: open_recipe_row(row.key))
    rv.use_event(element, "keydown.space.self.prevent", lambda *_: open_recipe_row(row.key))
    return element


@solara.component
def RecipeTabs():
    """The view tab of the panel under the editor on the recipe (design
    pass 9 §2), VSCode Elements' tabs, `.bl-class-tabs`, with the one header
    `Recipe`, `.bl-class-tab` with data-tab, selected; it is the tab shown,
    so a click on it changes nothing."""
    header = ViewTab(
        RECIPE_TAB,
        "bl-class-tab bl-active",
        {"data-tab": RECIPE_TAB, "title": "The recipe's bindings"},
        lambda: None,
        False,
    )
    return rv.Html(
        tag="vscode-tabs",
        class_="bl-class-tabs",
        attributes={"selected-index": "0"},
        children=[header],
    )


def InspectorStrip(tabs, path: str, panel: str):
    """The strip of the panel under the editor, its only head (unit N, Task
    2; design pass 10 §4; N-D4), `div.bl-inspector-strip`, 28 px: the view
    tabs `tabs` at its left; the open file's name, `.bl-inspector-file` in
    Code small in ink-2, the strip's context, as Details' context (design
    pass 13 §5; the fix wave Q3b, item 20, N2), at its right, the file's
    path `path` as its hover;
    then the icon button `open wide` of the panel `panel` (`WideButton`;
    AAS, L-D12; N-I31). It holds no name of the panel and no close button,
    since the rail's button folds the panel."""
    name = rv.Html(
        tag="span",
        class_="bl-inspector-file bl-code-small",
        attributes={"title": path},
        children=[Path(path).name],
    )
    return rv.Html(
        tag="div", class_="bl-inspector-strip", children=[tabs, name, WideButton(panel)]
    )


@solara.component
def RecipeTable(rows, written, offered_by: dict, trellis_offered: dict, listed: dict, opened=None):
    """The table of the Recipe tab (AAS, M-D17; design pass 9 §3),
    `.bl-recipe-table`, role table: the trellis row,
    `.bl-recipe-trellis-row`, the key `trellis` and the trellis file's
    select (`RecipeEntry`; `—` where the recipe writes none); the column
    heads, `.bl-recipe-heads`, in Label, each with its hover
    (`RECIPE_HEAD_HOVERS`; design pass 10 §4); one row per stage
    (`RecipeRow`), the row of the stage `opened` open and every other at
    rest (design pass 11 §2). The add row stands after the table
    (`RecipeRegion`). `offered_by` maps a stage's
    key to its columns' options and `trellis_offered` holds the trellis
    row's (`offered_entries`); `listed` maps a stage's key to the periods
    the trellis lists it in."""
    with rv.Html(
        tag="div", class_="bl-recipe-table", attributes={"role": "table", "aria-label": "recipe"}
    ):
        trellis_file = (
            RecipeEntry(written, "", TRELLIS_KEY, trellis_offered)
            if written is not None
            else _none_written()
        )
        rv.Html(
            tag="div",
            class_="bl-recipe-trellis-row",
            attributes={"role": "row"},
            children=[
                rv.Html(tag="span", class_="bl-recipe-key bl-code-name", children=[TRELLIS_KEY]),
                rv.Html(tag="div", class_="bl-recipe-line", children=[trellis_file]),
            ],
        )
        rv.Html(
            tag="div",
            class_="bl-recipe-heads",
            attributes={"role": "row"},
            children=[
                rv.Html(
                    tag="span",
                    attributes={"role": "columnheader", "title": hover},
                    children=[word],
                )
                for word, hover in zip(RECIPE_HEADS, RECIPE_HEAD_HOVERS)
            ],
        )
        for row in rows:
            RecipeRow(row, offered_by[row.key], listed.get(row.key), row.key == opened).key(
                row.key
            )


@solara.component
def RecipeAddRow():
    """The add row of the Recipe tab, `.bl-recipe-add` (design pass 9 §3;
    design pass 10 §7): the text button `Stage` with the Codicon `add`,
    named `Add stage`, which opens the stage list beside it
    (`add_stage_from_recipe`), aria-expanded and drawn pressed while the
    list is open, and then the list (`StageChooser`). A component of its
    own, keyed in the panel under the table, at the panel's foot (design
    pass 13 §4; D15), so that the button keeps the widget that holds its
    click when a stage's row leaves or returns above it (unit N, Task 5)."""
    opened = recipe_chooser.value
    add = rv.Html(
        tag="button",
        class_="bl-text-button bl-recipe-add-stage",
        attributes={
            "type": "button",
            "title": ADD_STAGE_HOVER,
            "aria-label": ADD_STAGE_NAME,
            "aria-expanded": "true" if opened else "false",
        },
        children=[icons.codicon(icons.CODICONS["add"]), ADD_STAGE],
    )
    rv.use_event(add, "click", lambda *_: add_stage_from_recipe())
    return rv.Html(
        tag="div",
        class_="bl-recipe-add",
        children=[add, StageChooser()] if opened else [add],
    )


# the Codicon of each kind of item of the stage list, by the item's kind, as
# the graph's list draws them (flow-canvas.js, KIND_ICONS; design pass 8 §3)
STAGE_KIND_ICONS = {
    "stage": "symbol-structure",
    "template": "layers",
    "library": "library",
    "folder": "folder",
}
# the name of the stage list in its head, and the hover and spoken name of
# its control `×`, as the graph's list writes them (K-D24)
STAGE_LIST_NAME = "Stages"
STAGE_LIST_CLOSE = "close"
# the word an item of the stage list prints where the period's list holds it
# (unit K's decision K-D14)
LISTED = "listed"


def stage_item_hover(item: dict) -> str | None:
    """The hover of an item of the stage list (AAS, L-D9): its model's title
    and, after ` · `, the parameters its calibration gives, as the graph's
    list writes it (flow-canvas.js, `itemHover`); None where it has
    neither."""
    parts = [part for part in (item["title"], ", ".join(item["calibration"])) if part]
    return " · ".join(parts) if parts else None


@solara.component
def StageChooser():
    """The stage list of the Recipe tab's button `Stage` (unit N, Task 5;
    design pass 10 §7), the list a period's `+ stage` opens over the graph,
    as a popover beside the button: `div.bf-stage-list.bl-stage-chooser`,
    whose top-left stands at the button's bottom-left and which brand.css
    flips above the button where it would pass the panel's bottom edge and
    shifts left where it would pass its right edge. Its head, the Codicon
    `symbol-structure`, `Stages` and the control `×`; where the recipe's
    trellis names more than one period file (`creation.period_files`), the
    select `Period file`, `.bl-chooser-period-file`, whose list the item
    joins; then the items `trellis.stage_items` answers, each section's
    heading line before its first item, each item a button of one line,
    the Codicon of its kind, its key and its model's folder, its hover
    `stage_item_hover`, dimmed with `listed` where that list holds it, and
    marked chosen, `aria-current`, where it is the item last chosen. A
    click on an item, or Enter on it, adds it there (`choose_from_recipe`);
    Escape anywhere in the list, or `×`, closes it. The items are read once
    for each trellis held."""
    folder, held = tab_folder.value, trellis_shown.value
    texts = trellis.texts_of(unsaved_texts())
    items = solara.use_memo(
        lambda: trellis.stage_items(folder, held, texts)["items"] if held is not None else [],
        [folder, held],
    )
    files = solara.use_memo(
        lambda: creation.period_files(folder.root, _form_recipe(), texts), [folder, held]
    )
    chosen = recipe_chooser_file.value
    period_file = chosen if chosen in files else (files[0] if files else creation.PERIOD)
    h = solara.use_memo(
        lambda: trellis.list_period(held, folder.root, period_file, "", texts)
        if held is not None
        else None,
        [held, period_file],
    )
    close = rv.Html(
        tag="button",
        class_="bf-list-close",
        attributes={"type": "button", "title": STAGE_LIST_CLOSE, "aria-label": STAGE_LIST_CLOSE},
        children=[icons.codicon(icons.CODICONS["close"])],
    )
    rv.use_event(close, "click", lambda *_: close_recipe_chooser())
    parts = [
        rv.Html(
            tag="div",
            class_="bf-list-head",
            children=[
                icons.codicon(STAGE_KIND_ICONS["stage"]),
                rv.Html(
                    tag="span",
                    class_="bf-list-name",
                    attributes={"role": "heading", "aria-level": "2"},
                    children=[STAGE_LIST_NAME],
                ),
                close,
            ],
        )
    ]
    if len(files) > 1:
        parts.append(
            Field(
                kind="select",
                value=period_file,
                options=list(files),
                label="Period file",
                classes="bl-chooser-period-file",
                event_entered=recipe_chooser_file.set,
            )
        )
    section = None
    for item in items:
        if item["section"] and item["section"] != section:
            parts.append(
                rv.Html(
                    tag="div",
                    class_="bf-stage-section",
                    attributes={"role": "heading", "aria-level": "3"},
                    children=[item["section"]],
                )
            )
        section = item["section"]
        listed = h is not None and h in item["periods_listed"]
        parts.append(StageChoice(item, listed, period_file).key(f"{item['kind']} {item['id']}"))
    chooser = rv.Html(
        tag="div",
        class_="bf-stage-list bl-stage-chooser",
        attributes={"role": "group", "aria-label": "stages"},
        children=parts,
    )
    rv.use_event(chooser, "keydown.esc", lambda *_: close_recipe_chooser())
    return chooser


@solara.component
def StageChoice(item: dict, listed: bool, period_file: str):
    """One item of the Recipe tab's stage list (`StageChooser`), a button
    `.bf-stage-item` of one line with data-item and data-kind: the Codicon
    of its kind, its key in `.bf-stage-key` and its model's folder in
    `.bf-stage-model`, the item `From a folder…` its words alone; dimmed
    with the word `listed` and acting not at all where the period file's
    list holds it (`listed`); marked chosen where it is the item last
    chosen; a click, or Enter, adds it to that list
    (`choose_from_recipe`)."""
    folder_item = item["kind"] == "folder"
    marked = recipe_chosen_item.value == item["id"]
    children = [
        rv.Html(
            tag="span",
            class_="bf-stage-key",
            children=[icons.codicon(STAGE_KIND_ICONS[item["kind"]]), item["key"]],
        )
    ]
    if item["model_folder"]:
        children.append(
            rv.Html(tag="span", class_="bf-stage-model", children=[item["model_folder"]])
        )
    if listed:
        children.append(rv.Html(tag="span", class_="bf-stage-listed", children=[LISTED]))
    hover = stage_item_hover(item)
    attributes = {
        "type": "button",
        "data-item": item["id"],
        "data-kind": item["kind"],
        **({"aria-current": "true"} if marked else {}),
        **({"title": hover} if hover else {}),
        **({"aria-disabled": "true"} if listed else {}),
    }
    classes = ["bf-stage-item"]
    if listed:
        classes.append("bf-listed")
    if folder_item:
        classes.append("bf-stage-folder")
    if marked:
        classes.append("bf-chosen")
    button = rv.Html(
        tag="button", class_=" ".join(classes), attributes=attributes, children=children
    )
    rv.use_event(
        button, "click", lambda *_: None if listed else choose_from_recipe(item, period_file)
    )
    return button


@solara.component
def RecipeRegion():
    """The panel under the editor on its Recipe tab (AAS, M-D3 and M-D17;
    design pass 9 §§2 and 3), drawn while the open file is the recipe the
    trellis is read under (`shows_recipe`): `.bl-classification` with
    data-panel `recipe`, the panel's one height (the handle
    `classification`), `.bl-wide` while it stands in its wide panel; its
    strip (`InspectorStrip`; design pass 10 §4), the view tab `Recipe`
    (`RecipeTabs`), the recipe's name and `Open wide`, with no head above
    it, the main bar's `Inspector` folding the panel; then the table
    (`RecipeTable`) and under it the add row (`RecipeAddRow`), or `Not
    read` before a reading of the trellis answers. The table reads the
    recipe as
    the reading of the trellis shown read it, the text of each unsaved
    buffer that reading took in its file's place (`TrellisShown.texts`)
    and every other file from disk (spec 0.4 §3.1; AAS, M-D7), so that a
    change of the recipe's buffer reaches the table with the trellis it
    reads, before any save, and a buffer whose reading is refused leaves
    the table of the last reading that answered, the refusal standing in
    the list under the error mark; it is read again after every reading,
    refused or not (`trellis_outcome`), so that it follows the files on
    disk. The table shows every list of the recipe as written and marks no
    period, so it is read at the terminal period. One row at most is open,
    the row of `recipe_open_stage` (design pass 11 §2), which is forgotten
    once a reading gives a table with no row of its key."""
    folder, chosen = tab_folder.value, source.value
    held, outcome = trellis_shown.value, trellis_outcome.value
    rows = solara.use_memo(
        lambda: recipe.table(folder, chosen, held.syntactic, 0, held.texts)
        if held is not None and chosen is not None
        else [],
        [folder, held, chosen, outcome],
    )
    opened = recipe_open_stage.value
    keys = tuple(row.key for row in rows)

    def forget():
        if recipe_open_stage.value not in (None, *keys):
            recipe_open_stage.value = None

    solara.use_effect(forget, [keys])
    written = solara.use_memo(
        lambda: recipe.trellis_entry(folder, chosen, held.texts)
        if held is not None and chosen is not None
        else None,
        [folder, held, chosen, outcome],
    )
    listed = solara.use_memo(
        lambda: trellis.listed_periods(held) if held is not None else {}, [held]
    )
    files = solara.use_memo(
        lambda: {kind: recipe.choices(folder, kind) for kind in CHOSEN_KINDS}, [folder, tree.value]
    )
    slots = recipe_slots(rows)
    offered_by = {
        row.key: {
            kind: offered_entries(folder, chosen, files, slots, row.key, kind)
            for kind in ("stage", *recipe.KINDS)
        }
        for row in rows
    }
    trellis_offered = (
        {} if chosen is None else offered_entries(folder, chosen, files, slots, "", TRELLIS_KEY)
    )
    wide = region_wide.value == "recipe"
    with rv.Html(
        tag="section",
        class_="bl-classification" + (" bl-wide" if wide else ""),
        attributes={"aria-label": "recipe", "data-panel": "recipe"},
    ):
        InspectorStrip(RecipeTabs(), chosen.path if chosen is not None else "", "recipe")
        if held is None or chosen is None:
            rv.Html(tag="p", class_="bl-class-empty", children=[NOT_READ])
        else:
            RecipeTable(rows, written, offered_by, trellis_offered, listed, opened)
            # the add row at the panel's foot, under the table, whose rows
            # scroll between their heads and it (design pass 13 §4; D15)
            RecipeAddRow().key("add")



# The toggles of the tab row (design pass 10 §4), each a word and its
# hover: `Types`, pressed while the editor shows the bracketed entries, the
# types (spec 0.4 §5.4), and `Notes`, pressed while it shows the notes.
TYPES_TOGGLE = ("Types", "Show or hide the bracketed entries")
NOTES_TOGGLE = ("Notes", "Show or hide the notes")


@solara.component
def FileRegion(result: Outcome | None, held: dict | None, dirty: set):
    """The file: the handle on its right edge, between the two panes, the
    tabs' row and the editor, with the refusals of the last outcome as its
    diagnostics, and the refusal of the trellis's reading where it stands
    at a line of the open file (`trellis_diagnostics`; spec 0.4 §3.1); a
    folder with no stage file reads `No stage file.` The column opens with
    its tabs' row, under the main bar, no head above it (design pass 10
    §§2 and 4). The tabs' row (spec 0.4 §5.1; brief rule 4), a bar of 36
    px, holds the tabs (`Tabs`), whose marks `unsaved` read `dirty`, then
    at its right end the toggles `Types` and `Notes`, text buttons with
    aria-pressed whether the editor shows what they name (`TYPES_TOGGLE`,
    `NOTES_TOGGLE`): `Types` shows or hides the types in the editor (§5.4,
    `toggle_types`) and does not fold the panel under the editor, whose fold
    is the main bar's Inspector toggle; `Notes` draws every note as written
    or each behind its glyph (`toggle_notes`, the editor's property
    `show_notes`; design pass 10 §9), not pressed at first; and `Save`,
    the column's one primary button of VSCode Elements (`CommandButton`),
    its right edge on the column's text edge. Over a stage file, the
    BellmanType panel stands under the
    editor, with its handle on its top edge; over the recipe the trellis is
    read under, the same panel on its Recipe tab (`RecipeRegion`; AAS,
    M-D17; design pass 9 §2). The panel is given the parse
    of the buffer's text, editable while the text parses and a stage of
    the file is shown; while the text does not parse, it is given the last
    parse of the file the region holds, locked, and the refusals of the
    last outcome stand on the rows they name (unit R, R-D57; amendment 02
    rulings 7 to 10)."""
    path = open_path.value
    diagnostics = result.diagnostics if result is not None and result.path == path else []
    diagnostics = [*diagnostics, *trellis_diagnostics(path)]
    text = held["text"] if held is not None and _is_stage(path) else None
    parsed = solara.use_memo(
        lambda: None if text is None else parse_text(path, text), [path, text]
    )
    # the last parse of a text that parsed, with its file's path
    last_parsed = solara.use_ref(None)
    if parsed is not None and parsed.spans is not None:
        last_parsed.current = (path, parsed)
    with rv.Html(tag="section", class_="bl-file"):
        Handle("file")
        # the tabs stand in an element of their own, so that the buttons
        # are not re-created when a tab or its mark `unsaved` appears
        with rv.Html(tag="div", class_="bl-tab-row"):
            Tabs(dirty)
            with rv.Html(tag="span", class_="bl-tab-actions"):
                words, hover = TYPES_TOGGLE
                TextButton(
                    words,
                    toggle_types,
                    "bl-types-button",
                    hover,
                    {"aria-pressed": "false" if hide_types.value else "true"},
                )
                # pressed while the editor draws every note as written, its
                # property `show_notes` (design pass 10 §§4 and 9)
                words, hover = NOTES_TOGGLE
                TextButton(
                    words,
                    toggle_notes,
                    "bl-notes-button",
                    hover,
                    {"aria-pressed": "true" if show_notes.value else "false"},
                )
                CommandButton(
                    "Save",
                    request_save,
                    "bl-save bl-primary",
                    "Write the editor's text to the file (Ctrl+S)",
                    waits="Open a file" if path is None else None,
                )
        # the choice has a slot of its own above the editor, so that the
        # editor keeps its place, and its unsaved text, when the choice
        # opens or closes (reacton reconciles children by position)
        with rv.Html(tag="div", class_="bl-choice-slot"):
            if conflict.value is not None:
                Choice(conflict.value)
        with rv.Html(tag="div", class_="bl-editor-frame"):
            if held is None and first_stage(tree.value) is None and folder_read.value:
                rv.Html(
                    tag="p",
                    class_="bl-no-stage",
                    children=["No stage file."],
                )
            else:
                Editor(
                    path=path,
                    text=held["document"] if held is not None else "",
                    revision=held["document_revision"] if held is not None else 0,
                    diagnostics=diagnostics,
                    goto=goto_request.value,
                    save_request=save_request.value,
                    flush_request=flush_request.value,
                    hide_types=hide_types.value,
                    show_notes=show_notes.value,
                    edit=edit_request.value,
                    shortcuts=SHORTCUTS,
                    height="100%",
                    event_change=on_change,
                    event_save=on_save,
                    event_cursor=on_cursor,
                    event_applied=on_applied,
                    event_gesture_undo=on_gesture_undo,
                    # the role choices that are marked tags (R-D18)
                    role_words=[word for word in model.ROLE_CHOICES if word.startswith("!")],
                )
        # the BellmanType panel under the editor's frame, so that the
        # editor keeps its place among the region's children, and its
        # handle before it
        if _is_stage(path):
            current = shown.value
            here = current is not None and current.path == path
            parses = parsed is not None and parsed.spans is not None
            kept = last_parsed.current
            refusals = result.refusals if result is not None and result.path == path else []
            Handle("classification")
            BellmanTypeRegion(
                current if here else None,
                path,
                here and parses,
                parsed if parses else (kept[1] if kept is not None and kept[0] == path else None),
                tuple(folder_relative(_refusal_sentence(refusal)) for refusal in refusals),
            )
        elif shows_recipe(path):
            # the recipe the trellis is read under: the panel on its Recipe
            # tab (AAS, M-D17; design pass 9 §2)
            Handle("classification")
            RecipeRegion()


@solara.component
def Tabs(dirty: set):
    """The tabs over the text (spec 0.4 §5.1; brief rule 4; R-D4, R-D32):
    one tab (`Tab`) for each buffer the browser tab holds, in the order the
    buffers were opened, which is the order of the keys of `buffers`; the
    open file's tab is the active one, and a tab whose path is among
    `dirty` reads `unsaved` and its close control is disabled (R-D53).
    brand.css lets the tabs scroll sideways where they are wider than the
    text."""
    opened = open_path.value
    with rv.Html(tag="div", class_="bl-tabs"):
        for path in buffers.value:
            Tab(path, path == opened, path in dirty).key(path)


@solara.component
def Tab(path: str, active: bool, unsaved: bool):
    """One tab of `Tabs`, a document tab of the page's own (design pass 8
    §§4 and 5.3), `.bl-tab-item`, 36 px, also `.bl-active` while it is the
    open file's: a button `.bl-tab` with the path `path` as its hover,
    reading the file's last name in Label, then the mark `unsaved`, the
    Codicon `circle-filled`, `.bl-modified`, where `unsaved` holds, the
    buffer differing from its file, which keeps the word `unsaved` in its
    text, not drawn, and the term's definition as its hover. On the active
    tab, `active`, the name is `.bl-file-name`, the open file's name, and
    the tab stands raised with the accent's 2 px top edge. A click opens
    the file (`open_file`), which first reads the editor's document back
    into the buffer of the file left. After the button stands the tab's
    icon button `close`, the Codicon `close` (R-D53; amendment 02 ruling
    1), `.bl-tab-close`, named `Close` and the file's last name for a
    screen reader, whose hover reads `Close`; while the buffer is unsaved
    it is disabled and its hover reads `Save the file first.`. A click on
    it closes the tab (`close_file`)."""
    last = path.rsplit("/", 1)[-1]
    name = rv.Html(
        tag="span",
        class_="bl-file-name" if active else "",
        attributes={"data-path": path},
        children=[last],
    )
    children = [name]
    if unsaved:
        children.append(
            icons.codicon(
                icons.CODICONS["unsaved"],
                "bl-modified",
                {"title": TERMS["unsaved"]},
                children=[UnseenText("unsaved")],
            )
        )
    attributes = {"type": "button", "data-path": path, "title": path}
    if active:
        attributes["aria-current"] = "true"
    tab = rv.Html(
        tag="button",
        class_="bl-tab bl-active" if active else "bl-tab",
        attributes=attributes,
        children=children,
    )
    rv.use_event(tab, "click", lambda *_: open_file(path))
    close = ToolbarButton(
        "close",
        f"Close {last}",
        "Save the file first." if unsaved else "Close",
        lambda: close_file(path),
        "bl-tab-close",
        disabled=unsaved,
    )
    # the tab's button and its close control side by side, since a button
    # holds no other button
    return rv.Html(
        tag="span",
        class_="bl-tab-item" + (" bl-active" if active else ""),
        children=[tab, close],
    )


@solara.component
def Choice(found: dict):
    """The three choices after a save met a file that changed on disk:
    `Compare`, `Overwrite` and `Reload`, text buttons (design pass 8
    §§5.3 and 6), in a box drawn in the refusal's color, the mark of the
    refused save, whose sentence stands in the list under the error mark
    (AMD-MI-002 §6a rule 1)."""
    with rv.Html(tag="div", class_="bl-choice"):
        with rv.Html(tag="div", class_="bl-choice-buttons"):
            TextButton("Compare", choose_compare, "bl-choice-compare").key("compare")
            TextButton("Overwrite", choose_overwrite, "bl-choice-overwrite").key("overwrite")
            TextButton("Reload", choose_reload, "bl-choice-reload").key("reload")
        if compare_open.value:
            rv.Html(
                tag="pre",
                class_="bl-diff bl-code-small",
                children=[unified_diff(found["disk_text"], found["buffer_text"])],
            )


# --- the BellmanType panel (AMD-MI-002 §5): the classification table of
# unit T of the model interface specification 0.3, its tab Fields, and the
# tabs Parameters, Settings and Methods ---


@dataclasses.dataclass(frozen=True, eq=False)
class ParsedText:
    """The parse of the buffer of a stage file, which the Fields tab's
    tables read (unit R, R-D57): `text`; `spans`, its span table, the
    package's `source_spans`, None where the package refuses the text; and
    `sentence`, the sentence of that refusal (`model.refusal_of`), None
    where the text parses. Two parses are one where they are one object,
    so that a component's memory of a parse compares no tables."""

    text: str
    spans: dict | None
    sentence: str | None = None


def parse_text(path: str, text: str) -> ParsedText:
    """The `ParsedText` of `text`, the buffer of the stage file `path`."""
    try:
        return ParsedText(text, source_spans(text, path))
    except ValueError as refusal:
        return ParsedText(text, None, model.refusal_of(refusal, path).message)


def _classification_of(current: Shown | None, parsed: ParsedText | None = None) -> tuple:
    """The groups of the classification table: none before a stage has
    elaborated; the rows of the shown stage's fields and their listings in
    the span table of the text it was elaborated from, `current.spans`,
    which the loop read by the package's `source_spans`, where no parse is
    given or the parse is of that text; otherwise the rows read from the
    parse `parsed` of a later text, the shown stage being the last
    construction (`model.classification`; unit R, R-D57). The pairs of
    perches the block headers of that text write (`model.header_pairs`)
    place a new field where the package refused every builder, as in the
    empty stage "new stage" writes (unit L, Task 17)."""
    if current is None:
        return ()
    if parsed is None or parsed.spans is None or parsed.text == current.text:
        headers = model.header_pairs(current.spans, current.text)
        return model.classification(current.stage, current.spans, headers=headers)
    headers = model.header_pairs(parsed.spans, parsed.text)
    return model.classification(current.stage, parsed.spans, parsed.text, headers)


def _note_table(change: dict, sentence: str, refused: bool, revision: int, path: str) -> None:
    """Records the classification table's note of `change` (`table_note`):
    its group, its kind and its identity, `sentence`, whether the change
    was `refused`, the `revision` and the file `path` of the stage shown
    when it was made, and the moment of the note."""
    table_note.value = {
        "group": change.get("group"),
        "kind": change.get("kind"),
        "identity": change.get("identity"),
        "sentence": sentence,
        "refused": refused,
        "revision": revision,
        "path": path,
        "made": time.monotonic(),
    }


def _declared_edits(groups, change: dict) -> tuple:
    """The edits of `change` that write a field's declaration: the edits
    `model.classification_edits` answers for `groups` with no side that
    takes a new field's name alone, so that the listing of a decision
    state on the inputs of the block joining `dcsn` and `cntn` (AAS, L-D1)
    is left out. A change that writes no listing gives all its edits."""
    declaring = [
        group._replace(
            targets={
                kind: tuple(target for target in targets if not target.name_alone)
                for kind, targets in group.targets.items()
            }
        )
        for group in groups
    ]
    return model.classification_edits(declaring, change)


def on_table_change(change: dict) -> None:
    """A change of the classification table (rules 3 and 4): a set or a
    role entered in a cell, or a field in the box `add field`, while a
    stage of the open file is shown. The tables are read from the buffer's
    current text: from the shown stage where it was elaborated from that
    text, and otherwise from the text's parse, the shown stage being the
    last construction (`_classification_of`; unit R, R-D57), so that a
    change is written through the spans of the text it lands in and never
    through those of an older text. The replacements
    `model.classification_edits` answers are asked of the editor, which
    applies them as one edit where its document is that text, and the loop
    runs as after typing. The note names what the declaration writes and
    its lines, and where a decision state's name is also listed, the block
    that lists it, `q : ℝ₊ written to line 13 and listed on dcsn_to_cntn`
    (`_declared_edits`; AAS, L-D1). Adding a field selects the first line
    of its declaration, whatever the order of the blocks in the file
    (amendment 02 ruling 9), and any other change moves the editor to the
    first replacement. A change the table refuses, and any change while
    the buffer's text does not parse, which is refused with the parse's
    sentence, is recorded as refused (`_note_table`) with the file and the
    revision of the shown stage: its sentence stands in the list under the
    error mark and its cell or box is marked (AMD-MI-002 §6a rule 1)."""
    current, path = shown.value, open_path.value
    held = buffers.value.get(path) if path is not None else None
    if current is None or held is None or current.path != path:
        return
    parsed = parse_text(path, held["text"])
    if parsed.spans is None:
        _note_table(change, parsed.sentence, True, current.revision, path)
        return
    groups = _classification_of(current, parsed)
    try:
        edits = model.classification_edits(groups, change)
    except ValueError as refusal:
        _note_table(change, str(refusal), True, current.revision, current.path)
        return
    table_note.value = None
    if edits:
        edit_request.value = {
            "edits": [edit._asdict() for edit in edits],
            "expected": parsed.text.replace("\r\n", "\n"),
            "n": _counter(edit_request.value),
        }
        declared = _declared_edits(groups, change)
        first = declared[0]
        written = first.text.strip(", ")
        # the lines of the declaration: several where the box of the group
        # `all branches` writes into the block of each branch (AMD-MI-002 §5
        # rule 2, A2-D12)
        lines = [str(line) for line in sorted({edit.line for edit in declared})]
        where = (
            f"line {lines[0]}"
            if len(lines) == 1
            else f"lines {', '.join(lines[:-1])} and {lines[-1]}"
        )
        # the block whose inputs list a decision state's name (AAS, L-D1)
        listing = dict.fromkeys(
            model.block_at(parsed.spans, edit.line) for edit in edits if edit not in declared
        )
        listed = f" and listed on {' and '.join(listing)}" if listing else ""
        sentence = f"{written} written to {where}{listed}"
        _note_table(change, sentence, False, current.revision, current.path)
        if change.get("kind") == "add":
            # the whole of the declaration's first line, selected, the
            # editor given the focus (amendment 02 ruling 9)
            goto_line(first.line, 1, (first.line, None), focus=True)
        else:
            goto_line(first.line, first.column)


def choose_tab(name: str) -> None:
    """Shows the tab `name` of the BellmanType panel (AMD-MI-002 §5,
    A2-D7)."""
    class_tab.value = name


def _table_groups(groups, linked: frozenset = frozenset()) -> list[dict]:
    """The groups of `model.classification` as the component takes them:
    `perch`, `branch`, `key` (`<perch>/<branch>`, the branch empty where
    none), `heading`, the heading of a group of a branching stage, None
    for a table of one group, `roles`, the role words the group's box
    offers, and `rows`, each with `identity`, `field`, `set`, `role`,
    `line`, `editable`, true where a header lists the field, and `linked`,
    true where the field is among `linked`, the fields of the last
    construction, whose boxes its initial diagrams draw, so that the
    field's name links to its box (unit R, R-D57; amendment 02 ruling
    8)."""
    return [
        {
            "perch": group.perch,
            "branch": group.branch,
            "key": f"{group.perch}/{group.branch or ''}",
            "heading": group.heading,
            "roles": list(model.add_roles(group)),
            "rows": [
                {
                    "identity": row.identity,
                    "field": row.field,
                    "set": row.set,
                    "role": row.role,
                    "line": row.line,
                    "editable": bool(row.listings),
                    "linked": row.identity in linked,
                }
                for row in group.rows
            ],
        }
        for group in groups
    ]


# The title of each perch's table in the Fields tab, its sign and its word
# with a capital, `≺ Arrival`, which is also the hover of a perch's sign in
# Details (spec 0.4 §5.5; unit R, ruling R-P9; design pass 6 §3.1, AAS,
# L-D24).
PERCH_TITLES = {
    perch: f"{sign} {PERCH_WORD[perch].capitalize()}" for perch, sign in PERCH_SIGN.items()
}
# The hover of each perch's title in the Fields tab (design pass 6 §3.7).
PERCH_HOVERS = {
    ARRIVAL: "The information set at which the stage begins.",
    DECISION: "The information set at which the control is chosen.",
    CONTINUATION: "The information set after the control is chosen.",
}
# The texts of each perch's table in the Fields tab, by its perch word: the
# sign and the word of its title, the title's hover, and the accessible
# name of its `+`, `Add field at arrival` (design pass 6 §§3.1 and 3.7).
PERCH_TEXTS = {
    perch: {
        "sign": sign,
        "word": PERCH_WORD[perch].capitalize(),
        "hover": PERCH_HOVERS[perch],
        "add": f"Add field at {PERCH_WORD[perch]}",
    }
    for perch, sign in PERCH_SIGN.items()
}
# The hover of each role word of the Fields tab, the role in words with a
# capital, `Value` for `!vlu` (design pass 6 §3.7).
ROLE_HOVERS = {model.role_word(role): role.capitalize() for role in model.ROLE_CLASS}


@solara.component_vue("classification.vue")
def ClassificationTables(
    groups: list = [],
    perch_texts: dict = {},
    role_choices: list = [],
    role_hovers: dict = {},
    completions: list = [],
    shortcuts: dict = {},
    disabled: bool = False,
    note: dict = None,
    refused: dict = None,
    selected: str = None,
    event_change=None,
    event_select_field=None,
    named: dict = {},
):
    """The three tables of the classification table; see
    classification.vue."""


# the tabs of the BellmanType panel, in the order of their buttons, each
# with the title its button carries (AMD-MI-002 §5 rules 2 to 5), with a
# capital (M-I19; the delegated acceptance of unit M, D6)
CLASS_TABS = {
    "Fields": "The fields of each perch, with their sets and roles",
    "Parameters": "The parameters and their values at the occurrence",
    "Settings": "The settings of the occurrence",
    "Methods": "The methods bound within the occurrence",
}


def value_tab(
    current: Shown | None, name: str, folder: model.Folder | None = None
) -> recipe.Tab | None:
    """The tab `name`, Parameters, Settings or Methods, of the BellmanType
    panel for the shown stage (AMD-MI-002 §5 rules 3 to 7): its rows read
    through the tab's recipe at the occurrence the stage is bound as, from
    the occurrence's record, by `recipe.parameters_tab`,
    `recipe.settings_tab` or `recipe.methods_tab`, so that another recipe
    chosen for the tab changes every tab at once, its files named relative
    to `folder`, the tab's folder where none is given; None before a stage
    has elaborated."""
    if current is None:
        return None
    folder = folder if folder is not None else tab_folder.value
    key = current.position[1] if current.position is not None else None
    if name == "Parameters":
        return recipe.parameters_tab(folder, current.stage, current.record, key)
    if name == "Settings":
        return recipe.settings_tab(folder, current.record, key)
    return recipe.methods_tab(folder, current.stage, current.record, key)


def _naming_note(notes, name: str) -> str | None:
    """The first of `notes`, the sentences of a stage's binding, that names
    the parameter `name` as the package's check of a calibration names one,
    `parameter 'Π_α'` (`calibration_requirements` of `bellman.stage`), its
    paths printed from the folder (`folder_relative`; K-D11); None where none
    names it."""
    named = f"parameter {name!r}"
    return folder_relative(next((note for note in notes if named in note), None))


def _tab_rows(tab: recipe.Tab, queued: tuple = (), notes: tuple = ()) -> list[dict]:
    """The rows of a value tab as values.vue takes them: `name`, the
    parameter, the setting or the target; `detail`, the parameter's set,
    the setting's kind or the method the stage binds at the target;
    `value`, the value as the file writes it or the method's tag, the empty
    text where none is shown, and for a row of which `queued`, values typed
    in the tab and not yet written, holds a value, the text last typed
    (unit L, Task 16); `choices`, the tags the package admits at the
    target (`recipe.MethodRow`; unit L, Task 18); `note`, the stage's
    refusal where it binds no method at the target, or the package's
    refusal of the target's entry, and for a parameter the sentence of
    `notes`, the notes of the binding of the stage shown, that names it
    (`_naming_note`), the package's refusal of its value, which the row's
    input then shows (unit L, Task 16), each with its paths printed from
    the folder (`folder_relative`; K-D11); `refused`, whether `methodize`
    refuses the target's entry, the row's choice then marked with `note` as
    its hover (unit L, Task 18), false for a parameter or a setting; and
    `file` and `line`, where the value or the method is written, None where
    no file writes it."""
    typed = {entry["name"]: entry["typed"] for entry in queued}
    rows = []
    for row in tab.rows:
        where = (
            {"file": None, "line": None}
            if row.place is None
            else {"file": row.place.file, "line": row.place.line}
        )
        if isinstance(row, recipe.MethodRow):
            shown_row = {
                "name": row.target,
                "detail": row.bound or "",
                "value": row.tag,
                "choices": list(row.choices),
                "note": folder_relative(row.note),
                "refused": row.refused,
            }
        else:
            parameter = isinstance(row, recipe.ParameterRow)
            shown_row = {
                "name": row.name,
                "detail": row.domain if parameter else row.kind,
                "value": typed.get(row.name, row.value or ""),
                "choices": [],
                "note": _naming_note(notes, row.name) if parameter else None,
                "refused": False,
            }
        rows.append({**shown_row, **where})
    return rows


def _row_place(tab: recipe.Tab, name: str) -> tuple[str | None, int | None]:
    """The file that a write for the row `name` of a value tab changes
    (AMD-MI-002 §5 rule 6), with the row's line there: the file and the
    line that write the row's value or method, else the file the tab
    names, to which a value no file writes is added, and no line; None for
    the file where neither stands."""
    for row in tab.rows:
        named = row.target if isinstance(row, recipe.MethodRow) else row.name
        if named == name and row.place is not None:
            return row.place.file, row.place.line
    return tab.file, None


def _panel_write(
    tab: str, name: str, write, current: Shown, folder: model.Folder
) -> tuple[str | None, recipe.Written | None]:
    """A write asked in the tab `tab`, Parameters, Settings or Methods, of
    the BellmanType panel for its row `name` of the stage shown `current`
    in the folder `folder` (AMD-MI-002 §5 rule 6): refused while the file it
    changes (`_row_place`) holds unsaved text in the editor; otherwise
    `write(current, key)`, the call of `recipe.write_value` or
    `recipe.write_method` for that stage and the key of its occurrence,
    whose refusal is its sentence and nothing added (§6a rule 2). A refusal
    is recorded (`value_note`) with the row, the file and the row's line
    there, and the moment: its sentence stands in the list under the error
    mark and the row's input or select is marked (AMD-MI-002 §6a rule 1;
    ruling R46); a write of the same row clears it, so that a write of
    another row typed after it leaves it standing (unit L, Task 16).
    Answers the file the write changes and, where the file was written,
    the `Written`, None otherwise; the caller takes the steps after a
    write (`_after_write`)."""
    file, line = _row_place(value_tab(current, tab, folder), name)
    if file is not None and _dirty(buffers.value.get(file)):
        sentence = f"{file} holds unsaved text"
    else:
        key = current.position[1] if current.position is not None else None
        written = write(current, key)
        if written.saved:
            note = value_note.value
            if note is not None and (note["tab"], note["name"]) == (tab, name):
                value_note.value = None
            return file, written
        sentence = written.reason
    value_note.value = {
        "tab": tab,
        "name": name,
        "sentence": sentence,
        "file": file,
        "line": line,
        "path": current.path,
        "position": current.position,
        "source": current.source,
        "made": time.monotonic(),
    }
    return file, None


def _answer_value(answered_id, entry: dict | None = None) -> None:
    """Adds `answered_id` to the ids of the values answered, of which the
    last VALUE_ANSWERS are kept, and takes `entry`, where it is given, from
    the queue of values typed (`value_queue`); under VALUE_LOCK, so that a
    value added to the queue meanwhile is kept there."""
    with VALUE_LOCK:
        held = value_queue.value
        queue = tuple(each for each in held["queue"] if each is not entry)
        answered = (*held["answered"], answered_id)[-VALUE_ANSWERS:]
        value_queue.value = {"queue": queue, "answered": answered}


def write_queued() -> None:
    """Writes the values of the queue of values typed (`value_queue`) in the
    order of their Enter, each once, holding WRITER_LOCK (unit L, Task 16;
    defect 5 of the UX simulation): the first value of the queue is written
    by `recipe.write_value` to the calibration or the settings file the
    recipe names for the occurrence of the stage shown at its Enter, as the
    input showed it (`_panel_write`), and then taken from the queue and
    answered (`_answer_value`), so that the tab reads its files again and
    values.vue shows the value as the file writes it; a value typed while
    the queue is written is written in its turn. Once the queue is empty,
    or once a value's write raises, the steps after a write (`_after_write`)
    are taken once for each file written, with its last text, after which
    the loop binds the stage again (unit L's final judgment, §6 item 6). A
    writer that finds the queue empty, its values written by the writer
    before it, writes nothing. A value is answered even where its write
    raises, so that the queue never keeps a value it cannot write."""
    with WRITER_LOCK:
        written = {}
        try:
            while value_queue.value["queue"]:
                entry = value_queue.value["queue"][0]
                kind = "calibration" if entry["tab"] == "Parameters" else "settings"
                try:
                    file, made = _panel_write(
                        entry["tab"],
                        entry["name"],
                        lambda current, key, entry=entry, kind=kind: recipe.write_value(
                            entry["folder"],
                            current.record,
                            key,
                            kind,
                            entry["name"],
                            entry["shown"],
                            entry["typed"],
                        ),
                        entry["current"],
                        entry["folder"],
                    )
                    if made is not None:
                        written[file] = made
                finally:
                    _answer_value(entry["id"], entry)
        finally:
            for file, made in written.items():
                _after_write(file, made)


def on_value_write(data: dict) -> None:
    """A value typed in a row of the Parameters or the Settings tab, on
    Enter (AMD-MI-002 §5 rules 3, 4 and 6; A2-D8; unit L, Task 16): added
    to the queue of values typed (`value_queue`) with the stage shown and
    the tab's folder, and written in its turn by a writer started in a
    thread of its own (`write_queued`), so that the event is answered at
    once, the status line printing the loop running while the queue holds
    a value, and a value typed while an earlier one is written or bound is
    neither lost nor written twice. A value asked while no stage of the
    open file is shown is answered and written nowhere."""
    tab, name = data.get("tab"), data.get("name")
    if tab not in ("Parameters", "Settings"):
        return
    current = shown.value
    if current is None or current.path != open_path.value:
        _answer_value(data.get("id"))
        return
    entry = {
        "id": data.get("id"),
        "tab": tab,
        "name": name,
        "shown": data["shown"],
        "typed": data["typed"],
        "current": current,
        "folder": tab_folder.value,
    }
    with VALUE_LOCK:
        held = value_queue.value
        value_queue.value = {**held, "queue": (*held["queue"], entry)}
    threading.Thread(target=write_queued, name="value-writer", daemon=True).start()


def on_method_choice(data: dict) -> None:
    """A method chosen in a row of the Methods tab among the methods the
    package admits at its target (AMD-MI-002 §5 rules 5 and 6; unit L,
    Task 18): its tag written by `recipe.write_method` in the entry of the
    last methods file the recipe names for the occurrence that names the
    target (`_panel_write`), after which the tab reads its files again
    (`value_writes`) and the steps after a write are taken (`_after_write`),
    after which the loop binds the stage again. A choice asked while no
    stage of the open file is shown is dropped."""
    name = data.get("name")
    current = shown.value
    if current is None or current.path != open_path.value:
        return
    file, written = _panel_write(
        "Methods",
        name,
        lambda current, key: recipe.write_method(
            tab_folder.value, current.record, key, name, data["shown"], data["tag"]
        ),
        current,
        tab_folder.value,
    )
    if written is not None:
        value_writes.value = value_writes.value + 1
        _after_write(file, written)


def go_to_value_place(data: dict) -> None:
    """A row's name in a value tab, clicked or given Enter (spec 0.4 §5.5;
    unit R, R-D23): the file that writes the row opens in the editor at
    the row's line, and the place left is recorded (`open_at`)."""
    open_at(data["file"], int(data["line"]))


@solara.component_vue("values.vue")
def ValueTabs(
    tab: str = "Parameters",
    rows: list = [],
    file: str = None,
    sentence: str = None,
    refused: str = None,
    answered: list = [],
    disabled: bool = False,
    event_write=None,
    event_choose=None,
    event_open_place=None,
):
    """The tabs Parameters, Settings and Methods of the BellmanType panel;
    see values.vue."""


@solara.component
def ClassTabs(chosen: str):
    """The view tabs of the BellmanType panel (AMD-MI-002 §5 rules 2 to 5;
    design pass 8 §§4 and 6), VSCode Elements' tabs, `<vscode-tabs>` with
    one header per tab of `CLASS_TABS` (`ViewTab`), `.bl-class-tab` with
    `data-tab` and the tab's hover, the tab shown, `chosen`, the selected
    one and also `.bl-active`. A click on a tab, or Enter on the tab the
    arrow keys gave the focus, shows it (`choose_tab`); the header stops
    either, so that the library selects no tab of its own and the tab
    selected is always the one shown (the delegated acceptance of unit M,
    D3). The tabs hold no panel of their own, since the panel under them
    shows the tab chosen."""
    names = list(CLASS_TABS)
    headers = [
        ViewTab(
            name,
            "bl-class-tab" + (" bl-active" if name == chosen else ""),
            {"data-tab": name, "title": title},
            lambda name=name: choose_tab(name),
            True,
        ).key(name)
        for name, title in CLASS_TABS.items()
    ]
    return rv.Html(
        tag="vscode-tabs",
        class_="bl-class-tabs",
        attributes={"selected-index": str(names.index(chosen) if chosen in names else 0)},
        children=headers,
    )


@solara.component
def BellmanTypeRegion(
    current: Shown | None,
    path: str,
    editable: bool,
    parsed: ParsedText | None = None,
    refused: tuple = (),
):
    """The BellmanType panel under the editor (AMD-MI-002 §5; unit T, §4),
    `.bl-classification`, with no head: its strip (`InspectorStrip`; design
    pass 10 §4) holds the view tabs of its four tabs, Fields, Parameters,
    Settings and Methods, the tab shown marked (`ClassTabs`; design pass 8
    §6), the open file's name, its path `path` as its hover, and the icon
    button `open wide` (`WideButton`); the main bar's toggle `Inspector`
    folds the panel, window.vue keeping the fold, the loop's state standing
    in the status line alone (R-D50); then the tab shown,
    for the stage last elaborated for the open file, `current`, or `Not
    elaborated.` before the file has elaborated. While `region_wide` names
    it, the panel stands in its wide panel over the window, `.bl-wide`, a
    second click of `open wide` or Escape returning it to its column.
    Fields is the three tables of unit T, read from `parsed`, the parse of
    the buffer's text, where it is given and is not the text of `current`,
    and otherwise from `current` (`_classification_of`), which write the
    block headers of the text; a row's field links to its box where
    `current` holds the field, and is text otherwise; the row of each field
    that a sentence of `refused`, the refusals of the open file, names
    (`model.named_rows`) is marked, the sentence its hover (unit R, R-D57;
    amendment 02 rulings 7 and 8). Parameters, Settings and Methods show the
    values and the methods of `current` at the occurrence it is bound as,
    read through the tab's recipe (`value_tab`), each naming the file it
    writes, and write a value or a method to the file the recipe names (§5
    rules 3 to 7); a value typed in Parameters or Settings is shown as typed
    from its Enter until it is written (`value_queue`), and the input of a
    parameter that a note of the stage's binding names, the package's
    refusal of its value, is marked, the note its hover, while the note
    stands under the error mark (`_bound_as_read`; unit L, Task 16). The
    tabs are dimmed and locked where `editable` is false,
    which `FileRegion` passes while the buffer's text does not parse, the
    tables then being those of the file's last parse (amendment 02 ruling
    10). The tables always show the types, whatever `hide types` draws in
    the editor. The sentence of a change written stands under its group,
    and the cell or the box of a refused change is marked, while the shown
    stage is of the file and the revision it had when the change was made
    (`_standing_table_note`); the
    input or the select of a row whose write was refused is marked on its
    tab while the panel shows the file, the occurrence and the source on
    which the write was asked (`_standing_value_note`); the sentence of
    each refusal stands in the list under the error mark (AMD-MI-002 §6a
    rule 1; ruling R46). The region takes the height dragged on its handle
    (AMD-MI-002 §6 rule 2) and keeps one height on every tab, the tab's
    content scrolling inside it (R-D51)."""
    chosen = class_tab.value
    folder = tab_folder.value
    writes = value_writes.value
    writing = value_queue.value
    groups = solara.use_memo(lambda: _classification_of(current, parsed), [current, parsed])
    # the fields of the last construction, whose boxes its initial
    # diagrams draw
    linked = solara.use_memo(
        lambda: frozenset() if current is None else frozenset(map(str, current.stage.fields())),
        [current],
    )
    values = solara.use_memo(
        lambda: None if chosen == "Fields" else value_tab(current, chosen),
        [current, chosen, folder, writes, writing["answered"]],
    )
    # the values typed in the tab shown at the occurrence shown and not yet
    # written, and the notes of the stage's binding while they stand under
    # the error mark
    shown_at = None if current is None else (current.path, current.position, current.source)
    queued = tuple(
        entry
        for entry in writing["queue"]
        if entry["tab"] == chosen
        and (entry["current"].path, entry["current"].position, entry["current"].source) == shown_at
    )
    notes = tuple(current.notes) if current is not None and _bound_as_read(current) else ()
    # the note that stands: a change written, told under its group, or a
    # change refused, whose cell or box is marked
    note = _standing_table_note(current)
    told = marked = None
    if note is not None and note["refused"]:
        marked = {"group": note["group"], "kind": note["kind"], "identity": note["identity"]}
    elif note is not None:
        told = {"group": note["group"], "sentence": note["sentence"]}
    written = _standing_value_note(current)
    refused_row = written["name"] if written is not None and written["tab"] == chosen else None
    wide = region_wide.value == "types"
    with rv.Html(
        tag="section",
        class_="bl-classification" + (" bl-wide" if wide else ""),
        attributes={"aria-label": "types", "data-panel": "types"},
    ):
        InspectorStrip(ClassTabs(chosen), path, "types")
        if current is None:
            rv.Html(
                tag="p",
                class_="bl-class-empty",
                children=["Not elaborated."],
            )
        elif values is not None:
            ValueTabs(
                tab=chosen,
                rows=_tab_rows(values, queued, notes),
                file=values.file,
                sentence=folder_relative(values.sentence),
                refused=refused_row,
                answered=list(writing["answered"]),
                disabled=not editable,
                event_write=on_value_write,
                event_choose=on_method_choice,
                event_open_place=go_to_value_place,
            )
        else:
            ClassificationTables(
                groups=_table_groups(groups, linked),
                perch_texts=PERCH_TEXTS,
                role_choices=list(model.ROLE_CHOICES),
                role_hovers=ROLE_HOVERS,
                completions=list(model.set_completions(current.stage)),
                shortcuts=SHORTCUTS,
                disabled=not editable,
                note=told,
                refused=marked,
                selected=_selected_field(),
                event_change=on_table_change,
                event_select_field=on_select_field,
                named=model.named_rows(groups, refused),
            )


# --- the panel ---


def describe(selection: dict | None, current: Shown | None) -> dict | None:
    """What the panel shows for the selection: the piece of the node with,
    for a box, the head of its Details (`box_head`), or the sentence of a
    node the graph does not hold."""
    if selection is None or current is None:
        return None
    graph_id, node_id = selection["graphId"], selection["nodeId"]
    try:
        piece = model.piece(level_stage(current), graph_id, node_id, level_collection(current))
    except KeyError as error:
        return {"kind": "sentence", "text": error.args[0] if error.args else str(error)}
    # a builder at the declared level carries its unmet requirements, which
    # the stage, not the version the declared level reads, answers (R7;
    # specification 0.6 §9; SE-28)
    if piece.kind == "layer" and current.declared is not None and not builders_operative.value:
        namespace = node_id[: -len(LAYER_ID_ENDING)]
        piece = piece._replace(requires=model.requirements(current.stage, namespace))
    head = None
    if piece.kind == "box":
        head = box_head(level_stage(current), level_collection(current), graph_id, node_id, piece)
    return {"kind": "piece", "piece": piece, "head": head}


def _block_record(current: Shown | None, block: str | None) -> str:
    """The printed record of the block `block` of the shown stage
    (`model.block_record`), the empty string where none is held."""
    if current is None or not block:
        return ""
    try:
        return model.block_record(current.stage, block)
    except KeyError:
        return ""


def _builder_of_block(current: Shown | None, block: str | None) -> model.Piece | None:
    """The piece of the layer of the builder the block `block` denotes, in
    the builders graph that holds it (`model.piece`); None where no stage
    is shown, the cursor is in no block or no graph holds that layer."""
    if current is None or not block:
        return None
    node_id = f"{block}{LAYER_ID_ENDING}"
    graph_id = graph_of_node(level_collection(current), node_id)
    if graph_id is None:
        return None
    try:
        return model.piece(level_stage(current), graph_id, node_id, level_collection(current))
    except KeyError:
        return None


def _boxes_reading(current: Shown | None, line: int | None) -> list:
    """The boxes whose kernels read `line` of the shown stage's text, each
    as `(node id, graph id)` (`model.boxes_reading`); none where no stage
    is shown or the cursor is on no line."""
    if current is None or line is None:
        return []
    found = []
    for node_id in model.boxes_reading(level_stage(current), line):
        graph_id = graph_of_node(level_collection(current), node_id)
        if graph_id is not None:
            found.append((node_id, graph_id))
    return found


def _name_report(current: Shown | None, name: str | None):
    """The name under the cursor in the shown stage: its `model.NameReport`
    and the file and the line at which the calibration of the occurrence the
    stage is bound as writes its value (`recipe.value_place`), None where no
    file writes it; None where no stage is shown or the cursor stands on no
    name."""
    if current is None or not name:
        return None
    report = model.name_report(level_stage(current), level_collection(current), current.text, name)
    place = recipe.value_place(tab_folder.value, current.record, "calibration", name)
    return report, None if place is None else (place.file, place.line)


def FoldSummary(children: list):
    """The summary of a fold of Details, a row of 24 px, `.bl-row` (design
    pass 8 §§5.2 and 6): the twistie, the Codicon `chevron-right` while the
    fold is closed and `chevron-down` while it is open, which brand.css
    shows by the fold's state, then `children`, the fold's name with its
    capital."""
    twisties = [
        icons.codicon(icons.CODICONS["folded"], "bl-twistie bl-closed-twistie"),
        icons.codicon(icons.CODICONS["unfolded"], "bl-twistie bl-open-twistie"),
    ]
    return rv.Html(tag="summary", class_="bl-row bl-fold-summary", children=[*twisties, *children])


def LegendDetails(legend: solara.Element):
    """The legend of the graph shown, Details' last element whether or not
    a node is selected: the element `legend` under a details element whose
    summary reads `Legend` (design pass §2: the legend folded; unit K,
    K-D2; unit R, R-D36; design pass 8 §6), a row with its twistie
    (`FoldSummary`), which the browser opens and closes, so that no state
    of it is kept. The element is keyed, since the elements before it in
    Details vary in number, and an element of another tag at its place
    would otherwise take its widget."""
    return rv.Html(
        tag="details",
        class_="bl-legend-details",
        children=[FoldSummary(["Legend"]), legend],
    ).key("legend-details")


def details_context(collection: dict | None, selection: dict | None) -> str:
    """The context of Details' head (AAS, L-D12; design pass 3 §2): the
    selected node's name and its position, `𝐺 · cntn_to_dcsn` or `cons ·
    periods[1]`. For a layer, whose id is its namespace followed by
    `LAYER_ID_ENDING`, the namespace's last part and the parts before it;
    for a node of the selection's graph in `collection`, the first line of
    its label, else its id, and its namespace. Empty where nothing is
    selected or the view holds no such node."""
    if selection is None or collection is None:
        return ""
    node_id, graph_id = selection.get("nodeId"), selection.get("graphId")
    if not node_id:
        return ""
    if node_id.endswith(LAYER_ID_ENDING):
        parts = node_id[: -len(LAYER_ID_ENDING)].split("/")
        name, position = parts[-1], "/".join(parts[:-1])
    else:
        found = next((entry for entry in collection["graphs"] if entry["id"] == graph_id), None)
        nodes = found["nodes"] if found is not None else []
        node = next((entry for entry in nodes if entry["id"] == node_id), None)
        if node is None:
            return ""
        name = (node.get("label") or node_id).split("\n")[0]
        position = node.get("namespace", "")
    return f"{name} · {position}" if position else name


def details_class() -> str:
    """The classes of Details' section, `.bl-panel`, and `.bl-wide` while
    Details stands in its wide panel over the window (AAS, L-D12)."""
    return "bl-panel bl-wide" if region_wide.value == "details" else "bl-panel"


def DetailsHead(context: str):
    """The head of Details, the panels' one head (`RegionHead`; AAS, L-D12;
    design pass 3 §2; design pass 8 §5.5): the name `Details`, its context,
    the selected piece's name and position (`details_context`), in
    `.bl-details-context`, which its hover holds whole, the icon button
    `open wide`, the Codicon `window` (`WideButton`), and `close`, the
    Codicon `close` (`CloseButton`), which folds Details as the main bar's
    toggle `Details` does, and returns it to its column while it stands
    wide."""
    shown = []
    if context:
        shown.append(
            rv.Html(
                tag="span",
                class_="bl-details-context",
                attributes={"title": context},
                children=[context],
            )
        )
    wide = region_wide.value == "details"
    return RegionHead(
        "details", shown, wide=WideButton("details"), closing=CloseButton("details", wide)
    )


@solara.component
def Panel(result: Outcome | None, current: Shown | None, legend: solara.Element | None = None):
    """Details, under the view (spec 0.4 §5.5), `.bl-panel`, under its head
    (`DetailsHead`; AAS, L-D12), whose context is the selected node's name
    and position (`details_context`): the mark
    of each refusal of the open text that stands (`RefusalBox`), whose
    sentence, as each note of the bindings, stands in the list under the
    error mark (AMD-MI-002 §6a rule 1); the selected node's piece, or, when
    nothing is selected, the sentence of the empty state and the sheets of
    the stage; the name under the cursor (`NameView`), read from the shown
    object's own text at the cursor's line and column, so that a new
    elaboration reads it again, above the block's record (usability
    walkthrough §5, "Find where a field is used"; unit K, Task 14); and
    under the details element `.bl-cursor-details`, whose summary reads
    `cursor`, the block under the cursor with its record, the boxes born in
    it and the boxes whose kernels read the cursor's line, closed while a
    node is selected and open while nothing is (design pass §2, "An
    operator box"; unit K, Task 5), drawn where it holds one of them.
    `legend`, the element `Legend` that `ViewRegion` makes, is the body's
    last element, under `LegendDetails`, whether or not a node is selected,
    so that the collection's label never stands first (design pass §2;
    unit K, K-D2; G-R23); Details has a height of its own, so that the
    legend does not change the height of the graph's host (G-R76).

    While the open file's text is refused, `result` stale, Details
    describes the last construction of that file, whose label the legend
    names, and nothing the editor's cursor reads, since the cursor stands in
    a text that construction does not hold; where the file has no
    construction, Details holds the refusal rows alone (usability
    walkthrough §4 item 11; unit K, Task 13; spec 0.4 §5.7)."""
    selection = selected.value
    refused = result is not None and result.stale
    # the cursor's block and line are read against the shown object only
    # when it is the open file's
    own = current if current is not None and current.path == open_path.value else None
    if refused:
        current = own
    # the level the layers button shows is read by each memo below (SE-7)
    operative = builders_operative.value
    described = solara.use_memo(
        lambda: describe(selection, current), [selection, current, operative]
    )
    block = None if refused else cursor_block.value
    line = None if refused else cursor_line.value
    if refused:
        own = None
    record = solara.use_memo(lambda: _block_record(own, block), [own, block])
    builder = solara.use_memo(lambda: _builder_of_block(own, block), [own, block, operative])
    reading = solara.use_memo(lambda: _boxes_reading(own, line), [own, line, operative])
    place = cursor_place.value
    # the name under the cursor, read from the shown object's own text
    name = solara.use_memo(
        lambda: None if own is None or place is None else model.name_at(own.text, *place),
        [own, place],
    )
    named = solara.use_memo(lambda: _name_report(own, name), [own, name, operative])
    context = details_context(
        level_collection(current) if current is not None else None, selection
    )
    with rv.Html(tag="section", class_=details_class(), attributes={"aria-label": "details"}):
        DetailsHead(context)
        with rv.Html(tag="div", class_="bl-panel-body"):
            if result is not None:
                for refusal in result.refusals:
                    RefusalBox(result.path, refusal)
            # a refused text whose file has no construction: the refusal
            # rows alone, since nothing describes another file's stage
            alone = refused and current is None
            if described is None:
                if not alone:
                    EmptyPanel(current)
            elif described["kind"] == "piece":
                PieceView(described["piece"], described["head"])
            else:
                rv.Html(tag="div", class_="bl-empty", children=[described["text"]])
            # the name under the cursor, above the fold that holds the block's
            # record; keyed, since the elements before it vary in number
            if named is not None:
                NameView(*named).key("name-view")
            # the fold `cursor`, drawn where it holds the block, its boxes or
            # the boxes reading the cursor's line
            if (block and (current is not None or block_nodes.value)) or reading:
                # the fold is keyed, since the elements before it vary in
                # number; its attribute `open` follows the selection
                with rv.Html(
                    tag="details",
                    class_="bl-cursor-details",
                    attributes={"open": selection is None},
                ).key("cursor-details"):
                    FoldSummary([Term("cursor", "Cursor")])
                    if block and current is not None:
                        rv.Html(
                            tag="div",
                            class_="bl-cursor-block bl-code-small",
                            children=[
                                Term("block"),
                                f" {block} · ",
                                Term("builder"),
                                f" {block}",
                            ],
                        )
                        if record:
                            rv.Html(
                                tag="pre",
                                class_="bl-block-record bl-code-small",
                                children=[record],
                            )
                        # the builder's rows beside the block's record, unless
                        # the builder is the selected piece, whose rows stand
                        # above
                        if builder is not None and (
                            selection is None or selection["nodeId"] != builder.node_id
                        ):
                            rv.Html(
                                tag="div",
                                class_="bl-block-label",
                                children=[Term("builder"), f" {block}"],
                            )
                            with rv.Html(tag="div", class_="bl-builder-rows"):
                                AttributeRows(builder.attributes)
                            if builder.signature:
                                rv.Html(
                                    tag="pre",
                                    class_="bl-builder-signature bl-code-small",
                                    children=[builder.signature],
                                )
                    if block_nodes.value and block:
                        rv.Html(
                            tag="div",
                            class_="bl-block-label",
                            children=[Term("box", "boxes"), f" of {block}"],
                        )
                        with rv.Html(tag="ul", class_="bl-block-nodes bl-code-small"):
                            for node_id in block_nodes.value:
                                active = selection is not None and selection["nodeId"] == node_id
                                NodeItem(node_id, None, active).key(node_id)
                    if reading:
                        # a label of a few words, as `boxes of <block>`
                        # (design pass §1 item 8; unit K, Task 6)
                        rv.Html(
                            tag="div",
                            class_="bl-block-label",
                            children=[Term("box", "boxes"), f" reading line {line}"],
                        )
                        with rv.Html(tag="ul", class_="bl-reading-nodes bl-code-small"):
                            for node_id, graph_id in reading:
                                active = selection is not None and selection["nodeId"] == node_id
                                NodeItem(node_id, graph_id, active).key(f"{graph_id}:{node_id}")
            if legend is not None and not alone:
                LegendDetails(legend)


@solara.component
def RefusalBox(path: str, refusal: dict):
    """The mark of one refusal in the panel: its head, `refused at
    <file>:<line>:<column> · rule <rule>`, with the address and the refused
    direction where the refusal has them, in a box drawn in the refusal's
    color; its message, and the words the package says to write, stand in
    the list under the error mark (AMD-MI-002 §6a rule 1)."""
    places = []
    if refusal["line"] is not None:
        places.append(f"{path}:{refusal['line']}:{refusal['column']}")
    if refusal["address"] and not _is_position(refusal["address"], refusal["line"]):
        places.append(refusal["address"])
    where = f" at {', '.join(places)}" if places else f" in {path}"
    rule = _rule_word(refusal["rule"])
    head = [Term("refused"), where]
    if rule:
        head.extend([" · ", Term("rule"), " ", Term(rule) if rule in TERMS else rule])
    if refusal["direction"]:
        head.extend([" · ", Term(refusal["direction"]), " builders graph"])
    with rv.Html(tag="div", class_="bl-refusal bl-code-small"):
        rv.Html(tag="div", class_="bl-refusal-rule", children=head)


@solara.component
def SheetButton(sheet: str, opened: bool):
    """The text button of the stage's sheet `sheet` in Details (design pass
    §2; design pass 8 §§5.3 and 6), `.bl-sheet-button` with `data-sheet`,
    its word with a capital, `Definitions`, and `.bl-active` with
    `aria-pressed` while the sheet is shown, `opened`; a click shows the
    sheet or hides it (`toggle_sheet`)."""
    return TextButton(
        sheet.capitalize(),
        lambda: toggle_sheet(sheet),
        "bl-sheet-button" + (" bl-active" if opened else ""),
        f"The stage's {sheet} sheet",
        {"data-sheet": sheet, "aria-pressed": "true" if opened else "false"},
    )


@solara.component
def EmptyPanel(current: Shown | None):
    """Details when nothing is selected (spec 0.4 §5.5; design pass §2;
    design pass 8 §6): the words `No selection`, the sheets of the stage
    behind five text buttons on one row (`SheetButton`), and, in
    `div.bl-used-at`, where the stage's file is used
    (AMD-MI-002 §3 rule 6), the rows `periods`, the periods at which the
    tab's recipe holds it, and `also`, each other recipe of the folder that
    holds it with its periods, each a range and a link to that recipe's
    trellis at the occurrence the stage is bound as, or at the recipe's
    first where it holds no such occurrence (`trellis.use_rows`). The parts
    stand in one element, `div.bl-empty-panel`, since Solara lays out the
    several top-level elements of a component as a column with gaps of 12
    px between them, so that they stand 8 px apart, as every block of
    Details (design pass 13 §4; the fix wave Q3b, item 17, D25)."""
    name = sheet_open.value
    sheets = solara.use_memo(
        lambda: model.stage_sheets(current.stage) if current is not None and name else {},
        [current, name],
    )
    uses = solara.use_memo(
        lambda: trellis.use_rows(current.uses, current.source, current.position)
        if current is not None
        else [],
        [current],
    )
    with rv.Html(tag="div", class_="bl-empty-panel"):
        rv.Html(tag="div", class_="bl-empty", children=[NO_SELECTION])
        if current is not None:
            with rv.Html(tag="div", class_="bl-sheet-buttons"):
                for sheet in SHEETS:
                    SheetButton(sheet, name == sheet).key(sheet)
            if name and name in sheets:
                rv.Html(tag="pre", class_="bl-sheet bl-code-small", children=[sheets[name]])
            if uses:
                with rv.Html(tag="div", class_="bl-used-at"):
                    DetailsRows(uses)


# The term whose definition a row's key of Details carries, where it is not
# the key itself: the row `methods` lists the methods bound, which the term
# `method` defines, while `methods` defines the sources of methods.
DETAILS_TERMS = {"methods": "method"}
# The end of each part of a line of Details but the last, a space that does
# not break and the dot, so that a wrapped line ends with the dot and never
# begins with it; a plain space follows it.
PART_END = "\N{NO-BREAK SPACE}·"
# The rows of Details whose value is words of the page, the states a stage
# occurrence's version is bound to, printed in Small and joined as the
# status line joins them, `methodized, configured` (design pass 13 §3; C8).
WORD_ROWS = {"bound"}
# The parts of a line of Details that are words of the page among the
# file's words, which Details prints in Small (`.bl-small`): a route's
# status and a wire's origin in a cable's Details (design pass 13 §3; the
# fix wave Q3b, item 19, C8).
WORD_PARTS = {"certified", "not certified", "inferred", "authored"}
# The first words of a line's head that are words of the page, printed in
# Small before the name that follows them in Code small: a route's branch,
# `branch keep` (the fix wave Q3b, item 19, C8).
WORD_HEADS = {"branch"}
# The parts of a row of Details that are names, which the page prints in
# ink-1 among the row's values in ink-2 (design pass 13 §5; E9), by the
# row's key: `first`, the part's first word, a field's name before its set
# and role; `whole`, the whole part, a field or a join of two fields, a
# file's path, or another occurrence's joins. A row's other parts, sets,
# roles, states, periods and places, are values.
NAME_PARTS = {
    "fields": "first",
    "inputs": "first",
    "outputs": "first",
    "policies": "first",
    "from": "whole",
    "to": "whole",
    "also": "whole",
    "file": "whole",
    "sources": "whole",
    "written": "whole",
}


def sentence_case(words: str) -> str:
    """The page's words `words` with a capital on their first letter, as the
    page prints a key of Details and every Small label (design pass 13 §3;
    C12): `file` is `File`, `bound methods` is `Bound methods`."""
    return words[:1].upper() + words[1:]


@solara.component
def DetailsRows(rows, terms: dict | None = None):
    """The rows of Details for a selection or for the open stage file
    (design pass §2; unit K, K-D2), in `div.bl-details-rows`: each row
    `(key, lines)` a `.bl-details-row` with data-key, its key
    `.bl-details-key`, a word in sentence case that carries its definition
    (`Term`; design pass 13 §3), the
    definition of the term `terms` names for it where it names one, and its
    value `.bl-details-value`, one `.bl-details-line` per `trellis.Line`,
    a row of `WORD_ROWS` its parts joined by commas in `.bl-details-words`,
    holding the line's head `.bl-details-head` and its parts with ` · `
    between two of them, each part (`DetailsPart`) with the dot after it
    in a `.bl-details-item`, the parts after a head in `.bl-details-parts`;
    a value whose lines are `trellis.Cells` is a
    table (`DetailsTable`). A value wraps and is never cut."""
    named = {**DETAILS_TERMS, **(terms or {})}
    with rv.Html(tag="div", class_="bl-details-rows"):
        for key, lines in rows:
            attributes = {"data-key": key}
            with rv.Html(tag="div", class_="bl-details-row", attributes=attributes).key(key):
                Term(named.get(key, key), sentence_case(key), "bl-details-key")
                with rv.Html(tag="div", class_="bl-details-value bl-code-small"):
                    # the lines of a table are its rows, drawn by DetailsTable
                    if lines and isinstance(lines[0], trellis.Cells):
                        DetailsTable(key, lines)
                        continue
                    if key in WORD_ROWS:
                        # the page's words, in Small, joined by commas
                        for number, line in enumerate(lines):
                            words = ", ".join(str(part) for part in line.parts)
                            rv.Html(
                                tag="div",
                                class_="bl-details-line bl-details-words",
                                children=[words],
                            ).key(f"{key} {number}")
                        continue
                    for number, line in enumerate(lines):
                        items = []
                        last = len(line.parts) - 1
                        for index, part in enumerate(line.parts):
                            if isinstance(part, str) and part in WORD_PARTS:
                                # a word of the page among the file's words
                                shown = rv.Html(
                                    tag="span", class_="bl-details-part bl-small", children=[part]
                                )
                            else:
                                shown = NamedPart(part, NAME_PARTS.get(key))
                            held = [shown] + ([PART_END] if index < last else [])
                            item = rv.Html(tag="span", class_="bl-details-item", children=held)
                            items += [item, " "] if index < last else [item]
                        children = items
                        if line.head:
                            # the parts after a head stand in one box, so that
                            # a wrapped line hangs under its first part
                            # (design pass 13 §4; D16)
                            head = head_children(line.head)
                            children = [
                                rv.Html(tag="span", class_="bl-details-head", children=head),
                                " ",
                                rv.Html(tag="span", class_="bl-details-parts", children=items),
                            ]
                        # a line's key names its row, since reacton allows
                        # each key once per component
                        rv.Html(tag="div", class_="bl-details-line", children=children).key(
                            f"{key} {number}"
                        )


def head_children(head: str) -> list:
    """The parts of a line's head as Details prints them (`DetailsRows`): a
    head whose first word is a word of the page (`WORD_HEADS`), `branch
    keep`, gives that word in Small, `.bl-small`, and the name after it in
    the value's Code small; any other head is its text alone (design pass
    13 §3; the fix wave Q3b, item 19, C8)."""
    word, space, rest = head.partition(" ")
    if word in WORD_HEADS and space:
        return [rv.Html(tag="span", class_="bl-small", children=[word]), f" {rest}"]
    return [head]


def DetailsTable(key: str, lines):
    """The value of the row `key` of Details whose lines are
    `trellis.Cells`, a join wire's joined fields (design pass §2, "A join
    wire"): the table `.bl-details-table`, one row `tr.bl-details-line` per
    line, one cell `td` per text."""
    body = [
        rv.Html(
            tag="tr",
            class_="bl-details-line",
            children=[rv.Html(tag="td", children=[cell]) for cell in line.cells],
        ).key(f"{key} {number}")
        for number, line in enumerate(lines)
    ]
    return rv.Html(
        tag="table", class_="bl-details-table", children=[rv.Html(tag="tbody", children=body)]
    )


def NamedPart(part, names: str | None):
    """The part `part` of a line of Details (`DetailsPart`) with the name it
    holds in `.bl-details-name`, which brand.css draws in ink-1 (design pass
    13 §5; E9): for `names` `whole` the whole part, for `first` the first
    word of a text part, and for None no name."""
    if names == "whole":
        return rv.Html(tag="span", class_="bl-details-name", children=[DetailsPart(part)])
    if names == "first" and isinstance(part, str):
        name, space, rest = part.partition(" ")
        children = [rv.Html(tag="span", class_="bl-details-name", children=[name])]
        if space:
            children.append(space + rest)
        return rv.Html(tag="span", class_="bl-details-part", children=children)
    return DetailsPart(part)


def DetailsPart(part):
    """One part of a line of Details: a `trellis.Link`, which opens a file
    of the model at a line (`DetailsLink`); a `trellis.Use`, which shows a
    recipe's trellis at an occurrence (`UsedRecipe`); or a text, the span
    `.bl-details-part`. A path's text breaks after a slash
    (`path_children`)."""
    if isinstance(part, trellis.Link):
        return DetailsLink(part)
    if isinstance(part, trellis.Use):
        return UsedRecipe(part)
    return rv.Html(tag="span", class_="bl-details-part", children=path_children(part))


@solara.component
def DetailsLink(link):
    """A link of a row of Details to a line of a file of the model, a
    `trellis.Link`, the span `.bl-link` with data-path and data-line; a
    click opens the file there, the view as it stands (`open_at`)."""
    item = rv.Html(
        tag="span",
        class_="bl-link",
        attributes={
            "data-path": link.path,
            "data-line": str(link.line),
            "title": f"open {link.path} at line {link.line}",
        },
        children=path_children(link.text),
    )
    rv.use_event(item, "click", lambda *_: open_at(link.path, link.line))
    return item


@solara.component
def UsedRecipe(use):
    """One recipe of the rows `periods` and `also` of Details, a
    `trellis.Use`: the span `.bl-used-recipe` with data-path, the recipe,
    and data-occurrence, the occurrence its link shows,
    `periods[3]/tenure`, its text the recipe's periods as ranges; a click
    shows that recipe's trellis there (`show_occurrence`)."""
    h, key = use.position
    address = f"periods[{h}]/{key}"
    item = rv.Html(
        tag="span",
        class_="bl-used-recipe",
        attributes={
            "data-path": use.source.path,
            "data-occurrence": address,
            "title": f"the trellis of {use.source.path} at {address}",
        },
        children=path_children(use.text),
    )
    rv.use_event(item, "click", lambda *_: show_occurrence(use.source, use.position))
    return item


@solara.component
def NodeItem(node_id: str, graph_id: str | None, active: bool):
    """One node named in a list of the panel; a click selects it in the
    view, in its graph where one is named."""
    item = rv.Html(
        tag="li",
        class_="bl-active" if active else "",
        attributes={"data-node": node_id, "data-graph": graph_id or ""},
        children=[node_id],
    )
    rv.use_event(item, "click", lambda *_: select_node(node_id, graph_id))
    return item


@solara.component
def LinkItem(link):
    """One link of the panel to a line of a file of the model, a
    `trellis.Link`; a click opens the file there, the view as it stands."""
    item = rv.Html(
        tag="li",
        class_="bl-link",
        attributes={
            "data-path": link.path,
            "data-line": str(link.line),
            "title": f"open {link.path} at line {link.line}",
        },
        children=[link.text],
    )
    rv.use_event(item, "click", lambda *_: open_at(link.path, link.line))
    return item


@solara.component
def NameItem(line: int, column: int, declared: bool):
    """One occurrence of the name under the cursor, `line:column`, followed
    by the word `declaration`, with its definition, where `declared`; a
    click moves the editor to its line and column."""
    item = rv.Html(
        tag="li",
        attributes={"data-line": str(line), "data-column": str(column)},
        children=[f"{line}:{column}", *(["  ", Term("declaration")] if declared else [])],
    )
    rv.use_event(item, "click", lambda *_: goto_line(line, column))
    return item


@solara.component
def NameView(report: model.NameReport, calibration):
    """The name under the cursor (specification §3.2, the reference view),
    under the label `name <name>`, its term carrying its definition: its
    occurrences in the file, the declaration's first, each a link to its
    line and column, the first occurrence on the declaration's line marked
    `declaration`; the line of the calibration that sets it, a link that
    reads `given at <file>, line <n>` and opens that file there; and, under
    the label `boxes depending on <name>`, each term carrying its
    definition, the boxes `name_report` lists, those that depend on the
    name as `TERMS["depends on"]` defines it, each a link that selects the
    box. The labels are a word or a few, not sentences (design pass §1 item
    8; unit K, Task 6)."""
    rv.Html(
        tag="div",
        class_="bl-block-label bl-name",
        children=[Term("name"), f" {report.name}"],
    )
    with rv.Html(tag="ul", class_="bl-name-occurrences bl-code-small"):
        for number, (line, column) in enumerate(report.occurrences):
            # the report lists the occurrences on the declaration's line first
            declared = number == 0 and line == report.declaration
            NameItem(line, column, declared).key(f"{line}:{column}")
    if calibration is not None:
        path, line = calibration
        with rv.Html(tag="ul", class_="bl-name-calibration bl-code-small"):
            LinkItem(trellis.Link(f"given at {path}, line {line}", path, line))
    if report.boxes:
        rv.Html(
            tag="div",
            class_="bl-block-label",
            children=[
                Term("box", "boxes"),
                " ",
                Term("depends on", "depending on"),
                f" {report.name}",
            ],
        )
        with rv.Html(tag="ul", class_="bl-name-boxes bl-code-small"):
            for node_id, graph_id in report.boxes:
                NodeItem(node_id, graph_id, False).key(f"{graph_id}:{node_id}")


@solara.component
def OccurrenceItem(address: str, graph_id: str):
    """One occurrence named in the panel of a period by its address,
    `periods[1]/cons`; a click selects the occurrence's layer in the view,
    in the graph `graph_id`, as `NodeItem` selects a node."""
    node_id = address + LAYER_ID_ENDING
    item = rv.Html(
        tag="li",
        attributes={"data-node": node_id, "data-graph": graph_id},
        children=[address],
    )
    rv.use_event(item, "click", lambda *_: select_node(node_id, graph_id))
    return item


def PanelHead(
    name,
    direction: str,
    place="",
    kind: str = "",
    under=None,
    code: bool = False,
    word: str = "",
):
    """The head of a piece's panel (design pass 8 §§5.1 and 6): its name, a
    string or a printed term, in Head; where one is given, the kind of the
    selection the name heads, `word`, a word of the page in sentence case,
    `Period`, `Builder` or `Sub-builder`, in Small in ink-3,
    `.bl-panel-word` (design pass 13 §3; the fix wave Q3b, item 19, C1,
    C12); where one is given, its place, `.bl-panel-place`, a stage
    occurrence's period and the period's age (design pass §2), in Code
    small, a text or its parts (`place_children`); where one is given, a
    box's kind, `.bl-panel-kind`, carrying the definition of `kind`, in Code
    small; its graph's direction in Small, in sentence case as the graph
    bar's select prints it, `Backward` (design pass 13 §3); and where
    `under` is given, the second line `.bl-panel-under` holding it in Code
    small, a box's identifier and the perches its builder joins (design pass
    §2, "An operator box"). With `code`, the name is an identifier, a
    stage's key, a period, a builder's namespace or a box's label, in Code
    name, `.bl-panel-name` (design pass 13 §3; C1)."""
    classes = "bl-panel-name bl-code-name" if code else ""
    children = [rv.Html(tag="span", class_=classes, children=[name])]
    if word:
        children += [" ", rv.Html(tag="span", class_="bl-panel-word", children=[word])]
    if place:
        held = place if isinstance(place, list) else [place]
        placed = rv.Html(tag="span", class_="bl-panel-place bl-code-small", children=held)
        children += [" ", placed]
    if kind:
        children += [" ", Term("kind", kind, "bl-panel-kind bl-code-small")]
    direction_word = Term(direction, sentence_case(direction))
    children.append(rv.Html(tag="span", class_="bl-panel-label", children=["  ", direction_word]))
    if under:
        children.append(
            rv.Html(tag="div", class_="bl-panel-under bl-code-small", children=list(under))
        )
    return rv.Html(tag="div", class_="bl-panel-head", children=children)


def place_children(place: str) -> list:
    """The parts of a stage occurrence's place as its head prints them
    (`PanelHead`): `periods[2] · age 68` gives the period and the number of
    the place in its Code small, and the page's word `age` between them in
    Small, `.bl-small` (design pass 13 §3; the fix wave Q3b, item 19, C8);
    a place with no age is the period alone. The text of the parts is the
    place's; no place gives no parts."""
    period, separator, age = place.partition(" · age ")
    if not separator:
        return [place] if place else []
    return [f"{period} · ", rv.Html(tag="span", class_="bl-small", children=["age"]), f" {age}"]


def DetailRow(key: str, children: list):
    """One row of Details in the form of spec 0.4 §5.5, `.bl-attribute`
    with data-key: its key `.bl-attribute-key`, the word in sentence case
    carrying the definition of the key without its number (`_term_of_key`;
    design pass 13 §3), and its
    value `.bl-attribute-value`, which holds `children` and takes the
    keyboard's focus (R-I82). A value wraps at word boundaries and is never
    cut (K-I29)."""
    return rv.Html(
        tag="div",
        class_="bl-attribute",
        attributes={"data-key": key},
        children=[
            Term(_term_of_key(key), sentence_case(key), "bl-attribute-key"),
            rv.Html(
                tag="div",
                class_="bl-attribute-value bl-code-small",
                attributes={"tabindex": "0"},
                children=children,
            ),
        ],
    ).key(key)


@solara.component
def AttributeRows(attributes: dict):
    """The rows of a node's attributes as the exporter writes them, each a
    `DetailRow` whose key carries its definition and whose value wraps and
    is never cut (spec 0.4 §5.5; K-I29)."""
    with rv.Html(tag="div", class_="bl-attributes"):
        for key, value in attributes.items():
            DetailRow(key, [str(value)])


# The key of the row of each side of a box's ports in its Details, which
# replace the ports table (design pass §2, "An operator box").
BOX_SIDES = {"inputs": "reads", "outputs": "writes"}
# The key of the row of each side of the ports of an occurrence's own
# `Inputs` and `Outputs`, and of a boundary marker of the trellis, where data
# enter or leave the drawn range (design pass 10 §6): the one port of a
# marker stands under `inputs` where its wire enters the graph and under
# `outputs` where it leaves.
BOUNDARY_SIDES = {"inputs": "inputs", "outputs": "outputs"}
# The attributes a port of the trellis view holds after its label, perch,
# type and role (`trellis.PORT_KEYS`), each printed after its term.
PORT_JOIN_KEYS = ("join", "paired by", "outside")


def PortItem(port: dict):
    """One port in Details, `.bl-port` (spec 0.4 §2.1): on its first line,
    a `.bl-attribute-line`, its label `.bl-port-label`, which carries the
    port's type in its hover; on its second, the parts the port holds, a
    dot after each but the last: its perch `.bl-port-perch` and its role
    `.bl-port-role`, each carrying the definition of its attribute, and in
    the trellis view its join, the rule that paired it and the occurrence
    outside the view, each after its term (`.bl-port-join`,
    `.bl-port-paired-by`, `.bl-port-outside`)."""
    label = rv.Html(
        tag="span",
        class_="bl-port-label",
        attributes={"title": port["type"]} if port.get("type") else {},
        children=[port["label"]],
    )
    parts = []
    for key in ("perch", "role"):
        if port.get(key):
            parts.append(
                rv.Html(
                    tag="span",
                    class_=f"bl-port-{key}",
                    attributes={"title": TERMS[key]},
                    children=[port[key]],
                )
            )
    for key in PORT_JOIN_KEYS:
        if port.get(key):
            value = rv.Html(
                tag="span", class_="bl-port-" + key.replace(" ", "-"), children=[port[key]]
            )
            parts.append(rv.Html(tag="span", children=[Term(key), " ", value]))
    last = len(parts) - 1
    items = []
    for index, part in enumerate(parts):
        held = [part] + ([PART_END] if index < last else [])
        items += [rv.Html(tag="span", class_="bl-details-item", children=held)]
        if index < last:
            items.append(" ")
    lines = [rv.Html(tag="div", class_="bl-attribute-line", children=[label])]
    if items:
        lines.append(rv.Html(tag="div", class_="bl-attribute-line", children=items))
    return rv.Html(tag="div", class_="bl-port", children=lines)


def PortRows(ports: dict, sides: dict) -> list:
    """The rows of the ports of a box or of a boundary node in Details:
    for each side of `ports`, `{"inputs": [row…], "outputs": [row…]}`,
    that holds a port, one `DetailRow` keyed by the word `sides` gives the
    side, holding one `PortItem` per port, in place of the four columns of
    a ports table (design pass §2, "An operator box")."""
    rows = []
    for side, word in sides.items():
        held = ports.get(side) or []
        if held:
            items = [PortItem(port).key(f"{side} {number}") for number, port in enumerate(held)]
            rows.append(DetailRow(word, items))
    return rows


@solara.component
def PieceButtons(piece: model.Piece, path: str | None = None):
    """The text buttons under a piece (design pass 8 §§5.3 and 6): `Card`,
    which copies its card, `Paper`, which writes the stage's paper files
    while `paper_offered` holds (`run_paper`), `Block`, which moves the
    editor to its block's header line, `Open in editor` where the setting
    names an editor, and `Item` for a refusal, which moves the editor to the
    refusal's line."""
    # the folder's entries, read so that the buttons are drawn again when
    # the folder is read again, as after `paper` writes its files (R-D41)
    tree.value
    with rv.Html(tag="div", class_="bl-piece-buttons"):
        if piece.card and piece.kind != "refusal":
            CopyButton(
                text=piece.card,
                label="Card",
                title=TERMS["card"].capitalize(),
                button_class="bl-card-button",
            )
        current = shown.value
        if paper_offered(current, _result_of(open_path.value)):
            name = f"{model.PAPER_FOLDER}/{current.stage.name}"
            TextButton(
                "Paper", run_paper, "bl-paper-button", f"Write {name}.md and {name}.svg"
            ).key("paper-button")
        if piece.block:
            # keyed, so that the panel's re-render after a cursor event keeps
            # the same element and a click that lands then is not lost
            TextButton(
                "Block",
                lambda: goto_block(piece.block),
                "bl-block-button",
                f"The header line of {piece.block}",
            ).key("block-button")
        file = path or (current.path if current is not None else None)
        line = model.header_line_of(piece.attributes)
        if line is None and current is not None and current.path == file and piece.block:
            span = current.spans.get(piece.block)
            line = span.line if span is not None else None
        if file is not None and line is not None and os.environ.get(desktop.EDITOR_VARIABLE):
            TextButton(
                "Open in editor",
                lambda: open_external_editor(file, line),
                "bl-open-in-editor",
            ).key("open-in-editor")
        if piece.kind == "refusal" and piece.attributes.get("line") is not None:
            line = int(piece.attributes["line"])
            column = int(piece.attributes.get("column") or 1)
            TextButton(
                "Item",
                lambda: goto_line(line, column),
                "bl-item-button",
                f"The refused item at line {line}",
            ).key("item-button")


@solara.component
def PieceView(piece: model.Piece, head: BoxHead | None = None, path: str | None = None):
    """One piece of the view in the panel, by its kind: a box's Details
    (`BoxDetails`), with `head`, its symbol and the perches its builder
    joins, and `path`, the file its lines open in the trellis view; a
    layer's rows, signature and buttons; the signature of the graph for its
    Inputs and Outputs nodes; a refused graph's position and rule with the
    button to the item, its message standing in the list under the error
    mark (`standing_refusals`; AMD-MI-002 §6a rule 1); the rows of a block
    or a field of an initial diagram. The card is not drawn, since the rows
    carry its content (AAS, 1 October 2026); a builder's layer adds, after
    its signature, the sections `Declared`, `Conditions` and `Method` its card
    holds (`model.builder_sections`; specification 0.6 §9)."""
    kind = piece.kind
    if kind == "box":
        BoxDetails(piece, head, path)
        return
    if kind == "boundary":
        PanelHead(Term("Inputs" if piece.node_id == "GraphInputs" else "Outputs"), piece.direction)
    elif kind == "layer":
        namespace = piece.node_id[: -len(LAYER_ID_ENDING)]
        # a layer of an initial diagram is a perch (design pass 14 §7, rule 6)
        if piece.direction in INITIAL_IDS.values():
            word = "Perch"
        else:
            word = "Builder" if "/" not in namespace else "Sub-builder"
        PanelHead(namespace, piece.direction, word=word, code=True)
    elif kind == "refusal":
        PanelHead(f"{piece.direction} builders graph refused", piece.direction)
    else:
        PanelHead(piece.node_id, piece.direction)
    if kind == "refusal":
        rows = {
            key: piece.attributes[key]
            for key in ("file", "line", "column", "address")
            if piece.attributes.get(key) is not None
        }
        if "file" in rows:
            rows["file"] = Path(str(rows["file"])).name
        if "address" in rows and _is_position(str(rows["address"]), piece.attributes.get("line")):
            del rows["address"]
        rows["rule"] = _rule_word(piece.attributes.get("rule"))
        AttributeRows(rows)
    else:
        # a builder whose card prints the section `Method` shows its binding
        # there, so that its row `method` is not printed twice (SE-9)
        headings = {heading for heading, _ in piece.sections}
        rows = (
            {key: value for key, value in piece.attributes.items() if key != "method"}
            if "Method" in headings
            else dict(piece.attributes)
        )
        # a declared builder's unmet requirements, one row after its row
        # `method` (SE-28)
        if piece.requires:
            rows["requires"] = ", ".join(piece.requires)
        AttributeRows(rows)
    if kind in ("layer", "boundary") and piece.signature:
        rv.Html(tag="div", class_="bl-block-label", children=[Term("signature", "Signature")])
        rv.Html(tag="pre", class_="bl-signature bl-code-small", children=[piece.signature])
    # a builder's sections `Declared`, `Conditions` and `Method`, as its card
    # holds them at the level shown, each a label over its rows as the
    # signature is drawn (specification 0.6 §9; the controller's third ruling
    # on design pass 15; SE-9)
    for heading, text in piece.sections:
        rv.Html(tag="div", class_="bl-block-label", children=[Term(heading.lower(), heading)])
        rv.Html(tag="pre", class_="bl-section bl-code-small", children=[text])
    PieceButtons(piece, path)


@dataclasses.dataclass(frozen=True)
class BoxHead:
    """What the head of a box's Details prints beside the box's kind and
    its graph (design pass §2, "An operator box"): `symbol`, the symbol the
    box prints, its label without the mark of a bound method; and
    `perches`, the pair of perches its block's builder joins, `("cntn",
    "dcsn")`, None for a builder that joins no pair, as the policy
    builder."""

    symbol: str
    perches: tuple | None = None


def box_head(stage, collection: dict, graph: str, node_id: str, piece: model.Piece) -> BoxHead:
    """The `BoxHead` of the box `node_id` of the graph `graph` of the view
    `collection`, whose piece is `piece` and whose stage is `stage`: its
    symbol, the label the view holds for its node (the package's
    `node_label`) without the mark ` · <tag>` with which that label ends
    where a method is bound, `<tag>` being the box's `method` row; and the
    pair of perches the builder of its block joins, read from
    `stage.builder` (`model._builder_blocks`)."""
    label = model._node(collection, graph, node_id).get("label") or piece.node_id
    method = piece.attributes.get("method")
    if method:
        label = label.removesuffix(f" · {method}")
    pairs = {block: pair for pair, block in model._builder_blocks(stage).items()}
    return BoxHead(label, pairs.get(piece.block))


def numbered_values(attributes: dict, word: str) -> list[str]:
    """The values of the attribute `word` of a node, or of `word 1`, `word
    2`, … where the package numbers several (`box_attributes`), in
    order."""
    return [str(value) for key, value in attributes.items() if _term_of_key(key) == word]


# The key of each row of a box's Details by the attribute the package
# writes on the box (`box_attributes`) whose value it prints, in the order
# the rows stand (design pass §2, "An operator box").
BOX_ROWS = {"policy": "at", "method": "method", "lines": "lines"}


def box_rows(attributes: dict) -> list[tuple[str, str]]:
    """The rows of a box's Details (design pass §2, "An operator box";
    spec 0.4 §5.5), each `(key, value)`, for each attribute of `BOX_ROWS`
    the box holds: `at`, the policies its row is held at, which the package
    names `policy`; `method`, the tag of the method bound within it; and
    `lines`. The kind stands in the head, and the rule and the kernel in
    blocks of their own (`MathBlock`), so that no row repeats a text a
    block prints. The bound method's handler and options, which the package
    reads from the card's `Method` and `Options` sections, stand in the
    card the button `card` copies, and the settings among the rows of the
    box's builder."""
    return [(BOX_ROWS[key], str(attributes[key])) for key in BOX_ROWS if attributes.get(key)]


# The places at which the display may break a line of a rule or a kernel:
# the space before an `=` that a space follows, and the space after a `;`
# (design pass §2, "An operator box": the package's texts wrapped at `=`
# and `;`, not rewritten).
MATH_BREAK = re.compile(r" (?== )|(?<=;) ")


def math_parts(line: str) -> list[str]:
    """The parts of one line of a rule or a kernel between the places at
    which the display may break it (`MATH_BREAK`); joined by one space, the
    parts are the line."""
    return MATH_BREAK.split(line)


def statement_text(text: str) -> str:
    """An authored line as the row `source` prints it: the statement
    without its annotation `:: [ … ]` and the spaces before it, the first
    `::` opening the annotation, as the package's cards divide a line
    (design pass §2: the annotations leave the source lines)."""
    return text.partition("::")[0].rstrip()


def MathBlock(word: str, lines: list[str], classes: str):
    """A rule or a kernel of a box's Details, printed once and whole
    (design pass §2, "An operator box"), in `.bl-math`: its label
    `.bl-math-label`, the term `word` carrying its definition, and the
    block `classes`, one `.bl-math-line` per line of the package's text,
    each part of the line (`math_parts`) a `.bl-math-part`, which moves to
    the next line whole where it fits on one. The parts are separated by a
    space and the lines by a line break, so that the block's text is the
    package's text."""
    body = []
    for number, line in enumerate(lines):
        parts = []
        for index, part in enumerate(math_parts(line)):
            parts += [" "] if index else []
            parts.append(rv.Html(tag="span", class_="bl-math-part", children=[part]))
        body += ["\n"] if number else []
        body.append(rv.Html(tag="div", class_="bl-math-line", children=parts))
    return rv.Html(
        tag="div",
        class_="bl-math",
        children=[
            rv.Html(tag="div", class_="bl-math-label", children=[Term(word, sentence_case(word))]),
            rv.Html(tag="div", class_=f"{classes} bl-code-small", children=body),
        ],
    )


@solara.component
def LineLink(
    text: str, line: int, path: str | None, classes: str, tag: str = "span", title: str = ""
):
    """A text of a box's Details that is a link to a line of the box's
    stage file, the element `tag` of `classes` with data-line: where `path`
    is None, in the stage view, a click moves the editor to the line
    (`goto_line`); otherwise, in the trellis view, it opens the
    occurrence's stage file `path` there (`open_at`), and the element
    carries data-path. Its hover is `title`, or what the click does."""
    attributes = {"data-line": str(line)}
    if path is None:
        attributes["title"] = title or f"move the editor to line {line}"
    else:
        attributes.update({"data-path": path, "title": title or f"open {path} at line {line}"})
    item = rv.Html(tag=tag, class_=classes, attributes=attributes, children=[text])

    def follow(*_):
        if path is None:
            goto_line(line, 1)
        else:
            open_at(path, line)

    rv.use_event(item, "click", follow)
    return item


def UsedItems(definitions: list, path: str | None) -> list:
    """The parts of the row `uses` of a box's Details: each definition the
    box's record names, `(name, identity, line)`, as its name and the line
    that declares it, `τ 8`, a link to that line (`LineLink`,
    `.bl-definition-link`), or as its name alone where no line declares it
    (`.bl-definition`), its identity in its hover; each part with the dot
    after it but the last in a `.bl-details-item`, separated by spaces."""
    last = len(definitions) - 1
    items = []
    for index, (name, identity, line) in enumerate(definitions):
        if line is None:
            part = rv.Html(
                tag="span", class_="bl-definition", attributes={"title": identity}, children=[name]
            )
        else:
            part = LineLink(f"{name} {line}", line, path, "bl-definition-link", title=identity)
        held = [part] + ([PART_END] if index < last else [])
        items.append(rv.Html(tag="span", class_="bl-details-item", children=held).key(identity))
        if index < last:
            items.append(" ")
    return items


def BoxDetails(piece: model.Piece, head: BoxHead | None, path: str | None):
    """Details of a selected box (design pass §2, "An operator box"; spec
    0.4 §5.5; unit K, Task 5): the head, its symbol (`head`, or its
    identifier where none is given), its kind and its graph, then its
    identifier with the perches its builder joins; the rows `at`, `method`
    and `lines` (`box_rows`), `lines` a link to its first line; the rule,
    a block; `reads` and `writes`, its ports
    (`PortRows`); the kernel, a block (`MathBlock`), each block printed
    once; `source`, the lines its card quotes, each without its
    annotation (`statement_text`) and a link to its line; `uses`, the
    definitions its record names (`UsedItems`); and the buttons
    (`PieceButtons`), all in `div.bl-box-details`. In the stage view a
    link moves the editor; in the trellis view it opens the occurrence's
    stage file `path`."""
    symbol, perches = (head.symbol, head.perches) if head is not None else (piece.node_id, None)
    under = [piece.node_id]
    if perches:
        # each sign carries its perch's word in its hover, `≻ continuation`
        source, target = (
            rv.Html(
                tag="span", attributes={"title": PERCH_TITLES[perch]}, children=[PERCH_SIGN[perch]]
            )
            for perch in perches
        )
        signs = rv.Html(tag="span", class_="bl-panel-perches", children=[source, " → ", target])
        under += ["  ", signs]
    kind = str(piece.attributes.get("kind") or "")
    # one element holds the card, since Solara lays out the several
    # top-level elements of a component as a column with gaps between them
    with rv.Html(tag="div", class_="bl-box-details"):
        PanelHead(symbol, piece.direction, kind=kind, under=under, code=True)
        first = model.header_line_of(piece.attributes)
        with rv.Html(tag="div", class_="bl-attributes"):
            for key, value in box_rows(piece.attributes):
                if key == "lines" and first is not None:
                    DetailRow(key, [LineLink(value, first, path, "bl-lines-link")])
                else:
                    DetailRow(key, [value])
        rules = numbered_values(piece.attributes, "rule")
        if rules:
            MathBlock("rule", rules, "bl-rule")
        if piece.ports.get("inputs") or piece.ports.get("outputs"):
            with rv.Html(tag="div", class_="bl-attributes"):
                PortRows(piece.ports, BOX_SIDES)
        if piece.kernel:
            MathBlock("kernel", piece.kernel.split("\n"), "bl-kernel")
        if piece.source_lines or piece.definitions:
            with rv.Html(tag="div", class_="bl-attributes"):
                if piece.source_lines:
                    lines = [
                        LineLink(
                            f"{number}  {statement_text(text)}",
                            number,
                            path,
                            "bl-source-line bl-attribute-line",
                            "div",
                        ).key(f"s{number}")
                        for number, text in piece.source_lines
                    ]
                    DetailRow("source", lines)
                if piece.definitions:
                    used = UsedItems(piece.definitions, path)
                    line = rv.Html(tag="div", class_="bl-attribute-line", children=used)
                    DetailRow("uses", [line])
        PieceButtons(piece, path)


# --- the view ---


# the word of each trellis verb applied, as the status line names the version
BOUND_WORDS = {"calibrate": "calibrated", "methodize": "methodized", "configure": "configured"}

# the words Details shows with nothing selected, in either view
# (specification §2.3 and §3.1; design pass 8 §§6 and 8, item 8)
NO_SELECTION = "No selection"


def trellis_status_parts(outcome, held) -> tuple[list, list]:
    """The status line of the trellis view as two lists of pairs of a text
    and the term it carries, None for plain text (specification §2.5 and
    §3.1; spec 0.4 §5.7; design pass §1 item 10 and §5 item 6; unit K,
    Task 6): the line, which the visible status line prints, and the rest,
    each of its parts after its separator, which follows the line where the
    whole fits in its box and stands in the details' line otherwise
    (`StatusRegion`). The line: the file; `trellis`, then `unsaved` where
    the reading took the text of a buffer that still differs from its file
    (`TrellisShown.buffered`, `unsaved_texts`), as the stage's status line
    marks a buffer (spec 0.4 §3.1), so that the mark leaves once that buffer
    is saved; then `refused` where the last reading was refused; the
    bindings applied, the verbs or `symbolic`, which stand at the head of
    the rest where the line with them does not fit
    (`narrow_status_parts`); the restriction, followed by the number of
    periods of the whole trellis, `of 51`, where the restriction names
    periods and no stage keys, and the occurrences the restriction shows;
    and the seconds of the loop, followed by the stages it bound alone,
    `for renter_cons`, where the reading bound those stages' occurrences
    and kept the others (`TrellisShown.alone`; unit L, Task 20). The rest:
    the periods and the occurrences;
    the unjoined fields of the forward graph, `3 unjoined fields`
    (`trellis.unjoined_count`; amendment 02, recommendation 17), counted by
    the rule by which the checklist lists them, so that the two give one
    number while the last reading answered `held` (unit L, Task 21; defect
    20 of the UX simulation); after a refused reading the checklist lists
    no field and the line counts those of the dimmed trellis; and the
    occurrences the last reading constructed or bound anew. Before a
    trellis stands, the line is the file and `refused`, or `reading`, and
    there is no rest."""
    name = source.value.path if source.value is not None else ""
    refused = outcome is not None and outcome.refusal is not None
    if held is None:
        return [
            (name, None),
            (" · ", None),
            ("refused", "refused") if refused else ("reading", None),
        ], []
    line = [(held.source.path, None), (" · ", None), ("trellis", "trellis")]
    if set(held.buffered) & set(unsaved_texts()):
        line += [(" · ", None), ("unsaved", "unsaved")]
    if refused:
        line += [(" · ", None), ("refused", "refused")]
    words = [BOUND_WORDS[verb] for verb in held.binding.bound]
    line += [(" · ", None), (", ".join(words), "bound") if words else ("symbolic", "symbolic")]
    counts = held.counts
    if held.restriction is not None:
        line += [(" · shown ", None), (held.restriction.text, "restriction")]
        # a number written after stage keys would read as a count of stages
        if held.restriction.periods is not None and held.restriction.stages is None:
            line += [(f" of {counts['periods']}", None)]
        line += [(f" ({counts['shown']} occurrences)", None)]
    line += [(" · ", None), ("loop", "loop"), (f" {held.seconds:.2f} s", None)]
    if held.alone:
        line += [(f" for {', '.join(held.alone)}", None)]
    rest = [(f" · {counts['periods']} periods, {counts['occurrences']} ", None)]
    rest += [("occurrences", "occurrence")]
    # the unjoined fields of the forward graph (amendment 02, recommendation
    # 17; J-D39), which a removal leaves and a drag joins, by the checklist's
    # rule (K-I180; unit L, Task 21)
    unjoined = trellis.unjoined_count(held)
    rest += [(f" · {unjoined} unjoined field" + ("" if unjoined == 1 else "s"), None)]
    if held.changed:
        rest += [(f" · {len(held.changed)} occurrences elaborated or bound again", None)]
    return line, rest


# the terms of the parts of the trellis's line that name the bindings
# applied (`trellis_status_parts`)
BINDING_TERMS = ("bound", "symbolic")


def narrow_status_parts(line: list, rest: list) -> tuple[list, list]:
    """The trellis's line and its rest (`trellis_status_parts`) where the
    line with the bindings applied does not fit in its box: the line without
    the bindings applied and their separator, and the rest with them at its
    head (spec 0.4 §5.7; unit K, Task 6). A line that names no bindings,
    before a trellis stands, is answered as it is."""
    at = next((index for index, (_, term) in enumerate(line) if term in BINDING_TERMS), None)
    if at is None:
        return line, rest
    return line[: at - 1] + line[at + 1 :], line[at - 1 : at + 1] + rest


# the number of the texts the browser measures (`StatusFit`) that fit in
# the width the visible status line leaves the trellis's line, as the
# browser last measured it: 2, the whole line, its rest included; 1, the
# line with the bindings applied, its rest standing in the details' line;
# 0, neither, the bindings applied standing at the head of the rest in the
# details' line (`narrow_status_parts`); 0 before a measure (spec 0.4 §5.7;
# design pass §1 item 10; unit K, Task 6)
status_fit = solara.reactive(0)


def on_status_fit(count) -> None:
    """Records the browser's measure of the trellis's status line
    (`StatusFit`)."""
    status_fit.value = int(count)


@solara.component
def StatusParts(parts: list, class_: str = ""):
    """Parts of the status line, each a text or a term carrying its
    definition (`trellis_status_parts`), in one span of the class
    `class_`, since Solara lays out the several top-level elements of a
    component as a column. A text that begins with the separator
    `STATUS_SEPARATOR` begins a new part of the line: its separator is kept
    in the line's text and not drawn (`status_dot`), and the texts and terms
    up to the next separator stand together in `span.bl-status-part`, the
    parts 16 px apart (design pass 8 §6). The paths among them, the file of
    the trellis's line, are set in Code small."""
    groups: list[list] = [[]]
    for index, (text, word) in enumerate(parts):
        if word is None and text.startswith(STATUS_SEPARATOR):
            groups.append([("dot", STATUS_SEPARATOR, index)])
            text = text[len(STATUS_SEPARATOR) :]
            groups.append([])
            if not text:
                continue
        groups[-1].append(("text" if word is None else "term", (text, word), index))
    with rv.Html(tag="span", class_=class_):
        for number, group in enumerate(groups):
            if not group:
                continue
            if group[0][0] == "dot":
                status_dot().key(f"dot {number}")
                continue
            with rv.Html(tag="span", class_="bl-status-part").key(f"part {number}"):
                for kind, (text, word), index in group:
                    if kind == "term":
                        Term(word, text).key(str(index))
                    elif number == 0 and index == 0:
                        # the trellis's file, the line's first text
                        rv.Html(tag="span", class_="bl-code-small", children=[text]).key(
                            str(index)
                        )
                    else:
                        rv.Html(tag="span", children=[text]).key(str(index))


@solara.component
def TrellisStatus(line: list, rest: list, fits: bool):
    """The status line of the trellis view in `span.bl-trellis-status`: the
    parts of `line`; where the whole fits, `fits`, the parts of `rest` in
    `span.bl-trellis-rest`, which the details' line holds otherwise
    (`trellis_status_parts`, `narrow_status_parts`, `StatusRegion`); each
    term carrying its definition; then the line the last gesture of the
    trellis graph wrote (`GestureNote`; brief rule 7). It is printed once,
    in the visible line (`StatusRegion`)."""
    with rv.Html(tag="span", class_="bl-trellis-status"):
        StatusParts(line).key("line")
        if rest and fits:
            StatusParts(rest, "bl-trellis-rest").key("rest")
        GestureNote().key("gesture")


# the hovers of the view tab `Stage` (unit K, K-D20; design pass 2 §4;
# design pass 8 §8, item 1): while the editor holds a stage file, and while
# it holds none
STAGE_SEGMENT_HOVER = "The graph of the stage file open in the editor"
NO_STAGE_FILE_HOVER = "No stage file open"
# the hover of the view tab `Trellis`, the term's definition with a capital
TRELLIS_TAB_HOVER = "The model over its periods, each a frame of its stage occurrences"


def ViewTab(word: str, classes: str, attributes: dict, act, acts: bool):
    """One view tab of the graph's bar (design pass 8 §§4 and 6), a header
    of VSCode Elements' tabs, `<vscode-tab-header>`, with the classes
    `classes`, the attributes `attributes` and its word `word`. A click, or
    Enter, calls `act` where `acts` holds and nothing otherwise; either is
    stopped at the header, so that the library's tabs do not select a tab
    themselves and the tab selected is always the one Python names."""
    header = rv.Html(
        tag="vscode-tab-header",
        class_=classes,
        attributes={"slot": "header", **attributes},
        children=[word],
    )
    rv.use_event(header, "click.stop", lambda *_: act() if acts else None)
    rv.use_event(header, "keydown.enter.stop", lambda *_: act() if acts else None)
    return header


@solara.component
def ViewSwitch(composed: bool, stage_open: bool, in_trellis: bool):
    """The view tabs `Stage` and `Trellis` of the graph's bar (spec 0.4
    §2.1, G-D16; R-D56; unit K, K-D20; design pass 8 §§4 and 6),
    VSCode Elements' tabs, `<vscode-tabs>` `.bl-view-switch`, the tab of
    the graph shown selected and `.bl-active`, the trellis's where
    `in_trellis`, each tab's choice also its `aria-pressed`. `Stage`,
    `.bl-stage-button`, shows the view of the stage file open in the editor
    (`choose_stage`); while the editor holds no stage file, `stage_open`
    false, it carries `aria-disabled`, which keeps its hover `No stage file
    open`, and does not act. `Trellis`, `.bl-trellis-button`, shows the
    trellis view (`choose_trellis`) and, without a composition, `composed`,
    carries `aria-disabled` and does not act. The tabs hold no panel of
    their own, since the canvas under them shows the graph chosen."""
    stage = ViewTab(
        "Stage",
        "bl-stage-button" + ("" if in_trellis else " bl-active"),
        {
            "title": STAGE_SEGMENT_HOVER if stage_open else NO_STAGE_FILE_HOVER,
            "aria-pressed": "false" if in_trellis else "true",
            "aria-disabled": "false" if stage_open else "true",
        },
        choose_stage,
        True,
    )
    trellis_tab = ViewTab(
        "Trellis",
        "bl-trellis-button" + (" bl-active" if in_trellis else ""),
        {
            "title": TRELLIS_TAB_HOVER,
            "aria-pressed": "true" if in_trellis else "false",
            "aria-disabled": "false" if composed else "true",
        },
        choose_trellis,
        composed,
    )
    return rv.Html(
        tag="vscode-tabs",
        class_="bl-view-switch",
        attributes={
            "selected-index": "1" if in_trellis else "0",
            "aria-label": "Graph shown",
        },
        children=[stage.key("stage"), trellis_tab.key("trellis")],
    )


@solara.component_vue("restriction.vue")
def RestrictionSelect(
    text: str = "all",
    refused: bool = False,
    title: str = "",
    ranges: list = [],
    stages: list = [],
    typed: str = "",
    event_chosen=None,
):
    """The select of the view's bar that restricts the trellis view, with its
    menu (unit K, K-D17 and K-D18; design pass 2 §3); see restriction.vue."""


@solara.component
def ViewRestriction():
    """The select of the view's bar that restricts the trellis view (spec 0.4
    §2.6; unit K, K-D17 and K-D18; design pass 2 §3), in the face and the
    size of the bar's other items, with no label of its own. It prints the
    restriction as written, `restriction_text`, `periods 0–2` or `periods
    0–1, stages cons`, R-D55's word `periods` first where the text names
    periods, and `all` for the whole trellis; its hover is the term's
    gloss. Its menu lists the ranges from the terminal period and `all`,
    then the trellis's stage keys as checks (`trellis.restriction_menu`),
    and at its foot a field that holds the restriction as written, for any
    text of the grammar. Every choice, and Enter in the field, calls
    `apply_restriction` with its text, as the field of R-D55 did, so that
    the history (R-D57, R-D59) and the links that write `periods h` stand.
    The select is drawn in the refusal's color while the parser's refusal
    of the text or the package's refusal of the selection stands
    (`_restriction_refused`), whose sentence stands in the list under the
    error mark (AMD-MI-002 §6a rule 1). The text typed at the foot is held
    by the browser until Enter, so that a render of the page, which sends
    the same `typed`, leaves it as it is."""
    held = trellis_shown.value
    ranges, stages = trellis.restriction_menu(
        restriction.value, held.syntactic if held is not None else None
    )
    return RestrictionSelect(
        text=restriction_text.value or "all",
        refused=_restriction_refused() is not None,
        title=TERMS["restriction"],
        ranges=[choice._asdict() for choice in ranges],
        stages=[choice._asdict() for choice in stages],
        typed=restriction_text.value,
        event_chosen=apply_restriction,
    )


@solara.component
def TrellisRefusal(refusal: model.Diagnostic):
    """The mark of the trellis's refused reading: `refused`, the file and
    the address or the position it names and its rule, in a box drawn in
    the refusal's color, and, where the place stands at a line of a file
    of the model (`_trellis_refusal_place`), the button `Open at the
    address`, which opens the file there (specification §2.2 rule 2,
    D11), a text button (design pass 8 §§5.3 and 6); its sentence stands
    in the list under the error mark (AMD-MI-002 §6a rule 1)."""
    path, line = _trellis_refusal_place(refusal)
    name = recipe.relative(tab_folder.value, refusal.file) if refusal.file else ""
    where = ", ".join(part for part in (name, refusal.address or "") if part)
    head_parts = [Term("refused"), f" in {where}" if where else ""]
    rule = _rule_word(refusal.rule)
    if rule:
        head_parts += [" · ", Term("rule"), f" {rule}"]
    with rv.Html(tag="div", class_="bl-refusal bl-trellis-refusal bl-code-small"):
        rv.Html(tag="div", class_="bl-refusal-rule", children=head_parts)
        if line is not None:
            TextButton(
                "Open at the address",
                lambda: open_at(path, line),
                "bl-address-button",
                f"{path}, line {line}",
            )


@solara.component
def OccurrenceDetails(subject):
    """In Details, the stage occurrence selected in the trellis view (design
    pass §2, "A stage occurrence"; unit K, K-D2), in
    `div.bl-occurrence-details`: the head, the stage's key, its period with
    the period's age, and the graph's direction word (`PanelHead`); the
    rows `trellis.occurrence_rows` answers (`DetailsRows`), with the
    refusal of the trellis's last reading and the folder's recipes; and
    the text buttons (design pass 8 §§5.3 and 6) `Head`, which makes it the
    head, which the main bar's path names, and `Open the stage`, which opens
    its stage file bound as it, as a double click on its layer in the view
    does (`on_opened`). The two controls of its removal, `Remove from
    periods` and `Remove stage`, text buttons with the Codicon `trash`,
    stand last in Details, after the fold `Legend`, which `TrellisPanel`
    places (`RemovalButtons`; unit N, Task 5; design pass 10 §7; design
    pass 13 §5, Q-D15; the fix wave Q3b, item 17, D24). The head prints
    the period's word `age` in Small among the place's Code small (design
    pass 13 §3; the fix wave Q3b, item 19, C8). The rows
    are read again when the occurrence, the trellis held, the folder's
    recipes or that refusal change."""
    held = trellis_shown.value
    outcome = trellis_outcome.value
    refusal = outcome.refusal if outcome is not None else None
    recipes = sources.value
    details = solara.use_memo(
        lambda: trellis.occurrence_rows(
            tab_folder.value,
            held,
            subject.graph,
            subject.position,
            recipes,
            refusal,
            trellis.texts_of(unsaved_texts()),
        ),
        [subject, held, recipes, refusal],
    )
    with rv.Html(tag="div", class_="bl-occurrence-details"):
        PanelHead(details.key, subject.graph, place_children(details.place), code=True)
        DetailsRows(details.rows)
        with rv.Html(tag="div", class_="bl-piece-buttons"):
            TextButton(
                "Head",
                lambda: set_head(subject.position),
                "bl-occurrence-head",
                "Make this occurrence the head",
            ).key("head")
            TextButton(
                "Open the stage",
                lambda: open_occurrence(subject.position),
                "bl-occurrence-open",
                "Open its stage file, bound as this occurrence",
            ).key("open")


@solara.component
def TrellisSubject(subject, links: list):
    """One node of the trellis view in the panel, by its kind (specification
    §2.4 and §3.1): a period's rows and the occurrences of it the view
    holds, each named by its address and a link that selects it, for
    the terminal period what a period typed first would move
    (`MovedRanges`; spec 0.4 §3.6), and, for a trellis of more than one
    period read from a recipe, the text button `Remove period`,
    `.bl-period-remove`, which removes it (`remove_period`; unit L, Task
    25); an
    occurrence's rows and buttons (`OccurrenceDetails`); a box
    or a builder of an occurrence as a stage's panel shows it (`PieceView`),
    a box's ports with their joins, its lines, source lines and
    definitions each a link to its line in the occurrence's stage file,
    then the text button `Open at the block`; the inputs and the outputs of the
    trellis or of an occurrence, their ports with their joins
    (`PortRows`); and the refusing node's head with each
    unpaired join's links to the header that declares a wire and to the
    connector, its sentence, the row `refusal`, standing in the list under
    the error mark (AMD-MI-002 §6a rule 1)."""
    kind = subject.kind
    if kind == "period":
        PanelHead(subject.occurrence, subject.graph, word="Period", code=True)
        AttributeRows(subject.rows)
        rv.Html(tag="div", class_="bl-block-label", children=[Term("occurrence", "Occurrences")])
        with rv.Html(tag="ul", class_="bl-occurrences bl-code-small"):
            for address, _ in subject.occurrences:
                OccurrenceItem(address, subject.graph).key(address)
        if subject.occurrence == "periods[0]":
            MovedRanges()
        held = trellis_shown.value
        found = _PERIOD_WORD.fullmatch(subject.occurrence or "")
        if (
            found is not None
            and held is not None
            and held.source.kind == "recipe"
            and len(held.trellis["periods"]) > 1
        ):
            h = int(found[1])
            with rv.Html(tag="div", class_="bl-piece-buttons"):
                TextButton(
                    REMOVE_PERIOD,
                    lambda: remove_period(h),
                    "bl-period-remove",
                    f"Remove {subject.occurrence} from the trellis",
                )
    elif kind == "occurrence":
        OccurrenceDetails(subject)
    elif kind == "piece":
        # the block button and the line links of a stage's panel move the
        # editor within the file open in it, which in the trellis view need
        # not be the occurrence's; here `open at the block` and each line
        # link open the occurrence's own file
        piece, held = subject.piece, trellis_shown.value
        head = None
        if piece.kind == "box":
            h, key = subject.position
            stage = held.trellis["periods"][h]["stages"][key]
            head = box_head(stage, held.collection, subject.graph, subject.node_id, piece)
        path = trellis.occurrence_file(tab_folder.value, held, subject.position)
        PieceView(piece._replace(block=""), head, path)
        if piece.block:
            TextButton(
                "Open at the block",
                lambda: open_occurrence(subject.position, piece.block),
                "bl-occurrence-block",
                f"The header of {piece.block} in the occurrence's stage file",
            ).key("block")
    elif kind in ("inputs", "outputs"):
        # a boundary marker of the trellis, which stands in no occurrence,
        # is headed by its label, `starting data μ≺` (design pass 10 §6)
        label = subject.rows.get("label") if not subject.occurrence else None
        PanelHead(label or Term("Inputs" if kind == "inputs" else "Outputs"), subject.graph)
        with rv.Html(tag="div", class_="bl-attributes"):
            PortRows(subject.ports, BOUNDARY_SIDES)
    else:
        PanelHead(f"{subject.graph} trellis graph refused", subject.graph)
        AttributeRows(
            {
                key: value
                for key, value in subject.rows.items()
                if not key.startswith("join") and key != "refusal"
            }
        )
        for number, join in enumerate(links, 1):
            with rv.Html(tag="div", class_="bl-unpaired bl-code-small").key(str(number)):
                rv.Html(
                    tag="div",
                    children=[
                        Term("join"),
                        f" {number}: {join.label}, from {join.source} to {join.target}",
                    ],
                )
                with rv.Html(tag="ul", class_="bl-links bl-code-small"):
                    # a link's key names its join, since reacton allows each
                    # key once per component and joins at several periods
                    # link to one line with one text
                    for link in join.links:
                        LinkItem(link).key(f"{number} {link.text}:{link.line}")


# The term whose definition a row's key of a join wire's Details carries,
# where it is not the key itself: in that card `periods`, `fields` and
# `also` name the periods the join's entry reaches, the fields it joins and
# the other occurrences its entry joins to the same reader (design pass §2).
JOIN_TERMS = {"periods": "join periods", "fields": "joined fields", "also": "same entry"}


# the label of the button of Details that renames the reading field of a
# join by equal names (unit L, Task 15; design pass 8 §8, item 1)
RENAME = "Rename"


@solara.component
def JoinRename(names: tuple, file: str):
    """Under the rows of Details for a join wire some of whose joins are
    made by equal names (unit L, Task 15; defect 3 of the UX simulation),
    in `div.bl-join-rename`, the fields of the forms (design pass 8 §§4 and
    6): the select `Field`, `.bl-join-rename-field`, of the arrival fields
    those joins reach (`trellis.JoinRows.names`), the first chosen at
    first; the text field `New name`, `.bl-join-rename-name`; and the
    secondary button `Rename`, `.bl-join-rename-button`, its hover `Rename
    <field> in <file>`, `file` the reading stage's file, which waits while
    the name typed, read without the spaces around it, is empty or the
    field's own, and otherwise renames the field in that file
    (`rename_join`). The caller keys the component by the wire, so that
    another wire selected begins with its first field and no name."""
    field, set_field = solara.use_state(names[0])
    typed, set_typed = solara.use_state("")
    chosen = field if field in names else names[0]
    name = typed.strip()
    waits = None
    if not name:
        waits = "Type a new name"
    elif name == chosen:
        waits = "Type a name other than the field's"
    with rv.Html(tag="div", class_="bl-join-rename"):
        Field(
            kind="select",
            value=chosen,
            options=list(names),
            label="Field",
            classes="bl-join-rename-field",
            event_entered=set_field,
        )
        Field(
            value=typed,
            label="New name",
            classes="bl-join-rename-name",
            event_entered=set_typed,
        )
        CommandButton(
            RENAME,
            lambda: rename_join(chosen, name),
            "bl-join-rename-button",
            f"Rename {chosen} in {file}",
            waits,
            secondary=True,
        )


@solara.component
def JoinDetails(join: dict):
    """In Details, the join wire selected in the forward trellis graph, or
    the cable selected in the backward graph (design pass §2, "A join wire";
    design pass 10 §8; unit K, K-D2; unit J's decision J-D39),
    or the pair of periods whose shared piece is selected (K-D5), in
    `div.bl-join-details`: the head, the word `Join` in sentence case (the
    fix wave Q3b of unit Q, item 19; C12), its writing stage
    occurrence, or the pair's writing period, and its reading stage
    occurrence by their addresses and the graph's direction word
    (`PanelHead`); the rows `trellis.join_rows` answers
    (`DetailsRows`), `written`, `pairs` or `periods`, `measure`, `fields`,
    a table, and `also`, read through the tab's unsaved texts; where joins
    of the wire are made by equal names, the rename of their reading field
    in the reading stage's file (`JoinRename`; unit L, Task 15); and, where
    an entry of a file writes a join of the wire, the text button `Remove`,
    its hover `Remove the join from <file>`, which removes it (`remove_join`;
    J-D33), a wire whose joins are all by equal names having none. A wire
    the trellis held no longer holds, whose selection the new reading ends,
    prints nothing."""
    held = trellis_shown.value

    def rows():
        if held is None:
            return None
        try:
            texts = trellis.texts_of(unsaved_texts())
            return trellis.join_rows(tab_folder.value, held, join, texts)
        except KeyError:
            return None

    details = solara.use_memo(rows, [join, held])
    if details is None:
        return
    with rv.Html(tag="div", class_="bl-join-details"):
        PanelHead(Term("join", "Join"), join.get("graph") or "forward", details.place)
        DetailsRows(details.rows, JOIN_TERMS)
        if details.names:
            reader = (join["reading"]["h"], join["reading"]["key"])
            file = Path(trellis.occurrence_file(tab_folder.value, held, reader)).name
            JoinRename(details.names, file).key(" ".join(str(join[key]) for key in JOIN_IDS))
        if details.removable:
            TextButton(
                REMOVE,
                remove_join,
                "bl-join-remove",
                f"Remove the join from {join['file']}",
            )


@solara.component
def TrellisPanel(legend: solara.Element | None = None):
    """Details in the trellis view (spec 0.4 §5.5), `.bl-panel`, under its
    head (`DetailsHead`; AAS, L-D12), whose context is the selected node's
    name and position (`details_context`), none while a join wire is: the
    mark of the last reading's refusal (`TrellisRefusal`), whose sentence,
    as each sentence of the verbs the package refused in the binding,
    stands in the list under the error mark (AMD-MI-002 §6a rule 1); and
    the selected node (`TrellisSubject`), the sentence of a node the
    view does not hold, or, with nothing selected while the view shows a
    graph of the trellis, `No selection` (specification §2.3 and
    §3.1); while a join wire is selected in the forward graph, or a cable in
    the backward graph, that join (`JoinDetails`; J-D39; design pass 10 §8).
    `legend` stands as in `Panel`, under
    `LegendDetails` at the body's end whether or not a node or a join wire
    is selected (design pass §2; K-D2), and, for a selected stage
    occurrence, the two controls of its removal after it, last in the panel
    (`RemovalButtons`; design pass 13 §5; the fix wave Q3b, item 17,
    D24)."""
    outcome, held = trellis_outcome.value, trellis_shown.value
    selection = selected.value
    views = solara.use_memo(dict, [held])
    subject = solara.use_memo(lambda: describe_trellis(selection, held, views), [selection, held])
    links = solara.use_memo(
        lambda: trellis.refusal_links(
            tab_folder.value, held, subject.graph, trellis.texts_of(unsaved_texts())
        )
        if held is not None and isinstance(subject, trellis.Subject) and subject.kind == "refusal"
        else [],
        [subject, held],
    )
    # the join wire selected in the forward graph, or the cable selected in
    # the backward graph, which Details shows in place of a node (J-D39;
    # design pass 10 §8)
    join_shown = chosen_join.value is not None and graph.value in ("forward", "backward")
    context = details_context(
        held.collection if held is not None else None, None if join_shown else selection
    )
    with rv.Html(tag="section", class_=details_class(), attributes={"aria-label": "details"}):
        DetailsHead(context)
        with rv.Html(tag="div", class_="bl-panel-body"):
            if outcome is not None and outcome.refusal is not None:
                TrellisRefusal(outcome.refusal)
            if held is not None and held.view_refusal is not None:
                rv.Html(tag="div", class_="bl-empty", children=["Graph unavailable. See Problems."])
                TrellisRefusal(held.view_refusal)
            elif join_shown:
                JoinDetails(chosen_join.value["join"])
            elif subject is None:
                # the trellis view shows its two builders graphs and, since
                # design pass 14 §7, its two initial diagrams
                if graph.value in ("backward", "forward", *INITIAL_IDS.values()):
                    rv.Html(tag="div", class_="bl-empty", children=[NO_SELECTION])
            elif isinstance(subject, str):
                rv.Html(tag="div", class_="bl-empty", children=[subject])
            else:
                TrellisSubject(subject, links)
            if legend is not None:
                LegendDetails(legend)
            # a destructive act stands last in its panel, after the legend
            # (design pass 13 §5; D24)
            shows_occurrence = (
                not (held is not None and held.view_refusal is not None)
                and not join_shown
                and isinstance(subject, trellis.Subject)
                and subject.kind == "occurrence"
            )
            if shows_occurrence:
                RemovalButtons(tuple(subject.position)).key("removal")


@dataclasses.dataclass(frozen=True)
class LegendEntry:
    """One entry of the legend under the graph: `text`, what the entry names
    as the legend prints it, a level, a bound method's tag and place, a
    mark, a perch or a role with its fields; `swatch`, the level, box or
    perch key that brand.css colors, None for an entry with no swatch;
    and `sentence`, the words printed after a mark (`MARK_WORDS`), the empty
    text for every other entry."""

    text: str
    swatch: str | None = None
    sentence: str = ""


# The groups of the legend, by the key under which `legend_entries` answers
# each, with the title the legend prints before it, in the order it draws
# them (AMD-MI-001, decisions A1-D2 and A1-D4).
LEGEND_GROUPS = {
    "levels": "levels",
    "methods": "bound methods",
    "marks": "marks",
    "perches": "perch overlays",
    "roles": "roles",
}
# The word the legend prints for each level whose layer colors
# `LAYER_COLORS` gives; the layers of an initial diagram are its perches.
LEVEL_WORDS = {
    "period": "period",
    "stage": "stage occurrence",
    "builder": "builder",
    "sub-builder": "sub-builder",
}
# The words for each box kind and for an initial diagram's perch layers.
BOX_WORDS = {
    "operator": "primitive operator",
    "output": "builder's output",
    "field": "field",
    "block": "block",
    "perch": "perch",
}
# the words the legend prints after each mark a drawn label may hold (AAS,
# 4 October 2026: a label is a word or a few)
MARK_WORDS = {
    "method": "bound method",
    "policy": "at a policy",
    "law": "law of motion",
}
# The letter in which the drawing writes a law of motion: the name a
# pullback or a push-forward gives the law it reads begins with it, `𝑔≻`,
# `𝑔_keep≻`, and a pullback along coordinate functions, `𝑐 ∘ 𝑚_d≻`, names
# none.
LAW_LETTER = "𝑔"


def _attribute(node: dict, key: str) -> str:
    """The value of the attribute `key` of a node of the view, the empty
    text where the node has none."""
    return next((item["value"] for item in node.get("attrs") or [] if item["key"] == key), "")


def _layer_namespaces(nodes: list) -> list[str]:
    """The namespaces of the layers a graph draws, each once, in the order
    of its nodes: every leading part of a node's namespace, `policy` and
    `policy/endoggrid` for the namespace `policy/endoggrid`."""
    found = {}
    for node in nodes:
        parts = (node.get("namespace") or "").split("/")
        if parts[0]:
            for depth in range(1, len(parts) + 1):
                found.setdefault("/".join(parts[:depth]), None)
    return list(found)


def _layer_colors(configs: list, namespace: str) -> tuple:
    """The fill, the border and the label of the layer `namespace` as the
    viewer's page colors it from the graph's layer configurations
    `configs`: each from the first configuration whose pattern matches the
    namespace and that sets it, None where none does."""
    return tuple(
        next(
            (
                config[key]
                for config in configs
                if config.get(key) and re.search(config["namespaceRegex"], namespace)
            ),
            None,
        )
        for key in ("backgroundColor", "borderColor", "textColor")
    )


def _legend_levels(graph: dict, initial: bool) -> list[LegendEntry]:
    """The levels a graph draws, with the swatch keys brand.css colors
    (specification §§2.1 and 5.3). A builders graph's layers are named by
    the level whose colors `LAYER_COLORS` gives them, in that order:
    period, stage, builder, sub-builder; then operator (`NODE_STYLE`) and
    output (`OUTPUT_STYLE`). An initial diagram's layers are its perches,
    and its nodes its fields and its blocks."""
    nodes = graph.get("nodes") or []
    configs = graph.get("groupNodeConfigs") or []
    drawn = set()
    for namespace in _layer_namespaces(nodes):
        colors = _layer_colors(configs, namespace)
        level = (
            "perch"
            if initial
            else next((key for key, held in LAYER_COLORS.items() if tuple(held) == colors), None)
        )
        if level is not None:
            drawn.add(level)
    styles = {"operator": NODE_STYLE, "output": OUTPUT_STYLE}
    styles = {key: dataclasses.asdict(style) for key, style in styles.items()}
    for node in nodes:
        kind, style = _attribute(node, "kind"), node.get("style") or {}
        if initial:
            key = kind if kind in ("field", "block") else None
        elif style == styles["output"]:
            key = "output"
        elif kind and style == styles["operator"]:
            key = "operator"
        else:
            key = None
        if key is not None:
            drawn.add(key)
    order = ["perch", "field", "block"] if initial else [*LAYER_COLORS, "operator", "output"]
    return [
        LegendEntry(LEVEL_WORDS.get(key) or BOX_WORDS[key], key) for key in order if key in drawn
    ]


def _legend_methods(collection: dict, graph_id: str, graph: dict) -> list[LegendEntry]:
    """Each bound method of a graph as its tag and its place, two spaces
    between them, `!egm  policy:Evaluation`, read from the `method` rows of
    the graph's layers and nodes in the order of its nodes, a layer before
    the nodes inside it. A place is the namespace of a layer or the id of a
    node. In a trellis it is written with the key of the stage it stands in
    and without its period, `cons/policy:Evaluation`, the occurrence read
    from the namespace the collection holds (`node_place`), so that a place
    every period holds is listed once and the places of two stages read
    apart."""
    layers = graph.get("groupNodeAttributes") or {}
    occurrences = {}

    def place(name: str, namespace: str) -> str:
        if namespace not in occurrences:
            held = node_place(collection, graph_id, namespace + LAYER_ID_ENDING)
            occurrences[namespace] = held.occurrence
        occurrence = occurrences[namespace]
        prefix = occurrence + "/"
        if not occurrence or not name.startswith(prefix):
            return name
        # the occurrence's namespace, `periods[1]/cons`, ends with the key of
        # its stage, the name the view gives the occurrence's layer
        key = occurrence.rpartition("/")[2]
        return f"{key}/{name[len(prefix) :]}"

    found = {}
    for node in graph.get("nodes") or []:
        namespace = node.get("namespace") or ""
        parts = namespace.split("/") if namespace else []
        for depth in range(1, len(parts) + 1):
            layer = "/".join(parts[:depth])
            tag = (layers.get(layer) or {}).get("method")
            if tag:
                found.setdefault(f"{tag}  {place(layer, layer)}", None)
        tag = _attribute(node, "method")
        if tag:
            found.setdefault(f"{tag}  {place(node['id'], namespace)}", None)
    return [LegendEntry(text) for text in found]


def _legend_marks(graph: dict) -> list[LegendEntry]:
    """The marks the nodes of a graph hold, each with its words
    (`MARK_WORDS`): `· !tag` where a label ends in the tag of a method
    bound within its box; `at` and the policies the nodes' rows are held at,
    read from the attribute `policy`, `at 𝑐`; and the laws of motion the
    labels of the pullbacks and the push-forwards name (`LAW_LETTER`),
    `𝑔≺, 𝑔≻`."""
    method, policies, laws = False, {}, set()
    for node in graph.get("nodes") or []:
        kind = _attribute(node, "kind")
        if not kind:
            continue
        symbol, bound, _ = node["label"].partition(" · !")
        method = method or bool(bound)
        held = _attribute(node, "policy")
        if held:
            for policy in held.split(", "):
                policies.setdefault(policy, None)
        if kind == "Pullback":
            law = symbol.rpartition(" ∘ ")[2]
        elif kind == "Pushforward":
            law = symbol.partition("∗")[0]
        else:
            law = ""
        if law.startswith(LAW_LETTER):
            laws.add(law)
    entries = []
    if method:
        entries.append(LegendEntry("· !tag", None, MARK_WORDS["method"]))
    if policies:
        entries.append(LegendEntry(f"at {', '.join(policies)}", None, MARK_WORDS["policy"]))
    if laws:
        entries.append(LegendEntry(", ".join(sorted(laws)), None, MARK_WORDS["law"]))
    return entries


def _legend_roles(graph: dict) -> list[LegendEntry]:
    """Each role of an initial diagram's fields with the labels of its
    fields, two spaces between them, `value  V≻, V, V≺`, in the order of
    the nodes."""
    roles = {}
    for node in graph.get("nodes") or []:
        if _attribute(node, "kind") == "field":
            roles.setdefault(_attribute(node, "role"), []).append(node["label"])
    return [LegendEntry(f"{role}  {', '.join(labels)}") for role, labels in roles.items()]


def legend_entries(collection: dict | None, graph_id: str, overlays: dict | None) -> tuple:
    """The legend of the graph `graph_id` of the view `collection`
    (AMD-MI-001, decisions A1-D2 and A1-D4), as `(title, groups)`: the
    title is the collection's label, which names the version drawn, `cons
    methodized`; the groups are lists of `LegendEntry` under the keys of
    `LEGEND_GROUPS`, each empty where the graph holds nothing of it:
    `levels`, the levels the graph draws with their swatches
    (`_legend_levels`); `methods`, each bound method's tag and place
    (`_legend_methods`); `marks`, the marks its labels hold with their
    words (`_legend_marks`); `perches`, each perch overlay the view
    draws, `overlays`, the dictionary `model.edge_overlays` answers, by
    the name the overlay carries, also its swatch key, and nothing where
    `overlays` is None, as it is while the overlays are off;
    and `roles`, in an initial diagram, each role with its fields
    (`_legend_roles`). No collection gives no title, and a graph the
    collection does not hold gives empty groups but the perches."""
    groups = {group: [] for group in LEGEND_GROUPS}
    if overlays is not None:
        groups["perches"] = [
            LegendEntry(overlay["name"], overlay["name"]) for overlay in overlays["overlays"]
        ]
    if not collection:
        return "", groups
    held = next((entry for entry in collection["graphs"] if entry["id"] == graph_id), None)
    if held is not None:
        initial = graph_id in INITIAL_IDS.values()
        groups["levels"] = _legend_levels(held, initial)
        groups["methods"] = _legend_methods(collection, graph_id, held)
        groups["marks"] = _legend_marks(held)
        groups["roles"] = _legend_roles(held) if initial else []
    return collection.get("label", ""), groups


def legend_title_parts(title: str) -> tuple[str, list[str]]:
    """The legend's title, the collection's label, as its two parts: the
    name, `tenure`, and the states of the version the collection draws, the
    words of the bindings the exporter writes after the stage's name,
    `["methodized", "configured"]` for `tenure methodized configured`, none
    for a trellis's label, `trellis` (design pass 13 §3; the fix wave Q3b,
    item 19, C8)."""
    words = title.split(" ")
    states = []
    while len(words) > 1 and words[-1] in BOUND_WORDS.values():
        states.insert(0, words.pop())
    return " ".join(words), states


@solara.component
def Legend(collection: dict | None, graph_id: str, overlays: dict | None):
    """The legend of the graph shown, the element `.bl-legend`, which
    `ViewRegion` makes and Details holds (spec 0.4 §2.1, decision 45;
    G-R23): the title
    `.bl-legend-name`, the collection's label (`legend_title_parts`): its
    name in Code small, then the states of the version, `methodized,
    configured`, in Small in `.bl-legend-states`; and one `.bl-legend-group`
    for each group `legend_entries` answers with entries, carrying its key
    as data-group and its title in `.bl-legend-title`; each entry is a
    `.bl-legend-item` holding `.bl-legend-ground`, the navy background of
    its swatch `.bl-legend-swatch`, drawn as a
    line for a perch, with data-level or data-perch naming the custom
    property brand.css uses (specification §5.3), its text
    `.bl-legend-text` and the words after a mark, `.bl-legend-sentence`.
    `overlays` is the dictionary of the perch overlays the view draws, None
    while they are off. The entries are read again only when the collection,
    the graph or the overlays change."""
    title, groups = solara.use_memo(
        lambda: legend_entries(collection, graph_id, overlays),
        [collection, graph_id, overlays],
    )
    name, states = legend_title_parts(title)
    with rv.Html(tag="div", class_="bl-legend"):
        if title:
            # the collection's name in Code small, then the states of the
            # version it draws, the page's words, in Small joined by commas
            # (design pass 13 §3; the fix wave Q3b, item 19, C8)
            parts = [rv.Html(tag="span", class_="bl-code-small", children=[name])]
            if states:
                words = ", ".join(states)
                states_part = rv.Html(
                    tag="span", class_="bl-legend-states bl-small", children=[words]
                )
                parts += [" ", states_part]
            rv.Html(tag="span", class_="bl-legend-name", children=parts)
        for group, entries in groups.items():
            if not entries:
                continue
            with rv.Html(
                tag="div", class_="bl-legend-group", attributes={"data-group": group}
            ).key(group):
                # the page's words in sentence case: the group's title and,
                # but for the file's words of the methods, the marks and the
                # roles, each entry's text and the words after a mark
                # (design pass 13 §3; C12)
                title_words = sentence_case(LEGEND_GROUPS[group])
                rv.Html(tag="span", class_="bl-legend-title", children=[title_words])
                for entry in entries:
                    kept = group in ("methods", "marks", "roles")
                    text = entry.text if kept else sentence_case(entry.text)
                    children = []
                    if entry.swatch is not None:
                        line = " bl-legend-line" if group == "perches" else ""
                        children.append(
                            rv.Html(
                                tag="span",
                                class_="bl-legend-ground",
                                children=[
                                    rv.Html(
                                        tag="span",
                                        class_=f"bl-legend-swatch{line}",
                                        attributes={
                                            ("data-perch" if group == "perches" else "data-level"): (
                                                entry.swatch
                                            )
                                        },
                                    )
                                ],
                            )
                        )
                    code = " bl-code-small" if group in ("methods", "marks") else ""
                    children.append(
                        rv.Html(tag="span", class_=f"bl-legend-text{code}", children=[text])
                    )
                    if entry.sentence:
                        # the space parts the mark from its words in the
                        # legend's text; the item's layout draws no space
                        children += [
                            " ",
                            rv.Html(
                                tag="span",
                                class_="bl-legend-sentence",
                                children=[sentence_case(entry.sentence)],
                            ),
                        ]
                    rv.Html(tag="span", class_="bl-legend-item", children=children).key(entry.text)


# The hover of each select of the graph's bar (R-D56; design pass 8 §6), by
# the select's name.
HEADER_SELECT_HOVERS = {
    "graph": "The builders graph or the initial diagram of the stage",
    "direction": "The direction of the graph",
}


def _header_select(name: str, words: tuple, shown: str, choose, class_: str):
    """One select of the graph's bar (R-D56; design pass 8 §§4 and 6), a
    select of VSCode Elements (`Field`) in the wrapper `.bl-view-select`
    with the class `class_`, which carries the select's hover, its
    accessible name `name` with a capital, `Graph` or `Direction`: its options
    `words`, AAS's words, each written with a capital as the page writes
    its own words (§8, item 1), `Operator` or `Backward`, the word `shown`
    chosen; a choice calls `choose` with its word as the page reads it, in
    lowercase, which shows the graph of the two words (`choose_kind`,
    `choose_direction`)."""
    return Field(
        kind="select",
        value=shown.capitalize(),
        options=[word.capitalize() for word in words],
        hover=HEADER_SELECT_HOVERS[name],
        named=name.capitalize(),
        classes=f"bl-view-select {class_}",
        event_entered=lambda text: choose(text.lower()),
    )


@solara.component
def GraphChoice(chosen: str, mode: str, stage: bool, composed: bool, stage_open: bool):
    """The graph's bar (spec 0.4 §2.1; R-D56; amendment 02 ruling 5; design
    pass 8 §6), for the graph `chosen` shown in the view `mode`: in a
    stage's view showing a stage, `stage`, and in the trellis view alike
    (design pass 14 §7; S-D12), the select `graph`, `Operator` or
    `Initial`; the select `direction`, `Backward` or `Forward`, the four
    graphs of a stage and the four of the trellis being the two selects'
    two by two; and the view tabs `Stage` and `Trellis` (`ViewSwitch`; unit
    K, K-D20), `Trellis` not acting without a composition, `composed`, and
    `Stage` while the editor holds no stage file, `stage_open` false."""
    in_trellis = mode == "trellis"
    with rv.Html(tag="span", class_="bl-graph-choice"):
        if stage or in_trellis:
            _header_select("graph", GRAPH_KINDS, kind_of(chosen), choose_kind, "bl-view-kind").key(
                "kind"
            )
        _header_select(
            "direction", DIRECTIONS, direction_of(chosen), choose_direction, "bl-view-direction"
        ).key("direction")
        ViewSwitch(composed, stage_open, in_trellis).key("switch")


# The hover of the icon button `Perch overlays` at the canvas's foot
# (design pass 8 §§3 and 6), while the overlays are off and while they are
# drawn.
OVERLAYS_HOVERS = {
    False: "Draw the wires of each perch over the graph, in the perch's color",
    True: "Hide the perch overlays",
}


@solara.component
def OverlaysButton(waits: bool):
    """The icon button `Perch overlays` at the foot of a stage's canvas
    (design pass 8 §§3 and 6), the Codicon `layers` (`ToolbarButton`),
    `.bl-overlays-button`, the library's toggle, its button a switch, which
    stands checked, and `.bl-active`, while the overlays are drawn: a click
    draws the wires of each perch over the graph, in the perch's color, or
    hides them (`toggle_overlays`). While no stage is shown, `waits`, it
    does not act."""
    on = overlays_on.value
    return ToolbarButton(
        "perch overlays",
        "Perch overlays",
        OVERLAYS_HOVERS[on],
        toggle_overlays,
        "bl-overlays-button" + (" bl-active" if on else ""),
        {"toggleable": "", **({"checked": ""} if on else {})},
        disabled=waits,
    )


# The hover of the layers button (design pass 15; SE-3, SE-5): the act a click
# performs while the declared builders are shown and while the operative
# ones are, and what it waits for where it does not act.
LAYERS_HOVERS = {
    False: "Show operative builders",
    True: "Show declared builders",
    "one level": "No method adds operations",
    "initial": "Applies to the builders graph",
}


@solara.component
def LayersButton(current: Shown | None, chosen: str):
    """The layers button (specification 0.6 §9; design pass 15; SE-2 to
    SE-5, SE-15), at the foot of a stage's canvas after `Perch overlays`,
    the icon button `Operative builders` (`ToolbarButton`),
    `.bl-layers-button`, the library's toggle, its button a switch, which
    stands checked, and `.bl-active`, while the operative builders are
    shown: the Codicon `layers-dot` while the declared builders are shown and
    `layers-active` while the operative ones are; a click shows the other
    level (`toggle_builders`). It does not act where the two levels of the
    stage `current` are one object, its hover `No method adds operations`,
    nor while the graph `chosen` is an initial diagram, its hover `Applies
    to the builders graph`, keeping its state; nor while no stage is
    shown."""
    on = builders_operative.value
    if current is not None and current.declared is None:
        hover, waits = LAYERS_HOVERS["one level"], True
    elif kind_of(chosen) == "initial":
        hover, waits = LAYERS_HOVERS["initial"], True
    else:
        hover, waits = LAYERS_HOVERS[on], current is None
    return ToolbarButton(
        "operative builders" if on else "declared builders",
        "Operative builders",
        hover,
        toggle_builders,
        "bl-layers-button" + (" bl-active" if on else ""),
        {"toggleable": "", **({"checked": ""} if on else {})},
        disabled=waits,
    )


def view_request(current: Shown | None) -> dict | None:
    """The view's property `place` (AMD-MI-002 §3 rule 4): the place the
    history last asked of the view (`place_request`), as its graph, the
    layers that show its selected node (`navigation.opened_layers`, with
    the occurrence the package's `node_place` places the node in), that
    node, and the request's number, once the view's collection is the
    place's own: in the trellis view, the trellis of the place's recipe
    under its restriction; in a stage's view, the stage of the place's file
    where that file is a stage file, else the stage shown, `current`. None
    before then, and where no place is asked."""
    asked = place_request.value
    if asked is None:
        return None
    place = asked["place"]
    if place.view != view_mode.value:
        return None
    if place.view == "trellis":
        held = trellis_shown.value
        if held is None or (held.source, held.restriction) != (place.recipe, place.restriction):
            return None
        collection = held.collection
        defaults = held.layers.get(place.graph, [])
    else:
        if current is None or (_is_stage(place.file) and current.path != place.file):
            return None
        collection = level_collection(current)
        defaults = current.layers.get(place.graph, [])
    chosen = place.selected or {}
    node = chosen.get("nodeId", "") if chosen.get("graphId") == place.graph else ""
    try:
        # the empty text for a node of a stage's view, whose namespaces name
        # no period
        occurrence = node_place(collection, place.graph, node).occurrence if node else ""
    except (KeyError, ValueError):
        # a node or a graph the collection does not hold
        occurrence = ""
    return {
        "graph": place.graph,
        "layers": navigation.opened_layers(defaults, node, occurrence),
        "nodeId": node,
        "n": asked["n"],
    }


@solara.component
def ViewRegion(result: Outcome | None, current: Shown | None):
    """Spec 0.4 §§2.1–2.2, in the graph column of design pass 8 §6 as design
    pass 10 §2 joins its head to its bar: the graph bar, `.bl-graph-bar`,
    36 px, with the words `Semantic graph`, the graph's selects and the
    view tabs `Stage` and `Trellis` (`GraphChoice`), the restriction's
    select in the trellis view (`ViewRestriction`), the place of the button
    `Stages`, the outdated-source note and the Problems control at its
    right (`ErrorMark`), the words not drawn while the bar's items do not
    fit one row with them (`GraphBarFit`; the fix wave Q3b, item 16, D22);
    the canvas,
    `.bl-canvas`, holding the graph and, floating 12 px inside its lower
    left, the foot's icon buttons, the graph's layout and zoom, which the
    graph's bundle draws, and in a stage's view `Perch overlays`
    (`OverlaysButton`); a folded Matsya opens from the main bar's toggle
    (`MainBar`; design pass 10 §3), where the bar's `Υ` of unit K's K-D19
    stood; and Details, which holds the legend of the graph shown (§5.5;
    G-R23), preceded by the handle on its top edge (AMD-MI-002 §6 rule 2).
    Matsya's column stands beside this region, rendered by `Page` (spec 0.4
    §5.1; unit R, brief rule 2). In a stage's view the foot holds after
    `Perch overlays` the layers button (`LayersButton`), which shows the
    declared or the operative builders (specification 0.6 §9), the
    collection drawn and described being that of the level shown
    (`level_collection`). In the trellis view the collection and the
    layers are the trellis's (unit B), with the record of each builder's
    pair of perches by which the region codes its box
    (`trellis.builder_records`; AAS, L-D7), and Details is the trellis's.
    While a stage's graph is dimmed, the graph bar reads `last constructed
    <digest>`, the construction it shows (`.bl-view-shown`; spec 0.4
    §5.7)."""
    in_trellis = view_mode.value == "trellis"
    held = trellis_shown.value
    unjoined, reading, stages, adds, joins = use_gesture_properties(in_trellis, held)
    builders = solara.use_memo(
        lambda: trellis.builder_records(held) if in_trellis and held is not None else None,
        [held, in_trellis],
    )
    # the recipe's order of the stage keys, by which the region stands every
    # period's occurrences in rows (`trellis.stage_order`; the fix wave Q3a,
    # item 2)
    stage_order = solara.use_memo(
        lambda: trellis.stage_order(held) if in_trellis and held is not None else None,
        [held, in_trellis],
    )
    if in_trellis:
        collection = held.collection if held is not None else None
        layers = held.layers if held is not None else {}
        stale = _trellis_stale()
        scope = f"trellis {source.value.path}" if source.value is not None else "trellis"
    else:
        collection = level_collection(current) if current is not None else None
        layers = current.layers if current is not None else {}
        stale = bool(result is not None and result.stale)
        scope = f"stage {current.path}" if current is not None else "stage"
    overlays = solara.use_memo(
        lambda: model.edge_overlays(current.stage)
        if current is not None and overlays_on.value and not in_trellis
        else None,
        [current, overlays_on.value, in_trellis],
    )
    with rv.Html(tag="section", class_="bl-view"):
        # the one bar of 36 px over the canvas (design pass 10 §2): the
        # graph's name, its selects and the view tabs, the restriction's
        # select and the outdated-source note in `.bl-graph-tools`, the name
        # not drawn where the items do not fit one row with it
        # (`GraphBarFit`; D22), and the items that still do not fit a
        # narrow column take a further row (amendment 02 ruling 5), and
        # Problems at the bar's upper right
        with rv.Html(
            tag="div", class_="bl-bar bl-graph-bar", attributes={"data-graph": graph.value}
        ):
            with rv.Html(tag="div", class_="bl-graph-tools"):
                rv.Html(tag="h2", class_="bl-graph-name", children=["Semantic graph"]).key(
                    "name"
                )
                GraphChoice(
                    graph.value,
                    view_mode.value,
                    current is not None,
                    bool(sources.value),
                    _is_stage(open_path.value),
                ).key("choice")
                if in_trellis:
                    ViewRestriction().key("restriction")
                    rv.Html(tag="span", class_="bl-graph-head").key("graph-head")
                # the construction a dimmed graph of a stage shows, by the
                # digest of its text (spec 0.4 §5.7; Design brief 7 §14), so
                # that the canvas keeps its size while the graph is dimmed
                if (
                    stale
                    and not in_trellis
                    and current is not None
                    and current.path == result.path
                ):
                    rv.Html(
                        tag="span",
                        class_="bl-view-shown",
                        children=[
                            "last constructed ",
                            rv.Html(
                                tag="span", class_="bl-code-small", children=[current.digest[:7]]
                            ),
                        ],
                    ).key("shown")
                # the measure of the bar's row, an element not displayed,
                # last among the items it measures, so that Problems stays
                # the bar's last element (`GraphBarFit`; D22)
                GraphBarFit().key("fit")
            ErrorMark()
        # the canvas, and the foot's controls floating 12 px inside its lower
        # left (design pass 8 §§6 and 8, item 10)
        with rv.Html(tag="div", class_="bl-canvas"):
            Graph(
                collection=collection,
                overlays_request=overlays,
                layers=layers,
                graph=graph.value,
                select=select_request.value,
                stale=stale,
                scope=scope,
                place=view_request(current),
                styles=GRAPH_STYLES,
                unjoined=unjoined,
                reading=reading,
                stages=stages,
                adds=adds,
                joins=joins,
                builders=builders,
                stage_order=stage_order,
                event_selected=on_selected,
                event_processed=on_processed,
                event_opened=on_opened,
                event_refused=on_refused,
                event_connected=on_connected,
                event_dropped=on_dropped,
                event_join_chosen=on_join_chosen,
                event_removed=on_removed,
                event_moved=on_moved,
            )
            with rv.Html(
                tag="div",
                class_="bl-graph-controls",
                attributes={"role": "group", "aria-label": "Graph controls"},
            ):
                rv.Html(tag="span", class_="bl-graph-icons").key("icons")
                if not in_trellis:
                    OverlaysButton(current is None).key("overlays")
                    # the layers button beside it, since in the graph bar
                    # it took the bar past its one row at the 314-px column
                    # (the controller's second ruling on design pass 15;
                    # SE-15)
                    LayersButton(current, graph.value).key("layers")
        # the legend is an argument of Details, which places it, and not a
        # child of this region
        legend = Legend(collection, graph.value, overlays)
        Handle("panel")
        if in_trellis:
            TrellisPanel(legend)
        else:
            Panel(result, current, legend)


# --- the status line ---


def count_fragments(counts: dict) -> list:
    """The elements of the counts of the object in the status line: `5
    blocks (3 backward, 2 forward), 5 builders, 20 wires` where every key
    is held, `5 blocks` where the term's blocks alone are known, and
    nothing where no count is known."""
    if "blocks" not in counts:
        return []
    fragments = [f"{counts['blocks']} ", Term("block", "blocks")]
    if "builders" not in counts:
        return fragments
    fragments.extend(
        [
            f" ({counts['blocks_backward']} ",
            Term("backward"),
            f", {counts['blocks_forward']} ",
            Term("forward"),
            f"), {counts['builders']} ",
            Term("builder", "builders"),
            f", {counts['wires']} ",
            Term("wire", "wires"),
        ]
    )
    return fragments


def status_fragments(result: Outcome, dirty: bool) -> list:
    """The elements of the status line's details for `result`
    (specification §2.5), which the button `more` shows: the file and
    whether it is a buffer or a file, the refusal count first, in ice-2,
    when it is not zero, the state of the loop, the version, the counts of
    the object, the time of the whole loop and the digest of every input,
    each named."""
    file_word = "buffer, unsaved" if dirty else "file"
    fragments = [f"{result.path} (", Term("unsaved", file_word) if dirty else file_word, ")"]
    if result.refusals:
        fragments.extend(
            [
                " · ",
                rv.Html(
                    tag="span",
                    class_="bl-refused bl-refused-some",
                    attributes={"title": TERMS["refused"]},
                    children=[f"{len(result.refusals)} refused"],
                ),
            ]
        )
    if result.state:
        fragments.extend([" · ", Term(result.state, result.state, "bl-state")])
    if result.version:
        fragments.extend([" · ", Term(result.version)])
    counts = count_fragments(result.counts)
    if counts:
        fragments.extend([" · ", *counts])
    fragments.extend([" · ", Term("loop"), f" {result.seconds:.2f} s"])
    digests = []
    for name, digest in result.digests.items():
        digests.extend([" · ", Term(name), f" {digest[:7]}"])
    fragments.append(rv.Html(tag="span", class_="bl-digests", children=digests))
    return fragments


# the commands whose sentence the status line's note prints: the files
# `paper` and `notebook` write (ruling R-P6)
NOTED_COMMANDS = ("paper", "notebook")
# the separator of two parts of the status line's text
STATUS_SEPARATOR = " · "


def status_dot():
    """The separator of two parts of the visible status line,
    `STATUS_SEPARATOR`, kept in the line's text and not drawn (`UnseenText`):
    the parts stand 16 px apart with no dot between them (design pass 8 §6;
    §8, item 7)."""
    return UnseenText(STATUS_SEPARATOR)


def status_summary(result: Outcome | None, current: Shown | None, place: tuple | None) -> list:
    """The two groups of the visible status line (spec 0.4 §5.7; Design
    brief 7 §13; brief rule 8, §5; R-D20, R-D33, R-D39), nothing where
    `result`, the loop's outcome for the open file, is None.
    `.bl-status-where`: the cursor's place `place`, `(line, column)`, as
    `8:33` (`.bl-status-place`, left out where `place` is None); the file's
    name (`.bl-status-file`); and the stage of `current`, the construction
    shown, where it is of the same file: the occurrence it is bound as, or
    `stage <name>` (`.bl-status-stage`). `.bl-status-loop`: where the loop
    has a state, the square (`.bl-status-square`, its `data-state` the
    state), the state as a focusable term (`.bl-status-state`) and the
    first seven characters of the digest of the text the state was computed
    from (`.bl-status-digest`), then the count `<n> refused`
    (`.bl-status-refused`); then `indent 4` (`.bl-status-indent`) and,
    for a stage file, the language `BellmanSym` (`.bl-status-language`).
    No method is printed, since a stage binds several (R-D33), and no
    refusal's sentence, which stands in the list under the error mark.

    Design pass 8 §6: the parts stand 16 px apart with no dot between them,
    each separator ` · ` kept in the line's text and not drawn
    (`status_dot`); the place, the file and the digest, the file's words,
    are set in Code small (`.bl-code-small`), the occurrence among them (the
    fix wave Q3b, item 19, C20), the rest in Small; the square
    is the Codicon `pass-filled` in mint while the state is `constructed`,
    and `circle-large-outline` in ink-3 otherwise, never orange (spec 0.4
    §5.7); the square, the state and the digest stand as one part,
    `.bl-status-construction`."""
    if result is None:
        return []
    where = []
    if place is not None:
        line, column = place
        where += [
            rv.Html(
                tag="span", class_="bl-status-place bl-code-small", children=[f"{line}:{column}"]
            ),
            status_dot(),
        ]
    where += [
        rv.Html(
            tag="span", class_="bl-status-file bl-code-small", children=[Path(result.path).name]
        )
    ]
    if current is not None and current.path == result.path:
        # the occurrence, an address of the file's words, in Code small; or
        # the page's word `stage` in Small before the stage's name in Code
        # small (design pass 13 §3; the fix wave Q3b, item 19, C20)
        if current.occurrence:
            stage = rv.Html(
                tag="span", class_="bl-status-stage bl-code-small", children=[current.occurrence]
            )
        else:
            name = rv.Html(tag="span", class_="bl-code-small", children=[current.stage.name])
            stage = rv.Html(tag="span", class_="bl-status-stage", children=["stage ", name])
        where += [status_dot(), stage]
    loop = []
    if result.state:
        constructed = result.state == "constructed"
        square = icons.CODICONS["constructed" if constructed else "not constructed"]
        loop += [
            rv.Html(
                tag="span",
                class_="bl-status-construction",
                children=[
                    icons.codicon(square, "bl-status-square", {"data-state": result.state}),
                    Term(result.state, result.state, "bl-status-state", focusable=True),
                    " ",
                    rv.Html(
                        tag="span",
                        class_="bl-status-digest bl-code-small",
                        children=[result.digests["text"][:7]],
                    ),
                ],
            ),
            status_dot(),
            Term("refused", f"{len(result.refusals)} refused", "bl-status-refused"),
            status_dot(),
        ]
    loop += [rv.Html(tag="span", class_="bl-status-indent", children=[f"indent {INDENT}"])]
    if _is_stage(result.path):
        loop += [
            status_dot(),
            rv.Html(tag="span", class_="bl-status-language", children=["BellmanSym"]),
        ]
    return [
        rv.Html(tag="span", class_="bl-status-where", children=where),
        rv.Html(tag="span", class_="bl-status-loop", children=loop),
    ]


@solara.component
def StatusRegion(result: Outcome | None, pending: bool, current: Shown | None, dirty: bool):
    """The foot (spec 0.4 §5.7; brief rule 8; R-D9). The status line,
    visible, 24 px high under a hairline (design pass 8 §6): in a stage's
    view the two groups of `status_summary` for the cursor's place and the
    last gesture's note (`GestureNote`; unit N, Task 5), in the trellis
    view the trellis's line, which holds that note (`TrellisStatus`); then
    `elaborating` or `drawing` while the loop runs or the view draws; then
    `.bl-status-note`, the sentence of the last answer of `paper` or
    `notebook` where it was not refused (ruling R-P6), which names the file
    written; then the icon button `More`, the Codicon `chevron-up`, which
    shows the details, and is named `Less`, the Codicon `chevron-down`,
    while they are shown (`ToolbarButton`). The
    details, over the line: the line of the inputs' digests, the counts and
    the seconds (`status_fragments`) and git's line (`GitLine`), which stay
    in the page while hidden, so that what reads them reads the same text.
    Before a file is open the details' line reads `Open a stage file.`, or
    `No stage file.` in a folder that holds none; a file opened as text
    reads its note; the notes of the bindings stand in the list under the
    error mark (AMD-MI-002 §6a rule 1). In the trellis view the trellis's
    line stands in the visible line alone, printed once, with the bindings
    applied where the line with them fits there (spec 0.4 §5.7), and its
    rest after it where the whole fits there; what does not fit stands at
    the head of the details' line, the bindings applied first
    (`trellis_status_parts`, `narrow_status_parts`, `StatusFit`; design
    pass §1 item 10), and the details' line holds what follows it there.
    The status line counts no slot of the recipe, since a slot is a
    parameter of the load and no lack (unit K's decision K-D29). It prints
    `elaborating` also while the queue of values typed in the Parameters
    and Settings tabs holds a value not yet written (`value_queue`), so
    that each Enter is answered at once with the loop running (unit L,
    Task 16)."""
    pending = pending or bool(value_queue.value["queue"])
    answer = git_answer.value
    note = (
        answer["sentence"]
        if answer is not None and not answer["refused"] and answer["command"] in NOTED_COMMANDS
        else None
    )
    # the trellis's line and its rest, which follows the line in the visible
    # line where the whole fits there, as the browser measures it
    # (`StatusFit`), and stands in the details' line otherwise, headed by
    # the bindings applied where the line with them does not fit (spec 0.4
    # §5.7; design pass §1 item 10; unit K, Task 6)
    line, rest = [], []
    if view_mode.value == "trellis":
        line, rest = trellis_status_parts(trellis_outcome.value, trellis_shown.value)
    gesture = gesture_note.value
    sentence = f" · {gesture['sentence']}" if gesture is not None else ""
    # the texts the browser measures: the line with the bindings applied,
    # then the whole line, each with the last gesture's note
    measured = [
        "".join(text for text, _ in line) + sentence,
        "".join(text for text, _ in line + rest) + sentence,
    ]
    fit = status_fit.value
    if fit == 0:
        line, rest = narrow_status_parts(line, rest)
    with rv.Html(tag="footer", class_="bl-status"):
        with rv.Html(
            tag="div", class_="bl-status-lines" + ("" if show_status.value else " bl-hidden")
        ):
            with rv.Html(tag="div", class_="bl-status-line"):
                if view_mode.value == "trellis":
                    # the trellis's line stands in the visible line alone,
                    # so that it is printed once; its rest stands here
                    # where the whole does not fit there
                    if rest and fit < 2:
                        StatusParts(rest, "bl-trellis-rest")
                elif result is None:
                    if (
                        open_path.value is None
                        and folder_read.value
                        and first_stage(tree.value) is None
                    ):
                        solara.Text("No stage file.")
                    else:
                        solara.Text("Open a stage file.")
                elif result.note:
                    solara.Text(result.note)
                else:
                    rv.Html(tag="span", children=status_fragments(result, dirty))
                if pending:
                    rv.Html(tag="span", class_="bl-pending", children=[" · elaborating"])
                elif drawing.value:
                    rv.Html(tag="span", class_="bl-pending", children=[" · drawing"])
            GitLine()
        if view_mode.value == "trellis":
            parts = [TrellisStatus(line, rest, fit == 2)]
        else:
            # the last gesture's note stands in a stage's view too, so that
            # a removal or an addition made from Details or the Recipe tab
            # names what it wrote in either view (unit N, Task 5)
            parts = [*status_summary(result, current, cursor_place.value), GestureNote()]
        if pending:
            parts.append(rv.Html(tag="span", class_="bl-pending", children=["elaborating"]))
        elif drawing.value:
            parts.append(rv.Html(tag="span", class_="bl-pending", children=["drawing"]))
        if note:
            parts.append(
                rv.Html(
                    tag="span",
                    class_="bl-status-note",
                    attributes={"title": note},
                    children=[note],
                )
            )
        shown_details = show_status.value
        parts.append(
            ToolbarButton(
                "less" if shown_details else "more",
                "Less" if shown_details else "More",
                "Hide the details" if shown_details else "Show the details",
                toggle_status,
                "bl-status-toggle" + (" bl-active" if shown_details else ""),
                {"aria-expanded": "true" if shown_details else "false"},
            )
        )
        rv.Html(tag="div", class_="bl-status-summary", children=parts)
        if view_mode.value == "trellis":
            StatusFit(lines=measured, event_fit=on_status_fit)


@solara.component
def GitLine():
    """Git's line (specification §2.5 and §5): git's summary of the tab's
    folder; inside a repository, `commit`, which opens the commit form, and
    `push`; where a stage is shown or the trellis view holds a trellis,
    `export view` (spec 0.4 §4; G-D10), text buttons (design pass 8 §§5.3
    and 6; M-I23) whose words stay in the lowercase of the details' line
    (M-I19); and the sentence of the answer to the last command
    (`git_answer`), git's own or the export's, where the command was not
    refused, or `git is running` while one runs, the buttons not acting
    meanwhile, their hover the same words. Where the last command was
    refused, its button carries the refusal's mark and its sentence stands
    in the list under the error mark (AMD-MI-002 §6a rule 1). A folder no repository
    holds shows neither `commit` nor `push`, since neither would act."""
    running = git_task.pending
    answer = git_answer.value
    refused = answer["command"] if answer is not None and answer["refused"] else None

    def marked(command: str) -> list[str]:
        # the refusal's mark on the button of the refused command
        return ["bl-refusal-mark"] if command == refused else []

    waits = GIT_RUNNING if running else None
    with rv.Html(tag="div", class_="bl-git-line"):
        rv.Html(tag="span", children=[git_line.value])
        if tab_folder.value.git_root is not None:
            TextButton(
                "commit",
                lambda: open_commit(),
                " ".join(["bl-git-commit", *marked("commit")]),
                "Commit the files of this folder you name",
                waits=waits,
            ).key("commit")
            TextButton(
                "push",
                lambda: git_task(kind="push"),
                " ".join(["bl-git-push", *marked("push")]),
                "Push the current branch with the credentials git holds",
                waits=waits,
            ).key("push")
        if shown.value is not None or (
            view_mode.value == "trellis" and trellis_shown.value is not None
        ):
            TextButton(
                "export view",
                run_export,
                " ".join(["bl-git-export", *marked("export")]),
                "Write the shown view under model-explorer/ with its record",
                waits=waits,
            ).key("export")
        if running:
            rv.Html(tag="span", class_="bl-pending", children=[" · git is running"])
        elif answer is not None and not answer["refused"] and answer["sentence"]:
            rv.Html(
                tag="span",
                class_="bl-git-sentence",
                attributes={"title": answer["sentence"]},
                children=[" · " + " · ".join(answer["sentence"].splitlines())],
            )


def FormNote(text: str):
    """The note under a form's head (AAS, L-D14; design pass 4 §2): what the
    form writes, `text`, its paths printed relative to the model folder
    (`folder_relative`; K-D11), in one line in the prose face, which
    brand.css cuts at the form's width with an ellipsis, whole in the
    element's title; `.bl-form-note`."""
    shown = folder_relative(text)
    return rv.Html(tag="p", class_="bl-form-note", attributes={"title": shown}, children=[shown])


@solara.component
def FormHead(
    icon: str,
    name: str,
    context: str = "",
    hover: str | None = None,
    note: str | tuple[str, ...] = "",
):
    """The head of a form (AAS, L-D14; design pass 4 §§2 and 3, kept in the
    system of design pass 8 §§5.5 and 6), `.bl-form-top` with a hairline
    under it: one line 28 px high, `.bl-head.bl-form-head`, holding the
    Codicon of the control `icon` (`icons.CODICONS`), the heading `h2`, the
    form's name `name` in Head, with a capital (§8, item 1), and, after it,
    its context `context` in Code small, `.bl-form-context`, whose hover is
    `hover`, else the context, and at its right end the icon button `close`,
    `.bl-form-close`, whose hover and accessible name are `Close` and whose
    click closes the form as `Cancel` does (`close_form`); under the line
    the note `note` (`FormNote`), where one is given, or each line of it
    where it is a tuple of lines, as the form "new variant" names the
    registry it copies under what it writes (unit L, Task 13)."""
    words = [name]
    if context:
        place = rv.Html(
            tag="span",
            class_="bl-form-context bl-code-small",
            attributes={"title": folder_relative(hover or context)},
            children=[context],
        )
        words += [" ", place]
    with rv.Html(tag="header", class_="bl-form-top") as top:
        with rv.Html(tag="div", class_="bl-head bl-form-head"):
            icons.codicon(icons.CODICONS[icon], "bl-form-icon")
            rv.Html(tag="h2", children=words)
            ToolbarButton("close", "Close", "Close", close_form, "bl-form-close")
        for line in (note,) if isinstance(note, str) else note:
            if line:
                FormNote(line)
    return top


def FormRefusal(sentence: str):
    """The refusal of a form (AAS, L-D14; design pass 4 §2; spec 0.4 §5.7: a
    form's own refusal stands in its form), drawn under the field it
    concerns: the sentence `sentence` of the package, the Workbench or git,
    its paths relative to the model folder (`folder_relative`; K-D11), in
    one line in refusal orange, cut with an ellipsis and whole in its
    hover; `.bl-form-error`."""
    shown = folder_relative(sentence)
    return rv.Html(
        tag="p",
        class_="bl-form-error",
        attributes={"title": shown, "role": "alert"},
        children=[shown],
    )


def FormFoot(primary: str, classes: list, waits: str | None, on_click):
    """The foot of a form (AAS, L-D14; design pass 4 §2, in the controls of
    design pass 8 §5.3), `.bl-form-buttons`, a hairline above it: at its
    right `Cancel`, `.bl-form-cancel`, a text button (`TextButton`) that
    closes the form (`close_form`), then last the form's one primary
    button, a button of VSCode Elements (`CommandButton`), the words
    `primary` with the classes `classes` and `.bl-primary`, filled in the
    accent's fill; while `waits`, the few words that name what it waits
    for, is given, the primary does not act and `waits` is its hover. Each
    is 26 px high, and the words take a capital (§8, item 1)."""
    with rv.Html(tag="div", class_="bl-form-buttons"):
        TextButton("Cancel", close_form, "bl-form-cancel")
        CommandButton(primary, on_click, " ".join([*classes, "bl-primary"]), waits=waits)


def FormLabel(text: str):
    """The label above a list or a choice of a form, `.bl-form-label`, in
    Small, the face of a field's label (design pass 8 §5.1)."""
    return rv.Html(tag="div", class_="bl-form-label", children=[text])


def StageKeyField(value: str, on_value, refused: int = 0, autofocus: bool = False):
    """The field `Stage key` of a form that copies a stage, `.bl-create-key`,
    a field of VSCode Elements (`Field`), holding `value`, each change
    answered by `on_value`; `refused` counts the form's refusals since its
    stage was read, and at each new one the field is drawn again holding the
    focus, so that another key is typed in place of the one refused (AAS,
    L-D5)."""
    # a new element for each refusal, since a field takes the focus when it
    # is drawn
    return Field(
        value=value,
        label="Stage key",
        classes="bl-create-key",
        autofocus=autofocus or refused > 0,
        event_entered=on_value,
    ).key(f"stage key {refused}")


def CheckMark(checked: bool):
    """The mark of a check of a list of several (design pass 8 §§3 and 6):
    a box of 14 px within the control border, `.bl-check`, holding the
    Codicon `check` while `checked`."""
    children = [icons.codicon(icons.CODICONS["checked"])] if checked else []
    return rv.Html(
        tag="span", class_="bl-check" + (" bl-on" if checked else ""), children=children
    )


def ChoiceMark(chosen: bool):
    """The mark of a choice of one (design pass 8 §6 and its mock): a ring
    of 14 px in the control border, `.bl-radio`, filled at its center while
    `chosen`, `.bl-on`."""
    return rv.Html(tag="span", class_="bl-radio" + (" bl-on" if chosen else ""))


@solara.component
def CommitRow(change, named: bool):
    """One change of the commit form, a row of its list of 24 px (AAS, L-D14;
    design pass 4 §2's choice of several; design pass 8 §6): one button
    `.bl-row.bl-commit-path`, also `.bl-commit-tick`, with `data-path`, a
    checkbox, `aria-checked` whether the change is named, that leaves it out
    or names it again, holding its mark (`CheckMark`), git's letters and its
    path, a rename's original first, in Code small; a change left out is
    also `.bl-unticked`."""
    path = f"{change.original} → {change.path}" if change.original else change.path
    row = rv.Html(
        tag="button",
        class_="bl-row bl-commit-path bl-commit-tick bl-list-item"
        + ("" if named else " bl-unticked"),
        attributes={
            "type": "button",
            "data-path": change.path,
            "role": "checkbox",
            "aria-checked": "true" if named else "false",
            "title": path,
        },
        children=[
            CheckMark(named),
            rv.Html(tag="span", class_="bl-commit-mark bl-code-small", children=[change.mark]),
            rv.Html(tag="span", class_="bl-commit-name bl-code-small", children=[path]),
        ],
    )
    rv.use_event(row, "click", lambda *_: toggle_commit_path(change.path))
    return row


@solara.component
def CommitForm():
    """The commit form (specification §5; AAS, L-D14; design pass 4 §3, 440
    px; design pass 8 §6): its head, the Codicon `git-commit`, `Commit` and,
    as its
    context, the branch, `on main`, whose hover names the branch and the
    push destination; its note the files the commit names, by their paths
    from the model folder (K-D11), `commits declaration/spec.yml, …`; each
    change git reports under the tab's folder, by its letters and its path,
    a rename by its original and its new path, each named until left out,
    as a list of checkboxes (`CommitRow`); the message, a text area of two
    lines of VSCode Elements (`Field`), with the refusal under it; and the
    foot, `Cancel` and `Commit`,
    which commits the named paths alone, `git commit --only`, and leaves
    other staged work as it is."""
    place = solara.use_memo(lambda: model.git_place(tab_folder.value), [tab_folder.value])
    left = commit_unticked.value
    named = [change.path for change in commit_changes.value if change.path not in left]
    FormHead(
        "commit",
        "Commit",
        f"on {place.branch}" if place.branch else "",
        f"branch {place.branch or 'none'} · push destination {place.destination or 'none'}",
        f"commits {', '.join(named)}" if named else "commits no file",
    )
    with rv.Html(tag="div", class_="bl-form-list bl-commit-paths"):
        if not commit_changes.value:
            rv.Html(tag="p", class_="bl-form-note", children=["no change"])
        for change in commit_changes.value:
            CommitRow(change, change.path not in commit_unticked.value).key(change.path)
    # the text area of two lines (design pass 8 §4)
    Field(
        kind="area",
        value=commit_message.value,
        label="Message",
        classes="bl-commit-message",
        autofocus=True,
        event_entered=commit_message.set,
    )
    if form_error.value:
        FormRefusal(form_error.value)
    if git_task.pending:
        waits = GIT_RUNNING
    elif not commit_paths():
        waits = "name a file"
    elif not commit_message.value.strip():
        waits = "type a message"
    else:
        waits = None
    FormFoot("Commit", ["bl-commit-submit"], waits, submit_commit)


# The two buttons of a chosen template's row in the form "new trellis", each
# word with its `data-period`: the stage stands in every period, or in the
# terminal period alone (unit K, Task 12; the usability walkthrough §4
# item 7).
PERIOD_CHOICE = (("Every period", "every"), ("Terminal period", "terminal"))


def template_hover(template) -> str:
    """The hover of a template's row (AAS, L-D14; design pass 4 §3), one
    line: its model's title, the parameters its calibration must give and
    the files it brings, by their paths from the template's folder
    (`creation.brought_files`), `brings no file` where it brings none, each
    part after ` · `."""
    brought = ", ".join(creation.brought_files(template))
    parts = (template.model, ", ".join(template.calibration), f"brings {brought or 'no file'}")
    return " · ".join(part for part in parts if part)


@solara.component
def TemplateRow(
    template,
    chosen: bool,
    on_toggle,
    single: bool = False,
    key: str | None = None,
    on_rename=None,
    terminal=None,
    on_terminal=None,
):
    """One template of a stage in a form's list, `.bl-template` with
    `data-template`, `.bl-active` while chosen (AAS, L-D14; design pass 4
    §3; design pass 8 §6): its line, one button of 24 px,
    `.bl-row.bl-template-button`, a choice of one (`single`, its ring,
    `ChoiceMark`) or a checkbox (its box, `CheckMark`), `aria-checked`
    whether it is chosen, whose press chooses it or leaves it (`on_toggle`),
    printing in Code small the key,
    `.bl-template-name`, the name of the folder of its model,
    `.bl-template-model` (`trellis.model_folder_name`), and the parameters
    its calibration must give, `.bl-template-calibration`, its model's title
    and the files it brings in its hover (`template_hover`). Once chosen in
    the form "new trellis" (`key` not None), under the line the key it is
    copied under (`StageKeyField`) and, where `terminal` is not None, the
    two text buttons of `PERIOD_CHOICE`, `terminal` being whether the stage
    stands in the terminal period alone and the button that says so marked,
    each press answered by `on_terminal(template id, whether terminal)`
    (unit K, Task 12)."""
    mark = ChoiceMark(chosen) if single else CheckMark(chosen)
    with rv.Html(
        tag="li",
        class_="bl-template" + (" bl-active" if chosen else ""),
        attributes={"data-template": template.id},
    ):
        button = rv.Html(
            tag="button",
            class_="bl-row bl-template-button bl-list-item",
            attributes={
                "type": "button",
                "data-template": template.id,
                "role": "radio" if single else "checkbox",
                "aria-checked": "true" if chosen else "false",
                "title": template_hover(template),
            },
            children=[
                mark,
                rv.Html(
                    tag="span", class_="bl-template-name bl-code-small", children=[template.key]
                ),
                rv.Html(
                    tag="span",
                    class_="bl-template-model bl-code-small",
                    children=[trellis.model_folder_name(template.stage)],
                ),
                rv.Html(
                    tag="span",
                    class_="bl-template-calibration bl-code-small",
                    children=[", ".join(template.calibration)],
                ),
            ],
        )
        rv.use_event(button, "click", lambda *_: on_toggle(template))
        if chosen and key is not None:
            StageKeyField(key, lambda value: on_rename(template.id, value))
        if chosen and terminal is not None:
            named = {"role": "group", "aria-label": "periods"}
            with rv.Html(tag="span", class_="bl-create-period", attributes=named):
                for word, value in PERIOD_CHOICE:
                    marked = terminal == (value == "terminal")
                    TextButton(
                        word,
                        lambda value=value: on_terminal(template.id, value == "terminal"),
                        "bl-active" if marked else "",
                        attributes={
                            "data-period": value,
                            "aria-pressed": "true" if marked else "false",
                        },
                    ).key(value)


def TemplateRefusal(sentence: str):
    """The row of the template list where the corpus itself cannot be read
    (AAS, L-D14; design pass 4 §3), `.bl-template-refused`: the Codicon
    `warning` and the sentence, its paths relative to the model
    folder (K-D11), in one line in refusal orange, cut with an ellipsis and
    whole in its hover."""
    shown = folder_relative(sentence)
    return rv.Html(
        tag="li",
        class_="bl-template-refused",
        attributes={"title": shown},
        children=[
            icons.codicon(icons.CODICONS["refused template"]),
            rv.Html(tag="span", children=[shown]),
        ],
    )


def RefusedTemplateRow(refused):
    """The row of one entry of the template list whose template the package
    refuses, `refused`, a `creation.RefusedTemplate` (unit L, Task 13;
    defect 1 of the UX simulation; design pass 4 §3), standing in the
    entry's place and chosen by no press: `.bl-template-refused` with
    `data-template`, the Codicon `warning`, the entry's key,
    `.bl-template-name`, the name of the folder of the file refused,
    `.bl-template-model` (`trellis.model_folder_name`), and `refused · <rule>`,
    `.bl-template-refusal`, `refused` alone where the refusal names no rule,
    in one line; the package's sentence, its paths relative to the model
    folder (K-D11), in its hover."""
    words = f"refused · {refused.rule}" if refused.rule else "refused"
    return rv.Html(
        tag="li",
        class_="bl-template-refused",
        attributes={"data-template": refused.id, "title": folder_relative(refused.sentence)},
        children=[
            icons.codicon(icons.CODICONS["refused template"]),
            rv.Html(tag="span", class_="bl-template-name bl-code-small", children=[refused.key]),
            rv.Html(
                tag="span",
                class_="bl-template-model bl-code-small",
                children=[trellis.model_folder_name(refused.file)],
            ),
            rv.Html(tag="span", class_="bl-template-refusal", children=[words]),
        ],
    )


def _read_templates() -> tuple[tuple, str]:
    """The entries of the template list (`creation.template_entries`), each
    a template of the application corpus or the refusal of one, with the
    empty sentence; or no entry, with the sentence of the refusal, where
    the corpus itself cannot be read."""
    try:
        return creation.template_entries(), ""
    except ValueError as error:
        return (), str(error)


def parent_folder(typed: str) -> Path | None:
    """The folder the field `parent folder` of the form "new trellis" names
    (unit L, Task 13): the path `typed`, read without the spaces around it
    and from `~`, the home folder; None for a path that is not full or that
    names no folder."""
    typed = typed.strip()
    given = Path(typed).expanduser()
    return given if typed and given.is_absolute() and given.is_dir() else None


def new_trellis_note(named: Path | None, root: Path, held: bool) -> str:
    """The note of the form "new trellis" (unit L, Task 13; design pass 4
    §3): `writes <parent>/<name>/`, the parent folder `named` by its name,
    then ` beside <model>` where it is the folder that holds the open model
    folder `root`, and `, with a new repository` where no repository holds
    it, `held` being whether one does; `writes <name>/` while the field
    names no folder."""
    if named is None:
        return "writes <name>/"
    beside = f" beside {root.name}" if named.resolve() == root.parent else ""
    made = "" if held else ", with a new repository"
    return f"writes {named.name or named}/<name>/{beside}{made}"


@solara.component
def NewTrellisForm():
    """The one-screen form "new trellis" (specification §4; AAS, L-D14;
    design pass 4 §3, 560 px; unit L, Task 13; design pass 8 §6, its fields
    VSCode Elements' at 26 px, `Field`): its head, the Codicon `new-folder`
    and `New trellis`, with its note, where the folder is written, beside
    the open model by default, and `with a new repository` where no
    repository holds it (`new_trellis_note`); on one row the folder's name
    and the number of periods, a field of six characters; the parent
    folder, `.bl-create-parent`, a full path or one from `~`, which holds
    the folder that holds the tab's model folder until the author types
    another and is read on Enter or when it is left (C-R7 amended; defect
    15 of the UX simulation); the push
    destination of the new repository where one is made; the period's
    label; and the entries of the template list (`_read_templates`): each
    template of the application corpus as a checkbox (`TemplateRow`),
    chosen under a key that defaults to its own, and standing in `every
    period` or, pressed, in the `terminal period` alone (unit K, Task 12),
    and each entry whose template the package refuses as its row in its
    place (`RefusedTemplateRow`; defect 1); where the corpus cannot be
    read, the list holds the refusal's row (`TemplateRefusal`). A refusal
    stands under the field it concerns (`form_error_field`; design pass 4
    §2; unit L's final judgment, §6 item 10): under the row of the name and
    the periods, the parent folder, the push destination or the period's
    label, and under the template list for the templates or for a refusal
    that concerns no one answer. `Write the
    folder` waits for a name and a parent folder, and for no template,
    since a folder with no stage is filled by `new stage`."""
    root = tab_folder.value.root
    name = solara.use_reactive("")
    parent = solara.use_reactive(str(root.parent))
    destination = solara.use_reactive("")
    label = solara.use_reactive("")
    repeat = solara.use_reactive(1)
    # the templates chosen, by id, each with the key it is copied under, in
    # the order chosen
    chosen = solara.use_reactive({})
    # the ids of the templates chosen whose stage stands in the terminal
    # period alone
    terminal = solara.use_reactive(frozenset())
    named = solara.use_memo(lambda: parent_folder(parent.value), [parent.value])
    # whether a repository holds the parent folder named
    in_repository = solara.use_memo(
        lambda: named is not None and model.open_folder(named).git_root is not None, [named]
    )
    entries, unread = solara.use_memo(_read_templates, [])

    def toggle(template):
        held = dict(chosen.value)
        if template.id in held:
            del held[template.id]
            terminal.value = terminal.value - {template.id}
        else:
            held[template.id] = template.key
        chosen.value = held

    def rename(template_id, key):
        chosen.value = {**chosen.value, template_id: key}

    def mark(template_id, alone):
        held = terminal.value
        terminal.value = held | {template_id} if alone else held - {template_id}

    def submit():
        written = label.value.strip() or name.value.strip().replace("-", "_") + "_period"
        pairs = [(key, template_id) for template_id, key in chosen.value.items()]
        alone = [key for template_id, key in chosen.value.items() if template_id in terminal.value]
        submit_new_trellis(
            parent.value, name.value, destination.value, written, repeat.value, pairs, alone
        )

    # the field the standing refusal is drawn under, `templates` for one
    # that concerns no one answer
    refused = form_error.value
    under = (form_error_field.value or "templates") if refused else None
    def count(text):
        # the number of periods, a whole number; a text that is none leaves
        # the number last typed
        try:
            repeat.set(int(text))
        except ValueError:
            pass

    FormHead("new trellis", "New trellis", note=new_trellis_note(named, root, in_repository))
    with rv.Html(tag="div", class_="bl-form-row"):
        Field(
            value=name.value,
            label="Name",
            classes="bl-create-name",
            autofocus=True,
            event_entered=name.set,
        )
        Field(
            kind="number",
            value=str(repeat.value),
            label="Periods",
            classes="bl-create-repeat",
            event_entered=count,
        )
    if under in ("name", "periods"):
        FormRefusal(refused)
    Field(
        value=parent.value,
        label="Parent folder",
        classes="bl-create-parent",
        continuous=False,
        event_entered=parent.set,
    )
    if under == "parent":
        FormRefusal(refused)
    if not in_repository:
        Field(
            value=destination.value,
            label="Push destination of the new repository (optional)",
            classes="bl-create-destination",
            event_entered=destination.set,
        )
    if under == "destination":
        FormRefusal(refused)
    Field(
        value=label.value,
        label="Period label (optional)",
        classes="bl-create-label",
        event_entered=label.set,
    )
    if under == "label":
        FormRefusal(refused)
    FormLabel("Templates")
    listed = {"aria-label": "templates"}
    with rv.Html(tag="ul", class_="bl-form-list bl-templates", attributes=listed):
        if unread:
            TemplateRefusal(unread)
        for item in entries:
            if isinstance(item, creation.RefusedTemplate):
                RefusedTemplateRow(item).key(item.id)
                continue
            TemplateRow(
                item,
                item.id in chosen.value,
                toggle,
                key=chosen.value.get(item.id),
                on_rename=rename,
                terminal=item.id in terminal.value,
                on_terminal=mark,
            ).key(item.id)
    if under == "templates":
        FormRefusal(refused)
    if not name.value.strip():
        waits = "type a name"
    elif named is None:
        waits = "type a parent folder"
    else:
        waits = None
    FormFoot("Write the folder", ["bl-create-submit"], waits, submit)


@solara.component
def AddStageForm():
    """The form "add stage from template", the form of new trellis reduced
    to one question (specification §4; AAS, L-D14; design pass 4 §3, 440
    px; design pass 8 §6): its head, the Codicon `symbol-structure`, `Add
    stage` and the context `from a template`; its note every file the form
    writes, by its path from the
    model folder: the stage into `declaration/`, added to the recipe, to
    the file of the period's list and, where the folder holds it, to
    answers.yml; the templates as a list of choices of one (`TemplateRow`),
    each entry whose template the package refuses as its row in its place
    (`RefusedTemplateRow`; unit L, Task 13);
    the template chosen, its key, which defaults to its own
    (`StageKeyField`), with the refusal under it; and the period file that
    lists it, asked where the recipe's trellis file names more than one
    (`creation.period_files`, read with the tab's unsaved texts). The recipe
    is the one the form edits (`_form_recipe`; spec 0.4 §3.5). Opened by a
    template dropped on a period whose key the recipe or the stage folder
    holds (`form_fill`), the template is chosen and the period's list is
    the one the drop named, its file and its entry, so that the key alone
    is left to type. Where the corpus cannot be read, the list holds the
    refusal's row (`TemplateRefusal`)."""
    root, recipe_name = tab_folder.value.root, _form_recipe()
    fill = form_fill.value or {}

    def filled():
        try:
            template = creation.template_of(fill["template"])
        except (KeyError, ValueError):
            return None
        return template.id, template.key

    chosen = solara.use_reactive(solara.use_memo(filled, []))
    files = solara.use_memo(
        lambda: creation.period_files(root, recipe_name, trellis.texts_of(unsaved_texts())), []
    )
    period_file = solara.use_reactive(
        fill.get("period") or (files[0] if files else creation.PERIOD)
    )
    entry = fill.get("entry", "")
    edited = [creation.factory_path(recipe_name), creation.factory_path(period_file.value)]
    if (root / creation.ANSWERS).is_file():
        edited.append(creation.ANSWERS)
    entries, unread = solara.use_memo(_read_templates, [])

    def toggle(template):
        same = chosen.value is not None and chosen.value[0] == template.id
        chosen.value = None if same else (template.id, template.key)

    FormHead(
        "add stage",
        "Add stage",
        "from a template",
        note=(
            f"writes the stage into {creation.FACTORY_FOLDER}/ and adds it to "
            f"{', '.join(edited[:-1])} and {edited[-1]}"
        ),
    )
    FormLabel("Templates")
    listed = {"aria-label": "templates"}
    with rv.Html(tag="ul", class_="bl-form-list bl-templates", attributes=listed):
        if unread:
            TemplateRefusal(unread)
        for item in entries:
            if isinstance(item, creation.RefusedTemplate):
                RefusedTemplateRow(item).key(item.id)
                continue
            held = chosen.value is not None and chosen.value[0] == item.id
            TemplateRow(item, held, toggle, single=True).key(item.id)
    if chosen.value is not None:
        StageKeyField(chosen.value[1], lambda key: chosen.set((chosen.value[0], key)))
    if form_error.value:
        FormRefusal(form_error.value)
    if len(files) > 1 and not fill:
        Field(
            kind="select",
            value=period_file.value,
            options=list(files),
            label="Period file",
            classes="bl-add-period-file",
            event_entered=period_file.set,
        )
    FormFoot(
        "Add the stage",
        ["bl-add-submit"],
        "choose a template" if chosen.value is None else None,
        lambda: submit_add_stage(chosen.value[0], chosen.value[1], period_file.value, entry),
    )


def listed_folder(typed: str) -> Path | None:
    """The folder the chooser of the form "add stage" from a folder lists for
    the path `typed` (unit K's decision K-D26): the folder `typed` names, or
    the folder that holds the file it names, the path read without the
    spaces around it and from `~`, the home folder (AAS, L-D5); None for a
    path that is not full or that names nothing."""
    typed = typed.strip()
    given = Path(typed).expanduser()
    if not typed or not given.is_absolute():
        return None
    return given if given.is_dir() else given.parent if given.is_file() else None


def folder_entries(typed: str) -> list[tuple[str, str]]:
    """The entries the chooser of the form "add stage" from a folder lists
    for the path `typed` (unit K's decision K-D26), each as its text and the
    path a click on it writes in the form's field: in the folder
    `listed_folder` reads from `typed`, the folder above it as `..`, then
    the folders, each text ending in "/", and then the stage files
    `<name>.bl`, the folders and the files each in the order of their
    names, a name beginning with "." left out. No entry for a path that is
    not full or that names nothing; `..` alone for a folder that cannot be
    read."""
    listed = listed_folder(typed)
    if listed is None:
        return []
    entries = [("..", str(listed.parent))] if listed.parent != listed else []
    try:
        children = sorted(
            (child for child in listed.iterdir() if not child.name.startswith(".")),
            key=lambda child: child.name.lower(),
        )
    except OSError:
        return entries
    entries += [(f"{child.name}/", str(child)) for child in children if child.is_dir()]
    entries += [
        (child.name, str(child)) for child in children if child.is_file() and child.suffix == ".bl"
    ]
    return entries


# The control of `icons.CODICONS` whose Codicon an entry of the chooser of
# the form "add stage" from a folder draws, by the entry's kind (design pass
# 8 §3): the folder above, `arrow-up`, a folder, `folder`, a stage file,
# `file`.
ENTRY_ICONS = {"above": "above", "folder": "folder", "stage": "file"}


@solara.component
def FolderEntry(text: str, target: str, path: solara.Reactive, current: bool = False):
    """One entry of the chooser of the form "add stage" from a folder, one
    row of 24 px of its list (AAS, L-D14; design pass 4 §§2 and 3),
    `.bl-row.bl-folder-entry` with `data-path`, reached by Tab and pressed by
    a click or Enter (window.vue): its Codicon (`ENTRY_ICONS`), `arrow-up`
    before `..`, `folder` before a folder's name, `file` before a stage
    file's name, its text in Code small, and a click that writes `target`, its
    path, in the
    form's field `path`. The entry the field names, `current`, carries
    `.bl-current`, which brand.css marks with the selection's bar, and
    `aria-current`."""
    if text == "..":
        kind = "above"
    else:
        kind = "stage" if text.endswith(".bl") else "folder"
    marked = {"aria-current": "true"} if current else {}
    item = rv.Html(
        tag="li",
        class_="bl-row bl-choice-file bl-folder-entry bl-list-item"
        + (" bl-current" if current else ""),
        attributes={"data-path": target, "role": "button", "tabindex": "0", **marked},
        children=[
            icons.codicon(icons.CODICONS[ENTRY_ICONS[kind]]),
            rv.Html(tag="span", class_="bl-code-small", children=[text]),
        ],
    )
    rv.use_event(item, "click", lambda *_: path.set(target))
    return item


@solara.component
def FolderStageForm():
    """The form "add stage" that the item `From a folder…` of the stage list
    opens (unit K's decision K-D26; the plan of unit K, Task 25; AAS,
    L-D14; design pass 4 §3, 560 px; design pass 8 §6): its head, the
    Codicon `symbol-structure`, `Add stage` and the context `from a folder`,
    with its note, as the form for a
    template says it, the files it edits; the field `folder`, the path of a
    folder of the disk, as wide as the form, which opens on the folder
    `form_fill` names: the first folder of the library where one exists,
    else the folder that holds the model folder
    (`trellis._disk_folder_form`), and, for a stage of the library whose key
    the model folder already holds, that stage's folder in the library
    (`trellis._template_drop`; AAS, L-D6); the field is read on Enter or
    when it is left, and takes a path from `~` and a path with spaces around
    it (AAS, L-D5). Under it the chooser, a list headed by the name of the
    folder it lists (`listed_folder`), of the entries of that folder
    (`folder_entries`, `FolderEntry`), a click on one writing its path in
    the field, the entry the field names marked as the current one; then,
    where the path names a stage folder or its stage file
    (`creation.folder_template`), the stage's row (`TemplateRow`), chosen,
    and the field `stage key`, the folder's name, which the author may
    change (`StageKeyField`), with the refusal under it, the field drawn
    again holding the focus at each refusal (`form_refusals`; L-D5); where
    it names a folder with no stage file, the one line `no stage file in
    this folder`, and where it names no stage otherwise, the sentence that
    says why, in one line, whole in its hover. Opened from the list the
    button `stages` opens, which names no period, the form holds the select
    `period`, the periods drawn, the terminal period first, which chooses
    the period's list (`form_fill`, `periods`); opened from a period, it
    holds none. `add the stage` copies the stage into the period's list the
    drop named or the select chose, its file and its entry, as the form
    copies a template (`submit_add_stage`)."""
    root, recipe_name = tab_folder.value.root, _form_recipe()
    fill = form_fill.value or {}
    path = solara.use_reactive(fill.get("folder", ""))
    typed = path.value.strip()
    # the periods of the select, and the name of the one chosen
    periods = fill.get("periods") or []
    named = solara.use_reactive(periods[0]["name"] if periods else None)
    # the refusals of the form since the path was last read, each of which
    # draws the key field again with the focus
    since = solara.use_memo(lambda: form_refusals.value, [typed])
    refused = form_refusals.value - since

    def read():
        try:
            return creation.folder_template(typed), ""
        except (OSError, ValueError) as error:
            return None, str(error)

    record, reason = solara.use_memo(read, [typed])
    entries = solara.use_memo(lambda: folder_entries(typed), [typed])
    listed = solara.use_memo(lambda: listed_folder(typed), [typed])
    # the stage read from the path, by its id, and the key it is copied
    # under, or None while no stage is chosen
    chosen = solara.use_reactive(None)

    def propose():
        chosen.value = (record.id, record.key) if record is not None else None

    solara.use_effect(propose, [typed])
    period = next((each for each in periods if each["name"] == named.value), fill)
    period_file, entry = period.get("period", creation.PERIOD), period.get("entry", "")
    edited = [creation.factory_path(recipe_name), creation.factory_path(period_file)]
    if (root / creation.ANSWERS).is_file():
        edited.append(creation.ANSWERS)

    def toggle(template):
        chosen.value = None if chosen.value is not None else (template.id, template.key)

    FormHead(
        "add stage",
        "Add stage",
        "from a folder",
        note=(
            f"writes the stage into {creation.FACTORY_FOLDER}/ and adds it to "
            f"{', '.join(edited[:-1])} and {edited[-1]}"
        ),
    )
    Field(
        value=path.value,
        label="Folder",
        classes="bl-folder-path",
        autofocus=True,
        continuous=False,
        event_entered=path.set,
    )
    # the path the field names, read as `folder_entries` reads it
    named_path = str(Path(typed).expanduser()) if typed else None
    with rv.Html(tag="div", class_="bl-form-list bl-folder-chooser"):
        if listed is not None:
            rv.Html(
                tag="div",
                class_="bl-form-list-head bl-code-small",
                children=[listed.name or str(listed)],
            )
        with rv.Html(tag="ul", class_="bl-choices bl-folder-choices"):
            for text, target in entries:
                # keyed apart from the stage's row, which its path keys
                FolderEntry(text, target, path, target == named_path).key(f"entry {target}")
    held = record is not None and chosen.value is not None and chosen.value[0] == record.id
    if record is None:
        empty = (
            listed is not None
            and Path(typed).expanduser().is_dir()
            and not any(text.endswith(".bl") for text, _ in entries)
        )
        shown = "no stage file in this folder" if empty else folder_relative(reason)
        rv.Html(
            tag="p",
            class_="bl-form-note bl-folder-reason",
            attributes={"title": shown},
            children=[shown],
        )
    else:
        with rv.Html(tag="ul", class_="bl-form-list bl-templates"):
            TemplateRow(record, held, toggle).key(record.id)
        if held:
            StageKeyField(
                chosen.value[1], lambda key: chosen.set((record.id, key)), refused=refused
            )
    if form_error.value:
        FormRefusal(form_error.value)
    if periods:
        Field(
            kind="select",
            value=named.value,
            options=[each["name"] for each in periods],
            label="Period",
            classes="bl-folder-period",
            event_entered=named.set,
        )
    FormFoot(
        "Add the stage",
        ["bl-add-submit"],
        None if held else "choose a stage",
        lambda: submit_add_stage(record, chosen.value[1], period_file, entry),
    )


@solara.component
def PeriodStage(key: str, ticked: bool, toggle):
    """One stage of the form "add period", a check of a list of several, a
    row of 24 px (design pass 4 §2; design pass 8 §6): the button
    `.bl-row.bl-period-stage` with `data-key`, `role` checkbox and
    `aria-checked`, also `.bl-active` while ticked, holding its mark
    (`CheckMark`) and the stage's key in Code small; a press ticks it or
    leaves it (`toggle`)."""
    row = rv.Html(
        tag="button",
        class_="bl-row bl-period-stage bl-list-item" + (" bl-active" if ticked else ""),
        attributes={
            "type": "button",
            "data-key": key,
            "role": "checkbox",
            "aria-checked": "true" if ticked else "false",
        },
        children=[CheckMark(ticked), rv.Html(tag="span", class_="bl-code-small", children=[key])],
    )
    rv.use_event(row, "click", lambda *_: toggle(key))
    return row


@solara.component
def AddPeriodForm():
    """The form "add period" (specification §4; AAS, L-D14; design pass 4
    §3, 440 px; design pass 8 §6): the period's label and its stages, chosen
    among the keys of the recipe the form edits (`_form_recipe`,
    `creation.recipe_keys`, read with the tab's unsaved texts; spec 0.4
    §3.6); the period is the earliest
    of the model, written at the end of the list of the trellis file that
    recipe names. Its head, the Codicon `split-horizontal` and `Add
    period`, opened
    from a `+ period` control (`form_fill`) ends with the place the period
    is added at as its context, `before periods[5]` or `between periods[3]
    and periods[2]`, the stage dropped on the control is chosen, and the
    button adds the period at that place, the index `at`. Its note says
    every file the form writes, by its path from the model folder: the
    period file `declaration/period.<label>.yml`, and the period added to
    the trellis file and, where the folder holds it, to answers.yml. The
    field `Label`, with the refusal under it; the stages as a list of
    checkboxes with their keys (`PeriodStage`), two columns where more than
    six (design pass 4 §2)."""
    root, recipe_name = tab_folder.value.root, _form_recipe()
    fill = form_fill.value or {}
    label = solara.use_reactive("")
    chosen = solara.use_reactive(tuple(fill.get("keys") or ()))

    def read_recipe():
        texts = trellis.texts_of(unsaved_texts())
        try:
            # the recipe, the trellis file it names, then its period files
            named = creation.variant_sources(root, recipe_name, texts)[1]
        except (OSError, ValueError):
            named = creation.factory_path(creation.TRELLIS)
        return creation.recipe_keys(root, recipe_name, texts), named

    keys, trellis_file = solara.use_memo(read_recipe, [])
    edited = [trellis_file] + ([creation.ANSWERS] if (root / creation.ANSWERS).is_file() else [])

    def toggle(key):
        held = chosen.value
        chosen.value = tuple(k for k in held if k != key) if key in held else (*held, key)

    head = fill.get("head")
    FormHead(
        "add period",
        "Add period",
        head or "",
        note=(
            f"writes {creation.factory_path('period.<label>.yml')} and adds the period, "
            f"{head or 'the earliest'}, to {' and '.join(edited)}"
        ),
    )
    Field(
        value=label.value,
        label="Label",
        classes="bl-period-label",
        autofocus=True,
        event_entered=label.set,
    )
    if form_error.value:
        FormRefusal(form_error.value)
    FormLabel("Stages")
    columns = " bl-two-columns" if len(keys) > 6 else ""
    with rv.Html(tag="div", class_="bl-checks bl-period-stages" + columns):
        for key in keys:
            ticked = key in chosen.value
            PeriodStage(key, ticked, toggle).key(key)
    if not label.value.strip():
        waits = "type a label"
    elif not chosen.value:
        waits = "choose a stage"
    else:
        waits = None
    FormFoot(
        "Add the period",
        ["bl-period-submit"],
        waits,
        lambda: submit_add_period(label.value, chosen.value, fill.get("at")),
    )


@solara.component
def NewVariantForm():
    """The one-line form "new variant" (specification §4, new variant; AAS,
    L-D14; design pass 4 §3, 440 px; design pass 8 §6): its head, the
    Codicon `versions`, `New variant` and the context `of spec.yml`, the recipe
    it copies, with its
    note, which files the variant writes and where, beside the folder's
    recipe `declaration/spec.yml`, and, where that recipe holds a
    `registry` block, a second line naming the registry the copy keeps,
    `copies the registry of spec.yml: calibration/wage_schedule`
    (`creation.registry_sources`), since the periods' ages the trellis graph
    prints are read from it (unit L, Task 13; defect 19 of the UX
    simulation); the variant's name, a plain word, with the refusal under
    it."""
    name = solara.use_reactive("")
    folder = creation.FACTORY_FOLDER
    recipe_name = creation.RECIPE
    root = tab_folder.value.root
    registry = solara.use_memo(lambda: creation.registry_sources(root, recipe_name), [root])
    lines = [f"writes spec.<name>.yml, trellis.<name>.yml and period.<name>.yml in {folder}/"]
    if registry:
        lines.append(f"copies the registry of {recipe_name}: {', '.join(registry)}")
    FormHead("new variant", "New variant", f"of {recipe_name}", note=tuple(lines))
    Field(
        value=name.value,
        label="Name",
        classes="bl-variant-name",
        autofocus=True,
        event_entered=name.set,
    )
    if form_error.value:
        FormRefusal(form_error.value)
    FormFoot(
        "Write the variant",
        ["bl-variant-submit"],
        None if name.value.strip() else "type a name",
        lambda: submit_new_variant(name.value),
    )


@solara.component
def NewStageForm():
    """The one-line form "new stage" (unit K's decision K-D7; AAS, L-D14;
    design pass 4 §3, 440 px; design pass 8 §6): its head, the Codicon
    `new-file` and `New stage`,
    with its note, every file the form writes, by its path from the model
    folder: the stage file `declaration/stages/<key>/<key>.bl`, and the
    stage added to the recipe the form edits (`_form_recipe`) and, where the
    folder holds it, to answers.yml; the stage's key, with the refusal under
    it."""
    key = solara.use_reactive("")
    root = tab_folder.value.root
    edited = [creation.factory_path(_form_recipe())]
    if (root / creation.ANSWERS).is_file():
        edited.append(creation.ANSWERS)
    FormHead(
        "new stage",
        "New stage",
        note=(
            f"writes {creation.factory_path(creation.stage_file('<key>'))} and adds the "
            f"stage to {' and '.join(edited)}"
        ),
    )
    Field(
        value=key.value,
        label="Stage key",
        classes="bl-new-stage-key",
        autofocus=True,
        event_entered=key.set,
    )
    if form_error.value:
        FormRefusal(form_error.value)
    FormFoot(
        "Write the stage",
        ["bl-new-stage-submit"],
        None if key.value.strip() else "type a key",
        lambda: submit_new_stage(key.value),
    )


# The forms whose panel is 560 px wide, since each holds a chooser or the
# list of templates with its keys (design pass 4 §2): by the value of
# `form_open`, the form "add stage" from a folder by the fill of a folder.
WIDE_FORMS = ("new trellis",)


@solara.component
def Forms():
    """The form open over the window, if any (`form_open`): every form one
    panel, which brand.css draws (AAS, L-D8, L-D14; design pass 4 §2), at
    most 440 px wide, or 560 px with a chooser or the list of templates
    with its keys (`WIDE_FORMS`, and the form from a folder),
    `.bl-form-wide`. Each form draws its own refusal under the field it
    concerns (`FormRefusal`)."""
    with rv.Html(tag="div", class_="bl-forms"):
        if form_open.value is not None:
            from_folder = form_open.value == "add stage" and "folder" in (form_fill.value or {})
            wide = form_open.value in WIDE_FORMS or from_folder
            with rv.Html(tag="div", class_="bl-form-ground"):
                with rv.Html(
                    tag="section",
                    class_="bl-form" + (" bl-form-wide" if wide else ""),
                    attributes={"data-form": form_open.value},
                ):
                    if form_open.value == "new trellis":
                        NewTrellisForm()
                    elif form_open.value == "new variant":
                        NewVariantForm()
                    elif form_open.value == "new stage":
                        NewStageForm()
                    elif from_folder:
                        FolderStageForm()
                    elif form_open.value == "add stage":
                        AddStageForm()
                    elif form_open.value == "add period":
                        AddPeriodForm()
                    else:
                        CommitForm()


# The two libraries of design pass 8 (§§3 and 4), each a file of the
# package's public/ folder, which Solara serves at /static/assets/ (G-D12):
# Codicons' stylesheet, linked under the id VSCode Elements reads, and
# VSCode Elements' module, which defines the toolbar buttons and the other
# controls the page draws.
CODICON_STYLESHEET = "codicons/codicon.css"
VSCODE_ELEMENTS = "vscode-elements/bundled.js"


@solara.component
def Libraries():
    """The two libraries of design pass 8, each loaded once in the page's
    head from the package's own files, never from a network (§§3 and 4):
    Codicons' stylesheet, `link#vscode-codicon-stylesheet`, the id VSCode
    Elements' icons read to draw their glyphs, and VSCode Elements' module,
    `script[type=module]`; each by Solara's `HeadTag`, whose element in the
    page holds no box."""
    root = solara.use_router().root_path
    with rv.Html(tag="div", class_="bl-libraries", attributes={"hidden": ""}):
        HeadTag(
            tagname="link",
            key="vscode-codicon-stylesheet",
            attributes={
                "rel": "stylesheet",
                "id": "vscode-codicon-stylesheet",
                "href": f"{root}/static/assets/{CODICON_STYLESHEET}",
            },
        )
        HeadTag(
            tagname="script",
            key="vscode-elements",
            attributes={"type": "module", "src": f"{root}/static/assets/{VSCODE_ELEMENTS}"},
        )


@solara.component
def Layout(children=[]):
    """The page's frame: the libraries of design pass 8 (`Libraries`), then
    the children alone, in place of Solara's own application bar and
    sidebar."""
    return rv.Html(tag="div", class_="bl-root", children=[Libraries(), *children])


@solara.component
def Page():
    """The window: the main bar across its first row (`MainBar`; design
    pass 10 §§2 and 3), the folder, the file, the view with
    its legend and its panel, Matsya's column with the handle on its left
    edge, from the window's first row to its foot, unless the setting `off`
    holds (`MATSYA_OFF`; spec 0.4 §6), the status line, and the behavior of
    the window as a whole (`Window`), which gives the columns their widths,
    folds the folder, the Inspector, Details and Matsya on a click of the
    main bar's toggles, of a panel's `×` or of Matsya's head, or on a command's
    `request_fold`, a folded Matsya taking no width (unit K's decision
    K-D19), folds Matsya while the trellis view is shown (K-D6), sizes the
    regions from their handles, keeps the sizes and the folds for the tab's
    folder and reads the keys of the history and of Goto Anything and
    Escape of a wide panel (AAS, L-D11 and L-D12), and keeps the
    high-contrast setting; the ground under a panel's wide panel
    (`WideGround`); Goto Anything (`Goto`), with the entries of `@`
    (`goto_entries`) and of `>` (`goto_commands`); the loop's task and the
    watcher of the files on disk. The trellis's task reads the trellis of
    the source shown (`run_trellis`); the folder opens on its trellis where
    it holds a source of one, and else on its first stage file, when the
    page does (`open_first`), and a file the desktop application or the
    page's address requests opens over it (`Desktop`, `on_desktop_open`)."""
    solara.Title(f"{tab_folder.value.root.name} · Bellman Workbench")
    solara.Style(BRAND_CSS)
    path = open_path.value
    held = buffers.value.get(path) if path is not None else None
    revision = held["revision"] if held is not None else 0
    digest = held["digest"] if held is not None else None
    task = solara.lab.use_task(
        run_loop,
        dependencies=[path, revision, rebind.value, source.value, head.value],
        raise_error=False,
    )
    # the source, the restriction, the watcher's count and the unsaved inputs
    # of this render
    trellis_values = (
        source.value,
        restriction.value,
        trellis_rebuild.value,
        unsaved_inputs(),
    )
    trellis_task = solara.lab.use_task(run_trellis, dependencies=None, raise_error=False)

    def read_trellis():
        # no call while `_use_source` writes a new source's opening text, so
        # that the change of restriction starts no reading of the source before
        if writing_opening.value:
            return
        # Solara's thread passes this call's argument to `run_trellis`, so the
        # run reads the values of the render whose effect made the call
        trellis_task(trellis_values)

    solara.use_effect(read_trellis, list(trellis_values))
    solara.use_thread(watch, dependencies=[path, digest], intrusive_cancel=False)
    result = _result_of(path)
    current = shown.value
    # the folder's first file, opened by the page itself, so that a page
    # rendered without a browser opens it too; `desktop.vue`'s mount then
    # opens a requested file over it (`on_desktop_open`), and `open_first`
    # returns where a file is open
    solara.use_effect(open_first, [])
    solara.use_effect(
        apply_desktop_request,
        [desktop_pending.value, path, revision, result, current, drawing.value],
    )
    dirty = _dirty_paths()
    pending = trellis_task.pending if view_mode.value == "trellis" else task.pending
    # the entries of `@`, read again when what they are read from changes
    entries = solara.use_memo(
        lambda: goto_entries(current, result),
        [current, result, held, view_mode.value, graph.value, trellis_shown.value],
    )
    with rv.Html(tag="main", class_="bl-window"):
        Desktop(
            folder=str(tab_folder.value.root),
            acknowledged={
                "path": path,
                "text": held["text"] if held is not None else None,
                "dirty": bool(dirty),
            },
            event_open=on_desktop_open,
        )
        # the main bar first of the regions, so that Tab reaches it first
        MainBar(current)
        # the palette after the main bar, which holds its button, so that
        # Tab from its last result goes on to the folder
        Goto(
            open_request=goto_open_request.value,
            entries=entries + goto_commands(),
            selection=selected.value,
            event_preview=on_goto_preview,
            event_chosen=on_goto_chosen,
            event_cancelled=on_goto_cancelled,
        )
        FolderRegion(dirty)
        FileRegion(result, held, dirty)
        ViewRegion(result, current)
        if not MATSYA_OFF:
            Handle("matsya")
            # Matsya's column (spec 0.4 §5.6), keyed so that it keeps its
            # state and its task when the window's other children change;
            # its conversation is named by a digest of the folder's path
            # (decision 32)
            matsya_window.MatsyaWindow(
                _session(),
                Field,
                ToolbarButton,
                TextButton,
                matsya_context(),
                MATSYA_ACTIONS,
                Handle,
            ).key("matsya")
        StatusRegion(result, pending, current, path in dirty)
        Forms()
        Window(
            folder=str(tab_folder.value.root),
            fold_request=fold_request.value,
            event_back=go_back,
            event_forward=go_forward,
            contrast_request=contrast_request.value,
            event_goto=open_goto,
            trellis_view=view_mode.value == "trellis",
            wide_panel=region_wide.value is not None,
            lower_panel=lower_panel(open_path.value),
            event_escape=close_wide,
            event_region_folded=on_region_folded,
            event_close_recipe_row=close_recipe_row,
        )
        # last, so that the children before it keep their places
        if region_wide.value is not None:
            WideGround()
