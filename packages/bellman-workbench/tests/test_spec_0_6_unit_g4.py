"""The tests of unit G4 of specification 0.6, design pass 16, the Matsya
column to the standard of Cursor's agent column (the development
repository's brief of unit G4, the Matsya column, and its record of design
pass 16; amendment 06 of spec 0.4, §2 items 1, 3, 6, 25 and 28). Each test is named by the acceptance item of the brief it
checks. The page tests open `tenure.bl` of a copy of the durables model,
with the tests' stand-in client; item 2 reads the colors of a screenshot's
pixels, decoded in the page by a canvas."""

from __future__ import annotations

import base64
import hashlib
import json

import ipyvue
import solara
from workbench_support import (
    MATSYA_TOGGLE,
    boxes,
    choose_option,
    new_tab,
    open_file,
    returned_job,
    stub_calls,
    stub_job,
    stub_turn,
    wait_until,
)

from bellman_workbench import matsya_window, matsya_work, model, recipe

# the stage file the page tests open
TENURE_FILE = "declaration/stages/tenure/tenure.bl"

# The pixels of a PNG screenshot, decoded in the page by a canvas: its
# width, its height and each pixel's red, green and blue, row by row.
PIXELS_JS = r"""
async (data) => {
  const image = new Image();
  image.src = 'data:image/png;base64,' + data;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = image.width;
  canvas.height = image.height;
  const context = canvas.getContext('2d');
  context.drawImage(image, 0, 0);
  const found = context.getImageData(0, 0, image.width, image.height).data;
  const pixels = [];
  for (let i = 0; i < found.length; i += 4) pixels.push([found[i], found[i + 1], found[i + 2]]);
  return { width: image.width, height: image.height, pixels };
}
"""

# The colors the page's tokens give, as the browser computes them, and the
# hairline composited over the ground: `--bl-hairline` is ice-2 at 18
# percent over a transparent ground.
TOKENS_JS = r"""
() => {
  const probe = document.createElement('span');
  document.body.append(probe);
  const read = (token) => {
    probe.style.color = `var(${token})`;
    return getComputedStyle(probe).color;
  };
  const values = { ground: read('--bl-ground'), raised: read('--bl-raised'),
                   hairline: read('--bl-hairline'), border: read('--bl-control-border') };
  probe.remove();
  return values;
}
"""


def _rgb(text: str) -> tuple:
    """The red, green, blue and alpha of a computed color, `rgb(…)`,
    `rgba(…)` or `color(srgb …)`."""
    inside = text[text.index("(") + 1 : text.rindex(")")]
    if text.startswith("color("):
        parts = inside.replace("srgb", "").replace("/", " ").split()
        values = [float(part) * 255 for part in parts[:3]]
        alpha = float(parts[3]) if len(parts) > 3 else 1.0
        return (*values, alpha)
    parts = [float(part) for part in inside.replace(",", " ").replace("/", " ").split()]
    return (*parts[:3], parts[3] if len(parts) > 3 else 1.0)


def _over(ink: tuple, ground: tuple) -> tuple:
    """The color `ink`, with its alpha, composited over the opaque `ground`."""
    alpha = ink[3]
    return tuple(round(ink[i] * alpha + ground[i] * (1 - alpha)) for i in range(3))


def _near(found, expected, tolerance: int = 2) -> bool:
    """Whether two colors differ by at most `tolerance` in each channel."""
    return all(abs(a - b) <= tolerance for a, b in zip(found, expected))


def _row(tab, x0: int, x1: int, y: int) -> list:
    """The colors of the pixels from x0 to x1, exclusive, on the row y of a
    screenshot of the window at device scale 1."""
    png = tab.screenshot(clip={"x": x0, "y": y, "width": x1 - x0, "height": 1})
    read = tab.evaluate(PIXELS_JS, base64.b64encode(png).decode("ascii"))
    return [tuple(pixel) for pixel in read["pixels"]]


def _open_tenure(browser, server_on, durables_folder):
    """A tab on the durables model with `tenure.bl` open and Matsya's
    column open, the pointer over the folder column."""
    context, tab = new_tab(browser)
    url = server_on(durables_folder)
    open_file(tab, url, TENURE_FILE)
    if not tab.evaluate(
        "() => !!document.querySelector('.bl-window:not([data-folded-matsya]) .bl-matsya')"
    ):
        tab.click(MATSYA_TOGGLE)
    wait_until(
        lambda: tab.evaluate(
            "() => !!document.querySelector('.bl-matsya-field vscode-textarea')"
        ),
        20.0,
        "the composer",
    )
    tab.mouse.move(40, 600)
    tab.wait_for_timeout(300)
    return context, tab


def test_item_2_the_column_stands_on_the_page_s_ground_and_one_hairline_separates_it(
    browser, server_on, durables_folder
):
    """Acceptance item 2 (S0-9; amendment 06 §2 item 28; record §3 rule 1),
    read from the colors of a screenshot's pixels at device scale 1. The
    column's ground is the window's, `--bl-ground`, across its empty
    conversation; between the graph column's right edge and the column's
    text edge exactly one pixel differs from the ground, the divider at the
    middle of the column gap, in `--bl-hairline` composited over the
    ground, on the row of the head, of the conversation and of the composer;
    no rule stands under the head; and the main bar's hairline and the
    status line's reach the divider across the gap."""
    context, tab = _open_tenure(browser, server_on, durables_folder)
    try:
        tokens = tab.evaluate(TOKENS_JS)
        ground = _rgb(tokens["ground"])[:3]
        hairline = _over(_rgb(tokens["hairline"]), ground)
        column = boxes(tab, ".bl-matsya")[0]
        view = boxes(tab, ".bl-view")[0]
        status = boxes(tab, ".bl-status")[0]
        gap = tab.evaluate(
            "() => parseFloat(getComputedStyle(document.querySelector('.bl-window')).columnGap)"
        )
        left, right = round(column["left"]), round(column["left"] + column["width"])
        divider = round(column["left"] - gap / 2)
        view_right = round(view["left"] + view["width"])
        # the column's ground across its empty conversation
        for y in (200, 500, 800):
            found = _row(tab, left, right, y)
            assert all(_near(pixel, ground) for pixel in found), (
                y,
                sorted(set(found))[:4],
                ground,
            )
        # one pixel of hairline between the graph column and the text edge
        for y in (18, 500, round(boxes(tab, ".bl-matsya-row")[0]["top"]) + 4):
            found = _row(tab, view_right, left + 12, y)
            differing = [
                view_right + i for i, pixel in enumerate(found) if not _near(pixel, ground)
            ]
            assert differing == [divider], (y, differing, divider)
            assert _near(found[divider - view_right], hairline), (
                y,
                found[divider - view_right],
                hairline,
            )
        # no rule under the head: the head's last row and the row below it
        for y in (35, 36):
            found = _row(tab, divider + 1, right, y)
            assert all(_near(pixel, ground) for pixel in found), (y, sorted(set(found))[:4])
        # the main bar's hairline and the status line's carried to the divider
        for y in (35, round(status["top"])):
            found = _row(tab, view_right, divider + 1, y)
            assert all(_near(pixel, hairline) for pixel in found), (
                y,
                sorted(set(found))[:4],
                hairline,
            )
        print(f"unit G4 item 2: ground {ground}, hairline {hairline} at x {divider}")
    finally:
        context.close()


# The composer as the page draws it: the box's style; its children's
# classes in order, the first child's data-handle, and their boxes; the
# send control's box and its foot row's; the field's face and size, read
# on the inner element of its text area (amendment 07 of spec 0.4); the
# chips' texts and faces.
COMPOSER_JS = r"""
() => {
  const R = (element) => {
    const r = element.getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom,
             width: r.width, height: r.height };
  };
  const box = document.querySelector('.bl-matsya-body > .bl-matsya-row');
  if (!box) return null;
  const style = getComputedStyle(box);
  const host = box.querySelector('.bl-matsya-field vscode-textarea');
  const input = host && host.shadowRoot && host.shadowRoot.querySelector('textarea');
  const foot = box.querySelector('.bl-matsya-foot');
  const ask = box.querySelector('.bl-matsya-ask');
  const chips = Array.from(box.querySelectorAll('.bl-matsya-context .bl-matsya-chip'))
    .map((chip) => ({
      kind: chip.getAttribute('data-kind'), text: chip.textContent.trim(),
      face: getComputedStyle(chip).fontFamily.split(',')[0].replace(/"/g, '').trim(),
      size: parseFloat(getComputedStyle(chip).fontSize),
    }));
  const face = (element) => element ? [
    getComputedStyle(element).fontFamily.split(',')[0].replace(/"/g, '').trim(),
    parseFloat(getComputedStyle(element).fontSize)] : null;
  return {
    box: R(box),
    border: [style.borderTopWidth, style.borderRightWidth,
             style.borderBottomWidth, style.borderLeftWidth],
    borderColor: style.borderTopColor,
    background: style.backgroundColor,
    radius: style.borderTopLeftRadius,
    children: Array.from(box.children).map((child) => child.className),
    handle: box.firstElementChild ? box.firstElementChild.getAttribute('data-handle') : null,
    rows: Array.from(box.children).map(R),
    foot: foot ? R(foot) : null,
    ask: ask ? R(ask) : null,
    askInFoot: !!(ask && foot && foot.contains(ask)),
    lastInFoot: !!(foot && foot.lastElementChild && foot.lastElementChild.contains(ask)),
    field: face(input),
    chips,
    column: R(document.querySelector('.bl-matsya')),
  };
}
"""


def test_item_3_the_composer_is_one_bordered_box_with_the_context_row_above_and_the_foot_row_below(
    browser, server_on, durables_folder
):
    """Acceptance item 3 (amendment 06 §2 items 1 and 28; record §3 rule
    7). The composer `.bl-matsya-row` is one box: a 1-px border in
    `--bl-control-border`, radius 4, on `--bl-raised`, its outer edge on
    the column's text edge, 12 px in. Its children, in order, are the
    handle `composer` on its top edge (amendment 07 of spec 0.4, §2 item 5)
    and its rows, the context `.bl-matsya-context`, the field and the foot
    row `.bl-matsya-foot`, the context above the field and the foot row
    below it; the send control
    `.bl-matsya-ask` is the foot row's last control, at its right end, 8 px
    inside the box's right edge, on the foot row's axis. The field's text
    is in Label, Archivo at 13 px; the chips are in Code small, IBM Plex
    Mono at 11 px, and name the recipe `spec.yml` with `saved`, the
    session `not connected` and the service."""
    context, tab = _open_tenure(browser, server_on, durables_folder)
    try:
        tokens = tab.evaluate(TOKENS_JS)
        drawn = tab.evaluate(COMPOSER_JS)
        assert drawn is not None
        assert drawn["border"] == ["1px"] * 4, drawn["border"]
        assert _near(_rgb(drawn["borderColor"])[:3], _rgb(tokens["border"])[:3], 1), drawn[
            "borderColor"
        ]
        assert _rgb(drawn["borderColor"])[3] == _rgb(tokens["border"])[3], drawn["borderColor"]
        assert _rgb(drawn["background"])[:3] == _rgb(tokens["raised"])[:3], drawn["background"]
        assert drawn["radius"] == "4px", drawn["radius"]
        box, column = drawn["box"], drawn["column"]
        assert abs(box["left"] - (column["left"] + 12)) <= 0.5, (box, column)
        assert abs(box["right"] - (column["right"] - 12)) <= 0.5, (box, column)
        assert drawn["children"] == [
            "bl-handle",
            "bl-matsya-context",
            "bl-field bl-matsya-field",
            "bl-matsya-foot",
        ], drawn
        assert drawn["handle"] == "composer", drawn
        _, context_row, field_row, foot_row = drawn["rows"]
        assert (
            context_row["bottom"] <= field_row["top"] and field_row["bottom"] <= foot_row["top"]
        ), drawn["rows"]
        ask, foot = drawn["ask"], drawn["foot"]
        assert drawn["askInFoot"] and drawn["lastInFoot"], drawn
        assert abs((box["right"] - 8) - ask["right"]) <= 1, (ask, box)
        assert abs((ask["top"] + ask["height"] / 2) - (foot["top"] + foot["height"] / 2)) <= 1, (
            ask,
            foot,
        )
        assert drawn["field"] == ["Archivo", 13], drawn["field"]
        kinds = {chip["kind"]: chip for chip in drawn["chips"]}
        assert {"source", "session", "service"} <= set(kinds), drawn["chips"]
        assert kinds["source"]["text"] == "spec.ymlsaved", kinds["source"]
        assert kinds["session"]["text"] == "not connected", kinds["session"]
        assert all(
            (chip["face"], chip["size"]) == ("IBM Plex Mono", 11) for chip in drawn["chips"]
        ), drawn["chips"]
        print(
            f"unit G4 item 3: the composer {box['width']} × {box['height']} px, "
            f"chips {[chip['text'] for chip in drawn['chips']]}"
        )
    finally:
        context.close()


# --- acceptance item 5: a job's five parts, and the citations ---

CALIBRATION = "declaration/calibration/durables.yml"
HIGH, LOW = "τ: 0.12", "τ: 0.08"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _connected(folder) -> matsya_work.Session:
    """Connects the folder to the stand-in's service as the client's
    `project init` records a connection, `.bellman-matsya/project.json`,
    and answers the folder's session."""
    project = folder.root / matsya_work.PROJECT_FILE
    project.parent.mkdir(parents=True, exist_ok=True)
    held = {"session": _sha256(folder.root.name)[:32], "server": "http://127.0.0.1:8710"}
    project.write_text(json.dumps(held), encoding="utf-8")
    return matsya_work.connected_session(folder)


def _submitted(folder, session) -> int:
    """The number of a job of the folder's recipe that unit G2's adapter
    prepared and submitted, so that the folder holds its request record."""
    source = recipe.Source("recipe", "declaration/spec.yml")
    prepared = matsya_work.prepare(folder, source, "recipe", session, 1)
    work = matsya_work.submit(folder, prepared.path, session)
    return int(work.record["accepted"].removeprefix("job-"))


def _texts_of(rendered, class_: str) -> list:
    """The texts of the rendered elements of the class `class_`, in order."""
    found = rendered.find(ipyvue.Html, class_=class_)
    return ["".join(str(child) for child in widget.children) for widget in found.widgets]


def _click(rendered, class_: str) -> None:
    """Clicks the one rendered button of the class `class_`."""
    found = rendered.find(ipyvue.Html, tag="button", class_=class_)
    found.assert_single()
    found.widget.fire_event("click", {})


def test_item_5_a_job_s_result_shows_its_five_parts_apart_and_its_files_are_reached_from_it(
    matsya_durables, app_state, matsya_state
):
    """Acceptance item 5, first part (amendment 06 §2 items 3, 20, 22, 23
    and 25). In a folder connected to Matsya, a job unit G2's adapter
    submitted and the stand-in ended, with a changed calibration, stands in
    the column as a message of its own: its number and state, then its
    five parts apart, in order: `converged`, the one comment on the prose,
    the one unresolved assumption, `not downloaded` and `not run`, each
    detail under its part; and the actions `Discuss`, which selects the job
    as the one the conversation discusses and names it in the composer's
    chips, and `Download returned files`. The
    download writes the saved copy, after which the construction and
    binding of the copy reads `constructed`, with its two declared terminal
    inputs, and the actions are `Open returned files`
    and `Replace model files…`. The plan names the calibration's
    destination with its line difference; `Replace model files` writes it,
    and `Commit…` stands for the recorded adoption."""
    from bellman_workbench import app

    folder = model.open_folder(matsya_durables)
    session = _connected(folder)
    number = _submitted(folder, session)
    job = returned_job(folder.root, session.id, number, 2, {CALIBRATION: (HIGH, LOW)})
    job["record"] = {
        "questions": ["Which transition probabilities does the paper give?"],
        "paper_source_check": [{"comment": "The prose names no borrowing limit."}],
    }
    stub_job(job)
    app_state(folder.root)
    _, rendered = solara.render(
        matsya_window.MatsyaWindow(
            app._session(),
            app.Field,
            app.ToolbarButton,
            app.TextButton,
            app.matsya_context(),
            app.MATSYA_ACTIONS,
        ),
        handle_error=False,
    )
    try:
        wait_until(lambda: job["id"] in matsya_state.jobs.value, 20.0, "the job read")
        message = rendered.find(ipyvue.Html, class_="bl-matsya-job").wait_for(timeout=10)
        assert message.widget.attributes["data-job"] == job["id"]
        parts = rendered.find(ipyvue.Html, class_="bl-matsya-part")
        assert [widget.attributes["data-part"] for widget in parts.widgets] == list(
            matsya_window.PART_NAMES
        )
        assert _texts_of(rendered, "bl-matsya-part-value") == [
            "converged",
            "1",
            "1",
            "not downloaded",
            "not run",
        ]
        assert _texts_of(rendered, "bl-matsya-part-detail") == [
            "The prose names no borrowing limit.",
            "Which transition probabilities does the paper give?",
        ]
        _click(rendered, "bl-text-button bl-matsya-discuss-job")
        assert matsya_state.discussed.value == job["id"]
        chips = rendered.find(ipyvue.Html, tag="li", class_="bl-matsya-chip bl-code-small")
        assert "job" in [widget.attributes["data-kind"] for widget in chips.widgets]
        _click(rendered, "bl-text-button bl-matsya-download")
        view = matsya_state.jobs.value[job["id"]]
        assert view.copy is not None and (folder.root / view.copy / CALIBRATION).is_file()
        rendered.find(
            ipyvue.Html, tag="button", class_="bl-text-button bl-matsya-replace"
        ).wait_for(timeout=10)
        values = _texts_of(rendered, "bl-matsya-part-value")
        assert values[3] == "constructed", values
        details = _texts_of(rendered, "bl-matsya-part-detail")
        assert details[2:] == [
            "External terminal input V[>] · bequest", "External terminal input age[>] · bequest",
        ]
        rendered.find(
            ipyvue.Html, tag="button", class_="bl-text-button bl-matsya-open-copy"
        ).assert_single()
        _click(rendered, "bl-text-button bl-matsya-replace")
        destinations = _texts_of(rendered, "bl-matsya-plan-destination bl-code-small")
        assert CALIBRATION in destinations, destinations
        differences = "\n".join(_texts_of(rendered, "bl-matsya-plan-difference bl-code-small"))
        assert "-  τ: 0.12" in differences and "+  τ: 0.08" in differences, differences
        assert (folder.root / CALIBRATION).read_text(encoding="utf-8").count(HIGH) == 1
        assert _texts_of(rendered, "bl-matsya-refusal") == [], _texts_of(
            rendered, "bl-matsya-refusal"
        )
        _click(rendered, "bl-text-button bl-matsya-replace-now")
        assert (folder.root / CALIBRATION).read_text(encoding="utf-8").count(LOW) == 1
        rendered.find(
            ipyvue.Html, tag="button", class_="bl-text-button bl-matsya-commit"
        ).wait_for(timeout=10)
        print(f"unit G4 item 5: {job['id']} parts {values}, copy {view.copy}")
    finally:
        rendered.close()
        matsya_state.clear_conversation()


def test_item_5_a_citation_opens_its_destination_or_names_it_unavailable(
    scratch_durables, matsya_state
):
    """Acceptance item 5, second part (amendment 06 §2 item 6). A path of
    the model folder opens that file at the line its location names; a
    retrieved passage opens its quotation with its path and page; a job's
    returned file is `not downloaded` until the folder holds a saved copy of
    the job, and then opens that copy; any other path is `unavailable`. In
    the column, an answer's passage of a model file is a button whose click
    asks the page to open the file at its line, a retrieved passage opens
    its quotation below its row, and the passage of an unresolved
    destination is text, with its state, which nothing opens."""
    folder = model.open_folder(scratch_durables)
    session = _connected(folder)
    tenure = "declaration/stages/tenure/tenure.bl"
    cited_file = {"path": tenure, "location": {"line": 41}}
    passage = {
        "identity": {"source": "index"},
        "path": "literature/stokey-lucas-prescott-1989.txt",
        "quote": "The value function is the unique fixed point of the operator.",
        "location": {"page": 12},
    }
    returned_file = {
        "identity": {"source": "job"},
        "location": {"job": "job-3", "output": "tenure.bl"},
    }
    elsewhere = {"path": "docs/overview/03-language.md"}
    root = folder.root
    assert matsya_window.resolve(root, cited_file) == matsya_window.Citation("file", tenure, 41)
    assert matsya_window.resolve(root, passage) == matsya_window.Citation(
        "passage",
        quote=passage["quote"],
        source="literature/stokey-lucas-prescott-1989.txt · p. 12",
    )
    assert matsya_window.resolve(root, returned_file) == matsya_window.Citation(
        "unavailable", state="not downloaded"
    )
    assert matsya_window.resolve(root, elsewhere) == matsya_window.Citation(
        "unavailable", state="unavailable"
    )
    returned_job(root, session.id, 3, 2)
    copy = matsya_work.download(folder, session, "job-3")
    assert copy.written, copy.refusal
    assert matsya_window.resolve(root, returned_file) == matsya_window.Citation(
        "copy", f"{copy.path}/{tenure}"
    )

    opened_files, opened_copies = [], []
    actions = matsya_window.Actions(
        folder=lambda: folder,
        open_file=lambda path, line: opened_files.append((path, line)),
        open_copy=opened_copies.append,
        buffers=dict,
        open_commit=lambda record: None,
    )
    from bellman_workbench import app

    names = (f"{tenure}", "literature/stokey-lucas-prescott-1989.txt — 9.2", elsewhere["path"])
    matsya_state.exchanges.value = (
        matsya_window.Exchange(
            "Which line takes the expectation?",
            "Line 41.",
            names,
            (cited_file, passage, elsewhere),
        ),
    )
    _, rendered = solara.render(
        matsya_window.MatsyaWindow(
            "folder-digest", app.Field, app.ToolbarButton, app.TextButton, None, actions
        ),
        handle_error=False,
    )
    try:
        citations = rendered.find(ipyvue.Html, class_="bl-matsya-citation")
        assert [widget.attributes["data-kind"] for widget in citations.widgets] == [
            "file",
            "passage",
            "unavailable",
        ]
        assert _texts_of(rendered, "bl-matsya-passage bl-code-small") == list(names)
        buttons = rendered.find(ipyvue.Html, tag="button", class_="bl-text-button bl-matsya-cited")
        assert len(buttons.widgets) == 2
        buttons.widgets[0].fire_event("click", {})
        assert opened_files == [(tenure, 41)]
        buttons.widgets[1].fire_event("click", {})
        quote = rendered.find(ipyvue.Html, class_="bl-matsya-quote-text").wait_for(timeout=5)
        assert quote.widget.children == [passage["quote"]]
        assert _texts_of(rendered, "bl-matsya-cited-state") == ["unavailable"]
        print(f"unit G4 item 5: opened {opened_files}, the passage quoted, one unavailable")
    finally:
        rendered.close()


# --- the two steps of a build (decision SG4-7) ---

TENURE = "declaration/stages/tenure/tenure.bl"


def test_a_build_is_two_steps_the_request_and_then_the_reviewed_material_with_one_action(
    matsya_durables, app_state, matsya_state, tmp_path, monkeypatch
):
    """Review the prompt and a saved file version before sending either."""
    from bellman_workbench import app

    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    folder = model.open_folder(matsya_durables)
    _connected(folder)
    app_state(folder.root)
    disk = (folder.root / TENURE).read_text(encoding="utf-8")
    app.buffers.value = {TENURE: {"text": disk + "\n", "digest": _sha256(disk)}}
    _, rendered = solara.render(
        matsya_window.MatsyaWindow(
            app._session(),
            app.Field,
            app.ToolbarButton,
            app.TextButton,
            app.matsya_context(),
            app.MATSYA_ACTIONS,
        ),
        handle_error=False,
    )
    try:
        matsya_state.set_kind(matsya_window.BUILD)
        matsya_state.set_target("Recipe")
        matsya_state.send("Lower the housing cost τ to 0.08")
        wait_until(
            lambda: matsya_state.builds.value.get(0, matsya_window.BuildView()).prepared,
            20.0,
            "the build prepared",
        )
        calls = [entry for entry in stub_calls(log) if isinstance(entry, list)]
        assert not any(call[:2] in (["session", "add"], ["job", "submit-prepared"])
                       for call in calls), calls
        prepared = matsya_state.builds.value[0].prepared
        assert prepared.record is None and TENURE in prepared.differences, prepared
        # the column is drawn again by the task's thread once the build is
        # prepared, so that its buttons are waited for
        choices = rendered.find(
            ipyvue.Html, tag="button", class_="bl-text-button bl-matsya-choice"
        ).wait_for(timeout=10)
        assert [widget.children[-1] for widget in choices.widgets] == [
            "Save",
            "Saved version",
            "Displayed text",
        ]
        choices.widgets[1].fire_event("click", {})
        record = matsya_state.builds.value[0].prepared.record
        assert record is not None and record["choice"] == "saved version", record
        assert _texts_of(rendered, "bl-small")[-1] == "Build declaration · Recipe"
        what = _texts_of(rendered, "bl-matsya-build-what bl-code-small")
        assert what[0] == f"spec.yml · {len(record['files'])} files", what
        assert not any(call[:2] == ["job", "submit-prepared"] for call in calls)
        _click(rendered, "bl-text-button bl-matsya-submit")
        wait_until(
            lambda: any(view.job for view in matsya_state.builds.value.values()),
            20.0, "the submitted job",
        )
        calls = [entry for entry in stub_calls(log) if isinstance(entry, list)]
        assert [call[:2] for call in calls].count(["session", "add"]) == 1, calls
        assert [call[:2] for call in calls].count(["job", "submit-prepared"]) == 1, calls
        job = matsya_state.builds.value[0].job
        assert job in matsya_state.jobs.value
        assert [exchange.kind for exchange in matsya_state.exchanges.value] == ["build", "job"]
        assert (folder.root / TENURE).read_text(encoding="utf-8") == disk
        print(f"unit G4 build: {what}, {job} submitted once")
    finally:
        rendered.close()
        app.buffers.value = {}


# --- Search sources and Connect this folder to Matsya ---


def _column(app):
    """The column as `app.Page` draws it, its context read at each drawing,
    so that a connection made in it names the new session."""

    @solara.component
    def Column():
        return matsya_window.MatsyaWindow(
            app._session(),
            app.Field,
            app.ToolbarButton,
            app.TextButton,
            app.matsya_context(),
            app.MATSYA_ACTIONS,
        )

    return Column()


def test_search_sources_starts_no_turn_and_no_job_and_a_passage_is_discussed_in_chat(
    scratch_durables, app_state, matsya_state, tmp_path, monkeypatch
):
    """Amendment 06 §2 item 8. `Search sources` in the collection
    `literature` runs the client's `search` alone, with no turn and no job:
    the stand-in's log holds one `search` naming `--collections literature`
    and the query after `--`. The column lists the literature passage the
    stand-in's index answers, under `Search sources · literature`; its
    quotation opens below its row with its collection, path and page; and
    `Discuss` puts the quotation and the passage's name in the field as the
    start of a question, the kind of request `Ask`."""
    from bellman_workbench import app

    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    app_state(model.open_folder(scratch_durables).root)
    _, rendered = solara.render(_column(app), handle_error=False)
    try:
        matsya_state.set_kind(matsya_window.SEARCH)
        matsya_state.set_collection("literature")
        matsya_state.send("Euler equation with a borrowing constraint")
        wait_until(lambda: matsya_state.exchanges.value[-1].answer is not None, 20.0, "the search")
        # the task's thread draws the column again once the search answered
        rendered.find(ipyvue.Html, tag="button", class_="bl-text-button bl-matsya-cited").wait_for(
            timeout=10
        )
        calls = [entry for entry in stub_calls(log) if isinstance(entry, list)]
        assert calls == [
            [
                "search",
                "--json",
                "--collections",
                "literature",
                "--",
                "Euler equation with a borrowing constraint",
            ]
        ], calls
        assert "Search sources · literature" in _texts_of(rendered, "bl-small")
        names = _texts_of(rendered, "bl-matsya-passage bl-code-small")
        assert names == ["literature/deaton-1991.txt — 2 The model"], names
        _click(rendered, "bl-text-button bl-matsya-cited")
        quote = rendered.find(ipyvue.Html, class_="bl-matsya-quote-text").wait_for(timeout=5)
        assert quote.widget.children[0].startswith("When the constraint binds")
        assert _texts_of(rendered, "bl-matsya-quote-source bl-code-small") == [
            "literature · literature/deaton-1991.txt · p. 1225"
        ]
        _click(rendered, "bl-text-button bl-matsya-discuss")
        assert matsya_state.kind.value == matsya_window.ASK
        assert matsya_state.draft.value.startswith("“When the constraint binds")
        assert matsya_state.draft.value.endswith("(literature/deaton-1991.txt — 2 The model) ")
        print(f"unit G4 search: {calls[0][:4]}, {names}")
    finally:
        rendered.close()


def test_connect_this_folder_to_matsya_writes_the_client_s_project_files_and_names_the_session(
    scratch_durables, app_state, matsya_state, tmp_path, monkeypatch
):
    """Amendment 06 §2 items 3, 9 and 14; D-1. A folder not connected
    shows `Connect this folder to Matsya` at the head of the conversation,
    with the folder's name, its `economics.md` and the service it reaches
    under it, and the session's chip reads `not connected`. The click runs
    the client's `project init` on the folder once, which writes
    `.bellman-matsya/project.json`; the button leaves the conversation, and
    the session's chip names the session after the folder."""
    from bellman_workbench import app

    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    folder = model.open_folder(scratch_durables)
    app_state(folder.root)
    _, rendered = solara.render(_column(app), handle_error=False)
    try:
        sent = _texts_of(rendered, "bl-matsya-connect-sent bl-code-small")
        assert len(sent) == 1 and sent[0].startswith("durables · economics.md · "), sent
        session_chip = rendered.find(ipyvue.Html, tag="li", class_="bl-matsya-chip bl-code-small")
        assert "not connected" in [
            "".join(map(str, child.children))
            for widget in session_chip.widgets
            if widget.attributes["data-kind"] == "session"
            for child in widget.children
            if hasattr(child, "children")
        ]
        _click(rendered, "bl-text-button bl-matsya-connect-button")
        calls = [entry for entry in stub_calls(log) if isinstance(entry, list)]
        assert calls == [["project", "init", str(folder.root), "--json"]], calls
        assert matsya_work.project(folder) is not None
        wait_until(
            lambda: not rendered.find(
                ipyvue.Html, class_="bl-matsya-connect-sent bl-code-small"
            ).widgets,
            10.0,
            "the connection's button gone",
        )
        values = _texts_of(rendered, "bl-matsya-chip-value")
        assert "durables" in values, values
        print(f"unit G4 connect: {calls[0][:2]}, chips {values}")
    finally:
        rendered.close()


def test_a_job_that_has_not_ended_is_followed_until_its_result_stands(
    matsya_durables, app_state, matsya_state
):
    """Amendment 06 §2 items 18 and 20. A job submitted and still queued
    stands as a message with its state and no part; the column reads it
    again every `FOLLOW_SECONDS`, and once the service's answer holds a
    result its five parts stand, with no file written by the following."""
    from bellman_workbench import app

    folder = model.open_folder(matsya_durables)
    session = _connected(folder)
    number = _submitted(folder, session)
    app_state(folder.root)
    _, rendered = solara.render(_column(app), handle_error=False)
    try:
        wait_until(lambda: f"job-{number}" in matsya_state.jobs.value, 20.0, "the job read")
        rendered.find(ipyvue.Html, class_="bl-matsya-job").wait_for(timeout=10)
        assert not rendered.find(ipyvue.Html, class_="bl-matsya-part").widgets
        before = sorted(path for path in folder.root.rglob("*") if path.is_file())
        returned_job(folder.root, session.id, number, 2)
        wait_until(
            lambda: len(rendered.find(ipyvue.Html, class_="bl-matsya-part").widgets) == 5,
            3 * matsya_window.FOLLOW_SECONDS,
            "the five parts after the job ended",
        )
        assert sorted(path for path in folder.root.rglob("*") if path.is_file()) == before
        print(f"unit G4 following: job-{number} read again until its result stood")
    finally:
        rendered.close()
        matsya_state.clear_conversation()


def test_item_2_the_ground_and_the_hairline_hold_with_a_conversation_and_in_the_build_mode(
    browser, server_on, durables_folder
):
    """Acceptance item 2 in the column's other states, read from the colors
    of a screenshot's pixels at device scale 1: with a question answered
    and the composer in the mode `Build declaration`, the column's ground
    under its conversation is the window's, exactly one pixel of hairline
    stands between the graph column and the column's text edge on the rows
    of the head, of the conversation and of the composer, and the composer's
    border, the focus elsewhere, is `--bl-control-border` over the raised
    surface, the ground just outside it."""
    context, tab = _open_tenure(browser, server_on, durables_folder)
    try:
        field = tab.locator(".bl-matsya-field textarea")
        field.fill("What is a perch?")
        field.press("Enter")
        tab.wait_for_selector(".bl-matsya-answer", timeout=20_000)
        choose_option(tab, ".bl-matsya-kind", "Build declaration")
        tab.wait_for_selector(".bl-matsya-target vscode-single-select", timeout=10_000)
        tab.evaluate("() => document.activeElement && document.activeElement.blur()")
        tab.mouse.move(40, 600)
        tab.wait_for_timeout(400)
        tokens = tab.evaluate(TOKENS_JS)
        ground = _rgb(tokens["ground"])[:3]
        hairline = _over(_rgb(tokens["hairline"]), ground)
        edge = _over(_rgb(tokens["border"]), _rgb(tokens["raised"])[:3])
        column, view = boxes(tab, ".bl-matsya")[0], boxes(tab, ".bl-view")[0]
        box = boxes(tab, ".bl-matsya-row")[0]
        left, right = round(column["left"]), round(column["left"] + column["width"])
        divider = round(column["left"] - 18)
        view_right = round(view["left"] + view["width"])
        below = round(boxes(tab, ".bl-matsya-exchange")[-1]["bottom"]) + 40
        found = _row(tab, left, right, below)
        assert all(_near(pixel, ground) for pixel in found), (below, sorted(set(found))[:4])
        for y in (18, below, round(box["top"]) + 4):
            found = _row(tab, view_right, left + 12, y)
            differing = [
                view_right + i for i, pixel in enumerate(found) if not _near(pixel, ground)
            ]
            assert differing == [divider], (y, differing)
            assert _near(found[divider - view_right], hairline), (y, found[divider - view_right])
        middle = round(box["top"] + box["height"] / 2)
        outside, border = _row(tab, round(box["left"]) - 1, round(box["left"]) + 1, middle)
        assert _near(outside, ground) and _near(border, edge), (outside, border, edge)
        print(
            f"unit G4 item 2, a conversation and the build mode: border {border}, ground {ground}"
        )
    finally:
        context.close()


# --- a connected folder's questions in its project session (SG4-25) ---


def test_a_question_of_a_connected_folder_is_a_turn_of_its_project_session(
    scratch_durables, app_state, matsya_state, tmp_path, monkeypatch
):
    """SG4-25 (D-1; amendment 06 §2 items 14, 17 and 18). In a folder not
    connected a question goes to unit M's conversation, the client's
    `session new` and `ask --json`. Once the folder is connected, a
    question starts a turn in the folder's project session by `ask
    --no-wait` with a delivery identifier, the request's record standing in
    the folder before the client runs; the answer is read by `turn status`
    once the service has finished the turn, with its passages, and no
    question goes to unit M's conversation."""
    from bellman_workbench import app

    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    folder = model.open_folder(scratch_durables)
    requests = folder.root / matsya_work.REQUESTS_FOLDER
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_REQUESTS", str(requests))
    app_state(folder.root)
    _, rendered = solara.render(_column(app), handle_error=False)
    try:
        matsya_state.send("What is a stage?")
        wait_until(
            lambda: matsya_state.exchanges.value[-1].answer is not None, 20.0, "unit M's answer"
        )
        calls = [entry for entry in stub_calls(log) if isinstance(entry, list)]
        assert [call[:2] for call in calls] == [
            ["session", "new"],
            ["ask", f"id-{app._session()}"],
        ]
        log.unlink()
        session = _connected(folder)
        matsya_state.send("What is a perch?")
        wait_until(
            lambda: (requests.is_dir() and any(requests.glob("*.json"))), 20.0, "the record"
        )
        (path,) = requests.glob("*.json")
        delivery = path.stem
        wait_until(
            lambda: json.loads(path.read_text(encoding="utf-8"))["accepted"] is not None,
            20.0,
            "the turn accepted",
        )
        record = json.loads(path.read_text(encoding="utf-8"))
        assert (record["kind"], record["session"], record["question"]) == (
            "turn",
            session.id,
            "What is a perch?",
        )
        assert matsya_state.exchanges.value[-1].answer is None
        stub_turn(
            {
                "id": record["accepted"],
                "session": session.id,
                "state": "finished",
                "record": {
                    "result": {
                        "status": "answered",
                        "answer": "An information set of a stage.",
                        "citations": [{"path": "docs/overview/03-language.md"}],
                    }
                },
            }
        )
        wait_until(
            lambda: matsya_state.exchanges.value[-1].answer is not None, 20.0, "the turn's answer"
        )
        answered = matsya_state.exchanges.value[-1]
        assert (answered.answer, answered.passages) == (
            "An information set of a stage.",
            ("docs/overview/03-language.md",),
        )
        entries = stub_calls(log)
        calls = [entry for entry in entries if isinstance(entry, list)]
        assert calls[0] == [
            "ask",
            session.id,
            "--no-wait",
            "--delivery-id",
            delivery,
            "--json",
            "--",
            "What is a perch?",
        ], calls[0]
        assert {"turn_requests_before": [f"{delivery}.json"]} in entries
        assert all(call[:2] == ["turn", "status"] for call in calls[1:]) and len(calls) > 1, calls
        print(f"unit G4 turn: {record['accepted']} of {session.id[:8]}, {len(calls) - 1} readings")
    finally:
        rendered.close()
