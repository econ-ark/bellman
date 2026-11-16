"""Small registries, a trellis file and a connector that the trellis tests
read, copies of model folders that those tests change, and functions that read
the pairs and routes of a trellis."""

import shutil
from pathlib import Path

from application_files import CONS_PORT, PORTFOLIO
from stage_texts import changed

from bellman.trellis import calibrate_trellis, connection_report, elaborate_trellis

# a trellis file of two periods written out, with no inter-period mapping
TWO_PERIOD_TRELLIS_TEXT = "!trellis\nperiods:\n  - stages: [worker]\n  - stages: [worker]\n"

# the six periods of the copies of the portfolio model and of cons-port
SIX_PERIODS = (0, 1, 2, 3, 4, 5)


# the connector of the terminal period of the two-stage durables trellis: the
# continuation fields of the keeper and of the adjuster each join the arrival
# fields a_bq, h_bq and z_bq of the bequest
BEQUEST_CONNECTOR = {
    "a_nxt_kp": "a_bq",
    "h_nxt_kp": "h_bq",
    "z_nxt_kp": "z_bq",
    "a_nxt_adj": "a_bq",
    "h_nxt_adj": "h_bq",
    "z_nxt_adj": "z_bq",
}


def write_files(folder, files):
    """Write the files `files`, each by its path relative to `folder`, under
    `folder`, and return the folder."""
    for relative, text in files.items():
        path = Path(folder) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return Path(folder)


def period_record(stages, connectors=()):
    """One period of the stage occurrences `stages`, by key, with its
    authored connectors."""
    return {"stages": dict(stages), "connectors": list(connectors)}


def selection_of_periods(periods, inter_connectors=()):
    """The selection that the connection report of the elaborated trellis of
    `periods` gives."""
    return connection_report(
        elaborate_trellis({"periods": list(periods), "inter_connectors": list(inter_connectors)})
    ).selection


def printed_pairs(selection):
    """The pairs of a selection as `(writing, reading, address)`, each field
    printed as `periods[h].key.field`."""
    return [(str(pair.writing), str(pair.reading), pair.address) for pair in selection.pairs]


def candidate_groups(selection):
    """The candidate groups of a selection as
    `{destination: {source: [(writing field, reading field, branch)]}}`."""
    return {
        group.destination: {
            candidate.source: [(w.field, r.field, w.branch) for w, r in candidate.pairs]
            for candidate in group.candidates
        }
        for group in selection.candidates
    }


def one_route(selection, source, branch, destination):
    """The one route of a selection from `source` on `branch` into
    `destination`."""
    (route,) = [
        route
        for route in selection.routes
        if (route.source, route.branch, route.destination) == (source, branch, destination)
    ]
    return route


def rejected_pairs(selection):
    """The rejected pairs of a selection as `(writing, reading, rule)`,
    sorted."""
    return sorted((str(r.writing), str(r.reading), r.rule) for r in selection.rejected)


def connection_between(earlier, later, calibration=None):
    """The connection report of two periods of one stage occurrence `bs`
    each, joined by the inter-period mapping `{a: k}`: the stage text
    `earlier` stands at `periods[1]` and `later` at `periods[0]`, each
    calibrated with `calibration` where one is given."""

    def occurrence(text):
        return {
            "stage": {"text": text, "origin": "buffer_stock.bl"},
            "calibration": calibration or {},
            "settings": {},
            "methods": {},
        }

    syntactic = {
        "periods": [
            {"stages": {"bs": occurrence(text)}, "connectors": []} for text in (later, earlier)
        ],
        "inter_connectors": [{"a": "k"}],
    }
    trellis = elaborate_trellis(syntactic)
    if calibration is not None:
        trellis = calibrate_trellis(trellis, syntactic)
    return connection_report(trellis)


# the files that the tests add to the two-node registry of the module
# `bellman.refusal_examples`, `REGISTRY_FILES`, whose one stage is the stage
# `two_nodes` of that module: a range source, a calibration source with a
# parent beside its top key, a replacing selection of the stage `two_nodes`
# beside its addition, and a recipe that names its trellis file, its stage's
# file and two slots, one of them in a range list alone; a methods list takes
# no slot
ADDED_REGISTRY_FILES = {
    "calibration/terminal.yml": "calibration:\n  R: 1.04\n",
    "calibration/child.yml": "parent: calibration/main\ncalibration:\n  R: 1.03\n",
    "stages/two_nodes/methods.other.bl": (
        "@methods: two_nodes\n"
        'n_k : ℕ              :: ["number of candidate levels of the search"]\n'
        "cntn_to_dcsn.method : !vfi(n_c=n_k)\n"
        'cntn_to_dcsn.handler : "test:other"\n'
    ),
    "spec.yml": (
        "trellis: trellis.yml\nstages:\n  two_nodes:\n"
        "    stage: stages/two_nodes/two_nodes.bl\n"
        "    calibration: {all: [calibration/main, $fill], "
        "'0-0': [calibration/terminal, $terminal]}\n"
        "    settings: {all: [settings/main, $fill]}\n"
        "    methods: {all: [stages/two_nodes/methods.bl]}\n"
    ),
}


def declarations_copy(folder):
    """Copy the declaration folders of the portfolio-choice and the cons-port
    applications, `PORTFOLIO` and `CONS_PORT`, under `folder`, each at its
    path in the repository, and return the copied portfolio-choice folder and
    the copied trellis file `trellis.port-cons-vfi.yml`.

    That trellis file is one of the six trellis files of the cons-port
    application that write each stage as a record, which `load_trellis`
    reads; the other five are the files `trellis.reference-*.yml`. The two
    other trellis files of the application, `trellis.cons-port.yml` and
    `trellis.port-cons.yml`, name their stages alone, and the recipes of the
    application give the files of those stages. Every file that the trellis
    file `trellis.port-cons-vfi.yml` names stands inside the copied
    `declaration/`."""
    registry = Path(folder) / "applications/portfolio-choice/declaration"
    shutil.copytree(PORTFOLIO, registry)
    declaration = Path(folder) / "applications/cons-port/declaration"
    shutil.copytree(CONS_PORT, declaration)
    return registry, declaration / "trellis.port-cons-vfi.yml"


def rewrite_once(path, old, new):
    """Write the file `path` with its one occurrence of `old` replaced by
    `new`; a file that holds `old` other than once is refused, so that a
    change of the file in the repository is seen where the copy is made."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        rewritten = changed(text, (old, new))
    except ValueError as refusal:
        raise ValueError(f"{path}: {refusal}") from refusal
    Path(path).write_text(rewritten, encoding="utf-8")


def port_cons_vfi_trellis_file_without_connectors(folder):
    """The copied trellis file of `declarations_copy` under `folder`, with its
    connector `{w: m}` and its one inter-period mapping `{disc.a: k}` each
    emptied to `{}`, so that no line joins `port`'s `w` to `cons`'s `m` or
    `disc`'s `a` to the next period's `k`."""
    _, trellis = declarations_copy(folder)
    rewrite_once(trellis, "- {w: m}", "- {}")
    rewrite_once(trellis, "- {disc.a: k}", "- {}")
    return trellis
