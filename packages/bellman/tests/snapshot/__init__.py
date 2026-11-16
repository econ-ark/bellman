"""The stored recordings of the applications' stage files, the script
record.py, which writes them, and the script validate_encodings.py, which
records the digests of the encodings.

The tests of the recordings, in `tests/test_applications.py`, parse and
elaborate every stage file under `applications/` and compare the results with
these recordings."""

import sys
from pathlib import Path

# the folder `packages/bellman` of the checkout that holds this file
PACKAGE = Path(__file__).resolve().parents[2]


def put_this_checkout_first():
    """Put the folder `packages/bellman` of this checkout first on
    `sys.path`. Each script of this folder calls it, when run as a script,
    before it imports `bellman` or a support module of the tests, so that it
    reads the package of its own checkout and not a copy that the
    environment has installed."""
    sys.path.insert(0, str(PACKAGE))
