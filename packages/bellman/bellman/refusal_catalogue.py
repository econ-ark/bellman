"""The catalogue of the package's refusals.

The package refuses a stage file, a method target, a compilation and a model's
files under three closed vocabularies of rules of `bellman.refusals`: `RULES`,
the claims about the authored file that graph construction checks;
`TARGET_RULES`, the rules of the identity table by which a methods-file
target is read; and `FACTORY_RULES`, the rules of the Bellman factory.
`EXAMPLES` of `bellman.refusal_examples` holds, for each rule of the three,
the smallest text that breaks it, with the way it is provoked; `refusal_of`
provokes one example, and `catalogue()` answers every rule with the four parts
of its refusal and the refusal as printed.

The four parts are those every refusal supplies: `where`, the file, line and
column the refusal names, or its address where it carries no position;
`what`, the line of the example with a mark under the column, which a refusal
raised after construction has none of; `why`, the message, the sentence in the
model's words that says what is wrong and names the objects; and `write`, what
to write instead. A refusal under the rule `syntax` carries it as the sentence
of the grammar's own comment for the place, and an example may carry it as its
own `write`; the other refusals of graph construction state it inside `why`.
"""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import os
import tempfile
from pathlib import Path

from bellman.factory.elaboration import elaborate_stage, elaborate_text
from bellman.factory.joins import forward_order
from bellman.factory.loading import load_stage, load_trellis
from bellman.factory.recipe import load_recipe
from bellman.factory.trellis import assemble_trellis, elaborate_trellis
from bellman.refusal_examples import CORPUS, EXAMPLES, write_registry
from bellman.refusals import (
    FACTORY_RULES,
    RULES,
    TARGET_RULES,
    ConstructionError,
    FactoryError,
    TargetError,
)
from bellman.stage.binding_verbs import methodize
from bellman.stage.denotations import card
from bellman.stage.grains import operators_of
from bellman.stage.kernels import compile_kernel, kernel
from bellman.stage.method_targets import resolve_target
from bellman.syntax.parse import marked_line

__all__ = ("CatalogueEntry", "catalogue", "refusal_of", "text_of")


# --- the catalogue and the four parts of a refusal ---


@dataclasses.dataclass(frozen=True, kw_only=True)
class CatalogueEntry:
    """One rule of the package, the four parts of the refusal its example
    provokes, and that refusal as printed.

    `rule` is the rule's name and `vocabulary` the closed vocabulary it belongs
    to, `graph construction`, `the identity table` or `the Bellman factory`.
    `where`, `what`, `why` and `write` are the four parts of a refusal, as the
    module docstring describes them; `refusal` is the refusal as a reader
    meets it."""

    rule: str
    vocabulary: str
    where: str
    what: str
    why: str
    write: str
    refusal: str

    def __str__(self):
        lines = [f"{self.rule}  ({self.vocabulary})", f"  where  {self.where}"]
        if self.what:
            lines += ["  what", self.what]
        lines.append(f"  why    {self.why}")
        if self.write:
            lines.append(f"  write  {self.write}")
        return "\n".join(lines)

    __repr__ = __str__


class Catalogue(tuple):
    """Every rule of the three vocabularies with its refusal, in the order the
    vocabularies write them; a tuple of `CatalogueEntry` records that prints as
    the catalogue of the rules."""

    def __str__(self):
        return "\n\n".join(str(entry) for entry in self)

    __repr__ = __str__


def catalogue():
    """Every rule of `RULES`, `TARGET_RULES` and `FACTORY_RULES` of
    `bellman.refusals` with the four parts of its refusal and that refusal
    as printed, in the order the three vocabularies write them.

    A rule the table holds no example for, and one whose example provokes no
    refusal, is answered with the reason in place of the parts, so that the
    catalogue names it rather than passing over it."""
    entries = []
    for rule, vocabulary in (
        [(rule, "graph construction") for rule in RULES]
        + [(rule, "the identity table") for rule in TARGET_RULES]
        + [(rule, "the Bellman factory") for rule in FACTORY_RULES]
    ):
        example = EXAMPLES.get(rule)
        if example is None:
            entries.append(
                CatalogueEntry(
                    rule=rule,
                    vocabulary=vocabulary,
                    where="",
                    what="",
                    why="no example of this rule stands in the table",
                    write="",
                    refusal="",
                )
            )
            continue
        refusal = refusal_of(example)
        if refusal is None:
            entries.append(
                CatalogueEntry(
                    rule=rule,
                    vocabulary=vocabulary,
                    where="",
                    what="",
                    why="the example provokes no refusal",
                    write="",
                    refusal="",
                )
            )
            continue
        entries.append(
            CatalogueEntry(
                rule=rule,
                vocabulary=vocabulary,
                refusal=str(refusal),
                **_four_parts(example, refusal),
            )
        )
    return Catalogue(entries)


def refusal_of(example):
    """The refusal `example` provokes, or None where the package does not
    refuse it."""
    try:
        _provoke(example)
    except (ConstructionError, TargetError, FactoryError) as refused:
        return refused
    return None


def _four_parts(example, refusal):
    """The four parts of one refusal, as the module docstring describes them,
    by the names of the fields of `CatalogueEntry`."""
    if isinstance(refusal, FactoryError):
        where = ", ".join(
            part
            for part in (
                refusal.file,
                None if refusal.address is None else f"address {refusal.address!r}",
            )
            if part
        )
        return dict(where=where, what=refusal.written, why=refusal.message, write=refusal.write)
    if isinstance(refusal, TargetError):
        return dict(
            where=f"stage {refusal.stage!r}, target {refusal.target!r}",
            what="",
            why=str(refusal),
            write="",
        )
    # the file, the line and the column in words: the position as an editor
    # reads it stands in `refusal`, and the spelling of a position is written
    # by `ConstructionError` and nowhere else
    where = (
        f"address {refusal.address!r}"
        if refusal.line is None
        else f"{refusal.file}, line {refusal.line}, column {refusal.column}"
        + (f" (address {refusal.address!r})" if refusal.address else "")
    )
    written = getattr(refusal, "parts", None)
    if written is not None:
        # `_syntax_refusal` stores the three parts of a refusal under the rule
        # `syntax` on the refusal, and they are read there
        return dict(where=where, what=written.what, why=written.why, write=written.write)
    what = (
        "" if refusal.line is None else marked_line(text_of(example), refusal.line, refusal.column)
    )
    return dict(where=where, what=what, why=refusal.message, write=example.write)


# --- the calls that provoke a refusal ---

# the name by which a refusal of an example addresses the example registry,
# whatever directory holds it
REGISTRY_NAME = "registry"


# The repository the examples that change a stage file read it from: the
# variable the repository's commands export, and otherwise the checkout this
# package stands in.
ROOT = Path(os.environ.get("BELLMAN_DDSL_ROOT") or Path(__file__).resolve().parents[3])


def _provoke(example):
    """Ask of the example's stage, registry or trellis what its rule refuses:
    the call `_PROVOKERS` holds for the example's word `provokes`."""
    if example.provokes not in _PROVOKERS:
        raise ValueError(f"{example.provokes!r} is no way of provoking a refusal")
    return _PROVOKERS[example.provokes](example)


def _from_registry(example, call):
    """`call` on the example registry of `example`, a registry directory of
    `REGISTRY_FILES` with the example's `files` replacing entries; a refusal
    names the directory as `REGISTRY_NAME`."""
    directory = _registry(tuple(sorted(example.files.items())))
    try:
        return call(directory)
    except FactoryError as refused:
        # the example registry is addressed by the fixed relative name
        # `registry`, so that the catalogue and the page that prints it do not
        # depend on the machine
        for part in ("file", "message", "written", "write"):
            if isinstance(getattr(refused, part), str):
                setattr(
                    refused, part, getattr(refused, part).replace(str(directory), REGISTRY_NAME)
                )
        raise


def _one_period(example):
    """The elaboration of a trellis of one period of the corpus stages the
    example names, by key, with its connectors."""
    stages = {key: load_stage(ROOT / CORPUS[name]) for key, name in example.stages.items()}
    return elaborate_trellis(
        {"periods": [{"stages": stages, "connectors": example.connectors}], "inter_connectors": []}
    )


def _one_period_order(example):
    """The computation order of one constructed period. A connector cycle
    remains on the model and prevents this order."""
    trellis = _one_period(example)
    return forward_order(trellis["periods"][0], "periods[0]")


def _stage(example):
    """The stage the example's text constructs."""
    return _stage_of_text(text_of(example), example.origin)


def _methodized(example):
    """The example's stage methodized with its one methods entry. The stage
    is elaborated anew, since `methodize` binds the stage it is called on."""
    stage = _fresh_stage(example)
    return methodize(stage, {"stage": stage.name, "methods": [dict(example.entry)]})


def _methodized_with_block(example):
    """The example's stage, elaborated anew, methodized with a methods file
    holding its one entry, or the entries of its methods source `methods`
    where it gives one, which name a block file of the example's `files`:
    the files and the methods file stand in one folder, so that the block's
    path is read relative to the methods file, and a refusal names the block
    file as the entry writes it."""
    entries = tuple(tuple(entry.items()) for entry in example.methods.get("methods", ())) or (
        tuple(example.entry.items()),
    )
    folder = _block_folder(tuple(sorted(example.files.items())), entries)
    return methodize(_fresh_stage(example), folder / "methods.yml")


def _fresh_stage(example):
    """The stage the example's text constructs, elaborated anew for a verb
    that binds it."""
    return elaborate_text(text_of(example), example.origin)


def _other_version(example):
    """The kernel, on the example's stage, of a box of a second version of
    that stage, a stage of the same text elaborated anew and calibrated,
    since `calibrate` binds the stage it is called on."""
    stage = _stage(example)
    return kernel(stage, operators_of(_fresh_stage(example).calibrate({"ρ": 2.0}))[0])


# each word an example's `provokes` may hold, and the call that provokes
# its refusal
_PROVOKERS = {
    "load_recipe": lambda example: _from_registry(
        example, lambda directory: load_recipe(directory, example.recipe, **example.fills)
    ),
    "assemble_trellis": lambda example: _from_registry(
        example, lambda directory: assemble_trellis(directory, example.recipe, **example.fills)
    ),
    "load_trellis": lambda example: _from_registry(
        example, lambda directory: load_trellis(directory / example.file)
    ),
    "elaborate_stage": lambda example: elaborate_stage(example.record),
    "load_stage": lambda example: load_stage(example.path),
    "elaborate_trellis": _one_period,
    "forward_order": _one_period_order,
    "elaborate": _stage,
    "compile_kernel": lambda example: compile_kernel(_stage(example), example.target),
    "kernel": lambda example: kernel(_stage(example), example.target),
    "card": lambda example: card(_stage(example), example.target),
    "target": lambda example: resolve_target(_stage(example), example.target),
    "methodize": _methodized,
    "methodize-block": _methodized_with_block,
    "configure-option": lambda example: methodize(
        _fresh_stage(example), example.methods
    ).configure(example.settings),
    "other-version": _other_version,
}


# --- the stage text of an example, and its registry ---


def text_of(example):
    """The stage text of `example`: the text it writes, or the stage file it
    names with its changes applied. A line the file no longer holds is refused,
    so that a change to a stage file is read here and not silently dropped."""
    if not example.corpus:
        return example.text
    text = _corpus_text(example.corpus)
    for written, changed in example.changes:
        if text.count(written) != 1:
            raise ValueError(f"{example.corpus} no longer holds the line {written!r} once")
        text = text.replace(written, changed)
    return text


# the examples share their stage texts, so a text is elaborated once for the
# catalogue; the reader is the factory's one `elaborate_text`
_stage_of_text = functools.lru_cache(maxsize=8)(elaborate_text)


@functools.lru_cache(maxsize=8)
def _block_folder(files, entries):
    """A folder holding the block files `files` and the methods file
    `methods.yml` of the entries `entries`, each the pairs of one entry,
    written once per process under the temporary directory at a name
    derived from the two."""
    digest = hashlib.sha256(repr((files, entries)).encode("utf-8")).hexdigest()[:12]
    folder = Path(tempfile.gettempdir()) / f"bellman-block-{digest}"
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in files:
        (folder / name).write_text(text, encoding="utf-8")
    lines = []
    for entry in entries:
        written = dict(entry)
        lines += [f"  - on: {written.pop('on')}", f"    method: {written.pop('method')}"]
        lines += [f"    {key}: {value}" for key, value in written.items()]
    (folder / "methods.yml").write_text("methods:\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return folder


@functools.lru_cache(maxsize=32)
def _registry(items):
    """A registry directory of `REGISTRY_FILES` with the files `items`
    replacing entries, written once per process under the temporary
    directory at a name derived from `items`; a refusal raised from it names
    the directory as `REGISTRY_NAME`."""
    digest = hashlib.sha256(repr(items).encode("utf-8")).hexdigest()[:12]
    return write_registry(Path(tempfile.gettempdir()) / f"bellman-registry-{digest}", dict(items))


def _corpus_text(name):
    """The text of the stage file `name`, a key of `CORPUS` or a path in the
    repository."""
    return (ROOT / CORPUS.get(name, name)).read_text(encoding="utf-8")
