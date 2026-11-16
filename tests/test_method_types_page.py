"""The page of the method types, `docs/Bellman-Sym/reference/methods.md`: its
entries as the records of the package print them, a representation family
registered later, its fragments and links, the sources of its entries, and
the declaration example of each entry."""

import contextlib
import re
import subprocess
import sys
from collections import Counter

import pytest
from application_files import ROOT, checkout_environment
from documentation_pages import link_target_path, links, reference_entries, slugify
from documentation_paths import DOCS, HOOKS, METHODS_PAGE

# the generator of the methods page, the source of a definition and the
# anchor of an entry, from the generator that writes the pages, which the
# import of documentation_pages above puts on the module path
from reference_pages import anchor_of as row_anchor
from reference_pages import methods_table, source_location
from skips import environment_without_git_variables, require_git_checkout
from stage_builders import methodized_copy
from stage_texts import GRID_VALUES

from bellman.native.hypergraphs import copy_native
from bellman.native.records import NO_REGISTERED_ARGUMENTS, OMISSIONS, EntryText, MethodOption
from bellman.refusals import ConstructionError
from bellman.stage.grids import GRID_CONSTRUCTORS
from bellman.stage.method_table import METHOD_TYPES
from bellman.stage.representations import RepresentationFamily, families, register, unregister

# the methods page, `METHODS_PAGE`, as a path under docs/, the form in which a
# link of another page reaches it
METHODS_PAGE_IN_DOCS = "Bellman-Sym/reference/methods.md"


# the source part of an entry's links: the module, the definition, the line,
# and the sentence of the public link
SOURCE_SENTENCE = re.compile(r"source `([^`]+)`, `([^`]+)`, line (\d+); ([^;]+)")


# the fragments of the methods page that links name: the anchor of each method
# type, `egm` to `fues`, and the anchors of the first sections, which the page
# keeps above its headings
PRESERVED_FRAGMENTS = (
    "egm", "vfi", "time-iteration", "explicit", "linear", "pchip", "closed-form",
    "gauss-hermite", "quadrature", "exact", "exact-markov", "markov", "markov-expectation",
    "sum", "tauchen", "deterministic", "histogram", "identity", "monte-carlo", "max",
    "discrete-choice", "golden-section", "scipy-bounded", "root-find", "newton",
    "analytic-inverse", "fues", "1-reading-the-table", "2-the-table", "3-the-grid",
)  # fmt: skip


# The two tables below give the stage on which the declaration example of a
# method type or a grid constructor is methodized, by the name of the stage's
# fixture: a stage that has the places that the example names, read in one
# call of `methodize` with the additions that `example_additions` names for
# the stage. The examples name places of several stages, since each shows its
# method where the applications write it. The examples of `!explicit`,
# `!Points` and `!Fibred` have tests of their own. This table holds the
# examples that name no setting.
EXAMPLES_WITHOUT_SETTINGS = {
    "time-iteration": "cons_savings_iid",
    "closed-form": "perfect_foresight_explicit",
    "quadrature": "cons_savings_iid",
    "exact": "cons_savings_iid",
    "exact-markov": "example_shocks",
    "markov": "example_shocks",
    "markov-expectation": "example_shocks",
    "sum": "example_shocks",
    "deterministic": "cons_savings_iid",
    "identity": "cons_savings_iid",
    "max": "cons_savings_iid",
    "discrete-choice": "cons_savings_iid",
    "scipy-bounded": "cons_savings_iid",
    "root-find": "port",
    "newton": "port",
    "analytic-inverse": "cons_savings_iid",
    "FUES": "worker_cons",
}


# the examples that name a count of a grid factor or a keyword whose values
# are restricted, each with its stage
EXAMPLES_WITH_A_RESTRICTED_SETTING = {
    "egm": "cons_savings_iid",
    "vfi": "cons_savings_iid",
    "Linear": "perfect_foresight",
    "pchip": "port",
    "gauss-hermite": "buffer_stock",
    "tauchen": "tenure",
    "histogram": "perfect_foresight",
    "monte-carlo": "cons_savings_iid",
    "golden_section": "cons_savings_iid",
    "Cartesian": "cons_savings_iid",
}


def page_fragments(text):
    """Every fragment of a page, an `<a id>` anchor or the anchor that MkDocs
    gives a heading, outside fenced blocks, with repetitions."""
    held = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    anchors = re.findall(r'<a id="([^"]+)"></a>', held)
    headings = [
        slugify(heading, "-") for heading in re.findall(r"^#{2,6}\s+(.*\S)", held, re.MULTILINE)
    ]
    return anchors + headings


def recorded_words():
    """The word of each method type and each grid constructor, with its `!`,
    in the order of `METHOD_TYPES` and `GRID_CONSTRUCTORS`: the words whose
    entries the methods page holds."""
    return [f"!{name}" for name in (*METHOD_TYPES, *GRID_CONSTRUCTORS)]


def record_of(name):
    """The record of the method type or the grid constructor `name`, written
    without its `!`."""
    return METHOD_TYPES[name] if name in METHOD_TYPES else GRID_CONSTRUCTORS[name]


def listed_arguments(name):
    """The arguments that the record of `name` lists, by name: the keywords of
    a method type, or the arguments of a grid constructor."""
    record = record_of(name)
    return record["keywords"] if name in METHOD_TYPES else record.arguments


def spline_family(required):
    """A representation family `!spline` defined in this module, its degree
    required or optional: one definition, changed between the two."""
    return RepresentationFamily(
        "spline",
        {
            "degree": MethodOption(
                "positive integer", required=required, description="The degree of the spline."
            )
        },
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


@contextlib.contextmanager
def registered_spline(required):
    """`!spline` of `spline_family(required)` registered for the statements of
    a `with` block, and removed when the block ends."""
    register(spline_family(required=required))
    try:
        yield
    finally:
        unregister("spline")


def generated_entry(word):
    """The entry of `word` in the methods page as the generator writes it now,
    or None where it writes none."""
    held = [entry for entry in reference_entries(methods_table(METHODS_PAGE)) if entry[1] == word]
    return held[0] if held else None


def example_settings(example):
    """The declarations of the settings an example names, with a valid value
    of each and, for its first count or keyword, an invalid value and the
    rule that refuses it: a count in a grid factor below two under
    `grid-bounds`, and a keyword's value outside its set under
    `method-option-value`."""
    keywords = re.findall(r"!\w+\(([^()]*)\)", example)
    named = [name for group in keywords for name in re.findall(r"=\s*(\w+)", group)]
    factors = [
        name.strip()
        for group in re.findall(r"=\(([^()]*)\)", example)
        for name in group.split(",")
    ]
    declarations, values, invalid = [], {}, None
    for name in dict.fromkeys(named + factors):
        if name.startswith("n_"):
            declarations.append(f"{name} : ℕ")
            values[name] = 3
            if invalid is None:
                rule = "method-option-value" if name in named else "grid-bounds"
                # a keyword's value 0 lies outside its set; a factor's count
                # of 1 lies below the two nodes that a grid factor needs
                invalid = (name, 0 if rule == "method-option-value" else 1, rule)
        elif name.endswith(("_min", "_max")):
            declarations.append(f"{name} : ℝ₊")
            values[name] = 0.5 if name.endswith("_min") else 5.0
    if "A_points" in example:
        declarations.append("A_points : ℝ₊ × ℝ₊ × ℝ₊")
        values["A_points"] = [0.5, 1.0, 2.0]
    return declarations, values, invalid


@pytest.fixture(scope="module")
def methods_page_text():
    """The text of the methods page."""
    return (ROOT / METHODS_PAGE).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def page_entries(methods_page_text):
    """The entries of the methods page, as `reference_entries` reads them."""
    return reference_entries(methods_page_text)


@pytest.fixture
def commit_with_an_ai_folder(tmp_path):
    """The folder of the git data of a new repository in a temporary folder,
    and the hash of its one commit, which holds a folder named `AI`, as a
    commit of the development repository does and no exported revision
    does, or a skip of the test outside a git checkout."""
    require_git_checkout()
    folder = tmp_path / "repository"
    (folder / "AI").mkdir(parents=True)
    (folder / "AI" / "README.md").write_text("The internal folder.\n", encoding="utf-8")
    settings = (
        "-c", "user.name=test", "-c", "user.email=test@example.org", "-c", "commit.gpgsign=false",
    )  # fmt: skip

    def git(*arguments):
        return subprocess.run(
            ["git", "-C", str(folder), *settings, *arguments],
            capture_output=True,
            text=True,
            check=True,
            env=environment_without_git_variables(),
        ).stdout.strip()

    git("init", "-q")
    git("add", "AI")
    git("commit", "-q", "--no-verify", "-m", "a commit that holds the internal folder")
    return folder / ".git", git("rev-parse", "HEAD")


def test_the_methods_page_holds_an_entry_for_each_method_type_then_each_grid_constructor(
    page_entries,
):
    """The methods page holds one entry for each method type of `METHOD_TYPES`,
    registered representation families included, then one for each grid
    constructor of `GRID_CONSTRUCTORS`, in the order of those tables and no
    other."""
    words = [word for _, word, _, _ in page_entries]
    assert words == (
        [f"!{word}" for word in METHOD_TYPES] + [f"!{word}" for word in GRID_CONSTRUCTORS]
    )


def test_each_entry_of_the_methods_page_carries_the_anchor_of_its_word(page_entries):
    """Each entry of the methods page carries the anchor that the generator
    gives its word, such as `golden-section` for `!golden_section`."""
    held = {word: anchor for anchor, word, _, _ in page_entries}
    assert held == {word: row_anchor(word[1:]) for word in recorded_words()}


def test_each_entry_of_the_methods_page_holds_the_parts_of_an_entry_in_their_order(page_entries):
    """Each entry holds the parts Declaration, Type parameters, Arguments,
    Compatibility, Example, Availability and Links in that order, with Factor
    forms before Compatibility where the entry's grid constructor has factor
    forms, and Stored data after it where the entry's method type is a
    representation family."""
    held = {word: list(parts) for _, word, parts, _ in page_entries}
    expected = {}
    for word in recorded_words():
        name = word[1:]
        constructor = GRID_CONSTRUCTORS.get(name)
        forms = ["Factor forms"] if constructor is not None and constructor.forms else []
        stored = ["Stored data"] if name in families() else []
        expected[word] = [
            "Declaration", "Type parameters", "Arguments", *forms, "Compatibility", *stored,
            "Example", "Availability", "Links",
        ]  # fmt: skip
    assert held == expected


def test_the_stored_data_of_each_representation_family_is_the_sentence_of_its_record(
    page_entries,
):
    """The Stored data part of the entry of each representation family of
    `families()` is the stored-data sentence of the family's record, its
    lines joined into one."""
    held = {
        word: parts["Stored data"] for _, word, parts, _ in page_entries if word[1:] in families()
    }
    assert held == {
        f"!{name}": " ".join(family.stored.split()) for name, family in families().items()
    }


def test_an_entry_lists_the_arguments_of_its_record_with_their_type_and_when_left_out(
    page_entries,
):
    """The argument table of each entry whose record lists arguments holds
    them in the record's order, each with its type and the sentence of the
    column `when left out`, what leaving the argument out means."""
    held = {word: rows for _, word, _, rows in page_entries if listed_arguments(word[1:])}
    listed = {word: listed_arguments(word[1:]) for word in recorded_words()}
    listed = {word: arguments for word, arguments in listed.items() if arguments}
    assert {word: [row[0].strip("`") for row in rows] for word, rows in held.items()} == {
        word: list(arguments) for word, arguments in listed.items()
    }
    # `OMISSIONS` holds the sentence of the column `when left out` of each
    # kind of argument
    assert {word: [(row[1], row[2]) for row in rows] for word, rows in held.items()} == {
        word: [(option.kind, OMISSIONS[option.omission]) for option in arguments.values()]
        for word, arguments in listed.items()
    }


def test_an_entry_whose_record_lists_no_argument_states_that_it_has_no_registered_ones(
    page_entries,
):
    """The Arguments part of each entry whose record lists no argument is the
    sentence `NO_REGISTERED_ARGUMENTS`, that a keyword the record does not
    list is kept for the numerical handler."""
    held = {
        word: parts["Arguments"]
        for _, word, parts, _ in page_entries
        if not listed_arguments(word[1:])
    }
    unlisted = [word for word in recorded_words() if not listed_arguments(word[1:])]
    assert held == dict.fromkeys(unlisted, NO_REGISTERED_ARGUMENTS)


def test_the_compatibility_of_each_entry_holds_the_compatibility_text_of_its_record(
    page_entries,
):
    """The Compatibility part of each entry holds the compatibility text of
    its record, its lines joined into one."""
    held = {
        word: " ".join(record_of(word[1:]).text.compatibility.split()) in parts["Compatibility"]
        for _, word, parts, _ in page_entries
    }
    assert held == dict.fromkeys(recorded_words(), True)


def test_the_compatibility_of_a_method_that_reads_a_grid_links_the_constructors_admitting_it(
    page_entries,
):
    """The Compatibility part of the entry of each method type that reads a
    grid links first the grid constructors whose sites admit that grid, in
    the order of `GRID_CONSTRUCTORS`."""
    expected = {
        f"!{word}": [
            name for name, grid in GRID_CONSTRUCTORS.items() if record.grid in grid.sites.readers
        ]
        for word, record in METHOD_TYPES.items()
        if record.grid is not None
    }
    held = {}
    for _, word, parts, _ in page_entries:
        record = METHOD_TYPES.get(word[1:])
        if record is None or record.grid is None:
            continue
        linked = re.findall(r"\[`!(\w+)`\]\(#", parts["Compatibility"])
        held[word] = linked[: len(expected.get(word, ()))]
    assert held == expected


def test_the_declaration_of_each_grid_constructor_writes_each_form_of_its_syntax(page_entries):
    """The Declaration part of the entry of each grid constructor writes each
    form of the constructor's syntax as code."""
    held = {
        word: [
            form
            for form in GRID_CONSTRUCTORS[word[1:]].syntax
            if f"`{form}`" in parts["Declaration"]
        ]
        for _, word, parts, _ in page_entries
        if word[1:] in GRID_CONSTRUCTORS
    }
    assert held == {f"!{name}": list(record.syntax) for name, record in GRID_CONSTRUCTORS.items()}


def test_the_entry_of_a_registered_family_stands_right_after_the_families_of_the_package():
    """The entry of a representation family registered after those of the
    package stands right after the entry of the last of them."""
    base = list(families())
    with registered_spline(required=True):
        words = [word for _, word, _, _ in reference_entries(methods_table(METHODS_PAGE))]
    assert words.index("!spline") == words.index(f"!{base[-1]}") + 1


def test_the_stored_data_of_a_registered_family_is_the_sentence_of_its_definition():
    """The Stored data part of the entry of a registered family is the
    stored-data sentence of its definition."""
    with registered_spline(required=True):
        _, _, parts, _ = generated_entry("!spline")
        assert parts["Stored data"] == families()["spline"].stored


def test_the_source_of_a_registered_family_names_the_file_defining_it_and_no_public_link():
    """The links of the entry of a registered family name, as its source, the
    file that defines it, and state its public link unavailable."""
    with registered_spline(required=True):
        _, _, parts, _ = generated_entry("!spline")
    assert (
        "test_method_types_page.py" in parts["Links"]
        and "public link unavailable" in parts["Links"]
    )


@pytest.mark.parametrize(
    ("required", "left_out"),
    [(True, "refused"), (False, "omitted")],
    ids=["degree-required", "degree-optional"],
)
def test_the_entry_of_a_registered_family_says_what_leaving_out_the_degree_means_by_definition(
    required, left_out
):
    """The argument row of the degree in the entry of `!spline` says what
    leaving the degree out means as the family's definition gives it: an
    entry that leaves it out is refused where the degree is required, and
    no value is supplied where it is optional."""
    with registered_spline(required=required):
        _, _, _, arguments = generated_entry("!spline")
    # the first three cells of the first argument row: the argument, its type
    # and what leaving it out means
    assert arguments[0][:3] == ["`degree`", "positive integer", OMISSIONS[left_out]]


def test_methodize_refuses_a_family_without_its_required_degree_and_admits_it_once_optional(
    cons_savings_iid,
):
    """Methodize refuses `!spline` written without its degree under
    `method-admission` while the family's definition requires the degree,
    and admits the same line once the definition makes the degree
    optional."""
    without_degree = "dcsn_to_arvl.evaluate.method : !spline\n"
    with registered_spline(required=True):
        with pytest.raises(ConstructionError) as refused:
            methodized_copy(cons_savings_iid, without_degree)
    assert refused.value.rule == "method-admission" and "degree" in refused.value.message
    with registered_spline(required=False):
        methodized_copy(cons_savings_iid, without_degree)


def test_methodize_admits_a_keyword_that_the_definition_of_a_family_does_not_list(
    cons_savings_iid,
):
    """Methodize admits `!spline(degree=d, smooth=s)`, although the family's
    definition lists no keyword `smooth`; a refusal fails the test."""
    with registered_spline(required=True):
        methodized_copy(
            cons_savings_iid,
            "d : ℤ\ns : ℤ\ndcsn_to_arvl.evaluate.method : !spline(degree=d, smooth=s)\n",
        )


def test_unregister_removes_the_entry_of_a_registered_family_from_the_methods_page():
    """`unregister` removes from the methods page as generated the entry of
    `!spline`, which the page holds while the family is registered."""
    with registered_spline(required=True):
        assert generated_entry("!spline") is not None
    assert generated_entry("!spline") is None


def test_two_generations_of_the_methods_page_give_the_same_text():
    """Two generations of the methods page in one process give the same
    text."""
    first, second = methods_table(METHODS_PAGE), methods_table(METHODS_PAGE)
    assert first == second


def test_the_check_of_the_generator_finds_the_methods_page_as_it_generates_it():
    """`reference_pages.py --check`, run on the methods page in a new
    interpreter, finds the page as the generator writes it."""
    run = subprocess.run(
        [sys.executable, str(HOOKS / "reference_pages.py"), "--check", "--page", METHODS_PAGE],
        cwd=str(ROOT),
        env=checkout_environment(),
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr


def test_the_methods_page_holds_neither_the_hash_of_the_checkouts_commit_nor_its_prefix(
    methods_page_text,
):
    """The methods page holds neither the hash of the commit of the checkout
    nor its first twelve characters, the form in which a link to a public
    source names a revision; the test is skipped outside a git checkout."""
    require_git_checkout()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=environment_without_git_variables(),
    ).stdout.strip()
    assert head and head not in methods_page_text and head[:12] not in methods_page_text


def test_each_fragment_of_the_methods_page_stands_once(methods_page_text):
    """Each fragment of the methods page, an anchor written in the page or the
    anchor that MkDocs gives a heading, stands on it once."""
    fragments = page_fragments(methods_page_text)
    repeated = sorted(fragment for fragment, count in Counter(fragments).items() if count > 1)
    assert repeated == []


def test_the_methods_page_keeps_each_fragment_of_preserved_fragments(methods_page_text):
    """The methods page holds every fragment of `PRESERVED_FRAGMENTS`."""
    assert sorted(set(PRESERVED_FRAGMENTS) - set(page_fragments(methods_page_text))) == []


def test_every_link_on_the_methods_page_reaches_a_fragment_of_it_or_a_page(methods_page_text):
    """Every link on the methods page that stays on the site reaches a
    fragment of the page or a page that stands under docs/."""
    fragments = page_fragments(methods_page_text)
    unreached = []
    for number, _, _, target in links(methods_page_text):
        if target.startswith("#"):
            if target[1:] not in fragments:
                unreached.append(f"line {number}: {target} reaches no fragment of the page")
        elif "://" not in target:
            reached = link_target_path(METHODS_PAGE_IN_DOCS, target)
            if reached is None or not (DOCS / reached).is_file():
                unreached.append(f"line {number}: {target} reaches no page")
    assert unreached == []


def test_every_link_of_the_documentation_into_the_methods_page_reaches_a_fragment_of_it(
    methods_page_text,
):
    """Every link of a page under docs/ that names a fragment of the methods
    page reaches a fragment that the page holds."""
    fragments = page_fragments(methods_page_text)
    unreached = []
    for path in sorted(DOCS.rglob("*.md")):
        for number, _, _, target in links(path.read_text(encoding="utf-8")):
            within = path.relative_to(DOCS).as_posix()
            if "#" in target and link_target_path(within, target) == METHODS_PAGE_IN_DOCS:
                if target.split("#", 1)[1] not in fragments:
                    unreached.append(f"{within}:{number}: {target} reaches no fragment")
    assert unreached == []


def test_the_source_of_each_entry_names_a_line_of_the_checkout_that_defines_its_word(
    page_entries,
):
    """The source in the links of each entry names a module of the package
    and a line of it that defines the entry's word: for a grid constructor
    the line holds the entry of its term class, and for a method type the
    word in quotes stands on that line or on one of the two after it."""
    sources = {word: SOURCE_SENTENCE.search(parts["Links"]) for _, word, parts, _ in page_entries}
    assert {word: found is not None for word, found in sources.items()} == dict.fromkeys(
        recorded_words(), True
    )
    undefined = []
    for word, found in sources.items():
        module, _, line, _ = found.groups()
        held = (ROOT / "packages/bellman/bellman" / module).read_text(encoding="utf-8")
        held = held.splitlines()
        # `line` counts from 1, and `held` from 0
        if word[1:] in GRID_CONSTRUCTORS:
            defines = f"T.{GRID_CONSTRUCTORS[word[1:]].term.__name__}:" in held[int(line) - 1]
        else:
            # a call may write its first argument on the line after the one
            # that opens it, so the line and the two after it are read
            defines = f'"{word[1:]}"' in " ".join(held[int(line) - 1 : int(line) + 2])
        if not defines:
            undefined.append(word)
    assert undefined == []


def test_each_entry_states_that_its_public_link_is_unavailable(page_entries):
    """The source in the links of each entry states its public link
    unavailable, since no exported revision of the package holds the
    definitions."""
    sources = {word: SOURCE_SENTENCE.search(parts["Links"]) for _, word, parts, _ in page_entries}
    assert {word: found is not None for word, found in sources.items()} == dict.fromkeys(
        recorded_words(), True
    )
    # the fourth part of the source sentence is that of the public link
    linked = [
        word
        for word, found in sources.items()
        if not found.group(4).startswith("public link unavailable")
    ]
    assert linked == []


def test_a_revision_that_holds_a_folder_named_ai_is_refused_as_the_exported_revision(
    commit_with_an_ai_folder, monkeypatch
):
    """`source_location` refuses as the exported revision a commit whose tree
    holds a folder `AI`, as a commit of the development repository does; the
    test is skipped outside a git checkout."""
    # git reads the repository that GIT_DIR names, so the generator asks the
    # repository of the fixture about its one commit
    git_folder, revision = commit_with_an_ai_folder
    monkeypatch.setenv("GIT_DIR", str(git_folder))
    with pytest.raises(SystemExit, match="no exported revision"):
        source_location("egm", METHOD_TYPES["egm"], "row", revision=revision)


def test_the_tables_of_the_examples_name_each_method_type_and_grid_constructor_once():
    """The tables of the declaration examples, with the three examples that
    have tests of their own, name each method type and each grid constructor
    once, so that the example of every entry is read."""
    named = [
        *EXAMPLES_WITHOUT_SETTINGS, *EXAMPLES_WITH_A_RESTRICTED_SETTING, "explicit", "Points",
        "Fibred",
    ]  # fmt: skip
    assert sorted(named) == sorted([*METHOD_TYPES, *GRID_CONSTRUCTORS])


@pytest.mark.parametrize(
    ("word", "stage_name"),
    EXAMPLES_WITHOUT_SETTINGS.items(),
    ids=list(EXAMPLES_WITHOUT_SETTINGS),
)
def test_a_declaration_example_that_names_no_setting_is_methodized_on_its_stage(
    request, example_additions, word, stage_name
):
    """The declaration example of the entry of `word`, which names no
    setting, is methodized on the stage of `stage_name` after the additions
    that write its place where the stage file does not; a refusal fails the
    test."""
    example = record_of(word).text.example
    assert example_settings(example) == ([], {}, None)
    stage = request.getfixturevalue(stage_name)
    methodized_copy(stage, *example_additions.get(stage_name, ()), example + "\n")


@pytest.mark.parametrize(
    ("word", "stage_name"),
    EXAMPLES_WITH_A_RESTRICTED_SETTING.items(),
    ids=list(EXAMPLES_WITH_A_RESTRICTED_SETTING),
)
def test_configure_admits_valid_settings_of_an_example_and_refuses_an_invalid_count_or_keyword(
    request, example_additions, word, stage_name
):
    """Configure admits valid values of the settings that the declaration
    example of `word` names, once the example is methodized on the stage of
    `stage_name`, and refuses an invalid value of its first count or keyword
    under the rule that `example_settings` gives it: `grid-bounds` for a
    count of a grid factor, and `method-option-value` for a keyword."""
    example = record_of(word).text.example
    declarations, values, invalid = example_settings(example)
    assert invalid is not None
    # a grid stands at a place with the method that reads it: the example of
    # `!Cartesian` writes the grid of the policy builder, which `!egm` reads
    context = {"Cartesian": "policy.method : !egm\n"}.get(word, "")
    text = "\n".join([*declarations, context + example]) + "\n"
    stage = request.getfixturevalue(stage_name)
    bound = methodized_copy(stage, *example_additions.get(stage_name, ()), text)
    copy_native(bound).configure({"settings": values})
    setting, value, rule = invalid
    with pytest.raises(ConstructionError) as refused:
        copy_native(bound).configure({"settings": {**values, setting: value}})
    assert refused.value.rule == rule, (word, refused.value.message)


def test_methodize_admits_the_example_of_explicit_only_on_a_stage_that_declares_its_names(
    perfect_foresight, cons_savings_iid
):
    """Methodize admits the declaration example of `!explicit` on the
    perfect-foresight stage, which declares the names that its line writes,
    and refuses it under `name-in-scope` on the stage of the fixture
    `cons_savings_iid`, which declares no `ρ`."""
    example = METHOD_TYPES["explicit"].text.example
    assert example_settings(example) == ([], {}, None)
    methodized_copy(perfect_foresight, example + "\n")
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(cons_savings_iid, example + "\n")
    assert refused.value.rule == "name-in-scope"


def test_the_example_of_points_is_configured_with_the_points_that_it_declares(cons_savings_iid):
    """The declaration example of `!Points`, methodized on the stage of the
    fixture `cons_savings_iid` with the declaration of its points, is
    configured with three points; a refusal fails the test."""
    example = GRID_CONSTRUCTORS["Points"].text.example
    declarations, values, invalid = example_settings(example)
    assert (values, invalid) == ({"A_points": [0.5, 1.0, 2.0]}, None)
    bound = methodized_copy(cons_savings_iid, "\n".join([*declarations, example]) + "\n")
    copy_native(bound).configure({"settings": values})


def test_the_example_of_the_fibred_grid_is_configured_on_the_stage_named_grids(
    grid_stage_with_one_addition,
):
    """The declaration example of `!Fibred`, typed on the stage `grids` of the
    fixture `grid_stage_with_one_addition` after `cntn_to_dcsn.method : !vfi`,
    whose grid it writes, is configured with the values of the grid settings of
    that stage; a refusal fails the test."""
    stage = grid_stage_with_one_addition(
        "cntn_to_dcsn.method : !vfi\n" + GRID_CONSTRUCTORS["Fibred"].text.example + "\n"
    )
    stage.configure({"settings": GRID_VALUES})
