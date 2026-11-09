"""The readers of the calibration and the settings a stage is bound from, and
the one reader of a YAML file.

`load_calibration` and `load_settings` read a calibration or a settings
source, a mapping or the path of a YAML file, into what a binding verb binds:
the parameter values or the numerical settings. A methods source is no YAML
source: the methods of a stage are `.bl` additions, read by
`bellman.stage.levels.read_addition` (specification 0.7 §4). A source given by
its path is read by `read_yaml_mapping`, the one reader of a YAML file of the
binding verbs and of the Bellman factory: it keeps every tag, refuses a key
written twice, which YAML reads silently as its last value, at the second key
with the first as a related location, and refuses every file it cannot read
as one mapping, as a `FactoryError` under the rule its caller names; the two
readers name `readable-file`. `key_marks` is the one reader of the node marks
of a YAML file, from which a refusal of a key is positioned, and
`settings_key_positions` reads from it the position of each setting's key in
the settings files a stage is configured from (Model Interface 0.9 §4,
decision 7). The binding verbs, which accept a source by its path, are
defined in `bellman.stage.binding_verbs`.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Union

import yaml

from bellman.refusals import FactoryError, Location

__all__ = [
    "key_marks",
    "load_calibration",
    "load_settings",
    "read_yaml_mapping",
    "settings_key_positions",
]


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
            f"the key {error.key!r} is written twice in {Path(path).name}, at line "
            f"{error.first_line} and again at line {error.line}",
            rule=rule,
            file=str(path),
            address=address,
            written=f"{error.key!r} at line {error.line}",
            write=f"one `{error.key}:` entry",
            line=error.line,
            column=error.column,
            related=(
                Location(
                    "original declaration",
                    file=str(path),
                    line=error.first_line,
                    column=error.first_column,
                    address=str(error.key),
                ),
            ),
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


def key_marks(path, *, text=None):
    """The position of every key and every sequence item of the YAML file at
    `path`, or of `text` read in its place, by its path in the document: a
    mapping from the tuple of the keys and sequence indices that lead to it
    to `(line, column)`, counted from one, read from the node marks of the
    composed document; the first mark where a key stands twice. Empty where
    the file is missing or the text does not compose, since the reader of
    the file refuses it."""
    try:
        if text is None:
            with open(path, encoding="utf-8") as stream:
                root = yaml.compose(stream, Loader=TagPreservingLoader)
        else:
            root = yaml.compose(text, Loader=TagPreservingLoader)
    except (OSError, yaml.YAMLError):
        return {}
    found = {}
    pending = [((), root)]
    while pending:
        prefix, node = pending.pop()
        if isinstance(node, yaml.MappingNode):
            for key_node, value_node in node.value:
                key = key_node.value if isinstance(key_node, yaml.ScalarNode) else None
                found.setdefault(
                    prefix + (key,), (key_node.start_mark.line + 1, key_node.start_mark.column + 1)
                )
                pending.append((prefix + (key,), value_node))
        elif isinstance(node, yaml.SequenceNode):
            for index, item in enumerate(node.value):
                found[prefix + (index,)] = (item.start_mark.line + 1, item.start_mark.column + 1)
                pending.append((prefix + (index,), item))
    return found


def settings_key_positions(paths):
    """The position of each setting's key in the settings files `paths`, read
    in order, a later file's key replacing an earlier file's as a later value
    replaces an earlier one: a mapping from the setting's name to `(file,
    line, column)`, read from the node marks of each file (`key_marks`) at
    the level `load_settings` reads the settings from, `settings` in the
    nested form, `calibration` then `settings` in the split form of a
    calibration file, and the top level in the flat form."""
    found = {}
    for path in paths:
        marks = key_marks(path)
        level = (
            ("settings",)
            if ("settings",) in marks
            else ("calibration", "settings")
            if ("calibration", "settings") in marks
            else ()
        )
        for key_path, (line, column) in marks.items():
            if len(key_path) == len(level) + 1 and key_path[:-1] == level:
                found[key_path[-1]] = (str(path), line, column)
    return found


class DuplicateKey(ValueError):
    """A mapping key written twice in a YAML document: `key`; `line` and
    `column` of the second writing; `first_line` and `first_column` of the
    first; which `read_yaml_mapping` refuses as a `FactoryError`."""

    def __init__(self, key, line, column, first_line, first_column):
        self.key, self.line, self.column = key, line, column
        self.first_line, self.first_column = first_line, first_column
        super().__init__(f"the key {key!r} is written twice, the second time at line {line}")


class TagPreservingLoader(yaml.SafeLoader):
    """A SafeLoader that keeps every `!tag` as `{"__yaml_tag__": tag, ...}`,
    reads the YAML keys `on` and `off` as those words, refuses a mapping key
    written twice with `DuplicateKey`, and ends a tag at a flow indicator
    inside a flow collection, as YAML 1.2 does (`scan_tag`)."""

    def scan_tag(self):
        """The token of a tag. Inside a flow collection, a tag `!<name>`
        followed directly by a comma or a closing bracket ends before it, as
        YAML 1.2 reads a tag (its `ns-tag-char` excludes the flow
        indicators), so that `{grid: !Cartesian, orders: {a: n_a}}` reads
        `!Cartesian` as the tag of an empty value (AMD-MB-003 §1); the
        scanner of PyYAML, which follows YAML 1.1 here, reads `Cartesian,` as
        the tag and refuses the text. The name is read over the letters, the
        digits and the characters `-;/?:@&=+$_.~*'()`; a tag that holds any
        other character, `%` and `!` among them, or that another character
        follows, is scanned by PyYAML's scanner."""
        if self.flow_level:
            length = 1
            ch = self.peek(length)
            while ch.isascii() and (ch.isalnum() or ch in "-;/?:@&=+$_.~*'()"):
                length += 1
                ch = self.peek(length)
            if length > 1 and ch in ",]}":
                start_mark = self.get_mark()
                suffix = self.prefix(length)[1:]
                self.forward(length)
                return yaml.tokens.TagToken(("!", suffix), start_mark, self.get_mark())
        return super().scan_tag()

    def construct_mapping(self, node, deep=False):
        """A YAML mapping, its keys `on` and `off` read as those words; a key
        written twice is refused as `DuplicateKey`, and a key that is no
        scalar as a `ValueError`."""
        first = {}
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self._mapping_key(key_node, deep)
            mark = (key_node.start_mark.line + 1, key_node.start_mark.column + 1)
            try:
                duplicate = key in first
            except TypeError as error:
                raise ValueError("a mapping key must be a scalar value") from error
            if duplicate:
                raise DuplicateKey(key, *mark, *first[key])
            first[key] = mark
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
