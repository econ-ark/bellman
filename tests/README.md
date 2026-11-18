# Tests

The workflow `.github/workflows/tests.yml` runs the tests on GitHub, on Ubuntu with Python 3.12. To run them on your machine, first install what the workflow installs, in the activated environment and from the root of the repository:

```bash
python -m pip install -e "packages/bellman[dev,docs,explore]"
python -m pip install -e packages/asva
```

These lines do not install JAX. The tests that need JAX are skipped, and pytest gives the reason. Then run the commands of the workflow from the root of the repository:

```bash
python -m pytest packages/bellman/tests -n logical -rfEsxX              # the default set
python -m pytest packages/bellman/tests -n logical --complete -rfEsxX   # the complete set
python -m pytest tests/test_documentation_structure.py tests/test_method_types_page.py \
  tests/test_package_documentation.py tests/test_documented_applications_and_lessons.py \
  tests/test_documentation_content.py tests/test_application_layout.py -n logical -rfEsxX   # the checks of the documentation
```

The default set leaves out each case marked `complete_set`: all rows but one of some tests that run over a table, such as the list of the stage files of the applications, and a few tests that run only in the complete set, such as the elaboration of whole registries. The complete set runs every case. The checks of the documentation take `--complete` too, which adds the strict build of the site among other checks. `-n logical` starts one process for each logical processor, and `-rfEsxX` lists each failure, skip and expected failure with its reason. The workflow runs the complete set on a pull request and on a push to `main`, and the default set on a push to any other branch.

The workflow does not run the tests of `packages/asva`, of the applications and of the tutorials. `python -m pytest packages/asva/tests applications tutorials -n logical` runs them in the environment that `install-dev.sh` makes: the tests of the tutorials read notebooks with packages that the install lines above do not provide. The root folder `tests/` holds further tests, which the workflow does not run either.
