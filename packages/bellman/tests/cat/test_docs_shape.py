"""The acceptance file of lane D of the internal developer release 0.01, the
documentation's shape and the reference catalogues (the second layer of the
tests, `packages/bellman/README.md` §8): one test for each item of the lane's
brief, `docs-shape-and-reference.md` §7, that a test closes, items 1 to 4,
each carrying the item of the documentation's architecture
(`docs-architecture.md` §5) it absorbs. Items 5 and 6 are readings: the
merged narrative of `overview/05-semantics.md` reviewed by `econ-tribe`, and
AAS reading the operations page and one API page beside what the package
prints. The last clause of item 1, that `mkdocs build --strict` passes, is
closed by no test here either: the strict build, `mkdocs build --strict`,
runs at the lane's acceptance beside the suite and not in it. Nor is the
first clause of item 4, that the retired pages stand in the private archive
with README rows and digests: the archive stands outside the repository, and
the lane's acceptance reads its README rows and SHA256SUMS digests. Item 2
is one of the suite's sweeps and runs with `-m sweep`, since its two scripts
elaborate every stage file under `applications/`.

A page is a markdown file under `docs/` other than a snippet, whose name
starts with `_`, a file under a folder whose name starts with `_`, and a file
under a folder named `old`, which `.gitignore` keeps outside git
(`LEFTOVER`). A page belongs to one part by its folder (architecture §2) and
carries that part's tag in the `tags:` list of its front matter,
`docs/<part>`, written without the `#` as the project's rules on tags write a
front-matter tag. The decision records, which stood under `docs/decisions/`
and belonged to no part, stand in the internal folder since 29 September
2026, which closes question 18 of the decisions record: no test here reads
them, and `tests/test_decision_records.py` checks that each documentation
page and wiki entry a record names exists.

The lists named `…_TODAY` hold what stands on `main` when lane D builds and
another lane or the coordinator changes: each entry is named, one by one, and
an entry that no longer holds fails the test, so that the list shrinks with
the work that empties it.
"""

from __future__ import annotations

import posixpath
import re
import subprocess
import sys
import warnings
from collections import Counter
from pathlib import PurePosixPath

import pytest
import yaml
from conftest import ROOT, methodized
from markdown.extensions.toc import slugify

from bellman.distributions.families import FAMILY_ARGUMENTS
from bellman.fold.table import KINDS
from bellman.refusals import FACTORY_RULES, RULES, TARGET_RULES
from bellman.stage.method_table import METHOD_TYPES
from bellman.typing.primitive_definitions import PRIMITIVE_DEFINITIONS

DOCS = ROOT / "docs"
HOOKS = DOCS / "_hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))

# the markers, the table reader and the row anchor of the generator that
# writes the pages
from reference_pages import MARKERS, methods_table, names, table_cells  # noqa: E402
from reference_pages import anchor_of as row_anchor  # noqa: E402

from bellman.native.hypergraphs import copy_native  # noqa: E402
from bellman.native.records import (  # noqa: E402
    NO_REGISTERED_ARGUMENTS,
    OMISSIONS,
    EntryText,
    MethodOption,
)
from bellman.refusals import ConstructionError  # noqa: E402
from bellman.stage.grids import GRID_CONSTRUCTORS  # noqa: E402
from bellman.stage.representations import (  # noqa: E402
    RepresentationFamily,
    families,
    register,
    unregister,
)

# a folder named `old` under docs/ is passed over wherever the test reads
# docs/: `.gitignore`'s `**/old/` keeps such a folder outside git, so it
# stands only as a leftover of a checkout and never in a clone
LEFTOVER = "old"

# --- the parts and their pages (architecture §§1, 2 and 4) ---

# the eleven children of the part tag
PARTS = (
    "home",
    "overview",
    "guide",
    "api",
    "appendix",
    "reference",
    "calculus",
    "example",
    "asva",
    "wiki",
    "about",
    "changelog",
)
# the part of a page by its folder, the first entry that holds it deciding:
# a path under docs/ that equals the entry or starts with it
FOLDER_PARTS = (
    ("index.md", "home"),
    ("changelog.md", "changelog"),
    ("about.md", "about"),
    ("overview/", "overview"),
    ("Bellman-Sym/API/", "api"),
    ("Bellman-Sym/appendices/", "appendix"),
    ("Bellman-Sym/reference/", "reference"),
    ("bellman-calculus/", "calculus"),
    ("examples/", "example"),
    ("asva/", "asva"),
    ("wiki/", "wiki"),
)
# the pages lane D writes or moves, which carry their part tag at its
# acceptance; every other page may still lack its tag until the follow-up
# after the release (question 19, deferred by AAS on 28 September), and the
# test counts it
LANE_D_PAGES = ("Bellman-Sym/API/", "Bellman-Sym/reference/", "overview/05-semantics.md")

# what docs/Bellman-Sym/ holds besides its root pages (brief §7 item 1, as
# DR2 corrected it)
BELLMAN_SYM_FOLDERS = ("API", "appendices", "reference", "figures", "img")

# the pages and folders lane D retires to the private archive (brief §§1-3, DR1,
# DR2): no page of them stands under docs/, and no page links to them; a
# folder named `old` among them stands outside git, and item 4 passes over it
# when it asks what stands (`LEFTOVER`)
RETIRED = (
    "Bellman-Term/",
    "semantics/",
    "Bellman-Sym/old/",
    "Bellman-Sym/reference/old/",
    # the calculus's `old/` (2 pages) and `catalogues/old/` (1), which the
    # row of the architecture's §2 for the calculus's excluded and stray
    # pages sends to the private archive under lane D
    "bellman-calculus/old/",
    "bellman-calculus/catalogues/old/",
    "Bellman-Sym/reference/primitives.md",
    "Bellman-Sym/reference/dolang_plus_schema.md",
    "bellman-calculus/catalogues/methods.md",
    # the moves of lane D's last commit (architecture §2): page 02, cut into
    # the nine pages of API/stage/ and retired to the private archive, and the
    # folder of the factory pages, whose five pages moved to API/factory/
    "Bellman-Sym/02-the-stage-object.md",
    "Bellman-Sym/syntax-API/",
)
# lane D's pattern for the sweep of the plan's §3, over its scope: docs/
# without the changelog, the site's scripts under docs/_hooks/ included,
# tutorials/, applications/ and the file AGENTS.md (CLAUDE.md is a symbolic
# link to it); the rule files are not read, since this sweep leaves the
# internal folder out (PL13), and the lane's acceptance sweeps them once by
# hand (BN62); the decision records, which quote the rules of their time
# (RH200), were left out while they stood under docs/decisions/, and stand in
# the internal folder since 29 September 2026
SWEEP = re.compile(
    r"Bellman-Term|reference/primitives\.md|docs/semantics|syntax-API|02-the-stage-object"
)
SWEPT = ("docs", "tutorials", "applications", "AGENTS.md")
# the text files the sweep reads in a folder, the lessons with their outputs
# and the stage files of the applications among them
SWEPT_SUFFIXES = (".md", ".ipynb", ".py", ".yml", ".yaml", ".txt", ".html", ".js", ".bl")

# --- the navigation (architecture §3) ---

# the parts of the navigation, in order, each a part of a page; AAS renamed
# Overviews, Bellman-SYM and Bellman calculus to Overview, Language and
# Foundations and added About us on 30 September 2026 (513896b71, 0025816ac)
NAV_PARTS = {
    "Home": "home",
    "Overview": "overview",
    "Language": "guide",
    "Foundations": "calculus",
    "Examples": "example",
    "Asva": "asva",
    "Wiki": "wiki",
    "About us": "about",
    "Changelog": "changelog",
}
# the groups under Language after its index page, in order
LANGUAGE_GROUPS = {
    "User guide": "guide",
    "API": "api",
    "Appendices": "appendix",
    "Reference": "reference",
}
# the pages that stand outside the navigation on main when lane D builds: the
# pages of question 16 of the decisions record, the HARK experiments and the
# output under housing_renting/converged_output/,
# wait for the follow-up after the release, "After the internal developer
# release 0.01: what waits", AAS having deferred the question on 28 September;
# the wiki's entries and the two formal pages that the architecture's §2
# sends into the navigation stand there since lane W's acceptance
OUTSIDE_THE_NAV_TODAY = (
    "examples/HARK-models-lean-experimental/ConsExtMargMed_mdp.md",
    "examples/HARK-models-lean-experimental/ConsGenIncProcess_mdp.md",
    "examples/HARK-models-lean-experimental/ConsIndShock_mdp.md",
    "examples/HARK-models-lean-experimental/ConsKinkedR_mdp.md",
    "examples/HARK-models-lean-experimental/ConsKinkyPref_mdp.md",
    "examples/HARK-models-lean-experimental/ConsLaborIntMarg_mdp.md",
    "examples/HARK-models-lean-experimental/ConsMarkov_mdp.md",
    "examples/HARK-models-lean-experimental/ConsMedShock_mdp.md",
    "examples/HARK-models-lean-experimental/ConsPerfForesight_mdp.md",
    "examples/HARK-models-lean-experimental/ConsPerfForesight_simple_mdp.md",
    "examples/HARK-models-lean-experimental/ConsPortfolio_mdp.md",
    "examples/HARK-models-lean-experimental/ConsPrefShock_mdp.md",
    "examples/HARK-models-lean-experimental/ConsRiskyAsset_mdp.md",
    "examples/HARK-models-lean-experimental/consumer_mdp.md",
    "examples/housing_renting/converged_output/non_convergence_report.md",
    "examples/housing_renting/converged_output/owner_cons.md",
    "examples/housing_renting/converged_output/owner_housing.md",
    "examples/housing_renting/converged_output/renter_cons.md",
    "examples/housing_renting/converged_output/renter_housing.md",
    "examples/housing_renting/converged_output/tenure_choice.md",
)

# --- the reference catalogues (brief §§3 and 4) ---

REFERENCE_PAGES = tuple(
    f"Bellman-Sym/reference/{name}.md"
    for name in ("operations", "laws", "forms", "methods", "refusals")
)
E3 = "bellman-calculus/catalogues/operators.md"
# the kinds DR3 retires, which Appendix E.3 names nowhere
RETIRED_KINDS = ("Selection", "Inversion", "Solution")
# the names E.3's operator table gave two kinds before DR3 renamed its rows to
# the kinds that realize them, which no row of that table keeps
RENAMED_ROWS = {"evaluate": "PolicyInsertion", "Function evaluation": "Evaluation"}
# the anchors of the forms rows that DR8 leaves without a link, since E.3
# defines no object for them; every other forms row links one
FORMS_WITHOUT_DENOTES = ("exp", "log", "min", "inv", "arithmetic", "laws")
# the six tables of the package whose entries stand in the reference rows,
# each as the `read from` cell spells it, the three vocabularies of the
# refusals among them
PACKAGE_TABLES = {
    'PRIMITIVE_DEFINITIONS["definitions"]': tuple(PRIMITIVE_DEFINITIONS["definitions"]),
    "FAMILY_ARGUMENTS": tuple(FAMILY_ARGUMENTS),
    "METHOD_TYPES": tuple(METHOD_TYPES),
    "RULES": tuple(RULES),
    "TARGET_RULES": tuple(TARGET_RULES),
    "FACTORY_RULES": tuple(FACTORY_RULES),
}

# --- the direction of the links (architecture §1 and §5 item 4) ---

# the lines of a page's intro box whose links may run from the calculus into
# the language, each by the label that opens it in bold
SANCTIONED_LABELS = ("Builds on", "Used by")
# the links that run from docs/bellman-calculus/ into docs/Bellman-Sym/
# outside the sanctioned lines: none since lane W repointed each one to the
# wiki entry of its term, moved it to its page's `Used by` line or removed it
# (question 15 of the decisions record); an entry
# here, as (the page under docs/, the text of the link, its target as
# written), would allow one such link in a page's body
BODY_LINKS_TODAY = ()
# the links on a line of the intro box other than `Builds on` and `Used by`:
# none since lane W relabeled those lines `Used by` (question 15)
BOX_LINKS_TODAY = ()


# --- reading the pages ---

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LINK = re.compile(r"(?<!!)\[(?P<text>[^\]\n]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^\s*(```|~~~)")


def leftover(path):
    """Whether a path under docs/, written relative to docs/, is a folder
    named `old` or lies in one, which the test passes over."""
    return LEFTOVER in PurePosixPath(path).parts


def pages():
    """Every page under docs/, as its path under docs/, sorted. A file in a
    folder named `old` is no page (`LEFTOVER`)."""
    found = []
    for path in DOCS.rglob("*.md"):
        relative = path.relative_to(DOCS)
        if any(part.startswith("_") for part in relative.parts) or leftover(relative):
            continue
        found.append(relative.as_posix())
    return sorted(found)


def part_of(page):
    """The part a page belongs to by its folder, or None where no part holds
    that folder."""
    if page.startswith("Bellman-Sym/") and page.count("/") == 1:
        return "guide"
    for folder, part in FOLDER_PARTS:
        if page == folder or (folder.endswith("/") and page.startswith(folder)):
            return part
    return None


def front_matter(text):
    """The front matter of a page as a mapping; empty where it has none."""
    found = FRONT_MATTER.match(text)
    if not found:
        return {}
    return yaml.safe_load(found.group(1)) or {}


def part_tags(text):
    """(the part tags of a page's front matter, the part tags written in its
    text), a tag inside a code span or a fenced block being no tag."""
    listed = front_matter(text).get("tags") or []
    listed = [listed] if isinstance(listed, str) else listed
    front = [str(tag).lstrip("#") for tag in listed if str(tag).lstrip("#").startswith("docs/")]
    body = FRONT_MATTER.sub("", text, count=1)
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    body = re.sub(r"`[^`\n]*`", "", body)
    return front, re.findall(r"(?<![\w/#])#(docs/[\w-]+)", body)


def links(text):
    """(line number, the line, the text, the target) of every markdown link of
    a page outside a fenced block and outside a code span; the text of a link
    may hold a code span."""
    found, fenced = [], False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        spans = [match.span() for match in re.finditer(r"`[^`]*`", line)]
        found += [
            (number, line, m.group("text"), m.group("target"))
            for m in LINK.finditer(line)
            if not any(start < m.start() < end for start, end in spans)
        ]
    return found


def resolved(page, target):
    """The path under docs/ a relative link of a page reaches, its anchor
    apart; None for a link that leaves the site, an anchor on the same page,
    or a link outside docs/."""
    if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
        return None
    path = target.split("#")[0].replace("%20", " ")
    reached = posixpath.normpath(posixpath.join(posixpath.dirname(page), path))
    return None if reached.startswith("..") else reached


def anchor_of(target):
    return target.split("#", 1)[1] if "#" in target else ""


def intro_box(text):
    """The lines of a page's intro box, the callout `[!info]- Relationship
    with other documents`, by their numbers: each with the label in bold that
    opens it, such as `Builds on`, or an empty label where none opens it. The
    box runs from its title line over the lines that start with `>`."""
    box, inside = {}, False
    for number, line in enumerate(text.splitlines(), start=1):
        if re.match(r">\s*\[!info\]-?\s*Relationship", line):
            inside = True
        elif inside and not line.startswith(">"):
            inside = False
        if inside:
            label = re.match(r">\s*\*\*([^*]+)\*\*", line)
            box[number] = label.group(1).strip() if label else ""
    return box


def mkdocs():
    """The site's configuration, a tag of Python's own ignored."""

    class Loader(yaml.SafeLoader):
        pass

    Loader.add_multi_constructor("tag:yaml.org,2002:python/", lambda loader, suffix, node: None)
    return yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=Loader)


def patterns(block):
    """The patterns of an `exclude_docs` or `not_in_nav` block, comments
    aside."""
    return [
        line.strip()
        for line in (block or "").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def matches(page, pattern):
    """Whether a page under docs/ matches one pattern of the site's
    configuration, in the gitignore form it is written in: a leading `/`
    anchors it at docs/, a trailing `/` names a folder, `**` any depth."""
    anchored = pattern.startswith("/")
    pattern = pattern.strip("/") + ("/**" if pattern.endswith("/") else "")
    expression = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    if anchored or "/" in pattern:
        return re.fullmatch(expression, page) is not None
    return re.fullmatch(expression, page.rsplit("/", 1)[-1]) is not None


def nav_entries(items, trail=()):
    """(the titles above it, the page) of every page the navigation names."""
    found = []
    for item in items:
        if isinstance(item, str):
            found.append((trail, item))
            continue
        for title, value in item.items():
            if isinstance(value, str):
                found.append((trail + (title,), value))
            else:
                found += nav_entries(value, trail + (title,))
    return found


def region(text):
    """What stands between the two markers of a page, or None."""
    if text.count(MARKERS[0]) != 1 or text.count(MARKERS[1]) != 1:
        return None
    start, end = text.index(MARKERS[0]) + len(MARKERS[0]), text.index(MARKERS[1])
    return text[start:end] if start <= end else None


def table_rows(text):
    """The rows of the table between the markers of a page, each a mapping
    from the column's head to the cell."""
    held = region(text)
    if held is None:
        return None
    rows = [cells for cells in map(table_cells, held.splitlines()) if cells]
    head, body = rows[0], rows[1:]
    return [dict(zip(head, row)) for row in body]


# the line that opens an entry of the methods page: its anchor, then, after
# one empty line, its numbered heading with the word
ENTRY = re.compile(r'^<a id="([^"]+)"></a>\n\n### \d+\.\d+ `(![^`]+)`$', re.MULTILINE)
PART = re.compile(r"^\*\*([A-Z][a-z]+(?: [a-z]+)*)\.\*\*", re.MULTILINE)


def reference_entries(text):
    """The entries of the generated part of the methods page, in order, each
    as (its anchor, its word with the `!`, its parts by label, each part's
    text from its label to the next label, and the rows of its argument
    table)."""
    held = region(text) if MARKERS[0] in text else text
    found = list(ENTRY.finditer(held))
    entries = []
    for number, match in enumerate(found):
        end = found[number + 1].start() if number + 1 < len(found) else len(held)
        body = held[match.end():end]
        body = re.split(r"^## ", body, flags=re.MULTILINE)[0]
        labels = list(PART.finditer(body))
        parts = {
            label.group(1): body[
                label.end():(labels[index + 1].start() if index + 1 < len(labels) else len(body))
            ].strip()
            for index, label in enumerate(labels)
        }
        arguments = [
            cells for cells in map(table_cells, parts.get("Arguments", "").splitlines()) if cells
        ][1:]
        entries.append((match.group(1), match.group(2), parts, arguments))
    return entries


def entry_rows(text):
    """The entries of the methods page as the rows the checks of the
    catalogues read: the word with its anchor, the places it is bound at,
    its `denotes` link and its `read from` reference."""
    rows = []
    for anchor, word, parts, _ in reference_entries(text):
        links = parts.get("Links", "").split("; ")
        rows.append(
            {
                "method": f'<a id="{anchor}"></a>`{word}`',
                "bound at": parts.get("Declaration", ""),
                "denotes": next((part for part in links if part.startswith("denotes ")), ""),
                "read from": next((part for part in links if part.startswith("read from ")), ""),
            }
        )
    return rows


def slug(heading):
    """The anchor MkDocs gives a heading."""
    return slugify(heading, "-")


def e3_sections(text):
    """The anchors of the sections of Appendix E.3, each with the first cells
    of the table rows it holds: an `<a id>` line above a heading and the
    heading's own anchor both reach the section."""
    sections, pending, current = [], None, None
    for line in re.sub(r"```.*?```", "", text, flags=re.DOTALL).splitlines():
        found = re.fullmatch(r'\s*<a id="([^"]+)"></a>\s*', line)
        if found:
            pending = found.group(1)
            continue
        heading = re.match(r"#{2,6}\s+(.*\S)", line)
        if heading:
            current = {
                "anchors": {slug(heading.group(1))} | ({pending} if pending else set()),
                "heading": heading.group(1),
                "cells": [],
            }
            sections.append(current)
            pending = None
            continue
        if line.strip():
            pending = None
        cells = table_cells(line)
        if cells and current is not None:
            current["cells"].append(cells[0])
    return sections


def reported(problems):
    return "\n".join(f"- {problem}" for problem in problems)


# --- the items ---


def test_item_1_the_folders_the_part_tags_and_the_navigation_follow_the_architecture():
    """Brief §7 item 1 with architecture items 1 and 2: docs/Bellman-Sym/ holds
    its root pages, index.md and the five folders and nothing else: index.md
    and each of the five folders stand there, no folder stands there but the
    five, a folder named `old` being passed over (`LEFTOVER`), and no file
    stands directly under it but a markdown page, a file whose name starts
    with `.`, such as the `.DS_Store` file Finder writes in a checkout, being
    passed over; docs/Bellman-Term/ and docs/semantics/ are gone; every page
    belongs to one part by its folder and carries no part tag but its own,
    the pages of lane D carrying theirs; the navigation names every page of
    the site once, in its part, in the order of the architecture's §3 and no
    retired page; the wiki's index names every entry; and only the snippets,
    the excluded pages and the pages of `OUTSIDE_THE_NAV_TODAY` stand outside
    it. The item's last clause, that
    `mkdocs build --strict` passes, is closed by the strict build,
    `mkdocs build --strict`, which runs at the lane's acceptance beside the
    suite and not in it."""
    problems = []
    held = {
        entry.name
        for entry in (DOCS / "Bellman-Sym").iterdir()
        if entry.is_dir() and not leftover(entry.name)
    }
    for folder in sorted(held - set(BELLMAN_SYM_FOLDERS)):
        problems.append(f"docs/Bellman-Sym/{folder}/ is no folder of the four parts (DR2)")
    for folder in BELLMAN_SYM_FOLDERS:
        if folder not in held:
            problems.append(
                f"docs/Bellman-Sym/{folder}/ does not exist, and brief §7 item 1 names it"
            )
    # a markdown file directly under the folder is a root page, whose place
    # the navigation check judges; a name that starts with `.` is passed over
    for entry in sorted((DOCS / "Bellman-Sym").iterdir()):
        if entry.is_file() and not entry.name.startswith(".") and entry.suffix != ".md":
            problems.append(
                f"docs/Bellman-Sym/{entry.name} is neither a root page nor a folder of the "
                f"four parts"
            )
    if not (DOCS / "Bellman-Sym" / "index.md").is_file():
        problems.append("docs/Bellman-Sym/index.md, the index of the four parts, does not exist")
    for gone in ("Bellman-Term", "semantics"):
        if (DOCS / gone).exists():
            problems.append(f"docs/{gone}/ still stands")

    lacking = []
    for page in pages():
        part = part_of(page)
        if part is None:
            problems.append(f"{page} belongs to no part of the architecture's §2 by its folder")
            continue
        try:
            front, inline = part_tags((DOCS / page).read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            problems.append(f"{page}: the front matter does not read as YAML ({error})")
            continue
        own = f"docs/{part}"
        for tag in sorted(set(front + inline) - {own}):
            named = "a tag" if tag.split("/", 1)[1] in PARTS else "a tag of no part"
            problems.append(f"{page} is a page of the part {part} and carries {named}, {tag}")
        if len(front) > 1:
            problems.append(f"{page} lists {len(front)} part tags in its front matter")
        if own not in front:
            if page.startswith(LANE_D_PAGES):
                problems.append(f"{page} is a page lane D writes and lacks its part tag {own}")
            else:
                lacking.append(page)
    if lacking:
        warnings.warn(
            f"{len(lacking)} of {len(pages())} pages under docs/ lack their part tag; they "
            f"receive it in the follow-up after the release, question 19 of the decisions record "
            f"being deferred (architecture §4)",
            stacklevel=1,
        )

    config = mkdocs()
    excluded = patterns(config.get("exclude_docs"))
    not_in_nav = patterns(config.get("not_in_nav"))
    entries = [
        (trail, page)
        for trail, page in nav_entries(config["nav"])
        if not re.match(r"[a-z][a-z0-9+.-]*://", page)
    ]  # a link that leaves the site is no page
    named = Counter(page for _, page in entries)
    for page, count in named.items():
        if count > 1:
            problems.append(f"the navigation names {page} {count} times")
        if not (DOCS / page).is_file():
            problems.append(f"the navigation names {page}, which does not exist")
        if page.startswith(RETIRED):
            problems.append(f"the navigation names the retired page {page}")
    titles = [trail[0] for trail, _ in entries if trail]
    if list(dict.fromkeys(titles)) != list(NAV_PARTS):
        problems.append(
            f"the navigation's parts are {list(dict.fromkeys(titles))}, and the architecture's "
            f"§3 orders them {list(NAV_PARTS)}"
        )
    groups = [trail[1] for trail, _ in entries if trail[:1] == ("Language",) and len(trail) > 1]
    if list(dict.fromkeys(groups)) != list(LANGUAGE_GROUPS):
        problems.append(
            f"Language holds the groups {list(dict.fromkeys(groups))}, and the architecture's "
            f"§3 holds {list(LANGUAGE_GROUPS)}"
        )
    for trail, page in entries:
        if not trail:
            continue
        expected = (
            LANGUAGE_GROUPS.get(trail[1])
            if trail[0] == "Language" and len(trail) > 1
            else NAV_PARTS.get(trail[0])
        )
        if expected is not None and part_of(page) != expected:
            problems.append(
                f"the navigation holds {page}, a page of the part {part_of(page)}, under "
                f"{' / '.join(trail)}"
            )
    outside = [
        page
        for page in pages()
        if page not in named
        and not any(matches(page, pattern) for pattern in excluded + not_in_nav)
    ]
    for page in sorted(set(outside) - set(OUTSIDE_THE_NAV_TODAY)):
        problems.append(f"{page} stands outside the navigation")
    for page in sorted(set(OUTSIDE_THE_NAV_TODAY) - set(outside)):
        problems.append(
            f"{page} is now in the navigation or gone; delete it from OUTSIDE_THE_NAV_TODAY"
        )

    index = (DOCS / "wiki/index.md").read_text(encoding="utf-8")
    listed = {resolved("wiki/index.md", target) for _, _, _, target in links(index)}
    for page in pages():
        if page.startswith("wiki/") and page != "wiki/index.md" and page not in listed:
            problems.append(f"the wiki's index names no link to {page}")
    if problems:
        pytest.fail("\n" + reported(problems), pytrace=False)


# the two scripts elaborate every stage file under applications/, assemble
# the two-stage durables trellis whole and print the refusal catalogue, so the
# test is one of the sweeps
@pytest.mark.sweep
def test_item_2_every_generated_table_and_listing_is_what_its_script_prints():
    """Brief §7 item 2 and architecture item 3: `reference_pages.py --check`
    finds every reference page's table and the API index's table as the
    package writes them, and `stage_object_page.py --check` every listing of
    the API pages and the reference pages as the package prints it."""
    for script in ("reference_pages.py", "stage_object_page.py"):
        run = subprocess.run(
            [sys.executable, str(HOOKS / script), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert run.returncode == 0, f"{script} --check\n{run.stdout}\n{run.stderr}"


def test_item_3_the_catalogues_relate_the_package_to_appendix_e3():
    """Brief §7 item 3 and DR3: every `denotes` link of a reference row
    resolves to a section of Appendix E.3; every row of the operations and
    the laws links one, and so does every row of the methods whose `bound at`
    cell names an operator, since a method whose places name none is bound
    on a whole builder, whose direction the method table does not state, and
    every row of the forms whose anchor `FORMS_WITHOUT_DENOTES` does not
    name, E.3 defining the object of each such row (DR8);
    every entry of `PRIMITIVE_DEFINITIONS`, `FAMILY_ARGUMENTS`,
    `METHOD_TYPES` and the three vocabularies of the refusals, `RULES`,
    `TARGET_RULES` and `FACTORY_RULES`, stands in exactly one reference row,
    and no row names an entry the table lacks; every `realized by` link of E.3
    reaches a row of the operations page's table, the link in a row of E.3's
    tables whose first cell names a kind reaches that kind's row, and no
    kind's row is reached by more than one link, the architecture's §1
    sanctioning one `realized by` link per kind; a link on the `Builds on` or
    `Used by` line of E.3's intro box, which item 4 sanctions, and a link
    without an anchor reach the page and no row, and are not judged (DR80);
    and E.3 names every kind of a card's row,
    `fold/table.py`'s `KINDS`, in the first cell of exactly one table row, no
    retired kind anywhere, and none by the name DR3 renamed."""
    problems = []
    e3 = (DOCS / E3).read_text(encoding="utf-8")
    sections = e3_sections(e3)
    anchors = {anchor for section in sections for anchor in section["anchors"]}
    stood = Counter()
    for page in REFERENCE_PAGES:
        path = DOCS / page
        reader = entry_rows if page.endswith("/methods.md") else table_rows
        rows = reader(path.read_text(encoding="utf-8")) if path.is_file() else None
        if rows is None:
            problems.append(
                f"{page} holds no table between the markers {MARKERS[0]} and {MARKERS[1]}"
            )
            continue
        name = page.rsplit("/", 1)[-1]
        for row in rows:
            cell = row.get("denotes", "")
            found = links(cell)
            must_link = (
                name in ("operations.md", "laws.md")
                or (name == "methods.md" and re.search(r"\boperator\b", row.get("bound at", "")))
                or (
                    name == "forms.md"
                    and (anchor := re.search(r'<a id="([^"]+)"></a>', row[next(iter(row))]))
                    is not None
                    and anchor.group(1) not in FORMS_WITHOUT_DENOTES
                )
            )
            if not found and must_link:
                shown = re.sub(r'<a id="[^"]*"></a>', "", row[next(iter(row))])
                problems.append(f"{page}: the row {shown} links no section of E.3")
            for _, _, _, target in found:
                if resolved(page, target) != E3 or anchor_of(target) not in anchors:
                    problems.append(f"{page}: the denotes link {target} reaches no section of E.3")
            for table, key in re.findall(r'`([^`]+)`, `"([^"`]+)"`', row.get("read from", "")):
                if table in PACKAGE_TABLES:
                    stood[(table, key)] += 1
    for table, entries in PACKAGE_TABLES.items():
        for key in entries:
            if stood[(table, key)] != 1:
                problems.append(f"{table} {key!r} stands in {stood[(table, key)]} reference rows")
    for table, key in stood:
        if key not in PACKAGE_TABLES[table]:
            problems.append(
                f"a reference row reads {table} {key!r}, which the package does not hold"
            )

    operations = DOCS / REFERENCE_PAGES[0]
    rows_held = set(
        re.findall(r'<a id="([^"]+)"></a>', region(operations.read_text(encoding="utf-8")) or "")
        if operations.is_file()
        else ()
    )
    labels = intro_box(e3)
    realized = Counter()
    for number, line, _, target in links(e3):
        # a link on the intro box's `Builds on` or `Used by` line, or one
        # without an anchor, reaches the page and no row of it, and is no
        # `realized by` link (DR80)
        if labels.get(number) in SANCTIONED_LABELS or not anchor_of(target):
            continue
        if resolved(E3, target) != REFERENCE_PAGES[0]:
            continue
        anchor = anchor_of(target)
        if anchor not in rows_held:
            problems.append(
                f"Appendix E.3 links {target}, which reaches no row of the operations page: "
                f"{line.strip()[:100]}"
            )
        # a row of E.3's tables whose first cell names a kind links the row
        # the generator writes for that kind
        cells = table_cells(line)
        named = [kind for kind in KINDS if cells and names(cells[0], kind)]
        if named and anchor not in {row_anchor(kind) for kind in named}:
            problems.append(
                f"Appendix E.3's row of {' and '.join(named)} links {target}, which is not the "
                f"row of {' or '.join(named)} on the operations page"
            )
        realized.update(kind for kind in KINDS if anchor == row_anchor(kind))
    for kind, count in sorted(realized.items()):
        if count > 1:
            problems.append(
                f"Appendix E.3 holds {count} `realized by` links to the row of the kind {kind}, "
                f"and the architecture's §1 sanctions one"
            )

    first_cells = [cell for section in sections for cell in section["cells"]]
    for kind in KINDS:
        if kind not in PRIMITIVE_DEFINITIONS["definitions"]:
            problems.append(f"the kind {kind} of a row has no definition in PRIMITIVE_DEFINITIONS")
        count = sum(names(cell, kind) for cell in first_cells)
        if count != 1:
            problems.append(f"Appendix E.3 names the kind {kind} in {count} table rows")
    for kind in RETIRED_KINDS:
        if kind in KINDS:
            continue  # the package still defines it: lane K has not merged
        if any(names(cell, kind) for cell in first_cells) or f"`{kind}`" in e3:
            problems.append(f"Appendix E.3 names the retired kind {kind}")
    kinds_named = [
        cell
        for section in sections
        if any(names(cell, kind) for cell in section["cells"] for kind in KINDS)
        for cell in section["cells"]
    ]
    for old, kind in RENAMED_ROWS.items():
        if any(names(cell, old) for cell in kinds_named):
            problems.append(
                f"Appendix E.3's table of the kinds keeps the row {old!r}; name it {kind}"
            )
    if problems:
        pytest.fail("\n" + reported(problems), pytrace=False)


def test_item_4_no_page_reaches_a_retired_page_and_the_calculus_links_down_only_where_sanctioned():
    """Brief §7 item 4 and architecture item 4: no retired page stands under
    docs/ and no page links to one; the sweep of the plan's §3 with lane D's
    pattern finds nothing in docs/ (the changelog aside), tutorials/,
    applications/ or AGENTS.md; and no relative link runs from
    docs/bellman-calculus/ into docs/Bellman-Sym/ outside the
    `Builds on` and `Used by` lines of a page's intro box and Appendix E.3's
    `realized by` links; `BODY_LINKS_TODAY` and `BOX_LINKS_TODAY`, which
    allowed the links standing when lane D built, are empty since lane W
    (question 15 of the decisions record). A folder named `old` is passed
    over (`LEFTOVER`), even one that `RETIRED` names. The first clause of
    item 4, that the retired pages stand in the private archive with README
    rows and digests, is closed by no test: the archive stands outside the
    repository, and the lane's acceptance reads its README rows and
    SHA256SUMS digests."""
    problems = []
    for gone in RETIRED:
        if (DOCS / gone).exists() and not leftover(gone):
            problems.append(f"the retired page or folder docs/{gone} still stands")
    # every page, the changelog among them, since a link to a retired page
    # breaks the site wherever it stands; the decision records, read here
    # while they stood under docs/decisions/, stand in the internal folder
    # since 29 September 2026, and tests/test_decision_records.py checks that
    # each documentation page and wiki entry a record names exists
    for page in pages():
        for number, _, _, target in links((DOCS / page).read_text(encoding="utf-8")):
            reached = resolved(page, target)
            if reached and reached.startswith(RETIRED):
                problems.append(f"{page}:{number} links to the retired {reached}")
    for swept in SWEPT:
        # a file of the scope is read itself, since `rglob` finds nothing
        # below a file; a folder by each of its text files
        found = [ROOT / swept] if (ROOT / swept).is_file() else sorted((ROOT / swept).rglob("*"))
        for path in found:
            relative = path.relative_to(ROOT).as_posix()
            if (
                not path.is_file()
                or (relative != swept and path.suffix not in SWEPT_SUFFIXES)
                or relative == "docs/changelog.md"
                or (swept == "docs" and leftover(path.relative_to(DOCS)))
            ):
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if SWEEP.search(line):
                    problems.append(f"{relative}:{number} names an old path: {line.strip()[:120]}")

    body, box = Counter(), Counter()
    for page in pages():
        if not page.startswith("bellman-calculus/"):
            continue
        text = (DOCS / page).read_text(encoding="utf-8")
        labels = intro_box(text)
        for number, line in enumerate(text.splitlines(), start=1):
            for _, _, link_text, target in links(line):
                reached = resolved(page, target)
                if not reached or not reached.startswith("Bellman-Sym/"):
                    continue
                if labels.get(number) in SANCTIONED_LABELS:
                    continue
                # E.3's `realized by` link of a kind reaches its row of the
                # operations page, whose anchor item 3 checks
                if page == E3 and reached == REFERENCE_PAGES[0] and anchor_of(target):
                    continue
                (box if number in labels else body)[(page, link_text, target)] += 1
    for held, allowed, name in (
        (body, BODY_LINKS_TODAY, "BODY_LINKS_TODAY"),
        (box, BOX_LINKS_TODAY, "BOX_LINKS_TODAY"),
    ):
        allowed = Counter(allowed)
        for link, count in (held - allowed).items():
            problems.append(
                f"{link[0]} links into the language outside the sanctioned lines: "
                f"[{link[1]}]({link[2]}) ({count})"
            )
        for link, count in (allowed - held).items():
            problems.append(
                f"{link[0]} no longer holds [{link[1]}]({link[2]}); delete it from {name}"
            )
    if problems:
        pytest.fail("\n" + reported(problems), pytrace=False)


# --- the method and grid reference (AMD-MT-003 build contract §7, item 6) ---

METHODS_PAGE = "docs/Bellman-Sym/reference/methods.md"


def _spline(required):
    """A representation family `!spline` defined in this module, its degree
    required or optional: one definition, changed between the two."""
    return RepresentationFamily(
        "spline",
        {"degree": MethodOption("positive integer", required=required,
                                description="The degree of the spline.")},
        ("own nodes",),
        derivatives=(),
        stored="The coefficients of the spline.",
        text=EntryText(
            meaning="A spline through the values at the nodes of its grid.",
            compatibility="Reads its own nodes on the grid of its place.",
            example="dcsn_to_arvl.evaluate.method : !spline(degree=d)",
            example_meaning="The value is represented by a spline of degree `d`.",
            implementation="No numerical implementation is identified.",
            definition="bellman-calculus/06-Methods.md#5-the-grid-as-the-discretized-domain",
            source=__name__,
        ),
    )


def _entry(word):
    """The generated entry of `word`, read from the generator's output."""
    held = [entry for entry in reference_entries(methods_table(METHODS_PAGE)) if entry[1] == word]
    return held[0] if held else None


def test_the_method_reference_holds_one_entry_per_registered_method_and_grid_constructor(
    cons_savings_iid,
):
    """The methods page holds one entry for each method of `METHOD_TYPES`,
    registered representation families included, then one for each grid
    constructor of `GRID_CONSTRUCTORS`, in the order of those records and
    no other; each entry's arguments are the record's, by name, kind and
    omission, an empty record printing the one sentence of the
    unlisted-keyword policy; its compatibility holds the record's text and
    names the grid constructors whose sites admit the method's grid; and the
    entry of each registered representation family holds, after its
    compatibility, the stored-data sentence of its record in `families()`.
    A family registered later has its entry, placed among the families,
    with its own stored-data sentence, and loses it when it is removed; a
    keyword the record does not list is
    admitted; and a changed definition, the degree of a family made
    optional, changes both validation and the generated entry."""
    page = (ROOT / METHODS_PAGE).read_text(encoding="utf-8")
    entries = reference_entries(page)
    assert reference_entries(methods_table(METHODS_PAGE)) == entries
    assert [word for _, word, _, _ in entries] == (
        [f"!{word}" for word in METHOD_TYPES] + [f"!{word}" for word in GRID_CONSTRUCTORS])
    for anchor, word, parts, arguments in entries:
        method = word[1:] in METHOD_TYPES
        record = METHOD_TYPES[word[1:]] if method else GRID_CONSTRUCTORS[word[1:]]
        held = record["keywords"] if method else record.arguments
        assert anchor == row_anchor(word[1:])
        forms = ("Factor forms",) if not method and record.forms else ()
        family = families().get(word[1:]) if method else None
        stored = ("Stored data",) if family is not None else ()
        assert list(parts) == ["Declaration", "Type parameters", "Arguments", *forms,
                               "Compatibility", *stored, "Example", "Availability",
                               "Links"], word
        if family is not None:
            assert " ".join(family.stored.split()) == parts["Stored data"], word
        if held:
            assert [row[0].strip("`") for row in arguments] == list(held), word
            assert [(row[1], row[2]) for row in arguments] == [
                (option.kind, OMISSIONS[option.omission]) for option in held.values()], word
        else:
            assert parts["Arguments"] == NO_REGISTERED_ARGUMENTS, word
        assert " ".join(record.text.compatibility.split()) in parts["Compatibility"], word
        if method and record.grid is not None:
            admitted = [name for name, grid in GRID_CONSTRUCTORS.items()
                        if record.grid in grid.sites.readers]
            assert (
                re.findall(r"\[`!(\w+)`\]\(#", parts["Compatibility"])[:len(admitted)]
                == admitted
            )
        if not method:
            for form in record.syntax:
                assert f"`{form}`" in parts["Declaration"], word

    # registration and removal: the family's entry stands after the base
    # families and before the rows that follow them, and goes with it
    base = list(families())
    register(_spline(required=True))
    try:
        words = [word for _, word, _, _ in reference_entries(methods_table(METHODS_PAGE))]
        assert words.index("!spline") == words.index(f"!{base[-1]}") + 1
        _, _, parts, arguments = _entry("!spline")
        assert arguments[0][:3] == ["`degree`", "positive integer", OMISSIONS["refused"]]
        assert parts["Stored data"] == families()["spline"].stored
        assert (
            "test_docs_shape.py" in parts["Links"]
            and "public link unavailable" in parts["Links"]
        )
        with pytest.raises(ConstructionError) as refused:
            methodized(cons_savings_iid, "dcsn_to_arvl.evaluate.method : !spline\n")
        assert refused.value.rule == "method-admission" and "degree" in refused.value.message
        # a keyword the record does not list is admitted and retained
        methodized(cons_savings_iid,
                   "d : ℤ\ns : ℤ\ndcsn_to_arvl.evaluate.method : !spline(degree=d, smooth=s)\n")
    finally:
        unregister("spline")
    assert _entry("!spline") is None

    # one definition changed: the degree made optional is admitted when it
    # is left out, and the entry prints the optional omission
    register(_spline(required=False))
    try:
        methodized(cons_savings_iid, "dcsn_to_arvl.evaluate.method : !spline\n")
        assert _entry("!spline")[3][0][:3] == [
            "`degree`", "positive integer", OMISSIONS["omitted"]]
    finally:
        unregister("spline")


# the fragments of the methods page that links may name: the anchor of each
# method of the earlier table, the section links, and the headings of the
# earlier layout, which the page retains as anchors
PRESERVED_FRAGMENTS = (
    "egm", "vfi", "time-iteration", "explicit", "linear", "pchip", "closed-form",
    "gauss-hermite", "quadrature", "exact", "exact-markov", "markov", "markov-expectation",
    "sum", "tauchen", "deterministic", "histogram", "identity", "monte-carlo", "max",
    "discrete-choice", "golden-section", "scipy-bounded", "root-find", "newton",
    "analytic-inverse", "fues", "1-reading-the-table", "2-the-table", "3-the-grid",
)
# a revision of the development repository, which holds the internal folder
# and so is no exported revision of the public repository
PRIVATE_REVISION = "4742e477c627672e3492ee594c034e91a0e0e652"


def page_fragments(text):
    """Every fragment of a page, an `<a id>` anchor or a heading's slug,
    outside fenced blocks, with repetitions."""
    held = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    anchors = re.findall(r'<a id="([^"]+)"></a>', held)
    headings = [slug(heading) for heading in re.findall(r"^#{2,6}\s+(.*\S)", held, re.MULTILINE)]
    return anchors + headings


def test_the_method_reference_is_reproducible_and_its_links_and_fragments_resolve():
    """The methods page is generated reproducibly: two generations agree,
    `reference_pages.py --check` finds the page as generated, and no
    revision of the checkout enters it. Its fragments are unique, every
    preserved fragment stands, every link on the page reaches its anchor or
    an existing page, and every link of the documentation into the page
    reaches a fragment it holds. Each source location names a line of the
    checkout that defines its word; no exported revision holds the
    definitions, so each entry states its public link unavailable, and a
    development revision named as exported is refused."""
    from reference_pages import source_location

    first, second = methods_table(METHODS_PAGE), methods_table(METHODS_PAGE)
    assert first == second
    run = subprocess.run(
        [sys.executable, str(HOOKS / "reference_pages.py"), "--check", "--page", METHODS_PAGE],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True,
                          text=True).stdout.strip()
    page = (ROOT / METHODS_PAGE).read_text(encoding="utf-8")
    assert head and head not in page and head[:12] not in page

    fragments = page_fragments(page)
    repeated = sorted(fragment for fragment, count in Counter(fragments).items() if count > 1)
    assert not repeated, f"fragments that stand twice: {repeated}"
    assert not set(PRESERVED_FRAGMENTS) - set(fragments)
    problems = []
    relative = "Bellman-Sym/reference/methods.md"
    for number, _, _, target in links(page):
        if target.startswith("#"):
            if target[1:] not in fragments:
                problems.append(f"line {number}: {target} reaches no fragment of the page")
        elif "://" not in target:
            reached = resolved(relative, target)
            if reached is None or not (DOCS / reached).is_file():
                problems.append(f"line {number}: {target} reaches no page")
    for path in sorted(DOCS.rglob("*.md")):
        for number, _, _, target in links(path.read_text(encoding="utf-8")):
            within = path.relative_to(DOCS).as_posix()
            if "#" in target and resolved(within, target) == relative:
                if target.split("#", 1)[1] not in fragments:
                    problems.append(f"{within}:{number}: {target} reaches no fragment")
    assert not problems, "\n".join(problems)

    for _, word, parts, _ in reference_entries(page):
        located = re.search(r"source `([^`]+)`, `([^`]+)`, line (\d+); ([^;]+)", parts["Links"])
        assert located, word
        module, _, line, public = located.groups()
        held = (
            (ROOT / "packages/bellman/bellman" / module).read_text(encoding="utf-8").splitlines()
        )
        if word[1:] in GRID_CONSTRUCTORS:
            assert f"T.{GRID_CONSTRUCTORS[word[1:]].term.__name__}:" in held[int(line) - 1], word
        else:
            assert f'"{word[1:]}"' in " ".join(held[int(line) - 1:int(line) + 2]), word
        assert public.startswith("public link unavailable"), word
    with pytest.raises(SystemExit, match="no exported revision"):
        source_location("egm", METHOD_TYPES["egm"], "row", revision=PRIVATE_REVISION)


# The shared fixtures on which the entries' declaration examples are
# executed, in the order tried: an example runs on the first stage whose
# places it names, read in one call of `methodize` with the additions that
# `example_additions` names for the stage. The examples name places of
# several stages, since each shows its method where the applications write
# it.
EXAMPLE_STAGES = ("cons_savings_iid", "cons", "port", "tenure", "perfect_foresight",
                  "buffer_stock", "cons_candidate", "perfect_foresight_explicit",
                  "example_shocks", "worker_cons")


def example_settings(example):
    """The declarations of the settings an example names, with a valid value
    of each and, for its first count or keyword, an invalid value and the
    rule that refuses it: a count in a grid factor below two under
    `grid-bounds`, and a keyword's value outside its set under
    `method-option-value`."""
    keywords = re.findall(r"!\w+\(([^()]*)\)", example)
    named = [name for group in keywords for name in re.findall(r"=\s*(\w+)", group)]
    factors = [name.strip() for group in re.findall(r"=\(([^()]*)\)", example)
               for name in group.split(",")]
    declarations, values, invalid = [], {}, None
    for name in dict.fromkeys(named + factors):
        if name.startswith("n_"):
            declarations.append(f"{name} : ℕ")
            values[name] = 3
            if invalid is None:
                rule = "method-option-value" if name in named else "grid-bounds"
                invalid = (name, 0 if rule == "method-option-value" else 1, rule)
        elif name.endswith(("_min", "_max")):
            declarations.append(f"{name} : ℝ₊")
            values[name] = 0.5 if name.endswith("_min") else 5.0
    if "A_points" in example:
        declarations.append("A_points : ℝ₊ × ℝ₊ × ℝ₊")
        values["A_points"] = [0.5, 1.0, 2.0]
    return declarations, values, invalid


def test_every_entry_of_the_method_reference_has_an_example_that_executes(
    request, grid_stage, example_additions,
):
    """Each entry's declaration example, as its record writes it, is
    methodized on a shared fixture, after the additions that write its place
    where the stage file does not, through the public steps it needs and
    configured with valid values of the settings it names; where a count or
    a keyword restricts a value, a representative invalid value is refused
    under the rule the entry names. A grid example stands with the method
    whose grid it writes, and the fibred grid on the stage of its own
    example. No numerical solve is run."""
    from conftest import GRID_VALUES

    executed, unexecuted = {}, {}
    records = [(word, row.text.example) for word, row in METHOD_TYPES.items()]
    records += [(word, record.text.example) for word, record in GRID_CONSTRUCTORS.items()]
    for word, example in records:
        context = {"Cartesian": "policy.method : !egm\n"}.get(word, "")
        declarations, values, invalid = example_settings(example)
        if word == "Fibred":
            stage = grid_stage("cntn_to_dcsn.method : !vfi\n" + example + "\n")
            stage.configure({"settings": GRID_VALUES})
            executed[word] = "grids"
            continue
        for name in EXAMPLE_STAGES:
            stage = request.getfixturevalue(name)
            text = "\n".join([*declarations, context + example]) + "\n"
            try:
                bound = methodized(stage, *example_additions.get(name, ()), text)
            except ConstructionError:
                continue
            executed[word] = name
            break
        else:
            unexecuted[word] = example
            continue
        if values:
            copy_native(bound).configure({"settings": values})
        if invalid is not None:
            setting, value, rule = invalid
            with pytest.raises(ConstructionError) as refused:
                copy_native(bound).configure({"settings": {**values, setting: value}})
            assert refused.value.rule == rule, (word, refused.value.message)
    assert not unexecuted, unexecuted
    assert len(executed) == len(records)
