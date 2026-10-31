"""The operations over a trellis dictionary, each a loop over its positions.

`specify_trellis` answers the trellis that `elaborate_trellis` and the three
trellis verbs make, and copies each stage occurrence once: it constructs each
distinct stage text once, places the stage at each of its positions without
a copy, binds each occurrence by the inner forms of the stage verbs
(`bellman.stage.binding_verbs`), which copy nothing, and `accrete` copies the
occurrence when it appends its period. `assemble_trellis` is
`specify_trellis` of the syntactic trellis `load_recipe` reads.
`respecify_trellis` answers what `specify_trellis` answers for a syntactic
trellis whose records changed, from the trellis specified before them: it
keeps each occurrence whose record is unchanged and constructs, binds and
copies the others alone.
`elaborate_trellis` constructs each distinct stage text once, places a full
copy of its stage at each of its positions and builds the result period by
period through `accrete`, which appends one period. The three trellis verbs
are `_bind` with one kind each; `_bind` copies each occurrence once, after
binding it.

The stages of one period share the parameters they declare under one name
(`bellman.factory.period_parameters`), and the connections between the
stage occurrences are selected once per reading
(`bellman.factory.connections`). The order of a reading,
written in `specify_trellis` and `respecify_trellis` and kept by
`elaborate_trellis` and `accrete`, is: place the occurrences
(`_placed`); reconcile the period parameters' declarations
(`shared_parameters`) and select the connections on the symbolic
occurrences, one `select_connections` over every period, which resolves
the authored endpoints, groups the candidates of inference, checks the
compatibility of each pair and selects the unique admissible ones,
certifies the complete routes and checks the cycles (`_check_periods`,
through `joins.checked_selection`), refusing an entry of no admitted shape
and retaining connection conflicts on the draft; reconcile the
values the records supply (`period_calibrations`); bind every occurrence's
calibration, then its methods, then its settings (`_bound_in_order`);
accrete (`_accreted`); and select again under the bound values
(`_rechecked`), the one reading at which a comparison reads a value, so
that a claim that depends on a value is made at the value bound and not
at a value requested. Nothing of the selection is written on the
dictionary: every public query selects again from the occurrences and
the entries it is given (`bellman.factory.joins`), and
`connections.connection_report` presents the selection of a trellis.
`AGENTS.md` lists the stage steps as elaborate, methodize, calibrate,
configure; the trellis verbs bind in the order calibrate, methodize,
configure (`_ORDER`, decision D36), and the stage verbs admit the
calibration before or after the methods, so the two orders agree on what
is bound and differ in the order of two steps the stage admits either
way; neither is reordered here.

One body binds one stage occurrence under one kind, `_bound_occurrence`, and
one loop applies it, `_bound_in_order`, every position under one kind before
the next, in the order calibrate, methodize, configure; `_bind` and
`specify_trellis` both bind through that loop. The body applies the stage
verb with the mapping the syntactic trellis holds at the position, the
calibration with the period's values for the shared parameters, once for
each distinct version and mapping, and places the result, with the
provenance of its own position, at the other positions of that version and
mapping; a changed method choice is the exception, which `_remethodized`
remakes at each position from its record. Before it applies the verb for a
new version and mapping, it gives a version it makes of that version the
answers an earlier one holding the very same records kept, so that the answers the graphs of one
construction determine are computed once and not once for each mapping.
`changed_positions` lists the positions a verb bound, a copy of a binding
among them, since it is a new version of its position. Neither dictionary
holds a graph; the joins of a period are read from its stages by
`bellman.factory.joins`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from copy import deepcopy
from typing import NamedTuple

from bellman.factory.elaboration import construct_stage, stage_occurrence, stage_text_of
from bellman.factory.joins import checked_selection
from bellman.factory.loading import KINDS, SOURCE_READERS, plain_python
from bellman.factory.period_parameters import period_calibrations, shared_parameters
from bellman.factory.recipe import load_recipe
from bellman.fold.block_lines import parameter_sets
from bellman.native.frozen import freeze
from bellman.native.hypergraphs import copy_native
from bellman.native.provenance import binding_provenance, grammar_versions, source_description
from bellman.native.versions import carry_answers, replace_stage, same_records
from bellman.refusals import FactoryError
from bellman.stage.binding_verbs import calibrated_version, configured_version, methodized_version
from bellman.stage.elaborated import ElaboratedStage
from bellman.stage.sources import load_calibration, load_methods, load_settings

__all__ = [
    "TrellisPosition",
    "accrete",
    "assemble_trellis",
    "calibrate_trellis",
    "changed_positions",
    "configure_trellis",
    "copy_trellis",
    "elaborate_trellis",
    "already_bound",
    "methodize_trellis",
    "positions",
    "respecify_trellis",
    "specify_trellis",
]


# --- the assembly and the elaboration of a trellis ---


def assemble_trellis(directory, recipe, /, **fills):
    """The specified trellis of a registry and a recipe,
    `specify_trellis(load_recipe(directory, recipe, **fills))`: the trellis
    the calls `load_recipe`, `elaborate_trellis`, `calibrate_trellis`,
    `methodize_trellis`, `configure_trellis` make, in that order, each stage
    occurrence copied once."""
    return specify_trellis(load_recipe(directory, recipe, **fills))


def specify_trellis(syntactic, previous=None, kinds=KINDS):
    """The specified trellis of a syntactic trellis: the trellis that
    `elaborate_trellis(syntactic, previous)` and the trellis verbs of `kinds`
    make, the verbs applied in the order calibrate, methodize, configure
    whatever order `kinds` writes, all three by default. Each stage
    occurrence is copied once, where that route copies it once for the
    elaboration and once for each verb. Each distinct stage text is
    constructed once, or taken from `previous` where the stage it holds at
    the position has the record's digest and origin, as `elaborate_trellis`
    takes it, and placed at each of its positions without a copy. The joins
    of each period are derived, and each inter-period mapping checked,
    before anything is bound, so that a trellis `elaborate_trellis` refuses
    is refused alike, the declarations of the parameters the stages of a
    period share among what is checked. The values the records supply for
    those parameters are then reconciled (`period_calibrations`), and each
    occurrence is bound by `_bound_in_order` with the record the syntactic
    trellis holds at its position, its calibration with the period's value
    for each shared parameter, every position under one kind before the
    next, so that a refusal is the one the verbs raise, naming the position
    and the kind. Each occurrence is copied when its period is appended
    (`_accreted`), the copy recording its position, and the connections are
    then selected again under the bound values (`_rechecked`). The order,
    place, reconcile, select, bind, accrete, recheck, is the module's."""
    order = _in_order(kinds)
    found = positions(syntactic)
    mappings = _inter_period_mappings(syntactic)
    inventory, texts = _sorted_positions(found, previous)
    by_period = _placed(inventory, _constructed(texts), grammar_versions() if texts else None)
    _check_periods(syntactic, by_period, mappings)
    calibrations = _period_calibrations(order, found, by_period, _trellis_file(syntactic))
    _bound_in_order(order, found, by_period, calibrations)
    specified = _accreted(syntactic, by_period, mappings)
    _rechecked(specified, _trellis_file(syntactic))
    # a trellis verb writes `periods` after the other keys of the trellis
    return {
        **{name: value for name, value in specified.items() if name != "periods"},
        "periods": specified["periods"],
    }


def respecify_trellis(specified, before, syntactic, kinds=KINDS):
    """The trellis `specify_trellis(syntactic, None, kinds)` answers, made
    from the trellis `specified` by binding again the positions whose
    record changed alone. `specified` is the trellis
    `specify_trellis(before, None, kinds)` answered for the syntactic
    trellis `before`, or that this function answered for it, with the same
    `kinds` (model interface specification 0.4, unit L, Task 20). A
    position whose record `syntactic` writes as `before` writes it, by the
    SHA-256 of each as `repr` writes it, keeps the stage occurrence
    `specified` holds there, the same object; every other position is
    constructed from its record, bound under `kinds` and copied as
    `specify_trellis` constructs, binds and copies it. A record holds the
    text of its stage, its three mappings and the digest of each file read
    for them, and the binding of a position reads nothing else but the
    values the other records of its period supply for the parameters its
    stage shares with theirs: a position whose record
    is unchanged but whose period now supplies another value for a
    parameter its stage declares is constructed, bound and copied anew as
    well, so that a kept occurrence is the one `specify_trellis` would bind
    there and a change of one stage's sources binds the occurrences of
    that stage and of the stages that share a changed parameter with it in
    the same period. A position whose record is a stage object is kept
    only where `before` holds the same object there. Every other entry of
    the result is copied from `syntactic`, as `specify_trellis` copies it.
    The
    connections of every period are selected, and each inter-period mapping
    checked, by `_check_periods`, which `specify_trellis` calls, before
    anything is bound, and again under the bound values after
    (`_rechecked`); a refusal is the one `specify_trellis` raises, since a
    kept position raised none when `specified` was made.
    Refused under `trellis-file-shape` where the two syntactic trellises
    differ in anything but their records, or `specified` holds other
    positions, and under `record-shape` where a kept occurrence holds the
    bindings of other kinds than `kinds`."""
    order = _in_order(kinds)
    found, earlier, held = positions(syntactic), positions(before), positions(specified)
    _check_same_frame(before, syntactic)
    if [(place.h, place.key) for place in held] != [(place.h, place.key) for place in found]:
        raise FactoryError(
            "the trellis given holds other positions than the syntactic trellis it was made from",
            rule="trellis-file-shape",
            address="periods",
            written=repr([(place.h, place.key) for place in held])[:80],
            write="the trellis specify_trellis answered for the first syntactic trellis",
        )
    kept = {(place.h, place.key): place.stage for place in held}
    renewed = [
        place for place, old in zip(found, earlier) if not _same_record(old.stage, place.stage)
    ]
    _check_kept_kinds(kept, found, renewed, order)
    mappings = _inter_period_mappings(syntactic)
    inventory, texts = _sorted_positions(renewed, None)
    version_record = grammar_versions() if texts else None
    constructed = _constructed(texts)
    placed = _placed(inventory, constructed, version_record)
    by_period = {}
    for place in found:
        stage = placed.get(place.h, {}).get(place.key, kept[place.h, place.key])
        by_period.setdefault(place.h, {})[place.key] = stage
    _check_periods(syntactic, by_period, mappings)
    calibrations = _period_calibrations(order, found, by_period, _trellis_file(syntactic))
    # a kept position whose period now supplies another calibration than
    # the occurrence holds, a shared parameter's value changed in another
    # stage's record, is constructed, bound and copied anew too, its text
    # constructed once where a renewed position constructed it already
    renewed_at = {(place.h, place.key) for place in renewed}
    changed = [
        place
        for place in found
        if (place.h, place.key) not in renewed_at
        and _calibration_changed(kept[place.h, place.key], calibrations.get((place.h, place.key)))
    ]
    if changed:
        more_inventory, more_texts = _sorted_positions(changed, None)
        missing = {key: module for key, module in more_texts.items() if key not in constructed}
        if missing and version_record is None:
            version_record = grammar_versions()
        constructed = {**constructed, **_constructed(missing)}
        for h, stages in _placed(more_inventory, constructed, version_record).items():
            by_period[h].update(stages)
        renewed_at |= {(place.h, place.key) for place in changed}
        renewed = [place for place in found if (place.h, place.key) in renewed_at]
    _bound_in_order(order, renewed, by_period, calibrations)
    bound = {(place.h, place.key) for place in renewed}
    periods = []
    for h, period in enumerate(syntactic["periods"]):
        # the entries in the order `accrete` writes them: the period's own,
        # `stages`, then `connectors` where the period writes none
        entry = {**_without(period, "stages"), "stages": None}
        entry = {**entry, "connectors": list(period.get("connectors") or [])}
        stages = by_period.get(h, {})
        periods.append(
            {
                name: (
                    {
                        key: _at_position(copy_native(stage), h, key)
                        if (h, key) in bound
                        else stage
                        for key, stage in stages.items()
                    }
                    if name == "stages"
                    else copy_trellis(value)
                )
                for name, value in entry.items()
            }
        )
    inter_connectors = [{} if mapping is None else deepcopy(dict(mapping)) for mapping in mappings]
    # the keys in the order `specify_trellis` writes them: the other keys of
    # the trellis, `inter_connectors`, then `periods`
    rest = _copy_without(syntactic, "periods", "inter_connectors")
    result = {**rest, "inter_connectors": inter_connectors, "periods": periods}
    _rechecked(result, _trellis_file(syntactic))
    return result


def _check_same_frame(before, syntactic):
    """Refuses under `trellis-file-shape` two syntactic trellises that differ
    in anything but the records at their positions: an entry of the trellis
    besides `periods`, or a period's own entries, the keys of its stages in
    their order among them, each compared as `repr` writes it. The refusal
    names the first entry that differs."""

    def frame(trellis):
        return {
            **_without(trellis, "periods"),
            **{
                f"periods[{h}]": {**_without(period, "stages"), "stages": list(period["stages"])}
                for h, period in enumerate(trellis["periods"])
            },
        }

    first, second = frame(before), frame(syntactic)
    differing = [
        name
        for name in dict.fromkeys([*first, *second])
        if repr(first.get(name)) != repr(second.get(name))
    ]
    if differing:
        raise FactoryError(
            f"the two syntactic trellises differ at {differing[0]}; only a record may differ",
            rule="trellis-file-shape",
            address=differing[0],
            written=repr(second.get(differing[0]))[:80],
            write="specify_trellis(syntactic) for a trellis whose periods or connectors changed",
        )


def _without(mapping, *names):
    """The entries of `mapping` but those under `names`, not copied."""
    return {name: value for name, value in mapping.items() if name not in names}


def _same_record(earlier, record):
    """Whether a position's record is unchanged: the very same stage object
    where either is one, and otherwise the same SHA-256 of the two records as
    `repr` writes them."""
    if isinstance(earlier, ElaboratedStage) or isinstance(record, ElaboratedStage):
        return earlier is record
    return _record_digest(earlier) == _record_digest(record)


def _record_digest(record):
    """The SHA-256 of a record as `repr` writes it, in UTF-8."""
    return hashlib.sha256(repr(record).encode("utf-8")).hexdigest()


def _check_kept_kinds(kept, found, renewed, order):
    """Refuses under `record-shape` a kept position whose record is a mapping
    and whose occurrence is no stage, or holds a binding of a kind not in
    `order`, or none of a kind in it, since `specify_trellis` binds such a
    position under the kinds of `order` alone."""
    renewed_at = {(place.h, place.key) for place in renewed}
    for place in found:
        if (place.h, place.key) in renewed_at or isinstance(place.stage, ElaboratedStage):
            continue
        stage = kept[place.h, place.key]
        held = (
            tuple(kind for kind in _ORDER if getattr(stage.bindings, kind) is not None)
            if isinstance(stage, ElaboratedStage)
            else None
        )
        if held != order:
            raise FactoryError(
                f"{place.address} of the trellis given is not bound under the kinds "
                f"{', '.join(order) or 'none'} alone",
                rule="record-shape",
                address=place.address,
                written=type(stage).__name__ if held is None else ", ".join(held),
                write="the trellis specify_trellis answered with the same kinds",
            )


def _at_position(stage, h, key):
    """`stage` with `position` in its provenance set to `{"h": h, "key":
    key}`, the place of the other entries kept, as `accrete` records the
    position of each stage occurrence it appends."""
    position = {"h": h, "key": key}
    return replace_stage(stage, provenance=freeze({**stage.provenance, "position": position}))


def elaborate_trellis(syntactic, previous=None):
    """The elaborated trellis, symbolic, of a syntactic trellis. Each distinct
    stage text is constructed once for each origin, and a full copy of its
    stage is placed at each of its positions, its position in its provenance,
    so that no two positions share an object. A position that already holds a
    stage is copied, the copy at its new position. With `previous`, a
    position whose record's digest and origin equal those of the stage
    `previous` holds at the same position is copied from it, so that a changed
    stage file alone is constructed again. Every other key of the argument is
    copied by `deepcopy`. The periods are checked as `specify_trellis`
    checks them (`_check_periods`): each period's shape, the declarations
    of the parameters its stages share, and the one selection of the
    connections over every period, which refuses an entry of no admitted
    shape and leaves semantic connection diagnostics on the draft; a
    refusal names the trellis file where the argument's provenance holds
    its path. The result is then built period by period (`_accreted`).
    Nothing is bound. The list `inter_connectors` holds one mapping per
    adjacent pair, as `read_trellis_file` writes it; another length is
    refused."""
    found = positions(syntactic)
    mappings = _inter_period_mappings(syntactic)
    inventory, texts = _sorted_positions(found, previous)
    version_record = grammar_versions() if texts else None
    by_period = _placed(inventory, _constructed(texts), version_record)
    _check_periods(syntactic, by_period, mappings)
    return _accreted(syntactic, by_period, mappings)


def _accreted(syntactic, by_period, mappings):
    """The trellis built period by period from the stage occurrences
    `by_period` holds, by period and key, with the mapping of `mappings`
    between each pair of adjacent periods and every other key of
    `syntactic` copied by `deepcopy`: each period's shape is checked
    (`_check_appended_period`) and the period appended (`_appended`), which
    copies each stage occurrence once. The connections were selected by
    `_check_periods` before, so no period is selected again here."""
    result = {
        **_copy_without(syntactic, "periods", "inter_connectors"),
        "periods": [],
        "inter_connectors": [],
    }
    for h, period in enumerate(syntactic["periods"]):
        built = {**_copy_without(period, "stages"), "stages": by_period.get(h, {})}
        mapping = None if h == 0 else mappings[h - 1]
        _check_appended_period(built, mapping, h)
        result = _appended(result, built, mapping)
    return result


def _check_periods(syntactic, by_period, mappings):
    """Refuses the periods of `syntactic`, with the stage occurrences
    `by_period` holds by period and key, before anything is bound: each
    period's shape and an inter-period mapping of `mappings` that is no
    mapping (`_check_appended_period`), the declarations of the parameters
    the stages of a period share (`shared_parameters`), and the one
    selection of the connections over every period on the symbolic
    occurrences (`joins.checked_selection`), which refuses an entry of no
    admitted shape and retains duplicate claims and cycles as diagnostics
    on the draft. A refusal names the trellis
    file where the provenance of `syntactic` holds its path.
    `elaborate_trellis`, `specify_trellis` and `respecify_trellis` check
    their periods here, so that the three refuse a trellis alike."""
    file = _trellis_file(syntactic)
    periods = []
    for h, period in enumerate(syntactic["periods"]):
        appended = {
            "stages": by_period.get(h, {}),
            "connectors": list(period.get("connectors") or []),
        }
        mapping = None if h == 0 else mappings[h - 1]
        _check_appended_period(appended, mapping, h)
        if _elaborated(appended):
            shared_parameters(appended["stages"], f"periods[{h}]", file)
        periods.append(appended)
    if all(_elaborated(period) for period in periods):
        checked_selection(periods, list(mappings), 0, file, rules=("connector-shape",))


def _rechecked(trellis, file):
    """The selection of the connections of `trellis` under the values its
    occurrences hold, refused as `_check_periods` refuses the symbolic
    selection: the recheck after the binding, at which a comparison reads a
    value, the one reading of the construction that does."""
    checked_selection(
        trellis["periods"], trellis["inter_connectors"], 0, file,
        rules=("connector-shape",),
    )


def _elaborated(period):
    """Whether every stage of a period is an `ElaboratedStage`, so that its
    fields are read; a period holding a record is checked when
    `elaborate_trellis` constructs it."""
    return all(isinstance(stage, ElaboratedStage) for stage in period["stages"].values())


def _trellis_file(syntactic):
    """The path of the trellis file the provenance of `syntactic` names, or
    None where it names none."""
    provenance = (
        syntactic.get("provenance") if isinstance(syntactic.get("provenance"), Mapping) else {}
    )
    return (
        provenance.get("trellis", {}).get("path")
        if isinstance(provenance.get("trellis"), Mapping)
        else None
    )


def _inter_period_mappings(syntactic):
    """The list `inter_connectors` of a syntactic trellis, which holds one
    mapping per adjacent pair of periods; another length is refused under
    `trellis-file-shape`."""
    mappings, pairs = syntactic["inter_connectors"], max(len(syntactic["periods"]) - 1, 0)
    if len(mappings) != pairs:
        raise FactoryError(
            f"{len(mappings)} inter-period mappings for {len(syntactic['periods'])} periods",
            rule="trellis-file-shape",
            address="inter_connectors",
            written=repr(mappings)[:60],
            write=f"{pairs} mappings, one for each adjacent pair",
        )
    return mappings


def _sorted_positions(found, previous):
    """The positions `found` sorted into three: a position holding a stage
    keeps it; a position whose record's text and origin are those of the
    stage `previous` holds there takes that stage; any other record's text is
    to be constructed. Answers `(h, key, address, stage or record, the key
    of its text or None)` for each position, and the texts to construct,
    each once, by `(digest, origin)`, with the addresses of the positions
    that hold it. A record `stage_text_of` refuses gains the note naming its
    position; two texts of one digest are refused under `record-shape`."""
    inventory, texts = [], {}
    for h, key, address, occurrence in found:
        if isinstance(occurrence, ElaboratedStage):
            inventory.append((h, key, address, occurrence, None))
            continue
        try:
            text, origin, digest, _ = stage_text_of(occurrence, address)
        except FactoryError as error:
            error.add_note(f"Stage occurrence: {address}")
            raise
        held = _unchanged_stage_at(previous, h, key, digest, origin)
        if held is not None:
            inventory.append((h, key, address, held, None))
            continue
        module = texts.setdefault(
            (digest, origin), {"text": text, "origin": origin, "occurrences": []}
        )
        if module["text"] != text:
            raise FactoryError(
                f"{address}: distinct module texts have the same SHA-256",
                rule="record-shape",
                address=address,
                written=digest,
                write="one text per digest",
            )
        module["occurrences"].append(address)
        inventory.append((h, key, address, occurrence, (digest, origin)))
    return inventory, texts


def _unchanged_stage_at(previous, h, key, digest, origin):
    """The stage `previous` holds at `(h, key)` where it holds one of the
    text `digest` at `origin`, else None."""
    if previous is None or h >= len(previous["periods"]):
        return None
    held = previous["periods"][h]["stages"].get(key)
    if (
        isinstance(held, ElaboratedStage)
        and held.provenance.get("sha256") == digest
        and held.provenance.get("origin") == origin
    ):
        return held
    return None


def _constructed(texts):
    """The stage each text of `texts` constructs, by `(digest, origin)`; a
    refusal gains the note naming the stage occurrences of the text."""
    constructed = {}
    for construction, module in texts.items():
        try:
            constructed[construction] = construct_stage(module["text"], module["origin"])
        except Exception as error:
            error.add_note("Affected stage occurrences: " + ", ".join(module["occurrences"]))
            raise
    return constructed


def _placed(inventory, constructed, version_record):
    """The stage at each position of `inventory`, by period and key: a stage
    kept or taken from the earlier trellis as it is, and for a record the
    version of its constructed stage whose provenance `stage_occurrence`
    writes, its position among it; a refusal gains the note naming the
    position."""
    by_period = {}
    for h, key, address, occurrence, construction in inventory:
        try:
            stage = (
                occurrence
                if construction is None
                else stage_occurrence(
                    occurrence,
                    constructed[construction],
                    address=address,
                    version_record=version_record,
                    position={"h": h, "key": key},
                )
            )
        except Exception as error:
            error.add_note(f"Stage occurrence: {address}")
            raise
        by_period.setdefault(h, {})[key] = stage
    return by_period


def _copy_without(mapping, *names):
    """A mapping of `deepcopy` copies of the entries of `mapping` but those
    under `names`."""
    return {name: deepcopy(value) for name, value in mapping.items() if name not in names}


# --- a period appended to a trellis ---


def accrete(trellis, period, inter_connector=None, *, file=None):
    """The trellis with `period` appended at the end of `periods`, the period
    earlier in time, and `inter_connector`, the mapping from its continuation
    fields to the arrival fields of the period appended before it, written at
    `inter_connectors[len(periods) - 2]`, the entry that joins the appended
    period to the one before it, `{}` when none is given. The terminal period,
    appended first, takes no mapping. The result is a new dictionary: the
    earlier periods' stage objects are the same objects under copied period
    dictionaries, and the appended period is copied, its stages by
    `copy_native`, so that no object of the caller's stands inside the
    trellis; a stage object placed by hand receives its new position on the
    copy. Where every stage of the appended period is an `ElaboratedStage`,
    the declarations of the parameters its stages share are reconciled and
    the connections of the period, and of the mapping given to the period
    before it, are selected (`_checked_joins`): an entry of no admitted
    shape is refused, naming `file`, the trellis file, when one is given.
    Duplicate claims, cycles and unresolved or ambiguous endpoints remain
    as diagnostics of the selection; order and transport operations check
    their own requirements. A period that holds records is checked when
    `elaborate_trellis` constructs it. No existing record is rewritten."""
    positions(trellis)
    n = len(trellis["periods"])
    _check_appended_period(period, inter_connector, n)
    result = _appended(trellis, period, inter_connector)
    _checked_joins(result, n, file)
    return result


def _appended(trellis, period, inter_connector):
    """`accrete`'s result before its checks: the trellis with `period`
    appended, copied, its stages by `copy_native` and each at its new
    position, and `inter_connector`, `{}` where none is given, written at
    the end of `inter_connectors` where the trellis holds a period
    already."""
    n = len(trellis["periods"])
    appended = copy_trellis({**period, "connectors": list(period.get("connectors") or [])})
    for key, stage in appended["stages"].items():
        if isinstance(stage, ElaboratedStage):
            appended["stages"][key] = _at_position(stage, n, key)
    # the earlier periods' dictionaries, their `stages` mappings and their
    # `connectors` lists are copied, so that a write into the result changes no
    # argument; the stage objects they hold are the same objects
    earlier = [
        {**held, "stages": dict(held["stages"]), "connectors": list(held["connectors"])}
        for held in trellis["periods"]
    ]
    result = {
        **trellis,
        "periods": [*earlier, appended],
        "inter_connectors": list(trellis["inter_connectors"]),
    }
    if trellis["periods"]:
        result["inter_connectors"].append(
            {} if inter_connector is None else deepcopy(dict(inter_connector))
        )
    return result


def _checked_joins(trellis, n, file):
    """Where every stage of `periods[n]` of `trellis`, the period appended
    last, is an `ElaboratedStage`: reconciles the declarations of the
    parameters its stages share, refusing two whose sets have no
    intersection the package reads (`shared_parameters`), and selects the
    connections of the period and, where every stage of `periods[n - 1]` is
    an `ElaboratedStage` too, of the mapping `inter_connectors[n - 1]`
    between the two (`joins.checked_selection`), refusing an entry of no
    admitted shape and retaining duplicate claims and cycles on the draft; a
    refusal names `file`, the trellis file, where it is given."""
    periods = trellis["periods"]
    appended = periods[n]
    if not _elaborated(appended):
        return
    shared_parameters(appended["stages"], f"periods[{n}]", file)
    if n > 0 and _elaborated(periods[n - 1]):
        checked_selection(
            [periods[n - 1], appended], [trellis["inter_connectors"][n - 1]], n - 1, file,
            rules=("connector-shape",),
        )
    else:
        checked_selection([appended], [], n, file, rules=("connector-shape",))


def _check_appended_period(period, inter_connector, n):
    """Refuses under `trellis-file-shape` a period to be appended at index
    `n` that is no mapping with `stages` or holds `connectors` that are no
    list, a mapping given with the terminal period, the first appended, and
    an inter-period connector that is no mapping."""
    if not isinstance(period, Mapping) or not isinstance(period.get("stages"), Mapping):
        raise FactoryError(
            "a period is a mapping with its stage occurrences "
            "under `stages` and a list `connectors`",
            rule="trellis-file-shape",
            address=f"periods[{n}]",
            written=repr(period)[:80],
            write='{"stages": {<key>: <record or stage>}, "connectors": []}',
        )
    if period.get("connectors") is not None and not isinstance(period["connectors"], list):
        raise FactoryError(
            f"periods[{n}].connectors is a {type(period['connectors']).__name__}, not a list",
            rule="trellis-file-shape",
            address=f"periods[{n}].connectors",
            written=repr(period["connectors"])[:80],
            write="connectors: []",
        )
    if n == 0 and inter_connector is not None:
        raise FactoryError(
            "the terminal period, the first appended, joins no later period; give no "
            "inter_connector with it",
            rule="trellis-file-shape",
            address="inter_connectors",
            written=repr(inter_connector),
            write="no inter_connector with the terminal period",
        )
    if inter_connector is not None and not isinstance(inter_connector, Mapping):
        raise FactoryError(
            "an inter-period connector is a mapping from continuation fields to arrival fields",
            rule="trellis-file-shape",
            address="inter_connectors",
            written=repr(inter_connector),
            write="{<continuation field>: <arrival field>}",
        )


# --- the three trellis verbs ---


def calibrate_trellis(elaborated, syntactic):
    """A new elaborated trellis, each stage occurrence calibrated with
    `syntactic["periods"][h]["stages"][key]["calibration"]`, the one value
    its period supplies standing for each parameter its stage shares with
    another stage of the period (`period_calibrations`), where that mapping
    differs, in the parameters the stage occurrence declares, from the
    calibration it holds, and copied otherwise."""
    return _bind(elaborated, syntactic, ("calibration",))


def methodize_trellis(elaborated, syntactic):
    """A new elaborated trellis, each stage occurrence methodized with the
    `methods` mapping at its key where it holds none; made anew from its record
    where it holds methods of another digest, since a version holds one
    methods binding; copied where the digests agree."""
    return _bind(elaborated, syntactic, ("methods",))


def configure_trellis(elaborated, syntactic):
    """A new elaborated trellis, each stage occurrence configured with the
    `settings` mapping at its key where it differs from the settings it holds,
    and copied otherwise; defined on methodized stage occurrences."""
    return _bind(elaborated, syntactic, ("settings",))


# the inner form of the stage verb that binds each kind of binding source,
# which copies nothing; its caller copies the version once
_VERBS = {
    "calibration": calibrated_version,
    "methods": methodized_version,
    "settings": configured_version,
}

# the kinds in the order the bindings are made, calibrate, methodize,
# configure (D36)
_ORDER = ("calibration", "methods", "settings")


def _in_order(kinds):
    """The kinds `kinds` names, in the order the bindings are made,
    calibration, methods, settings, whatever order `kinds` writes them in. A
    kind that is none of the three is refused with a ValueError, which names
    `kinds` as written, so that a string, read as its characters, is seen."""
    written, kinds = kinds, tuple(kinds)
    unknown = [kind for kind in kinds if kind not in _ORDER]
    if unknown:
        raise ValueError(
            f"a binding kind is one of {', '.join(_ORDER)}; {written!r} holds {unknown[0]!r}"
        )
    return tuple(kind for kind in _ORDER if kind in kinds)


def _bind(elaborated, syntactic, kinds=KINDS):
    """The trellis with the stage verbs of `kinds`, all three by default,
    applied at every position whose mapping in the syntactic trellis differs
    from what the stage occurrence holds, in the order calibrate, methodize,
    configure whatever order `kinds` writes, every position bound under one
    kind before the next (`_bound_in_order`); a position whose mapping is
    bound already, or where the syntactic trellis holds a stage object,
    which has no mapping to bind, keeps its version. Each position's version
    is then copied once, by `copy_native`, so that no two positions share an
    object. A refusal of a stage verb gains the notes naming the position and
    the kind. Where the calibration is bound, the connections are selected
    again under the bound values (`_rechecked`), as `specify_trellis`
    selects them after its binding."""
    order = _in_order(kinds)
    found = _stages_with_records(elaborated, syntactic)
    by_period = {}
    for h, key, _, stage, _ in found:
        by_period.setdefault(h, {})[key] = stage
    places = [(h, key, address, record) for h, key, address, _, record in found]
    calibrations = _period_calibrations(order, places, by_period, _trellis_file(syntactic))
    _bound_in_order(order, places, by_period, calibrations)
    bound = {
        **_copy_without(elaborated, "periods"),
        "periods": [
            {
                **_copy_without(period, "stages"),
                "stages": {key: copy_native(by_period[h][key]) for key in period["stages"]},
            }
            for h, period in enumerate(elaborated["periods"])
        ],
    }
    if "calibration" in order:
        _rechecked(bound, _trellis_file(syntactic))
    return bound


def _period_calibrations(order, found, by_period, file):
    """The calibration mapping to bind at each position of `found`, as
    `period_calibrations` answers it for the stage occurrences `by_period`
    holds, where `order` binds the calibration; nothing otherwise."""
    if "calibration" not in order:
        return {}
    return period_calibrations(
        [(h, key, address, record) for h, key, address, record in found], by_period, file
    )


def _calibration_changed(stage, mapping):
    """Whether `mapping`, the calibration a period supplies for a kept
    position, differs from the one its occurrence `stage` holds: a mapping
    that `already_bound` finds unbound; None, a stage object's position,
    differs from nothing."""
    return mapping is not None and not already_bound(stage, "calibration", mapping)


def _bound_in_order(order, found, by_period, calibrations):
    """`by_period`, the stage occurrences by period and key, with each kind of
    `order` bound in turn at every position of `found`, `(h, key, address,
    record)`, the record read from the syntactic trellis, the calibration
    with the mapping `calibrations` holds for the position, the record's
    own with the period's values for the parameters the stage shares
    (`period_calibrations`): the version `by_period` holds at a position is
    replaced by the one `_bound_occurrence` answers. Every position is bound
    under one kind before the next, so that a refusal is the one the trellis
    verbs, applied one after the other, raise. No version is copied; the
    caller copies each position once."""
    for kind in order:
        bound = {}
        for h, key, address, record in found:
            mapping = (
                calibrations[h, key]
                if kind == "calibration"
                else None
                if isinstance(record, ElaboratedStage)
                else record[kind]
            )
            by_period[h][key] = _bound_occurrence(
                kind, by_period[h][key], record, mapping, address, bound
            )
    return by_period


def _bound_occurrence(kind, stage, record, mapping, address, bound):
    """The version of `stage`, the stage occurrence at `address`, that binds
    `mapping`, the mapping of `kind` its record holds, before its copy:
    `stage` itself where `mapping` is None, as at a position whose `record`
    is a stage object, which has no mapping to bind, or where
    `stage` holds that binding already (`already_bound`); the version
    `_remethodized` binds, replacing the methods, where `stage` holds
    methods and is given others; and otherwise the version `_bound_once`
    binds, which carries, under `provenance["source_lists"]`, the record's
    list for the kind bound, the fill it holds marked bound, beside the
    elaboration's lists for the other kinds. `bound` holds the versions the
    stage verb of `kind` bound, by `_pair`. A refusal gains the note naming
    the position and the note naming the kind."""
    try:
        if mapping is None or already_bound(stage, kind, mapping):
            return stage
        if kind == "methods" and stage.bindings.methods is not None:
            return _remethodized(stage, record)
        return _with_source_list(_bound_once(kind, stage, mapping, bound), record, kind)
    except Exception as error:
        error.add_note(f"Stage occurrence: {address}")
        error.add_note(f"Binding kind: {kind}")
        raise


def _stages_with_records(elaborated, syntactic):
    """`(h, key, address, stage occurrence, record)` at every position of the
    first trellis, the record read from the second by `(h, key)`, since the
    order of the keys of a period carries no meaning: refused under
    `trellis-file-shape` where the two hold different positions, under
    `record-shape` where a position of the first holds a record, a position of
    the second holds neither a record nor a stage, a record's mapping of one
    kind is no mapping, or a record's text differs from the held version's,
    which `elaborate_trellis(syntactic, elaborated)` constructs again."""
    left, right = positions(elaborated), positions(syntactic)
    held = {(position.h, position.key) for position in left}
    given = {(position.h, position.key) for position in right}
    if held != given:
        raise FactoryError(
            "the elaborated trellis and the syntactic trellis given as the second argument hold "
            "different positions",
            rule="trellis-file-shape",
            address="periods",
            written=f"{sorted(held)!r} against {sorted(given)!r}",
            write="the syntactic trellis the elaborated one "
            "was made from, or one of the same periods and keys",
        )
    records = {(position.h, position.key): position.stage for position in right}
    for h, key, address, occurrence in left:
        record = records[h, key]
        if not isinstance(occurrence, ElaboratedStage):
            raise FactoryError(
                f"{address} of the first argument is a record, not an elaborated stage",
                rule="record-shape",
                address=address,
                written=type(occurrence).__name__,
                write="elaborate_trellis(syntactic) before the verbs",
            )
        if isinstance(record, ElaboratedStage):
            continue
        if not isinstance(record, Mapping) or any(kind not in record for kind in KINDS):
            raise FactoryError(
                f"{address} of the second argument holds no record; a verb reads its mapping from "
                "the syntactic trellis",
                rule="record-shape",
                address=address,
                written=type(record).__name__,
                write="the syntactic trellis, whose record at each key holds the three mappings",
            )
        for kind_name in KINDS:
            if not isinstance(record[kind_name], Mapping):
                raise FactoryError(
                    f"{address}.{kind_name} of the second argument is a "
                    f"{type(record[kind_name]).__name__}, not a mapping",
                    rule="record-shape",
                    address=f"{address}.{kind_name}",
                    written=repr(record[kind_name])[:80],
                    write=f"{kind_name}: {{...}}",
                )
        digest = stage_text_of(record, address).digest
        if digest != occurrence.provenance.get("sha256"):
            raise FactoryError(
                f"{address} of the second argument holds another text than the version the first "
                "holds; a changed stage file is constructed again before it is bound",
                rule="record-shape",
                address=address,
                written=digest,
                write="elaborate_trellis(syntactic, elaborated) before the verbs",
            )
    return [(h, key, address, occurrence, records[h, key]) for h, key, address, occurrence in left]


def already_bound(stage, kind, mapping):
    """Whether `stage` already holds the binding of `kind` that `mapping`
    would make: its calibration by numeric equality
    at each parameter the stage declares (0 and 0.0 equal, and the tuple a
    stage holds for a list-valued parameter equal to the list of the same
    entries), its settings by the equality of the loaded mapping, a numpy
    scalar converted first, its methods by the digest of the normalized
    mapping against the digest its provenance records under `sources`."""
    held = getattr(stage.bindings, kind)
    if held is None:
        return False
    if kind == "calibration":
        values = plain_python(load_calibration(mapping))
        given = {name: values[name] for name in parameter_sets(stage) if name in values}
        return set(held) == set(given) and all(
            bool(plain_python(held[name]) == given[name]) for name in given
        )
    if kind == "settings":
        return plain_python(held) == plain_python(load_settings(mapping))
    recorded = stage.provenance["sources"].get("methods")
    return (
        recorded is not None
        and recorded["sha256"] == source_description(load_methods(mapping))["sha256"]
    )


def _remethodized(stage, record):
    """The occurrence `stage` given the changed method choice its record
    holds: a version holding the occurrence's records, whose methods, and the
    blocks they opened, the record's methods replace as a whole
    (`methodized_version` with `replace_all`), and whose settings, where it
    holds any, are bound again for the new methods, each by the inner form of
    its stage verb on that version. The occurrence itself is left as it was,
    and the caller copies each position once, after every kind is bound."""
    version = methodized_version(replace_stage(stage), record["methods"], replace_all=True)
    if stage.bindings.settings is not None:
        version = configured_version(version, dict(stage.bindings.settings))
    return version


def _bound_once(kind, stage, mapping, bound):
    """The version the stage verb of `kind` binds of `stage` with `mapping`,
    before its copy, the verb's inner form applied once for each key of
    `_pair`: at the first position of a key the inner form's version, kept in
    `bound`; at each later position that version with the provenance
    `binding_provenance` records for `stage`. Before the inner form is
    applied at the first position of a key, a version this call makes of
    `stage` (`replace_stage`) is given the answers kept by a version in
    `bound` that holds the very same records (`versions.carry_answers`), and
    the inner form is applied to that version: the occurrences of one stage
    text hold its construction's records, so the answers its graphs
    determine are computed once for the text and not once for each key.
    `stage` itself keeps its own answers. The caller copies the version
    once."""
    loaded = SOURCE_READERS[kind](mapping)
    pair = _pair(stage, loaded)
    if pair in bound:
        first = bound[pair]
        return replace_stage(
            first,
            provenance=binding_provenance(stage, first.provenance["operation"], mapping, loaded),
        )
    earlier = next((version for version in bound.values() if same_records(version, stage)), None)
    # the inner form binds in place a version this call makes, which holds
    # the records of `stage`, since `stage` can be an object of the caller's
    # (specification 0.6 §4.1)
    stage = replace_stage(stage)
    if earlier is not None:
        carry_answers(earlier, stage)
    bound[pair] = _VERBS[kind](stage, mapping)
    return bound[pair]


def _pair(stage, loaded):
    """The key of a version and the loaded mapping a verb binds to it, under
    which `_bound_once` applies the verb once: the version's text by its
    digest and origin, the package and grammar that constructed it and the
    sources of its three mappings, as its provenance records them; and its
    three bindings and the loaded mapping as `repr` writes them, which keeps
    the order of each mapping's keys and the type of each value. A `Method`
    record of the methods binding is written as its box, method, handler and
    settings, since the record's own `repr` sorts its settings and so would
    give one key to two versions whose methods differ only in the order of a
    method's settings. Two versions of one key hold the same graphs and
    bindings written alike, so the verb makes of both the same version,
    written alike, apart from its provenance; a version prints each binding,
    a method's settings included, in the order its keys are written."""
    recorded = {
        name: stage.provenance.get(name) for name in ("sha256", "origin", "versions", "sources")
    }
    written = [_written_binding(kind, getattr(stage.bindings, kind)) for kind in KINDS] + [
        plain_python(loaded)
    ]
    return source_description(recorded)["sha256"], repr(written)


def _written_binding(kind, binding):
    """The binding of `kind` as `plain_python` writes it; a methods binding as
    a list holding, for each entry in its order, the box, the method, the
    handler and the settings, the settings in the order they are written."""
    if kind != "methods" or binding is None:
        return plain_python(binding)
    return [
        (box, entry.tag, entry.handler, plain_python(entry.settings))
        for box, entry in binding.items()
    ]


def _with_source_list(version, record, kind):
    """`version` with the record's source list of `kind` under
    `provenance["source_lists"]`, beside the lists it holds, where the record
    holds one."""
    lists = record.get("provenance", {}).get("source_lists", {})
    if kind not in lists:
        return version
    return replace_stage(
        version,
        provenance=freeze(
            {
                **version.provenance,
                "source_lists": {**version.provenance.get("source_lists", {}), kind: lists[kind]},
            }
        ),
    )


# --- the positions of a trellis, and its copy ---


def changed_positions(before, after):
    """The positions `(h, key)` whose stage occurrence in `after` is a new
    version of the one in `before`, or stands at a position `before` lacks.
    A verb writes the earlier version into the new
    one's provenance as its parent, a copy of a binding included, and a copy
    of an unchanged stage occurrence keeps its provenance equal, so the two
    provenances are compared."""
    earlier = {(position.h, position.key): position.stage for position in positions(before)}
    return [
        (position.h, position.key)
        for position in positions(after)
        if (position.h, position.key) not in earlier
        or not isinstance(earlier[position.h, position.key], ElaboratedStage)
        or earlier[position.h, position.key].provenance != position.stage.provenance
    ]


class TrellisPosition(NamedTuple):
    """One position of a trellis: the period's index `h`, the stage's key, the
    address of the position, `periods[h].stages['<key>']`, and what the
    position holds, a source record in a syntactic trellis and a stage
    occurrence in an elaborated one."""

    h: int
    key: str
    address: str
    stage: object


def positions(trellis):
    """The `TrellisPosition` of every position of a trellis, in order. The
    shape is refused under `trellis-file-shape`: a list `periods` and a list
    `inter_connectors`, a list `solutions` where present, each period a
    mapping with `stages` and a list `connectors`, each key a nonempty
    string."""
    for name in ("periods", "inter_connectors"):
        if not isinstance(trellis, Mapping) or not isinstance(trellis.get(name), list):
            raise FactoryError(
                f"the trellis has no list {name!r}",
                rule="trellis-file-shape",
                address=name,
                written=type(trellis).__name__,
                write='{"periods": [...], "inter_connectors": [...]}',
            )
    if "solutions" in trellis and not isinstance(trellis["solutions"], list):
        raise FactoryError(
            "solutions must be a list when present",
            rule="trellis-file-shape",
            address="solutions",
            written=type(trellis["solutions"]).__name__,
            write="solutions: []",
        )
    found = []
    for h, period in enumerate(trellis["periods"]):
        where = f"periods[{h}]"
        if not isinstance(period, Mapping) or not isinstance(period.get("stages"), Mapping):
            raise FactoryError(
                f"{where}.stages must be a mapping",
                rule="trellis-file-shape",
                address=where,
                written=repr(period)[:80],
                write='{"stages": {...}, "connectors": []}',
            )
        if not isinstance(period.get("connectors"), list):
            raise FactoryError(
                f"{where}.connectors must be a list",
                rule="trellis-file-shape",
                address=f"{where}.connectors",
                written=repr(period.get("connectors"))[:80],
                write="connectors: []",
            )
        for key, occurrence in period["stages"].items():
            if not isinstance(key, str) or not key:
                raise FactoryError(
                    f"{where}.stages requires nonempty string keys",
                    rule="trellis-file-shape",
                    address=where,
                    written=repr(key),
                    write="a stage key such as 'cons'",
                )
            found.append(
                TrellisPosition(h=h, key=key, address=f"{where}.stages[{key!r}]", stage=occurrence)
            )
    return found


def copy_trellis(value):
    """A copy of a trellis dictionary or of a part of one: every container
    copied and every stage occurrence a full copy by `copy_native`, so that
    no two positions share an object."""
    if isinstance(value, ElaboratedStage):
        return copy_native(value)
    if isinstance(value, Mapping):
        return {key: copy_trellis(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(copy_trellis(item) for item in value)
    return deepcopy(value)
