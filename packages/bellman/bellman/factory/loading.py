"""The readers of the files a model is written in.

`load_stage` reads one stage file into its source record. `load_trellis`
reads a trellis file whose stages are records into the syntactic trellis.
`read_trellis_file` reads the periods and the inter-period mappings a trellis
file writes, each `{template, repeat}` entry and a mapping standing for every
pair expanded; `load_trellis` and `load_recipe` both read a trellis file
through it. Nothing here parses a stage or binds a mapping.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from os import fspath
from pathlib import Path

from bellman.refusals import FactoryError
from bellman.stage.sources import load_calibration, load_methods, load_settings, read_yaml_mapping

__all__ = [
    "KINDS",
    "METADATA",
    "load_stage",
    "load_trellis",
    "period_and_repeat",
    "plain_python",
    "read_trellis_file",
]


# the three kinds of binding source, in the key order of a record; the trellis
# verbs bind them in another order, calibrate, methodize, configure
KINDS = ("calibration", "settings", "methods")

# the keys of a source file that are about the file and assign nothing
METADATA = frozenset({"parent", "description", "version", "__comment__", "__yaml_tag__"})


# --- the stage file ---


def load_stage(path):
    """The source record of the stage file at `path`: its text and its origin
    under `stage`, the calibration and the settings empty, the methods the
    empty methods mapping `{"methods": []}`, its origin and the digest of its
    text under `provenance`. Nothing is parsed. A path that names no `.bl`
    file, or a file that cannot be read as UTF-8 text, is refused under
    `readable-file`."""
    original = fspath(path)
    name = Path(original).name
    if Path(original).suffix != ".bl":
        raise FactoryError(
            f"load_stage reads a stage file, and {name} is no .bl file",
            rule="readable-file",
            file=original,
            written=name,
            write="the path of a stage file, `<name>.bl`",
        )
    try:
        with open(original, encoding="utf-8", newline="") as stream:
            text = stream.read()
    except FileNotFoundError:
        raise FactoryError(
            f"the file {original} does not exist",
            rule="readable-file",
            file=original,
            written=name,
            write="the path of a stage file that exists",
        ) from None
    except OSError as error:
        raise FactoryError(
            f"the file {original} cannot be read: {error.strerror}",
            rule="readable-file",
            file=original,
            written=name,
            write="the path of a readable stage file",
        ) from None
    except UnicodeDecodeError:
        raise FactoryError(
            f"the file {original} is not UTF-8 text",
            rule="readable-file",
            file=original,
            written=name,
            write="a stage file saved as UTF-8 text",
        ) from None
    return {
        "stage": {"text": text, "origin": original},
        "calibration": {},
        "settings": {},
        "methods": load_methods({}),
        "provenance": {"origin": original, "sha256": sha256(text.encode("utf-8")).hexdigest()},
    }


# --- the trellis file ---


def load_trellis(file, texts=None):
    """The syntactic trellis a trellis file writes out: each period's `stages`
    a mapping from keys to records, each record naming its `.bl` file under
    `stage` and its three mappings inline or as paths, both relative to the
    file's directory; a `{template, repeat}` entry read as `read_trellis_file`
    reads it; each stage file read once. The result holds `periods`,
    `inter_connectors` and, under `provenance`, the file's path and digest.
    `texts` maps a file's resolved path to the text read in its place, and
    reaches the trellis file and its period files alone, whose paths taken
    stand under the provenance's `texts` (model interface spec 0.4 §3.1)."""
    file = Path(file)
    directory = file.parent
    read = read_trellis_file(file, texts)
    # the source record of each stage file, read once
    stage_sources, periods = {}, []
    for h, period in enumerate(read["periods"]):
        address = f"periods[{h}]"
        if not isinstance(period["stages"], Mapping):
            raise _trellis_shape_refusal(
                f"{address}.stages is no mapping of keys to records",
                file=file,
                address=f"{address}.stages",
                written=repr(period["stages"])[:60],
                write="stages: {<key>: {stage: <file>.bl, "
                "calibration: ..., settings: ..., methods: ...}}",
            )
        records = {}
        for key, written in period["stages"].items():
            where = f"{address}.stages[{key!r}]"
            if not isinstance(written, Mapping) or not isinstance(written.get("stage"), str):
                raise _trellis_shape_refusal(
                    f"{where} has no `stage` naming a .bl file",
                    file=file,
                    address=where,
                    written=repr(written)[:60],
                    write="stage: <file>.bl",
                )
            path = (
                written["stage"]
                if Path(written["stage"]).is_absolute()
                else str(directory / written["stage"])
            )
            if Path(path).suffix != ".bl":
                raise _trellis_shape_refusal(
                    f"{where}.stage names {written['stage']!r}, which is no .bl file",
                    file=file,
                    address=f"{where}.stage",
                    written=written["stage"],
                    write="stage: <file>.bl",
                )
            if not Path(path).is_file():
                raise _trellis_shape_refusal(
                    f"{where}.stage names {written['stage']!r}, and no such file exists",
                    file=file,
                    address=f"{where}.stage",
                    written=written["stage"],
                    write="stage: the path of a stage file, "
                    "relative to the trellis file or absolute",
                )
            if path not in stage_sources:
                stage_sources[path] = load_stage(path)
            source = stage_sources[path]
            record = {
                "stage": dict(source["stage"]),
                "provenance": {**source["provenance"], "source_lists": {}},
            }
            for kind in KINDS:
                record[kind], record["provenance"]["source_lists"][kind] = _record_mapping(
                    kind, written.get(kind), directory, file, f"{where}.{kind}"
                )
            if "label" in written:
                record["label"] = written["label"]
            records[key] = record
        periods.append({"stages": records, "connectors": period["connectors"]})
    provenance = {"trellis": {"path": read["path"], "sha256": read["sha256"]}}
    if "texts" in read:
        provenance["texts"] = read["texts"]
    return {
        "periods": periods,
        "inter_connectors": read["inter_connectors"],
        "provenance": provenance,
    }


def read_trellis_file(file, texts=None):
    """The periods and the inter-period mappings a trellis file writes,
    expanded: each entry of `periods` written out or
    given as `{template: <period file>, repeat: n}` and then repeated `n`
    times; `inter_connectors` one mapping per adjacent pair, or one mapping
    standing for every pair, or none, standing for empty mappings. Each period
    is `{"stages": <as written: a list of keys or a mapping of records>,
    "connectors": [...]}`; the file's path and digest stand beside them.
    `texts` maps a file's resolved path to the text read in its place, for
    the trellis file and the period files; the digest is that of the text
    read, and the sorted paths taken stand under `texts`, a key written only
    where one was taken (model interface spec 0.4 §3.1)."""
    file = Path(file)
    raw, digest, text_path = _mapping_and_digest(
        file, texts, rule="trellis-file-shape", address="periods"
    )
    # the resolved paths of the texts read in their files' places
    taken = set() if text_path is None else {text_path}
    if not isinstance(raw.get("periods"), list) or not raw["periods"]:
        raise _trellis_shape_refusal(
            "the trellis file has no list `periods`",
            file=file,
            address="periods",
            written=repr(raw)[:60],
            write="periods: [{template: period.yml, repeat: 51}] or the periods written out",
        )
    periods = []
    for number, entry in enumerate(raw["periods"]):
        period, repeat = period_and_repeat(entry, file.parent, file, f"periods[{number}]", texts)
        periods.extend(deepcopy(period) for _ in range(repeat))
        # the period file's resolved path, where `period_and_repeat` read its text from the mapping
        held =_text_path(period["template"], texts) if "template" in period else None
        if held is not None:
            taken.add(held)
    inter = raw.get("inter_connectors") or []
    if not isinstance(inter, list) or not all(isinstance(mapping, Mapping) for mapping in inter):
        raise _trellis_shape_refusal(
            "`inter_connectors` is a list of mappings",
            file=file,
            address="inter_connectors",
            written=repr(inter)[:60],
            write="inter_connectors: [{<continuation field>: <arrival field>}]",
        )
    pairs = max(len(periods) - 1, 0)
    if len(inter) == 1:
        # one mapping stands for every pair, and for no pair when the file
        # writes one period, so a template with a standing mapping is read at
        # `repeat: 1`
        inter = [deepcopy(inter[0]) for _ in range(pairs)]
    elif not inter:
        inter = [{} for _ in range(pairs)]
    elif len(inter) != pairs:
        raise _trellis_shape_refusal(
            f"{len(inter)} inter-period mappings for {len(periods)} periods",
            file=file,
            address="inter_connectors",
            written=repr(inter)[:60],
            write=f"{pairs} mappings, one for each adjacent pair, or one standing for every pair",
        )
    read = {
        "periods": periods,
        "inter_connectors": [dict(mapping) for mapping in inter],
        "path": str(file),
        "sha256": digest,
    }
    if taken:
        read["texts"] = sorted(taken)
    return read


def period_and_repeat(entry, directory, file, address, texts=None):
    """The period one entry of the `periods` list writes and the number of
    times it is repeated: the entry itself, or the period file its `template`
    names, read relative to `directory`, the entry's own keys standing over
    the file's; a period read from a file carries the file's path under
    `template`. A `repeat` that is not a positive integer is refused.
    `texts` maps a file's resolved path to the text read in its place, the
    period file's text read where it holds one (model interface spec 0.4
    §3.1)."""
    if not isinstance(entry, Mapping):
        raise _trellis_shape_refusal(
            f"{address} is no mapping",
            file=file,
            address=address,
            written=repr(entry)[:60],
            write="{stages: ..., connectors: []} or {template: <period file>, repeat: <n>}",
        )
    period = {key: value for key, value in entry.items() if key != "__yaml_tag__"}
    template = None
    if "template" in period:
        template = Path(directory) / str(period.pop("template"))
        named, _, _ = _mapping_and_digest(
            template, texts, rule="trellis-file-shape", address=f"{address}.template"
        )
        period = {**named, **period}
    if "stages" not in period:
        raise _trellis_shape_refusal(
            f"{address} names no `stages`",
            file=file,
            address=address,
            written=repr(period)[:60],
            write="stages: [<keys>] in the trellis file, or in the period file the entry names",
        )
    connectors = period.get("connectors") or []
    if not isinstance(connectors, list):
        raise _trellis_shape_refusal(
            f"{address}.connectors is no list",
            file=file,
            address=f"{address}.connectors",
            written=repr(connectors)[:60],
            write="connectors: []",
        )
    repeat = period.get("repeat", 1)
    if isinstance(repeat, bool) or not isinstance(repeat, int) or repeat < 1:
        raise _trellis_shape_refusal(
            f"{address}.repeat is {repeat!r}, not a positive integer",
            file=file,
            address=f"{address}.repeat",
            written=repr(repeat),
            write="repeat: <n> with n a positive integer, or no repeat for one period",
        )
    expanded = {"stages": period["stages"], "connectors": deepcopy(connectors)}
    if template is not None:
        expanded["template"] = str(template)
    return expanded, repeat


# --- the texts of unsaved buffers (model interface spec 0.4 §3.1) ---


def _text_path(path, texts):
    """The resolved path of `path`, as a string, where `texts`, a mapping
    from a file's resolved path to the text read in its place, holds a text
    for it; None where it holds none."""
    if not texts:
        return None
    resolved = str(Path(path).resolve())
    return resolved if resolved in texts else None


def _mapping_and_digest(path, texts, *, rule, address):
    """The YAML mapping `read_yaml_mapping` reads at `path` under `rule` and
    `address`, from the text `texts` holds for the file's resolved path where
    it holds one and from the file otherwise; the SHA-256 of the UTF-8 bytes
    of that text, or of the file's bytes; and the resolved path where the
    text was taken, else None (model interface spec 0.4 §3.1)."""
    taken = _text_path(path, texts)
    if taken is None:
        mapping = read_yaml_mapping(path, rule=rule, address=address)
        return mapping, sha256(Path(path).read_bytes()).hexdigest(), None
    text = texts[taken]
    mapping = read_yaml_mapping(path, rule=rule, address=address, text=text)
    return mapping, sha256(text.encode("utf-8")).hexdigest(), taken


# --- the mappings of a record and the refusal of a trellis file ---

# the reader of each kind of binding source
SOURCE_READERS = {
    "calibration": load_calibration,
    "settings": load_settings,
    "methods": load_methods,
}


def _record_mapping(kind, value, directory, file, address):
    """The mapping of one kind a written record gives, inline or read from the
    file its string names relative to `directory`, with its provenance
    entries: one for a file, none for a mapping. An absent or null methods
    value is the empty methods mapping `{"methods": []}`; a methods file read
    by path drops the metadata keys `METADATA` names."""
    if value is None:
        return (load_methods({}) if kind == "methods" else {}), []
    if isinstance(value, Mapping):
        return (load_methods(value) if kind == "methods" else dict(value)), []
    if isinstance(value, str):
        path = Path(value) if Path(value).is_absolute() else Path(directory) / value
        if not path.is_file():
            raise _trellis_shape_refusal(
                f"{address} names {value!r}, and no such file stands beside the trellis file",
                file=file,
                address=address,
                written=value,
                write=f"{kind}: {{...}} inline, or the path of a file",
            )
        mapping = SOURCE_READERS[kind](path)
        if kind == "methods":
            mapping = {key: item for key, item in mapping.items() if key not in METADATA}
        return mapping, [
            {"source": value, "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}
        ]
    raise _trellis_shape_refusal(
        f"{address} is a {type(value).__name__}; a record's "
        f"{kind} is a mapping or the path of a file",
        file=file,
        address=address,
        written=repr(value)[:60],
        write=f"{kind}: {{...}} or {kind}: <file>.yml",
    )


def _trellis_shape_refusal(message, *, file, address, written, write):
    """The refusal under `trellis-file-shape` of what the trellis file `file`
    writes at `address`."""
    return FactoryError(
        message,
        rule="trellis-file-shape",
        file=str(file),
        address=address,
        written=written,
        write=write,
    )


# --- plain Python values ---


def plain_python(value):
    """`value` with every mapping a `dict`, every sequence a `list` and every
    numpy scalar the Python number it holds, so that two mappings equal
    in value compare equal whatever containers hold them."""
    if isinstance(value, Mapping):
        return {key: plain_python(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain_python(item) for item in value]
    if type(value).__module__ == "numpy" and hasattr(value, "item"):
        return value.item()
    return value
