"""The public names of a period, `bellman.period`: the joins of a period and
the orders they determine, `period_joins`, `forward_order`, `backward_order`
and `computable_together`, and `diagram_period`, which draws one period of a
trellis. `_EXPORTS` maps each name to the module that defines it, which is
imported when the name is first used; the modules stand in `bellman.factory`,
and this package holds the table and nothing else (`packages/bellman/README.md`
§1 and §6).
"""

from importlib import import_module

_EXPORTS = {
    "period_joins": "bellman.factory.joins",
    "forward_order": "bellman.factory.joins",
    "backward_order": "bellman.factory.joins",
    "computable_together": "bellman.factory.joins",
    "diagram_period": "bellman.factory.trellis_drawings",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    """The public name `name`, read from the module that defines it, which is
    imported on this first use; every other name is refused with an
    AttributeError, so that a submodule is still imported as one."""
    try:
        module_name = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    return getattr(import_module(module_name), name)


def __dir__():
    return sorted(set(globals()) | set(__all__))
