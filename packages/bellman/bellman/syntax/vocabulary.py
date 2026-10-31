"""The words of the language that every folder reads, each written once.

A stage file names three perches, gives each field a role, marks a line as a
node or as documentation, writes a perch mark after a name, and declares a
set by one of the spellings of a primitive set. The package reads those words
in every folder: the declaration pass classifies a field by its role, the
fold reads the roles of the values a backward builder writes, the graphs
order the perches, the printers write the perch marks, and the set algebra,
the printer of a term and the calibration read the primitive sets. This
module holds the words, so that no folder spells one again.
"""

from __future__ import annotations

import dataclasses
import math

from bellman.syntax import terms

# --- the perches ---

# The three perches of a stage in their forward order, by the tokens a wire
# type carries; `shck` is the token of a shock, which is at no perch.
ARRIVAL, DECISION, CONTINUATION = "arvl", "dcsn", "cntn"
PERCHES = (ARRIVAL, DECISION, CONTINUATION)
SHCK = "shck"
# The perch word of arrival as a string, `bellman.stage.arvl == "arvl"`,
# exported so that a key of `stage.builder` is written without quotation marks.
arvl = ARRIVAL
# The perch word of decision as a string, `bellman.stage.dcsn == "dcsn"`,
# exported so that a key of `stage.builder` is written without quotation marks.
dcsn = DECISION
# The perch word of continuation as a string, `bellman.stage.cntn == "cntn"`,
# exported so that a key of `stage.builder` is written without quotation marks.
cntn = CONTINUATION
# The four builders of a standard stage, as (input perch, output perch): the
# two forward builders over states and the two backward builders over values,
# two chains of builders. A file that writes all four describes a whole stage,
# and the construction then checks that a block writes each of its fields or
# the stage receives it.
STAGE_BUILDERS = (
    (ARRIVAL, DECISION),
    (DECISION, CONTINUATION),
    (CONTINUATION, DECISION),
    (DECISION, ARRIVAL),
)
# the perch a side of a header names, by the term the lowering makes of
# its word
PERCH_OF_SIDE = {
    terms.Arrival: ARRIVAL,
    terms.Decision: DECISION,
    terms.Continuation: CONTINUATION,
}
# the word of each perch as a sheet writes it
PERCH_WORD = {ARRIVAL: "arrival", DECISION: "decision", CONTINUATION: "continuation"}

# --- the perch marks ---

# The sign of each perch, printed on a sheet before the fields of the perch
# and on the arrow of the edge that draws a shock.
PERCH_SIGN = {ARRIVAL: "≺", DECISION: "∼", CONTINUATION: "≻"}
# The mark a name carries for each perch, printed directly after its letters:
# `V≻`, `μ≺`, `c`. The mark as the file writes it, `V[>]`, `V[<]`, `c`, is
# `WRITTEN_MARK`. A name at the decision perch is written and printed bare;
# the written `[~]` lowers to the bare name.
PERCH_MARK = {perch: "" if perch == DECISION else sign for perch, sign in PERCH_SIGN.items()}
WRITTEN_MARK = {ARRIVAL: "[<]", DECISION: "", CONTINUATION: "[>]"}

# --- the roles of a field ---

# The role a field carries in the fields table. The subject of a distribution
# declaration (`~`) has the role "shock"; a field that carries no role word
# has the role "state"; a multiplier a block body declares has the role
# "multiplier".
STATE, CONTROL, VALUE, SHOCK = ("state", "control", "value", "shock")
MULTIPLIER = "multiplier"
# the roles of the values a backward builder's G yields, in the order n of the
# lowering's `Value(n)`: the value alone, since AMD-MB-001 retired the
# marginal roles; a derivative of a value is the term `D_{x}V`
VALUE_ROLES = (VALUE,)
# the word of each role as a header writes it after `!`: `c : !ctrl`
ROLE_WORD = {
    STATE: "state",
    CONTROL: "ctrl",
    VALUE: "vlu",
    SHOCK: "shck",
}

# the role words retired by AMD-MB-001 §4.1, which a header may not write: a
# derivative of a value is the term `D_{x}V`, and the lowering refuses the
# words under `marginal-role-retired`
RETIRED_ROLE_WORDS = ("mrgnvl", "sndmrgnvl")

# --- the primitive sets ---


@dataclasses.dataclass(frozen=True, kw_only=True)
class Primitive:
    """One primitive set: the glyph of the set a spelling names, its kind, the
    order within that kind, for a real set its endpoints as
    (lower, lower closed, upper, upper closed), and the name under which the
    typing pass records the set a value lies in. A set of a higher order lies
    in every set of its kind of a lower order. An integer set and an extended
    real have no endpoints, so the rules that read endpoints do not reach
    them; an extended real carries no domain name, since the typing pass
    names it after its spelling."""

    glyph: str
    kind: str
    order: int | None
    bounds: tuple | None
    domain: str | None = None


REAL, INTEGER, EXTENDED_REAL = "real", "integer", "extended real"
_INF = math.inf

# Every spelling the grammar's tokens `BBSET` and `RPLUS` admit
# (`bellman/syntax/grammars/stage.lark`): the three real sets ℝ ⊇ ℝ₊ ⊇ ℝ₊₊,
# written also `R_{+}`, `R+`, `R_{++}` and `R++`; the two integer sets ℤ ⊇ ℕ;
# and the four extended reals ℝ̄, ℝ_{+∞}, ℝ_{-∞} and ℝ_{±∞}. A bare `R` is no
# spelling of ℝ: the grammar reads it as a `plain_name`, so it names a set the
# author declares. The table carries the name under which the typing pass
# records the set a value lies in, so that the spellings are listed once.
_REALS = Primitive(
    glyph="ℝ", kind=REAL, order=0, bounds=(-_INF, False, _INF, False), domain="primitive:real"
)
_NONNEGATIVE_REALS = Primitive(
    glyph="ℝ₊",
    kind=REAL,
    order=1,
    bounds=(0, True, _INF, False),
    domain="primitive:nonnegative-real",
)
_POSITIVE_REALS = Primitive(
    glyph="ℝ₊₊",
    kind=REAL,
    order=2,
    bounds=(0, False, _INF, False),
    domain="primitive:positive-real",
)
# the primitive set each spelling names, by the spelling: `ℝ₊`, `R_{+}` and
# `R+` name one set
PRIMITIVE_SETS = {
    "ℝ": _REALS,
    "ℝ₊": _NONNEGATIVE_REALS,
    "R_{+}": _NONNEGATIVE_REALS,
    "R+": _NONNEGATIVE_REALS,
    "ℝ₊₊": _POSITIVE_REALS,
    "R_{++}": _POSITIVE_REALS,
    "R++": _POSITIVE_REALS,
    "ℤ": Primitive(glyph="ℤ", kind=INTEGER, order=0, bounds=None, domain="primitive:integer"),
    "ℕ": Primitive(glyph="ℕ", kind=INTEGER, order=1, bounds=None, domain="primitive:natural"),
    "ℝ̄": Primitive(glyph="ℝ̄", kind=EXTENDED_REAL, order=None, bounds=None),
    "ℝ_{+∞}": Primitive(glyph="ℝ_{+∞}", kind=EXTENDED_REAL, order=None, bounds=None),
    "ℝ_{-∞}": Primitive(glyph="ℝ_{-∞}", kind=EXTENDED_REAL, order=None, bounds=None),
    "ℝ_{±∞}": Primitive(glyph="ℝ_{±∞}", kind=EXTENDED_REAL, order=None, bounds=None),
}

# --- the roles of an authored line ---

# The role of a line of a block, which the construction
# (`stage/construction.py`) gives it: a `!node` line, a line defining a block
# output, an intermediate name, a `!doc` line.
NODE, OUTPUT_LINE, ALIAS, DOC = "node", "output", "alias", "doc"
