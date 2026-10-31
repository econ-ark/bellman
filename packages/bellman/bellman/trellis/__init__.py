"""The public names of a trellis, `bellman.trellis`, and of the factory route
that assembles one: `read_trellis_file`, which expands the period and
connector records without loading stage files, and the readers
`load_trellis` and `load_recipe`; the
construction `elaborate_trellis`, `accrete` and `changed_positions`; the
binding `calibrate_trellis`, `methodize_trellis`, `configure_trellis`,
`specify_trellis`, `respecify_trellis` and `assemble_trellis`;
`inter_period_joins`, the joins between two periods, `unjoined_fields`,
the state fields no join reaches, and `derivative_missing`, the derivative
readings a route carries that no stage's value meets; `trellis_selection` with its record
`Selection`, the one selection of a trellis's connections (AMD-COMP-001
§3), `connection_report` with its record `ConnectionReport`, which
presents it, and the five transports along a certified route,
`transport_point`, `transport_vector`, `transport_hessian`,
`transport_atoms` and `pull_back`; `diagram_trellis`;
`unpaired_joins` with its two records, the joins of a trellis view that
leave a value unpaired;
`entry_span`, `entry_value`, `replace_entry`, `append_to_mapping`,
`append_to_sequence`, `insert_in_sequence`, `split_entry`,
`remove_from_sequence`, `remove_from_mapping` and `written_at`, which find,
read, replace, append, insert, split and remove one entry of a model's YAML
files as text; `period_entries`, the entry that writes each period of a
trellis file, and `connector_entry` with its record `ConnectorEntry`, the
entry in which a connector line between two unjoined ports is written; and
the names of the view in Model Explorer.
The view's functions that take a stage or a trellis, or
read a view of either, and six of its constants, `BOUNDARY_IDS`,
`LAYER_ID_ENDING` and its colors `LAYER_COLORS`, `NODE_STYLE`,
`OUTPUT_STYLE` and `PERCH_COLORS`, stand in
`bellman.stage` too, naming the same module there: one object in two
tables; `box_attributes` and `INITIAL_IDS` stand in `bellman.stage` alone.
`_EXPORTS` maps each name to the module that defines it, imported when the
name is first used; this package holds the table and nothing else
(`packages/bellman/README.md` §1 and §6).
"""

from importlib import import_module

_EXPORTS = {
    "load_trellis": "bellman.factory.loading",
    "read_trellis_file": "bellman.factory.loading",
    "load_recipe": "bellman.factory.recipe",
    "elaborate_trellis": "bellman.factory.trellis",
    "accrete": "bellman.factory.trellis",
    "changed_positions": "bellman.factory.trellis",
    "calibrate_trellis": "bellman.factory.trellis",
    "methodize_trellis": "bellman.factory.trellis",
    "configure_trellis": "bellman.factory.trellis",
    "specify_trellis": "bellman.factory.trellis",
    "respecify_trellis": "bellman.factory.trellis",
    "assemble_trellis": "bellman.factory.trellis",
    "inter_period_joins": "bellman.factory.joins",
    "unjoined_fields": "bellman.factory.joins",
    "derivative_missing": "bellman.factory.joins",
    "connection_report": "bellman.factory.connections",
    "ConnectionReport": "bellman.factory.connections",
    "trellis_selection": "bellman.factory.connections",
    "Selection": "bellman.factory.connections",
    "transport_point": "bellman.factory.connection_maps",
    "transport_vector": "bellman.factory.connection_maps",
    "transport_hessian": "bellman.factory.connection_maps",
    "transport_atoms": "bellman.factory.connection_maps",
    "pull_back": "bellman.factory.connection_maps",
    "diagram_trellis": "bellman.factory.trellis_drawings",
    "to_model_explorer": "bellman.factory.model_explorer",
    "perch_overlays": "bellman.factory.model_explorer",
    "layers_to_open": "bellman.factory.model_explorer",
    "node_place": "bellman.factory.model_explorer",
    "wire_counts": "bellman.factory.model_explorer",
    "BOUNDARY_IDS": "bellman.factory.model_explorer",
    "LAYER_ID_ENDING": "bellman.factory.model_explorer",
    "LAYER_COLORS": "bellman.factory.model_explorer",
    "NODE_STYLE": "bellman.factory.model_explorer",
    "OUTPUT_STYLE": "bellman.factory.model_explorer",
    "PERCH_COLORS": "bellman.factory.model_explorer",
    "explore": "bellman.factory.model_explorer",
    "write_model_explorer": "bellman.factory.model_explorer",
    "unpaired_joins": "bellman.factory.model_explorer",
    "UnpairedJoin": "bellman.factory.model_explorer",
    "UnpairedWire": "bellman.factory.model_explorer",
    "EntrySpan": "bellman.factory.file_entries",
    "entry_span": "bellman.factory.file_entries",
    "entry_value": "bellman.factory.file_entries",
    "replace_entry": "bellman.factory.file_entries",
    "append_to_mapping": "bellman.factory.file_entries",
    "append_to_sequence": "bellman.factory.file_entries",
    "insert_in_sequence": "bellman.factory.file_entries",
    "split_entry": "bellman.factory.file_entries",
    "remove_from_sequence": "bellman.factory.file_entries",
    "remove_from_mapping": "bellman.factory.file_entries",
    "written_at": "bellman.factory.file_entries",
    "written_spans": "bellman.factory.file_entries",
    "period_entries": "bellman.factory.file_entries",
    "ConnectorEntry": "bellman.factory.file_entries",
    "connector_entry": "bellman.factory.file_entries",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    """The public name `name`, read from the module that defines it, which is
    imported on this first use; every other name is refused with an
    AttributeError, so that a submodule is still imported as one."""
    try:
        module_name = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    return getattr(import_module(module_name), name)


def __dir__():
    return sorted(set(globals()) | set(__all__))
