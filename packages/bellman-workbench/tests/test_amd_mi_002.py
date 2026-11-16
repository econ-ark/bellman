"""The acceptance tests of AMD-MI-002 of the model interface specification
0.3 (into a stage and back, the panes' names, the BellmanType panel): one
test per acceptance item of its brief, named `test_item_<n>_*`, for items
1 to 5; item 6 is AAS's own reading and has no test."""

from __future__ import annotations

import re
import sys
import time

import yaml

from workbench_support import (
    BEQUEST,
    BUTTON_SHOWN_JS,
    CONS,
    DOCUMENT_JS,
    ERROR_MARK_COLOR_JS,
    INK_3,
    KEEPER_CONS,
    ORANGE,
    RECIPE_FILE,
    RESTRICTION_FIELD,
    ROOT,
    STATUS,
    TABLE_ROWS_JS,
    TENURE,
    TWO_STAGES,
    VIEWPORT,
    active_line,
    breadcrumb,
    choose_option,
    choose_restriction,
    click_line,
    click_until,
    digest7,
    double_click_node,
    edited,
    error_count,
    error_lines,
    git,
    held_graph_ids,
    history_buttons,
    occurrence_head,
    open_cons,
    open_file,
    open_path_shown,
    open_restriction,
    open_trellis,
    panel_head,
    press_in_field,
    press_outside_fields,
    recipe_head,
    record_texts,
    record_view_state,
    recorded_texts,
    replace_in_editor,
    restrict,
    reveal_in_tree,
    select_until,
    settled_status,
    status_settled_on,
    toggle_errors,
    trellis_settled,
    used_at,
    view_state,
    wait_for_view,
    wait_until,
)

from bellman.stage import admitted_methods, elaborate_text
from bellman_workbench import model, recipe, trellis


def test_item_1_the_bars_read_the_new_names_the_error_mark_lists_refusals_no_file_holds_the_old(
    page, server, model_folder, original
):
    """With cons.bl open, the text pane has no running head and the graph
    bar reads `Semantic graph` (unit N, Task 1; design pass 10 §2), and the
    strip of the panel under the text names the file `cons.bl`, the panel
    having no head (unit N, Task 2; design pass 10 §4), the loop's state,
    `constructed`, standing in the status line and not in the panel (unit
    R, R-D50); the head of the pane under the graph reads `Details` (spec
    0.4 §5.5; unit R, brief rule 6; L-D12; L-D28). No text file under
    `packages/bellman-workbench` or `docs/overview` holds any of the three
    old names (the search of item 1), and no file under
    `packages/bellman-workbench` but its documents holds a sentence the
    page's words removed (A2-D14; the amendment's §6a rule 2), each found
    by a part that the code before wrote within one string; the files
    searched include `app.py` and `07-workbench.md`.

    The graph bar ends with the error mark, Problems (A2-D13; the
    amendment's §6a rule 1; rulings R44 and R45; design pass 10 §2). With
    nothing refused the mark is quiet, in ink-3 (design pass 8 §6; unit M,
    Task 4) and with
    no count, and a click on it opens the
    list under it, which reads `nothing refused`. Two refusals made to
    stand, the loop's refusal of `a = m_d - - c` at line 18 and, in the
    trellis view, the package's refusal of the restriction `periods 9`,
    make the mark read 2 in orange, and the list holds the package's two
    sentences, newest first, the loop's with its file and its line as a
    link, which moves the editor to line 18. The panel's refusal names its
    place and its rule without the sentence, and the restriction's select
    is marked without one. `all` in the restriction's menu clears its
    refusal, and the mark reads 1; the line restored, nothing stands, the
    mark is quiet again and the list reads `nothing refused`; a second
    click on the mark closes the list. The file on disk is unchanged."""
    open_cons(page, server)
    page.wait_for_selector(".bl-class-row", timeout=10_000)
    assert page.locator(".bl-file > .bl-head").count() == 0
    assert page.locator(".bl-graph-bar .bl-graph-name").text_content() == "Semantic graph"
    # the panels' heads read their names (unit L, Task 12; AAS, L-D12), each
    # with its capital (unit L, Task 29; L-D28)
    assert page.locator(".bl-panel .bl-region-name").text_content() == "Details"
    # the panel under the editor has its strip in place of a head (unit N,
    # Task 2; design pass 10 §4)
    types_strip = '.bl-classification[data-panel="types"] .bl-inspector-strip'
    assert page.locator(f"{types_strip} .bl-inspector-file").text_content() == "cons.bl"
    assert page.locator('.bl-classification[data-panel="types"] .bl-class-state').count() == 0
    assert page.locator(".bl-status-summary .bl-status-state").text_content() == "constructed"

    def mark():
        # the count the error mark reads, the lines of its list and the
        # mark's color, read together, since the count and the list are
        # elements the page updates one after the other
        return error_count(page), error_lines(page), page.evaluate(ERROR_MARK_COLOR_JS)

    # the error mark, the last element of the graph bar, quiet while nothing
    # stands refused, its list reading two words
    assert page.locator(".bl-graph-bar > .bl-errors:last-child > .bl-error-mark").count() == 1
    assert mark() == (0, [], INK_3)
    toggle_errors(page)
    assert page.locator(".bl-error-list").text_content() == "nothing refused"
    # closed, so that the list leaves the view's bar under it
    toggle_errors(page)

    # the loop's refusal of the text at line 18
    refused_text = edited(original, 18, "    a = m_d - - c")
    (diagnostic,) = model.elaborate_buffer(refused_text, CONS).diagnostics
    standing = [(diagnostic.message, CONS, 18)]
    click_line(page, 18)
    page.keyboard.press("End")
    page.keyboard.press("ArrowLeft")
    page.keyboard.type("- ")
    wait_until(lambda: mark() == (1, standing, ORANGE), 10.0, "the loop's refusal listed")
    assert page.locator(".bl-refusal").text_content() == f"refused at {CONS}:18:15 · rule syntax"

    # the package's refusal of the restriction `periods 9`, the trellis
    # holding six periods
    restricted = trellis.show_trellis(
        model.open_folder(model_folder),
        recipe.Source("recipe", RECIPE_FILE),
        trellis.parse_restriction("periods 9"),
    ).restricted
    page.click(".bl-trellis-button")
    restrict(page, "periods 9")
    both = [(restricted, None, None), *standing]
    wait_until(lambda: mark() == (2, both, ORANGE), 60.0, "the two refusals, newest first")
    marked = page.locator(".bl-restriction.bl-refusal-mark")
    wait_until(lambda: marked.count() == 1, 10.0, "the restriction's select marked")
    assert page.locator(".bl-restriction-group").text_content().strip() == "periods 9"

    # the loop's line is a link to its file and its line
    click_line(page, 1)
    wait_until(lambda: active_line(page) == 1, 5.0, "the cursor on line 1")
    toggle_errors(page)
    page.click(f'.bl-error-place[data-path="{CONS}"][data-line="18"]')
    wait_until(lambda: active_line(page) == 18, 10.0, "the editor on line 18")
    toggle_errors(page)

    # one refusal cleared, then none standing
    choose_restriction(page, "all")
    wait_until(lambda: mark() == (1, standing, ORANGE), 30.0, "the restriction's refusal cleared")
    wait_until(lambda: marked.count() == 0, 10.0, "the restriction's select unmarked")
    replace_in_editor(page, "a = m_d - - c", "a = m_d - c")
    wait_until(lambda: mark() == (0, [], INK_3), 30.0, "nothing refused")
    toggle_errors(page)
    assert page.locator(".bl-error-list").text_content() == "nothing refused"
    toggle_errors(page)
    assert (model_folder / CONS).read_text(encoding="utf-8") == original

    # the three old names, each space written `[ ]` so that this file does
    # not hold them
    old_names = re.compile(
        r"Symbolic[ ]Bellman|Denotational[ ]Semantic[ ]Graph|The[ ]classification[ ]table"
    )
    # the files git tracks under the two folders, and the untracked ones it
    # does not ignore
    listed = git(
        ROOT, "ls-files", "-z", "--cached", "--others", "--exclude-standard",
        "--", "packages/bellman-workbench", "docs/overview",
    )
    # the sentences the page's words removed, each by a part that the code
    # before wrote within one string, each space written `[ ]` as above
    removed = re.compile(
        "|".join(
            (
                r"the[ ]view[ ]shows[ ]the[ ]last[ ]stage[ ]elaborated",
                # the two sentences of a value not written, in full, so that
                # the sentences of brief §5 of unit J, which hold the words
                # `was not written` by design, are not matched (J-D35)
                r"\{entry\.file\}[ ]was[ ]not[ ]written:[ ]\{written\.reason\}",
                r"the[ ]\{what\}[ ]of[ ]\{name\}[ ]was[ ]not[ ]written:[ ]\{written\.reason\}",
                r"select[ ]an[ ]occurrence[ ]in[ ]the[ ]view",
                r"The[ ]folder[ ]holds[ ]no[ ]stage[ ]file",
                r"save[ ]it[ ]or[ ]reload[ ]it",
                r"a[ ]hook[ ]of[ ]this[ ]repository",
                r"the[ ]new[ ]folder[ ]opens[ ]in[ ]this[ ]tab",
                r"add[ ]stage[ ]edits[ ]these[ ]files",
                r"add[ ]period[ ]edits[ ]these[ ]files",
                r"copies[ ]these[ ]files[ ]as[ ]they[ ]stand[ ]on[ ]disk",
                r"the[ ]table[ ]waits[ ]until[ ]the[ ]text[ ]has[ ]been[ ]read[ ]again",
                r"the[ ]table[ ]follows[ ]once[ ]the[ ]text[ ]is",
                r"Add[ ]a[ ]file[ ]ending[ ]in[ ]\.bl",
                r"from[ ]the[ ]folder[ ]at[ ]the[ ]left",
                r"The[ ]tabs[ ]fill[ ]when[ ]the[ ]open[ ]file[ ]elaborates",
                r"git[ ]reports[ ]no[ ]change[ ]under[ ]this[ ]folder",
                r"its[ ]bindings[ ]are[ ]slots",
                r"a[ ]push[ ]will[ ]fail[ ]with[ ]git",
                r"a[ ]repository[ ]is[ ]made[ ]for[ ]the[ ]new[ ]folder",
                r"Choose[ ]the[ ]stages[ ]of[ ]the[ ]period",
                r"Adding[ ]the[ ]period[ ]writes[ ]the[ ]period[ ]file",
                r"the[ ]line[ ]under[ ]the[ ]cursor[ ]in[ ]full",
                r"with[ ]their[ ]sets[ ]and[ ]roles,[ ]read[ ]from[ ]the[ ]stage's",
                r"from[ ]the[ ]calibration[ ]files[ ]the[ ]recipe[ ]lists",
                r"with[ ]the[ ]methods[ ]the[ ]method[ ]table[ ]admits[ ]there",
                r"the[ ]settings[ ]the[ ]recipe's[ ]settings[ ]files[ ]give",
                r"so[ ]no[ ]term[ ]exists;[ ]the[ ]refusal[ ]stands[ ]at",
                r"are[ ]counted[ ]and[ ]the[ ]last[ ]graph[ ]stays,[ ]dimmed",
                r"which[ ]the[ ]view[ ]draws[ ]as[ ]one[ ]node",
                r"drawn[ ]in[ ]the[ ]view[ ]as[ ]one[ ]box[ ]that[ ]opens",
                r"however[ ]many[ ]boxes[ ]read[ ]it",
                r"says[ ]why[ ]in[ ]its[ ]own[ ]words",
                r"the[ ]key[ ]the[ ]stage's[ ]provenance[ ]records",
                r"followed[ ]by[ ]the[ ]first[ ]seven[ ]characters",
                r"the[ ]trellis's[ ]status[ ]line[ ]names[ ]the[ ]bindings[ ]applied",
                r"the[ ]export[ ]of[ ]the[ ]view,[ ]and[ ]for[ ]a[ ]stage[ ]file[ ]also[ ]the",
                r"the[ ]function's[ ]domain[ ]is[ ]in[ ]type",
                r"when[ ]bound,[ ]its[ ]value",
                r"where[ ]the[ ]file[ ]may[ ]be[ ]correct",
                r"counted[ ]apart[ ]from[ ]refusals",
                r"each[ ]occurrence[ ]a[ ]frame[ ]holding[ ]its[ ]builders",
                r"by[ ]the[ ]sources[ ]its[ ]record[ ]names[ ]for[ ]that[ ]position",
                r"its[ ]stage[ ]occurrences[ ]joined[ ]by[ ]their[ ]fields",
                r"written[ ]as[ ]the[ ]trellis[ ]drawing[ ]writes[ ]it",
                r"the[ ]wire[ ]stands[ ]at[ ]the[ ]view's[ ]own[ ]inputs[ ]or[ ]outputs",
                r"removed[ ]by[ ]the[ ]button[ ]whole[ ]trellis",
                r"each[ ]recipe[ ]is[ ]read[ ]to[ ]a[ ]trellis[ ]of[ ]its[ ]own",
                r"the[ ]line[ ]of[ ]a[ ]shock's[ ]distribution",
                r"the[ ]definitions[ ]its[ ]record[ ]rests[ ]on,[ ]followed[ ]through[ ]the",
                r"that[ ]the[ ]recipe[ ]lists[ ]for[ ]the[ ]occurrence",
                r"the[ ]window[ ]sends[ ]the[ ]service[ ]the[ ]question[ ]typed",
                r"its[ ]questions[ ]and[ ]answers[ ]are[ ]kept",
                r"Matsya's[ ]client[ ]is[ ]not[ ]on[ ]this[ ]machine",
                r"the[ ]service[ ]could[ ]not[ ]be[ ]reached",
                r"the[ ]rest[ ]of[ ]the[ ]Workbench[ ]works[ ]as[ ]before",
                r"give[ ]the[ ]variant[ ]another[ ]name",
                r"give[ ]the[ ]stage[ ]another[ ]key",
                r"give[ ]the[ ]period[ ]another[ ]label",
                r"add[ ]it[ ]with[ ]add[ ]stage",
                r"edits[ ]a[ ]folder[ ]that",
                r"choose[ ]one[ ]of[ ]them",
                r"give[ ]each[ ]stage[ ]its[ ]own",
                r"write[ ]another[ ]key",
                r"write[ ]another[ ]label",
                r"not[ ]as[ ]a[ ]name;[ ]write[ ]another",
                r"Bellman[ ]Workbench[ ]reads[ ]its",
                r"new[ ]trellis[ ]writes[ ]a[ ]folder[ ]that[ ]does[ ]not",
                r"a[ ]period[ ]holds[ ]at[ ]least[ ]one[ ]stage",
                r"new[ ]variant[ ]copies[ ]a[ ]recipe[ ]of",
                r"copies[ ]a[ ]period[ ]file[ ]of",
                r"the[ ]files[ ]a[ ]recipe[ ]and[ ]its[ ]trellis[ ]file[ ]name[ ]there",
                r"<name>[ ]of[ ]the[ ]variant's[ ]files",
                r"so[ ]nothing[ ]is[ ]committed",
                r"Bellman[ ]Workbench[ ]does[ ]not[ ]check",
                r"let[ ]git's[ ]credential[ ]helper",
                r"write[ ]it[ ]in[ ]a[ ]form[ ]such[ ]as",
                r"so[ ]the[ ]table[ ]writes[ ]nothing",
                r"press[ ]Escape[ ]to[ ]keep[ ]the[ ]one[ ]declared",
                r"so[ ]the[ ]table[ ]does[ ]not[ ]write[ ]it",
                r"write[ ]the[ ]field's[ ]name[ ]in[ ]the[ ]box",
                r"writes[ ]it[ ]nowhere[ ]else",
                r"is[ ]not[ ]applied",
                r"names[ ]no[ ]record[ ]for",
                r"stands[ ]at[ ]the[ ]folder's[ ]top,[ ]and[ ]the[ ]Workbench",
                r"add[ ]one[ ]in[ ]the[ ]recipe[ ]table",
                r"the[ ]stage's[ ]parameters[ ]cannot[ ]be[ ]read",
                r"so[ ]no[ ]method[ ]is[ ]offered",
                r";[ ]a[ ]typed[ ]value[ ]is[ ]one[ ]value[ ]written[ ]without",
                r"no[ ]record[ ]of[ ]the[ ]trellis[ ]names[ ]a[ ]source",
                r"applies,[ ]or[ ]block[ ]or[ ]field",
                r"writes[ ]\{name\}[ ]any[ ]longer",
            )
        )
    )
    relpaths = list(filter(None, listed.split("\0")))
    # the listing holds the page's module and the page's document, so that
    # the search below reads the files it guards
    assert "packages/bellman-workbench/bellman_workbench/app.py" in relpaths
    assert "docs/overview/07-workbench.md" in relpaths
    holding, keeping = [], []
    for relpath in relpaths:
        path = ROOT / relpath
        data = path.read_bytes() if path.is_file() else b""
        # a file holding a NUL byte is binary and is not searched, as in rg
        if b"\0" in data:
            continue
        text = data.decode("utf-8", "replace")
        if old_names.search(text):
            holding.append(relpath)
        # the documents are not searched for the removed sentences
        found = None if relpath.endswith(".md") else removed.search(text)
        if found is not None:
            keeping.append((relpath, found.group()))
    assert holding == []
    assert keeping == []


def test_item_2_a_double_click_opens_the_occurrence_and_alt_arrows_go_back_and_forward(
    page, server_on, lifecycle_folder
):
    """On the trellis of the lifecycle registry's recipe, a double click on
    the occurrence `periods[1]/cons`, sent as the viewer's events (the
    element's `hoveredNodeChanged` naming the occurrence's layer and a
    `dblclick` on its host), opens `declaration/stages/cons/cons.bl` in the
    BellmanSym pane bound as that occurrence: the occurrence line reads
    `periods[1] / cons`, the status line's version word `bound`, the
    Semantic graph shows the stage's view, and the breadcrumb reads
    `lifecycle › spec.yml › periods[1] › cons` (A2-D2, A2-D3; the
    amendment's §3 rules 2 and 3). Alt+←, pressed with the focus outside
    any text field, returns to the trellis view with that occurrence
    selected, in the panel and in the viewer, and its layer open in the
    viewer, the breadcrumb reading `lifecycle › spec.yml › periods[1] ›
    cons`, the selected occurrence standing as the path's last parts (unit
    N, Task 1; design pass 10 §2); Alt+→ returns to the stage (A2-D4; rule
    4). Alt+← and Alt+→ pressed with no wait between
    them, the second while the editor's switch to the trellis's file still
    waits, leave the stage with its file in the editor. The button ←
    stands in the breadcrumb while a place stands behind, and → while one
    stands ahead (specification §10). With the recipe opened again from
    the tree, which shows the trellis with the recipe as text, the button
    of the selected occurrence's panel reads `open the stage` and does the
    same, and Alt+← and Alt+→ then do the same. Alt+← pressed in the field
    at the foot of the restriction's menu keeps the browser's word-movement
    default on macOS; on other platforms, the page prevents the browser's
    default step back in its history. The expected prevention follows the
    platform the browser reports. The page stays on the trellis with its
    URL, the field's text and the buttons as they were."""
    open_trellis(page, server_on(lifecycle_folder), RECIPE_FILE, minimum=10)
    layer = "periods[1]/cons___group___"

    def in_trellis() -> bool:
        # the restriction's select stands in the trellis view alone
        return page.locator(".bl-restriction").count() > 0

    field = RESTRICTION_FIELD
    is_macos = page.evaluate("() => navigator.platform").startswith("Mac")
    address, buttons = page.url, history_buttons(page)
    open_restriction(page)
    page.fill(field, "periods 0–1")
    assert press_in_field(page, field, "Alt+ArrowLeft") is (not is_macos)
    page.wait_for_timeout(1_000)
    assert page.url == address and page.locator(".bl-window").count() == 1
    assert page.locator(field).input_value() == "periods 0–1"
    assert in_trellis() and history_buttons(page) == buttons
    # the menu closed by Escape, which applies nothing of the text typed
    page.keyboard.press("Escape")
    page.wait_for_selector(".bl-restriction-menu", state="detached", timeout=5_000)

    def version() -> str | None:
        # the version word of the status line once it has settled on the
        # stage file
        line = status_settled_on(page, CONS)
        found = STATUS.match(line) if line is not None else None
        return found["version"] if found is not None else None

    def opened(buttons: tuple[int, int]) -> None:
        # the occurrence's stage file, bound as the occurrence; the stage's
        # view, with the select `graph` in the bar, and the stage's initial
        # diagrams in the viewer's element (since design pass 14 §7 the
        # trellis holds initial diagrams of its own, so the view is told by
        # `in_trellis` first); the breadcrumb of the chosen position, and the
        # buttons ← and →
        wait_until(
            lambda: open_path_shown(page) == CONS, 60.0, "the stage file"
        )
        wait_until(lambda: recipe_head(page) == "periods[1] / cons", 60.0, "the occurrence line")
        wait_until(lambda: version() == "bound", 60.0, "the version word bound")
        kind = page.locator(".bl-view-kind")
        wait_until(lambda: not in_trellis() and kind.count() == 1, 60.0, "the stage's view")
        wait_until(
            lambda: "backward initial diagram" in held_graph_ids(page),
            60.0,
            "the stage's view in the viewer",
        )
        wait_until(
            lambda: breadcrumb(page) == "lifecycle › spec.yml › periods[1] › cons",
            30.0,
            "the breadcrumb of the occurrence",
        )
        wait_until(lambda: history_buttons(page) == buttons, 10.0, f"the buttons {buttons}")

    def returned(buttons: tuple[int, int]) -> None:
        # the trellis view, the occurrence the head and the panel's subject,
        # the viewer selecting its layer and holding the layer open, the
        # breadcrumb of the trellis, and the buttons ← and →
        wait_until(
            lambda: in_trellis() and recipe_head(page) == "periods[1] / cons", 60.0, "the trellis"
        )
        wait_until(
            lambda: panel_head(page).startswith(occurrence_head("periods[1]/cons")),
            30.0,
            "the panel of the occurrence",
        )

        def selected_and_open() -> bool:
            state = view_state(page)
            return state is not None and state["selected"] == layer and layer in state["open"]

        wait_until(selected_and_open, 60.0, "the occurrence selected and open in the viewer")
        assert breadcrumb(page) == "lifecycle › spec.yml › periods[1] › cons"
        wait_until(lambda: history_buttons(page) == buttons, 10.0, f"the buttons {buttons}")

    def back_and_forward(behind: int) -> None:
        # Alt+← to the trellis and Alt+→ to the stage, `behind` places
        # standing behind the trellis
        record_view_state(page)
        press_outside_fields(page, "Alt+ArrowLeft")
        returned((min(behind, 1), 1))
        press_outside_fields(page, "Alt+ArrowRight")
        opened((1, 0))

    double_click_node(page, layer, "backward")
    opened((1, 0))
    back_and_forward(0)
    # Alt+← and Alt+→ with no wait between them. Both steps are taken once
    # the graph bar has read the trellis's form, which holds the restriction
    # select after the switch, its options' words `all` or `periods` after
    # `Trellis` in the bar's text, and then the stage's, which holds no
    # restriction (since design pass 14 §7 both forms hold the select
    # `graph`, so the word `Operator` tells them apart no longer; S-D28),
    # and the breadcrumb names the occurrence, which it names in both views
    # (unit N, Task 1). The editor answers the first step's flush request before the
    # second step's view reaches the page, and Python reads that answer
    # next; a second later the editor still holds the stage's file and has
    # held no other. The breadcrumb's path is read in `.bl-crumbs`, which
    # holds it alone. The open file's path is read in the folder's
    # `.bl-rail-open`, one element that prints it whichever tab is active
    # (unit R, R-D32).
    record_texts(page, (".bl-crumbs", ".bl-graph-bar", ".bl-rail-open"))
    press_outside_fields(page, "Alt+ArrowLeft", "Alt+ArrowRight")

    def restricted(text: str) -> bool:
        # the restriction select's options follow the switch's `Trellis`
        return re.search(r"Trellis(all|periods)", text) is not None

    def both_steps() -> bool:
        bars = recorded_texts(page, ".bl-graph-bar")
        trellis = any(restricted(text) for text in bars)
        stage = bool(bars) and not restricted(bars[-1])
        return trellis and stage and recorded_texts(page, ".bl-crumbs")[-1].endswith(
            "periods[1] › cons"
        )

    wait_until(both_steps, 30.0, "the step back and the step forward")
    page.wait_for_timeout(1_000)
    assert recorded_texts(page, ".bl-rail-open") == [CONS]
    opened((1, 0))

    page.click(f'.bl-tree-file[data-path="{RECIPE_FILE}"]')
    wait_until(
        lambda: in_trellis() and open_path_shown(page) == RECIPE_FILE,
        30.0,
        "the trellis with the recipe as text",
    )
    select_until(
        page,
        layer,
        "backward",
        lambda: page.locator(".bl-occurrence-open").count() > 0,
        "the panel of periods[1]/cons",
    )
    assert page.locator(".bl-occurrence-open").text_content().strip() == "Open the stage"
    click_until(page, ".bl-occurrence-open", lambda: not in_trellis(), "the stage view")
    opened((1, 0))
    back_and_forward(2)


def test_item_3_a_stage_from_the_tree_offers_its_positions_its_uses_and_the_recipes_holding_it(
    page, server_on, durables_folder
):
    """On a copy of the durables model, whose recipe `declaration/spec.yml`
    binds `keeper_cons.bl` and `tenure.bl` at 51 positions each and whose
    variant `declaration/spec.two-stages.yml` binds `keeper_cons.bl` at 51
    and holds no tenure stage, with the restriction `periods 0–2` standing
    (the amendment's §3 rules 5 and 6; the brief's rules 2 and 6).

    `bequest.bl` opened from the tree, which `spec.yml` holds at one
    position, reads `periods[0] / bequest` on the occurrence line, with
    neither a choice of positions nor a link to a recipe, and the
    breadcrumb `durables › spec.yml › bequest › periods[0]`.
    `keeper_cons.bl` opened from the tree is bound as its first occurrence
    in the tab's recipe, `spec.yml`: the occurrence line reads
    `periods[0] / keeper_cons`, the version word `bound`, the breadcrumb
    `durables › spec.yml › keeper_cons › periods[0]`. `periods[3]`
    chosen on the occurrence line binds it there, the breadcrumb reading
    `durables › spec.yml › periods[3] › keeper_cons`; Alt+← returns to the
    first form and Alt+→ to the second, since the choice records the place
    it leaves. The breadcrumb's period, which the restriction omits, opens
    the trellis drawn under `periods 3` with that period selected and open,
    and Alt+← returns to the stage.

    With nothing selected, the panel prints where the file is used as one
    range for each recipe (unit K, Task 3): `0–50` under `periods` for
    `spec.yml`, the tab's, and `declaration/spec.two-stages.yml · periods
    0–50` under `also`, each a link at the occurrence the stage is bound as.
    The link of `spec.yml`, at `periods[3]/keeper_cons`, which the
    restriction omits, opens that recipe's trellis drawn under `periods 3`:
    the occurrence is the head and the panel's subject, and the viewer
    selects it with its layer open, a layer that a trellis of 51 periods
    keeps closed, as it keeps that of `periods[3]/tenure`. Alt+← returns to
    the stage at `periods[3]` and restores the restriction `periods 0–2`,
    under which the trellis of the next link is drawn: with `periods[1]`
    chosen on the occurrence line, the link of `spec.two-stages.yml`, at
    `periods[1]/keeper_cons`, which the restriction holds, opens that
    recipe's trellis with the occurrence selected and open.

    Under that recipe `tenure.bl` from the tree reads `durables › tenure.bl`,
    its occurrence line saying that the recipe holds no occurrence of it,
    the version word `symbolic`, with one link, to `declaration/spec.yml`.
    The link makes `spec.yml` the tab's recipe and binds the file as
    `periods[0] / tenure`, the version word `bound`, with the income
    functions supplied by the declared calibration source, under `durables ›
    spec.yml › tenure › periods[0]`, the stage's view kept; Alt+←
    returns to `durables › tenure.bl`."""
    open_trellis(page, server_on(durables_folder), RECIPE_FILE, minimum=10, timeout=240_000)
    restrict(page, "periods 0–2")
    wait_until(
        lambda: "shown periods 0–2 " in (trellis_settled(page, RECIPE_FILE) or ""),
        120.0,
        "the trellis under periods 0–2",
    )

    def in_trellis() -> bool:
        # the restriction's select stands in the trellis view alone
        return page.locator(".bl-restriction").count() > 0

    def version(path: str) -> str | None:
        # the version word of the status line once it has settled on `path`
        line = status_settled_on(page, path)
        found = STATUS.match(line) if line is not None else None
        return found["version"] if found is not None else None

    def stage(path: str, line: str, crumbs: str, word: str) -> None:
        # the stage's view of `path`: its occurrence line `line`, the
        # breadcrumb `crumbs` and the version word `word`
        wait_until(lambda: open_path_shown(page) == path, 60.0, path)
        wait_until(lambda: recipe_head(page) == line, 60.0, f"the occurrence line {line!r}")
        wait_until(lambda: breadcrumb(page) == crumbs, 30.0, f"the breadcrumb {crumbs!r}")
        wait_until(lambda: version(path) == word, 60.0, f"the version word {word}")
        assert not in_trellis()

    def trellis_at(path: str, shown: str, line: str, head: str, layer: str) -> None:
        # the trellis view of the recipe `path` drawn under the restriction
        # `shown`, the occurrence line `line`, the panel's head beginning
        # with `head`, the viewer selecting the layer `layer` and holding it
        # open, and the breadcrumb of the trellis
        wait_until(
            lambda: in_trellis() and recipe_head(page) == line, 60.0, f"the trellis at {line}"
        )
        wait_until(
            lambda: f"shown {shown} " in (trellis_settled(page, path) or ""),
            120.0,
            f"the trellis of {path} under {shown}",
        )
        wait_until(lambda: panel_head(page).startswith(head), 30.0, f"the panel of {head}")

        def selected_and_open() -> bool:
            state = view_state(page)
            return state is not None and state["selected"] == layer and layer in state["open"]

        wait_until(selected_and_open, 60.0, f"{layer} selected and open in the viewer")
        # the trellis's path, ending in the selected occurrence (unit N,
        # Task 1; design pass 10 §2)
        named = path.rsplit("/", 1)[-1]
        assert breadcrumb(page) == f"durables › {named} › " + line.replace(" / ", " › ")

    reveal_in_tree(page, BEQUEST)
    page.click(f'.bl-tree-file[data-path="{BEQUEST}"]')
    wait_until(lambda: open_path_shown(page) == BEQUEST, 60.0, BEQUEST)
    wait_until(lambda: recipe_head(page) == "periods[0] / bequest", 60.0, "periods[0] / bequest")
    # what the path does not name of the occurrence, its choice and its
    # links are drawn together after the path (unit N, Task 1)
    line = page.locator(".bl-path-occurrence")
    assert line.locator(".bl-recipe-positions, .bl-recipe-holder").count() == 0
    # the path names the occurrence once, its key and its period (the fix
    # wave Q3b of unit Q, item 19; C19)
    one = "durables › spec.yml › bequest › periods[0]"
    wait_until(lambda: breadcrumb(page) == one, 10.0, one)

    reveal_in_tree(page, KEEPER_CONS)
    page.click(f'.bl-tree-file[data-path="{KEEPER_CONS}"]')
    from_tree = "durables › spec.yml › keeper_cons › periods[0]"
    stage(KEEPER_CONS, "periods[0] / keeper_cons", from_tree, "bound")
    chosen = "durables › spec.yml › periods[3] › keeper_cons"
    choose_option(page, ".bl-recipe-positions", "periods[3] / keeper_cons")
    stage(KEEPER_CONS, "periods[3] / keeper_cons", chosen, "bound")
    press_outside_fields(page, "Alt+ArrowLeft")
    stage(KEEPER_CONS, "periods[0] / keeper_cons", from_tree, "bound")
    press_outside_fields(page, "Alt+ArrowRight")
    stage(KEEPER_CONS, "periods[3] / keeper_cons", chosen, "bound")
    # a link's click may be read late while the server reads a trellis
    record_view_state(page)
    click_until(page, '.bl-crumb[data-link="period"]', in_trellis, "the trellis", 60.0)
    trellis_at(
        RECIPE_FILE,
        "periods 3",
        "periods[3] / keeper_cons",
        # the period's identifier in Code name, then its kind (the fix wave
        # Q3b of unit Q, item 19; C1)
        "periods[3] Period ",
        "periods[3]___group___",
    )
    press_outside_fields(page, "Alt+ArrowLeft")
    stage(KEEPER_CONS, "periods[3] / keeper_cons", chosen, "bound")

    def uses(address: str) -> list[tuple[str, str, str]]:
        # each recipe's periods as the panel prints them, the tab's first,
        # each a link at `address`
        return [
            (RECIPE_FILE, "0–50", address),
            (TWO_STAGES, f"{TWO_STAGES} · periods 0–50", address),
        ]

    wait_until(
        lambda: used_at(page) == uses("periods[3]/keeper_cons"),
        30.0,
        "the periods of each recipe, the tab's first",
    )
    click_until(
        page,
        f'.bl-used-recipe[data-path="{RECIPE_FILE}"]',
        in_trellis,
        "the trellis of spec.yml",
        60.0,
    )
    trellis_at(
        RECIPE_FILE,
        "periods 3",
        "periods[3] / keeper_cons",
        occurrence_head("periods[3]/keeper_cons"),
        "periods[3]/keeper_cons___group___",
    )
    assert "periods[3]/tenure___group___" not in view_state(page)["open"]
    press_outside_fields(page, "Alt+ArrowLeft")
    stage(KEEPER_CONS, "periods[3] / keeper_cons", chosen, "bound")
    choose_option(page, ".bl-recipe-positions", "periods[1] / keeper_cons")
    first = "durables › spec.yml › periods[1] › keeper_cons"
    stage(KEEPER_CONS, "periods[1] / keeper_cons", first, "bound")
    wait_until(
        lambda: used_at(page) == uses("periods[1]/keeper_cons"),
        30.0,
        "the links at periods[1]/keeper_cons",
    )
    click_until(
        page,
        f'.bl-used-recipe[data-path="{TWO_STAGES}"]',
        in_trellis,
        "the trellis of spec.two-stages.yml",
        60.0,
    )
    trellis_at(
        TWO_STAGES,
        "periods 0–2",
        "periods[1] / keeper_cons",
        occurrence_head("periods[1]/keeper_cons"),
        "periods[1]/keeper_cons___group___",
    )

    reveal_in_tree(page, TENURE)
    page.click(f'.bl-tree-file[data-path="{TENURE}"]')
    holds_none = f"{TWO_STAGES} holds no occurrence of this file"
    stage(TENURE, holds_none, "durables › tenure.bl", "symbolic")
    links = page.locator(".bl-recipe-holder")
    assert links.evaluate_all("(found) => found.map((link) => link.dataset.path)") == [RECIPE_FILE]
    click_until(
        page,
        f'.bl-recipe-holder[data-path="{RECIPE_FILE}"]',
        lambda: recipe_head(page) == "periods[0] / tenure",
        "the stage bound through spec.yml",
        60.0,
    )
    stage(TENURE, "periods[0] / tenure", "durables › spec.yml › tenure › periods[0]", "bound")
    press_outside_fields(page, "Alt+ArrowLeft")
    stage(TENURE, holds_none, "durables › tenure.bl", "symbolic")


def test_item_4_the_bellmantype_tabs_show_and_write_the_values_and_methods_of_the_occurrence(
    page, server_on, scratch_durables
):
    """On a copy of the durables model, the backend of the BellmanType
    panel's Parameters, Settings and Methods tabs (the amendment's §5 rules 3
    to 6; the brief's rule 7; A2-D8).

    At `periods[3]/tenure`, the seven parameters retain their sets and
    source positions. Y and y_R are complete functions on Age in the last
    calibration file, wage_schedule.yml. An edit of R changes its original
    source alone. Removing R_H from the temporary copy makes it unvalued;
    its replacement appends to the last calibration source. A replacement
    list for Y is refused by the current source editor, without changing
    any bytes. A scalar string for y_R is written and then refused by the
    package as a value of Age → ℝ₊. Invalid YAML and aliases are refused
    before writing, including deeply nested input. The
    Settings tab lists the settings of `declaration/settings/durables.yml`,
    each with the set its declaration in the addition names and its value as
    the file writes it, `fues_eps_d`, which no addition declares, written
    `1.0e-05`, and `400` typed for `n_a`, declared in ℕ, lands at
    line 13 of that file; a text nested deeper than the reader can follow,
    typed within quotes for the text setting `keeper_upper_envelope`, reads
    as a string and is written at line 37 in double quotes, since its plain
    form does not read. The Methods tab lists the four places the stage's
    addition types (`stage.methods`; decision S7-W1 of specification 0.7),
    each with the line of its entry in `stages/tenure/methods.bl`, and
    offers at each the words the package admits at the place, the branching
    stage's places listed as any stage's (unit L, Task 18).
    At `periods[3]/keeper_cons` the Methods tab shows the `!Linear` its
    addition types at the decision builder's Evaluation, with its line;
    `write_method` replaces that word in the block's header at line 60 of
    `stages/keeper_cons/methods.bl` by `!pchip`, the keyword arguments
    kept, and an alias typed as the word is refused as no word of the
    method table. No other byte of the copy changes, and the tabs read
    again show each value written, the keeper's Evaluation bound by
    `!pchip`; the text written for `keeper_upper_envelope`, outside the set
    the keeper's addition declares, is refused at that binding under
    `setting-outside-set` (decision S7-S1).

    In the page, on the copy as the fixture made it (the brief's rule 7;
    the amendment's §5 rules 1 and 6), `tenure.bl` opened from the tree and
    bound as `periods[3]/tenure` on the occurrence line shows the panel's
    four tabs in its bar, Fields first and shown. Parameters names the
    calibration file it writes and shows `R` `1.045`, linked to its source line,
    and `Y` as a finite list; Settings shows `n_a`, in ℕ, `300`;
    Methods shows its four rows, each with a choice of method, and no
    sentence. `1.05` typed
    for `R`, with Enter, changes the source line of R alone, and
    the tree marks the file changed; `[1, 2` typed for `y_R`, which does not
    read as YAML, is refused, the row's input marked and the sentence
    standing in the list under the error mark with the calibration file
    (A2-D13, ruling R46), the tab
    showing `1.05` for `R`; the tab chosen again shows `1.05`. No other
    file of the copy changes.

    Fields, chosen again, shows the branching of `tenure.bl` (the amendment's
    §5 rule 2, A2-D12): at `cntn`, the group of each branch, headed
    `cntn · d = keep` and `cntn · d = adjust` by the control that selects
    it, with that branch's states and the values on them, then the group
    `cntn · all branches`, holding the two incoming age fields,
    each group with its own +. `ℝ₊` entered as the set of z_kp in the group
    `keep` and saved changes line 23 of the file alone, z_adj of `adjust`
    keeping its set; `x`, `ℝ₊`, `state` added in the group `all branches`
    and saved is written into the nested block of each branch, lines 23 and
    28, which the sentence under the group names, and no other byte of the
    copy changes. The loop then refuses that text, since each branch writes
    fields of its own."""
    folder = model.open_folder(scratch_durables)
    calibration = "declaration/calibration/durables.yml"
    wages = "declaration/calibration/wage_schedule.yml"
    settings = "declaration/settings/durables.yml"
    tenure_methods = "declaration/stages/tenure/methods.bl"
    keeper_methods = "declaration/stages/keeper_cons/methods.bl"
    before = {
        path: (scratch_durables / path).read_bytes()
        for path in (calibration, wages, settings, keeper_methods)
    }
    lines = {path: before[path].decode("utf-8").split("\n") for path in before}

    def bound(path: str, key: str):
        # the stage file `path` bound as `periods[3] / <key>` of the recipe,
        # with that occurrence's record
        found = recipe.find_occurrence(
            folder, recipe.Source("recipe", RECIPE_FILE), path, (3, key)
        )
        text = (scratch_durables / path).read_text(encoding="utf-8")
        return recipe.bind_occurrence(elaborate_text(text, found.origin), found)

    tenure = bound(TENURE, "tenure")
    parameters = recipe.parameters_tab(folder, tenure.stage, tenure.record, "tenure")
    assert (parameters.file, parameters.sentence) == (wages, None)
    rows = {row.name: row for row in parameters.rows}
    income = yaml.safe_load(before[wages])["calibration"]
    original_y = rows["Y"].value
    assert [(row.name, row.domain) for row in parameters.rows] == [
        ("R", "ℝ₊₊"), ("R_H", "ℝ₊₊"), ("δ", "[0, 1)"),
        ("ρ_z", "(0, 1)"), ("σ_z", "ℝ₊"),
        ("Y", "Age → ℝ₊"), ("y_R", "Age → ℝ₊"),
    ]
    assert [rows[name].value for name in ("R", "R_H", "δ", "ρ_z", "σ_z")] == [
        "1.045", "1.0", "0.0", "0.82", "0.11",
    ]
    for name in ("Y", "y_R"):
        assert yaml.safe_load(rows[name].value) == income[name]
        assert len(income[name]) == 52
    places = {row.name: row.place for row in parameters.rows}
    r_line = lines[calibration].index("  R: 1.045") + 1
    assert places["R"] == recipe.Place(calibration, "calibration.R", r_line)
    for name in ("Y", "y_R"):
        assert places[name] == recipe.Place(
            wages, f"calibration.{name}", lines[wages].index(f"  {name}:") + 2
        )
    assert recipe.value_place(folder, tenure.record, "calibration", "R") == places["R"]

    written = recipe.write_value(
        folder, tenure.record, "tenure", "calibration", "R", "1.045", "1.05"
    )
    assert written.saved
    lines[calibration][r_line - 1] = "  R: 1.05"
    assert written.text == "\n".join(lines[calibration])

    # An absent scalar appends to the final source, preserving its income tables.
    lines[calibration].remove("  R_H: 1.0")
    (scratch_durables / calibration).write_text("\n".join(lines[calibration]), encoding="utf-8")
    incomplete = bound(TENURE, "tenure")
    absent = next(row for row in recipe.parameters_tab(
        folder, incomplete.stage, incomplete.record, "tenure"
    ).rows if row.name == "R_H")
    assert (absent.value, absent.place) == ("unvalued", None)
    written = recipe.write_value(
        folder, incomplete.record, "tenure", "calibration", "R_H", "unvalued", "1.0"
    )
    assert written.saved
    lines[wages].insert(len(lines[wages]) - 1, "  R_H: 1.0")
    assert written.text == "\n".join(lines[wages])
    assert bound(TENURE, "tenure").notes == []

    refused = recipe.write_value(
        folder, tenure.record, "tenure", "calibration", "Y", rows["Y"].value,
        "[" + ", ".join(["1.0"] * 52) + "]",
    )
    assert not refused.saved
    assert "a list is no string, int, float, boolean or tag" in refused.reason
    assert (scratch_durables / wages).read_text(encoding="utf-8") == "\n".join(lines[wages])

    written = recipe.write_value(
        folder, tenure.record, "tenure", "calibration", "y_R", rows["y_R"].value, "1e-5"
    )
    assert written.saved
    start = lines[wages].index("  y_R:") + 1
    end = lines[wages].index("  R_H: 1.0")
    lines[wages][start:end] = ["    1e-5"]
    assert written.text == "\n".join(lines[wages])
    refused_notes = [note for note in bound(TENURE, "tenure").notes if "parameter 'y_R'" in note]
    assert len(refused_notes) == 1
    assert "the value '1e-5' is one value where Age → ℝ₊ takes one entry per member" in refused_notes[0]
    # a text with a value its core tag cannot build does not read
    refused = recipe.write_value(
        folder, tenure.record, "tenure", "calibration", "y_R", "1e-5", "!!bool abc"
    )
    assert (refused.saved, refused.reason) == (False, "!!bool abc does not read as YAML")
    # each level a mapping that merges ten aliases of the level below
    levels = ["l0: &l0 {" + ", ".join(f"k{i}: {i}" for i in range(10)) + "}"]
    levels += [f"l{k}: &l{k} {{<<: [" + ", ".join([f"*l{k - 1}"] * 10) + "]}" for k in range(1, 8)]
    merged = "{" + ", ".join(levels) + "}"
    started = time.perf_counter()
    refused = recipe.write_value(
        folder, tenure.record, "tenure", "calibration", "y_R", "1e-5", merged
    )
    assert time.perf_counter() - started < 1.0
    assert (refused.saved, refused.reason) == (
        False,
        f"{merged} writes an anchor, which a typed value may not",
    )
    bracketed = "[" * 9998 + "*a"
    refused = recipe.write_value(
        folder, tenure.record, "tenure", "calibration", "y_R", "1e-5", bracketed
    )
    assert (refused.saved, refused.reason) == (False, f"{bracketed} does not read as YAML")
    assert (scratch_durables / wages).read_text(encoding="utf-8") == written.text

    tab = recipe.settings_tab(folder, tenure.stage, tenure.record, "tenure")
    assert (tab.file, tab.sentence) == (settings, None)
    # the settings the addition declares come first, in its order, each with
    # its declared set (decision S7-W4), the tie's branch before the grids;
    # the names the file values that no addition declares follow, with no set
    assert tab.rows[:2] == (
        recipe.ValueRow(
            "tie_break",
            "{keep, adjust}",
            "adjust",
            recipe.Place(settings, "settings.tie_break", 76),
        ),
        recipe.ValueRow("n_a", "ℕ", "300", recipe.Place(settings, "settings.n_a", 13)),
    )
    # a row shows a value as the file writes it, which reads back as that value
    eps_d = next(row for row in tab.rows if row.name == "fues_eps_d")
    assert eps_d == recipe.ValueRow(
        "fues_eps_d", "", "1.0e-05", recipe.Place(settings, "settings.fues_eps_d", 41)
    )
    written = recipe.write_value(folder, tenure.record, "tenure", "settings", "n_a", "300", "400")
    assert written.saved
    lines[settings][12] = "  n_a: 400"
    assert written.text == "\n".join(lines[settings])
    # as many levels as the recursion limit, more than the reader's composer
    # can follow, since it calls itself at least once for each level
    depth = sys.getrecursionlimit()
    deep = "{a: " * depth + "1" + "}" * depth
    written = recipe.write_value(
        folder,
        tenure.record,
        "tenure",
        "settings",
        "keeper_upper_envelope",
        "FUES",
        f"'{deep}'",
    )
    assert written.saved
    lines[settings][36] = f'  keeper_upper_envelope: "{deep}"'
    assert written.text == "\n".join(lines[settings])

    methods = recipe.methods_tab(folder, tenure.stage, tenure.record, "tenure")
    assert (methods.file, methods.sentence) == (tenure_methods, None)
    assert [(row.target, row.tag, row.bound, row.place) for row in methods.rows] == [
        (
            "arvl_to_dcsn",
            "!monte_carlo",
            "!monte_carlo",
            recipe.Place(tenure_methods, "arvl_to_dcsn.method", 47),
        ),
        (
            "cntn_to_dcsn.evaluate[V]",
            "!Linear",
            "!Linear",
            recipe.Place(tenure_methods, "cntn_to_dcsn.evaluate[V].method", 38),
        ),
        (
            "dcsn_to_arvl.value.E_ε",
            "!tauchen",
            "!tauchen",
            recipe.Place(tenure_methods, "dcsn_to_arvl.value.E_ε.method", 45),
        ),
        ("policy", "!max", "!max", recipe.Place(tenure_methods, "policy.method", 34)),
    ]
    # each row offers the words the package admits at its place, the
    # branching stage's places listed as any stage's (unit L, Task 18)
    assert recipe.places_refusal(tenure.stage) is None
    for row in methods.rows:
        assert row.choices == admitted_methods(tenure.stage, row.target)

    keeper = bound(KEEPER_CONS, "keeper_cons")
    methods = recipe.methods_tab(folder, keeper.stage, keeper.record, "keeper_cons")
    assert (methods.file, methods.sentence) == (keeper_methods, None)
    evaluate = recipe.Place(keeper_methods, "cntn_to_dcsn.evaluate.method", 60)
    assert [(row.target, row.tag, row.place) for row in methods.rows] == [
        ("cntn_to_dcsn.evaluate", "!Linear", evaluate),
        ("policy", "!egm", recipe.Place(keeper_methods, "policy.method", 44)),
    ]
    refused = recipe.write_method(
        folder, keeper.record, "keeper_cons", "cntn_to_dcsn.evaluate", "!Linear", "*pchip"
    )
    assert (refused.saved, refused.reason) == (False, "*pchip is no word of the method table")
    written = recipe.write_method(
        folder, keeper.record, "keeper_cons", "cntn_to_dcsn.evaluate", "!Linear", "!pchip"
    )
    assert written.saved
    lines[keeper_methods][59] = lines[keeper_methods][59].replace("!Linear(", "!pchip(", 1)
    assert written.text == "\n".join(lines[keeper_methods])

    # no other file of the copy changed, and no file was added
    assert sorted(git(scratch_durables, "status", "--porcelain").splitlines()) == [
        f" M {path}" for path in sorted(before)
    ]
    assert all(
        (scratch_durables / path).read_text(encoding="utf-8") == "\n".join(lines[path])
        for path in before
    )

    # the tabs read again show each value written
    tenure = bound(TENURE, "tenure")
    rows = recipe.parameters_tab(folder, tenure.stage, tenure.record, "tenure").rows
    assert {row.name: (row.value, row.place) for row in rows if row.name in ("R", "Y")} == {
        "R": ("1.05", recipe.Place(calibration, "calibration.R", r_line)),
        "Y": (original_y, places["Y"]),
    }
    settings_rows = recipe.settings_tab(folder, tenure.stage, tenure.record, "tenure").rows
    assert settings_rows[1].value == "400"
    keeper = bound(KEEPER_CONS, "keeper_cons")
    rows = recipe.methods_tab(folder, keeper.stage, keeper.record, "keeper_cons").rows
    assert [(row.target, row.tag) for row in rows][0] == ("cntn_to_dcsn.evaluate", "!pchip")
    # the text written for `keeper_upper_envelope` lies outside the set the
    # keeper's addition declares, so the package refuses it at this binding
    # (decision S7-S1)
    (note,) = keeper.notes
    assert keeper.failures[0].rule == "setting-outside-set"
    assert "keeper_upper_envelope" in note and "lies outside the declared set" in note

    # the copy as the fixture made it, for the steps that follow
    for path, data in before.items():
        (scratch_durables / path).write_bytes(data)
    assert git(scratch_durables, "status", "--porcelain") == ""

    # the panel in the page: the folder opens on its recipe, and tenure.bl
    # from the tree is bound as its first occurrence, then as periods[3]
    page.goto(server_on(scratch_durables))
    wait_until(
        lambda: open_path_shown(page) == RECIPE_FILE,
        60.0,
        "the recipe open",
    )
    reveal_in_tree(page, TENURE)
    page.click(f'.bl-tree-file[data-path="{TENURE}"]')
    wait_until(lambda: recipe_head(page) == "periods[0] / tenure", 120.0, "periods[0] / tenure")
    choose_option(page, ".bl-recipe-positions", "periods[3] / tenure")
    wait_until(lambda: recipe_head(page) == "periods[3] / tenure", 60.0, "periods[3] / tenure")
    tabs = page.locator(".bl-class-tab")
    assert tabs.evaluate_all("(found) => found.map((tab) => tab.dataset.tab)") == [
        "Fields",
        "Parameters",
        "Settings",
        "Methods",
    ]
    assert page.locator(".bl-class-tab.bl-active").get_attribute("data-tab") == "Fields"

    def chosen(tab: str) -> None:
        # the tab `tab` chosen in the panel's bar, and drawn
        page.click(f'.bl-class-tab[data-tab="{tab}"]')
        page.wait_for_selector(f'.bl-values[data-tab="{tab}"]', timeout=10_000)

    def value(name: str) -> str | None:
        # the value in the input of the row `name` of the tab shown
        cell = page.locator(f'.bl-values-row[data-name="{name}"] .bl-values-value')
        return cell.input_value() if cell.count() else None

    chosen("Parameters")
    assert page.locator(".bl-values-file").text_content() == f"writes {wages}"
    assert (value("R"), value("Y")) == ("1.045", original_y)
    # the row's name is the button that opens its file at its line (unit R,
    # R-D23)
    link = page.locator('.bl-values-row[data-name="R"] .bl-values-name button')
    assert link.get_attribute("data-path") == calibration
    assert link.get_attribute("data-line") == str(r_line)
    assert link.get_attribute("aria-description") == f"{calibration}:{r_line}"
    chosen("Settings")
    assert page.locator(".bl-values-file").text_content() == f"writes {settings}"
    assert value("n_a") == "300"
    declared = page.locator('.bl-values-row[data-name="n_a"] .bl-values-detail')
    assert declared.text_content() == "ℕ"
    chosen("Methods")
    assert page.locator(".bl-values-file").text_content() == f"writes {tenure_methods}"
    assert page.locator(".bl-values-sentence").count() == 0
    assert page.locator(".bl-values-row").count() == 4
    assert page.locator(".bl-values-method").count() == 4

    chosen("Parameters")
    cell = page.locator('.bl-values-row[data-name="R"] .bl-values-value')
    cell.fill("1.05")
    cell.press("Enter")
    calibration_lines = before[calibration].decode("utf-8").split("\n")
    calibration_lines[r_line - 1] = "  R: 1.05"
    wait_until(
        lambda: (scratch_durables / calibration).read_text(encoding="utf-8")
        == "\n".join(calibration_lines),
        10.0,
        "1.05 written for R through the page",
    )
    reveal_in_tree(page, calibration)
    mark = page.locator(f'.bl-tree-file[data-path="{calibration}"] .bl-tree-mark')
    wait_until(lambda: mark.text_content() == "M", 10.0, "the tree's mark of the written file")
    cell = page.locator('.bl-values-row[data-name="y_R"] .bl-values-value')
    cell.fill("[1, 2")
    cell.press("Enter")
    # the row's input marked, and the sentence in the list under the error
    # mark with the source file and line of y_R
    marked = '.bl-values-row[data-name="y_R"] .bl-values-value.bl-refusal-mark'
    page.locator(marked).wait_for(timeout=10_000)
    sentence = "[1, 2 does not read as YAML"
    wait_until(
        lambda: (sentence, wages, places["y_R"].line) in error_lines(page),
        10.0,
        "the refused value's sentence in the list under the error mark",
    )
    # the tab drawn again with the mark shows the value written for R
    assert value("R") == "1.05"
    chosen("Settings")
    chosen("Parameters")
    wait_until(lambda: value("R") == "1.05", 10.0, "the tab showing 1.05 for R")
    assert git(scratch_durables, "status", "--porcelain").splitlines() == [f" M {calibration}"]
    assert (scratch_durables / calibration).read_text(encoding="utf-8") == "\n".join(
        calibration_lines
    )

    # the tab Fields of the branching stage (A2-D12): at `cntn`, one group
    # per branch, headed by the control `d` that selects it, then the group
    # of the fields every branch holds, including the two incoming ages,
    # each group with its own +
    page.click('.bl-class-tab[data-tab="Fields"]')
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=10_000)
    cntn = page.locator('.bl-class-perch[data-perch="cntn"]')
    assert cntn.locator(".bl-class-branch").all_text_contents() == [
        "cntn · d = keep",
        "cntn · d = adjust",
        "cntn · all branches",
    ]
    groups = {}
    for row in page.evaluate(TABLE_ROWS_JS):
        if row["perch"] == "cntn":
            groups.setdefault(row["group"], []).append(row["field"])
    assert groups == {
        "cntn/keep": ["w_kp", "h_kp", "z_kp", "V_kp[>]"],
        "cntn/adjust": ["w_adj", "z_adj", "V_adj[>]"],
        "cntn/all branches": ["age_kp[>]", "age_adj[>]"],
    }
    assert [
        cntn.locator(f'.bl-class-group[data-group="cntn/{name}"] .bl-add-button').count()
        for name in ("keep", "adjust", "all branches")
    ] == [1, 1, 1]

    # a set entered in the group `keep`, then saved, changes the declaration
    # of z_kp in that branch's block, line 23, and no other byte: z_adj of
    # `adjust`, line 28, keeps its set
    text = (scratch_durables / TENURE).read_text(encoding="utf-8")
    assert [text.split("\n")[n - 1] for n in (23, 28)] == [
        "    [label=keep, () -> (w_kp : ℝ₊₊, h_kp : ℝ₊₊, z_kp : ℝ₊₊) : !cntn] {",
        "    [label=adjust, () -> (w_adj : ℝ₊₊, z_adj : ℝ₊₊) : !cntn] {",
    ]
    cell = page.locator('.bl-class-row[data-identity="tenure:cntn:z_kp"] .bl-class-set')
    cell.fill("ℝ₊")
    cell.press("Enter")
    keep = "    [label=keep, () -> (w_kp : ℝ₊₊, h_kp : ℝ₊₊, z_kp : ℝ₊) : !cntn] {"
    text = edited(text, 23, keep)
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == text, 5.0, "the set of z_kp in the text")
    page.click(".bl-save")
    wait_until(
        lambda: (scratch_durables / TENURE).read_text(encoding="utf-8") == text,
        10.0,
        "the set of z_kp saved",
    )
    assert settled_status(page, digest7(text), 60.0)["state"] == "constructed"
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=10_000)

    # a field added in the group `all branches`, then saved, is written into
    # the block of every branch, lines 23 and 28, and no other byte changes;
    # the loop then refuses the text, since each branch writes fields of its
    # own (the language's rule `declared-once`)
    box = cntn.locator('.bl-class-group[data-group="cntn/all branches"] .bl-add-field')
    box.locator('[data-entry="field"]').fill("x")
    box.locator('[data-entry="set"]').fill("ℝ₊")
    box.locator('[data-entry="role"]').select_option("state")
    box.locator(".bl-add-button").click()
    note = cntn.locator('.bl-class-group[data-group="cntn/all branches"] .bl-class-note')
    note.wait_for(timeout=5_000)
    assert note.text_content() == "x : ℝ₊ written to lines 23 and 28"
    keep = "    [label=keep, () -> (w_kp : ℝ₊₊, h_kp : ℝ₊₊, z_kp : ℝ₊, x : ℝ₊) : !cntn] {"
    adjust = "    [label=adjust, () -> (w_adj : ℝ₊₊, z_adj : ℝ₊₊, x : ℝ₊) : !cntn] {"
    text = edited(edited(text, 23, keep), 28, adjust)
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == text, 5.0, "x in the block of each branch")
    page.click(".bl-save")
    wait_until(
        lambda: (scratch_durables / TENURE).read_text(encoding="utf-8") == text,
        10.0,
        "x saved",
    )
    assert sorted(git(scratch_durables, "status", "--porcelain").splitlines()) == [
        f" M {calibration}",
        f" M {TENURE}",
    ]
    assert settled_status(page, digest7(text), 60.0)["state"] == "parsed, refused"


def test_item_5_the_add_buttons_read_plus_and_the_handle_resizes_the_panes(
    page, server_on, lifecycle_folder
):
    """With `declaration/stages/cons/cons.bl` of the lifecycle registry
    open, the button that adds a variant, `New variant` in the head of the
    folder column, is the icon button of the Codicon `versions`, which
    prints no text, its hover saying what it writes and its accessible name
    its word; the button that adds a field, `+` in the last row of each
    table of the BellmanType panel, the icon button of the Codicon `add`,
    prints no text, its hover `Add field` and its accessible name `Add field
    at` and its table's perch (unit L, Task 29; design pass 6 §§3.6 and
    3.7, AAS, L-D24); `New trellis` is the icon button of the Codicon
    `new-folder`, its word its accessible name (A2-D10; the amendment's §6
    rule 1; design pass 8 §§3 and 6, unit M, Task 6). The folder's bar no
    longer holds `add stage` and `add period`, whose forms open from the
    forward trellis graph (model interface specification 0.4, §3.6; unit
    J's item 5).

    The handle between the panes, on the right edge of the BellmanSym pane,
    sizes that pane (A2-D11; the amendment's §6 rule 2). The test drags the
    handle with the mouse: the pane's right edge follows the pointer; past
    the least width, the pane is 300 px wide (spec 0.4 §5.1; R-D14); after
    the release, the pane keeps its width through a reload of the page; with
    cons.bl opened again, a window too narrow for that width leaves the
    Semantic graph pane its least width, 300 px, and narrows the BellmanSym
    pane, which has its kept width again in the wide window; and a double
    click returns the pane to its default width, which a further reload
    keeps."""
    open_file(page, server_on(lifecycle_folder), CONS, minimum=4)
    page.wait_for_selector(".bl-class-row", timeout=10_000)
    variants = page.locator(".bl-new-variant")
    assert variants.count() >= 1
    for number in range(variants.count()):
        shown = variants.nth(number).evaluate(BUTTON_SHOWN_JS)
        assert (shown["text"], shown["title"], shown["label"]) == (
            "",
            "Write a variant of spec.yml",
            "New variant",
        )
        assert variants.nth(number).get_attribute("icon") == "versions"
    perches = {"arvl": "arrival", "dcsn": "decision", "cntn": "continuation"}
    adds = page.locator(".bl-add-button")
    assert adds.count() >= 1
    for number in range(adds.count()):
        add = adds.nth(number)
        perch = add.evaluate("(button) => button.closest('.bl-class-perch').dataset.perch")
        shown = add.evaluate(BUTTON_SHOWN_JS)
        assert (shown["text"], shown["title"], shown["label"]) == (
            "",
            "Add field",
            f"Add field at {perches[perch]}",
        )
    trellis_button = page.locator(".bl-new-trellis")
    assert trellis_button.evaluate("(button) => button.label") == "New trellis"
    assert trellis_button.get_attribute("icon") == "new-folder"

    pane = page.locator(".bl-file")
    handle = page.locator('.bl-handle[data-handle="file"]')

    def width() -> float:
        return pane.bounding_box()["width"]

    def right_edge() -> float:
        found = pane.bounding_box()
        return found["x"] + found["width"]

    default, edge = width(), right_edge()
    least = 300
    box = handle.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    # at 1600 px the graph and Matsya hold 34 px above their least widths,
    # which the pane may take (spec 0.4 §5.1; unit R, Task 12)
    for moved in (30, -120):
        page.mouse.move(x + moved, y, steps=4)
        assert abs(right_edge() - (edge + moved)) < 1
    # the pointer near the pane's left edge, far past the least width
    page.mouse.move(pane.bounding_box()["x"] + 10, y, steps=4)
    assert abs(width() - least) < 0.5
    page.mouse.move(x - 120, y, steps=4)
    page.mouse.up()
    kept = width()
    assert abs(kept - (default - 120)) < 1

    page.reload()
    handle.wait_for(timeout=60_000)
    wait_until(lambda: abs(width() - kept) < 0.5, 30, "the kept width after the reload")

    # the reload opens the folder on its recipe, whose trellis view folds
    # Matsya and gives the graph its width (unit K's decision K-D6); cons.bl
    # is opened again, so that the graph's least width is read in its view
    reveal_in_tree(page, CONS)
    page.click(f'.bl-tree-file[data-path="{CONS}"]')
    wait_until(lambda: status_settled_on(page, CONS), 60, "cons.bl after the reload")
    view = page.locator(".bl-view")
    page.set_viewport_size({**VIEWPORT, "width": 1056})
    wait_until(
        lambda: abs(view.bounding_box()["width"] - least) < 0.5, 10, "the view at its least width"
    )
    assert least - 0.5 < width() < kept
    page.set_viewport_size(VIEWPORT)
    wait_until(lambda: abs(width() - kept) < 0.5, 10, "the kept width in the wide window")

    handle.dblclick()
    wait_until(
        lambda: abs(width() - default) < 0.5, 10, "the default width after the double click"
    )
    page.reload()
    # the view drawn after the reload, so that the window's component has
    # applied the sizes kept for the folder
    wait_for_view(page, minimum=4, timeout=60_000)
    assert abs(width() - default) < 0.5
