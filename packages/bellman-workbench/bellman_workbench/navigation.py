"""The places of one tab of Bellman Workbench, its history of them, and the
breadcrumb (model interface specification 0.3, amendment AMD-MI-002 §3
rules 3 to 5 and 7): what a place holds, how the history records the place
a handler leaves and steps back and forward, the layers the view opens to
show a place, and the parts of the breadcrumb read from the tab's state.

The module holds no state, reads no file and imports no part of the page:
each function answers new values from its arguments and changes none. The
page, `app.py`, keeps the tab's one history for the tab's life (A2-D5),
and neither the history nor the context of a place is written in the model
folder (rule 7)."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import NamedTuple

from bellman.stage import LAYER_ID_ENDING


class Place(NamedTuple):
    """A place of the tab, the pair of a view and a selection (AMD-MI-002 §3
    rule 4): `view`, `trellis` or `stage`; `recipe`, the source of the tab's
    trellis, a `recipe.Source`, None where the folder offers none;
    `restriction`, the restriction of the trellis view, a
    `trellis.Restriction`, None for the whole trellis; `position`, the head,
    the occurrence `(h, key)` a stage file is bound as, None where none is
    chosen; `file`, the file open in the editor, relative to the folder,
    None before one opens; `graph`, the id of the graph the view shows; and
    `selected`, the node selected in the view, `{"nodeId", "graphId"}`,
    None for none."""

    view: str
    recipe: object
    restriction: object
    position: tuple | None
    file: str | None
    graph: str
    selected: dict | None


class History(NamedTuple):
    """The tab's history of places (AMD-MI-002 §3 rule 4): `behind`, the
    places a step back shows, the last one first; and `ahead`, the places a
    step forward shows, the first one first."""

    behind: tuple = ()
    ahead: tuple = ()


def moved(left: Place, arrived: Place) -> bool:
    """Whether the tab moved from `left` to `arrived`: their view, recipe,
    position or file differ. A change of the selection alone is no move, as
    the brief of AMD-MI-002 decides in its rule 4, and neither is a change
    of the graph or of the restriction alone."""
    return (left.view, left.recipe, left.position, left.file) != (
        arrived.view,
        arrived.recipe,
        arrived.position,
        arrived.file,
    )


def visit(history: History, left: Place, arrived: Place) -> History:
    """The history after a handler moved the tab from `left` to `arrived`:
    `left` stands last behind and no place stands ahead, since a new move
    discards the places that steps back put ahead. Where the tab did not
    move (`moved`), or `left` holds no file, as the window does before its
    first file opens, the answer is `history` itself."""
    if left.file is None or not moved(left, arrived):
        return history
    return History((*history.behind, left), ())


def back(history: History, here: Place) -> tuple[History, Place] | None:
    """A step back from `here`: the history with its last place behind taken
    away and `here` put first ahead, and the place taken, which the tab
    shows next; None where no place stands behind."""
    if not history.behind:
        return None
    return History(history.behind[:-1], (here, *history.ahead)), history.behind[-1]


def forward(history: History, here: Place) -> tuple[History, Place] | None:
    """A step forward from `here`, which undoes a step back: the history
    with its first place ahead taken away and `here` put last behind, and
    the place taken, which the tab shows next; None where no place stands
    ahead."""
    if not history.ahead:
        return None
    return History((*history.behind, here), history.ahead[1:]), history.ahead[0]


def opened_layers(defaults, node_id: str, occurrence: str = "") -> list[str]:
    """The namespaces of the layers the view opens to show a place, each
    once: the view's own, `defaults`; where the selected node lies inside a
    stage occurrence of a trellis view, `occurrence`, the address the
    package's `node_place` gives it, `periods[40]/tenure`, that
    occurrence's period and its layer, `periods[40]` and
    `periods[40]/tenure` (AMD-MI-002 §3 rule 4: back to a trellis opens the
    occurrence's period and layer); and, where the selected node `node_id`
    is a layer, `periods[1]/cons/policy___group___` (`LAYER_ID_ENDING`),
    that layer and each layer that holds it. A box inside a closed builder
    is shown by the viewer, which opens the layer that holds a selected
    node."""
    namespaces = list(defaults)
    layer = node_id[: -len(LAYER_ID_ENDING)] if node_id.endswith(LAYER_ID_ENDING) else ""
    for namespace in (occurrence, layer):
        parts = namespace.split("/") if namespace else []
        namespaces += ["/".join(parts[: number + 1]) for number in range(len(parts))]
    return list(dict.fromkeys(namespaces))


# the separator of the breadcrumb's parts, U+203A between two spaces
SEPARATOR = " › "


class Crumb(NamedTuple):
    """One part of the breadcrumb: `text`, what it reads; and `link`, what a
    click on it shows: `folder`, what the folder opens on; `recipe`, the
    recipe's trellis; `period`, that trellis with the period open; None for
    the place shown, the last part."""

    text: str
    link: str | None


def breadcrumb(
    folder: str,
    recipe: str | None = None,
    stage: str | None = None,
    positions: tuple = (),
    chosen: tuple | None = None,
) -> list[Crumb]:
    """The parts of the breadcrumb (AMD-MI-002 §3 rules 3 and 5, A2-D3),
    read from the tab's state, the name of the folder `folder` first. With
    no `stage`, the trellis view of the recipe `recipe`, `durables ›
    spec.yml`. For the stage file `stage` shown, bound through `recipe`,
    whose occurrences there stand at `positions`, each `(h, key)` in the
    order of the periods: at the position `chosen`, where it is one of
    them, `durables › spec.yml › periods[3] › tenure`; at no position
    chosen, the stage's key and then the period of the occurrence it is
    bound as, its first, `durables › spec.yml › tenure › periods[0]`, so
    that the path names the occurrence once and the count of its positions
    stands once, in the select after the path (design pass 13 §3; the fix
    wave Q3b of unit Q, item 19, C19); and where the recipe holds no
    occurrence of the file, or no recipe is given, the file alone,
    `durables › tenure.bl`. The recipe and the stage file are named by
    their file names. Every part but the last is a link, but a stage's key
    at no position chosen; the last is the place shown."""
    parts = [Crumb(folder, "folder")]
    if stage is None:
        if recipe is not None:
            parts.append(Crumb(PurePosixPath(recipe).name, "recipe"))
    elif recipe is None or not positions:
        parts.append(Crumb(PurePosixPath(stage).name, None))
    else:
        parts.append(Crumb(PurePosixPath(recipe).name, "recipe"))
        if chosen in positions:
            h, key = chosen
            parts += [Crumb(f"periods[{h}]", "period"), Crumb(key, None)]
        else:
            h, key = positions[0]
            parts += [Crumb(key, None), Crumb(f"periods[{h}]", None)]
    return [*parts[:-1], parts[-1]._replace(link=None)]
