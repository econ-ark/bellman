"""The DisCoPy classes of a stage, their immutable subclasses, and the copy of
a stage version's objects.

`BellmanHypergraph` is the hypergraph class of a stage, and `Block` and
`Builder` are the bubbles of a block of an initial diagram and of a builder
of a builders graph; the public DisCoPy classes are not modified.
`freeze_native` makes the immutable form of a value a stage holds, in which
each DisCoPy object is an instance of the immutable subclass of its class.
`copy_native` gives a new version its own objects, one copy of each object
however often it is referred to. A scalar, a class and an empty tuple are
held as they are. A mapping the two make is a `MappingProxyType`, which the
standard pickle writes as a call of `_mapping_proxy` on a plain dict.
`_Encoder` and `_Decoder` write a bubble's interior as a JSON tree and read
it back.
"""

from __future__ import annotations

import copyreg
import dataclasses
import importlib
from collections.abc import Mapping
from contextvars import ContextVar
from functools import cached_property, wraps
from types import MappingProxyType

from discopy import cat, frobenius, hypergraph, messages, monoidal, rigid
from discopy.utils import AxiomError, assert_isatomic, assert_isinstance

from bellman.native.labels import graph_text


class BellmanHypergraph(frobenius.Hypergraph):
    """The hypergraph class of a Bellman stage: the public frobenius
    hypergraph whose constructor performs the library's own consistency
    checks in one pass.

    The public constructor rebuilds the port list once per port it checks;
    on a stage's graphs that is most of elaboration time. This subclass makes
    the same checks, raising the same errors, on one port list computed once,
    and relabels spiders by first occurrence exactly as the public constructor
    does. Sequential and parallel composition, ``from_box`` and ``id`` return
    this class, since the library constructs their results with the class of
    their arguments. Nothing about the library is modified.
    """

    def __init__(self, dom, cod, boxes, wires, spider_types=None, offsets=None):
        assert_isinstance(dom, self.category.ob)
        assert_isinstance(cod, self.category.ob)
        for box in boxes:
            assert_isinstance(box, self.category.ar)
        self.dom, self.cod, self.boxes = dom, cod, boxes
        dom_wires, box_wires, cod_wires = wires
        if len(dom_wires) != len(dom):
            raise ValueError
        if len(cod_wires) != len(cod):
            raise ValueError
        if len(box_wires) != len(boxes):
            raise ValueError
        for box, (box_dom_wires, box_cod_wires) in zip(boxes, box_wires):
            if len(box_dom_wires) != len(box.dom):
                raise ValueError
            if len(box_cod_wires) != len(box.cod):
                raise ValueError
        flat_wires = dom_wires + sum([x + y for x, y in box_wires], ()) + cod_wires
        connected = dict.fromkeys(flat_wires)  # spiders in order of first occurrence
        ports = self.ports  # computed once
        if spider_types is None:
            spider_types = {spider: port.obj for spider, port in zip(flat_wires, ports)}
        if not isinstance(spider_types, Mapping):
            spider_types = dict(enumerate(spider_types))
        relabeling = list(connected) + sorted(set(spider_types.keys()) - set(connected))
        index = {spider: i for i, spider in enumerate(relabeling)}
        self.spider_types = tuple(
            typ.r if getattr(typ, "z", 0) else typ for typ in (spider_types[s] for s in relabeling)
        )
        self.flat_wires = tuple(index[s] for s in flat_wires)
        self.wires = self.rebracket(self.flat_wires)
        self.dom_wires, self.box_wires, self.cod_wires = self.wires
        for obj in self.spider_types:
            assert_isatomic(obj, self.category.ob)
        for obj, spider_wires in zip(self.spider_types, self.spider_wires):
            adjoint = getattr(obj, "r", obj)
            for i in set.union(*spider_wires):
                if ports[i].obj not in (obj, adjoint):
                    raise AxiomError(messages.TYPE_ERROR.format(obj, ports[i].obj))
        self.offsets = offsets or tuple(len(boxes) * [None])

    def __str__(self):
        """The printed listing of the graph: its boxes, in the order its
        drawing shows them, under the labels the drawing shows
        (`labels.graph_text`)."""
        return graph_text(self)


class _NamedBubble(frobenius.Bubble):
    """A bubble named by a block id, which holds its interior, a DisCoPy
    diagram, and its `data`.

    The two public classes below are its only subclasses. They behave alike
    and differ in name, which is what distinguishes the two boxes that share
    a block id: a `Block` in an initial diagram and a `Builder` in a builders
    graph. Equality compares the class, so a block never equals a builder.
    """

    def __init__(self, *args, data=None, **kwargs):
        super().__init__(*args, data=data, **kwargs)
        self.data = data
        self.is_dagger = kwargs.get("is_dagger", False)

    def __eq__(self, other):
        if isinstance(other, _NamedBubble):
            left, right = _public(self), _public(other)
            return type(left) is type(right) and all(
                getattr(left, name) == getattr(right, name)
                for name in ("args", "dom", "cod", "name", "method", "data", "is_dagger")
            )
        return not isinstance(other, cat.Box) and super().__eq__(other)

    def __hash__(self):
        return hash(
            (
                type(self).__name__,
                self.args,
                self.dom,
                self.cod,
                self.name,
                self.method,
                self.data,
                self.is_dagger,
            )
        )

    def __repr__(self):
        return (
            f"{__name__}.{type(_public(self)).__name__}({', '.join(map(repr, self.args))}, "
            f"dom={self.dom!r}, cod={self.cod!r}, name={self.name!r}, "
            f"method={self.method!r}, data={self.data!r}, "
            f"is_dagger={self.is_dagger!r})"
        )

    def to_tree(self):
        """The tree DisCoPy writes for the bubble, its interior and data
        written by `_Encoder`, and whether it is frozen."""
        encode = _Encoder()
        return dict(
            factory=f"{__name__}.{type(_public(self)).__name__}",
            name=self.name,
            args=encode(self.args),
            dom=encode(self.dom),
            cod=encode(self.cod),
            data=encode(self.data),
            method=self.method,
            is_dagger=self.is_dagger,
            frozen=is_frozen_native(self),
        )

    @classmethod
    def from_tree(cls, tree):
        """The bubble a tree of `to_tree` describes, frozen where the tree
        says it was."""
        decode = _Decoder()
        args = decode(tree["args"])
        made = getattr(cls, "_native_class", cls)
        result = made(
            *args,
            dom=decode(tree["dom"]),
            cod=decode(tree["cod"]),
            name=tree["name"],
            data=decode(tree["data"]),
            method=tree.get("method", "bubble"),
            is_dagger=tree.get("is_dagger", False),
        )
        return freeze_native(result) if tree.get("frozen") else result


class Block(_NamedBubble):
    """A box of an initial diagram: the authored block, named by its id,
    holding one box per authored line on field wires."""


class Builder(_NamedBubble):
    """A box of a builders graph: the operator a block denotes, holding the
    primitive operators of its lines and, for a `!node` line, the sub-builder
    bubble of that node."""


# The values the copier holds as they are.
_SCALARS = (str, bytes, int, float, complex, bool, type(None))
# The DisCoPy objects the copier makes instances of an immutable subclass.
_NATIVE = (cat.Ob, cat.Arrow, hypergraph.Hypergraph)
# The attributes that make up a DisCoPy object's structure, through which the
# copier admits a cycle.
_STRUCTURE = frozenset(
    ("dom", "cod", "inside", "args", "boxes", "boxes_or_types", "spider_types", "terms")
)


def freeze_native(value):
    """The immutable form of a value a stage holds: each DisCoPy object in it
    copied into the immutable subclass of its class, an object already
    immutable kept, and no value the caller holds modified."""
    return _Copier(copy_frozen=False).copy(value)


def copy_native(value):
    """An immutable copy of a value in which each DisCoPy object, record and
    container is new, each copied once however often it is referred to. A
    stage version passes on, in the same walk, the answers its graphs
    determine (`versions.StageVersion._carry`), so that the copies refer to the
    objects of the new version."""
    walk = _Copier(copy_frozen=True)
    result = walk.copy(value)
    carry = getattr(type(value), "_carry", None)
    if carry is not None:
        carry(value, result, walk.copy)
    return result


def is_frozen_native(value):
    """Whether a value and everything in it refuse an ordinary write: an
    immutable DisCoPy object, a scalar, or a tuple, a frozenset, a
    `MappingProxyType` or a frozen record of such values.

    It does not ask whether a caller still holds the dict beneath a
    `MappingProxyType`, and a write through `object.__setattr__` or
    `__dict__` is not considered.
    """
    seen = set()

    def check(item):
        if isinstance(item, _NATIVE):
            return isinstance(item, Immutable) and item.__dict__.get("_bellman_frozen", False)
        if type(item) in _SCALARS:
            return True
        if id(item) in seen:
            return True
        seen.add(id(item))
        if type(item) in (tuple, frozenset):
            return all(check(child) for child in item)
        if type(item) is MappingProxyType:
            return all(check(key) and check(child) for key, child in item.items())
        if is_frozen_record(item):
            return all(check(getattr(item, field.name)) for field in dataclasses.fields(item))
        return False

    return check(value)


def is_frozen_record(value):
    """Whether `value` is an instance of a frozen dataclass."""
    return (
        dataclasses.is_dataclass(value)
        and not isinstance(value, type)
        and value.__dataclass_params__.frozen
    )


# The kinds of value the copier tells apart, by the class of the value: held
# as it is, a DisCoPy object, a tuple or a list, a set or a frozenset, a
# mapping, a frozen record, a named tuple, and any other value, which it
# refuses.
_KEEP, _GRAPH_OBJECT, _SEQUENCE, _SET, _MAPPING, _RECORD, _NAMED_TUPLE, _REFUSED = range(8)

# The kind of each class the copier has met (`_kind_of`), the names of its
# cached properties (`_cached_properties`) and, for a frozen record, the names
# of its fields in their order (`_field_names`). Each depends on the class
# alone, so it is found once per class and not once per object. A class
# changed after the copier first met it is read as it was then.
_KINDS = {}
_CACHED_PROPERTIES = {}
_FIELD_NAMES = {}


def _kind_of(cls):
    """The kind of the values of class `cls`, tested in the order the copier
    applies: a scalar or a class is held as it is; then a DisCoPy object, a
    tuple or a list, a named tuple (a tuple subclass with `_fields`, such as
    the `Diagnostic` the kept diagnostics hold), a set or a frozenset, a
    mapping and a frozen record."""
    if cls in _SCALARS or issubclass(cls, type):
        kind = _KEEP
    elif issubclass(cls, _NATIVE):
        kind = _GRAPH_OBJECT
    elif cls in (tuple, list):
        kind = _SEQUENCE
    elif issubclass(cls, tuple) and hasattr(cls, "_fields"):
        kind = _NAMED_TUPLE
    elif cls in (set, frozenset):
        kind = _SET
    elif issubclass(cls, Mapping):
        kind = _MAPPING
    elif dataclasses.is_dataclass(cls) and cls.__dataclass_params__.frozen:
        kind = _RECORD
    else:
        kind = _REFUSED
    _KINDS[cls] = kind
    return kind


class _Copier:
    """One walk of the copier. It makes each copy once and gives a value
    reached again the copy it made (`memo`); a copy it made is kept as it is
    (`owned`); `active` holds the values being copied, which a cycle reaches
    again; `sources` keeps every source alive during the walk, so that no id
    is reused. `copy_frozen` says whether an object already immutable is
    copied as well."""

    def __init__(self, *, copy_frozen, memo=None):
        self.copy_frozen = copy_frozen
        self.memo = {} if memo is None else memo
        self.active, self.owned = {}, {}
        self.sources = {}

    def copy(self, value, component=None, structural=False):
        """The copy of `value` in this walk: a scalar, a class and a copy the
        walk made are themselves, and so is an immutable DisCoPy object where
        the walk does not copy frozen objects. `component` marks the DisCoPy
        object whose structure is being walked and `structural` whether
        `value` is reached through that structure, which `_refuse_cycle`
        reads."""
        cls = type(value)
        kind = _KINDS.get(cls)
        if kind is None:
            kind = _kind_of(cls)
        if kind == _KEEP:
            return value
        key = id(value)
        if key in self.owned:
            return value
        if kind == _GRAPH_OBJECT and not self.copy_frozen and is_frozen_native(value):
            return value
        if component is None:
            component = object()
        active, memo = self.active, self.memo
        started = key not in active
        if not started:
            self._refuse_cycle(value, component, structural)
        if key in memo:
            return memo[key]
        self.sources[key] = value
        if started:
            active[key] = component, structural
        if kind == _GRAPH_OBJECT:
            result = self._copy_graph_object(value, component)
        elif kind == _SEQUENCE:
            result = self._copy_sequence(value, component, structural)
        elif kind == _NAMED_TUPLE:
            result = self._copy_named_tuple(value, component, structural)
        elif kind == _SET:
            result = frozenset([self.copy(child) for child in value])
        elif kind == _MAPPING:
            result = self._copy_mapping(value)
        elif kind == _RECORD:
            result = self._copy_frozen_record(value)
        else:
            raise TypeError(f"Cannot copy immutable native data of type {cls.__name__}.")
        self.owned[id(result)] = result
        memo[key] = result
        if started:
            del active[key]
        return result

    def _refuse_cycle(self, value, component, structural):
        """Refuses a value reached again while it is being copied, unless the
        cycle runs through the structure of one native object."""
        previous_component, previous_structural = self.active[id(value)]
        if not (
            structural
            and previous_component is component
            and (isinstance(value, _NATIVE) or type(value) is tuple and previous_structural)
        ):
            raise TypeError("Cyclic attached data cannot be copied.")

    def _copy_graph_object(self, value, component):
        """The immutable copy of a DisCoPy object, a type, a box or a graph."""
        cls = type(value)
        result = object.__new__(_frozen_class_of(cls))
        self.memo[id(value)] = result
        cached = _cached_properties(cls)
        copy = self.copy
        for name, child in vars(value).items():
            if name == "_bellman_frozen" or name in cached:
                continue
            if name in _STRUCTURE:
                copied = copy(child, component, True)
            else:
                copied = copy(child, object(), False)
            object.__setattr__(result, name, copied)
        if isinstance(value, hypergraph.Hypergraph) and not is_frozen_native(value):
            # Public mutable children may have changed since construction.
            _check_native_wiring(result)
        object.__setattr__(result, "_bellman_frozen", True)
        return result

    def _copy_sequence(self, value, component, structural):
        """A tuple of the copies of a sequence's items; a tuple whose items
        are all kept is kept itself, unless the walk copies frozen objects."""
        copy = self.copy
        children = tuple([copy(child, component, structural) for child in value])
        return self.memo.get(
            id(value),
            value
            if not self.copy_frozen
            and type(value) is tuple
            and all(a is b for a, b in zip(value, children))
            else children,
        )

    def _copy_named_tuple(self, value, component, structural):
        """A named tuple of the copies of its fields, of the value's own
        class; the value itself where every field is kept and the walk does
        not copy frozen objects."""
        copy = self.copy
        children = [copy(child, component, structural) for child in value]
        if not self.copy_frozen and all(a is b for a, b in zip(value, children)):
            return value
        return type(value)(*children)

    def _copy_mapping(self, value):
        """A read-only mapping of the copies of a mapping's keys and values."""
        copy = self.copy
        return MappingProxyType({copy(key): copy(child) for key, child in value.items()})

    def _copy_frozen_record(self, value):
        """A frozen record with the copies of its fields, or the record itself
        where every field is kept and the walk does not copy frozen objects."""
        cls = type(value)
        names, declared = _field_names(cls)
        # The stored value of a field, not the attribute: three attributes
        # of `ElaboratedStage` answer with a navigation object built on
        # access, which holds the stage and is not what the version holds.
        state = getattr(value, "__dict__", {})
        cached = _cached_properties(cls)
        held = state
        if cached:
            held = {name: child for name, child in state.items() if name not in cached}
        undeclared = not held.keys() <= declared
        source = {name: held[name] if name in held else getattr(value, name) for name in names}
        copy = self.copy
        fields = {name: copy(child) for name, child in source.items()}
        if undeclared:
            raise TypeError("Frozen dataclass data has undeclared attributes.")
        if not self.copy_frozen and all(child is source[name] for name, child in fields.items()):
            return value
        result = object.__new__(cls)
        for name, child in fields.items():
            object.__setattr__(result, name, child)
        return result


def _cached_properties(cls):
    """The names of the cached properties of `cls`, each name read where the
    class and its bases first define it: the value an object remembers under
    such a name is no data of the object, so the copier passes over it. An
    identity remembers its spelling this way."""
    names = _CACHED_PROPERTIES.get(cls)
    if names is None:
        first = {}
        for base in cls.__mro__:
            for name, descriptor in vars(base).items():
                first.setdefault(name, descriptor)
        names = frozenset(
            name for name, descriptor in first.items() if isinstance(descriptor, cached_property)
        )
        _CACHED_PROPERTIES[cls] = names
    return names


def _field_names(cls):
    """The names of the fields of the frozen record class `cls`, in the order
    `dataclasses.fields` gives them, and the same names as a set."""
    names = _FIELD_NAMES.get(cls)
    if names is None:
        ordered = tuple(field.name for field in dataclasses.fields(cls))
        names = _FIELD_NAMES[cls] = ordered, frozenset(ordered)
    return names


def _check_native_wiring(value):
    """The library constructor's consistency checks in one pass over the ports.

    A public hypergraph may have had a box or a type changed after its
    construction. These are the checks of ``Hypergraph.__init__`` on the
    retained attributes, raising the same errors, without rebuilding the
    port list once per port as the library does.
    """
    cls = getattr(type(value), "_native_class", type(value))
    objects, arrows = cls.category.ob, cls.category.ar
    assert_isinstance(value.dom, objects)
    assert_isinstance(value.cod, objects)
    for box in value.boxes:
        assert_isinstance(box, arrows)
    dom_wires, box_wires, cod_wires = value.wires
    if (
        len(dom_wires) != len(value.dom)
        or len(cod_wires) != len(value.cod)
        or len(box_wires) != len(value.boxes)
    ):
        raise ValueError
    for box, (inputs, outputs) in zip(value.boxes, box_wires):
        if len(inputs) != len(box.dom) or len(outputs) != len(box.cod):
            raise ValueError
    spider_types = value.spider_types
    for typ in spider_types:
        assert_isatomic(typ, objects)

    def check(ports, wires):
        for port, spider in zip(ports, wires):
            typ = spider_types[spider]
            if port not in (typ, getattr(typ, "r", typ)):
                raise AxiomError(messages.TYPE_ERROR.format(typ, port))

    check(value.dom, dom_wires)
    for box, (inputs, outputs) in zip(value.boxes, box_wires):
        check(box.dom, inputs)
        check(box.cod, outputs)
    check(value.cod, cod_wires)


def _mapping_proxy(entries):
    """The read-only mapping over the dict `entries`. The reducer registered
    below writes a mapping the copier makes as a call of this function, which
    the standard pickle records by its module and name; pickle cannot record
    the type `MappingProxyType` so, since it finds no `mappingproxy` among the
    built-in names. `copy.deepcopy` reads the same reducer. Importing this
    module registers the reducer with `copyreg` for `types.MappingProxyType`
    in the whole Python process, so that `pickle` and `copy.deepcopy`, which
    otherwise refuse a read-only mapping, then accept any read-only mapping
    in that process and write it as this function applied to a copy of its
    entries."""
    return MappingProxyType(entries)


copyreg.pickle(MappingProxyType, lambda proxy: (_mapping_proxy, (dict(proxy),)))


# The answers of one complete comparison, by `comparison_answered_once`. It is
# a `ContextVar`, so that two comparisons at once, in two threads or two
# tasks, each keep their own.
_COMPARISONS = ContextVar("bellman_native_comparisons", default=None)


def comparison_answered_once(compare):
    """`compare`, answering each pair of operands once within one complete
    comparison; the answers are forgotten when that comparison ends."""

    @wraps(compare)
    def equal(left, right):
        # A DisCoPy type holds no record whose comparison is costly, so it is
        # compared directly.
        if isinstance(left, cat.Ob):
            return compare(left, right)
        memo = _COMPARISONS.get()
        token = None
        if memo is None:
            memo = {}
            token = _COMPARISONS.set(memo)
        try:
            key = compare, id(left), id(right)
            if key not in memo:
                # Keep operands alive: temporary tuples can otherwise
                # reuse ids.
                memo[key] = left, right, compare(left, right)
            _, _, result = memo[key]
            return result
        finally:
            if token is not None:
                _COMPARISONS.reset(token)

    return equal


class Immutable:
    """The base of the immutable subclasses. Once `_bellman_frozen` is set, a
    write or a deletion of an attribute is refused. Equality, the hash and
    the repr are those of the public class the subclass freezes
    (`_native_class`), and a copy is made by the copier."""

    def __setattr__(self, name, value):
        if self.__dict__.get("_bellman_frozen", False):
            raise AttributeError(f"{type(self)._native_class.__name__} is frozen.")
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if self.__dict__.get("_bellman_frozen", False):
            raise AttributeError(f"{type(self)._native_class.__name__} is frozen.")
        object.__delattr__(self, name)

    @comparison_answered_once
    def __eq__(self, other):
        return type(self)._native_class.__eq__(_public(self), _public(other))

    def __hash__(self):
        return type(self)._native_class.__hash__(_public(self))

    def __repr__(self):
        return type(self)._native_class.__repr__(_public(self))

    def __deepcopy__(self, memo):
        return _Copier(copy_frozen=True, memo=memo).copy(self)

    def __copy__(self):
        return copy_native(self)

    def __setstate__(self, state):
        if self.__dict__.get("_bellman_frozen", False):
            raise AttributeError("A frozen native object cannot be replaced.")
        object.__setattr__(self, "__dict__", state)


def _public(value):
    """An instance of the public class with the same attributes, which the
    library's own comparison, hash and repr read."""
    if not isinstance(value, Immutable):
        return value
    result = object.__new__(type(value)._native_class)
    result.__dict__.update(value.__dict__)
    return result


# The immutable subclass of each public class, by that class, as
# `declare_frozen_class` records it.
_FROZEN_CLASSES = {}


def declare_frozen_class(frozen):
    """Declare the immutable subclass of one public class and record it under
    the class it freezes.

    The subclasses are declared once, where the class they freeze is defined,
    and are never made on first use: a class made on first use is absent from
    its module until the call that makes it, so a graph pickled in one process
    could not be loaded in a fresh one. A subclass of a class
    of another module is declared in that module and registered here, which
    keeps the direction of the imports downward.
    """
    _FROZEN_CLASSES[frozen._native_class] = frozen
    return frozen


def _frozen_class_of(cls):
    """The immutable subclass of a public class, as `declare_frozen_class`
    declared it. A class already immutable is itself."""
    if issubclass(cls, Immutable):
        return cls
    frozen = _FROZEN_CLASSES.get(cls)
    if frozen is None:
        raise TypeError(
            f"No immutable subclass of {cls.__module__}.{cls.__qualname__} is declared. A class "
            f"whose instances a stage retains declares its subclass beside itself with "
            f"hypergraphs.declare_frozen_class."
        )
    return frozen


# The immutable subclasses of the public classes a stage's graphs hold,
# declared once here and, for `records.Sort`, in the module that defines it.
# A pickle names each by its module and its name, so a graph pickled before
# one of them is renamed or moved cannot be read after it.


@declare_frozen_class
class _FrozenOb(Immutable, frobenius.Ob):
    _native_class = frobenius.Ob


@declare_frozen_class
class _FrozenTy(Immutable, frobenius.Ty):
    _native_class = frobenius.Ty


@declare_frozen_class
class _FrozenBox(Immutable, frobenius.Box):
    _native_class = frobenius.Box


@declare_frozen_class
class _FrozenDiagram(Immutable, frobenius.Diagram):
    _native_class = frobenius.Diagram


@declare_frozen_class
class _FrozenSwap(Immutable, frobenius.Swap):
    _native_class = frobenius.Swap


@declare_frozen_class
class _FrozenCup(Immutable, frobenius.Cup):
    _native_class = frobenius.Cup


@declare_frozen_class
class _FrozenCap(Immutable, frobenius.Cap):
    _native_class = frobenius.Cap


@declare_frozen_class
class _FrozenSpider(Immutable, frobenius.Spider):
    _native_class = frobenius.Spider


@declare_frozen_class
class _FrozenBubble(Immutable, frobenius.Bubble):
    _native_class = frobenius.Bubble


@declare_frozen_class
class _FrozenHypergraph(Immutable, frobenius.Hypergraph):
    _native_class = frobenius.Hypergraph


@declare_frozen_class
class _FrozenRigidLayer(Immutable, rigid.Layer):
    _native_class = rigid.Layer


@declare_frozen_class
class _FrozenMonoidalLayer(Immutable, monoidal.Layer):
    _native_class = monoidal.Layer


@declare_frozen_class
class _FrozenBellmanHypergraph(Immutable, BellmanHypergraph):
    _native_class = BellmanHypergraph


@declare_frozen_class
class _FrozenBuilder(Immutable, Builder):
    _native_class = Builder


@declare_frozen_class
class _FrozenBlock(Immutable, Block):
    _native_class = Block


class _Encoder:
    """The JSON tree of a bubble's interior and data: each object written
    once, under a number, and written as a reference to that number where it
    recurs."""

    def __init__(self):
        self.memo = {}

    def __call__(self, value):
        if type(value) in (str, int, float, bool, type(None)):
            return value
        if id(value) in self.memo:
            return {"ref": self.memo[id(value)]}
        index = self.memo[id(value)] = len(self.memo)
        if type(value) is bytes:
            return dict(id=index, kind="bytes", value=value.hex())
        if type(value) is complex:
            return dict(id=index, kind="complex", real=value.real, imag=value.imag)
        if isinstance(value, _NATIVE):
            entries = {
                name: child for name, child in vars(value).items() if name != "_bellman_frozen"
            }
            return dict(
                id=index,
                kind="native",
                cls=_class_name(type(value)),
                fields={name: self(child) for name, child in entries.items()},
            )
        if dataclasses.is_dataclass(value):
            return dict(
                id=index,
                kind="record",
                cls=_class_name(type(value)),
                fields={
                    field.name: self(getattr(value, field.name))
                    for field in dataclasses.fields(value)
                },
            )
        if isinstance(value, Mapping):
            return dict(
                id=index, kind="mapping", items=[[self(k), self(v)] for k, v in value.items()]
            )
        if type(value) in (tuple, list, frozenset, set):
            return dict(id=index, kind=type(value).__name__, items=list(map(self, value)))
        raise TypeError(f"No native tree encoding for {type(value).__name__}.")


def _class_name(cls):
    """The name a tree writes for a class, `module:qualified name` of the
    public class; a stage's hypergraph class is written as DisCoPy's."""
    cls = getattr(cls, "_native_class", cls)
    if cls in (frobenius.Hypergraph, BellmanHypergraph):
        return "discopy.frobenius:Hypergraph"
    return cls.__module__ + ":" + cls.__qualname__


class _Decoder:
    """The reading of a tree `_Encoder` wrote, each object made once."""

    def __init__(self):
        self.memo, self.trees = {}, {}

    def __call__(self, tree):
        if not isinstance(tree, dict):
            return tree
        if "ref" in tree:
            reference = tree["ref"]
            return self.memo[reference] if reference in self.memo else self(self.trees[reference])
        if tree["id"] in self.memo:
            return self.memo[tree["id"]]
        self.trees[tree["id"]] = tree
        kind = tree["kind"]
        if kind in ("native", "record"):
            result = object.__new__(_class(tree["cls"]))
            self.memo[tree["id"]] = result
            for name, child in tree["fields"].items():
                object.__setattr__(result, name, self(child))
        elif kind == "mapping":
            result = {self(k): self(v) for k, v in tree["items"]}
        elif kind == "bytes":
            result = bytes.fromhex(tree["value"])
        elif kind == "complex":
            result = complex(tree["real"], tree["imag"])
        else:
            values = tuple(map(self, tree["items"]))
            result = self.memo.get(
                tree["id"], frozenset(values) if kind in ("set", "frozenset") else values
            )
        self.memo[tree["id"]] = result
        return result


def _class(name):
    """The class a tree names; DisCoPy's hypergraph class is read as
    `BellmanHypergraph`."""
    if name == "discopy.frobenius:Hypergraph":
        return BellmanHypergraph
    module, path = name.split(":", 1)
    result = importlib.import_module(module)
    for part in path.split("."):
        result = getattr(result, part)
    return result
