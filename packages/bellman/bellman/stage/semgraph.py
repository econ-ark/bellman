"""The record of one stored or derived graph (AMD-SG-005).

The construction stands in `construction.py`: the typing of the stage, the fold
of its lines into the definitions table and the rows of the construction table,
the construction of the four stored graphs — the two initial diagrams and the
builder grain of the two builders graphs, each a `Refusal` where it cannot be
constructed — and the stage itself. Every other grain is derived from the
stored graphs by `grains.graph_of(stage, level, direction, grain)`, which
selects and never interprets; the conditions a caller assumes when it selects a
graph are checked here against the conditions of the stage.

`record` returns a `Semgraph`: one stored or derived graph with the sorts of
its inputs and outputs, the conditions of the stage, the parameters its
equations name and the calibration of the version. The conditions a caller
may assume away are read by `conditions_with_assumptions` of
`bellman.native.records`, which stands beneath this module and beneath the
graph queries, so that both read one function.
"""

from bellman.fold.block_lines import require_stage
from bellman.native.records import Semgraph, checked_assumptions, conditions_with_assumptions
from bellman.native.versions import kept_answer
from bellman.stage.grains import grain_token, graph_of, wire_table
from bellman.stage.stage_answers import obligations


def record(stage, *, level, direction, grain="builder", assumptions=()):
    """The record of AMD-SG-005 for one stored graph: the graph itself, the
    sorts of its inputs and outputs, the conditions of the stage
    (`stage_answers.obligations`) with the caller's assumptions in place of
    those they discharge, the sorts of the parameters its equations name, and
    the calibration of the version. `level` is `initial` or `builders` and
    `direction` is `backward` or `forward`; `grain` is a grain the graph
    queries read. The record of a selection is made once per stage."""
    require_stage(stage)
    if level not in ("initial", "builders"):
        raise ValueError("level must be 'initial' or 'builders'")
    if direction not in ("forward", "backward"):
        raise ValueError("record requires direction='forward' or 'backward'")
    grain = grain_token(grain)
    checked_assumptions(assumptions)

    def make():
        graph = graph_of(stage, level, direction, grain)
        conditions = conditions_with_assumptions(obligations(stage), assumptions)
        parameters = () if level == "initial" else wire_table(stage).parameters(direction)
        return Semgraph(
            graph=graph,
            inputs=tuple(graph.dom.inside),
            outputs=tuple(graph.cod.inside),
            obligations=conditions,
            parameters=parameters,
            calibration=stage.bindings.calibration,
        )

    if assumptions:
        return make()
    return kept_answer(stage, ("record", level, direction, grain), make)
