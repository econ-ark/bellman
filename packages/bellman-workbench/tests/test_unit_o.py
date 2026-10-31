"""The acceptance tests of unit O of model interface specification 0.4,
design pass 11, the cable as a line and the Recipe tab at rest: the test
of the Recipe tab's rows at rest and its one open row (§2), reading the
page's elements, never a screenshot's pixels, with the rows' type, grid and
marks as design pass 13 §§3 to 5 draws them (unit Q). The test of the
cable's strokes stands in `tests/test_unit_n.py`. Deleted when the next
amendment is accepted (lean implementation rule, layer 2).
"""

from __future__ import annotations

from workbench_support import (
    DOCUMENT_JS,
    RECIPE_FILE,
    file_bytes,
    new_tab,
    open_recipe_row,
    open_trellis,
    property_color,
    recipe_rows_at_rest,
    unsaved_in_tree,
    wait_until,
)

# The bequest's calibration as the durables recipe writes it, and as the
# test's copy writes it, with one source, so that the bequest's row holds
# one line in every column.
BEQUEST_TWO_SOURCES = "calibration: {all: [calibration/durables, $fill]}, periods: [0, 0]}"
BEQUEST_ONE_SOURCE = "calibration: {all: [calibration/durables]}, periods: [0, 0]}"

# The rows of the copy's recipe as the Recipe tab prints them at rest
# (design pass 11 §2; K-D30), by the stage's key: the text of each line,
# its parts joined by a space, the Stage cell's key, alone since each stage
# file of the durables recipe is `<key>.bl` (design pass 13 §3; C10), then
# each kind's entries in the file's order, `—` for a kind the recipe
# writes no list of, then the periods, `All` where the recipe writes none.
REST_TEXTS = {
    "tenure": [
        "tenure",
        "durables",
        "$fill",
        "durables",
        "$fill",
        "methods",
        "$tenure_method",
        "All",
    ],
    "keeper_cons": [
        "keeper_cons",
        "durables",
        "$fill",
        "durables",
        "$fill",
        "methods",
        "$keeper_method",
        "All",
    ],
    "adjuster_cons": [
        "adjuster_cons",
        "durables",
        "$fill",
        "durables",
        "$fill",
        "methods",
        "$adjuster_method",
        "All",
    ],
    "bequest": ["bequest", "durables", "—", "—", "0–0"],
}
# The stage file of adjuster_cons as the recipe writes it, the hover of its
# key, the row printing no file's name where it is `<key>.bl` (C10).
ADJUSTER_CONS_STAGE = "stages/adjuster_cons/adjuster_cons.bl"

# The Recipe tab as the browser draws it: each row's height and class by
# its stage's key; the color of a file's text, of a slot's and of the
# periods' `All` at rest, each the first of tenure's row; the trash's icon
# color in tenure's row; tenure's ground, outline and outline offset; the
# open row's ground and left bar; the number of `New file` buttons by the
# key of the row that holds them; the stage file's name of adjuster_cons
# where the row prints one, whether it is cut and its hover, and its key's
# hover and whether its key is cut; and the element that holds the focus,
# the key of a row where it is the row itself.
RECIPE_TAB_JS = r"""
() => {
  const table = document.querySelector('.bl-recipe-table');
  const rows = Array.from(table.querySelectorAll('.bl-recipe-row'));
  const tenure = table.querySelector('.bl-recipe-row[data-stage="tenure"]');
  const style = tenure ? getComputedStyle(tenure) : null;
  const color = (element) => element ? getComputedStyle(element).color : null;
  const icon = (button) => {
    if (!button) return null;
    const value = getComputedStyle(button).getPropertyValue('--vscode-icon-foreground').trim();
    const probe = document.createElement('span');
    probe.style.color = value || '#cccccc';
    document.body.append(probe);
    const found = getComputedStyle(probe).color;
    probe.remove();
    return found;
  };
  const open = table.querySelector('.bl-recipe-row[aria-expanded="true"]');
  const adjuster = table.querySelector('.bl-recipe-row[data-stage="adjuster_cons"]');
  const name = adjuster && adjuster.querySelector('[data-kind="stage"] .bl-recipe-text');
  const key = adjuster && adjuster.querySelector('.bl-recipe-key');
  const focused = document.activeElement;
  const newFiles = {};
  for (const button of table.querySelectorAll('.bl-new-file')) {
    const row = button.closest('.bl-recipe-row').dataset.stage;
    newFiles[row] = (newFiles[row] || 0) + 1;
  }
  return {
    heights: Object.fromEntries(rows.map((row) =>
      [row.dataset.stage, row.getBoundingClientRect().height])),
    classes: Object.fromEntries(rows.map((row) => [row.dataset.stage, row.className])),
    cursor: style ? style.cursor : null,
    tenureGround: style ? style.backgroundColor : null,
    outline: style ? [style.outlineStyle, style.outlineWidth, style.outlineColor,
      style.outlineOffset] : null,
    file: color(tenure && tenure.querySelector(
      '.bl-recipe-text:not(.bl-recipe-slot):not(.bl-recipe-placeholder)')),
    slot: color(tenure && tenure.querySelector('.bl-recipe-slot')),
    all: color(tenure && tenure.querySelector('.bl-recipe-placeholder')),
    trash: icon(tenure && tenure.querySelector('.bl-remove-stage')),
    ground: open ? getComputedStyle(open).backgroundColor : null,
    bar: open ? getComputedStyle(open).boxShadow : null,
    newFiles,
    name: name ? [name.scrollWidth > name.clientWidth, name.getAttribute('title')] : null,
    keyTitle: key ? key.getAttribute('title') : null,
    keyCut: key ? key.scrollWidth > key.clientWidth : null,
    focus: focused && focused.classList.contains('bl-recipe-row') ? focused.dataset.stage : null,
  };
}
"""

# The rhythm of the rows at rest (the controller's addendum to design pass
# 11 §2; design pass 13 §§3 and 4, Q-D21): the baseline of the heads'
# first word, and of each row its top and the baselines of each cell's
# key, texts, `—` and ranges in the cell's order, each read as the bottom
# of an empty inline block placed at the start of its element; and each
# trash's box with the box of its row's first line, the key's, and the
# row's box.
RHYTHM_JS = r"""
() => {
  const baseline = (element) => {
    const probe = document.createElement('span');
    probe.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
    element.insertBefore(probe, element.firstChild);
    const y = probe.getBoundingClientRect().bottom;
    probe.remove();
    return y;
  };
  const box = (element) => {
    const found = element.getBoundingClientRect();
    return [found.left, found.top, found.width, found.height];
  };
  const table = document.querySelector('.bl-recipe-table');
  const rows = Array.from(table.querySelectorAll('.bl-recipe-row'));
  return {
    heads: baseline(table.querySelector('.bl-recipe-heads > span')),
    rows: rows.map((row) => ({
      top: box(row)[1],
      cells: Array.from(row.querySelectorAll('.bl-recipe-cell'), (cell) => Array.from(
        cell.querySelectorAll(
          '.bl-recipe-key, .bl-recipe-text, .bl-recipe-none, .bl-recipe-range'),
        baseline)),
    })),
    trash: rows.map((row) => [box(row.querySelector(':scope > .bl-remove-stage')),
      box(row.querySelector('.bl-recipe-key-line')), box(row)]),
  };
}
"""

# a select of tenure's row: its first calibration entry
TENURE_CALIBRATION_SELECT = (
    '.bl-recipe-entry[data-address="stages.tenure.calibration.all[0]"] vscode-single-select'
)


def expanded(tab) -> list[str]:
    """The keys of the Recipe tab's rows that stand open."""
    return [key for key, row in recipe_rows_at_rest(tab).items() if row["expanded"]]


def test_the_recipe_tab_s_rows_are_text_at_rest_and_one_row_opens_to_its_controls(
    browser, server_on, scratch_durables
):
    """Design pass 11 §2 with the controller's addendum, at 1600 × 1000, on
    a copy of the durables model whose bequest is calibrated by one file,
    with the rows' type, grid and marks of design pass 13 §§3 to 5 (C3,
    C10, D2, Q-D9, Q-D21). With the recipe open, every row of the Recipe
    tab stands at rest: aria-expanded false, no select and no `New file`,
    each line the text the recipe's entry prints, the Stage cell its key
    alone, never cut, since each stage file is `<key>.bl`, the key's hover
    the file's path, a file in ink-1, a slot and `All` in ink-3, the
    pointer a control's, the trash in ink-3 and in ink-2 under the pointer
    on the row; a row with two sources in a column is 48 px high, and the
    bequest's, one line in every column, 32 px; every baseline of the rows'
    keys and texts stands on a whole pixel, each cell's first baseline 20
    px below its row's top, 8 px of padding and 12 px in the key's line of
    14 px as in a value's line of 16 px, and each further line of a cell 16
    px below the one above it (the fix wave Q3b of unit Q, item 15; D21);
    each trash's target of 24 × 24 px stands in the table's last column,
    centered on its row's key line, its right edge 8 px inside the row's.
    A click on keeper_cons's key opens that row alone, 68 px, selected, on
    the selection's wash with a bar of 3 px in the accent at its left, its
    seven selects and its two `New file` buttons drawn; the pointer pressed on
    tenure's file name draws tenure on the pressed wash, and released opens
    tenure and closes keeper_cons. Escape while a select of the open row holds
    its list open closes the list alone; a second Escape closes the row, the
    focus standing on the row with a 1-px accent ring inset; Enter on the row
    opens it, Escape closes it, Space opens it, and a click outside the
    table closes it. None of this writes: the recipe's text in the editor
    and the folder's files are as before, and no file is marked unsaved.
    Last, a click on the bequest's trash removes its row and opens none."""
    recipe_file = scratch_durables / RECIPE_FILE
    original = recipe_file.read_text(encoding="utf-8")
    assert original.count(BEQUEST_TWO_SOURCES) == 1
    recipe_text = original.replace(BEQUEST_TWO_SOURCES, BEQUEST_ONE_SOURCE)
    recipe_file.write_text(recipe_text, encoding="utf-8")
    rows = [line for line in recipe_text.splitlines(True) if line.startswith("  bequest:")]
    assert len(rows) == 1
    no_bequest = recipe_text.replace(rows[0], "")
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_durables), RECIPE_FILE)
        tab.wait_for_selector(".bl-recipe-table .bl-recipe-row", timeout=60_000)
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == recipe_text, 30.0, "the recipe in the editor"
        )
        before = file_bytes(scratch_durables)
        ink_1, ink_2, ink_3 = (property_color(tab, f"--bl-ink-{n}") for n in (1, 2, 3))
        accent = property_color(tab, "--bl-accent")

        # every row at rest, text alone, on the rhythm of 4 px
        tab.mouse.move(1200, 500)
        rest = recipe_rows_at_rest(tab)
        print(f"design pass 11 §2: the rows at rest {rest}")
        assert {key: row["texts"] for key, row in rest.items()} == REST_TEXTS, rest
        assert {key: (row["expanded"], row["selects"]) for key, row in rest.items()} == {
            key: (False, 0) for key in REST_TEXTS
        }, rest
        drawn = tab.evaluate(RECIPE_TAB_JS)
        print(f"design pass 11 §2: the tab at rest {drawn}")
        assert drawn["newFiles"] == {}, drawn
        heights = {key: round(height, 1) for key, height in drawn["heights"].items()}
        assert heights == {
            "tenure": 48.0,
            "keeper_cons": 48.0,
            "adjuster_cons": 48.0,
            "bequest": 32.0,
        }, drawn
        assert (drawn["file"], drawn["slot"], drawn["all"]) == (ink_1, ink_3, ink_3), drawn
        assert (drawn["cursor"], drawn["trash"]) == ("pointer", ink_3), drawn
        assert drawn["name"] is None and drawn["keyTitle"] == ADJUSTER_CONS_STAGE, drawn
        assert drawn["keyCut"] is False, drawn
        rhythm = tab.evaluate(RHYTHM_JS)
        print(f"design pass 13 §4: the rhythm at rest {rhythm}")
        assert rhythm["heads"] == round(rhythm["heads"]), rhythm
        for row in rhythm["rows"]:
            baselines = [y for cell in row["cells"] for y in cell]
            assert all(y == round(y) for y in baselines), row
            # each cell's first baseline 20 px below the row's top, and each
            # further line of a cell 16 px below the one above it
            assert {cell[0] - row["top"] for cell in row["cells"]} == {20}, row
            for cell in row["cells"]:
                lines = sorted(set(cell))
                assert all(b - a == 16 for a, b in zip(lines, lines[1:])), row
        for trash, line, row in rhythm["trash"]:
            # the target of 24 px in the last column, centered on the key's
            # line of 14 px, its right edge 8 px inside the row's
            assert (trash[2], trash[3]) == (24, 24), rhythm
            assert abs(trash[1] + 12 - (line[1] + line[3] / 2)) <= 0.5 and line[3] == 14, rhythm
            assert abs(trash[0] + trash[2] - (row[0] + row[2] - 8)) <= 0.5, rhythm
        tab.hover('.bl-recipe-row[data-stage="tenure"] [data-kind="settings"]')
        drawn = tab.evaluate(RECIPE_TAB_JS)
        assert (drawn["trash"], drawn["tenureGround"]) == (
            ink_2,
            property_color(tab, "--bl-hover"),
        ), drawn

        # a click on keeper_cons's key opens that row alone, with its controls
        open_recipe_row(tab, "keeper_cons")
        assert expanded(tab) == ["keeper_cons"]
        opened = recipe_rows_at_rest(tab)
        assert opened["keeper_cons"]["selects"] == 7, opened
        assert [opened[key]["selects"] for key in ("tenure", "adjuster_cons", "bequest")] == [
            0,
            0,
            0,
        ], opened
        drawn = tab.evaluate(RECIPE_TAB_JS)
        print(f"design pass 11 §2: keeper_cons open {drawn}")
        assert drawn["classes"]["keeper_cons"] == "bl-recipe-row bl-recipe-open", drawn
        assert drawn["classes"]["tenure"] == "bl-recipe-row", drawn
        assert abs(drawn["heights"]["keeper_cons"] - 68) <= 0.5, drawn
        assert drawn["newFiles"] == {"keeper_cons": 2}, drawn
        assert drawn["ground"] == property_color(tab, "--bl-selected"), drawn
        assert drawn["bar"] == f"{accent} 3px 0px 0px 0px inset", drawn

        # the pointer pressed on tenure's file name draws the pressed wash;
        # released, it opens tenure and closes keeper_cons
        tab.hover('.bl-recipe-row[data-stage="tenure"] [data-kind="calibration"] .bl-recipe-text')
        tab.mouse.down()
        assert tab.evaluate(RECIPE_TAB_JS)["tenureGround"] == property_color(tab, "--bl-press")
        tab.mouse.up()
        wait_until(lambda: expanded(tab) == ["tenure"], 10.0, "tenure open alone")

        # Escape closes a select's open list first, then the row, the focus
        # returning to the row, which draws its ring
        tab.click(TENURE_CALIBRATION_SELECT)
        tab.wait_for_selector(f"{TENURE_CALIBRATION_SELECT}[open]", timeout=10_000)
        tab.keyboard.press("Escape")
        tab.wait_for_selector(f"{TENURE_CALIBRATION_SELECT}:not([open])", timeout=10_000)
        tab.wait_for_timeout(500)
        assert expanded(tab) == ["tenure"]
        tab.keyboard.press("Escape")
        wait_until(lambda: expanded(tab) == [], 10.0, "tenure closed by Escape")
        drawn = tab.evaluate(RECIPE_TAB_JS)
        assert drawn["focus"] == "tenure", drawn
        assert drawn["outline"] == ["solid", "1px", accent, "-1px"], drawn

        # Enter and Space on the row open it, Escape closes it
        tab.keyboard.press("Enter")
        wait_until(lambda: expanded(tab) == ["tenure"], 10.0, "tenure opened by Enter")
        tab.keyboard.press("Escape")
        wait_until(lambda: expanded(tab) == [], 10.0, "tenure closed by Escape")
        assert tab.evaluate(RECIPE_TAB_JS)["focus"] == "tenure"
        tab.keyboard.press("Space")
        wait_until(lambda: expanded(tab) == ["tenure"], 10.0, "tenure opened by Space")

        # a click outside the table closes the open row
        tab.click(".bl-inspector-file")
        wait_until(lambda: expanded(tab) == [], 10.0, "tenure closed by a click outside")

        # nothing written
        assert tab.evaluate(DOCUMENT_JS) == recipe_text
        assert file_bytes(scratch_durables) == before
        assert unsaved_in_tree(tab) == []

        # the trash removes the bequest's row and opens no row
        tab.click('.bl-recipe-row[data-stage="bequest"] .bl-remove-stage')
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == no_bequest, 30.0, "bequest's row out")
        wait_until(lambda: "bequest" not in recipe_rows_at_rest(tab), 30.0, "bequest's row gone")
        assert expanded(tab) == []
    finally:
        context.close()
