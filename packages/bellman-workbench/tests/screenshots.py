"""Writes the screenshots of Bellman Workbench's window over one model
folder: the four the report of unit A1 names (model interface
specification 0.3, §12 A1 item 5), or the trellis of unit B:

- `01-opened.png`, the window as it opens on the first stage file of a
  folder that holds no recipe and no trellis file, or on the file `--file`
  names;
- `04-status.png`, the window with the status line's details and git's
  line shown under the button `more`;
- `02-layer-panel.png`, the panel of the first builder of the drawn graph;
- `03-refused-direction.png`, the one refusing node of a refused builders
  graph with its panel, written only when the open file's state names a
  refused direction (`entrepreneur_death.bl` of
  `applications/cagetti-denardi-2006`);
- `05-trellis.png`, the trellis of the trellis file or the recipe `--trellis`
  names, restricted as `--restriction` is typed into the view's input and
  scaled by `--zoom-in` presses of the button `zoom in` where those options
  are given, written in place of the four others when `--trellis` is given.

With `--frames`, in place of all of these, the frames of item 6 of unit R
(model interface specification 0.4, §8; Task 15 of unit R's plan), each
at 1600 and at 1200 pixels wide and 1000 high, named
`<width>-<n>-<frame>.png`: the five states of `workbench_support.STATES`,
then the folder folded, Matsya folded and Goto Anything open on `@cntn`,
then each form of `workbench_support.PAGE_FORMS` open over the forward
trellis graph of the folder's recipe (unit L, Task 9; AAS, L-D8), as
design pass 4 §3 draws it, the first template of `new trellis` and of
`add stage` chosen and the form from a folder on the corpus's stage folder
of `port` (Task 23; L-D14), and last the stage list that the button
`stages` opens over that graph (design pass 4 §4); and
`contrast.json`, the rows of `workbench_support.contrast_rows` of each
frame, by its width and its name. `<folder>` is then a copy of
`applications/portfolio-choice`, whose `declaration/stages/cons/cons.bl`
the states read; the frames are taken over copies of it, and over a copy
of `applications/cons-port` for the trellis, in a temporary folder, so that
nothing is written into `<folder>`.

Usage, from the checkout's root with its virtual environment, where
`tests/` is `packages/bellman-workbench/tests/`:

    python tests/screenshots.py <folder> <out>
    python tests/screenshots.py <folder> <out> --file <relpath>
    python tests/screenshots.py <folder> <out> --trellis <relpath>
    python tests/screenshots.py <folder> <out> --trellis <relpath> \
        --restriction "periods 0–1" --zoom-in 2
    python tests/screenshots.py <folder> <out> --frames

The server is started on a free port through the console command's own
command line and environment and stopped at the end; Chromium is launched
as the tests launch it, headless, from the executable the environment
variable BELLMAN_WORKBENCH_CHROMIUM names when that is set, else Playwright's
own (`workbench_support.launch_chromium`); the window is 1600 by 1000
pixels but for the frames at 1200. The functions that read and drive the
page are those of `workbench_support.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workbench_support import (  # noqa: E402  (the path above makes the module importable)
    FRAME_TRACKS,
    HELD_COLLECTION_JS,
    MATSYA_FOLD,
    PAGE_FORMS,
    RECIPE_FILE,
    ROOT,
    STATES,
    TRELLIS_TRACKS,
    applications_copy,
    choose_view,
    contrast_rows,
    free_port,
    goto_results,
    launch_chromium,
    new_tab,
    open_goto,
    open_page_form,
    open_path_shown,
    open_stage_list,
    open_trellis,
    panel_head,
    repository_copy,
    restrict,
    reveal_in_tree,
    select_node,
    server_error,
    show_state,
    show_status,
    start_server,
    status_settled_on,
    stop_server,
    svg_texts,
    tracks_near,
    trellis_settled,
    wait_for_view,
    wait_until,
    write_refused_cons,
)

# The widths in pixels at which the frames are taken (R-D59: 1600 and 1200)
# and the height of every frame.
FRAME_WIDTHS = (1600, 1200)
FRAME_HEIGHT = 1000
# The frames taken after the five states, each from cons.bl constructed.
OTHER_FRAMES = ("folder folded", "Matsya folded", "palette open")
# The frames of the forms, each form open over the forward trellis graph of
# the folder's recipe (unit L, Task 9), and last the frame of the stage list
# open over that graph (Task 23; design pass 4 §4).
FORM_FRAMES = tuple(f"form {form}" for form in PAGE_FORMS)
LIST_FRAMES = ("stage list",)
# the corpus's stage folder of `port`, which the frame of the form from a
# folder types in its field (Task 23)
PORT_STAGE_FOLDER = ROOT / "applications/portfolio-choice/declaration/stages/port"

# the seconds the page may take to draw and to settle: the pension stage's
# loop takes several seconds on a cold server
PAGE_SECONDS = 90


def drawn_graph(status: str) -> str:
    """The id of the builders graph the view draws for `status`: `forward`
    when the backward graph is refused, else `backward`."""
    return "forward" if "backward refused" in status else "backward"


def refused_direction(status: str) -> str | None:
    """The direction `status` names as refused, None when it names none."""
    for direction in ("forward", "backward"):
        if f"{direction} refused" in status:
            return direction
    return None


def first_layer(page, graph: str) -> str | None:
    """The viewer's id of the first layer the view opens in `graph`, read
    from the collection the element holds; None when the graph has no
    layer."""
    from bellman.stage import LAYER_ID_ENDING, layers_to_open

    layers = layers_to_open(page.evaluate(HELD_COLLECTION_JS), graph, 1)
    return f"{layers[0]}{LAYER_ID_ENDING}" if layers else None


def write_screenshots(url: str, out: Path, relpath: str | None) -> list[Path]:
    """Opens the page at `url` in headless Chromium, clicks `relpath` in the
    tree when one is given, and writes the screenshots into `out`; answers
    the files written."""
    from playwright.sync_api import sync_playwright

    written = []

    def shot(page, name: str) -> None:
        path = out / name
        page.screenshot(path=str(path))
        written.append(path)

    with sync_playwright() as playwright:
        browser = launch_chromium(playwright)
        context, page = new_tab(browser)
        try:
            page.goto(url)
            page.wait_for_selector(".bl-tree-file", timeout=PAGE_SECONDS * 1000)
            if relpath is not None:
                reveal_in_tree(page, relpath, PAGE_SECONDS * 1000)
                page.click(f'.bl-tree-file[data-path="{relpath}"]')
            else:
                relpath = wait_until(lambda: open_path_shown(page), 30.0, "a file open")[0]
            status = wait_until(
                lambda: status_settled_on(page, relpath), PAGE_SECONDS, f"the loop of {relpath}"
            )[0]
            wait_for_view(page, 4, PAGE_SECONDS * 1000)
            page.wait_for_timeout(500)
            print(f"status: {status}")
            shot(page, "01-opened.png")

            show_status(page)
            page.wait_for_timeout(300)
            shot(page, "04-status.png")

            graph = drawn_graph(status)
            layer = first_layer(page, graph)
            if layer is not None:
                select_node(page, layer, graph)
                page.wait_for_selector(".bl-signature", timeout=10_000)
                page.wait_for_timeout(300)
                print(f"layer panel: {panel_head(page)}")
                shot(page, "02-layer-panel.png")

            direction = refused_direction(status)
            if direction is not None:
                choose_view(page, "operator", direction)
                wait_until(
                    lambda: any("refused" in text for text in svg_texts(page)),
                    15.0,
                    "the refusing node drawn",
                )
                select_node(page, f"{direction}:refused", direction)
                page.wait_for_selector(".bl-item-button", timeout=10_000)
                page.wait_for_timeout(300)
                print(f"refusing node's panel: {panel_head(page)}")
                shot(page, "03-refused-direction.png")
        finally:
            context.close()
            browser.close()
    return written


def write_trellis_screenshot(
    url: str, out: Path, relpath: str, restriction: str | None = None, zoom_in: int = 0
) -> Path:
    """Opens the page at `url`, clicks the trellis file or the recipe
    `relpath` in the tree, waits for its trellis to be drawn, types
    `restriction` into the view's input and presses Enter where one is
    given, waiting for the restricted trellis to be drawn, presses the
    button `zoom in` `zoom_in` times about the view's center, within scale
    one, and writes `05-trellis.png`
    into `out`; answers the file written."""
    from playwright.sync_api import sync_playwright

    path = out / "05-trellis.png"
    with sync_playwright() as playwright:
        browser = launch_chromium(playwright)
        context, page = new_tab(browser)
        try:
            page.goto(url)
            selector = f'.bl-tree-file[data-path="{relpath}"]'
            reveal_in_tree(page, relpath, PAGE_SECONDS * 1000)
            page.click(selector)
            wait_until(
                lambda: trellis_settled(page, relpath), PAGE_SECONDS, f"the trellis of {relpath}"
            )
            wait_for_view(page, 20, PAGE_SECONDS * 1000)
            if restriction is not None:
                restrict(page, restriction)
                wait_until(
                    lambda: " · shown " in (trellis_settled(page, relpath) or ""),
                    PAGE_SECONDS,
                    f"the trellis of {relpath} restricted to {restriction}",
                )
                wait_for_view(page, 20, PAGE_SECONDS * 1000)
            for _ in range(zoom_in):
                page.wait_for_timeout(500)
                page.click('.bl-zoom-button[data-zoom="zoom in"]')
            # the pointer, left where the click was, would draw the table's
            # cell under it in the hover color; the panel's empty foot has none
            page.mouse.move(1200, 850)
            page.wait_for_timeout(500)
            page.screenshot(path=str(path))
        finally:
            context.close()
            browser.close()
    return path


def show_frame(page, frame: str, urls: dict[str, str], width: int) -> None:
    """Brings the page into the frame `frame` at the window's width `width`
    over the server `urls` names for it. The state, a state of STATES or
    cons.bl constructed for the other frames, is brought about at 1600
    pixels (`show_state`), where the folder's tree, through which a file is
    opened, stands open; the window is then narrowed to `width`, and the
    columns are waited for (FRAME_TRACKS, or TRELLIS_TRACKS for the
    trellis, whose view folds Matsya; unit K's decision K-D6). Then the
    folder is folded by its button `files` where the width function has not
    folded it, Matsya is folded by the button of its head, or Goto
    Anything is opened by P with the primary modifier and `@cntn` typed, as
    the frame names. A frame of FORM_FRAMES opens the folder's recipe in
    the trellis view at 1600 pixels, shows its forward graph and opens its
    form there (`open_page_form`), since the folder's bar, which holds the
    buttons of three forms, is folded at 1200 pixels, the form drawn as
    design pass 4 §3 draws it: the first template of `new trellis` and of
    `add stage` chosen, and the corpus's stage folder of `port` typed in the
    field of the form from a folder (Task 23); the window is then narrowed
    with the form open. The frame of LIST_FRAMES opens the stage list by the
    button `stages` there."""
    if frame in FORM_FRAMES:
        open_trellis(page, urls[frame], RECIPE_FILE)
        choose_view(page, None, "forward")
        form = frame.removeprefix("form ")
        selector = open_page_form(page, form)
        if form in ("new trellis", "add stage"):
            page.locator(f"{selector} .bl-template-button").first.click()
            page.wait_for_selector(f"{selector} .bl-create-key")
        elif form == "from a folder":
            field = f"{selector} .bl-folder-path input"
            page.fill(field, str(PORT_STAGE_FOLDER))
            page.press(field, "Enter")
            page.wait_for_selector(f"{selector} .bl-create-key", timeout=30_000)
    elif frame in LIST_FRAMES:
        open_trellis(page, urls[frame], RECIPE_FILE)
        choose_view(page, None, "forward")
        open_stage_list(page)
    else:
        show_state(page, frame if frame in STATES else "constructed", urls[frame])
    page.set_viewport_size({"width": width, "height": FRAME_HEIGHT})
    trellis_view = frame == "trellis" or frame in FORM_FRAMES or frame in LIST_FRAMES
    columns = (TRELLIS_TRACKS if trellis_view else FRAME_TRACKS)[width, False]
    wait_until(lambda: tracks_near(page, columns), 10.0, f"the columns at {width} px")
    if frame == "folder folded":
        fold = page.locator('.bl-fold[data-fold="folder"]')
        if fold.get_attribute("aria-expanded") == "true":
            fold.click()
        page.wait_for_selector(".bl-window[data-folded-folder]", state="attached")
    elif frame == "Matsya folded":
        page.click(MATSYA_FOLD)
        page.wait_for_selector(".bl-window[data-folded-matsya]", state="attached")
    elif frame == "palette open":
        open_goto(page)
        page.keyboard.type("@cntn")
        wait_until(lambda: goto_results(page), 5.0, "the results of @cntn")


def write_frames(folder: Path, out: Path) -> list[Path]:
    """Writes the frames of `--frames` into `out` and answers the files
    written. In a temporary folder it makes a copy of `folder`, a second
    copy whose cons.bl holds the refused text (`write_refused_cons`) and a
    copy of cons-port (`applications_copy`), and starts a server over each
    with a cache folder of its own there; each frame is taken in a new
    browser context at its width, so that no fold or size the page keeps in
    the browser's storage passes from one frame to the next (`show_frame`),
    the pointer moved to the window's lower left corner. The servers are
    stopped at the end."""
    from playwright.sync_api import sync_playwright

    frames = (*STATES, *OTHER_FRAMES, *FORM_FRAMES, *LIST_FRAMES)
    written, rows = [], {}
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        folders = {
            "model": repository_copy(folder, base / "model" / folder.name),
            "refused": repository_copy(folder, base / "refused" / folder.name),
            "trellis": applications_copy(base / "applications"),
        }
        write_refused_cons(folders["refused"])
        processes, servers = [], {}
        try:
            for name, served in folders.items():
                port = free_port()
                url = f"http://localhost:{port}/"
                log_path = base / f"{name}.log"
                process = start_server(served, port, log_path, cache_home=base / "cache")
                processes.append(process)
                error = server_error(url, process, log_path)
                if error is not None:
                    raise RuntimeError(error)
                servers[name] = url
            urls = {frame: servers["model"] for frame in frames}
            urls["trellis"] = servers["trellis"]
            urls["refused before a construction"] = servers["refused"]
            with sync_playwright() as playwright:
                browser = launch_chromium(playwright)
                try:
                    for width in FRAME_WIDTHS:
                        rows[width] = {}
                        for number, frame in enumerate(frames, 1):
                            context, page = new_tab(browser)
                            try:
                                show_frame(page, frame, urls, width)
                                page.mouse.move(1, FRAME_HEIGHT - 1)
                                page.wait_for_timeout(500)
                                name = f"{width}-{number}-{frame.replace(' ', '-')}.png"
                                page.screenshot(path=str(out / name))
                                written.append(out / name)
                                rows[width][frame] = contrast_rows(page)
                            finally:
                                context.close()
                finally:
                    browser.close()
        finally:
            for process in processes:
                stop_server(process)
    contrast = out / "contrast.json"
    contrast.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    written.append(contrast)
    return written


def main(argv: list[str] | None = None) -> int:
    """Starts the server over the folder, writes the screenshots into the
    output folder and stops the server; answers 0, or 1 with the server's
    sentence on standard error when it does not start. With `--frames`,
    writes the frames of `write_frames`, which starts servers of its
    own."""
    parser = argparse.ArgumentParser(
        description="Writes the screenshots of Bellman Workbench's window over one folder."
    )
    parser.add_argument("folder", type=Path, help="the model folder")
    parser.add_argument("out", type=Path, help="the folder the screenshots are written into")
    parser.add_argument(
        "--file", default=None, help="the stage file to open, relative to the folder"
    )
    parser.add_argument(
        "--trellis",
        default=None,
        help="the trellis file or the recipe to draw, relative to the folder",
    )
    parser.add_argument(
        "--restriction",
        default=None,
        help="the restriction typed into the view's input before the trellis's picture",
    )
    parser.add_argument(
        "--zoom-in",
        type=int,
        default=0,
        help="the times the button zoom in is pressed before the trellis's picture",
    )
    parser.add_argument(
        "--frames",
        action="store_true",
        help="the frames of unit R's item 6 and contrast.json, at 1600 and 1200 pixels",
    )
    arguments = parser.parse_args(argv)
    folder = arguments.folder.resolve()
    out = arguments.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if arguments.frames:
        for path in write_frames(folder, out):
            print(f"written {path}")
        return 0
    port = free_port()
    url = f"http://localhost:{port}/"
    with tempfile.TemporaryDirectory() as temporary:
        log_path = Path(temporary) / "solara.log"
        process = start_server(folder, port, log_path)
        try:
            error = server_error(url, process, log_path)
            if error is not None:
                print(error, file=sys.stderr)
                return 1
            written = (
                [
                    write_trellis_screenshot(
                        url, out, arguments.trellis, arguments.restriction, arguments.zoom_in
                    )
                ]
                if arguments.trellis
                else write_screenshots(url, out, arguments.file)
            )
        finally:
            stop_server(process)
    for path in written:
        print(f"written {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
