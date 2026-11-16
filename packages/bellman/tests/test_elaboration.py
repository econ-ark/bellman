"""load_stage, elaborate_stage, elaborate_text and make_stage: what each
accepts, refuses and returns, with and without binding the sources of a
record, and how often a stage is copied."""

import functools
import hashlib
import json
import sys
import threading

import pytest
from application_files import (
    CONS_METHODS,
    CONS_PORT,
    CORPUS,
    DURABLES,
    DURABLES_RECIPE_WITHOUT_TENURE,
    FIRST_CALIBRATIONS,
    STAGES_WITH_BINDINGS,
)
from snapshot.record import recording_path
from stage_builders import differing_graph_triples, without_addresses
from stage_texts import UNADMITTED_FAMILY_AT_ARRIVAL, corpus_text

from bellman.factory.trellis import positions
from bellman.native import hypergraphs
from bellman.native.identity import Identity
from bellman.native.provenance import source_description
from bellman.native.records import DEFINITION_KINDS_AT_TOP_LEVEL, Sort, construction_typing_table
from bellman.refusals import FactoryError, NotConstructed
from bellman.stage import elaborate_stage, elaborate_text, load_stage, make_stage
from bellman.stage.levels import methods_source
from bellman.stage.sources import load_calibration, load_settings
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.trellis import (
    assemble_trellis,
    calibrate_trellis,
    changed_positions,
    configure_trellis,
    elaborate_trellis,
    load_trellis,
    methodize_trellis,
)

# a calibration of the Epstein-Zin savings stage that leaves out β
EZ_SAVINGS_WITHOUT_BETA = {
    name: value for name, value in FIRST_CALIBRATIONS["ez_savings"].items() if name != "β"
}


# an addition to the consumption stage that names a method no row of the
# catalogue of methods holds
UNKNOWN_METHOD = {
    "text": "@methods: cons\npolicy.method : !no_such_method\n",
    "origin": "cons.methods.bl",
}


def recorded_bindings(stage):
    """The bindings that the provenance of `stage` records, each as its verb
    and the description of its source, the last binding first."""
    bindings, provenance = [], stage.provenance
    while "operation" in provenance:
        bindings.append((provenance["operation"], dict(provenance["source"])))
        provenance = provenance["parent"]
    return bindings


def parameter_address(stage, name):
    """The address of the record of the parameter `name` in the definitions
    table of `stage`."""
    return next(
        record.address
        for record in stage.definitions.values()
        if record.kind == "parameter" and record.identity.field == name
    )


@pytest.fixture(scope="module")
def portfolio_calibration():
    """The values of the calibration file `calibration/portfolio.yml` of the
    cons-port application."""
    return load_calibration(CONS_PORT / "calibration/portfolio.yml")


@pytest.fixture(scope="module")
def consumption_settings():
    """The settings of the consumption stage in the cons-port application,
    from its file `settings/cons.yml`."""
    return load_settings(CONS_PORT / "settings/cons.yml")


@pytest.fixture(scope="module")
def consumption_addition():
    """The addition of the consumption stage of the portfolio-choice
    application, its file `methods.bl`, as a record holds it: its text and
    its origin."""
    return {"text": CONS_METHODS.read_text(encoding="utf-8"), "origin": str(CONS_METHODS)}


@pytest.fixture(scope="module")
def record_with_three_sources(portfolio_calibration, consumption_settings, consumption_addition):
    """The record of the consumption stage with a calibration, settings and
    its addition; no test changes it."""
    return {
        "stage": {"text": corpus_text("cons"), "origin": CORPUS["cons"]},
        "calibration": portfolio_calibration,
        "settings": consumption_settings,
        "methods": [consumption_addition],
    }


@pytest.fixture(scope="module")
def cons_from_load_stage(corpus_path):
    """The stage that `elaborate_stage` makes of the record that `load_stage`
    reads from the stage file of the consumption stage."""
    return elaborate_stage(load_stage(corpus_path("cons")))


@pytest.fixture(scope="module")
def cons_with_bind_false(record_with_three_sources):
    """The stage that `elaborate_stage` makes of the record with three sources
    when it is given `bind=False`."""
    return elaborate_stage(record_with_three_sources, bind=False)


@pytest.fixture(scope="module")
def cons_from_elaborate_text():
    """The stage that `elaborate_text` makes of the text of the consumption
    stage's file."""
    return elaborate_text(corpus_text("cons"), CORPUS["cons"])


@pytest.fixture(scope="module")
def cons_calibrated_by_its_record(portfolio_calibration):
    """The stage that `elaborate_stage` makes of a record of the consumption
    stage whose calibration alone holds values."""
    return elaborate_stage(
        {
            "stage": {"text": corpus_text("cons"), "origin": CORPUS["cons"]},
            "calibration": portfolio_calibration,
            "settings": {},
            "methods": {},
        }
    )


@pytest.fixture(scope="module")
def bound_and_chained(record_with_three_sources, portfolio_calibration, consumption_settings):
    """Two stages of the record with three sources: the one `elaborate_stage`
    binds, and the one the three binding verbs make of the symbolic stage
    from the same sources."""
    bound = elaborate_stage(record_with_three_sources)
    chained = (
        elaborate_stage(record_with_three_sources, bind=False)
        .calibrate(portfolio_calibration)
        .methodize(str(CONS_METHODS))
        .configure(consumption_settings)
    )
    return bound, chained


@pytest.fixture(scope="module")
def decoded_stage(corpus_path):
    """`decoded_stage(name)`: the stage that `make_stage` constructs, with no
    source positions, from the saved syntax tree of the corpus stage file
    `name`, made once for each name."""

    @functools.cache
    def make(name):
        saved = recording_path(corpus_path(name), ".ast.json").read_text(encoding="utf-8")
        return make_stage(from_json(json.loads(saved)), None)

    return make


@pytest.fixture(scope="module")
def faulty_records(record_with_three_sources):
    """Records of the consumption stage that `elaborate_stage` refuses for
    their shape, by the fault of each."""
    text = corpus_text("cons")
    return {
        "a-mapping-without-the-three-sources": {"stage": {"text": text, "origin": "cons.bl"}},
        "a-digest-that-disagrees-with-the-text": {
            "stage": {"text": text, "origin": "cons.bl"},
            "methods": {},
            "settings": {},
            "calibration": {},
            "provenance": {"sha256": "0" * 64},
        },
        "a-path-string-in-place-of-the-stage-text": {
            "stage": "applications/portfolio-choice/declaration/stages/cons/cons.bl",
            "methods": {},
            "settings": {},
            "calibration": {},
        },
        "a-path-in-place-of-the-additions": {
            **record_with_three_sources,
            "methods": str(CONS_METHODS),
        },
    }


@pytest.fixture
def copies(monkeypatch):
    """The name of the type of each value that `copy_native` copies during the
    test, counted by replacing the function in every module of the package
    that holds it."""
    copied = []
    original = hypergraphs.copy_native

    def counted(value):
        copied.append(type(value).__name__)
        return original(value)

    for name, module in list(sys.modules.items()):
        if name.startswith("bellman") and getattr(module, "copy_native", None) is original:
            monkeypatch.setattr(module, "copy_native", counted)
    return copied


def test_load_stage_reads_a_stage_file_into_a_record_with_empty_sources_its_origin_and_digest(
    corpus_path,
):
    """`load_stage` reads a stage file alone into a record of five keys with
    empty sources, whose origin is the file's path and whose digest is that
    of the text it holds."""
    record = load_stage(corpus_path("cons"))
    assert set(record) == {"stage", "calibration", "settings", "methods", "provenance"}
    # the methods of a record are its additions, none for a stage file alone
    assert (record["calibration"], record["settings"], record["methods"]) == ({}, {}, [])
    origin = str(corpus_path("cons"))
    assert record["stage"]["origin"] == origin and record["provenance"]["origin"] == origin
    assert (
        record["provenance"]["sha256"]
        == hashlib.sha256(record["stage"]["text"].encode("utf-8")).hexdigest()
    )


def test_the_stage_of_the_record_of_a_stage_file_has_the_graphs_and_definitions_of_its_text(
    cons_from_load_stage, cons
):
    """The stage that `elaborate_stage` makes of the record of a stage file has
    the graphs and, apart from the addresses, the definitions of the stage
    elaborated from the file's text."""
    assert (
        differing_graph_triples(cons_from_load_stage, cons),
        without_addresses(cons_from_load_stage.definitions) == without_addresses(cons.definitions),
    ) == ([], True)


def test_the_provenance_of_the_stage_of_a_stage_file_names_the_file_and_each_empty_source(
    cons_from_load_stage, corpus_path
):
    """The provenance of the stage of a stage file read alone names the file,
    no position in a trellis, and each of the three empty sources by the
    digest of the empty mapping."""
    stage = cons_from_load_stage
    assert (
        stage.provenance["origin"] == str(corpus_path("cons"))
        and "position" not in stage.provenance
    )
    # no addition is described as every empty source is, by the digest of the
    # empty mapping
    assert {
        kind: dict(description) for kind, description in stage.provenance["sources"].items()
    } == {
        "methods": {
            "origin": "in-memory",
            "sha256": hashlib.sha256(b'["mapping",[]]').hexdigest(),
        },
        "settings": {
            "origin": "in-memory",
            "sha256": hashlib.sha256(b'["mapping",[]]').hexdigest(),
        },
        "calibration": {
            "origin": "in-memory",
            "sha256": hashlib.sha256(b'["mapping",[]]').hexdigest(),
        },
    }


def test_the_record_of_a_parameter_is_addressed_by_the_file_name_its_caller_gave_and_the_line(
    cons_from_load_stage, cons, corpus_path
):
    """The record of a parameter is addressed by the name of the file that the
    caller of the elaboration gave and the line of the parameter, here the
    path in the file system and the path in the repository."""
    assert (parameter_address(cons_from_load_stage, "ρ"), parameter_address(cons, "ρ")) == (
        f"{corpus_path('cons')}:6",
        "applications/portfolio-choice/declaration/stages/cons/cons.bl:6",
    )


def test_load_stage_refuses_a_file_that_is_not_a_stage_file_naming_its_path(tmp_path):
    """`load_stage` refuses a file whose name does not end in `.bl` under the
    rule `readable-file`, with the file's path in the refusal."""
    with pytest.raises(FactoryError, match=r"\.bl") as refused:
        load_stage(tmp_path / "stage.yaml")
    assert (
        str(tmp_path / "stage.yaml") in str(refused.value)
        and refused.value.rule == "readable-file"
    )


def test_load_stage_refuses_a_missing_stage_file_naming_the_file_written(tmp_path):
    """`load_stage` refuses a stage file that does not exist under the rule
    `readable-file`, with the name of the file as what was written."""
    with pytest.raises(FactoryError, match="missing.bl") as refused:
        load_stage(tmp_path / "missing.bl")
    assert (refused.value.rule, refused.value.written) == ("readable-file", "missing.bl")


def test_elaborate_stage_refuses_a_stage_text_that_does_not_parse_naming_its_file_and_line(
    tmp_path,
):
    """`elaborate_stage` refuses the record of a stage file that the parser
    cannot read under the rule `syntax`, naming the file and the line."""
    broken = tmp_path / "broken.bl"
    broken.write_text("@stage: broken\n[id=step] { y = }\n", encoding="utf-8")
    with pytest.raises(ValueError) as refused:
        elaborate_stage(load_stage(broken))
    # the refusal carries the file and the line as fields of its own
    assert str(broken) in str(refused.value)
    assert (refused.value.rule, refused.value.file, refused.value.line) == (
        "syntax",
        str(broken),
        2,
    )


def test_elaborate_stage_refuses_a_path_string_and_says_to_write_load_stage_of_the_path():
    """`elaborate_stage` refuses a path string in place of a record under the
    rule `record-shape`, and its refusal says to write
    `elaborate_stage(load_stage(path))`."""
    with pytest.raises(FactoryError) as refused:
        elaborate_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    assert (refused.value.rule, refused.value.write) == (
        "record-shape",
        "elaborate_stage(load_stage(path))",
    )


@pytest.mark.parametrize(
    ("fault", "phrase"),
    [
        pytest.param(
            "a-mapping-without-the-three-sources",
            "the record holds no calibration, methods or settings fields",
            id="a-mapping-without-the-three-sources",
        ),
        pytest.param(
            "a-digest-that-disagrees-with-the-text",
            "the supplied module hash disagrees with the text read",
            id="a-digest-that-disagrees-with-the-text",
        ),
        pytest.param(
            "a-path-string-in-place-of-the-stage-text",
            "path string",
            id="a-path-string-in-place-of-the-stage-text",
        ),
        # a record's methods are the additions that load_stage read, their
        # texts and origins, since a verb of the factory reads no file
        pytest.param(
            "a-path-in-place-of-the-additions",
            "reads no file",
            id="a-path-in-place-of-the-additions",
        ),
    ],
)
def test_elaborate_stage_refuses_a_record_of_the_wrong_shape_naming_its_fault(
    faulty_records, fault, phrase
):
    """`elaborate_stage` refuses a record of the wrong shape under the rule
    `record-shape`, with a message that names the fault."""
    with pytest.raises(FactoryError) as refused:
        elaborate_stage(faulty_records[fault])
    assert refused.value.rule == "record-shape"
    assert phrase in refused.value.message


@pytest.mark.parametrize("name", STAGES_WITH_BINDINGS)
def test_a_stage_from_a_saved_syntax_tree_has_the_graphs_and_definitions_of_the_stage_of_its_text(
    request, decoded_stage, name
):
    """The stage that `make_stage` constructs from the saved syntax tree of a
    corpus stage file has the graphs and, apart from the addresses, the
    definitions of the stage elaborated from the file's text."""
    stage, fixture = decoded_stage(name), request.getfixturevalue(name)
    assert (
        differing_graph_triples(stage, fixture),
        without_addresses(stage.definitions) == without_addresses(fixture.definitions),
    ) == ([], True)


@pytest.mark.parametrize("name", STAGES_WITH_BINDINGS)
def test_a_stage_from_a_saved_syntax_tree_addresses_each_top_level_record_by_its_term_position(
    request, decoded_stage, corpus_path, name
):
    """Each record of a top-level item of a stage made from a saved syntax
    tree, which holds no source positions, is addressed by its position in
    the term, where the stage of the text names the file and the line."""
    stage, fixture = decoded_stage(name), request.getfixturevalue(name)
    top_level = [
        (record.address, fixture.definitions[identity].address)
        for identity, record in stage.definitions.items()
        if record.kind in DEFINITION_KINDS_AT_TOP_LEVEL
    ]
    assert top_level and all(
        decoded.isdigit() and f"/{corpus_path(name).name}:" in written
        for decoded, written in top_level
    )


def test_a_stage_from_a_term_without_source_positions_refuses_naming_the_term_position_alone():
    """The refusal that a stage made from a term without source positions
    gives when it lists its forward builders names the rule and the position
    in the term, and no line or file."""
    without_spans = make_stage(
        from_json(to_json(parse_with_spans(UNADMITTED_FAMILY_AT_ARRIVAL).term)), None
    )
    with pytest.raises(NotConstructed) as refused:
        without_spans.builder.fwd.list()
    assert (refused.value.rule, refused.value.address, refused.value.line, refused.value.file) == (
        "not-constructed",
        "3",
        None,
        None,
    )


def test_two_constructions_open_at_once_keep_separate_tables_of_typings():
    """A construction validates each sort against its own table of typings,
    which refuses a second role of an identity within the construction and
    not the role that another construction, open at the same time in
    another thread, has given that identity."""
    identity = Identity("field", stage="s", perch="arvl", field="a")
    first_has_built, second_has_built, first_has_finished = (threading.Event() for _ in range(3))
    refusals = []

    def first():
        try:
            with construction_typing_table():
                Sort(identity, "field", perch="arvl", role="state")
                first_has_built.set()
                assert second_has_built.wait(timeout=30)
                Sort(identity, "field", perch="arvl", role="state")
        except Exception as error:
            refusals.append(("first", error))
        finally:
            first_has_finished.set()

    def second():
        try:
            assert first_has_built.wait(timeout=30)
            with construction_typing_table():
                Sort(identity, "field", perch="arvl", role="control")
                second_has_built.set()
                assert first_has_finished.wait(timeout=30)
        except Exception as error:
            refusals.append(("second", error))
        finally:
            second_has_built.set()

    threads = [threading.Thread(target=first), threading.Thread(target=second)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert refusals == []

    with construction_typing_table():
        Sort(identity, "field", perch="arvl", role="state")
        with pytest.raises(ValueError, match="one typing"):
            Sort(identity, "field", perch="arvl", role="control")


def test_a_record_holding_the_values_of_a_calibration_file_gives_the_stage_calibrated_by_them(
    cons_calibrated_by_its_record,
):
    """A record whose calibration holds the values of
    `calibration/portfolio.yml` gives the calibrated stage, whose `ρ` is the
    file's 6.0."""
    assert repr(cons_calibrated_by_its_record) == "ElaboratedStage('cons', calibrated)"
    assert cons_calibrated_by_its_record.par.ρ == 6.0


def test_a_stage_calibrated_by_its_record_records_one_binding_of_the_values_held_in_memory(
    cons_calibrated_by_its_record, portfolio_calibration
):
    """The provenance of a stage calibrated by its record records one binding,
    `calibrate`, of a source held in memory whose digest is that of the
    values."""
    assert recorded_bindings(cons_calibrated_by_its_record) == [
        (
            "calibrate",
            {"origin": "in-memory", "sha256": source_description(portfolio_calibration)["sha256"]},
        )
    ]


def test_a_record_with_three_sources_gives_the_stage_that_the_three_binding_verbs_make(
    bound_and_chained,
):
    """The stage of a record with a calibration, settings and an addition
    equals in its graphs, definitions, bindings and tables of parameters,
    settings and methods the stage that `calibrate`, `methodize` and
    `configure` make of the symbolic stage from the same sources."""
    bound, chained = bound_and_chained
    assert repr(bound) == repr(chained) == "ElaboratedStage('cons', specified)"
    assert (
        differing_graph_triples(bound, chained) == [] and bound.definitions == chained.definitions
    )
    assert bound.bindings == chained.bindings
    assert [str(bound.par), str(bound.settings), str(bound.methods)] == [
        str(chained.par),
        str(chained.settings),
        str(chained.methods),
    ]


def test_a_stage_bound_by_its_record_records_no_methodize_and_the_same_additions_as_the_verbs(
    bound_and_chained,
):
    """The provenance of the stage of a record with three sources records
    `configure` and `calibrate` alone, where the stage that the three binding
    verbs make records `methodize` too, and the same additions as that stage,
    since the record's additions are read with the stage text."""
    bound, chained = bound_and_chained
    assert (
        [verb for verb, _ in recorded_bindings(bound)],
        [verb for verb, _ in recorded_bindings(chained)],
    ) == (["configure", "calibrate"], ["configure", "methodize", "calibrate"])
    assert bound.provenance["additions"] == chained.provenance["additions"]


SYMBOLIC_STAGES = [
    pytest.param("cons_with_bind_false", id="a-record-with-bind-false"),
    pytest.param("cons_from_load_stage", id="the-record-of-load-stage"),
    pytest.param("cons_from_elaborate_text", id="elaborate-text"),
]


@pytest.mark.parametrize("symbolic", SYMBOLIC_STAGES)
def test_a_symbolic_stage_leaves_its_parameter_unbound_and_makes_no_binding(request, symbolic):
    """The stage of a record given `bind=False`, the stage of the record that
    `load_stage` returns and the stage of `elaborate_text` are symbolic: the
    stage's one parameter is unbound and no binding is made."""
    stage = request.getfixturevalue(symbolic)
    assert repr(stage) == "ElaboratedStage('cons', symbolic)"
    assert str(stage.par["ρ"]) == "ρ : [1, inf), unbound"
    assert (stage.bindings.calibration, stage.bindings.blocks, stage.bindings.settings) == (
        None,
        None,
        None,
    )


@pytest.mark.parametrize("symbolic", SYMBOLIC_STAGES)
def test_the_provenance_of_a_symbolic_stage_records_its_elaboration_alone(request, symbolic):
    """The provenance of a symbolic stage holds the origin, the digest, the
    sources, the text and the versions of its elaboration, and no addition
    read."""
    stage = request.getfixturevalue(symbolic)
    assert "additions" not in stage.provenance
    assert sorted(stage.provenance) == ["origin", "sha256", "sources", "text", "versions"]


def test_a_stage_elaborated_with_bind_false_describes_each_source_of_its_record_by_its_digest(
    cons_with_bind_false, record_with_three_sources
):
    """The provenance of the stage of a record given `bind=False` describes
    each of the record's three sources by its digest, the additions by the
    path of the addition and the other two as held in memory."""
    record = record_with_three_sources
    described = {
        kind: dict(held) for kind, held in cons_with_bind_false.provenance["sources"].items()
    }
    assert described == {
        "methods": {
            "path": str(CONS_METHODS),
            "sha256": source_description(methods_source(record["methods"]))["sha256"],
        },
        "settings": {
            "origin": "in-memory",
            "sha256": source_description(record["settings"])["sha256"],
        },
        "calibration": {
            "origin": "in-memory",
            "sha256": source_description(record["calibration"])["sha256"],
        },
    }


def test_elaborate_text_gives_the_stage_that_elaborate_stage_makes_of_a_record_of_the_text(cons):
    """`elaborate_text` gives the stage that `elaborate_stage` makes of a
    record of the same text and origin with empty sources, the corpus stage
    that the fixture builds."""
    assert elaborate_text(corpus_text("cons"), CORPUS["cons"]) == cons


def test_elaborate_stage_copies_a_stage_once_where_its_record_binds_three_sources(
    copies, record_with_three_sources
):
    """`elaborate_stage` copies the stage once where its record binds a
    calibration, settings and an addition."""
    elaborate_stage(record_with_three_sources)
    assert copies == ["ElaboratedStage"]


def test_elaborate_trellis_given_an_earlier_trellis_copies_each_of_its_occurrences_once(copies):
    """`elaborate_trellis` of `trellis.reference-port-cons-vfi.yml`, given the
    specified trellis of `trellis.reference-port-cons.yml`, copies each of
    the 18 stage occurrences once, the six consumption stages that it
    constructs anew with the replacing method among them."""
    syntactic = load_trellis(CONS_PORT / "trellis.reference-port-cons.yml")
    specified = configure_trellis(
        methodize_trellis(calibrate_trellis(elaborate_trellis(syntactic), syntactic), syntactic),
        syntactic,
    )
    changed = load_trellis(CONS_PORT / "trellis.reference-port-cons-vfi.yml")
    copies.clear()
    remade = elaborate_trellis(changed, specified)
    # six periods of three stages each
    assert len(copies) == len(positions(remade)) == 18
    assert [key for _, key in changed_positions(specified, remade)] == ["cons"] * 6


def test_assemble_trellis_copies_each_stage_occurrence_of_the_two_stage_durables_recipe_once(
    copies,
):
    """`assemble_trellis` copies each of the 103 stage occurrences of the
    durables application's two-stage recipe once."""
    # no recipe assembles the trellis of the cons-port application, so the
    # test assembles the durables application's
    assembled = assemble_trellis(DURABLES, DURABLES_RECIPE_WITHOUT_TENURE)
    # fifty periods of the two consumption stages and the terminal period of
    # three stages: 50 * 2 + 3
    assert len(copies) == len(positions(assembled)) == 103


@pytest.mark.parametrize(
    ("name", "kind", "source", "verb", "words"),
    [
        pytest.param(
            "ez_savings",
            "calibration",
            EZ_SAVINGS_WITHOUT_BETA,
            "calibrate",
            "supplies no value for it",
            id="a-calibration-without-beta",
        ),
        # ρ is declared on [1, inf)
        pytest.param(
            "cons",
            "calibration",
            {"ρ": 0.5},
            "calibrate",
            "lies outside the declared set",
            id="a-value-outside-its-declared-set",
        ),
        pytest.param(
            "cons",
            "methods",
            UNKNOWN_METHOD,
            "methodize",
            "names the method `!no_such_method`, which no row of the catalogue holds",
            id="an-unknown-method",
        ),
    ],
)
def test_elaborate_stage_refuses_a_faulty_source_with_the_refusal_that_its_binding_verb_gives(
    name, kind, source, verb, words
):
    """`elaborate_stage` refuses a record with a faulty source with the type
    and the text of the refusal that the source's binding verb gives on the
    symbolic stage."""
    record = {
        "stage": {"text": corpus_text(name), "origin": CORPUS[name]},
        "calibration": {},
        "settings": {},
        "methods": [],
        kind: [source] if kind == "methods" else source,
    }
    # the refusal of a calibration or of settings is a ValueError, and that
    # of a method at its target a TargetError, a LookupError
    with pytest.raises((ValueError, LookupError)) as bound:
        elaborate_stage(record)
    with pytest.raises((ValueError, LookupError)) as chained:
        getattr(elaborate_stage(record, bind=False), verb)(source)
    assert (type(bound.value), str(bound.value)) == (type(chained.value), str(chained.value))
    assert words in str(bound.value), (verb, str(bound.value))


@pytest.mark.parametrize(
    "written",
    [
        pytest.param("yes", id="a-string"),
        pytest.param(1, id="the-integer-one-which-equals-true"),
        pytest.param(None, id="none"),
    ],
)
def test_elaborate_stage_refuses_a_bind_that_is_not_true_or_false_before_it_reads_the_record(
    written,
):
    """`elaborate_stage` refuses a `bind` that is not `True` or `False` with a
    sentence that says what to write, before it reads the record, here a path
    string that it refuses otherwise."""
    with pytest.raises(TypeError) as refused:
        elaborate_stage(
            "applications/portfolio-choice/declaration/stages/cons/cons.bl", bind=written
        )
    assert str(refused.value) == (
        f"elaborate_stage: bind is {written!r}, which is not True or False; bind says "
        "whether the sources the record supplies are bound; write bind=False for the "
        "symbolic stage, or leave bind out to bind them"
    )
