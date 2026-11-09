"""The fixtures of Bellman Workbench's tests, imported from
`workbench_support.py`, which defines them with the helpers and the
constants the test files read. The helpers stand in that module and not in
this one, because the root test run collects this folder together with
`packages/bellman/tests`, which has a `conftest.py` of its own, and the name
`conftest` then resolves to one of the two: a test file imports from
`workbench_support`, whose name is unique."""

from workbench_support import (  # noqa: F401  (the fixtures, found here by pytest)
    app_state,
    browser,
    buffer_stock_folder,
    cache_folder,
    cagetti_folder,
    chromium_executable,
    cons,
    cons_file,
    cons_text,
    consport_folder,
    demonstration_folder,
    durables_folder,
    entrepreneur_death,
    git_identity,
    lifecycle_folder,
    matsya_durables,
    matsya_state,
    matsya_stub,
    model_folder,
    no_stage_library,
    node,
    original,
    own_cache_folder,
    page,
    pension_folder,
    refused_pension,
    repository,
    retirement_folder,
    scratch_consport,
    scratch_durables,
    scratch_folder,
    scratch_lifecycle,
    scratch_pension,
    server,
    server_on,
    specify_calls,
)
