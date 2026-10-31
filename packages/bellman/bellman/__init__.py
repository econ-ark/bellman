"""Bellman-SYM in one distribution: `bellman.syntax` reads a stage file into
a term, and the folders above it construct, bind and print the stage's
semgraph, its semantic graph.

The package exports no name of its own. A public name is imported from the
namespace of the object it concerns: `bellman.stage` for a stage, `from
bellman.stage import load_stage, elaborate_stage`; `bellman.period` for a
period; and `bellman.trellis` for a trellis and the factory route that
assembles one. The four refusal classes stand in `bellman.refusals`. Each
namespace holds one table from each public name to the module that defines
it and imports the module when the name is first used, so that importing the
parser imports no DisCoPy. `packages/bellman/README.md` §1 lists the three
tables and §3 maps the folders beneath.
"""

__all__ = []
