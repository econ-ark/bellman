"""The entries of a model's YAML files, read and edited as text: the
recipe, the trellis file and the period files, and the calibration, settings
and methods files they name.

An entry is reached by its address, written as the factory's refusals write
one, keys joined by "." and indices in brackets, `stages.cons.methods.all[0]`
or `periods[0].connectors[0]`, a key that holds a "." or a bracket written in
quotes, `periods[0].stages['cons']`, or given as a sequence of keys and
indices. `entry_span` answers the lines and the columns at which the entry's
value is written, counted from one, the columns in code points, as a stage
file's spans count them; `entry_value` answers the value as the package's
reader of YAML files reads it (`stage.sources.TagPreservingLoader`), every
tag kept, the whole document for the empty address; `replace_entry` answers
the text with the characters of the entry's value alone replaced by a
string, within the value's quotes where it is quoted, or by a number, a
boolean or a tag, written plain, so that every comment, every other entry
and the layout stay as written and no parsed mapping is written back (the
model interface's specification 0.3, §3.2, and AMD-MI-002 §5);
`append_to_mapping` and `append_to_sequence` answer the text with one entry
added at the end of the mapping or the list at an address, every other
character kept as well; `insert_in_sequence` answers it with one item placed
before the item at an index of a list, and `split_entry` with an entry that
writes `repeat: n` written twice, its two repeats summing to n, every other
character kept again; `remove_from_sequence` and `remove_from_mapping`
answer it with one item of a list, or one key of a mapping, taken out, the
collection written `[]` or `{}` where its only entry goes; and `written_at`
moves an address of the expanded trellis, `periods[h]…` or
`inter_connectors[h]…`, to the file and the address at which a trellis
file, or the period file one of its entries names, writes it, the reverse
of the expansion of `loading.read_trellis_file`. `period_entries` answers,
for each period, the entry that writes it and the periods that entry
writes, and `connector_entry` the file, the address and the text of the
line a drag from an unjoined writing port of the trellis graph to a reading
port types.
The single-entry queries and writers refuse an absent address with a
KeyError naming the step, and unreadable YAML with a ValueError.
`written_spans` resolves several expanded addresses together, returning
the source path and span of each, or None where that source is unavailable.
"""

from __future__ import annotations

import json
import re
from collections import namedtuple
from pathlib import Path

import yaml

from bellman.factory.connections import (
    AUTHORED,
    INFERRED,
    _authored_connections,
    _connection_index,
    trellis_selection,
)
from bellman.factory.joins import _state_fields, unjoined_fields
from bellman.factory.loading import _text_path, period_and_repeat
from bellman.stage.sources import TagPreservingLoader

__all__ = [
    "EntrySpan",
    "entry_path",
    "entry_span",
    "entry_value",
    "replace_entry",
    "append_to_mapping",
    "append_to_sequence",
    "insert_in_sequence",
    "split_entry",
    "remove_from_sequence",
    "remove_from_mapping",
    "written_at",
    "written_spans",
    "period_entries",
    "ConnectorEntry",
    "connector_entry",
]

# one step of an address: an index in brackets, a key in quotes in brackets,
# or a key between dots
_STEP = re.compile(r"\[(\d+)\]|\['([^']*)'\]|\[\"([^\"]*)\"\]|([^.\[\]]+)")

# the tag a YAML composer gives a plain or quoted string
_STRING_TAG = "tag:yaml.org,2002:str"

# a key that an address writes in quotes
_QUOTED = re.compile(r"[.\[\]]")

# the refusal of a text nested deeper than the YAML reader can follow: its
# composer, and its constructor of a tagged value, call themselves once or
# more for each level of nesting, and stop at the interpreter's recursion
# limit
_TOO_DEEP = "the text does not read as YAML: it is nested deeper than the reader can follow"

# a line break as the YAML reader counts lines, "\r\n" counted once
_LINE_BREAK = re.compile(r"\r\n|[\r\n\x85\u2028\u2029]")

# the line breaks at the end of a block scalar, with the spaces of the blank
# lines among them
_TRAILING_BREAKS = re.compile(r"(?:[\r\n\x85\u2028\u2029][ \t]*)+\Z")


class EntrySpan(namedtuple("EntrySpan", "line column end_line end_column")):
    """Where an entry's value is written in a YAML text: the line and the
    column of its first character and those just after its last, counted
    from one, the columns in code points."""

    __slots__ = ()


def entry_path(address):
    """The keys and the indices of an address, in order:
    `periods[0].connectors[0]` gives `("periods", 0, "connectors", 0)`; a
    sequence of keys and indices is answered as a tuple."""
    if not isinstance(address, str):
        return tuple(address)
    return tuple(
        int(index) if index else single or double or key
        for index, single, double, key in _STEP.findall(address)
    )


def _address(path):
    """An address written from its keys and indices, keys joined by "." and
    indices in brackets, a key that holds a "." or a bracket in quotes."""
    written = []
    for step in path:
        if isinstance(step, int):
            written.append(f"[{step}]")
        elif _QUOTED.search(step):
            written.append(f"['{step}']")
        else:
            written.append(("." if written else "") + step)
    return "".join(written)


def _composed(text):
    """The node tree of a YAML text as the package's reader composes it; a
    text that does not read is refused with a ValueError, and so is a text
    nested deeper than the reader can follow."""
    try:
        return yaml.compose(text, Loader=TagPreservingLoader)
    except yaml.YAMLError as error:
        raise ValueError(f"the text does not read as YAML: {error}") from None
    except RecursionError:
        raise ValueError(_TOO_DEEP) from None


def _node_at(text, address):
    """The node of the value at `address` in a YAML text: a key of a mapping,
    an index of a sequence; a scalar stands for a list of itself at index
    0, as the recipe's reader takes a list written as one name. A step the
    text does not hold is refused with a KeyError, and a text that does not
    read, or is nested deeper than the reader can follow, with a ValueError
    (`_composed`)."""
    return _node_in(_composed(text), address)


def _node_in(node, address):
    """The value at `address` in a composed YAML document."""
    for step in entry_path(address):
        if isinstance(step, int):
            if isinstance(node, yaml.ScalarNode) and step == 0:
                continue
            if not isinstance(node, yaml.SequenceNode) or step >= len(node.value):
                raise KeyError(f"the file writes no entry [{step}] at {address!r}")
            node = node.value[step]
            continue
        found = (
            [
                value
                for key, value in node.value
                if isinstance(key, yaml.ScalarNode) and key.value == step
            ]
            if isinstance(node, yaml.MappingNode)
            else []
        )
        if not found:
            raise KeyError(f"the file writes no key {step!r} at {address!r}")
        node = found[0]
    if node is None:
        raise KeyError("the file holds no document")
    return node


def _value_end(node, text):
    """The index in `text` just after the last character of the value of
    `node`: a block mapping or a block sequence ends where its last item
    ends, a block scalar, written after "|" or ">", before its trailing line
    breaks, and every other node, a plain or quoted scalar, a flow
    collection or an empty value, where the YAML composer ends it. The
    composer ends a block collection at the next token, after the comments
    that follow it, and a block scalar after its trailing line breaks."""
    # the composer gives a block collection the flow style False, and a
    # sequence written at its key's indentation the flow style None
    if isinstance(node, yaml.MappingNode) and not node.flow_style and node.value:
        return _value_end(node.value[-1][1], text)
    if isinstance(node, yaml.SequenceNode) and not node.flow_style and node.value:
        return _value_end(node.value[-1], text)
    if isinstance(node, yaml.ScalarNode) and node.style in ("|", ">"):
        breaks = _TRAILING_BREAKS.search(text, node.start_mark.index, node.end_mark.index)
        if breaks:
            return breaks.start()
    return node.end_mark.index


def entry_span(text, address):
    """The `EntrySpan` of the value at `address` in a YAML text. A block
    mapping or a block sequence ends where its last item ends, and a block
    scalar before its trailing line breaks, so that no comment after the
    value stands in its span."""
    return _span_of(_node_at(text, address), text)


def _span_of(node, text):
    """The span of a composed value in its source text."""
    end = _value_end(node, text)
    breaks = list(_LINE_BREAK.finditer(text, 0, end))
    line_start = breaks[-1].end() if breaks else 0
    # the YAML reader counts no byte order mark in a column
    column = end - line_start - text.count("\ufeff", line_start, end)
    return EntrySpan(
        node.start_mark.line + 1, node.start_mark.column + 1, len(breaks) + 1, column + 1
    )


def entry_value(text, address=()):
    """The value at `address` in a YAML text as the package's reader of YAML
    files reads it: mappings, lists and scalars, every tag kept as
    `{"__yaml_tag__": tag, …}`, a key written twice refused; the whole
    document for the empty address, its tag `!trellis` or `!period` kept
    beside its keys. A text that does not read as YAML is refused with a
    ValueError, and so are a text nested deeper than the reader can follow
    and a text with a value that the reader cannot build under its core
    tag, `!!bool abc`, `!!int ''`, `!!timestamp abc`, `!!set [1]` or a
    float written in base 60 with 175 parts or more, `1:0:…:0.`, for which
    the reader raises a KeyError, an IndexError, an AttributeError, a
    TypeError or an OverflowError rather than a YAML error."""
    try:
        value = yaml.load(text, Loader=TagPreservingLoader)
    except yaml.YAMLError as error:
        raise ValueError(f"the text does not read as YAML: {error}") from None
    except RecursionError:
        raise ValueError(_TOO_DEEP) from None
    except (KeyError, IndexError, AttributeError, TypeError, OverflowError) as error:
        # the classes that PyYAML's constructors of the core tags raise for a
        # value they cannot build; a ValueError of theirs, `!!int abc`,
        # propagates as it is
        raise ValueError(
            f"the text does not read as YAML: the reader cannot build one of its values "
            f"({type(error).__name__}: {error})"
        ) from None
    return _value_at(value, address)


def _value_at(value, address):
    """The value at `address` within `value`, a document as `entry_value`
    reads it: a key of a mapping, an index of a list; a scalar stands for a
    list of itself at index 0. A step the document does not hold is refused
    with a KeyError."""
    for step in entry_path(address):
        if isinstance(step, int):
            if not isinstance(value, (list, dict)) and step == 0:
                continue
            if not isinstance(value, list) or step >= len(value):
                raise KeyError(f"the file writes no entry [{step}] at {address!r}")
        elif not isinstance(value, dict) or step not in value:
            raise KeyError(f"the file writes no key {step!r} at {address!r}")
        value = value[step]
    return value


def _with_value(value, path, written):
    """A copy of a read document with the value at `path` replaced by
    `written`, which a replaced text must read as."""
    if not path:
        return written
    step, rest = path[0], path[1:]
    if isinstance(step, int) and not isinstance(value, list):
        return _with_value(value, rest, written)
    copy = list(value) if isinstance(value, list) else dict(value)
    copy[step] = _with_value(value[step], rest, written)
    return copy


def _quoted(written, quote):
    """The string `written` within the quotes `quote`, a single or a double
    quote, escaped as YAML reads it there: a single quote doubled within
    single quotes, and within double quotes the escapes JSON writes."""
    if quote == "'":
        return "'" + written.replace("'", "''") + "'"
    return json.dumps(written, ensure_ascii=False)


def _plain(written, address):
    """The text that writes the number, the boolean or the tag `written`
    plain, and the words for its kind, `("1.0e-05", "a number")`. A number,
    an int or a float, and a boolean are written as YAML writes them,
    `0.95`, `400`, `1.0e-05`, `true`; a tag, given as `entry_value` reads a
    tagged scalar, `{"__yaml_tag__": "egm", "value": ""}`, is written as "!"
    and the tag, followed by its value after one space where the value is
    not empty, `!egm` or `!path grid.yml`. A value of any other kind is
    refused with a ValueError naming `address` and the value's kind, `a
    list`, `a mapping`, `a tag on a collection` (a tag written on a list or
    a mapping) or `a value of type <name>`, and not the value's text, whose
    length for a list or a mapping read through aliases grows exponentially
    with the levels of aliases."""
    if isinstance(written, bool):
        return ("true" if written else "false"), "a boolean"
    if isinstance(written, (int, float)):
        # a subclass of int or of float, numpy's float64 among them, is written
        # as the number it equals, since YAML's writer refuses a type it does
        # not know
        number = float(written) if isinstance(written, float) else int(written)
        # the first line of the document YAML writes for the number alone; its
        # second line is the end marker "..."
        return yaml.safe_dump(number).split("\n", 1)[0], "a number"
    if (
        isinstance(written, dict)
        and set(written) == {"__yaml_tag__", "value"}
        and all(isinstance(part, str) for part in written.values())
    ):
        tag, value = written["__yaml_tag__"], written["value"]
        return (f"!{tag} {value}" if value else f"!{tag}"), "a tag"
    if isinstance(written, list):
        kind = "a list"
    elif isinstance(written, dict) and "__yaml_tag__" not in written:
        kind = "a mapping"
    elif isinstance(written, dict) and (
        set(written) != {"__yaml_tag__", "value"} or isinstance(written["value"], list)
    ):
        # `entry_value` reads a tag on a mapping with the mapping's keys, and
        # a tag on a list with the list under `value`
        kind = "a tag on a collection"
    else:
        kind = f"a value of type {type(written).__name__}"
    raise ValueError(
        f"{kind} is no string, int, float, boolean or tag, and cannot be written at {address!r}"
    )


def replace_entry(text, address, written):
    """The YAML text with the characters of the value at `address` replaced
    by `written`, a string, a number, a boolean or a tag. A string is
    written, where the value is a scalar written in single or double quotes,
    within the same quotes where it reads back there as that string;
    otherwise plain where it reads back as that string, and in double quotes
    where it does not. A number, an int or a float, and a boolean are
    written plain as YAML writes them, `0.95`, `400`, `1.0e-05`, `true`, and
    a tag, given as `entry_value` reads one, `{"__yaml_tag__": "egm",
    "value": ""}`, plain as "!" and the tag, followed by its value after one
    space where the value is not empty, `!egm` or `!path grid.yml`; each
    replaces the value's quotes as well where the value is quoted
    (AMD-MI-002 §5). Every other character of the text is kept, so that the
    comments, the other entries and the layout stay as written. The result
    is read back, and one in which the entry does not read as `written`, or
    another entry changed, is refused with a ValueError, as is a value of
    any other kind, among them a mapping that is no tag and a list. A
    result is read back only where its entry composes to a scalar that the
    form makes alone, the string `written` for a string, and for a number,
    a boolean or a tag a scalar that ends where the form ends, so that the
    reader builds no collection that a form writes, such as mappings merged
    through aliases, whose entries it copies once for each alias: a tag
    whose value holds a line break, or a comma within a flow collection,
    would write such mappings beside the entry. The value ends where
    `entry_span` ends it, a block mapping or a block sequence where its last
    item ends and a block scalar before its trailing line breaks, so that
    the comments after it stay as written."""
    node = _node_at(text, address)
    start, end = node.start_mark.index, _value_end(node, text)
    expected = _with_value(entry_value(text), entry_path(address), written)
    if not isinstance(written, str):
        form, kind = _plain(written, address)
        candidate = text[:start] + form + text[end:]
        try:
            # the form writes one scalar, which ends where the form ends; a
            # candidate whose entry composes to a collection, or to a scalar
            # that leaves the rest of the form to other entries, is not read
            replaced = _node_at(candidate, address)
            if (
                isinstance(replaced, yaml.ScalarNode)
                and replaced.end_mark.index == start + len(form)
                and entry_value(candidate) == expected
            ):
                return candidate
        except (KeyError, ValueError):
            pass
        raise ValueError(f"{form} cannot be written as {kind} at {address!r}")
    forms = [written, json.dumps(written, ensure_ascii=False)]
    if isinstance(node, yaml.ScalarNode) and node.style in ("'", '"'):
        # a quoted value keeps its quotes
        forms.insert(0, _quoted(written, node.style))
    for form in dict.fromkeys(forms):
        candidate = text[:start] + form + text[end:]
        try:
            replaced = _node_at(candidate, address)
            # a candidate whose entry composes to no such string is not read
            if (
                replaced.tag == _STRING_TAG
                and replaced.value == written
                and entry_value(candidate) == expected
            ):
                return candidate
        except (KeyError, ValueError):
            continue
    raise ValueError(f"{written!r} cannot be written as a string at {address!r}")


def _shape(node, within=()):
    """What the node `node` composes to, its tags and its scalar values in
    nested tuples, without its styles and its positions. A node met again
    inside itself through an alias answers `("recursive",)`; None, which an
    empty text composes to, answers None."""
    if node is None:
        return None
    if any(node is held for held in within):
        return ("recursive",)
    if isinstance(node, yaml.ScalarNode):
        return (node.tag, node.value)
    within = (*within, node)
    if isinstance(node, yaml.SequenceNode):
        return (node.tag, tuple(_shape(item, within) for item in node.value))
    pairs = tuple((_shape(key, within), _shape(value, within)) for key, value in node.value)
    return (node.tag, pairs)


def _entries(node):
    """The entries of the collection `node` by their shapes (`_shape`): for
    a mapping, each key paired with its value; for a list, each item."""
    if isinstance(node, yaml.MappingNode):
        return [(_shape(key), _shape(value)) for key, value in node.value]
    return [_shape(item) for item in node.value]


def _with_line_after(text, number, line):
    """`text` with `line` on a line of its own after its line `number`,
    counted from one as `entry_span` counts lines, so that a comment ending
    that line stays on it. The new line ends as that line does; after a last
    line that has no line ending, it ends with a carriage return and a line
    feed where another line of the text ends so, and with a line feed
    otherwise."""
    breaks = list(_LINE_BREAK.finditer(text))
    if number <= len(breaks):
        after = breaks[number - 1]
        return text[: after.end()] + line + after.group() + text[after.end() :]
    newline = "\r\n" if "\r\n" in text else "\n"
    return text + newline + line + newline


def _appended(text, address, node, entry):
    """`text` with `entry` written as the last entry of the collection
    `node`, which stands at `address`: in flow style before its closing
    brace or bracket, after a comma where it holds an entry; in block style
    on a line of its own after the line on which `entry_span` ends the
    collection, at the column at which `entry_span` begins it, a list's
    entry after a dash."""
    if node.flow_style:
        # the composer ends a flow collection just after its closing brace or
        # bracket
        close = node.end_mark.index - 1
        return text[:close] + (", " if node.value else "") + entry + text[close:]
    span = entry_span(text, address)
    dash = "- " if isinstance(node, yaml.SequenceNode) else ""
    return _with_line_after(text, span.end_line, " " * (span.column - 1) + dash + entry)


def _not_extendable(address):
    """The ValueError of a text writer whose result the file's layout at
    `address` does not admit, naming the address."""
    return ValueError(
        f"the layout of the file at {_address(entry_path(address))} cannot be extended "
        "as text; add the entry there by hand"
    )


def _checked(new, address, kind, former, is_new, at=None):
    """`new`, the text a writer made, where the collection at `address` is
    of the node class `kind` and holds the entries `former`, in order, and
    one entry more for which `is_new` answers True: after them, or at the
    index `at` among them where `at` is given. Otherwise, and where `new`
    does not read as YAML, a ValueError that names the address and says
    that the file's layout there cannot be extended as text."""
    try:
        node = _node_at(new, address)
    except (KeyError, ValueError):
        node = None
    at = len(former) if at is None else at
    if isinstance(node, kind) and len(node.value) == len(former) + 1:
        entries = _entries(node)
        if entries[:at] + entries[at + 1 :] == former and is_new(node.value[at]):
            return new
    raise _not_extendable(address)


def append_to_mapping(text, address, key, value):
    """The YAML text with the entry `key: value` added at the end of the
    mapping at `address`: in block style on a line of its own after the
    mapping's last entry, at the indentation of its keys; in flow style
    before its closing brace, after a comma where the mapping holds an
    entry. `value` is written as given, and every other character of the
    text is kept, so that the comments, the other entries and the layout
    stay as written. The mapping ends where `entry_span` ends it, at its
    last entry's last character; in block style the new key stands at the
    column at which `entry_span` begins the mapping, the indentation of its
    keys unless a tag or an anchor is written before them. A key the
    mapping holds, and an address at which no mapping stands, are refused
    with a ValueError. The result is composed by the package's reader of
    YAML files, and the mapping at `address` must hold its former entries,
    in order, and then the key `key`; otherwise, and where the result does
    not read, the append is refused with a ValueError that names the
    address, the file's layout there being one that cannot be extended as
    text."""
    node = _node_at(text, address)
    written = _address(entry_path(address))
    if not isinstance(node, yaml.MappingNode):
        raise ValueError(f"the entry {written} is no mapping")
    if any(isinstance(name, yaml.ScalarNode) and name.value == key for name, _ in node.value):
        raise ValueError(f"the mapping {written} holds the key {key!r} already")
    return _checked(
        _appended(text, address, node, f"{key}: {value}"),
        address,
        yaml.MappingNode,
        _entries(node),
        lambda pair: isinstance(pair[0], yaml.ScalarNode) and pair[0].value == key,
    )


def append_to_sequence(text, address, item):
    """The YAML text with `item` added at the end of the list at `address`:
    in block style `- item` on a line of its own after the list's last
    entry, at the column of its dashes; in flow style before its closing
    bracket, after a comma where the list holds an item. `item` is written
    as given, and every other character of the text is kept. The list ends
    where `entry_span` ends it, at its last item's last character; in block
    style the new dash stands at the column at which `entry_span` begins
    the list, that of its dashes unless a tag or an anchor is written
    before them. An address at which no list stands, and an `item` that
    does not read as YAML, are refused with a ValueError. The result is
    composed by the package's reader of YAML files, and the list at
    `address` must hold its former items, in order, and then an item that
    composes to what `item` composes to alone; otherwise, and where the
    result does not read, the append is refused with a ValueError that
    names the address, the file's layout there being one that cannot be
    extended as text."""
    node = _node_at(text, address)
    if not isinstance(node, yaml.SequenceNode):
        raise ValueError(f"the entry {_address(entry_path(address))} is no list")
    alone = _shape(_composed(item))
    return _checked(
        _appended(text, address, node, item),
        address,
        yaml.SequenceNode,
        _entries(node),
        lambda last: _shape(last) == alone,
    )


def _dash_line(text, address, sequence, index):
    """Where the line that holds the dash of item `index` of the block list
    `sequence`, which stands at `address`, begins in `text`, and the spaces
    written before that dash. The dash is the last "-" before the item and
    after the end of the item before it, or after the list's start for the
    first item. Where no dash stands there, and where the dash is not the
    first character of its line other than spaces, as in a list nested in a
    list's item, the ValueError of a layout that cannot be extended as text
    is raised."""
    after = (
        sequence.start_mark.index if index == 0 else _value_end(sequence.value[index - 1], text)
    )
    dash = text.rfind("-", after, sequence.value[index].start_mark.index)
    start = max(text.rfind(mark, 0, dash) for mark in "\r\n\x85\u2028\u2029") + 1
    if dash < 0 or text[start:dash].strip(" "):
        raise _not_extendable(address)
    return start, text[start:dash]


def _newline(text, index):
    """The line break that ends the line of `text` that holds the index
    `index`; where that line has none, as the last line may not, a carriage
    return and a line feed where another line of the text ends so, and a
    line feed otherwise, as `_with_line_after` writes one."""
    found = _LINE_BREAK.search(text, index)
    if found:
        return found.group()
    return "\r\n" if "\r\n" in text else "\n"


def insert_in_sequence(text, address, index, item):
    """The YAML text with `item` placed before the item at `index` of the
    list at `address`: in block style `- item` on a line of its own just
    before the line that holds that item's dash, at the dash's column, the
    new line ending as that line ends; in flow style just before that item,
    followed by a comma and a space. An `index` equal to the list's length
    appends `item` as `append_to_sequence` does. It is one of the two
    writers model interface spec 0.4 §3.6 adds for a period added between
    two periods. `item` is written as given, and every other character of
    the text is kept, so that a comment ending the line of the item before
    stays on it and a comment on a line of its own stays before the new
    line. An address at which no list stands, an `index` that is no whole
    number from zero to the list's length, and an `item` that does not
    read as YAML are refused with a ValueError, and an address the text
    does not hold with a KeyError. The result is composed by the package's
    reader of YAML files, and the list at `address` must hold its former
    items, in order, with an item at `index` that composes to what `item`
    composes to alone; otherwise, and where the result does not read or the
    item's dash is not the first character of its line, the insertion is
    refused with a ValueError that names the address, the file's layout
    there being one that cannot be extended as text."""
    node = _node_at(text, address)
    written = _address(entry_path(address))
    if not isinstance(node, yaml.SequenceNode):
        raise ValueError(f"the entry {written} is no list")
    length = len(node.value)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= length:
        raise ValueError(f"index {index!r} lies outside the list {written} of length {length}")
    if index == length:
        return append_to_sequence(text, address, item)
    alone = _shape(_composed(item))
    if node.flow_style:
        start = node.value[index].start_mark.index
        new = text[:start] + item + ", " + text[start:]
    else:
        start, spaces = _dash_line(text, address, node, index)
        new = text[:start] + spaces + "- " + item + _newline(text, start) + text[start:]
    return _checked(
        new,
        address,
        yaml.SequenceNode,
        _entries(node),
        lambda placed: _shape(placed) == alone,
        at=index,
    )


def _repeated(shape, count):
    """The shape (`_shape`) of the mapping whose shape is `shape` with the
    value of its key `repeat` the integer `count`, written plain, as
    `replace_entry` writes it."""
    tag, pairs = shape
    number = _shape(_composed(str(count)))
    return (
        tag,
        tuple((key, number if key == (_STRING_TAG, "repeat") else value) for key, value in pairs),
    )


def split_entry(text, address, at):
    """The YAML text with the entry at `address`, an item of a list that
    writes `repeat: n`, written twice in its place, the first time with
    `repeat: at` and the second with `repeat: n - at`, so that the two
    entries stand for the periods the entry stood for. It is the writer
    that model interface spec 0.4 §3.6 names for a period added between two
    periods that one entry writes. In a block list the lines of the entry,
    from the line of its dash to the end of its value, are written again
    before that line, the comments within the entry with them, and a
    comment that ends the entry's last line stays with the second entry;
    in a flow list the entry's characters are written again before it,
    followed by a comma and a space. Only the two values of `repeat` are
    then replaced, by `replace_entry`, and every other character of the
    text is kept. An
    address that names no item of a list, an address whose list holds no
    item at that index, an entry that writes no integer `repeat`, as an
    entry that takes its repeat from the period file it names, and an `at`
    that is no whole number from one to `n - 1` are refused with a
    ValueError, and an address the text does not hold with a KeyError. The
    result is composed by the package's reader of YAML files, and the list
    must hold its former items, in order, with the entry's place taken by
    the two entries, each composing to the entry with its own `repeat`;
    otherwise, and where the result does not read or the entry's dash is
    not the first character of its line, the split is refused with a
    ValueError that names the list's address, the file's layout there
    being one that cannot be extended as text."""
    path = entry_path(address)
    if not path or not isinstance(path[-1], int):
        raise ValueError(f"the entry {_address(path)} is no item of a list")
    within, index = path[:-1], path[-1]
    sequence = _node_at(text, within)
    listed = _address(within)
    if not isinstance(sequence, yaml.SequenceNode):
        raise ValueError(f"the entry {listed} is no list")
    length = len(sequence.value)
    if not 0 <= index < length:
        raise ValueError(f"index {index} lies outside the list {listed} of length {length}")
    entry = entry_value(text, path)
    repeat = entry.get("repeat") if isinstance(entry, dict) else None
    if isinstance(repeat, bool) or not isinstance(repeat, int):
        raise ValueError(f"the entry {_address(path)} writes no integer repeat to split")
    if isinstance(at, bool) or not isinstance(at, int) or not 1 <= at < repeat:
        raise ValueError(
            f"the entry {_address(path)} writes repeat: {repeat}, which cannot be split at "
            f"{at!r}: each of the two entries must repeat a whole number of times, at least once"
        )
    node = sequence.value[index]
    end = _value_end(node, text)
    if sequence.flow_style:
        start = node.start_mark.index
        doubled = text[:start] + text[start:end] + ", " + text[start:]
    else:
        start, _ = _dash_line(text, within, sequence, index)
        doubled = text[:start] + text[start:end] + _newline(text, end) + text[start:]
    try:
        first = replace_entry(doubled, (*within, index, "repeat"), at)
        new = replace_entry(first, (*within, index + 1, "repeat"), repeat - at)
    except (KeyError, ValueError):
        raise _not_extendable(within) from None
    shape, former = _shape(node), _entries(sequence)
    return _checked(
        new,
        within,
        yaml.SequenceNode,
        [*former[:index], _repeated(shape, at), *former[index + 1 :]],
        lambda second: _shape(second) == _repeated(shape, repeat - at),
        at=index + 1,
    )


def _not_removable(address):
    """The ValueError of a removal whose result the file's layout at
    `address` does not admit, naming the address."""
    return ValueError(
        f"the layout of the file at {_address(entry_path(address))} does not admit the "
        "removal as text; remove the entry there by hand"
    )


def _line_start(text, index):
    """The index in `text` at which the line that holds the index `index`
    begins."""
    return max(text.rfind(mark, 0, index) for mark in "\r\n\x85  ") + 1


def _line_end(text, index):
    """The index in `text` just after the line break that ends the line that
    holds the index `index`; the end of the text where that line has none."""
    found = _LINE_BREAK.search(text, index)
    return found.end() if found else len(text)


def _with_comment_lines(text, start):
    """`start`, the index at which a line of `text` begins, moved back over
    the lines just above it that hold a comment alone, so that a removal of
    the entry written from `start` takes those lines with it; a blank line,
    or a line that holds anything but spaces and a comment, ends them."""
    while start > 0:
        above = _line_start(text, start - 1)
        if not text[above:start].strip(" \t\r\n\x85  ").startswith("#"):
            break
        start = above
    return start


def _removed_checked(new, address, kind, former, at, tag):
    """`new`, the text a removal made, where the collection at `address` is
    of the node class `kind`, keeps the tag `tag` and holds the entries
    `former`, in order, but the one at the index `at`. Otherwise, and where
    `new` does not read as YAML, the ValueError of a layout that does not
    admit the removal (`_not_removable`)."""
    try:
        node = _node_at(new, address)
    except (KeyError, ValueError):
        node = None
    if isinstance(node, kind) and node.tag == tag:
        if _entries(node) == former[:at] + former[at + 1 :]:
            return new
    raise _not_removable(address)


def _without_entry(text, address, node, at, starts, ends):
    """`text` with the entry `at` of the collection `node`, which stands at
    `address`, taken out: `starts` and `ends` give, for each entry, where it
    begins and where its value ends. The only entry is replaced, with the
    collection, by `[]` or `{}`, the comments around it kept. In flow style
    an entry before the last goes with the comma and the spaces after it,
    and the last with the comma before it. In block style the lines from
    the line on which the entry begins to the line on which its value ends
    go, with the comment ending that last line and, for an entry after the
    first, the lines just above it that hold a comment alone; an entry that
    does not begin its line, the first key of a mapping written on its
    list's dash, goes with everything up to the next key, and a later entry
    that does not begin its line is refused (`_not_removable`)."""
    if len(starts) == 1:
        empty = "[]" if isinstance(node, yaml.SequenceNode) else "{}"
        return text[: node.start_mark.index] + empty + text[_value_end(node, text) :]
    if node.flow_style:
        if at + 1 < len(starts):
            return text[: starts[at]] + text[starts[at + 1] :]
        return text[: ends[at - 1]] + text[ends[at] :]
    line = _line_start(text, starts[at])
    if text[line : starts[at]].strip(" "):
        if at != 0:
            raise _not_removable(address)
        return text[: starts[0]] + text[starts[1] :]
    start = _with_comment_lines(text, line) if at > 0 else line
    return text[:start] + text[_line_end(text, ends[at]) :]


def remove_from_sequence(text, address, index):
    """The YAML text with the item at `index` of the list at `address` taken
    out, every other character kept, so that the comments, the other entries
    and the layout stay as written. In block style the lines of the item go,
    from the line of its dash to the line on which its value ends, with the
    comment ending that line and, for an item after the first, the lines
    just above it that hold a comment alone, which describe it; in flow
    style the item goes with the comma that separates it from the next item,
    or, for the last item, from the item before it. Where the list's only
    item goes, the list is written `[]` in its place, the comments around it
    kept. It is one of the two writers by which a join of the trellis graph
    is removed (unit J's decisions J-D33 and J-D34). An address at which no
    list stands and an `index` that is no whole number within the list are
    refused with a ValueError, and an address the text does not hold with a
    KeyError. The result is composed by the package's reader of YAML files,
    and the list at `address` must hold its former items, in order, but the
    one at `index`; otherwise, and where the result does not read or the
    item's dash is not the first character of its line, the removal is
    refused with a ValueError that names the address, the file's layout
    there being one that does not admit the removal as text."""
    node = _node_at(text, address)
    written = _address(entry_path(address))
    if not isinstance(node, yaml.SequenceNode):
        raise ValueError(f"the entry {written} is no list")
    length = len(node.value)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < length:
        raise ValueError(f"the list {written} of length {length} holds no item {index!r}")
    if node.flow_style or length == 1:
        starts = [item.start_mark.index for item in node.value]
    else:
        try:
            starts = [_dash_line(text, address, node, at)[0] for at in range(length)]
        except ValueError:
            raise _not_removable(address) from None
        # the dash begins its line, so that the line's start is the item's
        starts = [start + len(text[start:]) - len(text[start:].lstrip(" ")) for start in starts]
    ends = [_value_end(item, text) for item in node.value]
    new = _without_entry(text, address, node, index, starts, ends)
    return _removed_checked(new, address, yaml.SequenceNode, _entries(node), index, node.tag)


def remove_from_mapping(text, address, key):
    """The YAML text with the key `key` of the mapping at `address` taken
    out with its value, every other character kept. In block style the
    lines of the entry go, from the key's line to the line on which its
    value ends, with the comment ending that line and, for a key after the
    first, the lines just above it that hold a comment alone; the first key
    of a mapping written on a list's dash, `- a: k`, goes with everything up
    to the next key, which then stands on the dash. In flow style the entry
    goes with the comma that separates it from the next entry, or, for the
    last entry, from the entry before it. Where the mapping's only key goes,
    the mapping is written `{}` in its place, the comments around it kept,
    so that an inter-period mapping left empty still stands for its pairs.
    It is one of the two writers by which a join of the trellis graph is
    removed (unit J's decisions J-D33 and J-D34). An address at which no
    mapping stands and a key the mapping does not hold are refused with a
    ValueError, and an address the text does not hold with a KeyError. The
    result is composed by the package's reader of YAML files, and the
    mapping at `address` must hold its former entries, in order, but the
    one of `key`; otherwise, and where the result does not read or a key
    after the first does not begin its line, the removal is refused with a
    ValueError that names the address, the file's layout there being one
    that does not admit the removal as text."""
    node = _node_at(text, address)
    written = _address(entry_path(address))
    if not isinstance(node, yaml.MappingNode):
        raise ValueError(f"the entry {written} is no mapping")
    names = [name.value if isinstance(name, yaml.ScalarNode) else None for name, _ in node.value]
    if key not in names:
        raise ValueError(f"the mapping {written} holds no key {key!r}")
    at = names.index(key)
    starts = [name.start_mark.index for name, _ in node.value]
    ends = [_value_end(value, text) for _, value in node.value]
    new = _without_entry(text, address, node, at, starts, ends)
    return _removed_checked(new, address, yaml.MappingNode, _entries(node), at, node.tag)


def written_at(file, address, texts=None):
    """The file and the address at which the trellis file `file` writes the
    part of its expanded trellis at `address`, the periods and the adjacent
    pairs counted as `loading.read_trellis_file` counts them. `texts` maps a
    file's resolved path to the text read in its place, for the trellis file
    and the period files, as the loader reads them (model interface spec 0.4
    §3.1).

    Under `periods[h]`, the answer is the entry of the file's `periods` list
    that writes period `h`: `periods[n]` in `file`, or, where that entry
    names a period file under `template` and does not itself write the next
    key of the address, the period file, with `periods[h]` removed. Each
    entry stands for as many periods as the loader repeats it, the count
    `loading.period_and_repeat` answers: the entry's own `repeat`, else the
    `repeat` written in the period file it names, else one. A period outside
    the expanded periods is refused with a KeyError naming the file.

    Under `inter_connectors[h]`, `h` is one of the adjacent pairs of the
    expanded periods, whose number is the number of periods less one. A
    file that writes one mapping, which stands for every pair, answers
    `inter_connectors[0]`, and a file that writes one mapping for each pair
    answers `inter_connectors[h]`. An `inter_connectors[h]` is refused with
    a KeyError naming the file where `h` lies outside the pairs; where the
    file writes no mapping, since the empty mapping the loader reads for
    each pair is written in no file; and where the file writes a list of
    another length, which the loader refuses.

    Any other address is answered in `file` as given. The answer is `(path,
    address)`, the path a string. A refusal of the shape of an entry is the
    loader's own, a `FactoryError`, which is a ValueError, naming the entry
    by its position in the file."""
    file = Path(file)
    path = entry_path(address)
    if not _expanded_address(path):
        return str(file), _address(path)
    document, repeats = _trellis_read(file, texts)
    return _written_in(file, document, repeats, path)


def _expanded_address(path):
    """Whether `path` names an expanded period or inter-period mapping."""
    return (len(path) >= 2 and path[0] in ("periods", "inter_connectors")
            and isinstance(path[1], int))


def written_spans(file, addresses, texts=None):
    """The source of each expanded address, in order, as `(path, EntrySpan)`.

    Addresses are resolved as `written_at` resolves them, and spans as
    `entry_span` measures them. A missing address, an unreadable source or
    a source whose shape the loader refuses answers None at that position;
    other positions remain available. `texts` supplies current unsaved text
    by resolved path, as for `written_at`.

    The trellis and its authored period entries are read once to resolve
    expansion. Each distinct source is composed once for all its spans.
    Nothing is retained between calls.
    """
    file = Path(file)
    unavailable = (OSError, ValueError, KeyError, TypeError, AttributeError)
    paths = []
    for address in addresses:
        try:
            paths.append(None if address is None else entry_path(address))
        except unavailable:
            paths.append(None)
    reading = None
    if any(path is not None and _expanded_address(path) for path in paths):
        try:
            reading = _trellis_read(file, texts)
        except unavailable:
            pass
    sources = {}
    found = []
    for path in paths:
        if path is None or (_expanded_address(path) and reading is None):
            found.append(None)
            continue
        try:
            source, address = (_written_in(file, *reading, path) if _expanded_address(path)
                               else (str(file), _address(path)))
            resolved = Path(source).resolve()
            if resolved not in sources:
                try:
                    text = _text(source, texts)
                    sources[resolved] = text, _composed(text)
                except unavailable:
                    sources[resolved] = None
            if sources[resolved] is None:
                found.append(None)
                continue
            text, document = sources[resolved]
            found.append((source, _span_of(_node_in(document, address), text)))
        except unavailable:
            found.append(None)
    return tuple(found)


def _text(path, texts):
    """The text `texts` holds for the resolved path of `path`, else the text
    of the file at `path` (model interface spec 0.4 §3.1)."""
    held = _text_path(path, texts)
    return Path(path).read_text(encoding="utf-8") if held is None else texts[held]


def _trellis_read(file, texts):
    """The document the trellis file `file` writes, read once, from the text
    `texts` holds for it or from the file, and the number of periods each
    entry of its `periods` list stands for, by the loader's own rule
    (`loading.period_and_repeat`)."""
    document = entry_value(_text(file, texts))
    repeats = [
        period_and_repeat(entry, file.parent, file, f"periods[{number}]", texts)[1]
        for number, entry in enumerate(document.get("periods") or [])
    ]
    return document, repeats


def _written_in(file, document, repeats, path):
    """`written_at`'s answer for `path`, an address under `periods[h]` or
    `inter_connectors[h]` given as its keys and indices, in the trellis file
    `file`, whose document and whose entries' numbers of periods
    `_trellis_read` answers."""
    entries = document.get("periods") or []
    if path[0] == "inter_connectors":
        mappings = document.get("inter_connectors") or []
        pairs = max(sum(repeats) - 1, 0)
        # the loader reads the file's own mappings only where the file writes
        # one mapping, standing for every pair, or one for each pair
        if not 0 <= path[1] < pairs or len(mappings) not in (1, pairs):
            raise KeyError(f"{file.name} writes no inter-period mapping {path[1]}")
        index = 0 if len(mappings) == 1 else path[1]
        return str(file), _address(("inter_connectors", index, *path[2:]))
    start = 0
    for number, (entry, repeat) in enumerate(zip(entries, repeats)):
        if start <= path[1] < start + repeat:
            template = entry.get("template")
            if template is not None and (len(path) == 2 or path[2] not in entry):
                return str(file.parent / str(template)), _address(path[2:])
            return str(file), _address(("periods", number, *path[2:]))
        start += repeat
    raise KeyError(f"{file.name} writes no period {path[1]}")


def period_entries(file, texts=None):
    """For each period of the expanded trellis the trellis file `file`
    writes, in order, `(path, address, periods)`: the file that writes the
    period, the period file where the period's entry names one under
    `template` and the trellis file otherwise; the address of the period's
    entry in that file, `periods[n]` in the trellis file and the empty
    address in a period file, as `written_at` answers `periods[h]`; and
    every period, in order, whose entry stands at that file and address. The
    trellis file is read once, each entry's number of periods counted by the
    loader's own rule (`loading.period_and_repeat`); `texts` maps a file's
    resolved path to the text read in its place, as the loader reads it
    (model interface spec 0.4 §3.1, §3.5; unit J's brief, rule 3)."""
    file = Path(file)
    document, repeats = _trellis_read(file, texts)
    places = [_written_in(file, document, repeats, ("periods", h)) for h in range(sum(repeats))]
    return [
        (*place, tuple(h for h, other in enumerate(places) if other == place)) for place in places
    ]


class ConnectorEntry(namedtuple("ConnectorEntry", "file address periods text reason shared held")):
    """Where the line a drag from an unjoined writing port to a reading port
    types is written, as `connector_entry` answers it (model interface spec
    0.4 §3.1; unit J's decisions J-D4 and J-D42): `file`, the path of the
    file that writes the line, and `address`, the line's address in it, a
    mapping to which the line adds its key or a list to which it adds an
    item; `periods`, the indices of the periods the line reaches, in order;
    `text`, the line; `reason`, None where the line is admitted, else one
    of `name-shared`, `no-mapping`, `port-joined`, `not-adjacent` and
    `source-authored`;
    `shared`, the `(h, key)` of the stage occurrence that shares a dragged
    name, where one does; and `held`, where `shared` is given, `(perch,
    name, keys)`: the perch at which the
    occurrences of `periods[h]` hold that name, `cntn` for a continuation
    field and `arvl` for an arrival field, the name, and the key of each
    occurrence of the period that holds it there, `shared`'s key being the
    first of them other than the dragged occurrence's. Where the line is
    not admitted, `text` is the line that was not written; `file`,
    `address`, `periods` and `text` are None, or the empty tuple, where the
    query stopped before it found them."""

    __slots__ = ()


def connector_entry(trellis, writing, reading, texts=None, *, selection=None, replacing=()):
    """The `ConnectorEntry` of a drag from the writing port `writing`, a
    continuation state field, to the reading port `reading`, an arrival
    state field, of the forward trellis graph of `trellis`, an elaborated
    trellis whose provenance names its trellis file; each port is `(h, key,
    field)`, the period's index, the stage occurrence's key and the field's
    name. The rule is that of model interface spec 0.4 §3.1 and §3.3 and of
    AMD-COMP-001 §3. The ports are read through `joins.unjoined_fields`
    from the trellis's one selection of its connections
    (`connections.trellis_selection`), and the trellis file is read once,
    through `texts`, which maps a file's resolved path to the text read in
    its place, to reverse its expansion as `written_at` reverses it. No
    stage is constructed, and a drag the rule does not admit is answered as
    a fact, never raised (unit J's decision J-D4).

    `selection`, when supplied, belongs to this exact trellis version.
    `replacing` names inferred pairs from that selection whose arrows are
    being moved. Their writing ports may be reused by the new connector;
    authored pairs must first be removed from their source mapping. The
    caller checks compatibility on the proposed complete selection before
    writing the returned entry. A pair outside this selection, or an
    authored pair in `replacing`, raises ValueError.

    A reading port that stands neither in the writing port's period nor in
    the period after it in time, `periods[h - 1]`, or that stands on the
    writing port's own stage occurrence, is `not-adjacent`; a writing port
    that a pair already reads, since a continuation field joins one arrival
    field, and a reading port that is no arrival state field of the
    trellis, are `port-joined`. A reading port that pairs already reach
    takes a further source, an arrival field taking several sources within
    its period and from the period before (docs/Bellman-Sym/07-trellis.md
    §2; unit J's decisions J-D41 and J-D42).

    The line is the shortest spelling that resolves back to the dragged
    pair, and to that pair alone, in every period the entry it joins
    reaches: the spellings are tried in the order `a: b`, `S.a: b`, `a:
    T.b`, `S.a: T.b`, the stage key written before a field only where the
    bare name resolves to no use or to several there, and each is checked
    by resolving the authored entries against the selection's uses
    (`_round_trips`), so that the line written is the one the reader
    resolves; a stage key holding a dot is split at its final dot by the
    reader. Within one period, where pairs already reach the reading port
    and a connector of the period's list writes one of them, the line is a
    further key of that connector, the first such in the list: of the
    connector itself where it is flat, and of its `fields`, as the bare
    `a: b`, where it is keyed from the writing port's stage occurrence to
    the reading port's, so that an existing keyed group is kept and the
    count of mappings never changes. If none of those connectors can hold
    it, an authored connector between the same two stage occurrences is
    extended where its complete mapping resolves in every reached period.
    Otherwise the line, `{a: b}` or its
    qualified spelling, fills the first empty mapping of the `connectors`
    list `written_at` answers for `periods[h].connectors`, or is appended
    to that list where no mapping is empty, and it reaches every period
    whose connectors that list writes. Where neither the period's entry nor
    its period file writes a `connectors` list, the reason is `no-mapping`
    at the address of the entry (the plan's decision J-D25). `shared`
    names the first other occurrence of a reached period that holds a
    dragged name at the same perch, and `held` what it holds, the dragged
    period searched first.

    Between two periods, the line is the entry `a: b`, or its qualified
    spelling, of the inter-period mapping `written_at` answers for
    `inter_connectors[h - 1]`, and it reaches the periods of every adjacent
    pair that mapping joins, each pair resolved separately; where the
    trellis file writes no mapping, the reason is `no-mapping` at
    `inter_connectors`. The reason is `name-shared`, within a period or
    between two, where no spelling resolves to the dragged pair at every
    period or pair the entry reaches, as where another pair's periods hold
    other stage keys; `text` is then the fully qualified spelling that was
    not written. An existing source key is never replaced by extension:
    `source-authored` names its mapping even when its target is unresolved."""
    (h, key, field), (h2, key2, field2) = writing, reading
    if h2 not in (h, h - 1) or (h2 == h and key2 == key):
        return ConnectorEntry(None, None, (), None, "not-adjacent", None, None)
    selection = trellis_selection(trellis) if selection is None else selection
    replacing = tuple(replacing)
    if any(pair.origin != INFERRED or pair not in selection.pairs for pair in replacing):
        raise ValueError("each replacement must name an inferred pair of this selection")
    unjoined = unjoined_fields(trellis, selection)
    arrival = (h2, key2, field2)
    occupied = [pair for pair in selection.pairs
                if (pair.writing.h, pair.writing.key, pair.writing.field) == writing]
    released = bool(occupied) and all(pair in replacing for pair in occupied)
    if ((h, key, field) not in unjoined["writing"] and not released) or (
        arrival not in unjoined["reading"] and arrival not in unjoined["sources"]
    ):
        return ConnectorEntry(None, None, (), None, "port-joined", None, None)
    file = Path(trellis["provenance"]["trellis"]["path"])
    document, repeats = _trellis_read(file, texts)
    index = _connection_index(selection.uses, selection.value_uses)
    if h2 == h:
        sources = unjoined["sources"].get(arrival, ())
        group_sources = tuple(
            pair.source_address
            for pair in selection.pairs
            if pair.origin == AUTHORED
            and (pair.writing.h, pair.writing.key) == (h, key)
            and (pair.reading.h, pair.reading.key) == (h2, key2)
        )
        return _connector_within(
            trellis, index, file, document, repeats, writing, reading, texts,
            sources, group_sources,
        )
    return _entry_between(trellis, index, file, document, repeats, writing, reading)


def _sharing(holders, h, own, perch, name):
    """`[(shared, held)]`, the `ConnectorEntry` fields of the name `name`
    that the stage occurrences of `periods[h]` hold at `perch`, `holders`
    being their keys in order, where more than one holds it: `shared`, `(h,
    key)` of the first key other than `own`, the dragged occurrence's; and
    `held`, `(perch, name, keys)`. The list is empty where one occurrence
    holds the name alone."""
    if len(holders) < 2:
        return []
    other = next(held for held in holders if held != own)
    return [((h, other), (perch, name, tuple(holders)))]


def _spellings(key, field, key2, field2):
    """The spellings of a line from `field` of the stage `key` to `field2`
    of the stage `key2`, shortest first: bare, the writing stage's key
    written, the reading stage's key written, both written."""
    return (
        (field, field2),
        (f"{key}.{field}", field2),
        (field, f"{key2}.{field2}"),
        (f"{key}.{field}", f"{key2}.{field2}"),
    )


def _round_trips(periods, inter_connectors, index, addresses, writing, reading):
    """Whether the trellis with its `periods` and `inter_connectors`
    replaced, a line written into them, resolves the authored pair from
    `writing` to `reading`, as `(key, field)` each, at every address of
    `addresses`, `(p, hw, address)` per period or adjacent pair the entry
    reaches, `hw` the period of the writing use and `p` of the reading one:
    the reader resolves the line to the dragged pair, which it does at no
    endpoint that names no use or several. Whether the pair is compatible
    or its route complete is the selection's answer and no condition of
    the writing. `index` holds the unchanged eligible uses of the supplied
    selection."""
    pairs, _, _, _ = _authored_connections(periods, inter_connectors, index)
    return all(
        any(
            pair.origin == AUTHORED
            and pair.address == address
            and (pair.writing.h, pair.writing.key, pair.writing.field) == (hw, *writing)
            and (pair.reading.h, pair.reading.key, pair.reading.field) == (p, *reading)
            for pair in pairs
        )
        for p, hw, address in addresses
    )


def _connector_within(
    trellis, index, file, document, repeats, writing, reading, texts, sources=(), group_sources=()
):
    """`connector_entry`'s answer for a drag within one period, from
    `writing`, admitted as unjoined, to `reading`, unjoined or reached by
    the pairs whose entries `sources` names (`joins.unjoined_fields`);
    `file` is the trellis file, whose document and whose entries' numbers of
    periods `_trellis_read` answers, and `index` the eligible uses of the
    selection before the line. `group_sources` names authored mappings
    between the same two stages, tried after those reaching the arrival field.
    """
    (h, key, field), (_, key2, field2) = writing, reading
    place = _written_in(file, document, repeats, ("periods", h, "connectors"))
    periods = tuple(
        p
        for p in range(len(trellis["periods"]))
        if _written_in(file, document, repeats, ("periods", p, "connectors")) == place
    )
    found = []
    for p in (h, *(p for p in periods if p != h)):
        stages, where = trellis["periods"][p]["stages"], f"periods[{p}]"
        continuing = [k for k, name in _state_fields(stages, "cntn", where) if name == field]
        arriving = [k for k, name in _state_fields(stages, "arvl", where) if name == field2]
        found += _sharing(continuing, p, key, "cntn", field)
        found += _sharing(arriving, p, key2, "arvl", field2)
    shared, held = found[0] if found else (None, None)
    held_periods = trellis["periods"]

    def written(number, connector):
        """The trellis's periods with `connector` at index `number` of the
        connectors list of every reached period, appended where the list
        is shorter, and the addresses of the entry."""
        changed = []
        for p, period in enumerate(held_periods):
            if p not in periods:
                changed.append(period)
                continue
            connectors = list(period.get("connectors") or [])
            if number < len(connectors):
                connectors[number] = connector
            else:
                connectors.append(connector)
            changed.append({**period, "connectors": connectors})
        return changed, [(p, p, f"periods[{p}].connectors[{number}]") for p in periods]

    def admitted(number, connector):
        changed, addresses = written(number, connector)
        return _round_trips(
            changed,
            trellis["inter_connectors"],
            index,
            addresses,
            (key, field),
            (key2, field2),
        )

    extended = _extended(held_periods[h], sources, key, key2)
    if extended is None:
        extended = _extended(held_periods[h], group_sources, key, key2)
    if extended is not None:
        number, connector, keyed = extended
        spellings = ((field, field2),) if keyed else _spellings(key, field, key2, field2)
        entries = connector["fields"] if keyed else connector
        occupied = False
        for source, target in spellings:
            if source in entries:
                occupied = True
                continue
            candidate = (
                {**connector, "fields": {**connector["fields"], source: target}}
                if keyed
                else {**connector, source: target}
            )
            if admitted(number, candidate):
                path = ("connectors", number, "fields") if keyed else ("connectors", number)
                destination, address = _written_in(file, document, repeats, ("periods", h, *path))
                return ConnectorEntry(
                    destination, address, periods, f"{{{source}: {target}}}", None, shared, held
                )
        if occupied:
            path = ("connectors", number, "fields") if keyed else ("connectors", number)
            destination, address = _written_in(file, document, repeats, ("periods", h, *path))
            source, target = spellings[-1]
            return ConnectorEntry(
                destination, address, periods, f"{{{source}: {target}}}",
                "source-authored", shared, held,
            )
    destination, address = place
    try:
        held_list = (
            _value_at(document, address)
            if destination == str(file)
            else entry_value(_text(destination, texts), address)
        )
    except KeyError:
        held_list = None
    if not isinstance(held_list, list):
        entry = _address(entry_path(address)[:-1])
        text = f"{{{field}: {field2}}}"
        return ConnectorEntry(destination, entry, periods, text, "no-mapping", shared, held)
    empty = [
        number for number, item in enumerate(held_list) if isinstance(item, dict) and not item
    ]
    number = empty[0] if empty else len(held_list)
    for source, target in _spellings(key, field, key2, field2):
        if admitted(number, {source: target}):
            if empty:
                address = _address((*entry_path(address), number))
            return ConnectorEntry(
                destination, address, periods, f"{{{source}: {target}}}", None, shared, held
            )
    text = f"{{{key}.{field}: {key2}.{field2}}}"
    return ConnectorEntry(destination, address, periods, text, "name-shared", shared, held)


def _extended(period, sources, key, key2):
    """The connector of `period` to which a drag from the stage occurrence
    `key` to an arrival field of the stage occurrence `key2`, reached by
    the pairs whose entries `sources` names (`joins.unjoined_fields`), adds
    its key (unit J's decision J-D42): `(number, connector, keyed)` for the
    first connector of the period's `connectors` list that writes one of
    those pairs and can hold the key, `keyed` where it is written in the
    keyed form from `key` to `key2` and False where it is flat; None where
    no connector of the list writes such a pair, the inferred pairs and
    those of the inter-period mapping being written by no connector of the
    period."""
    connectors = period.get("connectors") or []
    paths = [entry_path(address) for address in sources if address is not None]
    numbers = sorted({path[3] for path in paths if path[2:3] == ("connectors",)})
    for number in numbers:
        connector = connectors[number] if number < len(connectors) else None
        if not isinstance(connector, dict):
            continue
        if not any(name in connector for name in ("from", "to", "fields")):
            return number, connector, False
        if (connector.get("from"), connector.get("to")) == (key, key2) and isinstance(
            connector.get("fields"), dict
        ):
            return number, connector, True
    return None


def _entry_between(trellis, index, file, document, repeats, writing, reading):
    """`connector_entry`'s answer for a drag from `writing` in `periods[h]`
    to `reading` in `periods[h - 1]`, `writing` admitted as unjoined and
    `reading` unjoined or reached by pairs, the line a key of the
    inter-period mapping either way, resolved separately at each adjacent
    pair the mapping joins; `file` is the trellis file, whose document and
    whose entries' numbers of periods `_trellis_read` answers, and
    `index` the eligible uses of the selection before the line."""
    (h, key, field), (_, key2, field2) = writing, reading
    try:
        place = _written_in(file, document, repeats, ("inter_connectors", h - 1))
    except KeyError:
        text = f"{field}: {field2}"
        return ConnectorEntry(str(file), "inter_connectors", (), text, "no-mapping", None, None)
    # the pairs the mapping joins; pair `p` joins `periods[p + 1]` to
    # `periods[p]`
    pairs = [
        p
        for p in range(len(trellis["periods"]) - 1)
        if _written_in(file, document, repeats, ("inter_connectors", p)) == place
    ]
    periods = tuple(sorted({q for p in pairs for q in (p, p + 1)}))
    found = []
    for p in (h - 1, *(p for p in pairs if p != h - 1)):
        later, earlier = trellis["periods"][p + 1], trellis["periods"][p]
        leaving = [
            k
            for k, name in _state_fields(later["stages"], "cntn", f"periods[{p + 1}]")
            if name == field
        ]
        arriving = [
            k
            for k, name in _state_fields(earlier["stages"], "arvl", f"periods[{p}]")
            if name == field2
        ]
        found += _sharing(leaving, p + 1, key, "cntn", field)
        found += _sharing(arriving, p, key2, "arvl", field2)
    shared, held = found[0] if found else (None, None)
    mappings = trellis["inter_connectors"]
    occupied = False
    for source, target in _spellings(key, field, key2, field2):
        if any(source in mappings[p] for p in pairs):
            occupied = True
            continue
        changed = [
            {**dict(mapping), source: target} if p in pairs else mapping
            for p, mapping in enumerate(mappings)
        ]
        addresses = [(p, p + 1, f"inter_connectors[{p}]") for p in pairs]
        if _round_trips(
            trellis["periods"],
            changed,
            index,
            addresses,
            (key, field),
            (key2, field2),
        ):
            return ConnectorEntry(*place, periods, f"{source}: {target}", None, shared, held)
    text = f"{key}.{field}: {key2}.{field2}"
    reason = "source-authored" if occupied else "name-shared"
    return ConnectorEntry(*place, periods, text, reason, shared, held)
