"""The public namespaces and their import rules, the names a stage lists,
the version of the package, use without installation, and pickling."""

import pickle
import subprocess
import sys
from importlib import import_module, metadata

import pytest
from application_files import CORPUS, ROOT
from stage_builders import stage_from_text
from stage_texts import corpus_text

import bellman.period
import bellman.stage
import bellman.trellis
from bellman.factory import file_entries
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.elaborated import BINDING_VERBS, QUERY_METHODS, STAGE_VERBS
from bellman.trellis import assemble_trellis

# the namespaces of the package that hold a table of exports
NAMESPACES = ("bellman.stage", "bellman.period", "bellman.trellis")


@pytest.fixture(scope="module")
def pieces_of_cons(cons):
    """The consumption stage and four pieces of it, by the words that name
    each in a test id."""
    return {
        "the-stage": cons,
        "the-backward-builders-graph": cons.builder.bwd,
        "the-builder-from-continuation-to-decision": cons.builder.bwd["cntn_to_dcsn"],
        "the-pullback-of-that-builder": cons.builder.bwd["cntn_to_dcsn", "Pullback"],
        "the-backward-initial-diagram": cons.initial.backward,
    }


@pytest.fixture
def no_distribution_metadata(monkeypatch):
    """The metadata of the installed distributions made to answer that the
    package is not installed, as for a checkout imported by its path."""

    def none_installed(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", none_installed)


@pytest.fixture(scope="module")
def fresh_version():
    """A version of the consumption stage that has answered no query."""
    return stage_from_text(corpus_text("cons"), "pickled.bl")


@pytest.fixture(scope="module")
def queried_version():
    """A version of the consumption stage that has listed the primitives of
    its backward builders and answered its obligations."""
    version = stage_from_text(corpus_text("cons"), "pickled.bl")
    version.builder.bwd.primitives.list()
    version.obligations()
    return version


@pytest.fixture(scope="module")
def queried_trellis(two_nodes_registry):
    """The trellis of the small registry's recipe `spec.yml`, one of whose
    stages has answered its obligations."""
    trellis = assemble_trellis(two_nodes_registry, "spec.yml")
    trellis["periods"][1]["stages"]["two_nodes"].obligations()
    return trellis


def test_dir_of_a_stage_lists_its_attributes_perch_handles_queries_and_verbs_as_public_names(
    cons,
):
    """The names that `dir` lists of a stage and that do not begin with an
    underscore are its six public attributes, `builder`, the three perch
    handles, its queries, its own verbs and tables and its binding verbs."""
    # `builder` and the three perch handles `arvl`, `dcsn` and `cntn` are
    # properties, as `par` and `settings` are, and not among the seven
    # attributes; the seventh, the stored record `_builders`, is private
    assert [entry for entry in dir(cons) if not entry.startswith("_")] == sorted(
        {
            "name",
            "metadata",
            "definitions",
            "initial",
            "bindings",
            "provenance",
            "builder",
            "arvl",
            "dcsn",
            "cntn",
        }
        | set(QUERY_METHODS)
        | set(BINDING_VERBS)
        | set(STAGE_VERBS)
    )


def test_dir_of_a_stage_does_not_list_the_stored_record_of_its_builders(cons):
    """`dir` of a stage does not list `_builders`, the private stored record
    of its two builders graphs, which a reader reaches through `builder`."""
    assert "_builders" not in dir(cons)


def test_a_stage_has_no_attribute_of_a_function_that_takes_a_box_or_of_an_older_name(cons):
    """A stage has no attribute named after a function of the package that
    takes a box or a graph as its argument, such as `kernel` or
    `to_drawing`, or after an older name of its builders, its graphs or
    their signatures, such as `build`."""
    # `build` is the name that `builder` replaced, with no alias
    assert not any(
        hasattr(cons, name)
        for name in (
            "build",
            "kernel",
            "compile_kernel",
            "builders_graph",
            "initial_diagram",
            "to_drawing",
            "graph_inputs_and_outputs",
            "builder_signature",
            "box_signature",
        )
    )


@pytest.mark.parametrize(
    "piece",
    [
        "the-stage",
        "the-backward-builders-graph",
        "the-builder-from-continuation-to-decision",
        "the-pullback-of-that-builder",
        "the-backward-initial-diagram",
    ],
)
def test_no_piece_of_a_stage_has_an_attribute_of_a_name_that_the_package_removed(
    pieces_of_cons, piece
):
    """Neither a stage nor a graph, a builder, a primitive or an initial
    diagram of it has an attribute of a name that the package removed."""
    # ten names of former queries, and three former verbs that other verbs
    # replaced
    removed = (
        "transition_map",
        "aggregator",
        "policy_relation",
        "selection",
        "expectations",
        "methods_of",
        "definitions_of",
        "symbols",
        "kind",
        "branches",
        "origins",
        "affine",
        "directions",
    )
    assert not any(hasattr(pieces_of_cons[piece], name) for name in removed)


def test_dir_of_a_stage_lists_the_protocol_names_of_python_that_a_stage_defines(cons):
    """`dir` of a stage lists the names of Python's own protocols that a
    stage defines, `__eq__`, `__hash__`, `__repr__` and `__str__`."""
    assert {"__eq__", "__hash__", "__repr__", "__str__"} <= set(dir(cons))


def test_the_encoding_and_the_provenance_state_one_package_version_where_none_is_installed(
    no_distribution_metadata,
):
    """Where the package is not installed, as in a fresh clone, the encoding
    of a stage and its provenance state the same version of the package,
    and not the word `unreleased`."""
    # the provenance once read the metadata of the installed distribution and
    # the encoding the pyproject.toml above the package, so that one document
    # of a checkout that is not installed stated two versions
    stage = stage_from_text(corpus_text("cons"), "cons.bl")
    document = stage.encoding()
    assert (
        document["package_version"]
        == document["provenance"]["versions"]["package"]
        != "unreleased"
    )


def test_a_stage_file_elaborates_where_the_package_is_not_installed(no_distribution_metadata):
    """A checkout imported by its path, with no metadata of an installed
    distribution, elaborates the stage file of the consumption stage."""
    record = load_stage(ROOT / CORPUS["cons"])
    assert repr(elaborate_stage(record)) == "ElaboratedStage('cons', symbolic)"


@pytest.mark.parametrize(
    "written",
    [
        pytest.param("fresh_version", id="a-stage-version"),
        pytest.param("queried_version", id="a-stage-version-after-two-queries"),
        pytest.param("two_nodes_trellis", id="a-trellis"),
        pytest.param("queried_trellis", id="a-trellis-after-a-query-of-one-stage"),
    ],
)
def test_the_standard_pickle_reads_back_a_stage_version_or_a_trellis_equal_to_the_one_written(
    request, written
):
    """`pickle.dumps` and `pickle.loads` of the standard library write and read
    back a stage version, or a trellis, equal to the one written, before and
    after it has answered queries."""
    # a trellis is a dictionary, so that its equality is the equality of the
    # stages at each of its positions
    value = request.getfixturevalue(written)
    assert pickle.loads(pickle.dumps(value)) == value


def test_a_stage_version_read_back_by_pickle_holds_none_of_the_answers_the_written_one_kept(
    queried_version,
):
    """A stage version read back by the standard pickle holds none of the
    answers that the version written had kept."""
    back = pickle.loads(pickle.dumps(queried_version))
    assert vars(queried_version)["_kept"]
    assert "_kept" not in vars(back)


def test_a_stage_version_read_back_by_pickle_answers_a_query_with_the_answer_of_the_written_one():
    """A stage version read back by the standard pickle answers a query with
    the answer that the version written gave."""
    version = stage_from_text(corpus_text("cons"), "pickled.bl")
    listing = str(version.builder.bwd.primitives.list())
    version.obligations()
    back = pickle.loads(pickle.dumps(version))
    assert str(back.builder.bwd.primitives.list()) == listing


def test_the_functions_that_load_elaborate_join_draw_and_explore_are_objects_of_their_modules():
    """A name imported from the namespace of the object it concerns is the
    object of the module that defines it, here the functions that load,
    elaborate, join, draw and explore."""
    from bellman.factory import (
        elaboration,
        joins,
        loading,
        model_explorer,
        trellis,
        trellis_drawings,
    )
    from bellman.period import diagram_period, period_joins
    from bellman.stage import elaborate_stage, elaborate_text, load_stage
    from bellman.trellis import elaborate_trellis, explore, load_trellis

    assert (load_stage, elaborate_stage, elaborate_text) == (
        loading.load_stage,
        elaboration.elaborate_stage,
        elaboration.elaborate_text,
    )
    assert (period_joins, diagram_period) == (joins.period_joins, trellis_drawings.diagram_period)
    assert (load_trellis, elaborate_trellis, explore) == (
        loading.load_trellis,
        trellis.elaborate_trellis,
        model_explorer.explore,
    )


@pytest.mark.parametrize("name", ["explore", "write_model_explorer"])
def test_a_name_of_the_model_explorer_is_one_object_in_the_stage_and_the_trellis_namespaces(
    name,
):
    """A function of the model explorer that both the stage and the trellis
    namespaces export is one object in the two."""
    assert getattr(bellman.stage, name) is getattr(bellman.trellis, name)


@pytest.mark.parametrize("namespace", NAMESPACES)
def test_the_all_of_a_namespace_lists_the_names_of_its_table_of_exports(namespace):
    """The `__all__` of a namespace lists the names of its table from each
    public name to the module that defines it, in the order of the table."""
    module = import_module(namespace)
    assert list(module.__all__) == list(module._EXPORTS)


@pytest.mark.parametrize("namespace", NAMESPACES)
def test_each_name_a_namespace_exports_is_the_object_of_the_module_that_its_table_names(
    namespace,
):
    """Each name that a namespace exports is the object of that name in the
    module that the namespace's table names for it."""
    module = import_module(namespace)
    for name in module.__all__:
        assert getattr(import_module(module._EXPORTS[name]), name) is getattr(module, name), name


@pytest.mark.parametrize("namespace", NAMESPACES)
def test_a_namespace_refuses_a_name_that_it_does_not_export(namespace):
    """A namespace refuses with an `AttributeError` a name that its table does
    not hold."""
    module = import_module(namespace)
    with pytest.raises(AttributeError):
        module.no_such_name


def test_an_import_of_a_name_that_the_stage_namespace_does_not_export_is_refused():
    """`from bellman.stage import` of a name that the namespace does not
    export raises an `ImportError`."""
    with pytest.raises(ImportError):
        from bellman.stage import no_such_name  # noqa: F401


def test_a_submodule_of_the_stage_namespace_is_imported_as_itself_in_a_new_interpreter():
    """`from bellman.stage import grains` gives the submodule
    `bellman.stage.grains`, the module that the import system holds under
    that name, in a new interpreter, which the test starts since in its own
    process the submodule is already an attribute of `bellman.stage`; the
    test fails where that interpreter exits with an error."""
    import bellman.stage.grains  # noqa: F401  a submodule is still imported as one

    # in the new interpreter the namespace's own lookup of a name would answer
    # `grains` if the import system did not set the submodule as an attribute
    # of `bellman.stage` first; the interpreter starts in the folder of the
    # package, which stands first on its import path, so that it imports the
    # package of this checkout, whatever folder pytest runs from
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from bellman.stage import grains; import bellman.stage; import sys; "
            "assert bellman.stage.grains is grains; "
            "assert grains is sys.modules['bellman.stage.grains']",
        ],
        cwd=ROOT / "packages" / "bellman",
        check=True,
    )


def test_the_stage_namespace_exports_the_name_of_each_perch_as_its_text():
    """The stage namespace exports `arvl`, `dcsn` and `cntn`, each the text of
    the name of its perch."""
    assert (bellman.stage.arvl, bellman.stage.dcsn, bellman.stage.cntn) == (
        "arvl",
        "dcsn",
        "cntn",
    )


def test_the_stage_namespace_exports_no_name_of_a_recipe_or_a_period():
    """The stage namespace exports none of `load_recipe` and `accrete`, which
    the trellis namespace exports, and `period_joins`, which the period
    namespace exports."""
    assert {"load_recipe", "accrete"} <= set(bellman.trellis.__all__)
    assert "period_joins" in bellman.period.__all__
    assert not {"load_recipe", "accrete", "period_joins"} & set(bellman.stage.__all__)


def test_the_root_module_of_the_package_exports_no_name():
    """The module `bellman` exports no name and holds no table of exports, so
    that it refuses `load_stage` both to an import and to an attribute."""
    assert bellman.__all__ == [] and not hasattr(bellman, "_EXPORTS")
    assert not hasattr(bellman, "MethodOption")
    with pytest.raises(ImportError):
        from bellman import load_stage  # noqa: F401
    with pytest.raises(AttributeError):
        bellman.load_stage


@pytest.mark.parametrize(
    "name",
    [
        "connector_entry",
        "ConnectorEntry",
        "period_entries",
        "insert_in_sequence",
        "split_entry",
        "remove_from_sequence",
        "remove_from_mapping",
    ],
)
def test_the_trellis_namespace_exports_seven_names_of_the_entries_of_a_trellis_file(
    name,
):
    """The trellis namespace exports the two queries of the entries of a
    trellis file, the record of a connector's entry, the two writers of
    entries and the two removals of an entry, each the object of
    `bellman.factory.file_entries`."""
    assert getattr(bellman.trellis, name) is getattr(file_entries, name)
    assert name in bellman.trellis.__all__
