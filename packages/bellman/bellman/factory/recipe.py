"""`load_recipe`: the syntactic trellis a registry directory and its recipe
define.

A recipe names every file it reads by its path from the recipe's own folder,
the registry directory: the trellis file under `trellis:`, each stage's file
under the key `stage` of the stage's entry, and each source in a source list;
nothing is read in place of a path the recipe does not write. `load_recipe`
reads the recipe, the trellis file and its period templates, checks that the
recipe and the templates name the same stages, reads each stage file and each
source once, binds each fill to its slot, merges each source list and writes
one record per stage and period. A source file is told apart by its top key,
and its `parent:` chain is merged beneath it. A slot is written `$<name>` in
a source list. The `registry` block admits names no stage declares. A fill is
read against the declarations of the stages that receive it. Every refusal
names a rule of `FACTORY_RULES` and says where, what is written, why, and what
to write instead.
"""

from __future__ import annotations

import copy
import dataclasses
import re
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import NamedTuple

from bellman.factory.loading import (
    KINDS,
    METADATA,
    _mapping_and_digest,
    load_stage,
    plain_python,
    read_trellis_file,
)
from bellman.refusals import FactoryError
from bellman.stage.construction import stage_name
from bellman.stage.sources import entry_key, load_methods, read_yaml_mapping
from bellman.syntax.lower import item_addresses, parse_with_spans
from bellman.typing.declarations import Declarations

__all__ = ["load_recipe"]


def load_recipe(directory, recipe, texts=None, /, **fills):
    """The syntactic trellis a registry directory and a recipe define: the
    recipe, the trellis file and the stage files at the paths the recipe
    writes, the period templates the trellis file names and every source
    file the recipe names are read once; each `{template, repeat}` entry is
    expanded and a single inter-period mapping repeated for each adjacent
    pair; each fill stands in its slot; each source list is merged; one record
    is written per stage and period, holding the stage's text and digest, its
    three merged mappings and the ordered sources that produced them. A stage
    restricted by `periods: [lo, hi]` is absent from the other periods.
    Nothing is elaborated. `texts`, positional so that no slot can name it,
    maps a file's resolved path to the text read in its place, for the
    recipe, the trellis file and the period files alone, whose paths taken
    stand sorted under the provenance's `texts` (model interface spec 0.4
    §3.1)."""
    directory = Path(directory)
    read = _read_recipe(
        _registry_file(
            str(recipe), directory=directory, file=str(directory / str(recipe)), address="recipe"
        ),
        texts,
    )
    file = read["path"]
    unknown = sorted(slot for slot in fills if slot not in read["slots"])
    if unknown:
        declared = ", ".join("$" + slot for slot in sorted(read["slots"]))
        raise FactoryError(
            f"the keyword {unknown[0]!r} names no slot of the recipe; its slots are {declared}",
            rule="recipe-slot-unknown",
            file=file,
            address=unknown[0],
            written=unknown[0],
            write=f"one of {declared}, or a new `$` name in a source list of the recipe",
        )
    trellis = read_trellis_file(
        _registry_file(read["trellis"], directory=directory, file=file, address="trellis"),
        texts,
    )
    templates = [
        {
            "stages": template_keys(
                period["stages"], file=trellis["path"], address=f"periods[{number}]"
            ),
            "connectors": period["connectors"],
            "template": period.get("template"),
        }
        for number, period in enumerate(trellis["periods"])
    ]
    _check_recipe_template_agreement(read, templates, trellis["path"])
    stages = {
        key: stage_record(key, entry, directory=directory, file=file)
        for key, entry in read["stages"].items()
    }
    cache = {}
    registry, registry_lists = _registry_assignments(
        read, directory=directory, file=file, cache=cache
    )
    # the declarations a fill is read against parse every stage text, so they
    # are read when a fill is given
    if fills:
        declared = {
            key: declared_parameters(stages[key]["stage"]["text"], stages[key]["stage"]["origin"])
            for key in stages
        }
        settings = {
            key: _setting_names(read, key, directory=directory, file=file, cache=cache)
            for key in stages
        }
    else:
        declared = settings = {}
    slot_parts = _fill_parts(
        read, fills, declared=declared, settings=settings, registry=registry, file=file
    )
    for slot in fills:
        for kind, named in slot_parts[slot].registry.items():
            registry[kind] = _merge_sources([registry.get(kind, {}), named])
            registry_lists.setdefault(kind, []).append(
                {"slot": slot, "bound": True, "names": sorted(named)}
            )
    periods = _syntactic_periods(
        read,
        templates,
        stages=stages,
        slot_parts=slot_parts,
        directory=directory,
        file=file,
        cache=cache,
    )
    provenance = {
        "recipe": {"path": file, "sha256": read["sha256"]},
        "trellis": {"path": trellis["path"], "sha256": trellis["sha256"]},
        "registry": registry_lists,
    }
    # the resolved paths of the texts read in their files' places
    taken = set(trellis.get("texts", []))
    if read["taken"] is not None:
        taken.add(read["taken"])
    if taken:
        provenance["texts"] = sorted(taken)
    return {
        "periods": periods,
        "inter_connectors": trellis["inter_connectors"],
        "registry": registry,
        "provenance": provenance,
    }


# --- the recipe ---

# the keys a stage's block of the recipe may hold
_BLOCK_KEYS = ("stage",) + KINDS + ("periods",)


def _read_recipe(path, texts=None):
    """The recipe file as a dictionary: `stages`, each `{"stage": path, kind:
    {"all": [...], "lo-hi": [...]}, "periods": (lo, hi) or None}`, the path
    of the stage file as the entry writes it; the `slots` named; the
    `registry` block `{kind: [names]}`; the path of the `trellis` file as the
    recipe writes it; the file's `path` and `sha256`. A recipe that names no
    trellis file and an entry that names no stage file are refused under
    `recipe-shape`; a key written twice is refused by the reader. `texts`
    maps a file's resolved path to the text read in its place: the digest is
    that of the text read, and `taken` the recipe's resolved path where its
    text was taken, else None (model interface spec 0.4 §3.1)."""
    path = Path(path)
    raw, digest, taken = _mapping_and_digest(path, texts, rule="recipe-shape", address="recipe")
    file = str(path)
    if not isinstance(raw.get("stages"), Mapping):
        raise FactoryError(
            "the recipe has no top-level `stages` mapping",
            rule="recipe-shape",
            file=file,
            address="stages",
            written=repr(raw)[:80],
            write="stages: {<stage key>: {stage: <path>.bl, calibration: {all: [...]}, "
            "settings: {all: [...]}, methods: {all: [...]}}}",
        )
    if not _is_path(raw.get("trellis")):
        raise FactoryError(
            "the recipe names no trellis file",
            rule="recipe-shape",
            file=file,
            address="trellis",
            written=repr(raw)[:80],
            write="`trellis: trellis.yml`, the path from this folder",
        )
    stages, slots = {}, set()
    for stage, block in raw["stages"].items():
        if not isinstance(block, Mapping):
            raise FactoryError(
                f"stage {stage!r} is no mapping of its stage file and its calibration, settings "
                "and methods lists",
                rule="recipe-shape",
                file=file,
                address=f"stages.{stage}",
                written=repr(block)[:80],
                write="stage: <path>.bl, calibration: {all: [...]}, settings: {all: [...]}, "
                "methods: {all: [...]}",
            )
        unknown = sorted(str(key) for key in block if key not in _BLOCK_KEYS)
        if unknown:
            raise FactoryError(
                f"stage {stage!r} has the key {unknown[0]!r}, which is none of stage, "
                "calibration, settings, methods and periods",
                rule="recipe-shape",
                file=file,
                address=f"stages.{stage}.{unknown[0]}",
                written=unknown[0],
                write="stage:, calibration:, settings:, methods: "
                "and periods: as the keys of a stage's block",
            )
        if not _is_path(block.get("stage")):
            raise FactoryError(
                f"the entry `stages.{stage}` names no stage file",
                rule="recipe-shape",
                file=file,
                address=f"stages.{stage}",
                written=repr(block)[:80],
                write=f"`stage: stages/{stage}/{stage}.bl`, the path from this folder",
            )
        periods = None
        if "periods" in block:
            written = block["periods"]
            if (
                not isinstance(written, list)
                or len(written) != 2
                or any(isinstance(bound, bool) or not isinstance(bound, int) for bound in written)
                or written[0] > written[1]
            ):
                raise FactoryError(
                    f"periods of stage {stage!r} is not [lo, hi] with two integers, lo ≤ hi",
                    rule="recipe-shape",
                    file=file,
                    address=f"stages.{stage}.periods",
                    written=repr(written),
                    write="periods: [lo, hi] with lo ≤ hi, both integers",
                )
            periods = (written[0], written[1])
        entry = {"stage": block["stage"], "periods": periods}
        for kind in KINDS:
            entry[kind], named = _source_lists(block.get(kind), stage, kind, file=file)
            slots |= named
        stages[str(stage)] = entry
    registry = raw.get("registry") or {}
    if not isinstance(registry, Mapping) or any(
        kind not in KINDS or not isinstance(names, list) for kind, names in registry.items()
    ):
        raise FactoryError(
            "the registry block is not `{kind: [source names]}`",
            rule="recipe-shape",
            file=file,
            address="registry",
            written=repr(registry)[:80],
            write="registry: {calibration: [calibration/wage_schedule]}",
        )
    return {
        "path": file,
        "sha256": digest,
        "taken": taken,
        "trellis": raw["trellis"],
        "stages": stages,
        "slots": frozenset(slots),
        "registry": {kind: [str(name) for name in names] for kind, names in registry.items()},
    }


def _is_path(value):
    """Whether a recipe writes `value` as a path: a string that is not
    empty."""
    return isinstance(value, str) and bool(value.strip())


def _source_lists(block, stage, kind, *, file):
    """`{"all": [names], "lo-hi": [names]}` of one kind block of one stage and
    the slots it names; a missing block is an empty `all` list; the ranges
    are checked for their form and for overlap, the source names for their
    form."""
    address = f"stages.{stage}.{kind}"
    if block is None:
        return {"all": []}, set()
    if not isinstance(block, Mapping) or "all" not in block:
        raise FactoryError(
            f"the {kind} block of stage {stage!r} is no mapping with an `all` list",
            rule="recipe-shape",
            file=file,
            address=address,
            written=repr(block)[:80],
            write=f"{kind}: {{all: [<source>, $<slot>]}}",
        )
    lists, slots, ranges = {}, set(), []
    for key, names in block.items():
        names = [] if names is None else (list(names) if isinstance(names, list) else [names])
        sources = []
        for name in names:
            name = str(name).strip()
            if name.startswith("$"):
                slots.add(name[1:])
            elif ".." in name or Path(name).is_absolute():
                raise FactoryError(
                    f"the source name {name!r} in {address}.{key} is absolute or contains '..'",
                    rule="recipe-source",
                    file=file,
                    address=f"{address}.{key}",
                    written=name,
                    write="a path relative to the registry directory, such as calibration/main",
                )
            sources.append(name)
        if key != "all":
            ranges.append(_range(key, file=file, address=f"{address}.{key}"))
        lists[str(key)] = sources
    ordered = sorted(ranges)
    for (a_lo, a_hi), (b_lo, b_hi) in zip(ordered, ordered[1:]):
        if a_hi >= b_lo:
            raise FactoryError(
                f"the period ranges {a_lo}-{a_hi} and {b_lo}-{b_hi} of {address} overlap",
                rule="recipe-shape",
                file=file,
                address=address,
                written=f"{a_lo}-{a_hi}, {b_lo}-{b_hi}",
                write="ranges that share no period",
            )
    return lists, slots


_RANGE = re.compile(r"^(\d+)-(\d+)$")


def _range(key, *, file, address):
    """`(lo, hi)` of a range key written `lo-hi`, the periods counted from
    the terminal period, `0-0`."""
    found = _RANGE.match(str(key))
    if not found:
        raise FactoryError(
            f"the period range key {key!r} is not written lo-hi",
            rule="recipe-shape",
            file=file,
            address=address,
            written=str(key),
            write="a key such as '0-0' or '45-59', the terminal period being 0",
        )
    lo, hi = int(found.group(1)), int(found.group(2))
    if lo > hi:
        raise FactoryError(
            f"the period range {key!r} has lo {lo} above hi {hi}",
            rule="recipe-shape",
            file=file,
            address=address,
            written=str(key),
            write=f"'{hi}-{lo}'",
        )
    return lo, hi


# --- the period templates, the stage files and the registry block ---


def template_keys(stages, *, file, address):
    """The stage keys a period template names: a list of keys, or of one-key
    mappings as the period files write them; a key listed twice is refused
    under `recipe-shape`, and a mapping of records, the form `load_trellis`
    reads, under `trellis-file-shape`, since the recipe supplies the
    mappings."""
    if isinstance(stages, Mapping):
        raise FactoryError(
            f"{address}.stages is a mapping of records; under a recipe a period template lists "
            "its stage keys, and the recipe supplies their mappings",
            rule="trellis-file-shape",
            file=file,
            address=address,
            written=repr(stages)[:60],
            write="stages: [<keys>]",
        )
    if not isinstance(stages, list):
        raise FactoryError(
            f"{address}.stages is no list of keys",
            rule="trellis-file-shape",
            file=file,
            address=address,
            written=repr(stages)[:60],
            write="stages: [<keys>]",
        )
    keys = [
        key
        for item in stages
        for key in (list(item) if isinstance(item, Mapping) else [str(item)])
    ]
    twice = next((key for number, key in enumerate(keys) if key in keys[:number]), None)
    if twice is not None:
        raise FactoryError(
            f"the stage key {twice!r} is listed twice in {address}",
            rule="recipe-shape",
            file=file,
            address=f"{address}.stages",
            written=twice,
            write="each stage key once in the template",
        )
    return keys


def _check_recipe_template_agreement(read, templates, trellis_path):
    """Refuses, under `recipe-template-agreement`, a stage the recipe names
    that no period template holds or that is active at no period held, and a
    stage a template holds that the recipe does not name; the refusal names
    the stage, the recipe, the trellis file and the period file the period
    came from."""
    file = read["path"]
    for stage, entry in read["stages"].items():
        held = [h for h, template in enumerate(templates) if stage in template["stages"]]
        if not held:
            raise FactoryError(
                f"the recipe names the stage {stage!r}, which no period of {trellis_path} holds",
                rule="recipe-template-agreement",
                file=file,
                address=stage,
                written=stage,
                write=f"{stage!r} in a period template of "
                f"{trellis_path}, or no entry for it in the recipe",
            )
        if not any(_is_active(entry["periods"], h) for h in held):
            lo, hi = entry["periods"]
            raise FactoryError(
                f"the stage {stage!r} is restricted to periods {lo}-{hi} and {trellis_path} holds "
                f"it at {', '.join(map(str, held))} of its "
                f"{len(templates)} periods, so it is active at no period",
                rule="recipe-template-agreement",
                file=file,
                address=stage,
                written=f"periods: [{lo}, {hi}]",
                write=f"periods: [lo, hi] with lo ≤ {max(held)} and hi ≥ {min(held)}",
            )
    for h, template in enumerate(templates):
        where = (
            f"periods[{h}] of {template['template']}, named by {trellis_path}"
            if template.get("template")
            else f"periods[{h}] of {trellis_path}"
        )
        for key in template["stages"]:
            if key not in read["stages"]:
                raise FactoryError(
                    f"{where}, holds the stage {key!r}, which the recipe {file} does not name",
                    rule="recipe-template-agreement",
                    file=file,
                    address=f"periods[{h}].{key}",
                    written=key,
                    write=f"an entry {key}: {{stage: <path>.bl, calibration: {{all: [...]}}, "
                    f"...}} in the recipe, or the key removed from the template",
                )


def _is_active(periods, h):
    """Whether a stage whose recipe entry restricts it to `periods`, `(lo, hi)`
    or None, occupies period `h`."""
    return periods is None or periods[0] <= h <= periods[1]


def stage_record(key, entry, *, directory, file):
    """The source record of the stage file that the entry `entry` of the
    stage `key` names under `stage`, a path relative to the registry
    directory `directory`; a path that names no file, or no `.bl` file, is
    refused as `load_stage` refuses it, at the address of the path in the
    recipe `file`."""
    written = entry["stage"]
    try:
        return load_stage(str(Path(directory) / written))
    except FactoryError as refusal:
        raise FactoryError(
            refusal.message,
            rule=refusal.rule,
            file=file,
            address=f"stages.{key}.stage",
            written=written,
            write=refusal.write,
        ) from None


def _registry_assignments(read, *, directory, file, cache):
    """The registry-level names the recipe's `registry` block assigns, `{kind:
    {name: value}}`, and their ordered sources `{kind: [entry, ...]}`: names no
    stage declares, carried as data, bound to no stage."""
    registry, lists = {}, {}
    for kind, names in read["registry"].items():
        chain, entries = [], []
        for name in names:
            values, entry = _read_source(
                name, kind, directory=directory, file=file, address=f"registry.{kind}", cache=cache
            )
            chain.append(values)
            entries.append(entry)
        registry[kind], lists[kind] = _merge_sources(chain), entries
    return registry, lists


# --- the fills ---


def declared_parameters(text, origin):
    """The parameters a stage text declares, as the declaration pass
    classifies them and `stage.par` prints them: the top-level
    declarations that are neither fields a header lists nor shocks (the rule
    `parameter-or-field`), read by the pass's own reading of the parsed term;
    the stage is not constructed. A text the parser or the reading refuses
    raises that refusal."""
    term, spans = parse_with_spans(text, filename=origin)
    items = item_addresses(term)
    declarations = Declarations(stage_name(term, items, spans), items, spans)
    declarations.read(term)
    return tuple(declarations.parameters())


def _setting_names(read, key, *, directory, file, cache):
    """The setting names a stage may be given in a fill: the keys of the
    settings files its settings lists name, and the names the entries of its
    methods files reference under `settings`, since a stage file declares no
    setting."""
    names = set()
    for listed in read["stages"][key]["settings"].values():
        for name in listed:
            if not name.startswith("$"):
                names |= set(
                    _read_source(
                        name,
                        "settings",
                        directory=directory,
                        file=file,
                        address=f"stages.{key}.settings",
                        cache=cache,
                    ).assignments
                )
    for listed in read["stages"][key]["methods"].values():
        for name in listed:
            if not name.startswith("$"):
                mapping = _read_source(
                    name,
                    "methods",
                    directory=directory,
                    file=file,
                    address=f"stages.{key}.methods",
                    cache=cache,
                ).assignments
                for entry in mapping.get("methods", []):
                    names |= set(_strings_in(entry.get("settings", {})))
    return names


def _strings_in(value):
    """Every string among the values of a nested mapping or sequence."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _strings_in(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings_in(item)


@dataclasses.dataclass(frozen=True, kw_only=True)
class SlotFill:
    """What the fill of one slot contributes, as `_fill_parts` describes each
    field: `parts`, `registry`, `names` and `entry`."""

    parts: dict
    registry: dict
    names: dict
    entry: dict


def _fill_parts(read, fills, *, declared, settings, registry, file):
    """What each fill contributes, a `SlotFill` for each slot of the recipe:
    `parts`, `{kind: mapping or None}`, the keys the lists of the receiving
    stages take in that kind; `registry`, `{kind: mapping}`, the keys only
    the `registry` block admits, which no stage's mapping holds; `names`,
    `{kind: {stage: [name, ...]}}`, the names of the fill each receiving
    stage takes; and `entry`, the provenance entry `{"slot", "bound"}`, which
    `_merged_source_list` completes with the names. A slot no keyword binds
    contributes nothing. A numpy scalar among the values is read as the
    number it holds. `declared` and `settings` are read for a bound slot
    only."""
    slot_parts = {}
    for slot in read["slots"]:
        if slot not in fills:
            slot_parts[slot] = SlotFill(
                parts={kind: None for kind in KINDS},
                registry={},
                names={},
                entry={"slot": slot, "bound": False},
            )
            continue
        receivers = _receivers(read, slot)
        admits = {
            "calibration": {name for key in receivers["calibration"] for name in declared[key]},
            "settings": {name for key in receivers["settings"] for name in settings[key]},
        }
        admitted = {kind: set(registry.get(kind, {})) for kind in KINDS}
        stated = _declarations_stated(receivers, declared, settings)
        given = _fill_by_kind(
            slot,
            fills[slot],
            receivers=receivers,
            admits=admits,
            admitted=admitted,
            stated=stated,
            file=file,
        )
        parts, to_registry = {kind: None for kind in KINDS}, {}
        for kind, part in given.items():
            parts[kind], named = _split_part(
                slot,
                kind,
                part,
                receivers=receivers,
                admits=admits,
                admitted=admitted,
                stated=stated,
                file=file,
            )
            if named:
                to_registry[kind] = named
        slot_parts[slot] = SlotFill(
            parts=parts,
            registry=to_registry,
            names=_names_received(parts, receivers, declared, settings),
            entry={"slot": slot, "bound": True},
        )
    return slot_parts


def _receivers(read, slot):
    """The stages whose source lists of each kind name `slot`, `{kind: [key,
    ...]}`, each list sorted."""
    return {
        kind: sorted(
            key
            for key, entry in read["stages"].items()
            if any("$" + slot in names for names in entry[kind].values())
        )
        for kind in KINDS
    }


def _declarations_stated(receivers, declared, settings):
    """What the receiving stages declare, in words, for the calibration and
    the settings, as a refusal of a fill states it."""
    return {
        "calibration": "; ".join(
            f"{key} declares {', '.join(declared[key]) or 'nothing'}"
            for key in receivers["calibration"]
        )
        or "no stage receives it in a calibration list",
        "settings": "; ".join(
            f"{key} declares {', '.join(sorted(settings[key])) or 'nothing'}"
            for key in receivers["settings"]
        )
        or "no stage receives it in a settings list",
    }


def _fill_by_kind(slot, value, *, receivers, admits, admitted, stated, file):
    """The fill `value` of `slot` divided by kind, `{kind: part}`: a fill
    keyed by kind as written; a flat mapping read as a fill of the one kind
    whose names the receiving stages declare or the registry block admits.
    Refused: a fill that is no mapping, a flat fill naming parameters and
    settings both, a flat key of no kind."""
    methods_only = (
        bool(receivers["methods"]) and not receivers["calibration"] and not receivers["settings"]
    )
    if not isinstance(value, Mapping):
        raise FactoryError(
            f"slot {slot!r} is given a {type(value).__name__}, not a "
            f"{'methods mapping' if methods_only else 'mapping'}",
            rule="slot-value-not-a-mapping",
            file=file,
            address=slot,
            written=repr(value)[:60],
            write=(
                f"{slot}={{'methods': [{{'on': <target>, 'method': <tag>, ...}}]}}"
                if methods_only
                else f"{slot}={{'calibration': {{...}}, 'settings': {{...}}}} or a flat mapping "
                "of names to values"
            ),
        )
    value = plain_python(value)
    if value and set(value) <= set(KINDS):
        return {kind: value[kind] for kind in KINDS if kind in value}
    as_parameters = [
        name for name in value if name in admits["calibration"] or name in admitted["calibration"]
    ]
    as_settings = [
        name for name in value if name in admits["settings"] or name in admitted["settings"]
    ]
    if as_parameters and as_settings:
        raise FactoryError(
            f"slot {slot!r} names the parameters {', '.join(as_parameters)} and the settings "
            f"{', '.join(as_settings)} in one flat mapping",
            rule="fill-mixes-kinds",
            file=file,
            address=slot,
            written=", ".join(value),
            write=f"{slot}={{'calibration': {{...}}, "
            "'settings': {...}}, each name under its kind",
        )
    if value and not as_parameters and not as_settings:
        # a flat key of no kind is answered with both kinds' declarations
        key = next(iter(value))
        raise FactoryError(
            f"slot {slot!r}, key {key!r}: no stage that receives this slot declares {key!r} as "
            f"a parameter ({stated['calibration']}) or as a setting ({stated['settings']}), and "
            f"no registry block admits it; a fill key names a parameter or a setting of a stage "
            f"that receives it (AMD-FAC-002 §5)",
            rule="fill-names-nothing",
            file=file,
            address=slot,
            written=key,
            write=_unknown_key_advice(
                admits["calibration"] | admits["settings"],
                admitted["calibration"] | admitted["settings"],
            ),
        )
    return {"settings": dict(value)} if as_settings else {"calibration": dict(value)}


def _unknown_key_advice(declared, registry_names):
    """The advice of a `fill-names-nothing` refusal: the names the receiving
    stages declare and, listed apart, the registry-level names."""
    parts = []
    if declared:
        parts.append(f"one of the declared names {', '.join(sorted(declared))}")
    if registry_names:
        parts.append(f"one of the registry-level names {', '.join(sorted(registry_names))}")
    return (
        ", or ".join(parts)
        or "no name, since no stage receives the slot and no registry block admits a name"
    )


def _split_part(slot, kind, part, *, receivers, admits, admitted, stated, file):
    """The part of `kind` of the fill of `slot` divided in two: the names
    the receiving stages declare, which their lists take, and the names only
    the registry block admits; a methods part is read as a methods mapping by
    `load_methods` and goes to the stages whole. Refused: a methods part no
    stage receives in a methods list or that is no methods mapping, a part
    of another kind that is no mapping, and a name neither declared nor
    admitted."""
    if kind == "methods":
        if not receivers["methods"]:
            raise FactoryError(
                f"slot {slot!r} gives a methods part, and no stage receives this slot in a "
                f"methods list",
                rule="fill-names-nothing",
                file=file,
                address=slot,
                written="methods",
                write="a slot a methods list names, such as `$method_switch`",
            )
        part = {"methods": part} if isinstance(part, list) else part
        if not isinstance(part, Mapping) or not isinstance(part.get("methods"), list):
            raise FactoryError(
                f"the methods part of slot {slot!r} is no methods mapping",
                rule="slot-value-not-a-mapping",
                file=file,
                address=slot,
                written=repr(part)[:60],
                write=f"{slot}={{'methods': [{{'on': <target>, 'method': <tag>, ...}}]}}",
            )
        return load_methods(part), {}
    if not isinstance(part, Mapping):
        raise FactoryError(
            f"the {kind} part of slot {slot!r} is a {type(part).__name__}, not a mapping",
            rule="slot-value-not-a-mapping",
            file=file,
            address=slot,
            written=repr(part)[:60],
            write=f"{slot}={{'{kind}': {{<name>: <value>}}}}",
        )
    strange = [name for name in part if name not in admits[kind] and name not in admitted[kind]]
    if strange:
        raise FactoryError(
            f"slot {slot!r}, key {strange[0]!r}: no stage that receives this slot in a {kind} "
            f"list declares {strange[0]!r} ({stated[kind]}), and no registry block admits it; a "
            f"fill key names a parameter or a setting of a stage that receives it "
            f"(AMD-FAC-002 §5)",
            rule="fill-names-nothing",
            file=file,
            address=slot,
            written=strange[0],
            write=_unknown_key_advice(admits[kind], admitted[kind]),
        )
    return (
        {name: copy.deepcopy(part[name]) for name in part if name in admits[kind]},
        {name: copy.deepcopy(part[name]) for name in part if name not in admits[kind]},
    )


def _names_received(parts, receivers, declared, settings):
    """The names of the fill each receiving stage takes, `{kind: {stage:
    [name, ...]}}`: for a calibration list the fill's parameter names the
    stage declares, for a settings list its setting names the stage's
    settings files and methods name, for a methods list the targets of its
    methods entries."""
    return {
        "calibration": {
            key: [name for name in sorted(parts["calibration"] or {}) if name in declared[key]]
            for key in receivers["calibration"]
        },
        "settings": {
            key: [name for name in sorted(parts["settings"] or {}) if name in settings[key]]
            for key in receivers["settings"]
        },
        "methods": {
            key: sorted({entry["on"] for entry in (parts["methods"] or {}).get("methods", [])})
            for key in receivers["methods"]
        },
    }


# --- the records ---


def _syntactic_periods(read, templates, *, stages, slot_parts, directory, file, cache):
    """The periods of the syntactic trellis: one period per template and in it
    one record per stage the template names and the recipe makes active at
    that period, in the key order `stage, calibration, settings, methods,
    provenance`: the stage's source, the merged mapping of each kind
    and, under `provenance["source_lists"]`, the ordered sources that produced
    it; the interval of a stage restricted by `periods: [lo, hi]` stands under
    `provenance["active"]`. A record is its own dictionary and shares no
    mapping with another."""
    periods = []
    for h, template in enumerate(templates):
        records = {}
        for key in template["stages"]:
            entry = read["stages"][key]
            if not _is_active(entry["periods"], h):
                continue
            mappings, lists = {}, {}
            for kind in KINDS:
                mappings[kind], lists[kind] = _merged_source_list(
                    _source_names_at(entry, kind, h, file=file),
                    kind,
                    key,
                    directory=directory,
                    file=file,
                    cache=cache,
                    slot_parts=slot_parts,
                )
            provenance = {**stages[key]["provenance"], "source_lists": lists}
            if entry["periods"] is not None:
                provenance["active"] = list(entry["periods"])
            records[key] = {
                "stage": dict(stages[key]["stage"]),
                **mappings,
                "provenance": provenance,
            }
        periods.append({"stages": records, "connectors": copy.deepcopy(template["connectors"])})
    return periods


def _source_names_at(entry, kind, h, *, file):
    """The source names of one kind list of a stage that apply at period `h`:
    the `all` names, then the names of the one range holding `h`, each with
    its range key or None."""
    names = [(name, None) for name in entry[kind]["all"]]
    for key, listed in entry[kind].items():
        if key != "all":
            lo, hi = _range(key, file=file, address=key)
            if lo <= h <= hi:
                names.extend((name, key) for name in listed)
    return names


def _merged_source_list(names, kind, stage, *, directory, file, cache, slot_parts):
    """The merged assignments of one source list and its ordered provenance
    entries: a file's entry from `_read_source`, a slot's from `slot_parts`,
    its `names` the list of the fill's names of this kind that this stage
    declares, each entry with its range key where it stands in a range list;
    an unbound slot contributes nothing."""
    chain, entries = [], []
    for name, range_key in names:
        address = f"stages.{stage}.{kind}.{range_key or 'all'}"
        if name.startswith("$"):
            slot = slot_parts[name[1:]]
            part = slot.parts[kind]
            entry = {**slot.entry, "names": list(slot.names.get(kind, {}).get(stage, []))}
            values = (
                {}
                if part is None
                else {"methods": part}
                if kind == "methods" and isinstance(part, list)
                else part
            )
        else:
            values, entry = _read_source(
                name, kind, directory=directory, file=file, address=address, cache=cache
            )
            if "parents" in entry:
                entry["parents"] = list(entry["parents"])
        if range_key is not None:
            entry["range"] = range_key
        chain.append(values)
        entries.append(entry)
    merged = _merge_sources(chain)
    # a methods list merges to the methods mapping the reader returns,
    # `{"methods": []}` when the list names no source, the form into which
    # `load_trellis` reads an inline mapping, so that the two readers of a
    # trellis write one record
    return (load_methods(merged) if kind == "methods" else merged), entries


# --- the sources ---


class Source(NamedTuple):
    """A source as a source list reads it: its assignments and its provenance
    entry."""

    assignments: dict
    entry: dict


def _read_source(name, kind, *, directory, file, address, cache):
    """The assignments the source `name` makes, for a list of kind `kind`,
    read once per call through `cache`, and its provenance entry: the name,
    the path and the digest of the file, and the files of its parent chain.
    A file of another kind than the list it stands in is refused."""
    if name not in cache:
        path = _registry_file(name, directory=directory, file=file, address=address)
        contents, files = _source_contents(path, directory=directory, file=file, address=address)
        found, values = _kind_and_assignments(contents, path, file=file, address=address)
        entry = {
            "source": name,
            "path": str(path),
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "kind": found,
        }
        if len(files) > 1:
            entry["parents"] = files[1:]
        cache[name] = Source(assignments=values, entry=entry)
    read = cache[name]
    if read.entry["kind"] != kind:
        raise FactoryError(
            f"the source {name!r} is a {read.entry['kind']} file and stands in the {kind} list "
            f"{address}",
            rule="recipe-source",
            file=file,
            address=address,
            written=name,
            write=f"a {kind} file in this list",
        )
    return Source(
        assignments=read.assignments,
        entry={key: value for key, value in read.entry.items() if key != "kind"},
    )


def _registry_file(name, *, directory, file, address):
    """The file a name of the registry stands for, a source, the recipe or
    the trellis file: `<name>.yml`, `<name>.yaml` or the name as written,
    under the registry directory; a name written with its extension is read
    as written."""
    base = Path(directory) / name
    candidates = (
        (base,)
        if base.suffix in (".yml", ".yaml")
        else (Path(f"{base}.yml"), Path(f"{base}.yaml"), base)
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FactoryError(
        f"the registry holds no source file {name!r}; tried {', '.join(map(str, candidates))}",
        rule="recipe-source",
        file=file,
        address=address,
        written=name,
        write="the name of a file under the registry, without its extension",
    )


def _source_contents(path, *, directory, file, address, chain=()):
    """The contents of a source file with its `parent:` chain merged beneath
    it and its metadata keys removed, not yet unwrapped, and the files of the
    chain, the file itself first; the parent's methods list is merged by `on`,
    as a source list merges."""
    resolved = path.resolve()
    if len(chain) > 10:
        raise FactoryError(
            f"the parent chain of {chain[0]} exceeds ten files",
            rule="recipe-source",
            file=file,
            address=address,
            written=" -> ".join(str(p) for p in chain),
            write="a chain of at most ten files",
        )
    if resolved in chain:
        raise FactoryError(
            f"the parent chain of {chain[0]} returns to {path}",
            rule="recipe-source",
            file=file,
            address=address,
            written=" -> ".join(str(p) for p in chain + (resolved,)),
            write="a chain that ends in a file with no parent",
        )
    data = read_yaml_mapping(path, rule="recipe-source", address=address)
    parent = data.get("parent")
    contents = {key: copy.deepcopy(value) for key, value in data.items() if key not in METADATA}
    files = [str(path)]
    if parent is not None:
        if not isinstance(parent, str) or not parent.strip():
            raise FactoryError(
                f"the parent of {path} is {parent!r}, not a source name",
                rule="recipe-source",
                file=file,
                address=address,
                written=repr(parent),
                write="parent: <source name>",
            )
        above, parents = _source_contents(
            _registry_file(parent, directory=directory, file=file, address=address),
            directory=directory,
            file=file,
            address=address,
            chain=chain + (resolved,),
        )
        contents, files = _deep_merge(above, contents), files + parents
    return contents, files


def _kind_and_assignments(contents, path, *, file, address):
    """The kind and the assignments of a source file, its kind told by its
    top key: `calibration:` (and `parameters:` inside it) and `settings:`
    unwrapped, `methods:` read as a methods mapping by `load_methods`."""
    if "methods" in contents:
        try:
            return "methods", load_methods(contents)
        except (TypeError, ValueError) as error:
            raise FactoryError(
                f"{path} is not a methods file the reader admits: {error}",
                rule="recipe-source",
                file=file,
                address=address,
                written=repr(contents.get("methods"))[:60],
                write="methods: a list of entries, each naming its target under `on`",
            ) from None
    if set(contents) == {"calibration"} and isinstance(contents["calibration"], Mapping):
        inner = contents["calibration"]
        return "calibration", dict(inner.get("parameters", inner))
    if set(contents) == {"settings"} and isinstance(contents["settings"], Mapping):
        return "settings", dict(contents["settings"])
    raise FactoryError(
        f"{path} has the top keys {sorted(map(str, contents))!r}; a source file has one top key "
        f"naming its kind",
        rule="recipe-source",
        file=file,
        address=address,
        written=", ".join(sorted(map(str, contents))),
        write="calibration:, settings: or methods: as the one top key",
    )


def _merge_sources(chain):
    """The merge of a source list: every assignment of every source kept, the
    later source standing where two assign."""
    merged = {}
    for source in chain:
        merged = _deep_merge(merged, source)
    return merged


def _deep_merge(base, overlay):
    """The merge of two assignments: mappings key by key, lists of mappings
    entry by entry matched on `on`, any other value the overlay's."""
    if isinstance(base, Mapping) and isinstance(overlay, Mapping):
        result = dict(base)
        for key, value in overlay.items():
            result[key] = (
                _deep_merge(result[key], value) if key in result else copy.deepcopy(value)
            )
        return result
    if isinstance(base, list) and isinstance(overlay, list):
        return _merge_keyed_list(base, overlay)
    return copy.deepcopy(overlay)


def _merge_keyed_list(base, overlay):
    """Two lists of mappings merged entry by entry on the key `on`, an entry
    of `!marginals` matched only by another of `!marginals` (`entry_key`), the
    overlay's unmatched entries appended; the overlay replaces the list whole
    where an entry of either carries no `on`, since no entry of it can be
    matched."""
    if not all(isinstance(entry, Mapping) and "on" in entry for entry in base + overlay):
        return copy.deepcopy(overlay)
    result, seen = [], set()
    for entry in base:
        over = next((o for o in overlay if entry_key(o) == entry_key(entry)), None)
        result.append(_deep_merge(entry, over) if over is not None else copy.deepcopy(entry))
        seen.add(entry_key(entry))
    result.extend(copy.deepcopy(o) for o in overlay if entry_key(o) not in seen)
    return result
