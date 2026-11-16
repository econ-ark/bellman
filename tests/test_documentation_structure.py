"""The folders, the navigation and the links of the documentation, its
generated tables and listings, and how its reference pages relate the
package to Appendix E.3 of the calculus."""

import re
import subprocess
import sys
import warnings
from collections import Counter
from pathlib import PurePosixPath

import pytest
import yaml
from application_files import ROOT, checkout_environment
from documentation_pages import generated_part, link_target_path, links, reference_entries, slugify
from documentation_paths import DOCS, FRONT_MATTER, HOOKS

# the reader of a table row, whether a cell names a term, and the anchor of a
# row, from the generator that writes the pages, which the import of
# documentation_pages above puts on the module path
from reference_pages import anchor_of as row_anchor
from reference_pages import names as cell_names
from reference_pages import table_cells

from bellman.distributions.families import FAMILY_ARGUMENTS
from bellman.fold.table import KINDS
from bellman.refusals import FACTORY_RULES, RULES, TARGET_RULES
from bellman.stage.method_table import METHOD_TYPES
from bellman.typing.primitive_definitions import PRIMITIVE_DEFINITIONS

# a folder named `old` under docs/ is passed over wherever the tests read
# docs/: `.gitignore`'s `**/old/` keeps such a folder outside git, so it
# stands only as a leftover of a checkout and never in a clone
LEFTOVER = "old"


# the twelve parts of the documentation; a page's part tag is the tag
# `docs/<part>` of its front matter, such as `docs/guide`
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


# the pages that carry their part tag already: the API pages, the reference
# pages and the overview of the semantics; every other page may still lack
# its tag, and the test counts the pages that lack it
PAGES_WITH_THEIR_PART_TAG = (
    "Bellman-Sym/API/",
    "Bellman-Sym/reference/",
    "overview/05-semantics.md",
)


# what docs/Bellman-Sym/ holds besides its root pages
BELLMAN_SYM_FOLDERS = ("API", "appendices", "reference", "figures", "img")


# The retired pages and folders: pages that earlier versions of the
# documentation held and that it no longer holds. No page of them stands under
# docs/, and no page links to them. A folder named `old` among them stands
# outside git, and a test that asks what stands passes over it (`LEFTOVER`).
RETIRED = (
    "Bellman-Term/",
    "semantics/",
    "Bellman-Sym/old/",
    "Bellman-Sym/reference/old/",
    # the folders `old` of the calculus and of its catalogues
    "bellman-calculus/old/",
    "bellman-calculus/catalogues/old/",
    "Bellman-Sym/reference/primitives.md",
    "Bellman-Sym/reference/dolang_plus_schema.md",
    "bellman-calculus/catalogues/methods.md",
    # the page of the stage object, whose content stands in the nine pages of
    # API/stage/, and the folder of the factory pages, whose pages stand in
    # API/factory/
    "Bellman-Sym/02-the-stage-object.md",
    "Bellman-Sym/syntax-API/",
)


# the parts of the navigation, in order, each with the part of its pages
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


# the pages that stand outside the navigation: the pages of the HARK models
# and the output under housing_renting/converged_output/; a page of the list
# that the navigation comes to name, or that goes, is a fault until it is
# deleted from the list
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


# the five reference pages whose tables the generator writes; the first is the
# operations page
REFERENCE_PAGES = tuple(
    f"Bellman-Sym/reference/{name}.md"
    for name in ("operations", "laws", "forms", "methods", "refusals")
)


# Appendix E.3 of the calculus, the catalogue of its operators
OPERATORS_APPENDIX = "bellman-calculus/catalogues/operators.md"


# the retired kinds: three names that no kind of a card's row carries; the
# package writes the kinds of `KINDS`, and an earlier version of it also had
# kinds of these names
RETIRED_KINDS = ("Selection", "Inversion", "Solution")


# the names that an earlier version of Appendix E.3 gave the rows of two
# kinds in its table of the kinds, by the kind that the row now names
RENAMED_ROWS = {"evaluate": "PolicyInsertion", "Function evaluation": "Evaluation"}


# the anchors of the rows of the forms page whose object Appendix E.3 does not
# define, which link no section of it; every other row of that page links one
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


# the table and the key that a `read from` cell names, such as
# `RULES`, `"grid-bounds"`
READ_FROM = re.compile(r'`([^`]+)`, `"([^"`]+)"`')


# the lines of a page's intro box, the callout `[!info]- Relationship with
# other documents`, from which a page of the calculus, under
# docs/bellman-calculus/, may link a page of the language, under
# docs/Bellman-Sym/, each by the label that opens the line in bold
LINKING_LABELS = ("Builds on", "Used by")


# The links of a page of the calculus into the language that stand outside
# the lines of `LINKING_LABELS` and are no `realized by` link of Appendix
# E.3, each as (the page under docs/, the text of the link, its target as
# written): in the body of a page, and on another line of its intro box. Both
# lists are empty; tests/test_documentation_content.py reads them.
BODY_LINKS_TODAY = ()


BOX_LINKS_TODAY = ()


def leftover(path):
    """Whether a path under docs/, written relative to docs/, is a folder
    named `old` or lies in one, which the tests pass over."""
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


def front_matter_mapping(text):
    """The front matter of a page as a mapping; empty where it has none."""
    found = FRONT_MATTER.match(text)
    if not found:
        return {}
    return yaml.safe_load(found.group(1)) or {}


def part_tags(text):
    """(the part tags of a page's front matter, the part tags written in its
    text), a tag inside a code span or a fenced block being no tag."""
    listed = front_matter_mapping(text).get("tags") or []
    listed = [listed] if isinstance(listed, str) else listed
    front = [str(tag).lstrip("#") for tag in listed if str(tag).lstrip("#").startswith("docs/")]
    body = FRONT_MATTER.sub("", text, count=1)
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    body = re.sub(r"`[^`\n]*`", "", body)
    return front, re.findall(r"(?<![\w/#])#(docs/[\w-]+)", body)


def fragment_of(target):
    """The fragment of a link's target, after its `#`, or an empty string
    where it names none."""
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


def table_rows(text):
    """The rows of the table between the markers of a page, each a mapping
    from the column's head to the cell."""
    held = generated_part(text)
    if held is None:
        return None
    rows = [cells for cells in map(table_cells, held.splitlines()) if cells]
    head, body = rows[0], rows[1:]
    return [dict(zip(head, row)) for row in body]


def entry_rows(text):
    """The entries of the methods page as the rows that the other reference
    pages hold: the word with its anchor, the places it is bound at, its
    `denotes` link and its `read from` reference."""
    rows = []
    for anchor, word, parts, _ in reference_entries(text):
        link_parts = parts.get("Links", "").split("; ")
        rows.append(
            {
                "method": f'<a id="{anchor}"></a>`{word}`',
                "bound at": parts.get("Declaration", ""),
                "denotes": next((part for part in link_parts if part.startswith("denotes ")), ""),
                "read from": next(
                    (part for part in link_parts if part.startswith("read from ")), ""
                ),
            }
        )
    return rows


def shown(row):
    """The first cell of a reference row, its anchor apart."""
    return re.sub(r'<a id="[^"]*"></a>', "", row[next(iter(row))])


def appendix_sections(text):
    """The sections of Appendix E.3, each with its anchors and the first cells
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
                "anchors": {slugify(heading.group(1), "-")} | ({pending} if pending else set()),
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


def realized_by_links(text):
    """(the line, the target, its fragment) of each `realized by` link of
    Appendix E.3: a link with a fragment to the operations page that stands
    on no line of `LINKING_LABELS` of the intro box. A link on such a line,
    or one without a fragment, reaches the page and no row of it."""
    labels = intro_box(text)
    return [
        (line, target, fragment_of(target))
        for number, line, _, target in links(text)
        if labels.get(number) not in LINKING_LABELS
        and fragment_of(target)
        and link_target_path(OPERATORS_APPENDIX, target) == REFERENCE_PAGES[0]
    ]


def reported(problems):
    """The problems a test found, one to a line."""
    return "\n".join(f"- {problem}" for problem in problems)


@pytest.fixture(scope="module")
def appendix_e3():
    """The text of Appendix E.3."""
    return (DOCS / OPERATORS_APPENDIX).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def appendix_e3_sections(appendix_e3):
    """The sections of Appendix E.3, as `appendix_sections` reads them."""
    return appendix_sections(appendix_e3)


@pytest.fixture(scope="module")
def reference_rows():
    """The rows of each reference page by its path under docs/: the entries
    of the methods page as `entry_rows` gives them, and the rows of the table
    between the markers of each other page; None for a page that does not
    stand or does not hold the markers."""
    rows = {}
    for page in REFERENCE_PAGES:
        path = DOCS / page
        reader = entry_rows if page.endswith("/methods.md") else table_rows
        rows[page] = reader(path.read_text(encoding="utf-8")) if path.is_file() else None
    return rows


@pytest.fixture(scope="module")
def calculus_links_into_the_language():
    """The relative links of the pages of docs/bellman-calculus/ into
    docs/Bellman-Sym/ that stand on no line of `LINKING_LABELS` and are no
    `realized by` link of Appendix E.3, counted by (the page, the text of the
    link, its target) apart for each place: `body`, outside the page's intro
    box, and `intro box`, on another line of the box."""
    held = {"body": Counter(), "intro box": Counter()}
    for page in pages():
        if not page.startswith("bellman-calculus/"):
            continue
        text = (DOCS / page).read_text(encoding="utf-8")
        labels = intro_box(text)
        for number, line in enumerate(text.splitlines(), start=1):
            for _, _, link_text, target in links(line):
                reached = link_target_path(page, target)
                if not reached or not reached.startswith("Bellman-Sym/"):
                    continue
                if labels.get(number) in LINKING_LABELS:
                    continue
                # Appendix E.3's `realized by` link of a kind reaches its row
                # of the operations page, whose anchor another test checks
                if (
                    page == OPERATORS_APPENDIX
                    and reached == REFERENCE_PAGES[0]
                    and fragment_of(target)
                ):
                    continue
                place = "intro box" if number in labels else "body"
                held[place][(page, link_text, target)] += 1
    return held


@pytest.mark.xfail(
    strict=True,
    reason="The test expects the folders, the part tags and the navigation of the "
    "documentation to follow the parts that `PARTS`, `FOLDER_PARTS` and `NAV_PARTS` list. "
    "Today they do not: for example, the pages under `docs/workbench/` belong to no part.",
)
def test_the_folders_the_part_tags_and_the_navigation_of_the_documentation_follow_its_parts():
    """docs/Bellman-Sym/ holds index.md, its root pages and the five folders
    of `BELLMAN_SYM_FOLDERS` and nothing else, a folder named `old` and a
    file whose name starts with `.` being passed over; docs/Bellman-Term/ and
    docs/semantics/ are gone; every page belongs to one part by its folder
    and carries no part tag but its own, the pages of
    `PAGES_WITH_THEIR_PART_TAG` carry theirs, and the other pages that lack
    their tag are counted in a warning; the navigation names every page of
    the site once, in its part and in the order of `NAV_PARTS` and
    `LANGUAGE_GROUPS`, and names no retired page; the index of the wiki
    links every page of the wiki; and only the pages that `exclude_docs` and
    `not_in_nav` of `mkdocs.yml` name and the pages of
    `OUTSIDE_THE_NAV_TODAY` stand outside the navigation, each page of that
    list among them."""
    # the strict build of the site, `mkdocs build --strict`, is checked in the
    # complete set by the test of tests/test_package_documentation.py that
    # builds the documentation site under the strict option
    problems = []
    held = {
        entry.name
        for entry in (DOCS / "Bellman-Sym").iterdir()
        if entry.is_dir() and not leftover(entry.name)
    }
    for folder in sorted(held - set(BELLMAN_SYM_FOLDERS)):
        problems.append(f"docs/Bellman-Sym/{folder}/ is no folder of BELLMAN_SYM_FOLDERS")
    for folder in BELLMAN_SYM_FOLDERS:
        if folder not in held:
            problems.append(
                f"docs/Bellman-Sym/{folder}/ does not exist, and BELLMAN_SYM_FOLDERS names it"
            )
    # a markdown file directly under the folder is a root page, whose place
    # the navigation check judges; a name that starts with `.` is passed over
    for entry in sorted((DOCS / "Bellman-Sym").iterdir()):
        if entry.is_file() and not entry.name.startswith(".") and entry.suffix != ".md":
            problems.append(
                f"docs/Bellman-Sym/{entry.name} is neither a root page nor a folder of "
                f"BELLMAN_SYM_FOLDERS"
            )
    if not (DOCS / "Bellman-Sym" / "index.md").is_file():
        problems.append(
            "docs/Bellman-Sym/index.md, the index page of the groups of LANGUAGE_GROUPS, does not "
            "exist"
        )
    for gone in ("Bellman-Term", "semantics"):
        if (DOCS / gone).exists():
            problems.append(f"docs/{gone}/ still stands")

    lacking = []
    for page in pages():
        part = part_of(page)
        if part is None:
            problems.append(f"{page} belongs to no part of FOLDER_PARTS by its folder")
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
            if page.startswith(PAGES_WITH_THEIR_PART_TAG):
                problems.append(
                    f"{page} is a page of PAGES_WITH_THEIR_PART_TAG and lacks its part tag {own}"
                )
            else:
                lacking.append(page)
    if lacking:
        warnings.warn(
            f"{len(lacking)} of {len(pages())} pages under docs/ lack their part tag",
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
            f"the navigation's parts are {list(dict.fromkeys(titles))}, and NAV_PARTS orders "
            f"them {list(NAV_PARTS)}"
        )
    groups = [trail[1] for trail, _ in entries if trail[:1] == ("Language",) and len(trail) > 1]
    if list(dict.fromkeys(groups)) != list(LANGUAGE_GROUPS):
        problems.append(
            f"Language holds the groups {list(dict.fromkeys(groups))}, and LANGUAGE_GROUPS "
            f"holds {list(LANGUAGE_GROUPS)}"
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
    listed = {link_target_path("wiki/index.md", target) for _, _, _, target in links(index)}
    for page in pages():
        if page.startswith("wiki/") and page != "wiki/index.md" and page not in listed:
            problems.append(f"the wiki's index names no link to {page}")
    if problems:
        pytest.fail("\n" + reported(problems), pytrace=False)


# the two scripts elaborate every stage file under applications/, assemble
# the two-stage durables trellis whole and print the refusal catalogue, so
# both rows are in the complete set
@pytest.mark.complete_set
@pytest.mark.parametrize(
    "script",
    ["reference_pages.py", "stage_object_page.py"],
    ids=["tables-of-the-reference-pages", "listings-of-the-language-overview-and-example-pages"],
)
def test_the_check_of_each_generator_of_the_pages_finds_the_pages_as_the_package_writes_them(
    script,
):
    """`--check` of a generator of the pages, run in a new interpreter, finds
    each table or listing that it writes as the package writes or prints it:
    `reference_pages.py` the table of each reference page and of the API
    index, and `stage_object_page.py` each listing of a page of the language,
    the overview or the examples that shows what a listing prints."""
    run = subprocess.run(
        [sys.executable, str(HOOKS / script), "--check"],
        cwd=str(ROOT),
        env=checkout_environment(),
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, f"{script} --check\n{run.stdout}\n{run.stderr}"


# the reference pages but the methods page, whose entries `entry_rows` reads
@pytest.mark.parametrize(
    "page",
    [page for page in REFERENCE_PAGES if not page.endswith("/methods.md")],
    ids=["operations", "laws", "forms", "refusals"],
)
def test_each_reference_page_holds_its_generated_table_between_the_markers(reference_rows, page):
    """The reference page stands and holds its generated table between the two
    markers."""
    assert reference_rows[page] is not None


# the reference pages but the last, the refusals page, whose rows have no
# `denotes` link, as the test after this one checks
@pytest.mark.parametrize(
    "page", REFERENCE_PAGES[:4], ids=["operations", "laws", "forms", "methods"]
)
def test_every_denotes_link_of_a_reference_row_reaches_a_section_of_appendix_e3(
    reference_rows, appendix_e3_sections, page
):
    """Every `denotes` link of a row of the reference page reaches Appendix
    E.3 at the anchor of one of its sections."""
    anchors = {anchor for section in appendix_e3_sections for anchor in section["anchors"]}
    unreached = [
        target
        for row in reference_rows[page]
        for _, _, _, target in links(row.get("denotes", ""))
        if link_target_path(page, target) != OPERATORS_APPENDIX
        or fragment_of(target) not in anchors
    ]
    assert unreached == []


def test_no_row_of_the_refusals_page_has_a_denotes_link(reference_rows):
    """No row of the refusals page has a `denotes` link, since the generator
    names no section of Appendix E.3 for a rule and writes a dash."""
    linked = [
        shown(row)
        for row in reference_rows["Bellman-Sym/reference/refusals.md"]
        if links(row.get("denotes", ""))
    ]
    assert linked == []


# the operations page and the laws page, the first two reference pages
@pytest.mark.parametrize("page", REFERENCE_PAGES[:2], ids=["operations", "laws"])
def test_every_row_of_the_operations_page_and_the_laws_page_has_a_denotes_link(
    reference_rows, page
):
    """Every row of the operations page and of the laws page has a `denotes`
    link."""
    unlinked = [shown(row) for row in reference_rows[page] if not links(row.get("denotes", ""))]
    assert unlinked == []


def test_every_method_bound_at_an_operator_has_a_denotes_link(reference_rows):
    """Every entry of the methods page whose places name an operator has a
    `denotes` link; a method whose places name none is bound on a whole
    builder, whose direction the methods page does not state."""
    unlinked = [
        shown(row)
        for row in reference_rows["Bellman-Sym/reference/methods.md"]
        if re.search(r"\boperator\b", row.get("bound at", ""))
        and not links(row.get("denotes", ""))
    ]
    assert unlinked == []


def test_every_form_but_those_of_forms_without_denotes_has_a_denotes_link(
    reference_rows,
):
    """Every row of the forms page whose anchor `FORMS_WITHOUT_DENOTES` does
    not name has a `denotes` link."""
    unlinked = []
    for row in reference_rows["Bellman-Sym/reference/forms.md"]:
        anchor = re.search(r'<a id="([^"]+)"></a>', row[next(iter(row))])
        if anchor is None or anchor.group(1) in FORMS_WITHOUT_DENOTES:
            continue
        if not links(row.get("denotes", "")):
            unlinked.append(shown(row))
    assert unlinked == []


@pytest.mark.parametrize(
    "table",
    PACKAGE_TABLES,
    ids=[
        "primitive-definitions", "family-arguments", "method-types", "rules", "target-rules",
        "factory-rules",
    ],
)  # fmt: skip
def test_the_reference_rows_read_each_entry_of_a_package_table_once_and_no_other_key(
    reference_rows, table
):
    """The `read from` cells of the reference rows name each entry of the
    package table once and no key that the table does not hold."""
    read = [
        key
        for rows in reference_rows.values()
        for row in rows
        for name, key in READ_FROM.findall(row.get("read from", ""))
        if name == table
    ]
    assert sorted(read) == sorted(PACKAGE_TABLES[table])


def test_every_realized_by_link_of_appendix_e3_reaches_a_row_of_the_operations_page(appendix_e3):
    """Every `realized by` link of Appendix E.3 reaches the anchor of a row of
    the table of the operations page."""
    operations = DOCS / REFERENCE_PAGES[0]
    rows_held = set(
        re.findall(
            r'<a id="([^"]+)"></a>', generated_part(operations.read_text(encoding="utf-8")) or ""
        )
        if operations.is_file()
        else ()
    )
    unreached = [
        target
        for _, target, fragment in realized_by_links(appendix_e3)
        if fragment not in rows_held
    ]
    assert unreached == []


def test_the_realized_by_link_in_the_row_of_a_kind_reaches_the_row_of_that_kind(appendix_e3):
    """The `realized by` link in a row of the tables of Appendix E.3 whose
    first cell names a kind of `KINDS` reaches the row of that kind on the
    operations page."""
    misdirected = []
    for line, target, fragment in realized_by_links(appendix_e3):
        cells = table_cells(line)
        kinds_named = [kind for kind in KINDS if cells and cell_names(cells[0], kind)]
        if kinds_named and fragment not in {row_anchor(kind) for kind in kinds_named}:
            misdirected.append(target)
    assert misdirected == []


def test_no_row_of_a_kind_on_the_operations_page_is_reached_by_two_realized_by_links(appendix_e3):
    """No row of a kind on the operations page is reached by more than one
    `realized by` link of Appendix E.3."""
    reached = Counter(
        kind
        for _, _, fragment in realized_by_links(appendix_e3)
        for kind in KINDS
        if fragment == row_anchor(kind)
    )
    assert sorted(kind for kind, count in reached.items() if count > 1) == []


def test_every_kind_of_a_cards_row_has_a_definition_among_the_primitive_definitions():
    """Every kind of `KINDS` has a definition in `PRIMITIVE_DEFINITIONS`."""
    assert [kind for kind in KINDS if kind not in PRIMITIVE_DEFINITIONS["definitions"]] == []


def test_appendix_e3_names_each_kind_in_the_first_cell_of_exactly_one_table_row(
    appendix_e3_sections,
):
    """Appendix E.3 names each kind of `KINDS` in the first cell of exactly
    one row of its tables."""
    first_cells = [cell for section in appendix_e3_sections for cell in section["cells"]]
    counts = {kind: sum(cell_names(cell, kind) for cell in first_cells) for kind in KINDS}
    assert counts == dict.fromkeys(KINDS, 1)


@pytest.mark.parametrize("kind", RETIRED_KINDS, ids=list(RETIRED_KINDS))
def test_appendix_e3_names_no_retired_kind(appendix_e3, appendix_e3_sections, kind):
    """Appendix E.3 writes the retired kind `kind`, a name that no kind of the
    package carries, neither in the first cell of a table row nor as code."""
    assert kind not in KINDS
    first_cells = [cell for section in appendix_e3_sections for cell in section["cells"]]
    assert (
        not any(cell_names(cell, kind) for cell in first_cells) and f"`{kind}`" not in appendix_e3
    )


@pytest.mark.parametrize(
    ("earlier", "kind"), RENAMED_ROWS.items(), ids=["evaluate", "function-evaluation"]
)
def test_the_table_of_kinds_of_appendix_e3_has_no_row_named_evaluate_or_function_evaluation(
    appendix_e3_sections, earlier, kind
):
    """Where a section of Appendix E.3 names a kind of `KINDS` in the first
    cell of a table row, no first cell of that section names `earlier`, the
    name that the row of `kind` had in an earlier version of the appendix."""
    cells_of_kinds = [
        cell
        for section in appendix_e3_sections
        if any(cell_names(cell, named) for cell in section["cells"] for named in KINDS)
        for cell in section["cells"]
    ]
    assert not any(cell_names(cell, earlier) for cell in cells_of_kinds), f"name the row {kind}"


@pytest.mark.parametrize(
    "gone",
    [gone for gone in RETIRED if not leftover(gone)],
    ids=[gone.rstrip("/") for gone in RETIRED if not leftover(gone)],
)
def test_no_retired_page_or_folder_stands_under_docs(gone):
    """The retired page or folder `gone` does not stand under docs/."""
    assert not (DOCS / gone).exists()


def test_no_page_links_to_a_retired_page_or_folder():
    """No link of a page under docs/, the changelog among them, reaches a
    retired page or folder, since such a link breaks the site wherever it
    stands."""
    linking = []
    for page in pages():
        for number, _, _, target in links((DOCS / page).read_text(encoding="utf-8")):
            reached = link_target_path(page, target)
            if reached and reached.startswith(RETIRED):
                linking.append(f"{page}:{number} links to the retired {reached}")
    assert linking == []


@pytest.mark.parametrize(
    ("place", "allowed"),
    [("body", BODY_LINKS_TODAY), ("intro box", BOX_LINKS_TODAY)],
    ids=["body", "intro-box"],
)
def test_the_calculus_links_the_language_only_from_linking_lines_and_realized_by_links(
    calculus_links_into_the_language, place, allowed
):
    """The links of the pages of the calculus into the language that stand
    neither on a line of `LINKING_LABELS` nor among Appendix E.3's `realized
    by` links, in the body of a page or on another line of its intro box,
    are those of `allowed`, which is empty."""
    assert calculus_links_into_the_language[place] == Counter(allowed)
