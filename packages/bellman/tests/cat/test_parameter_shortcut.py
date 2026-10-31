"""The acceptance file of unit S of the internal developer release 0.01, the
parameter shortcut AAS decided on 29 September 2026 (the second layer of the
tests, `packages/bellman/README.md` §8): `stage.par.ρ` answers the value of
the parameter ρ alone and `stage.settings.n_a` the value of the setting `n_a`
alone, while `stage.par["ρ"]` and `stage.settings["n_a"]` keep answering the
whole record. One test for each case of the unit, whose decisions PS1 to PS4
stand in the release's record of decisions, on the corpus stage `cons` and
its bound versions, which `conftest.py` provides, and, for three parameter
names the corpus does not hold, on the text of `cons` with three
declarations added.
"""

from __future__ import annotations

import copy

import pytest

from bellman.native.hypergraphs import copy_native

# the table's own attributes and one of Python's protocol names, which
# `dir(stage.par)` lists beside the parameters
OWN = {"version", "list", "view", "keys", "items", "values", "get", "__getitem__"}


@pytest.fixture(scope="module")
def cons_named(text_of, elaborate_text):
    """The symbolic stage of the text of `cons` with three more parameters:
    `list`, the name of a verb of the table; `lambda`, a keyword of Python;
    and `ℓ`, which Python reads as `l` when it reads the source."""
    text = text_of("cons")
    assert text.count("ρ : [1, inf)\n") == 1
    return elaborate_text(
        text.replace("ρ : [1, inf)\n", "ρ : [1, inf)\nlist : ℝ₊₊\nlambda : ℝ₊₊\nℓ : ℝ₊₊\n"),
        "cons_named.bl",
    )


def test_item_1_a_calibrated_parameter_answers_the_value_its_record_holds(
    cons_calibrated, cons_configured
):
    """`stage.par.ρ` answers the number `stage.par["ρ"].value` holds, 6.0 on
    the calibration of `cons`, on the calibrated and on the specified version;
    the record is unchanged, and reading the value stores nothing on the table
    or on the stage."""
    table = cons_calibrated.par
    held = set(vars(cons_calibrated))
    assert table.ρ == table["ρ"].value == 6.0
    assert isinstance(table.ρ, float)
    assert cons_configured.par.ρ == 6.0
    assert str(table["ρ"]) == "ρ = 6.0 : [1, inf)"
    assert vars(table) == {"version": cons_calibrated}
    assert set(vars(cons_calibrated)) == held


def test_item_2_a_parameter_no_calibration_binds_is_refused_naming_the_record_and_the_verb(
    cons, cons_methods_only
):
    """On a version no calibration has bound, the symbolic `cons` and `cons`
    methodized alone, `stage.par.ρ` does not answer the word `unbound` as if
    it were a value: it raises an `AttributeError` whose message names the
    record's key and the verb that binds the value (PS1), and the record still
    answers by the key."""
    for version in (cons, cons_methods_only):
        with pytest.raises(AttributeError) as refused:
            version.par.ρ
        assert str(refused.value) == (
            "stage 'cons': the parameter 'ρ' has no value on this version, which no calibration "
            'has bound; stage.par["ρ"] answers its record, and calibrate(stage, source) binds '
            "its value"
        )
        assert not hasattr(version.par, "ρ")
        assert str(version.par["ρ"]) == "ρ : [1, inf), unbound"


def test_item_3_a_name_that_is_no_parameter_raises_attribute_error(cons_calibrated):
    """A name that is no parameter raises an `AttributeError` with the reason
    the key gives, so that `hasattr` and `getattr` with a default read it as
    absent; the names Python's own protocols ask a table for are no
    parameters, so a copy of the table answers as the table does."""
    with pytest.raises(AttributeError) as refused:
        cons_calibrated.par.rho
    assert str(refused.value) == (
        "stage 'cons': 'rho' is no parameter of the stage; a parameter is read by the name the "
        "file declares, and the parameters are ρ"
    )
    assert not hasattr(cons_calibrated.par, "rho")
    assert getattr(cons_calibrated.par, "rho", None) is None
    assert copy.copy(cons_calibrated.par).ρ == 6.0


def test_item_4_a_parameter_named_as_a_verb_of_the_table_is_read_by_the_key_alone(cons_named):
    """The language admits a parameter named `list`. On the table `list` stays
    the verb, which answers the table the mapping prints, and the parameter
    is read by its key (PS3); the docstring of the shortcut names each of the
    table's own attributes, the names under which a parameter is read by its
    key alone."""
    calibrated = cons_named.calibrate({"ρ": 6.0, "list": 2.0, "lambda": 3.0, "ℓ": 4.0})
    assert str(calibrated.par.list()) == str(calibrated.par)
    assert calibrated.par["list"].value == 2.0
    assert str(calibrated.par["list"]) == "list = 2.0 : ℝ₊₊"
    own = {name for name in dir(type(calibrated.par)) if not name.startswith("_")} | {"version"}
    written = type(calibrated.par).__getattr__.__doc__
    assert all(f"`{name}`" in written for name in own), own


def test_item_5_completion_lists_the_parameter_names_beside_the_tables_own(
    cons, cons_calibrated, cons_named
):
    """`dir(stage.par)`, which completion in Jupyter reads, lists every
    parameter whose name can be written after a dot beside the table's own
    attributes and Python's protocol names (PS2), on the symbolic and on the
    calibrated version; `lambda`, a keyword of Python, and `ℓ`, which Python
    reads as `l`, are left out, and each is still read by the key or by
    `getattr` with its name as a string."""
    for version in (cons, cons_calibrated):
        listed = dir(version.par)
        assert "ρ" in listed and set(object.__dir__(version.par)) <= set(listed)
    calibrated = cons_named.calibrate({"ρ": 6.0, "list": 2.0, "lambda": 3.0, "ℓ": 4.0})
    listed = set(dir(calibrated.par))
    assert OWN | {"ρ"} <= listed
    assert "lambda" not in listed and "ℓ" not in listed
    assert getattr(calibrated.par, "lambda") == calibrated.par["lambda"].value == 3.0
    assert getattr(calibrated.par, "ℓ") == 4.0


def test_item_6_a_setting_answers_its_value_alone(cons, cons_methodized, cons_configured):
    """`stage.settings.n_a` answers the configured value that
    `stage.settings["n_a"]` holds, 800 on the settings of `cons`, and
    completion lists it (PS4); a version that binds no settings refuses the
    name with the key's reason, an `AttributeError`; a setting whose name is
    no Python identifier is read by `getattr` or by the key and is not
    listed."""
    assert cons_configured.settings.n_a == cons_configured.settings["n_a"].value == 800
    assert str(cons_configured.settings["n_a"]) == "n_a = 800"
    assert "n_a" in dir(cons_configured.settings)
    with pytest.raises(AttributeError) as refused:
        cons.settings.n_a
    assert str(refused.value) == (
        "stage 'cons': 'n_a' is no setting of this version, which binds no settings; "
        "configure(stage, source) binds them"
    )
    configured = {name: record.value for name, record in cons_configured.settings.items()}
    widened = copy_native(cons_methodized).configure({**configured, "n-points": 5})
    assert getattr(widened.settings, "n-points") == widened.settings["n-points"].value == 5
    assert "n-points" not in dir(widened.settings)
