"""The skip of a test that needs a package outside the list `dev` of the
package's requirements: it skips where the package is absent, and raises the
error of an installed package that cannot import a module of its own or a
package on which it depends."""

import pytest
from skips import require_package

# the text of `__init__.py` of a package made for the test, by the row's id:
# the package imports a module of its own that is missing, or a dependency
# that is missing
FAULTY_PACKAGES = {
    "a module missing inside the package": (
        "from package_of_the_test.missing_module import solve\n",
        "package_of_the_test.missing_module",
    ),
    "a dependency of the package missing": (
        "import dependency_of_the_test\n",
        "dependency_of_the_test",
    ),
}


def test_an_absent_package_skips_the_test_with_the_extra_that_installs_it(tmp_path, monkeypatch):
    """`require_package` skips the test where the named package is absent, with
    a reason that names the extra that installs it."""
    monkeypatch.syspath_prepend(str(tmp_path))
    assert not (tmp_path / "package_of_the_test").exists()
    with pytest.raises(pytest.skip.Exception) as skipped:
        require_package("package_of_the_test.submodule", extra="docs")
    assert skipped.value.msg == (
        'the package package_of_the_test is not installed; install the extra "docs"'
    )


@pytest.mark.parametrize("init, missing", FAULTY_PACKAGES.values(), ids=FAULTY_PACKAGES)
def test_a_module_that_an_installed_package_cannot_import_raises_its_error(
    tmp_path, monkeypatch, init, missing
):
    """`require_package` raises the `ModuleNotFoundError` of the module that an
    installed package fails to import, in place of a skip."""
    package = tmp_path / "package_of_the_test"
    package.mkdir()
    (package / "__init__.py").write_text(init, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    # a skip is caught too, so that a skip of the test in place of the error
    # fails the test instead of skipping it
    with pytest.raises((ModuleNotFoundError, pytest.skip.Exception)) as raised:
        require_package("package_of_the_test", extra="docs")
    assert raised.type is ModuleNotFoundError, raised.value
    assert raised.value.name == missing
