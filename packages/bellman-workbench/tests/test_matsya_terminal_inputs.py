"""External terminal continuation inputs of a returned declaration."""

import shutil

from workbench_support import ROOT

from bellman_workbench import model, returned


def test_a_constructed_returned_model_lists_only_its_external_terminal_input(tmp_path):
    copy = f"{model.OUTPUT_FOLDER}/pension-retirement"
    shutil.copytree(
        ROOT / "applications/pension-retirement/declaration",
        tmp_path / copy / "declaration",
    )

    inspection = returned.inspect(model.open_folder(tmp_path), copy)

    assert inspection.shown is not None
    assert inspection.missing == inspection.construction == ()
    assert inspection.terminal_inputs == ("V[>] · terminal",)
