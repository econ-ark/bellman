"""The acceptance file of the table of the rules of the language and their
code, `SEMANTIC_RULES` of `bellman.semantic_rules` (the second layer of the
tests, `packages/bellman/README.md` §8): one test for each of the six items
of its brief, and a seventh for the pages that point to the rules that the
package does not yet check.

A row of the table states one rule of the page
`docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md`, of one
of its sections 2.1 to 2.5 or of one of its rules R1 to R12, with the
functions of the package that implement it and check it, the refusal rules
raised when a file breaks it and one test that exercises it. The tests below
read every row: each function is read by import and attribute lookup, each
test is one that pytest collects, each refusal is a rule of the refusal
catalogue, the sections of the rows are those of the page, every rule the
package refuses under has a row or a page that states it, and the example
of a rule the package does not yet check is read or refused as its row says.
The rows of `UNCHECKED_ELSEWHERE`, the rules not yet checked that another
section of the page or another page states, are run in the same way. The
last test reads the pages: each section and each page that such a row names
stands, and each page that points to the table of those rules is named by a
row.

The page `docs/Bellman-Sym/reference/rules.md` and the table of section 5.3
of the page of the rules are printed from the tables by
`docs/_hooks/reference_pages.py`, whose `--check` the test of the generated
tables runs (`tests/cat/test_docs_shape.py`, item 2).
"""

from __future__ import annotations

import inspect
import os
import posixpath
import re
import subprocess
import sys

import pytest
from conftest import ROOT

from bellman.factory.elaboration import elaborate_text
from bellman.refusal_catalogue import VOCABULARIES
from bellman.refusals import ConstructionError
from bellman.semantic_rules import (
    APPENDIX,
    RULES_STATED_ELSEWHERE,
    SEMANTIC_RULES,
    UNCHECKED_ELSEWHERE,
    example_texts,
    resolve,
)

DOCS = ROOT / "docs"
# the pages of the language, among which the last test looks for pointers
LANGUAGE_PAGES = DOCS / "Bellman-Sym"

# the heading of a section 2.1 to 2.5 or of a rule R1 to R12 on the page
SECTION_HEADING = re.compile(r"^### (2\.\d+|R\d+) ", re.MULTILINE)
# a numbered heading of the page, of the second or the third level, with its
# number: `## 3 The rules`, `### 1.1 Stages, perches, and fields`, `### R6
# Well-formedness`
NUMBERED_HEADING = re.compile(r"^(##|###) (\d+(?:\.\d+)?|R\d+) ")
# the marker that opens the printed table of the rules not yet checked
OPENING_MARKER = "<!-- reference-table -->"
# the options with which pytest lists the tests of files and runs none
COLLECT = ("--collect-only", "-q", "-p", "no:cacheprovider")


def every_rule():
    """Every rule of the three vocabularies the package refuses under."""
    return {rule for _, _, rules in VOCABULARIES for rule in rules}


def reported(problems):
    return "\n" + "\n".join(f"- {problem}" for problem in problems)


def unchecked_rows():
    """Every row that states a rule the package does not yet check, each
    after the words that name it in a report: the rows of `SEMANTIC_RULES`
    with `checked` false, then the rows of `UNCHECKED_ELSEWHERE`."""
    for row in SEMANTIC_RULES:
        if not row.checked:
            yield f"{row.section}, {row.item!r}", row
    for row in UNCHECKED_ELSEWHERE:
        yield f"{', '.join(row.sections) or 'another page'}, {row.item!r}", row


def refusal_of(text):
    """The rule under which the package refuses one text of an example, or
    None where it reads the text. The stage text is elaborated, and the call
    that ends the text, where it has one, is evaluated with `stage` naming
    that stage and `methods` the methods file of the text."""
    try:
        stage = elaborate_text(text.stage, "t.bl")
        if text.call is not None:
            methods = None if text.methods is None else {"text": text.methods, "origin": "m.bl"}
            eval(text.call, {"stage": stage, "methods": methods})
    except ConstructionError as refused:
        return refused.rule
    return None


def page_sections():
    """The text of each numbered section of the page of the rules, by its
    number, on one line, and the number of the section that holds the
    printed table of the rules not yet checked, None where no section holds
    it. A section runs from its heading to the next numbered heading, and a
    heading inside a fenced block is no heading."""
    sections, label, fenced, table = {}, None, False, None
    for line in (DOCS / APPENDIX).read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        found = None if fenced else NUMBERED_HEADING.match(line)
        if found is not None:
            label = found.group(2)
            sections[label] = []
        elif label is not None:
            sections[label].append(line)
            if line.strip() == OPENING_MARKER:
                table = label
    return {label: " ".join(" ".join(lines).split()) for label, lines in sections.items()}, table


def test_item_1_every_function_a_row_names_resolves_by_import_and_attribute_lookup():
    problems = []
    for row in SEMANTIC_RULES:
        for name in row.implements + row.checks:
            try:
                held = resolve(name)
            except (ImportError, AttributeError) as error:
                problems.append(f"{row.section}, {row.item!r}: {name} does not resolve ({error})")
                continue
            if not (inspect.isroutine(held) or isinstance(held, property)):
                problems.append(
                    f"{row.section}, {row.item!r}: {name} is a {type(held).__name__}, and a "
                    f"row names functions, methods and properties"
                )
    assert not problems, reported(problems)


def test_item_2_every_test_a_row_names_is_one_that_pytest_collects():
    named = {row.test for row in SEMANTIC_RULES if row.test is not None}
    files = sorted({test.split("::", 1)[0] for test in named})
    absent = [file for file in files if not (ROOT / file).is_file()]
    assert not absent, f"the rows name test files that do not exist: {absent}"
    if not files:
        return
    # the tests pytest collects in the files the rows name, each by its
    # path from the repository's root, its function and its case
    root = ("--rootdir", str(ROOT), "-c", str(ROOT / "pytest.ini"))
    run = subprocess.run(
        [sys.executable, "-m", "pytest", *COLLECT, *root, *files],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")},
    )
    assert run.returncode == 0, f"pytest did not collect {files}\n{run.stdout}\n{run.stderr}"
    collected = {line.strip() for line in run.stdout.splitlines() if "::" in line}
    # a row names one collected case, or a function with every case of it
    problems = [
        f"{test} is no test that pytest collects"
        for test in sorted(named)
        if test not in collected and not any(held.startswith(test + "[") for held in collected)
    ]
    assert not problems, reported(problems)


def test_item_3_every_refusal_a_row_names_is_a_rule_of_the_refusal_catalogue():
    rules = every_rule()
    problems = [
        f"{row.section}, {row.item!r}: {rule!r} is no rule of the three vocabularies"
        for row in SEMANTIC_RULES
        for rule in row.refusals
        if rule not in rules
    ]
    assert not problems, reported(problems)


def test_item_4_the_sections_of_the_rows_are_the_sections_and_rules_of_the_page():
    page = (DOCS / APPENDIX).read_text(encoding="utf-8")
    on_the_page = set(SECTION_HEADING.findall(page))
    assert on_the_page, f"docs/{APPENDIX} holds no heading of a section 2.n or of a rule Rn"
    in_the_table = {row.section for row in SEMANTIC_RULES}
    assert in_the_table == on_the_page, (
        f"sections of the page with no row: {sorted(on_the_page - in_the_table)}; "
        f"sections of rows that the page does not hold: {sorted(in_the_table - on_the_page)}"
    )


def test_item_5_every_rule_the_package_refuses_under_has_a_row_or_a_page_that_states_it():
    rules = every_rule()
    in_rows = {rule for row in SEMANTIC_RULES for rule in row.refusals}
    problems = [
        f"the rule {rule!r} stands in no row and RULES_STATED_ELSEWHERE names no page for it"
        for rule in sorted(rules - in_rows - set(RULES_STATED_ELSEWHERE))
    ]
    problems += [
        f"RULES_STATED_ELSEWHERE names {rule!r}, which is no rule of the three vocabularies"
        for rule in sorted(set(RULES_STATED_ELSEWHERE) - rules)
    ]
    problems += [
        f"RULES_STATED_ELSEWHERE names the page {page} for {rule!r}, and docs/ holds no such page"
        for rule, page in RULES_STATED_ELSEWHERE.items()
        if not (DOCS / page).is_file()
    ]
    assert not problems, reported(problems)


def test_item_6_the_example_of_every_rule_not_yet_checked_is_read_or_refused_as_its_row_says():
    rules = every_rule()
    problems = []
    for row in SEMANTIC_RULES:
        held = (row.package_today, row.example, row.also_concerns, row.see_also, row.refused_under)
        if row.checked and any(held):
            problems.append(
                f"{row.section}, {row.item!r}: a checked row holds none of `package_today`, "
                f"`example`, `also_concerns`, `see_also` and `refused_under`"
            )
    # a row whose example no longer behaves as it says is stale: where the
    # package now checks the rule, a row of SEMANTIC_RULES is given
    # checked=True with its functions, its refusals and a test, and a row of
    # UNCHECKED_ELSEWHERE is removed
    for where, row in unchecked_rows():
        if not row.package_today or not row.example:
            problems.append(f"{where}: a rule not yet checked holds `package_today` and `example`")
            continue
        if row.refused_under is not None and row.refused_under not in rules:
            problems.append(f"{where}: {row.refused_under!r} is no rule of the three vocabularies")
        for text in example_texts(row.example):
            try:
                refused = refusal_of(text)
            except Exception as error:  # a failure of any other class makes the row stale
                first = " ".join(str(error).split())[:300]
                problems.append(
                    f"{where}: the package answers {type(error).__name__} to the example: {first}"
                )
                continue
            if refused == row.refused_under:
                continue
            if row.refused_under is None:
                problems.append(
                    f"{where}: the package no longer reads the example and refuses it under "
                    f"{refused}"
                )
            elif refused is None:
                problems.append(
                    f"{where}: the package now reads the example, which its row says is refused "
                    f"under {row.refused_under}"
                )
            else:
                problems.append(
                    f"{where}: the package refuses the example under {refused}, and its row "
                    f"names {row.refused_under}"
                )
    if problems:
        pytest.fail(reported(problems), pytrace=False)


def test_item_7_the_rules_not_yet_checked_and_the_pages_that_point_to_them_name_each_other():
    sections, table = page_sections()
    assert table is not None, (
        f"no numbered section of docs/{APPENDIX} holds the marker {OPENING_MARKER} of the "
        f"printed table of the rules not yet checked"
    )
    in_the_rule_sections = set(SECTION_HEADING.findall((DOCS / APPENDIX).read_text("utf-8")))
    problems = []
    # each section and each page that a row names stands
    for where, row in unchecked_rows():
        for label in row.sections:
            if label not in sections:
                problems.append(f"{where}: docs/{APPENDIX} holds no section {label}")
        for path, section in row.see_also:
            page = DOCS / path
            if not page.is_file():
                problems.append(f"{where}: docs/ holds no page {path}")
            elif not re.search(
                rf"^#+ {re.escape(section)} ", page.read_text(encoding="utf-8"), re.MULTILINE
            ):
                problems.append(f"{where}: docs/{path} holds no section {section}")
    for row in UNCHECKED_ELSEWHERE:
        stated = sorted(set(row.sections) & in_the_rule_sections)
        if stated:
            problems.append(
                f"{row.item!r}: a rule of {', '.join(stated)} is a row of SEMANTIC_RULES, and "
                f"UNCHECKED_ELSEWHERE holds the rules that those sections do not state"
            )
        if not row.sections and not row.see_also:
            problems.append(f"{row.item!r}: the row names no section and no page that states it")
    rows = [row for _, row in unchecked_rows()]
    named_sections = {label for row in rows for label in row.sections}
    named_pages = {path for row in rows for path, _ in row.see_also}
    # a pointer of the page of the rules to its own table: a parenthesis
    # that cites the table's section after the other sections it cites
    own = re.compile(r"\((?:(?:§\d+(?:\.\d+)?|R\d+), )*§" + re.escape(table) + r"\)")
    for label, text in sections.items():
        if label != table and own.search(text) and label not in named_sections:
            problems.append(
                f"section {label} of docs/{APPENDIX} points to §{table} for a rule not yet "
                f"checked, and no row names that section"
            )
    # a pointer of another page: a parenthesis that links the page of the
    # rules and cites the table's section
    other = re.compile(
        r"\(\[Appendix C\]\([^)]*"
        + re.escape(posixpath.basename(APPENDIX))
        + r"[^)]*\) §"
        + re.escape(table)
        + r"\)"
    )
    pointing = 0
    for page in sorted(LANGUAGE_PAGES.rglob("*.md")):
        path = page.relative_to(DOCS).as_posix()
        if path == APPENDIX or not other.search(" ".join(page.read_text("utf-8").split())):
            continue
        pointing += 1
        if path not in named_pages:
            problems.append(
                f"docs/{path} points to §{table} of the page of the rules for a rule not yet "
                f"checked, and no row names that page"
            )
    assert not problems, reported(problems)
    assert pointing, "no page of the language points to the table, so the test finds no pointer"
