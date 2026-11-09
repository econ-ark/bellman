"""A listed input no line reads is a problem to review, not a refusal (the
brief of 17 October 2026 on the elaborator's diagnostic, acceptance item 4).

The portfolio model's `cons.bl`, with the header of its value block made to
list a second value input, `W[>]`, that no line of the block reads: with the
file open, the loop elaborates the stage and the view draws it; the package's
diagnostic stands in the list under the error mark as a line to review, with
the file and the line of the header, under the heading `Headers to check`,
and the mark counts it among the problems to review and not among the
errors. The fixture was re-recorded in unit D3 of Model Interface 0.9, since
the policy header the earlier fixture read lists `V[>]` alone, which its line
reads (AMD-MB-001).
"""

from __future__ import annotations

import ipyvuetify as v
import solara
from workbench_support import CONS, drawn_text

from bellman_workbench import app

HEADER = (
    "[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> "
    "(V : [-inf, inf) @ !vlu) : !dcsn] {"
)
LISTED = HEADER.replace("@ !vlu, c)", "@ !vlu, W[>] : ℝ @ !vlu, c)")
SENTENCE = "the header lists `W[>]`, which no line of the block reads"


def test_item_4_a_listed_input_no_line_reads_is_listed_to_review_and_the_stage_is_drawn(
    app_state, scratch_folder
):
    stage = scratch_folder / CONS
    text = stage.read_text(encoding="utf-8")
    assert text.count(HEADER) == 1
    stage.write_text(text.replace(HEADER, LISTED), encoding="utf-8")
    app_state(scratch_folder)
    app.open_file(CONS)
    app.run_loop()
    current = app.shown.value
    assert current is not None and current.path == CONS
    assert all(graph["nodes"] for graph in current.collection["graphs"])
    lines = stage.read_text(encoding="utf-8").splitlines()
    header_line = 1 + next(n for n, line in enumerate(lines) if line.startswith("[id=cntn_to_dcsn"))

    standing = app.standing_refusals()
    (listed,) = [item for item in standing if item.rule == "unread-input"]
    assert (listed.sentence, listed.file, listed.line) == (SENTENCE, CONS, header_line)
    assert listed.severity == "warning"
    assert (listed.diagnostic.kind, listed.diagnostic.operation) == ("check", "elaborate")
    errors = [item for item in standing if item.severity == "error"]
    review = [item for item in standing if item.severity != "error"]

    app.errors_open.value = True
    _, rendered = solara.render(app.ErrorMark(), handle_error=False)
    try:
        # the mark's class carries `bl-has-errors` and `bl-active` as well
        # where errors stand and the list is open
        (button,) = [
            item for item in rendered.find(v.Html, tag="button").widgets
            if "bl-error-mark" in (item.class_ or "").split()
        ]
        plural = "" if len(errors) == 1 else "s"
        assert button.attributes["aria-label"] == (
            f"Problems: {len(errors)} error{plural}, {len(review)} to review"
        )
        headings = [
            drawn_text(item) for item in rendered.find(v.Html, class_="bl-problem-heading").widgets
        ]
        assert "Headers to check" in headings
        lines = rendered.find(v.Html, class_="bl-error-line").widgets
        sentences = [drawn_text(line.children[0]) for line in lines]
        assert sentences.count(SENTENCE) == 1
        (line,) = [line for line in lines if drawn_text(line.children[0]) == SENTENCE]
        assert line.attributes["data-severity"] == "warning"
    finally:
        rendered.close()
        app.errors_open.value = False
