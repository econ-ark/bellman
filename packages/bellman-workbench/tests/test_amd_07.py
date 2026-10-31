"""The tests of amendment 07 of model interface specification 0.4, the
composer of the Matsya column: a text area sized by its text or by the
handle on the composer's top edge, and its keys. Each test is named by the
acceptance case of the amendment's §6 that it checks and prints its
measurements. The page tests open `tenure.bl` of a copy of the durables
model in headless Chrome, with the tests' stand-in client, so that no
request reaches Matsya's service; the test of Enter during an input
method's composition runs the handler of `field.vue` under Node, since the
browser cannot compose."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from workbench_support import (
    MATSYA_TOGGLE,
    VIEWPORT,
    boxes,
    drag_handle,
    layout_record,
    new_tab,
    node_output,
    open_file,
    reveal_in_tree,
    status_settled_on,
    wait_until,
)

# the stage file the page tests open
TENURE_FILE = "declaration/stages/tenure/tenure.bl"
# the inner element of the composer's text area, which Playwright's
# selectors reach through the control's open shadow root
FIELD = ".bl-matsya-field textarea"
# the handle on the composer's top edge
HANDLE = '.bl-handle[data-handle="composer"]'
# the component whose handler the composition test runs
FIELD_VUE = Path(__file__).resolve().parents[1] / "bellman_workbench/field.vue"

# The composer as the page draws it: the boxes of the text area's control,
# its inner element, the field's wrapper, the composer's box, the
# conversation, the foot row, the send control and the handle; the top of
# the line's band, the inner element's top with its border and padding,
# and the line's height; the left of the text, the inner element's left
# with its border and padding; the inner element's scroll and client
# heights and its text; the control's `rows` attribute; whether the handle
# is the box's first child; and the handle's cursor.
COMPOSER_JS = r"""
() => {
  const R = (element) => {
    const r = element.getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom,
             width: r.width, height: r.height };
  };
  const host = document.querySelector('.bl-matsya-field vscode-textarea');
  const inner = host && host.wrappedElement;
  if (!inner) return null;
  const style = getComputedStyle(inner);
  const px = (value) => parseFloat(value);
  const box = document.querySelector('.bl-matsya-body > .bl-matsya-row');
  const handle = box.querySelector(':scope > .bl-handle[data-handle="composer"]');
  return {
    host: R(host),
    inner: R(inner),
    band: R(inner).top + px(style.borderTopWidth) + px(style.paddingTop),
    line: px(style.lineHeight),
    textLeft: R(inner).left + px(style.borderLeftWidth) + px(style.paddingLeft),
    scroll: inner.scrollHeight,
    client: inner.clientHeight,
    value: inner.value,
    rows: host.getAttribute('rows'),
    wrapper: R(box.querySelector('.bl-matsya-field')),
    box: R(box),
    conversation: R(document.querySelector('.bl-matsya-exchanges')),
    foot: R(box.querySelector('.bl-matsya-foot')),
    ask: R(box.querySelector('.bl-matsya-ask')),
    handle: handle ? R(handle) : null,
    first: box.firstElementChild === handle,
    cursor: handle ? getComputedStyle(handle).cursor : null,
  };
}
"""

# whether the keyboard's focus stands on the conversation
FOCUS_ON_CONVERSATION_JS = """
() => !!document.activeElement && document.activeElement.classList.contains('bl-matsya-exchanges')
"""

# The Node module: reads {path, events, draft} on standard input, evaluates the
# script of the component at `path`, which sets `module.exports` to the
# component's options, and calls its method `submit` on a field that
# submits, for each key event of `events`, the event's target holding the
# draft; prints, for each event, the texts the field sent as `submitted`
# and whether the event's default, the new line, was prevented.
SUBMIT_SCRIPT = r"""
import { readFileSync } from "node:fs";

const input = JSON.parse(readFileSync(0, "utf8"));
const source = readFileSync(input.path, "utf8");
const script = source.slice(source.indexOf("<script>") + "<script>".length,
                            source.indexOf("</script>"));
const module = { exports: {} };
new Function("module", script)(module);
const results = input.events.map((given) => {
  const sent = [];
  let prevented = false;
  const field = { submits: true, submitted: (text) => sent.push(text) };
  const event = { ...given, target: { value: input.draft },
                  preventDefault: () => { prevented = true; } };
  module.exports.methods.submit.call(field, event);
  return { sent, prevented };
});
console.log(JSON.stringify(results));
"""

# the text written to the clipboard and pasted, two lines
PASTED = "The first line of a pasted question\nand its second line"


def _open_tenure(browser, server_on, durables_folder):
    """A tab on the durables model with `tenure.bl` open and Matsya's
    column open, the pointer over the folder column; answers the browser
    context, the tab and the page's address."""
    context, tab = new_tab(browser)
    url = server_on(durables_folder)
    open_file(tab, url, TENURE_FILE)
    if not tab.evaluate(
        "() => !!document.querySelector('.bl-window:not([data-folded-matsya]) .bl-matsya')"
    ):
        tab.click(MATSYA_TOGGLE)
    wait_until(lambda: tab.evaluate(COMPOSER_JS) is not None, 20.0, "the composer")
    tab.mouse.move(40, 600)
    tab.wait_for_timeout(300)
    return context, tab, url


def _host_height(tab) -> float:
    """The height of the composer's text area, its control's box."""
    return tab.evaluate(COMPOSER_JS)["host"]["height"]


def _model_files(folder: Path) -> dict:
    """The SHA-256 digest of each file of the model folder `folder`, by its
    path in the folder, the files of its git repository left out."""
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(folder).parts
    }


# --- case 1: lines ---


def test_case_1_shift_enter_begins_a_line_enter_sends_and_the_question_keeps_its_break(
    browser, server_on, durables_folder
):
    """Amendment 07 §6 case 1 (§2 items 1 and 3). In the composer's text
    area Shift+Enter begins a new line and Enter sends the draft: the
    question of two lines is listed with its break, the exchange's text
    holding the newline and its box two lines of 20 px high within 1 px,
    and the field is emptied."""
    question = "What is a perch?\nAnd what is a stage?"
    context, tab, _ = _open_tenure(browser, server_on, durables_folder)
    try:
        field = tab.locator(FIELD)
        field.click()
        tab.keyboard.type("What is a perch?")
        tab.keyboard.press("Shift+Enter")
        tab.keyboard.type("And what is a stage?")
        assert field.input_value() == question
        assert tab.locator(".bl-matsya-question").count() == 0
        tab.keyboard.press("Enter")
        listed = tab.locator(".bl-matsya-question")
        wait_until(lambda: listed.count() == 1, 10.0, "the question listed")
        assert listed.text_content() == question
        # two lines of 20 px within the box's padding of 5 px and its border
        height = boxes(tab, ".bl-matsya-question")[0]["height"]
        assert abs(height - (2 * 20 + 2 * 5 + 2)) <= 1, height
        wait_until(lambda: field.input_value() == "", 5.0, "the field emptied")
        wait_until(lambda: abs(_host_height(tab) - 26) <= 0.5, 5.0, "the field at one line")
        wait_until(
            lambda: tab.locator(".bl-matsya-answer").count() == 1, 20.0, "the stand-in's answer"
        )
        print(
            f"amendment 07 case 1: the question {question!r} listed, its box {height} px, "
            f"the field emptied at {_host_height(tab)} px"
        )
    finally:
        context.close()


def test_case_1_enter_during_an_input_method_s_composition_sends_nothing(node):
    """Amendment 07 §6 case 1, its last sentence (§2 item 1), on the
    handler of `field.vue` run under Node, since the browser cannot compose.
    Enter during an input method's composition, `isComposing`, or with the
    key code 229 of a key the input method reads, sends nothing and leaves
    the key's default to the input method; Shift+Enter sends nothing and
    begins a line; Enter alone sends the draft and begins no line."""
    events = [
        {"key": "Enter", "shiftKey": False, "isComposing": True, "keyCode": 13},
        {"key": "Enter", "shiftKey": False, "isComposing": False, "keyCode": 229},
        {"key": "Enter", "shiftKey": True, "isComposing": False, "keyCode": 13},
        {"key": "Enter", "shiftKey": False, "isComposing": False, "keyCode": 13},
    ]
    draft = "What is a perch?"
    found = node_output(
        node, SUBMIT_SCRIPT, {"path": str(FIELD_VUE), "events": events, "draft": draft}
    )
    assert found == [
        {"sent": [], "prevented": False},
        {"sent": [], "prevented": False},
        {"sent": [], "prevented": False},
        {"sent": [draft], "prevented": True},
    ], found
    print(f"amendment 07 case 1, composition: {json.dumps(found)}")


# --- case 2: growth ---


def test_case_2_the_field_is_one_centered_line_when_empty_and_grows_to_eight_lines(
    browser, server_on, durables_folder
):
    """Amendment 07 §6 case 2 (§2 items 2 and 4). With an empty draft the
    field's control is 26 px high within 0.5 px and carries no `rows`, and
    its one line stands centered within 1 px: the band from the inner
    element's top, with its border and padding, to 18 px below stands as
    far from the control's top as from its foot. Two, five and eight lines
    give 44, 98 and 152 px within 1 px; nine lines give 152 px, the inner
    element's scroll height exceeding its client height; emptied by a send,
    the field is 26 px again. Text pasted from the clipboard, written under
    the browser's clipboard permission and pasted with the primary modifier
    and V, keeps its line break, and the field is two lines high; the
    clipboard's text is written back after the paste."""
    context, tab, url = _open_tenure(browser, server_on, durables_folder)
    try:
        drawn = tab.evaluate(COMPOSER_JS)
        host = drawn["host"]
        assert abs(host["height"] - 26) <= 0.5, host
        assert drawn["rows"] is None, drawn["rows"]
        assert drawn["line"] == 18, drawn["line"]
        above = drawn["band"] - host["top"]
        below = host["bottom"] - (drawn["band"] + drawn["line"])
        assert abs(above - below) <= 1, (above, below)
        field = tab.locator(FIELD)
        heights = {}
        for count, expected in ((2, 44), (5, 98), (8, 152), (9, 152)):
            field.fill("\n".join(f"line {number}" for number in range(1, count + 1)))
            wait_until(
                lambda expected=expected: abs(_host_height(tab) - expected) <= 1,
                5.0,
                f"the field of {count} lines at {expected} px",
            )
            heights[count] = _host_height(tab)
        nine = tab.evaluate(COMPOSER_JS)
        assert nine["scroll"] > nine["client"], (nine["scroll"], nine["client"])
        field.press("Enter")
        wait_until(
            lambda: tab.locator(".bl-matsya-question").count() == 1, 10.0, "the question sent"
        )
        wait_until(lambda: abs(_host_height(tab) - 26) <= 0.5, 5.0, "the field emptied")
        emptied = _host_height(tab)

        context.grant_permissions(["clipboard-read", "clipboard-write"], origin=url)
        held = tab.evaluate("() => navigator.clipboard.readText().catch(() => null)")
        try:
            tab.evaluate("(text) => navigator.clipboard.writeText(text)", PASTED)
            field.focus()
            tab.keyboard.press("ControlOrMeta+V")
            wait_until(lambda: field.input_value() == PASTED, 5.0, "the pasted text")
        finally:
            if held is not None:
                tab.evaluate("(text) => navigator.clipboard.writeText(text)", held)
        wait_until(lambda: abs(_host_height(tab) - 44) <= 1, 5.0, "the pasted two lines")
        print(
            f"amendment 07 case 2: empty {host['height']} px, its line {above} px from the top "
            f"and {below} px from the foot; heights by lines {heights}; nine lines scroll "
            f"{nine['scroll']} over {nine['client']}; emptied {emptied} px; pasted "
            f"{field.input_value()!r} at {_host_height(tab)} px"
        )
    finally:
        context.close()


# --- case 3: the handle ---


def test_case_3_the_handle_sizes_the_field_its_height_is_kept_and_a_double_click_releases_it(
    browser, server_on, durables_folder
):
    """Amendment 07 §6 case 3 (§2 items 5 and 6). A drag upward by 80 px on
    the handle `composer` raises the field by 80 px within 1 px, and the
    conversation gives up the same; the height is kept after the page is
    reloaded on the same folder, within 0.5 px, the test opening `tenure.bl`
    again before measuring, since the durables copy opens on its recipe's
    trellis, which folds Matsya (K-D6); a double click on the handle removes
    it and the field returns to its text's height, one line; a drag of 2,000
    px downward stops at 26 px and one of 2,000 px upward stops where the
    conversation is 80 px, each within 1 px; and the record's
    `sizes.composer` holds the field's height. Where the window is too
    short for the dragged height beside the conversation's 80 px, the field
    gives up the difference (§2 item 5, its last sentence): the conversation
    stays at 80 px within 1 px and the foot row inside the box, and the
    window made high again returns the dragged height within 0.5 px."""
    context, tab, _ = _open_tenure(browser, server_on, durables_folder)
    try:
        before = tab.evaluate(COMPOSER_JS)
        drag_handle(tab, "composer", 0, -80)
        wait_until(
            lambda: abs(_host_height(tab) - (before["host"]["height"] + 80)) <= 1,
            5.0,
            "the field raised by 80 px",
        )
        dragged = tab.evaluate(COMPOSER_JS)
        given = before["conversation"]["height"] - dragged["conversation"]["height"]
        assert abs(given - 80) <= 1, given
        assert abs(dragged["box"]["top"] - (before["box"]["top"] - 80)) <= 1, dragged["box"]
        kept = layout_record(tab, durables_folder)["sizes"]["composer"]
        assert abs(kept - dragged["host"]["height"]) <= 0.5, (kept, dragged["host"])

        tab.reload()
        reveal_in_tree(tab, TENURE_FILE)
        tab.click(f'.bl-tree-file[data-path="{TENURE_FILE}"]')
        wait_until(lambda: status_settled_on(tab, TENURE_FILE), 60.0, "tenure.bl after the reload")
        wait_until(lambda: tab.evaluate(COMPOSER_JS) is not None, 20.0, "the composer")
        wait_until(
            lambda: abs(_host_height(tab) - kept) <= 0.5, 10.0, "the kept height after the reload"
        )
        reloaded = _host_height(tab)

        tab.locator(HANDLE).dblclick()
        wait_until(lambda: abs(_host_height(tab) - 26) <= 0.5, 5.0, "the field's text height")
        record = layout_record(tab, durables_folder)
        assert record is None or "composer" not in record["sizes"], record
        released = _host_height(tab)

        drag_handle(tab, "composer", 0, -100)
        wait_until(lambda: abs(_host_height(tab) - 126) <= 1, 5.0, "the field raised by 100 px")
        drag_handle(tab, "composer", 0, 2000)
        wait_until(lambda: abs(_host_height(tab) - 26) <= 1, 5.0, "the field stopped at 26 px")
        lowest = _host_height(tab)
        assert abs(layout_record(tab, durables_folder)["sizes"]["composer"] - 26) <= 0.5
        drag_handle(tab, "composer", 0, -2000)
        wait_until(
            lambda: abs(tab.evaluate(COMPOSER_JS)["conversation"]["height"] - 80) <= 1,
            5.0,
            "the conversation stopped at 80 px",
        )
        highest = tab.evaluate(COMPOSER_JS)
        record = layout_record(tab, durables_folder)
        assert abs(record["sizes"]["composer"] - highest["host"]["height"]) <= 0.5, (
            record,
            highest["host"],
        )

        tab.set_viewport_size({**VIEWPORT, "height": 400})
        wait_until(
            lambda: tab.evaluate(COMPOSER_JS)["box"]["bottom"] <= 400, 5.0, "the shorter window"
        )
        short = tab.evaluate(COMPOSER_JS)
        assert abs(short["conversation"]["height"] - 80) <= 1, short["conversation"]
        assert 26 - 0.5 <= short["host"]["height"] < highest["host"]["height"], short["host"]
        assert short["foot"]["bottom"] <= short["box"]["bottom"] - 7, (short["foot"], short["box"])
        tab.set_viewport_size(VIEWPORT)
        wait_until(
            lambda: abs(_host_height(tab) - highest["host"]["height"]) <= 0.5,
            5.0,
            "the dragged height in the high window",
        )
        print(
            f"amendment 07 case 3: dragged {before['host']['height']} to "
            f"{dragged['host']['height']} px, the conversation giving {given} px; kept {kept}, "
            f"after the reload {reloaded}; released {released}; least {lowest}; greatest "
            f"{highest['host']['height']} px with the conversation at "
            f"{highest['conversation']['height']} px; sizes.composer "
            f"{record['sizes']['composer']}; in a window 400 px high the field "
            f"{short['host']['height']} px, the conversation "
            f"{short['conversation']['height']} px"
        )
    finally:
        context.close()


# --- case 4: Escape ---


def test_case_4_escape_in_the_field_moves_the_focus_to_the_conversation_and_keeps_the_draft(
    browser, server_on, durables_folder
):
    """Amendment 07 §6 case 4 (§2 item 7). Escape in the field moves the
    keyboard's focus to the conversation, `.bl-matsya-exchanges`, and the
    draft stands: the field keeps its text, and the send control stays
    ready, as Python's draft holds the text."""
    draft = "A draft that Escape keeps"
    context, tab, _ = _open_tenure(browser, server_on, durables_folder)
    try:
        field = tab.locator(FIELD)
        field.click()
        tab.keyboard.type(draft)
        ask = tab.locator(".bl-matsya-ask")
        wait_until(lambda: ask.get_attribute("data-ready") == "true", 5.0, "the draft held")
        tab.keyboard.press("Escape")
        wait_until(
            lambda: tab.evaluate(FOCUS_ON_CONVERSATION_JS), 5.0, "the focus on the conversation"
        )
        tab.wait_for_timeout(500)
        assert field.input_value() == draft
        assert ask.get_attribute("data-ready") == "true"
        assert tab.locator(".bl-matsya-question").count() == 0
        print(
            f"amendment 07 case 4: the focus on the conversation, the field holding "
            f"{field.input_value()!r}"
        )
    finally:
        context.close()


# --- case 5: the geometry that stands ---


def test_case_5_the_text_stands_on_the_box_s_text_edge_and_the_handle_on_its_top_border(
    browser, server_on, durables_folder
):
    """Amendment 07 §6 case 5 (§2 items 2 and 5). With an empty draft the
    field's text stands on the box's text edge, 8 px inside its outer edge,
    within 1 px; the send control stands on the foot row's axis within 1
    px, its right edge 8 px inside the box's within 1 px; the handle
    `composer` is the box's first child, 7 px high, centered on the box's
    1-px top border within 1 px and as wide as the box within its side
    borders, with the cursor `row-resize`. At eight lines the box stands at
    the column's foot as before, the field 152 px high."""
    context, tab, _ = _open_tenure(browser, server_on, durables_folder)
    try:
        drawn = tab.evaluate(COMPOSER_JS)
        box, ask, foot, handle = drawn["box"], drawn["ask"], drawn["foot"], drawn["handle"]
        edge = drawn["textLeft"] - box["left"]
        assert abs(edge - 8) <= 1, edge
        axis = foot["top"] + foot["height"] / 2
        assert abs((ask["top"] + ask["height"] / 2) - axis) <= 1, (ask, foot)
        assert abs((box["right"] - 8) - ask["right"]) <= 1, (ask, box)
        assert drawn["first"] and handle is not None, drawn
        assert abs(handle["height"] - 7) <= 0.5, handle
        assert abs((handle["top"] + handle["height"] / 2) - (box["top"] + 0.5)) <= 1, (handle, box)
        assert abs(handle["width"] - (box["width"] - 2)) <= 1, (handle, box)
        assert drawn["cursor"] == "row-resize", drawn["cursor"]
        tab.locator(FIELD).fill("\n".join(f"line {number}" for number in range(1, 9)))
        wait_until(lambda: abs(_host_height(tab) - 152) <= 1, 5.0, "the field of eight lines")
        eight = tab.evaluate(COMPOSER_JS)
        assert abs(eight["box"]["bottom"] - box["bottom"]) <= 0.5, (eight["box"], box)
        assert abs(eight["textLeft"] - eight["box"]["left"] - 8) <= 1, eight["textLeft"]
        print(
            f"amendment 07 case 5: the text {edge} px inside the box, the send control's right "
            f"edge {box['right'] - ask['right']} px inside it, the handle {handle['width']} × "
            f"{handle['height']} px at {handle['top'] - box['top']} px from the box's top; "
            f"at eight lines the box {eight['box']['height']} px high"
        )
    finally:
        context.close()


# --- case 6: the record ---


def test_case_6_the_dragged_height_is_kept_in_the_browser_s_storage_and_in_no_model_file(
    browser, server_on, durables_folder
):
    """Amendment 07 §6 case 6 (§2 item 6; §4). After a drag of the handle
    `composer`, the record window.vue keeps in the browser's storage under
    the folder's path holds the field's height under `sizes.composer`,
    within 0.5 px, and no file of the model folder is written or changed by
    the drag or by its release."""
    context, tab, _ = _open_tenure(browser, server_on, durables_folder)
    try:
        files = _model_files(durables_folder)
        drag_handle(tab, "composer", 0, -60)
        wait_until(lambda: abs(_host_height(tab) - 86) <= 1, 5.0, "the field dragged to 86 px")
        record = layout_record(tab, durables_folder)
        height = _host_height(tab)
        assert abs(record["sizes"]["composer"] - height) <= 0.5, (record, height)
        tab.locator(HANDLE).dblclick()
        wait_until(lambda: abs(_host_height(tab) - 26) <= 0.5, 5.0, "the height released")
        tab.wait_for_timeout(500)
        assert _model_files(durables_folder) == files
        print(
            f"amendment 07 case 6: sizes.composer {record['sizes']['composer']} for a field of "
            f"{height} px; {len(files)} model files unchanged"
        )
    finally:
        context.close()
