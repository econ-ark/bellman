"""The catalogue of the package's refusals.

The package refuses a stage file, a name given to a query of the stage
object, a compilation and a model's files under three closed vocabularies of
rules of `bellman.refusals`, `VOCABULARIES`: `RULES`, the claims about the
authored file that graph construction checks; `TARGET_RULES`, the three
failures of a name read against the pieces of a version; and `FACTORY_RULES`,
the rules of the Bellman factory. `EXAMPLES` of `bellman.refusal_examples`
holds, for each rule of the three, the smallest text that breaks it, with the
way it is provoked and the edit that makes it pass; `refusal_of` provokes one
example, `entry` answers one rule's entry, that rule's example alone run, and
`catalogue()` answers every rule's entry in the order the vocabularies write
them.

An entry, a `CatalogueEntry`, holds the rule's vocabulary; its operation,
read from the way the rule's example is provoked (`operation`): the word of
the Workbench for the operation under which an author meets the refusal,
`parse`, `elaborate`, `methodize`, `configure`, `connect` or `read`, or
`query` where a Python caller meets it through a query of the stage object,
such as `kernel`, `compile_kernel` or `card`; its condition, the claim the
comment above the rule's name in `refusals.py` states (`claims`); its
example; and the four parts of the refusal the example provokes, which the
printed entry labels as the package's example. The four parts are those
every refusal supplies: `where`, the file, line and column the refusal
names, or its address where it carries no position; `what`, the line of the
example with a mark under the column, which a refusal raised after
construction has none of; `why`, the message, the sentence in the model's
words that says what is wrong and names the objects; and `write`, the
action, the edit the check establishes, which a refusal carries as its own
field and which is empty where the check establishes none. The edit the
example's table gives, `write` of the example, is not printed: the entry
runs the corrected example through the operation that refused the example
and records whether it passes, so that every admitted form the table gives
is checked.

An entry is answered from the installed package alone. An example that
reads a stage file of the repository, one of `CORPUS`, is run where the
repository's root `ROOT` holds that file, as a checkout does; an
installation outside the checkout holds none of them, and the entry of such
a rule gives its vocabulary, its operation and its condition, with the
reason in place of the four parts.

The published reference of the rules is the Refusals page of the
documentation, `REFERENCE_PAGE`, which anchors every rule of the three
vocabularies by its name: the entry of a rule stands at
`REFERENCE_PAGE + "#" + rule`. The Workbench's Rule link opens it and shows
the entry the installed package answers beside the sentence.
"""

from __future__ import annotations

import ast
import dataclasses
import functools
import hashlib
import inspect
import io
import os
import tempfile
import tokenize
from pathlib import Path

import bellman.refusals as rules_module
from bellman.factory.elaboration import elaborate_stage, elaborate_text
from bellman.factory.joins import forward_order
from bellman.factory.loading import load_stage, load_trellis
from bellman.factory.recipe import load_recipe
from bellman.factory.trellis import assemble_trellis, elaborate_trellis
from bellman.refusal_examples import CORPUS, EXAMPLES, corrected, write_registry
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
from bellman.syntax.parse import marked_line

__all__ = (
    "REFERENCE_PAGE",
    "VOCABULARIES",
    "CatalogueEntry",
    "catalogue",
    "claims",
    "entry",
    "operation",
    "refusal_of",
    "text_of",
)


# --- the vocabularies, the operations and the published page ---

# The Refusals page of the published documentation, which anchors every rule
# of the three vocabularies by its name.
REFERENCE_PAGE = "https://econ-ark.github.io/bellman/Bellman-Sym/reference/refusals/"

# The three vocabularies in the order the catalogue writes them, each by the
# words the catalogue names it by, the name of its table in
# `bellman.refusals` and the table itself.
VOCABULARIES = (
    ("graph construction", "RULES", RULES),
    ("the names of the pieces", "TARGET_RULES", TARGET_RULES),
    ("the Bellman factory", "FACTORY_RULES", FACTORY_RULES),
)

# the rule of the parser, whose refusal the Workbench files under `parse`
PARSER_RULE = "syntax"


def operation(rule):
    """The operation that refuses under `rule`: `parse` for the rule of the
    parser, whichever operation reads the text, and otherwise the operation
    `_PROVOKERS` gives the way the rule's example is provoked; the empty
    string where the table holds no example of the rule."""
    if rule == PARSER_RULE:
        return "parse"
    example = EXAMPLES.get(rule)
    return "" if example is None else _PROVOKERS[example.provokes][0]


@functools.cache
def claims():
    """The claim each rule of the three vocabularies states, by its name:
    the comment lines written above the rule's name in the tuple of its
    vocabulary in `refusals.py`, joined, read from the module's source. A
    rule written without a comment has the empty claim."""
    source = inspect.getsource(rules_module)
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    tables = {table for _, table, _ in VOCABULARIES}
    found, comment, inside, depth = {}, [], False, 0
    for index, token in enumerate(tokens):
        if not inside:
            if (
                token.type == tokenize.NAME
                and token.string in tables
                and token.start[1] == 0
                and tokens[index + 1].string == "="
            ):
                inside = True
            continue
        if token.type == tokenize.OP and token.string in "([{":
            depth += 1
        elif token.type == tokenize.OP and token.string in ")]}":
            depth -= 1
            if depth == 0:
                inside, comment = False, []
        elif token.type == tokenize.COMMENT:
            comment.append(token.string.lstrip("#").strip())
        elif token.type == tokenize.STRING:
            found[ast.literal_eval(token.string)] = " ".join(comment)
            comment = []
    return found


# --- the catalogue and the four parts of a refusal ---


@dataclasses.dataclass(frozen=True, kw_only=True)
class CatalogueEntry:
    """The entry of one rule of the package: the rule, its vocabulary, the
    operation that refuses under it, its condition, its example, the four
    parts of the refusal the example provokes, and that refusal as printed.

    `rule` is the rule's name, the fragment of its entry on the published
    page, and `vocabulary` the closed vocabulary it belongs to, `graph
    construction`, `the names of the pieces` or `the Bellman factory`;
    `operation` is the operation that refuses under the rule, as `operation`
    reads it; `condition` is the claim the rule states, as `claims` reads
    it; `example` is the rule's `Example` of `bellman.refusal_examples`,
    None where the table holds none. `where`, `what`, `why` and `write` are
    the four parts of the refusal the example provokes, as the module
    docstring describes them, and `refusal` is that refusal as a reader
    meets it; where the example is not run or provokes no refusal, `refusal`
    and three of the parts are empty and `why` holds the reason. `corrected`
    is the outcome of the example's corrected form run through the operation
    that refused the example: empty where it passes; otherwise `still
    refused:` and the first line of the refusal it still provokes, or `not
    run:` and the reason, which the printed entry then shows. The printed
    entry labels the four parts as those of the package's example, since
    they stand beside a refusal of the reader's own file in the Workbench."""

    rule: str
    vocabulary: str
    operation: str
    condition: str
    example: object
    where: str
    what: str
    why: str
    write: str
    refusal: str
    corrected: str = ""

    def __str__(self):
        named = f"{self.vocabulary}; {self.operation}" if self.operation else self.vocabulary
        lines = [f"{self.rule}  ({named})"]
        if self.condition:
            lines.append(f"  condition  {self.condition}")
        if self.refusal:
            lines += [
                "  example  the package's example of the rule, and the refusal it provokes:",
                f"  where  {self.where}",
            ]
        if self.what:
            lines += ["  what", self.what]
        lines.append(f"  why    {self.why}")
        if self.write:
            lines.append(f"  write  {self.write}")
        if self.corrected:
            lines.append(f"  corrected  {self.corrected}")
        return "\n".join(lines)

    __repr__ = __str__


class Catalogue(tuple):
    """Every rule of the three vocabularies with its entry, in the order the
    vocabularies write them; a tuple of `CatalogueEntry` records that prints
    as the catalogue of the rules."""

    def __str__(self):
        return "\n\n".join(str(entry) for entry in self)

    __repr__ = __str__


def catalogue():
    """Every rule of the three vocabularies with its entry (`entry`), in the
    order the vocabularies write them, each rule's example run and its
    corrected form run through the operation that refused the example."""
    return Catalogue(entry(rule) for _, _, table in VOCABULARIES for rule in table)


def entry(rule):
    """The entry of one rule, a `CatalogueEntry`: its vocabulary, the
    operation that refuses under it, its condition, its example and the four
    parts of the refusal the example provokes, from the installed package,
    that example alone run and its corrected form run through the operation
    that refused it. A rule whose example is not run (`_not_run`), and one
    whose example provokes no refusal, is answered with the reason in place
    of the parts, so that the catalogue names it rather than passing over
    it. A name no vocabulary holds, such as the rule of a check an
    elaboration records without refusing, `unread-input`, has no entry:
    None."""
    vocabulary = next((words for words, _, table in VOCABULARIES if rule in table), None)
    if vocabulary is None:
        return None
    example = EXAMPLES.get(rule)
    parts = dict(
        rule=rule,
        vocabulary=vocabulary,
        operation=operation(rule),
        condition=claims().get(rule, ""),
        example=example,
    )
    reason = _not_run(example)
    refusal = None if reason else refusal_of(example)
    if refusal is None:
        return CatalogueEntry(
            **parts,
            where="",
            what="",
            why=reason or "the example provokes no refusal",
            write="",
            refusal="",
        )
    return CatalogueEntry(
        **parts,
        refusal=str(refusal),
        corrected=still_refused(example),
        **_four_parts(example, refusal),
    )


def refusal_of(example):
    """The refusal `example` provokes, or None where the package does not
    refuse it."""
    try:
        _provoke(example)
    except (ConstructionError, TargetError, FactoryError) as refused:
        return refused
    return None


def still_refused(example):
    """What the corrected form of `example` provokes when it is run through
    the operation that refused the example: the empty string where it
    passes; `still refused:` and the first line of the refusal where the
    package still refuses it; and `not run:` and the reason where the form
    reads a stage file this installation does not hold, the table gives no
    corrected form or the operation fails for another reason."""
    try:
        form = corrected(example)
        reason = _not_run(form)
        refusal = None if reason else refusal_of(form)
    except Exception as error:  # the table's gap or the operation's own failure
        first = str(error).splitlines()[0] if str(error) else ""
        return f"not run: {type(error).__name__}: {first}"
    if reason:
        return f"not run: {reason}"
    return "" if refusal is None else f"still refused: {str(refusal).splitlines()[0]}"


def _not_run(example):
    """Why `example` is not run, or the empty string where it is: the table
    holds no example of the rule, or the example reads a stage file of the
    repository that `ROOT` does not hold, as an installation outside the
    checkout holds none (`_repository_files`)."""
    if example is None:
        return "no example of this rule stands in the table"
    absent = [path for path in _repository_files(example) if not (ROOT / path).is_file()]
    if absent:
        return (
            f"the example reads the stage file {absent[0]} of the repository, which this "
            f"installation does not hold"
        )
    return ""


def _repository_files(example):
    """The stage files of the repository `example` reads, each a path from
    the repository's root: the corpus stage its text changes, the corpus
    stages of its one period, and the path it gives `load_stage` where that
    path is a corpus stage's."""
    files = [CORPUS.get(example.corpus, example.corpus)] if example.corpus else []
    files += [CORPUS[name] for name in example.stages.values()]
    if example.path in CORPUS.values():
        files.append(example.path)
    return files


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
            why=refusal.message,
            write=refusal.write or "",
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
    write = refusal.write or ""
    written = getattr(refusal, "parts", None)
    if written is not None:
        # `syntax.parse.syntax_refusal` stores the two parts of a refusal
        # under the rule `syntax` on the refusal, and they are read there
        return dict(where=where, what=written.what, why=written.why, write=write)
    # a refusal at a line of an addition marks the addition's text
    what = (
        ""
        if refusal.line is None
        else marked_line(_text_in(example, refusal.file), refusal.line, refusal.column)
    )
    return dict(where=where, what=what, why=refusal.message, write=write)


def _text_in(example, file):
    """The text of the example's file `file`: the text of the addition among
    its `additions` that stands at that origin, and the stage text
    otherwise."""
    held = (text for origin, text in _additions_of(example) if origin == file)
    return next(held, text_of(example))


# --- the calls that provoke a refusal ---

# the name by which a refusal of an example addresses the example registry,
# whatever directory holds it
REGISTRY_NAME = "registry"


# The root of the repository, from which an example reads a stage file of
# `CORPUS`: the variable the repository's commands export, and otherwise the
# checkout this package stands in. An installation outside the checkout
# holds no such file, and the entry of such an example gives the reason in
# place of the four parts (`_not_run`).
ROOT = Path(os.environ.get("BELLMAN_DDSL_ROOT") or Path(__file__).resolve().parents[3])


def _provoke(example):
    """Ask of the example's stage, registry or trellis what its rule refuses:
    the call `_PROVOKERS` holds for the example's word `provokes`."""
    if example.provokes not in _PROVOKERS:
        raise ValueError(f"{example.provokes!r} is no way of provoking a refusal")
    _, call = _PROVOKERS[example.provokes]
    return call(example)


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


def _same_version(example):
    """The kernel, on the example's stage, of the first operator box of that
    same stage: the call `other-version` refuses, made as the version admits
    it."""
    stage = _stage(example)
    return kernel(stage, operators_of(stage)[0])


def _stage_path(path):
    """The path `load_stage` reads for an example: a path that names a file
    of the repository is read from the repository root, and any other path
    as written, so that a path refused before it is opened names no
    directory of the machine."""
    return ROOT / path if (ROOT / path).is_file() else path


def _methodized(example):
    """The example's stage methodized with the addition `methods`, a mapping
    holding its text and its origin. The stage is elaborated anew, since
    `methodize` binds the stage it is called on."""
    return methodize(_fresh_stage(example), example.methods)


def _fresh_stage(example):
    """The stage the example's text constructs, elaborated anew for a verb
    that binds it."""
    return elaborate_text(text_of(example), example.origin)


def _unioned(example):
    """The example's stage text elaborated with its additions unioned into it,
    each the origin and the text of a methods file (specification 0.7 §4);
    the stage text itself stands in the file `t.bl`."""
    return elaborate_stage(
        {
            "stage": {"text": text_of(example), "origin": "t.bl"},
            "calibration": {},
            "settings": {},
            "methods": [
                {"text": text, "origin": origin} for origin, text in _additions_of(example)
            ],
        }
    )


def _other_version(example):
    """The kernel, on the example's stage, of a box of a second version of
    that stage, a stage of the same text elaborated anew and calibrated,
    since `calibrate` binds the stage it is called on."""
    stage = _stage(example)
    return kernel(stage, operators_of(_fresh_stage(example).calibrate({"ρ": 2.0}))[0])


# Each word an example's `provokes` may hold, with the operation that
# refuses under the example's rule and the call that provokes its refusal.
# The operation is the word of the Workbench for what it runs, `elaborate`,
# `methodize`, `configure`, `connect` or `read`, where an author meets the
# refusal through an operation of the Workbench, and `query` where a Python
# caller meets it through a query of the stage object, whichever query the
# example makes, since several queries refuse under one such rule
# (`operation`).
_PROVOKERS = {
    "load_recipe": (
        "read",
        lambda example: _from_registry(
            example, lambda directory: load_recipe(directory, example.recipe, **example.fills)
        ),
    ),
    "assemble_trellis": (
        "connect",
        lambda example: _from_registry(
            example,
            lambda directory: assemble_trellis(directory, example.recipe, **example.fills),
        ),
    ),
    "load_trellis": (
        "read",
        lambda example: _from_registry(
            example, lambda directory: load_trellis(directory / example.file)
        ),
    ),
    "elaborate_stage": ("elaborate", lambda example: elaborate_stage(example.record)),
    "load_stage": ("read", lambda example: load_stage(_stage_path(example.path))),
    "elaborate_trellis": ("connect", _one_period),
    "forward_order": ("connect", _one_period_order),
    "elaborate": ("elaborate", _stage),
    "compile_kernel": (
        "query",
        lambda example: compile_kernel(_stage(example), example.target),
    ),
    "kernel": ("query", lambda example: kernel(_stage(example), example.target)),
    "card": ("query", lambda example: card(_stage(example), example.target)),
    "methodize": ("methodize", _methodized),
    "configure-option": (
        "configure",
        lambda example: methodize(_fresh_stage(example), example.methods).configure(
            example.settings
        ),
    ),
    "configure-addition": (
        "configure",
        lambda example: _unioned(example).configure(example.settings),
    ),
    "other-version": ("query", _other_version),
    "same-version": ("query", _same_version),
    "union": ("elaborate", _unioned),
}


# --- the stage text of an example, and its registry ---


def text_of(example):
    """The stage text of `example`: the text it writes, or the stage file it
    names with its changes applied, and then its `edits` that fall on the
    stage text. A line the file no longer holds is refused, so that a change
    to a stage file is read here and not silently dropped."""
    return _edited_texts(example)[0]


def _additions_of(example):
    """The additions of `example`, each its origin and its text, with the
    `edits` that fall on an addition applied."""
    return _edited_texts(example)[1]


def _edited_texts(example):
    """The stage text and the additions of `example` with its `edits`
    applied: each (line as written, line as changed) pair falls on the one
    text, among the stage text and the additions, that holds the line once,
    and a line no text or several texts hold once is refused."""
    if example.corpus:
        text = _corpus_text(example.corpus)
        for written, changed in example.changes:
            if text.count(written) != 1:
                raise ValueError(f"{example.corpus} no longer holds the line {written!r} once")
            text = text.replace(written, changed)
    else:
        text = example.text
    texts = [text] + [held for _, held in example.additions]
    for written, changed in example.edits:
        holders = [index for index, held in enumerate(texts) if held.count(written) == 1]
        if len(holders) != 1:
            raise ValueError(
                f"the example of {example.rule!r} holds the line {written!r} once in "
                f"{len(holders)} of its texts, and an edit falls on one"
            )
        texts[holders[0]] = texts[holders[0]].replace(written, changed)
    additions = tuple((origin, held) for (origin, _), held in zip(example.additions, texts[1:]))
    return texts[0], additions


# the examples share their stage texts, so a text is elaborated once for the
# catalogue; the reader is the factory's one `elaborate_text`
_stage_of_text = functools.lru_cache(maxsize=8)(elaborate_text)


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
