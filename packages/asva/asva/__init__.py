"""Asva is the numerical toolkit that stands beside the package ``bellman``.

It holds code that a methods file names as the handler of a method, the
endogenous grid factories of ``asva.egm_1d`` with ``asva.egm``, the step built
from the records of a stage's kernels, the compose-and-reapproximate operator
of ``asva.compose_interp`` and the utilities of ``asva.numerics``, and in
``asva.run`` a runner for parameter sweeps, moments, estimation and MPI. It
holds no structure of a model: it imports nothing of ``bellman`` and works on
the functions, arrays and plain records its caller passes it.
"""

from asva.egm_1d import egm

__all__ = ["egm"]
