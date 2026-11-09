"""Starting an empty model and navigating Files through the Workbench page."""

import yaml

from workbench_support import (
    new_tab,
    open_workbench,
    wait_until,
)


def test_an_empty_trellis_opens_its_recipe_and_offers_the_first_stage(browser, server_on, tmp_path):
    starter = tmp_path / "starter"
    starter.mkdir()
    folder = tmp_path / "inventory"
    context, page = new_tab(browser)
    try:
        open_workbench(page, server_on(starter, matsya_command="off"))
        page.set_viewport_size({"width": 390, "height": 780})
        # the narrow layout shows one pane, so one button named `New trellis`
        # is exposed once it has taken effect; the click waits for that
        new_trellis = page.get_by_role("button", name="New trellis", exact=True)
        wait_until(lambda: new_trellis.count() == 1, 5.0, "one New trellis button")
        new_trellis.click()
        page.fill(".bl-create-name input", "inventory")
        page.fill(".bl-create-repeat input", "2")
        page.click(".bl-create-submit")
        page.set_viewport_size({"width": 1600, "height": 1000})
        page.wait_for_selector(
            '.bl-tree-file.bl-open[data-path="declaration/spec.yml"]', timeout=12_000
        )
        first = page.get_by_role("button", name="Write first stage")
        first.wait_for(timeout=5_000)
        assert page.get_by_text("No stages to check yet", exact=True).first.is_visible()
        assert page.locator(".bl-error-mark").get_attribute("aria-label") == "Problems: none reported"
        first.click()
        form = page.locator('.bl-form[data-form="new stage"]')
        assert "stages list" in form.inner_text()
        page.fill(".bl-new-stage-key input", "inventory")
        page.click(".bl-new-stage-submit")
        path = "declaration/stages/inventory/inventory.bl"
        page.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{path}"]', timeout=12_000)
        assert (folder / path).read_text().startswith("@stage: inventory\n")
        period = (folder / "declaration/period.yml").read_text().removeprefix("!period\n")
        assert yaml.safe_load(period)["stages"] == ["inventory"]
    finally:
        context.close()


def test_files_tree_focus_moves_without_opening_a_file(browser, server_on, model_folder):
    context, page = new_tab(browser)
    try:
        open_workbench(page, server_on(model_folder, matsya_command="off"))
        tree = page.get_by_role("tree", name="Files")
        tree.wait_for(timeout=5_000)
        rows = tree.get_by_role("treeitem")
        wait_until(lambda: rows.count() > 2, 5, "file rows")
        page.locator(".bl-new-trellis").focus()
        for _ in range(20):
            page.keyboard.press("Tab")
            if tree.locator('[role="treeitem"]:focus').count():
                break
        focused = tree.locator('[role="treeitem"]:focus')
        assert focused.count() == 1
        assert rows.locator("xpath=self::*[@tabindex='0']").count() == 1
        page.keyboard.press("Home")
        assert focused.get_attribute("data-path") == "declaration"
        if focused.get_attribute("aria-expanded") == "true":
            page.keyboard.press("ArrowLeft")
            wait_until(lambda: focused.get_attribute("aria-expanded") == "false", 5, "folder closed")
        page.keyboard.press("ArrowRight")
        wait_until(lambda: focused.get_attribute("aria-expanded") == "true", 5, "folder open")
        tree.locator('[role="treeitem"][data-path^="declaration/"]').first.wait_for(timeout=5_000)
        page.keyboard.press("ArrowRight")
        assert focused.get_attribute("data-path").startswith("declaration/")
        page.keyboard.press("ArrowLeft")
        assert focused.get_attribute("data-path") == "declaration"
        page.keyboard.press("ArrowDown")
        page.keyboard.press("ArrowUp")
        assert focused.get_attribute("data-path") == "declaration"
        page.keyboard.press("End")
        last = focused.get_attribute("data-path")
        assert last == rows.last.get_attribute("data-path")
        assert focused.get_attribute("aria-current") != "page"
        page.keyboard.press("Enter")
        wait_until(
            lambda: tree.locator('[aria-current="page"]').get_attribute("data-path") == last,
            5,
            "file opened",
        )
        page.keyboard.press("Tab")
        assert focused.count() == 0
    finally:
        context.close()
