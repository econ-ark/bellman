"""The refusals of the package: the four classes a caller catches, the closed
vocabulary of rules each names, and the names of the conditions a stage states.

A refusal says where the fault is, what stands there, why it is refused and
what to write instead, the four parts of a refusal. Each class carries its
rule as a field, so that a caller — the elaborator, an editor, a test — reads
the rule and the position as fields rather than by matching the sentence:

- `ConstructionError`, a stage file that graph construction refuses, under one
  rule of `RULES`, with the position of the authored item responsible;
  `NotConstructed`, its subclass, a form the construction does not read, under
  the rule `not-constructed`;
- `TargetError`, a name that reaches no piece of a stage, or two, under one
  rule of `TARGET_RULES`;
- `FactoryError`, a registry, a recipe, a fill, a trellis file, a trellis
  dictionary, a record or a period that the Bellman factory refuses, under one
  rule of `FACTORY_RULES`.

`CONDITIONS` names the conditions a stage states and the construction does not
discharge, the field `condition` of a `records.Condition`. The
catalogue of the rules is `bellman.refusal_catalogue`, and the smallest
example that breaks each rule stands in `bellman.refusal_examples`.

A refusal of graph construction or of the factory may name a second place
beside the item it is raised at, a `Location` with its role, and may carry
the action, `write`, where the check establishes the edit; both are fields,
printed on lines after the sentence, so that a reader links the second place
and labels the action without reading the sentence (Model Interface 0.9 §4).

`Diagnostic` is what an elaboration records without refusing: a problem of a
connection of a trellis (`bellman.factory.connections`), or a value input a
backward block's header lists and no line of the block reads
(`bellman.stage.stage_answers`), each with its rule, its address and its
sentence. A reader shows a diagnostic beside the elaborated object; it stops
nothing.

A caller imports the four classes from this module, `bellman.refusals`;
`packages/bellman/README.md` states where this module stands in the order of
the folders.
"""

from __future__ import annotations

from typing import NamedTuple

__all__ = (
    "CONDITIONS",
    "ConstructionError",
    "Diagnostic",
    "FACTORY_RULES",
    "FactoryError",
    "Location",
    "METHOD_CONDITIONS",
    "NotConstructed",
    "RULES",
    "TARGET_AMBIGUOUS",
    "TARGET_NOT_FOUND",
    "TARGET_RULES",
    "TARGET_VERSION",
    "TargetError",
    "construction_error",
    "location",
    "written_kind",
)


# --- the second place a refusal names ---


class Location(NamedTuple):
    """A second place a refusal names beside the item it is raised at: its
    `role` in the refusal, `original declaration` for the earlier item of a
    pair, `authored law` for the forward law a backward line reaches a state
    through, `dependency` for an item of a cycle, `rejected setting` for the
    key of a settings file, `settings source` for the settings file itself;
    the `file`; the range `line`, `column`, `end_line` and `end_column`,
    counted as `ConstructionError` counts them, each None where the place has
    no position; and the `address` of the item, a term address or a key of a
    YAML file. `str` prints the role, the position and the address."""

    role: str
    file: "str | None" = None
    line: "int | None" = None
    column: "int | None" = None
    end_line: "int | None" = None
    end_column: "int | None" = None
    address: "str | None" = None

    def __str__(self) -> str:
        if self.line is not None:
            where = f"{self.file if self.file else '<text>'}:{self.line}:{self.column}"
            if self.end_line is not None and self.end_column is not None:
                where += f"-{self.end_line}:{self.end_column}"
            if self.address is not None:
                where += f" (address {self.address!r})"
        elif self.address is not None:
            where = (f"{self.file}: " if self.file else "") + f"address {self.address!r}"
        else:
            where = self.file or "<text>"
        return f"{self.role}: {where}"


def location(role, *, address=None, span=None, file=None):
    """The `Location` of a second item, positioned by `span`, a
    `bellman.syntax.lower.SourceSpan`, or by `file` alone where the item has
    no span, as `construction_error` positions the item responsible."""
    return Location(
        role,
        file=file if span is None else span.file,
        line=None if span is None else span.line,
        column=None if span is None else span.column,
        end_line=None if span is None else span.end_line,
        end_column=None if span is None else span.end_column,
        address=address,
    )


def written_kind(value):
    """What a value a YAML file or a Python caller wrote is, in words, for a
    refusal that expected another kind: `a list`, `the text 'x'`, `the number
    3`, `the word true` or `the word false` for a Boolean, `a mapping`,
    `nothing`, or `a value of another kind`."""
    if value is None:
        return "nothing"
    if isinstance(value, bool):
        return f"the word {str(value).lower()}"
    if isinstance(value, (int, float)):
        return f"the number {value!r}"
    if isinstance(value, str):
        return f"the text {value!r}"
    if isinstance(value, (list, tuple)):
        return "a list"
    if isinstance(value, dict):
        return "a mapping"
    return "a value of another kind"


def _lines_after(related, write):
    """The lines a refusal prints after its sentence: one per related
    location and one for the action, each indented."""
    lines = [f"\n  {held}" for held in related]
    if write:
        lines.append(f"\n  write: {write}")
    return "".join(lines)


# --- the refusals of graph construction ---

# The rules a stage file and its typed numerical bindings must satisfy. Each
# name is the field `rule` of a refusal and is a claim about authored input,
# not about the code that checks it.
RULES = (
    # The file is written in the forms the grammar admits, and every !-marked
    # word is one of the vocabulary. It is the first rule a
    # file meets: the refusal is raised where the parser or the lowering
    # stops, and names the forms admitted at that place.
    "syntax",
    # The roles `!mrgnvl` and `!sndmrgnvl` are retired from the language: a
    # backward header lists value fields and controls, and a derivative of a
    # value is the term `D_{x}V`.
    "marginal-role-retired",
    # The file names itself once: exactly one `@stage` line, with a name.
    "stage-name",
    # Each name, block id, statement id, and law is written once.
    "declared-once",
    # Within one block, an operative equation defines each name-sided left
    # side once, and a derivative line states each derivative term, `D_{m}V`,
    # once. A documentary line (`!doc`) defines and states none.
    "defined-once",
    # A name is one of a field, a function, a named space, a shock or a
    # parameter, and is not the name of a numerical operator.
    "one-name-one-meaning",
    # A name that a stage file declares at the top level is a field where a
    # block header lists it; where none does, it is a parameter unless it has
    # a law or the word `!shck`, and a parameter carries no role word. No line
    # of a block writes a parameter, a derived parameter or a setting.
    "parameter-or-field",
    # Every listed field has one perch, fixed by its side's perch word, its
    # mark, or its role, and the three must agree.
    "field-perch",
    # Every name a statement, method entry or definition body mentions is
    # declared where it is used, and every set a typing names, `n_m : Foo`, is a
    # named set the stage defines or a set of the language.
    "name-in-scope",
    # A selection takes a coordinate of a declared family by a key the family
    # admits.
    "family-selection",
    # Every operation of a line, a function body or a declared set reads
    # values of the kinds it takes: arithmetic, an ordered comparison and the
    # bounds of an interval read numbers, and a label is no number; a function
    # is applied to as many arguments as it declares, each of the kind it
    # declares; `Inv` inverts one function; the two sides of a line are of one
    # kind, and its left side names one field for each result of its
    # right side.
    "well-typed",
    # A divisor the file writes as a number is not zero: a division by a
    # written zero is defined at no point (the definedness conditions of the
    # fold).
    "divisor-nonzero",
    # A statement's perch has observed every shock the statement's right side
    # depends on; otherwise the statement asks for an expectation.
    "shock-observed",
    # A backward function does not read a shock again beside a term whose
    # expectation has integrated it.
    "shock-reintroduced",
    # The fields a statement's right side mentions are at the left side's
    # perch, before it, or forward of it along the stage's transitions.
    "forward-composite",
    # One block writes a field between two perches: a second block that
    # joins the same perches and writes a field the first writes is refused
    # naming both blocks.
    "one-builder-per-output",
    # A candidate line of a policy block, `x[>] = …`, names a control at the
    # candidate points, `c[>]`, a state of the decision perch, the grid line
    # `m[>] = a + c[>]`, or the value candidate an upper envelope of the
    # block compares; any other name is refused with the coordinates in
    # scope.
    "candidate-coordinate",
    # A candidate a policy block writes is read by a later line of the block
    # or is the grid line, whose points are the knots of the policy; a
    # candidate nothing reads is refused naming the line.
    "candidate-read",
    # A transition block's statements define the state transition g and
    # contain no expectation: the forward builder is the push-forward of a
    # measure through g, and integration over a shock belongs to a value
    # block (Operators and builders, §"Forward operators").
    "transition-without-expectation",
    # A block has at most one implicit statement for each output field.
    "one-implicit-statement",
    # The function definitions have a dependency order, and each applies a
    # defined function.
    "definition-order",
    # A derivative names one formal argument, not several arguments at once.
    "derivative-one-name",
    # The one formal argument a derivative names is scalar, not product-valued.
    "derivative-scalar-coordinate",
    # A derivative of a value field, `D_{a}V[>]`, names a state coordinate of the
    # perch at which the field is read, and not a discrete one; for the value
    # of a branch, `D_{a_w}V_w[>]`, a state the branch writes.
    "derivative-coordinate",
    # Every field is produced and consumed: a block writes it or the stage
    # receives it, and a block reads it or the stage delivers it.
    "stage-boundary",
    # Every required block output has an equation.
    "output-defined",
    # A grid line, a line that writes a decision state under the continuation
    # mark (`m_d[>] = a + c[>]`), agrees with the law of motion solved for
    # that state at the candidates: its right side and the law of motion so
    # solved reduce to one expression, every function read as an opaque
    # symbol.
    "grid-line-consistency",
    # No authored name collides with the spelling of an identity: a name
    # containing the colon that separates its segments, or a name equal to one
    # of the words a reader tests for in the last segment, `result`,
    # `declared` or `merged`.
    "identity-collision",
    # The item is a form the construction rules read.
    "readable-form",
    # A component of an operator's signature, its method, its grid or its
    # handler, is typed by one entry: two entries at one place, an entry for
    # the whole of an Evaluation beside one for an object it stores, or a
    # stage-wide or block-wide operator head beside one of its occurrences,
    # are refused naming both.
    "component-typed-twice",
    # The derivative operator `D` and its occurrences admit no typing: nothing
    # is differentiated by a method, and a definition by `D` is an authored
    # expression or a handler's.
    "no-method-for-derivative",
    # A method word stands at a place of a kind its row of the catalogue
    # admits, a representation at an Evaluation, a quadrature at an
    # expectation, a solution method on a builder, and its entry writes every
    # keyword the row requires there, one count per shock for a quadrature's
    # nodes.
    "method-admission",
    # No argument of a method word is written as a number, at any depth of
    # its tuples and nested words: a number that a method reads is a setting
    # the methods file declares, whose value the settings file holds.
    "method-setting-declared",
    # A function representation's family accepts the data its place
    # supplies, chosen in the order of an authored table, the policy pairs of
    # an `!egm` builder's closing Evaluation, a complete authored expression
    # with an explicit kernel, and the family's own nodes; missing data
    # selects no other case, and an optional grid beside an authored table
    # discretizes the coordinates at which the table is evaluated, written as
    # a name or as a tuple of names in the order of the grid's coordinates,
    # and has exactly its finite support where both are known at
    # configuration.
    "representation-source",
    # An `!explicit` builder is a policy or backward value builder to which
    # an addition appends lines in a block of the builder's id, `[id=policy,
    # policy.method : !explicit]`, which stand in place of the declared lines
    # at the operative level; a builder with no such block is refused. The
    # lines write every output by `output = expression` on the states of the
    # builder's own perch, the parameters, the derived parameters and the
    # names the block introduces, with a compiled kernel for each output: a
    # line that reads an input of the builder's header, a value input or its
    # derivative or a control at which a value builder's declared lines are
    # read, states a relation or applies an operator on its right side is
    # refused naming `!egm` or `!time_iteration`, a line that defines or reads
    # a field at another perch, the candidate `c[>]` or the identification
    # `c = c[>]`, naming `!egm`, and a block that writes no output with the
    # line `<output> = <expression>` to write; each refusal stands at the line
    # at fault, and at the typing entry where no line is. A complete block of
    # such lines under `!egm` or `!time_iteration`, appended by an addition or
    # written in the stage file, is refused, naming `!explicit`.
    "explicit-solution",
    # Over the files of a stage, a component is typed once, whether by an
    # absolute or a relative spelling of its path, a name is defined once, or
    # identically in each file, and a line id names one line of a block; the
    # union of the stage file and its additions refuses a second entry,
    # definition or line naming both positions.
    "declared-twice",
    # A nested block of an addition merges with the branch of the same label
    # under its parent, and a path inside a block names a line or an operator
    # of that block: a label the parent lacks, and a first segment that names
    # another block, are refused.
    "label-not-in-parent",
    # The field names determine a signature: a coordinate an addition restates
    # keeps the stage's typing, and a different type on it, or a different
    # perch word on its side, is refused.
    "type-conflict",
    # An addition names the stage it adds to, `@methods: <stage>`, with the
    # name the stage file gives itself, and a metadata line of another key
    # agrees with the stage file's line of that key.
    "metadata-mismatch",
    # Every factor of a grid names a coordinate of the function the place
    # holds, a control of the builder for a feasible factor or a shock for a
    # quadrature factor; a coordinate no factor names takes the default, the
    # product over the coordinates of that function, as every coordinate does
    # where the place writes no grid entry; a method that reads no grid has
    # none written at its place, and a representation fitted from the pairs
    # the endogenous grid method computes has no grid of its own at the
    # Evaluation of the builder that method solves, since its nodes are the
    # endogenous points of the pairs. A grid constructor stands only at the
    # places its record admits, `!Fibred` only where the occurrence's domain
    # is its base's states followed by its fibre's controls; the base of
    # `!Fibred` is `!Points` or a `!Cartesian` term on the states, and its
    # fibre a
    # `!Cartesian` term of feasible-control factors; each declared point of
    # `!Points` has one coordinate for each coordinate of the place.
    "grid-coordinate",
    # Every name a factor of a grid writes is a setting the methods file
    # declares, a node set the stage defines or an expectation operator of
    # the stage, and the declared points of `!Points` are a setting the
    # methods file declares or a set the stage defines; a bound or a count
    # written as a number is refused.
    "grid-setting-declared",
    # At configuration the bounds of a factor are in order and inside the
    # coordinate's declared set, its count is at least two, and a node set
    # is strictly increasing; each configured point of `!Points` has finite
    # real coordinates inside the coordinates' declared sets. A declared set
    # that reads a parameter is read at the calibration that is bound, and
    # before one is bound a bound of a factor over such a set is refused.
    "grid-bounds",
    # The predicate words a grid writes after `require` are among `!Empty`,
    # `!Cartesian`, `!NonCartesian` and `!UniformCartesian`, and no two
    # contradict each other; each holds of the grid wherever the bound values
    # decide it, an outer requirement of `!Fibred` of the joint grid and one
    # inside its fibre of each fibre. The numerical construction of a grid
    # establishes its finite points, a factor for each coordinate, a sampler
    # for each feasible set and every required property before the grid is
    # used, and reports what it cannot establish instead of supplying a
    # default.
    "grid-requirement",
    # A setting's configured value lies in the set its declaration names.
    "setting-outside-set",
    # Every setting the methods file declares, and every setting a bound
    # method's keyword arguments or grid name, has a value when settings are
    # bound.
    "setting-unvalued",
    # A multiplier is declared inside the block whose continuation grid it
    # extends, once, marked `[>]`, with one declared set and one bound after
    # ⟂ that names continuation states, multipliers of the block, parameters,
    # numbers or `inf`.
    "multiplier-declaration",
    # A field produced on one declared set and consumed on another is
    # declared with sets whose inclusion holds; otherwise the stage
    # declares the inclusion through the control's feasible set.
    "set-mismatch",
    # A set marked `!categories` is a nonempty range of integers written as a
    # comprehension over ℤ or ℕ, whose annotation gives each member one
    # category name and each name one member. The marker is written only on
    # a top-level named set, and a field declared on a set with category
    # codes names that set at every site that names a set.
    "category-codes",
    # A statement of a backward block reads values or marginal values, not
    # both: its kernel acts on one role and its output has that role.
    "value-input-role",
    # A forward block's header lists every field its lines read that no earlier
    # line of the block defines. A backward block's header lists the value
    # fields its lines read and the controls at which they are read, but no
    # state; a state of its output perch is a coordinate. A value field a
    # backward header lists and no line of the block reads is admitted: it is
    # left out of the block's builder and recorded as a diagnostic,
    # `unread-input`, in place of a refusal.
    "signature-complete",
    # A backward block's header lists the value fields it reads and writes
    # and the controls at which its lines are read, and no state: a state of
    # the perch at which its output stands is a coordinate of the output
    # function, and a state of its input perch is reached through the law of
    # motion.
    "header-coordinate",
    # A backward line reads a state of its input or a later perch only through
    # the law of motion. A direct read is refused, including in a relation or
    # a condition after `⟂`. A read under the expectation over the edge's shock
    # and continuation-state indexing on a policy candidate line are admitted.
    "input-perch-state",
    # A kernel that `compile_kernel` writes as a Python function is retained
    # arithmetic and calls to closed-form functions; a symbolic derivative has
    # no compile rule. The function takes the values of the parameters it
    # reads as arguments, so a symbolic version compiles too and answers no
    # values, `parameter_values` None.
    "kernel-form",
    # Every configured keyword argument of a method lies in the domain its
    # row of the catalogue names for it.
    "method-option-value",
    # `kernel` and `compile` read a primitive operator box, and `compile` one
    # whose kernel is g or G.
    "kernel-target",
    # The distribution declarations read one another without a cycle, and a
    # declaration does not read its own subject.
    "distribution-dependency",
    # The shocks of connected declarations are drawn on the edge of one
    # forward builder.
    "distribution-edge",
    # A declaration's family parameters lie in the family's domain: matched
    # dimensions, a symmetric positive semidefinite covariance, nonnegative
    # variances and deviations, finite endpoints in order, positive scales,
    # and real arguments that have a number.
    "distribution-domain",
    # A derived parameter's definition, `h := 1/(1 - Γ/R)`, reads declared
    # parameters, finite numbers and other derived parameters, and is formed
    # by signs, sums, differences, products, quotients, powers, the calls
    # `log` and `exp` of one argument and the calls `min` and `max` of one
    # argument or more, or by cases, `if … then … else …`; where the stage
    # defines a function of one of those four names, the definition calls
    # none of that name. The calibration supplies no value for it, and at the
    # calibration values every operation it evaluates is defined and its
    # value is a finite real number, or the infinity a branch of its
    # conditional writes. The set a definition declares, `q : (0,1) :=
    # (β*R)^(1/ρ)/R`, is a set of numbers and reads no setting, and it holds
    # each infinity that a branch writes: a definition that declares no set
    # writes no infinite branch.
    "derived-parameter",
    # The conditional distribution an expectation needs is a declared
    # conditional, a product of them, or a marginal or conditional of a joint
    # normal declaration whose conditioning block is positive definite.
    "conditional-not-declared",
    # A branching block holds one labeled nested block per label and nothing
    # else, at least two, in the forward block from the decision perch to the
    # continuation perch, whose own output side is empty; a nested block has an
    # empty input side and writes continuation fields.
    "branch-form",
    # The nested blocks carry the labels of the block's label coordinate, a
    # control or a shock with its law, whose set is a finite set of at least
    # two labels, each once and in the set's order.
    "branch-labels",
    # The value line selects by one tuple indexed by the label coordinate, one
    # entry per label, and the policy maximizes over the same tuple in the same
    # order; a branch a shock selects is read under the expectation over the
    # shock alone.
    "branch-tuple-mismatch",
    # A continuation value stands at one position of the selection tuples, the
    # position of the branch on whose fields it is a function.
    "branch-value-position",
    # The law of a label shock gives one probability to each label in the
    # order of the labels, `Categorical((p₁, …, pₙ))` or `Bernoulli(p)` over
    # two.
    "branch-law",
    # The item is a form of the language the construction does not read.
    "not-constructed",
)


class ConstructionError(ValueError):
    """A stage file that graph construction refuses, with the position of the
    authored item responsible and the rule it does not satisfy. No partial
    stage object is returned.

    The fields. `stage` is the stage's name, or None when the file's `@stage`
    line has not yet been read. `file`, `line`, `column`, `end_line`, and
    `end_column` are the position of the authored item responsible, taken from
    the transient source-span table of the parse (`bellman.syntax.lower.
    parse_with_spans`); all five are None for a term decoded from a saved AST,
    which carries no positions. `line` and `end_line` count lines from one;
    `column` and `end_column` count code points from one, as `SourceSpan`
    counts them, so an editor that counts UTF-16 code units converts a
    column that follows a character outside the Basic Multilingual Plane,
    such as 𝑢. `address` is the address of the item responsible: a block-line
    address (`policy`, `policy.cons_choice`), the file position of a
    top-level declaration (`cons.bl:6`), or the term address a term carries
    whether or not a span table was given; it is set whenever an authored
    item is responsible. `rule` is one of `RULES`, which the constructor
    checks wherever the refusal is made. `message` is the explanation, in
    the words of the model (field, perch, shock, block, statement), and
    states the condition the item fails; the action stands apart from it in
    `write`. `related` is the tuple of `Location`
    records of the second items the sentence names, the earlier declaration
    of a pair or the authored law a line reaches a state through, empty where
    it names none; `write` is the action, the edit the check establishes, or
    None where the check establishes none.

    `str(error)` leads with the position, as an editor and a compiler both
    print it, and the bookkeeping follows the sentence a modeler reads:

        cons.bl:33:5-33:52: block 'policy' … (address 'policy.cons_choice';
            rule name-in-scope)

    and, without a position,

        address 'policy.cons_choice': block 'policy' … (rule name-in-scope)

    The related locations and the action follow on lines of their own, so
    that the first line is the same whether or not they are filled.

    It is a `ValueError`, so that a caller that catches `ValueError` catches
    every refusal.
    """

    def __init__(
        self,
        message,
        *,
        stage=None,
        file=None,
        line=None,
        column=None,
        end_line=None,
        end_column=None,
        address=None,
        rule=None,
        related=(),
        write=None,
    ):
        if rule is not None and rule not in RULES:
            raise ValueError(
                f"{rule!r} is no rule of graph construction; the rules are {', '.join(RULES)}"
            )
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.file = file
        self.line = line
        self.column = column
        self.end_line = end_line
        self.end_column = end_column
        self.address = address
        self.rule = rule
        self.related = tuple(related)
        self.write = write

    def __str__(self) -> str:
        return self._head() + _lines_after(self.related, self.write)

    def _head(self) -> str:
        """The position, the message and the rule, which the related
        locations and the action follow on lines of their own."""
        tail = f"rule {self.rule}" if self.rule else "no rule named"
        if self.line is not None:
            where = f"{self.file if self.file else '<text>'}:{self.line}:{self.column}"
            if self.end_line is not None and self.end_column is not None:
                where += f"-{self.end_line}:{self.end_column}"
            if self.address is not None:
                return f"{where}: {self.message} (address {self.address!r}; {tail})"
            return f"{where}: {self.message} ({tail})"
        if self.address is not None:
            prefix = f"{self.file}: " if self.file else ""
            return f"{prefix}address {self.address!r}: {self.message} ({tail})"
        prefix = f"{self.file}: " if self.file else ""
        return f"{prefix}{self.message} ({tail})"


class NotConstructed(ConstructionError, NotImplementedError):
    """A form of the language that the construction rules do not read: a
    branching block listing a control beside its label coordinate, or one a
    shock selects in a stage that chooses, a definition or a law inside a
    block, a statement whose left side is not one field name. The file may be
    correct; no construction rule reads the form. It is a `ConstructionError`
    and a `NotImplementedError`, so a caller may catch either."""


def construction_error(
    message,
    *,
    stage,
    address,
    span,
    rule,
    error_class=ConstructionError,
    file=None,
    related=(),
    write=None,
):
    """A `ConstructionError` (or, with `error_class=NotConstructed`, a
    `NotConstructed`) for the item at `address`, positioned by `span` — a
    `bellman.syntax.lower.SourceSpan` for a fresh parse, or None for a term
    decoded from a saved AST, which carries no positions. A refusal made
    after construction, when no span table remains, gives no span and
    names the source the stage records as `file`. `related` and `write` are
    the second places the sentence names and the action, as the class holds
    them. The rule is refused where it is not one of `RULES`, by the
    constructor, which checks it at every site."""
    return error_class(
        message,
        stage=stage,
        address=address,
        rule=rule,
        file=file if span is None else span.file,
        line=None if span is None else span.line,
        column=None if span is None else span.column,
        end_line=None if span is None else span.end_line,
        end_column=None if span is None else span.end_column,
        related=related,
        write=write,
    )


# --- the refusals of a name that reaches no piece, or two ---

# The three failures a name can suffer when it is read against the pieces of
# a version (`stage/boxes.py`, `piece_and_place`), the one vocabulary of
# `TargetError.rule`: the constructor refuses a rule outside it, so that
# every site names one of them. Each name is the field `rule` of a
# `TargetError`, and the comment above it states the rule's claim, as the
# comments of `RULES` do.
TARGET_RULES = (
    # A name given to a query of the stage object, a box name or an identity,
    # names a piece the version asked holds.
    "target-not-found",
    # A name given to a query reaches one piece of the version, not two.
    "target-ambiguous",
    # An object given to a query belongs to the version asked: a box or a
    # record of one version is not read against another version, since
    # versions share no object.
    "target-version",
)
TARGET_NOT_FOUND, TARGET_AMBIGUOUS, TARGET_VERSION = TARGET_RULES


class TargetError(LookupError):
    """A name that reaches no piece of a stage, or two. `target` is the name
    as given; `stage` the stage's name; `rule` one of `TARGET_RULES`;
    `candidates` the names the stage holds; the message names all four."""

    def __init__(self, target, stage, rule, candidates, message, *, write=None):
        if rule not in TARGET_RULES:
            raise ValueError(
                f"{rule!r} is no rule of `TARGET_RULES`, the names of the pieces; the "
                f"rules are {', '.join(TARGET_RULES)}"
            )
        super().__init__(message)
        self.target = target
        self.stage = stage
        self.rule = rule
        self.candidates = tuple(candidates)
        self.message = message
        self.write = write

    def __str__(self):
        return self.message + _lines_after((), self.write)


# --- the refusals of the Bellman factory ---

# The rules of the Bellman factory: what a recipe, a
# source file, a fill, a trellis file, a trellis dictionary, a record and the
# joins of a period must satisfy. Each name is the field `rule` of a
# `FactoryError`.
FACTORY_RULES = (
    # The recipe names its trellis file under `trellis:` and has a `stages`
    # mapping; each stage key stands once and its entry names its stage file
    # under `stage:`, each file by its path from the recipe's folder; each
    # kind block is a mapping with an `all` list; a range key is written
    # `lo-hi` with lo ≤ hi and no two ranges of one list overlap; `periods:`
    # is a pair.
    "recipe-shape",
    # Every source name is relative to the registry without `..`, names a file
    # the registry holds, of the kind of the list it stands in, and its
    # `parent:` chain neither cycles nor exceeds ten files.
    "recipe-source",
    # Every fill names a slot the recipe declares by a `$` name in one of its
    # source lists.
    "recipe-slot-unknown",
    # Every stage the recipe names occupies a period the trellis file holds,
    # and every stage a period holds is named by the recipe.
    "recipe-template-agreement",
    # A slot is bound to a mapping.
    "slot-value-not-a-mapping",
    # Every key of a fill names a parameter or a setting a receiving stage
    # declares, or a name the `registry` block admits.
    "fill-names-nothing",
    # A flat fill names parameters or settings, not both.
    "fill-mixes-kinds",
    # A trellis file, or a trellis dictionary, lists its `periods` and its
    # `inter_connectors`; each period holds `stages` and `connectors`; each
    # record of a file names its `stage`.
    "trellis-file-shape",
    # A record holds `stage` as `{text, origin}` and its three mappings, and a
    # supplied digest or origin agrees with the source.
    "record-shape",
    # The pairs of a period, authored by its connectors or inferred from
    # equal field names, close no cycle, and no connector joins a stage to
    # itself.
    "period-join-cycle",
    # A connector is a mapping, flat or in the keyed form {from, to, fields}
    # within a period, and one entry maps a continuation field; a connector
    # whose endpoint names no field, or several, is a diagnostic of the
    # trellis's selection of its connections and no refusal.
    "connector-names-no-field",
    # A parameter name two or more stages of one period declare names one
    # parameter of the period: the sets the stages
    # declare it with have one nonempty intersection the package reads, the
    # stages' sources supply it one value, and that value lies in every
    # declared set; a setting name two or more stages declare in their
    # methods files names one setting of the period in the same way.
    "period-parameter-agreement",
    # A stage file, read by its path or named under `stage:` in a recipe, is a
    # readable `.bl` file of UTF-8 text; a source file a binding verb reads, or
    # a record of a trellis file names, is a readable YAML mapping that writes
    # each key once.
    "readable-file",
)


class FactoryError(ValueError):
    """A registry, a recipe, a fill, a trellis file, a trellis dictionary, a
    record or a period the Bellman factory refuses, under one rule of
    `FACTORY_RULES`, in the four parts of a refusal: `file` and `address` say
    where, `written` what stands there, `message` why, and `write` what to
    write instead. `line` and `column` are the position of the refused key
    in a YAML file, counted from one, where the reader of the file knows it,
    and None otherwise; `related` is the tuple of `Location` records of the
    second places the sentence names, the first writing of a key written
    twice among them. `str(error)` is the file with the position, the
    address, the message, the advice and the rule, then one line per related
    location; an empty part is left out."""

    def __init__(
        self,
        message,
        *,
        rule,
        file=None,
        address=None,
        written="",
        write="",
        line=None,
        column=None,
        related=(),
    ):
        if rule not in FACTORY_RULES:
            raise ValueError(
                f"{rule!r} is no rule of the Bellman factory; the rules are "
                f"{', '.join(FACTORY_RULES)}"
            )
        super().__init__(message)
        self.message, self.rule, self.file, self.address = message, rule, file, address
        self.written, self.write = written, write
        self.line, self.column, self.related = line, column, tuple(related)

    def __str__(self) -> str:
        head = f"{self.file}: " if self.file else ""
        if self.line is not None:
            head = f"{self.file if self.file else '<text>'}:{self.line}:{self.column}: "
        place = f"address {self.address!r}: " if self.address is not None else ""
        advice = f"; write {self.write}" if self.write else ""
        first = f"{head}{place}{self.message}{advice} (rule {self.rule})"
        return first + _lines_after(self.related, None)


# --- the conditions a stage states ---

# The conditions a stage states and the construction does not discharge, each
# the field `condition` of a `records.Condition`. A condition is a
# claim about the model that a later step must establish; a rule of `RULES`
# above is a claim about the authored file that the construction checks. No
# condition states that a policy attains the maximization a `!doc` line
# declares, nor a hypothesis of monotonicity, injectivity, coverage or
# concavity under which a relation defines a policy: those are propositions of
# the calculus, stated for the reader on its pages and held by no record.
CONDITIONS = (
    # the conditions the fold records on the lines, the definitions and the
    # sets (the `fold` folder, `distributions.edges.factorization_obligation`)
    "aggregation-admissibility",
    "arithmetic-definedness",
    "binding-domain",
    "conditioning-covariance-positive-definite",
    "covariance-positive-semidefinite",
    # the parameters of a uniform, truncated normal or type-I extreme-value
    # law lie in the family's domain, where an argument reads a name the
    # stage leaves without a value
    # (`distributions.families.parameter_condition`)
    "distribution-parameters-in-domain",
    "distribution-weights-are-a-probability-vector",
    "expectation-integrability",
    "external-callable-result-domain",
    "external-callable-signature-and-provider",
    "finite-real-arithmetic",
    "function-argument-domain-inclusion",
    "inverse-function-domain",
    "joint-distribution-factorization",
    # the masses of the measures a branching block writes, one per label, sum
    # to the mass of the measure it reads
    "mass-conservation",
    # a declared law gives probability only to values in its subjects'
    # declared sets; established at calibration where the package knows the
    # law's support (AMD-SG-036 §4). A numerical routine that provides the
    # law is no condition: a solver reads one where a methods file names it
    # and chooses its own otherwise
    "law-support",
    "numeric-domain-compatibility",
    "range-compatibility",
    "retained-relation",
    "set-inclusion",
    # the conditions of the stage as a whole (`stage/stage_answers.py`), of
    # which the two `native.records._STRUCTURAL` names a caller cannot assume
    # away
    "partial-field-stage",
    "unresolved-policy-evaluation",
    # the membership of a bound value in its declared set
    # (`stage/calibration_requirements.py`)
    "calibration-domain-membership",
    # the conditions a finite index set owes before its parameters have
    # values (`typing/sets.py`, `finite_set_conditions`): the bounds of an
    # integer range are integers in order, and the members of a listed set
    # are distinct and lie in the set they are declared to lie in
    "index-set-bounds",
    "index-set-members",
    # the feasibility of the pairs a policy insertion writes, which the
    # primitive definition of `PolicyInsertion` requires
    # (`typing/primitive_definitions.py`)
    "feasibility",
    # the condition under which the construction of a bound method satisfies
    # the builder's declared line, named by the method's row of the method
    # table, listed by `stage.obligations()` and checked by nothing
    # (specification 0.6 §4.1 and decision 2)
    "egm-eligibility",
    "marginal-reading",
    # the conditions a function representation owes (AMD-MT-003 build
    # contract §§3, 4; `stage/representations.py`): that it is evaluated where
    # its data support the represented function, that a family reading its
    # own nodes at an `!egm` builder's closing Evaluation is sampled from the
    # selected pairs, and that an optional grid beside an authored table has
    # the table's finite support
    "evaluation-domain",
    "pair-reconstruction",
    "table-grid-support",
)


# The conditions a bound method requires, of `CONDITIONS`, each with the
# sentence that states it; a card prints one by its name and its sentence,
# since it holds no term (specification 0.6 §§4, 4.1).
METHOD_CONDITIONS = {
    "egm-eligibility": (
        "the construction satisfies the declared line where the continuation value 𝑉≻ is "
        "concave and continuously differentiable on (0, ∞) with a finite positive right "
        "derivative at 0"
    ),
    "marginal-reading": (
        "the right side of each derivative line equals the derivative, in the named "
        "coordinate, of the value the builder writes, under the envelope conditions: "
        "concavity of the continuation value, interiority of the maximizer or the "
        "multiplier's term at a binding constraint, differentiability of the reward in "
        "the control, a measurable selection of the policy, and differentiability of the "
        "value at the point read; listed and not checked"
    ),
}


# --- the diagnostics an elaboration keeps without refusing ---


class Diagnostic(NamedTuple):
    """What an elaboration records without raising: the `rule` broken, the
    `address` of the entry or the block responsible, the `message`, one
    sentence, the `candidates`, the objects the sentence names, and the
    `source_entries`, the authored entries involved.

    The selection of a trellis's connections (`bellman.factory.connections`)
    records one under `connector-shape` (an entry that is no mapping, or a
    keyed connector of another shape than `{from, to, fields}` or between two
    periods), `endpoint-unresolved`, `endpoint-ambiguous`, `use-claimed-twice`,
    `authored-cycle` (a pair authored from a stage to itself among them),
    `pair-incompatible`, `pair-not-established`, `route-incomplete`,
    `route-incompatible`, `route-no-law`, `route-not-established` or
    `selected-cycle`, a cycle among the selected pairs the withdrawal of the
    inferred pairs left, which is a defect of the selection; its `candidates`
    are the uses an ambiguous endpoint could name, the pairs on a cycle in
    its order, the one pair an entry writes over a claimed use or from a stage
    to itself, or the entry of no admitted shape, and its `source_entries`
    each authored mapping entry involved as (expanded mapping address, source
    token, destination token), a token None when the entry has no field
    mapping. A malformed entry refuses construction; duplicate claims and
    cycles remain on a draft, while an operation requiring order refuses them.

    A stage records one under `unread-input` (`stage_answers.diagnostics`):
    its `address` is a backward block whose header lists a value input no
    line of the block reads, its one candidate that input's identity, and
    the block's builder leaves the input out (AAS, 17 October 2026).

    `depends_on` is the address of the diagnostic this one rests on, set on a
    route diagnostic whose route is uncertified because an authored cycle or
    a use claimed twice stands among its pairs, and None otherwise, so that a
    reader suppresses the secondary finding by this fact and not by the text
    of the sentence (Model Interface 0.9 §4). `write` is the action, the edit
    the check establishes, held apart from the sentence as a refusal holds
    it, and None where the check establishes none."""

    rule: str
    address: str
    message: str
    candidates: tuple = ()
    source_entries: tuple = ()
    depends_on: "str | None" = None
    write: "str | None" = None
