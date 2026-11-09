"""The acceptance file of units D4 and D5 of the implementation plan of
Model Interface 0.9, the author-facing sentences and the rules' entries.

D4's tests, `test_item_<n>_<claim>`, close items 1 and 2 of the plan's §2 D4;
items 3 and 4, the printed refusals page and the elaboration baseline, are
recorded in D4's report. D5's tests, `test_d5_item_<n>_<claim>`, close items
1 to 3 of the plan's §2 D5: the three vocabularies, the anchors of the
Refusals page and the development record agree, and every rule is classified;
the site builds strictly with every rule anchored; and the catalogue's entry
answers every rule in under a second, in the checkout and from the installed
package alone. D5's item 4, the Workbench's Rule link,
is a test of `packages/bellman-workbench/tests/test_spec09_diagnostics.py`.

The catalogue is `bellman.refusal_catalogue.catalogue`, which provokes the
example of every rule and runs the example's corrected form, `write` of
`bellman.refusal_examples.EXAMPLES`, through the operation that refused the
example; `entry` answers one rule's entry, that rule's example alone run.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time

import pytest
from conftest import ROOT

from bellman import refusal_catalogue
from bellman.refusal_catalogue import VOCABULARIES, catalogue, entry, operation, refusal_of
from bellman.refusal_examples import EXAMPLES, corrected

# the five rules whose sentence addresses a Python caller and keeps the names
# of the calls it is raised by
PUBLIC_API = (
    "kernel-form", "kernel-target", "target-not-found", "target-ambiguous", "target-version"
)

# what no author-facing sentence carries, each a pattern with its name: a
# code of an amendment, a decision or a specification, a documentation path,
# a Python module, type, call or attribute name, an internal identity, the
# retired target vocabulary, and an em dash
CODES = (
    (r"AMD-", "an amendment code"),
    (r"§", "a section sign"),
    (r"\b[A-Z]\d\d\b", "a decision or an evidence code"),
    (r"\bspec(?:ification)? 0\.\d", "a specification number"),
    (r"docs/", "a documentation path"),
    (r"—", "an em dash"),
)
PYTHON = (
    (r"\.py\b", "a module name"),
    (r"\b(?:str|dict|int|float|bool|NoneType)\b", "a Python type name"),
    (r"\bStatement\(|\b(?:FuncDef|CorrDef|Typer)\b", "a term class name"),
    (r"\[\x27|\{\x27", "a Python list or mapping as printed"),
    (r"\bload_stage\b|\belaborate_stage\b|\bkernel\(|\bcompile_kernel\b|\.calibration\b"
     r"|\.list\(\)", "a Python call or attribute"),
    (r"\b\w+:(?:arvl|dcsn|cntn|shck|distribution|function|typing|G|g):\w",
     "an internal identity"),
    (r":(?:Expectation|Evaluation|Aggregation|Pullback|Substitution|Derivative|Argmax)\b",
     "an internal identity"),
    (r"Method target", "the retired target vocabulary"),
)


def found(text, patterns):
    """The names of the patterns `text` holds, each with the text matched."""
    return [
        (name, re.search(pattern, text).group())
        for pattern, name in patterns
        if re.search(pattern, text)
    ]


def test_item_1_no_author_facing_sentence_carries_a_code_a_python_name_or_an_internal_identity(
    catalogue_entries,
):
    held = {}
    for each in catalogue_entries:
        if each.rule in PUBLIC_API:
            continue
        # a factory action may name the keyword argument a Python caller
        # writes, `fill={...}`; every other part is read by an author
        factory = each.vocabulary == "the Bellman factory"
        parts = (
            ("why", each.why, CODES + PYTHON),
            ("write", each.write, CODES if factory else CODES + PYTHON),
        )
        for part, text, patterns in parts:
            for name, matched in found(text, patterns):
                held[(each.rule, part, name)] = matched
    assert held == {}


def test_item_2_every_example_s_corrected_form_passes_the_operation_that_refused_it(catalogue_entries):
    # the catalogue runs the corrected form of each rule's example and records
    # what it still provokes; the examples outside the catalogue, the second
    # readings of a rule, are run here
    assert {entry.rule: entry.corrected for entry in catalogue_entries if entry.corrected} == {}
    assert all(example.write for example in EXAMPLES.values())
    ruled = {entry.rule for entry in catalogue_entries}
    still = {}
    for name, example in EXAMPLES.items():
        if name in ruled:
            continue
        refusal = refusal_of(corrected(example))
        if refusal is not None:
            still[name] = str(refusal).splitlines()[0]
    assert still == {}


# --- unit D5: the anchors, the catalogue's entry and the development record ---

# the Refusals page, which anchors every rule by its name
REFUSALS_PAGE = ROOT / "docs" / "Bellman-Sym" / "reference" / "refusals.md"
# the operations of the Workbench, under which an author meets a refusal; a
# rule the catalogue gives the operation `query` is met by a Python caller
# through a query of the stage object, and a rule no example provokes by no
# one
AUTHOR_OPERATIONS = (
    "parse", "elaborate", "methodize", "calibrate", "configure", "connect", "read"
)
# a row of the development record: the rule linked to its entry, the
# fragment, the class and the operation that opens the producer's cell
RECORD_ROW = re.compile(
    r"^\| \[`([^`]+)`\]\([^)#]*refusals\.md#([^)]+)\) \| ([\w-]+) \| ([\w_]*):", re.MULTILINE
)


def rules():
    """Every rule of the three vocabularies, in the order the catalogue
    writes them."""
    return [rule for _, _, table in VOCABULARIES for rule in table]


def class_of(rule):
    """The class of a rule: `author-facing` where the catalogue gives it an
    operation of the Workbench, `internal` where it gives none, and
    `public-API` otherwise, where it gives `query`."""
    word = operation(rule)
    if not word:
        return "internal"
    return "author-facing" if word in AUTHOR_OPERATIONS else "public-API"


def test_d5_item_1_the_vocabularies_the_page_s_anchors_and_the_development_record_agree():
    """The Refusals page anchors every rule of the three vocabularies by its
    name, in their order, and nothing else; every rule is classified, and
    the public-API rules are those whose sentences item 1 of D4 lets name a
    Python call; the development record, found by its folder's name since
    no file outside the internal folder names a path under it, holds one
    row per rule with the rule's name as its fragment and the class and the
    operation the catalogue gives, and its history rows name no rule the
    package emits. The record's comparison is skipped in a checkout without
    the internal folder, the exported tree."""
    page = REFUSALS_PAGE.read_text(encoding="utf-8")
    assert re.findall(r'<a id="([^"]+)"></a>', page) == rules()
    classes = {rule: class_of(rule) for rule in rules()}
    assert {rule for rule, held in classes.items() if held == "public-API"} == set(PUBLIC_API)
    found = sorted(ROOT.glob("*/build-areas/model-interface/spec_0.9/rule-record.md"))
    if not found:
        pytest.skip("the development record is not in this checkout")
    (path,) = found
    record = path.read_text(encoding="utf-8")
    current, history = record.split("## 4 History rows", 1)
    rows = {
        rule: (fragment, held, word) for rule, fragment, held, word in RECORD_ROW.findall(current)
    }
    assert rows == {rule: (rule, classes[rule], operation(rule)) for rule in rules()}
    retired = {
        name
        for cell in re.findall(r"^\| ([^|]+) \|", history, re.MULTILINE)
        for name in re.findall(r"`([^`]+)`", cell)
    }
    assert retired and retired.isdisjoint(rules())


def test_d5_item_2_the_site_builds_strictly_and_its_refusals_page_anchors_every_rule(tmp_path):
    """`mkdocs build --strict` builds the documentation from the
    repository's root with no warning, so that no page links a page that is
    not there, and the built Refusals page, the page the Workbench's Rule
    link opens, holds an anchor for every rule. The other half of the item,
    that no file the export carries names a private path, is the check of
    `tests/test_housekeeping.py`."""
    pytest.importorskip("mkdocs")
    site = tmp_path / "site"
    built = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(site)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    html = (site / "Bellman-Sym" / "reference" / "refusals" / "index.html").read_text(
        encoding="utf-8"
    )
    assert [rule for rule in rules() if f'id="{rule}"' not in html] == []


@pytest.mark.parametrize("installed", [False, True], ids=["checkout", "installed"])
def test_d5_item_3_entry_answers_every_rule_from_the_installed_package_in_under_a_second(
    installed, tmp_path, monkeypatch
):
    """`entry(rule)` answers each rule of the three vocabularies in under a
    second, without raising, in the checkout and from the installed package
    alone, with the repository's root an empty folder, as it is for an
    installation outside the checkout: its vocabulary, its operation and its
    condition, and the refusal its example provokes under the rule itself;
    from the installed package, an example that reads a stage file of the
    repository is not run, and the entry gives the reason in place of the
    four parts. A name no vocabulary holds, such as the rule of the check
    `unread-input`, has no entry."""
    if installed:
        monkeypatch.setattr(refusal_catalogue, "ROOT", tmp_path)
    slow, wrong = {}, {}
    for _, _, table in VOCABULARIES:
        for rule in table:
            started = time.perf_counter()
            found = entry(rule)
            seconds = time.perf_counter() - started
            if seconds >= 1.0:
                slow[rule] = round(seconds, 2)
            example = EXAMPLES[rule]
            if installed and (example.corpus or example.stages):
                answered = not found.refusal and bool(found.why)
            else:
                answered = bool(found.refusal) and refusal_of(example).rule == rule
            if not (found.vocabulary and found.operation and found.condition and answered):
                wrong[rule] = (found.operation, found.why)
    assert slow == {} and wrong == {}
    assert entry("unread-input") is None
