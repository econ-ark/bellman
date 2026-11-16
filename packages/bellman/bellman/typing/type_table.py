"""The table of types: the objects of a stage with the type each declaration
writes, the forms of a set expression, and the limits of the language on a
type.

A type is what a stage file or a methods file writes after a colon: sets, a
role word and a perch word, with `@` between them. Each fact about the types
of the language stands here once, in three tables of frozen records:

- `OBJECTS`: one row for each object of a stage, with what it denotes, a
  line of a file of the repository that declares it, the type that line
  writes, the record of the package that holds it and the expression that
  reads it from the stage object;
- `SET_FORMS`: one row for each constructor of a set expression of the
  abstract grammar (`setexpr` of `syntax/grammars/stage.asdl`), with a
  declaration that writes it, what it denotes and the objects in whose type
  the package reads it;
- `LIMITS`: one row for each limit of the language on a type, with a line
  that breaks it and the rule under which the package refuses that line.

The role words, the perch words with their marks and the reserved sets are
not copied here. `bellman.syntax.vocabulary` holds them, in `ROLE_WORD` and
`MULTIPLIER`, in `PERCHES`, `PERCH_WORD` and `WRITTEN_MARK`, and in
`PRIMITIVE_SETS`.

The page `docs/Bellman-Sym/reference/types.md` is printed from the three
tables and from those of the vocabulary by `docs/_hooks/reference_pages.py`
(`types_table`). `packages/bellman/tests/test_types.py` runs every row
through the package, so that a row which no longer holds fails, and
`tests/test_package_documentation.py` checks that the page holds the
tables that the script prints. The module imports
nothing of the package: a row names a record and an expression as text, and
the test resolves the one and evaluates the other.
"""

from __future__ import annotations

import dataclasses

# --- the objects of a stage ---


@dataclasses.dataclass(frozen=True, kw_only=True)
class StageObject:
    """One object of a stage.

    `name` is the word for the object. `denotes` says in one sentence what
    the object is. `line` is a line that declares it: a line of the file
    `file` of the repository, without its annotation. `written` is the type
    that line writes, as prose whose code spans hold stage text. `record` is
    the class of the package whose instance holds the object in an
    elaborated stage, as its module, a colon and its qualified name.
    `read_by` is the expression that reads the object from the stage object,
    as source text in which `stage` is the stage that `file` states or, for
    a methods file, the stage with that file read."""

    name: str
    denotes: str
    line: str
    file: str
    written: str
    record: str
    read_by: str


# The files whose lines the rows quote: the stage file of the perfect
# foresight application, the gridded methods file beside it, and the stage
# file of the buffer-stock application, which declares a shock.
_PERFECT_FORESIGHT = (
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight"
)
_STAGE_FILE = f"{_PERFECT_FORESIGHT}/perfect_foresight.bl"
_METHODS_FILE = f"{_PERFECT_FORESIGHT}/methods.egm.bl"
_BUFFER_STOCK = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"

_SORT = "bellman.native.records:Sort"
_DEFINITION = "bellman.native.records:Definition"

OBJECTS = (
    StageObject(
        name="field",
        denotes=(
            "A named quantity at a perch, with a declared set: a state, a control or a value."
        ),
        line="[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {",
        file=_STAGE_FILE,
        written=(
            "`ℝ₊₊ @ !ctrl` for `c`: a set and a role word. The word `!dcsn` after the side "
            "gives the perch. A field listed with a set and no role word, `a : Xa`, is a state. "
            "For a value-type field, `!vlu @ !cnst` specifies independence from states, "
            "shocks and choices."
        ),
        record=_SORT,
        read_by='stage.fields()["perfect_foresight:dcsn:c"]',
    ),
    StageObject(
        name="shock",
        denotes=(
            "A random quantity whose law the file states on a line of its own, "
            "`ψ ~ LogNormal(-(σ_ψ^2)/2, σ_ψ)`; it belongs to no perch."
        ),
        line="ψ : ℝ₊₊",
        file=_BUFFER_STOCK,
        written="`ℝ₊₊`: a set. The law is no part of the type.",
        record=_SORT,
        read_by='stage.fields()["buffer_stock:shck:ψ"]',
    ),
    StageObject(
        name="parameter",
        denotes="A constant of the model, whose value the calibration supplies.",
        line="β : ℝ₊₊ @ (0, R^(ρ-1))",
        file=_STAGE_FILE,
        written=(
            "`ℝ₊₊ @ (0, R^(ρ-1))`: two sets, which declare their intersection. A parameter "
            "takes no role word and no perch word."
        ),
        record=_DEFINITION,
        read_by='stage.par["β"]',
    ),
    StageObject(
        name="derived parameter",
        denotes=(
            "A constant that the file defines from parameters, numbers and other derived "
            "parameters; the calibration supplies no value for it."
        ),
        line="q : (0,1) := (β*R)^(1/ρ)/R",
        file=_STAGE_FILE,
        written=(
            "A declared set goes before `:=`. Calibration checks the computed value in that "
            "set. With no declared set it checks membership in `ℝ`. A definition by cases "
            "that writes `inf` or `-inf` declares a set that can hold that infinity."
        ),
        record=_DEFINITION,
        read_by='stage.par["q"]',
    ),
    StageObject(
        name="setting",
        denotes=(
            "A value that a numerical method reads, such as the number of points of a grid; a "
            "methods file declares it, and `configure` binds its value."
        ),
        line="n_a : ℕ",
        file=_METHODS_FILE,
        written="`ℕ`: a set.",
        record=_DEFINITION,
        read_by='stage.settings["n_a"]',
    ),
    StageObject(
        name="function",
        denotes="A function that the file defines by an expression in its arguments.",
        line="𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)",
        file=_STAGE_FILE,
        written=(
            "`ℝ₊₊` for the argument `c`: one set for each argument. No set is written for the "
            "values of the function."
        ),
        record=_DEFINITION,
        read_by='stage.definitions["perfect_foresight:function:𝑢"]',
    ),
    StageObject(
        name="operator",
        denotes=(
            "The operator that a block denotes, called a builder: it takes the functions, or "
            "the measures, at one perch to those at another."
        ),
        line=(
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, h[>] : ℝ₊ @ !vlu @ !cnst, c) : !cntn "
            "-> (V : ℝ @ !vlu, h : ℝ₊ @ !vlu @ !cnst) : !dcsn] {"
        ),
        file=_STAGE_FILE,
        written=(
            "The header lists the continuation fields `V[>]` and `h[>]` and the decision "
            "control `c` as inputs. Its outputs are the decision fields `V` and `h`."
        ),
        record="bellman.native.hypergraphs:Builder",
        read_by='stage.builder["cntn", "dcsn"]',
    ),
    StageObject(
        name="measure",
        denotes=(
            "A finite measure on the states of one perch, which the builder of a block that "
            "writes a state reads or writes."
        ),
        line="[id=arvl_to_dcsn, (k : Xa) : !arvl -> (m : Xm) : !dcsn] {",
        file=_STAGE_FILE,
        written=(
            "No type: no line declares a measure. The package makes one on the states of each "
            "side of such a block, here on `Xa` at arrival and on `Xm` at decision."
        ),
        record=_SORT,
        read_by='stage.builder["arvl", "dcsn"].signature()',
    ),
    StageObject(
        name="grid",
        denotes=(
            "The finite set of points at which a numerical method computes and stores a function."
        ),
        line="[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))",
        file=_METHODS_FILE,
        written=(
            "`!Cartesian(a=(a_min, a_max, n_a))`: a grid constructor, whose arguments name "
            "settings."
        ),
        record=_DEFINITION,
        read_by='stage.methods["policy"].grid',
    ),
    StageObject(
        name="method",
        denotes="The numerical procedure chosen for one operator.",
        line="[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))",
        file=_METHODS_FILE,
        written="`!egm`: a method word, followed by its keyword arguments where it takes any.",
        record=_DEFINITION,
        read_by='stage.methods["policy"]',
    ),
    StageObject(
        name="perch",
        denotes=(
            "One of the three information sets of a stage: arrival, decision and continuation."
        ),
        line="[id=arvl_to_dcsn, (k : Xa) : !arvl -> (m : Xm) : !dcsn] {",
        file=_STAGE_FILE,
        written=(
            "`!arvl` and `!dcsn`: the perch word after each side of the header. A mark on a "
            "name states the perch of one field, as `V[>]` does."
        ),
        record="bellman.stage.pieces:PerchHandle",
        read_by="stage.dcsn",
    ),
)


# --- the forms of a set expression ---


@dataclasses.dataclass(frozen=True, kw_only=True)
class SetForm:
    """One constructor of a set expression.

    `constructor` is the name of the constructor in the abstract grammar and
    of its class in `bellman.syntax.terms`. `example` is a declaration of
    one name that writes the form, a whole line. `denotes` says in one
    sentence what set the form is. `read_in` names the objects of `OBJECTS`
    in whose type the package reads the form."""

    constructor: str
    example: str
    denotes: str
    read_in: tuple


# The objects whose declaration writes a set, by their names in `OBJECTS`.
WITH_A_SET = ("field", "shock", "parameter", "derived parameter", "setting", "function")
# Every one of them but the derived parameter, whose value is one number
# and lies in no set of labels, no product and no set of functions.
_BUT_THE_DERIVED_PARAMETER = tuple(name for name in WITH_A_SET if name != "derived parameter")
# Those that one name declares on a line of its own, where several sets in
# one type are read. A field is taken as a block header lists it.
_ON_A_LINE_OF_ITS_OWN = ("shock", "parameter", "derived parameter", "setting")
# Those in whose set a union and a difference are read.
_PARAMETERS_AND_SETTINGS = ("parameter", "derived parameter", "setting")

SET_FORMS = (
    SetForm(
        constructor="Named",
        example="R : ℝ₊₊",
        denotes=(
            "The set of that name: a reserved set of the language, here the strictly positive "
            "real numbers, or a set that the file defines after `:=`, `Xa := ℝ₊`."
        ),
        read_in=WITH_A_SET,
    ),
    SetForm(
        constructor="Interval",
        example="ρ : (1, inf)",
        denotes=(
            "The real numbers between two endpoints, where a round bracket leaves its endpoint "
            "out and a square bracket includes it; an endpoint may read parameters, and `-inf` "
            "or `inf` leaves a side unbounded; an endpoint that is the bare name of a parameter "
            "or of a derived parameter which the calibration values at an infinity is read as "
            "that infinity."
        ),
        read_in=WITH_A_SET,
    ),
    SetForm(
        constructor="FiniteSet",
        example="d : {work, retire}",
        denotes="The labels listed, which carry no arithmetic.",
        read_in=_BUT_THE_DERIVED_PARAMETER,
    ),
    SetForm(
        constructor="Product",
        example="x : ℝ × ℝ",
        denotes="The ordered tuples that take one component from each factor.",
        read_in=_BUT_THE_DERIVED_PARAMETER,
    ),
    SetForm(
        constructor="Comprehension",
        example="θ : ℤ @ [1, inf)",
        denotes=(
            "The members of one set that satisfy every condition stated, here the integers of "
            "at least one; several sets in one type are kept in this form, and a named set "
            "writes it with braces after `:=`, `H := {i : ℤ | i >= 0, i <= 1}`."
        ),
        read_in=_ON_A_LINE_OF_ITS_OWN,
    ),
    SetForm(
        constructor="IntegerRange",
        example="j : {1, …, 5}",
        denotes=(
            "Every integer from the first bound to the second, both included; a bound may read "
            "parameters, and `...` is a second spelling of `…`."
        ),
        read_in=WITH_A_SET,
    ),
    SetForm(
        constructor="Points",
        example="s : {0, 1}",
        denotes=(
            "The integers listed, in the order written; a list in which a member reads a "
            "parameter names the set its members lie in, `{0, θ} ⊂ ℤ`."
        ),
        read_in=WITH_A_SET,
    ),
    SetForm(
        constructor="Functions",
        example="δ : {1, …, 5} → ℝ",
        denotes=(
            "The collections that hold one entry of the second set for each member of the "
            "finite index set. A function-valued constant may also have a continuous domain."
        ),
        read_in=_BUT_THE_DERIVED_PARAMETER,
    ),
    SetForm(
        constructor="SetUnion",
        example="ρ : (0,1) \\/ (1, inf)",
        denotes=(
            "The numbers that lie in at least one of the sets; `∪` is a second spelling of `\\/`."
        ),
        read_in=_PARAMETERS_AND_SETTINGS,
    ),
    SetForm(
        constructor="SetDifference",
        example="ρ : ℝ₊₊ \\ {1}",
        denotes=(
            "The numbers of the first set that the second does not hold; `∖` is a second "
            "spelling of `\\`."
        ),
        read_in=_PARAMETERS_AND_SETTINGS,
    ),
)


# --- the limits of the language on a type ---


@dataclasses.dataclass(frozen=True, kw_only=True)
class Limit:
    """One limit of the language on a type.

    `limit` states the limit in one sentence. `line` is a line that breaks
    it, which the package refuses in the stage text that holds the line
    alone after the line `@stage: t`. `rule` is the rule of that refusal."""

    limit: str
    line: str
    rule: str


LIMITS = (
    Limit(
        limit=(
            "Several sets in one type are one set of numbers and the intervals that bound it, "
            "so at most one of them is written otherwise than as an interval; a named set "
            "counts as such a set."
        ),
        line="θ : ℤ @ ℝ₊₊",
        rule="syntax",
    ),
    Limit(
        limit=(
            "The several sets of one type have a number in common, which the package decides "
            "from the endpoints that are numbers or ratios of two integers, `1/3`."
        ),
        line="β : (0,1) @ (2,3)",
        rule="syntax",
    ),
    Limit(
        limit=(
            "Several sets in one type restrict one declared name, and no declaration of "
            "several names carries them."
        ),
        line="(w, c) : ℝ @ (0, 1)",
        rule="syntax",
    ),
    Limit(
        limit=(
            "Several sets are read on a declaration that stands on a line of its own; a field "
            "listed on a block header and an argument of a function carry one set each."
        ),
        line="𝑓(x : ℝ₊ @ (0, 1)) := x^2",
        rule="readable-form",
    ),
    Limit(
        limit=(
            "A union and a difference are formed among sets of numbers; a set of labels, a "
            "product and a set of functions are no members of one."
        ),
        line="β : {a, b} \\/ (0, 1)",
        rule="syntax",
    ),
    Limit(
        limit=(
            "A union and a difference are read in the set of a parameter, of a derived "
            "parameter and of a setting; the set of a field, of a shock and of an argument of "
            "a function holds neither."
        ),
        line="c : ℝ₊₊ \\ {1} @ !ctrl",
        rule="readable-form",
    ),
    Limit(
        limit="The value of a named set, written after `:=`, is no union and no difference.",
        line="Xρ := (0,1) \\/ (1, inf)",
        rule="syntax",
    ),
    Limit(
        limit=(
            "The value of a named set holds no union and no difference inside it either, such "
            "as the set of the entries of a collection."
        ),
        line="Xq := {1, …, 2} → ℝ \\ {0}",
        rule="readable-form",
    ),
    Limit(
        limit=(
            "A definition that declares a set reads at least one name; a value that reads "
            "none is a number, which the calibration supplies."
        ),
        line="ρ : ℝ := 2",
        rule="readable-form",
    ),
    Limit(
        limit=(
            "A formula by cases may stand on the right side of an equation or of a derived "
            "parameter definition, including as a nested branch. A declared set endpoint "
            "admits no formula by cases."
        ),
        line="x : (0, if 1 < 2 then 1 else 2)",
        rule="syntax",
    ),
    Limit(
        limit=(
            "In a derived parameter's definition `inf` and `-inf` stand only as a whole branch "
            "of a definition by cases; a definition that reads a name valued at an infinity "
            "where it is evaluated, in a formula, a call or a test, as the branch that its test "
            "chooses or as its whole right side, has no value at that calibration, and neither "
            "has a bound of a declared set that computes with such a name; a bound that "
            "computes with the written `inf`, `(0, 2*inf)`, has none at any calibration; a "
            "bound that calls a function other than `log`, `exp`, `min` and `max` is not "
            "decided, whatever it computes with."
        ),
        line="x := 2*inf",
        rule="derived-parameter",
    ),
    Limit(
        limit="The words `if`, `then` and `else` are words of the language and no names.",
        line="if : ℝ₊₊",
        rule="syntax",
    ),
    Limit(
        limit=(
            "A branch written `inf` or `-inf` stands in a definition whose declared set can hold "
            "that infinity, and the set `ℝ` of a definition that declares none holds neither."
        ),
        line="h := if 1 < 2 then 1 else inf",
        rule="derived-parameter",
    ),
)
