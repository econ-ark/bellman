"""The readers of the sources a stage is bound from, and the one reader of a
YAML file.

`load_calibration`, `load_settings` and `load_methods` read a calibration,
settings or methods source, a mapping or the path of a YAML file, into what a
binding verb binds: the parameter values, the numerical settings, or the
ordered authored method records with each method tag and its payload kept. A
source given by its path is read by `read_yaml_mapping`, the one reader of a
YAML file of the binding verbs and of the Bellman factory: it keeps every tag,
refuses a key written twice, which YAML reads silently as its last value, and
refuses every file it cannot read as one mapping, as a `FactoryError` under the
rule its caller names; the three readers name `readable-file`. The binding
verbs, which accept a source by its path, are defined
in `bellman.stage.binding_verbs`.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional, Union

import yaml

from bellman.refusals import FactoryError

__all__ = ["load_calibration", "load_settings", "load_methods", "read_yaml_mapping"]


# --- the readers of a source ---


def load_calibration(source: Union[str, Path, dict]) -> dict:
    """The parameter values of a calibration source, as a flat mapping.

    The source is the path of a YAML file or a mapping in one of three
    forms: flat, `{beta: 0.96, delta: 0.03}`; nested,
    `{calibration: {parameters: {...}}}`; or split, `{parameters: {...},
    settings: {...}}`. The settings of a source are left out.
    """
    data = _load_source(source)

    if "calibration" in data:
        data = data["calibration"]
        if not isinstance(data, Mapping):
            raise ValueError(f"{source!r}: calibration must be a mapping")

    if "parameters" in data:
        data = data["parameters"]
        if not isinstance(data, Mapping):
            raise ValueError(f"{source!r}: parameters must be a mapping")
        return dict(data)

    if "settings" in data:
        data = {k: v for k, v in data.items() if k != "settings"}

    return dict(data)


def load_settings(source: Union[str, Path, dict]) -> dict:
    """The numerical settings of a settings source, as a flat mapping.

    The source is the path of a YAML file or a mapping in one of three
    forms: flat, `{n_w: 200, tol: 1e-8}`; nested, `{settings: {...}}`; or
    the split form of a calibration file, `{parameters: {...}, settings:
    {...}}`.
    """
    data = _load_source(source)

    if "settings" in data:
        data = data["settings"]
    elif "calibration" in data:
        calib = data["calibration"]
        if not isinstance(calib, Mapping):
            raise ValueError(f"{source!r}: calibration must be a mapping")
        if "settings" in calib:
            data = calib["settings"]
    if not isinstance(data, Mapping):
        raise ValueError(f"{source!r}: settings must be a mapping")

    return dict(data)


def _load_source(source: Union[str, Path, dict]) -> dict:
    """The mapping of a source given as a mapping or as the path of a YAML
    file that holds one."""
    if isinstance(source, Mapping):
        return dict(source)
    if not isinstance(source, (str, Path)):
        raise TypeError("a source must be a mapping or a YAML path")
    return read_yaml_mapping(source, rule="readable-file", address=None)


def load_methods(source: Union[str, Path, dict]) -> dict:
    """The authored method records of a methods source, a mapping or the
    path of a YAML file, in the order written, each tag and its payload
    kept."""
    if isinstance(source, Mapping):
        return _checked_methods(source)

    data = read_yaml_mapping(Path(source), rule="readable-file", address=None)
    return _checked_methods(data, source=str(source))


def _checked_methods(data: Any, source: Optional[str] = None) -> dict:
    """The authored entries of a methods source, checked, as independent
    records in source order."""
    where = source or "in-memory methods"
    if not isinstance(data, Mapping):
        raise TypeError(f"{where}: methodization source must be a mapping")
    if any(key in data for key in ("scheme", "schemes")):
        raise ValueError(f"{where}: scheme/schemes source records are not supported")
    methods = data.get("methods", [])
    if not isinstance(methods, list):
        raise TypeError(f"{where}: methods must be a list of authored records")
    result = {
        copy.deepcopy(key): _copy_authored(value)
        for key, value in data.items()
        if key != "methods"
    }
    result["methods"] = []
    targets = set()
    for index, item in enumerate(methods):
        location = f"{where}: methods entry {index + 1}"
        if not isinstance(item, Mapping):
            raise TypeError(f"{location} must be a mapping")
        entry = {}
        for key, value in item.items():
            key = "on" if key is True else key
            if key in entry:
                raise ValueError(f"{location}: Duplicate entry key {key!r}")
            entry[key] = _copy_authored(value)
        if any(key in entry for key in ("scheme", "schemes")):
            raise ValueError(f"{location}: scheme/schemes records are not supported")
        target = entry.get("on")
        if not isinstance(target, str) or not target.strip() or "," in target:
            raise ValueError(f"{location}: on must name one nonempty target without commas")
        key = entry_key(entry)
        if key in targets:
            raise ValueError(f"{location}: Duplicate methodization target {target!r}")
        targets.add(key)
        if "method" in entry:
            method = entry["method"]
            name = method.get("__yaml_tag__") if isinstance(method, Mapping) else method
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{location}: method must be a nonempty string or tagged mapping")
        if "settings" in entry and not isinstance(entry["settings"], Mapping):
            raise TypeError(f"{location}: settings must be a mapping")
        # `block` is the path of a block file, relative to the methods file
        # (specification 0.6 §4)
        for key in ("handler", "grid", "block"):
            if key in entry and (not isinstance(entry[key], str) or not entry[key].strip()):
                raise ValueError(f"{location}: {key} must be a nonempty string")
        result["methods"].append(entry)
    return result


# the spellings of the method `!marginals` in an entry of a methods source, a
# string or the tag of a tagged mapping
_MARGINALS = ("!marginals", "marginals")


def entry_key(entry):
    """The key that tells the entries of a methods source apart: the target
    the entry's `on` names, and whether its method is `!marginals`. A
    `!marginals` entry adds a marginal block's lines to the builder its target
    names, so it shares that target with one entry of another method, such as
    `!vfi` or a representation on the same builder (decision MB-U4)."""
    method = entry.get("method")
    name = method.get("__yaml_tag__") if isinstance(method, Mapping) else method
    return entry["on"], name in _MARGINALS


def _copy_authored(value, active=frozenset()):
    """A copy of nested source containers, read-only mappings included."""
    if isinstance(value, (Mapping, list, tuple)):
        if id(value) in active:
            raise ValueError("method records cannot contain recursive containers")
        active = active | {id(value)}
        if isinstance(value, Mapping):
            return {
                copy.deepcopy(key): _copy_authored(item, active) for key, item in value.items()
            }
        items = [_copy_authored(item, active) for item in value]
        return tuple(items) if isinstance(value, tuple) else items
    return copy.deepcopy(value)


# --- the one reader of a YAML file ---


def read_yaml_mapping(path, *, rule, address, text=None):
    """The YAML mapping at `path`, every tag kept as `{"__yaml_tag__": tag,
    ...}` and a document tag such as `!trellis` removed from the top; refused
    as a `FactoryError` under `rule`, at `address`, where the file is missing,
    cannot be read, does not read as YAML, writes a key twice or holds no
    mapping. A `text` given is read in the file's place, the text of an
    unsaved buffer of `path` (model interface spec 0.4 §3.1), with the same
    refusals but the two of a missing or unreadable file."""
    try:
        if text is None:
            with open(path, encoding="utf-8") as stream:
                raw = yaml.load(stream, Loader=TagPreservingLoader)
        else:
            raw = yaml.load(text, Loader=TagPreservingLoader)
    except FileNotFoundError:
        raise FactoryError(
            f"the file {path} does not exist",
            rule=rule,
            file=str(path),
            address=address,
            written=Path(path).name,
            write="a file that exists at this name",
        ) from None
    except DuplicateKey as error:
        raise FactoryError(
            f"the key {error.key!r} is written twice in "
            f"{path}, the second time at line {error.line}",
            rule=rule,
            file=str(path),
            address=address,
            written=f"{error.key!r} at line {error.line}",
            write="each key once",
        ) from None
    except OSError as error:
        raise FactoryError(
            f"the file {path} cannot be read: {error.strerror}",
            rule=rule,
            file=str(path),
            address=address,
            written=Path(path).name,
            write="a readable YAML file",
        ) from None
    except (yaml.YAMLError, ValueError) as error:
        raise FactoryError(
            f"the file {path} does not read as YAML: {error}",
            rule=rule,
            file=str(path),
            address=address,
            written=Path(path).name,
            write="a YAML mapping the loader reads",
        ) from None
    if not isinstance(raw, Mapping):
        raise FactoryError(
            f"{path} holds no mapping",
            rule=rule,
            file=str(path),
            address=address,
            written=repr(raw)[:60],
            write="a mapping at the top of the file",
        )
    return {key: value for key, value in raw.items() if key != "__yaml_tag__"}


class DuplicateKey(ValueError):
    """A mapping key written twice in a YAML document: `key`, and `line`, the
    line of the second writing, which `read_yaml_mapping` refuses as a
    `FactoryError`."""

    def __init__(self, key, line):
        self.key, self.line = key, line
        super().__init__(f"the key {key!r} is written twice, the second time at line {line}")


class TagPreservingLoader(yaml.SafeLoader):
    """A SafeLoader that keeps every `!tag` as `{"__yaml_tag__": tag, ...}`,
    reads the YAML keys `on` and `off` as those words, and refuses a mapping
    key written twice with `DuplicateKey`."""

    def construct_mapping(self, node, deep=False):
        """A YAML mapping, its keys `on` and `off` read as those words; a key
        written twice is refused as `DuplicateKey`, and a key that is no
        scalar as a `ValueError`."""
        keys = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self._mapping_key(key_node, deep)
            try:
                duplicate = key in keys
                keys.add(key)
            except TypeError as error:
                raise ValueError("a mapping key must be a scalar value") from error
            if duplicate:
                raise DuplicateKey(key, key_node.start_mark.line + 1)
        self.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = self._mapping_key(key_node, deep)
            result[key] = self.construct_object(value_node, deep=deep)
        return result

    def _mapping_key(self, key_node, deep):
        """A mapping key as YAML reads it, and the keys `on` and `off`, which
        YAML reads as booleans, as those words."""
        key = self.construct_object(key_node, deep=deep)
        if key_node.tag == "tag:yaml.org,2002:bool" and key_node.value.lower() in ("on", "off"):
            key = key_node.value.lower()
        return key


def _tag_constructor(loader, tag_suffix, node):
    """The value of a tagged node: the tag under `__yaml_tag__` beside the
    scalar, the mapping or the sequence the tag marks."""
    if isinstance(node, yaml.ScalarNode):
        return {"__yaml_tag__": tag_suffix, "value": loader.construct_scalar(node)}
    if isinstance(node, yaml.MappingNode):
        value = loader.construct_mapping(node, deep=True)
        if "__yaml_tag__" in value:
            raise ValueError("a tagged mapping cannot redefine __yaml_tag__")
        return {"__yaml_tag__": tag_suffix, **value}
    return {"__yaml_tag__": tag_suffix, "value": loader.construct_sequence(node, deep=True)}


TagPreservingLoader.add_multi_constructor("!", _tag_constructor)
