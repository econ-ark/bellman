"""The field each listing of a block header names, read from a stage text
without the construction of the stage (`bellman.stage.header_fields`)."""

from pathlib import Path

import pytest

from bellman.refusals import ConstructionError
from bellman.stage import elaborate_text, header_fields, header_of, source_spans

_STAGES = Path(__file__).resolve().parents[3] / "applications/life-cycle/declaration/stages"


def _read(key):
    """The text of the life-cycle stage file `key` and the origin recorded
    for it."""
    origin = f"applications/life-cycle/declaration/stages/{key}/{key}.bl"
    return (_STAGES / key / f"{key}.bl").read_text(encoding="utf-8"), origin


def test_a_constant_listed_by_a_forward_block_stands_at_the_continuation_perch():
    """`consumption.bl` lists the constant `age_next` on the arrival side of
    its forward block `arvl_to_dcsn`. The backward block `cntn_to_dcsn` takes
    that constant in at the continuation perch, so the listing names the
    field of the continuation perch, as the constructed stage reads it."""
    fields = header_fields(*_read("consumption"))
    held = {address: (str(field.identity), field.role) for address, field in fields.items()}
    assert held["arvl_to_dcsn.in.age_next"] == ("consumption:cntn:age_next", "value")
    assert held["cntn_to_dcsn.in.age_next"] == ("consumption:cntn:age_next", "value")
    assert held["arvl_to_dcsn.in.z_3"] == ("consumption:arvl:z_3", "state")
    assert held["dcsn_to_cntn.in.c"] == ("consumption:dcsn:c", "control")
    assert held["cntn_to_dcsn.in.V[>]"] == ("consumption:cntn:V", "value")
    assert held["dcsn_to_arvl.out.V[<]"] == ("consumption:arvl:V", "value")


@pytest.mark.parametrize("key", ("consumption", "draw", "mortality"))
def test_the_listings_are_those_of_the_span_table_and_the_fields_those_of_the_stage(key):
    """The mapping holds one entry for each listing of the span table, in its
    order, and the fields of each side of a block are those the constructed
    stage reads that side to list (`header_of`), a branch's outputs after one
    another on the output side of their block."""
    text, origin = _read(key)
    fields = header_fields(text, origin)
    spans = source_spans(text, origin)
    listed = [
        address
        for address in spans
        if address.rpartition(".")[0].endswith((".in", ".out"))
    ]
    assert list(fields) == listed
    stage = elaborate_text(text, origin)
    for direction in ("forward", "backward"):
        graph = getattr(stage.initial, direction)
        for name in graph.list().names:
            inputs, outputs = header_of(graph[name].box)
            for side, sorts in (("in", inputs), ("out", outputs)):
                read = [
                    field.identity
                    for address, field in fields.items()
                    if address.split(".")[0] == name and address.split(".")[-2] == side
                ]
                assert read == [sort.identity for sort in sorts], (name, side)


def test_a_text_whose_construction_is_refused_in_a_line_still_answers_its_headers():
    """A line that reads a name nothing declares refuses the construction of
    the stage and leaves the headers as they were, so the mapping is the one
    of the accepted text."""
    text, origin = _read("draw")
    refused = text.replace("a_d = a_2", "a_d = a_2 + nothing_declares_this")
    with pytest.raises(ConstructionError):
        elaborate_text(refused, origin)
    assert {a: (str(f.identity), f.role) for a, f in header_fields(refused, origin).items()} == {
        a: (str(f.identity), f.role) for a, f in header_fields(text, origin).items()
    }


def test_a_header_that_places_no_perch_is_refused_as_the_construction_refuses_it():
    """A side without a perch word, whose field carries no mark, is refused
    under `field-perch`, the rule under which `elaborate_text` refuses it."""
    text, origin = _read("draw")
    unplaced = text.replace("(z_3 : Z, a_3 : Xa) : !cntn", "(z_3 : Z, a_3 : Xa)")
    assert unplaced != text
    with pytest.raises(ConstructionError) as native:
        header_fields(unplaced, origin)
    with pytest.raises(ConstructionError) as constructed:
        elaborate_text(unplaced, origin)
    assert native.value.rule == constructed.value.rule == "field-perch"
